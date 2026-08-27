#!/usr/bin/env python3
"""Build the frozen full-79 downstream caregiver-response scoring handoff.

Each retained row targets the caregiver turn immediately following a child
turn.  The target is scored under an unconditional condition and four explicit
context conditions so that the child's incremental contribution can be
estimated without calling child-target predictability listener utility.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "configs/downstream_caregiver_response_utility.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/downstream_caregiver_response_handoff/full_20260827"
PBM_DATASETS = {"Brown", "Manchester", "Providence"}
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?")

OUTPUT_COLUMNS = (
    "dataset",
    "child_id",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_years",
    "age_bin",
    "age_bin_mid",
    "file",
    "line_no",
    "next_caregiver_line_no",
    "utt_id",
    "utterance_id",
    "response_pair_id",
    "speaker_mode",
    "target_text",
    "target_text_sha256",
    "child_text",
    "child_text_sha256",
    "shuffled_child_text",
    "shuffled_child_text_sha256",
    "context_base",
    "context_matched_child",
    "context_shuffled_child",
    "context_child_only",
    "context_base_sha256",
    "context_matched_child_sha256",
    "context_shuffled_child_sha256",
    "context_child_only_sha256",
    "child_word_count",
    "child_character_count",
    "response_word_count",
    "response_character_count",
    "base_context_word_count",
    "primary_eligible",
    "sensitivity_eligible",
    "shuffle_available",
    "shuffle_match_level",
    "shuffle_source_pair_id",
    "shuffle_source_child_key",
    "previous_caretaker_question_type",
    "child_question_type",
    "next_caregiver_question_type",
    "exact_imitation_candidate",
    "contained_imitation_candidate",
    "child_backchannel_candidate",
    "session_reading_candidate",
    "session_routine_candidate",
    "repair_sequence_candidate",
    "next_caregiver_clarification_candidate",
    "next_caregiver_acknowledgement_candidate",
)


def clean_text(value: object) -> str:
    return " ".join(("" if value is None else str(value)).split())


def lexical_word_count(value: object) -> int:
    return len(WORD_RE.findall(clean_text(value)))


def stable_id(*values: object) -> str:
    payload = "\x1f".join(str(value) for value in values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def text_sha256(value: object) -> str:
    return hashlib.sha256(clean_text(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@contextmanager
def reproducible_gzip_text(path: Path) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                yield text


def _open_csv(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open(encoding="utf-8", newline="")


def _age_bin_mid(label: str) -> str:
    match = re.fullmatch(r"(\d{3})-(\d{3})", label)
    if not match:
        return ""
    return str((int(match.group(1)) + int(match.group(2))) / 2)


def _compact_source_row(source: Mapping[str, str]) -> dict[str, object] | None:
    response = clean_text(source.get("next_main_utterance_clean", ""))
    child_text = clean_text(source.get("chi_utterance_clean", ""))
    base_context = clean_text(source.get("context_k3", ""))
    sensitivity = (
        source.get("raw_line_aligned") == "1"
        and source.get("raw_target_text_matches") == "1"
        and source.get("next_main_is_caretaker") == "1"
        and bool(response)
        and bool(child_text)
        and bool(base_context)
    )
    if not sensitivity:
        return None
    primary = (
        source.get("primary_responsive_turn_eligible") == "1"
        and source.get("context_k1_matches_nearest_caretaker") == "1"
    )
    dataset = clean_text(source.get("dataset", ""))
    child_id = clean_text(source.get("child_id", ""))
    file_label = clean_text(source.get("file", ""))
    line_no = clean_text(source.get("line_no", ""))
    next_line = clean_text(source.get("next_main_line_no", ""))
    child_key = f"{dataset}/{child_id}"
    pair_id = stable_id("caregiver_response_pair_v1", dataset, child_id, file_label, line_no, next_line)
    age_months = clean_text(source.get("age_months", ""))
    try:
        age_years = str(float(age_months) / 12)
    except ValueError:
        age_years = ""
    age_bin = clean_text(source.get("age_bin", ""))
    return {
        "dataset": dataset,
        "child_id": child_id,
        "child_key": child_key,
        "sample_group": "pbm_discovery" if dataset in PBM_DATASETS else "non_pbm_confirmation",
        "session_id": clean_text(source.get("session_id", "")),
        "age_months": age_months,
        "age_years": age_years,
        "age_bin": age_bin,
        "age_bin_mid": _age_bin_mid(age_bin),
        "file": file_label,
        "line_no": line_no,
        "next_caregiver_line_no": next_line,
        "utt_id": clean_text(source.get("utt_id", "")),
        "utterance_id": pair_id,
        "response_pair_id": pair_id,
        "speaker_mode": "caregiver_response",
        "target_text": response,
        "target_text_sha256": text_sha256(response),
        "child_text": child_text,
        "child_text_sha256": text_sha256(child_text),
        "context_base": base_context,
        "context_matched_child": f"{base_context} {child_text}",
        "context_child_only": child_text,
        "context_base_sha256": text_sha256(base_context),
        "context_matched_child_sha256": text_sha256(f"{base_context} {child_text}"),
        "context_child_only_sha256": text_sha256(child_text),
        "child_word_count": lexical_word_count(child_text),
        "child_character_count": len(child_text),
        "response_word_count": lexical_word_count(response),
        "response_character_count": len(response),
        "base_context_word_count": lexical_word_count(base_context),
        "primary_eligible": int(primary),
        "sensitivity_eligible": 1,
        **{
            column: clean_text(source.get(column, ""))
            for column in (
                "previous_caretaker_question_type",
                "child_question_type",
                "next_caregiver_question_type",
                "exact_imitation_candidate",
                "contained_imitation_candidate",
                "child_backchannel_candidate",
                "session_reading_candidate",
                "session_routine_candidate",
                "repair_sequence_candidate",
                "next_caregiver_clarification_candidate",
                "next_caregiver_acknowledgement_candidate",
            )
        },
    }


def _candidate_offsets(size: int, seed: int) -> list[int]:
    if size < 2:
        return []
    offsets = set(range(1, min(size, 258)))
    offsets.update({size // 2, max(1, size // 3), max(1, (2 * size) // 3)})
    offsets.add(1 + seed % (size - 1))
    return sorted(value for value in offsets if 0 < value < size)


def assign_deterministic_shuffles(rows: list[dict[str, object]], *, seed: int) -> Counter[str]:
    """Assign an exact dataset/age-bin/word-count negative-control permutation."""

    grouped: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[(str(row["dataset"]), str(row["age_bin"]), int(row["child_word_count"]))].append(index)
    counts: Counter[str] = Counter()
    for key, indices in grouped.items():
        indices.sort(key=lambda i: stable_id(seed, rows[i]["response_pair_id"]))
        if len(indices) < 2:
            for index in indices:
                rows[index].update(
                    {
                        "shuffled_child_text": "",
                        "shuffled_child_text_sha256": "",
                        "context_shuffled_child": "",
                        "context_shuffled_child_sha256": "",
                        "shuffle_available": 0,
                        "shuffle_match_level": "singleton_stratum",
                        "shuffle_source_pair_id": "",
                        "shuffle_source_child_key": "",
                    }
                )
                counts["singleton_stratum"] += 1
            continue

        best_offset = 1
        best_score: tuple[int, int, int] | None = None
        for offset in _candidate_offsets(len(indices), seed):
            different_text = different_session = different_child = 0
            for position, index in enumerate(indices):
                candidate = rows[indices[(position + offset) % len(indices)]]
                row = rows[index]
                different_text += int(candidate["child_text_sha256"] != row["child_text_sha256"])
                different_session += int(
                    (candidate["child_key"], candidate["file"]) != (row["child_key"], row["file"])
                )
                different_child += int(candidate["child_key"] != row["child_key"])
            score = (different_text, different_child, different_session)
            if best_score is None or score > best_score:
                best_score = score
                best_offset = offset

        for position, index in enumerate(indices):
            row = rows[index]
            candidate = rows[indices[(position + best_offset) % len(indices)]]
            different_text = candidate["child_text_sha256"] != row["child_text_sha256"]
            if not different_text:
                match_level = "same_surface_text_unavailable"
            elif candidate["child_key"] != row["child_key"]:
                match_level = "exact_dataset_age_words_other_child"
            elif candidate["file"] != row["file"]:
                match_level = "exact_dataset_age_words_other_file"
            else:
                match_level = "exact_dataset_age_words_same_file"
            shuffled = str(candidate["child_text"]) if different_text else ""
            shuffled_context = f"{row['context_base']} {shuffled}" if shuffled else ""
            row.update(
                {
                    "shuffled_child_text": shuffled,
                    "shuffled_child_text_sha256": text_sha256(shuffled) if shuffled else "",
                    "context_shuffled_child": shuffled_context,
                    "context_shuffled_child_sha256": text_sha256(shuffled_context) if shuffled else "",
                    "shuffle_available": int(different_text),
                    "shuffle_match_level": match_level,
                    "shuffle_source_pair_id": candidate["response_pair_id"] if different_text else "",
                    "shuffle_source_child_key": candidate["child_key"] if different_text else "",
                }
            )
            counts[match_level] += 1
    return counts


def write_dataset_input(path: Path, rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    counts: Counter[str] = Counter()
    children: set[str] = set()
    pair_ids: set[str] = set()
    with reproducible_gzip_text(path) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            pair_id = str(row["response_pair_id"])
            if pair_id in pair_ids:
                raise ValueError(f"duplicate response pair ID in {path.name}: {pair_id}")
            pair_ids.add(pair_id)
            children.add(str(row["child_key"]))
            counts["rows"] += 1
            counts["primary_rows"] += int(row["primary_eligible"])
            counts["shuffle_rows"] += int(row["shuffle_available"])
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})
    return {
        **counts,
        "children": len(children),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_deterministic_archive(source_root: Path, archive_path: Path, package_id: str) -> str:
    temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
    with temporary.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", fileobj=raw_handle, mode="wb", mtime=0) as gzip_handle:
            with tarfile.open(fileobj=gzip_handle, mode="w") as archive:
                for path in sorted(candidate for candidate in source_root.rglob("*") if candidate.is_file()):
                    relative = path.relative_to(source_root).as_posix()
                    info = archive.gettarinfo(str(path), arcname=f"{package_id}/{relative}")
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    info.mode = 0o644
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
    os.replace(temporary, archive_path)
    return sha256_file(archive_path)


def build_handoff(
    *,
    config_path: Path = DEFAULT_CONFIG,
    output_dir: Path = DEFAULT_OUTPUT,
    project_root: Path = PROJECT_ROOT,
    build_archive: bool = True,
) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    package_id = str(config["package_id"])
    source_path = project_root / str(config["source_flags"])
    source_audit_path = project_root / str(config["source_audit"])
    if sha256_file(source_path) != config["source_flags_sha256"]:
        raise ValueError("conversational source SHA-256 changed")
    source_audit = json.loads(source_audit_path.read_text(encoding="utf-8"))
    if int(source_audit["counts"]["rows"]) != int(config["expected"]["source_rows"]):
        raise ValueError("conversational source-row count changed")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"fresh output directory required: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    source_rows = 0
    with _open_csv(source_path) as handle:
        for source in csv.DictReader(handle):
            source_rows += 1
            compact = _compact_source_row(source)
            if compact is not None:
                rows.append(compact)
    shuffle_counts = assign_deterministic_shuffles(rows, seed=int(config["shuffle_seed"]))
    by_dataset: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_dataset[str(row["dataset"])].append(row)

    inventory: list[dict[str, object]] = []
    inputs_dir = output_dir / "inputs"
    for dataset in sorted(by_dataset):
        dataset_rows = sorted(
            by_dataset[dataset],
            key=lambda row: (str(row["child_id"]), str(row["file"]), int(float(str(row["line_no"])))),
        )
        path = inputs_dir / f"{dataset}.caregiver_response.csv.gz"
        stats = write_dataset_input(path, dataset_rows)
        inventory.append(
            {
                "dataset": dataset,
                "children": stats["children"],
                "rows": stats["rows"],
                "primary_rows": stats["primary_rows"],
                "shuffle_rows": stats["shuffle_rows"],
                "input_relpath": path.relative_to(output_dir).as_posix(),
                "size_bytes": stats["size_bytes"],
                "sha256": stats["sha256"],
            }
        )

    contracts: list[dict[str, object]] = []
    for item in inventory:
        for condition in config["conditions"]:
            context_column = str(condition["context_column"])
            available = int(item["rows"])
            if condition["condition"] == "shuffled_child":
                available = int(item["shuffle_rows"])
            contracts.append(
                {
                    "dataset": item["dataset"],
                    "scoring_condition": condition["condition"],
                    "input_relpath": item["input_relpath"],
                    "target_column": "target_text",
                    "context_column": context_column,
                    "expected_input_rows": item["rows"],
                    "expected_nonempty_target_rows": item["rows"],
                    "expected_context_available_rows": available,
                    "source_sha256": item["sha256"],
                }
            )

    scoring_plan = [
        {
            "model_key": model["model_key"],
            "model_id": model["model_id"],
            "dataset": item["dataset"],
            "target_rows": item["rows"],
            "conditions": ",".join(condition["condition"] for condition in config["conditions"]),
            "action": "SCORE_PENDING",
        }
        for model in config["models"]
        for item in inventory
    ]
    write_csv(output_dir / "dataset_inventory.csv", inventory)
    write_csv(output_dir / "scoring_contracts_template.csv", contracts)
    write_csv(output_dir / "model_scoring_plan.csv", scoring_plan)

    totals = {
        "source_rows": source_rows,
        "datasets": len(inventory),
        "children": sum(int(item["children"]) for item in inventory),
        "sensitivity_rows": len(rows),
        "primary_rows": sum(int(row["primary_eligible"]) for row in rows),
        "pbm_primary_rows": sum(
            int(row["primary_eligible"]) for row in rows if row["sample_group"] == "pbm_discovery"
        ),
        "non_pbm_primary_rows": sum(
            int(row["primary_eligible"]) for row in rows if row["sample_group"] == "non_pbm_confirmation"
        ),
        "shuffle_available_rows": sum(int(row["shuffle_available"]) for row in rows),
        "conditions": len(config["conditions"]),
        "contracts_per_model": len(contracts),
        "model_contracts_pending": len(contracts) * len(config["models"]),
    }
    for key, expected in config["expected"].items():
        if int(totals[key]) != int(expected):
            raise ValueError(f"frozen total changed for {key}: {totals[key]} != {expected}")

    audit = {
        "status": "PASS",
        "schema_version": config["schema_version"],
        "package_id": package_id,
        "source_flags_sha256": config["source_flags_sha256"],
        "source_conversational_audit_status": source_audit["status"],
        "source_context_k1_mismatches": source_audit["counts"].get("eligible_context_k1_mismatches", 0),
        "primary_excludes_context_k1_mismatches": True,
        "totals": totals,
        "shuffle_match_counts": dict(sorted(shuffle_counts.items())),
    }
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Downstream caregiver-response scoring handoff\n\n"
        "Targets are immediate next-caregiver utterances. Conditions are unconditional, preceding "
        "caregiver context alone, the same context plus the matched child utterance, the same context "
        "plus a deterministic exact-dataset/age-bin/word-count shuffled child utterance, and the child "
        "utterance alone. Raw scorer magnitudes must remain model-specific.\n",
        encoding="utf-8",
    )
    manifest_files = [
        path for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "handoff_manifest.json"
    ]
    manifest = {
        "schema_version": config["schema_version"],
        "package_id": package_id,
        "audit_status": "PASS",
        "totals": totals,
        "files": [
            {
                "path": path.relative_to(output_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in manifest_files
        ],
    }
    manifest_path = output_dir / "handoff_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "BUILD_COMPLETE_AND_AUDITED").write_text(
        f"{package_id}\n{sha256_file(manifest_path)}\n", encoding="utf-8"
    )

    archive_path = output_dir.parent / f"{package_id}.tar.gz"
    archive_sha256 = ""
    if build_archive:
        archive_sha256 = write_deterministic_archive(output_dir, archive_path, package_id)
        (archive_path.parent / f"{archive_path.name}.sha256").write_text(
            f"{archive_sha256}  {archive_path.name}\n", encoding="utf-8"
        )
    return {
        "status": "PASS",
        "output_dir": str(output_dir),
        "archive_path": str(archive_path) if build_archive else "",
        "archive_sha256": archive_sha256,
        **totals,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-archive", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            build_handoff(
                config_path=args.config,
                output_dir=args.output_dir,
                build_archive=not args.no_archive,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
