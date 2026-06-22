#!/usr/bin/env python3
"""Build a Route 1 report contrasting real children with controls.

The report is intentionally comparison-first:

* real child utterances vs random, n-gram, LSTM, and caretaker sources;
* no-context (k0) and contextual (k3) surprisal shown together;
* context gain through age, where gain = k0 sum_bits - k3 sum_bits;
* paired child-source difference models whenever the source is generated from
  the same child utterance.
"""

from __future__ import annotations

import argparse
import gc
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_real_vs_controls_context_report")
DEFAULT_FIG_DIR = Path("figs/route1_real_vs_controls_context_report")
DEFAULT_DOC_MD = Path("docs/route1_real_vs_controls_context_report.md")
DEFAULT_DOC_HTML = Path("docs/route1_real_vs_controls_context_report.html")
DEFAULT_INDEX = Path("docs/route1_current_reports_browser_index.html")
DEFAULT_SOURCE_ATLAS_DIR = Path("results/route1_source_specific_corrected_fixed_effort_atlas")
DEFAULT_CARETAKER_ATLAS_DIR = Path("results/route1_caretaker_atlas/full_fit")

CHILD_SOURCES = (
    "real",
    "random",
    "unigram",
    "bigram",
    "trigram",
    "lstm_additive_k3_same_length",
    "lstm_additive_k4_same_length",
    "lstm_additive_k5_same_length",
)
COMPARISON_SECTIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("random", "Real vs Random", ("random",)),
    ("unigram", "Real vs Unigram", ("unigram",)),
    ("bigram", "Real vs Bigram", ("bigram",)),
    ("trigram", "Real vs Trigram", ("trigram",)),
    (
        "lstm",
        "Real vs LSTMs",
        (
            "lstm_additive_k3_same_length",
            "lstm_additive_k4_same_length",
            "lstm_additive_k5_same_length",
        ),
    ),
    ("caretaker", "Real vs Caretakers", ("caretaker",)),
)

SOURCE_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
    "lstm_additive_k3_same_length": "LSTM k3",
    "lstm_additive_k4_same_length": "LSTM k4",
    "lstm_additive_k5_same_length": "LSTM k5",
    "caretaker": "Caretaker",
}
SOURCE_COLORS = {
    "real": "#1f2d30",
    "random": "#c44536",
    "unigram": "#7b4f9f",
    "bigram": "#3b7dd8",
    "trigram": "#1f9a8a",
    "lstm_additive_k3_same_length": "#c78c1f",
    "lstm_additive_k4_same_length": "#e07a1f",
    "lstm_additive_k5_same_length": "#7a9f2f",
    "caretaker": "#7f7f7f",
}
PRIMARY_LINE_MODEL = "M2"
PRIMARY_CARETAKER_LINE_MODEL = "CM2"
REGRESSION_EFFORT_COL = "nb_words"
REGRESSION_CONTEXT_K = "k3"
REGRESSION_EFFORT_VALUES = (2, 6, 10)
REGRESSION_MODEL_IDS = ("M2", "M3", "M4c", "M5", "M6", "M7", "M11", "M15")
CARETAKER_MODEL_MAP = {
    "M2": "CM2",
    "M3": "CM3",
    "M4c": "CM4c",
    "M5": "CM5",
    "M6": "CM6",
}
REGRESSION_MODEL_LABELS = {
    "M2": "identity + effort",
    "M3": "age x effort",
    "M4c": "question type",
    "M5": "context controls",
    "M6": "context interactions",
    "M7": "nonlinear age",
    "M11": "age x parent effort",
    "M15": "expanded interactions",
}


@dataclass(frozen=True)
class SectionOutput:
    slug: str
    title: str
    sources: tuple[str, ...]
    figures: dict[str, Path]


def slugify(value: object) -> str:
    text = str(value).strip().lower()
    out = []
    for char in text:
        out.append(char if char.isalnum() else "_")
    return "_".join("".join(out).split("_")).strip("_")


def age_bin_sort_key(value: object) -> tuple[int, str]:
    text = str(value)
    try:
        return (int(text.split("-", 1)[0]), text)
    except ValueError:
        return (9999, text)


def context_label(context_k: str) -> str:
    return "No context (k0)" if context_k == "k0" else "With context (k3)"


def truncate_text(value: object, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def fmt_number(value: object, digits: int = 3) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def fmt_p(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if math.isnan(number):
        return ""
    if number < 0.001:
        return "<.001"
    return f"{number:.3f}"


def md_table(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.loc[:, list(columns)] if columns else frame.copy()
    text = view.fillna("").astype(str)
    headers = list(text.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in text.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def coerce_numeric(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def read_source_wide(
    input_csv: Path,
    *,
    target_variant: str,
    role: str,
    chunksize: int,
    include_text: bool = False,
) -> pd.DataFrame:
    """Read k0/k3 rows for one source and return one row per utterance."""

    base_cols = [
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
        "nb_words",
    ]
    text_cols = ["target_utterance_clean", "context_text"] if include_text else []
    usecols = base_cols + text_cols
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        input_csv,
        usecols=usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        chunk = chunk[
            chunk["role"].eq(role)
            & chunk["target_variant"].eq(target_variant)
            & chunk["context_k"].isin(["k0", "k3"])
        ].copy()
        if chunk.empty:
            continue
        chunk = coerce_numeric(chunk, ["sum_bits", "age_months", "nb_words"])
        parts.append(chunk)
    if not parts:
        return pd.DataFrame()
    data = pd.concat(parts, ignore_index=True)
    del parts
    gc.collect()

    index_cols = [
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "role",
        "target_variant",
        "nb_words",
    ]
    bits = (
        data.pivot_table(index=index_cols, columns="context_k", values="sum_bits", aggfunc="mean")
        .reset_index()
        .rename_axis(None, axis=1)
    )
    bits = bits.rename(columns={"k0": "sum_bits_k0", "k3": "sum_bits_k3"})
    bits = bits.dropna(subset=["sum_bits_k0", "sum_bits_k3"]).copy()
    bits["context_gain"] = bits["sum_bits_k0"] - bits["sum_bits_k3"]
    bits["source"] = target_variant
    bits["source_label"] = SOURCE_LABELS.get(target_variant, target_variant)

    if include_text:
        text = data[data["context_k"].eq("k3")].copy()
        text = text.drop_duplicates(subset=["utterance_id", "target_variant"])
        text = text[["utterance_id", "target_variant", "target_utterance_clean", "context_text"]]
        bits = bits.merge(text, on=["utterance_id", "target_variant"], how="left")
    return bits


def wide_from_long(data: pd.DataFrame) -> pd.DataFrame:
    """Convert one source's k0/k3 long rows to one row per utterance."""

    if data.empty:
        return pd.DataFrame()
    index_cols = [
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "role",
        "target_variant",
        "nb_words",
    ]
    bits = (
        data.pivot_table(index=index_cols, columns="context_k", values="sum_bits", aggfunc="mean")
        .reset_index()
        .rename_axis(None, axis=1)
    )
    bits = bits.rename(columns={"k0": "sum_bits_k0", "k3": "sum_bits_k3"})
    bits = bits.dropna(subset=["sum_bits_k0", "sum_bits_k3"]).copy()
    bits["context_gain"] = bits["sum_bits_k0"] - bits["sum_bits_k3"]
    bits["source"] = bits["target_variant"].astype(str)
    bits["source_label"] = bits["source"].map(lambda source: SOURCE_LABELS.get(source, source))
    return bits


def read_all_sources_wide(input_csv: Path, *, chunksize: int) -> dict[str, pd.DataFrame]:
    """Read all k0/k3 source rows in one decompression pass."""

    wanted = set(CHILD_SOURCES) | {"caretaker"}
    usecols = [
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
        "nb_words",
    ]
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        input_csv,
        usecols=usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        chunk = chunk[chunk["context_k"].isin(["k0", "k3"]) & chunk["target_variant"].isin(wanted)].copy()
        if chunk.empty:
            continue
        chunk = coerce_numeric(chunk, ["sum_bits", "age_months", "nb_words"])
        chunk = chunk.dropna(subset=["sum_bits", "age_months", "nb_words"])
        parts.append(chunk)
    if not parts:
        return {}
    data = pd.concat(parts, ignore_index=True)
    del parts
    gc.collect()
    out: dict[str, pd.DataFrame] = {}
    for source, group in data.groupby("target_variant", sort=False):
        out[str(source)] = wide_from_long(group.copy())
    return out


def source_age_summary(wide: pd.DataFrame) -> pd.DataFrame:
    if wide.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for (source, source_label, age_bin), group in wide.groupby(["source", "source_label", "age_bin"], observed=True):
        rows.append(
            {
                "source": source,
                "source_label": source_label,
                "age_bin": age_bin,
                "age_mid": float(group["age_months"].median()),
                "n": int(len(group)),
                "children": int(group["child_id"].nunique()),
                "mean_sum_bits_k0": float(group["sum_bits_k0"].mean()),
                "mean_sum_bits_k3": float(group["sum_bits_k3"].mean()),
                "mean_context_gain": float(group["context_gain"].mean()),
                "mean_nb_words": float(group["nb_words"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    out["age_bin"] = pd.Categorical(
        out["age_bin"],
        categories=sorted(out["age_bin"].dropna().unique(), key=age_bin_sort_key),
        ordered=True,
    )
    return out.sort_values(["source", "age_bin"]).reset_index(drop=True)


def compare_child_source(real: pd.DataFrame, control: pd.DataFrame) -> pd.DataFrame:
    cols = ["utterance_id", "sum_bits_k0", "sum_bits_k3", "context_gain", "nb_words"]
    comp = real[
        ["utterance_id", "dataset", "child_id", "session_id", "age_months", "age_bin", "nb_words", "sum_bits_k0", "sum_bits_k3", "context_gain"]
    ].merge(
        control[cols + ["source", "source_label"]],
        on="utterance_id",
        how="inner",
        suffixes=("_real", "_control"),
    )
    comp = comp.rename(
        columns={
            "nb_words_real": "child_nb_words",
            "sum_bits_k0_real": "real_sum_bits_k0",
            "sum_bits_k3_real": "real_sum_bits_k3",
            "context_gain_real": "real_context_gain",
            "nb_words_control": "control_nb_words",
            "sum_bits_k0_control": "control_sum_bits_k0",
            "sum_bits_k3_control": "control_sum_bits_k3",
            "context_gain_control": "control_context_gain",
        }
    )
    comp["gap_k0"] = comp["control_sum_bits_k0"] - comp["real_sum_bits_k0"]
    comp["gap_k3"] = comp["control_sum_bits_k3"] - comp["real_sum_bits_k3"]
    comp["gain_gap"] = comp["control_context_gain"] - comp["real_context_gain"]
    return comp


def paired_gap_summary(comp: pd.DataFrame) -> pd.DataFrame:
    if comp.empty:
        return pd.DataFrame()
    rows = []
    for (source, source_label, age_bin), group in comp.groupby(["source", "source_label", "age_bin"], observed=True):
        rows.append(
            {
                "source": source,
                "source_label": source_label,
                "age_bin": age_bin,
                "age_mid": float(group["age_months"].median()),
                "n": int(len(group)),
                "mean_gap_k0": float(group["gap_k0"].mean()),
                "mean_gap_k3": float(group["gap_k3"].mean()),
                "mean_real_context_gain": float(group["real_context_gain"].mean()),
                "mean_control_context_gain": float(group["control_context_gain"].mean()),
                "mean_gain_gap": float(group["gain_gap"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    out["age_bin"] = pd.Categorical(
        out["age_bin"],
        categories=sorted(out["age_bin"].dropna().unique(), key=age_bin_sort_key),
        ordered=True,
    )
    return out.sort_values(["source", "age_bin"]).reset_index(drop=True)


def fit_clustered_model(frame: pd.DataFrame, outcome: str, *, source: str, model_kind: str) -> dict[str, object]:
    needed = [outcome, "age_months", "child_nb_words", "child_id"]
    data = frame.dropna(subset=needed).copy()
    data = data[np.isfinite(data[outcome]) & np.isfinite(data["age_months"]) & np.isfinite(data["child_nb_words"])]
    if data.empty or data["child_id"].nunique() < 2:
        return {"source": source, "model_kind": model_kind, "outcome": outcome, "status": "no_fit"}
    data["age_c"] = data["age_months"] - data["age_months"].mean()
    data["effort_c"] = data["child_nb_words"] - data["child_nb_words"].mean()
    result = smf.ols(f"{outcome} ~ age_c + effort_c + C(child_id)", data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["child_id"]}
    )
    return {
        "source": source,
        "source_label": SOURCE_LABELS.get(source, source),
        "model_kind": model_kind,
        "outcome": outcome,
        "status": "fit",
        "n": int(len(data)),
        "children": int(data["child_id"].nunique()),
        "mean_outcome": float(data[outcome].mean()),
        "age_coef": float(result.params.get("age_c", math.nan)),
        "age_p": float(result.pvalues.get("age_c", math.nan)),
        "effort_coef": float(result.params.get("effort_c", math.nan)),
        "effort_p": float(result.pvalues.get("effort_c", math.nan)),
        "r2": float(getattr(result, "rsquared", math.nan)),
    }


def fit_caretaker_source_model(frame: pd.DataFrame, outcome: str) -> dict[str, object]:
    data = frame.dropna(subset=[outcome, "age_months", "nb_words", "child_id", "source"]).copy()
    data = data[np.isfinite(data[outcome]) & np.isfinite(data["age_months"]) & np.isfinite(data["nb_words"])]
    if data.empty:
        return {"source": "caretaker", "model_kind": "source_interaction", "outcome": outcome, "status": "no_fit"}
    data["is_caretaker"] = data["source"].eq("caretaker").astype(int)
    data["age_c"] = data["age_months"] - data["age_months"].mean()
    data["effort_c"] = data["nb_words"] - data["nb_words"].mean()
    result = smf.ols(f"{outcome} ~ is_caretaker + age_c + is_caretaker:age_c + effort_c + C(child_id)", data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["child_id"]}
    )
    return {
        "source": "caretaker",
        "source_label": "Caretaker",
        "model_kind": "source_interaction",
        "outcome": outcome,
        "status": "fit",
        "n": int(len(data)),
        "children": int(data["child_id"].nunique()),
        "mean_real": float(data.loc[data["source"].eq("real"), outcome].mean()),
        "mean_control": float(data.loc[data["source"].eq("caretaker"), outcome].mean()),
        "source_coef": float(result.params.get("is_caretaker", math.nan)),
        "source_p": float(result.pvalues.get("is_caretaker", math.nan)),
        "source_age_coef": float(result.params.get("is_caretaker:age_c", math.nan)),
        "source_age_p": float(result.pvalues.get("is_caretaker:age_c", math.nan)),
        "r2": float(getattr(result, "rsquared", math.nan)),
    }


def plot_context_condition_means(summary: pd.DataFrame, sources: Sequence[str], title: str, path: Path) -> None:
    rows = []
    for _, row in summary[summary["source"].isin(sources)].iterrows():
        rows.append({**row.to_dict(), "context": "k0", "mean_sum_bits": row["mean_sum_bits_k0"]})
        rows.append({**row.to_dict(), "context": "k3", "mean_sum_bits": row["mean_sum_bits_k3"]})
    plot = pd.DataFrame(rows)
    plot["context_label"] = plot["context"].map(context_label)
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    for ax, context in zip(axes, ["k0", "k3"]):
        panel = plot[plot["context"].eq(context)]
        for source in sources:
            line = panel[panel["source"].eq(source)].sort_values("age_mid")
            if line.empty:
                continue
            ax.plot(
                line["age_bin"].astype(str),
                line["mean_sum_bits"],
                marker="o",
                linewidth=2.4,
                label=SOURCE_LABELS.get(source, source),
                color=SOURCE_COLORS.get(source),
            )
        ax.set_title(context_label(context))
        ax.set_xlabel("Child age bin")
        ax.tick_params(axis="x", rotation=35)
    axes[0].set_ylabel("Mean utterance sum_bits")
    axes[1].legend(frameon=False, loc="best")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_with_context_focus(summary: pd.DataFrame, sources: Sequence[str], title: str, path: Path) -> None:
    plot = summary[summary["source"].isin(sources)].copy().sort_values(["source", "age_mid"])
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 6))
    for source in sources:
        line = plot[plot["source"].eq(source)]
        if line.empty:
            continue
        ax.plot(
            line["age_bin"].astype(str),
            line["mean_sum_bits_k3"],
            marker="o",
            linewidth=2.5,
            label=SOURCE_LABELS.get(source, source),
            color=SOURCE_COLORS.get(source),
        )
    ax.set_title(title)
    ax.set_xlabel("Child age bin")
    ax.set_ylabel("Mean sum_bits with k3 context")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_context_gain(summary: pd.DataFrame, sources: Sequence[str], title: str, path: Path) -> None:
    plot = summary[summary["source"].isin(sources)].copy().sort_values(["source", "age_mid"])
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 6))
    for source in sources:
        line = plot[plot["source"].eq(source)]
        if line.empty:
            continue
        ax.plot(
            line["age_bin"].astype(str),
            line["mean_context_gain"],
            marker="o",
            linewidth=2.5,
            label=SOURCE_LABELS.get(source, source),
            color=SOURCE_COLORS.get(source),
        )
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Child age bin")
    ax.set_ylabel("Context gain: k0 sum_bits - k3 sum_bits")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_gap_summary(gap_summary: pd.DataFrame, sources: Sequence[str], title: str, path: Path, *, caretaker: bool = False) -> None:
    plot = gap_summary[gap_summary["source"].isin(sources)].copy().sort_values(["source", "age_mid"])
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(17, 6), sharex=True)
    if caretaker:
        gap_col = "mean_gap_k3"
        gain_col = "mean_gain_gap"
    else:
        gap_col = "mean_gap_k3"
        gain_col = "mean_gain_gap"
    for source in sources:
        line = plot[plot["source"].eq(source)]
        if line.empty:
            continue
        label = SOURCE_LABELS.get(source, source)
        color = SOURCE_COLORS.get(source)
        axes[0].plot(line["age_bin"].astype(str), line[gap_col], marker="o", linewidth=2.4, label=label, color=color)
        axes[1].plot(line["age_bin"].astype(str), line[gain_col], marker="o", linewidth=2.4, label=label, color=color)
    for ax in axes:
        ax.axhline(0, color="#333333", linewidth=1)
        ax.set_xlabel("Child age bin")
        ax.tick_params(axis="x", rotation=35)
    axes[0].set_title("With-context unpredictability gap")
    axes[0].set_ylabel("Control/caretaker k3 mean - real k3 mean")
    axes[1].set_title("Context-gain gap")
    axes[1].set_ylabel("Control/caretaker gain - real child gain")
    axes[1].legend(frameon=False, loc="best")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def atlas_source_dir(source: str, source_atlas_dir: Path, caretaker_atlas_dir: Path) -> Path:
    if source == "caretaker":
        return caretaker_atlas_dir
    return source_atlas_dir / source


def read_regression_predictions(
    source: str,
    *,
    source_atlas_dir: Path,
    caretaker_atlas_dir: Path,
    primary_only: bool = False,
) -> pd.DataFrame:
    """Read saved Atlas fixed-effort prediction lines for one source."""

    directory = atlas_source_dir(source, source_atlas_dir, caretaker_atlas_dir)
    path = (
        directory / "caretaker_fixed_effort_predictions.csv.gz"
        if source == "caretaker"
        else directory / "fixed_effort_predictions.csv.gz"
    )
    if not path.exists():
        return pd.DataFrame()
    usecols = [
        "age_months",
        "fixed_effort_value",
        "atlas_bin",
        "model_id",
        "effort_col",
        "predicted_sum_bits",
        "target_source",
        "context_k",
        "model_label",
        "effort_label",
    ]
    data = pd.read_csv(path, usecols=usecols)
    wanted_models = [PRIMARY_CARETAKER_LINE_MODEL] if source == "caretaker" else [PRIMARY_LINE_MODEL]
    if not primary_only:
        wanted_models = list(CARETAKER_MODEL_MAP.values()) if source == "caretaker" else list(REGRESSION_MODEL_IDS)
    data = data[
        data["context_k"].eq(REGRESSION_CONTEXT_K)
        & data["effort_col"].eq(REGRESSION_EFFORT_COL)
        & data["model_id"].isin(wanted_models)
        & data["fixed_effort_value"].isin(REGRESSION_EFFORT_VALUES)
    ].copy()
    if data.empty:
        return data
    data["source"] = source
    data["source_label"] = SOURCE_LABELS.get(source, source)
    if source == "caretaker":
        reverse_map = {value: key for key, value in CARETAKER_MODEL_MAP.items()}
        data["common_model_id"] = data["model_id"].map(reverse_map).fillna(data["model_id"])
    else:
        data["common_model_id"] = data["model_id"]
    data["common_model_label"] = data["common_model_id"].map(lambda model: REGRESSION_MODEL_LABELS.get(model, model))
    return data


def read_regression_slopes(
    source: str,
    *,
    source_atlas_dir: Path,
    caretaker_atlas_dir: Path,
) -> pd.DataFrame:
    """Read saved Atlas fixed-effort age slopes for one source."""

    directory = atlas_source_dir(source, source_atlas_dir, caretaker_atlas_dir)
    path = (
        directory / "caretaker_fixed_slice_slopes.csv"
        if source == "caretaker"
        else directory / "fixed_slice_slopes.csv"
    )
    if not path.exists():
        return pd.DataFrame()
    data = pd.read_csv(path)
    wanted_models = list(CARETAKER_MODEL_MAP.values()) if source == "caretaker" else list(REGRESSION_MODEL_IDS)
    data = data[
        data["context_k"].eq(REGRESSION_CONTEXT_K)
        & data["effort_col"].eq(REGRESSION_EFFORT_COL)
        & data["model_id"].isin(wanted_models)
    ].copy()
    if data.empty:
        return data
    data["source"] = source
    data["source_label"] = SOURCE_LABELS.get(source, source)
    if source == "caretaker":
        reverse_map = {value: key for key, value in CARETAKER_MODEL_MAP.items()}
        data["common_model_id"] = data["model_id"].map(reverse_map).fillna(data["model_id"])
    else:
        data["common_model_id"] = data["model_id"]
    data["common_model_label"] = data["common_model_id"].map(lambda model: REGRESSION_MODEL_LABELS.get(model, model))
    return data


def load_regression_artifacts(
    sources: Sequence[str],
    *,
    source_atlas_dir: Path,
    caretaker_atlas_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_sources = ["real", *[source for source in sources if source != "real"]]
    predictions = []
    slopes = []
    for source in all_sources:
        predictions.append(
            read_regression_predictions(
                source,
                source_atlas_dir=source_atlas_dir,
                caretaker_atlas_dir=caretaker_atlas_dir,
                primary_only=True,
            )
        )
        slopes.append(
            read_regression_slopes(
                source,
                source_atlas_dir=source_atlas_dir,
                caretaker_atlas_dir=caretaker_atlas_dir,
            )
        )
    pred = pd.concat([item for item in predictions if not item.empty], ignore_index=True) if predictions else pd.DataFrame()
    slope = pd.concat([item for item in slopes if not item.empty], ignore_index=True) if slopes else pd.DataFrame()
    return pred, slope


def trim_predictions_to_common_age(predictions: pd.DataFrame, sources: Sequence[str]) -> pd.DataFrame:
    if predictions.empty:
        return predictions
    wanted = ["real", *[source for source in sources if source != "real"]]
    view = predictions[predictions["source"].isin(wanted)].copy()
    if view.empty or view["source"].nunique() < 2:
        return view
    bounds = view.groupby("source")["age_months"].agg(["min", "max"])
    min_age = float(bounds["min"].max())
    max_age = float(bounds["max"].min())
    return view[view["age_months"].between(min_age, max_age)].copy()


def plot_fixed_effort_regression_lines(predictions: pd.DataFrame, sources: Sequence[str], title: str, path: Path) -> None:
    plot = trim_predictions_to_common_age(predictions, sources)
    if plot.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, len(REGRESSION_EFFORT_VALUES), figsize=(18, 5.5), sharey=True)
    if len(REGRESSION_EFFORT_VALUES) == 1:
        axes = [axes]
    order = ["real", *[source for source in sources if source != "real"]]
    for ax, effort_value in zip(axes, REGRESSION_EFFORT_VALUES):
        panel = plot[plot["fixed_effort_value"].eq(effort_value)]
        for source in order:
            line = panel[panel["source"].eq(source)].sort_values("age_months")
            if line.empty:
                continue
            ax.plot(
                line["age_months"],
                line["predicted_sum_bits"],
                linewidth=2.5,
                label=SOURCE_LABELS.get(source, source),
                color=SOURCE_COLORS.get(source),
            )
        ax.set_title(f"{int(effort_value)} words")
        ax.set_xlabel("Age in months")
    axes[0].set_ylabel("Predicted k3 sum_bits")
    axes[-1].legend(frameon=False, loc="best")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def prediction_gap_lines(predictions: pd.DataFrame, sources: Sequence[str]) -> pd.DataFrame:
    plot = trim_predictions_to_common_age(predictions, sources)
    if plot.empty:
        return pd.DataFrame()
    rows = []
    for effort_value in REGRESSION_EFFORT_VALUES:
        real_line = (
            plot[plot["source"].eq("real") & plot["fixed_effort_value"].eq(effort_value)]
            .sort_values("age_months")
            .copy()
        )
        if real_line.empty:
            continue
        real_ages = real_line["age_months"].to_numpy(dtype=float)
        real_pred = real_line["predicted_sum_bits"].to_numpy(dtype=float)
        for source in sources:
            source_line = (
                plot[plot["source"].eq(source) & plot["fixed_effort_value"].eq(effort_value)]
                .sort_values("age_months")
                .copy()
            )
            if source_line.empty:
                continue
            source_ages = source_line["age_months"].to_numpy(dtype=float)
            source_pred = source_line["predicted_sum_bits"].to_numpy(dtype=float)
            valid = (real_ages >= source_ages.min()) & (real_ages <= source_ages.max())
            if not np.any(valid):
                continue
            interp_source = np.interp(real_ages[valid], source_ages, source_pred)
            for age, gap in zip(real_ages[valid], interp_source - real_pred[valid]):
                rows.append(
                    {
                        "source": source,
                        "source_label": SOURCE_LABELS.get(source, source),
                        "age_months": age,
                        "fixed_effort_value": effort_value,
                        "predicted_gap": gap,
                    }
                )
    return pd.DataFrame(rows)


def plot_regression_gap_lines(predictions: pd.DataFrame, sources: Sequence[str], title: str, path: Path) -> pd.DataFrame:
    gaps = prediction_gap_lines(predictions, sources)
    if gaps.empty:
        return gaps
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, len(REGRESSION_EFFORT_VALUES), figsize=(18, 5.5), sharey=True)
    if len(REGRESSION_EFFORT_VALUES) == 1:
        axes = [axes]
    for ax, effort_value in zip(axes, REGRESSION_EFFORT_VALUES):
        panel = gaps[gaps["fixed_effort_value"].eq(effort_value)]
        for source in sources:
            line = panel[panel["source"].eq(source)].sort_values("age_months")
            if line.empty:
                continue
            ax.plot(
                line["age_months"],
                line["predicted_gap"],
                linewidth=2.5,
                label=SOURCE_LABELS.get(source, source),
                color=SOURCE_COLORS.get(source),
            )
        ax.axhline(0, color="#333333", linewidth=1)
        ax.set_title(f"{int(effort_value)} words")
        ax.set_xlabel("Age in months")
    axes[0].set_ylabel("Predicted source - real k3 bits")
    axes[-1].legend(frameon=False, loc="best")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return gaps


def slope_difference_summary(slopes: pd.DataFrame, sources: Sequence[str]) -> pd.DataFrame:
    if slopes.empty:
        return slopes
    summary = (
        slopes.groupby(["source", "source_label", "common_model_id", "common_model_label"], as_index=False)
        .agg(
            mean_slope_bits_per_6_months=("slope_bits_per_6_months", "mean"),
            downward_lines=("direction", lambda values: int((values == "downward").sum())),
            upward_lines=("direction", lambda values: int((values == "upward").sum())),
            total_lines=("direction", "size"),
        )
    )
    real = summary[summary["source"].eq("real")][
        ["common_model_id", "mean_slope_bits_per_6_months", "downward_lines", "upward_lines", "total_lines"]
    ].rename(
        columns={
            "mean_slope_bits_per_6_months": "real_slope_bits_per_6_months",
            "downward_lines": "real_downward_lines",
            "upward_lines": "real_upward_lines",
            "total_lines": "real_total_lines",
        }
    )
    out = summary[summary["source"].isin(sources)].merge(real, on="common_model_id", how="left")
    out = out.rename(columns={"mean_slope_bits_per_6_months": "source_slope_bits_per_6_months"})
    out["source_minus_real_slope"] = out["source_slope_bits_per_6_months"] - out["real_slope_bits_per_6_months"]
    model_order = {model: idx for idx, model in enumerate(REGRESSION_MODEL_IDS)}
    out["model_order"] = out["common_model_id"].map(lambda model: model_order.get(model, 999))
    return out.sort_values(["model_order", "source"]).reset_index(drop=True)


def plot_model_slope_differences(slope_diff: pd.DataFrame, sources: Sequence[str], title: str, path: Path) -> None:
    plot = slope_diff[slope_diff["source"].isin(sources)].copy()
    if plot.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for source in sources:
        line = plot[plot["source"].eq(source)].sort_values("model_order")
        if line.empty:
            continue
        ax.plot(
            line["common_model_label"],
            line["source_minus_real_slope"],
            marker="o",
            linewidth=2.5,
            label=SOURCE_LABELS.get(source, source),
            color=SOURCE_COLORS.get(source),
        )
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Regression model")
    ax.set_ylabel("Slope diff, bits per 6 months")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout(rect=(0.02, 0.04, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_regression_line_artifacts(
    *,
    section_slug: str,
    title: str,
    sources: Sequence[str],
    source_atlas_dir: Path,
    caretaker_atlas_dir: Path,
    output_dir: Path,
    fig_dir: Path,
) -> tuple[dict[str, Path], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictions, slopes = load_regression_artifacts(
        sources,
        source_atlas_dir=source_atlas_dir,
        caretaker_atlas_dir=caretaker_atlas_dir,
    )
    figures = {
        "regression_lines": fig_dir / f"{section_slug}_m2_k3_fixed_word_regression_lines.png",
        "regression_gaps": fig_dir / f"{section_slug}_m2_k3_fixed_word_regression_gaps.png",
        "slope_differences": fig_dir / f"{section_slug}_k3_word_model_slope_differences.png",
    }
    if not predictions.empty:
        plot_fixed_effort_regression_lines(
            predictions,
            sources,
            f"{title}: model-based k3 regression lines at fixed word counts",
            figures["regression_lines"],
        )
    gap_lines = plot_regression_gap_lines(
        predictions,
        sources,
        f"{title}: model-based source-minus-real line gaps",
        figures["regression_gaps"],
    )
    slope_diff = slope_difference_summary(slopes, sources)
    if not slope_diff.empty:
        plot_model_slope_differences(
            slope_diff,
            sources,
            f"{title}: slope differences across model variants",
            figures["slope_differences"],
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    if not predictions.empty:
        predictions.to_csv(output_dir / f"{section_slug}_regression_line_predictions.csv", index=False)
    if not slopes.empty:
        slopes.to_csv(output_dir / f"{section_slug}_regression_line_slopes.csv", index=False)
    if not slope_diff.empty:
        slope_diff.to_csv(output_dir / f"{section_slug}_regression_line_slope_differences.csv", index=False)
    if not gap_lines.empty:
        gap_lines.to_csv(output_dir / f"{section_slug}_regression_line_gaps.csv", index=False)
    return figures, predictions, slope_diff, gap_lines


def caretaker_gap_summary(real: pd.DataFrame, caretaker: pd.DataFrame) -> pd.DataFrame:
    real_summary = source_age_summary(real)
    caretaker_summary = source_age_summary(caretaker)
    merged = real_summary[real_summary["source"].eq("real")].merge(
        caretaker_summary[caretaker_summary["source"].eq("caretaker")],
        on="age_bin",
        suffixes=("_real", "_control"),
        how="inner",
    )
    rows = []
    for _, row in merged.iterrows():
        rows.append(
            {
                "source": "caretaker",
                "source_label": "Caretaker",
                "age_bin": row["age_bin"],
                "age_mid": row["age_mid_real"],
                "n": int(row["n_control"]),
                "mean_gap_k0": row["mean_sum_bits_k0_control"] - row["mean_sum_bits_k0_real"],
                "mean_gap_k3": row["mean_sum_bits_k3_control"] - row["mean_sum_bits_k3_real"],
                "mean_real_context_gain": row["mean_context_gain_real"],
                "mean_control_context_gain": row["mean_context_gain_control"],
                "mean_gain_gap": row["mean_context_gain_control"] - row["mean_context_gain_real"],
            }
        )
    return pd.DataFrame(rows)


def select_examples(comp: pd.DataFrame, source: str, n: int) -> pd.DataFrame:
    if comp.empty:
        return pd.DataFrame()
    view = comp.copy()
    view = view[np.isfinite(view["gap_k3"])].copy()
    view = view[view["gap_k3"].gt(0)]
    if view.empty:
        return pd.DataFrame()
    view["example_score"] = view["gap_k3"] + 0.25 * view["real_context_gain"].clip(lower=0)
    chosen = (
        view.sort_values(["example_score", "gap_k3"], ascending=False)
        .drop_duplicates(subset=["child_id", "age_bin"], keep="first")
        .head(n)
        .copy()
    )
    chosen["source"] = source
    return chosen


def fetch_texts(input_csv: Path, requests: set[tuple[str, str]], *, chunksize: int) -> dict[tuple[str, str], dict[str, str]]:
    if not requests:
        return {}
    variants = {source for source, _ in requests}
    utterances = {utt for _, utt in requests}
    usecols = ["utterance_id", "target_variant", "context_k", "target_utterance_clean", "context_text"]
    found: dict[tuple[str, str], dict[str, str]] = {}
    for chunk in pd.read_csv(
        input_csv,
        usecols=usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        chunk = chunk[
            chunk["context_k"].eq("k3")
            & chunk["target_variant"].isin(variants)
            & chunk["utterance_id"].isin(utterances)
        ].copy()
        if chunk.empty:
            continue
        for row in chunk.itertuples(index=False):
            key = (str(row.target_variant), str(row.utterance_id))
            if key not in requests or key in found:
                continue
            found[key] = {
                "target_utterance_clean": str(row.target_utterance_clean),
                "context_text": str(row.context_text),
            }
        if len(found) >= len(requests):
            break
    return found


def enrich_examples(input_csv: Path, examples: pd.DataFrame, *, chunksize: int) -> pd.DataFrame:
    if examples.empty:
        return examples
    requests: set[tuple[str, str]] = set()
    for row in examples.itertuples(index=False):
        requests.add(("real", str(row.utterance_id)))
        requests.add((str(row.source), str(row.utterance_id)))
    texts = fetch_texts(input_csv, requests, chunksize=chunksize)
    rows = []
    for row in examples.itertuples(index=False):
        real_text = texts.get(("real", str(row.utterance_id)), {})
        source_text = texts.get((str(row.source), str(row.utterance_id)), {})
        rows.append(
            {
                "source": str(row.source),
                "source_label": SOURCE_LABELS.get(str(row.source), str(row.source)),
                "dataset": row.dataset,
                "child_id": row.child_id,
                "age_months": fmt_number(row.age_months, 1),
                "age_bin": row.age_bin,
                "context": truncate_text(real_text.get("context_text", "")),
                "real_child_utterance": truncate_text(real_text.get("target_utterance_clean", ""), 120),
                "control_utterance": truncate_text(source_text.get("target_utterance_clean", ""), 120),
                "real_k3_bits": fmt_number(row.real_sum_bits_k3, 2),
                "control_k3_bits": fmt_number(row.control_sum_bits_k3, 2),
                "control_minus_real_k3": fmt_number(row.gap_k3, 2),
                "real_context_gain": fmt_number(row.real_context_gain, 2),
                "control_context_gain": fmt_number(row.control_context_gain, 2),
            }
        )
    return pd.DataFrame(rows)


def select_unpaired_source_examples(wide: pd.DataFrame, source: str, n: int) -> pd.DataFrame:
    view = wide[wide["source"].eq(source)].copy()
    if view.empty:
        return pd.DataFrame()
    view = view.sort_values("context_gain", ascending=False).drop_duplicates(subset=["child_id", "age_bin"]).head(n)
    return view


def enrich_unpaired_examples(input_csv: Path, examples: pd.DataFrame, *, chunksize: int) -> pd.DataFrame:
    if examples.empty:
        return examples
    requests = {(str(row.source), str(row.utterance_id)) for row in examples.itertuples(index=False)}
    texts = fetch_texts(input_csv, requests, chunksize=chunksize)
    rows = []
    for row in examples.itertuples(index=False):
        text = texts.get((str(row.source), str(row.utterance_id)), {})
        rows.append(
            {
                "source": SOURCE_LABELS.get(str(row.source), str(row.source)),
                "dataset": row.dataset,
                "child_id": row.child_id,
                "age_months": fmt_number(row.age_months, 1),
                "age_bin": row.age_bin,
                "context": truncate_text(text.get("context_text", "")),
                "utterance": truncate_text(text.get("target_utterance_clean", ""), 130),
                "k3_bits": fmt_number(row.sum_bits_k3, 2),
                "context_gain": fmt_number(row.context_gain, 2),
                "nb_words": fmt_number(row.nb_words, 0),
            }
        )
    return pd.DataFrame(rows)


def model_summary_for_report(models: pd.DataFrame, sources: Sequence[str]) -> pd.DataFrame:
    view = models[models["source"].isin(sources)].copy()
    if view.empty:
        return view
    out = []
    for row in view.itertuples(index=False):
        if getattr(row, "model_kind", "") == "source_interaction":
            out.append(
                {
                    "source": getattr(row, "source_label", ""),
                    "test": getattr(row, "outcome", ""),
                    "mean": f"real {fmt_number(getattr(row, 'mean_real', math.nan))}; source {fmt_number(getattr(row, 'mean_control', math.nan))}",
                    "age_slope": f"source x age {fmt_number(getattr(row, 'source_age_coef', math.nan))}",
                    "p": fmt_p(getattr(row, "source_age_p", math.nan)),
                    "n": str(int(getattr(row, "n", 0) or 0)),
                }
            )
        else:
            out.append(
                {
                    "source": getattr(row, "source_label", ""),
                    "test": getattr(row, "outcome", ""),
                    "mean": fmt_number(getattr(row, "mean_outcome", math.nan)),
                    "age_slope": fmt_number(getattr(row, "age_coef", math.nan)),
                    "p": fmt_p(getattr(row, "age_p", math.nan)),
                    "n": str(int(getattr(row, "n", 0) or 0)),
                }
            )
    return pd.DataFrame(out)


def primary_slope_takeaway(section_slopes: pd.DataFrame) -> str:
    if section_slopes.empty:
        return ""
    primary = section_slopes[section_slopes["common_model_id"].eq(PRIMARY_LINE_MODEL)].copy()
    if primary.empty:
        return ""
    pieces = []
    for row in primary.itertuples(index=False):
        real = fmt_number(getattr(row, "real_slope_bits_per_6_months", math.nan), 3)
        source = fmt_number(getattr(row, "source_slope_bits_per_6_months", math.nan), 3)
        diff = fmt_number(getattr(row, "source_minus_real_slope", math.nan), 3)
        real_down = int(getattr(row, "real_downward_lines", 0) or 0)
        real_total = int(getattr(row, "real_total_lines", 0) or 0)
        source_down = int(getattr(row, "downward_lines", 0) or 0)
        source_total = int(getattr(row, "total_lines", 0) or 0)
        label = getattr(row, "source_label", "")
        pieces.append(
            f"{label}: source slope {source} vs real slope {real} bits per 6 months "
            f"(source-real {diff}; real {real_down}/{real_total} downward lines, source {source_down}/{source_total})."
        )
    return "Primary fixed-effort slope read under M2/CM2: " + " ".join(pieces)


def build_section_figures(
    *,
    section_slug: str,
    title: str,
    sources: Sequence[str],
    source_summary: pd.DataFrame,
    gap_summary: pd.DataFrame,
    fig_dir: Path,
    caretaker: bool = False,
) -> dict[str, Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    source_list = ("real", *tuple(sources))
    figures = {
        "context_conditions": fig_dir / f"{section_slug}_k0_vs_k3_age_means.png",
        "with_context": fig_dir / f"{section_slug}_k3_with_context_focus.png",
        "context_gain": fig_dir / f"{section_slug}_context_gain_by_age.png",
        "gaps": fig_dir / f"{section_slug}_real_gap_by_age.png",
    }
    plot_context_condition_means(
        source_summary,
        source_list,
        f"{title}: no-context and with-context trajectories",
        figures["context_conditions"],
    )
    plot_with_context_focus(
        source_summary,
        source_list,
        f"{title}: with-context information",
        figures["with_context"],
    )
    plot_context_gain(
        source_summary,
        source_list,
        f"{title}: context gain through age",
        figures["context_gain"],
    )
    plot_gap_summary(
        gap_summary,
        sources,
        f"{title}: control/caretaker minus real child",
        figures["gaps"],
        caretaker=caretaker,
    )
    return figures


def relative_to_doc(path: Path, doc_path: Path) -> str:
    return os.path.relpath(path, start=doc_path.parent)


def build_report_markdown(
    *,
    doc_path: Path,
    sections: Sequence[SectionOutput],
    source_summary: pd.DataFrame,
    gap_summary: pd.DataFrame,
    model_summary: pd.DataFrame,
    regression_slope_summary: pd.DataFrame,
    examples: pd.DataFrame,
    caretaker_examples: pd.DataFrame,
) -> str:
    overview = source_summary[source_summary["source"].isin(["real", "random", "unigram", "bigram", "trigram", "lstm_additive_k3_same_length", "lstm_additive_k4_same_length", "lstm_additive_k5_same_length", "caretaker"])].copy()
    overview_latest = (
        overview.sort_values("age_bin")
        .groupby("source", as_index=False, observed=True)
        .agg(
            rows=("n", "sum"),
            children=("children", "max"),
            mean_k0=("mean_sum_bits_k0", "mean"),
            mean_k3=("mean_sum_bits_k3", "mean"),
            mean_gain=("mean_context_gain", "mean"),
        )
    )
    overview_latest["source"] = overview_latest["source"].map(lambda x: SOURCE_LABELS.get(x, x))
    for col in ["mean_k0", "mean_k3", "mean_gain"]:
        overview_latest[col] = overview_latest[col].map(lambda x: fmt_number(x, 2))
    overview_latest["rows"] = overview_latest["rows"].astype(int).astype(str)
    overview_latest["children"] = overview_latest["children"].astype(int).astype(str)

    lines = [
        "# Route 1: Real Children Versus Baselines, LSTMs, and Caretakers",
        "",
        "This report systematically contrasts real child utterances with matched generated baselines, LSTM same-length baselines, and caretaker speech over the same developmental age bins.",
        "",
        "The main quantities are:",
        "",
        "- **No-context information:** `sum_bits` with `context_k = k0`.",
        "- **With-context information:** `sum_bits` with `context_k = k3`, using the preceding three caretaker utterances.",
        "- **Context gain:** `k0 sum_bits - k3 sum_bits`; positive values mean the preceding context made the target more predictable to the scoring model.",
        "- **Source gap:** source `k3 sum_bits - real-child k3 sum_bits`; positive values mean the source is more unpredictable than the real child utterance under the same context.",
        "- **Regression-line gap:** source model-predicted k3 bits minus real-child model-predicted k3 bits at the same fixed word count.",
        "",
        "For random, n-gram, and LSTM conditions, comparisons are paired by the same original child utterance. Caretaker comparisons are not utterance-paired; they compare caretaker utterances from the same corpus/session age structure.",
        "",
        "The regression-line layer uses the saved corrected fixed-effort Atlas predictions. The primary line plots use the identity-controlled fixed-effort model (`M2` for child sources, `CM2` for caretakers) at 2, 6, and 10 words. The slope-difference plot then asks whether the same downward or upward developmental tendency holds across richer model variants. A downward fixed-effort line means the model predicts fewer information bits at older ages for utterances of the same length.",
        "",
        "## Overview",
        "",
        md_table(overview_latest, ["source", "rows", "children", "mean_k0", "mean_k3", "mean_gain"]),
        "",
    ]

    for section in sections:
        lines.extend(["", f"## {section.title}", ""])
        lines.append(
            "This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age."
        )
        lines.extend(
            [
                "",
                f"![{section.title} k0 vs k3]({relative_to_doc(section.figures['context_conditions'], doc_path)})",
                "",
                f"![{section.title} with context]({relative_to_doc(section.figures['with_context'], doc_path)})",
                "",
                f"![{section.title} context gain]({relative_to_doc(section.figures['context_gain'], doc_path)})",
                "",
                f"![{section.title} gaps]({relative_to_doc(section.figures['gaps'], doc_path)})",
                "",
            ]
        )

        section_models = model_summary_for_report(model_summary, section.sources)
        if not section_models.empty:
            lines.extend(
                [
                    "### Difference Models",
                    "",
                    "For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.",
                    "",
                    md_table(section_models, ["source", "test", "mean", "age_slope", "p", "n"]),
                    "",
                ]
            )

        if {"regression_lines", "regression_gaps", "slope_differences"}.issubset(section.figures):
            lines.extend(
                [
                    "### Fixed-Effort Regression Lines",
                    "",
                    "These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.",
                    "",
                    f"![{section.title} fixed-effort regression lines]({relative_to_doc(section.figures['regression_lines'], doc_path)})",
                    "",
                    f"![{section.title} fixed-effort regression gaps]({relative_to_doc(section.figures['regression_gaps'], doc_path)})",
                    "",
                    f"![{section.title} model slope differences]({relative_to_doc(section.figures['slope_differences'], doc_path)})",
                    "",
                ]
            )
            section_slopes = regression_slope_summary[regression_slope_summary["source"].isin(section.sources)].copy()
            if not section_slopes.empty:
                table = section_slopes.copy()
                table["model"] = table["common_model_id"] + ": " + table["common_model_label"]
                table["real_slope_bits_per_6_months"] = table["real_slope_bits_per_6_months"].map(lambda x: fmt_number(x, 3))
                table["source_slope_bits_per_6_months"] = table["source_slope_bits_per_6_months"].map(lambda x: fmt_number(x, 3))
                table["source_minus_real_slope"] = table["source_minus_real_slope"].map(lambda x: fmt_number(x, 3))
                table["real_line_directions"] = table["real_downward_lines"].astype(int).astype(str) + " down / " + table["real_total_lines"].astype(int).astype(str)
                table["source_line_directions"] = table["downward_lines"].astype(int).astype(str) + " down / " + table["total_lines"].astype(int).astype(str)
                takeaway = primary_slope_takeaway(section_slopes)
                if takeaway:
                    lines.extend([takeaway, ""])
                lines.extend(
                    [
                        "Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.",
                        "",
                        md_table(
                            table,
                            [
                                "source_label",
                                "model",
                                "real_slope_bits_per_6_months",
                                "source_slope_bits_per_6_months",
                                "source_minus_real_slope",
                                "real_line_directions",
                                "source_line_directions",
                            ],
                        ),
                        "",
                    ]
                )

        section_examples = examples[examples["source"].isin(section.sources)].copy()
        if not section_examples.empty:
            lines.extend(
                [
                    "### Matched Examples",
                    "",
                    "These are illustrative matched rows where the real child utterance has much lower with-context surprisal than the control utterance in the same preceding context. They are examples, not statistical tests.",
                    "",
                    md_table(
                        section_examples.head(8),
                        [
                            "source_label",
                            "dataset",
                            "child_id",
                            "age_months",
                            "context",
                            "real_child_utterance",
                            "control_utterance",
                            "real_k3_bits",
                            "control_k3_bits",
                            "control_minus_real_k3",
                            "real_context_gain",
                            "control_context_gain",
                        ],
                    ),
                    "",
                ]
            )

        if section.slug == "caretaker" and not caretaker_examples.empty:
            lines.extend(
                [
                    "### Representative Context-Gain Examples",
                    "",
                    "Caretaker utterances are not matched generated alternatives for the same child row, so examples are shown as representative high context-gain utterances for each source.",
                    "",
                    md_table(
                        caretaker_examples.head(10),
                        ["source", "dataset", "child_id", "age_months", "context", "utterance", "k3_bits", "context_gain", "nb_words"],
                    ),
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "## Saved Artifacts",
            "",
            "```text",
            "results/route1_real_vs_controls_context_report/source_age_summary.csv",
            "results/route1_real_vs_controls_context_report/paired_gap_summary.csv",
            "results/route1_real_vs_controls_context_report/difference_model_summary.csv",
            "results/route1_real_vs_controls_context_report/matched_examples.csv",
            "results/route1_real_vs_controls_context_report/caretaker_examples.csv",
            "results/route1_real_vs_controls_context_report/*_regression_line_predictions.csv",
            "results/route1_real_vs_controls_context_report/*_regression_line_slopes.csv",
            "results/route1_real_vs_controls_context_report/*_regression_line_slope_differences.csv",
            "results/route1_real_vs_controls_context_report/*_regression_line_gaps.csv",
            "figs/route1_real_vs_controls_context_report/",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def update_index(index_path: Path, report_html: Path) -> None:
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    href = report_html.name
    label = "Real vs controls context report"
    if href in text:
        return
    marker = "</ul>"
    item = f'\n<li><a href="{href}">{label}</a></li>'
    if marker in text:
        text = text.replace(marker, item + "\n" + marker, 1)
    else:
        text += item
    index_path.write_text(text, encoding="utf-8")


def run_report(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_md: Path,
    doc_html: Path,
    source_atlas_dir: Path,
    caretaker_atlas_dir: Path,
    chunksize: int,
    examples_per_source: int,
    index_path: Path | None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc_md.parent.mkdir(parents=True, exist_ok=True)

    print("[read] all sources k0/k3 compact rows", flush=True)
    loaded_sources = read_all_sources_wide(input_csv, chunksize=chunksize)
    if "real" not in loaded_sources:
        raise RuntimeError("No real child k0/k3 rows found in input.")
    real = loaded_sources["real"]
    all_source_summaries = [source_age_summary(real)]
    all_gap_summaries: list[pd.DataFrame] = []
    all_models: list[dict[str, object]] = []
    example_candidates: list[pd.DataFrame] = []

    for source in CHILD_SOURCES:
        if source == "real":
            continue
        print(f"[compare] {source}", flush=True)
        control = loaded_sources.get(source, pd.DataFrame())
        if control.empty:
            print(f"[warn] no rows for {source}", flush=True)
            continue
        all_source_summaries.append(source_age_summary(control))
        comp = compare_child_source(real, control)
        comp.to_csv(output_dir / f"{source}_paired_real_comparison.csv.gz", index=False)
        all_gap_summaries.append(paired_gap_summary(comp))
        all_models.append(fit_clustered_model(comp, "gap_k3", source=source, model_kind="paired_gap_k3"))
        all_models.append(fit_clustered_model(comp, "gain_gap", source=source, model_kind="paired_context_gain_gap"))
        example_candidates.append(select_examples(comp, source, examples_per_source))
        del comp
        gc.collect()

    print("[compare] caretaker", flush=True)
    caretaker = loaded_sources.get("caretaker", pd.DataFrame())
    if caretaker.empty:
        raise RuntimeError("No caretaker k0/k3 rows found in input.")
    all_source_summaries.append(source_age_summary(caretaker))
    caretaker_gaps = caretaker_gap_summary(real, caretaker)
    all_gap_summaries.append(caretaker_gaps)
    caretaker_model_frame = pd.concat([real, caretaker], ignore_index=True)
    all_models.append(fit_caretaker_source_model(caretaker_model_frame, "sum_bits_k3"))
    all_models.append(fit_caretaker_source_model(caretaker_model_frame, "context_gain"))

    source_summary = pd.concat(all_source_summaries, ignore_index=True)
    gap_summary = pd.concat(all_gap_summaries, ignore_index=True)
    model_summary = pd.DataFrame(all_models)
    source_summary.to_csv(output_dir / "source_age_summary.csv", index=False)
    gap_summary.to_csv(output_dir / "paired_gap_summary.csv", index=False)
    model_summary.to_csv(output_dir / "difference_model_summary.csv", index=False)

    print("[examples] matched child-source examples", flush=True)
    example_seed = pd.concat(example_candidates, ignore_index=True) if example_candidates else pd.DataFrame()
    examples = enrich_examples(input_csv, example_seed, chunksize=chunksize) if not example_seed.empty else pd.DataFrame()
    examples.to_csv(output_dir / "matched_examples.csv", index=False)

    caretaker_real_examples = select_unpaired_source_examples(real, "real", max(3, examples_per_source // 2))
    caretaker_source_examples = select_unpaired_source_examples(caretaker, "caretaker", max(3, examples_per_source // 2))
    caretaker_examples_seed = pd.concat([caretaker_real_examples, caretaker_source_examples], ignore_index=True)
    caretaker_examples = enrich_unpaired_examples(input_csv, caretaker_examples_seed, chunksize=chunksize)
    caretaker_examples.to_csv(output_dir / "caretaker_examples.csv", index=False)

    sections: list[SectionOutput] = []
    regression_slope_summaries: list[pd.DataFrame] = []
    for slug, title, sources in COMPARISON_SECTIONS:
        print(f"[plot] {title}", flush=True)
        figures = build_section_figures(
            section_slug=slug,
            title=title,
            sources=sources,
            source_summary=source_summary,
            gap_summary=gap_summary,
            fig_dir=fig_dir,
            caretaker=slug == "caretaker",
        )
        regression_figures, _, slope_diff, _ = build_regression_line_artifacts(
            section_slug=slug,
            title=title,
            sources=sources,
            source_atlas_dir=source_atlas_dir,
            caretaker_atlas_dir=caretaker_atlas_dir,
            output_dir=output_dir,
            fig_dir=fig_dir,
        )
        figures.update({key: value for key, value in regression_figures.items() if value.exists()})
        if not slope_diff.empty:
            slope_diff = slope_diff.copy()
            slope_diff["section_slug"] = slug
            slope_diff["section_title"] = title
            regression_slope_summaries.append(slope_diff)
        sections.append(SectionOutput(slug=slug, title=title, sources=sources, figures=figures))
    regression_slope_summary = (
        pd.concat(regression_slope_summaries, ignore_index=True) if regression_slope_summaries else pd.DataFrame()
    )
    if not regression_slope_summary.empty:
        regression_slope_summary.to_csv(output_dir / "regression_line_slope_difference_summary.csv", index=False)

    markdown = build_report_markdown(
        doc_path=doc_md,
        sections=sections,
        source_summary=source_summary,
        gap_summary=gap_summary,
        model_summary=model_summary,
        regression_slope_summary=regression_slope_summary,
        examples=examples,
        caretaker_examples=caretaker_examples,
    )
    doc_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(doc_md, doc_html)
    embedded = doc_md.with_suffix(".embedded.html")
    render_markdown_file(doc_md, embedded, embed_images=True)
    if index_path is not None:
        update_index(index_path, doc_html)
    return {
        "md": doc_md,
        "html": doc_html,
        "embedded_html": embedded,
        "source_summary": output_dir / "source_age_summary.csv",
        "gap_summary": output_dir / "paired_gap_summary.csv",
        "model_summary": output_dir / "difference_model_summary.csv",
        "examples": output_dir / "matched_examples.csv",
    }


def run_report_from_outputs(
    *,
    output_dir: Path,
    fig_dir: Path,
    doc_md: Path,
    doc_html: Path,
    source_atlas_dir: Path,
    caretaker_atlas_dir: Path,
    index_path: Path | None,
) -> dict[str, Path]:
    """Regenerate Markdown/HTML from already saved CSV and figure outputs."""

    source_summary = pd.read_csv(output_dir / "source_age_summary.csv")
    gap_summary = pd.read_csv(output_dir / "paired_gap_summary.csv")
    model_summary = pd.read_csv(output_dir / "difference_model_summary.csv")
    examples = pd.read_csv(output_dir / "matched_examples.csv")
    caretaker_examples = pd.read_csv(output_dir / "caretaker_examples.csv")
    sections: list[SectionOutput] = []
    regression_slope_summaries: list[pd.DataFrame] = []
    for slug, title, sources in COMPARISON_SECTIONS:
        figures = {
            "context_conditions": fig_dir / f"{slug}_k0_vs_k3_age_means.png",
            "with_context": fig_dir / f"{slug}_k3_with_context_focus.png",
            "context_gain": fig_dir / f"{slug}_context_gain_by_age.png",
            "gaps": fig_dir / f"{slug}_real_gap_by_age.png",
        }
        regression_figures, _, slope_diff, _ = build_regression_line_artifacts(
            section_slug=slug,
            title=title,
            sources=sources,
            source_atlas_dir=source_atlas_dir,
            caretaker_atlas_dir=caretaker_atlas_dir,
            output_dir=output_dir,
            fig_dir=fig_dir,
        )
        figures.update({key: value for key, value in regression_figures.items() if value.exists()})
        if not slope_diff.empty:
            slope_diff = slope_diff.copy()
            slope_diff["section_slug"] = slug
            slope_diff["section_title"] = title
            regression_slope_summaries.append(slope_diff)
        sections.append(SectionOutput(slug=slug, title=title, sources=sources, figures=figures))
    regression_slope_summary = (
        pd.concat(regression_slope_summaries, ignore_index=True) if regression_slope_summaries else pd.DataFrame()
    )
    if not regression_slope_summary.empty:
        regression_slope_summary.to_csv(output_dir / "regression_line_slope_difference_summary.csv", index=False)
    markdown = build_report_markdown(
        doc_path=doc_md,
        sections=sections,
        source_summary=source_summary,
        gap_summary=gap_summary,
        model_summary=model_summary,
        regression_slope_summary=regression_slope_summary,
        examples=examples,
        caretaker_examples=caretaker_examples,
    )
    doc_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(doc_md, doc_html)
    embedded = doc_md.with_suffix(".embedded.html")
    render_markdown_file(doc_md, embedded, embed_images=True)
    if index_path is not None:
        update_index(index_path, doc_html)
    return {"md": doc_md, "html": doc_html, "embedded_html": embedded}


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all", "report"), default="all")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--source-atlas-dir", type=Path, default=DEFAULT_SOURCE_ATLAS_DIR)
    parser.add_argument("--caretaker-atlas-dir", type=Path, default=DEFAULT_CARETAKER_ATLAS_DIR)
    parser.add_argument("--chunksize", type=int, default=350_000)
    parser.add_argument("--examples-per-source", type=int, default=5)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--no-index", action="store_true")
    return parser


def main() -> None:
    args = build_cli().parse_args()
    if args.stage == "report":
        outputs = run_report_from_outputs(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            doc_md=args.doc_md,
            doc_html=args.doc_html,
            source_atlas_dir=args.source_atlas_dir,
            caretaker_atlas_dir=args.caretaker_atlas_dir,
            index_path=None if args.no_index else args.index,
        )
    else:
        outputs = run_report(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            doc_md=args.doc_md,
            doc_html=args.doc_html,
            source_atlas_dir=args.source_atlas_dir,
            caretaker_atlas_dir=args.caretaker_atlas_dir,
            chunksize=args.chunksize,
            examples_per_source=args.examples_per_source,
            index_path=None if args.no_index else args.index,
        )
    for path in outputs.values():
        print(path)


if __name__ == "__main__":
    main()
