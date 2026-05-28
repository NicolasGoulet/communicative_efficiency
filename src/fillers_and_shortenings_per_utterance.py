#!/usr/bin/env python3
"""
Count fillers and parenthetical shortenings in usable CHAT utterances.

The script reads raw CHAT files through the same discovery and cleaning path as
prepare_datasets.py. By default, an utterance is included only when its cleaned
form has at least one word, matching the downstream "scorable utterance" rule.

Default outputs are written to results/fillers_shortenings/<run_name>/.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass
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
DEFAULT_FILLER_TYPES = ("uh", "um", "er", "eh", "ah", "hmm", "mhm", "uhuh", "huh")

EDGE_PUNCT = " \t\r\n.,!?;:\"'[]{}<>"
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
PAREN_LETTERS_RE = re.compile(r"\(([A-Za-z][A-Za-z'’-]*)\)")


@dataclass(frozen=True)
class FillerToken:
    raw_token: str
    filler_type: str
    normalized: str


@dataclass(frozen=True)
class ShorteningToken:
    raw_token: str
    observed_form: str
    expanded_form: str
    parenthetical_text: str


def parse_csv_list(value: str) -> Tuple[str, ...]:
    parts = tuple(part.strip() for part in value.split(",") if part.strip())
    if not parts:
        raise argparse.ArgumentTypeError("expected at least one comma-separated value")
    return parts


def parse_dataset_list(value: str) -> Tuple[str, ...]:
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


def cleaned_word_count(text: object) -> int:
    return len(WORD_RE.findall("" if text is None else str(text)))


def speaker_group_for(speaker: object) -> str:
    code = str(speaker).upper()
    if code == "CHI":
        return "CHILD"
    if code in {"MOT", "FAT"}:
        return "CARETAKERS"
    return code


def age_bin_label(age_months: object, width: int) -> str:
    if age_months in (None, ""):
        return ""
    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return ""
    lo = int(age // width) * width
    return f"{lo}_{lo + width}"


def age_mid(age_bin: str) -> str:
    if "_" not in age_bin:
        return ""
    lo, hi = age_bin.split("_", 1)
    try:
        return str((float(lo) + float(hi)) / 2.0)
    except ValueError:
        return ""


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 8)


def normalize_for_filler(raw_token: str) -> str:
    token = raw_token.strip(EDGE_PUNCT).lower()
    if "@" in token:
        token = token.rsplit("@", 1)[0]
    token = re.sub(r"^&[-=~]*", "", token)
    return re.sub(r"[^a-z]", "", token)


def classify_filler(normalized: str) -> Optional[str]:
    if not normalized:
        return None
    if re.fullmatch(r"u+h+u+h+", normalized):
        return "uhuh"
    if re.fullmatch(r"u+h+", normalized):
        return "uh"
    if re.fullmatch(r"u+m+", normalized):
        return "um"
    if re.fullmatch(r"e+r+", normalized):
        return "er"
    if re.fullmatch(r"e+h+", normalized):
        return "eh"
    if re.fullmatch(r"a+h+", normalized):
        return "ah"
    if re.fullmatch(r"h+u+h+", normalized):
        return "huh"
    if re.fullmatch(r"m+h+m+", normalized):
        return "mhm"
    if re.fullmatch(r"h+m+|m{2,}", normalized):
        return "hmm"
    return None


def extract_fillers(utterance: object) -> List[FillerToken]:
    fillers: List[FillerToken] = []
    if utterance is None:
        return fillers
    for raw_token in str(utterance).split():
        normalized = normalize_for_filler(raw_token)
        filler_type = classify_filler(normalized)
        if filler_type is None:
            continue
        fillers.append(
            FillerToken(
                raw_token=raw_token.strip(EDGE_PUNCT),
                filler_type=filler_type,
                normalized=normalized,
            )
        )
    return fillers


def extract_shortenings(utterance: object) -> List[ShorteningToken]:
    shortenings: List[ShorteningToken] = []
    if utterance is None:
        return shortenings
    for raw_token in str(utterance).split():
        token = raw_token.strip(EDGE_PUNCT)
        matches = PAREN_LETTERS_RE.findall(token)
        if not matches:
            continue
        expanded = PAREN_LETTERS_RE.sub(lambda match: match.group(1), token)
        observed = PAREN_LETTERS_RE.sub("", token)
        if not expanded or expanded == observed:
            continue
        shortenings.append(
            ShorteningToken(
                raw_token=token,
                observed_form=observed,
                expanded_form=expanded,
                parenthetical_text="+".join(part.lower() for part in matches),
            )
        )
    return shortenings


def iter_dataset_units(datasets: Sequence[str]) -> Iterator[Tuple[str, List[ChatUnit], Path]]:
    for dataset in datasets:
        raw_base = resolve_base_dir(dataset, None)
        if not raw_base.exists():
            raise FileNotFoundError(f"Raw base directory not found for {dataset}: {raw_base}")
        units = discover_dataset_units(dataset, raw_base)
        if not units:
            raise FileNotFoundError(f"No .cha files found for {dataset} under {raw_base}")
        yield dataset, units, raw_base


def base_row(row: Dict[str, object], age_bin_width: int, word_count: int) -> Dict[str, object]:
    speaker = str(row["speaker"]).upper()
    return {
        "dataset": row["dataset"],
        "child_id": row["child_id"],
        "source_group": row["source_group"],
        "session_id": row["session_id"],
        "age_raw": row["age_raw"],
        "age_months": row["age_months"],
        "age_bin": age_bin_label(row["age_months"], age_bin_width),
        "sex": row["sex"],
        "file": row["file"],
        "line_no": row["line_no"],
        "reference_line": row["reference_line"],
        "utt_id": row["utt_id"],
        "utt_id_role": row["utt_id_role"],
        "speaker": speaker,
        "speaker_group": speaker_group_for(speaker),
        "utterance": row["utterance"],
        "utterance_clean": row["utterance_clean"],
        "cleaned_word_count": word_count,
    }


def analyze_units(
    units: Sequence[ChatUnit],
    *,
    speakers: Sequence[str] = DEFAULT_SPEAKERS,
    filler_types: Sequence[str] = DEFAULT_FILLER_TYPES,
    age_bin_width: int = 6,
    include_unscorable: bool = False,
    min_cleaned_words: int = 1,
    examples_per_type: int = 20,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    speaker_set = {speaker.upper() for speaker in speakers}
    filler_type_set = set(filler_types)
    filler_rows: List[Dict[str, object]] = []
    shortening_rows: List[Dict[str, object]] = []
    filler_examples: List[Dict[str, object]] = []
    shortening_examples: List[Dict[str, object]] = []
    filler_example_counts: Counter = Counter()
    shortening_example_counts: Counter = Counter()

    for unit in units:
        for row in prepared_rows_for_unit(unit):
            speaker = str(row["speaker"]).upper()
            if speaker not in speaker_set:
                continue
            word_count = cleaned_word_count(row["utterance_clean"])
            if not include_unscorable and word_count < min_cleaned_words:
                continue

            info = base_row(row, age_bin_width, word_count)

            fillers = extract_fillers(row["utterance"])
            filler_counts = Counter(filler.filler_type for filler in fillers if filler.filler_type in filler_type_set)
            filler_row = {
                **info,
                "n_filler_tokens": sum(filler_counts.values()),
                "has_filler": int(sum(filler_counts.values()) > 0),
                "filler_types": ";".join(sorted(filler_counts)),
                "filler_raw_tokens": ";".join(filler.raw_token for filler in fillers),
                "filler_normalized_tokens": ";".join(filler.normalized for filler in fillers),
            }
            for filler_type in filler_types:
                filler_row[f"n_filler_{filler_type}"] = int(filler_counts.get(filler_type, 0))
            filler_rows.append(filler_row)

            for filler in fillers:
                if filler.filler_type not in filler_type_set:
                    continue
                if filler_example_counts[filler.filler_type] >= examples_per_type:
                    continue
                filler_example_counts[filler.filler_type] += 1
                filler_examples.append(
                    {
                        "filler_type": filler.filler_type,
                        "raw_token": filler.raw_token,
                        "normalized": filler.normalized,
                        "dataset": info["dataset"],
                        "child_id": info["child_id"],
                        "speaker": info["speaker"],
                        "speaker_group": info["speaker_group"],
                        "age_months": info["age_months"],
                        "reference_line": info["reference_line"],
                        "utterance": info["utterance"],
                        "utterance_clean": info["utterance_clean"],
                    }
                )

            shortenings = extract_shortenings(row["utterance"])
            shortening_counts = Counter(shortening.parenthetical_text for shortening in shortenings)
            shortening_row = {
                **info,
                "n_shortening_tokens": sum(shortening_counts.values()),
                "has_shortening": int(sum(shortening_counts.values()) > 0),
                "shortening_parenthetical_texts": ";".join(
                    shortening.parenthetical_text for shortening in shortenings
                ),
                "shortening_raw_tokens": ";".join(shortening.raw_token for shortening in shortenings),
                "shortening_observed_forms": ";".join(shortening.observed_form for shortening in shortenings),
                "shortening_expanded_forms": ";".join(shortening.expanded_form for shortening in shortenings),
            }
            shortening_rows.append(shortening_row)

            for shortening in shortenings:
                key = shortening.parenthetical_text
                if shortening_example_counts[key] >= examples_per_type:
                    continue
                shortening_example_counts[key] += 1
                shortening_examples.append(
                    {
                        "parenthetical_text": shortening.parenthetical_text,
                        "raw_token": shortening.raw_token,
                        "observed_form": shortening.observed_form,
                        "expanded_form": shortening.expanded_form,
                        "dataset": info["dataset"],
                        "child_id": info["child_id"],
                        "speaker": info["speaker"],
                        "speaker_group": info["speaker_group"],
                        "age_months": info["age_months"],
                        "reference_line": info["reference_line"],
                        "utterance": info["utterance"],
                        "utterance_clean": info["utterance_clean"],
                    }
                )

    return filler_rows, shortening_rows, filler_examples, shortening_examples


def analyze_datasets(
    datasets: Sequence[str],
    **kwargs,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], Dict[str, Path]]:
    all_fillers: List[Dict[str, object]] = []
    all_shortenings: List[Dict[str, object]] = []
    all_filler_examples: List[Dict[str, object]] = []
    all_shortening_examples: List[Dict[str, object]] = []
    raw_bases: Dict[str, Path] = {}

    for dataset, units, raw_base in iter_dataset_units(datasets):
        raw_bases[dataset] = raw_base
        filler_rows, shortening_rows, filler_examples, shortening_examples = analyze_units(units, **kwargs)
        all_fillers.extend(filler_rows)
        all_shortenings.extend(shortening_rows)
        all_filler_examples.extend(filler_examples)
        all_shortening_examples.extend(shortening_examples)

    return all_fillers, all_shortenings, all_filler_examples, all_shortening_examples, raw_bases


def summary_rows(
    rows: Sequence[Dict[str, object]],
    *,
    count_col: str,
    has_col: str,
    token_label: str,
) -> List[Dict[str, object]]:
    totals: Counter = Counter()
    utts: Counter = Counter()
    tokens: Counter = Counter()
    for row in rows:
        key = (str(row["dataset"]), str(row["speaker_group"]))
        totals[key] += 1
        count = int(row[count_col])
        tokens[key] += count
        if int(row[has_col]):
            utts[key] += 1

    out: List[Dict[str, object]] = []
    for dataset, speaker_group in sorted(totals):
        total = totals[(dataset, speaker_group)]
        count = tokens[(dataset, speaker_group)]
        out.append(
            {
                "dataset": dataset,
                "speaker_group": speaker_group,
                "total_usable_utterances": total,
                f"utterances_with_{token_label}": utts[(dataset, speaker_group)],
                f"{token_label}_token_occurrences": count,
                "utterance_rate": safe_rate(utts[(dataset, speaker_group)], total),
                "mean_tokens_per_utterance": safe_rate(count, total),
            }
        )
    return out


def filler_type_summary_rows(
    rows: Sequence[Dict[str, object]], filler_types: Sequence[str]
) -> List[Dict[str, object]]:
    totals: Counter = Counter()
    token_counts: Counter = Counter()
    utt_counts: Counter = Counter()
    for row in rows:
        key = (str(row["dataset"]), str(row["speaker_group"]))
        totals[key] += 1
        for filler_type in filler_types:
            count = int(row.get(f"n_filler_{filler_type}", 0))
            token_counts[(*key, filler_type)] += count
            if count:
                utt_counts[(*key, filler_type)] += 1

    out: List[Dict[str, object]] = []
    for dataset, speaker_group in sorted(totals):
        total = totals[(dataset, speaker_group)]
        for filler_type in filler_types:
            key = (dataset, speaker_group, filler_type)
            out.append(
                {
                    "dataset": dataset,
                    "speaker_group": speaker_group,
                    "filler_type": filler_type,
                    "total_usable_utterances": total,
                    "utterances_with_filler_type": utt_counts[key],
                    "filler_token_occurrences": token_counts[key],
                    "utterance_rate": safe_rate(utt_counts[key], total),
                    "mean_tokens_per_utterance": safe_rate(token_counts[key], total),
                }
            )
    return out


def age_filler_type_summary_rows(
    rows: Sequence[Dict[str, object]], filler_types: Sequence[str]
) -> List[Dict[str, object]]:
    totals: Counter = Counter()
    token_counts: Counter = Counter()
    utt_counts: Counter = Counter()
    for row in rows:
        age_bin = str(row["age_bin"])
        if not age_bin:
            continue
        key = (str(row["dataset"]), str(row["speaker_group"]), age_bin)
        totals[key] += 1
        for filler_type in filler_types:
            count = int(row.get(f"n_filler_{filler_type}", 0))
            token_counts[(*key, filler_type)] += count
            if count:
                utt_counts[(*key, filler_type)] += 1

    out: List[Dict[str, object]] = []
    for dataset, speaker_group, age_bin in sorted(totals):
        total = totals[(dataset, speaker_group, age_bin)]
        for filler_type in filler_types:
            key = (dataset, speaker_group, age_bin, filler_type)
            out.append(
                {
                    "dataset": dataset,
                    "speaker_group": speaker_group,
                    "age_bin": age_bin,
                    "age_mid": age_mid(age_bin),
                    "filler_type": filler_type,
                    "total_usable_utterances": total,
                    "utterances_with_filler_type": utt_counts[key],
                    "filler_token_occurrences": token_counts[key],
                    "utterance_rate": safe_rate(utt_counts[key], total),
                    "mean_tokens_per_utterance": safe_rate(token_counts[key], total),
                }
            )
    return out


def shortening_text_summary_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    totals: Counter = Counter()
    token_counts: Counter = Counter()
    utt_counts: Counter = Counter()
    all_texts = set()

    for row in rows:
        key = (str(row["dataset"]), str(row["speaker_group"]))
        totals[key] += 1
        texts = [text for text in str(row["shortening_parenthetical_texts"]).split(";") if text]
        counts = Counter(texts)
        all_texts.update(counts)
        for text, count in counts.items():
            token_counts[(*key, text)] += count
            utt_counts[(*key, text)] += 1

    out: List[Dict[str, object]] = []
    for dataset, speaker_group in sorted(totals):
        total = totals[(dataset, speaker_group)]
        for text in sorted(all_texts):
            key = (dataset, speaker_group, text)
            tokens = token_counts[key]
            utts = utt_counts[key]
            if not tokens:
                continue
            out.append(
                {
                    "dataset": dataset,
                    "speaker_group": speaker_group,
                    "parenthetical_text": text,
                    "total_usable_utterances": total,
                    "utterances_with_parenthetical_text": utts,
                    "shortening_token_occurrences": tokens,
                    "utterance_rate": safe_rate(utts, total),
                    "mean_tokens_per_utterance": safe_rate(tokens, total),
                }
            )
    return out


def age_shortening_text_summary_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    totals: Counter = Counter()
    token_counts: Counter = Counter()
    utt_counts: Counter = Counter()

    for row in rows:
        age_bin = str(row["age_bin"])
        if not age_bin:
            continue
        key = (str(row["dataset"]), str(row["speaker_group"]), age_bin)
        totals[key] += 1
        counts = Counter(text for text in str(row["shortening_parenthetical_texts"]).split(";") if text)
        for text, count in counts.items():
            token_counts[(*key, text)] += count
            utt_counts[(*key, text)] += 1

    out: List[Dict[str, object]] = []
    for dataset, speaker_group, age_bin, text in sorted(token_counts):
        total = totals[(dataset, speaker_group, age_bin)]
        key = (dataset, speaker_group, age_bin, text)
        out.append(
            {
                "dataset": dataset,
                "speaker_group": speaker_group,
                "age_bin": age_bin,
                "age_mid": age_mid(age_bin),
                "parenthetical_text": text,
                "total_usable_utterances": total,
                "utterances_with_parenthetical_text": utt_counts[key],
                "shortening_token_occurrences": token_counts[key],
                "utterance_rate": safe_rate(utt_counts[key], total),
                "mean_tokens_per_utterance": safe_rate(token_counts[key], total),
            }
        )
    return out


def write_csv_rows(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field) for field in fieldnames})


def write_outputs(
    out_dir: Path,
    *,
    filler_rows: Sequence[Dict[str, object]],
    shortening_rows: Sequence[Dict[str, object]],
    filler_examples: Sequence[Dict[str, object]],
    shortening_examples: Sequence[Dict[str, object]],
    filler_types: Sequence[str],
    datasets: Sequence[str],
    speakers: Sequence[str],
    raw_bases: Dict[str, Path],
    age_bin_width: int,
    include_unscorable: bool,
    min_cleaned_words: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    base_fields = [
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
    ]

    write_csv_rows(
        out_dir / "fillers_per_utterance.csv",
        filler_rows,
        [
            *base_fields,
            "n_filler_tokens",
            "has_filler",
            "filler_types",
            "filler_raw_tokens",
            "filler_normalized_tokens",
            *[f"n_filler_{filler_type}" for filler_type in filler_types],
        ],
    )
    write_csv_rows(
        out_dir / "fillers_by_dataset_speaker_group.csv",
        summary_rows(
            filler_rows,
            count_col="n_filler_tokens",
            has_col="has_filler",
            token_label="filler",
        ),
        [
            "dataset",
            "speaker_group",
            "total_usable_utterances",
            "utterances_with_filler",
            "filler_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "fillers_by_dataset_speaker_group_type.csv",
        filler_type_summary_rows(filler_rows, filler_types),
        [
            "dataset",
            "speaker_group",
            "filler_type",
            "total_usable_utterances",
            "utterances_with_filler_type",
            "filler_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "fillers_by_age_bin_speaker_group_type.csv",
        age_filler_type_summary_rows(filler_rows, filler_types),
        [
            "dataset",
            "speaker_group",
            "age_bin",
            "age_mid",
            "filler_type",
            "total_usable_utterances",
            "utterances_with_filler_type",
            "filler_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "filler_examples.csv",
        filler_examples,
        [
            "filler_type",
            "raw_token",
            "normalized",
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

    write_csv_rows(
        out_dir / "shortenings_per_utterance.csv",
        shortening_rows,
        [
            *base_fields,
            "n_shortening_tokens",
            "has_shortening",
            "shortening_parenthetical_texts",
            "shortening_raw_tokens",
            "shortening_observed_forms",
            "shortening_expanded_forms",
        ],
    )
    write_csv_rows(
        out_dir / "shortenings_by_dataset_speaker_group.csv",
        summary_rows(
            shortening_rows,
            count_col="n_shortening_tokens",
            has_col="has_shortening",
            token_label="shortening",
        ),
        [
            "dataset",
            "speaker_group",
            "total_usable_utterances",
            "utterances_with_shortening",
            "shortening_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "shortenings_by_dataset_speaker_group_text.csv",
        shortening_text_summary_rows(shortening_rows),
        [
            "dataset",
            "speaker_group",
            "parenthetical_text",
            "total_usable_utterances",
            "utterances_with_parenthetical_text",
            "shortening_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "shortenings_by_age_bin_speaker_group_text.csv",
        age_shortening_text_summary_rows(shortening_rows),
        [
            "dataset",
            "speaker_group",
            "age_bin",
            "age_mid",
            "parenthetical_text",
            "total_usable_utterances",
            "utterances_with_parenthetical_text",
            "shortening_token_occurrences",
            "utterance_rate",
            "mean_tokens_per_utterance",
        ],
    )
    write_csv_rows(
        out_dir / "shortening_examples.csv",
        shortening_examples,
        [
            "parenthetical_text",
            "raw_token",
            "observed_form",
            "expanded_form",
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
        "CHAT filler and shortening report",
        f"datasets: {', '.join(datasets)}",
        f"speakers: {', '.join(speakers)}",
        f"filler_types: {', '.join(filler_types)}",
        f"age_bin_width_months: {age_bin_width}",
        f"include_unscorable: {include_unscorable}",
        f"min_cleaned_words: {min_cleaned_words}",
        f"total_usable_utterances: {len(filler_rows)}",
        "raw_bases:",
        *[f"  {dataset}: {raw_bases[dataset]}" for dataset in sorted(raw_bases)],
    ]
    (out_dir / "metadata.txt").write_text("\n".join(metadata) + "\n", encoding="utf-8")


def default_run_name(datasets: Sequence[str], speakers: Sequence[str]) -> str:
    return "fillers_shortenings__" + "_".join(datasets) + "__" + "_".join(speakers)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count fillers and parenthetical shortenings per usable CHAT utterance."
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
        "--filler-types",
        type=parse_csv_list,
        default=DEFAULT_FILLER_TYPES,
        help="Comma-separated filler categories to report.",
    )
    parser.add_argument(
        "--age-bin-width",
        type=int,
        default=6,
        help="Age-bin width in months for age summaries. Default: 6.",
    )
    parser.add_argument(
        "--include-unscorable",
        action="store_true",
        help="Include utterances with fewer than --min-cleaned-words cleaned words.",
    )
    parser.add_argument(
        "--min-cleaned-words",
        type=int,
        default=1,
        help="Minimum cleaned word count for a scorable utterance. Default: 1.",
    )
    parser.add_argument(
        "--examples-per-type",
        type=int,
        default=20,
        help="Maximum examples to keep per filler or shortening type. Default: 20.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "fillers_shortenings",
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
    filler_types = tuple(filler_type.lower() for filler_type in args.filler_types)
    run_name = args.run_name or default_run_name(datasets, speakers)
    out_dir = args.output_dir.expanduser().resolve() / run_name

    filler_rows, shortening_rows, filler_examples, shortening_examples, raw_bases = analyze_datasets(
        datasets,
        speakers=speakers,
        filler_types=filler_types,
        age_bin_width=args.age_bin_width,
        include_unscorable=args.include_unscorable,
        min_cleaned_words=args.min_cleaned_words,
        examples_per_type=args.examples_per_type,
    )
    write_outputs(
        out_dir,
        filler_rows=filler_rows,
        shortening_rows=shortening_rows,
        filler_examples=filler_examples,
        shortening_examples=shortening_examples,
        filler_types=filler_types,
        datasets=datasets,
        speakers=speakers,
        raw_bases=raw_bases,
        age_bin_width=args.age_bin_width,
        include_unscorable=args.include_unscorable,
        min_cleaned_words=args.min_cleaned_words,
    )

    total_filler_utts = sum(int(row["has_filler"]) for row in filler_rows)
    total_filler_tokens = sum(int(row["n_filler_tokens"]) for row in filler_rows)
    total_shortening_utts = sum(int(row["has_shortening"]) for row in shortening_rows)
    total_shortening_tokens = sum(int(row["n_shortening_tokens"]) for row in shortening_rows)
    print(f"Wrote filler/shortening report to {out_dir}")
    print(f"Usable utterances in report: {len(filler_rows):,}")
    print(f"Utterances with fillers: {total_filler_utts:,}")
    print(f"Filler token occurrences: {total_filler_tokens:,}")
    print(f"Utterances with shortenings: {total_shortening_utts:,}")
    print(f"Shortening token occurrences: {total_shortening_tokens:,}")


if __name__ == "__main__":
    main()
