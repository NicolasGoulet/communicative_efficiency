#!/usr/bin/env python3
"""Fit and report the frozen direct-surprisal replication model suite.

Inputs are child-wide tables created by
``build_direct_surprisal_wide_table.py``. The primary point estimates use
exact-design-cell WLS: utterances with identical child, age, and exact/top-coded
word effort are collapsed to their mean with their row count as the weight.
This preserves the OLS point estimate and cluster score sums while making the
full-79 analysis tractable and auditable.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gaussian


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from render_markdown_report import render_markdown_file


AGE_BINS = [
    "006-023",
    "024-029",
    "030-035",
    "036-041",
    "042-047",
    "048-053",
    "054-059",
    "060-065",
]
WORD_CATEGORIES = [*[str(value) for value in range(1, 12)], "12+"]
PRIMARY_OUTCOMES = {
    "P1_k3_contextual": "real_k3_sum_bits",
    "P2_k0_unconditional": "real_k0_sum_bits",
    "P3_k3_context_gain": "real_context_gain_k3",
}
SECONDARY_OUTCOMES = {
    "S1_k1_contextual": "real_k1_sum_bits",
    "S2_k2_contextual": "real_k2_sum_bits",
    "S3_k1_context_gain": "real_context_gain_k1",
    "S4_k2_context_gain": "real_context_gain_k2",
    "B1_random_minus_real_k3": "random_minus_real_k3_bits",
    "B2_unigram_minus_real_k3": "unigram_minus_real_k3_bits",
    "B3_bigram_minus_real_k3": "bigram_minus_real_k3_bits",
    "B4_trigram_minus_real_k3": "trigram_minus_real_k3_bits",
}
READ_COLUMNS = [
    "scorer_id",
    "dataset",
    "child_id",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_bin",
    "utterance_id",
    "real_nb_words",
    "real_nb_characters",
    "context_available_k1",
    "context_available_k2",
    "context_available_k3",
    "real_k0_sum_bits",
    "real_k1_sum_bits",
    "real_k2_sum_bits",
    "real_k3_sum_bits",
    "real_k0_n_eval_tokens",
    "real_k1_n_eval_tokens",
    "real_k2_n_eval_tokens",
    "real_k3_n_eval_tokens",
    "real_context_gain_k1",
    "real_context_gain_k2",
    "real_context_gain_k3",
    "random_minus_real_k3_bits",
    "unigram_minus_real_k3_bits",
    "bigram_minus_real_k3_bits",
    "trigram_minus_real_k3_bits",
]
NUMERIC_COLUMNS = [
    column
    for column in READ_COLUMNS
    if column
    not in {
        "scorer_id",
        "dataset",
        "child_id",
        "child_key",
        "sample_group",
        "session_id",
        "age_bin",
        "utterance_id",
    }
]


@dataclass(frozen=True)
class FitSpec:
    model_id: str
    outcome: str
    tier: str


def md_table(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> str:
    if columns is not None:
        frame = frame.loc[:, [column for column in columns if column in frame.columns]]
    if frame.empty:
        return "_No rows._"
    display = frame.copy()
    for column in display.columns:
        if pd.api.types.is_numeric_dtype(display[column]):
            display[column] = display[column].map(format_number)
    display = display.fillna("").astype(str)
    lines = [
        "| " + " | ".join(display.columns) + " |",
        "| " + " | ".join(["---"] * len(display.columns)) + " |",
    ]
    for _, row in display.iterrows():
        lines.append(
            "| " + " | ".join(row[column].replace("|", "\\|") for column in display.columns) + " |"
        )
    return "\n".join(lines)


def format_number(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    if not math.isfinite(number):
        return ""
    if number != 0 and abs(number) < 0.001:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def relative(path: Path, report_path: Path) -> str:
    return os.path.relpath(path, start=report_path.parent).replace(os.sep, "/")


def read_wide_table(path: Path) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0, keep_default_na=False).columns
    missing = sorted(set(READ_COLUMNS) - set(header))
    if missing:
        raise ValueError(f"Wide table is missing required columns: {missing}")
    frame = pd.read_csv(
        path,
        usecols=READ_COLUMNS,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["word_count_exact_top12"] = word_category(frame["real_nb_words"])
    frame["age_bin"] = pd.Categorical(frame["age_bin"], categories=AGE_BINS, ordered=True)
    frame["bits_per_word_k3"] = frame["real_k3_sum_bits"] / frame["real_nb_words"].replace(0, np.nan)
    frame["bits_per_word_k0"] = frame["real_k0_sum_bits"] / frame["real_nb_words"].replace(0, np.nan)
    return frame


def word_category(values: pd.Series) -> pd.Categorical:
    numeric = pd.to_numeric(values, errors="coerce")
    labels = numeric.map(
        lambda value: "" if pd.isna(value) or value < 1 else ("12+" if value >= 12 else str(int(value)))
    )
    return pd.Categorical(labels, categories=WORD_CATEGORIES, ordered=True)


def scope_frames(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    scopes: dict[str, pd.DataFrame] = {}
    discovery = frame[frame["sample_group"] == "pbm_discovery"].copy()
    confirmation = frame[frame["sample_group"] == "non_pbm_confirmation"].copy()
    if not discovery.empty:
        scopes["pbm_discovery"] = discovery
    if not confirmation.empty:
        scopes["non_pbm_confirmation"] = confirmation
    if not discovery.empty and not confirmation.empty:
        scopes["all79_descriptive"] = frame.copy()
    return scopes


def eligibility_mask(frame: pd.DataFrame, outcome: str) -> pd.Series:
    mask = (
        frame["age_months"].between(6, 65, inclusive="both")
        & (frame["real_nb_words"] >= 1)
        & frame[outcome].notna()
    )
    # The frozen k0 decomposition keeps initial/no-context turns, whereas all
    # contextual, context-gain, and candidate-gap outcomes require the same
    # genuine k3 context-bearing support as P1.
    if outcome != "real_k0_sum_bits":
        mask &= frame["context_available_k3"].fillna(0).astype(float) > 0
    if outcome == "real_k3_sum_bits":
        mask &= frame["real_k3_n_eval_tokens"].fillna(0) > 0
    elif outcome == "real_k0_sum_bits":
        mask &= frame["real_k0_n_eval_tokens"].fillna(0) > 0
    return mask


def sample_flow(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
    steps: list[dict[str, object]] = []

    def add(step: str, mask: pd.Series) -> None:
        view = frame[mask]
        steps.append(
            {
                "scope": scope,
                "step": step,
                "rows": len(view),
                "children": view["child_key"].nunique(),
                "corpora": view["dataset"].nunique(),
                "sessions": view[["child_key", "session_id"]].drop_duplicates().shape[0],
            }
        )

    all_rows = pd.Series(True, index=frame.index)
    valid_age = frame["age_months"].between(6, 65, inclusive="both")
    valid_words = valid_age & (frame["real_nb_words"] >= 1)
    valid_k3 = valid_words & frame["real_k3_sum_bits"].notna() & (frame["real_k3_n_eval_tokens"] > 0)
    context = valid_k3 & (frame["context_available_k3"] > 0)
    add("source_rows", all_rows)
    add("age_006_065", valid_age)
    add("nonempty_real_target", valid_words)
    add("finite_scored_real_k3", valid_k3)
    add("primary_context_bearing", context)
    return pd.DataFrame(steps)


def collapse_exact_design_cells(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    data = frame[eligibility_mask(frame, outcome)].copy()
    data = data.dropna(subset=[outcome, "age_months", "word_count_exact_top12", "child_key"])
    group_cols = [
        "dataset",
        "child_key",
        "age_months",
        "age_bin",
        "word_count_exact_top12",
    ]
    cells = (
        data.groupby(group_cols, observed=True, dropna=False)[outcome]
        .agg(outcome_mean="mean", row_count="size", outcome_sd="std")
        .reset_index()
    )
    if cells.empty:
        return cells
    weighted_age_mean = float(np.average(cells["age_months"], weights=cells["row_count"]))
    cells["age_c"] = cells["age_months"] - weighted_age_mean
    cells["word_count_exact_top12"] = pd.Categorical(
        cells["word_count_exact_top12"], categories=WORD_CATEGORIES, ordered=True
    )
    return cells


def coefficient_frame(result: object, metadata: Mapping[str, object]) -> pd.DataFrame:
    intervals = result.conf_int()
    rows = []
    for term in result.params.index:
        rows.append(
            {
                **metadata,
                "term": term,
                "estimate": float(result.params[term]),
                "std_error": float(result.bse[term]),
                "ci_low": float(intervals.loc[term, 0]),
                "ci_high": float(intervals.loc[term, 1]),
                "p_value": float(result.pvalues[term]),
            }
        )
    return pd.DataFrame(rows)


def fit_result_row(
    result: object,
    *,
    spec: FitSpec,
    scope: str,
    estimator: str,
    formula: str,
    cells: pd.DataFrame,
    source_rows: int,
    warning_text: str,
) -> dict[str, object]:
    term = "age_c" if "age_c" in result.params.index else "age_within"
    intervals = result.conf_int()
    return {
        "scope": scope,
        "model_id": spec.model_id,
        "tier": spec.tier,
        "outcome": spec.outcome,
        "estimator": estimator,
        "formula": formula,
        "source_rows": source_rows,
        "design_cells": len(cells),
        "children": cells["child_key"].nunique(),
        "corpora": cells["dataset"].nunique(),
        "age_term": term,
        "age_estimate": float(result.params.get(term, np.nan)),
        "age_std_error": float(result.bse.get(term, np.nan)),
        "age_ci_low": float(intervals.loc[term, 0]) if term in intervals.index else np.nan,
        "age_ci_high": float(intervals.loc[term, 1]) if term in intervals.index else np.nan,
        "age_p_value": float(result.pvalues.get(term, np.nan)),
        "r_squared": float(getattr(result, "rsquared", np.nan)),
        "aic": float(getattr(result, "aic", np.nan)),
        "fit_status": "PASS",
        "warnings": warning_text,
    }


def fit_wls(
    cells: pd.DataFrame, spec: FitSpec, scope: str
) -> tuple[object, dict[str, object], pd.DataFrame]:
    formula = "outcome_mean ~ age_c + C(word_count_exact_top12) + C(child_key)"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.wls(formula, data=cells, weights=cells["row_count"]).fit(
            cov_type="cluster",
            cov_kwds={"groups": cells["child_key"], "use_correction": True},
        )
    warning_text = " | ".join(str(item.message) for item in caught)
    metadata = {
        "scope": scope,
        "model_id": spec.model_id,
        "tier": spec.tier,
        "outcome": spec.outcome,
        "estimator": "exact_cell_wls_child_cluster",
        "formula": formula,
    }
    summary = fit_result_row(
        result,
        spec=spec,
        scope=scope,
        estimator="exact_cell_wls_child_cluster",
        formula=formula,
        cells=cells,
        source_rows=int(cells["row_count"].sum()),
        warning_text=warning_text,
    )
    return result, summary, coefficient_frame(result, metadata)


def fit_quadratic_wls(cells: pd.DataFrame, spec: FitSpec, scope: str) -> tuple[dict[str, object], pd.DataFrame]:
    formula = "outcome_mean ~ age_c + I(age_c ** 2) + C(word_count_exact_top12) + C(child_key)"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.wls(formula, data=cells, weights=cells["row_count"]).fit(
            cov_type="cluster",
            cov_kwds={"groups": cells["child_key"], "use_correction": True},
        )
    warning_text = " | ".join(str(item.message) for item in caught)
    metadata = {
        "scope": scope,
        "model_id": f"{spec.model_id}_quadratic",
        "tier": "secondary_nonlinear",
        "outcome": spec.outcome,
        "estimator": "exact_cell_wls_child_cluster",
        "formula": formula,
    }
    summary = fit_result_row(
        result,
        spec=FitSpec(metadata["model_id"], spec.outcome, metadata["tier"]),
        scope=scope,
        estimator=metadata["estimator"],
        formula=formula,
        cells=cells,
        source_rows=int(cells["row_count"].sum()),
        warning_text=warning_text,
    )
    return summary, coefficient_frame(result, metadata)


def fit_age_bin_wls(cells: pd.DataFrame, spec: FitSpec, scope: str) -> tuple[dict[str, object], pd.DataFrame]:
    formula = (
        "outcome_mean ~ C(age_bin, Treatment(reference='006-023')) "
        "+ C(word_count_exact_top12) + C(child_key)"
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.wls(formula, data=cells, weights=cells["row_count"]).fit(
            cov_type="cluster",
            cov_kwds={"groups": cells["child_key"], "use_correction": True},
        )
    warning_text = " | ".join(str(item.message) for item in caught)
    model_id = f"{spec.model_id}_age_bins"
    metadata = {
        "scope": scope,
        "model_id": model_id,
        "tier": "secondary_age_bins",
        "outcome": spec.outcome,
        "estimator": "exact_cell_wls_child_cluster",
        "formula": formula,
    }
    summary = {
        "scope": scope,
        "model_id": model_id,
        "tier": "secondary_age_bins",
        "outcome": spec.outcome,
        "estimator": "exact_cell_wls_child_cluster",
        "formula": formula,
        "source_rows": int(cells["row_count"].sum()),
        "design_cells": len(cells),
        "children": cells["child_key"].nunique(),
        "corpora": cells["dataset"].nunique(),
        "age_term": "joint_age_bin_contrasts",
        "age_estimate": np.nan,
        "age_std_error": np.nan,
        "age_ci_low": np.nan,
        "age_ci_high": np.nan,
        "age_p_value": np.nan,
        "r_squared": float(getattr(result, "rsquared", np.nan)),
        "aic": float(getattr(result, "aic", np.nan)),
        "fit_status": "PASS",
        "warnings": warning_text,
    }
    return summary, coefficient_frame(result, metadata)


def fit_mundlak_wls(cells: pd.DataFrame, spec: FitSpec, scope: str) -> tuple[dict[str, object], pd.DataFrame]:
    data = cells.copy()
    child_age = (
        data.assign(weighted_age=data["age_months"] * data["row_count"])
        .groupby("child_key", observed=True)
        .agg(weighted_age=("weighted_age", "sum"), weight=("row_count", "sum"))
    )
    child_age["age_between"] = child_age["weighted_age"] / child_age["weight"]
    data = data.join(child_age["age_between"], on="child_key")
    data["age_within"] = data["age_months"] - data["age_between"]
    grand = float(np.average(data["age_between"], weights=data["row_count"]))
    data["age_between"] = data["age_between"] - grand
    formula = "outcome_mean ~ age_within + age_between + C(word_count_exact_top12) + C(dataset)"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.wls(formula, data=data, weights=data["row_count"]).fit(
            cov_type="cluster",
            cov_kwds={"groups": data["child_key"], "use_correction": True},
        )
    warning_text = " | ".join(str(item.message) for item in caught)
    metadata = {
        "scope": scope,
        "model_id": f"{spec.model_id}_mundlak",
        "tier": "estimator_sensitivity",
        "outcome": spec.outcome,
        "estimator": "mundlak_wls_child_cluster",
        "formula": formula,
    }
    summary = fit_result_row(
        result,
        spec=FitSpec(metadata["model_id"], spec.outcome, metadata["tier"]),
        scope=scope,
        estimator=metadata["estimator"],
        formula=formula,
        cells=data,
        source_rows=int(data["row_count"].sum()),
        warning_text=warning_text,
    )
    return summary, coefficient_frame(result, metadata)


def fit_gee(cells: pd.DataFrame, spec: FitSpec, scope: str) -> tuple[dict[str, object], pd.DataFrame]:
    formula = "outcome_mean ~ age_c + C(word_count_exact_top12)"
    metadata = {
        "scope": scope,
        "model_id": f"{spec.model_id}_gee",
        "tier": "estimator_sensitivity",
        "outcome": spec.outcome,
        "estimator": "exact_cell_gee_child_cluster",
        "formula": formula,
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.gee(
            formula,
            groups="child_key",
            data=cells,
            weights=cells["row_count"],
            family=Gaussian(),
            cov_struct=Exchangeable(),
        ).fit()
        # Access covariance-derived properties while the warning recorder is
        # active; Statsmodels may defer numerical warnings until bse/conf_int.
        summary = fit_result_row(
            result,
            spec=FitSpec(metadata["model_id"], spec.outcome, metadata["tier"]),
            scope=scope,
            estimator=metadata["estimator"],
            formula=formula,
            cells=cells,
            source_rows=int(cells["row_count"].sum()),
            warning_text="",
        )
        coefficients = coefficient_frame(result, metadata)
    summary["warnings"] = " | ".join(str(item.message) for item in caught)
    return summary, coefficients


def prediction_grid(
    result: object,
    cells: pd.DataFrame,
    *,
    spec: FitSpec,
    scope: str,
    points: int = 60,
) -> pd.DataFrame:
    ages = np.linspace(float(cells["age_months"].min()), float(cells["age_months"].max()), points)
    age_center = float(np.average(cells["age_months"], weights=cells["row_count"]))
    children = sorted(cells["child_key"].unique())
    rows: list[dict[str, object]] = []
    for word_category_value in ["1", "2", "4", "6", "10", "12+"]:
        if word_category_value not in set(cells["word_count_exact_top12"].astype(str)):
            continue
        for age in ages:
            new = pd.DataFrame(
                {
                    "age_c": age - age_center,
                    "word_count_exact_top12": pd.Categorical(
                        [word_category_value] * len(children),
                        categories=WORD_CATEGORIES,
                        ordered=True,
                    ),
                    "child_key": children,
                }
            )
            values = np.asarray(result.predict(new), dtype=float)
            rows.append(
                {
                    "scope": scope,
                    "model_id": spec.model_id,
                    "outcome": spec.outcome,
                    "age_months": age,
                    "word_count_exact_top12": word_category_value,
                    "predicted_mean": float(np.mean(values)),
                    "predicted_child_sd": float(np.std(values, ddof=1)) if len(values) > 1 else np.nan,
                    "standardized_children": len(children),
                }
            )
    return pd.DataFrame(rows)


def word_effect(result: object, category: str) -> float:
    if category == "1":
        return 0.0
    return float(result.params.get(f"C(word_count_exact_top12)[T.{category}]", 0.0))


def build_child_trajectories(
    frame: pd.DataFrame,
    scope: str,
    primary_results: Mapping[str, object],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    needed = frame[eligibility_mask(frame, "real_k3_sum_bits")].copy()
    for outcome in ["real_k3_sum_bits", "real_k0_sum_bits", "real_context_gain_k3"]:
        result = primary_results[outcome]
        reference = word_effect(result, "2")
        effects = needed["word_count_exact_top12"].astype(str).map(
            lambda category: word_effect(result, category)
        )
        needed[f"{outcome}_adjusted_2_words"] = needed[outcome] - effects + reference

    group_cols = ["scorer_id", "dataset", "child_id", "child_key", "session_id", "age_months", "age_bin"]
    trajectories = (
        needed.groupby(group_cols, observed=True, dropna=False)
        .agg(
            utterances=("utterance_id", "size"),
            mean_words=("real_nb_words", "mean"),
            raw_k3_bits=("real_k3_sum_bits", "mean"),
            adjusted_k3_bits_2_words=("real_k3_sum_bits_adjusted_2_words", "mean"),
            raw_k0_bits=("real_k0_sum_bits", "mean"),
            adjusted_k0_bits_2_words=("real_k0_sum_bits_adjusted_2_words", "mean"),
            raw_context_gain_k3=("real_context_gain_k3", "mean"),
            adjusted_context_gain_k3_2_words=("real_context_gain_k3_adjusted_2_words", "mean"),
        )
        .reset_index()
    )
    trajectories.insert(1, "scope", scope)
    slopes = child_slope_summary(trajectories)
    return trajectories, slopes


def weighted_slope(x: np.ndarray, y: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    design = np.column_stack([np.ones(len(x)), x])
    root_weights = np.sqrt(weights)
    beta, *_ = np.linalg.lstsq(design * root_weights[:, None], y * root_weights, rcond=None)
    fitted = design @ beta
    residual = y - fitted
    total = np.average((y - np.average(y, weights=weights)) ** 2, weights=weights)
    unexplained = np.average(residual**2, weights=weights)
    r_squared = 1 - unexplained / total if total > 0 else np.nan
    return float(beta[1]), float(r_squared)


def child_slope_summary(trajectories: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    outcomes = [
        "adjusted_k3_bits_2_words",
        "adjusted_k0_bits_2_words",
        "adjusted_context_gain_k3_2_words",
    ]
    for child_key, group in trajectories.groupby("child_key", observed=True):
        ages = pd.to_numeric(group["age_months"], errors="coerce")
        distinct_ages = ages.nunique()
        age_span = float(ages.max() - ages.min()) if distinct_ages else np.nan
        supported = distinct_ages >= 3 and age_span >= 6 and int(group["utterances"].sum()) >= 100
        base = {
            "scope": group["scope"].iloc[0],
            "scorer_id": group["scorer_id"].iloc[0],
            "dataset": group["dataset"].iloc[0],
            "child_id": group["child_id"].iloc[0],
            "child_key": child_key,
            "trajectory_points": len(group),
            "distinct_ages": distinct_ages,
            "age_min": float(ages.min()),
            "age_max": float(ages.max()),
            "age_span": age_span,
            "utterances": int(group["utterances"].sum()),
            "slope_supported": int(supported),
        }
        for outcome in outcomes:
            data = group[["age_months", "utterances", outcome]].dropna()
            if supported and len(data) >= 3:
                slope, r_squared = weighted_slope(
                    data["age_months"].to_numpy(float),
                    data[outcome].to_numpy(float),
                    data["utterances"].to_numpy(float),
                )
            else:
                slope, r_squared = np.nan, np.nan
            base[f"{outcome}_slope_per_month"] = slope
            base[f"{outcome}_r_squared"] = r_squared
        rows.append(base)
    return pd.DataFrame(rows).sort_values(["dataset", "child_id"]).reset_index(drop=True)


def child_fe_crossproducts(
    cells: pd.DataFrame,
    *,
    outcome_column: str = "outcome_mean",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return per-child sufficient statistics after removing child means.

    The target coefficient is from a weighted regression on age plus word-count
    indicators with a separate intercept for every child. Weighted demeaning
    removes those intercepts exactly, allowing thousands of cluster-bootstrap
    fits without repeatedly constructing a large dummy-variable matrix.
    """

    word_dummies = pd.get_dummies(
        pd.Categorical(
            cells["word_count_exact_top12"], categories=WORD_CATEGORIES, ordered=True
        ),
        prefix="word",
        dtype=float,
    )
    reference_column = "word_1"
    if reference_column in word_dummies:
        word_dummies = word_dummies.drop(columns=reference_column)
    design = np.column_stack(
        [cells["age_months"].to_numpy(float), word_dummies.to_numpy(float)]
    )
    outcome = cells[outcome_column].to_numpy(float)
    weights = cells["row_count"].to_numpy(float)
    child_values = cells["child_key"].astype(str).to_numpy()
    children = np.array(sorted(pd.unique(child_values)))
    matrices = []
    vectors = []
    for child in children:
        take = child_values == child
        child_weights = weights[take]
        child_design = design[take]
        child_outcome = outcome[take]
        design_centered = child_design - np.average(
            child_design, axis=0, weights=child_weights
        )
        outcome_centered = child_outcome - np.average(child_outcome, weights=child_weights)
        matrices.append(design_centered.T @ (child_weights[:, None] * design_centered))
        vectors.append(design_centered.T @ (child_weights * outcome_centered))
    return children, np.stack(matrices), np.stack(vectors)


def influence_age_slopes(cells: pd.DataFrame, *, spec: FitSpec, scope: str) -> pd.DataFrame:
    children, matrices, vectors = child_fe_crossproducts(cells)
    full_matrix = matrices.sum(axis=0)
    full_vector = vectors.sum(axis=0)
    observed = float(np.linalg.lstsq(full_matrix, full_vector, rcond=None)[0][0])
    child_to_corpus = (
        cells[["child_key", "dataset"]].drop_duplicates().set_index("child_key")["dataset"].to_dict()
    )
    rows = []

    def add(drop_level: str, drop_id: str, keep: np.ndarray) -> None:
        if int(keep.sum()) < 2:
            return
        estimate = float(
            np.linalg.lstsq(matrices[keep].sum(axis=0), vectors[keep].sum(axis=0), rcond=None)[0][0]
        )
        rows.append(
            {
                "scope": scope,
                "model_id": spec.model_id,
                "outcome": spec.outcome,
                "drop_level": drop_level,
                "drop_id": drop_id,
                "remaining_children": int(keep.sum()),
                "observed_age_estimate": observed,
                "leave_out_age_estimate": estimate,
                "change_from_observed": estimate - observed,
            }
        )

    for index, child in enumerate(children):
        keep = np.ones(len(children), dtype=bool)
        keep[index] = False
        add("child", str(child), keep)
    corpora = sorted(set(child_to_corpus.values()))
    for corpus in corpora:
        keep = np.array([child_to_corpus[child] != corpus for child in children], dtype=bool)
        add("corpus", str(corpus), keep)
    return pd.DataFrame(rows)


def bootstrap_age_slopes(
    cells: pd.DataFrame,
    *,
    spec: FitSpec,
    scope: str,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    if reps <= 0:
        return pd.DataFrame()
    children, child_matrices, child_vectors = child_fe_crossproducts(cells)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for rep in range(reps):
        sampled_indices = rng.integers(0, len(children), size=len(children))
        try:
            matrix = child_matrices[sampled_indices].sum(axis=0)
            vector = child_vectors[sampled_indices].sum(axis=0)
            estimate = float(np.linalg.lstsq(matrix, vector, rcond=None)[0][0])
            status = "PASS"
            problem = ""
        except Exception as exc:  # pragma: no cover - production audit path
            estimate = np.nan
            status = "FAIL"
            problem = f"{type(exc).__name__}: {exc}"
        rows.append(
            {
                "scope": scope,
                "model_id": spec.model_id,
                "outcome": spec.outcome,
                "replicate": rep,
                "seed": seed,
                "age_estimate": estimate,
                "status": status,
                "problem": problem,
            }
        )
    return pd.DataFrame(rows)


def bootstrap_summary(draws: pd.DataFrame) -> pd.DataFrame:
    if draws.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in draws.groupby(["scope", "model_id", "outcome"], observed=True):
        values = group.loc[group["status"] == "PASS", "age_estimate"].dropna().to_numpy(float)
        rows.append(
            {
                "scope": keys[0],
                "model_id": keys[1],
                "outcome": keys[2],
                "requested_reps": len(group),
                "successful_reps": len(values),
                "bootstrap_mean": float(np.mean(values)) if len(values) else np.nan,
                "bootstrap_se": float(np.std(values, ddof=1)) if len(values) > 1 else np.nan,
                "bootstrap_ci_low": float(np.quantile(values, 0.025)) if len(values) else np.nan,
                "bootstrap_ci_high": float(np.quantile(values, 0.975)) if len(values) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def protocol_result(row: pd.Series) -> str:
    """Label frozen directional outcomes without selecting on significance."""

    if row.get("fit_status") != "PASS":
        return "not_evaluable"
    if row.get("model_id") not in PRIMARY_OUTCOMES:
        return "secondary_no_decision_rule"
    if row.get("model_id") == "P2_k0_unconditional":
        return "decomposition_no_directional_rule"
    estimate = pd.to_numeric(pd.Series([row.get("age_estimate")]), errors="coerce").iloc[0]
    low = pd.to_numeric(pd.Series([row.get("age_ci_low")]), errors="coerce").iloc[0]
    high = pd.to_numeric(pd.Series([row.get("age_ci_high")]), errors="coerce").iloc[0]
    if not np.isfinite(estimate) or not np.isfinite(low) or not np.isfinite(high):
        return "not_evaluable"
    expected_sign = -1 if row.get("model_id") == "P1_k3_contextual" else 1
    direction_matches = np.sign(estimate) == expected_sign
    excludes_zero = low > 0 or high < 0
    if direction_matches and excludes_zero:
        if row.get("scope") == "non_pbm_confirmation":
            return "confirmation_direction_and_interval_pass"
        return "expected_direction_interval_excludes_zero"
    if direction_matches:
        return "expected_direction_interval_includes_zero"
    if excludes_zero:
        return "contrary_direction_interval_excludes_zero"
    return "contrary_or_zero_direction_interval_includes_zero"


def safe_slug(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def plot_population_predictions(predictions: pd.DataFrame, output: Path, title: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5), constrained_layout=True)
    model_order = ["P1_k3_contextual", "P2_k0_unconditional", "P3_k3_context_gain"]
    for ax, model_id in zip(axes, model_order):
        view = predictions[predictions["model_id"] == model_id]
        for word, group in view.groupby("word_count_exact_top12", observed=True):
            ax.plot(group["age_months"], group["predicted_mean"], label=f"{word} words")
        ax.axhline(0, color="#777777", linewidth=0.7, alpha=0.5)
        ax.set_title(model_id.replace("_", " "))
        ax.set_xlabel("Child age (months)")
        ax.set_ylabel("Predicted bits")
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=min(6, len(labels)), frameon=False)
    fig.suptitle(title, fontsize=14)
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def plot_child_profile(group: pd.DataFrame, slope_row: pd.Series, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    panels = [
        ("adjusted_k3_bits_2_words", "Contextual surprisal (k3), adjusted to 2 words"),
        ("adjusted_k0_bits_2_words", "Unconditional surprisal (k0), adjusted to 2 words"),
        ("adjusted_context_gain_k3_2_words", "Context gain (k0 - k3), adjusted to 2 words"),
        ("mean_words", "Observed mean lexical words"),
    ]
    ordered = group.sort_values("age_months")
    sizes = np.clip(np.sqrt(ordered["utterances"].to_numpy(float)) * 5, 18, 180)
    for ax, (column, label) in zip(axes.ravel(), panels):
        ax.scatter(ordered["age_months"], ordered[column], s=sizes, alpha=0.7, color="#2f6f73")
        if slope_row.get("slope_supported", 0) and column != "mean_words":
            data = ordered[["age_months", "utterances", column]].dropna()
            if len(data) >= 3:
                design = np.column_stack([np.ones(len(data)), data["age_months"]])
                root_w = np.sqrt(data["utterances"].to_numpy(float))
                beta, *_ = np.linalg.lstsq(
                    design * root_w[:, None], data[column].to_numpy(float) * root_w, rcond=None
                )
                age_grid = np.linspace(data["age_months"].min(), data["age_months"].max(), 60)
                ax.plot(age_grid, beta[0] + beta[1] * age_grid, color="#b3483e", linewidth=2)
        ax.set_xlabel("Age (months)")
        ax.set_ylabel(label)
        ax.grid(alpha=0.18)
    fig.suptitle(
        f"{group['dataset'].iloc[0]}/{group['child_id'].iloc[0]} — "
        f"{int(group['utterances'].sum()):,} utterances",
        fontsize=14,
    )
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def build_child_profile_plots(
    trajectories: pd.DataFrame,
    slopes: pd.DataFrame,
    fig_dir: Path,
    scope: str,
) -> pd.DataFrame:
    rows = []
    slope_lookup = slopes.set_index("child_key") if not slopes.empty else pd.DataFrame()
    for child_key, group in trajectories.groupby("child_key", observed=True):
        slope_row = slope_lookup.loc[child_key] if child_key in slope_lookup.index else pd.Series(dtype=object)
        output = fig_dir / scope / "children" / f"{safe_slug(child_key)}.png"
        plot_child_profile(group, slope_row, output)
        rows.append(
            {
                "scope": scope,
                "dataset": group["dataset"].iloc[0],
                "child_id": group["child_id"].iloc[0],
                "child_key": child_key,
                "plot": str(output),
                "trajectory_points": len(group),
                "utterances": int(group["utterances"].sum()),
                "slope_supported": int(slope_row.get("slope_supported", 0)),
            }
        )
    return pd.DataFrame(rows).sort_values(["dataset", "child_id"]).reset_index(drop=True)


def build_report(
    *,
    scorer_label: str,
    input_wide: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    sample_flows: pd.DataFrame,
    summaries: pd.DataFrame,
    coefficients: pd.DataFrame,
    bootstrap: pd.DataFrame,
    influence: pd.DataFrame,
    slopes: pd.DataFrame,
    profile_audit: pd.DataFrame,
    population_plots: Mapping[str, Path],
) -> None:
    lines = [
        f"# {scorer_label}: Direct-Surprisal Replication",
        "",
        "This report implements the frozen 2026-07-21 direct-surprisal protocol. "
        "A negative contextual-surprisal age coefficient means greater scorer predictability "
        "at the same exact/top-coded lexical word effort; it is not, by itself, proof of a "
        "normative efficiency optimum.",
        "",
        "## Input And Sample Flow",
        "",
        f"Input wide table: `{input_wide}`",
        "",
        md_table(sample_flows),
        "",
        "## Frozen Primary Results",
        "",
        md_table(
            summaries[
                summaries["model_id"].isin(PRIMARY_OUTCOMES)
                & (summaries["estimator"] == "exact_cell_wls_child_cluster")
            ],
            [
                "scope",
                "model_id",
                "source_rows",
                "children",
                "corpora",
                "age_estimate",
                "age_ci_low",
                "age_ci_high",
                "age_p_value",
                "protocol_result",
                "fit_status",
            ],
        ),
        "",
        "Context gain is `sum_bits_k0 - sum_bits_k3`; positive values mean context made the "
        "observed target more probable under this scorer.",
        "",
    ]
    if not bootstrap.empty:
        lines.extend(["## Child Bootstrap", "", md_table(bootstrap), ""])
    age_bin_contrasts = coefficients[
        coefficients["model_id"].str.endswith("_age_bins", na=False)
        & coefficients["term"].str.contains("C(age_bin", regex=False, na=False)
    ]
    lines.extend(
        [
            "## Frozen Age-Bin Contrasts",
            "",
            "Contrasts use `006-023` as the reference at fixed exact/top-coded lexical "
            "word effort with child fixed effects and child-clustered covariance. They "
            "do not by themselves establish a sustained developmental onset.",
            "",
            md_table(
                age_bin_contrasts,
                ["scope", "model_id", "term", "estimate", "ci_low", "ci_high", "p_value"],
            ),
            "",
        ]
    )
    lines.extend(["## Fixed-Effort Population Lines", ""])
    for scope, path in population_plots.items():
        lines.extend([f"### {scope}", "", f"![{scope} population predictions]({relative(path, report_md)})", ""])
    lines.extend(
        [
            "## Estimator And Secondary-Outcome Audit",
            "",
            md_table(
                summaries,
                [
                    "scope",
                    "model_id",
                    "tier",
                    "estimator",
                    "age_estimate",
                    "age_ci_low",
                    "age_ci_high",
                    "age_p_value",
                    "fit_status",
                    "warnings",
                ],
            ),
            "",
            "## Leave-One-Child And Leave-One-Corpus Influence",
            "",
            md_table(influence),
            "",
            "## Individual Child Trajectories",
            "",
            "Point size reflects the number of utterances in the child-session-age cell. "
            "Adjusted outcomes remove the fitted exact/top-coded word-count effect and put "
            "every observation on the two-word reference scale. A child line is drawn only "
            "when the support rule is met (at least three distinct ages, six months of span, "
            "and 100 utterances).",
            "",
            md_table(
                slopes,
                [
                    "scope",
                    "dataset",
                    "child_id",
                    "distinct_ages",
                    "age_span",
                    "utterances",
                    "slope_supported",
                    "adjusted_k3_bits_2_words_slope_per_month",
                    "adjusted_context_gain_k3_2_words_slope_per_month",
                ],
            ),
            "",
        ]
    )
    if profile_audit.empty:
        lines.extend(["_No child profiles were produced because a primary fit failed._", ""])
    else:
        for scope, scope_rows in profile_audit.groupby("scope", observed=True):
            lines.extend([f"### {scope}", ""])
            for dataset, dataset_rows in scope_rows.groupby("dataset", observed=True):
                lines.extend([f"#### {dataset}", ""])
                for row in dataset_rows.itertuples():
                    path = Path(row.plot)
                    lines.extend(
                        [
                            f"##### {row.child_key}",
                            "",
                            f"![{row.child_key} trajectory]({relative(path, report_md)})",
                            "",
                        ]
                    )
    lines.extend(
        [
            "## Interpretation Boundary",
            "",
            "PBM results are discovery/scorer-robustness results. A pooled 79-child estimate "
            "is descriptive. Only the separately reported non-PBM estimate is the frozen "
            "sample confirmation. Generated n-gram candidates are not same-meaning "
            "alternatives, and caretaker trajectories reflect input adaptation.",
            "",
            "## Saved Artifacts",
            "",
            f"- Model summaries: `{output_dir / 'model_summaries.csv'}`",
            f"- Coefficients: `{output_dir / 'coefficients_long.csv'}`",
            f"- Prediction grid: `{output_dir / 'prediction_grid.csv'}`",
            f"- Child trajectories: `{output_dir / 'child_age_session_trajectories.csv.gz'}`",
            f"- Child slopes: `{output_dir / 'child_slope_summary.csv'}`",
            f"- Leave-one-cluster-out estimates: `{output_dir / 'leave_one_cluster_out.csv'}`",
            f"- Child profile audit: `{output_dir / 'child_profile_audit.csv'}`",
        ]
    )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(report_md, report_html, title=f"{scorer_label}: Direct-Surprisal Replication")


def run_suite(
    *,
    input_wide: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    scorer_label: str,
    bootstrap_reps: int = 0,
    bootstrap_seed: int = 20260721,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_wide_table(input_wide)
    scopes = scope_frames(frame)
    if not scopes:
        raise ValueError("No PBM discovery or non-PBM confirmation rows found")

    fit_specs = [
        *[FitSpec(model_id, outcome, "primary") for model_id, outcome in PRIMARY_OUTCOMES.items()],
        *[FitSpec(model_id, outcome, "secondary") for model_id, outcome in SECONDARY_OUTCOMES.items()],
    ]
    flow_frames = []
    summary_rows: list[dict[str, object]] = []
    coefficient_frames: list[pd.DataFrame] = []
    prediction_frames: list[pd.DataFrame] = []
    trajectory_frames: list[pd.DataFrame] = []
    slope_frames: list[pd.DataFrame] = []
    bootstrap_frames: list[pd.DataFrame] = []
    influence_frames: list[pd.DataFrame] = []
    profile_frames: list[pd.DataFrame] = []
    population_plots: dict[str, Path] = {}

    for scope, scoped in scopes.items():
        flow_frames.append(sample_flow(scoped, scope))
        primary_results: dict[str, object] = {}
        scope_predictions = []
        for spec in fit_specs:
            cells = collapse_exact_design_cells(scoped, spec.outcome)
            if cells.empty or cells["child_key"].nunique() < 2:
                summary_rows.append(
                    {
                        "scope": scope,
                        "model_id": spec.model_id,
                        "tier": spec.tier,
                        "outcome": spec.outcome,
                        "estimator": "exact_cell_wls_child_cluster",
                        "formula": "",
                        "source_rows": 0,
                        "design_cells": 0,
                        "children": cells["child_key"].nunique() if not cells.empty else 0,
                        "corpora": cells["dataset"].nunique() if not cells.empty else 0,
                        "fit_status": "SKIP_INSUFFICIENT_CLUSTERS",
                    }
                )
                continue
            try:
                result, summary, coefficients = fit_wls(cells, spec, scope)
                summary_rows.append(summary)
                coefficient_frames.append(coefficients)
                if spec.model_id in PRIMARY_OUTCOMES:
                    primary_results[spec.outcome] = result
                    predictions = prediction_grid(result, cells, spec=spec, scope=scope)
                    prediction_frames.append(predictions)
                    scope_predictions.append(predictions)
                    influence_frames.append(influence_age_slopes(cells, spec=spec, scope=scope))
                    age_bin_summary, age_bin_coefficients = fit_age_bin_wls(cells, spec, scope)
                    summary_rows.append(age_bin_summary)
                    coefficient_frames.append(age_bin_coefficients)
                if spec.model_id in {"P1_k3_contextual", "P3_k3_context_gain"}:
                    quadratic_summary, quadratic_coefficients = fit_quadratic_wls(cells, spec, scope)
                    summary_rows.append(quadratic_summary)
                    coefficient_frames.append(quadratic_coefficients)
                    mundlak_summary, mundlak_coefficients = fit_mundlak_wls(cells, spec, scope)
                    summary_rows.append(mundlak_summary)
                    coefficient_frames.append(mundlak_coefficients)
                    gee_summary, gee_coefficients = fit_gee(cells, spec, scope)
                    summary_rows.append(gee_summary)
                    coefficient_frames.append(gee_coefficients)
                    if bootstrap_reps:
                        bootstrap_frames.append(
                            bootstrap_age_slopes(
                                cells,
                                spec=spec,
                                scope=scope,
                                reps=bootstrap_reps,
                                seed=bootstrap_seed + len(bootstrap_frames),
                            )
                        )
            except Exception as exc:
                summary_rows.append(
                    {
                        "scope": scope,
                        "model_id": spec.model_id,
                        "tier": spec.tier,
                        "outcome": spec.outcome,
                        "estimator": "exact_cell_wls_child_cluster",
                        "formula": "",
                        "source_rows": int(cells["row_count"].sum()),
                        "design_cells": len(cells),
                        "children": cells["child_key"].nunique(),
                        "corpora": cells["dataset"].nunique(),
                        "fit_status": "FAIL",
                        "warnings": f"{type(exc).__name__}: {exc}",
                    }
                )

        if set(PRIMARY_OUTCOMES.values()).issubset(primary_results):
            trajectories, slopes = build_child_trajectories(scoped, scope, primary_results)
            trajectory_frames.append(trajectories)
            slope_frames.append(slopes)
            profiles = build_child_profile_plots(trajectories, slopes, fig_dir, scope)
            profile_frames.append(profiles)
        if scope_predictions:
            scope_prediction_frame = pd.concat(scope_predictions, ignore_index=True)
            output = fig_dir / scope / "population_fixed_effort_lines.png"
            plot_population_predictions(
                scope_prediction_frame,
                output,
                f"{scorer_label}: {scope} fixed-effort trajectories",
            )
            population_plots[scope] = output

    flows = pd.concat(flow_frames, ignore_index=True)
    summaries = pd.DataFrame(summary_rows)
    summaries["protocol_result"] = summaries.apply(protocol_result, axis=1)
    coefficients = pd.concat(coefficient_frames, ignore_index=True) if coefficient_frames else pd.DataFrame()
    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    trajectories = pd.concat(trajectory_frames, ignore_index=True) if trajectory_frames else pd.DataFrame()
    slopes = pd.concat(slope_frames, ignore_index=True) if slope_frames else pd.DataFrame()
    bootstrap_draws = pd.concat(bootstrap_frames, ignore_index=True) if bootstrap_frames else pd.DataFrame()
    bootstrap_summaries = bootstrap_summary(bootstrap_draws)
    influence = pd.concat(influence_frames, ignore_index=True) if influence_frames else pd.DataFrame()
    profile_audit = pd.concat(profile_frames, ignore_index=True) if profile_frames else pd.DataFrame()

    flows.to_csv(output_dir / "sample_flow.csv", index=False)
    summaries.to_csv(output_dir / "model_summaries.csv", index=False)
    coefficients.to_csv(output_dir / "coefficients_long.csv", index=False)
    predictions.to_csv(output_dir / "prediction_grid.csv", index=False)
    trajectories.to_csv(output_dir / "child_age_session_trajectories.csv.gz", index=False)
    slopes.to_csv(output_dir / "child_slope_summary.csv", index=False)
    bootstrap_draws.to_csv(output_dir / "child_bootstrap_draws.csv.gz", index=False)
    bootstrap_summaries.to_csv(output_dir / "child_bootstrap_summary.csv", index=False)
    influence.to_csv(output_dir / "leave_one_cluster_out.csv", index=False)
    profile_audit.to_csv(output_dir / "child_profile_audit.csv", index=False)

    audit = {
        "input_wide": str(input_wide),
        "scorer_label": scorer_label,
        "source_rows": len(frame),
        "scopes": {scope: len(scoped) for scope, scoped in scopes.items()},
        "model_attempts": len(summaries),
        "model_failures": int((summaries["fit_status"] == "FAIL").sum()),
        "trajectory_rows": len(trajectories),
        "child_profiles": len(profile_audit),
        "bootstrap_reps": bootstrap_reps,
        "protocol": "docs/direct_surprisal_replication_protocol_2026-07-21.md",
    }
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    build_report(
        scorer_label=scorer_label,
        input_wide=input_wide,
        output_dir=output_dir,
        fig_dir=fig_dir,
        report_md=report_md,
        report_html=report_html,
        sample_flows=flows,
        summaries=summaries,
        coefficients=coefficients,
        bootstrap=bootstrap_summaries,
        influence=influence,
        slopes=slopes,
        profile_audit=profile_audit,
        population_plots=population_plots,
    )
    return audit


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-wide", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fig-dir", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-html", type=Path, required=True)
    parser.add_argument("--scorer-label", required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=0)
    parser.add_argument("--bootstrap-seed", type=int, default=20260721)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    audit = run_suite(
        input_wide=args.input_wide,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
        scorer_label=args.scorer_label,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
