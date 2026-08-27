#!/usr/bin/env python3
"""Run resumable TinyDialogues PBM caregiver-response scoring on local CPU."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPUTE_ROOT = PROJECT_ROOT.parent / "compute_surprisal_mila"
DEFAULT_RUN_ROOT = PROJECT_ROOT / "results/downstream_caregiver_response_local/tinydialogues/run"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "results/downstream_caregiver_response_local/tinydialogues/scores"
DEFAULT_STAGE_DIR = PROJECT_ROOT / "results/downstream_caregiver_response_local/models/tinydialogues"
EXPECTED_TRANSFORMERS_VERSION = "4.57.5"


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _code_identity(compute_root: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/crossmodel_word_surprisal.py",
        "src/new_score_utterances_fast.py",
        "src/run_crossmodel_word_surprisal.py",
        "src/tinydialogues_model.py",
    ):
        path = compute_root / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return f"local-sha256-{digest.hexdigest()}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("smoke", "production"), required=True)
    parser.add_argument("--compute-root", type=Path, default=DEFAULT_COMPUTE_ROOT)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--stage-dir", type=Path, default=DEFAULT_STAGE_DIR)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--cpu-threads", type=int, default=8)
    args = parser.parse_args()
    if args.batch_size < 1 or args.cpu_threads < 1:
        raise ValueError("batch size and CPU thread count must be positive")

    compute_root = args.compute_root.expanduser().resolve()
    run_root = args.run_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    stage_dir = args.stage_dir.expanduser().resolve()
    if not (run_root / "PBM_LOCAL_PREPARATION_PASSED").is_file():
        raise ValueError("PBM local preparation marker is missing")
    if args.scope == "production" and not (run_root / "smoke/LOCAL_CPU_SMOKE_PASSED").is_file():
        raise ValueError("production is blocked until the real-model CPU smoke passes")

    sys.path.insert(0, str(compute_root / "src"))
    import torch
    from run_crossmodel_word_surprisal import run_contracts

    transformers_version = importlib.metadata.version("transformers")
    if transformers_version != EXPECTED_TRANSFORMERS_VERSION:
        raise ValueError(
            f"use compute_surprisal_mila/.venv; expected Transformers "
            f"{EXPECTED_TRANSFORMERS_VERSION}, found {transformers_version}"
        )
    torch.set_num_threads(args.cpu_threads)
    torch.set_num_interop_threads(1)
    selection_name = "pbm_smoke_selection.json" if args.scope == "smoke" else "pbm_production_selection.json"
    selection_path = run_root / "manifests" / selection_name
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    contract_ids = {int(value) for value in selection["contract_ids"]}
    selected_output = run_root / "smoke/scored" if args.scope == "smoke" else output_root
    summary_path = run_root / f"reports/{args.scope}/local_cpu_summary.json"
    started = time.perf_counter()
    summaries = run_contracts(
        contract_manifest=run_root / "manifests/word_output_contracts.tsv",
        output_root=selected_output,
        model_key="tinydialogues",
        staged_model_path=stage_dir,
        scoring_code_revision=_code_identity(compute_root),
        contract_ids=contract_ids,
        row_selection_json=selection_path,
        batch_size=args.batch_size,
        max_length=256,
        device_name="cpu",
        dtype_name="fp32",
        transformers_version=transformers_version,
        torch_version=importlib.metadata.version("torch"),
        runtime_format="local_cpu_uv_environment",
        word_level=False,
    )
    payload = {
        "status": "PASS",
        "scope": args.scope,
        "contracts": len(summaries),
        "passed": sum(row["score_status"] == "PASS" for row in summaries),
        "skipped": sum(row["score_status"] == "SKIP" for row in summaries),
        "selected_source_rows": int(selection["rows"]),
        "target_condition_rows": int(selection["rows"]) * len(contract_ids) // 3,
        "elapsed_seconds": time.perf_counter() - started,
        "batch_size": args.batch_size,
        "cpu_threads": args.cpu_threads,
        "output_root": str(selected_output),
        "summaries": summaries,
    }
    if len(summaries) != int(selection["expected_contracts"]):
        raise ValueError(f"scorer returned an incomplete contract set: {len(summaries)}")
    _atomic_json(summary_path, payload)
    marker = run_root / ("smoke/LOCAL_CPU_SMOKE_PASSED" if args.scope == "smoke" else "PBM_LOCAL_SCORING_COMPLETE")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("PASS\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "summaries"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
