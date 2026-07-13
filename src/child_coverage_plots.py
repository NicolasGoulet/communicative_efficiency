"""Plotting functions for child coverage reports."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

DATASET_COLORS = {
    "Belfast": "#4e79a7",
    "Brown": "#f28e2b",
    "Demetras1": "#e15759",
    "Forrester": "#76b7b2",
    "Kuczaj": "#59a14f",
    "Lara": "#edc948",
    "MPI-EVA-Manchester": "#b07aa1",
    "Manchester": "#ff9da7",
    "Post": "#9c755f",
    "Providence": "#bab0ab",
    "Sachs": "#2f6f73",
    "Weist": "#c76f2c",
    "Wells": "#6f4e7c",
}


def plot_vertical(frame: pd.DataFrame, output: Path) -> None:
    colors = frame["dataset"].map(DATASET_COLORS).fillna("#777777")
    fig_width = max(18.0, len(frame) * 0.22)
    fig, ax = plt.subplots(figsize=(fig_width, 7.2))
    ax.bar(
        range(len(frame)),
        frame["child_utterances"],
        color=colors,
        width=0.48,
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_yscale("log")
    ax.set_ylabel("Child utterances, log scale")
    ax.set_xlabel("Individual children, sorted by count")
    ax.set_title("Child utterance counts in the current strict naturalistic bundle")
    ax.set_xticks(range(len(frame)))
    ax.set_xticklabels(frame["child_label"], rotation=90, ha="center", fontsize=6.5)
    ax.grid(axis="y", alpha=0.25)

    handles = []
    labels = []
    for dataset in frame["dataset"].drop_duplicates():
        handles.append(plt.Rectangle((0, 0), 1, 1, color=DATASET_COLORS.get(dataset, "#777777")))
        labels.append(dataset)
    ax.legend(handles, labels, title="Dataset", frameon=False, ncol=4, fontsize=8, title_fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def plot_horizontal(frame: pd.DataFrame, output: Path) -> None:
    colors = frame["dataset"].map(DATASET_COLORS).fillna("#777777")
    height = max(10.0, len(frame) * 0.18)
    fig, ax = plt.subplots(figsize=(12, height))
    ax.barh(
        range(len(frame)),
        frame["child_utterances"],
        color=colors,
        height=0.62,
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_xscale("log")
    ax.set_xlabel("Child utterances, log scale")
    ax.set_ylabel("Individual children, sorted by count")
    ax.set_title("Child utterance counts by child")
    ax.set_yticks(range(len(frame)))
    ax.set_yticklabels(frame["child_label"], fontsize=6.5)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def plot_age_coverage(frame: pd.DataFrame, age_points: pd.DataFrame, output: Path, *, order_by: str) -> None:
    if order_by == "first_age":
        ordered = frame.sort_values(["child_age_min_months", "dataset", "child_id"], ascending=[True, True, True]).copy()
        title = "Age coverage by child, sorted by first observed age"
    elif order_by == "utterance_count":
        ordered = frame.sort_values("child_utterances", ascending=False).copy()
        title = "Age coverage by child, sorted by utterance count"
    else:
        raise ValueError(f"Unknown order_by: {order_by}")

    ordered = ordered.reset_index(drop=True)
    y_lookup = {label: idx for idx, label in enumerate(ordered["child_label"])}
    points = age_points[age_points["child_label"].isin(y_lookup)].copy()
    points["y"] = points["child_label"].map(y_lookup)
    points["size"] = 7 + 22 * (points["n_utterances"].clip(lower=1).pow(0.35) / points["n_utterances"].max() ** 0.35)

    height = max(13.0, len(ordered) * 0.19)
    fig, ax = plt.subplots(figsize=(14, height))

    age_bins = [
        ("006-023", 6, 23),
        ("024-029", 24, 29),
        ("030-035", 30, 35),
        ("036-041", 36, 41),
        ("042-047", 42, 47),
        ("048-053", 48, 53),
        ("054-059", 54, 59),
        ("060-065", 60, 65),
    ]
    for idx, (label, start, end) in enumerate(age_bins):
        ax.axvspan(start, end, color="#f2f5f4" if idx % 2 == 0 else "#ffffff", zorder=0)
        ax.text((start + end) / 2, -2.2, label, ha="center", va="center", fontsize=8, color="#657074")

    for _, row in ordered.iterrows():
        y = y_lookup[row["child_label"]]
        color = DATASET_COLORS.get(row["dataset"], "#777777")
        ax.hlines(
            y=y,
            xmin=row["child_age_min_months"],
            xmax=row["child_age_max_months"],
            color=color,
            linewidth=1.8,
            alpha=0.78,
            zorder=2,
        )

    ax.scatter(
        points["age_months"],
        points["y"],
        s=points["size"],
        c=points["dataset"].map(DATASET_COLORS).fillna("#777777"),
        alpha=0.72,
        edgecolors="white",
        linewidths=0.25,
        zorder=3,
    )
    ax.set_yticks(range(len(ordered)))
    ax.set_yticklabels(ordered["child_label"], fontsize=6.5)
    ax.invert_yaxis()
    ax.set_xlim(6, 65)
    ax.set_xlabel("Child age in months")
    ax.set_ylabel("Individual children")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.28)

    handles = []
    labels = []
    for dataset in ordered["dataset"].drop_duplicates():
        handles.append(plt.Line2D([0], [0], color=DATASET_COLORS.get(dataset, "#777777"), marker="o", lw=2))
        labels.append(dataset)
    ax.legend(handles, labels, title="Dataset", frameon=False, ncol=2, fontsize=8, title_fontsize=9, loc="lower right")
    fig.text(
        0.01,
        0.01,
        "Line = observed age span; dots = observed recording ages; dot size scales with child utterance count at that age.",
        fontsize=8,
        color="#657074",
    )
    fig.tight_layout(rect=[0, 0.02, 1, 0.98])
    fig.savefig(output, dpi=220)
    plt.close(fig)
