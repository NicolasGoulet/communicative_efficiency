#!/usr/bin/env python3
"""Build the Route 1 best-model robustness package before the supervisor report.

This is a pre-supervisor evidence gallery. It does not replace the final
supervisor-facing report. It pulls together existing Route 1 artifacts and adds
a compact child-month/effort-band estimator-family comparison so the core
formula families can be viewed across OLS, GEE, GLM, and MixedLM analogues.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gamma, Gaussian
from statsmodels.genmod.families.links import Log

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_route1_corrected_baseline_atlas import question_type
    from build_supervisor_candidate_report import markdown_table, relative_to_report
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_corrected_baseline_atlas import question_type
    from src.build_supervisor_candidate_report import markdown_table, relative_to_report
    from src.render_markdown_report import render_markdown_file


ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_best_model_robustness_package")
DEFAULT_FIG_DIR = Path("figs/route1_best_model_robustness_package")
DEFAULT_DOC_DIR = Path("docs")
DOC_BASENAME = "route1_best_model_robustness_package"

REAL_ATLAS_DIR = Path("results/route1_source_specific_corrected_fixed_effort_atlas/real")
SOURCE_ATLAS_DIR = Path("results/route1_source_specific_corrected_fixed_effort_atlas")
DEEP_DIVE_DIR = Path("results/m1_m2_utterance_information_deep_dive")
CHILD_STRUCTURE_DIR = Path("results/route1_corrected_baseline_atlas/full_child_structure_sensitivity")
AGE_ROBUSTNESS_DIR = Path("results/age_scrambling_robustness")
HELDOUT_DIR = Path("results/route1_heldout_real_child_prediction")
CARETAKER_DIR = Path("results/route1_caretaker_atlas/full_fit")

REAL_FIG_DIR = Path("figs/route1_source_specific_corrected_fixed_effort_atlas/real")
AGE_ROBUSTNESS_FIG_DIR = Path("figs/age_scrambling_robustness")
SUPERVISOR_FIG_DIR = Path("figs/supervisor_candidate_report")
CARETAKER_FIG_DIR = Path("figs/route1_caretaker_corrected_fixed_effort_atlas")

CORE_MODEL_ORDER = [
    "M2",
    "M3",
    "M4c",
    "M5_no_question",
    "M5",
    "M5_age_effort_no_question",
    "M5_age_effort_question",
    "M5_parent_reaction_no_question",
    "M5_parent_reaction_question",
    "M15",
]
NONLINEAR_MODELS = ["M7", "M8", "M9", "M10"]
QUESTION_TYPE_ORDER = ["empty/no context", "not question", "wh-question", "yes/no question", "other question"]


@dataclass(frozen=True)
class CoreFormula:
    model_id: str
    label: str
    question: str
    fe_formula: str
    population_formula: str
    needs_context_entropy: bool = False
    needs_parent_context_effort: bool = False
    needs_question_type: bool = False
    includes_interaction: bool = False


@dataclass(frozen=True)
class EstimatorSpec:
    estimator_id: str
    label: str
    family: str
    dependence: str
    effect_scale: str
    uses_child_fixed_effects: bool = False
    re_formula: str = ""


CORE_FORMULAS = (
    CoreFormula(
        model_id="M2",
        label="Primary child-adjusted model",
        question="At the same effort level, does child age still predict total utterance information after stable child differences are controlled?",
        fe_formula="mean_sum_bits ~ age_c + effort_c + C(child_id)",
        population_formula="mean_sum_bits ~ age_c + effort_c",
    ),
    CoreFormula(
        model_id="M3",
        label="Age by effort model",
        question="Does the age-information relation change depending on production effort?",
        fe_formula="mean_sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)",
        population_formula="mean_sum_bits ~ age_c + effort_c + age_c:effort_c",
        includes_interaction=True,
    ),
    CoreFormula(
        model_id="M4c",
        label="Question/form control model",
        question="Does the age effect survive broad preceding-context question/statement controls?",
        fe_formula="mean_sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)",
        population_formula="mean_sum_bits ~ age_c + effort_c + C(question_type)",
        needs_question_type=True,
    ),
    CoreFormula(
        model_id="M5",
        label="Combined context-control model with question type",
        question="Does the age effect remain after target effort, context entropy, preceding caretaker effort, and question type are controlled?",
        fe_formula="mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)",
        population_formula="mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type)",
        needs_context_entropy=True,
        needs_parent_context_effort=True,
        needs_question_type=True,
    ),
    CoreFormula(
        model_id="M5_no_question",
        label="Combined context-control model without question type",
        question="Does the age effect remain after target effort, context entropy, and preceding caretaker effort are controlled, without using question type?",
        fe_formula="mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)",
        population_formula="mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c",
        needs_context_entropy=True,
        needs_parent_context_effort=True,
    ),
    CoreFormula(
        model_id="M5_age_effort_no_question",
        label="Context-control age-by-effort model without question type",
        question="After context controls, does the age-information relation change depending on child production effort, without using question type?",
        fe_formula=(
            "mean_sum_bits ~ age_c + effort_c + age_c:effort_c "
            "+ context_entropy_c + parent_context_effort_c + C(child_id)"
        ),
        population_formula=(
            "mean_sum_bits ~ age_c + effort_c + age_c:effort_c "
            "+ context_entropy_c + parent_context_effort_c"
        ),
        needs_context_entropy=True,
        needs_parent_context_effort=True,
        includes_interaction=True,
    ),
    CoreFormula(
        model_id="M5_age_effort_question",
        label="Context-control age-by-effort model with question type",
        question="After context and question/form controls, does the age-information relation change depending on child production effort?",
        fe_formula=(
            "mean_sum_bits ~ age_c + effort_c + age_c:effort_c "
            "+ context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)"
        ),
        population_formula=(
            "mean_sum_bits ~ age_c + effort_c + age_c:effort_c "
            "+ context_entropy_c + parent_context_effort_c + C(question_type)"
        ),
        needs_context_entropy=True,
        needs_parent_context_effort=True,
        needs_question_type=True,
        includes_interaction=True,
    ),
    CoreFormula(
        model_id="M5_parent_reaction_no_question",
        label="Parent-context reaction model without question type",
        question="Does the relation between parent context effort and child utterance information change by age or by child effort, without using question type?",
        fe_formula=(
            "mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c "
            "+ age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)"
        ),
        population_formula=(
            "mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c "
            "+ age_c:parent_context_effort_c + effort_c:parent_context_effort_c"
        ),
        needs_context_entropy=True,
        needs_parent_context_effort=True,
        includes_interaction=True,
    ),
    CoreFormula(
        model_id="M5_parent_reaction_question",
        label="Parent-context reaction model with question type",
        question="Does the relation between parent context effort and child utterance information change by age or by child effort after question/form controls?",
        fe_formula=(
            "mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c "
            "+ age_c:parent_context_effort_c + effort_c:parent_context_effort_c "
            "+ C(question_type) + C(child_id)"
        ),
        population_formula=(
            "mean_sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c "
            "+ age_c:parent_context_effort_c + effort_c:parent_context_effort_c "
            "+ C(question_type)"
        ),
        needs_context_entropy=True,
        needs_parent_context_effort=True,
        needs_question_type=True,
        includes_interaction=True,
    ),
    CoreFormula(
        model_id="M15",
        label="Rich context-interaction stress test",
        question="Does the developmental effect survive a richer age/effort/context interaction stress test with lower-order terms kept?",
        fe_formula=(
            "mean_sum_bits ~ age_c + effort_c + age_c:effort_c + context_entropy_c + parent_context_effort_c + C(question_type) "
            "+ age_c:context_entropy_c + effort_c:context_entropy_c "
            "+ age_c:parent_context_effort_c + effort_c:parent_context_effort_c "
            "+ parent_context_effort_c:context_entropy_c + context_entropy_c:C(question_type) + C(child_id)"
        ),
        population_formula=(
            "mean_sum_bits ~ age_c + effort_c + age_c:effort_c + context_entropy_c + parent_context_effort_c + C(question_type) "
            "+ age_c:context_entropy_c + effort_c:context_entropy_c "
            "+ age_c:parent_context_effort_c + effort_c:parent_context_effort_c "
            "+ parent_context_effort_c:context_entropy_c + context_entropy_c:C(question_type)"
        ),
        needs_context_entropy=True,
        needs_parent_context_effort=True,
        needs_question_type=True,
        includes_interaction=True,
    ),
)

ESTIMATOR_SPECS = (
    EstimatorSpec(
        estimator_id="ols_fe_cluster",
        label="OLS + child fixed effects + clustered SE",
        family="OLS",
        dependence="C(child_id), covariance clustered by child",
        effect_scale="additive bits",
        uses_child_fixed_effects=True,
    ),
    EstimatorSpec(
        estimator_id="gee_gaussian",
        label="GEE Gaussian, clustered by child",
        family="GEE Gaussian",
        dependence="population-average GEE grouped by child",
        effect_scale="additive bits",
    ),
    EstimatorSpec(
        estimator_id="gee_gamma_log",
        label="GEE Gamma/log, clustered by child",
        family="GEE Gamma/log",
        dependence="population-average GEE grouped by child",
        effect_scale="log mean bits",
    ),
    EstimatorSpec(
        estimator_id="glm_gaussian",
        label="GLM Gaussian",
        family="GLM Gaussian",
        dependence="child fixed effects in the mean model",
        effect_scale="additive bits",
        uses_child_fixed_effects=True,
    ),
    EstimatorSpec(
        estimator_id="glm_gamma_log",
        label="GLM Gamma/log",
        family="GLM Gamma/log",
        dependence="child fixed effects in the mean model",
        effect_scale="log mean bits",
        uses_child_fixed_effects=True,
    ),
    EstimatorSpec(
        estimator_id="mixed_random_intercept",
        label="MixedLM random child intercept",
        family="MixedLM",
        dependence="random child intercept",
        effect_scale="additive bits",
        re_formula="1",
    ),
    EstimatorSpec(
        estimator_id="mixed_random_age_slope",
        label="MixedLM random child age slope",
        family="MixedLM",
        dependence="random child intercept and age slope",
        effect_scale="additive bits",
        re_formula="~age_c",
    ),
)


def parent_context_word_count(text: object) -> int:
    """Count word-like tokens in the prior caretaker context."""

    if text is None or pd.isna(text):
        return 0
    return len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:['-][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?", str(text)))


def assign_effort_band(value: object) -> str:
    val = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(val):
        return "missing"
    if val <= 4:
        return "1-4"
    if val <= 8:
        return "5-8"
    if val <= 12:
        return "9-12"
    return "13+"


def modal_value(values: pd.Series) -> str:
    modes = values.dropna().astype(str)
    if modes.empty:
        return ""
    counts = modes.value_counts()
    return str(counts.index[0])


def build_or_read_aggregate_frame(input_csv: Path, output_dir: Path, *, chunksize: int) -> pd.DataFrame:
    """Build child-session-context/effort-band aggregate rows for real k3 speech."""

    out_path = output_dir / "real_child_k3_month_effort_band_aggregate.csv.gz"
    if out_path.exists():
        return pd.read_csv(out_path)

    usecols = [
        "role",
        "target_variant",
        "context_k",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "sum_bits",
        "nb_words",
        "context_entropy_bits",
        "context_text",
    ]
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(input_csv, usecols=usecols, chunksize=chunksize, low_memory=False):
        chunk = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].eq("k3")
        ].copy()
        if chunk.empty:
            continue
        for col in ["age_months", "sum_bits", "nb_words", "context_entropy_bits"]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        chunk = chunk.dropna(subset=["age_months", "sum_bits", "nb_words"])
        chunk["question_type"] = chunk["context_text"].map(question_type)
        chunk["parent_context_effort"] = chunk["context_text"].map(parent_context_word_count)
        chunk["effort_band"] = chunk["nb_words"].map(assign_effort_band)
        parts.append(
            chunk[
                [
                    "dataset",
                    "child_id",
                    "session_id",
                    "age_months",
                    "age_bin",
                    "effort_band",
                    "sum_bits",
                    "nb_words",
                    "context_entropy_bits",
                    "parent_context_effort",
                    "question_type",
                ]
            ]
        )
    if not parts:
        raise RuntimeError(f"no real child k3 rows found in {input_csv}")
    rows = pd.concat(parts, ignore_index=True)
    grouped = rows.groupby(["dataset", "child_id", "session_id", "age_months", "age_bin", "effort_band"], dropna=False)
    aggregate = grouped.agg(
        n_utterances=("sum_bits", "size"),
        mean_sum_bits=("sum_bits", "mean"),
        mean_effort=("nb_words", "mean"),
        median_effort=("nb_words", "median"),
        mean_context_entropy=("context_entropy_bits", "mean"),
        context_entropy_nonblank=("context_entropy_bits", "count"),
        mean_parent_context_effort=("parent_context_effort", "mean"),
        question_type=("question_type", modal_value),
    ).reset_index()
    aggregate["question_type"] = pd.Categorical(aggregate["question_type"], categories=QUESTION_TYPE_ORDER, ordered=False)
    aggregate["unit_id"] = (
        aggregate["dataset"].astype(str)
        + "::"
        + aggregate["child_id"].astype(str)
        + "::"
        + aggregate["session_id"].astype(str)
        + "::"
        + aggregate["effort_band"].astype(str)
    )
    aggregate.to_csv(out_path, index=False)
    return aggregate


def prepare_model_frame(frame: pd.DataFrame, formula_def: CoreFormula) -> pd.DataFrame:
    """Return complete aggregate rows for one formula with centered predictors."""

    data = frame.copy()
    required = ["mean_sum_bits", "age_months", "mean_effort", "child_id"]
    if formula_def.needs_context_entropy:
        required.append("mean_context_entropy")
    if formula_def.needs_parent_context_effort:
        required.append("mean_parent_context_effort")
    if formula_def.needs_question_type:
        required.append("question_type")
    for col in ["mean_sum_bits", "age_months", "mean_effort", "mean_context_entropy", "mean_parent_context_effort"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=[col for col in required if col in data.columns]).copy()
    data = data[data["mean_sum_bits"] > 0].copy()
    data["age_c"] = data["age_months"] - data["age_months"].mean()
    data["effort_c"] = data["mean_effort"] - data["mean_effort"].mean()
    data["context_entropy_c"] = data["mean_context_entropy"] - data["mean_context_entropy"].mean()
    data["parent_context_effort_c"] = data["mean_parent_context_effort"] - data["mean_parent_context_effort"].mean()
    data["question_type"] = pd.Categorical(data["question_type"].astype(str), categories=QUESTION_TYPE_ORDER, ordered=False)
    return data


def observed_fitted_r2(observed: pd.Series, fitted: Iterable[float]) -> float:
    y = pd.to_numeric(observed, errors="coerce").to_numpy(dtype=float)
    yhat = np.asarray(list(fitted), dtype=float)
    mask = np.isfinite(y) & np.isfinite(yhat)
    if mask.sum() < 2 or np.nanstd(y[mask]) <= 0 or np.nanstd(yhat[mask]) <= 0:
        return math.nan
    return float(np.corrcoef(y[mask], yhat[mask])[0, 1] ** 2)


def extract_term(result: object, term: str) -> tuple[float, float, float, float]:
    params = getattr(result, "params", pd.Series(dtype=float))
    pvalues = getattr(result, "pvalues", pd.Series(dtype=float))
    bse = getattr(result, "bse", pd.Series(dtype=float))
    if term not in params.index:
        return math.nan, math.nan, math.nan, math.nan
    estimate = float(params[term])
    p_value = float(pvalues[term]) if term in pvalues.index else math.nan
    std_err = float(bse[term]) if term in bse.index else math.nan
    ci_low = estimate - 1.96 * std_err if math.isfinite(std_err) else math.nan
    ci_high = estimate + 1.96 * std_err if math.isfinite(std_err) else math.nan
    return estimate, p_value, ci_low, ci_high


KEY_TERM_COLUMNS = {
    "age_c": "age",
    "effort_c": "effort",
    "age_c:effort_c": "age_effort",
    "context_entropy_c": "context_entropy",
    "parent_context_effort_c": "parent_context_effort",
    "age_c:context_entropy_c": "age_context_entropy",
    "effort_c:context_entropy_c": "effort_context_entropy",
    "age_c:parent_context_effort_c": "age_parent_context_effort",
    "effort_c:parent_context_effort_c": "effort_parent_context_effort",
    "parent_context_effort_c:context_entropy_c": "parent_context_entropy",
}


def fit_one_estimator(frame: pd.DataFrame, formula_def: CoreFormula, estimator: EstimatorSpec) -> tuple[dict[str, object], object | None, pd.DataFrame]:
    """Fit one aggregate estimator and return summary, result, and model frame."""

    model_frame = prepare_model_frame(frame, formula_def)
    formula = formula_def.fe_formula if estimator.uses_child_fixed_effects else formula_def.population_formula
    base = {
        "model_id": formula_def.model_id,
        "model_label": formula_def.label,
        "question": formula_def.question,
        "estimator_id": estimator.estimator_id,
        "estimator_label": estimator.label,
        "estimator_family": estimator.family,
        "dependence": estimator.dependence,
        "effect_scale": estimator.effect_scale,
        "formula": formula,
        "n_obs": int(len(model_frame)),
        "n_children": int(model_frame["child_id"].nunique()) if "child_id" in model_frame else 0,
        "status": "error",
        "error": "",
        "warning": "",
    }
    if len(model_frame) < 10 or model_frame["child_id"].nunique() < 2:
        base["error"] = "not enough aggregate rows or children"
        return base, None, model_frame

    result = None
    warning_text = ""
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            if estimator.estimator_id == "ols_fe_cluster":
                result = smf.ols(formula, data=model_frame).fit(
                    cov_type="cluster",
                    cov_kwds={"groups": model_frame["child_id"]},
                )
            elif estimator.estimator_id == "glm_gaussian":
                result = smf.glm(formula, data=model_frame, family=Gaussian()).fit()
            elif estimator.estimator_id == "glm_gamma_log":
                result = smf.glm(formula, data=model_frame, family=Gamma(link=Log())).fit(maxiter=100)
            elif estimator.estimator_id == "gee_gaussian":
                result = smf.gee(formula, groups="child_id", data=model_frame, family=Gaussian(), cov_struct=Exchangeable()).fit()
            elif estimator.estimator_id == "gee_gamma_log":
                result = smf.gee(formula, groups="child_id", data=model_frame, family=Gamma(link=Log()), cov_struct=Exchangeable()).fit()
            elif estimator.estimator_id.startswith("mixed_"):
                result = smf.mixedlm(formula, data=model_frame, groups=model_frame["child_id"], re_formula=estimator.re_formula).fit(
                    reml=False,
                    method="lbfgs",
                    maxiter=200,
                    disp=False,
                )
            else:
                raise ValueError(f"unsupported estimator {estimator.estimator_id}")
            warning_text = "; ".join(str(item.message) for item in caught[:4])
        fitted = result.predict(model_frame)
        base.update(
            {
                "status": "fit",
                "warning": warning_text,
                "r2_observed_fitted": observed_fitted_r2(model_frame["mean_sum_bits"], fitted),
                "aic": float(getattr(result, "aic", math.nan)) if hasattr(result, "aic") else math.nan,
                "bic": float(getattr(result, "bic", math.nan)) if hasattr(result, "bic") else math.nan,
            }
        )
        for term, prefix in KEY_TERM_COLUMNS.items():
            coef, p_value, ci_low, ci_high = extract_term(result, term)
            base[f"{prefix}_coef"] = coef
            base[f"{prefix}_p"] = p_value
            base[f"{prefix}_ci_low"] = ci_low
            base[f"{prefix}_ci_high"] = ci_high
    except Exception as exc:  # pragma: no cover - exact failures depend on statsmodels versions
        base["error"] = f"{type(exc).__name__}: {exc}"
    return base, result, model_frame


def prediction_grid(model_frame: pd.DataFrame, formula_def: CoreFormula, estimator: EstimatorSpec) -> pd.DataFrame:
    ages = np.linspace(float(model_frame["age_months"].min()), float(model_frame["age_months"].max()), 80)
    effort = float(model_frame["mean_effort"].median())
    entropy = float(model_frame["mean_context_entropy"].mean()) if model_frame["mean_context_entropy"].notna().any() else 0.0
    parent = float(model_frame["mean_parent_context_effort"].mean()) if model_frame["mean_parent_context_effort"].notna().any() else 0.0
    children = sorted(model_frame["child_id"].astype(str).unique()) if estimator.uses_child_fixed_effects else [""]
    rows: list[dict[str, object]] = []
    for age in ages:
        for child in children:
            rows.append(
                {
                    "age_months": age,
                    "mean_effort": effort,
                    "mean_context_entropy": entropy,
                    "mean_parent_context_effort": parent,
                    "question_type": "not question",
                    "child_id": child,
                }
            )
    grid = pd.DataFrame(rows)
    grid["age_c"] = grid["age_months"] - model_frame["age_months"].mean()
    grid["effort_c"] = grid["mean_effort"] - model_frame["mean_effort"].mean()
    grid["context_entropy_c"] = grid["mean_context_entropy"] - model_frame["mean_context_entropy"].mean()
    grid["parent_context_effort_c"] = grid["mean_parent_context_effort"] - model_frame["mean_parent_context_effort"].mean()
    grid["question_type"] = pd.Categorical(grid["question_type"], categories=QUESTION_TYPE_ORDER, ordered=False)
    return grid


def fit_aggregate_estimators(aggregate: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summaries: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []
    fitted_rows: list[pd.DataFrame] = []
    for formula_def in CORE_FORMULAS:
        for estimator in ESTIMATOR_SPECS:
            summary, result, model_frame = fit_one_estimator(aggregate, formula_def, estimator)
            summaries.append(summary)
            if result is None or summary.get("status") != "fit":
                continue
            try:
                fitted = model_frame[
                    [
                        col
                        for col in [
                            "dataset",
                            "child_id",
                            "session_id",
                            "age_months",
                            "age_bin",
                            "effort_band",
                            "n_utterances",
                            "mean_sum_bits",
                            "mean_effort",
                            "mean_context_entropy",
                            "mean_parent_context_effort",
                            "question_type",
                        ]
                        if col in model_frame.columns
                    ]
                ].copy()
                fitted["model_id"] = formula_def.model_id
                fitted["estimator_id"] = estimator.estimator_id
                fitted["estimator_label"] = estimator.label
                fitted["effect_scale"] = estimator.effect_scale
                fitted["fitted_sum_bits"] = result.predict(model_frame)
                fitted["residual"] = fitted["mean_sum_bits"] - fitted["fitted_sum_bits"]
                fitted_rows.append(fitted)
                grid = prediction_grid(model_frame, formula_def, estimator)
                grid["predicted_sum_bits_raw"] = result.predict(grid)
                pred = (
                    grid.groupby("age_months", as_index=False)["predicted_sum_bits_raw"]
                    .mean()
                    .rename(columns={"predicted_sum_bits_raw": "predicted_sum_bits"})
                )
                pred["model_id"] = formula_def.model_id
                pred["estimator_id"] = estimator.estimator_id
                pred["estimator_label"] = estimator.label
                pred["effect_scale"] = estimator.effect_scale
                prediction_rows.append(pred)
            except Exception:
                continue
    summary_frame = pd.DataFrame(summaries)
    pred_frame = pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()
    fitted_frame = pd.concat(fitted_rows, ignore_index=True) if fitted_rows else pd.DataFrame()
    summary_frame.to_csv(output_dir / "aggregate_estimator_family_summary.csv", index=False)
    pred_frame.to_csv(output_dir / "aggregate_estimator_fixed_effort_predictions.csv", index=False)
    fitted_frame.to_csv(output_dir / "aggregate_estimator_fitted_values.csv.gz", index=False)
    return summary_frame, pred_frame, fitted_frame


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def build_artifact_audit(output_dir: Path) -> pd.DataFrame:
    """Record which existing artifacts satisfy each required evidence family."""

    checks = [
        ("corrected_ols_m1_m15", "Corrected real-child M1-M15 OLS Atlas", REAL_ATLAS_DIR / "model_summary.csv"),
        ("fixed_effort_predictions", "Corrected real-child fixed-effort prediction grids", REAL_ATLAS_DIR / "fixed_effort_predictions.csv.gz"),
        ("source_comparison", "Real/random/ngram/LSTM source-specific atlases", SOURCE_ATLAS_DIR / "real" / "fixed_slice_slopes.csv"),
        ("estimator_deep_dive", "Older M1-M3 OLS/GLM/GEE/MixedLM deep-dive fits", DEEP_DIVE_DIR / "expanded_model_family_summary.csv"),
        ("child_structure_sensitivity", "Corrected CS0-CS7 child-structure sensitivity for M1-M6", CHILD_STRUCTURE_DIR / "source_specific_model_summary.csv"),
        ("age_scrambling", "Age-scrambling and balanced-bootstrap robustness", AGE_ROBUSTNESS_DIR / "age_scrambling_robustness_summary.csv"),
        ("heldout_prediction", "Heldout actual-vs-predicted trajectory artifacts", HELDOUT_DIR / "heldout_prediction_fit_summary.csv"),
        ("caretaker_contrast", "Caretaker/parent Route 1 contrast", CARETAKER_DIR / "caretaker_model_summary.csv"),
    ]
    rows = []
    for audit_id, label, path in checks:
        rows.append(
            {
                "audit_id": audit_id,
                "requirement": label,
                "status": "available" if path.exists() else "missing",
                "path": str(path),
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "existing_artifact_audit.csv", index=False)
    return frame


def build_estimator_coverage(summary: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    rows = []
    for formula_def in CORE_FORMULAS:
        for estimator in ESTIMATOR_SPECS:
            sub = summary[
                summary["model_id"].eq(formula_def.model_id)
                & summary["estimator_id"].eq(estimator.estimator_id)
            ]
            fitted = bool((sub["status"] == "fit").any()) if not sub.empty else False
            rows.append(
                {
                    "model_id": formula_def.model_id,
                    "core_formula": formula_def.label,
                    "estimator_family": estimator.label,
                    "status": "fit in aggregate package" if fitted else "not fit",
                    "effect_scale": estimator.effect_scale,
                    "dependence_handling": estimator.dependence,
                    "artifact": str(output_dir / "aggregate_estimator_family_summary.csv"),
                }
            )
    for model_id in NONLINEAR_MODELS:
        rows.append(
            {
                "model_id": model_id,
                "core_formula": "Age-spline / nonlinear age variant",
                "estimator_family": "OLS + child fixed effects + clustered SE",
                "status": "available in corrected Atlas v2",
                "effect_scale": "additive bits",
                "dependence_handling": "C(child_id), covariance clustered by child",
                "artifact": str(REAL_ATLAS_DIR / "model_summary.csv"),
            }
        )
    rows.append(
        {
            "model_id": "aggregate",
            "core_formula": "Month-level aggregate estimator",
            "estimator_family": "child-month/session effort-band aggregate",
            "status": "fit in aggregate package",
            "effect_scale": "additive/log depending on estimator",
            "dependence_handling": "one row per child/session/effort band; optional child cluster/group/random effects",
            "artifact": str(output_dir / "real_child_k3_month_effort_band_aggregate.csv.gz"),
        }
    )
    rows.append(
        {
            "model_id": "heldout",
            "core_formula": "Heldout population prediction",
            "estimator_family": "PBM-trained population and Mundlak-compatible OLS",
            "status": "available in heldout report",
            "effect_scale": "additive bits",
            "dependence_handling": "no C(child_id) for unseen children; population/Mundlak design",
            "artifact": str(HELDOUT_DIR / "heldout_prediction_fit_summary.csv"),
        }
    )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "estimator_family_coverage.csv", index=False)
    return frame


def relation_text(coef: object, scale: object) -> str:
    val = pd.to_numeric(pd.Series([coef]), errors="coerce").iloc[0]
    if pd.isna(val):
        return ""
    direction = "higher" if val > 0 else "lower" if val < 0 else "unchanged"
    if str(scale) == "log mean bits":
        return f"{direction} expected sum_bits on the log-mean scale"
    return f"{direction} expected sum_bits on the additive-bit scale"


def build_key_term_relation_summary(summary: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Save a tidy table of the modeled relation between key predictors and sum_bits."""

    term_labels = {
        "age": "Age at session",
        "effort": "Child utterance effort",
        "age_effort": "Age x child effort",
        "context_entropy": "Context entropy",
        "parent_context_effort": "Parent context effort",
        "age_context_entropy": "Age x context entropy",
        "effort_context_entropy": "Child effort x context entropy",
        "age_parent_context_effort": "Age x parent context effort",
        "effort_parent_context_effort": "Child effort x parent context effort",
        "parent_context_entropy": "Parent context effort x context entropy",
    }
    rows: list[dict[str, object]] = []
    fitted = summary[summary["status"].eq("fit")].copy()
    for row in fitted.itertuples(index=False):
        row_data = row._asdict()
        for prefix, label in term_labels.items():
            coef = row_data.get(f"{prefix}_coef")
            p_value = row_data.get(f"{prefix}_p")
            if pd.isna(pd.to_numeric(pd.Series([coef]), errors="coerce").iloc[0]):
                continue
            rows.append(
                {
                    "model_id": row_data.get("model_id"),
                    "model_label": row_data.get("model_label"),
                    "estimator_label": row_data.get("estimator_label"),
                    "effect_scale": row_data.get("effect_scale"),
                    "term": label,
                    "coefficient": coef,
                    "p_value": p_value,
                    "ci_low": row_data.get(f"{prefix}_ci_low"),
                    "ci_high": row_data.get(f"{prefix}_ci_high"),
                    "relation_to_sum_bits": relation_text(coef, row_data.get("effect_scale")),
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "aggregate_key_term_relation_summary.csv", index=False)
    return frame


def plot_estimator_age_lines(predictions: pd.DataFrame, fig_dir: Path, *, model_id: str) -> Path:
    sub = predictions[predictions["model_id"].eq(model_id)].copy()
    fig, ax = plt.subplots(figsize=(12, 7))
    if sub.empty:
        ax.text(0.5, 0.5, f"No predictions for {model_id}", ha="center", va="center")
        ax.axis("off")
    else:
        additive = sub[sub["effect_scale"].eq("additive bits")]
        logscale = sub[sub["effect_scale"].eq("log mean bits")]
        for _, group in additive.groupby("estimator_label", sort=False):
            ax.plot(group["age_months"], group["predicted_sum_bits"], lw=2.2, label=group["estimator_label"].iloc[0])
        for _, group in logscale.groupby("estimator_label", sort=False):
            ax.plot(group["age_months"], group["predicted_sum_bits"], lw=2.0, linestyle="--", label=group["estimator_label"].iloc[0])
        ax.set_xlabel("Age (months)")
        ax.set_ylabel("Predicted mean sum_bits")
        ax.set_title(f"{model_id}: fixed-effort age lines across estimator families")
        ax.grid(color="#e5e7eb")
        ax.legend(fontsize=8, loc="best")
    path = fig_dir / f"{model_id.lower()}_aggregate_estimator_fixed_effort_age_lines.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_age_effect_forest(summary: pd.DataFrame, fig_dir: Path) -> Path:
    sub = summary[summary["status"].eq("fit")].copy()
    sub = sub[np.isfinite(pd.to_numeric(sub["age_coef"], errors="coerce"))].copy()
    sub["age_coef"] = pd.to_numeric(sub["age_coef"], errors="coerce")
    sub["age_ci_low"] = pd.to_numeric(sub["age_ci_low"], errors="coerce")
    sub["age_ci_high"] = pd.to_numeric(sub["age_ci_high"], errors="coerce")
    sub["model_id"] = pd.Categorical(sub["model_id"], categories=CORE_MODEL_ORDER, ordered=True)
    height = max(9, min(22, len(sub) * 0.22))
    fig, axes = plt.subplots(1, 2, figsize=(18, height), sharey=True)
    for ax, scale in zip(axes, ["additive bits", "log mean bits"]):
        data = sub[sub["effect_scale"].eq(scale)].sort_values(["model_id", "estimator_id"])
        if data.empty:
            ax.text(0.5, 0.5, f"No {scale} fits", ha="center", va="center")
            ax.axis("off")
            continue
        y_labels = [f"{row.model_id} | {row.estimator_family}" for row in data.itertuples()]
        y = np.arange(len(data))
        ax.hlines(y, data["age_ci_low"], data["age_ci_high"], color="#94a3b8", lw=1.8)
        ax.scatter(data["age_coef"], y, color="#0f766e", s=42)
        ax.axvline(0, color="#111827", lw=1.0, linestyle=":")
        ax.set_yticks(y)
        ax.set_yticklabels(y_labels, fontsize=7)
        ax.set_xlabel("Age coefficient")
        ax.set_title(scale)
        ax.grid(axis="x", color="#e5e7eb")
    fig.suptitle("Aggregate estimator-family age effects by core formula", y=1.01)
    plt.tight_layout()
    path = fig_dir / "aggregate_estimator_age_effect_forest.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_nested_r2(summary: pd.DataFrame, fig_dir: Path, output_dir: Path) -> Path:
    sub = summary[
        summary["status"].eq("fit")
        & summary["estimator_id"].eq("ols_fe_cluster")
        & summary["model_id"].isin(CORE_MODEL_ORDER)
    ].copy()
    sub["model_id"] = pd.Categorical(sub["model_id"], categories=CORE_MODEL_ORDER, ordered=True)
    sub = sub.sort_values("model_id")
    base = float(sub[sub["model_id"].astype(str).eq("M2")]["r2_observed_fitted"].iloc[0]) if (sub["model_id"].astype(str) == "M2").any() else math.nan
    sub["delta_r2_vs_m2"] = sub["r2_observed_fitted"] - base
    sub.to_csv(output_dir / "aggregate_ols_fe_nested_r2.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(18, 6.2))
    axes[0].bar(sub["model_id"].astype(str), sub["r2_observed_fitted"], color="#2f6f73")
    axes[0].set_ylabel("Observed-vs-fitted R2")
    axes[0].set_title("Aggregate OLS FE fit")
    axes[0].grid(axis="y", color="#e5e7eb")
    axes[0].tick_params(axis="x", labelrotation=35)
    axes[1].bar(sub["model_id"].astype(str), sub["delta_r2_vs_m2"] * 1000, color="#c76f2c")
    axes[1].axhline(0, color="#111827", lw=1)
    axes[1].set_ylabel("Delta R2 vs M2 x 1000")
    axes[1].set_title("Nested-model gain, not causal importance")
    axes[1].grid(axis="y", color="#e5e7eb")
    axes[1].tick_params(axis="x", labelrotation=35)
    plt.tight_layout()
    path = fig_dir / "aggregate_ols_fe_nested_r2.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_actual_vs_fitted(aggregate: pd.DataFrame, predictions: pd.DataFrame, fig_dir: Path, *, model_id: str = "M5") -> Path:
    pred = predictions[
        predictions["model_id"].eq(model_id)
        & predictions["estimator_id"].eq("ols_fe_cluster")
    ].copy()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.scatter(aggregate["age_months"], aggregate["mean_sum_bits"], s=16, alpha=0.22, color="#64748b", label="child-session/effort-band observed")
    by_age = aggregate.groupby(pd.cut(aggregate["age_months"], bins=18), observed=True).agg(
        age_mid=("age_months", "mean"),
        mean_sum_bits=("mean_sum_bits", "mean"),
    )
    ax.plot(by_age["age_mid"], by_age["mean_sum_bits"], color="#111827", lw=2.3, label="observed aggregate trend")
    if not pred.empty:
        ax.plot(pred["age_months"], pred["predicted_sum_bits"], color="#0f766e", lw=2.6, linestyle="--", label=f"{model_id} OLS FE fixed-effort prediction")
    ax.set_xlabel("Age (months)")
    ax.set_ylabel("Mean sum_bits")
    ax.set_title(f"Actual aggregate trajectory vs {model_id} fixed-effort model prediction")
    ax.grid(color="#e5e7eb")
    ax.legend()
    plt.tight_layout()
    path = fig_dir / f"{model_id.lower()}_aggregate_actual_vs_model_prediction.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_residual_calibration(fitted_values: pd.DataFrame, fig_dir: Path, *, model_id: str) -> Path:
    sub = fitted_values[fitted_values["model_id"].eq(model_id)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
    if sub.empty:
        for ax in axes:
            ax.text(0.5, 0.5, f"No fitted values for {model_id}", ha="center", va="center")
            ax.axis("off")
    else:
        sub["mean_sum_bits"] = pd.to_numeric(sub["mean_sum_bits"], errors="coerce")
        sub["fitted_sum_bits"] = pd.to_numeric(sub["fitted_sum_bits"], errors="coerce")
        sub["residual"] = pd.to_numeric(sub["residual"], errors="coerce")
        sub["age_months"] = pd.to_numeric(sub["age_months"], errors="coerce")
        rows = []
        for estimator_label, group in sub.groupby("estimator_label", sort=False):
            rows.append(
                {
                    "estimator_label": estimator_label,
                    "r2": observed_fitted_r2(group["mean_sum_bits"], group["fitted_sum_bits"]),
                }
            )
        r2_frame = pd.DataFrame(rows).sort_values("r2", ascending=True)
        axes[0].barh(r2_frame["estimator_label"], r2_frame["r2"], color="#2f6f73")
        axes[0].set_xlabel("Observed-vs-fitted R2")
        axes[0].set_title("Calibration summary by estimator")
        axes[0].grid(color="#e5e7eb")
        for estimator_label, group in sub.groupby("estimator_label", sort=False):
            by_age = group.groupby(pd.cut(group["age_months"], bins=18), observed=True).agg(
                age_mid=("age_months", "mean"),
                residual=("residual", "mean"),
            )
            axes[1].plot(by_age["age_mid"], by_age["residual"], lw=2.0, label=estimator_label)
        axes[1].axhline(0, color="#111827", lw=1.0, linestyle=":")
        axes[1].set_xlabel("Age (months)")
        axes[1].set_ylabel("Mean observed - fitted")
        axes[1].set_title("Residual trend over age by estimator")
        axes[1].grid(color="#e5e7eb")
        axes[1].legend(fontsize=7, loc="best")
    fig.suptitle(f"{model_id}: estimator calibration and residual checks", y=1.02)
    plt.tight_layout()
    path = fig_dir / f"{model_id.lower()}_estimator_residual_calibration.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_estimator_diagnostic(fitted_values: pd.DataFrame, fig_dir: Path, *, model_id: str, estimator: EstimatorSpec) -> Path:
    sub = fitted_values[
        fitted_values["model_id"].eq(model_id)
        & fitted_values["estimator_id"].eq(estimator.estimator_id)
    ].copy()
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8))
    if sub.empty:
        for ax in axes:
            ax.text(0.5, 0.5, f"No fitted values for {model_id} / {estimator.label}", ha="center", va="center")
            ax.axis("off")
    else:
        for col in ["mean_sum_bits", "fitted_sum_bits", "residual", "age_months"]:
            sub[col] = pd.to_numeric(sub[col], errors="coerce")
        axes[0].scatter(sub["fitted_sum_bits"], sub["mean_sum_bits"], s=16, alpha=0.25, color="#475569")
        lo = float(np.nanmin([sub["fitted_sum_bits"].min(), sub["mean_sum_bits"].min()]))
        hi = float(np.nanmax([sub["fitted_sum_bits"].max(), sub["mean_sum_bits"].max()]))
        axes[0].plot([lo, hi], [lo, hi], color="#0f766e", lw=1.8, linestyle="--")
        axes[0].set_xlabel("Fitted mean sum_bits")
        axes[0].set_ylabel("Observed mean sum_bits")
        axes[0].set_title("Actual vs fitted")
        axes[0].grid(color="#e5e7eb")
        axes[1].scatter(sub["age_months"], sub["residual"], s=16, alpha=0.22, color="#64748b")
        by_age = sub.groupby(pd.cut(sub["age_months"], bins=16), observed=True).agg(
            age_mid=("age_months", "mean"),
            residual=("residual", "mean"),
        )
        axes[1].plot(by_age["age_mid"], by_age["residual"], color="#c2410c", lw=2.0)
        axes[1].axhline(0, color="#111827", lw=1.0, linestyle=":")
        axes[1].set_xlabel("Age (months)")
        axes[1].set_ylabel("Observed - fitted")
        axes[1].set_title("Residuals over age")
        axes[1].grid(color="#e5e7eb")
    fig.suptitle(f"{model_id}: {estimator.label}", y=1.02)
    plt.tight_layout()
    path = fig_dir / f"{model_id.lower()}_{estimator.estimator_id}_actual_residual_diagnostic.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_model_term_forest(summary: pd.DataFrame, fig_dir: Path, formula_def: CoreFormula) -> Path:
    terms = relevant_term_prefixes(formula_def)
    rows: list[dict[str, object]] = []
    sub = summary[summary["model_id"].eq(formula_def.model_id) & summary["status"].eq("fit")].copy()
    for item in sub.to_dict(orient="records"):
        for prefix in terms:
            coef = pd.to_numeric(pd.Series([item.get(f"{prefix}_coef")]), errors="coerce").iloc[0]
            if pd.isna(coef):
                continue
            label, _, _ = TERM_READS[prefix]
            rows.append(
                {
                    "term": label,
                    "estimator": item.get("estimator_label"),
                    "scale": item.get("effect_scale"),
                    "coef": coef,
                    "ci_low": pd.to_numeric(pd.Series([item.get(f"{prefix}_ci_low")]), errors="coerce").iloc[0],
                    "ci_high": pd.to_numeric(pd.Series([item.get(f"{prefix}_ci_high")]), errors="coerce").iloc[0],
                }
            )
    data = pd.DataFrame(rows)
    height = max(6.5, min(22, len(data) * 0.25))
    fig, axes = plt.subplots(1, 2, figsize=(18, height), sharey=True)
    if data.empty:
        for ax in axes:
            ax.text(0.5, 0.5, f"No term estimates for {formula_def.model_id}", ha="center", va="center")
            ax.axis("off")
    else:
        for ax, scale in zip(axes, ["additive bits", "log mean bits"]):
            panel = data[data["scale"].eq(scale)].copy()
            if panel.empty:
                ax.text(0.5, 0.5, f"No {scale} estimates", ha="center", va="center")
                ax.axis("off")
                continue
            panel["label"] = panel["term"] + " | " + panel["estimator"]
            panel = panel.sort_values(["term", "estimator"])
            y = np.arange(len(panel))
            ax.hlines(y, panel["ci_low"], panel["ci_high"], color="#94a3b8", lw=1.7)
            ax.scatter(panel["coef"], y, color="#0f766e", s=40)
            ax.axvline(0, color="#111827", linestyle=":", lw=1.0)
            ax.set_yticks(y)
            ax.set_yticklabels(panel["label"], fontsize=7)
            ax.set_xlabel("Coefficient")
            ax.set_title(scale)
            ax.grid(axis="x", color="#e5e7eb")
    fig.suptitle(f"{formula_def.model_id}: predictor relations across estimators", y=1.01)
    plt.tight_layout()
    path = fig_dir / f"{formula_def.model_id.lower()}_term_effect_forest.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def atlas_fixed_effort_path(model_id: str) -> Path:
    return REAL_FIG_DIR / f"real_k3_{model_id.lower()}_nb_words_fixed_effort_atlas.png"


SOURCE_ORDER = [
    ("real", "Real child utterances"),
    ("random", "Random matched-length baseline"),
    ("unigram", "Unigram baseline"),
    ("bigram", "Bigram baseline"),
    ("trigram", "Trigram baseline"),
    ("lstm_additive_k3_same_length", "LSTM k3 same-length baseline"),
    ("lstm_additive_k4_same_length", "LSTM k4 same-length baseline"),
    ("lstm_additive_k5_same_length", "LSTM k5 same-length baseline"),
]


FOCUSED_ATLAS_MODELS = [
    {
        "model_id": "M2",
        "label": "Base fixed-effort child model",
        "why": "Baseline candidate: asks the communicative-efficiency question directly by comparing conditional information at fixed child effort and stable child identity.",
        "test": "At the same child effort level, are older sessions lower or higher in conditional utterance information for the same child identities?",
    },
    {
        "model_id": "M3",
        "label": "Child effort interaction model",
        "why": "Tests the user's core interaction concern: older children generally produce longer utterances, so the model asks whether the age slope changes at different child-effort levels.",
        "test": "Does the age-information relation depend on the child utterance effort level?",
    },
    {
        "model_id": "M4a",
        "label": "Parent-context effort model",
        "why": "Closest existing row-level Atlas candidate to the simple formula `sum_bits ~ age + child effort + parent effort + child identity`; it adds preceding parent/caretaker effort while keeping the age-by-child-effort term already used in the Atlas ladder.",
        "test": "Does the age pattern remain after accounting for how much the parent/caretaker just said?",
    },
    {
        "model_id": "M4c",
        "label": "Question/form control model",
        "why": "Checks whether the fixed-effort age pattern is just a question/statement or prompt-form artifact.",
        "test": "Does the age effect survive broad context-form controls?",
    },
    {
        "model_id": "M5",
        "label": "Combined parent/context control model",
        "why": "Promising fuller candidate: keeps child effort, parent effort, context entropy, question type, and child identity in one row-level model.",
        "test": "Does the age pattern remain when the main parent-context and predictability controls are in the same model?",
    },
    {
        "model_id": "M6",
        "label": "Context entropy interaction model",
        "why": "Promising robustness candidate from M1-M15: lets the relation with context entropy vary by age and child effort while preserving lower-order predictors.",
        "test": "Is the age pattern robust when context predictability can interact with age and effort?",
    },
    {
        "model_id": "M7",
        "label": "Nonlinear age model",
        "why": "Checks whether development is being forced into one straight line.",
        "test": "Is the developmental pattern approximately linear, or does a curved age term matter?",
    },
    {
        "model_id": "M11",
        "label": "Age by parent-context effort model",
        "why": "Directly addresses whether children react differently to parent context effort as they age.",
        "test": "Does the parent-context-effort relation change with child age?",
    },
    {
        "model_id": "M15",
        "label": "Rich interaction stress test",
        "why": "Stress-test candidate, not the cleanest supervisor story: keeps the main age, child-effort, parent-effort, context-entropy, and context-form interactions together.",
        "test": "Does the fixed-effort age pattern survive the richest currently available row-level interaction model?",
    },
]

PARENT_REACTION_SENSITIVITY_MODELS = [
    {
        "model_id": "M5_no_question",
        "label": "Exact context-control model without question type",
        "formula": "sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)",
        "why": "Separates the parent/context controls from question type so question coding is not doing hidden work.",
    },
    {
        "model_id": "M5_age_effort_no_question",
        "label": "Age by child-effort interaction without question type",
        "formula": "sum_bits ~ age_c + effort_c + age_c:effort_c + context_entropy_c + parent_context_effort_c + C(child_id)",
        "why": "Tests whether child effort changes the age relation while excluding question type.",
    },
    {
        "model_id": "M5_parent_reaction_no_question",
        "label": "Parent-reaction interaction model without question type",
        "formula": "sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)",
        "why": "Directly tests whether parent context effort relates differently to child bits by age and by child effort.",
    },
    {
        "model_id": "M5_parent_reaction_question",
        "label": "Parent-reaction interaction model with question type",
        "formula": "sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(question_type) + C(child_id)",
        "why": "Same parent-reaction test, but with question/form controls added.",
    },
]


CARETAKER_ANALOG = {
    "M1": "CM1",
    "M2": "CM2",
    "M3": "CM3",
    "M4a": "CM4a",
    "M4c": "CM4c",
    "M5": "CM5",
    "M6": "CM6",
}


def source_fixed_effort_path(source_id: str, model_id: str) -> Path:
    return Path("figs/route1_source_specific_corrected_fixed_effort_atlas") / source_id / f"{source_id}_k3_{model_id.lower()}_nb_words_fixed_effort_atlas.png"


def aggregate_estimator_line_path(model_id: str) -> Path:
    return DEFAULT_FIG_DIR / f"{model_id.lower()}_aggregate_estimator_fixed_effort_age_lines.png"


def caretaker_fixed_effort_path(model_id: str) -> Path | None:
    caretaker_model = CARETAKER_ANALOG.get(model_id)
    if caretaker_model is None:
        return None
    return CARETAKER_FIG_DIR / f"caretaker_k3_{caretaker_model.lower()}_nb_words_fixed_effort_atlas.png"


def source_model_summary(source_id: str) -> pd.DataFrame:
    return read_csv_if_exists(SOURCE_ATLAS_DIR / source_id / "model_summary.csv")


def source_slope_summary(source_id: str, model_id: str) -> str:
    slopes = read_csv_if_exists(SOURCE_ATLAS_DIR / source_id / "fixed_slice_slopes.csv")
    if slopes.empty:
        return "No fixed-slice slope table found."
    sub = slopes[
        slopes["context_k"].eq("k3")
        & slopes["effort_col"].eq("nb_words")
        & slopes["model_id"].eq(model_id)
    ].copy()
    if sub.empty:
        return "No k3 word-effort fixed-slice slopes found."
    min_slope = pd.to_numeric(sub["slope_bits_per_month"], errors="coerce").min()
    max_slope = pd.to_numeric(sub["slope_bits_per_month"], errors="coerce").max()
    directions = ", ".join(sorted(set(sub["direction"].dropna().astype(str))))
    return f"{directions}; {min_slope:.3f} to {max_slope:.3f} bits/month"


def row_level_model_sentence(row_level_summary: pd.DataFrame, model_id: str) -> str:
    if row_level_summary.empty:
        return f"No row-level summary found for {model_id}."
    sub = row_level_summary[
        row_level_summary["model_id"].eq(model_id)
        & row_level_summary["context_k"].eq("k3")
        & row_level_summary["effort_col"].eq("nb_words")
        & row_level_summary["status"].eq("fit")
    ]
    if sub.empty:
        return f"No k3 word-effort row-level summary found for {model_id}."
    row = sub.iloc[0]
    return (
        f"`{display_formula(row.get('statsmodels_formula'))}`; age coefficient "
        f"{f_text(row.get('age_coef'), 4)} bits/month, p={p_text(row.get('age_p'))}; "
        f"observed-vs-fitted R2 {f_text(row.get('r2_observed_fitted'), 4)}."
    )


def age_robustness_sentence(model_id: str) -> str:
    observed = read_csv_if_exists(AGE_ROBUSTNESS_DIR / "age_scrambling_observed_model_summary.csv")
    robust = read_csv_if_exists(AGE_ROBUSTNESS_DIR / "age_scrambling_robustness_summary.csv")
    if observed.empty:
        return "No age-robustness summary found."
    obs = observed[
        observed["model_id"].eq(model_id)
        & observed["context_k"].eq("k3")
        & observed["effort_col"].eq("nb_words")
    ]
    if obs.empty:
        return f"No k3 word-effort age-robustness row found for {model_id}."
    coef = pd.to_numeric(obs.iloc[0].get("age_coef"), errors="coerce")
    pieces = [f"age-bin/unit robustness observed age coefficient {f_text(coef, 4)}"]
    if robust.empty:
        return "; ".join(pieces) + "."
    sub = robust[
        robust["model_id"].eq(model_id)
        & robust["context_k"].eq("k3")
        & robust["effort_col"].eq("nb_words")
    ].copy()
    if sub.empty:
        return "; ".join(pieces) + "."
    labels = {
        "balanced_bootstrap": "balanced bootstrap",
        "age_bin_group_scramble": "age-bin label scramble",
        "unit_age_scramble": "unit-age scramble",
        "within_child_age_scramble": "within-child age scramble",
    }
    for method in ["balanced_bootstrap", "age_bin_group_scramble", "unit_age_scramble", "within_child_age_scramble"]:
        row = sub[sub["robustness_method"].eq(method)]
        if row.empty:
            continue
        item = row.iloc[0]
        q025 = f_text(item.get("null_q025_age_coef"), 4)
        q500 = f_text(item.get("null_q500_age_coef"), 4)
        q975 = f_text(item.get("null_q975_age_coef"), 4)
        outside = "outside" if bool(item.get("observed_outside_null_95")) else "inside"
        p_value = p_text(item.get("two_sided_permutation_p"))
        p_part = f", p={p_value}" if p_value else ""
        pieces.append(f"{labels[method]} 95% interval [{q025}, {q975}], median {q500}; observed {outside}{p_part}")
    return "; ".join(pieces) + "."


def multiple_age_effect_lines(doc_path: Path, row_level_summary: pd.DataFrame, row_level_slopes: pd.DataFrame) -> list[str]:
    """Explain the pooled-vs-child-controlled contrast that motivated Route 1."""

    lines = [
        "## Multiple Age Effects Can Coexist",
        "",
        "The report keeps both effects visible because they answer different questions.",
        "",
        "- **Pooled effort-only question:** if we control child production effort but do not control child identity, what is the age trend across the pooled corpus?",
        "- **Child-controlled question:** within the repeated-measures design, after controlling stable child identity, what is the age trend at the same effort level?",
        "",
        "### Pooled Effort-Only Contrast",
        "",
        f"**M1 row-level Atlas.** {row_level_model_sentence(row_level_summary, 'M1')}",
        "",
        f"**M1 fixed-effort slope read.** {source_slope_summary('real', 'M1')}. In the row-level Atlas this is essentially flat/slightly upward, not the child-controlled decrease.",
        "",
        md_image(doc_path, source_fixed_effort_path("real", "M1"), "M1 pooled effort-only fixed-effort regression lines"),
        "",
        f"**M1 balanced/scrambled robustness read.** {age_robustness_sentence('M1')}",
        "",
        "**M1 within-child scramble note.** The within-child age-scramble null is even more positive than the observed M1 slope. That is exactly why M1 is treated as a pooled/compositional contrast, not as the within-child communicative-efficiency result.",
        "",
        md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "m1_clear_robustness_regression_lines.png", "M1 balanced and scrambled robustness lines"),
        "",
        "### Child-Controlled Contrast",
        "",
        f"**M2 row-level Atlas.** {row_level_model_sentence(row_level_summary, 'M2')}",
        "",
        f"**M2 fixed-effort slope read.** {source_slope_summary('real', 'M2')}.",
        "",
        md_image(doc_path, source_fixed_effort_path("real", "M2"), "M2 child-identity fixed-effort regression lines"),
        "",
        f"**M2 balanced/scrambled robustness read.** {age_robustness_sentence('M2')}",
        "",
        md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "m2_clear_robustness_regression_lines.png", "M2 balanced and scrambled robustness lines"),
        "",
        f"**M3 row-level Atlas.** {row_level_model_sentence(row_level_summary, 'M3')}",
        "",
        f"**M3 fixed-effort slope read.** {source_slope_summary('real', 'M3')}.",
        "",
        md_image(doc_path, source_fixed_effort_path("real", "M3"), "M3 age-by-effort fixed-effort regression lines"),
        "",
        md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "m3_clear_robustness_regression_lines.png", "M3 balanced and scrambled robustness lines"),
        "",
        "**Interpretation.** The pooled M1 effect is a real descriptive/compositional effect of the sampled corpus. The Route 1 efficiency claim is the child-controlled effect: at the same effort level, with child identity handled, the fixed-effort slopes go downward. Both belong in the model-selection report because they explain why controlling child identity changes the story.",
        "",
    ]
    return lines


def source_model_row(source_id: str, model_id: str) -> pd.Series:
    summary = source_model_summary(source_id)
    if summary.empty:
        return pd.Series(dtype=object)
    sub = summary[
        summary["model_id"].eq(model_id)
        & summary["context_k"].eq("k3")
        & summary["effort_col"].eq("nb_words")
        & summary["status"].eq("fit")
    ]
    if sub.empty:
        return pd.Series(dtype=object)
    return sub.iloc[0]


def source_comparison_table(model_id: str) -> pd.DataFrame:
    rows = []
    for source_id, source_label in SOURCE_ORDER:
        row = source_model_row(source_id, model_id)
        fig = source_fixed_effort_path(source_id, model_id)
        rows.append(
            {
                "source": source_label,
                "status": "fit" if not row.empty else "missing fit",
                "age_coef": f_text(row.get("age_coef"), 3) if not row.empty else "",
                "age_p": p_text(row.get("age_p")) if not row.empty else "",
                "fixed_effort_slopes": source_slope_summary(source_id, model_id),
                "plot": "available" if fig.exists() else "missing",
            }
        )
    return pd.DataFrame(rows)


def estimator_coverage_for_model(model_id: str) -> pd.DataFrame:
    sensitivity = read_csv_if_exists(CHILD_STRUCTURE_DIR / "source_specific_model_summary.csv")
    if sensitivity.empty:
        return pd.DataFrame()
    sub = sensitivity[
        sensitivity["model_id"].eq(model_id)
        & sensitivity["target_source"].eq("real")
        & sensitivity["context_k"].eq("k3")
        & sensitivity["effort_col"].eq("nb_words")
    ].copy()
    if sub.empty:
        return pd.DataFrame()
    keep = sub[
        [
            "child_structure",
            "estimator",
            "covariance",
            "random_effects",
            "status",
            "r2",
            "aic",
            "bic",
        ]
    ].copy()
    for col in ["r2", "aic", "bic"]:
        keep[col] = pd.to_numeric(keep[col], errors="coerce").map(lambda x: "" if pd.isna(x) else f"{x:.4g}")
    return keep


def formula_rows_for_report(row_level_summary: pd.DataFrame) -> list[tuple[str, str]]:
    focused_ids = [item["model_id"] for item in FOCUSED_ATLAS_MODELS]
    fallback_labels = {item["model_id"]: item["label"] for item in FOCUSED_ATLAS_MODELS}
    if row_level_summary.empty:
        return [(model_id, fallback_labels[model_id]) for model_id in focused_ids]
    sub = row_level_summary[
        row_level_summary["context_k"].eq("k3")
        & row_level_summary["effort_col"].eq("nb_words")
        & row_level_summary["status"].eq("fit")
        & row_level_summary["model_id"].isin(focused_ids)
    ].copy()
    order = focused_ids
    sub["model_id"] = pd.Categorical(sub["model_id"], categories=order, ordered=True)
    sub = sub.sort_values("model_id").drop_duplicates("model_id")
    found = {str(row.model_id): str(row.model_label) for row in sub.itertuples()}
    return [(model_id, found.get(model_id, fallback_labels[model_id])) for model_id in focused_ids]


def focused_model_info(model_id: str) -> Mapping[str, str]:
    for item in FOCUSED_ATLAS_MODELS:
        if item["model_id"] == model_id:
            return item
    return {"model_id": model_id, "label": model_id, "why": "", "test": ""}


def short_estimator_coverage_sentence(model_id: str) -> str:
    table = estimator_coverage_for_model(model_id)
    if table.empty:
        return (
            "No row-level all-estimator sensitivity table is currently available for this candidate. "
            "The fixed-effort source plots shown here are the OLS child-fixed-effect Atlas view."
        )
    parts = []
    for row in table.itertuples(index=False):
        desc = str(row.estimator)
        cov = str(row.covariance)
        random_effects = str(row.random_effects)
        if random_effects and random_effects != "nan":
            desc = f"{desc} random effects {random_effects}"
        elif cov and cov != "nan":
            desc = f"{desc} {cov}"
        parts.append(f"{row.child_structure}: {desc} ({row.status})")
    return "Row-level repeated-measures sensitivity available: " + "; ".join(parts) + "."


def source_plot_lines(doc_path: Path, model_id: str) -> list[str]:
    lines: list[str] = []
    for source_id, source_label in SOURCE_ORDER:
        if source_id == "real":
            continue
        fig = source_fixed_effort_path(source_id, model_id)
        if not fig.exists():
            continue
        lines.extend(
            [
                f"#### {source_label}",
                "",
                md_image(doc_path, fig, f"{model_id} {source_label} fixed-effort regression lines"),
                "",
                f"**Line read.** {source_slope_summary(source_id, model_id)}",
                "",
            ]
        )
    return lines


def aggregate_screening_plot_lines(doc_path: Path, model_id: str) -> list[str]:
    lines: list[str] = []
    line_fig = aggregate_estimator_line_path(model_id)
    if line_fig.exists():
        lines.extend(
            [
                "### All-Estimator Screening Lines",
                "",
                md_image(doc_path, line_fig, f"{model_id} all-estimator fixed-effort screening lines"),
                "",
                (
                    "**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, "
                    "GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, "
                    "and MixedLM random age slope on the same candidate formula. It is a "
                    "fixed-effort screening/robustness plot for repeated utterance measurements, "
                    "not a raw total-bits growth plot and not a replacement for the row-level "
                    "source-specific Atlas line above."
                ),
                "",
            ]
        )
    return lines


def existing_figure(path: Path) -> Path:
    return path


def build_plot_manifest(generated: Mapping[str, Path], output_dir: Path) -> pd.DataFrame:
    rows = [
        ("fixed_effort_m2", "Fixed-effort age lines for M2", REAL_FIG_DIR / "real_k3_m2_nb_words_fixed_effort_atlas.png", "existing Atlas v2"),
        ("fixed_effort_m3", "Fixed-effort age lines for M3", REAL_FIG_DIR / "real_k3_m3_nb_words_fixed_effort_atlas.png", "existing Atlas v2"),
        ("fixed_effort_m4c", "Fixed-effort age lines for M4c", REAL_FIG_DIR / "real_k3_m4c_nb_words_fixed_effort_atlas.png", "existing Atlas v2"),
        ("fixed_effort_m5", "Fixed-effort age lines for M5", REAL_FIG_DIR / "real_k3_m5_nb_words_fixed_effort_atlas.png", "existing Atlas v2"),
        ("fixed_effort_m15", "Fixed-effort age lines for M15/rich", REAL_FIG_DIR / "real_k3_m15_nb_words_fixed_effort_atlas.png", "existing Atlas v2"),
        ("nonlinear_m7", "Nonlinear age fixed-effort check", REAL_FIG_DIR / "real_k3_m7_nb_words_fixed_effort_atlas.png", "existing Atlas v2"),
        ("estimator_m2", "Same question across estimator families for M2", generated["M2_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m3", "Age-by-effort model across estimator families", generated["M3_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m4c", "Question/form model across estimator families", generated["M4c_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m5_no_question", "Same context-control question without question type across estimator families", generated["M5_no_question_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m5", "Same question across estimator families for M5", generated["M5_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m5_age_effort_no_question", "Age-by-effort context-control model without question type across estimator families", generated["M5_age_effort_no_question_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m5_age_effort_question", "Age-by-effort context-control model with question type across estimator families", generated["M5_age_effort_question_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m5_parent_reaction_no_question", "Parent-context reaction model without question type across estimator families", generated["M5_parent_reaction_no_question_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m5_parent_reaction_question", "Parent-context reaction model with question type across estimator families", generated["M5_parent_reaction_question_estimator_lines"], "new estimator-sensitivity package"),
        ("estimator_m15", "Rich context-interaction stress test across estimator families", generated["M15_estimator_lines"], "new estimator-sensitivity package"),
        ("forest", "Coefficient/effect-size forest plot", generated["age_forest"], "new aggregate package"),
        ("delta_r2", "Variable-importance / nested delta-R2 plot", generated["nested_r2"], "new aggregate package"),
        ("actual_vs_predicted", "Actual aggregate line vs model-predicted line", generated["actual_vs_predicted"], "new aggregate package"),
        ("actual_vs_predicted_age_effort", "Actual aggregate line vs age-by-effort model prediction", generated["actual_vs_predicted_age_effort"], "new aggregate package"),
        ("actual_vs_predicted_parent_reaction", "Actual aggregate line vs parent-context reaction model prediction", generated["actual_vs_predicted_parent_reaction"], "new aggregate package"),
        ("heldout_lines", "Heldout actual-vs-predicted trajectory plots", SUPERVISOR_FIG_DIR / "heldout_pop_m4c_actual_vs_predicted_regression_lines.png", "existing heldout report"),
        ("heldout_calibration", "Heldout calibration and residual-over-age plots", SUPERVISOR_FIG_DIR / "heldout_pop_m4c_calibration_residuals.png", "existing heldout report"),
        ("age_scrambling", "Age-scrambling/null robustness plot", AGE_ROBUSTNESS_FIG_DIR / "m2_clear_robustness_regression_lines.png", "existing robustness report"),
        ("age_scrambling_heatmap", "Age-scrambling/null robustness heatmap", AGE_ROBUSTNESS_FIG_DIR / "robustness_outside_null_heatmap.png", "existing robustness report"),
        ("source_comparison", "Source comparison real/random/ngram/LSTM", SUPERVISOR_FIG_DIR / "source_comparison_m4c_k3_words_slopes.png", "existing supervisor candidate report"),
        ("caretaker_contrast_cm2", "Caretaker contrast plot CM2", CARETAKER_FIG_DIR / "caretaker_k3_cm2_nb_words_fixed_effort_atlas.png", "existing caretaker atlas"),
        ("caretaker_contrast_cm6", "Caretaker contrast plot CM6", CARETAKER_FIG_DIR / "caretaker_k3_cm6_nb_words_fixed_effort_atlas.png", "existing caretaker atlas"),
    ]
    seen = {plot_id for plot_id, _, _, _ in rows}
    for plot_id, path in sorted(generated.items()):
        if plot_id in seen:
            continue
        rows.append((plot_id, f"Generated model diagnostic: {plot_id}", path, "new estimator-sensitivity package"))
    frame = pd.DataFrame(
        [
            {
                "plot_id": plot_id,
                "requirement": requirement,
                "status": "available" if path.exists() else "missing",
                "path": str(path),
                "source": source,
            }
            for plot_id, requirement, path, source in rows
        ]
    )
    frame.to_csv(output_dir / "required_plot_manifest.csv", index=False)
    return frame


def md_image(report_path: Path, figure: Path, alt: str) -> str:
    if not figure.exists():
        return f"_Missing figure: `{figure}`_"
    return f"![{alt}]({relative_to_report(report_path, figure)})"


def md_link(report_path: Path, path: Path, label: str | None = None) -> str:
    return f"[{label or path.name}]({relative_to_report(report_path, path)})"


def scientific_formula(formula: str) -> str:
    """Convert aggregate implementation formulas to the utterance-level question."""

    return formula.replace("mean_sum_bits", "sum_bits")


def atlas_model_id_for(formula_def: CoreFormula) -> str | None:
    mapping = {
        "M2": "M2",
        "M3": "M3",
        "M4c": "M4c",
        "M5": "M5",
        "M15": "M15",
        "M7": "M7",
    }
    return mapping.get(formula_def.model_id)


def display_formula(formula: object) -> str:
    text = str(formula)
    replacements = {
        "age_c * effort_c": "age_c + effort_c + age_c:effort_c",
        "C(age_bin) * effort_c": "C(age_bin) + effort_c + C(age_bin):effort_c",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def row_level_atlas_result(row_level_summary: pd.DataFrame, formula_def: CoreFormula) -> pd.Series:
    atlas_id = atlas_model_id_for(formula_def)
    if atlas_id is None or row_level_summary.empty:
        return pd.Series(dtype=object)
    sub = row_level_summary[
        row_level_summary["model_id"].eq(atlas_id)
        & row_level_summary["context_k"].eq("k3")
        & row_level_summary["effort_col"].eq("nb_words")
        & row_level_summary["status"].eq("fit")
    ]
    if sub.empty:
        return pd.Series(dtype=object)
    return sub.iloc[0]


def row_level_slope_summary(row_level_slopes: pd.DataFrame, formula_def: CoreFormula) -> str:
    atlas_id = atlas_model_id_for(formula_def)
    if atlas_id is None or row_level_slopes.empty:
        return "No exact row-level fixed-effort Atlas slope is available for this newly requested formula variant yet."
    sub = row_level_slopes[
        row_level_slopes["model_id"].eq(atlas_id)
        & row_level_slopes["context_k"].eq("k3")
        & row_level_slopes["effort_col"].eq("nb_words")
    ].copy()
    if sub.empty:
        return "No exact row-level fixed-effort Atlas slope is available for this formula."
    min_slope = pd.to_numeric(sub["slope_bits_per_month"], errors="coerce").min()
    max_slope = pd.to_numeric(sub["slope_bits_per_month"], errors="coerce").max()
    directions = ", ".join(sorted(set(sub["direction"].dropna().astype(str))))
    return (
        f"Existing row-level Atlas fixed-effort slopes are {directions}: "
        f"{min_slope:.3f} to {max_slope:.3f} bits/month across the fixed word-effort values."
    )


def row_level_result_sentence(row_level_summary: pd.DataFrame, row_level_slopes: pd.DataFrame, formula_def: CoreFormula) -> str:
    row = row_level_atlas_result(row_level_summary, formula_def)
    slope_text = row_level_slope_summary(row_level_slopes, formula_def)
    if row.empty:
        return (
            "This exact newly requested formula is not yet part of the row-level Atlas. "
            f"{slope_text} Treat the aggregate estimator-family plots below as exploratory robustness only until this exact formula is fit row-level."
        )
    return (
        "Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. "
        f"The age coefficient is {f_text(row.get('age_coef'), 3)} bits/month "
        f"(p={p_text(row.get('age_p'))}) after the listed controls. {slope_text}"
    )


def render_pdf_report(html_path: Path, pdf_path: Path) -> bool:
    """Render an HTML report to PDF using a local Chromium/Brave binary."""

    browser = shutil.which("brave-browser") or shutil.which("google-chrome") or shutil.which("chromium")
    if not browser:
        return False
    if pdf_path.exists():
        pdf_path.unlink()
    try:
        subprocess.run(
            [
                browser,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                f"--print-to-pdf={pdf_path.resolve()}",
                f"file://{html_path.resolve()}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        return False
    return pdf_path.exists()


def format_summary_table(summary: pd.DataFrame) -> pd.DataFrame:
    keep = summary[summary["model_id"].isin(CORE_MODEL_ORDER)].copy()
    keep = keep[
        [
            "model_id",
            "estimator_label",
            "effect_scale",
            "status",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
            "warning",
            "error",
        ]
    ].copy()
    for col in ["r2_observed_fitted", "age_coef", "age_p", "effort_coef", "effort_p"]:
        keep[col] = pd.to_numeric(keep[col], errors="coerce").map(lambda x: "" if pd.isna(x) else f"{x:.4g}")
    return keep


def format_relation_table(relation_summary: pd.DataFrame, *, estimator_label: str | None = None) -> pd.DataFrame:
    keep = relation_summary.copy()
    if estimator_label is not None and not keep.empty:
        keep = keep[keep["estimator_label"].eq(estimator_label)].copy()
    cols = [
        "model_id",
        "estimator_label",
        "effect_scale",
        "term",
        "coefficient",
        "p_value",
        "relation_to_sum_bits",
    ]
    keep = keep[[col for col in cols if col in keep.columns]].copy()
    for col in ["coefficient", "p_value"]:
        if col in keep.columns:
            keep[col] = pd.to_numeric(keep[col], errors="coerce").map(lambda x: "" if pd.isna(x) else f"{x:.4g}")
    return keep


def p_text(value: object) -> str:
    val = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(val):
        return ""
    if val < 0.001:
        return "<.001"
    return f"{val:.3f}"


def f_text(value: object, digits: int = 3) -> str:
    val = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(val):
        return ""
    return f"{val:.{digits}f}"


def one_line_effect_sentences(summary: pd.DataFrame) -> pd.DataFrame:
    """Return literal interpretation sentences for promoted plot families."""

    fitted = summary[summary["status"].eq("fit")].copy()

    def row(model_id: str, estimator_id: str = "ols_fe_cluster") -> pd.Series:
        sub = fitted[fitted["model_id"].eq(model_id) & fitted["estimator_id"].eq(estimator_id)]
        if sub.empty:
            return pd.Series(dtype=object)
        return sub.iloc[0]

    m3 = row("M3")
    m4c = row("M4c")
    m5 = row("M5")
    return pd.DataFrame(
        [
            {
                "effect": "Age down arrow",
                "sentence": (
                    "In the promoted aggregate M5 OLS fixed-effect check, older age predicts lower "
                    f"`sum_bits` at fixed effort and context controls ({f_text(m5.get('age_coef'), 3)} bits/month, p={p_text(m5.get('age_p'))})."
                ),
            },
            {
                "effect": "Effort up arrow",
                "sentence": (
                    "In the same M5 check, longer utterances predict higher total information "
                    f"({f_text(m5.get('effort_coef'), 3)} bits per extra word-equivalent, p={p_text(m5.get('effort_p'))})."
                ),
            },
            {
                "effect": "Age x effort",
                "sentence": (
                    "The M3 interaction check asks whether the age slope changes by effort; its aggregate OLS fixed-effect "
                    f"age-by-effort term is {f_text(m3.get('age_effort_coef'), 4)} (p={p_text(m3.get('age_effort_p'))})."
                ),
            },
            {
                "effect": "Context entropy",
                "sentence": (
                    "In M5, context entropy is included as a predictability control; its aggregate OLS fixed-effect "
                    f"coefficient is {f_text(m5.get('context_entropy_coef'), 3)} (p={p_text(m5.get('context_entropy_p'))})."
                ),
            },
            {
                "effect": "Question type",
                "sentence": (
                    "The M4c question/form model keeps the age term in the model after broad context-form controls; "
                    f"the aggregate OLS fixed-effect age coefficient is {f_text(m4c.get('age_coef'), 3)} (p={p_text(m4c.get('age_p'))})."
                ),
            },
            {
                "effect": "Caretaker contrast",
                "sentence": (
                    "The caretaker plots ask the analogous fixed-effort question for adult/caretaker speech; they are used as a contrast "
                    "to test whether the child-age pattern appears automatically in adult speech from the same sessions."
                ),
            },
            {
                "effect": "Heldout prediction",
                "sentence": (
                    "The heldout panels put actual unseen-child regression lines and PBM-trained predicted lines in the same cells, "
                    "so generalization is judged by trajectory shape rather than by an in-sample child fixed effect."
                ),
            },
        ]
    )


TERM_READS = {
    "age": ("Age at session", "age_c", "older session age"),
    "effort": ("Child utterance effort", "effort_c", "more child production effort"),
    "age_effort": ("Age x child effort", "age_c:effort_c", "the child-effort slope changing with age"),
    "context_entropy": ("Context entropy", "context_entropy_c", "a less predictable prior context"),
    "parent_context_effort": ("Parent context effort", "parent_context_effort_c", "more parent/caretaker effort in the prior context"),
    "age_context_entropy": ("Age x context entropy", "age_c:context_entropy_c", "the context-entropy relation changing with age"),
    "effort_context_entropy": ("Child effort x context entropy", "effort_c:context_entropy_c", "the context-entropy relation changing with child effort"),
    "age_parent_context_effort": (
        "Age x parent context effort",
        "age_c:parent_context_effort_c",
        "the parent-context-effort relation changing with age",
    ),
    "effort_parent_context_effort": (
        "Child effort x parent context effort",
        "effort_c:parent_context_effort_c",
        "the parent-context-effort relation changing with child effort",
    ),
    "parent_context_entropy": (
        "Parent context effort x context entropy",
        "parent_context_effort_c:context_entropy_c",
        "the parent-effort relation changing with context entropy",
    ),
}


def relevant_term_prefixes(formula_def: CoreFormula) -> list[str]:
    formula = formula_def.fe_formula
    prefixes = ["age", "effort"]
    checks = [
        ("age_c:effort_c", "age_effort"),
        ("context_entropy_c", "context_entropy"),
        ("parent_context_effort_c", "parent_context_effort"),
        ("age_c:context_entropy_c", "age_context_entropy"),
        ("effort_c:context_entropy_c", "effort_context_entropy"),
        ("age_c:parent_context_effort_c", "age_parent_context_effort"),
        ("effort_c:parent_context_effort_c", "effort_parent_context_effort"),
        ("parent_context_effort_c:context_entropy_c", "parent_context_entropy"),
    ]
    for token, prefix in checks:
        if token in formula and prefix not in prefixes:
            prefixes.append(prefix)
    return prefixes


def formula_control_sentence(formula_def: CoreFormula) -> str:
    controls = ["child identity", "child utterance effort", "age at session"]
    if formula_def.needs_context_entropy:
        controls.append("context entropy")
    if formula_def.needs_parent_context_effort:
        controls.append("parent/caretaker context effort")
    if formula_def.needs_question_type:
        controls.append("question/form type")
    if formula_def.includes_interaction:
        controls.append("the listed interaction terms, with all lower-order predictors written explicitly")
    return ", ".join(controls)


def estimator_formula_for(formula_def: CoreFormula, estimator: EstimatorSpec) -> str:
    return formula_def.fe_formula if estimator.uses_child_fixed_effects else formula_def.population_formula


def estimator_result_row(summary: pd.DataFrame, model_id: str, estimator_id: str) -> pd.Series:
    sub = summary[summary["model_id"].eq(model_id) & summary["estimator_id"].eq(estimator_id)]
    if sub.empty:
        return pd.Series(dtype=object)
    return sub.iloc[0]


def term_result_sentence(row: pd.Series, prefix: str) -> str:
    label, term, meaning = TERM_READS[prefix]
    coef = row.get(f"{prefix}_coef")
    p_value = row.get(f"{prefix}_p")
    relation = relation_text(coef, row.get("effect_scale"))
    if not relation:
        return f"- **{label}.** `{term}` was not estimated in this formula."
    return (
        f"- **{label}.** `{term}` estimates {meaning}; coefficient "
        f"{f_text(coef, 4)}, p={p_text(p_value)}. In this estimator, that is "
        f"{relation}."
    )


def formula_deep_dive_lines(
    formula_def: CoreFormula,
    summary: pd.DataFrame,
    generated: Mapping[str, Path],
    doc_path: Path,
    row_level_summary: pd.DataFrame,
    row_level_slopes: pd.DataFrame,
    *,
    base_r2: float,
) -> list[str]:
    ols = estimator_result_row(summary, formula_def.model_id, "ols_fe_cluster")
    model_r2 = pd.to_numeric(pd.Series([ols.get("r2_observed_fitted")]), errors="coerce").iloc[0]
    delta_r2 = model_r2 - base_r2 if pd.notna(model_r2) and math.isfinite(base_r2) else math.nan
    lines = [
        f"## {formula_def.model_id}. {formula_def.label}",
        "",
        f"**Natural-language test.** {formula_def.question}",
        "",
        f"**Controls in plain language.** This model adjusts for {formula_control_sentence(formula_def)}.",
        "",
        "**Primary scientific formula, child-fixed-effect version.**",
        "",
        f"`{scientific_formula(formula_def.fe_formula)}`",
        "",
        "**Primary scientific formula, population/random-effect version.**",
        "",
        f"`{scientific_formula(formula_def.population_formula)}`",
        "",
        f"**Primary row-level fixed-effort answer.** {row_level_result_sentence(row_level_summary, row_level_slopes, formula_def)}",
        "",
        "**Interaction note.** Age and effort being correlated is not by itself an interaction. An interaction term asks whether the slope for one predictor changes at different values of the other predictor.",
        "",
        (
            "**Variable-importance read.** The OLS child-fixed-effect observed-vs-fitted R2 is "
            f"{f_text(model_r2, 4)}; the delta versus M2 is {f_text(delta_r2, 4)}. "
            "This is a fit diagnostic, not causal importance."
        ),
        "",
    ]
    atlas_figure = atlas_fixed_effort_path(formula_def.model_id)
    if atlas_figure.exists():
        lines.extend(
            [
                md_image(doc_path, atlas_figure, f"{formula_def.model_id} row-level Atlas fixed-effort lines"),
                "",
                "**Atlas plot read.** This is the primary row-level fixed-effort regression plot: utterance-level `sum_bits` is predicted at fixed child effort, with the listed controls. This is the plot to use for the core developmental claim.",
                "",
            ]
        )
    figure = generated.get(f"{formula_def.model_id}_estimator_lines")
    if figure is not None:
        lines.extend(
            [
                md_image(doc_path, figure, f"{formula_def.model_id} estimator-family fixed-effort lines"),
                "",
                "**Aggregate estimator-sensitivity read.** This plot is not the primary Atlas result. It uses child-session/effort-band cells with outcome `mean_sum_bits`, meaning the average total bits per utterance inside a cell. It is a pseudo-replication robustness check, and an upward aggregate line does not overturn the row-level fixed-effort `sum_bits` result above.",
                "",
            ]
        )
    actual_figure = generated.get(f"{formula_def.model_id}_actual_vs_predicted")
    if actual_figure is not None:
        lines.extend(
            [
                md_image(doc_path, actual_figure, f"{formula_def.model_id} actual-vs-predicted regression plot"),
                "",
                "**Actual-vs-predicted read.** Grey points are observed child-session/effort cells; the black line is the observed trend; the dashed line is the model prediction at fixed effort/context.",
                "",
            ]
        )
    residual_figure = generated.get(f"{formula_def.model_id}_residual_calibration")
    if residual_figure is not None:
        lines.extend(
            [
                md_image(doc_path, residual_figure, f"{formula_def.model_id} estimator residual and calibration plot"),
                "",
                "**Residual/calibration read.** The left panel compares observed-vs-fitted fit across estimators; the right panel checks whether residuals drift with age.",
                "",
            ]
        )
    term_figure = generated.get(f"{formula_def.model_id}_term_forest")
    if term_figure is not None:
        lines.extend(
            [
                md_image(doc_path, term_figure, f"{formula_def.model_id} term-effect forest plot"),
                "",
                "**Predictor-relation read.** This shows how age, child effort, context entropy, parent context effort, and interaction terms relate to `sum_bits` across estimator families.",
                "",
            ]
        )
    for estimator in ESTIMATOR_SPECS:
        row = estimator_result_row(summary, formula_def.model_id, estimator.estimator_id)
        lines.extend(
            [
                f"### {formula_def.model_id} - {estimator.label}",
                "",
                f"**What this estimator tests.** Same scientific formula, with dependence handled as: {estimator.dependence}.",
                "",
                f"**Scientific formula.** `{scientific_formula(estimator_formula_for(formula_def, estimator))}`",
                "",
                f"**Aggregate sensitivity implementation.** `{estimator_formula_for(formula_def, estimator)}`. This uses `mean_sum_bits` only for the child-session/effort-band robustness fit; it is not the main total-bits outcome.",
                "",
            ]
        )
        estimator_diag = generated.get(f"{formula_def.model_id}_{estimator.estimator_id}_diagnostic")
        if estimator_diag is not None:
            lines.extend(
                [
                    md_image(doc_path, estimator_diag, f"{formula_def.model_id} {estimator.label} diagnostic"),
                    "",
                    "**Estimator diagnostic read.** The left panel checks actual-vs-fitted calibration for this estimator; the right panel checks whether this estimator leaves age-structured residuals.",
                    "",
                ]
            )
        if row.empty or row.get("status") != "fit":
            lines.extend(
                [
                    f"**Status.** Not fit. {row.get('error', '') if not row.empty else ''}",
                    "",
                ]
            )
            continue
        lines.extend(
            [
                (
                    f"**Fit status.** Fit on {int(row.get('n_obs', 0)):,} model rows from "
                    f"{int(row.get('n_children', 0)):,} children; coefficient scale: {row.get('effect_scale')}."
                ),
                "",
                "**Relation between predictors and `sum_bits`.**",
                "",
            ]
        )
        for prefix in relevant_term_prefixes(formula_def):
            lines.append(term_result_sentence(row, prefix))
        warning = str(row.get("warning", "") or "")
        if warning:
            lines.extend(["", f"**Estimator caution.** {warning[:500]}"])
        lines.append("")
    return lines


def write_report(
    *,
    doc_path: Path,
    output_dir: Path,
    generated: Mapping[str, Path],
    artifact_audit: pd.DataFrame,
    coverage: pd.DataFrame,
    plot_manifest: pd.DataFrame,
    summary: pd.DataFrame,
    relation_summary: pd.DataFrame,
    row_level_summary: pd.DataFrame,
    row_level_slopes: pd.DataFrame,
) -> None:
    real_atlas = Path("docs/utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html")
    source_index = Path("docs/utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.html")
    heldout_report = Path("docs/utterance_information_route1_heldout_real_child_prediction_report.html")
    caretaker_report = Path("docs/utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html")
    age_report = Path("docs/utterance_information_age_scrambling_robustness.html")

    lines: list[str] = [
        "# Route 1 Focused Candidate Regression-Line Gallery",
        "",
        "This is a pre-supervisor evidence gallery for choosing the strongest Route 1 figures. It is intentionally plot-first and candidate-focused, not a dump of every M1-M15 Atlas section.",
        "",
        "The report keeps the scientific target fixed: estimate conditional utterance information at fixed production effort from repeated utterances sampled from the same children across sessions and ages.",
        "",
        "## Scope Lock",
        "",
        "- Main Route 1 estimand: age-related change in `sum_bits` after conditioning on child production effort and other controls.",
        "- This is communicative efficiency, not MLU. Raw total bits can increase with age simply because children say longer utterances.",
        "- Main effort control: child production effort, shown here with the word-count effort axis already used in the fixed-effort Atlas.",
        "- Parent/caretaker effort means the amount of preceding caretaker context production.",
        "- Child identity matters because the same children are observed repeatedly across sessions; child fixed effects or child-level random effects are used to avoid treating children as interchangeable single rows.",
        "- Tables are kept minimal. The central evidence objects are regression/fixed-effort age lines.",
        "- Bits per token, such as `mean_bits_per_token` or `sum_bits / nb_words`, is a secondary rate outcome and is not the same question as conditional total bits at fixed effort.",
        "- Raw observed-vs-fitted total-bit diagnostics are not promoted here because they mostly show the mechanical relation between length and total bits.",
        "- Whenever an interaction appears below, the lower-level predictors are written explicitly.",
        "",
        "## Estimator Rationale",
        "",
        "- **OLS + child fixed effects + clustered SE:** main Atlas-compatible view; controls stable child identity and clusters uncertainty by child.",
        "- **GEE Gaussian by child:** population-average repeated-measures check for a continuous bits outcome.",
        "- **GEE Gamma/log by child:** robustness check for positive, skewed bit outcomes; interpret through prediction lines rather than raw coefficient scale.",
        "- **GLM Gaussian and GLM Gamma/log:** distribution/link sensitivity checks where feasible.",
        "- **MixedLM random child intercept:** lets each child have a different baseline information level.",
        "- **MixedLM random child age slope:** lets each child have a different developmental trajectory; convergence warnings matter.",
        "- **Month/session aggregation:** useful only as robustness against pseudo-replication, not as the main row-level result.",
        "",
        "## Candidate Formula Family",
        "",
        "The focused parent-effort family requested for model selection is about conditional information, not raw length growth:",
        "",
        "```text",
        "sum_bits ~ age_c + effort_c + C(child_id)",
        "sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)",
        "sum_bits ~ age_c + effort_c + age_c:effort_c + parent_context_effort_c + C(child_id)",
        "sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)",
        "sum_bits ~ age_c + effort_c + parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)",
        "sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)",
        "```",
        "",
        "Existing promising Atlas candidates are used when they match this logic or answer an adjacent necessary control question: M2, M3, M4a, M4c, M5, M6, M7, M11, and M15.",
        "",
        "## Source Reports Used",
        "",
        f"- Real-child Atlas v2: {md_link(doc_path, real_atlas)}",
        f"- Source-specific Atlas v2 index: {md_link(doc_path, source_index)}",
        f"- Heldout prediction report: {md_link(doc_path, heldout_report)}",
        f"- Age-scrambling robustness report: {md_link(doc_path, age_report)}",
        f"- Caretaker Atlas v2: {md_link(doc_path, caretaker_report)}",
        "",
        "## Reading Rule",
        "",
        "Each fixed-effort line is a row-level model prediction for utterance `sum_bits` at a fixed child-effort or caretaker-effort value. Read the slope as conditional information at the same effort level; do not read it as children simply producing longer utterances.",
        "",
    ]
    lines.extend(multiple_age_effect_lines(doc_path, row_level_summary, row_level_slopes))
    for model_id, label in formula_rows_for_report(row_level_summary):
        info = focused_model_info(model_id)
        fake_formula = CoreFormula(model_id=model_id, label=label, question="", fe_formula="", population_formula="")
        row = row_level_atlas_result(row_level_summary, fake_formula)
        lines.extend(
            [
                f"## {model_id}. {info.get('label', label)}",
                "",
                f"**Why this candidate is here.** {info.get('why', '')}",
                "",
                f"**Natural-language test.** {info.get('test', '')}",
                "",
            ]
        )
        if not row.empty:
            lines.extend(
                [
                    f"**Row-level formula.** `{display_formula(row.get('statsmodels_formula'))}`",
                    "",
                    row_level_result_sentence(row_level_summary, row_level_slopes, fake_formula),
                    "",
                ]
            )
        lines.extend(
            [
                "### Real Child Regression Lines",
                "",
                md_image(doc_path, source_fixed_effort_path("real", model_id), f"{model_id} real child fixed-effort regression lines"),
                "",
                f"**Real-child read.** {source_slope_summary('real', model_id)} This is the main child-language plot for this candidate.",
                "",
                "### Generated Baseline Regression Lines",
                "",
            ]
        )
        lines.extend(source_plot_lines(doc_path, model_id))
        caretaker_fig = caretaker_fixed_effort_path(model_id)
        if caretaker_fig is not None and caretaker_fig.exists():
            lines.extend(
                [
                    "### Caretaker Contrast Regression Lines",
                    "",
                    md_image(doc_path, caretaker_fig, f"{model_id} caretaker contrast fixed-effort regression lines"),
                    "",
                    "**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.",
                    "",
                ]
            )
        lines.extend(["### Repeated-Measurement Estimator Checks", "", short_estimator_coverage_sentence(model_id), ""])
        lines.extend(aggregate_screening_plot_lines(doc_path, model_id))

    lines.extend(["## Exact Parent-Effort Interaction Screening", ""])
    for item in PARENT_REACTION_SENSITIVITY_MODELS:
        lines.extend(
            [
                f"## {item['model_id']}. {item['label']}",
                "",
                f"**Why this candidate is here.** {item['why']}",
                "",
                f"**Formula.** `{item['formula']}`",
                "",
                "**Status.** These are all-estimator screening artifacts for the requested parent-effort variants. They are useful for model choice, but the row-level source-specific Atlas should be regenerated for any variant promoted to the supervisor report.",
                "",
            ]
        )
        lines.extend(aggregate_screening_plot_lines(doc_path, item["model_id"]))

    lines.extend(
        [
            "## Heldout Prediction",
            "",
            "These are the prediction plots that matter here: actual heldout child regression lines and PBM-trained predicted regression lines in the same panel.",
            "",
            md_image(doc_path, SUPERVISOR_FIG_DIR / "heldout_pop_m4c_actual_vs_predicted_regression_lines.png", "Heldout actual vs predicted regression lines"),
            "",
            "**Heldout read.** These are the prediction plots that matter for generalization: actual heldout child regression lines and PBM-trained predicted regression lines in the same panel.",
            "",
            md_image(doc_path, SUPERVISOR_FIG_DIR / "heldout_pop_m4c_calibration_residuals.png", "Heldout calibration and residuals"),
            "",
            "## Robustness Regression-Line Checks",
            "",
            md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "m2_clear_robustness_regression_lines.png", "Age-scrambling regression-line robustness"),
            "",
            md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "robustness_outside_null_heatmap.png", "Age-scrambling outside-null heatmap"),
            "",
            "## Contrast Plots",
            "",
            md_image(doc_path, SUPERVISOR_FIG_DIR / "source_comparison_m4c_k3_words_slopes.png", "Source comparison fixed-effort slopes"),
            "",
            md_image(doc_path, CARETAKER_FIG_DIR / "caretaker_k3_cm2_nb_words_fixed_effort_atlas.png", "Caretaker fixed-effort CM2"),
            "",
            md_image(doc_path, CARETAKER_FIG_DIR / "caretaker_k3_cm6_nb_words_fixed_effort_atlas.png", "Caretaker fixed-effort CM6"),
            "",
            "## Secondary Rate Outcome Status",
            "",
            "`mean_bits_per_token` is available in the long scored dataset and can be modeled as a separate rate outcome. It should not be mixed into the main fixed-effort total-bits claim. The next rate-outcome check should reuse the strongest total-bits candidate formula and label the result as bits-per-token evidence.",
            "",
            "## Saved Row-Level Artifacts",
            "",
            "```text",
            str(REAL_ATLAS_DIR / "model_summary.csv"),
            str(REAL_ATLAS_DIR / "fixed_slice_slopes.csv"),
            str(REAL_ATLAS_DIR / "fixed_effort_predictions.csv.gz"),
            str(SOURCE_ATLAS_DIR),
            str(CARETAKER_DIR / "caretaker_model_summary.csv"),
            str(HELDOUT_DIR / "heldout_prediction_fit_summary.csv"),
            str(CHILD_STRUCTURE_DIR / "source_specific_model_summary.csv"),
            str(DEFAULT_FIG_DIR),
            "```",
            "",
        ]
    )
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    return

    missing_plots = plot_manifest[~plot_manifest["status"].eq("available")]
    base_ols = estimator_result_row(summary, "M2", "ols_fe_cluster")
    base_r2 = pd.to_numeric(pd.Series([base_ols.get("r2_observed_fitted")]), errors="coerce").iloc[0]
    lines: list[str] = [
        "# Route 1 Formula-by-Formula Robustness Deep Dive",
        "",
        "This is a **pre-supervisor model-selection evidence report**, not the final supervisor report.",
        "It is organized one formula at a time. Each formula has its own natural-language test sentence, the fully expanded formula, and one subsection per estimator family.",
        "",
        "## Reading Rules",
        "",
        "- Main outcome: `sum_bits`, the total information/uncertainty in one child utterance.",
        "- Effort predictors/controls: word, morpheme, syllable, or phoneme counts. In this report's main word-effort view, effort is `nb_words`.",
        "- Possible separate rate outcome: bits per token, e.g. `sum_bits / nb_words`. That is not the same scientific question as total utterance bits at fixed effort, and it should be modeled as a separate outcome if promoted.",
        "- Aggregate robustness outcome: `mean_sum_bits`, the average total utterance bits inside a child-session/effort-band cell. This is not bits per token and not the primary row-level outcome.",
        "- Age is the child's age at the session where the utterance was produced.",
        "- Parent context effort is the amount of caretaker/parent production effort in the preceding context.",
        "- Context entropy is the uncertainty/predictability of the preceding context.",
        "- Whenever an interaction appears, the lower-level predictors are written explicitly in the formula. For example, this report writes `age_c + effort_c + age_c:effort_c`, not shorthand.",
        "- Age and effort being correlated is not itself an interaction. The interaction asks whether the relation between effort and `sum_bits` changes as age changes.",
        "",
        "## Source Reports Used",
        "",
        f"- Real-child Atlas v2: {md_link(doc_path, real_atlas)}",
        f"- Source-specific Atlas v2 index: {md_link(doc_path, source_index)}",
        f"- Heldout prediction report: {md_link(doc_path, heldout_report)}",
        f"- Age-scrambling robustness report: {md_link(doc_path, age_report)}",
        f"- Caretaker Atlas v2: {md_link(doc_path, caretaker_report)}",
        "",
        "## Model Contrasts Added Here",
        "",
        "- **Without question type:** `M5_no_question` tests the same age, child-effort, context-entropy, and parent-effort controls as M5, but removes `C(question_type)`.",
        "- **With versus without age-by-effort:** `M5_age_effort_no_question` and `M5_age_effort_question` add `age_c:effort_c` while keeping `age_c` and `effort_c` written out.",
        "- **Parent-context reaction:** `M5_parent_reaction_no_question` and `M5_parent_reaction_question` test whether the relation between parent context effort and `sum_bits` changes with child age or child effort.",
        "- **Rich stress test:** M15 keeps the age-by-effort, context, parent-context, and context-form interactions together. This is for robustness and model-selection judgment, not for the simplest narrative.",
        "",
    ]

    for formula in CORE_FORMULAS:
        lines.extend(
            formula_deep_dive_lines(
                formula,
                summary,
                generated,
                doc_path,
                row_level_summary,
                row_level_slopes,
                base_r2=base_r2,
            )
        )

    lines.extend(
        [
            "## Cross-Formula Variable Importance",
            "",
            md_image(doc_path, generated["age_forest"], "Estimator-family age-effect forest plot"),
            "",
            "**Forest read.** Points left of zero mean older age predicts lower information. Additive-bit and log-mean-bit estimates are separated because they are not on the same coefficient scale.",
            "",
            md_image(doc_path, generated["nested_r2"], "Nested delta R2"),
            "",
            "**Delta-R2 read.** This is a nested-model fit diagnostic, not causal importance. It asks how much observed-vs-fitted R2 changes as controls and interactions are added.",
            "",
            "## Actual Data Regression Line vs Model-Predicted Lines",
            "",
            md_image(doc_path, generated["actual_vs_predicted"], "Actual trajectory vs M5 prediction"),
            "",
            md_image(doc_path, generated["actual_vs_predicted_age_effort"], "Actual trajectory vs age-by-effort prediction"),
            "",
            md_image(doc_path, generated["actual_vs_predicted_parent_reaction"], "Actual trajectory vs parent-context reaction prediction"),
            "",
            "**Actual-vs-predicted read.** Grey points are observed model cells; the black line is their descriptive trend; the dashed line is the fixed-effort model prediction. This separates raw developmental movement from controlled prediction.",
            "",
            "## Heldout Prediction",
            "",
            md_image(doc_path, SUPERVISOR_FIG_DIR / "heldout_pop_m4c_actual_vs_predicted_regression_lines.png", "Heldout actual vs predicted lines"),
            "",
            "**Heldout read.** Black lines are actual unseen-child trajectories; teal dashed lines are PBM-trained predictions. This is the generalization check, not a child-fixed-effect model.",
            "",
            md_image(doc_path, SUPERVISOR_FIG_DIR / "heldout_pop_m4c_calibration_residuals.png", "Heldout calibration and residuals"),
            "",
            "**Calibration read.** Points near the diagonal are better calibrated; residual trends over age show whether errors change developmentally.",
            "",
            "## Age-Scrambling / Null Robustness",
            "",
            md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "m2_clear_robustness_regression_lines.png", "M2 age-scrambling robustness lines"),
            "",
            md_image(doc_path, AGE_ROBUSTNESS_FIG_DIR / "robustness_outside_null_heatmap.png", "Age-scrambling outside-null heatmap"),
            "",
            "**Null read.** The observed age trend is stronger evidence when it sits outside age-label-scrambled null intervals. Balanced bootstrap intervals ask how stable the observed slope is under age-bin balancing.",
            "",
            "## Source Comparison: Real, Random, N-Gram, LSTM",
            "",
            md_image(doc_path, SUPERVISOR_FIG_DIR / "source_comparison_m4c_k3_words_slopes.png", "Source comparison M4c slopes"),
            "",
            "**Source read.** Real, random, n-gram, and LSTM targets are fit separately and then compared on the same fixed-effort slope scale. This is a source-specificity sanity check.",
            "",
            "## Caretaker Contrast",
            "",
            md_image(doc_path, CARETAKER_FIG_DIR / "caretaker_k3_cm2_nb_words_fixed_effort_atlas.png", "Caretaker CM2 fixed-effort lines"),
            "",
            md_image(doc_path, CARETAKER_FIG_DIR / "caretaker_k3_cm6_nb_words_fixed_effort_atlas.png", "Caretaker CM6 fixed-effort lines"),
            "",
            "**Caretaker read.** These plots ask whether adult/caretaker speech shows the same child-age pattern at fixed caretaker effort. They are a contrast, not a model of adult language development.",
            "",
            "## Reusable Machine-Readable Outputs",
            "",
            "The report avoids long reader-facing tables. The full estimator and term-level tables are saved for audit and regeneration:",
            "",
            "```text",
            str(output_dir / "real_child_k3_month_effort_band_aggregate.csv.gz"),
            str(output_dir / "aggregate_estimator_family_summary.csv"),
            str(output_dir / "aggregate_key_term_relation_summary.csv"),
            str(output_dir / "aggregate_estimator_fixed_effort_predictions.csv"),
            str(output_dir / "aggregate_estimator_fitted_values.csv.gz"),
            str(output_dir / "aggregate_ols_fe_nested_r2.csv"),
            str(output_dir / "estimator_family_coverage.csv"),
            str(output_dir / "existing_artifact_audit.csv"),
            str(output_dir / "required_plot_manifest.csv"),
            str(generated["M2_estimator_lines"].parent),
            "```",
            "",
        ]
    )
    if not missing_plots.empty:
        lines.extend(["## Missing Plot Warning", "", markdown_table(missing_plots, max_rows=30), ""])
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def run(*, input_csv: Path, output_dir: Path, fig_dir: Path, doc_dir: Path, chunksize: int) -> dict[str, Path]:
    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)

    artifact_audit = build_artifact_audit(output_dir)
    row_level_summary = read_csv_if_exists(REAL_ATLAS_DIR / "model_summary.csv")
    row_level_slopes = read_csv_if_exists(REAL_ATLAS_DIR / "fixed_slice_slopes.csv")
    summary = pd.DataFrame()
    coverage = pd.DataFrame()
    relation_summary = pd.DataFrame()
    generated: dict[str, Path] = {}
    plot_rows = []
    for model_id, _label in formula_rows_for_report(row_level_summary):
        for source_id, source_label in SOURCE_ORDER:
            path = source_fixed_effort_path(source_id, model_id)
            plot_rows.append(
                {
                    "plot_id": f"{model_id.lower()}_{source_id}_fixed_effort",
                    "requirement": f"{model_id} {source_label} fixed-effort regression lines",
                    "status": "available" if path.exists() else "missing",
                    "path": str(path),
                    "source": "source-specific row-level Atlas",
                }
            )
        caretaker_path = caretaker_fixed_effort_path(model_id)
        if caretaker_path is not None:
            plot_rows.append(
                {
                    "plot_id": f"{model_id.lower()}_caretaker_fixed_effort",
                    "requirement": f"{model_id} caretaker analog fixed-effort regression lines",
                    "status": "available" if caretaker_path.exists() else "missing",
                    "path": str(caretaker_path),
                    "source": "caretaker row-level Atlas",
                }
            )
    for plot_id, requirement, path, source in [
        ("m1_real_fixed_effort", "M1 pooled effort-only fixed-effort regression lines", source_fixed_effort_path("real", "M1"), "source-specific row-level Atlas"),
        ("m1_age_scrambling_lines", "M1 balanced/scrambled pooled-effort robustness lines", AGE_ROBUSTNESS_FIG_DIR / "m1_clear_robustness_regression_lines.png", "existing robustness report"),
        ("heldout_lines", "Heldout actual-vs-predicted regression lines", SUPERVISOR_FIG_DIR / "heldout_pop_m4c_actual_vs_predicted_regression_lines.png", "existing heldout report"),
        ("heldout_calibration", "Heldout calibration/residual lines", SUPERVISOR_FIG_DIR / "heldout_pop_m4c_calibration_residuals.png", "existing heldout report"),
        ("age_scrambling_lines", "Age-scrambling regression-line robustness", AGE_ROBUSTNESS_FIG_DIR / "m2_clear_robustness_regression_lines.png", "existing robustness report"),
        ("m3_age_scrambling_lines", "M3 balanced/scrambled age-by-effort robustness lines", AGE_ROBUSTNESS_FIG_DIR / "m3_clear_robustness_regression_lines.png", "existing robustness report"),
        ("age_scrambling_heatmap", "Age-scrambling outside-null heatmap", AGE_ROBUSTNESS_FIG_DIR / "robustness_outside_null_heatmap.png", "existing robustness report"),
        ("source_comparison", "Source-comparison fixed-effort slopes", SUPERVISOR_FIG_DIR / "source_comparison_m4c_k3_words_slopes.png", "existing supervisor candidate report"),
        ("caretaker_cm2", "Caretaker fixed-effort CM2", CARETAKER_FIG_DIR / "caretaker_k3_cm2_nb_words_fixed_effort_atlas.png", "existing caretaker atlas"),
        ("caretaker_cm6", "Caretaker fixed-effort CM6", CARETAKER_FIG_DIR / "caretaker_k3_cm6_nb_words_fixed_effort_atlas.png", "existing caretaker atlas"),
    ]:
        plot_rows.append(
            {
                "plot_id": plot_id,
                "requirement": requirement,
                "status": "available" if path.exists() else "missing",
                "path": str(path),
                "source": source,
            }
        )
    plot_manifest = pd.DataFrame(plot_rows)
    plot_manifest.to_csv(output_dir / "required_plot_manifest.csv", index=False)

    doc_path = doc_dir / f"{DOC_BASENAME}.md"
    html_path = doc_path.with_suffix(".html")
    embedded_path = doc_path.with_suffix(".embedded.html")
    pdf_path = doc_path.with_suffix(".pdf")
    write_report(
        doc_path=doc_path,
        output_dir=output_dir,
        generated=generated,
        artifact_audit=artifact_audit,
        coverage=coverage,
        plot_manifest=plot_manifest,
        summary=summary,
        relation_summary=relation_summary,
        row_level_summary=row_level_summary,
        row_level_slopes=row_level_slopes,
    )
    render_markdown_file(doc_path, html_path)
    render_markdown_file(doc_path, embedded_path, embed_images=True)
    outputs = {"md": doc_path, "html": html_path, "embedded_html": embedded_path}
    if render_pdf_report(html_path, pdf_path):
        outputs["pdf"] = pdf_path
    return outputs


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=ROUTE1_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--chunksize", type=int, default=250_000)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = run(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_dir=args.doc_dir,
        chunksize=args.chunksize,
    )
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
