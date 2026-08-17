#!/usr/bin/env python3
"""Build auditable child-turn eligibility and next-response flags from CHAT.

The scorer-ready child tables retain source file and physical CHAT line
numbers, but they do not retain intervening non-caregiver speakers or
dependent-tier annotations. This builder reopens the immutable raw CHAT files,
aligns every scorer-ready child row to its original main tier, and records the
immediately adjacent main tiers without changing or filtering the source data.

The lexical discourse labels in this module are deliberately named
``*_candidate``. They are transparent rules for stratified manual validation,
not validated behavioral outcomes.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, TextIO

try:
    from cleaning import clean_chat_utterance
except ImportError:  # pragma: no cover - package-style import in tests
    from src.cleaning import clean_chat_utterance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_ROOT = (
    PROJECT_ROOT / "data/big_cleaned_dataset/default_naturalistic_merged_006_023"
)
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data/raw_data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results/conversational_eligibility"
DEFAULT_REPORT_MD = PROJECT_ROOT / "docs/conversational_eligibility_working_report.md"

CARETAKER_SPEAKERS = {"MOT", "FAT"}
CARETAKER_SPEAKERS_BY_DATASET = {"Lara": {"MOT", "FAT", "ELS"}}
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?")
WH_WORDS = {"what", "where", "when", "who", "whom", "whose", "which", "why", "how"}
POLAR_STARTS = {
    "am", "are", "is", "was", "were", "be", "can", "could", "did", "do", "does",
    "had", "has", "have", "may", "might", "must", "shall", "should", "will", "would",
}
BACKCHANNEL_FORMS = {
    "yes", "yeah", "yep", "yup", "no", "nope", "ok", "okay", "right", "mhm",
    "mm", "mm hm", "uh huh", "uhuh", "oh", "wow", "really",
}
CLARIFICATION_PATTERNS = (
    re.compile(r"\b(?:pardon|huh|what)\b", re.I),
    re.compile(r"\b(?:say|tell) (?:it |that )?again\b", re.I),
    re.compile(r"\bwhat did you (?:say|mean)\b", re.I),
    re.compile(r"\bi (?:did not|didn't|cannot|can't) (?:hear|understand)\b", re.I),
)
READING_PATTERNS = (
    re.compile(r"\bread(?:ing)?\b", re.I),
    re.compile(r"\b(?:book|story|stories)\b", re.I),
)
ROUTINE_PATTERNS = (
    re.compile(r"\b(?:bath|bedtime|bed time|meal|dinner|lunch|breakfast)\b", re.I),
    re.compile(r"\b(?:getting dressed|dressing|daily routine|routine)\b", re.I),
    re.compile(r"\b(?:song|singing|nursery rhyme)\b", re.I),
)
REPAIR_MARKERS = ("[/]", "[//]", "[///]", "[?]", "+//.", "+/.", "+...")


@dataclass(frozen=True)
class MainTier:
    line_no: int
    speaker: str
    utterance_raw: str
    utterance_clean: str


OUTPUT_COLUMNS = [
    "dataset", "child_id", "session_id", "age_months", "age_bin", "file", "line_no",
    "utt_id", "utterance_id", "chi_utterance_clean", "context_k1", "context_k2",
    "context_k3", "raw_source_path", "raw_source_resolved", "raw_line_aligned",
    "raw_target_text_matches", "child_utterance_raw", "previous_main_speaker",
    "previous_main_line_no", "previous_main_utterance_clean", "previous_main_is_caretaker",
    "previous_main_is_child", "previous_main_is_other", "nearest_previous_caretaker_speaker",
    "nearest_previous_caretaker_line_no", "turns_since_previous_caretaker",
    "context_k1_matches_nearest_caretaker", "primary_responsive_turn_eligible",
    "child_initiated_candidate", "exact_imitation_candidate", "contained_imitation_candidate",
    "child_backchannel_candidate", "child_acknowledgement_candidate", "child_question_type",
    "previous_caretaker_question_type", "session_reading_candidate",
    "session_routine_candidate", "child_retrace_repair_candidate",
    "previous_caregiver_clarification_candidate", "repair_sequence_candidate",
    "next_main_speaker", "next_main_line_no", "next_main_utterance_clean",
    "next_main_is_caretaker", "nearest_next_caretaker_speaker",
    "nearest_next_caretaker_line_no", "turns_until_next_caretaker",
    "next_caregiver_response_available", "next_caregiver_question_type",
    "next_caregiver_clarification_candidate", "next_caregiver_acknowledgement_candidate",
]

MANUAL_COLUMNS = OUTPUT_COLUMNS + [
    "sample_strata", "manual_genuine_response", "manual_imitation",
    "manual_routine_or_reading", "manual_backchannel_or_acknowledgement",
    "manual_repair_or_clarification", "manual_next_response_contingent", "manual_notes",
]


def _open_text(path: Path, mode: str = "rt") -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", newline="")
    return path.open(mode, encoding="utf-8", newline="")


def _bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "1" if value else "0"


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower().replace("’", "'") for match in WORD_RE.finditer(text or "")]


def _normalized(text: str) -> str:
    return " ".join(_tokens(text))


def _question_type(text: str) -> str:
    text = (text or "").strip()
    if not text.endswith("?"):
        return "not_question"
    tokens = _tokens(text)
    if not tokens:
        return "other_question"
    if tokens[0] in WH_WORDS:
        return "wh_question"
    if tokens[0] in POLAR_STARTS:
        return "polar_question"
    return "other_question"


def _age_bin(age_months: str) -> str:
    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return ""
    if 6 <= age < 24:
        return "006-023"
    for start in range(24, 66, 6):
        if start <= age < start + 6:
            return f"{start:03d}-{start + 5:03d}"
    return ""


def _backchannel_candidate(text: str) -> bool:
    normalized = _normalized(text)
    return len(normalized.split()) <= 2 and normalized in BACKCHANNEL_FORMS


def _clarification_candidate(text: str) -> bool:
    normalized = _normalized(text)
    return any(pattern.search(normalized) for pattern in CLARIFICATION_PATTERNS)


def _contained_imitation(child_text: str, caregiver_text: str) -> bool:
    child = _tokens(child_text)
    caregiver = _tokens(caregiver_text)
    if not child or not caregiver or child == caregiver or len(child) > len(caregiver):
        return False
    width = len(child)
    return any(caregiver[index : index + width] == child for index in range(len(caregiver) - width + 1))


def _session_candidates(metadata: str) -> tuple[bool, bool]:
    return (
        any(pattern.search(metadata) for pattern in READING_PATTERNS),
        any(pattern.search(metadata) for pattern in ROUTINE_PATTERNS),
    )


def parse_chat_main_tiers(path: Path) -> tuple[list[MainTier], str]:
    """Parse all CHAT main tiers plus compact session-description metadata."""

    tiers: list[MainTier] = []
    metadata: list[str] = []
    speaker = ""
    line_no = 0
    parts: list[str] = []

    def flush() -> None:
        nonlocal speaker, line_no, parts
        if not speaker:
            return
        raw = " ".join(part.strip() for part in parts if part.strip())
        tiers.append(MainTier(line_no, speaker, raw, clean_chat_utterance(raw)))
        speaker = ""
        line_no = 0
        parts = []

    with path.open(encoding="utf-8", errors="replace") as handle:
        for current_line, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\r\n")
            stripped = line.lstrip()
            if stripped.startswith("*") and ":" in stripped:
                flush()
                tier, utterance = stripped.split(":", 1)
                speaker = tier[1:].strip().upper()
                line_no = current_line
                parts = [utterance.strip()]
                continue
            if stripped.startswith("@Situation:") or stripped.startswith("@Activities:") or stripped.startswith("@Comment:"):
                metadata.append(stripped.split(":", 1)[1].strip())
            if speaker and line[:1].isspace() and not stripped.startswith(("%", "@")):
                parts.append(stripped)
                continue
            if speaker and stripped.startswith(("%", "@")):
                flush()
        flush()
    return tiers, " ".join(metadata)


def _resolve_manifest_path(bundle_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    direct = PROJECT_ROOT / path
    if direct.exists():
        return direct
    return bundle_root / path


def _nearest(tiers: list[MainTier], index: int, speakers: set[str], direction: int) -> tuple[MainTier | None, int | None]:
    cursor = index + direction
    intervening = 0
    while 0 <= cursor < len(tiers):
        if tiers[cursor].speaker in speakers:
            return tiers[cursor], intervening
        intervening += 1
        cursor += direction
    return None, None


def _row_key(row: dict[str, str]) -> str:
    return "|".join(row.get(column, "") for column in ("dataset", "child_id", "file", "line_no", "utt_id"))


def _strata(row: dict[str, str]) -> list[str]:
    strata: list[str] = []
    if row["primary_responsive_turn_eligible"] == "1":
        strata.append("eligible_random")
    if row["previous_main_is_child"] == "1":
        strata.append("previous_child")
    if row["previous_main_is_other"] == "1":
        strata.append("previous_other_speaker")
    for column in (
        "exact_imitation_candidate", "contained_imitation_candidate", "child_backchannel_candidate",
        "session_reading_candidate", "session_routine_candidate", "repair_sequence_candidate",
        "next_caregiver_clarification_candidate", "next_caregiver_acknowledgement_candidate",
    ):
        if row[column] == "1":
            strata.append(column)
    if row["next_caregiver_question_type"] not in {"", "not_question"}:
        strata.append("next_caregiver_question")
    if row["next_caregiver_response_available"] == "0":
        strata.append("no_immediate_next_caregiver")
    return strata


class StratifiedPrioritySample:
    def __init__(self, per_stratum: int, seed: int):
        self.per_stratum = per_stratum
        self.seed = seed
        self.heaps: dict[str, list[tuple[int, str, dict[str, str]]]] = defaultdict(list)

    def consider(self, row: dict[str, str]) -> None:
        key = _row_key(row)
        for stratum in _strata(row):
            digest = hashlib.sha256(f"{self.seed}|{stratum}|{key}".encode()).digest()
            priority = int.from_bytes(digest[:8], "big")
            item = (-priority, key, dict(row))
            heap = self.heaps[stratum]
            if len(heap) < self.per_stratum:
                heapq.heappush(heap, item)
            elif priority < -heap[0][0]:
                heapq.heapreplace(heap, item)

    def rows(self) -> list[dict[str, str]]:
        merged: dict[str, dict[str, str]] = {}
        memberships: dict[str, set[str]] = defaultdict(set)
        for stratum, heap in self.heaps.items():
            for _, key, row in heap:
                merged[key] = row
                memberships[key].add(stratum)
        output = []
        for key in sorted(merged):
            output.append(
                {
                    **merged[key],
                    "sample_strata": ";".join(sorted(memberships[key])),
                    "manual_genuine_response": "",
                    "manual_imitation": "",
                    "manual_routine_or_reading": "",
                    "manual_backchannel_or_acknowledgement": "",
                    "manual_repair_or_clarification": "",
                    "manual_next_response_contingent": "",
                    "manual_notes": "",
                }
            )
        return output


def _flag_row(
    source: dict[str, str],
    *,
    raw_path: Path,
    tiers: list[MainTier],
    line_index: dict[int, int],
    metadata: str,
    caretakers: set[str],
) -> dict[str, str]:
    try:
        source_line = int(float(source.get("line_no", "")))
    except ValueError:
        source_line = -1
    index = line_index.get(source_line)
    base = {column: source.get(column, "") for column in OUTPUT_COLUMNS}
    if not base["age_bin"]:
        base["age_bin"] = _age_bin(base["age_months"])
    base.update({"raw_source_path": str(raw_path), "raw_source_resolved": "1"})
    if index is None:
        base.update({"raw_line_aligned": "0", "raw_target_text_matches": "0"})
        return base

    current = tiers[index]
    previous = tiers[index - 1] if index > 0 else None
    following = tiers[index + 1] if index + 1 < len(tiers) else None
    previous_caregiver, previous_gap = _nearest(tiers, index, caretakers, -1)
    next_caregiver, next_gap = _nearest(tiers, index, caretakers, 1)
    reading, routine = _session_candidates(metadata)
    target = source.get("chi_utterance_clean", "")
    prev_clean = previous.utterance_clean if previous else ""
    prev_is_caregiver = previous is not None and previous.speaker in caretakers
    prev_is_child = previous is not None and previous.speaker == "CHI"
    prev_is_other = previous is not None and not prev_is_caregiver and not prev_is_child
    next_is_caregiver = following is not None and following.speaker in caretakers
    exact_imitation = prev_is_caregiver and _normalized(target) == _normalized(prev_clean) and bool(_normalized(target))
    contained_imitation = prev_is_caregiver and _contained_imitation(target, prev_clean)
    backchannel = _backchannel_candidate(target)
    child_repair = any(marker in current.utterance_raw for marker in REPAIR_MARKERS)
    previous_clarification = prev_is_caregiver and _clarification_candidate(prev_clean)
    next_clarification = next_is_caregiver and _clarification_candidate(following.utterance_clean)
    next_acknowledgement = next_is_caregiver and _backchannel_candidate(following.utterance_clean)

    base.update(
        {
            "raw_line_aligned": "1",
            "raw_target_text_matches": _bool(_normalized(target) == _normalized(current.utterance_clean)),
            "child_utterance_raw": current.utterance_raw,
            "previous_main_speaker": previous.speaker if previous else "",
            "previous_main_line_no": str(previous.line_no) if previous else "",
            "previous_main_utterance_clean": prev_clean,
            "previous_main_is_caretaker": _bool(prev_is_caregiver),
            "previous_main_is_child": _bool(prev_is_child),
            "previous_main_is_other": _bool(prev_is_other),
            "nearest_previous_caretaker_speaker": previous_caregiver.speaker if previous_caregiver else "",
            "nearest_previous_caretaker_line_no": str(previous_caregiver.line_no) if previous_caregiver else "",
            "turns_since_previous_caretaker": str(previous_gap) if previous_gap is not None else "",
            "context_k1_matches_nearest_caretaker": _bool(
                previous_caregiver is not None
                and _normalized(source.get("context_k1", "")) == _normalized(previous_caregiver.utterance_clean)
            ),
            "primary_responsive_turn_eligible": _bool(
                current.speaker == "CHI"
                and bool(_normalized(target))
                and prev_is_caregiver
                and bool(_normalized(source.get("context_k1", "")))
            ),
            "child_initiated_candidate": _bool(not prev_is_caregiver),
            "exact_imitation_candidate": _bool(exact_imitation),
            "contained_imitation_candidate": _bool(contained_imitation),
            "child_backchannel_candidate": _bool(backchannel),
            "child_acknowledgement_candidate": _bool(prev_is_caregiver and backchannel),
            "child_question_type": _question_type(target),
            "previous_caretaker_question_type": _question_type(prev_clean) if prev_is_caregiver else "",
            "session_reading_candidate": _bool(reading),
            "session_routine_candidate": _bool(routine),
            "child_retrace_repair_candidate": _bool(child_repair),
            "previous_caregiver_clarification_candidate": _bool(previous_clarification),
            "repair_sequence_candidate": _bool(child_repair or previous_clarification or bool(next_clarification)),
            "next_main_speaker": following.speaker if following else "",
            "next_main_line_no": str(following.line_no) if following else "",
            "next_main_utterance_clean": following.utterance_clean if following else "",
            "next_main_is_caretaker": _bool(next_is_caregiver),
            "nearest_next_caretaker_speaker": next_caregiver.speaker if next_caregiver else "",
            "nearest_next_caretaker_line_no": str(next_caregiver.line_no) if next_caregiver else "",
            "turns_until_next_caretaker": str(next_gap) if next_gap is not None else "",
            "next_caregiver_response_available": _bool(next_is_caregiver and bool(_normalized(following.utterance_clean))),
            "next_caregiver_question_type": _question_type(following.utterance_clean) if next_is_caregiver else "",
            "next_caregiver_clarification_candidate": _bool(bool(next_clarification)),
            "next_caregiver_acknowledgement_candidate": _bool(bool(next_acknowledgement)),
        }
    )
    return base


def _write_rows(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.tmp-{os.getpid()}{path.suffix}")
    count = 0
    try:
        with _open_text(temporary, "wt") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
                count += 1
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return count


def build_conversational_flags(
    *,
    bundle_root: Path,
    raw_root: Path,
    output_csv: Path,
    audit_json: Path,
    manual_sample_csv: Path,
    per_stratum: int = 25,
    seed: int = 20260722,
) -> dict[str, object]:
    manifest_path = bundle_root / "manifest.csv"
    sampler = StratifiedPrioritySample(per_stratum, seed)
    counts: Counter[str] = Counter()
    dataset_counts: dict[str, Counter[str]] = defaultdict(Counter)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_csv.with_name(
        f".{output_csv.stem}.tmp-{os.getpid()}{output_csv.suffix}"
    )
    try:
        with manifest_path.open(newline="", encoding="utf-8") as manifest_handle, _open_text(temporary, "wt") as output_handle:
            writer = csv.DictWriter(output_handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            for unit in csv.DictReader(manifest_handle):
                if unit.get("child_scoring_ready") != "1":
                    continue
                dataset = unit.get("dataset", "")
                caretakers = CARETAKER_SPEAKERS_BY_DATASET.get(dataset, CARETAKER_SPEAKERS)
                scoring_csv = _resolve_manifest_path(bundle_root, unit.get("child_scoring_csv", ""))
                grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
                with scoring_csv.open(newline="", encoding="utf-8") as scoring_handle:
                    for row in csv.DictReader(scoring_handle):
                        grouped[row.get("file", "")].append(dict(row))
                for file_label, source_rows in grouped.items():
                    raw_path = raw_root / dataset / file_label
                    if not raw_path.is_file():
                        for source in source_rows:
                            flagged = {column: source.get(column, "") for column in OUTPUT_COLUMNS}
                            flagged.update({"raw_source_path": str(raw_path), "raw_source_resolved": "0", "raw_line_aligned": "0"})
                            writer.writerow(flagged)
                            sampler.consider(flagged)
                            counts["rows"] += 1
                            counts["unresolved_raw_rows"] += 1
                            dataset_counts[dataset]["rows"] += 1
                            dataset_counts[dataset]["unresolved_raw_rows"] += 1
                        continue
                    tiers, metadata = parse_chat_main_tiers(raw_path)
                    line_index = {tier.line_no: index for index, tier in enumerate(tiers)}
                    counts["raw_files"] += 1
                    dataset_counts[dataset]["raw_files"] += 1
                    for source in source_rows:
                        flagged = _flag_row(
                            source,
                            raw_path=raw_path,
                            tiers=tiers,
                            line_index=line_index,
                            metadata=metadata,
                            caretakers=caretakers,
                        )
                        writer.writerow(flagged)
                        sampler.consider(flagged)
                        counts["rows"] += 1
                        dataset_counts[dataset]["rows"] += 1
                        for column in OUTPUT_COLUMNS:
                            if flagged.get(column) == "1" and column not in {
                                "session_id", "utt_id", "line_no", "previous_main_line_no",
                                "nearest_previous_caretaker_line_no", "next_main_line_no",
                                "nearest_next_caretaker_line_no", "turns_since_previous_caretaker",
                                "turns_until_next_caretaker",
                            }:
                                counts[column] += 1
                                dataset_counts[dataset][column] += 1
                        if (
                            flagged["primary_responsive_turn_eligible"] == "1"
                            and flagged["context_k1_matches_nearest_caretaker"] != "1"
                        ):
                            counts["eligible_context_k1_mismatches"] += 1
                            dataset_counts[dataset]["eligible_context_k1_mismatches"] += 1
        os.replace(temporary, output_csv)
    finally:
        temporary.unlink(missing_ok=True)

    manual_rows = sampler.rows()
    _write_rows(manual_sample_csv, MANUAL_COLUMNS, manual_rows)
    audit_passed = (
        counts["unresolved_raw_rows"] == 0
        and counts["raw_line_aligned"] == counts["rows"]
        and counts["raw_target_text_matches"] == counts["rows"]
        and counts["eligible_context_k1_mismatches"] == 0
    )
    audit: dict[str, object] = {
        "status": "PASS" if audit_passed else "REVIEW",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_root": str(bundle_root.resolve()),
        "raw_root": str(raw_root.resolve()),
        "output_csv": str(output_csv),
        "manual_sample_csv": str(manual_sample_csv),
        "sample_seed": seed,
        "sample_per_stratum": per_stratum,
        "manual_sample_rows": len(manual_rows),
        "counts": dict(sorted(counts.items())),
        "by_dataset": {dataset: dict(sorted(values.items())) for dataset, values in sorted(dataset_counts.items())},
        "definitions": {
            "primary_responsive_turn_eligible": "nonempty CHI target whose immediately previous raw CHAT main tier is an allowed caregiver and whose scorer context_k1 is nonempty",
            "next_caregiver_response_available": "nonempty allowed-caregiver main tier immediately after the child main tier",
            "candidate_suffix": "transparent lexical or CHAT-marker heuristic requiring manual validation",
        },
    }
    audit_json.parent.mkdir(parents=True, exist_ok=True)
    audit_json.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def render_report(audit: dict[str, object], path: Path) -> None:
    counts = audit["counts"]
    assert isinstance(counts, dict)
    rows = int(counts.get("rows", 0))
    eligible = int(counts.get("primary_responsive_turn_eligible", 0))
    next_response = int(counts.get("next_caregiver_response_available", 0))
    lines = [
        "# Conversational Eligibility and Listener-Outcome Working Sample",
        "",
        "Generated from immutable raw CHAT main-tier adjacency and the current full-79 scorer-ready child rows.",
        "",
        "## Audit",
        "",
        f"- status: `{audit['status']}`",
        f"- child rows: `{rows:,}`",
        f"- raw CHAT files: `{int(counts.get('raw_files', 0)):,}`",
        f"- raw-line alignments: `{int(counts.get('raw_line_aligned', 0)):,}`",
        f"- unresolved raw rows: `{int(counts.get('unresolved_raw_rows', 0)):,}`",
        f"- primary immediate-caregiver response rows: `{eligible:,}` ({eligible / rows:.1%})" if rows else "- primary immediate-caregiver response rows: `0`",
        f"- rows with an immediate next caregiver response: `{next_response:,}` ({next_response / rows:.1%})" if rows else "- rows with an immediate next caregiver response: `0`",
        f"- manual validation rows: `{audit['manual_sample_rows']:,}`",
        "",
        "## Interpretation Boundary",
        "",
        "The primary eligibility flag is structural: a nonempty child main tier immediately follows an allowed caregiver main tier in the same raw CHAT file, and the scorer's k1 caregiver context is nonempty. It does not assume that the child turn is semantically contingent.",
        "",
        "Imitation, routines/reading, backchannels, repair/clarification, acknowledgement, and question-type columns are named candidates because they are rule-based screening labels. The stratified manual-review CSV must be coded before any of these becomes an exclusion or listener-utility outcome.",
        "",
        "The immediate next-caregiver text enables a downstream predictive-gain prototype without calling caregiver input an adult endpoint. No predictive model is fit by this builder.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--manual-per-stratum", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20260722)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_csv = args.output_dir / "full79_child_conversational_flags.csv.gz"
    audit_json = args.output_dir / "full79_child_conversational_flags.audit.json"
    manual_csv = args.output_dir / "full79_conversational_manual_validation_sample.csv"
    audit = build_conversational_flags(
        bundle_root=args.bundle_root,
        raw_root=args.raw_root,
        output_csv=output_csv,
        audit_json=audit_json,
        manual_sample_csv=manual_csv,
        per_stratum=args.manual_per_stratum,
        seed=args.seed,
    )
    render_report(audit, args.report_md)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
