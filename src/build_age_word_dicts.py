#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_age_binned_dicts.py
=========================

Build age-binned word-frequency dictionaries from Stage-0 CHILDES outputs.

Assumptions (Stage 0 = prepare_datasets.py):
- Each child folder contains:
    child_utts.csv
    session_index.csv   (must contain columns: session_id, age_months)

No extra cleaning:
- We DO NOT remove brackets/markers, DO NOT enforce @-policy here.
- We ONLY tokenize the chosen text column with TOKEN_RE.

Recommended text column:
- utterance_clean (canonical Stage 0 output)
- fallback: clean_utterance (alias if you added it)

Outputs (per bin directory):
- counts.json
- probs.json
- vocab.txt
- summary.csv

Directory layout (global scope):
  <OUT_DIR>/bin_006-011/{counts.json, probs.json, vocab.txt}

If --by-child:
  <OUT_DIR>/<DATASET>/<CHILD>/bin_006-011/{...}
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


# Same token pattern as prepare_datasets.py
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)*")


# ────────────────────────────────────────────────────────────────
# Data discovery
# ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChildUnit:
    dataset: str
    child: str
    folder: Path
    child_utts_csv: Path
    session_index_csv: Path


def iter_child_units(data_dir: Path, datasets: List[str]) -> List[ChildUnit]:
    """
    Find all <data_dir>/<DATASET>/<CHILD>/child_utts.csv with a sibling session_index.csv.
    """
    ds_set = set(datasets)
    units: List[ChildUnit] = []

    for p in data_dir.rglob("child_utts.csv"):
        try:
            rel = p.relative_to(data_dir)
        except ValueError:
            continue

        # Expect: DATASET / CHILD / child_utts.csv  (at least 3 parts)
        if len(rel.parts) < 3:
            continue

        dataset = rel.parts[0]
        if dataset not in ds_set:
            continue

        folder = p.parent
        child = folder.name
        sess_idx = folder / "session_index.csv"
        if not sess_idx.exists():
            # Hard fail later with a clear error; for now we still record it
            sess_idx = folder / "session_index.csv"

        units.append(ChildUnit(
            dataset=dataset,
            child=child,
            folder=folder,
            child_utts_csv=p,
            session_index_csv=sess_idx,
        ))

    units.sort(key=lambda u: (u.dataset, u.child, str(u.folder)))
    return units


# ────────────────────────────────────────────────────────────────
# Loading + age merge (NO “age candidates”)
# ────────────────────────────────────────────────────────────────

def load_stage0_with_age(unit: ChildUnit) -> pd.DataFrame:
    """
    Load child_utts.csv and merge age_months from session_index.csv via session_id.
    Expects:
      - child_utts.csv has session_id
      - session_index.csv has session_id, age_months
    """
    utts = pd.read_csv(unit.child_utts_csv)

    if "session_id" not in utts.columns:
        raise RuntimeError(f"{unit.child_utts_csv} missing required column: session_id")

    if not unit.session_index_csv.exists():
        raise RuntimeError(
            f"{unit.folder} is missing session_index.csv (needed for ages): {unit.session_index_csv}"
        )

    sess = pd.read_csv(unit.session_index_csv)
    if "session_id" not in sess.columns or "age_months" not in sess.columns:
        raise RuntimeError(
            f"{unit.session_index_csv} must contain columns: session_id, age_months"
        )

    sess_age = sess[["session_id", "age_months"]].copy()
    sess_age["session_id"] = pd.to_numeric(sess_age["session_id"], errors="coerce")
    sess_age["age_months"] = pd.to_numeric(sess_age["age_months"], errors="coerce")

    utts["session_id"] = pd.to_numeric(utts["session_id"], errors="coerce")

    merged = utts.merge(sess_age, on="session_id", how="left")
    return merged


# ────────────────────────────────────────────────────────────────
# Tokenization (NO CLEANING)
# ────────────────────────────────────────────────────────────────

def tokenize(text: str, lowercase: bool) -> List[str]:
    if text is None:
        return []
    s = str(text)
    if lowercase:
        s = s.lower()
    return TOKEN_RE.findall(s)


# ────────────────────────────────────────────────────────────────
# Binning helpers
# ────────────────────────────────────────────────────────────────

def bin_start(age_months: float, bin_months: int, min_age_months: float) -> int:
    """
    Compute integer bin start month. Uses floor-based binning from min_age_months.
    For stable labels like 006-011, min_age_months should usually be an integer.
    """
    base = int(math.floor(min_age_months))
    if age_months < min_age_months:
        return base
    k = int((age_months - min_age_months) // bin_months)
    return int(base + k * bin_months)


def bin_label(start: int, bin_months: int) -> str:
    end = start + bin_months - 1
    return f"{start:03d}-{end:03d}"


# ────────────────────────────────────────────────────────────────
# Writing
# ────────────────────────────────────────────────────────────────

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


# ────────────────────────────────────────────────────────────────
# Core build
# ────────────────────────────────────────────────────────────────

def build_dicts(
    units: List[ChildUnit],
    out_dir: Path,
    bin_months: int,
    min_age_months: float,
    max_age_months: float,
    by_child: bool,
    lowercase: bool,
    min_token_len: int,
    text_col: str,
) -> None:
    ensure_dir(out_dir)

    counters: Dict[Tuple, Counter] = defaultdict(Counter)
    token_totals: Dict[Tuple, int] = defaultdict(int)
    utt_totals: Dict[Tuple, int] = defaultdict(int)

    skipped = 0
    for unit in units:
        try:
            df = load_stage0_with_age(unit)
        except Exception as e:
            print(f"[WARN] Skipping {unit.folder}: {e}")
            skipped += 1
            continue

        if text_col not in df.columns:
            print(f"[WARN] Skipping {unit.folder}: missing text column '{text_col}'")
            skipped += 1
            continue

        df = df[df["age_months"].notna()].copy()
        df = df[(df["age_months"] >= min_age_months) & (df["age_months"] <= max_age_months)]
        if df.empty:
            continue

        for _, row in df.iterrows():
            age_m = float(row["age_months"])
            b0 = bin_start(age_m, bin_months, min_age_months)
            bl = bin_label(b0, bin_months)

            toks = tokenize(row[text_col], lowercase=lowercase)
            if min_token_len > 1:
                toks = [t for t in toks if len(t) >= min_token_len]
            if not toks:
                continue

            key = (unit.dataset, unit.child, bl) if by_child else (bl,)
            counters[key].update(toks)
            token_totals[key] += len(toks)
            utt_totals[key] += 1

    summary_rows: List[Dict] = []

    for key, ctr in sorted(counters.items(), key=lambda kv: kv[0]):
        total_tokens = token_totals[key]
        total_utts = utt_totals[key]
        vocab_size = len(ctr)

        if total_tokens <= 0 or vocab_size <= 0:
            continue

        if by_child:
            dataset, child, bl = key
            base_dir = out_dir / dataset / child / f"bin_{bl}"
            dataset_out, child_out = dataset, child
        else:
            (bl,) = key
            base_dir = out_dir / f"bin_{bl}"
            dataset_out, child_out = "ALL", "ALL"

        ensure_dir(base_dir)

        counts = dict(ctr)
        probs = {w: c / total_tokens for w, c in counts.items()}

        write_json(base_dir / "counts.json", counts)
        write_json(base_dir / "probs.json", probs)

        vocab_sorted = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        with (base_dir / "vocab.txt").open("w", encoding="utf-8") as f:
            for w, _c in vocab_sorted:
                f.write(w + "\n")

        summary_rows.append({
            "scope": "by_child" if by_child else "global",
            "dataset": dataset_out,
            "child": child_out,
            "bin_label": bl,
            "bin_months": bin_months,
            "n_utterances_used": total_utts,
            "n_tokens_used": total_tokens,
            "vocab_size": vocab_size,
            "text_col_used": text_col,
            "output_dir": str(base_dir),
        })

    pd.DataFrame(summary_rows).to_csv(out_dir / "summary.csv", index=False)
    print(f"[OK] Wrote dictionaries to: {out_dir}")
    if skipped:
        print(f"[WARN] Skipped {skipped} child folders (see warnings above).")


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=str, default="data",
                    help="Path to data/ directory containing Brown/, Manchester/, Providence/")
    ap.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"],
                    help="Top-level dataset folders to include")
    ap.add_argument("--bin_months", type=int, required=True, choices=[3, 6, 12],
                    help="Bin size in months (3, 6, or 12)")
    ap.add_argument("--out_dir", type=str, required=True,
                    help="Output directory to write bins")
    ap.add_argument("--min_age_months", type=float, default=0.0,
                    help="Minimum age (months) included in bins")
    ap.add_argument("--max_age_months", type=float, default=120.0,
                    help="Maximum age (months) included in bins")
    ap.add_argument("--by_child", action="store_true",
                    help="If set, output separate dictionaries per child")
    ap.add_argument("--no_lowercase", action="store_true",
                    help="Disable lowercasing tokens")
    ap.add_argument("--min_token_len", type=int, default=1,
                    help="Drop tokens shorter than this length (default 1 keeps all)")
    ap.add_argument("--text_col", type=str, default="utterance_clean",
                    help="Which column to tokenize (default: utterance_clean). "
                         "If you prefer your alias, use --text_col clean_utterance.")

    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)

    units = iter_child_units(data_dir, args.datasets)
    if not units:
        raise SystemExit(f"No child_utts.csv found under {data_dir} for datasets={args.datasets}.")

    build_dicts(
        units=units,
        out_dir=out_dir,
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
