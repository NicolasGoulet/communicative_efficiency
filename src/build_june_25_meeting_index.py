#!/usr/bin/env python3
"""Build the compact June 25th meeting index and linked pages."""

from __future__ import annotations

import argparse
import re
import html
import math
import os
from pathlib import Path
from typing import Sequence

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
OPTIMALITY_MD = DOC_DIR / "june_25th_optimality_checks.md"
OPTIMALITY_HTML = DOC_DIR / "june_25th_optimality_checks.html"
EXAMPLES_MD = DOC_DIR / "june_25th_context_examples.md"
EXAMPLES_HTML = DOC_DIR / "june_25th_context_examples.html"

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
PAIRWISE_COMPARISON_DIR = RESULTS_DIR / "route1_real_vs_controls_context_report"
OPTIMALITY_RESULTS_DIR = RESULTS_DIR / "june_25_optimality_checks"
OPTIMALITY_FIG_DIR = FIG_DIR / "june_25_optimality_checks"
OPTIMALITY_PERCENTILE_FIG = OPTIMALITY_FIG_DIR / "same_effort_percentile_by_age.png"
OPTIMALITY_CONTEXT_GAIN_FIG = OPTIMALITY_FIG_DIR / "context_gain_advantage_by_age.png"
ROUTE1_LONG_INPUT = RESULTS_DIR / "route1_analysis_dataset" / "route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz"
YANG_FOLLOWUP_ROWS = RESULTS_DIR / "yang_followup" / "yang_followup_analysis_rows.csv.gz"
EXAMPLES_RESULTS_DIR = RESULTS_DIR / "june_25_context_examples"

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
BASELINE_SPECS = [(source, label) for source, label in SOURCE_SPECS if source != "real"]
BASELINE_LABEL_ORDER = [label for _, label in BASELINE_SPECS]
BASELINE_PALETTE = {
    "Random": "#8c510a",
    "Unigram": "#01665e",
    "Bigram": "#5e3c99",
    "Trigram": "#c51b7d",
    "LSTM k3": "#2166ac",
    "LSTM k4": "#1b7837",
    "LSTM k5": "#b2182b",
}
FRONTIER_EFFORT_SPECS = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables"),
    ("nb_phonemes", "Phonemes"),
]


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


def mean_ci(frame: pd.DataFrame, group_cols: Sequence[str], value_col: str) -> pd.DataFrame:
    """Return mean and 95% normal-approximation CI by group."""

    summary = (
        frame.groupby(list(group_cols), observed=True, dropna=False)[value_col]
        .agg(["count", "mean", "std"])
        .reset_index()
        .rename(columns={"count": "n"})
    )
    summary["sem"] = summary["std"] / np.sqrt(summary["n"].replace(0, np.nan))
    summary["ci95"] = 1.96 * summary["sem"]
    return summary


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


EXAMPLE_BAD_TEXT = re.compile(
    r"xxx|yyy|www|\b0\b|_|@|\+|<|>|\[|\]|\(|\)|z_|\buh\b|\bum\b|\bhm\b|\bmm\b|Urs|Pucilia|Mommily|vash|toopa|rubadub",
    re.IGNORECASE,
)


def compact_text(value: object, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def md_escape(value: object) -> str:
    return compact_text(value).replace("|", "\\|")


def readable_example_response(value: object, *, min_words: int = 3, max_words: int = 14) -> bool:
    text = compact_text(value, limit=500)
    tokens = re.findall(r"[A-Za-z']+", text)
    if len(tokens) < min_words or len(tokens) > max_words:
        return False
    if EXAMPLE_BAD_TEXT.search(text):
        return False
    if sum(len(token) <= 1 for token in tokens) > 1:
        return False
    return True


def readable_example_context(value: object) -> bool:
    text = compact_text(value, limit=500)
    tokens = re.findall(r"[A-Za-z']+", text)
    if len(tokens) < 3 or len(tokens) > 60:
        return False
    if len(text) > 300:
        return False
    return not EXAMPLE_BAD_TEXT.search(text)


def select_context_example_pairs(max_pairs: int = 8) -> pd.DataFrame:
    """Select readable high-vs-low caretaker context example pairs."""

    if not YANG_FOLLOWUP_ROWS.exists():
        return pd.DataFrame()
    usecols = [
        "utterance_id",
        "dataset",
        "child_id",
        "age_months",
        "age_bin",
        "target_utterance_clean",
        "sum_bits",
        "nb_words",
        "prior_caretaker_count",
        "prior_caretaker_sum_bits",
        "prior_caretaker_nb_words",
        "prior_caretaker_text",
    ]
    frame = pd.read_csv(YANG_FOLLOWUP_ROWS, usecols=usecols)
    for col in ["age_months", "sum_bits", "nb_words", "prior_caretaker_count", "prior_caretaker_sum_bits", "prior_caretaker_nb_words"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[
        frame["nb_words"].between(3, 9)
        & frame["prior_caretaker_count"].ge(1)
        & frame["prior_caretaker_nb_words"].between(2, 60)
        & frame["target_utterance_clean"].map(readable_example_response)
        & frame["prior_caretaker_text"].map(readable_example_context)
    ].copy()
    frame = frame.drop_duplicates(["dataset", "child_id", "age_months", "target_utterance_clean", "prior_caretaker_text"])

    candidates: list[dict[str, object]] = []
    for (age_bin, child_words), group in frame.groupby(["age_bin", "nb_words"], observed=True):
        if len(group) < 80:
            continue
        high_pool = group[
            group["prior_caretaker_sum_bits"].ge(group["prior_caretaker_sum_bits"].quantile(0.80))
            & group["prior_caretaker_nb_words"].ge(group["prior_caretaker_nb_words"].quantile(0.60))
        ].copy()
        low_pool = group[
            group["prior_caretaker_sum_bits"].le(group["prior_caretaker_sum_bits"].quantile(0.40))
            & group["prior_caretaker_nb_words"].le(group["prior_caretaker_nb_words"].quantile(0.60))
        ].copy()
        if high_pool.empty or low_pool.empty:
            continue
        high_pool["_score"] = (
            high_pool["prior_caretaker_sum_bits"].rank(pct=True)
            + high_pool["prior_caretaker_nb_words"].rank(pct=True)
            - 0.5 * high_pool["sum_bits"].rank(pct=True)
        )
        low_pool["_score"] = low_pool["sum_bits"].rank(pct=True) - 0.2 * low_pool["prior_caretaker_sum_bits"].rank(pct=True)
        for _, high in high_pool.sort_values("_score", ascending=False).head(24).iterrows():
            for _, low in low_pool.sort_values("_score", ascending=False).head(24).iterrows():
                if high["utterance_id"] == low["utterance_id"]:
                    continue
                same_child = high["dataset"] == low["dataset"] and high["child_id"] == low["child_id"]
                age_gap = abs(float(high["age_months"]) - float(low["age_months"]))
                child_bits_gap = float(low["sum_bits"]) - float(high["sum_bits"])
                if not same_child or age_gap > 4.5 or child_bits_gap < 15:
                    continue
                candidates.append(
                    {
                        "age_bin": age_bin,
                        "child_words": int(child_words),
                        "same_child": same_child,
                        "age_gap_months": age_gap,
                        "child_bits_gap_low_minus_high": child_bits_gap,
                        "high_context_dataset": high["dataset"],
                        "high_context_child": high["child_id"],
                        "high_context_age_months": high["age_months"],
                        "high_context_words": high["prior_caretaker_nb_words"],
                        "high_context_bits": high["prior_caretaker_sum_bits"],
                        "high_context_child_bits": high["sum_bits"],
                        "high_context_text": high["prior_caretaker_text"],
                        "high_context_child_response": high["target_utterance_clean"],
                        "low_context_dataset": low["dataset"],
                        "low_context_child": low["child_id"],
                        "low_context_age_months": low["age_months"],
                        "low_context_words": low["prior_caretaker_nb_words"],
                        "low_context_bits": low["prior_caretaker_sum_bits"],
                        "low_context_child_bits": low["sum_bits"],
                        "low_context_text": low["prior_caretaker_text"],
                        "low_context_child_response": low["target_utterance_clean"],
                        "_selection_score": child_bits_gap - age_gap,
                    }
                )
    if not candidates:
        return pd.DataFrame()
    ranked = pd.DataFrame(candidates).sort_values("_selection_score", ascending=False)
    selected: list[pd.Series] = []
    used_high: set[tuple[object, object, object]] = set()
    used_low: set[tuple[object, object, object]] = set()
    child_counts: dict[tuple[object, object], int] = {}
    for _, row in ranked.iterrows():
        high_key = (row["high_context_dataset"], row["high_context_child"], row["high_context_child_response"])
        low_key = (row["low_context_dataset"], row["low_context_child"], row["low_context_child_response"])
        child_key = (row["high_context_dataset"], row["high_context_child"])
        if high_key in used_high or low_key in used_low:
            continue
        if child_counts.get(child_key, 0) >= 2:
            continue
        selected.append(row)
        used_high.add(high_key)
        used_low.add(low_key)
        child_counts[child_key] = child_counts.get(child_key, 0) + 1
        if len(selected) >= max_pairs:
            break
    out = pd.DataFrame(selected).drop(columns=["_selection_score"], errors="ignore")
    return out.reset_index(drop=True)


def example_pair_section(row: pd.Series, index: int) -> str:
    title = f"### Pair {index}: {row['age_bin']}, {int(row['child_words'])} child words"
    match = (
        f"Same child: `{row['high_context_dataset']} / {row['high_context_child']}`. "
        f"Age gap between examples: `{f_num(row['age_gap_months'], 1)}` months. "
        f"Low-context child response has `{f_num(row['child_bits_gap_low_minus_high'], 1)}` more `k3` bits than the high-context response."
    )
    table = pd.DataFrame(
        [
            {
                "side": "Higher caretaker context",
                "age": f_num(row["high_context_age_months"], 1),
                "context words": f_num(row["high_context_words"], 0),
                "context bits": f_num(row["high_context_bits"], 1),
                "child k3 bits": f_num(row["high_context_child_bits"], 1),
                "caretaker context": md_escape(row["high_context_text"]),
                "child response": md_escape(row["high_context_child_response"]),
            },
            {
                "side": "Lower caretaker context",
                "age": f_num(row["low_context_age_months"], 1),
                "context words": f_num(row["low_context_words"], 0),
                "context bits": f_num(row["low_context_bits"], 1),
                "child k3 bits": f_num(row["low_context_child_bits"], 1),
                "caretaker context": md_escape(row["low_context_text"]),
                "child response": md_escape(row["low_context_child_response"]),
            },
        ]
    )
    return "\n\n".join([title, match, markdown_table(table)])


def build_examples_report() -> None:
    examples = select_context_example_pairs(max_pairs=8)
    EXAMPLES_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if not examples.empty:
        examples.to_csv(EXAMPLES_RESULTS_DIR / "context_modulation_example_pairs.csv", index=False)
    sections = [
        "# Concrete Context-Modulation Examples",
        "Illustrative real-child examples for the caretaker-context modulation question. These examples do not replace the regression; they are a readable example bank.",
        "Selection rule: real child `k3` rows only; paired examples have the same child, same age bin, exact same child word count, and nearby ages. The higher-context side has a longer/higher-bit preceding caretaker context; the lower-context side has a shorter/lower-bit preceding caretaker context.",
        "Columns: `context bits` is the summed surprisal of the previous up-to-three caretaker utterances. `child k3 bits` is the child response surprisal with the `k3` context.",
    ]
    if examples.empty:
        sections.append("_No examples available. Run the Yang follow-up analysis first._")
    else:
        sections.extend(example_pair_section(row, idx) for idx, (_, row) in enumerate(examples.iterrows(), start=1))
        sections.extend(
            [
                "## Saved Artifact",
                "```text\nresults/june_25_context_examples/context_modulation_example_pairs.csv\n```",
            ]
        )
    EXAMPLES_MD.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    render_markdown_file(EXAMPLES_MD, EXAMPLES_HTML, title="Concrete Context-Modulation Examples")


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


def read_matched_baseline_pairs() -> pd.DataFrame:
    """Read cached row-matched real-vs-baseline comparisons for the available controls."""

    parts: list[pd.DataFrame] = []
    usecols = [
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "child_nb_words",
        "real_sum_bits_k3",
        "control_sum_bits_k3",
        "real_context_gain",
        "control_context_gain",
        "control_nb_words",
        "source",
        "source_label",
    ]
    for source, label in BASELINE_SPECS:
        path = PAIRWISE_COMPARISON_DIR / f"{source}_paired_real_comparison.csv.gz"
        if not path.exists():
            continue
        frame = pd.read_csv(path, usecols=usecols)
        frame["source"] = source
        frame["source_label"] = label
        parts.append(frame)
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    for col in [
        "age_months",
        "child_nb_words",
        "real_sum_bits_k3",
        "control_sum_bits_k3",
        "real_context_gain",
        "control_context_gain",
        "control_nb_words",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["real_minus_control_sum_bits_k3"] = out["real_sum_bits_k3"] - out["control_sum_bits_k3"]
    out["real_minus_control_context_gain"] = out["real_context_gain"] - out["control_context_gain"]
    out["same_word_count"] = out["child_nb_words"].eq(out["control_nb_words"])
    return out


def ordered_age_bins(values: pd.Series) -> list[str]:
    """Return age bins in the developmental order used by the project."""

    known = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
    present = [value for value in known if value in set(values.dropna().astype(str))]
    extra = sorted(set(values.dropna().astype(str)) - set(present))
    return present + extra


def build_baseline_position_table(pairwise: pd.DataFrame) -> pd.DataFrame:
    """Collapse seven controls per utterance into baseline-set position metrics."""

    if pairwise.empty:
        return pd.DataFrame()
    frame = pairwise.dropna(subset=["real_sum_bits_k3", "control_sum_bits_k3"]).copy()
    frame["control_below_real"] = frame["control_sum_bits_k3"] < frame["real_sum_bits_k3"]
    frame["control_above_real"] = frame["control_sum_bits_k3"] > frame["real_sum_bits_k3"]
    frame["control_equal_real"] = np.isclose(frame["control_sum_bits_k3"], frame["real_sum_bits_k3"])
    keys = [
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "child_nb_words",
    ]
    grouped = (
        frame.groupby(keys, observed=True, dropna=False)
        .agg(
            real_sum_bits_k3=("real_sum_bits_k3", "first"),
            real_context_gain=("real_context_gain", "first"),
            baseline_count=("control_sum_bits_k3", "count"),
            baseline_median_sum_bits_k3=("control_sum_bits_k3", "median"),
            baseline_median_context_gain=("control_context_gain", "median"),
            controls_below_real=("control_below_real", "sum"),
            controls_equal_real=("control_equal_real", "sum"),
            controls_above_real=("control_above_real", "sum"),
        )
        .reset_index()
    )
    grouped["real_minus_median_baseline_sum_bits_k3"] = (
        grouped["real_sum_bits_k3"] - grouped["baseline_median_sum_bits_k3"]
    )
    grouped["real_minus_median_baseline_context_gain"] = (
        grouped["real_context_gain"] - grouped["baseline_median_context_gain"]
    )
    grouped["real_percentile_in_baseline_sum_bits"] = (
        grouped["controls_below_real"] + 0.5 * grouped["controls_equal_real"]
    ) / grouped["baseline_count"].replace(0, np.nan)
    grouped["share_baselines_above_real_sum_bits"] = (
        grouped["controls_above_real"] / grouped["baseline_count"].replace(0, np.nan)
    )
    return grouped


def plot_same_effort_percentile(position: pd.DataFrame, path: Path) -> None:
    """Plot real utterance position among matched same-effort alternatives."""

    if position.empty:
        return
    age_order = ordered_age_bins(position["age_bin"])
    x_map = {label: idx for idx, label in enumerate(age_order)}
    specs = [
        (
            "real_percentile_in_baseline_sum_bits",
            "Real percentile among baseline total bits",
            "Percentile",
            "#1f7a8c",
        ),
        (
            "share_baselines_above_real_sum_bits",
            "Share of baselines with higher total bits than real",
            "Share",
            "#b45f06",
        ),
        (
            "real_minus_median_baseline_sum_bits_k3",
            "Real minus median baseline total bits",
            "Bits",
            "#6f4c9b",
        ),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.8), sharex=True)
    for ax, (metric, title, ylabel, color) in zip(axes, specs):
        summary = mean_ci(position.dropna(subset=[metric]), ["age_bin"], metric)
        summary["x"] = summary["age_bin"].astype(str).map(x_map)
        summary = summary.sort_values("x")
        xs = summary["x"].to_numpy(dtype=float)
        mean = summary["mean"].to_numpy(dtype=float)
        ci = summary["ci95"].fillna(0).to_numpy(dtype=float)
        if "percentile" in metric or metric.startswith("share_"):
            mean = mean * 100
            ci = ci * 100
            ax.set_ylim(0, 100)
        ax.plot(xs, mean, marker="o", linewidth=2.3, color=color)
        ax.fill_between(xs, mean - ci, mean + ci, color=color, alpha=0.14)
        ax.axhline(50 if "percentile" in metric or metric.startswith("share_") else 0, color="#2f3437", linewidth=1)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Age bin")
        ax.set_xticks(range(len(age_order)))
        ax.set_xticklabels(age_order, rotation=35, ha="right")
        ax.grid(alpha=0.22)
    fig.suptitle("Way 1: same-context, same-word-count position among baselines", y=0.98)
    fig.tight_layout(rect=(0, 0.02, 1, 0.90))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def frontier_fig_path(effort_col: str) -> Path:
    """Return the frontier figure path for one effort unit."""

    return OPTIMALITY_FIG_DIR / f"effort_information_frontier_{effort_col}.png"


def build_context_gain_lookup(pairwise: pd.DataFrame) -> pd.DataFrame:
    """Return context gain per matched utterance/source."""

    if pairwise.empty:
        return pd.DataFrame()
    real = pairwise[["utterance_id", "real_context_gain"]].drop_duplicates("utterance_id").copy()
    real["target_variant"] = "real"
    real = real.rename(columns={"real_context_gain": "context_gain"})
    controls = (
        pairwise[["utterance_id", "source", "control_context_gain"]]
        .rename(columns={"source": "target_variant", "control_context_gain": "context_gain"})
        .drop_duplicates(["utterance_id", "target_variant"])
    )
    out = pd.concat([real[["utterance_id", "target_variant", "context_gain"]], controls], ignore_index=True)
    out["context_gain"] = pd.to_numeric(out["context_gain"], errors="coerce")
    return out


def read_matched_source_effort_rows(pairwise: pd.DataFrame, *, chunksize: int = 500_000) -> pd.DataFrame:
    """Read k3 real/baseline rows with all effort measures for matched utterances."""

    if pairwise.empty:
        return pd.DataFrame()
    context_gain = build_context_gain_lookup(pairwise)
    if context_gain.empty:
        return pd.DataFrame()
    matched_ids = set(context_gain["utterance_id"].astype(str))
    variant_labels = {"real": "Real child", **{source: label for source, label in BASELINE_SPECS}}
    variants = set(variant_labels)
    usecols = [
        "utterance_id",
        "role",
        "target_variant",
        "context_k",
        "sum_bits",
        *[col for col, _ in FRONTIER_EFFORT_SPECS],
    ]
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        ROUTE1_LONG_INPUT,
        usecols=usecols,
        chunksize=chunksize,
        low_memory=False,
    ):
        sub = chunk[
            chunk["role"].eq("child")
            & chunk["context_k"].eq("k3")
            & chunk["target_variant"].isin(variants)
            & chunk["utterance_id"].astype(str).isin(matched_ids)
        ].copy()
        if sub.empty:
            continue
        sub = sub.drop(columns=["role", "context_k"]).rename(columns={"sum_bits": "sum_bits_k3"})
        parts.append(sub)
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out = out.merge(context_gain, on=["utterance_id", "target_variant"], how="inner")
    out["source_label"] = out["target_variant"].map(variant_labels)
    out["source_type"] = np.where(out["target_variant"].eq("real"), "real", "baseline")
    for col in ["sum_bits_k3", "context_gain", *[effort for effort, _ in FRONTIER_EFFORT_SPECS]]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def common_effort_values(long_sources: pd.DataFrame, effort_col: str, *, n: int = 12) -> list[int]:
    """Return the most represented exact effort values, sorted for plotting."""

    real = long_sources[long_sources["source_type"].eq("real")].copy()
    counts = real[effort_col].dropna().astype(int).value_counts().head(n)
    return sorted(int(value) for value in counts.index)


def plot_effort_information_frontier(
    long_sources: pd.DataFrame,
    path: Path,
    *,
    effort_col: str,
    effort_label: str,
) -> pd.DataFrame:
    """Plot real effort-information tradeoff against the baseline envelope."""

    if long_sources.empty:
        return pd.DataFrame()
    keep_efforts = common_effort_values(long_sources, effort_col)
    frame = long_sources[long_sources[effort_col].isin(keep_efforts)].copy()
    summary = (
        frame.groupby([effort_col, "source_label", "source_type"], observed=True)
        .agg(
            n=("sum_bits_k3", "size"),
            mean_sum_bits_k3=("sum_bits_k3", "mean"),
            mean_context_gain=("context_gain", "mean"),
        )
        .reset_index()
    )
    baseline = summary[summary["source_type"].eq("baseline")].copy()
    envelope = (
        baseline.groupby(effort_col, observed=True)
        .agg(
            baseline_min_sum_bits=("mean_sum_bits_k3", "min"),
            baseline_max_sum_bits=("mean_sum_bits_k3", "max"),
            baseline_median_sum_bits=("mean_sum_bits_k3", "median"),
            baseline_min_context_gain=("mean_context_gain", "min"),
            baseline_max_context_gain=("mean_context_gain", "max"),
            baseline_median_context_gain=("mean_context_gain", "median"),
        )
        .reset_index()
    )
    real = summary[summary["source_label"].eq("Real child")].copy()
    frontier = real.merge(envelope, on=effort_col, how="left")
    frontier.insert(0, "effort_col", effort_col)
    frontier.insert(1, "effort_label", effort_label)
    frontier["real_minus_low_cost_frontier_bits"] = frontier["mean_sum_bits_k3"] - frontier["baseline_min_sum_bits"]
    frontier["real_minus_median_baseline_bits"] = frontier["mean_sum_bits_k3"] - frontier["baseline_median_sum_bits"]
    frontier["real_minus_high_gain_frontier"] = frontier["mean_context_gain"] - frontier["baseline_max_context_gain"]
    frontier["real_minus_median_baseline_gain"] = frontier["mean_context_gain"] - frontier["baseline_median_context_gain"]

    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.2), sharex=True)
    real = real.sort_values(effort_col)
    envelope = envelope.sort_values(effort_col)
    x = envelope[effort_col].to_numpy(dtype=float)

    axes[0].fill_between(
        x,
        envelope["baseline_min_sum_bits"].to_numpy(dtype=float),
        envelope["baseline_max_sum_bits"].to_numpy(dtype=float),
        color="#888888",
        alpha=0.18,
        label="Baseline range",
    )
    axes[0].plot(x, envelope["baseline_min_sum_bits"], color="#555555", linestyle="--", linewidth=1.8, label="Lowest baseline mean")
    axes[0].plot(real[effort_col], real["mean_sum_bits_k3"], color="#1f5a5f", marker="o", linewidth=2.4, label="Real child")
    axes[0].set_title(f"Total bits by {effort_label.lower()}")
    axes[0].set_ylabel("Mean k3 total bits")

    baseline_context_effect_low = -envelope["baseline_max_context_gain"].to_numpy(dtype=float)
    baseline_context_effect_high = -envelope["baseline_min_context_gain"].to_numpy(dtype=float)
    real_context_effect = -real["mean_context_gain"].to_numpy(dtype=float)
    axes[1].fill_between(
        x,
        baseline_context_effect_low,
        baseline_context_effect_high,
        color="#888888",
        alpha=0.18,
        label="Baseline range",
    )
    axes[1].plot(x, baseline_context_effect_low, color="#555555", linestyle="--", linewidth=1.8, label="Largest baseline reduction")
    axes[1].plot(real[effort_col], real_context_effect, color="#1f5a5f", marker="o", linewidth=2.4, label="Real child")
    axes[1].set_title(f"Context-driven reduction by {effort_label.lower()}")
    axes[1].set_ylabel("Mean k3 - k0 bits")

    for ax in axes:
        ax.set_xlabel(f"Exact {effort_label.lower()}")
        ax.set_xticks(keep_efforts)
        ax.grid(alpha=0.22)
        ax.legend()
    fig.suptitle(f"Way 2: effort-information tradeoff by {effort_label.lower()}", y=0.98)
    fig.tight_layout(rect=(0, 0.02, 1, 0.91))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)
    return frontier


def frontier_summary_table(frontier: pd.DataFrame) -> pd.DataFrame:
    """Return compact summary rows for the effort-frontier check."""

    if frontier.empty:
        return pd.DataFrame()
    weights = pd.to_numeric(frontier["n"], errors="coerce").fillna(0)
    total = weights.sum()
    rows: list[dict[str, object]] = []
    for metric, label in [
        ("real_minus_low_cost_frontier_bits", "Real minus lowest baseline total-bits frontier"),
        ("real_minus_median_baseline_bits", "Real minus median baseline total bits"),
        ("real_minus_high_gain_frontier", "Real minus highest baseline context-gain frontier"),
        ("real_minus_median_baseline_gain", "Real minus median baseline context gain"),
    ]:
        values = pd.to_numeric(frontier[metric], errors="coerce")
        weighted_mean = float((values * weights).sum() / total) if total else float("nan")
        rows.append(
            {
                "effort unit": str(frontier["effort_label"].iloc[0]),
                "frontier metric": label,
                "weighted mean": f_num(weighted_mean, 2),
                "min exact-effort gap": f_num(values.min(), 2),
                "max exact-effort gap": f_num(values.max(), 2),
                "exact effort values": f"{int(frontier[frontier['effort_col'].iloc[0]].min())}-{int(frontier[frontier['effort_col'].iloc[0]].max())}",
            }
        )
    return pd.DataFrame(rows)


def plot_context_gain_advantage(pairwise: pd.DataFrame, position: pd.DataFrame, path: Path) -> None:
    """Plot real-minus-baseline context gain by age."""

    if pairwise.empty or position.empty:
        return
    age_order = ordered_age_bins(pairwise["age_bin"])
    x_map = {label: idx for idx, label in enumerate(age_order)}
    fig, axes = plt.subplots(1, 2, figsize=(14.4, 5.2), sharex=True)

    summary = mean_ci(pairwise.dropna(subset=["real_minus_control_context_gain"]), ["age_bin", "source_label"], "real_minus_control_context_gain")
    for label in BASELINE_LABEL_ORDER:
        group = summary[summary["source_label"].eq(label)].copy()
        if group.empty:
            continue
        group["x"] = group["age_bin"].astype(str).map(x_map)
        group = group.sort_values("x")
        color = BASELINE_PALETTE.get(label)
        xs = group["x"].to_numpy(dtype=float)
        mean = group["mean"].to_numpy(dtype=float)
        ci = group["ci95"].fillna(0).to_numpy(dtype=float)
        axes[0].plot(xs, mean, marker="o", linewidth=2, markersize=4, color=color, label=label)
        axes[0].fill_between(xs, mean - ci, mean + ci, color=color, alpha=0.10)
    axes[0].set_title("Pairwise context-gain advantage")
    axes[0].set_ylabel("Real minus baseline context gain")

    aggregate = mean_ci(position.dropna(subset=["real_minus_median_baseline_context_gain"]), ["age_bin"], "real_minus_median_baseline_context_gain")
    aggregate["x"] = aggregate["age_bin"].astype(str).map(x_map)
    aggregate = aggregate.sort_values("x")
    xs = aggregate["x"].to_numpy(dtype=float)
    mean = aggregate["mean"].to_numpy(dtype=float)
    ci = aggregate["ci95"].fillna(0).to_numpy(dtype=float)
    axes[1].plot(xs, mean, marker="o", linewidth=2.4, color="#2f7d32")
    axes[1].fill_between(xs, mean - ci, mean + ci, color="#2f7d32", alpha=0.14)
    axes[1].set_title("Real minus median baseline context gain")
    axes[1].set_ylabel("Bits")

    for ax in axes:
        ax.axhline(0, color="#2f3437", linewidth=1)
        ax.set_xlabel("Age bin")
        ax.set_xticks(range(len(age_order)))
        ax.set_xticklabels(age_order, rotation=35, ha="right")
        ax.grid(alpha=0.22)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Baseline", loc="lower center", ncol=4)
    fig.suptitle("Way 3: context-gain advantage at matched effort", y=0.98)
    fig.tight_layout(rect=(0, 0.13, 1, 0.91))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def optimality_summary_table(pairwise: pd.DataFrame, position: pd.DataFrame) -> pd.DataFrame:
    """Return a compact technical summary for the matched baseline section."""

    if pairwise.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for label in BASELINE_LABEL_ORDER:
        sub = pairwise[pairwise["source_label"].eq(label)].copy()
        if sub.empty:
            continue
        rows.append(
            {
                "comparison": f"Real vs {label}",
                "matched rows": f"{len(sub):,}",
                "word mismatches": f"{int((~sub['same_word_count']).sum()):,}",
                "mean real-baseline k3 bits": f_num(sub["real_minus_control_sum_bits_k3"].mean(), 2),
                "median real-baseline k3 bits": f_num(sub["real_minus_control_sum_bits_k3"].median(), 2),
                "mean real-baseline context gain": f_num(sub["real_minus_control_context_gain"].mean(), 2),
                "baseline higher k3 bits": f_pct((sub["real_minus_control_sum_bits_k3"] < 0).mean(), 1),
            }
        )
    if not position.empty:
        rows.append(
            {
                "comparison": "Real vs all seven baselines",
                "matched rows": f"{len(position):,}",
                "word mismatches": "0",
                "mean real-baseline k3 bits": f_num(position["real_minus_median_baseline_sum_bits_k3"].mean(), 2),
                "median real-baseline k3 bits": f_num(position["real_minus_median_baseline_sum_bits_k3"].median(), 2),
                "mean real-baseline context gain": f_num(position["real_minus_median_baseline_context_gain"].mean(), 2),
                "baseline higher k3 bits": f_pct(position["share_baselines_above_real_sum_bits"].mean(), 1),
            }
        )
    return pd.DataFrame(rows)


def build_optimality_report() -> None:
    """Build the fourth June 25 page for baseline-based optimality checks."""

    pairwise = read_matched_baseline_pairs()
    if pairwise.empty:
        OPTIMALITY_MD.write_text("# Optimality Checks\n\n_No matched baseline rows available._\n", encoding="utf-8")
        render_markdown_file(OPTIMALITY_MD, OPTIMALITY_HTML, title="Optimality Checks")
        return
    OPTIMALITY_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OPTIMALITY_FIG_DIR.mkdir(parents=True, exist_ok=True)
    position = build_baseline_position_table(pairwise)
    long_sources = read_matched_source_effort_rows(pairwise)
    summary = optimality_summary_table(pairwise, position)
    frontier_parts: list[pd.DataFrame] = []
    frontier_summary_parts: list[pd.DataFrame] = []
    frontier_figures: list[tuple[str, Path]] = []
    for effort_col, effort_label in FRONTIER_EFFORT_SPECS:
        fig_path = frontier_fig_path(effort_col)
        frontier = plot_effort_information_frontier(
            long_sources,
            fig_path,
            effort_col=effort_col,
            effort_label=effort_label,
        )
        if frontier.empty:
            continue
        frontier_parts.append(frontier)
        frontier_summary_parts.append(frontier_summary_table(frontier))
        frontier_figures.append(
            (
                f"{effort_label} effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.",
                fig_path,
            )
        )
    frontier_all = pd.concat(frontier_parts, ignore_index=True) if frontier_parts else pd.DataFrame()
    frontier_summary = pd.concat(frontier_summary_parts, ignore_index=True) if frontier_summary_parts else pd.DataFrame()
    pairwise.to_csv(OPTIMALITY_RESULTS_DIR / "matched_pairwise_baseline_gaps.csv.gz", index=False)
    position.to_csv(OPTIMALITY_RESULTS_DIR / "baseline_set_position_by_utterance.csv.gz", index=False)
    summary.to_csv(OPTIMALITY_RESULTS_DIR / "same_effort_baseline_summary.csv", index=False)
    frontier_all.to_csv(OPTIMALITY_RESULTS_DIR / "effort_frontier_by_exact_effort.csv", index=False)
    frontier_summary.to_csv(OPTIMALITY_RESULTS_DIR / "effort_frontier_summary.csv", index=False)
    plot_same_effort_percentile(position, OPTIMALITY_PERCENTILE_FIG)
    plot_context_gain_advantage(pairwise, position, OPTIMALITY_CONTEXT_GAIN_FIG)

    sections = [
        "# Optimality Checks",
        "Baseline-based counterfactual checks for the original optimality question. These use scored generated alternatives that are already matched to the real child utterance.",
        "Matching rule: same utterance id, same `k3` caretaker context, and exact same word count.",
        "Technical direction: lower `k3` total bits means lower surprisal under the context. `context_gain = k0 sum_bits - k3 sum_bits`; positive real-minus-baseline gain means the real utterance benefits more from the context.",
        "## Way 1: Same-Effort Percentile",
        "For each real utterance, rank the real `k3` total bits among the seven matched baselines.",
        "How obtained: each row uses the same child utterance id, same `k3` caretaker context, and exact same word count. Negative real-minus-baseline bits means the real utterance is less surprising than the matched baseline.",
        markdown_table(summary),
        "Plot note: the percentile panel shows where the real utterance falls among the seven baseline alternatives; the share panel shows how often baseline alternatives have higher `k3` bits; the gap panel shows real minus the median baseline.",
        figure_grid(
            [
                (
                    "Same-context, same-word-count position among baseline alternatives.",
                    OPTIMALITY_PERCENTILE_FIG,
                )
            ]
        ),
        "## Way 2: Effort-Information Frontier",
        "Compare the real child effort-information curve to the envelope formed by the matched baseline sources.",
        "This is descriptive: it groups by exact effort value and plots means. It does not control for age, child identity, or time; age-stratified/frontier models would be a separate follow-up.",
        "Words are exact-matched by construction. Morphemes, syllables, and phonemes are measured effort dimensions of the same matched utterances, not additional matching constraints.",
        "How obtained: rows are grouped by exact effort value. The real line is the mean real child value. The grey band is the range of baseline source means. The dashed line is the best baseline frontier: lowest total bits on the left, largest context-driven reduction on the right.",
        "Plot direction: the right panel displays `k3 - k0` rather than `k0 - k3`, so larger context-driven reductions appear lower on the y-axis, matching the total-bits panel.",
        markdown_table(frontier_summary),
        figure_grid(frontier_figures),
        "## Way 3: Context-Gain Advantage",
        "Compare how much the previous caretaker context reduces surprisal for the real child utterance versus each matched baseline.",
        "How obtained: `context_gain = k0 sum_bits - k3 sum_bits`. Positive real-minus-baseline context gain means the same caretaker context reduces surprisal more for the real child utterance than for the generated alternative.",
        "This repeats the context-gain column from Way 1, but shows it by age and baseline type.",
        figure_grid(
            [
                (
                    "Real-minus-baseline context gain by age.",
                    OPTIMALITY_CONTEXT_GAIN_FIG,
                )
            ]
        ),
        "## Saved Artifacts",
        "```text\n"
        f"{OPTIMALITY_RESULTS_DIR / 'matched_pairwise_baseline_gaps.csv.gz'}\n"
        f"{OPTIMALITY_RESULTS_DIR / 'baseline_set_position_by_utterance.csv.gz'}\n"
        f"{OPTIMALITY_RESULTS_DIR / 'same_effort_baseline_summary.csv'}\n"
        f"{OPTIMALITY_RESULTS_DIR / 'effort_frontier_by_exact_effort.csv'}\n"
        f"{OPTIMALITY_RESULTS_DIR / 'effort_frontier_summary.csv'}\n"
        f"{OPTIMALITY_FIG_DIR}/\n"
        "```",
    ]
    OPTIMALITY_MD.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    render_markdown_file(OPTIMALITY_MD, OPTIMALITY_HTML, title="Optimality Checks")


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
        ("Optimality Checks", OPTIMALITY_HTML, "Matched counterfactual checks using the scored random, n-gram, and LSTM baseline utterances."),
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
    build_optimality_report()
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
    for path in [INDEX_HTML, DISTRIBUTION_HTML, COMPARISON_HTML, OPTIMALITY_HTML, SUPERVISOR_REPORT_HTML, SUPERVISOR_REPORT_EMBEDDED]:
        print(f"[OK] {path}")


if __name__ == "__main__":
    main()
