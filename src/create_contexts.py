#!/usr/bin/env python3
"""
creating_contexts.py
====================

Create and append *context text columns* to utterance CSVs for CHILDES subsets.
This script **does not** compute contextual surprisal; it only writes context text
(e.g., previous turn(s)) into new columns so later scoring scripts can compute p(u|c).

Datasets supported:
  • Providence: data/Providence/Providence/<Child>
  • Manchester: data/Manchester/<Child>
  • Brown:      data/Brown/<Child>

It writes new columns into:
  child_utts.csv, mot_utts.csv, fat_utts.csv  (if file exists)

Context definitions (extensible):
  - prev1_any               : immediate previous utterance in same session (any speaker)
  - prevK_any               : concat last K utterances in same session (any speaker)
  - prev1_adult_for_child   : for CHI rows, last MOT/FAT utterance in same session
  - prevK_adult_for_child   : for CHI rows, concat last K MOT/FAT utts in session
  - prev1_child_for_child   : for CHI rows, last CHI utterance in same session
  - prevK_child_for_child   : for CHI rows, concat last K CHI utts in session
  - prevK_samefile          : for any row, concat last K utts restricted to same 'file'

Output column names (cleaned text):
  ctx_<name>[_K{K}]

Notes
-----
• Cleaning: by default we apply the same "surprisal-clean" policy as in compute_informativeness.
• Truncation: you can cap contexts by word count (--max-words, tail kept).
• Overwrite: re-create existing columns only if --overwrite is set (default off).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import re
import json

# ────────────────────────────────────────────────────────────────
# Repo roots and dataset registry
# ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DATA_ROOTS = {
    "Providence": PROJECT_ROOT / "data" / "Providence" / "Providence",
    "Manchester": PROJECT_ROOT / "data" / "Manchester",
    "Brown":      PROJECT_ROOT / "data" / "Brown",
}
RESULTS_ROOTS = {ds: (PROJECT_ROOT / "results" / ds) for ds in DATA_ROOTS.keys()}

CHILDREN_BY_DATASET: Dict[str, List[str]] = {
    "Providence": ["Alex", "Ethan", "Lily", "Naima", "Violet", "William"],
    "Manchester": ["Anne", "Aran", "Becky", "Carl", "Dominic", "Gail",
                   "Joel", "John", "Liz", "Nicole", "Ruth", "Warren"],
    "Brown":      ["Adam", "Eve", "Sarah"],
}

# ────────────────────────────────────────────────────────────────
# Cleaning (match compute_informativeness)
# ────────────────────────────────────────────────────────────────
_TIMECODE_RE = re.compile(r"\x15\d+_\d+\x15")
_BRACKETS_RE = re.compile(r"\[[^\]]*]")
_ANGLE_RE    = re.compile(r"<[^>]*>")
_UNTRANS_RE  = re.compile(r"\b(?:xxx|yyy|www)\b", re.IGNORECASE)
_PLUS_MARKER_RE = re.compile(r"(?:(?<=\s)|^)\+(?:[/.\-]+|\S+)")
_AT_MARKER_RE   = re.compile(r"(?:(?<=\s)|^)@[^\s]+")
_EVENT_MARKER_RE = re.compile(r"(?:(?<=\s)|^)&=[^\s]+")
_SPACES_RE = re.compile(r"\s+")

def surprisal_clean(text: str) -> str:
    s = text
    s = _TIMECODE_RE.sub(" ", s)
    s = _BRACKETS_RE.sub(" ", s)
    s = _ANGLE_RE.sub(" ", s)
    s = _UNTRANS_RE.sub(" ", s)
    s = _AT_MARKER_RE.sub(" ", s)
    s = _PLUS_MARKER_RE.sub(" ", s)
    s = _EVENT_MARKER_RE.sub(" ", s)
    s = _SPACES_RE.sub(" ", s).strip()
    return s

def maybe_clean(text: str, mode: str) -> str:
    if mode == "none":
        return str(text)
    return surprisal_clean(str(text))

def clip_words_tail(text: str, max_words: Optional[int]) -> str:
    if max_words is None or max_words <= 0:
        return text
    toks = str(text).split()
    if len(toks) <= max_words:
        return text
    return " ".join(toks[-max_words:])  # keep most recent words

# ────────────────────────────────────────────────────────────────
# I/O helpers
# ────────────────────────────────────────────────────────────────
def load_role_df(child_dir: Path, role: str) -> Optional[pd.DataFrame]:
    fname = {"CHI": "child_utts.csv", "MOT": "mot_utts.csv", "FAT": "fat_utts.csv"}[role]
    path = child_dir / fname
    if not path.exists():
        return None
    df = pd.read_csv(path)
    # Create a robust merge key
    for c in ["session_id", "utt_id", "file", "line_no"]:
        if c not in df.columns:
            df[c] = pd.NA
    df["session_id_num"] = pd.to_numeric(df["session_id"], errors="coerce").astype("Int64")
    df["utt_id_num"] = pd.to_numeric(df["utt_id"], errors="coerce")
    df["line_no_num"] = pd.to_numeric(df["line_no"], errors="coerce")
    df["merge_key"] = df.apply(
        lambda r: f"{r.get('session_id')}::{r.get('file')}::{r.get('line_no')}::{r.get('utt_id')}",
        axis=1,
    )
    df["role"] = role
    return df

def write_back(child_dir: Path, role: str, updated_cols: pd.DataFrame, overwrite: bool) -> None:
    fname = {"CHI": "child_utts.csv", "MOT": "mot_utts.csv", "FAT": "fat_utts.csv"}[role]
    path = child_dir / fname
    if not path.exists():
        return

    base = pd.read_csv(path)
    if "merge_key" not in base.columns:
        for c in ["session_id", "utt_id", "file", "line_no"]:
            if c not in base.columns:
                base[c] = pd.NA
        base["merge_key"] = base.apply(
            lambda r: f"{r.get('session_id')}::{r.get('file')}::{r.get('line_no')}::{r.get('utt_id')}",
            axis=1,
        )

    # Only add new columns (or overwrite if flagged)
    cols_to_add = [c for c in updated_cols.columns if c not in ("merge_key",)]
    if not overwrite:
        # If not overwriting, only keep columns that do NOT already exist in base
        cols_to_add = [c for c in cols_to_add if c not in base.columns]

    if not cols_to_add:
        print(f"[{role}] nothing to update in {path.name}")
        return

    # Merge on merge_key; suffixes apply ONLY to overlapping column names
    merged = base.merge(
        updated_cols[["merge_key"] + cols_to_add],
        on="merge_key",
        how="left",
        suffixes=("", "_new"),
    )

    for c in cols_to_add:
        new_col = f"{c}_new"

        if overwrite:
            # Overwrite existing values with new ones when provided
            if new_col in merged.columns:
                merged[c] = merged[new_col].where(merged[new_col].notna(), merged.get(c))
                merged.drop(columns=[new_col], inplace=True)
        else:
            # Not overwriting: we know c was NOT in base, so either:
            #  - it came in as 'c' (no suffix), OR
            #  - in some weird overlap case as 'c_new' (then rename).
            if new_col in merged.columns:
                merged[c] = merged[new_col]
                merged.drop(columns=[new_col], inplace=True)
            # If new_col is not there, 'c' is already the right-hand column and we don't touch it.

    # Backup once
    bkp = path.with_suffix(".csv.bak")
    if not bkp.exists():
        base.to_csv(bkp, index=False)

    merged.to_csv(path, index=False)
    print(f"[{role}] updated -> {path}")

# ────────────────────────────────────────────────────────────────
# Context building helpers
# ────────────────────────────────────────────────────────────────
def build_combined(child_dir: Path) -> pd.DataFrame:
    dfs = []
    for role in ("CHI", "MOT", "FAT"):
        df = load_role_df(child_dir, role)
        if df is not None and not df.empty:
            dfs.append(df)
    if not dfs:
        raise FileNotFoundError(f"No utt CSVs found under: {child_dir}")

    all_df = pd.concat(dfs, ignore_index=True)
    # Sort robustly within session
    all_df = all_df.sort_values(
        by=["session_id_num", "file", "line_no_num", "utt_id_num", "role"],
        kind="stable"
    ).reset_index(drop=True)
    return all_df

def concat_last_k(texts: List[str], k: int) -> str:
    if k <= 1:
        return texts[-1] if texts else ""
    start = max(0, len(texts) - k)
    return " ".join(texts[start:])

def _context_prevK_any(g: pd.DataFrame, k: int, clean_mode: str, max_words: Optional[int]) -> pd.Series:
    out = []
    acc: List[str] = []
    for _, r in g.iterrows():
        out.append(clip_words_tail(concat_last_k(acc, k), max_words))
        acc.append(maybe_clean(r["utterance"], clean_mode))
    return pd.Series(out, index=g.index, dtype="object")

def _context_prevK_filter(
    g: pd.DataFrame,
    k: int,
    roles: Tuple[str, ...],
    clean_mode: str,
    max_words: Optional[int]
) -> pd.Series:
    out = []
    history: List[str] = []
    for _, r in g.iterrows():
        # choose last k from history (already filtered)
        out.append(clip_words_tail(concat_last_k(history, k), max_words))
        u = maybe_clean(r["utterance"], clean_mode)
        if r["role"] in roles:
            history.append(u)
    return pd.Series(out, index=g.index, dtype="object")

# ────────────────────────────────────────────────────────────────
# Core: add_context_columns (fixed prev1_* logic)
# ────────────────────────────────────────────────────────────────
def add_context_columns(
    all_df: pd.DataFrame,
    definitions: List[str],
    K: int,
    clean_mode: str,
    max_words: Optional[int],
) -> pd.DataFrame:
    """
    definitions: list of keys among
      prev1_any, prevK_any, prev1_adult_for_child, prevK_adult_for_child,
      prev1_child_for_child, prevK_child_for_child, prevK_samefile
    """
    out = all_df.copy()

    # Build within each session (and per file for samefile variant)
    for sid, g_sess in out.groupby("session_id_num", dropna=True, sort=False):
        idxs = g_sess.index
        mask_chi = (g_sess["role"] == "CHI")

        # -------- Any-speaker variants --------
        if "prev1_any" in definitions:
            ctx_prev1_any = _context_prevK_any(
                g_sess, k=1, clean_mode=clean_mode, max_words=max_words
            )
            out.loc[idxs, "ctx_prev1_any"] = ctx_prev1_any

        if "prevK_any" in definitions:
            ctx_prevK_any = _context_prevK_any(
                g_sess, k=K, clean_mode=clean_mode, max_words=max_words
            )
            out.loc[idxs, f"ctx_prevK_any_K{K}"] = ctx_prevK_any

        # -------- Adult-for-child (MOT/FAT → CHI) --------
        if "prev1_adult_for_child" in definitions:
            ctx_prev1_adult = _context_prevK_filter(
                g_sess, k=1, roles=("MOT", "FAT"),
                clean_mode=clean_mode, max_words=max_words
            )
            # keep the full last MOT/FAT utterance
            out.loc[idxs[mask_chi], "ctx_prev1_adult"] = ctx_prev1_adult[mask_chi]

        if "prevK_adult_for_child" in definitions:
            ctx_prevK_adult = _context_prevK_filter(
                g_sess, k=K, roles=("MOT", "FAT"),
                clean_mode=clean_mode, max_words=max_words
            )
            out.loc[idxs[mask_chi], f"ctx_prevK_adult_K{K}"] = ctx_prevK_adult[mask_chi]

        # -------- Child-for-child (CHI history → CHI) --------
        if "prev1_child_for_child" in definitions:
            ctx_prev1_child = _context_prevK_filter(
                g_sess, k=1, roles=("CHI",),
                clean_mode=clean_mode, max_words=max_words
            )
            out.loc[idxs[mask_chi], "ctx_prev1_child"] = ctx_prev1_child[mask_chi]

        if "prevK_child_for_child" in definitions:
            ctx_prevK_child = _context_prevK_filter(
                g_sess, k=K, roles=("CHI",),
                clean_mode=clean_mode, max_words=max_words
            )
            out.loc[idxs[mask_chi], f"ctx_prevK_child_K{K}"] = ctx_prevK_child[mask_chi]

        # -------- Same-file K (any roles, but restricted to 'file') --------
        if "prevK_samefile" in definitions:
            for file_id, g_file in g_sess.groupby("file", sort=False):
                idxf = g_file.index
                out.loc[idxf, f"ctx_prevK_samefile_K{K}"] = _context_prevK_any(
                    g_file, k=K, clean_mode=clean_mode, max_words=max_words
                )

    return out

# ────────────────────────────────────────────────────────────────
# Orchestration
# ────────────────────────────────────────────────────────────────
def process_child(
    dataset: str,
    child: str,
    contexts: List[str],
    K: int,
    clean_mode: str,
    max_words: Optional[int],
    overwrite: bool,
) -> None:
    base = DATA_ROOTS[dataset]
    child_dir = base / child
    if not child_dir.exists():
        raise FileNotFoundError(f"Missing child dir: {child_dir}")

    all_df = build_combined(child_dir)
    with_ctx = add_context_columns(
        all_df, definitions=contexts, K=K,
        clean_mode=clean_mode, max_words=max_words
    )

    # Split by role and write back only the new columns (plus merge_key)
    new_cols = [c for c in with_ctx.columns if c.startswith("ctx_")]
    minimal = with_ctx[["merge_key", "role"] + new_cols].copy()

    for role in ("CHI", "MOT", "FAT"):
        sub = minimal[minimal["role"] == role].drop(columns=["role"])
        if not sub.empty:
            write_back(child_dir, role, sub, overwrite=overwrite)

def process_dataset(
    dataset: str,
    child_arg: str,
    contexts: List[str],
    K: int,
    clean_mode: str,
    max_words: Optional[int],
    overwrite: bool,
) -> None:
    children = CHILDREN_BY_DATASET[dataset]
    if child_arg.lower() == "total":
        for idx, ch in enumerate(children, 1):
            print(f"\n==> {dataset} ({idx}/{len(children)}) {ch}")
            process_child(dataset, ch, contexts, K, clean_mode, max_words, overwrite)
    else:
        if child_arg not in children:
            raise ValueError(f"[{dataset}] Unknown child '{child_arg}'. Valid: {', '.join(children)}")
        process_child(dataset, child_arg, contexts, K, clean_mode, max_words, overwrite)

# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Create context text columns for CHILDES utterance CSVs."
    )
    p.add_argument(
        "--dataset",
        required=True,
        choices=list(DATA_ROOTS.keys()),
        help="Providence | Manchester | Brown",
    )
    p.add_argument(
        "--child",
        required=True,
        help="Child name under the dataset, or 'total' for all children.",
    )
    p.add_argument(
        "--contexts",
        default="prev1_any,prev1_adult_for_child,prevK_any,prevK_adult_for_child",
        help=("Comma-separated context defs: "
              "prev1_any,prevK_any,"
              "prev1_adult_for_child,prevK_adult_for_child,"
              "prev1_child_for_child,prevK_child_for_child,"
              "prevK_samefile"),
    )
    p.add_argument(
        "--K",
        type=int,
        default=3,
        help="K for prevK_* contexts.",
    )
    p.add_argument(
        "--clean",
        choices=["surprisal", "none"],
        default="surprisal",
        help="Apply surprisal-style cleaning to context text.",
    )
    p.add_argument(
        "--max-words",
        type=int,
        default=128,
        help="Trim contexts to last N words (per cell). Use 0/neg to disable.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing context columns (default: only add if absent).",
    )
    return p

def main(argv: Optional[List[str]] = None) -> None:
    args = build_arg_parser().parse_args(argv)
    ctx_defs = [c.strip() for c in args.contexts.split(",") if c.strip()]
    process_dataset(
        dataset=args.dataset,
        child_arg=args.child,
        contexts=ctx_defs,
        K=args.K,
        clean_mode=args.clean,
        max_words=(None if args.max_words is None or args.max_words <= 0 else args.max_words),
        overwrite=args.overwrite,
    )

if __name__ == "__main__":
    main()

