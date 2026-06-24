#!/usr/bin/env python3
"""Build fixed-effort estimator plots for the two-final-candidates report."""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


DEFAULT_INPUT = Path("results/route1_child_length_controlled_model_suite/fixed_effort_predictions.csv.gz")
DEFAULT_SLOPES = Path("results/route1_child_length_controlled_model_suite/fixed_slice_slopes.csv")
DEFAULT_OUTPUT_DIR = Path("results/two_final_model_candidates_report")
DEFAULT_FIG_DIR = Path("figs/two_final_model_candidates_report")

FIXED_WORD_VALUES = (2, 6, 10)

SELECTED_ESTIMATORS: tuple[str, ...] = (
    "row_ols_fe_cluster",
    "agg_ols_fe_cluster",
    "agg_gee_gaussian",
    "agg_gee_gamma_log",
    "agg_mixed_random_intercept",
    "agg_mixed_session_intercept",
)

ESTIMATOR_TITLES = {
    "row_ols_fe_cluster": "Row OLS + child FE\nclustered SE",
    "agg_ols_fe_cluster": "Session/effort OLS\nchild FE + clustered SE",
    "agg_gee_gaussian": "GEE Gaussian\nby child",
    "agg_gee_gamma_log": "GEE Gamma/log\nby child",
    "agg_mixed_random_intercept": "MixedLM\nrandom child intercept",
    "agg_mixed_session_intercept": "MixedLM\nchild + session intercepts",
}


@dataclass(frozen=True)
class PlotSpec:
    """One report-facing fixed-effort estimator plot."""

    formula_id: str
    filename: str
    title: str
    subtitle: str


PLOT_SPECS: tuple[PlotSpec, ...] = (
    PlotSpec(
        formula_id="F01",
        filename="f01_m2_analogue_fixed_word_estimator_panels.png",
        title="M2 analogue: age + effort + child identity",
        subtitle="Predicted sum_bits by age at fixed 2-, 6-, and 10-word utterances",
    ),
    PlotSpec(
        formula_id="F02",
        filename="f02_m3_analogue_fixed_word_estimator_panels.png",
        title="M3 analogue: age + effort + age:effort + child identity",
        subtitle="Same fixed-word plot logic, now allowing the age slope to differ by utterance length",
    ),
    PlotSpec(
        formula_id="F10",
        filename="f10_context_controls_fixed_word_estimator_panels.png",
        title="Context-control estimator grid: M4-style age:effort plus context controls",
        subtitle="Closest already-fit estimator-grid analogue; this grid also includes question type",
    ),
    PlotSpec(
        formula_id="F19",
        filename="f19_exact_length_fixed_word_estimator_panels.png",
        title="Exact-length check: age slopes by exact word-count category",
        subtitle="This is the direct MLU guard because length is fixed as a category",
    ),
    PlotSpec(
        formula_id="F21",
        filename="f21_exact_length_context_fixed_word_estimator_panels.png",
        title="Exact-length context-control check",
        subtitle="Exact word-count categories plus context controls; this grid also includes question type",
    ),
)


def selected_predictions(
    predictions: pd.DataFrame,
    *,
    formula_id: str,
    estimator_ids: Sequence[str] = SELECTED_ESTIMATORS,
    fixed_values: Sequence[int] = FIXED_WORD_VALUES,
) -> pd.DataFrame:
    """Return the report plot slice from the saved fixed-effort grid."""

    required = {"formula_id", "estimator_id", "fixed_effort_value", "age_months", "predicted_sum_bits"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"prediction grid is missing columns: {sorted(missing)}")

    selected = predictions[
        predictions["formula_id"].astype(str).eq(formula_id)
        & predictions["estimator_id"].astype(str).isin(estimator_ids)
        & predictions["fixed_effort_value"].astype(int).isin([int(value) for value in fixed_values])
    ].copy()
    if selected.empty:
        return selected

    estimator_order = {estimator_id: idx for idx, estimator_id in enumerate(estimator_ids)}
    fixed_order = {int(value): idx for idx, value in enumerate(fixed_values)}
    selected["estimator_order"] = selected["estimator_id"].map(estimator_order)
    selected["fixed_order"] = selected["fixed_effort_value"].astype(int).map(fixed_order)
    selected = selected.sort_values(["estimator_order", "fixed_order", "age_months"]).reset_index(drop=True)
    return selected


def load_prediction_grid(path: Path) -> pd.DataFrame:
    """Read the saved prediction grid with only the columns needed here."""

    usecols = [
        "formula_id",
        "formula_label",
        "estimator_id",
        "estimator_label",
        "fixed_effort_value",
        "age_months",
        "predicted_sum_bits",
        "pred_ci_low",
        "pred_ci_high",
    ]
    return pd.read_csv(path, usecols=usecols)


def plot_estimator_panels(
    predictions: pd.DataFrame,
    spec: PlotSpec,
    *,
    fig_dir: Path,
    estimator_ids: Sequence[str] = SELECTED_ESTIMATORS,
    fixed_values: Sequence[int] = FIXED_WORD_VALUES,
) -> Path:
    """Create one multi-estimator fixed-word panel plot."""

    data = selected_predictions(
        predictions,
        formula_id=spec.formula_id,
        estimator_ids=estimator_ids,
        fixed_values=fixed_values,
    )
    if data.empty:
        raise ValueError(f"no fixed-effort predictions found for {spec.formula_id}")

    fig_dir.mkdir(parents=True, exist_ok=True)
    present_estimators = [estimator_id for estimator_id in estimator_ids if estimator_id in set(data["estimator_id"])]
    ncols = 3
    nrows = math.ceil(len(present_estimators) / ncols)
    palette = {
        int(fixed_values[0]): "#1b9e77",
        int(fixed_values[1]): "#d95f02",
        int(fixed_values[2]): "#3b5ba7",
    }

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(nrows, ncols, figsize=(15.8, 4.85 * nrows), sharex=True, sharey=True)
    flat_axes = list(axes.flat if hasattr(axes, "flat") else [axes])

    for ax, estimator_id in zip(flat_axes, present_estimators):
        estimator_data = data[data["estimator_id"].astype(str).eq(estimator_id)]
        for fixed_value in fixed_values:
            line = estimator_data[estimator_data["fixed_effort_value"].astype(int).eq(int(fixed_value))].sort_values(
                "age_months"
            )
            if line.empty:
                continue
            color = palette[int(fixed_value)]
            ax.plot(
                line["age_months"],
                line["predicted_sum_bits"],
                color=color,
                linewidth=2.3,
                label=f"{int(fixed_value)} words",
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
        ax.set_title(ESTIMATOR_TITLES.get(estimator_id, estimator_id), fontsize=14)
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Predicted total bits")
        ax.grid(alpha=0.22)

    for ax in flat_axes[len(present_estimators) :]:
        ax.axis("off")

    handles, labels = flat_axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(fixed_values), frameon=False, bbox_to_anchor=(0.5, -0.005))
    fig.suptitle(spec.title, fontsize=18, y=0.995)
    fig.text(0.5, 0.955, spec.subtitle, ha="center", va="top", fontsize=12, color="#555555")
    fig.tight_layout(rect=[0, 0.045, 1, 0.92])
    path = fig_dir / spec.filename
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return path


def summarize_slopes(
    slopes: pd.DataFrame,
    *,
    formula_ids: Sequence[str],
    estimator_ids: Sequence[str] = SELECTED_ESTIMATORS,
    fixed_values: Sequence[int] = FIXED_WORD_VALUES,
) -> pd.DataFrame:
    """Create a compact CSV table for the plotted slope values."""

    required = {"formula_id", "estimator_id", "fixed_effort_value", "slope_bits_per_6_months", "direction"}
    missing = required.difference(slopes.columns)
    if missing:
        raise ValueError(f"slope grid is missing columns: {sorted(missing)}")

    selected = slopes[
        slopes["formula_id"].astype(str).isin(formula_ids)
        & slopes["estimator_id"].astype(str).isin(estimator_ids)
        & slopes["fixed_effort_value"].astype(int).isin([int(value) for value in fixed_values])
    ].copy()
    columns = [
        "formula_id",
        "formula_label",
        "estimator_id",
        "estimator_label",
        "fixed_effort_value",
        "slope_bits_per_6_months",
        "direction",
    ]
    return selected[columns].sort_values(["formula_id", "estimator_id", "fixed_effort_value"]).reset_index(drop=True)


def build_outputs(
    *,
    input_csv: Path = DEFAULT_INPUT,
    slopes_csv: Path = DEFAULT_SLOPES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> dict[str, Path]:
    """Build all report figures and the supporting slope CSV."""

    predictions = load_prediction_grid(input_csv)
    paths = [plot_estimator_panels(predictions, spec, fig_dir=fig_dir) for spec in PLOT_SPECS]

    output_dir.mkdir(parents=True, exist_ok=True)
    slopes = pd.read_csv(slopes_csv)
    slope_summary = summarize_slopes(slopes, formula_ids=[spec.formula_id for spec in PLOT_SPECS])
    slope_summary_path = output_dir / "fixed_word_estimator_panel_slopes.csv"
    slope_summary.to_csv(slope_summary_path, index=False)

    manifest = pd.DataFrame(
        [
            {
                "formula_id": spec.formula_id,
                "title": spec.title,
                "subtitle": spec.subtitle,
                "figure": str(path),
            }
            for spec, path in zip(PLOT_SPECS, paths)
        ]
    )
    manifest_path = output_dir / "fixed_word_estimator_panel_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    return {"manifest": manifest_path, "slopes": slope_summary_path, **{spec.formula_id: path for spec, path in zip(PLOT_SPECS, paths)}}


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--slopes", type=Path, default=DEFAULT_SLOPES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = build_outputs(input_csv=args.input, slopes_csv=args.slopes, output_dir=args.output_dir, fig_dir=args.fig_dir)
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
