#!/usr/bin/env python3
"""Create a PBM-only early-age baseline rescoring bundle.

This is for the 2026-05-26 decision to rescore only the generated random,
unigram, bigram, and trigram child baselines for Brown, Manchester, and
Providence utterances whose floored child age is 006 through 023 months. Later
bins can keep already-scored outputs because their additive n-gram
distributions are unchanged.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import tarfile
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "big_cleaned_dataset"
    / "default_naturalistic_merged_006_023"
    / "preprocessed_data"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "results" / "rescoring_subsets" / "pbm_006_023_merged_early_baselines"
DEFAULT_TAR_GZ = (
    PROJECT_ROOT
    / "results"
    / "scoring_bundles"
    / "pbm_006_023_merged_early_baselines_rescoring_2026-05-26.tar.gz"
)
DEFAULT_DATASETS = ("Brown", "Manchester", "Providence")
DEFAULT_VARIANTS = ("random", "unigram", "bigram", "trigram")

VARIANT_COLUMNS = {
    "random": "random_model_utterance_bin6",
    "unigram": "unigram_model_utterance_bin6",
    "bigram": "bigram_model_utterance_bin6",
    "trigram": "trigram_model_utterance_bin6",
}

OUTPUT_COLUMNS = [
    "dataset",
    "child_id",
    "subset",
    "session_id",
    "age_months",
    "age_floor_month",
    "age_bin_rescore",
    "file",
    "line_no",
    "utt_id",
    "source_csv",
    "source_text_col",
    "source_row",
    "word_count",
    "morph_count",
    "context_k1",
    "context_k2",
    "context_k3",
    "utterance_for_scoring",
]


def text_or_empty(value: object) -> str:
    """Return a stripped string without None artifacts."""
    if value is None:
        return ""
    return str(value).strip()


def floor_age_month(age_months: object) -> Optional[int]:
    """Return floor(age_months), or None when age is blank/invalid."""
    try:
        age = float(text_or_empty(age_months))
    except ValueError:
        return None
    if math.isnan(age):
        return None
    return int(math.floor(age))


def age_is_in_floor_range(age_months: object, *, min_month: int, max_month: int) -> bool:
    """Return true when floor(age_months) is within the inclusive month range."""
    month = floor_age_month(age_months)
    return month is not None and min_month <= month <= max_month


def count_words(text: object) -> int:
    """Count whitespace-delimited words in a cleaned/generated utterance."""
    return len([token for token in text_or_empty(text).split() if token])


def iter_child_scoring_files(input_root: Path, datasets: Sequence[str]) -> Iterable[Tuple[str, str, Path]]:
    """Yield dataset, child_id, child scoring CSV path for selected datasets."""
    for dataset in datasets:
        dataset_dir = input_root / dataset
        if not dataset_dir.exists():
            continue
        for child_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
            path = child_dir / "chi.surprisal_scoring.csv"
            if path.exists():
                yield dataset, child_dir.name, path


def build_variant_row(
    *,
    dataset: str,
    child_id: str,
    source_row: Mapping[str, str],
    source_row_number: int,
    variant: str,
    variant_column: str,
    source_csv: str,
    age_bin_label: str,
) -> Optional[Dict[str, str]]:
    """Build one scorer-compatible row for one generated baseline variant."""
    utterance = text_or_empty(source_row.get(variant_column, ""))
    if not utterance:
        return None
    word_count = count_words(utterance)
    if word_count <= 0:
        return None
    age_floor = floor_age_month(source_row.get("age_months", ""))
    return {
        "dataset": dataset,
        "child_id": child_id,
        "subset": f"{variant}_chi/bin6",
        "session_id": text_or_empty(source_row.get("session_id", "")),
        "age_months": text_or_empty(source_row.get("age_months", "")),
        "age_floor_month": "" if age_floor is None else str(age_floor),
        "age_bin_rescore": age_bin_label,
        "file": text_or_empty(source_row.get("file", "")),
        "line_no": text_or_empty(source_row.get("line_no", "")),
        "utt_id": text_or_empty(source_row.get("utt_id", "")),
        "source_csv": source_csv,
        "source_text_col": variant_column,
        "source_row": str(source_row_number),
        "word_count": str(word_count),
        "morph_count": str(word_count),
        "context_k1": text_or_empty(source_row.get("context_k1", "")),
        "context_k2": text_or_empty(source_row.get("context_k2", "")),
        "context_k3": text_or_empty(source_row.get("context_k3", "")),
        "utterance_for_scoring": utterance,
    }


def read_variant_rows(
    path: Path,
    *,
    dataset: str,
    child_id: str,
    variant: str,
    min_month: int,
    max_month: int,
    source_csv: str = "chi.surprisal_scoring.csv",
) -> List[Dict[str, str]]:
    """Read one child scoring CSV and return rows for one generated variant."""
    if variant not in VARIANT_COLUMNS:
        raise ValueError(f"Unknown variant: {variant}")
    variant_column = VARIANT_COLUMNS[variant]
    age_bin_label = f"{min_month:03d}-{max_month:03d}"
    rows: List[Dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return rows
        if variant_column not in reader.fieldnames:
            raise KeyError(f"{path} missing required column {variant_column!r}")
        for source_row_number, row in enumerate(reader, start=2):
            if not age_is_in_floor_range(row.get("age_months", ""), min_month=min_month, max_month=max_month):
                continue
            out = build_variant_row(
                dataset=dataset,
                child_id=child_id,
                source_row=row,
                source_row_number=source_row_number,
                variant=variant,
                variant_column=variant_column,
                source_csv=source_csv,
                age_bin_label=age_bin_label,
            )
            if out is not None:
                rows.append(out)
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, str]], columns: Sequence[str] = OUTPUT_COLUMNS) -> None:
    """Write exact-schema quoted CSV rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(columns),
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_shards(
    output_root: Path,
    *,
    subset: str,
    rows: Sequence[Mapping[str, str]],
    chunk_size: int,
) -> List[Path]:
    """Write rows to subset shards and return created paths."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    shard_dir = output_root / subset / "shards"
    paths: List[Path] = []
    prefix = subset.replace("/", "__")
    for shard_index, start in enumerate(range(0, len(rows), chunk_size), start=1):
        chunk = rows[start : start + chunk_size]
        path = shard_dir / f"{prefix}__part{shard_index:05d}.csv"
        write_csv(path, chunk)
        paths.append(path)
    if not rows:
        write_csv(shard_dir / f"{prefix}__part00001.csv", [])
        paths.append(shard_dir / f"{prefix}__part00001.csv")
    return paths


def validate_csv_widths(paths: Iterable[Path]) -> List[str]:
    """Return row-width/header issues for generated CSV files."""
    issues: List[str] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                issues.append(f"{path}: empty file")
                continue
            if any(not column for column in header):
                issues.append(f"{path}: blank header")
            width = len(header)
            for line_number, row in enumerate(reader, start=2):
                if len(row) != width:
                    issues.append(f"{path}: row {line_number} has width {len(row)} not {width}")
                    break
    return issues


def write_readme(
    output_root: Path,
    *,
    input_root: Path,
    datasets: Sequence[str],
    variants: Sequence[str],
    min_month: int,
    max_month: int,
    chunk_size: int,
    total_rows: int,
) -> None:
    """Write a short README describing the rescoring subset."""
    text = f"""# PBM Early Baseline Rescoring Bundle

This folder contains only generated child-baseline utterances that need
rescoring after merging the early vocabulary/count bin to `006-023`.

- Source: `{input_root}`
- Datasets: {", ".join(datasets)}
- Variants: {", ".join(f"{variant}_chi/bin6" for variant in variants)}
- Age filter: floor(`age_months`) from `{min_month:03d}` through `{max_month:03d}`, inclusive
- Rows: {total_rows:,}
- Chunk size: {chunk_size:,}

The rows are scorer-compatible with `src/new_score_utterances.py`. Use
`utterance_for_scoring` as the text column and one of `context_k1`, `context_k2`,
or `context_k3` as the context column. For no-context scoring, omit
`--context-col`.

Rows for age `024+` are intentionally excluded because their additive
random/unigram/bigram/trigram distributions are unchanged from the previous PBM
run.
"""
    (output_root / "README.md").write_text(text, encoding="utf-8")


def create_bundle(
    *,
    input_root: Path = DEFAULT_INPUT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    datasets: Sequence[str] = DEFAULT_DATASETS,
    variants: Sequence[str] = DEFAULT_VARIANTS,
    min_month: int = 6,
    max_month: int = 23,
    chunk_size: int = 20_000,
    overwrite: bool = False,
    tar_gz: Optional[Path] = None,
) -> Dict[str, object]:
    """Create the PBM early generated-baseline rescoring bundle."""
    if output_root.exists():
        if not overwrite:
            raise FileExistsError(f"Output root already exists: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    child_files = list(iter_child_scoring_files(input_root, datasets))
    if not child_files:
        raise FileNotFoundError(f"No child scoring CSVs found under {input_root} for {datasets}")

    manifest_rows: List[Dict[str, str]] = []
    counts_by_dataset_child: Dict[Tuple[str, str], int] = {}
    all_shards: List[Path] = []
    total_rows = 0

    for variant in variants:
        if variant not in VARIANT_COLUMNS:
            raise ValueError(f"Unknown variant: {variant}")
        variant_rows: List[Dict[str, str]] = []
        per_child_counts: Dict[Tuple[str, str], int] = {}
        for dataset, child_id, path in child_files:
            rows = read_variant_rows(
                path,
                dataset=dataset,
                child_id=child_id,
                variant=variant,
                min_month=min_month,
                max_month=max_month,
            )
            variant_rows.extend(rows)
            per_child_counts[(dataset, child_id)] = len(rows)
            counts_by_dataset_child[(dataset, child_id)] = counts_by_dataset_child.get((dataset, child_id), 0) + len(rows)

        subset = f"{variant}_chi/bin6"
        shard_paths = write_shards(output_root, subset=subset, rows=variant_rows, chunk_size=chunk_size)
        all_shards.extend(shard_paths)
        total_rows += len(variant_rows)
        manifest_rows.append(
            {
                "subset": subset,
                "variant": variant,
                "variant_column": VARIANT_COLUMNS[variant],
                "n_rows": str(len(variant_rows)),
                "n_shards": str(len(shard_paths)),
                "chunk_size": str(chunk_size),
                "age_floor_min_month": str(min_month),
                "age_floor_max_month": str(max_month),
                "shards": json.dumps([str(path.relative_to(output_root)) for path in shard_paths], ensure_ascii=False),
            }
        )

        child_count_rows = [
            {
                "dataset": dataset,
                "child_id": child_id,
                "subset": subset,
                "n_rows": str(n_rows),
            }
            for (dataset, child_id), n_rows in sorted(per_child_counts.items())
        ]
        write_csv(
            output_root / subset / "row_counts_by_child.csv",
            child_count_rows,
            columns=["dataset", "child_id", "subset", "n_rows"],
        )

    write_csv(
        output_root / "manifest.csv",
        manifest_rows,
        columns=[
            "subset",
            "variant",
            "variant_column",
            "n_rows",
            "n_shards",
            "chunk_size",
            "age_floor_min_month",
            "age_floor_max_month",
            "shards",
        ],
    )

    combined_count_rows = [
        {
            "dataset": dataset,
            "child_id": child_id,
            "n_variant_rows_total": str(n_rows),
        }
        for (dataset, child_id), n_rows in sorted(counts_by_dataset_child.items())
    ]
    write_csv(
        output_root / "row_counts_by_dataset_child.csv",
        combined_count_rows,
        columns=["dataset", "child_id", "n_variant_rows_total"],
    )
    write_readme(
        output_root,
        input_root=input_root,
        datasets=datasets,
        variants=variants,
        min_month=min_month,
        max_month=max_month,
        chunk_size=chunk_size,
        total_rows=total_rows,
    )

    issues = validate_csv_widths([output_root / "manifest.csv", output_root / "row_counts_by_dataset_child.csv", *all_shards])
    if issues:
        raise RuntimeError("CSV validation failed:\n" + "\n".join(issues[:20]))

    if tar_gz is not None:
        tar_gz.parent.mkdir(parents=True, exist_ok=True)
        if tar_gz.exists():
            tar_gz.unlink()
        with tarfile.open(tar_gz, "w:gz") as tar:
            tar.add(output_root, arcname=output_root.name)

    return {
        "output_root": str(output_root),
        "tar_gz": "" if tar_gz is None else str(tar_gz),
        "n_child_files": len(child_files),
        "n_rows": total_rows,
        "n_shards": len(all_shards),
        "manifest": str(output_root / "manifest.csv"),
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS))
    parser.add_argument("--variants", nargs="+", choices=sorted(VARIANT_COLUMNS), default=list(DEFAULT_VARIANTS))
    parser.add_argument("--min-month", type=int, default=6)
    parser.add_argument("--max-month", type=int, default=23)
    parser.add_argument("--chunk-size", type=int, default=20_000)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--tar-gz", type=Path, default=DEFAULT_TAR_GZ)
    parser.add_argument("--no-tar", action="store_true", help="Do not create a tar.gz archive.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entry point."""
    args = parse_args(argv)
    summary = create_bundle(
        input_root=args.input_root,
        output_root=args.output_root,
        datasets=args.datasets,
        variants=args.variants,
        min_month=args.min_month,
        max_month=args.max_month,
        chunk_size=args.chunk_size,
        overwrite=bool(args.overwrite),
        tar_gz=None if args.no_tar else args.tar_gz,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
