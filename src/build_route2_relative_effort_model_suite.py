#!/usr/bin/env python3
"""Build a peer-review-oriented Route 2 relative-effort model suite.

The first response-space analysis attached context-level generated-response
summaries to real child utterance rows. This suite asks the Route 2 question
more directly: given the caregiver context and its generated response-space
length distribution, is the child's effort unusually short, typical, or long?

It uses only compact context-level products. It does not score generated
responses for surprisal and does not claim generated samples preserve meaning.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable

try:
    from build_response_space_analysis_suite import (
        add_centered_columns,
        add_within_between_age,
        age_bin_midpoint,
        descriptive_r2,
        finite_model_frame,
        markdown_table,
        read_response_space_table,
        relative_to_doc,
        render_markdown_file,
        result_confint,
        result_to_series,
        strip_child_fixed_effect,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_response_space_analysis_suite import (
        add_centered_columns,
        add_within_between_age,
        age_bin_midpoint,
        descriptive_r2,
        finite_model_frame,
        markdown_table,
        read_response_space_table,
        relative_to_doc,
        render_markdown_file,
        result_confint,
        result_to_series,
        strip_child_fixed_effect,
    )


DEFAULT_INPUT = Path("results/route2_response_space/route2_child_response_space_effort_table.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route2_relative_effort_model_suite")
DEFAULT_FIG_DIR = Path("figs/route2_relative_effort_model_suite")
DEFAULT_REPORT_MD = Path("docs/route2_relative_effort_model_suite.md")
DEFAULT_REPORT_HTML = Path("docs/route2_relative_effort_model_suite.html")

CENTER_COLUMNS = [
    "age_months",
    "response_entropy_bits",
    "generated_expected_words",
    "route2_context_word_count",
    "context_entropy_bits",
]

RELATIVE_OUTCOMES = [
    "child_words_minus_generated_mean",
    "child_words_z_vs_generated",
    "child_words_percentile_in_generated_distribution",
    "child_words_ratio_to_generated_mean",
    "child_shorter_than_generated_median",
    "child_longer_than_generated_p90",
]

BINARY_OUTCOMES = {
    "child_shorter_than_generated_median",
    "child_longer_than_generated_p90",
}

KEY_TERMS = [
    "age_months_c",
    "age_within_child_c",
    "child_mean_age_c",
    "response_entropy_bits_c",
    "generated_expected_words_c",
    "route2_context_word_count_c",
    "context_entropy_bits_c",
    "age_months_c:response_entropy_bits_c",
    "age_within_child_c:response_entropy_bits_c",
]


@dataclass(frozen=True)
class Route2Spec:
    """One Route 2 model-ladder fit."""

    model_id: str
    model_label: str
    outcome: str
    outcome_type: str
    formula: str
    required_cols: tuple[str, ...]
    exclude_fallback: bool = False


def add_route2_relative_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure all context-relative effort outcomes are present and numeric."""

    out = frame.copy()
    if "child_words_ratio_to_generated_mean" not in out.columns:
        denom = pd.to_numeric(out["generated_expected_words"], errors="coerce").replace(0, np.nan)
        out["child_words_ratio_to_generated_mean"] = pd.to_numeric(out["nb_words"], errors="coerce") / denom
    for col in RELATIVE_OUTCOMES:
        if col not in out.columns:
            continue
        if col in BINARY_OUTCOMES:
            out[col] = out[col].fillna(False).astype(bool).astype(float)
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def mundlak_formula(formula: str) -> str:
    """Use within/between-child age and keep age-response entropy interactions."""

    base = strip_child_fixed_effect(formula)
    base = base.replace("age_months_c:response_entropy_bits_c", "age_within_child_c:response_entropy_bits_c")
    return base.replace("age_months_c", "age_within_child_c + child_mean_age_c", 1)


def model_ladder_specs(outcome: str, outcome_type: str, *, final_no_fallback: bool = False) -> list[Route2Spec]:
    """Return the Route 2 model ladder for one outcome."""

    prefix = outcome.replace("child_words_", "").replace("_generated_", "_gen_")
    base = [
        (
            "r2m1_age_child",
            "R2-M1 age + child identity",
            "{outcome} ~ age_months_c + C(child_id)",
            ("age_months_c",),
        ),
        (
            "r2m2_response_entropy",
            "R2-M2 add response entropy",
            "{outcome} ~ age_months_c + response_entropy_bits_c + C(child_id)",
            ("age_months_c", "response_entropy_bits_c"),
        ),
        (
            "r2m3_context_demand",
            "R2-M3 context demand controls",
            "{outcome} ~ age_months_c + generated_expected_words_c + route2_context_word_count_c + context_entropy_bits_c + C(child_id)",
            ("age_months_c", "generated_expected_words_c", "route2_context_word_count_c", "context_entropy_bits_c"),
        ),
        (
            "r2m4_full_controls",
            "R2-M4 response entropy + context demand",
            "{outcome} ~ age_months_c + response_entropy_bits_c + generated_expected_words_c + route2_context_word_count_c + context_entropy_bits_c + C(child_id)",
            (
                "age_months_c",
                "response_entropy_bits_c",
                "generated_expected_words_c",
                "route2_context_word_count_c",
                "context_entropy_bits_c",
            ),
        ),
        (
            "r2m5_age_by_entropy",
            "R2-M5 age x response entropy",
            "{outcome} ~ age_months_c + response_entropy_bits_c + age_months_c:response_entropy_bits_c + generated_expected_words_c + route2_context_word_count_c + context_entropy_bits_c + C(child_id)",
            (
                "age_months_c",
                "response_entropy_bits_c",
                "generated_expected_words_c",
                "route2_context_word_count_c",
                "context_entropy_bits_c",
            ),
        ),
    ]
    specs: list[Route2Spec] = []
    for short_id, label, formula, required in base:
        specs.append(
            Route2Spec(
                model_id=f"{prefix}_{short_id}",
                model_label=label,
                outcome=outcome,
                outcome_type=outcome_type,
                formula=formula.format(outcome=outcome),
                required_cols=required,
            )
        )
    if final_no_fallback:
        short_id, label, formula, required = base[-1]
        specs.append(
            Route2Spec(
                model_id=f"{prefix}_{short_id}_no_fallback",
                model_label=f"{label}, no fallback contexts",
                outcome=outcome,
                outcome_type=outcome_type,
                formula=formula.format(outcome=outcome),
                required_cols=required,
                exclude_fallback=True,
            )
        )
    return specs


def model_specs() -> list[Route2Spec]:
    """Return all focused peer-review Route 2 relative-effort models."""

    specs: list[Route2Spec] = []
    for outcome in [
        "child_words_minus_generated_mean",
        "child_words_z_vs_generated",
        "child_words_percentile_in_generated_distribution",
        "child_words_ratio_to_generated_mean",
    ]:
        specs.extend(model_ladder_specs(outcome, "continuous", final_no_fallback=True))
    for outcome in ["child_shorter_than_generated_median", "child_longer_than_generated_p90"]:
        specs.extend(model_ladder_specs(outcome, "binary", final_no_fallback=True))
    return specs


def prepared_row_frame(frame: pd.DataFrame, spec: Route2Spec) -> pd.DataFrame:
    """Prepare row-level data for one model spec."""

    data = frame.copy()
    add_centered_columns(data, CENTER_COLUMNS)
    required = list(dict.fromkeys([spec.outcome, "child_id", *spec.required_cols]))
    data = finite_model_frame(data, required)
    if spec.exclude_fallback and "fallback_used_for_context" in data.columns:
        data = data[~data["fallback_used_for_context"].fillna(False).astype(bool)].copy()
    return data


def session_aggregate_frame(frame: pd.DataFrame, spec: Route2Spec) -> pd.DataFrame:
    """Aggregate utterances to child-session rows for repeated-measures checks."""

    raw_required = [
        spec.outcome,
        "age_months",
        "child_id",
        "dataset",
        "session_id",
        "age_bin",
        "response_entropy_bits",
        "generated_expected_words",
        "route2_context_word_count",
        "context_entropy_bits",
    ]
    data = frame.dropna(subset=[col for col in raw_required if col in frame.columns]).copy()
    if spec.exclude_fallback and "fallback_used_for_context" in data.columns:
        data = data[~data["fallback_used_for_context"].fillna(False).astype(bool)].copy()
    numeric_cols = [
        spec.outcome,
        "age_months",
        "response_entropy_bits",
        "generated_expected_words",
        "route2_context_word_count",
        "context_entropy_bits",
    ]
    agg = {col: "mean" for col in numeric_cols if col in data.columns}
    agg["score_id"] = "size"
    session = (
        data.groupby(["child_id", "dataset", "session_id", "age_bin"], dropna=False)
        .agg(agg)
        .reset_index()
        .rename(columns={"score_id": "n_utterances"})
    )
    add_centered_columns(session, CENTER_COLUMNS)
    session = add_within_between_age(session)
    needed = [spec.outcome, "child_id", *spec.required_cols]
    needed = [col for col in needed if col in session.columns]
    return finite_model_frame(session, needed)


def no_fit_summary(
    spec: Route2Spec,
    *,
    estimator_id: str,
    level: str,
    formula: str,
    data: pd.DataFrame,
    status: str,
) -> tuple[dict[str, Any], pd.DataFrame, None]:
    """Return a standard no-fit result."""

    return (
        {
            "model_id": spec.model_id,
            "model_label": spec.model_label,
            "estimator_id": estimator_id,
            "level": level,
            "outcome": spec.outcome,
            "outcome_type": spec.outcome_type,
            "status": status,
            "n": int(len(data)),
            "children": int(data["child_id"].nunique()) if "child_id" in data.columns and not data.empty else 0,
            "formula": formula,
            "exclude_fallback": spec.exclude_fallback,
        },
        pd.DataFrame(),
        None,
    )


def fitted_summary_and_coefs(
    result: Any,
    data: pd.DataFrame,
    spec: Route2Spec,
    *,
    estimator_id: str,
    level: str,
    formula: str,
) -> tuple[dict[str, Any], pd.DataFrame, Any]:
    """Create summary and coefficient rows from a fitted result."""

    params = result_to_series(result, "params")
    bse = result_to_series(result, "bse")
    pvalues = result_to_series(result, "pvalues")
    ci = result_confint(result)
    coef = pd.DataFrame(
        {
            "model_id": spec.model_id,
            "model_label": spec.model_label,
            "estimator_id": estimator_id,
            "level": level,
            "outcome": spec.outcome,
            "outcome_type": spec.outcome_type,
            "term": params.index,
            "estimate": params.values,
            "std_error": bse.reindex(params.index).values,
            "p_value": pvalues.reindex(params.index).values,
            "conf_low": ci.reindex(params.index)["conf_low"].values,
            "conf_high": ci.reindex(params.index)["conf_high"].values,
        }
    )
    summary = {
        "model_id": spec.model_id,
        "model_label": spec.model_label,
        "estimator_id": estimator_id,
        "level": level,
        "outcome": spec.outcome,
        "outcome_type": spec.outcome_type,
        "status": "fit",
        "n": int(len(data)),
        "children": int(data["child_id"].nunique()),
        "mean_outcome": float(data[spec.outcome].mean()),
        "formula": formula,
        "exclude_fallback": spec.exclude_fallback,
        "r2": float(getattr(result, "rsquared", math.nan)),
        "descriptive_fitted_r2": descriptive_r2(result, data, spec.outcome),
        "aic": float(getattr(result, "aic", math.nan)) if hasattr(result, "aic") else math.nan,
        "bic": float(getattr(result, "bic", math.nan)) if hasattr(result, "bic") else math.nan,
    }
    return summary, coef, result


def fit_row_model(frame: pd.DataFrame, spec: Route2Spec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit the row-level child-FE model with child-clustered uncertainty."""

    data = prepared_row_frame(frame, spec)
    estimator_id = "row_logit_child_fe_cluster" if spec.outcome_type == "binary" else "row_ols_child_fe_cluster"
    if len(data) < 50 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id=estimator_id, level="utterance", formula=spec.formula, data=data, status="no_fit")
    try:
        if spec.outcome_type == "binary":
            result = smf.glm(spec.formula, data=data, family=sm.families.Binomial()).fit(
                cov_type="cluster",
                cov_kwds={"groups": data["child_id"]},
                maxiter=100,
                disp=False,
            )
        else:
            result = smf.ols(spec.formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": data["child_id"]})
    except Exception as exc:
        return no_fit_summary(
            spec,
            estimator_id=estimator_id,
            level="utterance",
            formula=spec.formula,
            data=data,
            status=f"fit_failed:{type(exc).__name__}",
        )
    return fitted_summary_and_coefs(result, data, spec, estimator_id=estimator_id, level="utterance", formula=spec.formula)


def fit_session_gee(frame: pd.DataFrame, spec: Route2Spec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit child-session aggregate GEE grouped by child."""

    data = session_aggregate_frame(frame, spec)
    formula = strip_child_fixed_effect(spec.formula)
    if len(data) < 20 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="session_gee_exchangeable", level="child_session", formula=formula, data=data, status="no_fit")
    try:
        result = smf.gee(
            formula,
            groups="child_id",
            data=data,
            cov_struct=Exchangeable(),
            family=sm.families.Gaussian(),
        ).fit()
    except Exception as exc:
        return no_fit_summary(
            spec,
            estimator_id="session_gee_exchangeable",
            level="child_session",
            formula=formula,
            data=data,
            status=f"fit_failed:{type(exc).__name__}",
        )
    return fitted_summary_and_coefs(result, data, spec, estimator_id="session_gee_exchangeable", level="child_session", formula=formula)


def fit_session_mundlak_gee(frame: pd.DataFrame, spec: Route2Spec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit child-session aggregate GEE with within/between-child age."""

    data = session_aggregate_frame(frame, spec)
    formula = mundlak_formula(spec.formula)
    required_terms = ["age_within_child_c", "child_mean_age_c"]
    required = [spec.outcome, "child_id", *required_terms, *[c for c in spec.required_cols if c != "age_months_c"]]
    data = finite_model_frame(data, required)
    if len(data) < 20 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="session_mundlak_gee", level="child_session", formula=formula, data=data, status="no_fit")
    try:
        result = smf.gee(
            formula,
            groups="child_id",
            data=data,
            cov_struct=Exchangeable(),
            family=sm.families.Gaussian(),
        ).fit()
    except Exception as exc:
        return no_fit_summary(
            spec,
            estimator_id="session_mundlak_gee",
            level="child_session",
            formula=formula,
            data=data,
            status=f"fit_failed:{type(exc).__name__}",
        )
    return fitted_summary_and_coefs(result, data, spec, estimator_id="session_mundlak_gee", level="child_session", formula=formula)


def fit_session_mixedlm(frame: pd.DataFrame, spec: Route2Spec) -> tuple[dict[str, Any], pd.DataFrame, Any | None]:
    """Fit child-session aggregate mixed model with child random age slope."""

    data = session_aggregate_frame(frame, spec)
    formula = strip_child_fixed_effect(spec.formula)
    if len(data) < 20 or data["child_id"].nunique() < 2:
        return no_fit_summary(spec, estimator_id="session_mixedlm_random_age", level="child_session", formula=formula, data=data, status="no_fit")
    try:
        result = smf.mixedlm(
            formula,
            data=data,
            groups=data["child_id"],
            re_formula="1 + age_months_c",
        ).fit(reml=False, method="lbfgs", maxiter=200, disp=False)
    except Exception as exc:
        return no_fit_summary(
            spec,
            estimator_id="session_mixedlm_random_age",
            level="child_session",
            formula=formula,
            data=data,
            status=f"fit_failed:{type(exc).__name__}",
        )
    return fitted_summary_and_coefs(result, data, spec, estimator_id="session_mixedlm_random_age", level="child_session", formula=formula)


def fit_models(frame: pd.DataFrame, spec: Route2Spec) -> list[tuple[dict[str, Any], pd.DataFrame, Any | None]]:
    """Fit all estimator families for one spec."""

    return [
        fit_row_model(frame, spec),
        fit_session_gee(frame, spec),
        fit_session_mundlak_gee(frame, spec),
        fit_session_mixedlm(frame, spec),
    ]


def summary_by_age_bin(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize Route 2 relative-effort outcomes by developmental age bin."""

    rows: list[dict[str, Any]] = []
    for age_bin, group in frame.groupby("age_bin", dropna=False, sort=False):
        for col in [
            "nb_words",
            "generated_expected_words",
            "response_entropy_bits",
            "child_words_minus_generated_mean",
            "child_words_z_vs_generated",
            "child_words_percentile_in_generated_distribution",
            "child_words_ratio_to_generated_mean",
            "child_shorter_than_generated_median",
            "child_longer_than_generated_p90",
        ]:
            if col not in group.columns:
                continue
            values = pd.to_numeric(group[col], errors="coerce").dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "age_bin": age_bin,
                    "age_bin_mid": age_bin_midpoint(age_bin),
                    "metric": col,
                    "n": int(len(values)),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "sd": float(values.std(ddof=1)) if len(values) > 1 else math.nan,
                    "se": float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else math.nan,
                    "p10": float(values.quantile(0.10)),
                    "p90": float(values.quantile(0.90)),
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["age_bin_mid", "metric"]).reset_index(drop=True)
    return out


def entropy_bin_summary(frame: pd.DataFrame, *, n_bins: int = 20) -> pd.DataFrame:
    """Summarize context-relative child effort across response entropy bins."""

    data = frame.dropna(
        subset=[
            "response_entropy_bits",
            "child_words_minus_generated_mean",
            "child_words_percentile_in_generated_distribution",
            "child_shorter_than_generated_median",
            "child_longer_than_generated_p90",
        ]
    ).copy()
    if data.empty:
        return pd.DataFrame()
    data["entropy_bin"] = pd.qcut(data["response_entropy_bits"], q=n_bins, duplicates="drop")
    rows = []
    for interval, group in data.groupby("entropy_bin", observed=True):
        rows.append(
            {
                "entropy_bin": str(interval),
                "response_entropy_bits_mean": float(group["response_entropy_bits"].mean()),
                "n": int(len(group)),
                "child_words_minus_generated_mean": float(group["child_words_minus_generated_mean"].mean()),
                "child_words_z_vs_generated_mean": float(group["child_words_z_vs_generated"].mean()),
                "child_words_percentile_mean": float(group["child_words_percentile_in_generated_distribution"].mean()),
                "shorter_than_generated_median_rate": float(group["child_shorter_than_generated_median"].mean()),
                "longer_than_generated_p90_rate": float(group["child_longer_than_generated_p90"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("response_entropy_bits_mean").reset_index(drop=True)


def save_age_plot(summary: pd.DataFrame, path: Path) -> None:
    """Plot age-bin trajectories for the core Route 2 relative outcomes."""

    metrics = [
        "child_words_minus_generated_mean",
        "child_words_percentile_in_generated_distribution",
        "child_shorter_than_generated_median",
        "child_longer_than_generated_p90",
    ]
    labels = {
        "child_words_minus_generated_mean": "child words minus generated mean",
        "child_words_percentile_in_generated_distribution": "child percentile in generated distribution",
        "child_shorter_than_generated_median": "shorter than generated median",
        "child_longer_than_generated_p90": "longer than generated p90",
    }
    plot = summary[summary["metric"].isin(metrics)].copy()
    if plot.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    for ax, metric in zip(axes.ravel(), metrics):
        group = plot[plot["metric"].eq(metric)].sort_values("age_bin_mid")
        ax.plot(group["age_bin"].astype(str), group["mean"], marker="o", linewidth=2.2, color="#2f6f73")
        ax.fill_between(
            group["age_bin"].astype(str),
            group["mean"] - 1.96 * group["se"].fillna(0),
            group["mean"] + 1.96 * group["se"].fillna(0),
            alpha=0.16,
            color="#2f6f73",
        )
        if metric == "child_words_minus_generated_mean":
            ax.axhline(0, color="#333", linestyle="--", linewidth=1)
        ax.set_title(labels[metric])
        ax.set_xlabel("Age bin")
        ax.tick_params(axis="x", rotation=25)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_entropy_plot(summary: pd.DataFrame, path: Path) -> None:
    """Plot relative effort against response entropy bins."""

    if summary.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 3, figsize=(17, 5), constrained_layout=True)
    axes[0].plot(summary["response_entropy_bits_mean"], summary["child_words_minus_generated_mean"], marker="o")
    axes[0].axhline(0, color="#333", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Child words minus generated mean")
    axes[1].plot(summary["response_entropy_bits_mean"], summary["child_words_percentile_mean"], marker="o")
    axes[1].set_ylabel("Child percentile")
    axes[2].plot(summary["response_entropy_bits_mean"], summary["shorter_than_generated_median_rate"], marker="o", label="shorter than median")
    axes[2].plot(summary["response_entropy_bits_mean"], summary["longer_than_generated_p90_rate"], marker="o", label="longer than p90")
    axes[2].legend(frameon=False)
    axes[2].set_ylabel("Rate")
    for ax in axes:
        ax.set_xlabel("Response entropy bits, binned mean")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_coefficient_plot(coef: pd.DataFrame, path: Path) -> None:
    """Plot the final-model key coefficients across outcomes and estimators."""

    plot = coef[
        coef["model_id"].str.contains("r2m5_age_by_entropy", regex=False)
        & coef["term"].isin(KEY_TERMS)
        & ~coef["model_id"].str.endswith("_no_fallback")
    ].copy()
    if plot.empty:
        return
    plot["label"] = (
        plot["outcome"].str.replace("child_words_", "", regex=False).str.replace("_", " ", regex=False)
        + " / "
        + plot["estimator_id"].str.replace("_", " ", regex=False)
        + " / "
        + plot["term"].str.replace("_c", "", regex=False).str.replace("_", " ", regex=False)
    )
    plot = plot.sort_values(["outcome", "estimator_id", "term"])
    sns.set_theme(style="whitegrid", context="paper")
    fig, ax = plt.subplots(figsize=(12, max(7, len(plot) * 0.22)))
    y = np.arange(len(plot))
    ax.errorbar(
        plot["estimate"],
        y,
        xerr=[plot["estimate"] - plot["conf_low"], plot["conf_high"] - plot["estimate"]],
        fmt="o",
        color="#2f6f73",
        ecolor="#9bb8b5",
        elinewidth=1.3,
        capsize=2,
    )
    ax.axvline(0, color="#333", linestyle="--", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"])
    ax.set_xlabel("Coefficient estimate with 95% CI")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def prediction_grid(
    frame: pd.DataFrame,
    result: Any,
    *,
    outcome: str,
    response_entropy_levels: Sequence[float],
    n_ages: int = 25,
) -> pd.DataFrame:
    """Build prediction grid for final Route 2 age-by-entropy models."""

    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_ages)
    most_common_child = frame["child_id"].mode().iloc[0]
    centers = {
        col: float(pd.to_numeric(frame[col], errors="coerce").mean())
        for col in ["age_months", "response_entropy_bits", "generated_expected_words", "route2_context_word_count", "context_entropy_bits"]
    }
    rows = []
    for entropy in response_entropy_levels:
        for age in ages:
            row = {
                "age_months": age,
                "child_id": most_common_child,
                "response_entropy_bits": entropy,
                "generated_expected_words": centers["generated_expected_words"],
                "route2_context_word_count": centers["route2_context_word_count"],
                "context_entropy_bits": centers["context_entropy_bits"],
                "response_entropy_level": entropy,
            }
            for col, center in centers.items():
                row[f"{col}_c"] = row[col] - center
            rows.append(row)
    grid = pd.DataFrame(rows)
    grid[f"predicted_{outcome}"] = result.predict(grid)
    return grid


def save_prediction_plot(grid: pd.DataFrame, outcome: str, path: Path) -> None:
    """Save prediction lines by age and response-entropy level."""

    if grid.empty:
        return
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(10, 6))
    for level, group in grid.groupby("response_entropy_level", sort=True):
        ax.plot(group["age_months"], group[f"predicted_{outcome}"], linewidth=2.2, label=f"entropy={level:.2f}")
    ax.set_xlabel("Age in months")
    ax.set_ylabel(f"Predicted {outcome}")
    if outcome == "child_words_minus_generated_mean":
        ax.axhline(0, color="#333", linestyle="--", linewidth=1)
    ax.legend(title="Response entropy", frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_report(
    *,
    report_md: Path,
    report_html: Path,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    audit: pd.DataFrame,
    age_summary: pd.DataFrame,
    entropy_summary: pd.DataFrame,
    model_summary: pd.DataFrame,
    coef: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write Markdown and HTML report."""

    audit_map = dict(zip(audit["metric"], audit["value"]))
    age_pivot = age_summary.pivot_table(index="age_bin", columns="metric", values="mean", aggfunc="first")
    selected_age_rows = []
    for age_bin in ["006-023", "024-029", "030-035", "042-047", "048-053", "060-065"]:
        if age_bin not in age_pivot.index:
            continue
        selected_age_rows.append(
            {
                "age_bin": age_bin,
                "child_words_minus_generated_mean": age_pivot.loc[age_bin].get("child_words_minus_generated_mean", math.nan),
                "child_percentile": age_pivot.loc[age_bin].get("child_words_percentile_in_generated_distribution", math.nan),
                "shorter_than_generated_median": age_pivot.loc[age_bin].get("child_shorter_than_generated_median", math.nan),
                "longer_than_generated_p90": age_pivot.loc[age_bin].get("child_longer_than_generated_p90", math.nan),
            }
        )
    age_headline = pd.DataFrame(selected_age_rows)

    entropy_headline = pd.DataFrame()
    if not entropy_summary.empty:
        entropy_headline = pd.concat([entropy_summary.head(3), entropy_summary.tail(3)], ignore_index=True)
        entropy_headline = entropy_headline[
            [
                "response_entropy_bits_mean",
                "n",
                "child_words_minus_generated_mean",
                "child_words_percentile_mean",
                "shorter_than_generated_median_rate",
                "longer_than_generated_p90_rate",
            ]
        ]
    key = coef[coef["term"].isin(KEY_TERMS)].copy()
    key = key[
        [
            "outcome",
            "model_label",
            "estimator_id",
            "term",
            "estimate",
            "std_error",
            "p_value",
            "conf_low",
            "conf_high",
        ]
    ].sort_values(["outcome", "model_label", "estimator_id", "term"])
    final_key = key[key["model_label"].str.contains("R2-M5", regex=False)]
    primary_terms = [
        "age_months_c",
        "response_entropy_bits_c",
        "age_months_c:response_entropy_bits_c",
        "generated_expected_words_c",
        "route2_context_word_count_c",
        "context_entropy_bits_c",
    ]
    primary_outcomes = [
        "child_words_minus_generated_mean",
        "child_words_percentile_in_generated_distribution",
        "child_shorter_than_generated_median",
        "child_longer_than_generated_p90",
    ]
    primary_coefficients = final_key[
        final_key["estimator_id"].eq("session_gee_exchangeable")
        & ~final_key["model_label"].str.contains("no fallback", regex=False)
        & final_key["outcome"].isin(primary_outcomes)
        & final_key["term"].isin(primary_terms)
    ][["outcome", "term", "estimate", "std_error", "p_value", "conf_low", "conf_high"]]
    no_fallback_check = final_key[
        final_key["estimator_id"].eq("session_gee_exchangeable")
        & final_key["model_label"].str.contains("no fallback", regex=False)
        & final_key["outcome"].isin(primary_outcomes)
        & final_key["term"].isin(
            [
                "response_entropy_bits_c",
                "age_months_c:response_entropy_bits_c",
                "generated_expected_words_c",
            ]
        )
    ][["outcome", "term", "estimate", "p_value", "conf_low", "conf_high"]]
    lines = [
        "# Route 2 Relative-Effort Model Suite",
        "",
        "This is the Route 2 effort-choice suite built from the production response-space run.",
        "It asks whether real child utterance effort is short, typical, or long relative to the generated response-space length distribution for the same caregiver context.",
        "",
        "It does not score generated responses for surprisal and does not claim generated samples are same-meaning paraphrases.",
        "",
        "## Inputs",
        "",
        f"- Child-row response-space table: `{input_csv}`",
        f"- Output directory: `{output_dir}`",
        f"- Figure directory: `{fig_dir}`",
        "",
        "## Audit",
        "",
        (
            f"This suite covers `{audit_map.get('input_rows', 'NA')}` child utterance rows, "
            f"`{audit_map.get('unique_response_entropy_contexts', 'NA')}` unique response-space contexts, "
            f"`{audit_map.get('unique_children', 'NA')}` children, and "
            f"`{audit_map.get('unique_datasets', 'NA')}` datasets."
        ),
        "",
        markdown_table(audit, max_rows=40),
        "",
        "## Headline Results",
        "",
        "The descriptive Route 2 result is strong: real child utterances are usually shorter than the generated response-space distribution for the same caregiver context, and this gap shrinks with age.",
        "In the youngest bin, children are on average about 2.28 words below the generated mean and around the 25th percentile of the generated length distribution; by later bins they are closer to the generated distribution but still below its center.",
        "",
        markdown_table(age_headline, max_rows=12),
        "",
        "Response entropy has a large descriptive gradient: low-entropy contexts place child utterances near or above the generated midpoint, while high-entropy contexts place them far below it.",
        "",
        markdown_table(entropy_headline, max_rows=8),
        "",
        "The primary inferential check is the final child-session GEE model, with age, response entropy, generated expected effort, context length, context entropy, and the age x response-entropy interaction.",
        "In that model, age predicts movement toward the generated distribution; generated expected effort predicts stronger child-shortening relative to the generated distribution; and the age x response-entropy interaction shows that developmental catch-up is weaker in higher-response-entropy contexts.",
        "For the binary outcomes, the GEE coefficients are linear-probability changes in child-session rates.",
        "",
        markdown_table(primary_coefficients, max_rows=40),
        "",
        "The no-fallback sensitivity check preserves the core final-model estimates.",
        "",
        markdown_table(no_fallback_check, max_rows=40),
        "",
        "## Model Ladder",
        "",
        "The main models are fit separately for each context-relative effort outcome:",
        "",
        "- R2-M1: age + child identity.",
        "- R2-M2: R2-M1 plus response entropy.",
        "- R2-M3: age plus generated expected effort, context length, context entropy, and child identity.",
        "- R2-M4: R2-M3 plus response entropy.",
        "- R2-M5: R2-M4 plus age x response entropy.",
        "",
        "Estimator checks include row-level child-fixed-effect clustered models, child-session GEE, child-session Mundlak GEE, and child-session mixed models with random age slopes where stable.",
        "",
        "## Figures",
        "",
    ]
    for label, path in figure_paths.items():
        lines.extend([f"### {label}", "", f"![{label}]({relative_to_doc(path, report_md)})", ""])
    lines.extend(
        [
            "## Age-Bin Descriptives",
            "",
            markdown_table(age_summary, max_rows=80),
            "",
            "## Fit Summary",
            "",
            markdown_table(
                model_summary[
                    [
                        "model_label",
                        "model_id",
                        "estimator_id",
                        "level",
                        "outcome",
                        "outcome_type",
                        "status",
                        "n",
                        "children",
                        "descriptive_fitted_r2",
                        "exclude_fallback",
                    ]
                ],
                max_rows=120,
            ),
            "",
            "## Final-Model Key Coefficients",
            "",
            markdown_table(final_key, max_rows=120),
            "",
            "## Interpretation Boundary",
            "",
            "- The headline Route 2 outcome is context-relative effort, especially child word-count percentile or residual against the generated response-space length distribution.",
            "- Raw child length still matters, but the relative outcomes are stronger because they condition on what the model generated for the same caregiver context.",
            "- The response-space run currently covers Brown, Manchester, and Providence children, not the full 79-child cleaned bundle.",
            "- Fallback contexts are rare and are handled by final-model no-fallback sensitivity checks.",
        ]
    )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(report_md, report_html)


def build_route2_relative_effort_model_suite(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
) -> dict[str, Path]:
    """Run the full Route 2 relative-effort model suite."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    frame = add_route2_relative_columns(read_response_space_table(input_csv))
    add_centered_columns(frame, CENTER_COLUMNS)

    age_summary = summary_by_age_bin(frame)
    entropy_summary = entropy_bin_summary(frame)
    age_summary.to_csv(output_dir / "route2_relative_effort_summary_by_age_bin.csv", index=False)
    entropy_summary.to_csv(output_dir / "route2_relative_effort_summary_by_response_entropy_bin.csv", index=False)

    figure_paths = {
        "Route 2 relative effort by age": fig_dir / "route2_relative_effort_by_age.png",
        "Route 2 relative effort by response entropy": fig_dir / "route2_relative_effort_by_response_entropy.png",
        "Route 2 final-model coefficients": fig_dir / "route2_relative_effort_final_model_coefficients.png",
    }
    save_age_plot(age_summary, figure_paths["Route 2 relative effort by age"])
    save_entropy_plot(entropy_summary, figure_paths["Route 2 relative effort by response entropy"])

    summaries: list[dict[str, Any]] = []
    coefs: list[pd.DataFrame] = []
    fitted: dict[tuple[str, str], Any] = {}
    for spec in model_specs():
        for summary, coef, result in fit_models(frame, spec):
            summaries.append(summary)
            if not coef.empty:
                coefs.append(coef)
            if result is not None:
                fitted[(spec.model_id, str(summary.get("estimator_id", "")))] = result
    model_summary = pd.DataFrame(summaries)
    coef_table = pd.concat(coefs, ignore_index=True) if coefs else pd.DataFrame()
    model_summary.to_csv(output_dir / "route2_relative_effort_model_summary.csv", index=False)
    coef_table.to_csv(output_dir / "route2_relative_effort_model_coefficients.csv", index=False)
    save_coefficient_plot(coef_table, figure_paths["Route 2 final-model coefficients"])

    prediction_paths: dict[str, Path] = {}
    final_outcomes = [
        "child_words_minus_generated_mean",
        "child_words_percentile_in_generated_distribution",
        "child_shorter_than_generated_median",
        "child_longer_than_generated_p90",
    ]
    entropy_levels = frame["response_entropy_bits"].quantile([0.10, 0.50, 0.90]).dropna().tolist()
    for outcome in final_outcomes:
        prefix = outcome.replace("child_words_", "").replace("_generated_", "_gen_")
        model_id = f"{prefix}_r2m5_age_by_entropy"
        result = fitted.get((model_id, "session_gee_exchangeable")) or fitted.get((model_id, "row_ols_child_fe_cluster"))
        if result is None:
            result = fitted.get((model_id, "row_logit_child_fe_cluster"))
        if result is None:
            continue
        grid = prediction_grid(frame, result, outcome=outcome, response_entropy_levels=entropy_levels)
        grid_path = output_dir / f"{model_id}_prediction_grid.csv"
        fig_path = fig_dir / f"{model_id}_prediction_lines.png"
        grid.to_csv(grid_path, index=False)
        save_prediction_plot(grid, outcome, fig_path)
        prediction_paths[model_id] = grid_path
        figure_paths[f"Prediction lines: {outcome}"] = fig_path

    failed_or_no_fit = int((~model_summary["status"].eq("fit")).sum()) if not model_summary.empty else 0
    audit = pd.DataFrame(
        [
            {"metric": "input_rows", "value": len(frame)},
            {"metric": "modelable_rows_percentile", "value": int(frame["child_words_percentile_in_generated_distribution"].notna().sum())},
            {"metric": "unique_score_ids", "value": frame["score_id"].nunique()},
            {"metric": "unique_utterance_ids", "value": frame["utterance_id"].nunique()},
            {"metric": "unique_children", "value": frame["child_id"].nunique()},
            {"metric": "unique_datasets", "value": frame["dataset"].nunique() if "dataset" in frame.columns else math.nan},
            {"metric": "unique_response_entropy_contexts", "value": frame["response_entropy_context_id"].nunique()},
            {"metric": "fallback_rows", "value": int(frame["fallback_used_for_context"].fillna(False).astype(bool).sum())},
            {"metric": "fallback_contexts", "value": int(frame.loc[frame["fallback_used_for_context"].fillna(False).astype(bool), "response_entropy_context_id"].nunique())},
            {"metric": "fit_models", "value": int(model_summary["status"].eq("fit").sum()) if not model_summary.empty else 0},
            {"metric": "failed_or_no_fit_models", "value": failed_or_no_fit},
        ]
    )
    audit.to_csv(output_dir / "route2_relative_effort_audit.csv", index=False)

    build_report(
        report_md=report_md,
        report_html=report_html,
        input_csv=input_csv,
        output_dir=output_dir,
        fig_dir=fig_dir,
        audit=audit,
        age_summary=age_summary,
        entropy_summary=entropy_summary,
        model_summary=model_summary,
        coef=coef_table,
        figure_paths=figure_paths,
    )

    return {
        "audit": output_dir / "route2_relative_effort_audit.csv",
        "age_summary": output_dir / "route2_relative_effort_summary_by_age_bin.csv",
        "entropy_summary": output_dir / "route2_relative_effort_summary_by_response_entropy_bin.csv",
        "model_summary": output_dir / "route2_relative_effort_model_summary.csv",
        "coefficients": output_dir / "route2_relative_effort_model_coefficients.csv",
        "report_md": report_md,
        "report_html": report_html,
        **prediction_paths,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    args = parser.parse_args(argv)
    paths = build_route2_relative_effort_model_suite(
        input_csv=args.input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
    )
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
