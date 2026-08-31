#!/usr/bin/env python3
"""Safely audit, extract, and link downstream caregiver-response scores."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import tarfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/downstream_caregiver_response_score_import_20260831.json"
DEFAULT_ARCHIVE_ROOT = (
    ROOT.parent
    / "compute_surprisal_mila/mila_results/downstream_caregiver_response_surprisal/20260831_123914"
)
DEFAULT_REPORT_ROOT = ROOT / "results/downstream_caregiver_response_score_import/20260831_123914"
DEFAULT_LINK_ROOT = ROOT / "results/external/compute_surprisal_mila"
SCHEMA = "crossmodel_word_surprisal_v2"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    names: set[str] = set()
    for member in members:
        name = PurePosixPath(member.name)
        if (
            name.is_absolute()
            or ".." in name.parts
            or member.issym()
            or member.islnk()
            or not (member.isfile() or member.isdir())
        ):
            raise ValueError(f"unsafe archive member: {member.name}")
        if member.name in names:
            raise ValueError(f"duplicate archive member: {member.name}")
        names.add(member.name)
    return members


def _bytes(archive: tarfile.TarFile, name: str) -> bytes:
    try:
        member = archive.getmember(name)
    except KeyError as exc:
        raise ValueError(f"missing archive member: {name}") from exc
    handle = archive.extractfile(member)
    if handle is None:
        raise ValueError(f"archive member is not a file: {name}")
    return handle.read()


def _gzip_csv_shape(data: bytes) -> tuple[int, tuple[str, ...]]:
    with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as compressed:
        with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
            reader = csv.reader(text)
            header = tuple(next(reader))
            rows = sum(1 for _ in reader)
    return rows, header


def audit_archive(
    archive_path: Path,
    *,
    spec: dict[str, object],
    config: dict[str, object],
) -> dict[str, object]:
    scorer = str(spec["scorer_key"])
    if archive_path.stat().st_size != int(spec["archive_bytes"]):
        raise ValueError(f"archive byte count mismatch for {scorer}")
    archive_sha = sha256_path(archive_path)
    if archive_sha != str(spec["archive_sha256"]):
        raise ValueError(f"archive SHA-256 mismatch for {scorer}")

    coverage: list[dict[str, object]] = []
    with tarfile.open(archive_path, "r:gz") as archive:
        members = _safe_members(archive)
        names = {member.name for member in members}
        required = {
            "SURPRISAL_COMPLETE",
            "manifests/word_output_contracts.tsv",
            "reports/completion/audit_report.json",
        }
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"required members missing for {scorer}: {missing}")
        completion = json.loads(_bytes(archive, "reports/completion/audit_report.json"))
        expectations = {
            "status": "PASS",
            "model_key": scorer,
            "scope": "downstream_caregiver_response_v1",
            "contracts": int(config["expected_contracts"]),
            "audited_contracts": int(config["expected_contracts"]),
            "utterance_rows": int(config["expected_utterance_rows"]),
            "problem_count": 0,
            "word_level": False,
            "scoring_code_revision": str(config["scoring_code_revision"]),
        }
        for key, expected in expectations.items():
            if completion.get(key) != expected:
                raise ValueError(
                    f"completion {key} mismatch for {scorer}: "
                    f"expected {expected!r}, found {completion.get(key)!r}"
                )

        manifest_data = _bytes(archive, "manifests/word_output_contracts.tsv").decode()
        contracts = list(csv.DictReader(io.StringIO(manifest_data), delimiter="\t"))
        if len(contracts) != int(config["expected_contracts"]):
            raise ValueError(f"contract count mismatch for {scorer}")
        datasets = {row["corpus"] for row in contracts}
        conditions = {row["context_window"] for row in contracts}
        if len(datasets) != int(config["expected_datasets"]):
            raise ValueError(f"dataset count mismatch for {scorer}")
        if conditions != set(config["expected_conditions"]):
            raise ValueError(f"condition inventory mismatch for {scorer}")
        if any(row["model_key"] != scorer for row in contracts):
            raise ValueError(f"manifest model mismatch for {scorer}")

        required_columns = {
            "source_row",
            "utterance_id",
            "target_text",
            "score_status",
            "context_available",
            "utterance_sum_bits",
            "model_key",
            "scoring_code_revision",
        }
        for row in contracts:
            base = f"outputs/{row['output_relpath']}"
            summary_name = f"{base}/contract_summary.json"
            marker_name = f"{base}/CONTRACT_COMPLETE"
            score_name = f"{base}/utterances.csv.gz"
            for name in (summary_name, marker_name, score_name):
                if name not in names:
                    raise ValueError(f"missing contract member for {scorer}: {name}")
            summary_bytes = _bytes(archive, summary_name)
            marker = _bytes(archive, marker_name).decode().splitlines()
            if marker != [SCHEMA, sha256_bytes(summary_bytes)]:
                raise ValueError(f"contract marker mismatch: {scorer}/{row['contract_id']}")
            summary = json.loads(summary_bytes)
            summary_expectations = {
                "status": "COMPLETE",
                "schema_version": SCHEMA,
                "scope": "downstream_caregiver_response_v1",
                "model_key": scorer,
                "contract_id": int(row["contract_id"]),
                "context_window": row["context_window"],
                "source_sha256": row["source_sha256"],
                "target_text_sha256": row["target_text_sha256"],
                "context_text_sha256": row["context_text_sha256"],
                "source_rows": int(row["source_rows"]),
                "utterance_rows": int(row["source_rows"]),
                "word_level": False,
            }
            for key, expected in summary_expectations.items():
                if summary.get(key) != expected:
                    raise ValueError(
                        f"contract {key} mismatch: {scorer}/{row['contract_id']}"
                    )
            artifact = _bytes(archive, score_name)
            recorded = summary.get("artifacts", {}).get("utterances.csv.gz", {})
            if recorded.get("bytes") != len(artifact):
                raise ValueError(f"artifact bytes mismatch: {scorer}/{row['contract_id']}")
            if recorded.get("sha256") != sha256_bytes(artifact):
                raise ValueError(f"artifact hash mismatch: {scorer}/{row['contract_id']}")
            rows, header = _gzip_csv_shape(artifact)
            if rows != int(row["source_rows"]):
                raise ValueError(f"artifact row mismatch: {scorer}/{row['contract_id']}")
            if not required_columns.issubset(header):
                raise ValueError(f"artifact schema mismatch: {scorer}/{row['contract_id']}")
            coverage.append(
                {
                    "contract_id": int(row["contract_id"]),
                    "dataset": row["corpus"],
                    "condition": row["context_window"],
                    "output_relpath": row["output_relpath"],
                    "rows": rows,
                    "artifact_sha256": recorded["sha256"],
                }
            )
    return {
        "status": "PASS",
        "scorer_key": scorer,
        "archive": str(archive_path.resolve()),
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": archive_sha,
        "hash_basis": "locally_frozen_after_rsync_plus_embedded_contract_hash_audit",
        "contracts": len(coverage),
        "datasets": len({item["dataset"] for item in coverage}),
        "conditions": sorted({item["condition"] for item in coverage}),
        "utterance_rows": sum(int(item["rows"]) for item in coverage),
        "coverage": coverage,
    }


def extract_archive(archive_path: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"fresh extraction destination required: {destination}")
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in _safe_members(archive):
                target = temporary / member.name
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f"cannot extract member: {member.name}")
                with target.open("wb") as output:
                    shutil.copyfileobj(source, output)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def run_import(
    *,
    config_path: Path,
    archive_root: Path,
    report_root: Path,
    link_root: Path,
) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    report_root.mkdir(parents=True, exist_ok=True)
    extracted_root = archive_root / "extracted"
    extracted_root.mkdir(parents=True, exist_ok=True)
    audits = []
    for spec in config["models"]:
        scorer = str(spec["scorer_key"])
        archive_path = archive_root / str(spec["archive"])
        audit = audit_archive(archive_path, spec=spec, config=config)
        destination = extracted_root / scorer
        extract_archive(archive_path, destination)
        for item in audit["coverage"]:
            artifact = (
                destination
                / "outputs"
                / str(item["output_relpath"])
                / "utterances.csv.gz"
            )
            if sha256_path(artifact) != str(item["artifact_sha256"]):
                raise ValueError(f"relocated artifact hash mismatch: {artifact}")
        link_root.mkdir(parents=True, exist_ok=True)
        link = link_root / str(spec["link_name"])
        if link.exists() or link.is_symlink():
            raise FileExistsError(f"fresh external link required: {link}")
        link.symlink_to(destination, target_is_directory=True)
        audit["extracted_root"] = str(destination.resolve())
        audit["external_link"] = str(link)
        audits.append(audit)

    report = {
        "status": "PASS",
        "schema_version": "1.0.0",
        "config": str(config_path.resolve()),
        "config_sha256": sha256_path(config_path),
        "run_id": config["run_id"],
        "models": audits,
    }
    audit_path = report_root / "relocation_audit.json"
    audit_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (report_root / "SCORES_IMPORTED_AND_AUDITED").write_text(
        f"{sha256_path(audit_path)}\n"
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--link-root", type=Path, default=DEFAULT_LINK_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_import(
        config_path=args.config.resolve(),
        archive_root=args.archive_root.resolve(),
        report_root=args.report_root.resolve(),
        link_root=args.link_root.resolve(),
    )
    print(json.dumps({"status": report["status"], "models": len(report["models"])}, sort_keys=True))


if __name__ == "__main__":
    main()
