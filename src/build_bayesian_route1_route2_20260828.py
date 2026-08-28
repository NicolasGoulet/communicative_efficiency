#!/usr/bin/env python3
"""Staged Bayesian Route 1 / Route 2 robustness program.

The production controller is deliberately fail-closed.  In particular, no
full posterior fit is launched until immutable data, priors, synthetic
recovery, and a representative real-data resource pilot have all passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import statsmodels.api as sm
import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "configs/bayesian_route1_route2_20260828/analysis_contract.json"
DEFAULT_OUTPUT = ROOT / "results/bayesian_route1_route2_20260828"
DEFAULT_FIGURES = ROOT / "figs/bayesian_route1_route2_20260828"
DEFAULT_REPORT_MD = ROOT / "docs/bayesian_route1_route2_report.md"
DEFAULT_REPORT_HTML = ROOT / "docs/bayesian_route1_route2_report.html"

SAMPLE_SCOPES = ("pbm_discovery", "non_pbm_replication", "all79_descriptive")
MODEL_FAMILIES = ("B1", "B2", "B3", "B4", "B5")
AGE_SHAPES = ("linear", "quadratic", "low_rank_smooth")
PRIOR_SETS = ("weak", "skeptical", "wide")
PBM_DATASETS = ("Brown", "Manchester", "Providence")
CONTEXT_CONDITIONS = ("k0", "k1", "k2", "k3")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunksize: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunksize):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_text(value: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def atomic_json(value: Mapping[str, Any], path: Path) -> None:
    atomic_text(json.dumps(value, indent=2, sort_keys=True) + "\n", path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def atomic_csv_gzip(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(
        temporary,
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 6, "mtime": 0},
    )
    os.replace(temporary, path)


def file_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def configure_duckdb(connection: duckdb.DuckDBPyConnection, temp_dir: Path, memory_limit: str) -> None:
    temp_dir.mkdir(parents=True, exist_ok=True)
    connection.execute(f"SET memory_limit={sql_literal(memory_limit)}")
    connection.execute("SET threads=4")
    connection.execute("SET preserve_insertion_order=false")
    connection.execute("SET temp_directory=?", [str(temp_dir)])


def copy_parquet(connection: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    connection.execute(
        f"COPY ({query}) TO ? (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)",
        [str(temporary)],
    )
    os.replace(temporary, path)


def write_manifest(
    *,
    stage: str,
    manifest_path: Path,
    inputs: Mapping[str, Path],
    outputs: Mapping[str, Path],
    audit: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stage": stage,
        "completed_at": utc_now(),
        "controller_sha256": sha256_file(Path(__file__)),
        "inputs": {name: file_record(path) for name, path in inputs.items()},
        "outputs": {name: file_record(path) for name, path in outputs.items()},
        "audit": dict(audit),
    }
    if extra:
        payload.update(extra)
    atomic_json(payload, manifest_path)
    return payload


def require_manifest(path: Path, stage: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing {stage} manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("stage") != stage:
        raise RuntimeError(f"expected {stage} manifest, found {payload.get('stage')}")
    for direction in ("inputs", "outputs"):
        for name, record in payload.get(direction, {}).items():
            target = Path(record["path"])
            if not target.exists() or sha256_file(target) != record["sha256"]:
                label = "input" if direction == "inputs" else "output"
                raise RuntimeError(f"stale {stage} {label}: {name} ({target})")
    return payload


def validate_contract_payload(contract: Mapping[str, Any]) -> None:
    problems: list[str] = []
    if tuple(contract.get("sample_scopes", [])) != SAMPLE_SCOPES:
        problems.append("sample_scopes do not match the frozen roles")
    if tuple(contract.get("model_families", [])) != MODEL_FAMILIES:
        problems.append("model_families must be exactly B1-B5")
    if tuple(contract.get("age_shapes", [])) != AGE_SHAPES:
        problems.append("age_shapes registry is incomplete")
    if tuple(contract.get("prior_sets", [])) != PRIOR_SETS:
        problems.append("prior_sets registry is incomplete")
    if not contract.get("backend_lock", {}).get("path") or not contract.get("backend_lock", {}).get("sha256"):
        problems.append("backend_lock path/hash is missing")
    scope_datasets = contract.get("scope_datasets", {})
    if tuple(scope_datasets.get("pbm_discovery", [])) != PBM_DATASETS:
        problems.append("scope_datasets changed for pbm_discovery")
    all79 = set(scope_datasets.get("all79_descriptive", []))
    non_pbm = set(scope_datasets.get("non_pbm_replication", []))
    if set(PBM_DATASETS) & non_pbm or set(PBM_DATASETS) | non_pbm != all79:
        problems.append("scope_datasets are not a disjoint 3-corpus/10-corpus split")
    priors = contract.get("priors", {})
    for prior_set in PRIOR_SETS:
        if prior_set not in priors:
            problems.append(f"missing prior set: {prior_set}")
    families = contract.get("families", {})
    for family in MODEL_FAMILIES:
        record = families.get(family, {})
        for key in ("formula", "contrasts", "diagnostics", "synthetic_truth", "variants"):
            if not record.get(key):
                problems.append(f"{family} missing {key}")
    for key in ("bits_six_month", "words_six_month", "rank_percentile_six_month"):
        if float(contract.get("ropes", {}).get(key, 0)) <= 0:
            problems.append(f"missing positive ROPE: {key}")
    if problems:
        raise ValueError("invalid Bayesian contract: " + "; ".join(problems))


def load_and_validate_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    validate_contract_payload(contract)
    return contract


def audit_route1_pairs(frame: pd.DataFrame) -> dict[str, int]:
    required = {"utterance_id", "condition", "mean_bits"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"route1 pair table missing columns: {sorted(missing)}")
    duplicates = frame.duplicated(["utterance_id", "condition"], keep=False)
    if duplicates.any():
        raise ValueError(f"duplicate utterance-condition identities: {int(duplicates.sum())}")
    conditions = frame.groupby("utterance_id", observed=True).condition.agg(lambda x: tuple(sorted(x)))
    expected = tuple(CONTEXT_CONDITIONS)
    incomplete = int((conditions != expected).sum())
    if incomplete:
        raise ValueError(f"complete k0-k3 pairing failed for {incomplete} utterances")
    if not np.isfinite(pd.to_numeric(frame.mean_bits, errors="coerce")).all():
        raise ValueError("route1 pairs contain non-finite scores")
    return {"utterances": int(conditions.size), "long_rows": int(len(frame))}


def aggregate_route1_cells(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    pair_audit = audit_route1_pairs(frame)
    group_columns = [
        "dataset", "child_key", "session_id", "age_months",
        "word_count_top12", "condition",
    ]
    missing = set(group_columns) - set(frame.columns)
    if missing:
        raise ValueError(f"route1 aggregation missing columns: {sorted(missing)}")
    grouped = frame.groupby(group_columns, observed=True, dropna=False).mean_bits
    cells = grouped.agg(cell_mean_bits="mean", cell_sd_bits="std", cell_n="size").reset_index()
    cells["cell_sd_bits"] = cells.cell_sd_bits.fillna(0.0)
    cells["cell_se_bits"] = cells.cell_sd_bits / np.sqrt(cells.cell_n)
    weighted = float(np.average(cells.cell_mean_bits, weights=cells.cell_n))
    raw = float(frame.mean_bits.mean())
    if not np.isclose(weighted, raw, rtol=0, atol=1e-12):
        raise ValueError("exact cell aggregation mean audit failed")
    return cells, {
        **pair_audit,
        "cells": int(len(cells)),
        "raw_long_rows": int(len(frame)),
        "weighted_mean": weighted,
        "raw_mean": raw,
        "singleton_cells": int((cells.cell_n == 1).sum()),
    }


def add_rank200(frame: pd.DataFrame, tolerance: float = 1e-9) -> tuple[pd.DataFrame, dict[str, Any]]:
    column = "effort_percentile_in_qwen"
    if column not in frame:
        raise ValueError(f"missing {column}")
    result = frame.copy()
    values = pd.to_numeric(result[column], errors="coerce").to_numpy(float)
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError("effort percentiles must be finite on [0,1]")
    scaled = 200.0 * values
    rounded = np.rint(scaled)
    error = float(np.max(np.abs(scaled - rounded), initial=0.0))
    if error > tolerance:
        raise ValueError(f"rank200 grid mismatch: maximum error {error}")
    result["rank200"] = rounded.astype(np.int16)
    return result, {
        "rows": int(len(result)),
        "zero_endpoints": int(np.sum(values == 0.0)),
        "one_endpoints": int(np.sum(values == 1.0)),
        "max_rank200_rounding_error": error,
    }


def estimate_shared_bootstrap_slopes(
    frame: pd.DataFrame,
    *,
    bootstrap_draws: int = 100,
    seed: int = 20260828,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    required = {
        "child_key", "dataset", "age_z", "word_count_top12", "k3_bits",
        "child_words", "entropy_z", "context_words_z",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"B5 shared-bootstrap table missing columns: {sorted(missing)}")
    if frame.duplicated(["child_key", "utterance_id"]).any():
        raise ValueError("B5 shared-bootstrap table has duplicated child/utterance identities")
    if bootstrap_draws < 20:
        raise ValueError("B5 shared bootstrap requires at least 20 draws")

    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    problems: list[str] = []
    for child_key, child in frame.groupby("child_key", sort=True, observed=True):
        child = child.reset_index(drop=True)
        if child.dataset.nunique() != 1:
            problems.append(f"{child_key}: multiple corpora")
            continue
        word_dummies = pd.get_dummies(
            child.word_count_top12.astype(str), prefix="word", drop_first=True, dtype=float
        )
        x1 = np.column_stack([
            np.ones(len(child)),
            child.age_z.to_numpy(float),
            word_dummies.to_numpy(float),
        ])
        x2 = np.column_stack([
            np.ones(len(child)),
            child.age_z.to_numpy(float),
            child.entropy_z.to_numpy(float),
            (child.age_z * child.entropy_z).to_numpy(float),
            child.context_words_z.to_numpy(float),
        ])
        y1 = child.k3_bits.to_numpy(float)
        y2 = np.log1p(child.child_words.to_numpy(float))
        if len(child) <= max(x1.shape[1], x2.shape[1]) + 10:
            problems.append(f"{child_key}: insufficient rows")
            continue
        if np.linalg.matrix_rank(x1) != x1.shape[1] or np.linalg.matrix_rank(x2) != x2.shape[1]:
            problems.append(f"{child_key}: rank-deficient shared-bootstrap design")
            continue
        estimate1 = np.linalg.lstsq(x1, y1, rcond=None)[0][1]
        estimate2 = np.linalg.lstsq(x2, y2, rcond=None)[0][3]
        draws: list[tuple[float, float]] = []
        for _ in range(bootstrap_draws):
            indices = rng.integers(0, len(child), size=len(child))
            bx1 = x1[indices]
            bx2 = x2[indices]
            slope1 = np.linalg.lstsq(bx1, y1[indices], rcond=None)[0][1]
            slope2 = np.linalg.lstsq(bx2, y2[indices], rcond=None)[0][3]
            if np.isfinite(slope1) and np.isfinite(slope2):
                draws.append((float(slope1), float(slope2)))
        if len(draws) < max(20, int(0.9 * bootstrap_draws)):
            problems.append(f"{child_key}: only {len(draws)} valid shared bootstrap draws")
            continue
        covariance = np.cov(np.asarray(draws), rowvar=False, ddof=1)
        minimum_eigenvalue = float(np.linalg.eigvalsh(covariance).min())
        if minimum_eigenvalue <= 1e-12:
            covariance = covariance + np.eye(2) * (1e-12 - minimum_eigenvalue + 1e-12)
        rows.append({
            "child_key": child_key,
            "dataset": str(child.dataset.iloc[0]),
            "r1_slope": float(estimate1),
            "r2_slope": float(estimate2),
            "r1_se": float(np.sqrt(covariance[0, 0])),
            "r2_se": float(np.sqrt(covariance[1, 1])),
            "r1_r2_cov": float(covariance[0, 1]),
            "bootstrap_draws": len(draws),
            "source_rows": len(child),
        })
    if problems:
        raise ValueError("B5 shared bootstrap failed: " + "; ".join(problems))
    result = pd.DataFrame(rows)
    for record in result.itertuples(index=False):
        determinant = record.r1_se**2 * record.r2_se**2 - record.r1_r2_cov**2
        if not np.isfinite(determinant) or determinant <= 0:
            raise ValueError(f"B5 non-positive-definite estimation covariance: {record.child_key}")
    return result, {
        "status": "PASS",
        "children": int(len(result)),
        "corpora": int(result.dataset.nunique()),
        "bootstrap_draws_requested": bootstrap_draws,
        "bootstrap_draws_minimum": int(result.bootstrap_draws.min()),
        "source_rows": int(result.source_rows.sum()),
        "estimand_r1": "within-child k3 fixed-word age slope per six months",
        "estimand_r2": "within-child log1p-word age-by-response-entropy slope",
        "shared_resampling": True,
    }


def _age_expression(shape: str) -> str:
    return {
        "linear": "age_z",
        "quadratic": "age_z + I(age_z^2)",
        "low_rank_smooth": "s(age_z, k=5)",
    }[shape]


def build_registered_fit_inventory(contract: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family in MODEL_FAMILIES:
        family_record = contract["families"][family]
        for variant in family_record["variants"]:
            for age_shape in AGE_SHAPES:
                formula = family_record["formula"].replace("AGE", _age_expression(age_shape))
                if variant != family_record["variants"][0] and family_record.get("sensitivity_formula"):
                    formula += " " + family_record["sensitivity_formula"]
                formula_hash = sha256_text(formula)
                for prior_set in PRIOR_SETS:
                    for sample_scope in SAMPLE_SCOPES:
                        rows.append({
                            "fit_id": f"{family}__{variant}__{sample_scope}__{age_shape}__{prior_set}",
                            "model_family": family,
                            "variant": variant,
                            "sample_scope": sample_scope,
                            "age_shape": age_shape,
                            "prior_set": prior_set,
                            "formula": formula,
                            "formula_sha256": formula_hash,
                            "family": family_record["family"],
                        })
    return pd.DataFrame(rows)


def synthetic_likelihood_recovery(seed: int = 20260828) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    records: dict[str, dict[str, Any]] = {}

    n = 16000
    age = rng.normal(size=n)
    condition = rng.integers(0, 4, size=n)
    offsets = np.array([0.0, -2.0, -3.0, -4.0])
    slopes = np.array([-0.2, -0.25, -0.3, -0.35])
    design = np.column_stack([
        np.ones(n),
        *(condition == level for level in range(1, 4)),
        *(age * (condition == level) for level in range(4)),
    ]).astype(float)
    outcome = 35.0 + offsets[condition] + slopes[condition] * age + rng.standard_t(7, n) * 0.4
    estimate = np.linalg.lstsq(design, outcome, rcond=None)[0]
    context_error = float(np.max(np.abs(estimate[1:4] - offsets[1:4])))
    records["B1"] = {"status": "PASS" if context_error < 0.35 else "FAIL", "max_context_error": context_error, "problems": [] if context_error < 0.35 else ["context recovery"]}

    n = 30000
    age = rng.uniform(-2, 2, n)
    mean = 25.0 - 0.35 * age
    sigma = np.exp(1.2 - 0.12 * age)
    outcome = mean + sigma * rng.standard_t(7, n)
    mean_fit = np.linalg.lstsq(np.column_stack([np.ones(n), age]), outcome, rcond=None)[0]
    residual = outcome - np.column_stack([np.ones(n), age]) @ mean_fit
    scale_fit = np.linalg.lstsq(np.column_stack([np.ones(n), age]), np.log(np.abs(residual) + 1e-6), rcond=None)[0]
    dispersion_error = float(abs(scale_fit[1] - (-0.12)))
    records["B2"] = {"status": "PASS" if dispersion_error < 0.15 else "FAIL", "dispersion_age_error": dispersion_error, "problems": [] if dispersion_error < 0.15 else ["dispersion recovery"]}

    n = 25000
    age = rng.normal(size=n)
    entropy = rng.normal(size=n)
    interaction = age * entropy
    x = np.column_stack([np.ones(n), age, entropy, interaction])
    truth = np.array([0.8, 0.1, 0.15, -0.12])
    mu = np.exp(x @ truth)
    latent_rate = rng.gamma(shape=3.0, scale=mu / 3.0)
    counts = rng.poisson(latent_rate)
    count_fit = sm.GLM(counts, x, family=sm.families.NegativeBinomial(alpha=1 / 3.0)).fit()
    count_error = float(np.max(np.abs(count_fit.params - truth)))
    records["B3"] = {"status": "PASS" if count_error < 0.12 else "FAIL", "max_count_coefficient_error": count_error, "problems": [] if count_error < 0.12 else ["count recovery"]}

    n = 40000
    endpoint = rng.binomial(1, 0.22, n).astype(bool)
    upper = rng.binomial(1, 0.45, n)
    interior = rng.beta(8, 10, n)
    rank = np.where(endpoint, upper * 200, rng.binomial(200, interior))
    endpoint_estimate = float(np.mean((rank == 0) | (rank == 200)))
    endpoint_error = abs(endpoint_estimate - 0.22)
    records["B4"] = {"status": "PASS" if endpoint_error < 0.03 else "FAIL", "endpoint_probability_error": endpoint_error, "literal_zero": int(np.sum(rank == 0)), "literal_one": int(np.sum(rank == 200)), "problems": [] if endpoint_error < 0.03 else ["endpoint recovery"]}

    covariance = np.array([[0.12**2, -0.4 * 0.12 * 0.10], [-0.4 * 0.12 * 0.10, 0.10**2]])
    slopes_drawn = rng.multivariate_normal([-0.25, 0.1], covariance, size=12000)
    correlation = float(np.corrcoef(slopes_drawn.T)[0, 1])
    correlation_error = abs(correlation - (-0.4))
    records["B5"] = {"status": "PASS" if correlation_error < 0.08 else "FAIL", "correlation_error": correlation_error, "estimated_correlation": correlation, "problems": [] if correlation_error < 0.08 else ["correlation recovery"]}

    status = "PASS" if all(record["status"] == "PASS" for record in records.values()) else "FAIL"
    return {"status": status, "seed": seed, "families": records}


def simulate_prior_predictive_checks(
    contract: Mapping[str, Any], seed: int = 20260828, draws: int = 20000
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for prior_set in PRIOR_SETS:
        prior = contract["priors"][prior_set]
        coefficient_sd = float(prior["coefficient_sd"])
        dispersion_sd = float(prior["dispersion_log_sd"])
        random_sd = float(prior["random_sd"])

        age = rng.uniform(-4, 4, draws)
        bits = rng.normal(32, 12, draws) + rng.normal(0, coefficient_sd, draws) * age
        plausible = float(np.mean((bits > -50) & (bits < 250)))
        rows.append({"model_family": "B1", "prior_set": prior_set, "check": "bits_supported_range", "value": plausible, "threshold": 0.99, "status": "PASS" if plausible >= 0.99 else "FAIL"})

        sigma = np.exp(rng.normal(np.log(8), dispersion_sd, draws))
        plausible = float(np.mean((sigma > 0.05) & (sigma < 150)))
        rows.append({"model_family": "B2", "prior_set": prior_set, "check": "residual_scale_plausibility", "value": plausible, "threshold": 0.95, "status": "PASS" if plausible >= 0.95 else "FAIL"})

        predictor = rng.uniform(-1, 1, (draws, 4))
        coefficients = rng.normal(0, coefficient_sd, (draws, 4))
        mean_words = np.exp(np.log(3) + np.sum(predictor * coefficients, axis=1))
        plausible = float(np.mean((mean_words >= 0.05) & (mean_words <= 100)))
        rows.append({"model_family": "B3", "prior_set": prior_set, "check": "expected_word_count_plausibility", "value": plausible, "threshold": 0.95, "status": "PASS" if plausible >= 0.95 else "FAIL"})

        mu = 1 / (1 + np.exp(-rng.normal(0, coefficient_sd, draws)))
        zoi = 1 / (1 + np.exp(-rng.normal(-1.3, coefficient_sd, draws)))
        plausible = float(np.mean((mu > 0.001) & (mu < 0.999) & (zoi < 0.9)))
        rows.append({"model_family": "B4", "prior_set": prior_set, "check": "rank_and_endpoint_probability_plausibility", "value": plausible, "threshold": 0.95, "status": "PASS" if plausible >= 0.95 else "FAIL"})

        slope = rng.normal(0, random_sd, (draws, 2))
        plausible = float(np.mean(np.max(np.abs(slope), axis=1) < 5.0))
        rows.append({"model_family": "B5", "prior_set": prior_set, "check": "latent_slope_plausibility", "value": plausible, "threshold": 0.95, "status": "PASS" if plausible >= 0.95 else "FAIL"})
    return pd.DataFrame(rows)


def run_priors_stage(args: argparse.Namespace) -> dict[str, Any]:
    dataset_manifest_path = args.output_dir / "datasets/dataset_manifest.json"
    require_manifest(dataset_manifest_path, "datasets")
    contract = load_and_validate_contract(args.contract)
    prior_dir = args.output_dir / "priors"
    prior_dir.mkdir(parents=True, exist_ok=True)
    prior_registry_path = prior_dir / "prior_registry.csv"
    contrast_registry_path = prior_dir / "contrast_registry.csv"
    checks_path = prior_dir / "prior_predictive_checks.csv"
    frozen_path = prior_dir / "frozen_priors.json"
    audit_path = prior_dir / "priors_audit.json"
    manifest_path = prior_dir / "priors_manifest.json"

    prior_rows: list[dict[str, Any]] = []
    for family in MODEL_FAMILIES:
        for prior_set in PRIOR_SETS:
            for parameter, value in contract["priors"][prior_set].items():
                prior_rows.append({
                    "model_family": family,
                    "prior_set": prior_set,
                    "parameter": parameter,
                    "value": value,
                    "scale_contract": "age coefficients are per six months; continuous Route 2 predictors use frozen all-79 z scales",
                })
    atomic_csv(pd.DataFrame(prior_rows), prior_registry_path)

    contrast_rows: list[dict[str, Any]] = []
    for family in MODEL_FAMILIES:
        for contrast in contract["families"][family]["contrasts"]:
            if family in ("B1", "B2"):
                rope_name = "bits_six_month"
            elif family == "B3":
                rope_name = "words_six_month"
            else:
                rope_name = "rank_percentile_six_month"
            contrast_rows.append({
                "model_family": family,
                "contrast": contrast,
                "rope_name": rope_name,
                "rope_half_width": contract["ropes"][rope_name],
            })
    atomic_csv(pd.DataFrame(contrast_rows), contrast_registry_path)

    checks = simulate_prior_predictive_checks(contract)
    atomic_csv(checks, checks_path)
    failed_checks = checks.loc[
        checks.status != "PASS", ["model_family", "prior_set", "check"]
    ].astype(str)
    problems = [
        f"{row['model_family']}: {row['prior_set']}: {row['check']}"
        for row in failed_checks.to_dict(orient="records")
    ]
    frozen = {
        "frozen_at": utc_now(),
        "prior_sets": contract["priors"],
        "ropes": contract["ropes"],
        "age_shapes": list(AGE_SHAPES),
        "seed": 20260828,
        "draws_per_check": 20000,
        "outcomes_inspected_before_freeze": True,
        "posthoc_extension": True,
    }
    atomic_json(frozen, frozen_path)
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "prior_records": len(prior_rows),
        "contrast_records": len(contrast_rows),
        "plausibility_checks": int(len(checks)),
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("prior predictive checks failed: " + "; ".join(problems))
    return write_manifest(
        stage="priors",
        manifest_path=manifest_path,
        inputs={"dataset_manifest": dataset_manifest_path, "tracked_contract": args.contract},
        outputs={
            "prior_registry": prior_registry_path,
            "contrast_registry": contrast_registry_path,
            "prior_predictive_checks": checks_path,
            "frozen_priors": frozen_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def audit_completion_inventory(frame: pd.DataFrame, contract: Mapping[str, Any]) -> dict[str, Any]:
    expected = build_registered_fit_inventory(contract)
    key = ["fit_id"]
    missing = sorted(set(expected.fit_id) - set(frame.get("fit_id", [])))
    problems = [f"missing registered fit: {fit_id}" for fit_id in missing]
    required = {
        "fit_status", "rhat_max", "ess_bulk_min", "ess_tail_min", "divergences",
        "treedepth_saturated", "energy_bfmi_min", "ppc_status", "loo_status", "influence_status",
    }
    absent_columns = sorted(required - set(frame.columns))
    problems.extend(f"missing diagnostic column: {column}" for column in absent_columns)
    if not absent_columns and not frame.empty:
        bad = frame[
            (frame.fit_status != "PASS")
            | (frame.rhat_max > 1.01)
            | (frame.ess_bulk_min < 100)
            | (frame.ess_tail_min < 100)
            | (frame.divergences != 0)
            | (frame.treedepth_saturated != 0)
            | (frame.energy_bfmi_min < 0.3)
            | (frame.ppc_status != "PASS")
            | (frame.loo_status != "PASS")
            | (frame.influence_status != "PASS")
        ]
        problems.extend(f"diagnostic failure: {fit_id}" for fit_id in bad.fit_id.tolist())
    return {"status": "PASS" if not problems else "FAIL", "expected_fits": int(len(expected)), "observed_fits": int(len(frame)), "problems": problems}


def run_r_backend(*args: str, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    script = ROOT / "src/fit_bayesian_route1_route2_models.R"
    return subprocess.run(
        ["Rscript", str(script), "--root", str(ROOT), *args],
        cwd=ROOT,
        env=dict(os.environ, **(env or {})),
        text=True,
        capture_output=True,
        check=False,
    )


def render_report_from_saved_payload(payload: Mapping[str, Any], path: Path) -> None:
    stages = "\n".join(f"- `{name}`: {status}" for name, status in payload.get("stage_status", {}).items())
    guardrails = "\n".join(f"- {item}" for item in payload.get("scientific_guardrails", []))
    body = f"""# Bayesian Route 1 / Route 2 program

Status: **{payload.get('program_status', 'UNKNOWN')}**

This is a post-hoc Bayesian extension with the frozen PBM/non-PBM split. No
posterior scientific result is reported unless every registered fit and
diagnostic has passed the independent audit.

## Stage status

{stages}

## Pilot decision

{payload.get('pilot_decision', 'Not available.')}

## Interpretation guardrails

{guardrails}
"""
    atomic_text(body, path)


def audit_backend_environment(contract: Mapping[str, Any]) -> dict[str, Any]:
    package_names = ("brms", "cmdstanr", "posterior", "loo", "bayesplot")
    local_library = (ROOT / contract["backend"]["library"]).resolve()
    expression = (
        ".libPaths(c(" + json.dumps(str(local_library)) + ", .Library.site, .Library));"
        "for (p in c(" + ",".join(json.dumps(name) for name in package_names) + ")) {"
        "if (requireNamespace(p, quietly=TRUE)) {"
        "cat(p, as.character(packageVersion(p)), normalizePath(find.package(p)), sep='\\t')"
        "} else {cat(p, 'MISSING', 'MISSING', sep='\\t')}; cat('\\n')}"
    )
    environment = dict(os.environ)
    completed = subprocess.run(
        ["Rscript", "-e", expression],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    packages: dict[str, str] = {}
    package_paths: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) == 3:
            name, version, package_path = fields
            packages[name] = version
            package_paths[name] = package_path
    cmdstan_path = ROOT / contract["backend"]["cmdstan_path"]
    expected = {
        "brms": contract["backend"]["brms"],
        "cmdstanr": contract["backend"]["cmdstanr"],
    }
    version_matches = {
        name: packages.get(name) == version for name, version in expected.items()
    }
    local_path_matches = {
        name: Path(package_paths.get(name, "/MISSING")).is_relative_to(local_library)
        for name in package_names
    }
    compilers = {
        name: shutil.which(name) for name in ("make", "g++", "Rscript")
    }
    required_cmdstan_files = tuple(
        cmdstan_path / relative
        for relative in ("bin/stanc", "bin/diagnose", "bin/print", "bin/stansummary")
    )
    ready = (
        completed.returncode == 0
        and all(version_matches.values())
        and all(local_path_matches.values())
        and all(path.is_file() for path in required_cmdstan_files)
        and all(compilers.values())
    )
    return {
        "status": "PASS" if ready else "MISSING_LOCAL_BACKEND",
        "ready": ready,
        "r_command_returncode": completed.returncode,
        "r_stderr": completed.stderr.strip(),
        "r_library": str(local_library),
        "packages": packages,
        "package_paths": package_paths,
        "expected_versions": expected,
        "version_matches": version_matches,
        "local_path_matches": local_path_matches,
        "cmdstan_path": str(cmdstan_path),
        "cmdstan_present": all(path.is_file() for path in required_cmdstan_files),
        "cmdstan_required_files": [str(path) for path in required_cmdstan_files],
        "compilers": compilers,
        "global_install_allowed": False,
    }


def run_contract_stage(args: argparse.Namespace) -> dict[str, Any]:
    contract = load_and_validate_contract(args.contract)
    contract_dir = args.output_dir / "contract"
    contract_dir.mkdir(parents=True, exist_ok=True)
    frozen_path = contract_dir / "analysis_contract.json"
    source_audit_path = contract_dir / "source_audit.json"
    backend_audit_path = contract_dir / "backend_environment.json"
    inventory_path = contract_dir / "registered_fit_inventory.csv"
    audit_path = contract_dir / "contract_audit.json"
    manifest_path = contract_dir / "contract_manifest.json"

    source_records: dict[str, Any] = {}
    problems: list[str] = []
    paper_path = Path(contract["source_paper"]["path"])
    paper_actual = sha256_file(paper_path) if paper_path.exists() else None
    if paper_actual != contract["source_paper"]["sha256"]:
        problems.append("source paper hash mismatch")
    source_records["source_paper"] = {
        "path": str(paper_path),
        "expected_sha256": contract["source_paper"]["sha256"],
        "actual_sha256": paper_actual,
        "match": paper_actual == contract["source_paper"]["sha256"],
    }
    backend_lock_path = ROOT / contract["backend_lock"]["path"]
    backend_lock_actual = sha256_file(backend_lock_path) if backend_lock_path.exists() else None
    backend_lock_match = backend_lock_actual == contract["backend_lock"]["sha256"]
    source_records["backend_lock"] = {
        "path": str(backend_lock_path.resolve()),
        "expected_sha256": contract["backend_lock"]["sha256"],
        "actual_sha256": backend_lock_actual,
        "match": backend_lock_match,
    }
    if not backend_lock_match:
        problems.append("backend lock hash mismatch")
    immutable_paths: dict[str, Path] = {}
    for name, record in contract["inputs"].items():
        path = ROOT / record["path"]
        immutable_paths[name] = path
        actual = sha256_file(path) if path.exists() else None
        match = actual == record["sha256"]
        source_records[name] = {
            "path": str(path.resolve()),
            "expected_sha256": record["sha256"],
            "actual_sha256": actual,
            "match": match,
        }
        if not match:
            problems.append(f"immutable input hash mismatch: {name}")

    atomic_json(contract, frozen_path)
    atomic_json({"status": "PASS" if not problems else "FAIL", "sources": source_records, "problems": problems}, source_audit_path)
    backend = audit_backend_environment(contract)
    atomic_json(backend, backend_audit_path)
    inventory = build_registered_fit_inventory(contract)
    atomic_csv(inventory, inventory_path)
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "problems": problems,
        "starting_git_sha": contract["starting_git_sha"],
        "registered_fits": int(len(inventory)),
        "backend_ready": bool(backend["ready"]),
        "backend_status": backend["status"],
        "posthoc_extension": True,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("contract stage failed: " + "; ".join(problems))
    return write_manifest(
        stage="contract",
        manifest_path=manifest_path,
        inputs={
            "tracked_contract": args.contract,
            "backend_lock": backend_lock_path,
            "source_paper": paper_path,
            **immutable_paths,
        },
        outputs={
            "frozen_contract": frozen_path,
            "source_audit": source_audit_path,
            "backend_audit": backend_audit_path,
            "fit_inventory": inventory_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def run_datasets_stage(args: argparse.Namespace) -> dict[str, Any]:
    contract_manifest_path = args.output_dir / "contract/contract_manifest.json"
    require_manifest(contract_manifest_path, "contract")
    contract = load_and_validate_contract(args.contract)
    source = {name: ROOT / record["path"] for name, record in contract["inputs"].items()}
    dataset_dir = args.output_dir / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    route1_wide = dataset_dir / "route1_paired_wide.parquet"
    route1_long = dataset_dir / "route1_paired_long.parquet"
    route1_cells = dataset_dir / "route1_condition_cells.parquet"
    route2_rows = dataset_dir / "route2_rows.parquet"
    b5_rows = dataset_dir / "b5_shared_utterance_rows.parquet"
    flow_path = dataset_dir / "sample_flow.csv"
    scaling_path = dataset_dir / "scaling.json"
    schema_path = dataset_dir / "schemas.json"
    audit_path = dataset_dir / "dataset_audit.json"
    manifest_path = dataset_dir / "dataset_manifest.json"
    pbm_sql = ", ".join(sql_literal(name) for name in PBM_DATASETS)

    with tempfile.TemporaryDirectory(prefix="bayesian_route_datasets_", dir=args.temp_dir) as temporary:
        temporary_path = Path(temporary)
        connection = duckdb.connect(str(temporary_path / "datasets.duckdb"))
        configure_duckdb(connection, temporary_path / "spill", args.duckdb_memory_limit)
        route1_query = f"""
            SELECT utterance_id, dataset, child_key,
                   CAST(session_id AS BIGINT) AS session_id,
                   CAST(age_months AS DOUBLE) AS age_months,
                   age_bin,
                   CAST(real_nb_words AS INTEGER) AS word_count,
                   CASE WHEN CAST(real_nb_words AS INTEGER) >= 12 THEN '12+'
                        ELSE CAST(CAST(real_nb_words AS INTEGER) AS VARCHAR) END AS word_count_top12,
                   (CAST(age_months AS DOUBLE) - 42.0) / 6.0 AS age_z,
                   CASE WHEN dataset IN ({pbm_sql}) THEN 'pbm_discovery'
                        ELSE 'non_pbm_replication' END AS split_scope,
                   CAST(real_k0_sum_bits AS DOUBLE) AS k0_bits,
                   CAST(real_k1_sum_bits AS DOUBLE) AS k1_bits,
                   CAST(real_k2_sum_bits AS DOUBLE) AS k2_bits,
                   CAST(real_k3_sum_bits AS DOUBLE) AS k3_bits
            FROM read_csv_auto({sql_literal(source['route1_wide'])}, sample_size=200000)
        """
        copy_parquet(connection, route1_query, route1_wide)
        connection.execute(f"CREATE VIEW r1 AS SELECT * FROM read_parquet({sql_literal(route1_wide)})")
        long_query = " UNION ALL ".join(
            f"SELECT utterance_id, dataset, child_key, session_id, age_months, age_bin, "
            f"word_count, word_count_top12, age_z, split_scope, '{condition}' AS condition, "
            f"{condition}_bits AS mean_bits FROM r1"
            for condition in CONTEXT_CONDITIONS
        )
        copy_parquet(connection, long_query, route1_long)
        connection.execute(f"CREATE VIEW r1_long AS SELECT * FROM read_parquet({sql_literal(route1_long)})")
        cell_query = """
            SELECT dataset, child_key, session_id, age_months, age_bin,
                   word_count, word_count_top12, age_z, split_scope, condition,
                   AVG(mean_bits) AS cell_mean_bits,
                   COALESCE(STDDEV_SAMP(mean_bits), 0.0) AS cell_sd_bits,
                   COUNT(*)::INTEGER AS cell_n,
                   CASE WHEN COUNT(*) > 1 THEN STDDEV_SAMP(mean_bits) / SQRT(COUNT(*))
                        ELSE 0.0 END AS cell_se_bits,
                   GREATEST(CASE WHEN COUNT(*) > 1 THEN STDDEV_SAMP(mean_bits) / SQRT(COUNT(*))
                                 ELSE 0.0 END, 1e-6) AS cell_se_for_model
            FROM r1_long
            GROUP BY dataset, child_key, session_id, age_months, age_bin,
                     word_count, word_count_top12, age_z, split_scope, condition
        """
        copy_parquet(connection, cell_query, route1_cells)

        route2_source = source["route2_model_rows"]
        scaling_row = connection.execute(
            """SELECT AVG(response_entropy_bits), STDDEV_SAMP(response_entropy_bits),
                      AVG(LN(1 + context_word_count)), STDDEV_SAMP(LN(1 + context_word_count)),
                      AVG(qwen_mean_word_count), STDDEV_SAMP(qwen_mean_word_count)
               FROM read_parquet(?)""",
            [str(route2_source)],
        ).fetchone()
        scaling = {
            "age_center_months": 42.0,
            "age_unit_months": 6.0,
            "entropy_mean": float(scaling_row[0]),
            "entropy_sd": float(scaling_row[1]),
            "log_context_words_mean": float(scaling_row[2]),
            "log_context_words_sd": float(scaling_row[3]),
            "qwen_mean_words_mean": float(scaling_row[4]),
            "qwen_mean_words_sd": float(scaling_row[5]),
            "reference_scope": "all79_descriptive",
        }
        atomic_json(scaling, scaling_path)
        route2_query = f"""
            SELECT r.*,
                   CASE WHEN r.dataset IN ({pbm_sql}) THEN 'pbm_discovery'
                        ELSE 'non_pbm_replication' END AS split_scope,
                   (r.age_months - 42.0) / 6.0 AS age_z,
                   (r.response_entropy_bits - {scaling['entropy_mean']!r}) / {scaling['entropy_sd']!r} AS entropy_z,
                   (LN(1 + r.context_word_count) - {scaling['log_context_words_mean']!r}) / {scaling['log_context_words_sd']!r} AS context_words_z,
                   (r.qwen_mean_word_count - {scaling['qwen_mean_words_mean']!r}) / {scaling['qwen_mean_words_sd']!r} AS qwen_mean_words_z,
                   CASE WHEN r.child_words >= 12 THEN '12+' ELSE CAST(r.child_words AS VARCHAR) END AS word_count_top12,
                   CAST(ROUND(200 * r.effort_percentile_in_qwen) AS SMALLINT) AS rank200
            FROM read_parquet({sql_literal(route2_source)}) r
        """
        copy_parquet(connection, route2_query, route2_rows)
        connection.execute(f"CREATE VIEW r2 AS SELECT * FROM read_parquet({sql_literal(route2_rows)})")
        b5_query = """
            SELECT r2.utterance_id, r2.dataset, r2.child_key, r2.session_id,
                   r2.age_months, r2.age_bin, r2.age_z, r2.split_scope,
                   r1.word_count_top12, r1.k3_bits,
                   r2.child_words, r2.entropy_z, r2.response_entropy_bits,
                   r2.context_words_z, r2.context_word_count
            FROM r2
            INNER JOIN r1 USING (utterance_id)
        """
        copy_parquet(connection, b5_query, b5_rows)

        expected = contract["expected_data"]
        r1_stats = connection.execute(
            """SELECT COUNT(*), COUNT(DISTINCT utterance_id),
                      COUNT(DISTINCT child_key), COUNT(DISTINCT dataset),
                      SUM(CASE WHEN NOT isfinite(k0_bits) OR NOT isfinite(k1_bits)
                                    OR NOT isfinite(k2_bits) OR NOT isfinite(k3_bits) THEN 1 ELSE 0 END)
               FROM r1"""
        ).fetchone()
        long_stats = connection.execute("SELECT COUNT(*), COUNT(DISTINCT condition) FROM r1_long").fetchone()
        cell_stats = connection.execute(
            f"""SELECT COUNT(*), SUM(cell_n), SUM(CASE WHEN cell_n=1 THEN 1 ELSE 0 END),
                       (SELECT AVG(mean_bits) FROM r1_long),
                       SUM(cell_mean_bits * cell_n) / SUM(cell_n)
                FROM read_parquet({sql_literal(route1_cells)})"""
        ).fetchone()
        r2_stats = connection.execute(
            """SELECT COUNT(*), COUNT(DISTINCT utterance_id), COUNT(DISTINCT child_key),
                      COUNT(DISTINCT dataset), COUNT(DISTINCT context_id),
                      SUM(rank200=0), SUM(rank200=200),
                      MAX(ABS(200 * effort_percentile_in_qwen - rank200)),
                      COUNT(DISTINCT child_key) FILTER (WHERE split_scope='pbm_discovery'),
                      COUNT(DISTINCT child_key) FILTER (WHERE split_scope='non_pbm_replication')
               FROM r2"""
        ).fetchone()
        cloud_stats = connection.execute(
            """SELECT COUNT(*), COUNT(DISTINCT r2.utterance_id),
                      SUM(CASE WHEN cloud.qwen_responses != 100 THEN 1 ELSE 0 END)
               FROM r2 LEFT JOIN read_parquet(?) cloud USING (utterance_id)""",
            [str(source["route2_observed_cloud_metrics"])],
        ).fetchone()
        b5_count = connection.execute(f"SELECT COUNT(*) FROM read_parquet({sql_literal(b5_rows)})").fetchone()[0]

        problems: list[str] = []
        checks = {
            "route1_rows": int(r1_stats[0]),
            "route1_unique_utterances": int(r1_stats[1]),
            "route1_children": int(r1_stats[2]),
            "route1_corpora": int(r1_stats[3]),
            "route1_nonfinite_pairs": int(r1_stats[4]),
            "route1_long_rows": int(long_stats[0]),
            "route1_conditions": int(long_stats[1]),
            "route1_cells": int(cell_stats[0]),
            "route1_cell_n_sum": int(cell_stats[1]),
            "route1_singleton_cells": int(cell_stats[2]),
            "route1_raw_mean": float(cell_stats[3]),
            "route1_reconstructed_mean": float(cell_stats[4]),
            "route2_rows": int(r2_stats[0]),
            "route2_unique_utterances": int(r2_stats[1]),
            "route2_children": int(r2_stats[2]),
            "route2_corpora": int(r2_stats[3]),
            "route2_contexts": int(r2_stats[4]),
            "rank_zero_endpoints": int(r2_stats[5]),
            "rank_one_endpoints": int(r2_stats[6]),
            "rank200_max_error": float(r2_stats[7]),
            "pbm_children": int(r2_stats[8]),
            "non_pbm_children": int(r2_stats[9]),
            "cloud_join_rows": int(cloud_stats[0]),
            "cloud_unique_utterances": int(cloud_stats[1]),
            "cloud_non100_rows": int(cloud_stats[2]),
            "b5_shared_rows": int(b5_count),
        }
        exact_expectations = {
            "route1_rows": expected["route1_rows"],
            "route1_unique_utterances": expected["route1_rows"],
            "route1_children": expected["children"],
            "route1_corpora": expected["corpora"],
            "route1_nonfinite_pairs": 0,
            "route1_long_rows": 4 * expected["route1_rows"],
            "route1_conditions": 4,
            "route1_cell_n_sum": 4 * expected["route1_rows"],
            "route2_rows": expected["route2_rows"],
            "route2_unique_utterances": expected["route2_rows"],
            "route2_children": expected["children"],
            "route2_corpora": expected["corpora"],
            "rank_zero_endpoints": expected["rank_zero_endpoints"],
            "rank_one_endpoints": expected["rank_one_endpoints"],
            "pbm_children": expected["pbm_children"],
            "non_pbm_children": expected["non_pbm_children"],
            "cloud_join_rows": expected["route2_rows"],
            "cloud_unique_utterances": expected["route2_rows"],
            "cloud_non100_rows": 0,
            "b5_shared_rows": expected["route2_rows"],
        }
        for name, value in exact_expectations.items():
            if checks[name] != value:
                problems.append(f"{name}: expected {value}, observed {checks[name]}")
        if checks["rank200_max_error"] > 1e-9:
            problems.append(f"rank200 mismatch: {checks['rank200_max_error']}")
        if not np.isclose(checks["route1_raw_mean"], checks["route1_reconstructed_mean"], atol=1e-12, rtol=0):
            problems.append("route1 exact aggregation mean mismatch")

        flow = connection.execute(
            """SELECT 'route1' AS route, split_scope AS sample_scope, COUNT(*) AS rows,
                      COUNT(DISTINCT child_key) AS children, COUNT(DISTINCT dataset) AS corpora FROM r1 GROUP BY split_scope
               UNION ALL SELECT 'route1', 'all79_descriptive', COUNT(*), COUNT(DISTINCT child_key), COUNT(DISTINCT dataset) FROM r1
               UNION ALL SELECT 'route2', split_scope, COUNT(*), COUNT(DISTINCT child_key), COUNT(DISTINCT dataset) FROM r2 GROUP BY split_scope
               UNION ALL SELECT 'route2', 'all79_descriptive', COUNT(*), COUNT(DISTINCT child_key), COUNT(DISTINCT dataset) FROM r2
               ORDER BY route, sample_scope"""
        ).fetchdf()
        atomic_csv(flow, flow_path)
        schemas: dict[str, Any] = {}
        for name, path in {
            "route1_wide": route1_wide,
            "route1_long": route1_long,
            "route1_cells": route1_cells,
            "route2_rows": route2_rows,
            "b5_rows": b5_rows,
        }.items():
            description = connection.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).fetchdf()
            schemas[name] = description[["column_name", "column_type"]].to_dict(orient="records")
        atomic_json(schemas, schema_path)
        connection.close()

    audit = {"status": "PASS" if not problems else "FAIL", **checks, "problems": problems}
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("dataset stage failed: " + "; ".join(problems))
    return write_manifest(
        stage="datasets",
        manifest_path=manifest_path,
        inputs={
            "contract_manifest": contract_manifest_path,
            "route1_wide": source["route1_wide"],
            "route2_model_rows": source["route2_model_rows"],
            "route2_observed_cloud_metrics": source["route2_observed_cloud_metrics"],
        },
        outputs={
            "route1_wide": route1_wide,
            "route1_long": route1_long,
            "route1_cells": route1_cells,
            "route2_rows": route2_rows,
            "b5_rows": b5_rows,
            "sample_flow": flow_path,
            "scaling": scaling_path,
            "schemas": schema_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def run_synthetic_smoke_stage(args: argparse.Namespace) -> dict[str, Any]:
    priors_manifest_path = args.output_dir / "priors/priors_manifest.json"
    require_manifest(priors_manifest_path, "priors")
    contract = load_and_validate_contract(args.contract)
    synthetic_dir = args.output_dir / "synthetic-smoke"
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    recovery_path = synthetic_dir / "deterministic_likelihood_recovery.json"
    fit_records_path = synthetic_dir / "fit_records.csv"
    parameter_records_path = synthetic_dir / "parameter_recovery.csv"
    recovery_checks_path = synthetic_dir / "recovery_checks.csv"
    backend_smoke_path = synthetic_dir / "backend_smoke_audit.json"
    backend_audit_path = synthetic_dir / "backend_environment.json"
    stdout_path = synthetic_dir / "backend_stdout.log"
    stderr_path = synthetic_dir / "backend_stderr.log"
    audit_path = synthetic_dir / "synthetic_smoke_audit.json"
    manifest_path = synthetic_dir / "synthetic_smoke_manifest.json"

    deterministic = synthetic_likelihood_recovery(seed=20260828)
    atomic_json(deterministic, recovery_path)
    backend = audit_backend_environment(contract)
    atomic_json(backend, backend_audit_path)
    problems: list[str] = []
    if deterministic["status"] != "PASS":
        problems.append("deterministic likelihood recovery failed")
    if not backend["ready"]:
        problems.append("repository-local Bayesian backend audit failed")

    completed: subprocess.CompletedProcess[str] | None = None
    if not problems:
        completed = run_r_backend(
            "--mode", "synthetic-smoke",
            "--output-dir", str(synthetic_dir),
            "--seed", "20260828",
            "--chains", str(args.smoke_chains),
            "--warmup", str(args.smoke_warmup),
            "--sampling", str(args.smoke_sampling),
        )
        atomic_text(completed.stdout, stdout_path)
        atomic_text(completed.stderr, stderr_path)
        if completed.returncode != 0:
            problems.append(f"R/Stan synthetic smoke exited {completed.returncode}")
    else:
        atomic_text("backend not launched because preflight failed\n", stdout_path)
        atomic_text("\n".join(problems) + "\n", stderr_path)

    smoke_payload: dict[str, Any] = {}
    if backend_smoke_path.exists():
        smoke_payload = json.loads(backend_smoke_path.read_text(encoding="utf-8"))
        if smoke_payload.get("status") != "PASS":
            problems.append("R/Stan backend smoke audit failed")
    elif completed is not None and completed.returncode == 0:
        problems.append("R/Stan backend smoke did not write its audit")

    expected_fits = {
        "B1_synthetic", "B2_synthetic", "B3_synthetic",
        "B4_beta_binomial_synthetic", "B4_zoib_synthetic", "B5_synthetic",
    }
    observed_fits: set[str] = set()
    if fit_records_path.exists():
        fit_records = pd.read_csv(fit_records_path)
        observed_fits = set(fit_records.get("fit_id", pd.Series(dtype=str)).astype(str))
        if observed_fits != expected_fits:
            problems.append("R/Stan synthetic fit inventory mismatch")
    elif completed is not None and completed.returncode == 0:
        problems.append("R/Stan backend smoke did not write fit records")

    audit = {
        "status": "PASS" if not problems else "FAIL",
        "deterministic_recovery": deterministic["status"],
        "backend_ready": backend["ready"],
        "r_returncode": None if completed is None else completed.returncode,
        "expected_synthetic_fits": sorted(expected_fits),
        "observed_synthetic_fits": sorted(observed_fits),
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("synthetic smoke stage failed: " + "; ".join(problems))
    return write_manifest(
        stage="synthetic-smoke",
        manifest_path=manifest_path,
        inputs={
            "priors_manifest": priors_manifest_path,
            "tracked_contract": args.contract,
            "r_backend": ROOT / "src/fit_bayesian_route1_route2_models.R",
            "b5_stan": ROOT / "src/stan/b5_bivariate_measurement_error.stan",
        },
        outputs={
            "deterministic_recovery": recovery_path,
            "fit_records": fit_records_path,
            "parameter_recovery": parameter_records_path,
            "recovery_checks": recovery_checks_path,
            "backend_smoke": backend_smoke_path,
            "backend_environment": backend_audit_path,
            "stdout": stdout_path,
            "stderr": stderr_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def _stable_hash(value: str) -> str:
    return sha256_text(value)


def prepare_real_pilot_inputs(
    args: argparse.Namespace,
    contract: Mapping[str, Any],
    pilot_dir: Path,
) -> tuple[dict[str, Path], dict[str, Any]]:
    dataset_dir = args.output_dir / "datasets"
    route1_cells = dataset_dir / "route1_condition_cells.parquet"
    route1_wide = dataset_dir / "route1_paired_wide.parquet"
    route2_rows = dataset_dir / "route2_rows.parquet"
    b5_rows = dataset_dir / "b5_shared_utterance_rows.parquet"
    input_dir = pilot_dir / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    selected_children_path = input_dir / "selected_children.csv"
    b1_path = input_dir / "B1.csv"
    b2_path = input_dir / "B2.csv"
    b3_b4_path = input_dir / "B3_B4.csv"
    b5_source_path = input_dir / "B5_source.csv.gz"
    b5_slopes_path = input_dir / "B5_slopes.csv"
    bootstrap_audit_path = input_dir / "B5_shared_bootstrap_audit.json"

    gate = contract["pilot_gate"]
    target_children = int(gate["pilot_children_B5"])
    with tempfile.TemporaryDirectory(prefix="bayesian_real_pilot_", dir=args.temp_dir) as temporary:
        connection = duckdb.connect(str(Path(temporary) / "pilot.duckdb"))
        configure_duckdb(connection, Path(temporary) / "spill", args.duckdb_memory_limit)
        child_stats = connection.execute(
            """SELECT child_key, dataset, COUNT(*) AS rows,
                      MIN(age_z) AS age_min, MAX(age_z) AS age_max,
                      STDDEV_SAMP(age_z) AS age_sd
               FROM read_parquet(?)
               GROUP BY child_key, dataset
               HAVING COUNT(*) >= 500 AND STDDEV_SAMP(age_z) >= 0.15""",
            [str(b5_rows)],
        ).fetchdf()
        child_stats["stable_order"] = [
            _stable_hash(f"{dataset}\0{child}")
            for child, dataset in zip(child_stats.child_key, child_stats.dataset)
        ]
        child_stats = child_stats.sort_values(
            ["dataset", "age_sd", "rows", "stable_order"],
            ascending=[True, False, False, True],
        )
        primary = child_stats.groupby("dataset", sort=True, as_index=False).head(1)
        remaining = child_stats.loc[~child_stats.child_key.isin(primary.child_key)].sort_values("stable_order")
        selected = pd.concat(
            [primary, remaining.head(target_children - len(primary))], ignore_index=True
        )
        if len(selected) != target_children or selected.dataset.nunique() != contract["expected_data"]["corpora"]:
            raise RuntimeError(
                f"pilot child selection failed: {len(selected)} children / {selected.dataset.nunique()} corpora"
            )
        selected = selected.sort_values(["dataset", "child_key"]).reset_index(drop=True)
        atomic_csv(selected.drop(columns="stable_order"), selected_children_path)
        connection.register("selected_children", selected[["child_key"]])

        b1_per_condition = int(gate["pilot_rows_B1"]) // 4
        b1 = connection.execute(
            f"""WITH ranked AS (
                    SELECT cells.*,
                           ROW_NUMBER() OVER (
                             PARTITION BY condition
                             ORDER BY hash(child_key, session_id, age_months, word_count, condition)
                           ) AS pilot_rank
                    FROM read_parquet({sql_literal(route1_cells)}) cells
                    INNER JOIN selected_children USING (child_key)
                  )
                  SELECT * EXCLUDE (pilot_rank) FROM ranked
                  WHERE pilot_rank <= {b1_per_condition}
                  ORDER BY condition, child_key, session_id, word_count"""
        ).fetchdf()
        per_child_raw = int(np.ceil(int(gate["pilot_rows_B2"]) / target_children))
        b2 = connection.execute(
            f"""WITH ranked AS (
                    SELECT rows.*,
                           ROW_NUMBER() OVER (
                             PARTITION BY child_key ORDER BY hash(utterance_id)
                           ) AS pilot_rank
                    FROM read_parquet({sql_literal(route1_wide)}) rows
                    INNER JOIN selected_children USING (child_key)
                  )
                  SELECT * EXCLUDE (pilot_rank) FROM ranked
                  WHERE pilot_rank <= {per_child_raw}
                  ORDER BY child_key, utterance_id
                  LIMIT {int(gate['pilot_rows_B2'])}"""
        ).fetchdf()
        per_child_route2 = int(np.ceil(int(gate["pilot_rows_B3"]) / target_children))
        b3_b4 = connection.execute(
            f"""WITH ranked AS (
                    SELECT rows.*,
                           ROW_NUMBER() OVER (
                             PARTITION BY child_key ORDER BY hash(utterance_id)
                           ) AS pilot_rank
                    FROM read_parquet({sql_literal(route2_rows)}) rows
                    INNER JOIN selected_children USING (child_key)
                  )
                  SELECT * EXCLUDE (pilot_rank) FROM ranked
                  WHERE pilot_rank <= {per_child_route2}
                  ORDER BY child_key, utterance_id
                  LIMIT {int(gate['pilot_rows_B3'])}"""
        ).fetchdf()
        b5_source = connection.execute(
            f"""WITH ranked AS (
                    SELECT rows.*,
                           ROW_NUMBER() OVER (
                             PARTITION BY child_key ORDER BY hash(utterance_id)
                           ) AS pilot_rank
                    FROM read_parquet({sql_literal(b5_rows)}) rows
                    INNER JOIN selected_children USING (child_key)
                  )
                  SELECT * EXCLUDE (pilot_rank) FROM ranked
                  WHERE pilot_rank <= {int(args.pilot_b5_rows_per_child)}
                  ORDER BY child_key, utterance_id"""
        ).fetchdf()
        scope_counts = connection.execute(
            f"""SELECT 'B1' AS model_family,
                       CASE WHEN split_scope='pbm_discovery' THEN 'pbm_discovery'
                            ELSE 'non_pbm_replication' END AS sample_scope,
                       COUNT(*) AS rows
                FROM read_parquet({sql_literal(route1_cells)}) GROUP BY split_scope
                UNION ALL SELECT 'B1', 'all79_descriptive', COUNT(*) FROM read_parquet({sql_literal(route1_cells)})
                UNION ALL SELECT 'B2', split_scope, COUNT(*) FROM read_parquet({sql_literal(route1_wide)}) GROUP BY split_scope
                UNION ALL SELECT 'B2', 'all79_descriptive', COUNT(*) FROM read_parquet({sql_literal(route1_wide)})
                UNION ALL SELECT 'B3', split_scope, COUNT(*) FROM read_parquet({sql_literal(route2_rows)}) GROUP BY split_scope
                UNION ALL SELECT 'B3', 'all79_descriptive', COUNT(*) FROM read_parquet({sql_literal(route2_rows)})
                UNION ALL SELECT 'B4', split_scope, COUNT(*) FROM read_parquet({sql_literal(route2_rows)}) GROUP BY split_scope
                UNION ALL SELECT 'B4', 'all79_descriptive', COUNT(*) FROM read_parquet({sql_literal(route2_rows)})
                ORDER BY model_family, sample_scope"""
        ).fetchdf()
        connection.close()

    if len(b1) != int(gate["pilot_rows_B1"]) or b1.condition.nunique() != 4:
        raise RuntimeError("B1 pilot sample dimension mismatch")
    if len(b2) != int(gate["pilot_rows_B2"]):
        raise RuntimeError("B2 pilot sample dimension mismatch")
    if len(b3_b4) != int(gate["pilot_rows_B3"]):
        raise RuntimeError("B3/B4 pilot sample dimension mismatch")
    b5_slopes, bootstrap_audit = estimate_shared_bootstrap_slopes(
        b5_source,
        bootstrap_draws=args.pilot_bootstrap_draws,
        seed=20260828,
    )
    if len(b5_slopes) != target_children:
        raise RuntimeError("B5 pilot slope dimension mismatch")
    atomic_csv(b1, b1_path)
    atomic_csv(b2, b2_path)
    atomic_csv(b3_b4, b3_b4_path)
    atomic_csv_gzip(b5_source, b5_source_path)
    atomic_csv(b5_slopes, b5_slopes_path)
    atomic_json(bootstrap_audit, bootstrap_audit_path)
    inputs = {
        "selected_children": selected_children_path,
        "B1": b1_path,
        "B2": b2_path,
        "B3_B4": b3_b4_path,
        "B5_source": b5_source_path,
        "B5_slopes": b5_slopes_path,
        "B5_bootstrap_audit": bootstrap_audit_path,
    }
    audit = {
        "status": "PASS",
        "selected_children": int(len(selected)),
        "selected_corpora": int(selected.dataset.nunique()),
        "selected_pbm_children": int(selected.dataset.isin(PBM_DATASETS).sum()),
        "B1_rows": int(len(b1)),
        "B1_children": int(b1.child_key.nunique()),
        "B1_corpora": int(b1.dataset.nunique()),
        "B2_rows": int(len(b2)),
        "B3_B4_rows": int(len(b3_b4)),
        "B5_source_rows": int(len(b5_source)),
        "B5_children": int(len(b5_slopes)),
        "scope_counts": scope_counts.to_dict(orient="records"),
        "shared_bootstrap": bootstrap_audit,
    }
    return inputs, audit


def project_registered_fits(
    pilot_records: pd.DataFrame,
    contract: Mapping[str, Any],
    scope_counts: list[Mapping[str, Any]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    inventory = build_registered_fit_inventory(contract)
    pilot_map = {
        ("B1", "paired_primary"): "B1_pilot",
        ("B2", "location_scale_primary"): "B2_pilot",
        ("B3", "raw_total_association_primary"): "B3_primary_pilot",
        ("B3", "qwen_expected_length_adjusted_sensitivity"): "B3_qwen_adjusted_pilot",
        ("B4", "beta_binomial_primary"): "B4_beta_binomial_pilot",
        ("B4", "zoib_registered_sensitivity"): "B4_zoib_pilot",
        ("B5", "shared_bootstrap_measurement_error_primary"): "B5_pilot",
    }
    count_map = {
        (str(row["model_family"]), str(row["sample_scope"])): int(row["rows"])
        for row in scope_counts
    }
    child_counts = {"pbm_discovery": 21, "non_pbm_replication": 58, "all79_descriptive": 79}
    pilot_lookup = pilot_records.set_index("fit_id", drop=False)
    production = contract["production_sampler"]
    gate = contract["pilot_gate"]
    iteration_multiplier = (
        (production["warmup"] + production["sampling"])
        / (gate["warmup"] + gate["sampling"])
    )
    shape_multiplier = {"linear": 0.70, "quadratic": 0.82, "low_rank_smooth": 1.0}
    prior_multiplier = {"weak": 1.0, "skeptical": 1.0, "wide": 1.10}
    rows: list[dict[str, Any]] = []
    for fit in inventory.itertuples(index=False):
        pilot_id = pilot_map[(fit.model_family, fit.variant)]
        pilot = pilot_lookup.loc[pilot_id]
        final_rows = (
            child_counts[fit.sample_scope]
            if fit.model_family == "B5"
            else count_map[(fit.model_family, fit.sample_scope)]
        )
        row_ratio = max(1.0, final_rows / float(pilot["rows"]))
        wall_seconds = (
            float(pilot["elapsed_seconds"])
            * iteration_multiplier
            * row_ratio**0.80
            * shape_multiplier[fit.age_shape]
            * prior_multiplier[fit.prior_set]
        )
        output_bytes = (
            float(pilot["output_bytes"])
            * (production["chains"] / float(pilot["chains"]))
            * (production["sampling"] / float(pilot["sampling"]))
            * row_ratio**0.35
        )
        peak_memory_gb = (
            float(pilot["peak_rss_kb"]) / 1024**2 * row_ratio**0.25
        )
        projected_ess_hour = float(pilot["minimum_bulk_ess_per_hour"]) / row_ratio**0.30
        rows.append({
            **fit._asdict(),
            "pilot_fit_id": pilot_id,
            "pilot_rows": int(pilot["rows"]),
            "projected_rows": int(final_rows),
            "row_multiplier": row_ratio,
            "projected_wall_hours": wall_seconds / 3600,
            "projected_cpu_hours": wall_seconds / 3600 * production["chains"],
            "projected_peak_memory_gb": peak_memory_gb,
            "projected_output_gb": output_bytes / 1e9,
            "projected_minimum_bulk_ess_per_hour": projected_ess_hour,
        })
    projection = pd.DataFrame(rows)
    summary = {
        "registered_fits": int(len(projection)),
        "maximum_single_fit_wall_hours": float(projection.projected_wall_hours.max()),
        "total_projected_cpu_hours": float(projection.projected_cpu_hours.sum()),
        "maximum_peak_memory_gb": float(projection.projected_peak_memory_gb.max()),
        "total_projected_output_gb": float(projection.projected_output_gb.sum()),
        "minimum_projected_bulk_ess_per_hour": float(projection.projected_minimum_bulk_ess_per_hour.min()),
        "projection_model": "pilot elapsed including compile; N^0.80 wall, N^0.25 memory, N^0.35 output parameter growth; frozen production sampler",
    }
    return projection, summary


def run_real_pilot_stage(args: argparse.Namespace) -> dict[str, Any]:
    synthetic_manifest_path = args.output_dir / "synthetic-smoke/synthetic_smoke_manifest.json"
    require_manifest(synthetic_manifest_path, "synthetic-smoke")
    contract = load_and_validate_contract(args.contract)
    pilot_dir = args.output_dir / "real-pilot"
    pilot_dir.mkdir(parents=True, exist_ok=True)
    inputs, input_audit = prepare_real_pilot_inputs(args, contract, pilot_dir)
    input_audit_path = pilot_dir / "pilot_input_audit.json"
    atomic_json(input_audit, input_audit_path)

    fit_records_path = pilot_dir / "fit_records.csv"
    formula_registry_path = pilot_dir / "formula_registry.csv"
    backend_audit_path = pilot_dir / "pilot_backend_audit.json"
    stdout_path = pilot_dir / "backend_stdout.log"
    stderr_path = pilot_dir / "backend_stderr.log"
    projection_path = pilot_dir / "registered_fit_resource_projection.csv"
    decision_path = pilot_dir / "pilot_decision.json"
    report_path = pilot_dir / "pilot_report.md"
    audit_path = pilot_dir / "real_pilot_audit.json"
    manifest_path = pilot_dir / "real_pilot_manifest.json"

    completed = run_r_backend(
        "--mode", "pilot",
        "--input-dir", str(pilot_dir / "inputs"),
        "--output-dir", str(pilot_dir),
        "--prior-set", "skeptical",
        "--seed", "20260828",
        "--chains", str(contract["pilot_gate"]["chains"]),
        "--warmup", str(contract["pilot_gate"]["warmup"]),
        "--sampling", str(contract["pilot_gate"]["sampling"]),
    )
    atomic_text(completed.stdout, stdout_path)
    atomic_text(completed.stderr, stderr_path)
    problems: list[str] = []
    if completed.returncode != 0:
        problems.append(f"R/Stan real pilot exited {completed.returncode}")

    expected_pilot_fits = {
        "B1_pilot", "B2_pilot", "B3_primary_pilot", "B3_qwen_adjusted_pilot",
        "B4_beta_binomial_pilot", "B4_zoib_pilot", "B5_pilot",
    }
    if fit_records_path.exists():
        fit_records = pd.read_csv(fit_records_path)
    else:
        fit_records = pd.DataFrame(columns=[
            "fit_id", "fit_status", "elapsed_seconds", "rows", "chains",
            "warmup", "sampling", "output_bytes", "peak_rss_kb",
            "minimum_bulk_ess_per_hour", "rhat_max", "ess_bulk_min",
            "ess_tail_min", "divergences", "treedepth_saturated", "energy_bfmi_min",
        ])
        atomic_csv(fit_records, fit_records_path)
    observed_pilot_fits = set(fit_records.fit_id.astype(str))
    if observed_pilot_fits != expected_pilot_fits:
        problems.append("representative pilot fit inventory is incomplete")
    if not formula_registry_path.exists():
        atomic_csv(
            pd.DataFrame(columns=["fit_id", "model_family", "variant", "age_shape", "prior_set", "formula", "rows"]),
            formula_registry_path,
        )
    if not backend_audit_path.exists():
        atomic_json(
            {"status": "FAIL", "reason": "backend did not reach its final audit"},
            backend_audit_path,
        )

    diagnostic_problems: list[str] = []
    if observed_pilot_fits == expected_pilot_fits:
        bad = fit_records[
            (fit_records.fit_status != "PASS")
            | (fit_records.rhat_max > 1.10)
            | (fit_records.ess_bulk_min < 20)
            | (fit_records.ess_tail_min < 20)
            | (fit_records.divergences != 0)
            | (fit_records.treedepth_saturated > 0.01 * fit_records.chains * fit_records.sampling)
            | (fit_records.energy_bfmi_min < 0.20)
        ]
        diagnostic_problems.extend(
            f"pilot diagnostic gate failed: {fit_id}" for fit_id in bad.fit_id.astype(str)
        )
    problems.extend(diagnostic_problems)

    projection_summary: dict[str, Any] = {
        "registered_fits": len(build_registered_fit_inventory(contract)),
        "projection_unavailable": True,
    }
    if observed_pilot_fits == expected_pilot_fits:
        projection, projection_summary = project_registered_fits(
            fit_records, contract, input_audit["scope_counts"]
        )
        atomic_csv(projection, projection_path)
    else:
        atomic_csv(pd.DataFrame(columns=["fit_id", "projection_unavailable"]), projection_path)

    gate = contract["pilot_gate"]
    resource_problems: list[str] = []
    if not projection_summary.get("projection_unavailable"):
        checks = {
            "maximum_single_fit_wall_hours": gate["max_projected_single_fit_wall_hours"],
            "total_projected_cpu_hours": gate["max_projected_total_cpu_hours"],
            "maximum_peak_memory_gb": gate["max_projected_peak_memory_gb"],
            "total_projected_output_gb": gate["max_projected_output_gb"],
        }
        for metric, maximum in checks.items():
            if float(projection_summary[metric]) > float(maximum):
                resource_problems.append(
                    f"{metric}={projection_summary[metric]:.3f} exceeds {maximum}"
                )
        if (
            float(projection_summary["minimum_projected_bulk_ess_per_hour"])
            < float(gate["minimum_bulk_ess_per_hour"])
        ):
            resource_problems.append(
                "minimum projected bulk ESS/hour is below the frozen gate"
            )
    problems.extend(resource_problems)
    safe_to_proceed = not problems
    decision = {
        "status": "PROCEED_TO_PRODUCTION" if safe_to_proceed else "STOP_UNSAFE",
        "safe_to_proceed": safe_to_proceed,
        "reason": (
            "all representative likelihood, diagnostic, and frozen resource gates passed"
            if safe_to_proceed
            else "production posterior fitting is blocked; no estimand or unit may be simplified without review"
        ),
        "pilot_fit_problems": diagnostic_problems,
        "resource_problems": resource_problems,
        "all_problems": problems,
        "projection_summary": projection_summary,
        "frozen_gates": gate,
        "production_sampler": contract["production_sampler"],
    }
    atomic_json(decision, decision_path)
    report_lines = [
        "# Bayesian Route 1 / Route 2 real-data pilot",
        "",
        f"Decision: **{decision['status']}**",
        "",
        "This is a computational and likelihood pilot, not a scientific posterior result.",
        "No production fit is launched when this decision is `STOP_UNSAFE`.",
        "",
        f"- Pilot fits observed: {len(observed_pilot_fits)}/{len(expected_pilot_fits)}",
        f"- Registered production fits projected: {projection_summary.get('registered_fits')}",
        f"- R backend exit code: {completed.returncode}",
        f"- Shared-bootstrap B5 children: {input_audit['B5_children']}",
        "",
        "## Blocking findings",
        "",
    ]
    report_lines.extend(f"- {problem}" for problem in problems)
    if not problems:
        report_lines.append("- None.")
    report_lines.extend([
        "",
        "The safe next action after a STOP is review of the registered fit inventory and CPU plan;",
        "it is not an automatic change to aggregation, likelihood, sample, or cluster hardware.",
    ])
    atomic_text("\n".join(report_lines) + "\n", report_path)
    audit = {
        "status": "PASS_PROCEED" if safe_to_proceed else "PASS_STOPPED_UNSAFE",
        "safe_to_proceed": safe_to_proceed,
        "pilot_fit_count": int(len(observed_pilot_fits)),
        "expected_pilot_fit_count": int(len(expected_pilot_fits)),
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    outputs = {
        **inputs,
        "input_audit": input_audit_path,
        "fit_records": fit_records_path,
        "formula_registry": formula_registry_path,
        "backend_audit": backend_audit_path,
        "stdout": stdout_path,
        "stderr": stderr_path,
        "projection": projection_path,
        "decision": decision_path,
        "pilot_report": report_path,
        "audit": audit_path,
    }
    return write_manifest(
        stage="real-pilot",
        manifest_path=manifest_path,
        inputs={
            "synthetic_manifest": synthetic_manifest_path,
            "tracked_contract": args.contract,
            "r_backend": ROOT / "src/fit_bayesian_route1_route2_models.R",
            "b5_stan": ROOT / "src/stan/b5_bivariate_measurement_error.stan",
            "route1_cells": args.output_dir / "datasets/route1_condition_cells.parquet",
            "route1_wide": args.output_dir / "datasets/route1_paired_wide.parquet",
            "route2_rows": args.output_dir / "datasets/route2_rows.parquet",
            "b5_rows": args.output_dir / "datasets/b5_shared_utterance_rows.parquet",
        },
        outputs=outputs,
        audit=audit,
        extra={"decision": decision},
    )


def run_models_stage(args: argparse.Namespace) -> dict[str, Any]:
    pilot_manifest_path = args.output_dir / "real-pilot/real_pilot_manifest.json"
    pilot_manifest = require_manifest(pilot_manifest_path, "real-pilot")
    decision = pilot_manifest.get("decision", {})
    models_dir = args.output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    status_path = models_dir / "production_status.json"
    inventory_path = models_dir / "production_fit_inventory.csv"
    audit_path = models_dir / "models_audit.json"
    manifest_path = models_dir / "models_manifest.json"
    contract = load_and_validate_contract(args.contract)
    if decision.get("safe_to_proceed"):
        raise RuntimeError(
            "pilot unexpectedly authorizes production, but this invocation has no explicit production authorization"
        )
    inventory = build_registered_fit_inventory(contract).assign(
        fit_status="BLOCKED_BY_REAL_PILOT_GATE",
        posterior_available=False,
        blocking_decision=decision.get("status", "UNKNOWN"),
    )
    atomic_csv(inventory, inventory_path)
    status = {
        "status": "SKIPPED_BY_REAL_PILOT_GATE",
        "production_fits_launched": 0,
        "registered_fits_blocked": int(len(inventory)),
        "decision": decision,
        "estimand_changed": False,
        "unit_changed": False,
        "mila_work_launched": False,
    }
    atomic_json(status, status_path)
    audit = {
        "status": "PASS_STOP_ENFORCED",
        "safe_to_proceed": False,
        "production_fits_launched": 0,
        "blocked_fits": int(len(inventory)),
        "problems": [],
    }
    atomic_json(audit, audit_path)
    return write_manifest(
        stage="models",
        manifest_path=manifest_path,
        inputs={"real_pilot_manifest": pilot_manifest_path, "tracked_contract": args.contract},
        outputs={
            "production_status": status_path,
            "fit_inventory": inventory_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def run_diagnostics_stage(args: argparse.Namespace) -> dict[str, Any]:
    models_manifest_path = args.output_dir / "models/models_manifest.json"
    require_manifest(models_manifest_path, "models")
    diagnostics_dir = args.output_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    pilot_records_path = args.output_dir / "real-pilot/fit_records.csv"
    diagnostics_path = diagnostics_dir / "pilot_fit_diagnostics.csv"
    summary_path = diagnostics_dir / "diagnostics_summary.json"
    audit_path = diagnostics_dir / "diagnostics_audit.json"
    manifest_path = diagnostics_dir / "diagnostics_manifest.json"
    pilot = pd.read_csv(pilot_records_path)
    if pilot.empty:
        raise RuntimeError("real pilot diagnostics are missing")
    diagnostic = pilot[[
        "fit_id", "rhat_max", "ess_bulk_min", "ess_tail_min", "divergences",
        "treedepth_saturated", "energy_bfmi_min", "minimum_bulk_ess_per_hour",
    ]].copy()
    diagnostic["pilot_gate_status"] = np.where(
        (diagnostic.rhat_max <= 1.10)
        & (diagnostic.ess_bulk_min >= 20)
        & (diagnostic.ess_tail_min >= 20)
        & (diagnostic.divergences == 0)
        & (diagnostic.energy_bfmi_min >= 0.20),
        "PASS",
        "FAIL",
    )
    atomic_csv(diagnostic, diagnostics_path)
    failures = diagnostic.loc[diagnostic.pilot_gate_status == "FAIL", "fit_id"].astype(str).tolist()
    summary = {
        "status": "PILOT_DIAGNOSTICS_RECORDED_PRODUCTION_BLOCKED",
        "pilot_fits": int(len(diagnostic)),
        "pilot_failures": failures,
        "production_diagnostics_available": False,
        "production_diagnostics_expected": 189,
        "production_diagnostics_missing_by_design_after_stop": 189,
    }
    atomic_json(summary, summary_path)
    audit = {
        "status": "PASS_STOP_RECORDED",
        "pilot_fit_count": int(len(diagnostic)),
        "pilot_failure_count": len(failures),
        "production_claim_allowed": False,
        "problems": [],
    }
    atomic_json(audit, audit_path)
    return write_manifest(
        stage="diagnostics",
        manifest_path=manifest_path,
        inputs={"models_manifest": models_manifest_path, "pilot_fit_records": pilot_records_path},
        outputs={"pilot_diagnostics": diagnostics_path, "summary": summary_path, "audit": audit_path},
        audit=audit,
    )


def run_synthesis_stage(args: argparse.Namespace) -> dict[str, Any]:
    diagnostics_manifest_path = args.output_dir / "diagnostics/diagnostics_manifest.json"
    require_manifest(diagnostics_manifest_path, "diagnostics")
    synthesis_dir = args.output_dir / "synthesis"
    synthesis_dir.mkdir(parents=True, exist_ok=True)
    decision_path = args.output_dir / "real-pilot/pilot_decision.json"
    pilot_records_path = args.output_dir / "real-pilot/fit_records.csv"
    projection_path = args.output_dir / "real-pilot/registered_fit_resource_projection.csv"
    synthesis_path = synthesis_dir / "pilot_synthesis.json"
    family_projection_path = synthesis_dir / "resource_projection_by_family.csv"
    top_fits_path = synthesis_dir / "largest_projected_fits.csv"
    audit_path = synthesis_dir / "synthesis_audit.json"
    manifest_path = synthesis_dir / "synthesis_manifest.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    pilot = pd.read_csv(pilot_records_path)
    projection = pd.read_csv(projection_path)
    if projection.empty or len(projection) != 189:
        raise RuntimeError("registered resource projection must contain all 189 fits")
    by_family = (
        projection.groupby("model_family", observed=True)
        .agg(
            registered_fits=("fit_id", "size"),
            projected_cpu_hours=("projected_cpu_hours", "sum"),
            maximum_wall_hours=("projected_wall_hours", "max"),
            projected_output_gb=("projected_output_gb", "sum"),
            maximum_memory_gb=("projected_peak_memory_gb", "max"),
        )
        .reset_index()
    )
    top = projection.nlargest(20, "projected_cpu_hours")[[
        "fit_id", "model_family", "variant", "sample_scope", "age_shape",
        "prior_set", "projected_rows", "projected_wall_hours",
        "projected_cpu_hours", "projected_peak_memory_gb", "projected_output_gb",
    ]]
    atomic_csv(by_family, family_projection_path)
    atomic_csv(top, top_fits_path)
    synthesis = {
        "status": "PILOT_ONLY_STOP_UNSAFE",
        "scientific_posterior_results_available": False,
        "pilot_fit_count": int(len(pilot)),
        "registered_fit_count": int(len(projection)),
        "decision": decision,
        "pilot_diagnostics": {
            "maximum_rhat": float(pilot.rhat_max.max()),
            "minimum_bulk_ess": float(pilot.ess_bulk_min.min()),
            "minimum_tail_ess": float(pilot.ess_tail_min.min()),
            "total_divergences": int(pilot.divergences.sum()),
            "fits_with_divergences": pilot.loc[pilot.divergences > 0, "fit_id"].astype(str).tolist(),
            "maximum_peak_rss_gb": float(pilot.peak_rss_kb.max() / 1024**2),
        },
        "guardrail": "Pilot fits are not used for scientific inference; they are computational and likelihood checks only.",
    }
    atomic_json(synthesis, synthesis_path)
    audit = {
        "status": "PASS_PILOT_ONLY",
        "registered_projection_rows": int(len(projection)),
        "posterior_scientific_claims": 0,
        "problems": [],
    }
    atomic_json(audit, audit_path)
    return write_manifest(
        stage="synthesis",
        manifest_path=manifest_path,
        inputs={
            "diagnostics_manifest": diagnostics_manifest_path,
            "decision": decision_path,
            "pilot_records": pilot_records_path,
            "projection": projection_path,
        },
        outputs={
            "synthesis": synthesis_path,
            "family_projection": family_projection_path,
            "largest_fits": top_fits_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def _save_figure_atomic(figure: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    figure.savefig(temporary, format=path.suffix.lstrip("."), dpi=180, bbox_inches="tight")
    os.replace(temporary, path)


def run_plots_stage(args: argparse.Namespace) -> dict[str, Any]:
    synthesis_manifest_path = args.output_dir / "synthesis/synthesis_manifest.json"
    require_manifest(synthesis_manifest_path, "synthesis")
    matplotlib_config = args.temp_dir / "bayesian-route-matplotlib"
    matplotlib_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    args.figures_dir.mkdir(parents=True, exist_ok=True)
    family_path = args.output_dir / "synthesis/resource_projection_by_family.csv"
    pilot_path = args.output_dir / "real-pilot/fit_records.csv"
    resource_figure_path = args.figures_dir / "pilot_projected_cpu_hours_by_family.png"
    diagnostics_figure_path = args.figures_dir / "pilot_sampler_diagnostics.png"
    audit_path = args.output_dir / "plots/plots_audit.json"
    manifest_path = args.output_dir / "plots/plots_manifest.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    family = pd.read_csv(family_path).sort_values("projected_cpu_hours", ascending=True)
    figure, axis = plt.subplots(figsize=(8, 4.6))
    axis.barh(family.model_family, family.projected_cpu_hours, color="#3b6fb6")
    axis.axvline(2000, color="#b33a3a", linestyle="--", linewidth=1.5, label="whole-program CPU gate")
    axis.set_xlabel("Projected CPU-hours across registered fits")
    axis.set_ylabel("Model family")
    axis.set_title("Bayesian production projection (pilot only; no production fits run)")
    axis.legend(frameon=False)
    _save_figure_atomic(figure, resource_figure_path)
    plt.close(figure)

    pilot = pd.read_csv(pilot_path).sort_values("fit_id")
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].barh(pilot.fit_id, pilot.rhat_max, color="#528b63")
    axes[0].axvline(1.10, color="#b33a3a", linestyle="--")
    axes[0].set_xlabel("Maximum R-hat (pilot gate 1.10)")
    axes[0].set_title("Pilot convergence summary")
    colors = ["#b33a3a" if value > 0 else "#777777" for value in pilot.divergences]
    axes[1].barh(pilot.fit_id, pilot.divergences, color=colors)
    axes[1].set_xlabel("Divergent transitions")
    axes[1].set_title("B5 blocks production with one divergence")
    figure.suptitle("Representative real-data pilot diagnostics—not scientific results")
    _save_figure_atomic(figure, diagnostics_figure_path)
    plt.close(figure)

    audit = {
        "status": "PASS",
        "figures": 2,
        "fitting_functions_called": 0,
        "source": "saved pilot diagnostics and saved resource projections only",
        "problems": [],
    }
    atomic_json(audit, audit_path)
    return write_manifest(
        stage="plots",
        manifest_path=manifest_path,
        inputs={
            "synthesis_manifest": synthesis_manifest_path,
            "family_projection": family_path,
            "pilot_records": pilot_path,
        },
        outputs={
            "resource_figure": resource_figure_path,
            "diagnostics_figure": diagnostics_figure_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def build_pilot_stop_report(payload: Mapping[str, Any]) -> str:
    decision = payload["decision"]
    data = payload["data_audit"]
    synthetic = payload["synthetic_audit"]
    pilot_rows = payload["pilot_records"]
    family_rows = payload["family_projection"]
    pilot_table = "\n".join(
        "| {fit_id} | {elapsed_seconds:.1f} | {rhat_max:.3f} | {ess_bulk_min:.1f} | {divergences} | {peak_gb:.2f} |".format(
            **row, peak_gb=float(row["peak_rss_kb"]) / 1024**2
        )
        for row in pilot_rows
    )
    family_table = "\n".join(
        "| {model_family} | {registered_fits} | {projected_cpu_hours:.1f} | {maximum_wall_hours:.1f} | {projected_output_gb:.1f} |".format(**row)
        for row in family_rows
    )
    blockers = "\n".join(f"- {problem}" for problem in decision["all_problems"])
    guardrails = "\n".join(f"- {guardrail}" for guardrail in payload["guardrails"])
    divergence_rows = [
        row for row in pilot_rows if int(row.get("divergences", 0)) > 0
    ]
    total_divergences = sum(int(row.get("divergences", 0)) for row in pilot_rows)
    if divergence_rows:
        divergence_fits = ", ".join(str(row["fit_id"]) for row in divergence_rows)
        divergence_summary = (
            f"The pilot produced {total_divergences} divergent transition(s) in "
            f"{divergence_fits}. This fails the frozen diagnostic gate and does "
            "not license scientific interpretation of any pilot coefficient."
        )
    else:
        divergence_summary = (
            "All seven representative pilot fits produced zero divergent "
            "transitions. The STOP is imposed by the frozen resource gate, and "
            "no pilot coefficient is licensed for scientific interpretation."
        )
    return f"""# Bayesian Route 1 / Route 2 program: audited pilot handoff

Status: **PILOT STOP — production not run**

This is a post-hoc Bayesian robustness and extension program over the preserved
PBM-discovery, non-PBM-replication, and all-79 descriptive scopes. Existing
outcomes had already been inspected. The seven real-data fits reported here
are computational/likelihood pilots, not scientific posterior results.

## Outcome

The frozen gate returned `{decision['status']}`. No production posterior,
language-model scoring, Mila job, alternative aggregation, or changed estimand
was launched.

{blockers}

The complete 189-fit suite projects to
**{decision['projection_summary']['total_projected_cpu_hours']:.1f} CPU-hours**
against the frozen 2,000-hour ceiling. Maximum projected single-fit wall time
is {decision['projection_summary']['maximum_single_fit_wall_hours']:.1f} hours;
peak memory is {decision['projection_summary']['maximum_peak_memory_gb']:.1f}
GB; total posterior output is {decision['projection_summary']['total_projected_output_gb']:.1f} GB.

## Immutable data and synthetic gates

- Route 1 child utterances: {data['route1_rows']:,}; paired k0-k3 long rows: {data['route1_long_rows']:,}.
- Route 1 audited condition cells: {data['route1_cells']:,}; cell counts sum exactly to {data['route1_cell_n_sum']:,}.
- Route 2 eligible observed utterances: {data['route2_rows']:,}; children: {data['route2_children']}; corpora: {data['route2_corpora']}.
- Literal effort-rank endpoints: {data['rank_zero_endpoints']:,} zero and {data['rank_one_endpoints']:,} one; maximum rank200 error {data['rank200_max_error']:.3g}.
- Synthetic posterior fits: {len(synthetic['observed_synthetic_fits'])}/{len(synthetic['expected_synthetic_fits'])}; deterministic and posterior recovery gates: PASS.

## Representative real-data pilot diagnostics

| Fit | Seconds | max R-hat | min bulk ESS | divergences | peak RSS GB |
|---|---:|---:|---:|---:|---:|
{pilot_table}

{divergence_summary}

## Registered production projection

| Family | Fits | CPU-hours | max wall-hours | output GB |
|---|---:|---:|---:|---:|
{family_table}

The registry is unchanged across `pbm_discovery`, `non_pbm_replication`, and
`all79_descriptive`, three age shapes, and weak/skeptical/wide prior sets.
The STOP cannot be bypassed by silently changing the likelihood, raw-row unit,
sample role, or Qwen adjustment.

## Scientific interpretation boundaries

{guardrails}

## Reproducibility state

- Branch: `{payload['git']['branch']}`; report-build HEAD: `{payload['git']['head']}`.
- Frozen starting SHA: `{payload['starting_git_sha']}`.
- Backend: repository-local brms 2.23.0, cmdstanr 0.9.0, CmdStan 2.39.0.
- Source paper SHA-256: `{payload['source_paper_sha256']}`.
- Production completion marker: deliberately absent.

The next safe step is scientific/computational review of the 189-fit CPU plan
and compilation/execution strategy. Resuming production requires a new
explicitly reviewed gate; it is not an automatic controller action.
"""


def render_pilot_report_html(markdown_text: str) -> str:
    import html
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bayesian Route 1 / Route 2 pilot</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#202124}}pre{{white-space:pre-wrap;font:inherit}} </style>
</head><body><pre>{}</pre></body></html>
""".format(html.escape(markdown_text))


def run_report_stage(args: argparse.Namespace) -> dict[str, Any]:
    plots_manifest_path = args.output_dir / "plots/plots_manifest.json"
    require_manifest(plots_manifest_path, "plots")
    report_dir = args.output_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload_path = report_dir / "report_payload.json"
    audit_path = report_dir / "report_audit.json"
    manifest_path = report_dir / "report_manifest.json"
    contract = load_and_validate_contract(args.contract)
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    payload = {
        "decision": json.loads((args.output_dir / "real-pilot/pilot_decision.json").read_text(encoding="utf-8")),
        "data_audit": json.loads((args.output_dir / "datasets/dataset_audit.json").read_text(encoding="utf-8")),
        "synthetic_audit": json.loads((args.output_dir / "synthetic-smoke/synthetic_smoke_audit.json").read_text(encoding="utf-8")),
        "pilot_records": pd.read_csv(args.output_dir / "real-pilot/fit_records.csv").to_dict(orient="records"),
        "family_projection": pd.read_csv(args.output_dir / "synthesis/resource_projection_by_family.csv").to_dict(orient="records"),
        "guardrails": contract["interpretation_guardrails"],
        "starting_git_sha": contract["starting_git_sha"],
        "source_paper_sha256": contract["source_paper"]["sha256"],
        "git": {"branch": branch, "head": head},
    }
    markdown_text = build_pilot_stop_report(payload)
    html_text = render_pilot_report_html(markdown_text)
    atomic_json(payload, payload_path)
    atomic_text(markdown_text, args.report_md)
    atomic_text(html_text, args.report_html)
    audit = {
        "status": "PASS",
        "program_status": "PILOT_STOP",
        "fitting_functions_called": 0,
        "scientific_posterior_results_reported": 0,
        "markdown_sha256": sha256_text(markdown_text),
        "html_sha256": sha256_text(html_text),
        "problems": [],
    }
    atomic_json(audit, audit_path)
    return write_manifest(
        stage="report",
        manifest_path=manifest_path,
        inputs={
            "plots_manifest": plots_manifest_path,
            "tracked_contract": args.contract,
            "decision": args.output_dir / "real-pilot/pilot_decision.json",
            "data_audit": args.output_dir / "datasets/dataset_audit.json",
            "synthetic_audit": args.output_dir / "synthetic-smoke/synthetic_smoke_audit.json",
            "pilot_records": args.output_dir / "real-pilot/fit_records.csv",
            "family_projection": args.output_dir / "synthesis/resource_projection_by_family.csv",
        },
        outputs={"payload": payload_path, "markdown": args.report_md, "html": args.report_html, "audit": audit_path},
        audit=audit,
    )


def run_audit_stage(args: argparse.Namespace) -> dict[str, Any]:
    report_manifest_path = args.output_dir / "report/report_manifest.json"
    require_manifest(report_manifest_path, "report")
    audit_dir = args.output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "final_audit.json"
    marker_path = audit_dir / "PILOT_STOP_AUDITED"
    manifest_path = audit_dir / "audit_manifest.json"
    completion_marker = args.output_dir / "BAYESIAN_ROUTE1_ROUTE2_COMPLETE_AND_AUDITED"
    contract = load_and_validate_contract(args.contract)
    problems: list[str] = []

    stage_status: dict[str, Any] = {}
    for stage, relative in {
        "contract": "contract/contract_manifest.json",
        "datasets": "datasets/dataset_manifest.json",
        "priors": "priors/priors_manifest.json",
        "synthetic-smoke": "synthetic-smoke/synthetic_smoke_manifest.json",
        "real-pilot": "real-pilot/real_pilot_manifest.json",
        "models": "models/models_manifest.json",
        "diagnostics": "diagnostics/diagnostics_manifest.json",
        "synthesis": "synthesis/synthesis_manifest.json",
        "plots": "plots/plots_manifest.json",
        "report": "report/report_manifest.json",
    }.items():
        try:
            manifest = require_manifest(args.output_dir / relative, stage)
            stage_status[stage] = manifest.get("audit", {}).get("status", "UNKNOWN")
        except Exception as error:  # independent audit records the exact failure
            problems.append(f"{stage}: {error}")

    decision = json.loads(
        (args.output_dir / "real-pilot/pilot_decision.json").read_text(encoding="utf-8")
    )
    if decision.get("safe_to_proceed") or decision.get("status") != "STOP_UNSAFE":
        problems.append("real-pilot STOP_UNSAFE decision is not preserved")
    blocked_inventory = pd.read_csv(args.output_dir / "models/production_fit_inventory.csv")
    completion_audit = audit_completion_inventory(blocked_inventory, contract)
    if completion_audit["status"] != "FAIL":
        problems.append("production completion audit did not refuse blocked fits")
    if completion_marker.exists():
        problems.append("production completion marker exists despite pilot STOP")

    payload = json.loads(
        (args.output_dir / "report/report_payload.json").read_text(encoding="utf-8")
    )
    rebuilt_markdown = build_pilot_stop_report(payload)
    rebuilt_html = render_pilot_report_html(rebuilt_markdown)
    if sha256_text(rebuilt_markdown) != sha256_file(args.report_md):
        problems.append("Markdown report is not a deterministic rebuild from saved payload")
    if sha256_text(rebuilt_html) != sha256_file(args.report_html):
        problems.append("HTML report is not a deterministic rebuild from saved payload")
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    if branch != "agent/bayesian-route1-route2-v1":
        problems.append(f"unexpected branch: {branch}")

    audit = {
        "status": "PASS_PILOT_STOP_AUDITED" if not problems else "FAIL",
        "program_status": "PILOT_STOP",
        "stage_status": stage_status,
        "real_pilot_decision": decision["status"],
        "production_completion_audit": completion_audit,
        "production_completion_marker_present": completion_marker.exists(),
        "pilot_stop_marker": str(marker_path),
        "branch": branch,
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("independent pilot-stop audit failed: " + "; ".join(problems))
    atomic_text(
        "PILOT_STOP_AUDITED\nNo production posterior fits were authorized or completed.\n",
        marker_path,
    )
    return write_manifest(
        stage="audit",
        manifest_path=manifest_path,
        inputs={"report_manifest": report_manifest_path, "tracked_contract": args.contract},
        outputs={"audit": audit_path, "pilot_stop_marker": marker_path},
        audit=audit,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("contract", "datasets", "priors", "synthetic-smoke", "real-pilot", "models", "diagnostics", "synthesis", "plots", "report", "audit", "all"),
        default="contract",
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--temp-dir", type=Path, default=Path("/tmp"))
    parser.add_argument("--duckdb-memory-limit", default="12GB")
    parser.add_argument("--smoke-chains", type=int, default=2)
    parser.add_argument("--smoke-warmup", type=int, default=100)
    parser.add_argument("--smoke-sampling", type=int, default=100)
    parser.add_argument("--pilot-bootstrap-draws", type=int, default=100)
    parser.add_argument("--pilot-b5-rows-per-child", type=int, default=1500)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    stages = (
        "contract", "datasets", "priors", "synthetic-smoke", "real-pilot",
        "models", "diagnostics", "synthesis", "plots", "report", "audit",
    ) if args.stage == "all" else (args.stage,)
    for stage in stages:
        print(f"[{stage}] starting", flush=True)
        if stage == "contract":
            run_contract_stage(args)
        elif stage == "datasets":
            run_datasets_stage(args)
        elif stage == "priors":
            run_priors_stage(args)
        elif stage == "synthetic-smoke":
            run_synthetic_smoke_stage(args)
        elif stage == "real-pilot":
            run_real_pilot_stage(args)
        elif stage == "models":
            run_models_stage(args)
        elif stage == "diagnostics":
            run_diagnostics_stage(args)
        elif stage == "synthesis":
            run_synthesis_stage(args)
        elif stage == "plots":
            run_plots_stage(args)
        elif stage == "report":
            run_report_stage(args)
        elif stage == "audit":
            run_audit_stage(args)
        else:
            raise SystemExit(f"stage {stage!r} is registered but not implemented yet")
        print(f"[{stage}] complete", flush=True)


if __name__ == "__main__":
    main()
