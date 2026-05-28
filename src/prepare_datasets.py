#!/usr/bin/env python3
"""
Prepare raw CHAT transcripts into simple raw/cleaned CSV files.

Goal
----
This is the maintainable Stage 0 preprocessing entry point. It keeps the useful
corpus traversal skeleton from the older prepare_datasets.py, but delegates all
utterance cleaning to cleaning.py so there is one cleaning policy to test.

Normal output for each child/session group:
- chi.csv: CHI utterances only.
- caretakers.csv: MOT and FAT utterances in CHAT order.

Testing output:
- When --testing is passed, also write testing.csv with CHI, MOT, and FAT rows
  together in CHAT order. This is for quick human inspection of raw vs cleaned
  output.

This script intentionally does not compute word counts, syllables, morphemes,
contexts, generated utterances, or scoring inputs.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from cleaning import DEFAULT_SPEAKERS, iter_cleaned_chat_rows


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DATASETS = (
    "Brown",
    "Manchester",
    "Providence",
    "Hall",
    "MPI-EVA-Manchester",
    "Belfast",
    "Wells",
    "Champaign",
    "EHS",
    "Cummings",
    "Lara",
    "Sachs",
    "Weist",
    "Kuczaj",
    "Post",
    "Demetras1",
    "Forrester",
)

DEFAULT_RAW_ROOTS = {
    "Brown": [
        PROJECT_ROOT / "data" / "raw_data" / "Brown",
        PROJECT_ROOT / "data" / "Brown",
        Path.cwd() / "data" / "raw_data" / "Brown",
        Path.cwd() / "data" / "Brown",
    ],
    "Manchester": [
        PROJECT_ROOT / "data" / "raw_data" / "Manchester",
        PROJECT_ROOT / "data" / "Manchester",
        Path.cwd() / "data" / "raw_data" / "Manchester",
        Path.cwd() / "data" / "Manchester",
    ],
    "Providence": [
        PROJECT_ROOT / "data" / "raw_data" / "Providence",
        PROJECT_ROOT / "data" / "Providence",
        Path.cwd() / "data" / "raw_data" / "Providence",
        Path.cwd() / "data" / "Providence",
    ],
    "Hall": [
        PROJECT_ROOT / "data" / "raw_data" / "Hall",
        Path.cwd() / "data" / "raw_data" / "Hall",
    ],
    "MPI-EVA-Manchester": [
        PROJECT_ROOT / "data" / "raw_data" / "MPI-EVA-Manchester",
        PROJECT_ROOT / "data" / "MPI-EVA-Manchester",
        Path.cwd() / "data" / "raw_data" / "MPI-EVA-Manchester",
        Path.cwd() / "data" / "MPI-EVA-Manchester",
    ],
    "Belfast": [
        PROJECT_ROOT / "data" / "raw_data" / "Belfast",
        PROJECT_ROOT / "data" / "Belfast",
        Path.cwd() / "data" / "raw_data" / "Belfast",
        Path.cwd() / "data" / "Belfast",
    ],
    "Wells": [
        PROJECT_ROOT / "data" / "raw_data" / "Wells",
        PROJECT_ROOT / "data" / "Wells",
        Path.cwd() / "data" / "raw_data" / "Wells",
        Path.cwd() / "data" / "Wells",
    ],
    "Champaign": [
        PROJECT_ROOT / "data" / "raw_data" / "Champaign",
        PROJECT_ROOT / "data" / "Champaign",
        Path.cwd() / "data" / "raw_data" / "Champaign",
        Path.cwd() / "data" / "Champaign",
    ],
    "EHS": [
        PROJECT_ROOT / "data" / "raw_data" / "EHS",
        PROJECT_ROOT / "data" / "EHS",
        Path.cwd() / "data" / "raw_data" / "EHS",
        Path.cwd() / "data" / "EHS",
    ],
    "Cummings": [
        PROJECT_ROOT / "data" / "raw_data" / "Cummings",
        PROJECT_ROOT / "data" / "Cummings",
        Path.cwd() / "data" / "raw_data" / "Cummings",
        Path.cwd() / "data" / "Cummings",
    ],
    "Lara": [
        PROJECT_ROOT / "data" / "raw_data" / "Lara",
        PROJECT_ROOT / "data" / "Lara",
        Path.cwd() / "data" / "raw_data" / "Lara",
        Path.cwd() / "data" / "Lara",
    ],
    "Sachs": [
        PROJECT_ROOT / "data" / "raw_data" / "Sachs",
        PROJECT_ROOT / "data" / "Sachs",
        Path.cwd() / "data" / "raw_data" / "Sachs",
        Path.cwd() / "data" / "Sachs",
    ],
    "Weist": [
        PROJECT_ROOT / "data" / "raw_data" / "Weist",
        PROJECT_ROOT / "data" / "Weist",
        Path.cwd() / "data" / "raw_data" / "Weist",
        Path.cwd() / "data" / "Weist",
    ],
    "Kuczaj": [
        PROJECT_ROOT / "data" / "raw_data" / "Kuczaj",
        PROJECT_ROOT / "data" / "Kuczaj",
        Path.cwd() / "data" / "raw_data" / "Kuczaj",
        Path.cwd() / "data" / "Kuczaj",
    ],
    "Post": [
        PROJECT_ROOT / "data" / "raw_data" / "Post",
        PROJECT_ROOT / "data" / "Post",
        Path.cwd() / "data" / "raw_data" / "Post",
        Path.cwd() / "data" / "Post",
    ],
    "Demetras1": [
        PROJECT_ROOT / "data" / "raw_data" / "Demetras1",
        PROJECT_ROOT / "data" / "Demetras1",
        Path.cwd() / "data" / "raw_data" / "Demetras1",
        Path.cwd() / "data" / "Demetras1",
    ],
    "Forrester": [
        PROJECT_ROOT / "data" / "raw_data" / "Forrester",
        PROJECT_ROOT / "data" / "Forrester",
        Path.cwd() / "data" / "raw_data" / "Forrester",
        Path.cwd() / "data" / "Forrester",
    ],
}

ROOT_DIRECT_CHILD_IDS = {
    "Lara": "Lara",
    "Sachs": "Naomi",
    "Kuczaj": "Abe",
    "Demetras1": "Trevor",
    "Forrester": "Ella",
}

DEFAULT_CARETAKER_SPEAKERS = ("MOT", "FAT")
CARETAKER_SPEAKERS_BY_DATASET = {
    # Lara includes a grandmother speaker (`ELS`) as a primary caregiver in
    # many recordings; keep her with caretakers rather than losing that context.
    "Lara": ("MOT", "FAT", "ELS"),
}

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "preprocessed_data"

PREPARED_CHAT_COLUMNS = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_raw",
    "age_months",
    "sex",
    "file",
    "line_no",
    "reference_line",
    "utt_id",
    "utt_id_role",
    "speaker",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
]

CHI_ID_RE = re.compile(r"^@ID:\s*[^|]*\|[^|]*\|CHI\|([^|]*)\|([^|]*)\|", re.IGNORECASE)
FILENAME_AGE_RE = re.compile(r"^(?P<years>\d{2})(?P<months>\d{2})(?P<days>\d{2})(?:[a-z])?$", re.IGNORECASE)
PARENT_MONTH_AGE_RE = re.compile(r"^(?P<months>\d{2})(?:[-_a-z]+)$", re.IGNORECASE)
COMMENT_AGE_RE = re.compile(r"^@Comment:\s*age\s+is\s+(.+?)\s*$", re.IGNORECASE)
COMMENT_SEX_RE = re.compile(r"^@Comment:\s*sex\s+is\s+(.+?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class ChatUnit:
    """
    A group of CHAT files that should become one prepared child directory.

    Goal: represent the only unit prepare_datasets.py writes: one child-like
    folder containing chi.csv, caretakers.csv, and optionally testing.csv.
    """

    child_id: str
    files: List[Path]
    base_dir: Path
    dataset: str = ""
    source_group: str = ""


def age_str_to_months(age: str) -> Optional[float]:
    """
    Convert a CHILDES age string like 5;00.16 into months.

    Goal: preserve a lightweight age field without pulling the old heavy
    metadata machinery back into this preprocessing stage.
    """
    if not age:
        return None

    match = re.match(r"^\s*(\d+)\s*;\s*(\d{1,2})(?:\.(\d{0,2}))?\s*\.?\s*$", age)
    if not match:
        return None

    years = int(match.group(1))
    months = int(match.group(2))
    days_text = match.group(3) or ""
    days = int(days_text) if days_text.isdigit() else 0
    return round((years * 12) + months + (days / 30.0), 3)


def age_from_filename_stem(cha_path: Path) -> Tuple[str, Optional[float]]:
    """
    Infer a CHILDES-style age string from filename stems like 030400 or 020500b.

    Goal: MPI-EVA-Manchester has some files where the CHI @ID age is blank but
    the filename encodes the recording age as YYMMDD, optionally followed by a
    session letter. This keeps those sessions usable in age-bin analyses without
    changing the raw CHAT files.
    """
    match = FILENAME_AGE_RE.match(cha_path.stem)
    if not match:
        return "", None

    years = int(match.group("years"))
    months = int(match.group("months"))
    days = int(match.group("days"))

    if months > 11 or days > 31:
        return "", None

    age_raw = f"{years};{months:02d}.{days:02d}"
    return age_raw, age_str_to_months(age_raw)


def age_from_parent_month_dir(cha_path: Path) -> Tuple[str, Optional[float]]:
    """
    Infer a CHILDES-style age from parent folders like 21P or 30X.

    Goal: Champaign groups files under nominal measurement/context folders. A
    few transcripts have blank CHI @ID age, so the parent directory gives the
    best available age-bin value.
    """
    match = PARENT_MONTH_AGE_RE.match(cha_path.parent.name)
    if not match:
        return "", None

    total_months = int(match.group("months"))
    years, months = divmod(total_months, 12)
    age_raw = f"{years};{months:02d}.00"
    return age_raw, float(total_months)


def read_session_metadata(cha_path: Path) -> Dict[str, object]:
    """
    Read only the CHI age and sex metadata from one CHAT file.

    Goal: add basic provenance columns to output rows while ignoring dependent
    tiers and avoiding scientific measures that belong in later pipeline steps.
    """
    age_raw = ""
    sex = ""
    comment_age_raw = ""
    comment_sex = ""

    with cha_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("*"):
                break
            if line.startswith("@ID:") and "|CHI|" in line:
                match = CHI_ID_RE.match(line)
                if match:
                    age_raw = match.group(1).strip()
                    sex = match.group(2).strip()
                continue
            age_match = COMMENT_AGE_RE.match(line)
            if age_match and not comment_age_raw:
                comment_age_raw = age_match.group(1).strip()
            sex_match = COMMENT_SEX_RE.match(line)
            if sex_match and not comment_sex:
                comment_sex = sex_match.group(1).strip()

    if not age_raw:
        age_raw = comment_age_raw
    if not sex:
        sex = comment_sex
    if not age_raw:
        age_raw, _ = age_from_filename_stem(cha_path)
    if not age_raw:
        age_raw, _ = age_from_parent_month_dir(cha_path)

    return {
        "age_raw": age_raw,
        "age_months": age_str_to_months(age_raw),
        "sex": sex,
    }


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    """
    Write prepared rows using the stable Stage 0 schema.

    Goal: make chi.csv, caretakers.csv, and testing.csv share exactly the same
    columns so files can be compared directly.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=PREPARED_CHAT_COLUMNS,
            quoting=csv.QUOTE_NONNUMERIC,
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: "" if row.get(column) is None else row.get(column) for column in PREPARED_CHAT_COLUMNS})


def resolve_base_dir(dataset: str, base_override: Optional[Path]) -> Path:
    """
    Resolve the raw-data directory for a known dataset.

    Goal: keep the old convenient --dataset interface while preferring the
    current data/raw_data layout.
    """
    if base_override is not None:
        return base_override.expanduser().resolve()

    for candidate in DEFAULT_RAW_ROOTS[dataset]:
        if candidate.exists():
            return candidate.resolve()

    return DEFAULT_RAW_ROOTS[dataset][0].resolve()


def _files_directly_under(path: Path) -> List[Path]:
    """Return sorted direct .cha children for a directory."""
    return sorted(p for p in path.glob("*.cha") if p.is_file())


def discover_input_units(input_path: Path) -> List[ChatUnit]:
    """
    Discover child-like units from a standalone CHAT file or arbitrary directory.

    Goal: support quick fixture/debug runs without requiring the full corpus
    directory layout.
    """
    input_path = input_path.expanduser().resolve()
    if input_path.is_file():
        return [
            ChatUnit(
                child_id=input_path.stem,
                files=[input_path],
                base_dir=input_path.parent,
            )
        ]

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    direct_files = _files_directly_under(input_path)
    if direct_files:
        return [
            ChatUnit(
                child_id=input_path.name,
                files=direct_files,
                base_dir=input_path,
            )
        ]

    units: List[ChatUnit] = []
    for child_dir in sorted(p for p in input_path.iterdir() if p.is_dir()):
        files = _files_directly_under(child_dir)
        if files:
            units.append(ChatUnit(child_id=child_dir.name, files=files, base_dir=input_path))

    if units:
        return units

    raise FileNotFoundError(f"No .cha files found under {input_path}")


def discover_dataset_units(dataset: str, base_dir: Path) -> List[ChatUnit]:
    """
    Discover child-like units for a known corpus layout.

    Goal: keep the old corpus convenience while emitting the new simple output
    files. Hall is handled as one child per .cha file; other corpora are handled
    as one child directory containing one or more .cha sessions.
    """
    if dataset == "Hall":
        units: List[ChatUnit] = []
        seen: Dict[str, int] = {}
        for group_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
            files = _files_directly_under(group_dir)
            for cha_path in files:
                base_child_id = cha_path.stem
                seen[base_child_id] = seen.get(base_child_id, 0) + 1
                child_id = base_child_id if seen[base_child_id] == 1 else f"{base_child_id}_{group_dir.name}"
                units.append(
                    ChatUnit(
                        child_id=child_id,
                        files=[cha_path],
                        base_dir=base_dir,
                        dataset=dataset,
                        source_group=group_dir.name,
                    )
                )
        return units

    if dataset in {"Champaign", "EHS"}:
        files_by_child: Dict[str, List[Path]] = defaultdict(list)
        for measurement_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
            for cha_path in _files_directly_under(measurement_dir):
                files_by_child[cha_path.stem].append(cha_path)
        return [
            ChatUnit(
                child_id=child_id,
                files=sorted(files),
                base_dir=base_dir,
                dataset=dataset,
                source_group=dataset,
            )
            for child_id, files in sorted(files_by_child.items())
        ]

    direct_files = _files_directly_under(base_dir)
    if direct_files:
        return [
            ChatUnit(
                child_id=ROOT_DIRECT_CHILD_IDS.get(dataset, dataset),
                files=direct_files,
                base_dir=base_dir,
                dataset=dataset,
                source_group=dataset,
            )
        ]

    return [
        ChatUnit(
            child_id=child_dir.name,
            files=_files_directly_under(child_dir),
            base_dir=base_dir,
            dataset=dataset,
            source_group=dataset,
        )
        for child_dir in sorted(p for p in base_dir.iterdir() if p.is_dir())
        if _files_directly_under(child_dir)
    ]


def caretaker_speakers_for_unit(unit: ChatUnit) -> Tuple[str, ...]:
    """Return the CHAT speaker tiers that count as caretakers for one unit."""
    return CARETAKER_SPEAKERS_BY_DATASET.get(unit.dataset, DEFAULT_CARETAKER_SPEAKERS)


def prepared_rows_for_unit(unit: ChatUnit) -> List[Dict[str, object]]:
    """
    Build all prepared CHI/MOT/FAT rows for one child-like unit.

    Goal: enrich the raw/cleaned rows produced by cleaning.py with stable
    provenance columns and role-order identifiers, without changing the cleaning
    policy here.
    """
    rows: List[Dict[str, object]] = []
    speakers = ("CHI", *caretaker_speakers_for_unit(unit))
    role_counts = {speaker: 0 for speaker in speakers}

    for session_id, cha_path in enumerate(sorted(unit.files), start=1):
        metadata = read_session_metadata(cha_path)
        for raw_row in iter_cleaned_chat_rows(cha_path, base_dir=unit.base_dir, speakers=speakers):
            speaker = str(raw_row["speaker"])
            reference_line = f"{raw_row['file']}:{raw_row['line_no']}"
            role_counts[speaker] += 1
            rows.append(
                {
                    "dataset": unit.dataset,
                    "child_id": unit.child_id,
                    "source_group": unit.source_group,
                    "session_id": session_id,
                    "age_raw": metadata["age_raw"],
                    "age_months": metadata["age_months"],
                    "sex": metadata["sex"],
                    "file": raw_row["file"],
                    "line_no": raw_row["line_no"],
                    "reference_line": reference_line,
                    "utt_id": len(rows) + 1,
                    "utt_id_role": role_counts[speaker],
                    "speaker": speaker,
                    "utterance": raw_row["utterance"],
                    "utterance_clean": raw_row["utterance_clean"],
                    "cleaned_is_empty": raw_row["cleaned_is_empty"],
                }
            )

    return rows


def _subset_rows(rows: Sequence[Dict[str, object]], speakers: Iterable[str]) -> List[Dict[str, object]]:
    """
    Return rows for one output file and renumber utt_id within that file.

    Goal: make chi.csv and caretakers.csv each have simple sequential utt_id
    values while keeping utt_id_role as the per-speaker identifier.
    """
    speaker_set = set(speakers)
    selected: List[Dict[str, object]] = []
    for source_row in rows:
        if source_row["speaker"] not in speaker_set:
            continue
        row = dict(source_row)
        row["utt_id"] = len(selected) + 1
        selected.append(row)
    return selected


def write_prepared_unit(output_dir: Path, unit: ChatUnit, testing: bool = False) -> int:
    """
    Write chi.csv, caretakers.csv, and optionally testing.csv for one unit.

    Goal: keep the file contract obvious and small. The testing CSV mirrors the
    fixture-style combined view requested for manual checking.
    """
    rows = prepared_rows_for_unit(unit)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(output_dir / "chi.csv", _subset_rows(rows, ("CHI",)))
    write_csv(output_dir / "caretakers.csv", _subset_rows(rows, caretaker_speakers_for_unit(unit)))

    if testing:
        testing_rows = [dict(row, utt_id=i) for i, row in enumerate(rows, start=1)]
        write_csv(output_dir / "testing.csv", testing_rows)

    return len(rows)


def write_units(units: Sequence[ChatUnit], output_root: Path, testing: bool = False) -> Dict[str, int]:
    """
    Write all discovered units under one output root.

    Goal: provide one shared writer for --input, --dataset, and --dataset all.
    """
    output_root = output_root.expanduser().resolve()
    total_rows = 0
    for unit in units:
        total_rows += write_prepared_unit(output_root / unit.child_id, unit, testing=testing)
    return {"children": len(units), "rows": total_rows}


def process_input_path(input_path: Path, output_root: Path, testing: bool = False) -> Dict[str, int]:
    """
    Prepare a standalone CHAT file or arbitrary CHAT directory.

    Goal: make it easy to run the new preprocessing on tiny fixtures while
    developing cleaning rules.
    """
    units = discover_input_units(input_path)
    return write_units(units, output_root, testing=testing)


def process_dataset(
    dataset: str,
    output_root: Path,
    *,
    base_dir: Optional[Path] = None,
    testing: bool = False,
) -> Dict[str, int]:
    """
    Prepare one known corpus by dataset name.

    Goal: preserve the ergonomic old command style while writing the new
    chi.csv/caretakers.csv/testing.csv outputs.
    """
    raw_base = resolve_base_dir(dataset, base_dir)
    if not raw_base.exists():
        raise FileNotFoundError(f"Raw base directory not found for {dataset}: {raw_base}")

    units = discover_dataset_units(dataset, raw_base)
    if not units:
        raise FileNotFoundError(f"No .cha files found for {dataset} under {raw_base}")

    return write_units(units, output_root.expanduser().resolve() / dataset, testing=testing)


def build_cli() -> argparse.ArgumentParser:
    """
    Build the command-line interface.

    Goal: support both full-corpus runs and small fixture/debug runs from the
    same implementation.
    """
    parser = argparse.ArgumentParser(
        description="Prepare raw CHAT transcripts into chi.csv and caretakers.csv files."
    )
    parser.add_argument(
        "--dataset",
        choices=[*DATASETS, "all"],
        default=None,
        help="Known corpus to prepare. Use --input for a standalone .cha file or arbitrary directory.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Standalone .cha file or directory to prepare outside the known dataset layouts.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Override raw input base directory when using --dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output root. Dataset runs write under <output-dir>/<Dataset>/; --input writes directly under <output-dir>/.",
    )
    parser.add_argument(
        "--testing",
        action="store_true",
        help="Also write testing.csv containing CHI, MOT, and FAT rows together for manual inspection.",
    )
    parser.add_argument("--emit-session-counts", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cleaned-output-dir", default=None, help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    Run preprocessing from CLI arguments.

    Goal: keep command-line behavior thin and testable; all real work happens
    in process_input_path/process_dataset.
    """
    args = build_cli().parse_args(argv)

    if args.input is not None and args.dataset is not None:
        raise SystemExit("[ERROR] Use either --input or --dataset, not both.")
    if args.input is None and args.dataset is None:
        raise SystemExit("[ERROR] Provide --input or --dataset.")
    if args.dataset == "all" and args.base_dir is not None:
        raise SystemExit("[ERROR] --base-dir can only be used with one dataset, not --dataset all.")

    if args.input is not None:
        summary = process_input_path(args.input, args.output_dir, testing=args.testing)
        print(f"Wrote {summary['rows']:,} rows for {summary['children']:,} child folder(s) to {args.output_dir}")
        return

    datasets = DATASETS if args.dataset == "all" else (args.dataset,)
    total_children = 0
    total_rows = 0
    for dataset in datasets:
        summary = process_dataset(
            str(dataset),
            args.output_dir,
            base_dir=args.base_dir,
            testing=args.testing,
        )
        total_children += summary["children"]
        total_rows += summary["rows"]
        print(f"{dataset}: wrote {summary['rows']:,} rows for {summary['children']:,} child folder(s)")

    print(f"Done: wrote {total_rows:,} rows for {total_children:,} child folder(s) to {args.output_dir}")


if __name__ == "__main__":
    main()
