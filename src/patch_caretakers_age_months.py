#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
patch_caretakers_age_months.py
==============================

Goal
----
Add/patch `age_months` for caretakers data using the child's `chi.csv` as source.

We assume: within a given (child_id, session_id), the child age is constant (or near).
So we compute session_age = median(age_months) over chi utterances in that session.

Patches
-------
(A) Raw caretakers CSVs (optional):
    data/<Dataset>/<Child>/caretakers.csv

(B) Scored caretakers CSVs (optional):
    results/raw_surprisal/{WITH_context,WITHOUT_context}/<base_llm>/<Dataset>/<Child>/caretakers__utterance_clean.scored.csv

Column placement
---------------
We insert age_months right AFTER `line_no` if possible.

Backups
-------
Creates timestamped backups alongside each file before overwriting:
  <file>.bak_YYYYmmdd_HHMMSS

Usage
-----
From repo root:
  python3 src/patch_caretakers_age_months.py --patch-raw --patch-scored

If you only want scored:
  python3 src/patch_caretakers_age_months.py --patch-scored

If you only want raw:
  python3 src/patch_caretakers_age_months.py --patch-raw
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import datetime as dt

import pandas as pd


# -----------------------------
# Project paths
# -----------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results" / "raw_surprisal"

DEFAULT_CONTEXTS = ["WITH_context", "WITHOUT_context"]
CARETAKERS_RAW_NAME = "caretakers.csv"
CHI_RAW_NAME = "chi.csv"
CARETAKERS_SCORED_NAME = "caretakers__utterance_clean.scored.csv"


# -----------------------------
# Helpers
# -----------------------------
def ts_str() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_file(path: Path) -> Path:
    bak = path.with_name(path.name + f".bak_{ts_str()}")
    bak.write_bytes(path.read_bytes())
    return bak


def atomic_write_csv(df: pd.DataFrame, out_path: Path) -> None:
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(out_path)


def insert_col_after(df: pd.DataFrame, after_col: str, new_col: str, values) -> pd.DataFrame:
    """
    Insert new_col after after_col if after_col exists.
    If after_col missing, append at end.
    If new_col already exists, overwrite values in-place without moving it.
    """
    if new_col in df.columns:
        df[new_col] = values
        return df

    cols = list(df.columns)
    if after_col in cols:
        i = cols.index(after_col) + 1
    else:
        i = len(cols)

    # Build new frame with inserted column
    left = cols[:i]
    right = cols[i:]
    out = df[left].copy()
    out[new_col] = values
    for c in right:
        out[c] = df[c].values
    return out


def read_chi_session_age_map(chi_csv: Path, reducer: str = "median") -> Dict[int, float]:
    """
    Return dict: session_id(int) -> age_months(float)
    """
    if not chi_csv.exists():
        raise FileNotFoundError(f"Missing: {chi_csv}")

    usecols = None
    # try minimal read
    df = pd.read_csv(chi_csv, usecols=lambda c: c in {"session_id", "age_months"})
    if df.empty:
        return {}

    if "session_id" not in df.columns or "age_months" not in df.columns:
        raise ValueError(f"{chi_csv} must contain session_id and age_months")

    df["session_id"] = pd.to_numeric(df["session_id"], errors="coerce")
    df["age_months"] = pd.to_numeric(df["age_months"], errors="coerce")
    df = df.dropna(subset=["session_id", "age_months"])
    if df.empty:
        return {}

    df["session_id"] = df["session_id"].astype(int)

    g = df.groupby("session_id", sort=False)["age_months"]
    if reducer == "median":
        s = g.median()
    elif reducer == "mean":
        s = g.mean()
    elif reducer == "min":
        s = g.min()
    elif reducer == "max":
        s = g.max()
    elif reducer == "first":
        s = g.first()
    else:
        raise ValueError(f"Unknown reducer: {reducer}")

    return {int(k): float(v) for k, v in s.to_dict().items()}


@dataclass(frozen=True)
class ChildRef:
    dataset: str
    child: str
    child_dir: Path  # data/<Dataset>/<Child>


def iter_children(data_root: Path, datasets: Optional[List[str]] = None) -> Iterable[ChildRef]:
    if not data_root.exists():
        raise SystemExit(f"[ERROR] data_root not found: {data_root}")

    ds_dirs = [p for p in data_root.iterdir() if p.is_dir()]
    if datasets is not None:
        dset = set(datasets)
        ds_dirs = [p for p in ds_dirs if p.name in dset]

    for ds in sorted(ds_dirs, key=lambda p: p.name):
        for child_dir in sorted([p for p in ds.iterdir() if p.is_dir()], key=lambda p: p.name):
            yield ChildRef(dataset=ds.name, child=child_dir.name, child_dir=child_dir)


def patch_one_csv_add_age_months(
    csv_path: Path,
    session_age: Dict[int, float],
    strict: bool,
) -> Tuple[int, int]:
    """
    Patch a caretakers-like CSV by mapping session_id -> age_months.
    Returns: (rows_total, rows_missing_age)
    """
    df = pd.read_csv(csv_path)
    if df.empty:
        # still ensure column exists?
        return 0, 0

    if "session_id" not in df.columns:
        raise ValueError(f"{csv_path} missing session_id")

    sid = pd.to_numeric(df["session_id"], errors="coerce")
    sid_int = sid.astype("Int64")  # nullable integer

    ages = sid_int.map(lambda x: session_age.get(int(x), None) if pd.notna(x) else None)
    # ages is object dtype (floats/None), convert to float
    ages = pd.to_numeric(ages, errors="coerce")

    missing = int(ages.isna().sum())
    total = int(len(df))

    if strict and missing > 0:
        # show a few missing session_ids
        miss_sids = (
            df.loc[ages.isna(), "session_id"]
            .dropna()
            .astype(int, errors="ignore")
            .unique()
            .tolist()
        )
        raise RuntimeError(
            f"[STRICT] {csv_path}: {missing}/{total} rows missing age_months. "
            f"Missing session_ids (sample): {miss_sids[:10]}"
        )

    # insert after line_no if present, else just append/overwrite
    after_col = "line_no" if "line_no" in df.columns else "file"
    df2 = insert_col_after(df, after_col=after_col, new_col="age_months", values=ages)

    backup_file(csv_path)
    atomic_write_csv(df2, csv_path)

    return total, missing


def iter_scored_caretakers_files(
    results_root: Path,
    contexts: List[str],
    base_llms: Optional[List[str]],
    datasets: Optional[List[str]],
    children: Optional[List[str]],
) -> Iterable[Path]:
    """
    Yield paths like:
    results/raw_surprisal/WITH_context/<base>/<Dataset>/<Child>/caretakers__utterance_clean.scored.csv
    """
    if not results_root.exists():
        raise SystemExit(f"[ERROR] results_root not found: {results_root}")

    ctx_set = set(contexts)
    dset_set = set(datasets) if datasets is not None else None
    child_set = set(children) if children is not None else None
    base_set = set(base_llms) if base_llms is not None else None

    for ctx in contexts:
        ctx_dir = results_root / ctx
        if not ctx_dir.exists():
            continue
        for base_dir in sorted([p for p in ctx_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
            if base_set is not None and base_dir.name not in base_set:
                continue
            for ds_dir in sorted([p for p in base_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
                if dset_set is not None and ds_dir.name not in dset_set:
                    continue
                for child_dir in sorted([p for p in ds_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
                    if child_set is not None and child_dir.name not in child_set:
                        continue
                    f = child_dir / CARETAKERS_SCORED_NAME
                    if f.exists():
                        yield f


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    ap.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)

    ap.add_argument("--datasets", nargs="+", default=None, help="e.g. Brown Providence Manchester")
    ap.add_argument("--children", nargs="+", default=None, help="e.g. Adam Eve Sarah (optional filter)")

    ap.add_argument("--contexts", nargs="+", default=DEFAULT_CONTEXTS)
    ap.add_argument("--base-llms", nargs="+", default=None, help="e.g. mistralai__Mistral-7B-v0.3 (optional filter)")

    ap.add_argument("--patch-raw", action="store_true", help="Patch data/.../caretakers.csv")
    ap.add_argument("--patch-scored", action="store_true", help="Patch results/.../caretakers__utterance_clean.scored.csv")

    ap.add_argument("--reducer", choices=["median", "mean", "min", "max", "first"], default="median",
                    help="How to compute a single age_months per session_id from chi.csv")
    ap.add_argument("--strict", action="store_true",
                    help="If any caretakers rows can't be mapped to a session age, error out.")

    args = ap.parse_args(argv)

    if not args.patch_raw and not args.patch_scored:
        raise SystemExit("[ERROR] You must pass at least one of: --patch-raw, --patch-scored")

    # Limit child selection for raw traversal too
    child_filter = set(args.children) if args.children is not None else None

    # Precompute session-age maps per (dataset, child)
    session_maps: Dict[Tuple[str, str], Dict[int, float]] = {}

    def get_map(dataset: str, child: str) -> Dict[int, float]:
        key = (dataset, child)
        if key in session_maps:
            return session_maps[key]
        chi_path = args.data_root / dataset / child / CHI_RAW_NAME
        m = read_chi_session_age_map(chi_path, reducer=args.reducer)
        session_maps[key] = m
        return m

    patched_raw = 0
    patched_scored = 0
    missing_total_raw = 0
    missing_total_scored = 0

    # ---- Patch raw caretakers.csv in data/ ----
    if args.patch_raw:
        for cref in iter_children(args.data_root, datasets=args.datasets):
            if child_filter is not None and cref.child not in child_filter:
                continue

            caret_path = cref.child_dir / CARETAKERS_RAW_NAME
            if not caret_path.exists():
                continue

            sess_map = get_map(cref.dataset, cref.child)
            if not sess_map:
                print(f"[WARN] No session-age map for {cref.dataset}/{cref.child} (chi.csv empty?) -> skipping raw")
                continue

            try:
                total, missing = patch_one_csv_add_age_months(caret_path, sess_map, strict=args.strict)
            except Exception as e:
                raise SystemExit(f"[ERROR] raw patch failed for {caret_path}: {e}")

            patched_raw += 1
            missing_total_raw += missing
            print(f"[OK] raw patched: {caret_path}  (rows={total}, missing_age={missing})")

    # ---- Patch scored caretakers__utterance_clean.scored.csv in results/ ----
    if args.patch_scored:
        # We need dataset/child to find the chi.csv map.
        # We infer dataset/child from the scored file path segments.
        for scored_path in iter_scored_caretakers_files(
            args.results_root,
            contexts=args.contexts,
            base_llms=args.base_llms,
            datasets=args.datasets,
            children=args.children,
        ):
            # .../<ctx>/<base>/<Dataset>/<Child>/caretakers__utterance_clean.scored.csv
            parts = scored_path.parts
            # robust extraction: dataset is parent.parent.name, child is parent.name
            child = scored_path.parent.name
            dataset = scored_path.parent.parent.name

            sess_map = get_map(dataset, child)
            if not sess_map:
                print(f"[WARN] No session-age map for {dataset}/{child} -> skipping scored {scored_path}")
                continue

            try:
                total, missing = patch_one_csv_add_age_months(scored_path, sess_map, strict=args.strict)
            except Exception as e:
                raise SystemExit(f"[ERROR] scored patch failed for {scored_path}: {e}")

            patched_scored += 1
            missing_total_scored += missing
            print(f"[OK] scored patched: {scored_path}  (rows={total}, missing_age={missing})")

    print("\n[SUMMARY]")
    print(f"  raw patched files:    {patched_raw}")
    print(f"  scored patched files: {patched_scored}")
    print(f"  raw missing ages total:    {missing_total_raw}")
    print(f"  scored missing ages total: {missing_total_scored}")
    print("Done.")


if __name__ == "__main__":
    main()

