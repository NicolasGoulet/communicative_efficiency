#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_contexts_slurm_data_chi.py
================================

Adds context columns to slurm_data/*/*/chi.csv using caretakers.csv as the source.

For each CHI row:
  - context_k1 : previous 1 caretakers utterance_clean earlier in the same session
  - context_kK : previous K caretakers utterance_clean (if K>1), concatenated with spaces

Ordering is computed by combining chi + caretakers within each session and sorting by:
  (session_id_num, file, line_no_num, utt_id_num, role_order)

We only *consume* caretakers utterance_clean into the context history.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd


# -------------------------
# CSV/TSV delimiter detect
# -------------------------
def detect_sep(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        return dialect.delimiter
    except Exception:
        return ","


def read_table(path: Path) -> tuple[pd.DataFrame, str]:
    sep = detect_sep(path)
    df = pd.read_csv(path, sep=sep, engine="python")
    return df, sep


def backup_once(path: Path) -> None:
    bkp = path.with_suffix(path.suffix + ".bak")  # chi.csv -> chi.csv.bak
    if not bkp.exists():
        bkp.write_bytes(path.read_bytes())


def num_col(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def concat_last_k(hist: List[str], k: int) -> str:
    if k <= 0:
        return ""
    if not hist:
        return ""
    return " ".join(hist[-k:])


def ensure_cols(df: pd.DataFrame, required: List[str], who: str, path: Path) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"[{who}] Missing columns {missing} in {path}")


def build_context_for_chi(
    chi: pd.DataFrame,
    care: pd.DataFrame,
    k: int,
    max_words: Optional[int],
) -> pd.Series:
    # minimal required columns
    ensure_cols(chi, ["session_id", "file", "line_no", "utterance_clean"], "CHI", Path("<chi>"))
    ensure_cols(care, ["session_id", "file", "line_no", "utterance_clean"], "CARE", Path("<caretakers>"))

    # normalize
    chi2 = chi.copy()
    care2 = care.copy()

    for df in (chi2, care2):
        df["session_id_str"] = df["session_id"].astype(str).fillna("")
        df["session_id_num"] = num_col(df["session_id"])
        df["file_str"] = df["file"].astype(str).fillna("")
        df["line_no_num"] = num_col(df["line_no"])
        if "utt_id" in df.columns:
            df["utt_id_num"] = num_col(df["utt_id"])
        else:
            df["utt_id_num"] = pd.NA

    chi2["_role"] = "CHI"
    care2["_role"] = "CARE"

    # combine for ordering
    combo = pd.concat([chi2, care2], ignore_index=True)

    # group key: prefer numeric session id; fall back to string
    combo["_sid_key"] = combo["session_id_num"].astype("Int64").astype(str)
    # if session_id_num is NA, use string
    combo.loc[combo["session_id_num"].isna(), "_sid_key"] = "S:" + combo.loc[combo["session_id_num"].isna(), "session_id_str"]

    # role order: caretakers first when tie
    combo["_role_order"] = combo["_role"].map({"CARE": 0, "CHI": 1}).fillna(9).astype(int)

    combo = combo.sort_values(
        by=["_sid_key", "file_str", "line_no_num", "utt_id_num", "_role_order"],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)

    # compute contexts only for CHI rows, consuming CARE utterances
    ctx_out = [""] * len(combo)
    current_sid = None
    hist: List[str] = []

    for i, r in combo.iterrows():
        sid = r["_sid_key"]
        if sid != current_sid:
            current_sid = sid
            hist = []

        # assign context for CHI rows from caretakers history
        if r["_role"] == "CHI":
            ctx = concat_last_k(hist, k)
            if max_words and max_words > 0:
                toks = ctx.split()
                if len(toks) > max_words:
                    ctx = " ".join(toks[-max_words:])
            ctx_out[i] = ctx

        # update history only with caretakers utterance_clean
        if r["_role"] == "CARE":
            txt = "" if pd.isna(r["utterance_clean"]) else str(r["utterance_clean"]).strip()
            if txt:
                hist.append(txt)

    combo["__ctx__"] = ctx_out

    # pull back only CHI rows in original chi order
    # We need a stable join key into combo. Create an internal row id before concat.
    chi2["__row_id__"] = range(len(chi2))
    care2["__row_id__"] = -1  # unused
    combo2 = pd.concat([chi2, care2], ignore_index=True)

    # redo same sort to align __ctx__ (simplest: rebuild with ids)
    combo2["_sid_key"] = combo2["session_id_num"].astype("Int64").astype(str)
    combo2.loc[combo2["session_id_num"].isna(), "_sid_key"] = "S:" + combo2.loc[combo2["session_id_num"].isna(), "session_id_str"]
    combo2["_role_order"] = combo2["_role"].map({"CARE": 0, "CHI": 1}).fillna(9).astype(int)
    combo2 = combo2.sort_values(
        by=["_sid_key", "file_str", "line_no_num", "utt_id_num", "_role_order"],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)

    combo2["__ctx__"] = ctx_out  # aligned by same sort

    chi_ctx = combo2.loc[combo2["_role"] == "CHI", ["__row_id__", "__ctx__"]].sort_values("__row_id__")
    return chi_ctx["__ctx__"].reset_index(drop=True)


def iter_child_dirs(root: Path, dataset: str, child: str) -> List[Path]:
    datasets = [dataset] if dataset != "ALL" else [p.name for p in root.iterdir() if p.is_dir() and p.name != "filelists"]
    out: List[Path] = []
    for ds in datasets:
        ds_dir = root / ds
        if not ds_dir.exists():
            continue
        if child == "total":
            for ch_dir in sorted([p for p in ds_dir.iterdir() if p.is_dir()]):
                out.append(ch_dir)
        else:
            ch_dir = ds_dir / child
            if ch_dir.exists() and ch_dir.is_dir():
                out.append(ch_dir)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="slurm_data", help="Root folder containing datasets (default: slurm_data).")
    ap.add_argument("--dataset", default="ALL", help="Brown | Manchester | Providence | ALL (default).")
    ap.add_argument("--child", default="total", help="Child name or 'total' (default).")
    ap.add_argument("--K", type=int, default=1, help="Number of caretakers utts to concat (default 1).")
    ap.add_argument("--max-words", type=int, default=128, help="Keep last N words in context (0 disables).")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing context columns.")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root not found: {root}")

    child_dirs = iter_child_dirs(root, args.dataset, args.child)
    if not child_dirs:
        print("[WARN] No child dirs found.")
        return

    k = max(1, int(args.K))
    max_words = None if args.max_words is None or args.max_words <= 0 else int(args.max_words)
    col_name = "context_k1" if k == 1 else f"context_k{k}"

    for ch_dir in child_dirs:
        chi_path = ch_dir / "chi.csv"
        care_path = ch_dir / "caretakers.csv"
        if not chi_path.exists() or not care_path.exists():
            continue

        chi_df, chi_sep = read_table(chi_path)
        care_df, _ = read_table(care_path)

        if (col_name in chi_df.columns) and (not args.overwrite):
            print(f"[SKIP] {chi_path} already has {col_name} (use --overwrite)")
            continue

        # build and write
        ctx = build_context_for_chi(chi_df, care_df, k=k, max_words=max_words)
        backup_once(chi_path)
        chi_df[col_name] = ctx

        chi_df.to_csv(chi_path, index=False, sep=chi_sep)
        print(f"[OK] Wrote {col_name} -> {chi_path}")

    print("DONE")


if __name__ == "__main__":
    main()

