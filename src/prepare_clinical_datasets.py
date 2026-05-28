#!/usr/bin/env python3
"""
Prepare clinical CHILDES/CHAT corpora into separate Stage 0 CSV files.

This script intentionally keeps clinical/probe corpora outside the main
naturalistic `data/preprocessed_data` tree. The output contract mirrors the
regular Stage 0 files:

- chi.csv: target-child utterances.
- caretakers.csv: caregiver utterances detected from CHAT roles.

It also writes metadata summaries so clinical/control coverage is inspectable
without opening hundreds of transcripts.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from cleaning import iter_cleaned_chat_rows
from extract_child_metadata_summary import (
    aggregate_header_values,
    compact_values,
    parse_chat_date,
    summarize_prepared_csv,
)
from prepare_datasets import PREPARED_CHAT_COLUMNS, age_str_to_months, read_session_metadata, write_csv


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw_data" / "Clinical"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "preprocessed_clinical_data"
DEFAULT_CHILD_METADATA = PROJECT_ROOT / "results" / "metadata" / "clinical_child_metadata_summary.csv"
DEFAULT_DATASET_METADATA = PROJECT_ROOT / "results" / "metadata" / "clinical_dataset_summary.csv"

KNOWN_CAREGIVER_CODES = {
    "MOT",
    "FAT",
    "MOM",
    "DAD",
    "MTH",
    "FTH",
    "PAR",
    "PAR0",
    "PAR1",
    "PAR2",
}
CAREGIVER_ROLE_TERMS = (
    "mother",
    "father",
    "parent",
    "caregiver",
    "grandmother",
    "grandfather",
    "grandparent",
    "nanny",
)
NON_CAREGIVER_ROLE_TERMS = (
    "target_child",
    "child",
    "investigator",
    "experimenter",
    "brother",
    "sister",
    "sibling",
    "adult",
    "toy",
)
NON_CAREGIVER_CODES = {"CHI", "INV", "EXP", "BRO", "SIS", "SIB", "NAR", "EXA"}

CLINICAL_HEADER_TERMS = (
    "control",
    "down syndrome",
    "downs",
    "autism",
    "hearing",
    "impair",
    "sli",
    "late talker",
    "language",
    "lesion",
    "gestational",
    "birthweight",
    "group",
    "rla",
    "ela",
    "diagnos",
    "clinical",
)

CLINICAL_CHILD_METADATA_COLUMNS = [
    "clinical_dataset",
    "corpus",
    "child_id",
    "clinical_group",
    "clinical_status",
    "is_control",
    "source_groups",
    "output_dir",
    "stage0_ready",
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
    "raw_files",
    "demographic_header_values",
    "clinical_header_values",
]

CLINICAL_DATASET_METADATA_COLUMNS = [
    "clinical_dataset",
    "corpus",
    "clinical_group",
    "clinical_status",
    "is_control",
    "n_children",
    "n_control_children",
    "n_clinical_children",
    "n_children_with_child_rows",
    "n_children_with_caretaker_rows",
    "child_nonempty_utterances",
    "caretaker_nonempty_utterances",
    "total_nonempty_utterances",
    "n_sessions",
    "n_source_files",
    "age_months_min",
    "age_months_max",
    "sex_values",
    "caretaker_speaker_values",
    "types_values",
]

SESSION_SUFFIX_RE = re.compile(r"\d+$")
FILENAME_AGE_RE = re.compile(r"^(?P<years>\d{2})(?P<months>\d{2})(?P<days>\d{2})(?:[a-z])?$", re.IGNORECASE)


@dataclass(frozen=True)
class ClinicalSpec:
    """Configuration for one clinical/control corpus subset."""

    clinical_dataset: str
    raw_parts: Tuple[str, ...]
    corpus: str
    clinical_group: str
    clinical_status: str
    is_control: int
    layout: str


@dataclass(frozen=True)
class ClinicalUnit:
    """A set of CHAT files that belong to one target child."""

    spec: ClinicalSpec
    child_id: str
    files: List[Path]
    base_dir: Path
    source_group: str


CLINICAL_SPECS = (
    ClinicalSpec("Ambrose_HL", ("Ambrose", "HL"), "Ambrose", "HL", "hearing_loss", 0, "ambrose_age_dirs"),
    ClinicalSpec("Ambrose_TD", ("Ambrose", "TD"), "Ambrose", "TD", "typically_developing_control", 1, "ambrose_age_dirs"),
    ClinicalSpec("Cummings_PD", ("Cummings",), "Cummings", "PD", "speech_sound_disorder_probe", 0, "child_dirs"),
    ClinicalSpec(
        "Feldman_SLI",
        ("Feldman", "ParentChild", "SLI"),
        "ParentChild",
        "SLI",
        "specific_language_impairment",
        0,
        "feldman_sli",
    ),
    ClinicalSpec(
        "Feldman_TD",
        ("Feldman", "ParentChild", "TD"),
        "ParentChild",
        "TD",
        "typically_developing_control",
        1,
        "feldman_td",
    ),
    ClinicalSpec("Flusberg_DS", ("Flusberg",), "Flusberg", "DS", "down_syndrome", 0, "child_dirs"),
    ClinicalSpec("Hooshyar_DS", ("Hooshyar", "DS"), "Hooshyar", "DS", "down_syndrome", 0, "hooshyar_tasks"),
    ClinicalSpec("Hooshyar_TD", ("Hooshyar", "TD"), "Hooshyar", "TD", "typically_developing_control", 1, "hooshyar_tasks"),
    ClinicalSpec("Nicholas_HL", ("Nicholas", "HL"), "Nicholas", "HL", "hearing_loss", 0, "nicholas_direct"),
    ClinicalSpec("Nicholas_TD", ("Nicholas", "TD"), "Nicholas", "TD", "typically_developing_control", 1, "nicholas_direct"),
    ClinicalSpec("Rescorla_LT", ("Rescorla", "LT"), "Rescorla", "LT", "late_talker", 0, "rescorla_age_dirs"),
    ClinicalSpec("Rescorla_TD", ("Rescorla", "TD"), "Rescorla", "TD", "typically_developing_control", 1, "rescorla_age_dirs"),
    ClinicalSpec("Rondal_DS", ("Rondal", "DS"), "Rondal", "DS", "down_syndrome", 0, "rondal_direct"),
    ClinicalSpec("Rondal_TD", ("Rondal", "TD"), "Rondal", "TD", "typically_developing_control", 1, "rondal_direct"),
    ClinicalSpec("UCSD_SLI", ("UCSD",), "UCSD", "SLI", "specific_language_impairment", 0, "child_dirs"),
)


def age_from_filename_stem(cha_path: Path) -> Tuple[str, Optional[float]]:
    """Infer an age from Cummings/UCSD-style YYMMDD filename stems."""
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


def age_from_numeric_parent_dir(cha_path: Path) -> Tuple[str, Optional[float]]:
    """Infer an age from a numeric measurement folder such as 36 or 108."""
    for parent in reversed(cha_path.parents):
        if parent.name.isdigit():
            total_months = int(parent.name)
            years, months = divmod(total_months, 12)
            age_raw = f"{years};{months:02d}.00"
            return age_raw, float(total_months)
    return "", None


def read_clinical_session_metadata(cha_path: Path) -> Dict[str, object]:
    """Read CHI age/sex, with clinical-corpus filename/folder fallbacks."""
    metadata = read_session_metadata(cha_path)
    if metadata.get("age_raw"):
        return metadata

    age_raw, age_months = age_from_filename_stem(cha_path)
    if not age_raw:
        age_raw, age_months = age_from_numeric_parent_dir(cha_path)

    return {
        "age_raw": age_raw,
        "age_months": age_months,
        "sex": metadata.get("sex", ""),
    }


def child_id_from_rondal_filename(cha_path: Path) -> str:
    """Return Rondal child ID by removing session digits: ava1 -> ava."""
    child_id = SESSION_SUFFIX_RE.sub("", cha_path.stem)
    return child_id or cha_path.stem


def child_id_from_ambrose_filename(cha_path: Path) -> str:
    """Return Ambrose child ID from files like 87FB_14.cha."""
    return cha_path.stem.split("_", 1)[0]


def child_id_from_hooshyar_filename(cha_path: Path) -> str:
    """Return Hooshyar child ID by removing task prefix: p042 -> 042."""
    match = re.match(r"^[a-zA-Z](.+)$", cha_path.stem)
    return match.group(1) if match else cha_path.stem


def child_id_from_nicholas_filename(cha_path: Path) -> str:
    """Return Nicholas child ID from files like hi24f-valencia.cha."""
    if "-" in cha_path.stem:
        return cha_path.stem.rsplit("-", 1)[1]
    return cha_path.stem


def child_id_from_feldman_filename(cha_path: Path) -> str:
    """Return Feldman child ID by stripping the trailing two-digit age code."""
    return re.sub(r"\d{2}$", "", cha_path.stem) or cha_path.stem


def child_id_from_rescorla_filename(cha_path: Path) -> str:
    """Return Rescorla child ID by removing the measurement-age suffix."""
    age_dir = ""
    for parent in reversed(cha_path.parents):
        if parent.name.isdigit():
            age_dir = parent.name
            break
    if age_dir:
        child_id = re.sub(rf"{re.escape(age_dir)}[a-zA-Z]*$", "", cha_path.stem)
        return child_id or cha_path.stem
    return re.sub(r"\d+[a-zA-Z]*$", "", cha_path.stem) or cha_path.stem


def _files_directly_under(path: Path) -> List[Path]:
    """Return sorted direct CHAT files in one folder."""
    return sorted(candidate for candidate in path.glob("*.cha") if candidate.is_file())


def _all_cha_files(path: Path) -> List[Path]:
    """Return sorted CHAT files recursively."""
    return sorted(candidate for candidate in path.rglob("*.cha") if candidate.is_file())


def _append_grouped_file(grouped: Dict[Tuple[str, str], List[Path]], child_id: str, source_group: str, path: Path) -> None:
    grouped[(child_id, source_group)].append(path)


def discover_units_for_spec(spec: ClinicalSpec, raw_root: Path) -> List[ClinicalUnit]:
    """Discover one ClinicalUnit per child for a configured clinical subset."""
    base_dir = raw_root.joinpath(*spec.raw_parts)
    if not base_dir.exists():
        return []

    grouped: Dict[Tuple[str, str], List[Path]] = defaultdict(list)

    if spec.layout == "child_dirs":
        for child_dir in sorted(candidate for candidate in base_dir.iterdir() if candidate.is_dir()):
            files = _files_directly_under(child_dir)
            if files:
                _append_grouped_file(grouped, child_dir.name, spec.clinical_group, files[0])
                for extra_file in files[1:]:
                    _append_grouped_file(grouped, child_dir.name, spec.clinical_group, extra_file)

    elif spec.layout == "ambrose_age_dirs":
        for cha_path in _all_cha_files(base_dir):
            _append_grouped_file(grouped, child_id_from_ambrose_filename(cha_path), spec.clinical_group, cha_path)

    elif spec.layout == "hooshyar_tasks":
        for cha_path in _all_cha_files(base_dir):
            _append_grouped_file(grouped, child_id_from_hooshyar_filename(cha_path), spec.clinical_group, cha_path)

    elif spec.layout == "nicholas_direct":
        for cha_path in _files_directly_under(base_dir):
            _append_grouped_file(grouped, child_id_from_nicholas_filename(cha_path), spec.clinical_group, cha_path)

    elif spec.layout == "rondal_direct":
        for cha_path in _files_directly_under(base_dir):
            _append_grouped_file(grouped, child_id_from_rondal_filename(cha_path), spec.clinical_group, cha_path)

    elif spec.layout == "feldman_td":
        for cha_path in _files_directly_under(base_dir):
            _append_grouped_file(grouped, child_id_from_feldman_filename(cha_path), spec.clinical_group, cha_path)

    elif spec.layout == "feldman_sli":
        for cha_path in _all_cha_files(base_dir):
            subgroup = cha_path.parent.name if cha_path.parent != base_dir else spec.clinical_group
            child_id = f"{subgroup}_{child_id_from_feldman_filename(cha_path)}"
            _append_grouped_file(grouped, child_id, f"{spec.clinical_group}/{subgroup}", cha_path)

    elif spec.layout == "rescorla_age_dirs":
        for cha_path in _all_cha_files(base_dir):
            _append_grouped_file(grouped, child_id_from_rescorla_filename(cha_path), spec.clinical_group, cha_path)

    else:
        raise ValueError(f"Unknown clinical layout: {spec.layout}")

    return [
        ClinicalUnit(
            spec=spec,
            child_id=child_id,
            files=sorted(files),
            base_dir=base_dir,
            source_group=source_group,
        )
        for (child_id, source_group), files in sorted(grouped.items())
    ]


def discover_clinical_units(raw_root: Path, datasets: Optional[Sequence[str]] = None) -> List[ClinicalUnit]:
    """Discover all requested clinical units."""
    requested = set(datasets) if datasets else None
    units: List[ClinicalUnit] = []
    for spec in CLINICAL_SPECS:
        if requested and spec.clinical_dataset not in requested:
            continue
        units.extend(discover_units_for_spec(spec, raw_root))
    return units


def parse_id_speaker_roles(cha_path: Path) -> Dict[str, str]:
    """Return CHAT speaker code -> role from @ID lines."""
    roles: Dict[str, str] = {}
    with cha_path.open(encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n\r")
            if line.startswith("*"):
                break
            if not line.startswith("@ID:"):
                continue
            payload = line.split(":", 1)[1].strip()
            parts = payload.split("|")
            if len(parts) < 8:
                continue
            code = parts[2].strip().upper()
            role = parts[7].strip()
            if code:
                roles[code] = role
    return roles


def is_caregiver_speaker(code: str, role: str) -> bool:
    """Return True when a CHAT speaker should be kept as caregiver context."""
    code_upper = code.upper()
    role_lower = role.strip().lower()
    if code_upper in NON_CAREGIVER_CODES:
        return False
    if code_upper in KNOWN_CAREGIVER_CODES:
        return True
    if role_lower and any(term in role_lower for term in NON_CAREGIVER_ROLE_TERMS):
        return False
    return bool(role_lower and any(term in role_lower for term in CAREGIVER_ROLE_TERMS))


def caretaker_speakers_for_unit(unit: ClinicalUnit) -> Tuple[str, ...]:
    """Infer caregiver speaker tiers for a clinical child unit."""
    speakers: Set[str] = set(KNOWN_CAREGIVER_CODES)
    for cha_path in unit.files:
        for code, role in parse_id_speaker_roles(cha_path).items():
            if is_caregiver_speaker(code, role):
                speakers.add(code.upper())
    return tuple(sorted(speakers))


def prepared_rows_for_unit(unit: ClinicalUnit) -> List[Dict[str, object]]:
    """Build Stage 0 rows for one clinical child unit."""
    rows: List[Dict[str, object]] = []
    caretaker_speakers = caretaker_speakers_for_unit(unit)
    speakers = ("CHI", *caretaker_speakers)
    role_counts: Dict[str, int] = defaultdict(int)

    for session_id, cha_path in enumerate(sorted(unit.files), start=1):
        metadata = read_clinical_session_metadata(cha_path)
        for raw_row in iter_cleaned_chat_rows(cha_path, base_dir=unit.base_dir, speakers=speakers):
            speaker = str(raw_row["speaker"])
            role_counts[speaker] += 1
            reference_line = f"{raw_row['file']}:{raw_row['line_no']}"
            rows.append(
                {
                    "dataset": unit.spec.clinical_dataset,
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


def subset_rows(rows: Sequence[Dict[str, object]], speakers: Iterable[str]) -> List[Dict[str, object]]:
    """Return selected speakers and renumber output-local utt_id values."""
    speaker_set = set(speakers)
    selected: List[Dict[str, object]] = []
    for source_row in rows:
        if source_row["speaker"] not in speaker_set:
            continue
        row = dict(source_row)
        row["utt_id"] = len(selected) + 1
        selected.append(row)
    return selected


def write_prepared_unit(unit: ClinicalUnit, output_root: Path, testing: bool = False) -> Dict[str, object]:
    """Write chi/caretakers CSVs for one clinical child unit."""
    output_dir = output_root / unit.spec.clinical_dataset / unit.child_id
    rows = prepared_rows_for_unit(unit)
    caretaker_speakers = caretaker_speakers_for_unit(unit)

    write_csv(output_dir / "chi.csv", subset_rows(rows, ("CHI",)))
    write_csv(output_dir / "caretakers.csv", subset_rows(rows, caretaker_speakers))
    if testing:
        write_csv(output_dir / "testing.csv", [dict(row, utt_id=index) for index, row in enumerate(rows, start=1)])

    return {
        "clinical_dataset": unit.spec.clinical_dataset,
        "child_id": unit.child_id,
        "rows": len(rows),
        "output_dir": str(output_dir),
    }


def parse_extra_clinical_header_values(raw_paths: Iterable[Path]) -> Set[str]:
    """Collect clinical/control comments that are not standard CHAT demographics."""
    values: Set[str] = set()
    for raw_path in raw_paths:
        if not raw_path.exists():
            continue
        with raw_path.open(encoding="utf-8", errors="replace") as handle:
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
                if any(term in lower for term in CLINICAL_HEADER_TERMS):
                    values.add(f"@{key}: {content}")
    return values


def _date_bounds(values: Iterable[str]) -> Tuple[str, str]:
    """Return ISO min/max dates from CHAT date values."""
    parsed = [date for date in (parse_chat_date(value) for value in values) if date is not None]
    if not parsed:
        return "", ""
    return min(parsed).date().isoformat(), max(parsed).date().isoformat()


def build_child_metadata_row(unit: ClinicalUnit, output_root: Path) -> Dict[str, object]:
    """Build one clinical child metadata row."""
    child_dir = output_root / unit.spec.clinical_dataset / unit.child_id
    chi = summarize_prepared_csv(child_dir / "chi.csv")
    caretakers = summarize_prepared_csv(child_dir / "caretakers.csv")
    age_values = list(chi["age_values"]) + list(caretakers["age_values"])
    sessions = set(chi["sessions"]) | set(caretakers["sessions"])
    files = set(chi["files"]) | set(caretakers["files"])
    sex_values = set(chi["sex_values"]) | set(caretakers["sex_values"])
    source_groups = set(chi["source_groups"]) | set(caretakers["source_groups"])

    raw_paths_by_label = {path.relative_to(unit.base_dir).as_posix(): path for path in unit.files}
    raw_paths = [raw_paths_by_label[file_label] for file_label in files if file_label in raw_paths_by_label]
    raw_missing = len([file_label for file_label in files if file_label not in raw_paths_by_label])
    header_values, raw_header_files_read = aggregate_header_values(raw_paths)
    clinical_header_values = parse_extra_clinical_header_values(raw_paths)
    date_min, date_max = _date_bounds(header_values.get("date_values", set()))

    return {
        "clinical_dataset": unit.spec.clinical_dataset,
        "corpus": unit.spec.corpus,
        "child_id": unit.child_id,
        "clinical_group": unit.spec.clinical_group,
        "clinical_status": unit.spec.clinical_status,
        "is_control": unit.spec.is_control,
        "source_groups": compact_values(source_groups),
        "output_dir": str(child_dir),
        "stage0_ready": int((child_dir / "chi.csv").exists() and (child_dir / "caretakers.csv").exists()),
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
        "sex_values": compact_values(sex_values | header_values.get("chi_id_sex_values", set())),
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
        "raw_files": compact_values(path.relative_to(unit.base_dir).as_posix() for path in unit.files),
        "demographic_header_values": compact_values(
            header_values.get("demographic_header_values", set()),
            max_chars=2000,
        ),
        "clinical_header_values": compact_values(clinical_header_values, max_chars=3000),
    }


def write_csv_with_columns(path: Path, columns: Sequence[str], rows: Sequence[Dict[str, object]]) -> None:
    """Write dictionaries with an exact output schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def split_compact_values(values: Iterable[object]) -> List[str]:
    """Split pipe-delimited child summaries before aggregating them again."""
    split_values: List[str] = []
    for value in values:
        for part in str(value).split(" | "):
            cleaned = part.strip()
            if cleaned:
                split_values.append(cleaned)
    return split_values


def build_dataset_metadata_rows(child_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Aggregate clinical child metadata to one row per clinical subset."""
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in child_rows:
        grouped[str(row["clinical_dataset"])].append(row)

    dataset_rows: List[Dict[str, object]] = []
    for clinical_dataset, rows in sorted(grouped.items()):
        first = rows[0]
        age_mins = [float(row["age_months_min"]) for row in rows if str(row.get("age_months_min", "")).strip()]
        age_maxes = [float(row["age_months_max"]) for row in rows if str(row.get("age_months_max", "")).strip()]
        is_control = int(first.get("is_control", 0))
        dataset_rows.append(
            {
                "clinical_dataset": clinical_dataset,
                "corpus": first.get("corpus", ""),
                "clinical_group": first.get("clinical_group", ""),
                "clinical_status": first.get("clinical_status", ""),
                "is_control": is_control,
                "n_children": len(rows),
                "n_control_children": len(rows) if is_control else 0,
                "n_clinical_children": 0 if is_control else len(rows),
                "n_children_with_child_rows": sum(int(row.get("child_rows", 0)) > 0 for row in rows),
                "n_children_with_caretaker_rows": sum(int(row.get("caretaker_rows", 0)) > 0 for row in rows),
                "child_nonempty_utterances": sum(int(row.get("child_nonempty_utterances", 0)) for row in rows),
                "caretaker_nonempty_utterances": sum(int(row.get("caretaker_nonempty_utterances", 0)) for row in rows),
                "total_nonempty_utterances": sum(int(row.get("total_nonempty_utterances", 0)) for row in rows),
                "n_sessions": sum(int(row.get("n_sessions", 0)) for row in rows),
                "n_source_files": sum(int(row.get("n_source_files", 0)) for row in rows),
                "age_months_min": round(min(age_mins), 3) if age_mins else "",
                "age_months_max": round(max(age_maxes), 3) if age_maxes else "",
                "sex_values": compact_values(split_compact_values(row.get("sex_values", "") for row in rows)),
                "caretaker_speaker_values": compact_values(
                    split_compact_values(row.get("caretaker_speaker_values", "") for row in rows)
                ),
                "types_values": compact_values(split_compact_values(row.get("types_values", "") for row in rows)),
            }
        )
    return dataset_rows


def prepare_clinical_datasets(
    raw_root: Path = DEFAULT_RAW_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    datasets: Optional[Sequence[str]] = None,
    child_metadata_path: Path = DEFAULT_CHILD_METADATA,
    dataset_metadata_path: Path = DEFAULT_DATASET_METADATA,
    testing: bool = False,
) -> Dict[str, int]:
    """Prepare clinical corpora and write metadata summaries."""
    raw_root = raw_root.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    units = discover_clinical_units(raw_root, datasets=datasets)
    if not units:
        raise FileNotFoundError(f"No clinical CHAT units found under {raw_root}")

    total_rows = 0
    for unit in units:
        summary = write_prepared_unit(unit, output_dir, testing=testing)
        total_rows += int(summary["rows"])

    child_rows = [build_child_metadata_row(unit, output_dir) for unit in units]
    child_rows.sort(key=lambda row: (str(row["clinical_dataset"]), str(row["child_id"])))
    dataset_rows = build_dataset_metadata_rows(child_rows)

    write_csv_with_columns(output_dir / "manifest.csv", CLINICAL_CHILD_METADATA_COLUMNS, child_rows)
    write_csv_with_columns(child_metadata_path, CLINICAL_CHILD_METADATA_COLUMNS, child_rows)
    write_csv_with_columns(dataset_metadata_path, CLINICAL_DATASET_METADATA_COLUMNS, dataset_rows)

    return {
        "clinical_datasets": len({unit.spec.clinical_dataset for unit in units}),
        "children": len(units),
        "rows": total_rows,
        "control_children": sum(unit.spec.is_control for unit in units),
        "clinical_children": sum(1 - unit.spec.is_control for unit in units),
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Prepare clinical CHILDES/CHAT corpora.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--child-metadata", type=Path, default=DEFAULT_CHILD_METADATA)
    parser.add_argument("--dataset-metadata", type=Path, default=DEFAULT_DATASET_METADATA)
    parser.add_argument("--datasets", nargs="*", default=None, help="Optional clinical dataset names, e.g. Rondal_DS.")
    parser.add_argument("--testing", action="store_true", help="Also write combined testing.csv files.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Run clinical preprocessing."""
    args = parse_args(argv)
    summary = prepare_clinical_datasets(
        raw_root=args.raw_root,
        output_dir=args.output_dir,
        datasets=args.datasets,
        child_metadata_path=args.child_metadata,
        dataset_metadata_path=args.dataset_metadata,
        testing=args.testing,
    )
    print(
        "Prepared "
        f"{summary['children']:,} children "
        f"({summary['control_children']:,} control, {summary['clinical_children']:,} clinical) "
        f"across {summary['clinical_datasets']:,} clinical dataset groups; "
        f"wrote {summary['rows']:,} rows."
    )
    print(f"Prepared files: {args.output_dir}")
    print(f"Child metadata: {args.child_metadata}")
    print(f"Dataset metadata: {args.dataset_metadata}")


if __name__ == "__main__":
    main()
