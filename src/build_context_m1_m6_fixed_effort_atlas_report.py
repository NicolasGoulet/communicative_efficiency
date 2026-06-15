#!/usr/bin/env python3
"""Build a full M1-M6 context fixed-effort atlas.

This is the long internal review report requested after the smaller context
permutation reports. It combines:

- the M1-M6 model ladder;
- k0/k1/k2/k3 scoring-context versions;
- context entropy, matched context size, and entropy+size variants for M4-M6;
- exact fixed-effort slice panels.

For words and morphemes, fixed-effort panels are exact values 1-4, 5-8, and
9-12. For syllables and phonemes, the panels use the 12 most frequent observed
exact values split into three ordered groups of four.
"""

from __future__ import annotations

import argparse
import gc
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from sklearn.metrics import mean_absolute_error, mean_squared_error

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_context_fixed_effort_atlas_report import fixed_effort_bins, read_measured_context_rows
    from build_context_predictor_permutation_reports import fitted_r2, format_p, markdown_table, param_value, safe_float
    from build_m1_m2_utterance_information_deep_dive import EFFORT_MEASURES
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_context_fixed_effort_atlas_report import fixed_effort_bins, read_measured_context_rows
    from src.build_context_predictor_permutation_reports import fitted_r2, format_p, markdown_table, param_value, safe_float
    from src.build_m1_m2_utterance_information_deep_dive import EFFORT_MEASURES
    from src.render_markdown_report import render_markdown_file


DEFAULT_CONTEXT_OUTPUT_DIR = Path("results/context_predictor_permutations")
DEFAULT_OUTPUT_DIR = Path("results/context_m1_m6_fixed_effort_atlas")
DEFAULT_FIG_DIR = Path("figs/context_m1_m6_fixed_effort_atlas")
DEFAULT_DOC_MD = Path("docs/utterance_information_context_m1_m6_fixed_effort_atlas.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_context_m1_m6_fixed_effort_atlas.html")
DEFAULT_CONTEXT_KS = ("k0", "k1", "k2", "k3")

CONTEXT_SIZE_FOR_EFFORT = {
    "nb_words": ("context_nb_words", "Context words"),
    "nb_morphemes": ("context_nb_morphemes", "Context morphemes"),
    "nb_syllables_cmu_or_pkg": ("context_nb_syllables_cmu_or_pkg", "Context syllables: CMU/pkg"),
    "nb_syllables_pkg": ("context_nb_syllables_pkg", "Context syllables: pkg"),
    "nb_phonemes": ("context_nb_phonemes", "Context phonemes"),
}


@dataclass(frozen=True)
class M1M6ContextSpec:
    """One M1-M6 context-aware model variant."""

    model_id: str
    model_family: str
    model_label: str
    context_variant: str
    formula: str
    uses_entropy: bool
    uses_context_size: bool
    question: str


MODEL_SPECS = [
    M1M6ContextSpec(
        model_id="M1",
        model_family="M1",
        model_label="Pooled age and effort",
        context_variant="none",
        formula="sum_bits ~ age_c + target_effort_c",
        uses_entropy=False,
        uses_context_size=False,
        question="Pooling all children, does age predict total bits after controlling target utterance effort?",
    ),
    M1M6ContextSpec(
        model_id="M2",
        model_family="M2",
        model_label="Age and effort with child identity",
        context_variant="none",
        formula="sum_bits ~ age_c + target_effort_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=False,
        question="Does the developmental age effect remain after child identity is controlled?",
    ),
    M1M6ContextSpec(
        model_id="M3",
        model_family="M3",
        model_label="Age by effort",
        context_variant="none",
        formula="sum_bits ~ age_c * target_effort_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=False,
        question="Does the age trend change across target-effort values?",
    ),
    M1M6ContextSpec(
        model_id="M4E",
        model_family="M4",
        model_label="Context entropy added",
        context_variant="entropy",
        formula="sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=False,
        question="Does entropy add predictive information beyond age, target effort, and child identity?",
    ),
    M1M6ContextSpec(
        model_id="M4S",
        model_family="M4",
        model_label="Matched context size added",
        context_variant="context_size",
        formula="sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=True,
        question="Does matched context-window size add predictive information beyond age, target effort, and child identity?",
    ),
    M1M6ContextSpec(
        model_id="M4ES",
        model_family="M4",
        model_label="Entropy plus matched context size",
        context_variant="entropy_plus_size",
        formula="sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=True,
        question="Do entropy and matched context size explain distinct variance when entered together?",
    ),
    M1M6ContextSpec(
        model_id="M5E",
        model_family="M5",
        model_label="Age by context entropy",
        context_variant="entropy",
        formula="sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=False,
        question="Does the entropy association change over developmental time?",
    ),
    M1M6ContextSpec(
        model_id="M5S",
        model_family="M5",
        model_label="Age by matched context size",
        context_variant="context_size",
        formula="sum_bits ~ age_c * context_size_c + target_effort_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=True,
        question="Does the matched context-size association change over developmental time?",
    ),
    M1M6ContextSpec(
        model_id="M5ES",
        model_family="M5",
        model_label="Age by entropy and size",
        context_variant="entropy_plus_size",
        formula="sum_bits ~ age_c * context_entropy_c + age_c * context_size_c + target_effort_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=True,
        question="Do entropy and context-size age interactions both contribute?",
    ),
    M1M6ContextSpec(
        model_id="M6E",
        model_family="M6",
        model_label="Effort and entropy interactions",
        context_variant="entropy",
        formula="sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=False,
        question="Do age, target effort, and entropy interact when predicting total bits?",
    ),
    M1M6ContextSpec(
        model_id="M6S",
        model_family="M6",
        model_label="Effort and context-size interactions",
        context_variant="context_size",
        formula="sum_bits ~ age_c * target_effort_c + age_c * context_size_c + target_effort_c * context_size_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=True,
        question="Do age, target effort, and matched context size interact when predicting total bits?",
    ),
    M1M6ContextSpec(
        model_id="M6ES",
        model_family="M6",
        model_label="Interaction-rich entropy and size model",
        context_variant="entropy_plus_size",
        formula=(
            "sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + "
            "target_effort_c * context_entropy_c + age_c * context_size_c + "
            "target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id)"
        ),
        uses_entropy=True,
        uses_context_size=True,
        question="Do the interaction patterns survive when both context entropy and context size are present?",
    ),
]

MODEL_ORDER = [spec.model_id for spec in MODEL_SPECS]


def slugify(value: str) -> str:
    """Return a stable filename slug."""

    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def prepare_model_frame(
    frame: pd.DataFrame,
    *,
    effort_col: str,
    context_size_col: str,
    spec: M1M6ContextSpec,
) -> tuple[pd.DataFrame, str]:
    """Prepare centered rows for one fit."""

    out = frame.copy()
    out["target_effort_value"] = pd.to_numeric(out[effort_col], errors="coerce")
    required = ["sum_bits", "age_months", "target_effort_value", "child_id"]
    if spec.uses_entropy:
        out["context_entropy_bits"] = pd.to_numeric(out["context_entropy_bits"], errors="coerce")
        required.append("context_entropy_bits")
    if spec.uses_context_size:
        out["context_size_value"] = pd.to_numeric(out[context_size_col], errors="coerce")
        required.append("context_size_value")
    else:
        out["context_size_value"] = 0.0
    out = out.dropna(subset=required).copy()
    out = out[(out["sum_bits"] > 0) & (out["age_months"] > 0) & (out["target_effort_value"] > 0)].copy()
    if spec.uses_entropy:
        out = out[out["context_entropy_bits"] > 0].copy()
    if spec.uses_context_size:
        out = out[out["context_size_value"] > 0].copy()
    if out.empty:
        return out, "no complete rows"
    if out["child_id"].nunique() < 2:
        return out, "fewer than two children"
    for col, label in [
        ("age_months", "age"),
        ("target_effort_value", "target effort"),
        ("context_entropy_bits", "context entropy"),
        ("context_size_value", "context size"),
    ]:
        if col in out and (col in required or col == "context_size_value") and out[col].std(ddof=0) <= 0:
            if col == "context_size_value" and not spec.uses_context_size:
                continue
            if col == "context_entropy_bits" and not spec.uses_entropy:
                continue
            return out, f"{label} has no variation"
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["target_effort_c"] = out["target_effort_value"] - out["target_effort_value"].mean()
    out["context_entropy_c"] = (
        out["context_entropy_bits"] - out["context_entropy_bits"].mean() if spec.uses_entropy else 0.0
    )
    out["context_size_c"] = out["context_size_value"] - out["context_size_value"].mean() if spec.uses_context_size else 0.0
    out["child_id"] = out["child_id"].astype(str)
    return out.reset_index(drop=True), ""


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


def average_child_predictions(result: object, base: pd.DataFrame, child_ids: Sequence[str], *, has_child_id: bool) -> pd.DataFrame:
    """Predict and average over child fixed intercepts when the model has them."""

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
    spec: M1M6ContextSpec,
    effort_col: str,
    n_points: int,
) -> pd.DataFrame:
    """Generate fixed-effort age predictions for one fit."""

    ages = np.linspace(model_frame["age_months"].quantile(0.02), model_frame["age_months"].quantile(0.98), n_points)
    child_ids = sorted(model_frame["child_id"].astype(str).unique())
    parts: list[pd.DataFrame] = []
    for item in bin_defs[bin_defs["effort_col"].eq(effort_col)].to_dict("records"):
        values = [int(value.strip()) for value in str(item["fixed_values"]).split(",") if value.strip()]
        for fixed_value in values:
            base = pd.DataFrame(
                {
                    "age_months": ages,
                    "age_c": ages - model_frame["age_months"].mean(),
                    "target_effort_value": fixed_value,
                    "target_effort_c": fixed_value - model_frame["target_effort_value"].mean(),
                    "context_entropy_bits": model_frame["context_entropy_bits"].mean()
                    if spec.uses_entropy
                    else 0.0,
                    "context_entropy_c": 0.0,
                    "context_size_value": model_frame["context_size_value"].mean()
                    if spec.uses_context_size
                    else 0.0,
                    "context_size_c": 0.0,
                    "fixed_effort_value": int(fixed_value),
                    "atlas_bin": str(item["atlas_bin"]),
                    "model_id": spec.model_id,
                    "effort_col": effort_col,
                }
            )
            parts.append(
                average_child_predictions(
                    result,
                    base,
                    child_ids,
                    has_child_id="C(child_id)" in spec.formula,
                )
            )
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fit_context_m1_m6_atlas(
    frame: pd.DataFrame,
    *,
    context_k: str,
    n_points: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit all M1-M6 context variants for one k and produce predictions."""

    bin_defs = fixed_effort_bins(frame)
    summary_rows: list[dict[str, object]] = []
    prediction_parts: list[pd.DataFrame] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        context_size_col, context_size_label = CONTEXT_SIZE_FOR_EFFORT[effort_col]
        for spec in MODEL_SPECS:
            base_row = {
                "context_k": context_k,
                "model_id": spec.model_id,
                "model_family": spec.model_family,
                "model_label": spec.model_label,
                "context_variant": spec.context_variant,
                "question": spec.question,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "context_size_col": context_size_col if spec.uses_context_size else "",
                "context_size_label": context_size_label if spec.uses_context_size else "",
                "formula": spec.formula,
                "estimator": "linear OLS",
                "library": "statsmodels.formula.api.ols",
                "covariance": "child-cluster robust SE via cov_type='cluster'",
            }
            if context_k == "k0" and (spec.uses_entropy or spec.uses_context_size):
                summary_rows.append({**base_row, "status": "skipped", "error": "k0 has no context predictors"})
                continue
            model_frame, error = prepare_model_frame(
                frame,
                effort_col=effort_col,
                context_size_col=context_size_col,
                spec=spec,
            )
            if error:
                summary_rows.append(
                    {
                        **base_row,
                        "status": "skipped",
                        "error": error,
                        "n_obs": len(model_frame),
                        "n_children": int(model_frame["child_id"].nunique()) if not model_frame.empty else 0,
                    }
                )
                continue
            try:
                result = smf.ols(spec.formula, data=model_frame).fit(
                    cov_type="cluster",
                    cov_kwds={"groups": model_frame["child_id"]},
                )
                observed = np.asarray(result.model.endog, dtype=float)
                fitted = np.asarray(result.fittedvalues, dtype=float)
                summary_rows.append(
                    {
                        **base_row,
                        "status": "fit",
                        "error": "",
                        "n_obs": len(model_frame),
                        "n_children": int(model_frame["child_id"].nunique()),
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
                        "age_effort_coef": param_value(result, "age_c:target_effort_c"),
                        "age_effort_p": param_value(result, "age_c:target_effort_c", "pvalues"),
                        "age_entropy_coef": param_value(result, "age_c:context_entropy_c"),
                        "age_entropy_p": param_value(result, "age_c:context_entropy_c", "pvalues"),
                        "effort_entropy_coef": param_value(result, "target_effort_c:context_entropy_c"),
                        "effort_entropy_p": param_value(result, "target_effort_c:context_entropy_c", "pvalues"),
                        "age_context_size_coef": param_value(result, "age_c:context_size_c"),
                        "age_context_size_p": param_value(result, "age_c:context_size_c", "pvalues"),
                        "effort_context_size_coef": param_value(result, "target_effort_c:context_size_c"),
                        "effort_context_size_p": param_value(result, "target_effort_c:context_size_c", "pvalues"),
                        "entropy_context_size_coef": param_value(result, "context_entropy_c:context_size_c"),
                        "entropy_context_size_p": param_value(result, "context_entropy_c:context_size_c", "pvalues"),
                    }
                )
                pred = fixed_prediction_grid(
                    result=result,
                    model_frame=model_frame,
                    bin_defs=bin_defs,
                    spec=spec,
                    effort_col=effort_col,
                    n_points=n_points,
                )
                if not pred.empty:
                    pred["context_k"] = context_k
                    pred["model_family"] = spec.model_family
                    pred["model_label"] = spec.model_label
                    pred["context_variant"] = spec.context_variant
                    pred["effort_label"] = effort_label
                    prediction_parts.append(pred)
                result.remove_data()
            except Exception as exc:  # pragma: no cover
                summary_rows.append(
                    {
                        **base_row,
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                        "n_obs": len(model_frame),
                        "n_children": int(model_frame["child_id"].nunique()) if not model_frame.empty else 0,
                    }
                )
            del model_frame
            gc.collect()
    summary = pd.DataFrame(summary_rows)
    predictions = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    bin_defs["context_k"] = context_k
    return summary, predictions, bin_defs


def plot_fixed_predictions(predictions: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    """Plot fixed-effort atlas figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    group_cols = ["context_k", "model_id", "model_family", "model_label", "context_variant", "effort_col", "effort_label"]
    for keys, group in predictions.groupby(group_cols, sort=True):
        context_k, model_id, model_family, model_label, context_variant, effort_col, effort_label = keys
        bins = list(group["atlas_bin"].drop_duplicates())
        fig, axes = plt.subplots(1, len(bins), figsize=(5.8 * len(bins), 4.9), sharey=True)
        if len(bins) == 1:
            axes = [axes]
        for ax, atlas_bin in zip(axes, bins):
            panel = group[group["atlas_bin"].eq(atlas_bin)].copy()
            values = sorted(int(value) for value in panel["fixed_effort_value"].unique())
            palette = sns.color_palette("viridis", n_colors=len(values))
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
        fig.suptitle(f"{context_k.upper()} {model_id}: {model_label} | {effort_label}", y=1.05)
        fig.tight_layout()
        filename = f"{context_k}_{model_id.lower()}_{slugify(effort_col)}_fixed_effort_atlas.png"
        out = fig_dir / filename
        fig.savefig(out, dpi=210, bbox_inches="tight")
        fig.savefig(fig_dir / filename.replace(".png", ".pdf"), bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "context_k": context_k,
                "model_id": model_id,
                "model_family": model_family,
                "model_label": model_label,
                "context_variant": context_variant,
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
    keys = ["context_k", "model_id", "model_family", "model_label", "context_variant", "effort_col", "effort_label", "atlas_bin", "fixed_effort_value"]
    for key, group in predictions.groupby(keys, sort=True):
        context_k, model_id, model_family, model_label, context_variant, effort_col, effort_label, atlas_bin, fixed_value = key
        ages = group["age_months"].to_numpy(dtype=float)
        bits = group["predicted_sum_bits"].to_numpy(dtype=float)
        slope = float(np.polyfit(ages, bits, 1)[0]) if len(np.unique(ages)) >= 2 else math.nan
        rows.append(
            {
                "context_k": context_k,
                "model_id": model_id,
                "model_family": model_family,
                "model_label": model_label,
                "context_variant": context_variant,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "atlas_bin": atlas_bin,
                "fixed_effort_value": int(fixed_value),
                "slope_bits_per_month": slope,
                "slope_bits_per_6_months": slope * 6 if math.isfinite(slope) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def slope_summary(slopes: pd.DataFrame) -> pd.DataFrame:
    """Summarize plotted fixed-slice slopes."""

    if slopes.empty:
        return pd.DataFrame()
    return (
        slopes.groupby(["context_k", "model_id", "model_label", "effort_label", "atlas_bin"], observed=True)
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
    """Return compact fit overview by k and model."""

    fitted = summary[summary["status"].eq("fit")].copy()
    if fitted.empty:
        return pd.DataFrame()
    return (
        fitted.groupby(["context_k", "model_id", "model_family", "model_label", "context_variant"], observed=True)
        .agg(
            fitted_rows=("status", "size"),
            mean_r2=("r2_observed_fitted", "mean"),
            negative_age_coef_rows=("age_coef", lambda values: int((pd.to_numeric(values, errors="coerce") < 0).sum())),
            significant_age_rows=("age_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_entropy_rows=("context_entropy_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_context_size_rows=("context_size_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
        )
        .reset_index()
    )


def coefficient_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Return readable coefficient table."""

    cols = [
        "context_k",
        "model_id",
        "model_label",
        "context_variant",
        "effort_label",
        "context_size_label",
        "n_obs",
        "n_children",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "target_effort_coef",
        "target_effort_p",
        "context_entropy_coef",
        "context_entropy_p",
        "context_size_coef",
        "context_size_p",
        "age_effort_coef",
        "age_effort_p",
        "age_entropy_coef",
        "age_entropy_p",
        "effort_entropy_coef",
        "effort_entropy_p",
        "age_context_size_coef",
        "age_context_size_p",
        "effort_context_size_coef",
        "effort_context_size_p",
        "entropy_context_size_coef",
        "entropy_context_size_p",
    ]
    out = summary[summary["status"].eq("fit")][[col for col in cols if col in summary.columns]].copy()
    for col in [column for column in out.columns if column.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def model_formula_table() -> pd.DataFrame:
    """Return one row per model formula."""

    return pd.DataFrame(
        [
            {
                "model_id": spec.model_id,
                "model_family": spec.model_family,
                "model_label": spec.model_label,
                "context_variant": spec.context_variant,
                "question": spec.question,
                "formula": spec.formula,
            }
            for spec in MODEL_SPECS
        ]
    )


def build_markdown(
    *,
    summary: pd.DataFrame,
    bin_defs: pd.DataFrame,
    figure_manifest: pd.DataFrame,
    slopes: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> str:
    """Build Markdown report."""

    skipped = summary[summary["status"].ne("fit")].copy()
    overview = fit_overview(summary)
    coefs = coefficient_table(summary)
    slope_table = slope_summary(slopes)
    bin_table = bin_defs[["context_k", "effort_label", "atlas_bin", "fixed_values", "support_rows", "support_children", "rule"]].copy()

    lines: list[str] = [
        "# M1-M6 Context Fixed-Effort Atlas",
        "",
        "This is the long internal report that repeats the full M1-M6 model ladder across k0/k1/k2/k3 and fixed-effort slices.",
        "It is intentionally exhaustive so pieces can later be selected for the supervisor-facing report.",
        "",
        "## Implementation",
        "",
        "- Estimator: linear ordinary least squares regression.",
        "- Library: `statsmodels.formula.api.ols`.",
        "- Uncertainty: child-cluster robust standard errors with `cov_type='cluster'` and `child_id` as the cluster.",
        "- Outcome: `sum_bits`, the Mistral total information for the target utterance under the current scoring context.",
        "- Fixed slices: the model is fit on all eligible rows; fixed effort values only define the plotted prediction lines.",
        "- Context size: when included, it is matched to the target effort unit, so target words use context words, target phonemes use context phonemes, etc.",
        "",
        "## Model Formulas",
        "",
        "How to read: `target_effort_c`, `context_entropy_c`, and `context_size_c` are centered numeric predictors. `C(child_id)` controls child identity. Models with context predictors are not fit for `k0` because `k0` has no context.",
        "",
        markdown_table(model_formula_table(), max_rows=40, digits=4),
        "",
        "## Fixed-Effort Slice Definitions",
        "",
        "Words and morphemes use exact 1-4, 5-8, and 9-12 panels. Syllables and phonemes use the 12 most frequent exact values split into three ordered representative panels.",
        "",
        markdown_table(bin_table, max_rows=120, digits=4),
        "",
        "## Fit Overview",
        "",
        "How to read: `mean_r2` is in-sample fit across the effort-unit rows for that model. `negative_age_coef_rows` and `significant_age_rows` summarize the direction and p<.05 evidence for age within each model/context.",
        "",
        markdown_table(overview, max_rows=160, digits=4),
        "",
        "## Coefficient Table",
        "",
        "How to read: coefficients are in Mistral bits. `age_coef` is bits/month after the listed controls. Interaction columns say how one slope changes as the interacting predictor increases. P-values are child-cluster robust.",
        "",
        markdown_table(coefs, max_rows=260, digits=4),
        "",
        "## Fixed-Slice Slope Summary",
        "",
        "How to read: these are descriptive slopes computed from plotted prediction lines, not separate inferential models. Inference comes from the coefficient table.",
        "",
        markdown_table(slope_table, max_rows=260, digits=4),
        "",
        "## Figures",
        "",
        "How to read every figure: each colored line is an exact fixed effort value. The shaded band is the model-confidence band for the fitted mean. Context predictors in prediction slices are held at their fitted-data means, so the line isolates age at fixed target effort under average context conditions.",
        "",
    ]
    for context_k in DEFAULT_CONTEXT_KS:
        context_figs = figure_manifest[figure_manifest["context_k"].eq(context_k)].copy()
        if context_figs.empty:
            continue
        lines.extend([f"### {context_k.upper()}", ""])
        for model_family in ["M1", "M2", "M3", "M4", "M5", "M6"]:
            family_figs = context_figs[context_figs["model_family"].eq(model_family)].copy()
            if family_figs.empty:
                continue
            lines.extend([f"#### {model_family}", ""])
            for model_id, model_figs in family_figs.groupby("model_id", sort=False):
                model_label = str(model_figs["model_label"].iloc[0])
                variant = str(model_figs["context_variant"].iloc[0])
                formula = next(spec.formula for spec in MODEL_SPECS if spec.model_id == model_id)
                lines.extend([f"##### {model_id}: {model_label}", "", f"Formula: `{formula}`", "", f"Context variant: `{variant}`", ""])
                for row in model_figs.sort_values("effort_label").to_dict("records"):
                    lines.append(f"**{row['effort_label']}**")
                    lines.append("")
                    lines.append(f"![{row['context_k']} {row['model_id']} {row['effort_label']}](../{row['figure']})")
                    lines.append("")
    if not skipped.empty:
        lines.extend(
            [
                "## Skipped Rows",
                "",
                "Expected skipped rows are mostly k0 context variants: k0 has no context entropy or context size.",
                "",
                markdown_table(skipped[["context_k", "model_id", "model_label", "effort_label", "status", "error"]], max_rows=120, digits=4),
                "",
            ]
        )
    lines.extend(
        [
            "## Saved Outputs",
            "",
            "```text",
            str(output_dir / "context_m1_m6_model_summary.csv"),
            str(output_dir / "context_m1_m6_bin_definitions.csv"),
            str(output_dir / "context_m1_m6_predictions.csv.gz"),
            str(output_dir / "context_m1_m6_slice_slopes.csv"),
            str(output_dir / "context_m1_m6_figure_manifest.csv"),
            f"{fig_dir}/",
            "```",
        ]
    )
    return "\n".join(lines)


def run_analysis(
    *,
    context_output_dir: Path,
    output_dir: Path,
    fig_dir: Path,
    context_ks: Sequence[str],
    n_points: int,
) -> dict[str, Path]:
    """Run all M1-M6 context fixed-effort fits and plots."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_parts: list[pd.DataFrame] = []
    prediction_parts: list[pd.DataFrame] = []
    bin_parts: list[pd.DataFrame] = []
    for context_k in context_ks:
        print(f"[stage] M1-M6 context fixed-effort analysis {context_k}", flush=True)
        frame = read_measured_context_rows(context_output_dir, context_k)
        summary, predictions, bin_defs = fit_context_m1_m6_atlas(frame, context_k=context_k, n_points=n_points)
        summary_parts.append(summary)
        prediction_parts.append(predictions)
        bin_parts.append(bin_defs)
        del frame, summary, predictions, bin_defs
        gc.collect()
    summary_all = pd.concat(summary_parts, ignore_index=True) if summary_parts else pd.DataFrame()
    predictions_all = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    bin_defs_all = pd.concat(bin_parts, ignore_index=True) if bin_parts else pd.DataFrame()
    figure_manifest = plot_fixed_predictions(predictions_all, fig_dir=fig_dir)
    slopes = fixed_slice_slopes(predictions_all)
    summary_all.to_csv(output_dir / "context_m1_m6_model_summary.csv", index=False)
    bin_defs_all.to_csv(output_dir / "context_m1_m6_bin_definitions.csv", index=False)
    predictions_all.to_csv(output_dir / "context_m1_m6_predictions.csv.gz", index=False)
    slopes.to_csv(output_dir / "context_m1_m6_slice_slopes.csv", index=False)
    figure_manifest.to_csv(output_dir / "context_m1_m6_figure_manifest.csv", index=False)
    audit = pd.DataFrame(
        [
            {
                "context_ks": ",".join(context_ks),
                "model_rows": len(summary_all),
                "fitted_model_rows": int(summary_all["status"].eq("fit").sum()) if not summary_all.empty else 0,
                "prediction_rows": len(predictions_all),
                "figure_rows": len(figure_manifest),
            }
        ]
    )
    audit.to_csv(output_dir / "context_m1_m6_audit.csv", index=False)
    return {
        "summary": output_dir / "context_m1_m6_model_summary.csv",
        "bin_defs": output_dir / "context_m1_m6_bin_definitions.csv",
        "predictions": output_dir / "context_m1_m6_predictions.csv.gz",
        "slopes": output_dir / "context_m1_m6_slice_slopes.csv",
        "figure_manifest": output_dir / "context_m1_m6_figure_manifest.csv",
        "audit": output_dir / "context_m1_m6_audit.csv",
    }


def run_report(*, output_dir: Path, fig_dir: Path, md_path: Path, html_path: Path) -> dict[str, Path]:
    """Render report from saved outputs."""

    summary = pd.read_csv(output_dir / "context_m1_m6_model_summary.csv")
    bin_defs = pd.read_csv(output_dir / "context_m1_m6_bin_definitions.csv")
    figure_manifest = pd.read_csv(output_dir / "context_m1_m6_figure_manifest.csv")
    slopes = pd.read_csv(output_dir / "context_m1_m6_slice_slopes.csv")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        build_markdown(
            summary=summary,
            bin_defs=bin_defs,
            figure_manifest=figure_manifest,
            slopes=slopes,
            output_dir=output_dir,
            fig_dir=fig_dir,
        ),
        encoding="utf-8",
    )
    render_markdown_file(md_path, html_path)
    return {"md": md_path, "html": html_path}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-output-dir", type=Path, default=DEFAULT_CONTEXT_OUTPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--context-ks", nargs="+", default=list(DEFAULT_CONTEXT_KS))
    parser.add_argument("--n-points", type=int, default=60)
    parser.add_argument("--stage", choices=["all", "analysis", "report"], default="all")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.stage in {"all", "analysis"}:
        outputs = run_analysis(
            context_output_dir=args.context_output_dir,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_ks=args.context_ks,
            n_points=args.n_points,
        )
        print(f"[OK] wrote M1-M6 context audit: {outputs['audit']}")
        print(f"[OK] wrote M1-M6 context summary: {outputs['summary']}")
    if args.stage in {"all", "report"}:
        outputs = run_report(output_dir=args.output_dir, fig_dir=args.fig_dir, md_path=args.md, html_path=args.html)
        print(f"[OK] wrote M1-M6 context fixed-effort report: {outputs['html']}")


if __name__ == "__main__":
    main()
