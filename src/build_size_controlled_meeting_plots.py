#!/usr/bin/env python3
"""Build compact size-controlled trajectory plots for meeting review.

The figures here are intentionally separate from the supervisor-facing report.
They answer a narrow diagnostic question: how do developmental trajectories look
when utterances are stratified by word-count range and normalized by a named
effort unit?
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/meeting_size_controlled_plots")
DEFAULT_FIG_DIR = Path("figs/meeting_size_controlled_plots")
DEFAULT_DOC_MD = Path("docs/meeting_size_controlled_information_plots.md")
DEFAULT_DOC_HTML = Path("docs/meeting_size_controlled_information_plots.html")

AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
SIZE_BIN_ORDER = ["1-4 words", "5-8 words"]
EXACT_EFFORT_RANGES = [(range(1, 5), "1_4", "1-4"), (range(5, 9), "5_8", "5-8")]
METRICS = [
    ("nb_words", "bits_per_word", "Words", "Bits per word"),
    ("nb_morphemes", "bits_per_morpheme", "Morphemes", "Bits per morpheme"),
    ("nb_syllables_cmu_or_pkg", "bits_per_syllable_cmu_or_pkg", "Syllables (CMU/pkg)", "Bits per syllable (CMU/pkg)"),
    ("nb_syllables_pkg", "bits_per_syllable_pkg", "Syllables (pkg)", "Bits per syllable (pkg)"),
    ("nb_phonemes", "bits_per_phoneme", "Phonemes", "Bits per phoneme"),
]
USECOLS = [
    "score_id",
    "age_bin",
    "role",
    "target_variant",
    "context_k",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
]


def word_size_bin(nb_words: object) -> str | None:
    """Map an utterance word count to the meeting-requested size stratum."""

    try:
        value = int(float(nb_words))
    except (TypeError, ValueError):
        return None
    if 1 <= value <= 4:
        return "1-4 words"
    if 5 <= value <= 8:
        return "5-8 words"
    return None


def sem(values: pd.Series) -> float:
    """Standard error of the mean with finite-value protection."""

    clean = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if clean.shape[0] <= 1:
        return math.nan
    return float(clean.std(ddof=1) / math.sqrt(clean.shape[0]))


def summarize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize finite metric values by age, comparison group, and size bin."""

    summaries: list[pd.DataFrame] = []
    group_cols = ["comparison", "age_bin", "size_bin"]
    for _, metric, _, metric_label in METRICS:
        metric_frame = frame.dropna(subset=[metric]).copy()
        metric_frame[metric] = pd.to_numeric(metric_frame[metric], errors="coerce")
        metric_frame = metric_frame[np.isfinite(metric_frame[metric])]
        if metric_frame.empty:
            continue
        summary = (
            metric_frame.groupby(group_cols, observed=True)[metric]
            .agg(mean="mean", sem=sem, n_rows="count")
            .reset_index()
        )
        summary["metric"] = metric
        summary["metric_label"] = metric_label
        summaries.append(summary)
    if not summaries:
        return pd.DataFrame(columns=group_cols + ["mean", "sem", "n_rows", "metric", "metric_label"])
    out = pd.concat(summaries, ignore_index=True)
    out["age_bin"] = pd.Categorical(out["age_bin"], AGE_BIN_ORDER, ordered=True)
    out["size_bin"] = pd.Categorical(out["size_bin"], SIZE_BIN_ORDER, ordered=True)
    return out.sort_values(["metric", "comparison", "size_bin", "age_bin"]).reset_index(drop=True)


def summarize_exact_effort_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize trajectories at exact effort values 1 through 8."""

    summaries: list[pd.DataFrame] = []
    group_cols = ["comparison", "age_bin", "effort_value"]
    for effort_col, metric, effort_label, metric_label in METRICS:
        metric_frame = frame.dropna(subset=[metric, effort_col]).copy()
        metric_frame[metric] = pd.to_numeric(metric_frame[metric], errors="coerce")
        metric_frame[effort_col] = pd.to_numeric(metric_frame[effort_col], errors="coerce")
        metric_frame = metric_frame[
            np.isfinite(metric_frame[metric])
            & np.isfinite(metric_frame[effort_col])
            & metric_frame[effort_col].between(1, 8)
            & metric_frame[effort_col].mod(1).eq(0)
        ].copy()
        if metric_frame.empty:
            continue
        metric_frame["effort_value"] = metric_frame[effort_col].astype(int)
        summary = (
            metric_frame.groupby(group_cols, observed=True)[metric]
            .agg(mean="mean", sem=sem, n_rows="count")
            .reset_index()
        )
        summary["effort_col"] = effort_col
        summary["effort_label"] = effort_label
        summary["metric"] = metric
        summary["metric_label"] = metric_label
        summaries.append(summary)
    if not summaries:
        return pd.DataFrame(
            columns=group_cols + ["mean", "sem", "n_rows", "effort_col", "effort_label", "metric", "metric_label"]
        )
    out = pd.concat(summaries, ignore_index=True)
    out["age_bin"] = pd.Categorical(out["age_bin"], AGE_BIN_ORDER, ordered=True)
    return out.sort_values(["effort_col", "comparison", "effort_value", "age_bin"]).reset_index(drop=True)


def comparison_frames(chunk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return child baseline and child/caretaker comparison frames from a chunk."""

    chunk = chunk.copy()
    chunk["nb_words"] = pd.to_numeric(chunk["nb_words"], errors="coerce")
    chunk["size_bin"] = chunk["nb_words"].map(word_size_bin)
    chunk = chunk[chunk["size_bin"].notna() & chunk["age_bin"].isin(AGE_BIN_ORDER) & chunk["context_k"].eq("k3")].copy()

    child_baseline = chunk[
        chunk["role"].eq("child") & chunk["target_variant"].isin(["real", "random", "trigram"])
    ].copy()
    child_baseline["comparison"] = child_baseline["target_variant"].map(
        {"real": "Real child", "random": "Random", "trigram": "Trigram"}
    )

    speaker = chunk[
        (chunk["role"].eq("child") & chunk["target_variant"].eq("real"))
        | (chunk["role"].eq("caretaker") & chunk["target_variant"].eq("caretaker"))
    ].copy()
    speaker["comparison"] = speaker["role"].map({"child": "Child", "caretaker": "Caretaker"})

    return child_baseline, speaker


def read_and_summarize(input_csv: Path, *, chunksize: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the long scored table in chunks and return the requested summaries."""

    baseline_parts: list[pd.DataFrame] = []
    speaker_parts: list[pd.DataFrame] = []
    exact_baseline_parts: list[pd.DataFrame] = []
    exact_speaker_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        baseline, speaker = comparison_frames(chunk)
        if not baseline.empty:
            baseline_parts.append(summarize_frame(baseline))
            exact_baseline_parts.append(summarize_exact_effort_frame(baseline))
        if not speaker.empty:
            speaker_parts.append(summarize_frame(speaker))
            exact_speaker_parts.append(summarize_exact_effort_frame(speaker))

    baseline_summary = combine_chunk_summaries(baseline_parts)
    speaker_summary = combine_chunk_summaries(speaker_parts)
    exact_baseline_summary = combine_exact_chunk_summaries(exact_baseline_parts)
    exact_speaker_summary = combine_exact_chunk_summaries(exact_speaker_parts)
    return baseline_summary, speaker_summary, exact_baseline_summary, exact_speaker_summary


def combine_chunk_summaries(parts: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Combine per-chunk means into exact weighted means and pooled SEMs."""

    frames = [part for part in parts if not part.empty]
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    raw["sum_x"] = raw["mean"] * raw["n_rows"]
    # From each chunk summary: sd^2 = sem^2 * n. Reconstruct the chunk sum
    # of squares so pooled confidence intervals remain valid across chunks.
    chunk_variance = raw["sem"].fillna(0) ** 2 * raw["n_rows"]
    raw["sum_x2"] = (raw["n_rows"] - 1).clip(lower=0) * chunk_variance + raw["n_rows"] * raw["mean"] ** 2
    group_cols = ["metric", "metric_label", "comparison", "age_bin", "size_bin"]
    combined = raw.groupby(group_cols, observed=True).agg(
        n_rows=("n_rows", "sum"),
        sum_x=("sum_x", "sum"),
        sum_x2=("sum_x2", "sum"),
    ).reset_index()
    combined["mean"] = combined["sum_x"] / combined["n_rows"]
    variance = (combined["sum_x2"] - (combined["sum_x"] ** 2 / combined["n_rows"])) / (combined["n_rows"] - 1)
    combined["sem"] = np.sqrt(np.maximum(variance, 0)) / np.sqrt(combined["n_rows"])
    combined.loc[combined["n_rows"].le(1), "sem"] = np.nan
    combined["age_bin"] = pd.Categorical(combined["age_bin"], AGE_BIN_ORDER, ordered=True)
    combined["size_bin"] = pd.Categorical(combined["size_bin"], SIZE_BIN_ORDER, ordered=True)
    return combined.sort_values(group_cols).reset_index(drop=True)


def combine_exact_chunk_summaries(parts: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Combine per-chunk exact-effort summaries into pooled means and SEMs."""

    frames = [part for part in parts if not part.empty]
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    raw["sum_x"] = raw["mean"] * raw["n_rows"]
    chunk_variance = raw["sem"].fillna(0) ** 2 * raw["n_rows"]
    raw["sum_x2"] = (raw["n_rows"] - 1).clip(lower=0) * chunk_variance + raw["n_rows"] * raw["mean"] ** 2
    group_cols = ["effort_col", "effort_label", "metric", "metric_label", "comparison", "age_bin", "effort_value"]
    combined = raw.groupby(group_cols, observed=True).agg(
        n_rows=("n_rows", "sum"),
        sum_x=("sum_x", "sum"),
        sum_x2=("sum_x2", "sum"),
    ).reset_index()
    combined["mean"] = combined["sum_x"] / combined["n_rows"]
    variance = (combined["sum_x2"] - (combined["sum_x"] ** 2 / combined["n_rows"])) / (combined["n_rows"] - 1)
    combined["sem"] = np.sqrt(np.maximum(variance, 0)) / np.sqrt(combined["n_rows"])
    combined.loc[combined["n_rows"].le(1), "sem"] = np.nan
    combined["age_bin"] = pd.Categorical(combined["age_bin"], AGE_BIN_ORDER, ordered=True)
    return combined.sort_values(group_cols).reset_index(drop=True)


def plot_metric(summary: pd.DataFrame, *, metric: str, title: str, ylabel: str, palette: dict[str, str], path_prefix: Path) -> None:
    """Plot one metric with separate panels for the two word-count strata."""

    sub = summary[summary["metric"].eq(metric)].copy()
    if sub.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5), sharey=True)
    for ax, size_bin in zip(axes, SIZE_BIN_ORDER):
        panel = sub[sub["size_bin"].astype(str).eq(size_bin)].copy()
        for comparison, group in panel.groupby("comparison", observed=True):
            group = group.sort_values("age_bin")
            x = [AGE_BIN_ORDER.index(str(value)) for value in group["age_bin"]]
            low = group["mean"] - 1.96 * group["sem"].fillna(0)
            high = group["mean"] + 1.96 * group["sem"].fillna(0)
            ax.plot(x, group["mean"], marker="o", linewidth=2.2, label=str(comparison), color=palette.get(str(comparison)))
            ax.fill_between(x, low, high, alpha=0.12, color=palette.get(str(comparison)))
        ax.set_title(size_bin)
        ax.set_xticks(range(len(AGE_BIN_ORDER)))
        ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
        ax.set_xlabel("Age bin")
        ax.grid(alpha=0.22)
    axes[0].set_ylabel(ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=max(1, len(labels)), frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(title, y=1.08, fontsize=14)
    fig.tight_layout()
    fig.savefig(path_prefix.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(path_prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_all_metrics(summary: pd.DataFrame, *, title: str, palette: dict[str, str], path_prefix: Path) -> None:
    """Plot all effort-normalized metrics in one compact review grid."""

    fig, axes = plt.subplots(len(METRICS), 2, figsize=(12.0, 16.0), sharex=True)
    for row, (_, metric, _, metric_label) in enumerate(METRICS):
        sub = summary[summary["metric"].eq(metric)].copy()
        for col, size_bin in enumerate(SIZE_BIN_ORDER):
            ax = axes[row, col]
            panel = sub[sub["size_bin"].astype(str).eq(size_bin)].copy()
            for comparison, group in panel.groupby("comparison", observed=True):
                group = group.sort_values("age_bin")
                x = [AGE_BIN_ORDER.index(str(value)) for value in group["age_bin"]]
                low = group["mean"] - 1.96 * group["sem"].fillna(0)
                high = group["mean"] + 1.96 * group["sem"].fillna(0)
                ax.plot(x, group["mean"], marker="o", linewidth=1.9, label=str(comparison), color=palette.get(str(comparison)))
                ax.fill_between(x, low, high, alpha=0.10, color=palette.get(str(comparison)))
            if row == 0:
                ax.set_title(size_bin)
            if col == 0:
                ax.set_ylabel(metric_label)
            ax.grid(alpha=0.20)
    for ax in axes[-1, :]:
        ax.set_xticks(range(len(AGE_BIN_ORDER)))
        ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
        ax.set_xlabel("Age bin")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=max(1, len(labels)), frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.suptitle(title, y=1.02, fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(path_prefix.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(path_prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_exact_effort_grid(summary: pd.DataFrame, *, effort_col: str, title: str, palette: dict[str, str], path_prefix: Path) -> None:
    """Plot age trajectories in panels where every utterance has exactly N effort units."""

    sub = summary[summary["effort_col"].eq(effort_col)].copy()
    if sub.empty:
        return
    metric_label = str(sub["metric_label"].iloc[0])
    effort_label = str(sub["effort_label"].iloc[0])
    fig, axes = plt.subplots(4, 2, figsize=(12.2, 14.0), sharex=True, sharey=True)
    axes_flat = axes.ravel()
    for idx, effort_value in enumerate(range(1, 9)):
        ax = axes_flat[idx]
        panel = sub[sub["effort_value"].eq(effort_value)].copy()
        for comparison, group in panel.groupby("comparison", observed=True):
            group = group.sort_values("age_bin")
            x = [AGE_BIN_ORDER.index(str(value)) for value in group["age_bin"]]
            low = group["mean"] - 1.96 * group["sem"].fillna(0)
            high = group["mean"] + 1.96 * group["sem"].fillna(0)
            ax.plot(x, group["mean"], marker="o", linewidth=1.9, label=str(comparison), color=palette.get(str(comparison)))
            ax.fill_between(x, low, high, alpha=0.10, color=palette.get(str(comparison)))
        unit = effort_label[:-1].lower() if effort_value == 1 and effort_label.endswith("s") else effort_label.lower()
        ax.set_title(f"Exactly {effort_value} {unit}")
        ax.grid(alpha=0.20)
        if idx % 2 == 0:
            ax.set_ylabel(metric_label)
        if idx >= 6:
            ax.set_xticks(range(len(AGE_BIN_ORDER)))
            ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
            ax.set_xlabel("Age bin")
    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=max(1, len(labels)), frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.suptitle(title, y=1.02, fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(path_prefix.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(path_prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_exact_effort_range_grid(
    summary: pd.DataFrame,
    *,
    effort_col: str,
    effort_values: range,
    title: str,
    palette: dict[str, str],
    path_prefix: Path,
) -> None:
    """Plot one 2x2 grid for a small exact-effort range."""

    sub = summary[summary["effort_col"].eq(effort_col)].copy()
    if sub.empty:
        return
    metric_label = str(sub["metric_label"].iloc[0])
    effort_label = str(sub["effort_label"].iloc[0])
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 7.2), sharex=True, sharey=True)
    axes_flat = axes.ravel()
    for idx, effort_value in enumerate(effort_values):
        ax = axes_flat[idx]
        panel = sub[sub["effort_value"].eq(effort_value)].copy()
        for comparison, group in panel.groupby("comparison", observed=True):
            group = group.sort_values("age_bin")
            x = [AGE_BIN_ORDER.index(str(value)) for value in group["age_bin"]]
            ax.plot(x, group["mean"], marker="o", linewidth=2.1, label=str(comparison), color=palette.get(str(comparison)))
        unit = effort_label[:-1].lower() if effort_value == 1 and effort_label.endswith("s") else effort_label.lower()
        ax.set_title(f"Exactly {effort_value} {unit}")
        ax.grid(alpha=0.20)
        if idx % 2 == 0:
            ax.set_ylabel(metric_label)
        if idx >= 2:
            ax.set_xticks(range(len(AGE_BIN_ORDER)))
            ax.set_xticklabels(AGE_BIN_ORDER, rotation=35, ha="right")
            ax.set_xlabel("Age bin")
    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=max(1, len(labels)), frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.suptitle(title, y=1.03, fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(path_prefix.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(path_prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_exact_effort_results(
    baseline_summary: pd.DataFrame,
    speaker_summary: pd.DataFrame,
    *,
    fig_dir: Path,
    baseline_palette: dict[str, str],
    speaker_palette: dict[str, str],
) -> None:
    """Write exact-effort trajectory grids for all effort measures."""

    for effort_col, _, effort_label, metric_label in METRICS:
        suffix = effort_col.replace("nb_", "")
        plot_exact_effort_grid(
            baseline_summary,
            effort_col=effort_col,
            title=f"Exact {effort_label}: Child Real vs Random vs Trigram",
            palette=baseline_palette,
            path_prefix=fig_dir / f"exact_{suffix}_child_real_random_trigram",
        )
        plot_exact_effort_grid(
            speaker_summary,
            effort_col=effort_col,
            title=f"Exact {effort_label}: Child vs Caretaker",
            palette=speaker_palette,
            path_prefix=fig_dir / f"exact_{suffix}_child_vs_caretaker",
        )
        for effort_values, range_slug, range_label in EXACT_EFFORT_RANGES:
            plot_exact_effort_range_grid(
                baseline_summary,
                effort_col=effort_col,
                effort_values=effort_values,
                title=f"Exact {range_label} {effort_label}: Child Real vs Random vs Trigram",
                palette=baseline_palette,
                path_prefix=fig_dir / f"exact_{suffix}_{range_slug}_child_real_random_trigram",
            )
            plot_exact_effort_range_grid(
                speaker_summary,
                effort_col=effort_col,
                effort_values=effort_values,
                title=f"Exact {range_label} {effort_label}: Child vs Caretaker",
                palette=speaker_palette,
                path_prefix=fig_dir / f"exact_{suffix}_{range_slug}_child_vs_caretaker",
            )


def build_split_exact_plots_from_summary_files(output_dir: Path, fig_dir: Path) -> None:
    """Create split 1-4 and 5-8 exact-effort plots from existing summaries."""

    baseline_summary = pd.read_csv(output_dir / "child_real_random_trigram_exact_effort_summary.csv")
    speaker_summary = pd.read_csv(output_dir / "child_vs_caretaker_exact_effort_summary.csv")
    baseline_palette = {"Real child": "#1f5a5f", "Random": "#b9473f", "Trigram": "#5f7f3a"}
    speaker_palette = {"Child": "#1f5a5f", "Caretaker": "#8a5a9e"}
    plot_exact_effort_results(
        baseline_summary,
        speaker_summary,
        fig_dir=fig_dir,
        baseline_palette=baseline_palette,
        speaker_palette=speaker_palette,
    )


def write_report(doc_md: Path, *, fig_dir: Path) -> None:
    """Write a tiny review page pointing to the new figures."""

    doc_md.parent.mkdir(parents=True, exist_ok=True)
    relative_fig = Path("..") / fig_dir
    doc_md.write_text(
        "\n".join(
            [
                "# Size-Controlled Information Trajectories",
                "",
                "These plots are intentionally separate from the main report. They are quick meeting figures for checking whether developmental trends remain visible when utterances are restricted to the same exact or coarse effort range.",
                "",
                "Interpretation note: the exact-effort plots are the safest descriptive figures here. Each panel only includes utterances with exactly the displayed number of words, morphemes, syllables, or phonemes. The coarse `1-4` and `5-8` plots are only diagnostics.",
                "",
                "## Exact-Effort Plots",
                "",
                "These are the plots to use when making a simple size-control claim. Each panel fixes the effort count exactly.",
                "",
                "### Exact Words",
                "",
                f"![Exact 1-4 words: child real/random/trigram]({relative_fig / 'exact_words_1_4_child_real_random_trigram.png'})",
                "",
                f"![Exact 5-8 words: child real/random/trigram]({relative_fig / 'exact_words_5_8_child_real_random_trigram.png'})",
                "",
                f"![Exact 1-4 words: child/caretaker]({relative_fig / 'exact_words_1_4_child_vs_caretaker.png'})",
                "",
                f"![Exact 5-8 words: child/caretaker]({relative_fig / 'exact_words_5_8_child_vs_caretaker.png'})",
                "",
                "### Exact Morphemes",
                "",
                f"![Exact 1-4 morphemes: child real/random/trigram]({relative_fig / 'exact_morphemes_1_4_child_real_random_trigram.png'})",
                "",
                f"![Exact 5-8 morphemes: child real/random/trigram]({relative_fig / 'exact_morphemes_5_8_child_real_random_trigram.png'})",
                "",
                "### Exact Syllables",
                "",
                f"![Exact 1-4 syllables CMU/pkg: child real/random/trigram]({relative_fig / 'exact_syllables_cmu_or_pkg_1_4_child_real_random_trigram.png'})",
                "",
                f"![Exact 5-8 syllables CMU/pkg: child real/random/trigram]({relative_fig / 'exact_syllables_cmu_or_pkg_5_8_child_real_random_trigram.png'})",
                "",
                f"![Exact 1-4 syllables pkg: child real/random/trigram]({relative_fig / 'exact_syllables_pkg_1_4_child_real_random_trigram.png'})",
                "",
                f"![Exact 5-8 syllables pkg: child real/random/trigram]({relative_fig / 'exact_syllables_pkg_5_8_child_real_random_trigram.png'})",
                "",
                "### Exact Phonemes",
                "",
                f"![Exact 1-4 phonemes: child real/random/trigram]({relative_fig / 'exact_phonemes_1_4_child_real_random_trigram.png'})",
                "",
                f"![Exact 5-8 phonemes: child real/random/trigram]({relative_fig / 'exact_phonemes_5_8_child_real_random_trigram.png'})",
                "",
                f"![Exact words: child real/random/trigram]({relative_fig / 'exact_words_child_real_random_trigram.png'})",
                "",
                f"![Exact words: child/caretaker]({relative_fig / 'exact_words_child_vs_caretaker.png'})",
                "",
                f"![Exact morphemes: child real/random/trigram]({relative_fig / 'exact_morphemes_child_real_random_trigram.png'})",
                "",
                f"![Exact syllables CMU/pkg: child real/random/trigram]({relative_fig / 'exact_syllables_cmu_or_pkg_child_real_random_trigram.png'})",
                "",
                f"![Exact phonemes: child real/random/trigram]({relative_fig / 'exact_phonemes_child_real_random_trigram.png'})",
                "",
                "## Coarse Word-Stratified Diagnostics",
                "",
                f"![Child real/random/trigram bits per word]({relative_fig / 'child_real_random_trigram_bits_per_word_by_size.png'})",
                "",
                f"![Child real/random/trigram all effort controls]({relative_fig / 'child_real_random_trigram_all_effort_controls.png'})",
                "",
                "## Child vs Caretaker",
                "",
                f"![Child/caretaker bits per word]({relative_fig / 'child_vs_caretaker_bits_per_word_by_size.png'})",
                "",
                f"![Child/caretaker all effort controls]({relative_fig / 'child_vs_caretaker_all_effort_controls.png'})",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_plots(input_csv: Path, output_dir: Path, fig_dir: Path, doc_md: Path, doc_html: Path, *, chunksize: int) -> None:
    """Build all meeting plots and summaries."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    baseline_summary, speaker_summary, exact_baseline_summary, exact_speaker_summary = read_and_summarize(input_csv, chunksize=chunksize)
    baseline_summary.to_csv(output_dir / "child_real_random_trigram_size_controlled_summary.csv", index=False)
    speaker_summary.to_csv(output_dir / "child_vs_caretaker_size_controlled_summary.csv", index=False)
    exact_baseline_summary.to_csv(output_dir / "child_real_random_trigram_exact_effort_summary.csv", index=False)
    exact_speaker_summary.to_csv(output_dir / "child_vs_caretaker_exact_effort_summary.csv", index=False)

    baseline_palette = {"Real child": "#1f5a5f", "Random": "#b9473f", "Trigram": "#5f7f3a"}
    speaker_palette = {"Child": "#1f5a5f", "Caretaker": "#8a5a9e"}
    for _, metric, _, metric_label in METRICS:
        slug = metric
        plot_metric(
            baseline_summary,
            metric=metric,
            title=f"Child Real vs Random vs Trigram: {metric_label}",
            ylabel=metric_label,
            palette=baseline_palette,
            path_prefix=fig_dir / f"child_real_random_trigram_{slug}_by_size",
        )
        plot_metric(
            speaker_summary,
            metric=metric,
            title=f"Child vs Caretaker: {metric_label}",
            ylabel=metric_label,
            palette=speaker_palette,
            path_prefix=fig_dir / f"child_vs_caretaker_{slug}_by_size",
        )

    plot_all_metrics(
        baseline_summary,
        title="Child Real vs Random vs Trigram: Size-Stratified Per-Unit Information",
        palette=baseline_palette,
        path_prefix=fig_dir / "child_real_random_trigram_all_effort_controls",
    )
    plot_all_metrics(
        speaker_summary,
        title="Child vs Caretaker: Size-Stratified Per-Unit Information",
        palette=speaker_palette,
        path_prefix=fig_dir / "child_vs_caretaker_all_effort_controls",
    )
    plot_exact_effort_results(
        exact_baseline_summary,
        exact_speaker_summary,
        fig_dir=fig_dir,
        baseline_palette=baseline_palette,
        speaker_palette=speaker_palette,
    )

    write_report(doc_md, fig_dir=fig_dir)
    render_markdown_file(doc_md, doc_html)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--chunksize", type=int, default=500_000)
    args = parser.parse_args()
    build_plots(
        input_csv=args.input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        doc_md=args.doc_md,
        doc_html=args.doc_html,
        chunksize=args.chunksize,
    )


if __name__ == "__main__":
    main()
