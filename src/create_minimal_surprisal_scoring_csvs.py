#!/usr/bin/env python3
"""
Create compact per-child CSVs for later surprisal scoring.

Inputs are the role-specific shared-context files:

  chi.shared_caretaker_contexts.csv
  caretakers.shared_caretaker_contexts.csv

Outputs are compact sibling files:

  chi.surprisal_scoring.csv
  caretakers.surprisal_scoring.csv

The child file is wide: the real child utterance and the random/unigram/bigram/
trigram variants share the same context_k1/context_k2/context_k3 columns on the
same row. The caretaker file contains only the caretaker cleaned utterance and
its caretaker-history context windows.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd

from build_age_word_dicts import ChildUnit, iter_child_units


CHILD_CONTEXT_FILENAME = "chi.shared_caretaker_contexts.csv"
CARETAKER_CONTEXT_FILENAME = "caretakers.shared_caretaker_contexts.csv"
CHILD_OUTPUT_FILENAME = "chi.surprisal_scoring.csv"
CARETAKER_OUTPUT_FILENAME = "caretakers.surprisal_scoring.csv"

CONTEXT_COLUMNS = ["context_k1", "context_k2", "context_k3"]
CHILD_VARIANT_COLUMNS = [
    "random_model_utterance_bin6",
    "unigram_model_utterance_bin6",
    "bigram_model_utterance_bin6",
    "trigram_model_utterance_bin6",
]
CHILD_OUTPUT_COLUMNS = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "chi_utterance_clean",
    *CHILD_VARIANT_COLUMNS,
]
CARETAKER_OUTPUT_COLUMNS = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "speaker",
    "context_k1",
    "context_k2",
    "context_k3",
    "caretaker_utterance_clean",
]


def read_csv_text(path: Path) -> pd.DataFrame:
    """Read CSV without converting blanks to NaN."""
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def text_or_empty(value: object) -> str:
    """Return a stripped text value without NaN/None artifacts."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def ensure_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Return a copy with required columns present."""
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return out


def normalize_metadata_value(row: pd.Series, column: str, fallback: str = "") -> str:
    """Read a metadata value with a fallback when blank."""
    value = text_or_empty(row.get(column, ""))
    return value if value else fallback


def child_scoring_row(row: pd.Series) -> Dict[str, str]:
    """Build one compact child scoring row."""
    dataset = normalize_metadata_value(row, "dataset")
    return {
        "dataset": dataset,
        "child_id": normalize_metadata_value(row, "child_id"),
        "source_group": normalize_metadata_value(row, "source_group", dataset),
        "session_id": normalize_metadata_value(row, "session_id"),
        "age_months": normalize_metadata_value(row, "age_months"),
        "file": normalize_metadata_value(row, "file"),
        "line_no": normalize_metadata_value(row, "line_no"),
        "utt_id": normalize_metadata_value(row, "utt_id"),
        "context_k1": normalize_metadata_value(row, "context_k1"),
        "context_k2": normalize_metadata_value(row, "context_k2"),
        "context_k3": normalize_metadata_value(row, "context_k3"),
        "chi_utterance_clean": normalize_metadata_value(row, "utterance_clean"),
        "random_model_utterance_bin6": normalize_metadata_value(row, "random_model_utterance_bin6"),
        "unigram_model_utterance_bin6": normalize_metadata_value(row, "unigram_model_utterance_bin6"),
        "bigram_model_utterance_bin6": normalize_metadata_value(row, "bigram_model_utterance_bin6"),
        "trigram_model_utterance_bin6": normalize_metadata_value(row, "trigram_model_utterance_bin6"),
    }


def caretaker_scoring_row(row: pd.Series) -> Dict[str, str]:
    """Build one compact caretaker scoring row."""
    dataset = normalize_metadata_value(row, "dataset")
    return {
        "dataset": dataset,
        "child_id": normalize_metadata_value(row, "child_id"),
        "source_group": normalize_metadata_value(row, "source_group", dataset),
        "session_id": normalize_metadata_value(row, "session_id"),
        "age_months": normalize_metadata_value(row, "age_months"),
        "file": normalize_metadata_value(row, "file"),
        "line_no": normalize_metadata_value(row, "line_no"),
        "utt_id": normalize_metadata_value(row, "utt_id"),
        "speaker": normalize_metadata_value(row, "speaker"),
        "context_k1": normalize_metadata_value(row, "context_k1"),
        "context_k2": normalize_metadata_value(row, "context_k2"),
        "context_k3": normalize_metadata_value(row, "context_k3"),
        "caretaker_utterance_clean": normalize_metadata_value(row, "utterance_clean"),
    }


def child_row_has_target(row: Dict[str, str]) -> bool:
    """Return true when at least one child target/variant is non-empty."""
    return any(text_or_empty(row[column]) for column in ["chi_utterance_clean", *CHILD_VARIANT_COLUMNS])


def caretaker_row_has_target(row: Dict[str, str]) -> bool:
    """Return true when the caretaker target utterance is non-empty."""
    return bool(text_or_empty(row["caretaker_utterance_clean"]))


def write_rows(path: Path, columns: Sequence[str], rows: Sequence[Dict[str, str]]) -> None:
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


def build_child_scoring_rows(df: pd.DataFrame, *, drop_empty: bool = True) -> List[Dict[str, str]]:
    """Build compact child scoring rows from child shared-context rows."""
    df = ensure_columns(df, ["utterance_clean", *CHILD_OUTPUT_COLUMNS, *CHILD_VARIANT_COLUMNS])
    rows = [child_scoring_row(row) for _, row in df.iterrows()]
    if drop_empty:
        rows = [row for row in rows if child_row_has_target(row)]
    return rows


def build_caretaker_scoring_rows(df: pd.DataFrame, *, drop_empty: bool = True) -> List[Dict[str, str]]:
    """Build compact caretaker scoring rows from caretaker shared-context rows."""
    df = ensure_columns(df, ["utterance_clean", *CARETAKER_OUTPUT_COLUMNS])
    rows = [caretaker_scoring_row(row) for _, row in df.iterrows()]
    if drop_empty:
        rows = [row for row in rows if caretaker_row_has_target(row)]
    return rows


def write_scoring_files_for_unit(
    unit: ChildUnit,
    *,
    child_context_filename: str = CHILD_CONTEXT_FILENAME,
    caretaker_context_filename: str = CARETAKER_CONTEXT_FILENAME,
    child_output_filename: str = CHILD_OUTPUT_FILENAME,
    caretaker_output_filename: str = CARETAKER_OUTPUT_FILENAME,
    drop_empty: bool = True,
) -> Dict[str, object]:
    """Write compact child and caretaker scoring files for one child folder."""
    child_context_path = unit.folder / child_context_filename
    caretaker_context_path = unit.folder / caretaker_context_filename
    if not child_context_path.exists():
        raise FileNotFoundError(f"Missing child context file: {child_context_path}")
    if not caretaker_context_path.exists():
        raise FileNotFoundError(f"Missing caretaker context file: {caretaker_context_path}")

    child_rows = build_child_scoring_rows(read_csv_text(child_context_path), drop_empty=drop_empty)
    caretaker_rows = build_caretaker_scoring_rows(read_csv_text(caretaker_context_path), drop_empty=drop_empty)

    child_output_path = unit.folder / child_output_filename
    caretaker_output_path = unit.folder / caretaker_output_filename
    write_rows(child_output_path, CHILD_OUTPUT_COLUMNS, child_rows)
    write_rows(caretaker_output_path, CARETAKER_OUTPUT_COLUMNS, caretaker_rows)

    return {
        "dataset": unit.dataset,
        "child": unit.child,
        "child_rows": len(child_rows),
        "caretaker_rows": len(caretaker_rows),
        "child_output": str(child_output_path),
        "caretaker_output": str(caretaker_output_path),
    }


def write_scoring_files_for_units(
    units: Sequence[ChildUnit],
    *,
    child_context_filename: str = CHILD_CONTEXT_FILENAME,
    caretaker_context_filename: str = CARETAKER_CONTEXT_FILENAME,
    child_output_filename: str = CHILD_OUTPUT_FILENAME,
    caretaker_output_filename: str = CARETAKER_OUTPUT_FILENAME,
    drop_empty: bool = True,
) -> List[Dict[str, object]]:
    """Write compact scoring files for all requested units."""
    summaries: List[Dict[str, object]] = []
    for unit in units:
        summary = write_scoring_files_for_unit(
            unit,
            child_context_filename=child_context_filename,
            caretaker_context_filename=caretaker_context_filename,
            child_output_filename=child_output_filename,
            caretaker_output_filename=caretaker_output_filename,
            drop_empty=drop_empty,
        )
        summaries.append(summary)
        print(
            f"[OK] {unit.dataset}/{unit.child}: "
            f"child_rows={summary['child_rows']} caretaker_rows={summary['caretaker_rows']}"
        )
    return summaries


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data/preprocessed_data")
    parser.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"])
    parser.add_argument("--child_context_filename", default=CHILD_CONTEXT_FILENAME)
    parser.add_argument("--caretaker_context_filename", default=CARETAKER_CONTEXT_FILENAME)
    parser.add_argument("--child_output_filename", default=CHILD_OUTPUT_FILENAME)
    parser.add_argument("--caretaker_output_filename", default=CARETAKER_OUTPUT_FILENAME)
    parser.add_argument("--keep_empty", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    units = iter_child_units(Path(args.data_dir), args.datasets)
    if not units:
        raise SystemExit(f"No chi.csv files found under {args.data_dir} for datasets={args.datasets}.")

    summaries = write_scoring_files_for_units(
        units,
        child_context_filename=args.child_context_filename,
        caretaker_context_filename=args.caretaker_context_filename,
        child_output_filename=args.child_output_filename,
        caretaker_output_filename=args.caretaker_output_filename,
        drop_empty=not args.keep_empty,
    )
    print(
        "[SUMMARY] "
        f"files={len(summaries) * 2} "
        f"child_rows={sum(int(row['child_rows']) for row in summaries)} "
        f"caretaker_rows={sum(int(row['caretaker_rows']) for row in summaries)}"
    )


if __name__ == "__main__":
    main()
