#!/usr/bin/env python3
"""Stream PBM child utterances and audit vocabulary by additive age bin."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import filter_tokens, tokenize  # noqa: E402
from custom_age_bins import floor_age_month, make_merged_early_bins  # noqa: E402
from run_lstm_baseline_pipeline import DEFAULT_MANIFEST, discover_units_from_manifest  # noqa: E402


def parse_int_list(values: Sequence[str]) -> list[int]:
    return [int(value) for value in values]


def coverage(counter: Counter[str], vocabset: set[str]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return sum(count for token, count in counter.items() if token in vocabset) / total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"])
    parser.add_argument("--vocab_caps", nargs="+", default=["5000", "10000", "30000"])
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "results"
        / "lstm_baselines"
        / "pbm_additive_lstm_training_generation_2026_06_03"
        / "child_vocab_by_age_bin_audit.csv",
    )
    args = parser.parse_args()

    vocab_caps = parse_int_list(args.vocab_caps)
    bins = make_merged_early_bins(first_start=6, first_end=23, max_month=65)
    units = discover_units_from_manifest(args.manifest, datasets=args.datasets)

    bin_counters = {age_bin.label: Counter() for age_bin in bins}
    bin_rows = {age_bin.label: 0 for age_bin in bins}
    bin_token_rows = {age_bin.label: 0 for age_bin in bins}

    for unit in units:
        with unit.chi_csv.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    age = float(row.get("age_months", ""))
                except ValueError:
                    continue
                month = floor_age_month(age)
                if month is None:
                    continue
                age_bin = next((candidate for candidate in bins if candidate.contains_month(month)), None)
                if age_bin is None:
                    continue
                bin_rows[age_bin.label] += 1
                tokens = filter_tokens(tokenize(row.get("utterance_clean", ""), lowercase=True), min_token_len=1)
                if not tokens:
                    continue
                bin_token_rows[age_bin.label] += 1
                bin_counters[age_bin.label].update(tokens)
        print(f"[READ] {unit.dataset}/{unit.child}", flush=True)

    cumulative_counter: Counter[str] = Counter()
    rows: list[dict[str, object]] = []
    for age_bin in bins:
        label = age_bin.label
        target_counter = bin_counters[label]
        cumulative_counter.update(target_counter)
        sorted_tokens = [
            token
            for token, _count in sorted(cumulative_counter.items(), key=lambda item: (-item[1], item[0]))
        ]
        row: dict[str, object] = {
            "age_bin": label,
            "source_child_rows": bin_rows[label],
            "target_token_rows": bin_token_rows[label],
            "target_token_occurrences": sum(target_counter.values()),
            "target_unique_child_tokens": len(target_counter),
            "cumulative_token_occurrences": sum(cumulative_counter.values()),
            "cumulative_unique_child_tokens": len(cumulative_counter),
        }
        for cap in vocab_caps:
            vocabset = set(sorted_tokens[:cap])
            row[f"target_token_coverage_vocab{cap}"] = f"{coverage(target_counter, vocabset):.6f}"
            row[f"cumulative_token_coverage_vocab{cap}"] = f"{coverage(cumulative_counter, vocabset):.6f}"
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[DONE] wrote {args.output}")


if __name__ == "__main__":
    main()
