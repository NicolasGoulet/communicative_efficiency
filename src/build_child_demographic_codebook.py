"""Build a child-level demographic codebook with explicit provenance.

The generated table keeps extracted CHAT metadata separate from curated
documentation-based fields. This is intentional: SES and race/ethnicity are
not consistently represented across CHILDES corpora, and corpus-level claims
should not be silently converted into child-specific covariates.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping


DEFAULT_METADATA = Path(
    "results/metadata/strict_naturalistic_custom_early20k_child_metadata_summary.csv"
)
DEFAULT_OVERRIDES = Path("configs/manual_child_demographic_overrides.csv")
DEFAULT_OUTPUT = Path(
    "results/metadata/strict_naturalistic_child_demographic_codebook_2026-06-03.csv"
)
DEFAULT_PBM_OUTPUT = Path("results/metadata/pbm_child_demographic_codebook_2026-06-03.csv")
DEFAULT_SUMMARY_OUTPUT = Path(
    "results/metadata/strict_naturalistic_child_demographic_codebook_summary_2026-06-03.csv"
)

UNKNOWN = "unknown"

OUTPUT_COLUMNS = [
    "dataset",
    "child_id",
    "sex",
    "local_chat_group_values",
    "local_chat_ses_values",
    "local_chat_education_values",
    "local_demographic_header_available",
    "age_months_min",
    "age_months_max",
    "n_sessions",
    "child_nonempty_utterances",
    "caretaker_nonempty_utterances",
    "ses_category",
    "ses_label",
    "ses_scope",
    "ses_source_type",
    "ses_source_url",
    "ses_source_note",
    "ses_confidence",
    "race_ethnicity",
    "race_scope",
    "race_source_type",
    "race_source_url",
    "race_source_note",
    "race_confidence",
    "parental_education",
    "parental_education_scope",
    "parental_education_source_url",
    "parental_education_source_note",
    "demographic_notes",
    "ses_usable_as_core_predictor",
    "race_usable_as_core_predictor",
]

OVERRIDE_COLUMNS = [
    "dataset",
    "child_id",
    "ses_category",
    "ses_label",
    "ses_scope",
    "ses_source_type",
    "ses_source_url",
    "ses_source_note",
    "ses_confidence",
    "race_ethnicity",
    "race_scope",
    "race_source_type",
    "race_source_url",
    "race_source_note",
    "race_confidence",
    "parental_education",
    "parental_education_scope",
    "parental_education_source_url",
    "parental_education_source_note",
    "notes",
]

PBM_DATASETS = {"Brown", "Manchester", "Providence"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def blank_to_unknown(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else UNKNOWN


def normalize_local_ses(value: str) -> tuple[str, str, str]:
    value = blank_to_unknown(value)
    if value == "MC":
        return "middle_class", "MC", "local_chat_id"
    if value == "WC":
        return "working_class", "WC", "local_chat_id"
    if value == UNKNOWN:
        return UNKNOWN, UNKNOWN, UNKNOWN
    return value, value, "local_chat_id"


def load_overrides(path: Path) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv_rows(path)
    exact: dict[tuple[str, str], dict[str, str]] = {}
    wildcard: dict[str, dict[str, str]] = {}
    for row in rows:
        missing = set(OVERRIDE_COLUMNS) - set(row)
        if missing:
            raise ValueError(f"{path} is missing override columns: {sorted(missing)}")
        dataset = row["dataset"].strip()
        child_id = row["child_id"].strip()
        if not dataset or not child_id:
            raise ValueError(f"{path} has an override row without dataset/child_id")
        if child_id == "*":
            wildcard[dataset] = row
        else:
            exact[(dataset, child_id)] = row
    return exact, wildcard


def override_for_child(
    row: Mapping[str, str],
    exact: Mapping[tuple[str, str], Mapping[str, str]],
    wildcard: Mapping[str, Mapping[str, str]],
) -> Mapping[str, str] | None:
    key = (row["dataset"], row["child_id"])
    return exact.get(key) or wildcard.get(row["dataset"])


def seeded_demographics(row: Mapping[str, str]) -> dict[str, str]:
    ses_category, ses_label, ses_scope = normalize_local_ses(row.get("chi_id_ses_values", ""))
    ses_source_type = "local_chat_id" if ses_category != UNKNOWN else ""
    ses_confidence = "medium" if ses_category != UNKNOWN else "none"
    return {
        "ses_category": ses_category,
        "ses_label": ses_label,
        "ses_scope": ses_scope,
        "ses_source_type": ses_source_type,
        "ses_source_url": "",
        "ses_source_note": "Extracted from CHI @ID SES field." if ses_category != UNKNOWN else "",
        "ses_confidence": ses_confidence,
        "race_ethnicity": UNKNOWN,
        "race_scope": UNKNOWN,
        "race_source_type": "",
        "race_source_url": "",
        "race_source_note": "",
        "race_confidence": "none",
        "parental_education": UNKNOWN,
        "parental_education_scope": UNKNOWN,
        "parental_education_source_url": "",
        "parental_education_source_note": "",
        "demographic_notes": "",
    }


def apply_override(seed: dict[str, str], override: Mapping[str, str] | None) -> dict[str, str]:
    if not override:
        return seed
    out = dict(seed)
    mapped = {
        "ses_category": "ses_category",
        "ses_label": "ses_label",
        "ses_scope": "ses_scope",
        "ses_source_type": "ses_source_type",
        "ses_source_url": "ses_source_url",
        "ses_source_note": "ses_source_note",
        "ses_confidence": "ses_confidence",
        "race_ethnicity": "race_ethnicity",
        "race_scope": "race_scope",
        "race_source_type": "race_source_type",
        "race_source_url": "race_source_url",
        "race_source_note": "race_source_note",
        "race_confidence": "race_confidence",
        "parental_education": "parental_education",
        "parental_education_scope": "parental_education_scope",
        "parental_education_source_url": "parental_education_source_url",
        "parental_education_source_note": "parental_education_source_note",
        "notes": "demographic_notes",
    }
    for src, dst in mapped.items():
        value = (override.get(src) or "").strip()
        if value:
            out[dst] = value
    return out


def yes_no_for_core_ses(row: Mapping[str, str]) -> str:
    if row["ses_category"] == UNKNOWN:
        return "no"
    if row["ses_scope"] in {"child_specific", "corpus_level_single_child"}:
        return "yes_with_caution"
    return "no_corpus_or_community_level"


def yes_no_for_core_race(row: Mapping[str, str]) -> str:
    if row["race_ethnicity"] == UNKNOWN:
        return "no"
    if row["race_scope"] in {"child_specific", "corpus_level_single_child"}:
        return "yes_with_caution"
    return "no_community_or_corpus_level"


def build_codebook_rows(
    metadata_rows: Iterable[Mapping[str, str]],
    override_rows: tuple[Mapping[tuple[str, str], Mapping[str, str]], Mapping[str, Mapping[str, str]]],
) -> list[dict[str, str]]:
    exact, wildcard = override_rows
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source in sorted(metadata_rows, key=lambda r: (r["dataset"], r["child_id"])):
        key = (source["dataset"], source["child_id"])
        if key in seen:
            raise ValueError(f"Duplicate child key in metadata: {key}")
        seen.add(key)
        demo = apply_override(seeded_demographics(source), override_for_child(source, exact, wildcard))
        row = {
            "dataset": source["dataset"],
            "child_id": source["child_id"],
            "sex": blank_to_unknown(source.get("sex_values")),
            "local_chat_group_values": blank_to_unknown(source.get("chi_id_group_values")),
            "local_chat_ses_values": blank_to_unknown(source.get("chi_id_ses_values")),
            "local_chat_education_values": blank_to_unknown(source.get("chi_id_education_values")),
            "local_demographic_header_available": (
                "yes" if (source.get("demographic_header_values") or "").strip() else "no"
            ),
            "age_months_min": blank_to_unknown(source.get("age_months_min")),
            "age_months_max": blank_to_unknown(source.get("age_months_max")),
            "n_sessions": blank_to_unknown(source.get("n_sessions")),
            "child_nonempty_utterances": blank_to_unknown(source.get("child_nonempty_utterances")),
            "caretaker_nonempty_utterances": blank_to_unknown(
                source.get("caretaker_nonempty_utterances")
            ),
            **demo,
        }
        row["ses_usable_as_core_predictor"] = yes_no_for_core_ses(row)
        row["race_usable_as_core_predictor"] = yes_no_for_core_race(row)
        output.append({col: row.get(col, "") for col in OUTPUT_COLUMNS})
    return output


def write_csv(path: Path, rows: Iterable[Mapping[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = list(rows)
    by_dataset: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        by_dataset[row["dataset"]].append(row)

    summary: list[dict[str, str]] = []
    for dataset in sorted(by_dataset):
        sub = by_dataset[dataset]
        ses_counts = Counter(row["ses_category"] for row in sub)
        race_counts = Counter(row["race_ethnicity"] for row in sub)
        summary.append(
            {
                "dataset": dataset,
                "children": str(len(sub)),
                "ses_known_children": str(sum(row["ses_category"] != UNKNOWN for row in sub)),
                "ses_categories": "; ".join(f"{k}:{v}" for k, v in sorted(ses_counts.items())),
                "race_known_children_or_groups": str(
                    sum(row["race_ethnicity"] != UNKNOWN for row in sub)
                ),
                "race_categories": "; ".join(f"{k}:{v}" for k, v in sorted(race_counts.items())),
                "core_ses_usable_children": str(
                    sum(row["ses_usable_as_core_predictor"] == "yes_with_caution" for row in sub)
                ),
                "core_race_usable_children": str(
                    sum(row["race_usable_as_core_predictor"] == "yes_with_caution" for row in sub)
                ),
            }
        )
    summary.append(
        {
            "dataset": "TOTAL",
            "children": str(len(rows)),
            "ses_known_children": str(sum(row["ses_category"] != UNKNOWN for row in rows)),
            "ses_categories": "; ".join(
                f"{k}:{v}" for k, v in sorted(Counter(row["ses_category"] for row in rows).items())
            ),
            "race_known_children_or_groups": str(
                sum(row["race_ethnicity"] != UNKNOWN for row in rows)
            ),
            "race_categories": "; ".join(
                f"{k}:{v}"
                for k, v in sorted(Counter(row["race_ethnicity"] for row in rows).items())
            ),
            "core_ses_usable_children": str(
                sum(row["ses_usable_as_core_predictor"] == "yes_with_caution" for row in rows)
            ),
            "core_race_usable_children": str(
                sum(row["race_usable_as_core_predictor"] == "yes_with_caution" for row in rows)
            ),
        }
    )
    return summary


def build_outputs(
    metadata_path: Path,
    overrides_path: Path,
    output_path: Path,
    pbm_output_path: Path,
    summary_output_path: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    metadata_rows = read_csv_rows(metadata_path)
    rows = build_codebook_rows(metadata_rows, load_overrides(overrides_path))
    write_csv(output_path, rows, OUTPUT_COLUMNS)
    write_csv(
        pbm_output_path,
        [row for row in rows if row["dataset"] in PBM_DATASETS],
        OUTPUT_COLUMNS,
    )
    summary = summarize_rows(rows)
    summary_columns = list(summary[0].keys()) if summary else []
    write_csv(summary_output_path, summary, summary_columns)
    return rows, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pbm-output", type=Path, default=DEFAULT_PBM_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows, summary = build_outputs(
        args.metadata,
        args.overrides,
        args.output,
        args.pbm_output,
        args.summary_output,
    )
    print(f"Wrote {len(rows)} child rows to {args.output}")
    print(f"Wrote PBM subset to {args.pbm_output}")
    print(f"Wrote {len(summary)} summary rows to {args.summary_output}")


if __name__ == "__main__":
    main()
