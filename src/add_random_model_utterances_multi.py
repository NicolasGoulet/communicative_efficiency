#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
add_random_and_unigram_utts.py
==============================

Add random-model (uniform) and unigram-model (frequency-weighted) utterance columns
to each child_utts.csv, for multiple age binning schemes.

Creates columns like:
  random_model_utterance_bin3
  unigram_model_utterance_bin3
  random_model_utterance_bin6
  unigram_model_utterance_bin6
  random_model_utterance_bin12
  unigram_model_utterance_bin12

Random LM: samples uniformly from vocab.txt
Unigram LM: samples weighted by counts.json

Expected dictionary layout (per bin label):
  <DICT_ROOT>/bin_006-011/vocab.txt
  <DICT_ROOT>/bin_006-011/counts.json

Example DICT_ROOTs:
  results/age_word_dicts/bin3
  results/age_word_dicts/bin6
  results/age_word_dicts/bin12

IMPORTANT (robustness):
Even if some CHAT/CLAN markers accidentally leaked into vocab/counts,
this script filters them out at load-time:

  - drops 0word omissions (tokens starting with '0')
  - drops fillers/nonwords/events starting with '&' (e.g., &-uh, &~mm, &=hiccup)
  - drops xxx/yyy/www
  - drops tokens containing '<' or '>' (parsing artifacts)
  - handles @-markers:
      * if token has @TAG and TAG is NOT in {b,c,o} -> drop
      * if token has @b/@c/@o -> keep the STEM only (strip @TAG)
      * if token has no @ -> keep as-is

Output:
  - sibling mode (default): <child_dir>/child_utts.random_and_unigram.csv
  - inplace mode: overwrites child_utts.csv (backs up once)

Usage:
  python3 src/add_random_and_unigram_utts.py \
    --datasets Brown Manchester Providence \
    --models 3:results/age_word_dicts/bin3 6:results/age_word_dicts/bin6 12:results/age_word_dicts/bin12
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


# -------------------------
# Age parsing
# -------------------------

AGE_CANDIDATE_COLS = [
    "age_months", "age_mo", "age_in_months", "child_age_months",
    "age", "child_age", "target_child_age",
    "age_days", "age_in_days",
    "age_weeks", "age_in_weeks",
    "age_years", "age_in_years",
]
AGE_STRING_RE = re.compile(r"^\s*(\d+)\s*;\s*(\d+)(?:\.(\d+))?\s*$")  # 2;03.12
PUNCT_ONLY_RE = re.compile(r"^\W+$", re.UNICODE)


def parse_age_to_months(x) -> Optional[float]:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)

    s = str(x).strip()
    if not s:
        return None

    m = AGE_STRING_RE.match(s)
    if m:
        years = int(m.group(1))
        months = int(m.group(2))
        days = int(m.group(3)) if m.group(3) is not None else 0
        return years * 12.0 + months + (days / 30.4375)

    try:
        return float(s)
    except ValueError:
        return None


def find_age_column(df: pd.DataFrame) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in AGE_CANDIDATE_COLS:
        if cand in cols_lower:
            return cols_lower[cand]
    for c in df.columns:
        cl = c.lower()
        if "age" in cl and ("month" in cl or "mo" in cl):
            return c
    for c in df.columns:
        if "age" in c.lower():
            return c
    return None


def normalize_age_months(df: pd.DataFrame, age_col: str) -> pd.Series:
    col_lower = age_col.lower()
    s = df[age_col].apply(parse_age_to_months)

    if "day" in col_lower:
        return s.apply(lambda v: None if v is None else float(v) / 30.4375)
    if "week" in col_lower:
        return s.apply(lambda v: None if v is None else float(v) * 7.0 / 30.4375)
    if "year" in col_lower:
        return s.apply(lambda v: None if v is None else float(v) * 12.0)

    return s


# -------------------------
# Binning
# -------------------------

def bin_start(age_months: float, bin_months: int, min_age: float) -> int:
    if age_months < min_age:
        return int(min_age)
    k = int((age_months - min_age) // bin_months)
    return int(min_age + k * bin_months)


def bin_label(start: int, bin_months: int) -> str:
    end = start + bin_months - 1
    return f"{start:03d}-{end:03d}"


def trailing_punct_tokens(utt: str) -> List[str]:
    """Keep trailing punctuation-only tokens from the original tokenization (e.g. '.' at end)."""
    if utt is None:
        return []
    toks = str(utt).strip().split()
    out = []
    i = len(toks) - 1
    while i >= 0 and PUNCT_ONLY_RE.match(toks[i]):
        out.append(toks[i])
        i -= 1
    out.reverse()
    return out


def estimate_word_len_from_utterance(utt: str) -> int:
    """Fallback if word_count missing: count non-punct tokens."""
    toks = str(utt).strip().split()
    toks = [t for t in toks if t and not PUNCT_ONLY_RE.match(t)]
    return len(toks)


# -------------------------
# CHAT-aware token filtering / normalization
# -------------------------

_ALLOWED_AT_TAGS_DEFAULT = {"b", "c", "o"}  # strict set
_AT_SPLIT_RE = re.compile(r"^(?P<stem>.+?)@(?P<tag>[A-Za-z][A-Za-z0-9:._-]*)$")


def normalize_vocab_token(
    tok: str,
    allowed_at_tags: set[str],
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
) -> Optional[str]:
    """
    Returns normalized token or None if token should be dropped.

    Rules:
      - drop tokens with '<' or '>' if drop_angle_artifacts
      - drop CHAT omission tokens: 0word and '0'
      - drop CHAT nonlexical markers: anything starting with '&' (fillers/nonwords/events/fragments)
      - drop xxx/yyy/www
      - if token has @TAG:
          * keep only if TAG in allowed_at_tags
          * return stem only (strip @TAG)
      - else keep token as-is
    """
    if tok is None:
        return None
    t = str(tok).strip()
    if not t:
        return None

    if drop_angle_artifacts and ("<" in t or ">" in t):
        return None

    if drop_chat_markers:
        if t == "0" or t.startswith("0"):
            return None
        if t.startswith("&"):
            return None
        if t.lower() in {"xxx", "yyy", "www"}:
            return None

    # handle @TAG
    m = _AT_SPLIT_RE.match(t)
    if m:
        stem = m.group("stem")
        tag = m.group("tag")

        if tag not in allowed_at_tags:
            return None

        t = stem.strip()
        if not t:
            return None

        if drop_angle_artifacts and ("<" in t or ">" in t):
            return None

        if drop_chat_markers:
            if t == "0" or t.startswith("0") or t.startswith("&"):
                return None
            if t.lower() in {"xxx", "yyy", "www"}:
                return None

    return t


def normalize_vocab_list(
    toks: List[str],
    allowed_at_tags: set[str],
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
) -> List[str]:
    """Normalize + deduplicate while preserving order."""
    out: List[str] = []
    seen = set()
    for w in toks:
        nw = normalize_vocab_token(
            w,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )
        if nw is None:
            continue
        if nw not in seen:
            seen.add(nw)
            out.append(nw)
    return out


def normalize_counts(
    counts: Dict[str, int],
    allowed_at_tags: set[str],
    drop_chat_markers: bool = True,
    drop_angle_artifacts: bool = True,
) -> Dict[str, int]:
    """Normalize keys and AGGREGATE counts when multiple raw keys map to same normalized stem."""
    agg: Dict[str, int] = {}
    for k, v in counts.items():
        nk = normalize_vocab_token(
            k,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )
        if nk is None:
            continue
        iv = int(v)
        if iv <= 0:
            continue
        agg[nk] = agg.get(nk, 0) + iv
    return agg


def counts_from_vocab_uniform(vocab: List[str]) -> Dict[str, int]:
    """Fallback if no counts exist: treat each vocab item as weight 1."""
    return {w: 1 for w in vocab if w}


# -------------------------
# Discovery
# -------------------------

@dataclass
class ChildUnit:
    dataset: str
    child: str
    folder: Path
    child_utts_csv: Path
    session_index_csv: Path


def discover_child_units(data_dir: Path, datasets: List[str]) -> List[ChildUnit]:
    ds = set(datasets)
    units: List[ChildUnit] = []
    for p in data_dir.rglob("child_utts.csv"):
        try:
            rel = p.relative_to(data_dir)
        except ValueError:
            continue
        if len(rel.parts) < 2:
            continue
        dataset = rel.parts[0]
        if dataset not in ds:
            continue
        folder = p.parent
        sess = folder / "session_index.csv"
        if not sess.exists():
            sess = Path("")
        units.append(ChildUnit(dataset=dataset, child=folder.name, folder=folder,
                               child_utts_csv=p, session_index_csv=sess))
    units.sort(key=lambda u: (u.dataset, u.child, str(u.folder)))
    return units


def load_utts_with_age(unit: ChildUnit) -> pd.DataFrame:
    utts = pd.read_csv(unit.child_utts_csv)

    age_col_utts = find_age_column(utts)
    if age_col_utts is not None:
        utts["age_months"] = normalize_age_months(utts, age_col_utts)
        return utts

    if unit.session_index_csv and unit.session_index_csv.exists():
        sess = pd.read_csv(unit.session_index_csv)
        age_col_sess = find_age_column(sess)
        if age_col_sess is None:
            raise RuntimeError(f"No age-like column in session_index.csv for {unit.folder}")
        sess_age = sess[["session_id", age_col_sess]].copy()
        sess_age["age_months"] = normalize_age_months(sess_age, age_col_sess)
        merged = utts.merge(sess_age[["session_id", "age_months"]], on="session_id", how="left")
        return merged

    raise RuntimeError(f"No age in child_utts.csv and missing session_index.csv for {unit.folder}")


# -------------------------
# Samplers (uniform + weighted)
# -------------------------

class UniformSampler:
    def __init__(self, vocab: List[str]):
        self.vocab = [w for w in vocab if w]
        self.m = len(self.vocab)

    def sample_n(self, rng: random.Random, n: int) -> List[str]:
        if n <= 0 or self.m == 0:
            return []
        return [self.vocab[rng.randrange(self.m)] for _ in range(n)]


class WeightedSampler:
    """
    Weighted sampling using cumulative counts + bisect.
    O(log V) per sampled word; avoids float probs.
    """
    def __init__(self, counts: Dict[str, int]):
        items = [(w, int(c)) for w, c in counts.items() if w and int(c) > 0]
        items.sort(key=lambda x: x[0])  # deterministic order

        self.words = [w for w, _ in items]
        cum = []
        total = 0
        for _w, c in items:
            total += c
            cum.append(total)
        self.cum = cum
        self.total = total

    def sample_one(self, rng: random.Random) -> str:
        r = rng.randrange(1, self.total + 1)
        i = bisect.bisect_left(self.cum, r)
        return self.words[i]

    def sample_n(self, rng: random.Random, n: int) -> List[str]:
        if n <= 0 or self.total <= 0:
            return []
        return [self.sample_one(rng) for _ in range(n)]


# -------------------------
# Dict loading
# -------------------------

def load_vocab(
    dict_root: Path,
    blabel: str,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> List[str]:
    p = dict_root / f"bin_{blabel}" / "vocab.txt"
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        raw = [line.strip() for line in f if line.strip()]
    return normalize_vocab_list(
        raw,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=drop_chat_markers,
        drop_angle_artifacts=drop_angle_artifacts,
    )


def load_counts(
    dict_root: Path,
    blabel: str,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> Dict[str, int]:
    p = dict_root / f"bin_{blabel}" / "counts.json"
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    raw = {str(k): int(v) for k, v in obj.items()}
    return normalize_counts(
        raw,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=drop_chat_markers,
        drop_angle_artifacts=drop_angle_artifacts,
    )


def build_global_fallback_vocab(
    dict_root: Path,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> List[str]:
    all_vocab: List[str] = []
    for vp in dict_root.glob("bin_*/vocab.txt"):
        with vp.open("r", encoding="utf-8") as f:
            all_vocab.extend([line.strip() for line in f if line.strip()])
    return normalize_vocab_list(
        all_vocab,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=drop_chat_markers,
        drop_angle_artifacts=drop_angle_artifacts,
    )


def build_global_fallback_counts(
    dict_root: Path,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> Dict[str, int]:
    agg: Dict[str, int] = {}
    for cp in dict_root.glob("bin_*/counts.json"):
        with cp.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        raw = {str(k): int(v) for k, v in obj.items()}
        norm = normalize_counts(
            raw,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )
        for k, v in norm.items():
            agg[k] = agg.get(k, 0) + int(v)
    return agg


# -------------------------
# Main processing
# -------------------------

def process(
    units: List[ChildUnit],
    model_specs: List[Tuple[int, Path]],   # (bin_months, dict_root)
    which: str,                            # "random", "unigram", "both"
    out_mode: str,
    seed: int,
    min_age_months: float,
    max_age_months: float,
    preserve_trailing_punct: bool,
    allowed_at_tags: set[str],
    drop_chat_markers: bool,
    drop_angle_artifacts: bool,
) -> None:
    rng = random.Random(seed)

    # caches keyed by (bin_m, blabel) — root is per-bin in your usage anyway
    uniform_cache: Dict[Tuple[int, str, str], UniformSampler] = {}
    unigram_cache: Dict[Tuple[int, str, str], WeightedSampler] = {}
    fallback_uniform: Dict[Tuple[int, str], UniformSampler] = {}
    fallback_unigram: Dict[Tuple[int, str], WeightedSampler] = {}

    def get_uniform(bin_m: int, root: Path, blabel: str) -> UniformSampler:
        key = (bin_m, str(root), blabel)
        if key in uniform_cache:
            return uniform_cache[key]

        vocab = load_vocab(
            root, blabel,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )

        if not vocab:
            fb_key = (bin_m, str(root))
            if fb_key not in fallback_uniform:
                fb_vocab = build_global_fallback_vocab(
                    root,
                    allowed_at_tags=allowed_at_tags,
                    drop_chat_markers=drop_chat_markers,
                    drop_angle_artifacts=drop_angle_artifacts,
                )
                fallback_uniform[fb_key] = UniformSampler(fb_vocab)
            return fallback_uniform[fb_key]

        sampler = UniformSampler(vocab)
        uniform_cache[key] = sampler
        return sampler

    def get_unigram(bin_m: int, root: Path, blabel: str) -> WeightedSampler:
        key = (bin_m, str(root), blabel)
        if key in unigram_cache:
            return unigram_cache[key]

        counts = load_counts(
            root, blabel,
            allowed_at_tags=allowed_at_tags,
            drop_chat_markers=drop_chat_markers,
            drop_angle_artifacts=drop_angle_artifacts,
        )

        if not counts:
            fb_key = (bin_m, str(root))
            if fb_key not in fallback_unigram:
                fb_counts = build_global_fallback_counts(
                    root,
                    allowed_at_tags=allowed_at_tags,
                    drop_chat_markers=drop_chat_markers,
                    drop_angle_artifacts=drop_angle_artifacts,
                )
                if not fb_counts:
                    fb_vocab = build_global_fallback_vocab(
                        root,
                        allowed_at_tags=allowed_at_tags,
                        drop_chat_markers=drop_chat_markers,
                        drop_angle_artifacts=drop_angle_artifacts,
                    )
                    fb_counts = counts_from_vocab_uniform(fb_vocab)

                fallback_unigram[fb_key] = WeightedSampler(fb_counts)
            return fallback_unigram[fb_key]

        sampler = WeightedSampler(counts)
        unigram_cache[key] = sampler
        return sampler

    total_rows = 0
    missing_age = 0

    for unit in units:
        try:
            df = load_utts_with_age(unit)
        except Exception as e:
            print(f"[WARN] Skipping {unit.folder}: {e}")
            continue

        if "utterance" not in df.columns:
            print(f"[WARN] Skipping {unit.folder}: no 'utterance' column")
            continue

        has_word_count = "word_count" in df.columns

        df["age_months"] = pd.to_numeric(df["age_months"], errors="coerce")
        mask_age = df["age_months"].notna()
        missing_age += int((~mask_age).sum())

        # create cols (blank by default)
        for bin_m, _root in model_specs:
            if which in ("random", "both"):
                df[f"random_model_utterance_bin{bin_m}"] = ""
            if which in ("unigram", "both"):
                df[f"unigram_model_utterance_bin{bin_m}"] = ""

        df_ok = df[mask_age].copy()
        df_ok = df_ok[(df_ok["age_months"] >= min_age_months) & (df_ok["age_months"] <= max_age_months)].copy()

        if not df_ok.empty:
            for row in df_ok.itertuples(index=True):
                idx = row.Index
                age_m = float(row.age_months)
                utt = row.utterance

                L = int(row.word_count) if has_word_count and not (
                    isinstance(row.word_count, float) and math.isnan(row.word_count)
                ) else estimate_word_len_from_utterance(utt)

                puncts = trailing_punct_tokens(utt) if preserve_trailing_punct else []

                for bin_m, root in model_specs:
                    bstart = bin_start(age_m, bin_m, min_age_months)
                    blabel = bin_label(bstart, bin_m)

                    if which in ("random", "both"):
                        uni = get_uniform(bin_m, root, blabel)
                        sampled = uni.sample_n(rng, L)
                        if puncts:
                            sampled = sampled + puncts
                        df.at[idx, f"random_model_utterance_bin{bin_m}"] = " ".join(sampled)

                    if which in ("unigram", "both"):
                        w = get_unigram(bin_m, root, blabel)
                        sampled = w.sample_n(rng, L)
                        if puncts:
                            sampled = sampled + puncts
                        df.at[idx, f"unigram_model_utterance_bin{bin_m}"] = " ".join(sampled)

        # write output
        if out_mode == "sibling":
            out_path = unit.folder / "child_utts.random_and_unigram.csv"
        elif out_mode == "inplace":
            bak = unit.folder / "child_utts.csv.bak_random_and_unigram"
            if not bak.exists():
                unit.child_utts_csv.replace(bak)
            out_path = unit.folder / "child_utts.csv"
        else:
            raise ValueError("--out_mode must be 'sibling' or 'inplace'")

        df.to_csv(out_path, index=False)
        total_rows += len(df)
        print(f"[OK] {unit.dataset}/{unit.child}: wrote {out_path}")

    print("\n[SUMMARY]")
    print(f"  Total rows seen: {total_rows}")
    print(f"  Rows missing age_months (cols left blank): {missing_age}")
    print(f"  allowed_at_tags for @TAG forms: {sorted(allowed_at_tags)}")
    print(f"  drop_chat_markers: {drop_chat_markers} (drops 0*, &*, xxx/yyy/www)")
    print(f"  drop_angle_artifacts: {drop_angle_artifacts} (drops tokens containing < or >)")


def parse_model_specs(args_models: List[str]) -> List[Tuple[int, Path]]:
    """
    Parse --models items like:
      3:results/age_word_dicts/bin3
      6:results/age_word_dicts/bin6
      12:results/age_word_dicts/bin12
    """
    out: List[Tuple[int, Path]] = []
    for item in args_models:
        if ":" not in item:
            raise ValueError(f"Bad --models entry (expected BIN:PATH): {item}")
        left, right = item.split(":", 1)
        bin_m = int(left)
        if bin_m <= 0:
            raise ValueError(f"Bin months must be positive; got {bin_m}")
        p = Path(right)
        if not p.exists():
            raise ValueError(f"Dict root does not exist: {p}")
        out.append((bin_m, p))
    out.sort(key=lambda x: x[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=str, default="data")
    ap.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"])

    ap.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="List of BIN:DICT_ROOT like 3:results/age_word_dicts/bin3 6:... 12:...",
    )

    ap.add_argument("--which", choices=["random", "unigram", "both"], default="both")
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--min_age_months", type=float, default=0.0)
    ap.add_argument("--max_age_months", type=float, default=120.0)

    ap.add_argument("--out_mode", type=str, default="sibling", choices=["sibling", "inplace"])
    ap.add_argument("--no_preserve_trailing_punct", action="store_true")

    ap.add_argument(
        "--allowed_at_tags",
        nargs="+",
        default=sorted(_ALLOWED_AT_TAGS_DEFAULT),
        help="For tokens with @TAG, only keep if TAG is in this set; then strip @TAG. Default: b c o",
    )
    ap.add_argument(
        "--keep_chat_markers",
        action="store_true",
        help="If set, DO NOT drop CHAT markers (0*, &*, xxx/yyy/www). Default is to drop them.",
    )
    ap.add_argument(
        "--keep_angle_artifacts",
        action="store_true",
        help="If set, DO NOT drop tokens containing '<' or '>'. Default is to drop them.",
    )

    args = ap.parse_args()

    units = discover_child_units(Path(args.data_dir), args.datasets)
    if not units:
        raise SystemExit(f"No child_utts.csv found under {args.data_dir} for datasets={args.datasets}")

    model_specs = parse_model_specs(args.models)
    allowed_at_tags = set(args.allowed_at_tags)

    process(
        units=units,
        model_specs=model_specs,
        which=args.which,
        out_mode=args.out_mode,
        seed=args.seed,
        min_age_months=args.min_age_months,
        max_age_months=args.max_age_months,
        preserve_trailing_punct=not args.no_preserve_trailing_punct,
        allowed_at_tags=allowed_at_tags,
        drop_chat_markers=not args.keep_chat_markers,
        drop_angle_artifacts=not args.keep_angle_artifacts,
    )


if __name__ == "__main__":
    main()
