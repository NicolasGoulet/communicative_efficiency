#!/usr/bin/env python3
"""Build child utterance-count, age-coverage, and demographic metadata report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from child_coverage_data import (  # noqa: E402
    DEFAULT_AGE_POINTS,
    DEFAULT_DEMOGRAPHIC_CODEBOOK,
    DEFAULT_INPUT,
    DEFAULT_ONLINE_RESEARCH_AUDIT,
    DEFAULT_ONLINE_VALUE_PATCHES,
    build_child_metadata_profile,
    child_profile_display,
    child_source_display,
    dataset_metadata_summary,
    field_availability,
    read_age_points,
    read_counts,
    read_demographic_codebook,
    read_online_research_audit,
    read_online_value_patches,
)
from child_coverage_plots import plot_age_coverage, plot_horizontal, plot_vertical  # noqa: E402
from child_coverage_report import build_report  # noqa: E402

DEFAULT_OUTPUT_DIR = Path("results/child_utterance_count_histogram")
DEFAULT_FIG_DIR = Path("figs/child_utterance_count_histogram")
DEFAULT_DOC_MD = Path("docs/child_utterance_count_histogram.md")
DEFAULT_DOC_HTML = Path("docs/child_utterance_count_histogram.html")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--age-points", type=Path, default=DEFAULT_AGE_POINTS)
    parser.add_argument("--demographic-codebook", type=Path, default=DEFAULT_DEMOGRAPHIC_CODEBOOK)
    parser.add_argument("--online-value-patches", type=Path, default=DEFAULT_ONLINE_VALUE_PATCHES)
    parser.add_argument("--online-research-audit", type=Path, default=DEFAULT_ONLINE_RESEARCH_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(args.input)
    if not args.age_points.exists():
        raise FileNotFoundError(args.age_points)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.fig_dir.mkdir(parents=True, exist_ok=True)
    args.doc_md.parent.mkdir(parents=True, exist_ok=True)

    frame = read_counts(args.input)
    age_points = read_age_points(args.age_points)
    codebook = read_demographic_codebook(args.demographic_codebook)
    online_patches = read_online_value_patches(args.online_value_patches)
    online_audit = read_online_research_audit(args.online_research_audit)
    metadata_profile = build_child_metadata_profile(frame, codebook, online_patches=online_patches)
    availability_summary = field_availability(metadata_profile)
    dataset_metadata = dataset_metadata_summary(metadata_profile)
    profile_display = child_profile_display(metadata_profile)
    source_display = child_source_display(metadata_profile)

    vertical_fig = args.fig_dir / "child_utterance_counts_thin_vertical.png"
    horizontal_fig = args.fig_dir / "child_utterance_counts_horizontal.png"
    coverage_first_age_fig = args.fig_dir / "child_age_coverage_sorted_by_first_age.png"
    coverage_count_order_fig = args.fig_dir / "child_age_coverage_sorted_by_utterance_count.png"
    plot_vertical(frame, vertical_fig)
    plot_horizontal(frame, horizontal_fig)
    plot_age_coverage(frame, age_points, coverage_first_age_fig, order_by="first_age")
    plot_age_coverage(frame, age_points, coverage_count_order_fig, order_by="utterance_count")
    build_report(
        frame=frame,
        age_points=age_points,
        metadata_profile=metadata_profile,
        availability_summary=availability_summary,
        dataset_metadata=dataset_metadata,
        profile_display=profile_display,
        source_display=source_display,
        online_audit=online_audit,
        output_dir=args.output_dir,
        doc_md=args.doc_md,
        doc_html=args.doc_html,
        vertical_fig=vertical_fig,
        horizontal_fig=horizontal_fig,
        coverage_first_age_fig=coverage_first_age_fig,
        coverage_count_order_fig=coverage_count_order_fig,
    )
    print(
        {
            "status": "ok",
            "children": int(len(frame)),
            "utterances": int(frame["child_utterances"].sum()),
            "sex_known": int(metadata_profile["sex_available"].sum()),
            "ses_known": int(metadata_profile["ses_available"].sum()),
            "race_known": int(metadata_profile["race_available"].sum()),
            "online_audit_rows": int(len(online_audit)),
            "plot": str(vertical_fig),
            "report": str(args.doc_html),
        }
    )


if __name__ == "__main__":
    main()
