#!/usr/bin/env python3
"""Freeze an age-matched snapshot comparator for the Hall corpus.

Selection is outcome-blind.  It reads only identity, age, session, scope, and
row-count fields from the existing full-79 Mistral trajectory input, restricts
to the Hall-compatible 54--59 month bin, and chooses one session per child
closest to the median age of the primary Hall sample.  The selected session
manifest can later be joined to scored utterances without turning a
cross-sectional question into another longitudinal trajectory analysis.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HALL_METADATA = PROJECT_ROOT / "results/hall_snapshot_preprocessing/hall_child_metadata.csv"
DEFAULT_TRAJECTORY_INPUT = (
    PROJECT_ROOT
    / "results/direct_surprisal_replication/mistral_full79/modular/prepared/trajectory_input.csv.gz"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "results/hall_snapshot_preprocessing/hall_comparison_snapshot_manifest.csv"
DEFAULT_AUDIT = PROJECT_ROOT / "results/hall_snapshot_preprocessing/hall_comparison_snapshot_audit.json"

ELIGIBLE_SCOPES = {"pbm_discovery", "non_pbm_confirmation"}
OUTPUT_COLUMNS = [
    "dataset", "child_id", "child_key", "scope", "session_id", "age_months",
    "age_bin", "utterances", "hall_target_age_months",
    "distance_from_target_months", "selection_rule",
]


def _open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", newline="", encoding="utf-8")
    return path.open("r", newline="", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _hall_primary_ages(path: Path) -> list[float]:
    ages: list[float] = []
    with _open_text(path) as handle:
        for row in csv.DictReader(handle):
            if row.get("primary_eligible", "") != "1":
                continue
            age = _float(row.get("age_months", ""))
            if age is not None:
                ages.append(age)
    return ages


def _candidate_sessions(
    path: Path,
    *,
    age_min: float,
    age_max_exclusive: float,
) -> Iterator[dict[str, object]]:
    counts: dict[tuple[str, ...], int] = defaultdict(int)
    with _open_text(path) as handle:
        reader = csv.DictReader(handle)
        required = {
            "role", "scope", "dataset", "child_id", "child_key", "session_id",
            "age_months", "age_bin", "utterances",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Trajectory input is missing columns: {sorted(missing)}")
        for row in reader:
            if row["role"] != "child" or row["scope"] not in ELIGIBLE_SCOPES:
                continue
            age = _float(row["age_months"])
            if age is None or not (age_min <= age < age_max_exclusive):
                continue
            key = (
                row["dataset"], row["child_id"], row["child_key"], row["scope"],
                row["session_id"], row["age_months"], row["age_bin"],
            )
            try:
                counts[key] += int(float(row["utterances"]))
            except (TypeError, ValueError):
                pass
    for key, utterances in counts.items():
        dataset, child_id, child_key, scope, session_id, age_text, age_bin = key
        yield {
            "dataset": dataset,
            "child_id": child_id,
            "child_key": child_key,
            "scope": scope,
            "session_id": session_id,
            "age_months": float(age_text),
            "age_bin": age_bin,
            "utterances": utterances,
        }


def build_snapshot_comparator(
    *,
    hall_metadata: Path = DEFAULT_HALL_METADATA,
    trajectory_input: Path = DEFAULT_TRAJECTORY_INPUT,
    output_csv: Path = DEFAULT_OUTPUT,
    audit_json: Path = DEFAULT_AUDIT,
    age_min: float = 54.0,
    age_max_exclusive: float = 60.0,
) -> dict[str, object]:
    """Select one closest-age session per current Mistral child."""

    hall_metadata = hall_metadata.expanduser().resolve()
    trajectory_input = trajectory_input.expanduser().resolve()
    ages = _hall_primary_ages(hall_metadata)
    if not ages:
        raise ValueError("No primary Hall child ages were available")
    target_age = float(statistics.median(ages))
    candidates = list(
        _candidate_sessions(
            trajectory_input,
            age_min=age_min,
            age_max_exclusive=age_max_exclusive,
        )
    )

    by_child: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in candidates:
        by_child[str(row["child_key"])].append(row)

    selected: list[dict[str, object]] = []
    for child_key in sorted(by_child):
        choice = min(
            by_child[child_key],
            key=lambda row: (
                abs(float(row["age_months"]) - target_age),
                float(row["age_months"]),
                str(row["session_id"]),
            ),
        )
        selected.append(
            {
                **choice,
                "hall_target_age_months": target_age,
                "distance_from_target_months": abs(float(choice["age_months"]) - target_age),
                "selection_rule": "one_session_per_child_nearest_hall_primary_median_age_outcome_blind",
            }
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        writer.writerows(selected)

    problems: list[str] = []
    if not selected:
        problems.append("no_eligible_comparator_sessions")
    if len(selected) != len({str(row["child_key"]) for row in selected}):
        problems.append("duplicate_selected_children")
    audit: dict[str, object] = {
        "status": "PASS" if not problems else "REVIEW",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hall_metadata": str(hall_metadata),
        "hall_metadata_sha256": _sha256(hall_metadata),
        "trajectory_input": str(trajectory_input),
        "trajectory_input_sha256": _sha256(trajectory_input),
        "hall_primary_children_with_age": len(ages),
        "hall_primary_target_age_months": target_age,
        "age_window": {"minimum_inclusive": age_min, "maximum_exclusive": age_max_exclusive},
        "candidate_sessions": len(candidates),
        "selected_children": len(selected),
        "selected_pbm_children": sum(row["scope"] == "pbm_discovery" for row in selected),
        "selected_non_pbm_children": sum(row["scope"] == "non_pbm_confirmation" for row in selected),
        "problems": problems,
        "selection_uses_outcomes": False,
    }
    audit_json.parent.mkdir(parents=True, exist_ok=True)
    audit_json.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hall-metadata", type=Path, default=DEFAULT_HALL_METADATA)
    parser.add_argument("--trajectory-input", type=Path, default=DEFAULT_TRAJECTORY_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--age-min", type=float, default=54.0)
    parser.add_argument("--age-max-exclusive", type=float, default=60.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    audit = build_snapshot_comparator(
        hall_metadata=args.hall_metadata,
        trajectory_input=args.trajectory_input,
        output_csv=args.output_csv,
        audit_json=args.audit_json,
        age_min=args.age_min,
        age_max_exclusive=args.age_max_exclusive,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
