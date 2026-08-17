#!/usr/bin/env python3
"""Relocation-aware audit for the completed Hall Mistral scoring archive.

The Mila archive records absolute cluster paths in provenance fields and in its
sidecar checksum.  This auditor deliberately treats those values as immutable
provenance while independently hashing the local archive, validating safe tar
members, checking every compressed product against its contract summary, and
rechecking the cross-context utterance panel against the frozen Hall input.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

import pandas as pd


EXPECTED_ARCHIVE_SHA256 = "c7c2422f19f87a0096136f73bf3a1fa664f5551ed095371920b3462db6d21202"
EXPECTED_INPUT_SHA256 = "5db6653d2df145096252daa289031fa2510f4f8e160bd14ae221e6e9bad7add8"
EXPECTED_MODEL_REVISION = "caa1feb0e54d415e2df31207e5f4e273e33509b1"
EXPECTED_CODE_REVISION = "66812c461e878d3ff52dec542255c2dc537b5ed9"
EXPECTED_ROWS = 71_830
EXPECTED_TOTALS = {
    "utterance_rows": 287_320,
    "word_rows": 1_182_476,
    "token_rows": 1_769_650,
    "allocation_rows": 1_461_794,
}
EXPECTED_CONTEXTS = ("k0", "k1", "k2", "k3")
MODEL_SLUG = "mistralai__Mistral-7B-v0.3__caa1feb0e54d"
INPUT_MEMBER = (
    "prepared/hall_snapshot_mistral_real_k0_k3_v1/inputs/"
    "hall_child_snapshot_scoring.csv"
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        frame.to_csv(temporary, index=False, lineterminator="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _member_bytes(archive: tarfile.TarFile, member_name: str) -> bytes:
    try:
        member = archive.getmember(member_name)
    except KeyError as exc:
        raise ValueError(f"required archive member is missing: {member_name}") from exc
    handle = archive.extractfile(member)
    if handle is None:
        raise ValueError(f"archive member is not a regular file: {member_name}")
    return handle.read()


def _json_member(archive: tarfile.TarFile, member_name: str) -> dict[str, object]:
    return json.loads(_member_bytes(archive, member_name).decode("utf-8"))


def _csv_member(archive: tarfile.TarFile, member_name: str) -> pd.DataFrame:
    data = _member_bytes(archive, member_name)
    if member_name.endswith(".gz"):
        data = gzip.decompress(data)
    return pd.read_csv(io.BytesIO(data), low_memory=False)


def _compressed_csv_rows(data: bytes) -> int:
    with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as handle:
        lines = sum(1 for _ in handle)
    return max(0, lines - 1)


def _boolean(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.fillna(False).astype(bool)
    values = series.fillna("").astype(str).str.strip().str.lower()
    if not set(values).issubset({"true", "false", "1", "0"}):
        raise ValueError(f"invalid boolean values: {sorted(set(values))[:5]}")
    return values.isin({"true", "1"})


def _validate_safe_members(archive: tarfile.TarFile) -> None:
    for member in archive.getmembers():
        name = PurePosixPath(member.name)
        if name.is_absolute() or ".." in name.parts or member.issym() or member.islnk():
            raise ValueError(f"unsafe archive member: {member.name}")
        if not (member.isfile() or member.isdir()):
            raise ValueError(f"unsupported archive member type: {member.name}")


def _contract_base(context: str) -> str:
    return (
        f"outputs/{MODEL_SLUG}/Hall/all_children/"
        f"real_{context}.word_surprisal"
    )


def audit_scored_archive(
    *,
    archive_path: Path,
    output_dir: Path,
    expected_archive_sha256: str = EXPECTED_ARCHIVE_SHA256,
    expected_input_sha256: str = EXPECTED_INPUT_SHA256,
    expected_rows: int = EXPECTED_ROWS,
    expected_totals: Mapping[str, int] = EXPECTED_TOTALS,
    expected_model_revision: str = EXPECTED_MODEL_REVISION,
    expected_code_revision: str = EXPECTED_CODE_REVISION,
) -> dict[str, object]:
    """Audit a local copy without relying on Mila absolute paths."""

    archive_path = archive_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(f"Hall scored archive is missing: {archive_path}")
    actual_archive_sha = sha256_path(archive_path)
    if actual_archive_sha != expected_archive_sha256:
        raise ValueError(
            "Hall archive SHA-256 mismatch: "
            f"expected {expected_archive_sha256}, found {actual_archive_sha}"
        )

    coverage: list[dict[str, object]] = []
    problems: list[str] = []
    identity_reference: pd.DataFrame | None = None
    unavailable_counts: list[int] = []
    blank_mean_diffs: list[float] = []
    blank_sum_diffs: list[float] = []
    totals = {key: 0 for key in expected_totals}

    with tarfile.open(archive_path, "r:gz") as archive:
        _validate_safe_members(archive)
        members = {member.name for member in archive.getmembers()}
        required_markers = {
            "WORD_SURPRISAL_COMPLETE",
            "reports/final/FINAL_AUDIT_PASSED",
            "reports/final/final_report.json",
            INPUT_MEMBER,
        }
        missing_markers = sorted(required_markers - members)
        if missing_markers:
            raise ValueError(f"required archive members are missing: {missing_markers}")

        input_bytes = _member_bytes(archive, INPUT_MEMBER)
        actual_input_sha = sha256_bytes(input_bytes)
        if actual_input_sha != expected_input_sha256:
            problems.append(
                f"input SHA-256 mismatch: expected {expected_input_sha256}, found {actual_input_sha}"
            )
        source = pd.read_csv(io.BytesIO(input_bytes), low_memory=False)
        required_source = {
            "utterance_id", "chi_utterance_clean", "child_id", "file", "line_no",
            "context_k1", "context_k2", "context_k3", "nb_words",
        }
        missing_source = sorted(required_source - set(source.columns))
        if missing_source:
            problems.append(f"frozen input is missing columns: {missing_source}")
        if len(source) != expected_rows:
            problems.append(f"input has {len(source)} rows; expected {expected_rows}")
        if source.get("utterance_id", pd.Series(dtype=str)).astype(str).duplicated().any():
            problems.append("frozen input contains duplicate utterance_id values")
        if source.get("chi_utterance_clean", pd.Series(dtype=str)).fillna("").astype(str).str.strip().eq("").any():
            problems.append("frozen input contains blank target text")

        final_report = _json_member(archive, "reports/final/final_report.json")
        final_expectations = {
            "status": "PASS", "problem_count": 0, "audited_contracts": 4,
            "model_revision": expected_model_revision,
            "code_revision": expected_code_revision,
            "dtype": "fp16", "batch_size": 16, "max_length": 4096,
            "word_level": True,
            "blank_context_policy": "score_target_only_and_retain_context_available_false",
        }
        for key, expected in final_expectations.items():
            if final_report.get(key) != expected:
                problems.append(
                    f"final report {key} mismatch: expected {expected!r}, found {final_report.get(key)!r}"
                )
        if tuple(final_report.get("contexts", [])) != EXPECTED_CONTEXTS:
            problems.append(f"final report contexts mismatch: {final_report.get('contexts')!r}")

        k0_scores: pd.DataFrame | None = None
        for contract_id, context in enumerate(EXPECTED_CONTEXTS):
            base = _contract_base(context)
            summary_name = f"{base}/contract_summary.json"
            complete_name = f"{base}/CONTRACT_COMPLETE"
            if complete_name not in members:
                problems.append(f"missing contract marker: {complete_name}")
                continue
            summary = _json_member(archive, summary_name)
            contract_expectations = {
                "status": "COMPLETE", "contract_id": contract_id,
                "context_window": context, "source_rows": expected_rows,
                "scored_utterance_rows": expected_rows, "utterance_rows": expected_rows,
                "source_sha256": expected_input_sha256,
                "model_key": "mistral-7b-v0.3", "word_level": True,
                "score_unavailable_context_as_k0": True,
            }
            for key, expected in contract_expectations.items():
                if summary.get(key) != expected:
                    problems.append(
                        f"{context} summary {key} mismatch: expected {expected!r}, found {summary.get(key)!r}"
                    )
            provenance = dict(summary.get("provenance", {}))
            if provenance.get("model_revision") != expected_model_revision:
                problems.append(f"{context} model revision mismatch")
            if provenance.get("scoring_code_revision") != expected_code_revision:
                problems.append(f"{context} scoring code revision mismatch")
            for key in totals:
                totals[key] += int(summary.get(key, 0))

            artifact_rows: dict[str, int] = {}
            for filename, row_key in (
                ("utterances.csv.gz", "utterance_rows"),
                ("words.csv.gz", "word_rows"),
                ("tokens.csv.gz", "token_rows"),
                ("token_word_allocations.csv.gz", "allocation_rows"),
            ):
                member_name = f"{base}/{filename}"
                data = _member_bytes(archive, member_name)
                record = dict(summary.get("artifacts", {}).get(filename, {}))
                if record.get("bytes") != len(data):
                    problems.append(f"{context}/{filename} byte count mismatch")
                if record.get("sha256") != sha256_bytes(data):
                    problems.append(f"{context}/{filename} SHA-256 mismatch")
                rows = _compressed_csv_rows(data)
                artifact_rows[row_key] = rows
                if rows != int(summary.get(row_key, -1)):
                    problems.append(
                        f"{context}/{filename} has {rows} rows; summary records {summary.get(row_key)}"
                    )

            scores = _csv_member(archive, f"{base}/utterances.csv.gz")
            required_scores = {
                "source_row", "utterance_id", "child_id", "file", "line_no",
                "context_window", "context_available", "target_text", "context_text",
                "score_status", "utterance_word_count_cleaned", "utterance_sum_bits",
                "utterance_mean_bits_per_token", "utterance_eval_tokens",
                "n_context_tokens_truncated", "model_revision", "scoring_code_revision",
            }
            missing_scores = sorted(required_scores - set(scores.columns))
            if missing_scores:
                problems.append(f"{context} utterance product is missing columns: {missing_scores}")
                continue
            if len(scores) != expected_rows:
                problems.append(f"{context} has {len(scores)} utterance rows; expected {expected_rows}")
            if scores["source_row"].duplicated().any() or set(scores["source_row"]) != set(range(expected_rows)):
                problems.append(f"{context} source_row is not the exact 0..{expected_rows - 1} identity")
            scores = scores.sort_values("source_row").reset_index(drop=True)
            if set(scores["context_window"].astype(str)) != {context}:
                problems.append(f"{context} output contains another context label")
            if set(scores["score_status"].astype(str)) != {"scored"}:
                problems.append(f"{context} output contains non-scored rows")
            if scores["target_text"].fillna("").astype(str).str.strip().eq("").any():
                problems.append(f"{context} output contains blank targets")
            for column in ("utterance_sum_bits", "utterance_mean_bits_per_token"):
                values = pd.to_numeric(scores[column], errors="coerce")
                if values.isna().any() or not all(math.isfinite(float(value)) for value in values):
                    problems.append(f"{context} contains non-finite {column}")
            if (pd.to_numeric(scores["utterance_eval_tokens"], errors="coerce") <= 0).any():
                problems.append(f"{context} contains a nonpositive target token count")
            if (pd.to_numeric(scores["n_context_tokens_truncated"], errors="coerce") != 0).any():
                problems.append(f"{context} contains truncated contexts")
            if not scores["target_text"].fillna("").astype(str).equals(
                source["chi_utterance_clean"].fillna("").astype(str)
            ):
                problems.append(f"{context} target text differs from the frozen input")
            if not scores["utterance_id"].astype(str).equals(source["utterance_id"].astype(str)):
                problems.append(f"{context} utterance identity differs from the frozen input")
            expected_context = (
                pd.Series([""] * len(source), dtype=str)
                if context == "k0"
                else source[f"context_{context}"].fillna("").astype(str)
            )
            if not scores["context_text"].fillna("").astype(str).equals(expected_context):
                problems.append(f"{context} context text differs from the frozen input")
            available = _boolean(scores["context_available"])
            expected_available = (
                pd.Series([True] * len(source))
                if context == "k0"
                else expected_context.str.strip().ne("")
            )
            if not available.reset_index(drop=True).equals(expected_available.reset_index(drop=True)):
                problems.append(f"{context} context availability differs from the frozen input")

            identities = scores[["source_row", "utterance_id", "target_text"]]
            if identity_reference is None:
                identity_reference = identities
                k0_scores = scores
            elif not identities.equals(identity_reference):
                problems.append(f"{context} cross-context row identity mismatch")
            if context != "k0":
                unavailable_counts.append(int((~available).sum()))
                if k0_scores is not None:
                    unavailable_index = ~available
                    blank_mean_diffs.extend(
                        (scores.loc[unavailable_index, "utterance_mean_bits_per_token"].astype(float)
                         - k0_scores.loc[unavailable_index, "utterance_mean_bits_per_token"].astype(float)).abs().tolist()
                    )
                    blank_sum_diffs.extend(
                        (scores.loc[unavailable_index, "utterance_sum_bits"].astype(float)
                         - k0_scores.loc[unavailable_index, "utterance_sum_bits"].astype(float)).abs().tolist()
                    )
            coverage.append(
                {
                    "contract_id": contract_id,
                    "context_window": context,
                    "utterance_rows": artifact_rows.get("utterance_rows", 0),
                    "word_rows": artifact_rows.get("word_rows", 0),
                    "token_rows": artifact_rows.get("token_rows", 0),
                    "allocation_rows": artifact_rows.get("allocation_rows", 0),
                    "context_available_rows": int(available.sum()),
                    "blank_context_rows": int((~available).sum()),
                    "status": "PASS",
                }
            )

        for key, expected in expected_totals.items():
            if totals[key] != int(expected):
                problems.append(f"total {key} mismatch: expected {expected}, found {totals[key]}")
            if int(final_report.get(key, -1)) != int(expected):
                problems.append(
                    f"final report {key} mismatch: expected {expected}, found {final_report.get(key)}"
                )
        if unavailable_counts and len(set(unavailable_counts)) != 1:
            problems.append(f"blank-context row counts differ across k1-k3: {unavailable_counts}")
        if max(blank_mean_diffs, default=0.0) > 0.15:
            problems.append("blank-context mean-bits equivalence exceeds 0.15")
        if max(blank_sum_diffs, default=0.0) > 0.5:
            problems.append("blank-context sum-bits equivalence exceeds 0.5")

        member_count = len(archive.getmembers())

    report: dict[str, object] = {
        "status": "PASS" if not problems else "FAIL",
        "problem_count": len(problems),
        "problems": problems,
        "archive_path": str(archive_path),
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": actual_archive_sha,
        "input_sha256": actual_input_sha,
        "member_count": member_count,
        "audited_contracts": len(coverage),
        "contexts": list(EXPECTED_CONTEXTS),
        "children": int(source["child_id"].nunique()) if "child_id" in source else 0,
        **totals,
        "blank_context_rows_per_nonzero_context": (
            unavailable_counts[0] if unavailable_counts and len(set(unavailable_counts)) == 1 else None
        ),
        "blank_context_comparison_rows": len(blank_mean_diffs),
        "blank_context_max_abs_mean_bits_diff": max(blank_mean_diffs, default=0.0),
        "blank_context_max_abs_sum_bits_diff": max(blank_sum_diffs, default=0.0),
        "model_id": "mistralai/Mistral-7B-v0.3",
        "model_revision": expected_model_revision,
        "scoring_code_revision": expected_code_revision,
        "dtype": "fp16",
        "score_unit": "bits",
        "word_level": True,
        "absolute_mila_paths_treated_as_provenance": True,
    }
    _atomic_csv(pd.DataFrame(coverage), output_dir / "coverage_by_contract.csv")
    _atomic_text(
        output_dir / "local_retrieval_audit.json",
        json.dumps(report, indent=2, sort_keys=True) + "\n",
    )
    if problems:
        raise ValueError(f"Hall local retrieval audit failed with {len(problems)} problem(s): {problems[0]}")
    _atomic_text(
        output_dir / "LOCAL_RETRIEVAL_AUDIT_PASSED",
        f"LOCAL_RETRIEVAL_AUDIT_PASSED\n{sha256_path(output_dir / 'local_retrieval_audit.json')}\n",
    )
    return report


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    report = audit_scored_archive(archive_path=args.archive, output_dir=args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
