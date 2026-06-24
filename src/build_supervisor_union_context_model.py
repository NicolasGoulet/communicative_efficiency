#!/usr/bin/env python3
"""Fit the supervisor no-question union context model.

This model is the union of the M4a and M4b predictors without adding question
type:

    sum_bits ~ age_c + effort_c + age_c:effort_c
             + parent_context_effort_c + context_entropy_c + C(child_id)

It is meant as a clean supervisor-facing follow-up after M3.
"""

from __future__ import annotations

import argparse
import gc
import sys
from pathlib import Path
from typing import Sequence

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_route1_corrected_baseline_atlas import (
        CorrectedModelSpec,
        EFFORT_SPECS,
        add_corrected_predictors,
        read_route1_rows,
        selected_effort_specs,
        split_csv,
    )
    from build_route1_source_specific_m1_m6_fixed_effort_atlas import (
        fit_one_spec,
        fixed_effort_bins,
        fixed_slice_slopes,
        plot_fixed_predictions,
    )
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_corrected_baseline_atlas import (
        CorrectedModelSpec,
        EFFORT_SPECS,
        add_corrected_predictors,
        read_route1_rows,
        selected_effort_specs,
        split_csv,
    )
    from src.build_route1_source_specific_m1_m6_fixed_effort_atlas import (
        fit_one_spec,
        fixed_effort_bins,
        fixed_slice_slopes,
        plot_fixed_predictions,
    )


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/supervisor_union_context_model")
DEFAULT_FIG_DIR = Path("figs/supervisor_union_context_model")
MODEL_ID = "M4ab_no_question"
MODEL_LABEL = "Parent-context effort plus context entropy, no question type"


def build_union_specs(effort_cols: Sequence[str]) -> list[CorrectedModelSpec]:
    """Return one union-context model spec per requested effort column."""

    specs: list[CorrectedModelSpec] = []
    for effort in selected_effort_specs(effort_cols):
        readable = "sum_bits ~ age * effort + parent_context_effort + context_entropy + C(child_id)"
        statsmodels = (
            "sum_bits ~ age_c + effort_c + age_c:effort_c "
            "+ parent_context_effort_c + context_entropy_c + C(child_id)"
        )
        specs.append(
            CorrectedModelSpec(
                model_id=MODEL_ID,
                model_label=MODEL_LABEL,
                question=(
                    "Does the age-by-effort pattern remain after controlling both "
                    "preceding caretaker effort and context entropy, without question type?"
                ),
                model_tier="core",
                target_source="real",
                context_k="k3",
                effort_col=effort.effort_col,
                effort_label=effort.effort_label,
                parent_context_col=effort.parent_context_col,
                child_structure="CS1",
                estimator="ols",
                covariance="cluster_child",
                random_effects="",
                readable_formula=readable,
                statsmodels_formula=statsmodels,
                needs_parent_context_effort=True,
                needs_context_entropy=True,
                needs_question_type=False,
                uses_age_bin=False,
                stage="supervisor_union_context_model",
            )
        )
    return specs


def fit_union_context_model(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    effort_cols: Sequence[str],
    chunksize: int,
    n_points: int,
    max_rows: int | None = None,
) -> dict[str, Path]:
    """Fit the no-question union model and write reusable artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    frame = read_route1_rows(
        input_csv,
        chunksize=chunksize,
        max_rows=max_rows,
        target_sources=("real",),
        context_ks=("k3",),
        roles=("child",),
    )
    if frame.empty:
        raise RuntimeError("No real child k3 rows were found.")
    frame = add_corrected_predictors(frame)

    bin_defs = fixed_effort_bins(frame)
    rows: list[dict[str, object]] = []
    prediction_parts: list[pd.DataFrame] = []
    coefficient_parts: list[pd.DataFrame] = []

    specs = build_union_specs(effort_cols)
    for idx, spec in enumerate(specs, start=1):
        print(f"[union-context] fitting {idx}/{len(specs)} {spec.effort_col}", flush=True)
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
    slopes = fixed_slice_slopes(predictions)
    figures = plot_fixed_predictions(
        predictions,
        fig_dir=fig_dir,
        title_template="Model 4: both context controls | {effort_label}",
    )

    paths = {
        "summary": output_dir / "union_context_model_summary.csv",
        "predictions": output_dir / "union_context_fixed_effort_predictions.csv.gz",
        "coefficients": output_dir / "union_context_coefficient_long.csv",
        "slopes": output_dir / "union_context_fixed_slice_slopes.csv",
        "bin_defs": output_dir / "union_context_fixed_effort_bins.csv",
        "figures": output_dir / "union_context_figure_manifest.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    predictions.to_csv(paths["predictions"], index=False)
    coefficients.to_csv(paths["coefficients"], index=False)
    slopes.to_csv(paths["slopes"], index=False)
    bin_defs.to_csv(paths["bin_defs"], index=False)
    figures.to_csv(paths["figures"], index=False)
    return paths


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--effort-cols", default=",".join(spec.effort_col for spec in EFFORT_SPECS))
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--n-points", type=int, default=90)
    parser.add_argument("--max-rows", type=int, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    paths = fit_union_context_model(
        input_csv=args.input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        effort_cols=split_csv(args.effort_cols),
        chunksize=args.chunksize,
        n_points=args.n_points,
        max_rows=args.max_rows,
    )
    for label, path in paths.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
