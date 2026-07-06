#!/usr/bin/env python3
"""Build an available-now efficiency cloud from already scored baselines.

This uses real child, random, n-gram, and LSTM utterances that have already
been scored with the same Mistral surprisal model. It does not depend on
scoring the Mistral-generated response-entropy samples.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_RESPONSE_SPACE = Path("results/route2_response_space/route2_child_response_space_effort_table.csv.gz")
DEFAULT_PAIRWISE_DIR = Path("results/route1_real_vs_controls_context_report")
DEFAULT_OUTPUT_DIR = Path("results/existing_scored_baseline_efficiency_cloud")
DEFAULT_FIG_DIR = Path("figs/existing_scored_baseline_efficiency_cloud")
DEFAULT_REPORT_MD = Path("docs/existing_scored_baseline_efficiency_cloud.md")
DEFAULT_REPORT_HTML = Path("docs/existing_scored_baseline_efficiency_cloud.html")

VARIANT_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
    "lstm_additive_k3_same_length": "LSTM k3",
    "lstm_additive_k4_same_length": "LSTM k4",
    "lstm_additive_k5_same_length": "LSTM k5",
}
SOURCE_ORDER = list(VARIANT_LABELS.values())
SOURCE_PALETTE = {
    "Real child": "#1f5a5f",
    "Random": "#8c510a",
    "Unigram": "#01665e",
    "Bigram": "#5e3c99",
    "Trigram": "#c51b7d",
    "LSTM k3": "#2166ac",
    "LSTM k4": "#1b7837",
    "LSTM k5": "#b2182b",
}
PLOT_VARIANTS = list(VARIANT_LABELS)
PLOT_VALUE_COLS = [
    "sum_bits",
    "mean_bits_per_token",
    "bits_per_word",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_phonemes",
    "context_entropy_bits",
    "response_entropy_bits",
    "generated_expected_words",
]
LONG_USECOLS = [
    "utterance_id",
    "dataset",
    "child_id",
    "session_id",
    "age_months",
    "age_bin",
    "role",
    "target_variant",
    "context_k",
    "sum_bits",
    "mean_bits_per_token",
    "bits_per_word",
    "n_eval_tokens",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_phonemes",
    "context_entropy_bits",
]
RESPONSE_USECOLS = [
    "utterance_id",
    "response_entropy_bits",
    "response_top_probability",
    "response_unique_response_count",
    "generated_expected_words",
]
PAIRWISE_SOURCES = [
    ("random", "Random"),
    ("unigram", "Unigram"),
    ("bigram", "Bigram"),
    ("trigram", "Trigram"),
    ("lstm_additive_k3_same_length", "LSTM k3"),
    ("lstm_additive_k4_same_length", "LSTM k4"),
    ("lstm_additive_k5_same_length", "LSTM k5"),
]


def age_bin_midpoint(value: object) -> float:
    """Return the midpoint of an age-bin label like ``024-029``."""

    text = str(value)
    if "-" not in text:
        return math.nan
    left, right = text.split("-", 1)
    try:
        return (float(left) + float(right)) / 2.0
    except ValueError:
        return math.nan


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 30, digits: int = 4) -> str:
    """Render a compact Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    out = shown.astype(object)
    for col in shown.columns:
        if pd.api.types.is_numeric_dtype(shown[col]):
            out[col] = shown[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}g}")
    header = "| " + " | ".join(out.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(out.columns)) + " |"
    rows = ["| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |" for row in out.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *rows])


def relative_to_doc(path: Path, doc_path: Path) -> str:
    """Return a POSIX relative path from a report document."""

    return Path("../" + path.as_posix()).as_posix() if not path.is_absolute() else path.as_posix()


def read_response_entropy_lookup(path: Path) -> pd.DataFrame:
    """Read response-entropy predictors keyed by real child utterance id."""

    available = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [col for col in RESPONSE_USECOLS if col in available]
    missing = {"utterance_id", "response_entropy_bits"} - set(usecols)
    if missing:
        raise KeyError(f"{path} missing required response-entropy columns: {sorted(missing)}")
    lookup = pd.read_csv(path, usecols=usecols, low_memory=False)
    for col in [c for c in usecols if c != "utterance_id"]:
        lookup[col] = pd.to_numeric(lookup[col], errors="coerce")
    return lookup.drop_duplicates("utterance_id").reset_index(drop=True)


def response_entropy_edges(series: pd.Series, *, q: int = 4) -> tuple[np.ndarray, list[str]]:
    """Return quantile edges and labels for response entropy."""

    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return np.array([-np.inf, np.inf]), ["all"]
    quantiles = values.quantile(np.linspace(0, 1, q + 1)).to_numpy(dtype=float)
    edges = np.unique(quantiles)
    if len(edges) < 3:
        return np.array([-np.inf, np.inf]), ["all"]
    edges[0] = -np.inf
    edges[-1] = np.inf
    base_labels = ["low", "mid-low", "mid-high", "high"]
    labels = base_labels[: len(edges) - 1]
    return edges, labels


def add_plot_columns(frame: pd.DataFrame, entropy_edges: np.ndarray, entropy_labels: Sequence[str]) -> pd.DataFrame:
    """Add labels, age midpoints, effort buckets, and entropy bins."""

    out = frame.copy()
    out["source_label"] = out["target_variant"].map(VARIANT_LABELS).fillna(out["target_variant"])
    out["age_bin_mid"] = out["age_bin"].map(age_bin_midpoint)
    words = pd.to_numeric(out["nb_words"], errors="coerce")
    out["nb_words_bucket"] = np.where(words.le(12), words.round().astype("Int64").astype(str), "13+")
    out.loc[words.isna(), "nb_words_bucket"] = "missing"
    out["response_entropy_bin"] = "missing"
    has_entropy = pd.to_numeric(out.get("response_entropy_bits"), errors="coerce").notna()
    if has_entropy.any():
        out.loc[has_entropy, "response_entropy_bin"] = pd.cut(
            out.loc[has_entropy, "response_entropy_bits"],
            bins=entropy_edges,
            labels=list(entropy_labels),
            include_lowest=True,
        ).astype(str)
    return out


def summarize_chunk(frame: pd.DataFrame, group_cols: Sequence[str], value_cols: Sequence[str]) -> pd.DataFrame:
    """Summarize one chunk for later additive accumulation."""

    present_values = [col for col in value_cols if col in frame.columns]
    grouped = frame.groupby(list(group_cols), observed=True, dropna=False)
    size = grouped.size().rename("n")
    sums = grouped[present_values].sum(numeric_only=True).add_suffix("__sum")
    counts = grouped[present_values].count().add_suffix("__count")
    return pd.concat([size, sums, counts], axis=1).reset_index()


def accumulate_summary(existing: pd.DataFrame | None, new: pd.DataFrame, group_cols: Sequence[str]) -> pd.DataFrame:
    """Add one chunk summary to an accumulated summary table."""

    if existing is None or existing.empty:
        return new
    combined = pd.concat([existing, new], ignore_index=True)
    value_cols = [col for col in combined.columns if col not in group_cols]
    return combined.groupby(list(group_cols), observed=True, dropna=False)[value_cols].sum().reset_index()


def finalize_summary(accumulated: pd.DataFrame, group_cols: Sequence[str], value_cols: Sequence[str]) -> pd.DataFrame:
    """Convert accumulated sums/counts into mean columns."""

    if accumulated.empty:
        return accumulated
    out = accumulated[list(group_cols) + ["n"]].copy()
    for col in value_cols:
        sum_col = f"{col}__sum"
        count_col = f"{col}__count"
        if sum_col not in accumulated.columns or count_col not in accumulated.columns:
            continue
        out[f"mean_{col}"] = accumulated[sum_col] / accumulated[count_col].replace(0, np.nan)
    sort_cols = [col for col in ["source_label", "target_variant", "age_bin_mid", "nb_words_bucket", "response_entropy_bin"] if col in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)
    return out


def read_cloud_products(
    *,
    input_csv: Path,
    response_space_csv: Path,
    output_dir: Path,
    chunksize: int,
    sample_frac: float,
    sample_per_source: int,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame]:
    """Read the long scored table once and write compact cloud products."""

    output_dir.mkdir(parents=True, exist_ok=True)
    response_lookup = read_response_entropy_lookup(response_space_csv)
    entropy_edges, entropy_labels = response_entropy_edges(response_lookup["response_entropy_bits"])

    available = pd.read_csv(input_csv, nrows=0).columns.tolist()
    usecols = [col for col in LONG_USECOLS if col in available]
    missing = {"utterance_id", "role", "target_variant", "context_k", "sum_bits", "nb_words"} - set(usecols)
    if missing:
        raise KeyError(f"{input_csv} missing required columns: {sorted(missing)}")

    group_specs = {
        "source": ["target_variant", "source_label"],
        "age": ["target_variant", "source_label", "age_bin", "age_bin_mid"],
        "age_effort": ["target_variant", "source_label", "age_bin", "age_bin_mid", "nb_words_bucket"],
        "response_entropy": ["target_variant", "source_label", "response_entropy_bin"],
    }
    accumulators: dict[str, pd.DataFrame | None] = {name: None for name in group_specs}
    sampled_parts: list[pd.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    rows_read = 0
    filtered_rows = 0
    response_entropy_matched = 0

    for chunk_index, chunk in enumerate(pd.read_csv(input_csv, usecols=usecols, chunksize=chunksize, low_memory=False)):
        rows_read += len(chunk)
        sub = chunk[
            chunk["role"].eq("child")
            & chunk["context_k"].eq("k3")
            & chunk["target_variant"].isin(PLOT_VARIANTS)
        ].copy()
        if sub.empty:
            continue
        for col in [c for c in PLOT_VALUE_COLS + ["age_months", "n_eval_tokens", "session_id"] if c in sub.columns]:
            sub[col] = pd.to_numeric(sub[col], errors="coerce")
        sub = sub.merge(response_lookup, on="utterance_id", how="left", suffixes=("", "_route2"))
        if "generated_expected_words_route2" in sub.columns and "generated_expected_words" not in sub.columns:
            sub = sub.rename(columns={"generated_expected_words_route2": "generated_expected_words"})
        elif "generated_expected_words_route2" in sub.columns:
            sub["generated_expected_words"] = sub["generated_expected_words"].fillna(sub["generated_expected_words_route2"])
            sub = sub.drop(columns=["generated_expected_words_route2"])
        sub = add_plot_columns(sub, entropy_edges, entropy_labels)
        filtered_rows += len(sub)
        response_entropy_matched += int(sub["response_entropy_bits"].notna().sum())

        for name, group_cols in group_specs.items():
            summary = summarize_chunk(sub, group_cols, PLOT_VALUE_COLS)
            accumulators[name] = accumulate_summary(accumulators[name], summary, group_cols)

        if sample_frac > 0:
            sampled = sub.sample(frac=min(sample_frac, 1.0), random_state=seed + chunk_index)
            sampled_parts.append(
                sampled[
                    [
                        "utterance_id",
                        "dataset",
                        "child_id",
                        "session_id",
                        "age_months",
                        "age_bin",
                        "age_bin_mid",
                        "target_variant",
                        "source_label",
                        "sum_bits",
                        "mean_bits_per_token",
                        "bits_per_word",
                        "nb_words",
                        "nb_morphemes",
                        "nb_syllables_cmu_or_pkg",
                        "nb_phonemes",
                        "context_entropy_bits",
                        "response_entropy_bits",
                        "response_entropy_bin",
                        "generated_expected_words",
                    ]
                ]
            )

        audit_rows.append(
            {
                "chunk_index": chunk_index,
                "rows_read": len(chunk),
                "filtered_cloud_rows": len(sub),
                "response_entropy_matched_rows": int(sub["response_entropy_bits"].notna().sum()),
            }
        )

    summaries = {
        name: finalize_summary(accum if accum is not None else pd.DataFrame(), group_specs[name], PLOT_VALUE_COLS)
        for name, accum in accumulators.items()
    }
    sample = pd.concat(sampled_parts, ignore_index=True) if sampled_parts else pd.DataFrame()
    if not sample.empty:
        sample = pd.concat(
            [
                group.sample(n=min(len(group), sample_per_source), random_state=seed)
                for _, group in sample.groupby("source_label", observed=True)
            ],
            ignore_index=True,
        )

    audit = pd.DataFrame(
        [
            {"metric": "input_rows_read", "value": rows_read},
            {"metric": "filtered_child_k3_cloud_rows", "value": filtered_rows},
            {"metric": "response_entropy_matched_rows", "value": response_entropy_matched},
            {"metric": "sample_rows", "value": len(sample)},
            {"metric": "sources", "value": sample["source_label"].nunique() if not sample.empty else 0},
            {"metric": "response_entropy_lookup_rows", "value": len(response_lookup)},
        ]
    )
    audit.to_csv(output_dir / "existing_scored_baseline_efficiency_cloud_audit.csv", index=False)
    pd.DataFrame(audit_rows).to_csv(output_dir / "existing_scored_baseline_efficiency_cloud_chunk_audit.csv", index=False)
    for name, summary in summaries.items():
        summary.to_csv(output_dir / f"existing_scored_baseline_efficiency_cloud_summary_by_{name}.csv", index=False)
    sample.to_csv(output_dir / "existing_scored_baseline_efficiency_cloud_sample.csv.gz", index=False)
    return sample, summaries, audit


def read_pairwise_gap_summary(pairwise_dir: Path, output_dir: Path) -> pd.DataFrame:
    """Summarize existing same-utterance real-vs-baseline paired comparisons."""

    rows: list[pd.DataFrame] = []
    usecols = ["utterance_id", "age_bin", "age_months", "source", "source_label", "gap_k3", "gain_gap"]
    for source, label in PAIRWISE_SOURCES:
        path = pairwise_dir / f"{source}_paired_real_comparison.csv.gz"
        if not path.exists():
            continue
        frame = pd.read_csv(path, usecols=usecols)
        frame["source"] = source
        frame["source_label"] = label
        frame["gap_k3"] = pd.to_numeric(frame["gap_k3"], errors="coerce")
        frame["gain_gap"] = pd.to_numeric(frame["gain_gap"], errors="coerce")
        frame["age_bin_mid"] = frame["age_bin"].map(age_bin_midpoint)
        frame["baseline_higher_k3_bits"] = frame["gap_k3"] > 0
        summary = (
            frame.groupby(["source", "source_label", "age_bin", "age_bin_mid"], observed=True, dropna=False)
            .agg(
                n=("gap_k3", "size"),
                mean_control_minus_real_k3_bits=("gap_k3", "mean"),
                median_control_minus_real_k3_bits=("gap_k3", "median"),
                baseline_higher_k3_bits_rate=("baseline_higher_k3_bits", "mean"),
                mean_control_minus_real_context_gain=("gain_gap", "mean"),
            )
            .reset_index()
        )
        rows.append(summary)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not out.empty:
        out = out.sort_values(["source_label", "age_bin_mid"]).reset_index(drop=True)
    out.to_csv(output_dir / "existing_scored_baseline_pairwise_real_gap_summary.csv", index=False)
    return out


def save_3d_scatter(sample: pd.DataFrame, path: Path) -> None:
    """Save a sampled 3D age-effort-information scatter."""

    if sample.empty:
        return
    plot = sample.dropna(subset=["age_months", "nb_words", "sum_bits"]).copy()
    plot = plot[plot["nb_words"].between(0, 16) & plot["sum_bits"].between(0, plot["sum_bits"].quantile(0.995))]
    if plot.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    for label in SOURCE_ORDER:
        group = plot[plot["source_label"].eq(label)]
        if group.empty:
            continue
        group = group.sample(n=min(len(group), 2500), random_state=7)
        ax.scatter(
            group["age_months"],
            group["nb_words"],
            group["sum_bits"],
            s=8 if label == "Real child" else 5,
            alpha=0.34 if label == "Real child" else 0.12,
            color=SOURCE_PALETTE.get(label),
            label=label,
        )
    ax.set_xlabel("Age in months")
    ax.set_ylabel("Effort: words")
    ax.set_zlabel("Information: Mistral k3 bits")
    ax.view_init(elev=24, azim=-58)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_3d_centroid_trajectory(age_summary: pd.DataFrame, path: Path) -> None:
    """Save a 3D line plot of source centroids by age."""

    if age_summary.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    for label in SOURCE_ORDER:
        group = age_summary[age_summary["source_label"].eq(label)].sort_values("age_bin_mid")
        if group.empty:
            continue
        ax.plot(
            group["age_bin_mid"],
            group["mean_nb_words"],
            group["mean_sum_bits"],
            marker="o",
            linewidth=2.5 if label == "Real child" else 1.8,
            color=SOURCE_PALETTE.get(label),
            label=label,
        )
    ax.set_xlabel("Age-bin midpoint")
    ax.set_ylabel("Mean effort: words")
    ax.set_zlabel("Mean information: Mistral k3 bits")
    ax.view_init(elev=23, azim=-50)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_effort_information_facets(sample: pd.DataFrame, path: Path) -> None:
    """Save faceted 2D effort-information sampled clouds."""

    if sample.empty:
        return
    plot = sample.dropna(subset=["nb_words", "sum_bits", "age_months"]).copy()
    plot = plot[plot["nb_words"].between(0, 14) & plot["sum_bits"].between(0, plot["sum_bits"].quantile(0.99))]
    if plot.empty:
        return
    sns.set_theme(style="whitegrid", context="paper")
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharex=True, sharey=True, constrained_layout=True)
    for ax, label in zip(axes.ravel(), SOURCE_ORDER):
        group = plot[plot["source_label"].eq(label)]
        if group.empty:
            ax.set_visible(False)
            continue
        group = group.sample(n=min(len(group), 6000), random_state=13)
        points = ax.scatter(
            group["nb_words"],
            group["sum_bits"],
            c=group["age_months"],
            cmap="viridis",
            s=4,
            alpha=0.24,
            linewidths=0,
        )
        ax.set_title(label)
        ax.set_xlabel("Words")
        ax.set_ylabel("Mistral k3 bits")
    fig.colorbar(points, ax=axes.ravel().tolist(), shrink=0.72, label="Age in months")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_age_centroid_panels(age_summary: pd.DataFrame, path: Path) -> None:
    """Save age-bin centroid trajectories for information, effort, and rate."""

    if age_summary.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    metrics = [
        ("mean_sum_bits", "Mean Mistral k3 bits"),
        ("mean_nb_words", "Mean words"),
        ("mean_bits_per_word", "Mean bits per word"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8), sharex=True, constrained_layout=True)
    for ax, (metric, ylabel) in zip(axes, metrics):
        for label in SOURCE_ORDER:
            group = age_summary[age_summary["source_label"].eq(label)].sort_values("age_bin_mid")
            if group.empty or metric not in group.columns:
                continue
            ax.plot(
                group["age_bin"].astype(str),
                group[metric],
                marker="o",
                linewidth=2.6 if label == "Real child" else 1.8,
                color=SOURCE_PALETTE.get(label),
                label=label,
            )
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Age bin")
        ax.tick_params(axis="x", rotation=35)
    axes[0].legend(frameon=False, fontsize=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_fixed_effort_trajectories(age_effort_summary: pd.DataFrame, path: Path) -> None:
    """Save age trajectories at fixed exact word counts."""

    if age_effort_summary.empty:
        return
    keep_words = ["1", "2", "3", "4", "5", "6"]
    plot = age_effort_summary[age_effort_summary["nb_words_bucket"].isin(keep_words)].copy()
    if plot.empty:
        return
    sns.set_theme(style="whitegrid", context="paper")
    fig, axes = plt.subplots(2, 3, figsize=(16, 8.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, word in zip(axes.ravel(), keep_words):
        sub = plot[plot["nb_words_bucket"].eq(word)]
        for label in SOURCE_ORDER:
            group = sub[sub["source_label"].eq(label)].sort_values("age_bin_mid")
            if group.empty:
                continue
            ax.plot(
                group["age_bin"].astype(str),
                group["mean_sum_bits"],
                marker="o",
                linewidth=2.4 if label == "Real child" else 1.5,
                color=SOURCE_PALETTE.get(label),
                label=label,
            )
        ax.set_title(f"{word} word{'s' if word != '1' else ''}")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Mean Mistral k3 bits")
        ax.tick_params(axis="x", rotation=35)
    axes[0, 0].legend(frameon=False, fontsize=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_response_entropy_panels(entropy_summary: pd.DataFrame, path: Path) -> None:
    """Save source means across response-entropy bins."""

    if entropy_summary.empty or "response_entropy_bin" not in entropy_summary.columns:
        return
    plot = entropy_summary[~entropy_summary["response_entropy_bin"].eq("missing")].copy()
    if plot.empty:
        return
    order = [label for label in ["low", "mid-low", "mid-high", "high", "all"] if label in set(plot["response_entropy_bin"])]
    sns.set_theme(style="whitegrid", context="talk")
    metrics = [
        ("mean_sum_bits", "Mean Mistral k3 bits"),
        ("mean_nb_words", "Mean words"),
        ("mean_bits_per_word", "Mean bits per word"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), sharex=True, constrained_layout=True)
    for ax, (metric, ylabel) in zip(axes, metrics):
        for label in SOURCE_ORDER:
            group = plot[plot["source_label"].eq(label)].copy()
            if group.empty or metric not in group.columns:
                continue
            group["response_entropy_bin"] = pd.Categorical(group["response_entropy_bin"], categories=order, ordered=True)
            group = group.sort_values("response_entropy_bin")
            ax.plot(
                group["response_entropy_bin"].astype(str),
                group[metric],
                marker="o",
                linewidth=2.6 if label == "Real child" else 1.8,
                color=SOURCE_PALETTE.get(label),
                label=label,
            )
        ax.set_xlabel("Mistral response entropy bin")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=20)
    axes[0].legend(frameon=False, fontsize=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_pairwise_gap_plot(pairwise_summary: pd.DataFrame, path: Path) -> None:
    """Save same-utterance real-vs-baseline gap trajectories."""

    if pairwise_summary.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.8), sharex=True, constrained_layout=True)
    for label in SOURCE_ORDER:
        if label == "Real child":
            continue
        group = pairwise_summary[pairwise_summary["source_label"].eq(label)].sort_values("age_bin_mid")
        if group.empty:
            continue
        axes[0].plot(
            group["age_bin"].astype(str),
            group["mean_control_minus_real_k3_bits"],
            marker="o",
            color=SOURCE_PALETTE.get(label),
            label=label,
        )
        axes[1].plot(
            group["age_bin"].astype(str),
            group["baseline_higher_k3_bits_rate"],
            marker="o",
            color=SOURCE_PALETTE.get(label),
            label=label,
        )
    axes[0].axhline(0, color="#333", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Control minus real Mistral k3 bits")
    axes[1].axhline(0.5, color="#333", linestyle="--", linewidth=1)
    axes[1].set_ylabel("Share controls higher than real")
    for ax in axes:
        ax.set_xlabel("Age bin")
        ax.tick_params(axis="x", rotation=35)
    axes[0].legend(frameon=False, fontsize=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def source_summary_table(source_summary: pd.DataFrame) -> pd.DataFrame:
    """Return compact source-level report rows."""

    if source_summary.empty or "source_label" not in source_summary.columns:
        return pd.DataFrame()
    cols = [
        "source_label",
        "n",
        "mean_sum_bits",
        "mean_nb_words",
        "mean_bits_per_word",
        "mean_response_entropy_bits",
    ]
    available = [col for col in cols if col in source_summary.columns]
    out = source_summary[available].copy()
    out["source_label"] = pd.Categorical(out["source_label"], categories=SOURCE_ORDER, ordered=True)
    return out.sort_values("source_label").reset_index(drop=True)


def build_report(
    *,
    report_md: Path,
    report_html: Path,
    input_csv: Path,
    response_space_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    audit: pd.DataFrame,
    source_summary: pd.DataFrame,
    pairwise_summary: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write the Markdown and HTML report."""

    audit_map = dict(zip(audit["metric"], audit["value"]))
    pairwise_head = pairwise_summary[
        [
            "source_label",
            "age_bin",
            "n",
            "mean_control_minus_real_k3_bits",
            "baseline_higher_k3_bits_rate",
            "mean_control_minus_real_context_gain",
        ]
    ].head(56) if not pairwise_summary.empty else pd.DataFrame()
    lines = [
        "# Existing Scored Baseline Efficiency Cloud",
        "",
        "This report uses the cloud we already have: real child utterances, random baselines, n-gram baselines, and additive LSTM baselines, all scored under the same Mistral surprisal model.",
        "It is different from the future Mistral-generated response cloud. Here, the generators are already decoupled from the scorer for random, n-gram, and LSTM baselines.",
        "",
        "## Why This Is Useful Now",
        "",
        "- It gives an immediate information-effort cloud without waiting for Mistral-generated sampled responses to be scored.",
        "- It compares real child utterances to multiple non-Mistral generators under one common scorer.",
        "- It can be used as an early communicative-efficiency visualization: age, effort, and Mistral information in one space.",
        "- Mistral response entropy is retained as a context-level scorer uncertainty predictor, not as independent behavioral evidence.",
        "",
        "## Inputs",
        "",
        f"- Scored long table: `{input_csv}`",
        f"- Response entropy table: `{response_space_csv}`",
        f"- Output directory: `{output_dir}`",
        f"- Figure directory: `{fig_dir}`",
        "",
        "## Audit",
        "",
        (
            f"The builder scanned `{audit_map.get('input_rows_read', 'NA')}` long-table rows and retained "
            f"`{audit_map.get('filtered_child_k3_cloud_rows', 'NA')}` child `k3` cloud rows across "
            f"`{audit_map.get('sources', 'NA')}` sources."
        ),
        "",
        markdown_table(audit, max_rows=20),
        "",
        "## Source-Level Means",
        "",
        markdown_table(source_summary_table(source_summary), max_rows=20),
        "",
        "## Figures",
        "",
    ]
    for label, path in figure_paths.items():
        lines.extend([f"### {label}", "", f"![{label}]({relative_to_doc(path, report_md)})", ""])
    lines.extend(
        [
            "## Same-Utterance Real-Vs-Baseline Gap Summary",
            "",
            "Positive `control minus real` means the generated control has higher Mistral k3 surprisal than the real child utterance for the matched utterance.",
            "",
            markdown_table(pairwise_head, max_rows=80),
            "",
            "## Interpretation Boundary",
            "",
            "- This is an already-scored baseline cloud, not a Mistral sampled-response cloud.",
            "- Random, n-gram, and LSTM utterances are not same-meaning paraphrases; they are matched baseline alternatives or generated utterances under the same child/context rows.",
            "- Response entropy from the Mistral-generated response-space run remains useful as the scorer model's context-level uncertainty, but it should be named that way.",
            "- The future full cloud should include scored Mistral-generated samples as a self-reference condition and, ideally, other-generator samples scored by Mistral as decoupled-generator conditions.",
        ]
    )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(report_md, report_html)


def build_existing_scored_baseline_efficiency_cloud(
    *,
    input_csv: Path,
    response_space_csv: Path,
    pairwise_dir: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    chunksize: int,
    sample_frac: float,
    sample_per_source: int,
    seed: int,
) -> dict[str, Path]:
    """Build all existing scored baseline cloud outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    sample, summaries, audit = read_cloud_products(
        input_csv=input_csv,
        response_space_csv=response_space_csv,
        output_dir=output_dir,
        chunksize=chunksize,
        sample_frac=sample_frac,
        sample_per_source=sample_per_source,
        seed=seed,
    )
    pairwise_summary = read_pairwise_gap_summary(pairwise_dir, output_dir)

    figure_paths = {
        "3D sampled cloud: age, effort, information": fig_dir / "existing_scored_baseline_3d_sampled_cloud.png",
        "3D centroid trajectories by source": fig_dir / "existing_scored_baseline_3d_centroid_trajectories.png",
        "Effort-information sampled facets": fig_dir / "existing_scored_baseline_effort_information_facets.png",
        "Age-bin cloud centroids": fig_dir / "existing_scored_baseline_age_centroids.png",
        "Fixed-word information trajectories": fig_dir / "existing_scored_baseline_fixed_word_trajectories.png",
        "Response-entropy stratified cloud means": fig_dir / "existing_scored_baseline_response_entropy_panels.png",
        "Same-utterance real-vs-baseline gaps": fig_dir / "existing_scored_baseline_pairwise_gap_by_age.png",
    }
    save_3d_scatter(sample, figure_paths["3D sampled cloud: age, effort, information"])
    save_3d_centroid_trajectory(summaries["age"], figure_paths["3D centroid trajectories by source"])
    save_effort_information_facets(sample, figure_paths["Effort-information sampled facets"])
    save_age_centroid_panels(summaries["age"], figure_paths["Age-bin cloud centroids"])
    save_fixed_effort_trajectories(summaries["age_effort"], figure_paths["Fixed-word information trajectories"])
    save_response_entropy_panels(summaries["response_entropy"], figure_paths["Response-entropy stratified cloud means"])
    save_pairwise_gap_plot(pairwise_summary, figure_paths["Same-utterance real-vs-baseline gaps"])

    build_report(
        report_md=report_md,
        report_html=report_html,
        input_csv=input_csv,
        response_space_csv=response_space_csv,
        output_dir=output_dir,
        fig_dir=fig_dir,
        audit=audit,
        source_summary=summaries["source"],
        pairwise_summary=pairwise_summary,
        figure_paths=figure_paths,
    )

    return {
        "audit": output_dir / "existing_scored_baseline_efficiency_cloud_audit.csv",
        "sample": output_dir / "existing_scored_baseline_efficiency_cloud_sample.csv.gz",
        "source_summary": output_dir / "existing_scored_baseline_efficiency_cloud_summary_by_source.csv",
        "age_summary": output_dir / "existing_scored_baseline_efficiency_cloud_summary_by_age.csv",
        "age_effort_summary": output_dir / "existing_scored_baseline_efficiency_cloud_summary_by_age_effort.csv",
        "response_entropy_summary": output_dir / "existing_scored_baseline_efficiency_cloud_summary_by_response_entropy.csv",
        "pairwise_summary": output_dir / "existing_scored_baseline_pairwise_real_gap_summary.csv",
        "report_md": report_md,
        "report_html": report_html,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--response-space", type=Path, default=DEFAULT_RESPONSE_SPACE)
    parser.add_argument("--pairwise-dir", type=Path, default=DEFAULT_PAIRWISE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--sample-frac", type=float, default=0.04)
    parser.add_argument("--sample-per-source", type=int, default=12_000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    paths = build_existing_scored_baseline_efficiency_cloud(
        input_csv=args.input,
        response_space_csv=args.response_space,
        pairwise_dir=args.pairwise_dir,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
        chunksize=args.chunksize,
        sample_frac=args.sample_frac,
        sample_per_source=args.sample_per_source,
        seed=args.seed,
    )
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
