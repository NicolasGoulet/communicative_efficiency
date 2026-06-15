#!/usr/bin/env python3
"""Attach response-level entropy features to a Route 1 long table.

This script does not recompute entropy. It joins the per-context features from
``summarize_response_entropy_samples.py`` back onto utterance rows by a stable
hash of the normalized context text.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import pandas as pd

try:
    from build_response_entropy_manifest import context_id, normalize_context
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_response_entropy_manifest import context_id, normalize_context


DEFAULT_ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
DEFAULT_FEATURES = Path("results/response_level_context_entropy/context_response_entropy_features.csv")
DEFAULT_OUTPUT = Path("results/route1_analysis_dataset/route1_with_response_entropy_long.csv.gz")

FEATURE_COLUMNS = [
    "sample_count",
    "unique_response_count",
    "response_entropy_mle_bits",
    "response_entropy_miller_madow_bits",
    "response_entropy_normalized_by_sample_cap",
    "response_evenness_observed_types",
    "top_response_probability",
    "mean_sample_word_count",
    "mean_sample_morpheme_count_surface",
    "mean_sample_syllable_count_pkg",
    "model_used",
    "top_p",
    "max_new_tokens",
]


def load_temperature_features(features_csv: Path, *, temperature: float) -> pd.DataFrame:
    """Load one temperature slice of context-level features."""

    features = pd.read_csv(features_csv, dtype=str, keep_default_na=False, low_memory=False)
    required = {"context_id", "temperature"} | set(FEATURE_COLUMNS)
    missing = required - set(features.columns)
    if missing:
        raise KeyError(f"{features_csv} missing required columns: {sorted(missing)}")
    features["temperature_numeric"] = pd.to_numeric(features["temperature"], errors="coerce")
    selected = features[features["temperature_numeric"].round(6) == round(float(temperature), 6)].copy()
    if selected.empty:
        available = sorted(features["temperature"].dropna().astype(str).unique().tolist())
        raise ValueError(f"no response-entropy rows for temperature={temperature}; available={available}")
    selected = selected.drop_duplicates(subset=["context_id"], keep="first").copy()
    keep = ["context_id", "temperature"] + FEATURE_COLUMNS
    selected = selected[keep].rename(
        columns={
            "context_id": "response_entropy_context_id",
            "temperature": "response_entropy_temperature",
            "sample_count": "response_entropy_sample_count",
            "unique_response_count": "response_entropy_unique_response_count",
            "top_response_probability": "response_entropy_top_response_probability",
            "mean_sample_word_count": "response_entropy_mean_sample_word_count",
            "mean_sample_morpheme_count_surface": "response_entropy_mean_sample_morpheme_count_surface",
            "mean_sample_syllable_count_pkg": "response_entropy_mean_sample_syllable_count_pkg",
            "model_used": "response_entropy_model_used",
            "top_p": "response_entropy_top_p",
            "max_new_tokens": "response_entropy_max_new_tokens",
        }
    )
    return selected


def attach_features_chunk(chunk: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """Attach response entropy features to one Route 1 chunk without dropping rows."""

    if "context_text" not in chunk.columns:
        raise KeyError("input table must contain context_text")
    chunk = chunk.copy()
    chunk["response_entropy_context_id"] = chunk["context_text"].map(lambda text: context_id(normalize_context(text)))
    out = chunk.merge(features, on="response_entropy_context_id", how="left", validate="many_to_one")
    out["response_entropy_context_matched"] = out["response_entropy_sample_count"].notna()
    return out


def attach_response_entropy_features(
    *,
    input_csv: Path,
    features_csv: Path,
    output_csv: Path,
    temperature: float,
    chunksize: int,
) -> dict[str, int]:
    """Chunk through a Route 1 table, attach features, and write a new table."""

    features = load_temperature_features(features_csv, temperature=temperature)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    matched_rows = 0
    first = True
    for chunk in pd.read_csv(input_csv, chunksize=chunksize, dtype=str, keep_default_na=False, low_memory=False):
        out = attach_features_chunk(chunk, features)
        total_rows += len(out)
        matched_rows += int(out["response_entropy_context_matched"].sum())
        out.to_csv(output_csv, mode="w" if first else "a", header=first, index=False)
        first = False
    return {"rows": total_rows, "matched_rows": matched_rows, "unmatched_rows": total_rows - matched_rows}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ROUTE1_INPUT)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--chunksize", type=int, default=250_000)
    args = parser.parse_args(argv)
    summary = attach_response_entropy_features(
        input_csv=args.input,
        features_csv=args.features,
        output_csv=args.output,
        temperature=args.temperature,
        chunksize=args.chunksize,
    )
    print(
        "[OK] wrote {rows:,} rows to {output}; matched={matched_rows:,}; unmatched={unmatched_rows:,}".format(
            output=args.output,
            **summary,
        )
    )


if __name__ == "__main__":
    main()
