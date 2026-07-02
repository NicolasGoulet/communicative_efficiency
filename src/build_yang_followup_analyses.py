#!/usr/bin/env python3
"""Build follow-up analyses requested after Yang's supervisor-report feedback."""

from __future__ import annotations

import argparse
import html
import math
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

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
    from build_route1_analysis_dataset import count_effort
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_analysis_dataset import count_effort
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/yang_followup")
DEFAULT_FIG_DIR = Path("figs/yang_followup")
DEFAULT_DOC_MD = Path("docs/yang_feedback_followup_report.md")
DEFAULT_DOC_HTML = Path("docs/yang_feedback_followup_report.html")
AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]


def fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def fmt_p(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    if number < 0.001:
        return "<.001"
    return f"{number:.3f}"


def md_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    text = frame.fillna("").astype(str)
    headers = list(text.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in text.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in headers) + " |")
    return "\n".join(lines)


def rel(path: Path, base: Path) -> str:
    return os.path.relpath(path, start=base.parent).replace(os.sep, "/")


def shorten(text: object, limit: int = 170) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "..."


def coerce_numeric(frame: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def context_effort_words(text: object) -> int:
    return count_effort("" if pd.isna(text) else str(text)).nb_words


def read_child_and_caretaker_rows(input_csv: Path, *, chunksize: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    usecols = [
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "utt_id",
        "speaker",
        "role",
        "target_variant",
        "context_k",
        "target_utterance_clean",
        "context_text",
        "sum_bits",
        "n_eval_tokens",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_syllables_pkg",
        "nb_phonemes",
        "context_entropy_bits",
    ]
    child_parts: list[pd.DataFrame] = []
    caretaker_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(usecols),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        child = chunk[
            chunk["role"].eq("child") & chunk["target_variant"].eq("real") & chunk["context_k"].eq("k3")
        ].copy()
        if not child.empty:
            child_parts.append(child)
        caretaker = chunk[
            chunk["role"].eq("caretaker")
            & chunk["target_variant"].eq("caretaker")
            & chunk["context_k"].eq("k0")
        ].copy()
        if not caretaker.empty:
            caretaker_parts.append(caretaker)
    if not child_parts:
        raise RuntimeError("No real-child k3 rows found.")
    child_rows = pd.concat(child_parts, ignore_index=True)
    caretaker_rows = pd.concat(caretaker_parts, ignore_index=True) if caretaker_parts else pd.DataFrame(columns=usecols)
    numeric = [
        "age_months",
        "line_no",
        "utt_id",
        "sum_bits",
        "n_eval_tokens",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_syllables_pkg",
        "nb_phonemes",
        "context_entropy_bits",
    ]
    return coerce_numeric(child_rows, numeric), coerce_numeric(caretaker_rows, numeric)


def attach_context_effort(child: pd.DataFrame) -> pd.DataFrame:
    out = child.copy()
    unique_contexts = out["context_text"].fillna("").astype(str).drop_duplicates()
    lookup = {text: context_effort_words(text) for text in unique_contexts}
    out["parent_context_nb_words"] = out["context_text"].fillna("").astype(str).map(lookup).astype(float)
    return out


def attach_prior_caretaker_bits(child: pd.DataFrame, caretaker: pd.DataFrame) -> pd.DataFrame:
    child_base = child.copy().reset_index(drop=True)
    child_base["_child_row_id"] = np.arange(len(child_base))
    child_min = child_base[
        [
            "_child_row_id",
            "dataset",
            "child_id",
            "session_id",
            "file",
            "line_no",
            "utt_id",
            "target_utterance_clean",
        ]
    ].copy()
    child_min["_row_type"] = "child"
    caretaker_min = caretaker[
        [
            "dataset",
            "child_id",
            "session_id",
            "file",
            "line_no",
            "utt_id",
            "target_utterance_clean",
            "sum_bits",
            "nb_words",
        ]
    ].copy()
    caretaker_min["_row_type"] = "caretaker"
    combined = pd.concat([child_min, caretaker_min], ignore_index=True, sort=False)
    combined["_file_sort"] = combined["file"].astype(str)
    combined["_line_no_num"] = pd.to_numeric(combined["line_no"], errors="coerce")
    combined["_utt_id_num"] = pd.to_numeric(combined["utt_id"], errors="coerce")
    combined["_role_order"] = combined["_row_type"].map({"caretaker": 0, "child": 1}).fillna(9)
    rows: list[dict[str, object]] = []
    group_cols = ["dataset", "child_id", "session_id"]
    for _, group in combined.groupby(group_cols, sort=False, dropna=False):
        history: list[dict[str, object]] = []
        ordered = group.sort_values(["_file_sort", "_line_no_num", "_utt_id_num", "_role_order"], kind="stable")
        for row in ordered.to_dict("records"):
            if row["_row_type"] == "caretaker":
                if math.isfinite(float(row.get("sum_bits", math.nan))) and float(row.get("nb_words", math.nan)) > 0:
                    history.append(
                        {
                            "text": row.get("target_utterance_clean", ""),
                            "sum_bits": float(row.get("sum_bits")),
                            "nb_words": float(row.get("nb_words")),
                        }
                    )
                continue
            recent = history[-3:]
            rows.append(
                {
                    "_child_row_id": int(row["_child_row_id"]),
                    "prior_caretaker_count": len(recent),
                    "prior_caretaker_sum_bits": sum(item["sum_bits"] for item in recent),
                    "prior_caretaker_nb_words": sum(item["nb_words"] for item in recent),
                    "prior_caretaker_text": " ".join(str(item["text"]) for item in recent),
                }
            )
    context = pd.DataFrame(rows)
    out = child_base.merge(context, on="_child_row_id", how="left")
    out["prior_caretaker_mean_bits_per_word"] = out["prior_caretaker_sum_bits"] / out["prior_caretaker_nb_words"].replace(0, np.nan)
    return out.drop(columns=["_child_row_id"])


def analysis_frame(input_csv: Path, *, chunksize: int, output_dir: Path) -> pd.DataFrame:
    cached = output_dir / "yang_followup_analysis_rows.csv.gz"
    if cached.exists():
        return pd.read_csv(cached)
    child, caretaker = read_child_and_caretaker_rows(input_csv, chunksize=chunksize)
    child = attach_context_effort(child)
    child = attach_prior_caretaker_bits(child, caretaker)
    required = [
        "sum_bits",
        "age_months",
        "age_bin",
        "child_id",
        "nb_words",
        "parent_context_nb_words",
        "context_entropy_bits",
        "prior_caretaker_sum_bits",
    ]
    child = child.dropna(subset=required).copy()
    child = child[
        (child["sum_bits"] > 0)
        & (child["age_months"] > 0)
        & (child["nb_words"] > 0)
        & (child["parent_context_nb_words"] > 0)
        & (child["context_entropy_bits"] > 0)
        & (child["prior_caretaker_count"] > 0)
    ].copy()
    child["child_id"] = child["child_id"].astype(str)
    child["age_bin"] = pd.Categorical(child["age_bin"].astype(str), AGE_BIN_ORDER, ordered=True)
    child["age_c"] = child["age_months"] - child["age_months"].mean()
    child["child_words_c"] = child["nb_words"] - child["nb_words"].mean()
    child["parent_context_words_c"] = child["parent_context_nb_words"] - child["parent_context_nb_words"].mean()
    child["context_entropy_c"] = child["context_entropy_bits"] - child["context_entropy_bits"].mean()
    child["prior_caretaker_sum_bits_c"] = child["prior_caretaker_sum_bits"] - child["prior_caretaker_sum_bits"].mean()
    output_dir.mkdir(parents=True, exist_ok=True)
    child.to_csv(cached, index=False)
    return child


def fit_clustered(formula: str, frame: pd.DataFrame):
    return smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame["child_id"].astype(str)})


def model_row(model_name: str, result: object, terms: Sequence[str]) -> pd.DataFrame:
    rows = []
    conf = result.conf_int()
    for term in terms:
        rows.append(
            {
                "model": model_name,
                "term": term,
                "estimate": float(result.params.get(term, math.nan)),
                "ci_low": float(conf.loc[term, 0]) if term in conf.index else math.nan,
                "ci_high": float(conf.loc[term, 1]) if term in conf.index else math.nan,
                "p": float(result.pvalues.get(term, math.nan)),
                "n": int(result.nobs),
                "r2": float(getattr(result, "rsquared", math.nan)),
            }
        )
    return pd.DataFrame(rows)


def fit_followup_models(frame: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    models = {
        "M4 current context controls": fit_clustered(
            "sum_bits ~ age_c + child_words_c + age_c:child_words_c + parent_context_words_c + context_entropy_c + C(child_id)",
            frame,
        ),
        "Direct caretaker information": fit_clustered(
            "sum_bits ~ age_c + child_words_c + age_c:child_words_c + parent_context_words_c + prior_caretaker_sum_bits_c + C(child_id)",
            frame,
        ),
        "Age-varying informativeness modulation": fit_clustered(
            "sum_bits ~ age_c + child_words_c + age_c:child_words_c + parent_context_words_c + context_entropy_c + age_c:parent_context_words_c + age_c:context_entropy_c + C(child_id)",
            frame,
        ),
        "Child effort modulation": fit_clustered(
            "nb_words ~ age_c + parent_context_words_c + context_entropy_c + C(child_id)",
            frame,
        ),
        "Age-varying child effort modulation": fit_clustered(
            "nb_words ~ age_c + parent_context_words_c + context_entropy_c + age_c:parent_context_words_c + age_c:context_entropy_c + C(child_id)",
            frame,
        ),
    }
    terms = {
        "M4 current context controls": ["age_c", "child_words_c", "age_c:child_words_c", "parent_context_words_c", "context_entropy_c"],
        "Direct caretaker information": ["age_c", "child_words_c", "age_c:child_words_c", "parent_context_words_c", "prior_caretaker_sum_bits_c"],
        "Age-varying informativeness modulation": [
            "age_c",
            "child_words_c",
            "age_c:child_words_c",
            "parent_context_words_c",
            "context_entropy_c",
            "age_c:parent_context_words_c",
            "age_c:context_entropy_c",
        ],
        "Child effort modulation": ["age_c", "parent_context_words_c", "context_entropy_c"],
        "Age-varying child effort modulation": [
            "age_c",
            "parent_context_words_c",
            "context_entropy_c",
            "age_c:parent_context_words_c",
            "age_c:context_entropy_c",
        ],
    }
    summary = pd.concat([model_row(name, result, terms[name]) for name, result in models.items()], ignore_index=True)
    summary.to_csv(output_dir / "yang_followup_model_summary.csv", index=False)
    return summary, models


def average_predictions(result: object, base: pd.DataFrame, child_ids: Sequence[str]) -> np.ndarray:
    preds = []
    for child_id in child_ids:
        grid = base.copy()
        grid["child_id"] = child_id
        preds.append(np.asarray(result.predict(grid), dtype=float))
    return np.vstack(preds).mean(axis=0)


def plot_age_modulation(frame: pd.DataFrame, models: dict[str, object], fig_dir: Path) -> dict[str, Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    child_ids = sorted(frame["child_id"].astype(str).unique())
    ages = np.linspace(frame["age_months"].quantile(0.03), frame["age_months"].quantile(0.97), 80)
    fixed_words = float(frame["nb_words"].median())
    low_context, high_context = frame["parent_context_nb_words"].quantile([0.15, 0.85]).tolist()
    low_entropy, high_entropy = frame["context_entropy_bits"].quantile([0.15, 0.85]).tolist()
    mean_age = float(frame["age_months"].mean())
    mean_words = float(frame["nb_words"].mean())
    mean_context = float(frame["parent_context_nb_words"].mean())
    mean_entropy = float(frame["context_entropy_bits"].mean())

    info_model = models["Age-varying informativeness modulation"]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharey=True)
    for value, label, color in [(low_context, f"short context: {low_context:.0f} words", "#2f6f73"), (high_context, f"long context: {high_context:.0f} words", "#c76f2c")]:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - mean_age,
                "child_words_c": fixed_words - mean_words,
                "parent_context_words_c": value - mean_context,
                "context_entropy_c": 0.0,
            }
        )
        axes[0].plot(ages, average_predictions(info_model, base, child_ids), label=label, color=color, lw=2.4)
    axes[0].set_title("Parent context effort")
    axes[0].set_xlabel("Age in months")
    axes[0].set_ylabel(f"Predicted child sum_bits\nfixed child length = {fixed_words:.0f} words")
    axes[0].legend(frameon=True, fontsize=9)
    for value, label, color in [(low_entropy, f"low entropy: {low_entropy:.1f}", "#2f6f73"), (high_entropy, f"high entropy: {high_entropy:.1f}", "#c76f2c")]:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - mean_age,
                "child_words_c": fixed_words - mean_words,
                "parent_context_words_c": 0.0,
                "context_entropy_c": value - mean_entropy,
            }
        )
        axes[1].plot(ages, average_predictions(info_model, base, child_ids), label=label, color=color, lw=2.4)
    axes[1].set_title("Context entropy")
    axes[1].set_xlabel("Age in months")
    axes[1].legend(frameon=True, fontsize=9)
    fig.suptitle("Does child informativeness modulation change with age?", y=1.02)
    fig.tight_layout()
    info_path = fig_dir / "age_varying_informativeness_modulation.png"
    fig.savefig(info_path, dpi=190, bbox_inches="tight")
    plt.close(fig)

    effort_model = models["Age-varying child effort modulation"]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharey=True)
    for value, label, color in [(low_context, f"short context: {low_context:.0f} words", "#2f6f73"), (high_context, f"long context: {high_context:.0f} words", "#c76f2c")]:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - mean_age,
                "parent_context_words_c": value - mean_context,
                "context_entropy_c": 0.0,
            }
        )
        axes[0].plot(ages, average_predictions(effort_model, base, child_ids), label=label, color=color, lw=2.4)
    axes[0].set_title("Parent context effort")
    axes[0].set_xlabel("Age in months")
    axes[0].set_ylabel("Predicted child word count")
    axes[0].legend(frameon=True, fontsize=9)
    for value, label, color in [(low_entropy, f"low entropy: {low_entropy:.1f}", "#2f6f73"), (high_entropy, f"high entropy: {high_entropy:.1f}", "#c76f2c")]:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - mean_age,
                "parent_context_words_c": 0.0,
                "context_entropy_c": value - mean_entropy,
            }
        )
        axes[1].plot(ages, average_predictions(effort_model, base, child_ids), label=label, color=color, lw=2.4)
    axes[1].set_title("Context entropy")
    axes[1].set_xlabel("Age in months")
    axes[1].legend(frameon=True, fontsize=9)
    fig.suptitle("Does child effort modulation change with age?", y=1.02)
    fig.tight_layout()
    effort_path = fig_dir / "age_varying_effort_modulation.png"
    fig.savefig(effort_path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return {"info_age_modulation": info_path, "effort_age_modulation": effort_path}


def fit_age_bin_coefficients(frame: pd.DataFrame, output_dir: Path, fig_dir: Path) -> Path:
    rows: list[dict[str, object]] = []
    for age_bin in AGE_BIN_ORDER:
        sub = frame[frame["age_bin"].astype(str).eq(age_bin)].copy()
        if len(sub) < 1000 or sub["child_id"].nunique() < 2:
            continue
        sub["child_words_bin_c"] = sub["nb_words"] - sub["nb_words"].mean()
        sub["parent_context_words_bin_c"] = sub["parent_context_nb_words"] - sub["parent_context_nb_words"].mean()
        sub["context_entropy_bin_c"] = sub["context_entropy_bits"] - sub["context_entropy_bits"].mean()
        for outcome, formula in [
            (
                "child sum_bits",
                "sum_bits ~ child_words_bin_c + parent_context_words_bin_c + context_entropy_bin_c + C(child_id)",
            ),
            (
                "child word count",
                "nb_words ~ parent_context_words_bin_c + context_entropy_bin_c + C(child_id)",
            ),
        ]:
            try:
                result = smf.ols(formula, data=sub).fit(
                    cov_type="cluster",
                    cov_kwds={"groups": sub["child_id"].astype(str)},
                )
            except Exception:
                continue
            conf = result.conf_int()
            for term, label in [
                ("parent_context_words_bin_c", "parent context words"),
                ("context_entropy_bin_c", "context entropy"),
            ]:
                if term not in result.params:
                    continue
                rows.append(
                    {
                        "age_bin": age_bin,
                        "age_mid": np.mean([float(x) for x in age_bin.split("-")]) if "-" in age_bin else math.nan,
                        "outcome": outcome,
                        "predictor": label,
                        "estimate": float(result.params[term]),
                        "ci_low": float(conf.loc[term, 0]),
                        "ci_high": float(conf.loc[term, 1]),
                        "p": float(result.pvalues[term]),
                        "n": int(result.nobs),
                        "children": int(sub["child_id"].nunique()),
                    }
                )
    coef = pd.DataFrame(rows)
    coef.to_csv(output_dir / "age_bin_modulation_coefficients.csv", index=False)
    if coef.empty:
        return Path()
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 2, figsize=(14, 8.5), sharex=True)
    for ax, ((outcome, predictor), group) in zip(axes.flatten(), coef.groupby(["outcome", "predictor"], sort=True)):
        group = group.sort_values("age_mid")
        x = np.arange(len(group))
        ax.axhline(0, color="#333333", lw=1)
        ax.errorbar(
            x,
            group["estimate"],
            yerr=[group["estimate"] - group["ci_low"], group["ci_high"] - group["estimate"]],
            fmt="o-",
            color="#2f6f73" if predictor == "parent context words" else "#c76f2c",
            lw=2.0,
            capsize=3,
        )
        ax.set_title(f"{outcome}: {predictor}")
        ax.set_xticks(x)
        ax.set_xticklabels(group["age_bin"], rotation=35, ha="right")
        ax.set_ylabel("Coefficient")
    fig.suptitle("Age-bin modulation coefficients", y=1.02)
    fig.tight_layout()
    path = fig_dir / "age_bin_modulation_coefficients.png"
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return path


def select_examples(frame: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    data = frame.copy()
    data = data[data["nb_words"].between(2, 8)].copy()
    context_word_q25, context_word_q75 = data["parent_context_nb_words"].quantile([0.25, 0.75]).tolist()
    context_bits_q25, context_bits_q75 = data["prior_caretaker_sum_bits"].quantile([0.25, 0.75]).tolist()
    child_bits_q25 = data.groupby("nb_words")["sum_bits"].transform(lambda values: values.quantile(0.25))
    child_bits_q75 = data.groupby("nb_words")["sum_bits"].transform(lambda values: values.quantile(0.75))
    data["is_high_context_low_child"] = (
        (data["parent_context_nb_words"] >= context_word_q75)
        & (data["prior_caretaker_sum_bits"] >= context_bits_q75)
        & (data["sum_bits"] <= child_bits_q25)
    )
    data["is_low_context_high_child"] = (
        (data["parent_context_nb_words"] <= context_word_q25)
        & (data["prior_caretaker_sum_bits"] <= context_bits_q25)
        & (data["sum_bits"] >= child_bits_q75)
    )
    pairs: list[dict[str, object]] = []
    for (words, age_bin), group in data.groupby(["nb_words", "age_bin"], observed=True):
        high = group[group["is_high_context_low_child"]].sort_values("sum_bits", ascending=True)
        low = group[group["is_low_context_high_child"]].sort_values("sum_bits", ascending=False)
        if high.empty or low.empty:
            continue
        high_row = high.iloc[0]
        low_row = low.iloc[0]
        pairs.append(
            {
                "age_bin": age_bin,
                "child_words": int(words),
                "high_context_dataset": high_row["dataset"],
                "high_context_child": high_row["child_id"],
                "high_context_age_months": fmt(high_row["age_months"], 1),
                "high_context_words": int(high_row["parent_context_nb_words"]),
                "high_context_bits": fmt(high_row["prior_caretaker_sum_bits"], 1),
                "high_context_child_bits": fmt(high_row["sum_bits"], 1),
                "high_context_text": shorten(high_row["context_text"]),
                "high_context_child_response": shorten(high_row["target_utterance_clean"]),
                "low_context_dataset": low_row["dataset"],
                "low_context_child": low_row["child_id"],
                "low_context_age_months": fmt(low_row["age_months"], 1),
                "low_context_words": int(low_row["parent_context_nb_words"]),
                "low_context_bits": fmt(low_row["prior_caretaker_sum_bits"], 1),
                "low_context_child_bits": fmt(low_row["sum_bits"], 1),
                "low_context_text": shorten(low_row["context_text"]),
                "low_context_child_response": shorten(low_row["target_utterance_clean"]),
                "child_bits_gap_low_minus_high": float(low_row["sum_bits"] - high_row["sum_bits"]),
            }
        )
    out = pd.DataFrame(pairs).sort_values("child_bits_gap_low_minus_high", ascending=False).head(8)
    out.to_csv(output_dir / "matched_context_examples.csv", index=False)
    return out


def compact_model_table(summary: pd.DataFrame) -> pd.DataFrame:
    view = summary[
        summary["term"].isin(
            [
                "parent_context_words_c",
                "context_entropy_c",
                "prior_caretaker_sum_bits_c",
                "age_c:parent_context_words_c",
                "age_c:context_entropy_c",
            ]
        )
    ].copy()
    view["estimate"] = view["estimate"].map(lambda value: fmt(value, 4))
    view["95% CI"] = view.apply(lambda row: f"{fmt(row['ci_low'], 4)} to {fmt(row['ci_high'], 4)}", axis=1)
    view["p"] = view["p"].map(fmt_p)
    view["R2"] = view["r2"].map(lambda value: fmt(value, 3))
    return view[["model", "term", "estimate", "95% CI", "p", "n", "R2"]]


def compact_examples_table(examples: pd.DataFrame) -> pd.DataFrame:
    if examples.empty:
        return examples
    cols = [
        "age_bin",
        "child_words",
        "high_context_words",
        "high_context_bits",
        "high_context_child_bits",
        "high_context_text",
        "high_context_child_response",
        "low_context_words",
        "low_context_bits",
        "low_context_child_bits",
        "low_context_text",
        "low_context_child_response",
    ]
    return examples[cols].head(3).copy()


def build_report(
    *,
    md_path: Path,
    frame: pd.DataFrame,
    summary: pd.DataFrame,
    examples: pd.DataFrame,
    figures: dict[str, Path],
    age_bin_figure: Path,
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "# Yang Feedback Follow-up",
        "",
        "This is a technical follow-up to the supervisor-facing report. It does not replace the main report.",
        "",
        "## Point-by-point response",
        "",
        "1. **Question being answered.** The current Route 1 analyses mainly answer: what factors predict or modulate the informativeness of child speech? They show modulation of child `sum_bits` after controlling age, child effort, and child identity.",
        "",
        "2. **Caretaker-context interpretation.** The current Model 4 context predictors are `parent_context_nb_words` and `context_entropy_bits`. The entropy variable is next-token uncertainty after the preceding caretaker context; it is not identical to caretaker utterance informativeness. Therefore, this follow-up adds a direct companion predictor: the summed k0 `sum_bits` of the previous up-to-three caretaker utterances.",
        "",
        "3. **Concrete examples.** The table below gives illustrative matched cases where child word count is the same within the pair. These examples are for intuition only; the regression is the evidential test.",
        "",
        "4. **Context window clarification.** `k1`, `k2`, and `k3` mean previous caretaker utterances, not words. The supervisor-report Model 4 uses `k3`: up to three previous caretaker utterances in the same session. There is no word cap inside each caretaker utterance beyond the fact that the window is bounded to three utterances.",
        "",
        "5. **Effort analogue.** A first-pass child-effort model is included below: child word count is predicted from age, preceding-context effort, context entropy, and child identity. This is the natural next Route 1 sibling model.",
        "",
        "6. **When modulation emerges.** Two plots below visualize whether context modulation changes with age: one using continuous age interactions, and one using age-bin-specific context coefficients.",
        "",
        "## Model summary",
        "",
        md_table(compact_model_table(summary)),
        "",
        "## Matched examples",
        "",
        md_table(compact_examples_table(examples)),
        "",
        "Saved full example table:",
        "",
        "```text",
        "results/yang_followup/matched_context_examples.csv",
        "```",
        "",
        "## Age-varying modulation plots",
        "",
        f"![Age-varying informativeness modulation]({rel(figures['info_age_modulation'], md_path)})",
        "",
        f"![Age-varying effort modulation]({rel(figures['effort_age_modulation'], md_path)})",
        "",
        f"![Age-bin modulation coefficients]({rel(age_bin_figure, md_path)})" if age_bin_figure else "",
        "",
        "## Original near-optimality question",
        "",
        "The original question asks whether children are near-optimally informative, not just whether their informativeness is modulated. The present Route 1 results are evidence for modulation, but not a full optimality test. A stronger optimality test needs counterfactual alternatives for the same context and comparable effort, then asks where the real child utterance lies relative to those alternatives or an effort-information frontier.",
        "",
        "Route 2 is the closer bridge to that question: for each caretaker context, generate/sample possible child responses, score their effort and informativeness, and compare the actual child response to the response set. The current Route 2 response-space entropy work is therefore not a distraction; it is the machinery needed to define the alternative response space for an optimality-style analysis.",
        "",
        "## Saved artifacts",
        "",
        "```text",
        f"Rows: {len(frame):,}",
        "results/yang_followup/yang_followup_analysis_rows.csv.gz",
        "results/yang_followup/yang_followup_model_summary.csv",
        "results/yang_followup/age_bin_modulation_coefficients.csv",
        "figs/yang_followup/",
        "```",
    ]
    md_path.write_text("\n".join(str(section) for section in sections if section != "") + "\n", encoding="utf-8")
    render_markdown_file(md_path, md_path.with_suffix(".html"), title="Yang Feedback Follow-up")
    render_markdown_file(md_path, md_path.with_suffix(".embedded.html"), title="Yang Feedback Follow-up", embed_images=True)


def build(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_md: Path,
    chunksize: int,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = analysis_frame(input_csv, chunksize=chunksize, output_dir=output_dir)
    summary, models = fit_followup_models(frame, output_dir)
    figures = plot_age_modulation(frame, models, fig_dir)
    age_bin_figure = fit_age_bin_coefficients(frame, output_dir, fig_dir)
    examples = select_examples(frame, output_dir)
    build_report(md_path=doc_md, frame=frame, summary=summary, examples=examples, figures=figures, age_bin_figure=age_bin_figure)
    return {
        "md": doc_md,
        "html": doc_md.with_suffix(".html"),
        "embedded": doc_md.with_suffix(".embedded.html"),
        "summary": output_dir / "yang_followup_model_summary.csv",
        "examples": output_dir / "matched_context_examples.csv",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--chunksize", type=int, default=350_000)
    args = parser.parse_args()
    paths = build(
        input_csv=args.input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_md=args.doc_md,
        chunksize=args.chunksize,
    )
    for label, path in paths.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
