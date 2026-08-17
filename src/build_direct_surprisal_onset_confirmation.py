#!/usr/bin/env python3
"""Apply the frozen sustained-onset rule with child-bootstrap bands.

This analysis consumes the immutable exact/top-coded word design cells from
the modular direct-surprisal workflow. It fits the same additive age-bin,
word-bin, and child-fixed-effects mean structure, then resamples children and
constructs a simultaneous max-|t| bootstrap band over the seven post-reference
age-bin contrasts.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


AGE_ORDER = [
    "006-023", "024-029", "030-035", "036-041",
    "042-047", "048-053", "054-059", "060-065",
]
POST_AGE_BINS = AGE_ORDER[1:]
DEFAULT_INPUT_ROOT = Path(
    "results/direct_surprisal_replication/mistral_full79/modular/prepared/design_cells/child"
)
DEFAULT_COEFFICIENTS = Path(
    "results/direct_surprisal_replication/mistral_full79/modular/models/coefficients_long.csv"
)
DEFAULT_OUTPUT_DIR = Path("results/direct_surprisal_onset_confirmation")
DEFAULT_FIG_DIR = Path("figs/direct_surprisal_onset_confirmation")
DEFAULT_DOC_MD = Path("docs/direct_surprisal_onset_confirmation.md")
DEFAULT_DOC_HTML = Path("docs/direct_surprisal_onset_confirmation.html")
SCOPES = ("pbm_discovery", "non_pbm_confirmation")


def _word_sort(value: str) -> tuple[int, str]:
    text = str(value)
    number = "".join(character for character in text if character.isdigit())
    return (int(number) if number else 10_000, text)


def _within_child_crossproducts(
    frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, list[str], list[str], np.ndarray]:
    """Return per-child crossproducts after weighted child demeaning."""

    data = frame.copy()
    data["age_bin"] = pd.Categorical(data["age_bin"], categories=AGE_ORDER, ordered=True)
    word_levels = sorted(data["word_count_exact_top12"].astype(str).unique(), key=_word_sort)
    data["word_count_exact_top12"] = pd.Categorical(
        data["word_count_exact_top12"].astype(str), categories=word_levels, ordered=True
    )
    age_dummies = pd.get_dummies(data["age_bin"], prefix="age", dtype=float)[
        [f"age_{age}" for age in POST_AGE_BINS]
    ]
    word_dummies = pd.get_dummies(data["word_count_exact_top12"], prefix="word", dtype=float)
    if len(word_dummies.columns) > 1:
        word_dummies = word_dummies.iloc[:, 1:]
    else:
        word_dummies = word_dummies.iloc[:, 0:0]
    design = pd.concat([age_dummies, word_dummies], axis=1)
    names = list(design.columns)
    x = design.to_numpy(dtype=float)
    y = pd.to_numeric(data["outcome_mean"], errors="raise").to_numpy(dtype=float)
    weights = pd.to_numeric(data["row_count"], errors="raise").to_numpy(dtype=float)
    child_values = data["child_key"].astype(str).to_numpy()
    children = sorted(set(child_values))
    p = x.shape[1]
    cross_xx = np.zeros((len(children), p, p), dtype=float)
    cross_xy = np.zeros((len(children), p), dtype=float)
    child_rows = np.zeros(len(children), dtype=float)
    for child_index, child in enumerate(children):
        mask = child_values == child
        xc = x[mask]
        yc = y[mask]
        wc = weights[mask]
        total = float(wc.sum())
        if total <= 0:
            continue
        x_mean = np.average(xc, axis=0, weights=wc)
        y_mean = float(np.average(yc, weights=wc))
        x_within = xc - x_mean
        y_within = yc - y_mean
        cross_xx[child_index] = x_within.T @ (wc[:, None] * x_within)
        cross_xy[child_index] = x_within.T @ (wc * y_within)
        child_rows[child_index] = total
    return cross_xx, cross_xy, names, children, child_rows


def _solve(xx: np.ndarray, xy: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(xx, xy, rcond=None)[0]


def fit_bootstrap_bands(
    frame: pd.DataFrame,
    *,
    reps: int,
    seed: int,
    min_children: int = 5,
    min_corpora: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Fit contrasts and a simultaneous child-bootstrap max-|t| band."""

    cross_xx, cross_xy, names, children, child_rows = _within_child_crossproducts(frame)
    point = _solve(cross_xx.sum(axis=0), cross_xy.sum(axis=0))
    age_indices = [names.index(f"age_{age}") for age in POST_AGE_BINS]
    point_age = point[age_indices]
    rng = np.random.default_rng(seed)
    draws = np.empty((reps, len(POST_AGE_BINS)), dtype=float)
    successful = 0
    for rep in range(reps):
        multiplicities = rng.multinomial(len(children), np.full(len(children), 1 / len(children)))
        xx = np.tensordot(multiplicities, cross_xx, axes=(0, 0))
        xy = np.tensordot(multiplicities, cross_xy, axes=(0, 0))
        beta = _solve(xx, xy)
        age_values = beta[age_indices]
        if np.isfinite(age_values).all():
            draws[successful] = age_values
            successful += 1
    draws = draws[:successful]
    if successful < max(50, int(0.9 * reps)):
        raise RuntimeError(f"Only {successful}/{reps} child-bootstrap fits were finite")

    bootstrap_se = draws.std(axis=0, ddof=1)
    valid_se = np.isfinite(bootstrap_se) & (bootstrap_se > 0)
    standardized = np.full_like(draws, np.nan)
    standardized[:, valid_se] = np.abs(
        (draws[:, valid_se] - point_age[valid_se]) / bootstrap_se[valid_se]
    )
    max_t = np.nanmax(standardized, axis=1)
    critical = float(np.quantile(max_t, 0.95))

    support_rows: list[dict[str, object]] = []
    contrast_rows: list[dict[str, object]] = []
    data = frame.copy()
    data["dataset"] = data["child_key"].astype(str).str.split("/", n=1).str[0]
    for index, age in enumerate(POST_AGE_BINS):
        subset = data[data["age_bin"].astype(str) == age]
        child_count = int(subset["child_key"].nunique())
        corpus_count = int(subset["dataset"].nunique())
        supported = child_count >= min_children and corpus_count >= min_corpora
        simultaneous_low = float(point_age[index] - critical * bootstrap_se[index])
        simultaneous_high = float(point_age[index] + critical * bootstrap_se[index])
        support_rows.append(
            {
                "age_bin": age,
                "children": child_count,
                "corpora": corpus_count,
                "minimum_children": min_children,
                "minimum_corpora": min_corpora,
                "adequately_supported": int(supported),
            }
        )
        contrast_rows.append(
            {
                "age_bin": age,
                "estimate_vs_006_023": float(point_age[index]),
                "bootstrap_se": float(bootstrap_se[index]),
                "percentile_ci_low": float(np.quantile(draws[:, index], 0.025)),
                "percentile_ci_high": float(np.quantile(draws[:, index], 0.975)),
                "simultaneous_ci_low": simultaneous_low,
                "simultaneous_ci_high": simultaneous_high,
                "simultaneous_critical_max_t": critical,
                "adequately_supported": int(supported),
            }
        )

    contrasts = pd.DataFrame(contrast_rows)
    support = pd.DataFrame(support_rows)
    supported = contrasts[contrasts["adequately_supported"] == 1].reset_index(drop=True)
    onset = "not_established"
    for candidate_index, candidate in supported.iterrows():
        later = supported.iloc[candidate_index:]
        if bool((later["simultaneous_ci_high"] < 0).all()):
            onset = str(candidate["age_bin"])
            break
    audit = {
        "children": len(children),
        "source_rows": int(frame["row_count"].sum()),
        "design_cells": int(len(frame)),
        "bootstrap_reps_requested": reps,
        "bootstrap_reps_successful": successful,
        "seed": seed,
        "simultaneous_method": "child-resampling bootstrap max-absolute-studentized-deviation",
        "simultaneous_critical_value": critical,
        "sustained_onset": onset,
        "total_child_weight": int(child_rows.sum()),
    }
    draw_frame = pd.DataFrame(draws, columns=POST_AGE_BINS)
    draw_frame.insert(0, "bootstrap_rep", np.arange(successful))
    return contrasts.merge(support, on="age_bin", suffixes=("", "_support")), draw_frame, audit


def _saved_age_contrasts(coefficients: Path, scope: str) -> pd.DataFrame:
    frame = pd.read_csv(coefficients)
    subset = frame[
        (frame["scope"] == scope)
        & (frame["model_id"] == "P1_k3_contextual_age_bins")
        & frame["term"].astype(str).str.contains("C\\(age_bin", regex=True)
    ].copy()
    subset["age_bin"] = subset["term"].str.extract(r"\[T\.([^]]+)\]")
    return subset[["age_bin", "estimate"]]


def _plot(all_contrasts: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5), sharey=False)
    for axis, scope in zip(axes, SCOPES):
        data = all_contrasts[all_contrasts["scope"] == scope].copy()
        x = np.arange(len(data))
        axis.axhline(0, color="#363636", lw=1)
        axis.errorbar(
            x,
            data["estimate_vs_006_023"],
            yerr=np.vstack(
                [
                    data["estimate_vs_006_023"] - data["simultaneous_ci_low"],
                    data["simultaneous_ci_high"] - data["estimate_vs_006_023"],
                ]
            ),
            fmt="o",
            color="#2f6f73" if scope == "pbm_discovery" else "#b45f35",
            capsize=4,
        )
        unsupported = data["adequately_supported"] == 0
        axis.scatter(x[unsupported], data.loc[unsupported, "estimate_vs_006_023"], marker="x", color="#222222", zorder=4)
        axis.set_xticks(x, data["age_bin"], rotation=35, ha="right")
        axis.set_title("PBM discovery" if scope == "pbm_discovery" else "Non-PBM confirmation")
        axis.set_xlabel("Age bin")
        axis.set_ylabel("Fixed-effort contrast vs 006-023 (bits)")
    fig.suptitle("Simultaneous child-bootstrap age-bin bands")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return ""
    return f"{number:.{digits}f}"


def _md_table(frame: pd.DataFrame) -> str:
    columns = [
        "scope", "age_bin", "estimate_vs_006_023", "simultaneous_ci_low",
        "simultaneous_ci_high", "children", "corpora", "adequately_supported",
    ]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].iterrows():
        lines.append("| " + " | ".join(_fmt(row[column]) if column not in {"scope", "age_bin"} else str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def _report(all_contrasts: pd.DataFrame, audits: list[dict[str, object]], fig_path: Path, doc_md: Path, doc_html: Path) -> None:
    audit_by_scope = {str(item["scope"]): item for item in audits}
    confirmation = audit_by_scope["non_pbm_confirmation"]
    discovery = audit_by_scope["pbm_discovery"]
    text = f"""# Direct-Surprisal Sustained-Onset Confirmation

This report applies the onset rule frozen on 21 July 2026 to the real-child
Mistral k3 exact/top-coded word-effort design cells. The reference category is
`006-023`. Uncertainty is produced by resampling children and using a
simultaneous 95% max-absolute-studentized-deviation band across the seven
post-reference contrasts.

## Result

- PBM discovery sustained onset: `{discovery['sustained_onset']}`.
- Non-PBM confirmation sustained onset: `{confirmation['sustained_onset']}`.
- Confirmation bootstrap fits: `{confirmation['bootstrap_reps_successful']}` / `{confirmation['bootstrap_reps_requested']}`.
- A confirmation bin is eligible for the rule only with at least five children
  and three corpora.

![Simultaneous child-bootstrap onset bands]({os.path.relpath(fig_path, doc_md.parent).replace(os.sep, '/')})

{_md_table(all_contrasts)}

## Interpretation

An onset is not the first nominally significant coefficient. It is the first
adequately supported post-reference bin whose upper simultaneous band is below
zero and for which every later adequately supported bin also remains below
zero. If the confirmation result is `not_established`, the prior PBM statement
that the first row-level decrease appears by 24–29 months remains exploratory
and must not be promoted as a replicated developmental onset.

These bands use the frozen lexical-word effort definition. Full-79 validated
morpheme, syllable, and phoneme controls are not yet available, so this report
does not satisfy that separate alternative-effort validation requirement.
"""
    doc_md.parent.mkdir(parents=True, exist_ok=True)
    doc_md.write_text(text, encoding="utf-8")
    render_markdown_file(doc_md, doc_html)


def build(
    *,
    input_root: Path,
    coefficients: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_md: Path,
    doc_html: Path,
    reps: int,
    seed: int,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    all_contrasts: list[pd.DataFrame] = []
    audits: list[dict[str, object]] = []
    max_saved_difference = 0.0
    for scope_index, scope in enumerate(SCOPES):
        path = input_root / scope / "p1_k3_contextual.csv.gz"
        frame = pd.read_csv(path, low_memory=False)
        contrasts, draws, audit = fit_bootstrap_bands(
            frame,
            reps=reps,
            seed=seed + scope_index,
        )
        contrasts.insert(0, "scope", scope)
        draws.insert(0, "scope", scope)
        saved = _saved_age_contrasts(coefficients, scope)
        check = contrasts.merge(saved, on="age_bin", how="left")
        check["absolute_difference_from_saved"] = (
            check["estimate_vs_006_023"] - check["estimate"]
        ).abs()
        max_difference = float(check["absolute_difference_from_saved"].max())
        max_saved_difference = max(max_saved_difference, max_difference)
        audit.update(
            {
                "scope": scope,
                "input": str(path),
                "saved_point_estimate_max_absolute_difference": max_difference,
            }
        )
        all_contrasts.append(contrasts)
        audits.append(audit)
        draws.to_csv(output_dir / f"{scope}_age_bin_child_bootstrap_draws.csv.gz", index=False)
    combined = pd.concat(all_contrasts, ignore_index=True)
    combined.to_csv(output_dir / "age_bin_simultaneous_bands.csv", index=False)
    fig_path = fig_dir / "age_bin_simultaneous_bands.png"
    _plot(combined, fig_path)
    status = "PASS" if max_saved_difference < 1e-8 else "FAIL"
    final_audit = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bootstrap_reps": reps,
        "seed": seed,
        "point_estimate_tolerance": 1e-8,
        "max_saved_point_estimate_difference": max_saved_difference,
        "scopes": audits,
    }
    (output_dir / "audit.json").write_text(
        json.dumps(final_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _report(combined, audits, fig_path, doc_md, doc_html)
    if status != "PASS":
        raise RuntimeError(
            f"Within-child point estimates differ from saved model by {max_saved_difference}"
        )
    return final_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--coefficients", type=Path, default=DEFAULT_COEFFICIENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260722)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = build(
        input_root=args.input_root,
        coefficients=args.coefficients,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_md=args.doc_md,
        doc_html=args.doc_html,
        reps=args.bootstrap_reps,
        seed=args.seed,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
