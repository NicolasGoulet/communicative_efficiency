#!/usr/bin/env python3
"""Build an audited PBM-excluded child-response training handoff.

The output is architecture-neutral.  A causal LM and an encoder-decoder model
must consume the same ``context_turns`` and ``target_text`` fields so that a
model comparison cannot accidentally become a data comparison.

Brown, Manchester, and Providence (PBM) are written only to the evaluation
files.  They are forbidden from every training and validation file.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from collections import defaultdict
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, TextIO, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "transformer_training_expansion.json"
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data" / "preprocessed_data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "transformer_training_expansion" / "current"
PBM_DATASETS = ("Brown", "Manchester", "Providence")
EXPECTED_EXPANSION_CHILDREN = {
    "Howe": 16,
    "Tardif": 24,
    "Valian": 21,
    "Higginson": 3,
    "Edinburgh": 47,
    "Thomas": 1,
}
AUDIT_COLUMNS = [
    "dataset",
    "sample_role",
    "available",
    "expected_children",
    "child_folders",
    "chi_rows",
    "chi_nonempty",
    "caretaker_rows",
    "caretaker_nonempty",
    "missing_age_child_rows",
    "age_min_months",
    "age_max_months",
    "eligible_examples",
    "training_examples",
    "validation_examples",
    "issue",
]


@dataclass(frozen=True)
class PreparedUnit:
    """One Stage-0 child folder."""

    dataset: str
    child_id: str
    folder: Path
    chi_csv: Path
    caretakers_csv: Path


@dataclass
class DatasetAudit:
    """Mutable counters for one requested corpus."""

    dataset: str
    sample_role: str
    expected_children: Optional[int] = None
    child_folders: int = 0
    chi_rows: int = 0
    chi_nonempty: int = 0
    caretaker_rows: int = 0
    caretaker_nonempty: int = 0
    missing_age_child_rows: int = 0
    age_min_months: Optional[float] = None
    age_max_months: Optional[float] = None
    eligible_examples: int = 0
    training_examples: int = 0
    validation_examples: int = 0
    issues: List[str] | None = None

    def __post_init__(self) -> None:
        if self.issues is None:
            self.issues = []

    def update_age(self, age: Optional[float]) -> None:
        if age is None:
            return
        self.age_min_months = age if self.age_min_months is None else min(self.age_min_months, age)
        self.age_max_months = age if self.age_max_months is None else max(self.age_max_months, age)

    def as_row(self) -> Dict[str, object]:
        available = self.child_folders > 0
        return {
            "dataset": self.dataset,
            "sample_role": self.sample_role,
            "available": int(available),
            "expected_children": self.expected_children if self.expected_children is not None else "",
            "child_folders": self.child_folders,
            "chi_rows": self.chi_rows,
            "chi_nonempty": self.chi_nonempty,
            "caretaker_rows": self.caretaker_rows,
            "caretaker_nonempty": self.caretaker_nonempty,
            "missing_age_child_rows": self.missing_age_child_rows,
            "age_min_months": "" if self.age_min_months is None else round(self.age_min_months, 3),
            "age_max_months": "" if self.age_max_months is None else round(self.age_max_months, 3),
            "eligible_examples": self.eligible_examples,
            "training_examples": self.training_examples,
            "validation_examples": self.validation_examples,
            "issue": "; ".join(self.issues or []),
        }


def load_config(path: Path) -> Dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return config


def age_bins_from_config(config: Mapping[str, object]) -> List[Tuple[int, int]]:
    bins = [(int(pair[0]), int(pair[1])) for pair in config["age_bins"]]  # type: ignore[index]
    if not bins or any(start > end for start, end in bins):
        raise ValueError("Invalid age_bins in training-expansion config")
    if any(left[1] + 1 != right[0] for left, right in zip(bins, bins[1:])):
        raise ValueError("Configured age bins must be contiguous")
    return bins


def age_bin_label(start: int, end: int) -> str:
    return f"{start:03d}-{end:03d}"


def floor_age(value: object) -> Optional[int]:
    try:
        age = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(age):
        return None
    return math.floor(age)


def discover_units(data_root: Path, datasets: Sequence[str]) -> List[PreparedUnit]:
    units: List[PreparedUnit] = []
    for dataset in datasets:
        dataset_dir = data_root / dataset
        for chi_csv in sorted(dataset_dir.glob("*/chi.csv")):
            folder = chi_csv.parent
            units.append(
                PreparedUnit(
                    dataset=dataset,
                    child_id=folder.name,
                    folder=folder,
                    chi_csv=chi_csv,
                    caretakers_csv=folder / "caretakers.csv",
                )
            )
    return units


def stable_fraction(seed: int, dataset: str, child_id: str) -> float:
    digest = hashlib.sha256(f"{seed}\0{dataset}\0{child_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def select_validation_units(
    units: Sequence[PreparedUnit], *, fraction: float, seed: int
) -> set[Tuple[str, str]]:
    """Select whole child units, never rows or sessions, for validation."""
    if not 0 <= fraction < 1:
        raise ValueError("validation fraction must be in [0, 1)")
    by_dataset: Dict[str, List[PreparedUnit]] = defaultdict(list)
    for unit in units:
        by_dataset[unit.dataset].append(unit)

    selected: set[Tuple[str, str]] = set()
    for dataset, dataset_units in sorted(by_dataset.items()):
        if fraction == 0 or len(dataset_units) < 2:
            continue
        count = max(1, min(len(dataset_units) - 1, round(len(dataset_units) * fraction)))
        ranked = sorted(
            dataset_units,
            key=lambda unit: (stable_fraction(seed, unit.dataset, unit.child_id), unit.child_id),
        )
        selected.update((unit.dataset, unit.child_id) for unit in ranked[:count])
    return selected


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"session_id", "file", "line_no", "utterance_clean", "age_months"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing Stage-0 columns: {sorted(missing)}")
        return list(reader)


def integer_sort_value(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return -1


def normalized_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def conversation_sort_key(row: Mapping[str, object]) -> Tuple[int, str, int, int, int]:
    return (
        integer_sort_value(row.get("session_id")),
        str(row.get("file", "")),
        integer_sort_value(row.get("line_no")),
        integer_sort_value(row.get("utt_id")),
        0 if row.get("_role") == "CARETAKER" else 1,
    )


def iter_examples(
    unit: PreparedUnit,
    *,
    context_utterances: int,
    max_context_tokens: int,
    age_bins: Sequence[Tuple[int, int]],
) -> Iterator[Dict[str, object]]:
    """Yield eligible child targets with preceding caretaker-turn context."""
    child_rows = [dict(row, _role="CHI") for row in read_csv_rows(unit.chi_csv)]
    caretaker_rows = [dict(row, _role="CARETAKER") for row in read_csv_rows(unit.caretakers_csv)]
    combined = sorted([*child_rows, *caretaker_rows], key=conversation_sort_key)
    history_by_session: Dict[str, List[str]] = defaultdict(list)

    for row in combined:
        session = str(row.get("session_id", ""))
        text = normalized_text(row.get("utterance_clean"))
        if row["_role"] == "CARETAKER":
            if text:
                history_by_session[session].append(text)
            continue
        if not text:
            continue

        month = floor_age(row.get("age_months"))
        if month is None:
            continue
        matching = [(start, end) for start, end in age_bins if start <= month <= end]
        if not matching:
            continue
        start, end = matching[0]
        turns = list(history_by_session.get(session, [])[-context_utterances:])
        if max_context_tokens > 0 and turns:
            tokens_remaining = max_context_tokens
            clipped_reversed: List[str] = []
            for turn in reversed(turns):
                tokens = turn.split()
                if tokens_remaining <= 0:
                    break
                kept = tokens[-tokens_remaining:]
                clipped_reversed.append(" ".join(kept))
                tokens_remaining -= len(kept)
            turns = list(reversed(clipped_reversed))

        reference_line = str(row.get("reference_line") or f"{row.get('file', '')}:{row.get('line_no', '')}")
        identity = f"{unit.dataset}\0{unit.child_id}\0{reference_line}"
        context_text = " <turn> ".join(turns)
        yield {
            "example_id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24],
            "dataset": unit.dataset,
            "child_id": unit.child_id,
            "session_id": str(row.get("session_id", "")),
            "file": str(row.get("file", "")),
            "line_no": integer_sort_value(row.get("line_no")),
            "reference_line": reference_line,
            "age_months": float(str(row["age_months"])),
            "age_floor_month": month,
            "target_age_bin": age_bin_label(start, end),
            "speaker": "CHI",
            "context_turns": turns,
            "context_text": context_text,
            "context_turn_count": len(turns),
            "context_word_count": len(context_text.replace("<turn>", "").split()),
            "target_text": text,
            "target_word_count": len(text.split()),
        }


def write_json_line(handle: TextIO, row: Mapping[str, object]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


@contextmanager
def reproducible_gzip_text(path: Path) -> Iterator[TextIO]:
    """Write gzip text without a wall-clock timestamp in the gzip header."""
    with path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
            with io.TextIOWrapper(gzip_handle, encoding="utf-8", newline="") as text_handle:
                yield text_handle


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_row_counts(unit: PreparedUnit, audit: DatasetAudit) -> None:
    child_rows = read_csv_rows(unit.chi_csv)
    caretaker_rows = read_csv_rows(unit.caretakers_csv)
    audit.chi_rows += len(child_rows)
    audit.caretaker_rows += len(caretaker_rows)
    for row in child_rows:
        if normalized_text(row.get("utterance_clean")):
            audit.chi_nonempty += 1
        age_text = str(row.get("age_months", "")).strip()
        if not age_text:
            audit.missing_age_child_rows += 1
        else:
            try:
                audit.update_age(float(age_text))
            except ValueError:
                audit.missing_age_child_rows += 1
    audit.caretaker_nonempty += sum(
        bool(normalized_text(row.get("utterance_clean"))) for row in caretaker_rows
    )


def build_handoff(
    *,
    config_path: Path,
    data_root: Path,
    output_dir: Path,
    validation_fraction: float,
    seed: int,
) -> Dict[str, object]:
    config = load_config(config_path)
    existing = [str(value) for value in config["training_datasets_existing"]]  # type: ignore[index]
    expansion = [str(value) for value in config["training_datasets_expansion"]]  # type: ignore[index]
    evaluation = [str(value) for value in config["held_out_evaluation_datasets"]]  # type: ignore[index]
    if set(existing + expansion) & set(evaluation):
        raise RuntimeError("PBM leakage: at least one dataset is assigned to both training and evaluation")
    if tuple(evaluation) != PBM_DATASETS:
        raise RuntimeError(f"Held-out evaluation must be exactly PBM: {PBM_DATASETS}")

    bins = age_bins_from_config(config)
    context_utterances = int(config["context_utterances"])
    max_context_tokens = int(config["max_context_tokens"])
    training_datasets = [*existing, *expansion]
    training_units = discover_units(data_root, training_datasets)
    evaluation_units = discover_units(data_root, evaluation)
    validation_units = select_validation_units(training_units, fraction=validation_fraction, seed=seed)

    output_dir.mkdir(parents=True, exist_ok=False)
    examples_dir = output_dir / "examples"
    cumulative_dir = output_dir / "cumulative_age_models"
    target_dir = output_dir / "pbm_target_age_bins"
    examples_dir.mkdir(parents=True)
    cumulative_dir.mkdir(parents=True)
    target_dir.mkdir(parents=True)

    audits: Dict[str, DatasetAudit] = {}
    for dataset in training_datasets:
        audits[dataset] = DatasetAudit(
            dataset=dataset,
            sample_role="training_expansion" if dataset in expansion else "existing_non_pbm_training",
            expected_children=EXPECTED_EXPANSION_CHILDREN.get(dataset),
        )
    for dataset in evaluation:
        audits[dataset] = DatasetAudit(dataset=dataset, sample_role="held_out_pbm_evaluation")

    for unit in [*training_units, *evaluation_units]:
        audits[unit.dataset].child_folders += 1
        source_row_counts(unit, audits[unit.dataset])
    for audit in audits.values():
        if audit.child_folders == 0:
            audit.issues.append("missing Stage-0 corpus")
        if audit.expected_children is not None and audit.child_folders != audit.expected_children:
            audit.issues.append(
                f"expected {audit.expected_children} children, found {audit.child_folders}"
            )

    cumulative_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    target_counts: Dict[str, int] = defaultdict(int)
    output_paths: List[Path] = []
    with ExitStack() as stack:
        train_all_path = examples_dir / "train_all_ages.jsonl.gz"
        validation_all_path = examples_dir / "validation_all_ages.jsonl.gz"
        development_all_path = examples_dir / "development_all_ages.jsonl.gz"
        evaluation_all_path = examples_dir / "pbm_evaluation_all_ages.jsonl.gz"
        train_all = stack.enter_context(reproducible_gzip_text(train_all_path))
        validation_all = stack.enter_context(reproducible_gzip_text(validation_all_path))
        development_all = stack.enter_context(reproducible_gzip_text(development_all_path))
        evaluation_all = stack.enter_context(reproducible_gzip_text(evaluation_all_path))
        output_paths.extend([train_all_path, validation_all_path, development_all_path, evaluation_all_path])

        cumulative_handles: Dict[Tuple[str, str], TextIO] = {}
        for start, end in bins:
            label = age_bin_label(start, end)
            bin_dir = cumulative_dir / f"through_{end:03d}_months"
            bin_dir.mkdir()
            for split in ("train", "validation", "development"):
                path = bin_dir / f"{split}.jsonl.gz"
                cumulative_handles[(label, split)] = stack.enter_context(reproducible_gzip_text(path))
                output_paths.append(path)

        target_handles: Dict[str, TextIO] = {}
        for start, end in bins:
            label = age_bin_label(start, end)
            path = target_dir / f"pbm_{label}.jsonl.gz"
            target_handles[label] = stack.enter_context(reproducible_gzip_text(path))
            output_paths.append(path)

        for unit in training_units:
            split = "validation" if (unit.dataset, unit.child_id) in validation_units else "train"
            for example in iter_examples(
                unit,
                context_utterances=context_utterances,
                max_context_tokens=max_context_tokens,
                age_bins=bins,
            ):
                example["split"] = split
                write_json_line(validation_all if split == "validation" else train_all, example)
                write_json_line(development_all, example)
                audit = audits[unit.dataset]
                audit.eligible_examples += 1
                if split == "validation":
                    audit.validation_examples += 1
                else:
                    audit.training_examples += 1
                month = int(example["age_floor_month"])
                for start, end in bins:
                    if bins[0][0] <= month <= end:
                        label = age_bin_label(start, end)
                        write_json_line(cumulative_handles[(label, split)], example)
                        write_json_line(cumulative_handles[(label, "development")], example)
                        cumulative_counts[(label, split)] += 1
                        cumulative_counts[(label, "development")] += 1

        for unit in evaluation_units:
            for example in iter_examples(
                unit,
                context_utterances=context_utterances,
                max_context_tokens=max_context_tokens,
                age_bins=bins,
            ):
                example["split"] = "held_out_pbm_evaluation"
                write_json_line(evaluation_all, example)
                label = str(example["target_age_bin"])
                write_json_line(target_handles[label], example)
                audits[unit.dataset].eligible_examples += 1
                target_counts[label] += 1

    validation_rows = [
        {"dataset": dataset, "child_id": child_id, "split": "validation", "selection_seed": seed}
        for dataset, child_id in sorted(validation_units)
    ]
    write_csv(
        output_dir / "validation_children.csv",
        ["dataset", "child_id", "split", "selection_seed"],
        validation_rows,
    )
    write_csv(output_dir / "dataset_audit.csv", AUDIT_COLUMNS, [audit.as_row() for audit in audits.values()])

    schedule_rows: List[Dict[str, object]] = []
    for start, end in bins:
        label = age_bin_label(start, end)
        schedule_rows.append(
            {
                "target_age_bin": label,
                "cumulative_min_month": bins[0][0],
                "cumulative_max_month": end,
                "train_examples": cumulative_counts[(label, "train")],
                "validation_examples": cumulative_counts[(label, "validation")],
                "development_examples": cumulative_counts[(label, "development")],
                "pbm_target_examples": target_counts[label],
                "train_file": f"cumulative_age_models/through_{end:03d}_months/train.jsonl.gz",
                "validation_file": f"cumulative_age_models/through_{end:03d}_months/validation.jsonl.gz",
                "final_refit_file": f"cumulative_age_models/through_{end:03d}_months/development.jsonl.gz",
                "pbm_evaluation_file": f"pbm_target_age_bins/pbm_{label}.jsonl.gz",
            }
        )
    schedule_columns = [
        "target_age_bin",
        "cumulative_min_month",
        "cumulative_max_month",
        "train_examples",
        "validation_examples",
        "development_examples",
        "pbm_target_examples",
        "train_file",
        "validation_file",
        "final_refit_file",
        "pbm_evaluation_file",
    ]
    write_csv(output_dir / "age_model_schedule.csv", schedule_columns, schedule_rows)

    missing_expansion = [dataset for dataset in expansion if audits[dataset].child_folders == 0]
    pbm_in_training_files = set(training_datasets) & set(PBM_DATASETS)
    fatal_issues = [
        f"{audit.dataset}: {issue}"
        for audit in audits.values()
        for issue in (audit.issues or [])
        if audit.dataset not in missing_expansion
    ]
    if pbm_in_training_files:
        fatal_issues.append(f"PBM datasets assigned to training: {sorted(pbm_in_training_files)}")

    checksums = {str(path.relative_to(output_dir)): sha256_file(path) for path in sorted(output_paths)}
    status = "complete" if not missing_expansion and not fatal_issues else "partial"
    manifest = {
        "status": status,
        "config": str(config_path),
        "data_root": str(data_root),
        "training_datasets_requested": training_datasets,
        "training_datasets_available": sorted({unit.dataset for unit in training_units}),
        "held_out_evaluation_datasets": evaluation,
        "missing_expansion_datasets": missing_expansion,
        "fatal_issues": fatal_issues,
        "pbm_dataset_overlap_with_training": sorted(pbm_in_training_files),
        "validation_split_unit": "whole child within each training corpus",
        "final_refit_policy": "After architecture/hyperparameter selection, refit each age model on its development file (train plus validation) before PBM generation.",
        "validation_fraction": validation_fraction,
        "validation_seed": seed,
        "context_utterances": context_utterances,
        "max_context_tokens": max_context_tokens,
        "age_bins": [age_bin_label(start, end) for start, end in bins],
        "training_examples": sum(audit.training_examples for audit in audits.values()),
        "validation_examples": sum(audit.validation_examples for audit in audits.values()),
        "pbm_evaluation_examples": sum(audits[dataset].eligible_examples for dataset in evaluation),
        "output_sha256": checksums,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    marker = "BUILD_COMPLETE_AND_AUDITED" if status == "complete" else "BUILD_PARTIAL_MISSING_AUTHENTICATED_CORPORA"
    (output_dir / marker).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--validation-fraction", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=20260825)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    manifest = build_handoff(
        config_path=args.config.resolve(),
        data_root=args.data_root.resolve(),
        output_dir=args.output_dir.resolve(),
        validation_fraction=args.validation_fraction,
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
