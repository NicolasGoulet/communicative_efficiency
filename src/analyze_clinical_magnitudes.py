#!/usr/bin/env python3
"""
Analyze clinical dataset magnitudes against controls and naturalistic data.

Outputs focus on two questions:

1. Are clinical/probe sessions smaller than strict naturalistic sessions?
2. How many utterances do we have per 6-month age bin for the newly prepared
   clinical subjects and their matched TD/control arms?
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_CLINICAL_METADATA = PROJECT_ROOT / "results" / "metadata" / "clinical_child_metadata_summary.csv"
DEFAULT_NATURALISTIC_MANIFEST = (
    PROJECT_ROOT / "data" / "big_cleaned_dataset" / "default_naturalistic_custom_early20k" / "manifest.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "clinical_magnitude_analysis"
DEFAULT_FIG_DIR = PROJECT_ROOT / "figs" / "clinical_magnitude_analysis"

GROUP_ORDER = [
    "Autism",
    "Down syndrome",
    "Hearing loss",
    "Focal lesions",
    "Other clinical",
    "New TD controls",
]
POPULATION_ORDER = ["Clinical", "New TD controls", "Strict naturalistic"]
ROLE_METRICS = [
    ("child_utterances", "Child utterances"),
    ("caretaker_utterances", "Caretaker utterances"),
    ("total_utterances", "Total utterances"),
]
ROLE_ORDER = ["child", "caretaker", "total"]


def numeric_or_none(value: object) -> Optional[float]:
    """Return a float when value is numeric, else None."""
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    if math.isnan(out):
        return None
    return out


def clinical_population(row: Mapping[str, object]) -> str:
    """Return broad clinical-vs-control population label."""
    return "New TD controls" if str(row.get("is_control", "")).strip() == "1" else "Clinical"


def clinical_group(row: Mapping[str, object]) -> str:
    """Return the requested clinical group label, with controls separated."""
    if clinical_population(row) == "New TD controls":
        return "New TD controls"

    searchable = " ".join(
        str(row.get(key, ""))
        for key in (
            "clinical_dataset",
            "clinical_group",
            "clinical_status",
            "types_values",
            "demographic_header_values",
            "clinical_header_values",
        )
    ).lower()
    dataset = str(row.get("clinical_dataset", ""))
    status = str(row.get("clinical_status", "")).lower()

    if "autis" in searchable or "asd" in searchable:
        return "Autism"
    if "down_syndrome" in status or "down syndrome" in searchable or dataset.endswith("_DS"):
        return "Down syndrome"
    if "hearing_loss" in status or dataset.endswith("_HL"):
        return "Hearing loss"
    if dataset == "Feldman_SLI" or "lesion" in searchable or "infarct" in searchable:
        return "Focal lesions"
    return "Other clinical"


def fixed_age_bin_label(age_months: object, bin_months: int = 6, start_month: int = 6) -> str:
    """Return fixed-width age bin label such as 024-029."""
    age = numeric_or_none(age_months)
    if age is None:
        return ""
    month = int(math.floor(age))
    if month < start_month:
        start = (month // bin_months) * bin_months
    else:
        start = start_month + ((month - start_month) // bin_months) * bin_months
    end = start + bin_months - 1
    return f"{start:03d}-{end:03d}"


def age_bin_sort_key(label: str) -> Tuple[int, int]:
    """Sort an age bin label by its start/end months."""
    if not label or "-" not in label:
        return (10**9, 10**9)
    start, end = label.split("-", 1)
    return (int(start), int(end))


def read_dict_rows(path: Path) -> List[Dict[str, str]]:
    """Read a CSV into dictionaries."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_clinical_metadata(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    """Return clinical metadata indexed by dataset/child."""
    metadata: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in read_dict_rows(path):
        enriched = dict(row)
        enriched["population"] = clinical_population(row)
        enriched["analysis_group"] = clinical_group(row)
        metadata[(row["clinical_dataset"], row["child_id"])] = enriched
    return metadata


def scan_role_counts(path: Path, role_name: str) -> Dict[Tuple[str, str], Dict[str, object]]:
    """Count non-empty utterances by session/file for one role-specific CSV."""
    counts: Dict[Tuple[str, str], Dict[str, object]] = {}
    if not path.exists():
        return counts

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not str(row.get("utterance_clean", "")).strip():
                continue
            key = (str(row.get("session_id", "")), str(row.get("file", "")))
            record = counts.setdefault(
                key,
                {
                    "session_id": row.get("session_id", ""),
                    "file": row.get("file", ""),
                    "age_months_values": [],
                    "child_utterances": 0,
                    "caretaker_utterances": 0,
                },
            )
            age = numeric_or_none(row.get("age_months"))
            if age is not None:
                record["age_months_values"].append(age)
            if role_name == "child":
                record["child_utterances"] = int(record["child_utterances"]) + 1
            else:
                record["caretaker_utterances"] = int(record["caretaker_utterances"]) + 1

    return counts


def merge_role_counts(
    child_counts: Mapping[Tuple[str, str], Mapping[str, object]],
    caretaker_counts: Mapping[Tuple[str, str], Mapping[str, object]],
) -> List[Dict[str, object]]:
    """Merge child and caretaker counts to one row per session/file."""
    merged: List[Dict[str, object]] = []
    for key in sorted(set(child_counts) | set(caretaker_counts)):
        child = child_counts.get(key, {})
        caretaker = caretaker_counts.get(key, {})
        ages = list(child.get("age_months_values", [])) + list(caretaker.get("age_months_values", []))
        child_n = int(child.get("child_utterances", 0))
        caretaker_n = int(caretaker.get("caretaker_utterances", 0))
        merged.append(
            {
                "session_id": child.get("session_id") or caretaker.get("session_id") or key[0],
                "file": child.get("file") or caretaker.get("file") or key[1],
                "age_months": round(sum(ages) / len(ages), 3) if ages else "",
                "child_utterances": child_n,
                "caretaker_utterances": caretaker_n,
                "total_utterances": child_n + caretaker_n,
            }
        )
    return merged


def collect_unit_session_records(
    dataset: str,
    child_id: str,
    child_csv: Path,
    caretaker_csv: Path,
    *,
    source_type: str,
    population: str,
    analysis_group: str,
    clinical_status: str = "",
) -> List[Dict[str, object]]:
    """Return one record per transcript/session for a child folder."""
    merged = merge_role_counts(scan_role_counts(child_csv, "child"), scan_role_counts(caretaker_csv, "caretaker"))
    records: List[Dict[str, object]] = []
    for row in merged:
        age_bin = fixed_age_bin_label(row["age_months"])
        records.append(
            {
                "source_type": source_type,
                "dataset": dataset,
                "child_id": child_id,
                "unit_label": f"{dataset}/{child_id}",
                "population": population,
                "analysis_group": analysis_group,
                "clinical_status": clinical_status,
                "session_id": row["session_id"],
                "file": row["file"],
                "session_label": f"{dataset}/{child_id}/{row['file'] or row['session_id']}",
                "age_months": row["age_months"],
                "age_bin_6m": age_bin,
                "child_utterances": row["child_utterances"],
                "caretaker_utterances": row["caretaker_utterances"],
                "total_utterances": row["total_utterances"],
            }
        )
    return records


def collect_clinical_session_records(metadata_path: Path) -> List[Dict[str, object]]:
    """Collect session-level rows for the newly prepared clinical/control data."""
    metadata = load_clinical_metadata(metadata_path)
    records: List[Dict[str, object]] = []
    for (dataset, child_id), row in sorted(metadata.items()):
        output_dir = Path(row["output_dir"])
        records.extend(
            collect_unit_session_records(
                dataset,
                child_id,
                output_dir / "chi.csv",
                output_dir / "caretakers.csv",
                source_type="clinical_new",
                population=row["population"],
                analysis_group=row["analysis_group"],
                clinical_status=row["clinical_status"],
            )
        )
    return records


def collect_naturalistic_session_records(manifest_path: Path) -> List[Dict[str, object]]:
    """Collect session-level rows for the current strict naturalistic bundle."""
    records: List[Dict[str, object]] = []
    if not manifest_path.exists():
        return records
    for row in read_dict_rows(manifest_path):
        records.extend(
            collect_unit_session_records(
                row["dataset"],
                row["child_id"],
                PROJECT_ROOT / row["chi_csv"],
                PROJECT_ROOT / row["caretakers_csv"],
                source_type="strict_naturalistic_custom_early20k",
                population="Strict naturalistic",
                analysis_group="Strict naturalistic",
            )
        )
    return records


def role_long_records(session_df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide session counts to long role rows."""
    records: List[Dict[str, object]] = []
    for row in session_df.to_dict("records"):
        for metric, role in (
            ("child_utterances", "child"),
            ("caretaker_utterances", "caretaker"),
            ("total_utterances", "total"),
        ):
            records.append({**row, "role": role, "utterances": int(row.get(metric, 0))})
    return pd.DataFrame.from_records(records)


def complete_age_bin_table(
    df: pd.DataFrame,
    *,
    group_column: str,
    group_order: Sequence[str],
    roles: Sequence[str] = ROLE_ORDER,
) -> pd.DataFrame:
    """Aggregate utterances by age bin/group/role, keeping explicit zero rows."""
    observed_bins = sorted(
        [label for label in df["age_bin_6m"].dropna().astype(str).unique() if label],
        key=age_bin_sort_key,
    )
    long_df = role_long_records(df[df["age_bin_6m"].astype(str).str.strip() != ""])
    if long_df.empty:
        return pd.DataFrame(columns=["age_bin_6m", group_column, "role", "utterances", "n_sessions", "n_children"])

    grouped = (
        long_df.groupby(["age_bin_6m", group_column, "role"], dropna=False)
        .agg(
            utterances=("utterances", "sum"),
            n_sessions=("session_label", "nunique"),
            n_children=("unit_label", "nunique"),
        )
        .reset_index()
    )
    index = {
        (row["age_bin_6m"], row[group_column], row["role"]): row
        for row in grouped.to_dict("records")
    }
    rows: List[Dict[str, object]] = []
    for age_bin in observed_bins:
        for group in group_order:
            for role in roles:
                rows.append(
                    {
                        "age_bin_6m": age_bin,
                        group_column: group,
                        "role": role,
                        "utterances": int(index.get((age_bin, group, role), {}).get("utterances", 0)),
                        "n_sessions": int(index.get((age_bin, group, role), {}).get("n_sessions", 0)),
                        "n_children": int(index.get((age_bin, group, role), {}).get("n_children", 0)),
                    }
                )
    return pd.DataFrame.from_records(rows)


def missing_age_table(df: pd.DataFrame, *, group_column: str, group_order: Sequence[str]) -> pd.DataFrame:
    """Aggregate utterances that cannot be assigned to a 6-month age bin."""
    missing_df = df[df["age_bin_6m"].astype(str).str.strip() == ""].copy()
    long_df = role_long_records(missing_df) if not missing_df.empty else pd.DataFrame()
    grouped: Dict[Tuple[str, str], Dict[str, object]] = {}
    if not long_df.empty:
        aggregate = (
            long_df.groupby([group_column, "role"], dropna=False)
            .agg(
                utterances=("utterances", "sum"),
                n_sessions=("session_label", "nunique"),
                n_children=("unit_label", "nunique"),
            )
            .reset_index()
        )
        grouped = {(row[group_column], row["role"]): row for row in aggregate.to_dict("records")}

    rows: List[Dict[str, object]] = []
    for group in group_order:
        for role in ROLE_ORDER:
            row = grouped.get((group, role), {})
            rows.append(
                {
                    group_column: group,
                    "role": role,
                    "utterances": int(row.get("utterances", 0)),
                    "n_sessions": int(row.get("n_sessions", 0)),
                    "n_children": int(row.get("n_children", 0)),
                }
            )
    return pd.DataFrame.from_records(rows)


def session_summary(df: pd.DataFrame, group_columns: Sequence[str]) -> pd.DataFrame:
    """Summarize utterance counts per transcript/session."""
    grouped = df.groupby(list(group_columns), dropna=False)
    rows: List[Dict[str, object]] = []
    for key, group in grouped:
        key_values = key if isinstance(key, tuple) else (key,)
        row = {column: value for column, value in zip(group_columns, key_values)}
        row.update(
            {
                "n_children": group["unit_label"].nunique(),
                "n_sessions": len(group),
                "child_utterances_total": int(group["child_utterances"].sum()),
                "caretaker_utterances_total": int(group["caretaker_utterances"].sum()),
                "total_utterances_total": int(group["total_utterances"].sum()),
                "child_utterances_median_per_session": round(float(group["child_utterances"].median()), 3),
                "caretaker_utterances_median_per_session": round(float(group["caretaker_utterances"].median()), 3),
                "total_utterances_median_per_session": round(float(group["total_utterances"].median()), 3),
                "child_utterances_mean_per_session": round(float(group["child_utterances"].mean()), 3),
                "caretaker_utterances_mean_per_session": round(float(group["caretaker_utterances"].mean()), 3),
                "total_utterances_mean_per_session": round(float(group["total_utterances"].mean()), 3),
            }
        )
        rows.append(row)
    return pd.DataFrame.from_records(rows)


def write_tables(session_df: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    """Write session and age-bin tables."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "session_counts": output_dir / "session_counts.csv",
        "session_summary_by_population": output_dir / "session_summary_by_population.csv",
        "session_summary_by_dataset": output_dir / "session_summary_by_dataset.csv",
        "session_summary_by_clinical_group": output_dir / "session_summary_by_clinical_group.csv",
        "age_bins_clinical_vs_new_controls": output_dir / "age_bin_counts_clinical_vs_new_controls.csv",
        "age_bins_by_group": output_dir / "age_bin_counts_by_group.csv",
        "missing_age_by_population": output_dir / "missing_age_counts_clinical_vs_new_controls.csv",
        "missing_age_by_group": output_dir / "missing_age_counts_by_group.csv",
    }

    session_df.to_csv(paths["session_counts"], index=False)
    session_summary(session_df, ["population"]).to_csv(paths["session_summary_by_population"], index=False)
    session_summary(session_df, ["source_type", "dataset"]).to_csv(paths["session_summary_by_dataset"], index=False)
    session_summary(
        session_df[session_df["source_type"] == "clinical_new"],
        ["population", "analysis_group"],
    ).to_csv(paths["session_summary_by_clinical_group"], index=False)

    clinical_df = session_df[session_df["source_type"] == "clinical_new"].copy()
    complete_age_bin_table(
        clinical_df,
        group_column="population",
        group_order=["Clinical", "New TD controls"],
    ).to_csv(paths["age_bins_clinical_vs_new_controls"], index=False)
    complete_age_bin_table(clinical_df, group_column="analysis_group", group_order=GROUP_ORDER).to_csv(
        paths["age_bins_by_group"],
        index=False,
    )
    missing_age_table(clinical_df, group_column="population", group_order=["Clinical", "New TD controls"]).to_csv(
        paths["missing_age_by_population"],
        index=False,
    )
    missing_age_table(clinical_df, group_column="analysis_group", group_order=GROUP_ORDER).to_csv(
        paths["missing_age_by_group"],
        index=False,
    )
    return paths


def set_common_plot_style() -> None:
    """Apply consistent readable plotting defaults."""
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 200,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 9,
        }
    )


def savefig(path: Path) -> None:
    """Save current figure with tight layout."""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def plot_session_population_boxplot(df: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot per-session utterance distributions by broad population."""
    path = fig_dir / "utterances_per_session_by_population.png"
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    colors = ["#7b6fd6", "#2f9c95", "#444444"]
    for ax, (metric, title) in zip(axes, ROLE_METRICS):
        data = [
            df.loc[df["population"] == population, metric].astype(float).values
            for population in POPULATION_ORDER
            if not df.loc[df["population"] == population].empty
        ]
        labels = [population for population in POPULATION_ORDER if not df.loc[df["population"] == population].empty]
        box = ax.boxplot(data, tick_labels=labels, showfliers=False, patch_artist=True)
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.45)
        ax.set_title(title)
        ax.set_yscale("symlog", linthresh=10)
        ax.set_ylabel("Non-empty utterances per transcript")
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Session size: clinical/probe data vs current strict naturalistic bundle")
    savefig(path)
    return path


def plot_session_group_boxplot(df: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot per-session utterance distributions by clinical group."""
    path = fig_dir / "utterances_per_session_by_clinical_group.png"
    clinical_df = df[df["source_type"] == "clinical_new"].copy()
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    colors = ["#b5535a", "#4c78a8", "#72b7b2", "#eeca3b", "#9d755d", "#59a14f"]
    for ax, (metric, title) in zip(axes, ROLE_METRICS):
        data = [
            clinical_df.loc[clinical_df["analysis_group"] == group, metric].astype(float).values
            for group in GROUP_ORDER
        ]
        box = ax.boxplot(data, tick_labels=GROUP_ORDER, showfliers=False, patch_artist=True)
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.45)
        ax.set_title(title)
        ax.set_yscale("symlog", linthresh=10)
        ax.set_ylabel("Non-empty utterances per transcript")
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Session size inside the newly prepared clinical/control data")
    savefig(path)
    return path


def plot_dataset_medians(df: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot median total utterances per session by dataset."""
    path = fig_dir / "median_total_utterances_per_session_by_dataset.png"
    summary_df = session_summary(df, ["source_type", "dataset"])
    summary_df = summary_df.sort_values("total_utterances_median_per_session", ascending=True)
    colors = summary_df["source_type"].map(
        {
            "clinical_new": "#4c78a8",
            "strict_naturalistic_custom_early20k": "#444444",
        }
    )
    plt.figure(figsize=(8, max(5, len(summary_df) * 0.25)))
    plt.barh(summary_df["dataset"], summary_df["total_utterances_median_per_session"], color=colors)
    plt.xlabel("Median non-empty utterances per transcript")
    plt.ylabel("Dataset")
    plt.title("Dataset-level session size")
    plt.grid(axis="x", alpha=0.25)
    savefig(path)
    return path


def _plot_age_lines(table: pd.DataFrame, group_column: str, order: Sequence[str], title: str, path: Path) -> Path:
    """Plot age-bin utterance trajectories by group and role."""
    bins = sorted(table["age_bin_6m"].dropna().astype(str).unique(), key=age_bin_sort_key)
    x = range(len(bins))
    fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
    palette = {
        "Clinical": "#b5535a",
        "New TD controls": "#2f9c95",
        "Autism": "#a05195",
        "Down syndrome": "#4c78a8",
        "Hearing loss": "#72b7b2",
        "Focal lesions": "#eeca3b",
        "Other clinical": "#9d755d",
    }
    for ax, role in zip(axes, ROLE_ORDER):
        role_df = table[table["role"] == role]
        for group in order:
            series = (
                role_df[role_df[group_column] == group]
                .set_index("age_bin_6m")
                .reindex(bins)["utterances"]
                .fillna(0)
            )
            ax.plot(x, series.values, marker="o", linewidth=1.8, label=group, color=palette.get(group))
        ax.set_ylabel(f"{role.title()} utterances")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(loc="upper right", ncol=2, fontsize=8)
    axes[-1].set_xticks(list(x))
    axes[-1].set_xticklabels(bins, rotation=45, ha="right")
    fig.suptitle(title)
    savefig(path)
    return path


def plot_age_bin_population(table: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot clinical total versus new TD controls by age bin."""
    return _plot_age_lines(
        table,
        "population",
        ["Clinical", "New TD controls"],
        "6-month age-bin utterance counts: clinical subjects vs new TD controls",
        fig_dir / "age_bins_clinical_vs_new_td_controls.png",
    )


def plot_age_bin_groups(table: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot requested clinical/control groups by age bin."""
    return _plot_age_lines(
        table,
        "analysis_group",
        GROUP_ORDER,
        "6-month age-bin utterance counts by clinical/control group",
        fig_dir / "age_bins_by_clinical_group.png",
    )


def plot_age_bin_heatmap(table: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot a total-utterance heatmap by group and age bin."""
    path = fig_dir / "age_bins_by_group_total_heatmap.png"
    total_df = table[table["role"] == "total"].copy()
    bins = sorted(total_df["age_bin_6m"].dropna().astype(str).unique(), key=age_bin_sort_key)
    matrix = (
        total_df.pivot_table(index="analysis_group", columns="age_bin_6m", values="utterances", aggfunc="sum")
        .reindex(index=GROUP_ORDER, columns=bins)
        .fillna(0)
    )
    values = matrix.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(15, 4.8))
    image = ax.imshow(values, aspect="auto", cmap="viridis")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
    ax.set_title("Total utterances per 6-month bin by group")
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Total non-empty utterances")
    savefig(path)
    return path


def build_analyses(
    clinical_metadata: Path = DEFAULT_CLINICAL_METADATA,
    naturalistic_manifest: Path = DEFAULT_NATURALISTIC_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> Dict[str, List[Path]]:
    """Build all tables and figures for clinical magnitude analysis."""
    clinical_records = collect_clinical_session_records(clinical_metadata)
    naturalistic_records = collect_naturalistic_session_records(naturalistic_manifest)
    session_df = pd.DataFrame.from_records(clinical_records + naturalistic_records)
    if session_df.empty:
        raise RuntimeError("No session records were found.")
    for metric, _ in ROLE_METRICS:
        session_df[metric] = pd.to_numeric(session_df[metric], errors="coerce").fillna(0).astype(int)

    table_paths = write_tables(session_df, output_dir)
    clinical_df = session_df[session_df["source_type"] == "clinical_new"].copy()
    population_table = complete_age_bin_table(
        clinical_df,
        group_column="population",
        group_order=["Clinical", "New TD controls"],
    )
    group_table = complete_age_bin_table(clinical_df, group_column="analysis_group", group_order=GROUP_ORDER)

    set_common_plot_style()
    fig_paths = [
        plot_session_population_boxplot(session_df, fig_dir),
        plot_session_group_boxplot(session_df, fig_dir),
        plot_dataset_medians(session_df, fig_dir),
        plot_age_bin_population(population_table, fig_dir),
        plot_age_bin_groups(group_table, fig_dir),
        plot_age_bin_heatmap(group_table, fig_dir),
    ]
    return {"tables": list(table_paths.values()), "figures": fig_paths}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--clinical-metadata", type=Path, default=DEFAULT_CLINICAL_METADATA)
    parser.add_argument("--naturalistic-manifest", type=Path, default=DEFAULT_NATURALISTIC_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entry point."""
    args = parse_args(argv)
    outputs = build_analyses(
        clinical_metadata=args.clinical_metadata,
        naturalistic_manifest=args.naturalistic_manifest,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
    )
    print("Tables:")
    for path in outputs["tables"]:
        print(f"  {path}")
    print("Figures:")
    for path in outputs["figures"]:
        print(f"  {path}")


if __name__ == "__main__":
    main()
