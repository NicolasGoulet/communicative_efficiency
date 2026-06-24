#!/usr/bin/env python3
"""Build the compact June 25th meeting index and linked pages."""

from __future__ import annotations

import argparse
import html
import math
import os
from pathlib import Path
from typing import Sequence

import pandas as pd

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


DOC_DIR = Path("docs")
FIG_DIR = Path("figs")
RESULTS_DIR = Path("results")

INDEX_HTML = DOC_DIR / "june_25th_meeting_index.html"
DISTRIBUTION_MD = DOC_DIR / "june_25th_effort_token_distributions.md"
DISTRIBUTION_HTML = DOC_DIR / "june_25th_effort_token_distributions.html"
COMPARISON_MD = DOC_DIR / "june_25th_real_baseline_caretaker_regression_lines.md"
COMPARISON_HTML = DOC_DIR / "june_25th_real_baseline_caretaker_regression_lines.html"

SUPERVISOR_REPORT_HTML = DOC_DIR / "predicting_utterance_level_information_report.html"
SUPERVISOR_REPORT_MD = DOC_DIR / "predicting_utterance_level_information_report.md"
SUPERVISOR_REPORT_EMBEDDED = DOC_DIR / "predicting_utterance_level_information_report.embedded.html"

EFFORT_SUMMARY = RESULTS_DIR / "effort_slice_audit" / "effort_quantile_summary.csv"
EFFORT_DISTRIBUTION = RESULTS_DIR / "effort_slice_audit" / "effort_value_distribution.csv"
TAIL_SUMMARY = RESULTS_DIR / "effort_distribution_tail_audit" / "effort_distribution_tail_summary.csv"
SCORABLE_SUMMARY = RESULTS_DIR / "effort_distribution_tail_audit" / "scorable_token_distribution_tail_summary.csv"
SCORABLE_DISTRIBUTION = RESULTS_DIR / "effort_distribution_tail_audit" / "scorable_token_exact_distribution.csv"
ANCOVA_SOURCE_TRAJECTORIES = FIG_DIR / "route1_exhaustive_ancova_gallery" / "child_sources_adjusted_sum_bits_k3_by_effort.png"
ANCOVA_WORD_GAPS = FIG_DIR / "route1_exhaustive_ancova_gallery" / "nb_words_sum_bits_k3_source_minus_real_gap_lines.png"

EFFORT_ORDER = [
    ("nb_words", "Words", FIG_DIR / "effort_distribution_tail_audit" / "real_words_full_distribution_tail.png"),
    ("nb_morphemes", "Morphemes", FIG_DIR / "effort_distribution_tail_audit" / "real_morphemes_full_distribution_tail.png"),
    (
        "nb_syllables_cmu_or_pkg",
        "Syllables: CMU/pkg",
        FIG_DIR / "effort_distribution_tail_audit" / "real_syllables_cmu_or_pkg_full_distribution_tail.png",
    ),
    (
        "nb_syllables_pkg",
        "Syllables: pkg",
        FIG_DIR / "effort_distribution_tail_audit" / "real_syllables_pkg_full_distribution_tail.png",
    ),
    ("nb_phonemes", "Phonemes", FIG_DIR / "effort_distribution_tail_audit" / "real_phonemes_full_distribution_tail.png"),
]
SCORABLE_PLOT = FIG_DIR / "effort_distribution_tail_audit" / "real_scorable_tokens_full_distribution_tail.png"

SOURCE_SPECS = [
    ("real", "Real child"),
    ("random", "Random"),
    ("unigram", "Unigram"),
    ("bigram", "Bigram"),
    ("trigram", "Trigram"),
    ("lstm_additive_k3_same_length", "LSTM k3"),
    ("lstm_additive_k4_same_length", "LSTM k4"),
    ("lstm_additive_k5_same_length", "LSTM k5"),
]
CARETAKER_LABEL = "Caretaker"


def rel(path: Path, base: Path = DOC_DIR) -> str:
    """Return a POSIX relative path from a document directory."""

    return Path(os.path.relpath(path, start=base)).as_posix()


def f_num(value: object, digits: int = 2) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    return f"{parsed:.{digits}f}"


def f_pct(value: object, digits: int = 2) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    return f"{100 * parsed:.{digits}f}%"


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    rendered = frame.astype(object).copy()
    header = "| " + " | ".join(str(col) for col in rendered.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def top_12_from_distribution(distribution: pd.DataFrame, *, value_col: str) -> str:
    top = distribution.sort_values(["rows", value_col], ascending=[False, True]).head(12).copy()
    return ", ".join(f"{int(row[value_col])} ({f_pct(row['pct_rows'] if 'pct_rows' in row else row['pct'])})" for _, row in top.iterrows())


def distribution_summary_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    quantiles = pd.read_csv(EFFORT_SUMMARY)
    effort_distribution = pd.read_csv(EFFORT_DISTRIBUTION)
    tail = pd.read_csv(TAIL_SUMMARY)
    scorable_summary = pd.read_csv(SCORABLE_SUMMARY)
    scorable_distribution = pd.read_csv(SCORABLE_DISTRIBUTION)

    rows: list[dict[str, object]] = []
    top_rows: list[dict[str, object]] = []
    for effort_col, label, _ in EFFORT_ORDER:
        q = quantiles[quantiles["effort_col"].eq(effort_col)].iloc[0]
        t = tail[tail["effort_col"].eq(effort_col)].iloc[0]
        dist = effort_distribution[effort_distribution["effort_col"].eq(effort_col)].copy()
        rows.append(
            {
                "measure": label,
                "mean": f_num(q["mean"]),
                "Q1": f_num(q["p25"], 0),
                "median": f_num(q["p50"], 0),
                "Q3": f_num(q["p75"], 0),
                "p90": f_num(q["p90"], 0),
                "p95": f_num(q["p95"], 0),
                "max": f_num(q["max"], 0),
                "tail beyond marker": f_pct(t["pct_above_current_fixed_max"]),
            }
        )
        top_rows.append({"measure": label, "top 12 exact values by row count": top_12_from_distribution(dist, value_col="effort_value")})

    sc = scorable_summary.iloc[0]
    exact = scorable_distribution.rename(columns={"scorable_token_count": "value"}).copy()
    exact["pct"] = exact["rows"] / exact["rows"].sum()
    exact_sorted = exact.sort_values("value").copy()
    exact_sorted["cum"] = exact_sorted["rows"].cumsum() / exact_sorted["rows"].sum()
    q1 = int(exact_sorted.loc[exact_sorted["cum"].ge(0.25), "value"].iloc[0])
    rows.append(
        {
            "measure": "Scorable target tokens",
            "mean": f_num((exact["value"] * exact["rows"]).sum() / exact["rows"].sum()),
            "Q1": str(q1),
            "median": f_num(sc["p50"], 0),
            "Q3": f_num(sc["p75"], 0),
            "p90": f_num(sc["p90"], 0),
            "p95": f_num(sc["p95"], 0),
            "max": f_num(sc["max"], 0),
            "tail beyond marker": f_pct(sc["pct_above_reference"]),
        }
    )
    top_rows.append(
        {
            "measure": "Scorable target tokens",
            "top 12 exact values by row count": top_12_from_distribution(exact.rename(columns={"value": "effort_value"}), value_col="effort_value"),
        }
    )
    return pd.DataFrame(rows), pd.DataFrame(top_rows)


def figure_grid(figures: Sequence[tuple[str, Path]]) -> str:
    lines = ['<div class="figure-grid">']
    for idx, (caption, path) in enumerate(figures):
        klass = ' class="centered"' if len(figures) % 2 == 1 and idx == len(figures) - 1 else ""
        lines.extend(
            [
                f"<figure{klass}>",
                f'<img src="{rel(path)}" alt="{html.escape(caption, quote=True)}">',
                f"<figcaption>{html.escape(caption)}</figcaption>",
                "</figure>",
            ]
        )
    lines.append("</div>")
    return "\n".join(lines)


def build_distribution_report() -> None:
    summary, top = distribution_summary_rows()
    figures = [(label, path) for _, label, path in EFFORT_ORDER] + [("Scorable target tokens", SCORABLE_PLOT)]
    md = "\n\n".join(
        [
            "# Effort and Scorable-Token Distributions",
            "Direct counts from the real-child `k3` analysis rows. No model predictions are used here.",
            "Rows: `446,985` utterances.",
            "## Summary",
            markdown_table(summary),
            "## Top Exact Values",
            markdown_table(top),
            "## Plots",
            figure_grid(figures),
        ]
    )
    DISTRIBUTION_MD.write_text(md + "\n", encoding="utf-8")
    render_markdown_file(DISTRIBUTION_MD, DISTRIBUTION_HTML, title="Effort and Scorable-Token Distributions")


def source_plot_path(source: str, model_id: str) -> Path:
    return (
        FIG_DIR
        / "route1_source_specific_corrected_fixed_effort_atlas"
        / source
        / f"{source}_k3_{model_id.lower()}_nb_words_fixed_effort_atlas.png"
    )


def caretaker_plot_path(model_id: str) -> Path:
    return FIG_DIR / "route1_caretaker_corrected_fixed_effort_atlas" / f"caretaker_k3_c{model_id.lower()}_nb_words_fixed_effort_atlas.png"


def read_source_slopes(source: str, model_id: str) -> pd.DataFrame:
    path = RESULTS_DIR / "route1_source_specific_corrected_fixed_effort_atlas" / source / "fixed_slice_slopes.csv"
    frame = pd.read_csv(path)
    return frame[
        frame["context_k"].eq("k3") & frame["model_id"].eq(model_id) & frame["effort_col"].eq("nb_words")
    ].copy()


def read_caretaker_slopes(model_id: str) -> pd.DataFrame:
    path = RESULTS_DIR / "route1_caretaker_atlas" / "full_fit" / "caretaker_fixed_slice_slopes.csv"
    frame = pd.read_csv(path)
    return frame[
        frame["context_k"].eq("k3") & frame["model_id"].eq(f"C{model_id}") & frame["effort_col"].eq("nb_words")
    ].copy()


def slope_row(label: str, slopes: pd.DataFrame) -> dict[str, object]:
    if slopes.empty:
        return {"source": label, "lines": "0", "mean slope / 6 mo": "", "range / 6 mo": "", "downward lines": ""}
    values = pd.to_numeric(slopes["slope_bits_per_6_months"], errors="coerce").dropna()
    n_down = int((values < 0).sum())
    return {
        "source": label,
        "lines": str(len(values)),
        "mean slope / 6 mo": f_num(values.mean(), 3),
        "range / 6 mo": f"{f_num(values.min(), 3)} to {f_num(values.max(), 3)}",
        "downward lines": f"{n_down}/{len(values)}",
    }


def comparison_table(model_id: str) -> pd.DataFrame:
    rows = [slope_row(label, read_source_slopes(source, model_id)) for source, label in SOURCE_SPECS]
    rows.append(slope_row(CARETAKER_LABEL, read_caretaker_slopes(model_id)))
    return pd.DataFrame(rows)


def comparison_figures(model_id: str) -> list[tuple[str, Path]]:
    figures = [(label, source_plot_path(source, model_id)) for source, label in SOURCE_SPECS]
    figures.append((CARETAKER_LABEL, caretaker_plot_path(model_id)))
    return figures


def overview_figures() -> list[tuple[str, Path]]:
    return [
        (
            "ANCOVA adjusted source trajectories: k3 sum bits by effort measure, controlling child identity and effort",
            ANCOVA_SOURCE_TRAJECTORIES,
        ),
        (
            "Words-controlled ANCOVA source-minus-real gaps: zero is the real-child fitted trajectory",
            ANCOVA_WORD_GAPS,
        ),
    ]


def build_comparison_report() -> None:
    sections = [
        "# Real, Baseline, and Caretaker Regression Lines",
        "Fixed-word `k3` regression-line comparisons. Tables report the plotted line slopes in bits per six months.",
        "Shaded bands in the source figures are fitted-mean confidence bands where available.",
        "## Overview Plots",
        "Two compact ANCOVA-style views before the detailed source-by-source regression-line dump.",
        figure_grid(overview_figures()),
    ]
    for model_id, title in [("M2", "M2: age + words + identity"), ("M3", "M3: M2 plus age-by-words")]:
        sections.extend(
            [
                f"## {title}",
                markdown_table(comparison_table(model_id)),
                figure_grid(comparison_figures(model_id)),
            ]
        )
    COMPARISON_MD.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    render_markdown_file(COMPARISON_MD, COMPARISON_HTML, title="Real, Baseline, and Caretaker Regression Lines")


def build_index() -> None:
    css = """
body { margin: 0; background: #eef2f1; color: #1e2528; font: 17px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 920px; margin: 48px auto; padding: 42px 48px; background: white; box-shadow: 0 18px 50px rgba(31, 45, 48, .12); }
h1 { margin-top: 0; border-bottom: 3px solid #2f6f73; padding-bottom: .35em; }
.links { display: grid; gap: 16px; margin-top: 28px; }
a.card { display: block; padding: 18px 20px; border: 1px solid #d9e0df; border-radius: 8px; color: inherit; text-decoration: none; background: #fafbfb; }
a.card:hover { border-color: #2f6f73; background: #f3f8f7; }
.title { font-weight: 700; font-size: 1.12rem; color: #2f6f73; }
.desc { margin-top: 4px; color: #5e686d; }
"""
    cards = [
        ("Report", SUPERVISOR_REPORT_HTML, "Main supervisor-facing report."),
        ("Effort and Scorable-Token Distributions", DISTRIBUTION_HTML, "Direct row-count summaries and plots for words, morphemes, syllables, phonemes, and evaluated target tokens."),
        ("Real, Baseline, and Caretaker Regression Lines", COMPARISON_HTML, "M2/M3 fixed-word line comparisons for real child utterances, generated baselines, and caretaker speech."),
    ]
    card_html = "\n".join(
        (
            f'<a class="card" href="{html.escape(rel(path), quote=True)}">'
            f'<div class="title">{html.escape(title)}</div>'
            f'<div class="desc">{html.escape(desc)}</div>'
            "</a>"
        )
        for title, path, desc in cards
    )
    text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>June 25th Meeting</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>June 25th Meeting</h1>
<div class="links">
{card_html}
</div>
</main>
</body>
</html>
"""
    INDEX_HTML.write_text(text, encoding="utf-8")


def build_all() -> None:
    build_distribution_report()
    build_comparison_report()
    build_index()
    render_markdown_file(SUPERVISOR_REPORT_MD, SUPERVISOR_REPORT_HTML, title="Predicting Informational Content at the Utterance Level")
    render_markdown_file(
        SUPERVISOR_REPORT_MD,
        SUPERVISOR_REPORT_EMBEDDED,
        title="Predicting Informational Content at the Utterance Level",
        embed_images=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    build_all()
    for path in [INDEX_HTML, DISTRIBUTION_HTML, COMPARISON_HTML, SUPERVISOR_REPORT_HTML, SUPERVISOR_REPORT_EMBEDDED]:
        print(f"[OK] {path}")


if __name__ == "__main__":
    main()
