#!/usr/bin/env python3
"""Audit PBM additive LSTM vocabulary pressure before training."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from custom_age_bins import make_merged_early_bins  # noqa: E402
from generate_lstm_utterances import LSTMConfig, SPECIAL_TOKENS  # noqa: E402
from run_lstm_additive_age_context_pipeline import (  # noqa: E402
    cumulative_train_examples,
    target_bin_examples,
)
from run_lstm_baseline_pipeline import (  # noqa: E402
    DEFAULT_MANIFEST,
    build_examples_by_unit,
    discover_units_from_manifest,
)


def parse_int_list(values: Sequence[str]) -> list[int]:
    return [int(value) for value in values]


def token_counter(sequences: Iterable[Sequence[str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for sequence in sequences:
        counter.update(sequence)
    return counter


def coverage(counter: Counter[str], vocabset: set[str]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    covered = sum(count for token, count in counter.items() if token in vocabset)
    return covered / total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"])
    parser.add_argument("--contexts", nargs="+", default=["3", "4", "5"])
    parser.add_argument("--vocab_caps", nargs="+", default=["5000", "10000", "30000"])
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "results"
        / "lstm_baselines"
        / "pbm_additive_lstm_training_generation_2026_06_03"
        / "vocab_audit.csv",
    )
    args = parser.parse_args()

    contexts = parse_int_list(args.contexts)
    vocab_caps = parse_int_list(args.vocab_caps)
    age_bins = make_merged_early_bins(first_start=6, first_end=23, max_month=65)
    units = discover_units_from_manifest(args.manifest, datasets=args.datasets)

    fieldnames = [
        "context_utterances",
        "age_bin",
        "train_examples",
        "target_examples",
        "raw_unique_train_tokens",
        "train_token_occurrences",
        "target_child_token_occurrences",
    ]
    for cap in vocab_caps:
        fieldnames.extend(
            [
                f"target_child_token_coverage_vocab{cap}",
                f"train_token_coverage_vocab{cap}",
                f"lexical_slots_vocab{cap}",
            ]
        )

    rows: list[dict[str, object]] = []
    for context_utterances in contexts:
        config = LSTMConfig(
            context_utterances=context_utterances,
            max_context_tokens=60,
            min_age_months=6.0,
            max_age_months=65.999,
            min_token_len=1,
            lowercase=True,
        )
        examples_by_unit, all_examples = build_examples_by_unit(units, config)
        for age_bin in age_bins:
            train_examples = cumulative_train_examples(
                all_examples,
                first_start=age_bins[0].start,
                age_bin=age_bin,
            )
            target_examples = []
            for examples in examples_by_unit.values():
                target_examples.extend(target_bin_examples(examples, bins=age_bins, age_bin=age_bin))

            train_counter = token_counter(
                example.context_tokens + example.child_tokens for example in train_examples
            )
            target_child_counter = token_counter(example.child_tokens for example in target_examples)
            sorted_tokens = [
                token
                for token, _count in sorted(train_counter.items(), key=lambda item: (-item[1], item[0]))
                if token not in SPECIAL_TOKENS
            ]

            row: dict[str, object] = {
                "context_utterances": context_utterances,
                "age_bin": age_bin.label,
                "train_examples": len(train_examples),
                "target_examples": len(target_examples),
                "raw_unique_train_tokens": len(train_counter),
                "train_token_occurrences": sum(train_counter.values()),
                "target_child_token_occurrences": sum(target_child_counter.values()),
            }
            for cap in vocab_caps:
                lexical_slots = max(0, cap - len(SPECIAL_TOKENS))
                vocabset = set(sorted_tokens[:lexical_slots]) | set(SPECIAL_TOKENS)
                row[f"target_child_token_coverage_vocab{cap}"] = f"{coverage(target_child_counter, vocabset):.6f}"
                row[f"train_token_coverage_vocab{cap}"] = f"{coverage(train_counter, vocabset):.6f}"
                row[f"lexical_slots_vocab{cap}"] = lexical_slots
            rows.append(row)
            print(
                f"[VOCAB] k={context_utterances} bin={age_bin.label} "
                f"unique={len(train_counter)} target_tokens={sum(target_child_counter.values())}",
                flush=True,
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[DONE] wrote {args.output}")


if __name__ == "__main__":
    main()
