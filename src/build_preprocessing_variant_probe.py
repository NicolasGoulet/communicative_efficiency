#!/usr/bin/env python3
"""
Build a small real-data probe set for testing preprocessing effects on surprisal.

The output is intentionally not a scored file. It is a curated set of actual
CHAT utterances with several text variants for each base utterance, so the same
examples can be scored under different preprocessing choices.

Default outputs are written to results/preprocessing_variant_probe/<run_name>/:
- preprocessing_variant_probe_long.csv: one row per base utterance x variant
- preprocessing_variant_probe_wide.csv: one row per base utterance
- metadata.txt
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from cleaning import clean_chat_utterance
from fillers_and_shortenings_per_utterance import (
    classify_filler,
    extract_fillers,
    extract_shortenings,
    normalize_for_filler,
    speaker_group_for,
)
from prepare_datasets import (
    DATASETS,
    PROJECT_ROOT,
    ChatUnit,
    discover_dataset_units,
    prepared_rows_for_unit,
    resolve_base_dir,
)
from special_forms_per_utterance import DEFAULT_MARKERS, extract_special_forms


DEFAULT_DATASETS = ("Brown", "Manchester", "Providence")
DEFAULT_SPEAKERS = ("CHI", "MOT", "FAT")

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
SPACES_RE = re.compile(r"\s+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.!?;:])")
PAREN_LETTERS_RE = re.compile(r"\(([A-Za-z][A-Za-z'’-]*)\)")
TERMINAL_PUNCT_RE = re.compile(r"([.!?])\s*$")

TIMECODE_RE = re.compile(r"\x15\s*\d+(?:[_:]\d+)?\s*\x15")
BRACKETS_RE = re.compile(r"\[[^\]]*]")
PARENS_RE = re.compile(r"\([^)]*\)")
ANGLE_KEEP_RE = re.compile(r"<([^>]*)>")
UNTRANS_RE = re.compile(r"\b(?:xxx|yyy|www)\b", re.IGNORECASE)
PLUS_MARKER_RE = re.compile(r"(?:(?<=\s)|^)\+(?:[/.\-]+|\S+)")
FILLER_MARKER_RE = re.compile(
    r"(?:(?<=\s)|^)&-(uh|um|er|eh)(?::[A-Za-z]*)?(?=[\s,.;!?]|$)",
    re.IGNORECASE,
)
AT_MARKER_RE = re.compile(r"(?:(?<=\s)|^)@[^\s]+")
AMP_MARKER_RE = re.compile(r"(?:(?<=\s)|^)&[^\s]+")
ZERO_MARKER_RE = re.compile(r"(?:(?<=\s)|^)0[^\s]*")


@dataclass(frozen=True)
class Variant:
    variant_id: str
    variant_description: str
    text: str


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


def norm_ws(text: object) -> str:
    s = SPACES_RE.sub(" ", "" if text is None else str(text)).strip()
    return SPACE_BEFORE_PUNCT_RE.sub(r"\1", s)


def word_count(text: object) -> int:
    return len(WORD_RE.findall("" if text is None else str(text)))


def terminal_punct(text: object) -> str:
    match = TERMINAL_PUNCT_RE.search("" if text is None else str(text))
    return match.group(1) if match else ""


def expand_parenthetical_letters(text: object) -> str:
    """Expand CHAT letter parentheses such as y(ou), an(d), and (be)cause."""
    return PAREN_LETTERS_RE.sub(lambda match: match.group(1), "" if text is None else str(text))


def remove_filler_tokens(text: object) -> str:
    """Remove filler-like words from an already readable utterance variant."""
    raw = "" if text is None else str(text)
    punct = terminal_punct(raw)
    kept: List[str] = []
    for token in raw.split():
        normalized = normalize_for_filler(token)
        if classify_filler(normalized) is not None:
            continue
        kept.append(token)

    out = norm_ws(" ".join(kept))
    if out and punct and not TERMINAL_PUNCT_RE.search(out):
        out = f"{out}{punct}"
    return out


def clean_preserving_at_suffixes(text: object) -> str:
    """
    Clean ordinary CHAT markup but keep word-level @ suffixes such as ow@i.

    This is deliberately a diagnostic variant, not the production cleaning
    policy. It lets us test whether the model penalizes the written marker.
    """
    s = "" if text is None else str(text)
    punct = terminal_punct(s)
    s = TIMECODE_RE.sub(" ", s)
    s = BRACKETS_RE.sub(" ", s)
    s = PARENS_RE.sub(" ", s)
    s = ANGLE_KEEP_RE.sub(r"\1", s)
    s = UNTRANS_RE.sub(" ", s)
    s = FILLER_MARKER_RE.sub(lambda match: f" {match.group(1).lower()} ", s)
    s = AT_MARKER_RE.sub(" ", s)
    s = PLUS_MARKER_RE.sub(" ", s)
    s = AMP_MARKER_RE.sub(" ", s)
    s = ZERO_MARKER_RE.sub(" ", s)
    s = norm_ws(s)
    if s and punct and not TERMINAL_PUNCT_RE.search(s):
        s = f"{s}{punct}"
    return s


def drop_target_special_form_tokens(text: object, markers: Sequence[str] = DEFAULT_MARKERS) -> str:
    """Remove tokens whose @ family is one of the target special-form markers."""
    punct = terminal_punct(text)
    marker_set = set(markers)
    kept: List[str] = []
    for raw_token in ("" if text is None else str(text)).split():
        forms = extract_special_forms(raw_token)
        if forms and any(form.marker_family in marker_set for form in forms):
            continue
        kept.append(raw_token)
    out = clean_chat_utterance(" ".join(kept))
    if out and punct and not TERMINAL_PUNCT_RE.search(out):
        out = f"{out}{punct}"
    return out


def build_variants(raw_utterance: object, current_clean: object) -> List[Variant]:
    raw = norm_ws(raw_utterance)
    current = norm_ws(current_clean)
    expanded = clean_chat_utterance(expand_parenthetical_letters(raw))
    no_fillers = remove_filler_tokens(current)
    expanded_no_fillers = remove_filler_tokens(expanded)
    preserve_at = clean_preserving_at_suffixes(raw)
    drop_special = drop_target_special_form_tokens(raw)

    return [
        Variant("current_clean", "Current production utterance_clean.", current),
        Variant("raw_chat_main_tier", "Raw CHAT main-tier text with transcription markup.", raw),
        Variant("expand_shortenings", "Expand letter material in parentheses before cleaning.", expanded),
        Variant("remove_fillers", "Use current_clean but remove filler-like words.", no_fillers),
        Variant(
            "expand_shortenings_remove_fillers",
            "Expand parenthetical shortenings and remove filler-like words.",
            expanded_no_fillers,
        ),
        Variant(
            "preserve_special_at_suffixes",
            "Clean ordinary CHAT markup but keep word-level @ suffixes.",
            preserve_at,
        ),
        Variant(
            "drop_special_form_tokens",
            "Remove target CHAT special-form tokens before cleaning.",
            drop_special,
        ),
    ]


def classify_base_example(raw_utterance: object) -> Tuple[str, Dict[str, object]]:
    fillers = extract_fillers(raw_utterance)
    shortenings = extract_shortenings(raw_utterance)
    special_forms = [
        form for form in extract_special_forms(raw_utterance) if form.marker_family in set(DEFAULT_MARKERS)
    ]
    has_filler = bool(fillers)
    has_shortening = bool(shortenings)
    has_special = bool(special_forms)

    if has_filler and has_shortening and has_special:
        category = "filler_shortening_special"
    elif has_filler and has_shortening:
        category = "filler_shortening"
    elif has_filler and has_special:
        category = "filler_special"
    elif has_shortening and has_special:
        category = "shortening_special"
    elif has_filler:
        category = "filler_only"
    elif has_shortening:
        category = "shortening_only"
    elif has_special:
        category = "special_only"
    else:
        category = "ordinary_control"

    diagnostics = {
        "has_filler": int(has_filler),
        "has_shortening": int(has_shortening),
        "has_special_form": int(has_special),
        "filler_types": ";".join(sorted({filler.filler_type for filler in fillers})),
        "shortening_raw_tokens": ";".join(shortening.raw_token for shortening in shortenings),
        "special_form_raw_tokens": ";".join(form.raw_token for form in special_forms),
        "special_form_markers": ";".join(sorted({form.marker_family for form in special_forms})),
    }
    return category, diagnostics


def example_quality(row: Dict[str, object], category: str) -> Tuple[int, int, str]:
    """Sort shorter, cleaner examples first while keeping enough phenomena."""
    wc = word_count(row["utterance_clean"])
    raw = str(row["utterance"])
    ideal_length_penalty = abs(wc - 5)
    category_bonus = 0 if category != "ordinary_control" else 3
    return (ideal_length_penalty + category_bonus, len(raw), raw)


def iter_dataset_units(datasets: Sequence[str]) -> Iterator[Tuple[str, List[ChatUnit], Path]]:
    for dataset in datasets:
        raw_base = resolve_base_dir(dataset, None)
        if not raw_base.exists():
            raise FileNotFoundError(f"Raw base directory not found for {dataset}: {raw_base}")
        units = discover_dataset_units(dataset, raw_base)
        if not units:
            raise FileNotFoundError(f"No .cha files found for {dataset} under {raw_base}")
        yield dataset, units, raw_base


def collect_candidate_rows(
    datasets: Sequence[str],
    *,
    speakers: Sequence[str],
    max_cleaned_words: int,
) -> Tuple[Dict[str, List[Dict[str, object]]], Dict[str, Path]]:
    speaker_set = {speaker.upper() for speaker in speakers}
    buckets: Dict[str, List[Dict[str, object]]] = {}
    raw_bases: Dict[str, Path] = {}
    seen_refs = set()

    for dataset, units, raw_base in iter_dataset_units(datasets):
        raw_bases[dataset] = raw_base
        for unit in units:
            for row in prepared_rows_for_unit(unit):
                speaker = str(row["speaker"]).upper()
                if speaker not in speaker_set:
                    continue
                wc = word_count(row["utterance_clean"])
                if wc < 1 or wc > max_cleaned_words:
                    continue
                ref = str(row["reference_line"])
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)

                category, diagnostics = classify_base_example(row["utterance"])
                enriched = {
                    **row,
                    "speaker_group": speaker_group_for(speaker),
                    "base_category": category,
                    "cleaned_word_count": wc,
                    **diagnostics,
                }
                buckets.setdefault(category, []).append(enriched)

    for category, rows in buckets.items():
        rows.sort(key=lambda item: example_quality(item, category))
    return buckets, raw_bases


def select_examples(
    buckets: Dict[str, List[Dict[str, object]]],
    *,
    examples_per_category: int,
    max_base_examples: int,
) -> List[Dict[str, object]]:
    priority = [
        "filler_shortening_special",
        "filler_shortening",
        "shortening_special",
        "filler_special",
        "shortening_only",
        "filler_only",
        "special_only",
        "ordinary_control",
    ]
    selected: List[Dict[str, object]] = []
    for category in priority:
        for row in buckets.get(category, [])[:examples_per_category]:
            selected.append(row)
            if len(selected) >= max_base_examples:
                return selected
    return selected


def build_output_rows(
    base_rows: Sequence[Dict[str, object]]
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    long_rows: List[Dict[str, object]] = []
    wide_rows: List[Dict[str, object]] = []

    for base_index, row in enumerate(base_rows, start=1):
        variants = build_variants(row["utterance"], row["utterance_clean"])
        base_payload = {
            "probe_id": f"probe_{base_index:04d}",
            "dataset": row["dataset"],
            "child_id": row["child_id"],
            "source_group": row["source_group"],
            "session_id": row["session_id"],
            "age_raw": row["age_raw"],
            "age_months": row["age_months"],
            "sex": row["sex"],
            "file": row["file"],
            "line_no": row["line_no"],
            "reference_line": row["reference_line"],
            "utt_id": row["utt_id"],
            "utt_id_role": row["utt_id_role"],
            "speaker": row["speaker"],
            "speaker_group": row["speaker_group"],
            "base_category": row["base_category"],
            "has_filler": row["has_filler"],
            "has_shortening": row["has_shortening"],
            "has_special_form": row["has_special_form"],
            "filler_types": row["filler_types"],
            "shortening_raw_tokens": row["shortening_raw_tokens"],
            "special_form_raw_tokens": row["special_form_raw_tokens"],
            "special_form_markers": row["special_form_markers"],
            "utterance": row["utterance"],
            "utterance_clean": row["utterance_clean"],
            "cleaned_word_count": row["cleaned_word_count"],
        }

        wide_row = dict(base_payload)
        for variant in variants:
            variant_text = norm_ws(variant.text)
            variant_wc = word_count(variant_text)
            wide_row[f"variant_{variant.variant_id}"] = variant_text
            wide_row[f"variant_{variant.variant_id}_word_count"] = variant_wc

            long_rows.append(
                {
                    **base_payload,
                    "variant_id": variant.variant_id,
                    "variant_description": variant.variant_description,
                    "utterance_for_scoring": variant_text,
                    "word_count": variant_wc,
                    "morph_count": variant_wc,
                    "is_scorable_variant": int(variant_wc > 0),
                    "word_count_note": "Regex word count; morph_count duplicated only for scorer eligibility.",
                }
            )
        wide_rows.append(wide_row)

    return long_rows, wide_rows


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
    long_rows: Sequence[Dict[str, object]],
    wide_rows: Sequence[Dict[str, object]],
    datasets: Sequence[str],
    speakers: Sequence[str],
    raw_bases: Dict[str, Path],
    examples_per_category: int,
    max_base_examples: int,
    max_cleaned_words: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    long_fields = [
        "probe_id",
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
        "speaker_group",
        "base_category",
        "has_filler",
        "has_shortening",
        "has_special_form",
        "filler_types",
        "shortening_raw_tokens",
        "special_form_raw_tokens",
        "special_form_markers",
        "utterance",
        "utterance_clean",
        "cleaned_word_count",
        "variant_id",
        "variant_description",
        "utterance_for_scoring",
        "word_count",
        "morph_count",
        "is_scorable_variant",
        "word_count_note",
    ]

    variant_ids = [
        "current_clean",
        "raw_chat_main_tier",
        "expand_shortenings",
        "remove_fillers",
        "expand_shortenings_remove_fillers",
        "preserve_special_at_suffixes",
        "drop_special_form_tokens",
    ]
    wide_fields = [
        field
        for field in long_fields
        if field
        not in {
            "variant_id",
            "variant_description",
            "utterance_for_scoring",
            "word_count",
            "morph_count",
            "is_scorable_variant",
            "word_count_note",
        }
    ]
    for variant_id in variant_ids:
        wide_fields.extend([f"variant_{variant_id}", f"variant_{variant_id}_word_count"])

    write_csv_rows(out_dir / "preprocessing_variant_probe_long.csv", long_rows, long_fields)
    write_csv_rows(out_dir / "preprocessing_variant_probe_wide.csv", wide_rows, wide_fields)

    category_counts = Counter(row["base_category"] for row in wide_rows)
    metadata = [
        "Preprocessing variant surprisal probe set",
        f"datasets: {', '.join(datasets)}",
        f"speakers: {', '.join(speakers)}",
        f"base_examples: {len(wide_rows)}",
        f"long_rows: {len(long_rows)}",
        f"examples_per_category: {examples_per_category}",
        f"max_base_examples: {max_base_examples}",
        f"max_cleaned_words: {max_cleaned_words}",
        "variants:",
        "  current_clean: current production utterance_clean",
        "  raw_chat_main_tier: raw CHAT main-tier text",
        "  expand_shortenings: expand letter parentheses before cleaning",
        "  remove_fillers: remove filler-like words from current_clean",
        "  expand_shortenings_remove_fillers: combine both changes",
        "  preserve_special_at_suffixes: clean ordinary CHAT but keep @ suffixes",
        "  drop_special_form_tokens: remove target special @ tokens before cleaning",
        "category_counts:",
        *[f"  {category}: {category_counts[category]}" for category in sorted(category_counts)],
        "raw_bases:",
        *[f"  {dataset}: {raw_bases[dataset]}" for dataset in sorted(raw_bases)],
    ]
    (out_dir / "metadata.txt").write_text("\n".join(metadata) + "\n", encoding="utf-8")


def build_probe(
    datasets: Sequence[str],
    *,
    speakers: Sequence[str],
    examples_per_category: int,
    max_base_examples: int,
    max_cleaned_words: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], Dict[str, Path]]:
    buckets, raw_bases = collect_candidate_rows(
        datasets,
        speakers=speakers,
        max_cleaned_words=max_cleaned_words,
    )
    selected = select_examples(
        buckets,
        examples_per_category=examples_per_category,
        max_base_examples=max_base_examples,
    )
    long_rows, wide_rows = build_output_rows(selected)
    return long_rows, wide_rows, raw_bases


def default_run_name(datasets: Sequence[str], speakers: Sequence[str]) -> str:
    return "variant_probe__" + "_".join(datasets) + "__" + "_".join(speakers)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build real CHAT utterance examples with preprocessing variants for surprisal probes."
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
        "--examples-per-category",
        type=int,
        default=12,
        help="Maximum base utterances to keep from each phenomenon category. Default: 12.",
    )
    parser.add_argument(
        "--max-base-examples",
        type=int,
        default=96,
        help="Maximum total base utterances. Default: 96.",
    )
    parser.add_argument(
        "--max-cleaned-words",
        type=int,
        default=12,
        help="Ignore longer utterances when choosing compact examples. Default: 12.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "preprocessing_variant_probe",
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
    run_name = args.run_name or default_run_name(datasets, speakers)
    out_dir = args.output_dir.expanduser().resolve() / run_name

    long_rows, wide_rows, raw_bases = build_probe(
        datasets,
        speakers=speakers,
        examples_per_category=args.examples_per_category,
        max_base_examples=args.max_base_examples,
        max_cleaned_words=args.max_cleaned_words,
    )
    write_outputs(
        out_dir,
        long_rows=long_rows,
        wide_rows=wide_rows,
        datasets=datasets,
        speakers=speakers,
        raw_bases=raw_bases,
        examples_per_category=args.examples_per_category,
        max_base_examples=args.max_base_examples,
        max_cleaned_words=args.max_cleaned_words,
    )

    print(f"Wrote preprocessing variant probe to {out_dir}")
    print(f"Base utterances: {len(wide_rows):,}")
    print(f"Variant rows for scoring: {len(long_rows):,}")


if __name__ == "__main__":
    main()
