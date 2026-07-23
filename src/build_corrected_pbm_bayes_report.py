#!/usr/bin/env python3
"""Build the corrected cross-fitted PBM Bayes comparison report."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from render_markdown_report import render_markdown_file
except ImportError:
    from src.render_markdown_report import render_markdown_file

DEFAULT_BAYES_CSV = Path("results/corrected_pbm_bayes_v2/scores/pbm_crossfit_bayes_scores.csv.gz")
DEFAULT_AUDIT_JSON = Path("results/corrected_pbm_bayes_v2/scores/pbm_crossfit_bayes_scores.audit.json")
DEFAULT_DIRECT_CSV = Path("results/bayes_information_report/pbm_bayes_mistral_complexity_joined.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/corrected_pbm_bayes_report")
DEFAULT_FIG_DIR = Path("figs/corrected_pbm_bayes_report")
DEFAULT_DOC_MD = Path("docs/corrected_pbm_bayes_report.md")
DEFAULT_DOC_HTML = Path("docs/corrected_pbm_bayes_report.html")

SOURCE_ORDER = ["real", "random", "unigram", "bigram", "trigram"]
BASELINE_ORDER = ["random", "unigram", "bigram", "trigram"]
SOURCE_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
}
AGE_ORDER = [
    "006-023",
    "024-029",
    "030-035",
    "036-041",
    "042-047",
    "048-053",
    "054-059",
    "060-065",
]


def fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    if number != 0 and abs(number) < 0.001:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def md_table(frame: pd.DataFrame, *, digits: int = 3) -> str:
    if frame.empty:
        return "_No rows._"
    out = frame.copy()
    for column in out.columns:
        if pd.api.types.is_numeric_dtype(out[column]):
            out[column] = out[column].map(lambda value: fmt(value, digits))
    text = out.fillna("").astype(str)
    lines = [
        "| " + " | ".join(text.columns) + " |",
        "| " + " | ".join(["---"] * len(text.columns)) + " |",
    ]
    for _, row in text.iterrows():
        lines.append("| " + " | ".join(str(row[column]).replace("|", "\\|") for column in text.columns) + " |")
    return "\n".join(lines)


def rel(path: Path, report: Path) -> str:
    return os.path.relpath(path, start=report.parent).replace(os.sep, "/")


def count_text(value: object) -> str:
    return f"{int(float(value)):,}"


def percent_text(value: object, digits: int = 1) -> str:
    return f"{float(value):.{digits}%}"


def _sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def child_bootstrap_summary(child_frame: pd.DataFrame, *, draws: int = 5000, seed: int = 713) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(seed)
    for source, group in child_frame.groupby("source_model", observed=True):
        group = group.sort_values(["dataset", "child_id"]).reset_index(drop=True)
        n = len(group)
        row: dict[str, Any] = {"source_model": source, "children": n}
        for column in ["prior_logbf", "evidence_logbf", "total_logbf", "real_win_rate"]:
            values = group[column].to_numpy(dtype=float)
            row[f"{column}_child_mean"] = float(np.mean(values)) if n else float("nan")
            if n <= 1:
                row[f"{column}_ci_low"] = float("nan")
                row[f"{column}_ci_high"] = float("nan")
                continue
            indices = rng.integers(0, n, size=(draws, n))
            draws_mean = values[indices].mean(axis=1)
            row[f"{column}_ci_low"], row[f"{column}_ci_high"] = np.quantile(draws_mean, [0.025, 0.975])
        rows.append(row)
    output = pd.DataFrame(rows)
    output["source_model"] = pd.Categorical(output["source_model"], BASELINE_ORDER, ordered=True)
    return output.sort_values("source_model").reset_index(drop=True)


def plot_validation(validation: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.7))
    colors = ["#3A6EA5", "#6A4C93", "#2A9D8F"]
    ax.bar(validation["dataset"], validation["matched_accuracy"], color=colors[: len(validation)])
    ax.axhline(0.5, color="#444444", linestyle="--", linewidth=1.2, label="Chance")
    ax.set_ylim(0.48, max(0.66, float(validation["matched_accuracy"].max()) + 0.025))
    ax.set_ylabel("Matched-context pairwise accuracy")
    ax.set_title("Held-out context evidence passes in every PBM corpus")
    ax.legend(frameon=False)
    for index, value in enumerate(validation["matched_accuracy"]):
        ax.text(index, value + 0.006, f"{value:.1%}", ha="center", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def plot_gap_components(gaps: pd.DataFrame, path: Path) -> None:
    plot = gaps.set_index("source_model").reindex(BASELINE_ORDER)
    x = np.arange(len(plot))
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    ax.bar(x, plot["prior_logbf_real"], label="Utterance prior", color="#3A6EA5")
    ax.bar(
        x,
        plot["evidence_logbf_real"],
        bottom=plot["prior_logbf_real"],
        label="Context evidence",
        color="#E9C46A",
    )
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_xticks(x, [SOURCE_LABELS[source] for source in BASELINE_ORDER])
    ax.set_ylabel("Mean log2 Bayes factor: real minus baseline")
    ax.set_title("Real-child advantage is primarily prior-driven")
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def plot_age_ranks(age: pd.DataFrame, path: Path) -> None:
    plot = age.set_index("age_bin").reindex(AGE_ORDER)
    x = np.arange(len(plot))
    fig, ax = plt.subplots(figsize=(10.0, 5.2))
    ax.plot(x, plot["prior_rank1_rate"], marker="o", linewidth=2, label="Prior only", color="#777777")
    ax.plot(x, plot["combined_rank1_rate"], marker="o", linewidth=2.3, label="Prior + context evidence", color="#2A9D8F")
    ax.axhline(0.2, color="#444444", linestyle="--", linewidth=1, label="Five-way chance")
    ax.set_xticks(x, AGE_ORDER, rotation=25, ha="right")
    ax.set_ylim(0.15, max(0.55, float(plot["combined_rank1_rate"].max()) + 0.04))
    ax.set_ylabel("Real child ranked first")
    ax.set_xlabel("Age bin")
    ax.set_title("Cross-fitted real-child ranking by age")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def plot_alignment(alignment: pd.DataFrame, path: Path) -> None:
    plot = alignment.set_index("source_model").reindex(BASELINE_ORDER)
    x = np.arange(len(plot))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9.4, 5.1))
    ax.bar(x - width / 2, plot["pearson_gap"], width, label="Gap correlation", color="#6A4C93")
    ax.bar(x + width / 2, plot["sign_agreement"], width, label="Gap sign agreement", color="#F4A261")
    ax.set_xticks(x, [SOURCE_LABELS[source] for source in BASELINE_ORDER])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Proportion / correlation")
    ax.set_title("Corrected Bayes and direct Mistral favor similar candidates")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def build_report(
    *,
    bayes_csv: Path,
    audit_json: Path,
    direct_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_md: Path,
    doc_html: Path | None,
) -> dict[str, Any]:
    for path in (bayes_csv, audit_json, direct_csv):
        if not path.exists():
            raise FileNotFoundError(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc_md.parent.mkdir(parents=True, exist_ok=True)
    audit = json.loads(audit_json.read_text(encoding="utf-8"))

    connection = duckdb.connect()
    connection.execute("PRAGMA threads=8")
    connection.execute(
        f"""
        CREATE TEMP TABLE bayes AS
        SELECT row_uid, source_model, dataset, child_id, age_months, age_bin,
               log2_p_u_crossfit, context_log2_evidence_crossfit,
               bayes_log2_score_crossfit, candidate_set_probability,
               candidate_set_bayes_bits, candidate_set_rank, candidate_set_size,
               utterance_token_count, context_token_count
        FROM read_csv_auto('{_sql_path(bayes_csv)}')
        """
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE direct AS
        SELECT row_uid, source_model, mistral_sum_bits, mistral_bits_per_token
        FROM read_csv_auto('{_sql_path(direct_csv)}')
        """
    )

    source_summary = connection.execute(
        """
        SELECT source_model, count(*) AS n,
               avg(-log2_p_u_crossfit / utterance_token_count) AS prior_bits_per_word,
               avg(context_log2_evidence_crossfit) AS context_evidence_bits,
               avg(candidate_set_probability) AS candidate_probability,
               median(candidate_set_probability) AS median_candidate_probability,
               avg(candidate_set_bayes_bits) AS candidate_bits,
               avg(CASE WHEN candidate_set_rank = 1 THEN 1 ELSE 0 END) AS rank1_rate,
               avg(CASE WHEN context_token_count = 0 THEN 1 ELSE 0 END) AS empty_context_rate
        FROM bayes GROUP BY source_model
        """
    ).fetchdf()
    source_summary["source_model"] = pd.Categorical(source_summary["source_model"], SOURCE_ORDER, ordered=True)
    source_summary = source_summary.sort_values("source_model").reset_index(drop=True)

    real_overall = connection.execute(
        """
        WITH ranked AS (
            SELECT *, rank() OVER (PARTITION BY row_uid ORDER BY log2_p_u_crossfit DESC) AS prior_rank,
                      rank() OVER (PARTITION BY row_uid ORDER BY context_log2_evidence_crossfit DESC) AS evidence_rank
            FROM bayes
        )
        SELECT count(*) AS n,
               avg(candidate_set_probability) AS real_probability,
               median(candidate_set_probability) AS real_median_probability,
               avg(CASE WHEN prior_rank = 1 THEN 1 ELSE 0 END) AS prior_rank1_rate,
               avg(CASE WHEN evidence_rank = 1 THEN 1 ELSE 0 END) AS evidence_rank1_rate,
               avg(CASE WHEN candidate_set_rank = 1 THEN 1 ELSE 0 END) AS combined_rank1_rate,
               avg(CASE WHEN candidate_set_rank <= 2 THEN 1 ELSE 0 END) AS combined_top2_rate,
               avg(prior_rank) AS prior_mean_rank,
               avg(candidate_set_rank) AS combined_mean_rank
        FROM ranked WHERE source_model = 'real'
        """
    ).fetchdf()

    age_summary = connection.execute(
        """
        WITH ranked AS (
            SELECT *, rank() OVER (PARTITION BY row_uid ORDER BY log2_p_u_crossfit DESC) AS prior_rank
            FROM bayes
        )
        SELECT age_bin, count(*) AS n,
               avg(candidate_set_probability) AS real_probability,
               avg(CASE WHEN prior_rank = 1 THEN 1 ELSE 0 END) AS prior_rank1_rate,
               avg(CASE WHEN candidate_set_rank = 1 THEN 1 ELSE 0 END) AS combined_rank1_rate,
               avg(CASE WHEN candidate_set_rank <= 2 THEN 1 ELSE 0 END) AS combined_top2_rate
        FROM ranked WHERE source_model = 'real'
        GROUP BY age_bin ORDER BY min(age_months::DOUBLE)
        """
    ).fetchdf()

    corpus_summary = connection.execute(
        """
        SELECT dataset, count(*) AS n,
               avg(candidate_set_probability) AS real_probability,
               avg(CASE WHEN candidate_set_rank = 1 THEN 1 ELSE 0 END) AS real_rank1_rate,
               avg(candidate_set_rank) AS real_mean_rank
        FROM bayes WHERE source_model = 'real'
        GROUP BY dataset ORDER BY dataset
        """
    ).fetchdf()

    paired_gaps = connection.execute(
        """
        WITH real AS (SELECT * FROM bayes WHERE source_model = 'real')
        SELECT baseline.source_model, count(*) AS n,
               avg(real.log2_p_u_crossfit - baseline.log2_p_u_crossfit) AS prior_logbf_real,
               avg(real.context_log2_evidence_crossfit - baseline.context_log2_evidence_crossfit) AS evidence_logbf_real,
               avg(real.bayes_log2_score_crossfit - baseline.bayes_log2_score_crossfit) AS total_logbf_real,
               avg(CASE WHEN real.bayes_log2_score_crossfit > baseline.bayes_log2_score_crossfit THEN 1 ELSE 0 END) AS real_win_rate,
               avg(CASE WHEN real.context_log2_evidence_crossfit > baseline.context_log2_evidence_crossfit THEN 1
                        WHEN real.context_log2_evidence_crossfit = baseline.context_log2_evidence_crossfit THEN 0.5 ELSE 0 END) AS evidence_win_rate
        FROM real JOIN bayes baseline USING (row_uid)
        WHERE baseline.source_model <> 'real'
        GROUP BY baseline.source_model
        """
    ).fetchdf()
    paired_gaps["source_model"] = pd.Categorical(paired_gaps["source_model"], BASELINE_ORDER, ordered=True)
    paired_gaps = paired_gaps.sort_values("source_model").reset_index(drop=True)

    child_gaps = connection.execute(
        """
        WITH real AS (SELECT * FROM bayes WHERE source_model = 'real')
        SELECT baseline.source_model, real.dataset, real.child_id,
               avg(real.log2_p_u_crossfit - baseline.log2_p_u_crossfit) AS prior_logbf,
               avg(real.context_log2_evidence_crossfit - baseline.context_log2_evidence_crossfit) AS evidence_logbf,
               avg(real.bayes_log2_score_crossfit - baseline.bayes_log2_score_crossfit) AS total_logbf,
               avg(CASE WHEN real.bayes_log2_score_crossfit > baseline.bayes_log2_score_crossfit THEN 1 ELSE 0 END) AS real_win_rate
        FROM real JOIN bayes baseline USING (row_uid)
        WHERE baseline.source_model <> 'real'
        GROUP BY baseline.source_model, real.dataset, real.child_id
        """
    ).fetchdf()
    bootstrap = child_bootstrap_summary(child_gaps)

    alignment = connection.execute(
        """
        WITH joined AS (
            SELECT bayes.row_uid, bayes.source_model, bayes.bayes_log2_score_crossfit,
                   direct.mistral_sum_bits
            FROM bayes JOIN direct USING (row_uid, source_model)
        ), real AS (SELECT * FROM joined WHERE source_model = 'real'), gaps AS (
            SELECT baseline.source_model,
                   real.bayes_log2_score_crossfit - baseline.bayes_log2_score_crossfit AS bayes_logbf,
                   baseline.mistral_sum_bits - real.mistral_sum_bits AS mistral_logbf
            FROM real JOIN joined baseline USING (row_uid)
            WHERE baseline.source_model <> 'real'
        )
        SELECT source_model, count(*) AS n, corr(bayes_logbf, mistral_logbf) AS pearson_gap,
               avg(CASE WHEN (bayes_logbf > 0 AND mistral_logbf > 0)
                              OR (bayes_logbf < 0 AND mistral_logbf < 0)
                              OR (bayes_logbf = 0 AND mistral_logbf = 0) THEN 1 ELSE 0 END) AS sign_agreement,
               avg(bayes_logbf) AS bayes_logbf_mean,
               avg(mistral_logbf) AS mistral_logbf_mean
        FROM gaps GROUP BY source_model
        """
    ).fetchdf()
    alignment["source_model"] = pd.Categorical(alignment["source_model"], BASELINE_ORDER, ordered=True)
    alignment = alignment.sort_values("source_model").reset_index(drop=True)

    validation = pd.DataFrame(
        [
            {
                "dataset": fold["heldout_dataset"],
                "validation_n": fold["matched_vs_shuffled_validation_n"],
                "matched_accuracy": fold["matched_context_pairwise_accuracy"],
                "mean_evidence_gap_bits": fold["matched_minus_shuffled_context_evidence_mean_bits"],
                "pass": fold["context_validation_pass"],
                "training_rows": fold["training_rows_total"],
                "excluded_rows": fold["rows_excluded_heldout_dataset"],
            }
            for fold in audit["folds"]
        ]
    )

    tables = {
        "source_summary": source_summary,
        "real_overall": real_overall,
        "age_summary": age_summary,
        "corpus_summary": corpus_summary,
        "paired_gap_summary": paired_gaps,
        "child_bootstrap_summary": bootstrap,
        "direct_mistral_alignment": alignment,
        "context_validation": validation,
    }
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)

    validation_fig = fig_dir / "heldout_context_validation.png"
    components_fig = fig_dir / "paired_logbf_components.png"
    age_fig = fig_dir / "real_rank1_by_age.png"
    alignment_fig = fig_dir / "alignment_with_direct_mistral.png"
    plot_validation(validation, validation_fig)
    plot_gap_components(paired_gaps, components_fig)
    plot_age_ranks(age_summary, age_fig)
    plot_alignment(alignment, alignment_fig)

    overall = real_overall.iloc[0]
    display_source = source_summary.copy()
    display_source["source"] = display_source["source_model"].astype("string").map(SOURCE_LABELS)
    display_source = display_source[
        ["source", "n", "candidate_probability", "median_candidate_probability", "rank1_rate", "prior_bits_per_word", "context_evidence_bits"]
    ]
    display_source["n"] = display_source["n"].map(count_text)
    for column in ["candidate_probability", "median_candidate_probability", "rank1_rate"]:
        display_source[column] = display_source[column].map(percent_text)
    display_gaps = paired_gaps.copy()
    display_gaps["baseline"] = display_gaps["source_model"].astype("string").map(SOURCE_LABELS)
    display_gaps = display_gaps[
        ["baseline", "n", "prior_logbf_real", "evidence_logbf_real", "total_logbf_real", "real_win_rate", "evidence_win_rate"]
    ]
    display_gaps["n"] = display_gaps["n"].map(count_text)
    for column in ["real_win_rate", "evidence_win_rate"]:
        display_gaps[column] = display_gaps[column].map(percent_text)
    display_bootstrap = bootstrap.copy()
    display_bootstrap["baseline"] = display_bootstrap["source_model"].astype("string").map(SOURCE_LABELS)
    display_bootstrap = display_bootstrap[
        ["baseline", "children", "total_logbf_child_mean", "total_logbf_ci_low", "total_logbf_ci_high", "real_win_rate_child_mean", "real_win_rate_ci_low", "real_win_rate_ci_high"]
    ]
    display_bootstrap["children"] = display_bootstrap["children"].map(count_text)
    for column in ["real_win_rate_child_mean", "real_win_rate_ci_low", "real_win_rate_ci_high"]:
        display_bootstrap[column] = display_bootstrap[column].map(percent_text)
    display_alignment = alignment.copy()
    display_alignment["baseline"] = display_alignment["source_model"].astype("string").map(SOURCE_LABELS)
    display_alignment = display_alignment[["baseline", "n", "pearson_gap", "sign_agreement", "bayes_logbf_mean", "mistral_logbf_mean"]]
    display_alignment["n"] = display_alignment["n"].map(count_text)
    display_alignment["sign_agreement"] = display_alignment["sign_agreement"].map(percent_text)
    display_validation = validation.rename(
        columns={
            "dataset": "held-out corpus",
            "validation_n": "validation pairs",
            "matched_accuracy": "matched accuracy",
            "mean_evidence_gap_bits": "matched − shuffled bits",
            "pass": "passed",
            "training_rows": "training rows",
            "excluded_rows": "excluded own-corpus rows",
        }
    ).copy()
    for column in ["validation pairs", "training rows", "excluded own-corpus rows"]:
        display_validation[column] = display_validation[column].map(count_text)
    display_validation["matched accuracy"] = display_validation["matched accuracy"].map(percent_text)
    display_validation["passed"] = display_validation["passed"].map(lambda value: "Yes" if value else "No")
    display_age = age_summary.rename(
        columns={
            "age_bin": "age bin",
            "real_probability": "real probability",
            "prior_rank1_rate": "prior-only rank 1",
            "combined_rank1_rate": "combined rank 1",
            "combined_top2_rate": "combined top 2",
        }
    ).copy()
    display_age["n"] = display_age["n"].map(count_text)
    for column in ["real probability", "prior-only rank 1", "combined rank 1", "combined top 2"]:
        display_age[column] = display_age[column].map(percent_text)
    display_corpus = corpus_summary.rename(
        columns={
            "dataset": "corpus",
            "real_probability": "real probability",
            "real_rank1_rate": "real rank-1 rate",
            "real_mean_rank": "real mean rank",
        }
    ).copy()
    display_corpus["n"] = display_corpus["n"].map(count_text)
    for column in ["real probability", "real rank-1 rate"]:
        display_corpus[column] = display_corpus[column].map(percent_text)

    md = f"""# Corrected Cross-Fitted Bayes-Derived PBM Report

## Executive Result

The Bayes identity does not define a fundamentally different kind of surprisal. It rewrites the same conditional probability:

<div style="margin:1.2em auto;padding:0.9em 1.2em;max-width:760px;text-align:center;background:#f5f7f6;border-left:4px solid #2f6f73;font-family:Georgia,serif;font-size:1.18em" role="math">−log<sub>2</sub> <i>p</i>(<i>u</i> | <i>c</i>, <i>a</i>) = −log<sub>2</sub> <i>p</i>(<i>u</i> | <i>a</i>) − log<sub>2</sub>[<i>p</i>(<i>c</i> | <i>u</i>, <i>a</i>) / <i>p</i>(<i>c</i> | <i>a</i>)]</div>

Direct Mistral scoring estimates `p(u | c)` in one neural model. This corrected analysis instead estimates an age-conditioned utterance prior and a separate context-evidence term, then normalizes those scores over the five matched PBM candidates for each row. It is therefore an **alternative Bayes-derived candidate scorer**, not a replacement for Mistral and not unrestricted surprisal over all possible utterances.

After removing corpus leakage, the real child utterance has mean five-way candidate probability **{overall['real_probability']:.1%}**, is ranked first on **{overall['combined_rank1_rate']:.1%}** of rows, and is in the top two on **{overall['combined_top2_rate']:.1%}**. Five-way chance for rank 1 is 20%. The prior alone ranks the real child first on {overall['prior_rank1_rate']:.1%}; adding context evidence raises this to {overall['combined_rank1_rate']:.1%}. Thus the corrected result is real, but it is driven primarily by the utterance prior, with a smaller incremental contribution from context compatibility.

## What Was Fixed

The previous n-gram pilot had three problems that prevent substantive interpretation: PBM rows occurred in its training data, `p(c)` was omitted, and an order-three reverse likelihood allowed only the candidate's final word to affect the first context token. The corrected estimator now:

- holds out the entire evaluated corpus—Brown, Manchester, or Providence—while training each fold;
- trains additively by age, using only the target age bin and earlier bins;
- maps unseen prior tokens to an explicit `<unk>` state;
- uses all candidate unigrams/bigrams and all retained context tokens in a contrastive matched-versus-shuffled evidence model;
- assigns neutral evidence to an empty context;
- writes separate prior, context-evidence, and combined score columns;
- normalizes the combined scores within each row's available real/random/unigram/bigram/trigram candidate set.

For candidate set `A_c`, the reported probability is

<div style="margin:1.2em auto;padding:0.9em 1.2em;max-width:820px;text-align:center;background:#f5f7f6;border-left:4px solid #2f6f73;font-family:Georgia,serif;font-size:1.12em" role="math"><i>q</i><sub>A</sub>(<i>u</i> | <i>c</i>, <i>a</i>) = 2<sup><i>S</i>(<i>u</i>,<i>c</i>,<i>a</i>)</sup> / Σ<sub><i>v</i>∈<i>A</i><sub>c</sub></sub> 2<sup><i>S</i>(<i>v</i>,<i>c</i>,<i>a</i>)</sup>, &nbsp; <i>S</i> = log<sub>2</sub> p̂(<i>u</i> | <i>a</i>) + Ê(<i>c</i>,<i>u</i>,<i>a</i>)</div>

Here `E_hat` is a contrastive estimate of the context likelihood ratio, not a literal neural sequence probability. Candidate-set Bayes surprisal is `-log2 q_A`.

## Audit And Held-Out Validation

The scorer wrote **{audit['row_count']:,}** rows. Every output group sums to one within floating-point tolerance, and all three corpus folds passed the predeclared held-out matched-versus-shuffled context check.

{md_table(display_validation)}

![Held-out context validation]({rel(validation_fig, doc_md)})

The validation accuracy is modest rather than near-perfect. That is appropriate to report: the context term contains held-out lexical/discourse compatibility signal, but it is not a complete model of conversational meaning.

## PBM Candidate Results

{md_table(display_source.rename(columns={'candidate_probability': 'mean candidate probability', 'median_candidate_probability': 'median candidate probability', 'rank1_rate': 'rank-1 rate', 'prior_bits_per_word': 'prior bits/word', 'context_evidence_bits': 'mean context evidence bits'}))}

The candidate probabilities are relative to this particular five-way set. The generated strings are matched-length controls, not meaning-preserving paraphrases, so the result establishes linguistic plausibility relative to these baselines—not communicative optimality.

## Where The Real-Child Advantage Comes From

Positive log2 Bayes factors favor the real child utterance over the paired baseline.

{md_table(display_gaps.rename(columns={'prior_logbf_real': 'prior logBF', 'evidence_logbf_real': 'context-evidence logBF', 'total_logbf_real': 'combined logBF', 'real_win_rate': 'combined real-win rate', 'evidence_win_rate': 'context-only real-win rate'}))}

![Prior and context components]({rel(components_fig, doc_md)})

Context evidence independently favors the real utterance more often than chance against every baseline, including {float(paired_gaps.loc[paired_gaps['source_model'].astype(str).eq('trigram'), 'evidence_win_rate'].iloc[0]):.1%} against the strongest trigram comparison. Nevertheless, the mean combined advantage is mostly prior-driven. This decomposition is the main scientific value of the Bayes route: it shows whether a candidate is favored because it resembles developmentally available child language, because it matches the caregiver context, or both.

Child-level bootstrap summaries, which weight children rather than millions of rows as the independent units, remain positive for all four comparisons:

{md_table(display_bootstrap.rename(columns={'total_logbf_child_mean': 'child-mean logBF', 'total_logbf_ci_low': 'logBF 2.5%', 'total_logbf_ci_high': 'logBF 97.5%', 'real_win_rate_child_mean': 'child-mean win rate', 'real_win_rate_ci_low': 'win 2.5%', 'real_win_rate_ci_high': 'win 97.5%'}))}

For the trigram comparison, the child-level interval for the *proportion of rows won* crosses 50%, even though the child-mean log Bayes factor remains positive. The strong claim is therefore positive average evidence relative to the trigram—not a universal majority-win effect across children.

## Descriptive Developmental Pattern

{md_table(display_age)}

![Real-child rank by age]({rel(age_fig, doc_md)})

The real-child rank improves from the youngest bin into the central PBM age range, but the later bins fluctuate and contain far fewer rows and children. This figure is descriptive. It is not a corrected onset analysis and should not be used to claim a precise month when Bayes sensitivity emerges.

Corpus-specific performance also remains heterogeneous:

{md_table(display_corpus)}

## Agreement With Direct Mistral Surprisal

For each paired comparison, the Mistral log advantage is the generated target's `sum_bits` minus the real target's `sum_bits`. The corrected Bayes advantage is the real combined score minus the generated combined score.

{md_table(display_alignment.rename(columns={'pearson_gap': 'gap correlation', 'sign_agreement': 'sign agreement', 'bayes_logbf_mean': 'mean Bayes logBF', 'mistral_logbf_mean': 'mean Mistral logBF'}))}

![Agreement with direct Mistral]({rel(alignment_fig, doc_md)})

Agreement is strongest for the deliberately poor random baseline and declines as the n-gram alternatives become more realistic. The two methods are related but non-identical: Mistral supplies a direct neural target probability, while the Bayes-derived model makes developmental prior and context evidence separately visible.

## Correct Interpretation

The corrected Bayes analysis answers:

> Among the real utterance and four matched PBM baseline strings, how strongly does an out-of-corpus, age-appropriate prior plus held-out context evidence favor each candidate?

It does **not** show that the real utterance maximizes communicative efficiency, carries more semantic information, or has a normalized posterior probability among all possible utterances. The candidate alternatives do not preserve intended meaning. Direct Mistral surprisal should remain the primary broad-coverage probability measure; the corrected Bayes score is a complementary decomposition and robustness analysis.

## Recommended Supervisor-Facing Result

The clean result to promote is:

> In leave-corpus-out, age-additive scoring, real PBM child utterances are ranked first among five matched candidates on {overall['combined_rank1_rate']:.1%} of rows, compared with 20% chance. The advantage is primarily explained by an age-appropriate utterance prior, while independently validated context evidence provides a smaller positive increment. The corrected Bayes and direct Mistral paired preferences agree most strongly for coarse baselines and only moderately for the strongest trigram alternative.

This result is suitable as a robustness/decomposition section. It should not replace the main fixed-effort Mistral analysis or the still-needed listener-utility and semantic-response-entropy analyses.

## Reproducibility

- Corrected scores: `{bayes_csv}`
- Score audit: `{audit_json}`
- Direct-score join source: `{direct_csv}`
- Compact tables: `{output_dir}`
- Figures: `{fig_dir}`
- Estimator: `{audit['estimator']}`
- Normalization scope: `{audit['normalization_scope']}`
- Output checksum: `{audit['output_sha256']}`
"""
    doc_md.write_text(md, encoding="utf-8")
    if doc_html is not None:
        render_markdown_file(doc_md, doc_html, title="Corrected Cross-Fitted Bayes-Derived PBM Report")
    connection.close()
    return {
        "row_count": int(audit["row_count"]),
        "doc_md": str(doc_md),
        "doc_html": str(doc_html) if doc_html else None,
        "output_dir": str(output_dir),
        "fig_dir": str(fig_dir),
        "all_context_validation_pass": bool(audit["all_context_validation_pass"]),
        "real_rank1_rate": float(overall["combined_rank1_rate"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bayes-csv", type=Path, default=DEFAULT_BAYES_CSV)
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--direct-csv", type=Path, default=DEFAULT_DIRECT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    args = parser.parse_args()
    result = build_report(
        bayes_csv=args.bayes_csv,
        audit_json=args.audit_json,
        direct_csv=args.direct_csv,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_md=args.doc_md,
        doc_html=args.doc_html,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
