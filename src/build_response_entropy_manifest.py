#!/usr/bin/env python3
"""Build a context manifest for response-level entropy sampling.

The manifest contains unique preceding contexts from the Route 1 long table.
It does not score anything and it does not call a language model. The expensive
step is handled by ``sample_context_responses.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
DEFAULT_OUTPUT = Path("results/response_level_context_entropy/context_response_sampling_manifest.csv")
SPACES_RE = re.compile(r"\s+")
USECOLS = [
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "age_months",
    "age_bin",
    "role",
    "target_variant",
    "context_k",
    "context_text",
    "target_utterance_clean",
    "nb_words",
]


def split_csv(value: str) -> list[str]:
    """Parse comma-separated CLI values."""

    return [part.strip() for part in value.split(",") if part.strip()]


def normalize_context(text: object) -> str:
    """Collapse whitespace and return a stable context string."""

    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    value = str(text)
    if value.lower() == "nan":
        return ""
    return SPACES_RE.sub(" ", value).strip()


def context_id(text: object) -> str:
    """Return a stable id for one normalized context string."""

    normalized = normalize_context(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


@dataclass
class ContextStats:
    """Accumulated provenance for one unique context."""

    context_id: str
    context_text: str
    context_k_values: set[str] = field(default_factory=set)
    datasets: set[str] = field(default_factory=set)
    child_ids: set[str] = field(default_factory=set)
    age_bins: set[str] = field(default_factory=set)
    target_roles: set[str] = field(default_factory=set)
    target_variants: set[str] = field(default_factory=set)
    n_target_rows: int = 0
    age_months_min: float | None = None
    age_months_max: float | None = None
    example_score_id: str = ""
    example_utterance_id: str = ""
    example_target_utterance_clean: str = ""

    def update(self, row: pd.Series) -> None:
        """Add one target row using this context."""

        self.n_target_rows += 1
        self.context_k_values.add(str(row.get("context_k", "")))
        self.datasets.add(str(row.get("dataset", "")))
        self.child_ids.add(str(row.get("child_id", "")))
        self.age_bins.add(str(row.get("age_bin", "")))
        self.target_roles.add(str(row.get("role", "")))
        self.target_variants.add(str(row.get("target_variant", "")))
        age = pd.to_numeric(row.get("age_months", None), errors="coerce")
        if pd.notna(age):
            value = float(age)
            self.age_months_min = value if self.age_months_min is None else min(self.age_months_min, value)
            self.age_months_max = value if self.age_months_max is None else max(self.age_months_max, value)
        if not self.example_score_id:
            self.example_score_id = str(row.get("score_id", ""))
            self.example_utterance_id = str(row.get("utterance_id", ""))
            self.example_target_utterance_clean = str(row.get("target_utterance_clean", ""))

    def as_dict(self) -> dict[str, object]:
        """Return a CSV-serializable manifest row."""

        context_words = len([tok for tok in self.context_text.split(" ") if tok])
        sorted_age_bins = sorted(x for x in self.age_bins if x)
        return {
            "context_id": self.context_id,
            "context_text": self.context_text,
            "context_word_count": context_words,
            "context_k_values": ";".join(sorted(x for x in self.context_k_values if x)),
            "datasets": ";".join(sorted(x for x in self.datasets if x)),
            "child_ids": ";".join(sorted(x for x in self.child_ids if x)),
            "child_count": len([x for x in self.child_ids if x]),
            "age_bins": ";".join(sorted_age_bins),
            "age_bin_first": sorted_age_bins[0] if sorted_age_bins else "",
            "target_roles": ";".join(sorted(x for x in self.target_roles if x)),
            "target_variants": ";".join(sorted(x for x in self.target_variants if x)),
            "n_target_rows": self.n_target_rows,
            "age_months_min": self.age_months_min,
            "age_months_max": self.age_months_max,
            "example_score_id": self.example_score_id,
            "example_utterance_id": self.example_utterance_id,
            "example_target_utterance_clean": self.example_target_utterance_clean,
        }


def filter_chunk(
    chunk: pd.DataFrame,
    *,
    roles: set[str],
    target_variants: set[str],
    context_ks: set[str],
    min_context_words: int,
) -> pd.DataFrame:
    """Keep only target rows whose preceding context should be sampled."""

    out = chunk[
        chunk["role"].astype(str).isin(roles)
        & chunk["target_variant"].astype(str).isin(target_variants)
        & chunk["context_k"].astype(str).isin(context_ks)
    ].copy()
    out["context_text"] = out["context_text"].map(normalize_context)
    out = out[out["context_text"].astype(str).str.len() > 0].copy()
    if min_context_words > 0:
        out = out[out["context_text"].map(lambda text: len(text.split()) >= min_context_words)].copy()
    return out


def build_manifest(
    *,
    input_csv: Path,
    output_csv: Path,
    roles: Sequence[str],
    target_variants: Sequence[str],
    context_ks: Sequence[str],
    chunksize: int,
    min_context_words: int,
    sample_per_age_bin: int | None,
    max_contexts: int | None,
    seed: int,
) -> pd.DataFrame:
    """Build and write a unique-context response-sampling manifest."""

    stats: dict[str, ContextStats] = {}
    role_set = set(roles)
    variant_set = set(target_variants)
    context_k_set = set(context_ks)

    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        wanted = filter_chunk(
            chunk,
            roles=role_set,
            target_variants=variant_set,
            context_ks=context_k_set,
            min_context_words=min_context_words,
        )
        for _, row in wanted.iterrows():
            text = str(row["context_text"])
            cid = context_id(text)
            if cid not in stats:
                stats[cid] = ContextStats(context_id=cid, context_text=text)
            stats[cid].update(row)

    manifest = pd.DataFrame([item.as_dict() for item in stats.values()])
    if manifest.empty:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(output_csv, index=False)
        return manifest

    manifest = manifest.sort_values(["age_bin_first", "context_word_count", "context_id"]).reset_index(drop=True)
    if sample_per_age_bin is not None:
        rng = random.Random(seed)
        sampled_parts: list[pd.DataFrame] = []
        for _, group in manifest.groupby("age_bin_first", sort=True, dropna=False):
            if len(group) <= sample_per_age_bin:
                sampled_parts.append(group)
            else:
                positions = sorted(rng.sample(range(len(group)), sample_per_age_bin))
                sampled_parts.append(group.iloc[positions])
        manifest = pd.concat(sampled_parts, ignore_index=True).sort_values(["age_bin_first", "context_id"])
    if max_contexts is not None:
        manifest = manifest.head(max_contexts).copy()
    manifest = manifest.reset_index(drop=True)
    manifest.insert(0, "manifest_row", range(len(manifest)))
    manifest["manifest_build_filters_json"] = json.dumps(
        {
            "roles": list(roles),
            "target_variants": list(target_variants),
            "context_ks": list(context_ks),
            "min_context_words": min_context_words,
            "sample_per_age_bin": sample_per_age_bin,
            "max_contexts": max_contexts,
            "seed": seed,
        },
        sort_keys=True,
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(output_csv, index=False)
    return manifest


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--roles", default="child")
    parser.add_argument("--target-variants", default="real")
    parser.add_argument("--context-ks", default="k3")
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--min-context-words", type=int, default=1)
    parser.add_argument("--sample-per-age-bin", type=int, default=None)
    parser.add_argument("--max-contexts", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260605)
    args = parser.parse_args(argv)
    manifest = build_manifest(
        input_csv=args.input,
        output_csv=args.output,
        roles=split_csv(args.roles),
        target_variants=split_csv(args.target_variants),
        context_ks=split_csv(args.context_ks),
        chunksize=args.chunksize,
        min_context_words=args.min_context_words,
        sample_per_age_bin=args.sample_per_age_bin,
        max_contexts=args.max_contexts,
        seed=args.seed,
    )
    print(f"[OK] wrote {len(manifest):,} unique contexts to {args.output}")
    if not manifest.empty:
        print(manifest["age_bin_first"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
