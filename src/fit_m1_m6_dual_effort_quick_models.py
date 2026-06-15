#!/usr/bin/env python3
"""Fit compact M1-M6 models with two effort strategies.

This is the analysis stage for the quick-share M1-M6 report. It deliberately
separates model fitting/plotting from report rendering.

For every M1-M6 family and every effort unit, we fit two variants:

1. ``continuous``: the effort count enters the formula as a numeric predictor.
2. ``effort_level``: the same effort count is converted to low/mid/high
   tertile groups and enters the formula as a categorical predictor.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    from build_m1_m2_utterance_information_deep_dive import (
        DEFAULT_INPUT,
        EFFORT_MEASURES,
        SEED,
        assign_effort_level,
        prediction_summary_frame,
        read_modeling_rows,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import (
        DEFAULT_INPUT,
        EFFORT_MEASURES,
        SEED,
        assign_effort_level,
        prediction_summary_frame,
        read_modeling_rows,
    )


DEFAULT_OUTPUT_DIR = Path("results/m1_m6_dual_effort_quick_share")
DEFAULT_FIG_DIR = Path("figs/m1_m6_dual_effort_quick_share")

EFFORT_ORDER = [label for _, label in EFFORT_MEASURES]
EFFORT_LABEL_TO_COL = {label: col for col, label in EFFORT_MEASURES}
EFFORT_LEVELS = ["low effort", "mid effort", "high effort"]


@dataclass(frozen=True)
class DualModelSpec:
    """One M1-M6 specification in continuous and categorical effort forms."""

    model_id: str
    model_title: str
    question: str
    continuous_formula: str
    effort_level_formula: str


@dataclass(frozen=True)
class DualFitBundle:
    """A fitted dual-effort model plus metadata."""

    model_id: str
    model_title: str
    question: str
    effort_strategy: str
    effort_col: str
    effort_label: str
    formula: str
    readable_formula: str
    result: object | None
    status: str
    error: str
    n_obs: int
    n_children: int
    age_mean: float
    effort_mean: float
    effort_median: float
    entropy_mean: float


DUAL_MODEL_SPECS = [
    DualModelSpec(
        model_id="M1",
        model_title="Pooled age and effort",
        question="Pooling all children, does age predict total bits after controlling utterance effort?",
        continuous_formula="sum_bits ~ age_c + effort_c",
        effort_level_formula="sum_bits ~ age_c + C(effort_level)",
    ),
    DualModelSpec(
        model_id="M2",
        model_title="Age and effort with child identity",
        question="Does the developmental age effect remain after child identity is controlled?",
        continuous_formula="sum_bits ~ age_c + effort_c + C(child_id)",
        effort_level_formula="sum_bits ~ age_c + C(effort_level) + C(child_id)",
    ),
    DualModelSpec(
        model_id="M3",
        model_title="Age by effort",
        question="Does the relation between effort and total bits change with age?",
        continuous_formula="sum_bits ~ age_c * effort_c + C(child_id)",
        effort_level_formula="sum_bits ~ age_c * C(effort_level) + C(child_id)",
    ),
    DualModelSpec(
        model_id="M4",
        model_title="Context entropy added",
        question="Does context entropy add predictive information beyond age, effort, and child identity?",
        continuous_formula="sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)",
        effort_level_formula="sum_bits ~ age_c + C(effort_level) + context_entropy_c + C(child_id)",
    ),
    DualModelSpec(
        model_id="M5",
        model_title="Age by context entropy",
        question="Does the context-entropy effect on total bits change over development?",
        continuous_formula="sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id)",
        effort_level_formula="sum_bits ~ age_c * context_entropy_c + C(effort_level) + C(child_id)",
    ),
    DualModelSpec(
        model_id="M6",
        model_title="Interaction-rich exploratory model",
        question="Do age, effort, and context entropy interact when predicting total bits?",
        continuous_formula=(
            "sum_bits ~ age_c * effort_c + age_c * context_entropy_c + "
            "effort_c * context_entropy_c + C(child_id)"
        ),
        effort_level_formula=(
            "sum_bits ~ age_c * C(effort_level) + context_entropy_c * C(effort_level) + "
            "age_c * context_entropy_c + C(child_id)"
        ),
    ),
]


READABLE_FORMULAS: Mapping[tuple[str, str], str] = {
    ("M1", "continuous"): "sum_bits ~ age + effort",
    ("M1", "effort_level"): "sum_bits ~ age + effort_level",
    ("M2", "continuous"): "sum_bits ~ age + effort + child identity",
    ("M2", "effort_level"): "sum_bits ~ age + effort_level + child identity",
    ("M3", "continuous"): "sum_bits ~ age * effort + child identity",
    ("M3", "effort_level"): "sum_bits ~ age * effort_level + child identity",
    ("M4", "continuous"): "sum_bits ~ age + effort + context_entropy + child identity",
    ("M4", "effort_level"): "sum_bits ~ age + effort_level + context_entropy + child identity",
    ("M5", "continuous"): "sum_bits ~ age * context_entropy + effort + child identity",
    ("M5", "effort_level"): "sum_bits ~ age * context_entropy + effort_level + child identity",
    ("M6", "continuous"): "sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity",
    ("M6", "effort_level"): "sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity",
}


def needs_context_entropy(spec: DualModelSpec) -> bool:
    """Return whether a model requires context entropy."""

    return "context_entropy_c" in spec.continuous_formula or "context_entropy_c" in spec.effort_level_formula


def model_frame_for_effort(frame: pd.DataFrame, effort_col: str, *, require_entropy: bool) -> pd.DataFrame:
    """Create the centered model frame for one effort unit."""

    out = frame.copy()
    out["effort_value"] = pd.to_numeric(out[effort_col], errors="coerce")
    needed = ["sum_bits", "age_months", "effort_value", "child_id"]
    if require_entropy:
        out["context_entropy_bits"] = pd.to_numeric(out["context_entropy_bits"], errors="coerce")
        needed.append("context_entropy_bits")
    out = out.dropna(subset=needed).copy()
    out = out[(out["sum_bits"] > 0) & (out["age_months"] > 0) & (out["effort_value"] > 0)].copy()
    if require_entropy:
        out = out[out["context_entropy_bits"] > 0].copy()
    if out.empty:
        return out
    out["age_mean"] = float(out["age_months"].mean())
    out["effort_mean"] = float(out["effort_value"].mean())
    out["entropy_mean"] = float(out["context_entropy_bits"].mean()) if require_entropy else 0.0
    out["age_c"] = out["age_months"] - out["age_mean"].iloc[0]
    out["effort_c"] = out["effort_value"] - out["effort_mean"].iloc[0]
    out["context_entropy_c"] = (
        out["context_entropy_bits"] - out["entropy_mean"].iloc[0]
        if require_entropy
        else 0.0
    )
    out["effort_level"] = assign_effort_level(out["effort_value"])
    out["child_id"] = out["child_id"].astype(str)
    return out.reset_index(drop=True)


def fit_dual_models(frame: pd.DataFrame) -> tuple[list[DualFitBundle], dict[tuple[str, str], pd.DataFrame]]:
    """Fit all M1-M6 continuous and effort-level models."""

    bundles: list[DualFitBundle] = []
    model_frames: dict[tuple[str, str], pd.DataFrame] = {}
    for spec in DUAL_MODEL_SPECS:
        for effort_col, effort_label in EFFORT_MEASURES:
            model_frame = model_frame_for_effort(frame, effort_col, require_entropy=needs_context_entropy(spec))
            model_frames[(spec.model_id, effort_col)] = model_frame
            for strategy, formula in [
                ("continuous", spec.continuous_formula),
                ("effort_level", spec.effort_level_formula),
            ]:
                if model_frame.empty:
                    result = None
                    status = "empty"
                    error = "no complete rows"
                else:
                    try:
                        result = smf.ols(formula, data=model_frame).fit(
                            cov_type="cluster",
                            cov_kwds={"groups": model_frame["child_id"]},
                        )
                        status = "fit"
                        error = ""
                    except Exception as exc:  # pragma: no cover - real-data guard
                        result = None
                        status = "failed"
                        error = f"{type(exc).__name__}: {exc}"
                bundles.append(
                    DualFitBundle(
                        model_id=spec.model_id,
                        model_title=spec.model_title,
                        question=spec.question,
                        effort_strategy=strategy,
                        effort_col=effort_col,
                        effort_label=effort_label,
                        formula=formula,
                        readable_formula=READABLE_FORMULAS[(spec.model_id, strategy)],
                        result=result,
                        status=status,
                        error=error,
                        n_obs=len(model_frame),
                        n_children=int(model_frame["child_id"].nunique()) if not model_frame.empty else 0,
                        age_mean=float(model_frame["age_mean"].iloc[0]) if not model_frame.empty else math.nan,
                        effort_mean=float(model_frame["effort_mean"].iloc[0]) if not model_frame.empty else math.nan,
                        effort_median=float(model_frame["effort_value"].median()) if not model_frame.empty else math.nan,
                        entropy_mean=float(model_frame["entropy_mean"].iloc[0]) if not model_frame.empty else math.nan,
                    )
                )
    return bundles, model_frames


def fitted_r2(observed: np.ndarray, fitted: np.ndarray) -> float:
    """Compute observed-vs-fitted R2."""

    sst = float(np.sum((observed - np.mean(observed)) ** 2))
    if sst <= 0:
        return math.nan
    return 1.0 - float(np.sum((observed - fitted) ** 2)) / sst


def param_value(result: object | None, term: str, attr: str = "params") -> float:
    """Read a coefficient, standard error, or p-value."""

    if result is None:
        return math.nan
    source = getattr(result, attr, None)
    if source is None or term not in source.index:
        return math.nan
    return float(source[term])


def model_summary_rows(bundles: Sequence[DualFitBundle]) -> pd.DataFrame:
    """Summarize all fitted M1-M6 dual-effort models."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = bundle.result
        if result is None:
            observed = np.array([], dtype=float)
            fitted = np.array([], dtype=float)
        else:
            observed = np.asarray(result.model.endog, dtype=float)
            fitted = np.asarray(result.fittedvalues, dtype=float)
        rows.append(
            {
                "model_id": bundle.model_id,
                "model_title": bundle.model_title,
                "question": bundle.question,
                "effort_strategy": bundle.effort_strategy,
                "effort_col": bundle.effort_col,
                "effort_label": bundle.effort_label,
                "formula": bundle.formula,
                "readable_formula": bundle.readable_formula,
                "status": bundle.status,
                "error": bundle.error,
                "n_obs": bundle.n_obs,
                "n_children": bundle.n_children,
                "r2_observed_fitted": fitted_r2(observed, fitted) if len(observed) else math.nan,
                "rmse": math.sqrt(mean_squared_error(observed, fitted)) if len(observed) else math.nan,
                "mae": float(mean_absolute_error(observed, fitted)) if len(observed) else math.nan,
                "age_coef": param_value(result, "age_c"),
                "age_p": param_value(result, "age_c", "pvalues"),
                "effort_coef": param_value(result, "effort_c"),
                "effort_p": param_value(result, "effort_c", "pvalues"),
                "entropy_coef": param_value(result, "context_entropy_c"),
                "entropy_p": param_value(result, "context_entropy_c", "pvalues"),
                "age_effort_coef": param_value(result, "age_c:effort_c"),
                "age_effort_p": param_value(result, "age_c:effort_c", "pvalues"),
                "age_entropy_coef": param_value(result, "age_c:context_entropy_c"),
                "age_entropy_p": param_value(result, "age_c:context_entropy_c", "pvalues"),
                "effort_entropy_coef": param_value(result, "effort_c:context_entropy_c"),
                "effort_entropy_p": param_value(result, "effort_c:context_entropy_c", "pvalues"),
                "mid_effort_coef": param_value(result, "C(effort_level)[T.mid effort]"),
                "mid_effort_p": param_value(result, "C(effort_level)[T.mid effort]", "pvalues"),
                "high_effort_coef": param_value(result, "C(effort_level)[T.high effort]"),
                "high_effort_p": param_value(result, "C(effort_level)[T.high effort]", "pvalues"),
                "mid_effort_age_delta": param_value(result, "age_c:C(effort_level)[T.mid effort]"),
                "mid_effort_age_delta_p": param_value(result, "age_c:C(effort_level)[T.mid effort]", "pvalues"),
                "high_effort_age_delta": param_value(result, "age_c:C(effort_level)[T.high effort]"),
                "high_effort_age_delta_p": param_value(result, "age_c:C(effort_level)[T.high effort]", "pvalues"),
                "mid_effort_entropy_delta": param_value(result, "context_entropy_c:C(effort_level)[T.mid effort]"),
                "mid_effort_entropy_delta_p": param_value(result, "context_entropy_c:C(effort_level)[T.mid effort]", "pvalues"),
                "high_effort_entropy_delta": param_value(result, "context_entropy_c:C(effort_level)[T.high effort]"),
                "high_effort_entropy_delta_p": param_value(result, "context_entropy_c:C(effort_level)[T.high effort]", "pvalues"),
            }
        )
    return pd.DataFrame(rows)


def prediction_frame(result: object, frame: pd.DataFrame) -> pd.DataFrame:
    """Return predictions and confidence intervals for a new-data frame."""

    summary = prediction_summary_frame(result, frame)
    out = frame.copy()
    out["predicted_sum_bits"] = summary["predicted_sum_bits"].to_numpy(dtype=float)
    out["pred_ci_low"] = summary["pred_ci_low"].to_numpy(dtype=float)
    out["pred_ci_high"] = summary["pred_ci_high"].to_numpy(dtype=float)
    return out


def average_child_predictions(bundle: DualFitBundle, base: pd.DataFrame, child_ids: Sequence[str]) -> pd.DataFrame:
    """Predict a frame, averaging over child fixed intercepts when present."""

    if bundle.result is None:
        return pd.DataFrame()
    if "C(child_id)" not in bundle.formula:
        return prediction_frame(bundle.result, base)
    parts: list[pd.DataFrame] = []
    for child_id in child_ids:
        child_frame = base.copy()
        child_frame["child_id"] = child_id
        parts.append(prediction_frame(bundle.result, child_frame))
    combined = pd.concat(parts, ignore_index=True)
    return combined.groupby("age_months", as_index=False)[
        ["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]
    ].mean()


def continuous_prediction_grid(
    bundle: DualFitBundle,
    model_frame: pd.DataFrame,
    *,
    n_points: int = 90,
) -> pd.DataFrame:
    """Create an adjusted age line for a continuous-effort fit."""

    if bundle.result is None or model_frame.empty:
        return pd.DataFrame()
    ages = np.linspace(model_frame["age_months"].quantile(0.02), model_frame["age_months"].quantile(0.98), n_points)
    base = pd.DataFrame(
        {
            "age_months": ages,
            "age_c": ages - bundle.age_mean,
            "effort_value": bundle.effort_median,
            "effort_c": bundle.effort_median - bundle.effort_mean,
            "context_entropy_bits": bundle.entropy_mean,
            "context_entropy_c": 0.0,
        }
    )
    pred = average_child_predictions(bundle, base, sorted(model_frame["child_id"].astype(str).unique()))
    pred["reference"] = "median continuous effort"
    pred["fixed_effort_value"] = bundle.effort_median
    return pred


def effort_level_prediction_grid(
    bundle: DualFitBundle,
    model_frame: pd.DataFrame,
    *,
    n_points: int = 90,
) -> pd.DataFrame:
    """Create adjusted age lines for low/mid/high effort-level fits."""

    if bundle.result is None or model_frame.empty:
        return pd.DataFrame()
    ages = np.linspace(model_frame["age_months"].quantile(0.02), model_frame["age_months"].quantile(0.98), n_points)
    parts: list[pd.DataFrame] = []
    child_ids = sorted(model_frame["child_id"].astype(str).unique())
    for level in EFFORT_LEVELS:
        if level not in set(model_frame["effort_level"].astype(str)):
            continue
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - bundle.age_mean,
                "effort_level": pd.Categorical([level] * len(ages), categories=EFFORT_LEVELS, ordered=True),
                "context_entropy_bits": bundle.entropy_mean,
                "context_entropy_c": 0.0,
            }
        )
        pred = average_child_predictions(bundle, base, child_ids)
        pred["reference"] = level
        pred["fixed_effort_value"] = level
        parts.append(pred)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def prediction_rows(
    bundles: Sequence[DualFitBundle],
    model_frames: Mapping[tuple[str, str], pd.DataFrame],
) -> pd.DataFrame:
    """Create saved prediction rows for all fitted models."""

    parts: list[pd.DataFrame] = []
    for bundle in bundles:
        model_frame = model_frames.get((bundle.model_id, bundle.effort_col), pd.DataFrame())
        if bundle.effort_strategy == "continuous":
            pred = continuous_prediction_grid(bundle, model_frame)
        else:
            pred = effort_level_prediction_grid(bundle, model_frame)
        if pred.empty:
            continue
        pred["model_id"] = bundle.model_id
        pred["model_title"] = bundle.model_title
        pred["effort_strategy"] = bundle.effort_strategy
        pred["effort_col"] = bundle.effort_col
        pred["effort_label"] = bundle.effort_label
        pred["readable_formula"] = bundle.readable_formula
        parts.append(pred)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def plot_dual_predictions(predictions: pd.DataFrame, fig_dir: Path) -> None:
    """Plot one compact two-strategy figure for each M1-M6 model."""

    if predictions.empty:
        return
    fig_dir.mkdir(parents=True, exist_ok=True)
    continuous_color = "#4c78a8"
    level_palette = {
        "low effort": "#4c78a8",
        "mid effort": "#f58518",
        "high effort": "#54a24b",
    }
    for spec in DUAL_MODEL_SPECS:
        sub = predictions[predictions["model_id"].eq(spec.model_id)].copy()
        if sub.empty:
            continue
        fig, axes = plt.subplots(2, 5, figsize=(19.0, 8.4), sharey=True)
        for col_idx, effort_label in enumerate(EFFORT_ORDER):
            continuous = sub[
                sub["effort_label"].eq(effort_label)
                & sub["effort_strategy"].eq("continuous")
            ]
            ax = axes[0, col_idx]
            if continuous.empty:
                ax.axis("off")
            else:
                ax.plot(
                    continuous["age_months"],
                    continuous["predicted_sum_bits"],
                    color=continuous_color,
                    linewidth=2.3,
                    label="continuous effort at median",
                )
                ci = continuous[["pred_ci_low", "pred_ci_high"]].apply(pd.to_numeric, errors="coerce")
                if ci.notna().all(axis=None):
                    ax.fill_between(
                        continuous["age_months"].to_numpy(dtype=float),
                        ci["pred_ci_low"].to_numpy(dtype=float),
                        ci["pred_ci_high"].to_numpy(dtype=float),
                        color=continuous_color,
                        alpha=0.14,
                        linewidth=0,
                    )
                fixed = continuous["fixed_effort_value"].iloc[0]
                ax.set_title(f"{effort_label}\ncontinuous, median={float(fixed):.1f}")
                ax.grid(alpha=0.18)
            ax.set_xlabel("Age in months")
            level = sub[
                sub["effort_label"].eq(effort_label)
                & sub["effort_strategy"].eq("effort_level")
            ]
            ax = axes[1, col_idx]
            if level.empty:
                ax.axis("off")
            else:
                for reference, group in level.groupby("reference", sort=False):
                    color = level_palette.get(str(reference), "#333333")
                    ax.plot(
                        group["age_months"],
                        group["predicted_sum_bits"],
                        color=color,
                        linewidth=2.1,
                        label=str(reference),
                    )
                    ci = group[["pred_ci_low", "pred_ci_high"]].apply(pd.to_numeric, errors="coerce")
                    if ci.notna().all(axis=None):
                        ax.fill_between(
                            group["age_months"].to_numpy(dtype=float),
                            ci["pred_ci_low"].to_numpy(dtype=float),
                            ci["pred_ci_high"].to_numpy(dtype=float),
                            color=color,
                            alpha=0.10,
                            linewidth=0,
                        )
                ax.set_title(f"{effort_label}\nlow/mid/high groups")
                ax.grid(alpha=0.18)
            ax.set_xlabel("Age in months")
        axes[0, 0].set_ylabel("Predicted total bits")
        axes[1, 0].set_ylabel("Predicted total bits")
        handles, labels = axes[1, 0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, title="Effort level", loc="lower center", ncol=3)
            bottom = 0.10
        else:
            bottom = 0.02
        fig.suptitle(f"{spec.model_id}: {spec.model_title}", y=0.98)
        fig.tight_layout(rect=(0, bottom, 1, 0.93))
        stem = f"{spec.model_id.lower()}_dual_effort_predictions"
        fig.savefig(fig_dir / f"{stem}.png", dpi=240)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)


def fit_and_plot_dual_effort_models(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    chunksize: int,
) -> Mapping[str, Path]:
    """Run the fitting/plotting stage and save CSV/figure artifacts."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_modeling_rows(input_csv, context_k=context_k, chunksize=chunksize)
    bundles, model_frames = fit_dual_models(frame)
    summary = model_summary_rows(bundles)
    predictions = prediction_rows(bundles, model_frames)
    summary.to_csv(output_dir / "dual_model_summary.csv", index=False)
    predictions.to_csv(output_dir / "dual_model_predictions.csv", index=False)
    audit = pd.DataFrame(
        [
            {
                "input_csv": str(input_csv),
                "context_k": context_k,
                "rows": len(frame),
                "children": frame["child_id"].nunique(),
                "age_min": frame["age_months"].min(),
                "age_max": frame["age_months"].max(),
                "fitted_model_rows": len(summary),
                "prediction_rows": len(predictions),
            }
        ]
    )
    audit.to_csv(output_dir / "dual_model_audit.csv", index=False)
    plot_dual_predictions(predictions, fig_dir)
    return {
        "summary": output_dir / "dual_model_summary.csv",
        "predictions": output_dir / "dual_model_predictions.csv",
        "audit": output_dir / "dual_model_audit.csv",
        "fig_dir": fig_dir,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--context-k", default="k3")
    parser.add_argument("--chunksize", type=int, default=500_000)
    args = parser.parse_args(argv)
    outputs = fit_and_plot_dual_effort_models(
        input_csv=args.input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        context_k=args.context_k,
        chunksize=args.chunksize,
    )
    print(f"[OK] wrote dual M1-M6 summary: {outputs['summary']}")
    print(f"[OK] wrote dual M1-M6 predictions: {outputs['predictions']}")
    print(f"[OK] wrote dual M1-M6 figures under: {outputs['fig_dir']}")


if __name__ == "__main__":
    main()
