#!/usr/bin/env python3
"""Attach Mistral context-entropy features to the Route 1 long dataset.

The entropy scorer produced one row per distinct non-empty context window. The
Route 1 analysis dataset is one row per target utterance/context condition. This
script joins the context-level features back onto each child target row using
the exact `(context_col_used, context_text)` pair.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import os
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, TextIO

from utterance_count_strategies import normalize_text


DEFAULT_ROUTE1_DIR = Path("results/route1_analysis_dataset")
DEFAULT_INPUT_CSV_GZ = DEFAULT_ROUTE1_DIR / "route1_scored_utterance_effort_long.csv.gz"
DEFAULT_INPUT_CSV_PLAIN = DEFAULT_ROUTE1_DIR / "route1_scored_utterance_effort_long.plain.csv"
DEFAULT_OUTPUT_CSV_GZ = (
    DEFAULT_ROUTE1_DIR / "route1_scored_utterance_effort_context_entropy_long.csv.gz"
)
DEFAULT_AUDIT_CSV = DEFAULT_ROUTE1_DIR / "context_entropy_join_audit.csv"
DEFAULT_ENTROPY_FEATURES = (
    Path("results/external/compute_surprisal_mila/context_entropy_mistral")
    / "context_entropy_features.csv.gz"
)

ENTROPY_SOURCE_COLUMNS = [
    "context_id",
    "context_token_count",
    "llm_next_entropy_bits",
    "llm_next_top1_prob",
    "llm_next_top5_mass",
    "llm_next_top10_mass",
    "llm_next_top50_mass",
    "llm_next_argmax_bits",
    "model_used",
    "dtype_used",
    "max_length_used",
    "seed_used",
]

ENTROPY_OUTPUT_COLUMNS = [
    "context_entropy_join_status",
    "context_entropy_context_id",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "context_next_top5_mass",
    "context_next_top10_mass",
    "context_next_top50_mass",
    "context_next_argmax_bits",
    "context_entropy_model_used",
    "context_entropy_dtype_used",
    "context_entropy_max_length_used",
    "context_entropy_seed_used",
]

SOURCE_TO_OUTPUT = {
    "context_id": "context_entropy_context_id",
    "context_token_count": "context_entropy_token_count",
    "llm_next_entropy_bits": "context_entropy_bits",
    "llm_next_top1_prob": "context_next_top1_prob",
    "llm_next_top5_mass": "context_next_top5_mass",
    "llm_next_top10_mass": "context_next_top10_mass",
    "llm_next_top50_mass": "context_next_top50_mass",
    "llm_next_argmax_bits": "context_next_argmax_bits",
    "model_used": "context_entropy_model_used",
    "dtype_used": "context_entropy_dtype_used",
    "max_length_used": "context_entropy_max_length_used",
    "seed_used": "context_entropy_seed_used",
}


@dataclass
class EntropyJoinAudit:
    input_csv: str
    entropy_features_csv: str
    output_csv: str
    rows_read: int = 0
    rows_written: int = 0
    child_rows: int = 0
    caretaker_rows: int = 0
    entropy_lookup_rows_read: int = 0
    entropy_lookup_keys: int = 0
    entropy_duplicate_same_rows: int = 0
    entropy_duplicate_conflict_rows: int = 0
    matched_child_context_rows: int = 0
    matched_child_context_rows_exact: int = 0
    matched_child_context_rows_text_fallback: int = 0
    missing_child_context_rows: int = 0
    empty_child_context_rows: int = 0
    k0_child_rows: int = 0
    not_applicable_caretaker_rows: int = 0
    output_has_entropy_columns: int = 0
    max_rows_limit: str = ""


def default_input_csv() -> Path:
    """Return the current best available Route 1 base CSV."""

    if DEFAULT_INPUT_CSV_GZ.exists():
        return DEFAULT_INPUT_CSV_GZ
    return DEFAULT_INPUT_CSV_PLAIN


def open_text_input(path: Path) -> TextIO:
    """Open plain or gzipped text input based on suffix."""

    if ".gz" in path.suffixes:
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


def open_text_output(path: Path) -> TextIO:
    """Open plain or gzipped text output based on suffix."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if ".gz" in path.suffixes:
        return gzip.open(path, "wt", encoding="utf-8", newline="")
    return path.open("w", encoding="utf-8", newline="")


def temporary_output_path(path: Path) -> Path:
    """Return a hidden sibling temp path for atomic writes."""

    return path.with_name(f".{path.name}.tmp")


def publish_temporary_outputs(path_pairs: Iterable[tuple[Path, Path]]) -> None:
    """Atomically publish completed outputs."""

    for tmp_path, final_path in path_pairs:
        final_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_path, final_path)


def cleanup_temporary_outputs(paths: Iterable[Path]) -> None:
    """Remove stale temp files left by interrupted runs."""

    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def entropy_key(context_col: object, context_text: object) -> tuple[str, str]:
    """Return the normalized join key for one context."""

    return (normalize_text(context_col), normalize_text(context_text))


def entropy_payload(row: Mapping[str, str]) -> dict[str, str]:
    """Keep only scorer fields that should be attached to the long dataset."""

    return {col: normalize_text(row.get(col, "")) for col in ENTROPY_SOURCE_COLUMNS}


def load_entropy_lookup(entropy_features_csv: Path) -> tuple[dict[tuple[str, str], dict[str, str]], Counter[str]]:
    """Load context entropy rows keyed by `(context_col, context_text)`."""

    lookup: dict[tuple[str, str], dict[str, str]] = {}
    counts: Counter[str] = Counter()
    with open_text_input(entropy_features_csv) as handle:
        reader = csv.DictReader(handle)
        required = {"context_col", "context_text", *ENTROPY_SOURCE_COLUMNS}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{entropy_features_csv} is missing required columns: {sorted(missing)}"
            )
        for row in reader:
            counts["rows_read"] += 1
            key = entropy_key(row.get("context_col", ""), row.get("context_text", ""))
            payload = entropy_payload(row)
            previous = lookup.get(key)
            if previous is None:
                lookup[key] = payload
                continue
            if previous == payload:
                counts["duplicate_same_rows"] += 1
            else:
                counts["duplicate_conflict_rows"] += 1
    counts["keys"] = len(lookup)
    return lookup, counts


def load_entropy_lookups(
    entropy_features_csv: Path,
) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, dict[str, str]], Counter[str]]:
    """Load entropy rows keyed both by exact window+text and by text alone.

    The scorer manifest deduplicates contexts by text. If the same text appears
    as both `context_k1` and `context_k2`, it is scored once. The entropy value
    is still valid for either window label because the model only receives the
    text string.
    """

    exact_lookup, counts = load_entropy_lookup(entropy_features_csv)
    text_lookup: dict[str, dict[str, str]] = {}
    text_conflicts = 0
    for (_, context_text), payload in exact_lookup.items():
        previous = text_lookup.get(context_text)
        if previous is None:
            text_lookup[context_text] = payload
        elif previous != payload:
            text_conflicts += 1
    counts["text_keys"] = len(text_lookup)
    counts["text_conflicts"] = text_conflicts
    return exact_lookup, text_lookup, counts


def blank_entropy_columns(status: str) -> dict[str, str]:
    """Return blank entropy columns with a join status."""

    row = {col: "" for col in ENTROPY_OUTPUT_COLUMNS}
    row["context_entropy_join_status"] = status
    return row


def output_entropy_columns(payload: Mapping[str, str]) -> dict[str, str]:
    """Map entropy scorer fields to Route 1 analysis column names."""

    out = blank_entropy_columns("matched")
    for src, dst in SOURCE_TO_OUTPUT.items():
        out[dst] = payload.get(src, "")
    return out


def attach_entropy_to_row(
    row: Mapping[str, str],
    entropy_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    entropy_text_lookup: Mapping[str, Mapping[str, str]],
    audit: EntropyJoinAudit,
    *,
    child_only: bool,
) -> dict[str, str]:
    """Return entropy columns for one Route 1 row and update audit counters."""

    role = normalize_text(row.get("role", ""))
    context_k = normalize_text(row.get("context_k", ""))
    context_col = normalize_text(row.get("context_col_used", ""))
    context_text = normalize_text(row.get("context_text", ""))

    if role == "child":
        audit.child_rows += 1
    elif role == "caretaker":
        audit.caretaker_rows += 1

    if child_only and role != "child":
        audit.not_applicable_caretaker_rows += 1
        return blank_entropy_columns("not_applicable_caretaker")
    if context_k == "k0":
        if role == "child":
            audit.k0_child_rows += 1
        return blank_entropy_columns("no_context_k0")
    if not context_text or not context_col:
        if role == "child":
            audit.empty_child_context_rows += 1
        return blank_entropy_columns("empty_context")

    payload = entropy_lookup.get(entropy_key(context_col, context_text))
    if payload is not None:
        if role == "child":
            audit.matched_child_context_rows += 1
            audit.matched_child_context_rows_exact += 1
        return output_entropy_columns(payload)

    payload = entropy_text_lookup.get(context_text)
    if payload is not None:
        if role == "child":
            audit.matched_child_context_rows += 1
            audit.matched_child_context_rows_text_fallback += 1
        out = output_entropy_columns(payload)
        out["context_entropy_join_status"] = "matched_text_fallback"
        return out

    if payload is None:
        if role == "child":
            audit.missing_child_context_rows += 1
        return blank_entropy_columns("missing_entropy")


def attach_context_entropy(
    *,
    input_csv: Path,
    entropy_features_csv: Path,
    output_csv: Path,
    audit_csv: Path,
    child_only: bool = True,
    strict: bool = True,
    max_rows: int | None = None,
) -> EntropyJoinAudit:
    """Attach context entropy features to a Route 1 long CSV."""

    tmp_output_csv = temporary_output_path(output_csv)
    tmp_audit_csv = temporary_output_path(audit_csv)
    cleanup_temporary_outputs([tmp_output_csv, tmp_audit_csv])

    entropy_lookup, entropy_text_lookup, entropy_counts = load_entropy_lookups(entropy_features_csv)
    audit = EntropyJoinAudit(
        input_csv=str(input_csv),
        entropy_features_csv=str(entropy_features_csv),
        output_csv=str(output_csv),
        entropy_lookup_rows_read=entropy_counts["rows_read"],
        entropy_lookup_keys=entropy_counts["keys"],
        entropy_duplicate_same_rows=entropy_counts["duplicate_same_rows"],
        entropy_duplicate_conflict_rows=entropy_counts["duplicate_conflict_rows"],
        max_rows_limit="" if max_rows is None else str(max_rows),
    )
    if audit.entropy_duplicate_conflict_rows and strict:
        raise ValueError(
            "Entropy feature table has conflicting duplicate context keys: "
            f"{audit.entropy_duplicate_conflict_rows}"
        )
    if entropy_counts["text_conflicts"] and strict:
        raise ValueError(
            "Entropy feature table has conflicting duplicate context texts: "
            f"{entropy_counts['text_conflicts']}"
        )

    with open_text_input(input_csv) as in_handle, open_text_output(tmp_output_csv) as out_handle:
        reader = csv.DictReader(in_handle)
        if reader.fieldnames is None:
            raise ValueError(f"{input_csv} has no header")
        overlap = set(reader.fieldnames) & set(ENTROPY_OUTPUT_COLUMNS)
        if overlap:
            raise ValueError(f"{input_csv} already has entropy output columns: {sorted(overlap)}")
        fieldnames = [*reader.fieldnames, *ENTROPY_OUTPUT_COLUMNS]
        writer = csv.DictWriter(out_handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        audit.output_has_entropy_columns = 1
        for row in reader:
            if max_rows is not None and audit.rows_read >= max_rows:
                break
            audit.rows_read += 1
            entropy_cols = attach_entropy_to_row(
                row,
                entropy_lookup,
                entropy_text_lookup,
                audit,
                child_only=child_only,
            )
            writer.writerow({**row, **entropy_cols})
            audit.rows_written += 1

    write_audit(tmp_audit_csv, audit)
    if strict and audit.missing_child_context_rows:
        raise ValueError(
            "Some child context rows could not be matched to entropy features: "
            f"{audit.missing_child_context_rows}. Output left in temporary file "
            f"{tmp_output_csv}"
        )

    publish_temporary_outputs([(tmp_output_csv, output_csv), (tmp_audit_csv, audit_csv)])
    return audit


def write_audit(path: Path, audit: EntropyJoinAudit) -> None:
    """Write a one-row audit CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(EntropyJoinAudit.__dataclass_fields__),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(asdict(audit))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--entropy-features-csv", type=Path, default=DEFAULT_ENTROPY_FEATURES)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV_GZ)
    parser.add_argument("--audit-csv", type=Path, default=DEFAULT_AUDIT_CSV)
    parser.add_argument(
        "--include-caretakers",
        action="store_true",
        help="Attach entropy to caretaker rows too. Default leaves caretaker rows as NA.",
    )
    parser.add_argument(
        "--allow-missing-child-contexts",
        action="store_true",
        help="Publish output even when non-empty child contexts do not match entropy rows.",
    )
    parser.add_argument("--max-rows", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_csv = args.input_csv or default_input_csv()
    audit = attach_context_entropy(
        input_csv=input_csv,
        entropy_features_csv=args.entropy_features_csv,
        output_csv=args.output_csv,
        audit_csv=args.audit_csv,
        child_only=not args.include_caretakers,
        strict=not args.allow_missing_child_contexts,
        max_rows=args.max_rows,
    )
    print(
        "Attached context entropy: "
        f"rows_written={audit.rows_written} "
        f"matched_child_context_rows={audit.matched_child_context_rows} "
        f"missing_child_context_rows={audit.missing_child_context_rows} "
        f"output={args.output_csv}"
    )


if __name__ == "__main__":
    main()
