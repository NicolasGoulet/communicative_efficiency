#!/usr/bin/env python3
"""
Create supervisor-friendly plots from the diagnostic analysis CSVs.

Inputs are the already-generated summary CSVs under:
- results/special_forms/<run_name>/
- results/fillers_shortenings/<run_name>/
- results/preprocessing_variant_probe/<run_name>/

Outputs are written to figs/diagnostic_analyses/<run_name>/ as PNG and PDF,
plus small summary CSVs and a README.md figure index.
"""

from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_RUN_NAME = "brown_manchester_providence_chi_mot_fat"
DEFAULT_AGE_BIN_MONTHS = 6

GROUP_COLORS = {
    "CHILD": "#2E6F9E",
    "CARETAKERS": "#C66A2E",
}
PHENOMENON_COLORS = {
    "Special forms": "#6E5AA8",
    "Fillers": "#3E8F6B",
    "Shortenings": "#C45B55",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")
    return pd.read_csv(path)


def read_csv_columns(path: Path, usecols: Sequence[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")
    return pd.read_csv(path, usecols=list(usecols))


def save_current_figure(out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_base.with_suffix(".png"), dpi=300)
    plt.savefig(out_base.with_suffix(".pdf"))
    plt.close()


def percent(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0) * 100.0


def add_bar_labels(ax, bars, values: Sequence[float], *, fmt: str = "{:.1f}") -> None:
    for bar, value in zip(bars, values):
        if value <= 0:
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=0,
        )


def aggregate_group_summary(
    special_group: pd.DataFrame,
    fillers_group: pd.DataFrame,
    shortenings_group: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    specs = [
        (
            "Special forms",
            special_group,
            "utterances_with_target_special_form",
            "target_special_form_token_occurrences",
        ),
        ("Fillers", fillers_group, "utterances_with_filler", "filler_token_occurrences"),
        (
            "Shortenings",
            shortenings_group,
            "utterances_with_shortening",
            "shortening_token_occurrences",
        ),
    ]
    for phenomenon, df, utt_col, token_col in specs:
        grouped = (
            df.groupby("speaker_group", as_index=False)
            .agg(
                total_usable_utterances=("total_usable_utterances", "sum"),
                utterances_with_phenomenon=(utt_col, "sum"),
                token_occurrences=(token_col, "sum"),
            )
        )
        grouped["phenomenon"] = phenomenon
        grouped["utterance_rate"] = (
            grouped["utterances_with_phenomenon"] / grouped["total_usable_utterances"].replace(0, np.nan)
        ).fillna(0)
        grouped["mean_tokens_per_utterance"] = (
            grouped["token_occurrences"] / grouped["total_usable_utterances"].replace(0, np.nan)
        ).fillna(0)
        rows.extend(grouped.to_dict("records"))
    return pd.DataFrame(rows)


def age_mid_from_label(label: object) -> float:
    text = "" if label is None else str(label)
    if "_" not in text:
        return float("nan")
    lo, hi = text.split("_", 1)
    try:
        return (float(lo) + float(hi)) / 2.0
    except ValueError:
        return float("nan")


def phenomenon_age_summary_from_frames(
    special_rows: pd.DataFrame,
    filler_rows: pd.DataFrame,
    shortening_rows: pd.DataFrame,
) -> pd.DataFrame:
    pieces: List[pd.DataFrame] = []
    specs = [
        ("Special forms", special_rows, "has_target_special_form"),
        ("Fillers", filler_rows, "has_filler"),
        ("Shortenings", shortening_rows, "has_shortening"),
    ]
    for phenomenon, df, has_col in specs:
        work = df[["speaker_group", "age_bin", has_col]].copy()
        work = work.dropna(subset=["age_bin"])
        work["age_bin"] = work["age_bin"].astype(str)
        work = work[work["age_bin"].str.contains("_")]
        work[has_col] = pd.to_numeric(work[has_col], errors="coerce").fillna(0).astype(int)
        grouped = (
            work.groupby(["speaker_group", "age_bin"], as_index=False)
            .agg(
                total_usable_utterances=(has_col, "size"),
                utterances_with_phenomenon=(has_col, "sum"),
            )
        )
        grouped["phenomenon"] = phenomenon
        grouped["age_mid"] = grouped["age_bin"].apply(age_mid_from_label)
        grouped["utterance_rate"] = (
            grouped["utterances_with_phenomenon"]
            / grouped["total_usable_utterances"].replace(0, np.nan)
        ).fillna(0)
        pieces.append(grouped)
    return pd.concat(pieces, ignore_index=True)


def load_phenomenon_age_summary(special_dir: Path, fillers_dir: Path) -> pd.DataFrame:
    special_rows = read_csv_columns(
        special_dir / "special_forms_per_utterance.csv",
        ["speaker_group", "age_bin", "has_target_special_form"],
    )
    filler_rows = read_csv_columns(
        fillers_dir / "fillers_per_utterance.csv",
        ["speaker_group", "age_bin", "has_filler"],
    )
    shortening_rows = read_csv_columns(
        fillers_dir / "shortenings_per_utterance.csv",
        ["speaker_group", "age_bin", "has_shortening"],
    )
    return phenomenon_age_summary_from_frames(special_rows, filler_rows, shortening_rows)


def plot_phenomenon_age_trajectories(
    age_summary: pd.DataFrame,
    out_dir: Path,
    *,
    age_bin_months: int = DEFAULT_AGE_BIN_MONTHS,
) -> None:
    groups = ["CHILD", "CARETAKERS"]
    phenomena = ["Special forms", "Fillers", "Shortenings"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for ax, group in zip(axes, groups):
        sub_group = age_summary[age_summary["speaker_group"] == group].copy()
        for phenomenon in phenomena:
            sub = sub_group[sub_group["phenomenon"] == phenomenon].sort_values("age_mid")
            if sub.empty:
                continue
            ax.plot(
                sub["age_mid"],
                percent(sub["utterance_rate"]),
                marker="o",
                linewidth=1.8,
                color=PHENOMENON_COLORS[phenomenon],
                label=phenomenon,
            )
        ax.set_title(group.title())
        ax.set_xlabel(f"Age bin midpoint (months; {age_bin_months}-month bins)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Utterances with phenomenon (%)")
    axes[-1].legend(frameon=False, loc="upper right")
    fig.suptitle(
        f"Special Forms, Fillers, and Shortenings Over Age ({age_bin_months}-month age bins)",
        y=1.02,
        fontsize=14,
    )
    save_current_figure(out_dir / "phenomenon_age_trajectories_child_vs_caretakers")


def plot_age_bin_denominators(age_summary: pd.DataFrame, out_dir: Path) -> None:
    """Show the number of scorable utterances underlying each age-bin dot."""
    denom = (
        age_summary[age_summary["phenomenon"] == "Special forms"]
        [["speaker_group", "age_bin", "age_mid", "total_usable_utterances"]]
        .copy()
        .drop_duplicates(["speaker_group", "age_bin"])
        .sort_values(["speaker_group", "age_mid"])
    )
    if denom.empty:
        return

    groups = ["CHILD", "CARETAKERS"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6), sharey=False)
    for ax, group in zip(axes, groups):
        sub = denom[denom["speaker_group"] == group].copy()
        bars = ax.bar(
            sub["age_mid"],
            sub["total_usable_utterances"],
            width=4.2,
            color=GROUP_COLORS[group],
            alpha=0.85,
        )
        ax.set_title(group.title())
        ax.set_xlabel(f"Age bin midpoint (months; {DEFAULT_AGE_BIN_MONTHS}-month bins)")
        ax.set_ylabel("Scorable utterances")
        ax.grid(axis="y", alpha=0.2)
        for bar, value in zip(bars, sub["total_usable_utterances"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{int(value):,}",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=90,
            )
        ax.set_ylim(0, max(sub["total_usable_utterances"].max() * 1.22, 1))
    fig.suptitle(
        f"Denominators for Age-Trajectory Dots ({DEFAULT_AGE_BIN_MONTHS}-month age bins)",
        y=1.02,
        fontsize=14,
    )
    save_current_figure(out_dir / "age_bin_scorable_utterance_counts")


def plot_combined_age_denominator_and_rates(age_summary: pd.DataFrame, out_dir: Path) -> None:
    """Show phenomenon rates and denominator counts in one aligned figure."""
    if age_summary.empty:
        return

    denom = (
        age_summary[age_summary["phenomenon"] == "Special forms"]
        [["speaker_group", "age_bin", "age_mid", "total_usable_utterances"]]
        .drop_duplicates(["speaker_group", "age_bin"])
        .sort_values(["speaker_group", "age_mid"])
    )
    groups = ["CHILD", "CARETAKERS"]
    phenomena = ["Special forms", "Fillers", "Shortenings"]

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(15, 8),
        sharex="col",
        gridspec_kw={"height_ratios": [2.1, 1.0]},
    )

    for col, group in enumerate(groups):
        ax_rate = axes[0, col]
        ax_count = axes[1, col]
        sub_group = age_summary[age_summary["speaker_group"] == group].copy()

        for phenomenon in phenomena:
            sub = sub_group[sub_group["phenomenon"] == phenomenon].sort_values("age_mid")
            if sub.empty:
                continue
            ax_rate.plot(
                sub["age_mid"],
                percent(sub["utterance_rate"]),
                marker="o",
                linewidth=1.8,
                color=PHENOMENON_COLORS[phenomenon],
                label=phenomenon,
            )

        sub_denom = denom[denom["speaker_group"] == group].copy()
        bars = ax_count.bar(
            sub_denom["age_mid"],
            sub_denom["total_usable_utterances"],
            width=4.2,
            color=GROUP_COLORS[group],
            alpha=0.82,
        )
        for bar, value in zip(bars, sub_denom["total_usable_utterances"]):
            ax_count.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{int(value):,}",
                ha="center",
                va="bottom",
                fontsize=6.5,
                rotation=90,
            )

        ax_rate.set_title(group.title())
        ax_rate.set_ylabel("Utterances with phenomenon (%)")
        ax_rate.grid(alpha=0.2)
        ax_count.set_ylabel("Scorable utterances")
        ax_count.set_xlabel(f"Age bin midpoint (months; {DEFAULT_AGE_BIN_MONTHS}-month bins)")
        ax_count.grid(axis="y", alpha=0.2)
        ax_count.set_ylim(0, max(sub_denom["total_usable_utterances"].max() * 1.28, 1))

    axes[0, 1].legend(frameon=False, loc="upper right")
    fig.suptitle(
        "Age-Bin Denominators and Phenomenon Rates",
        y=1.01,
        fontsize=14,
    )
    save_current_figure(out_dir / "age_bin_counts_and_phenomenon_rates")


def plot_overall_rates(summary: pd.DataFrame, out_dir: Path) -> None:
    order = ["Special forms", "Fillers", "Shortenings"]
    groups = ["CHILD", "CARETAKERS"]
    x = np.arange(len(order))
    width = 0.36

    plt.figure(figsize=(9, 5))
    ax = plt.gca()
    for offset, group in zip([-width / 2, width / 2], groups):
        values = []
        for phenomenon in order:
            sub = summary[(summary["phenomenon"] == phenomenon) & (summary["speaker_group"] == group)]
            values.append(float(percent(sub["utterance_rate"]).iloc[0]) if not sub.empty else 0.0)
        bars = ax.bar(
            x + offset,
            values,
            width=width,
            label=group.title(),
            color=GROUP_COLORS[group],
        )
        add_bar_labels(ax, bars, values)

    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Utterances with phenomenon (%)")
    ax.set_title("How Often Do These Forms Appear?")
    ax.legend(frameon=False)
    ax.set_ylim(0, max(1.0, ax.get_ylim()[1] * 1.12))
    save_current_figure(out_dir / "overview_utterance_rates_child_vs_caretakers")


def plot_dataset_rates(summary_by_dataset: pd.DataFrame, out_dir: Path) -> None:
    phenomena = ["Special forms", "Fillers", "Shortenings"]
    datasets = sorted(summary_by_dataset["dataset"].unique())
    groups = ["CHILD", "CARETAKERS"]

    fig, axes = plt.subplots(1, len(phenomena), figsize=(15, 4.8), sharey=True)
    for ax, phenomenon in zip(axes, phenomena):
        sub = summary_by_dataset[summary_by_dataset["phenomenon"] == phenomenon]
        x = np.arange(len(datasets))
        width = 0.36
        for offset, group in zip([-width / 2, width / 2], groups):
            values = []
            for dataset in datasets:
                row = sub[(sub["dataset"] == dataset) & (sub["speaker_group"] == group)]
                values.append(float(percent(row["utterance_rate"]).iloc[0]) if not row.empty else 0.0)
            ax.bar(x + offset, values, width=width, color=GROUP_COLORS[group], label=group.title())
        ax.set_title(phenomenon)
        ax.set_xticks(x)
        ax.set_xticklabels(datasets, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.2)

    axes[0].set_ylabel("Utterances with phenomenon (%)")
    axes[-1].legend(frameon=False, loc="upper right")
    fig.suptitle("Rates by Dataset and Speaker Group", y=1.02, fontsize=14)
    save_current_figure(out_dir / "dataset_utterance_rates_child_vs_caretakers")


def make_dataset_summary(
    special_group: pd.DataFrame,
    fillers_group: pd.DataFrame,
    shortenings_group: pd.DataFrame,
) -> pd.DataFrame:
    pieces = []
    specs = [
        (
            "Special forms",
            special_group,
            "utterances_with_target_special_form",
            "target_special_form_token_occurrences",
        ),
        ("Fillers", fillers_group, "utterances_with_filler", "filler_token_occurrences"),
        (
            "Shortenings",
            shortenings_group,
            "utterances_with_shortening",
            "shortening_token_occurrences",
        ),
    ]
    for phenomenon, df, utt_col, token_col in specs:
        out = df[
            ["dataset", "speaker_group", "total_usable_utterances", utt_col, token_col]
        ].copy()
        out = out.rename(
            columns={
                utt_col: "utterances_with_phenomenon",
                token_col: "token_occurrences",
            }
        )
        out["phenomenon"] = phenomenon
        out["utterance_rate"] = (
            out["utterances_with_phenomenon"] / out["total_usable_utterances"].replace(0, np.nan)
        ).fillna(0)
        pieces.append(out)
    return pd.concat(pieces, ignore_index=True)


def plot_special_marker_rates(marker_df: pd.DataFrame, out_dir: Path) -> None:
    target = marker_df.copy()
    marker_order = (
        target.groupby("marker")["marker_token_occurrences"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    groups = ["CHILD", "CARETAKERS"]
    x = np.arange(len(marker_order))
    width = 0.36

    plt.figure(figsize=(12, 5.2))
    ax = plt.gca()
    for offset, group in zip([-width / 2, width / 2], groups):
        values = []
        for marker in marker_order:
            sub = target[(target["marker"] == marker) & (target["speaker_group"] == group)]
            totals = sub["total_usable_utterances"].sum()
            utts = sub["utterances_with_marker"].sum()
            values.append((utts / totals * 100.0) if totals else 0.0)
        ax.bar(x + offset, values, width=width, color=GROUP_COLORS[group], label=group.title())

    ax.set_xticks(x)
    ax.set_xticklabels([f"@{m}" for m in marker_order])
    ax.set_ylabel("Utterances with marker (%)")
    ax.set_title("Special CHAT Markers by Speaker Group")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    save_current_figure(out_dir / "special_marker_rates_child_vs_caretakers")


def plot_special_marker_tokens(marker_df: pd.DataFrame, out_dir: Path) -> None:
    target = marker_df.copy()
    totals = (
        target.groupby(["speaker_group", "marker"], as_index=False)["marker_token_occurrences"]
        .sum()
    )
    marker_order = (
        totals.groupby("marker")["marker_token_occurrences"].sum().sort_values().index.tolist()
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(marker_order))
    left = np.zeros(len(marker_order))
    for group in ["CHILD", "CARETAKERS"]:
        values = []
        for marker in marker_order:
            sub = totals[(totals["speaker_group"] == group) & (totals["marker"] == marker)]
            values.append(int(sub["marker_token_occurrences"].iloc[0]) if not sub.empty else 0)
        ax.barh(y, values, left=left, color=GROUP_COLORS[group], label=group.title())
        left += np.array(values)

    ax.set_yticks(y)
    ax.set_yticklabels([f"@{marker}" for marker in marker_order])
    ax.set_xlabel("Token occurrences")
    ax.set_title("Special CHAT Marker Token Counts")
    ax.legend(frameon=False)
    ax.grid(axis="x", alpha=0.2)
    save_current_figure(out_dir / "special_marker_token_counts_stacked")


def plot_filler_type_rates(filler_type_df: pd.DataFrame, out_dir: Path) -> None:
    type_order = (
        filler_type_df.groupby("filler_type")["filler_token_occurrences"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    groups = ["CHILD", "CARETAKERS"]
    x = np.arange(len(type_order))
    width = 0.36

    plt.figure(figsize=(11, 5.2))
    ax = plt.gca()
    for offset, group in zip([-width / 2, width / 2], groups):
        values = []
        for filler_type in type_order:
            sub = filler_type_df[
                (filler_type_df["filler_type"] == filler_type)
                & (filler_type_df["speaker_group"] == group)
            ]
            totals = sub["total_usable_utterances"].sum()
            utts = sub["utterances_with_filler_type"].sum()
            values.append((utts / totals * 100.0) if totals else 0.0)
        ax.bar(x + offset, values, width=width, color=GROUP_COLORS[group], label=group.title())

    ax.set_xticks(x)
    ax.set_xticklabels(type_order)
    ax.set_ylabel("Utterances with filler type (%)")
    ax.set_title("Filler Types by Speaker Group")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    save_current_figure(out_dir / "filler_type_rates_child_vs_caretakers")


def plot_top_shortening_texts(shortening_text_df: pd.DataFrame, out_dir: Path, top_n: int = 18) -> None:
    totals = (
        shortening_text_df.groupby(["speaker_group", "parenthetical_text"], as_index=False)[
            "shortening_token_occurrences"
        ]
        .sum()
    )
    top_texts = (
        totals.groupby("parenthetical_text")["shortening_token_occurrences"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .sort_values()
        .index.tolist()
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    y = np.arange(len(top_texts))
    left = np.zeros(len(top_texts))
    for group in ["CHILD", "CARETAKERS"]:
        values = []
        for text in top_texts:
            sub = totals[(totals["speaker_group"] == group) & (totals["parenthetical_text"] == text)]
            values.append(int(sub["shortening_token_occurrences"].iloc[0]) if not sub.empty else 0)
        ax.barh(y, values, left=left, color=GROUP_COLORS[group], label=group.title())
        left += np.array(values)

    ax.set_yticks(y)
    ax.set_yticklabels([f"({text})" for text in top_texts])
    ax.set_xlabel("Token occurrences")
    ax.set_title(f"Top {top_n} Parenthetical Shortening Pieces")
    ax.legend(frameon=False)
    ax.grid(axis="x", alpha=0.2)
    save_current_figure(out_dir / "shortening_top_parenthetical_texts")


def plot_age_trajectory(
    age_df: pd.DataFrame,
    *,
    item_col: str,
    item_label_prefix: str,
    count_col: str,
    utt_col: str,
    out_base: Path,
    title: str,
    age_bin_months: int = DEFAULT_AGE_BIN_MONTHS,
    top_n: int = 5,
) -> None:
    if age_df.empty:
        return

    top_items = (
        age_df.groupby(item_col)[count_col].sum().sort_values(ascending=False).head(top_n).index.tolist()
    )
    groups = ["CHILD", "CARETAKERS"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for ax, group in zip(axes, groups):
        sub_group = age_df[age_df["speaker_group"] == group].copy()
        for item in top_items:
            sub = sub_group[sub_group[item_col] == item].copy()
            if sub.empty:
                continue
            sub["rate_percent"] = (
                sub[utt_col] / sub["total_usable_utterances"].replace(0, np.nan) * 100.0
            ).fillna(0)
            sub = (
                sub.groupby("age_mid", as_index=False)["rate_percent"]
                .mean()
                .sort_values("age_mid")
            )
            ax.plot(
                sub["age_mid"],
                sub["rate_percent"],
                marker="o",
                linewidth=1.5,
                label=f"{item_label_prefix}{item}",
            )
        ax.set_title(group.title())
        ax.set_xlabel(f"Age bin midpoint (months; {age_bin_months}-month bins)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Utterance rate (%)")
    axes[-1].legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle(f"{title} ({age_bin_months}-month age bins)", y=1.02, fontsize=14)
    save_current_figure(out_base)


def plot_variant_category_counts(probe_wide: pd.DataFrame, out_dir: Path) -> None:
    counts = probe_wide["base_category"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(counts.index, counts.values, color="#567C5D")
    ax.set_xlabel("Base utterances")
    ax.set_title("Preprocessing Probe: Example Categories")
    ax.grid(axis="x", alpha=0.2)
    for y, value in enumerate(counts.values):
        ax.text(value, y, f" {value}", va="center", fontsize=9)
    save_current_figure(out_dir / "variant_probe_category_counts")


def plot_variant_word_counts(probe_long: pd.DataFrame, out_dir: Path) -> None:
    order = [
        "current_clean",
        "raw_chat_main_tier",
        "expand_shortenings",
        "remove_fillers",
        "expand_shortenings_remove_fillers",
        "preserve_special_at_suffixes",
        "drop_special_form_tokens",
    ]
    labels = {
        "current_clean": "Current",
        "raw_chat_main_tier": "Raw CHAT",
        "expand_shortenings": "Expand\nshortenings",
        "remove_fillers": "Remove\nfillers",
        "expand_shortenings_remove_fillers": "Expand +\nremove fillers",
        "preserve_special_at_suffixes": "Preserve\n@ suffixes",
        "drop_special_form_tokens": "Drop special\nforms",
    }
    data = [probe_long.loc[probe_long["variant_id"] == variant, "word_count"].astype(float) for variant in order]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.boxplot(data, tick_labels=[labels[v] for v in order], showfliers=False)
    ax.set_ylabel("Regex word count")
    ax.set_title("Preprocessing Probe: Variant Lengths")
    ax.grid(axis="y", alpha=0.2)
    save_current_figure(out_dir / "variant_probe_word_count_distributions")


def plot_variant_scorable_counts(probe_long: pd.DataFrame, out_dir: Path) -> None:
    summary = (
        probe_long.groupby(["variant_id", "speaker_group"], as_index=False)["is_scorable_variant"]
        .sum()
    )
    order = [
        "current_clean",
        "raw_chat_main_tier",
        "expand_shortenings",
        "remove_fillers",
        "expand_shortenings_remove_fillers",
        "preserve_special_at_suffixes",
        "drop_special_form_tokens",
    ]
    x = np.arange(len(order))
    width = 0.36
    fig, ax = plt.subplots(figsize=(12, 5.2))
    for offset, group in zip([-width / 2, width / 2], ["CHILD", "CARETAKERS"]):
        values = []
        for variant in order:
            sub = summary[(summary["variant_id"] == variant) & (summary["speaker_group"] == group)]
            values.append(int(sub["is_scorable_variant"].iloc[0]) if not sub.empty else 0)
        ax.bar(x + offset, values, width=width, color=GROUP_COLORS[group], label=group.title())
    ax.set_xticks(x)
    ax.set_xticklabels(
        [
            "Current",
            "Raw",
            "Expand",
            "No fillers",
            "Expand +\nno fillers",
            "Keep @",
            "Drop special",
        ],
        rotation=0,
    )
    ax.set_ylabel("Scorable variant rows")
    ax.set_title("Preprocessing Probe: Scorable Rows by Variant")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    save_current_figure(out_dir / "variant_probe_scorable_counts")


def write_summary_readme(out_dir: Path, run_name: str) -> None:
    readme = f"""# Diagnostic Analysis Figures

Run: `{run_name}`

Recommended figures to send first:

1. `overview_utterance_rates_child_vs_caretakers.png`
2. `dataset_utterance_rates_child_vs_caretakers.png`
3. `special_marker_rates_child_vs_caretakers.png`
4. `filler_type_rates_child_vs_caretakers.png`
5. `shortening_top_parenthetical_texts.png`
6. `age_bin_counts_and_phenomenon_rates.png`
7. `phenomenon_age_trajectories_child_vs_caretakers.png`
8. `age_bin_scorable_utterance_counts.png`
9. `special_marker_age_trajectories.png`
10. `filler_age_trajectories.png`
11. `shortening_age_trajectories.png`
12. `variant_probe_category_counts.png`
13. `variant_probe_word_count_distributions.png`

All figures are written as both PNG and PDF.

Interpretation note: rates use scorable utterances as denominators. In the
diagnostic scripts, scorable means `utterance_clean` contains at least one word
token. `CHILD` is `CHI`; `CARETAKERS` merges `MOT` and `FAT`.

Age-trajectory note: trajectory plots are not continuous-age curves. The x-axis
shows the midpoint of 6-month age bins. For example, x = 27 means the 24_30
month bin, not exactly age 27 months.

The companion figure `age_bin_scorable_utterance_counts.png` shows the number
of scorable utterances behind each age-bin dot.

The combined figure `age_bin_counts_and_phenomenon_rates.png` puts both pieces
together: rates for special forms, fillers, and shortenings above, with the
number of scorable utterances per age bin directly below.
"""
    (out_dir / "README.md").write_text(textwrap.dedent(readme), encoding="utf-8")


def make_title_from_stem(stem: str) -> str:
    return stem.replace("_", " ").title()


def write_pdf_packet(out_dir: Path, figure_stems: Sequence[str]) -> None:
    packet_path = out_dir / "diagnostic_figures_packet.pdf"
    with PdfPages(packet_path) as pdf:
        for stem in figure_stems:
            png_path = out_dir / f"{stem}.png"
            if not png_path.exists():
                continue
            image = mpimg.imread(png_path)
            height, width = image.shape[:2]
            fig_width = 11
            fig_height = max(6.5, fig_width * height / max(width, 1))
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            ax.imshow(image)
            ax.axis("off")
            ax.set_title(make_title_from_stem(stem), fontsize=14, pad=14)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create plots from special-form, filler, shortening, and variant-probe diagnostics."
    )
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument(
        "--special-dir",
        type=Path,
        default=None,
        help="Override results/special_forms/<run-name> input directory.",
    )
    parser.add_argument(
        "--fillers-dir",
        type=Path,
        default=None,
        help="Override results/fillers_shortenings/<run-name> input directory.",
    )
    parser.add_argument(
        "--probe-dir",
        type=Path,
        default=None,
        help="Override results/preprocessing_variant_probe/<run-name> input directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override figs/diagnostic_analyses/<run-name> output directory.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_cli().parse_args(argv)
    run_name = args.run_name
    special_dir = args.special_dir or PROJECT_ROOT / "results" / "special_forms" / run_name
    fillers_dir = args.fillers_dir or PROJECT_ROOT / "results" / "fillers_shortenings" / run_name
    probe_dir = args.probe_dir or PROJECT_ROOT / "results" / "preprocessing_variant_probe" / run_name
    out_dir = args.output_dir or PROJECT_ROOT / "figs" / "diagnostic_analyses" / run_name
    out_dir = out_dir.expanduser().resolve()

    special_group = read_csv(special_dir / "special_forms_by_dataset_speaker_group.csv")
    special_marker = read_csv(special_dir / "special_forms_by_dataset_speaker_group_marker.csv")
    special_age = read_csv(special_dir / "special_forms_by_age_bin_speaker_group_marker.csv")
    fillers_group = read_csv(fillers_dir / "fillers_by_dataset_speaker_group.csv")
    filler_type = read_csv(fillers_dir / "fillers_by_dataset_speaker_group_type.csv")
    filler_age = read_csv(fillers_dir / "fillers_by_age_bin_speaker_group_type.csv")
    shortenings_group = read_csv(fillers_dir / "shortenings_by_dataset_speaker_group.csv")
    shortening_text = read_csv(fillers_dir / "shortenings_by_dataset_speaker_group_text.csv")
    shortening_age = read_csv(fillers_dir / "shortenings_by_age_bin_speaker_group_text.csv")
    probe_long = read_csv(probe_dir / "preprocessing_variant_probe_long.csv")
    probe_wide = read_csv(probe_dir / "preprocessing_variant_probe_wide.csv")
    phenomenon_age = load_phenomenon_age_summary(special_dir, fillers_dir)

    summary = aggregate_group_summary(special_group, fillers_group, shortenings_group)
    dataset_summary = make_dataset_summary(special_group, fillers_group, shortenings_group)
    write_csv(out_dir / "diagnostic_overall_summary.csv", summary)
    write_csv(out_dir / "diagnostic_dataset_summary.csv", dataset_summary)
    write_csv(out_dir / "diagnostic_phenomenon_age_summary.csv", phenomenon_age)

    plot_overall_rates(summary, out_dir)
    plot_dataset_rates(dataset_summary, out_dir)
    plot_special_marker_rates(special_marker, out_dir)
    plot_special_marker_tokens(special_marker, out_dir)
    plot_filler_type_rates(filler_type, out_dir)
    plot_top_shortening_texts(shortening_text, out_dir)
    plot_phenomenon_age_trajectories(phenomenon_age, out_dir)
    plot_age_bin_denominators(phenomenon_age, out_dir)
    plot_combined_age_denominator_and_rates(phenomenon_age, out_dir)
    plot_age_trajectory(
        special_age,
        item_col="marker",
        item_label_prefix="@",
        count_col="marker_token_occurrences",
        utt_col="utterances_with_marker",
        out_base=out_dir / "special_marker_age_trajectories",
        title="Special Marker Rates Over Age",
        top_n=5,
    )
    plot_age_trajectory(
        filler_age,
        item_col="filler_type",
        item_label_prefix="",
        count_col="filler_token_occurrences",
        utt_col="utterances_with_filler_type",
        out_base=out_dir / "filler_age_trajectories",
        title="Filler Rates Over Age",
        top_n=5,
    )
    plot_age_trajectory(
        shortening_age,
        item_col="parenthetical_text",
        item_label_prefix="(",
        count_col="shortening_token_occurrences",
        utt_col="utterances_with_parenthetical_text",
        out_base=out_dir / "shortening_age_trajectories",
        title="Parenthetical Shortening Rates Over Age",
        top_n=5,
    )
    plot_variant_category_counts(probe_wide, out_dir)
    plot_variant_word_counts(probe_long, out_dir)
    plot_variant_scorable_counts(probe_long, out_dir)
    write_summary_readme(out_dir, run_name)
    recommended = [
        "overview_utterance_rates_child_vs_caretakers",
        "dataset_utterance_rates_child_vs_caretakers",
        "special_marker_rates_child_vs_caretakers",
        "filler_type_rates_child_vs_caretakers",
        "shortening_top_parenthetical_texts",
        "age_bin_counts_and_phenomenon_rates",
        "phenomenon_age_trajectories_child_vs_caretakers",
        "age_bin_scorable_utterance_counts",
        "special_marker_age_trajectories",
        "filler_age_trajectories",
        "shortening_age_trajectories",
        "variant_probe_category_counts",
        "variant_probe_word_count_distributions",
    ]
    write_pdf_packet(out_dir, recommended)

    figure_count = len(list(out_dir.glob("*.png")))
    print(f"Wrote {figure_count} PNG figures plus PDFs to {out_dir}")
    print(f"Wrote combined packet to {out_dir / 'diagnostic_figures_packet.pdf'}")


if __name__ == "__main__":
    main()
