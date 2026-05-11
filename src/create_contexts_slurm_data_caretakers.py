#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_contexts_slurm_data_caretakers.py
=======================================

Adds context columns to slurm_data/*/*/caretakers.csv.

For each caretakers row:
  - context_k1 : previous 1 utterance_clean earlier in the same session
  - context_kK : previous K utterance_clean (if K>1), concatenated with spaces

By default, history is built from ANY speaker (CHI + caretakers).
You can restrict history with --source:
  - any         : CHI + caretakers (default)
  - chi_only    : only CHI utterances contribute to history
  - care_only   : only caretakers utterances contribute to history
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Optional, List

import pandas as pd


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
    bkp = path.with_suffix(path.suffix + ".bak")
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


def build_context_for_caretakers(
    chi: pd.DataFrame,
    care: pd.DataFrame,
    k: int,
    max_words: Optional[int],
    source: str,
) -> pd.Series:
    ensure_cols(chi, ["session_id", "file", "line_no", "utterance_clean"], "CHI", Path("<chi>"))
    ensure_cols(care, ["session_id", "file", "line_no", "utterance_clean"], "CARE", Path("<caretakers>"))

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
    care2["__row_id__"] = range(len(care2))
    chi2["__row_id__"] = -1  # unused

    combo = pd.concat([chi2, care2], ignore_index=True)

    combo["_sid_key"] = combo["session_id_num"].astype("Int64").astype(str)
    combo.loc[combo["session_id_num"].isna(), "_sid_key"] = "S:" + combo.loc[combo["session_id_num"].isna(), "session_id_str"]

    combo["_role_order"] = combo["_role"].map({"CARE": 0, "CHI": 1}).fillna(9).astype(int)

    combo = combo.sort_values(
        by=["_sid_key", "file_str", "line_no_num", "utt_id_num", "_role_order"],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)

    ctx_out = [""] * len(combo)
    current_sid = None
    hist: List[str] = []

    def can_contribute(role: str) -> bool:
        if source == "any":
            return True
        if source == "chi_only":
            return role == "CHI"
        if source == "care_only":
            return role == "CARE"
        return True

    for i, r in combo.iterrows():
        sid = r["_sid_key"]
        if sid != current_sid:
            current_sid = sid
            hist = []

        # assign context for CARE rows
        if r["_role"] == "CARE":
            ctx = concat_last_k(hist, k)
            if max_words and max_words > 0:
                toks = ctx.split()
                if len(toks) > max_words:
                    ctx = " ".join(toks[-max_words:])
            ctx_out[i] = ctx

        # update history
        if can_contribute(r["_role"]):
            txt = "" if pd.isna(r["utterance_clean"]) else str(r["utterance_clean"]).strip()
            if txt:
                hist.append(txt)

    combo["__ctx__"] = ctx_out

    care_ctx = combo.loc[combo["_role"] == "CARE", ["__row_id__", "__ctx__"]].sort_values("__row_id__")
    return care_ctx["__ctx__"].reset_index(drop=True)


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
    ap.add_argument("--K", type=int, default=1, help="Number of previous utts to concat (default 1).")
    ap.add_argument("--max-words", type=int, default=128, help="Keep last N words in context (0 disables).")
    ap.add_argument("--source", choices=["any", "chi_only", "care_only"], default="any",
                    help="Which utterances contribute to context history (default: any).")
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

        care_df, care_sep = read_table(care_path)
        chi_df, _ = read_table(chi_path)

        if (col_name in care_df.columns) and (not args.overwrite):
            print(f"[SKIP] {care_path} already has {col_name} (use --overwrite)")
            continue

        ctx = build_context_for_caretakers(chi_df, care_df, k=k, max_words=max_words, source=args.source)
        backup_once(care_path)
        care_df[col_name] = ctx
        care_df.to_csv(care_path, index=False, sep=care_sep)
        print(f"[OK] Wrote {col_name} -> {care_path}")

    print("DONE")


if __name__ == "__main__":
    main()

