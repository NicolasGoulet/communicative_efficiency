#!/usr/bin/env python3
"""Build a supervisor-facing candidate synthesis report.

This report is intentionally selective. It pulls the clearest Route 1 evidence
from the source-specific Atlas v2 outputs, adds heldout actual-vs-predicted
regression-line checks, and writes a candidate report that can be refined into
the supervisor-facing narrative.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from render_markdown_report import render_markdown_file


SOURCE_ATLAS_DIR = Path("results/route1_source_specific_corrected_fixed_effort_atlas")
HELDOUT_DIR = Path("results/route1_heldout_real_child_prediction")
ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/supervisor_candidate_report")
DEFAULT_FIG_DIR = Path("figs/supervisor_candidate_report")
DEFAULT_DOC_DIR = Path("docs")

DOC_BASENAME = "communicative_efficiency_supervisor_candidate_report_v0"

MODEL_ORDER = [
    "M1",
    "M2",
    "M3",
    "M4a",
    "M4b",
    "M4c",
    "M5",
    "M6",
    "M7",
    "M8",
    "M9",
    "M10",
    "M11",
    "M12",
    "M13",
    "M14",
    "M15",
]

SOURCE_ORDER = [
    "real",
    "random",
    "unigram",
    "bigram",
    "trigram",
    "lstm_additive_k3_same_length",
    "lstm_additive_k4_same_length",
    "lstm_additive_k5_same_length",
]

SOURCE_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
    "lstm_additive_k3_same_length": "LSTM k3",
    "lstm_additive_k4_same_length": "LSTM k4",
    "lstm_additive_k5_same_length": "LSTM k5",
}

MODEL_ONE_LINERS = {
    "M1": "Pooled age + effort sanity check; not the main developmental claim.",
    "M2": "Primary controlled line: age + effort with child identity fixed effects.",
    "M3": "Checks whether the age line changes across effort levels.",
    "M4a": "Adds preceding caretaker/context effort as a confound control.",
    "M4b": "Adds next-token context entropy as a contextual predictability control.",
    "M4c": "Adds broad question type, a key context-form confound from the email.",
    "M5": "Combines context effort, context entropy, and question type.",
    "M6": "Tests whether context entropy changes the age/effort relation.",
    "M7": "Nonlinear age check: age plus age squared.",
    "M8": "Nonlinear age-by-effort check.",
    "M9": "Categorical age-bin check rather than one straight age slope.",
    "M10": "Age-bin-by-effort check.",
    "M11": "Age-by-parent-context-effort interaction check.",
    "M12": "Age-by-question-type interaction check.",
    "M13": "Context-entropy-by-question-type interaction check.",
    "M14": "Parent-context-effort-by-context-entropy interaction check.",
    "M15": "Richest current context-interaction stress test.",
}

CHILD_ORDER = ["Forrester/Ella", "Sachs/Naomi", "MPI-EVA-Manchester/Helen"]
BAND_ORDER = ["1-4", "5-8", "9-12"]


def relative_to_report(report_path: Path, figure_path: Path) -> str:
    return os.path.relpath(figure_path.resolve(), start=report_path.parent.resolve()).replace(os.sep, "/")


def p_text(value: object) -> str:
    val = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(val):
        return ""
    if val < 0.001:
        return "<.001"
    return f"{val:.3f}"


def f_text(value: object, digits: int = 3) -> str:
    val = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(val):
        return ""
    return f"{val:.{digits}f}"


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 30) -> str:
    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    columns = [str(col) for col in shown.columns]
    rows = shown.astype(object).where(pd.notna(shown), "").astype(str).values.tolist()

    def clean(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(clean(col) for col in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(clean(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def figure_guide(*, shows: str, read: str, means: str, caution: str = "") -> list[str]:
    """Return a compact plain-language guide for one report figure."""
    lines = [
        f"- **What the figure shows:** {shows}",
        f"- **How to read it:** {read}",
        f"- **What it means here:** {means}",
    ]
    if caution:
        lines.append(f"- **Do not overclaim:** {caution}")
    return [*lines, ""]


def read_real_summary() -> pd.DataFrame:
    summary = pd.read_csv(SOURCE_ATLAS_DIR / "real" / "model_summary.csv")
    summary["model_id"] = pd.Categorical(summary["model_id"], categories=MODEL_ORDER, ordered=True)
    return summary.sort_values(["model_id", "context_k", "effort_col"]).reset_index(drop=True)


def model_cards(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model_id in MODEL_ORDER:
        sub = summary[summary["model_id"].astype(str).eq(model_id) & summary["status"].eq("fit")]
        if sub.empty:
            continue
        row = sub.iloc[0]
        rows.append(
            {
                "model": model_id,
                "question": row["question"],
                "formula": row["readable_formula"],
                "plain-language role": MODEL_ONE_LINERS.get(model_id, ""),
            }
        )
    return pd.DataFrame(rows)


def real_k3_words(summary: pd.DataFrame) -> pd.DataFrame:
    return (
        summary[
            summary["context_k"].eq("k3")
            & summary["effort_col"].eq("nb_words")
            & summary["status"].eq("fit")
        ]
        .copy()
        .sort_values("model_id")
    )


def build_importance_table(summary: pd.DataFrame) -> pd.DataFrame:
    sub = real_k3_words(summary)
    wanted = ["M1", "M2", "M3", "M4a", "M4b", "M4c", "M5", "M6", "M15"]
    sub = sub[sub["model_id"].astype(str).isin(wanted)].copy()
    base_m2 = float(sub[sub["model_id"].astype(str).eq("M2")]["r2_observed_fitted"].iloc[0])
    rows = []
    for _, row in sub.iterrows():
        model_id = str(row["model_id"])
        rows.append(
            {
                "model": model_id,
                "what changed": MODEL_ONE_LINERS.get(model_id, ""),
                "R2": f_text(row["r2_observed_fitted"], 4),
                "delta R2 vs M2": f_text(float(row["r2_observed_fitted"]) - base_m2, 4),
                "age effect": f"{f_text(row['age_coef'], 3)} bits/month (p={p_text(row['age_p'])})",
                "effort effect": f"{f_text(row['effort_coef'], 2)} bits/word (p={p_text(row['effort_p'])})",
                "context entropy": f"{f_text(row['context_entropy_coef'], 3)} (p={p_text(row['context_entropy_p'])})",
                "context effort": f"{f_text(row['parent_context_effort_coef'], 3)} (p={p_text(row['parent_context_effort_p'])})",
            }
        )
    return pd.DataFrame(rows)


def build_effect_sentence_table(summary: pd.DataFrame) -> pd.DataFrame:
    sub = real_k3_words(summary)
    m4c = sub[sub["model_id"].astype(str).eq("M4c")].iloc[0]
    m6 = sub[sub["model_id"].astype(str).eq("M6")].iloc[0]
    m3 = sub[sub["model_id"].astype(str).eq("M3")].iloc[0]
    return pd.DataFrame(
        [
            {
                "arrow": "age ↓",
                "effect": "Older children carry less total information at the same word count, after child identity and question type are controlled.",
                "number": f"{f_text(m4c['age_coef'], 3)} bits/month; p={p_text(m4c['age_p'])}",
            },
            {
                "arrow": "effort ↑",
                "effect": "Longer utterances carry much more information; this is the mechanical predictor we must hold fixed.",
                "number": f"{f_text(m4c['effort_coef'], 2)} bits per extra word; p={p_text(m4c['effort_p'])}",
            },
            {
                "arrow": "age × effort ≈ flat",
                "effect": "In real child speech, the age slope is not strongly different across word-count levels in this model.",
                "number": f"{f_text(m3['age_effort_coef'], 4)} bits/month/word; p={p_text(m3['age_effort_p'])}",
            },
            {
                "arrow": "context entropy ↓",
                "effect": "Next-token context entropy is a meaningful control here, but it is not the final Route 2 response-space entropy claim.",
                "number": f"{f_text(m6['context_entropy_coef'], 3)} bits; p={p_text(m6['context_entropy_p'])}",
            },
            {
                "arrow": "parent context effort ↓",
                "effect": "Longer preceding caretaker context slightly lowers child utterance information at fixed child effort.",
                "number": f"{f_text(m6['parent_context_effort_coef'], 3)} bits/context word; p={p_text(m6['parent_context_effort_p'])}",
            },
            {
                "arrow": "question type matters",
                "effect": "Question/statement form improves fit, so it belongs as a confound before telling the developmental story.",
                "number": "M4c has the best simple k3/word R2 among the context-control candidates.",
            },
        ]
    )


def plot_route_map(fig_dir: Path) -> Path:
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 6.0))
    ax.axis("off")
    boxes = [
        (
            0.04,
            0.58,
            0.42,
            0.30,
            "Route 1: information given effort",
            "Outcome: sum_bits\nQuestion: at the same effort,\ndoes information change with age?\nCurrent evidence: Atlas v2 + heldout check",
        ),
        (
            0.54,
            0.58,
            0.42,
            0.30,
            "Route 2: effort given context",
            "Outcome: utterance length / effort\nQuestion: when context is predictive,\ndo children shorten?\nStatus: next report after entropy predictors",
        ),
        (
            0.04,
            0.12,
            0.92,
            0.24,
            "Controls from the email",
            "Child age and identity; target effort; parent-context effort;\ncontext entropy/predictability; question type;\nlater SES/gender/clinical condition when metadata support it.",
        ),
    ]
    for x, y, w, h, title, text in boxes:
        rect = plt.Rectangle((x, y), w, h, transform=ax.transAxes, fc="#f7faf9", ec="#2f6f73", lw=1.8)
        ax.add_patch(rect)
        ax.text(x + 0.02, y + h - 0.07, title, transform=ax.transAxes, fontsize=15, weight="bold", color="#1f4e52")
        ax.text(x + 0.02, y + h - 0.14, text, transform=ax.transAxes, fontsize=10.5, va="top", color="#263238")
    ax.annotate("", xy=(0.55, 0.71), xytext=(0.45, 0.71), xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "lw": 2.0, "color": "#c76f2c"})
    ax.text(0.50, 0.77, "complementary", transform=ax.transAxes, ha="center", color="#8a4a1e", fontsize=11)
    path = fig_dir / "route1_route2_map.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_model_ladder_r2(summary: pd.DataFrame, fig_dir: Path, output_dir: Path) -> Path:
    sub = real_k3_words(summary)
    wanted = ["M1", "M2", "M3", "M4a", "M4b", "M4c", "M5", "M6", "M7", "M8", "M9", "M10", "M15"]
    sub = sub[sub["model_id"].astype(str).isin(wanted)].copy()
    sub["model_id_str"] = sub["model_id"].astype(str)
    base_m2 = float(sub[sub["model_id_str"].eq("M2")]["r2_observed_fitted"].iloc[0])
    sub["delta_r2_vs_m2"] = sub["r2_observed_fitted"] - base_m2
    sub.to_csv(output_dir / "real_k3_words_model_ladder_importance.csv", index=False)

    colors = ["#7a8793" if mid not in {"M2", "M4c", "M15"} else "#2f6f73" for mid in sub["model_id_str"]]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    axes[0].bar(sub["model_id_str"], sub["r2_observed_fitted"], color=colors)
    axes[0].set_ylim(max(0, sub["r2_observed_fitted"].min() - 0.006), sub["r2_observed_fitted"].max() + 0.002)
    axes[0].set_ylabel("R2: observed vs fitted")
    axes[0].set_title("Absolute model fit")
    axes[0].grid(axis="y", color="#e5e7eb")
    axes[1].bar(sub["model_id_str"], sub["delta_r2_vs_m2"] * 1000, color=colors)
    axes[1].axhline(0, color="#111827", lw=1)
    axes[1].set_ylabel("Delta R2 vs M2 x 1000")
    axes[1].set_title("Increment beyond child identity + effort")
    axes[1].grid(axis="y", color="#e5e7eb")
    for ax in axes:
        ax.set_xlabel("Model")
    fig.suptitle("Variable-importance view: most variance is effort/child identity; context controls add smaller but interpretable gains", y=1.02)
    plt.tight_layout()
    path = fig_dir / "real_k3_words_model_ladder_r2_importance.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_source_slope_comparison(fig_dir: Path, output_dir: Path, *, model_id: str = "M4c") -> Path:
    rows = []
    for source in SOURCE_ORDER:
        path = SOURCE_ATLAS_DIR / source / "fixed_slice_slopes.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        sub = frame[
            frame["context_k"].eq("k3")
            & frame["effort_col"].eq("nb_words")
            & frame["model_id"].eq(model_id)
        ].copy()
        for band, group in sub.groupby("atlas_bin", sort=False):
            rows.append(
                {
                    "source": source,
                    "source_label": SOURCE_LABELS.get(source, source),
                    "effort_band": band,
                    "slope_bits_per_6_months": float(group["slope_bits_per_6_months"].mean()),
                }
            )
    slopes = pd.DataFrame(rows)
    slopes.to_csv(output_dir / f"source_comparison_{model_id.lower()}_k3_words_slopes.csv", index=False)
    slopes["source_label"] = pd.Categorical(slopes["source_label"], [SOURCE_LABELS[s] for s in SOURCE_ORDER], ordered=True)
    slopes["effort_band"] = pd.Categorical(slopes["effort_band"], BAND_ORDER, ordered=True)

    fig, ax = plt.subplots(figsize=(12, 6.7))
    sns.barplot(
        data=slopes,
        y="source_label",
        x="slope_bits_per_6_months",
        hue="effort_band",
        palette={"1-4": "#2563eb", "5-8": "#d97706", "9-12": "#7c3aed"},
        ax=ax,
    )
    ax.axvline(0, color="#111827", lw=1.2)
    ax.set_xlabel("Fixed-effort age slope: bits per 6 months")
    ax.set_ylabel("")
    ax.set_title(f"Do fixed-effort age lines go down? Source-specific {model_id}, k3, words")
    ax.legend(title="Word-count band", loc="lower right")
    ax.grid(axis="x", color="#e5e7eb")
    sns.despine(ax=ax, left=True)
    plt.tight_layout()
    path = fig_dir / f"source_comparison_{model_id.lower()}_k3_words_slopes.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def line_fit(x: Sequence[float], y: Sequence[float]) -> tuple[float, float] | None:
    xvals = np.asarray(x, dtype=float)
    yvals = np.asarray(y, dtype=float)
    mask = np.isfinite(xvals) & np.isfinite(yvals)
    if mask.sum() < 2 or np.nanstd(xvals[mask]) <= 0:
        return None
    slope, intercept = np.polyfit(xvals[mask], yvals[mask], 1)
    return float(slope), float(intercept)


def plot_heldout_regression_check(fig_dir: Path, output_dir: Path, *, model_id: str = "POP_M4C") -> Path:
    observed = pd.read_csv(HELDOUT_DIR / "heldout_fixed_effort_observed_monthly.csv.gz")
    predicted = pd.read_csv(HELDOUT_DIR / "heldout_fixed_effort_prediction_grid.csv.gz")
    obs = observed[
        observed["context_k"].eq("k3")
        & observed["effort_col"].eq("nb_words")
        & observed["model_id"].eq(model_id)
        & (observed["rows"] >= 3)
    ].copy()
    pred = predicted[
        predicted["context_k"].eq("k3")
        & predicted["effort_col"].eq("nb_words")
        & predicted["model_id"].eq(model_id)
    ].copy()
    obs["effort_band"] = pd.Categorical(obs["effort_band"].astype(str), BAND_ORDER, ordered=True)
    pred["fixed_effort_band"] = pd.Categorical(pred["fixed_effort_band"].astype(str), BAND_ORDER, ordered=True)

    slope_rows = []
    fig, axes = plt.subplots(len(CHILD_ORDER), len(BAND_ORDER), figsize=(16, 11), sharex=False, sharey=True)
    for i, child in enumerate(CHILD_ORDER):
        for j, band in enumerate(BAND_ORDER):
            ax = axes[i, j]
            child_obs = obs[obs["child_key"].eq(child) & obs["effort_band"].eq(band)].sort_values("age_months")
            child_pred = pred[pred["child_key"].eq(child) & pred["fixed_effort_band"].eq(band)].sort_values("age_months")
            ax.scatter(child_obs["age_months"], child_obs["actual_sum_bits"], s=32, alpha=0.62, color="#111827", label="actual monthly points")
            actual_fit = line_fit(child_obs["age_months"], child_obs["actual_sum_bits"])
            pred_fit = line_fit(child_pred["age_months"], child_pred["predicted_sum_bits"])
            if actual_fit is not None:
                slope, intercept = actual_fit
                xs = np.linspace(child_obs["age_months"].min(), child_obs["age_months"].max(), 50)
                ax.plot(xs, slope * xs + intercept, color="#111827", lw=2.4, label="actual regression")
            if pred_fit is not None:
                slope_p, intercept_p = pred_fit
                xs = np.linspace(child_pred["age_months"].min(), child_pred["age_months"].max(), 80)
                ax.plot(xs, slope_p * xs + intercept_p, color="#0f766e", lw=2.4, linestyle="--", label="PBM prediction regression")
            slope_rows.append(
                {
                    "child_key": child,
                    "effort_band": band,
                    "actual_slope_bits_per_month": actual_fit[0] if actual_fit else math.nan,
                    "predicted_slope_bits_per_month": pred_fit[0] if pred_fit else math.nan,
                    "actual_month_points": int(len(child_obs)),
                }
            )
            ax.set_title(f"{child}\n{band} words")
            ax.grid(color="#e5e7eb")
            if i == len(CHILD_ORDER) - 1:
                ax.set_xlabel("Age (months)")
            if j == 0:
                ax.set_ylabel("Actual sum_bits")
            if actual_fit and pred_fit:
                ax.text(
                    0.03,
                    0.95,
                    f"actual {actual_fit[0]:+.2f}/mo\npred {pred_fit[0]:+.2f}/mo",
                    transform=ax.transAxes,
                    va="top",
                    fontsize=9,
                    bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#d1d5db", "alpha": 0.9},
                )
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Heldout child regression check: real-data line vs PBM-trained prediction line", y=1.01)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    slope_frame = pd.DataFrame(slope_rows)
    slope_frame.to_csv(output_dir / f"heldout_{model_id.lower()}_actual_vs_predicted_regression_slopes.csv", index=False)
    path = fig_dir / f"heldout_{model_id.lower()}_actual_vs_predicted_regression_lines.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def plot_heldout_calibration(fig_dir: Path, output_dir: Path, *, model_id: str = "POP_M4C") -> Path:
    monthly = pd.read_csv(HELDOUT_DIR / "heldout_prediction_monthly.csv.gz")
    data = monthly[
        monthly["context_k"].eq("k3")
        & monthly["effort_col"].eq("nb_words")
        & monthly["model_id"].eq(model_id)
    ].copy()
    data.to_csv(output_dir / f"heldout_{model_id.lower()}_monthly_calibration.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    sns.scatterplot(
        data=data,
        x="actual_sum_bits",
        y="predicted_sum_bits",
        hue="child_key",
        alpha=0.72,
        s=42,
        ax=axes[0],
    )
    lo = float(np.nanmin([data["actual_sum_bits"].min(), data["predicted_sum_bits"].min()]))
    hi = float(np.nanmax([data["actual_sum_bits"].max(), data["predicted_sum_bits"].max()]))
    axes[0].plot([lo, hi], [lo, hi], color="#111827", lw=1.2, linestyle=":")
    axes[0].set_title("Calibration: actual vs predicted monthly means")
    axes[0].set_xlabel("Actual monthly mean sum_bits")
    axes[0].set_ylabel("Predicted monthly mean sum_bits")
    axes[0].grid(color="#e5e7eb")

    sns.scatterplot(
        data=data,
        x="age_months",
        y="residual",
        hue="child_key",
        alpha=0.72,
        s=42,
        legend=False,
        ax=axes[1],
    )
    axes[1].axhline(0, color="#111827", lw=1.2, linestyle=":")
    for child, group in data.groupby("child_key"):
        fit = line_fit(group["age_months"], group["residual"])
        if fit:
            slope, intercept = fit
            xs = np.linspace(group["age_months"].min(), group["age_months"].max(), 50)
            axes[1].plot(xs, slope * xs + intercept, lw=1.7)
    axes[1].set_title("Residual check: actual minus predicted over age")
    axes[1].set_xlabel("Age (months)")
    axes[1].set_ylabel("Residual sum_bits")
    axes[1].grid(color="#e5e7eb")
    axes[0].legend(title="", fontsize=9)
    plt.tight_layout()
    path = fig_dir / f"heldout_{model_id.lower()}_calibration_residuals.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return path


def compute_predictor_correlations(input_csv: Path, output_dir: Path, fig_dir: Path, chunksize: int) -> tuple[pd.DataFrame, Path]:
    out_csv = output_dir / "pbm_real_k3_predictor_correlations.csv"
    usecols = [
        "role",
        "target_variant",
        "context_k",
        "sum_bits",
        "age_months",
        "nb_words",
        "nb_morphemes",
        "context_entropy_bits",
        "context_entropy_token_count",
        "context_next_top1_prob",
        "context_next_argmax_bits",
    ]
    parts = []
    for chunk in pd.read_csv(input_csv, usecols=usecols, dtype=str, chunksize=chunksize, keep_default_na=False, low_memory=False):
        chunk = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].eq("k3")
        ].copy()
        if chunk.empty:
            continue
        numeric_cols = [col for col in usecols if col not in {"role", "target_variant", "context_k"}]
        for col in numeric_cols:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        parts.append(chunk[numeric_cols])
    if not parts:
        corr = pd.DataFrame()
    else:
        data = pd.concat(parts, ignore_index=True)
        data = data.rename(
            columns={
                "sum_bits": "target information",
                "age_months": "age",
                "nb_words": "child words",
                "nb_morphemes": "child morphemes",
                "context_entropy_bits": "context entropy",
                "context_entropy_token_count": "context token count",
                "context_next_top1_prob": "context top1 prob",
                "context_next_argmax_bits": "context argmax bits",
            }
        )
        corr = data.corr(numeric_only=True, method="pearson")
    corr.to_csv(out_csv)

    fig, ax = plt.subplots(figsize=(10.5, 8.3))
    sns.heatmap(corr, vmin=-1, vmax=1, cmap="vlag", center=0, annot=True, fmt=".2f", square=True, ax=ax)
    ax.set_title("Raw predictor correlations: PBM real child, k3 context")
    plt.tight_layout()
    path = fig_dir / "pbm_real_k3_predictor_correlation_heatmap.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return corr, path


def render_pdf(html_path: Path, pdf_path: Path) -> bool:
    browser = shutil.which("brave-browser") or shutil.which("google-chrome") or "/usr/bin/brave-browser"
    if not Path(browser).exists() and not shutil.which(browser):
        browser = ""
    if not browser:
        return False
    subprocess.run(
        [
            browser,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path.resolve()}",
            f"file://{html_path.resolve()}",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def write_report(
    *,
    doc_path: Path,
    figures: dict[str, Path],
    model_cards_frame: pd.DataFrame,
    importance_table: pd.DataFrame,
    effect_table: pd.DataFrame,
    output_dir: Path,
) -> None:
    real_atlas = Path("docs/utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html")
    tech_companion = Path("docs/utterance_information_m1_m6_technical_implementation_companion.html")
    heldout_report = Path("docs/utterance_information_route1_heldout_real_child_prediction_report.html")
    lines = [
        "# Candidate Supervisor Report v0: Communicative Efficiency in Child Speech",
        "",
        "This is a candidate synthesis, not the final supervisor-facing report. It selects the clearest Route 1 plots, adds heldout regression checks, and states exactly what each line means.",
        "",
        "## One-Sentence Story",
        "",
        "At the same production effort, real children show an age-related change in utterance information that survives child identity and context-form controls, and PBM-trained models can be checked against unseen children with explicit actual-vs-predicted regression lines.",
        "",
        "## Links To The Technical Model Cards",
        "",
        f"- Real-child Atlas v2 model cards for the implemented M1-M15 ladder: [{real_atlas.name}]({relative_to_report(doc_path, real_atlas)})",
        f"- Technical implementation companion for OLS, GLM, GEE, MixedLM, fixed effects, clustered SE, and interaction hierarchy: [{tech_companion.name}]({relative_to_report(doc_path, tech_companion)})",
        f"- Heldout child prediction report used for the new regression checks: [{heldout_report.name}]({relative_to_report(doc_path, heldout_report)})",
        "",
        "**Important naming note.** I found implemented model cards for M1-M15. I do not find a real implemented M16 artifact in the current Atlas v2 ladder, so this candidate report does not pretend M16 exists.",
        "",
        "## 1. The Two Questions From The Email",
        "",
        f"![Route map]({relative_to_report(doc_path, figures['route_map'])})",
        "",
        *figure_guide(
            shows="the split between the current Route 1 evidence and the later Route 2 effort-choice question.",
            read="Route 1 keeps production effort fixed and predicts utterance information; Route 2 makes effort or length the outcome.",
            means="this candidate report can support the information-given-effort claim now, while keeping the stronger context-predictability/effort-choice claim parked for the next analysis.",
            caution="the route map is conceptual; it is not a statistical result.",
        ),
        "- **Route 1:** Given context and fixed production effort, do children change the information content of their utterances over development?",
        "- **Route 2:** Given context, do children modulate production effort itself, for example producing shorter utterances when context is more predictive?",
        "",
        "This candidate report mainly supports Route 1. Route 2 is the next report family once response-space/context-predictability predictors are attached at production scale.",
        "",
        "## 2. The Main Line Meaning",
        "",
        "In the Atlas v2 fixed-effort plots, a line is not a raw average. It is the fitted regression model asking: **what `sum_bits` would we expect at this age if effort is held fixed and the listed controls are included?**",
        "",
        "- **Downward fixed-effort line:** at the same word count, older children are predicted to carry less total information.",
        "- **Upward fixed-effort line:** at the same word count, older children are predicted to carry more total information.",
        "- **Separated low/mid/high effort lines:** longer utterances carry more information, which is why effort must be controlled.",
        "- **Non-parallel effort lines:** the age effect changes depending on effort.",
        "",
        f"![Source comparison]({relative_to_report(doc_path, figures['source_slopes'])})",
        "",
        *figure_guide(
            shows="the fitted age slope for each target source, using the same k3 context window, M4c controls, and word-count effort bands.",
            read="bars left of zero mean predicted `sum_bits` goes down with age at fixed word count; bars right of zero mean it goes up. The three colors are short, medium, and longer utterance bands.",
            means="real child speech has negative fixed-effort slopes, while the random baseline is positive; n-gram and LSTM baselines mostly show negative slopes but with different magnitudes. This makes the real-child pattern visible against matched generated-target controls.",
            caution="these baselines are sanity checks for source specificity and scoring mechanics, not psychological models of children.",
        ),
        "**Clean read:** the real-child fixed-effort slopes are downward in this k3/word M4c view, while the random baseline goes upward. That is a useful sanity check: the developmental line is not just a mechanical consequence of word count or the plotting code.",
        "",
        "## 3. What The Best Controlled Model Is Doing",
        "",
        f"![Model ladder importance]({relative_to_report(doc_path, figures['r2_importance'])})",
        "",
        *figure_guide(
            shows="how much observed-vs-fitted R2 each real-child k3/word model achieves, and how much each model changes R2 relative to M2.",
            read="the left panel is absolute fit; the right panel is the small gain or loss after the primary child-identity-plus-effort model. Taller bars mean better in-sample fit, not causal importance.",
            means="effort and child identity carry the large fit improvement, while question type and richer context controls add smaller but interpretable gains. The age coefficient remains negative in the promoted controlled models.",
            caution="delta-R2 says what improves prediction inside this model family; it does not prove that a predictor causes the information change.",
        ),
        "This plot is a variable-importance view, but not a causal ranking. In Advanced Data Analytics terms, it is a nested-model diagnostic: most variance is explained by effort and child identity; context controls add smaller but interpretable gains.",
        "",
        markdown_table(importance_table, max_rows=12),
        "",
        "### One-Line Effect Cards",
        "",
        markdown_table(effect_table, max_rows=12),
        "",
        "## 4. Heldout Children: Real Regression Line vs Prediction Regression Line",
        "",
        "The plot below is the check you asked for. The black dots are actual heldout child data aggregated to month x effort-band cells. The black line is the regression line fitted to those actual heldout points. The teal dashed line is the regression line implied by the PBM-trained prediction for the same child and effort band.",
        "",
        f"![Heldout regression lines]({relative_to_report(doc_path, figures['heldout_regression'])})",
        "",
        *figure_guide(
            shows="for each heldout child and word-count band, the observed heldout monthly trajectory and the PBM-trained model's predicted trajectory.",
            read="black points are actual heldout child month-by-band means; the black solid line is their fitted actual trend; the teal dashed line is the PBM-trained predicted trend for the same child and effort band.",
            means="the model can be checked visually on children it did not train on. In this current version, predicted slopes are flatter than several actual heldout slopes, so this is a useful diagnostic rather than the cleanest proof.",
            caution="the heldout panels summarize month/effort cells and should not be read as exact utterance-level predictions.",
        ),
        "**Clean read:** this plot makes the generalization claim inspectable. We are no longer asking the reader to infer the regression from a model table; the actual heldout line and predicted line are literally in the same panel.",
        "",
        f"![Heldout calibration]({relative_to_report(doc_path, figures['heldout_calibration'])})",
        "",
        *figure_guide(
            shows="whether PBM-trained monthly predictions match heldout monthly means, and whether prediction errors drift with child age.",
            read="in the calibration panel, points near the diagonal are better calibrated. In the residual panel, points near zero mean the prediction is close; a sloped residual trend means errors change over development.",
            means="this separates level accuracy from developmental-shape accuracy: a model can get average information roughly right while still missing age-related changes.",
            caution="calibration and residual plots diagnose prediction quality; they do not replace the source-specific fixed-effort model evidence.",
        ),
        "**Clean read:** calibration asks whether high-information months are predicted as high-information months. Residual-over-age asks whether the PBM-trained model misses systematically for younger or older heldout sessions.",
        "",
        "## 5. Predictor Relations And Confounds",
        "",
        f"![Predictor correlations]({relative_to_report(doc_path, figures['correlations'])})",
        "",
        *figure_guide(
            shows="raw Pearson correlations among age, information, effort, and context-predictability variables for PBM real-child k3 rows.",
            read="red/blue cells show stronger positive or negative pairwise association before regression controls are applied. Values near zero mean little linear pairwise association.",
            means="the plot explains why controls are needed: effort measures are strongly related to information, and context variables are not independent of the rest of the design.",
            caution="raw correlations are descriptive confound checks, not the final controlled age effect.",
        ),
        "This heatmap is intentionally labeled as raw correlation. It is useful for seeing confounding, not for making the final claim. The controlled regression lines above are the actual scientific test.",
        "",
        "Confounds handled in the current Route 1 candidate:",
        "",
        "- child identity: handled by child fixed effects in Atlas v2 source-specific models;",
        "- repeated utterances within children: primary uncertainty uses child-cluster robust standard errors where available;",
        "- effort/length: held fixed in the plotted fixed-effort lines;",
        "- parent context effort: included in M4a/M5/M6/M15-style controls;",
        "- context predictability: current next-token context entropy is included in M4b/M5/M6/M15; response-space entropy is still Route 2/future-predictor work;",
        "- question/statement type: included in M4c/M5/M12/M13/M15-style controls.",
        "",
        "## 6. Regression Assumption Checks",
        "",
        "- We should not pretend individual utterance rows are independent. The report therefore uses child fixed effects, child-cluster robust uncertainty, and heldout month/effort-bin summaries for visual checks.",
        "- We should not assume one straight line blindly. Atlas v2 includes nonlinear age checks (M7/M8) and categorical age-bin checks (M9/M10). These belong in the technical appendix, while M2/M4c/M15 carry the clean story.",
        "- We should not call raw correlations variable importance. The report separates raw correlations, nested R2 diagnostics, and controlled coefficient directions.",
        "- We should not overclaim Route 2 from Route 1. Context entropy predicting `sum_bits` is not the same as context predictability predicting child length choice.",
        "",
        "## 7. Candidate Model Card Appendix: Implemented M1-M15",
        "",
        markdown_table(model_cards_frame, max_rows=30),
        "",
        "## Saved Candidate Artifacts",
        "",
        "```text",
        str(output_dir / "real_k3_words_model_ladder_importance.csv"),
        str(output_dir / "source_comparison_m4c_k3_words_slopes.csv"),
        str(output_dir / "heldout_pop_m4c_actual_vs_predicted_regression_slopes.csv"),
        str(output_dir / "heldout_pop_m4c_monthly_calibration.csv"),
        str(output_dir / "pbm_real_k3_predictor_correlations.csv"),
        "figs/supervisor_candidate_report/",
        "```",
        "",
    ]
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def run(*, output_dir: Path, fig_dir: Path, doc_dir: Path, chunksize: int) -> dict[str, Path]:
    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)

    summary = read_real_summary()
    cards = model_cards(summary)
    importance = build_importance_table(summary)
    effects = build_effect_sentence_table(summary)
    cards.to_csv(output_dir / "candidate_model_cards_m1_m15.csv", index=False)
    importance.to_csv(output_dir / "candidate_variable_importance_table.csv", index=False)
    effects.to_csv(output_dir / "candidate_effect_sentence_cards.csv", index=False)

    figures = {
        "route_map": plot_route_map(fig_dir),
        "r2_importance": plot_model_ladder_r2(summary, fig_dir, output_dir),
        "source_slopes": plot_source_slope_comparison(fig_dir, output_dir, model_id="M4c"),
        "heldout_regression": plot_heldout_regression_check(fig_dir, output_dir, model_id="POP_M4C"),
        "heldout_calibration": plot_heldout_calibration(fig_dir, output_dir, model_id="POP_M4C"),
    }
    _, corr_path = compute_predictor_correlations(ROUTE1_INPUT, output_dir, fig_dir, chunksize)
    figures["correlations"] = corr_path

    doc_path = doc_dir / f"{DOC_BASENAME}.md"
    html_path = doc_path.with_suffix(".html")
    embedded_path = doc_path.with_suffix(".embedded.html")
    pdf_path = doc_path.with_suffix(".pdf")
    write_report(
        doc_path=doc_path,
        figures=figures,
        model_cards_frame=cards,
        importance_table=importance,
        effect_table=effects,
        output_dir=output_dir,
    )
    render_markdown_file(doc_path, html_path)
    render_markdown_file(doc_path, embedded_path, embed_images=True)
    outputs = {"md": doc_path, "html": html_path, "embedded_html": embedded_path}
    if render_pdf(html_path, pdf_path) and pdf_path.exists():
        outputs["pdf"] = pdf_path
    return outputs


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--chunksize", type=int, default=250_000)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = run(output_dir=args.output_dir, fig_dir=args.fig_dir, doc_dir=args.doc_dir, chunksize=args.chunksize)
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
