#!/usr/bin/env python3
"""Build an immutable, audited Hall real-target handoff for Mila scoring."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ID = "hall_snapshot_mistral_real_k0_k3_v1"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "results/hall_snapshot_preprocessing"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results/scoring_bundles" / PACKAGE_ID

DEFAULT_SOURCES = {
    "scoring": DEFAULT_REPORT_ROOT / "hall_child_snapshot_scoring.csv",
    "metadata": DEFAULT_REPORT_ROOT / "hall_child_metadata.csv",
    "inventory": DEFAULT_REPORT_ROOT / "hall_file_inventory.csv",
    "preprocessing_audit": DEFAULT_REPORT_ROOT / "hall_preprocessing_audit.json",
    "comparator": DEFAULT_REPORT_ROOT / "hall_comparison_snapshot_manifest.csv",
    "comparator_audit": DEFAULT_REPORT_ROOT / "hall_comparison_snapshot_audit.json",
    "protocol": PROJECT_ROOT / "docs/hall_snapshot_preprocessing_and_analysis_plan.md",
    "preprocessor_source": PROJECT_ROOT / "src/prepare_hall_snapshot.py",
    "comparator_source": PROJECT_ROOT / "src/build_hall_snapshot_comparator.py",
    "handoff_builder_source": Path(__file__).resolve(),
}

DESTINATIONS = {
    "scoring": "inputs/hall_child_snapshot_scoring.csv",
    "metadata": "metadata/hall_child_metadata.csv",
    "inventory": "metadata/hall_file_inventory.csv",
    "preprocessing_audit": "audits/hall_preprocessing_audit.json",
    "comparator": "comparators/hall_comparison_snapshot_manifest.csv",
    "comparator_audit": "comparators/hall_comparison_snapshot_audit.json",
    "protocol": "support/hall_snapshot_preprocessing_and_analysis_plan.md",
    "preprocessor_source": "support/prepare_hall_snapshot.py",
    "comparator_source": "support/build_hall_snapshot_comparator.py",
    "handoff_builder_source": "support/build_hall_mila_handoff.py",
}

REAL_V1_EXPECTED_COUNTS = {
    "source_files": 40,
    "main_tier_rows": 238_249,
    "scoring_rows": 71_830,
    "primary_rows": 70_510,
    "children": 37,
    "primary_children": 36,
    "sensitivity_children": 37,
    "child_after_adult_rows": 33_030,
    "rows_with_context": 70_018,
    "comparator_children": 20,
}

REQUIRED_SCORING_COLUMNS = {
    "dataset", "child_id", "source_group", "race", "social_class", "stratum",
    "demographic_source", "primary_eligible", "sensitivity_eligible",
    "age_months", "file", "line_no", "utterance_id", "situation_id",
    "setting_auto", "previous_main_role_group", "child_after_adult",
    "context_k1", "context_k2", "context_k3", "chi_utterance_clean",
    "nb_words", "nb_characters",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def audit_scoring_input(path: Path) -> dict[str, object]:
    children: set[str] = set()
    primary_children: set[str] = set()
    sensitivity_children: set[str] = set()
    utterance_ids: set[str] = set()
    rows = 0
    primary_rows = 0
    sensitivity_rows = 0
    child_after_adult_rows = 0
    rows_with_context = 0
    blank_targets = 0
    duplicate_utterance_ids = 0
    invalid_context_nesting = 0
    invalid_datasets = 0

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_SCORING_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Hall scoring input is missing columns: {sorted(missing)}")
        for row in reader:
            rows += 1
            child = row["child_id"].strip()
            children.add(child)
            primary = row["primary_eligible"].strip() == "1"
            sensitivity = row["sensitivity_eligible"].strip() == "1"
            if primary:
                primary_rows += 1
                primary_children.add(child)
            if sensitivity:
                sensitivity_rows += 1
                sensitivity_children.add(child)
            if row["child_after_adult"].strip() == "1":
                child_after_adult_rows += 1
            contexts = [row[f"context_k{k}"].strip() for k in (1, 2, 3)]
            if contexts[0]:
                rows_with_context += 1
            if bool(contexts[1]) != bool(contexts[0]) or bool(contexts[2]) != bool(contexts[0]):
                invalid_context_nesting += 1
            if not row["chi_utterance_clean"].strip():
                blank_targets += 1
            utterance_id = row["utterance_id"].strip()
            if utterance_id in utterance_ids:
                duplicate_utterance_ids += 1
            utterance_ids.add(utterance_id)
            if row["dataset"].strip() != "Hall":
                invalid_datasets += 1

    return {
        "rows": rows,
        "primary_rows": primary_rows,
        "sensitivity_rows": sensitivity_rows,
        "children": len(children),
        "primary_children": len(primary_children),
        "sensitivity_children": len(sensitivity_children),
        "child_after_adult_rows": child_after_adult_rows,
        "rows_with_context": rows_with_context,
        "rows_without_context": rows - rows_with_context,
        "blank_targets": blank_targets,
        "duplicate_utterance_ids": duplicate_utterance_ids,
        "invalid_context_nesting": invalid_context_nesting,
        "invalid_datasets": invalid_datasets,
    }


def write_contracts(path: Path, *, rows: int, rows_with_context: int) -> None:
    columns = [
        "contract_id", "context_id", "target_column", "context_column",
        "expected_input_rows", "expected_nonempty_target_rows",
        "expected_nonempty_context_rows", "model_family", "scoring_dtype",
    ]
    contracts = []
    for context_id in ("k0", "k1", "k2", "k3"):
        contracts.append(
            {
                "contract_id": f"hall_real_child_{context_id}",
                "context_id": context_id,
                "target_column": "chi_utterance_clean",
                "context_column": "" if context_id == "k0" else f"context_{context_id}",
                "expected_input_rows": rows,
                "expected_nonempty_target_rows": rows,
                "expected_nonempty_context_rows": 0 if context_id == "k0" else rows_with_context,
                "model_family": "mistralai/Mistral-7B-v0.3",
                "scoring_dtype": "fp16_match_full79_production",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        writer.writerows(contracts)


def write_deterministic_archive(source_root: Path, archive_path: Path, package_id: str) -> str:
    temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
    with temporary.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
            with tarfile.open(fileobj=gzip_handle, mode="w") as archive:
                for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
                    relative = path.relative_to(source_root).as_posix()
                    info = archive.gettarinfo(str(path), arcname=f"{package_id}/{relative}")
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    info.mode = 0o644
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
    os.replace(temporary, archive_path)
    return sha256_file(archive_path)


def build_hall_mila_handoff(
    *,
    sources: Mapping[str, Path] = DEFAULT_SOURCES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    expected_counts: Mapping[str, int] = REAL_V1_EXPECTED_COUNTS,
    package_id: str = PACKAGE_ID,
) -> dict[str, object]:
    """Build a deterministic archive only after every frozen input gate passes."""

    resolved_sources = {name: Path(path).expanduser().resolve() for name, path in sources.items()}
    missing_sources = [name for name, path in resolved_sources.items() if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError(f"Missing Hall handoff sources: {missing_sources}")
    for required in (
        "scoring", "metadata", "inventory", "preprocessing_audit",
        "comparator", "comparator_audit",
    ):
        if required not in resolved_sources:
            raise ValueError(f"Required Hall source was not provided: {required}")

    preprocessing_audit = json.loads(resolved_sources["preprocessing_audit"].read_text(encoding="utf-8"))
    comparator_audit = json.loads(resolved_sources["comparator_audit"].read_text(encoding="utf-8"))
    input_audit = audit_scoring_input(resolved_sources["scoring"])
    observed = {
        "source_files": int(preprocessing_audit.get("counts", {}).get("files", -1)),
        "main_tier_rows": int(preprocessing_audit.get("counts", {}).get("main_tier_rows", -1)),
        "scoring_rows": int(input_audit["rows"]),
        "primary_rows": int(input_audit["primary_rows"]),
        "children": int(input_audit["children"]),
        "primary_children": int(input_audit["primary_children"]),
        "sensitivity_children": int(input_audit["sensitivity_children"]),
        "child_after_adult_rows": int(input_audit["child_after_adult_rows"]),
        "rows_with_context": int(input_audit["rows_with_context"]),
        "comparator_children": count_csv_rows(resolved_sources["comparator"]),
    }
    problems: list[str] = []
    if preprocessing_audit.get("status") != "PASS":
        problems.append("preprocessing_audit_not_pass")
    if comparator_audit.get("status") != "PASS":
        problems.append("comparator_audit_not_pass")
    for key, expected in expected_counts.items():
        if observed.get(key) != expected:
            problems.append(f"count_mismatch:{key}:expected={expected}:observed={observed.get(key)}")
    for key in (
        "blank_targets", "duplicate_utterance_ids", "invalid_context_nesting", "invalid_datasets",
    ):
        if input_audit[key] != 0:
            problems.append(f"input_audit:{key}={input_audit[key]}")
    if input_audit["sensitivity_rows"] != input_audit["rows"]:
        problems.append("not_all_scoring_rows_are_sensitivity_eligible")
    if problems:
        raise ValueError("Hall Mila handoff gates failed: " + "; ".join(problems))

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{package_id}.tar.gz"
    with tempfile.TemporaryDirectory(prefix=f"{package_id}_", dir="/tmp") as tmpdir:
        staging = Path(tmpdir)
        copied: list[dict[str, object]] = []
        for name, source in sorted(resolved_sources.items()):
            destination_name = DESTINATIONS.get(name, f"support/{source.name}")
            destination = staging / destination_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied.append(
                {
                    "source_key": name,
                    "archive_path": destination_name,
                    "size_bytes": destination.stat().st_size,
                    "sha256": sha256_file(destination),
                }
            )

        contracts_path = staging / "contracts/scoring_contracts.csv"
        write_contracts(
            contracts_path,
            rows=int(input_audit["rows"]),
            rows_with_context=int(input_audit["rows_with_context"]),
        )
        readme = staging / "README.md"
        readme.write_text(
            "# Hall snapshot Mistral real-target handoff\n\n"
            "Score only `inputs/hall_child_snapshot_scoring.csv` under the four contracts in "
            f"`contracts/scoring_contracts.csv`. Preserve all {int(input_audit['rows']):,} input rows "
            "for every context. "
            "Blank k1-k3 contexts are structural and must be retained with availability flags. "
            "Do not fit Hall scientific models in the compute repository.\n",
            encoding="utf-8",
        )
        generated_files = [contracts_path, readme]
        file_manifest_rows = copied + [
            {
                "source_key": "generated",
                "archive_path": path.relative_to(staging).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in generated_files
        ]
        file_manifest_path = staging / "file_manifest.csv"
        with file_manifest_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["source_key", "archive_path", "size_bytes", "sha256"],
                quoting=csv.QUOTE_NONNUMERIC,
            )
            writer.writeheader()
            writer.writerows(file_manifest_rows)

        handoff_manifest = {
            "package_id": package_id,
            "contract_version": "hall-mistral-real-k0-k3-v1",
            "scientific_scope": "Hall cross-sectional real child utterances only",
            "target_column": "chi_utterance_clean",
            "contexts": {"k0": "", "k1": "context_k1", "k2": "context_k2", "k3": "context_k3"},
            "expected_contracts": 4,
            "expected_scored_rows": int(input_audit["rows"]) * 4,
            "input_audit": input_audit,
            "frozen_counts": dict(expected_counts),
            "source_artifacts": file_manifest_rows,
            "model_requirement": {
                "family": "mistralai/Mistral-7B-v0.3",
                "calibration": "match the completed full-79 Mistral production exactly",
                "dtype": "fp16",
                "revision_policy": "recover and record exact model/tokenizer/scoring revisions; do not invent blanks",
            },
            "production_policy": {
                "cpu_preflight": "required",
                "fresh_exact_wrapper_gpu_smoke": "required",
                "production_afterok_smoke": "required",
                "atomic_outputs": "required",
                "resume_only_after_validation": "required",
                "final_complete_and_audited_marker": "required",
            },
        }
        manifest_path = staging / "handoff_manifest.json"
        manifest_path.write_text(json.dumps(handoff_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        archive_sha256 = write_deterministic_archive(staging, archive_path, package_id)

    checksum_path = output_dir / f"{archive_path.name}.sha256"
    checksum_path.write_text(f"{archive_sha256}  {archive_path.name}\n", encoding="utf-8")
    audit = {
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "package_id": package_id,
        "archive_path": str(archive_path),
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_sha256": archive_sha256,
        "checksum_path": str(checksum_path),
        "observed_counts": observed,
        "input_audit": input_audit,
        "expected_contracts": 4,
        "expected_scored_rows": int(input_audit["rows"]) * 4,
        "problems": [],
    }
    audit_path = output_dir / "LOCAL_HANDOFF_AUDIT.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = output_dir / "LOCAL_HANDOFF_REPORT.md"
    report_path.write_text(
        "# Hall Mila handoff report\n\n"
        f"- Status: **PASS**\n"
        f"- Archive: `{archive_path.name}`\n"
        f"- SHA-256: `{archive_sha256}`\n"
        f"- Input rows: {input_audit['rows']:,}\n"
        f"- Children: {input_audit['children']}\n"
        f"- Contracts: 4 (k0, k1, k2, k3)\n"
        f"- Expected scored rows: {int(input_audit['rows']) * 4:,}\n"
        "- Required next gate: compute-repository tests, CPU preflight, then a fresh exact-wrapper GPU smoke.\n",
        encoding="utf-8",
    )
    return audit


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--package-id", default=PACKAGE_ID)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    audit = build_hall_mila_handoff(output_dir=args.output_dir, package_id=args.package_id)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
