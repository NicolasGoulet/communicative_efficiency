#!/usr/bin/env python3
"""Build old-style fixed-effort atlases for each Route 1 source.

This is the plot-heavy report layer for the corrected source-specific fits.
It deliberately mirrors the older M1-M6 atlas style: fit summaries,
coefficient tables, fixed-effort prediction slices, slope summaries, figure
manifests, Markdown, HTML, and PDF-ready files. It covers the full corrected
model ladder, including M1-M6 and extended M7-M15 families.
"""

from __future__ import annotations

import argparse
import gc
import math
import os
import sys
from dataclasses import asdict
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
    from build_route1_corrected_baseline_atlas import (
        DEFAULT_CONTEXT_KS,
        DEFAULT_MODEL_IDS,
        DEFAULT_TARGET_SOURCES,
        EFFORT_SPECS,
        QUESTION_TYPE_ORDER,
        CorrectedModelSpec,
        concrete_specs,
        fit_prepared_model,
        markdown_table,
        prepare_model_frame,
        read_route1_rows,
        selected_effort_specs,
        split_csv,
    )
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_corrected_baseline_atlas import (
        DEFAULT_CONTEXT_KS,
        DEFAULT_MODEL_IDS,
        DEFAULT_TARGET_SOURCES,
        EFFORT_SPECS,
        QUESTION_TYPE_ORDER,
        CorrectedModelSpec,
        concrete_specs,
        fit_prepared_model,
        markdown_table,
        prepare_model_frame,
        read_route1_rows,
        selected_effort_specs,
        split_csv,
    )
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_source_specific_corrected_fixed_effort_atlas")
DEFAULT_FIG_DIR = Path("figs/route1_source_specific_corrected_fixed_effort_atlas")
DEFAULT_DOC_DIR = Path("docs")
AGE_SCRAMBLING_OUTPUT_DIR = Path("results/age_scrambling_robustness")
AGE_SCRAMBLING_FIG_DIR = Path("figs/age_scrambling_robustness")
AGE_SCRAMBLING_DOC_MD = Path("docs/utterance_information_age_scrambling_robustness.md")
AGE_SCRAMBLING_DOC_HTML = Path("docs/utterance_information_age_scrambling_robustness.html")
VERSION_SENSITIVITY_PATH = (
    Path("results/route1_corrected_baseline_atlas/full_child_structure_sensitivity/source_specific_model_summary.csv")
)
REAL_ESTIMATOR_SENSITIVITY_PATH = Path("results/m1_m2_utterance_information_deep_dive/expanded_model_family_summary.csv")
REAL_ESTIMATOR_FIG_DIR = Path("figs/m1_m2_utterance_information_deep_dive")
REPORT_MODEL_IDS = DEFAULT_MODEL_IDS

MODEL_TAKEAWAYS = {
    "M1": "Pooled age and effort baseline. Useful as a sanity check, but not sufficient for developmental interpretation because child identity is not controlled.",
    "M2": "First child-adjusted model. This is the compact test of whether the age effect remains after target effort and child identity are controlled.",
    "M3": "Age-by-effort model. The fixed-effort plots are central here because they show whether the age trend depends on utterance size.",
    "M4a": "Adds preceding caretaker-context effort. This checks whether local context amount explains additional target information.",
    "M4b": "Adds context entropy. This checks whether the age pattern survives the available next-token context-entropy control.",
    "M4c": "Adds broad question type. This checks whether local interrogative structure explains additional target information.",
    "M5": "Combines context effort, context entropy, and question type with the age-by-effort child-adjusted model.",
    "M6": "Interaction stress test for age/effort with context entropy. Useful for robustness, not a first-pass headline by itself.",
    "M7": "Nonlinear age model. Checks whether a curved developmental trajectory fits better than a straight age slope.",
    "M8": "Nonlinear age-by-effort model. Checks whether curved developmental change depends on target utterance effort.",
    "M9": "Categorical age-bin trajectory. Checks developmental shape without forcing one continuous age slope.",
    "M10": "Age-bin-by-effort model. Checks whether age-bin differences vary across target effort.",
    "M11": "Age-by-parent-context-effort model. Tests whether the age pattern changes with preceding context effort.",
    "M12": "Age-by-question-type model. Tests whether the age pattern differs across broad preceding-context question types.",
    "M13": "Context-entropy-by-question-type model. Tests whether context entropy behaves differently by question type.",
    "M14": "Parent-context-effort-by-context-entropy model. Tests whether context amount and entropy carry separable information.",
    "M15": "Expanded context interaction stress test. Checks the richest corrected interaction set in the current ladder.",
}

COEFFICIENT_NAMES = (
    ("age_c", "age_coef", "age_p"),
    ("effort_c", "effort_coef", "effort_p"),
    ("parent_context_effort_c", "parent_context_effort_coef", "parent_context_effort_p"),
    ("context_entropy_c", "context_entropy_coef", "context_entropy_p"),
    ("age_c:effort_c", "age_effort_coef", "age_effort_p"),
    ("age_c:context_entropy_c", "age_entropy_coef", "age_entropy_p"),
    ("effort_c:context_entropy_c", "effort_entropy_coef", "effort_entropy_p"),
    ("I(age_c ** 2)", "age_quadratic_coef", "age_quadratic_p"),
    ("I(age_c ** 2):effort_c", "age_quadratic_effort_coef", "age_quadratic_effort_p"),
    ("age_c:parent_context_effort_c", "age_parent_context_effort_coef", "age_parent_context_effort_p"),
    ("effort_c:parent_context_effort_c", "effort_parent_context_effort_coef", "effort_parent_context_effort_p"),
    ("parent_context_effort_c:context_entropy_c", "parent_context_effort_entropy_coef", "parent_context_effort_entropy_p"),
)


def slugify(value: str) -> str:
    """Return a filename-safe slug."""

    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def format_p(value: object) -> str:
    """Format p-values for report tables."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def param_value(result: object, name: str, attr: str = "params") -> float:
    """Extract a named parameter from statsmodels results."""

    if result is None or not hasattr(result, attr):
        return math.nan
    values = getattr(result, attr)
    try:
        if hasattr(values, "get"):
            value = values.get(name, math.nan)
        else:
            names = list(getattr(result.model, "exog_names", []))
            value = values[names.index(name)] if name in names else math.nan
        return float(value)
    except Exception:
        return math.nan


def prediction_summary_frame(result: object, new_frame: pd.DataFrame) -> pd.DataFrame:
    """Return predicted means and model-confidence bands."""

    try:
        summary = result.get_prediction(new_frame).summary_frame(alpha=0.05)
    except Exception:
        pred = np.asarray(result.predict(new_frame), dtype=float)
        return pd.DataFrame({"predicted_sum_bits": pred, "pred_ci_low": np.nan, "pred_ci_high": np.nan})
    mean_col = "mean" if "mean" in summary.columns else "predicted_mean" if "predicted_mean" in summary.columns else None
    low_col = "mean_ci_lower" if "mean_ci_lower" in summary.columns else "ci_lower" if "ci_lower" in summary.columns else None
    high_col = "mean_ci_upper" if "mean_ci_upper" in summary.columns else "ci_upper" if "ci_upper" in summary.columns else None
    return pd.DataFrame(
        {
            "predicted_sum_bits": np.asarray(summary[mean_col], dtype=float)
            if mean_col
            else np.asarray(result.predict(new_frame), dtype=float),
            "pred_ci_low": np.asarray(summary[low_col], dtype=float) if low_col else np.nan,
            "pred_ci_high": np.asarray(summary[high_col], dtype=float) if high_col else np.nan,
        }
    )


def coefficient_long_table(result: object, spec: CorrectedModelSpec) -> pd.DataFrame:
    """Return one row per fitted coefficient term."""

    if result is None or not hasattr(result, "params"):
        return pd.DataFrame()
    params = getattr(result, "params")
    names = list(params.index) if hasattr(params, "index") else list(getattr(result.model, "exog_names", []))
    pvalues = getattr(result, "pvalues", None)
    try:
        conf = result.conf_int()
    except Exception:
        conf = None
    rows: list[dict[str, object]] = []
    for idx, term in enumerate(names):
        try:
            estimate = float(params[term]) if hasattr(params, "__getitem__") and term in params else float(params[idx])
        except Exception:
            estimate = math.nan
        try:
            p_value = float(pvalues[term]) if hasattr(pvalues, "__getitem__") and term in pvalues else float(pvalues[idx])
        except Exception:
            p_value = math.nan
        ci_low = math.nan
        ci_high = math.nan
        if conf is not None:
            try:
                if hasattr(conf, "loc"):
                    ci_low = float(conf.loc[term].iloc[0])
                    ci_high = float(conf.loc[term].iloc[1])
                else:
                    ci_low = float(conf[idx][0])
                    ci_high = float(conf[idx][1])
            except Exception:
                pass
        rows.append(
            {
                "target_source": spec.target_source,
                "context_k": spec.context_k,
                "effort_col": spec.effort_col,
                "effort_label": spec.effort_label,
                "model_id": spec.model_id,
                "model_label": spec.model_label,
                "model_tier": spec.model_tier,
                "child_structure": spec.child_structure,
                "term": str(term),
                "estimate": estimate,
                "p_value": p_value,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "is_child_fixed_effect": str(term).startswith("C(child_id)"),
                "is_age_bin_term": "age_bin" in str(term),
                "is_question_type_term": "question_type" in str(term),
            }
        )
    return pd.DataFrame(rows)


def split_ordered_values(values: Sequence[int]) -> list[tuple[str, list[int]]]:
    ordered = sorted({int(value) for value in values if int(value) > 0})
    chunks = np.array_split(np.array(ordered), 3) if ordered else []
    labels = ["low representative sizes", "middle representative sizes", "high representative sizes"]
    return [(label, [int(value) for value in chunk.tolist()]) for label, chunk in zip(labels, chunks) if len(chunk)]


def age_bins_for_grid(model_frame: pd.DataFrame, ages: np.ndarray) -> list[str]:
    """Assign each plotted age to an observed age-bin level."""

    if "age_bin" not in model_frame.columns:
        return [""] * len(ages)
    valid = model_frame[["age_months", "age_bin"]].copy()
    valid["age_months"] = pd.to_numeric(valid["age_months"], errors="coerce")
    valid["age_bin"] = valid["age_bin"].astype(str)
    valid = valid.dropna(subset=["age_months"])
    valid = valid[valid["age_bin"].ne("")]
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
        distances = (containing["median"] - age).abs()
        assigned.append(str(containing.iloc[int(distances.to_numpy().argmin())]["age_bin"]))
    return assigned


def fixed_effort_bins(frame: pd.DataFrame) -> pd.DataFrame:
    """Return fixed-effort bin definitions for every effort unit."""

    rows: list[dict[str, object]] = []
    for spec in EFFORT_SPECS:
        effort_col = spec.effort_col
        if effort_col in {"nb_words", "nb_morphemes"}:
            bins = [
                ("1-4", [1, 2, 3, 4], "Exact fixed values 1-4."),
                ("5-8", [5, 6, 7, 8], "Exact fixed values 5-8."),
                ("9-12", [9, 10, 11, 12], "Exact fixed values 9-12."),
            ]
        else:
            counts = pd.to_numeric(frame[effort_col], errors="coerce").dropna().astype(int).value_counts().head(12)
            bins = [
                (label, values, "Ordered split of the 12 most frequent observed exact values.")
                for label, values in split_ordered_values(counts.index.astype(int).tolist())
            ]
        for atlas_bin, values, rule in bins:
            support = frame[pd.to_numeric(frame[effort_col], errors="coerce").isin(values)]
            rows.append(
                {
                    "effort_col": effort_col,
                    "effort_label": spec.effort_label,
                    "atlas_bin": atlas_bin,
                    "fixed_values": ", ".join(str(value) for value in values),
                    "n_fixed_values": len(values),
                    "support_rows": int(len(support)),
                    "support_children": int(support["child_id"].nunique()) if not support.empty else 0,
                    "rule": rule,
                }
            )
    return pd.DataFrame(rows)


def average_child_predictions(
    result: object,
    base: pd.DataFrame,
    child_ids: Sequence[str],
    *,
    has_child_id: bool,
) -> pd.DataFrame:
    """Predict fixed slices, averaging over child fixed intercepts if present."""

    if not has_child_id:
        pred = prediction_summary_frame(result, base)
        return pd.concat([base.reset_index(drop=True), pred.reset_index(drop=True)], axis=1)
    parts: list[pd.DataFrame] = []
    for child_id in child_ids:
        child_frame = base.copy()
        child_frame["child_id"] = child_id
        pred = prediction_summary_frame(result, child_frame)
        parts.append(pd.concat([child_frame.reset_index(drop=True), pred.reset_index(drop=True)], axis=1))
    combined = pd.concat(parts, ignore_index=True)
    group_cols = ["age_months", "fixed_effort_value", "atlas_bin", "model_id", "effort_col"]
    return (
        combined.groupby(group_cols, as_index=False)[["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]]
        .mean()
        .copy()
    )


def fixed_prediction_grid(
    *,
    result: object,
    model_frame: pd.DataFrame,
    bin_defs: pd.DataFrame,
    spec: CorrectedModelSpec,
    n_points: int,
) -> pd.DataFrame:
    """Generate fixed-effort age predictions for one fitted model."""

    ages = np.linspace(model_frame["age_months"].quantile(0.02), model_frame["age_months"].quantile(0.98), n_points)
    child_ids = sorted(model_frame["child_id"].astype(str).unique())
    age_bins = age_bins_for_grid(model_frame, ages)
    modal_question = (
        str(model_frame["question_type"].mode(dropna=True).iloc[0])
        if "question_type" in model_frame and not model_frame["question_type"].dropna().empty
        else "not question"
    )
    parts: list[pd.DataFrame] = []
    for item in bin_defs[bin_defs["effort_col"].eq(spec.effort_col)].to_dict("records"):
        values = [int(value.strip()) for value in str(item["fixed_values"]).split(",") if value.strip()]
        for fixed_value in values:
            base = pd.DataFrame(
                {
                    "age_months": ages,
                    "age_bin": age_bins,
                    "age_c": ages - float(model_frame["age_months"].mean()),
                    "effort_value": fixed_value,
                    "effort_c": fixed_value - float(model_frame["effort_value"].mean()),
                    "parent_context_effort_value": float(model_frame["parent_context_effort_value"].mean())
                    if "parent_context_effort_value" in model_frame
                    else 0.0,
                    "parent_context_effort_c": 0.0,
                    "context_entropy_bits": float(model_frame["context_entropy_bits"].mean())
                    if "context_entropy_bits" in model_frame
                    else 0.0,
                    "context_entropy_c": 0.0,
                    "question_type": pd.Categorical([modal_question] * len(ages), categories=QUESTION_TYPE_ORDER),
                    "fixed_effort_value": int(fixed_value),
                    "atlas_bin": str(item["atlas_bin"]),
                    "model_id": spec.model_id,
                    "effort_col": spec.effort_col,
                }
            )
            parts.append(
                average_child_predictions(
                    result,
                    base,
                    child_ids,
                    has_child_id="C(child_id)" in spec.statsmodels_formula,
                )
            )
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fit_one_spec(
    frame: pd.DataFrame,
    spec: CorrectedModelSpec,
    bin_defs: pd.DataFrame,
    *,
    n_points: int,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    """Fit one spec and return report summary, predictions, and coefficients."""

    model_frame, prepare_error = prepare_model_frame(frame, spec)
    row = asdict(spec)
    row.update(
        {
            "n_obs": int(len(model_frame)),
            "n_children": int(model_frame["child_id"].nunique()) if "child_id" in model_frame else 0,
            "status": "skipped" if prepare_error else "fit",
            "error": prepare_error,
            "r2_observed_fitted": math.nan,
            "aic": math.nan,
            "bic": math.nan,
        }
    )
    for _, coef_col, p_col in COEFFICIENT_NAMES:
        row[coef_col] = math.nan
        row[p_col] = math.nan
    if prepare_error:
        return row, pd.DataFrame(), pd.DataFrame()
    result, fit_error = fit_prepared_model(model_frame, spec)
    if fit_error or result is None:
        row["status"] = "failed"
        row["error"] = fit_error
        return row, pd.DataFrame(), pd.DataFrame()
    row["r2_observed_fitted"] = float(getattr(result, "rsquared", math.nan))
    row["aic"] = float(getattr(result, "aic", math.nan)) if hasattr(result, "aic") else math.nan
    row["bic"] = float(getattr(result, "bic", math.nan)) if hasattr(result, "bic") else math.nan
    for param_name, coef_col, p_col in COEFFICIENT_NAMES:
        row[coef_col] = param_value(result, param_name)
        row[p_col] = param_value(result, param_name, "pvalues")
    coefficients = coefficient_long_table(result, spec)
    predictions = fixed_prediction_grid(result=result, model_frame=model_frame, bin_defs=bin_defs, spec=spec, n_points=n_points)
    if not predictions.empty:
        predictions["target_source"] = spec.target_source
        predictions["context_k"] = spec.context_k
        predictions["model_label"] = spec.model_label
        predictions["model_tier"] = spec.model_tier
        predictions["effort_label"] = spec.effort_label
    try:
        result.remove_data()
    except Exception:
        pass
    return row, predictions, coefficients


def fit_source_atlas(
    frame: pd.DataFrame,
    *,
    source: str,
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    n_points: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit the core source-specific atlas and build prediction grids."""

    bin_defs = fixed_effort_bins(frame)
    specs = concrete_specs(
        target_sources=(source,),
        context_ks=context_ks,
        effort_specs=selected_effort_specs(effort_cols),
        model_ids=model_ids,
        child_structures=("primary",),
        stage="source_specific_corrected_fixed_effort_atlas_v2",
    )
    rows: list[dict[str, object]] = []
    prediction_parts: list[pd.DataFrame] = []
    coefficient_parts: list[pd.DataFrame] = []
    for idx, spec in enumerate(specs, start=1):
        print(f"[fit] {source} {idx}/{len(specs)} {spec.context_k} {spec.model_id} {spec.effort_col}", flush=True)
        row, predictions, coefficients = fit_one_spec(frame, spec, bin_defs, n_points=n_points)
        rows.append(row)
        if not predictions.empty:
            prediction_parts.append(predictions)
        if not coefficients.empty:
            coefficient_parts.append(coefficients)
        gc.collect()
    summary = pd.DataFrame(rows)
    predictions = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    coefficients = pd.concat(coefficient_parts, ignore_index=True) if coefficient_parts else pd.DataFrame()
    bin_defs["target_source"] = source
    return summary, predictions, coefficients, bin_defs


def plot_fixed_predictions(predictions: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    """Plot fixed-effort atlas figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    group_cols = ["target_source", "context_k", "model_id", "model_label", "effort_col", "effort_label"]
    for keys, group in predictions.groupby(group_cols, sort=True):
        source, context_k, model_id, model_label, effort_col, effort_label = keys
        bins = list(group["atlas_bin"].drop_duplicates())
        fig, axes = plt.subplots(1, len(bins), figsize=(5.8 * len(bins), 4.9), sharey=True)
        if len(bins) == 1:
            axes = [axes]
        for ax, atlas_bin in zip(axes, bins):
            panel = group[group["atlas_bin"].eq(atlas_bin)].copy()
            values = sorted(int(value) for value in panel["fixed_effort_value"].unique())
            palette = sns.color_palette("viridis", n_colors=max(1, len(values)))
            color_map = {value: palette[idx] for idx, value in enumerate(values)}
            for fixed_value, line in panel.groupby("fixed_effort_value", sort=True):
                color = color_map[int(fixed_value)]
                ax.plot(line["age_months"], line["predicted_sum_bits"], color=color, linewidth=2.0, label=str(int(fixed_value)))
                if line[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                    ax.fill_between(
                        line["age_months"].to_numpy(dtype=float),
                        line["pred_ci_low"].to_numpy(dtype=float),
                        line["pred_ci_high"].to_numpy(dtype=float),
                        color=color,
                        alpha=0.08,
                        linewidth=0,
                    )
            ax.set_title(atlas_bin)
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
            ax.legend(title="Fixed value", fontsize=8, title_fontsize=9)
        axes[0].set_ylabel("Predicted total bits")
        fig.suptitle(f"{source} | {context_k.upper()} {model_id}: {model_label} | {effort_label}", y=1.05)
        fig.tight_layout()
        filename = f"{slugify(source)}_{context_k}_{model_id.lower()}_{slugify(effort_col)}_fixed_effort_atlas.png"
        out = fig_dir / filename
        fig.savefig(out, dpi=210, bbox_inches="tight")
        fig.savefig(fig_dir / filename.replace(".png", ".pdf"), bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "target_source": source,
                "context_k": context_k,
                "model_id": model_id,
                "model_label": model_label,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "figure": str(out),
            }
        )
    return pd.DataFrame(rows)


def fixed_slice_slopes(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive slopes from plotted fixed-effort lines."""

    if predictions.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    keys = [
        "target_source",
        "context_k",
        "model_id",
        "model_label",
        "effort_col",
        "effort_label",
        "atlas_bin",
        "fixed_effort_value",
    ]
    for key, group in predictions.groupby(keys, sort=True):
        source, context_k, model_id, model_label, effort_col, effort_label, atlas_bin, fixed_value = key
        ages = group["age_months"].to_numpy(dtype=float)
        bits = group["predicted_sum_bits"].to_numpy(dtype=float)
        slope = float(np.polyfit(ages, bits, 1)[0]) if len(np.unique(ages)) >= 2 else math.nan
        rows.append(
            {
                "target_source": source,
                "context_k": context_k,
                "model_id": model_id,
                "model_label": model_label,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "atlas_bin": atlas_bin,
                "fixed_effort_value": int(fixed_value),
                "slope_bits_per_month": slope,
                "slope_bits_per_6_months": slope * 6 if math.isfinite(slope) else math.nan,
                "direction": "downward" if slope < 0 else "upward" if slope > 0 else "flat",
            }
        )
    return pd.DataFrame(rows)


def slope_summary(slopes: pd.DataFrame) -> pd.DataFrame:
    """Summarize plotted fixed-slice slopes."""

    if slopes.empty:
        return pd.DataFrame()
    return (
        slopes.groupby(["target_source", "context_k", "model_id", "model_label", "effort_label", "atlas_bin"], observed=True)
        .agg(
            n_fixed_slices=("fixed_effort_value", "nunique"),
            negative_slices=("slope_bits_per_month", lambda values: int((values < 0).sum())),
            positive_slices=("slope_bits_per_month", lambda values: int((values > 0).sum())),
            mean_slope_bits_per_month=("slope_bits_per_month", "mean"),
            min_slope_bits_per_month=("slope_bits_per_month", "min"),
            max_slope_bits_per_month=("slope_bits_per_month", "max"),
        )
        .reset_index()
    )


def fit_overview(summary: pd.DataFrame) -> pd.DataFrame:
    """Return compact fit overview."""

    fitted = summary[summary["status"].eq("fit")].copy()
    if fitted.empty:
        return pd.DataFrame()
    return (
        fitted.groupby(["target_source", "context_k", "model_id", "model_label"], observed=True)
        .agg(
            fitted_rows=("status", "size"),
            mean_r2=("r2_observed_fitted", "mean"),
            negative_age_coef_rows=("age_coef", lambda values: int((pd.to_numeric(values, errors="coerce") < 0).sum())),
            significant_age_rows=("age_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_effort_rows=("effort_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_context_entropy_rows=("context_entropy_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
        )
        .reset_index()
    )


def coefficient_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Return readable coefficient table."""

    cols = [
        "target_source",
        "context_k",
        "model_id",
        "model_label",
        "effort_label",
        "n_obs",
        "n_children",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "effort_coef",
        "effort_p",
        "parent_context_effort_coef",
        "parent_context_effort_p",
        "context_entropy_coef",
        "context_entropy_p",
        "age_effort_coef",
        "age_effort_p",
        "age_entropy_coef",
        "age_entropy_p",
        "effort_entropy_coef",
        "effort_entropy_p",
        "age_quadratic_coef",
        "age_quadratic_p",
        "age_quadratic_effort_coef",
        "age_quadratic_effort_p",
        "age_parent_context_effort_coef",
        "age_parent_context_effort_p",
        "effort_parent_context_effort_coef",
        "effort_parent_context_effort_p",
        "parent_context_effort_entropy_coef",
        "parent_context_effort_entropy_p",
    ]
    out = summary[summary["status"].eq("fit")][[col for col in cols if col in summary.columns]].copy()
    for col in [column for column in out.columns if column.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def formula_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Return one row per model formula."""

    cols = ["model_id", "model_label", "question", "readable_formula", "statsmodels_formula"]
    out = summary[cols].drop_duplicates("model_id").copy()
    order = {model_id: idx for idx, model_id in enumerate(DEFAULT_MODEL_IDS)}
    out["_order"] = out["model_id"].map(order).fillna(len(order))
    return out.sort_values(["_order", "model_id"]).drop(columns=["_order"]).reset_index(drop=True)


def model_reader_card(summary: pd.DataFrame, model_id: str) -> list[str]:
    """Plain-language model card for the reader-facing atlas."""

    rows = summary[summary["model_id"].astype(str).eq(model_id)].copy()
    if rows.empty:
        return []
    row = rows.iloc[0]
    fitted = rows[rows["status"].eq("fit")].copy()
    contexts = ", ".join(str(value).upper() for value in sorted(rows["context_k"].dropna().unique()))
    efforts = ", ".join(str(value) for value in sorted(rows["effort_label"].dropna().unique()))
    if not fitted.empty and "n_obs" in fitted:
        n_obs_text = f"{int(fitted['n_obs'].min()):,}-{int(fitted['n_obs'].max()):,}"
    else:
        n_obs_text = "not available"
    if not fitted.empty and "r2_observed_fitted" in fitted:
        mean_r2 = float(fitted["r2_observed_fitted"].mean())
        r2_text = f"{mean_r2:.3f}" if math.isfinite(mean_r2) else "not available"
    else:
        r2_text = "not available"
    controls = [
        "`age_c`: child age in months, centered",
        "`effort_c`: the centered effort measure named under each plot",
    ]
    formula = str(row.get("readable_formula", "")).strip()
    statsmodels_formula = str(row.get("statsmodels_formula", "")).strip()
    question = str(row.get("question", "")).strip()
    label = str(row.get("model_label", "")).strip()
    return [
        f"### {model_id}: {label}",
        "",
        f"**Question.** {question}",
        "",
        "**Regression type.** Linear regression / ordinary least squares.",
        "",
        "**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.",
        "",
        "**Outcome.** `sum_bits`: total information of the target utterance for this source.",
        "",
        f"**Formula.** `{formula}`",
        "",
        f"**Statsmodels formula.** `{statsmodels_formula}`",
        "",
        "**Core controls.** " + "; ".join(controls) + ".",
        "",
        f"**Coverage.** {len(fitted)}/{len(rows)} fitted combinations across {contexts}; effort axes: {efforts}. Observations per fitted combination: {n_obs_text}. Mean descriptive R2: {r2_text}.",
        "",
        f"**Plain read.** {MODEL_TAKEAWAYS.get(model_id, '')}",
        "",
        "**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.",
        "",
    ]


def figure_link(report_path: Path, figure_path: str) -> str:
    """Return a Markdown-relative figure path."""

    return relative_to_report(report_path, figure_path)


def relative_to_report(report_path: Path, figure_path: str) -> str:
    """Return a figure path that works from the Markdown/HTML report file."""

    report_base = report_path if report_path.suffix == "" else report_path.parent
    try:
        return os.path.relpath(Path(figure_path).resolve(), start=report_base.resolve()).replace(os.sep, "/")
    except ValueError:
        return Path(figure_path).resolve().as_posix()


def age_scrambling_section(*, report_dir: Path) -> list[str]:
    """Return the real-child age-scrambling robustness section if artifacts exist."""

    audit_path = AGE_SCRAMBLING_OUTPUT_DIR / "age_scrambling_audit.csv"
    summary_path = AGE_SCRAMBLING_OUTPUT_DIR / "age_scrambling_robustness_summary.csv"
    figure_manifest_path = AGE_SCRAMBLING_OUTPUT_DIR / "age_scrambling_figure_manifest.csv"
    clear_figure_manifest_path = AGE_SCRAMBLING_OUTPUT_DIR / "age_scrambling_clear_figure_manifest.csv"
    if not (audit_path.exists() and summary_path.exists() and figure_manifest_path.exists()):
        return [
            "## Real-Child Age-Scrambling Robustness",
            "",
            "_No saved age-scrambling robustness artifacts were found for the real-child data._",
            "",
        ]
    audit = pd.read_csv(audit_path)
    summary = pd.read_csv(summary_path)
    figures = pd.read_csv(figure_manifest_path)
    clear_figures = pd.read_csv(clear_figure_manifest_path) if clear_figure_manifest_path.exists() else pd.DataFrame()
    compact_summary = (
        summary.groupby(["context_k", "model_id", "robustness_method"], observed=True)
        .agg(
            fitted_rows=("observed_age_coef", "size"),
            outside_null_95_rows=("observed_outside_null_95", lambda values: int(pd.Series(values).astype(bool).sum())),
            mean_observed_age_coef=("observed_age_coef", "mean"),
            mean_null_age_coef=("null_mean_age_coef", "mean"),
        )
        .reset_index()
        if not summary.empty
        else pd.DataFrame()
    )
    lines = [
        "## Real-Child Age-Scrambling Robustness",
        "",
        "This sub-analysis is available for the real-child rows and is included here because it checks whether the real developmental age effect survives balanced age-bin resampling and weakens when age structure is deliberately scrambled.",
        "",
        "Full standalone report:",
        "",
        f"- Markdown: `{AGE_SCRAMBLING_DOC_MD}`",
        f"- HTML: `{AGE_SCRAMBLING_DOC_HTML}`",
        "",
        "The audit and observed-vs-scrambled result tables remain saved in the age-scrambling artifact directory. This reader view keeps the visual checks in the report body.",
        "",
        "### Robustness Figures",
        "",
    ]
    for row in figures.to_dict("records"):
        path = Path(str(row["path"]))
        if not path.exists():
            continue
        rel = relative_to_report(report_dir, str(path))
        lines.extend([f"**{row['description']}**", "", f"![{row['figure_id']}]({rel})", ""])
    if not clear_figures.empty:
        lines.extend(["### Clear Regression-Line Robustness Figures", ""])
        for row in clear_figures.to_dict("records"):
            path = Path(str(row["path"]))
            if not path.exists():
                continue
            rel = relative_to_report(report_dir, str(path))
            lines.extend([f"**{row['description']}**", "", f"![{row['figure_id']}]({rel})", ""])
    return lines


def model_version_section(source: str, *, report_dir: Path) -> list[str]:
    """Return the saved estimator/structure/version sensitivity section."""

    lines = [
        "## Model-Version And Estimator Sensitivity",
        "",
        "The primary fixed-effort atlas above is the corrected source-specific M1-M15 ladder. This section records the saved model-version layer: child-structure variants, estimator variants, and formula versions that are available on disk.",
        "",
    ]
    if VERSION_SENSITIVITY_PATH.exists():
        version = pd.read_csv(VERSION_SENSITIVITY_PATH)
        if "target_source" in version:
            version = version[version["target_source"].astype(str).eq(source)].copy()
        if not version.empty:
            cols = [
                "model_id",
                "model_label",
                "context_k",
                "effort_label",
                "child_structure",
                "estimator",
                "covariance",
                "random_effects",
                "readable_formula",
                "status",
                "n_obs",
                "n_children",
                "r2",
                "error",
            ]
            status = (
                version.groupby(["model_id", "child_structure", "estimator", "covariance", "status"], dropna=False)
                .size()
                .reset_index(name="rows")
            )
            lines.extend(
                [
                    "### Corrected Child-Structure / Estimator Versions",
                    "",
                    "These saved rows include pooled OLS, child-clustered OLS, child fixed intercepts, child fixed intercepts plus age slopes, GEE grouped by child, MixedLM random child intercept/slope variants, within-child age, and Mundlak within/between age variants where they were fit.",
                    "",
                    f"Saved CSV: `{VERSION_SENSITIVITY_PATH}`",
                    "",
                    f"Rows available for this source: `{len(version)}`. The full table is intentionally not printed in this reader view.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "### Corrected Child-Structure / Estimator Versions",
                    "",
                    f"_No corrected version-sensitivity rows are currently saved for `{source}` in `{VERSION_SENSITIVITY_PATH}`._",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "### Corrected Child-Structure / Estimator Versions",
                "",
                f"_No saved corrected version-sensitivity file was found at `{VERSION_SENSITIVITY_PATH}`._",
                "",
            ]
        )
    if source == "real" and REAL_ESTIMATOR_SENSITIVITY_PATH.exists():
        estimator = pd.read_csv(REAL_ESTIMATOR_SENSITIVITY_PATH)
        cols = [
            "approach_id",
            "model_family_id",
            "model_family_label",
            "effort_label",
            "readable_formula",
            "fit_type",
            "effect_scale",
            "status",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
            "age_effort_coef",
            "age_effort_p",
        ]
        for col in [column for column in estimator.columns if column.endswith("_p")]:
            estimator[col] = estimator[col].map(format_p)
        status = (
            estimator.groupby(["approach_id", "model_family_id", "fit_type", "effect_scale", "status"], dropna=False)
            .size()
            .reset_index(name="rows")
        )
        lines.extend(
            [
                "### Real-Child V1 Estimator Family Versions",
                "",
                "These are the saved Atlas v1 estimator-family rows for the real-child data, including OLS, child-clustered OLS, Gaussian GLM, Gamma/log GLM, GEE, and MixedLM variants where the old report fit them.",
                "",
                f"Saved CSV: `{REAL_ESTIMATOR_SENSITIVITY_PATH}`",
                "",
                f"Rows available: `{len(estimator)}`. The full estimator table is intentionally not printed in this reader view.",
                "",
            ]
        )
        if REAL_ESTIMATOR_FIG_DIR.exists():
            pngs = sorted(
                path
                for path in REAL_ESTIMATOR_FIG_DIR.glob("*.png")
                if any(
                    token in path.name
                    for token in [
                        "adjusted_age_lines",
                        "interaction_age_lines",
                        "expanded_age_coefficients",
                        "expanded_interaction_coefficients",
                        "expanded_r2",
                        "m4_",
                        "m5_",
                        "m6_",
                    ]
                )
            )
            lines.extend(["### Real-Child V1 Expanded-Model Figure Gallery", ""])
            for path in pngs:
                rel = relative_to_report(report_dir, str(path))
                title = path.stem.replace("_", " ")
                lines.extend([f"**{title}**", "", f"![{title}]({rel})", ""])
    return lines


def build_markdown(
    *,
    source: str,
    summary: pd.DataFrame,
    bin_defs: pd.DataFrame,
    figure_manifest: pd.DataFrame,
    slopes: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
    report_dir: Path,
) -> str:
    """Build old-style Markdown report for one source."""

    skipped = summary[summary["status"].ne("fit")].copy()
    lines: list[str] = [
        f"# Route 1 Corrected Fixed-Effort Atlas v2: {source}",
        "",
        "This report rebuilds the old plot-heavy M1-M6 atlas style for one target source, with the corrected extended M1-M15 model ladder.",
        "The model ladder is fit independently for this source, not pooled across real/generated conditions.",
        "",
        "## Implementation",
        "",
        "- Estimator: linear ordinary least squares regression.",
        "- Library: `statsmodels.formula.api.ols` through the corrected Route 1 atlas code.",
        "- Uncertainty: child-cluster robust standard errors for the primary child-adjusted models.",
        "- Outcome: `sum_bits`, the total utterance information for this target source.",
        "- Fixed slices: the model is fit on all eligible rows; fixed effort values only define plotted prediction lines.",
        "- Context predictors in prediction slices are held at their fitted-data means; question type is held at its modal level.",
        "",
        "## Start Here",
        "",
        "Each section below is one model. It starts with the model question, formula, regression type, library, uncertainty structure, and then the plots. Long tables are kept out of the report body and saved as CSV artifacts.",
        "",
        "## Model Atlas",
        "",
    ]
    model_order = [model_id for model_id in DEFAULT_MODEL_IDS if model_id in set(summary["model_id"].astype(str))]
    for model_id in model_order:
        model_figs_all = figure_manifest[figure_manifest["model_id"].astype(str).eq(model_id)].copy()
        if model_figs_all.empty:
            continue
        lines.extend(model_reader_card(summary, model_id))
        for context_k in sorted(model_figs_all["context_k"].dropna().unique()):
            model_figs = model_figs_all[model_figs_all["context_k"].eq(context_k)].copy()
            if model_figs.empty:
                continue
            lines.extend([f"#### {context_k.upper()} plots", ""])
            for row in model_figs.sort_values("effort_label").to_dict("records"):
                rel = relative_to_report(report_dir, str(row["figure"]))
                lines.extend([f"**{row['effort_label']}**", "", f"![{context_k} {model_id} {row['effort_label']}]({rel})", ""])
    lines.extend(model_version_section(source, report_dir=report_dir))
    if source == "real":
        lines.extend(age_scrambling_section(report_dir=report_dir))
    lines.extend(
        [
            "## Saved Tables And Artifacts",
            "",
            "The long coefficient tables, fixed-effort prediction grids, slice definitions, and slope summaries are saved as CSV artifacts. They are intentionally not printed in this HTML report because the consultation layer is the model cards and plots above.",
            "",
        ]
    )
    if not skipped.empty:
        lines.extend(
            [
                "### Skipped Or Failed Fits",
                "",
                "Some requested model/context/effort combinations did not fit. The exact rows are saved in `model_summary.csv`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Saved Outputs",
            "",
            "```text",
            str(output_dir / "model_summary.csv"),
            str(output_dir / "coefficient_long.csv"),
            str(output_dir / "fixed_effort_predictions.csv.gz"),
            str(output_dir / "fixed_slice_slopes.csv"),
            str(output_dir / "figure_manifest.csv"),
            f"{fig_dir}/",
            "```",
        ]
    )
    return "\n".join(lines)


def render_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Render PDF using headless Brave when available."""

    import shutil
    import subprocess

    browser = shutil.which("brave-browser") or shutil.which("google-chrome")
    if not browser:
        return False
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
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
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def run_source(
    *,
    input_csv: Path,
    source: str,
    output_root: Path,
    fig_root: Path,
    doc_dir: Path,
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
    n_points: int,
    render_pdf_file: bool,
    stage: str,
) -> dict[str, Path]:
    """Build analysis artifacts and reports for one source."""

    source_slug = slugify(source)
    output_dir = output_root / source_slug
    fig_dir = fig_root / source_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    if stage in {"all", "analysis"}:
        print(f"[read] {source}", flush=True)
        frame = read_route1_rows(
            input_csv,
            chunksize=chunksize,
            max_rows=None,
            target_sources=(source,),
            context_ks=context_ks,
            roles=("child",),
        )
        summary, predictions, coefficients, bin_defs = fit_source_atlas(
            frame,
            source=source,
            context_ks=context_ks,
            effort_cols=effort_cols,
            model_ids=model_ids,
            n_points=n_points,
        )
        figure_manifest = plot_fixed_predictions(predictions, fig_dir=fig_dir)
        slopes = fixed_slice_slopes(predictions)
        summary.to_csv(output_dir / "model_summary.csv", index=False)
        coefficients.to_csv(output_dir / "coefficient_long.csv", index=False)
        predictions.to_csv(output_dir / "fixed_effort_predictions.csv.gz", index=False)
        bin_defs.to_csv(output_dir / "fixed_effort_bin_definitions.csv", index=False)
        slopes.to_csv(output_dir / "fixed_slice_slopes.csv", index=False)
        figure_manifest.to_csv(output_dir / "figure_manifest.csv", index=False)
        audit = pd.DataFrame(
            [
                {
                    "target_source": source,
                    "model_rows": len(summary),
                    "fit_rows": int(summary["status"].eq("fit").sum()) if not summary.empty else 0,
                    "coefficient_rows": len(coefficients),
                    "prediction_rows": len(predictions),
                    "figure_rows": len(figure_manifest),
                }
            ]
        )
        audit.to_csv(output_dir / "audit.csv", index=False)
    if stage in {"all", "report"}:
        required = {
            "summary": output_dir / "model_summary.csv",
            "bin_defs": output_dir / "fixed_effort_bin_definitions.csv",
            "slopes": output_dir / "fixed_slice_slopes.csv",
            "figure_manifest": output_dir / "figure_manifest.csv",
        }
        missing = [str(path) for path in required.values() if not path.exists()]
        if missing:
            raise FileNotFoundError(f"missing saved artifacts for report-only stage: {missing}")
        summary = pd.read_csv(required["summary"])
        bin_defs = pd.read_csv(required["bin_defs"])
        slopes = pd.read_csv(required["slopes"])
        figure_manifest = pd.read_csv(required["figure_manifest"])
    md_path = doc_dir / f"utterance_information_route1_{source_slug}_corrected_fixed_effort_atlas_v2.md"
    html_path = doc_dir / f"utterance_information_route1_{source_slug}_corrected_fixed_effort_atlas_v2.html"
    pdf_path = doc_dir / f"utterance_information_route1_{source_slug}_corrected_fixed_effort_atlas_v2.pdf"
    if stage in {"all", "report"}:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(
            build_markdown(
                source=source,
                summary=summary,
                bin_defs=bin_defs,
                figure_manifest=figure_manifest,
                slopes=slopes,
                output_dir=output_dir,
                fig_dir=fig_dir,
                report_dir=doc_dir,
            ),
            encoding="utf-8",
        )
        render_markdown_file(md_path, html_path)
        if render_pdf_file:
            render_pdf(html_path, pdf_path)
        print(f"[OK] {source}: {md_path}", flush=True)
    return {
        "summary": output_dir / "model_summary.csv",
        "predictions": output_dir / "fixed_effort_predictions.csv.gz",
        "coefficients": output_dir / "coefficient_long.csv",
        "figures": output_dir / "figure_manifest.csv",
        "md": md_path,
        "html": html_path,
        "pdf": pdf_path,
    }


def write_index(outputs: Sequence[dict[str, Path]], *, doc_dir: Path, render_pdf_file: bool) -> dict[str, Path]:
    """Write an index report linking all source-specific atlases."""

    md_path = doc_dir / "utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.md"
    html_path = md_path.with_suffix(".html")
    pdf_path = md_path.with_suffix(".pdf")
    rows = []
    for output in outputs:
        summary = pd.read_csv(output["summary"])
        source = str(summary["target_source"].iloc[0]) if "target_source" in summary and not summary.empty else output["md"].stem
        rows.append(
            {
                "target_source": source,
                "model_rows": len(summary),
                "fit_rows": int(summary["status"].eq("fit").sum()),
                "md": str(output["md"]),
                "html": str(output["html"]),
                "pdf": str(output["pdf"]),
                "figures": str(output["figures"]),
            }
        )
    table = pd.DataFrame(rows)
    lines = [
        "# Route 1 Source-Specific Corrected Fixed-Effort Atlas v2 Index",
        "",
        "This index links the old-style, plot-heavy fixed-effort atlases rebuilt independently for each target source with the corrected M1-M15 model ladder.",
        "",
        markdown_table(table, max_rows=40),
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    render_markdown_file(md_path, html_path)
    if render_pdf_file:
        render_pdf(html_path, pdf_path)
    return {"md": md_path, "html": html_path, "pdf": pdf_path}


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["all", "analysis", "report"], default="all")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--sources", default=",".join(DEFAULT_TARGET_SOURCES))
    parser.add_argument("--context-ks", default=",".join(DEFAULT_CONTEXT_KS))
    parser.add_argument("--effort-cols", default="all")
    parser.add_argument("--model-ids", default=",".join(REPORT_MODEL_IDS))
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--n-points", type=int, default=60)
    parser.add_argument("--no-pdf", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    sources = split_csv(args.sources)
    context_ks = split_csv(args.context_ks)
    effort_cols = split_csv(args.effort_cols)
    model_ids = split_csv(args.model_ids)
    outputs = []
    for source in sources:
        outputs.append(
            run_source(
                input_csv=args.input,
                source=source,
                output_root=args.output_dir,
                fig_root=args.fig_dir,
                doc_dir=args.doc_dir,
                context_ks=context_ks,
                effort_cols=effort_cols,
                model_ids=model_ids,
                chunksize=args.chunksize,
                n_points=args.n_points,
                render_pdf_file=not args.no_pdf,
                stage=args.stage,
            )
        )
    if args.stage in {"all", "report"}:
        index = write_index(outputs, doc_dir=args.doc_dir, render_pdf_file=not args.no_pdf)
        print(f"[OK] index: {index['md']}", flush=True)


if __name__ == "__main__":
    main()
