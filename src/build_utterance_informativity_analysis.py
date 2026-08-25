#!/usr/bin/env python3
"""Build the utterance-level informativity extension for Routes 1 and 2.

This workflow does not redefine a single utterance occurrence's surprisal as
type-level informativity.  It uses three distinct objects:

* occurrence predictability: ``-log2 p(u | c)`` (Mistral k3);
* effort-standardized population informativity: the adjusted mean k3 score in
  an age/speaker population under a shared utterance-length distribution;
* recurrent utterance-type informativity: mean k3 score across the attested
  contexts of a sufficiently recurrent exact utterance string.

The workflow also fits the missing utterance-level analogue of the
frequency/informativity analysis: how k0 and k3 score density are coupled, and
whether that coupling changes with child age.  Existing frozen Route 1
P1/P2/P3 and Route 2 M1/M2/M4/M5 fits are inventoried rather than duplicated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import patsy
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHILD = ROOT / "results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz"
DEFAULT_CARETAKER = ROOT / "results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz"
DEFAULT_ROUTE1_MODELS = ROOT / "results/direct_surprisal_replication/mistral_full79/modular/models/model_summaries.csv"
DEFAULT_ROUTE2_MODELS = ROOT / "results/full79_joint_efficiency_analysis/models/combined_model_registry.csv"
DEFAULT_OUTPUT = ROOT / "results/utterance_informativity_analysis"
DEFAULT_REPORT_MD = ROOT / "docs/utterance_informativity_route1_route2_report.md"
DEFAULT_REPORT_HTML = ROOT / "docs/utterance_informativity_route1_route2_report.html"

PBM_CORPORA = {"Brown", "Manchester", "Providence"}
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
SCOPES = ("pbm_discovery", "non_pbm_confirmation", "all79_descriptive")
ROLES = ("child", "caretaker")

CHILD_COLUMNS = [
    "dataset",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_bin",
    "utterance_id",
    "real_target_text",
    "real_target_text_sha256",
    "real_nb_words",
    "real_k0_sum_bits",
    "real_k0_mean_bits_per_token",
    "real_k0_n_eval_tokens",
    "real_k3_sum_bits",
    "real_k3_mean_bits_per_token",
    "real_k3_n_eval_tokens",
    "real_context_gain_k3",
    "context_available_k3",
]

CARETAKER_COLUMNS = [
    "dataset",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_bin",
    "utterance_id",
    "target_text",
    "target_text_sha256",
    "nb_words",
    "k0_sum_bits",
    "k0_mean_bits_per_token",
    "k0_n_eval_tokens",
    "k3_sum_bits",
    "k3_mean_bits_per_token",
    "k3_n_eval_tokens",
    "context_gain_k3",
    "context_available_k3",
]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {"path": str(resolved), "bytes": resolved.stat().st_size, "sha256": sha256_file(resolved)}


def atomic_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".csv.gz" if str(path).endswith(".gz") else ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
    frame.to_csv(temporary, index=False, compression="gzip" if suffix.endswith(".gz") else None)
    os.replace(temporary, path)


def _scope_from_dataset(dataset: pd.Series) -> pd.Series:
    return np.where(dataset.astype(str).isin(PBM_CORPORA), "pbm_discovery", "non_pbm_confirmation")


def canonicalize_role_frame(frame: pd.DataFrame, role: str) -> pd.DataFrame:
    """Map a scorer-wide child/caretaker chunk to one common row contract."""

    if role not in ROLES:
        raise ValueError(f"unknown role: {role}")
    if role == "child":
        rename = {
            "real_target_text": "target_text",
            "real_target_text_sha256": "target_hash",
            "real_nb_words": "words",
            "real_k0_sum_bits": "k0_total",
            "real_k0_mean_bits_per_token": "k0_density",
            "real_k0_n_eval_tokens": "k0_tokens",
            "real_k3_sum_bits": "k3_total",
            "real_k3_mean_bits_per_token": "k3_density",
            "real_k3_n_eval_tokens": "k3_tokens",
            "real_context_gain_k3": "context_gain_total",
        }
    else:
        rename = {
            "target_text_sha256": "target_hash",
            "nb_words": "words",
            "k0_sum_bits": "k0_total",
            "k0_mean_bits_per_token": "k0_density",
            "k0_n_eval_tokens": "k0_tokens",
            "k3_sum_bits": "k3_total",
            "k3_mean_bits_per_token": "k3_density",
            "k3_n_eval_tokens": "k3_tokens",
            "context_gain_k3": "context_gain_total",
        }
    result = frame.rename(columns=rename).copy()
    required = {
        "dataset",
        "child_key",
        "age_months",
        "age_bin",
        "utterance_id",
        "target_text",
        "target_hash",
        "words",
        "k0_total",
        "k0_density",
        "k0_tokens",
        "k3_total",
        "k3_density",
        "k3_tokens",
        "context_gain_total",
        "context_available_k3",
    }
    missing = sorted(required - set(result.columns))
    if missing:
        raise ValueError(f"{role} frame missing required columns: {missing}")
    numeric = [
        "age_months",
        "words",
        "k0_total",
        "k0_density",
        "k0_tokens",
        "k3_total",
        "k3_density",
        "k3_tokens",
        "context_gain_total",
        "context_available_k3",
    ]
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    finite = np.ones(len(result), dtype=bool)
    for column in ["age_months", "words", "k0_total", "k0_density", "k3_total", "k3_density", "context_gain_total"]:
        finite &= np.isfinite(result[column].to_numpy(dtype=float))
    finite &= result["context_available_k3"].eq(1).to_numpy()
    finite &= result["words"].gt(0).to_numpy()
    finite &= result["target_hash"].notna().to_numpy()
    result = result.loc[finite].copy()
    result["role"] = role
    result["words"] = result["words"].astype(int)
    result["words_top12"] = result["words"].clip(upper=12).astype(int)
    result["density_pair_valid"] = (
        result["k0_tokens"].gt(0)
        & result["k3_tokens"].gt(0)
        & result["k0_tokens"].eq(result["k3_tokens"])
    )
    result["context_gain_density"] = np.where(
        result["density_pair_valid"],
        result["k0_density"] - result["k3_density"],
        np.nan,
    )
    result["analysis_scope"] = _scope_from_dataset(result["dataset"])
    result["age_bin"] = pd.Categorical(result["age_bin"], categories=AGE_BINS, ordered=True)
    result = result[result["age_bin"].notna()].copy()
    return result


def build_recurring_type_table(
    frame: pd.DataFrame,
    *,
    min_occurrences: int = 100,
    min_children: int = 10,
    min_corpora: int = 3,
) -> pd.DataFrame:
    """Estimate exact utterance-type informativity on a supported subset."""

    required = {
        "role",
        "target_hash",
        "target_text",
        "child_key",
        "dataset",
        "age_bin",
        "words",
        "k0_total",
        "k3_total",
        "context_gain_total",
        "k0_density",
        "k3_density",
        "context_gain_density",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"recurring-type frame missing columns: {missing}")
    totals = frame.groupby("role", observed=True).size().to_dict()
    aggregations: dict[str, tuple[str, str]] = {
        "target_text": ("target_text", "first"),
        "occurrences": ("target_hash", "size"),
        "children": ("child_key", "nunique"),
        "corpora": ("dataset", "nunique"),
        "age_bins": ("age_bin", "nunique"),
        "word_count": ("words", "median"),
        "mean_k0_total_bits": ("k0_total", "mean"),
        "mean_k3_total_bits": ("k3_total", "mean"),
        "mean_context_support_bits": ("context_gain_total", "mean"),
        "mean_k0_bits_per_token": ("k0_density", "mean"),
        "mean_k3_bits_per_token": ("k3_density", "mean"),
        "mean_context_support_bits_per_token": ("context_gain_density", "mean"),
    }
    if "density_pair_valid" in frame:
        aggregations["density_pair_occurrences"] = ("density_pair_valid", "sum")
    grouped = (
        frame.groupby(["role", "target_hash"], observed=True, as_index=False)
        .agg(**aggregations)
    )
    grouped = grouped[
        grouped["occurrences"].ge(min_occurrences)
        & grouped["children"].ge(min_children)
        & grouped["corpora"].ge(min_corpora)
    ].copy()
    grouped["reference_role_rows"] = grouped["role"].map(totals).astype(int)
    grouped["empirical_frequency_bits"] = -np.log2(
        grouped["occurrences"] / grouped["reference_role_rows"]
    )
    grouped["definition"] = "mean Mistral k3 self-information across attested contexts of this exact normalized utterance string"
    grouped = grouped.sort_values(["role", "occurrences", "target_hash"], ascending=[True, False, True]).reset_index(drop=True)
    return grouped


def _weighted_group(frame: pd.DataFrame, keys: Sequence[str]) -> pd.DataFrame:
    value_columns = [
        "age_mean",
        "k0_total_mean",
        "k3_total_mean",
        "context_gain_total_mean",
        "k0_density_mean",
        "k3_density_mean",
        "context_gain_density_mean",
    ]
    working = frame.copy()
    for column in value_columns:
        working[f"__{column}"] = working[column] * working["n"]
    aggregations: dict[str, tuple[str, str]] = {"n": ("n", "sum")}
    aggregations.update({f"__{column}": (f"__{column}", "sum") for column in value_columns})
    result = working.groupby(list(keys), observed=True, as_index=False).agg(**aggregations)
    for column in value_columns:
        result[column] = result.pop(f"__{column}") / result["n"]
    return result


def build_model_cells(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse occurrences while preserving k0-density variation for coupling."""

    working = frame.copy()
    if "density_pair_valid" not in working:
        working["density_pair_valid"] = True
    working["k0_density_bin"] = np.where(
        working["density_pair_valid"],
        (working["k0_density"] * 2).round() / 2,
        -1.0,
    )
    keys = [
        "role",
        "dataset",
        "child_key",
        "analysis_scope",
        "age_bin",
        "words_top12",
        "density_pair_valid",
        "k0_density_bin",
    ]
    return (
        working.groupby(keys, observed=True, as_index=False)
        .agg(
            n=("utterance_id", "size"),
            age_mean=("age_months", "mean"),
            k0_total_mean=("k0_total", "mean"),
            k3_total_mean=("k3_total", "mean"),
            context_gain_total_mean=("context_gain_total", "mean"),
            k0_density_mean=("k0_density", "mean"),
            k3_density_mean=("k3_density", "mean"),
            context_gain_density_mean=("context_gain_density", "mean"),
        )
    )


def _scope_rows(cells: pd.DataFrame, role: str, scope: str) -> pd.DataFrame:
    if scope not in SCOPES:
        raise ValueError(f"unknown scope: {scope}")
    selected = cells[cells["role"].eq(role)].copy()
    if scope != "all79_descriptive":
        selected = selected[selected["analysis_scope"].eq(scope)].copy()
    if selected.empty:
        raise ValueError(f"no rows for {role}/{scope}")
    selected["age_bin"] = pd.Categorical(selected["age_bin"], categories=AGE_BINS, ordered=True)
    return selected


def _clustered_wls(formula: str, data: pd.DataFrame, weight_column: str = "n"):
    model = smf.wls(formula, data=data, weights=data[weight_column])
    return model.fit(cov_type="cluster", cov_kwds={"groups": data["child_key"]})


def _design_average(
    fit,
    *,
    age_bin: str,
    children: Sequence[str],
    word_weights: pd.Series,
    extra: dict[str, float] | None = None,
) -> np.ndarray:
    rows = []
    weights = []
    for child in children:
        for words, probability in word_weights.items():
            row: dict[str, Any] = {"age_bin": age_bin, "words_top12": int(words), "child_key": child}
            if extra:
                row.update(extra)
            rows.append(row)
            weights.append(float(probability) / len(children))
    design = patsy.build_design_matrices([fit.model.data.design_info], pd.DataFrame(rows))[0]
    return np.asarray(design).T @ np.asarray(weights)


def fit_standardized_outcome(
    cells: pd.DataFrame,
    *,
    role: str,
    scope: str,
    outcome: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Fit child-controlled exact-effort cells and g-standardize by age bin."""

    selected = _scope_rows(cells, role, scope)
    selected = _weighted_group(
        selected,
        ["role", "dataset", "child_key", "analysis_scope", "age_bin", "words_top12"],
    )
    formula = f"{outcome} ~ C(age_bin, Treatment(reference='006-023')) + C(words_top12) + C(child_key)"
    fit = _clustered_wls(formula, selected)
    children = sorted(selected["child_key"].astype(str).unique())
    word_counts = selected.groupby("words_top12", observed=True)["n"].sum()
    word_weights = word_counts / word_counts.sum()
    covariance = np.asarray(fit.cov_params())
    estimates = []
    for age_bin in AGE_BINS:
        xbar = _design_average(
            fit,
            age_bin=age_bin,
            children=children,
            word_weights=word_weights,
        )
        estimate = float(xbar @ np.asarray(fit.params))
        variance = max(0.0, float(xbar @ covariance @ xbar))
        standard_error = math.sqrt(variance)
        estimates.append(
            {
                "role": role,
                "analysis_scope": scope,
                "outcome": outcome,
                "age_bin": age_bin,
                "estimate": estimate,
                "std_error": standard_error,
                "ci_low": estimate - 1.96 * standard_error,
                "ci_high": estimate + 1.96 * standard_error,
                "reference_effort_distribution": "scope-role pooled exact/top-coded word-count distribution",
                "reference_children": len(children),
            }
        )
    registry = {
        "model_id": f"standardized_{role}_{scope}_{outcome}",
        "route": "Route 1",
        "role": role,
        "analysis_scope": scope,
        "outcome": outcome,
        "formula": formula,
        "estimator": "opportunity-weighted WLS with child-clustered covariance",
        "n_cells": len(selected),
        "source_rows": int(selected["n"].sum()),
        "children": len(children),
        "corpora": int(selected["dataset"].nunique()),
        "status": "PASS",
        "r_squared": float(fit.rsquared),
    }
    return registry, pd.DataFrame(estimates)


def _weighted_quantile(values: pd.Series, weights: pd.Series, quantile: float) -> float:
    order = np.argsort(values.to_numpy(dtype=float))
    sorted_values = values.to_numpy(dtype=float)[order]
    sorted_weights = weights.to_numpy(dtype=float)[order]
    cumulative = np.cumsum(sorted_weights) / sorted_weights.sum()
    return float(np.interp(quantile, cumulative, sorted_values))


def fit_frequency_informativity_coupling(
    cells: pd.DataFrame,
    *,
    role: str,
    scope: str,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Fit the k0/k3 density relationship and its developmental moderation."""

    selected = _scope_rows(cells, role, scope)
    if "density_pair_valid" in selected:
        selected = selected[selected["density_pair_valid"].astype(bool)].copy()
    selected = selected[
        np.isfinite(selected["k0_density_mean"])
        & np.isfinite(selected["k3_density_mean"])
    ].copy()
    age_center = float(np.average(selected["age_mean"], weights=selected["n"]))
    selected["age_c"] = (selected["age_mean"] - age_center) / 6.0
    formula = (
        "k3_density_mean ~ age_c + I(age_c ** 2) + k0_density_mean "
        "+ I(k0_density_mean ** 2) + age_c:k0_density_mean "
        "+ C(words_top12) + C(child_key)"
    )
    fit = _clustered_wls(formula, selected)
    confidence = fit.conf_int()
    coefficients = pd.DataFrame(
        {
            "term": fit.params.index,
            "estimate": fit.params.to_numpy(dtype=float),
            "std_error": fit.bse.to_numpy(dtype=float),
            "ci_low": confidence.iloc[:, 0].to_numpy(dtype=float),
            "ci_high": confidence.iloc[:, 1].to_numpy(dtype=float),
            "p_value": fit.pvalues.to_numpy(dtype=float),
        }
    )
    coefficients.insert(0, "model_id", f"coupling_{role}_{scope}")
    children = sorted(selected["child_key"].astype(str).unique())
    word_counts = selected.groupby("words_top12", observed=True)["n"].sum()
    word_weights = word_counts / word_counts.sum()
    k0_low = _weighted_quantile(selected["k0_density_mean"], selected["n"], 0.10)
    k0_high = _weighted_quantile(selected["k0_density_mean"], selected["n"], 0.90)
    covariance = np.asarray(fit.cov_params())
    contrasts = []
    for age_bin in AGE_BINS:
        age_rows = selected[selected["age_bin"].eq(age_bin)]
        age_value = float(np.average(age_rows["age_mean"], weights=age_rows["n"])) if not age_rows.empty else age_center
        age_c = (age_value - age_center) / 6.0
        low = _design_average(
            fit,
            age_bin=age_bin,
            children=children,
            word_weights=word_weights,
            extra={"age_c": age_c, "k0_density_mean": k0_low},
        )
        high = _design_average(
            fit,
            age_bin=age_bin,
            children=children,
            word_weights=word_weights,
            extra={"age_c": age_c, "k0_density_mean": k0_high},
        )
        difference = high - low
        estimate = float(difference @ np.asarray(fit.params))
        standard_error = math.sqrt(max(0.0, float(difference @ covariance @ difference)))
        contrasts.append(
            {
                "model_id": f"coupling_{role}_{scope}",
                "role": role,
                "analysis_scope": scope,
                "age_bin": age_bin,
                "age_months_reference": age_value,
                "k0_p10_bits_per_token": k0_low,
                "k0_p90_bits_per_token": k0_high,
                "k3_p90_minus_p10_estimate": estimate,
                "std_error": standard_error,
                "ci_low": estimate - 1.96 * standard_error,
                "ci_high": estimate + 1.96 * standard_error,
            }
        )
    registry = {
        "model_id": f"coupling_{role}_{scope}",
        "route": "Route 1 extension",
        "role": role,
        "analysis_scope": scope,
        "outcome": "k3_density_mean",
        "formula": formula,
        "estimator": "opportunity-weighted WLS with child-clustered covariance",
        "n_cells": len(selected),
        "source_rows": int(selected["n"].sum()),
        "children": len(children),
        "corpora": int(selected["dataset"].nunique()),
        "status": "PASS",
        "r_squared": float(fit.rsquared),
        "age_center_months": age_center,
        "interpretation": "developmental moderation of scorer-indexed k0/k3 density coupling; not semantic utility",
    }
    return registry, coefficients, pd.DataFrame(contrasts)


def _load_role_input(path: Path, role: str, chunksize: int) -> pd.DataFrame:
    columns = CHILD_COLUMNS if role == "child" else CARETAKER_COLUMNS
    chunks = []
    for index, chunk in enumerate(pd.read_csv(path, usecols=columns, chunksize=chunksize), start=1):
        canonical = canonicalize_role_frame(chunk, role)
        if not canonical.empty:
            chunks.append(canonical)
        print(f"[datasets] {role} chunk {index}: retained={sum(len(item) for item in chunks):,}", flush=True)
    if not chunks:
        raise RuntimeError(f"no eligible {role} rows in {path}")
    return pd.concat(chunks, ignore_index=True)


def run_datasets_stage(
    output_dir: Path,
    child_input: Path,
    caretaker_input: Path,
    *,
    chunksize: int = 200_000,
    min_type_occurrences: int = 100,
    min_type_children: int = 10,
    min_type_corpora: int = 3,
) -> dict[str, Any]:
    dataset_dir = output_dir / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    all_cells = []
    all_types = []
    role_audits = []
    for role, path in (("child", child_input), ("caretaker", caretaker_input)):
        rows = _load_role_input(path, role, chunksize)
        cells = build_model_cells(rows)
        recurring = build_recurring_type_table(
            rows,
            min_occurrences=min_type_occurrences,
            min_children=min_type_children,
            min_corpora=min_type_corpora,
        )
        all_cells.append(cells)
        all_types.append(recurring)
        role_audits.append(
            {
                "role": role,
                "eligible_rows": len(rows),
                "children": int(rows["child_key"].nunique()),
                "corpora": int(rows["dataset"].nunique()),
                "age_bins": sorted(rows["age_bin"].astype(str).unique().tolist()),
                "model_cells": len(cells),
                "supported_recurrent_types": len(recurring),
                "finite_k0": int(np.isfinite(rows["k0_total"]).sum()),
                "finite_k3": int(np.isfinite(rows["k3_total"]).sum()),
                "finite_context_support": int(np.isfinite(rows["context_gain_total"]).sum()),
                "density_pair_rows": int(rows["density_pair_valid"].sum()),
                "density_pair_excluded": int((~rows["density_pair_valid"]).sum()),
            }
        )
        del rows
    cells_path = dataset_dir / "model_cells.csv.gz"
    types_path = dataset_dir / "recurrent_utterance_types.csv.gz"
    atomic_csv(pd.concat(all_cells, ignore_index=True), cells_path)
    atomic_csv(pd.concat(all_types, ignore_index=True), types_path)
    problems = []
    for audit in role_audits:
        if audit["children"] != 79:
            problems.append(f"{audit['role']} child-index coverage is {audit['children']}, expected 79")
        if audit["corpora"] != 13:
            problems.append(f"{audit['role']} corpus coverage is {audit['corpora']}, expected 13")
        if audit["age_bins"] != AGE_BINS:
            problems.append(f"{audit['role']} age bins differ from the frozen eight bins")
        for measure in ("finite_k0", "finite_k3", "finite_context_support"):
            if audit[measure] != audit["eligible_rows"]:
                problems.append(f"{audit['role']} has nonfinite {measure} rows")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "scientific_unit": "eligible utterance occurrence collapsed to child-age-effort-k0-density model cells",
        "roles": list(ROLES),
        "role_audits": role_audits,
        "recurrent_type_gate": {
            "min_occurrences": min_type_occurrences,
            "min_children": min_type_children,
            "min_corpora": min_type_corpora,
        },
        "problems": problems,
    }
    if problems:
        raise RuntimeError("; ".join(problems))
    audit_path = dataset_dir / "dataset_audit.json"
    atomic_json(audit, audit_path)
    manifest = {
        "stage": "datasets",
        "status": "complete",
        "inputs": {
            "controller": file_record(Path(__file__)),
            "child_wide": file_record(child_input),
            "caretaker_wide": file_record(caretaker_input),
        },
        "outputs": {
            "model_cells": file_record(cells_path),
            "recurrent_utterance_types": file_record(types_path),
            "audit": file_record(audit_path),
        },
        "audit": audit,
    }
    atomic_json(manifest, dataset_dir / "dataset_manifest.json")
    return manifest


def _validate_existing_inventories(route1: pd.DataFrame, route2: pd.DataFrame) -> None:
    route1_required = {
        "P1_k3_contextual",
        "P2_k0_unconditional",
        "P3_k3_context_gain",
        "C1_caretaker_k3_contextual",
        "C2_caretaker_k0_unconditional",
        "C3_caretaker_k3_context_gain",
    }
    route2_required = {
        "m1_length_primary",
        "m2_length_qwen_reference",
        "m4_effort_percentile",
        "m5_exact_length_k3_gap",
    }
    missing_route1 = route1_required - set(route1["model_id"].astype(str))
    missing_route2 = route2_required - set(route2["model_id"].astype(str))
    if missing_route1:
        raise RuntimeError(f"Route 1 inventory missing registered fits: {sorted(missing_route1)}")
    if missing_route2:
        raise RuntimeError(f"Route 2 inventory missing registered fits: {sorted(missing_route2)}")
    route1_status = "fit_status" if "fit_status" in route1 else "status"
    if route1.loc[route1["model_id"].isin(route1_required), route1_status].isin(["FAIL"]).any():
        raise RuntimeError("Route 1 required inventory contains failed fits")
    if route2.loc[route2["model_id"].isin(route2_required), "status"].ne("PASS").any():
        raise RuntimeError("Route 2 required inventory contains non-PASS fits")


def run_models_stage(output_dir: Path, route1_models: Path, route2_models: Path) -> dict[str, Any]:
    dataset_dir = output_dir / "datasets"
    model_dir = output_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    cells_path = dataset_dir / "model_cells.csv.gz"
    types_path = dataset_dir / "recurrent_utterance_types.csv.gz"
    cells = pd.read_csv(cells_path)
    recurring = pd.read_csv(types_path)
    route1 = pd.read_csv(route1_models)
    route2 = pd.read_csv(route2_models)
    _validate_existing_inventories(route1, route2)

    registries: list[dict[str, Any]] = []
    standardized_frames = []
    coefficient_frames = []
    contrast_frames = []
    for role in ROLES:
        for scope in SCOPES:
            for outcome in (
                "k3_total_mean",
                "k0_total_mean",
                "context_gain_total_mean",
                "k3_density_mean",
            ):
                registry, estimates = fit_standardized_outcome(
                    cells, role=role, scope=scope, outcome=outcome
                )
                registries.append(registry)
                standardized_frames.append(estimates)
            registry, coefficients, contrasts = fit_frequency_informativity_coupling(
                cells, role=role, scope=scope
            )
            registries.append(registry)
            coefficient_frames.append(coefficients)
            contrast_frames.append(contrasts)

    route1_keep = route1[
        route1["model_id"].astype(str).str.match(r"^(P1|P2|P3|C1|C2|C3)")
    ].copy()
    route2_keep = route2[
        route2["model_id"].isin(
            [
                "m1_length_primary",
                "m2_length_qwen_reference",
                "m3_information_k3_total",
                "m3b_information_k3_per_token",
                "m3c_information_k0_total",
                "m3d_context_support",
                "m4_effort_percentile",
                "m5_exact_length_k3_gap",
            ]
        )
    ].copy()
    outputs = {
        "model_registry": model_dir / "model_registry.csv",
        "standardized_age_informativity": model_dir / "standardized_age_informativity.csv",
        "frequency_informativity_coefficients": model_dir / "frequency_informativity_coefficients.csv",
        "frequency_informativity_age_contrasts": model_dir / "frequency_informativity_age_contrasts.csv",
        "existing_route1_inventory": model_dir / "existing_route1_inventory.csv",
        "existing_route2_inventory": model_dir / "existing_route2_inventory.csv",
    }
    atomic_csv(pd.DataFrame(registries), outputs["model_registry"])
    atomic_csv(pd.concat(standardized_frames, ignore_index=True), outputs["standardized_age_informativity"])
    atomic_csv(pd.concat(coefficient_frames, ignore_index=True), outputs["frequency_informativity_coefficients"])
    atomic_csv(pd.concat(contrast_frames, ignore_index=True), outputs["frequency_informativity_age_contrasts"])
    atomic_csv(route1_keep, outputs["existing_route1_inventory"])
    atomic_csv(route2_keep, outputs["existing_route2_inventory"])
    registry_frame = pd.DataFrame(registries)
    audit = {
        "status": "PASS" if registry_frame["status"].eq("PASS").all() else "FAIL",
        "new_registered_models": len(registry_frame),
        "standardized_models": int(registry_frame["model_id"].str.startswith("standardized_").sum()),
        "coupling_models": int(registry_frame["model_id"].str.startswith("coupling_").sum()),
        "standardized_rows": int(sum(len(frame) for frame in standardized_frames)),
        "coupling_contrast_rows": int(sum(len(frame) for frame in contrast_frames)),
        "recurrent_types_available": len(recurring),
        "existing_route1_rows_retained": len(route1_keep),
        "existing_route2_rows_retained": len(route2_keep),
    }
    if audit["status"] != "PASS":
        raise RuntimeError("one or more registered informativity models failed")
    audit_path = model_dir / "models_audit.json"
    atomic_json(audit, audit_path)
    manifest = {
        "stage": "models",
        "status": "complete",
        "inputs": {
            "controller": file_record(Path(__file__)),
            "model_cells": file_record(cells_path),
            "recurrent_types": file_record(types_path),
            "route1_models": file_record(route1_models),
            "route2_models": file_record(route2_models),
        },
        "outputs": {key: file_record(path) for key, path in outputs.items()} | {"audit": file_record(audit_path)},
        "audit": audit,
    }
    atomic_json(manifest, model_dir / "models_manifest.json")
    return manifest


def _markdown_table(frame: pd.DataFrame, columns: Sequence[str], max_rows: int | None = None) -> str:
    selected = frame.loc[:, [column for column in columns if column in frame]].copy()
    if max_rows is not None:
        selected = selected.head(max_rows)
    for column in selected.select_dtypes(include=["float"]).columns:
        selected[column] = selected[column].map(lambda value: "" if not math.isfinite(value) else f"{value:.4g}")
    header = "| " + " | ".join(selected.columns) + " |"
    separator = "| " + " | ".join("---" for _ in selected.columns) + " |"
    rows = ["| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in selected.itertuples(index=False, name=None)]
    return "\n".join([header, separator, *rows])


def run_report_stage(output_dir: Path, report_md: Path, report_html: Path) -> dict[str, Any]:
    model_dir = output_dir / "models"
    dataset_dir = output_dir / "datasets"
    standardized = pd.read_csv(model_dir / "standardized_age_informativity.csv")
    coefficients = pd.read_csv(model_dir / "frequency_informativity_coefficients.csv")
    route1 = pd.read_csv(model_dir / "existing_route1_inventory.csv")
    route2 = pd.read_csv(model_dir / "existing_route2_inventory.csv")
    recurring = pd.read_csv(dataset_dir / "recurrent_utterance_types.csv.gz")
    dataset_audit = json.loads((dataset_dir / "dataset_audit.json").read_text(encoding="utf-8"))
    role_audits = {item["role"]: item for item in dataset_audit["role_audits"]}
    coupling = coefficients[coefficients["term"].eq("age_c:k0_density_mean")].copy()
    coupling[["role", "analysis_scope"]] = coupling["model_id"].str.extract(
        r"^coupling_(child|caretaker)_(.+)$"
    )
    primary_standardized = standardized[
        standardized["analysis_scope"].eq("all79_descriptive")
        & standardized["outcome"].isin(["k3_total_mean", "k0_total_mean", "context_gain_total_mean"])
    ].copy()
    primary_standardized["estimand"] = primary_standardized["outcome"].map(
        {
            "k3_total_mean": "contextual informativity (k3)",
            "k0_total_mean": "unconditional form information (k0)",
            "context_gain_total_mean": "context support (k0-k3)",
        }
    )
    route1_columns = [
        "scope",
        "model_id",
        "tier",
        "age_estimate",
        "age_ci_low",
        "age_ci_high",
        "fit_status",
        "protocol_result",
    ]
    route1_base = route1[route1["model_id"].isin(
        [
            "P1_k3_contextual",
            "P2_k0_unconditional",
            "P3_k3_context_gain",
            "C1_caretaker_k3_contextual",
            "C2_caretaker_k0_unconditional",
            "C3_caretaker_k3_context_gain",
        ]
    )]
    route2_columns = [
        "analysis_scope",
        "model_id",
        "outcome",
        "family",
        "n_rows",
        "deviance_explained",
        "status",
    ]
    recurring_columns = [
        "role",
        "target_text",
        "occurrences",
        "children",
        "corpora",
        "word_count",
        "empirical_frequency_bits",
        "mean_k3_total_bits",
        "mean_context_support_bits",
    ]
    recurring_display = (
        recurring.sort_values(["role", "occurrences"], ascending=[True, False])
        .groupby("role", observed=True, group_keys=False)
        .head(15)
    )
    markdown = f"""# Utterance Informativity: Route 1 and Route 2

This report treats utterances as the primary unit. It leverages the distinction
between unconditional frequency and contextual predictability without
reproducing a phone-level analysis.

## Definitions

```text
k0 = -log2 p_Mistral(utterance)
k3 = -log2 p_Mistral(utterance | preceding three utterances)
context support = k0 - k3
```

One occurrence's k3 score is contextual self-information. The developmental
informativity summaries below are adjusted mean k3 scores after every age bin
is standardized to the same pooled exact/top-coded word-effort distribution.
Lower values mean greater Mistral predictability, not more meaning transmitted.

The total-bit models retain {role_audits['child']['eligible_rows']:,} child and
{role_audits['caretaker']['eligible_rows']:,} caregiver utterances. The
k0-versus-k3 density coupling requires identical positive evaluation-token
counts and therefore uses {role_audits['child']['density_pair_rows']:,} child
and {role_audits['caretaker']['density_pair_rows']:,} caregiver rows; the
{role_audits['child']['density_pair_excluded']:,} and
{role_audits['caretaker']['density_pair_excluded']:,} excluded rows remain in
the valid total-bit analyses.

## Existing Route 1 models retained

{_markdown_table(route1_base, route1_columns)}

These are the frozen fixed-effort P1/P2/P3 child models and C1/C2/C3 caregiver
comparisons. The new terminology does not change their original outcomes,
sample roles, intervals, or protocol decisions.

## Effort-standardized utterance informativity

{_markdown_table(primary_standardized, ["role", "estimand", "age_bin", "estimate", "ci_low", "ci_high"])}

Formula for each saved outcome:

```text
cell mean ~ age bin + exact/top-coded word count + child identity
```

The estimates average the fitted cells over the same scope/role-pooled effort
distribution and the same scope-specific child reference population.

## Developmental frequency-informativity coupling

{_markdown_table(coupling, ["role", "analysis_scope", "estimate", "std_error", "ci_low", "ci_high", "p_value"])}

The displayed term is `age:k0 density` from the registered nonlinear cell
model. It asks whether unconditional and contextual scorer predictability
become more or less coupled with age. Shared Mistral scoring creates mechanical
association between k0 and k3, so the interaction and separate context-support
trajectory are the relevant quantities.

## Existing Route 2 and joint models retained

{_markdown_table(route2, route2_columns)}

Route 2 remains the effort-adaptation analysis. Raw effort (`m1`), the separate
Qwen expected-length sensitivity (`m2`), generated-relative effort percentile
(`m4`), and exact-length information calibration (`m5`) are distinct
estimands. Same-length n-gram or LSTM candidates are not effort baselines.

## Recurrent exact utterance types

The table below uses exact strings with at least 100 occurrences, 10 children,
and 3 corpora. Type informativity is mean k3 across attested contexts.

{_markdown_table(recurring_display, recurring_columns)}

## Interpretation limits

- Lower k3 means greater scorer predictability, not greater Shannon information
  transmitted.
- k0 is unconditional Mistral self-information, not empirical frequency. The
  recurrent table contains the separate empirical recurrence measure.
- The analysis does not measure semantic informativeness or listener utility.
- Exact-string Qwen entropy is not semantic response uncertainty.
- Generated responses are not meaning-preserving alternatives.
- PBM discovery, non-PBM confirmation, and all-79 descriptive estimates remain
  separate.
"""
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(markdown, encoding="utf-8")
    from render_markdown_report import render_markdown_file

    render_markdown_file(report_md, report_html, title="Utterance Informativity: Route 1 and Route 2")
    audit = {
        "status": "PASS",
        "standardized_rows_rendered": len(primary_standardized),
        "coupling_models_rendered": len(coupling),
        "route1_rows_rendered": len(route1_base),
        "route2_rows_rendered": len(route2),
        "recurrent_types_available": len(recurring),
    }
    report_dir = output_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    audit_path = report_dir / "report_audit.json"
    atomic_json(audit, audit_path)
    manifest = {
        "stage": "report",
        "status": "complete",
        "inputs": {
            "controller": file_record(Path(__file__)),
            "models_manifest": file_record(model_dir / "models_manifest.json"),
            "dataset_manifest": file_record(dataset_dir / "dataset_manifest.json"),
        },
        "outputs": {"markdown": file_record(report_md), "html": file_record(report_html), "audit": file_record(audit_path)},
        "audit": audit,
    }
    atomic_json(manifest, report_dir / "report_manifest.json")
    return manifest


def _verify_records(section: dict[str, Any], problems: list[str], label: str) -> None:
    for name, record in section.items():
        if not isinstance(record, dict) or "path" not in record or "sha256" not in record:
            continue
        path = Path(record["path"])
        if not path.exists():
            problems.append(f"{label}.{name} is missing: {path}")
            continue
        if sha256_file(path) != record["sha256"]:
            problems.append(f"{label}.{name} hash mismatch: {path}")


def run_audit_stage(output_dir: Path, report_md: Path, report_html: Path) -> dict[str, Any]:
    required_manifests = [
        output_dir / "datasets/dataset_manifest.json",
        output_dir / "models/models_manifest.json",
        output_dir / "report/report_manifest.json",
    ]
    problems = []
    manifests = []
    for path in required_manifests:
        if not path.exists():
            problems.append(f"missing manifest: {path}")
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifests.append(manifest)
        if manifest.get("audit", {}).get("status") != "PASS":
            problems.append(f"non-PASS stage audit: {path}")
        _verify_records(manifest.get("inputs", {}), problems, f"{manifest.get('stage')}.inputs")
        _verify_records(manifest.get("outputs", {}), problems, f"{manifest.get('stage')}.outputs")
    registry_path = output_dir / "models/model_registry.csv"
    standardized_path = output_dir / "models/standardized_age_informativity.csv"
    contrasts_path = output_dir / "models/frequency_informativity_age_contrasts.csv"
    recurring_path = output_dir / "datasets/recurrent_utterance_types.csv.gz"
    for path in (registry_path, standardized_path, contrasts_path, recurring_path, report_md, report_html):
        if not path.exists():
            problems.append(f"missing required output: {path}")
    registry = pd.read_csv(registry_path) if registry_path.exists() else pd.DataFrame()
    standardized = pd.read_csv(standardized_path) if standardized_path.exists() else pd.DataFrame()
    contrasts = pd.read_csv(contrasts_path) if contrasts_path.exists() else pd.DataFrame()
    recurring = pd.read_csv(recurring_path) if recurring_path.exists() else pd.DataFrame()
    if len(registry) != 30 or not registry.get("status", pd.Series(dtype=str)).eq("PASS").all():
        problems.append(f"registered model gate failed: expected 30 PASS rows, found {len(registry)}")
    if len(standardized) != 192:
        problems.append(f"standardized-row gate failed: expected 192, found {len(standardized)}")
    if len(contrasts) != 48:
        problems.append(f"coupling-contrast gate failed: expected 48, found {len(contrasts)}")
    if set(recurring.get("role", pd.Series(dtype=str))) != set(ROLES):
        problems.append("recurrent-type table does not cover child and caretaker roles")
    if not standardized.empty and not np.isfinite(
        standardized[["estimate", "std_error", "ci_low", "ci_high"]].to_numpy(dtype=float)
    ).all():
        problems.append("nonfinite standardized estimates")
    report_text = report_md.read_text(encoding="utf-8") if report_md.exists() else ""
    for phrase in (
        "Route 1",
        "Route 2",
        "not more meaning transmitted",
        "not semantic response uncertainty",
        "not meaning-preserving alternatives",
    ):
        if phrase not in report_text:
            problems.append(f"report interpretation label missing: {phrase}")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "problems": problems,
        "registered_models": len(registry),
        "standardized_rows": len(standardized),
        "coupling_contrast_rows": len(contrasts),
        "recurrent_types": len(recurring),
        "roles": sorted(recurring["role"].unique().tolist()) if "role" in recurring else [],
        "report_sha256": sha256_file(report_md) if report_md.exists() else None,
        "html_sha256": sha256_file(report_html) if report_html.exists() else None,
    }
    audit_dir = output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "final_audit.json"
    atomic_json(audit, audit_path)
    marker = output_dir / "UTTERANCE_INFORMATIVITY_COMPLETE_AND_AUDITED"
    if problems:
        if marker.exists():
            marker.unlink()
        raise RuntimeError("; ".join(problems))
    marker.write_text(
        "STATUS=PASS\n"
        f"AUDIT_SHA256={sha256_file(audit_path)}\n"
        f"REGISTERED_MODELS={len(registry)}\n"
        f"STANDARDIZED_ROWS={len(standardized)}\n"
        f"COUPLING_CONTRAST_ROWS={len(contrasts)}\n",
        encoding="utf-8",
    )
    return audit


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["datasets", "models", "report", "audit", "all"], default="all")
    parser.add_argument("--child-input", type=Path, default=DEFAULT_CHILD)
    parser.add_argument("--caretaker-input", type=Path, default=DEFAULT_CARETAKER)
    parser.add_argument("--route1-models", type=Path, default=DEFAULT_ROUTE1_MODELS)
    parser.add_argument("--route2-models", type=Path, default=DEFAULT_ROUTE2_MODELS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--chunksize", type=int, default=200_000)
    parser.add_argument("--min-type-occurrences", type=int, default=100)
    parser.add_argument("--min-type-children", type=int, default=10)
    parser.add_argument("--min-type-corpora", type=int, default=3)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stages = ["datasets", "models", "report", "audit"] if args.stage == "all" else [args.stage]
    for stage in stages:
        print(f"[{stage}] starting", flush=True)
        if stage == "datasets":
            run_datasets_stage(
                args.output_dir,
                args.child_input,
                args.caretaker_input,
                chunksize=args.chunksize,
                min_type_occurrences=args.min_type_occurrences,
                min_type_children=args.min_type_children,
                min_type_corpora=args.min_type_corpora,
            )
        elif stage == "models":
            run_models_stage(args.output_dir, args.route1_models, args.route2_models)
        elif stage == "report":
            run_report_stage(args.output_dir, args.report_md, args.report_html)
        elif stage == "audit":
            run_audit_stage(args.output_dir, args.report_md, args.report_html)
        print(f"[{stage}] complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
