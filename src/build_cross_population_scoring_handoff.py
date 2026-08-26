#!/usr/bin/env python3
"""Build an audited child-utterance handoff spanning all prepared populations.

The handoff keeps naturalistic, structured, clinical/control, and Hall samples
explicitly labelled.  It contains real child targets only.  Context windows are
formed from prior caregiver turns in the same prepared session and never cross
session boundaries.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import tarfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence, TextIO

from build_age_word_dicts import iter_child_units
from create_shared_caretaker_contexts import iter_context_rows_for_unit


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs/cross_population_scoring_handoff.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/cross_population_scoring_handoff/full_20260826"
CLINICAL_METADATA = PROJECT_ROOT / "results/metadata/clinical_child_metadata_summary.csv"

OUTPUT_COLUMNS = (
    "dataset",
    "child_id",
    "child_key",
    "collection_id",
    "analysis_group",
    "population_class",
    "speech_setting",
    "clinical_group",
    "clinical_status",
    "is_control",
    "source_group",
    "session_id",
    "age_raw",
    "age_months",
    "sex",
    "file",
    "line_no",
    "reference_line",
    "utt_id",
    "utterance_id",
    "speaker_mode",
    "target_text",
    "context_k1",
    "context_k2",
    "context_k3",
    "context_k1_available",
    "context_k2_available",
    "context_k3_available",
    "primary_eligible",
    "sensitivity_eligible",
    "race",
    "social_class",
    "setting",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_id(*values: object) -> str:
    payload = "\x1f".join(str(value) for value in values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clean_cell(value: object) -> str:
    """Normalize scalar text without serializing pandas/numpy NA as `nan`."""
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


@contextmanager
def reproducible_gzip_text(path: Path) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                yield text


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def clinical_metadata_index(path: Path = CLINICAL_METADATA) -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv_rows(path)
    return {(row["clinical_dataset"], row["child_id"]): row for row in rows}


def normalized_standard_row(
    row: Mapping[str, object],
    *,
    dataset: str,
    child: str,
    collection: Mapping[str, object],
    clinical: Mapping[str, str] | None,
) -> dict[str, object]:
    target = clean_cell(row.get("utterance_clean", ""))
    reference = clean_cell(row.get("reference_line", ""))
    if not reference:
        reference = f"{clean_cell(row.get('file', ''))}:{clean_cell(row.get('line_no', ''))}"
    utterance_id = stable_id(dataset, child, reference, row.get("utt_id", ""))
    contexts = {f"context_k{k}": clean_cell(row.get(f"context_k{k}", "")) for k in (1, 2, 3)}
    return {
        "dataset": dataset,
        "child_id": child,
        "child_key": f"{dataset}/{child}",
        "collection_id": collection["collection_id"],
        "analysis_group": collection["analysis_group"],
        "population_class": collection["population_class"],
        "speech_setting": collection["speech_setting"],
        "clinical_group": "" if clinical is None else clinical.get("clinical_group", ""),
        "clinical_status": "not_clinical_corpus" if clinical is None else clinical.get("clinical_status", ""),
        "is_control": "" if clinical is None else clinical.get("is_control", ""),
        "source_group": row.get("source_group", ""),
        "session_id": row.get("session_id", ""),
        "age_raw": row.get("age_raw", ""),
        "age_months": row.get("age_months", ""),
        "sex": row.get("sex", ""),
        "file": row.get("file", ""),
        "line_no": row.get("line_no", ""),
        "reference_line": reference,
        "utt_id": row.get("utt_id", ""),
        "utterance_id": utterance_id,
        "speaker_mode": "real_child",
        "target_text": target,
        **contexts,
        **{f"context_k{k}_available": int(bool(contexts[f"context_k{k}"])) for k in (1, 2, 3)},
        "primary_eligible": 1,
        "sensitivity_eligible": 1,
        "race": "",
        "social_class": "",
        "setting": "",
    }


def iter_standard_dataset_rows(
    *,
    project_root: Path,
    collection: Mapping[str, object],
    dataset: str,
    clinical_index: Mapping[tuple[str, str], Mapping[str, str]],
) -> tuple[list[object], Iterator[dict[str, object]]]:
    prepared_root = project_root / str(collection["prepared_root"])
    units = iter_child_units(prepared_root, [dataset])

    def rows() -> Iterator[dict[str, object]]:
        for unit in units:
            clinical = clinical_index.get((dataset, unit.child))
            if collection["analysis_group"] == "clinical_and_matched_controls" and clinical is None:
                raise ValueError(f"clinical metadata missing for {dataset}/{unit.child}")
            for row in iter_context_rows_for_unit(unit, ks=(1, 2, 3)):
                if str(row.get("speaker_group", "")).strip() != "CHILD":
                    continue
                normalized = normalized_standard_row(
                    row,
                    dataset=dataset,
                    child=unit.child,
                    collection=collection,
                    clinical=clinical,
                )
                if normalized["target_text"]:
                    yield normalized

    return units, rows()


def iter_hall_rows(path: Path, hall: Mapping[str, object]) -> Iterator[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {
            "dataset", "child_id", "age_raw", "age_months", "sex", "file", "line_no",
            "utterance_id", "context_k1", "context_k2", "context_k3", "chi_utterance_clean",
            "primary_eligible", "sensitivity_eligible", "race", "social_class", "setting_auto",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Hall source missing columns: {sorted(missing)}")
        for source in reader:
            target = source["chi_utterance_clean"].strip()
            if not target:
                continue
            contexts = {f"context_k{k}": source[f"context_k{k}"].strip() for k in (1, 2, 3)}
            yield {
                "dataset": "Hall",
                "child_id": source["child_id"],
                "child_key": f"Hall/{source['child_id']}",
                "collection_id": hall["collection_id"],
                "analysis_group": hall["analysis_group"],
                "population_class": hall["population_class"],
                "speech_setting": hall["speech_setting"],
                "clinical_group": "",
                "clinical_status": "not_clinical_corpus",
                "is_control": "",
                "source_group": source.get("source_group", ""),
                "session_id": source.get("situation_id", ""),
                "age_raw": source["age_raw"],
                "age_months": source["age_months"],
                "sex": source["sex"],
                "file": source["file"],
                "line_no": source["line_no"],
                "reference_line": f"{source['file']}:{source['line_no']}",
                "utt_id": "",
                "utterance_id": source["utterance_id"],
                "speaker_mode": "real_child",
                "target_text": target,
                **contexts,
                **{f"context_k{k}_available": int(bool(contexts[f"context_k{k}"])) for k in (1, 2, 3)},
                "primary_eligible": source["primary_eligible"],
                "sensitivity_eligible": source["sensitivity_eligible"],
                "race": source["race"],
                "social_class": source["social_class"],
                "setting": source["setting_auto"],
            }


def write_dataset_input(
    path: Path,
    rows: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    counts: Counter[str] = Counter()
    children: set[str] = set()
    utterance_ids: set[str] = set()
    duplicate_ids = 0
    ages_missing = 0
    with reproducible_gzip_text(path) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            target = clean_cell(row.get("target_text", ""))
            if not target:
                continue
            utterance_id = str(row["utterance_id"])
            duplicate_ids += int(utterance_id in utterance_ids)
            utterance_ids.add(utterance_id)
            children.add(str(row["child_key"]))
            ages_missing += int(not clean_cell(row.get("age_months", "")))
            counts["rows"] += 1
            counts["primary_rows"] += int(str(row.get("primary_eligible", "0")) == "1")
            for k in (1, 2, 3):
                counts[f"context_k{k}_rows"] += int(bool(clean_cell(row.get(f"context_k{k}", ""))))
            writer.writerow({column: clean_cell(row.get(column, "")) for column in OUTPUT_COLUMNS})
    return {
        **counts,
        "children": len(children),
        "duplicate_utterance_ids": duplicate_ids,
        "missing_age_rows": ages_missing,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    config_path = config_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    project_root = project_root.expanduser().resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    package_id = str(config["package_id"])
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"fresh output directory required: {output_dir}")
    output_dir.mkdir(parents=True)
    inputs_dir = output_dir / "inputs"
    clinical_index = clinical_metadata_index(project_root / CLINICAL_METADATA.relative_to(PROJECT_ROOT))
    inventory: list[dict[str, object]] = []
    expected_collection_children: dict[str, int] = {}
    observed_collection_children: Counter[str] = Counter()

    for collection in config["collections"]:
        collection_id = str(collection["collection_id"])
        expected_collection_children[collection_id] = int(collection["expected_children"])
        for dataset in collection["datasets"]:
            units, rows = iter_standard_dataset_rows(
                project_root=project_root,
                collection=collection,
                dataset=dataset,
                clinical_index=clinical_index,
            )
            input_path = inputs_dir / f"{dataset}.child_scoring.csv.gz"
            stats = write_dataset_input(input_path, rows)
            if stats["duplicate_utterance_ids"]:
                raise ValueError(f"duplicate utterance IDs in {dataset}: {stats['duplicate_utterance_ids']}")
            if stats["rows"] < 1:
                raise ValueError(f"no non-empty child targets for {dataset}")
            observed_collection_children[collection_id] += len(units)
            inventory.append(
                {
                    "dataset": dataset,
                    "collection_id": collection_id,
                    "analysis_group": collection["analysis_group"],
                    "population_class": collection["population_class"],
                    "speech_setting": collection["speech_setting"],
                    "source_children": len(units),
                    "children": stats["children"],
                    "children_without_scoreable_targets": len(units) - int(stats["children"]),
                    **stats,
                    "input_relpath": input_path.relative_to(output_dir).as_posix(),
                }
            )

    hall = config["hall"]
    hall_path = project_root / hall["input_csv"]
    hall_input = inputs_dir / "Hall.child_scoring.csv.gz"
    hall_stats = write_dataset_input(hall_input, iter_hall_rows(hall_path, hall))
    if int(hall_stats["rows"]) != int(hall["expected_rows"]):
        raise ValueError(f"Hall row mismatch: {hall_stats['rows']} != {hall['expected_rows']}")
    if int(hall_stats["children"]) != int(hall["expected_children"]):
        raise ValueError(f"Hall child mismatch: {hall_stats['children']} != {hall['expected_children']}")
    inventory.append(
        {
            "dataset": "Hall",
            "collection_id": hall["collection_id"],
            "analysis_group": hall["analysis_group"],
            "population_class": hall["population_class"],
            "speech_setting": hall["speech_setting"],
            "source_children": hall_stats["children"],
            "children": hall_stats["children"],
            "children_without_scoreable_targets": 0,
            **hall_stats,
            "input_relpath": hall_input.relative_to(output_dir).as_posix(),
        }
    )

    collection_problems = []
    for collection_id, expected in expected_collection_children.items():
        observed = observed_collection_children[collection_id]
        if observed != expected:
            collection_problems.append(f"{collection_id}:expected={expected}:observed={observed}")
    if collection_problems:
        raise ValueError("collection child-count mismatch: " + "; ".join(collection_problems))

    contract_rows: list[dict[str, object]] = []
    for source in inventory:
        for context in config["contexts"]:
            context_col = "" if context == "k0" else f"context_{context}"
            context_rows = int(source["rows"] if context == "k0" else source[f"context_{context}_rows"])
            contract_rows.append(
                {
                    "dataset": source["dataset"],
                    "context_window": context,
                    "input_relpath": source["input_relpath"],
                    "target_column": "target_text",
                    "context_column": context_col,
                    "expected_input_rows": source["rows"],
                    "expected_nonempty_target_rows": source["rows"],
                    "expected_context_available_rows": context_rows,
                    "source_sha256": source["sha256"],
                }
            )

    reuse_cells = {
        (model, dataset)
        for item in config.get("reuse", [])
        for model in item["models"]
        for dataset in item["datasets"]
    }
    scoring_plan: list[dict[str, object]] = []
    for model in config["models"]:
        for source in inventory:
            dataset = str(source["dataset"])
            reused = (model["model_key"], dataset) in reuse_cells
            scoring_plan.append(
                {
                    "model_key": model["model_key"],
                    "model_id": model["model_id"],
                    "dataset": dataset,
                    "collection_id": source["collection_id"],
                    "children": source["children"],
                    "target_rows": source["rows"],
                    "contexts": ",".join(config["contexts"]),
                    "action": "REUSE_AUDITED" if reused else "SCORE_PENDING",
                }
            )

    inventory_path = output_dir / "dataset_inventory.csv"
    contracts_path = output_dir / "scoring_contracts_template.csv"
    plan_path = output_dir / "model_scoring_plan.csv"
    write_csv(inventory_path, inventory)
    write_csv(contracts_path, contract_rows)
    write_csv(plan_path, scoring_plan)
    totals = {
        "datasets": len(inventory),
        "children": sum(int(row["children"]) for row in inventory),
        "target_rows": sum(int(row["rows"]) for row in inventory),
        "primary_rows": sum(int(row["primary_rows"]) for row in inventory),
        "context_k1_rows": sum(int(row["context_k1_rows"]) for row in inventory),
        "context_k2_rows": sum(int(row["context_k2_rows"]) for row in inventory),
        "context_k3_rows": sum(int(row["context_k3_rows"]) for row in inventory),
        "contracts_per_model": len(contract_rows),
        "model_dataset_cells_pending": sum(row["action"] == "SCORE_PENDING" for row in scoring_plan),
        "model_dataset_cells_reused": sum(row["action"] == "REUSE_AUDITED" for row in scoring_plan),
    }
    audit = {
        "status": "PASS",
        "schema_version": config["schema_version"],
        "package_id": package_id,
        "totals": totals,
        "expected_collection_children": expected_collection_children,
        "observed_collection_children": dict(observed_collection_children),
        "hall_expected_primary_children": hall["expected_primary_children"],
        "inputs_with_duplicate_utterance_ids": sum(int(row["duplicate_utterance_ids"] > 0) for row in inventory),
    }
    audit_path = output_dir / "audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme = output_dir / "README.md"
    readme.write_text(
        "# Cross-population child scoring handoff\n\n"
        "This package contains real child utterances only, with k0-k3 caregiver-context contracts. "
        "Naturalistic, structured, clinical/control, and Hall samples remain explicitly labelled. "
        "Use within-corpus matched controls for primary clinical contrasts. Do not pool raw bits across scorers. "
        "Rows with unavailable caregiver context remain in the input but must be marked unavailable; they must not "
        "be silently interpreted as observed k0 rows.\n",
        encoding="utf-8",
    )
    manifest_files = [
        path for path in sorted(output_dir.rglob("*")) if path.is_file() and path.name not in {"handoff_manifest.json"}
    ]
    handoff_manifest = {
        "schema_version": config["schema_version"],
        "package_id": package_id,
        "audit_status": audit["status"],
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
    manifest_path.write_text(json.dumps(handoff_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    summary = build_handoff(
        config_path=args.config,
        output_dir=args.output_dir,
        build_archive=not args.no_archive,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
