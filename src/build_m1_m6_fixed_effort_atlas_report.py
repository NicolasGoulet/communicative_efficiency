#!/usr/bin/env python3
"""Build an exhaustive M1-M6 fixed-effort atlas report.

This is a report/plotting stage built on top of the fixed-effort M1-M6
analysis outputs. It does not refit models. It creates readable grouped plots:

- words and morphemes: 1-4, 5-8, 9-12 exact fixed slices
- syllables and phonemes: the 12 most frequent exact sizes, split into three
  ordered groups of four

The report includes coefficient tables, column guides, formulas, effort-size
distributions, global marginal adjusted trends, and grouped fixed-slice plots.
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
    from build_m1_m2_utterance_information_deep_dive import EFFORT_MEASURES
    from fit_m1_m6_dual_effort_quick_models import DUAL_MODEL_SPECS, EFFORT_ORDER
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import EFFORT_MEASURES
    from src.fit_m1_m6_dual_effort_quick_models import DUAL_MODEL_SPECS, EFFORT_ORDER
    from src.render_markdown_report import render_markdown_file


DEFAULT_FIXED_OUTPUT_DIR = Path("results/m1_m6_fixed_effort_slices")
DEFAULT_EFFORT_AUDIT_DIR = Path("results/effort_slice_audit")
DEFAULT_OUTPUT_DIR = Path("results/m1_m6_fixed_effort_atlas")
DEFAULT_FIG_DIR = Path("figs/m1_m6_fixed_effort_atlas")
DEFAULT_SOURCE_FIG_DIR = Path("figs/m1_m6_fixed_effort_slices")
DEFAULT_DOC_MD = Path("docs/utterance_information_m1_m6_fixed_effort_atlas.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_m1_m6_fixed_effort_atlas.html")
SIGNIFICANCE_ALPHA = 0.05

MODEL_FORMULAS = {
    "M1": "sum_bits ~ age + effort",
    "M2": "sum_bits ~ age + effort + child identity",
    "M3": "sum_bits ~ age * effort + child identity",
    "M4": "sum_bits ~ age + effort + context_entropy + child identity",
    "M5": "sum_bits ~ age * context_entropy + effort + child identity",
    "M6": "sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity",
}

MODEL_TAKEAWAY_PREFIX = {
    "M1": "Pooled model. Useful as a baseline, but not sufficient for developmental interpretation because it ignores child identity.",
    "M2": "First primary child-adjusted model. If age slopes are negative here, the developmental trend remains after controlling effort and child identity.",
    "M3": "Checks whether the age trend changes across effort values. The fixed-slice plots are especially important here.",
    "M4": "Adds provisional next-token context entropy. This asks whether the child-adjusted age pattern survives context-predictability control.",
    "M5": "Tests whether the entropy association changes with age. Treat this as context-sensitivity evidence only if the interaction is stable.",
    "M6": "Interaction-rich stress test. Useful for robustness, but the interactions should not become the central claim unless they are stable.",
}

COEFFICIENT_COLUMNS = [
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
    "effort_entropy_coef",
    "effort_entropy_p",
]

COLUMN_GUIDE = [
    ("model_id", "Which model family is being summarized, M1 through M6."),
    ("effort_label", "Which effort unit is controlled in that model row: words, morphemes, syllables, or phonemes."),
    ("n_obs", "Number of utterance rows used to fit that model."),
    ("n_children", "Number of distinct children represented in the fitted rows."),
    ("r2_observed_fitted", "In-sample correspondence between observed and fitted total bits; higher means better descriptive fit."),
    ("age_coef", "Estimated monthly age slope for total bits after the controls in that formula. Negative means predicted total bits decrease with age."),
    ("age_p", "p-value for the age slope. Use it as inferential support, not as the visual effect size."),
    ("effort_coef", "Estimated change in total bits for one additional effort unit when effort is continuous."),
    ("effort_p", "p-value for the effort slope."),
    ("entropy_coef", "Estimated change in total bits for one additional bit of next-token context entropy."),
    ("entropy_p", "p-value for the context-entropy slope."),
    ("age_effort_coef", "Interaction: how much the age slope changes for each additional effort unit."),
    ("age_effort_p", "p-value for the age-by-effort interaction."),
    ("age_entropy_coef", "Interaction: how much the age slope changes for each additional bit of context entropy."),
    ("age_entropy_p", "p-value for the age-by-entropy interaction."),
    ("effort_entropy_coef", "Interaction: how much the effort slope changes as context entropy increases."),
    ("effort_entropy_p", "p-value for the effort-by-entropy interaction."),
]

PREDICTOR_GUIDE = {
    "age": "developmental time, measured in months",
    "effort": "utterance production effort in the current effort unit",
    "context_entropy": "next-token context entropy in bits",
    "age_by_effort": "whether the age trend changes as effort increases",
    "age_by_context_entropy": "whether the age trend changes as context entropy increases",
    "effort_by_context_entropy": "whether the effort slope changes as context entropy increases",
}

PREDICTOR_COLUMNS = {
    "age": ("age_coef", "age_p"),
    "effort": ("effort_coef", "effort_p"),
    "context_entropy": ("entropy_coef", "entropy_p"),
    "age_by_effort": ("age_effort_coef", "age_effort_p"),
    "age_by_context_entropy": ("age_entropy_coef", "age_entropy_p"),
    "effort_by_context_entropy": ("effort_entropy_coef", "effort_entropy_p"),
}


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 80, digits: int = 4) -> str:
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


def format_p(value: object) -> str:
    """Format p-values for report tables."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def display_summary(summary: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return a readable model-specific coefficient table."""

    table = summary[summary["model_id"].eq(model_id)][COEFFICIENT_COLUMNS].copy()
    for col in [column for column in table.columns if column.endswith("_p")]:
        table[col] = table[col].map(format_p)
    return table


def split_top12_values(values: Sequence[int]) -> list[tuple[str, list[int]]]:
    """Split ordered representative values into three readable groups."""

    ordered = sorted({int(value) for value in values})
    if not ordered:
        return []
    chunks = np.array_split(np.array(ordered), 3)
    names = ["low representative sizes", "middle representative sizes", "high representative sizes"]
    return [(name, [int(value) for value in chunk.tolist()]) for name, chunk in zip(names, chunks) if len(chunk)]


def effort_bin_definitions(selected: pd.DataFrame) -> pd.DataFrame:
    """Define the grouped fixed-effort panels used by the atlas."""

    rows: list[dict[str, object]] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        if effort_col in {"nb_words", "nb_morphemes"}:
            bins = [
                ("1-4", [1, 2, 3, 4], "Exact values 1-4."),
                ("5-8", [5, 6, 7, 8], "Exact values 5-8."),
                ("9-12", [9, 10, 11, 12], "Exact values 9-12."),
            ]
        else:
            top = selected[
                selected["effort_col"].eq(effort_col)
                & selected["proposal_set"].eq("top_frequency_12")
            ]["fixed_effort_value"].astype(int)
            bins = [
                (
                    name,
                    values,
                    "Ordered split of the 12 most frequent exact effort values.",
                )
                for name, values in split_top12_values(top.tolist())
            ]
        for label, values, rule in bins:
            rows.append(
                {
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "atlas_bin": label,
                    "fixed_values": ", ".join(str(value) for value in values),
                    "n_fixed_values": len(values),
                    "rule": rule,
                }
            )
    return pd.DataFrame(rows)


def distribution_for_atlas_bins(
    distribution: pd.DataFrame,
    bin_defs: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize row counts for the atlas bins."""

    rows: list[dict[str, object]] = []
    totals = distribution.groupby("effort_col")["rows"].sum().to_dict()
    for item in bin_defs.to_dict("records"):
        values = [int(value.strip()) for value in str(item["fixed_values"]).split(",") if value.strip()]
        sub = distribution[
            distribution["effort_col"].eq(item["effort_col"])
            & distribution["effort_value"].astype(int).isin(values)
        ].copy()
        rows.append(
            {
                "effort_label": item["effort_label"],
                "atlas_bin": item["atlas_bin"],
                "fixed_values": item["fixed_values"],
                "rows": int(sub["rows"].sum()),
                "pct_effort_rows": float(sub["rows"].sum() / totals.get(item["effort_col"], math.nan)),
                "n_children_max": int(sub["n_children"].max()) if not sub.empty else 0,
                "n_age_bins_max": int(sub["n_age_bins"].max()) if not sub.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def distribution_by_age_bin(
    by_age: pd.DataFrame,
    bin_defs: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize atlas-bin row counts across age bins."""

    rows: list[dict[str, object]] = []
    for item in bin_defs.to_dict("records"):
        values = [int(value.strip()) for value in str(item["fixed_values"]).split(",") if value.strip()]
        sub = by_age[
            by_age["effort_col"].eq(item["effort_col"])
            & by_age["effort_value"].astype(int).isin(values)
        ].copy()
        if sub.empty:
            continue
        grouped = sub.groupby("age_bin", observed=True)["rows"].sum().reset_index()
        for row in grouped.to_dict("records"):
            rows.append(
                {
                    "effort_label": item["effort_label"],
                    "atlas_bin": item["atlas_bin"],
                    "fixed_values": item["fixed_values"],
                    "age_bin": row["age_bin"],
                    "rows": int(row["rows"]),
                }
            )
    return pd.DataFrame(rows)


def plot_atlas_bin_distribution(bin_distribution: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot overall row support for each atlas bin."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(14, 7))
    data = bin_distribution.copy()
    data["label"] = data["effort_label"] + "\n" + data["atlas_bin"]
    sns.barplot(data=data, x="label", y="rows", hue="effort_label", dodge=False, ax=ax)
    ax.set_title("Utterance rows represented by each atlas effort bin")
    ax.set_xlabel("Effort bin")
    ax.set_ylabel("Rows")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Effort unit", loc="upper right")
    fig.tight_layout()
    out = fig_dir / "atlas_effort_bin_distribution.png"
    fig.savefig(out, dpi=230)
    fig.savefig(fig_dir / "atlas_effort_bin_distribution.pdf")
    plt.close(fig)
    return out


def plot_atlas_bin_distribution_by_age(by_age_distribution: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot row support over age bins for each effort bin."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    efforts = [label for _, label in EFFORT_MEASURES]
    fig, axes = plt.subplots(len(efforts), 1, figsize=(14, 18), sharex=True)
    for ax, effort_label in zip(axes, efforts):
        sub = by_age_distribution[by_age_distribution["effort_label"].eq(effort_label)].copy()
        if sub.empty:
            ax.axis("off")
            continue
        sns.lineplot(
            data=sub,
            x="age_bin",
            y="rows",
            hue="atlas_bin",
            marker="o",
            ax=ax,
        )
        ax.set_title(effort_label)
        ax.set_xlabel("")
        ax.set_ylabel("Rows")
        ax.tick_params(axis="x", rotation=35)
        ax.legend(title="Effort bin", loc="upper right")
    fig.suptitle("Atlas effort-bin row support by age bin", y=1.002)
    fig.tight_layout()
    out = fig_dir / "atlas_effort_bin_distribution_by_age.png"
    fig.savefig(out, dpi=230, bbox_inches="tight")
    fig.savefig(fig_dir / "atlas_effort_bin_distribution_by_age.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def plot_model_effort_bin_predictions(
    predictions: pd.DataFrame,
    bin_defs: pd.DataFrame,
    *,
    fig_dir: Path,
) -> pd.DataFrame:
    """Plot one three-panel fixed-slice figure for each model and effort unit."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    rows: list[dict[str, object]] = []
    for spec in DUAL_MODEL_SPECS:
        for effort_col, effort_label in EFFORT_MEASURES:
            bins = bin_defs[bin_defs["effort_col"].eq(effort_col)].copy()
            if bins.empty:
                continue
            fig, axes = plt.subplots(1, len(bins), figsize=(5.8 * len(bins), 4.9), sharey=True)
            if len(bins) == 1:
                axes = [axes]
            for ax, item in zip(axes, bins.to_dict("records")):
                values = [int(value.strip()) for value in str(item["fixed_values"]).split(",") if value.strip()]
                sub = predictions[
                    predictions["model_id"].eq(spec.model_id)
                    & predictions["effort_col"].eq(effort_col)
                    & predictions["fixed_effort_value"].astype(int).isin(values)
                ].copy()
                if sub.empty:
                    ax.axis("off")
                    continue
                palette = sns.color_palette("viridis", n_colors=len(values))
                color_map = {value: palette[idx] for idx, value in enumerate(values)}
                for value, group in sub.groupby("fixed_effort_value", sort=True):
                    color = color_map[int(value)]
                    ax.plot(
                        group["age_months"],
                        group["predicted_sum_bits"],
                        color=color,
                        linewidth=2.1,
                        label=str(int(value)),
                    )
                    ci = group[["pred_ci_low", "pred_ci_high"]].apply(pd.to_numeric, errors="coerce")
                    if ci.notna().all(axis=None):
                        ax.fill_between(
                            group["age_months"].to_numpy(dtype=float),
                            ci["pred_ci_low"].to_numpy(dtype=float),
                            ci["pred_ci_high"].to_numpy(dtype=float),
                            color=color,
                            alpha=0.08,
                            linewidth=0,
                        )
                ax.set_title(f"{item['atlas_bin']}\nvalues: {item['fixed_values']}")
                ax.set_xlabel("Age in months")
                ax.grid(alpha=0.18)
                ax.legend(title="Fixed value", fontsize=8, title_fontsize=9)
            axes[0].set_ylabel("Predicted total bits")
            fig.suptitle(f"{spec.model_id}: {spec.model_title} | {effort_label}", y=1.05)
            fig.tight_layout()
            stem = f"{spec.model_id.lower()}_{effort_col}_atlas_bins"
            out = fig_dir / f"{stem}.png"
            fig.savefig(out, dpi=230, bbox_inches="tight")
            fig.savefig(fig_dir / f"{stem}.pdf", bbox_inches="tight")
            plt.close(fig)
            rows.append(
                {
                    "model_id": spec.model_id,
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "figure": str(out),
                }
            )
    return pd.DataFrame(rows)


def fixed_slice_slopes(predictions: pd.DataFrame, bin_defs: pd.DataFrame) -> pd.DataFrame:
    """Estimate descriptive age slopes for every plotted fixed-effort line."""

    if predictions.empty:
        return pd.DataFrame()
    value_to_bin: dict[tuple[str, int], str] = {}
    for row in bin_defs.to_dict("records"):
        values = [int(value.strip()) for value in str(row["fixed_values"]).split(",") if value.strip()]
        for value in values:
            value_to_bin[(str(row["effort_col"]), value)] = str(row["atlas_bin"])
    rows: list[dict[str, object]] = []
    keys = ["model_id", "model_title", "effort_col", "effort_label", "fixed_effort_value"]
    for key, group in predictions.groupby(keys, sort=True):
        model_id, model_title, effort_col, effort_label, fixed_value = key
        ages = group["age_months"].to_numpy(dtype=float)
        bits = group["predicted_sum_bits"].to_numpy(dtype=float)
        if len(np.unique(ages)) < 2:
            slope = math.nan
        else:
            slope = float(np.polyfit(ages, bits, 1)[0])
        rows.append(
            {
                "model_id": model_id,
                "model_title": model_title,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "atlas_bin": value_to_bin.get((str(effort_col), int(fixed_value)), ""),
                "fixed_effort_value": int(fixed_value),
                "slope_bits_per_month": slope,
                "slope_bits_per_6_months": slope * 6 if math.isfinite(slope) else math.nan,
                "interpretation": (
                    "downward predicted age trajectory"
                    if math.isfinite(slope) and slope < 0
                    else "upward predicted age trajectory"
                    if math.isfinite(slope) and slope > 0
                    else "flat or unavailable"
                ),
            }
        )
    return pd.DataFrame(rows)


def fixed_slice_slope_summary(slopes: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Summarize fixed-slice slopes for one model."""

    sub = slopes[slopes["model_id"].eq(model_id)].copy()
    if sub.empty:
        return pd.DataFrame()
    return (
        sub.groupby(["effort_label", "atlas_bin"], observed=True)
        .agg(
            n_fixed_slices=("fixed_effort_value", "nunique"),
            negative_slices=("slope_bits_per_month", lambda values: int((values < 0).sum())),
            positive_slices=("slope_bits_per_month", lambda values: int((values > 0).sum())),
            min_slope_bits_per_month=("slope_bits_per_month", "min"),
            max_slope_bits_per_month=("slope_bits_per_month", "max"),
            mean_slope_bits_per_month=("slope_bits_per_month", "mean"),
        )
        .reset_index()
        .sort_values(["effort_label", "atlas_bin"])
    )


def age_slope_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Summarize signs of the age coefficient by model."""

    rows: list[dict[str, object]] = []
    for model_id, group in summary.groupby("model_id", sort=True):
        age = pd.to_numeric(group["age_coef"], errors="coerce").dropna()
        pvals = pd.to_numeric(group.loc[age.index, "age_p"], errors="coerce")
        rows.append(
            {
                "model_id": model_id,
                "negative_age_slopes": int((age < 0).sum()),
                "positive_age_slopes": int((age > 0).sum()),
                "significant_age_slopes_p_lt_05": int((pvals < 0.05).sum()),
                "tested_effort_units": int(age.shape[0]),
                "age_coef_min": float(age.min()) if not age.empty else math.nan,
                "age_coef_max": float(age.max()) if not age.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def model_fit_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Summarize fit and age-sign evidence by model."""

    rows: list[dict[str, object]] = []
    for model_id, group in summary.groupby("model_id", sort=True):
        r2 = pd.to_numeric(group["r2_observed_fitted"], errors="coerce").dropna()
        age = pd.to_numeric(group["age_coef"], errors="coerce")
        age_p = pd.to_numeric(group["age_p"], errors="coerce")
        rows.append(
            {
                "model_id": model_id,
                "mean_r2_observed_fitted": float(r2.mean()) if not r2.empty else math.nan,
                "min_r2_observed_fitted": float(r2.min()) if not r2.empty else math.nan,
                "max_r2_observed_fitted": float(r2.max()) if not r2.empty else math.nan,
                "significant_age_slopes_p_lt_05": int((age_p < SIGNIFICANCE_ALPHA).sum()),
                "negative_age_slopes": int((age < 0).sum()),
                "positive_age_slopes": int((age > 0).sum()),
                "effort_units_tested": int(age.notna().sum()),
            }
        )
    return pd.DataFrame(rows)


def predictor_significance_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Summarize which predictors are significant across model/effort rows."""

    rows: list[dict[str, object]] = []
    for model_id, group in summary.groupby("model_id", sort=True):
        for predictor, (coef_col, p_col) in PREDICTOR_COLUMNS.items():
            if coef_col not in group or p_col not in group:
                continue
            coefs = pd.to_numeric(group[coef_col], errors="coerce")
            pvals = pd.to_numeric(group[p_col], errors="coerce")
            tested = coefs.notna() & pvals.notna()
            significant = tested & (pvals < SIGNIFICANCE_ALPHA)
            if int(tested.sum()) == 0:
                continue
            rows.append(
                {
                    "model_id": model_id,
                    "predictor": predictor,
                    "what_it_represents": PREDICTOR_GUIDE[predictor],
                    "tested_effort_units": int(tested.sum()),
                    "significant_p_lt_05": int(significant.sum()),
                    "negative_significant": int(((coefs < 0) & significant).sum()),
                    "positive_significant": int(((coefs > 0) & significant).sum()),
                    "coef_min": float(coefs[tested].min()),
                    "coef_max": float(coefs[tested].max()),
                }
            )
    return pd.DataFrame(rows)


def hottest_takeaways(
    *,
    fit_summary: pd.DataFrame,
    predictor_summary: pd.DataFrame,
    slope_summary: pd.DataFrame,
) -> list[str]:
    """Return compact data-driven takeaways for the report ending."""

    bullets: list[str] = []
    if not fit_summary.empty:
        best = fit_summary.sort_values("mean_r2_observed_fitted", ascending=False).iloc[0]
        bullets.append(
            "The largest descriptive fit is "
            f"{best['model_id']} with mean in-sample R2={best['mean_r2_observed_fitted']:.3f} "
            "across effort units. This is variance explained by the fitted predictors in the current data, not held-out prediction accuracy."
        )
        m1 = fit_summary[fit_summary["model_id"].eq("M1")]
        m2 = fit_summary[fit_summary["model_id"].eq("M2")]
        if not m1.empty and not m2.empty:
            bullets.append(
                "Adding child identity changes the developmental conclusion: "
                f"M1 has {int(m1['negative_age_slopes'].iloc[0])}/{int(m1['effort_units_tested'].iloc[0])} "
                "negative age slopes, while "
                f"M2 has {int(m2['negative_age_slopes'].iloc[0])}/{int(m2['effort_units_tested'].iloc[0])}. "
                "That is the core reason child-adjusted models are scientifically central here."
            )
    age_rows = predictor_summary[predictor_summary["predictor"].eq("age")]
    if not age_rows.empty:
        age_sig = int(age_rows["significant_p_lt_05"].sum())
        age_tested = int(age_rows["tested_effort_units"].sum())
        age_neg = int(age_rows["negative_significant"].sum())
        bullets.append(
            f"Age is significant in {age_sig}/{age_tested} fitted model-effort rows, "
            f"with {age_neg} significant negative coefficients. Negative means lower predicted total bits with development after the controls in that formula."
        )
    entropy_rows = predictor_summary[predictor_summary["predictor"].eq("context_entropy")]
    if not entropy_rows.empty:
        entropy_sig = int(entropy_rows["significant_p_lt_05"].sum())
        entropy_tested = int(entropy_rows["tested_effort_units"].sum())
        bullets.append(
            f"Context entropy is significant in {entropy_sig}/{entropy_tested} rows where it is included. "
            "This supports keeping context information as a candidate control/predictor, but it remains tied to the current entropy-estimation method."
        )
    if not slope_summary.empty:
        total_slices = int(slope_summary["n_fixed_slices"].sum())
        negative_slices = int(slope_summary["negative_slices"].sum())
        bullets.append(
            f"Across the plotted fixed-effort slices, {negative_slices}/{total_slices} exact conditional age trajectories slope downward. "
            "These slice slopes are descriptive prediction summaries, useful for checking whether the global conclusion depends on a particular effort value."
        )
    return bullets


def model_takeaway(summary: pd.DataFrame, model_id: str) -> str:
    """Create a short model-level takeaway from age coefficients."""

    group = summary[summary["model_id"].eq(model_id)].copy()
    age = pd.to_numeric(group["age_coef"], errors="coerce")
    pvals = pd.to_numeric(group["age_p"], errors="coerce")
    negative = int((age < 0).sum())
    positive = int((age > 0).sum())
    significant = int((pvals < 0.05).sum())
    return (
        f"{MODEL_TAKEAWAY_PREFIX[model_id]} In this run, {negative}/5 effort-unit "
        f"age slopes are negative, {positive}/5 are positive, and {significant}/5 "
        "age slopes have p<.05."
    )


def build_atlas_markdown(
    *,
    summary: pd.DataFrame,
    bin_defs: pd.DataFrame,
    bin_distribution: pd.DataFrame,
    age_bin_distribution: pd.DataFrame,
    fit_summary: pd.DataFrame,
    predictor_summary: pd.DataFrame,
    slopes: pd.DataFrame,
    figure_manifest: pd.DataFrame,
    distribution_fig: Path,
    age_distribution_fig: Path,
    fixed_output_dir: Path,
    output_dir: Path,
    fig_dir: Path,
    source_fig_dir: Path,
) -> str:
    """Build the exhaustive atlas Markdown."""

    del age_bin_distribution
    column_guide = pd.DataFrame(COLUMN_GUIDE, columns=["column", "how_to_interpret"])
    slope_summary = age_slope_summary(summary)
    slope_bin_summary_all = (
        slopes.groupby(["model_id", "effort_label", "atlas_bin"], observed=True)
        .agg(
            n_fixed_slices=("fixed_effort_value", "nunique"),
            negative_slices=("slope_bits_per_month", lambda values: int((values < 0).sum())),
            positive_slices=("slope_bits_per_month", lambda values: int((values > 0).sum())),
        )
        .reset_index()
        if not slopes.empty
        else pd.DataFrame()
    )
    hot_bullets = hottest_takeaways(
        fit_summary=fit_summary,
        predictor_summary=predictor_summary,
        slope_summary=slope_bin_summary_all,
    )
    lines: list[str] = []
    for spec in DUAL_MODEL_SPECS:
        model_id = spec.model_id
        lines.append(f"## {model_id}: {spec.model_title}\n")
        lines.append(f"**Question.** {spec.question}\n")
        lines.append(f"**Formula.** `{MODEL_FORMULAS[model_id]}`\n")
        lines.append(f"**Takeaway.** {model_takeaway(summary, model_id)}\n")
        lines.append("**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.\n")
        lines.append(markdown_table(display_summary(summary, model_id), max_rows=10, digits=3))
        model_slopes = fixed_slice_slope_summary(slopes, model_id)
        if not model_slopes.empty:
            lines.append("\n**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.\n")
            lines.append(markdown_table(model_slopes, max_rows=30, digits=3))
        marginal = source_fig_dir / f"{model_id.lower()}_marginal_adjusted_global_trends.png"
        if marginal.exists():
            lines.append("\n### Global marginal adjusted trend\n")
            lines.append("How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?\n")
            lines.append(f"![{model_id} global marginal adjusted trend](../{marginal})\n")
        lines.append("\n### Fixed effort slices by effort unit\n")
        lines.append("Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.\n")
        for _, effort_label in EFFORT_MEASURES:
            row = figure_manifest[
                figure_manifest["model_id"].eq(model_id)
                & figure_manifest["effort_label"].eq(effort_label)
            ]
            if row.empty:
                continue
            path = Path(row["figure"].iloc[0])
            lines.append(f"#### {effort_label}\n")
            lines.append("How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.\n")
            lines.append(f"![{model_id} {effort_label} fixed slices](../{path})\n")

    return f"""# Exhaustive Fixed-Effort Atlas For M1-M6

This is an internal review report. It replaces median-only interpretation with
three complementary views:

1. coefficient tables for the fitted M1-M6 models;
2. global marginal adjusted age trends that average over observed effort,
   children, and context rows;
3. exact fixed-effort slices grouped into readable panels.

The report does **not** refit models. It reads:

```text
{fixed_output_dir / "fixed_effort_model_summary.csv"}
{fixed_output_dir / "marginal_adjusted_predictions.csv"}
{fixed_output_dir / "fixed_effort_predictions.csv"}
{fixed_output_dir / "selected_fixed_effort_values.csv"}
```

## Statistical Framing

This follows the Advanced Data Analytics guidance checked locally on
2026-06-09:

- `sum_bits` is a continuous outcome;
- utterances are repeated within children, so child identity matters;
- prediction summaries and inference are separate objects;
- effort measures are highly correlated, so each model uses one effort unit at
  a time;
- fixed-effort slices are prediction views, not separate fitted models.

The surprising/core result to watch is the sign change after child identity is
controlled: pooled models can look weak or upward, while child-adjusted models
show a downward age trend, meaning children become less surprising over time
after effort and child identity are controlled.

## Table Column Guide

{markdown_table(column_guide, max_rows=40)}

## Age-Slope Summary

{markdown_table(slope_summary, digits=3)}

## Variance Explained Summary

How to read: `mean_r2_observed_fitted` is the average in-sample R2 across the
five effort-unit versions of a model. It describes how much observed variation
in total utterance bits is captured by the fitted predictors in these rows. It
is not held-out predictive accuracy.

{markdown_table(fit_summary, digits=3)}

## Predictor Significance Summary

How to read: each row asks whether a predictor is significant across the
effort-unit versions where it appears. `significant_p_lt_05` counts how many
effort-unit models have p<.05 for that predictor. `coef_min` and `coef_max`
show the range of estimated coefficients across effort units.

{markdown_table(predictor_summary, max_rows=80, digits=3)}

## Effort Bin Definitions

{markdown_table(bin_defs, max_rows=30)}

## Effort Bin Row Support

The next table and plots show how many real child utterances support each bin.
This matters because fixed-effort slices should be interpreted more cautiously
when they represent fewer rows or fewer age bins.

{markdown_table(bin_distribution, max_rows=30, digits=3)}

![Atlas effort bin distribution](../{distribution_fig})

![Atlas effort bin distribution by age](../{age_distribution_fig})

## Model Sections

{chr(10).join(lines)}

## Hottest Takeaways For The Research Question

{chr(10).join(f"- {bullet}" for bullet in hot_bullets)}

## Saved Atlas Outputs

```text
{output_dir / "atlas_effort_bin_definitions.csv"}
{output_dir / "atlas_effort_bin_distribution.csv"}
{output_dir / "atlas_effort_bin_distribution_by_age.csv"}
{output_dir / "atlas_model_fit_summary.csv"}
{output_dir / "atlas_predictor_significance_summary.csv"}
{output_dir / "atlas_fixed_slice_slopes.csv"}
{output_dir / "atlas_figure_manifest.csv"}
{fig_dir}/
```
"""


def build_fixed_effort_atlas(
    *,
    fixed_output_dir: Path,
    effort_audit_dir: Path,
    output_dir: Path,
    fig_dir: Path,
    source_fig_dir: Path,
    md_path: Path,
    html_path: Path,
) -> Mapping[str, Path]:
    """Build the exhaustive fixed-effort atlas."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(fixed_output_dir / "fixed_effort_model_summary.csv")
    predictions = pd.read_csv(fixed_output_dir / "fixed_effort_predictions.csv")
    selected = pd.read_csv(fixed_output_dir / "selected_fixed_effort_values.csv")
    distribution = pd.read_csv(effort_audit_dir / "effort_value_distribution.csv")
    by_age = pd.read_csv(effort_audit_dir / "effort_by_age_bin_distribution.csv")

    bin_defs = effort_bin_definitions(selected)
    bin_distribution = distribution_for_atlas_bins(distribution, bin_defs)
    by_age_distribution = distribution_by_age_bin(by_age, bin_defs)
    distribution_fig = plot_atlas_bin_distribution(bin_distribution, fig_dir)
    by_age_fig = plot_atlas_bin_distribution_by_age(by_age_distribution, fig_dir)
    figure_manifest = plot_model_effort_bin_predictions(predictions, bin_defs, fig_dir=fig_dir)
    slopes = fixed_slice_slopes(predictions, bin_defs)
    fit_summary = model_fit_summary(summary)
    predictor_summary = predictor_significance_summary(summary)

    bin_defs.to_csv(output_dir / "atlas_effort_bin_definitions.csv", index=False)
    bin_distribution.to_csv(output_dir / "atlas_effort_bin_distribution.csv", index=False)
    by_age_distribution.to_csv(output_dir / "atlas_effort_bin_distribution_by_age.csv", index=False)
    fit_summary.to_csv(output_dir / "atlas_model_fit_summary.csv", index=False)
    predictor_summary.to_csv(output_dir / "atlas_predictor_significance_summary.csv", index=False)
    slopes.to_csv(output_dir / "atlas_fixed_slice_slopes.csv", index=False)
    figure_manifest.to_csv(output_dir / "atlas_figure_manifest.csv", index=False)

    md = build_atlas_markdown(
        summary=summary,
        bin_defs=bin_defs,
        bin_distribution=bin_distribution,
        age_bin_distribution=by_age_distribution,
        fit_summary=fit_summary,
        predictor_summary=predictor_summary,
        slopes=slopes,
        figure_manifest=figure_manifest,
        distribution_fig=distribution_fig,
        age_distribution_fig=by_age_fig,
        fixed_output_dir=fixed_output_dir,
        output_dir=output_dir,
        fig_dir=fig_dir,
        source_fig_dir=source_fig_dir,
    )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {
        "md": md_path,
        "html": html_path,
        "bin_defs": output_dir / "atlas_effort_bin_definitions.csv",
        "bin_distribution": output_dir / "atlas_effort_bin_distribution.csv",
        "by_age_distribution": output_dir / "atlas_effort_bin_distribution_by_age.csv",
        "fit_summary": output_dir / "atlas_model_fit_summary.csv",
        "predictor_summary": output_dir / "atlas_predictor_significance_summary.csv",
        "slopes": output_dir / "atlas_fixed_slice_slopes.csv",
        "figure_manifest": output_dir / "atlas_figure_manifest.csv",
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-output-dir", type=Path, default=DEFAULT_FIXED_OUTPUT_DIR)
    parser.add_argument("--effort-audit-dir", type=Path, default=DEFAULT_EFFORT_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--source-fig-dir", type=Path, default=DEFAULT_SOURCE_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    args = parser.parse_args(argv)
    outputs = build_fixed_effort_atlas(
        fixed_output_dir=args.fixed_output_dir,
        effort_audit_dir=args.effort_audit_dir,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        source_fig_dir=args.source_fig_dir,
        md_path=args.md,
        html_path=args.html,
    )
    print(f"[OK] wrote fixed-effort atlas Markdown: {outputs['md']}")
    print(f"[OK] wrote fixed-effort atlas HTML: {outputs['html']}")
    print(f"[OK] wrote atlas figure manifest: {outputs['figure_manifest']}")


if __name__ == "__main__":
    main()
