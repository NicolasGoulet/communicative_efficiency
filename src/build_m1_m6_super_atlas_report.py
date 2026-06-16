#!/usr/bin/env python3
"""Build an exhaustive internal M1-M6 model atlas report.

This report is a synthesis layer. It does not refit the heavy models. It reads
the saved model summaries, fixed-effort slices, context-window atlases,
age-scrambling robustness checks, and existing figures, then writes one
internal Markdown/HTML report with extra cross-atlas overview plots.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/m1_m6_super_atlas")
DEFAULT_FIG_DIR = Path("figs/m1_m6_super_atlas")
DEFAULT_DOC_MD = Path("docs/utterance_information_m1_m6_super_atlas.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_m1_m6_super_atlas.html")

DEEP_DIVE_DIR = Path("results/m1_m2_utterance_information_deep_dive")
DUAL_DIR = Path("results/m1_m6_dual_effort_quick_share")
FIXED_SLICE_DIR = Path("results/m1_m6_fixed_effort_slices")
FIXED_ATLAS_DIR = Path("results/m1_m6_fixed_effort_atlas")
CONTEXT_M1_M6_DIR = Path("results/context_m1_m6_fixed_effort_atlas")
CONTEXT_FIXED_DIR = Path("results/context_fixed_effort_atlas")
ROBUSTNESS_DIR = Path("results/age_scrambling_robustness")

MODEL_ORDER = ["M1", "M2", "M3", "M4", "M5", "M6"]
EFFORT_ORDER = [
    "Words",
    "Morphemes",
    "Syllables: CMU/pkg",
    "Syllables: pkg",
    "Phonemes",
]
EFFORT_NAME_BY_COL = {
    "nb_words": "Words",
    "nb_morphemes": "Morphemes",
    "nb_syllables_cmu_or_pkg": "Syllables: CMU/pkg",
    "nb_syllables_pkg": "Syllables: pkg",
    "nb_phonemes": "Phonemes",
}

FIGURE_SOURCES = [
    (
        "deep_dive",
        "M1-M3 estimator deep dive plus early M4-M6 plots",
        Path("figs/m1_m2_utterance_information_deep_dive"),
    ),
    ("dual_effort", "M1-M6 continuous versus effort-level plots", Path("figs/m1_m6_dual_effort_quick_share")),
    ("fixed_slices", "M1-M6 fixed-effort slice plots", Path("figs/m1_m6_fixed_effort_slices")),
    ("fixed_atlas", "M1-M6 fixed-effort atlas plots", Path("figs/m1_m6_fixed_effort_atlas")),
    ("context_m1_m6", "M1-M6 context-window fixed-effort atlas plots", Path("figs/context_m1_m6_fixed_effort_atlas")),
    ("context_adjunct", "Context-predictor adjunct fixed-effort atlas plots", Path("figs/context_fixed_effort_atlas")),
    ("robustness", "Age-bin bootstrap and scrambling robustness plots", Path("figs/age_scrambling_robustness")),
    ("m2_simple", "Supervisor-facing Model 2 simple plots", Path("figs/m2_simple_plots")),
]

ARTIFACTS = [
    ("deep_fit", "M1/M2 primary fit summary", DEEP_DIVE_DIR / "model_fit_summary.csv"),
    ("deep_coef", "M1/M2 primary coefficient table", DEEP_DIVE_DIR / "model_coefficients.csv"),
    ("expanded", "M1-M3 estimator-family sensitivity summary", DEEP_DIVE_DIR / "expanded_model_family_summary.csv"),
    ("m4_context", "M4 context-entropy sensitivity summary", DEEP_DIVE_DIR / "m4_context_entropy_model_summary.csv"),
    ("m5_m6_saturated", "M5/M6 effort-level exploratory summary", DEEP_DIVE_DIR / "m5_m6_saturated_model_summary.csv"),
    ("dual", "M1-M6 continuous and effort-level model summary", DUAL_DIR / "dual_model_summary.csv"),
    ("fixed_summary", "M1-M6 fixed-effort continuous model summary", FIXED_SLICE_DIR / "fixed_effort_model_summary.csv"),
    ("fixed_predictions", "M1-M6 fixed-effort prediction rows", FIXED_SLICE_DIR / "fixed_effort_predictions.csv"),
    ("atlas_fit", "M1-M6 fixed-effort atlas fit summary", FIXED_ATLAS_DIR / "atlas_model_fit_summary.csv"),
    ("atlas_slopes", "M1-M6 fixed-effort atlas slice slopes", FIXED_ATLAS_DIR / "atlas_fixed_slice_slopes.csv"),
    ("atlas_manifest", "M1-M6 fixed-effort atlas figure manifest", FIXED_ATLAS_DIR / "atlas_figure_manifest.csv"),
    ("context_m1_m6", "Context-window M1-M6 model summary", CONTEXT_M1_M6_DIR / "context_m1_m6_model_summary.csv"),
    ("context_m1_m6_slopes", "Context-window M1-M6 fixed-slice slopes", CONTEXT_M1_M6_DIR / "context_m1_m6_slice_slopes.csv"),
    ("context_m1_m6_manifest", "Context-window M1-M6 figure manifest", CONTEXT_M1_M6_DIR / "context_m1_m6_figure_manifest.csv"),
    ("context_fixed", "Context-predictor adjunct model summary", CONTEXT_FIXED_DIR / "context_fixed_effort_model_summary.csv"),
    ("context_fixed_manifest", "Context-predictor adjunct figure manifest", CONTEXT_FIXED_DIR / "context_fixed_effort_figure_manifest.csv"),
    ("robustness", "Age-bin bootstrap and scrambling summary", ROBUSTNESS_DIR / "age_scrambling_robustness_summary.csv"),
    ("robustness_figures", "Age-bin robustness figure manifest", ROBUSTNESS_DIR / "age_scrambling_figure_manifest.csv"),
    ("robustness_clear_figures", "Clear robustness figure manifest", ROBUSTNESS_DIR / "age_scrambling_clear_figure_manifest.csv"),
]

MODEL_GUIDE = {
    "M1": {
        "title": "Pooled age and effort",
        "question": "Pooling children, does age predict utterance total information after controlling utterance effort?",
        "formula": "sum_bits ~ age + effort",
        "actual": "Main OLS code uses centered `age_c` and `effort_c`; the centered form has the same slope interpretation.",
        "estimator": "Ordinary least squares via `statsmodels.formula.api.ols` is the baseline. Sensitivity rows also include Gaussian GLM, Gamma GLM with log link, and child-clustered OLS standard errors.",
        "random": "No child fixed effects and no random effects in the primary M1. Child clustering changes uncertainty only.",
        "meaning": "M1 is a baseline and a warning light. It shows the age-effort association before accounting for stable differences between children or corpora.",
        "caveat": "Do not use M1 alone as the developmental claim: pooled child coverage can make age look like child/corpus composition.",
    },
    "M2": {
        "title": "Age and effort with child identity",
        "question": "Does the age effect remain after controlling utterance effort and each child's baseline?",
        "formula": "sum_bits ~ age + effort + C(child_id)",
        "actual": "Most M2 atlas rows use centered `age_c`, centered effort, and `C(child_id)` fixed intercepts.",
        "estimator": "Primary M2 is ordinary least squares with child fixed intercepts and child-cluster robust standard errors in statsmodels.",
        "random": "`C(child_id)` is a fixed effect, not a random effect. Sensitivity checks additionally tried GEE and MixedLM random child intercept/slope variants.",
        "meaning": "M2 is the cleanest first candidate for the supervisor-facing result: it asks whether same-child developmental change predicts total bits at fixed effort.",
        "caveat": "The shared age slope is still linear and averaged over children. Child-specific slope variants are diagnostics, not the primary simple story.",
    },
    "M3": {
        "title": "Age by effort",
        "question": "Does the developmental age effect depend on utterance effort?",
        "formula": "sum_bits ~ age * effort + C(child_id)",
        "actual": "Continuous-effort M3 uses centered `age_c * effort_c`; effort-level M3 uses `age_c * C(effort_level)`.",
        "estimator": "Primary M3 atlas rows are OLS with child fixed intercepts and child-cluster robust standard errors. Deep-dive sensitivity rows include OLS, GLM, GEE, and MixedLM variants.",
        "random": "Primary M3 uses child fixed intercepts. MixedLM variants with random intercepts/slopes are sensitivity checks and can be singular.",
        "meaning": "M3 tells us whether a single age slope hides different trajectories for short versus long utterances.",
        "caveat": "Interaction coefficients are harder to interpret than fixed-effort slices. Prefer the fixed-slice plots when explaining M3.",
    },
    "M4": {
        "title": "Context predictor added",
        "question": "Does context entropy, matched context size, or both explain total information beyond age, target effort, and child identity?",
        "formula": "sum_bits ~ age + effort + context predictor + C(child_id)",
        "actual": "Context atlas variants are M4E, M4S, and M4ES for entropy, context size, and entropy plus size.",
        "estimator": "The context M1-M6 atlas uses ordinary least squares via `statsmodels.formula.api.ols` with child-cluster robust standard errors.",
        "random": "Child identity is represented as fixed intercepts in primary M4. The earlier M4 deep dive also includes Gaussian and Gamma GEE sensitivity models clustered by child.",
        "meaning": "M4 asks whether the developmental result survives a control for how predictable the next-token context is.",
        "caveat": "The context feature here is next-token context entropy from the scored feature pipeline, not full response-level entropy.",
    },
    "M5": {
        "title": "Age by context predictor",
        "question": "Does the context-predictor association itself change with age?",
        "formula": "sum_bits ~ age * context predictor + effort + C(child_id)",
        "actual": "Context atlas variants are M5E, M5S, and M5ES for age by entropy, age by context size, and both interactions.",
        "estimator": "Primary atlas rows are OLS with child fixed intercepts and child-cluster robust standard errors.",
        "random": "No random effects in the primary M5 atlas. Child baselines are fixed intercepts.",
        "meaning": "M5 is about developmental context sensitivity: whether older children show a different relation between context predictability and produced information.",
        "caveat": "Treat M5 as explanatory/exploratory unless the interaction is stable across context windows and effort measures.",
    },
    "M6": {
        "title": "Interaction-rich stress test",
        "question": "Do age, target effort, and context predictors interact when predicting total information?",
        "formula": "sum_bits ~ age * effort + age * context + effort * context + C(child_id)",
        "actual": "Context atlas variants are M6E, M6S, and M6ES; the most saturated ES version also includes entropy by context-size interaction.",
        "estimator": "Primary atlas rows are OLS with child fixed intercepts and child-cluster robust standard errors.",
        "random": "No random effects in the primary M6 atlas. Mixed/random-effect evidence belongs to the M1-M3 sensitivity family only.",
        "meaning": "M6 is a robustness stress test: it asks whether the simpler M2-M5 stories collapse under richer interactions.",
        "caveat": "This model is easiest to overinterpret. Multicollinearity and interaction saturation mean plots and sign stability matter more than any single coefficient.",
    },
}


def read_optional_csv(path: Path) -> pd.DataFrame:
    """Read a CSV if present, otherwise return an empty frame."""

    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 30, digits: int = 4) -> str:
    """Render a compact dataframe as a Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    rendered = shown.astype(object).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]) or pd.api.types.is_integer_dtype(shown[col]):
            rendered[col] = shown[col].map(format_number)
        else:
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(str(col) for col in rendered.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("\n", " ").replace("|", "/") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    tail = ""
    if len(frame) > max_rows:
        tail = f"\n\n_Showing {max_rows} of {len(frame)} rows._"
    return "\n".join([header, separator, *rows]) + tail


def format_number(value: object, *, digits: int = 4) -> str:
    """Format numeric table cells without hiding very small values."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "" if pd.isna(value) else str(value)
    if not math.isfinite(parsed):
        return ""
    if abs(parsed) < 0.001 and parsed != 0:
        return f"{parsed:.2e}"
    return f"{parsed:.{digits}g}"


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


def rel_link(path: Path, base: Path) -> str:
    """Return a POSIX path from a Markdown file to another local path."""

    try:
        return Path(path).resolve().relative_to(base.resolve().parent).as_posix()
    except ValueError:
        return Path("../") / Path(path)


def image_md(path: Path, alt: str, *, md_path: Path) -> str:
    """Return Markdown image syntax for an existing local figure."""

    if not path.exists():
        return f"_Missing plot: `{path}`_"
    return f"![{alt}]({Path('../') / path})"


def infer_model_ids(text: str) -> list[str]:
    """Infer all M1-M6 model families referenced by a filename/path."""

    lower = text.lower()
    found: list[str] = []
    for lo, hi in [("m1_m2", ["M1", "M2"]), ("m5_m6", ["M5", "M6"])]:
        if lo in lower:
            found.extend(hi)
    for match in re.finditer(r"(?<![a-z0-9])m([1-6])(?:[a-z]{0,3})?(?=(_|-|\.|$))", lower):
        found.append(f"M{match.group(1)}")
    # Deep-dive figures named m4_m4a etc. still belong to M4.
    for match in re.finditer(r"(?<![a-z0-9])m([1-6])_", lower):
        found.append(f"M{match.group(1)}")
    ordered: list[str] = []
    for model_id in MODEL_ORDER:
        if model_id in found and model_id not in ordered:
            ordered.append(model_id)
    return ordered


def infer_context_k(text: str) -> str:
    """Infer k0-k3 from a filename if present."""

    match = re.search(r"(?<![a-z0-9])k([0-3])(?=(_|-|\.|$))", text.lower())
    return f"k{match.group(1)}" if match else ""


def infer_effort_label(text: str) -> str:
    """Infer an effort label from a filename if present."""

    lower = text.lower()
    for col, label in EFFORT_NAME_BY_COL.items():
        if col in lower:
            return label
    if "words" in lower:
        return "Words"
    if "morphemes" in lower:
        return "Morphemes"
    if "phonemes" in lower:
        return "Phonemes"
    if "syllables_cmu" in lower:
        return "Syllables: CMU/pkg"
    if "syllables_pkg" in lower:
        return "Syllables: pkg"
    return ""


def collect_figure_inventory(
    sources: Sequence[tuple[str, str, Path]] | None = None,
) -> pd.DataFrame:
    """Collect all PNG figures relevant to the model atlas."""

    if sources is None:
        sources = FIGURE_SOURCES
    rows: list[dict[str, object]] = []
    for source_id, source_label, source_dir in sources:
        if not source_dir.exists():
            rows.append(
                {
                    "source_id": source_id,
                    "source_label": source_label,
                    "source_dir": source_dir.as_posix(),
                    "path": "",
                    "filename": "",
                    "models": "",
                    "context_k": "",
                    "effort_label": "",
                    "exists": False,
                }
            )
            continue
        for path in sorted(source_dir.glob("*.png")):
            rows.append(
                {
                    "source_id": source_id,
                    "source_label": source_label,
                    "source_dir": source_dir.as_posix(),
                    "path": path.as_posix(),
                    "filename": path.name,
                    "models": ";".join(infer_model_ids(path.name)),
                    "context_k": infer_context_k(path.name),
                    "effort_label": infer_effort_label(path.name),
                    "exists": True,
                }
            )
    return pd.DataFrame(rows)


def artifact_inventory(artifacts: Sequence[tuple[str, str, Path]] | None = None) -> pd.DataFrame:
    """Summarize CSV artifacts used by the report."""

    if artifacts is None:
        artifacts = ARTIFACTS
    rows: list[dict[str, object]] = []
    for artifact_id, label, path in artifacts:
        if path.exists():
            frame = pd.read_csv(path, nrows=0)
            try:
                with path.open("r", encoding="utf-8") as handle:
                    row_count = sum(1 for _ in handle) - 1
            except UnicodeDecodeError:
                row_count = len(pd.read_csv(path))
            rows.append(
                {
                    "artifact_id": artifact_id,
                    "label": label,
                    "path": path.as_posix(),
                    "exists": True,
                    "rows": max(row_count, 0),
                    "columns": len(frame.columns),
                    "first_columns": ", ".join(frame.columns[:8]),
                }
            )
        else:
            rows.append(
                {
                    "artifact_id": artifact_id,
                    "label": label,
                    "path": path.as_posix(),
                    "exists": False,
                    "rows": 0,
                    "columns": 0,
                    "first_columns": "",
                }
            )
    return pd.DataFrame(rows)


def ordered_effort_columns(columns: Iterable[str]) -> list[str]:
    """Return effort columns in the standard effort order."""

    present = list(columns)
    return [label for label in EFFORT_ORDER if label in present] + [label for label in present if label not in EFFORT_ORDER]


def save_heatmap(
    frame: pd.DataFrame,
    *,
    index: str,
    columns: str,
    values: str,
    path: Path,
    title: str,
    cbar_label: str,
    center: float | None = None,
    cmap: str = "vlag",
) -> Path | None:
    """Save a heatmap from long-form data."""

    if frame.empty or not {index, columns, values}.issubset(frame.columns):
        return None
    plot_frame = frame.copy()
    plot_frame[values] = pd.to_numeric(plot_frame[values], errors="coerce")
    plot_frame = plot_frame.dropna(subset=[values])
    if plot_frame.empty:
        return None
    pivot = plot_frame.pivot_table(index=index, columns=columns, values=values, aggfunc="mean")
    pivot = pivot.reindex(columns=ordered_effort_columns(pivot.columns))
    height = max(3.5, min(18.0, 0.34 * len(pivot) + 1.8))
    width = max(7.0, min(13.5, 1.35 * len(pivot.columns) + 3.0))
    fig, ax = plt.subplots(figsize=(width, height))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=cmap,
        center=center,
        annot=True,
        fmt=".3g",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": cbar_label},
    )
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def source_plot_manifest_row(path: Path | None, figure_id: str, description: str) -> dict[str, str] | None:
    """Return a report figure manifest row."""

    if path is None:
        return None
    return {"figure_id": figure_id, "path": path.as_posix(), "description": description}


def plot_estimator_variant_coefficients(expanded: pd.DataFrame, fig_dir: Path) -> Path | None:
    """Plot M1-M3 estimator-family age coefficients."""

    required = {"approach_id", "model_family_label", "effort_label", "age_coef", "status"}
    if expanded.empty or not required.issubset(expanded.columns):
        return None
    frame = expanded[expanded["status"].eq("fit")].copy()
    frame["age_coef"] = pd.to_numeric(frame["age_coef"], errors="coerce")
    frame = frame.dropna(subset=["age_coef"])
    if frame.empty:
        return None
    frame["row_label"] = frame["approach_id"].astype(str) + ": " + frame["model_family_label"].astype(str)
    row_order = (
        frame[["approach_id", "row_label"]]
        .drop_duplicates()
        .sort_values(["approach_id", "row_label"])["row_label"]
        .tolist()
    )
    fig, ax = plt.subplots(figsize=(11.5, max(7.0, 0.35 * len(row_order) + 2.0)))
    sns.scatterplot(
        data=frame,
        x="age_coef",
        y="row_label",
        hue="effort_label",
        hue_order=ordered_effort_columns(frame["effort_label"].dropna().unique()),
        s=70,
        ax=ax,
    )
    ax.axvline(0, color="#222222", linewidth=1.0, linestyle="--")
    ax.set_yticks(range(len(row_order)))
    ax.set_yticklabels(row_order)
    ax.set_title("M1-M3 estimator sensitivity: age coefficient by effort unit")
    ax.set_xlabel("Age coefficient")
    ax.set_ylabel("")
    ax.legend(title="Effort unit", loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()
    path = fig_dir / "estimator_variant_age_coefficients.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def plot_context_predictor_significance(context_summary: pd.DataFrame, fig_dir: Path) -> Path | None:
    """Plot signed significance counts for context predictor terms."""

    if context_summary.empty:
        return None
    term_pairs = [
        ("context_entropy", "context_entropy_coef", "context_entropy_p"),
        ("context_size", "context_size_coef", "context_size_p"),
        ("age_x_entropy", "age_entropy_coef", "age_entropy_p"),
        ("age_x_context_size", "age_context_size_coef", "age_context_size_p"),
        ("effort_x_entropy", "effort_entropy_coef", "effort_entropy_p"),
        ("effort_x_context_size", "effort_context_size_coef", "effort_context_size_p"),
        ("entropy_x_context_size", "entropy_context_size_coef", "entropy_context_size_p"),
    ]
    rows: list[dict[str, object]] = []
    for label, coef_col, p_col in term_pairs:
        if coef_col not in context_summary.columns or p_col not in context_summary.columns:
            continue
        coef = pd.to_numeric(context_summary[coef_col], errors="coerce")
        pvals = pd.to_numeric(context_summary[p_col], errors="coerce")
        available = coef.notna() & pvals.notna()
        significant = available & (pvals < 0.05)
        rows.extend(
            [
                {"term": label, "direction": "significant positive", "rows": int((significant & (coef > 0)).sum())},
                {"term": label, "direction": "significant negative", "rows": int((significant & (coef < 0)).sum())},
                {"term": label, "direction": "not significant or unavailable", "rows": int((~significant).sum())},
            ]
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return None
    fig, ax = plt.subplots(figsize=(12.0, 5.8))
    sns.barplot(data=frame, x="term", y="rows", hue="direction", ax=ax)
    ax.set_title("Context M1-M6: signed significance counts across context/effort/model rows")
    ax.set_xlabel("")
    ax.set_ylabel("Rows")
    ax.tick_params(axis="x", rotation=28)
    ax.legend(title="")
    fig.tight_layout()
    path = fig_dir / "context_predictor_significance_counts.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def plot_figure_inventory_counts(inventory: pd.DataFrame, fig_dir: Path) -> Path | None:
    """Plot figure counts by source."""

    if inventory.empty or "source_label" not in inventory.columns:
        return None
    counts = (
        inventory[inventory["exists"].astype(bool)]
        .groupby(["source_id", "source_label"], observed=True)
        .size()
        .reset_index(name="figures")
        .sort_values("figures", ascending=False)
    )
    if counts.empty:
        return None
    fig, ax = plt.subplots(figsize=(11.0, 5.8))
    sns.barplot(data=counts, y="source_label", x="figures", color="#2f6f73", ax=ax)
    ax.set_title("Included PNG figures by source atlas")
    ax.set_xlabel("PNG figures")
    ax.set_ylabel("")
    fig.tight_layout()
    path = fig_dir / "figure_inventory_by_source.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def build_overview_plots(
    *,
    output_dir: Path,
    fig_dir: Path,
    expanded: pd.DataFrame,
    dual: pd.DataFrame,
    atlas_slopes: pd.DataFrame,
    context_summary: pd.DataFrame,
    context_slopes: pd.DataFrame,
    robustness: pd.DataFrame,
    figure_inventory: pd.DataFrame,
) -> pd.DataFrame:
    """Build cross-atlas summary figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    rows: list[dict[str, str]] = []

    if not dual.empty:
        dual_fit = dual[dual.get("status", "").eq("fit")].copy() if "status" in dual.columns else dual.copy()
        for strategy, figure_id, title in [
            ("continuous", "dual_continuous_age_coefficients", "M1-M6 continuous-effort models: age coefficients"),
            ("effort_level", "dual_effort_level_age_coefficients", "M1-M6 effort-level models: age coefficients"),
        ]:
            sub = dual_fit[dual_fit["effort_strategy"].eq(strategy)].copy()
            path = save_heatmap(
                sub,
                index="model_id",
                columns="effort_label",
                values="age_coef",
                path=fig_dir / f"{figure_id}.png",
                title=title,
                cbar_label="Age coefficient",
                center=0,
            )
            row = source_plot_manifest_row(path, figure_id, title)
            if row:
                rows.append(row)
        path = save_heatmap(
            dual_fit[dual_fit["effort_strategy"].eq("continuous")].copy(),
            index="model_id",
            columns="effort_label",
            values="r2_observed_fitted",
            path=fig_dir / "dual_continuous_r2.png",
            title="M1-M6 continuous-effort models: observed-vs-fitted R2",
            cbar_label="R2",
            center=None,
            cmap="YlGnBu",
        )
        row = source_plot_manifest_row(path, "dual_continuous_r2", "M1-M6 continuous-effort R2 heatmap.")
        if row:
            rows.append(row)

    row = source_plot_manifest_row(
        plot_estimator_variant_coefficients(expanded, fig_dir),
        "estimator_variant_age_coefficients",
        "M1-M3 estimator-family age coefficient scatterplot.",
    )
    if row:
        rows.append(row)

    if not context_summary.empty:
        context = context_summary.copy()
        context["row_label"] = (
            context["context_k"].astype(str)
            + " "
            + context["model_id"].astype(str)
            + " "
            + context["context_variant"].astype(str)
        )
        path = save_heatmap(
            context,
            index="row_label",
            columns="effort_label",
            values="age_coef",
            path=fig_dir / "context_m1_m6_age_coefficients.png",
            title="Context-window M1-M6 age coefficients",
            cbar_label="Age coefficient",
            center=0,
        )
        row = source_plot_manifest_row(path, "context_m1_m6_age_coefficients", "Context-window age coefficient heatmap.")
        if row:
            rows.append(row)
        path = save_heatmap(
            context,
            index="row_label",
            columns="effort_label",
            values="r2_observed_fitted",
            path=fig_dir / "context_m1_m6_r2.png",
            title="Context-window M1-M6 observed-vs-fitted R2",
            cbar_label="R2",
            center=None,
            cmap="YlGnBu",
        )
        row = source_plot_manifest_row(path, "context_m1_m6_r2", "Context-window R2 heatmap.")
        if row:
            rows.append(row)
        row = source_plot_manifest_row(
            plot_context_predictor_significance(context_summary, fig_dir),
            "context_predictor_significance_counts",
            "Signed significance counts for context-predictor terms.",
        )
        if row:
            rows.append(row)

    if not atlas_slopes.empty:
        slopes = atlas_slopes.copy()
        slopes["negative_slope_share"] = pd.to_numeric(slopes["slope_bits_per_month"], errors="coerce") < 0
        fixed_share = (
            slopes.groupby(["model_id", "effort_label"], observed=True)["negative_slope_share"]
            .mean()
            .reset_index()
        )
        path = save_heatmap(
            fixed_share,
            index="model_id",
            columns="effort_label",
            values="negative_slope_share",
            path=fig_dir / "fixed_slice_negative_share.png",
            title="M1-M6 fixed-effort atlas: share of slices with negative age slope",
            cbar_label="Share negative",
            center=0.5,
            cmap="vlag",
        )
        row = source_plot_manifest_row(path, "fixed_slice_negative_share", "Share of fixed-effort slices with negative age slopes.")
        if row:
            rows.append(row)

    if not context_slopes.empty:
        slopes = context_slopes.copy()
        slopes["negative_slope_share"] = pd.to_numeric(slopes["slope_bits_per_month"], errors="coerce") < 0
        slopes["row_label"] = slopes["context_k"].astype(str) + " " + slopes["model_family"].astype(str)
        context_share = (
            slopes.groupby(["row_label", "effort_label"], observed=True)["negative_slope_share"]
            .mean()
            .reset_index()
        )
        path = save_heatmap(
            context_share,
            index="row_label",
            columns="effort_label",
            values="negative_slope_share",
            path=fig_dir / "context_fixed_slice_negative_share.png",
            title="Context M1-M6 fixed slices: share with negative age slope",
            cbar_label="Share negative",
            center=0.5,
            cmap="vlag",
        )
        row = source_plot_manifest_row(path, "context_fixed_slice_negative_share", "Context fixed-slice negative slope share.")
        if row:
            rows.append(row)

    if not robustness.empty:
        robust = robustness.copy()
        robust["outside_share"] = robust["observed_outside_null_95"].astype(bool)
        robust_share = (
            robust.groupby(["model_id", "robustness_method"], observed=True)["outside_share"]
            .mean()
            .reset_index()
        )
        path = save_heatmap(
            robust_share,
            index="model_id",
            columns="robustness_method",
            values="outside_share",
            path=fig_dir / "robustness_outside_null_summary.png",
            title="Age robustness: share of rows outside corresponding null 95% interval",
            cbar_label="Share outside null",
            center=0.5,
            cmap="vlag",
        )
        row = source_plot_manifest_row(path, "robustness_outside_null_summary", "Robustness outside-null summary heatmap.")
        if row:
            rows.append(row)

    row = source_plot_manifest_row(
        plot_figure_inventory_counts(figure_inventory, fig_dir),
        "figure_inventory_by_source",
        "Figure counts by source atlas.",
    )
    if row:
        rows.append(row)

    manifest = pd.DataFrame(rows)
    manifest.to_csv(output_dir / "overview_figure_manifest.csv", index=False)
    return manifest


def compact_dual_table(dual: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return compact M1-M6 dual-effort rows for one model."""

    cols = [
        "effort_strategy",
        "effort_label",
        "readable_formula",
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
        "status",
    ]
    if dual.empty:
        return pd.DataFrame()
    out = dual[dual["model_id"].eq(model_id)][[col for col in cols if col in dual.columns]].copy()
    if out.empty:
        return out
    strategy_order = {"continuous": 0, "effort_level": 1}
    out["_strategy"] = out["effort_strategy"].map(strategy_order).fillna(9)
    out["_effort"] = out["effort_label"].map({label: idx for idx, label in enumerate(EFFORT_ORDER)}).fillna(99)
    out = out.sort_values(["_strategy", "_effort"]).drop(columns=["_strategy", "_effort"])
    for col in [col for col in out.columns if col.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def compact_expanded_table(expanded: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return compact estimator-family rows for one model."""

    if expanded.empty or "approach_id" not in expanded.columns:
        return pd.DataFrame()
    cols = [
        "model_family_label",
        "fit_type",
        "effect_scale",
        "effort_label",
        "readable_formula",
        "status",
        "n_obs",
        "n_children",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "effort_coef",
        "effort_p",
        "age_effort_coef",
        "age_effort_p",
    ]
    out = expanded[expanded["approach_id"].eq(model_id)][[col for col in cols if col in expanded.columns]].copy()
    for col in [col for col in out.columns if col.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out.sort_values(["model_family_label", "effort_label"]) if not out.empty else out


def compact_context_table(context_summary: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return context-window rows for one M1-M6 family."""

    if context_summary.empty:
        return pd.DataFrame()
    family = model_id
    if "model_family" not in context_summary.columns:
        return pd.DataFrame()
    cols = [
        "context_k",
        "model_id",
        "context_variant",
        "effort_label",
        "estimator",
        "library",
        "covariance",
        "n_obs",
        "n_children",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "target_effort_coef",
        "target_effort_p",
        "context_entropy_coef",
        "context_entropy_p",
        "context_size_coef",
        "context_size_p",
        "age_effort_coef",
        "age_effort_p",
        "age_entropy_coef",
        "age_entropy_p",
        "age_context_size_coef",
        "age_context_size_p",
    ]
    out = context_summary[context_summary["model_family"].eq(family)][[col for col in cols if col in context_summary.columns]].copy()
    if out.empty:
        return out
    for col in [col for col in out.columns if col.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out.sort_values(["context_k", "model_id", "effort_label"])


def compact_robustness_table(robustness: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return a compact robustness summary for one model."""

    if robustness.empty:
        return pd.DataFrame()
    sub = robustness[robustness["model_id"].eq(model_id)].copy()
    if sub.empty:
        return sub
    out = (
        sub.groupby(["context_k", "robustness_method"], observed=True)
        .agg(
            rows=("observed_age_coef", "size"),
            negative_observed=("observed_age_coef", lambda values: int((pd.to_numeric(values, errors="coerce") < 0).sum())),
            outside_null_95=("observed_outside_null_95", lambda values: int(pd.Series(values).astype(bool).sum())),
            mean_same_sign_share=("same_sign_share", "mean"),
            median_permutation_p=("two_sided_permutation_p", "median"),
        )
        .reset_index()
    )
    out["median_permutation_p"] = out["median_permutation_p"].map(format_p)
    return out.sort_values(["context_k", "robustness_method"])


def model_takeaway(
    model_id: str,
    *,
    dual: pd.DataFrame,
    atlas_slopes: pd.DataFrame,
    context_summary: pd.DataFrame,
    robustness: pd.DataFrame,
) -> str:
    """Generate a short computed take-away sentence for one model."""

    pieces: list[str] = []
    if not dual.empty:
        sub = dual[dual["model_id"].eq(model_id) & dual["effort_strategy"].eq("continuous")].copy()
        ages = pd.to_numeric(sub.get("age_coef", pd.Series(dtype=float)), errors="coerce").dropna()
        if not ages.empty:
            pieces.append(f"continuous-effort age signs: {(ages < 0).sum()} negative, {(ages > 0).sum()} positive across {len(ages)} effort units")
    if not atlas_slopes.empty:
        sub = atlas_slopes[atlas_slopes["model_id"].eq(model_id)].copy()
        slopes = pd.to_numeric(sub.get("slope_bits_per_month", pd.Series(dtype=float)), errors="coerce").dropna()
        if not slopes.empty:
            pieces.append(f"fixed-effort slices: {(slopes < 0).mean():.0%} negative age slopes")
    if not context_summary.empty and "model_family" in context_summary.columns:
        sub = context_summary[context_summary["model_family"].eq(model_id)].copy()
        ages = pd.to_numeric(sub.get("age_coef", pd.Series(dtype=float)), errors="coerce").dropna()
        if not ages.empty:
            pieces.append(f"context-window atlas age signs: {(ages < 0).sum()} negative, {(ages > 0).sum()} positive across {len(ages)} rows")
    if not robustness.empty:
        sub = robustness[robustness["model_id"].eq(model_id)].copy()
        if not sub.empty:
            outside = sub["observed_outside_null_95"].astype(bool).mean()
            pieces.append(f"robustness outside-null share: {outside:.0%}")
    if not pieces:
        return "No saved summary rows were available for this model."
    return "; ".join(pieces) + "."


def figures_for_model(inventory: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return figure inventory rows associated with one model."""

    if inventory.empty:
        return pd.DataFrame()
    mask = inventory["models"].fillna("").str.split(";").map(lambda values: model_id in values)
    return inventory[mask & inventory["exists"].astype(bool)].copy()


def figure_gallery(
    figures: pd.DataFrame,
    *,
    md_path: Path,
    max_per_source: int | None = None,
) -> str:
    """Return a grouped Markdown gallery for figure inventory rows."""

    if figures.empty:
        return "_No figures found for this group._"
    lines: list[str] = []
    for source_id, group in figures.sort_values(["source_id", "filename"]).groupby("source_id", sort=False):
        label = group["source_label"].iloc[0]
        shown = group if max_per_source is None else group.head(max_per_source)
        lines.append(f"#### {label}\n")
        for row in shown.to_dict("records"):
            path = Path(str(row["path"]))
            caption_bits = [str(row["filename"])]
            if row.get("context_k"):
                caption_bits.append(str(row["context_k"]))
            if row.get("effort_label"):
                caption_bits.append(str(row["effort_label"]))
            lines.append(image_md(path, " / ".join(caption_bits), md_path=md_path))
            lines.append(f"*{'; '.join(caption_bits)}*\n")
        if max_per_source is not None and len(group) > max_per_source:
            lines.append(f"_Showing {max_per_source} of {len(group)} figures from this source._\n")
    return "\n".join(lines)


def model_formula_table() -> pd.DataFrame:
    """Return the model map table used in the report."""

    rows = []
    for model_id in MODEL_ORDER:
        guide = MODEL_GUIDE[model_id]
        rows.append(
            {
                "model": model_id,
                "title": guide["title"],
                "readable formula": guide["formula"],
                "primary scientific role": guide["meaning"],
            }
        )
    return pd.DataFrame(rows)


def estimator_guide_table() -> pd.DataFrame:
    """Return a guide to estimators and dependence structures used."""

    return pd.DataFrame(
        [
            {
                "label": "OLS",
                "library/object": "`statsmodels.formula.api.ols`",
                "what it is": "ordinary linear regression on additive total bits",
                "where used": "M1 baseline; primary M1-M6 atlas fits after adding child fixed effects where specified",
                "dependence handling": "none unless cluster covariance or `C(child_id)` is added",
            },
            {
                "label": "OLS + child-clustered SE",
                "library/object": "`fit(cov_type='cluster', cov_kwds={'groups': child_id})`",
                "what it is": "same OLS fitted line with standard errors adjusted for repeated utterances within child",
                "where used": "primary dual-effort, fixed-effort, context atlas, and many deep-dive rows",
                "dependence handling": "affects uncertainty/p-values, not fitted means",
            },
            {
                "label": "Child fixed intercepts",
                "library/object": "`C(child_id)` in statsmodels formulas",
                "what it is": "one intercept per child",
                "where used": "primary M2-M6 formulas",
                "dependence handling": "controls stable child baselines; it is not a random effect",
            },
            {
                "label": "Child fixed age slopes",
                "library/object": "`age_c:C(child_id)`",
                "what it is": "one linear age slope adjustment per child",
                "where used": "M2/M3 sensitivity checks",
                "dependence handling": "diagnostic for child-specific developmental slopes",
            },
            {
                "label": "Gaussian GLM",
                "library/object": "`statsmodels.formula.api.glm(..., family=Gaussian())`",
                "what it is": "GLM version of the additive-bit linear model",
                "where used": "M1-M3 sensitivity rows",
                "dependence handling": "no child dependence unless formula includes child terms",
            },
            {
                "label": "Gamma GLM, log link",
                "library/object": "`statsmodels.formula.api.glm(..., family=Gamma(link=Log()))`",
                "what it is": "positive-outcome sensitivity model; coefficients are on log expected bits",
                "where used": "M1-M3 and M4 sensitivity rows",
                "dependence handling": "no child dependence unless formula includes child terms",
            },
            {
                "label": "GEE Gaussian/Gamma",
                "library/object": "`statsmodels.formula.api.gee(..., groups='child_id')`",
                "what it is": "population-average model clustered by child",
                "where used": "M2/M3 and M4 sensitivity rows",
                "dependence handling": "models within-child correlation through GEE clustering",
            },
            {
                "label": "MixedLM random child intercept/slope",
                "library/object": "`statsmodels` mixed linear model",
                "what it is": "linear mixed model with random child intercept and sometimes random age slope",
                "where used": "M2/M3 sensitivity rows only",
                "dependence handling": "random effects; several rows are singular/warning-prone, so use as diagnostics",
            },
        ]
    )


def build_model_section(
    model_id: str,
    *,
    expanded: pd.DataFrame,
    m4_context: pd.DataFrame,
    saturated: pd.DataFrame,
    dual: pd.DataFrame,
    atlas_slopes: pd.DataFrame,
    context_summary: pd.DataFrame,
    robustness: pd.DataFrame,
    figure_inventory: pd.DataFrame,
    md_path: Path,
) -> str:
    """Return one full model section."""

    guide = MODEL_GUIDE[model_id]
    sections: list[str] = []
    sections.append(
        f"""## {model_id}: {guide['title']}

**Scientific question.** {guide['question']}

**Readable formula.** `{guide['formula']}`

**Exact implementation note.** {guide['actual']}

**Estimator/library.** {guide['estimator']}

**Fixed/random effects.** {guide['random']}

**Scientific meaning.** {guide['meaning']}

**Main caveat.** {guide['caveat']}

**Computed take-away across saved artifacts.** {model_takeaway(model_id, dual=dual, atlas_slopes=atlas_slopes, context_summary=context_summary, robustness=robustness)}
"""
    )

    dual_table = compact_dual_table(dual, model_id)
    if not dual_table.empty:
        sections.append("### Dual Effort Summary\n\nThis table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.\n\n" + markdown_table(dual_table, max_rows=14))

    expanded_table = compact_expanded_table(expanded, model_id)
    if not expanded_table.empty:
        sections.append("### Estimator Sensitivity Rows\n\nThese are the non-simple-OLS variants from the deep-dive packet. Use them to check whether the age conclusion depends on estimator family, child clustering, child fixed effects, GEE clustering, Gamma/log scaling, or mixed/random-effect structure.\n\n" + markdown_table(expanded_table, max_rows=80))

    if model_id == "M4" and not m4_context.empty:
        m4 = m4_context.copy()
        for col in [col for col in m4.columns if col.endswith("_p")]:
            m4[col] = m4[col].map(format_p)
        cols = [
            "model_id",
            "model_label",
            "fit_type",
            "effort_label",
            "formula",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "entropy_coef",
            "entropy_p",
            "status",
        ]
        sections.append("### M4 Context-Entropy Deep-Dive Rows\n\nThese rows include OLS/clustered, GEE, and Gamma/log variants for the context-entropy addition.\n\n" + markdown_table(m4[[col for col in cols if col in m4.columns]], max_rows=35))

    if model_id in {"M5", "M6"} and not saturated.empty:
        sat = saturated[saturated["model_id"].eq(model_id)].copy()
        for col in [col for col in sat.columns if col.endswith("_p")]:
            sat[col] = sat[col].map(format_p)
        cols = [
            "model_id",
            "model_label",
            "fit_type",
            "effort_label",
            "formula",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "context_entropy_coef",
            "context_entropy_p",
            "status",
        ]
        sections.append("### Effort-Level Context Exploratory Rows\n\nThese are the earlier M5/M6 low/mid/high effort-level context models. They are useful but less clean than the fixed-effort atlas when explaining effort-specific trajectories.\n\n" + markdown_table(sat[[col for col in cols if col in sat.columns]], max_rows=20))

    context_table = compact_context_table(context_summary, model_id)
    if not context_table.empty:
        sections.append("### Context-Window M1-M6 Atlas Rows\n\nThese rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.\n\n" + markdown_table(context_table, max_rows=70))

    robust_table = compact_robustness_table(robustness, model_id)
    if not robust_table.empty:
        sections.append("### Age-Bin Bootstrap And Scrambling Robustness\n\nRows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.\n\n" + markdown_table(robust_table, max_rows=30))

    figures = figures_for_model(figure_inventory, model_id)
    sections.append(f"### All Plots For {model_id}\n\n" + figure_gallery(figures, md_path=md_path))
    return "\n\n".join(sections)


def build_appendix_sections(
    *,
    context_fixed: pd.DataFrame,
    figure_inventory: pd.DataFrame,
    overview_manifest: pd.DataFrame,
    md_path: Path,
) -> str:
    """Return appendix sections for adjunct outputs and figure inventory."""

    sections: list[str] = []
    adjunct_figs = figure_inventory[
        figure_inventory["source_id"].eq("context_adjunct") & figure_inventory["exists"].astype(bool)
    ].copy()
    if not context_fixed.empty or not adjunct_figs.empty:
        if not context_fixed.empty:
            cf = context_fixed.copy()
            for col in [col for col in cf.columns if col.endswith("_p")]:
                cf[col] = cf[col].map(format_p)
            cols = [
                "context_k",
                "model_id",
                "model_label",
                "effort_label",
                "formula",
                "n_obs",
                "n_children",
                "r2_observed_fitted",
                "age_coef",
                "age_p",
                "context_entropy_coef",
                "context_entropy_p",
                "context_size_coef",
                "context_size_p",
                "status",
            ]
            table = markdown_table(cf[[col for col in cols if col in cf.columns]], max_rows=85)
        else:
            table = "_No context-adjunct table found._"
        sections.append(
            "## Appendix A: Context-Predictor Adjunct Atlas\n\n"
            "This CF0-CF3 atlas is adjacent to the M1-M6 ladder. It is especially useful for separating target effort, context entropy, and matched context-window size before interpreting M4-M6.\n\n"
            + table
            + "\n\n### Context Adjunct Plots\n\n"
            + figure_gallery(adjunct_figs, md_path=md_path)
        )

    if not overview_manifest.empty:
        lines = ["## Appendix B: New Cross-Atlas Overview Plots\n"]
        for row in overview_manifest.to_dict("records"):
            lines.append(image_md(Path(row["path"]), str(row["description"]), md_path=md_path))
            lines.append(f"*{row['description']}*\n")
        sections.append("\n".join(lines))

    figure_counts = (
        figure_inventory[figure_inventory["exists"].astype(bool)]
        .groupby(["source_id", "source_label"], observed=True)
        .agg(figures=("filename", "size"))
        .reset_index()
        .sort_values("figures", ascending=False)
    )
    sections.append(
        "## Appendix C: Complete Figure Inventory\n\n"
        "The report embeds PNGs only. PDF duplicates remain in the figure folders but are intentionally not embedded here.\n\n"
        + markdown_table(figure_counts, max_rows=30)
        + "\n\n"
        + markdown_table(
            figure_inventory[figure_inventory["exists"].astype(bool)][
                ["source_id", "filename", "models", "context_k", "effort_label", "path"]
            ],
            max_rows=500,
        )
    )
    return "\n\n".join(sections)


def build_super_atlas_markdown(
    *,
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
) -> tuple[str, dict[str, pd.DataFrame]]:
    """Build the super-atlas Markdown and derived summary tables."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    expanded = read_optional_csv(DEEP_DIVE_DIR / "expanded_model_family_summary.csv")
    m4_context = read_optional_csv(DEEP_DIVE_DIR / "m4_context_entropy_model_summary.csv")
    saturated = read_optional_csv(DEEP_DIVE_DIR / "m5_m6_saturated_model_summary.csv")
    dual = read_optional_csv(DUAL_DIR / "dual_model_summary.csv")
    atlas_slopes = read_optional_csv(FIXED_ATLAS_DIR / "atlas_fixed_slice_slopes.csv")
    context_summary = read_optional_csv(CONTEXT_M1_M6_DIR / "context_m1_m6_model_summary.csv")
    context_slopes = read_optional_csv(CONTEXT_M1_M6_DIR / "context_m1_m6_slice_slopes.csv")
    context_fixed = read_optional_csv(CONTEXT_FIXED_DIR / "context_fixed_effort_model_summary.csv")
    robustness = read_optional_csv(ROBUSTNESS_DIR / "age_scrambling_robustness_summary.csv")

    figure_inventory = collect_figure_inventory()
    artifacts = artifact_inventory()
    overview_manifest = build_overview_plots(
        output_dir=output_dir,
        fig_dir=fig_dir,
        expanded=expanded,
        dual=dual,
        atlas_slopes=atlas_slopes,
        context_summary=context_summary,
        context_slopes=context_slopes,
        robustness=robustness,
        figure_inventory=figure_inventory,
    )

    figure_inventory.to_csv(output_dir / "figure_inventory.csv", index=False)
    artifacts.to_csv(output_dir / "source_artifact_inventory.csv", index=False)
    coverage_rows: list[dict[str, object]] = []
    for model_id in MODEL_ORDER:
        coverage_rows.append(
            {
                "model": model_id,
                "dual_rows": int((dual["model_id"].eq(model_id)).sum()) if not dual.empty and "model_id" in dual.columns else 0,
                "estimator_sensitivity_rows": int((expanded["approach_id"].eq(model_id)).sum()) if not expanded.empty and "approach_id" in expanded.columns else 0,
                "context_rows": int((context_summary["model_family"].eq(model_id)).sum()) if not context_summary.empty and "model_family" in context_summary.columns else 0,
                "robustness_rows": int((robustness["model_id"].eq(model_id)).sum()) if not robustness.empty and "model_id" in robustness.columns else 0,
                "figure_rows": int(len(figures_for_model(figure_inventory, model_id))),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(output_dir / "model_coverage_summary.csv", index=False)

    source_counts = figure_inventory[figure_inventory["exists"].astype(bool)]["source_id"].value_counts().to_dict()
    intro = f"""# Exhaustive Internal M1-M6 Model Atlas

This is an internal source report for cherry-picking into the supervisor-facing writeup. It is intentionally broader than a polished manuscript section: it pulls together the M1-M6 model ladder, estimator-sensitivity checks, fixed-effort slices, context-window variants, and age-scrambling robustness checks.

It does not pretend that every model is equally central. The report separates the primary scientific interpretation from sensitivity checks and clearly states when a model is ordinary least squares, when child identity is a fixed effect, when uncertainty is child-clustered, and when a GEE/GLM/MixedLM sensitivity was used.

Outcome throughout the M1-M6 ladder:

```text
sum_bits
```

Primary practical reading rule: the most supervisor-ready result is still the child-adjusted fixed-effort story, especially M2 and the fixed-effort slices. M3-M6 are valuable for stress-testing and for deciding which nuance belongs in the dissertation/report, but they should not all become headline claims.

## Coverage Snapshot

{markdown_table(coverage, max_rows=10)}

## Source Artifacts

{markdown_table(artifacts, max_rows=30)}

## Model Ladder

{markdown_table(model_formula_table(), max_rows=6)}

## Estimator And Library Guide

{markdown_table(estimator_guide_table(), max_rows=20)}

## Cross-Atlas Overview Plots

The following plots were built for this report from saved outputs. They are a quick way to see the shape of the result before entering the exhaustive model sections.

"""
    overview_lines = []
    for row in overview_manifest.to_dict("records"):
        overview_lines.append(image_md(Path(row["path"]), str(row["description"]), md_path=md_path))
        overview_lines.append(f"*{row['description']}*\n")
    intro += "\n".join(overview_lines)
    intro += f"""

## How To Use This Report

Read M2 first if the goal is the supervisor-facing narrative. Then use M3 to ask whether effort-specific slopes matter, M4 to ask whether context predictability changes the interpretation, M5 to ask whether context sensitivity changes with age, and M6 as the saturation/stress-test layer.

Figure coverage by source is: {', '.join(f'{key}={value}' for key, value in sorted(source_counts.items()))}. PNG files are embedded; PDF duplicates are not.
"""

    model_sections = [
        build_model_section(
            model_id,
            expanded=expanded,
            m4_context=m4_context,
            saturated=saturated,
            dual=dual,
            atlas_slopes=atlas_slopes,
            context_summary=context_summary,
            robustness=robustness,
            figure_inventory=figure_inventory,
            md_path=md_path,
        )
        for model_id in MODEL_ORDER
    ]
    appendices = build_appendix_sections(
        context_fixed=context_fixed,
        figure_inventory=figure_inventory,
        overview_manifest=overview_manifest,
        md_path=md_path,
    )
    md = "\n\n".join([intro, *model_sections, appendices])
    return md, {
        "figure_inventory": figure_inventory,
        "artifacts": artifacts,
        "coverage": coverage,
        "overview_manifest": overview_manifest,
    }


def build_super_atlas_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
    md_path: Path = DEFAULT_DOC_MD,
    html_path: Path = DEFAULT_DOC_HTML,
) -> dict[str, Path]:
    """Write the exhaustive internal M1-M6 atlas report."""

    md, tables = build_super_atlas_markdown(output_dir=output_dir, fig_dir=fig_dir, md_path=md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {
        "md": md_path,
        "html": html_path,
        "figure_inventory": output_dir / "figure_inventory.csv",
        "source_artifacts": output_dir / "source_artifact_inventory.csv",
        "coverage": output_dir / "model_coverage_summary.csv",
        "overview_manifest": output_dir / "overview_figure_manifest.csv",
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""

    args = parse_args()
    outputs = build_super_atlas_report(
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        md_path=args.md,
        html_path=args.html,
    )
    print(f"[OK] wrote Markdown: {outputs['md']}")
    print(f"[OK] wrote HTML: {outputs['html']}")
    print(f"[OK] wrote figure inventory: {outputs['figure_inventory']}")


if __name__ == "__main__":
    main()
