#!/usr/bin/env python3
"""Build two internal Route 1 model-review reports.

Report 1 is a more explicit version of the M1/M2/M3 deep dive. It uses the
already fitted M1/M2/M3 outputs and focuses on interpretation.

Report 2 is an exploratory model zoo informed by the communicative-efficiency
research questions. It derives additional predictors from the Route 1 long
table, fits a broad set of candidate models on bounded samples, and writes
figures/tables for review before anything is promoted to the supervisor-facing
report.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gamma, Gaussian, Poisson
from statsmodels.genmod.families.links import Log

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
M123_OUTPUT_DIR = Path("results/m1_m2_utterance_information_deep_dive")
M123_FIG_DIR = Path("figs/m1_m2_utterance_information_deep_dive")

DETAIL_OUTPUT_DIR = Path("results/utterance_information_m123_extended")
DETAIL_DOC_MD = Path("docs/utterance_information_m123_extended.md")
DETAIL_DOC_HTML = Path("docs/utterance_information_m123_extended.html")

ZOO_OUTPUT_DIR = Path("results/utterance_information_research_model_zoo")
ZOO_FIG_DIR = Path("figs/utterance_information_research_model_zoo")
ZOO_DOC_MD = Path("docs/utterance_information_research_model_zoo.md")
ZOO_DOC_HTML = Path("docs/utterance_information_research_model_zoo.html")

SEED = 20260608
AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
VARIANT_ORDER = ["real", "random", "unigram", "bigram", "trigram"]
EFFORT_MEASURES = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables: CMU/pkg"),
    ("nb_syllables_pkg", "Syllables: pkg"),
    ("nb_phonemes", "Phonemes"),
]
EFFORT_Z_TERMS = [
    "nb_words_z",
    "nb_morphemes_z",
    "nb_syllables_cmu_or_pkg_z",
    "nb_syllables_pkg_z",
    "nb_phonemes_z",
]
EFFORT_DENSITY_OUTCOMES = [
    ("bits_per_word", "Words", "log_nb_words"),
    ("bits_per_morpheme", "Morphemes", "log_nb_morphemes"),
    ("bits_per_syllable_cmu_or_pkg", "Syllables: CMU/pkg", "log_nb_syllables"),
    ("bits_per_syllable_pkg", "Syllables: pkg", "log_nb_syllables"),
    ("bits_per_phoneme", "Phonemes", "log_nb_phonemes"),
]
ZOO_CARD_DEFS = [
    {
        "model": "Z1 Information | child FE",
        "short": "Z1",
        "title": "Information With Child Identity",
        "question_family": "Does total utterance information change with age after child identity and one effort measure are controlled?",
        "outside_m1_m4": "This is a sibling of M2 but kept in the expanded report because it repeats the child-identity analysis across every effort measure.",
        "plot": "z1_information_child_fe_age.png",
        "plot_reading": "The line is a visual age regression for real child total bits; dots are age-bin means. The fitted model also controls word count and child identity.",
        "takeaway_term": "age_months_z",
    },
    {
        "model": "Z2 Information density | nonlinear age",
        "short": "Z2",
        "title": "Nonlinear Information Density",
        "question_family": "Does information per unit of effort follow a curved developmental trajectory?",
        "outside_m1_m4": "M1-M4 use simple linear age terms; this asks whether a curved developmental trajectory is needed.",
        "plot": "z2_nonlinear_information_density.png",
        "plot_reading": "The curve is a quadratic regression of bits per word over age. A curve rather than a straight line suggests nonlinear development.",
        "takeaway_term": "I(age_months_z ** 2)",
    },
    {
        "model": "Z3 Effort from context entropy",
        "short": "Z3",
        "title": "Context Entropy Predicting Effort",
        "question_family": "Do children produce more effortful utterances after less predictable caretaker contexts?",
        "outside_m1_m4": "M4 introduces context entropy; this expanded version adds question type and context length in a GEE effort model.",
        "plot": "z3_context_entropy_effort.png",
        "plot_reading": "The regression line shows whether child word count rises or falls as next-token context entropy increases.",
        "takeaway_term": "context_entropy_bits_z",
    },
    {
        "model": "Z4 Information from context entropy",
        "short": "Z4",
        "title": "Context Entropy Predicting Information",
        "question_family": "Does contextual uncertainty predict the information carried by an utterance after effort is controlled?",
        "outside_m1_m4": "This tests context entropy as a direct predictor of total utterance information while controlling one effort measure at a time.",
        "plot": "z4_context_entropy_density.png",
        "plot_reading": "The regression line is a descriptive view of total bits across contexts with lower versus higher next-token entropy. The fitted subvariants below add explicit effort controls.",
        "takeaway_term": "context_entropy_bits_z",
    },
    {
        "model": "Z5 Context window sensitivity",
        "short": "Z5",
        "title": "Scoring Context Window Sensitivity",
        "question_family": "Do conclusions change when surprisal is scored with k1, k2, or k3 caretaker context windows?",
        "outside_m1_m4": "M1-M4 use k3 as the main condition; this asks whether the age trajectory changes under k1, k2, or k3 scoring.",
        "plot": "z5_context_window_sensitivity.png",
        "plot_reading": "Lines compare bits per word by age under k1, k2, and k3 scoring. Separation means the amount of context used for scoring matters.",
        "takeaway_term": "age_months_z",
    },
    {
        "model": "Z6 Question-type effort",
        "short": "Z6",
        "title": "Question Type Predicting Effort",
        "question_family": "Does the type of preceding caretaker question predict how much effort the child produces?",
        "outside_m1_m4": "This adds a conversational-control variable: whether the preceding caretaker context is a wh-question, yes/no question, other question, or not a question.",
        "plot": "z6_question_type_effort.png",
        "plot_reading": "Lines compare mean child word count by age after different broad caretaker context types.",
        "takeaway_term": "age_months_z",
    },
    {
        "model": "Z7 Baseline comparison",
        "short": "Z7",
        "title": "Real Children Versus All Matched Baselines",
        "question_family": "Do real children differ from generated baselines after one effort measure is controlled?",
        "outside_m1_m4": "M1-M4 only analyze real child utterances; this model asks whether real children differ from random and n-gram baselines after controlling effort. Effort controls are kept separate.",
        "plot": "z7_baseline_comparison.png",
        "plot_reading": "Lines compare real children and generated baselines over age. The plot is descriptive; the Z7 model table below is the effort-controlled comparison.",
        "takeaway_term": "age_months_z",
    },
    {
        "model": "Z8 Child vs caretaker information",
        "short": "Z8",
        "title": "Children Versus Caretakers",
        "question_family": "Do children and caretakers show different age-linked information trajectories after effort is controlled?",
        "outside_m1_m4": "M1-M4 are child-only; this compares child and caretaker trajectories over child age.",
        "plot": "z8_child_caretaker_density.png",
        "plot_reading": "Lines compare child and caretaker bits per word. This is not row-matched, so read it as a speaker-group trajectory contrast.",
        "takeaway_term": "age_months_z",
    },
    {
        "model": "Z9 Information per unit",
        "short": "Z9",
        "title": "Information Per Effort Unit",
        "question_family": "Does information per effort unit change with age when the effort unit itself is the outcome denominator?",
        "outside_m1_m4": "M1-M4 control effort as a predictor; this complementary family treats information per effort unit as the outcome.",
        "plot": "z9_phonological_efficiency.png",
        "plot_reading": "The regression line shows the phoneme-denominated version of this family. The fitted subvariants below repeat the density model for every effort unit.",
        "takeaway_term": "age_months_z",
    },
    {
        "model": "Z10 Context certainty",
        "short": "Z10",
        "title": "Context Certainty Predicting Effort",
        "question_family": "Do children produce less effort when the model is more certain about the next token after the context?",
        "outside_m1_m4": "This is the inverse of the entropy framing: it uses the probability of the most likely next token as a context-certainty predictor.",
        "plot": "z10_context_certainty_effort.png",
        "plot_reading": "The regression line shows whether child word count changes when the model is more certain about the next token.",
        "takeaway_term": "context_next_top1_prob_z",
    },
    {
        "model": "Z11 Real-minus-baseline delta",
        "short": "Z11",
        "title": "Real Minus Baseline Delta",
        "question_family": "Does the row-matched real-minus-baseline information gap change with age after effort is controlled?",
        "outside_m1_m4": "This is the most direct baseline-difference analysis and is row-matched rather than child-only. Effort controls are fitted one at a time.",
        "plot": "z11_real_minus_baseline_delta.png",
        "plot_reading": "Lines below zero mean real child utterances have lower total bits than the baseline; movement over age means the gap changes developmentally.",
        "takeaway_term": "age_months_z",
    },
]

USECOLS = [
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "session_id",
    "age_months",
    "age_bin",
    "role",
    "target_variant",
    "context_k",
    "context_text",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "same_word_count_as_child_real",
    "delta_nb_morphemes_vs_child_real",
    "delta_nb_syllables_cmu_or_pkg_vs_child_real",
    "delta_nb_syllables_pkg_vs_child_real",
    "delta_nb_phonemes_vs_child_real",
    "context_entropy_join_status",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "context_next_top5_mass",
    "context_next_top10_mass",
    "context_next_top50_mass",
    "context_next_argmax_bits",
]
NUMERIC_COLS = [
    "age_months",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "same_word_count_as_child_real",
    "delta_nb_morphemes_vs_child_real",
    "delta_nb_syllables_cmu_or_pkg_vs_child_real",
    "delta_nb_syllables_pkg_vs_child_real",
    "delta_nb_phonemes_vs_child_real",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "context_next_top5_mass",
    "context_next_top10_mass",
    "context_next_top50_mass",
    "context_next_argmax_bits",
]
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


@dataclass(frozen=True)
class ZooData:
    """Bounded data products for the exploratory model zoo."""

    real_k3: pd.DataFrame
    context_real: pd.DataFrame
    baseline_k3: pd.DataFrame
    caretaker_k3: pd.DataFrame
    role_k3: pd.DataFrame
    baseline_deltas: pd.DataFrame
    baseline_trends: pd.DataFrame
    role_trends: pd.DataFrame
    extraction_summary: pd.DataFrame
    entropy_status: pd.DataFrame


def write_markdown_table(frame: pd.DataFrame, *, max_rows: int = 30, digits: int = 4) -> str:
    """Render a small dataframe to a GitHub-flavored Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    rendered = shown.astype(object).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]):
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else f"{value:.{digits}g}")
        else:
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(str(col) for col in rendered.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    body = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, sep, *body])


def format_p(value: object) -> str:
    """Format p-values compactly."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def word_count(text: object) -> int:
    """Count simple surface word tokens in a text field."""

    return len(WORD_RE.findall("" if text is None else str(text).lower()))


def question_type(text: object) -> str:
    """Classify a preceding context into rough question categories."""

    clean = ("" if text is None else str(text)).strip().lower()
    if not clean:
        return "empty/no context"
    starts = clean.split(maxsplit=1)[0].strip("¿¡.,!?;:\"'()[]{}") if clean.split() else ""
    wh_words = {"what", "where", "who", "why", "how", "when", "which", "whose", "whom"}
    yesno_starts = {
        "are",
        "am",
        "is",
        "was",
        "were",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "should",
        "shall",
        "have",
        "has",
        "had",
    }
    if "?" not in clean:
        return "not question"
    if starts in wh_words:
        return "wh-question"
    if starts in yesno_starts:
        return "yes/no question"
    return "other question"


def age_stage(age_months: object) -> str:
    """Return coarse developmental stage labels used for plots."""

    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return "unknown"
    if age < 24:
        return "006-023"
    if age < 36:
        return "024-035"
    if age < 48:
        return "036-047"
    return "048-065"


def coerce_and_derive(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns and derive reusable predictors."""

    out = frame.copy()
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out[np.isfinite(out["sum_bits"]) & (out["sum_bits"] > 0)].copy()
    for col in ["nb_words", "nb_morphemes", "nb_syllables_cmu_or_pkg", "nb_syllables_pkg", "nb_phonemes"]:
        if col in out.columns:
            out = out[np.isfinite(out[col]) & (out[col] > 0)].copy()
    out["context_word_count"] = out.get("context_text", "").map(word_count)
    out["context_char_count"] = out.get("context_text", "").astype(str).str.len()
    out["context_question_type"] = out.get("context_text", "").map(question_type)
    out["age_stage"] = out["age_months"].map(age_stage)
    out["age_after_24"] = np.maximum(out["age_months"] - 24.0, 0.0)
    out["age_after_36"] = np.maximum(out["age_months"] - 36.0, 0.0)
    out["log_nb_words"] = np.log(out["nb_words"])
    out["log_nb_morphemes"] = np.log(out["nb_morphemes"])
    out["log_nb_syllables"] = np.log(out["nb_syllables_cmu_or_pkg"])
    out["log_nb_phonemes"] = np.log(out["nb_phonemes"])
    out["log_context_words_plus1"] = np.log1p(out["context_word_count"])
    out["any_effort_fallback"] = (
        out[["cmu_oov_word_count", "syllable_pkg_fallback_word_count", "g2p_fallback_word_count"]]
        .fillna(0)
        .sum(axis=1)
        .gt(0)
        .astype(int)
    )
    entropy_tokens = out.get("context_entropy_token_count", pd.Series(np.nan, index=out.index))
    out["context_entropy_per_token"] = out["context_entropy_bits"] / entropy_tokens.replace(0, np.nan)
    out["age_bin"] = pd.Categorical(out["age_bin"], AGE_BIN_ORDER, ordered=True)
    return out.reset_index(drop=True)


def add_standardized_columns(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Add z-scored versions of selected columns."""

    out = frame.copy()
    for col in columns:
        if col not in out.columns:
            continue
        values = pd.to_numeric(out[col], errors="coerce")
        std = values.std(ddof=0)
        if not math.isfinite(float(std)) or std == 0:
            out[f"{col}_z"] = 0.0
        else:
            out[f"{col}_z"] = (values - values.mean()) / std
    return out


def stratified_sample(frame: pd.DataFrame, group_cols: Sequence[str], n_per_group: int) -> pd.DataFrame:
    """Return a deterministic sample within groups."""

    if frame.empty:
        return frame.copy()
    rng = np.random.default_rng(SEED)
    parts: list[pd.DataFrame] = []
    for _, group in frame.groupby(list(group_cols), observed=True, dropna=False, sort=False):
        if len(group) <= n_per_group:
            parts.append(group)
        else:
            positions = np.sort(rng.choice(len(group), size=n_per_group, replace=False))
            parts.append(group.iloc[positions])
    return pd.concat(parts, ignore_index=True)


def combine_count_tables(parts: list[pd.DataFrame], group_cols: Sequence[str], count_col: str = "rows") -> pd.DataFrame:
    """Combine per-chunk count tables."""

    if not parts:
        return pd.DataFrame(columns=[*group_cols, count_col])
    return (
        pd.concat(parts, ignore_index=True)
        .groupby(list(group_cols), dropna=False, observed=True)[count_col]
        .sum()
        .reset_index()
        .sort_values(list(group_cols))
    )


def aggregate_chunk_stats(frame: pd.DataFrame, group_cols: Sequence[str], value_cols: Sequence[str]) -> pd.DataFrame:
    """Return count/sum/sum-square sufficient statistics for one chunk."""

    if frame.empty:
        return pd.DataFrame(columns=[*group_cols, "n_rows"])
    out = frame.copy()
    for col in value_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out[f"{col}__sq"] = out[col] ** 2
    agg_spec: dict[str, tuple[str, str]] = {"n_rows": (value_cols[0], "size")}
    for col in value_cols:
        agg_spec[f"{col}__sum"] = (col, "sum")
        agg_spec[f"{col}__sum_sq"] = (f"{col}__sq", "sum")
        agg_spec[f"{col}__valid_n"] = (col, "count")
    return out.groupby(list(group_cols), observed=True, dropna=False).agg(**agg_spec).reset_index()


def combine_aggregate_stats(parts: list[pd.DataFrame], group_cols: Sequence[str], value_cols: Sequence[str]) -> pd.DataFrame:
    """Combine chunk sufficient statistics into means and standard errors."""

    if not parts:
        cols = [*group_cols, "n_rows"]
        for col in value_cols:
            cols.extend([f"{col}_mean", f"{col}_sem", f"{col}_valid_n"])
        return pd.DataFrame(columns=cols)
    raw = pd.concat([part for part in parts if not part.empty], ignore_index=True)
    if raw.empty:
        return pd.DataFrame()
    sum_cols = ["n_rows"]
    for col in value_cols:
        sum_cols.extend([f"{col}__sum", f"{col}__sum_sq", f"{col}__valid_n"])
    combined = raw.groupby(list(group_cols), observed=True, dropna=False)[sum_cols].sum().reset_index()
    for col in value_cols:
        n = combined[f"{col}__valid_n"].astype(float)
        total = combined[f"{col}__sum"].astype(float)
        total_sq = combined[f"{col}__sum_sq"].astype(float)
        combined[f"{col}_mean"] = total / n.replace(0, np.nan)
        variance = (total_sq - (total**2 / n.replace(0, np.nan))) / (n - 1).replace(0, np.nan)
        combined[f"{col}_sem"] = np.sqrt(np.maximum(variance, 0)) / np.sqrt(n.replace(0, np.nan))
        combined.loc[n.le(1), f"{col}_sem"] = np.nan
        combined = combined.rename(columns={f"{col}__valid_n": f"{col}_valid_n"})
    drop_cols = []
    for col in value_cols:
        drop_cols.extend([f"{col}__sum", f"{col}__sum_sq"])
    return combined.drop(columns=drop_cols).sort_values(list(group_cols)).reset_index(drop=True)


def build_baseline_deltas(baseline_rows: pd.DataFrame) -> pd.DataFrame:
    """Pivot row-matched real and baseline child utterances into deltas."""

    if baseline_rows.empty:
        return pd.DataFrame()
    keys = ["utterance_id", "dataset", "child_id", "session_id", "age_months", "age_bin"]
    effort_cols = [col for col, _ in EFFORT_MEASURES]
    metric = baseline_rows[
        keys + ["target_variant", "sum_bits", "bits_per_word", *effort_cols]
    ].copy()
    pivot = metric.pivot_table(
        index=keys,
        columns="target_variant",
        values=["sum_bits", "bits_per_word"],
        aggfunc="first",
        observed=True,
    )
    pivot.columns = [f"{value}_{variant}" for value, variant in pivot.columns]
    out = pivot.reset_index()
    effort = metric[metric["target_variant"].eq("real")][keys + effort_cols].drop_duplicates(keys)
    out = out.merge(effort, on=keys, how="left")
    for variant in ["random", "unigram", "bigram", "trigram"]:
        if f"sum_bits_{variant}" in out.columns:
            out[f"delta_sum_bits_real_minus_{variant}"] = out["sum_bits_real"] - out[f"sum_bits_{variant}"]
        if f"bits_per_word_{variant}" in out.columns:
            out[f"delta_bits_per_word_real_minus_{variant}"] = out["bits_per_word_real"] - out[f"bits_per_word_{variant}"]
    out = add_standardized_columns(coerce_delta_numeric(out), ["age_months", *effort_cols])
    return out


def coerce_delta_numeric(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns in a baseline-delta table."""

    out = frame.copy()
    for col in out.columns:
        if col.startswith(("sum_bits", "bits_per_word", "delta_", "nb_", "age_months")):
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["age_bin"] = pd.Categorical(out["age_bin"], AGE_BIN_ORDER, ordered=True)
    return out


def read_zoo_data(input_csv: Path, output_dir: Path, *, chunksize: int, max_rows: int | None = None) -> ZooData:
    """Read the Route 1 long table and create bounded modeling samples."""

    real_parts: list[pd.DataFrame] = []
    context_parts: list[pd.DataFrame] = []
    baseline_sample_parts: list[pd.DataFrame] = []
    baseline_delta_parts: list[pd.DataFrame] = []
    caretaker_parts: list[pd.DataFrame] = []
    extraction_parts: list[pd.DataFrame] = []
    entropy_parts: list[pd.DataFrame] = []
    baseline_trend_parts: list[pd.DataFrame] = []
    role_trend_parts: list[pd.DataFrame] = []
    trend_value_cols = [
        "sum_bits",
        "bits_per_word",
        "bits_per_phoneme",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_syllables_pkg",
        "nb_phonemes",
    ]
    rows_seen = 0
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        if max_rows is not None:
            remaining = max_rows - rows_seen
            if remaining <= 0:
                break
            chunk = chunk.head(remaining).copy()
        rows_seen += len(chunk)
        extraction_parts.append(
            chunk.groupby(["dataset", "role", "target_variant", "context_k"], dropna=False, observed=True)
            .size()
            .reset_index(name="rows")
        )
        entropy_parts.append(
            chunk.groupby(["role", "target_variant", "context_k", "context_entropy_join_status"], dropna=False, observed=True)
            .size()
            .reset_index(name="rows")
        )
        child_k3_variants = chunk[
            chunk["role"].eq("child")
            & chunk["context_k"].eq("k3")
            & chunk["target_variant"].isin(VARIANT_ORDER)
        ].copy()
        if not child_k3_variants.empty:
            baseline_trend_parts.append(
                aggregate_chunk_stats(child_k3_variants, ["age_bin", "target_variant"], trend_value_cols)
            )
            clean_baseline = coerce_and_derive(child_k3_variants)
            baseline_delta_parts.append(
                clean_baseline[
                    [
                        "utterance_id",
                        "dataset",
                        "child_id",
                        "session_id",
                        "age_months",
                        "age_bin",
                        "target_variant",
                        "sum_bits",
                        "bits_per_word",
                        "nb_words",
                        "nb_morphemes",
                        "nb_syllables_cmu_or_pkg",
                        "nb_syllables_pkg",
                        "nb_phonemes",
                    ]
                ]
            )
            baseline_sample_parts.append(stratified_sample(clean_baseline, ["child_id", "age_bin", "target_variant"], 45))
        real_k3 = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].eq("k3")
        ].copy()
        if not real_k3.empty:
            real_parts.append(stratified_sample(coerce_and_derive(real_k3), ["child_id", "age_bin"], 70))
        context_real = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].isin(["k1", "k2", "k3"])
            & chunk["context_entropy_join_status"].isin(["matched", "matched_text_fallback"])
        ].copy()
        if not context_real.empty:
            context_parts.append(stratified_sample(coerce_and_derive(context_real), ["child_id", "age_bin", "context_k"], 65))
        caretaker_k3 = chunk[
            chunk["role"].eq("caretaker")
            & chunk["target_variant"].eq("caretaker")
            & chunk["context_k"].eq("k3")
        ].copy()
        if not caretaker_k3.empty:
            caretaker_parts.append(stratified_sample(coerce_and_derive(caretaker_k3), ["child_id", "age_bin"], 55))
        role_trend = chunk[
            (
                chunk["role"].eq("child")
                & chunk["target_variant"].eq("real")
                & chunk["context_k"].eq("k3")
            )
            | (
                chunk["role"].eq("caretaker")
                & chunk["target_variant"].eq("caretaker")
                & chunk["context_k"].eq("k3")
            )
        ].copy()
        if not role_trend.empty:
            role_trend["speaker_group"] = np.where(role_trend["role"].eq("child"), "child", "caretaker")
            role_trend_parts.append(
                aggregate_chunk_stats(role_trend, ["age_bin", "speaker_group"], trend_value_cols)
            )
    real_k3 = stratified_sample(pd.concat(real_parts, ignore_index=True), ["child_id", "age_bin"], 120) if real_parts else pd.DataFrame()
    context_real = stratified_sample(pd.concat(context_parts, ignore_index=True), ["child_id", "age_bin", "context_k"], 120) if context_parts else pd.DataFrame()
    baseline_k3 = stratified_sample(pd.concat(baseline_sample_parts, ignore_index=True), ["child_id", "age_bin", "target_variant"], 90) if baseline_sample_parts else pd.DataFrame()
    caretaker_k3 = stratified_sample(pd.concat(caretaker_parts, ignore_index=True), ["child_id", "age_bin"], 100) if caretaker_parts else pd.DataFrame()
    baseline_min = pd.concat(baseline_delta_parts, ignore_index=True) if baseline_delta_parts else pd.DataFrame()
    baseline_deltas = build_baseline_deltas(baseline_min)
    baseline_trends = combine_aggregate_stats(
        baseline_trend_parts,
        ["age_bin", "target_variant"],
        trend_value_cols,
    )
    role_trends = combine_aggregate_stats(
        role_trend_parts,
        ["age_bin", "speaker_group"],
        trend_value_cols,
    )

    for name, frame in [
        ("real_child_k3_sample", real_k3),
        ("child_context_entropy_sample", context_real),
        ("child_baseline_k3_sample", baseline_k3),
        ("caretaker_k3_sample", caretaker_k3),
        ("baseline_delta_table", baseline_deltas),
        ("baseline_trends", baseline_trends),
        ("role_trends", role_trends),
    ]:
        if not frame.empty:
            frame.to_csv(output_dir / f"{name}.csv.gz", index=False)

    role_k3 = pd.concat(
        [
            real_k3.assign(speaker_group="child"),
            caretaker_k3.assign(speaker_group="caretaker"),
        ],
        ignore_index=True,
    ) if not real_k3.empty and not caretaker_k3.empty else pd.DataFrame()

    extraction_summary = combine_count_tables(
        extraction_parts,
        ["dataset", "role", "target_variant", "context_k"],
    )
    entropy_status = combine_count_tables(
        entropy_parts,
        ["role", "target_variant", "context_k", "context_entropy_join_status"],
    )
    extraction_summary.to_csv(output_dir / "extraction_counts.csv", index=False)
    entropy_status.to_csv(output_dir / "entropy_status_counts.csv", index=False)

    z_frames = [real_k3, context_real, baseline_k3, caretaker_k3, role_k3]
    z_cols = [
        "age_months",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_syllables_pkg",
        "nb_phonemes",
        "context_word_count",
        "context_entropy_bits",
        "context_next_top1_prob",
        "context_next_top5_mass",
        "context_next_argmax_bits",
    ]
    standardized = [add_standardized_columns(frame, z_cols) if not frame.empty else frame for frame in z_frames]
    real_k3, context_real, baseline_k3, caretaker_k3, role_k3 = standardized
    return ZooData(
        real_k3=real_k3,
        context_real=context_real,
        baseline_k3=baseline_k3,
        caretaker_k3=caretaker_k3,
        role_k3=role_k3,
        baseline_deltas=baseline_deltas,
        baseline_trends=baseline_trends,
        role_trends=role_trends,
        extraction_summary=extraction_summary,
        entropy_status=entropy_status,
    )


def observed_fitted_r2(model: object | None) -> float:
    """Return OLS R2 when available, otherwise observed/fitted squared correlation."""

    if model is None:
        return math.nan
    if hasattr(model, "rsquared"):
        try:
            return float(model.rsquared)
        except Exception:
            pass
    try:
        observed = np.asarray(model.model.endog, dtype=float)
        fitted = np.asarray(model.fittedvalues, dtype=float)
        mask = np.isfinite(observed) & np.isfinite(fitted)
        if mask.sum() < 3:
            return math.nan
        corr = np.corrcoef(observed[mask], fitted[mask])[0, 1]
        return float(corr * corr)
    except Exception:
        return math.nan


def fit_stats_model(label: str, question: str, formula: str, frame: pd.DataFrame, family: str, *, groups: str = "child_id") -> tuple[object | None, dict[str, object], pd.DataFrame]:
    """Fit one statsmodels model and return model, summary row, coefficients."""

    if frame.empty:
        return None, {"model": label, "question": question, "formula": formula, "family": family, "status": "empty data"}, pd.DataFrame()
    try:
        if family == "ols_cluster":
            result = smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame[groups]})
        elif family == "gee_gaussian":
            result = smf.gee(formula, groups=groups, data=frame, cov_struct=Exchangeable(), family=Gaussian()).fit()
        elif family == "gee_poisson":
            result = smf.gee(formula, groups=groups, data=frame, cov_struct=Exchangeable(), family=Poisson()).fit()
        elif family == "gee_gamma_log":
            result = smf.gee(formula, groups=groups, data=frame, cov_struct=Exchangeable(), family=Gamma(link=Log())).fit()
        elif family == "glm_gamma_log":
            result = smf.glm(formula, data=frame, family=Gamma(link=Log())).fit()
        else:
            raise ValueError(f"unknown family: {family}")
        summary = {
            "model": label,
            "question": question,
            "formula": formula,
            "family": family,
            "status": "fit",
            "n_obs": int(result.nobs),
            "n_children": int(frame[groups].nunique()) if groups in frame.columns else math.nan,
            "r2_or_observed_fitted_r2": observed_fitted_r2(result),
            "aic": float(getattr(result, "aic", math.nan)) if hasattr(result, "aic") else math.nan,
        }
        coefs = coefficient_rows(label, result)
        return result, summary, coefs
    except Exception as exc:
        return None, {
            "model": label,
            "question": question,
            "formula": formula,
            "family": family,
            "status": f"failed: {type(exc).__name__}: {exc}",
        }, pd.DataFrame()


def coefficient_rows(label: str, result: object) -> pd.DataFrame:
    """Extract a coefficient table from a fitted statsmodels result."""

    rows: list[dict[str, object]] = []
    params = getattr(result, "params", pd.Series(dtype=float))
    pvalues = getattr(result, "pvalues", pd.Series(index=params.index, dtype=float))
    bse = getattr(result, "bse", pd.Series(index=params.index, dtype=float))
    for term, estimate in params.items():
        rows.append(
            {
                "model": label,
                "term": term,
                "estimate": float(estimate),
                "std_error": float(bse.get(term, math.nan)),
                "p_value": float(pvalues.get(term, math.nan)),
            }
        )
    return pd.DataFrame(rows)


def fit_model_zoo(data: ZooData, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Fit exploratory research-question models."""

    models: dict[str, object] = {}
    summaries: list[dict[str, object]] = []
    coefficients: list[pd.DataFrame] = []

    specs: list[tuple[str, str, str, pd.DataFrame, str]] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        effort_z = f"{effort_col}_z"
        specs.append(
            (
                f"Z1 Information | child FE | effort={effort_label}",
                f"At the same {effort_label.lower()} level, does child total information change with age after child identity is controlled?",
                f"sum_bits ~ age_months_z + {effort_z} + C(child_id)",
                data.real_k3,
                "ols_cluster",
            )
        )
    for outcome, unit_label, log_effort in EFFORT_DENSITY_OUTCOMES:
        specs.append(
            (
                f"Z2 Information density | nonlinear age | unit={unit_label}",
                f"Does information per {unit_label.lower()} follow a nonlinear developmental trajectory?",
                f"{outcome} ~ age_months_z + I(age_months_z ** 2) + {log_effort} + C(child_id)",
                data.real_k3,
                "ols_cluster",
            )
        )
    for effort_col, effort_label in EFFORT_MEASURES:
        specs.append(
            (
                f"Z3 Effort from context entropy | effort={effort_label}",
                f"Do children produce more {effort_label.lower()} after more uncertain caretaker contexts?",
                f"{effort_col} ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)",
                data.context_real,
                "gee_poisson",
            )
        )
    for effort_col, effort_label in EFFORT_MEASURES:
        effort_z = f"{effort_col}_z"
        specs.append(
            (
                f"Z4 Information from context entropy | effort={effort_label}",
                f"Is total child information related to context entropy after {effort_label.lower()} is controlled?",
                f"sum_bits ~ age_months_z * context_entropy_bits_z + {effort_z} + log_context_words_plus1 + C(context_k)",
                data.context_real,
                "gee_gamma_log",
            )
        )
    for outcome, unit_label, log_effort in EFFORT_DENSITY_OUTCOMES:
        specs.append(
            (
                f"Z5 Context window sensitivity | unit={unit_label}",
                f"Does the age trajectory of information per {unit_label.lower()} change across k1/k2/k3 scoring windows?",
                f"{outcome} ~ age_months_z * C(context_k) + {log_effort} + context_entropy_bits_z",
                data.context_real,
                "gee_gaussian",
            )
        )
    for effort_col, effort_label in EFFORT_MEASURES:
        specs.append(
            (
                f"Z6 Question-type effort | effort={effort_label}",
                f"Does caretaker question type modulate child {effort_label.lower()}, and does that modulation change with age?",
                f"{effort_col} ~ age_months_z * C(context_question_type) + context_entropy_bits_z + log_context_words_plus1",
                data.context_real,
                "gee_poisson",
            )
        )
    for effort_col, effort_label in EFFORT_MEASURES:
        effort_z = f"{effort_col}_z"
        specs.append(
            (
                f"Z7 Baseline comparison | effort={effort_label}",
                f"Do real child utterances differ from random/ngram baselines after controlling {effort_label.lower()}?",
                f"sum_bits ~ age_months_z * C(target_variant) + {effort_z}",
                data.baseline_k3,
                "gee_gamma_log",
            )
        )
    for effort_col, effort_label in EFFORT_MEASURES:
        effort_z = f"{effort_col}_z"
        specs.append(
            (
                f"Z8 Child vs caretaker information | effort={effort_label}",
                f"Do child and caretaker total-bit trajectories differ after controlling {effort_label.lower()}?",
                f"sum_bits ~ age_months_z * C(speaker_group) + {effort_z}",
                data.role_k3,
                "gee_gamma_log",
            )
        )
    for outcome, unit_label, log_effort in EFFORT_DENSITY_OUTCOMES:
        specs.append(
            (
                f"Z9 Information per unit | unit={unit_label}",
                f"Does information per {unit_label.lower()} change with age after child identity is controlled?",
                f"{outcome} ~ age_months_z + {log_effort} + C(child_id)",
                data.real_k3,
                "ols_cluster",
            )
        )
    for effort_col, effort_label in EFFORT_MEASURES:
        specs.append(
            (
                f"Z10 Context certainty | effort={effort_label}",
                f"Is child {effort_label.lower()} lower when the model assigns high probability to the most likely next token?",
                f"{effort_col} ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)",
                data.context_real,
                "gee_poisson",
            )
        )
    for label, question, formula, frame, family in specs:
        model, summary, coefs = fit_stats_model(label, question, formula, frame, family)
        summaries.append(summary)
        if model is not None:
            models[label] = model
        if not coefs.empty:
            coefficients.append(coefs)

    delta_long = baseline_delta_long(data.baseline_deltas)
    if not delta_long.empty:
        model, summary, coefs = fit_stats_model(
            "Z11 Real-minus-baseline delta | no effort control",
            "Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls?",
            "delta_sum_bits ~ age_months_z * C(baseline_variant) + C(child_id)",
            delta_long,
            "ols_cluster",
        )
        summaries.append(summary)
        if model is not None:
            models["Z11 Real-minus-baseline delta | no effort control"] = model
        if not coefs.empty:
            coefficients.append(coefs)
        for effort_col, effort_label in EFFORT_MEASURES:
            effort_z = f"{effort_col}_z"
            if effort_z not in delta_long.columns:
                continue
            model, summary, coefs = fit_stats_model(
                f"Z11 Real-minus-baseline delta | effort={effort_label}",
                f"Does the real-child advantage or penalty relative to each baseline change with age after controlling {effort_label.lower()}?",
                f"delta_sum_bits ~ age_months_z * C(baseline_variant) + {effort_z} + C(child_id)",
                delta_long,
                "ols_cluster",
            )
            summaries.append(summary)
            if model is not None:
                models[f"Z11 Real-minus-baseline delta | effort={effort_label}"] = model
            if not coefs.empty:
                coefficients.append(coefs)

    summary_df = pd.DataFrame(summaries)
    coef_df = pd.concat(coefficients, ignore_index=True) if coefficients else pd.DataFrame()
    summary_df.to_csv(output_dir / "model_zoo_summary.csv", index=False)
    coef_df.to_csv(output_dir / "model_zoo_coefficients.csv", index=False)
    build_zoo_variant_manifest(summary_df, output_dir)
    return summary_df, coef_df, models


def fit_comparison_models(data: ZooData, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit explicit child-vs-baseline and child-vs-caretaker comparison models."""

    summaries: list[dict[str, object]] = []
    coefficients: list[pd.DataFrame] = []
    delta = baseline_delta_long(data.baseline_deltas)
    for variant in ["random", "unigram", "bigram", "trigram"]:
        variant_delta = delta[delta["baseline_variant"].eq(variant)].copy()
        for effort_col, effort_label in EFFORT_MEASURES:
            effort_z = f"{effort_col}_z"
            if effort_z not in variant_delta.columns:
                continue
            model, summary, coefs = fit_stats_model(
                f"Child minus {variant}: total bits | effort={effort_label}",
                f"Does the real-child minus {variant} total-bit gap change with age after controlling {effort_label.lower()} and child identity?",
                f"delta_sum_bits ~ age_months_z + {effort_z} + C(child_id)",
                variant_delta,
                "ols_cluster",
            )
            summaries.append(summary)
            if not coefs.empty:
                coefficients.append(coefs)
        pair = data.baseline_k3[data.baseline_k3["target_variant"].isin(["real", variant])].copy()
        for effort_col, effort_label in EFFORT_MEASURES:
            effort_z = f"{effort_col}_z"
            if effort_z not in pair.columns:
                continue
            model, summary, coefs = fit_stats_model(
                f"Trajectory interaction: child vs {variant} | effort={effort_label}",
                f"Do real child and {variant} total-bit trajectories diverge over age when {effort_label.lower()} is controlled?",
                f"sum_bits ~ age_months_z * C(target_variant) + {effort_z}",
                pair,
                "gee_gamma_log",
            )
            summaries.append(summary)
            if not coefs.empty:
                coefficients.append(coefs)

    if not data.role_k3.empty:
        for effort_col, effort_label in EFFORT_MEASURES:
            effort_z = f"{effort_col}_z"
            if effort_z not in data.role_k3.columns:
                continue
            model, summary, coefs = fit_stats_model(
                f"Child vs caretaker: total bits | effort={effort_label}",
                f"Do child and caretaker total-bit trajectories differ after controlling {effort_label.lower()}?",
                f"sum_bits ~ age_months_z * C(speaker_group) + {effort_z}",
                data.role_k3,
                "gee_gamma_log",
            )
            summaries.append(summary)
            if not coefs.empty:
                coefficients.append(coefs)

    summary_df = pd.DataFrame(summaries)
    coef_df = pd.concat(coefficients, ignore_index=True) if coefficients else pd.DataFrame()
    summary_df.to_csv(output_dir / "comparison_model_summary.csv", index=False)
    coef_df.to_csv(output_dir / "comparison_model_coefficients.csv", index=False)
    return summary_df, coef_df


def baseline_delta_long(delta_table: pd.DataFrame) -> pd.DataFrame:
    """Return long baseline-delta rows for modeling and plotting."""

    if delta_table.empty:
        return pd.DataFrame()
    effort_cols = [col for col, _ in EFFORT_MEASURES]
    parts: list[pd.DataFrame] = []
    for variant in ["random", "unigram", "bigram", "trigram"]:
        col = f"delta_sum_bits_real_minus_{variant}"
        density_col = f"delta_bits_per_word_real_minus_{variant}"
        if col not in delta_table.columns:
            continue
        sub = delta_table[
            [
                "utterance_id",
                "dataset",
                "child_id",
                "session_id",
                "age_months",
                "age_bin",
                *effort_cols,
                col,
                density_col,
            ]
        ].copy()
        sub = sub.rename(columns={col: "delta_sum_bits", density_col: "delta_bits_per_word"})
        sub["baseline_variant"] = variant
        parts.append(sub)
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if out.empty:
        return out
    out = out.dropna(subset=["delta_sum_bits", "age_months", *effort_cols]).copy()
    return add_standardized_columns(out, ["age_months", *effort_cols])


def mean_sem(frame: pd.DataFrame, group_cols: Sequence[str], value_col: str) -> pd.DataFrame:
    """Compute mean, sem, and row count."""

    return (
        frame.dropna(subset=[value_col])
        .groupby(list(group_cols), observed=True)[value_col]
        .agg(mean="mean", sem="sem", n_rows="count")
        .reset_index()
    )


def save_basic_zoo_tables(data: ZooData, output_dir: Path) -> dict[str, pd.DataFrame]:
    """Write aggregate tables used in the exploratory report."""

    question_counts = (
        data.context_real.groupby(["age_bin", "context_question_type"], observed=True).size().reset_index(name="rows")
        if not data.context_real.empty and {"age_bin", "context_question_type"}.issubset(data.context_real.columns)
        else pd.DataFrame(columns=["age_bin", "context_question_type", "rows"])
    )
    role_counts = (
        data.role_k3.groupby(["speaker_group", "age_bin"], observed=True).size().reset_index(name="rows")
        if not data.role_k3.empty and {"speaker_group", "age_bin"}.issubset(data.role_k3.columns)
        else pd.DataFrame(columns=["speaker_group", "age_bin", "rows"])
    )
    tables = {
        "context_question_counts": question_counts,
        "role_counts": role_counts,
        "baseline_delta_long": baseline_delta_long(data.baseline_deltas),
    }
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
    predictor_dict = pd.DataFrame(
        [
            {"predictor": "context_entropy_bits", "meaning": "Mistral next-token entropy after the preceding caretaker context."},
            {"predictor": "context_next_top1_prob", "meaning": "Probability assigned to the single most likely next token after the caretaker context."},
            {"predictor": "context_word_count", "meaning": "Surface word count of the preceding caretaker context window."},
            {"predictor": "context_question_type", "meaning": "Rule-based classification of the caretaker context as wh-question, yes/no question, other question, or not question."},
            {"predictor": "baseline deltas", "meaning": "Real child bits minus matched random/unigram/bigram/trigram bits for the same utterance row and context."},
            {"predictor": "age_after_24 / age_after_36", "meaning": "Piecewise age transforms available for future nonlinear models."},
            {"predictor": "any_effort_fallback", "meaning": "Whether any syllable/phoneme effort count needed an automatic fallback."},
        ]
    )
    predictor_dict.to_csv(output_dir / "derived_predictor_dictionary.csv", index=False)
    return tables


def plot_context_entropy_effort(data: ZooData, fig_dir: Path) -> None:
    """Plot context entropy against child effort and information density."""

    required = {"context_entropy_bits", "nb_words", "bits_per_word", "age_stage"}
    if data.context_real.empty or not required.issubset(data.context_real.columns):
        return
    frame = data.context_real.dropna(subset=["context_entropy_bits", "nb_words", "bits_per_word"]).copy()
    if frame.empty:
        return
    frame["entropy_decile"] = pd.qcut(frame["context_entropy_bits"], q=10, duplicates="drop")
    for outcome, ylabel, filename in [
        ("nb_words", "Child words", "context_entropy_child_words"),
        ("bits_per_word", "Bits per word", "context_entropy_bits_per_word"),
    ]:
        summary = frame.groupby(["entropy_decile", "age_stage"], observed=True).agg(
            context_entropy_bits=("context_entropy_bits", "mean"),
            mean=(outcome, "mean"),
            sem=(outcome, "sem"),
            n_rows=(outcome, "count"),
        ).reset_index()
        fig, ax = plt.subplots(figsize=(8.8, 5.2))
        for stage, group in summary.groupby("age_stage", observed=True):
            group = group.sort_values("context_entropy_bits")
            ax.plot(group["context_entropy_bits"], group["mean"], marker="o", linewidth=2, label=stage)
            ax.fill_between(
                group["context_entropy_bits"].to_numpy(),
                (group["mean"] - 1.96 * group["sem"].fillna(0)).to_numpy(),
                (group["mean"] + 1.96 * group["sem"].fillna(0)).to_numpy(),
                alpha=0.12,
            )
        ax.set_xlabel("Context entropy (bits)")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel + " by context uncertainty")
        ax.grid(alpha=0.22)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, title="Age stage")
        fig.tight_layout()
        fig.savefig(fig_dir / f"{filename}.png", dpi=220)
        fig.savefig(fig_dir / f"{filename}.pdf")
        plt.close(fig)


def age_positions(values: pd.Series) -> pd.Series:
    """Map age-bin labels to plotting positions."""

    x_map = {label: idx for idx, label in enumerate(AGE_BIN_ORDER)}
    return values.astype(str).map(x_map)


def plot_trend_with_sem(
    ax: plt.Axes,
    frame: pd.DataFrame,
    *,
    group_col: str,
    group_order: Sequence[str],
    y_mean_col: str,
    y_sem_col: str,
    palette: Mapping[str, str],
) -> None:
    """Plot age-bin mean trajectories with 95% normal intervals."""

    for group_name in group_order:
        group = frame[frame[group_col].astype(str).eq(str(group_name))].copy()
        if group.empty:
            continue
        group = group.sort_values("age_bin")
        xs = age_positions(group["age_bin"]).to_numpy(dtype=float)
        mean = pd.to_numeric(group[y_mean_col], errors="coerce").to_numpy(dtype=float)
        sem = pd.to_numeric(group[y_sem_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        color = palette.get(str(group_name), None)
        ax.plot(xs, mean, marker="o", linewidth=2.1, label=str(group_name), color=color)
        ax.fill_between(xs, mean - 1.96 * sem, mean + 1.96 * sem, alpha=0.12, color=color)
    ax.set_xticks(range(len(AGE_BIN_ORDER)))
    ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
    ax.grid(alpha=0.22)


def baseline_palette() -> dict[str, str]:
    """Return stable colors for real and generated baselines."""

    return {
        "real": "#1f5a5f",
        "random": "#b9473f",
        "unigram": "#b8872d",
        "bigram": "#4869a8",
        "trigram": "#5f7f3a",
    }


def plot_full_baseline_trajectories(data: ZooData, fig_dir: Path) -> None:
    """Plot all real/generated baseline trajectories using full aggregate rows."""

    trends = data.baseline_trends.copy()
    if trends.empty:
        return
    palette = baseline_palette()
    specs = [
        ("sum_bits_mean", "sum_bits_sem", "Mean total bits", "baseline_all_total_bits"),
        ("bits_per_word_mean", "bits_per_word_sem", "Mean bits per word", "baseline_all_bits_per_word"),
        ("bits_per_phoneme_mean", "bits_per_phoneme_sem", "Mean bits per phoneme", "baseline_all_bits_per_phoneme"),
        ("nb_phonemes_mean", "nb_phonemes_sem", "Mean phonemes", "baseline_all_phoneme_effort"),
    ]
    for mean_col, sem_col, ylabel, filename in specs:
        fig, ax = plt.subplots(figsize=(9.4, 5.4))
        plot_trend_with_sem(
            ax,
            trends,
            group_col="target_variant",
            group_order=VARIANT_ORDER,
            y_mean_col=mean_col,
            y_sem_col=sem_col,
            palette=palette,
        )
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Age bin")
        ax.set_title(ylabel + ": real children and matched baselines")
        ax.legend(title="Target")
        fig.tight_layout()
        fig.savefig(fig_dir / f"{filename}.png", dpi=220)
        fig.savefig(fig_dir / f"{filename}.pdf")
        plt.close(fig)


def plot_effort_profile_by_variant(data: ZooData, fig_dir: Path) -> None:
    """Plot non-word effort differences across variants."""

    trends = data.baseline_trends.copy()
    if trends.empty:
        return
    palette = baseline_palette()
    specs = [
        ("nb_morphemes_mean", "nb_morphemes_sem", "Morphemes"),
        ("nb_syllables_cmu_or_pkg_mean", "nb_syllables_cmu_or_pkg_sem", "Syllables"),
        ("nb_phonemes_mean", "nb_phonemes_sem", "Phonemes"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16.0, 5.0), sharex=True)
    for ax, (mean_col, sem_col, title) in zip(axes, specs):
        plot_trend_with_sem(
            ax,
            trends,
            group_col="target_variant",
            group_order=VARIANT_ORDER,
            y_mean_col=mean_col,
            y_sem_col=sem_col,
            palette=palette,
        )
        ax.set_title(title)
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Mean count")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Target", loc="lower center", ncol=5)
    fig.suptitle("Baseline Effort Profiles Beyond Word Count", y=0.98)
    fig.tight_layout(rect=(0, 0.11, 1, 0.92))
    fig.savefig(fig_dir / "baseline_effort_profiles_nonword_units.png", dpi=220)
    fig.savefig(fig_dir / "baseline_effort_profiles_nonword_units.pdf")
    plt.close(fig)


def baseline_delta_summary(data: ZooData) -> pd.DataFrame:
    """Return full real-minus-baseline mean/SEM trajectories."""

    delta = baseline_delta_long(data.baseline_deltas)
    if delta.empty:
        return pd.DataFrame()
    summaries = []
    for outcome in ["delta_sum_bits", "delta_bits_per_word"]:
        summary = mean_sem(delta, ["age_bin", "baseline_variant"], outcome)
        summary["outcome"] = outcome
        summaries.append(summary)
    return pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()


def plot_pairwise_baseline_dashboards(data: ZooData, fig_dir: Path) -> None:
    """Write one dashboard per child-vs-baseline comparison."""

    trends = data.baseline_trends.copy()
    deltas = baseline_delta_summary(data)
    if trends.empty or deltas.empty:
        return
    palette = baseline_palette()
    for variant in ["random", "unigram", "bigram", "trigram"]:
        pair = trends[trends["target_variant"].isin(["real", variant])].copy()
        delta_pair = deltas[deltas["baseline_variant"].eq(variant)].copy()
        fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.0))
        plot_trend_with_sem(
            axes[0, 0],
            pair,
            group_col="target_variant",
            group_order=["real", variant],
            y_mean_col="sum_bits_mean",
            y_sem_col="sum_bits_sem",
            palette=palette,
        )
        axes[0, 0].set_title("Total bits")
        axes[0, 0].set_ylabel("Mean total bits")
        plot_trend_with_sem(
            axes[0, 1],
            pair,
            group_col="target_variant",
            group_order=["real", variant],
            y_mean_col="bits_per_word_mean",
            y_sem_col="bits_per_word_sem",
            palette=palette,
        )
        axes[0, 1].set_title("Bits per word")
        axes[0, 1].set_ylabel("Mean bits per word")
        for ax, outcome, title, ylabel in [
            (axes[1, 0], "delta_sum_bits", "Real minus baseline: total bits", "Delta total bits"),
            (axes[1, 1], "delta_bits_per_word", "Real minus baseline: bits per word", "Delta bits per word"),
        ]:
            sub = delta_pair[delta_pair["outcome"].eq(outcome)].sort_values("age_bin")
            xs = age_positions(sub["age_bin"]).to_numpy(dtype=float)
            mean = sub["mean"].to_numpy(dtype=float)
            sem = sub["sem"].fillna(0).to_numpy(dtype=float)
            ax.axhline(0, color="#303030", linewidth=1)
            ax.plot(xs, mean, marker="o", linewidth=2.2, color="#6f4c9b")
            ax.fill_between(xs, mean - 1.96 * sem, mean + 1.96 * sem, color="#6f4c9b", alpha=0.14)
            ax.set_xticks(range(len(AGE_BIN_ORDER)))
            ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
            ax.set_title(title)
            ax.set_ylabel(ylabel)
            ax.set_xlabel("Age bin")
            ax.grid(alpha=0.22)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, title="Target", loc="lower center", ncol=2)
        fig.suptitle(f"Real Child vs {variant.capitalize()} Baseline", y=0.98)
        fig.tight_layout(rect=(0, 0.07, 1, 0.94))
        stem = f"child_vs_{variant}_dashboard"
        fig.savefig(fig_dir / f"{stem}.png", dpi=220)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)


def plot_child_caretaker_dashboard(data: ZooData, fig_dir: Path) -> None:
    """Plot child versus caretaker trajectories using full aggregate rows."""

    trends = data.role_trends.copy()
    if trends.empty:
        return
    palette = {"child": "#1f5a5f", "caretaker": "#c76f2c"}
    specs = [
        ("sum_bits_mean", "sum_bits_sem", "Total bits", "Mean total bits"),
        ("bits_per_word_mean", "bits_per_word_sem", "Bits per word", "Mean bits per word"),
        ("nb_words_mean", "nb_words_sem", "Word effort", "Mean words"),
        ("nb_phonemes_mean", "nb_phonemes_sem", "Phoneme effort", "Mean phonemes"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 8.8))
    for ax, (mean_col, sem_col, title, ylabel) in zip(axes.flatten(), specs):
        plot_trend_with_sem(
            ax,
            trends,
            group_col="speaker_group",
            group_order=["child", "caretaker"],
            y_mean_col=mean_col,
            y_sem_col=sem_col,
            palette=palette,
        )
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Age bin")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Speaker", loc="lower center", ncol=2)
    fig.suptitle("Children and Caretakers Over Child Age", y=0.98)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(fig_dir / "child_vs_caretaker_dashboard.png", dpi=220)
    fig.savefig(fig_dir / "child_vs_caretaker_dashboard.pdf")
    plt.close(fig)


def plot_baseline_deltas(data: ZooData, fig_dir: Path) -> None:
    """Plot real-minus-baseline deltas by age."""

    delta = baseline_delta_long(data.baseline_deltas)
    if delta.empty:
        return
    for outcome, ylabel, filename in [
        ("delta_sum_bits", "Real child bits minus baseline bits", "baseline_delta_sum_bits_by_age"),
        ("delta_bits_per_word", "Real child bits/word minus baseline bits/word", "baseline_delta_bits_per_word_by_age"),
    ]:
        summary = mean_sem(delta, ["age_bin", "baseline_variant"], outcome)
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        x_map = {label: idx for idx, label in enumerate(AGE_BIN_ORDER)}
        for variant, group in summary.groupby("baseline_variant", observed=True):
            group = group.sort_values("age_bin")
            xs = group["age_bin"].astype(str).map(x_map)
            ax.plot(xs, group["mean"], marker="o", linewidth=2, label=variant)
            ax.fill_between(
                xs.to_numpy(dtype=float),
                (group["mean"] - 1.96 * group["sem"].fillna(0)).to_numpy(),
                (group["mean"] + 1.96 * group["sem"].fillna(0)).to_numpy(),
                alpha=0.12,
            )
        ax.axhline(0, color="#303030", linewidth=1)
        ax.set_xticks(range(len(AGE_BIN_ORDER)))
        ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
        ax.set_xlabel("Age bin")
        ax.set_ylabel(ylabel)
        ax.set_title("Matched real-minus-baseline gap")
        ax.grid(alpha=0.22)
        ax.legend(title="Baseline")
        fig.tight_layout()
        fig.savefig(fig_dir / f"{filename}.png", dpi=220)
        fig.savefig(fig_dir / f"{filename}.pdf")
        plt.close(fig)


def plot_question_effort(data: ZooData, fig_dir: Path) -> None:
    """Plot effort by caretaker question type."""

    required = {"context_question_type", "age_bin", "nb_words"}
    if data.context_real.empty or not required.issubset(data.context_real.columns):
        return
    frame = data.context_real.copy()
    if frame.empty:
        return
    keep = ["not question", "wh-question", "yes/no question", "other question"]
    frame = frame[frame["context_question_type"].isin(keep)].copy()
    summary = mean_sem(frame, ["age_bin", "context_question_type"], "nb_words")
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    x_map = {label: idx for idx, label in enumerate(AGE_BIN_ORDER)}
    for qtype, group in summary.groupby("context_question_type", observed=True):
        group = group.sort_values("age_bin")
        xs = group["age_bin"].astype(str).map(x_map)
        ax.plot(xs, group["mean"], marker="o", linewidth=2, label=qtype)
    ax.set_xticks(range(len(AGE_BIN_ORDER)))
    ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
    ax.set_ylabel("Mean child words")
    ax.set_xlabel("Age bin")
    ax.set_title("Child effort by preceding caretaker context type")
    ax.grid(alpha=0.22)
    ax.legend(title="Context type")
    fig.tight_layout()
    fig.savefig(fig_dir / "question_type_child_words_by_age.png", dpi=220)
    fig.savefig(fig_dir / "question_type_child_words_by_age.pdf")
    plt.close(fig)


def plot_role_comparison(data: ZooData, fig_dir: Path) -> None:
    """Plot child versus caretaker information density."""

    required = {"age_bin", "speaker_group", "bits_per_word"}
    if data.role_k3.empty or not required.issubset(data.role_k3.columns):
        return
    frame = data.role_k3.copy()
    if frame.empty:
        return
    summary = mean_sem(frame, ["age_bin", "speaker_group"], "bits_per_word")
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    x_map = {label: idx for idx, label in enumerate(AGE_BIN_ORDER)}
    for role, group in summary.groupby("speaker_group", observed=True):
        group = group.sort_values("age_bin")
        xs = group["age_bin"].astype(str).map(x_map)
        ax.plot(xs, group["mean"], marker="o", linewidth=2.2, label=role)
        ax.fill_between(
            xs.to_numpy(dtype=float),
            (group["mean"] - 1.96 * group["sem"].fillna(0)).to_numpy(),
            (group["mean"] + 1.96 * group["sem"].fillna(0)).to_numpy(),
            alpha=0.13,
        )
    ax.set_xticks(range(len(AGE_BIN_ORDER)))
    ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
    ax.set_ylabel("Bits per word")
    ax.set_xlabel("Child age bin")
    ax.set_title("Child and caretaker information density")
    ax.grid(alpha=0.22)
    ax.legend(title="Speaker group")
    fig.tight_layout()
    fig.savefig(fig_dir / "child_vs_caretaker_bits_per_word_by_age.png", dpi=220)
    fig.savefig(fig_dir / "child_vs_caretaker_bits_per_word_by_age.pdf")
    plt.close(fig)


def plot_model_coefficient_heatmap(coefs: pd.DataFrame, fig_dir: Path) -> None:
    """Plot key model coefficients in one heatmap."""

    if coefs.empty:
        return
    wanted_terms = [
        "age_months_z",
        "context_entropy_bits_z",
        "age_months_z:context_entropy_bits_z",
        "context_next_top1_prob_z",
        "age_months_z:context_next_top1_prob_z",
        "nb_words_z",
        "log_nb_words",
    ]
    sub = coefs[coefs["term"].isin(wanted_terms)].copy()
    if sub.empty:
        return
    pivot = sub.pivot_table(index="model", columns="term", values="estimate", aggfunc="first")
    fig_height = max(4.8, 0.38 * len(pivot) + 2.0)
    fig, ax = plt.subplots(figsize=(12.5, fig_height))
    sns.heatmap(pivot, ax=ax, center=0, cmap="vlag", annot=True, fmt=".3g", cbar_kws={"label": "Coefficient"})
    ax.set_title("Key coefficients across exploratory models")
    ax.set_xlabel("Term")
    ax.set_ylabel("Model")
    fig.tight_layout()
    fig.savefig(fig_dir / "model_zoo_key_coefficients.png", dpi=220)
    fig.savefig(fig_dir / "model_zoo_key_coefficients.pdf")
    plt.close(fig)


def parse_effort_controlled_model_name(model_name: object) -> tuple[str, str]:
    """Split a comparison-model label into family and effort-control label."""

    text = str(model_name)
    if " | effort=" not in text:
        return text, ""
    family, effort = text.split(" | effort=", 1)
    return family, effort


def zoo_card_for_model(model_name: object) -> Mapping[str, str] | None:
    """Return the model-family card matching a zoo model name."""

    text = str(model_name)
    for card in ZOO_CARD_DEFS:
        if text.startswith(str(card["model"])):
            return card
    return None


def model_subvariant_label(model_name: object) -> str:
    """Return the meaningful suffix that distinguishes model subvariants."""

    text = str(model_name)
    for separator in [" | effort=", " | unit="]:
        if separator in text:
            suffix = text.split(separator, 1)[1]
            label = "effort" if separator.endswith("effort=") else "unit"
            return f"{label}: {suffix}"
    return "main specification"


def build_zoo_variant_manifest(summary: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Write a model-family/subvariant manifest for the expanded zoo."""

    rows: list[dict[str, object]] = []
    if summary.empty:
        manifest = pd.DataFrame()
    else:
        for row in summary.to_dict(orient="records"):
            card = zoo_card_for_model(row.get("model", ""))
            if card is None:
                continue
            rows.append(
                {
                    "family_id": card["short"],
                    "family_title": card["title"],
                    "subvariant": model_subvariant_label(row.get("model", "")),
                    "model": row.get("model", ""),
                    "question": row.get("question", ""),
                    "formula": row.get("formula", ""),
                    "estimator": row.get("family", ""),
                    "status": row.get("status", ""),
                    "n_obs": row.get("n_obs", math.nan),
                    "n_children": row.get("n_children", math.nan),
                    "r2_or_observed_fitted_r2": row.get("r2_or_observed_fitted_r2", math.nan),
                }
            )
        manifest = pd.DataFrame(rows)
    manifest.to_csv(output_dir / "zoo_model_variant_manifest.csv", index=False)
    return manifest


def is_reportable_zoo_term(term: object) -> bool:
    """Return True for coefficients worth showing in compact zoo plots."""

    text = str(term)
    if text == "Intercept" or text.startswith("C(child_id)"):
        return False
    keep_fragments = [
        "age_months_z",
        "context_entropy",
        "context_next_top1_prob",
        "nb_words_z",
        "nb_morphemes_z",
        "nb_syllables_cmu_or_pkg_z",
        "nb_syllables_pkg_z",
        "nb_phonemes_z",
        "log_",
        "C(target_variant)",
        "C(baseline_variant)",
        "C(speaker_group)",
        "C(context_k)",
        "C(context_question_type)",
    ]
    return any(fragment in text for fragment in keep_fragments)


def pretty_term(term: object) -> str:
    """Shorten statsmodels term names for plot labels."""

    text = str(term)
    replacements = {
        "age_months_z": "age",
        "context_entropy_bits_z": "context entropy",
        "context_next_top1_prob_z": "top1 certainty",
        "nb_words_z": "words",
        "nb_morphemes_z": "morphemes",
        "nb_syllables_cmu_or_pkg_z": "syllables cmu/pkg",
        "nb_syllables_pkg_z": "syllables pkg",
        "nb_phonemes_z": "phonemes",
        "log_context_words_plus1": "log context words",
        "log_nb_words": "log words",
        "log_nb_morphemes": "log morphemes",
        "log_nb_syllables": "log syllables",
        "log_nb_phonemes": "log phonemes",
        "C(target_variant)": "target",
        "C(baseline_variant)": "baseline",
        "C(speaker_group)": "speaker",
        "C(context_k)": "context window",
        "C(context_question_type)": "question type",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("[T.", "=").replace("]", "")
    return text[:80]


def plot_effort_controlled_comparison_overview(summary: pd.DataFrame, coefs: pd.DataFrame, fig_dir: Path) -> None:
    """Plot compact diagnostics for effort-controlled comparison models."""

    model_text = summary.get("model", pd.Series(dtype=str)).astype(str)
    comparison_mask = model_text.str.contains(" | effort=", regex=False, na=False) & model_text.str.startswith(
        ("Child minus", "Trajectory interaction", "Child vs caretaker", "Z7", "Z8", "Z11"),
        na=False,
    )
    comparison = summary[comparison_mask].copy()
    if comparison.empty:
        return
    parsed = comparison["model"].map(parse_effort_controlled_model_name)
    comparison["comparison_family"] = [item[0] for item in parsed]
    comparison["effort_control"] = [item[1] for item in parsed]
    effort_order = [label for _, label in EFFORT_MEASURES]
    family_order = comparison["comparison_family"].drop_duplicates().tolist()
    pivot = comparison.pivot_table(
        index="comparison_family",
        columns="effort_control",
        values="r2_or_observed_fitted_r2",
        aggfunc="first",
        observed=True,
    ).reindex(index=family_order, columns=effort_order)
    fig, ax = plt.subplots(figsize=(12.8, max(6.2, 0.34 * len(pivot) + 2.0)))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap="crest",
        annot=True,
        fmt=".3f",
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"label": "Observed/fitted R2"},
    )
    ax.set_title("Effort-Controlled Comparison Model Fit")
    ax.set_xlabel("Effort control")
    ax.set_ylabel("Comparison model")
    fig.tight_layout()
    fig.savefig(fig_dir / "effort_controlled_comparison_model_r2.png", dpi=230)
    fig.savefig(fig_dir / "effort_controlled_comparison_model_r2.pdf")
    plt.close(fig)

    coef_model_text = coefs.get("model", pd.Series(dtype=str)).astype(str)
    coef_term_text = coefs.get("term", pd.Series(dtype=str)).astype(str)
    coef_rows = coefs[
        coef_model_text.str.contains(" | effort=", regex=False, na=False)
        & coef_model_text.str.startswith(("Child minus", "Trajectory interaction", "Child vs caretaker", "Z7", "Z8", "Z11"), na=False)
        & (
            coef_term_text.eq("age_months_z")
            | coef_term_text.str.contains("age_months_z:C", regex=False, na=False)
        )
    ].copy()
    if coef_rows.empty:
        return
    parsed = coef_rows["model"].map(parse_effort_controlled_model_name)
    coef_rows["comparison_family"] = [item[0] for item in parsed]
    coef_rows["effort_control"] = [item[1] for item in parsed]
    coef_rows["coefficient"] = np.where(
        coef_rows["term"].astype(str).str.contains(":C", regex=False),
        "age interaction",
        "age main effect",
    )
    coef_rows["plot_label"] = coef_rows["comparison_family"].str.replace("Trajectory interaction: ", "", regex=False).str.replace("Child minus ", "Delta: ", regex=False)
    fig, ax = plt.subplots(figsize=(13.5, max(6.0, 0.24 * len(coef_rows) + 1.8)))
    sns.pointplot(
        data=coef_rows,
        x="estimate",
        y="plot_label",
        hue="effort_control",
        dodge=0.45,
        errorbar=None,
        linestyle="none",
        ax=ax,
        palette="colorblind",
    )
    ax.axvline(0, color="#303030", linewidth=1)
    ax.set_title("Age Coefficients in Effort-Controlled Comparisons")
    ax.set_xlabel("Coefficient estimate")
    ax.set_ylabel("Comparison")
    ax.grid(axis="x", alpha=0.18)
    ax.legend(title="Effort control", loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.tight_layout(rect=(0, 0, 0.82, 1))
    fig.savefig(fig_dir / "effort_controlled_comparison_age_coefficients.png", dpi=230)
    fig.savefig(fig_dir / "effort_controlled_comparison_age_coefficients.pdf")
    plt.close(fig)


def plot_zoo_family_coefficients(coefs: pd.DataFrame, fig_dir: Path) -> None:
    """Write one compact coefficient plot per zoo model family."""

    if coefs.empty or "model" not in coefs.columns or "term" not in coefs.columns:
        return
    for card in ZOO_CARD_DEFS:
        sub = coefs[
            coefs["model"].astype(str).str.startswith(str(card["model"]), na=False)
            & coefs["term"].map(is_reportable_zoo_term)
        ].copy()
        if sub.empty:
            continue
        sub["subvariant"] = sub["model"].map(model_subvariant_label)
        sub["term_label"] = sub["term"].map(pretty_term)
        sub["plot_label"] = sub["subvariant"] + " | " + sub["term_label"]
        sub = sub.sort_values(["subvariant", "term_label"]).head(36)
        estimates = pd.to_numeric(sub["estimate"], errors="coerce").to_numpy(dtype=float)
        errors = 1.96 * pd.to_numeric(sub["std_error"], errors="coerce").fillna(0).to_numpy(dtype=float)
        y = np.arange(len(sub))
        fig, ax = plt.subplots(figsize=(10.5, max(5.0, 0.28 * len(sub) + 1.8)))
        ax.errorbar(estimates, y, xerr=errors, fmt="o", color="#315f72", ecolor="#8fb3bf", capsize=3)
        ax.axvline(0, color="#303030", linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels(sub["plot_label"])
        ax.set_xlabel("Coefficient estimate with approximate 95% interval")
        ax.set_ylabel("Subvariant and coefficient")
        ax.set_title(f"{card['short']}: Key Coefficients Across Subvariants")
        ax.grid(axis="x", alpha=0.18)
        fig.tight_layout()
        stem = f"{str(card['short']).lower()}_family_coefficients"
        fig.savefig(fig_dir / f"{stem}.png", dpi=230)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)


def plot_predictor_correlation(data: ZooData, fig_dir: Path) -> pd.DataFrame:
    """Plot correlations among derived predictors."""

    if data.context_real.empty:
        return pd.DataFrame()
    cols = [
        "age_months",
        "nb_words",
        "nb_phonemes",
        "context_word_count",
        "context_entropy_bits",
        "context_next_top1_prob",
        "context_next_top5_mass",
        "bits_per_word",
    ]
    existing_cols = [col for col in cols if col in data.context_real.columns]
    if len(existing_cols) < 2:
        return pd.DataFrame()
    frame = data.context_real[existing_cols].copy()
    corr = frame.apply(pd.to_numeric, errors="coerce").corr()
    fig, ax = plt.subplots(figsize=(8.6, 7.0))
    sns.heatmap(corr, ax=ax, center=0, vmin=-1, vmax=1, cmap="vlag", annot=True, fmt=".2f", square=True)
    ax.set_title("Exploratory predictor correlations")
    fig.tight_layout()
    fig.savefig(fig_dir / "exploratory_predictor_correlation.png", dpi=220)
    fig.savefig(fig_dir / "exploratory_predictor_correlation.pdf")
    plt.close(fig)
    return corr


def sample_for_plot(frame: pd.DataFrame, *, n: int = 12000) -> pd.DataFrame:
    """Return a deterministic plotting sample."""

    if len(frame) <= n:
        return frame.copy()
    return frame.sample(n=n, random_state=SEED).copy()


def save_plot(fig: plt.Figure, fig_dir: Path, stem: str) -> None:
    """Save a report plot as PNG and PDF."""

    fig.tight_layout()
    fig.savefig(fig_dir / f"{stem}.png", dpi=230)
    fig.savefig(fig_dir / f"{stem}.pdf")
    plt.close(fig)


def plot_zoo_model_card_figures(data: ZooData, fig_dir: Path) -> None:
    """Write one readable figure for each expanded model-atlas card."""

    fig_dir.mkdir(parents=True, exist_ok=True)

    # Z1
    if not data.real_k3.empty:
        frame = sample_for_plot(data.real_k3.dropna(subset=["age_months", "sum_bits"]))
        means = (
            data.real_k3.dropna(subset=["age_months", "sum_bits"])
            .groupby("age_bin", observed=True)
            .agg(age_months=("age_months", "mean"), mean=("sum_bits", "mean"))
            .reset_index()
        )
        fig, ax = plt.subplots(figsize=(8.7, 5.2))
        sns.regplot(data=frame, x="age_months", y="sum_bits", scatter_kws={"s": 8, "alpha": 0.10}, line_kws={"linewidth": 2.4, "color": "#1f5a5f"}, ax=ax)
        ax.plot(means["age_months"], means["mean"], marker="o", linewidth=0, color="#b9473f", label="Age-bin means")
        ax.set_title("Z1: Real Child Total Bits by Age")
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Total bits")
        ax.legend()
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z1_information_child_fe_age")

        fig, ax = plt.subplots(figsize=(8.7, 5.2))
        sns.regplot(
            data=frame.dropna(subset=["bits_per_word"]),
            x="age_months",
            y="bits_per_word",
            order=2,
            scatter_kws={"s": 8, "alpha": 0.10},
            line_kws={"linewidth": 2.4, "color": "#4869a8"},
            ax=ax,
        )
        ax.set_title("Z2: Nonlinear Bits Per Word by Age")
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Bits per word")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z2_nonlinear_information_density")

        fig, ax = plt.subplots(figsize=(8.7, 5.2))
        sns.regplot(
            data=frame.dropna(subset=["bits_per_phoneme"]),
            x="age_months",
            y="bits_per_phoneme",
            scatter_kws={"s": 8, "alpha": 0.10},
            line_kws={"linewidth": 2.4, "color": "#5f7f3a"},
            ax=ax,
        )
        ax.set_title("Z9: Information Per Phoneme by Age")
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Bits per phoneme")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z9_phonological_efficiency")

    # Z3, Z4, Z10
    if not data.context_real.empty:
        frame = sample_for_plot(data.context_real.dropna(subset=["context_entropy_bits", "nb_words", "bits_per_word", "sum_bits"]))
        fig, ax = plt.subplots(figsize=(8.7, 5.2))
        sns.regplot(
            data=frame,
            x="context_entropy_bits",
            y="nb_words",
            scatter_kws={"s": 8, "alpha": 0.08},
            line_kws={"linewidth": 2.4, "color": "#b8872d"},
            ax=ax,
        )
        ax.set_title("Z3: Child Word Effort by Context Entropy")
        ax.set_xlabel("Context entropy (bits)")
        ax.set_ylabel("Child words")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z3_context_entropy_effort")

        fig, ax = plt.subplots(figsize=(8.7, 5.2))
        sns.regplot(
            data=frame,
            x="context_entropy_bits",
            y="sum_bits",
            scatter_kws={"s": 8, "alpha": 0.08},
            line_kws={"linewidth": 2.4, "color": "#4869a8"},
            ax=ax,
        )
        ax.set_title("Z4: Total Bits by Context Entropy")
        ax.set_xlabel("Context entropy (bits)")
        ax.set_ylabel("Total bits")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z4_context_entropy_density")

        if "context_next_top1_prob" in frame.columns:
            certainty = frame.dropna(subset=["context_next_top1_prob", "nb_words"])
            fig, ax = plt.subplots(figsize=(8.7, 5.2))
            sns.regplot(
                data=certainty,
                x="context_next_top1_prob",
                y="nb_words",
                scatter_kws={"s": 8, "alpha": 0.08},
                line_kws={"linewidth": 2.4, "color": "#b9473f"},
                ax=ax,
            )
            ax.set_title("Z10: Child Word Effort by Context Certainty")
            ax.set_xlabel("Top-1 next-token probability")
            ax.set_ylabel("Child words")
            ax.grid(alpha=0.20)
            save_plot(fig, fig_dir, "z10_context_certainty_effort")

        # Z5
        summary = mean_sem(data.context_real, ["age_bin", "context_k"], "bits_per_word")
        fig, ax = plt.subplots(figsize=(8.9, 5.3))
        palette = {"k1": "#4c78a8", "k2": "#f58518", "k3": "#54a24b"}
        for context_k, group in summary.groupby("context_k", observed=True):
            group = group.sort_values("age_bin")
            xs = age_positions(group["age_bin"]).to_numpy(dtype=float)
            color = palette.get(str(context_k))
            ax.plot(xs, group["mean"], marker="o", linewidth=2.2, color=color, label=str(context_k))
            ax.fill_between(xs, group["mean"] - 1.96 * group["sem"].fillna(0), group["mean"] + 1.96 * group["sem"].fillna(0), color=color, alpha=0.12)
        ax.set_xticks(range(len(AGE_BIN_ORDER)))
        ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
        ax.set_title("Z5: Bits Per Word by Scoring Context Window")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Bits per word")
        ax.legend(title="Context window")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z5_context_window_sensitivity")

        # Z6
        keep = ["not question", "wh-question", "yes/no question", "other question"]
        qframe = data.context_real[data.context_real["context_question_type"].isin(keep)].copy()
        summary = mean_sem(qframe, ["age_bin", "context_question_type"], "nb_words")
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        for qtype, group in summary.groupby("context_question_type", observed=True):
            group = group.sort_values("age_bin")
            xs = age_positions(group["age_bin"]).to_numpy(dtype=float)
            ax.plot(xs, group["mean"], marker="o", linewidth=2.0, label=str(qtype))
        ax.set_xticks(range(len(AGE_BIN_ORDER)))
        ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
        ax.set_title("Z6: Child Word Effort by Caretaker Context Type")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Child words")
        ax.legend(title="Context type")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z6_question_type_effort")

    # Z7
    if not data.baseline_trends.empty:
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        plot_trend_with_sem(
            ax,
            data.baseline_trends,
            group_col="target_variant",
            group_order=VARIANT_ORDER,
            y_mean_col="sum_bits_mean",
            y_sem_col="sum_bits_sem",
            palette=baseline_palette(),
        )
        ax.set_title("Z7: Real Children and Matched Baselines")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Mean total bits")
        ax.legend(title="Target")
        save_plot(fig, fig_dir, "z7_baseline_comparison")

    # Z8
    if not data.role_trends.empty:
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        plot_trend_with_sem(
            ax,
            data.role_trends,
            group_col="speaker_group",
            group_order=["child", "caretaker"],
            y_mean_col="bits_per_word_mean",
            y_sem_col="bits_per_word_sem",
            palette={"child": "#1f5a5f", "caretaker": "#c76f2c"},
        )
        ax.set_title("Z8: Child and Caretaker Information Density")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Mean bits per word")
        ax.legend(title="Speaker")
        save_plot(fig, fig_dir, "z8_child_caretaker_density")

    # Z11
    deltas = baseline_delta_summary(data)
    if not deltas.empty:
        delta_sum = deltas[deltas["outcome"].eq("delta_sum_bits")].copy()
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        for variant, group in delta_sum.groupby("baseline_variant", observed=True):
            group = group.sort_values("age_bin")
            xs = age_positions(group["age_bin"]).to_numpy(dtype=float)
            ax.plot(xs, group["mean"], marker="o", linewidth=2.0, label=str(variant))
            ax.fill_between(xs, group["mean"] - 1.96 * group["sem"].fillna(0), group["mean"] + 1.96 * group["sem"].fillna(0), alpha=0.12)
        ax.axhline(0, color="#303030", linewidth=1)
        ax.set_xticks(range(len(AGE_BIN_ORDER)))
        ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
        ax.set_title("Z11: Real Minus Baseline Total Bits")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Real child bits minus baseline bits")
        ax.legend(title="Baseline")
        ax.grid(alpha=0.20)
        save_plot(fig, fig_dir, "z11_real_minus_baseline_delta")


def plot_exploratory_figures(data: ZooData, summary: pd.DataFrame, coefs: pd.DataFrame, output_dir: Path, fig_dir: Path) -> None:
    """Write all exploratory figures and table outputs."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    plot_full_baseline_trajectories(data, fig_dir)
    plot_effort_profile_by_variant(data, fig_dir)
    plot_pairwise_baseline_dashboards(data, fig_dir)
    plot_child_caretaker_dashboard(data, fig_dir)
    plot_context_entropy_effort(data, fig_dir)
    plot_baseline_deltas(data, fig_dir)
    plot_question_effort(data, fig_dir)
    plot_role_comparison(data, fig_dir)
    plot_model_coefficient_heatmap(coefs, fig_dir)
    plot_effort_controlled_comparison_overview(summary, coefs, fig_dir)
    plot_zoo_family_coefficients(coefs, fig_dir)
    plot_zoo_model_card_figures(data, fig_dir)
    corr = plot_predictor_correlation(data, fig_dir)
    corr.to_csv(output_dir / "exploratory_predictor_correlation.csv")


def write_extended_m123_report(*, output_dir: Path, md_path: Path, html_path: Path) -> None:
    """Write a more detailed interpretive report for the existing M1/M2/M3 outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    expanded = pd.read_csv(M123_OUTPUT_DIR / "expanded_model_family_summary.csv")
    basic = pd.read_csv(M123_OUTPUT_DIR / "model_fit_summary.csv")
    vif = pd.read_csv(M123_OUTPUT_DIR / "vif_diagnostic.csv")
    age_bins = pd.read_csv(M123_OUTPUT_DIR / "by_age_bin.csv")
    m1 = basic[basic["model_id"].eq("M1")][["effort_label", "r2"]].rename(columns={"r2": "m1_r2"})
    m2 = basic[basic["model_id"].eq("M2")][["effort_label", "r2"]].rename(columns={"r2": "m2_r2"})
    age_effects = expanded[
        expanded["model_family_id"].isin(["ols_cluster", "ols_child_fe", "ols_child_fe_interaction"])
        & expanded["effort_label"].isin([label for _, label in EFFORT_MEASURES])
    ][["approach_id", "model_family_label", "effort_label", "age_coef", "age_p", "effort_coef", "age_effort_coef", "age_effort_p", "r2_observed_fitted"]].copy()
    age_effects["age_p"] = age_effects["age_p"].map(format_p)
    age_effects["age_effort_p"] = age_effects["age_effort_p"].map(format_p)
    sign = (
        expanded[expanded["model_family_id"].isin(["ols_cluster", "ols_child_fe"])]
        .pivot_table(index="effort_label", columns="approach_id", values="age_coef", aggfunc="first")
        .reset_index()
    )
    if {"M1", "M2"}.issubset(sign.columns):
        sign["interpretation"] = np.where(
            np.sign(sign["M1"]) == np.sign(sign["M2"]),
            "same direction",
            "direction changes after child identity is added",
        )
    sign = sign.merge(m1, on="effort_label", how="left").merge(m2, on="effort_label", how="left")
    m3_focus = expanded[
        expanded["approach_id"].eq("M3")
        & expanded["model_family_id"].isin(["ols_cluster_interaction", "ols_child_fe_interaction", "gee_gaussian_interaction"])
    ][["model_family_label", "effort_label", "r2_observed_fitted", "age_coef", "effort_coef", "age_effort_coef", "age_effort_p"]].copy()
    m3_focus["age_effort_p"] = m3_focus["age_effort_p"].map(format_p)
    status = expanded.groupby(["approach_id", "status"], dropna=False).size().reset_index(name="fits")
    output_tables = {
        "m1_m2_sign_flip_table": sign,
        "m3_interaction_focus": m3_focus,
        "selected_age_effects": age_effects,
        "model_status_counts": status,
    }
    for name, table in output_tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)

    md = f"""# Extended Internal Review: Utterance Information Models M1-M3

This report is a more explicit companion to the M1/M2/M3 deep dive. It does not
introduce new fitted models; it makes the current results easier to explain.

## Literature Anchors

- Communicative-efficiency work on children motivates testing whether children
  shorten or lengthen messages when context makes a shorter message sufficient.
- Work on child-directed and learner-directed speech motivates comparing
  children and caretakers, and treating redundancy as potentially adaptive.
- The Wang et al. word-formation paper motivates interaction models: different
  information sources can jointly constrain efficient form choice, so
  age-by-effort and age-by-context interactions are not decorative terms.

## What The Three Models Ask

| model | formula template | question |
| --- | --- | --- |
| M1 | `sum_bits ~ age + effort` | In the pooled child data, does age predict total bits after utterance size is controlled? |
| M2 | `sum_bits ~ age + effort + child identity` | Within a child-adjusted developmental frame, does age predict total bits after utterance size is controlled? |
| M3 | `sum_bits ~ age * effort` | Does the amount of information associated with each unit of effort itself change with age? |

All effort measures are kept separate. This is a scientific constraint, not a
coding convenience: the effort measures are strongly collinear.

## Why The Fixed-Median Prediction Lines Exist

Regression lines over age need one concrete utterance size. When a plot says
"effort fixed at median X", the fitted model has **not** been changed. The
line asks what the fitted model predicts as age varies for a typical utterance
with that effort value. This is the visual version of "controlling for
utterance size."

## Effort Collinearity

{write_markdown_table(vif, max_rows=20)}

![Predictor correlations](../figs/m1_m2_utterance_information_deep_dive/predictor_correlation_heatmap.png)

## M1 Versus M2: The Important Sign Flip

{write_markdown_table(sign, max_rows=20)}

Interpretation: M1 is a pooled model and can mix within-child development with
which children contribute data at which ages. M2 adds child identity and is
therefore closer to the developmental question. In the current results, the
child-adjusted models show a downward developmental age effect across all
effort versions, whereas the pooled model does not.

![M1/M2 adjusted trajectories](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)

## M3 Interaction Focus

{write_markdown_table(m3_focus, max_rows=40)}

The interaction coefficient is `age_effort_coef`. For additive-bit models,
positive values mean the effort-to-information slope increases with age;
negative values mean it decreases with age. For Gamma/log-link models, read
the prediction plots first because coefficients are on the log expected-bits
scale.

![M3 interaction coefficients](../figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png)

![M3 OLS interaction lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png)

![M3 child fixed-effect interaction lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)

## Fit Status And Caveats

{write_markdown_table(status, max_rows=20)}

Mixed-model singularity warnings are not hidden. They mean that a random-effect
variance was estimated at or near the boundary, so these fits are sensitivity
diagnostics rather than the primary evidence. The stable primary ladder remains:
pooled OLS, child-clustered OLS, child fixed effects, and GEE.

## Age-Bin Coverage

{write_markdown_table(age_bins, max_rows=20)}

## Output Tables

- `{output_dir / "m1_m2_sign_flip_table.csv"}`
- `{output_dir / "m3_interaction_focus.csv"}`
- `{output_dir / "selected_age_effects.csv"}`
"""
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)


def write_model_zoo_report(
    *,
    data: ZooData,
    summary: pd.DataFrame,
    coefs: pd.DataFrame,
    comparison_summary: pd.DataFrame,
    comparison_coefs: pd.DataFrame,
    tables: Mapping[str, pd.DataFrame],
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
) -> None:
    """Write the exploratory research-question model zoo report."""

    model_table = summary.copy()
    if not model_table.empty and "r2_or_observed_fitted_r2" in model_table.columns:
        model_table = model_table.sort_values("model")
    wanted_terms = [
        "age_months_z",
        "context_entropy_bits_z",
        "age_months_z:context_entropy_bits_z",
        "context_next_top1_prob_z",
        "age_months_z:context_next_top1_prob_z",
        "nb_words_z",
        "log_nb_words",
    ]
    if coefs.empty or "term" not in coefs.columns:
        key_coef = pd.DataFrame()
    else:
        term_text = coefs["term"].astype(str)
        key_coef = coefs[
            term_text.isin(wanted_terms)
            | term_text.str.contains(
                r"C\(target_variant\)|C\(baseline_variant\)|C\(speaker_group\)|age_months_z:C",
                regex=True,
                na=False,
            )
        ].copy()
    if not key_coef.empty:
        key_coef["p_value"] = key_coef["p_value"].map(format_p)
    entropy_gap = data.entropy_status[
        data.entropy_status["context_entropy_join_status"].astype(str).str.contains("missing", na=False)
    ]
    response_entropy_exists = Path("results/response_level_context_entropy/context_response_entropy_features.csv").exists()
    variant_manifest = read_csv_if_exists(output_dir / "zoo_model_variant_manifest.csv")
    workflow_table = pd.DataFrame(
        [
            {
                "stage": "extract",
                "what it does": "Reads the large long table once and writes bounded samples plus full aggregate summaries.",
                "rerun when": "The scored utterance table, row filters, or sampling logic changes.",
            },
            {
                "stage": "model",
                "what it does": "Fits zoo models and regenerates plots from saved bounded samples.",
                "rerun when": "A formula, model family, plot, or comparison specification changes.",
            },
            {
                "stage": "report",
                "what it does": "Builds Markdown/HTML from existing CSV and figure outputs only.",
                "rerun when": "Only wording, section order, or display formatting changes.",
            },
        ]
    )
    column_dictionary = pd.DataFrame(
        [
            {"column": "model", "meaning": "Unique fitted model/subvariant name."},
            {"column": "formula", "meaning": "Statsmodels formula used to fit that subvariant."},
            {"column": "family", "meaning": "Estimator class, e.g. OLS with child-clustered SE or GEE with a specified response family."},
            {"column": "status", "meaning": "`fit` if the model converged; otherwise the recorded failure or empty-data reason."},
            {"column": "n_obs", "meaning": "Number of modeled rows used by that subvariant."},
            {"column": "n_children", "meaning": "Number of distinct child IDs contributing rows, when defined."},
            {"column": "r2_or_observed_fitted_r2", "meaning": "OLS R2 when available; otherwise squared correlation between observed and fitted values."},
            {"column": "estimate", "meaning": "Coefficient estimate on the model's scale. Log-link models are on the log expected-outcome scale."},
            {"column": "std_error", "meaning": "Standard error; clustered or GEE robust where that estimator is used."},
            {"column": "p_value", "meaning": "Wald-style p-value supplied by the fitted statsmodels object."},
        ]
    )
    summary_cols = ["model", "family", "status", "n_obs", "n_children", "r2_or_observed_fitted_r2", "question"]
    coef_cols = ["model", "term", "estimate", "std_error", "p_value"]

    def table_columns(frame: pd.DataFrame, columns: Sequence[str], *, max_rows: int = 30) -> str:
        if frame.empty:
            return "_No rows._"
        return write_markdown_table(frame[[col for col in columns if col in frame.columns]], max_rows=max_rows)

    def rows_matching(frame: pd.DataFrame, text: str) -> pd.DataFrame:
        if frame.empty or "model" not in frame.columns:
            return pd.DataFrame()
        return frame[frame["model"].astype(str).str.contains(text, case=False, regex=False, na=False)].copy()

    def rows_for_card(frame: pd.DataFrame, card: Mapping[str, str]) -> pd.DataFrame:
        if frame.empty or "model" not in frame.columns:
            return pd.DataFrame()
        return frame[frame["model"].astype(str).str.startswith(str(card["model"]), na=False)].copy()

    def cleaned_coef_rows(frame: pd.DataFrame, text: str) -> pd.DataFrame:
        sub = rows_matching(frame, text)
        if sub.empty or "term" not in sub.columns:
            return sub
        sub = sub[~sub["term"].astype(str).eq("Intercept")].copy()
        if "p_value" in sub.columns:
            sub["p_value"] = sub["p_value"].map(format_p)
        return sub

    def cleaned_coef_rows_for_model(frame: pd.DataFrame, model_name: object) -> pd.DataFrame:
        if frame.empty or "model" not in frame.columns or "term" not in frame.columns:
            return pd.DataFrame()
        sub = frame[frame["model"].astype(str).eq(str(model_name))].copy()
        sub = sub[sub["term"].map(is_reportable_zoo_term)].copy()
        if "p_value" in sub.columns:
            sub["p_value"] = sub["p_value"].map(format_p)
        return sub

    baseline_intro = pd.DataFrame(
        [
            {
                "comparison": "child vs random",
                "scientific question": "Do children differ from utterances sampled uniformly from the age-bin vocabulary?",
                "matched design": "same child row, same context window, same word count",
            },
            {
                "comparison": "child vs unigram",
                "scientific question": "Do children differ from a frequency-only language baseline?",
                "matched design": "same child row, same context window, same word count",
            },
            {
                "comparison": "child vs bigram",
                "scientific question": "Do children differ from a local one-step sequence baseline seeded by the caretaker context?",
                "matched design": "same child row, same context window, same word count",
            },
            {
                "comparison": "child vs trigram",
                "scientific question": "Do children differ from a local two-step sequence baseline seeded by the caretaker context?",
                "matched design": "same child row, same context window, same word count",
            },
            {
                "comparison": "child vs caretaker",
                "scientific question": "Are children moving toward caretaker-like information density and effort?",
                "matched design": "not row-matched; comparisons control word count and cluster by child where possible",
            },
        ]
    )

    comparison_rows = table_columns(comparison_summary, summary_cols, max_rows=80)
    comparison_coef_rows = cleaned_coef_rows(comparison_coefs, "")
    comparison_coef_table = table_columns(comparison_coef_rows, coef_cols, max_rows=140)

    baseline_sections: list[str] = []
    for variant in ["random", "unigram", "bigram", "trigram"]:
        label = variant.capitalize()
        baseline_sections.append(
            f"""## Child Versus {label}

**Question.** Does the real child utterance differ from the {variant} baseline,
and does that gap change over development?

**Design.** This is the cleanest comparison in the current report: each
generated baseline utterance is matched to the same child utterance, same
preceding caretaker context, and same word count. The dashboard therefore shows
both raw trajectories and real-minus-baseline deltas. The fitted models below
then repeat the comparison with each effort measure controlled separately, so
the inference is not word-only.

**How to read this plot.** The top row compares real child and {variant}
trajectories. The bottom row plots real-minus-baseline differences, so zero
means no gap and a changing line means the gap changes with age.

![Child versus {variant} dashboard](../figs/utterance_information_research_model_zoo/child_vs_{variant}_dashboard.png)

Model rows:

{table_columns(rows_matching(comparison_summary, variant), summary_cols, max_rows=12)}

Key coefficients:

{table_columns(cleaned_coef_rows(comparison_coefs, variant), coef_cols, max_rows=28)}
"""
        )

    context_models = model_table[
        model_table.get("model", pd.Series(dtype=str)).astype(str).str.startswith(("Z3", "Z4", "Z5", "Z6", "Z10"), na=False)
    ].copy()
    context_coefs = key_coef[
        key_coef.get("model", pd.Series(dtype=str)).astype(str).str.startswith(("Z3", "Z4", "Z5", "Z6", "Z10"), na=False)
    ].copy()
    model_zoo_only = model_table[
        model_table.get("model", pd.Series(dtype=str)).astype(str).str.startswith("Z", na=False)
    ].copy()
    delta_means = baseline_delta_summary(data)
    if not delta_means.empty:
        delta_means = delta_means.rename(columns={"mean": "mean_delta", "sem": "sem_delta"})

    def card_takeaway(card: Mapping[str, str]) -> str:
        model_rows = rows_for_card(summary, card)
        coef_rows = cleaned_coef_rows(coefs, card["model"])
        if model_rows.empty:
            return "This model did not produce a summary row in the current build."
        fit_count = int(model_rows["status"].astype(str).eq("fit").sum()) if "status" in model_rows.columns else 0
        if fit_count == 0:
            status_counts = model_rows.get("status", pd.Series(dtype=str)).astype(str).value_counts().to_dict()
            return f"No subvariant fit cleanly in the current build. Status counts: `{status_counts}`."
        term = card.get("takeaway_term", "")
        if coef_rows.empty or not term:
            return f"{fit_count}/{len(model_rows)} subvariants fit cleanly. See the subvariant tables for formulas and coefficients."
        term_match = coef_rows[coef_rows["term"].astype(str).eq(term)].copy()
        if term_match.empty:
            return f"{fit_count}/{len(model_rows)} subvariants fit cleanly. The focal coefficient `{term}` is not present for every subvariant."
        estimates = pd.to_numeric(term_match["estimate"], errors="coerce").dropna()
        if estimates.empty:
            return f"{fit_count}/{len(model_rows)} subvariants fit cleanly; focal coefficient estimates are unavailable."
        n_pos = int((estimates > 0).sum())
        n_neg = int((estimates < 0).sum())
        return f"{fit_count}/{len(model_rows)} subvariants fit cleanly. For `{term}`, {n_pos} estimates are positive and {n_neg} are negative across fitted subvariants."

    def model_card_section(card: Mapping[str, str]) -> str:
        model_rows = rows_for_card(summary, card)
        coef_rows = cleaned_coef_rows(coefs, card["model"])
        if not coef_rows.empty:
            coef_rows = coef_rows[
                ~coef_rows["term"].astype(str).str.startswith("C(child_id)", na=False)
                & coef_rows["term"].map(is_reportable_zoo_term)
            ].copy()
        manifest_rows = (
            variant_manifest[variant_manifest["family_id"].astype(str).eq(str(card["short"]))]
            if not variant_manifest.empty and "family_id" in variant_manifest.columns
            else pd.DataFrame()
        )
        subvariant_sections: list[str] = []
        for idx, row in model_rows.reset_index(drop=True).iterrows():
            model_name = row.get("model", "")
            sub_coefs = cleaned_coef_rows_for_model(coefs, model_name).head(12)
            single = pd.DataFrame([row])
            subvariant_sections.append(
                f"""### {card["short"]}.{idx + 1}: {model_subvariant_label(model_name)}

**Question asked by this subvariant.** {row.get("question", "")}

**Formula.** `{row.get("formula", "")}`

**Estimator.** `{row.get("family", "")}`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

{table_columns(single, summary_cols, max_rows=1)}

Key coefficients:

{table_columns(sub_coefs, coef_cols, max_rows=12)}
"""
            )
        family_coef_path = fig_dir / f"{str(card['short']).lower()}_family_coefficients.png"
        family_coef_md = (
            f"""
**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![{card["short"]} coefficients](../figs/utterance_information_research_model_zoo/{family_coef_path.name})
"""
            if family_coef_path.exists()
            else ""
        )
        return f"""## {card["short"]}: {card["title"]}

**Question family.** {card.get("question_family", "Not specified.")}

**Why it is in the expanded atlas.** {card["outside_m1_m4"]}

**How to read this plot.** {card["plot_reading"]}

![{card["short"]} plot](../figs/utterance_information_research_model_zoo/{card["plot"]})

**Compact result.** {card_takeaway(card)}

Subvariants in this family:

{table_columns(manifest_rows, ["family_id", "subvariant", "estimator", "status", "n_obs", "n_children", "r2_or_observed_fitted_r2"], max_rows=20)}

Family key coefficients:

{table_columns(coef_rows.head(25), coef_cols, max_rows=25)}

{family_coef_md}

{"".join(subvariant_sections)}
"""

    model_card_sections = "\n".join(model_card_section(card) for card in ZOO_CARD_DEFS)

    md = f"""# Expanded Internal Model Atlas

This is an internal modeling report, not the supervisor-facing document. Its job
is to make the central communicative-efficiency comparisons explicit before we
decide which results deserve promotion.

## Workflow Separation

The analysis and report generation are deliberately decoupled.

{write_markdown_table(workflow_table, max_rows=10)}

Current commands:

- Re-extract samples and refit everything: `uv run python src/build_route1_model_report_suite.py --stage analysis`
- Refit models and plots from saved samples only: `uv run python src/build_route1_model_report_suite.py --stage model`
- Rebuild Markdown/HTML only: `uv run python src/build_route1_model_report_suite.py --stage report`

## How To Read Model Tables

{write_markdown_table(column_dictionary, max_rows=20)}

## Scientific Map

{write_markdown_table(baseline_intro, max_rows=10)}

## Data Used

The descriptive trajectory plots use full age-bin aggregates from the available
k3 scored rows. The more flexible exploratory models use bounded samples where
needed so the report can be regenerated quickly. Real-minus-baseline delta
models use row-matched child rows, so their interpretation is tighter than the
child-versus-caretaker comparison.

Extraction counts:

{write_markdown_table(data.extraction_summary.head(30), max_rows=30)}

Context entropy status:

{write_markdown_table(data.entropy_status.head(40), max_rows=40)}

Response-level entropy features present: `{response_entropy_exists}`.

If response-level entropy is absent, this report uses next-token context entropy
as a provisional context-predictability measure. This is not the same thing as
sampling full possible responses from the model, so final context-efficiency
claims should wait for the response-level entropy audit.

## Derived Predictors

{write_markdown_table(pd.read_csv(output_dir / "derived_predictor_dictionary.csv"), max_rows=20)}

**How to read this plot.** Each cell is a Pearson correlation between two
predictors. Darker positive cells mean two predictors rise together; darker
negative cells mean one tends to fall when the other rises. This is a warning
system for model design, not a result about development.

![Predictor correlations](../figs/utterance_information_research_model_zoo/exploratory_predictor_correlation.png)

## Model Family Manifest

This table is the audit trail for the zoo. A **family** is a scientific question
such as child-versus-baseline or context entropy predicting effort. A
**subvariant** is a true model change, usually replacing the effort definition
or the information-density unit. Alternate plots of the same fitted model are
diagnostic views, not subvariants.

{write_markdown_table(variant_manifest, max_rows=80)}

## Omnibus Baseline Trajectories

These plots answer the first sanity question: how far are real child utterances
from increasingly structured baselines over developmental time?

**How to read this plot.** Each line is an age-bin mean for one target type.
This plot uses total utterance bits, so it is descriptive and still reflects
utterance-size differences.

![All baseline total bits](../figs/utterance_information_research_model_zoo/baseline_all_total_bits.png)

**How to read this plot.** This is the same baseline comparison after dividing
total bits by word count. It is a direct information-density view, but it only
controls word count, not phonemes, syllables, or morphemes.

![All baseline bits per word](../figs/utterance_information_research_model_zoo/baseline_all_bits_per_word.png)

Because the generated baselines are word-count matched but not necessarily
phoneme-, syllable-, or morpheme-matched, effort profiles are checked directly.

**How to read this plot.** Each panel checks whether real and generated
utterances differ in non-word effort units. The baselines are word-count
matched, but they can still differ in morphemes, syllables, and phonemes.

![Baseline effort profiles](../figs/utterance_information_research_model_zoo/baseline_effort_profiles_nonword_units.png)

Real-minus-baseline deltas:

{write_markdown_table(delta_means.head(40), max_rows=40)}

## Explicit Comparison Models

{comparison_rows}

**How to read this plot.** Each row is one child-vs-baseline or
child-vs-caretaker model, and each column is the effort measure controlled in
that version. This is a model-fit overview, not the substantive effect itself:
it shows whether the comparison model explains more or less variance depending
on how effort is controlled.

![Effort-controlled comparison model fit](../figs/utterance_information_research_model_zoo/effort_controlled_comparison_model_r2.png)

**How to read this plot.** Each point is an age-related coefficient from an
effort-controlled comparison model. Values to the right of zero mean the
age-related gap increases; values to the left mean it decreases. The same
comparison is repeated under words, morphemes, syllables, and phonemes as
separate effort controls.

![Effort-controlled comparison age coefficients](../figs/utterance_information_research_model_zoo/effort_controlled_comparison_age_coefficients.png)

Key comparison coefficients:

{comparison_coef_table}

{"".join(baseline_sections)}

## Children Versus Caretakers

**Question.** Are children becoming more caretaker-like in information density,
or are child and caretaker trajectories governed by different constraints?

**Design.** This comparison is not row-matched. The fitted comparison models
repeat the child/caretaker contrast with each effort measure controlled
separately and cluster by child where the model family allows it, but this
should still be interpreted as a speaker-group developmental contrast rather
than a matched baseline test.

**How to read this plot.** The panels compare child and caretaker trajectories
over the child's age. Because this is not row-matched, the plot is useful for a
broad developmental contrast, not for claiming that a specific child response
is more or less efficient than its caretaker context.

![Child caretaker dashboard](../figs/utterance_information_research_model_zoo/child_vs_caretaker_dashboard.png)

Model rows:

{table_columns(rows_matching(comparison_summary, "caretaker"), summary_cols, max_rows=10)}

Key coefficients:

{table_columns(cleaned_coef_rows(comparison_coefs, "caretaker"), coef_cols, max_rows=25)}

## Context Predictability And Effort

**Question.** Given the preceding caretaker context, do children modulate their
production effort or information density? This is the analysis family closest
to the proposal that contextual predictability should help predict child
utterance length.

**How to read this plot.** The x-axis is next-token entropy of the preceding
caretaker context. A rising line would mean children use more words when the
model sees the context as less predictive.

![Context entropy and child words](../figs/utterance_information_research_model_zoo/context_entropy_child_words.png)

**How to read this plot.** This asks whether information density, not just
utterance length, varies with context entropy. A rising line means higher bits
per word in less predictable contexts.

![Context entropy and bits per word](../figs/utterance_information_research_model_zoo/context_entropy_bits_per_word.png)

**How to read this plot.** Lines compare child word count after different broad
caretaker context types. This is a conversational-control check: wh-questions,
yes/no questions, other questions, and non-questions can invite different
response lengths.

![Question type effort](../figs/utterance_information_research_model_zoo/question_type_child_words_by_age.png)

Context-model rows:

{table_columns(context_models, summary_cols, max_rows=20)}

Context-model key coefficients:

{table_columns(context_coefs, coef_cols, max_rows=60)}

Question-type counts:

{write_markdown_table(tables["context_question_counts"].head(40), max_rows=40)}

## Expanded Model Cards

These are broader models that test nonlinear age, context-window sensitivity,
phonological efficiency, baseline differences, child/caretaker contrasts, and
context-predictability logic. They are for triage, not final reporting.

{model_card_sections}

## Compact Model Zoo Summary

{table_columns(model_zoo_only, summary_cols, max_rows=35)}

Selected coefficients:

{table_columns(key_coef, coef_cols, max_rows=100)}

**How to read this plot.** Each point is a selected coefficient from one of the
expanded atlas models. Positive values mean the coefficient increases the
outcome; negative values mean it decreases the outcome. Coefficients from
different model families are not always on exactly the same interpretive scale,
so use this as a map of candidates rather than as the final comparison.

![Key coefficients](../figs/utterance_information_research_model_zoo/model_zoo_key_coefficients.png)

## What This Report Suggests Checking Next

- Response-level context entropy from sampled full responses should replace or
  complement next-token entropy once available.
- Final models should keep effort measures separate instead of combining highly
  collinear word, morpheme, syllable, and phoneme counts.
- The strongest baseline claims should come from row-matched real-minus-baseline
  deltas, especially child versus trigram.
- Child-versus-caretaker analyses are useful but should not be described as
  matched controls.
- Mixed-effect or GEE specifications should be retained as sensitivity checks
  because child trajectories are not exchangeable independent rows.

## Output Files

- `{output_dir / "model_zoo_summary.csv"}`
- `{output_dir / "model_zoo_coefficients.csv"}`
- `{output_dir / "comparison_model_summary.csv"}`
- `{output_dir / "comparison_model_coefficients.csv"}`
- `{output_dir / "baseline_delta_table.csv.gz"}`
- `{output_dir / "baseline_trends.csv.gz"}`
- `{output_dir / "role_trends.csv.gz"}`
- `{output_dir / "derived_predictor_dictionary.csv"}`
"""
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    """Read a CSV/CSV.GZ if present; return an empty frame otherwise."""

    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def restore_loaded_zoo_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Restore numeric, categorical, and standardized columns in saved samples."""

    if frame.empty:
        return frame
    out = frame.copy()
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "age_bin" in out.columns:
        out["age_bin"] = pd.Categorical(out["age_bin"].astype(str), AGE_BIN_ORDER, ordered=True)
    if "age_stage" not in out.columns and "age_months" in out.columns:
        out["age_stage"] = out["age_months"].map(age_stage)
    if "context_word_count" not in out.columns and "context_text" in out.columns:
        out["context_word_count"] = out["context_text"].map(word_count)
    if "context_question_type" not in out.columns and "context_text" in out.columns:
        out["context_question_type"] = out["context_text"].map(question_type)
    if "log_context_words_plus1" not in out.columns and "context_word_count" in out.columns:
        out["log_context_words_plus1"] = np.log1p(out["context_word_count"])
    log_pairs = [
        ("nb_words", "log_nb_words"),
        ("nb_morphemes", "log_nb_morphemes"),
        ("nb_syllables_cmu_or_pkg", "log_nb_syllables"),
        ("nb_phonemes", "log_nb_phonemes"),
    ]
    for source, target in log_pairs:
        if target not in out.columns and source in out.columns:
            out[target] = np.log(pd.to_numeric(out[source], errors="coerce").replace(0, np.nan))
    z_cols = [
        "age_months",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_syllables_pkg",
        "nb_phonemes",
        "context_word_count",
        "context_entropy_bits",
        "context_next_top1_prob",
        "context_next_top5_mass",
        "context_next_argmax_bits",
    ]
    return add_standardized_columns(out, z_cols)


def load_zoo_data_from_outputs(output_dir: Path) -> ZooData:
    """Reconstruct the report data object from saved analysis outputs."""

    real_k3 = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "real_child_k3_sample.csv.gz"))
    context_real = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "child_context_entropy_sample.csv.gz"))
    baseline_k3 = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "child_baseline_k3_sample.csv.gz"))
    caretaker_k3 = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "caretaker_k3_sample.csv.gz"))
    baseline_deltas = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "baseline_delta_table.csv.gz"))
    baseline_trends = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "baseline_trends.csv.gz"))
    role_trends = restore_loaded_zoo_frame(read_csv_if_exists(output_dir / "role_trends.csv.gz"))
    role_k3 = (
        pd.concat(
            [
                real_k3.assign(speaker_group="child"),
                caretaker_k3.assign(speaker_group="caretaker"),
            ],
            ignore_index=True,
        )
        if not real_k3.empty and not caretaker_k3.empty
        else pd.DataFrame()
    )
    return ZooData(
        real_k3=real_k3,
        context_real=context_real,
        baseline_k3=baseline_k3,
        caretaker_k3=caretaker_k3,
        role_k3=role_k3,
        baseline_deltas=baseline_deltas,
        baseline_trends=baseline_trends,
        role_trends=role_trends,
        extraction_summary=read_csv_if_exists(output_dir / "extraction_counts.csv"),
        entropy_status=read_csv_if_exists(output_dir / "entropy_status_counts.csv"),
    )


def load_basic_zoo_tables(output_dir: Path) -> dict[str, pd.DataFrame]:
    """Load small report tables written by the analysis stage."""

    return {
        "context_question_counts": read_csv_if_exists(output_dir / "context_question_counts.csv"),
        "role_counts": read_csv_if_exists(output_dir / "role_counts.csv"),
        "baseline_delta_long": read_csv_if_exists(output_dir / "baseline_delta_long.csv"),
    }


def run_suite_modeling_from_outputs(
    *,
    output_dir: Path = ZOO_OUTPUT_DIR,
    fig_dir: Path = ZOO_FIG_DIR,
) -> Mapping[str, Path]:
    """Fit models and plots from saved bounded samples without reading raw input."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    data = load_zoo_data_from_outputs(output_dir)
    save_basic_zoo_tables(data, output_dir)
    summary, coefs, _models = fit_model_zoo(data, output_dir)
    comparison_summary, comparison_coefs = fit_comparison_models(data, output_dir)
    combined_summary = pd.concat([summary, comparison_summary], ignore_index=True)
    combined_coefs = pd.concat([coefs, comparison_coefs], ignore_index=True)
    plot_exploratory_figures(data, combined_summary, combined_coefs, output_dir, fig_dir)
    return {"zoo_output_dir": output_dir, "zoo_fig_dir": fig_dir}


def run_suite_analysis(
    *,
    input_csv: Path = ROUTE1_INPUT,
    output_dir: Path = ZOO_OUTPUT_DIR,
    fig_dir: Path = ZOO_FIG_DIR,
    chunksize: int = 350_000,
    max_rows: int | None = None,
) -> Mapping[str, Path]:
    """Run expensive model-zoo analysis and write tables/figures."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    data = read_zoo_data(input_csv, output_dir, chunksize=chunksize, max_rows=max_rows)
    if not data.baseline_deltas.empty:
        data.baseline_deltas.to_csv(output_dir / "baseline_delta_table.csv.gz", index=False)
    save_basic_zoo_tables(data, output_dir)
    summary, coefs, _models = fit_model_zoo(data, output_dir)
    comparison_summary, comparison_coefs = fit_comparison_models(data, output_dir)
    combined_summary = pd.concat([summary, comparison_summary], ignore_index=True)
    combined_coefs = pd.concat([coefs, comparison_coefs], ignore_index=True)
    plot_exploratory_figures(data, combined_summary, combined_coefs, output_dir, fig_dir)
    return {"zoo_output_dir": output_dir, "zoo_fig_dir": fig_dir}


def render_suite_reports_from_outputs(
    *,
    output_dir: Path = ZOO_OUTPUT_DIR,
    fig_dir: Path = ZOO_FIG_DIR,
    detail_output_dir: Path = DETAIL_OUTPUT_DIR,
    detail_md_path: Path = DETAIL_DOC_MD,
    detail_html_path: Path = DETAIL_DOC_HTML,
    zoo_md_path: Path = ZOO_DOC_MD,
    zoo_html_path: Path = ZOO_DOC_HTML,
) -> Mapping[str, Path]:
    """Render internal reports from existing analysis outputs only."""

    sns.set_theme(style="whitegrid", context="talk")
    write_extended_m123_report(output_dir=detail_output_dir, md_path=detail_md_path, html_path=detail_html_path)
    data = load_zoo_data_from_outputs(output_dir)
    summary = read_csv_if_exists(output_dir / "model_zoo_summary.csv")
    coefs = read_csv_if_exists(output_dir / "model_zoo_coefficients.csv")
    comparison_summary = read_csv_if_exists(output_dir / "comparison_model_summary.csv")
    comparison_coefs = read_csv_if_exists(output_dir / "comparison_model_coefficients.csv")
    combined_summary = pd.concat([summary, comparison_summary], ignore_index=True)
    combined_coefs = pd.concat([coefs, comparison_coefs], ignore_index=True)
    write_model_zoo_report(
        data=data,
        summary=combined_summary,
        coefs=combined_coefs,
        comparison_summary=comparison_summary,
        comparison_coefs=comparison_coefs,
        tables=load_basic_zoo_tables(output_dir),
        output_dir=output_dir,
        fig_dir=fig_dir,
        md_path=zoo_md_path,
        html_path=zoo_html_path,
    )
    return {
        "extended_html": detail_html_path,
        "zoo_html": zoo_html_path,
        "zoo_output_dir": output_dir,
        "zoo_fig_dir": fig_dir,
    }


def build_suite(
    *,
    input_csv: Path = ROUTE1_INPUT,
    chunksize: int = 350_000,
    max_rows: int | None = None,
) -> Mapping[str, Path]:
    """Run analysis and render both internal reports."""

    run_suite_analysis(input_csv=input_csv, output_dir=ZOO_OUTPUT_DIR, fig_dir=ZOO_FIG_DIR, chunksize=chunksize, max_rows=max_rows)
    return render_suite_reports_from_outputs()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROUTE1_INPUT)
    parser.add_argument("--chunksize", type=int, default=350_000)
    parser.add_argument("--max-rows", type=int, default=None, help="Optional row cap for smoke testing.")
    parser.add_argument(
        "--stage",
        choices=["all", "analysis", "extract", "model", "report"],
        default="all",
        help=(
            "all reruns extraction, models, and report; analysis/extract+model writes tables/figures only; "
            "extract refreshes bounded samples from the raw long table; model refits/replots from saved samples; "
            "report rebuilds Markdown/HTML from existing outputs."
        ),
    )
    args = parser.parse_args(argv)
    if args.stage in {"all", "analysis"}:
        outputs = run_suite_analysis(input_csv=args.input, chunksize=args.chunksize, max_rows=args.max_rows)
        print(f"[OK] wrote/updated model zoo tables: {outputs['zoo_output_dir']}")
        print(f"[OK] wrote/updated model zoo figures: {outputs['zoo_fig_dir']}")
    if args.stage == "extract":
        ZOO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ZOO_FIG_DIR.mkdir(parents=True, exist_ok=True)
        read_zoo_data(args.input, ZOO_OUTPUT_DIR, chunksize=args.chunksize, max_rows=args.max_rows)
        print(f"[OK] wrote/updated bounded model zoo samples: {ZOO_OUTPUT_DIR}")
    if args.stage == "model":
        outputs = run_suite_modeling_from_outputs()
        print(f"[OK] refit model zoo tables from saved samples: {outputs['zoo_output_dir']}")
        print(f"[OK] replotted model zoo figures from saved samples: {outputs['zoo_fig_dir']}")
    if args.stage in {"all", "report"}:
        outputs = render_suite_reports_from_outputs()
        print(f"[OK] wrote extended report: {outputs['extended_html']}")
        print(f"[OK] wrote model zoo report: {outputs['zoo_html']}")


if __name__ == "__main__":
    main()
