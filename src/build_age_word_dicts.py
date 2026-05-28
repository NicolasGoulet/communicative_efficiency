#!/usr/bin/env python3
"""
Build additive age-binned unigram, bigram, and trigram dictionaries.

This script reads the current Stage-0 prepared files:

  data/preprocessed_data/<DATASET>/<CHILD>/chi.csv
  data/preprocessed_data/<DATASET>/<CHILD>/caretakers.csv

Only child utterance tokens are predicted by the n-gram models. The immediately
previous caretaker utterance supplies the left context for the first child word:

  bigram:  p1 c1, c1 c2, c2 c3, ...
  trigram: p2 p1 c1, p1 c1 c2, c1 c2 c3, ...

where p2/p1 are the last two tokens from the most recent prior MOT/FAT
utterance in the same session.

Age bins are additive. A bin such as 030-035 contains counts from that bin plus
all earlier bins in the same scope.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from custom_age_bins import AgeBin, find_age_bin, write_age_bins_config


TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)*")


@dataclass(frozen=True)
class ChildUnit:
    """One prepared child folder containing child and caretaker utterances."""

    dataset: str
    child: str
    folder: Path
    chi_csv: Path
    caretakers_csv: Optional[Path]


@dataclass(frozen=True)
class ChildUtteranceContext:
    """A child utterance with the latest prior caretaker tokens attached."""

    row_index: int
    age_months: float
    child_tokens: Tuple[str, ...]
    previous_caretaker_tokens: Tuple[str, ...]


@dataclass
class BinCounts:
    """Raw counts for one non-additive age bin before cumulative folding."""

    unigram: Counter[str] = field(default_factory=Counter)
    bigram: Counter[Tuple[str, str]] = field(default_factory=Counter)
    trigram: Counter[Tuple[str, str, str]] = field(default_factory=Counter)
    n_utterances: int = 0
    n_child_tokens: int = 0


def tokenize(text: object, lowercase: bool = True) -> List[str]:
    """Tokenize a cleaned utterance into word tokens used by the n-gram models."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return []
    s = str(text)
    if lowercase:
        s = s.lower()
    return TOKEN_RE.findall(s)


def filter_tokens(tokens: Iterable[str], min_token_len: int) -> List[str]:
    """Drop tokens shorter than the requested minimum length."""
    if min_token_len <= 1:
        return [token for token in tokens if token]
    return [token for token in tokens if len(token) >= min_token_len]


def bin_start(age_months: float, bin_months: int, min_age_months: float) -> int:
    """Return the integer start month for an age bin."""
    base = int(math.floor(min_age_months))
    if age_months < min_age_months:
        return base
    offset = int((age_months - min_age_months) // bin_months)
    return base + (offset * bin_months)


def bin_label(start: int, bin_months: int) -> str:
    """Return a readable inclusive age-bin label such as 024-029."""
    end = start + bin_months - 1
    return f"{start:03d}-{end:03d}"


def contextual_bigram_pairs(
    child_tokens: Sequence[str],
    previous_caretaker_tokens: Sequence[str],
) -> List[Tuple[str, str]]:
    """
    Return bigram observations for one child utterance.

    If a prior caretaker utterance exists, the first child word is counted as
    following the last caretaker word. Within-child bigrams are then counted
    normally.
    """
    if not child_tokens:
        return []

    pairs: List[Tuple[str, str]] = []
    if previous_caretaker_tokens:
        pairs.append((previous_caretaker_tokens[-1], child_tokens[0]))

    pairs.extend(zip(child_tokens, child_tokens[1:]))
    return pairs


def contextual_trigram_triples(
    child_tokens: Sequence[str],
    previous_caretaker_tokens: Sequence[str],
) -> List[Tuple[str, str, str]]:
    """
    Return trigram observations for one child utterance.

    The first trigram uses the last two words from the latest prior caretaker
    utterance when available. The second uses the last caretaker word plus the
    first generated/observed child word. Later trigrams are within-child.
    """
    if not child_tokens:
        return []

    triples: List[Tuple[str, str, str]] = []
    if len(previous_caretaker_tokens) >= 2:
        triples.append((previous_caretaker_tokens[-2], previous_caretaker_tokens[-1], child_tokens[0]))

    if len(previous_caretaker_tokens) >= 1 and len(child_tokens) >= 2:
        triples.append((previous_caretaker_tokens[-1], child_tokens[0], child_tokens[1]))

    for i in range(2, len(child_tokens)):
        triples.append((child_tokens[i - 2], child_tokens[i - 1], child_tokens[i]))

    return triples


def iter_child_units(data_dir: Path, datasets: Sequence[str]) -> List[ChildUnit]:
    """Discover prepared child folders for the requested datasets."""
    dataset_set = set(datasets)
    units: List[ChildUnit] = []

    for chi_csv in data_dir.rglob("chi.csv"):
        try:
            rel = chi_csv.relative_to(data_dir)
        except ValueError:
            continue
        if len(rel.parts) < 3:
            continue

        dataset = rel.parts[0]
        if dataset not in dataset_set:
            continue

        folder = chi_csv.parent
        caretakers_csv = folder / "caretakers.csv"
        if not caretakers_csv.exists():
            caretakers_csv = None

        units.append(
            ChildUnit(
                dataset=dataset,
                child=folder.name,
                folder=folder,
                chi_csv=chi_csv,
                caretakers_csv=caretakers_csv,
            )
        )

    units.sort(key=lambda unit: (unit.dataset, unit.child, str(unit.folder)))
    return units


def _ensure_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = pd.NA
    return out


def _prepared_role_frame(path: Optional[Path], role: str, text_col: str) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    required = ["session_id", "file", "line_no", "utt_id", "speaker", "age_months", text_col]
    df = _ensure_columns(df, required)
    df["_source_index"] = df.index
    df["_role_group"] = role
    df["_line_no_num"] = pd.to_numeric(df["line_no"], errors="coerce")
    df["_utt_id_num"] = pd.to_numeric(df["utt_id"], errors="coerce")
    df["_session_sort"] = df["session_id"].astype(str)
    df["_file_sort"] = df["file"].astype(str)
    return df


def load_child_utterance_contexts(
    unit: ChildUnit,
    *,
    text_col: str = "utterance_clean",
    lowercase: bool = True,
    min_token_len: int = 1,
) -> List[ChildUtteranceContext]:
    """
    Load child utterances and attach most recent prior caretaker tokens.

    Context is reset at session boundaries and never crosses into later
    caretaker utterances. Only MOT/FAT rows from caretakers.csv are used as
    caretaker context.
    """
    chi = _prepared_role_frame(unit.chi_csv, "CHI", text_col)
    if chi.empty:
        return []

    caretakers = _prepared_role_frame(unit.caretakers_csv, "CARETAKER", text_col)
    combined = pd.concat([chi, caretakers], ignore_index=True, sort=False)
    combined = combined.sort_values(
        by=["_session_sort", "_file_sort", "_line_no_num", "_utt_id_num", "_role_group"],
        kind="stable",
    )

    contexts: List[ChildUtteranceContext] = []
    last_caretaker_by_session: Dict[str, Tuple[str, ...]] = {}

    for _idx, row in combined.iterrows():
        session_key = str(row["_session_sort"])
        tokens = tuple(filter_tokens(tokenize(row[text_col], lowercase=lowercase), min_token_len))

        if row["_role_group"] == "CARETAKER":
            if tokens:
                last_caretaker_by_session[session_key] = tokens
            continue

        if not tokens:
            continue

        age = pd.to_numeric(row["age_months"], errors="coerce")
        if pd.isna(age):
            continue

        contexts.append(
            ChildUtteranceContext(
                row_index=int(row["_source_index"]),
                age_months=float(age),
                child_tokens=tokens,
                previous_caretaker_tokens=last_caretaker_by_session.get(session_key, tuple()),
            )
        )

    contexts.sort(key=lambda ctx: ctx.row_index)
    return contexts


def _add_contextual_counts(accumulator: BinCounts, context: ChildUtteranceContext) -> None:
    accumulator.unigram.update(context.child_tokens)
    accumulator.bigram.update(
        contextual_bigram_pairs(context.child_tokens, context.previous_caretaker_tokens)
    )
    accumulator.trigram.update(
        contextual_trigram_triples(context.child_tokens, context.previous_caretaker_tokens)
    )
    accumulator.n_utterances += 1
    accumulator.n_child_tokens += len(context.child_tokens)


def _nested_bigram_counts(counter: Counter[Tuple[str, str]]) -> Dict[str, Dict[str, int]]:
    nested: DefaultDict[str, Dict[str, int]] = defaultdict(dict)
    for (w1, w2), count in sorted(counter.items()):
        nested[w1][w2] = int(count)
    return dict(nested)


def _nested_trigram_counts(counter: Counter[Tuple[str, str, str]]) -> Dict[str, Dict[str, Dict[str, int]]]:
    nested: DefaultDict[str, DefaultDict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    for (w1, w2, w3), count in sorted(counter.items()):
        nested[w1][w2][w3] = int(count)
    return {w1: dict(second) for w1, second in nested.items()}


def _unigram_probs(counter: Counter[str]) -> Dict[str, float]:
    total = sum(counter.values())
    if total <= 0:
        return {}
    return {word: count / total for word, count in sorted(counter.items())}


def _conditional_bigram_probs(counter: Counter[Tuple[str, str]]) -> Dict[str, Dict[str, float]]:
    totals: Counter[str] = Counter()
    for (w1, _w2), count in counter.items():
        totals[w1] += count

    nested: DefaultDict[str, Dict[str, float]] = defaultdict(dict)
    for (w1, w2), count in sorted(counter.items()):
        nested[w1][w2] = count / totals[w1]
    return dict(nested)


def _conditional_trigram_probs(
    counter: Counter[Tuple[str, str, str]]
) -> Dict[str, Dict[str, Dict[str, float]]]:
    totals: Counter[Tuple[str, str]] = Counter()
    for (w1, w2, _w3), count in counter.items():
        totals[(w1, w2)] += count

    nested: DefaultDict[str, DefaultDict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for (w1, w2, w3), count in sorted(counter.items()):
        nested[w1][w2][w3] = count / totals[(w1, w2)]
    return {w1: dict(second) for w1, second in nested.items()}


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2, sort_keys=True)


def _write_bin_outputs(
    bin_dir: Path,
    unigram: Counter[str],
    bigram: Counter[Tuple[str, str]],
    trigram: Counter[Tuple[str, str, str]],
) -> None:
    unigram_counts = {word: int(count) for word, count in sorted(unigram.items())}
    unigram_probs = _unigram_probs(unigram)

    _write_json(bin_dir / "unigram_counts.json", unigram_counts)
    _write_json(bin_dir / "unigram_probs.json", unigram_probs)
    _write_json(bin_dir / "counts.json", unigram_counts)
    _write_json(bin_dir / "probs.json", unigram_probs)

    _write_json(bin_dir / "bigram_counts.json", _nested_bigram_counts(bigram))
    _write_json(bin_dir / "bigram_probs.json", _conditional_bigram_probs(bigram))
    _write_json(bin_dir / "trigram_counts.json", _nested_trigram_counts(trigram))
    _write_json(bin_dir / "trigram_probs.json", _conditional_trigram_probs(trigram))

    vocab_sorted = sorted(unigram.items(), key=lambda item: (-item[1], item[0]))
    with (bin_dir / "vocab.txt").open("w", encoding="utf-8") as handle:
        for word, _count in vocab_sorted:
            handle.write(f"{word}\n")


def build_dicts(
    units: Sequence[ChildUnit],
    out_dir: Path,
    bin_months: int = 6,
    min_age_months: float = 0.0,
    max_age_months: float = 120.0,
    by_child: bool = False,
    lowercase: bool = True,
    min_token_len: int = 1,
    text_col: str = "utterance_clean",
    age_bins: Optional[Sequence[AgeBin]] = None,
    age_bin_strategy: str = "fixed_width",
    age_bin_threshold: Optional[int] = None,
) -> None:
    """
    Build additive n-gram dictionaries for all requested units.

    When by_child is false, all datasets/children share one cumulative age-bin
    dictionary. When by_child is true, additive folding happens separately
    inside each child.
    """
    if bin_months <= 0:
        raise ValueError("bin_months must be positive")

    out_dir.mkdir(parents=True, exist_ok=True)

    custom_bins = sorted(age_bins or [], key=lambda age_bin: age_bin.start)
    custom_bins_by_label = {age_bin.label: age_bin for age_bin in custom_bins}
    custom_bin_labels = [age_bin.label for age_bin in custom_bins]
    if custom_bins:
        write_age_bins_config(
            out_dir / "age_bins.json",
            bins=custom_bins,
            strategy=age_bin_strategy,
            threshold=age_bin_threshold,
        )

    base_counts: DefaultDict[Tuple[str, str], DefaultDict[object, BinCounts]] = defaultdict(
        lambda: defaultdict(BinCounts)
    )
    skipped_units = 0

    for unit in units:
        try:
            contexts = load_child_utterance_contexts(
                unit,
                text_col=text_col,
                lowercase=lowercase,
                min_token_len=min_token_len,
            )
        except Exception as exc:
            print(f"[WARN] Skipping {unit.folder}: {exc}")
            skipped_units += 1
            continue

        scope = (unit.dataset, unit.child) if by_child else ("ALL", "ALL")
        for context in contexts:
            if context.age_months < min_age_months or context.age_months > max_age_months:
                continue
            if custom_bins:
                age_bin = find_age_bin(context.age_months, custom_bins)
                if age_bin is None:
                    continue
                bin_key: object = age_bin.label
            else:
                bin_key = bin_start(context.age_months, bin_months, min_age_months)
            _add_contextual_counts(base_counts[scope][bin_key], context)

    summary_rows: List[Dict[str, object]] = []

    for scope, bins in sorted(base_counts.items()):
        dataset, child = scope
        cumulative_unigram: Counter[str] = Counter()
        cumulative_bigram: Counter[Tuple[str, str]] = Counter()
        cumulative_trigram: Counter[Tuple[str, str, str]] = Counter()
        cumulative_utterances = 0
        cumulative_child_tokens = 0

        if custom_bins:
            ordered_keys: List[object] = [label for label in custom_bin_labels if label in bins]
        else:
            ordered_keys = sorted(bins)

        for bin_key in ordered_keys:
            raw_bin = bins[bin_key]
            cumulative_unigram.update(raw_bin.unigram)
            cumulative_bigram.update(raw_bin.bigram)
            cumulative_trigram.update(raw_bin.trigram)
            cumulative_utterances += raw_bin.n_utterances
            cumulative_child_tokens += raw_bin.n_child_tokens

            if custom_bins:
                label = str(bin_key)
                age_bin = custom_bins_by_label[label]
                start = age_bin.start
                end = age_bin.end
                effective_bin_months = age_bin.width
            else:
                start = int(bin_key)
                label = bin_label(start, bin_months)
                end = start + bin_months - 1
                effective_bin_months = bin_months

            if by_child:
                bin_dir = out_dir / dataset / child / f"bin_{label}"
            else:
                bin_dir = out_dir / f"bin_{label}"

            _write_bin_outputs(bin_dir, cumulative_unigram, cumulative_bigram, cumulative_trigram)

            summary_rows.append(
                {
                    "scope": "by_child" if by_child else "global",
                    "dataset": dataset,
                    "child": child,
                    "bin_label": label,
                    "bin_start_month": start,
                    "bin_end_month": end,
                    "bin_months": effective_bin_months,
                    "binning_strategy": age_bin_strategy if custom_bins else "fixed_width",
                    "additive_bins": True,
                    "n_utterances_in_bin": raw_bin.n_utterances,
                    "n_utterances_cumulative": cumulative_utterances,
                    "n_child_tokens_in_bin": raw_bin.n_child_tokens,
                    "n_child_tokens_cumulative": cumulative_child_tokens,
                    "unigram_types": len(cumulative_unigram),
                    "bigram_contexts": len({w1 for (w1, _w2) in cumulative_bigram}),
                    "bigram_types": len(cumulative_bigram),
                    "trigram_contexts": len({(w1, w2) for (w1, w2, _w3) in cumulative_trigram}),
                    "trigram_types": len(cumulative_trigram),
                    "text_col_used": text_col,
                    "output_dir": str(bin_dir),
                }
            )

    pd.DataFrame(summary_rows).to_csv(out_dir / "summary.csv", index=False)
    print(f"[OK] Wrote additive n-gram dictionaries to: {out_dir}")
    if skipped_units:
        print(f"[WARN] Skipped {skipped_units} prepared child folders.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data/preprocessed_data",
        help="Prepared data directory containing <DATASET>/<CHILD>/chi.csv.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["Brown", "Manchester", "Providence"],
        help="Dataset folders to include.",
    )
    parser.add_argument("--bin_months", type=int, default=6, help="Age-bin size in months.")
    parser.add_argument("--out_dir", type=str, required=True, help="Output dictionary root.")
    parser.add_argument("--min_age_months", type=float, default=0.0)
    parser.add_argument("--max_age_months", type=float, default=120.0)
    parser.add_argument("--by_child", action="store_true")
    parser.add_argument("--no_lowercase", action="store_true")
    parser.add_argument("--min_token_len", type=int, default=1)
    parser.add_argument("--text_col", type=str, default="utterance_clean")

    args = parser.parse_args()

    units = iter_child_units(Path(args.data_dir), args.datasets)
    if not units:
        raise SystemExit(f"No chi.csv files found under {args.data_dir} for datasets={args.datasets}.")

    build_dicts(
        units=units,
        out_dir=Path(args.out_dir),
        bin_months=args.bin_months,
        min_age_months=args.min_age_months,
        max_age_months=args.max_age_months,
        by_child=args.by_child,
        lowercase=not args.no_lowercase,
        min_token_len=args.min_token_len,
        text_col=args.text_col,
    )


if __name__ == "__main__":
    main()
