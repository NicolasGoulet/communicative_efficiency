#!/usr/bin/env python3
"""Build the heldout real-child trajectory prediction report.

This report asks whether PBM-trained Route 1 models predict the real
sum-bits trajectories of three unseen children: Forrester/Ella,
Sachs/Naomi, and MPI-EVA-Manchester/Helen.
"""

from __future__ import annotations

import argparse
import math
import os
import gc
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

from build_route1_corrected_baseline_atlas import (
    EFFORT_SPECS,
    QUESTION_TYPE_ORDER,
    context_effort_row,
    question_type,
    read_route1_rows,
)
from render_markdown_report import render_markdown_file


DEFAULT_PBM_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_HELDOUT_INPUT = Path("results/route1_heldout_real_child_prediction/heldout_scored_utterance_effort_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_heldout_real_child_prediction")
DEFAULT_FIG_DIR = Path("figs/route1_heldout_real_child_prediction")
DEFAULT_DOC_DIR = Path("docs")
DEFAULT_COVERAGE_PBM = Path("results/route1_current_scored_coverage/current_scored_real_child_age_points.csv")

HELDOUT_CHILD_ORDER = ["Forrester/Ella", "Sachs/Naomi", "MPI-EVA-Manchester/Helen"]
PRIMARY_CONTEXTS = ("k0", "k1", "k2", "k3")
PRIMARY_EFFORT_COLS = ("nb_words", "nb_morphemes")
PRIMARY_MODELS = (
    "POP_M1",
    "POP_M3",
    "POP_M4A",
    "POP_M4C",
    "POP_M7",
    "POP_M8",
    "MUND_M1",
    "MUND_M3",
)


@dataclass(frozen=True)
class PredictionModel:
    model_id: str
    label: str
    atlas_analogue: str
    formula: str
    needs_context: bool = False
    needs_parent_context_effort: bool = False
    needs_question_type: bool = False
    uses_mundlak_age: bool = False
    fixed_effort_values: tuple[int, int, int] = (2, 6, 10)


MODEL_LIBRARY: dict[str, PredictionModel] = {
    "POP_M1": PredictionModel(
        "POP_M1",
        "Population age + effort",
        "M1 without child fixed effects",
        "sum_bits ~ age_c + effort_c",
    ),
    "POP_M3": PredictionModel(
        "POP_M3",
        "Population age x effort",
        "M3 without child fixed effects",
        "sum_bits ~ age_c * effort_c",
    ),
    "POP_M4A": PredictionModel(
        "POP_M4A",
        "Population age x effort + parent-context effort",
        "M4a without child fixed effects",
        "sum_bits ~ age_c * effort_c + parent_context_effort_c",
        needs_context=True,
        needs_parent_context_effort=True,
    ),
    "POP_M4C": PredictionModel(
        "POP_M4C",
        "Population age x effort + question type",
        "M4c without child fixed effects",
        "sum_bits ~ age_c * effort_c + C(question_type)",
        needs_context=True,
        needs_question_type=True,
    ),
    "POP_M7": PredictionModel(
        "POP_M7",
        "Population nonlinear age",
        "M7 without child fixed effects",
        "sum_bits ~ age_c + effort_c + I(age_c ** 2)",
    ),
    "POP_M8": PredictionModel(
        "POP_M8",
        "Population nonlinear age x effort",
        "M8 without child fixed effects",
        "sum_bits ~ age_c * effort_c + I(age_c ** 2) + I(age_c ** 2):effort_c",
    ),
    "MUND_M1": PredictionModel(
        "MUND_M1",
        "Mundlak within/between age + effort",
        "child-coverage-adjusted M1-like model",
        "sum_bits ~ age_within_child_c + child_mean_age_c + effort_c",
        uses_mundlak_age=True,
    ),
    "MUND_M3": PredictionModel(
        "MUND_M3",
        "Mundlak within-age x effort",
        "child-coverage-adjusted M3-like model",
        "sum_bits ~ age_within_child_c * effort_c + child_mean_age_c",
        uses_mundlak_age=True,
    ),
}


def effort_label(effort_col: str) -> str:
    for spec in EFFORT_SPECS:
        if spec.effort_col == effort_col:
            return spec.effort_label
    return effort_col


def parent_context_col(effort_col: str) -> str:
    return f"parent_context_{effort_col}"


def relative_to_report(report_path: Path, figure_path: Path) -> str:
    base = report_path if report_path.suffix == "" else report_path.parent
    return os.path.relpath(figure_path.resolve(), start=base.resolve()).replace(os.sep, "/")


def child_key(frame: pd.DataFrame) -> pd.Series:
    return frame["dataset"].astype(str) + "/" + frame["child_id"].astype(str)


def coerce_numeric(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def read_heldout_rows(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)
    if "target_source" not in frame:
        frame["target_source"] = frame["target_variant"].astype(str)
    frame["child_key"] = child_key(frame)
    return frame


def prepare_features(
    frame: pd.DataFrame,
    *,
    context_k: str,
    effort_col: str,
    model: PredictionModel,
    train_centers: dict[str, float] | None = None,
    child_mean_source: pd.Series | None = None,
) -> tuple[pd.DataFrame, dict[str, float], str]:
    """Prepare centered training or heldout prediction rows."""

    data = frame.copy()
    if "target_source" not in data:
        data["target_source"] = data["target_variant"].astype(str)
    data = data[
        data["role"].astype(str).eq("child")
        & data["target_source"].astype(str).eq("real")
        & data["context_k"].astype(str).eq(context_k)
    ].copy()
    if data.empty:
        return data, {}, "no rows"
    pcontext_col = parent_context_col(effort_col)
    needed_parent_cols = [pcontext_col] if model.needs_parent_context_effort else []
    if model.needs_question_type and "question_type" not in data.columns:
        context_series = data.get("context_text", pd.Series("", index=data.index)).fillna("").astype(str)
        data["question_type"] = context_series.map(question_type)
    for col in needed_parent_cols:
        if col not in data.columns:
            context_series = data.get("context_text", pd.Series("", index=data.index)).fillna("").astype(str)
            unique_counts = {text: context_effort_row(text) for text in sorted(context_series.unique())}
            data[col] = context_series.map(lambda text, column=col: unique_counts[text][column])

    numeric_cols = ["sum_bits", "age_months", effort_col]
    if model.needs_parent_context_effort:
        numeric_cols.append(pcontext_col)
    for col in numeric_cols:
        if col not in data:
            data[col] = np.nan
    data = coerce_numeric(data, numeric_cols)
    data["effort_value"] = data[effort_col]
    data["parent_context_effort_value"] = data[pcontext_col] if model.needs_parent_context_effort else 0.0
    required = ["sum_bits", "age_months", "effort_value", "child_id", "dataset"]
    if model.needs_parent_context_effort:
        required.append("parent_context_effort_value")
    if model.needs_question_type:
        required.append("question_type")
    data = data.dropna(subset=required).copy()
    data = data[(data["sum_bits"] > 0) & (data["age_months"] > 0) & (data["effort_value"] > 0)].copy()
    if data.empty:
        return data, {}, "no complete rows"
    if model.needs_context and context_k == "k0":
        return data.iloc[0:0].copy(), {}, "model needs context but context is k0"

    if train_centers is None:
        centers = {
            "age_mean": float(data["age_months"].mean()),
            "effort_mean": float(data["effort_value"].mean()),
            "parent_context_effort_mean": float(data["parent_context_effort_value"].mean())
            if model.needs_parent_context_effort
            else 0.0,
        }
    else:
        centers = train_centers

    data["age_c"] = data["age_months"] - centers["age_mean"]
    data["effort_c"] = data["effort_value"] - centers["effort_mean"]
    data["parent_context_effort_c"] = (
        data["parent_context_effort_value"] - centers["parent_context_effort_mean"]
        if model.needs_parent_context_effort
        else 0.0
    )
    data["child_key"] = child_key(data)
    if child_mean_source is None:
        child_mean = data.groupby("child_key")["age_months"].transform("mean")
    else:
        child_mean_map = child_mean_source.to_dict()
        child_mean = data["child_key"].map(child_mean_map)
    data["child_mean_age"] = child_mean
    data["child_mean_age_c"] = data["child_mean_age"] - centers["age_mean"]
    data["age_within_child_c"] = data["age_months"] - data["child_mean_age"]
    if "question_type" in data:
        data["question_type"] = pd.Categorical(data["question_type"].astype(str), categories=QUESTION_TYPE_ORDER)
    else:
        data["question_type"] = pd.Categorical(["not question"] * len(data), categories=QUESTION_TYPE_ORDER)
    data["effort_col"] = effort_col
    data["effort_label"] = effort_label(effort_col)
    data["context_k"] = context_k
    return data.reset_index(drop=True), centers, ""


def fit_model(train: pd.DataFrame, model: PredictionModel):
    result = smf.ols(model.formula, data=train).fit()
    return result


def predict_frame(result, frame: pd.DataFrame) -> np.ndarray:
    return np.asarray(result.predict(frame), dtype=float)


def row_prediction_summary(frame: pd.DataFrame, predicted: np.ndarray, *, model: PredictionModel, context_k: str, effort_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = frame[
        [
            "dataset",
            "child_id",
            "child_key",
            "session_id",
            "age_months",
            "age_bin",
            "sum_bits",
            "effort_value",
            "context_k",
            "effort_label",
        ]
    ].copy()
    out["predicted_sum_bits"] = predicted
    out["residual"] = out["sum_bits"] - out["predicted_sum_bits"]
    out["model_id"] = model.model_id
    out["model_label"] = model.label
    out["atlas_analogue"] = model.atlas_analogue
    out["effort_col"] = effort_col
    out["context_k"] = context_k
    out["month"] = np.floor(pd.to_numeric(out["age_months"], errors="coerce")).astype("Int64")

    metrics_rows: list[dict[str, object]] = []
    for key, group in out.groupby("child_key", sort=False):
        actual = group["sum_bits"].to_numpy(dtype=float)
        pred = group["predicted_sum_bits"].to_numpy(dtype=float)
        residual = actual - pred
        corr = float(np.corrcoef(actual, pred)[0, 1]) if len(group) > 2 and np.std(actual) > 0 and np.std(pred) > 0 else math.nan
        session = (
            group.groupby("age_months", as_index=False)
            .agg(actual_sum_bits=("sum_bits", "mean"), predicted_sum_bits=("predicted_sum_bits", "mean"))
            .sort_values("age_months")
        )
        actual_slope = slope(session["age_months"], session["actual_sum_bits"])
        predicted_slope = slope(session["age_months"], session["predicted_sum_bits"])
        metrics_rows.append(
            {
                "model_id": model.model_id,
                "model_label": model.label,
                "atlas_analogue": model.atlas_analogue,
                "context_k": context_k,
                "effort_col": effort_col,
                "effort_label": effort_label(effort_col),
                "child_key": key,
                "rows": int(len(group)),
                "age_min": float(group["age_months"].min()),
                "age_max": float(group["age_months"].max()),
                "actual_mean": float(np.mean(actual)),
                "predicted_mean": float(np.mean(pred)),
                "mean_error_actual_minus_predicted": float(np.mean(residual)),
                "mae": float(np.mean(np.abs(residual))),
                "rmse": float(np.sqrt(np.mean(residual**2))),
                "correlation": corr,
                "actual_age_slope": actual_slope,
                "predicted_age_slope": predicted_slope,
                "same_slope_sign": bool(np.sign(actual_slope) == np.sign(predicted_slope))
                if np.isfinite(actual_slope) and np.isfinite(predicted_slope)
                else False,
            }
        )
    metrics = pd.DataFrame(metrics_rows)
    monthly = (
        out.groupby(["model_id", "model_label", "atlas_analogue", "context_k", "effort_col", "effort_label", "child_key", "month"], as_index=False)
        .agg(
            age_months=("age_months", "mean"),
            rows=("sum_bits", "size"),
            actual_sum_bits=("sum_bits", "mean"),
            predicted_sum_bits=("predicted_sum_bits", "mean"),
            residual=("residual", "mean"),
            mean_effort=("effort_value", "mean"),
        )
        .copy()
    )
    return metrics, monthly


def slope(x: pd.Series, y: pd.Series) -> float:
    xvals = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    yvals = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(xvals) & np.isfinite(yvals)
    if mask.sum() < 2 or np.nanstd(xvals[mask]) <= 0:
        return math.nan
    return float(np.polyfit(xvals[mask], yvals[mask], 1)[0])


def fixed_effort_predictions(
    result,
    train: pd.DataFrame,
    heldout: pd.DataFrame,
    *,
    model: PredictionModel,
    context_k: str,
    effort_col: str,
    centers: dict[str, float],
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    modal_question = (
        str(train["question_type"].mode(dropna=True).iloc[0])
        if "question_type" in train and not train["question_type"].dropna().empty
        else "not question"
    )
    child_means = heldout.groupby("child_key")["age_months"].mean().to_dict()
    for child in HELDOUT_CHILD_ORDER:
        child_rows = heldout[heldout["child_key"].eq(child)].copy()
        if child_rows.empty:
            continue
        ages = np.linspace(float(child_rows["age_months"].min()), float(child_rows["age_months"].max()), 80)
        for fixed_value in model.fixed_effort_values:
            base = pd.DataFrame(
                {
                    "age_months": ages,
                    "age_c": ages - centers["age_mean"],
                    "effort_value": fixed_value,
                    "effort_c": fixed_value - centers["effort_mean"],
                    "parent_context_effort_value": centers.get("parent_context_effort_mean", 0.0),
                    "parent_context_effort_c": 0.0,
                    "question_type": pd.Categorical([modal_question] * len(ages), categories=QUESTION_TYPE_ORDER),
                    "child_key": child,
                    "child_mean_age": child_means[child],
                    "child_mean_age_c": child_means[child] - centers["age_mean"],
                    "age_within_child_c": ages - child_means[child],
                }
            )
            pred = predict_frame(result, base)
            base["predicted_sum_bits"] = pred
            base["fixed_effort_value"] = fixed_value
            base["fixed_effort_band"] = effort_band_label(fixed_value)
            base["model_id"] = model.model_id
            base["model_label"] = model.label
            base["context_k"] = context_k
            base["effort_col"] = effort_col
            base["effort_label"] = effort_label(effort_col)
            rows.append(base)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def effort_band_label(value: float) -> str:
    if value <= 4:
        return "1-4"
    if value <= 8:
        return "5-8"
    return "9-12"


def add_effort_band(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["effort_band"] = pd.cut(
        pd.to_numeric(out["effort_value"], errors="coerce"),
        bins=[0, 4, 8, np.inf],
        labels=["1-4", "5-8", "9-12"],
        include_lowest=True,
    )
    return out


def observed_fixed_effort_summary(heldout: pd.DataFrame, *, context_k: str, effort_col: str, model_id: str, model_label: str) -> pd.DataFrame:
    data = heldout[heldout["context_k"].astype(str).eq(context_k)].copy()
    data = coerce_numeric(data, ["sum_bits", "age_months", effort_col])
    data = data[(data["sum_bits"] > 0) & (data["age_months"] > 0) & (data[effort_col] > 0)].copy()
    data["effort_value"] = data[effort_col]
    data["child_key"] = child_key(data)
    data = add_effort_band(data)
    data["month"] = np.floor(data["age_months"]).astype("Int64")
    obs = (
        data.groupby(["child_key", "month", "effort_band"], observed=True, as_index=False)
        .agg(age_months=("age_months", "mean"), actual_sum_bits=("sum_bits", "mean"), rows=("sum_bits", "size"))
        .copy()
    )
    obs["model_id"] = model_id
    obs["model_label"] = model_label
    obs["context_k"] = context_k
    obs["effort_col"] = effort_col
    obs["effort_label"] = effort_label(effort_col)
    return obs


def fit_and_predict(
    *,
    train_all: pd.DataFrame,
    heldout_all: pd.DataFrame,
    contexts: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fit_rows: list[dict[str, object]] = []
    metric_parts: list[pd.DataFrame] = []
    monthly_parts: list[pd.DataFrame] = []
    fixed_parts: list[pd.DataFrame] = []
    observed_fixed_parts: list[pd.DataFrame] = []

    for context_k in contexts:
        for effort_col in effort_cols:
            for model_id in model_ids:
                model = MODEL_LIBRARY[model_id]
                print(f"[fit] {context_k} {effort_col} {model_id}", flush=True)
                if model.needs_context and context_k == "k0":
                    fit_rows.append(
                        {
                            "model_id": model_id,
                            "model_label": model.label,
                            "context_k": context_k,
                            "effort_col": effort_col,
                            "effort_label": effort_label(effort_col),
                            "status": "skipped",
                            "error": "model needs context but context is k0",
                        }
                    )
                    continue
                train, centers, prep_error = prepare_features(
                    train_all,
                    context_k=context_k,
                    effort_col=effort_col,
                    model=model,
                )
                heldout, _, heldout_error = prepare_features(
                    heldout_all,
                    context_k=context_k,
                    effort_col=effort_col,
                    model=model,
                    train_centers=centers or None,
                    child_mean_source=None,
                )
                row = {
                    "model_id": model_id,
                    "model_label": model.label,
                    "atlas_analogue": model.atlas_analogue,
                    "formula": model.formula,
                    "context_k": context_k,
                    "effort_col": effort_col,
                    "effort_label": effort_label(effort_col),
                    "status": "fit",
                    "error": "",
                    "train_rows": int(len(train)),
                    "train_children": int(train["child_key"].nunique()) if "child_key" in train else 0,
                    "heldout_rows": int(len(heldout)),
                    "heldout_children": int(heldout["child_key"].nunique()) if "child_key" in heldout else 0,
                    "age_center": centers.get("age_mean", math.nan) if centers else math.nan,
                    "effort_center": centers.get("effort_mean", math.nan) if centers else math.nan,
                    "parent_context_effort_center": centers.get("parent_context_effort_mean", math.nan) if centers else math.nan,
                    "r2": math.nan,
                }
                if prep_error or heldout_error or train.empty or heldout.empty:
                    row["status"] = "skipped"
                    row["error"] = prep_error or heldout_error or "empty train or heldout"
                    fit_rows.append(row)
                    continue
                try:
                    result = fit_model(train, model)
                    row["r2"] = float(getattr(result, "rsquared", math.nan))
                    predicted = predict_frame(result, heldout)
                    metrics, monthly = row_prediction_summary(heldout, predicted, model=model, context_k=context_k, effort_col=effort_col)
                    fixed = fixed_effort_predictions(
                        result,
                        train,
                        heldout,
                        model=model,
                        context_k=context_k,
                        effort_col=effort_col,
                        centers=centers,
                    )
                    observed_fixed = observed_fixed_effort_summary(
                        heldout_all,
                        context_k=context_k,
                        effort_col=effort_col,
                        model_id=model_id,
                        model_label=model.label,
                    )
                    metric_parts.append(metrics)
                    monthly_parts.append(monthly)
                    fixed_parts.append(fixed)
                    observed_fixed_parts.append(observed_fixed)
                    print(
                        f"[fit-ok] {context_k} {effort_col} {model_id} "
                        f"train={len(train):,} heldout={len(heldout):,} r2={row['r2']:.4f}",
                        flush=True,
                    )
                except Exception as exc:  # pragma: no cover - real-data guard
                    row["status"] = "failed"
                    row["error"] = f"{type(exc).__name__}: {exc}"
                    print(f"[fit-failed] {context_k} {effort_col} {model_id}: {row['error']}", flush=True)
                fit_rows.append(row)
                del train, heldout
                gc.collect()

    fit_summary = pd.DataFrame(fit_rows)
    metrics = pd.concat(metric_parts, ignore_index=True) if metric_parts else pd.DataFrame()
    monthly = pd.concat(monthly_parts, ignore_index=True) if monthly_parts else pd.DataFrame()
    fixed = pd.concat(fixed_parts, ignore_index=True) if fixed_parts else pd.DataFrame()
    observed_fixed = pd.concat(observed_fixed_parts, ignore_index=True) if observed_fixed_parts else pd.DataFrame()
    output_dir.mkdir(parents=True, exist_ok=True)
    fit_summary.to_csv(output_dir / "heldout_prediction_fit_summary.csv", index=False)
    metrics.to_csv(output_dir / "heldout_prediction_metrics.csv", index=False)
    monthly.to_csv(output_dir / "heldout_prediction_monthly.csv.gz", index=False)
    fixed.to_csv(output_dir / "heldout_fixed_effort_prediction_grid.csv.gz", index=False)
    observed_fixed.to_csv(output_dir / "heldout_fixed_effort_observed_monthly.csv.gz", index=False)
    return fit_summary, metrics, monthly, fixed


def coverage_rows(pbm_age_points: pd.DataFrame, heldout: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pbm = pbm_age_points.copy()
    pbm["month"] = pd.to_numeric(pbm["month"], errors="coerce").astype("Int64")
    for dataset, group in pbm.groupby("dataset", sort=True):
        months = sorted(int(m) for m in group["month"].dropna().unique())
        rows.append(
            {
                "row_label": f"PBM corpus: {dataset}",
                "row_kind": "PBM corpus",
                "row_order": len(rows),
                "months": months,
                "n_children": int(group["child_id"].nunique()),
                "n_age_points": int(len(group)),
                "n_utterances": int(group["n_utterances"].sum()),
                "first_age": float(group["age_months"].min()),
                "last_age": float(group["age_months"].max()),
            }
        )
    months = sorted(int(m) for m in pbm["month"].dropna().unique())
    rows.append(
        {
            "row_label": "PBM union: Brown + Manchester + Providence",
            "row_kind": "PBM union",
            "row_order": len(rows),
            "months": months,
            "n_children": int(pbm["child_id"].nunique()),
            "n_age_points": int(len(pbm)),
            "n_utterances": int(pbm["n_utterances"].sum()),
            "first_age": float(pbm["age_months"].min()),
            "last_age": float(pbm["age_months"].max()),
        }
    )

    held = heldout[heldout["context_k"].astype(str).eq("k0")].copy()
    held = coerce_numeric(held, ["age_months", "sum_bits"])
    held["month"] = np.floor(held["age_months"]).astype("Int64")
    held["child_key"] = child_key(held)
    for key in HELDOUT_CHILD_ORDER:
        group = held[held["child_key"].eq(key)].copy()
        months = sorted(int(m) for m in group["month"].dropna().unique())
        rows.append(
            {
                "row_label": f"heldout child: {key}",
                "row_kind": "heldout child",
                "row_order": len(rows),
                "months": months,
                "n_children": 1,
                "n_age_points": int(group["age_months"].nunique()),
                "n_utterances": int(len(group)),
                "first_age": float(group["age_months"].min()),
                "last_age": float(group["age_months"].max()),
            }
        )
    months = sorted(int(m) for m in held["month"].dropna().unique())
    rows.append(
        {
            "row_label": "heldout union: Ella + Naomi + Helen",
            "row_kind": "heldout union",
            "row_order": len(rows),
            "months": months,
            "n_children": int(held["child_key"].nunique()),
            "n_age_points": int(held.groupby("child_key")["age_months"].nunique().sum()),
            "n_utterances": int(len(held)),
            "first_age": float(held["age_months"].min()),
            "last_age": float(held["age_months"].max()),
        }
    )
    return pd.DataFrame(rows)


def plot_coverage(coverage: pd.DataFrame, *, fig_dir: Path) -> Path:
    fig_dir.mkdir(parents=True, exist_ok=True)
    month_min = 6
    month_max = 65
    fig, ax = plt.subplots(figsize=(14, 5.8))
    colors = {
        "PBM corpus": "#5677a4",
        "PBM union": "#1f3f5f",
        "heldout child": "#d17a22",
        "heldout union": "#8f3b16",
    }
    for _, row in coverage.sort_values("row_order").iterrows():
        y = row["row_order"]
        for month in row["months"]:
            ax.barh(y, 0.92, left=month - 0.46, height=0.64, color=colors[row["row_kind"]], alpha=0.9)
        label = f"{row['n_children']} child; {row['n_utterances']:,} utt; {len(row['months'])} months"
        ax.text(month_max + 0.8, y, label, va="center", fontsize=9, color="#334155")
    ax.set_xlim(month_min - 1, month_max + 14)
    ax.set_ylim(-0.8, len(coverage) - 0.2)
    ax.set_yticks(coverage["row_order"])
    ax.set_yticklabels(coverage["row_label"])
    ax.invert_yaxis()
    ax.set_xlabel("Integer child age month covered")
    ax.set_title("Why these heldout children: compact coverage against the scored PBM training universe")
    ax.grid(axis="x", color="#e2e8f0")
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    plt.tight_layout()
    path = fig_dir / "heldout_selection_pbm_corpus_coverage.png"
    plt.savefig(path, dpi=220)
    plt.savefig(path.with_suffix(".pdf"))
    plt.close(fig)
    return path


def plot_prediction_trajectories(monthly: pd.DataFrame, *, fig_dir: Path, context_k: str = "k3", effort_col: str = "nb_words") -> list[Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    model_ids = ["POP_M3", "POP_M4A", "POP_M4C", "MUND_M3"]
    for model_id in model_ids:
        data = monthly[
            monthly["model_id"].eq(model_id)
            & monthly["context_k"].eq(context_k)
            & monthly["effort_col"].eq(effort_col)
        ].copy()
        if data.empty:
            continue
        fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
        for ax, child in zip(axes, HELDOUT_CHILD_ORDER):
            sub = data[data["child_key"].eq(child)].sort_values("age_months")
            ax.plot(sub["age_months"], sub["actual_sum_bits"], color="#111827", linewidth=2.2, label="actual")
            ax.plot(sub["age_months"], sub["predicted_sum_bits"], color="#0f766e", linewidth=2.2, label="PBM prediction")
            ax.fill_between(
                sub["age_months"].to_numpy(dtype=float),
                (sub["predicted_sum_bits"] - sub["residual"].std()).to_numpy(dtype=float),
                (sub["predicted_sum_bits"] + sub["residual"].std()).to_numpy(dtype=float),
                color="#0f766e",
                alpha=0.08,
                linewidth=0,
            )
            ax.set_title(child)
            ax.set_xlabel("Age (months)")
            ax.grid(color="#e5e7eb")
        axes[0].set_ylabel("Mean sum_bits per month")
        axes[0].legend(loc="best")
        label = data["model_label"].iloc[0]
        fig.suptitle(f"Actual vs PBM-predicted heldout trajectories: {label}, {context_k}, Words", y=1.02)
        plt.tight_layout()
        path = fig_dir / f"actual_vs_predicted_{context_k}_{model_id}_{effort_col}.png"
        plt.savefig(path, dpi=220, bbox_inches="tight")
        plt.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
        plt.close(fig)
        outputs.append(path)
    return outputs


def plot_fixed_effort(fixed: pd.DataFrame, output_dir: Path, *, fig_dir: Path, context_k: str = "k3") -> list[Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    observed = pd.read_csv(output_dir / "heldout_fixed_effort_observed_monthly.csv.gz")
    outputs: list[Path] = []
    panels = [
        ("POP_M3", "nb_words"),
        ("POP_M4A", "nb_words"),
        ("MUND_M3", "nb_words"),
        ("POP_M3", "nb_morphemes"),
        ("MUND_M3", "nb_morphemes"),
    ]
    palette = {"1-4": "#2563eb", "5-8": "#d97706", "9-12": "#7c3aed"}
    for model_id, effort_col in panels:
        pred = fixed[
            fixed["model_id"].eq(model_id)
            & fixed["context_k"].eq(context_k)
            & fixed["effort_col"].eq(effort_col)
        ].copy()
        obs = observed[
            observed["model_id"].eq(model_id)
            & observed["context_k"].eq(context_k)
            & observed["effort_col"].eq(effort_col)
        ].copy()
        if pred.empty or obs.empty:
            continue
        fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), sharey=True)
        for ax, child in zip(axes, HELDOUT_CHILD_ORDER):
            child_pred = pred[pred["child_key"].eq(child)].copy()
            child_obs = obs[obs["child_key"].eq(child)].copy()
            for band, band_pred in child_pred.groupby("fixed_effort_band", sort=True):
                ax.plot(
                    band_pred["age_months"],
                    band_pred["predicted_sum_bits"],
                    color=palette.get(str(band), "#334155"),
                    linewidth=2.2,
                    label=f"prediction {band}",
                )
            for band, band_obs in child_obs.groupby("effort_band", observed=True, sort=True):
                band_obs = band_obs[band_obs["rows"] >= 3]
                ax.scatter(
                    band_obs["age_months"],
                    band_obs["actual_sum_bits"],
                    color=palette.get(str(band), "#334155"),
                    edgecolor="white",
                    s=26,
                    alpha=0.58,
                    label=f"actual {band}",
                )
            ax.set_title(child)
            ax.set_xlabel("Age (months)")
            ax.grid(color="#e5e7eb")
        axes[0].set_ylabel("sum_bits")
        handles, labels = axes[0].get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        axes[0].legend(unique.values(), unique.keys(), fontsize=8, loc="best")
        label = pred["model_label"].iloc[0]
        effort = pred["effort_label"].iloc[0]
        fig.suptitle(f"Fixed-effort heldout check: {label}, {context_k}, {effort}", y=1.02)
        plt.tight_layout()
        path = fig_dir / f"fixed_effort_{context_k}_{model_id}_{effort_col}.png"
        plt.savefig(path, dpi=220, bbox_inches="tight")
        plt.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
        plt.close(fig)
        outputs.append(path)
    return outputs


def model_metric_table(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return pd.DataFrame()
    view = metrics[metrics["context_k"].eq("k3") & metrics["effort_col"].eq("nb_words")].copy()
    if view.empty:
        view = metrics.copy()
    out = (
        view.groupby(["model_id", "model_label"], as_index=False)
        .agg(
            mean_mae=("mae", "mean"),
            mean_rmse=("rmse", "mean"),
            mean_corr=("correlation", "mean"),
            slope_sign_matches=("same_slope_sign", "sum"),
            child_rows=("child_key", "nunique"),
        )
        .sort_values(["mean_rmse", "mean_mae"])
    )
    for col in ["mean_mae", "mean_rmse", "mean_corr"]:
        out[col] = out[col].map(lambda value: f"{value:.3f}" if pd.notna(value) else "")
    return out


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 20) -> str:
    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    columns = [str(col) for col in shown.columns]
    rows = shown.astype(object).where(pd.notna(shown), "").astype(str).values.tolist()

    def clean_cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(clean_cell(col) for col in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(clean_cell(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def write_report(
    *,
    doc_path: Path,
    coverage_figure: Path,
    trajectory_figures: Sequence[Path],
    fixed_figures: Sequence[Path],
    fit_summary: pd.DataFrame,
    metrics: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> None:
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    fitted = fit_summary[fit_summary["status"].eq("fit")].copy()
    skipped = fit_summary[fit_summary["status"].ne("fit")].copy()
    metric_table = model_metric_table(metrics)
    lines: list[str] = [
        "# Heldout Real-Child Trajectory Prediction Report",
        "",
        "This is the out-of-child robustness check: can models trained only on the scored PBM universe predict the real `sum_bits` trajectories of three unseen children?",
        "",
        "The heldout children are `Forrester/Ella`, `Sachs/Naomi`, and `MPI-EVA-Manchester/Helen`. They were not part of the scored PBM training universe used for the Route 1 Atlas v2 model fits.",
        "",
        "## 1. Why These Three Children",
        "",
        "We selected the smallest non-PBM set that gives broad month coverage across the child-language age range while staying small enough to score and inspect carefully. The plot below deliberately shows PBM at the corpus level only, then each heldout child and the heldout union.",
        "",
        f"![Heldout coverage]({relative_to_report(doc_path, coverage_figure)})",
        "",
        "Read: the PBM rows show the training/scored universe by corpus; the heldout rows show why Ella, Naomi, and Helen are complementary. Ella covers early through late ages, Naomi fills much of the early/middle trajectory, and Helen densely covers the later months. Their union covers 50 integer months from 12 to 61 months.",
        "",
        "## 2. Prediction Design",
        "",
        "- Training data: PBM real-child scored rows from the Route 1 analysis dataset.",
        "- Test data: heldout real utterances for Ella, Naomi, and Helen, scored on the PC and rsynced locally.",
        "- Outcome: `sum_bits`, total information in the real child utterance.",
        "- Estimator: `statsmodels.formula.api.ols` linear regression.",
        "- Prediction target: population-level out-of-child prediction. `C(child_id)` fixed-effect models are not used for the main heldout prediction because a brand-new child has no fitted child intercept.",
        "- Child adjustment used where possible: Mundlak-style within/between age models, which can predict unseen children because they use the child mean age rather than a child-specific intercept.",
        "- Current predictor boundary: `context_entropy_bits` and response-space entropy are not yet computed for the heldout contexts, so entropy-dependent Atlas models are explicitly withheld from this report.",
        "",
        "Models fit for this report:",
        "",
        markdown_table(
            pd.DataFrame(
                [
                    {
                        "model_id": model.model_id,
                        "model": model.label,
                        "atlas analogue": model.atlas_analogue,
                        "formula": model.formula,
                    }
                    for model in MODEL_LIBRARY.values()
                ]
            ),
            max_rows=20,
        ),
        "",
        "## 3. Overall Heldout Prediction Metrics",
        "",
        "The compact table below summarizes the main k3/word-count comparison across the three children. Lower MAE/RMSE is better; slope-sign matches count how many of the three children have the same actual and predicted developmental direction.",
        "",
        markdown_table(metric_table, max_rows=12),
        "",
        f"Full fit summary: `{output_dir / 'heldout_prediction_fit_summary.csv'}`",
        f"Full metrics: `{output_dir / 'heldout_prediction_metrics.csv'}`",
        "",
        "## 4. Actual vs Predicted Trajectories",
        "",
        "These plots use each child's actual heldout utterances and compare monthly mean actual `sum_bits` to monthly mean PBM-model predictions. This is not fixed-effort yet; it is the row-wise prediction sanity check.",
        "",
    ]
    for path in trajectory_figures:
        title = path.stem.replace("_", " ")
        lines.extend([f"### {title}", "", f"![{title}]({relative_to_report(doc_path, path)})", ""])
    lines.extend(
        [
            "## 5. Fixed-Effort Trajectory Checks",
            "",
            "These are the closest analogue to the Atlas fixed-effort plots. Lines are PBM-trained predictions at fixed effort levels. Points are heldout observed monthly means in the matching effort bands.",
            "",
        ]
    )
    for path in fixed_figures:
        title = path.stem.replace("_", " ")
        lines.extend([f"### {title}", "", f"![{title}]({relative_to_report(doc_path, path)})", ""])
    lines.extend(
        [
            "## 6. Interpretation Boundary",
            "",
            "This report answers the first robustness question: the PBM-trained age/effort/context-size/question-type models can now be compared against real unseen-child trajectories. The honest limitation is that fixed child identity effects cannot be directly transported to new children; the Mundlak variants are the out-of-sample-compatible child-coverage adjustment.",
            "",
            "The next predictor-enrichment step is to compute heldout `context_entropy_bits` and later response-space entropy for the same contexts. Once those are attached, the entropy-dependent M4b/M5/M6/M11-M15 families and Route 2 prediction models can be tested on the same heldout children.",
            "",
            "## Saved Artifacts",
            "",
            "```text",
            str(output_dir / "heldout_scored_utterance_effort_long.csv.gz"),
            str(output_dir / "heldout_prediction_fit_summary.csv"),
            str(output_dir / "heldout_prediction_metrics.csv"),
            str(output_dir / "heldout_prediction_monthly.csv.gz"),
            str(output_dir / "heldout_fixed_effort_prediction_grid.csv.gz"),
            str(output_dir / "heldout_fixed_effort_observed_monthly.csv.gz"),
            str(output_dir / "heldout_selection_coverage_rows.csv"),
            str(fig_dir),
            "```",
            "",
        ]
    )
    if not skipped.empty:
        lines.extend(
            [
                "## Skipped Fits",
                "",
                "Some model/context combinations are intentionally skipped, mostly because context models do not apply to k0.",
                "",
                markdown_table(skipped[["model_id", "context_k", "effort_label", "status", "error"]], max_rows=20),
            "",
        ]
    )
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def render_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Render PDF using a headless browser when available."""

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


def run_report(
    *,
    pbm_input: Path,
    heldout_input: Path,
    coverage_pbm: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_dir: Path,
    contexts: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
) -> dict[str, Path]:
    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("[read] PBM training rows", flush=True)
    train = read_route1_rows(
        pbm_input,
        chunksize=chunksize,
        max_rows=None,
        target_sources=("real",),
        context_ks=contexts,
        roles=("child",),
    )
    train["target_source"] = train.get("target_source", train.get("target_variant", "real")).astype(str)
    train["child_key"] = child_key(train)
    print(f"[read] PBM rows={len(train):,}", flush=True)

    print("[read] heldout rows", flush=True)
    heldout = read_heldout_rows(heldout_input)
    print(f"[read] heldout rows={len(heldout):,}", flush=True)

    coverage = coverage_rows(pd.read_csv(coverage_pbm), heldout)
    coverage.to_csv(output_dir / "heldout_selection_coverage_rows.csv", index=False)
    coverage_figure = plot_coverage(coverage, fig_dir=fig_dir)

    fit_summary, metrics, monthly, fixed = fit_and_predict(
        train_all=train,
        heldout_all=heldout,
        contexts=contexts,
        effort_cols=effort_cols,
        model_ids=model_ids,
        output_dir=output_dir,
    )
    trajectory_figures = plot_prediction_trajectories(monthly, fig_dir=fig_dir)
    fixed_figures = plot_fixed_effort(fixed, output_dir, fig_dir=fig_dir)

    doc_path = doc_dir / "utterance_information_route1_heldout_real_child_prediction_report.md"
    html_path = doc_path.with_suffix(".html")
    embedded_path = doc_path.with_suffix(".embedded.html")
    pdf_path = doc_path.with_suffix(".pdf")
    write_report(
        doc_path=doc_path,
        coverage_figure=coverage_figure,
        trajectory_figures=trajectory_figures,
        fixed_figures=fixed_figures,
        fit_summary=fit_summary,
        metrics=metrics,
        output_dir=output_dir,
        fig_dir=fig_dir,
    )
    render_markdown_file(doc_path, html_path)
    render_markdown_file(doc_path, embedded_path, embed_images=True)
    render_pdf(html_path, pdf_path)
    return {
        "md": doc_path,
        "html": html_path,
        "embedded_html": embedded_path,
        "pdf": pdf_path,
        "coverage": coverage_figure,
        "fit_summary": output_dir / "heldout_prediction_fit_summary.csv",
        "metrics": output_dir / "heldout_prediction_metrics.csv",
    }


def split_csv(value: str) -> list[str]:
    if value == "all":
        return list(PRIMARY_MODELS)
    return [item.strip() for item in value.split(",") if item.strip()]


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pbm-input", type=Path, default=DEFAULT_PBM_INPUT)
    parser.add_argument("--heldout-input", type=Path, default=DEFAULT_HELDOUT_INPUT)
    parser.add_argument("--coverage-pbm", type=Path, default=DEFAULT_COVERAGE_PBM)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--contexts", default=",".join(PRIMARY_CONTEXTS))
    parser.add_argument("--effort-cols", default=",".join(PRIMARY_EFFORT_COLS))
    parser.add_argument("--model-ids", default=",".join(PRIMARY_MODELS))
    parser.add_argument("--chunksize", type=int, default=250_000)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = run_report(
        pbm_input=args.pbm_input,
        heldout_input=args.heldout_input,
        coverage_pbm=args.coverage_pbm,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_dir=args.doc_dir,
        contexts=split_csv(args.contexts),
        effort_cols=split_csv(args.effort_cols),
        model_ids=split_csv(args.model_ids),
        chunksize=args.chunksize,
    )
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
