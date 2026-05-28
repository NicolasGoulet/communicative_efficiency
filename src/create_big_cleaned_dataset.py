#!/usr/bin/env python3
"""
Build a consolidated cleaned dataset with generated baseline utterances.

The output folder is intentionally separate from data/preprocessed_data. It
copies the Stage 0 cleaned child/caretaker CSVs for the selected datasets, then
builds additive n-gram dictionaries, generates matched-length random/unigram/
bigram/trigram child baselines, creates shared caretaker-context windows, and
writes compact surprisal-scoring CSVs.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from add_random_and_unigram_utterances import process as generate_ngram_utterances
from build_age_word_dicts import ChildUnit, build_dicts, iter_child_units
from create_minimal_surprisal_scoring_csvs import write_scoring_files_for_units
from create_shared_caretaker_contexts import write_context_files_for_units
from custom_age_bins import AgeBin, floor_age_month, make_merged_early_bins, make_threshold_early_bins


DEFAULT_GROUPING_CSV = Path("results/corpus_groups/dataset_group_assignments.csv")
DEFAULT_SOURCE_DATA_DIR = Path("data/preprocessed_data")
DEFAULT_OUTPUT_ROOT = Path("data/big_cleaned_dataset/default_naturalistic_bin6")
BASE_STAGE0_FILENAMES = ("chi.csv", "caretakers.csv")
GENERATED_FILENAME = "chi.ngram_generated.csv"
CHILD_CONTEXT_FILENAME = "chi.shared_caretaker_contexts.csv"
CARETAKER_CONTEXT_FILENAME = "caretakers.shared_caretaker_contexts.csv"
CHILD_SCORING_FILENAME = "chi.surprisal_scoring.csv"
CARETAKER_SCORING_FILENAME = "caretakers.surprisal_scoring.csv"
CHILD_BASELINE_COLUMNS = [
    "random_model_utterance_bin6",
    "unigram_model_utterance_bin6",
    "bigram_model_utterance_bin6",
    "trigram_model_utterance_bin6",
]
MANIFEST_COLUMNS = [
    "dataset",
    "child_id",
    "stage0_ready",
    "ngram_generated_ready",
    "child_context_ready",
    "caretaker_context_ready",
    "child_scoring_ready",
    "caretaker_scoring_ready",
    "scoring_ready",
    "chi_rows",
    "caretaker_rows",
    "child_scoring_rows",
    "caretaker_scoring_rows",
    "chi_csv",
    "caretakers_csv",
    "ngram_generated_csv",
    "child_context_csv",
    "caretaker_context_csv",
    "child_scoring_csv",
    "caretaker_scoring_csv",
]


def read_group_assignments(path: Path) -> Dict[str, Dict[str, str]]:
    """Read corpus grouping metadata keyed by dataset name."""
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["dataset"]: row for row in csv.DictReader(handle)}


def available_datasets(data_dir: Path) -> List[str]:
    """Return dataset folders that contain at least one child chi.csv."""
    datasets = {
        chi_csv.relative_to(data_dir).parts[0]
        for chi_csv in data_dir.rglob("chi.csv")
        if len(chi_csv.relative_to(data_dir).parts) >= 3
    }
    return sorted(datasets)


def select_datasets(
    *,
    data_dir: Path,
    grouping_csv: Path,
    selection: str,
    datasets: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    Select datasets for the consolidated output.

    The default naturalistic selection uses the auditable grouping CSV and keeps
    clinical/probe and structured-observation corpora out of the big scoring
    bundle unless explicitly requested.
    """
    available = set(available_datasets(data_dir))
    grouping = read_group_assignments(grouping_csv)

    if datasets:
        selected = list(datasets)
    elif selection == "default_naturalistic":
        selected = [
            dataset
            for dataset, row in sorted(grouping.items())
            if row.get("include_in_default_naturalistic", "").strip() == "1"
        ]
    elif selection == "all_preprocessed":
        selected = sorted(available)
    else:
        raise ValueError(f"Unknown selection: {selection}")

    missing = [dataset for dataset in selected if dataset not in available]
    if missing:
        print(f"[WARN] Selected datasets not found under {data_dir}: {', '.join(missing)}")

    return [dataset for dataset in selected if dataset in available]


def prepare_output_root(output_root: Path, *, overwrite: bool = False) -> None:
    """Create a fresh output root without silently overwriting older outputs."""
    if output_root.exists() and any(output_root.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"Output folder already exists and is not empty: {output_root}. "
                "Use --overwrite to rebuild it."
            )
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def copy_stage0_files(units: Sequence[ChildUnit], destination_data_dir: Path) -> List[ChildUnit]:
    """Copy Stage 0 cleaned files into a separate consolidated tree."""
    copied_units: List[ChildUnit] = []
    for unit in units:
        child_dir = destination_data_dir / unit.dataset / unit.child
        child_dir.mkdir(parents=True, exist_ok=True)

        chi_out = child_dir / "chi.csv"
        shutil.copy2(unit.chi_csv, chi_out)

        caretaker_out: Optional[Path] = None
        if unit.caretakers_csv is not None and unit.caretakers_csv.exists():
            caretaker_out = child_dir / "caretakers.csv"
            shutil.copy2(unit.caretakers_csv, caretaker_out)

        copied_units.append(
            ChildUnit(
                dataset=unit.dataset,
                child=unit.child,
                folder=child_dir,
                chi_csv=chi_out,
                caretakers_csv=caretaker_out,
            )
        )
    return copied_units


def count_csv_rows(path: Optional[Path]) -> int:
    """Count data rows in a CSV, returning zero for missing files."""
    if path is None or not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _row in reader)


def count_child_utterances_by_month(units: Sequence[ChildUnit]) -> Dict[int, int]:
    """Count non-empty cleaned child utterances by floored age month."""
    counts: Dict[int, int] = {}
    for unit in units:
        with unit.chi_csv.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if not row.get("utterance_clean", "").strip():
                    continue
                month = floor_age_month(row.get("age_months"))
                if month is None:
                    continue
                counts[month] = counts.get(month, 0) + 1
    return counts


def manifest_row(unit: ChildUnit) -> Dict[str, object]:
    """Return one manifest row for a consolidated child folder."""
    paths = {
        "chi_csv": unit.folder / "chi.csv",
        "caretakers_csv": unit.folder / "caretakers.csv",
        "ngram_generated_csv": unit.folder / GENERATED_FILENAME,
        "child_context_csv": unit.folder / CHILD_CONTEXT_FILENAME,
        "caretaker_context_csv": unit.folder / CARETAKER_CONTEXT_FILENAME,
        "child_scoring_csv": unit.folder / CHILD_SCORING_FILENAME,
        "caretaker_scoring_csv": unit.folder / CARETAKER_SCORING_FILENAME,
    }
    child_scoring_ready = paths["child_scoring_csv"].exists()
    caretaker_scoring_ready = paths["caretaker_scoring_csv"].exists()
    return {
        "dataset": unit.dataset,
        "child_id": unit.child,
        "stage0_ready": int(paths["chi_csv"].exists() and paths["caretakers_csv"].exists()),
        "ngram_generated_ready": int(paths["ngram_generated_csv"].exists()),
        "child_context_ready": int(paths["child_context_csv"].exists()),
        "caretaker_context_ready": int(paths["caretaker_context_csv"].exists()),
        "child_scoring_ready": int(child_scoring_ready),
        "caretaker_scoring_ready": int(caretaker_scoring_ready),
        "scoring_ready": int(child_scoring_ready and caretaker_scoring_ready),
        "chi_rows": count_csv_rows(paths["chi_csv"]),
        "caretaker_rows": count_csv_rows(paths["caretakers_csv"]),
        "child_scoring_rows": count_csv_rows(paths["child_scoring_csv"]),
        "caretaker_scoring_rows": count_csv_rows(paths["caretaker_scoring_csv"]),
        **{key: str(path) if path.exists() else "" for key, path in paths.items()},
    }


def write_manifest(path: Path, units: Sequence[ChildUnit]) -> List[Dict[str, object]]:
    """Write exact-schema child-level readiness/count manifest."""
    rows = [manifest_row(unit) for unit in units]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def filter_child_scoring_files_for_complete_baselines(
    units: Sequence[ChildUnit],
    *,
    child_scoring_filename: str = CHILD_SCORING_FILENAME,
    baseline_columns: Sequence[str] = CHILD_BASELINE_COLUMNS,
) -> int:
    """
    Drop compact child scoring rows that cannot support model comparison.

    Stage 0 copied files still preserve every cleaned utterance. This filter
    only affects chi.surprisal_scoring.csv, where rows without all generated
    baseline variants are not useful for child-vs-model surprisal comparisons.
    """
    dropped_total = 0
    for unit in units:
        path = unit.folder / child_scoring_filename
        if not path.exists():
            continue

        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        kept = [
            row
            for row in rows
            if row.get("chi_utterance_clean", "").strip()
            and all(row.get(column, "").strip() for column in baseline_columns)
        ]
        dropped_total += len(rows) - len(kept)

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                extrasaction="ignore",
                quoting=csv.QUOTE_ALL,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(kept)

    return dropped_total


def write_dataset_readme(
    path: Path,
    *,
    datasets: Sequence[str],
    bin_months: int,
    dict_subdir: str,
    binning_strategy: str,
    age_bins: Sequence[AgeBin],
    selection: str,
    manifest_rows: Sequence[Dict[str, object]],
    dropped_child_rows_without_baselines: int = 0,
) -> None:
    """Write a short README inside the generated dataset folder."""
    n_child_rows = sum(int(row["chi_rows"]) for row in manifest_rows)
    n_caretaker_rows = sum(int(row["caretaker_rows"]) for row in manifest_rows)
    n_child_scoring_rows = sum(int(row["child_scoring_rows"]) for row in manifest_rows)
    n_caretaker_scoring_rows = sum(int(row["caretaker_scoring_rows"]) for row in manifest_rows)
    text = f"""# Big Cleaned Dataset

Generated: {datetime.now().isoformat(timespec="seconds")}

Selection: `{selection}`

Binning strategy for additive n-gram dictionaries: `{binning_strategy}`.

Default age-bin width after the early custom interval: `{bin_months}` months.

Age bins:

{chr(10).join(f"- {age_bin.label}" for age_bin in age_bins)}

Datasets:

{chr(10).join(f"- {dataset}" for dataset in datasets)}

Folder contents:

- `preprocessed_data/`: copied Stage 0 `chi.csv` and `caretakers.csv` files, plus generated sibling files.
- `age_ngram_dicts/{dict_subdir}/`: additive random/unigram/bigram/trigram source vocabularies and counts.
- `manifest.csv`: one row per child folder with readiness flags and row counts.

Generated child files:

- `chi.ngram_generated.csv`
- `chi.shared_caretaker_contexts.csv`
- `chi.surprisal_scoring.csv`

Generated caretaker files:

- `caretakers.shared_caretaker_contexts.csv`
- `caretakers.surprisal_scoring.csv`

Summary:

- Child folders: {len(manifest_rows):,}
- Stage 0 child rows: {n_child_rows:,}
- Stage 0 caretaker rows: {n_caretaker_rows:,}
- Child scoring rows: {n_child_scoring_rows:,}
- Caretaker scoring rows: {n_caretaker_scoring_rows:,}
- Child scoring rows dropped for incomplete baselines: {dropped_child_rows_without_baselines:,}
"""
    path.write_text(text, encoding="utf-8")


def create_big_cleaned_dataset(
    *,
    source_data_dir: Path = DEFAULT_SOURCE_DATA_DIR,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    grouping_csv: Path = DEFAULT_GROUPING_CSV,
    selection: str = "default_naturalistic",
    datasets: Optional[Sequence[str]] = None,
    bin_months: int = 6,
    ks: Sequence[int] = (1, 2, 3),
    min_age_months: float = 0.0,
    max_age_months: float = 120.0,
    seed: int = 123,
    overwrite: bool = False,
    require_child_baselines: bool = True,
    binning_strategy: str = "fixed_width",
    early_threshold: int = 20_000,
) -> List[Dict[str, object]]:
    """Run the full consolidated cleaned-data generation pipeline."""
    selected_datasets = select_datasets(
        data_dir=source_data_dir,
        grouping_csv=grouping_csv,
        selection=selection,
        datasets=datasets,
    )
    if not selected_datasets:
        raise SystemExit("No datasets selected for the big cleaned dataset.")

    source_units = iter_child_units(source_data_dir, selected_datasets)
    if not source_units:
        raise SystemExit(f"No child folders found under {source_data_dir} for {selected_datasets}.")

    prepare_output_root(output_root, overwrite=overwrite)
    output_data_dir = output_root / "preprocessed_data"
    copied_units = copy_stage0_files(source_units, output_data_dir)

    age_bins: List[AgeBin] = []
    dict_subdir = f"bin{bin_months}"
    age_bin_strategy_for_dicts = "fixed_width"
    age_bin_threshold_for_dicts: Optional[int] = None
    if binning_strategy == "threshold_early_20k":
        month_counts = count_child_utterances_by_month(copied_units)
        age_bins = make_threshold_early_bins(
            month_counts,
            threshold=early_threshold,
            first_start=6,
            first_base_end=17,
            donor_end=23,
            standard_bin_months=bin_months,
            max_month=max(month_counts.keys(), default=23),
        )
        dict_subdir = f"custom_early_{early_threshold}"
        age_bin_strategy_for_dicts = "threshold_early_20k"
        age_bin_threshold_for_dicts = early_threshold
    elif binning_strategy == "merged_early_006_023":
        month_counts = count_child_utterances_by_month(copied_units)
        age_bins = make_merged_early_bins(
            first_start=6,
            first_end=23,
            standard_bin_months=bin_months,
            max_month=max(month_counts.keys(), default=23),
        )
        dict_subdir = "merged_early_006_023"
        age_bin_strategy_for_dicts = "merged_early_006_023"
    elif binning_strategy != "fixed_width":
        raise ValueError(f"Unknown binning strategy: {binning_strategy}")

    dict_root = output_root / "age_ngram_dicts" / dict_subdir
    build_dicts(
        units=copied_units,
        out_dir=dict_root,
        bin_months=bin_months,
        min_age_months=min_age_months,
        max_age_months=max_age_months,
        by_child=False,
        age_bins=age_bins or None,
        age_bin_strategy=age_bin_strategy_for_dicts,
        age_bin_threshold=age_bin_threshold_for_dicts,
    )

    generate_ngram_utterances(
        units=copied_units,
        model_specs=[(bin_months, dict_root)],
        which="all",
        out_mode="sibling",
        seed=seed,
        min_age_months=min_age_months,
        max_age_months=max_age_months,
    )

    write_context_files_for_units(
        copied_units,
        ks=sorted({k for k in ks if k > 0}),
        generated_filename=GENERATED_FILENAME,
        child_output_filename=CHILD_CONTEXT_FILENAME,
        caretaker_output_filename=CARETAKER_CONTEXT_FILENAME,
    )

    write_scoring_files_for_units(
        copied_units,
        child_context_filename=CHILD_CONTEXT_FILENAME,
        caretaker_context_filename=CARETAKER_CONTEXT_FILENAME,
        child_output_filename=CHILD_SCORING_FILENAME,
        caretaker_output_filename=CARETAKER_SCORING_FILENAME,
        drop_empty=True,
    )
    dropped_child_rows_without_baselines = 0
    if require_child_baselines:
        dropped_child_rows_without_baselines = filter_child_scoring_files_for_complete_baselines(copied_units)

    manifest_rows = write_manifest(output_root / "manifest.csv", copied_units)
    write_dataset_readme(
        output_root / "README.md",
        datasets=selected_datasets,
        bin_months=bin_months,
        dict_subdir=dict_subdir,
        binning_strategy=binning_strategy,
        age_bins=age_bins,
        selection=selection,
        manifest_rows=manifest_rows,
        dropped_child_rows_without_baselines=dropped_child_rows_without_baselines,
    )
    return manifest_rows


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_data_dir", type=Path, default=DEFAULT_SOURCE_DATA_DIR)
    parser.add_argument("--output_root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--grouping_csv", type=Path, default=DEFAULT_GROUPING_CSV)
    parser.add_argument(
        "--selection",
        choices=["default_naturalistic", "all_preprocessed"],
        default="default_naturalistic",
    )
    parser.add_argument("--datasets", nargs="*", default=None)
    parser.add_argument("--bin_months", type=int, default=6)
    parser.add_argument(
        "--binning_strategy",
        choices=["fixed_width", "threshold_early_20k", "merged_early_006_023"],
        default="fixed_width",
    )
    parser.add_argument("--early_threshold", type=int, default=20_000)
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--min_age_months", type=float, default=0.0)
    parser.add_argument("--max_age_months", type=float, default=120.0)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--keep_child_rows_without_baselines",
        action="store_true",
        help="Keep compact child scoring rows even when one or more generated baseline columns is blank.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    rows = create_big_cleaned_dataset(
        source_data_dir=args.source_data_dir,
        output_root=args.output_root,
        grouping_csv=args.grouping_csv,
        selection=args.selection,
        datasets=args.datasets,
        bin_months=args.bin_months,
        ks=args.ks,
        min_age_months=args.min_age_months,
        max_age_months=args.max_age_months,
        seed=args.seed,
        overwrite=args.overwrite,
        require_child_baselines=not args.keep_child_rows_without_baselines,
        binning_strategy=args.binning_strategy,
        early_threshold=args.early_threshold,
    )
    print(
        "[SUMMARY] "
        f"children={len(rows)} "
        f"child_scoring_rows={sum(int(row['child_scoring_rows']) for row in rows)} "
        f"caretaker_scoring_rows={sum(int(row['caretaker_scoring_rows']) for row in rows)}"
    )


if __name__ == "__main__":
    main()
