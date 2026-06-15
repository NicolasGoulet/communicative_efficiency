#!/usr/bin/env python3
"""Audit effort-count distributions and propose fixed-effort slices.

This script answers a plotting/model-interpretation question: which exact
effort values should we use when drawing adjusted age trajectories?

It is deliberately separate from model fitting. It reads the same real-child
modeling rows used by the M1-M6 analyses, summarizes the empirical effort
distributions, documents the low/mid/high effort-level rules, and proposes
fixed effort values for future plots.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from build_m1_m2_utterance_information_deep_dive import (
        AGE_BIN_ORDER,
        DEFAULT_INPUT,
        EFFORT_MEASURES,
        assign_effort_level,
        read_modeling_rows,
    )
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import (
        AGE_BIN_ORDER,
        DEFAULT_INPUT,
        EFFORT_MEASURES,
        assign_effort_level,
        read_modeling_rows,
    )
    from src.render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/effort_slice_audit")
DEFAULT_FIG_DIR = Path("figs/effort_slice_audit")
DEFAULT_DOC_MD = Path("docs/utterance_effort_slice_audit.md")
DEFAULT_DOC_HTML = Path("docs/utterance_effort_slice_audit.html")

QUANTILES = [0, 0.01, 0.05, 0.10, 0.25, 1 / 3, 0.50, 2 / 3, 0.75, 0.90, 0.95, 0.99, 1]
QUANTILE_LABELS = {
    0: "min",
    0.01: "p01",
    0.05: "p05",
    0.10: "p10",
    0.25: "p25",
    1 / 3: "p33",
    0.50: "p50",
    2 / 3: "p66",
    0.75: "p75",
    0.90: "p90",
    0.95: "p95",
    0.99: "p99",
    1: "max",
}


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 20, digits: int = 4) -> str:
    """Render a compact Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    rendered = shown.astype(object).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]):
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else f"{value:.{digits}g}")
        else:
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(str(col) for col in rendered.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def nearest_observed_value(observed_values: Iterable[int], target: float) -> int:
    """Return the observed integer value closest to a target quantile value."""

    values = sorted({int(value) for value in observed_values})
    if not values:
        raise ValueError("cannot choose nearest value from an empty set")
    return min(values, key=lambda value: (abs(value - target), value))


def effort_quantile_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute distribution summaries for every effort count."""

    rows: list[dict[str, object]] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        values = pd.to_numeric(frame[effort_col], errors="coerce").dropna()
        values = values[values > 0]
        row: dict[str, object] = {
            "effort_col": effort_col,
            "effort_label": effort_label,
            "rows": int(values.shape[0]),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=0)),
        }
        for quantile in QUANTILES:
            row[QUANTILE_LABELS[quantile]] = float(values.quantile(quantile))
        rows.append(row)
    return pd.DataFrame(rows)


def effort_value_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Count each exact effort value overall."""

    rows: list[dict[str, object]] = []
    total = len(frame)
    for effort_col, effort_label in EFFORT_MEASURES:
        values = pd.to_numeric(frame[effort_col], errors="coerce")
        sub = frame.assign(effort_value=values).dropna(subset=["effort_value"]).copy()
        sub = sub[sub["effort_value"] > 0].copy()
        sub["effort_value"] = sub["effort_value"].round().astype(int)
        counts = (
            sub.groupby("effort_value", observed=True)
            .agg(
                rows=("score_id", "size"),
                n_children=("child_id", "nunique"),
                n_age_bins=("age_bin", "nunique"),
                age_min=("age_months", "min"),
                age_max=("age_months", "max"),
            )
            .reset_index()
            .sort_values("effort_value")
        )
        counts["pct_rows"] = counts["rows"] / total
        counts["cumulative_pct"] = counts["rows"].cumsum() / counts["rows"].sum()
        counts.insert(0, "effort_label", effort_label)
        counts.insert(0, "effort_col", effort_col)
        rows.extend(counts.to_dict("records"))
    return pd.DataFrame(rows)


def effort_by_age_bin_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Count exact effort values inside each age bin."""

    rows: list[pd.DataFrame] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        sub = frame[["score_id", "age_bin", "child_id", effort_col]].copy()
        sub["effort_value"] = pd.to_numeric(sub[effort_col], errors="coerce")
        sub = sub.dropna(subset=["effort_value"]).copy()
        sub = sub[sub["effort_value"] > 0].copy()
        sub["effort_value"] = sub["effort_value"].round().astype(int)
        counts = (
            sub.groupby(["age_bin", "effort_value"], observed=True)
            .agg(rows=("score_id", "size"), n_children=("child_id", "nunique"))
            .reset_index()
        )
        counts.insert(0, "effort_label", effort_label)
        counts.insert(0, "effort_col", effort_col)
        rows.append(counts)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def effort_level_definitions(frame: pd.DataFrame) -> pd.DataFrame:
    """Document how low/mid/high effort groups are defined and populated."""

    rows: list[dict[str, object]] = []
    total = len(frame)
    for effort_col, effort_label in EFFORT_MEASURES:
        values = pd.to_numeric(frame[effort_col], errors="coerce")
        low_cut = float(values.quantile(1 / 3))
        high_cut = float(values.quantile(2 / 3))
        levels = assign_effort_level(values)
        sub = frame.assign(effort_value=values, effort_level=levels).dropna(subset=["effort_value"]).copy()
        for level in ["low effort", "mid effort", "high effort"]:
            group = sub[sub["effort_level"].astype(str).eq(level)]
            rows.append(
                {
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "effort_level": level,
                    "low_cut_p33": low_cut,
                    "high_cut_p66": high_cut,
                    "rule": level_rule(level, low_cut, high_cut),
                    "rows": int(group.shape[0]),
                    "pct_rows": float(group.shape[0] / total) if total else math.nan,
                    "min_value": float(group["effort_value"].min()) if not group.empty else math.nan,
                    "median_value": float(group["effort_value"].median()) if not group.empty else math.nan,
                    "max_value": float(group["effort_value"].max()) if not group.empty else math.nan,
                    "n_children": int(group["child_id"].nunique()) if not group.empty else 0,
                    "n_age_bins": int(group["age_bin"].nunique()) if not group.empty else 0,
                }
            )
    return pd.DataFrame(rows)


def level_rule(level: str, low_cut: float, high_cut: float) -> str:
    """Return the human-readable rule for one tertile effort level."""

    if not np.isfinite(low_cut) or not np.isfinite(high_cut) or low_cut >= high_cut:
        return "fallback split at median because tertile cutpoints collapsed"
    if level == "low effort":
        return f"value <= p33 ({low_cut:.2f})"
    if level == "high effort":
        return f"value >= p66 ({high_cut:.2f})"
    return f"p33 < value < p66 ({low_cut:.2f} to {high_cut:.2f})"


def distribution_lookup(distribution: pd.DataFrame) -> Mapping[tuple[str, int], dict[str, object]]:
    """Return exact-value distribution rows keyed by effort column and value."""

    lookup: dict[tuple[str, int], dict[str, object]] = {}
    for row in distribution.to_dict("records"):
        lookup[(str(row["effort_col"]), int(row["effort_value"]))] = row
    return lookup


def add_proposal_row(
    rows: list[dict[str, object]],
    *,
    lookup: Mapping[tuple[str, int], dict[str, object]],
    effort_col: str,
    effort_label: str,
    value: int,
    proposal_set: str,
    reason: str,
    min_rows: int,
    min_age_bins: int,
    min_children: int,
) -> None:
    """Append one proposed fixed effort value with support metadata."""

    support = lookup.get((effort_col, int(value)), {})
    rows.append(
        {
            "effort_col": effort_col,
            "effort_label": effort_label,
            "proposal_set": proposal_set,
            "fixed_effort_value": int(value),
            "reason": reason,
            "rows": int(support.get("rows", 0) or 0),
            "pct_rows": float(support.get("pct_rows", 0.0) or 0.0),
            "n_children": int(support.get("n_children", 0) or 0),
            "n_age_bins": int(support.get("n_age_bins", 0) or 0),
            "age_min": support.get("age_min", math.nan),
            "age_max": support.get("age_max", math.nan),
            "meets_support_rule": bool(
                int(support.get("rows", 0) or 0) >= min_rows
                and int(support.get("n_age_bins", 0) or 0) >= min_age_bins
                and int(support.get("n_children", 0) or 0) >= min_children
            ),
        }
    )


def proposed_fixed_slices(
    frame: pd.DataFrame,
    distribution: pd.DataFrame,
    *,
    min_rows: int = 500,
    min_age_bins: int = 6,
    min_children: int = 10,
) -> pd.DataFrame:
    """Propose fixed effort values for adjusted age plots."""

    rows: list[dict[str, object]] = []
    lookup = distribution_lookup(distribution)
    for effort_col, effort_label in EFFORT_MEASURES:
        values = pd.to_numeric(frame[effort_col], errors="coerce").dropna()
        values = values[values > 0].round().astype(int)
        observed = sorted(values.unique())
        if not observed:
            continue

        if effort_col in {"nb_words", "nb_morphemes"}:
            for value in range(1, 13):
                add_proposal_row(
                    rows,
                    lookup=lookup,
                    effort_col=effort_col,
                    effort_label=effort_label,
                    value=value,
                    proposal_set="requested_dense_1_12",
                    reason="User-requested exact slices for words and morphemes.",
                    min_rows=min_rows,
                    min_age_bins=min_age_bins,
                    min_children=min_children,
                )

        for proposal_set, quantiles in [
            ("primary_low_median_high_p25_p50_p75", [0.25, 0.50, 0.75]),
            ("wide_low_median_high_p10_p50_p90", [0.10, 0.50, 0.90]),
            ("tertile_boundary_anchors_p33_p50_p66", [1 / 3, 0.50, 2 / 3]),
        ]:
            for quantile in quantiles:
                raw = float(values.quantile(quantile))
                fixed = nearest_observed_value(observed, raw)
                add_proposal_row(
                    rows,
                    lookup=lookup,
                    effort_col=effort_col,
                    effort_label=effort_label,
                    value=fixed,
                    proposal_set=proposal_set,
                    reason=f"Nearest observed integer to {QUANTILE_LABELS[quantile]}={raw:.2f}.",
                    min_rows=min_rows,
                    min_age_bins=min_age_bins,
                    min_children=min_children,
                )

        supported = distribution[
            distribution["effort_col"].eq(effort_col)
            & (distribution["rows"] >= min_rows)
            & (distribution["n_age_bins"] >= min_age_bins)
            & (distribution["n_children"] >= min_children)
        ].copy()
        if not supported.empty:
            p95 = float(values.quantile(0.95))
            supported = supported[supported["effort_value"] <= math.ceil(p95)].copy()
            for value in supported["effort_value"].astype(int).tolist():
                add_proposal_row(
                    rows,
                    lookup=lookup,
                    effort_col=effort_col,
                    effort_label=effort_label,
                    value=value,
                    proposal_set="data_supported_dense_core",
                    reason=(
                        f"At least {min_rows} rows, {min_children} children, "
                        f"{min_age_bins} age bins, and not above p95."
                    ),
                    min_rows=min_rows,
                    min_age_bins=min_age_bins,
                    min_children=min_children,
                )

        top_frequency = (
            distribution[distribution["effort_col"].eq(effort_col)]
            .sort_values(["rows", "effort_value"], ascending=[False, True])
            .head(12)
            .sort_values("effort_value")
        )
        for value in top_frequency["effort_value"].astype(int).tolist():
            add_proposal_row(
                rows,
                lookup=lookup,
                effort_col=effort_col,
                effort_label=effort_label,
                value=value,
                proposal_set="top_frequency_12",
                reason="One of the 12 most frequent exact effort values for this effort unit.",
                min_rows=min_rows,
                min_age_bins=min_age_bins,
                min_children=min_children,
            )

    out = pd.DataFrame(rows).drop_duplicates(
        subset=["effort_col", "proposal_set", "fixed_effort_value"],
        keep="first",
    )
    return out.sort_values(["effort_col", "proposal_set", "fixed_effort_value"]).reset_index(drop=True)


def plot_effort_distributions(
    distribution: pd.DataFrame,
    quantiles: pd.DataFrame,
    *,
    fig_dir: Path,
) -> Path:
    """Plot exact effort-value distributions."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(len(EFFORT_MEASURES), 1, figsize=(14, 18), constrained_layout=True)
    for ax, (effort_col, effort_label) in zip(axes, EFFORT_MEASURES):
        sub = distribution[distribution["effort_col"].eq(effort_col)].copy()
        qrow = quantiles[quantiles["effort_col"].eq(effort_col)].iloc[0]
        max_x = int(math.ceil(float(qrow["p99"])))
        shown = sub[sub["effort_value"] <= max_x].copy()
        ax.bar(shown["effort_value"], shown["rows"], color="#4c78a8", alpha=0.85)
        for label, color in [("p25", "#f58518"), ("p50", "#54a24b"), ("p75", "#e45756"), ("p90", "#7f3c8d")]:
            value = float(qrow[label])
            ax.axvline(value, color=color, linestyle="--", linewidth=1.8, label=label)
        ax.set_title(f"{effort_label}: exact effort-value distribution (shown through p99)")
        ax.set_xlabel("Exact effort count")
        ax.set_ylabel("Utterance rows")
        ax.legend(loc="upper right", ncol=4)
    out = fig_dir / "effort_value_distributions.png"
    fig.savefig(out, dpi=220)
    fig.savefig(fig_dir / "effort_value_distributions.pdf")
    plt.close(fig)
    return out


def compact_proposal_list(proposals: pd.DataFrame, proposal_set: str) -> pd.DataFrame:
    """Return one compact row per effort label for a proposal set."""

    rows: list[dict[str, object]] = []
    sub = proposals[proposals["proposal_set"].eq(proposal_set)].copy()
    for effort_col, effort_label in EFFORT_MEASURES:
        group = sub[sub["effort_col"].eq(effort_col)].sort_values("fixed_effort_value")
        rows.append(
            {
                "effort": effort_label,
                "values": ", ".join(str(int(value)) for value in group["fixed_effort_value"].unique()),
                "supported_values": ", ".join(
                    str(int(value))
                    for value in group[group["meets_support_rule"]]["fixed_effort_value"].unique()
                ),
            }
        )
    return pd.DataFrame(rows)


def build_markdown(
    *,
    quantiles: pd.DataFrame,
    distribution: pd.DataFrame,
    by_age: pd.DataFrame,
    levels: pd.DataFrame,
    proposals: pd.DataFrame,
    fig_path: Path,
    output_dir: Path,
) -> str:
    """Build the effort-slice audit Markdown."""

    del by_age  # The CSV path is documented; the table would be too large.
    qcols = [
        "effort_label",
        "rows",
        "mean",
        "sd",
        "p10",
        "p25",
        "p33",
        "p50",
        "p66",
        "p75",
        "p90",
        "p95",
        "p99",
        "max",
    ]
    level_cols = [
        "effort_label",
        "effort_level",
        "rule",
        "rows",
        "pct_rows",
        "min_value",
        "median_value",
        "max_value",
        "n_children",
        "n_age_bins",
    ]
    mandatory = compact_proposal_list(proposals, "requested_dense_1_12")
    primary = compact_proposal_list(proposals, "primary_low_median_high_p25_p50_p75")
    wide = compact_proposal_list(proposals, "wide_low_median_high_p10_p50_p90")
    dense = compact_proposal_list(proposals, "data_supported_dense_core")

    support_cols = [
        "effort_label",
        "proposal_set",
        "fixed_effort_value",
        "rows",
        "n_children",
        "n_age_bins",
        "meets_support_rule",
    ]
    support_preview = proposals[
        proposals["proposal_set"].isin(
            [
                "requested_dense_1_12",
                "primary_low_median_high_p25_p50_p75",
                "wide_low_median_high_p10_p50_p90",
            ]
        )
    ][support_cols].copy()

    rel_fig = Path("..") / fig_path
    return f"""# Effort Slice Audit For Adjusted Age Plots

This document fixes the plotting issue we identified: a single median-effort
line is only one conditional slice of a fitted model. It is useful, but it is
not enough as the main evidence.

The audit uses the same real-child `k3` modeling rows used by the M1-M6 reports.
It does not refit any M1-M6 model.

## Straight Answer

Use three complementary views:

1. **Exact fixed-effort slices.** These are the strongest visual controls
   because every plotted line corresponds to a concrete effort count.
2. **Low / median / high fixed slices.** These should be quantile anchors such
   as p25/p50/p75 or wider p10/p50/p90, not only one median line.
3. **Low / mid / high effort groups.** These are diagnostic categorical models.
   They are not the same thing as exact fixed-effort control because each group
   contains a range of effort values.

## Saved Outputs

```text
{output_dir / "effort_quantile_summary.csv"}
{output_dir / "effort_value_distribution.csv"}
{output_dir / "effort_by_age_bin_distribution.csv"}
{output_dir / "effort_level_definitions.csv"}
{output_dir / "proposed_fixed_effort_slices.csv"}
```

## Effort Distributions

![Exact effort value distributions]({rel_fig})

{markdown_table(quantiles[qcols], digits=3)}

## How Low / Mid / High Effort Is Currently Defined

For each effort unit separately, we compute the empirical 33rd and 66th
percentiles. Then:

```text
low effort  = value <= p33
high effort = value >= p66
mid effort  = values between p33 and p66
```

Because effort counts are integers, these groups can be uneven. If p33 and p66
fall around the same integer, the mid group can become very narrow. This is why
low/mid/high effort groups should be treated as a diagnostic view, not the only
evidence.

{markdown_table(levels[level_cols], max_rows=20, digits=3)}

## Proposed Fixed Effort Slices

### Mandatory Exact Word And Morpheme Slices

These implement the decision to show words and morphemes from 1 to 12.

{markdown_table(mandatory, digits=3)}

### Primary Low / Median / High Fixed Slices

These are p25/p50/p75 anchors. They are a cleaner replacement for a single
median line when we want only three lines.

{markdown_table(primary, digits=3)}

### Wider Low / Median / High Fixed Slices

These are p10/p50/p90 anchors. They are useful when p25/p75 are too close and
we want to visibly stress-test the trajectory at small versus large utterances.

{markdown_table(wide, digits=3)}

### Data-Supported Dense Core

These are exact effort values with enough support to be plotted without relying
on tiny cells. Current support rule:

```text
at least 500 rows, at least 10 children, at least 6 age bins, and not above p95
```

{markdown_table(dense, digits=3)}

## Support Preview For Key Proposed Values

{markdown_table(support_preview, max_rows=80, digits=3)}

## Recommendation

For the next M1-M6 figures:

- use **1-12 exact slices** for words and morphemes;
- use **distribution-supported dense-core values** for syllables and phonemes;
- include **p25/p50/p75** and optionally **p10/p50/p90** versions as compact
  low/median/high summaries;
- keep low/mid/high categorical models, but label them as coarse diagnostics.

This is more granular and safer than median-only plotting.
"""


def run_effort_slice_audit(
    *,
    frame: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
    min_rows: int = 500,
    min_age_bins: int = 6,
    min_children: int = 10,
) -> Mapping[str, Path]:
    """Write CSV, figure, Markdown, and HTML effort-slice audit outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    quantiles = effort_quantile_summary(frame)
    distribution = effort_value_distribution(frame)
    by_age = effort_by_age_bin_distribution(frame)
    levels = effort_level_definitions(frame)
    proposals = proposed_fixed_slices(
        frame,
        distribution,
        min_rows=min_rows,
        min_age_bins=min_age_bins,
        min_children=min_children,
    )
    quantiles.to_csv(output_dir / "effort_quantile_summary.csv", index=False)
    distribution.to_csv(output_dir / "effort_value_distribution.csv", index=False)
    by_age.to_csv(output_dir / "effort_by_age_bin_distribution.csv", index=False)
    levels.to_csv(output_dir / "effort_level_definitions.csv", index=False)
    proposals.to_csv(output_dir / "proposed_fixed_effort_slices.csv", index=False)
    fig_path = plot_effort_distributions(distribution, quantiles, fig_dir=fig_dir)
    md = build_markdown(
        quantiles=quantiles,
        distribution=distribution,
        by_age=by_age,
        levels=levels,
        proposals=proposals,
        fig_path=fig_path,
        output_dir=output_dir,
    )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {
        "quantiles": output_dir / "effort_quantile_summary.csv",
        "distribution": output_dir / "effort_value_distribution.csv",
        "by_age": output_dir / "effort_by_age_bin_distribution.csv",
        "levels": output_dir / "effort_level_definitions.csv",
        "proposals": output_dir / "proposed_fixed_effort_slices.csv",
        "figure": fig_path,
        "md": md_path,
        "html": html_path,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--context-k", default="k3")
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--min-rows", type=int, default=500)
    parser.add_argument("--min-age-bins", type=int, default=6)
    parser.add_argument("--min-children", type=int, default=10)
    args = parser.parse_args(argv)
    frame = read_modeling_rows(args.input, context_k=args.context_k, chunksize=args.chunksize)
    outputs = run_effort_slice_audit(
        frame=frame,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        md_path=args.md,
        html_path=args.html,
        min_rows=args.min_rows,
        min_age_bins=args.min_age_bins,
        min_children=args.min_children,
    )
    print(f"[OK] wrote effort quantiles: {outputs['quantiles']}")
    print(f"[OK] wrote effort distributions: {outputs['distribution']}")
    print(f"[OK] wrote proposed fixed slices: {outputs['proposals']}")
    print(f"[OK] wrote effort-slice report: {outputs['html']}")


if __name__ == "__main__":
    main()
