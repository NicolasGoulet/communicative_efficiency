#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
plot_distributions.py
=====================

Create distribution plots for cleaned child utterances.

Main outputs:

  figs/utterance_distributions/
  ├── Brown/
  ├── Manchester/
  ├── Providence/
  └── ALL_DATASETS/

Each folder contains:
  - metric distributions for sizes 1..8
  - count CSVs
  - dataset/global overview CSVs
  - age-bin plots when age_months is available

Usage from project root:

  uv run python src/plot_distributions.py

Optional examples:

  uv run python src/plot_distributions.py --age_bin_months 6

  uv run python src/plot_distributions.py --age_bin_months 12

  uv run python src/plot_distributions.py --max_size 12
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------

DEFAULT_DATASETS = ["Brown", "Manchester", "Providence"]

DEFAULT_METRICS = [
    "word_count",
    "morph_count",
    "utt_syllables_basic",
    "utt_syllables_lenient",
    "utt_syllables_strictY",
    "utt_syllables_le",
    "n_alpha_words",
]

# Your actual files are chi.csv.
# Enriched versions are listed first in case you later create them.
CSV_CANDIDATES = [
    "chi.random_unigram_bigram.csv",
    "chi.random_and_unigram.csv",
    "chi.random.csv",
    "chi.csv",
    "child_utts.random_unigram_bigram.csv",
    "child_utts.random_and_unigram.csv",
    "child_utts.random.csv",
    "child_utts.csv",
]


# ---------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------

def find_child_csv(child_dir: Path) -> Optional[Path]:
    """
    Find the best child utterance CSV for one child folder.
    """
    for name in CSV_CANDIDATES:
        p = child_dir / name
        if p.exists():
            return p

    return None


def discover_files(data_root: Path, datasets: List[str]) -> List[Tuple[str, str, Path]]:
    """
    Return a list of:

      (dataset_name, child_name, csv_path)
    """
    found: List[Tuple[str, str, Path]] = []

    for dataset in datasets:
        dataset_dir = data_root / dataset

        if not dataset_dir.exists():
            print(f"[WARN] Dataset folder not found: {dataset_dir}")
            continue

        for child_dir in sorted(dataset_dir.iterdir()):
            if not child_dir.is_dir():
                continue

            csv_path = find_child_csv(child_dir)

            if csv_path is None:
                print(f"[WARN] No chi/child utterance CSV found in: {child_dir}")
                continue

            found.append((dataset, child_dir.name, csv_path))

    return found


# ---------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------

def load_all(files: List[Tuple[str, str, Path]]) -> pd.DataFrame:
    """
    Load all discovered child CSVs into one dataframe.

    Adds:
      - dataset
      - child
      - child_label
      - source_file
    """
    dfs = []

    for dataset, child, csv_path in files:
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"[WARN] Could not read {csv_path}: {e}")
            continue

        df["dataset"] = dataset
        df["child"] = child
        df["child_label"] = f"{dataset}/{child}"
        df["source_file"] = str(csv_path)

        dfs.append(df)

        print(f"[OK] Loaded {dataset}/{child}: {len(df):,} rows from {csv_path.name}")

    if not dfs:
        raise RuntimeError("No usable CSV files were loaded.")

    return pd.concat(dfs, ignore_index=True)


def filter_clean_utterances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows with a non-empty utterance_clean column.

    If utterance_clean does not exist, keep all rows but warn.
    """
    if "utterance_clean" not in df.columns:
        print("[WARN] Column 'utterance_clean' not found. Keeping all rows.")
        return df.copy()

    out = df.copy()
    out["utterance_clean"] = out["utterance_clean"].fillna("").astype(str)
    out = out[out["utterance_clean"].str.strip() != ""].copy()

    return out


def add_derived_lengths(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a derived token count from utterance_clean.

    This helps sanity-check word_count.
    """
    out = df.copy()

    if "utterance_clean" in out.columns:
        out["utterance_clean_token_count"] = (
            out["utterance_clean"]
            .fillna("")
            .astype(str)
            .str.split()
            .apply(len)
        )

    return out


# ---------------------------------------------------------------------
# Age bins
# ---------------------------------------------------------------------

def make_age_bin_label(age_months: float, bin_months: int) -> Optional[str]:
    """
    Convert an age in months to a label like:

      012-017
      018-023

    for bin_months = 6.
    """
    if age_months is None or pd.isna(age_months):
        return None

    if bin_months <= 0:
        raise ValueError("bin_months must be positive.")

    start = int(math.floor(float(age_months) / bin_months) * bin_months)
    end = start + bin_months - 1

    return f"{start:03d}-{end:03d}"


def add_age_bins(df: pd.DataFrame, age_bin_months: int) -> pd.DataFrame:
    """
    Add age_bin column based on age_months.
    """
    out = df.copy()

    if "age_months" not in out.columns:
        print("[WARN] age_months not found. Age-bin plots will be skipped.")
        return out

    out["age_months"] = pd.to_numeric(out["age_months"], errors="coerce")
    age_col = f"age_bin_{age_bin_months}m"

    out[age_col] = out["age_months"].apply(
        lambda x: make_age_bin_label(x, age_bin_months)
    )

    return out


# ---------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------

def make_dataset_overview(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic summary table by dataset and child.
    """
    rows = []

    for (dataset, child), g in df.groupby(["dataset", "child"], dropna=False):
        row = {
            "dataset": dataset,
            "child": child,
            "n_rows": len(g),
        }

        if "utterance_clean" in g.columns:
            row["n_nonempty_utterance_clean"] = (
                g["utterance_clean"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        if "age_months" in g.columns:
            age = pd.to_numeric(g["age_months"], errors="coerce")
            row["min_age_months"] = age.min()
            row["max_age_months"] = age.max()
            row["mean_age_months"] = age.mean()

        for metric in DEFAULT_METRICS + ["utterance_clean_token_count"]:
            if metric in g.columns:
                values = pd.to_numeric(g[metric], errors="coerce")
                row[f"{metric}_nonmissing"] = values.notna().sum()
                row[f"{metric}_mean"] = values.mean()
                row[f"{metric}_min"] = values.min()
                row[f"{metric}_max"] = values.max()

        rows.append(row)

    return pd.DataFrame(rows)


def make_global_overview(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-row global summary across all datasets and children.
    """
    row = {
        "n_rows": len(df),
        "n_datasets": df["dataset"].nunique() if "dataset" in df.columns else None,
        "n_children": df["child_label"].nunique() if "child_label" in df.columns else None,
    }

    if "utterance_clean" in df.columns:
        row["n_nonempty_utterance_clean"] = (
            df["utterance_clean"]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
            .sum()
        )

    if "age_months" in df.columns:
        age = pd.to_numeric(df["age_months"], errors="coerce")
        row["min_age_months"] = age.min()
        row["max_age_months"] = age.max()
        row["mean_age_months"] = age.mean()

    for metric in DEFAULT_METRICS + ["utterance_clean_token_count"]:
        if metric in df.columns:
            values = pd.to_numeric(df[metric], errors="coerce")
            row[f"{metric}_nonmissing"] = values.notna().sum()
            row[f"{metric}_mean"] = values.mean()
            row[f"{metric}_min"] = values.min()
            row[f"{metric}_max"] = values.max()

    return pd.DataFrame([row])


def metric_size_counts(
    df: pd.DataFrame,
    metric: str,
    min_size: int,
    max_size: int,
    group_col: str = "child_label",
) -> pd.DataFrame:
    """
    Count utterances by metric size, from min_size to max_size.

    Returns:
      size, all_utterances, one column per group
    """
    if metric not in df.columns:
        raise ValueError(f"Metric not found: {metric}")

    tmp_cols = [metric]
    if group_col in df.columns:
        tmp_cols.append(group_col)

    tmp = df[tmp_cols].copy()
    tmp[metric] = pd.to_numeric(tmp[metric], errors="coerce")
    tmp = tmp[tmp[metric].notna()].copy()

    tmp[metric] = tmp[metric].round().astype(int)

    sizes = list(range(min_size, max_size + 1))
    out = pd.DataFrame({"size": sizes})

    all_counts = tmp[metric].value_counts().reindex(sizes, fill_value=0)
    out["all_utterances"] = out["size"].map(all_counts).fillna(0).astype(int)

    if group_col in tmp.columns:
        for group in sorted(tmp[group_col].dropna().unique()):
            group_counts = (
                tmp.loc[tmp[group_col] == group, metric]
                .value_counts()
                .reindex(sizes, fill_value=0)
            )
            out[group] = out["size"].map(group_counts).fillna(0).astype(int)

    return out


def metric_size_counts_by_age_bin(
    df: pd.DataFrame,
    metric: str,
    age_bin_col: str,
    min_size: int,
    max_size: int,
) -> pd.DataFrame:
    """
    Count utterances by metric size and age bin.

    Returns:
      size, one column per age bin
    """
    if metric not in df.columns:
        raise ValueError(f"Metric not found: {metric}")

    if age_bin_col not in df.columns:
        raise ValueError(f"Age-bin column not found: {age_bin_col}")

    tmp = df[[metric, age_bin_col]].copy()
    tmp[metric] = pd.to_numeric(tmp[metric], errors="coerce")
    tmp = tmp[tmp[metric].notna()].copy()
    tmp = tmp[tmp[age_bin_col].notna()].copy()

    tmp[metric] = tmp[metric].round().astype(int)

    tmp = tmp[(tmp[metric] >= min_size) & (tmp[metric] <= max_size)]

    if tmp.empty:
        return pd.DataFrame({"size": list(range(min_size, max_size + 1))})

    counts = (
        tmp.groupby([metric, age_bin_col])
        .size()
        .unstack(age_bin_col, fill_value=0)
    )

    counts = counts.reindex(range(min_size, max_size + 1), fill_value=0)
    counts.index.name = "size"

    return counts.reset_index()


def mean_metric_by_age_bin(
    df: pd.DataFrame,
    metric: str,
    age_bin_col: str,
) -> pd.DataFrame:
    """
    Compute mean metric value by age bin.
    """
    tmp = df[[metric, age_bin_col]].copy()
    tmp[metric] = pd.to_numeric(tmp[metric], errors="coerce")
    tmp = tmp[tmp[metric].notna()].copy()
    tmp = tmp[tmp[age_bin_col].notna()].copy()

    if tmp.empty:
        return pd.DataFrame(columns=[age_bin_col, "n", "mean", "median"])

    out = (
        tmp.groupby(age_bin_col)[metric]
        .agg(n="count", mean="mean", median="median")
        .reset_index()
        .sort_values(age_bin_col)
    )

    return out


# ---------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------

def plot_metric_distribution(
    counts_df: pd.DataFrame,
    title: str,
    metric: str,
    out_path: Path,
) -> None:
    """
    Bar plot pooling all utterances in the current dataframe.
    """
    x = counts_df["size"]
    y = counts_df["all_utterances"]

    plt.figure(figsize=(8, 5))
    plt.bar(x, y)

    plt.title(title)
    plt.xlabel(metric)
    plt.ylabel("Number of utterances")
    plt.xticks(x)
    plt.tight_layout()

    plt.savefig(out_path, dpi=300)
    plt.close()


def plot_metric_distribution_by_group(
    counts_df: pd.DataFrame,
    title: str,
    metric: str,
    out_path: Path,
) -> None:
    """
    Line plot by child or group.
    """
    group_cols = [
        c for c in counts_df.columns
        if c not in {"size", "all_utterances"}
    ]

    if not group_cols:
        return

    plt.figure(figsize=(11, 6))

    for group in group_cols:
        plt.plot(
            counts_df["size"],
            counts_df[group],
            marker="o",
            label=group,
        )

    plt.title(title)
    plt.xlabel(metric)
    plt.ylabel("Number of utterances")
    plt.xticks(counts_df["size"])
    plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()

    plt.savefig(out_path, dpi=300)
    plt.close()


def plot_age_stacked_distribution(
    counts_df: pd.DataFrame,
    title: str,
    metric: str,
    out_path: Path,
) -> None:
    """
    Stacked bar plot.

    X-axis: utterance length / metric size.
    Stacks: age bins.
    """
    if counts_df.empty or len(counts_df.columns) <= 1:
        return

    plot_df = counts_df.set_index("size")

    ax = plot_df.plot(
        kind="bar",
        stacked=True,
        figsize=(10, 6),
    )

    ax.set_title(title)
    ax.set_xlabel(metric)
    ax.set_ylabel("Number of utterances")
    ax.legend(title="Age bin", fontsize=7, ncol=2)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


def plot_mean_metric_by_age(
    summary_df: pd.DataFrame,
    title: str,
    metric: str,
    age_bin_col: str,
    out_path: Path,
) -> None:
    """
    Line plot of mean metric value by age bin.
    """
    if summary_df.empty:
        return

    plt.figure(figsize=(10, 5))

    plt.plot(
        summary_df[age_bin_col],
        summary_df["mean"],
        marker="o",
        label="mean",
    )

    plt.plot(
        summary_df[age_bin_col],
        summary_df["median"],
        marker="o",
        label="median",
    )

    plt.title(title)
    plt.xlabel("Age bin")
    plt.ylabel(metric)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()

    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------

def process_collection(
    df: pd.DataFrame,
    collection_name: str,
    out_root: Path,
    metrics: List[str],
    min_size: int,
    max_size: int,
    age_bin_months: int,
    group_col: str,
) -> None:
    """
    Create plots and summaries for either:
      - one dataset
      - all datasets pooled
    """
    collection_dir = out_root / collection_name
    collection_dir.mkdir(parents=True, exist_ok=True)

    if df.empty:
        print(f"[WARN] No rows for collection: {collection_name}")
        return

    # Overview
    if collection_name == "ALL_DATASETS":
        overview = make_global_overview(df)
    else:
        overview = make_dataset_overview(df)

    overview_path = collection_dir / "overview.csv"
    overview.to_csv(overview_path, index=False)
    print(f"[OK] Wrote overview: {overview_path}")

    # Add age bins if possible
    df = add_age_bins(df, age_bin_months)
    age_bin_col = f"age_bin_{age_bin_months}m"
    has_age_bins = "age_months" in df.columns and age_bin_col in df.columns

    for metric in metrics:
        if metric not in df.columns:
            print(f"[WARN] {collection_name}: metric not found, skipping: {metric}")
            continue

        numeric_values = pd.to_numeric(df[metric], errors="coerce")

        if numeric_values.notna().sum() == 0:
            print(f"[WARN] {collection_name}: metric has no numeric values, skipping: {metric}")
            continue

        # -------------------------------------------------------------
        # Standard size distribution
        # -------------------------------------------------------------
        counts = metric_size_counts(
            df,
            metric=metric,
            min_size=min_size,
            max_size=max_size,
            group_col=group_col,
        )

        counts_path = collection_dir / f"{metric}_size_{min_size}_to_{max_size}_counts.csv"
        counts.to_csv(counts_path, index=False)

        plot_path = collection_dir / f"{metric}_size_{min_size}_to_{max_size}_all.png"
        plot_metric_distribution(
            counts,
            title=f"{collection_name}: cleaned utterances by {metric}",
            metric=metric,
            out_path=plot_path,
        )

        group_plot_path = collection_dir / f"{metric}_size_{min_size}_to_{max_size}_by_{group_col}.png"
        plot_metric_distribution_by_group(
            counts,
            title=f"{collection_name}: {metric} distribution by {group_col}",
            metric=metric,
            out_path=group_plot_path,
        )

        print(f"[OK] {collection_name}: wrote size plots/counts for {metric}")

        # -------------------------------------------------------------
        # Age-bin stacked distribution
        # -------------------------------------------------------------
        if has_age_bins:
            age_counts = metric_size_counts_by_age_bin(
                df,
                metric=metric,
                age_bin_col=age_bin_col,
                min_size=min_size,
                max_size=max_size,
            )

            age_counts_path = collection_dir / (
                f"{metric}_size_{min_size}_to_{max_size}_by_age_bin_{age_bin_months}m_counts.csv"
            )
            age_counts.to_csv(age_counts_path, index=False)

            age_plot_path = collection_dir / (
                f"{metric}_size_{min_size}_to_{max_size}_by_age_bin_{age_bin_months}m_stacked.png"
            )
            plot_age_stacked_distribution(
                age_counts,
                title=f"{collection_name}: {metric} distribution by {age_bin_months}-month age bins",
                metric=metric,
                out_path=age_plot_path,
            )

            # ---------------------------------------------------------
            # Trend: mean / median metric by age bin
            # ---------------------------------------------------------
            trend = mean_metric_by_age_bin(
                df,
                metric=metric,
                age_bin_col=age_bin_col,
            )

            trend_path = collection_dir / f"{metric}_mean_by_age_bin_{age_bin_months}m.csv"
            trend.to_csv(trend_path, index=False)

            trend_plot_path = collection_dir / f"{metric}_mean_by_age_bin_{age_bin_months}m.png"
            plot_mean_metric_by_age(
                trend,
                title=f"{collection_name}: mean/median {metric} by {age_bin_months}-month age bin",
                metric=metric,
                age_bin_col=age_bin_col,
                out_path=trend_plot_path,
            )

            print(f"[OK] {collection_name}: wrote age-bin plots/counts for {metric}")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--data_root",
        type=str,
        default="data/preprocessed_data",
        help="Root folder containing Brown/, Manchester/, Providence/",
    )

    ap.add_argument(
        "--out_root",
        type=str,
        default="figs/utterance_distributions",
        help="Output folder for figures and summaries.",
    )

    ap.add_argument(
        "--datasets",
        nargs="+",
        default=DEFAULT_DATASETS,
        help="Datasets to include.",
    )

    ap.add_argument(
        "--metrics",
        nargs="+",
        default=DEFAULT_METRICS + ["utterance_clean_token_count"],
        help="Numeric metrics to plot.",
    )

    ap.add_argument(
        "--min_size",
        type=int,
        default=1,
        help="Minimum utterance size to show.",
    )

    ap.add_argument(
        "--max_size",
        type=int,
        default=8,
        help="Maximum utterance size to show.",
    )

    ap.add_argument(
        "--age_bin_months",
        type=int,
        default=6,
        help="Age-bin size in months for age-colored/stacked plots.",
    )

    args = ap.parse_args()

    data_root = Path(args.data_root)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    print("[INFO] Discovering child utterance files...")
    files = discover_files(data_root, args.datasets)

    if not files:
        raise SystemExit(
            f"No child utterance CSV files found under {data_root} "
            f"for datasets={args.datasets}"
        )

    print(f"[INFO] Found {len(files)} child CSV files.")

    df = load_all(files)
    print(f"[INFO] Loaded total rows: {len(df):,}")

    df = filter_clean_utterances(df)
    print(f"[INFO] Rows after keeping non-empty cleaned utterances: {len(df):,}")

    df = add_derived_lengths(df)

    # Save global column list
    columns_path = out_root / "available_columns.txt"
    with columns_path.open("w", encoding="utf-8") as f:
        for col in df.columns:
            f.write(col + "\n")

    print(f"[OK] Wrote available columns to: {columns_path}")

    # Save loaded file list
    file_list_path = out_root / "loaded_files.csv"
    pd.DataFrame(
        [
            {
                "dataset": dataset,
                "child": child,
                "csv_path": str(path),
            }
            for dataset, child, path in files
        ]
    ).to_csv(file_list_path, index=False)

    print(f"[OK] Wrote loaded file list to: {file_list_path}")

    # -------------------------------------------------------------
    # Per-dataset outputs
    # -------------------------------------------------------------
    for dataset in args.datasets:
        d = df[df["dataset"] == dataset].copy()

        process_collection(
            df=d,
            collection_name=dataset,
            out_root=out_root,
            metrics=args.metrics,
            min_size=args.min_size,
            max_size=args.max_size,
            age_bin_months=args.age_bin_months,
            group_col="child_label",
        )

    # -------------------------------------------------------------
    # Global outputs across all datasets and all children
    # -------------------------------------------------------------
    process_collection(
        df=df,
        collection_name="ALL_DATASETS",
        out_root=out_root,
        metrics=args.metrics,
        min_size=args.min_size,
        max_size=args.max_size,
        age_bin_months=args.age_bin_months,
        group_col="dataset",
    )

    print("\n[DONE]")
    print(f"Figures and summaries written to: {out_root}")


if __name__ == "__main__":
    main()