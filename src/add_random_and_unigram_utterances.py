#!/usr/bin/env python3
"""
Generate random, unigram, bigram, and trigram baseline utterances.

The script consumes the additive dictionaries produced by
build_age_word_dicts.py and writes same-length generated utterance columns for
each row in prepared chi.csv files.

Bigram/trigram generation uses the same caretaker-to-child boundary logic as
dictionary building:

  bigram first word:  P(c1 | p1)
  trigram first word: P(c1 | p2, p1)
  trigram second word: P(c2 | p1, c1)

where p2/p1 are the last two tokens from the most recent prior caretaker
utterance in the same session. Missing n-gram contexts back off to lower-order
models.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from build_age_word_dicts import (
    ChildUnit,
    bin_label,
    bin_start,
    iter_child_units,
    load_child_utterance_contexts,
)
from custom_age_bins import AgeBin, find_age_bin, load_age_bins_config


PUNCT_ONLY_RE = re.compile(r"^\W+$", re.UNICODE)
TERMINAL_PUNCT_RE = re.compile(r"([.!?])\s*$")
CONTEXT_P2_COL = "caretaker_context_p2"
CONTEXT_P1_COL = "caretaker_context_p1"
CONTEXT_LAST_TWO_COL = "caretaker_context_last_two"
METADATA_FALLBACK_COLUMNS = ("dataset", "child_id", "source_group", "speaker")
BASE_OUTPUT_COLUMNS = [
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
    "speaker",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
]
CONTEXT_OUTPUT_COLUMNS = [CONTEXT_P2_COL, CONTEXT_P1_COL, CONTEXT_LAST_TWO_COL]

_ALLOWED_AT_TAGS_DEFAULT = {
    "b",
    "c",
    "d",
    "f",
    "i",
    "k",
    "l",
    "ls",
    "n",
    "o",
    "p",
    "wp",
}
_AT_SPLIT_RE = re.compile(r"^(?P<stem>.+?)@(?P<tag>[A-Za-z][A-Za-z0-9:._-]*)(?:\$[A-Za-z]+)?$")


def normalize_vocab_token(
    tok: object,
    allowed_at_tags: set[str],
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
) -> Optional[str]:
    """Normalize a dictionary token or return None when it should be dropped."""
    if tok is None or (isinstance(tok, float) and math.isnan(tok)):
        return None
    token = str(tok).strip()
    if not token:
        return None

    if drop_angle_artifacts and ("<" in token or ">" in token):
        return None

    if drop_chat_markers:
        lowered = token.lower()
        if token == "0" or token.startswith("0"):
            return None
        if token.startswith("&"):
            return None
        if lowered in {"xxx", "yyy", "www"}:
            return None

    match = _AT_SPLIT_RE.match(token)
    if match:
        stem = match.group("stem").strip()
        tag = match.group("tag").split(":", 1)[0]
        if tag not in allowed_at_tags:
            return None
        token = stem

    return token or None


def normalize_vocab_list(
    toks: Sequence[object],
    allowed_at_tags: set[str],
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
) -> List[str]:
    """Normalize and deduplicate vocabulary items while preserving order."""
    out: List[str] = []
    seen = set()
    for token in toks:
        normalized = normalize_vocab_token(
            token,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def normalize_counts(
    counts: Dict[str, int],
    allowed_at_tags: set[str],
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
) -> Dict[str, int]:
    """Normalize count keys and aggregate entries with the same stem."""
    out: Dict[str, int] = {}
    for raw_key, raw_count in counts.items():
        normalized = normalize_vocab_token(
            raw_key,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )
        if normalized is None:
            continue
        count = int(raw_count)
        if count <= 0:
            continue
        out[normalized] = out.get(normalized, 0) + count
    return out


def counts_from_vocab_uniform(vocab: Sequence[str]) -> Dict[str, int]:
    """Build a one-count fallback distribution from a vocabulary."""
    return {word: 1 for word in vocab if word}


def terminal_punctuation(text: object) -> str:
    """Return final sentence punctuation, if present."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    match = TERMINAL_PUNCT_RE.search(str(text).strip())
    return match.group(1) if match else ""


def with_terminal_punctuation(words: Sequence[str], punctuation: str) -> str:
    """Join generated words and optionally attach terminal punctuation."""
    if not words:
        return ""
    out = list(words)
    if punctuation:
        out[-1] = f"{out[-1]}{punctuation}"
    return " ".join(out)


def caretaker_context_debug_values(previous_caretaker_tokens: Sequence[str]) -> Dict[str, str]:
    """Return the p2/p1 caretaker boundary words used by bigram/trigram generation."""
    p2 = previous_caretaker_tokens[-2] if len(previous_caretaker_tokens) >= 2 else ""
    p1 = previous_caretaker_tokens[-1] if len(previous_caretaker_tokens) >= 1 else ""
    return {
        CONTEXT_P2_COL: p2,
        CONTEXT_P1_COL: p1,
        CONTEXT_LAST_TWO_COL: " ".join(token for token in (p2, p1) if token),
    }


def normalize_generated_metadata(df: pd.DataFrame, unit: ChildUnit) -> pd.DataFrame:
    """
    Fill metadata columns that make generated sibling CSVs auditable.

    Some existing prepared files have an empty `source_group` column for corpora
    without subgroups. The generated outputs should still show a meaningful
    provenance value, so those blanks are filled with the dataset name.
    """
    out = df.copy()
    for column in list(out.columns):
        column_name = str(column).strip()
        if not column_name or column_name.startswith("Unnamed:"):
            out = out.drop(columns=[column])

    fallback_values = {
        "dataset": unit.dataset,
        "child_id": unit.child,
        "source_group": unit.dataset,
        "speaker": "CHI",
    }
    for column in METADATA_FALLBACK_COLUMNS:
        if column not in out.columns:
            out[column] = fallback_values[column]
        else:
            values = out[column].astype("string").fillna("").str.strip()
            out[column] = values.mask(values.eq(""), fallback_values[column])
    return out


def generated_model_columns(model_specs: Sequence[Tuple[int, Path]], which: str) -> List[str]:
    """Return generated utterance columns in stable output order."""
    columns: List[str] = []
    for bin_months, _root in model_specs:
        if which in {"random", "all"}:
            columns.append(f"random_model_utterance_bin{bin_months}")
        if which in {"unigram", "all"}:
            columns.append(f"unigram_model_utterance_bin{bin_months}")
        if which in {"bigram", "all"}:
            columns.append(f"bigram_model_utterance_bin{bin_months}")
        if which in {"trigram", "all"}:
            columns.append(f"trigram_model_utterance_bin{bin_months}")
    return columns


def enforce_generated_output_schema(
    df: pd.DataFrame,
    model_specs: Sequence[Tuple[int, Path]],
    which: str,
) -> pd.DataFrame:
    """Return generated output with no blank headers and no `utt_id_role` column."""
    out = df.copy()
    for column in BASE_OUTPUT_COLUMNS + CONTEXT_OUTPUT_COLUMNS + generated_model_columns(model_specs, which):
        if column not in out.columns:
            out[column] = ""
    output_columns = BASE_OUTPUT_COLUMNS + CONTEXT_OUTPUT_COLUMNS + generated_model_columns(model_specs, which)
    return out.loc[:, output_columns]


class UniformSampler:
    """Uniform sampler over a vocabulary."""

    def __init__(self, vocab: Sequence[str]):
        self.vocab = [word for word in vocab if word]
        self.size = len(self.vocab)

    def sample_n(self, rng: random.Random, n: int) -> List[str]:
        if n <= 0 or self.size == 0:
            return []
        return [self.vocab[rng.randrange(self.size)] for _ in range(n)]


class WeightedSampler:
    """Weighted sampler backed by integer counts."""

    def __init__(self, counts: Dict[str, int]):
        items = [(str(word), int(count)) for word, count in counts.items() if word and int(count) > 0]
        items.sort(key=lambda item: item[0])
        self.words = [word for word, _count in items]
        self.cumulative: List[int] = []
        total = 0
        for _word, count in items:
            total += count
            self.cumulative.append(total)
        self.total = total

    def sample_one(self, rng: random.Random) -> str:
        if self.total <= 0:
            return ""
        draw = rng.randrange(1, self.total + 1)
        index = bisect.bisect_left(self.cumulative, draw)
        return self.words[index]

    def sample_n(self, rng: random.Random, n: int) -> List[str]:
        if n <= 0 or self.total <= 0:
            return []
        return [self.sample_one(rng) for _ in range(n)]


class ConditionalSampler:
    """Sampler for one conditional next-word distribution."""

    def __init__(self, probs: Dict[str, float]):
        items = [(str(word), float(prob)) for word, prob in probs.items() if float(prob) > 0]
        items.sort(key=lambda item: item[0])
        self.words = [word for word, _prob in items]
        self.cumulative: List[float] = []
        total = 0.0
        for _word, prob in items:
            total += prob
            self.cumulative.append(total)
        if total > 0:
            self.cumulative = [value / total for value in self.cumulative]

    def sample_one(self, rng: random.Random) -> str:
        if not self.words:
            return ""
        draw = rng.random()
        index = bisect.bisect_left(self.cumulative, draw)
        if index >= len(self.words):
            index = len(self.words) - 1
        return self.words[index]


class BigramSampler:
    """
    Bigram generator with unigram backoff.

    The first generated word can condition on the final token of the most
    recent prior caretaker utterance.
    """

    def __init__(self, bigram_probs: Dict[str, Dict[str, float]], unigram_backoff: WeightedSampler):
        self.backoff = unigram_backoff
        self.contexts = {
            str(previous): ConditionalSampler(next_words)
            for previous, next_words in bigram_probs.items()
            if isinstance(next_words, dict) and next_words
        }

    def sample_next(self, rng: random.Random, previous_word: Optional[str]) -> str:
        if previous_word is not None:
            sampler = self.contexts.get(previous_word)
            if sampler is not None:
                sampled = sampler.sample_one(rng)
                if sampled:
                    return sampled
        return self.backoff.sample_one(rng)

    def sample_sequence(
        self,
        rng: random.Random,
        n: int,
        previous_caretaker_tokens: Sequence[str] = (),
    ) -> List[str]:
        if n <= 0:
            return []
        previous_word = previous_caretaker_tokens[-1] if previous_caretaker_tokens else None
        out: List[str] = []
        for _ in range(n):
            word = self.sample_next(rng, previous_word)
            if not word:
                break
            out.append(word)
            previous_word = word
        return out


class TrigramSampler:
    """
    Trigram generator with bigram and unigram backoff.

    The first generated word can condition on p2,p1 from the latest prior
    caretaker utterance; after generation starts, generated words become the
    running context.
    """

    def __init__(
        self,
        trigram_probs: Dict[str, Dict[str, Dict[str, float]]],
        bigram_backoff: BigramSampler,
        unigram_backoff: WeightedSampler,
    ):
        self.bigram_backoff = bigram_backoff
        self.unigram_backoff = unigram_backoff
        self.contexts: Dict[Tuple[str, str], ConditionalSampler] = {}
        for first, second_level in trigram_probs.items():
            if not isinstance(second_level, dict):
                continue
            for second, next_words in second_level.items():
                if isinstance(next_words, dict) and next_words:
                    self.contexts[(str(first), str(second))] = ConditionalSampler(next_words)

    def sample_next(
        self,
        rng: random.Random,
        previous_two_words: Sequence[str],
    ) -> str:
        if len(previous_two_words) >= 2:
            key = (previous_two_words[-2], previous_two_words[-1])
            sampler = self.contexts.get(key)
            if sampler is not None:
                sampled = sampler.sample_one(rng)
                if sampled:
                    return sampled

        if previous_two_words:
            return self.bigram_backoff.sample_next(rng, previous_two_words[-1])

        return self.unigram_backoff.sample_one(rng)

    def sample_sequence(
        self,
        rng: random.Random,
        n: int,
        previous_caretaker_tokens: Sequence[str] = (),
    ) -> List[str]:
        if n <= 0:
            return []
        history = list(previous_caretaker_tokens[-2:])
        out: List[str] = []
        for _ in range(n):
            word = self.sample_next(rng, history)
            if not word:
                break
            out.append(word)
            history.append(word)
            history = history[-2:]
        return out


def _load_json(path: Path) -> object:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_vocab(
    dict_root: Path,
    blabel: str,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> List[str]:
    path = dict_root / f"bin_{blabel}" / "vocab.txt"
    if not path.exists():
        return []
    raw = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return normalize_vocab_list(
        raw,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=drop_chat_markers,
        drop_angle_artifacts=drop_angle_artifacts,
    )


def load_unigram_counts(
    dict_root: Path,
    blabel: str,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> Dict[str, int]:
    bin_dir = dict_root / f"bin_{blabel}"
    path = bin_dir / "unigram_counts.json"
    if not path.exists():
        path = bin_dir / "counts.json"
    obj = _load_json(path)
    if not isinstance(obj, dict):
        return {}
    raw = {str(key): int(value) for key, value in obj.items()}
    return normalize_counts(
        raw,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=drop_chat_markers,
        drop_angle_artifacts=drop_angle_artifacts,
    )


def load_bigram_probs(dict_root: Path, blabel: str) -> Dict[str, Dict[str, float]]:
    obj = _load_json(dict_root / f"bin_{blabel}" / "bigram_probs.json")
    if not isinstance(obj, dict):
        return {}
    out: Dict[str, Dict[str, float]] = {}
    for previous, next_words in obj.items():
        if isinstance(next_words, dict):
            out[str(previous)] = {str(word): float(prob) for word, prob in next_words.items()}
    return out


def load_trigram_probs(dict_root: Path, blabel: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    obj = _load_json(dict_root / f"bin_{blabel}" / "trigram_probs.json")
    if not isinstance(obj, dict):
        return {}
    out: Dict[str, Dict[str, Dict[str, float]]] = {}
    for first, second_level in obj.items():
        if not isinstance(second_level, dict):
            continue
        out[str(first)] = {}
        for second, next_words in second_level.items():
            if isinstance(next_words, dict):
                out[str(first)][str(second)] = {
                    str(word): float(prob) for word, prob in next_words.items()
                }
    return out


def build_global_fallback_vocab(
    dict_root: Path,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> List[str]:
    vocab: List[str] = []
    for path in sorted(dict_root.glob("bin_*/vocab.txt")):
        vocab.extend([line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
    return normalize_vocab_list(
        vocab,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=drop_chat_markers,
        drop_angle_artifacts=drop_angle_artifacts,
    )


def build_global_fallback_unigram_counts(
    dict_root: Path,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for path in sorted(dict_root.glob("bin_*/unigram_counts.json")):
        obj = _load_json(path)
        if not isinstance(obj, dict):
            continue
        normalized = normalize_counts(
            {str(key): int(value) for key, value in obj.items()},
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )
        for word, count in normalized.items():
            counts[word] = counts.get(word, 0) + count
    return counts


def parse_model_specs(args_models: Sequence[str]) -> List[Tuple[int, Path]]:
    """Parse --models entries like 6:results/age_ngram_dicts/bin6."""
    out: List[Tuple[int, Path]] = []
    for item in args_models:
        if ":" not in item:
            raise ValueError(f"Bad --models entry, expected BIN:PATH: {item}")
        left, right = item.split(":", 1)
        bin_months = int(left)
        if bin_months <= 0:
            raise ValueError(f"Bin months must be positive: {item}")
        root = Path(right)
        if not root.exists():
            raise ValueError(f"Dictionary root does not exist: {root}")
        out.append((bin_months, root))
    return sorted(out, key=lambda spec: spec[0])


def process(
    units: Sequence[ChildUnit],
    model_specs: Sequence[Tuple[int, Path]],
    which: str = "all",
    out_mode: str = "sibling",
    seed: int = 123,
    min_age_months: float = 0.0,
    max_age_months: float = 120.0,
    preserve_terminal_punct: bool = True,
    allowed_at_tags: Optional[set[str]] = None,
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
    text_col: str = "utterance_clean",
    lowercase: bool = True,
    min_token_len: int = 1,
) -> None:
    """Add generated utterance columns to each prepared child file."""
    allowed = allowed_at_tags or set(_ALLOWED_AT_TAGS_DEFAULT)
    rng = random.Random(seed)

    uniform_cache: Dict[Tuple[int, str, str], UniformSampler] = {}
    unigram_cache: Dict[Tuple[int, str, str], WeightedSampler] = {}
    bigram_cache: Dict[Tuple[int, str, str], BigramSampler] = {}
    trigram_cache: Dict[Tuple[int, str, str], TrigramSampler] = {}

    fallback_uniform: Dict[Tuple[int, str], UniformSampler] = {}
    fallback_unigram: Dict[Tuple[int, str], WeightedSampler] = {}
    custom_bins_cache: Dict[str, List[AgeBin]] = {}

    def label_for_age(bin_months: int, root: Path, age_months: float) -> Optional[str]:
        custom_bins = custom_bins_cache.setdefault(str(root), load_age_bins_config(root / "age_bins.json"))
        if custom_bins:
            age_bin = find_age_bin(age_months, custom_bins)
            return age_bin.label if age_bin is not None else None
        return bin_label(bin_start(age_months, bin_months, min_age_months), bin_months)

    def get_uniform(bin_months: int, root: Path, label: str) -> UniformSampler:
        key = (bin_months, str(root), label)
        if key in uniform_cache:
            return uniform_cache[key]

        vocab = load_vocab(root, label, allowed, drop_chat_markers, drop_angle_artifacts)
        if not vocab:
            fallback_key = (bin_months, str(root))
            if fallback_key not in fallback_uniform:
                fallback_uniform[fallback_key] = UniformSampler(
                    build_global_fallback_vocab(root, allowed, drop_chat_markers, drop_angle_artifacts)
                )
            return fallback_uniform[fallback_key]

        sampler = UniformSampler(vocab)
        uniform_cache[key] = sampler
        return sampler

    def get_unigram(bin_months: int, root: Path, label: str) -> WeightedSampler:
        key = (bin_months, str(root), label)
        if key in unigram_cache:
            return unigram_cache[key]

        counts = load_unigram_counts(root, label, allowed, drop_chat_markers, drop_angle_artifacts)
        if not counts:
            fallback_key = (bin_months, str(root))
            if fallback_key not in fallback_unigram:
                fallback_counts = build_global_fallback_unigram_counts(
                    root, allowed, drop_chat_markers, drop_angle_artifacts
                )
                if not fallback_counts:
                    fallback_counts = counts_from_vocab_uniform(
                        build_global_fallback_vocab(root, allowed, drop_chat_markers, drop_angle_artifacts)
                    )
                fallback_unigram[fallback_key] = WeightedSampler(fallback_counts)
            return fallback_unigram[fallback_key]

        sampler = WeightedSampler(counts)
        unigram_cache[key] = sampler
        return sampler

    def get_bigram(bin_months: int, root: Path, label: str) -> BigramSampler:
        key = (bin_months, str(root), label)
        if key in bigram_cache:
            return bigram_cache[key]

        sampler = BigramSampler(load_bigram_probs(root, label), get_unigram(bin_months, root, label))
        bigram_cache[key] = sampler
        return sampler

    def get_trigram(bin_months: int, root: Path, label: str) -> TrigramSampler:
        key = (bin_months, str(root), label)
        if key in trigram_cache:
            return trigram_cache[key]

        unigram = get_unigram(bin_months, root, label)
        bigram = get_bigram(bin_months, root, label)
        sampler = TrigramSampler(load_trigram_probs(root, label), bigram, unigram)
        trigram_cache[key] = sampler
        return sampler

    total_rows = 0
    generated_rows = 0

    for unit in units:
        df = pd.read_csv(unit.chi_csv, dtype=str, keep_default_na=False, low_memory=False)
        df = normalize_generated_metadata(df, unit)
        contexts = load_child_utterance_contexts(
            unit,
            text_col=text_col,
            lowercase=lowercase,
            min_token_len=min_token_len,
        )

        for column in [CONTEXT_P2_COL, CONTEXT_P1_COL, CONTEXT_LAST_TWO_COL]:
            df[column] = ""

        for column in generated_model_columns(model_specs, which):
            df[column] = ""

        for context in contexts:
            if context.age_months < min_age_months or context.age_months > max_age_months:
                continue

            n_tokens = len(context.child_tokens)
            if n_tokens <= 0:
                continue

            row_text = df.at[context.row_index, text_col] if text_col in df.columns else ""
            punct = terminal_punctuation(row_text) if preserve_terminal_punct else ""
            for column, value in caretaker_context_debug_values(context.previous_caretaker_tokens).items():
                df.at[context.row_index, column] = value

            for bin_months, root in model_specs:
                label = label_for_age(bin_months, root, context.age_months)
                if label is None:
                    continue

                if which in {"random", "all"}:
                    sampled = get_uniform(bin_months, root, label).sample_n(rng, n_tokens)
                    df.at[context.row_index, f"random_model_utterance_bin{bin_months}"] = (
                        with_terminal_punctuation(sampled, punct)
                    )

                if which in {"unigram", "all"}:
                    sampled = get_unigram(bin_months, root, label).sample_n(rng, n_tokens)
                    df.at[context.row_index, f"unigram_model_utterance_bin{bin_months}"] = (
                        with_terminal_punctuation(sampled, punct)
                    )

                if which in {"bigram", "all"}:
                    sampled = get_bigram(bin_months, root, label).sample_sequence(
                        rng, n_tokens, context.previous_caretaker_tokens
                    )
                    df.at[context.row_index, f"bigram_model_utterance_bin{bin_months}"] = (
                        with_terminal_punctuation(sampled, punct)
                    )

                if which in {"trigram", "all"}:
                    sampled = get_trigram(bin_months, root, label).sample_sequence(
                        rng, n_tokens, context.previous_caretaker_tokens
                    )
                    df.at[context.row_index, f"trigram_model_utterance_bin{bin_months}"] = (
                        with_terminal_punctuation(sampled, punct)
                    )

            generated_rows += 1

        if out_mode == "sibling":
            out_path = unit.folder / "chi.ngram_generated.csv"
        elif out_mode == "inplace":
            out_path = unit.chi_csv
        else:
            raise ValueError("out_mode must be 'sibling' or 'inplace'")

        output_df = enforce_generated_output_schema(df, model_specs, which)
        output_df.to_csv(
            out_path,
            index=False,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        total_rows += len(output_df)
        print(f"[OK] {unit.dataset}/{unit.child}: wrote {out_path}")

    print("[SUMMARY]")
    print(f"  Child rows seen: {total_rows}")
    print(f"  Scorable child rows generated: {generated_rows}")
    print(f"  Models: {which}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data/preprocessed_data")
    parser.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"])
    parser.add_argument(
        "--models",
        nargs="+",
        default=["6:results/age_ngram_dicts/bin6"],
        help="BIN:DICT_ROOT entries, for example 6:results/age_ngram_dicts/bin6.",
    )
    parser.add_argument("--which", choices=["random", "unigram", "bigram", "trigram", "all"], default="all")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--min_age_months", type=float, default=0.0)
    parser.add_argument("--max_age_months", type=float, default=120.0)
    parser.add_argument("--out_mode", choices=["sibling", "inplace"], default="sibling")
    parser.add_argument("--no_preserve_terminal_punct", action="store_true")
    parser.add_argument("--allowed_at_tags", nargs="+", default=sorted(_ALLOWED_AT_TAGS_DEFAULT))
    parser.add_argument("--keep_chat_markers", action="store_true")
    parser.add_argument("--keep_angle_artifacts", action="store_true")
    parser.add_argument("--text_col", type=str, default="utterance_clean")
    parser.add_argument("--no_lowercase", action="store_true")
    parser.add_argument("--min_token_len", type=int, default=1)

    args = parser.parse_args()

    units = iter_child_units(Path(args.data_dir), args.datasets)
    if not units:
        raise SystemExit(f"No chi.csv files found under {args.data_dir} for datasets={args.datasets}.")

    process(
        units=units,
        model_specs=parse_model_specs(args.models),
        which=args.which,
        out_mode=args.out_mode,
        seed=args.seed,
        min_age_months=args.min_age_months,
        max_age_months=args.max_age_months,
        preserve_terminal_punct=not args.no_preserve_terminal_punct,
        allowed_at_tags=set(args.allowed_at_tags),
        drop_chat_markers=not args.keep_chat_markers,
        drop_angle_artifacts=not args.keep_angle_artifacts,
        text_col=args.text_col,
        lowercase=not args.no_lowercase,
        min_token_len=args.min_token_len,
    )


if __name__ == "__main__":
    main()
