#!/usr/bin/env python3
"""Fit M1-M6 and predict many fixed-effort slices.

The earlier compact report plotted one continuous-effort line at the median.
That was only one conditional slice of the fitted model. This script keeps the
same fitted model families, but creates prediction grids for many exact effort
values:

- words: exact values 1-12
- morphemes: exact values 1-12
- syllables / phonemes: data-supported values from the effort-slice audit
- quantile anchors: p25/p50/p75 and p10/p50/p90

The models are fit on all eligible real child utterances. The fixed effort
values only affect prediction grids and plots.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from build_effort_slice_audit_report import (
        DEFAULT_OUTPUT_DIR as DEFAULT_AUDIT_OUTPUT_DIR,
        effort_value_distribution,
        proposed_fixed_slices,
    )
    from build_m1_m2_utterance_information_deep_dive import DEFAULT_INPUT, EFFORT_MEASURES, read_modeling_rows
    from fit_m1_m6_dual_effort_quick_models import (
        DUAL_MODEL_SPECS,
        EFFORT_ORDER,
        average_child_predictions,
        fit_dual_models,
        model_summary_rows,
    )
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_effort_slice_audit_report import (
        DEFAULT_OUTPUT_DIR as DEFAULT_AUDIT_OUTPUT_DIR,
        effort_value_distribution,
        proposed_fixed_slices,
    )
    from src.build_m1_m2_utterance_information_deep_dive import DEFAULT_INPUT, EFFORT_MEASURES, read_modeling_rows
    from src.fit_m1_m6_dual_effort_quick_models import (
        DUAL_MODEL_SPECS,
        EFFORT_ORDER,
        average_child_predictions,
        fit_dual_models,
        model_summary_rows,
    )
    from src.render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/m1_m6_fixed_effort_slices")
DEFAULT_FIG_DIR = Path("figs/m1_m6_fixed_effort_slices")
DEFAULT_DOC_MD = Path("docs/utterance_information_m1_m6_fixed_effort_slices.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_m1_m6_fixed_effort_slices.html")
DEFAULT_PROPOSAL_CSV = DEFAULT_AUDIT_OUTPUT_DIR / "proposed_fixed_effort_slices.csv"

PLOT_GROUPS = {
    "top_frequency_12": "Top 12 most frequent exact effort sizes",
    "granular_primary": "Words/morphemes 1-12; syllables/phonemes data-supported dense core",
    "primary_anchors_p25_p50_p75": "Primary low/median/high fixed slices",
    "wide_anchors_p10_p50_p90": "Wide low/median/high fixed slices",
}
MAX_GRANULAR_PLOT_LINES = 8
DEFAULT_MARGINAL_SAMPLE_SIZE = 8_000


def ensure_proposals(frame: pd.DataFrame, proposal_csv: Path) -> pd.DataFrame:
    """Read proposal CSV or derive it from the current frame."""

    if proposal_csv.exists():
        return pd.read_csv(proposal_csv)
    distribution = effort_value_distribution(frame)
    proposal_csv.parent.mkdir(parents=True, exist_ok=True)
    proposals = proposed_fixed_slices(frame, distribution)
    proposals.to_csv(proposal_csv, index=False)
    return proposals


def selected_fixed_values(proposals: pd.DataFrame) -> pd.DataFrame:
    """Select fixed values used by the M1-M6 plots."""

    support = proposals["meets_support_rule"].map(
        lambda value: str(value).strip().lower() in {"true", "1", "yes"}
    )
    rows: list[pd.DataFrame] = []
    mandatory = proposals[
        proposals["proposal_set"].eq("requested_dense_1_12")
        & proposals["effort_col"].isin(["nb_words", "nb_morphemes"])
    ].copy()
    mandatory["plot_group"] = "granular_primary"
    rows.append(mandatory)

    dense = proposals[
        proposals["proposal_set"].eq("data_supported_dense_core")
        & proposals["effort_col"].isin(
            ["nb_syllables_cmu_or_pkg", "nb_syllables_pkg", "nb_phonemes"]
        )
        & support
    ].copy()
    dense["plot_group"] = "granular_primary"
    rows.append(dense)

    primary = proposals[proposals["proposal_set"].eq("primary_low_median_high_p25_p50_p75")].copy()
    primary["plot_group"] = "primary_anchors_p25_p50_p75"
    rows.append(primary)

    wide = proposals[proposals["proposal_set"].eq("wide_low_median_high_p10_p50_p90")].copy()
    wide["plot_group"] = "wide_anchors_p10_p50_p90"
    rows.append(wide)

    top = proposals[proposals["proposal_set"].eq("top_frequency_12")].copy()
    top["plot_group"] = "top_frequency_12"
    rows.append(top)

    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return (
        out.drop_duplicates(subset=["effort_col", "fixed_effort_value", "plot_group"])
        .sort_values(["plot_group", "effort_col", "fixed_effort_value"])
        .reset_index(drop=True)
    )


def fixed_effort_prediction_grid(
    bundle,
    model_frame: pd.DataFrame,
    fixed_values: pd.DataFrame,
    *,
    n_points: int,
) -> pd.DataFrame:
    """Predict one fitted continuous-effort bundle at many exact effort values."""

    if bundle.result is None or model_frame.empty or fixed_values.empty:
        return pd.DataFrame()
    ages = np.linspace(
        model_frame["age_months"].quantile(0.02),
        model_frame["age_months"].quantile(0.98),
        n_points,
    )
    parts: list[pd.DataFrame] = []
    child_ids = sorted(model_frame["child_id"].astype(str).unique())
    for proposal in fixed_values.to_dict("records"):
        fixed_value = float(proposal["fixed_effort_value"])
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - bundle.age_mean,
                "effort_value": fixed_value,
                "effort_c": fixed_value - bundle.effort_mean,
                "context_entropy_bits": bundle.entropy_mean,
                "context_entropy_c": 0.0,
            }
        )
        pred = average_child_predictions(bundle, base, child_ids)
        pred["fixed_effort_value"] = int(fixed_value)
        pred["proposal_set"] = proposal["proposal_set"]
        pred["plot_group"] = proposal["plot_group"]
        pred["proposal_reason"] = proposal.get("reason", "")
        pred["support_rows"] = proposal.get("rows", math.nan)
        pred["support_children"] = proposal.get("n_children", math.nan)
        pred["support_age_bins"] = proposal.get("n_age_bins", math.nan)
        parts.append(pred)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fixed_effort_predictions(
    frame: pd.DataFrame,
    selected_values: pd.DataFrame,
    *,
    n_points: int,
) -> tuple[list[object], dict[tuple[str, str], pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Fit M1-M6 and generate exact fixed-effort predictions."""

    bundles, model_frames = fit_dual_models(frame)
    continuous_bundles = [bundle for bundle in bundles if bundle.effort_strategy == "continuous"]
    summary = model_summary_rows(continuous_bundles)
    parts: list[pd.DataFrame] = []
    for bundle in continuous_bundles:
        effort_values = selected_values[selected_values["effort_col"].eq(bundle.effort_col)].copy()
        pred = fixed_effort_prediction_grid(
            bundle,
            model_frames.get((bundle.model_id, bundle.effort_col), pd.DataFrame()),
            effort_values,
            n_points=n_points,
        )
        if pred.empty:
            continue
        pred["model_id"] = bundle.model_id
        pred["model_title"] = bundle.model_title
        pred["question"] = bundle.question
        pred["effort_col"] = bundle.effort_col
        pred["effort_label"] = bundle.effort_label
        pred["readable_formula"] = bundle.readable_formula
        parts.append(pred)
    predictions = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    return continuous_bundles, model_frames, summary, predictions


def marginal_adjusted_predictions(
    bundles: Sequence[object],
    model_frames: Mapping[tuple[str, str], pd.DataFrame],
    *,
    n_points: int,
    sample_size: int,
    seed: int = 20260609,
) -> pd.DataFrame:
    """Average model predictions over the observed effort/child distribution.

    This is the single global adjusted age trend. For every target age, we keep
    a standardization sample's observed effort values, child IDs, and context
    entropy values, change only age, predict, then average predictions.
    """

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = getattr(bundle, "result", None)
        model_frame = model_frames.get((bundle.model_id, bundle.effort_col), pd.DataFrame())
        if result is None or model_frame.empty:
            continue
        standard = model_frame.copy()
        if len(standard) > sample_size:
            standard = standard.sample(sample_size, random_state=seed)
        standard = standard.reset_index(drop=True)
        ages = np.linspace(
            model_frame["age_months"].quantile(0.02),
            model_frame["age_months"].quantile(0.98),
            n_points,
        )
        for age in ages:
            new = standard.copy()
            new["age_months"] = age
            new["age_c"] = age - bundle.age_mean
            predicted = np.asarray(result.predict(new), dtype=float)
            rows.append(
                {
                    "model_id": bundle.model_id,
                    "model_title": bundle.model_title,
                    "question": bundle.question,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "age_months": float(age),
                    "predicted_sum_bits": float(np.mean(predicted)),
                    "standardization_rows": int(len(standard)),
                    "standardization": "row-weighted observed effort, child, and context distribution",
                    "readable_formula": bundle.readable_formula,
                }
            )
    return pd.DataFrame(rows)


def readable_plot_values(values: Sequence[int], *, plot_group: str) -> list[int]:
    """Return a readable subset of fixed values for one plot panel.

    The prediction CSV keeps every selected fixed value. The plot layer caps
    dense panels so the report remains interpretable.
    """

    unique = sorted({int(value) for value in values})
    if plot_group != "granular_primary" or len(unique) <= MAX_GRANULAR_PLOT_LINES:
        return unique
    positions = np.linspace(0, len(unique) - 1, MAX_GRANULAR_PLOT_LINES)
    selected = [unique[int(round(pos))] for pos in positions]
    return sorted(set(selected))


def displayed_fixed_values(selected_values: pd.DataFrame) -> pd.DataFrame:
    """Document which fixed values are displayed in plots."""

    rows: list[dict[str, object]] = []
    for (plot_group, effort_col, effort_label), group in selected_values.groupby(
        ["plot_group", "effort_col", "effort_label"],
        sort=True,
    ):
        all_values = sorted(int(value) for value in group["fixed_effort_value"].unique())
        shown_values = readable_plot_values(all_values, plot_group=str(plot_group))
        rows.append(
            {
                "plot_group": plot_group,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "all_fixed_values": ", ".join(str(value) for value in all_values),
                "displayed_fixed_values": ", ".join(str(value) for value in shown_values),
                "n_all_values": len(all_values),
                "n_displayed_values": len(shown_values),
                "display_note": "full values saved in prediction CSV"
                if len(shown_values) < len(all_values)
                else "all values displayed",
            }
        )
    return pd.DataFrame(rows)


def plot_fixed_slice_predictions(predictions: pd.DataFrame, *, fig_dir: Path) -> list[Path]:
    """Plot all M1-M6 fixed-slice prediction groups."""

    if predictions.empty:
        return []
    fig_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for spec in DUAL_MODEL_SPECS:
        for plot_group, description in PLOT_GROUPS.items():
            sub = predictions[
                predictions["model_id"].eq(spec.model_id)
                & predictions["plot_group"].eq(plot_group)
            ].copy()
            if sub.empty:
                continue
            fig, axes = plt.subplots(1, 5, figsize=(21, 4.8), sharey=True)
            for ax, effort_label in zip(axes, EFFORT_ORDER):
                panel = sub[sub["effort_label"].eq(effort_label)].copy()
                if panel.empty:
                    ax.axis("off")
                    continue
                all_values = sorted(int(value) for value in panel["fixed_effort_value"].unique())
                values = readable_plot_values(all_values, plot_group=plot_group)
                panel = panel[panel["fixed_effort_value"].astype(int).isin(values)].copy()
                palette = sns.color_palette("viridis", n_colors=len(values))
                color_map = {value: palette[idx] for idx, value in enumerate(values)}
                for value, group in panel.groupby("fixed_effort_value", sort=True):
                    color = color_map[int(value)]
                    ax.plot(
                        group["age_months"],
                        group["predicted_sum_bits"],
                        color=color,
                        linewidth=1.8 if len(values) <= 12 else 1.25,
                        alpha=0.92 if len(values) <= 12 else 0.74,
                        label=str(int(value)),
                    )
                    if len(values) <= 12:
                        ci = group[["pred_ci_low", "pred_ci_high"]].apply(pd.to_numeric, errors="coerce")
                        if ci.notna().all(axis=None):
                            ax.fill_between(
                                group["age_months"].to_numpy(dtype=float),
                                ci["pred_ci_low"].to_numpy(dtype=float),
                                ci["pred_ci_high"].to_numpy(dtype=float),
                                color=color,
                                alpha=0.06,
                                linewidth=0,
                            )
                ax.set_title(effort_label)
                ax.set_xlabel("Age in months")
                ax.grid(alpha=0.18)
                if len(values) <= 12:
                    ax.legend(title="Fixed value", fontsize=7, title_fontsize=8, ncol=2)
                if len(values) < len(all_values):
                    ax.text(
                        0.02,
                        0.98,
                        f"{len(values)}/{len(all_values)} values shown\nfull set in CSV",
                        transform=ax.transAxes,
                        va="top",
                        ha="left",
                        fontsize=9,
                        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#cccccc", "alpha": 0.9},
                    )
            axes[0].set_ylabel("Predicted total bits")
            fig.suptitle(f"{spec.model_id}: {spec.model_title}\n{description}", y=1.05)
            fig.tight_layout()
            stem = f"{spec.model_id.lower()}_{plot_group}_fixed_effort_slices"
            path = fig_dir / f"{stem}.png"
            fig.savefig(path, dpi=230, bbox_inches="tight")
            fig.savefig(fig_dir / f"{stem}.pdf", bbox_inches="tight")
            plt.close(fig)
            outputs.append(path)
    return outputs


def plot_marginal_adjusted_predictions(predictions: pd.DataFrame, *, fig_dir: Path) -> list[Path]:
    """Plot one global adjusted line per model and effort unit."""

    if predictions.empty:
        return []
    fig_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for spec in DUAL_MODEL_SPECS:
        sub = predictions[predictions["model_id"].eq(spec.model_id)].copy()
        if sub.empty:
            continue
        fig, axes = plt.subplots(1, 5, figsize=(20, 4.6), sharey=True)
        for ax, effort_label in zip(axes, EFFORT_ORDER):
            panel = sub[sub["effort_label"].eq(effort_label)].copy()
            if panel.empty:
                ax.axis("off")
                continue
            ax.plot(
                panel["age_months"],
                panel["predicted_sum_bits"],
                color="#222222",
                linewidth=2.7,
            )
            ax.set_title(effort_label)
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
            ax.text(
                0.02,
                0.98,
                "global adjusted line",
                transform=ax.transAxes,
                va="top",
                ha="left",
                fontsize=9,
                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#cccccc", "alpha": 0.9},
            )
        axes[0].set_ylabel("Predicted total bits")
        fig.suptitle(f"{spec.model_id}: {spec.model_title}\nMarginal adjusted global trend", y=1.04)
        fig.tight_layout()
        stem = f"{spec.model_id.lower()}_marginal_adjusted_global_trends"
        path = fig_dir / f"{stem}.png"
        fig.savefig(path, dpi=230, bbox_inches="tight")
        fig.savefig(fig_dir / f"{stem}.pdf", bbox_inches="tight")
        plt.close(fig)
        outputs.append(path)
    return outputs


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 40, digits: int = 4) -> str:
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


def compact_value_table(selected_values: pd.DataFrame) -> pd.DataFrame:
    """Summarize selected fixed values by plot group and effort."""

    rows: list[dict[str, object]] = []
    for (plot_group, effort_label), group in selected_values.groupby(["plot_group", "effort_label"], sort=True):
        values = sorted(int(value) for value in group["fixed_effort_value"].unique())
        rows.append(
            {
                "plot_group": plot_group,
                "effort": effort_label,
                "values": ", ".join(str(value) for value in values),
                "n_values": len(values),
            }
        )
    return pd.DataFrame(rows)


def build_fixed_effort_report(
    *,
    selected_values: pd.DataFrame,
    display_values: pd.DataFrame,
    summary: pd.DataFrame,
    marginal_figure_paths: Sequence[Path],
    fixed_figure_paths: Sequence[Path],
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
) -> Mapping[str, Path]:
    """Write Markdown/HTML report for fixed-effort M1-M6 predictions."""

    value_table = compact_value_table(selected_values)
    display_table = display_values[
        [
            "plot_group",
            "effort_label",
            "displayed_fixed_values",
            "n_displayed_values",
            "n_all_values",
            "display_note",
        ]
    ].copy()
    summary_cols = [
        "model_id",
        "effort_label",
        "n_obs",
        "n_children",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "effort_coef",
        "effort_p",
        "entropy_coef",
        "entropy_p",
        "age_effort_coef",
        "age_effort_p",
        "age_entropy_coef",
        "age_entropy_p",
    ]
    plot_lines = []
    for spec in DUAL_MODEL_SPECS:
        plot_lines.append(f"## {spec.model_id}: {spec.model_title}\n")
        plot_lines.append(f"Question: {spec.question}\n")
        marginal_matches = [
            path for path in marginal_figure_paths if path.name.startswith(f"{spec.model_id.lower()}_marginal")
        ]
        if marginal_matches:
            rel = Path("..") / marginal_matches[0]
            plot_lines.append("### Global adjusted trend\n")
            plot_lines.append(
                "How to read: this is the single global age trend after accounting "
                "for effort and child/context composition by averaging predictions "
                "over observed rows. It is not restricted to one length.\n"
            )
            plot_lines.append(f"![{spec.model_id} marginal adjusted trend]({rel})\n")
        plot_lines.append(
            "How to read: each line is a prediction from the same fitted model, "
            "but at a different exact fixed effort value. The model was fit on "
            "all utterance lengths; only the prediction slice changes.\n"
        )
        for plot_group, description in PLOT_GROUPS.items():
            matches = [
                path for path in fixed_figure_paths if path.name.startswith(f"{spec.model_id.lower()}_{plot_group}")
            ]
            if not matches:
                continue
            rel = Path("..") / matches[0]
            plot_lines.append(f"### {description}\n")
            plot_lines.append(f"![{spec.model_id} {plot_group}]({rel})\n")
    md = f"""# M1-M6 Fixed-Effort Slice Predictions

This report replaces the insufficient median-only view. It repeats the M1-M6
continuous-effort prediction stage across many exact fixed effort values.

Important: the models are still fit on all eligible real child utterances. The
fixed values only define the prediction lines.

Why the script refits: the previous reports saved coefficient CSVs and figures,
but not serialized model objects. To generate new prediction grids, we refit the
same formulas once per model/effort unit, then write new predictions. We do not
fit separate models for each fixed effort value.

## Outputs

```text
{output_dir / "fixed_effort_model_summary.csv"}
{output_dir / "marginal_adjusted_predictions.csv"}
{output_dir / "fixed_effort_predictions.csv"}
{output_dir / "selected_fixed_effort_values.csv"}
{fig_dir}/
```

## Statistical Checkpoint

This follows the Advanced Data Analytics guidance checked on 2026-06-09:

- outcome is continuous (`sum_bits`);
- rows are repeated within children, so child identity must be handled in the
  model family or uncertainty structure;
- fitting and reporting are separated: run `--stage analysis` for models and
  predictions, and `--stage report` for Markdown/HTML only;
- the single global line is a **marginal adjusted prediction**, not a new
  inferential test;
- fixed-slice lines are conditional prediction views, not separate fitted
  models for each length.

## Selected Fixed Values

{markdown_table(value_table, max_rows=80)}

## Plot Readability Rule

The model predictions are computed for all selected fixed values. The figures
are capped for readability: dense granular panels display at most
{MAX_GRANULAR_PLOT_LINES} representative values per effort unit. The full set
remains in `fixed_effort_predictions.csv`.

{markdown_table(display_table, max_rows=80)}

## Model Summary

{markdown_table(summary[summary_cols], max_rows=40, digits=3)}

{chr(10).join(plot_lines)}
"""
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {"md": md_path, "html": html_path}


def run_fixed_effort_slice_analysis(
    *,
    input_csv: Path,
    proposal_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    chunksize: int,
    n_points: int,
    marginal_sample_size: int,
) -> Mapping[str, Path]:
    """Run the fitting/prediction/plotting stage only."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_modeling_rows(input_csv, context_k=context_k, chunksize=chunksize)
    proposals = ensure_proposals(frame, proposal_csv)
    selected_values = selected_fixed_values(proposals)
    display_values = displayed_fixed_values(selected_values)
    bundles, model_frames, summary, predictions = fixed_effort_predictions(
        frame,
        selected_values,
        n_points=n_points,
    )
    marginal_predictions = marginal_adjusted_predictions(
        bundles,
        model_frames,
        n_points=n_points,
        sample_size=marginal_sample_size,
    )
    selected_values.to_csv(output_dir / "selected_fixed_effort_values.csv", index=False)
    display_values.to_csv(output_dir / "displayed_fixed_effort_values.csv", index=False)
    summary.to_csv(output_dir / "fixed_effort_model_summary.csv", index=False)
    marginal_predictions.to_csv(output_dir / "marginal_adjusted_predictions.csv", index=False)
    predictions.to_csv(output_dir / "fixed_effort_predictions.csv", index=False)
    audit = pd.DataFrame(
        [
            {
                "input_csv": str(input_csv),
                "proposal_csv": str(proposal_csv),
                "context_k": context_k,
                "rows": len(frame),
                "children": frame["child_id"].nunique(),
                "selected_fixed_value_rows": len(selected_values),
                "fitted_model_rows": len(summary),
                "marginal_prediction_rows": len(marginal_predictions),
                "prediction_rows": len(predictions),
            }
        ]
    )
    audit.to_csv(output_dir / "fixed_effort_audit.csv", index=False)
    marginal_figures = plot_marginal_adjusted_predictions(marginal_predictions, fig_dir=fig_dir)
    fixed_figures = plot_fixed_slice_predictions(predictions, fig_dir=fig_dir)
    return {
        "selected_values": output_dir / "selected_fixed_effort_values.csv",
        "display_values": output_dir / "displayed_fixed_effort_values.csv",
        "summary": output_dir / "fixed_effort_model_summary.csv",
        "marginal_predictions": output_dir / "marginal_adjusted_predictions.csv",
        "predictions": output_dir / "fixed_effort_predictions.csv",
        "audit": output_dir / "fixed_effort_audit.csv",
        "fig_dir": fig_dir,
        "marginal_figures": marginal_figures,
        "fixed_figures": fixed_figures,
    }


def build_fixed_effort_report_from_outputs(
    *,
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
) -> Mapping[str, Path]:
    """Render the report from saved CSV/figure artifacts only."""

    selected_values = pd.read_csv(output_dir / "selected_fixed_effort_values.csv")
    display_values = pd.read_csv(output_dir / "displayed_fixed_effort_values.csv")
    summary = pd.read_csv(output_dir / "fixed_effort_model_summary.csv")
    marginal_figures = sorted(fig_dir.glob("*_marginal_adjusted_global_trends.png"))
    fixed_figures = sorted(fig_dir.glob("*_fixed_effort_slices.png"))
    report = build_fixed_effort_report(
        selected_values=selected_values,
        display_values=display_values,
        summary=summary,
        marginal_figure_paths=list(marginal_figures),
        fixed_figure_paths=list(fixed_figures),
        output_dir=output_dir,
        fig_dir=fig_dir,
        md_path=md_path,
        html_path=html_path,
    )
    return report


def fit_and_plot_fixed_effort_slices(
    *,
    input_csv: Path,
    proposal_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
    context_k: str,
    chunksize: int,
    n_points: int,
    marginal_sample_size: int,
) -> Mapping[str, Path]:
    """Run both analysis and report stages."""

    analysis = run_fixed_effort_slice_analysis(
        input_csv=input_csv,
        proposal_csv=proposal_csv,
        output_dir=output_dir,
        fig_dir=fig_dir,
        context_k=context_k,
        chunksize=chunksize,
        n_points=n_points,
        marginal_sample_size=marginal_sample_size,
    )
    report = build_fixed_effort_report_from_outputs(
        output_dir=output_dir,
        fig_dir=fig_dir,
        md_path=md_path,
        html_path=html_path,
    )
    return {
        **analysis,
        "md": report["md"],
        "html": report["html"],
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--proposal-csv", type=Path, default=DEFAULT_PROPOSAL_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--context-k", default="k3")
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--n-points", type=int, default=90)
    parser.add_argument("--marginal-sample-size", type=int, default=DEFAULT_MARGINAL_SAMPLE_SIZE)
    parser.add_argument("--stage", choices=["all", "analysis", "report"], default="all")
    args = parser.parse_args(argv)
    if args.stage in {"all", "analysis"}:
        outputs = run_fixed_effort_slice_analysis(
            input_csv=args.input,
            proposal_csv=args.proposal_csv,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_k=args.context_k,
            chunksize=args.chunksize,
            n_points=args.n_points,
            marginal_sample_size=args.marginal_sample_size,
        )
        print(f"[OK] wrote fixed effort selected values: {outputs['selected_values']}")
        print(f"[OK] wrote fixed effort model summary: {outputs['summary']}")
        print(f"[OK] wrote marginal adjusted predictions: {outputs['marginal_predictions']}")
        print(f"[OK] wrote fixed effort predictions: {outputs['predictions']}")
    if args.stage in {"all", "report"}:
        report = build_fixed_effort_report_from_outputs(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            md_path=args.md,
            html_path=args.html,
        )
        print(f"[OK] wrote fixed effort report: {report['html']}")


if __name__ == "__main__":
    main()
