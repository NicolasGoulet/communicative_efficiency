#!/usr/bin/env python3
"""Build a Route 1 formula-permutation estimator report.

This report is intentionally internal/model-selection facing.  It fits a
systematic grid of Route 1 formulas where age, child production effort, and
child identity handling are always present, then toggles context predictors and
age interactions.  The heavy repeated-measures estimator grid is fit on the
existing child-session/effort-band aggregate frame; row-level Atlas and heldout
artifacts are linked where available.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.genmod.families import Gamma, Gaussian
from statsmodels.genmod.families.links import Log

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_route1_best_model_robustness_package import (
        CARETAKER_FIG_DIR,
        DEFAULT_FIG_DIR as LEGACY_FIG_DIR,
        ESTIMATOR_SPECS as LEGACY_ESTIMATOR_SPECS,
        HELDOUT_DIR,
        REAL_ATLAS_DIR,
        REAL_FIG_DIR,
        ROUTE1_INPUT,
        SOURCE_ATLAS_DIR,
        SUPERVISOR_FIG_DIR,
        CoreFormula,
        EstimatorSpec,
        build_or_read_aggregate_frame,
        display_formula,
        estimator_formula_for,
        fit_one_estimator,
        f_text,
        md_image,
        md_link,
        p_text,
        plot_model_term_forest,
        relation_text,
        relevant_term_prefixes,
        scientific_formula,
        term_result_sentence,
    )
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_best_model_robustness_package import (
        CARETAKER_FIG_DIR,
        DEFAULT_FIG_DIR as LEGACY_FIG_DIR,
        ESTIMATOR_SPECS as LEGACY_ESTIMATOR_SPECS,
        HELDOUT_DIR,
        REAL_ATLAS_DIR,
        REAL_FIG_DIR,
        ROUTE1_INPUT,
        SOURCE_ATLAS_DIR,
        SUPERVISOR_FIG_DIR,
        CoreFormula,
        EstimatorSpec,
        build_or_read_aggregate_frame,
        display_formula,
        estimator_formula_for,
        fit_one_estimator,
        f_text,
        md_image,
        md_link,
        p_text,
        plot_model_term_forest,
        relation_text,
        relevant_term_prefixes,
        scientific_formula,
        term_result_sentence,
    )
    from src.render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/route1_formula_permutation_estimator_report")
DEFAULT_FIG_DIR = Path("figs/route1_formula_permutation_estimator_report")
DEFAULT_DOC_DIR = Path("docs")
DOC_BASENAME = "route1_formula_permutation_estimator_report"


EXACT_ROW_LEVEL_ATLAS_MODEL_BY_FORMULA = {
    "F01": "M2",
    "F02": "M3",
    "F04": "M4c",
    "F07": "M4a",
    "F15": "M4b",
    "F33": "M5",
    "F34": "M11",
}


def estimator_specs_with_child_identity() -> tuple[EstimatorSpec, ...]:
    """Return estimator specs with child identity controlled in every sensible case."""

    specs: list[EstimatorSpec] = []
    for spec in LEGACY_ESTIMATOR_SPECS:
        if spec.estimator_id in {"gee_gaussian", "gee_gamma_log"}:
            specs.append(
                EstimatorSpec(
                    estimator_id=spec.estimator_id,
                    label=spec.label,
                    family=spec.family,
                    dependence=f"{spec.dependence}; C(child_id) also included in the mean model",
                    effect_scale=spec.effect_scale,
                    uses_child_fixed_effects=True,
                    re_formula=spec.re_formula,
                )
            )
        else:
            specs.append(spec)
    return tuple(specs)


ESTIMATOR_SPECS = estimator_specs_with_child_identity()


def formula_grid() -> tuple[CoreFormula, ...]:
    """Build the requested formula grid.

    Always present:
    age_c, effort_c, and child identity handling.  Optional context controls:
    context entropy, parent/caretaker context effort, and question/form type.
    Optional interactions:
    age_c:effort_c, age_c:context_entropy_c, and
    age_c:parent_context_effort_c.  Interactions are only allowed when their
    lower-order predictors are present.
    """

    rows: list[CoreFormula] = []
    idx = 1
    for include_entropy in [False, True]:
        for include_parent_effort in [False, True]:
            for include_question_type in [False, True]:
                for include_age_effort in [False, True]:
                    entropy_interactions = [False, True] if include_entropy else [False]
                    parent_interactions = [False, True] if include_parent_effort else [False]
                    for include_age_entropy in entropy_interactions:
                        for include_age_parent in parent_interactions:
                            terms = ["age_c", "effort_c"]
                            descriptor_parts = ["age", "child effort"]
                            if include_entropy:
                                terms.append("context_entropy_c")
                                descriptor_parts.append("context entropy")
                            if include_parent_effort:
                                terms.append("parent_context_effort_c")
                                descriptor_parts.append("parent context effort")
                            if include_question_type:
                                terms.append("C(question_type)")
                                descriptor_parts.append("question/form type")
                            interaction_parts: list[str] = []
                            if include_age_effort:
                                terms.append("age_c:effort_c")
                                interaction_parts.append("age x child effort")
                            if include_age_entropy:
                                terms.append("age_c:context_entropy_c")
                                interaction_parts.append("age x context entropy")
                            if include_age_parent:
                                terms.append("age_c:parent_context_effort_c")
                                interaction_parts.append("age x parent context effort")

                            model_id = f"F{idx:02d}"
                            label = " + ".join(descriptor_parts)
                            if interaction_parts:
                                label += " with " + ", ".join(interaction_parts)
                            question = (
                                "Does child age predict total utterance information at fixed child effort"
                                " after controlling child identity"
                            )
                            if len(descriptor_parts) > 2:
                                question += " and " + ", ".join(descriptor_parts[2:])
                            if interaction_parts:
                                question += "; and do the listed age interactions change that relation"
                            question += "?"

                            fe_formula = "mean_sum_bits ~ " + " + ".join([*terms, "C(child_id)"])
                            population_formula = "mean_sum_bits ~ " + " + ".join(terms)
                            rows.append(
                                CoreFormula(
                                    model_id=model_id,
                                    label=label,
                                    question=question,
                                    fe_formula=fe_formula,
                                    population_formula=population_formula,
                                    needs_context_entropy=include_entropy,
                                    needs_parent_context_effort=include_parent_effort,
                                    needs_question_type=include_question_type,
                                    includes_interaction=bool(interaction_parts),
                                )
                            )
                            idx += 1
    return tuple(rows)


CORE_FORMULAS = formula_grid()
CORE_MODEL_ORDER = [formula.model_id for formula in CORE_FORMULAS]


def output_is_complete(summary_path: Path, formulas: Sequence[CoreFormula]) -> bool:
    if not summary_path.exists():
        return False
    try:
        summary = pd.read_csv(summary_path)
    except Exception:
        return False
    expected = {(formula.model_id, estimator.estimator_id) for formula in formulas for estimator in ESTIMATOR_SPECS}
    observed = set(zip(summary.get("model_id", []), summary.get("estimator_id", [])))
    return expected.issubset(observed)


def prediction_grid(model_frame: pd.DataFrame, formula_def: CoreFormula, estimator: EstimatorSpec) -> pd.DataFrame:
    """Prediction grid at median child effort and average context controls."""

    ages = np.linspace(float(model_frame["age_months"].min()), float(model_frame["age_months"].max()), 80)
    effort = float(model_frame["mean_effort"].median())
    entropy = float(model_frame["mean_context_entropy"].mean()) if "mean_context_entropy" in model_frame else 0.0
    parent = float(model_frame["mean_parent_context_effort"].mean()) if "mean_parent_context_effort" in model_frame else 0.0
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
    return grid


def fit_formula_estimators(
    aggregate: pd.DataFrame,
    *,
    output_dir: Path,
    formulas: Sequence[CoreFormula],
    force: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit formula-estimator grid or reuse complete cached outputs."""

    summary_path = output_dir / "formula_estimator_summary.csv"
    pred_path = output_dir / "formula_fixed_effort_predictions.csv"
    fitted_path = output_dir / "formula_fitted_values.csv.gz"
    if not force and output_is_complete(summary_path, formulas) and pred_path.exists() and fitted_path.exists():
        return pd.read_csv(summary_path), pd.read_csv(pred_path), pd.read_csv(fitted_path)

    summaries: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []
    fitted_rows: list[pd.DataFrame] = []
    total = len(formulas) * len(ESTIMATOR_SPECS)
    done = 0
    for formula_def in formulas:
        for estimator in ESTIMATOR_SPECS:
            done += 1
            print(f"[fit {done}/{total}] {formula_def.model_id} {estimator.estimator_id}", flush=True)
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
            except Exception as exc:  # pragma: no cover - model-specific guard
                print(f"[warn] prediction failed for {formula_def.model_id} {estimator.estimator_id}: {exc}", flush=True)

    summary = pd.DataFrame(summaries)
    predictions = pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()
    fitted_values = pd.concat(fitted_rows, ignore_index=True) if fitted_rows else pd.DataFrame()
    summary.to_csv(summary_path, index=False)
    predictions.to_csv(pred_path, index=False)
    fitted_values.to_csv(fitted_path, index=False)
    return summary, predictions, fitted_values


def relation_summary(summary: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    term_labels = {
        "age": "Age at session",
        "effort": "Child utterance effort",
        "age_effort": "Age x child effort",
        "context_entropy": "Context entropy",
        "parent_context_effort": "Parent context effort",
        "age_context_entropy": "Age x context entropy",
        "age_parent_context_effort": "Age x parent context effort",
    }
    rows: list[dict[str, object]] = []
    for row in summary[summary["status"].eq("fit")].to_dict("records"):
        for prefix, label in term_labels.items():
            coef = pd.to_numeric(pd.Series([row.get(f"{prefix}_coef")]), errors="coerce").iloc[0]
            if pd.isna(coef):
                continue
            rows.append(
                {
                    "model_id": row["model_id"],
                    "model_label": row["model_label"],
                    "estimator_label": row["estimator_label"],
                    "effect_scale": row["effect_scale"],
                    "term": label,
                    "coefficient": coef,
                    "p_value": row.get(f"{prefix}_p"),
                    "ci_low": row.get(f"{prefix}_ci_low"),
                    "ci_high": row.get(f"{prefix}_ci_high"),
                    "relation_to_sum_bits": relation_text(coef, row.get("effect_scale")),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(output_dir / "formula_key_term_relation_summary.csv", index=False)
    return out


def nested_r2(summary: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    sub = summary[summary["status"].eq("fit") & summary["estimator_id"].eq("ols_fe_cluster")].copy()
    sub["r2_observed_fitted"] = pd.to_numeric(sub["r2_observed_fitted"], errors="coerce")
    base = float(sub[sub["model_id"].eq("F01")]["r2_observed_fitted"].iloc[0]) if (sub["model_id"] == "F01").any() else math.nan
    sub["delta_r2_vs_base"] = sub["r2_observed_fitted"] - base
    sub["rank_by_r2"] = sub["r2_observed_fitted"].rank(ascending=False, method="first")
    out = sub[
        [
            "model_id",
            "model_label",
            "formula",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "delta_r2_vs_base",
            "rank_by_r2",
            "age_coef",
            "age_p",
        ]
    ].sort_values(["rank_by_r2", "model_id"])
    out.to_csv(output_dir / "formula_ols_fe_nested_r2.csv", index=False)
    return out


def plot_nested_r2(r2: pd.DataFrame, fig_dir: Path) -> Path:
    top = r2.sort_values("r2_observed_fitted", ascending=False).head(24).copy()
    top = top.sort_values("r2_observed_fitted")
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.barh(top["model_id"], top["delta_r2_vs_base"] * 1000, color="#2f6f73")
    ax.axvline(0, color="#111827", lw=1)
    ax.set_xlabel("Delta observed-vs-fitted R2 vs F01, multiplied by 1000")
    ax.set_ylabel("Formula")
    ax.set_title("Aggregate screening fit gains under OLS child fixed effects")
    ax.grid(axis="x", color="#e5e7eb")
    path = fig_dir / "formula_nested_delta_r2_top24.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_age_effect_forest(summary: pd.DataFrame, fig_dir: Path) -> Path:
    sub = summary[summary["status"].eq("fit")].copy()
    sub["age_coef"] = pd.to_numeric(sub["age_coef"], errors="coerce")
    sub["age_ci_low"] = pd.to_numeric(sub["age_ci_low"], errors="coerce")
    sub["age_ci_high"] = pd.to_numeric(sub["age_ci_high"], errors="coerce")
    top_models = (
        sub[sub["estimator_id"].eq("ols_fe_cluster")]
        .sort_values("r2_observed_fitted", ascending=False)
        .head(18)["model_id"]
        .tolist()
    )
    data = sub[sub["model_id"].isin(top_models)].copy()
    data["label"] = data["model_id"] + " | " + data["estimator_family"]
    data = data.sort_values(["model_id", "estimator_id"])
    fig, axes = plt.subplots(1, 2, figsize=(18, max(8, len(data) * 0.16)), sharey=True)
    for ax, scale in zip(axes, ["additive bits", "log mean bits"]):
        panel = data[data["effect_scale"].eq(scale)].copy()
        if panel.empty:
            ax.axis("off")
            continue
        y = np.arange(len(panel))
        ax.hlines(y, panel["age_ci_low"], panel["age_ci_high"], color="#94a3b8", lw=1.5)
        ax.scatter(panel["age_coef"], y, color="#0f766e", s=32)
        ax.axvline(0, color="#111827", linestyle=":", lw=1)
        ax.set_yticks(y)
        ax.set_yticklabels(panel["label"], fontsize=7)
        ax.set_xlabel("Age coefficient")
        ax.set_title(scale)
        ax.grid(axis="x", color="#e5e7eb")
    fig.suptitle("Aggregate screening age coefficients across estimator families", y=1.01)
    plt.tight_layout()
    path = fig_dir / "formula_age_effect_forest_top18.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_aggregate_estimator_age_lines(predictions: pd.DataFrame, fig_dir: Path, *, model_id: str) -> Path:
    """Plot the aggregate estimator-family screen with explicit caution labels."""

    sub = predictions[predictions["model_id"].eq(model_id)].copy()
    fig, ax = plt.subplots(figsize=(12, 7))
    if sub.empty:
        ax.text(0.5, 0.5, f"No aggregate predictions for {model_id}", ha="center", va="center")
        ax.axis("off")
    else:
        additive = sub[sub["effect_scale"].eq("additive bits")]
        logscale = sub[sub["effect_scale"].eq("log mean bits")]
        for _, group in additive.groupby("estimator_label", sort=False):
            ax.plot(group["age_months"], group["predicted_sum_bits"], lw=2.2, label=group["estimator_label"].iloc[0])
        for _, group in logscale.groupby("estimator_label", sort=False):
            ax.plot(group["age_months"], group["predicted_sum_bits"], lw=2.0, linestyle="--", label=group["estimator_label"].iloc[0])
        ax.set_xlabel("Age (months)")
        ax.set_ylabel("Predicted aggregate mean_sum_bits")
        ax.set_title(f"{model_id}: aggregate estimator screen at median effort")
        ax.text(
            0.01,
            0.02,
            "Sensitivity screen only: not the row-level fixed-size Atlas result.",
            transform=ax.transAxes,
            fontsize=9,
            color="#7c2d12",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#fff7ed", "edgecolor": "#fed7aa"},
        )
        ax.grid(color="#e5e7eb")
        ax.legend(fontsize=8, loc="best")
    path = fig_dir / f"{model_id.lower()}_aggregate_estimator_screen_age_lines.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def read_real_atlas_predictions() -> pd.DataFrame:
    path = REAL_ATLAS_DIR / "fixed_effort_predictions.csv.gz"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_real_atlas_slopes() -> pd.DataFrame:
    path = REAL_ATLAS_DIR / "fixed_slice_slopes.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def exact_row_level_atlas_model(formula_id: str) -> str | None:
    return EXACT_ROW_LEVEL_ATLAS_MODEL_BY_FORMULA.get(formula_id)


def row_level_atlas_figure(atlas_model_id: str) -> Path:
    return REAL_FIG_DIR / f"real_k3_{atlas_model_id.lower()}_nb_words_fixed_effort_atlas.png"


def row_level_slope_text(slopes: pd.DataFrame, atlas_model_id: str) -> str:
    if slopes.empty:
        return "No row-level fixed-effort slope table is available."
    sub = slopes[
        slopes["target_source"].eq("real")
        & slopes["context_k"].eq("k3")
        & slopes["effort_col"].eq("nb_words")
        & slopes["model_id"].eq(atlas_model_id)
    ].copy()
    if sub.empty:
        return "No row-level fixed-effort slopes are available for this exact Atlas model."
    sub["slope_bits_per_month"] = pd.to_numeric(sub["slope_bits_per_month"], errors="coerce")
    mean_slope = sub["slope_bits_per_month"].mean()
    min_slope = sub["slope_bits_per_month"].min()
    max_slope = sub["slope_bits_per_month"].max()
    directions = ", ".join(sorted(set(sub["direction"].dropna().astype(str))))
    return (
        f"Across fixed word-count values, the row-level fixed-effort slopes are {directions}: "
        f"mean {mean_slope:.3f}, range {min_slope:.3f} to {max_slope:.3f} bits/month."
    )


def plot_row_level_global_fixed_effort_summary(
    predictions: pd.DataFrame,
    slopes: pd.DataFrame,
    fig_dir: Path,
    *,
    formula_id: str,
    atlas_model_id: str,
) -> tuple[Path | None, dict[str, object]]:
    """Plot the global trend across all row-level fixed-size prediction lines."""

    summary: dict[str, object] = {
        "formula_id": formula_id,
        "atlas_model_id": atlas_model_id,
        "status": "missing",
        "path": "",
        "n_fixed_effort_values": 0,
        "mean_slope_bits_per_month": math.nan,
        "min_slope_bits_per_month": math.nan,
        "max_slope_bits_per_month": math.nan,
        "directions": "",
    }
    if predictions.empty:
        return None, summary
    pred = predictions[
        predictions["target_source"].eq("real")
        & predictions["context_k"].eq("k3")
        & predictions["effort_col"].eq("nb_words")
        & predictions["model_id"].eq(atlas_model_id)
    ].copy()
    if pred.empty:
        return None, summary
    pred["fixed_effort_value"] = pd.to_numeric(pred["fixed_effort_value"], errors="coerce")
    pred["predicted_sum_bits"] = pd.to_numeric(pred["predicted_sum_bits"], errors="coerce")
    pred["age_months"] = pd.to_numeric(pred["age_months"], errors="coerce")
    pred = pred.dropna(subset=["fixed_effort_value", "predicted_sum_bits", "age_months"]).copy()
    if pred.empty:
        return None, summary

    slope_sub = slopes[
        slopes["target_source"].eq("real")
        & slopes["context_k"].eq("k3")
        & slopes["effort_col"].eq("nb_words")
        & slopes["model_id"].eq(atlas_model_id)
    ].copy()
    if not slope_sub.empty:
        slope_sub["fixed_effort_value"] = pd.to_numeric(slope_sub["fixed_effort_value"], errors="coerce")
        slope_sub["slope_bits_per_month"] = pd.to_numeric(slope_sub["slope_bits_per_month"], errors="coerce")
        slope_sub = slope_sub.dropna(subset=["fixed_effort_value", "slope_bits_per_month"]).copy()

    global_line = (
        pred.groupby("age_months", as_index=False)
        .agg(
            mean_predicted_sum_bits=("predicted_sum_bits", "mean"),
            q25_predicted_sum_bits=("predicted_sum_bits", lambda values: float(np.nanpercentile(values, 25))),
            q75_predicted_sum_bits=("predicted_sum_bits", lambda values: float(np.nanpercentile(values, 75))),
        )
        .sort_values("age_months")
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw={"width_ratios": [1.55, 1]})
    ax = axes[0]
    palette = sns.color_palette("viridis", n_colors=int(pred["fixed_effort_value"].nunique()))
    for color, (effort_value, group) in zip(palette, pred.groupby("fixed_effort_value", sort=True)):
        group = group.sort_values("age_months")
        ax.plot(group["age_months"], group["predicted_sum_bits"], color=color, alpha=0.28, lw=1.2)
    ax.plot(
        global_line["age_months"],
        global_line["mean_predicted_sum_bits"],
        color="#111827",
        lw=3.0,
        label="unweighted mean across fixed word counts",
    )
    ax.fill_between(
        global_line["age_months"],
        global_line["q25_predicted_sum_bits"],
        global_line["q75_predicted_sum_bits"],
        color="#111827",
        alpha=0.10,
        label="middle 50% of fixed word-count lines",
    )
    ax.set_xlabel("Age (months)")
    ax.set_ylabel("Predicted sum_bits at fixed word counts")
    ax.set_title(f"{formula_id} / {atlas_model_id}: global fixed-effort trajectory")
    ax.grid(color="#e5e7eb")
    ax.legend(fontsize=8, loc="best")

    ax = axes[1]
    if slope_sub.empty:
        ax.text(0.5, 0.5, "No slope table", ha="center", va="center")
        ax.axis("off")
    else:
        slope_sub = slope_sub.sort_values("fixed_effort_value")
        colors = np.where(slope_sub["slope_bits_per_month"] < 0, "#0f766e", "#b45309")
        ax.bar(slope_sub["fixed_effort_value"].astype(int).astype(str), slope_sub["slope_bits_per_month"], color=colors)
        ax.axhline(0, color="#111827", lw=1)
        ax.set_xlabel("Fixed word count")
        ax.set_ylabel("Slope, bits/month")
        ax.set_title("Age slope at each fixed size")
        ax.grid(axis="y", color="#e5e7eb")
        summary.update(
            {
                "n_fixed_effort_values": int(slope_sub["fixed_effort_value"].nunique()),
                "mean_slope_bits_per_month": float(slope_sub["slope_bits_per_month"].mean()),
                "min_slope_bits_per_month": float(slope_sub["slope_bits_per_month"].min()),
                "max_slope_bits_per_month": float(slope_sub["slope_bits_per_month"].max()),
                "directions": ", ".join(sorted(set(slope_sub["direction"].dropna().astype(str)))),
            }
        )
    fig.suptitle("Row-level fixed-effort result: same production effort through time", y=1.02)
    plt.tight_layout()
    path = fig_dir / f"{formula_id.lower()}_{atlas_model_id.lower()}_row_level_global_fixed_effort_summary.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    summary.update({"status": "available", "path": str(path)})
    return path, summary


def plot_actual_vs_predicted(
    fitted_values: pd.DataFrame,
    predictions: pd.DataFrame,
    fig_dir: Path,
    *,
    model_id: str,
) -> Path:
    obs = fitted_values[fitted_values["model_id"].eq(model_id) & fitted_values["estimator_id"].eq("ols_fe_cluster")].copy()
    pred = predictions[predictions["model_id"].eq(model_id) & predictions["estimator_id"].eq("ols_fe_cluster")].copy()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    if obs.empty:
        ax.text(0.5, 0.5, f"No fitted rows for {model_id}", ha="center", va="center")
        ax.axis("off")
    else:
        ax.scatter(obs["age_months"], obs["mean_sum_bits"], s=16, alpha=0.20, color="#64748b", label="observed aggregate cells")
        by_age = obs.groupby(pd.cut(obs["age_months"], bins=18), observed=True).agg(
            age_mid=("age_months", "mean"),
            mean_sum_bits=("mean_sum_bits", "mean"),
        )
        ax.plot(by_age["age_mid"], by_age["mean_sum_bits"], color="#111827", lw=2.2, label="observed aggregate trend")
        if not pred.empty:
            ax.plot(pred["age_months"], pred["predicted_sum_bits"], color="#0f766e", lw=2.6, linestyle="--", label="fixed-effort prediction")
        ax.set_xlabel("Age (months)")
        ax.set_ylabel("Mean sum_bits")
        ax.set_title(f"{model_id}: observed aggregate trend vs fixed-effort prediction")
        ax.grid(color="#e5e7eb")
        ax.legend()
    path = fig_dir / f"{model_id.lower()}_actual_vs_fixed_effort_prediction.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def build_figures(
    *,
    summary: pd.DataFrame,
    predictions: pd.DataFrame,
    fitted_values: pd.DataFrame,
    formulas: Sequence[CoreFormula],
    r2: pd.DataFrame,
    fig_dir: Path,
    output_dir: Path,
) -> dict[str, Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Path] = {
        "nested_r2": plot_nested_r2(r2, fig_dir),
        "age_forest": plot_age_effect_forest(summary, fig_dir),
    }
    atlas_predictions = read_real_atlas_predictions()
    atlas_slopes = read_real_atlas_slopes()
    row_level_summaries: list[dict[str, object]] = []
    top_models = r2.head(8)["model_id"].tolist()
    formula_by_id = {formula.model_id: formula for formula in formulas}
    for formula in formulas:
        model_id = formula.model_id
        atlas_model_id = exact_row_level_atlas_model(model_id)
        if atlas_model_id is not None:
            row_level_fig, row_level_summary = plot_row_level_global_fixed_effort_summary(
                atlas_predictions,
                atlas_slopes,
                fig_dir,
                formula_id=model_id,
                atlas_model_id=atlas_model_id,
            )
            row_level_summaries.append(row_level_summary)
            if row_level_fig is not None:
                generated[f"{model_id}_row_level_global_fixed_effort"] = row_level_fig
        generated[f"{model_id}_estimator_lines"] = plot_aggregate_estimator_age_lines(predictions, fig_dir, model_id=model_id)
        generated[f"{model_id}_term_forest"] = plot_model_term_forest(summary, fig_dir, formula)
    for model_id in top_models:
        formula = formula_by_id[model_id]
        generated[f"{model_id}_actual_vs_predicted"] = plot_actual_vs_predicted(fitted_values, predictions, fig_dir, model_id=model_id)
    pd.DataFrame(row_level_summaries).to_csv(output_dir / "row_level_global_fixed_effort_summaries.csv", index=False)
    return generated


def estimator_subsection_lines(
    formula: CoreFormula,
    summary: pd.DataFrame,
    *,
    estimator: EstimatorSpec,
) -> list[str]:
    sub = summary[summary["model_id"].eq(formula.model_id) & summary["estimator_id"].eq(estimator.estimator_id)]
    row = sub.iloc[0] if not sub.empty else pd.Series(dtype=object)
    lines = [
        f"### {estimator.label}",
        "",
        f"**Why this estimator is here.** {estimator.dependence}. Outcome scale: {estimator.effect_scale}.",
        "",
        f"**Formula used.** `{scientific_formula(estimator_formula_for(formula, estimator))}`",
        "",
    ]
    if row.empty or row.get("status") != "fit":
        lines.extend([f"**Status.** Not fit. {row.get('error', '') if not row.empty else ''}", ""])
        return lines
    lines.extend(
        [
            (
                f"**Aggregate screen fit.** {int(row.get('n_obs', 0)):,} child-session/effort-band rows, "
                f"{int(row.get('n_children', 0)):,} children; observed-vs-fitted R2 = {f_text(row.get('r2_observed_fitted'), 4)}. "
                "This subsection is estimator sensitivity, not the primary row-level fixed-effort answer."
            ),
            "",
            "**Predictor read for the aggregate sensitivity screen.**",
            "",
        ]
    )
    for prefix in relevant_term_prefixes(formula):
        lines.append(term_result_sentence(row, prefix))
    warning_value = row.get("warning", "")
    warning = "" if pd.isna(warning_value) else str(warning_value or "")
    if warning:
        lines.extend(["", f"**Caution.** {warning[:450]}"])
    lines.append("")
    return lines


def heldout_summary_lines(doc_path: Path) -> list[str]:
    metrics_path = HELDOUT_DIR / "heldout_prediction_metrics.csv"
    lines = [
        "## Heldout Children",
        "",
        "The heldout prediction artifacts are row-level PBM-trained population/Mundlak models for Forrester/Ella, Sachs/Naomi, and MPI-EVA-Manchester/Helen. These models cannot use `C(child_id)` for unseen children, so they use population or Mundlak-compatible analogues of the Route 1 formulas.",
        "",
    ]
    if metrics_path.exists():
        metrics = pd.read_csv(metrics_path)
        view = metrics[metrics["context_k"].eq("k3") & metrics["effort_col"].eq("nb_words")].copy()
        if not view.empty:
            model_view = (
                view.groupby(["model_id", "model_label"], as_index=False)
                .agg(mean_mae=("mae", "mean"), mean_rmse=("rmse", "mean"), same_slope_share=("same_slope_sign", "mean"))
                .sort_values(["mean_rmse", "mean_mae"])
                .head(5)
            )
            lines.extend(
                [
                    "**Best available heldout-compatible k3/word candidates by mean RMSE.**",
                    "",
                ]
            )
            for row in model_view.itertuples(index=False):
                lines.append(
                    f"- `{row.model_id}` ({row.model_label}): mean RMSE {row.mean_rmse:.3f}, mean MAE {row.mean_mae:.3f}, same-slope share {row.same_slope_share:.2f}."
                )
            lines.append("")
    for fig in [
        Path("figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M4C_nb_words.png"),
        Path("figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M4A_nb_words.png"),
        Path("figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M3_nb_words.png"),
        SUPERVISOR_FIG_DIR / "heldout_pop_m4c_actual_vs_predicted_regression_lines.png",
    ]:
        if fig.exists():
            lines.extend([md_image(doc_path, fig, fig.stem), ""])
    lines.extend(
        [
            "**Heldout read.** The heldout panels compare actual unseen-child age trajectories with PBM-trained predicted trajectories. This is the right prediction check; it is separate from the child-fixed-effect models because an unseen child cannot have a fitted child dummy.",
            "",
        ]
    )
    return lines


def write_report(
    *,
    doc_path: Path,
    output_dir: Path,
    fig_dir: Path,
    formulas: Sequence[CoreFormula],
    summary: pd.DataFrame,
    r2: pd.DataFrame,
    generated: Mapping[str, Path],
) -> None:
    real_atlas = Path("docs/utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html")
    heldout_report = Path("docs/utterance_information_route1_heldout_real_child_prediction_report.html")
    caretaker_report = Path("docs/utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html")
    formula_by_id = {formula.model_id: formula for formula in formulas}
    formula_order = [formula.model_id for formula in formulas]
    atlas_slopes = read_real_atlas_slopes()

    lines: list[str] = [
        "# Route 1 Formula-Permutation Estimator Report",
        "",
        "This is an internal model-selection report for Route 1. It is organized around formulas, not around a compact aggregate grid.",
        "",
        "The key question is: at the same production-effort level, do children's utterances contain more or less surprisal as they get older? The primary evidence for that question is the row-level fixed-effort Atlas: separate lines for fixed word counts, plus the global average across those fixed-size lines.",
        "",
        "## Non-Negotiable Controls",
        "",
        "- Every formula includes age at session.",
        "- Every formula includes child utterance effort.",
        "- Every fixed-effect estimator includes `C(child_id)`.",
        "- MixedLM controls child identity with random child intercepts, and the random-slope version also allows child-specific age trajectories.",
        "- GEE models include `C(child_id)` in the mean model and cluster by child, so they handle both child identity and within-child repeated measurements.",
        "",
        "## Outcome And Repeated-Measurement Frame",
        "",
        "- Scientific outcome: `sum_bits`, the total information in one utterance.",
        "- Estimator-grid outcome used here: `mean_sum_bits`, the mean utterance `sum_bits` in child-session/effort-band cells. This makes GEE/GLM/MixedLM screening tractable and reduces row-level pseudo-replication.",
        "- Primary row-level Atlas plots remain the evidence to promote later; this report is for choosing which formulas deserve row-level promotion.",
        "- Read age coefficients as conditional information at fixed effort and controls, not as raw growth in utterance length.",
        "- If a row-level fixed-effort plot and an aggregate estimator-screen plot visually disagree, treat the row-level fixed-effort plot as the scientific Route 1 answer. The aggregate plot is an estimator-sensitivity screen, not the main result.",
        "",
        "## Formula Grid",
        "",
        "The grid starts from:",
        "",
        "`sum_bits ~ age_c + effort_c + C(child_id)`",
        "",
        "Then it toggles context entropy, parent/caretaker context effort, question/form type, `age_c:effort_c`, `age_c:context_entropy_c`, and `age_c:parent_context_effort_c`. Interactions are only fit when the lower-level predictors are also present.",
        "",
        f"Total formulas fit: **{len(formulas)}**. Estimator families per formula: **{len(ESTIMATOR_SPECS)}**.",
        "",
        "## Cross-Formula Plots",
        "",
        md_image(doc_path, generated["nested_r2"], "Nested delta R2 across formula permutations"),
        "",
        "**Variable-importance read.** This is not causal importance. It shows which added controls/interactions improve observed-vs-fitted R2 relative to the base age + effort + child-identity formula.",
        "",
        md_image(doc_path, generated["age_forest"], "Age effect forest across estimator families"),
        "",
        "**Age-effect read.** Additive-bit and log-mean-bit estimators are separated because their coefficients are on different scales. Prediction lines are safer than comparing raw log and additive coefficients directly.",
        "",
        "## Important Interpretation Guardrail",
        "",
        "The formula grid below includes an aggregate repeated-measures screen, so formulas can look better by R2 while still showing a positive aggregate age coefficient. That does **not** by itself mean older children are less efficient. The communicative-efficiency claim is read from row-level fixed-effort Atlas plots and the global fixed-effort summaries. Use the aggregate estimator screen to choose formulas and assess estimator sensitivity; do not treat it as the scientific conclusion.",
        "",
        "## Source Reports Used",
        "",
        f"- Row-level real-child Atlas: {md_link(doc_path, real_atlas)}",
        f"- Heldout prediction report: {md_link(doc_path, heldout_report)}",
        f"- Caretaker contrast report: {md_link(doc_path, caretaker_report)}",
        "",
        "## Formula Deep Dives",
        "",
        "Every formula below has one section, and each section has one subsection per estimator family. Sections are ordered in formula-grid order so the simpler controls and interactions are readable before the richer permutations.",
        "",
    ]

    for model_id in formula_order:
        formula = formula_by_id[model_id]
        row = r2[r2["model_id"].eq(model_id)].iloc[0]
        lines.extend(
            [
                f"## {formula.model_id}. {formula.label}",
                "",
                f"**Natural-language test.** {formula.question}",
                "",
                "**Child-fixed-effect formula.**",
                "",
                f"`{scientific_formula(formula.fe_formula)}`",
                "",
                "**Random-effect / population formula.**",
                "",
                f"`{scientific_formula(formula.population_formula)}`",
                "",
                (
                    f"**Aggregate screen fit read.** OLS child-fixed-effect R2 = {f_text(row.get('r2_observed_fitted'), 4)}; "
                    f"delta vs base F01 = {f_text(row.get('delta_r2_vs_base'), 5)}."
                ),
                "",
            ]
        )
        atlas_model_id = exact_row_level_atlas_model(model_id)
        if atlas_model_id is not None:
            atlas_fig = row_level_atlas_figure(atlas_model_id)
            if atlas_fig.exists():
                lines.extend(
                    [
                        "### Primary Row-Level Fixed-Effort Atlas",
                        "",
                        md_image(doc_path, atlas_fig, f"{model_id} exact row-level Atlas fixed-effort lines"),
                        "",
                        (
                            f"**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `{atlas_model_id}`. "
                            "Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age."
                        ),
                        "",
                        f"**Slope read.** {row_level_slope_text(atlas_slopes, atlas_model_id)}",
                        "",
                    ]
                )
            global_fig = generated.get(f"{model_id}_row_level_global_fixed_effort")
            if global_fig is not None:
                lines.extend(
                    [
                        "### Global Fixed-Effort Summary Across Fixed Sizes",
                        "",
                        md_image(doc_path, global_fig, f"{model_id} global fixed-effort summary"),
                        "",
                        (
                            "**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. "
                            "This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed."
                        ),
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "### Primary Row-Level Fixed-Effort Atlas",
                    "",
                    "_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._",
                    "",
                ]
            )
        for key, read in [
            (
                f"{model_id}_estimator_lines",
                "Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.",
            ),
            (f"{model_id}_term_forest", "Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators."),
        ]:
            fig = generated.get(key)
            if fig is not None:
                lines.extend([md_image(doc_path, fig, key), "", f"**{read}**", ""])
        for estimator in ESTIMATOR_SPECS:
            lines.extend(estimator_subsection_lines(formula, summary, estimator=estimator))

    lines.extend(
        [
            "## Complete Formula Grid Location",
            "",
            "The full 36-formula by 7-estimator grid is also saved here for sorting/filtering outside the prose report:",
            "",
            "```text",
            str(output_dir / "formula_estimator_summary.csv"),
            str(output_dir / "formula_key_term_relation_summary.csv"),
            str(output_dir / "formula_fixed_effort_predictions.csv"),
            str(output_dir / "formula_fitted_values.csv.gz"),
            str(output_dir / "formula_ols_fe_nested_r2.csv"),
            str(output_dir / "row_level_global_fixed_effort_summaries.csv"),
            str(fig_dir),
            "```",
            "",
        ]
    )
    lines.extend(heldout_summary_lines(doc_path))
    lines.extend(
        [
            "## Baseline And Caretaker Contrast Pointers",
            "",
            md_image(doc_path, Path("figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png"), "Row-level real child M3"),
            "",
            md_image(doc_path, Path("figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m5_nb_words_fixed_effort_atlas.png"), "Row-level real child M5"),
            "",
            md_image(doc_path, CARETAKER_FIG_DIR / "caretaker_k3_cm2_nb_words_fixed_effort_atlas.png", "Caretaker CM2"),
            "",
            md_image(doc_path, CARETAKER_FIG_DIR / "caretaker_k3_cm6_nb_words_fixed_effort_atlas.png", "Caretaker CM6"),
            "",
        ]
    )
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def run(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_dir: Path,
    chunksize: int,
    force: bool = False,
) -> dict[str, Path]:
    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)

    formulas = CORE_FORMULAS
    aggregate = build_or_read_aggregate_frame(input_csv, output_dir, chunksize=chunksize)
    summary, predictions, fitted_values = fit_formula_estimators(
        aggregate,
        output_dir=output_dir,
        formulas=formulas,
        force=force,
    )
    rel = relation_summary(summary, output_dir)
    r2 = nested_r2(summary, output_dir)
    generated = build_figures(
        summary=summary,
        predictions=predictions,
        fitted_values=fitted_values,
        formulas=formulas,
        r2=r2,
        fig_dir=fig_dir,
        output_dir=output_dir,
    )
    manifest = pd.DataFrame(
        [
            {
                "figure_id": key,
                "path": str(path),
                "status": "available" if path.exists() else "missing",
            }
            for key, path in sorted(generated.items())
        ]
    )
    manifest.to_csv(output_dir / "formula_report_figure_manifest.csv", index=False)

    doc_path = doc_dir / f"{DOC_BASENAME}.md"
    html_path = doc_path.with_suffix(".html")
    embedded_path = doc_path.with_suffix(".embedded.html")
    write_report(
        doc_path=doc_path,
        output_dir=output_dir,
        fig_dir=fig_dir,
        formulas=formulas,
        summary=summary,
        r2=r2,
        generated=generated,
    )
    render_markdown_file(doc_path, html_path)
    render_markdown_file(doc_path, embedded_path, embed_images=True)
    return {"md": doc_path, "html": html_path, "embedded_html": embedded_path}


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=ROUTE1_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = run(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_dir=args.doc_dir,
        chunksize=args.chunksize,
        force=args.force,
    )
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
