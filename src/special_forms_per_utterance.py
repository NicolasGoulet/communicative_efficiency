#!/usr/bin/env python3
"""
Count CHAT special @ forms in the utterances used by the Stage 0 cleaner.

The script reads raw CHAT files through the same discovery and cleaning path as
prepare_datasets.py, then reports how often special @ forms occur in usable
CHI/MOT/FAT main-tier utterances.

Default outputs are written to results/special_forms/<run_name>/:
- special_forms_per_utterance.csv
- special_forms_by_dataset_speaker_marker.csv
- special_forms_by_age_bin_marker.csv
- special_forms_by_full_code.csv
- special_form_examples.csv
- metadata.txt
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from prepare_datasets import (
    DATASETS,
    PROJECT_ROOT,
    ChatUnit,
    discover_dataset_units,
    prepared_rows_for_unit,
    resolve_base_dir,
)


DEFAULT_DATASETS = ("Brown", "Manchester", "Providence")
DEFAULT_SPEAKERS = ("CHI", "MOT", "FAT")

SPECIAL_FORM_LABELS = {
    "b": "babbling",
    "c": "child_invented",
    "d": "dialect",
    "f": "family_specific",
    "i": "interjection",
    "k": "multiple_letters",
    "l": "letter",
    "ls": "letter_plural",
    "n": "neologism",
    "o": "onomatopoeia",
    "p": "phonologically_consistent_form",
    "wp": "word_play",
}
DEFAULT_MARKERS = tuple(SPECIAL_FORM_LABELS)

EDGE_PUNCT = " \t\r\n.,!?;:\"'()[]{}<>"
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
LEADING_ALPHA_RE = re.compile(r"^[A-Za-z]+")


@dataclass(frozen=True)
class SpecialForm:
    """One raw token containing a CHAT @ special-form suffix."""

    raw_token: str
    lexical_base: str
    marker_code: str
    marker_family: str


@dataclass
class SpecialFormReport:
    """In-memory report tables and counters before CSV writing."""

    utterance_rows: List[Dict[str, object]] = field(default_factory=list)
    examples: List[Dict[str, object]] = field(default_factory=list)
    group_totals: Counter = field(default_factory=Counter)
    group_any_at_utts: Counter = field(default_factory=Counter)
    group_target_utts: Counter = field(default_factory=Counter)
    group_any_at_tokens: Counter = field(default_factory=Counter)
    group_target_tokens: Counter = field(default_factory=Counter)
    group_marker_token_counts: Counter = field(default_factory=Counter)
    group_marker_utt_counts: Counter = field(default_factory=Counter)
    full_code_token_counts: Counter = field(default_factory=Counter)
    full_code_utt_counts: Counter = field(default_factory=Counter)
    age_totals: Counter = field(default_factory=Counter)
    age_marker_token_counts: Counter = field(default_factory=Counter)
    age_marker_utt_counts: Counter = field(default_factory=Counter)
    datasets_seen: Counter = field(default_factory=Counter)


def parse_csv_list(value: str) -> Tuple[str, ...]:
    """Parse comma-separated CLI lists while rejecting empty values."""
    parts = tuple(part.strip() for part in value.split(",") if part.strip())
    if not parts:
        raise argparse.ArgumentTypeError("expected at least one comma-separated value")
    return parts


def parse_dataset_list(value: str) -> Tuple[str, ...]:
    """Parse --datasets, accepting all as a shortcut."""
    if value.strip().lower() == "all":
        return tuple(DATASETS)

    datasets = parse_csv_list(value)
    unknown = [dataset for dataset in datasets if dataset not in DATASETS]
    if unknown:
        known = ", ".join((*DATASETS, "all"))
        raise argparse.ArgumentTypeError(
            f"unknown dataset(s): {', '.join(unknown)}; expected one of {known}"
        )
    return datasets


def parse_marker_list(value: str) -> Tuple[str, ...]:
    """Parse marker families such as f,c,d,b,i,k,l,ls,n,o,p,wp."""
    markers = tuple(marker.strip().lower() for marker in value.split(",") if marker.strip())
    if not markers:
        raise argparse.ArgumentTypeError("expected at least one marker")
    return markers


def cleaned_word_count(text: object) -> int:
    """Count lightweight word tokens in utterance_clean for report context."""
    return len(WORD_RE.findall("" if text is None else str(text)))


def speaker_group_for(speaker: object) -> str:
    """Collapse CHAT speaker tiers into the analysis split used in reports."""
    code = str(speaker).upper()
    if code == "CHI":
        return "CHILD"
    if code in {"MOT", "FAT"}:
        return "CARETAKERS"
    return code


def age_bin_label(age_months: object, width: int) -> str:
    """Return a stable age-bin label such as 24_30, or empty if age is missing."""
    if age_months in (None, ""):
        return ""
    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return ""
    lo = int(age // width) * width
    hi = lo + width
    return f"{lo}_{hi}"


def _normalize_at_token(raw_token: str) -> str:
    return raw_token.strip(EDGE_PUNCT)


def extract_special_forms(utterance: object) -> List[SpecialForm]:
    """
    Extract CHAT @ special-form suffixes from one raw main-tier utterance.

    marker_code is the exact suffix before optional POS coding, so
    dumpf@n$v -> n and word@z:rftd -> z:rftd. marker_family is the leading
    alphabetic run, so istemem@s:hu -> s and no@q-s -> q.
    """
    if utterance is None:
        return []

    forms: List[SpecialForm] = []
    for raw_token in str(utterance).split():
        token = _normalize_at_token(raw_token)
        if "@" not in token:
            continue

        lexical_base, suffix = token.rsplit("@", 1)
        lexical_base = lexical_base.strip(EDGE_PUNCT)
        suffix = suffix.strip(EDGE_PUNCT)
        if not lexical_base or not suffix:
            continue

        marker_code = suffix.split("$", 1)[0].lower()
        if not marker_code:
            continue

        family_match = LEADING_ALPHA_RE.match(marker_code)
        marker_family = family_match.group(0).lower() if family_match else marker_code
        forms.append(
            SpecialForm(
                raw_token=token,
                lexical_base=lexical_base,
                marker_code=marker_code,
                marker_family=marker_family,
            )
        )

    return forms


def iter_dataset_units(datasets: Sequence[str]) -> Iterator[Tuple[str, List[ChatUnit], Path]]:
    """Yield discovered raw CHAT units for each requested dataset."""
    for dataset in datasets:
        raw_base = resolve_base_dir(dataset, None)
        if not raw_base.exists():
            raise FileNotFoundError(f"Raw base directory not found for {dataset}: {raw_base}")
        units = discover_dataset_units(dataset, raw_base)
        if not units:
            raise FileNotFoundError(f"No .cha files found for {dataset} under {raw_base}")
        yield dataset, units, raw_base


def _format_marker_counts(marker_counts: Counter, markers: Sequence[str]) -> Dict[str, int]:
    return {f"n_at_{marker}": int(marker_counts.get(marker, 0)) for marker in markers}


def analyze_units(
    units: Sequence[ChatUnit],
    *,
    speakers: Sequence[str] = DEFAULT_SPEAKERS,
    markers: Sequence[str] = DEFAULT_MARKERS,
    age_bin_width: int = 6,
    include_empty_cleaned: bool = False,
    min_cleaned_words: int = 1,
    utterance_mode: str = "all",
    examples_per_marker: int = 20,
) -> SpecialFormReport:
    """
    Analyze already-discovered CHAT units and return report tables.

    By default this excludes utterances whose cleaned text is empty, matching
    the rows that should not be scored downstream.
    """
    speaker_set = {speaker.upper() for speaker in speakers}
    marker_set = {marker.lower() for marker in markers}
    example_counts: Counter = Counter()
    report = SpecialFormReport()

    for unit in units:
        dataset = unit.dataset
        for row in prepared_rows_for_unit(unit):
            speaker = str(row["speaker"]).upper()
            if speaker not in speaker_set:
                continue
            word_count = cleaned_word_count(row["utterance_clean"])
            if not include_empty_cleaned and word_count < min_cleaned_words:
                continue

            forms = extract_special_forms(row["utterance"])
            marker_counts = Counter(form.marker_family for form in forms)
            target_counts = Counter(
                {marker: count for marker, count in marker_counts.items() if marker in marker_set}
            )
            full_code_counts = Counter(form.marker_code for form in forms)
            n_any_at = sum(marker_counts.values())
            n_target = sum(target_counts.values())
            if utterance_mode == "with-special" and n_target == 0:
                continue

            speaker_group = speaker_group_for(speaker)
            age_bin = age_bin_label(row["age_months"], age_bin_width)
            group_key = (dataset, speaker)
            age_key = (dataset, speaker, age_bin)

            report.datasets_seen[dataset] += 1
            report.group_totals[group_key] += 1
            report.group_any_at_tokens[group_key] += n_any_at
            report.group_target_tokens[group_key] += n_target
            if n_any_at:
                report.group_any_at_utts[group_key] += 1
            if n_target:
                report.group_target_utts[group_key] += 1
            if age_bin:
                report.age_totals[age_key] += 1

            for marker, count in marker_counts.items():
                report.group_marker_token_counts[(dataset, speaker, marker)] += count
                report.group_marker_utt_counts[(dataset, speaker, marker)] += 1
                if age_bin:
                    report.age_marker_token_counts[(dataset, speaker, age_bin, marker)] += count
                    report.age_marker_utt_counts[(dataset, speaker, age_bin, marker)] += 1

            for code, count in full_code_counts.items():
                report.full_code_token_counts[(dataset, speaker, code)] += count
                report.full_code_utt_counts[(dataset, speaker, code)] += 1

            marker_text = ";".join(sorted(marker_counts))
            token_text = ";".join(form.raw_token for form in forms)
            base_text = ";".join(form.lexical_base for form in forms)
            utterance_record = {
                "dataset": dataset,
                "child_id": row["child_id"],
                "source_group": row["source_group"],
                "session_id": row["session_id"],
                "age_raw": row["age_raw"],
                "age_months": row["age_months"],
                "age_bin": age_bin,
                "sex": row["sex"],
                "file": row["file"],
                "line_no": row["line_no"],
                "reference_line": row["reference_line"],
                "utt_id": row["utt_id"],
                "utt_id_role": row["utt_id_role"],
                "speaker": speaker,
                "speaker_group": speaker_group,
                "utterance": row["utterance"],
                "utterance_clean": row["utterance_clean"],
                "cleaned_word_count": word_count,
                "n_at_form_tokens": n_any_at,
                "n_target_special_form_tokens": n_target,
                "has_at_form": int(n_any_at > 0),
                "has_target_special_form": int(n_target > 0),
                "special_form_marker_families": marker_text,
                "special_form_raw_tokens": token_text,
                "special_form_lexical_bases": base_text,
            }
            utterance_record.update(_format_marker_counts(target_counts, markers))
            report.utterance_rows.append(utterance_record)

            for form in forms:
                if form.marker_family not in marker_set:
                    continue
                if example_counts[form.marker_family] >= examples_per_marker:
                    continue
                example_counts[form.marker_family] += 1
                report.examples.append(
                    {
                        "marker": form.marker_family,
                        "marker_label": SPECIAL_FORM_LABELS.get(form.marker_family, ""),
                        "raw_token": form.raw_token,
                        "lexical_base": form.lexical_base,
                        "dataset": dataset,
                        "child_id": row["child_id"],
                        "speaker": speaker,
                        "speaker_group": speaker_group,
                        "age_months": row["age_months"],
                        "reference_line": row["reference_line"],
                        "utterance": row["utterance"],
                        "utterance_clean": row["utterance_clean"],
                    }
                )

    return report


def analyze_datasets(
    datasets: Sequence[str],
    *,
    speakers: Sequence[str] = DEFAULT_SPEAKERS,
    markers: Sequence[str] = DEFAULT_MARKERS,
    age_bin_width: int = 6,
    include_empty_cleaned: bool = False,
    min_cleaned_words: int = 1,
    utterance_mode: str = "all",
    examples_per_marker: int = 20,
) -> Tuple[SpecialFormReport, Dict[str, Path]]:
    """Discover and analyze raw CHAT units for the requested datasets."""
    report = SpecialFormReport()
    raw_bases: Dict[str, Path] = {}

    for dataset, units, raw_base in iter_dataset_units(datasets):
        raw_bases[dataset] = raw_base
        dataset_report = analyze_units(
            units,
            speakers=speakers,
            markers=markers,
            age_bin_width=age_bin_width,
            include_empty_cleaned=include_empty_cleaned,
            min_cleaned_words=min_cleaned_words,
            utterance_mode=utterance_mode,
            examples_per_marker=examples_per_marker,
        )
        merge_reports(report, dataset_report)

    return report, raw_bases


def merge_reports(target: SpecialFormReport, source: SpecialFormReport) -> None:
    """Merge one dataset-level report into the global report."""
    target.utterance_rows.extend(source.utterance_rows)
    target.examples.extend(source.examples)
    for name in (
        "group_totals",
        "group_any_at_utts",
        "group_target_utts",
        "group_any_at_tokens",
        "group_target_tokens",
        "group_marker_token_counts",
        "group_marker_utt_counts",
        "full_code_token_counts",
        "full_code_utt_counts",
        "age_totals",
        "age_marker_token_counts",
        "age_marker_utt_counts",
        "datasets_seen",
    ):
        getattr(target, name).update(getattr(source, name))


def marker_summary_rows(report: SpecialFormReport, markers: Sequence[str]) -> List[Dict[str, object]]:
    """Build tall summary rows by dataset, speaker, and marker family."""
    rows: List[Dict[str, object]] = []
    marker_set = set(markers)
    keys = set(report.group_marker_token_counts)
    for dataset, speaker in report.group_totals:
        for marker in marker_set:
            keys.add((dataset, speaker, marker))

    for dataset, speaker, marker in sorted(keys):
        group_key = (dataset, speaker)
        total_utts = report.group_totals[group_key]
        utts = report.group_marker_utt_counts[(dataset, speaker, marker)]
        tokens = report.group_marker_token_counts[(dataset, speaker, marker)]
        rows.append(
            {
                "dataset": dataset,
                "speaker": speaker,
                "marker": marker,
                "marker_label": SPECIAL_FORM_LABELS.get(marker, ""),
                "is_target_marker": int(marker in marker_set),
                "total_usable_utterances": total_utts,
                "utterances_with_marker": utts,
                "marker_token_occurrences": tokens,
                "utterance_rate": _safe_rate(utts, total_utts),
                "mean_tokens_per_utterance": _safe_rate(tokens, total_utts),
            }
        )
    return rows


def age_summary_rows(report: SpecialFormReport, markers: Sequence[str]) -> List[Dict[str, object]]:
    """Build tall summary rows by dataset, speaker, age bin, and marker."""
    rows: List[Dict[str, object]] = []
    marker_set = set(markers)
    for dataset, speaker, age_bin, marker in sorted(report.age_marker_token_counts):
        total_utts = report.age_totals[(dataset, speaker, age_bin)]
        utts = report.age_marker_utt_counts[(dataset, speaker, age_bin, marker)]
        tokens = report.age_marker_token_counts[(dataset, speaker, age_bin, marker)]
        rows.append(
            {
                "dataset": dataset,
                "speaker": speaker,
                "age_bin": age_bin,
                "age_mid": _age_mid(age_bin),
                "marker": marker,
                "marker_label": SPECIAL_FORM_LABELS.get(marker, ""),
                "is_target_marker": int(marker in marker_set),
                "total_usable_utterances": total_utts,
                "utterances_with_marker": utts,
                "marker_token_occurrences": tokens,
                "utterance_rate": _safe_rate(utts, total_utts),
                "mean_tokens_per_utterance": _safe_rate(tokens, total_utts),
            }
        )
    return rows


def full_code_rows(report: SpecialFormReport, markers: Sequence[str]) -> List[Dict[str, object]]:
    """Build observed exact-code rows such as s:hu, q-s, or z:rftd."""
    rows: List[Dict[str, object]] = []
    marker_set = set(markers)
    for dataset, speaker, marker_code in sorted(report.full_code_token_counts):
        total_utts = report.group_totals[(dataset, speaker)]
        utts = report.full_code_utt_counts[(dataset, speaker, marker_code)]
        tokens = report.full_code_token_counts[(dataset, speaker, marker_code)]
        family_match = LEADING_ALPHA_RE.match(marker_code)
        marker_family = family_match.group(0).lower() if family_match else marker_code
        rows.append(
            {
                "dataset": dataset,
                "speaker": speaker,
                "marker_code": marker_code,
                "marker_family": marker_family,
                "marker_label": SPECIAL_FORM_LABELS.get(marker_family, ""),
                "is_target_marker": int(marker_family in marker_set),
                "total_usable_utterances": total_utts,
                "utterances_with_code": utts,
                "code_token_occurrences": tokens,
                "utterance_rate": _safe_rate(utts, total_utts),
            }
        )
    return rows


def group_summary_rows(report: SpecialFormReport) -> List[Dict[str, object]]:
    """Build broad denominator rows by dataset and speaker."""
    rows: List[Dict[str, object]] = []
    for dataset, speaker in sorted(report.group_totals):
        group_key = (dataset, speaker)
        total = report.group_totals[group_key]
        any_utts = report.group_any_at_utts[group_key]
        target_utts = report.group_target_utts[group_key]
        any_tokens = report.group_any_at_tokens[group_key]
        target_tokens = report.group_target_tokens[group_key]
        rows.append(
            {
                "dataset": dataset,
                "speaker": speaker,
                "total_usable_utterances": total,
                "utterances_with_any_at_form": any_utts,
                "utterances_with_target_special_form": target_utts,
                "any_at_form_utterance_rate": _safe_rate(any_utts, total),
                "target_special_form_utterance_rate": _safe_rate(target_utts, total),
                "any_at_form_token_occurrences": any_tokens,
                "target_special_form_token_occurrences": target_tokens,
                "mean_target_special_forms_per_utterance": _safe_rate(target_tokens, total),
            }
        )
    return rows


def speaker_group_summary_rows(report: SpecialFormReport) -> List[Dict[str, object]]:
    """Build broad denominator rows by dataset and CHILD/CARETAKERS group."""
    aggregates: Dict[Tuple[str, str], Counter] = defaultdict_counter()
    for row in report.utterance_rows:
        key = (str(row["dataset"]), str(row["speaker_group"]))
        aggregates[key]["total_usable_utterances"] += 1
        aggregates[key]["utterances_with_any_at_form"] += int(row["has_at_form"])
        aggregates[key]["utterances_with_target_special_form"] += int(row["has_target_special_form"])
        aggregates[key]["any_at_form_token_occurrences"] += int(row["n_at_form_tokens"])
        aggregates[key]["target_special_form_token_occurrences"] += int(row["n_target_special_form_tokens"])

    rows: List[Dict[str, object]] = []
    for (dataset, speaker_group), counts in sorted(aggregates.items()):
        total = counts["total_usable_utterances"]
        target_tokens = counts["target_special_form_token_occurrences"]
        rows.append(
            {
                "dataset": dataset,
                "speaker_group": speaker_group,
                "total_usable_utterances": total,
                "utterances_with_any_at_form": counts["utterances_with_any_at_form"],
                "utterances_with_target_special_form": counts["utterances_with_target_special_form"],
                "any_at_form_utterance_rate": _safe_rate(counts["utterances_with_any_at_form"], total),
                "target_special_form_utterance_rate": _safe_rate(
                    counts["utterances_with_target_special_form"], total
                ),
                "any_at_form_token_occurrences": counts["any_at_form_token_occurrences"],
                "target_special_form_token_occurrences": target_tokens,
                "mean_target_special_forms_per_utterance": _safe_rate(target_tokens, total),
            }
        )
    return rows


def speaker_group_marker_summary_rows(
    report: SpecialFormReport, markers: Sequence[str]
) -> List[Dict[str, object]]:
    """Build target-marker rows by dataset and CHILD/CARETAKERS group."""
    totals: Counter = Counter()
    token_counts: Counter = Counter()
    utt_counts: Counter = Counter()

    for row in report.utterance_rows:
        group_key = (str(row["dataset"]), str(row["speaker_group"]))
        totals[group_key] += 1
        for marker in markers:
            count = int(row.get(f"n_at_{marker}", 0))
            token_counts[(*group_key, marker)] += count
            if count:
                utt_counts[(*group_key, marker)] += 1

    rows: List[Dict[str, object]] = []
    for dataset, speaker_group in sorted(totals):
        total = totals[(dataset, speaker_group)]
        for marker in markers:
            key = (dataset, speaker_group, marker)
            tokens = token_counts[key]
            utts = utt_counts[key]
            rows.append(
                {
                    "dataset": dataset,
                    "speaker_group": speaker_group,
                    "marker": marker,
                    "marker_label": SPECIAL_FORM_LABELS.get(marker, ""),
                    "total_usable_utterances": total,
                    "utterances_with_marker": utts,
                    "marker_token_occurrences": tokens,
                    "utterance_rate": _safe_rate(utts, total),
                    "mean_tokens_per_utterance": _safe_rate(tokens, total),
                }
            )
    return rows


def age_speaker_group_marker_summary_rows(
    report: SpecialFormReport, markers: Sequence[str]
) -> List[Dict[str, object]]:
    """Build target-marker rows by dataset, CHILD/CARETAKERS group, and age bin."""
    totals: Counter = Counter()
    token_counts: Counter = Counter()
    utt_counts: Counter = Counter()

    for row in report.utterance_rows:
        age_bin = str(row["age_bin"])
        if not age_bin:
            continue
        group_key = (str(row["dataset"]), str(row["speaker_group"]), age_bin)
        totals[group_key] += 1
        for marker in markers:
            count = int(row.get(f"n_at_{marker}", 0))
            token_counts[(*group_key, marker)] += count
            if count:
                utt_counts[(*group_key, marker)] += 1

    rows: List[Dict[str, object]] = []
    for dataset, speaker_group, age_bin in sorted(totals):
        total = totals[(dataset, speaker_group, age_bin)]
        for marker in markers:
            key = (dataset, speaker_group, age_bin, marker)
            tokens = token_counts[key]
            utts = utt_counts[key]
            rows.append(
                {
                    "dataset": dataset,
                    "speaker_group": speaker_group,
                    "age_bin": age_bin,
                    "age_mid": _age_mid(age_bin),
                    "marker": marker,
                    "marker_label": SPECIAL_FORM_LABELS.get(marker, ""),
                    "total_usable_utterances": total,
                    "utterances_with_marker": utts,
                    "marker_token_occurrences": tokens,
                    "utterance_rate": _safe_rate(utts, total),
                    "mean_tokens_per_utterance": _safe_rate(tokens, total),
                }
            )
    return rows


def write_csv_rows(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    """Write rows with stable quoting and empty strings for None."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field) for field in fieldnames})


def write_report(
    report: SpecialFormReport,
    out_dir: Path,
    *,
    markers: Sequence[str],
    datasets: Sequence[str],
    speakers: Sequence[str],
    raw_bases: Dict[str, Path],
    age_bin_width: int,
    include_empty_cleaned: bool,
    min_cleaned_words: int,
    utterance_mode: str,
) -> None:
    """Write all CSV and metadata outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)

    utterance_fields = [
        "dataset",
        "child_id",
        "source_group",
        "session_id",
        "age_raw",
        "age_months",
        "age_bin",
        "sex",
        "file",
        "line_no",
        "reference_line",
        "utt_id",
        "utt_id_role",
        "speaker",
        "speaker_group",
        "utterance",
        "utterance_clean",
        "cleaned_word_count",
        "n_at_form_tokens",
        "n_target_special_form_tokens",
        "has_at_form",
        "has_target_special_form",
        "special_form_marker_families",
        "special_form_raw_tokens",
        "special_form_lexical_bases",
        *[f"n_at_{marker}" for marker in markers],
    ]
    write_csv_rows(out_dir / "special_forms_per_utterance.csv", report.utterance_rows, utterance_fields)

    write_csv_rows(
        out_dir / "special_forms_by_dataset_speaker.csv",
        group_summary_rows(report),
        [
            "dataset",
            "speaker",
            "total_usable_utterances",
            "utterances_with_any_at_form",
            "utterances_with_target_special_form",
            "any_at_form_utterance_rate",
            "target_special_form_utterance_rate",
            "any_at_form_token_occurrences",
            "target_special_form_token_occurrences",
            "mean_target_special_forms_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "special_forms_by_dataset_speaker_group.csv",
        speaker_group_summary_rows(report),
        [
            "dataset",
            "speaker_group",
            "total_usable_utterances",
            "utterances_with_any_at_form",
            "utterances_with_target_special_form",
            "any_at_form_utterance_rate",
            "target_special_form_utterance_rate",
            "any_at_form_token_occurrences",
            "target_special_form_token_occurrences",
            "mean_target_special_forms_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "special_forms_by_dataset_speaker_marker.csv",
        marker_summary_rows(report, markers),
        [
            "dataset",
            "speaker",
            "marker",
            "marker_label",
            "is_target_marker",
            "total_usable_utterances",
            "utterances_with_marker",
            "marker_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "special_forms_by_dataset_speaker_group_marker.csv",
        speaker_group_marker_summary_rows(report, markers),
        [
            "dataset",
            "speaker_group",
            "marker",
            "marker_label",
            "total_usable_utterances",
            "utterances_with_marker",
            "marker_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "special_forms_by_age_bin_marker.csv",
        age_summary_rows(report, markers),
        [
            "dataset",
            "speaker",
            "age_bin",
            "age_mid",
            "marker",
            "marker_label",
            "is_target_marker",
            "total_usable_utterances",
            "utterances_with_marker",
            "marker_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "special_forms_by_age_bin_speaker_group_marker.csv",
        age_speaker_group_marker_summary_rows(report, markers),
        [
            "dataset",
            "speaker_group",
            "age_bin",
            "age_mid",
            "marker",
            "marker_label",
            "total_usable_utterances",
            "utterances_with_marker",
            "marker_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "special_forms_by_full_code.csv",
        full_code_rows(report, markers),
        [
            "dataset",
            "speaker",
            "marker_code",
            "marker_family",
            "marker_label",
            "is_target_marker",
            "total_usable_utterances",
            "utterances_with_code",
            "code_token_occurrences",
            "utterance_rate",
        ],
    )
    write_csv_rows(
        out_dir / "special_form_examples.csv",
        report.examples,
        [
            "marker",
            "marker_label",
            "raw_token",
            "lexical_base",
            "dataset",
            "child_id",
            "speaker",
            "speaker_group",
            "age_months",
            "reference_line",
            "utterance",
            "utterance_clean",
        ],
    )

    metadata = [
        "Special CHAT @ form report",
        f"datasets: {', '.join(datasets)}",
        f"speakers: {', '.join(speakers)}",
        f"markers: {', '.join(markers)}",
        f"age_bin_width_months: {age_bin_width}",
        f"include_empty_cleaned: {include_empty_cleaned}",
        f"min_cleaned_words: {min_cleaned_words}",
        f"utterance_mode: {utterance_mode}",
        f"total_report_rows: {len(report.utterance_rows)}",
        "raw_bases:",
        *[f"  {dataset}: {raw_bases[dataset]}" for dataset in sorted(raw_bases)],
    ]
    (out_dir / "metadata.txt").write_text("\n".join(metadata) + "\n", encoding="utf-8")


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 8)


def defaultdict_counter() -> Dict[Tuple[str, str], Counter]:
    return defaultdict(Counter)


def _age_mid(age_bin: str) -> str:
    if not age_bin or "_" not in age_bin:
        return ""
    lo, hi = age_bin.split("_", 1)
    try:
        return str((float(lo) + float(hi)) / 2.0)
    except ValueError:
        return ""


def default_run_name(datasets: Sequence[str], speakers: Sequence[str]) -> str:
    """Make a compact deterministic default run directory name."""
    return "special_forms__" + "_".join(datasets) + "__" + "_".join(speakers)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count CHAT special @ forms per usable utterance."
    )
    parser.add_argument(
        "--datasets",
        type=parse_dataset_list,
        default=DEFAULT_DATASETS,
        help="Comma-separated datasets to scan, or all. Default: Brown,Manchester,Providence.",
    )
    parser.add_argument(
        "--speakers",
        type=parse_csv_list,
        default=DEFAULT_SPEAKERS,
        help="Comma-separated speaker tiers. Default: CHI,MOT,FAT.",
    )
    parser.add_argument(
        "--markers",
        type=parse_marker_list,
        default=DEFAULT_MARKERS,
        help="Target marker families for per-utterance columns. Default: f,c,d,b,i,k,l,ls,n,o,p,wp.",
    )
    parser.add_argument(
        "--age-bin-width",
        type=int,
        default=6,
        help="Age-bin width in months for the age-bin summary. Default: 6.",
    )
    parser.add_argument(
        "--include-empty-cleaned",
        action="store_true",
        help="Include rows that would otherwise be treated as unscorable. Default excludes them.",
    )
    parser.add_argument(
        "--min-cleaned-words",
        type=int,
        default=1,
        help="Minimum cleaned word count for a scorable utterance. Default: 1.",
    )
    parser.add_argument(
        "--utterance-mode",
        choices=("all", "with-special"),
        default="all",
        help="Write all usable utterances or only utterances with target special forms.",
    )
    parser.add_argument(
        "--examples-per-marker",
        type=int,
        default=20,
        help="Maximum examples to keep per target marker. Default: 20.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "special_forms",
        help="Base output directory. A run-name subdirectory is created inside it.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Output subdirectory name. Default is based on datasets and speakers.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_cli().parse_args(argv)

    datasets = tuple(args.datasets)
    speakers = tuple(speaker.upper() for speaker in args.speakers)
    markers = tuple(marker.lower() for marker in args.markers)
    run_name = args.run_name or default_run_name(datasets, speakers)
    out_dir = args.output_dir.expanduser().resolve() / run_name

    report, raw_bases = analyze_datasets(
        datasets,
        speakers=speakers,
        markers=markers,
        age_bin_width=args.age_bin_width,
        include_empty_cleaned=args.include_empty_cleaned,
        min_cleaned_words=args.min_cleaned_words,
        utterance_mode=args.utterance_mode,
        examples_per_marker=args.examples_per_marker,
    )
    write_report(
        report,
        out_dir,
        markers=markers,
        datasets=datasets,
        speakers=speakers,
        raw_bases=raw_bases,
        age_bin_width=args.age_bin_width,
        include_empty_cleaned=args.include_empty_cleaned,
        min_cleaned_words=args.min_cleaned_words,
        utterance_mode=args.utterance_mode,
    )

    total_utts = len(report.utterance_rows)
    target_utts = sum(report.group_target_utts.values())
    target_tokens = sum(report.group_target_tokens.values())
    print(f"Wrote special-form report to {out_dir}")
    print(f"Usable utterances in report: {total_utts:,}")
    print(f"Utterances with target special forms: {target_utts:,}")
    print(f"Target special-form token occurrences: {target_tokens:,}")


if __name__ == "__main__":
    main()
