#!/usr/bin/env python3
"""Prepare the Hall corpus as an auditable cross-sectional snapshot dataset.

Hall differs from the longitudinal caregiver-child corpora in this project: a
file follows one focal child across home, school, and transition settings, and
the interlocutor set includes parents, teachers, investigators, other adults,
peers, siblings, unidentified speakers, and media.  This module therefore
preserves every CHAT main tier and its active ``@Situation`` while also writing
the familiar ``chi.csv`` and ``caretakers.csv`` compatibility views.

The demographic fields are historical corpus strata.  They are preserved with
their source and scope; they are not silently reinterpreted as modern household
income, education, or a continuous SES measure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

try:
    from cleaning import clean_chat_utterance
    from prepare_datasets import PREPARED_CHAT_COLUMNS, age_str_to_months
except ImportError:  # pragma: no cover - package imports used by unit tests
    from src.cleaning import clean_chat_utterance
    from src.prepare_datasets import PREPARED_CHAT_COLUMNS, age_str_to_months


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data/raw_data/Hall"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data/preprocessed_data/Hall"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "results/hall_snapshot_preprocessing"

GROUP_DEMOGRAPHICS = {
    "BlackPro": ("Black", "UC"),
    "BlackWork": ("Black", "WC"),
    "WhitePro": ("White", "UC"),
    "WhiteWork": ("White", "WC"),
}

ADULT_CODES = {"MOT", "FAT", "GRA", "GRF", "EXP", "TEA", "FAD", "MAD", "TCA"}
CHILD_PEER_CODES = {"MCH", "FCH", "BRO", "SIS"}
MEDIA_CODES = {"TEL"}
UNIDENTIFIED_CODES = {"UNK", "GRO"}
FAMILY_CAREGIVER_CODES = {"MOT", "FAT", "GRA", "GRF"}

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?")
SPACE_RE = re.compile(r"\s+")

ALL_SPEAKER_COLUMNS = [
    "dataset", "child_id", "source_group", "race", "social_class",
    "demographic_source", "age_raw", "age_months", "sex", "file",
    "line_no", "reference_line", "turn_id", "speaker",
    "speaker_description", "speaker_role_group", "situation_id",
    "situation_text", "setting_auto", "setting_review_required", "utterance",
    "utterance_clean", "cleaned_is_empty", "previous_main_speaker",
    "previous_main_role_group", "child_after_adult",
]

INVENTORY_COLUMNS = [
    "dataset", "child_id", "source_group", "source_file", "raw_sha256",
    "age_raw", "age_months", "sex", "race", "social_class", "stratum",
    "demographic_source", "demographic_scope", "demographic_conflict",
    "main_tier_rows", "target_child_rows", "target_child_nonempty_rows",
    "adult_interlocutor_rows", "child_peer_rows", "situation_count",
    "analysis_status", "primary_eligible", "sensitivity_eligible",
    "exclusion_reasons",
]

METADATA_COLUMNS = [
    "dataset", "child_id", "source_group", "age_raw", "age_months", "sex",
    "race", "social_class", "stratum", "chi_id_ses_raw",
    "metadata_csv_race", "metadata_csv_social_class", "demographic_source",
    "demographic_scope", "demographic_conflict", "primary_eligible",
    "sensitivity_eligible", "analysis_status",
]

SCORING_COLUMNS = [
    "dataset", "child_id", "source_group", "race", "social_class", "stratum",
    "demographic_source", "primary_eligible", "sensitivity_eligible",
    "age_raw", "age_months", "sex", "file", "line_no", "utterance_id",
    "situation_id", "situation_text", "setting_auto", "setting_review_required",
    "previous_main_speaker", "previous_main_role_group", "child_after_adult",
    "context_k1", "context_k2", "context_k3", "chi_utterance_clean",
    "nb_words", "nb_characters",
]


@dataclass(frozen=True)
class Demographics:
    race: str
    social_class: str
    source: str
    scope: str
    conflict: bool
    primary_eligible: bool
    sensitivity_eligible: bool

    @property
    def stratum(self) -> str:
        if not self.race or not self.social_class:
            return ""
        return f"{self.race}_{self.social_class}"


@dataclass
class HallChatDocument:
    child_id: str
    source_group: str
    age_raw: str
    age_months: float | None
    sex: str
    child_id_ses_raw: str
    comments: list[str]
    participants: dict[str, str]
    situations: list[str]
    rows: list[dict[str, object]]


def _normalized(value: object) -> str:
    return "" if value is None else str(value).strip()


def _parse_ses(value: str) -> tuple[str, str]:
    pieces = [piece.strip() for piece in (value or "").split(",")]
    if len(pieces) < 2:
        return "", ""
    race = pieces[0].title()
    social_class = pieces[1].upper()
    if race not in {"Black", "White"} or social_class not in {"UC", "WC"}:
        return "", ""
    return race, social_class


def resolve_child_demographics(
    *,
    child_id: str,
    source_group: str,
    child_id_ses_raw: str,
    metadata_row: Mapping[str, str] | None,
) -> Demographics:
    """Resolve Hall race/class strata while retaining source provenance."""

    metadata_row = metadata_row or {}
    id_race, id_class = _parse_ses(child_id_ses_raw)
    csv_race = _normalized(metadata_row.get("race", "")).title()
    csv_class = _normalized(metadata_row.get("social_class", "")).upper()
    if csv_race not in {"Black", "White"}:
        csv_race = ""
    if csv_class not in {"UC", "WC"}:
        csv_class = ""
    group_race, group_class = GROUP_DEMOGRAPHICS.get(source_group, ("", ""))

    explicit_pairs = {
        pair for pair in ((id_race, id_class), (csv_race, csv_class)) if all(pair)
    }
    conflict = len(explicit_pairs) > 1
    if id_race and id_class:
        race, social_class, source = id_race, id_class, "chi_id"
    elif csv_race and csv_class:
        race, social_class, source = csv_race, csv_class, "children_meta_csv"
    else:
        race, social_class, source = group_race, group_class, "source_group_inferred"

    if race and social_class and group_race and group_class:
        conflict = conflict or (race, social_class) != (group_race, group_class)

    child_specific = source in {"chi_id", "children_meta_csv"}
    has_stratum = bool(race and social_class)
    return Demographics(
        race=race,
        social_class=social_class,
        source=source if has_stratum else "missing",
        scope="child_specific" if child_specific else ("folder_group" if has_stratum else "missing"),
        conflict=conflict,
        primary_eligible=has_stratum and child_specific and not conflict,
        sensitivity_eligible=has_stratum and not conflict,
    )


def speaker_role_group(code: str, description: str) -> str:
    """Map a Hall participant to a broad, auditable conversational role."""

    code = (code or "").upper()
    description = (description or "").strip().lower()
    if code == "CHI" or description == "target_child":
        return "target_child"
    if code in ADULT_CODES or description in {
        "mother", "father", "adult", "investigator", "teacher",
        "grandmother", "grandfather",
    }:
        return "adult_interlocutor"
    if code in CHILD_PEER_CODES or description in {"child", "brother", "sister"}:
        return "child_peer"
    if code in MEDIA_CODES or description == "media":
        return "media"
    if code in UNIDENTIFIED_CODES or description == "unidentified":
        return "unidentified"
    return "unresolved_participant"


def classify_situation(text: str) -> tuple[str, int]:
    """Return a conservative automatic home/school/transition setting label."""

    value = SPACE_RE.sub(" ", (text or "").strip().lower())
    if not value:
        return "unknown", 1
    if (
        "arriving home" in value
        or "before leaving home" in value
        or "departure for school" in value
        or any(
            phrase in value
            for phrase in ("before dinner", "dinner time", "before bed", "at home", "breakfast")
        )
    ):
        return "home", 0
    if "on the way" in value or (
        "to school" in value and "arriving at school" not in value
    ):
        if "before school" not in value and "prior to" not in value:
            return "transition", 0
    if "arriving at school" in value or "at school" in value or "school classroom" in value:
        return "school", 0
    if "before school" in value or ("prior to" in value and "school" in value):
        return "home", 0
    if "school" in value:
        return "school", 1
    return "other", 1


def _parse_participants(value: str) -> dict[str, str]:
    participants: dict[str, str] = {}
    for item in value.split(","):
        pieces = item.strip().split(maxsplit=1)
        if not pieces:
            continue
        participants[pieces[0].upper()] = pieces[1].strip() if len(pieces) > 1 else ""
    return participants


def parse_hall_chat(path: Path, *, source_group: str) -> HallChatDocument:
    """Parse all Hall main tiers and attach the active situation to each turn."""

    participants: dict[str, str] = {}
    comments: list[str] = []
    situations: list[str] = []
    rows: list[dict[str, object]] = []
    age_raw = ""
    sex = ""
    child_id_ses_raw = ""
    current_situation = ""
    current_situation_id = 0
    current_speaker = ""
    current_line = 0
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_speaker, current_line, current_parts
        if not current_speaker:
            return
        utterance = SPACE_RE.sub(" ", " ".join(current_parts)).strip()
        cleaned = clean_chat_utterance(utterance)
        description = participants.get(current_speaker, "")
        role = speaker_role_group(current_speaker, description)
        setting, review = classify_situation(current_situation)
        previous = rows[-1] if rows else None
        rows.append(
            {
                "line_no": current_line,
                "turn_id": len(rows) + 1,
                "speaker": current_speaker,
                "speaker_description": description,
                "speaker_role_group": role,
                "situation_id": current_situation_id,
                "situation_text": current_situation,
                "setting_auto": setting,
                "setting_review_required": review,
                "utterance": utterance,
                "utterance_clean": cleaned,
                "cleaned_is_empty": int(not cleaned),
                "previous_main_speaker": previous["speaker"] if previous else "",
                "previous_main_role_group": previous["speaker_role_group"] if previous else "",
                "child_after_adult": int(
                    role == "target_child"
                    and previous is not None
                    and previous["speaker_role_group"] == "adult_interlocutor"
                ),
            }
        )
        current_speaker = ""
        current_line = 0
        current_parts = []

    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\r\n")
            stripped = line.lstrip()
            if stripped.startswith("*") and ":" in stripped:
                flush()
                tier, utterance = stripped.split(":", 1)
                current_speaker = tier[1:].strip().upper()
                current_line = line_no
                current_parts = [utterance.strip()]
                continue
            if stripped.startswith("@Situation:"):
                flush()
                current_situation = stripped.split(":", 1)[1].strip()
                situations.append(current_situation)
                current_situation_id += 1
                continue
            if stripped.startswith("@Participants:"):
                participants.update(_parse_participants(stripped.split(":", 1)[1].strip()))
            elif stripped.startswith("@Comment:"):
                comments.append(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("@ID:"):
                fields = stripped.split(":", 1)[1].strip().split("|")
                if len(fields) > 2 and fields[2].strip().upper() == "CHI":
                    age_raw = fields[3].strip() if len(fields) > 3 else ""
                    sex = fields[4].strip() if len(fields) > 4 else ""
                    child_id_ses_raw = fields[6].strip() if len(fields) > 6 else ""
            if (
                current_speaker
                and line[:1].isspace()
                and stripped
                and not stripped.startswith(("*", "%", "@"))
            ):
                current_parts.append(stripped)
                continue
            if current_speaker and stripped.startswith(("%", "@")):
                flush()
        flush()

    return HallChatDocument(
        child_id=path.stem,
        source_group=source_group,
        age_raw=age_raw,
        age_months=age_str_to_months(age_raw),
        sex=sex,
        child_id_ses_raw=child_id_ses_raw,
        comments=comments,
        participants=participants,
        situations=situations,
        rows=rows,
    )


def _read_metadata(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {row["child_id"].strip(): row for row in csv.DictReader(handle)}


def _write_csv(path: Path, rows: Iterable[Mapping[str, object]], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: "" if row.get(column) is None else row.get(column) for column in columns})


def _standard_rows(
    enriched_rows: Sequence[dict[str, object]],
    *,
    speakers: set[str] | None = None,
    role: str | None = None,
) -> list[dict[str, object]]:
    selected = [
        row for row in enriched_rows
        if (speakers is None or str(row["speaker"]) in speakers)
        and (role is None or row["speaker_role_group"] == role)
    ]
    role_counts: dict[str, int] = {}
    output: list[dict[str, object]] = []
    for index, row in enumerate(selected, start=1):
        speaker = str(row["speaker"])
        role_counts[speaker] = role_counts.get(speaker, 0) + 1
        output.append(
            {
                "dataset": "Hall",
                "child_id": row["child_id"],
                "source_group": row["source_group"],
                "session_id": 1,
                "age_raw": row["age_raw"],
                "age_months": row["age_months"],
                "sex": row["sex"],
                "file": row["file"],
                "line_no": row["line_no"],
                "reference_line": row["reference_line"],
                "utt_id": index,
                "utt_id_role": role_counts[speaker],
                "speaker": speaker,
                "utterance": row["utterance"],
                "utterance_clean": row["utterance_clean"],
                "cleaned_is_empty": row["cleaned_is_empty"],
            }
        )
    return output


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hall_scoring_rows(
    rows: Sequence[dict[str, object]],
    *,
    demographics: Demographics,
    primary_eligible: bool,
    sensitivity_eligible: bool,
) -> list[dict[str, object]]:
    """Build nonempty child targets with prior-adult contexts per situation."""

    if not sensitivity_eligible:
        return []
    histories: dict[int, list[str]] = {}
    output: list[dict[str, object]] = []
    for row in rows:
        situation_id = int(row["situation_id"])
        history = histories.setdefault(situation_id, [])
        role = row["speaker_role_group"]
        cleaned = str(row["utterance_clean"]).strip()
        if role == "target_child" and WORD_RE.search(cleaned):
            tokens = WORD_RE.findall(cleaned)
            output.append(
                {
                    "dataset": "Hall",
                    "child_id": row["child_id"],
                    "source_group": row["source_group"],
                    "race": demographics.race,
                    "social_class": demographics.social_class,
                    "stratum": demographics.stratum,
                    "demographic_source": demographics.source,
                    "primary_eligible": int(primary_eligible),
                    "sensitivity_eligible": int(sensitivity_eligible),
                    "age_raw": row["age_raw"],
                    "age_months": row["age_months"],
                    "sex": row["sex"],
                    "file": row["file"],
                    "line_no": row["line_no"],
                    "utterance_id": f"Hall|{row['child_id']}|{row['file']}|{row['line_no']}",
                    "situation_id": situation_id,
                    "situation_text": row["situation_text"],
                    "setting_auto": row["setting_auto"],
                    "setting_review_required": row["setting_review_required"],
                    "previous_main_speaker": row["previous_main_speaker"],
                    "previous_main_role_group": row["previous_main_role_group"],
                    "child_after_adult": row["child_after_adult"],
                    "context_k1": " ".join(history[-1:]),
                    "context_k2": " ".join(history[-2:]),
                    "context_k3": " ".join(history[-3:]),
                    "chi_utterance_clean": cleaned,
                    "nb_words": len(tokens),
                    "nb_characters": len(cleaned),
                }
            )
        if role == "adult_interlocutor" and cleaned:
            history.append(cleaned)
    return output


def prepare_hall_snapshot(
    *, raw_root: Path = DEFAULT_RAW_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_root: Path = DEFAULT_REPORT_ROOT,
) -> dict[str, object]:
    """Prepare Hall files, compatibility tables, manifests, and sample gates."""

    raw_root = raw_root.expanduser().resolve()
    output_root = output_root.expanduser().resolve()
    report_root = report_root.expanduser().resolve()
    if not raw_root.exists():
        raise FileNotFoundError(f"Hall raw root does not exist: {raw_root}")

    metadata_lookup = _read_metadata(raw_root / "children_meta.csv")
    inventory: list[dict[str, object]] = []
    metadata_rows: list[dict[str, object]] = []
    seen_children: set[str] = set()
    duplicate_children: list[str] = []
    all_main_rows = 0
    scoring_rows: list[dict[str, object]] = []

    for source_group in sorted(GROUP_DEMOGRAPHICS):
        group_dir = raw_root / source_group
        for path in sorted(group_dir.glob("*.cha")) if group_dir.exists() else []:
            document = parse_hall_chat(path, source_group=source_group)
            if document.child_id in seen_children:
                duplicate_children.append(document.child_id)
            seen_children.add(document.child_id)
            meta = metadata_lookup.get(document.child_id, {})
            demographics = resolve_child_demographics(
                child_id=document.child_id,
                source_group=source_group,
                child_id_ses_raw=document.child_id_ses_raw,
                metadata_row=meta,
            )
            age_raw = document.age_raw or _normalized(meta.get("age", ""))
            age_months = age_str_to_months(age_raw)
            sex = document.sex or _normalized(meta.get("sex", ""))
            file_label = f"{source_group}/{path.name}"

            enriched: list[dict[str, object]] = []
            for row in document.rows:
                enriched.append(
                    {
                        "dataset": "Hall",
                        "child_id": document.child_id,
                        "source_group": source_group,
                        "race": demographics.race,
                        "social_class": demographics.social_class,
                        "demographic_source": demographics.source,
                        "age_raw": age_raw,
                        "age_months": age_months,
                        "sex": sex,
                        "file": file_label,
                        "reference_line": f"{file_label}:{row['line_no']}",
                        **row,
                    }
                )
            all_main_rows += len(enriched)

            child_dir = output_root / document.child_id
            _write_csv(child_dir / "all_speakers.csv", enriched, ALL_SPEAKER_COLUMNS)
            _write_csv(
                child_dir / "adult_interlocutors.csv",
                (row for row in enriched if row["speaker_role_group"] == "adult_interlocutor"),
                ALL_SPEAKER_COLUMNS,
            )
            _write_csv(
                child_dir / "chi.csv",
                _standard_rows(enriched, speakers={"CHI"}),
                PREPARED_CHAT_COLUMNS,
            )
            _write_csv(
                child_dir / "caretakers.csv",
                _standard_rows(enriched, speakers=FAMILY_CAREGIVER_CODES),
                PREPARED_CHAT_COLUMNS,
            )

            child_rows = [row for row in enriched if row["speaker_role_group"] == "target_child"]
            nonempty_child_rows = [row for row in child_rows if WORD_RE.search(str(row["utterance_clean"]))]
            comments = " ".join(document.comments).lower()
            reasons: list[str] = []
            if "transcript missing" in comments:
                reasons.append("missing_transcript")
            if "asr" in comments and ("revis" in comments or "check" in comments):
                reasons.append("unrevised_asr")
            if not child_rows:
                reasons.append("no_target_child_tier")
            elif not nonempty_child_rows:
                reasons.append("no_scorable_child_utterances")
            if demographics.conflict:
                reasons.append("demographic_conflict")
            if not demographics.sensitivity_eligible:
                reasons.append("missing_race_or_social_class")

            transcript_eligible = not any(
                reason in reasons
                for reason in (
                    "missing_transcript", "unrevised_asr", "no_target_child_tier",
                    "no_scorable_child_utterances", "demographic_conflict",
                    "missing_race_or_social_class",
                )
            )
            primary_eligible = transcript_eligible and demographics.primary_eligible
            sensitivity_eligible = transcript_eligible and demographics.sensitivity_eligible
            if primary_eligible:
                analysis_status = "primary"
            elif sensitivity_eligible:
                analysis_status = "sensitivity_only"
            else:
                analysis_status = "excluded"

            scoring_rows.extend(
                _hall_scoring_rows(
                    enriched,
                    demographics=demographics,
                    primary_eligible=primary_eligible,
                    sensitivity_eligible=sensitivity_eligible,
                )
            )

            inventory.append(
                {
                    "dataset": "Hall",
                    "child_id": document.child_id,
                    "source_group": source_group,
                    "source_file": file_label,
                    "raw_sha256": _sha256(path),
                    "age_raw": age_raw,
                    "age_months": age_months,
                    "sex": sex,
                    "race": demographics.race,
                    "social_class": demographics.social_class,
                    "stratum": demographics.stratum,
                    "demographic_source": demographics.source,
                    "demographic_scope": demographics.scope,
                    "demographic_conflict": int(demographics.conflict),
                    "main_tier_rows": len(enriched),
                    "target_child_rows": len(child_rows),
                    "target_child_nonempty_rows": len(nonempty_child_rows),
                    "adult_interlocutor_rows": sum(
                        row["speaker_role_group"] == "adult_interlocutor" for row in enriched
                    ),
                    "child_peer_rows": sum(row["speaker_role_group"] == "child_peer" for row in enriched),
                    "situation_count": len(document.situations),
                    "analysis_status": analysis_status,
                    "primary_eligible": int(primary_eligible),
                    "sensitivity_eligible": int(sensitivity_eligible),
                    "exclusion_reasons": " | ".join(reasons),
                }
            )
            metadata_rows.append(
                {
                    "dataset": "Hall",
                    "child_id": document.child_id,
                    "source_group": source_group,
                    "age_raw": age_raw,
                    "age_months": age_months,
                    "sex": sex,
                    "race": demographics.race,
                    "social_class": demographics.social_class,
                    "stratum": demographics.stratum,
                    "chi_id_ses_raw": document.child_id_ses_raw,
                    "metadata_csv_race": _normalized(meta.get("race", "")),
                    "metadata_csv_social_class": _normalized(meta.get("social_class", "")),
                    "demographic_source": demographics.source,
                    "demographic_scope": demographics.scope,
                    "demographic_conflict": int(demographics.conflict),
                    "primary_eligible": int(primary_eligible),
                    "sensitivity_eligible": int(sensitivity_eligible),
                    "analysis_status": analysis_status,
                }
            )

    _write_csv(report_root / "hall_file_inventory.csv", inventory, INVENTORY_COLUMNS)
    _write_csv(report_root / "hall_child_metadata.csv", metadata_rows, METADATA_COLUMNS)
    _write_csv(report_root / "hall_child_snapshot_scoring.csv", scoring_rows, SCORING_COLUMNS)

    problems: list[str] = []
    conflicts = [row["child_id"] for row in inventory if row["demographic_conflict"]]
    if conflicts:
        problems.append(f"demographic_conflicts:{','.join(map(str, conflicts))}")
    if duplicate_children:
        problems.append(f"duplicate_child_ids:{','.join(sorted(set(duplicate_children)))}")
    if not inventory:
        problems.append("no_chat_files")

    audit: dict[str, object] = {
        "status": "PASS" if not problems else "REVIEW",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "raw_root": str(raw_root),
        "output_root": str(output_root),
        "report_root": str(report_root),
        "counts": {
            "files": len(inventory),
            "main_tier_rows": all_main_rows,
            "snapshot_scoring_rows": len(scoring_rows),
            "snapshot_scoring_primary_rows": sum(int(row["primary_eligible"]) for row in scoring_rows),
            "snapshot_scoring_child_after_adult_rows": sum(int(row["child_after_adult"]) for row in scoring_rows),
            "primary_children": sum(int(row["primary_eligible"]) for row in inventory),
            "sensitivity_children": sum(int(row["sensitivity_eligible"]) for row in inventory),
            "excluded_children": sum(row["analysis_status"] == "excluded" for row in inventory),
            "demographic_conflicts": len(conflicts),
        },
        "problems": problems,
        "sample_definition": {
            "primary": "valid transcript plus child-specific race and social-class stratum",
            "sensitivity": "primary plus valid transcript with folder-inferred race/class stratum",
        },
    }
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "hall_preprocessing_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return audit


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    audit = prepare_hall_snapshot(
        raw_root=args.raw_root,
        output_root=args.output_root,
        report_root=args.report_root,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
