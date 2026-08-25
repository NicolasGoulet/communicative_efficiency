#!/usr/bin/env python3
"""Build a four-page Route 1 / Route 2 / word-surprisal report site.

The audited August supervisor package remains the complete evidence archive.
This builder reorganizes frozen saved model products into a supervisor-facing
reading path.  Its only new fit is an explicitly diagnostic effort-only bridge
between raw Route 1 trajectories and the registered child-adjusted model; it
does not select or replace any frozen result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/august_routes_report")
DEFAULT_FIG_DIR = DEFAULT_OUTPUT_DIR / "plots"
DEFAULT_REPORT_MD = Path("docs/august_routes_report.md")
DEFAULT_REPORT_HTML = Path("docs/august_routes_report.html")

PROTECTED_RELATIVE_PATHS = (
    Path("docs/august_supervisor_index.html"),
    Path("docs/august_supervisor_report.md"),
    Path("docs/august_supervisor_report.html"),
    Path("results/august_supervisor_report/AUGUST_REPORT_COMPLETE_AND_AUDITED"),
)

ROUTE1_MODEL_ORDER = (
    "P1_k3_contextual",
    "P1_k3_contextual_quadratic",
    "P1_k3_contextual_mundlak",
    "P1_k3_contextual_gee",
)

ROUTE1_MODEL_METADATA = {
    "P1_k3_contextual": (
        "Linear child-adjusted",
        "exact word-effort cells; child fixed effects; 95% interval clustered by child",
    ),
    "P1_k3_contextual_quadratic": (
        "Nonlinear age",
        "adds age squared; reported coefficient is the local slope at centered age; child fixed effects; clustered by child",
    ),
    "P1_k3_contextual_mundlak": (
        "Within/between child",
        "separates within-child age from between-child mean age; corpus controls; clustered by child",
    ),
    "P1_k3_contextual_gee": (
        "Repeated-measures GEE",
        "Gaussian GEE with exchangeable within-child correlation; exact word-effort controls",
    ),
}

ROUTE2_ESTIMATOR_ORDER = (
    "row_ols_child_fe_cluster",
    "session_gee_exchangeable",
    "session_mundlak_gee",
    "session_mixedlm_random_age",
)

ROUTE2_ESTIMATOR_METADATA = {
    "row_ols_child_fe_cluster": (
        "Linear child-fixed baseline",
        "utterance rows; child fixed effects; uncertainty clustered by child",
    ),
    "session_gee_exchangeable": (
        "Session GEE",
        "child-session means; exchangeable repeated observations grouped by child",
    ),
    "session_mundlak_gee": (
        "Within/between-child GEE",
        "separates within-child age from child mean age; grouped by child",
    ),
    "session_mixedlm_random_age": (
        "Mixed model",
        "child-session means; random child intercept and age slope",
    ),
}

WORD_QUESTION_ORDER = (
    "same_word_k0_age",
    "same_word_k3_age",
    "context_gain_age",
    "longer_words_context_support",
)

WORD_QUESTION_LABELS = {
    "same_word_k0_age": "Same-word unconditional age slope",
    "same_word_k3_age": "Same-word contextual age slope",
    "context_gain_age": "Word context-gain age slope",
    "longer_words_context_support": "Longer-word context support",
}

SCORER_ORDER = ("Mistral", "Qwen3-14B", "TinyDialogues")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        frame.to_csv(temporary, index=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.tmp-{os.getpid()}{path.suffix}")
    try:
        fig.savefig(temporary, dpi=190, bbox_inches="tight")
        os.replace(temporary, path)
    finally:
        plt.close(fig)
        temporary.unlink(missing_ok=True)


def require_status(path: Path, *, key: str, expected: object) -> Mapping[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"required manifest is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    actual = payload.get(key)
    if actual != expected:
        raise RuntimeError(f"{path}: expected {expected} for {key}, found {actual}")
    return payload


def protected_hashes(paths: Sequence[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"protected audited artifact is missing: {resolved}")
        hashes[str(resolved)] = sha256_file(resolved)
    return hashes


def assert_protected_unchanged(before: Mapping[str, str]) -> None:
    for raw_path, expected in before.items():
        path = Path(raw_path)
        if not path.exists() or sha256_file(path) != expected:
            raise RuntimeError(f"protected audited artifact changed: {path}")


def _required_columns(frame: pd.DataFrame, columns: Sequence[str], *, label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise RuntimeError(f"{label} is missing columns: {missing}")


def route1_ladder(summary: pd.DataFrame, *, scorer: str, scope: str) -> pd.DataFrame:
    required = [
        "scope",
        "model_id",
        "estimator",
        "age_term",
        "age_estimate",
        "age_ci_low",
        "age_ci_high",
        "age_p_value",
        "fit_status",
        "children",
        "source_rows",
    ]
    _required_columns(summary, required, label=f"Route 1 {scorer}")
    selected = summary[
        summary["scope"].eq(scope) & summary["model_id"].isin(ROUTE1_MODEL_ORDER)
    ].copy()
    if set(selected["model_id"]) != set(ROUTE1_MODEL_ORDER):
        missing = sorted(set(ROUTE1_MODEL_ORDER) - set(selected["model_id"]))
        raise RuntimeError(f"Route 1 {scorer}/{scope} is missing ladder models: {missing}")
    if not selected["fit_status"].eq("PASS").all():
        bad = selected.loc[~selected["fit_status"].eq("PASS"), "model_id"].tolist()
        raise RuntimeError(f"Route 1 {scorer}/{scope} contains non-PASS models: {bad}")
    order = {model_id: index for index, model_id in enumerate(ROUTE1_MODEL_ORDER)}
    selected["_order"] = selected["model_id"].map(order)
    selected = selected.sort_values("_order")
    rows = []
    for row in selected.itertuples(index=False):
        model, adjustment = ROUTE1_MODEL_METADATA[row.model_id]
        rows.append(
            {
                "scorer": scorer,
                "scope": scope,
                "model": model,
                "estimator": row.estimator,
                "adjustment": adjustment,
                "age_term": row.age_term,
                "estimate": row.age_estimate,
                "ci_low": row.age_ci_low,
                "ci_high": row.age_ci_high,
                "p_value": row.age_p_value,
                "children": int(row.children),
                "source_rows": int(row.source_rows),
            }
        )
    return pd.DataFrame(rows)


def attach_route1_bootstrap(ladder: pd.DataFrame, bootstrap: pd.DataFrame, *, scope: str) -> pd.DataFrame:
    required = ["scope", "model_id", "successful_reps", "bootstrap_ci_low", "bootstrap_ci_high"]
    _required_columns(bootstrap, required, label="Route 1 bootstrap")
    match = bootstrap[
        bootstrap["scope"].eq(scope) & bootstrap["model_id"].eq("P1_k3_contextual")
    ]
    if len(match) != 1:
        raise RuntimeError(f"expected one Route 1 bootstrap row for {scope}, found {len(match)}")
    row = match.iloc[0]
    result = ladder.copy()
    result["bootstrap_reps"] = np.nan
    result["bootstrap_ci_low"] = np.nan
    result["bootstrap_ci_high"] = np.nan
    primary = result["model"].eq("Linear child-adjusted")
    result.loc[primary, "bootstrap_reps"] = int(row["successful_reps"])
    result.loc[primary, "bootstrap_ci_low"] = float(row["bootstrap_ci_low"])
    result.loc[primary, "bootstrap_ci_high"] = float(row["bootstrap_ci_high"])
    return result


def route2_final_ladder(coefficients: pd.DataFrame, *, term_role: str) -> pd.DataFrame:
    required = ["model_id", "estimator_id", "term", "estimate", "conf_low", "conf_high", "p_value"]
    _required_columns(coefficients, required, label="Route 2 coefficients")
    if term_role not in {"age", "interaction"}:
        raise ValueError(f"invalid Route 2 term role: {term_role}")
    term_by_estimator = {
        "row_ols_child_fe_cluster": (
            "age_months_c" if term_role == "age" else "age_months_c:response_entropy_bits_c"
        ),
        "session_gee_exchangeable": (
            "age_months_c" if term_role == "age" else "age_months_c:response_entropy_bits_c"
        ),
        "session_mundlak_gee": (
            "age_within_child_c"
            if term_role == "age"
            else "age_within_child_c:response_entropy_bits_c"
        ),
        "session_mixedlm_random_age": (
            "age_months_c" if term_role == "age" else "age_months_c:response_entropy_bits_c"
        ),
    }
    data = coefficients[
        coefficients["model_id"].eq("minus_gen_mean_r2m5_age_by_entropy")
        & coefficients["estimator_id"].isin(ROUTE2_ESTIMATOR_ORDER)
    ].copy()
    rows = []
    for estimator in ROUTE2_ESTIMATOR_ORDER:
        term = term_by_estimator[estimator]
        match = data[data["estimator_id"].eq(estimator) & data["term"].eq(term)]
        if len(match) != 1:
            raise RuntimeError(
                f"expected one Route 2 {term_role} row for {estimator}/{term}, found {len(match)}"
            )
        row = match.iloc[0]
        model, adjustment = ROUTE2_ESTIMATOR_METADATA[estimator]
        rows.append(
            {
                "model": model,
                "estimator": estimator,
                "adjustment": adjustment,
                "term": term,
                "estimate": row["estimate"],
                "ci_low": row["conf_low"],
                "ci_high": row["conf_high"],
                "p_value": row["p_value"],
            }
        )
    return pd.DataFrame(rows)


def word_effect_table(effects: pd.DataFrame) -> pd.DataFrame:
    required = [
        "scorer",
        "question_id",
        "model_id",
        "estimate",
        "ci_low",
        "ci_high",
        "bootstrap_ci_low",
        "bootstrap_ci_high",
    ]
    _required_columns(effects, required, label="word effects")
    selected = effects[effects["question_id"].isin(WORD_QUESTION_ORDER)].copy()
    present_questions = [
        question for question in WORD_QUESTION_ORDER if question in set(selected["question_id"])
    ]
    if not present_questions:
        raise RuntimeError("word effects contain none of the requested scientific questions")
    expected = {(question, scorer) for question in present_questions for scorer in SCORER_ORDER}
    actual = set(zip(selected["question_id"], selected["scorer"]))
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(f"word effect grid mismatch: missing={missing} extra={extra}")
    if selected.duplicated(["question_id", "scorer"]).any():
        raise RuntimeError("word effects contain duplicate question/scorer rows")
    question_order = {value: index for index, value in enumerate(WORD_QUESTION_ORDER)}
    scorer_order = {value: index for index, value in enumerate(SCORER_ORDER)}
    selected["_q"] = selected["question_id"].map(question_order)
    selected["_s"] = selected["scorer"].map(scorer_order)
    selected = selected.sort_values(["_q", "_s"])
    rows = []
    for row in selected.itertuples(index=False):
        same_word = row.question_id.startswith("same_word") or row.question_id == "context_gain_age"
        adjustment = (
            "child and word fixed effects; position, utterance length, and singleton controls; "
            "child-clustered interval; 1,000-replicate child bootstrap"
            if same_word
            else "corpus fixed effects; word length and leave-corpus-out rarity; child-clustered "
            "interval; 1,000-replicate child bootstrap"
        )
        rows.append(
            {
                "question_id": row.question_id,
                "question": WORD_QUESTION_LABELS[row.question_id],
                "scorer": row.scorer,
                "model_id": row.model_id,
                "estimate": row.estimate,
                "ci_low": row.ci_low,
                "ci_high": row.ci_high,
                "bootstrap_ci_low": row.bootstrap_ci_low,
                "bootstrap_ci_high": row.bootstrap_ci_high,
                "adjustment": adjustment,
            }
        )
    return pd.DataFrame(rows)


def fit_effort_only_diagnostic(
    cells: pd.DataFrame,
    *,
    points: int = 60,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Fit the July-style effort-only diagnostic on frozen exact design cells.

    This intentionally omits child identity.  It is a descriptive bridge from
    Model 0 to the registered child-adjusted Model 2 and must never replace the
    frozen primary inference.
    """

    required = [
        "age_months",
        "age_c",
        "word_count_exact_top12",
        "outcome_mean",
        "row_count",
    ]
    _required_columns(cells, required, label="effort-only diagnostic cells")
    data = cells.dropna(subset=required).copy()
    data["word_count_exact_top12"] = data["word_count_exact_top12"].astype(str)
    if data.empty or data["age_months"].nunique() < 2:
        raise RuntimeError("effort-only diagnostic has insufficient age support")
    formula = "outcome_mean ~ age_c + C(word_count_exact_top12)"
    result = smf.wls(formula, data=data, weights=data["row_count"]).fit(cov_type="HC1")
    interval = result.conf_int().loc["age_c"]
    summary = {
        "formula": formula,
        "estimator": "exact-cell WLS, HC1; no child identity",
        "age_estimate": float(result.params["age_c"]),
        "age_std_error": float(result.bse["age_c"]),
        "ci_low": float(interval.iloc[0]),
        "ci_high": float(interval.iloc[1]),
        "p_value": float(result.pvalues["age_c"]),
        "source_rows": int(data["row_count"].sum()),
        "design_cells": int(len(data)),
        "children": int(data["child_key"].nunique()) if "child_key" in data else np.nan,
    }
    ages = np.linspace(float(data["age_months"].min()), float(data["age_months"].max()), points)
    center = float(np.average(data["age_months"], weights=data["row_count"]))
    available = set(data["word_count_exact_top12"])
    preferred = [level for level in ["1", "2", "4", "6"] if level in available]
    if not preferred:
        preferred = sorted(available)[:4]
    frames = []
    for level in preferred:
        new = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - center,
                "word_count_exact_top12": [level] * len(ages),
            }
        )
        predicted = result.get_prediction(new).summary_frame(alpha=0.05)
        frames.append(
            pd.DataFrame(
                {
                    "age_months": ages,
                    "word_count_exact_top12": level,
                    "predicted_mean": predicted["mean"].to_numpy(float),
                    "ci_low": predicted["mean_ci_lower"].to_numpy(float),
                    "ci_high": predicted["mean_ci_upper"].to_numpy(float),
                }
            )
        )
    return summary, pd.concat(frames, ignore_index=True)


def route2_model_implied_lines(
    coefficients: pd.DataFrame,
    reference_grid: pd.DataFrame,
    *,
    points: int = 60,
) -> pd.DataFrame:
    """Return centered regression lines for all final Route 2 estimators."""

    _required_columns(
        coefficients,
        ["model_id", "estimator_id", "term", "estimate"],
        label="Route 2 coefficients",
    )
    _required_columns(
        reference_grid,
        [
            "age_months",
            "age_months_c",
            "response_entropy_level",
            "response_entropy_bits_c",
        ],
        label="Route 2 reference grid",
    )
    model_id = "percentile_in_gen_distribution_r2m5_age_by_entropy"
    terms = {
        "row_ols_child_fe_cluster": (
            "age_months_c",
            "age_months_c:response_entropy_bits_c",
        ),
        "session_gee_exchangeable": (
            "age_months_c",
            "age_months_c:response_entropy_bits_c",
        ),
        "session_mundlak_gee": (
            "age_within_child_c",
            "age_within_child_c:response_entropy_bits_c",
        ),
        "session_mixedlm_random_age": (
            "age_months_c",
            "age_months_c:response_entropy_bits_c",
        ),
    }
    model_labels = {
        "row_ols_child_fe_cluster": "Child-FE row model",
        "session_gee_exchangeable": "Session GEE",
        "session_mundlak_gee": "Within/between-child GEE",
        "session_mixedlm_random_age": "Mixed model",
    }
    data = coefficients[coefficients["model_id"].eq(model_id)].copy()
    reference_age = float(
        np.median(reference_grid["age_months"] - reference_grid["age_months_c"])
    )
    age_values = np.linspace(
        float(reference_grid["age_months"].min()),
        float(reference_grid["age_months"].max()),
        points,
    )
    level_frame = (
        reference_grid[["response_entropy_level", "response_entropy_bits_c"]]
        .drop_duplicates()
        .sort_values("response_entropy_level")
    )
    rows = []
    for estimator, (age_term, interaction_term) in terms.items():
        age_match = data[data["estimator_id"].eq(estimator) & data["term"].eq(age_term)]
        interaction_match = data[
            data["estimator_id"].eq(estimator) & data["term"].eq(interaction_term)
        ]
        if len(age_match) != 1 or len(interaction_match) != 1:
            raise RuntimeError(
                f"Route 2 line terms missing for {estimator}: "
                f"age={len(age_match)} interaction={len(interaction_match)}"
            )
        age_beta = float(age_match.iloc[0]["estimate"])
        interaction_beta = float(interaction_match.iloc[0]["estimate"])
        for level in level_frame.itertuples(index=False):
            entropy_c = float(level.response_entropy_bits_c)
            slope = age_beta + interaction_beta * entropy_c
            for age in age_values:
                rows.append(
                    {
                        "estimator_id": estimator,
                        "model": model_labels[estimator],
                        "age_months": age,
                        "response_entropy_level": float(level.response_entropy_level),
                        "response_entropy_bits_c": entropy_c,
                        "predicted_change": slope * (age - reference_age),
                        "age_slope_at_entropy": slope,
                        "reference_age": reference_age,
                    }
                )
    return pd.DataFrame(rows)


def word_model_implied_lines(
    effects: pd.DataFrame,
    *,
    reference_age: float = 36.0,
    age_min: float = 12.0,
    age_max: float = 62.0,
    points: int = 51,
) -> pd.DataFrame:
    """Turn registered same-word slopes into centered fitted age trajectories."""

    required = [
        "question_id",
        "scorer",
        "estimate",
        "ci_low",
        "ci_high",
        "bootstrap_ci_low",
        "bootstrap_ci_high",
    ]
    _required_columns(effects, required, label="word effects")
    requested = ["same_word_k0_age", "same_word_k3_age", "context_gain_age"]
    data = effects[effects["question_id"].isin(requested)].copy()
    expected = {(question, scorer) for question in requested for scorer in SCORER_ORDER}
    actual = set(zip(data["question_id"], data["scorer"]))
    if actual != expected:
        raise RuntimeError(f"word regression-line grid mismatch: missing={sorted(expected - actual)}")
    ages = np.linspace(age_min, age_max, points)
    rows = []
    for row in data.itertuples(index=False):
        low_beta = float(row.bootstrap_ci_low)
        high_beta = float(row.bootstrap_ci_high)
        if not np.isfinite(low_beta) or not np.isfinite(high_beta):
            low_beta = float(row.ci_low)
            high_beta = float(row.ci_high)
        for age in ages:
            delta = age - reference_age
            estimate = float(row.estimate) * delta
            endpoints = [low_beta * delta, high_beta * delta]
            rows.append(
                {
                    "question_id": row.question_id,
                    "scorer": row.scorer,
                    "age_months": age,
                    "predicted_change": estimate,
                    "ci_low": min(endpoints),
                    "ci_high": max(endpoints),
                    "reference_age": reference_age,
                }
            )
    return pd.DataFrame(rows)


def _format_number(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    if not math.isfinite(number):
        return "—"
    if number != 0 and abs(number) < 0.001:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def markdown_table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    display = frame.loc[:, [column for column in columns if column in frame.columns]].copy()
    if display.empty:
        return "_No rows._"
    for column in display.columns:
        if pd.api.types.is_numeric_dtype(display[column]):
            if column.endswith("_reps") or column in {
                "analysis_rows",
                "children",
                "corpora",
                "sessions",
                "source_rows",
            }:
                display[column] = display[column].map(
                    lambda value: "—" if pd.isna(value) else str(int(value))
                )
            else:
                display[column] = display[column].map(_format_number)
    display = display.fillna("—").astype(str)
    lines = [
        "| " + " | ".join(display.columns) + " |",
        "| " + " | ".join(["---"] * len(display.columns)) + " |",
    ]
    for row in display.itertuples(index=False, name=None):
        values = [value.replace("|", "\\|").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _relative(path: Path, report: Path) -> str:
    return os.path.relpath(path.resolve(), start=report.parent.resolve()).replace(os.sep, "/")


def plot_route1(route1: pd.DataFrame, path: Path) -> None:
    groups = list(dict.fromkeys(route1["display_group"]))
    colors = {
        "Mistral — PBM discovery": "#2166ac",
        "TinyDialogues — PBM robustness": "#4d9221",
        "Mistral — non-PBM confirmation": "#b2182b",
    }
    fig, axes = plt.subplots(1, len(groups), figsize=(15, 5.4), sharey=True)
    if len(groups) == 1:
        axes = [axes]
    model_order = [ROUTE1_MODEL_METADATA[item][0] for item in ROUTE1_MODEL_ORDER]
    y = np.arange(len(model_order))
    for ax, group in zip(axes, groups):
        data = route1[route1["display_group"].eq(group)].set_index("model").reindex(model_order)
        estimate = pd.to_numeric(data["estimate"], errors="coerce").to_numpy(float)
        low = pd.to_numeric(data["ci_low"], errors="coerce").to_numpy(float)
        high = pd.to_numeric(data["ci_high"], errors="coerce").to_numpy(float)
        valid = np.isfinite(estimate) & np.isfinite(low) & np.isfinite(high)
        ax.errorbar(
            estimate[valid],
            y[valid],
            xerr=np.vstack([estimate[valid] - low[valid], high[valid] - estimate[valid]]),
            fmt="o",
            color=colors.get(group, "#374151"),
            capsize=3,
        )
        missing = ~valid & np.isfinite(estimate)
        ax.scatter(estimate[missing], y[missing], marker="x", color=colors.get(group, "#374151"))
        ax.axvline(0, color="#111827", lw=1)
        ax.set_title(group)
        ax.set_xlabel("reported age coefficient (bits/month at fixed word effort)")
        ax.grid(axis="x", color="#e5e7eb")
        ax.set_yticks(y, model_order)
        ax.invert_yaxis()
    fig.suptitle("Route 1: linear and repeated-measures sensitivity models")
    fig.text(
        0.01,
        0.01,
        "Intervals are estimator-specific 95% intervals. An x marks a fitted estimate whose saved GEE interval is unavailable.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    atomic_figure(fig, path)


def plot_route2(age: pd.DataFrame, interaction: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    for ax, data, title, xlabel in [
        (axes[0], age, "Age and relative effort", "words/month relative to generated mean"),
        (
            axes[1],
            interaction,
            "Age × exact-string response entropy",
            "words/month per entropy bit",
        ),
    ]:
        y = np.arange(len(data))
        estimate = data["estimate"].to_numpy(float)
        low = data["ci_low"].to_numpy(float)
        high = data["ci_high"].to_numpy(float)
        ax.errorbar(
            estimate,
            y,
            xerr=np.vstack([estimate - low, high - estimate]),
            fmt="o",
            color="#7b3294",
            capsize=3,
        )
        ax.axvline(0, color="#111827", lw=1)
        ax.set_yticks(y, data["model"])
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", color="#e5e7eb")
    fig.suptitle("Route 2: estimator sensitivity for the fully adjusted model")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    atomic_figure(fig, path)


def plot_word(word: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.0))
    colors = {"Mistral": "#2166ac", "Qwen3-14B": "#b2182b", "TinyDialogues": "#4d9221"}
    for ax, question_id in zip(axes.flat, WORD_QUESTION_ORDER):
        data = word[word["question_id"].eq(question_id)].set_index("scorer").reindex(SCORER_ORDER)
        y = np.arange(len(data))
        estimate = data["estimate"].to_numpy(float)
        low = data["ci_low"].to_numpy(float)
        high = data["ci_high"].to_numpy(float)
        for index, scorer in enumerate(SCORER_ORDER):
            ax.errorbar(
                estimate[index],
                index,
                xerr=[[estimate[index] - low[index]], [high[index] - estimate[index]]],
                fmt="o",
                color=colors[scorer],
                capsize=3,
            )
        ax.axvline(0, color="#111827", lw=1)
        ax.set_yticks(y, SCORER_ORDER)
        ax.invert_yaxis()
        ax.set_title(WORD_QUESTION_LABELS[question_id])
        ax.set_xlabel("scorer-specific coefficient")
        ax.grid(axis="x", color="#e5e7eb")
    fig.suptitle("Word-level surprisal: separately fit scorer-specific models")
    fig.text(
        0.01,
        0.01,
        "Panels have independent scales. Compare directions and interval support, not raw magnitudes across tokenizers.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    atomic_figure(fig, path)


def write_report(
    report_path: Path,
    *,
    figures: Mapping[str, Path],
    route1_tables: Mapping[str, pd.DataFrame],
    route2_age: pd.DataFrame,
    route2_interaction: pd.DataFrame,
    word_table: pd.DataFrame,
) -> None:
    age_gee = route2_age[route2_age["model"].eq("Session GEE")]
    interaction_gee = route2_interaction[route2_interaction["model"].eq("Session GEE")]
    r2_age_gee = age_gee.iloc[0] if not age_gee.empty else route2_age.iloc[0]
    r2_interaction_gee = (
        interaction_gee.iloc[0] if not interaction_gee.empty else route2_interaction.iloc[0]
    )

    lines = [
        "# Communicative efficiency: three core analyses",
        "",
        "This is the short model-centered companion to the complete August package. It keeps only Route 1, Route 2, and word-level surprisal in the main reading path. The original audited August package is preserved unchanged and remains the evidence archive for Bayes, onset, Hall, trajectories, and all other analyses.",
        "",
        "## The result in one page",
        "",
        "1. **Route 1 — information given effort.** In PBM discovery, contextual utterance surprisal decreases with age at the same exact/top-coded word effort after child identity is controlled. TinyDialogues shows the same direction on the same children. For non-PBM confirmation, the separate Mistral estimate is negative, but its frozen primary child-clustered interval crosses zero, so confirmation is not met.",
        "2. **Route 2 — effort relative to contextual demand.** Child word effort relative to the generated reference rises with age. In the preferred child-session GEE, the age-by-response-entropy interaction is negative, not the predicted positive interaction. The entropy measure is exact-string and model-dependent.",
        "3. **Word-level surprisal.** For the same word, both unconditional and contextual surprisal decrease with age in all three separately fitted PBM scorers. Word-level context-gain development is scorer-dependent. These are scorer-robustness results on the same 21 children, not remaining-child confirmation.",
        "",
        "> Lower surprisal means greater model-based predictability. It does not, by itself, mean more information communicated, greater listener utility, or a demonstrated efficiency optimum.",
        "",
        "## Why the report does not rely on one OLS model",
        "",
        "The transparent linear model is always shown first, but the inferential reading uses repeated-measures and child-adjusted checks appropriate to longitudinal utterances.",
        "",
        "| model family | role here | child/repetition handling |",
        "| --- | --- | --- |",
        "| Exact-cell weighted linear model | interpretable fixed-effort baseline | child fixed effects and child-clustered uncertainty |",
        "| Nonlinear age model | checks whether one straight developmental slope is inadequate | child fixed effects and child-clustered uncertainty |",
        "| Mundlak within/between model | separates change within a child from differences between children | within-child age, child mean age, and child clustering |",
        "| GEE | population-average repeated-measures sensitivity | observations grouped by child with exchangeable correlation |",
        "| Mixed-effects model | partial pooling and heterogeneous developmental trajectories in Route 2 | random child intercept and random age slope |",
        "| Child bootstrap | distribution-free sensitivity to which children are sampled | resamples whole children, never individual utterances |",
        "| Absorbed child/word fixed effects | same-child and same-word word-level comparisons | controls stable child and lexical-type differences |",
        "",
        "## Route 1 — information given effort",
        "",
        "**Question.** At the same measured production effort, does contextual self-information of the child's utterance change with age?",
        "",
        "**Outcome.** Mistral or TinyDialogues contextual target surprisal, `-log2 p(u | c)`, in bits. Word count is controlled as exact categories through 11 words and a `12+` category rather than assumed to have one linear effect.",
        "",
        f"![Route 1 model ladder]({_relative(figures['route1'], report_path)})",
        "",
        "*How to read it.* Values left of zero mean that older children's utterances are more predictable at fixed word effort. The four rows compare the linear child-adjusted model, a quadratic-age check, a within/between-child decomposition, and GEE. In the quadratic row, the reported age coefficient is the local linear component at centered age, not one global slope. The non-PBM GEE point with unavailable saved covariance is marked separately and is not used to override the frozen primary interval.",
        "",
    ]
    for label, table in route1_tables.items():
        lines.extend(
            [
                f"### {label}",
                "",
                markdown_table(
                    table,
                    [
                        "model",
                        "estimate",
                        "ci_low",
                        "ci_high",
                        "p_value",
                        "bootstrap_reps",
                        "bootstrap_ci_low",
                        "bootstrap_ci_high",
                        "adjustment",
                    ],
                ),
                "",
            ]
        )
    lines.extend(
        [
            "**Route 1 conclusion.** The PBM age direction is not an artifact of one estimator: it remains negative under linear, nonlinear, Mundlak, GEE, and child-bootstrap checks for both scorers. The non-PBM primary estimate remains qualified because its registered clustered interval includes zero; a nonlinear sensitivity or child bootstrap cannot replace that decision rule.",
            "",
            "## Route 2 — effort relative to contextual demand",
            "",
            "**Question.** Relative to a generated response distribution for the same context, does child word effort change with age and exact-string response uncertainty?",
            "",
            "**Outcome.** Observed child word count minus the generated mean word count. This is relative effort, not raw effort. The generated expected effort may mediate contextual demand, so it is not automatically interpreted as an ordinary confound.",
            "",
            "**Adjustment ladder.** R2-M1 begins with age and child identity; R2-M2 adds response entropy; R2-M3 adds generated expected words, context length, and next-token context entropy; R2-M4 combines those controls; R2-M5 adds the age-by-response-entropy interaction. The table and figure below show R2-M5 across estimator families.",
            "",
            f"![Route 2 estimator ladder]({_relative(figures['route2'], report_path)})",
            "",
            "### Age association in the fully adjusted model",
            "",
            markdown_table(route2_age, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
            "",
            "### Age × response-entropy interaction",
            "",
            markdown_table(
                route2_interaction,
                ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"],
            ),
            "",
            f"**Route 2 conclusion.** The preferred session GEE estimates the age association at {_format_number(r2_age_gee['estimate'])} words/month (95% CI {_format_number(r2_age_gee['ci_low'])} to {_format_number(r2_age_gee['ci_high'])}) relative to the generated mean. Its age-by-entropy interaction is {_format_number(r2_interaction_gee['estimate'])} (95% CI {_format_number(r2_interaction_gee['ci_low'])} to {_format_number(r2_interaction_gee['ci_high'])}), opposite the simple positive-adaptation prediction. The GEE and mixed-effects estimates agree in direction; the utterance-level fixed-effect baseline does not show that interaction, which is why estimator and aggregation sensitivity stay visible.",
            "",
            "**Limit.** Exact-string entropy depends on the generator, prompt, temperature, seed, and surface forms. It is not semantic response uncertainty or a validated listener outcome.",
            "",
            "## Word-level surprisal",
            "",
            "**Question.** Does the information assigned to the same lexical item change with age, and does preceding context support different word types differently?",
            "",
            "**Primary adjustment.** Same-word models absorb both child and word identity and control within-utterance position, utterance length, and singleton utterances. Intervals are clustered by child and checked with 1,000 child-bootstrap replicates. Integrative word-type models separately control corpus, word length, and leave-corpus-out rarity. Raw coefficients are never pooled across tokenizers.",
            "",
            f"![Word-level effects]({_relative(figures['word'], report_path)})",
            "",
            markdown_table(
                word_table,
                [
                    "question",
                    "scorer",
                    "estimate",
                    "ci_low",
                    "ci_high",
                    "bootstrap_ci_low",
                    "bootstrap_ci_high",
                    "adjustment",
                ],
            ),
            "",
            "**Word-level conclusion.** The same-word contextual age slope is negative with interval support in Mistral, Qwen3-14B, and TinyDialogues. The unconditional same-word slope is also negative in all three. In contrast, the word-level context-gain age slope is negative for Mistral but includes zero for Qwen3-14B and TinyDialogues, so context-gain development is scorer-dependent.",
            "",
            "**Limit.** All three word analyses use the exact same PBM children and occurrence set. Agreement is scorer robustness, not an independent sample confirmation. The remaining-58 word production has not yet been completed and audited.",
            "",
            "## What to say in the meeting",
            "",
            "The safest single sentence is: **Within the PBM discovery sample, older children's forms are more predictable to the scorer at the same measured effort, and this direction survives child identity controls, repeated-measures estimators, nonlinear checks, whole-child resampling, and three separately fitted word-level scorers; the distinct non-PBM utterance-level confirmation criterion was not met under its frozen primary interval.**",
            "",
            "Route 2 is complementary: relative effort rises with age, but the interaction with current exact-string response entropy is negative in the preferred repeated-measures model. Neither route yet establishes listener utility or a normative efficiency optimum.",
            "",
            "## Full evidence preserved",
            "",
            "Nothing from the August synthesis was removed. Use these links when a question goes beyond the three core analyses:",
            "",
            "- [Original audited August package](august_supervisor_index.html)",
            "- [Complete August supervisor report](august_supervisor_report.html)",
            "- [Direct-surprisal results explorer](direct_surprisal_results_explorer.html)",
            "- [Route 2 technical model suite](route2_relative_effort_model_suite.html)",
            "- [Word cross-scorer comparison](word_cross_scorer_comparison.html)",
            "",
            "The complete package remains authoritative for corrected Bayes, sustained onset, Hall, child trajectories, and the full limitations inventory.",
            "",
        ]
    )
    atomic_text(report_path, "\n".join(lines))


# July-style visual report -------------------------------------------------
#
# The first compact version above is kept as a historical implementation
# reference inside this uncommitted companion builder.  The definition below
# intentionally replaces its table-led layout with the regression-line model
# sequence used in the July supervisor report.


def route1_model_implied_lines(
    summary: pd.DataFrame,
    coefficients: pd.DataFrame,
    *,
    scope: str,
    sample: str,
    age_center: float,
    age_min: float,
    age_max: float,
    points: int = 60,
) -> pd.DataFrame:
    """Create centered fixed-effort trajectories from saved fitted models."""

    model_labels = {
        "P1_k3_contextual": "Child-FE WLS (primary)",
        "P1_k3_contextual_quadratic": "Quadratic child-FE WLS",
        "P1_k3_contextual_mundlak": "Mundlak within-child",
        "P1_k3_contextual_gee": "GEE exchangeable",
        "P1_k3_contextual_mixed_random_age": "Mixed random age (unweighted)",
    }
    ages = np.linspace(age_min, age_max, points)
    rows = []
    for model_id, label in model_labels.items():
        match = summary[
            summary["scope"].eq(scope)
            & summary["model_id"].eq(model_id)
            & summary["outcome"].eq("real_k3_sum_bits")
        ]
        if "role" in match and not match.empty:
            match = match[match["role"].eq("child")]
        if len(match) != 1:
            raise RuntimeError(f"expected one Route 1 model row for {sample}/{model_id}, found {len(match)}")
        fitted = match.iloc[0]
        if fitted["fit_status"] != "PASS":
            continue
        linear = float(fitted["age_estimate"])
        ci_low = float(fitted["age_ci_low"]) if pd.notna(fitted["age_ci_low"]) else np.nan
        ci_high = float(fitted["age_ci_high"]) if pd.notna(fitted["age_ci_high"]) else np.nan
        quadratic = 0.0
        interval_available = np.isfinite(ci_low) and np.isfinite(ci_high)
        if model_id.endswith("_quadratic"):
            q = coefficients[
                coefficients["scope"].eq(scope)
                & coefficients["model_id"].eq(model_id)
                & coefficients["term"].eq("I(age_c ** 2)")
            ]
            if "role" in q and not q.empty:
                q = q[q["role"].eq("child")]
            if len(q) != 1:
                raise RuntimeError(f"quadratic coefficient missing for {sample}")
            quadratic = float(q.iloc[0]["estimate"])
            interval_available = False
        for age in ages:
            delta = age - age_center
            predicted = linear * delta + quadratic * delta**2
            if interval_available:
                endpoints = [ci_low * delta, ci_high * delta]
                low, high = min(endpoints), max(endpoints)
            else:
                low = high = np.nan
            rows.append(
                {
                    "sample": sample,
                    "scope": scope,
                    "model_id": model_id,
                    "model": label,
                    "age_months": age,
                    "predicted_change": predicted,
                    "ci_low": low,
                    "ci_high": high,
                    "reference_age": age_center,
                    "age_estimate": linear,
                    "quadratic_estimate": quadratic,
                    "weighting_note": fitted.get("weighting_note", ""),
                }
            )
    return pd.DataFrame(rows)


def primary_prediction_lines(
    predictions: pd.DataFrame,
    summary: pd.DataFrame,
    bootstrap: pd.DataFrame,
    *,
    scope: str,
    sample: str,
    age_center: float,
) -> pd.DataFrame:
    """Attach whole-child age-slope bands to saved Model 2 predictions."""

    data = predictions[
        predictions["scope"].eq(scope)
        & predictions["model_id"].eq("P1_k3_contextual")
        & predictions["outcome"].eq("real_k3_sum_bits")
        & predictions["word_count_exact_top12"].astype(str).isin(["1", "2", "4"])
    ].copy()
    model = summary[
        summary["scope"].eq(scope) & summary["model_id"].eq("P1_k3_contextual")
    ]
    boot = bootstrap[
        bootstrap["scope"].eq(scope) & bootstrap["model_id"].eq("P1_k3_contextual")
    ]
    if len(model) != 1 or len(boot) != 1:
        raise RuntimeError(f"primary prediction support missing for {sample}")
    beta = float(model.iloc[0]["age_estimate"])
    low_beta = float(boot.iloc[0]["bootstrap_ci_low"])
    high_beta = float(boot.iloc[0]["bootstrap_ci_high"])
    delta = data["age_months"].to_numpy(float) - age_center
    low_end = data["predicted_mean"].to_numpy(float) + (low_beta - beta) * delta
    high_end = data["predicted_mean"].to_numpy(float) + (high_beta - beta) * delta
    data["ci_low"] = np.minimum(low_end, high_end)
    data["ci_high"] = np.maximum(low_end, high_end)
    data["sample"] = sample
    data["reference_age"] = age_center
    return data


def _plot_finish(ax: plt.Axes) -> None:
    ax.grid(color="#d7dde5", alpha=0.65, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)


def plot_route1_raw_lines(summary: pd.DataFrame, path: Path) -> None:
    metrics = [
        ("lexical_words", "Mean utterance length", "words"),
        ("contextual_k3_bits", "Contextual utterance surprisal", "scorer bits"),
        ("unconditional_k0_bits", "Unconditional utterance surprisal", "scorer bits"),
        ("context_gain_k3", "Context support (k0 − k3)", "scorer bits"),
    ]
    scopes = {
        "pbm_discovery": ("PBM discovery", "#1769aa"),
        "non_pbm_confirmation": ("Non-PBM confirmation", "#c0444b"),
    }
    frame = summary[summary["role"].eq("child")].copy()
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    for ax, (metric, title, ylabel) in zip(axes.flat, metrics):
        for scope, (label, color) in scopes.items():
            view = frame[frame["scope"].eq(scope) & frame["outcome"].eq(metric)].sort_values("age_bin")
            ax.plot(view["age_bin"], view["mean"], marker="o", linewidth=2.4, label=label, color=color)
            if metric != "lexical_words":
                ax.fill_between(
                    np.arange(len(view)),
                    view["q10"].to_numpy(float),
                    view["q90"].to_numpy(float),
                    color=color,
                    alpha=0.08,
                )
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=38)
        _plot_finish(ax)
    axes[0, 0].legend(frameon=False)
    fig.suptitle("Model 0 — raw developmental trajectories (no adjustment)", fontsize=16)
    atomic_figure(fig, path)


def plot_effort_only_lines(grids: pd.DataFrame, path: Path) -> None:
    samples = list(dict.fromkeys(grids["sample"]))
    colors = {"1": "#1769aa", "2": "#e07a32", "4": "#3a9d5d", "6": "#8e62b5"}
    fig, axes = plt.subplots(1, len(samples), figsize=(15, 4.8), constrained_layout=True)
    if len(samples) == 1:
        axes = [axes]
    for ax, sample in zip(axes, samples):
        view = grids[grids["sample"].eq(sample)]
        for level, group in view.groupby("word_count_exact_top12", observed=True):
            group = group.sort_values("age_months")
            color = colors.get(str(level), "#444444")
            ax.plot(group["age_months"], group["predicted_mean"], color=color, lw=2.3, label=f"{level} words")
            ax.fill_between(group["age_months"], group["ci_low"], group["ci_high"], color=color, alpha=0.13)
        ax.set_title(sample)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("predicted contextual surprisal (bits)")
        _plot_finish(ax)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Model 1 — effort-only regression lines (child identity omitted)", fontsize=16)
    atomic_figure(fig, path)


def plot_primary_fixed_effort_lines(lines: pd.DataFrame, path: Path) -> None:
    samples = list(dict.fromkeys(lines["sample"]))
    colors = {"1": "#1769aa", "2": "#e07a32", "4": "#3a9d5d"}
    fig, axes = plt.subplots(1, len(samples), figsize=(15, 4.8), constrained_layout=True)
    if len(samples) == 1:
        axes = [axes]
    for ax, sample in zip(axes, samples):
        view = lines[lines["sample"].eq(sample)]
        for level, group in view.groupby("word_count_exact_top12", observed=True):
            group = group.sort_values("age_months")
            color = colors[str(level)]
            ax.plot(group["age_months"], group["predicted_mean"], color=color, lw=2.5, label=f"{level} words")
            ax.fill_between(group["age_months"], group["ci_low"], group["ci_high"], color=color, alpha=0.14)
        ax.set_title(sample)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("predicted contextual surprisal (bits)")
        _plot_finish(ax)
    axes[0].legend(frameon=False)
    fig.suptitle("Model 2 — child-adjusted fixed-effort regression lines", fontsize=16)
    fig.text(0.5, -0.015, "Bands show whole-child bootstrap uncertainty in the age slope; they are not individual prediction intervals.", ha="center", fontsize=9)
    atomic_figure(fig, path)


def plot_route1_complex_lines(lines: pd.DataFrame, path: Path) -> None:
    samples = list(dict.fromkeys(lines["sample"]))
    colors = {
        "Child-FE WLS (primary)": "#111827",
        "Quadratic child-FE WLS": "#d97706",
        "Mundlak within-child": "#1769aa",
        "GEE exchangeable": "#3a9d5d",
        "Mixed random age (unweighted)": "#9a4f96",
    }
    fig, axes = plt.subplots(1, len(samples), figsize=(16, 5.5), constrained_layout=False)
    if len(samples) == 1:
        axes = [axes]
    for ax, sample in zip(axes, samples):
        view = lines[lines["sample"].eq(sample)]
        for model, group in view.groupby("model", sort=False):
            group = group.sort_values("age_months")
            color = colors[model]
            style = "--" if model == "Mixed random age (unweighted)" else "-"
            ax.plot(group["age_months"], group["predicted_change"], color=color, linestyle=style, lw=2.2, label=model)
            if group["ci_low"].notna().all():
                ax.fill_between(group["age_months"], group["ci_low"], group["ci_high"], color=color, alpha=0.08)
        ax.axhline(0, color="#6b7280", lw=0.8)
        ax.set_title(sample)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("model-implied change from centered age (bits)")
        _plot_finish(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    fig.suptitle("Model 3 — nonlinear and repeated-measures regression lines", fontsize=16)
    fig.tight_layout(rect=(0.0, 0.17, 1.0, 0.93))
    atomic_figure(fig, path)


def plot_route2_raw_lines(summary: pd.DataFrame, path: Path) -> None:
    metrics = [
        ("nb_words", "Observed child effort", "words"),
        ("generated_expected_words", "Generated expected effort", "words"),
        ("child_words_minus_generated_mean", "Child minus generated mean", "words"),
        ("child_words_percentile_in_generated_distribution", "Child percentile in generated distribution", "percentile"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5), constrained_layout=True)
    for ax, (metric, title, ylabel) in zip(axes.flat, metrics):
        view = summary[summary["metric"].eq(metric)].sort_values("age_bin_mid")
        ax.plot(view["age_bin_mid"], view["mean"], marker="o", color="#7b3294", lw=2.5)
        ax.fill_between(view["age_bin_mid"], view["p10"], view["p90"], color="#7b3294", alpha=0.12)
        if metric == "child_words_minus_generated_mean":
            ax.axhline(0, color="#6b7280", lw=0.8)
        ax.set_title(title)
        ax.set_xlabel("age-bin midpoint (months)")
        ax.set_ylabel(ylabel)
        _plot_finish(ax)
    fig.suptitle("Route 2 Model 0 — raw relative-effort trajectories", fontsize=16)
    atomic_figure(fig, path)


def plot_route2_primary_lines(grids: Mapping[str, pd.DataFrame], path: Path) -> None:
    panels = [
        ("percentile", "Child percentile in generated distribution"),
        ("minus_mean", "Child words minus generated mean"),
    ]
    colors = ["#1769aa", "#e07a32", "#3a9d5d"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for ax, (key, title) in zip(axes, panels):
        frame = grids[key]
        predicted_col = [column for column in frame if column.startswith("predicted_")][0]
        for color, (level, group) in zip(colors, frame.groupby("response_entropy_level", observed=True)):
            group = group.sort_values("age_months")
            ax.plot(group["age_months"], group[predicted_col], color=color, lw=2.5, label=f"entropy {float(level):.2f}")
        if key == "minus_mean":
            ax.axhline(0, color="#6b7280", lw=0.8)
        ax.set_title(title)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("adjusted predicted outcome")
        _plot_finish(ax)
    axes[0].legend(frameon=False)
    fig.suptitle("Route 2 Model 2 — fully adjusted child-FE regression lines", fontsize=16)
    atomic_figure(fig, path)


def plot_route2_complex_lines(lines: pd.DataFrame, path: Path) -> None:
    estimators = list(dict.fromkeys(lines["model"]))
    colors = ["#1769aa", "#e07a32", "#3a9d5d"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    for ax, model in zip(axes.flat, estimators):
        view = lines[lines["model"].eq(model)]
        for color, (level, group) in zip(colors, view.groupby("response_entropy_level", observed=True)):
            group = group.sort_values("age_months")
            ax.plot(group["age_months"], group["predicted_change"], color=color, lw=2.4, label=f"entropy {float(level):.2f}")
        ax.axhline(0, color="#6b7280", lw=0.8)
        ax.set_title(model)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("change from centered age in percentile")
        _plot_finish(ax)
    axes[0, 0].legend(frameon=False)
    fig.suptitle("Route 2 Model 3 — OLS, GEE, Mundlak, and mixed-model regression lines", fontsize=16)
    atomic_figure(fig, path)


def plot_word_primary_lines(lines: pd.DataFrame, path: Path) -> None:
    labels = {
        "same_word_k0_age": "Unconditional word surprisal (k0)",
        "same_word_k3_age": "Contextual word surprisal (k3)",
        "context_gain_age": "Word context support (k0 − k3)",
    }
    colors = {
        "same_word_k0_age": "#1769aa",
        "same_word_k3_age": "#e07a32",
        "context_gain_age": "#3a9d5d",
    }
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    for ax, scorer in zip(axes, SCORER_ORDER):
        view = lines[lines["scorer"].eq(scorer)]
        for question, group in view.groupby("question_id", sort=False):
            group = group.sort_values("age_months")
            color = colors[question]
            ax.plot(group["age_months"], group["predicted_change"], color=color, lw=2.4, label=labels[question])
            ax.fill_between(group["age_months"], group["ci_low"], group["ci_high"], color=color, alpha=0.11)
        ax.axhline(0, color="#6b7280", lw=0.8)
        ax.set_title(scorer)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("same-word adjusted change from age 36 (bits)")
        _plot_finish(ax)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Word Model 1 — child- and word-adjusted regression lines", fontsize=16)
    atomic_figure(fig, path)


def plot_word_nonlinear_lines(coefficients: Mapping[str, pd.DataFrame], path: Path) -> None:
    ages = np.linspace(12, 62, 80)
    reference_age = 36.0
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    for ax, scorer in zip(axes, SCORER_ORDER):
        data = coefficients[scorer]
        primary = data[data["model_id"].eq("same_word_k3_primary") & data["term"].eq("age_c")]
        linear = data[data["model_id"].eq("same_word_k3_quadratic_age") & data["term"].eq("age_c")]
        square = data[data["model_id"].eq("same_word_k3_quadratic_age") & data["term"].eq("age_c_sq")]
        if len(primary) != 1 or len(linear) != 1 or len(square) != 1:
            raise RuntimeError(f"word nonlinear coefficients missing for {scorer}")
        delta = ages - reference_age
        primary_line = float(primary.iloc[0]["estimate"]) * delta
        quadratic_line = float(linear.iloc[0]["estimate"]) * delta + float(square.iloc[0]["estimate"]) * delta**2
        ax.plot(ages, primary_line, color="#111827", lw=2.5, label="linear primary")
        ax.plot(ages, quadratic_line, color="#d97706", lw=2.5, linestyle="--", label="quadratic sensitivity")
        ax.axhline(0, color="#6b7280", lw=0.8)
        ax.set_title(scorer)
        ax.set_xlabel("child age (months)")
        ax.set_ylabel("same-word k3 change from age 36 (bits)")
        _plot_finish(ax)
    axes[0].legend(frameon=False)
    fig.suptitle("Word Model 2 — linear and nonlinear regression lines", fontsize=16)
    atomic_figure(fig, path)


def plot_data_age_coverage(descriptive: pd.DataFrame, path: Path) -> None:
    """Plot current contextual-score coverage without merging sample roles."""

    data = descriptive[
        descriptive["role"].eq("child")
        & descriptive["outcome"].eq("contextual_k3_bits")
        & descriptive["scope"].isin(["pbm_discovery", "non_pbm_confirmation"])
    ].copy()
    if data.empty:
        raise RuntimeError("current PBM/non-PBM contextual coverage rows are missing")

    age_order = list(dict.fromkeys(data["age_bin"].astype(str)))
    scope_order = ["pbm_discovery", "non_pbm_confirmation"]
    labels = {
        "pbm_discovery": "PBM discovery (21 children)",
        "non_pbm_confirmation": "Non-PBM confirmation (58 children)",
    }
    colors = {"pbm_discovery": "#2f6f73", "non_pbm_confirmation": "#c76f2c"}
    x = np.arange(len(age_order), dtype=float)
    width = 0.38
    fig, ax = plt.subplots(figsize=(12.2, 5.8))
    for index, scope in enumerate(scope_order):
        subset = data[data["scope"].eq(scope)].set_index("age_bin").reindex(age_order)
        values = pd.to_numeric(subset["rows"], errors="coerce").fillna(0).to_numpy(float)
        offset = (index - 0.5) * width
        ax.bar(
            x + offset,
            values,
            width=width,
            label=labels[scope],
            color=colors[scope],
            alpha=0.9,
        )
    ax.set_xticks(x, age_order)
    ax.set_xlabel("developmental age bin (months)")
    ax.set_ylabel("Mistral child utterances with contextual k3 scores")
    ax.set_title("Developmental coverage is uneven and sample roles stay separate")
    ax.grid(axis="y", color="#d9e0df", linewidth=0.8)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    atomic_figure(fig, path)


def write_report(
    report_path: Path,
    *,
    figures: Mapping[str, Path],
    simple_models: pd.DataFrame,
    route1_tables: Mapping[str, pd.DataFrame],
    route2_age: pd.DataFrame,
    route2_interaction: pd.DataFrame,
    word_table: pd.DataFrame,
) -> None:
    """Write the July-style, regression-line-led supervisor report."""

    lines = [
        "# Predicting utterance and word surprisal — a July-style visual report",
        "",
        "This report deliberately returns to the structure of the first July report: start with raw trajectories, add one adjustment at a time, and show the fitted regression lines before the coefficient tables. It is a companion view over the current audited August products; it does not delete or replace the full evidence package.",
        "",
        "## How to read every regression line",
        "",
        "A downward line means the scorer assigns lower surprisal at older ages under the controls named for that model. Lower surprisal means greater model-based predictability, not more Shannon information, better communication, or a proven efficiency optimum. A shaded band is uncertainty for the fitted mean or age slope as identified in the caption; it is not the raw spread of utterances.",
        "",
        "PBM (Brown, Manchester, Providence; 21 children) remains the discovery sample. The other 58 children are the separate non-PBM confirmation sample. TinyDialogues and the three word scorers reuse PBM children and therefore provide scorer robustness, not independent-sample confirmation.",
        "",
        "## Route 1 — utterance surprisal at fixed word effort",
        "",
        "### Model 0 — no controls: what the raw data look like",
        "",
        "The raw lines mix development with increasing utterance length and changing sample composition. They are orientation, not the inferential answer.",
        "",
        f"![Route 1 raw regression line trajectories]({_relative(figures['route1_raw'], report_path)})",
        "",
        "### Model 1 — effort only",
        "",
        "```text\ncontextual utterance surprisal ~ age + exact/top-coded word count\n```",
        "",
        "These fitted regression lines compare utterances at the same word count but still treat the pooled sample as if child identity were irrelevant. This model is intentionally incomplete and is labeled diagnostic; its HC1 interval is not used for the frozen claim.",
        "",
        f"![Route 1 effort-only regression lines]({_relative(figures['route1_simple'], report_path)})",
        "",
        markdown_table(simple_models, ["sample", "age_estimate", "ci_low", "ci_high", "p_value", "children", "source_rows"]),
        "",
        "### Model 2 — control child identity",
        "",
        "```text\ncontextual utterance surprisal ~ age + exact/top-coded word count + child identity\n```",
        "",
        "This is the registered primary design: exact word-effort cells are weighted by their utterance counts, child fixed effects remove stable between-child differences, and uncertainty is clustered or bootstrapped by whole child. The regression lines are standardized across the children in each sample. The bands show whole-child uncertainty in the age slope.",
        "",
        f"![Route 1 child-adjusted fixed-effort regression lines]({_relative(figures['route1_primary'], report_path)})",
        "",
        "The PBM Mistral and TinyDialogues lines slope downward with intervals excluding zero. The non-PBM Mistral line is also downward, but its frozen primary clustered interval crosses zero, so the registered confirmation criterion is not met.",
        "",
        "### Model 3 — nonlinear and repeated-measures models",
        "",
        "The next figure puts the primary child-fixed WLS line beside a quadratic age curve, a Mundlak model separating within-child age from between-child mean age, population-average GEE, and a random-age mixed model. All lines show the model-implied change from the sample's centered age at a fixed effort level, so their slopes and curvature—not their intercepts—are the comparison.",
        "",
        f"![Route 1 complex-model regression lines]({_relative(figures['route1_complex'], report_path)})",
        "",
        "The mixed-model sensitivity is deliberately visible but not promoted: it uses unweighted design cells and answers a different weighted estimand. Singular fits are omitted. GEE, Mundlak, nonlinear, mixed-effects, and child-bootstrap results are sensitivities around the registered primary model, not opportunities to select whichever interval is most convenient.",
        "",
    ]
    for label, table in route1_tables.items():
        lines.extend([
            f"#### {label}",
            "",
            markdown_table(table, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
            "",
        ])
    lines.extend([
        "## Route 2 — child effort relative to a generated response space",
        "",
        "### Model 0 — raw relative-effort trajectories",
        "",
        "Observed child utterances lengthen with age. Generated expected length also changes, so raw child length and child length relative to the generated distribution are kept as different outcomes.",
        "",
        f"![Route 2 raw trajectory lines]({_relative(figures['route2_raw'], report_path)})",
        "",
        "### Model 1 — simple age association",
        "",
        "The simplest question is whether relative effort changes with age after child identity is included. The answer is positive for the principal percentile and residual outcomes, but it does not yet ask whether contextual uncertainty changes that age trajectory.",
        "",
        "### Model 2 — add response entropy and situation-specific controls",
        "",
        "```text\nrelative effort ~ age * response entropy\n                + generated expected words\n                + context word count + next-token context entropy\n                + child identity\n```",
        "",
        "The fitted regression lines below hold the other continuous controls at their saved reference values and show low, middle, and high exact-string response entropy. This entropy is surface-form and generator dependent; it is not semantic uncertainty.",
        "",
        f"![Route 2 adjusted regression lines]({_relative(figures['route2_primary'], report_path)})",
        "",
        "### Model 3 — GEE, Mundlak, and mixed-effects checks",
        "",
        "The row model, child-session GEE, within/between-child GEE, and random-intercept/random-age mixed model do not all estimate the interaction identically. In the session-based models, higher response entropy flattens the positive age trajectory—the opposite of the original simple positive-interaction prediction.",
        "",
        f"![Route 2 complex regression lines]({_relative(figures['route2_complex'], report_path)})",
        "",
        "#### Final-model age terms",
        "",
        markdown_table(route2_age, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
        "",
        "#### Final-model age × response-entropy terms",
        "",
        markdown_table(route2_interaction, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
        "",
        "## Word-level surprisal",
        "",
        "### Model 0 — descriptive trajectories for common words",
        "",
        "These are raw age-bin means for repeatedly observed words. Different words live at different surprisal levels, so this view motivates rather than replaces the same-word regression.",
        "",
        f"![Common-word descriptive lines]({_relative(figures['word_descriptive'], report_path)})",
        "",
        "### Model 1 — compare the same word within children",
        "",
        "```text\nword surprisal ~ age + position + utterance length + singleton\n                 + child identity + word identity\n```",
        "",
        "The regression lines are centered at age 36 because absorbed child and word fixed effects identify developmental change, not a universally meaningful absolute intercept. Each scorer is fit and plotted separately. Bands are 1,000-replicate whole-child bootstrap intervals transformed into the age trajectory.",
        "",
        f"![Word-level adjusted regression lines]({_relative(figures['word_primary'], report_path)})",
        "",
        "All three scorers show negative same-word contextual and unconditional age slopes. Word context-support development is scorer dependent: Mistral is negative, whereas the Qwen3-14B and TinyDialogues intervals include zero. Raw bit magnitudes must not be compared across tokenizers.",
        "",
        "### Model 2 — nonlinear age sensitivity",
        "",
        "The final word figure compares the registered linear same-word trajectory with the saved quadratic-age sensitivity. It shows whether a single straight line is masking curvature; the quadratic curve is a sensitivity, not a selected replacement for the registered linear model.",
        "",
        f"![Word-level nonlinear regression lines]({_relative(figures['word_nonlinear'], report_path)})",
        "",
        markdown_table(word_table, ["question", "scorer", "estimate", "ci_low", "ci_high", "bootstrap_ci_low", "bootstrap_ci_high"]),
        "",
        "## Bottom line",
        "",
        "The clearest result remains narrow: in PBM discovery, older children's utterances are more predictable to the scorer at the same exact word effort after child identity is controlled. That direction is visible in the fitted lines and survives several repeated-measures and nonlinear checks. The separate non-PBM primary interval crosses zero, so it does not pass the frozen confirmation rule. Route 2 shows increasing relative effort with age but a contrary-direction entropy interaction in the session models. Word-level same-word predictability decreases with age across three PBM scorers, while word context-support development is scorer dependent.",
        "",
        "None of these lines alone measures listener utility or proves that children optimize a normative efficiency objective.",
        "",
        "## Full evidence preserved",
        "",
        "- [Original audited August package](august_supervisor_index.html)",
        "- [Complete August supervisor report](august_supervisor_report.html)",
        "- [Direct-surprisal results explorer](direct_surprisal_results_explorer.html)",
        "- [Route 2 technical model suite](route2_relative_effort_model_suite.html)",
        "- [Word cross-scorer comparison](word_cross_scorer_comparison.html)",
        "",
        "The original audited August package remains authoritative for corrected Bayes, sustained onset, Hall, child trajectories, audit records, and the full limitations inventory.",
        "",
    ])
    atomic_text(report_path, "\n".join(lines))


SITE_CSS = """
.report-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: -1.1rem -0.4rem 2rem;
  padding: 0.65rem;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 7px 22px rgba(31, 45, 48, 0.08);
}
.report-nav a {
  flex: 1 1 130px;
  padding: 0.55rem 0.75rem;
  border-radius: 7px;
  color: var(--muted);
  font-weight: 650;
  text-align: center;
  text-decoration: none;
}
.report-nav a:hover {
  background: var(--soft);
  color: var(--accent);
}
.report-nav a.active {
  background: var(--accent);
  color: white;
}
.route-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 1.25rem 0 1.7rem;
}
.route-card {
  display: flex;
  min-height: 120px;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1.05rem;
  border: 1px solid var(--line);
  border-top: 5px solid var(--accent);
  border-radius: 9px;
  color: var(--ink);
  text-decoration: none;
  background: var(--paper);
}
.route-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(31, 45, 48, 0.10);
}
.route-card span {
  color: var(--muted);
  font-size: 0.84rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.route-card strong {
  color: var(--accent);
  font-size: 1.16rem;
}
.route-card em {
  color: var(--muted);
  font-style: normal;
  line-height: 1.35;
}
.next-page {
  margin-top: 2.2rem;
  padding: 1rem 1.2rem;
  border: 1px solid var(--line);
  border-radius: 8px;
  text-align: right;
  background: var(--soft);
  font-weight: 650;
}
@media screen and (max-width: 720px) {
  .route-grid { grid-template-columns: 1fr; }
  .report-nav { position: static; }
  main {
    margin: 0;
    padding: 28px 22px 42px;
    box-shadow: none;
  }
  table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
    font-size: 0.86em;
  }
}
"""


def site_page_paths(report_path: Path) -> dict[str, Path]:
    """Return stable four-page paths while keeping the historical entry URL."""

    stem = report_path.stem
    base = stem[: -len("_report")] if stem.endswith("_report") else stem
    suffix = report_path.suffix
    return {
        "data": report_path,
        "route1": report_path.with_name(f"{base}_route1{suffix}"),
        "route2": report_path.with_name(f"{base}_route2{suffix}"),
        "word_level": report_path.with_name(f"{base}_word_level{suffix}"),
    }


def _site_navigation(pages: Mapping[str, Path], active: str) -> str:
    labels = {
        "data": "Data overview",
        "route1": "Route 1",
        "route2": "Route 2",
        "word_level": "Word level",
    }
    links = []
    for key in ["data", "route1", "route2", "word_level"]:
        active_class = ' class="active"' if key == active else ""
        links.append(
            f'<a{active_class} href="{pages[key].with_suffix(".html").name}">{labels[key]}</a>'
        )
    return '<div class="report-nav" aria-label="Report pages">' + "".join(links) + "</div>"


def _next_page(pages: Mapping[str, Path], key: str, label: str) -> str:
    href = pages[key].with_suffix(".html").name
    return f'<div class="next-page">Next: <a href="{href}">{label} →</a></div>'


def _route_cards(pages: Mapping[str, Path]) -> str:
    return (
        '<div class="route-grid">'
        f'<a class="route-card" href="{pages["route1"].with_suffix(".html").name}"><span>Page 2</span><strong>Route 1</strong><em>Utterance surprisal at fixed word effort</em></a>'
        f'<a class="route-card" href="{pages["route2"].with_suffix(".html").name}"><span>Page 3</span><strong>Route 2</strong><em>Child effort relative to a generated response space</em></a>'
        f'<a class="route-card" href="{pages["word_level"].with_suffix(".html").name}"><span>Page 4</span><strong>Word level</strong><em>Same-word surprisal across three scorers</em></a>'
        "</div>"
    )


def write_report_site(
    report_path: Path,
    *,
    figures: Mapping[str, Path],
    sample_table: pd.DataFrame,
    simple_models: pd.DataFrame,
    route1_tables: Mapping[str, pd.DataFrame],
    route2_age: pd.DataFrame,
    route2_interaction: pd.DataFrame,
    word_table: pd.DataFrame,
) -> dict[str, Path]:
    """Write the four-page supervisor reading path requested by the user."""

    pages = site_page_paths(report_path)
    nav = {key: _site_navigation(pages, key) for key in pages}

    data_lines = [
        nav["data"],
        "",
        "# Data and analysis overview",
        "",
        "This is the entry page for the supervisor-facing report. It restores the July reading order: first understand the data and measurements, then open one analysis at a time. The longer audited August package remains unchanged as the evidence archive.",
        "",
        "## The three analysis pages",
        "",
        _route_cards(pages),
        "",
        "## Corpora, children, and inferential roles",
        "",
        "The longitudinal data come from 13 strict-naturalistic CHILDES corpora. Brown, Manchester, and Providence form the **21-child PBM discovery sample**. The other 58 children across 10 corpora are a separate **non-PBM confirmation sample**. These roles are fixed and the samples are not pooled for a stronger-looking result.",
        "",
        "TinyDialogues and the three word-level scorers reuse the PBM children. Agreement across them is scorer robustness, not independent-sample confirmation. Hall remains a separate historical cross-sectional/domain-sensitivity analysis and is not part of these four pages.",
        "",
        markdown_table(sample_table, ["analysis", "sample", "analysis_rows", "children", "role"]),
        "",
        "> Row counts are analysis-specific denominators. The same utterance or word occurrence can contribute to more than one separately fit scorer, so the rows in this table must not be added together.",
        "",
        "## Developmental coverage",
        "",
        "The age distribution is uneven, as expected in longitudinal CHILDES data. The plot shows Mistral contextual-score coverage for the two longitudinal samples; it does not combine discovery and confirmation.",
        "",
        f"![PBM and non-PBM contextual-score coverage by age]({_relative(figures['data_age_coverage'], pages['data'])})",
        "",
        "The first bin combines 6–23 months; subsequent bins are six-month intervals through 60–65 months. Later-age estimates depend on fewer utterances and a changing mix of children and corpora, which is why child identity, within-child change, clustering, and repeated-measures checks matter.",
        "",
        "## What is measured",
        "",
        "- **Unconditional utterance surprisal (k0):** `-log2 p(u)`, a scorer-indexed measure of form predictability without preceding conversational context.",
        "- **Contextual utterance surprisal (k3):** `-log2 p(u | c)`, using up to three preceding caregiver utterances.",
        "- **Context gain:** `k0 - k3`, kept separate from unconditional form frequency.",
        "- **Production effort:** lexical word count is the primary validated measure in these pages. Alternative morpheme, syllable, and phoneme measures remain sensitivities pending full validation.",
        "- **Response-space uncertainty:** exact-string entropy over sampled Mistral responses. It is generator- and setting-dependent and is not semantic entropy.",
        "- **Word-level surprisal:** scorer-specific information assigned to aligned word occurrences; Mistral, Qwen3-14B, and TinyDialogues are fit separately because their tokenizers and raw bit scales differ.",
        "",
        "## Why the models become more complex",
        "",
        "Many utterances come from the same child, and many word observations repeat the same lexical item. The report therefore starts with transparent descriptive lines, then adds effort controls, child identity, within-child decompositions, GEE or mixed effects, nonlinear age terms, and whole-child resampling. The more complex models are checks around a declared primary estimand; they are not used to select whichever result is most favorable.",
        "",
        "## How to read the plots",
        "",
        "A downward surprisal line means that the scorer finds the form more predictable at older ages under the controls named for that model. It does not by itself mean that more Shannon information was communicated, that a listener benefited, or that the child reached a normative efficiency optimum. Shaded ribbons are model-based uncertainty, not the raw spread of utterances.",
        "",
        "## Full evidence preserved",
        "",
        "- [Original audited August package](august_supervisor_index.html)",
        "- [Complete August supervisor report](august_supervisor_report.html)",
        "- [Combined self-contained archive of the three analysis pages](august_routes_report.embedded.html)",
        "",
        _next_page(pages, "route1", "Route 1 — utterance surprisal at fixed effort"),
        "",
    ]

    route1_lines = [
        nav["route1"],
        "",
        "# Route 1 — utterance surprisal at fixed effort",
        "",
        "**Question.** At the same measured word effort, does contextual self-information of the child's utterance change with age?",
        "",
        "> Main result: PBM Mistral and same-child TinyDialogues lines are negative after child adjustment. The separate non-PBM Mistral estimate is also negative, but its frozen primary clustered interval crosses zero, so the confirmation criterion is not met.",
        "",
        "## Route 1 results",
        "",
        "### Model 0 — raw developmental trajectories",
        "",
        "The raw lines show what changes with age before adjustment. They mix development with longer utterances, child composition, and corpus composition, so they orient the reader but do not answer the fixed-effort question.",
        "",
        f"![Route 1 raw regression lines]({_relative(figures['route1_raw'], pages['route1'])})",
        "",
        "### Model 1 — control measured effort",
        "",
        "```text\ncontextual utterance surprisal ~ age + exact/top-coded word count\n```",
        "",
        "These fitted lines compare utterances at the same word count but omit child identity. This effort-only HC1 model is a diagnostic bridge from the raw plot, not a registered primary claim.",
        "",
        f"![Route 1 effort-only regression lines]({_relative(figures['route1_simple'], pages['route1'])})",
        "",
        markdown_table(simple_models, ["sample", "age_estimate", "ci_low", "ci_high", "p_value", "children", "source_rows"]),
        "",
        "### Model 2 — control child identity",
        "",
        "```text\ncontextual utterance surprisal ~ age + exact/top-coded word count + child identity\n```",
        "",
        "This is the registered primary design. Exact word-effort cells are weighted by their utterance counts, stable between-child differences are absorbed, and uncertainty is clustered or bootstrapped by whole child.",
        "",
        f"![Route 1 child-adjusted regression lines]({_relative(figures['route1_primary'], pages['route1'])})",
        "",
        "### Model 3 — nonlinear and repeated-measures checks",
        "",
        "The final figure compares the child-fixed WLS primary line with a quadratic-age curve, a Mundlak within/between-child decomposition, population-average GEE, and an available random-age mixed-model sensitivity. Their slopes and curvature are the comparison; intercepts and weighting differ.",
        "",
        f"![Route 1 nonlinear, Mundlak, GEE, and mixed-model lines]({_relative(figures['route1_complex'], pages['route1'])})",
        "",
        "The mixed sensitivity uses unweighted design cells and is not a replacement for the weighted primary model. Singular fits are omitted. The frozen primary interval remains the decision rule for non-PBM confirmation.",
        "",
    ]
    for label, table in route1_tables.items():
        route1_lines.extend(
            [
                f"#### {label}",
                "",
                markdown_table(table, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
                "",
            ]
        )
    route1_lines.extend(
        [
            "## Route 1 conclusion",
            "",
            "The strongest supported claim is narrow: within PBM discovery, older children's utterances are more predictable to the scorer at the same exact/top-coded word effort after child identity is controlled. TinyDialogues repeats the direction on the same children. The non-PBM primary result remains qualified because its registered interval includes zero.",
            "",
            _next_page(pages, "route2", "Route 2 — effort relative to response space"),
            "",
        ]
    )

    route2_lines = [
        nav["route2"],
        "",
        "# Route 2 — effort relative to a generated response space",
        "",
        "**Question.** Relative to responses generated for the same context, does child word effort change with age and exact-string response uncertainty? This is a different estimand from Route 1.",
        "",
        "> Main result: relative effort increases with age, but the age-by-response-entropy interaction is negative in the principal session models—the opposite of the original simple positive-interaction prediction.",
        "",
        "## Route 2 results",
        "",
        "### Model 0 — raw relative-effort trajectories",
        "",
        "Observed child utterances lengthen with age, but generated expected length also changes. Raw child effort and effort relative to the generated distribution therefore stay separate.",
        "",
        f"![Route 2 raw trajectories]({_relative(figures['route2_raw'], pages['route2'])})",
        "",
        "### Model 1 — age and child identity",
        "",
        "The simplest adjusted model asks whether relative effort changes with age after stable child differences are controlled. It does not yet ask whether contextual uncertainty changes the developmental trajectory.",
        "",
        "### Model 2 — add response entropy and situation-specific controls",
        "",
        "```text\nrelative effort ~ age * response entropy\n                + generated expected words\n                + context word count + next-token context entropy\n                + child identity\n```",
        "",
        "The lines hold other continuous predictors at their saved reference values and show low, middle, and high exact-string response entropy.",
        "",
        f"![Route 2 fully adjusted regression lines]({_relative(figures['route2_primary'], pages['route2'])})",
        "",
        "### Model 3 — GEE, Mundlak, and mixed-effects checks",
        "",
        "The comparison includes an utterance-level child-fixed model, child-session GEE, within/between-child Mundlak GEE, and a random-intercept/random-age mixed model. These handle longitudinal repetition differently and keep estimator sensitivity visible.",
        "",
        f"![Route 2 GEE, Mundlak, and mixed-model regression lines]({_relative(figures['route2_complex'], pages['route2'])})",
        "",
        "#### Fully adjusted age terms",
        "",
        markdown_table(route2_age, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
        "",
        "#### Fully adjusted age × response-entropy terms",
        "",
        markdown_table(route2_interaction, ["model", "estimate", "ci_low", "ci_high", "p_value", "adjustment"]),
        "",
        "## Route 2 conclusion",
        "",
        "The session GEE and mixed model support a positive age association in relative effort and a negative age-by-entropy interaction. The utterance-level fixed-effect model does not show the same interaction, so aggregation and estimator sensitivity remain part of the result. Exact-string entropy is model-, prompt-, temperature-, seed-, and surface-form-dependent; it is not semantic uncertainty or listener utility.",
        "",
        _next_page(pages, "word_level", "Word-level surprisal"),
        "",
    ]

    word_lines = [
        nav["word_level"],
        "",
        "# Word-level surprisal",
        "",
        "**Question.** Does the information assigned to the same lexical item change with child age, and does preceding context support different word types differently?",
        "",
        "> Main result: unconditional and contextual same-word surprisal decline with age in all three separately fitted PBM scorers. Development of word-level context gain is scorer-dependent.",
        "",
        "## Word-level results",
        "",
        "### Model 0 — descriptive trajectories for common words",
        "",
        "These raw age-bin trajectories follow repeatedly observed words. Different lexical items occupy different surprisal levels, so the descriptive plot motivates—but cannot replace—the same-word model.",
        "",
        f"![Common-word descriptive trajectories]({_relative(figures['word_descriptive'], pages['word_level'])})",
        "",
        "### Model 1 — compare the same word within children",
        "",
        "```text\nword surprisal ~ age + position + utterance length + singleton\n                 + child identity + word identity\n```",
        "",
        "The primary model absorbs child and word identity and controls within-utterance position, utterance length, and singleton utterances. The plotted lines are centered at 36 months because the absorbed fixed effects identify developmental change rather than one universal intercept. Bands use 1,000 whole-child bootstrap replicates.",
        "",
        f"![Child- and word-adjusted regression lines]({_relative(figures['word_primary'], pages['word_level'])})",
        "",
        "Mistral, Qwen3-14B, and TinyDialogues are fit and displayed separately. Directions and interval support can be compared; raw bit magnitudes cannot be pooled across their tokenizers.",
        "",
        "### Model 2 — nonlinear age sensitivity",
        "",
        "The quadratic-age curve checks whether a single straight line hides curvature. It is a registered sensitivity, not a selected replacement for the linear primary model.",
        "",
        f"![Linear and nonlinear same-word regression lines]({_relative(figures['word_nonlinear'], pages['word_level'])})",
        "",
        markdown_table(word_table, ["question", "scorer", "estimate", "ci_low", "ci_high", "bootstrap_ci_low", "bootstrap_ci_high"]),
        "",
        "## Word-level conclusion",
        "",
        "All three scorer-specific fits support negative unconditional and contextual same-word age slopes. Mistral shows a negative word context-gain slope, while the Qwen3-14B and TinyDialogues intervals include zero. Longer word types receive more contextual support in all three fits. Because every scorer uses the same 21 PBM children and exact shared occurrence set, this is scorer robustness rather than confirmation in the remaining 58 children.",
        "",
        "## Return to the full evidence package",
        "",
        "- [Data overview](august_routes_report.html)",
        "- [Original audited August package](august_supervisor_index.html)",
        "- [Complete August supervisor report](august_supervisor_report.html)",
        "- [Word cross-scorer technical comparison](word_cross_scorer_comparison.html)",
        "",
    ]

    content = {
        "data": data_lines,
        "route1": route1_lines,
        "route2": route2_lines,
        "word_level": word_lines,
    }
    for key, path in pages.items():
        atomic_text(path, "\n".join(content[key]))
    return pages


def decorate_site_html(path: Path) -> None:
    """Add the report-site navigation styles without changing the global renderer."""

    html_text = path.read_text(encoding="utf-8")
    if SITE_CSS not in html_text:
        html_text = html_text.replace("</style>", SITE_CSS + "</style>", 1)
    atomic_text(path, html_text)


def _validate_inputs(root: Path) -> dict[str, object]:
    completion = require_status(
        root / "results/august_supervisor_report/AUGUST_REPORT_COMPLETE_AND_AUDITED",
        key="status",
        expected="AUGUST_REPORT_COMPLETE_AND_AUDITED",
    )
    if completion.get("audit", {}).get("verdict") != "AUDIT_PASS":
        raise RuntimeError("original August completion marker does not contain AUDIT_PASS")
    word_manifest = require_status(
        root / "results/word_cross_scorer_comparison/manifest.json",
        key="status",
        expected="PASS",
    )
    for relative in [
        "results/direct_surprisal_replication/tinydialogues_pbm/models/audit.json",
        "results/direct_surprisal_replication/mistral_full79/models/audit.json",
    ]:
        audit = json.loads((root / relative).read_text(encoding="utf-8"))
        if int(audit.get("model_failures", -1)) != 0:
            raise RuntimeError(f"{relative}: expected zero model failures")
    route2_audit = pd.read_csv(
        root / "results/route2_relative_effort_model_suite/route2_relative_effort_audit.csv"
    )
    values = dict(zip(route2_audit["metric"], route2_audit["value"]))
    if int(float(values.get("failed_or_no_fit_models", -1))) != 0:
        raise RuntimeError("Route 2 audit contains failed or missing fits")
    return {"completion": completion, "word_manifest": word_manifest}


def build(
    *,
    root: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
) -> dict[str, object]:
    root = root.resolve()
    output_dir = (root / output_dir).resolve() if not output_dir.is_absolute() else output_dir.resolve()
    fig_dir = (root / fig_dir).resolve() if not fig_dir.is_absolute() else fig_dir.resolve()
    report_md = (root / report_md).resolve() if not report_md.is_absolute() else report_md.resolve()
    report_html = (root / report_html).resolve() if not report_html.is_absolute() else report_html.resolve()
    embedded_html = report_html.with_suffix(".embedded.html")
    word_root = root.parent / "developmental_word_information" / "results/modular_analysis"

    protected_paths = [root / path for path in PROTECTED_RELATIVE_PATHS]
    before = protected_hashes(protected_paths)
    validated = _validate_inputs(root)

    paths = {
        "mistral_summary": root / "results/direct_surprisal_replication/mistral_full79/modular/models/model_summaries.csv",
        "mistral_coefficients": root / "results/direct_surprisal_replication/mistral_full79/modular/models/coefficients_long.csv",
        "mistral_bootstrap": root / "results/direct_surprisal_replication/mistral_full79/modular/models/child_bootstrap_summary.csv",
        "mistral_predictions": root / "results/direct_surprisal_replication/mistral_full79/modular/models/prediction_grid.csv",
        "mistral_descriptive": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/descriptive_age_bin_summary.csv",
        "mistral_pbm_cells": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/design_cells/child/pbm_discovery/p1_k3_contextual.csv.gz",
        "mistral_non_pbm_cells": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/design_cells/child/non_pbm_confirmation/p1_k3_contextual.csv.gz",
        "tiny_summary": root / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/model_summaries.csv",
        "tiny_coefficients": root / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/coefficients_long.csv",
        "tiny_bootstrap": root / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/child_bootstrap_summary.csv",
        "tiny_predictions": root / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/prediction_grid.csv",
        "tiny_pbm_cells": root / "results/direct_surprisal_replication/tinydialogues_pbm/modular/prepared/design_cells/child/pbm_discovery/p1_k3_contextual.csv.gz",
        "route2_coefficients": root / "results/route2_relative_effort_model_suite/route2_relative_effort_model_coefficients.csv",
        "route2_summary": root / "results/route2_relative_effort_model_suite/route2_relative_effort_model_summary.csv",
        "route2_audit": root / "results/route2_relative_effort_model_suite/route2_relative_effort_audit.csv",
        "route2_age_summary": root / "results/route2_relative_effort_model_suite/route2_relative_effort_summary_by_age_bin.csv",
        "route2_percentile_grid": root / "results/route2_relative_effort_model_suite/percentile_in_gen_distribution_r2m5_age_by_entropy_prediction_grid.csv",
        "route2_minus_grid": root / "results/route2_relative_effort_model_suite/minus_gen_mean_r2m5_age_by_entropy_prediction_grid.csv",
        "word_effects": root / "results/word_cross_scorer_comparison/scientific_question_effects_by_scorer.csv",
        "word_manifest": root / "results/word_cross_scorer_comparison/manifest.json",
        "sample_registry": root / "results/august_supervisor_report/sample_registry.csv",
        "word_mistral_coefficients": word_root / "mistral_pbm21/models/coefficients.csv",
        "word_qwen_coefficients": word_root / "qwen_pbm21/models/coefficients.csv",
        "word_tiny_coefficients": word_root / "tinydialogues_pbm21/models/coefficients.csv",
        "word_mistral_audit": word_root / "mistral_pbm21/audit_all.json",
        "word_qwen_audit": word_root / "qwen_pbm21/audit_all.json",
        "word_tiny_audit": word_root / "tinydialogues_pbm21/audit_all.json",
        "word_descriptive_source": word_root / "mistral_pbm21/plots/same_word_trajectories.png",
    }
    for label, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"required report input is missing ({label}): {path}")
    for key in ["word_mistral_audit", "word_qwen_audit", "word_tiny_audit"]:
        require_status(paths[key], key="status", expected="PASS")

    mistral = pd.read_csv(paths["mistral_summary"])
    mistral_coefficients = pd.read_csv(paths["mistral_coefficients"])
    mistral_bootstrap = pd.read_csv(paths["mistral_bootstrap"])
    mistral_predictions = pd.read_csv(paths["mistral_predictions"])
    tiny = pd.read_csv(paths["tiny_summary"])
    tiny_coefficients = pd.read_csv(paths["tiny_coefficients"])
    tiny_bootstrap = pd.read_csv(paths["tiny_bootstrap"])
    tiny_predictions = pd.read_csv(paths["tiny_predictions"])
    route2_coefficients = pd.read_csv(paths["route2_coefficients"])
    route2_summary = pd.read_csv(paths["route2_summary"])
    route2_audit = pd.read_csv(paths["route2_audit"])
    if not route2_summary["status"].eq("fit").all():
        raise RuntimeError("Route 2 summary contains non-fit rows")
    word_effects = pd.read_csv(paths["word_effects"])

    route1_tables = {
        "Mistral PBM discovery": attach_route1_bootstrap(
            route1_ladder(mistral, scorer="Mistral", scope="pbm_discovery"),
            mistral_bootstrap,
            scope="pbm_discovery",
        ),
        "TinyDialogues PBM scorer robustness": attach_route1_bootstrap(
            route1_ladder(tiny, scorer="TinyDialogues", scope="pbm_discovery"),
            tiny_bootstrap,
            scope="pbm_discovery",
        ),
        "Mistral non-PBM confirmation": attach_route1_bootstrap(
            route1_ladder(mistral, scorer="Mistral", scope="non_pbm_confirmation"),
            mistral_bootstrap,
            scope="non_pbm_confirmation",
        ),
    }
    display_groups = {
        "Mistral PBM discovery": "Mistral — PBM discovery",
        "TinyDialogues PBM scorer robustness": "TinyDialogues — PBM robustness",
        "Mistral non-PBM confirmation": "Mistral — non-PBM confirmation",
    }
    for label, table in route1_tables.items():
        table["display_group"] = display_groups[label]
    route1_all = pd.concat(route1_tables.values(), ignore_index=True)

    cell_specs = [
        ("Mistral — PBM discovery", pd.read_csv(paths["mistral_pbm_cells"]), mistral, mistral_coefficients, mistral_predictions, mistral_bootstrap, "pbm_discovery"),
        ("TinyDialogues — PBM robustness", pd.read_csv(paths["tiny_pbm_cells"]), tiny, tiny_coefficients, tiny_predictions, tiny_bootstrap, "pbm_discovery"),
        ("Mistral — non-PBM confirmation", pd.read_csv(paths["mistral_non_pbm_cells"]), mistral, mistral_coefficients, mistral_predictions, mistral_bootstrap, "non_pbm_confirmation"),
    ]
    simple_rows = []
    simple_grids = []
    primary_lines = []
    complex_lines = []
    for sample, cells, summary, coefficients, predictions, bootstrap, scope in cell_specs:
        center = float(np.median(cells["age_months"] - cells["age_c"]))
        simple_summary, simple_grid = fit_effort_only_diagnostic(cells)
        simple_summary["sample"] = sample
        simple_rows.append(simple_summary)
        simple_grids.append(simple_grid.assign(sample=sample))
        primary_lines.append(
            primary_prediction_lines(
                predictions,
                summary,
                bootstrap,
                scope=scope,
                sample=sample,
                age_center=center,
            )
        )
        complex_lines.append(
            route1_model_implied_lines(
                summary,
                coefficients,
                scope=scope,
                sample=sample,
                age_center=center,
                age_min=float(cells["age_months"].min()),
                age_max=float(cells["age_months"].max()),
            )
        )
    simple_models = pd.DataFrame(simple_rows)
    simple_grid_all = pd.concat(simple_grids, ignore_index=True)
    primary_line_all = pd.concat(primary_lines, ignore_index=True)
    complex_line_all = pd.concat(complex_lines, ignore_index=True)

    route2_age = route2_final_ladder(route2_coefficients, term_role="age")
    route2_interaction = route2_final_ladder(route2_coefficients, term_role="interaction")
    route2_percentile_grid = pd.read_csv(paths["route2_percentile_grid"])
    route2_minus_grid = pd.read_csv(paths["route2_minus_grid"])
    route2_complex = route2_model_implied_lines(route2_coefficients, route2_percentile_grid)
    word = word_effect_table(word_effects)
    word_lines = word_model_implied_lines(word)
    word_coefficients = {
        "Mistral": pd.read_csv(paths["word_mistral_coefficients"]),
        "Qwen3-14B": pd.read_csv(paths["word_qwen_coefficients"]),
        "TinyDialogues": pd.read_csv(paths["word_tiny_coefficients"]),
    }
    route2_audit_values = dict(zip(route2_audit["metric"], route2_audit["value"]))
    sample_registry = pd.read_csv(paths["sample_registry"])
    word_registry = sample_registry[
        sample_registry["sample_id"].eq("SAMPLE_WORD_CROSS_SCORER_PREDICTABILITY")
    ]
    route2_registry = sample_registry[
        sample_registry["sample_id"].eq("SAMPLE_ROUTE2_RELATIVE_EFFORT_AGE")
    ]
    if len(word_registry) != 1 or len(route2_registry) != 1:
        raise RuntimeError("August sample registry is missing Route 2 or word-level sample rows")
    sample_roles = {
        "Mistral — PBM discovery": "discovery",
        "TinyDialogues — PBM robustness": "same-child scorer robustness",
        "Mistral — non-PBM confirmation": "confirmation",
    }
    sample_table_rows = [
        {
            "analysis": "Route 1",
            "sample": row["sample"],
            "analysis_rows": row["source_rows"],
            "children": row["children"],
            "role": sample_roles[row["sample"]],
        }
        for row in simple_models.to_dict(orient="records")
    ]
    sample_table_rows.extend(
        [
            {
                "analysis": "Route 2",
                "sample": "PBM utterances; final models use 976 child-session aggregates",
                "analysis_rows": int(float(route2_audit_values["input_rows"])),
                "children": int(float(route2_audit_values["unique_children"])),
                "role": "response-space exploration",
            },
            {
                "analysis": "Word level",
                "sample": "exact shared PBM word-occurrence set",
                "analysis_rows": int(float(word_registry.iloc[0]["rows"])),
                "children": int(float(word_registry.iloc[0]["children"])),
                "role": "same-child scorer robustness",
            },
        ]
    )
    sample_table = pd.DataFrame(sample_table_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "route1": output_dir / "route1_model_ladder.csv",
        "route1_simple": output_dir / "route1_effort_only_diagnostic.csv",
        "route1_simple_grid": output_dir / "route1_effort_only_prediction_grid.csv",
        "route1_primary_lines": output_dir / "route1_primary_prediction_lines.csv",
        "route1_complex_lines": output_dir / "route1_complex_model_lines.csv",
        "route2_age": output_dir / "route2_age_model_ladder.csv",
        "route2_interaction": output_dir / "route2_interaction_model_ladder.csv",
        "route2_complex_lines": output_dir / "route2_complex_model_lines.csv",
        "word": output_dir / "word_level_effects.csv",
        "word_lines": output_dir / "word_level_model_lines.csv",
    }
    table_frames = {
        "route1": route1_all,
        "route1_simple": simple_models,
        "route1_simple_grid": simple_grid_all,
        "route1_primary_lines": primary_line_all,
        "route1_complex_lines": complex_line_all,
        "route2_age": route2_age,
        "route2_interaction": route2_interaction,
        "route2_complex_lines": route2_complex,
        "word": word,
        "word_lines": word_lines,
    }
    for key, path in tables.items():
        atomic_frame(table_frames[key], path)

    figures = {
        "data_age_coverage": fig_dir / "data_contextual_coverage_by_age.png",
        "route1_raw": fig_dir / "route1_model0_raw_lines.png",
        "route1_simple": fig_dir / "route1_model1_effort_only_lines.png",
        "route1_primary": fig_dir / "route1_model2_child_adjusted_lines.png",
        "route1_complex": fig_dir / "route1_model3_complex_lines.png",
        "route2_raw": fig_dir / "route2_model0_raw_lines.png",
        "route2_primary": fig_dir / "route2_model2_adjusted_lines.png",
        "route2_complex": fig_dir / "route2_model3_complex_lines.png",
        "word_descriptive": fig_dir / "word_model0_common_word_lines.png",
        "word_primary": fig_dir / "word_model1_adjusted_lines.png",
        "word_nonlinear": fig_dir / "word_model2_nonlinear_lines.png",
    }
    mistral_descriptive = pd.read_csv(paths["mistral_descriptive"])
    plot_data_age_coverage(mistral_descriptive, figures["data_age_coverage"])
    plot_route1_raw_lines(mistral_descriptive, figures["route1_raw"])
    plot_effort_only_lines(simple_grid_all, figures["route1_simple"])
    plot_primary_fixed_effort_lines(primary_line_all, figures["route1_primary"])
    plot_route1_complex_lines(complex_line_all, figures["route1_complex"])
    plot_route2_raw_lines(pd.read_csv(paths["route2_age_summary"]), figures["route2_raw"])
    plot_route2_primary_lines(
        {"percentile": route2_percentile_grid, "minus_mean": route2_minus_grid},
        figures["route2_primary"],
    )
    plot_route2_complex_lines(route2_complex, figures["route2_complex"])
    temporary_copy = figures["word_descriptive"].with_name(
        f".{figures['word_descriptive'].name}.tmp-{os.getpid()}"
    )
    shutil.copyfile(paths["word_descriptive_source"], temporary_copy)
    os.replace(temporary_copy, figures["word_descriptive"])
    plot_word_primary_lines(word_lines, figures["word_primary"])
    plot_word_nonlinear_lines(word_coefficients, figures["word_nonlinear"])

    combined_md = report_md.with_name(f".{report_md.stem}.combined-{os.getpid()}.md")
    try:
        write_report(
            combined_md,
            figures=figures,
            simple_models=simple_models,
            route1_tables=route1_tables,
            route2_age=route2_age,
            route2_interaction=route2_interaction,
            word_table=word,
        )
        render_markdown_file(
            combined_md,
            embedded_html,
            title="Combined Route 1, Route 2, and Word-Level Archive",
            embed_images=True,
        )
    finally:
        combined_md.unlink(missing_ok=True)

    markdown_pages = write_report_site(
        report_md,
        figures=figures,
        sample_table=sample_table,
        simple_models=simple_models,
        route1_tables=route1_tables,
        route2_age=route2_age,
        route2_interaction=route2_interaction,
        word_table=word,
    )
    html_pages = site_page_paths(report_html)
    titles = {
        "data": "Data Overview — Predicting Utterance and Word Surprisal",
        "route1": "Route 1 — Utterance Surprisal at Fixed Effort",
        "route2": "Route 2 — Effort Relative to a Response Space",
        "word_level": "Word-Level Surprisal",
    }
    for key in ["data", "route1", "route2", "word_level"]:
        render_markdown_file(markdown_pages[key], html_pages[key], title=titles[key])
        decorate_site_html(html_pages[key])
    assert_protected_unchanged(before)

    output_paths = [
        *tables.values(),
        *figures.values(),
        *markdown_pages.values(),
        *html_pages.values(),
        embedded_html,
    ]

    def input_name(path: Path) -> str:
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    manifest = {
        "status": "PASS",
        "purpose": "Four-page July-style supervisor report site; frozen claims preserved",
        "diagnostic_refit": {
            "model": "effort-only exact-cell WLS with HC1 uncertainty",
            "role": "descriptive bridge only; not a registered claim or primary replacement",
            "samples": simple_models.to_dict(orient="records"),
        },
        "original_august_commit": validated["completion"].get("commit"),
        "original_august_audit": validated["completion"].get("audit", {}).get("verdict"),
        "original_august_protected_hashes": before,
        "input_hashes": {input_name(path): sha256_file(path) for path in paths.values()},
        "output_hashes": {str(path.relative_to(root)): sha256_file(path) for path in output_paths},
        "report_pages": {
            key: {
                "markdown": str(markdown_pages[key].relative_to(root)),
                "html": str(html_pages[key].relative_to(root)),
            }
            for key in ["data", "route1", "route2", "word_level"]
        },
        "model_families": [
            "diagnostic effort-only weighted linear model",
            "registered weighted child fixed-effects model with child-clustered uncertainty",
            "quadratic age sensitivity",
            "Mundlak within/between-child model",
            "GEE repeated-measures sensitivity",
            "mixed-effects random child intercept and age slope sensitivity",
            "absorbed child and word fixed effects",
            "whole-child bootstrap",
        ],
        "figures": len(figures),
        "pages": len(markdown_pages),
        "route1_rows": int(len(route1_all)),
        "route2_age_rows": int(len(route2_age)),
        "route2_interaction_rows": int(len(route2_interaction)),
        "word_rows": int(len(word)),
    }
    manifest_path = output_dir / "manifest.json"
    atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build(
        root=args.root,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
