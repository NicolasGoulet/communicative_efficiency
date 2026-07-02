#!/usr/bin/env python3
"""Build a private long-list bank of context-modulation example candidates."""

from __future__ import annotations

import argparse
import html
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


YANG_ROWS = Path("results/yang_followup/yang_followup_analysis_rows.csv.gz")
ROUTE1_LONG = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
OUTPUT_DIR = Path("results/context_example_candidate_bank_for_review")
DOC_HTML = Path("docs/context_example_candidate_bank_for_review.html")

BASELINE_ORDER = [
    ("real", "Real child"),
    ("random", "Random"),
    ("unigram", "Unigram"),
    ("bigram", "Bigram"),
    ("trigram", "Trigram"),
    ("lstm_additive_k3_same_length", "LSTM k3"),
    ("lstm_additive_k4_same_length", "LSTM k4"),
    ("lstm_additive_k5_same_length", "LSTM k5"),
]
VARIANT_LABELS = dict(BASELINE_ORDER)
VARIANT_SET = set(VARIANT_LABELS)

BAD_TEXT = re.compile(
    r"xxx|yyy|www|\b0\b|_|@|\+|<|>|\[|\]|\(|\)|z_|\buh\b|\bum\b|\bhm\b|\bmm\b|"
    r"Urs|Pucilia|Mommily|vash|toopa|rubadub",
    re.IGNORECASE,
)


def f_num(value: object, digits: int = 1) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    return f"{number:.{digits}f}"


def compact(value: object, limit: int = 240) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def word_tokens(value: object) -> list[str]:
    return re.findall(r"[A-Za-z']+", str(value or ""))


def readable_response(value: object, *, min_words: int = 2, max_words: int = 14) -> bool:
    text = compact(value, limit=500)
    tokens = word_tokens(text)
    if len(tokens) < min_words or len(tokens) > max_words:
        return False
    if BAD_TEXT.search(text):
        return False
    if sum(len(token) <= 1 for token in tokens) > 1:
        return False
    return True


def readable_context(value: object) -> bool:
    text = compact(value, limit=700)
    tokens = word_tokens(text)
    if len(tokens) < 3 or len(tokens) > 80:
        return False
    if len(text) > 420:
        return False
    return not BAD_TEXT.search(text)


def add_within_group_quantiles(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    group_cols = ["age_bin", "nb_words"]
    out["q_context_bits"] = out.groupby(group_cols, observed=True)["prior_caretaker_sum_bits"].rank(pct=True)
    out["q_context_words"] = out.groupby(group_cols, observed=True)["prior_caretaker_nb_words"].rank(pct=True)
    out["q_child_bits"] = out.groupby(group_cols, observed=True)["sum_bits"].rank(pct=True)
    return out


def load_candidate_real_rows() -> pd.DataFrame:
    usecols = [
        "utterance_id",
        "dataset",
        "child_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "target_utterance_clean",
        "sum_bits",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_phonemes",
        "context_entropy_bits",
        "prior_caretaker_count",
        "prior_caretaker_sum_bits",
        "prior_caretaker_nb_words",
        "prior_caretaker_text",
    ]
    frame = pd.read_csv(YANG_ROWS, usecols=usecols)
    numeric = [
        "age_months",
        "line_no",
        "sum_bits",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_phonemes",
        "context_entropy_bits",
        "prior_caretaker_count",
        "prior_caretaker_sum_bits",
        "prior_caretaker_nb_words",
    ]
    for col in numeric:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[
        frame["nb_words"].between(2, 10)
        & frame["prior_caretaker_count"].ge(1)
        & frame["prior_caretaker_nb_words"].between(2, 80)
        & frame["target_utterance_clean"].map(readable_response)
        & frame["prior_caretaker_text"].map(readable_context)
    ].copy()
    frame = frame.drop_duplicates(["dataset", "child_id", "age_months", "target_utterance_clean", "prior_caretaker_text"])
    return add_within_group_quantiles(frame)


def select_candidates(frame: pd.DataFrame, *, per_age_type: int, max_per_child_type: int) -> pd.DataFrame:
    high = frame[
        frame["q_context_bits"].ge(0.70)
        & frame["q_context_words"].ge(0.45)
        & frame["q_child_bits"].le(0.60)
    ].copy()
    high["candidate_type"] = "high_context_candidate"
    high["review_score"] = high["q_context_bits"] + 0.5 * high["q_context_words"] + (1 - high["q_child_bits"])
    high["why_selected"] = "higher caretaker context bits/words; child response not in high surprisal tail"

    low = frame[
        frame["q_context_bits"].le(0.45)
        & frame["q_context_words"].le(0.70)
        & frame["q_child_bits"].ge(0.55)
    ].copy()
    low["candidate_type"] = "low_context_candidate"
    low["review_score"] = low["q_child_bits"] + (1 - low["q_context_bits"]) + 0.25 * (1 - low["q_context_words"])
    low["why_selected"] = "lower caretaker context bits/words; child response in higher surprisal range"

    pool = pd.concat([high, low], ignore_index=True)
    if pool.empty:
        return pool
    selected_parts: list[pd.DataFrame] = []
    for _, group in pool.groupby(["candidate_type", "age_bin"], observed=True):
        selected_parts.append(group.sort_values("review_score", ascending=False).head(per_age_type))
    ranked = pd.concat(selected_parts, ignore_index=True).sort_values("review_score", ascending=False)

    selected_rows = []
    counts: dict[tuple[str, str, str], int] = {}
    seen_responses: set[tuple[str, str, str]] = set()
    for _, row in ranked.iterrows():
        child_key = (str(row["candidate_type"]), str(row["dataset"]), str(row["child_id"]))
        response_key = (str(row["dataset"]), str(row["child_id"]), str(row["target_utterance_clean"]))
        if counts.get(child_key, 0) >= max_per_child_type:
            continue
        if response_key in seen_responses:
            continue
        selected_rows.append(row)
        counts[child_key] = counts.get(child_key, 0) + 1
        seen_responses.add(response_key)
    out = pd.DataFrame(selected_rows).reset_index(drop=True)
    out.insert(0, "candidate_id", [f"C{i:03d}" for i in range(1, len(out) + 1)])
    return out


def load_counterpart_rows(candidate_ids: set[str]) -> pd.DataFrame:
    usecols = [
        "utterance_id",
        "target_variant",
        "target_utterance_clean",
        "sum_bits",
        "n_eval_tokens",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_phonemes",
        "role",
        "context_k",
    ]
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(ROUTE1_LONG, usecols=usecols, chunksize=500_000, low_memory=False):
        sub = chunk[
            chunk["role"].eq("child")
            & chunk["context_k"].eq("k3")
            & chunk["target_variant"].isin(VARIANT_SET)
            & chunk["utterance_id"].astype(str).isin(candidate_ids)
        ].copy()
        if not sub.empty:
            parts.append(sub.drop(columns=["role", "context_k"]))
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out["source_label"] = out["target_variant"].map(VARIANT_LABELS)
    for col in ["sum_bits", "n_eval_tokens", "nb_words", "nb_morphemes", "nb_syllables_cmu_or_pkg", "nb_phonemes"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def build_wide_table(candidates: pd.DataFrame, counterparts: pd.DataFrame) -> pd.DataFrame:
    metrics = ["target_utterance_clean", "sum_bits", "nb_words", "nb_morphemes", "nb_syllables_cmu_or_pkg", "nb_phonemes"]
    wide = counterparts.pivot_table(
        index="utterance_id",
        columns="target_variant",
        values=metrics,
        aggfunc="first",
        observed=True,
    )
    wide.columns = [f"{variant}_{metric}" for metric, variant in wide.columns]
    wide = wide.reset_index()
    return candidates.merge(wide, on="utterance_id", how="left")


def candidate_summary(row: pd.Series) -> str:
    label = "HIGH context" if row["candidate_type"] == "high_context_candidate" else "LOW context"
    response = compact(row["target_utterance_clean"], 90)
    return (
        f"{html.escape(str(row['candidate_id']))} | {label} | {html.escape(str(row['dataset']))}/"
        f"{html.escape(str(row['child_id']))} | age {f_num(row['age_months'], 1)} | "
        f"{int(row['nb_words'])} words | ctx {f_num(row['prior_caretaker_nb_words'], 0)}w/"
        f"{f_num(row['prior_caretaker_sum_bits'], 1)} bits | child {f_num(row['sum_bits'], 1)} bits | "
        f"{html.escape(response)}"
    )


def counterpart_table_html(utterance_id: str, counterparts: pd.DataFrame) -> str:
    rows = []
    sub = counterparts[counterparts["utterance_id"].astype(str).eq(str(utterance_id))].copy()
    order = {variant: idx for idx, (variant, _) in enumerate(BASELINE_ORDER)}
    sub["_order"] = sub["target_variant"].map(order)
    for _, source in sub.sort_values("_order").iterrows():
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(source['source_label']))}</td>"
            f"<td>{html.escape(compact(source['target_utterance_clean'], 170))}</td>"
            f"<td>{f_num(source['sum_bits'], 1)}</td>"
            f"<td>{f_num(source['nb_words'], 0)}</td>"
            f"<td>{f_num(source['nb_morphemes'], 0)}</td>"
            f"<td>{f_num(source['nb_syllables_cmu_or_pkg'], 0)}</td>"
            f"<td>{f_num(source['nb_phonemes'], 0)}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="7">No counterpart rows found.</td></tr>')
    return (
        "<table><thead><tr>"
        "<th>Source</th><th>Utterance</th><th>k3 bits</th><th>Words</th><th>Morph.</th><th>Syll.</th><th>Phon.</th>"
        "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def render_html(candidates: pd.DataFrame, counterparts: pd.DataFrame, output_html: Path) -> None:
    css = """
body { margin: 0; background: #f4f5f2; color: #1f2528; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 1280px; margin: 28px auto; padding: 26px 34px; background: white; box-shadow: 0 12px 38px rgba(25,35,40,.12); }
h1 { margin-top: 0; }
.note { color: #4f5c61; max-width: 980px; }
.pill { display: inline-block; padding: 2px 7px; border-radius: 999px; background: #e8efef; color: #234; font-size: 12px; margin-right: 4px; }
details { border-top: 1px solid #d9dfdd; padding: 8px 0; }
summary { cursor: pointer; font-weight: 650; }
.meta { margin: 8px 0 10px; color: #4e5a5f; }
.context { margin: 8px 0; padding: 8px 10px; background: #f7f8f8; border-left: 3px solid #607d80; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; table-layout: fixed; }
th, td { border-bottom: 1px solid #e2e6e5; padding: 5px 6px; vertical-align: top; text-align: left; overflow-wrap: anywhere; }
th { background: #eef3f2; }
td:nth-child(1) { width: 90px; font-weight: 650; }
td:nth-child(n+3), th:nth-child(n+3) { width: 58px; text-align: right; }
"""
    high_n = int(candidates["candidate_type"].eq("high_context_candidate").sum()) if not candidates.empty else 0
    low_n = int(candidates["candidate_type"].eq("low_context_candidate").sum()) if not candidates.empty else 0
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Context Example Candidate Bank</title>"
        f"<style>{css}</style></head><body><main>",
        "<h1>Context Example Candidate Bank</h1>",
        "<p class='note'>Private review page. This is intentionally a long candidate bank, not a polished supervisor-facing selection. "
        "Each entry is one real child moment with the same-moment generated baseline counterparts.</p>",
        f"<p><span class='pill'>{len(candidates):,} candidates</span><span class='pill'>{high_n:,} high-context</span><span class='pill'>{low_n:,} low-context</span></p>",
        "<p class='note'>Selection uses readable real-child k3 rows. High-context candidates have relatively high preceding caretaker context bits/words within their age-bin and word-count stratum. Low-context candidates have lower context bits/words and higher child surprisal. Baselines are matched by the exact same utterance id, k3 context, and word count.</p>",
    ]
    for candidate_type, heading in [
        ("high_context_candidate", "High-Context Candidates"),
        ("low_context_candidate", "Low-Context Candidates"),
    ]:
        section = candidates[candidates["candidate_type"].eq(candidate_type)].copy()
        if section.empty:
            continue
        parts.append(f"<h2>{html.escape(heading)}</h2>")
        for _, row in section.iterrows():
            parts.append("<details>")
            parts.append(f"<summary>{candidate_summary(row)}</summary>")
            parts.append(
                "<div class='meta'>"
                f"<strong>Why selected:</strong> {html.escape(str(row['why_selected']))}<br>"
                f"<strong>File/line:</strong> {html.escape(str(row.get('file', '')))}:{f_num(row.get('line_no'), 0)} &nbsp; "
                f"<strong>Age bin:</strong> {html.escape(str(row['age_bin']))} &nbsp; "
                f"<strong>Context entropy:</strong> {f_num(row.get('context_entropy_bits'), 2)}"
                "</div>"
            )
            parts.append(
                "<div class='context'><strong>Previous caretaker context:</strong> "
                f"{html.escape(compact(row['prior_caretaker_text'], 420))}</div>"
            )
            parts.append(counterpart_table_html(str(row["utterance_id"]), counterparts))
            parts.append("</details>")
    parts.append("</main></body></html>")
    output_html.write_text("\n".join(parts), encoding="utf-8")


def build(per_age_type: int, max_per_child_type: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = select_candidates(load_candidate_real_rows(), per_age_type=per_age_type, max_per_child_type=max_per_child_type)
    candidate_ids = set(candidates["utterance_id"].astype(str))
    counterparts = load_counterpart_rows(candidate_ids)
    wide = build_wide_table(candidates, counterparts)

    candidates.to_csv(OUTPUT_DIR / "candidate_real_rows.csv", index=False)
    counterparts.to_csv(OUTPUT_DIR / "candidate_counterparts_long.csv", index=False)
    wide.to_csv(OUTPUT_DIR / "candidate_bank_wide.csv", index=False)
    render_html(candidates, counterparts, DOC_HTML)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-age-type", type=int, default=24, help="Maximum candidates per age bin and candidate type.")
    parser.add_argument("--max-per-child-type", type=int, default=10, help="Maximum candidates per child and candidate type.")
    args = parser.parse_args()
    build(per_age_type=args.per_age_type, max_per_child_type=args.max_per_child_type)
    print(f"[OK] {DOC_HTML}")
    print(f"[OK] {OUTPUT_DIR / 'candidate_bank_wide.csv'}")
    print(f"[OK] {OUTPUT_DIR / 'candidate_counterparts_long.csv'}")


if __name__ == "__main__":
    main()
