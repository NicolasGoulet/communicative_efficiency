#!/usr/bin/env python3
"""Build context-predictor permutation reports for k0/k1/k2/k3.

This script asks a narrow Route 1 question:

Given child real utterances and a fixed scoring context size (`k0`-`k3`), does
context predict total utterance information after the usual controls?

The fitted outcome is always `sum_bits`. The control structure is:

    age + target utterance effort + child identity

The context predictors are varied as:

    baseline: no context predictor
    entropy_only: context entropy only
    size_only: context-window size only
    entropy_plus_size: context entropy and context-window size together

Context-window size is measured separately as words, surface morphemes,
CMU/pkg syllables, pkg syllables, and CMU/G2P phonemes. The script writes one
report per `k` plus one cross-k comparison report. It does not overwrite the
older M1-M6 reports.
"""

from __future__ import annotations

import argparse
import gc
import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import syllables
import statsmodels.formula.api as smf
from sklearn.metrics import mean_absolute_error, mean_squared_error

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_m1_m2_utterance_information_deep_dive import AGE_BIN_ORDER, DEFAULT_INPUT, EFFORT_MEASURES
    from render_markdown_report import render_markdown_file
    from utterance_count_strategies import count_morphemes_suffix_heuristic, count_words_regex, word_tokens_regex
    from validate_utterance_measurement_strategies import (
        first_cmu_pronunciation,
        g2p_pronunciation_for_word,
        phones_syllable_count,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import AGE_BIN_ORDER, DEFAULT_INPUT, EFFORT_MEASURES
    from src.render_markdown_report import render_markdown_file
    from src.utterance_count_strategies import count_morphemes_suffix_heuristic, count_words_regex, word_tokens_regex
    from src.validate_utterance_measurement_strategies import (
        first_cmu_pronunciation,
        g2p_pronunciation_for_word,
        phones_syllable_count,
    )


DEFAULT_OUTPUT_DIR = Path("results/context_predictor_permutations")
DEFAULT_FIG_DIR = Path("figs/context_predictor_permutations")
DEFAULT_DOC_DIR = Path("docs")
DEFAULT_CONTEXT_KS = ("k0", "k1", "k2", "k3")
DEFAULT_CHUNKSIZE = 500_000

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
    "context_entropy_join_status",
    "context_entropy_bits",
    "sum_bits",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
]

NUMERIC_COLS = [
    "age_months",
    "context_entropy_bits",
    "sum_bits",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
]

CONTEXT_SIZE_MEASURES = [
    ("context_nb_words", "Context words"),
    ("context_nb_morphemes", "Context morphemes"),
    ("context_nb_syllables_cmu_or_pkg", "Context syllables: CMU/pkg"),
    ("context_nb_syllables_pkg", "Context syllables: pkg"),
    ("context_nb_phonemes", "Context phonemes"),
]

MODEL_SPECS = [
    {
        "model_id": "C0",
        "model_label": "Baseline controls",
        "context_predictor_family": "baseline",
        "formula": "sum_bits ~ age_c + target_effort_c + C(child_id)",
        "question": "How much do age, target utterance effort, and child identity explain without context predictors?",
    },
    {
        "model_id": "C1",
        "model_label": "Entropy only",
        "context_predictor_family": "entropy_only",
        "formula": "sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)",
        "question": "Does context entropy add predictive information beyond age, target effort, and child identity?",
    },
    {
        "model_id": "C2",
        "model_label": "Context size only",
        "context_predictor_family": "context_size_only",
        "formula": "sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)",
        "question": "Does the size of the preceding caretaker context add predictive information beyond age, target effort, and child identity?",
    },
    {
        "model_id": "C3",
        "model_label": "Entropy plus context size",
        "context_predictor_family": "entropy_plus_context_size",
        "formula": "sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)",
        "question": "Do context entropy and context size explain distinct variance when entered together?",
    },
]

MODEL_ORDER = [spec["context_predictor_family"] for spec in MODEL_SPECS]
MODEL_LABELS = {spec["context_predictor_family"]: spec["model_label"] for spec in MODEL_SPECS}
CONTEXT_SIZE_LABELS = {col: label for col, label in CONTEXT_SIZE_MEASURES}
TARGET_EFFORT_LABELS = {col: label for col, label in EFFORT_MEASURES}


@dataclass(frozen=True)
class FitRecord:
    """Metadata and result for one fitted context-predictor model."""

    context_k: str
    model_id: str
    model_label: str
    context_predictor_family: str
    question: str
    target_effort_col: str
    target_effort_label: str
    context_size_col: str
    context_size_label: str
    formula: str
    status: str
    error: str
    n_obs: int
    n_children: int
    age_sd: float
    target_effort_sd: float
    context_entropy_sd: float
    context_size_sd: float
    sum_bits_sd: float
    r2_observed_fitted: float = math.nan
    rmse: float = math.nan
    mae: float = math.nan
    aic: float = math.nan
    bic: float = math.nan
    age_coef: float = math.nan
    age_p: float = math.nan
    target_effort_coef: float = math.nan
    target_effort_p: float = math.nan
    context_entropy_coef: float = math.nan
    context_entropy_p: float = math.nan
    context_size_coef: float = math.nan
    context_size_p: float = math.nan


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 40, digits: int = 4) -> str:
    """Render a compact Markdown table."""

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
    separator = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def format_p(value: object) -> str:
    """Format a p-value for a report table."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def safe_float(result: object | None, attr: str) -> float:
    """Read a numeric result attribute if available."""

    if result is None or not hasattr(result, attr):
        return math.nan
    try:
        return float(getattr(result, attr))
    except Exception:
        return math.nan


def fitted_r2(observed: np.ndarray, fitted: np.ndarray) -> float:
    """Return observed-versus-fitted R2."""

    sst = float(np.sum((observed - np.mean(observed)) ** 2))
    if sst <= 0:
        return math.nan
    sse = float(np.sum((observed - fitted) ** 2))
    return 1.0 - sse / sst


def param_value(result: object | None, term: str, attr: str = "params") -> float:
    """Read a parameter or p-value from a statsmodels result."""

    if result is None or not hasattr(result, attr):
        return math.nan
    values = getattr(result, attr)
    try:
        return float(values.get(term, math.nan))
    except AttributeError:
        try:
            return float(values[term])
        except Exception:
            return math.nan


def std_beta(coef: float, x_sd: float, y_sd: float) -> float:
    """Return standardized beta for one coefficient."""

    if not all(math.isfinite(value) for value in [coef, x_sd, y_sd]) or y_sd <= 0:
        return math.nan
    return coef * x_sd / y_sd


@lru_cache(maxsize=400_000)
def token_phonological_counts(token: str) -> tuple[int, int, int, int, int]:
    """Return fast syllable/phoneme counts for one token.

    This uses the same hierarchy as the publication measurement validation:
    CMUdict when available, `syllables` package for OOV syllables, and g2p-en
    for OOV phonemes. It avoids the validation probe's JSON audit objects
    because the context permutation models need counts for many repeated tokens.
    """

    cmu = first_cmu_pronunciation(token)
    syll_pkg = max(1, int(syllables.estimate(token.lower())))
    if cmu.pronunciation_count and cmu.syllables_first is not None and cmu.syllables_first > 0:
        syll_cmu_pkg = int(cmu.syllables_first)
        syll_fallback = 0
    else:
        syll_cmu_pkg = syll_pkg
        syll_fallback = 1
    if cmu.pronunciation_count and cmu.phonemes_first is not None and cmu.phonemes_first > 0:
        phonemes = int(cmu.phonemes_first)
        g2p_fallback = 0
    else:
        phones = list(g2p_pronunciation_for_word(token))
        if not phones:
            phones = ["ORTH"]
        phonemes = len(phones)
        g2p_fallback = 1
        if phones_syllable_count(phones) <= 0:
            syll_cmu_pkg = max(1, syll_cmu_pkg)
    return syll_cmu_pkg, syll_pkg, phonemes, syll_fallback, g2p_fallback


@lru_cache(maxsize=400_000)
def context_counts(text: str) -> tuple[int, int, int, int, int, int, int]:
    """Compute context-window size counts once per unique context text."""

    if not text:
        return (0, 0, 0, 0, 0, 0, 0)
    tokens = word_tokens_regex(text)
    if not tokens:
        return (0, 0, 0, 0, 0, 0, 0)
    token_counts = [token_phonological_counts(token) for token in tokens]
    return (
        count_words_regex(text),
        count_morphemes_suffix_heuristic(text),
        sum(count[0] for count in token_counts),
        sum(count[1] for count in token_counts),
        sum(count[2] for count in token_counts),
        sum(count[3] for count in token_counts),
        sum(count[4] for count in token_counts),
    )


def context_count_frame(context_texts: Sequence[str], *, checkpoint_csv: Path | None = None) -> pd.DataFrame:
    """Return one context-count row per unique context text."""

    count_columns = [
        "context_text",
        "context_nb_words",
        "context_nb_morphemes",
        "context_nb_syllables_cmu_or_pkg",
        "context_nb_syllables_pkg",
        "context_nb_phonemes",
        "context_syllable_pkg_fallback_word_count",
        "context_g2p_fallback_word_count",
    ]
    wanted_texts = list(dict.fromkeys(str(text) for text in context_texts))
    rows_by_text: dict[str, dict[str, object]] = {}
    if checkpoint_csv is not None and checkpoint_csv.exists():
        existing = pd.read_csv(
            checkpoint_csv,
            usecols=lambda col: col in set(count_columns),
            dtype={"context_text": str},
            keep_default_na=False,
            low_memory=False,
        )
        existing["context_text"] = existing["context_text"].astype(str)
        existing = existing.drop_duplicates(subset=["context_text"], keep="last")
        rows_by_text = {str(row["context_text"]): row for row in existing.to_dict("records")}

    def write_checkpoint() -> None:
        if checkpoint_csv is None:
            return
        checkpoint_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows_by_text.values(), columns=count_columns).to_csv(checkpoint_csv, index=False)

    for idx, text in enumerate(wanted_texts, start=1):
        if text in rows_by_text:
            continue
        words, morphs, syll_cmu_pkg, syll_pkg, phonemes, syll_fb, g2p_fb = context_counts(text)
        rows_by_text[text] = {
            "context_text": text,
            "context_nb_words": words,
            "context_nb_morphemes": morphs,
            "context_nb_syllables_cmu_or_pkg": syll_cmu_pkg,
            "context_nb_syllables_pkg": syll_pkg,
            "context_nb_phonemes": phonemes,
            "context_syllable_pkg_fallback_word_count": syll_fb,
            "context_g2p_fallback_word_count": g2p_fb,
        }
        if checkpoint_csv is not None and idx % 25_000 == 0:
            write_checkpoint()
            print(f"[progress] measured {idx:,}/{len(wanted_texts):,} unique context texts", flush=True)
    write_checkpoint()
    return pd.DataFrame([rows_by_text[text] for text in wanted_texts], columns=count_columns)


def read_real_child_rows(
    input_csv: Path,
    *,
    context_ks: Sequence[str],
    chunksize: int,
) -> pd.DataFrame:
    """Read real child rows for the requested context windows."""

    wanted_ks = set(context_ks)
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        wanted = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].isin(wanted_ks)
        ].copy()
        if not wanted.empty:
            parts.append(wanted)
    if not parts:
        raise ValueError(f"no real child rows found in {input_csv}")
    out = pd.concat(parts, ignore_index=True)
    for col in NUMERIC_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    needed = ["sum_bits", "age_months", "child_id", *[col for col, _ in EFFORT_MEASURES]]
    out = out.dropna(subset=needed).copy()
    out = out[(out["sum_bits"] > 0) & (out["age_months"] > 0)].copy()
    for col, _ in EFFORT_MEASURES:
        out = out[out[col] > 0].copy()
    out["context_text"] = out["context_text"].fillna("").astype(str)
    out["context_k"] = out["context_k"].astype(str)
    out["child_id"] = out["child_id"].astype(str)
    out["dataset"] = out["dataset"].astype(str)
    out["age_bin"] = pd.Categorical(out["age_bin"].astype(str), AGE_BIN_ORDER, ordered=True)
    return out.reset_index(drop=True)


def attach_context_size_counts(frame: pd.DataFrame, *, checkpoint_csv: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach context-window size counts to every row."""

    unique_contexts = sorted(frame["context_text"].drop_duplicates().astype(str).tolist())
    counts = context_count_frame(unique_contexts, checkpoint_csv=checkpoint_csv)
    merged = frame.copy()
    counts_indexed = counts.set_index("context_text")
    for col, _ in CONTEXT_SIZE_MEASURES:
        lookup = counts_indexed[col].to_dict()
        merged[col] = merged["context_text"].map(lookup)
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)
    for col in ["context_syllable_pkg_fallback_word_count", "context_g2p_fallback_word_count"]:
        lookup = counts_indexed[col].to_dict()
        merged[col] = pd.to_numeric(merged["context_text"].map(lookup), errors="coerce").fillna(0).astype(int)
    return merged, counts


def prepare_model_frame(
    frame: pd.DataFrame,
    *,
    target_effort_col: str,
    context_size_col: str | None,
    require_entropy: bool,
    require_context_size: bool,
) -> pd.DataFrame:
    """Return centered rows for one model fit."""

    out = frame.copy()
    out["target_effort_value"] = pd.to_numeric(out[target_effort_col], errors="coerce")
    required = ["sum_bits", "age_months", "target_effort_value", "child_id"]
    if require_entropy:
        out["context_entropy_bits"] = pd.to_numeric(out["context_entropy_bits"], errors="coerce")
        required.append("context_entropy_bits")
    if require_context_size:
        if context_size_col is None:
            return pd.DataFrame()
        out["context_size_value"] = pd.to_numeric(out[context_size_col], errors="coerce")
        required.append("context_size_value")
    else:
        out["context_size_value"] = 0.0
    out = out.dropna(subset=required).copy()
    out = out[(out["sum_bits"] > 0) & (out["age_months"] > 0) & (out["target_effort_value"] > 0)].copy()
    if require_entropy:
        out = out[out["context_entropy_bits"] > 0].copy()
    if require_context_size:
        out = out[out["context_size_value"] > 0].copy()
    if out.empty:
        return out
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["target_effort_c"] = out["target_effort_value"] - out["target_effort_value"].mean()
    out["context_entropy_c"] = (
        out["context_entropy_bits"] - out["context_entropy_bits"].mean()
        if require_entropy
        else 0.0
    )
    out["context_size_c"] = (
        out["context_size_value"] - out["context_size_value"].mean()
        if require_context_size
        else 0.0
    )
    return out


def can_fit_model(model_frame: pd.DataFrame, *, require_entropy: bool, require_context_size: bool) -> tuple[bool, str]:
    """Return whether a model frame has enough variation to fit."""

    if model_frame.empty:
        return False, "no complete rows"
    if model_frame["child_id"].nunique() < 2:
        return False, "fewer than two children"
    if model_frame["age_c"].std(ddof=0) <= 0:
        return False, "age has no variation"
    if model_frame["target_effort_c"].std(ddof=0) <= 0:
        return False, "target effort has no variation"
    if require_entropy and model_frame["context_entropy_c"].std(ddof=0) <= 0:
        return False, "context entropy has no variation"
    if require_context_size and model_frame["context_size_c"].std(ddof=0) <= 0:
        return False, "context size has no variation"
    return True, ""


def fit_one_model(
    *,
    context_k: str,
    spec: Mapping[str, str],
    target_effort_col: str,
    target_effort_label: str,
    context_size_col: str,
    context_size_label: str,
    model_frame: pd.DataFrame,
) -> FitRecord:
    """Fit one model and wrap the result."""

    family = str(spec["context_predictor_family"])
    require_entropy = family in {"entropy_only", "entropy_plus_context_size"}
    require_context_size = family in {"context_size_only", "entropy_plus_context_size"}
    fit_ok, error = can_fit_model(
        model_frame,
        require_entropy=require_entropy,
        require_context_size=require_context_size,
    )
    metrics: dict[str, float] = {
        "r2_observed_fitted": math.nan,
        "rmse": math.nan,
        "mae": math.nan,
        "aic": math.nan,
        "bic": math.nan,
        "age_coef": math.nan,
        "age_p": math.nan,
        "target_effort_coef": math.nan,
        "target_effort_p": math.nan,
        "context_entropy_coef": math.nan,
        "context_entropy_p": math.nan,
        "context_size_coef": math.nan,
        "context_size_p": math.nan,
    }
    status = "skipped"
    if fit_ok:
        try:
            result = smf.ols(str(spec["formula"]), data=model_frame).fit(
                cov_type="cluster",
                cov_kwds={"groups": model_frame["child_id"]},
            )
            observed = np.asarray(result.model.endog, dtype=float)
            fitted = np.asarray(result.fittedvalues, dtype=float)
            metrics.update(
                {
                    "r2_observed_fitted": fitted_r2(observed, fitted),
                    "rmse": math.sqrt(mean_squared_error(observed, fitted)),
                    "mae": float(mean_absolute_error(observed, fitted)),
                    "aic": safe_float(result, "aic"),
                    "bic": safe_float(result, "bic"),
                    "age_coef": param_value(result, "age_c"),
                    "age_p": param_value(result, "age_c", "pvalues"),
                    "target_effort_coef": param_value(result, "target_effort_c"),
                    "target_effort_p": param_value(result, "target_effort_c", "pvalues"),
                    "context_entropy_coef": param_value(result, "context_entropy_c"),
                    "context_entropy_p": param_value(result, "context_entropy_c", "pvalues"),
                    "context_size_coef": param_value(result, "context_size_c"),
                    "context_size_p": param_value(result, "context_size_c", "pvalues"),
                }
            )
            result.remove_data()
            status = "fit"
            error = ""
        except Exception as exc:  # pragma: no cover - real-data guard
            status = "failed"
            error = f"{type(exc).__name__}: {exc}"
    return FitRecord(
        context_k=context_k,
        model_id=str(spec["model_id"]),
        model_label=str(spec["model_label"]),
        context_predictor_family=family,
        question=str(spec["question"]),
        target_effort_col=target_effort_col,
        target_effort_label=target_effort_label,
        context_size_col=context_size_col,
        context_size_label=context_size_label,
        formula=str(spec["formula"]),
        status=status,
        error=error,
        n_obs=len(model_frame),
        n_children=int(model_frame["child_id"].nunique()) if not model_frame.empty else 0,
        age_sd=float(model_frame["age_months"].std(ddof=0)) if not model_frame.empty else math.nan,
        target_effort_sd=float(model_frame["target_effort_value"].std(ddof=0)) if not model_frame.empty else math.nan,
        context_entropy_sd=float(pd.to_numeric(model_frame["context_entropy_bits"], errors="coerce").std(ddof=0))
        if "context_entropy_bits" in model_frame and not model_frame.empty
        else math.nan,
        context_size_sd=float(pd.to_numeric(model_frame["context_size_value"], errors="coerce").std(ddof=0))
        if "context_size_value" in model_frame and not model_frame.empty
        else math.nan,
        sum_bits_sd=float(model_frame["sum_bits"].std(ddof=0)) if not model_frame.empty else math.nan,
        **metrics,
    )


def fit_context_permutation_models(frame: pd.DataFrame, *, context_k: str) -> list[FitRecord]:
    """Fit context-predictor permutations for one context window."""

    k_frame = frame[frame["context_k"].eq(context_k)].copy()
    records: list[FitRecord] = []
    for target_effort_col, target_effort_label in EFFORT_MEASURES:
        model_frames: dict[tuple[str, str], pd.DataFrame] = {}
        for spec in MODEL_SPECS:
            family = str(spec["context_predictor_family"])
            if family in {"baseline", "entropy_only"}:
                context_size_options = [("", "No context-size predictor")]
            else:
                context_size_options = CONTEXT_SIZE_MEASURES
            for context_size_col, context_size_label in context_size_options:
                require_entropy = family in {"entropy_only", "entropy_plus_context_size"}
                require_context_size = family in {"context_size_only", "entropy_plus_context_size"}
                key = (family, context_size_col)
                if key not in model_frames:
                    model_frames[key] = prepare_model_frame(
                        k_frame,
                        target_effort_col=target_effort_col,
                        context_size_col=context_size_col or None,
                        require_entropy=require_entropy,
                        require_context_size=require_context_size,
                    )
                records.append(
                    fit_one_model(
                        context_k=context_k,
                        spec=spec,
                        target_effort_col=target_effort_col,
                        target_effort_label=target_effort_label,
                        context_size_col=context_size_col,
                        context_size_label=context_size_label,
                        model_frame=model_frames[key],
                    )
                )
    return records


def summary_rows(records: Sequence[FitRecord]) -> pd.DataFrame:
    """Return one compact summary row per fit."""

    rows: list[dict[str, object]] = []
    for record in records:
        rows.append(
            {
                "context_k": record.context_k,
                "model_id": record.model_id,
                "model_label": record.model_label,
                "context_predictor_family": record.context_predictor_family,
                "question": record.question,
                "estimator": "linear OLS",
                "library": "statsmodels.formula.api.ols",
                "covariance": "child-cluster robust SE via cov_type='cluster'",
                "target_effort_col": record.target_effort_col,
                "target_effort_label": record.target_effort_label,
                "context_size_col": record.context_size_col,
                "context_size_label": record.context_size_label,
                "formula": record.formula,
                "status": record.status,
                "error": record.error,
                "n_obs": record.n_obs,
                "n_children": record.n_children,
                "r2_observed_fitted": record.r2_observed_fitted,
                "rmse": record.rmse,
                "mae": record.mae,
                "aic": record.aic,
                "bic": record.bic,
                "age_coef": record.age_coef,
                "age_p": record.age_p,
                "target_effort_coef": record.target_effort_coef,
                "target_effort_p": record.target_effort_p,
                "context_entropy_coef": record.context_entropy_coef,
                "context_entropy_p": record.context_entropy_p,
                "context_size_coef": record.context_size_coef,
                "context_size_p": record.context_size_p,
                "std_age_beta": std_beta(record.age_coef, record.age_sd, record.sum_bits_sd),
                "std_target_effort_beta": std_beta(record.target_effort_coef, record.target_effort_sd, record.sum_bits_sd),
                "std_context_entropy_beta": std_beta(record.context_entropy_coef, record.context_entropy_sd, record.sum_bits_sd),
                "std_context_size_beta": std_beta(record.context_size_coef, record.context_size_sd, record.sum_bits_sd),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    base = out[out["context_predictor_family"].eq("baseline")][
        ["context_k", "target_effort_col", "r2_observed_fitted"]
    ].rename(columns={"r2_observed_fitted": "baseline_r2_same_target_effort"})
    out = out.merge(base, how="left", on=["context_k", "target_effort_col"])
    out["delta_r2_vs_baseline"] = out["r2_observed_fitted"] - out["baseline_r2_same_target_effort"]
    return out


def context_distribution_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize context size and entropy by context window."""

    rows: list[dict[str, object]] = []
    for context_k, k_frame in frame.groupby("context_k", sort=True):
        for col, label in CONTEXT_SIZE_MEASURES:
            values = pd.to_numeric(k_frame[col], errors="coerce").dropna()
            rows.append(
                {
                    "context_k": context_k,
                    "measure_col": col,
                    "measure_label": label,
                    "rows": len(values),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "p75": float(values.quantile(0.75)),
                    "p90": float(values.quantile(0.90)),
                    "max": float(values.max()),
                }
            )
        entropy = pd.to_numeric(k_frame["context_entropy_bits"], errors="coerce").dropna()
        rows.append(
            {
                "context_k": context_k,
                "measure_col": "context_entropy_bits",
                "measure_label": "Context entropy bits",
                "rows": len(entropy),
                "mean": float(entropy.mean()) if not entropy.empty else math.nan,
                "median": float(entropy.median()) if not entropy.empty else math.nan,
                "p75": float(entropy.quantile(0.75)) if not entropy.empty else math.nan,
                "p90": float(entropy.quantile(0.90)) if not entropy.empty else math.nan,
                "max": float(entropy.max()) if not entropy.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def context_by_age_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize context predictors by age bin."""

    rows: list[dict[str, object]] = []
    for (context_k, age_bin), group in frame.groupby(["context_k", "age_bin"], observed=True, sort=True):
        if not str(age_bin) or str(age_bin) == "nan":
            continue
        for col, label in CONTEXT_SIZE_MEASURES:
            values = pd.to_numeric(group[col], errors="coerce")
            rows.append(
                {
                    "context_k": context_k,
                    "age_bin": age_bin,
                    "measure_col": col,
                    "measure_label": label,
                    "mean": float(values.mean()),
                    "se": float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else math.nan,
                    "rows": int(len(values)),
                }
            )
        entropy = pd.to_numeric(group["context_entropy_bits"], errors="coerce").dropna()
        rows.append(
            {
                "context_k": context_k,
                "age_bin": age_bin,
                "measure_col": "context_entropy_bits",
                "measure_label": "Context entropy bits",
                "mean": float(entropy.mean()) if not entropy.empty else math.nan,
                "se": float(entropy.std(ddof=1) / math.sqrt(len(entropy))) if len(entropy) > 1 else math.nan,
                "rows": int(len(entropy)),
            }
        )
    return pd.DataFrame(rows)


def plot_context_distributions(distribution: pd.DataFrame, *, context_k: str, fig_dir: Path) -> Path:
    """Plot context-predictor distribution summaries for one k."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    data = distribution[distribution["context_k"].eq(context_k)].copy()
    data = data[data["measure_col"].ne("context_entropy_bits")].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=data, x="measure_label", y="mean", color="#4c78a8", ax=ax)
    ax.set_title(f"{context_k}: mean context-window size")
    ax.set_xlabel("")
    ax.set_ylabel("Mean count")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    out = fig_dir / f"{context_k}_context_size_distribution.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / f"{context_k}_context_size_distribution.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_context_by_age(by_age: pd.DataFrame, *, context_k: str, fig_dir: Path) -> Path:
    """Plot context size and entropy by age bin for one k."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    data = by_age[by_age["context_k"].eq(context_k)].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    sizes = data[data["measure_col"].ne("context_entropy_bits")].copy()
    sns.lineplot(data=sizes, x="age_bin", y="mean", hue="measure_label", marker="o", ax=axes[0])
    axes[0].set_title(f"{context_k}: context-window size by age bin")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Mean context size")
    axes[0].legend(title="Measure", fontsize=8, title_fontsize=9)
    entropy = data[data["measure_col"].eq("context_entropy_bits")].copy()
    if entropy["mean"].notna().any():
        sns.lineplot(data=entropy, x="age_bin", y="mean", marker="o", color="#d95f02", ax=axes[1])
        axes[1].set_title(f"{context_k}: context entropy by age bin")
        axes[1].set_ylabel("Mean entropy bits")
    else:
        axes[1].text(0.5, 0.5, "No entropy for this context condition", ha="center", va="center")
        axes[1].set_axis_off()
    axes[1].set_xlabel("Age bin")
    axes[1].tick_params(axis="x", rotation=35)
    fig.tight_layout()
    out = fig_dir / f"{context_k}_context_predictors_by_age.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / f"{context_k}_context_predictors_by_age.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_r2_by_family(summary: pd.DataFrame, *, context_k: str, fig_dir: Path) -> Path:
    """Plot mean R2 and delta R2 by context predictor family."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sub = summary[(summary["context_k"].eq(context_k)) & summary["status"].eq("fit")].copy()
    agg = (
        sub.groupby(["context_predictor_family", "model_label"], observed=True)
        .agg(mean_r2=("r2_observed_fitted", "mean"), mean_delta_r2=("delta_r2_vs_baseline", "mean"), rows=("model_id", "size"))
        .reset_index()
    )
    agg["context_predictor_family"] = pd.Categorical(agg["context_predictor_family"], MODEL_ORDER, ordered=True)
    agg = agg.sort_values("context_predictor_family")
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    sns.barplot(data=agg, x="model_label", y="mean_r2", ax=axes[0], color="#4c78a8")
    axes[0].set_title(f"{context_k}: in-sample R2")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Mean R2")
    axes[0].tick_params(axis="x", rotation=25)
    sns.barplot(data=agg, x="model_label", y="mean_delta_r2", ax=axes[1], color="#59a14f")
    axes[1].set_title(f"{context_k}: delta R2 vs baseline")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Mean delta R2")
    axes[1].tick_params(axis="x", rotation=25)
    fig.tight_layout()
    out = fig_dir / f"{context_k}_model_family_r2.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / f"{context_k}_model_family_r2.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_entropy_coefficients(summary: pd.DataFrame, *, context_k: str, fig_dir: Path) -> Path:
    """Plot entropy coefficients for entropy-containing models."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sub = summary[
        summary["context_k"].eq(context_k)
        & summary["status"].eq("fit")
        & summary["context_predictor_family"].isin(["entropy_only", "entropy_plus_context_size"])
    ].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(13, 6))
    if sub.empty:
        ax.text(0.5, 0.5, "No entropy models fit for this context condition", ha="center", va="center")
        ax.set_axis_off()
    else:
        hue_levels = sub["context_predictor_family"].nunique()
        sns.pointplot(
            data=sub,
            x="target_effort_label",
            y="context_entropy_coef",
            hue="context_predictor_family",
            dodge=0.35 if hue_levels > 1 else False,
            errorbar=("ci", 95),
            ax=ax,
        )
        ax.axhline(0, color="#333333", linewidth=1)
        ax.set_title(f"{context_k}: context-entropy coefficients")
        ax.set_xlabel("Target effort control")
        ax.set_ylabel("Bits per 1-bit entropy increase")
        ax.tick_params(axis="x", rotation=25)
        ax.legend(title="Model family", fontsize=8, title_fontsize=9)
    fig.tight_layout()
    out = fig_dir / f"{context_k}_entropy_coefficients.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / f"{context_k}_entropy_coefficients.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_context_size_heatmaps(summary: pd.DataFrame, *, context_k: str, fig_dir: Path) -> Path:
    """Plot context-size coefficients as target-effort x context-size heatmaps."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sub = summary[
        summary["context_k"].eq(context_k)
        & summary["status"].eq("fit")
        & summary["context_predictor_family"].isin(["context_size_only", "entropy_plus_context_size"])
    ].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    for ax, family in zip(axes, ["context_size_only", "entropy_plus_context_size"]):
        panel = sub[sub["context_predictor_family"].eq(family)].copy()
        if panel.empty:
            ax.text(0.5, 0.5, "No fitted models", ha="center", va="center")
            ax.set_axis_off()
            continue
        pivot = panel.pivot_table(
            index="context_size_label",
            columns="target_effort_label",
            values="context_size_coef",
            aggfunc="mean",
        )
        sns.heatmap(pivot, center=0, cmap="vlag", annot=True, fmt=".3g", ax=ax)
        ax.set_title(MODEL_LABELS[family])
        ax.set_xlabel("Target effort control")
        ax.set_ylabel("Context size measure")
    fig.suptitle(f"{context_k}: context-size coefficients", y=1.02)
    fig.tight_layout()
    out = fig_dir / f"{context_k}_context_size_coefficients.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / f"{context_k}_context_size_coefficients.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_age_coefficients(summary: pd.DataFrame, *, context_k: str, fig_dir: Path) -> Path:
    """Plot age coefficients across context predictor families."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sub = summary[summary["context_k"].eq(context_k) & summary["status"].eq("fit")].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.pointplot(
        data=sub,
        x="context_predictor_family",
        y="age_coef",
        hue="target_effort_label",
        dodge=0.45,
        errorbar=("ci", 95),
        order=MODEL_ORDER,
        ax=ax,
    )
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_title(f"{context_k}: age coefficients across context-control choices")
    ax.set_xlabel("Context predictor family")
    ax.set_ylabel("Age coefficient: bits per month")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="Target effort", fontsize=8, title_fontsize=9)
    fig.tight_layout()
    out = fig_dir / f"{context_k}_age_coefficients.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / f"{context_k}_age_coefficients.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_cross_k_r2(summary: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot mean R2 and delta R2 across k."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sub = summary[summary["status"].eq("fit")].copy()
    agg = (
        sub.groupby(["context_k", "context_predictor_family", "model_label"], observed=True)
        .agg(mean_r2=("r2_observed_fitted", "mean"), mean_delta_r2=("delta_r2_vs_baseline", "mean"))
        .reset_index()
    )
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))
    sns.lineplot(data=agg, x="context_k", y="mean_r2", hue="model_label", marker="o", ax=axes[0])
    axes[0].set_title("Mean in-sample R2 by context window")
    axes[0].set_xlabel("Scoring context")
    axes[0].set_ylabel("Mean R2")
    sns.lineplot(data=agg, x="context_k", y="mean_delta_r2", hue="model_label", marker="o", ax=axes[1])
    axes[1].set_title("Mean delta R2 vs baseline by context window")
    axes[1].set_xlabel("Scoring context")
    axes[1].set_ylabel("Mean delta R2")
    axes[1].legend_.remove()
    fig.tight_layout()
    out = fig_dir / "compare_k_model_family_r2.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / "compare_k_model_family_r2.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_cross_k_context_coefficients(summary: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot entropy and context-size coefficient summaries across k."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sub = summary[summary["status"].eq("fit")].copy()
    entropy = sub[sub["context_entropy_coef"].notna()].copy()
    size = sub[sub["context_size_coef"].notna()].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))
    if entropy.empty:
        axes[0].text(0.5, 0.5, "No entropy fits", ha="center", va="center")
        axes[0].set_axis_off()
    else:
        entropy_hues = entropy["context_predictor_family"].nunique()
        sns.pointplot(
            data=entropy,
            x="context_k",
            y="context_entropy_coef",
            hue="context_predictor_family",
            dodge=0.35 if entropy_hues > 1 else False,
            ax=axes[0],
        )
        axes[0].axhline(0, color="#333333", linewidth=1)
        axes[0].set_title("Context entropy coefficient by k")
        axes[0].set_ylabel("Bits per entropy bit")
    if size.empty:
        axes[1].text(0.5, 0.5, "No context-size fits", ha="center", va="center")
        axes[1].set_axis_off()
    else:
        size_hues = size["context_predictor_family"].nunique()
        sns.pointplot(
            data=size,
            x="context_k",
            y="context_size_coef",
            hue="context_predictor_family",
            dodge=0.35 if size_hues > 1 else False,
            ax=axes[1],
        )
        axes[1].axhline(0, color="#333333", linewidth=1)
        axes[1].set_title("Context-size coefficient by k")
        axes[1].set_ylabel("Bits per context-size unit")
    fig.tight_layout()
    out = fig_dir / "compare_k_context_coefficients.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / "compare_k_context_coefficients.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_cross_k_context_predictors(by_age: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot context-size and entropy means across k."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    agg = (
        by_age.groupby(["context_k", "measure_col", "measure_label"], observed=True)
        .agg(mean=("mean", "mean"))
        .reset_index()
    )
    sizes = agg[agg["measure_col"].ne("context_entropy_bits")].copy()
    entropy = agg[agg["measure_col"].eq("context_entropy_bits")].copy()
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    sns.lineplot(data=sizes, x="context_k", y="mean", hue="measure_label", marker="o", ax=axes[0])
    axes[0].set_title("Mean context-window size by k")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Mean size")
    axes[0].legend(title="Measure", fontsize=8, title_fontsize=9)
    sns.lineplot(data=entropy, x="context_k", y="mean", marker="o", color="#d95f02", ax=axes[1])
    axes[1].set_title("Mean context entropy by k")
    axes[1].set_xlabel("Scoring context")
    axes[1].set_ylabel("Mean entropy bits")
    fig.tight_layout()
    out = fig_dir / "compare_k_context_predictor_distributions.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / "compare_k_context_predictor_distributions.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def write_outputs(
    *,
    summary: pd.DataFrame,
    distribution: pd.DataFrame,
    by_age: pd.DataFrame,
    measured_manifest: pd.DataFrame,
    output_dir: Path,
) -> Mapping[str, Path]:
    """Persist analysis outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "measured_manifest": output_dir / "route1_real_child_context_measures_manifest.csv",
        "model_summary": output_dir / "context_predictor_model_summary.csv",
        "context_distribution": output_dir / "context_predictor_distribution.csv",
        "context_by_age": output_dir / "context_predictors_by_age.csv",
    }
    measured_manifest.to_csv(paths["measured_manifest"], index=False)
    summary.to_csv(paths["model_summary"], index=False)
    distribution.to_csv(paths["context_distribution"], index=False)
    by_age.to_csv(paths["context_by_age"], index=False)
    return paths


def read_outputs(output_dir: Path) -> Mapping[str, pd.DataFrame]:
    """Read saved analysis outputs."""

    return {
        "measured_manifest": pd.read_csv(output_dir / "route1_real_child_context_measures_manifest.csv"),
        "model_summary": pd.read_csv(output_dir / "context_predictor_model_summary.csv"),
        "context_distribution": pd.read_csv(output_dir / "context_predictor_distribution.csv"),
        "context_by_age": pd.read_csv(output_dir / "context_predictors_by_age.csv"),
    }


def plot_all(
    summary: pd.DataFrame,
    distribution: pd.DataFrame,
    by_age: pd.DataFrame,
    *,
    fig_dir: Path,
    context_ks: Sequence[str] = DEFAULT_CONTEXT_KS,
) -> pd.DataFrame:
    """Generate all report figures and return a manifest."""

    rows: list[dict[str, object]] = []
    for context_k in context_ks:
        for kind, path in [
            ("context_size_distribution", plot_context_distributions(distribution, context_k=context_k, fig_dir=fig_dir)),
            ("context_predictors_by_age", plot_context_by_age(by_age, context_k=context_k, fig_dir=fig_dir)),
            ("model_family_r2", plot_r2_by_family(summary, context_k=context_k, fig_dir=fig_dir)),
            ("entropy_coefficients", plot_entropy_coefficients(summary, context_k=context_k, fig_dir=fig_dir)),
            ("context_size_coefficients", plot_context_size_heatmaps(summary, context_k=context_k, fig_dir=fig_dir)),
            ("age_coefficients", plot_age_coefficients(summary, context_k=context_k, fig_dir=fig_dir)),
        ]:
            rows.append({"context_k": context_k, "figure_kind": kind, "path": str(path)})
    if len(context_ks) > 1:
        for kind, path in [
            ("compare_k_model_family_r2", plot_cross_k_r2(summary, fig_dir)),
            ("compare_k_context_coefficients", plot_cross_k_context_coefficients(summary, fig_dir)),
            ("compare_k_context_predictor_distributions", plot_cross_k_context_predictors(by_age, fig_dir)),
        ]:
            rows.append({"context_k": "all", "figure_kind": kind, "path": str(path)})
    manifest = pd.DataFrame(rows)
    fig_dir.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(fig_dir.parent / "context_predictor_permutation_figure_manifest.csv", index=False)
    return manifest


def fitted_summary_for_report(summary: pd.DataFrame, *, context_k: str) -> pd.DataFrame:
    """Return compact fitted rows for one k."""

    cols = [
        "model_label",
        "estimator",
        "library",
        "covariance",
        "target_effort_label",
        "context_size_label",
        "status",
        "n_obs",
        "n_children",
        "r2_observed_fitted",
        "delta_r2_vs_baseline",
        "age_coef",
        "age_p",
        "target_effort_coef",
        "target_effort_p",
        "context_entropy_coef",
        "context_entropy_p",
        "context_size_coef",
        "context_size_p",
        "std_context_entropy_beta",
        "std_context_size_beta",
        "error",
    ]
    out = summary[summary["context_k"].eq(context_k)][cols].copy()
    for col in [column for column in out.columns if column.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def top_context_effects(summary: pd.DataFrame, *, context_k: str, n: int = 12) -> pd.DataFrame:
    """Return top context predictor rows by delta R2."""

    sub = summary[
        summary["context_k"].eq(context_k)
        & summary["status"].eq("fit")
        & summary["context_predictor_family"].ne("baseline")
    ].copy()
    if sub.empty:
        return sub
    cols = [
        "model_label",
        "target_effort_label",
        "context_size_label",
        "r2_observed_fitted",
        "delta_r2_vs_baseline",
        "context_entropy_coef",
        "context_entropy_p",
        "context_size_coef",
        "context_size_p",
        "std_context_entropy_beta",
        "std_context_size_beta",
    ]
    out = sub.sort_values("delta_r2_vs_baseline", ascending=False)[cols].head(n).copy()
    for col in ["context_entropy_p", "context_size_p"]:
        out[col] = out[col].map(format_p)
    return out


def context_k_takeaways(summary: pd.DataFrame, *, context_k: str) -> list[str]:
    """Return short data-driven takeaways for one k."""

    sub = summary[summary["context_k"].eq(context_k) & summary["status"].eq("fit")].copy()
    if sub.empty:
        return [f"No context-predictor models fit for {context_k}."]
    base = sub[sub["context_predictor_family"].eq("baseline")]
    nonbase = sub[sub["context_predictor_family"].ne("baseline")]
    bullets: list[str] = []
    if not base.empty:
        bullets.append(
            f"Baseline controls alone average R2={base['r2_observed_fitted'].mean():.3f} across target effort controls."
        )
    if not nonbase.empty:
        best = nonbase.sort_values("delta_r2_vs_baseline", ascending=False).iloc[0]
        bullets.append(
            "Best context addition: "
            f"{best['model_label']} with {best['target_effort_label']}"
            + (f" and {best['context_size_label']}" if best["context_size_label"] else "")
            + f", delta R2={best['delta_r2_vs_baseline']:.4f}."
        )
    entropy = nonbase[nonbase["context_entropy_coef"].notna()].copy()
    if not entropy.empty:
        sig = int((pd.to_numeric(entropy["context_entropy_p"], errors="coerce") < 0.05).sum())
        neg = int((pd.to_numeric(entropy["context_entropy_coef"], errors="coerce") < 0).sum())
        bullets.append(f"Entropy appears in {len(entropy)} fitted rows: {sig} have p<.05 and {neg} have negative coefficients.")
    size = nonbase[nonbase["context_size_coef"].notna()].copy()
    if not size.empty:
        sig = int((pd.to_numeric(size["context_size_p"], errors="coerce") < 0.05).sum())
        pos = int((pd.to_numeric(size["context_size_coef"], errors="coerce") > 0).sum())
        bullets.append(f"Context size appears in {len(size)} fitted rows: {sig} have p<.05 and {pos} have positive coefficients.")
    return bullets


def build_context_k_markdown(
    *,
    context_k: str,
    summary: pd.DataFrame,
    distribution: pd.DataFrame,
    fig_manifest: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> str:
    """Build one context-k report."""

    figures = {
        row["figure_kind"]: Path(row["path"])
        for row in fig_manifest[fig_manifest["context_k"].eq(context_k)].to_dict("records")
    }
    dist = distribution[distribution["context_k"].eq(context_k)].copy()
    fitted = fitted_summary_for_report(summary, context_k=context_k)
    top = top_context_effects(summary, context_k=context_k)
    takeaways = context_k_takeaways(summary, context_k=context_k)
    table_guide = pd.DataFrame(
        [
            ("model_label", "Which context-predictor permutation is being fit."),
            ("estimator", "The model family. Here this is linear OLS for every fitted row."),
            ("library", "The Python implementation used to fit the model."),
            ("covariance", "How standard errors and p-values are computed."),
            ("target_effort_label", "Which target utterance effort unit is controlled."),
            ("context_size_label", "Which context-window size unit is used; blank when the model has no context-size predictor."),
            ("r2_observed_fitted", "In-sample fitted-versus-observed R2."),
            ("delta_r2_vs_baseline", "Extra R2 relative to the same target-effort baseline with no context predictor."),
            ("context_entropy_coef", "Estimated bit change for a one-bit increase in context entropy."),
            ("context_size_coef", "Estimated bit change for one additional context-size unit."),
            ("std_context_entropy_beta", "Standardized entropy coefficient, useful for scale comparison."),
            ("std_context_size_beta", "Standardized context-size coefficient, useful for scale comparison."),
        ],
        columns=["column", "how_to_interpret"],
    )
    context_note = (
        "`k0` has no preceding context by definition, so entropy and context-size predictors are unavailable."
        if context_k == "k0"
        else "Context predictors are computed from the preceding caretaker context text for this k window."
    )
    return f"""# Context Predictor Permutations: {context_k}

This internal report is separate from the previous M1-M6 reports. It asks
whether context predictors explain total child utterance information.

{context_note}

## Model Question

Outcome:

```text
sum_bits
```

Baseline controls:

```text
age + target utterance effort + child identity
```

Context predictor permutations:

```text
C0: no context predictor
C1: context entropy only
C2: context-window size only
C3: context entropy + context-window size
```

Implementation details for every fitted row:

```text
Estimator: linear ordinary least squares regression
Library: statsmodels.formula.api.ols
Uncertainty: child-cluster robust standard errors, cov_type='cluster'
Cluster unit: child_id
```

This means the fitted mean is linear in the listed predictors. The p-values and
confidence intervals are adjusted for repeated observations within children by
clustering the covariance matrix at the child level. This is not a GEE, GLM, or
mixed-effects model; those would be separate estimator subvariants.

The target utterance effort unit and context-window size unit are varied
separately. That means, for example, one row may control target utterance
phonemes while using context-window words as the context-size predictor.

## Table Column Guide

{markdown_table(table_guide, max_rows=20)}

## Context Predictor Distributions

How to read: these tables and plots describe the context window itself, not the
target utterance. For `k0`, context sizes are zero and entropy is unavailable.

{markdown_table(dist, max_rows=12, digits=3)}

![{context_k} context size distribution](../{figures.get('context_size_distribution', '')})

![{context_k} context predictors by age](../{figures.get('context_predictors_by_age', '')})

## Model Fit Overview

How to read: the R2 plot shows fit; the delta-R2 plot shows how much context
predictors add beyond age, target effort, and child identity.

![{context_k} R2 by model family](../{figures.get('model_family_r2', '')})

## Coefficient Views

How to read: coefficients are in Mistral bits. Negative entropy coefficients
mean higher context entropy is associated with lower target utterance bits after
controls; positive context-size coefficients mean longer preceding context is
associated with higher target utterance bits after controls.

![{context_k} entropy coefficients](../{figures.get('entropy_coefficients', '')})

![{context_k} context size coefficients](../{figures.get('context_size_coefficients', '')})

![{context_k} age coefficients](../{figures.get('age_coefficients', '')})

## Top Context Effects

{markdown_table(top, max_rows=12, digits=4)}

## Full Model Summary

{markdown_table(fitted, max_rows=90, digits=4)}

## Hottest Takeaways For {context_k}

{chr(10).join(f"- {item}" for item in takeaways)}

## Saved Outputs

```text
{output_dir / "context_predictor_model_summary.csv"}
{output_dir / "context_predictor_distribution.csv"}
{output_dir / "context_predictors_by_age.csv"}
{fig_dir}/
```
"""


def build_compare_markdown(
    *,
    summary: pd.DataFrame,
    distribution: pd.DataFrame,
    fig_manifest: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> str:
    """Build cross-k comparison report."""

    figures = {
        row["figure_kind"]: Path(row["path"])
        for row in fig_manifest[fig_manifest["context_k"].eq("all")].to_dict("records")
    }
    fit_rows = (
        summary[summary["status"].eq("fit")]
        .groupby(["context_k", "model_label"], observed=True)
        .agg(
            fitted_rows=("model_id", "size"),
            mean_r2=("r2_observed_fitted", "mean"),
            mean_delta_r2=("delta_r2_vs_baseline", "mean"),
            significant_entropy=("context_entropy_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_context_size=("context_size_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
        )
        .reset_index()
    )
    context_overview = distribution[
        distribution["measure_col"].isin(["context_nb_words", "context_nb_phonemes", "context_entropy_bits"])
    ].copy()
    return f"""# Context Predictor Permutations: K0-K3 Comparison

This report compares the four scoring-context settings. It does not replace the
older M1-M6 reports; it is a new context-predictor sensitivity report.

## How To Read The Comparison

- `k0` is the no-context scorer condition. It can fit the baseline controls but
  cannot fit context entropy or context-size models because there is no context.
- `k1`, `k2`, and `k3` use increasingly larger preceding caretaker context
  windows.
- `mean_delta_r2` is the average added in-sample R2 relative to the no-context
  predictor baseline with the same target effort control.
- These are not held-out predictive scores; they are fit diagnostics and
  inferential screens for the current model family.

Implementation for all rows in this report:

```text
Estimator: linear OLS regression
Library: statsmodels.formula.api.ols
Uncertainty: child-cluster robust standard errors, cov_type='cluster'
Cluster unit: child_id
```

So these are linear child-clustered OLS screens, not GEE/GLM/mixed-model fits.

## Fit Summary By K

{markdown_table(fit_rows, max_rows=80, digits=4)}

## Context Predictor Magnitudes By K

{markdown_table(context_overview, max_rows=40, digits=3)}

## Cross-K Plots

How to read: the first plot asks whether adding context predictors increases
fit differently for k1/k2/k3. The second plot asks whether entropy and size
coefficients change as the context window grows. The third plot confirms that
context windows mechanically grow from k1 to k3.

![R2 comparison](../{figures.get('compare_k_model_family_r2', '')})

![Coefficient comparison](../{figures.get('compare_k_context_coefficients', '')})

![Context predictor distribution comparison](../{figures.get('compare_k_context_predictor_distributions', '')})

## Saved Outputs

```text
{output_dir / "context_predictor_model_summary.csv"}
{output_dir / "context_predictor_distribution.csv"}
{output_dir / "context_predictors_by_age.csv"}
{fig_dir}/
```
"""


def run_analysis(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_ks: Sequence[str],
    chunksize: int,
    checkpoint_csv: Path | None = None,
) -> Mapping[str, Path]:
    """Run data extraction, context counts, model fitting, and plotting."""

    records: list[FitRecord] = []
    distribution_parts: list[pd.DataFrame] = []
    by_age_parts: list[pd.DataFrame] = []
    measured_manifest_rows: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_csv = checkpoint_csv or output_dir / "unique_context_measurements.checkpoint.csv"

    for context_k in context_ks:
        print(f"[stage] reading and measuring {context_k}", flush=True)
        rows = read_real_child_rows(input_csv, context_ks=[context_k], chunksize=chunksize)
        measured, context_counts_df = attach_context_size_counts(rows, checkpoint_csv=checkpoint_csv)
        measured_path = output_dir / f"route1_real_child_context_measures_{context_k}.csv.gz"
        measured_for_output = measured.drop(columns=["context_text"], errors="ignore")
        measured_for_output.to_csv(measured_path, index=False)
        measured_manifest_rows.append(
            {
                "context_k": context_k,
                "path": str(measured_path),
                "rows": len(measured_for_output),
                "unique_context_texts_for_k": len(context_counts_df),
            }
        )
        distribution_parts.append(context_distribution_rows(measured_for_output))
        by_age_parts.append(context_by_age_rows(measured_for_output))
        print(f"[stage] fitting {context_k}", flush=True)
        records.extend(fit_context_permutation_models(measured_for_output, context_k=context_k))
        del rows, measured, measured_for_output, context_counts_df
        gc.collect()

    summary = summary_rows(records)
    distribution = pd.concat(distribution_parts, ignore_index=True) if distribution_parts else pd.DataFrame()
    by_age = pd.concat(by_age_parts, ignore_index=True) if by_age_parts else pd.DataFrame()
    measured_manifest = pd.DataFrame(measured_manifest_rows)
    paths = write_outputs(
        summary=summary,
        distribution=distribution,
        by_age=by_age,
        measured_manifest=measured_manifest,
        output_dir=output_dir,
    )
    fig_manifest = plot_all(summary, distribution, by_age, fig_dir=fig_dir, context_ks=context_ks)
    fig_manifest.to_csv(output_dir / "figure_manifest.csv", index=False)
    audit = pd.DataFrame(
        [
            {
                "input_csv": str(input_csv),
                "context_ks": ",".join(context_ks),
                "rows": int(measured_manifest["rows"].sum()) if not measured_manifest.empty else 0,
                "unique_context_texts_by_k_sum": int(measured_manifest["unique_context_texts_for_k"].sum())
                if not measured_manifest.empty
                else 0,
                "checkpoint_csv": str(checkpoint_csv),
                "model_rows": len(summary),
                "fitted_model_rows": int(summary["status"].eq("fit").sum()),
                "figure_rows": len(fig_manifest),
            }
        ]
    )
    audit.to_csv(output_dir / "context_predictor_audit.csv", index=False)
    return {**paths, "figure_manifest": output_dir / "figure_manifest.csv", "audit": output_dir / "context_predictor_audit.csv"}


def run_report(
    *,
    output_dir: Path,
    fig_dir: Path,
    doc_dir: Path,
) -> Mapping[str, Path]:
    """Render all context-k reports from saved analysis outputs."""

    outputs = read_outputs(output_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)
    summary = outputs["model_summary"]
    distribution = outputs["context_distribution"]
    fig_manifest = pd.read_csv(output_dir / "figure_manifest.csv")
    written: dict[str, Path] = {}
    for context_k in DEFAULT_CONTEXT_KS:
        md = doc_dir / f"utterance_information_context_predictors_{context_k}.md"
        html = doc_dir / f"utterance_information_context_predictors_{context_k}.html"
        md.write_text(
            build_context_k_markdown(
                context_k=context_k,
                summary=summary,
                distribution=distribution,
                fig_manifest=fig_manifest,
                output_dir=output_dir,
                fig_dir=fig_dir,
            ),
            encoding="utf-8",
        )
        render_markdown_file(md, html)
        written[f"{context_k}_md"] = md
        written[f"{context_k}_html"] = html
    compare_md = doc_dir / "utterance_information_context_predictors_k_comparison.md"
    compare_html = doc_dir / "utterance_information_context_predictors_k_comparison.html"
    compare_md.write_text(
        build_compare_markdown(
            summary=summary,
            distribution=distribution,
            fig_manifest=fig_manifest,
            output_dir=output_dir,
            fig_dir=fig_dir,
        ),
        encoding="utf-8",
    )
    render_markdown_file(compare_md, compare_html)
    written["compare_md"] = compare_md
    written["compare_html"] = compare_html
    return written


def run_all(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_dir: Path,
    context_ks: Sequence[str],
    chunksize: int,
    checkpoint_csv: Path | None = None,
) -> Mapping[str, Path]:
    """Run analysis and report rendering."""

    analysis = run_analysis(
        input_csv=input_csv,
        output_dir=output_dir,
        fig_dir=fig_dir,
        context_ks=context_ks,
        chunksize=chunksize,
        checkpoint_csv=checkpoint_csv,
    )
    report = run_report(output_dir=output_dir, fig_dir=fig_dir, doc_dir=doc_dir)
    return {**analysis, **report}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--context-ks", nargs="+", default=list(DEFAULT_CONTEXT_KS))
    parser.add_argument("--context-count-checkpoint", type=Path, default=None)
    parser.add_argument("--chunksize", type=int, default=DEFAULT_CHUNKSIZE)
    parser.add_argument("--stage", choices=["all", "analysis", "report"], default="all")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.stage in {"all", "analysis"}:
        outputs = run_analysis(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_ks=args.context_ks,
            chunksize=args.chunksize,
            checkpoint_csv=args.context_count_checkpoint,
        )
        print(f"[OK] wrote context-predictor model summary: {outputs['model_summary']}")
        print(f"[OK] wrote context-predictor audit: {outputs['audit']}")
    if args.stage in {"all", "report"}:
        written = run_report(output_dir=args.output_dir, fig_dir=args.fig_dir, doc_dir=args.doc_dir)
        print(f"[OK] wrote context-predictor comparison report: {written['compare_html']}")


if __name__ == "__main__":
    main()
