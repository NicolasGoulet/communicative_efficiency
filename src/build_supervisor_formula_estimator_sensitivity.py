#!/usr/bin/env python3
"""Fit the current supervisor formulas with repeated-measures estimators.

This is deliberately narrower than the larger Route 1 model atlas. It only
uses the four formulas currently discussed in the supervisor-facing report,
with word count as the effort measure:

M1: sum_bits ~ age + effort
M2: sum_bits ~ age + effort + child identity
M3: sum_bits ~ age + effort + age:effort + child identity
M4: sum_bits ~ age + effort + age:effort
               + parent context effort + context entropy + child identity

For mixed models, child identity is represented as a random child intercept
instead of fixed `C(child_id)`. That is the estimator adaptation.

No estimator in this report uses a session indicator or session random
intercept. The aggregate sensitivity estimators collapse repeated utterances
into child-age-exact-word cells, not session-ID cells.
"""

from __future__ import annotations

import argparse
import gc
import math
import os
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_route1_child_length_controlled_model_suite import (
        EstimatorSpec,
        FormulaSpec,
        build_child_base_frame,
        center_frame,
        coefficient_long_frame,
        fit_model,
        fit_quality_metrics,
        fixed_prediction_grid,
        fixed_slice_slopes,
        formula_needs_columns,
        prepare_analysis_frame,
        safe_slug,
        scalar_metric,
    )
    from build_route1_corrected_baseline_atlas import EFFORT_SPECS, QUESTION_TYPE_ORDER, read_route1_rows
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_child_length_controlled_model_suite import (
        EstimatorSpec,
        FormulaSpec,
        build_child_base_frame,
        center_frame,
        coefficient_long_frame,
        fit_model,
        fit_quality_metrics,
        fixed_prediction_grid,
        fixed_slice_slopes,
        formula_needs_columns,
        prepare_analysis_frame,
        safe_slug,
        scalar_metric,
    )
    from src.build_route1_corrected_baseline_atlas import EFFORT_SPECS, QUESTION_TYPE_ORDER, read_route1_rows
    from src.render_markdown_report import render_markdown_file


RUN_DATE = datetime.now().strftime("%Y-%m-%d")
DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/supervisor_formula_estimator_sensitivity")
DEFAULT_FIG_DIR = Path("figs/supervisor_formula_estimator_sensitivity")
DEFAULT_DOC_MD = Path("docs/supervisor_formula_estimator_sensitivity_report.md")
DEFAULT_DOC_HTML = Path("docs/supervisor_formula_estimator_sensitivity_report.html")

WORD_EFFORT_COL = "nb_words"
PARENT_WORD_CONTEXT_COL = "parent_context_nb_words"


@dataclass(frozen=True)
class SupervisorFormula:
    """One current supervisor formula plus its child-identity contract."""

    spec: FormulaSpec
    child_identity: bool
    supervisor_formula: str
    report_read: str


SUPERVISOR_FORMULAS: tuple[SupervisorFormula, ...] = (
    SupervisorFormula(
        FormulaSpec(
            "M1",
            "Only controlling for effort",
            ("age_c", "effort_c"),
            "Does age predict total bits after word count is controlled, before child identity is handled?",
            "This is intentionally naive: it controls target utterance size but not stable child identity.",
        ),
        child_identity=False,
        supervisor_formula="sum_bits ~ age + effort",
        report_read="Naive effort-control baseline.",
    ),
    SupervisorFormula(
        FormulaSpec(
            "M2",
            "Effort plus child identity",
            ("age_c", "effort_c"),
            "Does age predict total bits after word count and child identity are controlled?",
            "This is the core fixed-effort child-identity model.",
        ),
        child_identity=True,
        supervisor_formula="sum_bits ~ age + effort + child identity",
        report_read="Core child-controlled fixed-effort model.",
    ),
    SupervisorFormula(
        FormulaSpec(
            "M3",
            "Age by effort plus child identity",
            ("age_c", "effort_c", "age_c:effort_c"),
            "Does the fixed-effort age effect depend on utterance size?",
            "This keeps the child-controlled fixed-effort model and lets the age slope vary by effort.",
        ),
        child_identity=True,
        supervisor_formula="sum_bits ~ age + effort + age:effort + child identity",
        report_read="Current age-by-effort supervisor model.",
    ),
    SupervisorFormula(
        FormulaSpec(
            "M4",
            "Both context controls, no question type",
            ("age_c", "effort_c", "age_c:effort_c", "parent_context_effort_c", "context_entropy_c"),
            "Does the M3 pattern remain after parent-context effort and context entropy are controlled?",
            "This is the no-question union context formula currently used in the supervisor report.",
            needs_parent_context_effort=True,
            needs_context_entropy=True,
        ),
        child_identity=True,
        supervisor_formula=(
            "sum_bits ~ age + effort + age:effort + parent context effort "
            "+ context entropy + child identity"
        ),
        report_read="Exact current no-question M4 union context model.",
    ),
)


M1_ESTIMATORS: tuple[EstimatorSpec, ...] = (
    EstimatorSpec(
        "row_ols_plain",
        "Row-level OLS, model-based SE",
        "row",
        "ols",
        "model_based",
        explanation="Naive utterance-level OLS. This matches the intentionally incomplete M1 mean formula.",
        why_use="It is the plain baseline the report says is not sufficient.",
    ),
    EstimatorSpec(
        "row_ols_cluster",
        "Row-level OLS with child-clustered SE",
        "row",
        "ols",
        "cluster_child",
        explanation="Same M1 mean formula, but uncertainty is clustered by child.",
        why_use="This keeps the M1 mean formula while acknowledging repeated utterances for uncertainty.",
    ),
    EstimatorSpec(
        "age_word_ols_cluster",
        "Child-age-word-cell OLS with child-clustered SE",
        "child_age_word",
        "ols",
        "cluster_child",
        explanation="Same M1 mean formula after aggregating repeated rows into child-age-exact-word cells.",
        why_use="This checks whether M1 is dominated by high-row-count ages.",
    ),
    EstimatorSpec(
        "age_word_gee_gaussian",
        "Child-age-word-cell Gaussian GEE grouped by child",
        "child_age_word",
        "gee_gaussian",
        "exchangeable_child",
        explanation="Same M1 mean formula with population-average within-child correlation.",
        why_use="This is a repeated-measures version of the effort-only mean model.",
    ),
    EstimatorSpec(
        "age_word_gee_gamma_log",
        "Child-age-word-cell Gamma/log GEE grouped by child",
        "child_age_word",
        "gee_gamma_log",
        "exchangeable_child",
        explanation="Same M1 predictors with a positive-skew Gamma/log outcome model.",
        why_use="This checks whether M1 depends on Gaussian errors for positive total bits.",
    ),
)


CHILD_IDENTITY_ESTIMATORS: tuple[EstimatorSpec, ...] = (
    EstimatorSpec(
        "row_ols_fe_cluster",
        "Row-level OLS + child fixed effects + child-clustered SE",
        "row",
        "ols",
        "cluster_child",
        adds_child_fixed_effects=True,
        explanation="Supervisor-style row-level model with `C(child_id)` and child-clustered uncertainty.",
        why_use="This is the current transparent main estimator.",
    ),
    EstimatorSpec(
        "age_word_ols_fe_cluster",
        "Child-age-word-cell OLS + child fixed effects + child-clustered SE",
        "child_age_word",
        "ols",
        "cluster_child",
        adds_child_fixed_effects=True,
        explanation="Same fixed-effect mean formula after aggregating utterances into child-age-exact-word cells.",
        why_use="This reduces domination by high-row-count ages without adding a session indicator.",
    ),
    EstimatorSpec(
        "age_word_gee_gaussian_fe",
        "Child-age-word-cell Gaussian GEE + child fixed effects",
        "child_age_word",
        "gee_gaussian",
        "exchangeable_child",
        adds_child_fixed_effects=True,
        explanation="Population-average repeated-measures estimator with `C(child_id)` still in the mean model.",
        why_use="This keeps child identity in the formula and models within-child dependence.",
    ),
    EstimatorSpec(
        "age_word_gee_gamma_log_fe",
        "Child-age-word-cell Gamma/log GEE + child fixed effects",
        "child_age_word",
        "gee_gamma_log",
        "exchangeable_child",
        adds_child_fixed_effects=True,
        explanation="Positive-skew repeated-measures estimator with `C(child_id)` still in the mean model.",
        why_use="This checks whether the child-controlled result depends on Gaussian errors.",
    ),
    EstimatorSpec(
        "age_word_mixed_random_intercept",
        "Child-age-word-cell MixedLM with random child intercept",
        "child_age_word",
        "mixedlm",
        "random_child_intercept",
        random_effects="1",
        explanation="Adapts child identity from fixed `C(child_id)` to a random child intercept.",
        why_use="This is the standard mixed-model representation of repeated child measurements.",
    ),
)


def formula_estimator_pairs() -> list[tuple[SupervisorFormula, EstimatorSpec]]:
    """Return the exact M1-M4 estimator plan."""

    pairs: list[tuple[SupervisorFormula, EstimatorSpec]] = []
    for formula in SUPERVISOR_FORMULAS:
        estimators = CHILD_IDENTITY_ESTIMATORS if formula.child_identity else M1_ESTIMATORS
        pairs.extend((formula, estimator) for estimator in estimators)
    return pairs


def statsmodels_formula(formula: SupervisorFormula, estimator: EstimatorSpec) -> str:
    terms = list(formula.spec.terms)
    if formula.child_identity and estimator.adds_child_fixed_effects:
        terms.append("C(child_id)")
    return "route1_outcome ~ " + " + ".join(terms)


def readable_formula(formula: SupervisorFormula, estimator: EstimatorSpec) -> str:
    text = statsmodels_formula(formula, estimator)
    return (
        text.replace("route1_outcome", "sum_bits")
        .replace("age_c", "age")
        .replace("effort_c", "target_effort")
        .replace("parent_context_effort_c", "parent_context_effort")
        .replace("context_entropy_c", "context_entropy")
    )


def adaptation_note(formula: SupervisorFormula, estimator: EstimatorSpec) -> str:
    if not formula.child_identity and estimator.model_type == "mixedlm":
        return "M1 predictors with added random child intercept for the mixed repeated-measures estimator."
    if formula.child_identity and estimator.adds_child_fixed_effects:
        return "Exact child-identity formula using fixed child intercepts."
    if formula.child_identity and estimator.model_type == "mixedlm":
        return "Child identity adapted from fixed intercepts to random child intercepts."
    return "Exact fixed-effect mean formula; child grouping only affects uncertainty/correlation."


def aggregate_child_age_word_cells(data: pd.DataFrame) -> pd.DataFrame:
    """Average repeated utterances in child-age-exact-word cells.

    This intentionally does not group by `session_id` or add any session
    indicator. Age is already the developmental timestamp, so session IDs should
    not be added as another model structure for this sensitivity report.
    """

    group_cols = [
        "dataset",
        "child_id",
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
    grouped["session_key"] = (
        grouped["child_id"].astype(str)
        + "::age="
        + grouped["age_months"].round(4).astype(str)
        + "::words="
        + grouped["effort_value_int"].astype(str)
    )
    return grouped


def prepare_supervisor_analysis_frame(base: pd.DataFrame, formula: FormulaSpec, frame_kind: str) -> tuple[pd.DataFrame, str]:
    """Prepare row or child-age-word-cell frames without session-level terms."""

    if frame_kind == "row":
        return prepare_analysis_frame(base, formula, frame_kind)
    if frame_kind != "child_age_word":
        return base.copy(), f"unknown frame kind: {frame_kind}"

    required = formula_needs_columns(formula)
    data = base.copy()
    data = data.dropna(subset=[col for col in required if col in data.columns]).copy()
    if formula.needs_context_entropy:
        data = data[data["context_entropy_bits"] > 0].copy()
    if data.empty:
        return data, "no complete rows"

    data = aggregate_child_age_word_cells(data)
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
    return data.reset_index(drop=True), ""


def relative_to_report(report_path: Path, figure_path: str | Path) -> str:
    try:
        return os.path.relpath(Path(figure_path).resolve(), start=report_path.parent.resolve()).replace(os.sep, "/")
    except ValueError:
        return Path(figure_path).resolve().as_posix()


def fit_one_supervisor_formula(
    data: pd.DataFrame,
    *,
    formula: SupervisorFormula,
    estimator: EstimatorSpec,
    output_dir: Path,
    n_points: int,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    formula_text = statsmodels_formula(formula, estimator)
    summary: dict[str, object] = {
        "run_date": RUN_DATE,
        "formula_id": formula.spec.formula_id,
        "formula_label": formula.spec.label,
        "supervisor_formula": formula.supervisor_formula,
        "estimator_id": estimator.estimator_id,
        "estimator_label": estimator.label,
        "frame_kind": estimator.frame_kind,
        "model_type": estimator.model_type,
        "covariance": estimator.covariance,
        "adaptation_note": adaptation_note(formula, estimator),
        "context_k": "k3",
        "effort_col": WORD_EFFORT_COL,
        "effort_label": "Words",
        "statsmodels_formula": formula_text,
        "readable_formula": readable_formula(formula, estimator),
        "n_obs": int(len(data)),
        "n_source_rows": int(data["n_source_rows"].sum()) if "n_source_rows" in data else int(len(data)),
        "n_children": int(data["child_id"].nunique()) if "child_id" in data else 0,
        "n_sessions": int(data["session_key"].nunique()) if "session_key" in data else 0,
        "age_min": float(data["age_months"].min()) if len(data) else math.nan,
        "age_max": float(data["age_months"].max()) if len(data) else math.nan,
        "status": "fit",
        "error": "",
        "r2_observed_fitted": math.nan,
        "rmse": math.nan,
        "mae": math.nan,
        "aic": math.nan,
        "bic": math.nan,
        "warnings": "",
    }
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = fit_model(data, formula_text, estimator)
        summary["warnings"] = " | ".join(sorted({str(item.message) for item in caught}))[:2000]
        summary.update(fit_quality_metrics(result, data))
        summary["aic"] = scalar_metric(result, "aic")
        summary["bic"] = scalar_metric(result, "bic")
        coefficients = coefficient_long_frame(
            result,
            data,
            formula=formula.spec,
            estimator=estimator,
            effort_col=WORD_EFFORT_COL,
            effort_label="Words",
            context_k="k3",
        )
        predictions = fixed_prediction_grid(
            result,
            data,
            formula=formula.spec,
            estimator=estimator,
            formula_text=formula_text,
            effort_col=WORD_EFFORT_COL,
            effort_label="Words",
            context_k="k3",
            n_points=n_points,
        )
        try:
            result.remove_data()
        except Exception:
            pass
        return summary, coefficients, predictions
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        return summary, pd.DataFrame(), pd.DataFrame()


def load_base_frame(input_csv: Path, *, chunksize: int, max_rows: int | None) -> pd.DataFrame:
    print(f"[read] {input_csv}", flush=True)
    raw = read_route1_rows(
        input_csv,
        chunksize=chunksize,
        max_rows=max_rows,
        target_sources=("real",),
        context_ks=("k3",),
        roles=("child",),
    )
    if raw.empty:
        raise RuntimeError("No real child k3 rows found.")
    print(f"[read] rows={len(raw):,} children={raw['child_id'].nunique() if 'child_id' in raw else 'NA'}", flush=True)
    print("[prepare] word-effort base frame", flush=True)
    base = build_child_base_frame(raw, WORD_EFFORT_COL, PARENT_WORD_CONTEXT_COL)
    print(f"[prepare] rows={len(base):,} children={base['child_id'].nunique() if 'child_id' in base else 'NA'}", flush=True)
    return base


def fit_stage(
    *,
    input_csv: Path,
    output_dir: Path,
    chunksize: int,
    max_rows: int | None,
    n_points: int,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = load_base_frame(input_csv, chunksize=chunksize, max_rows=max_rows)
    base = base[base["context_k"].astype(str).eq("k3")].copy()
    summary_rows: list[dict[str, object]] = []
    coefficient_parts: list[pd.DataFrame] = []
    prediction_parts: list[pd.DataFrame] = []
    prepared_cache: dict[tuple[str, str], tuple[pd.DataFrame, str]] = {}
    pairs = formula_estimator_pairs()
    for idx, (formula, estimator) in enumerate(pairs, start=1):
        print(f"[fit] {idx}/{len(pairs)} {formula.spec.formula_id} {estimator.estimator_id}", flush=True)
        key = (formula.spec.formula_id, estimator.frame_kind)
        if key not in prepared_cache:
            prepared_cache[key] = prepare_supervisor_analysis_frame(base, formula.spec, estimator.frame_kind)
        data, prepare_error = prepared_cache[key]
        if prepare_error:
            summary_rows.append(
                {
                    "run_date": RUN_DATE,
                    "formula_id": formula.spec.formula_id,
                    "formula_label": formula.spec.label,
                    "supervisor_formula": formula.supervisor_formula,
                    "estimator_id": estimator.estimator_id,
                    "estimator_label": estimator.label,
                    "frame_kind": estimator.frame_kind,
                    "model_type": estimator.model_type,
                    "covariance": estimator.covariance,
                    "adaptation_note": adaptation_note(formula, estimator),
                    "context_k": "k3",
                    "effort_col": WORD_EFFORT_COL,
                    "effort_label": "Words",
                    "statsmodels_formula": statsmodels_formula(formula, estimator),
                    "readable_formula": readable_formula(formula, estimator),
                    "n_obs": int(len(data)),
                    "n_source_rows": int(data["n_source_rows"].sum()) if "n_source_rows" in data else int(len(data)),
                    "n_children": int(data["child_id"].nunique()) if "child_id" in data else 0,
                    "n_sessions": int(data["session_key"].nunique()) if "session_key" in data else 0,
                    "status": "skipped",
                    "error": prepare_error,
                }
            )
            continue
        row, coefficients, predictions = fit_one_supervisor_formula(
            data,
            formula=formula,
            estimator=estimator,
            output_dir=output_dir,
            n_points=n_points,
        )
        summary_rows.append(row)
        if not coefficients.empty:
            coefficient_parts.append(coefficients)
        if not predictions.empty:
            prediction_parts.append(predictions)
        gc.collect()
    summary = pd.DataFrame(summary_rows)
    coefficients = pd.concat(coefficient_parts, ignore_index=True) if coefficient_parts else pd.DataFrame()
    predictions = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    slopes = fixed_slice_slopes(predictions)
    formula_defs = pd.DataFrame(
        [
            {
                "formula_id": item.spec.formula_id,
                "formula_label": item.spec.label,
                "supervisor_formula": item.supervisor_formula,
                "terms_text": " + ".join(item.spec.terms),
                "child_identity": item.child_identity,
                "report_read": item.report_read,
            }
            for item in SUPERVISOR_FORMULAS
        ]
    )
    estimator_defs = pd.DataFrame(
        [
            {
                "formula_group": "M1" if estimator in M1_ESTIMATORS else "M2-M4",
                "estimator_id": estimator.estimator_id,
                "estimator_label": estimator.label,
                "frame_kind": estimator.frame_kind,
                "model_type": estimator.model_type,
                "covariance": estimator.covariance,
                "adds_child_fixed_effects": estimator.adds_child_fixed_effects,
                "random_effects": estimator.random_effects,
                "session_variance_component": estimator.session_variance_component,
                "explanation": estimator.explanation,
                "why_use": estimator.why_use,
            }
            for estimator in (*M1_ESTIMATORS, *CHILD_IDENTITY_ESTIMATORS)
        ]
    ).drop_duplicates(subset=["formula_group", "estimator_id"])
    paths = {
        "summary": output_dir / "model_summary.csv",
        "coefficients": output_dir / "coefficient_long.csv",
        "predictions": output_dir / "fixed_effort_predictions.csv.gz",
        "slopes": output_dir / "fixed_slice_slopes.csv",
        "formulas": output_dir / "formula_definitions.csv",
        "estimators": output_dir / "estimator_definitions.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    coefficients.to_csv(paths["coefficients"], index=False)
    predictions.to_csv(paths["predictions"], index=False)
    slopes.to_csv(paths["slopes"], index=False)
    formula_defs.to_csv(paths["formulas"], index=False)
    estimator_defs.to_csv(paths["estimators"], index=False)
    return paths


def representative_slope_table(slopes: pd.DataFrame) -> pd.DataFrame:
    if slopes.empty:
        return pd.DataFrame()
    data = slopes.copy()
    data["fixed_effort_value"] = pd.to_numeric(data["fixed_effort_value"], errors="coerce")
    data = data[data["fixed_effort_value"].isin([2, 6, 10])].copy()
    table = data.pivot_table(
        index=["formula_id", "estimator_id"],
        columns="fixed_effort_value",
        values="slope_bits_per_6_months",
        aggfunc="mean",
    ).reset_index()
    table.columns = [str(col).replace(".0", "") for col in table.columns]
    return table.sort_values(["formula_id", "estimator_id"]).reset_index(drop=True)


def plot_estimator_fixed_effort_panels(predictions: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    if predictions.empty:
        return pd.DataFrame()
    sns.set_theme(style="whitegrid", context="talk")
    rows: list[dict[str, object]] = []
    fixed_values = list(range(1, 13))
    palette = sns.color_palette("viridis", n_colors=len(fixed_values))
    color_map = dict(zip(fixed_values, palette))
    for formula_id, group in predictions.groupby("formula_id", sort=True, observed=True):
        group = group[group["fixed_effort_value"].astype(int).isin(fixed_values)].copy()
        if group.empty:
            continue
        estimator_ids = list(dict.fromkeys(group["estimator_id"].astype(str).tolist()))
        ncols = 3
        nrows = math.ceil(len(estimator_ids) / ncols)
        fig, axes = plt.subplots(nrows, ncols, figsize=(16.2, 4.9 * nrows), sharex=True, sharey=True)
        flat_axes = list(axes.flat if hasattr(axes, "flat") else [axes])
        for ax, estimator_id in zip(flat_axes, estimator_ids):
            estimator_data = group[group["estimator_id"].astype(str).eq(estimator_id)]
            estimator_label = str(estimator_data["estimator_label"].iloc[0])
            for fixed_value in fixed_values:
                line = estimator_data[estimator_data["fixed_effort_value"].astype(int).eq(fixed_value)].sort_values(
                    "age_months"
                )
                if line.empty:
                    continue
                ax.plot(
                    line["age_months"],
                    line["predicted_sum_bits"],
                    color=color_map[fixed_value],
                    linewidth=1.65,
                    label=str(fixed_value),
                )
            ax.set_title(estimator_label, fontsize=12)
            ax.set_xlabel("Age in months")
            ax.set_ylabel("Predicted total bits")
            ax.grid(alpha=0.20)
        for ax in flat_axes[len(estimator_ids) :]:
            ax.axis("off")
        handles, labels = flat_axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, title="Fixed words", loc="lower center", ncol=12, frameon=False, bbox_to_anchor=(0.5, -0.01))
        label = str(group["formula_label"].iloc[0])
        fig.suptitle(f"{formula_id}: {label}", fontsize=18, y=0.995)
        fig.text(
            0.5,
            0.955,
            "Same supervisor formula; panels change estimator/data structure",
            ha="center",
            va="top",
            fontsize=12,
            color="#555555",
        )
        fig.tight_layout(rect=[0, 0.05, 1, 0.92])
        path = fig_dir / f"{safe_slug(formula_id)}_fixed_word_estimator_panels.png"
        fig.savefig(path, dpi=190, bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "figure_type": "fixed_word_estimator_panels",
                "formula_id": formula_id,
                "formula_label": label,
                "figure": str(path),
                "description": "Predicted total bits by age at exact fixed word counts 1-12, faceted by estimator.",
            }
        )
    return pd.DataFrame(rows)


def plot_slope_heatmap(slopes: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    fig_dir.mkdir(parents=True, exist_ok=True)
    if slopes.empty:
        return pd.DataFrame()
    data = slopes.copy()
    data["fixed_effort_value"] = pd.to_numeric(data["fixed_effort_value"], errors="coerce")
    data = data[data["fixed_effort_value"].between(1, 12)].copy()
    data["model_estimator"] = data["formula_id"].astype(str) + " | " + data["estimator_id"].astype(str)
    pivot = data.pivot_table(
        index="model_estimator",
        columns="fixed_effort_value",
        values="slope_bits_per_6_months",
        aggfunc="mean",
    )
    order = []
    for formula in [item.spec.formula_id for item in SUPERVISOR_FORMULAS]:
        order.extend([idx for idx in pivot.index if idx.startswith(f"{formula} | ")])
    pivot = pivot.loc[order]
    fig, ax = plt.subplots(figsize=(12.5, max(7.5, 0.36 * len(pivot))))
    sns.heatmap(pivot, center=0, cmap="vlag", linewidths=0.3, linecolor="white", annot=True, fmt=".2f", ax=ax)
    ax.set_title("Fixed-word age slope by supervisor formula and estimator")
    ax.set_xlabel("Fixed word count")
    ax.set_ylabel("Formula | estimator")
    fig.tight_layout()
    path = fig_dir / "fixed_word_slope_heatmap.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "figure_type": "fixed_word_slope_heatmap",
                "formula_id": "all",
                "formula_label": "All supervisor formulas",
                "figure": str(path),
                "description": "Age slopes in predicted bits per six months for fixed word counts 1-12.",
            }
        ]
    )


def plot_stage(*, output_dir: Path, fig_dir: Path) -> dict[str, Path]:
    predictions = pd.read_csv(output_dir / "fixed_effort_predictions.csv.gz")
    slopes = pd.read_csv(output_dir / "fixed_slice_slopes.csv")
    manifest = pd.concat(
        [
            plot_estimator_fixed_effort_panels(predictions, fig_dir=fig_dir),
            plot_slope_heatmap(slopes, fig_dir=fig_dir),
        ],
        ignore_index=True,
    )
    path = output_dir / "figure_manifest.csv"
    manifest.to_csv(path, index=False)
    slope_table = representative_slope_table(slopes)
    slope_table.to_csv(output_dir / "representative_fixed_word_slopes.csv", index=False)
    return {"figures": path, "representative_slopes": output_dir / "representative_fixed_word_slopes.csv"}


def format_num(value: object, digits: int = 3) -> str:
    try:
        value = float(value)
    except Exception:
        return ""
    if not math.isfinite(value):
        return ""
    return f"{value:.{digits}f}"


def dataframe_to_markdown(df: pd.DataFrame, *, max_rows: int | None = None) -> list[str]:
    if max_rows is not None:
        df = df.head(max_rows).copy()
    if df.empty:
        return ["", "_No rows available._", ""]
    columns = list(df.columns)
    lines = ["", "| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    lines.append("")
    return lines


def report_stage(*, output_dir: Path, fig_dir: Path, doc_md: Path, doc_html: Path) -> dict[str, Path]:
    summary = pd.read_csv(output_dir / "model_summary.csv")
    slopes = pd.read_csv(output_dir / "fixed_slice_slopes.csv")
    figures = pd.read_csv(output_dir / "figure_manifest.csv")
    representative = pd.read_csv(output_dir / "representative_fixed_word_slopes.csv")
    fit_counts = summary["status"].value_counts(dropna=False).to_dict()
    lines: list[str] = [
        "# Supervisor Formula Estimator Sensitivity",
        "",
        f"Generated on {RUN_DATE}.",
        "",
        "This side report does exactly one thing: it takes the four formulas currently used in the supervisor-facing report and fits estimator variants around those formulas. It does not include exact-length F19/F21 models, generated baselines, caretaker contrasts, question-type variants, or session-level random intercepts.",
        "",
        "All plots here use real child k3 rows and word count as the effort measure, because that is the version used for the current Model 3 and Model 4 supervisor plots. The aggregate estimators use child-age-exact-word cells, not session-ID cells.",
        "",
        f"Fit status counts: `{fit_counts}`.",
        "",
        "## The Four Formulas",
        "",
        "| Model | Formula | Estimator adaptation note |",
        "| --- | --- | --- |",
    ]
    for item in SUPERVISOR_FORMULAS:
        note = "No child identity in the mean formula." if not item.child_identity else "OLS/GEE use fixed child intercepts; MixedLM adapts child identity to random child intercepts."
        lines.append(f"| {item.spec.formula_id} | `{item.supervisor_formula}` | {note} |")
    lines.extend(
        [
            "",
            "## How To Read These Plots",
            "",
            "Each panel is a different estimator or repeated-measures structure. Within a panel, the colored lines are predictions at exact fixed word counts from 1 to 12. The clean question is whether the same formula gives the same age-line direction after the estimator changes.",
            "",
            "No panel uses `session_id` as a predictor, grouping factor, or random intercept. The row-level panels fit utterance rows directly. The cell-level panels average repeated rows inside child-age-word cells before fitting OLS/GEE/MixedLM checks. MixedLM panels use child random intercepts only.",
            "",
            "Do not compare the vertical intercepts too aggressively across estimator families. Some panels are row-level predictions averaged over fixed child intercepts; others are population-average GEE or mixed-model fixed-effect predictions. The slope direction and flattening/steepening are the main comparison.",
            "",
            "## Exact Formula Used In Each Panel",
            "",
            "The table below separates the fixed-effects mean formula from the estimator structure. This is the part to audit if a plot looks surprising.",
        ]
    )
    formula_table = summary[
        [
            "formula_id",
            "estimator_id",
            "readable_formula",
            "adaptation_note",
            "n_obs",
            "n_source_rows",
        ]
    ].copy()
    lines.extend(dataframe_to_markdown(formula_table))
    lines.extend(
        [
            "## Main Plots",
            "",
        ]
    )
    for formula_id in [item.spec.formula_id for item in SUPERVISOR_FORMULAS]:
        row = figures[figures["formula_id"].astype(str).eq(formula_id)]
        if row.empty:
            continue
        figure = relative_to_report(doc_md, str(row.iloc[0]["figure"]))
        label = str(row.iloc[0]["formula_label"])
        lines.extend([f"### {formula_id}: {label}", "", f"![{formula_id} fixed-word estimator panels]({figure})", ""])
    heatmap = figures[figures["figure_type"].astype(str).eq("fixed_word_slope_heatmap")]
    if not heatmap.empty:
        lines.extend(
            [
                "## Slope Heatmap",
                "",
                "This heatmap gives the same information numerically: each cell is the age slope in predicted bits per six months at that fixed word count.",
                "",
                f"![Fixed-word slope heatmap]({relative_to_report(doc_md, str(heatmap.iloc[0]['figure']))})",
                "",
            ]
        )
    lines.extend(
        [
            "## Representative Slopes",
            "",
            "For quick reading, here are the slopes at 2, 6, and 10 words. Units are predicted bits per six months.",
        ]
    )
    rep = representative.copy()
    for col in ["2", "6", "10"]:
        if col in rep.columns:
            rep[col] = rep[col].map(lambda x: format_num(x, 3))
    lines.extend(dataframe_to_markdown(rep[["formula_id", "estimator_id", "2", "6", "10"]]))
    lines.extend(
        [
            "## Saved Artifacts",
            "",
            "```text",
            str(output_dir / "model_summary.csv"),
            str(output_dir / "coefficient_long.csv"),
            str(output_dir / "fixed_effort_predictions.csv.gz"),
            str(output_dir / "fixed_slice_slopes.csv"),
            str(output_dir / "representative_fixed_word_slopes.csv"),
            str(output_dir / "formula_definitions.csv"),
            str(output_dir / "estimator_definitions.csv"),
            str(output_dir / "figure_manifest.csv"),
            str(fig_dir),
            "```",
            "",
        ]
    )
    doc_md.parent.mkdir(parents=True, exist_ok=True)
    doc_md.write_text("\n".join(lines), encoding="utf-8")
    render_markdown_file(doc_md, doc_html, title="Supervisor Formula Estimator Sensitivity")
    render_markdown_file(doc_md, doc_html.with_suffix(".embedded.html"), title="Supervisor Formula Estimator Sensitivity", embed_images=True)
    return {"md": doc_md, "html": doc_html, "embedded_html": doc_html.with_suffix(".embedded.html")}


def build_all(
    *,
    input_csv: Path = DEFAULT_INPUT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
    doc_md: Path = DEFAULT_DOC_MD,
    doc_html: Path = DEFAULT_DOC_HTML,
    chunksize: int = 250_000,
    max_rows: int | None = None,
    n_points: int = 70,
) -> dict[str, Path]:
    paths = fit_stage(
        input_csv=input_csv,
        output_dir=output_dir,
        chunksize=chunksize,
        max_rows=max_rows,
        n_points=n_points,
    )
    paths.update(plot_stage(output_dir=output_dir, fig_dir=fig_dir))
    paths.update(report_stage(output_dir=output_dir, fig_dir=fig_dir, doc_md=doc_md, doc_html=doc_html))
    return paths


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["all", "fit", "plot", "report"], default="all")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--n-points", type=int, default=70)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    print(f"[stage] {args.stage}", flush=True)
    outputs: dict[str, Path] = {}
    if args.stage in {"all", "fit"}:
        outputs.update(
            fit_stage(
                input_csv=args.input,
                output_dir=args.output_dir,
                chunksize=args.chunksize,
                max_rows=args.max_rows,
                n_points=args.n_points,
            )
        )
    if args.stage in {"all", "plot"}:
        outputs.update(plot_stage(output_dir=args.output_dir, fig_dir=args.fig_dir))
    if args.stage in {"all", "report"}:
        outputs.update(report_stage(output_dir=args.output_dir, fig_dir=args.fig_dir, doc_md=args.doc_md, doc_html=args.doc_html))
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
