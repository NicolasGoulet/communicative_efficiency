#!/usr/bin/env python3
"""Run restartable direct-surprisal datasets, models, plots, and reports.

The expensive stages are intentionally separate:

``datasets``
    Read a scorer-wide table once and save compact exact-design cells,
    trajectory inputs, coverage, and descriptive summaries.
``models``
    Fit models only from the prepared design cells. No source-wide table or
    plotting code is touched.
``plots``
    Render population and child figures only from saved model/summary files.
``report``
    Render a short plot-led report and child gallery without fitting models or
    redrawing figures.

``all`` runs the four stages in order. Every stage writes a manifest so a long
fit can be audited and resumed without rebuilding upstream products.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import warnings
from dataclasses import asdict
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from build_direct_surprisal_model_suite import (
    AGE_BINS,
    PRIMARY_OUTCOMES,
    SECONDARY_OUTCOMES,
    WORD_CATEGORIES,
    FitSpec,
    bootstrap_age_slopes,
    bootstrap_summary,
    build_child_profile_plots,
    child_fe_crossproducts,
    child_slope_summary,
    coefficient_frame,
    collapse_exact_design_cells,
    eligibility_mask,
    fit_age_bin_wls,
    fit_gee,
    fit_mundlak_wls,
    fit_quadratic_wls,
    fit_result_row,
    fit_wls,
    influence_age_slopes,
    prediction_grid,
    protocol_result,
    read_wide_table,
    relative,
    sample_flow,
    scope_frames,
    word_category,
)
from render_markdown_report import render_markdown_file


PIPELINE_VERSION = "2026-07-21.modular-v1"
SCOPE_LABELS = {
    "pbm_discovery": "PBM discovery (21 children)",
    "non_pbm_confirmation": "Non-PBM confirmation (58 children)",
    "all79_descriptive": "All 79 children (descriptive)",
}
PRIMARY_LABELS = {
    "P1_k3_contextual": "Contextual predictability",
    "P2_k0_unconditional": "Unconditional form predictability",
    "P3_k3_context_gain": "Context support",
}
CHILD_SPECS = [
    *[FitSpec(model_id, outcome, "primary") for model_id, outcome in PRIMARY_OUTCOMES.items()],
    *[FitSpec(model_id, outcome, "secondary") for model_id, outcome in SECONDARY_OUTCOMES.items()],
]
CARETAKER_SPECS = [
    FitSpec("C1_caretaker_k3_contextual", "real_k3_sum_bits", "caretaker_input"),
    FitSpec("C2_caretaker_k0_unconditional", "real_k0_sum_bits", "caretaker_input"),
    FitSpec("C3_caretaker_k3_context_gain", "real_context_gain_k3", "caretaker_input"),
]
BOOTSTRAP_MODEL_IDS = {
    "P1_k3_contextual",
    "P3_k3_context_gain",
    "B1_random_minus_real_k3",
    "B2_unigram_minus_real_k3",
    "B3_bigram_minus_real_k3",
    "B4_trigram_minus_real_k3",
}
MIXED_MODEL_IDS = {"P1_k3_contextual", "P3_k3_context_gain"}


def atomic_csv(frame: pd.DataFrame, path: Path, *, compression: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".tmp.gz" if compression == "gzip" else ".tmp"
    temporary = path.with_name(path.name + suffix)
    frame.to_csv(temporary, index=False, compression=compression)
    os.replace(temporary, path)


def atomic_json(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def file_identity(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def safe_slug(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def design_cell_path(prepared_dir: Path, role: str, scope: str, model_id: str) -> Path:
    return prepared_dir / "design_cells" / role / scope / f"{safe_slug(model_id)}.csv.gz"


def prepare_trajectory_input(frame: pd.DataFrame, scope: str, *, role: str) -> pd.DataFrame:
    eligible = frame[eligibility_mask(frame, "real_k3_sum_bits")].copy()
    group_cols = [
        "scorer_id",
        "dataset",
        "child_id",
        "child_key",
        "session_id",
        "age_months",
        "age_bin",
        "word_count_exact_top12",
    ]
    outcome_cols = [
        "real_k3_sum_bits",
        "real_k0_sum_bits",
        "real_context_gain_k3",
        "real_nb_words",
    ]
    result = (
        eligible.groupby(group_cols, observed=True, dropna=False)[outcome_cols]
        .agg(["mean", "size"])
        .reset_index()
    )
    result.columns = [
        column if isinstance(column, str) else "_".join(part for part in column if part)
        for column in result.columns
    ]
    # Grouped ``size`` is identical across the outcome columns; retain one.
    result = result.rename(
        columns={
            "real_k3_sum_bits_mean": "raw_k3_bits",
            "real_k0_sum_bits_mean": "raw_k0_bits",
            "real_context_gain_k3_mean": "raw_context_gain_k3",
            "real_nb_words_mean": "mean_words",
            "real_k3_sum_bits_size": "utterances",
        }
    )
    result = result.drop(
        columns=[column for column in result if column.endswith("_size") and column != "utterances"]
    )
    result.insert(1, "role", role)
    result.insert(2, "scope", scope)
    return result


def descriptive_summaries(frame: pd.DataFrame, scope: str, *, role: str) -> pd.DataFrame:
    outcomes = {
        "contextual_k3_bits": "real_k3_sum_bits",
        "unconditional_k0_bits": "real_k0_sum_bits",
        "context_gain_k3": "real_context_gain_k3",
        "lexical_words": "real_nb_words",
    }
    rows: list[dict[str, object]] = []
    for label, column in outcomes.items():
        for age_bin, group in frame.groupby("age_bin", observed=True):
            values = pd.to_numeric(group[column], errors="coerce").dropna().to_numpy(float)
            if not len(values):
                continue
            rows.append(
                {
                    "role": role,
                    "scope": scope,
                    "age_bin": str(age_bin),
                    "outcome": label,
                    "rows": len(values),
                    "mean": float(np.mean(values)),
                    "median": float(np.median(values)),
                    "q10": float(np.quantile(values, 0.10)),
                    "q90": float(np.quantile(values, 0.90)),
                }
            )
    return pd.DataFrame(rows)


def coverage_summary(frame: pd.DataFrame, scope: str, *, role: str) -> pd.DataFrame:
    grouped = (
        frame.groupby(["dataset", "child_id", "child_key"], observed=True)
        .agg(
            rows=("utterance_id", "size"),
            sessions=("session_id", "nunique"),
            distinct_ages=("age_months", "nunique"),
            age_min=("age_months", "min"),
            age_max=("age_months", "max"),
        )
        .reset_index()
    )
    grouped["age_span"] = grouped["age_max"] - grouped["age_min"]
    grouped.insert(0, "scope", scope)
    grouped.insert(0, "role", role)
    return grouped


def read_caretaker_wide(path: Path) -> pd.DataFrame:
    columns = [
        "scorer_id",
        "dataset",
        "child_id",
        "child_key",
        "sample_group",
        "session_id",
        "age_months",
        "age_bin",
        "utterance_id",
        "nb_words",
        "nb_characters",
        "context_available_k1",
        "context_available_k2",
        "context_available_k3",
        "k0_sum_bits",
        "k1_sum_bits",
        "k2_sum_bits",
        "k3_sum_bits",
        "k0_n_eval_tokens",
        "k1_n_eval_tokens",
        "k2_n_eval_tokens",
        "k3_n_eval_tokens",
        "context_gain_k1",
        "context_gain_k2",
        "context_gain_k3",
    ]
    frame = pd.read_csv(path, usecols=columns, low_memory=False)
    rename = {
        "nb_words": "real_nb_words",
        "nb_characters": "real_nb_characters",
        "k0_sum_bits": "real_k0_sum_bits",
        "k1_sum_bits": "real_k1_sum_bits",
        "k2_sum_bits": "real_k2_sum_bits",
        "k3_sum_bits": "real_k3_sum_bits",
        "k0_n_eval_tokens": "real_k0_n_eval_tokens",
        "k1_n_eval_tokens": "real_k1_n_eval_tokens",
        "k2_n_eval_tokens": "real_k2_n_eval_tokens",
        "k3_n_eval_tokens": "real_k3_n_eval_tokens",
        "context_gain_k1": "real_context_gain_k1",
        "context_gain_k2": "real_context_gain_k2",
        "context_gain_k3": "real_context_gain_k3",
    }
    frame = frame.rename(columns=rename)
    numeric = [
        column
        for column in frame
        if column.startswith("real_") or column.startswith("context_available") or column == "age_months"
    ]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["age_bin"] = pd.Categorical(frame["age_bin"], categories=AGE_BINS, ordered=True)
    frame["word_count_exact_top12"] = word_category(frame["real_nb_words"])
    return frame


def prepare_role(
    frame: pd.DataFrame,
    *,
    role: str,
    specs: Sequence[FitSpec],
    prepared_dir: Path,
) -> dict[str, object]:
    scopes = scope_frames(frame)
    flow_frames: list[pd.DataFrame] = []
    trajectory_frames: list[pd.DataFrame] = []
    descriptive_frames: list[pd.DataFrame] = []
    coverage_frames: list[pd.DataFrame] = []
    cell_manifest: list[dict[str, object]] = []
    for scope, scoped in scopes.items():
        flow = sample_flow(scoped, scope)
        flow.insert(0, "role", role)
        flow_frames.append(flow)
        trajectory_frames.append(prepare_trajectory_input(scoped, scope, role=role))
        descriptive_frames.append(descriptive_summaries(scoped, scope, role=role))
        coverage_frames.append(coverage_summary(scoped, scope, role=role))
        for spec in specs:
            cells = collapse_exact_design_cells(scoped, spec.outcome)
            path = design_cell_path(prepared_dir, role, scope, spec.model_id)
            atomic_csv(cells, path, compression="gzip")
            cell_manifest.append(
                {
                    "role": role,
                    "scope": scope,
                    **asdict(spec),
                    "path": str(path),
                    "source_rows": int(cells["row_count"].sum()) if not cells.empty else 0,
                    "design_cells": len(cells),
                    "children": int(cells["child_key"].nunique()) if not cells.empty else 0,
                    "corpora": int(cells["dataset"].nunique()) if not cells.empty else 0,
                }
            )
    return {
        "scopes": {scope: len(scoped) for scope, scoped in scopes.items()},
        "flow": pd.concat(flow_frames, ignore_index=True) if flow_frames else pd.DataFrame(),
        "trajectory": pd.concat(trajectory_frames, ignore_index=True) if trajectory_frames else pd.DataFrame(),
        "descriptive": pd.concat(descriptive_frames, ignore_index=True) if descriptive_frames else pd.DataFrame(),
        "coverage": pd.concat(coverage_frames, ignore_index=True) if coverage_frames else pd.DataFrame(),
        "cells": pd.DataFrame(cell_manifest),
    }


def run_dataset_stage(
    *,
    input_wide: Path,
    caretaker_wide: Path | None,
    prepared_dir: Path,
    scorer_label: str,
) -> dict[str, object]:
    prepared_dir.mkdir(parents=True, exist_ok=True)
    child = read_wide_table(input_wide)
    child_products = prepare_role(
        child,
        role="child",
        specs=CHILD_SPECS,
        prepared_dir=prepared_dir,
    )
    products = [child_products]
    caretaker_identity: dict[str, object] | None = None
    if caretaker_wide is not None:
        caretaker = read_caretaker_wide(caretaker_wide)
        products.append(
            prepare_role(
                caretaker,
                role="caretaker",
                specs=CARETAKER_SPECS,
                prepared_dir=prepared_dir,
            )
        )
        caretaker_identity = file_identity(caretaker_wide)

    for key, filename in [
        ("flow", "sample_flow.csv"),
        ("descriptive", "descriptive_age_bin_summary.csv"),
        ("coverage", "child_coverage.csv"),
        ("cells", "design_cell_manifest.csv"),
    ]:
        frames = [product[key] for product in products if not product[key].empty]
        atomic_csv(pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(), prepared_dir / filename)
    trajectories = [product["trajectory"] for product in products if not product["trajectory"].empty]
    atomic_csv(
        pd.concat(trajectories, ignore_index=True) if trajectories else pd.DataFrame(),
        prepared_dir / "trajectory_input.csv.gz",
        compression="gzip",
    )
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "stage": "datasets",
        "scorer_label": scorer_label,
        "child_input": file_identity(input_wide),
        "caretaker_input": caretaker_identity,
        "child_scopes": child_products["scopes"],
        "caretaker_scopes": products[1]["scopes"] if len(products) > 1 else {},
        "design_cell_files": int(sum(len(product["cells"]) for product in products)),
        "status": "COMPLETE",
    }
    atomic_json(manifest, prepared_dir / "dataset_manifest.json")
    return manifest


def read_cells(path: Path) -> pd.DataFrame:
    cells = pd.read_csv(path)
    if "age_bin" in cells:
        cells["age_bin"] = pd.Categorical(cells["age_bin"], categories=AGE_BINS, ordered=True)
    if "word_count_exact_top12" in cells:
        cells["word_count_exact_top12"] = pd.Categorical(
            cells["word_count_exact_top12"].astype(str),
            categories=WORD_CATEGORIES,
            ordered=True,
        )
    return cells


def fit_mixed_sensitivity(
    cells: pd.DataFrame,
    spec: FitSpec,
    scope: str,
    *,
    random_age_slope: bool,
) -> tuple[dict[str, object], pd.DataFrame]:
    data = cells.copy()
    data["word_count_exact_top12"] = data["word_count_exact_top12"].cat.remove_unused_categories()
    re_formula = "~age_c" if random_age_slope else "1"
    suffix = "mixed_random_age" if random_age_slope else "mixed_random_intercept"
    model_id = f"{spec.model_id}_{suffix}"
    formula = "outcome_mean ~ age_c + C(word_count_exact_top12)"
    metadata = {
        "scope": scope,
        "model_id": model_id,
        "tier": "estimator_sensitivity",
        "outcome": spec.outcome,
        "estimator": suffix,
        "formula": formula,
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = smf.mixedlm(
            formula,
            data=data,
            groups=data["child_key"],
            re_formula=re_formula,
        )
        result = model.fit(reml=False, method="lbfgs", maxiter=500, disp=False)
        coefficients = coefficient_frame(result, metadata)
    intervals = result.conf_int()
    warning_text = " | ".join(str(item.message) for item in caught)
    converged = bool(getattr(result, "converged", False))
    if not converged:
        fit_status = "NONCONVERGED"
    elif "singular" in warning_text.lower() or "boundary of the parameter space" in warning_text.lower():
        fit_status = "SINGULAR"
    else:
        fit_status = "PASS"
    summary = {
        "scope": scope,
        "model_id": model_id,
        "tier": "estimator_sensitivity",
        "outcome": spec.outcome,
        "estimator": suffix,
        "formula": formula,
        "source_rows": int(data["row_count"].sum()),
        "design_cells": len(data),
        "children": data["child_key"].nunique(),
        "corpora": data["dataset"].nunique(),
        "age_term": "age_c",
        "age_estimate": float(result.params.get("age_c", np.nan)),
        "age_std_error": float(result.bse.get("age_c", np.nan)),
        "age_ci_low": float(intervals.loc["age_c", 0]) if "age_c" in intervals.index else np.nan,
        "age_ci_high": float(intervals.loc["age_c", 1]) if "age_c" in intervals.index else np.nan,
        "age_p_value": float(result.pvalues.get("age_c", np.nan)),
        "r_squared": np.nan,
        "aic": float(getattr(result, "aic", np.nan)),
        "fit_status": fit_status,
        "warnings": warning_text,
        "weighting_note": "unweighted exact child-age-word design cells",
    }
    return summary, coefficients


def fit_linear_effort_sensitivity(
    cells: pd.DataFrame, spec: FitSpec, scope: str
) -> tuple[dict[str, object], pd.DataFrame]:
    data = cells.copy()
    data["word_count_top12_numeric"] = data["word_count_exact_top12"].astype(str).replace("12+", "12").astype(float)
    formula = "outcome_mean ~ age_c + word_count_top12_numeric + C(child_key)"
    model_id = f"{spec.model_id}_linear_word_effort"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.wls(formula, data=data, weights=data["row_count"]).fit(
            cov_type="cluster",
            cov_kwds={"groups": data["child_key"], "use_correction": True},
        )
    metadata = {
        "scope": scope,
        "model_id": model_id,
        "tier": "effort_sensitivity",
        "outcome": spec.outcome,
        "estimator": "linear_top12_word_wls_child_cluster",
        "formula": formula,
    }
    summary = fit_result_row(
        result,
        spec=FitSpec(model_id, spec.outcome, "effort_sensitivity"),
        scope=scope,
        estimator=metadata["estimator"],
        formula=formula,
        cells=data,
        source_rows=int(data["row_count"].sum()),
        warning_text=" | ".join(str(item.message) for item in caught),
    )
    return summary, coefficient_frame(result, metadata)


def fit_tail_trim_sensitivity(
    cells: pd.DataFrame, spec: FitSpec, scope: str
) -> tuple[dict[str, object], pd.DataFrame]:
    values = cells["outcome_mean"].to_numpy(float)
    weights = cells["row_count"].to_numpy(float)
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order]) / weights.sum()
    low = values[order][np.searchsorted(cumulative, 0.005)]
    high = values[order][min(np.searchsorted(cumulative, 0.995), len(values) - 1)]
    trimmed = cells[cells["outcome_mean"].between(low, high, inclusive="both")].copy()
    trimmed_spec = FitSpec(f"{spec.model_id}_tail_trim_0_5pct", spec.outcome, "tail_sensitivity")
    result, summary, coefficients = fit_wls(trimmed, trimmed_spec, scope)
    summary["trim_low"] = low
    summary["trim_high"] = high
    return summary, coefficients


def cluster_bootstrap_slopes(
    cells: pd.DataFrame,
    *,
    spec: FitSpec,
    scope: str,
    cluster_level: str,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    if reps <= 0:
        return pd.DataFrame()
    children, matrices, vectors = child_fe_crossproducts(cells)
    child_meta = cells[["child_key", "dataset"]].drop_duplicates().set_index("child_key")
    if cluster_level == "child":
        labels = children
        member_indices = {str(label): np.array([index]) for index, label in enumerate(children)}
    elif cluster_level == "corpus":
        labels = np.array(sorted(child_meta["dataset"].astype(str).unique()))
        member_indices = {
            str(label): np.flatnonzero(
                np.array([str(child_meta.loc[child, "dataset"]) for child in children]) == str(label)
            )
            for label in labels
        }
    else:
        raise ValueError(f"Unknown cluster level: {cluster_level}")
    rng = np.random.default_rng(seed)
    rows = []
    for replicate in range(reps):
        sampled = rng.choice(labels, size=len(labels), replace=True)
        indices = np.concatenate([member_indices[str(label)] for label in sampled])
        matrix = matrices[indices].sum(axis=0)
        vector = vectors[indices].sum(axis=0)
        estimate = float(np.linalg.lstsq(matrix, vector, rcond=None)[0][0])
        rows.append(
            {
                "scope": scope,
                "model_id": spec.model_id,
                "outcome": spec.outcome,
                "cluster_level": cluster_level,
                "replicate": replicate,
                "seed": seed,
                "age_estimate": estimate,
                "status": "PASS",
            }
        )
    return pd.DataFrame(rows)


def permuted_age_slopes(
    cells: pd.DataFrame,
    *,
    spec: FitSpec,
    scope: str,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    if reps <= 0:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    child_indices = {
        child: indices.to_numpy()
        for child, indices in cells.groupby("child_key", observed=True).groups.items()
    }
    rows = []
    for replicate in range(reps):
        permuted = cells.copy()
        ages = permuted["age_months"].to_numpy(float).copy()
        for indices in child_indices.values():
            ages[indices] = rng.permutation(ages[indices])
        permuted["age_months"] = ages
        _, matrices, vectors = child_fe_crossproducts(permuted)
        estimate = float(np.linalg.lstsq(matrices.sum(axis=0), vectors.sum(axis=0), rcond=None)[0][0])
        rows.append(
            {
                "scope": scope,
                "model_id": spec.model_id,
                "outcome": spec.outcome,
                "replicate": replicate,
                "seed": seed,
                "age_estimate": estimate,
                "status": "PASS",
            }
        )
    return pd.DataFrame(rows)


def word_effect_from_coefficients(coefficients: pd.DataFrame, category: str) -> float:
    if category == "1":
        return 0.0
    term = f"C(word_count_exact_top12)[T.{category}]"
    match = coefficients[coefficients["term"].astype(str).eq(term)]
    return float(match["estimate"].iloc[0]) if not match.empty else 0.0


def build_trajectories_from_prepared(
    trajectory_input: pd.DataFrame,
    coefficients: pd.DataFrame,
    *,
    role: str,
    scope: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = trajectory_input[
        trajectory_input["role"].eq(role) & trajectory_input["scope"].eq(scope)
    ].copy()
    if data.empty:
        return pd.DataFrame(), pd.DataFrame()
    mapping = {
        "P1_k3_contextual" if role == "child" else "C1_caretaker_k3_contextual": (
            "raw_k3_bits",
            "adjusted_k3_bits_2_words",
        ),
        "P2_k0_unconditional" if role == "child" else "C2_caretaker_k0_unconditional": (
            "raw_k0_bits",
            "adjusted_k0_bits_2_words",
        ),
        "P3_k3_context_gain" if role == "child" else "C3_caretaker_k3_context_gain": (
            "raw_context_gain_k3",
            "adjusted_context_gain_k3_2_words",
        ),
    }
    for model_id, (raw, adjusted) in mapping.items():
        coef = coefficients[
            coefficients["scope"].eq(scope)
            & coefficients["model_id"].eq(model_id)
            & coefficients["estimator"].eq("exact_cell_wls_child_cluster")
        ]
        reference = word_effect_from_coefficients(coef, "2")
        effects = data["word_count_exact_top12"].astype(str).map(
            lambda category: word_effect_from_coefficients(coef, category)
        )
        data[adjusted] = data[raw] - effects + reference
    group_cols = [
        "scorer_id",
        "role",
        "scope",
        "dataset",
        "child_id",
        "child_key",
        "session_id",
        "age_months",
        "age_bin",
    ]
    value_cols = [
        "mean_words",
        "raw_k3_bits",
        "adjusted_k3_bits_2_words",
        "raw_k0_bits",
        "adjusted_k0_bits_2_words",
        "raw_context_gain_k3",
        "adjusted_context_gain_k3_2_words",
    ]
    rows = []
    for keys, group in data.groupby(group_cols, observed=True, dropna=False):
        weights = group["utterances"].to_numpy(float)
        row = dict(zip(group_cols, keys))
        row["utterances"] = int(weights.sum())
        for column in value_cols:
            values = pd.to_numeric(group[column], errors="coerce")
            valid = values.notna().to_numpy()
            row[column] = float(np.average(values[valid], weights=weights[valid])) if valid.any() else np.nan
        rows.append(row)
    trajectories = pd.DataFrame(rows)
    slopes = child_slope_summary(trajectories) if role == "child" else pd.DataFrame()
    return trajectories, slopes


def failed_summary(spec: FitSpec, scope: str, estimator: str, cells: pd.DataFrame, exc: Exception) -> dict[str, object]:
    return {
        "scope": scope,
        "model_id": spec.model_id,
        "tier": spec.tier,
        "outcome": spec.outcome,
        "estimator": estimator,
        "formula": "",
        "source_rows": int(cells["row_count"].sum()) if not cells.empty else 0,
        "design_cells": len(cells),
        "children": cells["child_key"].nunique() if not cells.empty else 0,
        "corpora": cells["dataset"].nunique() if not cells.empty else 0,
        "fit_status": "FAIL",
        "warnings": f"{type(exc).__name__}: {exc}",
    }


def run_model_stage(
    *,
    prepared_dir: Path,
    model_dir: Path,
    bootstrap_reps: int,
    permutation_reps: int,
    seed: int,
    include_mixed: bool,
) -> dict[str, object]:
    dataset_manifest = json.loads((prepared_dir / "dataset_manifest.json").read_text())
    cell_manifest = pd.read_csv(prepared_dir / "design_cell_manifest.csv")
    model_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    coef_frames: list[pd.DataFrame] = []
    prediction_frames: list[pd.DataFrame] = []
    influence_frames: list[pd.DataFrame] = []
    child_bootstrap_frames: list[pd.DataFrame] = []
    corpus_bootstrap_frames: list[pd.DataFrame] = []
    permutation_frames: list[pd.DataFrame] = []

    spec_lookup = {spec.model_id: spec for spec in [*CHILD_SPECS, *CARETAKER_SPECS]}
    for index, row in cell_manifest.iterrows():
        role = str(row["role"])
        scope = str(row["scope"])
        spec = spec_lookup[str(row["model_id"])]
        cells = read_cells(Path(row["path"]))
        if cells.empty or cells["child_key"].nunique() < 2:
            summaries.append(failed_summary(spec, scope, "exact_cell_wls_child_cluster", cells, ValueError("insufficient clusters")))
            continue
        try:
            result, summary, coef = fit_wls(cells, spec, scope)
            summary["role"] = role
            coef["role"] = role
            summaries.append(summary)
            coef_frames.append(coef)
            if spec.model_id in PRIMARY_OUTCOMES or spec.model_id.startswith("C"):
                age_summary, age_coef = fit_age_bin_wls(cells, spec, scope)
                age_summary["role"] = role
                age_coef["role"] = role
                summaries.append(age_summary)
                coef_frames.append(age_coef)
                prediction_frames.append(prediction_grid(result, cells, spec=spec, scope=scope).assign(role=role))
            if role == "child" and spec.model_id in {*PRIMARY_OUTCOMES, *SECONDARY_OUTCOMES}:
                influence_frames.append(influence_age_slopes(cells, spec=spec, scope=scope).assign(role=role))
            if role == "child" and spec.model_id in MIXED_MODEL_IDS:
                for fitter, estimator in [
                    (fit_quadratic_wls, "quadratic"),
                    (fit_mundlak_wls, "mundlak"),
                    (fit_gee, "gee"),
                    (fit_linear_effort_sensitivity, "linear_word_effort"),
                    (fit_tail_trim_sensitivity, "tail_trim"),
                ]:
                    try:
                        extra_summary, extra_coef = fitter(cells, spec, scope)
                        extra_summary["role"] = role
                        extra_coef["role"] = role
                        summaries.append(extra_summary)
                        coef_frames.append(extra_coef)
                    except Exception as exc:
                        summaries.append(failed_summary(spec, scope, estimator, cells, exc) | {"role": role})
                if include_mixed:
                    for random_slope in [False, True]:
                        estimator = "mixed_random_age" if random_slope else "mixed_random_intercept"
                        try:
                            extra_summary, extra_coef = fit_mixed_sensitivity(
                                cells, spec, scope, random_age_slope=random_slope
                            )
                            extra_summary["role"] = role
                            extra_coef["role"] = role
                            summaries.append(extra_summary)
                            coef_frames.append(extra_coef)
                        except Exception as exc:
                            summaries.append(failed_summary(spec, scope, estimator, cells, exc) | {"role": role})
                corpus_bootstrap_frames.append(
                    cluster_bootstrap_slopes(
                        cells,
                        spec=spec,
                        scope=scope,
                        cluster_level="corpus",
                        reps=bootstrap_reps,
                        seed=seed + index * 17 + 5,
                    ).assign(role=role)
                )
                permutation_frames.append(
                    permuted_age_slopes(
                        cells,
                        spec=spec,
                        scope=scope,
                        reps=permutation_reps,
                        seed=seed + index * 17 + 9,
                    ).assign(role=role)
                )
            if role == "child" and spec.model_id in BOOTSTRAP_MODEL_IDS:
                child_bootstrap_frames.append(
                    bootstrap_age_slopes(
                        cells,
                        spec=spec,
                        scope=scope,
                        reps=bootstrap_reps,
                        seed=seed + index * 17,
                    ).assign(role=role)
                )
        except Exception as exc:
            summaries.append(failed_summary(spec, scope, "exact_cell_wls_child_cluster", cells, exc) | {"role": role})

    summary_frame = pd.DataFrame(summaries)
    summary_frame["protocol_result"] = summary_frame.apply(protocol_result, axis=1)
    coefficients = pd.concat(coef_frames, ignore_index=True) if coef_frames else pd.DataFrame()
    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    influence = pd.concat(influence_frames, ignore_index=True) if influence_frames else pd.DataFrame()
    child_draws = pd.concat(child_bootstrap_frames, ignore_index=True) if child_bootstrap_frames else pd.DataFrame()
    corpus_draws = pd.concat(corpus_bootstrap_frames, ignore_index=True) if corpus_bootstrap_frames else pd.DataFrame()
    permutation_draws = pd.concat(permutation_frames, ignore_index=True) if permutation_frames else pd.DataFrame()

    trajectory_input = pd.read_csv(prepared_dir / "trajectory_input.csv.gz")
    trajectory_frames: list[pd.DataFrame] = []
    slope_frames: list[pd.DataFrame] = []
    for role, scope in trajectory_input[["role", "scope"]].drop_duplicates().itertuples(index=False):
        trajectories, slopes = build_trajectories_from_prepared(
            trajectory_input,
            coefficients,
            role=str(role),
            scope=str(scope),
        )
        trajectory_frames.append(trajectories)
        if not slopes.empty:
            slope_frames.append(slopes)
    trajectories = pd.concat(trajectory_frames, ignore_index=True) if trajectory_frames else pd.DataFrame()
    slopes = pd.concat(slope_frames, ignore_index=True) if slope_frames else pd.DataFrame()

    atomic_csv(summary_frame, model_dir / "model_summaries.csv")
    atomic_csv(coefficients, model_dir / "coefficients_long.csv")
    atomic_csv(predictions, model_dir / "prediction_grid.csv")
    atomic_csv(influence, model_dir / "leave_one_cluster_out.csv")
    atomic_csv(child_draws, model_dir / "child_bootstrap_draws.csv.gz", compression="gzip")
    atomic_csv(bootstrap_summary(child_draws), model_dir / "child_bootstrap_summary.csv")
    atomic_csv(corpus_draws, model_dir / "corpus_bootstrap_draws.csv.gz", compression="gzip")
    atomic_csv(bootstrap_summary(corpus_draws), model_dir / "corpus_bootstrap_summary.csv")
    atomic_csv(permutation_draws, model_dir / "age_permutation_draws.csv.gz", compression="gzip")
    atomic_csv(trajectories, model_dir / "child_age_session_trajectories.csv.gz", compression="gzip")
    atomic_csv(slopes, model_dir / "child_slope_summary.csv")
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "stage": "models",
        "upstream_dataset_manifest": dataset_manifest,
        "model_rows": len(summary_frame),
        "pass": int(summary_frame["fit_status"].eq("PASS").sum()),
        "singular": int(summary_frame["fit_status"].eq("SINGULAR").sum()),
        "nonconverged": int(summary_frame["fit_status"].eq("NONCONVERGED").sum()),
        "failed": int(summary_frame["fit_status"].eq("FAIL").sum()),
        "bootstrap_reps": bootstrap_reps,
        "permutation_reps": permutation_reps,
        "include_mixed": include_mixed,
        "status": "COMPLETE_WITH_RECORDED_FIT_STATUS",
    }
    atomic_json(manifest, model_dir / "model_manifest.json")
    return manifest


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)


def forest_plot(
    frame: pd.DataFrame,
    *,
    label_columns: Sequence[str],
    title: str,
    xlabel: str,
    output: Path,
    color_column: str | None = None,
) -> None:
    if frame.empty:
        return
    data = frame.dropna(subset=["age_estimate", "age_ci_low", "age_ci_high"]).copy()
    if data.empty:
        return
    data["label"] = data[list(label_columns)].astype(str).agg(" · ".join, axis=1)
    data = data.reset_index(drop=True)
    colors = {
        "pbm_discovery": "#3d6f8e",
        "non_pbm_confirmation": "#bc5b45",
        "all79_descriptive": "#658b4b",
        "child": "#3d6f8e",
        "caretaker": "#b9822f",
    }
    fig, ax = plt.subplots(figsize=(10.5, max(4.2, 0.42 * len(data) + 1.8)))
    for index, row in data.iterrows():
        color = colors.get(str(row.get(color_column, "")), "#3d6f8e")
        ax.errorbar(
            row["age_estimate"],
            index,
            xerr=[[row["age_estimate"] - row["age_ci_low"]], [row["age_ci_high"] - row["age_estimate"]]],
            fmt="o",
            color=color,
            ecolor=color,
            capsize=3,
        )
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(data["label"])
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.22)
    save_figure(fig, output)


def plot_headline_primary(summaries: pd.DataFrame, fig_dir: Path) -> list[dict[str, object]]:
    primary = summaries[
        summaries["role"].eq("child")
        & summaries["model_id"].isin(PRIMARY_OUTCOMES)
        & summaries["estimator"].eq("exact_cell_wls_child_cluster")
        & summaries["fit_status"].eq("PASS")
    ].copy()
    primary["sample"] = primary["scope"].map(SCOPE_LABELS).fillna(primary["scope"])
    primary["question"] = primary["model_id"].map(PRIMARY_LABELS).fillna(primary["model_id"])
    output = fig_dir / "headline_primary_age_slopes.png"
    forest_plot(
        primary,
        label_columns=["sample", "question"],
        title="Headline age slopes at fixed lexical effort",
        xlabel="Bits per month (negative = more scorer-predictable with age)",
        output=output,
        color_column="scope",
    )
    return [{"plot_id": "headline_primary", "path": str(output), "rows": len(primary)}] if output.exists() else []


def plot_estimator_robustness(summaries: pd.DataFrame, fig_dir: Path) -> list[dict[str, object]]:
    data = summaries[
        summaries["role"].eq("child")
        & summaries["model_id"].str.startswith("P1_k3_contextual", na=False)
        & ~summaries["model_id"].str.endswith("_age_bins", na=False)
        & summaries["age_estimate"].notna()
    ].copy()
    estimator_labels = {
        "P1_k3_contextual": "Primary: child FE + clustered SE",
        "P1_k3_contextual_quadratic": "Quadratic age",
        "P1_k3_contextual_mundlak": "Within/between age",
        "P1_k3_contextual_gee": "GEE repeated measures",
        "P1_k3_contextual_linear_word_effort": "Linear word-effort control",
        "P1_k3_contextual_tail_trim_0_5pct": "0.5% tail trim",
        "P1_k3_contextual_mixed_random_intercept": "Mixed random intercept",
        "P1_k3_contextual_mixed_random_age": "Mixed random age slope",
    }
    data["sample"] = data["scope"].map(SCOPE_LABELS).fillna(data["scope"])
    data["estimator_label"] = data["model_id"].map(estimator_labels).fillna(data["model_id"])
    flagged = ~data["fit_status"].eq("PASS")
    data.loc[flagged, "estimator_label"] = (
        data.loc[flagged, "estimator_label"]
        + " ["
        + data.loc[flagged, "fit_status"].str.lower()
        + "]"
    )
    output = fig_dir / "p1_estimator_robustness.png"
    forest_plot(
        data,
        label_columns=["sample", "estimator_label"],
        title="P1 robustness across estimators and sensitivities",
        xlabel="Contextual-surprisal age slope (bits/month)",
        output=output,
        color_column="scope",
    )
    return [{"plot_id": "p1_estimator_robustness", "path": str(output), "rows": len(data)}] if output.exists() else []


def plot_candidate_gaps(summaries: pd.DataFrame, fig_dir: Path) -> list[dict[str, object]]:
    data = summaries[
        summaries["role"].eq("child")
        & summaries["model_id"].str.startswith(("B1_", "B2_", "B3_", "B4_"), na=False)
        & summaries["estimator"].eq("exact_cell_wls_child_cluster")
        & summaries["fit_status"].eq("PASS")
    ].copy()
    data["candidate"] = data["model_id"].str.extract(r"B\d_([^_]+)")[0]
    data["sample"] = data["scope"].map(SCOPE_LABELS).fillna(data["scope"])
    output = fig_dir / "candidate_gap_age_slopes.png"
    forest_plot(
        data,
        label_columns=["sample", "candidate"],
        title="Development of generated-candidate minus real-child score gaps",
        xlabel="Change in candidate-minus-real bits per month",
        output=output,
        color_column="scope",
    )
    return [{"plot_id": "candidate_gaps", "path": str(output), "rows": len(data)}] if output.exists() else []


def plot_age_bin_contrasts(coefficients: pd.DataFrame, fig_dir: Path) -> list[dict[str, object]]:
    data = coefficients[
        coefficients["role"].eq("child")
        & coefficients["model_id"].eq("P1_k3_contextual_age_bins")
        & coefficients["term"].str.contains("C(age_bin", regex=False, na=False)
    ].copy()
    if data.empty:
        return []
    data["age_bin"] = data["term"].str.extract(r"\[T\.([^]]+)\]")[0]
    data["age_bin"] = pd.Categorical(data["age_bin"], AGE_BINS, ordered=True)
    colors = {
        "pbm_discovery": "#3d6f8e",
        "non_pbm_confirmation": "#bc5b45",
        "all79_descriptive": "#658b4b",
    }
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    positions = {age_bin: index for index, age_bin in enumerate(AGE_BINS[1:])}
    offsets = {scope: offset for scope, offset in zip(sorted(data["scope"].unique()), [-0.18, 0, 0.18])}
    for scope, group in data.groupby("scope", observed=True):
        group = group.sort_values("age_bin")
        x = np.array([positions[str(value)] for value in group["age_bin"]], dtype=float) + offsets.get(scope, 0)
        ax.errorbar(
            x,
            group["estimate"],
            yerr=[group["estimate"] - group["ci_low"], group["ci_high"] - group["estimate"]],
            fmt="o-",
            capsize=3,
            label=scope,
            color=colors.get(scope, "#555555"),
        )
    ax.axhline(0, color="#555555", linewidth=1)
    ax.set_xticks(range(len(AGE_BINS) - 1))
    ax.set_xticklabels(AGE_BINS[1:], rotation=30, ha="right")
    ax.set_ylabel("Difference from 006–023 months (bits)")
    ax.set_title("P1 fixed-effort age-bin contrasts")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.22)
    output = fig_dir / "p1_age_bin_contrasts.png"
    save_figure(fig, output)
    return [{"plot_id": "p1_age_bins", "path": str(output), "rows": len(data)}]


def plot_descriptive_trajectories(prepared_dir: Path, fig_dir: Path) -> list[dict[str, object]]:
    data = pd.read_csv(prepared_dir / "descriptive_age_bin_summary.csv")
    data = data[data["role"].eq("child") & data["outcome"].isin(["contextual_k3_bits", "context_gain_k3", "lexical_words"])]
    if data.empty:
        return []
    outcomes = [
        ("contextual_k3_bits", "Contextual target surprisal", "Bits"),
        ("context_gain_k3", "Context support for the target", "k0 − k3 bits"),
        ("lexical_words", "Observed lexical effort", "Words"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), constrained_layout=True)
    colors = {
        "pbm_discovery": "#3d6f8e",
        "non_pbm_confirmation": "#bc5b45",
        "all79_descriptive": "#658b4b",
    }
    positions = {age_bin: index for index, age_bin in enumerate(AGE_BINS)}
    for ax, (outcome, title, ylabel) in zip(axes, outcomes):
        view = data[data["outcome"].eq(outcome)].copy()
        for scope, group in view.groupby("scope", observed=True):
            group["x"] = group["age_bin"].map(positions)
            group = group.sort_values("x")
            ax.plot(
                group["x"],
                group["mean"],
                marker="o",
                label=SCOPE_LABELS.get(scope, scope),
                color=colors.get(scope),
            )
            ax.fill_between(group["x"], group["q10"], group["q90"], color=colors.get(scope), alpha=0.10)
        ax.set_xticks(range(len(AGE_BINS)))
        ax.set_xticklabels(AGE_BINS, rotation=35, ha="right")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Age bin")
        ax.grid(alpha=0.18)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=max(1, len(labels)), frameon=False)
    output = fig_dir / "raw_age_bin_trajectories.png"
    fig.savefig(output, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return [{"plot_id": "raw_age_trajectories", "path": str(output), "rows": len(data)}]


def plot_child_slopes(model_dir: Path, fig_dir: Path) -> list[dict[str, object]]:
    slopes = pd.read_csv(model_dir / "child_slope_summary.csv")
    slopes = slopes[slopes["slope_supported"].eq(1)].copy()
    column = "adjusted_k3_bits_2_words_slope_per_month"
    if slopes.empty:
        return []
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    scope_order = [scope for scope in ["pbm_discovery", "non_pbm_confirmation", "all79_descriptive"] if scope in set(slopes["scope"])]
    rng = np.random.default_rng(20260721)
    for index, scope in enumerate(scope_order):
        values = slopes.loc[slopes["scope"].eq(scope), column].dropna().to_numpy(float)
        x = index + rng.uniform(-0.12, 0.12, size=len(values))
        ax.scatter(x, values, alpha=0.62, s=25, label=f"{scope} (n={len(values)})")
        if len(values):
            ax.plot([index - 0.22, index + 0.22], [np.median(values)] * 2, color="#111111", linewidth=3)
    ax.axhline(0, color="#555555", linewidth=1)
    ax.set_xticks(range(len(scope_order)))
    ax.set_xticklabels([SCOPE_LABELS.get(scope, scope) for scope in scope_order], rotation=15, ha="right")
    ax.set_ylabel("Child-specific adjusted k3 slope (bits/month)")
    ax.set_title("Heterogeneity across supported child trajectories")
    ax.grid(axis="y", alpha=0.2)
    output = fig_dir / "child_slope_distribution.png"
    save_figure(fig, output)
    return [{"plot_id": "child_slope_distribution", "path": str(output), "rows": len(slopes)}]


def plot_coverage(prepared_dir: Path, fig_dir: Path) -> list[dict[str, object]]:
    trajectories = pd.read_csv(prepared_dir / "trajectory_input.csv.gz")
    trajectories = trajectories[trajectories["role"].eq("child")]
    rows = []
    for scope, group in trajectories.groupby("scope", observed=True):
        matrix = (
            group.groupby(["child_key", "age_bin"], observed=True)["utterances"]
            .sum()
            .unstack(fill_value=0)
            .reindex(columns=AGE_BINS, fill_value=0)
        )
        matrix = matrix.loc[matrix.index.to_series().map(lambda x: (str(x).split("/")[0], str(x)) ).sort_values().index]
        fig, ax = plt.subplots(figsize=(11.5, max(5, len(matrix) * 0.22 + 2)))
        image = ax.imshow(np.log10(matrix.to_numpy(float) + 1), aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(AGE_BINS)))
        ax.set_xticklabels(AGE_BINS, rotation=35, ha="right")
        ax.set_yticks(range(len(matrix)))
        ax.set_yticklabels(matrix.index, fontsize=7)
        ax.set_title(f"Observed child coverage — {SCOPE_LABELS.get(scope, scope)}")
        ax.set_xlabel("Age bin")
        ax.set_ylabel("Child")
        fig.colorbar(image, ax=ax, label="log10(utterances + 1)")
        output = fig_dir / f"coverage_{safe_slug(scope)}.png"
        save_figure(fig, output)
        rows.append({"plot_id": f"coverage_{scope}", "path": str(output), "rows": len(group)})
    return rows


def plot_caretaker_trajectories(prepared_dir: Path, fig_dir: Path) -> list[dict[str, object]]:
    data = pd.read_csv(prepared_dir / "descriptive_age_bin_summary.csv")
    data = data[data["outcome"].isin(["contextual_k3_bits", "lexical_words"])]
    if "caretaker" not in set(data["role"]):
        return []
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), constrained_layout=True)
    positions = {age_bin: index for index, age_bin in enumerate(AGE_BINS)}
    for ax, outcome, title, ylabel in [
        (axes[0], "contextual_k3_bits", "Child and caregiver target surprisal", "Mean k3 bits"),
        (axes[1], "lexical_words", "Child and caregiver lexical effort", "Mean words"),
    ]:
        view = data[data["outcome"].eq(outcome)]
        for (scope, role), group in view.groupby(["scope", "role"], observed=True):
            group = group.copy()
            group["x"] = group["age_bin"].map(positions)
            group = group.sort_values("x")
            style = "--" if role == "caretaker" else "-"
            ax.plot(
                group["x"],
                group["mean"],
                linestyle=style,
                marker="o",
                label=f"{SCOPE_LABELS.get(scope, scope)} · {role}",
            )
        ax.set_xticks(range(len(AGE_BINS)))
        ax.set_xticklabels(AGE_BINS, rotation=35, ha="right")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.18)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    output = fig_dir / "child_caretaker_trajectories.png"
    fig.savefig(output, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return [{"plot_id": "caretaker_trajectories", "path": str(output), "rows": len(data)}]


def build_model_coverage(summaries: pd.DataFrame, *, scorer_label: str) -> pd.DataFrame:
    mixed = summaries[summaries["estimator"].astype(str).str.startswith("mixed")]
    mixed_status = "complete" if mixed.empty or mixed["fit_status"].eq("PASS").all() else "complete with warnings"
    is_tiny = "tiny" in scorer_label.lower()
    rows = [
        ("Primary k3/k0/context-gain models", "complete", "Frozen child-FE/clustered models plus age bins"),
        ("k1/k2 context-window models", "complete", "Direct target and context-gain outcomes"),
        ("Random/unigram/bigram/trigram gaps", "complete", "Fixed-effort slopes, child bootstrap, influence"),
        ("Repeated-measures sensitivities", "complete", "Mundlak and GEE"),
        ("Mixed-effects sensitivities", mixed_status, "Boundary/nonconvergence status retained"),
        ("Child and corpus uncertainty", "complete", "200 child and corpus bootstrap draws"),
        ("Age permutation", "complete", "200 within-child permutations for P1/P3"),
        ("Caretaker-input trajectories", "complete", "Interpreted as input adaptation"),
        ("Individual child trajectories", "complete", "Separate gallery with support rule"),
        (
            "Next-token entropy/top-k models",
            "unavailable" if is_tiny else "partial",
            "No Tiny handoff" if is_tiny else "PBM Mistral product exists; not full-79",
        ),
        (
            "LSTM candidate comparisons",
            "unavailable" if is_tiny else "partial",
            "LSTM candidates not Tiny-scored" if is_tiny else "PBM Mistral only; full-79 production pending",
        ),
        (
            "Response-space/semantic entropy",
            "unavailable" if is_tiny else "partial",
            "Separate sampled-response product required" if is_tiny else "PBM exact-string product only",
        ),
        (
            "Corrected Bayes synthesis",
            "pending" if is_tiny else "partial",
            "Tiny direct-score comparison pending" if is_tiny else "Corrected cross-fitted PBM product exists",
        ),
        (
            "Rich complexity controls",
            "pending" if is_tiny else "partial",
            "Validated full join not in this run" if is_tiny else "PBM products exist; full-79 validation pending",
        ),
        ("Sustained developmental onset", "pending", "Simultaneous child-level band still required"),
    ]
    return pd.DataFrame(rows, columns=["model_family", "status", "reason"])


def plot_model_coverage(coverage: pd.DataFrame, fig_dir: Path) -> list[dict[str, object]]:
    if coverage.empty:
        return []
    colors = {
        "complete": "#3f7f5f",
        "complete with warnings": "#c28a2c",
        "partial": "#c28a2c",
        "pending": "#7a6ca8",
        "unavailable": "#9a9a9a",
    }
    fig, ax = plt.subplots(figsize=(11.5, max(6, 0.46 * len(coverage) + 1.5)))
    for index, row in coverage.reset_index(drop=True).iterrows():
        ax.scatter(0, index, s=180, color=colors.get(row["status"], "#777777"), marker="s")
        ax.text(0.04, index, row["status"], va="center", fontsize=10, color=colors.get(row["status"], "#555555"))
    ax.set_yticks(range(len(coverage)))
    ax.set_yticklabels(coverage["model_family"])
    ax.set_xlim(-0.04, 0.55)
    ax.set_xticks([])
    ax.set_title("Model-family coverage and data availability")
    ax.invert_yaxis()
    for spine in ax.spines.values():
        spine.set_visible(False)
    output = fig_dir / "model_family_coverage.png"
    save_figure(fig, output)
    return [{"plot_id": "model_family_coverage", "path": str(output), "rows": len(coverage)}]


def plot_resampling_checks(model_dir: Path, summaries: pd.DataFrame, fig_dir: Path) -> list[dict[str, object]]:
    paths = {
        "Child bootstrap": model_dir / "child_bootstrap_draws.csv.gz",
        "Corpus bootstrap": model_dir / "corpus_bootstrap_draws.csv.gz",
        "Age permutation": model_dir / "age_permutation_draws.csv.gz",
    }
    frames = []
    for label, path in paths.items():
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame = frame[frame["model_id"].eq("P1_k3_contextual")].copy()
        frame["resampling"] = label
        frames.append(frame)
    if not frames:
        return []
    data = pd.concat(frames, ignore_index=True)
    scope_order = [scope for scope in ["pbm_discovery", "non_pbm_confirmation", "all79_descriptive"] if scope in set(data["scope"])]
    fig, axes = plt.subplots(1, len(scope_order), figsize=(6 * len(scope_order), 4.8), squeeze=False)
    colors = {"Child bootstrap": "#3d6f8e", "Corpus bootstrap": "#c28a2c", "Age permutation": "#8a8a8a"}
    for ax, scope in zip(axes.ravel(), scope_order):
        view = data[data["scope"].eq(scope)]
        for label, group in view.groupby("resampling", observed=True):
            values = group["age_estimate"].dropna().to_numpy(float)
            ax.hist(values, bins=24, density=True, histtype="step", linewidth=2, color=colors[label], label=label)
        observed = summaries[
            summaries["scope"].eq(scope)
            & summaries["model_id"].eq("P1_k3_contextual")
            & summaries["estimator"].eq("exact_cell_wls_child_cluster")
        ]
        if not observed.empty:
            ax.axvline(observed["age_estimate"].iloc[0], color="#111111", linewidth=2, label="Observed")
        ax.axvline(0, color="#555555", linewidth=1, linestyle=":")
        ax.set_title(SCOPE_LABELS.get(scope, scope))
        ax.set_xlabel("P1 age slope (bits/month)")
        ax.set_ylabel("Density")
        ax.grid(alpha=0.16)
    axes[0, 0].legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    output = fig_dir / "p1_resampling_checks.png"
    fig.savefig(output, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return [{"plot_id": "p1_resampling_checks", "path": str(output), "rows": len(data)}]


def plot_influence_ranges(model_dir: Path, fig_dir: Path) -> list[dict[str, object]]:
    path = model_dir / "leave_one_cluster_out.csv"
    if not path.exists():
        return []
    data = pd.read_csv(path)
    data = data[data["model_id"].eq("P1_k3_contextual")].copy()
    rows = []
    for (scope, level), group in data.groupby(["scope", "drop_level"], observed=True):
        rows.append(
            {
                "scope": scope,
                "drop_level": level,
                "observed": group["observed_age_estimate"].iloc[0],
                "minimum": group["leave_out_age_estimate"].min(),
                "maximum": group["leave_out_age_estimate"].max(),
                "largest_change": group["change_from_observed"].abs().max(),
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return []
    summary["label"] = summary["scope"].map(SCOPE_LABELS).fillna(summary["scope"]) + " · leave one " + summary["drop_level"] + " out"
    fig, ax = plt.subplots(figsize=(10.5, max(4.2, 0.58 * len(summary) + 1.6)))
    for index, row in summary.reset_index(drop=True).iterrows():
        ax.plot([row["minimum"], row["maximum"]], [index, index], linewidth=5, alpha=0.55, color="#4a748b")
        ax.scatter(row["observed"], index, color="#b3483e", s=60, zorder=3)
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(range(len(summary)))
    ax.set_yticklabels(summary["label"])
    ax.set_xlabel("P1 contextual-surprisal age slope (bits/month)")
    ax.set_title("Leave-one-child and leave-one-corpus influence ranges")
    ax.grid(axis="x", alpha=0.2)
    output = fig_dir / "p1_influence_ranges.png"
    save_figure(fig, output)
    atomic_csv(summary, model_dir / "influence_range_summary.csv")
    return [{"plot_id": "p1_influence_ranges", "path": str(output), "rows": len(data)}]


def run_plot_stage(*, prepared_dir: Path, model_dir: Path, fig_dir: Path) -> dict[str, object]:
    model_manifest = json.loads((model_dir / "model_manifest.json").read_text())
    scorer_label = str(model_manifest["upstream_dataset_manifest"]["scorer_label"])
    fig_dir.mkdir(parents=True, exist_ok=True)
    summaries = pd.read_csv(model_dir / "model_summaries.csv")
    coefficients = pd.read_csv(model_dir / "coefficients_long.csv")
    plot_rows: list[dict[str, object]] = []
    plot_rows.extend(plot_headline_primary(summaries, fig_dir))
    plot_rows.extend(plot_estimator_robustness(summaries, fig_dir))
    plot_rows.extend(plot_candidate_gaps(summaries, fig_dir))
    plot_rows.extend(plot_age_bin_contrasts(coefficients, fig_dir))
    plot_rows.extend(plot_descriptive_trajectories(prepared_dir, fig_dir))
    plot_rows.extend(plot_child_slopes(model_dir, fig_dir))
    plot_rows.extend(plot_coverage(prepared_dir, fig_dir))
    plot_rows.extend(plot_caretaker_trajectories(prepared_dir, fig_dir))
    plot_rows.extend(plot_resampling_checks(model_dir, summaries, fig_dir))
    plot_rows.extend(plot_influence_ranges(model_dir, fig_dir))
    model_coverage = build_model_coverage(summaries, scorer_label=scorer_label)
    atomic_csv(model_coverage, model_dir / "model_coverage.csv")
    plot_rows.extend(plot_model_coverage(model_coverage, fig_dir))

    trajectories = pd.read_csv(model_dir / "child_age_session_trajectories.csv.gz")
    slopes = pd.read_csv(model_dir / "child_slope_summary.csv")
    profile_frames = []
    child_trajectories = trajectories[trajectories["role"].eq("child")] if "role" in trajectories else trajectories
    for scope, group in child_trajectories.groupby("scope", observed=True):
        scope_slopes = slopes[slopes["scope"].eq(scope)]
        profile_frames.append(build_child_profile_plots(group, scope_slopes, fig_dir, str(scope)))
    profiles = pd.concat(profile_frames, ignore_index=True) if profile_frames else pd.DataFrame()
    atomic_csv(profiles, model_dir / "child_profile_audit.csv")
    for row in profiles.itertuples():
        plot_rows.append({"plot_id": f"child_{safe_slug(row.child_key)}", "path": row.plot, "rows": row.trajectory_points})
    audit = pd.DataFrame(plot_rows)
    if not audit.empty:
        audit["exists"] = audit["path"].map(lambda value: Path(value).exists())
        audit["bytes"] = audit["path"].map(lambda value: Path(value).stat().st_size if Path(value).exists() else 0)
    atomic_csv(audit, model_dir / "plot_audit.csv")
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "stage": "plots",
        "upstream_model_manifest": model_manifest,
        "plots": len(audit),
        "missing": int((~audit["exists"]).sum()) if not audit.empty else 0,
        "child_profiles": len(profiles),
        "status": "COMPLETE" if audit.empty or audit["exists"].all() else "INCOMPLETE",
    }
    atomic_json(manifest, model_dir / "plot_manifest.json")
    return manifest


def fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "" if not math.isfinite(number) else f"{number:.{digits}f}"


def compact_primary_table(primary: pd.DataFrame) -> str:
    if primary.empty:
        return "_No primary estimates available._"
    labels = {
        "P1_k3_contextual": "Contextual predictability (k3)",
        "P2_k0_unconditional": "Unconditional form predictability (k0)",
        "P3_k3_context_gain": "Context support (k0 − k3)",
    }
    lines = [
        "| sample | question | slope per month | 95% interval | protocol reading |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in primary.itertuples():
        lines.append(
            "| "
            + " | ".join(
                [
                    SCOPE_LABELS.get(str(row.scope), str(row.scope)),
                    labels.get(str(row.model_id), str(row.model_id)),
                    fmt(row.age_estimate),
                    f"[{fmt(row.age_ci_low)}, {fmt(row.age_ci_high)}]",
                    str(row.protocol_result).replace("_", " "),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def primary_takeaways(primary: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    for scope in ["pbm_discovery", "non_pbm_confirmation", "all79_descriptive"]:
        row = primary[
            primary["scope"].eq(scope) & primary["model_id"].eq("P1_k3_contextual")
        ]
        if row.empty:
            continue
        item = row.iloc[0]
        interval = f"[{fmt(item['age_ci_low'])}, {fmt(item['age_ci_high'])}]"
        if scope == "non_pbm_confirmation":
            decision = (
                "meets the frozen primary confirmation rule"
                if item["age_ci_high"] < 0
                else "points in the expected direction but does not meet the frozen primary confirmation rule"
            )
        elif scope == "all79_descriptive":
            decision = "is descriptive because it pools discovery and confirmation children"
        else:
            decision = "is a discovery/scorer-robustness estimate"
        lines.append(
            f"- **{SCOPE_LABELS.get(scope, scope)}:** P1 = {fmt(item['age_estimate'])} bits/month, 95% CI {interval}; {decision}."
        )
    p3 = primary[primary["model_id"].eq("P3_k3_context_gain")]
    if not p3.empty:
        contrary = int((p3["age_estimate"] < 0).sum())
        lines.append(
            f"- Context-gain development is negative in {contrary}/{len(p3)} displayed samples, opposite the frozen positive prediction wherever the interval excludes zero."
        )
    return lines


def coverage_summary_text(model_manifest: Mapping[str, object], summaries: pd.DataFrame) -> str:
    pass_count = int(summaries["fit_status"].eq("PASS").sum())
    singular = int(summaries["fit_status"].eq("SINGULAR").sum())
    nonconverged = int(summaries["fit_status"].eq("NONCONVERGED").sum())
    failed = int(summaries["fit_status"].eq("FAIL").sum())
    return (
        f"This staged run records **{pass_count} passing fits**, **{singular} "
        f"singular/boundary fits**, **{nonconverged} nonconverged fits**, and "
        f"**{failed} failed fits**. Nonconvergence and "
        "singularity are retained as results of the sensitivity audit; they are not hidden."
    )


def build_child_gallery(
    *,
    profile_audit: pd.DataFrame,
    report_md: Path,
    report_html: Path,
    scorer_label: str,
) -> None:
    lines = [
        f"# {scorer_label}: Individual Child Trajectories",
        "",
        "Each point is a child-session-age mean. Point size reflects utterance count. "
        "Straight lines are shown only for children meeting the prespecified support rule. "
        "These child fits are descriptive and are not individually multiplicity-adjusted.",
        "",
    ]
    for scope, scope_rows in profile_audit.groupby("scope", observed=True):
        lines.extend([f"## {scope}", ""])
        for dataset, dataset_rows in scope_rows.groupby("dataset", observed=True):
            lines.extend([f"### {dataset}", ""])
            for row in dataset_rows.sort_values("child_id").itertuples():
                lines.extend(
                    [
                        f"#### {row.child_key}",
                        "",
                        f"![{row.child_key}]({relative(Path(row.plot), report_md)})",
                        "",
                    ]
                )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines), encoding="utf-8")
    render_markdown_file(report_md, report_html, title=f"{scorer_label}: Child Trajectories")


def run_report_stage(
    *,
    prepared_dir: Path,
    model_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    gallery_md: Path,
    gallery_html: Path,
    scorer_label: str,
) -> dict[str, object]:
    plot_manifest = json.loads((model_dir / "plot_manifest.json").read_text())
    model_manifest = json.loads((model_dir / "model_manifest.json").read_text())
    summaries = pd.read_csv(model_dir / "model_summaries.csv")
    profiles = pd.read_csv(model_dir / "child_profile_audit.csv")
    primary = summaries[
        summaries["role"].eq("child")
        & summaries["model_id"].isin(PRIMARY_OUTCOMES)
        & summaries["estimator"].eq("exact_cell_wls_child_cluster")
        & summaries["fit_status"].eq("PASS")
    ].copy()
    build_child_gallery(
        profile_audit=profiles,
        report_md=gallery_md,
        report_html=gallery_html,
        scorer_label=scorer_label,
    )

    def image(filename: str, alt: str) -> str:
        path = fig_dir / filename
        return f"![{alt}]({relative(path, report_md)})" if path.exists() else f"_{alt} unavailable._"

    takeaways = "\n".join(primary_takeaways(primary))
    coverage_plots = sorted(fig_dir.glob("coverage_*.png"))
    coverage_images = "\n\n".join(
        f"![{path.stem}]({relative(path, report_md)})" for path in coverage_plots
    )
    report = f"""# {scorer_label}: Visual Direct-Surprisal Summary

This is the short, plot-led report. It keeps the scientific decisions visible
and sends full coefficient tables, bootstrap draws, and diagnostics to saved
CSV files. A negative P1 slope means the scorer finds older children's observed
utterances more predictable at the same exact/top-coded word effort. It is not
proof of a universal efficiency optimum.

## What We Found

{takeaways}

{image("headline_primary_age_slopes.png", "Headline fixed-effort age slopes")}

## The Three Frozen Questions

{compact_primary_table(primary)}

Context gain is `k0 - k3`: positive values mean the preceding context supports
the observed utterance under this scorer. The slope asks whether that support
changes with age.

## What The Raw Data Look Like

The lines are age-bin means and the shaded regions span the 10th to 90th
percentiles. They are descriptive; the fixed-effort models come afterward.

{image("raw_age_bin_trajectories.png", "Raw age-bin trajectories")}

## Do The Conclusions Depend On The Estimator?

The first row for each scope is the frozen child-fixed, child-clustered model.
Other rows are nonlinear, within/between, GEE, word-effort, tail-trim, and
mixed-effects sensitivities. Mixed models use unweighted design cells and are
therefore sensitivity estimands, not replacements for the primary model.

{image("p1_estimator_robustness.png", "P1 estimator robustness")}

{coverage_summary_text(model_manifest, summaries)}

## Resampling And Influence Checks

Child bootstrap and corpus bootstrap show how the estimate changes when whole
sampling units are resampled. The age-permutation distribution is a falsification
reference created by scrambling age within children. In the influence plot, the
bar spans all leave-one-unit estimates and the red point is the full estimate.

{image("p1_resampling_checks.png", "P1 resampling checks")}

{image("p1_influence_ranges.png", "P1 influence ranges")}

## Development Across Frozen Age Bins

These are differences from 006–023 months at fixed lexical effort. They do not
by themselves establish a sustained onset.

{image("p1_age_bin_contrasts.png", "P1 age-bin contrasts")}

## Real Children Versus Generated N-Gram Candidates

These plots use candidate-minus-real score gaps. Random and n-gram utterances
are same-length controls, not same-meaning alternatives.

{image("candidate_gap_age_slopes.png", "Candidate-gap age slopes")}

## How Different Are Individual Children?

Each dot is one supported child-specific slope; the thick bar is the median.
The individual slopes are descriptive and not multiplicity-adjusted.

{image("child_slope_distribution.png", "Child slope distribution")}

[Open the individual-child trajectory gallery]({relative(gallery_html, report_md)})

## Child And Caregiver Input

Caregiver trajectories are indexed by child age and describe input adaptation;
they are not an adult developmental endpoint.

{image("child_caretaker_trajectories.png", "Child and caregiver trajectories")}

## Coverage Before Interpretation

Darker cells contain more observed utterances. Empty cells are genuine age
coverage gaps; plotted lines should not be read as observations there.

{coverage_images}

## What This Scorer Cannot Answer Yet

{image("model_family_coverage.png", "Model-family coverage")}

- Scorer-specific next-token entropy/top-k models require a separate entropy handoff.
- LSTM comparisons require the LSTM candidates to be scored by this scorer.
- Response-space and semantic-entropy analyses require separately frozen sampled responses.
- Corrected Bayes candidate-set probabilities and direct neural surprisal are different estimands.

## Detailed Audit Files

- Model status and headline coefficients: `{model_dir / "model_summaries.csv"}`
- Full coefficients: `{model_dir / "coefficients_long.csv"}`
- Child bootstrap: `{model_dir / "child_bootstrap_summary.csv"}`
- Corpus bootstrap: `{model_dir / "corpus_bootstrap_summary.csv"}`
- Age permutation draws: `{model_dir / "age_permutation_draws.csv.gz"}`
- Leave-one-child/corpus influence: `{model_dir / "leave_one_cluster_out.csv"}`
- Model-family coverage and blockers: `{model_dir / "model_coverage.csv"}`
- Child trajectories: `{model_dir / "child_age_session_trajectories.csv.gz"}`
- Dataset flow and coverage: `{prepared_dir}`
"""
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(report, encoding="utf-8")
    render_markdown_file(report_md, report_html, title=f"{scorer_label}: Visual Summary")
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "stage": "report",
        "upstream_plot_manifest": plot_manifest,
        "report_md": str(report_md),
        "report_html": str(report_html),
        "gallery_md": str(gallery_md),
        "gallery_html": str(gallery_html),
        "status": "COMPLETE",
    }
    atomic_json(manifest, model_dir / "report_manifest.json")
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["datasets", "models", "plots", "report", "all"], default="all")
    parser.add_argument("--input-wide", type=Path)
    parser.add_argument("--caretaker-wide", type=Path)
    parser.add_argument("--prepared-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--fig-dir", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-html", type=Path, required=True)
    parser.add_argument("--gallery-md", type=Path, required=True)
    parser.add_argument("--gallery-html", type=Path, required=True)
    parser.add_argument("--scorer-label", required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--permutation-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260721)
    parser.add_argument("--skip-mixed", action="store_true")
    args = parser.parse_args(argv)
    if args.stage in {"datasets", "all"} and args.input_wide is None:
        parser.error("--input-wide is required for the datasets/all stage")
    return args


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    outputs: dict[str, object] = {}
    if args.stage in {"datasets", "all"}:
        outputs["datasets"] = run_dataset_stage(
            input_wide=args.input_wide,
            caretaker_wide=args.caretaker_wide,
            prepared_dir=args.prepared_dir,
            scorer_label=args.scorer_label,
        )
    if args.stage in {"models", "all"}:
        outputs["models"] = run_model_stage(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            bootstrap_reps=args.bootstrap_reps,
            permutation_reps=args.permutation_reps,
            seed=args.seed,
            include_mixed=not args.skip_mixed,
        )
    if args.stage in {"plots", "all"}:
        outputs["plots"] = run_plot_stage(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            fig_dir=args.fig_dir,
        )
    if args.stage in {"report", "all"}:
        outputs["report"] = run_report_stage(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            fig_dir=args.fig_dir,
            report_md=args.report_md,
            report_html=args.report_html,
            gallery_md=args.gallery_md,
            gallery_html=args.gallery_html,
            scorer_label=args.scorer_label,
        )
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
