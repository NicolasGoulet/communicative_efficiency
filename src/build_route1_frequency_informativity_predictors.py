#!/usr/bin/env python3
"""Build reusable frequency/informativity predictors for Route 1 utterances.

The phonological CDS paper motivates a separate predictor layer for frequency
and informativity. This script creates joinable text-level predictors keyed by
``target_text_hash`` so later ANCOVA/regression reports can add lexical and
phonological frequency controls without re-reading all scored outputs.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
import pronouncing

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from utterance_count_strategies import normalize_text, word_tokens_regex
except ModuleNotFoundError:  # pragma: no cover
    from src.utterance_count_strategies import normalize_text, word_tokens_regex


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_frequency_informativity_predictors")
DEFAULT_CHUNKSIZE = 500_000
SOURCES = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
    "lstm_additive_k3_same_length": "LSTM k3",
    "lstm_additive_k4_same_length": "LSTM k4",
    "lstm_additive_k5_same_length": "LSTM k5",
    "caretaker": "Caretaker",
}
REFERENCE_SCOPES = {
    "caretaker_cds": {"caretaker"},
    "real_child": {"real"},
    "real_plus_caretaker": {"real", "caretaker"},
}
START = "<s>"
ALPHA = 0.1


@dataclass
class ReferenceCounts:
    word_counts: Counter[str]
    phone_counts: Counter[str]
    phone_bigram_counts: Counter[tuple[str, str]]
    phone_prev_counts: Counter[str]
    utterance_counts: Counter[str]
    row_count: int = 0


def make_reference_counts() -> dict[str, ReferenceCounts]:
    return {
        scope: ReferenceCounts(Counter(), Counter(), Counter(), Counter(), Counter(), 0)
        for scope in REFERENCE_SCOPES
    }


def strip_stress(phone: str) -> str:
    return phone.rstrip("0123456789")


@lru_cache(maxsize=500_000)
def orthographic_fallback_phones(token: str) -> tuple[str, ...]:
    letters = [char.upper() for char in token if char.isalpha()]
    return tuple(f"ORTH_{char}" for char in letters) or ("ORTH",)


@lru_cache(maxsize=500_000)
def token_phones(token: str, fallback: str = "orthographic") -> tuple[str, ...]:
    cmu_phones = pronouncing.phones_for_word(token.lower())
    if cmu_phones:
        phones = cmu_phones[0].split()
    elif fallback == "g2p":
        raise RuntimeError("g2p fallback is disabled in this stable predictor builder; use orthographic fallback")
    else:
        return orthographic_fallback_phones(token)
    phones = tuple(strip_stress(phone) for phone in phones if phone)
    return phones or ("ORTH",)


@lru_cache(maxsize=750_000)
def text_units(text: str, fallback: str = "orthographic") -> tuple[tuple[str, ...], tuple[str, ...]]:
    tokens = tuple(token.lower() for token in word_tokens_regex(normalize_text(text)))
    phones: list[str] = []
    for token in tokens:
        phones.extend(token_phones(token, fallback))
    return tokens, tuple(phones)


def update_reference(counts: ReferenceCounts, text_hash: str, tokens: Sequence[str], phones: Sequence[str]) -> None:
    counts.row_count += 1
    counts.utterance_counts[text_hash] += 1
    counts.word_counts.update(tokens)
    counts.phone_counts.update(phones)
    previous = START
    for phone in phones:
        counts.phone_bigram_counts[(previous, phone)] += 1
        counts.phone_prev_counts[previous] += 1
        previous = phone


def bits_from_count(count: int, total: int, vocab: int, *, alpha: float = ALPHA) -> float:
    denom = total + alpha * max(vocab, 1)
    prob = (count + alpha) / denom if denom > 0 else 0.0
    if prob <= 0:
        return math.nan
    return -math.log2(prob)


def score_unigrams(units: Sequence[str], counts: Counter[str]) -> tuple[float, float]:
    if not units:
        return math.nan, math.nan
    total = sum(counts.values())
    vocab = len(counts) + 1
    bits = [bits_from_count(counts.get(unit, 0), total, vocab) for unit in units]
    total_bits = float(sum(bits))
    return total_bits, total_bits / len(units)


def score_phone_bigrams(phones: Sequence[str], counts: ReferenceCounts) -> tuple[float, float]:
    if not phones:
        return math.nan, math.nan
    vocab = len(counts.phone_counts) + 1
    previous = START
    bits = []
    for phone in phones:
        numerator = counts.phone_bigram_counts.get((previous, phone), 0)
        denominator = counts.phone_prev_counts.get(previous, 0)
        prob = (numerator + ALPHA) / (denominator + ALPHA * max(vocab, 1)) if denominator >= 0 else math.nan
        bits.append(-math.log2(prob) if prob > 0 else math.nan)
        previous = phone
    total_bits = float(sum(bit for bit in bits if math.isfinite(bit)))
    return total_bits, total_bits / len(phones)


def collect_references(input_csv: Path, *, chunksize: int, fallback: str) -> tuple[dict[str, str], dict[str, ReferenceCounts], pd.DataFrame]:
    usecols = ["target_variant", "context_k", "target_text_hash", "target_utterance_clean", "age_bin"]
    unique_texts: dict[str, str] = {}
    references = make_reference_counts()
    source_age_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    reader = pd.read_csv(input_csv, usecols=usecols, chunksize=chunksize, engine="python", on_bad_lines="skip")
    for chunk_index, chunk in enumerate(reader, start=1):
        chunk = chunk[chunk["context_k"].eq("k3") & chunk["target_variant"].isin(SOURCES)].copy()
        if chunk.empty:
            continue
        for row in chunk.itertuples(index=False):
            text_hash = str(row.target_text_hash)
            text = normalize_text(row.target_utterance_clean)
            if not text_hash or not text:
                continue
            unique_texts.setdefault(text_hash, text)
            source = str(row.target_variant)
            source_age_counts[(source, str(row.age_bin))] += 1
            if source not in {"real", "caretaker"}:
                continue
            tokens, phones = text_units(text, fallback)
            for scope, scope_sources in REFERENCE_SCOPES.items():
                if source in scope_sources:
                    update_reference(references[scope], text_hash, tokens, phones)
        print(f"[collect] processed chunk {chunk_index}; unique_texts={len(unique_texts):,}", flush=True)
    source_age = pd.DataFrame(
        [
            {"source": source, "source_label": SOURCES.get(source, source), "age_bin": age_bin, "rows": rows}
            for (source, age_bin), rows in source_age_counts.items()
        ]
    )
    return unique_texts, references, source_age


def score_texts(unique_texts: dict[str, str], references: dict[str, ReferenceCounts], *, fallback: str) -> pd.DataFrame:
    rows = []
    for index, (text_hash, text) in enumerate(unique_texts.items(), start=1):
        tokens, phones = text_units(text, fallback)
        for scope, counts in references.items():
            word_sum, word_mean = score_unigrams(tokens, counts.word_counts)
            phone_sum, phone_mean = score_unigrams(phones, counts.phone_counts)
            phone_bigram_sum, phone_bigram_mean = score_phone_bigrams(phones, counts)
            rows.append(
                {
                    "target_text_hash": text_hash,
                    "reference_scope": scope,
                    "word_count": len(tokens),
                    "phone_count": len(phones),
                    "reference_row_count": counts.row_count,
                    "reference_utterance_frequency": counts.utterance_counts.get(text_hash, 0),
                    "word_unigram_sum_bits": word_sum,
                    "word_unigram_mean_bits": word_mean,
                    "phone_unigram_sum_bits": phone_sum,
                    "phone_unigram_mean_bits": phone_mean,
                    "phone_bigram_sum_bits": phone_bigram_sum,
                    "phone_bigram_mean_bits": phone_bigram_mean,
                }
            )
        if index % 100_000 == 0:
            print(f"[score] scored {index:,} unique texts", flush=True)
    return pd.DataFrame(rows)


def write_reference_counts(references: dict[str, ReferenceCounts], output_dir: Path) -> None:
    word_rows = []
    phone_rows = []
    bigram_rows = []
    for scope, counts in references.items():
        for unit, count in counts.word_counts.items():
            word_rows.append({"reference_scope": scope, "unit": unit, "count": count})
        for phone, count in counts.phone_counts.items():
            phone_rows.append({"reference_scope": scope, "phone": phone, "count": count})
        for (previous, phone), count in counts.phone_bigram_counts.items():
            bigram_rows.append({"reference_scope": scope, "previous_phone": previous, "phone": phone, "count": count})
    pd.DataFrame(word_rows).to_csv(output_dir / "reference_word_counts.csv.gz", index=False)
    pd.DataFrame(phone_rows).to_csv(output_dir / "reference_phone_counts.csv", index=False)
    pd.DataFrame(bigram_rows).to_csv(output_dir / "reference_phone_bigram_counts.csv", index=False)


def summarize_by_source_age(input_csv: Path, predictors: pd.DataFrame, output_dir: Path, *, chunksize: int) -> pd.DataFrame:
    default = predictors[predictors["reference_scope"].eq("real_plus_caretaker")].copy()
    keep = [
        "target_text_hash",
        "reference_utterance_frequency",
        "word_unigram_mean_bits",
        "phone_unigram_mean_bits",
        "phone_bigram_mean_bits",
    ]
    mapping = default[keep].drop_duplicates("target_text_hash")
    chunks = []
    usecols = ["target_variant", "context_k", "target_text_hash", "age_bin"]
    reader = pd.read_csv(input_csv, usecols=usecols, chunksize=chunksize, engine="python", on_bad_lines="skip")
    for chunk in reader:
        chunk = chunk[chunk["context_k"].eq("k3") & chunk["target_variant"].isin(SOURCES)].copy()
        if chunk.empty:
            continue
        chunk = chunk.merge(mapping, on="target_text_hash", how="left")
        grouped = (
            chunk.groupby(["target_variant", "age_bin"], as_index=False)
            .agg(
                rows=("target_text_hash", "size"),
                mean_reference_utterance_frequency=("reference_utterance_frequency", "mean"),
                mean_word_unigram_bits=("word_unigram_mean_bits", "mean"),
                mean_phone_unigram_bits=("phone_unigram_mean_bits", "mean"),
                mean_phone_bigram_bits=("phone_bigram_mean_bits", "mean"),
            )
        )
        chunks.append(grouped)
    if not chunks:
        return pd.DataFrame()
    partial = pd.concat(chunks, ignore_index=True)
    # Chunk means are weighted back together by row counts.
    rows = []
    for (source, age_bin), group in partial.groupby(["target_variant", "age_bin"], observed=True):
        weights = group["rows"]
        rows.append(
            {
                "source": source,
                "source_label": SOURCES.get(source, source),
                "age_bin": age_bin,
                "rows": int(weights.sum()),
                "mean_reference_utterance_frequency": float((group["mean_reference_utterance_frequency"] * weights).sum() / weights.sum()),
                "mean_word_unigram_bits": float((group["mean_word_unigram_bits"] * weights).sum() / weights.sum()),
                "mean_phone_unigram_bits": float((group["mean_phone_unigram_bits"] * weights).sum() / weights.sum()),
                "mean_phone_bigram_bits": float((group["mean_phone_bigram_bits"] * weights).sum() / weights.sum()),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(output_dir / "source_age_frequency_informativity_summary.csv", index=False)
    return out


def build_predictors(input_csv: Path, output_dir: Path, *, chunksize: int, fallback: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    unique_texts, references, source_age = collect_references(input_csv, chunksize=chunksize, fallback=fallback)
    text_manifest = pd.DataFrame(
        [{"target_text_hash": text_hash, "target_utterance_clean": text} for text_hash, text in unique_texts.items()]
    )
    text_manifest.to_csv(output_dir / "unique_target_text_manifest.csv.gz", index=False)
    source_age.to_csv(output_dir / "source_age_scoring_row_counts.csv", index=False)
    write_reference_counts(references, output_dir)
    predictors = score_texts(unique_texts, references, fallback=fallback)
    predictors.to_csv(output_dir / "text_frequency_informativity_predictors.csv.gz", index=False)
    summarize_by_source_age(input_csv, predictors, output_dir, chunksize=chunksize)
    dictionary = pd.DataFrame(
        [
            {
                "predictor": "reference_utterance_frequency",
                "meaning": "How often this exact target text appears in the reference scope.",
            },
            {
                "predictor": "word_unigram_mean_bits",
                "meaning": "Mean negative log2 unigram probability of the utterance's word tokens under the reference scope.",
            },
            {
                "predictor": "phone_unigram_mean_bits",
                "meaning": f"Mean negative log2 unigram probability of CMU ARPABET phones under the reference scope; OOV fallback mode: {fallback}.",
            },
            {
                "predictor": "phone_bigram_mean_bits",
                "meaning": f"Mean negative log2 phone bigram probability with a start symbol under the reference scope; OOV fallback mode: {fallback}.",
            },
        ]
    )
    dictionary.to_csv(output_dir / "predictor_dictionary.csv", index=False)
    print(output_dir / "text_frequency_informativity_predictors.csv.gz")


def build_hash_frequency_predictors(input_csv: Path, output_dir: Path, *, chunksize: int) -> None:
    """Build safe exact-target recurrence predictors without reading text."""

    output_dir.mkdir(parents=True, exist_ok=True)
    reference_counts = {scope: Counter() for scope in REFERENCE_SCOPES}
    source_age_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    all_hashes: set[str] = set()
    opener = gzip.open if str(input_csv).endswith(".gz") else open
    total_rows = 0
    kept_rows = 0
    with opener(input_csv, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total_rows += 1
            if row.get("context_k") != "k3":
                if total_rows % chunksize == 0:
                    print(f"[hash-frequency] scanned {total_rows:,}; kept={kept_rows:,}; hashes={len(all_hashes):,}", flush=True)
                continue
            source = row.get("target_variant", "")
            if source not in SOURCES:
                continue
            text_hash = str(row.get("target_text_hash", "")).strip()
            if not text_hash:
                continue
            kept_rows += 1
            age_bin = str(row.get("age_bin", ""))
            all_hashes.add(text_hash)
            source_age_counts[(source, age_bin)] += 1
            if source not in {"real", "caretaker"}:
                if total_rows % chunksize == 0:
                    print(f"[hash-frequency] scanned {total_rows:,}; kept={kept_rows:,}; hashes={len(all_hashes):,}", flush=True)
                continue
            for scope, scope_sources in REFERENCE_SCOPES.items():
                if source in scope_sources:
                    reference_counts[scope][text_hash] += 1
            if total_rows % chunksize == 0:
                print(f"[hash-frequency] scanned {total_rows:,}; kept={kept_rows:,}; hashes={len(all_hashes):,}", flush=True)
    if not all_hashes:
        raise RuntimeError("No k3 target hashes found for hash-frequency predictors.")

    predictor_path = output_dir / "hash_frequency_predictors.csv.gz"
    totals = {scope: sum(counts.values()) for scope, counts in reference_counts.items()}
    vocabs = {scope: len(counts) + 1 for scope, counts in reference_counts.items()}
    with gzip.open(predictor_path, "wt", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "target_text_hash",
            "reference_scope",
            "reference_row_count",
            "exact_target_frequency",
            "exact_target_frequency_bits",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, text_hash in enumerate(sorted(all_hashes), start=1):
            for scope, counts in reference_counts.items():
                count = int(counts.get(text_hash, 0))
                writer.writerow(
                    {
                        "target_text_hash": text_hash,
                        "reference_scope": scope,
                        "reference_row_count": totals[scope],
                        "exact_target_frequency": count,
                        "exact_target_frequency_bits": bits_from_count(count, totals[scope], vocabs[scope]),
                    }
                )
            if index % 250_000 == 0:
                print(f"[hash-frequency] wrote predictors for {index:,} hashes", flush=True)
    source_age = pd.DataFrame(
        [
            {"source": source, "source_label": SOURCES.get(source, source), "age_bin": age_bin, "rows": rows}
            for (source, age_bin), rows in source_age_counts.items()
        ]
    )
    source_age.to_csv(output_dir / "source_age_scoring_row_counts.csv", index=False)
    dictionary = pd.DataFrame(
        [
            {
                "predictor": "exact_target_frequency",
                "meaning": "How often the exact target text hash appears in the reference scope among k3 rows.",
            },
            {
                "predictor": "exact_target_frequency_bits",
                "meaning": "Negative log2 smoothed exact-target frequency under the reference scope.",
            },
        ]
    )
    dictionary.to_csv(output_dir / "hash_frequency_predictor_dictionary.csv", index=False)
    print(predictor_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--chunksize", type=int, default=DEFAULT_CHUNKSIZE)
    parser.add_argument("--fallback", choices=["orthographic"], default="orthographic")
    parser.add_argument("--mode", choices=["hash-only", "text"], default="hash-only")
    args = parser.parse_args()
    if args.mode == "hash-only":
        build_hash_frequency_predictors(args.input, args.output_dir, chunksize=args.chunksize)
    else:
        build_predictors(args.input, args.output_dir, chunksize=args.chunksize, fallback=args.fallback)


if __name__ == "__main__":
    main()
