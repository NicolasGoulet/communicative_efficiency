#!/usr/bin/env python3
"""Build preliminary Route 1 model-proposal diagnostics and report.

This script deliberately does not edit the supervisor-facing main report. It
creates a separate model-review packet so candidate regression/mixed-model
forms can be inspected before being promoted into the real report.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gamma, Gaussian
from statsmodels.genmod.families.links import Log

try:
    from utterance_count_strategies import normalize_text, word_tokens_regex
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.utterance_count_strategies import normalize_text, word_tokens_regex

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


ROUTE1_DIR = Path("results/route1_analysis_dataset")
DEFAULT_INPUT = ROUTE1_DIR / "route1_scored_utterance_effort_context_entropy_long.csv.gz"
DEFAULT_OUTPUT_DIR = Path("results/utterance_information_model_proposals")
DEFAULT_FIG_DIR = Path("figs/utterance_information_model_proposals")
DEFAULT_DOC_MD = Path("docs/utterance_information_model_proposals.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_model_proposals.html")
DEFAULT_NOTEBOOK = Path("notebooks/utterance_information_model_proposals.ipynb")
DEFAULT_SCORED_TREE = Path("results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023")
DEFAULT_CONTEXT_ENTROPY_DIR = Path("results/external/compute_surprisal_mila/context_entropy_mistral")

SEED = 20260604
VARIANT_ORDER = ["real", "random", "unigram", "bigram", "trigram"]
TARGET_VARIANT_CATEGORY_ORDER = VARIANT_ORDER + ["caretaker"]
COMPARISON_ORDER = ["real", "random", "unigram", "bigram", "trigram", "caretaker"]
CONTEXT_ORDER = ["k0", "k1", "k2", "k3"]
AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
EFFORT_CONTROLS = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables: CMU/pkg"),
    ("nb_syllables_pkg", "Syllables: pkg"),
    ("nb_phonemes", "Phonemes"),
]
USECOLS = [
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "session_id",
    "age_months",
    "age_bin",
    "file",
    "line_no",
    "role",
    "target_variant",
    "context_k",
    "context_text",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "same_word_count_as_child_real",
    "delta_nb_morphemes_vs_child_real",
    "delta_nb_syllables_cmu_or_pkg_vs_child_real",
    "delta_nb_syllables_pkg_vs_child_real",
    "delta_nb_phonemes_vs_child_real",
    "context_entropy_join_status",
    "context_entropy_bits",
    "context_entropy_token_count",
]
NUMERIC_COLS = [
    "age_months",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "same_word_count_as_child_real",
    "delta_nb_morphemes_vs_child_real",
    "delta_nb_syllables_cmu_or_pkg_vs_child_real",
    "delta_nb_syllables_pkg_vs_child_real",
    "delta_nb_phonemes_vs_child_real",
    "context_entropy_bits",
    "context_entropy_token_count",
]
PREDICTOR_COLS = [
    "age_months",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "n_eval_tokens",
    "context_entropy_bits",
]


@dataclass(frozen=True)
class AnalysisData:
    real_rows: pd.DataFrame
    baseline_k3_rows: pd.DataFrame
    caretaker_k3_rows: pd.DataFrame
    real_sample: pd.DataFrame
    baseline_sample: pd.DataFrame
    caretaker_sample: pd.DataFrame
    context_sample: pd.DataFrame
    long_counts: pd.DataFrame
    entropy_status_counts: pd.DataFrame


def numeric_clean(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce expected numeric fields and add reusable transformed predictors."""

    out = frame.copy()
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out[np.isfinite(out["sum_bits"]) & np.isfinite(out["bits_per_word"])].copy()
    out = out[(out["sum_bits"] > 0) & (out["bits_per_word"] > 0) & (out["nb_words"] > 0)].copy()
    out["age_centered"] = out["age_months"] - out["age_months"].mean()
    out["age_scaled"] = out["age_centered"] / out["age_months"].std(ddof=0)
    out["age_scaled_sq"] = out["age_scaled"] ** 2
    out["log_nb_words"] = np.log(out["nb_words"])
    out["log_sum_bits"] = np.log(out["sum_bits"])
    out["log_bits_per_word"] = np.log(out["bits_per_word"])
    out["age_bin"] = pd.Categorical(out["age_bin"], AGE_BIN_ORDER, ordered=True)
    out["context_k"] = pd.Categorical(out["context_k"], CONTEXT_ORDER, ordered=True)
    out["target_variant"] = pd.Categorical(out["target_variant"], TARGET_VARIANT_CATEGORY_ORDER, ordered=True)
    return out


def stratified_sample(frame: pd.DataFrame, group_cols: Sequence[str], n_per_group: int) -> pd.DataFrame:
    """Return a deterministic within-group sample."""

    if frame.empty:
        return frame.copy()
    rng = np.random.default_rng(SEED)
    sampled_parts: list[pd.DataFrame] = []
    for _, group in frame.groupby(list(group_cols), observed=True, dropna=False, sort=False):
        if len(group) <= n_per_group:
            sampled_parts.append(group)
        else:
            positions = np.sort(rng.choice(len(group), size=n_per_group, replace=False))
            sampled_parts.append(group.iloc[positions])
    return pd.concat(sampled_parts, ignore_index=True)


def read_analysis_data(input_csv: Path, output_dir: Path, *, chunksize: int) -> AnalysisData:
    """Extract compact real/baseline dataframes from the Route 1 long CSV."""

    real_parts: list[pd.DataFrame] = []
    baseline_parts: list[pd.DataFrame] = []
    caretaker_parts: list[pd.DataFrame] = []
    long_count_parts: list[pd.DataFrame] = []
    entropy_status_parts: list[pd.DataFrame] = []
    group_cols = ["dataset", "role", "target_variant", "context_k"]
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        long_count_parts.append(
            chunk.groupby(group_cols, dropna=False, observed=True)
            .size()
            .reset_index(name="long_rows")
        )
        entropy_status_parts.append(
            chunk.groupby(["role", "target_variant", "context_k", "context_entropy_join_status"], dropna=False, observed=True)
            .size()
            .reset_index(name="rows")
        )
        caretaker = chunk[chunk["role"].eq("caretaker") & chunk["context_k"].eq("k3")].copy()
        if not caretaker.empty:
            caretaker_parts.append(caretaker)
        child = chunk[chunk["role"].eq("child")].copy()
        if not child.empty:
            real = child[child["target_variant"].eq("real")].copy()
            if not real.empty:
                real_parts.append(real)
            baseline = child[
                child["context_k"].eq("k3") & child["target_variant"].isin(VARIANT_ORDER)
            ].copy()
            if not baseline.empty:
                baseline_parts.append(baseline)

    real_rows = numeric_clean(pd.concat(real_parts, ignore_index=True))
    baseline_k3_rows = numeric_clean(pd.concat(baseline_parts, ignore_index=True))
    caretaker_k3_rows = numeric_clean(pd.concat(caretaker_parts, ignore_index=True))
    long_counts = (
        pd.concat(long_count_parts, ignore_index=True)
        .groupby(group_cols, dropna=False, observed=True)["long_rows"]
        .sum()
        .reset_index()
        .sort_values(group_cols)
    )
    entropy_status_counts = (
        pd.concat(entropy_status_parts, ignore_index=True)
        .groupby(["role", "target_variant", "context_k", "context_entropy_join_status"], dropna=False, observed=True)["rows"]
        .sum()
        .reset_index()
        .sort_values(["role", "target_variant", "context_k", "context_entropy_join_status"])
    )

    real_sample = stratified_sample(
        real_rows,
        ["child_id", "age_bin", "context_k"],
        n_per_group=300,
    )
    baseline_sample = stratified_sample(
        baseline_k3_rows,
        ["child_id", "age_bin", "target_variant"],
        n_per_group=160,
    )
    caretaker_sample = stratified_sample(
        caretaker_k3_rows,
        ["child_id", "age_bin"],
        n_per_group=160,
    )
    context_rows = real_rows[
        real_rows["context_k"].isin(["k1", "k2", "k3"])
        & real_rows["context_entropy_join_status"].isin(["matched", "matched_text_fallback"])
        & np.isfinite(real_rows["context_entropy_bits"])
    ].copy()
    context_sample = stratified_sample(
        context_rows,
        ["child_id", "age_bin", "context_k"],
        n_per_group=250,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    real_sample.to_csv(output_dir / "child_real_modeling_sample.csv.gz", index=False)
    baseline_sample.to_csv(output_dir / "child_baseline_k3_modeling_sample.csv.gz", index=False)
    caretaker_sample.to_csv(output_dir / "caretaker_k3_modeling_sample.csv.gz", index=False)
    context_sample.to_csv(output_dir / "child_real_context_entropy_modeling_sample.csv.gz", index=False)
    long_counts.to_csv(output_dir / "long_table_counts_by_source_role_variant_context.csv", index=False)
    entropy_status_counts.to_csv(output_dir / "context_entropy_join_status_counts.csv", index=False)
    summarize_extraction(
        real_rows,
        baseline_k3_rows,
        real_sample,
        baseline_sample,
        context_sample,
        caretaker_k3_rows,
        caretaker_sample,
    ).to_csv(
        output_dir / "data_extraction_summary.csv",
        index=False,
    )
    return AnalysisData(
        real_rows=real_rows,
        baseline_k3_rows=baseline_k3_rows,
        caretaker_k3_rows=caretaker_k3_rows,
        real_sample=real_sample,
        baseline_sample=baseline_sample,
        caretaker_sample=caretaker_sample,
        context_sample=context_sample,
        long_counts=long_counts,
        entropy_status_counts=entropy_status_counts,
    )


def summarize_extraction(
    real_rows: pd.DataFrame,
    baseline_k3_rows: pd.DataFrame,
    real_sample: pd.DataFrame,
    baseline_sample: pd.DataFrame,
    context_sample: pd.DataFrame,
    caretaker_k3_rows: pd.DataFrame | None = None,
    caretaker_sample: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return high-level row counts for the analysis packet."""

    rows = [
        {"table": "real_rows_all_contexts", "rows": len(real_rows), "children": real_rows["child_id"].nunique()},
        {"table": "baseline_k3_rows", "rows": len(baseline_k3_rows), "children": baseline_k3_rows["child_id"].nunique()},
        {"table": "real_sample", "rows": len(real_sample), "children": real_sample["child_id"].nunique()},
        {"table": "baseline_sample", "rows": len(baseline_sample), "children": baseline_sample["child_id"].nunique()},
        {
            "table": "caretaker_k3_rows",
            "rows": 0 if caretaker_k3_rows is None else len(caretaker_k3_rows),
            "children": 0 if caretaker_k3_rows is None else caretaker_k3_rows["child_id"].nunique(),
        },
        {
            "table": "caretaker_sample",
            "rows": 0 if caretaker_sample is None else len(caretaker_sample),
            "children": 0 if caretaker_sample is None else caretaker_sample["child_id"].nunique(),
        },
        {"table": "context_entropy_sample", "rows": len(context_sample), "children": context_sample["child_id"].nunique()},
    ]
    return pd.DataFrame(rows)


def count_csv_data_rows(path: Path) -> int:
    """Count data rows in a CSV or CSV.GZ file without loading it into memory."""

    opener = pd.io.common.get_handle(path, mode="r", compression="infer", encoding="utf-8")
    try:
        total_lines = sum(1 for _ in opener.handle)
    finally:
        opener.close()
    return max(0, total_lines - 1)


def parse_float_or_none(value: object) -> float | None:
    """Parse a float-like value, returning None for blanks or NaN."""

    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def source_target_column(role: str, target_variant: str) -> str:
    """Return the source CSV text column for a role/variant pair."""

    if role == "caretaker":
        return "caretaker_utterance_clean"
    if target_variant == "real":
        return "chi_utterance_clean"
    return f"{target_variant}_model_utterance_bin6"


def count_source_csv_rows(path: Path, *, target_column: str) -> dict[str, int]:
    """Count raw and valid scored rows in one source scored CSV."""

    raw_rows = 0
    scored_rows = 0
    blank_target_rows = 0
    unscored_rows = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_rows += 1
            target = normalize_text(row.get(target_column, ""))
            has_words = bool(word_tokens_regex(target))
            has_bits = parse_float_or_none(row.get("sum_bits", "")) is not None
            if not target or not has_words:
                blank_target_rows += 1
            if not has_bits:
                unscored_rows += 1
            if target and has_words and has_bits:
                scored_rows += 1
    return {
        "raw_rows": raw_rows,
        "source_rows": scored_rows,
        "blank_target_rows": blank_target_rows,
        "unscored_rows": unscored_rows,
    }


def parse_scored_file(path: Path, root: Path) -> dict[str, object]:
    """Parse source-tree metadata from one scored CSV path."""

    rel = path.relative_to(root)
    parts = rel.parts
    if parts[0] == "WITHOUT_context":
        context_k = "k0"
    elif parts[0] == "WITH_context":
        context_k = parts[1]
    else:
        context_k = "unknown"

    name = path.name
    role = "child" if name.startswith("chi.") else "caretaker"
    target_variant = name.split("__", maxsplit=1)[-1].removesuffix(".scored.csv")
    target_column = source_target_column(role, target_variant)
    counts = count_source_csv_rows(path, target_column=target_column)
    return {
        "dataset": parts[-3],
        "child_id": parts[-2],
        "role": role,
        "target_variant": target_variant,
        "context_k": context_k,
        "target_column": target_column,
        "path": str(path),
        **counts,
    }


def source_tree_audit(
    *,
    scored_tree: Path,
    context_entropy_dir: Path,
    long_counts: pd.DataFrame,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compare symlinked scored CSV row counts to the combined long table."""

    output_dir.mkdir(parents=True, exist_ok=True)
    score_rows: list[dict[str, object]] = []
    if scored_tree.exists():
        for path in sorted(scored_tree.rglob("*.csv")):
            score_rows.append(parse_scored_file(path, scored_tree))

    score_file_counts = pd.DataFrame(score_rows)
    if score_file_counts.empty:
        source_counts = pd.DataFrame(columns=["dataset", "role", "target_variant", "context_k", "source_files", "source_rows"])
    else:
        source_counts = (
            score_file_counts.groupby(["dataset", "role", "target_variant", "context_k"], dropna=False, observed=True)
            .agg(
                source_files=("path", "count"),
                raw_rows=("raw_rows", "sum"),
                source_rows=("source_rows", "sum"),
                blank_target_rows=("blank_target_rows", "sum"),
                unscored_rows=("unscored_rows", "sum"),
            )
            .reset_index()
            .sort_values(["dataset", "role", "target_variant", "context_k"])
        )

    comparison = source_counts.merge(
        long_counts,
        on=["dataset", "role", "target_variant", "context_k"],
        how="outer",
    )
    for col in ["source_files", "raw_rows", "source_rows", "blank_target_rows", "unscored_rows", "long_rows"]:
        comparison[col] = pd.to_numeric(comparison[col], errors="coerce").fillna(0).astype("int64")
    comparison["row_delta_long_minus_source"] = comparison["long_rows"] - comparison["source_rows"]
    comparison["status"] = np.where(comparison["row_delta_long_minus_source"].eq(0), "matched", "mismatch")
    comparison = comparison.sort_values(["status", "dataset", "role", "target_variant", "context_k"])

    entropy_rows: list[dict[str, object]] = []
    for name in ["context_entropy_manifest.csv.gz", "context_entropy_features.csv.gz"]:
        path = context_entropy_dir / name
        entropy_rows.append(
            {
                "file": str(path),
                "exists": path.exists(),
                "rows": count_csv_data_rows(path) if path.exists() else 0,
            }
        )
    entropy_audit = pd.DataFrame(entropy_rows)

    audit = pd.DataFrame(
        [
            {
                "check": "scored_csv_files",
                "value": int(len(score_file_counts)),
                "status": "ok" if len(score_file_counts) > 0 else "missing",
            },
            {
                "check": "source_scored_rows",
                "value": int(source_counts["source_rows"].sum()) if not source_counts.empty else 0,
                "status": "ok" if not source_counts.empty else "missing",
            },
            {
                "check": "source_raw_rows",
                "value": int(source_counts["raw_rows"].sum()) if not source_counts.empty else 0,
                "status": "ok" if not source_counts.empty else "missing",
            },
            {
                "check": "source_unscored_or_blank_rows",
                "value": int((source_counts["raw_rows"] - source_counts["source_rows"]).sum()) if not source_counts.empty else 0,
                "status": "documented",
            },
            {
                "check": "long_table_rows",
                "value": int(long_counts["long_rows"].sum()),
                "status": "ok",
            },
            {
                "check": "source_vs_long_mismatched_groups",
                "value": int(comparison["status"].eq("mismatch").sum()) if not comparison.empty else 0,
                "status": "ok" if not comparison["status"].eq("mismatch").any() else "mismatch",
            },
            {
                "check": "context_entropy_feature_rows",
                "value": int(entropy_audit.loc[entropy_audit["file"].str.endswith("context_entropy_features.csv.gz"), "rows"].sum()),
                "status": "ok" if (context_entropy_dir / "context_entropy_features.csv.gz").exists() else "missing",
            },
        ]
    )

    score_file_counts.to_csv(output_dir / "source_scored_file_counts.csv", index=False)
    source_counts.to_csv(output_dir / "source_scored_counts_by_source_role_variant_context.csv", index=False)
    comparison.to_csv(output_dir / "source_tree_vs_long_table_counts.csv", index=False)
    entropy_audit.to_csv(output_dir / "source_context_entropy_file_counts.csv", index=False)
    audit.to_csv(output_dir / "source_audit_summary.csv", index=False)
    return audit, comparison, entropy_audit


def summarize_by_group(frame: pd.DataFrame, group_cols: Sequence[str]) -> pd.DataFrame:
    """Aggregate outcomes and predictors by group."""

    agg_cols = {
        "score_id": "count",
        "age_months": "mean",
        "sum_bits": "mean",
        "bits_per_word": "mean",
        "mean_bits_per_token": "mean",
        "nb_words": "mean",
        "nb_morphemes": "mean",
        "nb_syllables_cmu_or_pkg": "mean",
        "nb_syllables_pkg": "mean",
        "nb_phonemes": "mean",
        "context_entropy_bits": "mean",
    }
    existing = {key: value for key, value in agg_cols.items() if key in frame.columns}
    out = frame.groupby(list(group_cols), observed=True).agg(existing).reset_index()
    out = out.rename(columns={"score_id": "n_rows"})
    return out


def correlation_and_vif(data: AnalysisData, output_dir: Path, fig_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write correlation and VIF diagnostics for core predictors."""

    real_k3 = data.real_rows[data.real_rows["context_k"].eq("k3")].copy()
    context_k3 = data.context_sample[data.context_sample["context_k"].eq("k3")].copy()
    base = real_k3.merge(
        context_k3[["score_id", "context_entropy_bits"]],
        on="score_id",
        how="left",
        suffixes=("", "_ctx_sample"),
    )
    cols = [col for col in PREDICTOR_COLS if col in base.columns]
    corr_frame = base[cols].apply(pd.to_numeric, errors="coerce")
    corr = corr_frame.corr(method="pearson").round(3)
    corr.to_csv(output_dir / "predictor_correlation_pearson.csv")

    vif_rows: list[dict[str, object]] = []
    vif_data = corr_frame.dropna(axis=0, how="any")
    # VIF with all effort measures intentionally exposes collinearity.
    for target in cols:
        predictors = [col for col in cols if col != target]
        if len(predictors) < 2:
            continue
        X = vif_data[predictors].to_numpy(dtype=float)
        y = vif_data[target].to_numpy(dtype=float)
        X = StandardScaler().fit_transform(X)
        model = LinearRegression().fit(X, y)
        r2 = float(model.score(X, y))
        vif = math.inf if r2 >= 0.999999 else 1.0 / max(1e-12, 1.0 - r2)
        vif_rows.append({"predictor": target, "r_squared_from_other_predictors": r2, "vif": vif})
    vif = pd.DataFrame(vif_rows).sort_values("vif", ascending=False)
    vif.to_csv(output_dir / "predictor_vif.csv", index=False)

    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8.5, 7.0))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, square=True, cbar_kws={"label": "Pearson r"})
    plt.title("Predictor Correlations")
    plt.tight_layout()
    plt.savefig(fig_dir / "predictor_correlation_heatmap.png", dpi=220)
    plt.savefig(fig_dir / "predictor_correlation_heatmap.pdf")
    plt.close()
    return corr, vif


def fit_ols_cluster(formula: str, frame: pd.DataFrame, groups: str, label: str) -> tuple[object | None, dict[str, object]]:
    """Fit OLS with child-cluster robust standard errors."""

    try:
        model = smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame[groups]})
        return model, {
            "model": label,
            "status": "fit",
            "n_obs": int(model.nobs),
            "n_children": int(frame[groups].nunique()),
            "r_squared": float(model.rsquared),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "formula": formula,
        }
    except Exception as exc:
        return None, {"model": label, "status": f"failed: {type(exc).__name__}: {exc}", "formula": formula}


def fit_mixedlm(formula: str, frame: pd.DataFrame, label: str, re_formula: str = "1") -> tuple[object | None, dict[str, object]]:
    """Fit Gaussian mixed model with child grouping."""

    try:
        model = smf.mixedlm(formula, data=frame, groups=frame["child_id"], re_formula=re_formula)
        result = model.fit(reml=False, method="lbfgs", maxiter=300, disp=False)
        converged = bool(getattr(result, "converged", False))
        return result, {
            "model": label,
            "status": "fit_converged" if converged else "fit_not_converged",
            "n_obs": int(result.nobs),
            "n_children": int(frame["child_id"].nunique()),
            "aic": float(result.aic),
            "bic": float(result.bic),
            "log_likelihood": float(result.llf),
            "formula": formula,
            "random_effects": re_formula,
        }
    except Exception as exc:
        return None, {"model": label, "status": f"failed: {type(exc).__name__}: {exc}", "formula": formula, "random_effects": re_formula}


def fit_gee(formula: str, frame: pd.DataFrame, label: str, family: object) -> tuple[object | None, dict[str, object]]:
    """Fit a clustered GEE as a GLM-style correlated-data model."""

    try:
        model = smf.gee(
            formula,
            groups="child_id",
            data=frame,
            cov_struct=Exchangeable(),
            family=family,
        )
        result = model.fit(maxiter=100)
        return result, {
            "model": label,
            "status": "fit",
            "n_obs": int(result.nobs),
            "n_children": int(frame["child_id"].nunique()),
            "qic": safe_qic(result),
            "formula": formula,
            "family": result.family.__class__.__name__,
            "cov_struct": result.cov_struct.__class__.__name__,
        }
    except Exception as exc:
        return None, {"model": label, "status": f"failed: {type(exc).__name__}: {exc}", "formula": formula, "family": family.__class__.__name__}


def safe_qic(result: object) -> float | str:
    """Return QIC when statsmodels can compute it."""

    try:
        qic = result.qic()
    except Exception:
        return ""
    if isinstance(qic, tuple):
        return float(qic[0])
    return float(qic)


def coefficient_table(model: object | None, label: str, max_terms: int = 24) -> pd.DataFrame:
    """Return a compact coefficient table from a fitted statsmodels result."""

    if model is None:
        return pd.DataFrame()
    params = getattr(model, "params", pd.Series(dtype=float))
    bse = getattr(model, "bse", pd.Series(index=params.index, dtype=float))
    pvalues = getattr(model, "pvalues", pd.Series(index=params.index, dtype=float))
    rows = []
    for term in list(params.index)[:max_terms]:
        rows.append(
            {
                "model": label,
                "term": term,
                "estimate": float(params[term]),
                "std_error": float(bse.get(term, np.nan)),
                "p_value": float(pvalues.get(term, np.nan)),
            }
        )
    return pd.DataFrame(rows)


def fitted_observed_r2(model: object | None) -> float:
    """Return squared observed/fitted correlation as a descriptive pseudo-R2."""

    if model is None:
        return math.nan
    try:
        observed = np.asarray(model.model.endog, dtype=float)
        fitted = np.asarray(model.fittedvalues, dtype=float)
    except Exception:
        return math.nan
    mask = np.isfinite(observed) & np.isfinite(fitted)
    if mask.sum() < 3 or np.std(observed[mask]) == 0 or np.std(fitted[mask]) == 0:
        return math.nan
    corr = np.corrcoef(observed[mask], fitted[mask])[0, 1]
    return float(corr**2)


def pvalue_for_term(model: object | None, term: str) -> float:
    """Return a p-value for one model term when statsmodels exposes it."""

    if model is None or not hasattr(model, "pvalues"):
        return math.nan
    pvalues = getattr(model, "pvalues")
    try:
        if term in pvalues.index:
            return float(pvalues.loc[term])
    except AttributeError:
        return math.nan
    return math.nan


def min_pvalue_containing(model: object | None, pattern: str) -> float:
    """Return the smallest p-value among terms containing a pattern."""

    if model is None or not hasattr(model, "pvalues"):
        return math.nan
    pvalues = getattr(model, "pvalues")
    try:
        matches = [float(value) for term, value in pvalues.items() if pattern in str(term)]
    except AttributeError:
        return math.nan
    matches = [value for value in matches if math.isfinite(value)]
    return min(matches) if matches else math.nan


def canonical_r2(model: object | None) -> float:
    """Return OLS R2 when available, otherwise descriptive fitted-observed R2."""

    if model is None:
        return math.nan
    if hasattr(model, "rsquared"):
        try:
            return float(model.rsquared)
        except Exception:
            return math.nan
    return fitted_observed_r2(model)


def r2_type(model: object | None) -> str:
    """Return the interpretation label for the reported R2."""

    if model is not None and hasattr(model, "rsquared"):
        return "OLS R2"
    return "descriptive fitted-observed R2"


def model_status(model_summary: pd.DataFrame, label: str) -> str:
    """Return the fit status for a model label."""

    row = model_summary[model_summary["model"].eq(label)]
    if row.empty:
        return ""
    return str(row.iloc[0].get("status", ""))


def build_model_interpretation_stats(
    model_summary: pd.DataFrame,
    model_objects: Mapping[str, object],
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write full and short model-stat tables for plot annotation/review."""

    specs = [
        {
            "model_key": "m1",
            "model": "M1 OLS total bits",
            "outcome": "sum_bits",
            "controlled_for": "nb_words",
            "context": "k0/no context",
        },
        {
            "model_key": "m2",
            "model": "M2 OLS efficiency controls",
            "outcome": "bits_per_word",
            "controlled_for": "log_nb_words",
            "context": "k3 fixed",
        },
        {
            "model_key": "m3",
            "model": "M3 LMM child random intercept",
            "outcome": "bits_per_word",
            "controlled_for": "log_nb_words + child random intercept",
            "context": "k3 fixed",
        },
        {
            "model_key": "m4",
            "model": "M4 LMM child random intercept + age slope",
            "outcome": "bits_per_word",
            "controlled_for": "log_nb_words + child random intercept/slope",
            "context": "k3 fixed",
        },
        {
            "model_key": "m5",
            "model": "M5 Gamma GEE baseline comparison",
            "outcome": "sum_bits",
            "controlled_for": "nb_words + target variant + child-clustered correlation",
            "context": "k3 fixed",
        },
        {
            "model_key": "context_extension",
            "model": "Context extension Gaussian GEE",
            "outcome": "bits_per_word",
            "controlled_for": "log_nb_words + context_entropy_bits + context_k",
            "context": "k1/k2/k3 matched entropy rows",
        },
    ]
    rows = []
    for spec in specs:
        model = model_objects.get(spec["model_key"])
        row = {
            **spec,
            "status": model_status(model_summary, spec["model"]),
            "r2": canonical_r2(model),
            "r2_type": r2_type(model),
            "p_age_scaled": pvalue_for_term(model, "age_scaled"),
            "p_age_scaled_sq": pvalue_for_term(model, "age_scaled_sq"),
            "p_nb_words": pvalue_for_term(model, "nb_words"),
            "p_log_nb_words": pvalue_for_term(model, "log_nb_words"),
            "p_context_entropy_bits": pvalue_for_term(model, "context_entropy_bits"),
            "min_p_target_variant": min_pvalue_containing(model, "C(target_variant)"),
            "min_p_age_by_variant": min_pvalue_containing(model, "age_scaled:C(target_variant)"),
        }
        rows.append(row)
    full = pd.DataFrame(rows)
    short = full[["model", "status", "r2", "r2_type", "p_age_scaled"]].copy()
    short = short.rename(columns={"p_age_scaled": "p_age"})
    full.to_csv(output_dir / "model_interpretation_stats_full.csv", index=False)
    short.to_csv(output_dir / "model_interpretation_stats_short.csv", index=False)
    return full, short


def format_p(value: object) -> str:
    """Format a p-value compactly for figures and tables."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "NA"
    if not math.isfinite(parsed):
        return "NA"
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def format_r2(value: object) -> str:
    """Format R2 compactly for figures and tables."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "NA"
    if not math.isfinite(parsed):
        return "NA"
    return f"{parsed:.3f}"


def stat_label(model_stats: pd.DataFrame, model_key: str) -> str:
    """Return a compact R2/p annotation for one model."""

    row = model_stats[model_stats["model_key"].eq(model_key)]
    if row.empty:
        return ""
    row = row.iloc[0]
    return f"R2={format_r2(row['r2'])}\np(age)={format_p(row['p_age_scaled'])}"


def add_stats_box(ax: plt.Axes, label: str) -> None:
    """Add a small model-stat annotation to a plot."""

    if not label:
        return
    ax.text(
        0.02,
        0.98,
        label,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#999999", "alpha": 0.86, "boxstyle": "round,pad=0.35"},
    )


def write_placeholder_plot(fig_dir: Path, stem: str, title: str, message: str) -> None:
    """Write a placeholder figure when a candidate model diagnostic is unavailable."""

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.58, title, ha="center", va="center", fontsize=14, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10, wrap=True)
    fig.tight_layout()
    fig.savefig(fig_dir / f"{stem}.png", dpi=220)
    fig.savefig(fig_dir / f"{stem}.pdf")
    plt.close(fig)


def safe_random_effects(model: object | None) -> Mapping[str, object]:
    """Return random effects, or an empty mapping when unavailable."""

    if model is None:
        return {}
    try:
        return getattr(model, "random_effects")
    except Exception:
        return {}


def fit_models(data: AnalysisData, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, Mapping[str, object]]:
    """Fit the preliminary candidate models."""

    model_objects: dict[str, object] = {}
    summaries: list[dict[str, object]] = []
    coefs: list[pd.DataFrame] = []

    real = data.real_sample.copy()
    real_k0 = real[real["context_k"].eq("k0")].copy()
    real_k3 = real[real["context_k"].eq("k3")].copy()
    context = data.context_sample.copy()
    baseline = data.baseline_sample.copy()

    m1, s1 = fit_ols_cluster(
        "sum_bits ~ age_scaled + nb_words",
        real_k0,
        "child_id",
        "M1 OLS total bits",
    )
    summaries.append(s1)
    coefs.append(coefficient_table(m1, s1["model"]))
    if m1 is not None:
        model_objects["m1"] = m1

    m2, s2 = fit_ols_cluster(
        "bits_per_word ~ age_scaled + age_scaled_sq + log_nb_words",
        real_k3,
        "child_id",
        "M2 OLS efficiency controls",
    )
    summaries.append(s2)
    coefs.append(coefficient_table(m2, s2["model"]))
    if m2 is not None:
        model_objects["m2"] = m2

    m3, s3 = fit_mixedlm(
        "bits_per_word ~ age_scaled + log_nb_words",
        real_k3,
        "M3 LMM child random intercept",
        re_formula="1",
    )
    summaries.append(s3)
    coefs.append(coefficient_table(m3, s3["model"]))
    if m3 is not None:
        model_objects["m3"] = m3

    # Use a smaller balanced sample for the random-slope fit to improve stability.
    slope_data = stratified_sample(real_k3, ["child_id", "age_bin"], n_per_group=120)
    m4, s4 = fit_mixedlm(
        "bits_per_word ~ age_scaled + log_nb_words",
        slope_data,
        "M4 LMM child random intercept + age slope",
        re_formula="1 + age_scaled",
    )
    summaries.append(s4 | {"sample_note": "balanced 120 rows per child-age-bin where available"})
    coefs.append(coefficient_table(m4, s4["model"]))
    if m4 is not None:
        model_objects["m4"] = m4

    gee_data = baseline[
        baseline["target_variant"].isin(VARIANT_ORDER)
        & baseline["context_k"].eq("k3")
    ].copy()
    # Positive continuous outcome with child-level correlation; includes generated baselines.
    m5, s5 = fit_gee(
        "sum_bits ~ age_scaled * C(target_variant) + nb_words",
        gee_data,
        "M5 Gamma GEE baseline comparison",
        Gamma(link=Log()),
    )
    summaries.append(s5)
    coefs.append(coefficient_table(m5, s5["model"]))
    if m5 is not None:
        model_objects["m5"] = m5

    m6, s6 = fit_gee(
        "bits_per_word ~ age_scaled + log_nb_words + context_entropy_bits + C(context_k)",
        context,
        "Context extension Gaussian GEE",
        Gaussian(),
    )
    summaries.append(s6)
    coefs.append(coefficient_table(m6, s6["model"]))
    if m6 is not None:
        model_objects["context_extension"] = m6

    summary_df = pd.DataFrame(summaries)
    coef_df = pd.concat([table for table in coefs if not table.empty], ignore_index=True)
    summary_df.to_csv(output_dir / "model_fit_summary.csv", index=False)
    coef_df.to_csv(output_dir / "model_coefficient_summary.csv", index=False)
    return summary_df, coef_df, model_objects


def save_aggregate_tables(data: AnalysisData, output_dir: Path) -> dict[str, pd.DataFrame]:
    """Write small aggregate tables used for plots and report summaries."""

    tables = {
        "real_age_context": summarize_by_group(data.real_rows, ["age_bin", "context_k"]),
        "real_child_age_context": summarize_by_group(data.real_rows, ["dataset", "child_id", "age_bin", "context_k"]),
        "baseline_age_variant_k3": summarize_by_group(data.baseline_k3_rows, ["age_bin", "target_variant"]),
        "baseline_child_age_variant_k3": summarize_by_group(data.baseline_k3_rows, ["dataset", "child_id", "age_bin", "target_variant"]),
        "context_entropy_child_real": summarize_by_group(
            data.real_rows[data.real_rows["context_entropy_join_status"].isin(["matched", "matched_text_fallback"])],
            ["age_bin", "context_k"],
        ),
    }
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
    return tables


def ci95(mean: pd.Series, sem: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return lower/upper 95% normal-approximation intervals."""

    return mean - 1.96 * sem, mean + 1.96 * sem


def plot_age_context_trends(tables: Mapping[str, pd.DataFrame], fig_dir: Path) -> None:
    """Plot child real information trends by context window."""

    agg = tables["real_child_age_context"].dropna(subset=["bits_per_word", "sum_bits"]).copy()
    for metric, ylabel, filename in [
        ("bits_per_word", "Mean bits per word", "real_child_bits_per_word_by_age_context"),
        ("sum_bits", "Mean total bits", "real_child_sum_bits_by_age_context"),
    ]:
        summary = agg.groupby(["age_bin", "context_k"], observed=True)[metric].agg(["mean", "sem"]).reset_index()
        summary["x"] = summary["age_bin"].map({label: idx for idx, label in enumerate(AGE_BIN_ORDER)})
        low, high = ci95(summary["mean"], summary["sem"].fillna(0))
        plt.figure(figsize=(9.0, 5.2))
        for context_k, group in summary.groupby("context_k", observed=True):
            group = group.sort_values("x")
            lo = low.loc[group.index]
            hi = high.loc[group.index]
            plt.plot(group["x"], group["mean"], marker="o", label=str(context_k))
            plt.fill_between(group["x"].astype(float).to_numpy(), lo.to_numpy(), hi.to_numpy(), alpha=0.13)
        plt.xticks(range(len(AGE_BIN_ORDER)), AGE_BIN_ORDER, rotation=35, ha="right")
        plt.ylabel(ylabel)
        plt.xlabel("Age bin")
        plt.title(ylabel + " by Age and Context")
        plt.grid(alpha=0.25)
        plt.legend(title="Scoring context")
        plt.tight_layout()
        plt.savefig(fig_dir / f"{filename}.png", dpi=220)
        plt.savefig(fig_dir / f"{filename}.pdf")
        plt.close()


def plot_baseline_comparison(tables: Mapping[str, pd.DataFrame], fig_dir: Path) -> None:
    """Plot real and generated baseline utterance information."""

    agg = tables["baseline_child_age_variant_k3"].dropna(subset=["bits_per_word"]).copy()
    summary = agg.groupby(["age_bin", "target_variant"], observed=True)["bits_per_word"].agg(["mean", "sem"]).reset_index()
    summary["x"] = summary["age_bin"].map({label: idx for idx, label in enumerate(AGE_BIN_ORDER)})
    palette = {
        "real": "#1f5a5f",
        "random": "#b9473f",
        "unigram": "#b8872d",
        "bigram": "#4869a8",
        "trigram": "#5f7f3a",
    }
    plt.figure(figsize=(9.2, 5.4))
    for variant in VARIANT_ORDER:
        group = summary[summary["target_variant"].eq(variant)].sort_values("x")
        if group.empty:
            continue
        low, high = ci95(group["mean"], group["sem"].fillna(0))
        plt.plot(group["x"], group["mean"], marker="o", label=variant, color=palette.get(variant))
        plt.fill_between(group["x"].astype(float).to_numpy(), low.to_numpy(), high.to_numpy(), alpha=0.12, color=palette.get(variant))
    plt.xticks(range(len(AGE_BIN_ORDER)), AGE_BIN_ORDER, rotation=35, ha="right")
    plt.ylabel("Mean bits per word")
    plt.xlabel("Age bin")
    plt.title("Real vs Baseline Utterances")
    plt.grid(alpha=0.25)
    plt.legend(title="Target")
    plt.tight_layout()
    plt.savefig(fig_dir / "baseline_bits_per_word_by_age.png", dpi=220)
    plt.savefig(fig_dir / "baseline_bits_per_word_by_age.pdf")
    plt.close()


def plot_context_entropy(data: AnalysisData, fig_dir: Path) -> None:
    """Plot relation between context entropy and target information."""

    frame = data.context_sample.dropna(subset=["context_entropy_bits", "bits_per_word"]).copy()
    if frame.empty:
        return
    frame["entropy_bin"] = pd.qcut(frame["context_entropy_bits"], q=10, duplicates="drop")
    summary = frame.groupby(["entropy_bin", "context_k"], observed=True).agg(
        context_entropy_bits=("context_entropy_bits", "mean"),
        bits_per_word=("bits_per_word", "mean"),
        sem=("bits_per_word", "sem"),
        n_rows=("score_id", "count"),
    ).reset_index()
    plt.figure(figsize=(8.4, 5.0))
    for context_k, group in summary.groupby("context_k", observed=True):
        group = group.sort_values("context_entropy_bits")
        low, high = ci95(group["bits_per_word"], group["sem"].fillna(0))
        plt.plot(group["context_entropy_bits"], group["bits_per_word"], marker="o", label=str(context_k))
        plt.fill_between(group["context_entropy_bits"].to_numpy(), low.to_numpy(), high.to_numpy(), alpha=0.12)
    plt.xlabel("Context entropy (bits)")
    plt.ylabel("Target bits per word")
    plt.title("Context Uncertainty and Child Utterance Information")
    plt.grid(alpha=0.25)
    plt.legend(title="Context window")
    plt.tight_layout()
    plt.savefig(fig_dir / "context_entropy_vs_bits_per_word.png", dpi=220)
    plt.savefig(fig_dir / "context_entropy_vs_bits_per_word.pdf")
    plt.close()


def plot_model_predictions(data: AnalysisData, model_objects: Mapping[str, object], fig_dir: Path) -> None:
    """Plot simple fitted developmental curves for OLS and mixed models."""

    real_k3 = data.real_sample[data.real_sample["context_k"].eq("k3")].copy()
    if real_k3.empty:
        return
    grid = pd.DataFrame(
        {
            "age_months": np.linspace(real_k3["age_months"].min(), real_k3["age_months"].max(), 120),
            "nb_words": float(real_k3["nb_words"].median()),
            "log_nb_words": math.log(float(real_k3["nb_words"].median())),
            "dataset": "Providence",
            "child_id": "reference",
        }
    )
    grid["age_centered"] = grid["age_months"] - real_k3["age_months"].mean()
    grid["age_scaled"] = grid["age_centered"] / real_k3["age_months"].std(ddof=0)
    grid["age_scaled_sq"] = grid["age_scaled"] ** 2
    plt.figure(figsize=(8.4, 5.1))
    observed = real_k3.groupby("age_bin", observed=True)["bits_per_word"].mean().reset_index()
    observed["age_mid"] = observed["age_bin"].astype(str).map(age_bin_midpoint)
    plt.scatter(observed["age_mid"], observed["bits_per_word"], color="#1f5a5f", s=42, label="Observed age-bin means")
    for key, label, color in [
        ("m2", "OLS effort controls", "#c76f2c"),
        ("m3", "LMM random intercept", "#4869a8"),
        ("m4", "LMM random age slope", "#5f7f3a"),
    ]:
        model = model_objects.get(key)
        if model is None:
            continue
        try:
            pred = model.predict(grid)
        except Exception:
            continue
        plt.plot(grid["age_months"], pred, label=label, color=color, linewidth=2)
    plt.xlabel("Age in months")
    plt.ylabel("Bits per word")
    plt.title("Candidate Model Developmental Fits")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "candidate_model_fitted_age_curves.png", dpi=220)
    plt.savefig(fig_dir / "candidate_model_fitted_age_curves.pdf")
    plt.close()


def add_age_terms_from_reference(grid: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Add age transforms using the same reference frame as the fitted model."""

    out = grid.copy()
    age_std = reference["age_months"].std(ddof=0)
    if not math.isfinite(age_std) or age_std == 0:
        age_std = 1.0
    out["age_centered"] = out["age_months"] - reference["age_months"].mean()
    out["age_scaled"] = out["age_centered"] / age_std
    out["age_scaled_sq"] = out["age_scaled"] ** 2
    return out


def real_age_grid(reference: pd.DataFrame, n: int = 120) -> np.ndarray:
    """Return an age grid spanning the observed real-child age range."""

    return np.linspace(reference["age_months"].min(), reference["age_months"].max(), n)


def extract_random_effect_value(effect: object, candidates: Sequence[str], fallback_index: int = 0) -> float:
    """Extract one random-effect value from a statsmodels random-effect series."""

    if isinstance(effect, pd.Series):
        for key in candidates:
            if key in effect.index:
                return float(effect.loc[key])
        if len(effect) > fallback_index:
            return float(effect.iloc[fallback_index])
    if isinstance(effect, np.ndarray) and len(effect) > fallback_index:
        return float(effect[fallback_index])
    if isinstance(effect, Sequence) and not isinstance(effect, str) and len(effect) > fallback_index:
        return float(effect[fallback_index])
    return math.nan


def plot_model1_adjusted_total_bits(
    data: AnalysisData,
    model_objects: Mapping[str, object],
    model_stats: pd.DataFrame,
    fig_dir: Path,
) -> None:
    """Plot Model 1 total-bit predictions at fixed utterance lengths."""

    model = model_objects.get("m1")
    if model is None:
        return
    real_k0 = data.real_sample[data.real_sample["context_k"].eq("k0")].copy()
    if real_k0.empty:
        return
    word_levels = sorted({int(round(x)) for x in real_k0["nb_words"].quantile([0.25, 0.50, 0.75]).tolist()})
    word_levels = [max(1, value) for value in word_levels]
    age_values = real_age_grid(data.real_rows)
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    for nb_words in word_levels:
        grid = pd.DataFrame({"age_months": age_values, "nb_words": float(nb_words)})
        grid = add_age_terms_from_reference(grid, data.real_rows)
        pred = model.predict(grid)
        ax.plot(age_values, pred, linewidth=2, label=f"{nb_words} words")
    observed = real_k0.groupby("age_bin", observed=True)["sum_bits"].mean().reset_index()
    observed["age_mid"] = observed["age_bin"].astype(str).map(age_bin_midpoint)
    ax.scatter(observed["age_mid"], observed["sum_bits"], s=34, color="#333333", alpha=0.55, label="Raw age-bin means")
    add_stats_box(ax, stat_label(model_stats, "m1"))
    ax.set_xlabel("Age in months")
    ax.set_ylabel("Predicted total bits")
    ax.set_title("M1 Adjusted Total Bits")
    ax.grid(alpha=0.25)
    ax.legend(title="Fixed length")
    fig.tight_layout()
    fig.savefig(fig_dir / "model1_adjusted_total_bits_by_age.png", dpi=220)
    fig.savefig(fig_dir / "model1_adjusted_total_bits_by_age.pdf")
    plt.close(fig)


def plot_model2_adjusted_bits_per_word(
    data: AnalysisData,
    model_objects: Mapping[str, object],
    model_stats: pd.DataFrame,
    fig_dir: Path,
) -> None:
    """Plot Model 2 bits-per-word predictions at fixed length."""

    model = model_objects.get("m2")
    if model is None:
        return
    real_k3 = data.real_sample[data.real_sample["context_k"].eq("k3")].copy()
    if real_k3.empty:
        return
    age_values = real_age_grid(data.real_rows)
    median_words = float(real_k3["nb_words"].median())
    grid = pd.DataFrame(
        {
            "age_months": age_values,
            "nb_words": median_words,
            "log_nb_words": math.log(median_words),
        }
    )
    grid = add_age_terms_from_reference(grid, data.real_rows)
    pred = model.predict(grid)
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    observed = real_k3.groupby("age_bin", observed=True)["bits_per_word"].mean().reset_index()
    observed["age_mid"] = observed["age_bin"].astype(str).map(age_bin_midpoint)
    ax.scatter(observed["age_mid"], observed["bits_per_word"], color="#333333", s=34, alpha=0.55, label="Raw age-bin means")
    ax.plot(age_values, pred, linewidth=2.4, color="#c76f2c", label=f"Adjusted, {median_words:.0f} words")
    add_stats_box(ax, stat_label(model_stats, "m2"))
    ax.set_xlabel("Age in months")
    ax.set_ylabel("Predicted bits per word")
    ax.set_title("M2 Adjusted Bits Per Word")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "model2_adjusted_bits_per_word.png", dpi=220)
    fig.savefig(fig_dir / "model2_adjusted_bits_per_word.pdf")
    plt.close(fig)


def plot_model3_child_random_intercepts(
    model_objects: Mapping[str, object],
    model_stats: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> None:
    """Plot Model 3 child random intercepts."""

    model = model_objects.get("m3")
    random_effects = safe_random_effects(model)
    if not random_effects:
        write_placeholder_plot(
            fig_dir,
            "model3_child_random_intercepts",
            "M3 Random Effects Unavailable",
            "Statsmodels could not extract child random intercepts, usually because the fitted random-effect covariance was singular.",
        )
        return
    rows = []
    for child_id, effect in random_effects.items():
        rows.append({"child_id": child_id, "random_intercept": extract_random_effect_value(effect, ["Group", "Intercept"])})
    frame = pd.DataFrame(rows).dropna(subset=["random_intercept"]).sort_values("random_intercept")
    if frame.empty:
        return
    frame.to_csv(output_dir / "model3_child_random_intercepts.csv", index=False)
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.scatter(frame["random_intercept"], np.arange(len(frame)), color="#4869a8", s=34)
    ax.axvline(0, color="#333333", linewidth=1, alpha=0.6)
    ax.set_yticks(np.arange(len(frame)))
    ax.set_yticklabels(frame["child_id"], fontsize=7)
    add_stats_box(ax, stat_label(model_stats, "m3"))
    ax.set_xlabel("Child random intercept")
    ax.set_ylabel("Child")
    ax.set_title("M3 Child-Specific Baselines")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "model3_child_random_intercepts.png", dpi=220)
    fig.savefig(fig_dir / "model3_child_random_intercepts.pdf")
    plt.close(fig)


def plot_model4_random_slope_pilot(
    model_objects: Mapping[str, object],
    model_stats: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> None:
    """Plot Model 4 random intercepts and slopes when the pilot fit returns them."""

    model = model_objects.get("m4")
    random_effects = safe_random_effects(model)
    if not random_effects:
        write_placeholder_plot(
            fig_dir,
            "model4_random_slope_pilot",
            "M4 Random Effects Unavailable",
            "The random-slope pilot did not yield stable extractable child random effects. Treat this model as a candidate requiring refitting.",
        )
        return
    rows = []
    for child_id, effect in random_effects.items():
        rows.append(
            {
                "child_id": child_id,
                "random_intercept": extract_random_effect_value(effect, ["Group", "Intercept"], 0),
                "random_age_slope": extract_random_effect_value(effect, ["age_scaled"], 1),
            }
        )
    frame = pd.DataFrame(rows).dropna(subset=["random_intercept", "random_age_slope"])
    if frame.empty:
        return
    frame.to_csv(output_dir / "model4_child_random_slope_pilot.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.scatter(frame["random_intercept"], frame["random_age_slope"], color="#5f7f3a", s=42)
    for _, row in frame.iterrows():
        ax.annotate(str(row["child_id"]), (row["random_intercept"], row["random_age_slope"]), fontsize=6, alpha=0.75)
    ax.axhline(0, color="#333333", linewidth=1, alpha=0.5)
    ax.axvline(0, color="#333333", linewidth=1, alpha=0.5)
    add_stats_box(ax, stat_label(model_stats, "m4"))
    ax.set_xlabel("Random intercept")
    ax.set_ylabel("Random age slope")
    ax.set_title("M4 Random-Slope Pilot (Not Converged)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "model4_random_slope_pilot.png", dpi=220)
    fig.savefig(fig_dir / "model4_random_slope_pilot.pdf")
    plt.close(fig)


def plot_model5_baseline_adjusted_predictions(
    data: AnalysisData,
    model_objects: Mapping[str, object],
    model_stats: pd.DataFrame,
    fig_dir: Path,
) -> None:
    """Plot Model 5 adjusted total-bit predictions for real and baseline targets."""

    model = model_objects.get("m5")
    if model is None:
        return
    baseline = data.baseline_sample.copy()
    if baseline.empty:
        return
    age_values = real_age_grid(data.baseline_k3_rows)
    median_words = float(baseline["nb_words"].median())
    palette = {
        "real": "#1f5a5f",
        "random": "#b9473f",
        "unigram": "#b8872d",
        "bigram": "#4869a8",
        "trigram": "#5f7f3a",
    }
    plt.figure(figsize=(8.8, 5.2))
    for variant in VARIANT_ORDER:
        grid = pd.DataFrame(
            {
                "age_months": age_values,
                "target_variant": variant,
                "nb_words": median_words,
            }
        )
        grid = add_age_terms_from_reference(grid, data.baseline_k3_rows)
        pred = model.predict(grid)
        plt.plot(age_values, pred, linewidth=2, label=variant, color=palette.get(variant))
    add_stats_box(plt.gca(), stat_label(model_stats, "m5"))
    plt.xlabel("Age in months")
    plt.ylabel("Predicted total bits")
    plt.title("M5 Adjusted Real vs Baselines")
    plt.grid(alpha=0.25)
    plt.legend(title=f"Target, {median_words:.0f} words")
    plt.tight_layout()
    plt.savefig(fig_dir / "model5_adjusted_baseline_predictions.png", dpi=220)
    plt.savefig(fig_dir / "model5_adjusted_baseline_predictions.pdf")
    plt.close()


def plot_five_model_results(
    data: AnalysisData,
    model_objects: Mapping[str, object],
    model_stats: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> None:
    """Write one compact result plot for each of the five candidate models."""

    plot_model1_adjusted_total_bits(data, model_objects, model_stats, fig_dir)
    plot_model2_adjusted_bits_per_word(data, model_objects, model_stats, fig_dir)
    plot_model3_child_random_intercepts(model_objects, model_stats, output_dir, fig_dir)
    plot_model4_random_slope_pilot(model_objects, model_stats, output_dir, fig_dir)
    plot_model5_baseline_adjusted_predictions(data, model_objects, model_stats, fig_dir)


def comparison_palette() -> dict[str, str]:
    """Return stable colors for real, generated, and caretaker comparison groups."""

    return {
        "real": "#1f5a5f",
        "random": "#b9473f",
        "unigram": "#b8872d",
        "bigram": "#4869a8",
        "trigram": "#5f7f3a",
        "caretaker": "#6d5a8d",
    }


def build_effort_comparison_frame(data: AnalysisData, *, include_caretaker: bool) -> pd.DataFrame:
    """Return child baseline rows plus optionally caregiver rows for effort sensitivity."""

    child = data.baseline_sample.copy()
    child["comparison_group"] = child["target_variant"].astype(str)
    child["comparison_scope"] = "child_real_and_baselines"
    parts = [child]
    if include_caretaker:
        caretaker = data.caretaker_sample.copy()
        caretaker["comparison_group"] = "caretaker"
        caretaker["comparison_scope"] = "child_real_baselines_and_caretaker"
        parts.append(caretaker)
    frame = pd.concat(parts, ignore_index=True)
    frame = frame[frame["comparison_group"].isin(COMPARISON_ORDER)].copy()
    frame["comparison_group"] = pd.Categorical(frame["comparison_group"], COMPARISON_ORDER, ordered=True)
    return frame


def fit_effort_sensitivity_models(data: AnalysisData, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit utterance-level total-bit models with one effort control at a time."""

    stats_rows: list[dict[str, object]] = []
    coef_rows: list[pd.DataFrame] = []
    prediction_rows: list[pd.DataFrame] = []
    scopes = [
        ("child_real_and_baselines", False, "Child real + generated baselines"),
        ("child_real_baselines_and_caretaker", True, "Child real + generated baselines + caretakers"),
    ]
    for scope, include_caretaker, scope_label in scopes:
        frame = build_effort_comparison_frame(data, include_caretaker=include_caretaker)
        for effort_col, effort_label in EFFORT_CONTROLS:
            model_frame = frame.copy()
            model_frame["effort_value"] = pd.to_numeric(model_frame[effort_col], errors="coerce")
            model_frame = model_frame[np.isfinite(model_frame["effort_value"]) & (model_frame["effort_value"] > 0)].copy()
            if model_frame.empty:
                continue
            if hasattr(model_frame["comparison_group"], "cat"):
                model_frame["comparison_group"] = model_frame["comparison_group"].cat.remove_unused_categories()
            model_frame = add_age_terms_from_reference(model_frame, model_frame)
            formula = "sum_bits ~ age_scaled * C(comparison_group) + effort_value"
            model, summary = fit_ols_cluster(
                formula,
                model_frame,
                "child_id",
                f"{scope_label}: control={effort_label}",
            )
            if model is None:
                stats_rows.append(
                    {
                        "scope": scope,
                        "scope_label": scope_label,
                        "effort_control": effort_col,
                        "effort_label": effort_label,
                        "status": summary.get("status", "failed"),
                    }
                )
                continue
            coef = coefficient_table(model, summary["model"], max_terms=80)
            if not coef.empty:
                coef["scope"] = scope
                coef["effort_control"] = effort_col
                coef_rows.append(coef)
            stats_rows.append(
                {
                    "scope": scope,
                    "scope_label": scope_label,
                    "effort_control": effort_col,
                    "effort_label": effort_label,
                    "status": summary.get("status", ""),
                    "n_obs": int(model.nobs),
                    "n_children": int(model_frame["child_id"].nunique()),
                    "r2": float(model.rsquared),
                    "r2_type": "OLS R2",
                    "p_age": pvalue_for_term(model, "age_scaled"),
                    "p_effort": pvalue_for_term(model, "effort_value"),
                    "min_p_group": min_pvalue_containing(model, "C(comparison_group)"),
                    "min_p_age_by_group": min_pvalue_containing(model, "age_scaled:C(comparison_group)"),
                    "formula": formula,
                }
            )
            age_values = real_age_grid(model_frame)
            fixed_effort = float(model_frame["effort_value"].median())
            pred_parts = []
            for group in COMPARISON_ORDER:
                if group not in set(model_frame["comparison_group"].astype(str)):
                    continue
                grid = pd.DataFrame(
                    {
                        "age_months": age_values,
                        "comparison_group": group,
                        "effort_value": fixed_effort,
                    }
                )
                grid = add_age_terms_from_reference(grid, model_frame)
                grid["predicted_sum_bits"] = model.predict(grid)
                grid["scope"] = scope
                grid["scope_label"] = scope_label
                grid["effort_control"] = effort_col
                grid["effort_label"] = effort_label
                grid["fixed_effort_value"] = fixed_effort
                pred_parts.append(grid)
            if pred_parts:
                prediction_rows.append(pd.concat(pred_parts, ignore_index=True))

    stats_df = pd.DataFrame(stats_rows)
    coef_df = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    pred_df = pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()
    stats_df.to_csv(output_dir / "effort_sensitivity_model_stats_full.csv", index=False)
    short_cols = ["scope_label", "effort_label", "status", "r2", "p_age", "p_effort", "min_p_group", "min_p_age_by_group"]
    stats_df[[col for col in short_cols if col in stats_df.columns]].to_csv(
        output_dir / "effort_sensitivity_model_stats_short.csv",
        index=False,
    )
    coef_df.to_csv(output_dir / "effort_sensitivity_model_coefficients.csv", index=False)
    pred_df.to_csv(output_dir / "effort_sensitivity_adjusted_predictions.csv", index=False)
    return stats_df, coef_df, pred_df


def fit_child_control_ladder(data: AnalysisData, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit real-child utterance models with increasing child-control structure."""

    rows: list[dict[str, object]] = []
    coef_rows: list[pd.DataFrame] = []
    base = data.real_sample[data.real_sample["context_k"].eq("k3")].copy()
    for effort_col, effort_label in EFFORT_CONTROLS:
        frame = base.copy()
        frame["effort_value"] = pd.to_numeric(frame[effort_col], errors="coerce")
        frame = frame[np.isfinite(frame["effort_value"]) & (frame["effort_value"] > 0)].copy()
        if frame.empty:
            continue
        frame = add_age_terms_from_reference(frame, frame)
        specs = [
            ("length_age_only", "OLS: age + effort", "sum_bits ~ age_scaled + effort_value", "ols_cluster", "no child term; child-clustered SE"),
            ("child_fixed_effects", "OLS: age + effort + child fixed effects", "sum_bits ~ age_scaled + effort_value + C(child_id)", "ols_cluster", "child fixed effects; child-clustered SE"),
            ("gee_child_exchangeable", "GEE: age + effort grouped by child", "sum_bits ~ age_scaled + effort_value", "gee", "child exchangeable correlation"),
        ]
        for control_key, control_label, formula, fit_type, interpretation in specs:
            if fit_type == "ols_cluster":
                model, summary = fit_ols_cluster(formula, frame, "child_id", f"{control_label}: {effort_label}")
            else:
                model, summary = fit_gee(formula, frame, f"{control_label}: {effort_label}", Gaussian())
            if model is not None:
                coef = coefficient_table(model, summary["model"], max_terms=80)
                if not coef.empty:
                    coef["effort_control"] = effort_col
                    coef["effort_label"] = effort_label
                    coef["child_control"] = control_key
                    coef_rows.append(coef)
            rows.append(
                {
                    "effort_control": effort_col,
                    "effort_label": effort_label,
                    "child_control": control_key,
                    "child_control_label": control_label,
                    "status": summary.get("status", ""),
                    "n_obs": summary.get("n_obs", math.nan),
                    "n_children": summary.get("n_children", frame["child_id"].nunique()),
                    "r2": canonical_r2(model),
                    "r2_type": r2_type(model),
                    "p_age": pvalue_for_term(model, "age_scaled"),
                    "p_effort": pvalue_for_term(model, "effort_value"),
                    "formula": formula,
                    "interpretation": interpretation,
                }
            )
    stats_df = pd.DataFrame(rows)
    coef_df = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    stats_df.to_csv(output_dir / "child_control_ladder_stats.csv", index=False)
    coef_df.to_csv(output_dir / "child_control_ladder_coefficients.csv", index=False)
    return stats_df, coef_df


def plot_child_control_ladder(stats_df: pd.DataFrame, fig_dir: Path) -> None:
    """Plot age p-values and R2 across effort controls and child-control strategies."""

    if stats_df.empty:
        return
    frame = stats_df.copy()
    effort_order = [label for _, label in EFFORT_CONTROLS]
    control_order = ["length_age_only", "child_fixed_effects", "gee_child_exchangeable"]
    control_labels = {
        "length_age_only": "Length + age",
        "child_fixed_effects": "Child fixed effects",
        "gee_child_exchangeable": "GEE by child",
    }
    frame["effort_label"] = pd.Categorical(frame["effort_label"], effort_order, ordered=True)
    frame["child_control"] = pd.Categorical(frame["child_control"], control_order, ordered=True)
    frame["minus_log10_p_age"] = frame["p_age"].map(
        lambda value: -math.log10(max(float(value), 1e-300)) if pd.notna(value) and math.isfinite(float(value)) else math.nan
    )
    palette = {
        "length_age_only": "#1f5a5f",
        "child_fixed_effects": "#b8872d",
        "gee_child_exchangeable": "#4869a8",
    }
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 8.4), sharex=True)
    for control in control_order:
        sub = frame[frame["child_control"].eq(control)].sort_values("effort_label")
        if sub.empty:
            continue
        axes[0].plot(sub["effort_label"].astype(str), sub["r2"], marker="o", linewidth=2, label=control_labels[control], color=palette[control])
        axes[1].plot(sub["effort_label"].astype(str), sub["minus_log10_p_age"], marker="o", linewidth=2, label=control_labels[control], color=palette[control])
    axes[0].set_ylabel("R2 / pseudo-R2")
    axes[0].set_title("Child-Control Ladder: Fit")
    axes[0].grid(alpha=0.25)
    axes[0].legend(title="Model")
    axes[1].axhline(-math.log10(0.05), color="#333333", linestyle="--", linewidth=1, alpha=0.6)
    axes[1].set_ylabel("-log10 p(age)")
    axes[1].set_xlabel("Effort control")
    axes[1].set_title("Child-Control Ladder: Age Effect")
    axes[1].grid(alpha=0.25)
    plt.setp(axes[1].get_xticklabels(), rotation=25, ha="right")
    fig.tight_layout()
    fig.savefig(fig_dir / "child_control_ladder_r2_age_pvalues.png", dpi=220)
    fig.savefig(fig_dir / "child_control_ladder_r2_age_pvalues.pdf")
    plt.close(fig)


def plot_effort_sensitivity_grid(
    stats_df: pd.DataFrame,
    pred_df: pd.DataFrame,
    fig_dir: Path,
    *,
    scope: str,
    detail: str,
) -> None:
    """Plot adjusted utterance-level predictions for effort-control permutations."""

    scope_pred = pred_df[pred_df["scope"].eq(scope)].copy()
    if scope_pred.empty:
        return
    scope_label = str(scope_pred["scope_label"].iloc[0])
    fig, axes = plt.subplots(3, 2, figsize=(12.2, 12.0), sharex=True)
    axes_flat = axes.ravel()
    palette = comparison_palette()
    for idx, (effort_col, effort_label) in enumerate(EFFORT_CONTROLS):
        ax = axes_flat[idx]
        sub = scope_pred[scope_pred["effort_control"].eq(effort_col)].copy()
        stat = stats_df[(stats_df["scope"].eq(scope)) & (stats_df["effort_control"].eq(effort_col))]
        if sub.empty:
            ax.axis("off")
            continue
        for group in COMPARISON_ORDER:
            group_df = sub[sub["comparison_group"].astype(str).eq(group)].sort_values("age_months")
            if group_df.empty:
                continue
            ax.plot(
                group_df["age_months"],
                group_df["predicted_sum_bits"],
                linewidth=1.9,
                label=group,
                color=palette.get(group),
            )
        if not stat.empty:
            row = stat.iloc[0]
            if detail == "short":
                label = f"R2={format_r2(row.get('r2'))}\np(age)={format_p(row.get('p_age'))}"
            else:
                label = (
                    f"R2={format_r2(row.get('r2'))}\n"
                    f"p(age)={format_p(row.get('p_age'))}\n"
                    f"p(effort)={format_p(row.get('p_effort'))}\n"
                    f"min p(group)={format_p(row.get('min_p_group'))}"
                )
            add_stats_box(ax, label)
            fixed_effort = sub["fixed_effort_value"].iloc[0]
            ax.set_title(f"{effort_label} fixed at {fixed_effort:.1f}")
        ax.grid(alpha=0.22)
        ax.set_ylabel("Predicted total bits")
    axes_flat[-1].axis("off")
    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.94, 0.08), title="Target")
    for ax in axes_flat[:-1]:
        ax.set_xlabel("Age in months")
    fig.suptitle(f"Utterance-Level Sensitivity: {scope_label}", y=0.995)
    fig.tight_layout(rect=(0, 0.04, 1, 0.98))
    filename = f"effort_sensitivity_{scope}_{detail}"
    fig.savefig(fig_dir / f"{filename}.png", dpi=220)
    fig.savefig(fig_dir / f"{filename}.pdf")
    plt.close(fig)


def plot_effort_sensitivity_results(stats_df: pd.DataFrame, pred_df: pd.DataFrame, fig_dir: Path) -> None:
    """Write short and full effort-control sensitivity plot grids."""

    for scope in sorted(pred_df["scope"].dropna().unique()):
        for detail in ["short", "full"]:
            plot_effort_sensitivity_grid(stats_df, pred_df, fig_dir, scope=scope, detail=detail)


def age_bin_midpoint(label: str) -> float:
    """Return midpoint for labels like 024-029."""

    try:
        start, end = str(label).split("-")
        return (int(start) + int(end)) / 2
    except Exception:
        return math.nan


def write_markdown_table(frame: pd.DataFrame, *, max_rows: int = 20, float_digits: int = 3) -> str:
    """Return a small dataframe as GitHub-flavored Markdown."""

    if frame.empty:
        return "_No rows._"
    display = frame.head(max_rows).copy()
    for col in display.columns:
        if pd.api.types.is_float_dtype(display[col]):
            display[col] = display[col].map(lambda x: "" if pd.isna(x) else f"{x:.{float_digits}f}")
    cols = list(display.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in display.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if pd.isna(value) or str(value) == "nan":
                values.append("")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(
    *,
    output_md: Path,
    output_html: Path,
    output_dir: Path,
    fig_dir: Path,
    extraction: pd.DataFrame,
    source_audit: pd.DataFrame,
    source_comparison: pd.DataFrame,
    entropy_audit: pd.DataFrame,
    entropy_status_counts: pd.DataFrame,
    corr: pd.DataFrame,
    vif: pd.DataFrame,
    model_summary: pd.DataFrame,
    coef_summary: pd.DataFrame,
    model_stats_full: pd.DataFrame,
    model_stats_short: pd.DataFrame,
    effort_stats_full: pd.DataFrame,
    effort_stats_short: pd.DataFrame,
    child_control_stats: pd.DataFrame,
) -> None:
    """Write the separate model-proposal review report."""

    high_vif = vif[vif["vif"] > 10]["predictor"].tolist()
    high_vif_text = ", ".join(high_vif) if high_vif else "none above 10"
    source_mismatches = source_comparison[source_comparison["status"].eq("mismatch")].copy()
    source_status = "matched" if source_mismatches.empty else "mismatch"
    child_real_entropy = entropy_status_counts[
        entropy_status_counts["role"].eq("child")
        & entropy_status_counts["target_variant"].eq("real")
        & entropy_status_counts["context_k"].isin(["k1", "k2", "k3"])
    ].copy()
    md = f"""# Utterance-Level Information: Model Proposal Review

Working modeling packet, generated 2026-06-04.

This is a separate review document. It is not the supervisor-facing report. The
goal is to compare candidate model forms before deciding what belongs in the
main document.

## Modeling Principles Used

The model set follows the Advanced Data Analytics course guidance:

- start from the response variable and data-generating structure;
- audit predictor correlations and multicollinearity before interpreting
  regression coefficients;
- begin with a simple baseline model;
- respect repeated observations within children using clustered standard
  errors, mixed models, or GEE;
- treat flexible or more complex models as additions only when they answer a
  real scientific question.

## Current Data Extract

{write_markdown_table(extraction, max_rows=10)}

The working rows come from the scored PBM utterance-information long table.
Preliminary fits use
deterministic stratified samples so that model forms can be checked quickly
without treating a 6GB CSV as the day-to-day modeling object. Final analysis
tables should be materialized as compact Parquet/DuckDB tables or smaller CSVs.

## Unit Labels

`dataset` means the source corpus or collection: Brown, Manchester, or
Providence. It is not a child identifier. `child_id` is the individual child.
The primary proposal below does **not** center dataset/corpus fixed effects,
because the first scientific question is developmental and child-level rather
than corpus-comparison. Dataset/corpus can still be added later as a robustness
check if the timeline differences across Brown, Manchester, and Providence look
like they are driving an apparent developmental trend.

## Source-File Sanity Check

The scored long table is checked against the symlinked scored CSV tree before
the plots and models are interpreted. Source comparison status:
**{source_status}**.

{write_markdown_table(source_audit, max_rows=10)}

The source tree contains a small set of raw placeholder rows that have no
generated target and no finite surprisal. These are documented above as
`source_unscored_or_blank_rows`; they are not analysis rows and are not counted
as mismatches.

Context entropy source files:

{write_markdown_table(entropy_audit, max_rows=5)}

Context entropy join status for real child rows:

{write_markdown_table(child_real_entropy, max_rows=20)}

Source/long-table mismatches, if any:

{write_markdown_table(source_mismatches, max_rows=20)}

## Predictor Correlation and Multicollinearity

![Predictor correlation heatmap](../figs/utterance_information_model_proposals/predictor_correlation_heatmap.png)

Main VIF warning: **{high_vif_text}**.

{write_markdown_table(vif, max_rows=12)}

The effort predictors are intentionally redundant: words, morphemes,
syllables, phonemes, and tokenizer tokens all measure related aspects of
utterance size. The safest strategy is not to put all effort measures into a
single inferential model. Instead, use one primary effort scale, then run
parallel sensitivity models with alternative denominators.

The sensitivity analyses below therefore ask the same utterance-level question
several times, swapping the effort control one at a time: words, surface
morphemes, two syllable estimates, and phonemes.

Frequency predictors are not yet present in the current utterance-information table. The
recommended next addition is a target-level or utterance-level frequency
summary from the same additive age-bin vocabulary used by the baselines, such
as mean log word frequency or mean negative log frequency.

## Descriptive Plots

These plots are descriptive summaries, not final inferential controls. In
particular, the mean total-bits plot does **not** control for utterance size:
it shows how much information is in the whole utterance as utterances actually
occur. Because children produce longer utterances as they age, this plot can
mix developmental change in information with developmental change in
utterance length. The controlled/model-based plots below fix or adjust for
length using `nb_words` or `log_nb_words`.

![Real child bits per word by age and context](../figs/utterance_information_model_proposals/real_child_bits_per_word_by_age_context.png)

![Real child total bits by age and context](../figs/utterance_information_model_proposals/real_child_sum_bits_by_age_context.png)

![Real versus generated baselines](../figs/utterance_information_model_proposals/baseline_bits_per_word_by_age.png)

![Context entropy and target information](../figs/utterance_information_model_proposals/context_entropy_vs_bits_per_word.png)

## Five Candidate Models

### Model 1: Simple OLS Baseline

Formula:

```text
sum_bits ~ age_scaled + nb_words
```

Use: first sanity check for total information while controlling the most direct
length measure. Standard errors are clustered by child. This model does not
include context; it uses the no-context `k0` scoring condition as a baseline.

![M1 adjusted total bits](../figs/utterance_information_model_proposals/model1_adjusted_total_bits_by_age.png)

### Model 2: Effort-Controlled OLS

Formula:

```text
bits_per_word ~ age_scaled + age_scaled_sq + log_nb_words
```

Use: interpretable developmental curve for information per word with a minimal
residual word-length control. This fixes the scoring context to `k3`, so
context window is held constant by design.

![M2 adjusted bits per word](../figs/utterance_information_model_proposals/model2_adjusted_bits_per_word.png)

### Model 3: Linear Mixed Model With Child Random Intercepts

Formula:

```text
bits_per_word ~ age_scaled + log_nb_words
random: 1 | child_id
```

Use: same fixed effects as Model 2, but child baselines are allowed to differ.
This addresses repeated utterances within the same child.

![M3 child random intercepts](../figs/utterance_information_model_proposals/model3_child_random_intercepts.png)

If statsmodels reports a singular random-effect covariance for this model, that
does not mean child differences should be ignored. It means this random-effect
parameterization is unstable for the current pilot specification. The
child-control ladder below therefore includes child fixed effects and GEE
grouping by child as stable alternatives.

### Model 4: Linear Mixed Model With Child-Specific Age Slopes

Formula:

```text
bits_per_word ~ age_scaled + log_nb_words
random: 1 + age_scaled | child_id
```

Use: tests whether developmental trajectories differ across children, not just
their overall levels. The current pilot fit did not converge, so this plot is a
diagnostic proposal rather than an interpretable result.

![M4 random slope pilot](../figs/utterance_information_model_proposals/model4_random_slope_pilot.png)

### Model 5: Correlated-Data GLM/GEE Baseline Comparison

Formula:

```text
sum_bits ~ age_scaled * C(target_variant) + nb_words
family: Gamma(log), child-level exchangeable correlation
```

Use: compares real child utterances against random, unigram, bigram, and
trigram baselines while respecting child-level clustering. This is a
population-averaged GLM/GEE version of the GLMM question; if supervisors want
subject-specific random effects for this positive outcome, the final version
can be fit as a Gamma GLMM in R/glmmTMB.

![M5 adjusted baseline predictions](../figs/utterance_information_model_proposals/model5_adjusted_baseline_predictions.png)

## Context Extension

The context-only entropy feature is available for most child-context rows and
is measured in bits. The remaining missing context rows are isolated for patch
scoring; until that patch is merged, context-entropy models should use matched
or text-fallback matched rows only. A
natural extension is:

```text
bits_per_word ~ age_scaled + log_nb_words + context_entropy_bits + C(context_k)
cluster: child_id
```

This asks whether more uncertain contexts elicit child utterances with
different information density.

![Candidate fitted developmental curves](../figs/utterance_information_model_proposals/candidate_model_fitted_age_curves.png)

## Preliminary Fit Status

{write_markdown_table(model_summary, max_rows=20)}

## Selected Coefficients

{write_markdown_table(coef_summary, max_rows=60)}

## Compact Model Statistics

Short version:

{write_markdown_table(model_stats_short, max_rows=20)}

Full version:

{write_markdown_table(model_stats_full, max_rows=20)}

## Child-Control Ladder

Because individual children can differ systematically, the primary
developmental question should be checked in both simple and child-controlled
forms. This ladder uses real child utterances only, keeps age in every model,
and controls for one effort measure at a time:

- `OLS: age + effort`: simple length-controlled model, child-clustered standard
  errors but no child term;
- `OLS: age + effort + child fixed effects`: directly controls for each
  child's baseline level;
- `GEE: age + effort grouped by child`: population-averaged model with
  child-level correlation.

![Child control ladder](../figs/utterance_information_model_proposals/child_control_ladder_r2_age_pvalues.png)

{write_markdown_table(child_control_stats, max_rows=20)}

## Effort-Control Sensitivity At The Utterance Level

These plots use total utterance bits as the outcome and control for only one
effort measure at a time. This avoids putting highly collinear measures in the
same model while still showing whether the age trajectory depends on the chosen
effort granularity.

Child real utterances and generated baselines only:

![Effort sensitivity child short](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_and_baselines_short.png)

![Effort sensitivity child full](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_and_baselines_full.png)

Child real utterances, generated baselines, and caretakers:

![Effort sensitivity with caretakers short](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_baselines_and_caretaker_short.png)

![Effort sensitivity with caretakers full](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_baselines_and_caretaker_full.png)

Short effort-control statistics:

{write_markdown_table(effort_stats_short, max_rows=20)}

Full effort-control statistics:

{write_markdown_table(effort_stats_full, max_rows=30)}

## What Should Go Into The Real Report?

Recommended first pass:

1. Use Model 2 as the simple interpretive baseline.
2. Use Model 3 as the first main child-aware model.
3. Treat Model 4 as a developmental-trajectory candidate, but refit it more
   carefully before using it inferentially because the statsmodels pilot did
   not converge.
4. Use Model 5 for real-versus-baseline comparisons.
5. Keep context entropy as a follow-up once the small entropy patch is scored.
6. Do not include all effort predictors in the same model because the VIF
   diagnostics show that they are measuring strongly overlapping quantities.

Outputs written under:

```text
{output_dir}
{fig_dir}
```
"""
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(md, encoding="utf-8")
    render_markdown_file(output_md, output_html)


def write_notebook(path: Path) -> None:
    """Write a tiny reproducible notebook that points to the script."""

    path.parent.mkdir(parents=True, exist_ok=True)
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Utterance Information Model Proposals\n",
                    "\n",
                    "This notebook is a lightweight entry point. The heavy lifting is in `src/build_utterance_information_model_proposals.py` so it can be rerun reproducibly.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "!../.venv/bin/python ../src/build_utterance_information_model_proposals.py\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "Review the HTML report at `../docs/utterance_information_model_proposals.html`.\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb, indent=2), encoding="utf-8")


def build_packet(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    output_md: Path,
    output_html: Path,
    notebook: Path,
    scored_tree: Path,
    context_entropy_dir: Path,
    chunksize: int,
) -> None:
    """Build all model-proposal outputs."""

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    data = read_analysis_data(input_csv, output_dir, chunksize=chunksize)
    source_audit, source_comparison, entropy_audit = source_tree_audit(
        scored_tree=scored_tree,
        context_entropy_dir=context_entropy_dir,
        long_counts=data.long_counts,
        output_dir=output_dir,
    )
    tables = save_aggregate_tables(data, output_dir)
    corr, vif = correlation_and_vif(data, output_dir, fig_dir)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model_summary, coef_summary, model_objects = fit_models(data, output_dir)
        model_stats_full, model_stats_short = build_model_interpretation_stats(
            model_summary,
            model_objects,
            output_dir,
        )
        effort_stats_full, effort_coef_summary, effort_prediction_df = fit_effort_sensitivity_models(
            data,
            output_dir,
        )
        child_control_stats, child_control_coefs = fit_child_control_ladder(data, output_dir)

    plot_age_context_trends(tables, fig_dir)
    plot_baseline_comparison(tables, fig_dir)
    plot_context_entropy(data, fig_dir)
    plot_model_predictions(data, model_objects, fig_dir)
    plot_five_model_results(data, model_objects, model_stats_full, output_dir, fig_dir)
    plot_effort_sensitivity_results(effort_stats_full, effort_prediction_df, fig_dir)
    plot_child_control_ladder(child_control_stats, fig_dir)

    extraction = pd.read_csv(output_dir / "data_extraction_summary.csv")
    effort_stats_short = pd.read_csv(output_dir / "effort_sensitivity_model_stats_short.csv")
    write_report(
        output_md=output_md,
        output_html=output_html,
        output_dir=output_dir,
        fig_dir=fig_dir,
        extraction=extraction,
        source_audit=source_audit,
        source_comparison=source_comparison,
        entropy_audit=entropy_audit,
        entropy_status_counts=data.entropy_status_counts,
        corr=corr,
        vif=vif,
        model_summary=model_summary,
        coef_summary=coef_summary,
        model_stats_full=model_stats_full,
        model_stats_short=model_stats_short,
        effort_stats_full=effort_stats_full,
        effort_stats_short=effort_stats_short,
        child_control_stats=child_control_stats,
    )
    write_notebook(notebook)

    print(f"[OK] Wrote model proposal report: {output_html}")
    print(f"[OK] Wrote notebook: {notebook}")
    print(f"[OK] Wrote results: {output_dir}")
    print(f"[OK] Wrote figures: {fig_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--output-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument("--scored-tree", type=Path, default=DEFAULT_SCORED_TREE)
    parser.add_argument("--context-entropy-dir", type=Path, default=DEFAULT_CONTEXT_ENTROPY_DIR)
    parser.add_argument("--chunksize", type=int, default=350_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_packet(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        output_md=args.output_md,
        output_html=args.output_html,
        notebook=args.notebook,
        scored_tree=args.scored_tree,
        context_entropy_dir=args.context_entropy_dir,
        chunksize=args.chunksize,
    )


if __name__ == "__main__":
    main()
