#!/usr/bin/env python3
"""Build fixed-effort context-predictor atlas plots.

This report complements `build_context_predictor_permutation_reports.py`.
The previous context report gives coefficient/R2 summaries for the context
predictor permutations. This script adds the fixed-effort slice views the main
M1-M6 atlas uses:

- words and morphemes: exact fixed values 1-4, 5-8, 9-12;
- syllables and phonemes: the 12 most frequent exact values, split into three
  ordered groups of four.

The fitted models are still fit on all eligible rows. The fixed effort values
only define the prediction slices.
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
    from build_context_predictor_permutation_reports import fitted_r2, format_p, markdown_table, param_value, safe_float
    from build_m1_m2_utterance_information_deep_dive import EFFORT_MEASURES
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - imported as src.*
    from src.build_context_predictor_permutation_reports import fitted_r2, format_p, markdown_table, param_value, safe_float
    from src.build_m1_m2_utterance_information_deep_dive import EFFORT_MEASURES
    from src.render_markdown_report import render_markdown_file


DEFAULT_CONTEXT_OUTPUT_DIR = Path("results/context_predictor_permutations")
DEFAULT_OUTPUT_DIR = Path("results/context_fixed_effort_atlas")
DEFAULT_FIG_DIR = Path("figs/context_fixed_effort_atlas")
DEFAULT_DOC_MD = Path("docs/utterance_information_context_fixed_effort_atlas.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_context_fixed_effort_atlas.html")
DEFAULT_CONTEXT_KS = ("k0", "k1", "k2", "k3")

CONTEXT_SIZE_FOR_EFFORT = {
    "nb_words": ("context_nb_words", "Context words"),
    "nb_morphemes": ("context_nb_morphemes", "Context morphemes"),
    "nb_syllables_cmu_or_pkg": ("context_nb_syllables_cmu_or_pkg", "Context syllables: CMU/pkg"),
    "nb_syllables_pkg": ("context_nb_syllables_pkg", "Context syllables: pkg"),
    "nb_phonemes": ("context_nb_phonemes", "Context phonemes"),
}


@dataclass(frozen=True)
class ContextAtlasSpec:
    """One context-predictor model family for fixed-effort plotting."""

    model_id: str
    model_label: str
    formula: str
    uses_entropy: bool
    uses_context_size: bool
    question: str


MODEL_SPECS = [
    ContextAtlasSpec(
        model_id="CF0",
        model_label="Baseline controls",
        formula="sum_bits ~ age_c + target_effort_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=False,
        question="What is the age trajectory at fixed target effort, before adding context predictors?",
    ),
    ContextAtlasSpec(
        model_id="CF1",
        model_label="Entropy only",
        formula="sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=False,
        question="Does the fixed-effort age trajectory remain after controlling context entropy?",
    ),
    ContextAtlasSpec(
        model_id="CF2",
        model_label="Matched context size only",
        formula="sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)",
        uses_entropy=False,
        uses_context_size=True,
        question="Does the fixed-effort age trajectory remain after controlling the matching context-size unit?",
    ),
    ContextAtlasSpec(
        model_id="CF3",
        model_label="Entropy plus matched context size",
        formula="sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)",
        uses_entropy=True,
        uses_context_size=True,
        question="Does the fixed-effort age trajectory remain after controlling both context entropy and matching context size?",
    ),
]


def slugify(value: str) -> str:
    """Return a stable filename slug."""

    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def read_measured_context_rows(context_output_dir: Path, context_k: str) -> pd.DataFrame:
    """Read the per-k measured rows produced by the context permutation script."""

    path = context_output_dir / f"route1_real_child_context_measures_{context_k}.csv.gz"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run build_context_predictor_permutation_reports.py --stage analysis first."
        )
    frame = pd.read_csv(path, low_memory=False)
    frame["context_k"] = str(context_k)
    for col in [
        "age_months",
        "sum_bits",
        "context_entropy_bits",
        *[effort_col for effort_col, _ in EFFORT_MEASURES],
        *[col for col, _ in CONTEXT_SIZE_FOR_EFFORT.values()],
    ]:
        if col in frame:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["child_id"] = frame["child_id"].astype(str)
    return frame


def split_ordered_values(values: Sequence[int]) -> list[tuple[str, list[int]]]:
    """Split ordered values into three readable groups."""

    ordered = sorted({int(value) for value in values})
    chunks = np.array_split(np.array(ordered), 3)
    labels = ["1-4 representative ranks", "5-8 representative ranks", "9-12 representative ranks"]
    return [(label, [int(value) for value in chunk.tolist()]) for label, chunk in zip(labels, chunks) if len(chunk)]


def fixed_effort_bins(frame: pd.DataFrame) -> pd.DataFrame:
    """Return fixed-effort bin definitions for every effort unit."""

    rows: list[dict[str, object]] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        if effort_col in {"nb_words", "nb_morphemes"}:
            bins = [
                ("1-4", [1, 2, 3, 4], "Exact requested fixed values 1-4."),
                ("5-8", [5, 6, 7, 8], "Exact requested fixed values 5-8."),
                ("9-12", [9, 10, 11, 12], "Exact requested fixed values 9-12."),
            ]
        else:
            counts = (
                pd.to_numeric(frame[effort_col], errors="coerce")
                .dropna()
                .astype(int)
                .value_counts()
                .head(12)
            )
            ordered_top = sorted(counts.index.astype(int).tolist())
            bins = [
                (label, values, "Ordered split of the 12 most frequent observed exact values.")
                for label, values in split_ordered_values(ordered_top)
            ]
        for bin_label, values, rule in bins:
            support = frame[pd.to_numeric(frame[effort_col], errors="coerce").isin(values)]
            rows.append(
                {
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "atlas_bin": bin_label,
                    "fixed_values": ", ".join(str(value) for value in values),
                    "n_fixed_values": len(values),
                    "support_rows": int(len(support)),
                    "support_children": int(support["child_id"].nunique()) if not support.empty else 0,
                    "rule": rule,
                }
            )
    return pd.DataFrame(rows)


def prepare_model_frame(
    frame: pd.DataFrame,
    *,
    effort_col: str,
    context_size_col: str,
    spec: ContextAtlasSpec,
) -> tuple[pd.DataFrame, str]:
    """Center columns and return rows eligible for one model."""

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
    if out["age_months"].std(ddof=0) <= 0:
        return out, "age has no variation"
    if out["target_effort_value"].std(ddof=0) <= 0:
        return out, "target effort has no variation"
    if spec.uses_entropy and out["context_entropy_bits"].std(ddof=0) <= 0:
        return out, "context entropy has no variation"
    if spec.uses_context_size and out["context_size_value"].std(ddof=0) <= 0:
        return out, "context size has no variation"
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["target_effort_c"] = out["target_effort_value"] - out["target_effort_value"].mean()
    out["context_entropy_c"] = (
        out["context_entropy_bits"] - out["context_entropy_bits"].mean() if spec.uses_entropy else 0.0
    )
    out["context_size_c"] = out["context_size_value"] - out["context_size_value"].mean() if spec.uses_context_size else 0.0
    return out, ""


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


def average_child_predictions(result: object, base: pd.DataFrame, child_ids: Sequence[str]) -> pd.DataFrame:
    """Predict a frame, averaging over child fixed intercepts."""

    parts: list[pd.DataFrame] = []
    for child_id in child_ids:
        child_frame = base.copy()
        child_frame["child_id"] = child_id
        pred = prediction_summary_frame(result, child_frame)
        pred = pd.concat([child_frame.reset_index(drop=True), pred.reset_index(drop=True)], axis=1)
        parts.append(pred)
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
    spec: ContextAtlasSpec,
    effort_col: str,
    n_points: int,
) -> pd.DataFrame:
    """Generate fixed-effort age predictions for one fitted model."""

    ages = np.linspace(model_frame["age_months"].quantile(0.02), model_frame["age_months"].quantile(0.98), n_points)
    child_ids = sorted(model_frame["child_id"].astype(str).unique())
    pieces: list[pd.DataFrame] = []
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
            pieces.append(average_child_predictions(result, base, child_ids))
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def fit_and_predict_context_atlas(
    frame: pd.DataFrame,
    *,
    context_k: str,
    n_points: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit all context atlas models for one k."""

    bin_defs = fixed_effort_bins(frame)
    summary_rows: list[dict[str, object]] = []
    prediction_parts: list[pd.DataFrame] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        context_size_col, context_size_label = CONTEXT_SIZE_FOR_EFFORT[effort_col]
        for spec in MODEL_SPECS:
            if context_k == "k0" and (spec.uses_entropy or spec.uses_context_size):
                summary_rows.append(
                    {
                        "context_k": context_k,
                        "model_id": spec.model_id,
                        "model_label": spec.model_label,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "context_size_col": context_size_col if spec.uses_context_size else "",
                        "context_size_label": context_size_label if spec.uses_context_size else "",
                        "formula": spec.formula,
                        "status": "skipped",
                        "error": "k0 has no context predictors",
                    }
                )
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
                        "context_k": context_k,
                        "model_id": spec.model_id,
                        "model_label": spec.model_label,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "context_size_col": context_size_col if spec.uses_context_size else "",
                        "context_size_label": context_size_label if spec.uses_context_size else "",
                        "formula": spec.formula,
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
                        "context_k": context_k,
                        "model_id": spec.model_id,
                        "model_label": spec.model_label,
                        "question": spec.question,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "context_size_col": context_size_col if spec.uses_context_size else "",
                        "context_size_label": context_size_label if spec.uses_context_size else "",
                        "formula": spec.formula,
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
                    pred["model_label"] = spec.model_label
                    pred["effort_label"] = effort_label
                    pred["context_size_label"] = context_size_label if spec.uses_context_size else ""
                    prediction_parts.append(pred)
                result.remove_data()
            except Exception as exc:  # pragma: no cover - real-data guard
                summary_rows.append(
                    {
                        "context_k": context_k,
                        "model_id": spec.model_id,
                        "model_label": spec.model_label,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "context_size_col": context_size_col if spec.uses_context_size else "",
                        "context_size_label": context_size_label if spec.uses_context_size else "",
                        "formula": spec.formula,
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


def plot_context_fixed_predictions(predictions: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    """Plot one fixed-effort figure per k/model/effort unit."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    for keys, group in predictions.groupby(["context_k", "model_id", "model_label", "effort_col", "effort_label"], sort=True):
        context_k, model_id, model_label, effort_col, effort_label = keys
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
                ax.plot(
                    line["age_months"],
                    line["predicted_sum_bits"],
                    color=color,
                    linewidth=2.0,
                    label=str(int(fixed_value)),
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
            ax.set_title(atlas_bin)
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
            ax.legend(title="Fixed value", fontsize=8, title_fontsize=9)
        axes[0].set_ylabel("Predicted total bits")
        fig.suptitle(f"{context_k.upper()} {model_id}: {model_label} | {effort_label}", y=1.05)
        fig.tight_layout()
        filename = f"{context_k}_{model_id.lower()}_{slugify(effort_col)}_fixed_effort_atlas.png"
        out = fig_dir / filename
        fig.savefig(out, dpi=220, bbox_inches="tight")
        fig.savefig(fig_dir / filename.replace(".png", ".pdf"), bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
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
    """Compute descriptive slopes from plotted fixed-slice lines."""

    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    keys = ["context_k", "model_id", "model_label", "effort_col", "effort_label", "atlas_bin", "fixed_effort_value"]
    for key, group in predictions.groupby(keys, sort=True):
        context_k, model_id, model_label, effort_col, effort_label, atlas_bin, fixed_value = key
        ages = group["age_months"].to_numpy(dtype=float)
        bits = group["predicted_sum_bits"].to_numpy(dtype=float)
        slope = float(np.polyfit(ages, bits, 1)[0]) if len(np.unique(ages)) >= 2 else math.nan
        rows.append(
            {
                "context_k": context_k,
                "model_id": model_id,
                "model_label": model_label,
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
    """Summarize fixed-slice slopes by k/model/effort."""

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


def build_markdown(
    *,
    summary: pd.DataFrame,
    bin_defs: pd.DataFrame,
    figure_manifest: pd.DataFrame,
    slopes: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> str:
    """Build the context fixed-effort atlas Markdown."""

    fitted = summary[summary["status"].eq("fit")].copy()
    skipped = summary[summary["status"].ne("fit")].copy()
    slope_table = slope_summary(slopes)
    age_overview = (
        fitted.groupby(["context_k", "model_id", "model_label"], observed=True)
        .agg(
            fitted_rows=("status", "size"),
            mean_r2=("r2_observed_fitted", "mean"),
            negative_age_coef_rows=("age_coef", lambda values: int((pd.to_numeric(values, errors="coerce") < 0).sum())),
            significant_age_rows=("age_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
        )
        .reset_index()
    )
    coefficient_cols = [
        "context_k",
        "model_id",
        "model_label",
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
    ]
    coefficient_table = fitted[coefficient_cols].copy()
    for col in [column for column in coefficient_table.columns if column.endswith("_p")]:
        coefficient_table[col] = coefficient_table[col].map(format_p)

    lines = [
        "# Context Predictors: Fixed-Effort Atlas",
        "",
        "This internal report adds the fixed-effort slice views that were missing from the context-predictor reports.",
        "The models are fit on all eligible utterances. The fixed effort values only define the plotted prediction slices.",
        "",
        "## Model Families",
        "",
        "| id | question | formula |",
        "| --- | --- | --- |",
    ]
    for spec in MODEL_SPECS:
        lines.append(f"| {spec.model_id} | {spec.question} | `{spec.formula}` |")
    lines.extend(
        [
            "",
            "Implementation for all fitted rows: linear OLS via `statsmodels.formula.api.ols`, with child-cluster robust standard errors (`cov_type='cluster'`, cluster unit `child_id`).",
            "Context-size models use the context-size unit that matches the target effort unit: target words use context words, target phonemes use context phonemes, and so on. The broader coefficient report still contains every cross-unit context-size permutation.",
            "",
            "## Fixed-Effort Slice Definitions",
            "",
            "For words and morphemes, the panels are exact fixed values 1-4, 5-8, and 9-12. For syllables and phonemes, the panels are the 12 most frequent exact values split into three ordered groups of four, matching the earlier fixed-effort atlas logic.",
            "",
            markdown_table(bin_defs[["context_k", "effort_label", "atlas_bin", "fixed_values", "support_rows", "support_children", "rule"]], max_rows=120, digits=4),
            "",
            "## Model Overview",
            "",
            "How to read: `negative_age_coef_rows` counts how many effort-unit rows have a negative fitted age coefficient. `significant_age_rows` counts how many have p<.05 for age. R2 is in-sample fitted-versus-observed fit.",
            "",
            markdown_table(age_overview, max_rows=80, digits=4),
            "",
            "## Coefficient Table",
            "",
            "How to read: coefficients are in Mistral bits. `age_coef` is bits per month after the listed controls. `target_effort_coef` is bits per added target effort unit. `context_entropy_coef` is bits per additional entropy bit. `context_size_coef` is bits per additional matched context-size unit.",
            "",
            markdown_table(coefficient_table, max_rows=120, digits=4),
            "",
            "## Fixed-Effort Slope Summary",
            "",
            "How to read: these slopes are descriptive summaries of the plotted prediction lines, not separate inferential models. Inference comes from the coefficient table above.",
            "",
            markdown_table(slope_table, max_rows=120, digits=4),
            "",
            "## Fixed-Effort Prediction Figures",
            "",
            "How to read every figure: each colored line is one exact fixed effort value. The shaded ribbon is the model confidence band for the fitted mean line. The context predictors are held at their model-frame mean for the prediction slice, so the plot isolates age at fixed target effort under average context conditions.",
            "",
        ]
    )
    for context_k in DEFAULT_CONTEXT_KS:
        sub = figure_manifest[figure_manifest["context_k"].eq(context_k)].copy()
        if sub.empty:
            continue
        lines.extend([f"### {context_k.upper()}", ""])
        for model_id, model_group in sub.groupby("model_id", sort=True):
            model_label = str(model_group["model_label"].iloc[0])
            lines.extend([f"#### {model_id}: {model_label}", ""])
            for row in model_group.sort_values("effort_label").to_dict("records"):
                lines.append(f"**{row['effort_label']}**")
                lines.append("")
                lines.append(f"![{row['context_k']} {row['model_id']} {row['effort_label']}](../{row['figure']})")
                lines.append("")
    if not skipped.empty:
        lines.extend(
            [
                "## Skipped Rows",
                "",
                "These are expected mainly for `k0`, where there are no context predictors to fit.",
                "",
                markdown_table(skipped[["context_k", "model_id", "model_label", "effort_label", "status", "error"]], max_rows=120),
                "",
            ]
        )
    lines.extend(
        [
            "## Saved Outputs",
            "",
            "```text",
            str(output_dir / "context_fixed_effort_model_summary.csv"),
            str(output_dir / "context_fixed_effort_bin_definitions.csv"),
            str(output_dir / "context_fixed_effort_predictions.csv.gz"),
            str(output_dir / "context_fixed_effort_slice_slopes.csv"),
            str(output_dir / "context_fixed_effort_figure_manifest.csv"),
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
    """Fit context fixed-effort atlas models and write outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_parts: list[pd.DataFrame] = []
    prediction_parts: list[pd.DataFrame] = []
    bin_parts: list[pd.DataFrame] = []
    for context_k in context_ks:
        print(f"[stage] context fixed-effort analysis {context_k}", flush=True)
        frame = read_measured_context_rows(context_output_dir, context_k)
        summary, predictions, bin_defs = fit_and_predict_context_atlas(frame, context_k=context_k, n_points=n_points)
        summary_parts.append(summary)
        prediction_parts.append(predictions)
        bin_parts.append(bin_defs)
        del frame, summary, predictions, bin_defs
        gc.collect()
    summary_all = pd.concat(summary_parts, ignore_index=True) if summary_parts else pd.DataFrame()
    predictions_all = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    bin_defs_all = pd.concat(bin_parts, ignore_index=True) if bin_parts else pd.DataFrame()
    figure_manifest = plot_context_fixed_predictions(predictions_all, fig_dir=fig_dir)
    slopes = fixed_slice_slopes(predictions_all)
    summary_all.to_csv(output_dir / "context_fixed_effort_model_summary.csv", index=False)
    bin_defs_all.to_csv(output_dir / "context_fixed_effort_bin_definitions.csv", index=False)
    predictions_all.to_csv(output_dir / "context_fixed_effort_predictions.csv.gz", index=False)
    slopes.to_csv(output_dir / "context_fixed_effort_slice_slopes.csv", index=False)
    figure_manifest.to_csv(output_dir / "context_fixed_effort_figure_manifest.csv", index=False)
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
    audit.to_csv(output_dir / "context_fixed_effort_audit.csv", index=False)
    return {
        "summary": output_dir / "context_fixed_effort_model_summary.csv",
        "bin_defs": output_dir / "context_fixed_effort_bin_definitions.csv",
        "predictions": output_dir / "context_fixed_effort_predictions.csv.gz",
        "slopes": output_dir / "context_fixed_effort_slice_slopes.csv",
        "figure_manifest": output_dir / "context_fixed_effort_figure_manifest.csv",
        "audit": output_dir / "context_fixed_effort_audit.csv",
    }


def run_report(*, output_dir: Path, fig_dir: Path, md_path: Path, html_path: Path) -> dict[str, Path]:
    """Render the report from saved analysis outputs."""

    summary = pd.read_csv(output_dir / "context_fixed_effort_model_summary.csv")
    bin_defs = pd.read_csv(output_dir / "context_fixed_effort_bin_definitions.csv")
    figure_manifest = pd.read_csv(output_dir / "context_fixed_effort_figure_manifest.csv")
    slopes = pd.read_csv(output_dir / "context_fixed_effort_slice_slopes.csv")
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
    parser.add_argument("--n-points", type=int, default=70)
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
        print(f"[OK] wrote context fixed-effort audit: {outputs['audit']}")
        print(f"[OK] wrote context fixed-effort summary: {outputs['summary']}")
    if args.stage in {"all", "report"}:
        outputs = run_report(output_dir=args.output_dir, fig_dir=args.fig_dir, md_path=args.md, html_path=args.html)
        print(f"[OK] wrote context fixed-effort report: {outputs['html']}")


if __name__ == "__main__":
    main()
