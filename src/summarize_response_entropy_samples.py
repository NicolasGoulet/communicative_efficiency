#!/usr/bin/env python3
"""Summarize sampled responses into empirical response-entropy predictors."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Sequence

import pandas as pd
import syllables

try:
    from utterance_count_strategies import count_morphemes_suffix_heuristic, word_tokens_regex
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.utterance_count_strategies import count_morphemes_suffix_heuristic, word_tokens_regex


DEFAULT_SAMPLES = Path("results/response_level_context_entropy/context_response_samples.csv.gz")
DEFAULT_OUTPUT = Path("results/response_level_context_entropy/context_response_entropy_features.csv")
SPACES_RE = re.compile(r"\s+")


def canonical_response(text: object, *, mode: str) -> str:
    """Return a response type string for empirical entropy counts."""

    value = "" if text is None or (isinstance(text, float) and math.isnan(text)) else str(text)
    value = SPACES_RE.sub(" ", value).strip()
    if mode == "casefold":
        value = value.casefold()
    elif mode != "exact":
        raise ValueError(f"unknown response normalization mode: {mode}")
    return value if value else "<EMPTY_RESPONSE>"


def empirical_entropy_bits(counts: Counter[str]) -> float:
    """MLE empirical entropy in bits from response-type counts."""

    total = sum(counts.values())
    if total <= 0:
        return math.nan
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def miller_madow_entropy_bits(entropy_bits: float, *, unique_count: int, sample_count: int) -> float:
    """Miller-Madow finite-sample correction in bits."""

    if not math.isfinite(entropy_bits) or sample_count <= 0:
        return math.nan
    return entropy_bits + (max(unique_count, 1) - 1) / (2 * sample_count * math.log(2.0))


def response_word_count(text: object) -> int:
    """Count word-like response tokens."""

    return len(word_tokens_regex(text))


def response_syllable_pkg_count(text: object) -> int:
    """Estimate syllables for response words using the lightweight package."""

    return sum(max(1, int(syllables.estimate(token.lower()))) for token in word_tokens_regex(text))


def response_effort_counts(text: object) -> dict[str, int]:
    """Return lightweight effort counts for sampled responses."""

    return {
        "sample_word_count": response_word_count(text),
        "sample_morpheme_count_surface": count_morphemes_suffix_heuristic(text),
        "sample_syllable_count_pkg": response_syllable_pkg_count(text),
    }


def summarize_group(group: pd.DataFrame, *, normalization: str, top_n: int) -> dict[str, object]:
    """Summarize one context/temperature group."""

    canonical = [canonical_response(text, mode=normalization) for text in group["sampled_response_text"].tolist()]
    counts = Counter(canonical)
    sample_count = sum(counts.values())
    unique_count = len(counts)
    entropy = empirical_entropy_bits(counts)
    corrected = miller_madow_entropy_bits(entropy, unique_count=unique_count, sample_count=sample_count)
    most_common = counts.most_common(top_n)
    top_response, top_count = most_common[0] if most_common else ("", 0)
    effort_rows = [response_effort_counts(text) for text in group["sampled_response_text"].tolist()]
    effort = pd.DataFrame(effort_rows)
    log2_samples = math.log2(sample_count) if sample_count > 1 else math.nan
    log2_unique = math.log2(unique_count) if unique_count > 1 else math.nan
    return {
        "sample_count": sample_count,
        "unique_response_count": unique_count,
        "response_entropy_mle_bits": entropy,
        "response_entropy_miller_madow_bits": corrected,
        "response_entropy_normalized_by_sample_cap": entropy / log2_samples if log2_samples and math.isfinite(log2_samples) else math.nan,
        "response_evenness_observed_types": entropy / log2_unique if log2_unique and math.isfinite(log2_unique) else math.nan,
        "top_response_text": top_response,
        "top_response_count": top_count,
        "top_response_probability": top_count / sample_count if sample_count else math.nan,
        "mean_sample_word_count": float(effort["sample_word_count"].mean()) if not effort.empty else math.nan,
        "mean_sample_morpheme_count_surface": float(effort["sample_morpheme_count_surface"].mean()) if not effort.empty else math.nan,
        "mean_sample_syllable_count_pkg": float(effort["sample_syllable_count_pkg"].mean()) if not effort.empty else math.nan,
        "response_type_counts_json": json.dumps(
            [{"response": response, "count": int(count)} for response, count in most_common],
            ensure_ascii=False,
        ),
    }


def summarize_samples(
    *,
    samples_csv: Path,
    output_csv: Path,
    normalization: str,
    top_n: int,
) -> pd.DataFrame:
    """Write one feature row per context and temperature."""

    samples = pd.read_csv(samples_csv, dtype=str, keep_default_na=False, low_memory=False)
    required = {"context_id", "temperature", "sampled_response_text"}
    missing = required - set(samples.columns)
    if missing:
        raise KeyError(f"{samples_csv} missing required columns: {sorted(missing)}")
    samples["temperature"] = pd.to_numeric(samples["temperature"], errors="coerce")
    rows: list[dict[str, object]] = []
    group_cols = ["context_id", "temperature"]
    passthrough_cols = ["manifest_row", "context_text", "prompt_text", "model_used", "max_new_tokens", "top_p"]
    for keys, group in samples.groupby(group_cols, sort=True, dropna=False):
        context_id, temperature = keys
        summary = {"context_id": context_id, "temperature": temperature, "response_normalization": normalization}
        for col in passthrough_cols:
            if col in group.columns:
                summary[col] = group[col].iloc[0]
        summary.update(summarize_group(group, normalization=normalization, top_n=top_n))
        rows.append(summary)
    out = pd.DataFrame(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--normalization", choices=["exact", "casefold"], default="exact")
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args(argv)
    out = summarize_samples(
        samples_csv=args.samples,
        output_csv=args.output,
        normalization=args.normalization,
        top_n=args.top_n,
    )
    print(f"[OK] wrote {len(out):,} context-temperature entropy rows to {args.output}")


if __name__ == "__main__":
    main()

