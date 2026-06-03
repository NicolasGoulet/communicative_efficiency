"""Build utterance-information dataset summaries and report figures.

For dataset coverage and utterance-count plots, each utterance should be counted
once, so we read only the k0 real-child files and the k0 caretaker files.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from prepare_datasets import age_from_filename_stem


DEFAULT_SCORED_ROOT = Path(
    "results/external/compute_surprisal_mila/"
    "raw_surprisal_cleaned_mistral_patched_006_023"
)
DEFAULT_OUT_DIR = Path("results/utterance_information/report_assets")
DEFAULT_FIG_DIR = Path("figs/utterance_information")

ROLE_SPECS = {
    "child": {
        "pattern": "chi.surprisal_scoring__real.scored.csv",
        "label": "Child",
    },
    "caretaker": {
        "pattern": "caretakers.surprisal_scoring__caretaker.scored.csv",
        "label": "Caretaker",
    },
}

DATASET_ORDER = ["Brown", "Manchester", "Providence"]
DATASET_COLORS = {
    "Brown": "#2F6F73",
    "Manchester": "#C76F2C",
    "Providence": "#6B7F2A",
}
ROLE_COLORS = {
    "child": "#2F6F73",
    "caretaker": "#C76F2C",
}


@dataclass(frozen=True)
class AgeBin:
    """Half-open age bin in months."""

    label: str
    start_month: int
    end_month_exclusive: int


def route1_age_bins() -> list[AgeBin]:
    """Return the current report bins: 006-023, then six-month bins."""

    bins = [AgeBin("006-023", 6, 24)]
    for start in range(24, 66, 6):
        end_exclusive = start + 6
        bins.append(AgeBin(f"{start:03d}-{end_exclusive - 1:03d}", start, end_exclusive))
    return bins


def age_to_route1_bin(age_months: object, bins: Sequence[AgeBin] | None = None) -> str | None:
    """Map a numeric age in months to the current report age-bin label."""

    if bins is None:
        bins = route1_age_bins()
    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return None
    if pd.isna(age):
        return None
    for age_bin in bins:
        if age_bin.start_month <= age < age_bin.end_month_exclusive:
            return age_bin.label
    return None


def resolve_age_months(age_months: object, file_value: object = "") -> tuple[float | None, str]:
    """Resolve age months from the scored row, falling back to CHAT filename age.

    Some scored files preserve a blank `age_months` value even when the CHAT
    filename contains a CHILDES YYMMDD-style age, for example `030000.cha`.
    Report age-bin summaries should use that recoverable age rather than
    silently dropping the session.
    """

    try:
        age = float(age_months)
    except (TypeError, ValueError):
        age = float("nan")
    if not pd.isna(age):
        return age, "scored_age_months"

    file_text = "" if file_value is None else str(file_value)
    if file_text:
        _, fallback_age = age_from_filename_stem(Path(file_text))
        if fallback_age is not None:
            return float(fallback_age), "filename_age"
    return None, "missing"


def compact_count(value: float) -> str:
    """Format counts for plot labels."""

    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1000:
        return f"{value / 1000:.0f}k"
    return str(int(value))


def scored_files(scored_root: Path, role: str) -> list[Path]:
    """Return k0 scored files for one role."""

    if role not in ROLE_SPECS:
        raise ValueError(f"Unknown role: {role}")
    root = scored_root / "WITHOUT_context" / "k0"
    return sorted(root.rglob(ROLE_SPECS[role]["pattern"]))


def read_role_rows(scored_root: Path, role: str, keep_unbinned: bool = False) -> pd.DataFrame:
    """Read the minimal k0 metadata needed for report coverage summaries."""

    paths = scored_files(scored_root, role)
    if not paths:
        raise FileNotFoundError(
            f"No {role} scored files found under {scored_root / 'WITHOUT_context' / 'k0'}"
        )

    needed = {"dataset", "child_id", "session_id", "age_months", "file", "utt_id"}
    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = pd.read_csv(path, usecols=lambda column: column in needed)
        frame["role"] = role
        frame["scored_file"] = str(path)
        frames.append(frame)

    rows = pd.concat(frames, ignore_index=True)
    resolved = rows.apply(
        lambda row: resolve_age_months(row.get("age_months", ""), row.get("file", "")),
        axis=1,
    )
    rows["age_months"] = [age for age, _source in resolved]
    rows["age_months_source"] = [source for _age, source in resolved]
    rows["age_bin"] = rows["age_months"].map(age_to_route1_bin)
    if not keep_unbinned:
        rows = rows[rows["age_bin"].notna()].copy()
    rows["age_bin"] = pd.Categorical(
        rows["age_bin"],
        categories=[age_bin.label for age_bin in route1_age_bins()],
        ordered=True,
    )
    return rows


def zero_filled_age_counts(rows: pd.DataFrame, group_cols: Sequence[str]) -> pd.DataFrame:
    """Count rows by report age bin, preserving zero-count bins."""

    bins = [age_bin.label for age_bin in route1_age_bins()]
    group_values = [sorted(rows[column].dropna().unique().tolist()) for column in group_cols]
    index = pd.MultiIndex.from_product([*group_values, bins], names=[*group_cols, "age_bin"])
    counts = (
        rows.groupby([*group_cols, "age_bin"], observed=False)
        .size()
        .rename("n_utterances")
        .reindex(index, fill_value=0)
        .reset_index()
    )
    return counts


def build_summary_tables(scored_root: Path) -> dict[str, pd.DataFrame]:
    """Build report dataset, child, and age-bin summary tables."""

    child_rows_all = read_role_rows(scored_root, "child", keep_unbinned=True)
    caretaker_rows_all = read_role_rows(scored_root, "caretaker", keep_unbinned=True)
    child_rows = child_rows_all[child_rows_all["age_bin"].notna()].copy()
    caretaker_rows = caretaker_rows_all[caretaker_rows_all["age_bin"].notna()].copy()
    all_rows = pd.concat([child_rows, caretaker_rows], ignore_index=True)

    age_role_counts = zero_filled_age_counts(all_rows, ["role"])
    age_dataset_role_counts = zero_filled_age_counts(all_rows, ["role", "dataset"])

    child_summary = (
        child_rows.groupby(["dataset", "child_id"], observed=False)
        .agg(
            child_utterances=("utt_id", "size"),
            child_age_min_months=("age_months", "min"),
            child_age_max_months=("age_months", "max"),
            child_sessions=("session_id", pd.Series.nunique),
            child_files=("file", pd.Series.nunique),
            child_age_bins=("age_bin", pd.Series.nunique),
        )
        .reset_index()
    )
    caretaker_by_child = (
        caretaker_rows.groupby(["dataset", "child_id"], observed=False)
        .agg(
            caretaker_utterances=("utt_id", "size"),
            caretaker_sessions=("session_id", pd.Series.nunique),
            caretaker_files=("file", pd.Series.nunique),
            caretaker_age_min_months=("age_months", "min"),
            caretaker_age_max_months=("age_months", "max"),
        )
        .reset_index()
    )
    child_summary = child_summary.merge(
        caretaker_by_child,
        on=["dataset", "child_id"],
        how="left",
    ).fillna(
        {
            "caretaker_utterances": 0,
            "caretaker_sessions": 0,
            "caretaker_files": 0,
        }
    )

    dataset_summary = (
        child_summary.groupby("dataset", observed=False)
        .agg(
            children=("child_id", "nunique"),
            child_utterances=("child_utterances", "sum"),
            caretaker_utterances=("caretaker_utterances", "sum"),
            age_min_months=("child_age_min_months", "min"),
            age_max_months=("child_age_max_months", "max"),
            median_child_sessions=("child_sessions", "median"),
            total_child_sessions=("child_sessions", "sum"),
        )
        .reset_index()
    )
    dataset_summary["dataset"] = pd.Categorical(
        dataset_summary["dataset"],
        categories=[dataset for dataset in DATASET_ORDER if dataset in dataset_summary["dataset"].tolist()],
        ordered=True,
    )
    dataset_summary = dataset_summary.sort_values("dataset").reset_index(drop=True)
    dataset_summary["child_utterances"] = dataset_summary["child_utterances"].astype(int)
    dataset_summary["caretaker_utterances"] = dataset_summary["caretaker_utterances"].astype(int)

    coverage_rows = []
    for role, role_rows_all, role_rows in [
        ("child", child_rows_all, child_rows),
        ("caretaker", caretaker_rows_all, caretaker_rows),
    ]:
        missing_after_recovery = int(role_rows_all["age_months"].isna().sum())
        outside_route1_bins = int(
            role_rows_all[
                role_rows_all["age_months"].notna() & role_rows_all["age_bin"].isna()
            ].shape[0]
        )
        coverage_rows.append(
            {
                "role": role,
                "raw_k0_scored_rows": len(role_rows_all),
                "filename_recovered_age_rows": int(
                    (role_rows_all["age_months_source"] == "filename_age").sum()
                ),
                "age_binned_rows": len(role_rows),
                "missing_age_after_recovery": missing_after_recovery,
                "outside_route1_age_bins": outside_route1_bins,
                "min_age_months_in_bins": role_rows["age_months"].min(),
                "max_age_months_in_bins": role_rows["age_months"].max(),
            }
        )
    coverage_audit = pd.DataFrame(coverage_rows)

    return {
        "coverage_audit": coverage_audit,
        "age_role_counts": age_role_counts,
        "age_dataset_role_counts": age_dataset_role_counts,
        "child_trajectory_summary": child_summary.sort_values(
            ["dataset", "child_age_min_months", "child_id"]
        ).reset_index(drop=True),
        "dataset_summary": dataset_summary,
    }


def save_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> None:
    """Write report summary tables as CSV."""

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)


def plot_total_counts(age_role_counts: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot child and caretaker utterance totals by age bin."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    out = fig_dir / "total_utterances_by_age_bin.png"
    bins = [age_bin.label for age_bin in route1_age_bins()]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    for ax, role in zip(axes, ["child", "caretaker"]):
        role_counts = (
            age_role_counts[age_role_counts["role"] == role]
            .set_index("age_bin")
            .reindex(bins, fill_value=0)
        )
        values = role_counts["n_utterances"].astype(int).tolist()
        bars = ax.bar(bins, values, color=ROLE_COLORS[role], width=0.72)
        ax.set_title(f"{ROLE_SPECS[role]['label']} utterances")
        ax.set_xlabel("Age bin in months")
        ax.set_ylabel("Scored utterances")
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
        ymax = max(values) if values else 0
        ax.set_ylim(0, ymax * 1.18 if ymax else 1)
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(ymax * 0.02, 1),
                compact_count(value),
                ha="center",
                va="bottom",
                fontsize=8,
            )
    fig.suptitle("Utterance Coverage by Age", fontsize=14)
    fig.savefig(out, dpi=180)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out


def plot_dataset_counts(age_dataset_role_counts: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot stacked dataset contributions to each age bin."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    out = fig_dir / "utterances_by_age_bin_and_corpus.png"
    bins = [age_bin.label for age_bin in route1_age_bins()]
    datasets = [
        dataset
        for dataset in DATASET_ORDER
        if dataset in age_dataset_role_counts["dataset"].dropna().unique().tolist()
    ]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8.4), sharex=True, constrained_layout=True)
    for ax, role in zip(axes, ["child", "caretaker"]):
        bottom = [0] * len(bins)
        for dataset in datasets:
            subset = age_dataset_role_counts[
                (age_dataset_role_counts["role"] == role)
                & (age_dataset_role_counts["dataset"] == dataset)
            ]
            values = (
                subset.set_index("age_bin")
                .reindex(bins, fill_value=0)["n_utterances"]
                .astype(int)
                .tolist()
            )
            ax.bar(
                bins,
                values,
                bottom=bottom,
                label=dataset,
                color=DATASET_COLORS.get(dataset),
                width=0.72,
            )
            bottom = [old + new for old, new in zip(bottom, values)]
        ax.set_title(f"{ROLE_SPECS[role]['label']} utterances")
        ax.set_ylabel("Scored utterances")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(loc="upper right", ncols=len(datasets), frameon=False)
    axes[-1].set_xlabel("Age bin in months")
    axes[-1].tick_params(axis="x", rotation=35)
    fig.suptitle("Corpus Contributions by Age", fontsize=14)
    fig.savefig(out, dpi=180)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out


def plot_child_coverage(child_summary: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot each child's observed developmental coverage."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    out = fig_dir / "child_developmental_coverage.png"
    ordered = child_summary.sort_values(["dataset", "child_age_min_months", "child_id"]).reset_index(
        drop=True
    )
    labels = [f"{row.dataset}/{row.child_id}" for row in ordered.itertuples()]
    y_positions = list(range(len(ordered)))

    fig_height = max(6.0, 0.34 * len(ordered) + 1.5)
    fig, ax = plt.subplots(figsize=(11, fig_height), constrained_layout=True)

    for y, row in zip(y_positions, ordered.itertuples()):
        color = DATASET_COLORS.get(row.dataset, "#555555")
        ax.hlines(
            y,
            row.child_age_min_months,
            row.child_age_max_months,
            color=color,
            linewidth=3,
            alpha=0.9,
        )
        ax.scatter(
            [row.child_age_min_months, row.child_age_max_months],
            [y, y],
            color=color,
            s=24,
            zorder=3,
        )

    for boundary in [24, 30, 36, 42, 48, 54, 60, 66]:
        ax.axvline(boundary, color="#999999", linewidth=0.8, alpha=0.25)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Age in months")
    ax.set_title("Child Age Coverage")
    ax.grid(axis="x", alpha=0.2)
    ax.set_xlim(6, 66)
    fig.savefig(out, dpi=180)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out


def write_markdown_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> None:
    """Write compact Markdown tables for inclusion in the report."""

    out_dir.mkdir(parents=True, exist_ok=True)
    coverage = tables["coverage_audit"].copy()
    coverage = coverage.rename(
        columns={
            "role": "Role",
            "raw_k0_scored_rows": "Raw k0 scored rows",
            "filename_recovered_age_rows": "Age rows recovered from filename",
            "age_binned_rows": "Rows in age bins",
            "missing_age_after_recovery": "Missing age after recovery",
            "outside_route1_age_bins": "Outside age bins",
            "min_age_months_in_bins": "Min age in bins",
            "max_age_months_in_bins": "Max age in bins",
        }
    )
    (out_dir / "coverage_audit.md").write_text(dataframe_to_markdown(coverage), encoding="utf-8")

    dataset_summary = tables["dataset_summary"].copy()
    dataset_summary["age_range_months"] = dataset_summary.apply(
        lambda row: f"{row['age_min_months']:.1f}-{row['age_max_months']:.1f}",
        axis=1,
    )
    dataset_display = dataset_summary[
        [
            "dataset",
            "children",
            "child_utterances",
            "caretaker_utterances",
            "age_range_months",
            "total_child_sessions",
        ]
    ].rename(
        columns={
            "dataset": "Corpus",
            "children": "Children",
            "child_utterances": "Child utterances",
            "caretaker_utterances": "Caretaker utterances",
            "age_range_months": "Child age range",
            "total_child_sessions": "Child sessions/files",
        }
    )
    total_row = {
        "Corpus": "Total",
        "Children": int(dataset_display["Children"].sum()),
        "Child utterances": int(dataset_display["Child utterances"].sum()),
        "Caretaker utterances": int(dataset_display["Caretaker utterances"].sum()),
        "Child age range": (
            f"{dataset_summary['age_min_months'].min():.1f}-"
            f"{dataset_summary['age_max_months'].max():.1f}"
        ),
        "Child sessions/files": int(dataset_display["Child sessions/files"].sum()),
    }
    dataset_display = pd.concat([dataset_display, pd.DataFrame([total_row])], ignore_index=True)
    (out_dir / "dataset_summary.md").write_text(
        dataframe_to_markdown(dataset_display),
        encoding="utf-8",
    )

    age_counts = tables["age_role_counts"].pivot(
        index="age_bin",
        columns="role",
        values="n_utterances",
    ).reset_index()
    age_counts = age_counts.rename(
        columns={
            "age_bin": "Age bin",
            "child": "Child utterances",
            "caretaker": "Caretaker utterances",
        }
    )
    (out_dir / "age_role_counts.md").write_text(dataframe_to_markdown(age_counts), encoding="utf-8")


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    """Render a small DataFrame as a GitHub-style Markdown table."""

    columns = [str(column) for column in frame.columns]
    rows = []
    for _, row in frame.iterrows():
        rows.append([format_markdown_cell(row[column]) for column in frame.columns])
    widths = [
        max(len(columns[index]), *(len(row[index]) for row in rows)) if rows else len(columns[index])
        for index in range(len(columns))
    ]

    def render_row(values: Sequence[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(values)) + " |"

    output = [
        render_row(columns),
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    output.extend(render_row(row) for row in rows)
    return "\n".join(output)


def format_markdown_cell(value: object) -> str:
    """Format one table cell for Markdown output."""

    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def build_assets(scored_root: Path, out_dir: Path, fig_dir: Path) -> dict[str, pd.DataFrame]:
    """Build all report coverage assets."""

    tables = build_summary_tables(scored_root)
    validate_complete_age_coverage(tables["coverage_audit"])
    save_tables(tables, out_dir)
    write_markdown_tables(tables, out_dir)
    plot_total_counts(tables["age_role_counts"], fig_dir)
    plot_dataset_counts(tables["age_dataset_role_counts"], fig_dir)
    plot_child_coverage(tables["child_trajectory_summary"], fig_dir)
    return tables


def validate_complete_age_coverage(coverage_audit: pd.DataFrame) -> None:
    """Raise when any scored k0 row cannot be assigned to a report age bin."""

    problems = coverage_audit[
        (coverage_audit["raw_k0_scored_rows"] != coverage_audit["age_binned_rows"])
        | (coverage_audit["missing_age_after_recovery"] != 0)
        | (coverage_audit["outside_route1_age_bins"] != 0)
    ]
    if not problems.empty:
        details = "; ".join(
            (
                f"{row.role}: raw={row.raw_k0_scored_rows}, "
                f"binned={row.age_binned_rows}, "
                f"missing_after_recovery={row.missing_age_after_recovery}, "
                f"outside_bins={row.outside_route1_age_bins}"
            )
            for row in problems.itertuples()
        )
        raise ValueError(f"Age-bin coverage is incomplete: {details}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build utterance-information report coverage assets.")
    parser.add_argument("--scored-root", type=Path, default=DEFAULT_SCORED_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables = build_assets(args.scored_root, args.out_dir, args.fig_dir)
    print(f"[OK] Wrote report tables to {args.out_dir}")
    print(f"[OK] Wrote report figures to {args.fig_dir}")
    print(
        "[SUMMARY] child rows:",
        int(tables["dataset_summary"]["child_utterances"].sum()),
        "caretaker rows:",
        int(tables["dataset_summary"]["caretaker_utterances"].sum()),
    )


if __name__ == "__main__":
    main()
