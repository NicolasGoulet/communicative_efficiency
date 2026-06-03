#!/usr/bin/env python3
"""Merge Providence/Naima 030000 generated-baseline patch scores into a full tree.

Default behavior is a dry run that writes an audit report.  Use ``--apply`` to
update the full scored tree in place.  The script only touches these exact
generated-baseline outputs:

    Providence/Naima/chi.surprisal_scoring__{random,unigram,bigram,trigram}.scored.csv
    contexts k0, k1, k2, k3

Rows are matched by dataset, child_id, file, line_no, and utt_id.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd


MODEL_SLUG = "mistralai__Mistral-7B-v0.3"
DATASET = "Providence"
CHILD = "Naima"
INPUT_STEM = "chi.surprisal_scoring"
TARGET_FILE = "Naima/030000.cha"
KEY_COLUMNS = ("dataset", "child_id", "file", "line_no", "utt_id")
MODES = {
    "random": "random_model_utterance_bin6",
    "unigram": "unigram_model_utterance_bin6",
    "bigram": "bigram_model_utterance_bin6",
    "trigram": "trigram_model_utterance_bin6",
}
CONTEXTS = {
    "k0": ("WITHOUT_context", "k0"),
    "k1": ("WITH_context", "k1"),
    "k2": ("WITH_context", "k2"),
    "k3": ("WITH_context", "k3"),
}
SCORE_COLUMNS = (
    "mean_bits_per_token",
    "sum_bits",
    "n_eval_tokens",
    "model_used",
    "units_used",
    "text_cols_used",
    "context_col_used",
    "skip_zero_counts",
    "word_count_col_used",
    "morph_count_col_used",
    "min_word_count",
    "min_morph_count",
    "max_rows_used",
)


@dataclass(frozen=True)
class MergeAuditRow:
    context_k: str
    mode: str
    patch_csv: str
    full_csv: str
    patch_rows: int
    full_rows: int
    matched_rows: int
    duplicate_patch_keys: int
    duplicate_full_keys: int
    missing_in_full: int
    patch_blank_target_rows: int
    patch_missing_sum_bits_rows: int
    patch_zero_eval_token_rows: int
    applied: bool


def scored_path(root: Path, context_k: str, mode: str) -> Path:
    context_dir, label = CONTEXTS[context_k]
    return (
        root
        / context_dir
        / label
        / MODEL_SLUG
        / DATASET
        / CHILD
        / f"{INPUT_STEM}__{mode}.scored.csv"
    )


def key_frame(df: pd.DataFrame) -> pd.Series:
    return df.loc[:, list(KEY_COLUMNS)].astype(str).agg("\u241f".join, axis=1)


def columns_to_copy(patch: pd.DataFrame, target_col: str) -> list[str]:
    cols = [target_col]
    cols.extend(column for column in SCORE_COLUMNS if column in patch.columns)
    cols.extend(column for column in patch.columns if column.startswith("token_"))
    return cols


def merge_one(
    *,
    full_root: Path,
    patch_root: Path,
    context_k: str,
    mode: str,
    apply: bool,
    backup_root: Path | None,
) -> MergeAuditRow:
    target_col = MODES[mode]
    patch_csv = scored_path(patch_root, context_k, mode)
    full_csv = scored_path(full_root, context_k, mode)
    if not patch_csv.is_file():
        raise FileNotFoundError(f"Patch score CSV not found: {patch_csv}")
    if not full_csv.is_file():
        raise FileNotFoundError(f"Full score CSV not found: {full_csv}")

    patch = pd.read_csv(patch_csv, dtype=str, keep_default_na=False, low_memory=False)
    full = pd.read_csv(full_csv, dtype=str, keep_default_na=False, low_memory=False)

    patch = patch[patch["file"].eq(TARGET_FILE)].copy()
    duplicate_patch = int(patch.duplicated(list(KEY_COLUMNS)).sum())
    duplicate_full = int(full.duplicated(list(KEY_COLUMNS)).sum())

    patch_keys = key_frame(patch)
    full_keys = key_frame(full)
    full_index_by_key = {key: idx for idx, key in full_keys.items()}
    missing_keys = [key for key in patch_keys if key not in full_index_by_key]

    patch_blank_target = int(patch[target_col].fillna("").astype(str).str.strip().eq("").sum())
    patch_missing_sum = int(patch["sum_bits"].fillna("").astype(str).str.strip().eq("").sum())
    patch_zero_eval = int(pd.to_numeric(patch["n_eval_tokens"], errors="coerce").fillna(0).eq(0).sum())

    matched_rows = len(patch) - len(missing_keys)
    if apply:
        if duplicate_patch or duplicate_full or missing_keys or patch_blank_target or patch_missing_sum or patch_zero_eval:
            raise ValueError(
                "Refusing to apply unsafe patch: "
                f"duplicate_patch={duplicate_patch}, duplicate_full={duplicate_full}, "
                f"missing={len(missing_keys)}, blank_target={patch_blank_target}, "
                f"missing_sum={patch_missing_sum}, zero_eval={patch_zero_eval}"
            )

        if backup_root is not None:
            backup_path = backup_root / full_csv.relative_to(full_root)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_csv, backup_path)

        copy_cols = columns_to_copy(patch, target_col)
        patch_by_key = patch.assign(_merge_key=patch_keys).set_index("_merge_key")
        for key in patch_keys:
            full_idx = full_index_by_key[key]
            for column in copy_cols:
                if column not in full.columns:
                    full[column] = ""
                full.at[full_idx, column] = patch_by_key.at[key, column]
        full.to_csv(full_csv, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

    return MergeAuditRow(
        context_k=context_k,
        mode=mode,
        patch_csv=str(patch_csv),
        full_csv=str(full_csv),
        patch_rows=len(patch),
        full_rows=len(full),
        matched_rows=matched_rows,
        duplicate_patch_keys=duplicate_patch,
        duplicate_full_keys=duplicate_full,
        missing_in_full=len(missing_keys),
        patch_blank_target_rows=patch_blank_target,
        patch_missing_sum_bits_rows=patch_missing_sum,
        patch_zero_eval_token_rows=patch_zero_eval,
        applied=apply,
    )


def write_report(path: Path, rows: Sequence[MergeAuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0])), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-root",
        type=Path,
        default=Path("mila_results/raw_surprisal_cleaned_patched_006_023"),
        help="Full scored tree to patch.",
    )
    parser.add_argument(
        "--patch-root",
        type=Path,
        default=Path("results/raw_surprisal_cleaned_naima_030000_missing_baselines_patch"),
        help="Patch scored tree produced by score_naima_030000_missing_baselines_local.sh.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/audits/naima_030000_missing_baseline_merge.csv"),
    )
    parser.add_argument("--backup-root", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    full_root = args.full_root.expanduser().resolve()
    patch_root = args.patch_root.expanduser().resolve()
    backup_root = args.backup_root.expanduser().resolve() if args.backup_root else None

    rows: list[MergeAuditRow] = []
    for context_k in CONTEXTS:
        for mode in MODES:
            rows.append(
                merge_one(
                    full_root=full_root,
                    patch_root=patch_root,
                    context_k=context_k,
                    mode=mode,
                    apply=bool(args.apply),
                    backup_root=backup_root,
                )
            )
    write_report(args.report.expanduser().resolve(), rows)

    problem_total = sum(
        row.duplicate_patch_keys
        + row.duplicate_full_keys
        + row.missing_in_full
        + row.patch_blank_target_rows
        + row.patch_missing_sum_bits_rows
        + row.patch_zero_eval_token_rows
        for row in rows
    )
    print(f"[OK] Wrote audit report: {args.report}")
    print(f"[OK] Rows checked: {sum(row.patch_rows for row in rows)} patch score rows across {len(rows)} files")
    print(f"[OK] Problem count: {problem_total}")
    if problem_total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
