#!/usr/bin/env python3
"""Fit, plot, and report child-only length-controlled Route 1 models.

The point of this script is to keep three stages separate:

* ``fit`` writes reusable model artifacts and CSV summaries.
* ``plot`` reads saved fit artifacts and makes figures.
* ``report`` reads saved fit/plot artifacts and writes a reader-facing report.

All scientific formulas in this suite control target utterance effort. The
default run is intentionally child-only, real-child, K3-context, word-effort
focused, because that is the central Route 1 estimand before caretaker and
baseline extensions are layered in.
"""

from __future__ import annotations

import argparse
import gc
import math
import os
import pickle
import sys
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

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
    from build_route1_corrected_baseline_atlas import (
        EFFORT_SPECS,
        QUESTION_TYPE_ORDER,
        add_corrected_predictors,
        coerce_numeric,
        read_route1_rows,
        selected_effort_specs,
        split_csv,
    )
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - package import path
    from src.build_route1_corrected_baseline_atlas import (
        EFFORT_SPECS,
        QUESTION_TYPE_ORDER,
        add_corrected_predictors,
        coerce_numeric,
        read_route1_rows,
        selected_effort_specs,
        split_csv,
    )
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_child_length_controlled_model_suite")
DEFAULT_FIG_DIR = Path("figs/route1_child_length_controlled_model_suite")
DEFAULT_DOC_MD = Path("docs/route1_child_length_controlled_model_suite.md")
DEFAULT_DOC_HTML = Path("docs/route1_child_length_controlled_model_suite.html")
RUN_DATE = datetime.now().strftime("%Y-%m-%d")


@dataclass(frozen=True)
class FormulaSpec:
    """One length-controlled scientific formula."""

    formula_id: str
    label: str
    terms: tuple[str, ...]
    question: str
    explanation: str
    needs_parent_context_effort: bool = False
    needs_context_entropy: bool = False
    needs_question_type: bool = False
    uses_age_bin: bool = False
    uses_exact_effort_category: bool = False
    tier: str = "core"


@dataclass(frozen=True)
class EstimatorSpec:
    """One estimator/repeated-measures structure."""

    estimator_id: str
    label: str
    frame_kind: str
    model_type: str
    covariance: str
    adds_child_fixed_effects: bool = False
    random_effects: str = ""
    session_variance_component: bool = False
    primary: bool = False
    explanation: str = ""
    why_use: str = ""


FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "F01",
        "Age at fixed effort",
        ("age_c", "effort_c"),
        "Does age predict total utterance information after utterance effort is held constant?",
        "This is the minimum defensible Route 1 formula. The outcome is total bits for the child utterance, age is the developmental predictor, and effort is the utterance size control. A negative age line here means that, among utterances of the same size, older children produce utterances that are less surprising to the model.",
    ),
    FormulaSpec(
        "F02",
        "Age by effort",
        ("age_c", "effort_c", "age_c:effort_c"),
        "Does the developmental age effect depend on how large the utterance is?",
        "This is the basic fixed-effort interaction model. It lets one-word, two-word, and longer utterances have different developmental slopes. This directly tests whether a single global age effect is hiding different fixed-length trajectories.",
    ),
    FormulaSpec(
        "F03",
        "Parent effort control",
        ("age_c", "effort_c", "parent_context_effort_c"),
        "Does preceding caretaker-context amount explain extra child utterance information?",
        "This model keeps child utterance effort controlled and adds the amount of preceding caretaker context in the same effort unit. It asks whether a child utterance is more or less informative when it follows a longer local context.",
        needs_parent_context_effort=True,
    ),
    FormulaSpec(
        "F04",
        "Age by parent effort",
        ("age_c", "effort_c", "parent_context_effort_c", "age_c:parent_context_effort_c"),
        "Does the effect of preceding caretaker effort change with child age?",
        "This model tests whether the relation between caretaker-context amount and child information is developmentally changing, while still comparing child utterances at matched target effort.",
        needs_parent_context_effort=True,
    ),
    FormulaSpec(
        "F05",
        "Effort by parent effort",
        ("age_c", "effort_c", "parent_context_effort_c", "effort_c:parent_context_effort_c"),
        "Does preceding caretaker effort matter differently for short versus long child utterances?",
        "This model asks whether the local context amount changes the slope linking child utterance size to child utterance information. It is a context-by-length check, not a raw length-growth check.",
        needs_parent_context_effort=True,
    ),
    FormulaSpec(
        "F06",
        "Parent interaction stress test",
        (
            "age_c",
            "effort_c",
            "parent_context_effort_c",
            "age_c:effort_c",
            "age_c:parent_context_effort_c",
            "effort_c:parent_context_effort_c",
        ),
        "Do the age, target-effort, and parent-context-effort relations survive together?",
        "This is the richer parent-context formula. It keeps the key fixed-effort age-by-effort term and checks whether parent context effort changes either the developmental trajectory or the effort-information relation.",
        needs_parent_context_effort=True,
    ),
    FormulaSpec(
        "F07",
        "Question type control",
        ("age_c", "effort_c", "C(question_type)"),
        "Does the age effect remain after broad preceding-context question type is controlled?",
        "This formula compares fixed-effort child utterances while accounting for whether the preceding context is not a question, a wh-question, a yes/no question, another question, or empty. It is a local discourse control.",
        needs_question_type=True,
    ),
    FormulaSpec(
        "F08",
        "Context entropy control",
        ("age_c", "effort_c", "context_entropy_c"),
        "Does age still predict child utterance information after local context entropy is controlled?",
        "This formula adds the available context-entropy feature. It separates the developmental fixed-effort age pattern from the fact that some contexts make upcoming language more predictable than others.",
        needs_context_entropy=True,
    ),
    FormulaSpec(
        "F09",
        "All context controls",
        ("age_c", "effort_c", "parent_context_effort_c", "context_entropy_c", "C(question_type)"),
        "Does the fixed-effort age effect remain after the main local-context controls are added together?",
        "This is the compact contextual-control model. It estimates the age pattern at fixed child effort while simultaneously controlling caretaker context amount, context entropy, and broad question type.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
    ),
    FormulaSpec(
        "F10",
        "All context controls with age by effort",
        (
            "age_c",
            "effort_c",
            "parent_context_effort_c",
            "context_entropy_c",
            "C(question_type)",
            "age_c:effort_c",
        ),
        "Does the fixed-effort age-by-effort pattern remain after the main context controls are added?",
        "This is a strong candidate headline formula because it keeps the fixed-length interpretation explicit and adds the major local-context confounds.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
    ),
    FormulaSpec(
        "F11",
        "Entropy interactions",
        (
            "age_c",
            "effort_c",
            "parent_context_effort_c",
            "context_entropy_c",
            "C(question_type)",
            "age_c:effort_c",
            "age_c:context_entropy_c",
            "effort_c:context_entropy_c",
        ),
        "Does sensitivity to context entropy change with child age or child utterance effort?",
        "This formula checks whether the context-entropy control is only an additive nuisance variable or whether entropy changes the developmental and fixed-effort slopes themselves.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        tier="extended",
    ),
    FormulaSpec(
        "F12",
        "Full context interaction stress test",
        (
            "age_c",
            "effort_c",
            "parent_context_effort_c",
            "context_entropy_c",
            "C(question_type)",
            "age_c:effort_c",
            "age_c:parent_context_effort_c",
            "effort_c:parent_context_effort_c",
            "age_c:context_entropy_c",
            "effort_c:context_entropy_c",
            "parent_context_effort_c:context_entropy_c",
        ),
        "Do the developmental fixed-effort results persist under a richer context-interaction stress test?",
        "This is deliberately not the simplest interpretation model. It is a stress test for the claim that the age pattern is not just an artifact of parent context effort, entropy, or their interaction with child effort.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        tier="extended",
    ),
    FormulaSpec(
        "F13",
        "Question interactions",
        (
            "age_c",
            "effort_c",
            "parent_context_effort_c",
            "context_entropy_c",
            "C(question_type)",
            "age_c:effort_c",
            "age_c:C(question_type)",
            "context_entropy_c:C(question_type)",
        ),
        "Does the developmental or entropy effect differ by broad preceding-context question type?",
        "This formula checks whether wh-questions, yes/no questions, and other contexts produce different fixed-effort developmental patterns.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        tier="extended",
    ),
    FormulaSpec(
        "F14",
        "Curved age trajectory",
        ("age_c", "I(age_c ** 2)", "effort_c"),
        "Is the fixed-effort developmental trajectory curved rather than straight?",
        "This formula keeps effort controlled but allows the age trajectory to bend. It is useful if the decline or increase in fixed-effort information is strongest at early ages and then flattens later.",
        tier="extended",
    ),
    FormulaSpec(
        "F15",
        "Curved age by effort",
        ("age_c", "I(age_c ** 2)", "effort_c", "age_c:effort_c", "I(age_c ** 2):effort_c"),
        "Does the curved developmental trajectory differ across utterance sizes?",
        "This is the nonlinear version of the age-by-effort model. It checks whether one-word and longer utterances have different curved age trajectories.",
        tier="extended",
    ),
    FormulaSpec(
        "F16",
        "Age-bin trajectory",
        ("C(age_bin)", "effort_c"),
        "Do developmental age-bin differences remain after target effort is controlled?",
        "This formula avoids imposing a straight age slope. It compares age bins directly, while still holding utterance effort constant.",
        uses_age_bin=True,
        tier="extended",
    ),
    FormulaSpec(
        "F17",
        "Age-bin by effort",
        ("C(age_bin)", "effort_c", "C(age_bin):effort_c"),
        "Do age-bin differences depend on utterance effort?",
        "This is the categorical-age version of the fixed-effort interaction model. It asks whether developmental differences look different for short and long utterances without assuming a linear age trend.",
        uses_age_bin=True,
        tier="extended",
    ),
    FormulaSpec(
        "F18",
        "Exact-length fixed effects",
        ("age_c", "C(effort_value_int)"),
        "Does age predict total information after each exact utterance length gets its own baseline?",
        "This model treats length as a category, not as a linear covariate. It removes the MLU explanation by comparing the age trajectory after arbitrary differences among exact word counts have been absorbed.",
        uses_exact_effort_category=True,
        tier="mlu_proof",
    ),
    FormulaSpec(
        "F19",
        "Exact-length age slopes",
        ("age_c", "C(effort_value_int)", "age_c:C(effort_value_int)"),
        "Do the age slopes remain downward inside exact utterance-length strata?",
        "This is the main MLU-proof formula. It estimates a separate age slope for each exact utterance length, so the developmental effect is read within same-length comparisons rather than across the changing MLU distribution.",
        uses_exact_effort_category=True,
        tier="mlu_proof",
    ),
    FormulaSpec(
        "F20",
        "Exact-length fixed effects with context controls",
        ("age_c", "C(effort_value_int)", "parent_context_effort_c", "context_entropy_c", "C(question_type)"),
        "Does the exact-length age effect remain after the main local-context controls?",
        "This model keeps exact length categorical and adds caretaker context effort, context entropy, and question type. It asks whether the same-length age trajectory survives the major local context controls.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        uses_exact_effort_category=True,
        tier="mlu_proof",
    ),
    FormulaSpec(
        "F21",
        "Exact-length age slopes with context controls",
        (
            "age_c",
            "C(effort_value_int)",
            "age_c:C(effort_value_int)",
            "parent_context_effort_c",
            "context_entropy_c",
            "C(question_type)",
        ),
        "Do exact-length age slopes remain after local-context controls?",
        "This is the strongest current same-length formula. Each exact utterance length can have its own age slope, and the model still controls parent context effort, context entropy, question type, and child identity through the estimator.",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        uses_exact_effort_category=True,
        tier="mlu_proof",
    ),
)


ESTIMATORS: tuple[EstimatorSpec, ...] = (
    EstimatorSpec(
        "row_ols_fe_cluster",
        "Row-level OLS with child fixed intercepts and child-clustered SE",
        "row",
        "ols",
        "cluster_child",
        adds_child_fixed_effects=True,
        primary=True,
        explanation="Fits the utterance-level model directly and adds one intercept for each child. Standard errors are clustered by child, so repeated utterances from the same child are not treated as independent for uncertainty.",
        why_use="This is the clearest fixed-effort baseline: it answers the Route 1 question on the original utterance rows while controlling child identity.",
    ),
    EstimatorSpec(
        "agg_ols_fe_cluster",
        "Session/effort-cell OLS with child fixed intercepts and child-clustered SE",
        "aggregate",
        "ols",
        "cluster_child",
        adds_child_fixed_effects=True,
        explanation="Averages utterances into child-session-exact-effort-context cells, then fits OLS with child fixed intercepts and child-clustered standard errors.",
        why_use="It prevents sessions with many repeated utterances from dominating the analysis and checks that the row-level result is not just a high-row-count-session result.",
    ),
    EstimatorSpec(
        "agg_glm_gaussian",
        "Session/effort-cell Gaussian GLM with child fixed intercepts",
        "aggregate",
        "glm_gaussian",
        "model_based",
        adds_child_fixed_effects=True,
        explanation="Fits the same mean formula through the GLM framework with a Gaussian outcome distribution. It is close to OLS but uses the generalized-model machinery.",
        why_use="It is a bridge from ordinary regression to the generalized estimators used for positive skewed outcomes.",
    ),
    EstimatorSpec(
        "agg_glm_gamma_log",
        "Session/effort-cell Gamma/log GLM with child fixed intercepts",
        "aggregate",
        "glm_gamma_log",
        "model_based",
        adds_child_fixed_effects=True,
        explanation="Fits positive total bits with a Gamma mean-variance relation and a log link, while keeping the same length-controlled formula and child fixed intercepts.",
        why_use="Total bits are positive and often right-skewed, so this checks whether the fixed-effort age result depends on a Gaussian error assumption.",
    ),
    EstimatorSpec(
        "agg_gee_gaussian",
        "Session/effort-cell Gaussian GEE grouped by child",
        "aggregate",
        "gee_gaussian",
        "exchangeable_child",
        adds_child_fixed_effects=True,
        explanation="Fits a population-average Gaussian model with an exchangeable working correlation for repeated cells from the same child. Child fixed intercepts remain in the mean model.",
        why_use="This estimates the mean relation while representing within-child dependence, which is essential for repeated utterances from the same children.",
    ),
    EstimatorSpec(
        "agg_gee_gamma_log",
        "Session/effort-cell Gamma/log GEE grouped by child",
        "aggregate",
        "gee_gamma_log",
        "exchangeable_child",
        adds_child_fixed_effects=True,
        explanation="Combines a positive skewed Gamma/log mean with GEE's child-level working correlation.",
        why_use="This checks whether the positive-outcome GEE story agrees with the fixed-effort OLS and mixed-model stories.",
    ),
    EstimatorSpec(
        "agg_mixed_random_intercept",
        "Session/effort-cell mixed model with random child intercept",
        "aggregate",
        "mixedlm",
        "random_child_intercept",
        random_effects="1",
        explanation="Fits a linear mixed model where each child has a random intercept rather than a fixed intercept.",
        why_use="This is the standard repeated-measures model when children are sampled units and the analysis should estimate child-to-child variability.",
    ),
    EstimatorSpec(
        "agg_mixed_random_age_slope",
        "Session/effort-cell mixed model with random child age slope",
        "aggregate",
        "mixedlm",
        "random_child_intercept_age_slope",
        random_effects="1 + age_c",
        explanation="Allows children to differ both in their baseline information level and in their developmental age slope.",
        why_use="This is the main check for whether one average developmental line is hiding children with different age trajectories.",
    ),
    EstimatorSpec(
        "agg_mixed_session_intercept",
        "Session/effort-cell mixed model with child and session intercepts",
        "aggregate",
        "mixedlm",
        "random_child_and_session_intercepts",
        random_effects="1",
        session_variance_component=True,
        explanation="Adds a child random intercept and a session-level variance component.",
        why_use="The data are repeated utterances inside sessions inside children. This model asks whether the age effect survives after both levels are represented.",
    ),
)


IMPORTANT_TERMS = (
    "age_c",
    "effort_c",
    "parent_context_effort_c",
    "context_entropy_c",
    "age_c:effort_c",
    "age_c:parent_context_effort_c",
    "effort_c:parent_context_effort_c",
    "age_c:context_entropy_c",
    "effort_c:context_entropy_c",
    "parent_context_effort_c:context_entropy_c",
    "I(age_c ** 2)",
    "I(age_c ** 2):effort_c",
)
EXACT_LENGTH_FORMULA_IDS = {"F18", "F19", "F20", "F21"}


def formula_lookup() -> dict[str, FormulaSpec]:
    return {spec.formula_id: spec for spec in FORMULAS}


def estimator_lookup() -> dict[str, EstimatorSpec]:
    return {spec.estimator_id: spec for spec in ESTIMATORS}


def selected_formulas(ids: Sequence[str]) -> list[FormulaSpec]:
    requested = set(ids or ["all"])
    if requested == {"all"}:
        return list(FORMULAS)
    if requested == {"core"}:
        return [spec for spec in FORMULAS if spec.tier == "core"]
    if requested == {"extended"}:
        return [spec for spec in FORMULAS if spec.tier == "extended"]
    if requested in ({"mlu_proof"}, {"mluproof"}):
        return [spec for spec in FORMULAS if spec.tier == "mlu_proof"]
    lookup = formula_lookup()
    missing = requested - set(lookup)
    if missing:
        raise ValueError(f"unknown formula ids: {sorted(missing)}")
    return [lookup[item] for item in ids]


def selected_estimators(ids: Sequence[str]) -> list[EstimatorSpec]:
    requested = set(ids or ["all"])
    if requested == {"all"}:
        return list(ESTIMATORS)
    if requested == {"primary"}:
        return [spec for spec in ESTIMATORS if spec.primary]
    if requested == {"aggregate"}:
        return [spec for spec in ESTIMATORS if spec.frame_kind == "aggregate"]
    lookup = estimator_lookup()
    missing = requested - set(lookup)
    if missing:
        raise ValueError(f"unknown estimator ids: {sorted(missing)}")
    return [lookup[item] for item in ids]


def safe_slug(value: object) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(value).lower()).strip("_")


def statsmodels_formula(formula: FormulaSpec, estimator: EstimatorSpec) -> str:
    terms = list(formula.terms)
    if estimator.adds_child_fixed_effects:
        terms.append("C(child_id)")
    return "route1_outcome ~ " + " + ".join(terms)


def readable_formula(formula: FormulaSpec, estimator: EstimatorSpec) -> str:
    text = statsmodels_formula(formula, estimator)
    return (
        text.replace("route1_outcome", "sum_bits")
        .replace("age_c", "age")
        .replace("effort_c", "target_effort")
        .replace("parent_context_effort_c", "parent_context_effort")
        .replace("context_entropy_c", "context_entropy")
    )


def formula_needs_columns(formula: FormulaSpec) -> list[str]:
    columns = ["sum_bits", "age_months", "effort_value", "child_id", "session_key"]
    if formula.needs_parent_context_effort:
        columns.append("parent_context_effort_value")
    if formula.needs_context_entropy:
        columns.append("context_entropy_bits")
    if formula.needs_question_type:
        columns.append("question_type")
    if formula.uses_age_bin:
        columns.append("age_bin")
    if formula.uses_exact_effort_category:
        columns.append("effort_value_int")
    return columns


def build_child_base_frame(raw: pd.DataFrame, effort_col: str, parent_context_col: str) -> pd.DataFrame:
    """Return a child-only analysis base frame for one effort measure."""

    data = add_corrected_predictors(raw)
    if "target_source" not in data.columns:
        data["target_source"] = data.get("target_variant", "").astype(str)
    for col in ["dataset", "child_id", "session_id", "age_bin", "context_text", "question_type"]:
        if col not in data.columns:
            data[col] = ""
    for col in ["sum_bits", "age_months", effort_col, parent_context_col, "context_entropy_bits"]:
        if col not in data.columns:
            data[col] = math.nan
    data = coerce_numeric(data, ["sum_bits", "age_months", effort_col, parent_context_col, "context_entropy_bits"])
    data["effort_value"] = data[effort_col]
    data["effort_value_int"] = pd.to_numeric(data["effort_value"], errors="coerce").round().astype("Int64")
    data["parent_context_effort_value"] = data[parent_context_col]
    data["session_key"] = (
        data["dataset"].astype(str).fillna("")
        + "::"
        + data["child_id"].astype(str).fillna("")
        + "::"
        + data["session_id"].astype(str).fillna("")
    )
    data["question_type"] = pd.Categorical(data["question_type"].astype(str), categories=QUESTION_TYPE_ORDER)
    data["age_bin"] = data["age_bin"].astype(str)
    required = ["sum_bits", "age_months", "effort_value", "effort_value_int", "child_id", "session_key"]
    data = data.dropna(subset=required).copy()
    data = data[(data["sum_bits"] > 0) & (data["age_months"] > 0) & (data["effort_value"] > 0)].copy()
    keep = [
        "dataset",
        "child_id",
        "session_id",
        "session_key",
        "context_k",
        "age_months",
        "age_bin",
        "question_type",
        "sum_bits",
        "effort_value",
        "effort_value_int",
        "parent_context_effort_value",
        "context_entropy_bits",
    ]
    return data[keep].reset_index(drop=True)


def aggregate_exact_effort_cells(data: pd.DataFrame) -> pd.DataFrame:
    """Average repeated utterances in child-session-exact-effort cells."""

    group_cols = [
        "dataset",
        "child_id",
        "session_id",
        "session_key",
        "age_months",
        "age_bin",
        "effort_value",
        "effort_value_int",
        "question_type",
    ]
    grouped = (
        data.groupby(group_cols, dropna=False, observed=True)
        .agg(
            route1_outcome=("sum_bits", "mean"),
            n_source_rows=("sum_bits", "size"),
            parent_context_effort_value=("parent_context_effort_value", "mean"),
            context_entropy_bits=("context_entropy_bits", "mean"),
        )
        .reset_index()
    )
    grouped["question_type"] = pd.Categorical(grouped["question_type"].astype(str), categories=QUESTION_TYPE_ORDER)
    return grouped


def center_frame(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["effort_c"] = out["effort_value"] - out["effort_value"].mean()
    out["parent_context_effort_c"] = out["parent_context_effort_value"] - out["parent_context_effort_value"].mean()
    out["context_entropy_c"] = out["context_entropy_bits"] - out["context_entropy_bits"].mean()
    child_mean_age = out.groupby("child_id", observed=True)["age_months"].transform("mean")
    out["age_within_child_c"] = out["age_months"] - child_mean_age
    out["child_mean_age_c"] = child_mean_age - out["age_months"].mean()
    out["child_id"] = out["child_id"].astype(str)
    out["session_key"] = out["session_key"].astype(str)
    out["age_bin"] = out["age_bin"].astype(str)
    out["effort_value_int"] = pd.to_numeric(out["effort_value_int"], errors="coerce").astype(int)
    out["question_type"] = pd.Categorical(out["question_type"].astype(str), categories=QUESTION_TYPE_ORDER)
    return out


def prepare_analysis_frame(base: pd.DataFrame, formula: FormulaSpec, frame_kind: str) -> tuple[pd.DataFrame, str]:
    """Prepare one formula-specific row or aggregate frame."""

    required = formula_needs_columns(formula)
    data = base.copy()
    data = data.dropna(subset=[col for col in required if col in data.columns]).copy()
    if formula.needs_context_entropy:
        data = data[data["context_entropy_bits"] > 0].copy()
    if formula.uses_age_bin:
        data = data[data["age_bin"].astype(str).ne("")].copy()
    if data.empty:
        return data, "no complete rows"
    if frame_kind == "row":
        data["route1_outcome"] = data["sum_bits"]
        data["n_source_rows"] = 1
    elif frame_kind == "aggregate":
        data = aggregate_exact_effort_cells(data)
    else:
        return data, f"unknown frame kind: {frame_kind}"
    data = data.dropna(subset=["route1_outcome", "age_months", "effort_value", "child_id"]).copy()
    data = data[(data["route1_outcome"] > 0) & (data["age_months"] > 0) & (data["effort_value"] > 0)].copy()
    if formula.needs_context_entropy:
        data = data[data["context_entropy_bits"] > 0].copy()
    if data["child_id"].nunique() < 2:
        return data, "fewer than two children"
    if len(data) < 20:
        return data, "fewer than 20 analysis rows"
    data = center_frame(data)
    for col, label in [
        ("age_c", "age has no variation"),
        ("effort_c", "target effort has no variation"),
    ]:
        if pd.to_numeric(data[col], errors="coerce").std(ddof=0) <= 0:
            return data, label
    if formula.needs_parent_context_effort and pd.to_numeric(data["parent_context_effort_c"], errors="coerce").std(ddof=0) <= 0:
        return data, "parent context effort has no variation"
    if formula.needs_context_entropy and pd.to_numeric(data["context_entropy_c"], errors="coerce").std(ddof=0) <= 0:
        return data, "context entropy has no variation"
    if formula.uses_age_bin and data["age_bin"].nunique(dropna=True) < 2:
        return data, "age bin has fewer than two levels"
    return data.reset_index(drop=True), ""


def fit_model(data: pd.DataFrame, formula_text: str, estimator: EstimatorSpec) -> object:
    """Fit one prepared statsmodels model."""

    if estimator.model_type == "ols":
        result = smf.ols(formula_text, data=data).fit()
        if estimator.covariance == "cluster_child":
            result = result.get_robustcov_results(cov_type="cluster", groups=data["child_id"])
        return result
    if estimator.model_type == "glm_gaussian":
        return smf.glm(formula_text, data=data, family=Gaussian()).fit()
    if estimator.model_type == "glm_gamma_log":
        return smf.glm(formula_text, data=data, family=Gamma(link=Log())).fit()
    if estimator.model_type == "gee_gaussian":
        return smf.gee(
            formula_text,
            groups="child_id",
            data=data,
            cov_struct=Exchangeable(),
            family=Gaussian(),
        ).fit()
    if estimator.model_type == "gee_gamma_log":
        return smf.gee(
            formula_text,
            groups="child_id",
            data=data,
            cov_struct=Exchangeable(),
            family=Gamma(link=Log()),
        ).fit()
    if estimator.model_type == "mixedlm":
        vc_formula = {"session": "0 + C(session_key)"} if estimator.session_variance_component else None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return smf.mixedlm(
                formula_text,
                data=data,
                groups=data["child_id"],
                re_formula=estimator.random_effects or "1",
                vc_formula=vc_formula,
            ).fit(reml=False, method="lbfgs", maxiter=200, disp=False)
    raise ValueError(f"unknown estimator model type: {estimator.model_type}")


def model_names(result: object) -> list[str]:
    params = getattr(result, "params", None)
    if hasattr(params, "index"):
        return [str(item) for item in params.index]
    model = getattr(result, "model", None)
    return [str(item) for item in getattr(model, "exog_names", [])]


def named_values(result: object, attr: str) -> dict[str, float]:
    values = getattr(result, attr, None)
    names = model_names(result)
    out: dict[str, float] = {}
    if values is None:
        return out
    if hasattr(values, "index"):
        for name in values.index:
            try:
                out[str(name)] = float(values[name])
            except Exception:
                out[str(name)] = math.nan
        return out
    for idx, name in enumerate(names):
        try:
            out[name] = float(values[idx])
        except Exception:
            out[name] = math.nan
    return out


def confidence_intervals(result: object) -> dict[str, tuple[float, float]]:
    try:
        conf = result.conf_int()
    except Exception:
        return {}
    names = model_names(result)
    out: dict[str, tuple[float, float]] = {}
    if hasattr(conf, "index"):
        for name in conf.index:
            try:
                out[str(name)] = (float(conf.loc[name].iloc[0]), float(conf.loc[name].iloc[1]))
            except Exception:
                out[str(name)] = (math.nan, math.nan)
        return out
    for idx, name in enumerate(names):
        try:
            out[name] = (float(conf[idx][0]), float(conf[idx][1]))
        except Exception:
            out[name] = (math.nan, math.nan)
    return out


def term_series(term: str, data: pd.DataFrame) -> pd.Series | None:
    if term in data.columns:
        return pd.to_numeric(data[term], errors="coerce")
    if term == "I(age_c ** 2)":
        return pd.to_numeric(data["age_c"], errors="coerce") ** 2
    if term == "I(age_c ** 2):effort_c":
        return (pd.to_numeric(data["age_c"], errors="coerce") ** 2) * pd.to_numeric(data["effort_c"], errors="coerce")
    if ":" in term and not term.startswith("C("):
        parts = term.split(":")
        series = pd.Series(1.0, index=data.index)
        for part in parts:
            values = term_series(part, data)
            if values is None:
                return None
            series = series * values
        return series
    return None


def coefficient_long_frame(
    result: object,
    data: pd.DataFrame,
    *,
    formula: FormulaSpec,
    estimator: EstimatorSpec,
    effort_col: str,
    effort_label: str,
    context_k: str,
) -> pd.DataFrame:
    params = named_values(result, "params")
    pvalues = named_values(result, "pvalues")
    intervals = confidence_intervals(result)
    y_sd = float(pd.to_numeric(data["route1_outcome"], errors="coerce").std(ddof=0))
    rows: list[dict[str, object]] = []
    for term, estimate in params.items():
        ci_low, ci_high = intervals.get(term, (math.nan, math.nan))
        x = term_series(term, data)
        standardized = math.nan
        if x is not None and y_sd > 0:
            x_sd = float(x.std(ddof=0))
            if math.isfinite(x_sd) and x_sd > 0:
                standardized = estimate * x_sd / y_sd
        rows.append(
            {
                "formula_id": formula.formula_id,
                "formula_label": formula.label,
                "estimator_id": estimator.estimator_id,
                "estimator_label": estimator.label,
                "frame_kind": estimator.frame_kind,
                "context_k": context_k,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "term": term,
                "estimate": estimate,
                "p_value": pvalues.get(term, math.nan),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "standardized_estimate": standardized,
                "abs_standardized_estimate": abs(standardized) if math.isfinite(standardized) else math.nan,
                "is_child_fixed_effect": term.startswith("C(child_id)"),
                "is_question_type_term": "question_type" in term,
                "is_age_bin_term": "age_bin" in term,
            }
        )
    return pd.DataFrame(rows)


def prediction_summary_frame(result: object, new_frame: pd.DataFrame) -> pd.DataFrame:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            warnings.simplefilter("ignore", FutureWarning)
            summary = result.get_prediction(new_frame).summary_frame(alpha=0.05)
        mean_col = "mean" if "mean" in summary.columns else "predicted_mean" if "predicted_mean" in summary.columns else None
        low_col = "mean_ci_lower" if "mean_ci_lower" in summary.columns else "ci_lower" if "ci_lower" in summary.columns else None
        high_col = "mean_ci_upper" if "mean_ci_upper" in summary.columns else "ci_upper" if "ci_upper" in summary.columns else None
        pred = np.asarray(summary[mean_col], dtype=float) if mean_col else np.asarray(result.predict(new_frame), dtype=float)
        return pd.DataFrame(
            {
                "predicted_sum_bits": pred,
                "pred_ci_low": np.asarray(summary[low_col], dtype=float) if low_col else np.nan,
                "pred_ci_high": np.asarray(summary[high_col], dtype=float) if high_col else np.nan,
            }
        )
    except Exception:
        try:
            pred = np.asarray(result.predict(new_frame), dtype=float)
        except Exception:
            pred = np.full(len(new_frame), np.nan)
        return pd.DataFrame({"predicted_sum_bits": pred, "pred_ci_low": np.nan, "pred_ci_high": np.nan})


def age_bins_for_grid(data: pd.DataFrame, ages: np.ndarray) -> list[str]:
    valid = data[["age_months", "age_bin"]].copy()
    valid["age_months"] = pd.to_numeric(valid["age_months"], errors="coerce")
    valid = valid.dropna(subset=["age_months"])
    valid = valid[valid["age_bin"].astype(str).ne("")]
    if valid.empty:
        return [""] * len(ages)
    ranges = (
        valid.groupby("age_bin", observed=True)["age_months"]
        .agg(["min", "max", "median"])
        .sort_values("median")
        .reset_index()
    )
    assigned: list[str] = []
    for age in ages:
        containing = ranges[(ranges["min"] <= age) & (ranges["max"] >= age)].copy()
        if containing.empty:
            containing = ranges.copy()
        distances = (containing["median"] - age).abs().to_numpy()
        assigned.append(str(containing.iloc[int(distances.argmin())]["age_bin"]))
    return assigned


def fixed_effort_values(data: pd.DataFrame, effort_col: str, max_values: int = 12) -> list[int]:
    values = pd.to_numeric(data["effort_value"], errors="coerce").dropna().astype(int)
    if effort_col in {"nb_words", "nb_morphemes"}:
        return [value for value in range(1, max_values + 1) if (values == value).any()]
    frequent = values.value_counts().head(max_values).index.astype(int).tolist()
    return sorted({int(value) for value in frequent if int(value) > 0})


def fixed_prediction_grid(
    result: object,
    data: pd.DataFrame,
    *,
    formula: FormulaSpec,
    estimator: EstimatorSpec,
    formula_text: str,
    effort_col: str,
    effort_label: str,
    context_k: str,
    n_points: int,
) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    low = float(data["age_months"].quantile(0.02))
    high = float(data["age_months"].quantile(0.98))
    if not math.isfinite(low) or not math.isfinite(high) or low == high:
        return pd.DataFrame()
    ages = np.linspace(low, high, n_points)
    age_bins = age_bins_for_grid(data, ages)
    values = fixed_effort_values(data, effort_col)
    if not values:
        return pd.DataFrame()
    modal_question = (
        str(data["question_type"].mode(dropna=True).iloc[0])
        if "question_type" in data and not data["question_type"].dropna().empty
        else "not question"
    )
    child_ids = sorted(data["child_id"].astype(str).unique())
    first_session = str(data["session_key"].iloc[0]) if "session_key" in data and len(data) else ""
    parts: list[pd.DataFrame] = []
    has_child_fixed_effects = "C(child_id)" in formula_text
    for fixed_value in values:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_bin": age_bins,
                "age_c": ages - float(data["age_months"].mean()),
                "effort_value": float(fixed_value),
                "effort_value_int": int(fixed_value),
                "effort_c": float(fixed_value) - float(data["effort_value"].mean()),
                "parent_context_effort_value": float(data["parent_context_effort_value"].mean())
                if "parent_context_effort_value" in data
                else 0.0,
                "parent_context_effort_c": 0.0,
                "context_entropy_bits": float(data["context_entropy_bits"].mean()) if "context_entropy_bits" in data else 0.0,
                "context_entropy_c": 0.0,
                "question_type": pd.Categorical([modal_question] * len(ages), categories=QUESTION_TYPE_ORDER),
                "session_key": first_session,
                "fixed_effort_value": int(fixed_value),
            }
        )
        if has_child_fixed_effects:
            child_parts: list[pd.DataFrame] = []
            for child_id in child_ids:
                child_frame = base.copy()
                child_frame["child_id"] = child_id
                pred = prediction_summary_frame(result, child_frame)
                child_parts.append(pd.concat([child_frame.reset_index(drop=True), pred.reset_index(drop=True)], axis=1))
            combined = pd.concat(child_parts, ignore_index=True)
            pred_part = (
                combined.groupby(["age_months", "age_bin", "fixed_effort_value"], as_index=False, observed=True)[
                    ["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]
                ]
                .mean()
                .copy()
            )
        else:
            base["child_id"] = child_ids[0] if child_ids else ""
            pred = prediction_summary_frame(result, base)
            pred_part = pd.concat([base.reset_index(drop=True), pred.reset_index(drop=True)], axis=1)
        pred_part["formula_id"] = formula.formula_id
        pred_part["formula_label"] = formula.label
        pred_part["estimator_id"] = estimator.estimator_id
        pred_part["estimator_label"] = estimator.label
        pred_part["frame_kind"] = estimator.frame_kind
        pred_part["context_k"] = context_k
        pred_part["effort_col"] = effort_col
        pred_part["effort_label"] = effort_label
        parts.append(pred_part)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fit_quality_metrics(result: object, data: pd.DataFrame) -> dict[str, float]:
    observed = pd.to_numeric(data["route1_outcome"], errors="coerce").to_numpy(dtype=float)
    try:
        fitted = np.asarray(getattr(result, "fittedvalues"), dtype=float)
        if len(fitted) != len(observed):
            fitted = np.asarray(result.predict(data), dtype=float)
    except Exception:
        try:
            fitted = np.asarray(result.predict(data), dtype=float)
        except Exception:
            fitted = np.full(len(observed), np.nan)
    mask = np.isfinite(observed) & np.isfinite(fitted)
    if mask.sum() < 2:
        return {"r2_observed_fitted": math.nan, "rmse": math.nan, "mae": math.nan}
    y = observed[mask]
    pred = fitted[mask]
    if float(np.std(y)) > 0 and float(np.std(pred)) > 0:
        corr = float(np.corrcoef(y, pred)[0, 1])
        r2 = corr * corr if math.isfinite(corr) else math.nan
    else:
        r2 = math.nan
    return {
        "r2_observed_fitted": r2,
        "rmse": float(np.sqrt(np.mean((y - pred) ** 2))),
        "mae": float(np.mean(np.abs(y - pred))),
    }


def scalar_metric(result: object, attr: str) -> float:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            value = float(getattr(result, attr))
    except Exception:
        return math.nan
    return value if math.isfinite(value) else math.nan


def save_model_result(result: object, path: Path) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        removable = result
        try:
            removable.remove_data()
        except Exception:
            pass
        with path.open("wb") as handle:
            pickle.dump(removable, handle)
        return str(path), ""
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


def fit_one(
    data: pd.DataFrame,
    *,
    formula: FormulaSpec,
    estimator: EstimatorSpec,
    effort_col: str,
    effort_label: str,
    context_k: str,
    output_dir: Path,
    n_points: int,
    save_models: bool,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    formula_text = statsmodels_formula(formula, estimator)
    summary: dict[str, object] = {
        "run_date": RUN_DATE,
        "formula_id": formula.formula_id,
        "formula_label": formula.label,
        "formula_tier": formula.tier,
        "formula_question": formula.question,
        "estimator_id": estimator.estimator_id,
        "estimator_label": estimator.label,
        "frame_kind": estimator.frame_kind,
        "model_type": estimator.model_type,
        "covariance": estimator.covariance,
        "context_k": context_k,
        "effort_col": effort_col,
        "effort_label": effort_label,
        "statsmodels_formula": formula_text,
        "readable_formula": readable_formula(formula, estimator),
        "n_obs": int(len(data)),
        "n_source_rows": int(data["n_source_rows"].sum()) if "n_source_rows" in data else int(len(data)),
        "n_children": int(data["child_id"].nunique()) if "child_id" in data else 0,
        "n_sessions": int(data["session_key"].nunique()) if "session_key" in data else 0,
        "age_min": float(data["age_months"].min()) if "age_months" in data and len(data) else math.nan,
        "age_max": float(data["age_months"].max()) if "age_months" in data and len(data) else math.nan,
        "status": "fit",
        "error": "",
        "model_path": "",
        "model_save_error": "",
        "r2_observed_fitted": math.nan,
        "rmse": math.nan,
        "mae": math.nan,
        "aic": math.nan,
        "bic": math.nan,
    }
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = fit_model(data, formula_text, estimator)
        warning_text = " | ".join(sorted({str(item.message) for item in caught}))[:2000]
        summary["warnings"] = warning_text
        metrics = fit_quality_metrics(result, data)
        summary.update(metrics)
        summary["aic"] = scalar_metric(result, "aic")
        summary["bic"] = scalar_metric(result, "bic")
        coefficients = coefficient_long_frame(
            result,
            data,
            formula=formula,
            estimator=estimator,
            effort_col=effort_col,
            effort_label=effort_label,
            context_k=context_k,
        )
        predictions = fixed_prediction_grid(
            result,
            data,
            formula=formula,
            estimator=estimator,
            formula_text=formula_text,
            effort_col=effort_col,
            effort_label=effort_label,
            context_k=context_k,
            n_points=n_points,
        )
        if save_models:
            model_name = f"{context_k}_{safe_slug(effort_col)}_{formula.formula_id}_{estimator.estimator_id}.pickle"
            path, save_error = save_model_result(result, output_dir / "models" / model_name)
            summary["model_path"] = path
            summary["model_save_error"] = save_error
        else:
            try:
                result.remove_data()
            except Exception:
                pass
        return summary, coefficients, predictions, pd.DataFrame()
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        return summary, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def fixed_slice_slopes(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    keys = [
        "formula_id",
        "formula_label",
        "estimator_id",
        "estimator_label",
        "frame_kind",
        "context_k",
        "effort_col",
        "effort_label",
        "fixed_effort_value",
    ]
    for key, group in predictions.groupby(keys, sort=True, observed=True):
        ages = group["age_months"].to_numpy(dtype=float)
        bits = group["predicted_sum_bits"].to_numpy(dtype=float)
        mask = np.isfinite(ages) & np.isfinite(bits)
        slope = float(np.polyfit(ages[mask], bits[mask], 1)[0]) if mask.sum() >= 2 else math.nan
        row = dict(zip(keys, key))
        row.update(
            {
                "slope_bits_per_month": slope,
                "slope_bits_per_6_months": slope * 6 if math.isfinite(slope) else math.nan,
                "direction": "downward" if slope < 0 else "upward" if slope > 0 else "flat",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def exact_length_observed_age_bin_means(
    base: pd.DataFrame,
    *,
    context_k: str,
    effort_col: str,
    effort_label: str,
    max_length: int = 12,
) -> pd.DataFrame:
    """Return descriptive observed means within exact length and age-bin cells."""

    if base.empty:
        return pd.DataFrame()
    data = base.copy()
    data["effort_value_int"] = pd.to_numeric(data["effort_value_int"], errors="coerce")
    data = data.dropna(subset=["effort_value_int", "age_months", "sum_bits", "age_bin"]).copy()
    data["effort_value_int"] = data["effort_value_int"].astype(int)
    data = data[(data["effort_value_int"] > 0) & (data["effort_value_int"] <= max_length)].copy()
    data = data[data["age_bin"].astype(str).ne("")].copy()
    if data.empty:
        return pd.DataFrame()
    return (
        data.groupby(["age_bin", "effort_value_int"], as_index=False, observed=True)
        .agg(
            mean_age_months=("age_months", "mean"),
            mean_sum_bits=("sum_bits", "mean"),
            rows=("sum_bits", "size"),
            children=("child_id", "nunique"),
            sessions=("session_key", "nunique"),
        )
        .assign(context_k=context_k, effort_col=effort_col, effort_label=effort_label)
        .sort_values(["effort_value_int", "mean_age_months"])
        .reset_index(drop=True)
    )


def fit_stage(
    *,
    input_csv: Path,
    output_dir: Path,
    target_source: str,
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    formulas: Sequence[FormulaSpec],
    estimators: Sequence[EstimatorSpec],
    chunksize: int,
    max_rows: int | None,
    n_points: int,
    save_models: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[read] {input_csv}", flush=True)
    raw = read_route1_rows(
        input_csv,
        chunksize=chunksize,
        max_rows=max_rows,
        target_sources=(target_source,),
        context_ks=context_ks,
        roles=("child",),
    )
    audit_rows = [
        {
            "target_source": target_source,
            "context_ks": ",".join(context_ks),
            "raw_rows": int(len(raw)),
            "children": int(raw["child_id"].nunique()) if "child_id" in raw else 0,
            "raw_session_labels": int(raw["session_id"].nunique()) if "session_id" in raw else 0,
            "child_session_keys": int(
                (
                    raw.get("dataset", pd.Series("", index=raw.index)).astype(str)
                    + "::"
                    + raw.get("child_id", pd.Series("", index=raw.index)).astype(str)
                    + "::"
                    + raw.get("session_id", pd.Series("", index=raw.index)).astype(str)
                ).nunique()
            )
            if len(raw)
            else 0,
            "max_rows_argument": max_rows if max_rows is not None else "",
        }
    ]
    summary_rows: list[dict[str, object]] = []
    coefficient_parts: list[pd.DataFrame] = []
    prediction_parts: list[pd.DataFrame] = []
    observed_exact_parts: list[pd.DataFrame] = []
    base_by_effort: dict[str, pd.DataFrame] = {}
    prepared_cache: dict[tuple[str, str, str, str], tuple[pd.DataFrame, str]] = {}
    effort_specs = selected_effort_specs(effort_cols)
    for effort in effort_specs:
        print(f"[prepare] {effort.effort_col}", flush=True)
        base_by_effort[effort.effort_col] = build_child_base_frame(raw, effort.effort_col, effort.parent_context_col)
    total = len(effort_specs) * len(formulas) * len(estimators) * len(context_ks)
    fit_index = 0
    for context_k in context_ks:
        for effort in effort_specs:
            base = base_by_effort[effort.effort_col]
            if "context_k" in base.columns:
                base = base[base["context_k"].astype(str).eq(context_k)].copy()
            observed_exact = exact_length_observed_age_bin_means(
                base,
                context_k=context_k,
                effort_col=effort.effort_col,
                effort_label=effort.effort_label,
            )
            if not observed_exact.empty:
                observed_exact_parts.append(observed_exact)
            for formula in formulas:
                for estimator in estimators:
                    fit_index += 1
                    print(
                        f"[fit] {fit_index}/{total} {context_k} {effort.effort_col} {formula.formula_id} {estimator.estimator_id}",
                        flush=True,
                    )
                    key = (context_k, effort.effort_col, formula.formula_id, estimator.frame_kind)
                    if key not in prepared_cache:
                        prepared_cache[key] = prepare_analysis_frame(base, formula, estimator.frame_kind)
                    data, prepare_error = prepared_cache[key]
                    if prepare_error:
                        formula_text = statsmodels_formula(formula, estimator)
                        summary_rows.append(
                            {
                                "run_date": RUN_DATE,
                                "formula_id": formula.formula_id,
                                "formula_label": formula.label,
                                "formula_tier": formula.tier,
                                "formula_question": formula.question,
                                "estimator_id": estimator.estimator_id,
                                "estimator_label": estimator.label,
                                "frame_kind": estimator.frame_kind,
                                "model_type": estimator.model_type,
                                "covariance": estimator.covariance,
                                "context_k": context_k,
                                "effort_col": effort.effort_col,
                                "effort_label": effort.effort_label,
                                "statsmodels_formula": formula_text,
                                "readable_formula": readable_formula(formula, estimator),
                                "n_obs": int(len(data)),
                                "n_source_rows": int(data["n_source_rows"].sum()) if "n_source_rows" in data else int(len(data)),
                                "n_children": int(data["child_id"].nunique()) if "child_id" in data else 0,
                                "n_sessions": int(data["session_key"].nunique()) if "session_key" in data else 0,
                                "status": "skipped",
                                "error": prepare_error,
                                "r2_observed_fitted": math.nan,
                                "rmse": math.nan,
                                "mae": math.nan,
                                "aic": math.nan,
                                "bic": math.nan,
                                "model_path": "",
                                "model_save_error": "",
                            }
                        )
                        continue
                    summary, coefficients, predictions, _ = fit_one(
                        data,
                        formula=formula,
                        estimator=estimator,
                        effort_col=effort.effort_col,
                        effort_label=effort.effort_label,
                        context_k=context_k,
                        output_dir=output_dir,
                        n_points=n_points,
                        save_models=save_models,
                    )
                    summary_rows.append(summary)
                    if not coefficients.empty:
                        coefficient_parts.append(coefficients)
                    if not predictions.empty:
                        prediction_parts.append(predictions)
                    gc.collect()
    summary = pd.DataFrame(summary_rows)
    coefficients = pd.concat(coefficient_parts, ignore_index=True) if coefficient_parts else pd.DataFrame()
    predictions = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    slopes = fixed_slice_slopes(predictions)
    observed_exact = pd.concat(observed_exact_parts, ignore_index=True) if observed_exact_parts else pd.DataFrame()
    formula_definitions = pd.DataFrame([{**asdict(item), "terms_text": " + ".join(item.terms)} for item in formulas])
    estimator_definitions = pd.DataFrame([asdict(item) for item in estimators])
    pd.DataFrame(audit_rows).to_csv(output_dir / "fit_input_audit.csv", index=False)
    formula_definitions.to_csv(output_dir / "formula_definitions.csv", index=False)
    estimator_definitions.to_csv(output_dir / "estimator_definitions.csv", index=False)
    summary.to_csv(output_dir / "model_summary.csv", index=False)
    coefficients.to_csv(output_dir / "coefficient_long.csv", index=False)
    predictions.to_csv(output_dir / "fixed_effort_predictions.csv.gz", index=False)
    slopes.to_csv(output_dir / "fixed_slice_slopes.csv", index=False)
    observed_exact.to_csv(output_dir / "exact_length_observed_age_bin_means.csv", index=False)
    print(f"[OK] fit artifacts: {output_dir}", flush=True)


def relative_to_report(report_path: Path, figure_path: str | Path) -> str:
    try:
        return os.path.relpath(Path(figure_path).resolve(), start=report_path.parent.resolve()).replace(os.sep, "/")
    except ValueError:
        return Path(figure_path).resolve().as_posix()


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def plot_primary_fixed_lines(predictions: pd.DataFrame, *, fig_dir: Path, primary_estimator: str) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    available = set(predictions["estimator_id"].astype(str))
    estimator_id = primary_estimator if primary_estimator in available else sorted(available)[0]
    selected = predictions[predictions["estimator_id"].astype(str).eq(estimator_id)].copy()
    sns.set_theme(style="whitegrid", context="talk")
    group_cols = ["formula_id", "formula_label", "context_k", "effort_col", "effort_label", "estimator_id", "estimator_label"]
    for keys, group in selected.groupby(group_cols, sort=True, observed=True):
        formula_id, formula_label, context_k, effort_col, effort_label, estimator_id, estimator_label = keys
        values = sorted(int(value) for value in group["fixed_effort_value"].dropna().unique())
        if not values:
            continue
        palette = sns.color_palette("viridis", n_colors=len(values))
        fig, ax = plt.subplots(figsize=(9.5, 6.0))
        for color, fixed_value in zip(palette, values):
            line = group[group["fixed_effort_value"].astype(int).eq(fixed_value)].sort_values("age_months")
            ax.plot(
                line["age_months"],
                line["predicted_sum_bits"],
                linewidth=2.0,
                color=color,
                label=str(fixed_value),
            )
            if line[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                ax.fill_between(
                    line["age_months"].to_numpy(dtype=float),
                    line["pred_ci_low"].to_numpy(dtype=float),
                    line["pred_ci_high"].to_numpy(dtype=float),
                    color=color,
                    alpha=0.08,
                    linewidth=0,
                )
        ax.axhline(0, color="#3a3a3a", linewidth=0.8, alpha=0.25)
        ax.set_title(f"{formula_id}: {formula_label}")
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Predicted total bits")
        ax.legend(title=f"Fixed {effort_label.lower()}", fontsize=9, title_fontsize=10, ncol=2)
        ax.grid(alpha=0.18)
        fig.tight_layout()
        path = fig_dir / f"{formula_id.lower()}_{safe_slug(context_k)}_{safe_slug(effort_col)}_{safe_slug(estimator_id)}_fixed_effort_lines.png"
        fig.savefig(path, dpi=190, bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "figure_type": "primary_fixed_effort_lines",
                "formula_id": formula_id,
                "formula_label": formula_label,
                "context_k": context_k,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "estimator_id": estimator_id,
                "estimator_label": estimator_label,
                "figure": str(path),
                "description": "Predicted total bits by age at exact fixed effort values for the primary row-level length-controlled estimator.",
            }
        )
    return pd.DataFrame(rows)


def plot_estimator_mean_lines(predictions: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    sns.set_theme(style="whitegrid", context="talk")
    group_cols = ["formula_id", "formula_label", "context_k", "effort_col", "effort_label"]
    for keys, group in predictions.groupby(group_cols, sort=True, observed=True):
        formula_id, formula_label, context_k, effort_col, effort_label = keys
        mean_lines = (
            group.groupby(["estimator_id", "estimator_label", "age_months"], as_index=False, observed=True)["predicted_sum_bits"]
            .mean()
            .copy()
        )
        if mean_lines.empty:
            continue
        fig, ax = plt.subplots(figsize=(10.2, 6.2))
        for estimator_id, line in mean_lines.groupby("estimator_id", sort=True):
            label = str(line["estimator_label"].iloc[0])
            ax.plot(line["age_months"], line["predicted_sum_bits"], linewidth=2.0, label=label)
        ax.set_title(f"{formula_id}: estimator comparison averaged across fixed {effort_label.lower()} slices")
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Predicted total bits")
        ax.legend(fontsize=8, title="Estimator", title_fontsize=9)
        ax.grid(alpha=0.18)
        fig.tight_layout()
        path = fig_dir / f"{formula_id.lower()}_{safe_slug(context_k)}_{safe_slug(effort_col)}_estimator_mean_lines.png"
        fig.savefig(path, dpi=190, bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "figure_type": "estimator_mean_fixed_effort_lines",
                "formula_id": formula_id,
                "formula_label": formula_label,
                "context_k": context_k,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "estimator_id": "all",
                "estimator_label": "All fitted estimators",
                "figure": str(path),
                "description": "Estimator comparison after averaging predictions across the fixed-effort slices, not across raw utterance lengths.",
            }
        )
    return pd.DataFrame(rows)


def plot_slope_heatmap(slopes: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    if slopes.empty:
        return pd.DataFrame()
    summary = (
        slopes.groupby(["formula_id", "formula_label", "estimator_id"], as_index=False, observed=True)["slope_bits_per_6_months"]
        .mean()
        .copy()
    )
    if summary.empty:
        return pd.DataFrame()
    pivot = summary.pivot(index="formula_id", columns="estimator_id", values="slope_bits_per_6_months")
    order = [spec.formula_id for spec in FORMULAS if spec.formula_id in pivot.index]
    pivot = pivot.loc[order]
    fig, ax = plt.subplots(figsize=(max(9.5, 1.05 * len(pivot.columns)), max(6.2, 0.35 * len(pivot.index))))
    sns.heatmap(pivot, center=0, cmap="vlag", linewidths=0.4, linecolor="white", annot=True, fmt=".2f", ax=ax)
    ax.set_title("Mean fixed-effort age slope by formula and estimator")
    ax.set_xlabel("Estimator")
    ax.set_ylabel("Formula")
    fig.tight_layout()
    path = fig_dir / "slope_heatmap_formula_by_estimator.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "figure_type": "slope_heatmap",
                "formula_id": "all",
                "formula_label": "All formulas",
                "context_k": ",".join(sorted(slopes["context_k"].astype(str).unique())),
                "effort_col": ",".join(sorted(slopes["effort_col"].astype(str).unique())),
                "effort_label": ",".join(sorted(slopes["effort_label"].astype(str).unique())),
                "estimator_id": "all",
                "estimator_label": "All fitted estimators",
                "figure": str(path),
                "description": "Mean slope in predicted total bits per six months, averaged across fixed-effort lines.",
            }
        ]
    )


def plot_exact_length_slope_proof(slopes: pd.DataFrame, *, fig_dir: Path, primary_estimator: str) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    if slopes.empty:
        return pd.DataFrame()
    data = slopes.copy()
    data = data[data["formula_id"].isin(EXACT_LENGTH_FORMULA_IDS)].copy()
    data = data[data["estimator_id"].astype(str).eq(primary_estimator)].copy()
    data["fixed_effort_value"] = pd.to_numeric(data["fixed_effort_value"], errors="coerce")
    data["slope_bits_per_6_months"] = pd.to_numeric(data["slope_bits_per_6_months"], errors="coerce")
    data = data.dropna(subset=["fixed_effort_value", "slope_bits_per_6_months"]).copy()
    if data.empty:
        return pd.DataFrame()
    summary = (
        data.groupby(["formula_id", "formula_label", "fixed_effort_value"], as_index=False, observed=True)[
            "slope_bits_per_6_months"
        ]
        .mean()
        .sort_values(["formula_id", "fixed_effort_value"])
    )
    fig, ax = plt.subplots(figsize=(9.8, 6.0))
    sns.lineplot(
        data=summary,
        x="fixed_effort_value",
        y="slope_bits_per_6_months",
        hue="formula_id",
        marker="o",
        linewidth=2.1,
        ax=ax,
    )
    ax.axhline(0, color="#2d2d2d", linewidth=1.0, alpha=0.7)
    ax.set_title("Exact-length age slopes: MLU cannot explain same-length lines")
    ax.set_xlabel("Exact utterance length")
    ax.set_ylabel("Predicted age slope: bits per six months")
    ax.legend(title="Formula", fontsize=9, title_fontsize=10)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    path = fig_dir / "mlu_proof_exact_length_age_slopes.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "figure_type": "mlu_proof_exact_length_slopes",
                "formula_id": "F18-F21",
                "formula_label": "Exact-length formulas",
                "context_k": ",".join(sorted(data["context_k"].astype(str).unique())),
                "effort_col": ",".join(sorted(data["effort_col"].astype(str).unique())),
                "effort_label": ",".join(sorted(data["effort_label"].astype(str).unique())),
                "estimator_id": primary_estimator,
                "estimator_label": "Primary row-level child fixed-effect estimator",
                "figure": str(path),
                "description": "Age slopes estimated inside exact utterance-length comparisons. This is the direct check that the pattern is not produced by the age-related MLU shift.",
            }
        ]
    )


def plot_observed_exact_length_age_bins(observed: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    if observed.empty:
        return pd.DataFrame()
    data = observed.copy()
    for col in ["effort_value_int", "mean_age_months", "mean_sum_bits", "rows"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["effort_value_int", "mean_age_months", "mean_sum_bits"]).copy()
    data = data[data["rows"].fillna(0) >= 20].copy()
    if data.empty:
        return pd.DataFrame()
    fig, ax = plt.subplots(figsize=(10.0, 6.2))
    lengths = sorted(int(value) for value in data["effort_value_int"].unique())
    palette = sns.color_palette("viridis", n_colors=max(1, len(lengths)))
    for color, length in zip(palette, lengths):
        line = data[data["effort_value_int"].astype(int).eq(length)].sort_values("mean_age_months")
        ax.plot(
            line["mean_age_months"],
            line["mean_sum_bits"],
            marker="o",
            linewidth=1.8,
            color=color,
            label=str(length),
        )
    ax.set_title("Observed age-bin means within exact utterance lengths")
    ax.set_xlabel("Mean age in age bin")
    ax.set_ylabel("Observed mean total bits")
    ax.legend(title="Exact length", ncol=2, fontsize=8, title_fontsize=9)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    path = fig_dir / "observed_exact_length_age_bin_means.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "figure_type": "observed_exact_length_age_bins",
                "formula_id": "descriptive",
                "formula_label": "Observed exact-length age-bin means",
                "context_k": ",".join(sorted(data["context_k"].astype(str).unique())),
                "effort_col": ",".join(sorted(data["effort_col"].astype(str).unique())),
                "effort_label": ",".join(sorted(data["effort_label"].astype(str).unique())),
                "estimator_id": "none",
                "estimator_label": "Descriptive age-bin means",
                "figure": str(path),
                "description": "Model-free descriptive means within exact utterance lengths. This is a sanity check, not the adjusted inferential estimate.",
            }
        ]
    )


def plot_r2(summary: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    fitted = summary[summary["status"].astype(str).eq("fit")].copy()
    fitted["r2_observed_fitted"] = pd.to_numeric(fitted["r2_observed_fitted"], errors="coerce")
    fitted = fitted.dropna(subset=["r2_observed_fitted"])
    if fitted.empty:
        return pd.DataFrame()
    order = [spec.formula_id for spec in FORMULAS if spec.formula_id in set(fitted["formula_id"].astype(str))]
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    sns.lineplot(
        data=fitted,
        x="formula_id",
        y="r2_observed_fitted",
        hue="estimator_id",
        marker="o",
        sort=False,
        ax=ax,
    )
    ax.set_xticks(range(len(order)), order, rotation=45, ha="right")
    ax.set_title("Observed-vs-fitted variance explained by formula and estimator")
    ax.set_xlabel("Formula")
    ax.set_ylabel("R2 / pseudo-R2 on fitted data")
    ax.legend(fontsize=8, title="Estimator", title_fontsize=9)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    path = fig_dir / "variance_explained_by_formula_estimator.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "figure_type": "variance_explained",
                "formula_id": "all",
                "formula_label": "All formulas",
                "context_k": ",".join(sorted(fitted["context_k"].astype(str).unique())),
                "effort_col": ",".join(sorted(fitted["effort_col"].astype(str).unique())),
                "effort_label": ",".join(sorted(fitted["effort_label"].astype(str).unique())),
                "estimator_id": "all",
                "estimator_label": "All fitted estimators",
                "figure": str(path),
                "description": "Observed-vs-fitted variance explained. For non-OLS estimators this is descriptive, not a classical OLS R2.",
            }
        ]
    )


def plot_variable_importance(coefficients: pd.DataFrame, *, fig_dir: Path, primary_estimator: str) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    if coefficients.empty:
        return pd.DataFrame()
    data = coefficients.copy()
    data["abs_standardized_estimate"] = pd.to_numeric(data["abs_standardized_estimate"], errors="coerce")
    data = data[data["term"].isin(IMPORTANT_TERMS)].copy()
    if primary_estimator in set(data["estimator_id"].astype(str)):
        data = data[data["estimator_id"].astype(str).eq(primary_estimator)].copy()
    data = data.dropna(subset=["abs_standardized_estimate"])
    if data.empty:
        return pd.DataFrame()
    summary = (
        data.groupby("term", as_index=False, observed=True)["abs_standardized_estimate"]
        .mean()
        .sort_values("abs_standardized_estimate", ascending=False)
        .head(20)
    )
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    sns.barplot(data=summary, x="abs_standardized_estimate", y="term", color="#2f6f73", ax=ax)
    ax.set_title("Control-dominance diagnostic: standardized coefficient magnitude")
    ax.set_xlabel("Mean absolute standardized estimate")
    ax.set_ylabel("Term")
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout()
    path = fig_dir / "variable_importance_standardized_coefficients.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "figure_type": "variable_importance",
                "formula_id": "all",
                "formula_label": "All formulas",
                "context_k": ",".join(sorted(data["context_k"].astype(str).unique())),
                "effort_col": ",".join(sorted(data["effort_col"].astype(str).unique())),
                "effort_label": ",".join(sorted(data["effort_label"].astype(str).unique())),
                "estimator_id": primary_estimator if primary_estimator in set(coefficients["estimator_id"].astype(str)) else "available",
                "estimator_label": "Primary or available fitted estimator",
                "figure": str(path),
                "description": "Control-dominance diagnostic. Large effort terms are treated as evidence that raw total bits are length-confounded, not as the substantive finding.",
            }
        ]
    )


def plot_stage(*, output_dir: Path, fig_dir: Path, primary_estimator: str) -> None:
    summary_path = output_dir / "model_summary.csv"
    coef_path = output_dir / "coefficient_long.csv"
    pred_path = output_dir / "fixed_effort_predictions.csv.gz"
    slopes_path = output_dir / "fixed_slice_slopes.csv"
    observed_path = output_dir / "exact_length_observed_age_bin_means.csv"
    missing = [path for path in [summary_path, coef_path, pred_path, slopes_path] if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing fit artifacts for plot stage: {missing}")
    summary = read_csv_or_empty(summary_path)
    coefficients = read_csv_or_empty(coef_path)
    predictions = read_csv_or_empty(pred_path)
    slopes = read_csv_or_empty(slopes_path)
    observed_exact = read_csv_or_empty(observed_path) if observed_path.exists() else pd.DataFrame()
    parts = [
        plot_observed_exact_length_age_bins(observed_exact, fig_dir=fig_dir),
        plot_exact_length_slope_proof(slopes, fig_dir=fig_dir, primary_estimator=primary_estimator),
        plot_primary_fixed_lines(predictions, fig_dir=fig_dir, primary_estimator=primary_estimator),
        plot_estimator_mean_lines(predictions, fig_dir=fig_dir),
        plot_slope_heatmap(slopes, fig_dir=fig_dir),
        plot_r2(summary, fig_dir=fig_dir),
        plot_variable_importance(coefficients, fig_dir=fig_dir, primary_estimator=primary_estimator),
    ]
    nonempty_parts = [part for part in parts if not part.empty]
    manifest = pd.concat(nonempty_parts, ignore_index=True) if nonempty_parts else pd.DataFrame()
    manifest.to_csv(output_dir / "figure_manifest.csv", index=False)
    print(f"[OK] figures: {fig_dir}", flush=True)


def report_formula_section(formulas: pd.DataFrame) -> list[str]:
    lines = ["## Formula Guide", ""]
    order = {spec.formula_id: idx for idx, spec in enumerate(FORMULAS)}
    formulas = formulas.copy()
    formulas["_order"] = formulas["formula_id"].map(order).fillna(len(order))
    for row in formulas.sort_values(["_order", "formula_id"]).to_dict("records"):
        terms_text = str(row.get("terms_text") or row.get("terms") or "").strip()
        lines.extend(
            [
                f"### {row['formula_id']}: {row['label']}",
                "",
                f"**Question.** {row['question']}",
                "",
                f"**Formula.** `sum_bits ~ {terms_text}`",
                "",
                f"**Meaning.** {row['explanation']}",
                "",
                "**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.",
                "",
            ]
        )
    return lines


def report_estimator_section(estimators: pd.DataFrame) -> list[str]:
    lines = ["## Estimator Guide", ""]
    order = {spec.estimator_id: idx for idx, spec in enumerate(ESTIMATORS)}
    estimators = estimators.copy()
    estimators["_order"] = estimators["estimator_id"].map(order).fillna(len(order))
    for row in estimators.sort_values(["_order", "estimator_id"]).to_dict("records"):
        lines.extend(
            [
                f"### {row['estimator_id']}",
                "",
                f"**Model.** {row['label']}",
                "",
                f"**What it does.** {row['explanation']}",
                "",
                f"**Why it is here.** {row['why_use']}",
                "",
                f"**Data scale.** `{row['frame_kind']}`. **Covariance/dependence structure.** `{row['covariance']}`.",
                "",
            ]
        )
    return lines


def summarize_fit_text(summary: pd.DataFrame, slopes: pd.DataFrame, observed_exact: pd.DataFrame | None = None) -> list[str]:
    fitted = summary[summary["status"].astype(str).eq("fit")].copy()
    failed = summary[~summary["status"].astype(str).eq("fit")].copy()
    lines = [
        "## Run Summary",
        "",
        f"- Requested model fits: `{len(summary):,}`.",
        f"- Successful fits: `{len(fitted):,}`.",
        f"- Skipped or failed fits: `{len(failed):,}`. Details are saved in `model_summary.csv`.",
    ]
    if not fitted.empty:
        lines.extend(
            [
                f"- Children represented in successful fits: `{int(fitted['n_children'].max()):,}`.",
                f"- Sessions represented in successful fits: `{int(fitted['n_sessions'].max()):,}`.",
                f"- Observation/cell count range across successful fits: `{int(fitted['n_obs'].min()):,}` to `{int(fitted['n_obs'].max()):,}`.",
            ]
        )
    if not slopes.empty:
        slope_values = pd.to_numeric(slopes["slope_bits_per_6_months"], errors="coerce").dropna()
        if not slope_values.empty:
            lines.extend(
                [
                    f"- Mean fixed-effort age slope across saved prediction lines: `{float(slope_values.mean()):.3f}` bits per six months.",
                    f"- Downward fixed-effort lines: `{int((slope_values < 0).sum()):,}`; upward fixed-effort lines: `{int((slope_values > 0).sum()):,}`.",
                ]
            )
        exact = slopes[
            slopes["formula_id"].isin(EXACT_LENGTH_FORMULA_IDS)
            & slopes["estimator_id"].astype(str).eq("row_ols_fe_cluster")
        ].copy()
        if not exact.empty:
            exact_values = pd.to_numeric(exact["slope_bits_per_6_months"], errors="coerce").dropna()
            upward_lengths = sorted(
                {
                    int(value)
                    for value in pd.to_numeric(
                        exact.loc[exact["direction"].astype(str).eq("upward"), "fixed_effort_value"],
                        errors="coerce",
                    ).dropna()
                }
            )
            lines.extend(
                [
                    f"- Primary exact-length slopes from F18-F21: `{int((exact_values < 0).sum()):,}` downward and `{int((exact_values > 0).sum()):,}` upward.",
                    f"- Upward primary exact-length slopes occur at exact lengths: `{', '.join(str(value) for value in upward_lengths) if upward_lengths else 'none'}`.",
                ]
            )
    if observed_exact is not None and not observed_exact.empty:
        support = observed_exact.copy()
        support["rows"] = pd.to_numeric(support["rows"], errors="coerce")
        support["effort_value_int"] = pd.to_numeric(support["effort_value_int"], errors="coerce")
        support = support.dropna(subset=["rows", "effort_value_int"])
        if not support.empty:
            by_length = support.groupby("effort_value_int", as_index=False, observed=True)["rows"].sum()
            sparse = by_length[by_length["effort_value_int"].isin([10, 11, 12])]
            if not sparse.empty:
                sparse_text = ", ".join(
                    f"{int(row.effort_value_int)} words={int(row.rows):,} rows" for row in sparse.itertuples(index=False)
                )
                lines.append(f"- The longest exact lengths are much sparser and should be read cautiously: {sparse_text}.")
    lines.append("")
    return lines


def report_figure_section(manifest: pd.DataFrame, report_path: Path) -> list[str]:
    lines = ["## Regression Plots", ""]
    if manifest.empty:
        return lines + ["_No figures were available. Run the plot stage first._", ""]
    priority = [
        "observed_exact_length_age_bins",
        "mlu_proof_exact_length_slopes",
        "slope_heatmap",
        "variance_explained",
        "variable_importance",
    ]
    for figure_type in priority:
        for row in manifest[manifest["figure_type"].astype(str).eq(figure_type)].to_dict("records"):
            rel = relative_to_report(report_path, row["figure"])
            lines.extend([f"### {row['description']}", "", f"![{row['figure_type']}]({rel})", ""])
    primary = manifest[manifest["figure_type"].astype(str).eq("primary_fixed_effort_lines")].copy()
    if not primary.empty:
        lines.extend(
            [
                "### Primary fixed-effort lines",
                "",
                "Each line is a model prediction at one exact utterance size. A downward line means predicted total bits decline with age when that size is held fixed. These are the key plots for separating communicative informativeness from raw MLU growth.",
                "",
            ]
        )
        for row in primary.sort_values(["formula_id", "effort_label"]).to_dict("records"):
            rel = relative_to_report(report_path, row["figure"])
            lines.extend([f"**{row['formula_id']}: {row['formula_label']}**", "", f"![{row['formula_id']}]({rel})", ""])
    estimator_lines = manifest[manifest["figure_type"].astype(str).eq("estimator_mean_fixed_effort_lines")].copy()
    if not estimator_lines.empty:
        lines.extend(
            [
                "### Estimator comparison lines",
                "",
                "These lines average over the plotted fixed-effort slices. This is the defensible version of a global effect across lengths: it is model-adjusted and length-controlled, not a raw mean over utterances of different sizes.",
                "",
            ]
        )
        for row in estimator_lines.sort_values(["formula_id", "effort_label"]).to_dict("records"):
            rel = relative_to_report(report_path, row["figure"])
            lines.extend([f"**{row['formula_id']}: {row['formula_label']}**", "", f"![{row['formula_id']} estimator comparison]({rel})", ""])
    return lines


def build_report(
    *,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
) -> None:
    required = {
        "summary": output_dir / "model_summary.csv",
        "coefficients": output_dir / "coefficient_long.csv",
        "predictions": output_dir / "fixed_effort_predictions.csv.gz",
        "slopes": output_dir / "fixed_slice_slopes.csv",
        "observed_exact": output_dir / "exact_length_observed_age_bin_means.csv",
        "formulas": output_dir / "formula_definitions.csv",
        "estimators": output_dir / "estimator_definitions.csv",
        "figures": output_dir / "figure_manifest.csv",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing artifacts for report stage: {missing}")
    summary = read_csv_or_empty(required["summary"])
    slopes = read_csv_or_empty(required["slopes"])
    observed_exact = read_csv_or_empty(required["observed_exact"])
    formulas = read_csv_or_empty(required["formulas"])
    estimators = read_csv_or_empty(required["estimators"])
    manifest = read_csv_or_empty(required["figures"])
    lines: list[str] = [
        "# Child Informativeness At Fixed Utterance Effort",
        "",
        f"Generated on {RUN_DATE}.",
        "",
        "This report is the child-only Route 1 modeling suite. The outcome is `sum_bits`, meaning total model-estimated information in the child utterance. Every scientific formula includes an explicit target-effort control or exact-length category control, because raw total bits are structurally entangled with utterance length and child MLU increases with age.",
        "",
        "The report deliberately emphasizes regression-line plots rather than tables. The CSV artifacts contain the exact coefficients, p-values, fit metrics, fixed-effort prediction grids, and saved model paths.",
        "",
        "## Scientific Contract",
        "",
        "- We are not asking whether older children talk more. They do.",
        "- We are asking whether, for utterances of the same size, older children produce utterances with more or less information.",
        "- The fixed-effort lines are the main evidence because they hold utterance size constant.",
        "- The exact-length formulas are the strongest MLU check because MLU cannot explain an age slope estimated inside one exact utterance length.",
        "- A global age effect across lengths is interpretable only when it is model-adjusted or averaged over fixed-effort slices. A raw average across utterances would mostly rediscover MLU.",
        "- Repeated utterances from the same children and sessions motivate GEE and mixed-model checks, not only OLS.",
        "",
        "## Why This Is Not Just MLU",
        "",
        "MLU is a change in the distribution of utterance lengths with age. The exact-length models remove that explanation by estimating age patterns while length is either fixed in the plotted slice or represented by exact length categories. In a two-word comparison, every utterance has two words; in a three-word comparison, every utterance has three words. MLU can change how often those lengths occur, but it cannot by itself create a developmental slope inside a fixed-length comparison.",
        "",
        "## Statistical Strategy",
        "",
        "Utterances are repeated observations nested in sessions and children. The estimator grid therefore includes a transparent row-level child fixed-effect model, session/exact-effort aggregate checks, GEE models grouped by child, Gamma/log positive-outcome checks, and mixed models with child and session random-effect structures. These are sensitivity layers around the same length-controlled scientific contrast.",
        "",
    ]
    lines.extend(summarize_fit_text(summary, slopes, observed_exact))
    lines.extend(report_formula_section(formulas))
    lines.extend(report_estimator_section(estimators))
    lines.extend(report_figure_section(manifest, report_md))
    lines.extend(
        [
            "## Saved Artifacts",
            "",
            "The reusable model memory for this run is saved on disk:",
            "",
            "```text",
            str(output_dir / "model_summary.csv"),
            str(output_dir / "coefficient_long.csv"),
            str(output_dir / "fixed_effort_predictions.csv.gz"),
            str(output_dir / "fixed_slice_slopes.csv"),
            str(output_dir / "exact_length_observed_age_bin_means.csv"),
            str(output_dir / "formula_definitions.csv"),
            str(output_dir / "estimator_definitions.csv"),
            str(output_dir / "models"),
            str(fig_dir),
            "```",
            "",
            "To regenerate only one layer later:",
            "",
            "```bash",
            ".venv/bin/python src/build_route1_child_length_controlled_model_suite.py --stage fit",
            ".venv/bin/python src/build_route1_child_length_controlled_model_suite.py --stage plot",
            ".venv/bin/python src/build_route1_child_length_controlled_model_suite.py --stage report",
            "```",
            "",
        ]
    )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines), encoding="utf-8")
    render_markdown_file(report_md, report_html)
    print(f"[OK] report: {report_md}", flush=True)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["all", "fit", "plot", "report"], default="all")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--target-source", default="real")
    parser.add_argument("--context-ks", default="k3")
    parser.add_argument("--effort-cols", default="nb_words")
    parser.add_argument("--formula-ids", default="all")
    parser.add_argument("--estimators", default="all")
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--n-points", type=int, default=60)
    parser.add_argument("--primary-estimator", default="row_ols_fe_cluster")
    parser.add_argument("--no-save-models", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    formulas = selected_formulas(split_csv(args.formula_ids))
    estimators = selected_estimators(split_csv(args.estimators))
    context_ks = split_csv(args.context_ks)
    effort_cols = split_csv(args.effort_cols)
    if args.stage in {"all", "fit"}:
        fit_stage(
            input_csv=args.input,
            output_dir=args.output_dir,
            target_source=args.target_source,
            context_ks=context_ks,
            effort_cols=effort_cols,
            formulas=formulas,
            estimators=estimators,
            chunksize=args.chunksize,
            max_rows=args.max_rows,
            n_points=args.n_points,
            save_models=not args.no_save_models,
        )
    if args.stage in {"all", "plot"}:
        plot_stage(output_dir=args.output_dir, fig_dir=args.fig_dir, primary_estimator=args.primary_estimator)
    if args.stage in {"all", "report"}:
        build_report(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            report_md=args.report_md,
            report_html=args.report_html,
        )


if __name__ == "__main__":
    main()
