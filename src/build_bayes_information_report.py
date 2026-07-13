#!/usr/bin/env python3
"""Build a working report for Bayes-decomposed informativeness analyses."""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import sys
from pathlib import Path
from typing import Iterable

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


DEFAULT_BAYES = Path("results/mila_modular_runs_2026_07_08/products/pbm_ngram_bayes_scores/pbm_ngram_bayes_scores.csv.gz")
DEFAULT_COMPLEXITY = Path("results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/pbm_candidate_complexity.csv.gz")
DEFAULT_TRAJECTORY = Path(
    "results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/pbm_real_complexity_trajectory.csv.gz"
)
DEFAULT_AGE_SUMMARY = Path(
    "results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/pbm_real_complexity_age_bin_summary.csv.gz"
)
DEFAULT_MISTRAL = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/bayes_information_report")
DEFAULT_FIG_DIR = Path("figs/bayes_information_report")
DEFAULT_DOC_MD = Path("docs/bayes_information_working_report.md")
DEFAULT_DOC_HTML = Path("docs/bayes_information_working_report.html")

SOURCE_ORDER = ["real", "random", "unigram", "bigram", "trigram"]
SOURCE_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
}
SOURCE_COLORS = {
    "real": "#1f2d30",
    "random": "#c44536",
    "unigram": "#7b4f9f",
    "bigram": "#3b7dd8",
    "trigram": "#1f9a8a",
}
AGE_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
PBM_DATASETS = {"Brown", "Manchester", "Providence"}


def stable_row_uid(row: pd.Series) -> str:
    parts = [
        row.get("dataset", ""),
        row.get("child_id", ""),
        row.get("session_id", ""),
        row.get("file", ""),
        row.get("line_no", ""),
        row.get("utt_id", ""),
    ]
    payload = "\x1f".join("" if pd.isna(part) else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def md_table(frame: pd.DataFrame, *, digits: int = 3) -> str:
    if frame.empty:
        return "_No rows._"
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].map(lambda value: fmt(value, digits))
    text = out.fillna("").astype(str)
    lines = [
        "| " + " | ".join(text.columns) + " |",
        "| " + " | ".join(["---"] * len(text.columns)) + " |",
    ]
    for _, row in text.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in text.columns) + " |")
    return "\n".join(lines)


def rel(path: Path, base: Path) -> str:
    return os.path.relpath(path, start=base.parent).replace(os.sep, "/")


def sem(values: pd.Series) -> float:
    n = values.notna().sum()
    if n <= 1:
        return float("nan")
    return float(values.std(ddof=1) / math.sqrt(n))


def summarize(frame: pd.DataFrame, group_cols: list[str], value_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, group in frame.groupby(group_cols, observed=True, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key))
        row["n"] = len(group)
        for col in value_cols:
            row[f"{col}_mean"] = group[col].mean()
            row[f"{col}_sem"] = sem(group[col])
        rows.append(row)
    return pd.DataFrame(rows)


def read_bayes(path: Path) -> pd.DataFrame:
    usecols = [
        "row_uid",
        "source_model",
        "log2_p_u",
        "log2_p_c_given_u",
        "bayes_bits_unnormalized",
        "utterance_token_count",
        "context_token_count",
        "target_variant",
        "dataset",
        "child_id",
        "source_group",
        "session_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "utt_id",
        "context_id",
    ]
    dtype = {col: "string" for col in usecols if col not in {"log2_p_u", "log2_p_c_given_u", "bayes_bits_unnormalized"}}
    frame = pd.read_csv(path, usecols=usecols, dtype=dtype, low_memory=False)
    for col in ["log2_p_u", "log2_p_c_given_u", "bayes_bits_unnormalized", "utterance_token_count", "context_token_count", "age_months"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["bayes_prior_bits"] = -frame["log2_p_u"]
    frame["bayes_context_bits"] = -frame["log2_p_c_given_u"]
    frame["bayes_bits_per_token"] = frame["bayes_bits_unnormalized"] / frame["utterance_token_count"].replace(0, np.nan)
    frame["bayes_prior_bits_per_token"] = frame["bayes_prior_bits"] / frame["utterance_token_count"].replace(0, np.nan)
    frame["bayes_context_bits_per_token"] = frame["bayes_context_bits"] / frame["context_token_count"].replace(0, np.nan)
    frame["source_model"] = pd.Categorical(frame["source_model"], categories=SOURCE_ORDER, ordered=True)
    frame["age_bin"] = pd.Categorical(frame["age_bin"], categories=AGE_ORDER, ordered=True)
    return frame


def read_complexity(path: Path) -> pd.DataFrame:
    usecols = [
        "row_uid",
        "source_model",
        "orthographic_word_count",
        "orthographic_char_count",
        "mean_word_length",
        "utterance_type_count",
        "estimated_syllable_count",
        "estimated_phoneme_proxy_count",
    ]
    frame = pd.read_csv(path, usecols=usecols, dtype={"row_uid": "string", "source_model": "string"}, low_memory=False)
    for col in [c for c in frame.columns if c not in {"row_uid", "source_model"}]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def read_real_trajectory(path: Path) -> pd.DataFrame:
    usecols = [
        "row_uid",
        "lexical_cumulative_child_vocab_size",
        "lexical_cumulative_child_token_count",
        "lexical_cumulative_child_ttr",
        "lexical_age_bin_vocab_size_so_far",
        "lexical_age_bin_token_count_so_far",
        "lexical_age_bin_ttr_so_far",
    ]
    frame = pd.read_csv(path, usecols=usecols, dtype={"row_uid": "string"}, low_memory=False)
    for col in [c for c in frame.columns if c != "row_uid"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def read_mistral(path: Path, *, chunksize: int) -> tuple[pd.DataFrame, dict[str, int]]:
    usecols = [
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "utt_id",
        "role",
        "target_variant",
        "context_k",
        "sum_bits",
        "mean_bits_per_token",
        "n_eval_tokens",
        "nb_words",
        "context_entropy_bits",
    ]
    parts: list[pd.DataFrame] = []
    raw_counts: dict[str, int] = {}
    for chunk in pd.read_csv(path, usecols=usecols, dtype=str, chunksize=chunksize, keep_default_na=False, low_memory=False):
        mask = (
            chunk["role"].eq("child")
            & chunk["context_k"].eq("k3")
            & chunk["target_variant"].isin(SOURCE_ORDER)
            & chunk["dataset"].isin(PBM_DATASETS)
        )
        sub = chunk.loc[mask].copy()
        if sub.empty:
            continue
        counts = sub["target_variant"].value_counts()
        for key, value in counts.items():
            raw_counts[str(key)] = raw_counts.get(str(key), 0) + int(value)
        sub["source_model"] = sub["target_variant"]
        sub["row_uid"] = sub.apply(stable_row_uid, axis=1)
        sub = sub[
            [
                "row_uid",
                "source_model",
                "sum_bits",
                "mean_bits_per_token",
                "n_eval_tokens",
                "nb_words",
                "context_entropy_bits",
            ]
        ].copy()
        parts.append(sub)
    if not parts:
        raise RuntimeError(f"No PBM child k3 rows found in {path}")
    frame = pd.concat(parts, ignore_index=True)
    for col in ["sum_bits", "mean_bits_per_token", "n_eval_tokens", "nb_words", "context_entropy_bits"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.rename(
        columns={
            "sum_bits": "mistral_sum_bits",
            "mean_bits_per_token": "mistral_bits_per_token",
            "n_eval_tokens": "mistral_eval_tokens",
            "nb_words": "mistral_nb_words",
        }
    )
    frame = frame.drop_duplicates(["row_uid", "source_model"], keep="first")
    return frame, raw_counts


def fit_model(name: str, formula: str, frame: pd.DataFrame, *, sample_n: int | None = 250_000) -> tuple[pd.DataFrame, dict[str, object]]:
    data = frame.replace([np.inf, -np.inf], np.nan).dropna(
        subset=[term.strip() for term in formula.replace("~", "+").replace("*", "+").replace(":", "+").split("+") if term.strip() in frame.columns]
    )
    if sample_n and len(data) > sample_n:
        data = (
            data.groupby("source_model", observed=True, group_keys=False)
            .apply(lambda group: group.sample(max(1, int(sample_n * len(group) / len(frame))), random_state=13))
            .reset_index(drop=True)
        )
    model = smf.ols(formula, data=data).fit(cov_type="HC3")
    table = (
        pd.DataFrame(
            {
                "term": model.params.index,
                "estimate": model.params.values,
                "std_error": model.bse.values,
                "p_value": model.pvalues.values,
            }
        )
        .assign(model=name)
        [["model", "term", "estimate", "std_error", "p_value"]]
    )
    info = {"model": name, "formula": formula, "n": int(model.nobs), "r2": float(model.rsquared)}
    return table, info


def plot_source_age_lines(summary: pd.DataFrame, value_col: str, sem_col: str, title: str, ylabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    x = np.arange(len(AGE_ORDER))
    for source in SOURCE_ORDER:
        sub = summary[summary["source_model"].astype(str).eq(source)].set_index("age_bin").reindex(AGE_ORDER)
        y = sub[value_col].astype(float).to_numpy()
        err = 1.96 * sub[sem_col].astype(float).to_numpy()
        ax.plot(x, y, marker="o", label=SOURCE_LABELS[source], color=SOURCE_COLORS[source], linewidth=2)
        ax.fill_between(x, y - err, y + err, color=SOURCE_COLORS[source], alpha=0.12)
    ax.set_xticks(x, AGE_ORDER, rotation=25, ha="right")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Age bin")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=3, frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_gap_lines(gaps: pd.DataFrame, value_col: str, title: str, ylabel: str, path: Path) -> None:
    summary = summarize(gaps, ["source_model", "age_bin"], [value_col])
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    x = np.arange(len(AGE_ORDER))
    for source in [s for s in SOURCE_ORDER if s != "real"]:
        sub = summary[summary["source_model"].astype(str).eq(source)].set_index("age_bin").reindex(AGE_ORDER)
        y = sub[f"{value_col}_mean"].astype(float).to_numpy()
        err = 1.96 * sub[f"{value_col}_sem"].astype(float).to_numpy()
        ax.plot(x, y, marker="o", label=SOURCE_LABELS[source], color=SOURCE_COLORS[source], linewidth=2)
        ax.fill_between(x, y - err, y + err, color=SOURCE_COLORS[source], alpha=0.13)
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_xticks(x, AGE_ORDER, rotation=25, ha="right")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Age bin")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=2, frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_bayes_mistral_scatter(frame: pd.DataFrame, path: Path) -> None:
    sample = frame.dropna(subset=["bayes_bits_per_token", "mistral_bits_per_token", "source_model"])
    if len(sample) > 220_000:
        sample = sample.groupby("source_model", observed=True, group_keys=False).sample(frac=220_000 / len(sample), random_state=17)
    fig, ax = plt.subplots(figsize=(8.2, 6.3))
    for source in SOURCE_ORDER:
        sub = sample[sample["source_model"].astype(str).eq(source)]
        if sub.empty:
            continue
        ax.scatter(
            sub["bayes_bits_per_token"],
            sub["mistral_bits_per_token"],
            s=4,
            alpha=0.16 if source != "real" else 0.22,
            color=SOURCE_COLORS[source],
            label=SOURCE_LABELS[source],
            rasterized=True,
        )
    ax.set_xlabel("Bayes-decomposed bits per token")
    ax.set_ylabel("Direct Mistral contextual bits per token")
    ax.set_title("Agreement between decomposition and direct contextual surprisal")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, markerscale=3)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_percentiles(percentiles: pd.DataFrame, path: Path) -> None:
    summary = summarize(percentiles, ["age_bin"], ["real_bayes_worse_fraction", "real_mistral_worse_fraction"])
    fig, ax = plt.subplots(figsize=(9.5, 5.3))
    x = np.arange(len(AGE_ORDER))
    for value, label, color in [
        ("real_bayes_worse_fraction", "Bayes decomposition", "#2f6f73"),
        ("real_mistral_worse_fraction", "Direct Mistral", "#c76f2c"),
    ]:
        sub = summary.set_index("age_bin").reindex(AGE_ORDER)
        y = 100 * sub[f"{value}_mean"].astype(float).to_numpy()
        err = 100 * 1.96 * sub[f"{value}_sem"].astype(float).to_numpy()
        ax.plot(x, y, marker="o", color=color, label=label, linewidth=2.2)
        ax.fill_between(x, y - err, y + err, color=color, alpha=0.15)
    ax.axhline(50, color="#555555", linestyle="--", linewidth=1)
    ax.set_xticks(x, AGE_ORDER, rotation=25, ha="right")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Generated alternatives with higher bits than real (%)")
    ax.set_xlabel("Age bin")
    ax.set_title("Same-context real-child advantage among n-gram alternatives")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_complexity(age_summary: pd.DataFrame, path: Path) -> None:
    agg = (
        age_summary.groupby("age_bin", observed=True)
        .agg(
            mean_words_per_utterance=("mean_words_per_utterance", "mean"),
            age_bin_vocab_size=("age_bin_vocab_size", "mean"),
            age_bin_ttr=("age_bin_ttr", "mean"),
        )
        .reindex(AGE_ORDER)
        .reset_index()
    )
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4), sharex=True)
    specs = [
        ("mean_words_per_utterance", "Mean words per utterance"),
        ("age_bin_vocab_size", "Mean age-bin vocabulary size"),
        ("age_bin_ttr", "Mean age-bin TTR"),
    ]
    x = np.arange(len(AGE_ORDER))
    for ax, (col, title) in zip(axes, specs):
        ax.plot(x, agg[col], marker="o", color="#2f6f73", linewidth=2)
        ax.set_title(title)
        ax.set_xticks(x, AGE_ORDER, rotation=35, ha="right")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Real-child complexity trajectories in the PBM subset", y=1.03)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_paired_gaps(frame: pd.DataFrame) -> pd.DataFrame:
    real_cols = [
        "row_uid",
        "bayes_bits_per_token",
        "bayes_prior_bits_per_token",
        "bayes_context_bits",
        "mistral_bits_per_token",
        "orthographic_word_count",
    ]
    real = frame[frame["source_model"].astype(str).eq("real")][real_cols].rename(
        columns={
            "bayes_bits_per_token": "real_bayes_bits_per_token",
            "bayes_prior_bits_per_token": "real_bayes_prior_bits_per_token",
            "bayes_context_bits": "real_bayes_context_bits",
            "mistral_bits_per_token": "real_mistral_bits_per_token",
            "orthographic_word_count": "real_orthographic_word_count",
        }
    )
    base = frame[~frame["source_model"].astype(str).eq("real")].merge(real, on="row_uid", how="inner")
    base["delta_bayes_bits_per_token_vs_real"] = base["bayes_bits_per_token"] - base["real_bayes_bits_per_token"]
    base["delta_mistral_bits_per_token_vs_real"] = base["mistral_bits_per_token"] - base["real_mistral_bits_per_token"]
    base["delta_words_vs_real"] = base["orthographic_word_count"] - base["real_orthographic_word_count"]
    return base


def build_percentiles(frame: pd.DataFrame) -> pd.DataFrame:
    value_cols = ["bayes_bits_per_token", "mistral_bits_per_token"]
    wide = frame.pivot_table(index=["row_uid", "age_bin"], columns="source_model", values=value_cols, aggfunc="first")
    rows: list[dict[str, object]] = []
    for (row_uid, age_bin), row in wide.iterrows():
        out = {"row_uid": row_uid, "age_bin": age_bin}
        for metric, out_col in [("bayes_bits_per_token", "real_bayes_worse_fraction"), ("mistral_bits_per_token", "real_mistral_worse_fraction")]:
            try:
                real_value = row[(metric, "real")]
            except KeyError:
                continue
            baseline_values = [row.get((metric, source), np.nan) for source in SOURCE_ORDER if source != "real"]
            baseline_values = [value for value in baseline_values if pd.notna(value)]
            out[out_col] = float(np.mean([value > real_value for value in baseline_values])) if baseline_values and pd.notna(real_value) else np.nan
        rows.append(out)
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bayes", type=Path, default=DEFAULT_BAYES)
    parser.add_argument("--complexity", type=Path, default=DEFAULT_COMPLEXITY)
    parser.add_argument("--trajectory", type=Path, default=DEFAULT_TRAJECTORY)
    parser.add_argument("--age-summary", type=Path, default=DEFAULT_AGE_SUMMARY)
    parser.add_argument("--mistral", type=Path, default=DEFAULT_MISTRAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--chunksize", type=int, default=600_000)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.fig_dir.mkdir(parents=True, exist_ok=True)
    args.doc_md.parent.mkdir(parents=True, exist_ok=True)

    bayes = read_bayes(args.bayes)
    complexity = read_complexity(args.complexity)
    trajectory = read_real_trajectory(args.trajectory)
    mistral, mistral_raw_counts = read_mistral(args.mistral, chunksize=args.chunksize)

    joined = (
        bayes.merge(complexity, on=["row_uid", "source_model"], how="left", validate="one_to_one")
        .merge(mistral, on=["row_uid", "source_model"], how="left", validate="one_to_one")
    )
    joined = joined.merge(trajectory, on="row_uid", how="left")
    joined["source_model"] = pd.Categorical(joined["source_model"], categories=SOURCE_ORDER, ordered=True)
    joined["age_bin"] = pd.Categorical(joined["age_bin"], categories=AGE_ORDER, ordered=True)
    joined_path = args.output_dir / "pbm_bayes_mistral_complexity_joined.csv.gz"
    joined.to_csv(joined_path, index=False)

    join_audit = pd.DataFrame(
        [
            {
                "source_model": source,
                "bayes_rows": int((bayes["source_model"].astype(str) == source).sum()),
                "mistral_raw_rows": int(mistral_raw_counts.get(source, 0)),
                "joined_rows": int((joined["source_model"].astype(str) == source).sum()),
                "missing_mistral_rows": int(joined[joined["source_model"].astype(str).eq(source)]["mistral_sum_bits"].isna().sum()),
                "missing_complexity_rows": int(joined[joined["source_model"].astype(str).eq(source)]["orthographic_word_count"].isna().sum()),
            }
            for source in SOURCE_ORDER
        ]
    )
    join_audit.to_csv(args.output_dir / "join_audit.csv", index=False)

    value_cols = [
        "bayes_bits_per_token",
        "bayes_prior_bits_per_token",
        "bayes_context_bits",
        "mistral_bits_per_token",
        "orthographic_word_count",
        "estimated_syllable_count",
    ]
    source_summary = summarize(joined, ["source_model"], value_cols)
    source_summary.to_csv(args.output_dir / "source_summary.csv", index=False)
    age_source_summary = summarize(joined, ["source_model", "age_bin"], value_cols)
    age_source_summary.to_csv(args.output_dir / "age_source_summary.csv", index=False)

    corr_rows: list[dict[str, object]] = []
    for source, group in joined.groupby("source_model", observed=True):
        corr_rows.append(
            {
                "source_model": str(source),
                "n": len(group),
                "pearson_bayes_mistral_per_token": group[["bayes_bits_per_token", "mistral_bits_per_token"]].corr().iloc[0, 1],
                "spearman_bayes_mistral_per_token": group[["bayes_bits_per_token", "mistral_bits_per_token"]].corr(method="spearman").iloc[0, 1],
                "pearson_prior_mistral_per_token": group[["bayes_prior_bits_per_token", "mistral_bits_per_token"]].corr().iloc[0, 1],
                "pearson_context_mistral_total": group[["bayes_context_bits", "mistral_sum_bits"]].corr().iloc[0, 1],
            }
        )
    correlations = pd.DataFrame(corr_rows)
    correlations.to_csv(args.output_dir / "bayes_mistral_correlations.csv", index=False)

    gaps = build_paired_gaps(joined)
    gaps.to_csv(args.output_dir / "paired_baseline_minus_real_gaps.csv.gz", index=False)
    gap_summary = summarize(
        gaps,
        ["source_model"],
        ["delta_bayes_bits_per_token_vs_real", "delta_mistral_bits_per_token_vs_real", "delta_words_vs_real"],
    )
    gap_summary.to_csv(args.output_dir / "paired_gap_summary.csv", index=False)

    percentiles = build_percentiles(joined)
    percentiles.to_csv(args.output_dir / "real_candidate_percentiles.csv.gz", index=False)
    percentile_summary = summarize(percentiles, ["age_bin"], ["real_bayes_worse_fraction", "real_mistral_worse_fraction"])
    percentile_summary.to_csv(args.output_dir / "real_candidate_percentile_summary.csv", index=False)

    age_summary = pd.read_csv(args.age_summary)

    figs = {
        "bayes_age": args.fig_dir / "bayes_bits_per_token_by_age_source.png",
        "mistral_age": args.fig_dir / "mistral_bits_per_token_by_age_source.png",
        "components_age": args.fig_dir / "bayes_component_bits_by_age_source.png",
        "scatter": args.fig_dir / "bayes_vs_mistral_scatter.png",
        "bayes_gap": args.fig_dir / "paired_bayes_gap_by_age.png",
        "mistral_gap": args.fig_dir / "paired_mistral_gap_by_age.png",
        "percentiles": args.fig_dir / "real_advantage_percentiles_by_age.png",
        "complexity": args.fig_dir / "real_child_complexity_trajectories.png",
    }
    plot_source_age_lines(age_source_summary, "bayes_bits_per_token_mean", "bayes_bits_per_token_sem", "Bayes-decomposed bits per token by source", "Unnormalized Bayes bits/token", figs["bayes_age"])
    plot_source_age_lines(age_source_summary, "mistral_bits_per_token_mean", "mistral_bits_per_token_sem", "Direct Mistral contextual bits per token by source", "Mistral bits/token", figs["mistral_age"])
    plot_source_age_lines(age_source_summary, "bayes_prior_bits_per_token_mean", "bayes_prior_bits_per_token_sem", "Bayes prior component by source", "Prior bits/token", figs["components_age"])
    plot_bayes_mistral_scatter(joined, figs["scatter"])
    plot_gap_lines(gaps, "delta_bayes_bits_per_token_vs_real", "Baseline minus real: Bayes-decomposed bits per token", "Baseline - real bits/token", figs["bayes_gap"])
    plot_gap_lines(gaps, "delta_mistral_bits_per_token_vs_real", "Baseline minus real: direct Mistral bits per token", "Baseline - real bits/token", figs["mistral_gap"])
    plot_percentiles(percentiles, figs["percentiles"])
    plot_complexity(age_summary, figs["complexity"])

    model_tables: list[pd.DataFrame] = []
    model_infos: list[dict[str, object]] = []
    model_specs = [
        (
            "Direct surprisal from Bayes score",
            "mistral_bits_per_token ~ bayes_bits_per_token + orthographic_word_count + C(source_model) + C(age_bin)",
            joined,
        ),
        (
            "Direct surprisal from Bayes components",
            "mistral_bits_per_token ~ bayes_prior_bits_per_token + bayes_context_bits + orthographic_word_count + C(source_model) + C(age_bin)",
            joined,
        ),
        (
            "Real-child direct surprisal with lexical complexity",
            "mistral_bits_per_token ~ bayes_prior_bits_per_token + bayes_context_bits + orthographic_word_count + lexical_cumulative_child_vocab_size + lexical_cumulative_child_ttr + C(age_bin) + C(child_id)",
            joined[joined["source_model"].astype(str).eq("real")],
        ),
        (
            "Paired baseline gap alignment",
            "delta_mistral_bits_per_token_vs_real ~ delta_bayes_bits_per_token_vs_real + delta_words_vs_real + C(source_model) + C(age_bin)",
            gaps,
        ),
    ]
    for name, formula, data in model_specs:
        table, info = fit_model(name, formula, data)
        model_tables.append(table)
        model_infos.append(info)
    models = pd.concat(model_tables, ignore_index=True)
    models.to_csv(args.output_dir / "model_coefficients.csv", index=False)
    model_info = pd.DataFrame(model_infos)
    model_info.to_csv(args.output_dir / "model_summary.csv", index=False)

    key_terms = models[
        models["term"].isin(
            [
                "bayes_bits_per_token",
                "bayes_prior_bits_per_token",
                "bayes_context_bits",
                "orthographic_word_count",
                "lexical_cumulative_child_vocab_size",
                "lexical_cumulative_child_ttr",
                "delta_bayes_bits_per_token_vs_real",
                "delta_words_vs_real",
            ]
        )
    ].copy()

    source_display = source_summary.copy()
    source_display["source"] = source_display["source_model"].astype(str).map(SOURCE_LABELS)
    source_display = source_display[
        [
            "source",
            "n",
            "bayes_bits_per_token_mean",
            "bayes_prior_bits_per_token_mean",
            "bayes_context_bits_mean",
            "mistral_bits_per_token_mean",
            "orthographic_word_count_mean",
        ]
    ]

    gap_display = gap_summary.copy()
    gap_display["source"] = gap_display["source_model"].astype(str).map(SOURCE_LABELS)
    gap_display = gap_display[
        [
            "source",
            "n",
            "delta_bayes_bits_per_token_vs_real_mean",
            "delta_mistral_bits_per_token_vs_real_mean",
            "delta_words_vs_real_mean",
        ]
    ]

    percentile_display = percentile_summary.copy()
    percentile_display["real_bayes_worse_pct"] = 100 * percentile_display["real_bayes_worse_fraction_mean"]
    percentile_display["real_mistral_worse_pct"] = 100 * percentile_display["real_mistral_worse_fraction_mean"]
    percentile_display = percentile_display[["age_bin", "n", "real_bayes_worse_pct", "real_mistral_worse_pct"]]

    md = f"""# Bayes-Decomposed Informativeness Working Report

This is a working report for the new Bayes-style information family. It is intentionally separate from the supervisor-facing July pages for now. The goal is to check whether the decomposition score behaves sensibly before we decide which results deserve promotion.

## What Was Scored

The Bayes table uses the decomposition

```text
log2 score(u, c) = log2 p(u) + log2 p(c | u)
bits = -log2 score(u, c)
```

The normalizer `p(c)` has **not** been estimated. That means these are unnormalized decomposition bits, useful for comparing candidate utterances in the same context and for exploratory analyses, but not a fully normalized posterior probability.

Inputs:

- Bayes scores: `{args.bayes}`
- Complexity predictors: `{args.complexity}`
- Direct contextual Mistral scores: `{args.mistral}`
- Joined analysis table: `{joined_path}`

## Audit

{md_table(join_audit)}

The join is clean enough for working analyses: Bayes and complexity products match exactly, and the direct Mistral table joins by `row_uid + source_model`. The `random` source has 16 fewer Bayes/complexity rows because empty generated random candidates were removed before scoring.

## Source-Level Patterns

{md_table(source_display, digits=3)}

Lower bits mean the model finds the utterance more expected or compatible. The most important comparison is not raw total bits alone, because utterance length matters; the main plots use bits per token where possible.

![Bayes bits per token by age and source]({rel(figs['bayes_age'], args.doc_md)})

![Direct Mistral bits per token by age and source]({rel(figs['mistral_age'], args.doc_md)})

![Bayes prior component by age and source]({rel(figs['components_age'], args.doc_md)})

## Does Bayes Agree With Direct Mistral Surprisal?

{md_table(correlations, digits=3)}

![Bayes versus direct Mistral scatter]({rel(figs['scatter'], args.doc_md)})

The decomposition and direct Mistral scores are not supposed to be identical. They use different estimators: the Bayes pilot uses count-based `p(u)` and reverse discourse `p(c | u)`, while direct Mistral estimates contextual target surprisal more directly. Agreement is therefore evidence of convergence; disagreement is scientifically informative rather than automatically a bug.

## Paired Real-Versus-Baseline Checks

Each generated baseline is paired to the same real child row and same context. Positive values below mean the generated baseline has more bits than the real child utterance.

{md_table(gap_display, digits=3)}

![Paired Bayes gaps]({rel(figs['bayes_gap'], args.doc_md)})

![Paired Mistral gaps]({rel(figs['mistral_gap'], args.doc_md)})

The same-context percentile view asks: among random/unigram/bigram/trigram alternatives for a row, what fraction have higher bits than the real child utterance?

{md_table(percentile_display, digits=2)}

![Real-child advantage percentiles]({rel(figs['percentiles'], args.doc_md)})

## Complexity And Effort

The new complexity repo adds orthographic MLU-style predictors, syllable/phoneme proxies, and lexical trajectory fields. These are not a replacement for the previous effort measures; they are extra controls and developmental descriptors.

![Real child complexity trajectories]({rel(figs['complexity'], args.doc_md)})

## First Regression Models

These are working models using heteroskedasticity-robust standard errors on a stratified sample where needed. They are meant to guide the next report iteration, not to be the final inferential specification.

{md_table(model_info, digits=3)}

Key coefficients:

{md_table(key_terms, digits=4)}

## Current Scientific Read

1. The Bayes products are runnable and joinable with the existing direct Mistral route.
2. The decomposition gives us two interpretable components: a prior/utterance-family term `p(u)` and a context-compatibility term `p(c | u)`.
3. The paired real-versus-baseline view is the most defensible immediate use: for the same child moment and context, ask whether the real utterance is favored relative to generated alternatives.
4. The Bayes score should stay labeled as an unnormalized decomposition score until we estimate or explicitly condition away `p(c)`.

## Next Decisions

- Decide whether the first supervisor-facing use should show paired real-versus-baseline gaps, correlations with Mistral, or complexity-controlled real-child developmental models.
- Add a sensitivity where Bayes `p(u)` is trained PBM-only rather than full-79, to show the full-79 result is not an artifact of training scope.
- Add the neural likelihood route only after the count-based decomposition has been explained and stabilized.
"""
    args.doc_md.write_text(md, encoding="utf-8")
    render_markdown_file(args.doc_md, args.doc_html)
    print(f"Wrote {args.doc_md}")
    print(f"Wrote {args.doc_html}")
    print(f"Wrote {joined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
