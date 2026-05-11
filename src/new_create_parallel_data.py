#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_INPUT_ROOT = PROJECT_ROOT / "new_clean_slurm"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "parallel_dataset_new"
VALID_DATASETS = ("Brown", "Manchester", "Providence")
VALID_BINS = (3, 6, 12)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Create sharded parallel datasets directly from new_clean_slurm/<Dataset>/<Child>/"
            "{chi.csv, caretakers.csv}."
        )
    )
    p.add_argument(
        "--input-root",
        type=Path,
        default=DEFAULT_INPUT_ROOT,
        help=f"Root containing Brown/Manchester/Providence child folders (default: {DEFAULT_INPUT_ROOT})",
    )
    p.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=(
            f"Where to write sharded subsets (default: {DEFAULT_OUTPUT_ROOT}). "
            "This defaults to a NEW root on purpose so you do not clobber the old parallel_dataset."
        ),
    )
    p.add_argument(
        "--dataset",
        default="ALL",
        help="Brown | Manchester | Providence | ALL (default: ALL)",
    )
    p.add_argument(
        "--child",
        default="total",
        help="Child name or 'total' (default: total)",
    )
    p.add_argument(
        "--bins",
        nargs="+",
        type=int,
        default=[6],
        choices=VALID_BINS,
        help="Synthetic bins to export if the corresponding columns exist (default: 6)",
    )
    p.add_argument(
        "--chunk-size",
        type=int,
        default=20_000,
        help="Rows per shard (default: 20000)",
    )
    p.add_argument(
        "--drop-empty-text",
        action="store_true",
        help="Drop rows whose utterance_for_scoring is empty after stripping whitespace.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove an existing subset folder before rewriting it.",
    )
    return p


def iter_child_dirs(root: Path, dataset: str, child: str) -> List[Tuple[str, Path]]:
    if not root.exists():
        raise FileNotFoundError(f"Input root not found: {root}")

    if dataset == "ALL":
        dataset_names = [p.name for p in root.iterdir() if p.is_dir() and p.name != "filelists"]
    else:
        dataset_names = [dataset]

    out: List[Tuple[str, Path]] = []
    for ds in sorted(dataset_names):
        ds_dir = root / ds
        if not ds_dir.exists():
            continue
        if child == "total":
            child_dirs = [p for p in ds_dir.iterdir() if p.is_dir()]
        else:
            child_dirs = [ds_dir / child]
        for ch_dir in sorted(child_dirs, key=lambda p: p.name):
            if ch_dir.exists() and ch_dir.is_dir():
                out.append((ds, ch_dir))
    return out


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path)


def ensure_cols(df: pd.DataFrame, cols: Sequence[str], where: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"{where} missing required columns: {missing}")


def stable_sort(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for src, tmp in [("session_id", "_session_id_num"), ("line_no", "_line_no_num"), ("utt_id", "_utt_id_num")]:
        out[tmp] = pd.to_numeric(out.get(src), errors="coerce")
    sort_cols = [c for c in ["_session_id_num", "file", "_line_no_num", "_utt_id_num"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols, kind="stable").reset_index(drop=True)
    drop_cols = [c for c in ["_session_id_num", "_line_no_num", "_utt_id_num"] if c in out.columns]
    return out.drop(columns=drop_cols)


def text_or_empty(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()


def count_words(text: str) -> int:
    return len([tok for tok in text.split() if tok])


def coerce_int_like(x) -> str:
    if pd.isna(x):
        return ""
    return str(x)


def numeric_or_blank(x, fallback: Optional[int] = None) -> int | str:
    v = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    if pd.notna(v):
        return int(v)
    if fallback is not None:
        return int(fallback)
    return ""


def base_record(
    *,
    dataset: str,
    child_id: str,
    subset: str,
    source_csv: str,
    source_text_col: str,
    source_row: int,
    row: pd.Series,
    scoring_text: str,
    speaker: str,
    utt_id_role: str,
    morph_fallback_to_words: bool,
) -> Dict[str, object]:
    word_count = count_words(scoring_text) if scoring_text else 0
    morph_fallback = word_count if morph_fallback_to_words else None
    morph_count = numeric_or_blank(row.get("morph_count"), fallback=morph_fallback)

    return {
        "dataset": dataset,
        "child_id": child_id,
        "subset": subset,
        "session_id": coerce_int_like(row.get("session_id")),
        "age_months": row.get("age_months", ""),
        "file": text_or_empty(row.get("file")),
        "line_no": coerce_int_like(row.get("line_no")),
        "utt_id": coerce_int_like(row.get("utt_id")),
        "utt_id_role": utt_id_role,
        "speaker": speaker,
        "source_csv": source_csv,
        "source_text_col": source_text_col,
        "source_row": source_row,
        "word_count": word_count,
        "morph_count": morph_count,
        "context_k1": text_or_empty(row.get("context_k1")),
        "context_k2": text_or_empty(row.get("context_k2")),
        "context_k3": text_or_empty(row.get("context_k3")),
        "utterance_for_scoring": scoring_text,
    }


def build_real_subset(
    *,
    dataset: str,
    child_id: str,
    df: pd.DataFrame,
    subset: str,
    source_csv: str,
    speaker_col: Optional[str] = None,
    utt_id_role_col: Optional[str] = None,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    text_col = "utterance_clean" if "utterance_clean" in df.columns else "utterance"

    for idx, row in enumerate(df.itertuples(index=False), start=1):
        s = pd.Series(row._asdict())
        rows.append(
            base_record(
                dataset=dataset,
                child_id=child_id,
                subset=subset,
                source_csv=source_csv,
                source_text_col=text_col,
                source_row=idx,
                row=s,
                scoring_text=text_or_empty(s.get(text_col)),
                speaker=text_or_empty(s.get(speaker_col)) if speaker_col else "",
                utt_id_role=text_or_empty(s.get(utt_id_role_col)) if utt_id_role_col else "",
                morph_fallback_to_words=False,
            )
        )
    return rows


def build_variant_subset(
    *,
    dataset: str,
    child_id: str,
    df: pd.DataFrame,
    subset: str,
    variant_col: str,
    source_csv: str,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        s = pd.Series(row._asdict())
        rows.append(
            base_record(
                dataset=dataset,
                child_id=child_id,
                subset=subset,
                source_csv=source_csv,
                source_text_col=variant_col,
                source_row=idx,
                row=s,
                scoring_text=text_or_empty(s.get(variant_col)),
                speaker="",
                utt_id_role="",
                morph_fallback_to_words=True,
            )
        )
    return rows


def shard_write(folder: Path, prefix: str, rows: List[Dict[str, object]], chunk_size: int) -> List[Path]:
    shards_dir = folder / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    columns = [
        "dataset", "child_id", "subset",
        "session_id", "age_months", "file", "line_no",
        "utt_id", "utt_id_role", "speaker",
        "source_csv", "source_text_col", "source_row",
        "word_count", "morph_count",
        "context_k1", "context_k2", "context_k3",
        "utterance_for_scoring",
    ]

    paths: List[Path] = []
    for part_idx, start in enumerate(range(0, len(rows), chunk_size), start=1):
        chunk = rows[start:start + chunk_size]
        out_path = shards_dir / f"{prefix}__part{part_idx:05d}.csv"
        pd.DataFrame(chunk, columns=columns).to_csv(out_path, index=False)
        paths.append(out_path)
    return paths


def write_subset(
    *,
    folder: Path,
    subset_path: str,
    rows: List[Dict[str, object]],
    chunk_size: int,
    overwrite: bool,
    source_file: str,
    variant_col: Optional[str] = None,
    drop_empty_text: bool,
) -> None:
    if drop_empty_text:
        rows = [r for r in rows if text_or_empty(r.get("utterance_for_scoring"))]

    if folder.exists():
        if not overwrite:
            raise FileExistsError(
                f"Output subset already exists: {folder}\n"
                f"Re-run with --overwrite if you want to replace it."
            )
        shutil.rmtree(folder)

    folder.mkdir(parents=True, exist_ok=True)
    prefix = subset_path.replace("/", "__")
    shard_paths = shard_write(folder, prefix, rows, chunk_size) if rows else []

    manifest = {
        "subset": subset_path,
        "n_rows": len(rows),
        "chunk_size": chunk_size,
        "n_shards": len(shard_paths),
        "shards": [str(p.relative_to(folder)) for p in shard_paths],
        "source_file": source_file,
        "variant_col": variant_col,
        "context_columns": ["context_k1", "context_k2", "context_k3"],
        "drop_empty_text": bool(drop_empty_text),
    }
    with (folder / "manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)

    input_root = args.input_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    chunk_size = int(args.chunk_size)
    if chunk_size <= 0:
        raise SystemExit("[ERROR] --chunk-size must be > 0")

    child_dirs = iter_child_dirs(input_root, args.dataset, args.child)
    if not child_dirs:
        raise SystemExit("[ERROR] No matching child directories found.")

    for dataset, child_dir in child_dirs:
        child_id = child_dir.name
        chi_path = child_dir / "chi.csv"
        care_path = child_dir / "caretakers.csv"

        if not chi_path.exists() or not care_path.exists():
            print(f"[WARN] Skipping {dataset}/{child_id}: missing chi.csv or caretakers.csv")
            continue

        chi_df = stable_sort(read_csv(chi_path))
        care_df = stable_sort(read_csv(care_path))

        ensure_cols(
            chi_df,
            ["session_id", "file", "line_no", "utt_id", "age_months", "context_k1", "context_k2", "context_k3"],
            str(chi_path),
        )
        ensure_cols(
            care_df,
            ["session_id", "file", "line_no", "utt_id", "age_months", "context_k1", "context_k2", "context_k3"],
            str(care_path),
        )

        subsets: List[Tuple[str, List[Dict[str, object]], str, Optional[str]]] = []
        subsets.append(
            (
                "chi",
                build_real_subset(
                    dataset=dataset,
                    child_id=child_id,
                    df=chi_df,
                    subset="chi",
                    source_csv="chi.csv",
                ),
                "chi.csv",
                None,
            )
        )
        subsets.append(
            (
                "caretakers",
                build_real_subset(
                    dataset=dataset,
                    child_id=child_id,
                    df=care_df,
                    subset="caretakers",
                    source_csv="caretakers.csv",
                    speaker_col="speaker",
                    utt_id_role_col="utt_id_role",
                ),
                "caretakers.csv",
                None,
            )
        )

        for b in args.bins:
            for prefix, col in [
                ("random_chi", f"random_model_utterance_bin{b}"),
                ("unigram_chi", f"unigram_model_utterance_bin{b}"),
                ("bigram_chi", f"bigram_model_utterance_bin{b}"),
            ]:
                if col not in chi_df.columns:
                    print(f"[WARN] {dataset}/{child_id}: missing column '{col}' -> skipping {prefix}/bin{b}")
                    continue
                subsets.append(
                    (
                        f"{prefix}/bin{b}",
                        build_variant_subset(
                            dataset=dataset,
                            child_id=child_id,
                            df=chi_df,
                            subset=f"{prefix}/bin{b}",
                            variant_col=col,
                            source_csv="chi.csv",
                        ),
                        "chi.csv",
                        col,
                    )
                )

        print(f"\n==> {dataset}/{child_id}")
        for subset_path, rows, source_file, variant_col in subsets:
            folder = output_root / dataset / child_id / subset_path
            write_subset(
                folder=folder,
                subset_path=subset_path,
                rows=rows,
                chunk_size=chunk_size,
                overwrite=bool(args.overwrite),
                source_file=source_file,
                variant_col=variant_col,
                drop_empty_text=bool(args.drop_empty_text),
            )
            print(f"  [OK] {subset_path}: {len(rows)} rows")

    print("\nDone.")


if __name__ == "__main__":
    main()
