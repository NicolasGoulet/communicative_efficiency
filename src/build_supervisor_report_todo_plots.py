#!/usr/bin/env python3
"""Build plots requested by TODOs in the supervisor-facing report.

The script reads only the real-child k3 rows and writes compact artifacts for
the report sections that currently ask for Model 0 descriptive plots and Model
1 effort-only fixed-effort plots.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import sys
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/supervisor_report_todo_plots")
DEFAULT_FIG_DIR = Path("figs/supervisor_report_todo_plots")
DEFAULT_M2_FIG_DIR = Path("figs/m2_simple_plots")
AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
EFFORTS = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables: CMU/pkg"),
    ("nb_syllables_pkg", "Syllables: pkg"),
    ("nb_phonemes", "Phonemes"),
]
EFFORT_UNITS = {
    "nb_words": ("word", "words"),
    "nb_morphemes": ("morpheme", "morphemes"),
    "nb_syllables_cmu_or_pkg": ("CMU/pkg syllable", "CMU/pkg syllables"),
    "nb_syllables_pkg": ("pkg syllable", "pkg syllables"),
    "nb_phonemes": ("phoneme", "phonemes"),
}


def as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def age_mid(age_bin: object) -> float:
    text = str(age_bin)
    try:
        low, high = text.split("-", 1)
        return (float(low) + float(high)) / 2.0
    except ValueError:
        return math.nan


def fixed_effort_label(effort_col: str, value: object) -> str:
    """Return a supervisor-facing fixed-effort label."""

    number = as_float(value)
    if not math.isfinite(number):
        return "fixed value"
    value_text = f"{number:g}"
    singular, plural = EFFORT_UNITS.get(effort_col, ("unit", "units"))
    unit = singular if abs(number - 1.0) < 1e-9 else plural
    return f"{value_text} {unit}"


def iter_real_k3_rows(input_csv: Path) -> Iterable[dict[str, object]]:
    opener = gzip.open if str(input_csv).endswith(".gz") else open
    scanned = 0
    kept = 0
    with opener(input_csv, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            scanned += 1
            if row.get("target_variant") != "real" or row.get("role") != "child" or row.get("context_k") != "k3":
                if scanned % 1_000_000 == 0:
                    print(f"[todo-plots] scanned={scanned:,}; kept={kept:,}", flush=True)
                continue
            age_months = as_float(row.get("age_months"))
            age_bin = str(row.get("age_bin", ""))
            sum_bits = as_float(row.get("sum_bits"))
            mean_bits = as_float(row.get("mean_bits_per_token"))
            efforts = {col: as_float(row.get(col)) for col, _ in EFFORTS}
            if not (math.isfinite(age_months) and age_bin in AGE_BIN_ORDER and math.isfinite(sum_bits) and math.isfinite(mean_bits)):
                continue
            if any(not math.isfinite(value) or value <= 0 for value in efforts.values()):
                continue
            kept += 1
            if scanned % 1_000_000 == 0:
                print(f"[todo-plots] scanned={scanned:,}; kept={kept:,}", flush=True)
            out = {
                "child_id": str(row.get("child_id", "")),
                "age_months": age_months,
                "age_bin": age_bin,
                "age_mid": age_mid(age_bin),
                "sum_bits": sum_bits,
                "mean_bits_per_token": mean_bits,
            }
            out.update(efforts)
            yield out
        print(f"[todo-plots] finished scan; scanned={scanned:,}; kept={kept:,}", flush=True)


def load_real_k3(input_csv: Path) -> pd.DataFrame:
    frame = pd.DataFrame(iter_real_k3_rows(input_csv))
    if frame.empty:
        raise RuntimeError("No real child k3 rows were found.")
    return frame


def summarize_age_bins(frame: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    rows = []
    for age_bin, group in frame.groupby("age_bin", observed=True):
        row = {"age_bin": age_bin, "age_mid": age_mid(age_bin), "n": len(group)}
        for col in ["nb_words", "sum_bits", "mean_bits_per_token"]:
            values = group[col].dropna()
            se = values.std(ddof=1) / math.sqrt(len(values)) if len(values) > 1 else math.nan
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_lo"] = float(values.mean() - 1.96 * se) if math.isfinite(se) else math.nan
            row[f"{col}_hi"] = float(values.mean() + 1.96 * se) if math.isfinite(se) else math.nan
        rows.append(row)
    out = pd.DataFrame(rows).sort_values("age_mid")
    out.to_csv(output_dir / "model0_age_bin_descriptives.csv", index=False)
    return out


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def prediction_summary(result: object, new_frame: pd.DataFrame) -> pd.DataFrame:
    """Return fitted means and 95% fitted-mean confidence intervals."""

    summary = result.get_prediction(new_frame).summary_frame(alpha=0.05)
    mean_col = "mean" if "mean" in summary.columns else "predicted_mean"
    low_col = "mean_ci_lower" if "mean_ci_lower" in summary.columns else "ci_lower"
    high_col = "mean_ci_upper" if "mean_ci_upper" in summary.columns else "ci_upper"
    return pd.DataFrame(
        {
            "predicted_sum_bits": summary[mean_col].to_numpy(dtype=float),
            "pred_ci_low": summary[low_col].to_numpy(dtype=float),
            "pred_ci_high": summary[high_col].to_numpy(dtype=float),
        }
    )


def child_average_prediction_summary(
    result: object,
    base: pd.DataFrame,
    child_ids: list[str],
) -> pd.DataFrame:
    """Predict for each child fixed intercept, then average the fitted means."""

    parts: list[pd.DataFrame] = []
    for child_id in child_ids:
        child_frame = base.copy()
        child_frame["child_id"] = child_id
        pred = prediction_summary(result, child_frame)
        parts.append(pd.concat([child_frame.reset_index(drop=True), pred.reset_index(drop=True)], axis=1))
    combined = pd.concat(parts, ignore_index=True)
    return (
        combined.groupby(["age_months", "line_type", "effort_level", "effort_value"], as_index=False)[
            ["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]
        ]
        .mean()
        .copy()
    )


def plot_descriptive(summary: pd.DataFrame, fig_dir: Path) -> None:
    specs = [
        ("nb_words_mean", "nb_words_lo", "nb_words_hi", "Mean length in words", "Model 0 descriptive: mean utterance length increases", "model0_mlu_words_by_age.png"),
        ("sum_bits_mean", "sum_bits_lo", "sum_bits_hi", "Mean total bits per utterance", "Model 0 descriptive: total utterance information increases", "model0_sum_bits_by_age.png"),
        ("mean_bits_per_token_mean", "mean_bits_per_token_lo", "mean_bits_per_token_hi", "Mean bits per evaluated token", "Model 0 descriptive: bits per token decreases", "model0_bits_per_token_by_age.png"),
    ]
    x = np.arange(len(summary))
    for mean_col, lo_col, hi_col, ylabel, title, filename in specs:
        plt.figure(figsize=(8.2, 4.8))
        y = summary[mean_col].to_numpy(dtype=float)
        lo = summary[lo_col].to_numpy(dtype=float)
        hi = summary[hi_col].to_numpy(dtype=float)
        plt.plot(x, y, marker="o", linewidth=2.2, color="#2f6f73")
        plt.fill_between(x, lo, hi, color="#2f6f73", alpha=0.24)
        plt.plot(x, lo, color="#2f6f73", linewidth=0.8, alpha=0.55)
        plt.plot(x, hi, color="#2f6f73", linewidth=0.8, alpha=0.55)
        plt.xticks(x, summary["age_bin"], rotation=35)
        plt.ylabel(ylabel)
        plt.xlabel("Age bin")
        plt.title(title)
        plt.grid(alpha=0.25)
        savefig(fig_dir / filename)


def fit_effort_only_models(frame: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficient_rows = []
    prediction_rows = []
    age_grid = np.linspace(frame["age_months"].min(), frame["age_months"].max(), 80)
    for effort_col, effort_label in EFFORTS:
        result = smf.ols(f"sum_bits ~ age_months + {effort_col}", data=frame).fit(
            cov_type="cluster",
            cov_kwds={"groups": frame["child_id"].astype(str)},
        )
        coefficient_rows.append(
            {
                "effort_col": effort_col,
                "effort_label": effort_label,
                "age_coef_bits_per_month": float(result.params["age_months"]),
                "age_p": float(result.pvalues["age_months"]),
                "effort_coef_bits_per_unit": float(result.params[effort_col]),
                "r2": float(result.rsquared),
                "nobs": int(result.nobs),
            }
        )
        quantiles = frame[effort_col].quantile([0.25, 0.50, 0.75]).to_dict()
        for label, effort_value in [("low", quantiles[0.25]), ("median", quantiles[0.50]), ("high", quantiles[0.75])]:
            grid = pd.DataFrame({"age_months": age_grid, effort_col: effort_value})
            pred_frame = prediction_summary(result, grid)
            for age, pred_row in zip(age_grid, pred_frame.to_dict("records")):
                prediction_rows.append(
                    {
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "effort_level": label,
                        "effort_value": float(effort_value),
                        "age_months": float(age),
                        "predicted_sum_bits": float(pred_row["predicted_sum_bits"]),
                        "pred_ci_low": float(pred_row["pred_ci_low"]),
                        "pred_ci_high": float(pred_row["pred_ci_high"]),
                    }
                )
    coefficients = pd.DataFrame(coefficient_rows)
    predictions = pd.DataFrame(prediction_rows)
    coefficients.to_csv(output_dir / "model1_effort_only_coefficients.csv", index=False)
    predictions.to_csv(output_dir / "model1_effort_only_predictions.csv", index=False)
    return coefficients, predictions


def plot_effort_only_predictions(predictions: pd.DataFrame, fig_dir: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.2), sharex=True)
    axes_flat = axes.flatten()
    colors = {"low": "#6d8f20", "median": "#2f6f73", "high": "#c76f2c"}
    for ax, (effort_col, effort_label) in zip(axes_flat, EFFORTS):
        panel = predictions[predictions["effort_col"].eq(effort_col)]
        for effort_value, group in panel.sort_values(["effort_value", "age_months"]).groupby("effort_value", sort=True):
            group = group.sort_values("age_months")
            level = str(group["effort_level"].iloc[0])
            if group[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                ax.fill_between(
                    group["age_months"].to_numpy(dtype=float),
                    group["pred_ci_low"].to_numpy(dtype=float),
                    group["pred_ci_high"].to_numpy(dtype=float),
                    color=colors.get(level, "gray"),
                    alpha=0.22,
                    linewidth=0,
                )
            ax.plot(
                group["age_months"],
                group["predicted_sum_bits"],
                color=colors.get(level, "gray"),
                linewidth=1.7,
                label=fixed_effort_label(effort_col, effort_value),
            )
            if group[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                ax.plot(
                    group["age_months"],
                    group["pred_ci_low"],
                    color=colors.get(level, "gray"),
                    linewidth=1.1,
                    alpha=0.75,
                )
                ax.plot(
                    group["age_months"],
                    group["pred_ci_high"],
                    color=colors.get(level, "gray"),
                    linewidth=1.1,
                    alpha=0.75,
                )
        ax.set_title(effort_label)
        ax.set_ylabel("Predicted total bits")
        ax.grid(alpha=0.25)
        ax.legend(title="Fixed value", fontsize=8, title_fontsize=8)
    axes_flat[-1].axis("off")
    fig.suptitle("Model 1: effort-only predictions without child identity", fontsize=15, y=1.02)
    for ax in axes_flat[:5]:
        ax.set_xlabel("Age in months")
    savefig(fig_dir / "model1_effort_only_fixed_effort_predictions.png")

    filenames = {
        "nb_words": "model1_words_effort_only_predictions.png",
        "nb_morphemes": "model1_morphemes_effort_only_predictions.png",
        "nb_syllables_cmu_or_pkg": "model1_syllables_cmu_pkg_effort_only_predictions.png",
        "nb_syllables_pkg": "model1_syllables_pkg_effort_only_predictions.png",
        "nb_phonemes": "model1_phonemes_effort_only_predictions.png",
    }
    for effort_col, effort_label in EFFORTS:
        panel = predictions[predictions["effort_col"].eq(effort_col)]
        plt.figure(figsize=(5.8, 3.7))
        for effort_value, group in panel.sort_values(["effort_value", "age_months"]).groupby("effort_value", sort=True):
            group = group.sort_values("age_months")
            level = str(group["effort_level"].iloc[0])
            if group[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                plt.fill_between(
                    group["age_months"].to_numpy(dtype=float),
                    group["pred_ci_low"].to_numpy(dtype=float),
                    group["pred_ci_high"].to_numpy(dtype=float),
                    color=colors.get(level, "gray"),
                    alpha=0.22,
                    linewidth=0,
                )
            plt.plot(
                group["age_months"],
                group["predicted_sum_bits"],
                color=colors.get(level, "gray"),
                linewidth=1.7,
                label=fixed_effort_label(effort_col, effort_value),
            )
            if group[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                plt.plot(
                    group["age_months"],
                    group["pred_ci_low"],
                    color=colors.get(level, "gray"),
                    linewidth=1.1,
                    alpha=0.75,
                )
                plt.plot(
                    group["age_months"],
                    group["pred_ci_high"],
                    color=colors.get(level, "gray"),
                    linewidth=1.1,
                    alpha=0.75,
                )
        plt.title(f"Model 1: {effort_label}")
        plt.xlabel("Age in months")
        plt.ylabel("Predicted total bits")
        plt.grid(alpha=0.25)
        plt.legend(title="Fixed value", fontsize=8, title_fontsize=8)
        savefig(fig_dir / filenames[effort_col])


def fit_child_identity_models(frame: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit Model 2 and generate shaded simple supervisor plots."""

    coefficient_rows = []
    prediction_rows = []
    age_grid = np.linspace(frame["age_months"].min(), frame["age_months"].max(), 80)
    child_ids = sorted(frame["child_id"].astype(str).unique())
    for effort_col, effort_label in EFFORTS:
        data = frame.copy()
        data["effort_value"] = data[effort_col]
        result = smf.ols("sum_bits ~ age_months + effort_value + C(child_id)", data=data).fit(
            cov_type="cluster",
            cov_kwds={"groups": data["child_id"].astype(str)},
        )
        coefficient_rows.append(
            {
                "effort_col": effort_col,
                "effort_label": effort_label,
                "age_coef_bits_per_month": float(result.params["age_months"]),
                "age_p": float(result.pvalues["age_months"]),
                "effort_coef_bits_per_unit": float(result.params["effort_value"]),
                "r2": float(result.rsquared),
                "nobs": int(result.nobs),
            }
        )
        fixed_values = [
            ("low", float(data["effort_value"].quantile(0.25))),
            ("median", float(data["effort_value"].quantile(0.50))),
            ("high", float(data["effort_value"].quantile(0.75))),
        ]
        fixed_values.append(("global adjusted trend", float(data["effort_value"].mean())))
        for label, effort_value in fixed_values:
            base = pd.DataFrame(
                {
                    "age_months": age_grid,
                    "effort_value": effort_value,
                    "line_type": "global" if label == "global adjusted trend" else "fixed",
                    "effort_level": label,
                }
            )
            pred_frame = child_average_prediction_summary(result, base, child_ids)
            for pred_row in pred_frame.to_dict("records"):
                prediction_rows.append(
                    {
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "line_type": pred_row["line_type"],
                        "effort_level": pred_row["effort_level"],
                        "effort_value": float(pred_row["effort_value"]),
                        "age_months": float(pred_row["age_months"]),
                        "predicted_sum_bits": float(pred_row["predicted_sum_bits"]),
                        "pred_ci_low": float(pred_row["pred_ci_low"]),
                        "pred_ci_high": float(pred_row["pred_ci_high"]),
                    }
                )
    coefficients = pd.DataFrame(coefficient_rows)
    predictions = pd.DataFrame(prediction_rows)
    coefficients.to_csv(output_dir / "model2_child_identity_coefficients.csv", index=False)
    predictions.to_csv(output_dir / "model2_child_identity_predictions.csv", index=False)
    return coefficients, predictions


def plot_child_identity_predictions(predictions: pd.DataFrame, fig_dir: Path) -> None:
    """Write the five M2 simple plots used by the supervisor-facing report."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    colors = {"low": "#1f77b4", "median": "#ff7f0e", "high": "#2ca02c", "global adjusted trend": "#222222"}
    filenames = {
        "nb_words": "m2_words_fixed_effort_and_global_trend.png",
        "nb_morphemes": "m2_morphemes_fixed_effort_and_global_trend.png",
        "nb_syllables_cmu_or_pkg": "m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png",
        "nb_syllables_pkg": "m2_syllables_pkg_fixed_effort_and_global_trend.png",
        "nb_phonemes": "m2_phonemes_fixed_effort_and_global_trend.png",
    }
    for effort_col, effort_label in EFFORTS:
        panel = predictions[predictions["effort_col"].eq(effort_col)]
        plt.figure(figsize=(8.2, 4.9))
        for level, group in panel.groupby("effort_level", observed=True):
            group = group.sort_values("age_months")
            color = colors.get(level, "gray")
            linewidth = 2.8 if level == "global adjusted trend" else 2.1
            label = (
                "Global adjusted trend"
                if level == "global adjusted trend"
                else f"Fixed {group['effort_value'].iloc[0]:g}"
            )
            if group[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                plt.fill_between(
                    group["age_months"].to_numpy(dtype=float),
                    group["pred_ci_low"].to_numpy(dtype=float),
                    group["pred_ci_high"].to_numpy(dtype=float),
                    color=color,
                    alpha=0.18 if level == "global adjusted trend" else 0.22,
                    linewidth=0,
                )
            plt.plot(group["age_months"], group["predicted_sum_bits"], color=color, linewidth=linewidth, label=label)
            if group[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                plt.plot(
                    group["age_months"],
                    group["pred_ci_low"],
                    color=color,
                    linewidth=1.0,
                    alpha=0.70,
                )
                plt.plot(
                    group["age_months"],
                    group["pred_ci_high"],
                    color=color,
                    linewidth=1.0,
                    alpha=0.70,
                )
        plt.title(f"M2: fixed-effort predictions + 95% fitted-mean CI ({effort_label})")
        plt.xlabel("Age in months")
        plt.ylabel("Predicted total bits")
        plt.grid(alpha=0.22)
        plt.legend(title="Line type", fontsize=8, title_fontsize=8)
        savefig(fig_dir / filenames[effort_col])


def plot_image_grid(image_paths: list[Path], output_path: Path, *, layout: str) -> None:
    if layout == "triptych":
        positions = [
            (0.04, 0.54, 0.44, 0.42),
            (0.52, 0.54, 0.44, 0.42),
            (0.28, 0.06, 0.44, 0.42),
        ]
        figsize = (10.0, 7.0)
    elif layout == "five":
        positions = [
            (0.04, 0.69, 0.44, 0.28),
            (0.52, 0.69, 0.44, 0.28),
            (0.04, 0.37, 0.44, 0.28),
            (0.52, 0.37, 0.44, 0.28),
            (0.28, 0.05, 0.44, 0.28),
        ]
        figsize = (10.5, 11.0)
    else:  # pragma: no cover
        raise ValueError(f"Unknown image grid layout: {layout}")

    fig = plt.figure(figsize=figsize)
    for path, position in zip(image_paths, positions):
        ax = fig.add_axes(position)
        ax.imshow(plt.imread(path))
        ax.axis("off")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_compact_report_grids(fig_dir: Path, m2_fig_dir: Path) -> None:
    plot_image_grid(
        [
            fig_dir / "model0_mlu_words_by_age.png",
            fig_dir / "model0_sum_bits_by_age.png",
            fig_dir / "model0_bits_per_token_by_age.png",
        ],
        fig_dir / "model0_descriptive_compact_grid.png",
        layout="triptych",
    )
    plot_image_grid(
        [
            m2_fig_dir / "m2_words_fixed_effort_and_global_trend.png",
            m2_fig_dir / "m2_morphemes_fixed_effort_and_global_trend.png",
            m2_fig_dir / "m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png",
            m2_fig_dir / "m2_syllables_pkg_fixed_effort_and_global_trend.png",
            m2_fig_dir / "m2_phonemes_fixed_effort_and_global_trend.png",
        ],
        fig_dir / "model2_fixed_effort_compact_grid.png",
        layout="five",
    )


def build(input_csv: Path, output_dir: Path, fig_dir: Path, m2_fig_dir: Path = DEFAULT_M2_FIG_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = load_real_k3(input_csv)
    print(f"[todo-plots] loaded real k3 rows: {len(frame):,}", flush=True)
    frame.to_csv(output_dir / "real_child_k3_model0_model1_rows.csv.gz", index=False)
    summary = summarize_age_bins(frame, output_dir)
    plot_descriptive(summary, fig_dir)
    _, predictions = fit_effort_only_models(frame, output_dir)
    plot_effort_only_predictions(predictions, fig_dir)
    _, m2_predictions = fit_child_identity_models(frame, output_dir)
    plot_child_identity_predictions(m2_predictions, m2_fig_dir)
    build_compact_report_grids(fig_dir, m2_fig_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--m2-fig-dir", type=Path, default=DEFAULT_M2_FIG_DIR)
    args = parser.parse_args()
    build(args.input, args.output_dir, args.fig_dir, args.m2_fig_dir)


if __name__ == "__main__":
    main()
