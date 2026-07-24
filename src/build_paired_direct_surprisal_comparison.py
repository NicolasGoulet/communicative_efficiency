#!/usr/bin/env python3
"""Audit and compare two scorers on exactly paired PBM child utterances.

The join is provenance-first: the stable source-derived utterance ID is the
key, while source fields plus real/generated target and context hashes must
also agree. Raw model-token-normalized values are retained only as tokenizer
diagnostics; scientific agreement is summarized within scorer using total,
word-normalized, character-normalized, context-gain, and candidate-gap scores.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from build_direct_surprisal_model_suite import (
    WORD_CATEGORIES,
    child_fe_crossproducts,
    md_table,
    word_category,
)
from render_markdown_report import render_markdown_file


JOIN_KEY = "utterance_id"
IDENTITY_COLUMNS = [
    "dataset",
    "child_id",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "context_k1_sha256",
    "context_k2_sha256",
    "context_k3_sha256",
    "real_target_text_sha256",
    "random_target_text_sha256",
    "unigram_target_text_sha256",
    "bigram_target_text_sha256",
    "trigram_target_text_sha256",
    "real_nb_words",
    "real_nb_characters",
    "context_available_k3",
]
SCORE_COLUMNS = [
    "real_k0_sum_bits",
    "real_k1_sum_bits",
    "real_k2_sum_bits",
    "real_k3_sum_bits",
    "real_context_gain_k1",
    "real_context_gain_k2",
    "real_context_gain_k3",
    "real_k0_n_eval_tokens",
    "real_k1_n_eval_tokens",
    "real_k2_n_eval_tokens",
    "real_k3_n_eval_tokens",
    "random_minus_real_k3_bits",
    "unigram_minus_real_k3_bits",
    "bigram_minus_real_k3_bits",
    "trigram_minus_real_k3_bits",
]
PRIMARY_OUTCOME_COLUMNS = [
    "real_k3_sum_bits",
    "real_k0_sum_bits",
    "real_context_gain_k3",
]
CORRELATION_OUTCOMES = [
    "real_k0_sum_bits",
    "real_k1_sum_bits",
    "real_k2_sum_bits",
    "real_k3_sum_bits",
    "real_context_gain_k1",
    "real_context_gain_k2",
    "real_context_gain_k3",
    "random_minus_real_k3_bits",
    "unigram_minus_real_k3_bits",
    "bigram_minus_real_k3_bits",
    "trigram_minus_real_k3_bits",
    "real_bits_per_word_k3",
    "real_bits_per_character_k3",
]


def read_scorer(path: Path, suffix: str) -> tuple[pd.DataFrame, str]:
    header = pd.read_csv(path, nrows=0, keep_default_na=False).columns
    required = {"scorer_id", JOIN_KEY, *IDENTITY_COLUMNS, *SCORE_COLUMNS}
    missing = sorted(required - set(header))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    frame = pd.read_csv(
        path,
        usecols=sorted(required),
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    frame = frame[frame["sample_group"].eq("pbm_discovery")].copy()
    if frame.empty:
        raise ValueError(f"No PBM discovery rows found in {path}")
    scorer_ids = sorted(value for value in frame["scorer_id"].unique() if value)
    if len(scorer_ids) != 1:
        raise ValueError(f"Expected one scorer_id in {path}, found {scorer_ids}")
    scorer_id = scorer_ids[0]
    frame = frame.drop(columns="scorer_id")
    rename = {
        column: f"{column}_{suffix}"
        for column in frame.columns
        if column != JOIN_KEY
    }
    return frame.rename(columns=rename), scorer_id


def duplicate_audit(frame: pd.DataFrame, suffix: str) -> pd.DataFrame:
    counts = frame[JOIN_KEY].value_counts(dropna=False)
    duplicates = counts[counts > 1]
    return pd.DataFrame(
        {
            "problem": f"duplicate_{suffix}",
            JOIN_KEY: duplicates.index.astype(str),
            "field": JOIN_KEY,
            "left_value": duplicates.astype(str).to_numpy(),
            "right_value": "",
            "available_child_key": "",
        }
    )


def values_equal(left: pd.Series, right: pd.Series, field: str) -> pd.Series:
    if field == "age_months":
        left_numeric = pd.to_numeric(left, errors="coerce")
        right_numeric = pd.to_numeric(right, errors="coerce")
        both_missing = left.eq("") & right.eq("")
        return both_missing | np.isclose(left_numeric, right_numeric, equal_nan=False)
    return left.fillna("").astype(str).eq(right.fillna("").astype(str))


def build_pair(
    left_path: Path,
    right_path: Path,
    *,
    left_suffix: str,
    right_suffix: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    left, left_scorer = read_scorer(left_path, left_suffix)
    right, right_scorer = read_scorer(right_path, right_suffix)
    problems = [duplicate_audit(left, left_suffix), duplicate_audit(right, right_suffix)]
    if not problems[0].empty or not problems[1].empty:
        mismatch = pd.concat(problems, ignore_index=True)
        raise ValueError(f"Duplicate join keys prevent a one-to-one scorer join: {len(mismatch)} rows")

    paired = left.merge(right, on=JOIN_KEY, how="outer", validate="one_to_one", indicator=True)
    for side, merge_value in [(left_suffix, "left_only"), (right_suffix, "right_only")]:
        missing = paired[paired["_merge"].eq(merge_value)]
        if not missing.empty:
            problems.append(
                pd.DataFrame(
                    {
                        "problem": f"missing_from_{right_suffix if side == left_suffix else left_suffix}",
                        JOIN_KEY: missing[JOIN_KEY].astype(str),
                        "field": JOIN_KEY,
                        "left_value": "",
                        "right_value": "",
                        "available_child_key": missing[
                            f"child_key_{side}"
                        ].fillna("").astype(str),
                    }
                )
            )
    inner = paired[paired["_merge"].eq("both")].copy()
    for field in IDENTITY_COLUMNS:
        left_column = f"{field}_{left_suffix}"
        right_column = f"{field}_{right_suffix}"
        equal = values_equal(inner[left_column], inner[right_column], field)
        if (~equal).any():
            mismatch = inner.loc[~equal, [JOIN_KEY, left_column, right_column]].copy()
            mismatch.columns = [JOIN_KEY, "left_value", "right_value"]
            mismatch.insert(0, "problem", "identity_mismatch")
            mismatch.insert(2, "field", field)
            mismatch["available_child_key"] = inner.loc[
                ~equal, f"child_key_{left_suffix}"
            ].to_numpy()
            problems.append(mismatch)

    nonempty_problems = [item for item in problems if not item.empty]
    if nonempty_problems:
        mismatch_table = pd.concat(nonempty_problems, ignore_index=True)
    else:
        mismatch_table = pd.DataFrame(
            columns=[
                "problem",
                JOIN_KEY,
                "field",
                "left_value",
                "right_value",
                "available_child_key",
            ]
        )
    return inner.drop(columns="_merge"), mismatch_table, left_scorer, right_scorer


def numeric_derivations(frame: pd.DataFrame, suffixes: Sequence[str]) -> pd.DataFrame:
    result = frame.copy()
    for suffix in suffixes:
        for column in SCORE_COLUMNS:
            full = f"{column}_{suffix}"
            result[full] = pd.to_numeric(result[full], errors="coerce")
        words = pd.to_numeric(result[f"real_nb_words_{suffix}"], errors="coerce")
        chars = pd.to_numeric(result[f"real_nb_characters_{suffix}"], errors="coerce")
        for context in ["k0", "k1", "k2", "k3"]:
            result[f"real_bits_per_word_{context}_{suffix}"] = (
                result[f"real_{context}_sum_bits_{suffix}"] / words.replace(0, np.nan)
            )
            result[f"real_bits_per_character_{context}_{suffix}"] = (
                result[f"real_{context}_sum_bits_{suffix}"] / chars.replace(0, np.nan)
            )
    return result


def pearson(left: pd.Series, right: pd.Series) -> float:
    clean = pd.concat([left, right], axis=1).dropna()
    return float(clean.iloc[:, 0].corr(clean.iloc[:, 1])) if len(clean) >= 3 else np.nan


def spearman(left: pd.Series, right: pd.Series) -> float:
    clean = pd.concat([left, right], axis=1).dropna()
    if len(clean) < 3:
        return np.nan
    return float(clean.iloc[:, 0].rank(method="average").corr(clean.iloc[:, 1].rank(method="average")))


def correlation_table(frame: pd.DataFrame, left_suffix: str, right_suffix: str) -> pd.DataFrame:
    rows = []
    scopes = [("all_pbm", frame)]
    scopes.extend((f"corpus:{dataset}", group) for dataset, group in frame.groupby(f"dataset_{left_suffix}"))
    for scope, group in scopes:
        child = group[f"child_key_{left_suffix}"]
        for outcome in CORRELATION_OUTCOMES:
            left = pd.to_numeric(group[f"{outcome}_{left_suffix}"], errors="coerce")
            right = pd.to_numeric(group[f"{outcome}_{right_suffix}"], errors="coerce")
            clean = left.notna() & right.notna()
            left_centered = left - left.groupby(child).transform("mean")
            right_centered = right - right.groupby(child).transform("mean")
            rows.append(
                {
                    "scope": scope,
                    "outcome": outcome,
                    "paired_rows": int(clean.sum()),
                    "children": int(child[clean].nunique()),
                    "pearson": pearson(left, right),
                    "spearman": spearman(left, right),
                    "within_child_pearson": pearson(left_centered, right_centered),
                    "within_child_spearman": spearman(left_centered, right_centered),
                    "same_sign_fraction": float(
                        (np.sign(left[clean]) == np.sign(right[clean])).mean()
                    )
                    if clean.any()
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


def collapse_paired_cells(
    frame: pd.DataFrame,
    outcome: str,
    left_suffix: str,
    right_suffix: str,
) -> pd.DataFrame:
    left_column = f"{outcome}_{left_suffix}"
    right_column = f"{outcome}_{right_suffix}"
    age = pd.to_numeric(frame[f"age_months_{left_suffix}"], errors="coerce")
    words = pd.to_numeric(frame[f"real_nb_words_{left_suffix}"], errors="coerce")
    tokens_left = pd.to_numeric(
        frame[f"real_{'k0' if outcome == 'real_k0_sum_bits' else 'k3'}_n_eval_tokens_{left_suffix}"],
        errors="coerce",
    )
    tokens_right = pd.to_numeric(
        frame[f"real_{'k0' if outcome == 'real_k0_sum_bits' else 'k3'}_n_eval_tokens_{right_suffix}"],
        errors="coerce",
    )
    mask = (
        age.between(6, 65, inclusive="both")
        & words.ge(1)
        & frame[left_column].notna()
        & frame[right_column].notna()
        & tokens_left.gt(0)
        & tokens_right.gt(0)
    )
    if outcome != "real_k0_sum_bits":
        mask &= pd.to_numeric(frame[f"context_available_k3_{left_suffix}"], errors="coerce").gt(0)
        mask &= pd.to_numeric(frame[f"context_available_k3_{right_suffix}"], errors="coerce").gt(0)
    data = pd.DataFrame(
        {
            "dataset": frame.loc[mask, f"dataset_{left_suffix}"],
            "child_key": frame.loc[mask, f"child_key_{left_suffix}"],
            "age_months": age[mask],
            "word_count_exact_top12": word_category(words[mask]),
            "left_outcome": frame.loc[mask, left_column],
            "right_outcome": frame.loc[mask, right_column],
        }
    )
    cells = (
        data.groupby(
            ["dataset", "child_key", "age_months", "word_count_exact_top12"],
            observed=True,
            dropna=False,
        )
        .agg(
            left_outcome=("left_outcome", "mean"),
            right_outcome=("right_outcome", "mean"),
            row_count=("left_outcome", "size"),
        )
        .reset_index()
    )
    cells["age_c"] = cells["age_months"] - np.average(
        cells["age_months"], weights=cells["row_count"]
    )
    cells["word_count_exact_top12"] = pd.Categorical(
        cells["word_count_exact_top12"], categories=WORD_CATEGORIES, ordered=True
    )
    return cells


def fit_age_slope(cells: pd.DataFrame, outcome_column: str, child_column: str = "child_key") -> float:
    formula = f"{outcome_column} ~ age_c + C(word_count_exact_top12) + C({child_column})"
    result = smf.wls(formula, data=cells, weights=cells["row_count"]).fit()
    return float(result.params["age_c"])


def paired_slope_bootstrap(
    frame: pd.DataFrame,
    *,
    left_suffix: str,
    right_suffix: str,
    reps: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    summary_rows = []
    draw_rows = []
    for outcome_index, outcome in enumerate(PRIMARY_OUTCOME_COLUMNS):
        cells = collapse_paired_cells(frame, outcome, left_suffix, right_suffix)
        observed_left = fit_age_slope(cells, "left_outcome")
        observed_right = fit_age_slope(cells, "right_outcome")
        left_cells = cells.rename(columns={"left_outcome": "outcome_mean"})
        right_cells = cells.rename(columns={"right_outcome": "outcome_mean"})
        children, left_matrices, left_vectors = child_fe_crossproducts(left_cells)
        right_children, right_matrices, right_vectors = child_fe_crossproducts(right_cells)
        if not np.array_equal(children, right_children):  # pragma: no cover - internal invariant
            raise ValueError("Paired scorer cells produced different child orderings")
        for replicate in range(reps):
            sampled_indices = rng.integers(0, len(children), size=len(children))
            try:
                left_estimate = float(
                    np.linalg.lstsq(
                        left_matrices[sampled_indices].sum(axis=0),
                        left_vectors[sampled_indices].sum(axis=0),
                        rcond=None,
                    )[0][0]
                )
                right_estimate = float(
                    np.linalg.lstsq(
                        right_matrices[sampled_indices].sum(axis=0),
                        right_vectors[sampled_indices].sum(axis=0),
                        rcond=None,
                    )[0][0]
                )
                status = "PASS"
                problem = ""
            except Exception as exc:  # pragma: no cover - production audit path
                left_estimate = right_estimate = np.nan
                status = "FAIL"
                problem = f"{type(exc).__name__}: {exc}"
            draw_rows.append(
                {
                    "outcome": outcome,
                    "replicate": replicate,
                    "seed": seed,
                    f"slope_{left_suffix}": left_estimate,
                    f"slope_{right_suffix}": right_estimate,
                    f"difference_{left_suffix}_minus_{right_suffix}": left_estimate - right_estimate,
                    "status": status,
                    "problem": problem,
                }
            )
        outcome_draws = [row for row in draw_rows if row["outcome"] == outcome and row["status"] == "PASS"]
        values = np.array(
            [row[f"difference_{left_suffix}_minus_{right_suffix}"] for row in outcome_draws],
            dtype=float,
        )
        summary_rows.append(
            {
                "outcome": outcome,
                "paired_rows": int(cells["row_count"].sum()),
                "children": len(children),
                f"observed_slope_{left_suffix}": observed_left,
                f"observed_slope_{right_suffix}": observed_right,
                f"observed_difference_{left_suffix}_minus_{right_suffix}": observed_left - observed_right,
                "requested_reps": reps,
                "successful_reps": len(values),
                "difference_ci_low": float(np.quantile(values, 0.025)) if len(values) else np.nan,
                "difference_ci_high": float(np.quantile(values, 0.975)) if len(values) else np.nan,
            }
        )
    return pd.DataFrame(summary_rows), pd.DataFrame(draw_rows)


def build_report(
    *,
    output: Path,
    html: Path,
    left_scorer: str,
    right_scorer: str,
    audit: dict[str, object],
    correlations: pd.DataFrame,
    slope_summary: pd.DataFrame,
    output_dir: Path,
) -> None:
    overall = correlations[correlations["scope"].eq("all_pbm")]
    lines = [
        "# Paired PBM Direct-Surprisal Scorer Comparison",
        "",
        f"This report compares `{left_scorer}` and `{right_scorer}` on exactly paired "
        "Brown, Manchester, and Providence utterances. It is a scorer-robustness "
        "analysis on the discovery sample, not an independent sample replication.",
        "",
        "## Join Audit",
        "",
        md_table(pd.DataFrame([audit])),
        "",
        "No paired analysis is valid unless the unexplained mismatch count is zero. A "
        "declared source-version coverage difference may be retained in the mismatch "
        "table, but only the exact intersection is analyzed. Target and context identity "
        "is checked using source fields and SHA-256 hashes, not row position.",
        "",
        "## Paired Score Agreement",
        "",
        md_table(overall),
        "",
        "Within-child correlations remove each child's mean before comparing scorers. "
        "Word- and character-normalized rows are comparable across tokenizers; raw "
        "bits per model token are deliberately omitted as scientific agreement measures.",
        "",
        "## Fixed-Effort Age-Slope Comparison",
        "",
        md_table(slope_summary),
        "",
        f"The reported difference is `{left_scorer} minus {right_scorer}`. Its interval "
        "resamples children and refits both scorer slopes to each identical bootstrap draw.",
        "",
        "## Interpretation Boundary",
        "",
        "Agreement means the PBM developmental pattern is less dependent on one scorer. "
        "A magnitude difference can reflect model calibration and scale as well as a "
        "scientific disagreement. Context gain is `k0 - k3`; positive values mean the "
        "preceding context supports the observed target under that scorer.",
        "",
        "## Saved Artifacts",
        "",
        f"- Join mismatches: `{output_dir / 'join_mismatches.csv'}`",
        f"- Exact paired wide table: `{output_dir / 'paired_direct_surprisal_wide.csv.gz'}`",
        f"- Paired correlations: `{output_dir / 'paired_correlations.csv'}`",
        f"- Paired slope summary: `{output_dir / 'paired_slope_bootstrap_summary.csv'}`",
        f"- Bootstrap draws: `{output_dir / 'paired_slope_bootstrap_draws.csv.gz'}`",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(output, html, title="Paired PBM Direct-Surprisal Scorer Comparison")


def run_comparison(
    *,
    left_path: Path,
    right_path: Path,
    output_dir: Path,
    report_md: Path,
    report_html: Path,
    left_suffix: str,
    right_suffix: str,
    bootstrap_reps: int,
    bootstrap_seed: int,
    allowed_right_only_child: str | None = None,
    allowed_right_only_count: int = 0,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paired, mismatches, left_scorer, right_scorer = build_pair(
        left_path,
        right_path,
        left_suffix=left_suffix,
        right_suffix=right_suffix,
    )
    mismatches["explanation"] = ""
    mismatches["is_explained"] = 0
    if allowed_right_only_child:
        expected_problem = f"missing_from_{left_suffix}"
        expected = mismatches["problem"].eq(expected_problem) & mismatches[
            "available_child_key"
        ].eq(allowed_right_only_child)
        if int(expected.sum()) == allowed_right_only_count:
            mismatches.loc[expected, "is_explained"] = 1
            mismatches.loc[expected, "explanation"] = (
                "Declared scorer-coverage difference: later full-79 source patch absent "
                "from the earlier scorer run."
            )
    mismatches.to_csv(output_dir / "join_mismatches.csv", index=False)
    unexplained = mismatches[mismatches["is_explained"].eq(0)]
    audit = {
        "left_scorer": left_scorer,
        "right_scorer": right_scorer,
        "paired_rows": len(paired),
        "children": int(paired[f"child_key_{left_suffix}"].nunique()),
        "corpora": int(paired[f"dataset_{left_suffix}"].nunique()),
        "join_mismatches": len(mismatches),
        "explained_join_mismatches": int(mismatches["is_explained"].sum()),
        "unexplained_join_mismatches": len(unexplained),
        "join_status": (
            "PASS"
            if mismatches.empty
            else "PASS_WITH_EXPLAINED_COVERAGE_DIFFERENCE"
            if unexplained.empty
            else "FAIL"
        ),
    }
    (output_dir / "join_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if not unexplained.empty:
        raise ValueError(
            f"Paired scorer join failed with {len(unexplained)} unexplained mismatches"
        )

    paired = numeric_derivations(paired, [left_suffix, right_suffix])
    paired["pair_status"] = "matched_exact_source_target_context"
    paired.to_csv(output_dir / "paired_direct_surprisal_wide.csv.gz", index=False)
    correlations = correlation_table(paired, left_suffix, right_suffix)
    correlations.to_csv(output_dir / "paired_correlations.csv", index=False)
    slope_summary, draws = paired_slope_bootstrap(
        paired,
        left_suffix=left_suffix,
        right_suffix=right_suffix,
        reps=bootstrap_reps,
        seed=bootstrap_seed,
    )
    slope_summary.to_csv(output_dir / "paired_slope_bootstrap_summary.csv", index=False)
    draws.to_csv(output_dir / "paired_slope_bootstrap_draws.csv.gz", index=False)
    build_report(
        output=report_md,
        html=report_html,
        left_scorer=left_scorer,
        right_scorer=right_scorer,
        audit=audit,
        correlations=correlations,
        slope_summary=slope_summary,
        output_dir=output_dir,
    )
    return audit


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left-wide", type=Path, required=True)
    parser.add_argument("--right-wide", type=Path, required=True)
    parser.add_argument("--left-suffix", default="tiny")
    parser.add_argument("--right-suffix", default="mistral")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-html", type=Path, required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--bootstrap-seed", type=int, default=20260721)
    parser.add_argument(
        "--allowed-right-only-child",
        default=None,
        help="Explicit child_key allowed only in the right scorer source.",
    )
    parser.add_argument("--allowed-right-only-count", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    audit = run_comparison(
        left_path=args.left_wide,
        right_path=args.right_wide,
        output_dir=args.output_dir,
        report_md=args.report_md,
        report_html=args.report_html,
        left_suffix=args.left_suffix,
        right_suffix=args.right_suffix,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
        allowed_right_only_child=args.allowed_right_only_child,
        allowed_right_only_count=args.allowed_right_only_count,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
