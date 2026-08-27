#!/usr/bin/env python3
"""Assemble reused baselines and fit the PBM caregiver-response utility models."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.build_downstream_caregiver_response_analysis import (
    _atomic_csv_gz,
    bootstrap_age_slope,
    fit_primary_cell_model,
    make_model_cells,
    sha256_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF = PROJECT_ROOT / "results/downstream_caregiver_response_handoff/full_20260827"
DEFAULT_SCORE_ROOT = PROJECT_ROOT / "results/downstream_caregiver_response_local/tinydialogues/scores"
DEFAULT_BASELINE = PROJECT_ROOT / "results/direct_surprisal_replication/tinydialogues_pbm/caretaker_direct_surprisal_wide.csv.gz"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/downstream_caregiver_response_analysis/pbm_tinydialogues"
PBM_DATASETS = ("Brown", "Manchester", "Providence")
NEW_CONDITIONS = ("matched_child", "shuffled_child", "child_only")
OUTCOMES = ("downstream_gain_bits", "matched_over_shuffled_bits", "child_only_gain_bits")
EXPECTED_PRIMARY_ROWS = 174_860


def _target_hash(value: object) -> str:
    normalized = " ".join(str(value).split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _load_primary_handoff(handoff_root: Path) -> pd.DataFrame:
    audit = json.loads((handoff_root / "audit.json").read_text(encoding="utf-8"))
    if audit.get("status") != "PASS" or not (handoff_root / "BUILD_COMPLETE_AND_AUDITED").is_file():
        raise ValueError("full caregiver-response handoff is not audited")
    frames = []
    for dataset in PBM_DATASETS:
        path = handoff_root / f"inputs/{dataset}.caregiver_response.csv.gz"
        frame = pd.read_csv(path, keep_default_na=False)
        primary = pd.to_numeric(frame["primary_eligible"], errors="coerce").fillna(0).astype(int).eq(1)
        frames.append(frame.loc[primary].copy())
    source = pd.concat(frames, ignore_index=True)
    if len(source) != EXPECTED_PRIMARY_ROWS or source["response_pair_id"].duplicated().any():
        raise ValueError("PBM primary response-pair identity changed")
    return source


def _join_reused_baseline(source: pd.DataFrame, baseline_wide: Path) -> pd.DataFrame:
    columns = [
        "dataset", "child_id", "file", "line_no", "target_text_sha256",
        "context_k3_sha256", "k0_sum_bits", "k3_sum_bits",
    ]
    baseline = pd.read_csv(baseline_wide, usecols=columns, keep_default_na=False)
    baseline = baseline.loc[baseline["dataset"].isin(PBM_DATASETS)].rename(
        columns={
            "line_no": "next_caregiver_line_no",
            "target_text_sha256": "baseline_target_sha256",
            "context_k3_sha256": "baseline_context_sha256",
            "k0_sum_bits": "unconditional_bits",
            "k3_sum_bits": "base_context_bits",
        }
    )
    keys = ["dataset", "child_id", "file", "next_caregiver_line_no"]
    if baseline.duplicated(keys).any():
        raise ValueError("reused caregiver baseline has duplicate response keys")
    joined = source.merge(baseline, on=keys, how="left", validate="one_to_one", indicator=True)
    exact_target = joined["target_text_sha256"].eq(joined["baseline_target_sha256"])
    exact_context = joined["context_base_sha256"].eq(joined["baseline_context_sha256"])
    finite = np.isfinite(
        joined[["unconditional_bits", "base_context_bits"]].apply(pd.to_numeric, errors="coerce")
    ).all(axis=1)
    if not joined["_merge"].eq("both").all() or not exact_target.all() or not exact_context.all() or not finite.all():
        raise ValueError("reused k0/k3 caregiver scores are not an exact PBM baseline match")
    return joined.drop(columns=["_merge", "baseline_target_sha256", "baseline_context_sha256"])


def _read_new_condition_scores(score_root: Path, condition: str) -> pd.DataFrame:
    frames = []
    for dataset in PBM_DATASETS:
        root = score_root / dataset / condition / "caregiver_response_surprisal"
        if not (root / "CONTRACT_COMPLETE").is_file():
            raise ValueError(f"incomplete score contract: {root}")
        frame = pd.read_csv(root / "utterances.csv.gz", keep_default_na=False)
        frame = frame[["utterance_id", "target_text", "score_status", "context_available", "utterance_sum_bits"]].copy()
        frame["dataset"] = dataset
        frames.append(frame)
    scored = pd.concat(frames, ignore_index=True)
    if scored["utterance_id"].duplicated().any():
        raise ValueError(f"duplicate response IDs in {condition} scores")
    scored[f"{condition}_target_sha256"] = scored["target_text"].map(_target_hash)
    return scored.rename(
        columns={
            "utterance_id": "response_pair_id",
            "score_status": f"{condition}_status",
            "context_available": f"{condition}_context_available",
            "utterance_sum_bits": f"{condition}_bits",
        }
    ).drop(columns="target_text")


def assemble_pbm_dataset(
    *,
    handoff_root: Path,
    baseline_wide: Path,
    score_root: Path,
    scorer_key: str,
    selected_ids: set[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    source = _load_primary_handoff(handoff_root)
    if selected_ids is not None:
        source = source.loc[source["response_pair_id"].isin(selected_ids)].copy()
        if set(source["response_pair_id"]) != selected_ids:
            raise ValueError("selected response IDs are not all in PBM primary")
    source = _join_reused_baseline(source, baseline_wide)
    expected_ids = set(source["response_pair_id"])
    condition_counts: dict[str, dict[str, int]] = {}
    for condition in NEW_CONDITIONS:
        scored = _read_new_condition_scores(score_root, condition)
        if set(scored["response_pair_id"]) != expected_ids:
            raise ValueError(f"{condition} scored response identity does not equal PBM primary")
        source = source.merge(scored, on=["response_pair_id", "dataset"], how="left", validate="one_to_one")
        if not source[f"{condition}_target_sha256"].eq(source["target_text_sha256"]).all():
            raise ValueError(f"{condition} target identity changed")
        source[f"{condition}_bits"] = pd.to_numeric(source[f"{condition}_bits"], errors="coerce")
        condition_counts[condition] = source[f"{condition}_status"].value_counts().to_dict()

    if not source["matched_child_status"].eq("scored").all() or not source["child_only_status"].eq("scored").all():
        raise ValueError("matched-child and child-only scores must cover every primary row")
    source["unconditional_bits"] = pd.to_numeric(source["unconditional_bits"], errors="raise")
    source["base_context_bits"] = pd.to_numeric(source["base_context_bits"], errors="raise")
    source["downstream_gain_bits"] = source["base_context_bits"] - source["matched_child_bits"]
    source["matched_over_shuffled_bits"] = source["shuffled_child_bits"] - source["matched_child_bits"]
    source["child_only_gain_bits"] = source["unconditional_bits"] - source["child_only_bits"]
    source.insert(0, "scorer_key", scorer_key)
    audit = {
        "status": "PASS",
        "scorer_key": scorer_key,
        "rows": len(source),
        "children": int(source["child_key"].nunique()),
        "datasets": sorted(source["dataset"].unique()),
        "baseline_exact_rows": len(source),
        "downstream_gain_rows": int(source["downstream_gain_bits"].notna().sum()),
        "matched_over_shuffled_rows": int(source["matched_over_shuffled_bits"].notna().sum()),
        "child_only_gain_rows": int(source["child_only_gain_bits"].notna().sum()),
        "condition_status_counts": condition_counts,
    }
    return source, audit


def fit_pbm_models(frame: pd.DataFrame, *, bootstrap_reps: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    registry_rows = []
    coefficients = []
    bootstraps = []
    scorer_key = str(frame["scorer_key"].iloc[0])
    for index, outcome in enumerate(OUTCOMES):
        cells = make_model_cells(frame, outcome)
        summary, coefficient = fit_primary_cell_model(cells)
        model_id = f"{scorer_key}__pbm_discovery__{outcome}"
        draws = bootstrap_age_slope(cells, reps=bootstrap_reps, seed=20260827 + index)
        passed = draws.loc[draws["status"].eq("PASS"), "age_estimate"]
        summary.update(
            {
                "bootstrap_reps": bootstrap_reps,
                "bootstrap_passed": len(passed),
                "bootstrap_ci_low": float(passed.quantile(0.025)) if len(passed) else np.nan,
                "bootstrap_ci_high": float(passed.quantile(0.975)) if len(passed) else np.nan,
            }
        )
        registry_rows.append({"model_id": model_id, "scorer_key": scorer_key, "scope": "pbm_discovery", "outcome": outcome, **summary})
        coefficient.insert(0, "model_id", model_id)
        draws.insert(0, "model_id", model_id)
        coefficients.append(coefficient)
        bootstraps.append(draws)
    return pd.DataFrame(registry_rows), pd.concat(coefficients, ignore_index=True), pd.concat(bootstraps, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff-root", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--score-root", type=Path, default=DEFAULT_SCORE_ROOT)
    parser.add_argument("--baseline-wide", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--scorer-key", default="tinydialogues")
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    args = parser.parse_args()
    if args.bootstrap_reps < 0:
        raise ValueError("bootstrap repetitions cannot be negative")

    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    frame, dataset_audit = assemble_pbm_dataset(
        handoff_root=args.handoff_root.expanduser().resolve(),
        baseline_wide=args.baseline_wide.expanduser().resolve(),
        score_root=args.score_root.expanduser().resolve(),
        scorer_key=args.scorer_key,
    )
    dataset_path = output / "pbm_response_utility.csv.gz"
    _atomic_csv_gz(frame, dataset_path)
    dataset_audit.update({"output": str(dataset_path), "output_sha256": sha256_file(dataset_path)})
    (output / "dataset_audit.json").write_text(json.dumps(dataset_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    registry, coefficients, bootstraps = fit_pbm_models(frame, bootstrap_reps=args.bootstrap_reps)
    registry.to_csv(output / "model_registry.csv", index=False)
    coefficients.to_csv(output / "coefficients.csv", index=False)
    _atomic_csv_gz(bootstraps, output / "child_bootstrap_draws.csv.gz")
    failures = int(bootstraps["status"].ne("PASS").sum())
    final = {
        "status": "PASS" if failures == 0 else "FAIL",
        "scorer_key": args.scorer_key,
        "rows": len(frame),
        "models": len(registry),
        "bootstrap_failures": failures,
        "age_effects": registry[["outcome", "age_estimate", "age_ci_low", "age_ci_high", "bootstrap_ci_low", "bootstrap_ci_high"]].to_dict("records"),
    }
    if failures:
        raise ValueError(f"PBM bootstrap failures: {failures}")
    final_path = output / "final_audit.json"
    final_path.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "PBM_CAREGIVER_RESPONSE_ANALYSIS_COMPLETE").write_text(f"{sha256_file(final_path)}\n", encoding="utf-8")
    print(json.dumps(final, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
