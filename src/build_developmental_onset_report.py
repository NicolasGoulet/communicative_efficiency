#!/usr/bin/env python3
"""Build a working report on when communicative-efficiency signals emerge."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


DEFAULT_YANG_ROWS = Path("results/yang_followup/yang_followup_analysis_rows.csv.gz")
DEFAULT_CONTEXT_COEFS = Path("results/yang_followup/age_bin_modulation_coefficients.csv")
DEFAULT_PAIRED_GAPS = Path("results/bayes_information_report/paired_baseline_minus_real_gaps.csv.gz")
DEFAULT_COMPLEXITY_AGE = Path(
    "results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/"
    "pbm_real_complexity_age_bin_summary.csv.gz"
)
DEFAULT_OUTPUT_DIR = Path("results/developmental_onset_report")
DEFAULT_FIG_DIR = Path("figs/developmental_onset_report")
DEFAULT_DOC_MD = Path("docs/developmental_onset_working_report.md")
DEFAULT_DOC_HTML = Path("docs/developmental_onset_working_report.html")

AGE_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
SOURCE_ORDER = ["random", "unigram", "bigram", "trigram"]
SOURCE_LABELS = {
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
}
SOURCE_COLORS = {
    "random": "#c44536",
    "unigram": "#7b4f9f",
    "bigram": "#3b7dd8",
    "trigram": "#1f9a8a",
}


def age_mid(label: object) -> float:
    if not isinstance(label, str) or "-" not in label:
        return float("nan")
    start, end = label.split("-", 1)
    return (float(start) + float(end)) / 2.0


def fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    if not math.isfinite(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def md_table(frame: pd.DataFrame, *, digits: int = 3) -> str:
    if frame.empty:
        return "_No rows._"
    out = frame.copy()
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


def sem(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) <= 1:
        return float("nan")
    return float(clean.std(ddof=1) / math.sqrt(len(clean)))


def ci_summary(frame: pd.DataFrame, group_cols: list[str], value_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, group in frame.groupby(group_cols, observed=True, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        row: dict[str, object] = dict(zip(group_cols, key))
        row["n_cells"] = len(group)
        for col in value_cols:
            values = pd.to_numeric(group[col], errors="coerce")
            mean = float(values.mean())
            se = sem(values)
            row[f"{col}_mean"] = mean
            row[f"{col}_sem"] = se
            row[f"{col}_ci_low"] = mean - 1.96 * se if math.isfinite(se) else float("nan")
            row[f"{col}_ci_high"] = mean + 1.96 * se if math.isfinite(se) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def require(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def read_real_child_age_rows(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    usecols = [
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "role",
        "target_variant",
        "context_k",
        "sum_bits",
        "nb_words",
        "context_entropy_bits",
        "parent_context_nb_words",
        "prior_caretaker_sum_bits",
    ]
    frame = pd.read_csv(path, usecols=usecols, low_memory=False)
    frame = frame[
        (frame["role"] == "child")
        & (frame["target_variant"] == "real")
        & (frame["context_k"] == "k3")
        & (pd.to_numeric(frame["nb_words"], errors="coerce") > 0)
    ].copy()
    for col in [
        "age_months",
        "sum_bits",
        "nb_words",
        "context_entropy_bits",
        "parent_context_nb_words",
        "prior_caretaker_sum_bits",
    ]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["bits_per_word"] = frame["sum_bits"] / frame["nb_words"].replace(0, np.nan)
    frame["age_bin"] = pd.Categorical(frame["age_bin"], categories=AGE_ORDER, ordered=True)

    group_cols = ["dataset", "child_id", "age_bin"]
    child_age = (
        frame.groupby(group_cols, observed=True)
        .agg(
            utterance_count=("sum_bits", "size"),
            session_count=("session_id", "nunique"),
            age_months_mean=("age_months", "mean"),
            mean_sum_bits=("sum_bits", "mean"),
            mean_words=("nb_words", "mean"),
            mean_bits_per_word=("bits_per_word", "mean"),
            mean_context_entropy_bits=("context_entropy_bits", "mean"),
            mean_parent_context_words=("parent_context_nb_words", "mean"),
            mean_prior_caretaker_sum_bits=("prior_caretaker_sum_bits", "mean"),
        )
        .reset_index()
    )
    child_age["age_mid"] = child_age["age_bin"].astype(str).map(age_mid)
    return frame, child_age


def extract_age_effects(model, age_bins: list[str], outcome: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for age in age_bins:
        term = f"C(age_bin)[T.{age}]"
        if term in model.params.index:
            estimate = float(model.params[term])
            ci_low, ci_high = [float(x) for x in model.conf_int().loc[term]]
            p_value = float(model.pvalues[term])
        else:
            estimate = 0.0
            ci_low = float("nan")
            ci_high = float("nan")
            p_value = float("nan")
        rows.append(
            {
                "outcome": outcome,
                "age_bin": age,
                "age_mid": age_mid(age),
                "estimate_vs_006_023": estimate,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def fit_controlled_age_effects(child_age: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = child_age.dropna(subset=["mean_sum_bits", "mean_bits_per_word", "mean_words", "utterance_count"]).copy()
    data["age_bin"] = pd.Categorical(data["age_bin"], categories=AGE_ORDER, ordered=True)
    data["weight"] = data["utterance_count"].clip(lower=1)
    outputs: list[pd.DataFrame] = []
    model_rows: list[dict[str, object]] = []
    for outcome, formula in [
        ("mean_sum_bits", "mean_sum_bits ~ mean_words + C(child_id) + C(age_bin)"),
        ("mean_bits_per_word", "mean_bits_per_word ~ mean_words + C(child_id) + C(age_bin)"),
    ]:
        model = smf.wls(formula, data=data, weights=data["weight"]).fit(cov_type="HC3")
        effects = extract_age_effects(model, AGE_ORDER, outcome)
        effects["n_child_age_cells"] = len(data)
        outputs.append(effects)
        model_rows.append(
            {
                "outcome": outcome,
                "formula": formula,
                "n_child_age_cells": int(model.nobs),
                "r2": float(model.rsquared),
                "aic": float(model.aic),
            }
        )
    return pd.concat(outputs, ignore_index=True), pd.DataFrame(model_rows)


def word_count_bin(values: pd.Series, cap: int = 12) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").fillna(0).astype(int)
    labels = numeric.clip(upper=cap).astype(str)
    labels[numeric >= cap] = f"{cap}_plus"
    return labels


def fit_utterance_age_models(real_rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = real_rows.dropna(subset=["sum_bits", "nb_words", "age_months", "age_bin", "child_id"]).copy()
    data["age_bin"] = pd.Categorical(data["age_bin"], categories=AGE_ORDER, ordered=True)
    data["word_count_bin"] = word_count_bin(data["nb_words"])
    data["age_c"] = data["age_months"] - data["age_months"].mean()

    continuous_formula = "sum_bits ~ age_c + C(word_count_bin) + C(child_id)"
    continuous = smf.ols(continuous_formula, data=data).fit(
        cov_type="cluster",
        cov_kwds={"groups": data["child_id"]},
    )

    age_bin_formula = "sum_bits ~ C(age_bin) + C(word_count_bin) + C(child_id)"
    age_bin_model = smf.ols(age_bin_formula, data=data).fit(
        cov_type="cluster",
        cov_kwds={"groups": data["child_id"]},
    )
    effects = extract_age_effects(age_bin_model, AGE_ORDER, "sum_bits_exact_word_count")
    effects["n_obs"] = int(age_bin_model.nobs)
    effects["n_children"] = int(data["child_id"].nunique())

    ci_low, ci_high = [float(x) for x in continuous.conf_int().loc["age_c"]]
    model_rows = [
        {
            "model": "continuous_age_exact_word_count",
            "formula": continuous_formula,
            "n_obs": int(continuous.nobs),
            "n_children": int(data["child_id"].nunique()),
            "r2": float(continuous.rsquared),
            "aic": float(continuous.aic),
            "age_coef_bits_per_month": float(continuous.params["age_c"]),
            "age_ci_low": ci_low,
            "age_ci_high": ci_high,
            "age_p": float(continuous.pvalues["age_c"]),
        },
        {
            "model": "age_bin_exact_word_count",
            "formula": age_bin_formula,
            "n_obs": int(age_bin_model.nobs),
            "n_children": int(data["child_id"].nunique()),
            "r2": float(age_bin_model.rsquared),
            "aic": float(age_bin_model.aic),
            "age_coef_bits_per_month": float("nan"),
            "age_ci_low": float("nan"),
            "age_ci_high": float("nan"),
            "age_p": float("nan"),
        },
    ]
    return effects, pd.DataFrame(model_rows)


def fit_utterance_changepoints(real_rows: pd.DataFrame) -> pd.DataFrame:
    data = real_rows.dropna(subset=["sum_bits", "nb_words", "age_months", "child_id"]).copy()
    data["word_count_bin"] = word_count_bin(data["nb_words"])
    data["age_c"] = data["age_months"] - data["age_months"].mean()
    candidates = [23.0, 26.5, 29.0, 32.5, 35.0, 38.5, 44.5, 50.5]
    rows: list[dict[str, object]] = []

    base_formula = "sum_bits ~ C(word_count_bin) + age_c + C(child_id)"
    base_model = smf.ols(base_formula, data=data).fit(
        cov_type="cluster",
        cov_kwds={"groups": data["child_id"]},
    )
    rows.append(
        {
            "outcome": "sum_bits_exact_word_count",
            "breakpoint_month": "linear_no_break",
            "aic": float(base_model.aic),
            "delta_aic_vs_best": float("nan"),
            "r2": float(base_model.rsquared),
            "age_slope": float(base_model.params.get("age_c", np.nan)),
            "post_break_slope_change": float("nan"),
            "post_break_p": float("nan"),
        }
    )
    for breakpoint in candidates:
        model_data = data.copy()
        model_data["post_break"] = np.maximum(0.0, model_data["age_months"] - breakpoint)
        formula = "sum_bits ~ C(word_count_bin) + age_c + post_break + C(child_id)"
        model = smf.ols(formula, data=model_data).fit(
            cov_type="cluster",
            cov_kwds={"groups": model_data["child_id"]},
        )
        rows.append(
            {
                "outcome": "sum_bits_exact_word_count",
                "breakpoint_month": breakpoint,
                "aic": float(model.aic),
                "delta_aic_vs_best": float("nan"),
                "r2": float(model.rsquared),
                "age_slope": float(model.params.get("age_c", np.nan)),
                "post_break_slope_change": float(model.params.get("post_break", np.nan)),
                "post_break_p": float(model.pvalues.get("post_break", np.nan)),
            }
        )
    out = pd.DataFrame(rows)
    out["delta_aic_vs_best"] = out["aic"] - out["aic"].min()
    return out


def fit_child_age_changepoints(child_age: pd.DataFrame) -> pd.DataFrame:
    data = child_age.dropna(subset=["mean_sum_bits", "mean_bits_per_word", "mean_words", "age_mid"]).copy()
    data["age_bin"] = pd.Categorical(data["age_bin"], categories=AGE_ORDER, ordered=True)
    data["weight"] = data["utterance_count"].clip(lower=1)
    candidates = [age_mid(x) for x in AGE_ORDER[1:-1]]
    rows: list[dict[str, object]] = []
    for outcome in ["mean_sum_bits", "mean_bits_per_word"]:
        base_formula = f"{outcome} ~ mean_words + age_mid + C(child_id)"
        base_model = smf.wls(base_formula, data=data, weights=data["weight"]).fit(cov_type="HC3")
        base_aic = float(base_model.aic)
        rows.append(
            {
                "outcome": outcome,
                "breakpoint_month": "linear_no_break",
                "aic": base_aic,
                "delta_aic_vs_best": float("nan"),
                "r2": float(base_model.rsquared),
                "age_slope": float(base_model.params.get("age_mid", np.nan)),
                "post_break_slope_change": float("nan"),
                "post_break_p": float("nan"),
            }
        )
        for breakpoint in candidates:
            data["post_break"] = np.maximum(0.0, data["age_mid"] - breakpoint)
            formula = f"{outcome} ~ mean_words + age_mid + post_break + C(child_id)"
            model = smf.wls(formula, data=data, weights=data["weight"]).fit(cov_type="HC3")
            rows.append(
                {
                    "outcome": outcome,
                    "breakpoint_month": breakpoint,
                    "aic": float(model.aic),
                    "delta_aic_vs_best": float("nan"),
                    "r2": float(model.rsquared),
                    "age_slope": float(model.params.get("age_mid", np.nan)),
                    "post_break_slope_change": float(model.params.get("post_break", np.nan)),
                    "post_break_p": float(model.pvalues.get("post_break", np.nan)),
                }
            )
    out = pd.DataFrame(rows)
    for outcome, group in out.groupby("outcome"):
        best = group["aic"].min()
        out.loc[out["outcome"] == outcome, "delta_aic_vs_best"] = out.loc[out["outcome"] == outcome, "aic"] - best
    return out


def read_paired_gaps(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usecols = [
        "row_uid",
        "source_model",
        "dataset",
        "child_id",
        "age_months",
        "age_bin",
        "delta_bayes_bits_per_token_vs_real",
        "delta_mistral_bits_per_token_vs_real",
    ]
    gaps = pd.read_csv(path, usecols=usecols, low_memory=False)
    gaps = gaps[gaps["source_model"].isin(SOURCE_ORDER)].copy()
    gaps["age_bin"] = pd.Categorical(gaps["age_bin"], categories=AGE_ORDER, ordered=True)
    for col in ["age_months", "delta_bayes_bits_per_token_vs_real", "delta_mistral_bits_per_token_vs_real"]:
        gaps[col] = pd.to_numeric(gaps[col], errors="coerce")

    child_source_age = (
        gaps.groupby(["dataset", "child_id", "age_bin", "source_model"], observed=True)
        .agg(
            row_count=("row_uid", "size"),
            age_months_mean=("age_months", "mean"),
            delta_mistral_bits_per_token_vs_real=("delta_mistral_bits_per_token_vs_real", "mean"),
            delta_bayes_bits_per_token_vs_real=("delta_bayes_bits_per_token_vs_real", "mean"),
        )
        .reset_index()
    )
    child_source_age["age_mid"] = child_source_age["age_bin"].astype(str).map(age_mid)
    summary = ci_summary(
        child_source_age,
        ["age_bin", "source_model"],
        ["delta_mistral_bits_per_token_vs_real", "delta_bayes_bits_per_token_vs_real"],
    )
    summary["age_mid"] = summary["age_bin"].astype(str).map(age_mid)
    summary["source_label"] = summary["source_model"].map(SOURCE_LABELS)

    onset_rows: list[dict[str, object]] = []
    metrics = [
        ("delta_mistral_bits_per_token_vs_real", "Direct Mistral paired gap"),
        ("delta_bayes_bits_per_token_vs_real", "Bayes decomposition paired gap"),
    ]
    for source in SOURCE_ORDER:
        subset = summary[summary["source_model"] == source].sort_values("age_mid")
        for metric, label in metrics:
            positive = subset[subset[f"{metric}_ci_low"] > 0]
            first = positive.iloc[0] if not positive.empty else None
            onset_rows.append(
                {
                    "signal": label,
                    "source_model": source,
                    "earliest_age_bin_ci_positive": "" if first is None else first["age_bin"],
                    "estimate_at_onset": float("nan") if first is None else first[f"{metric}_mean"],
                    "ci_low_at_onset": float("nan") if first is None else first[f"{metric}_ci_low"],
                    "ci_high_at_onset": float("nan") if first is None else first[f"{metric}_ci_high"],
                }
            )
    return child_source_age, summary, pd.DataFrame(onset_rows)


def read_context_modulation(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefs = pd.read_csv(path)
    coefs["age_bin"] = pd.Categorical(coefs["age_bin"], categories=AGE_ORDER, ordered=True)
    onset_rows: list[dict[str, object]] = []
    for (outcome, predictor), group in coefs.groupby(["outcome", "predictor"], observed=True):
        group = group.sort_values("age_mid")
        negative = group[group["ci_high"] < 0]
        positive = group[group["ci_low"] > 0]
        first_negative = negative.iloc[0] if not negative.empty else None
        first_positive = positive.iloc[0] if not positive.empty else None
        onset_rows.append(
            {
                "outcome": outcome,
                "predictor": predictor,
                "earliest_age_bin_ci_negative": "" if first_negative is None else first_negative["age_bin"],
                "negative_estimate_at_onset": float("nan") if first_negative is None else first_negative["estimate"],
                "earliest_age_bin_ci_positive": "" if first_positive is None else first_positive["age_bin"],
                "positive_estimate_at_onset": float("nan") if first_positive is None else first_positive["estimate"],
            }
        )
    return coefs, pd.DataFrame(onset_rows)


def read_complexity(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(path, low_memory=False)
    frame["age_bin"] = pd.Categorical(frame["age_bin"], categories=AGE_ORDER, ordered=True)
    frame["age_mid"] = frame["age_bin"].astype(str).map(age_mid)
    for col in [
        "utterance_count",
        "age_bin_vocab_size",
        "age_bin_ttr",
        "mean_words_per_utterance",
        "mean_syllables_per_utterance",
    ]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    summary = ci_summary(
        frame,
        ["age_bin"],
        ["mean_words_per_utterance", "mean_syllables_per_utterance", "age_bin_vocab_size", "age_bin_ttr"],
    )
    summary["age_mid"] = summary["age_bin"].astype(str).map(age_mid)

    effects: list[pd.DataFrame] = []
    data = frame.dropna(subset=["utterance_count"]).copy()
    data["weight"] = data["utterance_count"].clip(lower=1)
    data["log_utterance_count"] = np.log1p(data["utterance_count"])
    model_specs = [
        ("mean_words_per_utterance", "mean_words_per_utterance ~ C(child_id) + C(age_bin)"),
        ("mean_syllables_per_utterance", "mean_syllables_per_utterance ~ C(child_id) + C(age_bin)"),
        ("age_bin_vocab_size", "age_bin_vocab_size ~ log_utterance_count + C(child_id) + C(age_bin)"),
    ]
    for outcome, formula in model_specs:
        model_data = data.dropna(subset=[outcome]).copy()
        model = smf.wls(formula, data=model_data, weights=model_data["weight"]).fit(cov_type="HC3")
        effect = extract_age_effects(model, AGE_ORDER, outcome)
        effect["formula"] = formula
        effects.append(effect)
    return frame, summary, pd.concat(effects, ignore_index=True)


def first_age(table: pd.DataFrame, condition_col: str, *, direction: str) -> str:
    table = table.sort_values("age_mid")
    if direction == "negative":
        subset = table[table[condition_col] < 0]
    elif direction == "positive":
        subset = table[table[condition_col] > 0]
    else:
        raise ValueError(direction)
    return "" if subset.empty else str(subset.iloc[0]["age_bin"])


def build_onset_map(
    utterance_age_effects: pd.DataFrame,
    paired_summary: pd.DataFrame,
    context_coefs: pd.DataFrame,
    complexity_effects: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []

    def add_signal(label: str, source: pd.DataFrame, condition: pd.Series) -> None:
        signal = source.copy()
        signal["supported"] = condition.astype(bool).values
        for _, row in signal.iterrows():
            rows.append(
                {
                    "signal": label,
                    "age_bin": row["age_bin"],
                    "age_mid": age_mid(str(row["age_bin"])),
                    "supported": int(row["supported"]),
                }
            )

    add_signal(
        "Exact word-count age-bin decrease",
        utterance_age_effects[utterance_age_effects["outcome"] == "sum_bits_exact_word_count"],
        utterance_age_effects[utterance_age_effects["outcome"] == "sum_bits_exact_word_count"]["ci_high"] < 0,
    )
    trigram = paired_summary[paired_summary["source_model"] == "trigram"]
    add_signal(
        "Trigram paired Mistral gap positive",
        trigram,
        trigram["delta_mistral_bits_per_token_vs_real_ci_low"] > 0,
    )
    add_signal(
        "Trigram paired Bayes gap positive",
        trigram,
        trigram["delta_bayes_bits_per_token_vs_real_ci_low"] > 0,
    )
    ce = context_coefs[(context_coefs["outcome"] == "child sum_bits") & (context_coefs["predictor"] == "context entropy")]
    add_signal("Context entropy modulation negative", ce, ce["ci_high"] < 0)
    pcw = context_coefs[(context_coefs["outcome"] == "child sum_bits") & (context_coefs["predictor"] == "parent context words")]
    add_signal("Parent-context-word modulation negative", pcw, pcw["ci_high"] < 0)
    mlu = complexity_effects[complexity_effects["outcome"] == "mean_words_per_utterance"]
    add_signal("MLU higher than 006-023", mlu, mlu["ci_low"] > 0)

    onset_map = pd.DataFrame(rows)
    pivot = onset_map.pivot_table(index="signal", columns="age_bin", values="supported", fill_value=0, observed=True)
    pivot = pivot.reindex(columns=AGE_ORDER)
    return onset_map, pivot


def plot_age_effects(age_effects: pd.DataFrame, path: Path) -> None:
    labels = {
        "mean_sum_bits": "Mean total bits, adjusted",
        "mean_bits_per_word": "Mean bits/word, adjusted",
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharex=True)
    for ax, outcome in zip(axes, labels):
        data = age_effects[age_effects["outcome"] == outcome].sort_values("age_mid")
        ax.axhline(0, color="#3a3a3a", lw=1)
        ax.errorbar(
            data["age_mid"],
            data["estimate_vs_006_023"],
            yerr=[
                data["estimate_vs_006_023"] - data["ci_low"],
                data["ci_high"] - data["estimate_vs_006_023"],
            ],
            marker="o",
            lw=2,
            capsize=4,
            color="#2f6f73",
        )
        ax.set_title(labels[outcome])
        ax.set_xlabel("Age midpoint (months)")
        ax.set_ylabel("Difference from 006-023")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_utterance_age_effects(utterance_age_effects: pd.DataFrame, child_age_effects: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8), sharex=True)

    data = utterance_age_effects.sort_values("age_mid")
    axes[0].axhline(0, color="#3a3a3a", lw=1)
    axes[0].errorbar(
        data["age_mid"],
        data["estimate_vs_006_023"],
        yerr=[
            data["estimate_vs_006_023"] - data["ci_low"],
            data["ci_high"] - data["estimate_vs_006_023"],
        ],
        marker="o",
        lw=2,
        capsize=4,
        color="#2f6f73",
    )
    axes[0].set_title("Utterance-level exact word-count model")
    axes[0].set_xlabel("Age midpoint (months)")
    axes[0].set_ylabel("Difference from 006-023 bits")

    sensitivity = child_age_effects[child_age_effects["outcome"] == "mean_sum_bits"].sort_values("age_mid")
    axes[1].axhline(0, color="#3a3a3a", lw=1)
    axes[1].errorbar(
        sensitivity["age_mid"],
        sensitivity["estimate_vs_006_023"],
        yerr=[
            sensitivity["estimate_vs_006_023"] - sensitivity["ci_low"],
            sensitivity["ci_high"] - sensitivity["estimate_vs_006_023"],
        ],
        marker="o",
        lw=2,
        capsize=4,
        color="#8a6f2f",
    )
    axes[1].set_title("Child-age aggregate sensitivity")
    axes[1].set_xlabel("Age midpoint (months)")
    axes[1].set_ylabel("Difference from 006-023 bits")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_changepoints(changepoints: pd.DataFrame, path: Path) -> None:
    data = changepoints[changepoints["breakpoint_month"] != "linear_no_break"].copy()
    data["breakpoint_month"] = pd.to_numeric(data["breakpoint_month"])
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for outcome, group in data.groupby("outcome"):
        if outcome == "mean_sum_bits":
            label = "Aggregate total bits"
        elif outcome == "mean_bits_per_word":
            label = "Aggregate bits/word"
        else:
            label = "Exact word-count total bits"
        ax.plot(group["breakpoint_month"], group["delta_aic_vs_best"], marker="o", lw=2, label=label)
    ax.axhline(2, color="#888888", lw=1, ls="--")
    ax.set_xlabel("Candidate breakpoint month")
    ax.set_ylabel("Delta AIC versus best")
    ax.set_title("Piecewise onset scan")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_paired_gaps(paired_summary: pd.DataFrame, path: Path) -> None:
    metrics = [
        ("delta_mistral_bits_per_token_vs_real", "Direct Mistral baseline-minus-real gap"),
        ("delta_bayes_bits_per_token_vs_real", "Bayes baseline-minus-real gap"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharex=True)
    for ax, (metric, title) in zip(axes, metrics):
        ax.axhline(0, color="#3a3a3a", lw=1)
        for source in SOURCE_ORDER:
            group = paired_summary[paired_summary["source_model"] == source].sort_values("age_mid")
            x = group["age_mid"].to_numpy(dtype=float)
            y = group[f"{metric}_mean"].to_numpy(dtype=float)
            lo = group[f"{metric}_ci_low"].to_numpy(dtype=float)
            hi = group[f"{metric}_ci_high"].to_numpy(dtype=float)
            ax.plot(x, y, marker="o", lw=2, label=SOURCE_LABELS[source], color=SOURCE_COLORS[source])
            ax.fill_between(x, lo, hi, alpha=0.14, color=SOURCE_COLORS[source])
        ax.set_title(title)
        ax.set_xlabel("Age midpoint (months)")
        ax.set_ylabel("Bits/token")
    axes[1].legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_context_modulation(context_coefs: pd.DataFrame, path: Path) -> None:
    data = context_coefs[context_coefs["outcome"] == "child sum_bits"].copy()
    fig, ax = plt.subplots(figsize=(8.8, 5))
    palette = {"context entropy": "#2f6f73", "parent context words": "#c76f2c"}
    for predictor, group in data.groupby("predictor"):
        group = group.sort_values("age_mid")
        x = group["age_mid"].to_numpy(dtype=float)
        y = group["estimate"].to_numpy(dtype=float)
        lo = group["ci_low"].to_numpy(dtype=float)
        hi = group["ci_high"].to_numpy(dtype=float)
        ax.plot(x, y, marker="o", lw=2, label=predictor, color=palette.get(predictor, None))
        ax.fill_between(x, lo, hi, alpha=0.16, color=palette.get(predictor, None))
    ax.axhline(0, color="#3a3a3a", lw=1)
    ax.set_xlabel("Age midpoint (months)")
    ax.set_ylabel("Coefficient predicting child total bits")
    ax.set_title("Context modulation by age bin")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_complexity(complexity_summary: pd.DataFrame, path: Path) -> None:
    panels = [
        ("mean_words_per_utterance", "Mean words per utterance"),
        ("mean_syllables_per_utterance", "Mean syllables per utterance"),
        ("age_bin_vocab_size", "Age-bin vocabulary size"),
        ("age_bin_ttr", "Age-bin type-token ratio"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for ax, (metric, title) in zip(axes.flat, panels):
        data = complexity_summary.sort_values("age_mid")
        x = data["age_mid"].to_numpy(dtype=float)
        y = data[f"{metric}_mean"].to_numpy(dtype=float)
        lo = data[f"{metric}_ci_low"].to_numpy(dtype=float)
        hi = data[f"{metric}_ci_high"].to_numpy(dtype=float)
        ax.plot(x, y, marker="o", lw=2, color="#2f6f73")
        ax.fill_between(x, lo, hi, alpha=0.16, color="#2f6f73")
        ax.set_title(title)
        ax.set_xlabel("Age midpoint (months)")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_onset_map(pivot: pd.DataFrame, path: Path) -> None:
    fig_height = max(4.2, 0.48 * len(pivot) + 1.2)
    fig, ax = plt.subplots(figsize=(12, fig_height))
    sns.heatmap(
        pivot,
        cmap=sns.color_palette(["#f4f2ef", "#2f6f73"], as_cmap=True),
        cbar=False,
        linewidths=0.8,
        linecolor="white",
        ax=ax,
    )
    ax.set_xlabel("Age bin")
    ax.set_ylabel("")
    ax.set_title("Where each onset criterion is supported")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_report(
    *,
    doc_md: Path,
    doc_html: Path,
    output_dir: Path,
    fig_dir: Path,
    child_age: pd.DataFrame,
    utterance_age_effects: pd.DataFrame,
    utterance_models: pd.DataFrame,
    utterance_changepoints: pd.DataFrame,
    child_age_effects: pd.DataFrame,
    child_age_models: pd.DataFrame,
    paired_summary: pd.DataFrame,
    paired_onsets: pd.DataFrame,
    context_onsets: pd.DataFrame,
    complexity_summary: pd.DataFrame,
    complexity_effects: pd.DataFrame,
    onset_map: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    controlled_onsets = []
    continuous = utterance_models[utterance_models["model"] == "continuous_age_exact_word_count"].iloc[0]
    controlled_onsets.append(
        {
            "signal": "Continuous fixed-word-count age slope",
            "operational_definition": "utterance-level OLS with child fixed effects, exact/top-coded word-count controls, child-clustered SEs",
            "earliest_age_bin": "whole range",
            "estimate": continuous["age_coef_bits_per_month"],
            "ci_low": continuous["age_ci_low"],
            "ci_high": continuous["age_ci_high"],
        }
    )
    sub = utterance_age_effects[utterance_age_effects["ci_high"] < 0].sort_values("age_mid")
    first = sub.iloc[0] if not sub.empty else None
    controlled_onsets.append(
        {
            "signal": "Earliest exact-word-count age-bin decrease",
            "operational_definition": "age-bin model relative to 006-023 with child fixed effects and exact/top-coded word-count controls",
            "earliest_age_bin": "" if first is None else first["age_bin"],
            "estimate": float("nan") if first is None else first["estimate_vs_006_023"],
            "ci_low": float("nan") if first is None else first["ci_low"],
            "ci_high": float("nan") if first is None else first["ci_high"],
        }
    )

    key_context = context_onsets[
        (context_onsets["outcome"] == "child sum_bits")
        & (context_onsets["predictor"].isin(["context entropy", "parent context words"]))
    ].copy()
    for _, row in key_context.iterrows():
        controlled_onsets.append(
            {
                "signal": f"{row['predictor']} modulation",
                "operational_definition": "age-specific regression coefficient predicting child total bits",
                "earliest_age_bin": row["earliest_age_bin_ci_negative"],
                "estimate": row["negative_estimate_at_onset"],
                "ci_low": float("nan"),
                "ci_high": float("nan"),
            }
        )

    trigram_onsets = paired_onsets[paired_onsets["source_model"] == "trigram"].copy()
    for _, row in trigram_onsets.iterrows():
        controlled_onsets.append(
            {
                "signal": f"{row['signal']} against trigram",
                "operational_definition": "same-context generated baseline minus real child bits/token; positive means real child has lower bits",
                "earliest_age_bin": row["earliest_age_bin_ci_positive"],
                "estimate": row["estimate_at_onset"],
                "ci_low": row["ci_low_at_onset"],
                "ci_high": row["ci_high_at_onset"],
            }
        )

    onset_summary = pd.DataFrame(controlled_onsets)
    onset_summary.to_csv(output_dir / "high_level_onset_summary.csv", index=False)

    best_breaks = (
        utterance_changepoints.sort_values(["outcome", "aic"])
        .groupby("outcome", as_index=False)
        .first()
    )
    best_breaks["outcome"] = best_breaks["outcome"].map(
        {"sum_bits_exact_word_count": "Total bits with exact word-count control"}
    ).fillna(best_breaks["outcome"])

    child_age_audit = pd.DataFrame(
        [
            {
                "child_age_cells": len(child_age),
                "children": child_age["child_id"].nunique(),
                "datasets": child_age["dataset"].nunique(),
                "utterance_rows": int(child_age["utterance_count"].sum()),
                "first_age_bin": child_age.sort_values("age_mid")["age_bin"].astype(str).iloc[0],
                "last_age_bin": child_age.sort_values("age_mid")["age_bin"].astype(str).iloc[-1],
            }
        ]
    )

    report = f"""# Developmental Onset Of Communicative Efficiency

This is a working report for the new question raised in the latest supervisor discussion: not just whether the trajectory trends downward, but **when in developmental time the communicative-efficiency signal becomes detectable**.

## Transcript Anchor

The June 4 meeting transcript frames this as a control-and-timing problem. Around the 20-30 minute chunk, the discussion moves from simple averages to whether there is a decrease in surprisal when we control for the exact children and utterance length. That is the standard used here.

This report therefore treats "kick-in" as an operational question, not a single magical month.

## Analysis Scope

Inputs:

- Real child timing table: `results/yang_followup/yang_followup_analysis_rows.csv.gz`
- Context-modulation age-bin coefficients: `results/yang_followup/age_bin_modulation_coefficients.csv`
- Paired Bayes/Mistral baseline gaps: `results/bayes_information_report/paired_baseline_minus_real_gaps.csv.gz`
- PBM complexity age-bin summaries: `results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/pbm_real_complexity_age_bin_summary.csv.gz`

Audit:

{md_table(child_age_audit, digits=2)}

The headline timing model is utterance-level because that matches the earlier Route 1 evidence: child identity is controlled, word-count effort is held fixed with exact/top-coded word-count bins, and uncertainty is clustered by child. A stricter child-by-age-bin aggregate is included as a sensitivity check because it changes the weighting and has only 77 cells.

## What Counts As "Kick-In"

I compute three complementary timing signals:

1. **Controlled real-child trajectory:** age-bin effects on real child Mistral bits after controlling for child identity and fixed word-count effort.
2. **Paired real advantage:** generated baseline minus real child bits/token in the same context. Positive values mean the real child utterance is lower-bit than the generated alternative.
3. **Context modulation:** age-specific coefficients showing whether richer caregiver context predicts lower child total bits.

I also plot MLU and vocabulary timing beside these signals, because a reviewer will ask whether any CE onset is just grammatical or lexical growth.

## High-Level Onset Read

{md_table(onset_summary, digits=3)}

![Onset signal map]({rel(figure_paths["onset_map"], doc_md)})

## Controlled Real-Child Age Effects

The main model here is the same family as the earlier downward-trend evidence: utterance-level total bits, child fixed effects, and fixed word-count effort. Word counts are exact up to 11 words and top-coded as `12_plus` for rare longer child utterances. Coefficients are differences from `006-023`; negative values mean lower bits than the earliest bin at the same word-count level.

Model audit:

{md_table(utterance_models, digits=4)}

{md_table(utterance_age_effects[["outcome", "age_bin", "estimate_vs_006_023", "ci_low", "ci_high", "p_value"]], digits=4)}

![Controlled age effects]({rel(figure_paths["age_effects"], doc_md)})

Sensitivity check: when the data are first collapsed to child-by-age-bin cells and then modeled with mean word count, the simple age-bin effect is not the same. This is useful caution for peer review: the onset claim should be tied to the utterance-level fixed-effort model, and the child-age aggregate should be reported as a weighting sensitivity rather than ignored.

{md_table(child_age_models, digits=4)}

{md_table(child_age_effects[["outcome", "age_bin", "estimate_vs_006_023", "ci_low", "ci_high", "p_value"]], digits=4)}

## Change-Point Scan

The change-point scan is deliberately simple: fit a linear utterance-level fixed-word-count age model and a set of piecewise linear models with candidate breakpoints. This does not prove a biological phase transition, but it tells us where the descriptive elbow is strongest under this model family.

Best-supported breakpoint rows:

{md_table(best_breaks[["outcome", "breakpoint_month", "aic", "delta_aic_vs_best", "r2", "age_slope", "post_break_slope_change", "post_break_p"]], digits=4)}

Full change-point table:

{md_table(utterance_changepoints[["outcome", "breakpoint_month", "delta_aic_vs_best", "r2", "age_slope", "post_break_slope_change", "post_break_p"]], digits=4)}

![Change-point scan]({rel(figure_paths["changepoints"], doc_md)})

## Paired Real-Versus-Baseline Timing

These are child-age-cell summaries of same-context generated baselines. Positive means the baseline has higher bits/token than the real child response.

{md_table(paired_onsets, digits=3)}

![Paired baseline gaps]({rel(figure_paths["paired_gaps"], doc_md)})

## Context-Modulation Timing

This is the closest direct answer to the meeting concern about whether context begins to matter at a particular developmental point. Negative coefficients mean higher context entropy or longer parent context predicts lower child total bits within that age bin, after the controls used in the Yang follow-up analysis.

{md_table(context_onsets, digits=3)}

![Context modulation timing]({rel(figure_paths["context_modulation"], doc_md)})

## Complexity Timing As A Check

These are descriptive child-age-bin summaries for MLU-style and lexical predictors. They should be treated as timing controls and developmental descriptors, not as substitutes for information-theoretic CE.

{md_table(complexity_summary[["age_bin", "n_cells", "mean_words_per_utterance_mean", "mean_words_per_utterance_ci_low", "mean_words_per_utterance_ci_high", "age_bin_vocab_size_mean", "age_bin_vocab_size_ci_low", "age_bin_vocab_size_ci_high"]], digits=3)}

Adjusted complexity effects relative to `006-023`:

{md_table(complexity_effects[["outcome", "age_bin", "estimate_vs_006_023", "ci_low", "ci_high", "p_value"]], digits=4)}

![Complexity timing]({rel(figure_paths["complexity"], doc_md)})

## Current Scientific Read

- The safest phrasing is not "CE starts at exactly month X." The defensible claim is: **the fixed-word-count age-bin decrease is already detectable by 024-029, context-entropy modulation is visible in 006-023, and parent-context-word modulation becomes detectable in 024-029.**
- For supervisor-facing material, the strongest presentation is likely an onset map plus one controlled age-effect plot and one paired real-versus-trigram plot.
- Before promotion to the July report, the next robustness step should bootstrap by child and repeat the onset table for alternative effort controls: words, morphemes, syllables, and phoneme proxies.

## Outputs

- Working tables: `results/developmental_onset_report/`
- Figures: `figs/developmental_onset_report/`
- HTML report: `docs/developmental_onset_working_report.html`
"""
    doc_md.write_text(report, encoding="utf-8")
    render_markdown_file(doc_md, doc_html)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yang-rows", type=Path, default=DEFAULT_YANG_ROWS)
    parser.add_argument("--context-coefs", type=Path, default=DEFAULT_CONTEXT_COEFS)
    parser.add_argument("--paired-gaps", type=Path, default=DEFAULT_PAIRED_GAPS)
    parser.add_argument("--complexity-age", type=Path, default=DEFAULT_COMPLEXITY_AGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path, label in [
        (args.yang_rows, "real child Yang follow-up rows"),
        (args.context_coefs, "age-bin context coefficients"),
        (args.paired_gaps, "paired Bayes/Mistral gaps"),
        (args.complexity_age, "PBM complexity age-bin summary"),
    ]:
        require(path, label)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.fig_dir.mkdir(parents=True, exist_ok=True)
    args.doc_md.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    real_rows, child_age = read_real_child_age_rows(args.yang_rows)
    child_age.to_csv(args.output_dir / "child_age_bin_real_mistral.csv", index=False)

    utterance_age_effects, utterance_models = fit_utterance_age_models(real_rows)
    utterance_age_effects.to_csv(args.output_dir / "utterance_level_exact_word_age_effects.csv", index=False)
    utterance_models.to_csv(args.output_dir / "utterance_level_exact_word_model_audit.csv", index=False)

    child_age_effects, child_age_models = fit_controlled_age_effects(child_age)
    child_age_effects.to_csv(args.output_dir / "child_age_aggregate_controlled_age_effects.csv", index=False)
    child_age_models.to_csv(args.output_dir / "child_age_aggregate_model_audit.csv", index=False)

    utterance_changepoints = fit_utterance_changepoints(real_rows)
    utterance_changepoints.to_csv(args.output_dir / "changepoint_model_summary.csv", index=False)

    child_source_age, paired_summary, paired_onsets = read_paired_gaps(args.paired_gaps)
    child_source_age.to_csv(args.output_dir / "paired_gap_child_source_age.csv.gz", index=False)
    paired_summary.to_csv(args.output_dir / "paired_gap_age_summary.csv", index=False)
    paired_onsets.to_csv(args.output_dir / "paired_gap_onset_summary.csv", index=False)

    context_coefs, context_onsets = read_context_modulation(args.context_coefs)
    context_coefs.to_csv(args.output_dir / "context_modulation_coefficients.csv", index=False)
    context_onsets.to_csv(args.output_dir / "context_modulation_onset_summary.csv", index=False)

    complexity_rows, complexity_summary, complexity_effects = read_complexity(args.complexity_age)
    complexity_rows.to_csv(args.output_dir / "complexity_child_age_rows.csv", index=False)
    complexity_summary.to_csv(args.output_dir / "complexity_age_summary.csv", index=False)
    complexity_effects.to_csv(args.output_dir / "complexity_adjusted_age_effects.csv", index=False)

    onset_map, onset_pivot = build_onset_map(utterance_age_effects, paired_summary, context_coefs, complexity_effects)
    onset_map.to_csv(args.output_dir / "onset_signal_map_long.csv", index=False)
    onset_pivot.to_csv(args.output_dir / "onset_signal_map.csv")

    figure_paths = {
        "age_effects": args.fig_dir / "controlled_real_child_age_effects.png",
        "changepoints": args.fig_dir / "piecewise_changepoint_scan.png",
        "paired_gaps": args.fig_dir / "paired_real_advantage_onset.png",
        "context_modulation": args.fig_dir / "context_modulation_onset.png",
        "complexity": args.fig_dir / "complexity_timing_checks.png",
        "onset_map": args.fig_dir / "onset_signal_map.png",
    }
    plot_utterance_age_effects(utterance_age_effects, child_age_effects, figure_paths["age_effects"])
    plot_changepoints(utterance_changepoints, figure_paths["changepoints"])
    plot_paired_gaps(paired_summary, figure_paths["paired_gaps"])
    plot_context_modulation(context_coefs, figure_paths["context_modulation"])
    plot_complexity(complexity_summary, figure_paths["complexity"])
    plot_onset_map(onset_pivot, figure_paths["onset_map"])

    build_report(
        doc_md=args.doc_md,
        doc_html=args.doc_html,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        child_age=child_age,
        utterance_age_effects=utterance_age_effects,
        utterance_models=utterance_models,
        utterance_changepoints=utterance_changepoints,
        child_age_effects=child_age_effects,
        child_age_models=child_age_models,
        paired_summary=paired_summary,
        paired_onsets=paired_onsets,
        context_onsets=context_onsets,
        complexity_summary=complexity_summary,
        complexity_effects=complexity_effects,
        onset_map=onset_map,
        figure_paths=figure_paths,
    )

    print(
        {
            "status": "ok",
            "real_utterance_rows": int(len(real_rows)),
            "child_age_cells": int(len(child_age)),
            "report": str(args.doc_html),
        }
    )


if __name__ == "__main__":
    main()
