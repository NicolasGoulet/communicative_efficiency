"""Markdown/HTML report generation for child coverage summaries."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from child_coverage_data import fmt
except ModuleNotFoundError:  # pragma: no cover
    from src.child_coverage_data import fmt

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


def md_table(frame: pd.DataFrame, *, digits: int = 2) -> str:
    out = frame.copy()
    if out.empty:
        return "_No rows._"
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].map(lambda value: fmt(value, digits))
    out = out.fillna("").astype(str)
    lines = [
        "| " + " | ".join(out.columns) + " |",
        "| " + " | ".join(["---"] * len(out.columns)) + " |",
    ]
    for _, row in out.iterrows():
        lines.append("| " + " | ".join(row[col].replace("|", "\\|") for col in out.columns) + " |")
    return "\n".join(lines)


def rel(path: Path, base: Path) -> str:
    return os.path.relpath(path, start=base.parent).replace(os.sep, "/")


def dataset_child_sections(profile_display: pd.DataFrame) -> str:
    sections = []
    for dataset, group in profile_display.groupby("dataset", sort=True):
        visible = group[
            [
                "child_id",
                "child_utterances",
                "age_range_months",
                "sex",
                "sex_source_type",
                "corpus_region",
                "ses_label",
                "ses_scope",
                "race_ethnicity",
                "race_scope",
                "parental_education",
            ]
        ].copy()
        sections.append(f"### {dataset}\n\n{md_table(visible, digits=1)}")
    return "\n\n".join(sections)


def build_report(
    *,
    frame: pd.DataFrame,
    age_points: pd.DataFrame,
    metadata_profile: pd.DataFrame,
    availability_summary: pd.DataFrame,
    dataset_metadata: pd.DataFrame,
    profile_display: pd.DataFrame,
    source_display: pd.DataFrame,
    online_audit: pd.DataFrame,
    output_dir: Path,
    doc_md: Path,
    doc_html: Path,
    vertical_fig: Path,
    horizontal_fig: Path,
    coverage_first_age_fig: Path,
    coverage_count_order_fig: Path,
) -> None:
    top = frame.head(12)[
        [
            "dataset",
            "child_id",
            "child_utterances",
            "child_sessions",
            "child_age_min_months",
            "child_age_max_months",
            "child_age_bins",
        ]
    ].copy()
    bottom = frame.tail(12)[
        [
            "dataset",
            "child_id",
            "child_utterances",
            "child_sessions",
            "child_age_min_months",
            "child_age_max_months",
            "child_age_bins",
        ]
    ].copy()
    dataset_summary = (
        frame.groupby("dataset", as_index=False)
        .agg(children=("child_id", "nunique"), utterances=("child_utterances", "sum"))
        .sort_values("utterances", ascending=False)
    )
    dataset_summary["share_pct"] = 100 * dataset_summary["utterances"] / dataset_summary["utterances"].sum()

    summary = pd.DataFrame(
        [
            {
                "children": len(frame),
                "total_child_utterances": int(frame["child_utterances"].sum()),
                "median_per_child": frame["child_utterances"].median(),
                "min_per_child": frame["child_utterances"].min(),
                "max_per_child": frame["child_utterances"].max(),
            }
        ]
    )
    frame.to_csv(output_dir / "child_utterance_counts.csv", index=False)
    dataset_summary.to_csv(output_dir / "dataset_utterance_count_summary.csv", index=False)
    age_points.to_csv(output_dir / "child_age_coverage_points.csv", index=False)
    metadata_profile.to_csv(output_dir / "child_metadata_profile.csv", index=False)
    availability_summary.to_csv(output_dir / "child_metadata_availability_summary.csv", index=False)
    dataset_metadata.to_csv(output_dir / "dataset_metadata_availability_summary.csv", index=False)
    online_audit.to_csv(output_dir / "child_demographic_online_research_audit.csv", index=False)

    markdown = f"""# Child Utterance Counts

This plot uses the current strict naturalistic coverage summary:

`results/big_cleaned_dataset/default_naturalistic_merged_006_023/all_child_longitudinal_age_coverage_summary.csv`

## Summary

{md_table(summary)}

## Thin-Bar Histogram

Bars are sorted from the highest to lowest child utterance count. The y-axis is log-scaled because a few children have very large counts compared with many small Wells children.

![Thin vertical bars by child]({rel(vertical_fig, doc_md)})

## Readable Horizontal Version

Same data, rotated for labels.

![Horizontal bars by child]({rel(horizontal_fig, doc_md)})

## Age Range Covered By Each Child

Line segments show the minimum-to-maximum age range available for each child. Dots show the observed recording ages inside that range, with larger dots indicating more child utterances at that exact age.

![Age coverage sorted by first observed age]({rel(coverage_first_age_fig, doc_md)})

## Age Range In The Same Order As The Histogram

This is the same coverage information, but sorted by total child utterance count to match the thin-bar histogram above.

![Age coverage sorted by utterance count]({rel(coverage_count_order_fig, doc_md)})

## Demographic Metadata Availability

This section uses the current strict-naturalistic demographic codebook plus a small online source-backed patch file:

`results/metadata/strict_naturalistic_child_demographic_codebook_2026-06-03.csv`

`configs/child_demographic_online_value_patches.csv`

Unknown means "not available in the current extracted metadata", not that the child lacks the attribute. Nationality is not currently available as a child-specific extracted field; the report therefore includes only dataset-level corpus region.

Full CSVs:

- [child metadata profile]({rel(output_dir / "child_metadata_profile.csv", doc_md)})
- [field availability summary]({rel(output_dir / "child_metadata_availability_summary.csv", doc_md)})
- [dataset metadata summary]({rel(output_dir / "dataset_metadata_availability_summary.csv", doc_md)})
- [online research audit]({rel(output_dir / "child_demographic_online_research_audit.csv", doc_md)})

{md_table(availability_summary)}

## Online Research Audit

Official corpus pages were checked where local metadata had holes. The only new value patches found in this pass are the Gina and Helen sex/gender markers from the official MPI-EVA-Manchester page. The SES/race/nationality holes mostly remain unavailable in public corpus pages, so they stay coded as unknown/unavailable instead of being guessed.

{md_table(online_audit)}

## Dataset-Level Metadata Coverage

{md_table(dataset_metadata)}

## Child Mini Reports

Each row is one child. The source labels are intentionally explicit: child-specific is strongest; corpus-level and community-level entries are useful documentation but should be used cautiously in models.

{dataset_child_sections(profile_display)}

## Demographic Source Notes

These rows show the provenance notes currently available for children or corpora with any non-empty metadata source fields. The full CSV above preserves all profile columns.

{md_table(source_display)}

## Largest Children

{md_table(top)}

## Smallest Children

{md_table(bottom)}

## Dataset Contribution

{md_table(dataset_summary, digits=2)}
"""
    doc_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(doc_md, doc_html)
