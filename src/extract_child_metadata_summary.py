#!/usr/bin/env python3
"""
Create one metadata-summary CSV row per prepared child folder.

The goal is to make corpus coverage inspectable at a glance: utterance counts,
age coverage, demographics recoverable from CHAT headers, speaker information,
and downstream readiness flags.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from prepare_datasets import DEFAULT_RAW_ROOTS


OUTPUT_COLUMNS = [
    "dataset",
    "child_id",
    "analysis_group",
    "include_in_default_naturalistic",
    "source_groups",
    "stage0_ready",
    "ngram_generated_ready",
    "child_context_ready",
    "caretaker_context_ready",
    "child_scoring_ready",
    "caretaker_scoring_ready",
    "scoring_ready",
    "child_rows",
    "child_nonempty_utterances",
    "caretaker_rows",
    "caretaker_nonempty_utterances",
    "total_nonempty_utterances",
    "child_missing_age_rows",
    "caretaker_missing_age_rows",
    "n_sessions",
    "n_source_files",
    "age_months_min",
    "age_months_max",
    "age_months_mean",
    "sex_values",
    "chi_id_age_values",
    "chi_id_group_values",
    "chi_id_ses_values",
    "chi_id_role_values",
    "chi_id_education_values",
    "chi_id_custom_values",
    "birth_of_chi_values",
    "date_min",
    "date_max",
    "date_values",
    "location_values",
    "types_values",
    "participant_values",
    "caretaker_speaker_values",
    "raw_header_files_read",
    "raw_files_missing",
    "demographic_header_values",
]

ID_FIELDS = [
    "language",
    "corpus",
    "code",
    "age",
    "sex",
    "group",
    "ses",
    "role",
    "education",
    "custom",
]

DEMOGRAPHIC_TERMS = (
    "ses",
    "socio",
    "class",
    "income",
    "education",
    "educated",
    "race",
    "ethnic",
    "ethnicity",
    "gender",
    "sex",
    "maternal",
    "paternal",
)


def compact_values(values: Iterable[object], *, max_chars: int = 1000) -> str:
    """Return sorted unique non-empty values as a compact pipe-delimited string."""
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    out = " | ".join(cleaned)
    if len(out) <= max_chars:
        return out
    return out[: max_chars - 14].rstrip() + " | ...truncated"


def parse_chat_id_line(line: str) -> Dict[str, str]:
    """Parse a CHAT @ID line into named fields."""
    payload = line.split(":", 1)[1].strip() if ":" in line else line.strip()
    parts = payload.split("|")
    parts.extend([""] * (len(ID_FIELDS) - len(parts)))
    return {field: parts[index].strip() for index, field in enumerate(ID_FIELDS)}


def parse_chat_date(value: str) -> Optional[datetime]:
    """Parse common CHAT date strings, returning None when unknown."""
    value = (value or "").strip()
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.upper(), fmt)
        except ValueError:
            continue
    return None


def parse_chat_header(cha_path: Path) -> Dict[str, Set[str]]:
    """
    Read metadata from a CHAT header without reading the transcript body.

    Stops at the first main-tier line. Values are stored as sets because many
    child summaries aggregate several sessions.
    """
    values: Dict[str, Set[str]] = {
        "chi_id_age_values": set(),
        "chi_id_sex_values": set(),
        "chi_id_group_values": set(),
        "chi_id_ses_values": set(),
        "chi_id_role_values": set(),
        "chi_id_education_values": set(),
        "chi_id_custom_values": set(),
        "birth_of_chi_values": set(),
        "date_values": set(),
        "location_values": set(),
        "types_values": set(),
        "participant_values": set(),
        "demographic_header_values": set(),
    }

    with cha_path.open(encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n\r")
            if line.startswith("*"):
                break
            if not line.startswith("@") or ":" not in line:
                continue

            key, content = line[1:].split(":", 1)
            key = key.strip()
            content = content.strip()
            lower = f"{key}: {content}".lower()

            if key.upper() == "ID":
                parsed = parse_chat_id_line(line)
                if parsed.get("code", "").upper() == "CHI":
                    values["chi_id_age_values"].add(parsed.get("age", ""))
                    values["chi_id_sex_values"].add(parsed.get("sex", ""))
                    values["chi_id_group_values"].add(parsed.get("group", ""))
                    values["chi_id_ses_values"].add(parsed.get("ses", ""))
                    values["chi_id_role_values"].add(parsed.get("role", ""))
                    values["chi_id_education_values"].add(parsed.get("education", ""))
                    values["chi_id_custom_values"].add(parsed.get("custom", ""))
                continue

            if key == "Participants":
                values["participant_values"].add(content)
            elif key == "Birth of CHI":
                values["birth_of_chi_values"].add(content)
            elif key == "Date":
                values["date_values"].add(content)
            elif key == "Location":
                values["location_values"].add(content)
            elif key == "Types":
                values["types_values"].add(content)

            if any(term in lower for term in DEMOGRAPHIC_TERMS):
                values["demographic_header_values"].add(f"@{key}: {content}")

    return values


def numeric_or_none(value: object) -> Optional[float]:
    """Return a float when possible, otherwise None."""
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def summarize_prepared_csv(path: Path) -> Dict[str, object]:
    """Summarize one prepared CSV, returning counts and observed metadata."""
    summary: Dict[str, object] = {
        "rows": 0,
        "nonempty_utterances": 0,
        "missing_age_rows": 0,
        "age_values": [],
        "sessions": set(),
        "files": set(),
        "sex_values": set(),
        "source_groups": set(),
        "speaker_values": set(),
    }
    if not path.exists():
        return summary

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            summary["rows"] += 1
            if row.get("utterance_clean", "").strip():
                summary["nonempty_utterances"] += 1

            age = numeric_or_none(row.get("age_months"))
            if age is None:
                summary["missing_age_rows"] += 1
            else:
                summary["age_values"].append(age)

            for key, column in (
                ("sessions", "session_id"),
                ("files", "file"),
                ("sex_values", "sex"),
                ("source_groups", "source_group"),
                ("speaker_values", "speaker"),
            ):
                value = row.get(column, "").strip()
                if value:
                    summary[key].add(value)

    return summary


def read_group_assignments(path: Path) -> Dict[str, Dict[str, str]]:
    """Read dataset grouping metadata if available."""
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["dataset"]: row for row in csv.DictReader(handle)}


def resolve_raw_base(dataset: str) -> Optional[Path]:
    """Return the first existing raw root known for a dataset."""
    for candidate in DEFAULT_RAW_ROOTS.get(dataset, []):
        if candidate.exists():
            return candidate.resolve()
    return None


def discover_child_dirs(data_dir: Path, datasets: Optional[Sequence[str]] = None) -> List[Path]:
    """Find prepared child folders under selected datasets."""
    dataset_filter = set(datasets) if datasets else None
    child_dirs: List[Path] = []
    if not data_dir.exists():
        return child_dirs
    for dataset_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        if dataset_filter and dataset_dir.name not in dataset_filter:
            continue
        for child_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
            if (child_dir / "chi.csv").exists() or (child_dir / "caretakers.csv").exists():
                child_dirs.append(child_dir)
    return child_dirs


def aggregate_header_values(raw_paths: Iterable[Path]) -> Tuple[Dict[str, Set[str]], int]:
    """Aggregate CHAT header values across source files."""
    aggregate: Dict[str, Set[str]] = {}
    n_read = 0
    for raw_path in raw_paths:
        if not raw_path.exists():
            continue
        n_read += 1
        parsed = parse_chat_header(raw_path)
        for key, values in parsed.items():
            aggregate.setdefault(key, set()).update(values)
    return aggregate, n_read


def summarize_child_folder(
    child_dir: Path,
    *,
    grouping: Optional[Dict[str, Dict[str, str]]] = None,
    raw_base: Optional[Path] = None,
) -> Dict[str, object]:
    """Build one output row for one prepared child folder."""
    dataset = child_dir.parent.name
    child_id = child_dir.name
    grouping = grouping or {}
    group_row = grouping.get(dataset, {})

    chi = summarize_prepared_csv(child_dir / "chi.csv")
    caretakers = summarize_prepared_csv(child_dir / "caretakers.csv")
    age_values = list(chi["age_values"]) + list(caretakers["age_values"])
    sessions = set(chi["sessions"]) | set(caretakers["sessions"])
    files = set(chi["files"]) | set(caretakers["files"])
    sex_values = set(chi["sex_values"]) | set(caretakers["sex_values"])
    source_groups = set(chi["source_groups"]) | set(caretakers["source_groups"])

    raw_base = raw_base if raw_base is not None else resolve_raw_base(dataset)
    raw_paths: List[Path] = []
    raw_missing = 0
    if raw_base is not None:
        for file_label in files:
            raw_path = raw_base / file_label
            if raw_path.exists():
                raw_paths.append(raw_path)
            else:
                raw_missing += 1

    header_values, raw_header_files_read = aggregate_header_values(raw_paths)
    header_sex_values = header_values.get("chi_id_sex_values", set())

    parsed_dates = [
        parsed
        for parsed in (parse_chat_date(value) for value in header_values.get("date_values", set()))
        if parsed is not None
    ]
    date_min = min(parsed_dates).date().isoformat() if parsed_dates else ""
    date_max = max(parsed_dates).date().isoformat() if parsed_dates else ""

    row = {
        "dataset": dataset,
        "child_id": child_id,
        "analysis_group": group_row.get("analysis_group", ""),
        "include_in_default_naturalistic": group_row.get("include_in_default_naturalistic", ""),
        "source_groups": compact_values(source_groups),
        "stage0_ready": int((child_dir / "chi.csv").exists() and (child_dir / "caretakers.csv").exists()),
        "ngram_generated_ready": int((child_dir / "chi.ngram_generated.csv").exists()),
        "child_context_ready": int((child_dir / "chi.shared_caretaker_contexts.csv").exists()),
        "caretaker_context_ready": int((child_dir / "caretakers.shared_caretaker_contexts.csv").exists()),
        "child_scoring_ready": int((child_dir / "chi.surprisal_scoring.csv").exists()),
        "caretaker_scoring_ready": int((child_dir / "caretakers.surprisal_scoring.csv").exists()),
        "scoring_ready": int(
            (child_dir / "chi.surprisal_scoring.csv").exists()
            and (child_dir / "caretakers.surprisal_scoring.csv").exists()
        ),
        "child_rows": chi["rows"],
        "child_nonempty_utterances": chi["nonempty_utterances"],
        "caretaker_rows": caretakers["rows"],
        "caretaker_nonempty_utterances": caretakers["nonempty_utterances"],
        "total_nonempty_utterances": chi["nonempty_utterances"] + caretakers["nonempty_utterances"],
        "child_missing_age_rows": chi["missing_age_rows"],
        "caretaker_missing_age_rows": caretakers["missing_age_rows"],
        "n_sessions": len(sessions),
        "n_source_files": len(files),
        "age_months_min": round(min(age_values), 3) if age_values else "",
        "age_months_max": round(max(age_values), 3) if age_values else "",
        "age_months_mean": round(sum(age_values) / len(age_values), 3) if age_values else "",
        "sex_values": compact_values(sex_values | header_sex_values),
        "chi_id_age_values": compact_values(header_values.get("chi_id_age_values", set())),
        "chi_id_group_values": compact_values(header_values.get("chi_id_group_values", set())),
        "chi_id_ses_values": compact_values(header_values.get("chi_id_ses_values", set())),
        "chi_id_role_values": compact_values(header_values.get("chi_id_role_values", set())),
        "chi_id_education_values": compact_values(header_values.get("chi_id_education_values", set())),
        "chi_id_custom_values": compact_values(header_values.get("chi_id_custom_values", set())),
        "birth_of_chi_values": compact_values(header_values.get("birth_of_chi_values", set())),
        "date_min": date_min,
        "date_max": date_max,
        "date_values": compact_values(header_values.get("date_values", set())),
        "location_values": compact_values(header_values.get("location_values", set())),
        "types_values": compact_values(header_values.get("types_values", set())),
        "participant_values": compact_values(header_values.get("participant_values", set())),
        "caretaker_speaker_values": compact_values(caretakers["speaker_values"]),
        "raw_header_files_read": raw_header_files_read,
        "raw_files_missing": raw_missing,
        "demographic_header_values": compact_values(header_values.get("demographic_header_values", set()), max_chars=2000),
    }
    return row


def write_metadata_summary(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    """Write exact-schema metadata rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})


def build_metadata_summary(
    data_dir: Path,
    *,
    datasets: Optional[Sequence[str]] = None,
    grouping_csv: Path = Path("results/corpus_groups/dataset_group_assignments.csv"),
) -> List[Dict[str, object]]:
    """Build metadata rows for all selected prepared child folders."""
    grouping = read_group_assignments(grouping_csv)
    rows = [
        summarize_child_folder(child_dir, grouping=grouping)
        for child_dir in discover_child_dirs(data_dir, datasets=datasets)
    ]
    rows.sort(key=lambda row: (str(row["dataset"]), str(row["child_id"])))
    return rows


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, default=Path("data/preprocessed_data"))
    parser.add_argument("--output", type=Path, default=Path("results/metadata/child_metadata_summary.csv"))
    parser.add_argument("--grouping_csv", type=Path, default=Path("results/corpus_groups/dataset_group_assignments.csv"))
    parser.add_argument("--datasets", nargs="*", default=None)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    rows = build_metadata_summary(args.data_dir, datasets=args.datasets, grouping_csv=args.grouping_csv)
    write_metadata_summary(args.output, rows)
    print(f"Wrote {len(rows):,} child metadata rows to {args.output}")


if __name__ == "__main__":
    main()
