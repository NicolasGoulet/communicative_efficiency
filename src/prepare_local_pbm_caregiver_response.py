#!/usr/bin/env python3
"""Prepare resumable local PBM caregiver-response scoring selections."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPUTE_ROOT = PROJECT_ROOT.parent / "compute_surprisal_mila"
DEFAULT_HANDOFF = PROJECT_ROOT / "results/downstream_caregiver_response_handoff/full_20260827"
DEFAULT_RUN_ROOT = PROJECT_ROOT / "results/downstream_caregiver_response_local/tinydialogues/run"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "results/downstream_caregiver_response_local/tinydialogues/scores"
PBM_DATASETS = ("Brown", "Manchester", "Providence")
NEW_CONDITIONS = ("matched_child", "shuffled_child", "child_only")
EXPECTED_PRIMARY_ROWS = 174_860


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _read_contracts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def build_pbm_selections(
    *,
    contract_manifest: Path,
    run_root: Path,
    smoke_rows_per_dataset: int,
) -> dict[str, object]:
    if smoke_rows_per_dataset < 1:
        raise ValueError("smoke row count must be positive")
    contracts = _read_contracts(contract_manifest)
    selected = [
        row
        for row in contracts
        if row["child_key"] in PBM_DATASETS and row["context_window"] in NEW_CONDITIONS
    ]
    if len(selected) != len(PBM_DATASETS) * len(NEW_CONDITIONS):
        raise ValueError(f"expected 9 PBM scoring contracts, found {len(selected)}")

    contract_ids = sorted(int(row["contract_id"]) for row in selected)
    rows_by_source: dict[str, list[int]] = {}
    smoke_rows_by_source: dict[str, list[int]] = {}
    counts: dict[str, int] = {}
    for dataset in PBM_DATASETS:
        dataset_rows = [row for row in selected if row["child_key"] == dataset]
        source_values = {str(Path(row["input_csv"]).resolve()) for row in dataset_rows}
        if len(source_values) != 1:
            raise ValueError(f"PBM contracts do not share one source for {dataset}")
        source = Path(source_values.pop())
        frame = pd.read_csv(source, keep_default_na=False)
        primary = pd.to_numeric(frame["primary_eligible"], errors="coerce").fillna(0).astype(int).eq(1)
        indices = [int(value) for value in frame.index[primary]]
        rows_by_source[str(source)] = indices
        counts[dataset] = len(indices)

        eligible = frame.loc[primary].copy()
        context_columns = ["context_matched_child", "context_shuffled_child", "context_child_only"]
        complete = eligible[context_columns].astype(str).apply(
            lambda column: column.str.split().str.len().gt(0)
        ).all(axis=1)
        eligible = eligible.loc[complete]
        if eligible.empty:
            raise ValueError(f"no complete smoke rows for {dataset}")
        length = eligible[context_columns + ["target_text"]].astype(str).map(len).max(axis=1)
        smoke_rows_by_source[str(source)] = [
            int(value) for value in length.sort_values(ascending=False, kind="stable").index[:smoke_rows_per_dataset]
        ]

    if sum(counts.values()) != EXPECTED_PRIMARY_ROWS:
        raise ValueError(f"PBM primary row count changed: {counts}")

    common = {
        "schema_version": 1,
        "scope": "pbm_downstream_caregiver_response_primary_v1",
        "datasets": list(PBM_DATASETS),
        "conditions": list(NEW_CONDITIONS),
        "contract_ids": contract_ids,
        "expected_contracts": len(contract_ids),
    }
    production = {**common, "rows": sum(counts.values()), "rows_by_dataset": counts, "rows_by_source": rows_by_source}
    smoke = {
        **common,
        "rows": sum(len(values) for values in smoke_rows_by_source.values()),
        "rows_per_dataset": smoke_rows_per_dataset,
        "rows_by_source": smoke_rows_by_source,
    }
    _atomic_json(run_root / "manifests/pbm_production_selection.json", production)
    _atomic_json(run_root / "manifests/pbm_smoke_selection.json", smoke)
    return {
        "status": "PASS",
        "model": selected[0]["model_key"],
        "datasets": list(PBM_DATASETS),
        "primary_rows": sum(counts.values()),
        "new_conditions": list(NEW_CONDITIONS),
        "contracts": len(contract_ids),
        "new_target_condition_rows": sum(counts.values()) * len(NEW_CONDITIONS),
        "smoke_rows": smoke["rows"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compute-root", type=Path, default=DEFAULT_COMPUTE_ROOT)
    parser.add_argument("--handoff-root", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--model", default="tinydialogues")
    parser.add_argument("--smoke-rows-per-dataset", type=int, default=3)
    args = parser.parse_args()

    compute_root = args.compute_root.expanduser().resolve()
    sys.path.insert(0, str(compute_root / "src"))
    from prepare_downstream_caregiver_response_surprisal import prepare_downstream_contracts

    run_root = args.run_root.expanduser().resolve()
    marker = run_root / "PREPARATION_PASSED"
    if not marker.is_file():
        if run_root.exists() and any(run_root.iterdir()):
            raise ValueError(f"partial run root must be inspected before reuse: {run_root}")
        prepare_downstream_contracts(
            package_root=args.handoff_root.expanduser().resolve(),
            run_root=run_root,
            output_root=args.output_root.expanduser().resolve(),
            model_key=args.model,
            conditions=NEW_CONDITIONS,
            smoke_rows_per_source=args.smoke_rows_per_dataset,
        )

    summary = build_pbm_selections(
        contract_manifest=run_root / "manifests/word_output_contracts.tsv",
        run_root=run_root,
        smoke_rows_per_dataset=args.smoke_rows_per_dataset,
    )
    _atomic_json(run_root / "reports/preparation/pbm_local_plan.json", summary)
    (run_root / "PBM_LOCAL_PREPARATION_PASSED").write_text("PASS\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
