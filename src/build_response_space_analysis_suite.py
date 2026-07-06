#!/usr/bin/env python3
"""Build focused Route 1 and Route 2 analyses using response-space predictors.

This script consumes the compact child-row response-space table. It does not
read generated sample shards and it does not rescan the full Route 1 long table.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route2_response_space/route2_child_response_space_effort_table.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route2_response_space_analysis")
DEFAULT_FIG_DIR = Path("figs/route2_response_space_analysis")
DEFAULT_REPORT_MD = Path("docs/response_space_route1_route2_analysis.md")
DEFAULT_REPORT_HTML = Path("docs/response_space_route1_route2_analysis.html")

USECOLS = [
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "speaker",
    "context_text",
    "target_utterance_clean",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
    "context_entropy_bits",
    "context_next_top1_prob",
    "route2_context_word_count",
    "response_entropy_context_id",
    "response_entropy_bits",
    "response_entropy_empirical_bits",
    "response_unique_response_count",
    "response_top_probability",
    "response_rejection_rate",
    "response_valid_selected_count",
    "response_invalid_selected_count",
    "generated_expected_words",
    "generated_median_words",
    "generated_p90_words",
    "generated_valid_sample_words_sd",
    "generated_valid_sample_words_iqr",
    "generated_valid_sample_words_probability_le_3",
    "generated_valid_sample_words_probability_gt_20",
    "generated_valid_word_count_entropy_bits",
    "child_words_minus_generated_mean",
    "child_words_z_vs_generated",
    "child_words_percentile_in_generated_distribution",
    "child_words_cdf_lt_generated_distribution",
    "child_words_cdf_le_generated_distribution",
    "child_shorter_than_generated_median",
    "child_longer_than_generated_p90",
    "fallback_used_for_context",
    "valid_sample_count",
]

NUMERIC_COLS = [
    "session_id",
    "age_months",
    "line_no",
    "utt_id",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
    "context_entropy_bits",
    "context_next_top1_prob",
    "route2_context_word_count",
    "response_entropy_bits",
    "response_entropy_empirical_bits",
    "response_unique_response_count",
    "response_top_probability",
    "response_rejection_rate",
    "response_valid_selected_count",
    "response_invalid_selected_count",
    "generated_expected_words",
    "generated_median_words",
    "generated_p90_words",
    "generated_valid_sample_words_sd",
    "generated_valid_sample_words_iqr",
    "generated_valid_sample_words_probability_le_3",
    "generated_valid_sample_words_probability_gt_20",
    "generated_valid_word_count_entropy_bits",
    "child_words_minus_generated_mean",
    "child_words_z_vs_generated",
    "child_words_percentile_in_generated_distribution",
    "child_words_cdf_lt_generated_distribution",
    "child_words_cdf_le_generated_distribution",
    "valid_sample_count",
]

BOOL_COLS = [
    "child_shorter_than_generated_median",
    "child_longer_than_generated_p90",
    "fallback_used_for_context",
]

REUSABLE_PREDICTOR_COLS = [
    "response_entropy_context_id",
    "response_entropy_bits",
    "response_entropy_empirical_bits",
    "response_unique_response_count",
    "response_top_probability",
    "response_rejection_rate",
    "response_valid_selected_count",
    "response_invalid_selected_count",
    "generated_expected_words",
    "generated_median_words",
    "generated_p90_words",
    "generated_valid_sample_words_sd",
    "generated_valid_sample_words_iqr",
    "generated_valid_sample_words_probability_le_3",
    "generated_valid_sample_words_probability_gt_20",
    "generated_valid_word_count_entropy_bits",
    "valid_sample_count",
    "fallback_used_for_context",
    "route2_context_word_count",
]

CORE_MODEL_COLS = [
    "age_months",
    "child_id",
    "nb_words",
    "response_entropy_bits",
    "generated_expected_words",
    "route2_context_word_count",
    "context_entropy_bits",
]

PREDICTOR_TERMS = [
    "age_months_c",
    "age_within_child_c",
    "child_mean_age_c",
    "nb_words_c",
    "response_entropy_bits_c",
    "generated_expected_words_c",
    "route2_context_word_count_c",
    "context_entropy_bits_c",
    "age_months_c:response_entropy_bits_c",
    "age_within_child_c:response_entropy_bits_c",
]


@dataclass(frozen=True)
class ModelSpec:
    """One focused model to fit."""

    model_id: str
    family: str
    outcome: str
    formula: str
    required_cols: tuple[str, ...]
    exclude_fallback: bool = False


def age_bin_midpoint(value: object) -> float:
    """Return the midpoint of an age-bin label like ``024-029``."""

    match = re.match(r"^\s*(\d+)-(\d+)\s*$", str(value))
    if not match:
        return math.nan
    return (float(match.group(1)) + float(match.group(2))) / 2.0


def coerce_bool_series(series: pd.Series) -> pd.Series:
    """Convert mixed bool/string values to pandas nullable booleans."""

    truthy = {"1", "true", "t", "yes", "y"}
    falsy = {"0", "false", "f", "no", "n", ""}
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map(lambda value: True if value in truthy else (False if value in falsy else pd.NA))
        .astype("boolean")
    )


def read_response_space_table(path: Path) -> pd.DataFrame:
    """Read the analysis columns from the response-space child-row table."""

    available = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [col for col in USECOLS if col in available]
    missing = {"score_id", "utterance_id", "child_id", "age_months", "nb_words", "response_entropy_bits"} - set(usecols)
    if missing:
        raise KeyError(f"{path} missing required columns: {sorted(missing)}")
    frame = pd.read_csv(path, usecols=usecols, dtype=str, keep_default_na=False, low_memory=False)
    for col in NUMERIC_COLS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in BOOL_COLS:
        if col in frame.columns:
            frame[col] = coerce_bool_series(frame[col])
    frame["age_bin_mid"] = frame["age_bin"].map(age_bin_midpoint) if "age_bin" in frame.columns else math.nan
    return frame


def add_centered_columns(frame: pd.DataFrame, columns: Sequence[str]) -> dict[str, float]:
    """Add ``_c`` centered versions of present numeric columns."""

    centers: dict[str, float] = {}
    for col in columns:
        if col not in frame.columns:
            continue
        center = float(pd.to_numeric(frame[col], errors="coerce").mean())
        centers[col] = center
        frame[f"{col}_c"] = frame[col] - center
    return centers


def result_to_series(result: Any, attr: str) -> pd.Series:
    """Return statsmodels result arrays with stable term names."""

    values = getattr(result, attr)
    if isinstance(values, pd.Series):
        return values
    return pd.Series(values, index=result.model.exog_names)


def result_confint(result: Any) -> pd.DataFrame:
    """Return a named confidence interval table."""

    ci = result.conf_int()
    if isinstance(ci, pd.DataFrame):
        out = ci.copy()
    else:
        out = pd.DataFrame(ci, index=result.model.exog_names)
    out.columns = ["conf_low", "conf_high"]
    return out


CENTER_COLUMNS = [
    "age_months",
    "nb_words",
    "response_entropy_bits",
    "generated_expected_words",
    "route2_context_word_count",
    "context_entropy_bits",
]


def strip_child_fixed_effect(formula: str) -> str:
    """Remove child fixed effects from a Patsy formula."""

    return formula.replace(" + C(child_id)", "").replace("+ C(child_id)", "")


def mundlak_formula(formula: str) -> str:
    """Replace pooled centered age with within/between child age terms."""

    base = strip_child_fixed_effect(formula)
    base = base.replace("age_months_c:response_entropy_bits_c", "age_within_child_c:response_entropy_bits_c")
    return base.replace("age_months_c", "age_within_child_c + child_mean_age_c", 1)


def add_within_between_age(frame: pd.DataFrame) -> pd.DataFrame:
    """Add Mundlak-style within-child and between-child age terms."""

    out = frame.copy()
    child_mean = out.groupby("child_id")["age_months"].transform("mean")
    out["age_within_child"] = out["age_months"] - child_mean
    out["child_mean_age"] = child_mean
    out["age_within_child_c"] = out["age_within_child"] - out["age_within_child"].mean()
    out["child_mean_age_c"] = out["child_mean_age"] - out["child_mean_age"].mean()
    return out


def finite_model_frame(frame: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    """Drop rows with missing or non-finite numeric model columns."""

    data = frame.dropna(subset=cols).copy()
    for col in cols:
        if col != "child_id":
            data = data[np.isfinite(pd.to_numeric(data[col], errors="coerce"))]
    return data


def prepared_row_frame(frame: pd.DataFrame, spec: ModelSpec) -> pd.DataFrame:
    """Prepare row-level data for one model spec."""

    data = frame.copy()
    add_centered_columns(data, CENTER_COLUMNS)
    required = list(dict.fromkeys([spec.outcome, "child_id", *spec.required_cols]))
    data = finite_model_frame(data, required)
    if spec.exclude_fallback and "fallback_used_for_context" in data.columns:
        data = data[~data["fallback_used_for_context"].fillna(False).astype(bool)].copy()
    return data


def session_aggregate_frame(frame: pd.DataFrame, spec: ModelSpec) -> pd.DataFrame:
    """Aggregate utterance rows to child-session rows before fitting."""

    raw_required = [
        spec.outcome,
        "age_months",
        "child_id",
        "dataset",
        "session_id",
        "age_bin",
        "response_entropy_bits",
        "generated_expected_words",
        "route2_context_word_count",
        "context_entropy_bits",
    ]
    if "nb_words_c" in spec.required_cols and spec.outcome != "nb_words":
        raw_required.append("nb_words")
    data = frame.dropna(subset=[col for col in raw_required if col in frame.columns]).copy()
    if spec.exclude_fallback and "fallback_used_for_context" in data.columns:
        data = data[~data["fallback_used_for_context"].fillna(False).astype(bool)].copy()
    numeric_cols = [
        col
        for col in [
            spec.outcome,
            "age_months",
            "nb_words",
            "response_entropy_bits",
            "generated_expected_words",
            "route2_context_word_count",
            "context_entropy_bits",
        ]
        if col in data.columns
    ]
    agg = {col: "mean" for col in numeric_cols}
    agg["score_id"] = "size"
    group_cols = ["child_id", "dataset", "session_id", "age_bin"]
    session = data.groupby(group_cols, dropna=False).agg(agg).reset_index().rename(columns={"score_id": "n_utterances"})
    add_centered_columns(session, CENTER_COLUMNS)
    session = add_within_between_age(session)
    needed = [spec.outcome, "child_id", *spec.required_cols]
    needed = [col for col in needed if col in session.columns]
    return finite_model_frame(session, needed)


def descriptive_r2(result: Any, data: pd.DataFrame, outcome: str) -> float:
    """Return a descriptive fitted-vs-observed R2 when available."""

    try:
        fitted = np.asarray(result.fittedvalues)
        observed = np.asarray(data[outcome], dtype=float)
        ss_res = float(np.square(observed - fitted).sum())
        ss_tot = float(np.square(observed - observed.mean()).sum())
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else math.nan
    except Exception:
        return math.nan


def no_fit_summary(spec: ModelSpec, *, estimator_id: str, level: str, formula: str, data: pd.DataFrame, status: str) -> tuple[dict[str, Any], pd.DataFrame, None]:
    """Return a standard no-fit tuple."""

    return (
        {
            "model_id": spec.model_id,
            "estimator_id": estimator_id,
            "level": level,
            "family": spec.family,
            "outcome": spec.outcome,
            "status": status,
            "n": int(len(data)),
            "children": int(data["child_id"].nunique()) if "child_id" in data.columns and not data.empty else 0,
            "formula": formula,
            "exclude_fallback": spec.exclude_fallback,
        },
        pd.DataFrame(),
        None,
    )


def fitted_summary_and_coefs(
    result: Any,
    data: pd.DataFrame,
    spec: ModelSpec,
    *,
    estimator_id: str,
    level: str,
    formula: str,
) -> tuple[dict[str, Any], pd.DataFrame, Any]:
    """Create standard summary and coefficient rows from a fitted result."""

    params = result_to_series(result, "params")
    bse = result_to_series(result, "bse")
    pvalues = result_to_series(result, "pvalues")
    ci = result_confint(result)
    coef = pd.DataFrame(
        {
            "model_id": spec.model_id,
            "estimator_id": estimator_id,
            "level": level,
            "family": spec.family,
            "outcome": spec.outcome,
            "term": params.index,
            "estimate": params.values,
            "std_error": bse.reindex(params.index).values,
            "p_value": pvalues.reindex(params.index).values,
            "conf_low": ci.reindex(params.index)["conf_low"].values,
            "conf_high": ci.reindex(params.index)["conf_high"].values,
        }
    )
    summary = {
        "model_id": spec.model_id,
        "estimator_id": estimator_id,
        "level": level,
        "family": spec.family,
        "outcome": spec.outcome,
        "status": "fit",
        "n": int(len(data)),
        "children": int(data["child_id"].nunique()),
        "mean_outcome": float(data[spec.outcome].mean()),
        "formula": formula,
        "exclude_fallback": spec.exclude_fallback,
        "r2": float(getattr(result, "rsquared", math.nan)),
        "descriptive_fitted_r2": descriptive_r2(result, data, spec.outcome),
        "aic": float(getattr(result, "aic", math.nan)) if hasattr(result, "aic") else math.nan,
        "bic": float(getattr(result, "bic", math.nan)) if hasattr(result, "bic") else math.nan,
    }
    return summary, coef, result


def fit_row_ols_child_fe_cluster(frame: pd.DataFrame, spec: ModelSpec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit row-level OLS with child fixed effects and child-cluster SE."""

    data = prepared_row_frame(frame, spec)
    if len(data) < 50 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="row_ols_child_fe_cluster", level="utterance", formula=spec.formula, data=data, status="no_fit")
    result = smf.ols(spec.formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": data["child_id"]})
    return fitted_summary_and_coefs(
        result,
        data,
        spec,
        estimator_id="row_ols_child_fe_cluster",
        level="utterance",
        formula=spec.formula,
    )


def fit_session_gee_exchangeable(frame: pd.DataFrame, spec: ModelSpec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit child-session aggregate Gaussian GEE grouped by child."""

    data = session_aggregate_frame(frame, spec)
    formula = strip_child_fixed_effect(spec.formula)
    if len(data) < 20 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="session_gee_exchangeable", level="child_session", formula=formula, data=data, status="no_fit")
    result = smf.gee(
        formula,
        groups="child_id",
        data=data,
        cov_struct=Exchangeable(),
        family=sm.families.Gaussian(),
    ).fit()
    return fitted_summary_and_coefs(
        result,
        data,
        spec,
        estimator_id="session_gee_exchangeable",
        level="child_session",
        formula=formula,
    )


def fit_session_mundlak_gee(frame: pd.DataFrame, spec: ModelSpec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit child-session aggregate GEE with within/between-child age terms."""

    data = session_aggregate_frame(frame, spec)
    formula = mundlak_formula(spec.formula)
    required_terms = ["age_within_child_c", "child_mean_age_c"]
    data = finite_model_frame(data, [spec.outcome, "child_id", *required_terms, *[c for c in spec.required_cols if c != "age_months_c"]])
    if len(data) < 20 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="session_mundlak_gee", level="child_session", formula=formula, data=data, status="no_fit")
    result = smf.gee(
        formula,
        groups="child_id",
        data=data,
        cov_struct=Exchangeable(),
        family=sm.families.Gaussian(),
    ).fit()
    return fitted_summary_and_coefs(
        result,
        data,
        spec,
        estimator_id="session_mundlak_gee",
        level="child_session",
        formula=formula,
    )


def fit_session_mixedlm_random_age(frame: pd.DataFrame, spec: ModelSpec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit child-session aggregate mixed model with child random intercept/slope."""

    data = session_aggregate_frame(frame, spec)
    formula = strip_child_fixed_effect(spec.formula)
    if len(data) < 20 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="session_mixedlm_random_age", level="child_session", formula=formula, data=data, status="no_fit")
    try:
        result = smf.mixedlm(
            formula,
            data=data,
            groups=data["child_id"],
            re_formula="1 + age_months_c",
        ).fit(reml=False, method="lbfgs", maxiter=200, disp=False)
    except Exception as exc:
        summary, coef, _ = no_fit_summary(
            spec,
            estimator_id="session_mixedlm_random_age",
            level="child_session",
            formula=formula,
            data=data,
            status=f"fit_failed:{type(exc).__name__}",
        )
        return summary, coef, None
    return fitted_summary_and_coefs(
        result,
        data,
        spec,
        estimator_id="session_mixedlm_random_age",
        level="child_session",
        formula=formula,
    )


def fit_repeated_measure_models(frame: pd.DataFrame, spec: ModelSpec) -> list[tuple[dict[str, Any], pd.DataFrame, Any | None]]:
    """Fit the focused repeated-measures estimator set for one model spec."""

    return [
        fit_row_ols_child_fe_cluster(frame, spec),
        fit_session_gee_exchangeable(frame, spec),
        fit_session_mundlak_gee(frame, spec),
        fit_session_mixedlm_random_age(frame, spec),
    ]


def model_specs() -> list[ModelSpec]:
    """Return the bounded Route 1/Route 2 model list."""

    specs: list[ModelSpec] = []
    route2_formula = (
        "{outcome} ~ age_months_c + response_entropy_bits_c + "
        "generated_expected_words_c + route2_context_word_count_c + context_entropy_bits_c + C(child_id)"
    )
    route2_required = (
        "age_months_c",
        "response_entropy_bits_c",
        "generated_expected_words_c",
        "route2_context_word_count_c",
        "context_entropy_bits_c",
    )
    for outcome in ["nb_words", "nb_morphemes", "nb_syllables_pkg", "nb_phonemes"]:
        specs.append(
            ModelSpec(
                model_id=f"route2_{outcome}_effort_choice",
                family="route2_effort_choice",
                outcome=outcome,
                formula=route2_formula.format(outcome=outcome),
                required_cols=route2_required,
            )
        )
        specs.append(
            ModelSpec(
                model_id=f"route2_{outcome}_effort_choice_no_fallback",
                family="route2_effort_choice_no_fallback",
                outcome=outcome,
                formula=route2_formula.format(outcome=outcome),
                required_cols=route2_required,
                exclude_fallback=True,
            )
        )

    route1_formula = (
        "{outcome} ~ age_months_c + nb_words_c + response_entropy_bits_c + "
        "generated_expected_words_c + route2_context_word_count_c + context_entropy_bits_c + C(child_id)"
    )
    route1_interaction_formula = (
        "{outcome} ~ age_months_c + nb_words_c + response_entropy_bits_c + "
        "age_months_c:response_entropy_bits_c + generated_expected_words_c + "
        "route2_context_word_count_c + context_entropy_bits_c + C(child_id)"
    )
    route1_required = (
        "age_months_c",
        "nb_words_c",
        "response_entropy_bits_c",
        "generated_expected_words_c",
        "route2_context_word_count_c",
        "context_entropy_bits_c",
    )
    route1_interaction_required = (*route1_required, "age_months_c")
    for outcome in ["sum_bits", "mean_bits_per_token"]:
        specs.append(
            ModelSpec(
                model_id=f"route1_{outcome}_response_space_enriched",
                family="route1_information_response_space_enriched",
                outcome=outcome,
                formula=route1_formula.format(outcome=outcome),
                required_cols=route1_required,
            )
        )
        specs.append(
            ModelSpec(
                model_id=f"route1_{outcome}_age_by_response_entropy",
                family="route1_information_age_entropy_interaction",
                outcome=outcome,
                formula=route1_interaction_formula.format(outcome=outcome),
                required_cols=route1_interaction_required,
            )
        )
    return specs


def write_predictor_exports(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    """Write compact context-level and utterance-level response-space predictors."""

    output_dir.mkdir(parents=True, exist_ok=True)
    predictor_cols = [col for col in REUSABLE_PREDICTOR_COLS if col in frame.columns]
    context_cols = ["response_entropy_context_id", *[col for col in predictor_cols if col != "response_entropy_context_id"]]
    context = frame[context_cols].drop_duplicates("response_entropy_context_id").sort_values("response_entropy_context_id")
    utterance_cols = [
        "score_id",
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        *predictor_cols,
    ]
    utterance_cols = [col for col in utterance_cols if col in frame.columns]
    utterance = frame[utterance_cols].drop_duplicates("score_id").sort_values("score_id")

    route1_cols = [
        "score_id",
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "target_utterance_clean",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_pkg",
        "nb_phonemes",
        "sum_bits",
        "mean_bits_per_token",
        "context_entropy_bits",
        *predictor_cols,
    ]
    route1_cols = [col for col in route1_cols if col in frame.columns]
    route1_enriched = frame[route1_cols].drop_duplicates("score_id").sort_values("score_id")

    paths = {
        "context_predictors": output_dir / "response_space_predictors_by_context.csv.gz",
        "utterance_predictors": output_dir / "response_space_predictors_by_utterance.csv.gz",
        "route1_real_child_enriched": output_dir / "route1_real_child_response_space_enriched.csv.gz",
    }
    context.to_csv(paths["context_predictors"], index=False)
    utterance.to_csv(paths["utterance_predictors"], index=False)
    route1_enriched.to_csv(paths["route1_real_child_enriched"], index=False)
    return paths


def summary_by_age_bin(frame: pd.DataFrame, value_cols: Sequence[str]) -> pd.DataFrame:
    """Return age-bin means and standard errors for selected metrics."""

    rows: list[dict[str, Any]] = []
    for age_bin, group in frame.groupby("age_bin", dropna=False, sort=False):
        for col in value_cols:
            if col not in group.columns:
                continue
            values = pd.to_numeric(group[col], errors="coerce").dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "age_bin": age_bin,
                    "age_bin_mid": age_bin_midpoint(age_bin),
                    "metric": col,
                    "n": int(len(values)),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "sd": float(values.std(ddof=1)) if len(values) > 1 else math.nan,
                    "se": float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else math.nan,
                    "p10": float(values.quantile(0.10)),
                    "p90": float(values.quantile(0.90)),
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["age_bin_mid", "metric"]).reset_index(drop=True)
    return out


def response_entropy_bins(frame: pd.DataFrame, n_bins: int = 20) -> pd.DataFrame:
    """Bin response entropy and summarize child length residuals."""

    needed = ["response_entropy_bits", "child_words_minus_generated_mean", "nb_words", "generated_expected_words"]
    data = frame.dropna(subset=needed).copy()
    if data.empty:
        return pd.DataFrame()
    data["entropy_bin"] = pd.qcut(data["response_entropy_bits"], q=n_bins, duplicates="drop")
    rows = []
    for interval, group in data.groupby("entropy_bin", observed=True):
        rows.append(
            {
                "entropy_bin": str(interval),
                "response_entropy_bits_mean": float(group["response_entropy_bits"].mean()),
                "n": int(len(group)),
                "child_words_minus_generated_mean": float(group["child_words_minus_generated_mean"].mean()),
                "nb_words_mean": float(group["nb_words"].mean()),
                "generated_expected_words_mean": float(group["generated_expected_words"].mean()),
                "child_words_percentile_mean": float(group["child_words_percentile_in_generated_distribution"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("response_entropy_bits_mean").reset_index(drop=True)


def save_lineplot(summary: pd.DataFrame, metrics: Sequence[str], labels: dict[str, str], path: Path, *, ylabel: str) -> None:
    """Save an age-bin line plot for one or more metrics."""

    plot = summary[summary["metric"].isin(metrics)].copy()
    if plot.empty:
        return
    plot["label"] = plot["metric"].map(labels).fillna(plot["metric"])
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(11, 6))
    for label, group in plot.groupby("label", sort=False):
        group = group.sort_values("age_bin_mid")
        ax.plot(group["age_bin"].astype(str), group["mean"], marker="o", linewidth=2.2, label=label)
        if group["se"].notna().any():
            ax.fill_between(
                group["age_bin"].astype(str),
                group["mean"] - 1.96 * group["se"].fillna(0),
                group["mean"] + 1.96 * group["se"].fillna(0),
                alpha=0.16,
            )
    ax.set_xlabel("Age bin in months")
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_entropy_residual_plot(bins: pd.DataFrame, path: Path) -> None:
    """Plot child length residual versus response entropy bins."""

    if bins.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        bins["response_entropy_bits_mean"],
        bins["child_words_minus_generated_mean"],
        marker="o",
        linewidth=2.2,
        color="#2f6f73",
    )
    ax.axhline(0, color="#444", linewidth=1, linestyle="--")
    ax.set_xlabel("Response entropy (bits), binned mean")
    ax.set_ylabel("Child words minus generated expected words")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_coefficient_plot(coefs: pd.DataFrame, path: Path) -> None:
    """Plot coefficients for the focused response-space terms."""

    plot = coefs[coefs["term"].isin(PREDICTOR_TERMS)].copy()
    if plot.empty:
        return
    plot["model_label"] = (
        plot["model_id"].str.replace("_", " ", regex=False)
        + " / "
        + plot["estimator_id"].str.replace("_", " ", regex=False)
    )
    plot["term_label"] = plot["term"].str.replace("_c", "", regex=False).str.replace("_", " ", regex=False)
    plot = plot.sort_values(["family", "outcome", "term_label"])
    sns.set_theme(style="whitegrid", context="paper")
    height = max(6, 0.28 * len(plot))
    fig, ax = plt.subplots(figsize=(11, height))
    y = np.arange(len(plot))
    ax.errorbar(
        plot["estimate"],
        y,
        xerr=[plot["estimate"] - plot["conf_low"], plot["conf_high"] - plot["estimate"]],
        fmt="o",
        color="#2f6f73",
        ecolor="#9bb8b5",
        elinewidth=1.5,
        capsize=2,
    )
    ax.axvline(0, color="#333", linewidth=1, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(plot["model_label"] + " | " + plot["term_label"])
    ax.set_xlabel("Coefficient estimate with 95% CI")
    ax.set_ylabel("")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def prediction_grid(
    frame: pd.DataFrame,
    result: Any,
    *,
    outcome: str,
    response_entropy_levels: Sequence[float],
    n_ages: int = 25,
) -> pd.DataFrame:
    """Build illustrative fixed-covariate predictions for one fitted model."""

    age_values = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_ages)
    most_common_child = frame["child_id"].mode().iloc[0]
    centers = {col: frame[col].mean() for col in ["age_months", "nb_words", "response_entropy_bits", "generated_expected_words", "route2_context_word_count", "context_entropy_bits"] if col in frame.columns}
    rows = []
    for entropy in response_entropy_levels:
        for age in age_values:
            row = {
                "age_months": age,
                "child_id": most_common_child,
                "nb_words": centers.get("nb_words", math.nan),
                "response_entropy_bits": entropy,
                "generated_expected_words": centers.get("generated_expected_words", math.nan),
                "route2_context_word_count": centers.get("route2_context_word_count", math.nan),
                "context_entropy_bits": centers.get("context_entropy_bits", math.nan),
                "response_entropy_level": entropy,
            }
            for base_col, center in centers.items():
                row[f"{base_col}_c"] = row[base_col] - center
            rows.append(row)
    grid = pd.DataFrame(rows)
    grid[f"predicted_{outcome}"] = result.predict(grid)
    return grid


def save_prediction_plot(grid: pd.DataFrame, outcome: str, path: Path) -> None:
    """Save fixed-covariate model prediction lines."""

    if grid.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(10, 6))
    for level, group in grid.groupby("response_entropy_level", sort=True):
        ax.plot(group["age_months"], group[f"predicted_{outcome}"], linewidth=2.2, label=f"entropy={level:.2f}")
    ax.set_xlabel("Age in months")
    ax.set_ylabel(f"Predicted {outcome}")
    ax.legend(title="Response entropy", frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 20, digits: int = 4) -> str:
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
    """Return a POSIX relative path from a report document to an artifact."""

    return Path("../" + path.as_posix()).as_posix() if not path.is_absolute() else path.as_posix()


def build_report(
    *,
    report_md: Path,
    report_html: Path,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    audit: pd.DataFrame,
    model_summary: pd.DataFrame,
    coef: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write a short Markdown/HTML report."""

    audit_map = dict(zip(audit["metric"], audit["value"]))
    key_terms = coef[coef["term"].isin(PREDICTOR_TERMS)].copy()
    if not key_terms.empty:
        key_terms = key_terms[
            ["family", "outcome", "model_id", "term", "estimate", "std_error", "p_value", "conf_low", "conf_high"]
        ].sort_values(["family", "outcome", "model_id", "term"])
    lines = [
        "# Response-Space Route 1 / Route 2 Analysis",
        "",
        "This is a focused first-pass analysis using the production response-space entropy run.",
        "It does not score generated responses and does not claim that generated samples are same-meaning paraphrases.",
        "",
        "## Inputs",
        "",
        f"- Child-row response-space table: `{input_csv}`",
        f"- Output directory: `{output_dir}`",
        f"- Figure directory: `{fig_dir}`",
        "",
        "## Audit",
        "",
        (
            f"Scope warning: this response-space analysis currently covers "
            f"`{audit_map.get('unique_children', 'NA')}` children across "
            f"`{audit_map.get('unique_datasets', 'NA')}` datasets. It is the "
            "production response-space subset available right now, not the full "
            "79-child cleaned bundle."
        ),
        "",
        markdown_table(audit, max_rows=40),
        "",
        "## Figures",
        "",
    ]
    for label, path in figure_paths.items():
        lines.extend([f"### {label}", "", f"![{label}]({relative_to_doc(path, report_md)})", ""])
    lines.extend(
        [
            "## Model Summary",
            "",
            markdown_table(
                model_summary[
                    [
                        "family",
                        "model_id",
                        "estimator_id",
                        "level",
                        "outcome",
                        "status",
                        "n",
                        "children",
                        "descriptive_fitted_r2",
                        "exclude_fallback",
                    ]
                ],
                max_rows=60,
            ),
            "",
            "## Key Response-Space Coefficients",
            "",
            markdown_table(key_terms, max_rows=80),
            "",
            "## Interpretation Boundary",
            "",
            "- Route 2 effort-choice models ask whether actual child effort varies with response-space uncertainty and generated expected effort for the same context.",
            "- Route 1 enriched models ask whether actual child information is associated with response-space predictors after child effort and context controls.",
            "- The full communicative-efficiency cloud still requires scoring generated responses on Mila.",
        ]
    )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(report_md, report_html)


def build_response_space_analysis_suite(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
) -> dict[str, Path]:
    """Run the focused response-space analysis suite."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_response_space_table(input_csv)
    add_centered_columns(
        frame,
        ["age_months", "nb_words", "response_entropy_bits", "generated_expected_words", "route2_context_word_count", "context_entropy_bits"],
    )

    export_paths = write_predictor_exports(frame, output_dir)

    age_summary = summary_by_age_bin(
        frame,
        [
            "nb_words",
            "generated_expected_words",
            "response_entropy_bits",
            "child_words_percentile_in_generated_distribution",
            "child_words_minus_generated_mean",
        ],
    )
    entropy_bin_summary = response_entropy_bins(frame)
    age_summary.to_csv(output_dir / "response_space_summary_by_age_bin.csv", index=False)
    entropy_bin_summary.to_csv(output_dir / "response_entropy_binned_residual_summary.csv", index=False)

    figure_paths = {
        "Route 2 child length percentile by age": fig_dir / "route2_child_length_percentile_by_age.png",
        "Route 2 expected generated length and actual child length by age": fig_dir / "route2_actual_vs_generated_words_by_age.png",
        "Route 2 response entropy by age": fig_dir / "route2_response_entropy_by_age.png",
        "Route 2 child length residual versus response entropy": fig_dir / "route2_length_residual_vs_response_entropy.png",
        "Response-space model coefficients": fig_dir / "response_space_key_coefficients.png",
    }
    save_lineplot(
        age_summary,
        ["child_words_percentile_in_generated_distribution"],
        {"child_words_percentile_in_generated_distribution": "child percentile in generated word-count distribution"},
        figure_paths["Route 2 child length percentile by age"],
        ylabel="Mean percentile",
    )
    save_lineplot(
        age_summary,
        ["nb_words", "generated_expected_words"],
        {"nb_words": "actual child words", "generated_expected_words": "generated expected words"},
        figure_paths["Route 2 expected generated length and actual child length by age"],
        ylabel="Words",
    )
    save_lineplot(
        age_summary,
        ["response_entropy_bits"],
        {"response_entropy_bits": "response entropy bits"},
        figure_paths["Route 2 response entropy by age"],
        ylabel="Bits",
    )
    save_entropy_residual_plot(
        entropy_bin_summary,
        figure_paths["Route 2 child length residual versus response entropy"],
    )

    summaries: list[dict[str, Any]] = []
    coefs: list[pd.DataFrame] = []
    fitted_results: dict[tuple[str, str], Any] = {}
    for spec in model_specs():
        for summary, coef, result in fit_repeated_measure_models(frame, spec):
            summaries.append(summary)
            if not coef.empty:
                coefs.append(coef)
            if result is not None:
                fitted_results[(spec.model_id, str(summary.get("estimator_id", "")))] = result
    model_summary = pd.DataFrame(summaries)
    coef_table = pd.concat(coefs, ignore_index=True) if coefs else pd.DataFrame()
    model_summary.to_csv(output_dir / "response_space_model_summary.csv", index=False)
    coef_table.to_csv(output_dir / "response_space_model_coefficients.csv", index=False)
    save_coefficient_plot(coef_table, figure_paths["Response-space model coefficients"])

    prediction_paths: dict[str, Path] = {}
    for model_id, outcome in [
        ("route2_nb_words_effort_choice", "nb_words"),
        ("route1_sum_bits_response_space_enriched", "sum_bits"),
        ("route1_mean_bits_per_token_response_space_enriched", "mean_bits_per_token"),
    ]:
        result = fitted_results.get((model_id, "session_gee_exchangeable")) or fitted_results.get(
            (model_id, "row_ols_child_fe_cluster")
        )
        if result is None:
            continue
        levels = frame["response_entropy_bits"].quantile([0.10, 0.50, 0.90]).dropna().tolist()
        grid = prediction_grid(frame, result, outcome=outcome, response_entropy_levels=levels)
        grid_path = output_dir / f"{model_id}_prediction_grid.csv"
        fig_path = fig_dir / f"{model_id}_prediction_lines.png"
        grid.to_csv(grid_path, index=False)
        save_prediction_plot(grid, outcome, fig_path)
        prediction_paths[model_id] = grid_path
        figure_paths[f"Prediction lines: {model_id}"] = fig_path

    audit = pd.DataFrame(
        [
            {"metric": "input_rows", "value": len(frame)},
            {"metric": "unique_score_ids", "value": frame["score_id"].nunique()},
            {"metric": "unique_utterance_ids", "value": frame["utterance_id"].nunique()},
            {"metric": "unique_children", "value": frame["child_id"].nunique()},
            {"metric": "unique_datasets", "value": frame["dataset"].nunique() if "dataset" in frame.columns else math.nan},
            {"metric": "unique_response_entropy_contexts", "value": frame["response_entropy_context_id"].nunique()},
            {"metric": "fallback_rows", "value": int(frame["fallback_used_for_context"].fillna(False).astype(bool).sum())},
            {"metric": "fallback_contexts", "value": int(frame.loc[frame["fallback_used_for_context"].fillna(False).astype(bool), "response_entropy_context_id"].nunique())},
            {"metric": "missing_context_entropy_rows", "value": int(frame["context_entropy_bits"].isna().sum()) if "context_entropy_bits" in frame.columns else math.nan},
            {"metric": "context_predictor_rows", "value": int(pd.read_csv(export_paths["context_predictors"], usecols=["response_entropy_context_id"]).shape[0])},
            {"metric": "utterance_predictor_rows", "value": int(pd.read_csv(export_paths["utterance_predictors"], usecols=["score_id"]).shape[0])},
            {"metric": "fit_models", "value": int(model_summary["status"].eq("fit").sum()) if not model_summary.empty else 0},
        ]
    )
    audit.to_csv(output_dir / "response_space_analysis_audit.csv", index=False)

    build_report(
        report_md=report_md,
        report_html=report_html,
        input_csv=input_csv,
        output_dir=output_dir,
        fig_dir=fig_dir,
        audit=audit,
        model_summary=model_summary,
        coef=coef_table,
        figure_paths=figure_paths,
    )

    return {
        "audit": output_dir / "response_space_analysis_audit.csv",
        "age_summary": output_dir / "response_space_summary_by_age_bin.csv",
        "entropy_bins": output_dir / "response_entropy_binned_residual_summary.csv",
        "model_summary": output_dir / "response_space_model_summary.csv",
        "coefficients": output_dir / "response_space_model_coefficients.csv",
        "report_md": report_md,
        "report_html": report_html,
        **export_paths,
        **prediction_paths,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    args = parser.parse_args(argv)
    paths = build_response_space_analysis_suite(
        input_csv=args.input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
    )
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
