#!/usr/bin/env python3
"""Build an audited utterance-level analysis dataset for Route 1 modeling.

The output is a long, normalized CSV: each row is one scored target utterance
under one context condition. Child rows include the real child utterance and
matched-length generated baselines; caretaker rows include the scored caretaker
utterance. Effort measures are computed from the exact cleaned target string
that was scored, preserving child forms and generated baseline forms as written.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import os
from typing import Iterable, Iterator, Mapping, Sequence, TextIO

from build_route1_report_assets import age_to_route1_bin, resolve_age_months
from utterance_count_strategies import (
    clitic_morpheme_count_for_token,
    normalize_text,
    suffix_extra_morphemes,
    word_tokens_regex,
)
from validate_utterance_measurement_strategies import (
    count_cmudict_g2p_utterance,
    count_cmudict_or_syllables_pkg_utterance,
    count_syllables_pkg,
    first_cmu_pronunciation,
)


DEFAULT_MAIN_SCORED_ROOT = Path(
    "results/external/compute_surprisal_mila/"
    "raw_surprisal_cleaned_mistral_patched_006_023"
)
DEFAULT_OUTPUT_DIR = Path("results/route1_analysis_dataset")
DEFAULT_LONG_CSV = DEFAULT_OUTPUT_DIR / "route1_scored_utterance_effort_long.csv.gz"
DEFAULT_FILE_AUDIT_CSV = DEFAULT_OUTPUT_DIR / "source_file_audit.csv"
DEFAULT_VARIANT_AUDIT_CSV = DEFAULT_OUTPUT_DIR / "variant_context_audit.csv"
DEFAULT_SCHEMA_JSON = DEFAULT_OUTPUT_DIR / "schema.json"

CHILD_BASELINE_VARIANTS = {"random", "unigram", "bigram", "trigram"}
SCORED_SUFFIX = ".scored.csv"
ROUTE1_CONTEXT_KS = ("k0", "k1", "k2", "k3")


@dataclass(frozen=True)
class ScoredFileSpec:
    """Metadata inferred from one scored CSV path."""

    path: Path
    score_source: str
    context_condition: str
    context_k: str
    model_slug: str
    dataset_dir: str
    child_dir: str
    role: str
    target_variant: str
    target_column: str


@dataclass(frozen=True)
class EffortCounts:
    """Selected effort counts for one target utterance."""

    nb_words: int
    nb_morphemes: int
    nb_syllables_cmu_or_pkg: int
    nb_syllables_pkg: int
    nb_phonemes: int
    cmu_oov_word_count: int
    syllable_pkg_fallback_word_count: int
    g2p_fallback_word_count: int
    quality_flags: str


@dataclass
class FileAudit:
    """Per-source-file data-quality audit."""

    score_source: str
    scored_file: str
    context_condition: str
    context_k: str
    role: str
    target_variant: str
    target_column: str
    rows_read: int = 0
    rows_written: int = 0
    rows_skipped_unscored_or_empty: int = 0
    missing_target_column_rows: int = 0
    blank_target_rows: int = 0
    zero_word_rows: int = 0
    missing_or_outside_age_bin_rows: int = 0
    nonnumeric_line_no_rows: int = 0
    missing_sum_bits_rows: int = 0
    child_word_count_mismatch_rows: int = 0


class RunningStats:
    """Small numeric accumulator for grouped audit summaries."""

    def __init__(self) -> None:
        self.n = 0
        self.total = 0.0
        self.min_value: float | None = None
        self.max_value: float | None = None

    def add(self, value: object) -> None:
        parsed = parse_float(value)
        if parsed is None:
            return
        self.n += 1
        self.total += parsed
        self.min_value = parsed if self.min_value is None else min(self.min_value, parsed)
        self.max_value = parsed if self.max_value is None else max(self.max_value, parsed)

    @property
    def mean(self) -> float | None:
        if self.n == 0:
            return None
        return self.total / self.n


class GroupAudit:
    """Counters and means for one role/variant/context group."""

    def __init__(self) -> None:
        self.rows = 0
        self.counters: Counter[str] = Counter()
        self.stats: dict[str, RunningStats] = defaultdict(RunningStats)

    def add_row(
        self,
        *,
        counts: EffortCounts,
        sum_bits: object,
        mean_bits_per_token: object,
        n_eval_tokens: object,
        deltas: Mapping[str, object],
    ) -> None:
        self.rows += 1
        self.stats["sum_bits"].add(sum_bits)
        self.stats["mean_bits_per_token"].add(mean_bits_per_token)
        self.stats["n_eval_tokens"].add(n_eval_tokens)
        self.stats["nb_words"].add(counts.nb_words)
        self.stats["nb_morphemes"].add(counts.nb_morphemes)
        self.stats["nb_syllables_cmu_or_pkg"].add(counts.nb_syllables_cmu_or_pkg)
        self.stats["nb_syllables_pkg"].add(counts.nb_syllables_pkg)
        self.stats["nb_phonemes"].add(counts.nb_phonemes)
        self.stats["cmu_oov_word_count"].add(counts.cmu_oov_word_count)
        self.stats["syllable_pkg_fallback_word_count"].add(counts.syllable_pkg_fallback_word_count)
        self.stats["g2p_fallback_word_count"].add(counts.g2p_fallback_word_count)
        for field, value in deltas.items():
            self.stats[field].add(value)


ANALYSIS_COLUMNS = [
    "score_source",
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "age_months_source",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "speaker",
    "role",
    "target_variant",
    "target_column",
    "target_utterance_clean",
    "target_text_hash",
    "context_condition",
    "context_k",
    "context_col_used",
    "context_text",
    "context_text_hash",
    "mean_bits_per_token",
    "sum_bits",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "effort_quality_flags",
    "child_real_nb_words",
    "child_real_nb_morphemes",
    "child_real_nb_syllables_cmu_or_pkg",
    "child_real_nb_syllables_pkg",
    "child_real_nb_phonemes",
    "same_word_count_as_child_real",
    "delta_nb_words_vs_child_real",
    "delta_nb_morphemes_vs_child_real",
    "delta_nb_syllables_cmu_or_pkg_vs_child_real",
    "delta_nb_syllables_pkg_vs_child_real",
    "delta_nb_phonemes_vs_child_real",
    "model_used",
    "units_used",
    "text_cols_used",
]


def stable_hash(text: object, length: int = 20) -> str:
    """Return a short stable hash for row, target, and context keys."""

    value = normalize_text(text)
    if not value:
        return ""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def row_identity(row: Mapping[str, str], role: str) -> str:
    """Return a stable identity for the original child/caretaker utterance."""

    parts = [
        row.get("dataset", ""),
        row.get("child_id", ""),
        row.get("file", ""),
        row.get("line_no", ""),
        row.get("utt_id", ""),
        role,
    ]
    return stable_hash("|".join(parts), length=24)


def score_identity(utterance_id: str, target_variant: str, context_k: str, score_source: str) -> str:
    """Return a stable identity for one scored target/context row."""

    return stable_hash("|".join([utterance_id, target_variant, context_k, score_source]), length=24)


def parse_float(value: object) -> float | None:
    """Parse a float-like value, returning None for blanks."""

    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_float(value: float | None) -> str:
    """Format optional floats compactly for CSV output."""

    if value is None:
        return ""
    return f"{value:.12g}"


def safe_ratio(numerator: object, denominator: int) -> str:
    """Return numerator / denominator, blank when unavailable or zero."""

    parsed = parse_float(numerator)
    if parsed is None or denominator <= 0:
        return ""
    return format_float(parsed / denominator)


def variant_target_column(role: str, target_variant: str) -> str:
    """Map a scored-file variant to the utterance text column it scored."""

    if role == "caretaker":
        if target_variant != "caretaker":
            raise ValueError(f"Unexpected caretaker variant: {target_variant}")
        return "caretaker_utterance_clean"
    if target_variant == "real":
        return "chi_utterance_clean"
    if target_variant in CHILD_BASELINE_VARIANTS:
        return f"{target_variant}_model_utterance_bin6"
    if target_variant.startswith("lstm_"):
        return f"{target_variant}_utterance"
    raise ValueError(f"Unknown child target variant: {target_variant}")


def parse_scored_file(scored_root: Path, path: Path, score_source: str) -> ScoredFileSpec:
    """Infer context, role, and target variant from a scored CSV path."""

    rel = path.relative_to(scored_root)
    if len(rel.parts) < 6:
        raise ValueError(f"Scored path is not in the expected layout: {path}")
    context_condition, context_k, model_slug, dataset_dir, child_dir = rel.parts[:5]
    if context_k not in ROUTE1_CONTEXT_KS:
        raise ValueError(f"Unexpected context window {context_k!r} in {path}")
    name = path.name
    if not name.endswith(SCORED_SUFFIX) or "__" not in name:
        raise ValueError(f"Scored filename is not variant-tagged: {path}")
    target_variant = name.split("__", 1)[1][: -len(SCORED_SUFFIX)]
    role = "caretaker" if name.startswith("caretakers.") else "child"
    target_column = variant_target_column(role, target_variant)
    return ScoredFileSpec(
        path=path,
        score_source=score_source,
        context_condition=context_condition,
        context_k=context_k,
        model_slug=model_slug,
        dataset_dir=dataset_dir,
        child_dir=child_dir,
        role=role,
        target_variant=target_variant,
        target_column=target_column,
    )


def iter_scored_files(scored_root: Path, score_source: str) -> Iterator[ScoredFileSpec]:
    """Yield all scored CSV specs from one scored-result root."""

    for path in sorted(scored_root.rglob(f"*{SCORED_SUFFIX}")):
        yield parse_scored_file(scored_root, path, score_source)


def context_text_for_row(row: Mapping[str, str], spec: ScoredFileSpec) -> tuple[str, str]:
    """Return the exact context text used for this scored row."""

    context_col = normalize_text(row.get("context_col_used", ""))
    if not context_col and spec.context_k != "k0":
        context_col = f"context_{spec.context_k}"
    if spec.context_k == "k0":
        return "", context_col
    return normalize_text(row.get(context_col, "")), context_col


def token_morpheme_count(token: str) -> int:
    """Surface morpheme count contribution for one token."""

    return clitic_morpheme_count_for_token(token) + suffix_extra_morphemes(token)


def count_effort(text: object) -> EffortCounts:
    """Compute the final selected effort measures from one cleaned utterance."""

    return count_effort_cached(normalize_text(text))


@lru_cache(maxsize=750000)
def count_effort_cached(target: str) -> EffortCounts:
    """Cached implementation for repeated target strings across contexts."""

    tokens = tuple(word_tokens_regex(target))
    if not tokens:
        return EffortCounts(
            nb_words=0,
            nb_morphemes=0,
            nb_syllables_cmu_or_pkg=0,
            nb_syllables_pkg=0,
            nb_phonemes=0,
            cmu_oov_word_count=0,
            syllable_pkg_fallback_word_count=0,
            g2p_fallback_word_count=0,
            quality_flags="no_word_tokens",
        )

    syllable_hybrid = count_cmudict_or_syllables_pkg_utterance(tokens)
    phoneme_hybrid = count_cmudict_g2p_utterance(tokens)
    cmu_oov_count = sum(1 for token in tokens if first_cmu_pronunciation(token).pronunciation_count == 0)
    flags: list[str] = []
    if cmu_oov_count:
        flags.append("cmu_oov")
    if syllable_hybrid.fallback_word_count:
        flags.append("syllable_pkg_fallback_used")
    if phoneme_hybrid.hybrid_g2p_fallback_word_count:
        flags.append("g2p_fallback_used")
    return EffortCounts(
        nb_words=len(tokens),
        nb_morphemes=sum(token_morpheme_count(token) for token in tokens),
        nb_syllables_cmu_or_pkg=syllable_hybrid.syllable_count,
        nb_syllables_pkg=count_syllables_pkg(tokens),
        nb_phonemes=phoneme_hybrid.hybrid_phoneme_count,
        cmu_oov_word_count=cmu_oov_count,
        syllable_pkg_fallback_word_count=syllable_hybrid.fallback_word_count,
        g2p_fallback_word_count=phoneme_hybrid.hybrid_g2p_fallback_word_count,
        quality_flags=";".join(flags),
    )


def should_match_child_real_words(target_variant: str) -> bool:
    """Return whether a child generated target should preserve real child word count."""

    return target_variant in CHILD_BASELINE_VARIANTS or (
        target_variant.startswith("lstm_") and target_variant.endswith("_same_length")
    )


def effort_delta_columns(counts: EffortCounts, child_counts: EffortCounts | None) -> dict[str, object]:
    """Return child-real effort counts and deltas for child targets."""

    if child_counts is None:
        return {
            "child_real_nb_words": "",
            "child_real_nb_morphemes": "",
            "child_real_nb_syllables_cmu_or_pkg": "",
            "child_real_nb_syllables_pkg": "",
            "child_real_nb_phonemes": "",
            "same_word_count_as_child_real": "",
            "delta_nb_words_vs_child_real": "",
            "delta_nb_morphemes_vs_child_real": "",
            "delta_nb_syllables_cmu_or_pkg_vs_child_real": "",
            "delta_nb_syllables_pkg_vs_child_real": "",
            "delta_nb_phonemes_vs_child_real": "",
        }
    return {
        "child_real_nb_words": child_counts.nb_words,
        "child_real_nb_morphemes": child_counts.nb_morphemes,
        "child_real_nb_syllables_cmu_or_pkg": child_counts.nb_syllables_cmu_or_pkg,
        "child_real_nb_syllables_pkg": child_counts.nb_syllables_pkg,
        "child_real_nb_phonemes": child_counts.nb_phonemes,
        "same_word_count_as_child_real": int(counts.nb_words == child_counts.nb_words),
        "delta_nb_words_vs_child_real": counts.nb_words - child_counts.nb_words,
        "delta_nb_morphemes_vs_child_real": counts.nb_morphemes - child_counts.nb_morphemes,
        "delta_nb_syllables_cmu_or_pkg_vs_child_real": (
            counts.nb_syllables_cmu_or_pkg - child_counts.nb_syllables_cmu_or_pkg
        ),
        "delta_nb_syllables_pkg_vs_child_real": counts.nb_syllables_pkg - child_counts.nb_syllables_pkg,
        "delta_nb_phonemes_vs_child_real": counts.nb_phonemes - child_counts.nb_phonemes,
    }


def is_line_no_numeric(value: object) -> bool:
    """Return whether line_no can be parsed as a number."""

    return parse_float(value) is not None


def open_text_output(path: Path) -> TextIO:
    """Open plain or gzipped text output based on suffix."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        return gzip.open(path, "wt", encoding="utf-8", newline="")
    return path.open("w", encoding="utf-8", newline="")


def build_analysis_dataset(
    *,
    scored_roots: Sequence[tuple[str, Path]],
    output_csv: Path,
    file_audit_csv: Path,
    variant_audit_csv: Path,
    schema_json: Path,
    strict: bool = True,
    max_files: int | None = None,
) -> dict[str, object]:
    """Build the long analysis CSV and audits."""

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp_output_csv = temporary_output_path(output_csv)
    tmp_file_audit_csv = temporary_output_path(file_audit_csv)
    tmp_variant_audit_csv = temporary_output_path(variant_audit_csv)
    tmp_schema_json = temporary_output_path(schema_json)
    file_audits: list[FileAudit] = []
    group_audits: dict[tuple[str, str, str, str, str], GroupAudit] = defaultdict(GroupAudit)
    total_rows_written = 0
    total_files = 0

    cleanup_temporary_outputs(
        [tmp_output_csv, tmp_file_audit_csv, tmp_variant_audit_csv, tmp_schema_json]
    )

    with open_text_output(tmp_output_csv) as handle:
        writer = csv.DictWriter(handle, fieldnames=ANALYSIS_COLUMNS, lineterminator="\n")
        writer.writeheader()

        for score_source, scored_root in scored_roots:
            for spec in iter_scored_files(scored_root, score_source):
                if max_files is not None and total_files >= max_files:
                    break
                total_files += 1
                audit = process_scored_file(spec, writer, group_audits)
                file_audits.append(audit)
                total_rows_written += audit.rows_written
            if max_files is not None and total_files >= max_files:
                break

    write_file_audit(file_audits, tmp_file_audit_csv)
    write_variant_audit(group_audits, tmp_variant_audit_csv)
    write_schema(tmp_schema_json, scored_roots, output_csv, file_audit_csv, variant_audit_csv)
    if strict:
        validate_audits(file_audits)
    publish_temporary_outputs(
        [
            (tmp_output_csv, output_csv),
            (tmp_file_audit_csv, file_audit_csv),
            (tmp_variant_audit_csv, variant_audit_csv),
            (tmp_schema_json, schema_json),
        ]
    )

    return {
        "files_read": total_files,
        "rows_written": total_rows_written,
        "output_csv": str(output_csv),
        "file_audit_csv": str(file_audit_csv),
        "variant_audit_csv": str(variant_audit_csv),
        "schema_json": str(schema_json),
    }


def temporary_output_path(path: Path) -> Path:
    """Return a hidden sibling path used for atomic output publication."""

    return path.with_name(f".{path.name}.tmp")


def cleanup_temporary_outputs(paths: Sequence[Path]) -> None:
    """Remove stale temporary files left by an interrupted previous run."""

    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            continue


def publish_temporary_outputs(path_pairs: Sequence[tuple[Path, Path]]) -> None:
    """Atomically replace final outputs after all files have been validated."""

    for tmp_path, final_path in path_pairs:
        final_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_path, final_path)


def process_scored_file(
    spec: ScoredFileSpec,
    writer: csv.DictWriter,
    group_audits: dict[tuple[str, str, str, str, str], GroupAudit],
) -> FileAudit:
    """Read one scored file and append normalized analysis rows."""

    audit = FileAudit(
        score_source=spec.score_source,
        scored_file=str(spec.path),
        context_condition=spec.context_condition,
        context_k=spec.context_k,
        role=spec.role,
        target_variant=spec.target_variant,
        target_column=spec.target_column,
    )
    with spec.path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            audit.rows_read += 1
            if spec.target_column not in row:
                audit.missing_target_column_rows += 1
                continue

            target_text = normalize_text(row.get(spec.target_column, ""))
            if not target_text:
                audit.blank_target_rows += 1
            counts = count_effort(target_text)
            if counts.nb_words == 0:
                audit.zero_word_rows += 1
            if parse_float(row.get("sum_bits", "")) is None:
                audit.missing_sum_bits_rows += 1

            if not target_text or counts.nb_words == 0 or parse_float(row.get("sum_bits", "")) is None:
                audit.rows_skipped_unscored_or_empty += 1
                continue

            child_counts: EffortCounts | None = None
            if spec.role == "child":
                child_counts = count_effort(row.get("chi_utterance_clean", ""))
            deltas = effort_delta_columns(counts, child_counts)
            if (
                spec.role == "child"
                and should_match_child_real_words(spec.target_variant)
                and deltas["same_word_count_as_child_real"] != 1
            ):
                audit.child_word_count_mismatch_rows += 1

            age_months, age_source = resolve_age_months(row.get("age_months", ""), row.get("file", ""))
            age_bin = age_to_route1_bin(age_months)
            if age_bin is None:
                audit.missing_or_outside_age_bin_rows += 1
            if not is_line_no_numeric(row.get("line_no", "")):
                audit.nonnumeric_line_no_rows += 1

            context_text, context_col_used = context_text_for_row(row, spec)
            utterance_id = row_identity(row, spec.role)
            score_id = score_identity(utterance_id, spec.target_variant, spec.context_k, spec.score_source)
            out_row = build_analysis_row(
                spec=spec,
                source_row=row,
                counts=counts,
                deltas=deltas,
                target_text=target_text,
                context_text=context_text,
                context_col_used=context_col_used,
                age_months=age_months,
                age_source=age_source,
                age_bin=age_bin,
                utterance_id=utterance_id,
                score_id=score_id,
            )
            writer.writerow(out_row)
            audit.rows_written += 1

            group_key = (
                spec.score_source,
                spec.role,
                spec.target_variant,
                spec.context_condition,
                spec.context_k,
            )
            group_audits[group_key].add_row(
                counts=counts,
                sum_bits=row.get("sum_bits", ""),
                mean_bits_per_token=row.get("mean_bits_per_token", ""),
                n_eval_tokens=row.get("n_eval_tokens", ""),
                deltas={
                    key: value
                    for key, value in deltas.items()
                    if key.startswith("delta_") or key == "same_word_count_as_child_real"
                },
            )
    return audit


def build_analysis_row(
    *,
    spec: ScoredFileSpec,
    source_row: Mapping[str, str],
    counts: EffortCounts,
    deltas: Mapping[str, object],
    target_text: str,
    context_text: str,
    context_col_used: str,
    age_months: float | None,
    age_source: str,
    age_bin: str | None,
    utterance_id: str,
    score_id: str,
) -> dict[str, object]:
    """Return one normalized row for the long modeling CSV."""

    return {
        "score_source": spec.score_source,
        "score_id": score_id,
        "utterance_id": utterance_id,
        "dataset": source_row.get("dataset", spec.dataset_dir),
        "child_id": source_row.get("child_id", spec.child_dir),
        "source_group": source_row.get("source_group", ""),
        "session_id": source_row.get("session_id", ""),
        "age_months": "" if age_months is None else format_float(age_months),
        "age_months_source": age_source,
        "age_bin": age_bin or "",
        "file": source_row.get("file", ""),
        "line_no": source_row.get("line_no", ""),
        "utt_id": source_row.get("utt_id", ""),
        "speaker": source_row.get("speaker", ""),
        "role": spec.role,
        "target_variant": spec.target_variant,
        "target_column": spec.target_column,
        "target_utterance_clean": target_text,
        "target_text_hash": stable_hash(target_text),
        "context_condition": spec.context_condition,
        "context_k": spec.context_k,
        "context_col_used": context_col_used,
        "context_text": context_text,
        "context_text_hash": stable_hash(context_text),
        "mean_bits_per_token": source_row.get("mean_bits_per_token", ""),
        "sum_bits": source_row.get("sum_bits", ""),
        "n_eval_tokens": source_row.get("n_eval_tokens", ""),
        "bits_per_word": safe_ratio(source_row.get("sum_bits", ""), counts.nb_words),
        "bits_per_morpheme": safe_ratio(source_row.get("sum_bits", ""), counts.nb_morphemes),
        "bits_per_syllable_cmu_or_pkg": safe_ratio(
            source_row.get("sum_bits", ""), counts.nb_syllables_cmu_or_pkg
        ),
        "bits_per_syllable_pkg": safe_ratio(source_row.get("sum_bits", ""), counts.nb_syllables_pkg),
        "bits_per_phoneme": safe_ratio(source_row.get("sum_bits", ""), counts.nb_phonemes),
        "nb_words": counts.nb_words,
        "nb_morphemes": counts.nb_morphemes,
        "nb_syllables_cmu_or_pkg": counts.nb_syllables_cmu_or_pkg,
        "nb_syllables_pkg": counts.nb_syllables_pkg,
        "nb_phonemes": counts.nb_phonemes,
        "cmu_oov_word_count": counts.cmu_oov_word_count,
        "syllable_pkg_fallback_word_count": counts.syllable_pkg_fallback_word_count,
        "g2p_fallback_word_count": counts.g2p_fallback_word_count,
        "effort_quality_flags": counts.quality_flags,
        **deltas,
        "model_used": source_row.get("model_used", ""),
        "units_used": source_row.get("units_used", ""),
        "text_cols_used": source_row.get("text_cols_used", ""),
    }


def write_file_audit(file_audits: Sequence[FileAudit], output_csv: Path) -> None:
    """Write per-file audits."""

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(FileAudit.__dataclass_fields__),
            lineterminator="\n",
        )
        writer.writeheader()
        for audit in file_audits:
            writer.writerow(asdict(audit))


def write_variant_audit(
    group_audits: Mapping[tuple[str, str, str, str, str], GroupAudit],
    output_csv: Path,
) -> None:
    """Write role/variant/context audit summaries."""

    fieldnames = [
        "score_source",
        "role",
        "target_variant",
        "context_condition",
        "context_k",
        "rows",
        "mean_sum_bits",
        "mean_bits_per_token",
        "mean_n_eval_tokens",
        "mean_nb_words",
        "mean_nb_morphemes",
        "mean_nb_syllables_cmu_or_pkg",
        "mean_nb_syllables_pkg",
        "mean_nb_phonemes",
        "mean_cmu_oov_word_count",
        "mean_syllable_pkg_fallback_word_count",
        "mean_g2p_fallback_word_count",
        "mean_same_word_count_as_child_real",
        "mean_delta_nb_words_vs_child_real",
        "mean_delta_nb_morphemes_vs_child_real",
        "mean_delta_nb_syllables_cmu_or_pkg_vs_child_real",
        "mean_delta_nb_syllables_pkg_vs_child_real",
        "mean_delta_nb_phonemes_vs_child_real",
    ]
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for key in sorted(group_audits):
            score_source, role, target_variant, context_condition, context_k = key
            audit = group_audits[key]
            row: dict[str, object] = {
                "score_source": score_source,
                "role": role,
                "target_variant": target_variant,
                "context_condition": context_condition,
                "context_k": context_k,
                "rows": audit.rows,
            }
            for field in fieldnames[6:]:
                stat_key = variant_audit_stat_key(field)
                row[field] = format_float(audit.stats[stat_key].mean)
            writer.writerow(row)


def variant_audit_stat_key(field: str) -> str:
    """Map variant-audit mean columns to the internal stats key."""

    if field == "mean_bits_per_token":
        return "mean_bits_per_token"
    return field.removeprefix("mean_")


def write_schema(
    schema_json: Path,
    scored_roots: Sequence[tuple[str, Path]],
    output_csv: Path,
    file_audit_csv: Path,
    variant_audit_csv: Path,
) -> None:
    """Write a lightweight machine-readable schema and provenance note."""

    schema_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_for": "utterance-level communicative-efficiency modeling",
        "scored_roots": [{"score_source": name, "path": str(path)} for name, path in scored_roots],
        "outputs": {
            "long_csv": str(output_csv),
            "source_file_audit": str(file_audit_csv),
            "variant_context_audit": str(variant_audit_csv),
        },
        "row_grain": "one scored target utterance under one context condition",
        "age_bins": ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"],
        "effort_measures": {
            "nb_words": "regex lexical tokens in the exact cleaned scored target",
            "nb_morphemes": "surface clitic/suffix heuristic, selected as auto_morphemes_surface",
            "nb_syllables_cmu_or_pkg": "CMUdict syllables when covered, syllables package for OOV forms",
            "nb_syllables_pkg": "syllables package applied to every token",
            "nb_phonemes": "CMUdict phonemes when covered, g2p-en ARPABET prediction for OOV forms",
        },
        "columns": ANALYSIS_COLUMNS,
    }
    schema_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def validate_audits(file_audits: Sequence[FileAudit]) -> None:
    """Fail loudly on problems that would make the analysis dataset unsafe."""

    totals: Counter[str] = Counter()
    for audit in file_audits:
        totals["missing_target_column_rows"] += audit.missing_target_column_rows
        totals["missing_or_outside_age_bin_rows"] += audit.missing_or_outside_age_bin_rows
        totals["nonnumeric_line_no_rows"] += audit.nonnumeric_line_no_rows
        totals["child_word_count_mismatch_rows"] += audit.child_word_count_mismatch_rows
    problems = {key: value for key, value in totals.items() if value}
    if problems:
        details = ", ".join(f"{key}={value}" for key, value in sorted(problems.items()))
        raise ValueError(f"Analysis dataset audit failed: {details}")


def parse_score_root(value: str) -> tuple[str, Path]:
    """Parse score-source-name=path CLI values."""

    if "=" not in value:
        raise argparse.ArgumentTypeError("score roots must be formatted as name=path")
    name, path = value.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("score source name cannot be blank")
    return name, Path(path)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--score-root",
        action="append",
        type=parse_score_root,
        default=None,
        help=(
            "Scored root as name=path. May be repeated. Defaults to the patched "
            "PBM Mistral random/unigram/bigram/trigram tree."
        ),
    )
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_LONG_CSV)
    parser.add_argument("--file-audit-csv", type=Path, default=DEFAULT_FILE_AUDIT_CSV)
    parser.add_argument("--variant-audit-csv", type=Path, default=DEFAULT_VARIANT_AUDIT_CSV)
    parser.add_argument("--schema-json", type=Path, default=DEFAULT_SCHEMA_JSON)
    parser.add_argument("--max-files", type=int, default=None, help="Debug limit for smoke runs.")
    parser.add_argument("--no-strict", action="store_true", help="Write outputs even if audits find problems.")
    return parser


def main() -> None:
    args = build_cli().parse_args()
    scored_roots = args.score_root or [("pbm_mistral_patched_006_023", DEFAULT_MAIN_SCORED_ROOT)]
    result = build_analysis_dataset(
        scored_roots=scored_roots,
        output_csv=args.output_csv,
        file_audit_csv=args.file_audit_csv,
        variant_audit_csv=args.variant_audit_csv,
        schema_json=args.schema_json,
        strict=not args.no_strict,
        max_files=args.max_files,
    )
    print(f"[OK] Wrote {result['rows_written']} analysis rows from {result['files_read']} scored files")
    print(f"[OK] Long CSV: {result['output_csv']}")
    print(f"[OK] File audit: {result['file_audit_csv']}")
    print(f"[OK] Variant audit: {result['variant_audit_csv']}")


if __name__ == "__main__":
    main()
