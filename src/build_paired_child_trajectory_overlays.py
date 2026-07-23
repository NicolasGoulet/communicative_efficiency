#!/usr/bin/env python3
"""Build exactly matched TinyDialogues/Mistral PBM child trajectory overlays."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from build_direct_surprisal_model_suite import md_table
from render_markdown_report import render_markdown_file


KEYS = ["dataset", "child_id", "child_key", "session_id", "age_months", "age_bin"]
OUTCOMES = [
    ("adjusted_k3_bits_2_words", "Contextual surprisal k3"),
    ("adjusted_k0_bits_2_words", "Unconditional surprisal k0"),
    ("adjusted_context_gain_k3_2_words", "Context gain (k0 - k3)"),
]


def safe_slug(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def read_trajectories(path: Path, suffix: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"scope", "utterances", *KEYS, *(column for column, _ in OUTCOMES)}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing trajectory columns: {missing}")
    frame = frame[frame["scope"].eq("pbm_discovery")].copy()
    rename = {
        column: f"{column}_{suffix}"
        for column in frame.columns
        if column not in KEYS
    }
    return frame.rename(columns=rename)


def weighted_standardize(frame: pd.DataFrame, value_column: str, weight_column: str) -> pd.Series:
    values = pd.to_numeric(frame[value_column], errors="coerce")
    weights = pd.to_numeric(frame[weight_column], errors="coerce")
    valid = values.notna() & weights.gt(0)
    output = pd.Series(np.nan, index=frame.index)
    if not valid.any():
        return output
    mean = float(np.average(values[valid], weights=weights[valid]))
    variance = float(np.average((values[valid] - mean) ** 2, weights=weights[valid]))
    scale = math.sqrt(variance)
    if scale > 0:
        output.loc[valid] = (values[valid] - mean) / scale
    return output


def build_pair(
    left_path: Path,
    right_path: Path,
    left_suffix: str,
    right_suffix: str,
    allowed_right_only_child: str | None = None,
    allowed_right_only_count: int = 0,
) -> tuple[pd.DataFrame, dict[str, object]]:
    left = read_trajectories(left_path, left_suffix)
    right = read_trajectories(right_path, right_suffix)
    pair = left.merge(right, on=KEYS, how="outer", validate="one_to_one", indicator=True)
    audit = {
        "left_rows": len(left),
        "right_rows": len(right),
        "paired_rows": int(pair["_merge"].eq("both").sum()),
        "left_only_rows": int(pair["_merge"].eq("left_only").sum()),
        "right_only_rows": int(pair["_merge"].eq("right_only").sum()),
        "left_children": int(left["child_key"].nunique()),
        "right_children": int(right["child_key"].nunique()),
    }
    right_only = pair["_merge"].eq("right_only")
    explained_right_only = (
        int(right_only.sum()) == allowed_right_only_count
        and (
            not right_only.any()
            or pair.loc[right_only, "child_key"].eq(allowed_right_only_child).all()
        )
    )
    audit["explained_right_only_rows"] = (
        int(right_only.sum()) if explained_right_only else 0
    )
    audit["unexplained_mismatch_rows"] = (
        audit["left_only_rows"]
        + (0 if explained_right_only else audit["right_only_rows"])
    )
    if audit["unexplained_mismatch_rows"]:
        raise ValueError(f"Trajectory join failed: {audit}")
    pair = pair[pair["_merge"].eq("both")].drop(columns="_merge")
    for suffix in [left_suffix, right_suffix]:
        for outcome, _ in OUTCOMES:
            pair[f"{outcome}_z_{suffix}"] = weighted_standardize(
                pair,
                f"{outcome}_{suffix}",
                f"utterances_{suffix}",
            )
    audit["join_status"] = "PASS"
    return pair, audit


def weighted_line(group: pd.DataFrame, column: str, weight_column: str) -> tuple[np.ndarray, np.ndarray] | None:
    data = group[["age_months", column, weight_column]].dropna()
    if data["age_months"].nunique() < 3:
        return None
    x = data["age_months"].to_numpy(float)
    y = data[column].to_numpy(float)
    weights = data[weight_column].to_numpy(float)
    design = np.column_stack([np.ones(len(x)), x])
    root_weights = np.sqrt(weights)
    beta, *_ = np.linalg.lstsq(design * root_weights[:, None], y * root_weights, rcond=None)
    grid = np.linspace(x.min(), x.max(), 60)
    return grid, beta[0] + beta[1] * grid


def plot_child(
    group: pd.DataFrame,
    output: Path,
    left_suffix: str,
    right_suffix: str,
    left_label: str,
    right_label: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5), constrained_layout=True)
    colors = {left_suffix: "#2f6f73", right_suffix: "#b3483e"}
    labels = {left_suffix: left_label, right_suffix: right_label}
    for ax, (outcome, title) in zip(axes, OUTCOMES):
        for suffix in [left_suffix, right_suffix]:
            value = f"{outcome}_z_{suffix}"
            weight = f"utterances_{suffix}"
            sizes = np.clip(np.sqrt(group[weight].to_numpy(float)) * 4, 16, 130)
            ax.scatter(
                group["age_months"],
                group[value],
                s=sizes,
                alpha=0.55,
                color=colors[suffix],
                label=labels[suffix],
            )
            line = weighted_line(group, value, weight)
            if line is not None:
                ax.plot(line[0], line[1], color=colors[suffix], linewidth=2)
        ax.axhline(0, color="#777777", linewidth=0.8, alpha=0.5)
        ax.set_title(title)
        ax.set_xlabel("Age (months)")
        ax.set_ylabel("Within-scorer standardized adjusted score")
        ax.grid(alpha=0.18)
    handles, labels_found = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels_found, loc="lower center", ncol=2, frameon=False)
    fig.suptitle(f"{group['child_key'].iloc[0]} — paired scorer trajectories", fontsize=14)
    fig.savefig(output, dpi=165, bbox_inches="tight")
    plt.close(fig)


def run_overlays(
    *,
    left_trajectories: Path,
    right_trajectories: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    left_suffix: str,
    right_suffix: str,
    left_label: str,
    right_label: str,
    allowed_right_only_child: str | None = None,
    allowed_right_only_count: int = 0,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pair, audit = build_pair(
        left_trajectories,
        right_trajectories,
        left_suffix,
        right_suffix,
        allowed_right_only_child,
        allowed_right_only_count,
    )
    pair.to_csv(output_dir / "paired_child_age_session_trajectories.csv.gz", index=False)
    rows = []
    for child_key, group in pair.groupby("child_key", observed=True):
        output = fig_dir / f"{safe_slug(child_key)}.png"
        plot_child(group, output, left_suffix, right_suffix, left_label, right_label)
        rows.append(
            {
                "dataset": group["dataset"].iloc[0],
                "child_id": group["child_id"].iloc[0],
                "child_key": child_key,
                "paired_trajectory_rows": len(group),
                "age_min": group["age_months"].min(),
                "age_max": group["age_months"].max(),
                "plot": str(output),
            }
        )
    profiles = pd.DataFrame(rows).sort_values(["dataset", "child_id"]).reset_index(drop=True)
    profiles.to_csv(output_dir / "paired_child_profile_audit.csv", index=False)
    audit["child_profiles"] = len(profiles)
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = [
        "# Paired TinyDialogues–Mistral PBM Child Trajectories",
        "",
        "These overlays use exactly matched child/session/age trajectory cells. Scores "
        "are standardized separately within each scorer because the models have different "
        "tokenizers and calibration scales. Points are observed cells; straight lines are "
        "descriptive weighted slopes, not interpolation through missing ages.",
        "",
        "## Audit",
        "",
        md_table(pd.DataFrame([audit])),
        "",
        "## Child Profiles",
        "",
        md_table(profiles.drop(columns="plot")),
        "",
    ]
    for dataset, dataset_rows in profiles.groupby("dataset", observed=True):
        lines.extend([f"## {dataset}", ""])
        for row in dataset_rows.itertuples():
            href = os.path.relpath(Path(row.plot), start=report_md.parent).replace(os.sep, "/")
            lines.extend(
                [
                    f"### {row.child_key}",
                    "",
                    f"![{row.child_key} paired trajectories]({href})",
                    "",
                ]
            )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(report_md, report_html, title="Paired PBM Child Trajectories")
    return audit


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left-trajectories", type=Path, required=True)
    parser.add_argument("--right-trajectories", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fig-dir", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-html", type=Path, required=True)
    parser.add_argument("--left-suffix", default="tiny")
    parser.add_argument("--right-suffix", default="mistral")
    parser.add_argument("--left-label", default="TinyDialogues")
    parser.add_argument("--right-label", default="Mistral")
    parser.add_argument("--allowed-right-only-child", default=None)
    parser.add_argument("--allowed-right-only-count", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    audit = run_overlays(
        left_trajectories=args.left_trajectories,
        right_trajectories=args.right_trajectories,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
        left_suffix=args.left_suffix,
        right_suffix=args.right_suffix,
        left_label=args.left_label,
        right_label=args.right_label,
        allowed_right_only_child=args.allowed_right_only_child,
        allowed_right_only_count=args.allowed_right_only_count,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
