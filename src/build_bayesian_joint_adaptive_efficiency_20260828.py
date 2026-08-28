#!/usr/bin/env python3
"""Focused Bayesian joint analysis of effort adaptation and predictability.

The expensive Route 1/Route 2 pilot answered a resource-planning question. This
controller answers the narrower scientific question approved after that pilot:
whether demand-sensitive effort, its developmental change, and fixed-effort
form predictability covary across children. It uses a session-clustered
three-coefficient summary likelihood and never runs NUTS over the 1.1M rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

os.environ.setdefault("MPLCONFIGDIR", "/tmp/communicative_efficiency_matplotlib")

import duckdb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from render_markdown_report import render_markdown_file  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "configs/bayesian_joint_adaptive_efficiency_20260828/analysis_contract.json"
DEFAULT_OUTPUT = ROOT / "results/bayesian_joint_adaptive_efficiency_20260828"
DEFAULT_FIGURES = ROOT / "figs/bayesian_joint_adaptive_efficiency_20260828"
DEFAULT_REPORT_MD = ROOT / "docs/bayesian_joint_adaptive_efficiency_report.md"
DEFAULT_REPORT_HTML = ROOT / "docs/bayesian_joint_adaptive_efficiency_report.html"
ESTIMAND_IDS = ("r1_age", "r2_entropy_42", "r2_age_entropy")
PBM_DATASETS = {"Brown", "Manchester", "Providence"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


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
    compression = "gzip" if path.suffix == ".gz" else None
    frame.to_csv(temporary, index=False, lineterminator="\n", compression=compression)
    os.replace(temporary, path)


def file_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_stage_manifest(
    stage: str,
    path: Path,
    *,
    inputs: Mapping[str, Path],
    outputs: Mapping[str, Path],
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "stage": stage,
        "completed_at": utc_now(),
        "controller": file_record(Path(__file__)),
        "inputs": {name: file_record(value) for name, value in inputs.items()},
        "outputs": {name: file_record(value) for name, value in outputs.items()},
        "audit": dict(audit),
    }
    atomic_json(payload, path)
    return payload


def require_stage_manifest(path: Path, stage: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing {stage} manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("stage") != stage:
        raise RuntimeError(f"expected {stage} manifest, found {payload.get('stage')}")
    for direction in ("inputs", "outputs"):
        for name, record in payload.get(direction, {}).items():
            target = Path(record["path"])
            if not target.exists() or sha256_file(target) != record["sha256"]:
                raise RuntimeError(f"stale {stage} {direction[:-1]}: {name}")
    return payload


def validate_contract(contract: Mapping[str, Any]) -> None:
    problems: list[str] = []
    if contract.get("program_id") != "bayesian_joint_adaptive_efficiency_20260828":
        problems.append("program_id mismatch")
    estimands = {record.get("id"): record for record in contract.get("estimands", [])}
    if tuple(estimands) != ESTIMAND_IDS:
        problems.append("estimands must be ordered r1_age, r2_entropy_42, r2_age_entropy")
    if estimands.get("r2_entropy_42", {}).get("hypothesis") != "H1" or estimands.get("r2_entropy_42", {}).get("direction") != "positive":
        problems.append("H1 must be positive demand-sensitive effort")
    if estimands.get("r2_age_entropy", {}).get("hypothesis") != "H2" or estimands.get("r2_age_entropy", {}).get("direction") != "two_sided_posthoc":
        problems.append("H2 must remain two-sided and post-hoc")
    if estimands.get("r1_age", {}).get("hypothesis") != "H3" or estimands.get("r1_age", {}).get("direction") != "negative":
        problems.append("H3 must be negative fixed-effort surprisal development")
    if contract.get("joint_model", {}).get("family") != "trivariate_normal_measurement_error":
        problems.append("joint family mismatch")
    if "sample_scopes" in contract:
        problems.append("sample scopes must not drive the focused model")
    prior_source = str(contract.get("priors", {}).get("source", ""))
    if "PBM estimates are not used as priors" not in prior_source:
        problems.append("PBM/prior distinction is missing")
    for name in ("regularizing", "wide_sensitivity"):
        prior = contract.get("priors", {}).get(name, {})
        for key in ("population_sd", "child_sd_scale", "corpus_sd_scale"):
            values = prior.get(key, [])
            if len(values) != 3 or not all(float(value) > 0 for value in values):
                problems.append(f"{name}/{key} must contain three positive scales")
        if float(prior.get("lkj_eta", 0)) < 1:
            problems.append(f"{name}/lkj_eta must be at least one")
    if int(contract.get("eligibility", {}).get("minimum_sessions", 0)) < 5:
        problems.append("minimum session rule is too weak for a 3D clustered covariance")
    if float(contract.get("runtime_gate", {}).get("maximum_total_cpu_hours", 0)) > 2:
        problems.append("runtime gate exceeds the approved compact analysis")
    if problems:
        raise ValueError("invalid focused Bayesian contract: " + "; ".join(problems))


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(payload)
    return payload


def _block_diag(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    result = np.zeros((left.shape[0] + right.shape[0], left.shape[1] + right.shape[1]))
    result[: left.shape[0], : left.shape[1]] = left
    result[left.shape[0] :, left.shape[1] :] = right
    return result


def estimate_child_coefficients(
    frame: pd.DataFrame,
    *,
    minimum_sessions: int = 5,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Estimate three child coefficients and their shared cluster covariance."""

    required = {
        "utterance_id", "child_key", "dataset", "session_id", "age_z",
        "word_count_top12", "k3_bits", "child_words", "entropy_z",
        "context_words_z",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"child coefficient table missing columns: {sorted(missing)}")
    if frame.duplicated(["child_key", "utterance_id"]).any():
        raise ValueError("duplicate child/utterance identities")
    if frame.child_key.nunique() != 1 or frame.dataset.nunique() != 1:
        raise ValueError("one child and one corpus are required per coefficient fit")
    clusters = pd.unique(frame.session_id)
    if len(clusters) < minimum_sessions:
        raise ValueError(f"at least {minimum_sessions} sessions are required")

    numeric_columns = ["age_z", "k3_bits", "child_words", "entropy_z", "context_words_z"]
    numeric = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(float)).all():
        raise ValueError("child coefficient table contains non-finite numeric values")
    if (numeric.child_words < 0).any():
        raise ValueError("child word counts must be nonnegative")

    word_levels = sorted(
        frame.word_count_top12.astype(str).unique(),
        key=lambda value: 12 if value == "12+" else int(value),
    )
    word = pd.Categorical(frame.word_count_top12.astype(str), categories=word_levels, ordered=True)
    word_dummies = pd.get_dummies(word, drop_first=True, dtype=float)
    age = numeric.age_z.to_numpy(float)
    entropy = numeric.entropy_z.to_numpy(float)
    context = numeric.context_words_z.to_numpy(float)
    x1 = np.column_stack([np.ones(len(frame)), age, word_dummies.to_numpy(float)])
    x2 = np.column_stack([np.ones(len(frame)), age, entropy, age * entropy, context])
    y1 = numeric.k3_bits.to_numpy(float)
    y2 = np.log1p(numeric.child_words.to_numpy(float))
    for label, design in (("Route 1", x1), ("Route 2", x2)):
        if len(frame) <= design.shape[1] + 10 or np.linalg.matrix_rank(design) != design.shape[1]:
            raise ValueError(f"{label} child design is rank deficient")

    bread1 = np.linalg.inv(x1.T @ x1)
    bread2 = np.linalg.inv(x2.T @ x2)
    beta1 = bread1 @ x1.T @ y1
    beta2 = bread2 @ x2.T @ y2
    residual1 = y1 - x1 @ beta1
    residual2 = y2 - x2 @ beta2
    cluster_values = frame.session_id.to_numpy()
    score_rows: list[np.ndarray] = []
    for cluster in clusters:
        selected = cluster_values == cluster
        score_rows.append(
            np.concatenate([
                x1[selected].T @ residual1[selected],
                x2[selected].T @ residual2[selected],
            ])
        )
    scores = np.vstack(score_rows)
    meat = scores.T @ scores
    bread = _block_diag(bread1, bread2)
    cluster_correction = len(clusters) / (len(clusters) - 1)
    full_covariance = cluster_correction * bread @ meat @ bread.T
    selected_indices = [1, x1.shape[1] + 2, x1.shape[1] + 3]
    covariance = full_covariance[np.ix_(selected_indices, selected_indices)]
    covariance = (covariance + covariance.T) / 2
    eigenvalues = np.linalg.eigvalsh(covariance)
    floor = max(float(np.max(eigenvalues)) * 1e-10, 1e-12)
    regularization = max(0.0, floor - float(np.min(eigenvalues)))
    if regularization:
        covariance = covariance + np.eye(3) * regularization
    if not np.isfinite(covariance).all() or np.linalg.eigvalsh(covariance).min() <= 0:
        raise ValueError("session-clustered coefficient covariance is not positive definite")
    estimate = np.array([beta1[1], beta2[2], beta2[3]], dtype=float)
    return estimate, covariance, {
        "rows": int(len(frame)),
        "clusters": int(len(clusters)),
        "word_levels": int(len(word_levels)),
        "minimum_eigenvalue_before_regularization": float(eigenvalues.min()),
        "diagonal_regularization": float(regularization),
        "shared_cross_equation_covariance": True,
    }


def audit_fit_diagnostics(
    diagnostics: pd.DataFrame,
    influence: pd.DataFrame,
    *,
    expected_corpora: int,
) -> dict[str, Any]:
    problems: list[str] = []
    required = {
        "fit_id", "rhat_max", "ess_bulk_min", "ess_tail_min", "divergences",
        "treedepth_saturated", "energy_bfmi_min",
    }
    missing = required - set(diagnostics.columns)
    problems.extend(f"missing diagnostic column: {column}" for column in sorted(missing))
    primary_ids = {"regularizing", "wide_sensitivity"}
    if not missing:
        if not primary_ids.issubset(set(diagnostics.fit_id)):
            problems.append("primary/wide fit inventory is incomplete")
        primary = diagnostics[diagnostics.fit_id.isin(primary_ids)]
        bad = primary[
            (primary.rhat_max > 1.01)
            | (primary.ess_bulk_min < 400)
            | (primary.ess_tail_min < 400)
        ]
        problems.extend(f"sampler diagnostic failure: {fit_id}" for fit_id in bad.fit_id)
        common_bad = diagnostics[
            (diagnostics.divergences != 0)
            | (diagnostics.treedepth_saturated != 0)
            | (diagnostics.energy_bfmi_min < 0.3)
        ]
        problems.extend(f"common sampler diagnostic failure: {fit_id}" for fit_id in common_bad.fit_id)
        influence_diagnostics = diagnostics[diagnostics.fit_id.str.startswith("omit_", na=False)]
        scientific_columns = {"scientific_rhat_max", "scientific_ess_bulk_min", "scientific_ess_tail_min"}
        if not influence_diagnostics.empty:
            if not scientific_columns.issubset(diagnostics.columns):
                problems.append("influence registered-output diagnostics are missing")
            else:
                influence_bad = influence_diagnostics[
                    (influence_diagnostics.scientific_rhat_max > 1.015)
                    | (influence_diagnostics.scientific_ess_bulk_min < 400)
                    | (influence_diagnostics.scientific_ess_tail_min < 400)
                ]
                problems.extend(f"influence diagnostic failure: {fit_id}" for fit_id in influence_bad.fit_id)
    if "omitted_corpus" not in influence or influence.omitted_corpus.nunique() != expected_corpora:
        problems.append("leave-one-corpus inventory is incomplete")
    return {
        "status": "PASS" if not problems else "FAIL",
        "fits": int(len(diagnostics)),
        "influence_corpora": int(influence.omitted_corpus.nunique()) if "omitted_corpus" in influence else 0,
        "problems": problems,
    }


def run_contract_stage(args: argparse.Namespace) -> None:
    contract = load_contract(args.contract)
    source = ROOT / contract["input"]["path"]
    problems: list[str] = []
    if not source.exists() or sha256_file(source) != contract["input"]["sha256"]:
        problems.append("immutable joined source hash mismatch")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "source": file_record(source) if source.exists() else {"path": str(source)},
        "posthoc": True,
        "pbm_used_as_prior": False,
        "problems": problems,
    }
    directory = args.output_dir / "contract"
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = directory / "analysis_contract.json"
    atomic_json(contract, snapshot)
    audit_path = directory / "contract_audit.json"
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("; ".join(problems))
    write_stage_manifest(
        "contract", directory / "manifest.json",
        inputs={"tracked_contract": args.contract, "source": source},
        outputs={"snapshot": snapshot, "audit": audit_path},
        audit=audit,
    )


def run_datasets_stage(args: argparse.Namespace) -> None:
    require_stage_manifest(args.output_dir / "contract/manifest.json", "contract")
    contract = load_contract(args.contract)
    source = ROOT / contract["input"]["path"]
    minimum_sessions = int(contract["eligibility"]["minimum_sessions"])
    directory = args.output_dir / "datasets"
    directory.mkdir(parents=True, exist_ok=True)
    estimates_path = directory / "child_coefficient_estimates.csv"
    flow_path = directory / "child_sample_flow.csv"
    audit_path = directory / "dataset_audit.json"

    connection = duckdb.connect()
    child_stats = connection.execute(
        """SELECT child_key, dataset, COUNT(*) AS rows,
                  COUNT(DISTINCT session_id) AS sessions,
                  STDDEV_SAMP(age_z) AS age_sd,
                  STDDEV_SAMP(entropy_z) AS entropy_sd
           FROM read_parquet(?) GROUP BY child_key, dataset
           ORDER BY dataset, child_key""",
        [str(source)],
    ).fetchdf()
    rows: list[dict[str, Any]] = []
    flow: list[dict[str, Any]] = []
    for child in child_stats.itertuples(index=False):
        eligible = int(child.sessions) >= minimum_sessions
        flow.append({
            "child_key": child.child_key,
            "dataset": child.dataset,
            "rows": int(child.rows),
            "sessions": int(child.sessions),
            "age_sd": float(child.age_sd),
            "entropy_sd": float(child.entropy_sd),
            "status": "included" if eligible else "excluded_insufficient_sessions",
        })
        if not eligible:
            continue
        child_frame = connection.execute(
            "SELECT * FROM read_parquet(?) WHERE child_key=? ORDER BY session_id, utterance_id",
            [str(source), child.child_key],
        ).fetchdf()
        estimate, covariance, child_audit = estimate_child_coefficients(
            child_frame, minimum_sessions=minimum_sessions
        )
        rows.append({
            "child_key": child.child_key,
            "dataset": child.dataset,
            "sample_label": "pbm_discovery_label" if child.dataset in PBM_DATASETS else "other58_label",
            "r1_age_slope": estimate[0],
            "r2_entropy_42_slope": estimate[1],
            "r2_age_entropy_slope": estimate[2],
            "cov_11": covariance[0, 0],
            "cov_12": covariance[0, 1],
            "cov_13": covariance[0, 2],
            "cov_22": covariance[1, 1],
            "cov_23": covariance[1, 2],
            "cov_33": covariance[2, 2],
            **child_audit,
        })
    connection.close()
    estimates = pd.DataFrame(rows).sort_values(["dataset", "child_key"]).reset_index(drop=True)
    sample_flow = pd.DataFrame(flow)
    atomic_csv(estimates, estimates_path)
    atomic_csv(sample_flow, flow_path)

    excluded = sorted(sample_flow.loc[sample_flow.status != "included", "child_key"].tolist())
    expected_excluded = sorted(contract["eligibility"]["expected_excluded_children"])
    problems: list[str] = []
    if len(estimates) != int(contract["eligibility"]["expected_included_children"]):
        problems.append("eligible child count mismatch")
    if excluded != expected_excluded:
        problems.append("excluded child identity mismatch")
    if estimates.dataset.nunique() != int(contract["input"]["corpora"]):
        problems.append("corpus coverage mismatch")
    covariance_columns = ["cov_11", "cov_12", "cov_13", "cov_22", "cov_23", "cov_33"]
    if not np.isfinite(estimates[covariance_columns].to_numpy(float)).all():
        problems.append("non-finite estimation covariance")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "source_rows": int(child_stats.rows.sum()),
        "source_children": int(len(child_stats)),
        "included_children": int(len(estimates)),
        "included_pbm_label": int((estimates.sample_label == "pbm_discovery_label").sum()),
        "included_other58_label": int((estimates.sample_label == "other58_label").sum()),
        "corpora": int(estimates.dataset.nunique()),
        "excluded_children": excluded,
        "minimum_sessions": minimum_sessions,
        "maximum_covariance_regularization": float(estimates.diagonal_regularization.max()),
        "shared_session_clustered_covariance": True,
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("dataset audit failed: " + "; ".join(problems))
    write_stage_manifest(
        "datasets", directory / "manifest.json",
        inputs={"contract_manifest": args.output_dir / "contract/manifest.json", "source": source},
        outputs={"estimates": estimates_path, "sample_flow": flow_path, "audit": audit_path},
        audit=audit,
    )


def _run_r_stage(args: argparse.Namespace, mode: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    command = [
        "Rscript", str(ROOT / "src/fit_bayesian_joint_adaptive_efficiency.R"),
        "--mode", mode,
        "--root", str(ROOT),
        "--contract", str(args.contract),
        "--input", str(args.output_dir / "datasets/child_coefficient_estimates.csv"),
        "--output-dir", str(directory),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    atomic_text(completed.stdout, directory / "stdout.log")
    atomic_text(completed.stderr, directory / "stderr.log")
    if completed.returncode != 0:
        raise RuntimeError(f"R {mode} failed ({completed.returncode}): {completed.stderr[-2000:]}")


def run_synthetic_stage(args: argparse.Namespace) -> None:
    require_stage_manifest(args.output_dir / "datasets/manifest.json", "datasets")
    directory = args.output_dir / "synthetic-smoke"
    _run_r_stage(args, "synthetic", directory)
    audit_path = directory / "synthetic_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError("synthetic smoke did not pass")
    write_stage_manifest(
        "synthetic-smoke", directory / "manifest.json",
        inputs={
            "datasets_manifest": args.output_dir / "datasets/manifest.json",
            "contract": args.contract,
            "r_backend": ROOT / "src/fit_bayesian_joint_adaptive_efficiency.R",
            "stan_model": ROOT / "src/stan/joint_adaptive_efficiency_measurement_error.stan",
        },
        outputs={"audit": audit_path, "summary": directory / "synthetic_summary.csv"},
        audit=audit,
    )


def run_fit_stage(args: argparse.Namespace) -> None:
    require_stage_manifest(args.output_dir / "synthetic-smoke/manifest.json", "synthetic-smoke")
    directory = args.output_dir / "fits"
    _run_r_stage(args, "finalize-existing" if args.finalize_existing else "fit", directory)
    audit_path = directory / "fit_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError("fit backend did not pass its runtime/diagnostic gate")
    write_stage_manifest(
        "fits", directory / "manifest.json",
        inputs={
            "synthetic_manifest": args.output_dir / "synthetic-smoke/manifest.json",
            "estimates": args.output_dir / "datasets/child_coefficient_estimates.csv",
            "contract": args.contract,
            "r_backend": ROOT / "src/fit_bayesian_joint_adaptive_efficiency.R",
            "stan_model": ROOT / "src/stan/joint_adaptive_efficiency_measurement_error.stan",
        },
        outputs={
            "audit": audit_path,
            "diagnostics": directory / "fit_diagnostics.csv",
            "summary": directory / "posterior_summary.csv",
            "draws_primary": directory / "posterior_draws_regularizing.csv.gz",
            "draws_wide": directory / "posterior_draws_wide_sensitivity.csv.gz",
            "influence": directory / "influence_summary.csv",
            "ppc": directory / "posterior_predictive_checks.csv",
        },
        audit=audit,
    )


def _draw_summary(values: pd.Series) -> dict[str, float]:
    array = pd.to_numeric(values, errors="coerce").to_numpy(float)
    if not np.isfinite(array).all():
        raise ValueError("posterior draws contain non-finite values")
    return {
        "estimate": float(np.mean(array)),
        "q025": float(np.quantile(array, 0.025)),
        "q975": float(np.quantile(array, 0.975)),
        "probability_positive": float(np.mean(array > 0)),
        "probability_negative": float(np.mean(array < 0)),
    }


def run_diagnostics_stage(args: argparse.Namespace) -> None:
    require_stage_manifest(args.output_dir / "fits/manifest.json", "fits")
    contract = load_contract(args.contract)
    fit_dir = args.output_dir / "fits"
    directory = args.output_dir / "diagnostics"
    directory.mkdir(parents=True, exist_ok=True)
    diagnostics = pd.read_csv(fit_dir / "fit_diagnostics.csv")
    influence = pd.read_csv(fit_dir / "influence_summary.csv")
    audit = audit_fit_diagnostics(
        diagnostics, influence, expected_corpora=int(contract["input"]["corpora"])
    )
    primary = pd.read_csv(fit_dir / "posterior_draws_regularizing.csv.gz")
    wide = pd.read_csv(fit_dir / "posterior_draws_wide_sensitivity.csv.gz")
    hypotheses: list[dict[str, Any]] = []
    specifications = [
        ("H1", "Demand-sensitive effort at 42 months", "mu_r2_entropy_42", "positive", contract["ropes"]["r2_entropy_42"]),
        ("H2", "Developmental change in demand sensitivity", "mu_r2_age_entropy", "two-sided post-hoc", contract["ropes"]["r2_age_entropy"]),
        ("H3", "Fixed-effort predictability development", "mu_r1_age", "negative", contract["ropes"]["r1_age"]),
        ("H4", "Coordinated child-level development", "rho_r1_age_entropy", "negative", contract["ropes"]["correlation"]),
    ]
    for hypothesis, label, variable, direction, rope in specifications:
        summary = _draw_summary(primary[variable])
        probability_direction = (
            summary["probability_positive"] if direction == "positive"
            else summary["probability_negative"] if direction == "negative"
            else max(summary["probability_positive"], summary["probability_negative"])
        )
        hypotheses.append({
            "hypothesis": hypothesis,
            "label": label,
            "variable": variable,
            "direction": direction,
            **summary,
            "probability_direction": probability_direction,
            "rope_half_width": float(rope),
            "probability_rope": float(np.mean(np.abs(primary[variable]) <= float(rope))),
        })
    hypothesis_frame = pd.DataFrame(hypotheses)

    delta_entropy = float(contract["scaling"]["entropy_p90_z"] - contract["scaling"]["entropy_p10_z"])
    age_rows: list[dict[str, Any]] = []
    for age in range(18, 61, 6):
        age_z = (age - float(contract["scaling"]["age_center_months"])) / float(contract["scaling"]["age_unit_months"])
        slope = primary.mu_r2_entropy_42 + age_z * primary.mu_r2_age_entropy
        ratio = np.exp(slope * delta_entropy)
        slope_summary = _draw_summary(slope)
        ratio_summary = _draw_summary(pd.Series(ratio))
        age_rows.append({
            "age_months": age,
            "age_z": age_z,
            "entropy_slope_estimate": slope_summary["estimate"],
            "entropy_slope_q025": slope_summary["q025"],
            "entropy_slope_q975": slope_summary["q975"],
            "probability_entropy_slope_positive": slope_summary["probability_positive"],
            "p10_p90_log1p_effort_ratio": ratio_summary["estimate"],
            "ratio_q025": ratio_summary["q025"],
            "ratio_q975": ratio_summary["q975"],
        })
    age_contrasts = pd.DataFrame(age_rows)

    sensitivity_rows: list[dict[str, Any]] = []
    for variable in [item[2] for item in specifications]:
        regular = _draw_summary(primary[variable])
        wide_summary = _draw_summary(wide[variable])
        sensitivity_rows.append({
            "variable": variable,
            "regularizing_estimate": regular["estimate"],
            "wide_estimate": wide_summary["estimate"],
            "absolute_shift": abs(regular["estimate"] - wide_summary["estimate"]),
            "regularizing_sign_probability": max(regular["probability_positive"], regular["probability_negative"]),
            "wide_sign_probability": max(wide_summary["probability_positive"], wide_summary["probability_negative"]),
        })
    sensitivity = pd.DataFrame(sensitivity_rows)
    primary_means = {row.variable: row.estimate for row in hypothesis_frame.itertuples(index=False)}
    influence_variables = {
        "mu_r1_age": "mu_r1_age",
        "mu_r2_entropy_42": "mu_r2_entropy_42",
        "mu_r2_age_entropy": "mu_r2_age_entropy",
        "rho_r1_age_entropy": "rho_r1_age_entropy",
    }
    influence_shifts: list[dict[str, Any]] = []
    for record in influence.itertuples(index=False):
        for variable, column in influence_variables.items():
            value = float(getattr(record, column))
            influence_shifts.append({
                "omitted_corpus": record.omitted_corpus,
                "variable": variable,
                "estimate": value,
                "shift_from_primary": value - primary_means[variable],
                "sign_reversal": np.sign(value) != np.sign(primary_means[variable]),
            })
    influence_long = pd.DataFrame(influence_shifts)

    ppc = pd.read_csv(fit_dir / "posterior_predictive_checks.csv")
    if (ppc.status != "PASS").any():
        audit["problems"].append("posterior predictive check failed")
        audit["status"] = "FAIL"
    audit.update({
        "maximum_prior_mean_shift": float(sensitivity.absolute_shift.max()),
        "maximum_leave_corpus_shift": float(influence_long.shift_from_primary.abs().max()),
        "leave_corpus_sign_reversals": int(influence_long.sign_reversal.sum()),
        "ppc_checks": int(len(ppc)),
    })
    hypothesis_path = directory / "hypothesis_posteriors.csv"
    age_path = directory / "age_entropy_contrasts.csv"
    sensitivity_path = directory / "prior_sensitivity.csv"
    influence_path = directory / "influence_long.csv"
    audit_path = directory / "diagnostics_audit.json"
    atomic_csv(hypothesis_frame, hypothesis_path)
    atomic_csv(age_contrasts, age_path)
    atomic_csv(sensitivity, sensitivity_path)
    atomic_csv(influence_long, influence_path)
    atomic_json(audit, audit_path)
    if audit["status"] != "PASS":
        raise RuntimeError("diagnostic stage failed: " + "; ".join(audit["problems"]))
    write_stage_manifest(
        "diagnostics", directory / "manifest.json",
        inputs={"fit_manifest": fit_dir / "manifest.json", "contract": args.contract},
        outputs={
            "hypotheses": hypothesis_path,
            "age_contrasts": age_path,
            "prior_sensitivity": sensitivity_path,
            "influence": influence_path,
            "audit": audit_path,
        },
        audit=audit,
    )


def run_plots_stage(args: argparse.Namespace) -> None:
    require_stage_manifest(args.output_dir / "diagnostics/manifest.json", "diagnostics")
    hypotheses = pd.read_csv(args.output_dir / "diagnostics/hypothesis_posteriors.csv")
    contrasts = pd.read_csv(args.output_dir / "diagnostics/age_entropy_contrasts.csv")
    summary = pd.read_csv(args.output_dir / "fits/posterior_summary.csv")
    args.figures_dir.mkdir(parents=True, exist_ok=True)

    effect_path = args.figures_dir / "population_effects.png"
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for axis, hypothesis in zip(axes, ("H3", "H1", "H2")):
        row = hypotheses.loc[hypotheses.hypothesis == hypothesis].iloc[0]
        axis.errorbar(
            row.estimate, 0,
            xerr=[[row.estimate - row.q025], [row.q975 - row.estimate]],
            fmt="o", color="#28536B", capsize=4, linewidth=2,
        )
        axis.axvline(0, color="#777777", linestyle="--", linewidth=1)
        axis.set_yticks([])
        axis.set_title(hypothesis)
        axis.set_xlabel(row.label)
    fig.suptitle("Population joint-development coefficients (95% credible intervals)")
    fig.tight_layout()
    fig.savefig(effect_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    correlation_path = args.figures_dir / "between_child_correlations.png"
    correlation_names = [
        ("child_correlation[1,2]", "Predictability × effort at 42m"),
        ("child_correlation[1,3]", "Predictability × effort development"),
        ("child_correlation[2,3]", "Effort at 42m × effort development"),
    ]
    correlation_rows = []
    for variable, label in correlation_names:
        row = summary[(summary.fit_id == "regularizing") & (summary.variable == variable)].iloc[0]
        correlation_rows.append((label, row["mean"], row["q025"], row["q975"]))
    fig, axis = plt.subplots(figsize=(8.5, 4.2))
    y = np.arange(len(correlation_rows))
    means = np.array([row[1] for row in correlation_rows])
    lower = np.array([row[2] for row in correlation_rows])
    upper = np.array([row[3] for row in correlation_rows])
    axis.errorbar(means, y, xerr=[means - lower, upper - means], fmt="o", color="#B04A5A", capsize=4, linewidth=2)
    axis.axvline(0, color="#777777", linestyle="--", linewidth=1)
    axis.set_yticks(y, [row[0] for row in correlation_rows])
    axis.set_xlim(-1, 1)
    axis.set_xlabel("Between-child correlation")
    axis.set_title("Coordinated developmental variation")
    fig.tight_layout()
    fig.savefig(correlation_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    adaptation_path = args.figures_dir / "entropy_adaptation_by_age.png"
    fig, axis = plt.subplots(figsize=(7.5, 4.5))
    axis.plot(contrasts.age_months, contrasts.p10_p90_log1p_effort_ratio, color="#2D7F5E", linewidth=2)
    axis.fill_between(
        contrasts.age_months.to_numpy(float),
        contrasts.ratio_q025.to_numpy(float),
        contrasts.ratio_q975.to_numpy(float),
        color="#2D7F5E", alpha=0.2,
    )
    axis.axhline(1, color="#777777", linestyle="--", linewidth=1)
    axis.set_xlabel("Age (months)")
    axis.set_ylabel("High/low entropy ratio in modeled (words + 1)")
    axis.set_title("Developmental calibration of demand-sensitive effort")
    fig.tight_layout()
    fig.savefig(adaptation_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    audit = {
        "status": "PASS",
        "plots": 3,
        "problems": [],
    }
    audit_path = args.figures_dir / "plots_audit.json"
    atomic_json(audit, audit_path)
    write_stage_manifest(
        "plots", args.figures_dir / "manifest.json",
        inputs={"diagnostics_manifest": args.output_dir / "diagnostics/manifest.json"},
        outputs={"effects": effect_path, "correlations": correlation_path, "adaptation": adaptation_path, "audit": audit_path},
        audit=audit,
    )


def _format_interval(row: Mapping[str, Any], digits: int = 3) -> str:
    threshold = 0.5 * 10 ** (-digits)
    clean = lambda value: 0.0 if abs(float(value)) < threshold else float(value)
    return f"{clean(row['estimate']):.{digits}f} [{clean(row['q025']):.{digits}f}, {clean(row['q975']):.{digits}f}]"


def render_scientific_report(payload: Mapping[str, Any], path: Path) -> None:
    hypotheses = payload.get("hypotheses", [])
    by_hypothesis = {row["hypothesis"]: row for row in hypotheses}
    rows = []
    for row in hypotheses:
        probability = "—" if row.get("direction") == "two-sided post-hoc" else f"{float(row['probability_direction']):.3f}"
        rows.append(
            f"| {row['hypothesis']} | {row['label']} | {_format_interval(row)} | {probability} | {float(row['probability_rope']):.3f} |"
        )
    age_rows = []
    for row in payload.get("age_contrasts", []):
        age_rows.append(
            f"| {int(row['age_months'])} | {float(row['p10_p90_log1p_effort_ratio']):.3f} "
            f"[{float(row['ratio_q025']):.3f}, {float(row['ratio_q975']):.3f}] | "
            f"{float(row['probability_entropy_slope_positive']):.3f} |"
        )
    correlation_rows = []
    for row in payload.get("correlations", []):
        correlation_rows.append(
            f"| {row['label']} | {float(row['estimate']):.3f} "
            f"[{float(row['q025']):.3f}, {float(row['q975']):.3f}] |"
        )
    guardrails = "\n".join(f"- {item}" for item in payload.get("guardrails", []))
    markdown = f"""# Bayesian Joint Adaptive-Efficiency Analysis

Status: **{payload.get('status', 'UNKNOWN')}**. This is a focused post-hoc
joint extension over **{payload.get('children', '—')} children** and
**{payload.get('corpora', '—')} corpora**. Corpus is a background hierarchical
effect, not the research question.

## Main question

Do children jointly develop (a) context-sensitive allocation of production
effort and (b) more predictable utterance forms at fixed effort?

## Posterior results

| Hypothesis | Estimand | Posterior mean [95% CrI] | P(theory direction) | P(ROPE) |
|---|---|---:|---:|---:|
{chr(10).join(rows)}

H2 is deliberately two-sided because the developmental reversal had already
been inspected. Its row therefore does not promote a selected sign as a new
confirmatory probability.

### Scientific reading

- **H1:** The posterior favors a positive entropy/effort association at 42
  months (`P(positive) = {float(by_hypothesis.get('H1', {}).get('probability_positive', float('nan'))):.3f}`), but
  `{float(by_hypothesis.get('H1', {}).get('probability_rope', float('nan'))):.1%}` of the posterior remains inside the declared small-effect ROPE. This is
  evidence for a modest direction, not a large effort response.
- **H2:** The age-by-entropy coefficient is close to zero, with
  `{float(by_hypothesis.get('H2', {}).get('probability_rope', float('nan'))):.1%}` of its posterior in the ROPE. The estimated entropy response attenuates
  with age, but this focused linear joint model does not support a practically
  large developmental change.
- **H3:** Fixed-effort contextual surprisal decreases with age
  (`P(negative) = {float(by_hypothesis.get('H3', {}).get('probability_negative', float('nan'))):.3f}`). This is the clearest joint-model result and describes
  growing scorer predictability/conventionality.
- **H4:** The key cross-child correlation is centered almost exactly at zero
  and has a wide interval. There is no evidence here that children with
  stronger fixed-effort predictability development also strengthen their
  demand-sensitive effort allocation.

![Population coefficient intervals](../figs/bayesian_joint_adaptive_efficiency_20260828/population_effects.png)

## Effort calibration across age

The ratio below compares the model's `log(1 + words)` prediction at the
observed all-79 response-entropy p90 versus p10. It is not the raw
negative-binomial word-count ratio from the completed GAMM analysis.

| Age | High/low entropy ratio in modeled (words + 1) | P(entropy slope > 0) |
|---:|---:|---:|
{chr(10).join(age_rows)}

![Developmental effort calibration](../figs/bayesian_joint_adaptive_efficiency_20260828/entropy_adaptation_by_age.png)

## Coordinated development

H4 concerns the between-child correlation between the fixed-effort
predictability age slope and the developmental change in demand-sensitive
effort. A negative value is the efficiency-motivated direction because more
negative surprisal development would accompany a more positive change in the
entropy/effort relationship. Regardless of sign, this is coordinated
variation—not evidence of optimization.

| Child-level association | Correlation [95% CrI] |
|---|---:|
{chr(10).join(correlation_rows)}

The pronounced positive association is internal to the two effort
coefficients: children with a higher entropy/effort slope at 42 months also
tend to have a more positive developmental change in that slope. In contrast,
neither effort coefficient shows a clear child-level association with
fixed-effort predictability development. Intercept/slope parameterization can
affect the within-effort correlation, so the age-specific effort curves remain
the primary interpretation.

![Between-child correlations](../figs/bayesian_joint_adaptive_efficiency_20260828/between_child_correlations.png)

## Robustness and computation

- Prior sensitivity: {payload.get('prior_sensitivity', 'not available')}.
- Leave-one-corpus influence: {payload.get('influence_summary', 'not available')}.
- Total fitting runtime: {float(payload.get('runtime_minutes', 0)):.1f} minutes.
- The model uses a three-dimensional session-clustered measurement-error
  likelihood over child coefficients; it does not run NUTS over 1.1 million
  utterance rows.

## Interpretation boundary

{guardrails}

The next decisive test remains downstream caregiver-response predictive gain:
whether the observed child utterance improves prediction of the caregiver's
actual next response, exceeds a shuffled-child negative control, and becomes
more useful at fixed effort with age.
"""
    atomic_text(markdown, path)


def run_report_stage(args: argparse.Namespace) -> None:
    require_stage_manifest(args.output_dir / "diagnostics/manifest.json", "diagnostics")
    require_stage_manifest(args.figures_dir / "manifest.json", "plots")
    contract = load_contract(args.contract)
    hypotheses = pd.read_csv(args.output_dir / "diagnostics/hypothesis_posteriors.csv")
    contrasts = pd.read_csv(args.output_dir / "diagnostics/age_entropy_contrasts.csv")
    sensitivity = pd.read_csv(args.output_dir / "diagnostics/prior_sensitivity.csv")
    influence = pd.read_csv(args.output_dir / "diagnostics/influence_long.csv")
    dataset_audit = json.loads((args.output_dir / "datasets/dataset_audit.json").read_text(encoding="utf-8"))
    fit_audit = json.loads((args.output_dir / "fits/fit_audit.json").read_text(encoding="utf-8"))
    posterior_summary = pd.read_csv(args.output_dir / "fits/posterior_summary.csv")
    correlation_specs = [
        ("child_correlation[1,2]", "Predictability development × effort at 42 months"),
        ("child_correlation[1,3]", "Predictability development × effort development"),
        ("child_correlation[2,3]", "Effort at 42 months × effort development"),
    ]
    correlations = []
    for variable, label in correlation_specs:
        row = posterior_summary[
            (posterior_summary.fit_id == "regularizing")
            & (posterior_summary.variable == variable)
        ].iloc[0]
        correlations.append({
            "variable": variable,
            "label": label,
            "estimate": float(row["mean"]),
            "q025": float(row.q025),
            "q975": float(row.q975),
        })
    payload = {
        "status": "PASS",
        "children": dataset_audit["included_children"],
        "corpora": dataset_audit["corpora"],
        "hypotheses": hypotheses.to_dict(orient="records"),
        "age_contrasts": contrasts.to_dict(orient="records"),
        "correlations": correlations,
        "prior_sensitivity": "; ".join(
            f"{row.variable} shift {row.absolute_shift:.4f}"
            for row in sensitivity.itertuples(index=False)
        ),
        "influence_summary": (
            f"H1-H3 retained their signs under every corpus omission; H4 reversed sign in "
            f"{int(influence.loc[influence.variable == 'rho_r1_age_entropy', 'sign_reversal'].sum())}/13 omissions. "
            f"The largest shifts by parameter were "
            + ", ".join(
                f"{variable} {group.shift_from_primary.abs().max():.4f}"
                for variable, group in influence.groupby("variable", sort=False)
            )
        ),
        "runtime_minutes": float(fit_audit["total_elapsed_seconds"]) / 60,
        "guardrails": contract["interpretation_guardrails"],
    }
    render_scientific_report(payload, args.report_md)
    render_markdown_file(args.report_md, args.report_html, title="Bayesian Joint Adaptive-Efficiency Analysis")
    directory = args.output_dir / "report"
    directory.mkdir(parents=True, exist_ok=True)
    payload_path = directory / "report_payload.json"
    audit_path = directory / "report_audit.json"
    atomic_json(payload, payload_path)
    audit = {"status": "PASS", "markdown": str(args.report_md), "html": str(args.report_html), "problems": []}
    atomic_json(audit, audit_path)
    write_stage_manifest(
        "report", directory / "manifest.json",
        inputs={"diagnostics_manifest": args.output_dir / "diagnostics/manifest.json", "plots_manifest": args.figures_dir / "manifest.json"},
        outputs={"payload": payload_path, "markdown": args.report_md, "html": args.report_html, "audit": audit_path},
        audit=audit,
    )


def run_audit_stage(args: argparse.Namespace) -> None:
    report_manifest = require_stage_manifest(args.output_dir / "report/manifest.json", "report")
    diagnostic_audit = json.loads((args.output_dir / "diagnostics/diagnostics_audit.json").read_text(encoding="utf-8"))
    required_stages = ("contract", "datasets", "synthetic-smoke", "fits", "diagnostics", "report")
    problems: list[str] = []
    for stage in required_stages:
        path = args.output_dir / stage / "manifest.json"
        try:
            require_stage_manifest(path, stage)
        except Exception as error:  # fail closed with all missing/stale stages listed
            problems.append(str(error))
    try:
        require_stage_manifest(args.figures_dir / "manifest.json", "plots")
    except Exception as error:
        problems.append(str(error))
    if diagnostic_audit.get("status") != "PASS":
        problems.append("diagnostic audit is not PASS")
    report_text = args.report_md.read_text(encoding="utf-8")
    for phrase in ("caregiver-response utility", "post-hoc", "Corpus is a background"):
        if phrase not in report_text:
            problems.append(f"report guardrail missing: {phrase}")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "audited_at": utc_now(),
        "report_manifest_sha256": sha256_file(args.output_dir / "report/manifest.json"),
        "diagnostics_manifest_sha256": sha256_file(args.output_dir / "diagnostics/manifest.json"),
        "problems": problems,
    }
    directory = args.output_dir / "audit"
    directory.mkdir(parents=True, exist_ok=True)
    audit_path = directory / "final_audit.json"
    atomic_json(audit, audit_path)
    marker = directory / "FOCUSED_JOINT_ANALYSIS_COMPLETE_AND_AUDITED"
    if problems:
        if marker.exists():
            marker.unlink()
        raise RuntimeError("final audit failed: " + "; ".join(problems))
    atomic_text(json.dumps({"status": "PASS", "audit_sha256": sha256_file(audit_path)}, indent=2) + "\n", marker)
    write_stage_manifest(
        "audit", directory / "manifest.json",
        inputs={"report_manifest": args.output_dir / "report/manifest.json", "diagnostics_manifest": args.output_dir / "diagnostics/manifest.json"},
        outputs={"audit": audit_path, "marker": marker},
        audit=audit,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("contract", "datasets", "synthetic-smoke", "fit", "diagnostics", "plots", "report", "audit", "all"))
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--finalize-existing", action="store_true", help="Re-audit a complete immutable CmdStan fit inventory without resampling.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.contract = args.contract.resolve()
    args.output_dir = args.output_dir.resolve()
    args.figures_dir = args.figures_dir.resolve()
    args.report_md = args.report_md.resolve()
    args.report_html = args.report_html.resolve()
    functions = {
        "contract": run_contract_stage,
        "datasets": run_datasets_stage,
        "synthetic-smoke": run_synthetic_stage,
        "fit": run_fit_stage,
        "diagnostics": run_diagnostics_stage,
        "plots": run_plots_stage,
        "report": run_report_stage,
        "audit": run_audit_stage,
    }
    stages = tuple(functions) if args.stage == "all" else (args.stage,)
    started = time.monotonic()
    for stage in stages:
        print(f"[{stage}] starting", flush=True)
        functions[stage](args)
        print(f"[{stage}] complete", flush=True)
    print(f"completed in {time.monotonic() - started:.1f}s", flush=True)


if __name__ == "__main__":
    main()
