#!/usr/bin/env python3
"""
create_context_caretakers.py
============================

Create *caretaker context (k1 only)* for CHILDES subsets — aligned with the NEW pipeline.

What changed vs the old script
------------------------------
OLD behavior:
  - Built a combined CHI/MOT/FAT dataframe per session
  - Context was "adult-only history" (MOT+FAT) that could be attached to all roles
  - Supported prev1_adult and prevK_adult

NEW behavior (your request):
  - We ONLY create context for caretaker utterances (MOT+FAT), not CHI.
  - We ONLY build k1 context (no k2 / no prevK).
  - The context of a caretaker utterance is ALWAYS the immediately previous caretaker utterance
    **in the same session**, respecting conversational turns by restricting to caretaker turns only.
    Concretely:
        ctx_k1_caretaker(row_t) = cleaned_text(previous caretaker row in same session) else ""

Inputs expected (from prepare_datasets.py)
-----------------------------------------
Per child directory we expect:
  - caretakers_utts.csv   (preferred; created by prepare_datasets.py)

We update (in-place) caretakers_utts.csv by adding:
  - ctx_k1_caretaker

Cleaning policy
---------------
We must be coherent with the "canonical cleaning" used elsewhere in your pipeline:
  - remove time bullets (\x15 ... \x15)
  - remove [...] bracket annotations
  - remove (...) parenthetical annotations
  - remove <...> angle-bracket material
  - drop xxx/yyy/www
  - drop @MARKER tokens
  - drop +fragment markers
  - drop &... markers (including &=... and &-uh)
  - drop 0... omission markers
  - collapse whitespace

We apply this cleaning to the CONTEXT TEXT (and, by default, to the source caretaker utterance
that becomes context). We do NOT modify `utterance` or `utterance_clean` columns produced
by prepare_datasets; we only compute the context column.

Ordering / "respect turns"
--------------------------
We preserve CHAT file order by sorting by:
  (session_id, file, line_no, utt_id, speaker)

This makes "previous caretaker utterance" mean "previous caretaker turn in the session".

CLI examples
------------
# all children in Manchester
python3 create_context_caretakers.py --dataset Manchester --child total --overwrite

# a single child
python3 create_context_caretakers.py --dataset Brown --child Adam --overwrite

# limit context to last 128 words (tail kept)
python3 create_context_caretakers.py --dataset Providence --child total --max-words 128 --overwrite
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

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

# If you prefer "discover children from folders", you can drop this and just iterate directories.
CHILDREN_BY_DATASET: Dict[str, List[str]] = {
    "Providence": ["Alex", "Ethan", "Lily", "Naima", "Violet", "William"],
    "Manchester": ["Anne", "Aran", "Becky", "Carl", "Dominic", "Gail",
                   "Joel", "John", "Liz", "Nicole", "Ruth", "Warren"],
    "Brown":      ["Adam", "Eve", "Sarah"],
}

# ────────────────────────────────────────────────────────────────
# Canonical cleaning (same logic as prepare_datasets.py)
# ────────────────────────────────────────────────────────────────

_TIMECODE_RE = re.compile(r"\x15\s*\d+(?:[_:]\d+)?\s*\x15")
_BRACKETS_RE = re.compile(r"\[[^\]]*]")
_PARENS_RE   = re.compile(r"\([^)]*\)")
_ANGLE_RE    = re.compile(r"<[^>]*>")
_UNTRANS_RE  = re.compile(r"\b(?:xxx|yyy|www)\b", re.IGNORECASE)

_PLUS_MARKER_RE = re.compile(r"(?:(?<=\s)|^)\+(?:[/.\-]+|\S+)")
_AT_MARKER_RE   = re.compile(r"(?:(?<=\s)|^)@[^\s]+")
_AMP_MARKER_RE  = re.compile(r"(?:(?<=\s)|^)&[^\s]+")
_ZERO_MARKER_RE = re.compile(r"(?:(?<=\s)|^)0[^\s]*")

_SPACES_RE = re.compile(r"\s+")


def clean_chat_for_context(text: str) -> str:
    s = "" if text is None else str(text)

    s = _TIMECODE_RE.sub(" ", s)
    s = _BRACKETS_RE.sub(" ", s)
    s = _PARENS_RE.sub(" ", s)
    s = _ANGLE_RE.sub(" ", s)
    s = _UNTRANS_RE.sub(" ", s)

    s = _AT_MARKER_RE.sub(" ", s)
    s = _PLUS_MARKER_RE.sub(" ", s)
    s = _AMP_MARKER_RE.sub(" ", s)
    s = _ZERO_MARKER_RE.sub(" ", s)

    s = _SPACES_RE.sub(" ", s).strip()
    return s


def clip_words_tail(text: str, max_words: Optional[int]) -> str:
    if max_words is None or max_words <= 0:
        return text
    toks = str(text).split()
    if len(toks) <= max_words:
        return text
    return " ".join(toks[-max_words:])


# ────────────────────────────────────────────────────────────────
# Core logic: compute ctx_k1_caretaker on caretakers_utts.csv
# ────────────────────────────────────────────────────────────────

CTX_COL = "ctx_k1_caretaker"


def compute_ctx_k1_for_child(child_dir: Path, max_words: Optional[int]) -> pd.DataFrame:
    """
    Loads caretakers_utts.csv and returns updated df with ctx_k1_caretaker.
    Context is previous caretaker utterance (cleaned) within the same session.
    """
    path = child_dir / "caretakers_utts.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path} (run prepare_datasets.py first).")

    df = pd.read_csv(path)

    # Defensive columns
    for c in ["session_id", "file", "line_no", "utt_id", "speaker", "utterance", "utterance_clean"]:
        if c not in df.columns:
            df[c] = pd.NA

    df["session_id_num"] = pd.to_numeric(df["session_id"], errors="coerce").astype("Int64")
    df["line_no_num"] = pd.to_numeric(df["line_no"], errors="coerce")
    df["utt_id_num"] = pd.to_numeric(df["utt_id"], errors="coerce")

    # Preserve CHAT order inside session
    df = df.sort_values(
        by=["session_id_num", "file", "line_no_num", "utt_id_num", "speaker"],
        kind="stable"
    ).reset_index(drop=True)

    # We build context per session by shifting previous caretaker row.
    # Source for context: prefer utterance_clean if present; else clean(utterance)
    ctx_vals: List[str] = [""] * len(df)

    for sid, g in df.groupby("session_id_num", dropna=False, sort=False):
        idxs = list(g.index)

        prev_text = ""
        for i in idxs:
            # context for this row is previous caretaker text in this session
            ctx_vals[i] = clip_words_tail(prev_text, max_words)

            # update prev_text from current row (this current caretaker becomes next context)
            u_clean = df.at[i, "utterance_clean"]
            if isinstance(u_clean, str) and u_clean.strip():
                prev_text = clean_chat_for_context(u_clean)
            else:
                prev_text = clean_chat_for_context(df.at[i, "utterance"])

    df[CTX_COL] = ctx_vals

    # Drop helper cols before saving (optional, but keeps file clean)
    df.drop(columns=["session_id_num", "line_no_num", "utt_id_num"], inplace=True, errors="ignore")
    return df


def write_back(child_dir: Path, df_new: pd.DataFrame, overwrite: bool) -> None:
    path = child_dir / "caretakers_utts.csv"
    base = pd.read_csv(path)

    if (CTX_COL in base.columns) and (not overwrite):
        print(f"[skip] {child_dir.name}: {CTX_COL} already exists (use --overwrite).")
        return

    # Backup once
    bkp = path.with_suffix(".csv.bak")
    if not bkp.exists():
        base.to_csv(bkp, index=False)

    df_new.to_csv(path, index=False)
    print(f"[ok] {child_dir.name}: updated -> {path.name}")


# ────────────────────────────────────────────────────────────────
# Orchestration
# ────────────────────────────────────────────────────────────────

def process_child(
    dataset: str,
    child: str,
    max_words: Optional[int],
    overwrite: bool,
) -> None:
    base = DATA_ROOTS[dataset]
    child_dir = base / child
    if not child_dir.exists():
        raise FileNotFoundError(f"Missing child dir: {child_dir}")

    df_new = compute_ctx_k1_for_child(child_dir, max_words=max_words)
    write_back(child_dir, df_new, overwrite=overwrite)


def process_dataset(
    dataset: str,
    child_arg: str,
    max_words: Optional[int],
    overwrite: bool,
) -> None:
    base = DATA_ROOTS[dataset]
    if not base.exists():
        raise FileNotFoundError(f"Missing dataset root: {base}")

    children = CHILDREN_BY_DATASET.get(dataset, [])
    if child_arg.lower() == "total":
        # If registry is empty, fallback to folder discovery
        if not children:
            children = sorted([p.name for p in base.iterdir() if p.is_dir()])

        for idx, ch in enumerate(children, 1):
            print(f"\n==> {dataset} ({idx}/{len(children)}) {ch}")
            try:
                process_child(dataset, ch, max_words=max_words, overwrite=overwrite)
            except FileNotFoundError as e:
                print(f"[skip] {ch}: {e}")
    else:
        process_child(dataset, child_arg, max_words=max_words, overwrite=overwrite)


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Create caretaker k1 context column for caretakers_utts.csv (prev caretaker utterance within-session)."
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
        "--max-words",
        type=int,
        default=128,
        help="Trim context to last N words (tail kept). Use 0/neg to disable.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite ctx_k1_caretaker if it already exists.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> None:
    args = build_arg_parser().parse_args(argv)
    max_words = None if args.max_words is None or args.max_words <= 0 else int(args.max_words)
    process_dataset(
        dataset=args.dataset,
        child_arg=args.child,
        max_words=max_words,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
