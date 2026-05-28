#!/usr/bin/env python3
"""
Create role-specific CSVs with shared caretaker context windows.

For every real child or caretaker utterance, context_kN is the previous N
caretaker utterances in the same child/session, excluding the current row. Child
rows also carry the generated random/unigram/bigram/trigram utterance columns,
so all child variants can later be scored with the exact same context.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import pandas as pd

from build_age_word_dicts import ChildUnit, iter_child_units


DEFAULT_GENERATED_COLUMNS = [
    "random_model_utterance_bin6",
    "unigram_model_utterance_bin6",
    "bigram_model_utterance_bin6",
    "trigram_model_utterance_bin6",
]
BASE_OUTPUT_COLUMNS = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_raw",
    "age_months",
    "sex",
    "file",
    "line_no",
    "reference_line",
    "utt_id",
    "speaker",
    "speaker_group",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
]
HELPER_COLUMNS = {"_role_group", "_source_order", "_session_sort", "_file_sort", "_line_no_num", "_utt_id_num"}
GENERATED_COLUMN_RE = re.compile(r"^(random|unigram|bigram|trigram)_model_utterance_bin\d+$")
MODEL_ORDER = {"random": 0, "unigram": 1, "bigram": 2, "trigram": 3}


def read_csv_text(path: Path) -> pd.DataFrame:
    """Read a CSV as strings without converting blanks to NaN."""
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def detected_generated_columns(df: pd.DataFrame) -> List[str]:
    """Return generated model columns in model/bin order, or the bin6 defaults."""
    found = [column for column in df.columns if GENERATED_COLUMN_RE.match(str(column))]
    if not found:
        return list(DEFAULT_GENERATED_COLUMNS)

    def sort_key(column: str) -> Tuple[int, int, str]:
        model, rest = column.split("_model_utterance_bin", 1)
        try:
            bin_months = int(rest)
        except ValueError:
            bin_months = 0
        return (bin_months, MODEL_ORDER.get(model, 99), column)

    return sorted(found, key=sort_key)


def source_group_value(df: pd.DataFrame, unit: ChildUnit) -> str:
    """Return the first non-empty source_group, or a stable dataset fallback."""
    if "source_group" in df.columns:
        values = df["source_group"].astype(str).str.strip()
        non_empty = values[values != ""]
        if not non_empty.empty:
            return str(non_empty.iloc[0])
    return unit.dataset


def normalize_role_frame(
    df: pd.DataFrame,
    unit: ChildUnit,
    *,
    role_group: str,
    generated_columns: Sequence[str],
) -> pd.DataFrame:
    """Normalize one CHI or caretaker frame to the shared output schema."""
    out = df.copy()
    for column in list(out.columns):
        column_name = str(column).strip()
        if not column_name or column_name.startswith("Unnamed:") or column_name in HELPER_COLUMNS:
            out = out.drop(columns=[column])

    for column in BASE_OUTPUT_COLUMNS:
        if column not in out.columns:
            out[column] = ""
    for column in generated_columns:
        if column not in out.columns:
            out[column] = ""

    fallback_source_group = source_group_value(out, unit)
    fallback_values = {
        "dataset": unit.dataset,
        "child_id": unit.child,
        "source_group": fallback_source_group,
    }
    for column, fallback in fallback_values.items():
        values = out[column].astype("string").fillna("").str.strip()
        out[column] = values.mask(values.eq(""), fallback)

    out["speaker"] = out["speaker"].astype("string").fillna("").str.strip()
    if role_group == "CHI":
        out["speaker"] = out["speaker"].mask(out["speaker"].eq(""), "CHI")
        out["speaker_group"] = "CHILD"
    else:
        out["speaker"] = out["speaker"].where(out["speaker"].isin(["MOT", "FAT"]), "CARETAKER")
        out["speaker_group"] = "CARETAKER"
        for column in generated_columns:
            out[column] = ""

    out["_role_group"] = role_group
    out["_source_order"] = range(len(out))
    out["_session_sort"] = out["session_id"].astype(str)
    out["_file_sort"] = out["file"].astype(str)
    out["_line_no_num"] = pd.to_numeric(out["line_no"], errors="coerce")
    out["_utt_id_num"] = pd.to_numeric(out["utt_id"], errors="coerce")
    return out


def chi_source_path(unit: ChildUnit, generated_filename: str) -> Path:
    """Prefer generated child rows when present, otherwise fall back to chi.csv."""
    generated = unit.folder / generated_filename
    return generated if generated.exists() else unit.chi_csv


def load_unit_frames(unit: ChildUnit, generated_filename: str) -> Tuple[pd.DataFrame, List[str]]:
    """Load and normalize one child unit's child and caretaker rows."""
    chi_df = read_csv_text(chi_source_path(unit, generated_filename))
    generated_columns = detected_generated_columns(chi_df)
    chi = normalize_role_frame(chi_df, unit, role_group="CHI", generated_columns=generated_columns)

    if unit.caretakers_csv and unit.caretakers_csv.exists():
        caretakers_df = read_csv_text(unit.caretakers_csv)
    else:
        caretakers_df = pd.DataFrame()
    caretakers = normalize_role_frame(
        caretakers_df,
        unit,
        role_group="CARETAKER",
        generated_columns=generated_columns,
    )
    return pd.concat([chi, caretakers], ignore_index=True, sort=False), generated_columns


def sorted_conversation_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Sort rows in conversational order within one child unit."""
    return df.sort_values(
        by=["_session_sort", "_file_sort", "_line_no_num", "_utt_id_num", "_source_order"],
        kind="stable",
    ).reset_index(drop=True)


def concat_last_k(history: Sequence[str], k: int) -> str:
    """Concatenate the last k non-empty caretaker utterances."""
    if k <= 0 or not history:
        return ""
    return " ".join(history[-k:])


def context_columns_for_history(history: Sequence[str], ks: Sequence[int]) -> Dict[str, str]:
    """Return context_kN columns from the current caretaker history."""
    return {f"context_k{k}": concat_last_k(history, k) for k in ks}


def row_to_output(
    row: pd.Series,
    *,
    generated_columns: Sequence[str],
    context_values: Dict[str, str],
) -> Dict[str, str]:
    """Convert one sorted row plus context values to the flat output row."""
    output: Dict[str, str] = {}
    for column in BASE_OUTPUT_COLUMNS:
        output[column] = str(row.get(column, "") or "")
    for column in generated_columns:
        output[column] = str(row.get(column, "") or "")
    output.update(context_values)
    return output


def iter_context_rows_for_unit(
    unit: ChildUnit,
    *,
    ks: Sequence[int],
    generated_filename: str = "chi.ngram_generated.csv",
) -> Iterator[Dict[str, str]]:
    """Yield flat context rows for one child unit."""
    combined, generated_columns = load_unit_frames(unit, generated_filename)
    if combined.empty:
        return

    combined = sorted_conversation_rows(combined)
    context_history_by_session: Dict[str, List[str]] = {}

    for _, row in combined.iterrows():
        session_key = str(row["_session_sort"])
        history = context_history_by_session.setdefault(session_key, [])
        context_values = context_columns_for_history(history, ks)
        yield row_to_output(row, generated_columns=generated_columns, context_values=context_values)

        if row["_role_group"] == "CARETAKER":
            text = str(row.get("utterance_clean", "") or "").strip()
            if text:
                history.append(text)


def output_columns(generated_columns: Sequence[str], ks: Sequence[int], role_group: str) -> List[str]:
    """Return exact role-specific output header order."""
    columns = list(BASE_OUTPUT_COLUMNS)
    if role_group == "CHILD":
        columns.extend(generated_columns)
    columns.extend(f"context_k{k}" for k in ks)
    return columns


def write_context_files_for_unit(
    unit: ChildUnit,
    *,
    ks: Sequence[int],
    generated_filename: str = "chi.ngram_generated.csv",
    child_output_filename: str = "chi.shared_caretaker_contexts.csv",
    caretaker_output_filename: str = "caretakers.shared_caretaker_contexts.csv",
) -> Dict[str, object]:
    """Write child-only and caretaker-only context files for one child unit."""
    combined, generated_columns = load_unit_frames(unit, generated_filename)
    combined = sorted_conversation_rows(combined)

    child_path = unit.folder / child_output_filename
    caretaker_path = unit.folder / caretaker_output_filename
    child_count = 0
    caretaker_count = 0
    context_history_by_session: Dict[str, List[str]] = {}

    with child_path.open("w", newline="", encoding="utf-8") as child_handle, caretaker_path.open(
        "w", newline="", encoding="utf-8"
    ) as caretaker_handle:
        child_writer = csv.DictWriter(
            child_handle,
            fieldnames=output_columns(generated_columns, ks, "CHILD"),
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        caretaker_writer = csv.DictWriter(
            caretaker_handle,
            fieldnames=output_columns(generated_columns, ks, "CARETAKER"),
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        child_writer.writeheader()
        caretaker_writer.writeheader()

        for _, row in combined.iterrows():
            session_key = str(row["_session_sort"])
            history = context_history_by_session.setdefault(session_key, [])
            context_values = context_columns_for_history(history, ks)
            output_row = row_to_output(
                row,
                generated_columns=generated_columns,
                context_values=context_values,
            )

            if row["_role_group"] == "CHI":
                child_writer.writerow(output_row)
                child_count += 1
            else:
                caretaker_writer.writerow(output_row)
                caretaker_count += 1
                text = str(row.get("utterance_clean", "") or "").strip()
                if text:
                    history.append(text)

    return {
        "dataset": unit.dataset,
        "child": unit.child,
        "child_rows": child_count,
        "caretaker_rows": caretaker_count,
        "child_output": str(child_path),
        "caretaker_output": str(caretaker_path),
    }


def write_context_files_for_units(
    units: Sequence[ChildUnit],
    *,
    ks: Sequence[int],
    generated_filename: str = "chi.ngram_generated.csv",
    child_output_filename: str = "chi.shared_caretaker_contexts.csv",
    caretaker_output_filename: str = "caretakers.shared_caretaker_contexts.csv",
) -> List[Dict[str, object]]:
    """Write role-specific context files for all requested units."""
    summaries: List[Dict[str, object]] = []
    for unit in units:
        summary = write_context_files_for_unit(
            unit,
            ks=ks,
            generated_filename=generated_filename,
            child_output_filename=child_output_filename,
            caretaker_output_filename=caretaker_output_filename,
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
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--generated_filename", default="chi.ngram_generated.csv")
    parser.add_argument("--child_output_filename", default="chi.shared_caretaker_contexts.csv")
    parser.add_argument("--caretaker_output_filename", default="caretakers.shared_caretaker_contexts.csv")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    ks = sorted({k for k in args.ks if k > 0})
    if not ks:
        raise SystemExit("At least one positive k value is required.")

    units = iter_child_units(Path(args.data_dir), args.datasets)
    if not units:
        raise SystemExit(f"No chi.csv files found under {args.data_dir} for datasets={args.datasets}.")

    summaries = write_context_files_for_units(
        units,
        ks=ks,
        generated_filename=args.generated_filename,
        child_output_filename=args.child_output_filename,
        caretaker_output_filename=args.caretaker_output_filename,
    )
    print(
        "[SUMMARY] "
        f"files={len(summaries) * 2} "
        f"child_rows={sum(int(row['child_rows']) for row in summaries)} "
        f"caretaker_rows={sum(int(row['caretaker_rows']) for row in summaries)}"
    )


if __name__ == "__main__":
    main()
