#!/usr/bin/env python3
"""Build one interactive, human-readable explorer for direct-score results."""

from __future__ import annotations

import argparse
import html
import json
import math
import os
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "tiny_models": ROOT / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/model_summaries.csv",
    "tiny_coefficients": ROOT / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/coefficients_long.csv",
    "tiny_coverage": ROOT / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/model_coverage.csv",
    "tiny_profiles": ROOT / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/child_profile_audit.csv",
    "mistral_models": ROOT / "results/direct_surprisal_replication/mistral_full79/modular/models/model_summaries.csv",
    "mistral_coefficients": ROOT / "results/direct_surprisal_replication/mistral_full79/modular/models/coefficients_long.csv",
    "mistral_coverage": ROOT / "results/direct_surprisal_replication/mistral_full79/modular/models/model_coverage.csv",
    "mistral_profiles": ROOT / "results/direct_surprisal_replication/mistral_full79/modular/models/child_profile_audit.csv",
    "paired_slopes": ROOT / "results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_all_outcome_slopes.csv",
    "paired_quadratic": ROOT / "results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_quadratic_age_comparison.csv",
    "paired_rankings": ROOT / "results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_candidate_rankings.csv",
    "output": ROOT / "docs/direct_surprisal_results_explorer.html",
}

SCOPES = {
    "pbm_discovery": "PBM discovery · 21 children",
    "non_pbm_confirmation": "Non-PBM confirmation · 58 children",
    "all79_descriptive": "All 79 children · descriptive",
}

OUTCOMES = {
    "real_k3_sum_bits": "Contextual predictability (k3)",
    "real_k0_sum_bits": "Unconditional form predictability (k0)",
    "real_k1_sum_bits": "Contextual predictability (k1)",
    "real_k2_sum_bits": "Contextual predictability (k2)",
    "real_context_gain_k1": "Context support (k0 − k1)",
    "real_context_gain_k2": "Context support (k0 − k2)",
    "real_context_gain_k3": "Context support (k0 − k3)",
    "random_minus_real_k3_bits": "Random candidate minus real child",
    "unigram_minus_real_k3_bits": "Unigram candidate minus real child",
    "bigram_minus_real_k3_bits": "Bigram candidate minus real child",
    "trigram_minus_real_k3_bits": "Trigram candidate minus real child",
}

ESTIMATORS = {
    "exact_cell_wls_child_cluster": "Child-fixed weighted regression; uncertainty clustered by child",
    "exact_cell_gee_child_cluster": "GEE repeated-measures sensitivity grouped by child",
    "mundlak_wls_child_cluster": "Within/between-child (Mundlak) sensitivity",
    "linear_top12_word_wls_child_cluster": "Linear word-effort sensitivity with child fixed effects",
    "mixed_random_intercept": "Random-intercept mixed-model sensitivity",
    "mixed_random_age": "Random-age-slope mixed-model sensitivity",
}


def finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def clean(value: object) -> object:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def model_category(model_id: str, role: str) -> str:
    if role == "caretaker" or model_id.startswith("C"):
        return "caregiver"
    if model_id.startswith(("B1", "B2", "B3", "B4")):
        return "candidate"
    if model_id.startswith(("S1", "S2", "S3", "S4")):
        return "context"
    if any(token in model_id for token in ["mundlak", "gee", "mixed", "tail_trim", "linear_word_effort"]):
        return "robustness"
    if any(token in model_id for token in ["age_bins", "quadratic"]):
        return "age_shape"
    if model_id.startswith(("P1", "P2", "P3")):
        return "primary"
    return "other"


def category_label(category: str) -> str:
    return {
        "primary": "Primary question",
        "age_shape": "Age shape",
        "robustness": "Robustness check",
        "context": "Context-window comparison",
        "candidate": "Generated-candidate comparison",
        "caregiver": "Caregiver input",
        "other": "Additional model",
    }[category]


def model_title(model_id: str, outcome: str, category: str) -> str:
    base = OUTCOMES.get(outcome, outcome.replace("_", " "))
    suffixes = {
        "age_bins": " · age-bin model",
        "quadratic": " · curved-age model",
        "mundlak": " · within/between-child check",
        "gee": " · GEE check",
        "linear_word_effort": " · linear-effort check",
        "tail_trim_0_5pct": " · tail-trim check",
        "mixed_random_intercept": " · random-intercept check",
        "mixed_random_age": " · random-age-slope check",
    }
    suffix = next((label for token, label in suffixes.items() if token in model_id), "")
    if category == "caregiver":
        base = "Caregiver input: " + base.lower()
    return base + suffix


def model_question(outcome: str, category: str, role: str) -> str:
    subject = "caregiver input" if role == "caretaker" else "children's observed utterances"
    if outcome == "real_k3_sum_bits":
        return f"At the same lexical word effort, does {subject} become more or less predictable with child age?"
    if outcome == "real_k0_sum_bits":
        return f"Ignoring conversational context, does the utterance form become more or less predictable with child age?"
    if "context_gain" in outcome:
        return "Does the preceding caregiver context contribute more or less support as children get older?"
    if "minus_real" in outcome:
        return "Does this same-length generated candidate move closer to or farther from the real child utterance with age?"
    if outcome in {"real_k1_sum_bits", "real_k2_sum_bits"}:
        return "Does the developmental pattern persist when a shorter caregiver-context window is used?"
    return "What age-related association does this specification estimate?"


def controls_text(formula: str, estimator: str, weighting_note: object) -> str:
    parts = []
    if "word_count_exact_top12" in formula:
        parts.append("exact/top-coded lexical word count")
    elif "word_count_top12_numeric" in formula:
        parts.append("linear top-coded word count")
    if "C(child_key)" in formula:
        parts.append("a separate baseline for each child")
    if "C(dataset)" in formula:
        parts.append("corpus")
    if "age_within" in formula:
        parts.append("within- versus between-child age")
    if "I(age_c ** 2)" in formula:
        parts.append("quadratic age curvature")
    if not parts:
        parts.append("the controls shown in the formula")
    text = ", ".join(parts)
    if clean(weighting_note):
        text += f". Weighting note: {weighting_note}"
    return text


def result_text(row: Mapping[str, object]) -> str:
    estimate = finite(row.get("age_estimate"))
    low = finite(row.get("age_ci_low"))
    high = finite(row.get("age_ci_high"))
    outcome = str(row.get("outcome", ""))
    status = str(row.get("fit_status", ""))
    if estimate is None:
        if "age_bins" in str(row.get("model_id", "")):
            return "This model estimates separate differences for each age bin; it has no single monthly slope. Expand the card to see the age-bin coefficients."
        return "This specification does not have one directly comparable monthly age coefficient. Expand the card for its age terms and fit status."
    interval = f" Its 95% interval is {low:+.3f} to {high:+.3f}." if low is not None and high is not None else ""
    if status not in {"PASS", ""}:
        return f"The fitted age coefficient is {estimate:+.3f}, but this {status.lower()} sensitivity fit is not primary evidence.{interval}"
    crosses = low is not None and high is not None and low <= 0 <= high
    if outcome in {"real_k3_sum_bits", "real_k1_sum_bits", "real_k2_sum_bits"}:
        meaning = "greater predictability with age" if estimate < 0 else "lower predictability with age"
    elif outcome == "real_k0_sum_bits":
        meaning = "greater unconditional form predictability with age" if estimate < 0 else "lower unconditional form predictability with age"
    elif "context_gain" in outcome:
        meaning = "declining contextual support with age" if estimate < 0 else "increasing contextual support with age"
    elif "minus_real" in outcome:
        meaning = "a growing generated-candidate disadvantage" if estimate > 0 else "a shrinking generated-candidate disadvantage"
    else:
        meaning = "a negative age association" if estimate < 0 else "a positive age association"
    certainty = " The interval crosses zero, so the direction is uncertain under this fit." if crosses else " The interval does not cross zero."
    return f"The age coefficient is {estimate:+.3f} bits per month, corresponding to {meaning}.{interval}{certainty}"


def why_text(category: str) -> str:
    return {
        "primary": "This directly answers one of the three frozen scientific questions and is the first model to inspect.",
        "age_shape": "This checks whether a straight monthly trend hides curvature or age-bin changes; it does not replace the primary model.",
        "robustness": "This asks whether the primary conclusion depends on a different repeated-measures, effort, tail, or mixed-model assumption.",
        "context": "This checks whether conclusions depend on using one, two, or three preceding caregiver turns.",
        "candidate": "This compares real utterances with same-length random or n-gram controls. These candidates are not meaning-preserving alternatives.",
        "caregiver": "This describes how caregiver input varies with child age. It is not an adult developmental endpoint.",
        "other": "This is an additional diagnostic specification.",
    }[category]


def read_models(
    *, scorer: str, model_path: Path, coefficient_path: Path
) -> list[dict[str, object]]:
    summaries = pd.read_csv(model_path)
    coefficients = pd.read_csv(coefficient_path)
    key_terms = coefficients[
        coefficients["term"].astype(str).str.contains("age", case=False, regex=False)
    ]
    grouped_terms: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for key, group in key_terms.groupby(["scope", "model_id", "role"], observed=True):
        grouped_terms[key] = [
            {
                "term": str(term.term),
                "estimate": finite(term.estimate),
                "low": finite(term.ci_low),
                "high": finite(term.ci_high),
            }
            for term in group.itertuples()
        ]
    records = []
    for row in summaries.to_dict("records"):
        model_id = str(row["model_id"])
        role = str(row["role"])
        category = model_category(model_id, role)
        key = (str(row["scope"]), model_id, role)
        records.append(
            {
                "scorer": scorer,
                "scorer_label": "TinyDialogues" if scorer == "tiny" else "Mistral",
                "scope": str(row["scope"]),
                "scope_label": SCOPES.get(str(row["scope"]), str(row["scope"])),
                "model_id": model_id,
                "title": model_title(model_id, str(row["outcome"]), category),
                "category": category,
                "category_label": category_label(category),
                "role": role,
                "outcome": str(row["outcome"]),
                "outcome_label": OUTCOMES.get(str(row["outcome"]), str(row["outcome"])),
                "question": model_question(str(row["outcome"]), category, role),
                "answer": result_text(row),
                "why": why_text(category),
                "estimator": str(row["estimator"]),
                "estimator_label": ESTIMATORS.get(str(row["estimator"]), str(row["estimator"]).replace("_", " ")),
                "formula": str(row["formula"]),
                "controls": controls_text(str(row["formula"]), str(row["estimator"]), row.get("weighting_note")),
                "rows": int(row["source_rows"]),
                "cells": int(row["design_cells"]),
                "children": int(row["children"]),
                "corpora": int(row["corpora"]),
                "estimate": finite(row.get("age_estimate")),
                "low": finite(row.get("age_ci_low")),
                "high": finite(row.get("age_ci_high")),
                "p_value": finite(row.get("age_p_value")),
                "status": str(row["fit_status"]),
                "warnings": "" if clean(row.get("warnings")) is None else str(row["warnings"]),
                "protocol": "" if clean(row.get("protocol_result")) is None else str(row["protocol_result"]),
                "key_terms": grouped_terms.get(key, []),
            }
        )
    return records


PLOT_DESCRIPTIONS = {
    "headline_primary_age_slopes.png": ("Primary results", "The three frozen age slopes and their uncertainty intervals."),
    "raw_age_bin_trajectories.png": ("Raw patterns", "Unadjusted age-bin distributions before fitting fixed-effort models."),
    "p1_estimator_robustness.png": ("Model robustness", "How the P1 estimate changes across regression and repeated-measures specifications."),
    "p1_resampling_checks.png": ("Uncertainty", "Child bootstrap, corpus bootstrap, and within-child age-permutation checks."),
    "p1_influence_ranges.png": ("Influence", "How much the P1 estimate changes when one child or corpus is removed."),
    "p1_age_bin_contrasts.png": ("Age shape", "Fixed-effort differences from the earliest age bin."),
    "candidate_gap_age_slopes.png": ("Generated candidates", "Developmental slopes for random and n-gram candidate-minus-real gaps."),
    "child_slope_distribution.png": ("Children", "Distribution of supported child-specific developmental slopes."),
    "child_caretaker_trajectories.png": ("Caregiver input", "Child outcomes and caregiver-input trajectories shown separately."),
    "model_family_coverage.png": ("Coverage", "Which model families are complete, warning-bearing, partial, pending, or unavailable."),
    "paired_all_outcome_slopes.png": ("Scorer comparison", "TinyDialogues versus Mistral developmental slopes for all paired outcomes."),
    "paired_slope_difference_forest.png": ("Scorer comparison", "Paired child-bootstrap intervals for TinyDialogues-minus-Mistral slope differences."),
    "paired_child_p1_concordance.png": ("Children", "Child-by-child agreement in the P1 developmental direction."),
    "paired_p1_age_bins.png": ("Age shape", "Whether the paired PBM P1 age-bin patterns have similar shapes."),
    "paired_quadratic_age_differences.png": ("Age shape", "Paired differences in quadratic age curvature."),
    "paired_candidate_gap_ordering.png": ("Generated candidates", "Whether candidate ordering is consistent across scorers and age bins."),
    "paired_tokenization_diagnostics.png": ("Scale diagnostics", "Recorded evaluated-token counts and lexical-word-normalized score-scale differences."),
}


def relative_url(path: Path, output: Path) -> str:
    return Path(os.path.relpath(path.resolve(), output.parent.resolve())).as_posix()


def plot_records(output: Path) -> list[dict[str, str]]:
    groups = {
        "tiny": ROOT / "figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual",
        "mistral": ROOT / "figs/direct_surprisal_replication/mistral_full79/modular_visual",
        "paired": ROOT / "figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual",
    }
    labels = {"tiny": "TinyDialogues PBM", "mistral": "Mistral full-79", "paired": "Paired scorers"}
    records = []
    for group, directory in groups.items():
        for path in sorted(directory.glob("*.png")):
            if path.name.startswith("coverage_"):
                topic, description = "Coverage", "Observed child-by-age coverage; darker cells contain more utterances."
            else:
                topic, description = PLOT_DESCRIPTIONS.get(path.name, ("Other", path.stem.replace("_", " ")))
            records.append(
                {
                    "group": group,
                    "group_label": labels[group],
                    "topic": topic,
                    "title": path.stem.replace("_", " ").title(),
                    "description": description,
                    "path": relative_url(path, output),
                }
            )
    return records


def profile_records(*, scorer: str, path: Path, output: Path) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    records = []
    for row in frame.to_dict("records"):
        plot_path = Path(str(row["plot"]))
        if not plot_path.is_absolute():
            plot_path = ROOT / plot_path
        records.append(
            {
                "scorer": scorer,
                "scorer_label": "TinyDialogues" if scorer == "tiny" else "Mistral",
                "scope": str(row["scope"]),
                "scope_label": SCOPES.get(str(row["scope"]), str(row["scope"])),
                "dataset": str(row["dataset"]),
                "child_id": str(row["child_id"]),
                "child_key": str(row["child_key"]),
                "utterances": int(row["utterances"]),
                "points": int(row["trajectory_points"]),
                "supported": bool(row["slope_supported"]),
                "plot": relative_url(plot_path, output),
            }
        )
    return records


def coverage_records(*, scorer: str, path: Path) -> list[dict[str, str]]:
    frame = pd.read_csv(path)
    return [
        {
            "scorer": scorer,
            "scorer_label": "TinyDialogues" if scorer == "tiny" else "Mistral",
            "family": str(row.model_family),
            "status": str(row.status),
            "reason": str(row.reason),
        }
        for row in frame.itertuples()
    ]


def paired_records(slopes_path: Path, quadratic_path: Path, rankings_path: Path) -> dict[str, object]:
    slopes = pd.read_csv(slopes_path)
    quadratic = pd.read_csv(quadratic_path)
    rankings = pd.read_csv(rankings_path)
    return {
        "slopes": [{key: clean(value) for key, value in row.items()} for row in slopes.to_dict("records")],
        "quadratic": [{key: clean(value) for key, value in row.items()} for row in quadratic.to_dict("records")],
        "ranking_consistent": bool(
            rankings.groupby(["scorer", "age_bin"], observed=True)["candidate"].count().eq(4).all()
            and rankings.groupby(["age_bin", "candidate"], observed=True)["predictability_rank_within_scorer_age"].nunique().eq(1).all()
        ),
    }


CSS = r"""
:root{--ink:#18242a;--muted:#64737a;--paper:#fff;--wash:#f3f6f5;--line:#d9e2df;--teal:#16666c;--teal2:#dff0ee;--orange:#b85f2c;--orange2:#fff0e6;--red:#a43f45;--green:#28734e;--purple:#6e5796;--shadow:0 16px 45px rgba(28,49,53,.12)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--wash);color:var(--ink);font:16px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}button,select,input{font:inherit}a{color:var(--teal)}
.hero{background:linear-gradient(125deg,#103f44,#1a6d70 58%,#d37238);color:#fff;padding:54px max(24px,calc((100vw - 1240px)/2)) 48px}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:.76rem;font-weight:800;opacity:.78}.hero h1{font-size:clamp(2.1rem,5vw,4.25rem);line-height:1.02;margin:.25em 0 .25em;max-width:920px}.hero p{font-size:1.15rem;max-width:760px;margin:.4em 0 1.2em;opacity:.9}.hero-actions{display:flex;gap:10px;flex-wrap:wrap}.hero a{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.55);padding:10px 15px;border-radius:999px;font-weight:700}.hero a.primary{background:#fff;color:#14565b;border-color:#fff}
.page{max-width:1240px;margin:0 auto;padding:0 24px 70px}.jump{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);margin:0 -24px;padding:10px max(24px,calc((100vw - 1240px)/2));display:flex;gap:8px;overflow:auto}.jump a{white-space:nowrap;text-decoration:none;color:var(--ink);padding:7px 11px;border-radius:8px;font-weight:700;font-size:.9rem}.jump a:hover{background:var(--teal2);color:var(--teal)}
section{scroll-margin-top:72px;padding-top:54px}.section-head{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:20px}.section-head h2{font-size:2rem;line-height:1.1;margin:0}.section-head p{max-width:650px;color:var(--muted);margin:0}.callout{border-left:5px solid var(--orange);background:var(--orange2);padding:16px 19px;border-radius:0 12px 12px 0;margin:18px 0}.callout strong{color:#843d17}
.finding-grid,.sample-grid,.coverage-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.finding,.sample-card,.coverage-card{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 4px 14px rgba(30,52,55,.05)}.finding .number{font-size:2rem;font-weight:850;color:var(--teal);line-height:1}.finding h3,.sample-card h3{margin:.55em 0 .35em;font-size:1.1rem}.finding p,.sample-card p{margin:0;color:var(--muted)}.sample-card .big{font-size:2.2rem;font-weight:850;line-height:1;color:var(--purple)}
.model-map{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:15px}.model-map button,.chip{border:1px solid var(--line);background:#fff;color:var(--ink);padding:8px 12px;border-radius:999px;cursor:pointer;font-weight:700}.model-map button:hover,.model-map button.active,.chip.active{background:var(--teal);border-color:var(--teal);color:#fff}.filters{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px;display:grid;grid-template-columns:2fr repeat(4,1fr);gap:10px;margin-bottom:16px;box-shadow:0 5px 18px rgba(30,52,55,.05)}.filters label{font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800;color:var(--muted)}.filters input,.filters select{width:100%;border:1px solid #bccac7;border-radius:9px;padding:9px 10px;margin-top:5px;background:#fff;color:var(--ink)}.results-meta{color:var(--muted);margin:10px 2px 14px}.model-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.model-card{background:#fff;border:1px solid var(--line);border-radius:17px;padding:19px;box-shadow:0 5px 17px rgba(30,52,55,.06);display:flex;flex-direction:column;gap:11px}.card-top{display:flex;justify-content:space-between;gap:12px;align-items:start}.badges{display:flex;gap:6px;flex-wrap:wrap}.badge{font-size:.72rem;font-weight:850;text-transform:uppercase;letter-spacing:.055em;padding:5px 8px;border-radius:999px;background:var(--teal2);color:var(--teal)}.badge.status-pass{background:#e7f4eb;color:var(--green)}.badge.status-warning{background:#fff0e6;color:#914717}.model-id{font:700 .75rem ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}.model-card h3{font-size:1.22rem;line-height:1.2;margin:0}.question{font-weight:750}.answer{background:#f6f8f7;border-radius:11px;padding:12px 13px;color:#33444a}.ci{height:46px;position:relative;margin:1px 4px}.ci .axis{position:absolute;left:0;right:0;top:20px;height:2px;background:#ced8d5}.ci .zero{position:absolute;top:8px;bottom:8px;width:1px;background:#75847f}.ci .interval{position:absolute;top:17px;height:7px;background:var(--purple);border-radius:8px}.ci .point{position:absolute;top:12px;width:16px;height:16px;border-radius:50%;background:var(--purple);transform:translateX(-50%);border:3px solid #fff;box-shadow:0 0 0 1px var(--purple)}.ci .leftlabel,.ci .rightlabel{position:absolute;top:29px;font-size:.7rem;color:var(--muted)}.ci .rightlabel{right:0}.why{color:var(--muted);font-size:.92rem}.model-card details{border-top:1px solid var(--line);padding-top:10px}.model-card summary{cursor:pointer;font-weight:800;color:var(--teal)}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}.detail{background:var(--wash);padding:10px;border-radius:9px}.detail b{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:3px}.formula{font:13px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere;background:#17272c;color:#e9f3f1;border-radius:9px;padding:12px;margin-top:10px}.term-list{margin:8px 0 0;padding-left:18px}.warning{color:#8d3a22;background:#fff1e8;border-radius:9px;padding:10px;margin-top:10px}
.paired-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.paired-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}.paired-card h3{margin:0 0 6px}.paired-card .delta{font-size:1.8rem;font-weight:850;color:var(--purple)}
.gallery-controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.plot-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.plot-card{background:#fff;border:1px solid var(--line);border-radius:15px;overflow:hidden;cursor:pointer;box-shadow:0 5px 16px rgba(30,52,55,.06)}.plot-card img{width:100%;height:205px;object-fit:contain;background:#fff;border-bottom:1px solid var(--line)}.plot-card .copy{padding:13px}.plot-card h3{font-size:1rem;margin:0 0 4px}.plot-card p{font-size:.88rem;color:var(--muted);margin:0}.plot-card .source{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--teal);font-weight:850}
.child-layout{display:grid;grid-template-columns:330px 1fr;gap:16px;align-items:start}.child-controls,.child-viewer{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px}.child-controls{position:sticky;top:64px}.child-controls select,.child-controls input{width:100%;margin:4px 0 9px;padding:9px;border:1px solid #bccac7;border-radius:8px}.child-list{max-height:520px;overflow:auto;border-top:1px solid var(--line);margin-top:8px;padding-top:8px}.child-button{display:block;width:100%;text-align:left;border:0;background:transparent;padding:9px;border-radius:8px;cursor:pointer}.child-button:hover,.child-button.active{background:var(--teal2);color:var(--teal)}.child-viewer img{width:100%;max-height:720px;object-fit:contain}.child-meta{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 12px}.child-meta span{background:var(--wash);padding:6px 9px;border-radius:8px;color:var(--muted);font-size:.85rem}
.coverage-grid{grid-template-columns:1fr 1fr}.coverage-card{padding:0;overflow:hidden}.coverage-card h3{margin:0;padding:17px 18px;background:#eaf2f0}.coverage-row{display:grid;grid-template-columns:1fr auto;gap:8px;padding:12px 17px;border-top:1px solid var(--line)}.coverage-row p{grid-column:1/-1;margin:0;color:var(--muted);font-size:.87rem}.status{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;font-weight:850;border-radius:999px;padding:4px 7px}.status.complete{color:var(--green);background:#e7f4eb}.status.partial,.status.complete-with-warnings{color:#95501e;background:#fff0e3}.status.pending{color:#70538e;background:#f1eafa}.status.unavailable{color:#7a4146;background:#f8e8ea}
.glossary details{background:#fff;border:1px solid var(--line);border-radius:11px;margin:8px 0;padding:12px 14px}.glossary summary{font-weight:850;cursor:pointer}.glossary p{color:var(--muted);margin:.6em 0 .2em}.empty{grid-column:1/-1;background:#fff;border:1px dashed #aab9b5;border-radius:14px;padding:30px;text-align:center;color:var(--muted)}
.modal{display:none;position:fixed;inset:0;background:rgba(7,17,20,.86);z-index:100;padding:30px}.modal.open{display:flex;align-items:center;justify-content:center}.modal-inner{background:#fff;border-radius:14px;max-width:96vw;max-height:94vh;padding:14px;position:relative}.modal img{max-width:92vw;max-height:82vh;display:block}.modal button{position:absolute;right:12px;top:10px;border:0;border-radius:999px;background:#17272c;color:#fff;width:38px;height:38px;font-size:1.3rem;cursor:pointer}.modal h3{margin:10px 44px 2px 4px}.modal p{margin:3px 4px;color:var(--muted)}
footer{background:#17272c;color:#dfe9e7;padding:35px max(24px,calc((100vw - 1240px)/2));margin-top:50px}footer p{max-width:780px;margin:.3em 0;color:#b9c9c6}
@media(max-width:900px){.finding-grid,.sample-grid,.plot-grid,.paired-strip{grid-template-columns:1fr 1fr}.model-list{grid-template-columns:1fr}.filters{grid-template-columns:1fr 1fr}.filters .search{grid-column:1/-1}.child-layout{grid-template-columns:1fr}.child-controls{position:static}.coverage-grid{grid-template-columns:1fr}}
@media(max-width:580px){.page{padding-left:14px;padding-right:14px}.finding-grid,.sample-grid,.plot-grid,.paired-strip{grid-template-columns:1fr}.filters{grid-template-columns:1fr}.section-head{display:block}.section-head p{margin-top:8px}.detail-grid{grid-template-columns:1fr}.hero{padding-left:18px;padding-right:18px}.jump{margin-left:-14px;margin-right:-14px}.plot-card img{height:auto}}
"""


JS = r"""
const data=APP_DATA;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmt=v=>Number.isFinite(Number(v))?Number(v).toFixed(3):'—';
function ciPlot(m){if(m.estimate===null||m.low===null||m.high===null)return '';
 const extent=Math.max(Math.abs(m.low),Math.abs(m.high),Math.abs(m.estimate),.001)*1.18;
 const x=v=>((v+extent)/(2*extent))*100; return `<div class="ci" aria-label="Estimate ${fmt(m.estimate)}, interval ${fmt(m.low)} to ${fmt(m.high)}"><div class="axis"></div><div class="zero" style="left:${x(0)}%"></div><div class="interval" style="left:${x(m.low)}%;width:${Math.max(.5,x(m.high)-x(m.low))}%"></div><div class="point" style="left:${x(m.estimate)}%"></div><span class="leftlabel">${fmt(-extent)}</span><span class="rightlabel">+${fmt(extent)}</span></div>`}
function termList(terms){if(!terms?.length)return '<p>No single age term is stored for this specification.</p>';return `<ul class="term-list">${terms.map(t=>`<li><code>${esc(t.term)}</code>: ${fmt(t.estimate)} [${fmt(t.low)}, ${fmt(t.high)}]</li>`).join('')}</ul>`}
function modelCard(m){const warn=m.status==='PASS'?'status-pass':'status-warning';return `<article class="model-card"><div class="card-top"><div class="badges"><span class="badge">${esc(m.category_label)}</span><span class="badge">${esc(m.scorer_label)}</span><span class="badge">${esc(m.scope_label)}</span><span class="badge ${warn}">${esc(m.status)}</span></div><span class="model-id">${esc(m.model_id)}</span></div><h3>${esc(m.title)}</h3><div class="question">${esc(m.question)}</div><div class="answer">${esc(m.answer)}</div>${ciPlot(m)}<div class="why"><b>Why fit it?</b> ${esc(m.why)}</div><details><summary>See the actual model</summary><div class="detail-grid"><div class="detail"><b>Sample</b>${esc(m.scope_label)}</div><div class="detail"><b>Estimator</b>${esc(m.estimator_label)}</div><div class="detail"><b>Data</b>${m.rows.toLocaleString()} utterances → ${m.cells.toLocaleString()} design cells</div><div class="detail"><b>Clusters</b>${m.children} children · ${m.corpora} corpora</div><div class="detail"><b>Controls</b>${esc(m.controls)}</div><div class="detail"><b>Protocol reading</b>${esc(m.protocol||'Sensitivity/no directional decision rule')}</div></div><div class="formula">${esc(m.formula)}</div><b>Key age terms</b>${termList(m.key_terms)}${m.warnings?`<div class="warning"><b>Recorded warning:</b> ${esc(m.warnings)}</div>`:''}</details></article>`}
function renderModels(){const q=$('#modelSearch').value.toLowerCase(), scorer=$('#modelScorer').value, scope=$('#modelScope').value, category=$('#modelCategory').value, role=$('#modelRole').value, status=$('#modelStatus').value;
 const rows=data.models.filter(m=>(scorer==='all'||m.scorer===scorer)&&(scope==='all'||m.scope===scope)&&(category==='all'||m.category===category)&&(role==='all'||m.role===role)&&(status==='all'||(status==='warnings'?m.status!=='PASS':m.status===status))&&(!q||JSON.stringify(m).toLowerCase().includes(q)));
 $('#modelCount').textContent=`Showing ${rows.length} of ${data.models.length} fitted model records`;
 $('#modelList').innerHTML=rows.length?rows.map(modelCard).join(''):'<div class="empty">No models match these filters.</div>';
 $$('.model-map button').forEach(b=>b.classList.toggle('active',b.dataset.category===category));}
['modelSearch','modelScorer','modelScope','modelCategory','modelRole','modelStatus'].forEach(id=>$('#'+id).addEventListener(id==='modelSearch'?'input':'change',renderModels));
$$('.model-map button').forEach(b=>b.addEventListener('click',()=>{$('#modelCategory').value=b.dataset.category;renderModels();document.querySelector('#models').scrollIntoView()}));
function renderPaired(){const wanted=['real_k3_sum_bits','real_k0_sum_bits','real_context_gain_k3'];const rows=data.paired.slopes.filter(r=>wanted.includes(r.outcome));$('#pairedCards').innerHTML=rows.map(r=>`<article class="paired-card"><h3>${esc(r.label)}</h3><div class="delta">${fmt(r.slope_difference_left_minus_right)}</div><p>Tiny minus Mistral slope</p><p>Paired 95% interval: ${fmt(r.difference_ci_low)} to ${fmt(r.difference_ci_high)}</p><p>Tiny ${fmt(r.slope_tiny)} · Mistral ${fmt(r.slope_mistral)}</p></article>`).join('')}
let plotGroup='all';function renderPlots(){const rows=data.plots.filter(p=>plotGroup==='all'||p.group===plotGroup);$('#plotGrid').innerHTML=rows.map((p,i)=>`<article class="plot-card" data-i="${data.plots.indexOf(p)}"><img loading="lazy" src="${esc(p.path)}" alt="${esc(p.title)}"><div class="copy"><div class="source">${esc(p.group_label)} · ${esc(p.topic)}</div><h3>${esc(p.title)}</h3><p>${esc(p.description)}</p></div></article>`).join('');$$('.plot-card').forEach(c=>c.addEventListener('click',()=>openPlot(data.plots[Number(c.dataset.i)])));}
$$('[data-plot-group]').forEach(b=>b.addEventListener('click',()=>{plotGroup=b.dataset.plotGroup;$$('[data-plot-group]').forEach(x=>x.classList.toggle('active',x===b));renderPlots()}));
function openPlot(p){$('#modalImg').src=p.path;$('#modalTitle').textContent=p.title;$('#modalDescription').textContent=p.description;$('#plotModal').classList.add('open')}
function closeModal(){$('#plotModal').classList.remove('open');$('#modalImg').src=''}$('#modalClose').onclick=closeModal;$('#plotModal').addEventListener('click',e=>{if(e.target.id==='plotModal')closeModal()});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});
let selectedChild=null;function childRows(){const scorer=$('#childScorer').value,scope=$('#childScope').value,q=$('#childSearch').value.toLowerCase();return data.profiles.filter(p=>p.scorer===scorer&&p.scope===scope&&(!q||p.child_key.toLowerCase().includes(q))).sort((a,b)=>a.child_key.localeCompare(b.child_key))}
function updateScopeOptions(){const scorer=$('#childScorer').value;const scopes=[...new Set(data.profiles.filter(p=>p.scorer===scorer).map(p=>p.scope))];$('#childScope').innerHTML=scopes.map(s=>`<option value="${s}" ${s==='all79_descriptive'?'selected':''}>${esc(data.scopeLabels[s]||s)}</option>`).join('')}
function renderChildren(){const rows=childRows();if(!selectedChild||!rows.some(r=>r.scorer===selectedChild.scorer&&r.scope===selectedChild.scope&&r.child_key===selectedChild.child_key))selectedChild=rows[0]||null;$('#childCount').textContent=`${rows.length} children match`;
 $('#childList').innerHTML=rows.map(p=>`<button class="child-button ${selectedChild&&p.child_key===selectedChild.child_key?'active':''}" data-key="${esc(p.child_key)}">${esc(p.child_key)}</button>`).join('');$$('.child-button').forEach(b=>b.addEventListener('click',()=>{selectedChild=rows.find(p=>p.child_key===b.dataset.key);renderChildren()}));
 if(!selectedChild){$('#childViewer').innerHTML='<div class="empty">No child matches these filters.</div>';return}$('#childViewer').innerHTML=`<h3>${esc(selectedChild.child_key)}</h3><div class="child-meta"><span>${esc(selectedChild.scorer_label)}</span><span>${esc(selectedChild.scope_label)}</span><span>${selectedChild.utterances.toLocaleString()} utterances</span><span>${selectedChild.points} observed age/session cells</span><span>${selectedChild.supported?'Slope supported':'Descriptive only'}</span></div><img src="${esc(selectedChild.plot)}" alt="Trajectory for ${esc(selectedChild.child_key)}"><div class="callout"><strong>How to read it:</strong> Dot size represents the number of utterances. The first three panels put scores on the same two-word reference scale. The red line is drawn only when the support rule is met.</div>`}
$('#childScorer').addEventListener('change',()=>{selectedChild=null;updateScopeOptions();renderChildren()});$('#childScope').addEventListener('change',()=>{selectedChild=null;renderChildren()});$('#childSearch').addEventListener('input',()=>{selectedChild=null;renderChildren()});
function renderCoverage(){for(const scorer of ['tiny','mistral']){const rows=data.coverage.filter(r=>r.scorer===scorer);$(`#coverage-${scorer}`).innerHTML=`<h3>${scorer==='tiny'?'TinyDialogues PBM':'Mistral full-79'}</h3>`+rows.map(r=>`<div class="coverage-row"><b>${esc(r.family)}</b><span class="status ${esc(r.status.replaceAll(' ','-'))}">${esc(r.status)}</span><p>${esc(r.reason)}</p></div>`).join('')}}
renderModels();renderPaired();renderPlots();updateScopeOptions();renderChildren();renderCoverage();
if(location.hash)setTimeout(()=>document.querySelector(location.hash)?.scrollIntoView(),80);
"""


def build_explorer(
    *,
    tiny_models: Path,
    tiny_coefficients: Path,
    tiny_coverage: Path,
    tiny_profiles: Path,
    mistral_models: Path,
    mistral_coefficients: Path,
    mistral_coverage: Path,
    mistral_profiles: Path,
    paired_slopes: Path,
    paired_quadratic: Path,
    paired_rankings: Path,
    output: Path,
) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    models = read_models(scorer="tiny", model_path=tiny_models, coefficient_path=tiny_coefficients)
    models += read_models(scorer="mistral", model_path=mistral_models, coefficient_path=mistral_coefficients)
    profiles = profile_records(scorer="tiny", path=tiny_profiles, output=output)
    profiles += profile_records(scorer="mistral", path=mistral_profiles, output=output)
    coverage = coverage_records(scorer="tiny", path=tiny_coverage)
    coverage += coverage_records(scorer="mistral", path=mistral_coverage)
    app_data = {
        "models": models,
        "plots": plot_records(output),
        "profiles": profiles,
        "coverage": coverage,
        "paired": paired_records(paired_slopes, paired_quadratic, paired_rankings),
        "scopeLabels": SCOPES,
    }
    payload = json.dumps(app_data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Direct-Surprisal Results Explorer</title><style>{CSS}</style></head><body>
<header class="hero"><div class="eyebrow">Communicative efficiency · usable results view</div><h1>See the models, results, plots, and children in one place.</h1><p>This explorer translates the saved statistical artifacts into model cards you can inspect. Start with the three findings, then filter the actual fitted models or choose a child.</p><div class="hero-actions"><a class="primary" href="#models">Show me the models</a><a href="#children">Find a child</a><a href="#plots">Browse plots</a></div></header>
<main class="page"><nav class="jump"><a href="#start">Start here</a><a href="#samples">Samples</a><a href="#models">Models</a><a href="#paired">Scorer comparison</a><a href="#plots">Plots</a><a href="#children">Children</a><a href="#coverage">Coverage</a><a href="#glossary">Glossary</a></nav>
<section id="start"><div class="section-head"><div><div class="eyebrow">Read this first</div><h2>The three findings in plain language</h2></div><p>These are developmental associations under the scorers—not proof that children optimize one universal efficiency objective.</p></div>
<div class="finding-grid"><article class="finding"><div class="number">1</div><h3>PBM slopes are clearly negative under both scorers.</h3><p>At the same lexical word count, older PBM children's real utterances receive lower contextual surprisal: TinyDialogues −0.222 and Mistral −0.131 bits/month.</p></article><article class="finding"><div class="number">2</div><h3>The held-out-sample confirmation is not decisive.</h3><p>The 58 non-PBM children have a Mistral slope of −0.062, but the frozen primary interval is −0.132 to +0.007. It points negative but crosses zero.</p></article><article class="finding"><div class="number">3</div><h3>Context support decreases rather than increases.</h3><p>The k0−k3 context-support slope is negative in Tiny PBM, Mistral PBM, and non-PBM Mistral. That is opposite the frozen positive prediction.</p></article></div>
<div class="callout"><strong>Most important distinction:</strong> lower target surprisal means the scorer finds an utterance more predictable. It does not mean the utterance contains “less communication,” and it is not sufficient by itself to prove communicative efficiency.</div></section>
<section id="samples"><div class="section-head"><div><div class="eyebrow">What was analyzed</div><h2>Four samples with different jobs</h2></div><p>Discovery, scorer robustness, confirmation, and pooled description must not be mixed into one claim.</p></div><div class="sample-grid"><article class="sample-card"><div class="big">21</div><h3>TinyDialogues PBM</h3><p>Same Brown, Manchester, and Providence discovery children. This tests scorer robustness, not a new child sample.</p></article><article class="sample-card"><div class="big">21</div><h3>Mistral PBM</h3><p>The discovery estimate under the original scorer.</p></article><article class="sample-card"><div class="big">58</div><h3>Mistral non-PBM</h3><p>The prespecified confirmation sample from the other ten corpora.</p></article><article class="sample-card"><div class="big">79</div><h3>Mistral all children</h3><p>A useful descriptive overview, but not the confirmation estimate because it pools discovery and confirmation.</p></article></div></section>
<section id="models"><div class="section-head"><div><div class="eyebrow">The actual fitted models</div><h2>Model explorer</h2></div><p>Default: the primary models. Use the large buttons for model families, then expand any card to see its formula, estimator, controls, sample, key coefficients, and warnings.</p></div>
<div class="model-map"><button data-category="primary" class="active">Primary questions</button><button data-category="age_shape">Age shape</button><button data-category="robustness">Robustness</button><button data-category="context">Context windows</button><button data-category="candidate">Generated candidates</button><button data-category="caregiver">Caregiver input</button><button data-category="all">Everything</button></div>
<div class="filters"><div class="search"><label>Search models<input id="modelSearch" placeholder="Try: context gain, mixed, trigram…"></label></div><label>Scorer<select id="modelScorer"><option value="all">Both</option><option value="tiny">TinyDialogues</option><option value="mistral">Mistral</option></select></label><label>Sample<select id="modelScope"><option value="all">All samples</option><option value="pbm_discovery">PBM discovery</option><option value="non_pbm_confirmation">Non-PBM confirmation</option><option value="all79_descriptive">All 79 descriptive</option></select></label><label>Family<select id="modelCategory"><option value="primary">Primary questions</option><option value="age_shape">Age shape</option><option value="robustness">Robustness</option><option value="context">Context windows</option><option value="candidate">Generated candidates</option><option value="caregiver">Caregiver input</option><option value="all">Everything</option></select></label><label>Fit status<select id="modelStatus"><option value="all">All statuses</option><option value="PASS">Pass</option><option value="warnings">Warnings/nonconvergence</option></select></label><label style="display:none">Role<select id="modelRole"><option value="all">All</option></select></label></div><div class="results-meta" id="modelCount"></div><div class="model-list" id="modelList"></div></section>
<section id="paired"><div class="section-head"><div><div class="eyebrow">Same utterances, two scorers</div><h2>What changes between TinyDialogues and Mistral?</h2></div><p>Differences are TinyDialogues minus Mistral age slopes, with whole-child paired bootstrap intervals.</p></div><div class="paired-strip" id="pairedCards"></div><div class="callout"><strong>Child-level agreement:</strong> 18 of 21 supported PBM children have the same P1 slope sign under both scorers. Candidate ordering is {"consistent in every age bin" if app_data['paired']['ranking_consistent'] else "not fully consistent"}.</div></section>
<section id="plots"><div class="section-head"><div><div class="eyebrow">Visual evidence</div><h2>Plot browser</h2></div><p>Click any plot to enlarge it. The descriptions state what each figure is meant to answer.</p></div><div class="gallery-controls"><button class="chip active" data-plot-group="all">All plots</button><button class="chip" data-plot-group="tiny">TinyDialogues</button><button class="chip" data-plot-group="mistral">Mistral</button><button class="chip" data-plot-group="paired">Paired scorers</button></div><div class="plot-grid" id="plotGrid"></div></section>
<section id="children"><div class="section-head"><div><div class="eyebrow">Individual trajectories</div><h2>Find any child</h2></div><p>Select a scorer and scientific scope, then search by corpus or child name. Only one large, readable trajectory is shown at a time.</p></div><div class="child-layout"><aside class="child-controls"><label>Scorer<select id="childScorer"><option value="mistral">Mistral</option><option value="tiny">TinyDialogues</option></select></label><label>Sample<select id="childScope"></select></label><label>Search<input id="childSearch" placeholder="e.g. Wells or Adam"></label><div id="childCount" class="results-meta"></div><div id="childList" class="child-list"></div></aside><div id="childViewer" class="child-viewer"></div></div></section>
<section id="coverage"><div class="section-head"><div><div class="eyebrow">What exists and what does not</div><h2>Model-family coverage</h2></div><p>“Unavailable” means the needed scorer-specific data do not exist. It is not a failed regression hidden from the report.</p></div><div class="coverage-grid"><div class="coverage-card" id="coverage-tiny"></div><div class="coverage-card" id="coverage-mistral"></div></div></section>
<section id="glossary"><div class="section-head"><div><div class="eyebrow">No statistical decoding required</div><h2>Glossary</h2></div></div><div class="glossary"><details open><summary>Surprisal / target self-information</summary><p><code>−log₂ p(utterance | context)</code>. Lower values mean the scorer expected the observed utterance more strongly.</p></details><details><summary>Fixed effort</summary><p>The regression compares utterances at the same measured lexical word count. It does not claim that word count captures every kind of production effort.</p></details><details><summary>Age slope</summary><p>The estimated score change for one additional month of child age. A slope of −0.10 means 0.10 fewer bits per month at the same modeled effort.</p></details><details><summary>95% interval</summary><p>A child-clustered uncertainty interval for the primary fit. If it crosses zero, the estimated direction is not decisive under that uncertainty calculation.</p></details><details><summary>Child fixed effects</summary><p>The model gives every child their own baseline, so the age slope is identified from developmental changes within children rather than only differences between children.</p></details><details><summary>Context support / context gain</summary><p><code>k0 − k3</code>: how much the preceding caregiver context reduces surprisal for the observed utterance. A negative developmental slope means this support decreases with age.</p></details><details><summary>Primary versus sensitivity model</summary><p>The primary model implements the frozen decision rule. Sensitivity models change the age form, effort form, repeated-measures estimator, tail treatment, or random-effects structure to test dependence on assumptions.</p></details></div></section></main>
<div class="modal" id="plotModal"><div class="modal-inner"><button id="modalClose" aria-label="Close">×</button><img id="modalImg" alt=""><h3 id="modalTitle"></h3><p id="modalDescription"></p></div></div>
<footer><b>Direct-Surprisal Results Explorer</b><p>Generated entirely from saved model summaries, coefficient tables, plot audits, and child-profile manifests. No model is refit when this page is rebuilt.</p></footer>
<script>const APP_DATA={payload};{JS}</script></body></html>"""
    output.write_text(page, encoding="utf-8")
    return {
        "output": str(output),
        "models": len(models),
        "plots": len(app_data["plots"]),
        "profiles": len(profiles),
        "coverage_rows": len(coverage),
        "bytes": output.stat().st_size,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in DEFAULTS.items():
        parser.add_argument("--" + name.replace("_", "-"), type=Path, default=default)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    result = build_explorer(**vars(args))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
