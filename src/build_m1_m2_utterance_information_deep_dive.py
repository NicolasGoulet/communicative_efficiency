#!/usr/bin/env python3
"""Build the first utterance-information model analyses.

The packet is deliberately narrow:

M1: ``sum_bits ~ age + utterance size``
M2: ``sum_bits ~ age + utterance size + child identity``
M3: ``sum_bits ~ age * utterance size``
M4: ``sum_bits ~ age + utterance size + context entropy + child identity``

Each effort/size measure is modeled separately to avoid putting highly
collinear effort measures in the same regression.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gamma, Gaussian, Poisson
from statsmodels.genmod.families.links import Log

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/m1_m2_utterance_information_deep_dive")
DEFAULT_FIG_DIR = Path("figs/m1_m2_utterance_information_deep_dive")
DEFAULT_DOC_MD = Path("docs/utterance_information_m1_m2_deep_dive.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_m1_m2_deep_dive.html")

SEED = 20260608
AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
EFFORT_MEASURES = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables: CMU/pkg"),
    ("nb_syllables_pkg", "Syllables: pkg"),
    ("nb_phonemes", "Phonemes"),
]
EFFORT_LABEL_TO_COL = {label: col for col, label in EFFORT_MEASURES}
USECOLS = [
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "session_id",
    "age_months",
    "age_bin",
    "role",
    "target_variant",
    "context_k",
    "sum_bits",
    "context_text",
    "context_entropy_join_status",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
]
NUMERIC_COLS = [
    "age_months",
    "sum_bits",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
]
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


@dataclass(frozen=True)
class FitBundle:
    """One fitted model plus its metadata."""

    model_id: str
    model_label: str
    effort_col: str
    effort_label: str
    formula: str
    result: object
    n_obs: int
    n_children: int


@dataclass(frozen=True)
class ExpandedFitBundle:
    """One expanded model-family fit."""

    approach_id: str
    model_family_id: str
    model_family_label: str
    effort_col: str
    effort_label: str
    formula: str
    readable_formula: str
    fit_type: str
    effect_scale: str
    result: object | None
    status: str
    error: str
    n_obs: int
    n_children: int


@dataclass(frozen=True)
class M4FitBundle:
    """One context-entropy information model used in the M4 section."""

    model_id: str
    model_label: str
    question: str
    formula: str
    fit_type: str
    effort_col: str
    effort_label: str
    outcome: str
    effect_scale: str
    result: object | None
    status: str
    error: str
    n_obs: int
    n_children: int


@dataclass(frozen=True)
class SaturatedFitBundle:
    """One M5/M6 effort-level exploratory model."""

    model_id: str
    model_label: str
    question: str
    formula: str
    fit_type: str
    effect_scale: str
    effort_col: str
    effort_label: str
    result: object | None
    status: str
    error: str
    n_obs: int
    n_children: int


EXPANDED_MODEL_SPECS = [
    {
        "approach_id": "M1",
        "model_family_id": "ols",
        "model_family_label": "OLS",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort",
        "fit_type": "ols",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M1",
        "model_family_id": "ols_cluster",
        "model_family_label": "OLS, child-clustered SE",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M1",
        "model_family_id": "glm_gaussian",
        "model_family_label": "Gaussian GLM",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort",
        "fit_type": "glm_gaussian",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M1",
        "model_family_id": "glm_gamma_log",
        "model_family_label": "Gamma GLM, log link",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort",
        "fit_type": "glm_gamma_log",
        "effect_scale": "log mean bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "ols_child_fe",
        "model_family_label": "OLS + child fixed intercepts",
        "formula": "sum_bits ~ age_c + effort_c + C(child_id)",
        "readable_formula": "sum_bits ~ age + effort + C(child_id)",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "ols_child_fe_age_slope",
        "model_family_label": "OLS + child fixed intercepts and age slopes",
        "formula": "sum_bits ~ age_c + effort_c + C(child_id) + age_c:C(child_id)",
        "readable_formula": "sum_bits ~ age + effort + C(child_id) + age:C(child_id)",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "glm_gamma_log_child_fe",
        "model_family_label": "Gamma GLM, log link + child fixed intercepts",
        "formula": "sum_bits ~ age_c + effort_c + C(child_id)",
        "readable_formula": "sum_bits ~ age + effort + C(child_id)",
        "fit_type": "glm_gamma_log",
        "effect_scale": "log mean bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "gee_gaussian",
        "model_family_label": "Gaussian GEE, clustered by child",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort, grouped by child",
        "fit_type": "gee_gaussian",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "gee_gamma_log",
        "model_family_label": "Gamma GEE, log link, clustered by child",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort, grouped by child",
        "fit_type": "gee_gamma_log",
        "effect_scale": "log mean bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "mixed_random_intercept",
        "model_family_label": "Linear mixed model, random child intercept",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort + (1 | child_id)",
        "fit_type": "mixedlm",
        "re_formula": "1",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M2",
        "model_family_id": "mixed_random_age_slope",
        "model_family_label": "Linear mixed model, random child age slope",
        "formula": "sum_bits ~ age_c + effort_c",
        "readable_formula": "sum_bits ~ age + effort + (age | child_id)",
        "fit_type": "mixedlm",
        "re_formula": "~age_c",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "ols_interaction",
        "model_family_label": "OLS + age by effort interaction",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort",
        "fit_type": "ols",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "ols_cluster_interaction",
        "model_family_label": "OLS + interaction, child-clustered SE",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "glm_gaussian_interaction",
        "model_family_label": "Gaussian GLM + interaction",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort",
        "fit_type": "glm_gaussian",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "glm_gamma_log_interaction",
        "model_family_label": "Gamma GLM, log link + interaction",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort",
        "fit_type": "glm_gamma_log",
        "effect_scale": "log mean bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "ols_child_fe_interaction",
        "model_family_label": "OLS + interaction + child fixed intercepts",
        "formula": "sum_bits ~ age_c * effort_c + C(child_id)",
        "readable_formula": "sum_bits ~ age * effort + C(child_id)",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "ols_child_fe_age_slope_interaction",
        "model_family_label": "OLS + interaction + child fixed intercepts and age slopes",
        "formula": "sum_bits ~ age_c * effort_c + C(child_id) + age_c:C(child_id)",
        "readable_formula": "sum_bits ~ age * effort + C(child_id) + age:C(child_id)",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "glm_gamma_log_child_fe_interaction",
        "model_family_label": "Gamma GLM, log link + interaction + child fixed intercepts",
        "formula": "sum_bits ~ age_c * effort_c + C(child_id)",
        "readable_formula": "sum_bits ~ age * effort + C(child_id)",
        "fit_type": "glm_gamma_log",
        "effect_scale": "log mean bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "gee_gaussian_interaction",
        "model_family_label": "Gaussian GEE + interaction, clustered by child",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort, grouped by child",
        "fit_type": "gee_gaussian",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "gee_gamma_log_interaction",
        "model_family_label": "Gamma GEE, log link + interaction, clustered by child",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort, grouped by child",
        "fit_type": "gee_gamma_log",
        "effect_scale": "log mean bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "mixed_random_intercept_interaction",
        "model_family_label": "Linear mixed model + interaction, random child intercept",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort + (1 | child_id)",
        "fit_type": "mixedlm",
        "re_formula": "1",
        "effect_scale": "additive bits",
    },
    {
        "approach_id": "M3",
        "model_family_id": "mixed_random_age_slope_interaction",
        "model_family_label": "Linear mixed model + interaction, random child age slope",
        "formula": "sum_bits ~ age_c * effort_c",
        "readable_formula": "sum_bits ~ age * effort + (age | child_id)",
        "fit_type": "mixedlm",
        "re_formula": "~age_c",
        "effect_scale": "additive bits",
    },
]


def read_modeling_rows(
    input_csv: Path,
    *,
    context_k: str,
    chunksize: int,
) -> pd.DataFrame:
    """Read the real child rows used by M1/M2."""

    parts: list[pd.DataFrame] = []
    usecols = set(USECOLS)
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        wanted = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].eq(context_k)
        ].copy()
        if not wanted.empty:
            parts.append(wanted)
    if not parts:
        raise ValueError(f"no real child rows found for context_k={context_k} in {input_csv}")
    out = pd.concat(parts, ignore_index=True)
    return clean_modeling_rows(out)


def clean_modeling_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns and keep complete, positive modeling rows."""

    out = frame.copy()
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    needed = ["sum_bits", "age_months", "child_id", *[col for col, _ in EFFORT_MEASURES]]
    out = out.dropna(subset=needed).copy()
    out = out[(out["sum_bits"] > 0) & (out["age_months"] > 0)].copy()
    for col, _ in EFFORT_MEASURES:
        out = out[out[col] > 0].copy()
    out["age_bin"] = pd.Categorical(out["age_bin"], AGE_BIN_ORDER, ordered=True)
    out["child_id"] = out["child_id"].astype(str)
    out["dataset"] = out["dataset"].astype(str)
    if "context_text" not in out.columns:
        out["context_text"] = ""
    if "context_entropy_join_status" not in out.columns:
        out["context_entropy_join_status"] = ""
    return out.reset_index(drop=True)


def word_count(text: object) -> int:
    """Count surface words in a context string."""

    return len(WORD_RE.findall("" if text is None else str(text).lower()))


def age_stage(age_months: object) -> str:
    """Return compact developmental stage labels for M4 plots."""

    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return "unknown"
    if age < 24:
        return "006-023"
    if age < 36:
        return "024-035"
    if age < 48:
        return "036-047"
    return "048-065"


def fit_ols_cluster(formula: str, frame: pd.DataFrame, *, groups: str):
    """Fit OLS and use child-cluster robust standard errors for inference."""

    return smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame[groups]})


def fit_all_models(frame: pd.DataFrame) -> list[FitBundle]:
    """Fit M1/M2 once for each effort measure."""

    bundles: list[FitBundle] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        model_frame = frame.rename(columns={effort_col: "effort_value"}).copy()
        model_frame["effort_value"] = pd.to_numeric(model_frame["effort_value"], errors="coerce")
        model_frame = model_frame.dropna(subset=["sum_bits", "age_months", "effort_value", "child_id"]).copy()
        specs = [
            ("M1", "M1: age + effort", "sum_bits ~ age_months + effort_value"),
            ("M2", "M2: age + effort + child identity", "sum_bits ~ age_months + effort_value + C(child_id)"),
        ]
        for model_id, model_label, formula in specs:
            result = fit_ols_cluster(formula, model_frame, groups="child_id")
            bundles.append(
                FitBundle(
                    model_id=model_id,
                    model_label=model_label,
                    effort_col=effort_col,
                    effort_label=effort_label,
                    formula=formula,
                    result=result,
                    n_obs=int(result.nobs),
                    n_children=int(model_frame["child_id"].nunique()),
                )
            )
    return bundles


def expanded_model_frame(frame: pd.DataFrame, effort_col: str) -> pd.DataFrame:
    """Return a numerically stable model frame for one effort measure."""

    out = frame.rename(columns={effort_col: "effort_value"}).copy()
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["effort_c"] = out["effort_value"] - out["effort_value"].mean()
    out = out.dropna(subset=["sum_bits", "age_c", "effort_c", "child_id"]).copy()
    return out


def fit_expanded_spec(spec: Mapping[str, object], model_frame: pd.DataFrame) -> object:
    """Fit one expanded model specification."""

    formula = str(spec["formula"])
    fit_type = str(spec["fit_type"])
    if fit_type == "ols":
        return smf.ols(formula, data=model_frame).fit()
    if fit_type == "ols_cluster":
        return smf.ols(formula, data=model_frame).fit(cov_type="cluster", cov_kwds={"groups": model_frame["child_id"]})
    if fit_type == "glm_gaussian":
        return smf.glm(formula, data=model_frame, family=Gaussian()).fit()
    if fit_type == "glm_gamma_log":
        return smf.glm(formula, data=model_frame, family=Gamma(link=Log())).fit()
    if fit_type == "gee_gaussian":
        return smf.gee(formula, groups="child_id", data=model_frame, cov_struct=Exchangeable(), family=Gaussian()).fit()
    if fit_type == "gee_gamma_log":
        return smf.gee(formula, groups="child_id", data=model_frame, cov_struct=Exchangeable(), family=Gamma(link=Log())).fit()
    if fit_type == "mixedlm":
        return smf.mixedlm(
            formula,
            data=model_frame,
            groups=model_frame["child_id"],
            re_formula=str(spec.get("re_formula", "1")),
        ).fit(method="lbfgs", reml=False, maxiter=200, disp=False)
    raise ValueError(f"unknown expanded fit_type: {fit_type}")


def fit_expanded_models(frame: pd.DataFrame, *, include_slow: bool = True) -> list[ExpandedFitBundle]:
    """Fit all expanded M1/M2 variants across effort measures."""

    bundles: list[ExpandedFitBundle] = []
    specs = EXPANDED_MODEL_SPECS if include_slow else [
        spec for spec in EXPANDED_MODEL_SPECS if str(spec["fit_type"]) not in {"mixedlm", "gee_gamma_log"}
    ]
    for effort_col, effort_label in EFFORT_MEASURES:
        model_frame = expanded_model_frame(frame, effort_col)
        for spec in specs:
            try:
                result = fit_expanded_spec(spec, model_frame)
                status = "fit"
                error = ""
            except Exception as exc:  # pragma: no cover - exercised only on pathological real fits
                result = None
                status = "failed"
                error = f"{type(exc).__name__}: {exc}"
            bundles.append(
                ExpandedFitBundle(
                    approach_id=str(spec["approach_id"]),
                    model_family_id=str(spec["model_family_id"]),
                    model_family_label=str(spec["model_family_label"]),
                    effort_col=effort_col,
                    effort_label=effort_label,
                    formula=str(spec["formula"]),
                    readable_formula=str(spec["readable_formula"]),
                    fit_type=str(spec["fit_type"]),
                    effect_scale=str(spec["effect_scale"]),
                    result=result,
                    status=status,
                    error=error,
                    n_obs=len(model_frame),
                    n_children=int(model_frame["child_id"].nunique()),
                )
            )
    return bundles


M4_MODEL_SPECS = [
    {
        "model_id": "M4a",
        "model_label": "M4a: child FE + context entropy",
        "question": "Does context entropy explain total child bits after age, effort, and child identity are controlled?",
        "formula": "sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)",
        "fit_type": "ols_cluster",
        "outcome": "sum_bits",
        "effect_scale": "additive bits",
    },
    {
        "model_id": "M4b",
        "model_label": "M4b: GEE + context entropy",
        "question": "Does the same context-entropy effect appear in a population-average model clustered by child?",
        "formula": "sum_bits ~ age_c + effort_c + context_entropy_c",
        "fit_type": "gee_gaussian",
        "outcome": "sum_bits",
        "effect_scale": "additive bits",
    },
    {
        "model_id": "M4c",
        "model_label": "M4c: Gamma/log GEE + context entropy",
        "question": "Does the context-entropy effect survive a positive-continuous log-link sensitivity model?",
        "formula": "sum_bits ~ age_c + effort_c + context_entropy_c",
        "fit_type": "gee_gamma_log",
        "outcome": "sum_bits",
        "effect_scale": "log mean bits",
    },
    {
        "model_id": "M4d",
        "model_label": "M4d: age by context entropy + child FE",
        "question": "Does the context-entropy effect on total bits change with age after effort and child identity are controlled?",
        "formula": "sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id)",
        "fit_type": "ols_cluster",
        "outcome": "sum_bits",
        "effect_scale": "additive bits",
    },
    {
        "model_id": "M4e",
        "model_label": "M4e: M3 plus context entropy + child FE",
        "question": "Does the age-by-effort interaction remain after adding context entropy and child identity?",
        "formula": "sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id)",
        "fit_type": "ols_cluster",
        "outcome": "sum_bits",
        "effect_scale": "additive bits",
    },
]

SATURATED_MODEL_SPECS = [
    {
        "model_id": "M5",
        "model_label": "M5: context entropy + effort level + child FE",
        "question": "Does context entropy predict total information after child identity and low/mid/high effort level are controlled?",
        "formula": "sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id)",
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
    {
        "model_id": "M6",
        "model_label": "M6: age/context interactions + effort level + child FE",
        "question": "Do age, context entropy, and effort level interact when predicting total information?",
        "formula": (
            "sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + "
            "context_entropy_c * C(effort_level) + C(child_id)"
        ),
        "fit_type": "ols_cluster",
        "effect_scale": "additive bits",
    },
]


def context_entropy_model_frame(frame: pd.DataFrame, effort_col: str) -> pd.DataFrame:
    """Return complete rows for one M4 context-entropy information model."""

    if "context_entropy_bits" not in frame.columns:
        return pd.DataFrame()
    out = frame.rename(columns={effort_col: "effort_value"}).copy()
    out["context_entropy_bits"] = pd.to_numeric(out["context_entropy_bits"], errors="coerce")
    out["context_word_count"] = out["context_text"].map(word_count)
    out = out.dropna(subset=["context_entropy_bits", "sum_bits", "effort_value", "age_months", "child_id"]).copy()
    out = out[out["context_entropy_bits"] > 0].copy()
    out = out[out["effort_value"] > 0].copy()
    if out.empty:
        return out
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["context_entropy_c"] = out["context_entropy_bits"] - out["context_entropy_bits"].mean()
    out["effort_c"] = out["effort_value"] - out["effort_value"].mean()
    out["log_context_words_plus1"] = np.log1p(out["context_word_count"])
    out["age_stage"] = out["age_months"].map(age_stage)
    return out.reset_index(drop=True)


def fit_m4_result(spec: Mapping[str, object], frame: pd.DataFrame) -> object:
    """Fit one M4 context-entropy model."""

    formula = str(spec["formula"])
    fit_type = str(spec["fit_type"])
    if fit_type == "ols_cluster":
        return smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame["child_id"]})
    if fit_type == "gee_gaussian":
        return smf.gee(formula, groups="child_id", data=frame, cov_struct=Exchangeable(), family=Gaussian()).fit()
    if fit_type == "gee_gamma_log":
        return smf.gee(formula, groups="child_id", data=frame, cov_struct=Exchangeable(), family=Gamma(link=Log())).fit()
    if fit_type == "glm_gamma_log":
        return smf.glm(formula, data=frame, family=Gamma(link=Log())).fit()
    if fit_type == "gee_poisson":
        return smf.gee(formula, groups="child_id", data=frame, cov_struct=Exchangeable(), family=Poisson()).fit()
    raise ValueError(f"unknown M4 fit_type: {fit_type}")


def fit_m4_models(frame: pd.DataFrame) -> tuple[list[M4FitBundle], pd.DataFrame]:
    """Fit the M4 context-entropy models."""

    bundles: list[M4FitBundle] = []
    frame_parts: list[pd.DataFrame] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        model_frame = context_entropy_model_frame(frame, effort_col)
        if not model_frame.empty:
            frame_parts.append(model_frame.assign(effort_col=effort_col, effort_label=effort_label))
        if model_frame.empty:
            for spec in M4_MODEL_SPECS:
                bundles.append(
                    M4FitBundle(
                        model_id=str(spec["model_id"]),
                        model_label=str(spec["model_label"]),
                        question=str(spec["question"]),
                        formula=str(spec["formula"]),
                        fit_type=str(spec["fit_type"]),
                        effort_col=effort_col,
                        effort_label=effort_label,
                        outcome=str(spec["outcome"]),
                        effect_scale=str(spec["effect_scale"]),
                        result=None,
                        status="empty",
                        error="no rows with context entropy",
                        n_obs=0,
                        n_children=0,
                    )
                )
            continue
        for spec in M4_MODEL_SPECS:
            try:
                result = fit_m4_result(spec, model_frame)
                status = "fit"
                error = ""
            except Exception as exc:  # pragma: no cover - real-data guard
                result = None
                status = "failed"
                error = f"{type(exc).__name__}: {exc}"
            bundles.append(
                M4FitBundle(
                    model_id=str(spec["model_id"]),
                    model_label=str(spec["model_label"]),
                    question=str(spec["question"]),
                    formula=str(spec["formula"]),
                    fit_type=str(spec["fit_type"]),
                    effort_col=effort_col,
                    effort_label=effort_label,
                    outcome=str(spec["outcome"]),
                    effect_scale=str(spec["effect_scale"]),
                    result=result,
                    status=status,
                    error=error,
                    n_obs=len(model_frame),
                    n_children=int(model_frame["child_id"].nunique()),
                )
            )
    combined_frame = pd.concat(frame_parts, ignore_index=True) if frame_parts else pd.DataFrame()
    return bundles, combined_frame


def m4_summary_rows(bundles: Sequence[M4FitBundle]) -> pd.DataFrame:
    """Summarize M4 model fits in one compact table."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = bundle.result
        if result is None:
            rows.append(
                {
                    "model_id": bundle.model_id,
                    "model_label": bundle.model_label,
                    "question": bundle.question,
                    "formula": bundle.formula,
                    "fit_type": bundle.fit_type,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "outcome": bundle.outcome,
                    "effect_scale": bundle.effect_scale,
                    "status": bundle.status,
                    "error": bundle.error,
                    "n_obs": bundle.n_obs,
                    "n_children": bundle.n_children,
                    "r2_observed_fitted": math.nan,
                    "age_coef": math.nan,
                    "age_p": math.nan,
                    "effort_coef": math.nan,
                    "effort_p": math.nan,
                    "entropy_coef": math.nan,
                    "entropy_p": math.nan,
                    "age_entropy_coef": math.nan,
                    "age_entropy_p": math.nan,
                    "age_effort_coef": math.nan,
                    "age_effort_p": math.nan,
                }
            )
            continue
        observed = np.asarray(result.model.endog, dtype=float)
        fitted = np.asarray(result.fittedvalues, dtype=float)
        params = result.params
        pvalues = result.pvalues
        rows.append(
            {
                "model_id": bundle.model_id,
                "model_label": bundle.model_label,
                "question": bundle.question,
                "formula": bundle.formula,
                "fit_type": bundle.fit_type,
                "effort_col": bundle.effort_col,
                "effort_label": bundle.effort_label,
                "outcome": bundle.outcome,
                "effect_scale": bundle.effect_scale,
                "status": bundle.status,
                "error": bundle.error,
                "n_obs": bundle.n_obs,
                "n_children": bundle.n_children,
                "r2_observed_fitted": fitted_r2(observed, fitted),
                "age_coef": float(params.get("age_c", math.nan)),
                "age_p": float(pvalues.get("age_c", math.nan)),
                "effort_coef": float(params.get("effort_c", math.nan)),
                "effort_p": float(pvalues.get("effort_c", math.nan)),
                "entropy_coef": float(params.get("context_entropy_c", math.nan)),
                "entropy_p": float(pvalues.get("context_entropy_c", math.nan)),
                "age_entropy_coef": float(params.get("age_c:context_entropy_c", math.nan)),
                "age_entropy_p": float(pvalues.get("age_c:context_entropy_c", math.nan)),
                "age_effort_coef": float(params.get("age_c:effort_c", math.nan)),
                "age_effort_p": float(pvalues.get("age_c:effort_c", math.nan)),
            }
        )
    return pd.DataFrame(rows)


def m4_coefficient_rows(bundles: Sequence[M4FitBundle]) -> pd.DataFrame:
    """Extract M4 coefficient rows."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        if bundle.result is None:
            continue
        for term, estimate in bundle.result.params.items():
            rows.append(
                {
                    "model_id": bundle.model_id,
                    "model_label": bundle.model_label,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "term": term,
                    "estimate": float(estimate),
                    "std_error": float(bundle.result.bse.get(term, math.nan)),
                    "p_value": float(bundle.result.pvalues.get(term, math.nan)),
                }
            )
    return pd.DataFrame(rows)


def assign_effort_level(values: pd.Series) -> pd.Series:
    """Assign low/mid/high effort labels using tertile cut points."""

    numeric = pd.to_numeric(values, errors="coerce")
    low_cut = float(numeric.quantile(1 / 3))
    high_cut = float(numeric.quantile(2 / 3))
    if not np.isfinite(low_cut) or not np.isfinite(high_cut) or low_cut >= high_cut:
        median = float(numeric.median())
        labels = np.where(numeric <= median, "low effort", "high effort")
    else:
        labels = np.select(
            [numeric <= low_cut, numeric >= high_cut],
            ["low effort", "high effort"],
            default="mid effort",
        )
    return pd.Series(
        pd.Categorical(labels, categories=["low effort", "mid effort", "high effort"], ordered=True),
        index=values.index,
    )


def saturated_model_frame(frame: pd.DataFrame, effort_col: str) -> pd.DataFrame:
    """Return complete rows for one M5/M6 effort-level information model."""

    out = frame.copy()
    if "context_entropy_bits" not in out.columns:
        return pd.DataFrame()
    out["effort_value"] = pd.to_numeric(out[effort_col], errors="coerce")
    out["context_entropy_bits"] = pd.to_numeric(out["context_entropy_bits"], errors="coerce")
    out["context_word_count"] = out["context_text"].map(word_count)
    required = [
        "sum_bits",
        "age_months",
        "child_id",
        "context_entropy_bits",
        "effort_value",
    ]
    out = out.dropna(subset=required).copy()
    out = out[(out["sum_bits"] > 0) & (out["context_entropy_bits"] > 0)].copy()
    out = out[out["effort_value"] > 0].copy()
    if out.empty:
        return out
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["context_entropy_c"] = out["context_entropy_bits"] - out["context_entropy_bits"].mean()
    out["log_context_words_plus1"] = np.log1p(out["context_word_count"])
    out["effort_level"] = assign_effort_level(out["effort_value"])
    return out.reset_index(drop=True)


def fit_saturated_result(spec: Mapping[str, object], frame: pd.DataFrame) -> object:
    """Fit one M5/M6 saturated model."""

    formula = str(spec["formula"])
    fit_type = str(spec["fit_type"])
    if fit_type == "ols_cluster":
        return smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame["child_id"]})
    if fit_type == "gee_gaussian":
        return smf.gee(formula, groups="child_id", data=frame, cov_struct=Exchangeable(), family=Gaussian()).fit()
    raise ValueError(f"unknown saturated fit_type: {fit_type}")


def fit_saturated_models(frame: pd.DataFrame) -> tuple[list[SaturatedFitBundle], pd.DataFrame]:
    """Fit M5 and M6 effort-level exploratory models."""

    bundles: list[SaturatedFitBundle] = []
    frame_parts: list[pd.DataFrame] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        model_frame = saturated_model_frame(frame, effort_col)
        if not model_frame.empty:
            frame_parts.append(model_frame.assign(effort_col=effort_col, effort_label=effort_label))
        for spec in SATURATED_MODEL_SPECS:
            if model_frame.empty:
                result = None
                status = "empty"
                error = "no rows with context entropy"
            else:
                try:
                    result = fit_saturated_result(spec, model_frame)
                    status = "fit"
                    error = ""
                except Exception as exc:  # pragma: no cover - real-data guard
                    result = None
                    status = "failed"
                    error = f"{type(exc).__name__}: {exc}"
            bundles.append(
                SaturatedFitBundle(
                    model_id=str(spec["model_id"]),
                    model_label=str(spec["model_label"]),
                    question=str(spec["question"]),
                    formula=str(spec["formula"]),
                    fit_type=str(spec["fit_type"]),
                    effect_scale=str(spec["effect_scale"]),
                    effort_col=effort_col,
                    effort_label=effort_label,
                    result=result,
                    status=status,
                    error=error,
                    n_obs=len(model_frame),
                    n_children=int(model_frame["child_id"].nunique()) if not model_frame.empty else 0,
                )
            )
    combined_frame = pd.concat(frame_parts, ignore_index=True) if frame_parts else pd.DataFrame()
    return bundles, combined_frame


def saturated_summary_rows(bundles: Sequence[SaturatedFitBundle]) -> pd.DataFrame:
    """Summarize M5/M6 saturated model fits."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = bundle.result
        if result is None:
            rows.append(
                {
                    "model_id": bundle.model_id,
                    "model_label": bundle.model_label,
                    "question": bundle.question,
                    "formula": bundle.formula,
                    "fit_type": bundle.fit_type,
                    "effect_scale": bundle.effect_scale,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "status": bundle.status,
                    "error": bundle.error,
                    "n_obs": bundle.n_obs,
                    "n_children": bundle.n_children,
                    "r2_observed_fitted": math.nan,
                    "age_coef": math.nan,
                    "age_p": math.nan,
                    "context_entropy_coef": math.nan,
                    "context_entropy_p": math.nan,
                }
            )
            continue
        observed, fitted, _note = safe_observed_and_fitted(result)
        rows.append(
            {
                "model_id": bundle.model_id,
                "model_label": bundle.model_label,
                "question": bundle.question,
                "formula": bundle.formula,
                "fit_type": bundle.fit_type,
                "effect_scale": bundle.effect_scale,
                "effort_col": bundle.effort_col,
                "effort_label": bundle.effort_label,
                "status": bundle.status,
                "error": bundle.error,
                "n_obs": bundle.n_obs,
                "n_children": bundle.n_children,
                "r2_observed_fitted": fitted_r2(observed, fitted),
                "age_coef": float(result.params.get("age_c", math.nan)),
                "age_p": float(result.pvalues.get("age_c", math.nan)),
                "context_entropy_coef": float(result.params.get("context_entropy_c", math.nan)),
                "context_entropy_p": float(result.pvalues.get("context_entropy_c", math.nan)),
            }
        )
    return pd.DataFrame(rows)


def saturated_coefficient_rows(bundles: Sequence[SaturatedFitBundle]) -> pd.DataFrame:
    """Extract M5/M6 coefficients."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        if bundle.result is None:
            continue
        for term, estimate in bundle.result.params.items():
            rows.append(
                {
                    "model_id": bundle.model_id,
                    "model_label": bundle.model_label,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "term": term,
                    "estimate": float(estimate),
                    "std_error": float(bundle.result.bse.get(term, math.nan)),
                    "p_value": float(bundle.result.pvalues.get(term, math.nan)),
                }
            )
    return pd.DataFrame(rows)


def rmse(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    """Root mean squared error."""

    return float(math.sqrt(mean_squared_error(y_true, y_pred)))


def fitted_r2(observed: np.ndarray, fitted: np.ndarray) -> float:
    """Observed-versus-fitted R2 that works across model families."""

    sst = float(np.sum((observed - np.mean(observed)) ** 2))
    if sst <= 0:
        return math.nan
    sse = float(np.sum((observed - fitted) ** 2))
    return 1.0 - sse / sst


def result_value(result: object | None, attr: str) -> float:
    """Read an optional numeric result attribute."""

    if result is None:
        return math.nan
    if attr == "bic" and hasattr(result, "bic_llf"):
        try:
            return float(getattr(result, "bic_llf"))
        except Exception:
            return math.nan
    if not hasattr(result, attr):
        return math.nan
    try:
        return float(getattr(result, attr))
    except Exception:
        return math.nan


def safe_observed_and_fitted(result: object) -> tuple[np.ndarray, np.ndarray, str]:
    """Return observed and fitted values, falling back for singular MixedLM fits."""

    observed = np.asarray(result.model.endog, dtype=float)
    try:
        fitted = np.asarray(result.fittedvalues, dtype=float)
        return observed, fitted, "full fitted values"
    except ValueError as exc:
        if "singular covariance" not in str(exc).lower() or not hasattr(result, "fe_params"):
            raise
        fixed_params = np.asarray(result.fe_params, dtype=float)
        fixed_exog = np.asarray(result.model.exog, dtype=float)
        fitted = fixed_exog @ fixed_params
        return observed, fitted, "fixed effects only; random effects singular"


def expanded_fit_summary_rows(bundles: Sequence[ExpandedFitBundle]) -> pd.DataFrame:
    """Return one row per expanded model-family fit."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = bundle.result
        if result is None:
            rows.append(
                {
                    "approach_id": bundle.approach_id,
                    "model_family_id": bundle.model_family_id,
                    "model_family_label": bundle.model_family_label,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "readable_formula": bundle.readable_formula,
                    "fit_type": bundle.fit_type,
                    "effect_scale": bundle.effect_scale,
                    "status": bundle.status,
                    "error": bundle.error,
                    "fitted_value_note": "",
                    "n_obs": bundle.n_obs,
                    "n_children": bundle.n_children,
                    "r2_observed_fitted": math.nan,
                    "rmse": math.nan,
                    "mae": math.nan,
                    "aic": math.nan,
                    "bic": math.nan,
                    "age_coef": math.nan,
                    "age_p": math.nan,
                    "effort_coef": math.nan,
                    "effort_p": math.nan,
                    "age_effort_coef": math.nan,
                    "age_effort_p": math.nan,
                }
            )
            continue
        observed, fitted, fitted_note = safe_observed_and_fitted(result)
        interaction_term = "age_c:effort_c"
        rows.append(
            {
                "approach_id": bundle.approach_id,
                "model_family_id": bundle.model_family_id,
                "model_family_label": bundle.model_family_label,
                "effort_col": bundle.effort_col,
                "effort_label": bundle.effort_label,
                "readable_formula": bundle.readable_formula,
                "fit_type": bundle.fit_type,
                "effect_scale": bundle.effect_scale,
                "status": bundle.status,
                "error": bundle.error,
                "fitted_value_note": fitted_note,
                "n_obs": bundle.n_obs,
                "n_children": bundle.n_children,
                "r2_observed_fitted": fitted_r2(observed, fitted),
                "rmse": rmse(observed, fitted),
                "mae": float(mean_absolute_error(observed, fitted)),
                "aic": result_value(result, "aic"),
                "bic": result_value(result, "bic"),
                "age_coef": float(result.params["age_c"]) if "age_c" in result.params.index else math.nan,
                "age_p": float(result.pvalues["age_c"]) if "age_c" in result.pvalues.index else math.nan,
                "effort_coef": float(result.params["effort_c"]) if "effort_c" in result.params.index else math.nan,
                "effort_p": float(result.pvalues["effort_c"]) if "effort_c" in result.pvalues.index else math.nan,
                "age_effort_coef": float(result.params[interaction_term])
                if interaction_term in result.params.index
                else math.nan,
                "age_effort_p": float(result.pvalues[interaction_term])
                if interaction_term in result.pvalues.index
                else math.nan,
            }
        )
    return pd.DataFrame(rows)


def model_fit_rows(bundles: Sequence[FitBundle]) -> pd.DataFrame:
    """Return one fit-summary row per model."""

    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = bundle.result
        fitted = result.fittedvalues
        observed = result.model.endog
        rows.append(
            {
                "model_id": bundle.model_id,
                "model_label": bundle.model_label,
                "effort_col": bundle.effort_col,
                "effort_label": bundle.effort_label,
                "formula": bundle.formula,
                "n_obs": bundle.n_obs,
                "n_children": bundle.n_children,
                "r2": float(result.rsquared),
                "adj_r2": float(result.rsquared_adj),
                "aic": float(result.aic),
                "bic": float(result.bic),
                "rmse": rmse(observed, fitted),
                "mae": float(mean_absolute_error(observed, fitted)),
                "covariance": "child-cluster robust",
            }
        )
    return pd.DataFrame(rows)


def coefficient_rows(bundles: Sequence[FitBundle], frame: pd.DataFrame) -> pd.DataFrame:
    """Return coefficient rows for age and effort."""

    y_sd = frame["sum_bits"].std(ddof=0)
    x_sds = {col: frame[col].std(ddof=0) for col, _ in EFFORT_MEASURES}
    age_sd = frame["age_months"].std(ddof=0)
    rows: list[dict[str, object]] = []
    for bundle in bundles:
        result = bundle.result
        ci = result.conf_int()
        term_map = {
            "age_months": ("age_months", "Age in months", age_sd),
            "effort_value": (bundle.effort_col, bundle.effort_label, x_sds[bundle.effort_col]),
        }
        for term, (original_col, term_label, x_sd) in term_map.items():
            if term not in result.params.index:
                continue
            coef = float(result.params[term])
            rows.append(
                {
                    "model_id": bundle.model_id,
                    "model_label": bundle.model_label,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "term": term,
                    "term_label": term_label,
                    "original_col": original_col,
                    "coef": coef,
                    "std_err": float(result.bse[term]),
                    "p_value": float(result.pvalues[term]),
                    "ci_low": float(ci.loc[term, 0]),
                    "ci_high": float(ci.loc[term, 1]),
                    "standardized_beta": coef * x_sd / y_sd if y_sd and np.isfinite(y_sd) else math.nan,
                }
            )
    return pd.DataFrame(rows)


def plain_r2(formula: str, frame: pd.DataFrame) -> float:
    """Fit ordinary OLS only to compute comparable R2 drops."""

    return float(smf.ols(formula, data=frame).fit().rsquared)


def variable_importance_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute simple drop-in-R2 importance for M1/M2 terms."""

    rows: list[dict[str, object]] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        model_frame = frame.rename(columns={effort_col: "effort_value"}).copy()
        full_specs = [
            ("M1", "M1: age + effort", "sum_bits ~ age_months + effort_value"),
            ("M2", "M2: age + effort + child identity", "sum_bits ~ age_months + effort_value + C(child_id)"),
        ]
        for model_id, model_label, full_formula in full_specs:
            full_r2 = plain_r2(full_formula, model_frame)
            term_formulas = {
                "Age in months": "sum_bits ~ effort_value" + (" + C(child_id)" if model_id == "M2" else ""),
                effort_label: "sum_bits ~ age_months" + (" + C(child_id)" if model_id == "M2" else ""),
            }
            if model_id == "M2":
                term_formulas["Child identity"] = "sum_bits ~ age_months + effort_value"
            for term_label, reduced_formula in term_formulas.items():
                reduced_r2 = plain_r2(reduced_formula, model_frame)
                rows.append(
                    {
                        "model_id": model_id,
                        "model_label": model_label,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "importance_term": term_label,
                        "full_r2": full_r2,
                        "reduced_r2": reduced_r2,
                        "delta_r2_when_dropped": full_r2 - reduced_r2,
                    }
                )
    return pd.DataFrame(rows)


def predictor_correlation(frame: pd.DataFrame) -> pd.DataFrame:
    """Return correlation matrix among age and effort measures."""

    cols = ["age_months", *[col for col, _ in EFFORT_MEASURES]]
    return frame[cols].corr(method="pearson")


def vif_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute VIF for age and all effort measures together as a diagnostic."""

    cols = ["age_months", *[col for col, _ in EFFORT_MEASURES]]
    rows: list[dict[str, object]] = []
    for target in cols:
        others = [col for col in cols if col != target]
        X = frame[others].to_numpy(dtype=float)
        y = frame[target].to_numpy(dtype=float)
        r2 = float(LinearRegression().fit(X, y).score(X, y))
        vif = math.inf if r2 >= 0.999999 else 1.0 / max(1e-12, 1.0 - r2)
        rows.append({"predictor": target, "r2_from_other_predictors": r2, "vif": vif})
    return pd.DataFrame(rows)


def audit_tables(frame: pd.DataFrame, output_dir: Path) -> Mapping[str, pd.DataFrame]:
    """Write basic data audit tables."""

    output_dir.mkdir(parents=True, exist_ok=True)
    overview = pd.DataFrame(
        [
            {
                "rows": len(frame),
                "children": frame["child_id"].nunique(),
                "datasets": frame["dataset"].nunique(),
                "age_min": frame["age_months"].min(),
                "age_max": frame["age_months"].max(),
                "mean_sum_bits": frame["sum_bits"].mean(),
                "median_sum_bits": frame["sum_bits"].median(),
            }
        ]
    )
    by_dataset = frame.groupby("dataset", dropna=False).agg(
        rows=("sum_bits", "size"),
        children=("child_id", "nunique"),
        age_min=("age_months", "min"),
        age_max=("age_months", "max"),
        mean_sum_bits=("sum_bits", "mean"),
        mean_words=("nb_words", "mean"),
    ).reset_index()
    by_age_bin = frame.groupby("age_bin", observed=True, dropna=False).agg(
        rows=("sum_bits", "size"),
        children=("child_id", "nunique"),
        mean_sum_bits=("sum_bits", "mean"),
        mean_words=("nb_words", "mean"),
        mean_morphemes=("nb_morphemes", "mean"),
        mean_syllables_cmu_or_pkg=("nb_syllables_cmu_or_pkg", "mean"),
        mean_phonemes=("nb_phonemes", "mean"),
    ).reset_index()
    corr = predictor_correlation(frame).reset_index().rename(columns={"index": "predictor"})
    vif = vif_table(frame)
    tables = {
        "overview": overview,
        "by_dataset": by_dataset,
        "by_age_bin": by_age_bin,
        "predictor_correlation": corr,
        "vif": vif,
    }
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
    return tables


def ci_bounds(coef_df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Return asymmetric error bars for matplotlib."""

    y = coef_df["coef"].astype(float)
    return y - coef_df["ci_low"].astype(float), coef_df["ci_high"].astype(float) - y


def plot_predictor_correlation(frame: pd.DataFrame, fig_dir: Path) -> None:
    """Plot the predictor-correlation heatmap."""

    labels = {
        "age_months": "Age",
        "nb_words": "Words",
        "nb_morphemes": "Morphemes",
        "nb_syllables_cmu_or_pkg": "Syllables CMU/pkg",
        "nb_syllables_pkg": "Syllables pkg",
        "nb_phonemes": "Phonemes",
    }
    corr = predictor_correlation(frame).rename(index=labels, columns=labels)
    fig, ax = plt.subplots(figsize=(8.2, 6.4))
    sns.heatmap(corr, ax=ax, cmap="vlag", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f", square=True, cbar_kws={"label": "Pearson r"})
    ax.set_title("Predictor Correlations")
    fig.tight_layout()
    fig.savefig(fig_dir / "predictor_correlation_heatmap.png", dpi=220)
    fig.savefig(fig_dir / "predictor_correlation_heatmap.pdf")
    plt.close(fig)


def plot_coefficients(coefs: pd.DataFrame, fig_dir: Path, *, term: str, filename: str, ylabel: str, title: str) -> None:
    """Plot coefficients by effort measure and model."""

    sub = coefs[coefs["term"].eq(term)].copy()
    sub["x_label"] = pd.Categorical(sub["effort_label"], [label for _, label in EFFORT_MEASURES], ordered=True)
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    palette = {"M1": "#4c78a8", "M2": "#f58518"}
    offsets = {"M1": -0.16, "M2": 0.16}
    x_positions = {label: idx for idx, label in enumerate([label for _, label in EFFORT_MEASURES])}
    for model_id, group in sub.groupby("model_id", sort=False):
        xs = np.array([x_positions[label] + offsets[model_id] for label in group["effort_label"]])
        yerr = ci_bounds(group)
        ax.errorbar(xs, group["coef"], yerr=yerr, fmt="o", capsize=4, linewidth=1.6, color=palette[model_id], label=model_id)
    ax.axhline(0, color="#303030", linewidth=1)
    ax.set_xticks(range(len(x_positions)))
    ax.set_xticklabels(list(x_positions), rotation=18, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(title="Model")
    ax.grid(axis="y", alpha=0.18)
    fig.tight_layout()
    fig.savefig(fig_dir / f"{filename}.png", dpi=220)
    fig.savefig(fig_dir / f"{filename}.pdf")
    plt.close(fig)


def prediction_grid_for_bundle(bundle: FitBundle, frame: pd.DataFrame, n_points: int = 80) -> pd.DataFrame:
    """Create adjusted age predictions with effort held at its median."""

    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    effort_median = float(frame[bundle.effort_col].median())
    if bundle.model_id == "M1":
        pred_frame = pd.DataFrame({"age_months": ages, "effort_value": effort_median})
        pred = bundle.result.predict(pred_frame)
        return pd.DataFrame(
            {
                "age_months": ages,
                "predicted_sum_bits": pred,
                "model_id": bundle.model_id,
                "model_label": bundle.model_label,
                "effort_col": bundle.effort_col,
                "effort_label": bundle.effort_label,
                "held_effort_value": effort_median,
            }
        )
    child_ids = sorted(frame["child_id"].astype(str).unique())
    rows: list[pd.DataFrame] = []
    for age in ages:
        pred_frame = pd.DataFrame(
            {
                "age_months": [age] * len(child_ids),
                "effort_value": [effort_median] * len(child_ids),
                "child_id": child_ids,
            }
        )
        rows.append(
            pd.DataFrame(
                {
                    "age_months": [age],
                    "predicted_sum_bits": [float(np.mean(bundle.result.predict(pred_frame)))],
                    "model_id": bundle.model_id,
                    "model_label": bundle.model_label,
                    "effort_col": bundle.effort_col,
                    "effort_label": bundle.effort_label,
                    "held_effort_value": effort_median,
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def plot_adjusted_age_predictions(predictions: pd.DataFrame, frame: pd.DataFrame, fig_dir: Path) -> None:
    """Plot adjusted age trajectories for M1/M2."""

    raw = frame.groupby("age_bin", observed=True).agg(
        age_months=("age_months", "mean"),
        mean_sum_bits=("sum_bits", "mean"),
    ).reset_index()
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6), sharey=True)
    axes = axes.flatten()
    palette = {"M1": "#4c78a8", "M2": "#f58518"}
    for ax, (_, effort_label) in zip(axes, EFFORT_MEASURES):
        sub = predictions[predictions["effort_label"].eq(effort_label)]
        add_overall_age_ribbon(ax, frame, alpha=0.10)
        for model_id, group in sub.groupby("model_id", sort=False):
            ax.plot(group["age_months"], group["predicted_sum_bits"], color=palette[model_id], linewidth=2.4, label=model_id)
        ax.scatter(raw["age_months"], raw["mean_sum_bits"], color="#555555", s=28, alpha=0.7, label="Raw age-bin mean")
        held = sub["held_effort_value"].dropna().iloc[0] if not sub.empty else math.nan
        ax.set_title(f"{effort_label}\neffort fixed at median={held:.1f}")
        ax.grid(alpha=0.17)
        ax.set_xlabel("Age in months")
    axes[-1].axis("off")
    axes[0].set_ylabel("Predicted total bits")
    axes[3].set_ylabel("Predicted total bits")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.95, 0.08), frameon=True)
    fig.suptitle("Adjusted Age Trajectories for M1 and M2", y=0.99)
    fig.tight_layout(rect=(0, 0, 0.94, 0.96))
    fig.savefig(fig_dir / "m1_m2_adjusted_age_predictions.png", dpi=220)
    fig.savefig(fig_dir / "m1_m2_adjusted_age_predictions.pdf")
    plt.close(fig)


def continuous_effort_quantile_prediction_grid(bundle: FitBundle, frame: pd.DataFrame, n_points: int = 80) -> pd.DataFrame:
    """Create M1/M2 predictions at low/median/high continuous effort values."""

    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    quantiles = frame[bundle.effort_col].quantile([0.25, 0.50, 0.75]).to_dict()
    effort_levels = [
        ("low effort (25th pct.)", float(quantiles[0.25])),
        ("median effort (50th pct.)", float(quantiles[0.50])),
        ("high effort (75th pct.)", float(quantiles[0.75])),
    ]
    parts: list[pd.DataFrame] = []
    for effort_level, effort_value in effort_levels:
        if bundle.model_id == "M1":
            pred_frame = pd.DataFrame({"age_months": ages, "effort_value": effort_value})
            pred = pd.DataFrame(
                {
                    "age_months": ages,
                    "predicted_sum_bits": np.asarray(bundle.result.predict(pred_frame), dtype=float),
                }
            )
        else:
            child_parts: list[pd.DataFrame] = []
            child_ids = sorted(frame["child_id"].astype(str).unique())
            for child_id in child_ids:
                child_frame = pd.DataFrame(
                    {
                        "age_months": ages,
                        "effort_value": effort_value,
                        "child_id": child_id,
                    }
                )
                child_frame["predicted_sum_bits"] = np.asarray(bundle.result.predict(child_frame), dtype=float)
                child_parts.append(child_frame)
            pred = (
                pd.concat(child_parts, ignore_index=True)
                .groupby("age_months", as_index=False)["predicted_sum_bits"]
                .mean()
            )
        pred["model_id"] = bundle.model_id
        pred["model_label"] = bundle.model_label
        pred["effort_col"] = bundle.effort_col
        pred["effort_label"] = bundle.effort_label
        pred["effort_level"] = effort_level
        pred["fixed_effort_value"] = effort_value
        parts.append(pred)
    return pd.concat(parts, ignore_index=True)


def plot_m1_m2_low_mid_high_effort_lines(
    bundles: Sequence[FitBundle],
    frame: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Plot M1/M2 age lines at low/median/high continuous effort values."""

    prediction_parts = [continuous_effort_quantile_prediction_grid(bundle, frame) for bundle in bundles]
    predictions = pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    if predictions.empty:
        return predictions
    palette = {
        "low effort (25th pct.)": "#4c78a8",
        "median effort (50th pct.)": "#f58518",
        "high effort (75th pct.)": "#54a24b",
    }
    effort_order = [label for _, label in EFFORT_MEASURES]
    for model_id in ["M1", "M2"]:
        model_pred = predictions[predictions["model_id"].eq(model_id)]
        if model_pred.empty:
            continue
        fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6), sharey=True)
        axes = axes.flatten()
        for ax, effort_label in zip(axes, effort_order):
            sub = model_pred[model_pred["effort_label"].eq(effort_label)]
            if sub.empty:
                ax.axis("off")
                continue
            effort_col = EFFORT_LABEL_TO_COL[effort_label]
            ribbon_palette = {
                "low effort": "#4c78a8",
                "mid effort": "#f58518",
                "high effort": "#54a24b",
            }
            add_effort_level_age_ribbons(ax, frame, effort_value_col=effort_col, palette=ribbon_palette)
            for effort_level, group in sub.groupby("effort_level", sort=False):
                ax.plot(
                    group["age_months"],
                    group["predicted_sum_bits"],
                    linewidth=2.1,
                    color=palette.get(str(effort_level)),
                    label=f"{effort_level}: {group['fixed_effort_value'].iloc[0]:.1f}",
                )
            ax.set_title(effort_label)
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
        axes[-1].axis("off")
        axes[0].set_ylabel("Predicted total bits")
        axes[3].set_ylabel("Predicted total bits")
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, title="Continuous effort reference", loc="lower center", ncol=3)
        title = "M1: Low, Median, and High Continuous Effort" if model_id == "M1" else "M2: Low, Median, and High Continuous Effort"
        fig.suptitle(title, y=0.99)
        fig.tight_layout(rect=(0, 0.11, 1, 0.94))
        stem = "m1_low_mid_high_effort_adjusted_age_predictions" if model_id == "M1" else "m2_low_mid_high_effort_adjusted_age_predictions"
        fig.savefig(fig_dir / f"{stem}.png", dpi=240)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)
    return predictions


def plot_variable_importance(importance: pd.DataFrame, fig_dir: Path) -> None:
    """Plot drop-in-R2 variable importance."""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), sharey=True)
    for ax, model_id in zip(axes, ["M1", "M2"]):
        sub = importance[importance["model_id"].eq(model_id)].copy()
        sns.barplot(
            data=sub,
            x="effort_label",
            y="delta_r2_when_dropped",
            hue="importance_term",
            ax=ax,
            palette="Set2",
        )
        ax.set_title(model_id)
        ax.set_xlabel("")
        ax.set_ylabel("Drop in R2 when term is removed")
        ax.tick_params(axis="x", rotation=18)
        ax.grid(axis="y", alpha=0.18)
    axes[0].legend_.remove()
    axes[1].legend(title="Term", loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.suptitle("Variable Importance for the Two Starter Models")
    fig.tight_layout(rect=(0, 0, 0.9, 0.93))
    fig.savefig(fig_dir / "m1_m2_delta_r2_variable_importance.png", dpi=220)
    fig.savefig(fig_dir / "m1_m2_delta_r2_variable_importance.pdf")
    plt.close(fig)


def plot_residual_diagnostics(bundles: Sequence[FitBundle], frame: pd.DataFrame, fig_dir: Path) -> None:
    """Plot residual diagnostics for the word-count version of M1/M2."""

    rng = np.random.default_rng(SEED)
    word_bundles = [bundle for bundle in bundles if bundle.effort_col == "nb_words"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    for row_idx, bundle in enumerate(word_bundles):
        result = bundle.result
        resid = np.asarray(result.resid)
        fitted = np.asarray(result.fittedvalues)
        if len(resid) > 8000:
            idx = rng.choice(len(resid), 8000, replace=False)
            resid_plot = resid[idx]
            fitted_plot = fitted[idx]
        else:
            resid_plot = resid
            fitted_plot = fitted
        axes[row_idx, 0].scatter(fitted_plot, resid_plot, s=8, alpha=0.18, color="#4c78a8")
        axes[row_idx, 0].axhline(0, color="#202020", linewidth=1)
        axes[row_idx, 0].set_title(f"{bundle.model_id} residuals vs fitted")
        axes[row_idx, 0].set_xlabel("Fitted total bits")
        axes[row_idx, 0].set_ylabel("Residual")
        qs = np.linspace(0.01, 0.99, 99)
        observed_q = np.quantile(resid, qs)
        normal_q = np.quantile(np.random.default_rng(SEED).normal(size=200000), qs) * np.std(resid)
        axes[row_idx, 1].scatter(normal_q, observed_q, s=14, alpha=0.75, color="#f58518")
        lo = min(normal_q.min(), observed_q.min())
        hi = max(normal_q.max(), observed_q.max())
        axes[row_idx, 1].plot([lo, hi], [lo, hi], color="#202020", linewidth=1)
        axes[row_idx, 1].set_title(f"{bundle.model_id} residual quantiles")
        axes[row_idx, 1].set_xlabel("Normal-theory quantile")
        axes[row_idx, 1].set_ylabel("Observed residual quantile")
    fig.suptitle("Residual Diagnostics for Word-Count Models")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(fig_dir / "m1_m2_residual_diagnostics_words.png", dpi=220)
    fig.savefig(fig_dir / "m1_m2_residual_diagnostics_words.pdf")
    plt.close(fig)


def plot_model_specific_coefficients(coefs: pd.DataFrame, fig_dir: Path, *, model_id: str) -> None:
    """Plot age and effort coefficients for one model family."""

    sub = coefs[coefs["model_id"].eq(model_id)].copy()
    effort_order = [label for _, label in EFFORT_MEASURES]
    x_positions = {label: idx for idx, label in enumerate(effort_order)}
    colors = {"age_months": "#4c78a8", "effort_value": "#f58518"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    for ax, term, title, ylabel in [
        (axes[0], "age_months", "Age coefficient", "Bits per additional month"),
        (axes[1], "effort_value", "Effort coefficient", "Bits per effort unit"),
    ]:
        group = sub[sub["term"].eq(term)].copy()
        xs = np.array([x_positions[label] for label in group["effort_label"]])
        yerr = ci_bounds(group)
        ax.errorbar(xs, group["coef"], yerr=yerr, fmt="o", capsize=4, linewidth=1.8, color=colors[term])
        ax.axhline(0, color="#303030", linewidth=1)
        ax.set_xticks(range(len(effort_order)))
        ax.set_xticklabels(effort_order, rotation=18, ha="right")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.18)
    fig.suptitle(f"{model_id} Coefficients Across Effort Versions")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    stem = f"{model_id.lower()}_coefficients_by_effort_version"
    fig.savefig(fig_dir / f"{stem}.png", dpi=220)
    fig.savefig(fig_dir / f"{stem}.pdf")
    plt.close(fig)


def plot_expanded_heatmap(
    summary: pd.DataFrame,
    fig_dir: Path,
    *,
    approach_id: str,
    value_col: str,
    filename: str,
    title: str,
    cbar_label: str,
    center_zero: bool,
) -> None:
    """Plot one compact heatmap for expanded model-family results."""

    sub = summary[summary["approach_id"].eq(approach_id) & summary["status"].eq("fit")].copy()
    effort_order = [label for _, label in EFFORT_MEASURES]
    family_order = sub[["model_family_id", "model_family_label"]].drop_duplicates()["model_family_label"].tolist()
    pivot = sub.pivot(index="model_family_label", columns="effort_label", values=value_col)
    pivot = pivot.reindex(index=family_order, columns=effort_order)
    fig_height = max(4.5, 0.55 * len(pivot) + 1.8)
    fig, ax = plt.subplots(figsize=(12.6, fig_height))
    kwargs = {"annot": True, "fmt": ".3g", "linewidths": 0.5, "linecolor": "white", "cbar_kws": {"label": cbar_label}}
    if center_zero:
        sns.heatmap(pivot, ax=ax, cmap="vlag", center=0, **kwargs)
    else:
        sns.heatmap(pivot, ax=ax, cmap="crest", **kwargs)
    ax.set_title(title)
    ax.set_xlabel("Effort measure")
    ax.set_ylabel("Model family")
    fig.tight_layout()
    fig.savefig(fig_dir / f"{filename}.png", dpi=220)
    fig.savefig(fig_dir / f"{filename}.pdf")
    plt.close(fig)


def slugify(value: str) -> str:
    """Return a stable filename slug."""

    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def expanded_plot_stem(approach_id: str, model_family_id: str) -> str:
    """Filename stem for an expanded model-family line plot."""

    return f"{approach_id.lower()}_{slugify(model_family_id)}_adjusted_age_lines"


def m3_interaction_plot_stem(model_family_id: str) -> str:
    """Filename stem for an M3 age-by-effort interaction plot."""

    return f"m3_{slugify(model_family_id)}_interaction_age_lines"


def prediction_summary_frame(result: object, new_frame: pd.DataFrame) -> pd.DataFrame:
    """Return predicted means and model-confidence bands when available."""

    try:
        summary = result.get_prediction(new_frame).summary_frame(alpha=0.05)
    except Exception:
        pred = np.asarray(result.predict(new_frame), dtype=float)
        return pd.DataFrame(
            {
                "predicted_sum_bits": pred,
                "pred_ci_low": np.nan,
                "pred_ci_high": np.nan,
            }
        )

    mean_col = "mean" if "mean" in summary.columns else "predicted_mean" if "predicted_mean" in summary.columns else None
    low_col = "mean_ci_lower" if "mean_ci_lower" in summary.columns else "ci_lower" if "ci_lower" in summary.columns else None
    high_col = "mean_ci_upper" if "mean_ci_upper" in summary.columns else "ci_upper" if "ci_upper" in summary.columns else None
    pred = np.asarray(summary[mean_col], dtype=float) if mean_col else np.asarray(result.predict(new_frame), dtype=float)
    return pd.DataFrame(
        {
            "predicted_sum_bits": pred,
            "pred_ci_low": np.asarray(summary[low_col], dtype=float) if low_col else np.nan,
            "pred_ci_high": np.asarray(summary[high_col], dtype=float) if high_col else np.nan,
        }
    )


def expanded_prediction_grid(bundle: ExpandedFitBundle, frame: pd.DataFrame, n_points: int = 90) -> pd.DataFrame:
    """Create adjusted age predictions for one expanded fitted model."""

    if bundle.result is None:
        return pd.DataFrame()
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    effort_col = bundle.effort_col
    age_mean = float(frame["age_months"].mean())
    effort_mean = float(frame[effort_col].mean())
    effort_median = float(frame[effort_col].median())
    base = pd.DataFrame(
        {
            "age_months": ages,
            "age_c": ages - age_mean,
            "effort_value": effort_median,
            "effort_c": effort_median - effort_mean,
        }
    )
    if "C(child_id)" in bundle.formula:
        child_ids = sorted(frame["child_id"].astype(str).unique())
        parts: list[pd.DataFrame] = []
        for child_id in child_ids:
            child_frame = base.copy()
            child_frame["child_id"] = child_id
            pred_summary = prediction_summary_frame(bundle.result, child_frame)
            child_frame["predicted_sum_bits"] = pred_summary["predicted_sum_bits"].to_numpy()
            child_frame["pred_ci_low"] = pred_summary["pred_ci_low"].to_numpy()
            child_frame["pred_ci_high"] = pred_summary["pred_ci_high"].to_numpy()
            parts.append(child_frame)
        pred = (
            pd.concat(parts, ignore_index=True)
            .groupby("age_months", as_index=False)[["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]]
            .mean()
        )
    else:
        pred = base[["age_months"]].copy()
        pred_summary = prediction_summary_frame(bundle.result, base)
        pred["predicted_sum_bits"] = pred_summary["predicted_sum_bits"].to_numpy()
        pred["pred_ci_low"] = pred_summary["pred_ci_low"].to_numpy()
        pred["pred_ci_high"] = pred_summary["pred_ci_high"].to_numpy()
    pred["approach_id"] = bundle.approach_id
    pred["model_family_id"] = bundle.model_family_id
    pred["model_family_label"] = bundle.model_family_label
    pred["effort_label"] = bundle.effort_label
    pred["held_effort_value"] = effort_median
    pred["effect_scale"] = bundle.effect_scale
    return pred


def plot_expanded_regression_lines(
    expanded_bundles: Sequence[ExpandedFitBundle],
    frame: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Plot clear adjusted age lines for each expanded model-family version."""

    prediction_parts: list[pd.DataFrame] = []
    raw = frame.groupby("age_bin", observed=True).agg(
        age_months=("age_months", "mean"),
        mean_sum_bits=("sum_bits", "mean"),
    ).reset_index()
    palette = sns.color_palette("colorblind", n_colors=len(EFFORT_MEASURES))
    color_map = {label: palette[idx] for idx, (_, label) in enumerate(EFFORT_MEASURES)}
    grouped: dict[tuple[str, str], list[ExpandedFitBundle]] = {}
    for bundle in expanded_bundles:
        grouped.setdefault((bundle.approach_id, bundle.model_family_id), []).append(bundle)
    for (approach_id, model_family_id), bundles in grouped.items():
        label = bundles[0].model_family_label
        fig, ax = plt.subplots(figsize=(10.5, 6.2))
        ax.scatter(raw["age_months"], raw["mean_sum_bits"], color="#555555", s=34, alpha=0.75, label="Raw age-bin mean")
        for bundle in bundles:
            pred = expanded_prediction_grid(bundle, frame)
            if pred.empty:
                continue
            prediction_parts.append(pred)
            linestyle = "--" if bundle.effect_scale == "log mean bits" else "-"
            ax.plot(
                pred["age_months"],
                pred["predicted_sum_bits"],
                color=color_map[bundle.effort_label],
                linewidth=2.2,
                linestyle=linestyle,
                label=f"{bundle.effort_label}, fixed at median {pred['held_effort_value'].iloc[0]:.1f}",
            )
            ci = pred[["pred_ci_low", "pred_ci_high"]].apply(pd.to_numeric, errors="coerce")
            if ci.notna().all(axis=None):
                ax.fill_between(
                    pred["age_months"].to_numpy(dtype=float),
                    ci["pred_ci_low"].to_numpy(dtype=float),
                    ci["pred_ci_high"].to_numpy(dtype=float),
                    color=color_map[bundle.effort_label],
                    alpha=0.12,
                    linewidth=0,
                )
        ax.set_title(f"{approach_id}: {label}")
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Predicted total bits")
        ax.grid(alpha=0.18)
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True, fontsize=10)
        fig.tight_layout(rect=(0, 0, 0.78, 1))
        stem = expanded_plot_stem(approach_id, model_family_id)
        fig.savefig(fig_dir / f"{stem}.png", dpi=220)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)
    return pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()


def m3_interaction_prediction_grid(bundle: ExpandedFitBundle, frame: pd.DataFrame, n_points: int = 80) -> pd.DataFrame:
    """Create M3 predictions across age at low/median/high fixed effort values."""

    if bundle.result is None:
        return pd.DataFrame()
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    effort_col = bundle.effort_col
    age_mean = float(frame["age_months"].mean())
    effort_mean = float(frame[effort_col].mean())
    quantiles = frame[effort_col].quantile([0.25, 0.50, 0.75]).to_dict()
    effort_levels = [
        ("low effort (25th pct.)", float(quantiles[0.25])),
        ("median effort (50th pct.)", float(quantiles[0.50])),
        ("high effort (75th pct.)", float(quantiles[0.75])),
    ]
    parts: list[pd.DataFrame] = []
    for effort_label, effort_value in effort_levels:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - age_mean,
                "effort_value": effort_value,
                "effort_c": effort_value - effort_mean,
            }
        )
        if "C(child_id)" in bundle.formula:
            child_ids = sorted(frame["child_id"].astype(str).unique())
            child_parts: list[pd.DataFrame] = []
            for child_id in child_ids:
                child_frame = base.copy()
                child_frame["child_id"] = child_id
                pred_summary = prediction_summary_frame(bundle.result, child_frame)
                child_frame["predicted_sum_bits"] = pred_summary["predicted_sum_bits"].to_numpy()
                child_frame["pred_ci_low"] = pred_summary["pred_ci_low"].to_numpy()
                child_frame["pred_ci_high"] = pred_summary["pred_ci_high"].to_numpy()
                child_parts.append(child_frame)
            pred = (
                pd.concat(child_parts, ignore_index=True)
                .groupby("age_months", as_index=False)[["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]]
                .mean()
            )
        else:
            pred = base[["age_months"]].copy()
            pred_summary = prediction_summary_frame(bundle.result, base)
            pred["predicted_sum_bits"] = pred_summary["predicted_sum_bits"].to_numpy()
            pred["pred_ci_low"] = pred_summary["pred_ci_low"].to_numpy()
            pred["pred_ci_high"] = pred_summary["pred_ci_high"].to_numpy()
        pred["effort_level"] = effort_label
        pred["fixed_effort_value"] = effort_value
        pred["approach_id"] = bundle.approach_id
        pred["model_family_id"] = bundle.model_family_id
        pred["model_family_label"] = bundle.model_family_label
        pred["effort_label"] = bundle.effort_label
        pred["effect_scale"] = bundle.effect_scale
        parts.append(pred)
    return pd.concat(parts, ignore_index=True)


def plot_m3_interaction_regression_lines(
    expanded_bundles: Sequence[ExpandedFitBundle],
    frame: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Plot M3 interaction lines at low/median/high effort for each family."""

    m3_bundles = [bundle for bundle in expanded_bundles if bundle.approach_id == "M3"]
    prediction_parts: list[pd.DataFrame] = []
    grouped: dict[str, list[ExpandedFitBundle]] = {}
    for bundle in m3_bundles:
        grouped.setdefault(bundle.model_family_id, []).append(bundle)
    palette = {
        "low effort (25th pct.)": "#4c78a8",
        "median effort (50th pct.)": "#f58518",
        "high effort (75th pct.)": "#54a24b",
    }
    effort_order = [label for _, label in EFFORT_MEASURES]
    for model_family_id, bundles in grouped.items():
        label = bundles[0].model_family_label
        fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6), sharey=True)
        axes = axes.flatten()
        by_effort = {bundle.effort_label: bundle for bundle in bundles}
        for ax, effort_label in zip(axes, effort_order):
            bundle = by_effort.get(effort_label)
            if bundle is None:
                ax.axis("off")
                continue
            pred = m3_interaction_prediction_grid(bundle, frame)
            if pred.empty:
                ax.axis("off")
                continue
            prediction_parts.append(pred)
            ribbon_palette = {
                "low effort": "#4c78a8",
                "mid effort": "#f58518",
                "high effort": "#54a24b",
            }
            add_effort_level_age_ribbons(ax, frame, effort_value_col=bundle.effort_col, palette=ribbon_palette)
            for effort_level, group in pred.groupby("effort_level", sort=False):
                ax.plot(
                    group["age_months"],
                    group["predicted_sum_bits"],
                    linewidth=2.1,
                    color=palette[effort_level],
                    label=f"{effort_level}: {group['fixed_effort_value'].iloc[0]:.1f}",
                )
                ci = group[["pred_ci_low", "pred_ci_high"]].apply(pd.to_numeric, errors="coerce")
                if ci.notna().all(axis=None):
                    ax.fill_between(
                        group["age_months"].to_numpy(dtype=float),
                        ci["pred_ci_low"].to_numpy(dtype=float),
                        ci["pred_ci_high"].to_numpy(dtype=float),
                        color=palette[effort_level],
                        alpha=0.10,
                        linewidth=0,
                    )
            ax.set_title(effort_label)
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
        axes[-1].axis("off")
        axes[0].set_ylabel("Predicted total bits")
        axes[3].set_ylabel("Predicted total bits")
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.96, 0.08), frameon=True, fontsize=10)
        fig.suptitle(f"M3: {label}", y=0.99)
        fig.tight_layout(rect=(0, 0, 0.88, 0.95))
        stem = m3_interaction_plot_stem(model_family_id)
        fig.savefig(fig_dir / f"{stem}.png", dpi=220)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)
    return pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()


def mean_sem(frame: pd.DataFrame, group_cols: Sequence[str], value_col: str) -> pd.DataFrame:
    """Compute mean and standard error by group."""

    return (
        frame.dropna(subset=[value_col])
        .groupby(list(group_cols), observed=True)[value_col]
        .agg(mean="mean", sem="sem", n_rows="count")
        .reset_index()
    )


def add_overall_age_ribbon(
    ax: plt.Axes,
    frame: pd.DataFrame,
    *,
    y_col: str = "sum_bits",
    color: str = "#6b6b6b",
    alpha: float = 0.12,
    label: str = "Observed age-bin mean +/- SE",
) -> None:
    """Add an empirical mean +/- standard-error ribbon by age bin."""

    if frame.empty or y_col not in frame.columns:
        return
    summary = (
        frame.dropna(subset=["age_months", y_col])
        .groupby("age_bin", observed=True)
        .agg(age_months=("age_months", "mean"), mean=(y_col, "mean"), se=(y_col, "sem"), n_rows=(y_col, "size"))
        .reset_index()
        .sort_values("age_months")
    )
    if summary.empty:
        return
    x = summary["age_months"].to_numpy(dtype=float)
    y = summary["mean"].to_numpy(dtype=float)
    se = summary["se"].fillna(0).to_numpy(dtype=float)
    ax.fill_between(x, y - se, y + se, color=color, alpha=alpha, linewidth=0, label=label)


def add_effort_level_age_ribbons(
    ax: plt.Axes,
    frame: pd.DataFrame,
    *,
    effort_value_col: str,
    palette: Mapping[str, str],
    y_col: str = "sum_bits",
    alpha: float = 0.10,
) -> None:
    """Add empirical mean +/- SE ribbons by low/mid/high effort level."""

    if frame.empty or y_col not in frame.columns or effort_value_col not in frame.columns:
        return
    plot_frame = frame.dropna(subset=["age_months", y_col, effort_value_col]).copy()
    if plot_frame.empty:
        return
    if "effort_level" not in plot_frame.columns:
        plot_frame["effort_level"] = assign_effort_level(plot_frame[effort_value_col])
    else:
        plot_frame["effort_level"] = pd.Categorical(
            plot_frame["effort_level"].astype(str),
            categories=["low effort", "mid effort", "high effort"],
            ordered=True,
        )
    summary = (
        plot_frame.groupby(["age_bin", "effort_level"], observed=True)
        .agg(age_months=("age_months", "mean"), mean=(y_col, "mean"), se=(y_col, "sem"), n_rows=(y_col, "size"))
        .reset_index()
        .sort_values(["effort_level", "age_months"])
    )
    for level, group in summary.groupby("effort_level", sort=False, observed=True):
        if group.empty:
            continue
        level_str = str(level)
        x = group["age_months"].to_numpy(dtype=float)
        y = group["mean"].to_numpy(dtype=float)
        se = group["se"].fillna(0).to_numpy(dtype=float)
        ax.fill_between(
            x,
            y - se,
            y + se,
            color=palette.get(level_str, "#8a8a8a"),
            alpha=alpha,
            linewidth=0,
            label=f"Observed {level_str} +/- SE",
        )


def plot_m4_context_entropy_bins(m4_frame: pd.DataFrame, fig_dir: Path) -> None:
    """Plot descriptive context-entropy bins against total information."""

    if m4_frame.empty:
        return
    plot_frame = m4_frame.drop_duplicates(subset=["score_id"]).dropna(subset=["context_entropy_bits", "sum_bits"]).copy()
    if plot_frame.empty:
        return
    plot_frame["entropy_bin"] = pd.qcut(plot_frame["context_entropy_bits"], q=8, duplicates="drop")
    plot_frame["entropy_bin_mid"] = plot_frame["entropy_bin"].map(lambda interval: float(interval.mid)).astype(float)
    specs = [
        ("sum_bits", "Total bits", "Information: total bits"),
        ("nb_words", "Words in child utterance", "Effort: words"),
        ("nb_phonemes", "Phonemes in child utterance", "Effort: phonemes"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(17.0, 5.3))
    palette = {
        "006-023": "#4c78a8",
        "024-035": "#f58518",
        "036-047": "#54a24b",
        "048-065": "#b279a2",
    }
    for ax, (outcome, ylabel, title) in zip(axes, specs):
        summary = (
            plot_frame.groupby(["entropy_bin", "age_stage"], observed=True)
            .agg(entropy_mid=("entropy_bin_mid", "mean"), mean=(outcome, "mean"), sem=(outcome, "sem"), n_rows=(outcome, "count"))
            .reset_index()
            .dropna(subset=["entropy_mid", "mean"])
        )
        for stage, group in summary.groupby("age_stage", observed=True):
            group = group.sort_values("entropy_mid")
            color = palette.get(str(stage))
            ax.plot(group["entropy_mid"], group["mean"], marker="o", linewidth=2.0, label=str(stage), color=color)
            ax.fill_between(
                group["entropy_mid"].to_numpy(dtype=float),
                (group["mean"] - 1.96 * group["sem"].fillna(0)).to_numpy(dtype=float),
                (group["mean"] + 1.96 * group["sem"].fillna(0)).to_numpy(dtype=float),
                alpha=0.12,
                color=color,
            )
        ax.set_title(title)
        ax.set_xlabel("Context entropy (bits)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.20)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Age stage", loc="lower center", ncol=4)
    fig.suptitle("M4 Descriptive Check: Context Entropy Before Controls", y=0.98)
    fig.tight_layout(rect=(0, 0.12, 1, 0.91))
    fig.savefig(fig_dir / "m4_context_entropy_descriptive_bins.png", dpi=240)
    fig.savefig(fig_dir / "m4_context_entropy_descriptive_bins.pdf")
    plt.close(fig)


def m4_prediction_grid(bundle: M4FitBundle, m4_frame: pd.DataFrame, n_points: int = 90) -> pd.DataFrame:
    """Create adjusted M4 age predictions at low/median/high context entropy."""

    if bundle.result is None or m4_frame.empty:
        return pd.DataFrame()
    frame = m4_frame[m4_frame["effort_col"].eq(bundle.effort_col)].copy()
    if frame.empty:
        return pd.DataFrame()
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    age_mean = float(frame["age_months"].mean())
    entropy_mean = float(frame["context_entropy_bits"].mean())
    effort_mean = float(frame["effort_value"].mean())
    effort_median = float(frame["effort_value"].median())
    entropy_quantiles = frame["context_entropy_bits"].quantile([0.25, 0.50, 0.75]).to_dict()
    entropy_levels = [
        ("low entropy (25th pct.)", float(entropy_quantiles[0.25])),
        ("median entropy (50th pct.)", float(entropy_quantiles[0.50])),
        ("high entropy (75th pct.)", float(entropy_quantiles[0.75])),
    ]
    parts: list[pd.DataFrame] = []
    for entropy_label, entropy_value in entropy_levels:
        pred_frame = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - age_mean,
                "effort_value": effort_median,
                "effort_c": effort_median - effort_mean,
                "context_entropy_bits": entropy_value,
                "context_entropy_c": entropy_value - entropy_mean,
            }
        )
        if "C(child_id)" in bundle.formula:
            child_parts: list[pd.DataFrame] = []
            for child_id in sorted(frame["child_id"].astype(str).unique()):
                child_frame = pred_frame.copy()
                child_frame["child_id"] = child_id
                child_frame["predicted"] = np.asarray(bundle.result.predict(child_frame), dtype=float)
                child_parts.append(child_frame)
            pred = (
                pd.concat(child_parts, ignore_index=True)
                .groupby("age_months", as_index=False)["predicted"]
                .mean()
            )
        else:
            pred = pred_frame[["age_months"]].copy()
            pred["predicted"] = np.asarray(bundle.result.predict(pred_frame), dtype=float)
        pred["entropy_level"] = entropy_label
        pred["fixed_context_entropy_bits"] = entropy_value
        pred["fixed_effort_value"] = effort_median
        pred["model_id"] = bundle.model_id
        pred["model_label"] = bundle.model_label
        pred["outcome"] = bundle.outcome
        pred["effort_col"] = bundle.effort_col
        pred["effort_label"] = bundle.effort_label
        pred["effect_scale"] = bundle.effect_scale
        parts.append(pred)
    return pd.concat(parts, ignore_index=True)


def plot_m4_adjusted_predictions(bundles: Sequence[M4FitBundle], m4_frame: pd.DataFrame, fig_dir: Path) -> pd.DataFrame:
    """Plot adjusted M4 information predictions over age."""

    if m4_frame.empty:
        return pd.DataFrame()
    fitted = [bundle for bundle in bundles if bundle.result is not None]
    if not fitted:
        return pd.DataFrame()
    prediction_parts: list[pd.DataFrame] = []
    palette = {
        "low entropy (25th pct.)": "#4c78a8",
        "median entropy (50th pct.)": "#f58518",
        "high entropy (75th pct.)": "#54a24b",
    }
    order = [label for _, label in EFFORT_MEASURES]
    by_model: dict[str, list[M4FitBundle]] = {}
    for bundle in fitted:
        by_model.setdefault(bundle.model_id, []).append(bundle)

    for model_id, selected in by_model.items():
        selected = sorted(selected, key=lambda bundle: order.index(bundle.effort_label))
        fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6), sharey=True)
        axes = axes.flatten()
        used_axes = 0
        for ax, bundle in zip(axes, selected):
            pred = m4_prediction_grid(bundle, m4_frame)
            if pred.empty:
                ax.axis("off")
                continue
            prediction_parts.append(pred)
            used_axes += 1
            frame_slice = m4_frame[m4_frame["effort_col"].eq(bundle.effort_col)].copy()
            add_overall_age_ribbon(ax, frame_slice, alpha=0.10)
            for entropy_level, group in pred.groupby("entropy_level", sort=False):
                ax.plot(
                    group["age_months"],
                    group["predicted"],
                    linewidth=2.2,
                    color=palette.get(str(entropy_level)),
                    label=f"{entropy_level}: {group['fixed_context_entropy_bits'].iloc[0]:.2f} bits",
                )
            ax.set_title(f"{bundle.effort_label}\neffort reference={pred['fixed_effort_value'].iloc[0]:.1f}")
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.20)
        for ax in axes[used_axes:]:
            ax.axis("off")
        axes[0].set_ylabel("Predicted total bits")
        if len(axes) > 3:
            axes[3].set_ylabel("Predicted total bits")
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, title="Context entropy reference", loc="lower center", ncol=3)
        label = selected[0].model_label if selected else model_id
        fig.suptitle(f"{label}: Context-Entropy Reference Lines", y=0.99)
        fig.tight_layout(rect=(0, 0.12, 1, 0.94))
        stem = f"m4_{model_id.lower()}_context_entropy_adjusted_predictions"
        fig.savefig(fig_dir / f"{stem}.png", dpi=240)
        fig.savefig(fig_dir / f"{stem}.pdf")
        if model_id == "M4a":
            fig.savefig(fig_dir / "m4_context_entropy_adjusted_predictions.png", dpi=240)
            fig.savefig(fig_dir / "m4_context_entropy_adjusted_predictions.pdf")
        plt.close(fig)
    return pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()


def m4_effort_quantile_prediction_grid(bundle: M4FitBundle, m4_frame: pd.DataFrame, n_points: int = 90) -> pd.DataFrame:
    """Create M4a predictions at low/median/high continuous effort and median entropy."""

    if bundle.result is None or m4_frame.empty:
        return pd.DataFrame()
    frame = m4_frame[m4_frame["effort_col"].eq(bundle.effort_col)].copy()
    if frame.empty:
        return pd.DataFrame()
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    age_mean = float(frame["age_months"].mean())
    effort_mean = float(frame["effort_value"].mean())
    entropy_mean = float(frame["context_entropy_bits"].mean())
    entropy_median = float(frame["context_entropy_bits"].median())
    quantiles = frame["effort_value"].quantile([0.25, 0.50, 0.75]).to_dict()
    effort_levels = [
        ("low effort (25th pct.)", float(quantiles[0.25])),
        ("median effort (50th pct.)", float(quantiles[0.50])),
        ("high effort (75th pct.)", float(quantiles[0.75])),
    ]
    parts: list[pd.DataFrame] = []
    for effort_level, effort_value in effort_levels:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - age_mean,
                "effort_value": effort_value,
                "effort_c": effort_value - effort_mean,
                "context_entropy_bits": entropy_median,
                "context_entropy_c": entropy_median - entropy_mean,
            }
        )
        child_parts: list[pd.DataFrame] = []
        if "C(child_id)" in bundle.formula:
            for child_id in sorted(frame["child_id"].astype(str).unique()):
                child_frame = base.copy()
                child_frame["child_id"] = child_id
                child_frame["predicted"] = np.asarray(bundle.result.predict(child_frame), dtype=float)
                child_parts.append(child_frame)
            pred = (
                pd.concat(child_parts, ignore_index=True)
                .groupby("age_months", as_index=False)["predicted"]
                .mean()
            )
        else:
            pred = base[["age_months"]].copy()
            pred["predicted"] = np.asarray(bundle.result.predict(base), dtype=float)
        pred["model_id"] = bundle.model_id
        pred["model_label"] = bundle.model_label
        pred["effort_col"] = bundle.effort_col
        pred["effort_label"] = bundle.effort_label
        pred["effort_level"] = effort_level
        pred["fixed_effort_value"] = effort_value
        pred["fixed_context_entropy_bits"] = entropy_median
        parts.append(pred)
    return pd.concat(parts, ignore_index=True)


def plot_m4_effort_quantile_predictions(
    bundles: Sequence[M4FitBundle],
    m4_frame: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Plot M4a age lines at low/median/high continuous effort values."""

    selected = [bundle for bundle in bundles if bundle.model_id == "M4a" and bundle.result is not None]
    if not selected or m4_frame.empty:
        return pd.DataFrame()
    prediction_parts = [m4_effort_quantile_prediction_grid(bundle, m4_frame) for bundle in selected]
    predictions = pd.concat([part for part in prediction_parts if not part.empty], ignore_index=True) if prediction_parts else pd.DataFrame()
    if predictions.empty:
        return predictions
    palette = {
        "low effort (25th pct.)": "#4c78a8",
        "median effort (50th pct.)": "#f58518",
        "high effort (75th pct.)": "#54a24b",
    }
    effort_order = [label for _, label in EFFORT_MEASURES]
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6), sharey=True)
    axes = axes.flatten()
    for ax, effort_label in zip(axes, effort_order):
        sub = predictions[predictions["effort_label"].eq(effort_label)]
        if sub.empty:
            ax.axis("off")
            continue
        effort_col = EFFORT_LABEL_TO_COL[effort_label]
        frame_slice = m4_frame[m4_frame["effort_col"].eq(effort_col)].copy()
        ribbon_palette = {
            "low effort": "#4c78a8",
            "mid effort": "#f58518",
            "high effort": "#54a24b",
        }
        add_effort_level_age_ribbons(ax, frame_slice, effort_value_col="effort_value", palette=ribbon_palette)
        for effort_level, group in sub.groupby("effort_level", sort=False):
            ax.plot(
                group["age_months"],
                group["predicted"],
                linewidth=2.1,
                color=palette.get(str(effort_level)),
                label=f"{effort_level}: {group['fixed_effort_value'].iloc[0]:.1f}",
            )
        ax.set_title(f"{effort_label}\ncontext entropy={sub['fixed_context_entropy_bits'].iloc[0]:.2f}")
        ax.set_xlabel("Age in months")
        ax.grid(alpha=0.18)
    axes[-1].axis("off")
    axes[0].set_ylabel("Predicted total bits")
    axes[3].set_ylabel("Predicted total bits")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Continuous effort reference", loc="lower center", ncol=3)
    fig.suptitle("M4a: Context Controlled, Effort Varied", y=0.99)
    fig.tight_layout(rect=(0, 0.11, 1, 0.94))
    fig.savefig(fig_dir / "m4_effort_quantile_adjusted_predictions.png", dpi=240)
    fig.savefig(fig_dir / "m4_effort_quantile_adjusted_predictions.pdf")
    plt.close(fig)
    return predictions


def plot_m4_coefficients(m4_summary: pd.DataFrame, fig_dir: Path) -> None:
    """Plot M4 context-entropy coefficients."""

    if m4_summary.empty:
        return
    plot_frame = m4_summary[m4_summary["status"].eq("fit")].copy()
    if plot_frame.empty or "entropy_coef" not in plot_frame.columns:
        return
    effort_order = [label for _, label in EFFORT_MEASURES]
    family_order = plot_frame[["model_id", "model_label"]].drop_duplicates()["model_label"].tolist()
    pivot = plot_frame.pivot(index="model_label", columns="effort_label", values="entropy_coef").reindex(index=family_order, columns=effort_order)
    fig, ax = plt.subplots(figsize=(12.8, max(4.8, 0.6 * len(pivot) + 1.8)))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap="vlag",
        center=0,
        annot=True,
        fmt=".3g",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Context entropy coefficient"},
    )
    ax.set_xlabel("Effort control")
    ax.set_ylabel("M4 model family")
    ax.set_title("M4 Context-Entropy Coefficients Across Effort Controls")
    fig.tight_layout()
    fig.savefig(fig_dir / "m4_context_entropy_coefficients.png", dpi=240)
    fig.savefig(fig_dir / "m4_context_entropy_coefficients.pdf")
    plt.close(fig)


def saturated_prediction_grid(bundle: SaturatedFitBundle, frame: pd.DataFrame, n_points: int = 90) -> pd.DataFrame:
    """Create adjusted age predictions for M5/M6 by effort level."""

    if bundle.result is None or frame.empty:
        return pd.DataFrame()
    frame = frame[frame["effort_col"].eq(bundle.effort_col)].copy()
    if frame.empty:
        return pd.DataFrame()
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    levels = [level for level in ["low effort", "mid effort", "high effort"] if level in set(frame["effort_level"].astype(str))]
    parts: list[pd.DataFrame] = []
    for level in levels:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - float(frame["age_months"].mean()),
                "context_entropy_c": 0.0,
                "effort_level": pd.Categorical(
                    [level] * len(ages),
                    categories=["low effort", "mid effort", "high effort"],
                    ordered=True,
                ),
            }
        )
        if "C(child_id)" in bundle.formula:
            child_parts: list[pd.DataFrame] = []
            for child_id in sorted(frame["child_id"].astype(str).unique()):
                child_frame = base.copy()
                child_frame["child_id"] = child_id
                child_frame["predicted_sum_bits"] = np.asarray(bundle.result.predict(child_frame), dtype=float)
                child_parts.append(child_frame)
            pred = pd.concat(child_parts, ignore_index=True).groupby("age_months", as_index=False)["predicted_sum_bits"].mean()
        else:
            pred = base[["age_months"]].copy()
            pred["predicted_sum_bits"] = np.asarray(bundle.result.predict(base), dtype=float)
        pred["model_id"] = bundle.model_id
        pred["model_label"] = bundle.model_label
        pred["effort_col"] = bundle.effort_col
        pred["effort_label"] = bundle.effort_label
        pred["effort_level"] = level
        pred["fixed_context_entropy"] = "mean context entropy"
        parts.append(pred)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def plot_saturated_predictions(bundles: Sequence[SaturatedFitBundle], frame: pd.DataFrame, fig_dir: Path) -> pd.DataFrame:
    """Plot M5/M6 adjusted age predictions by categorical effort level."""

    if frame.empty:
        return pd.DataFrame()
    prediction_parts = [saturated_prediction_grid(bundle, frame) for bundle in bundles]
    predictions = pd.concat([part for part in prediction_parts if not part.empty], ignore_index=True) if prediction_parts else pd.DataFrame()
    if predictions.empty:
        return predictions
    palette = {
        "low effort": "#4c78a8",
        "mid effort": "#f58518",
        "high effort": "#54a24b",
    }
    effort_order = [label for _, label in EFFORT_MEASURES]
    fig, axes = plt.subplots(2, 5, figsize=(19.0, 8.8), sharey=True)
    for row_idx, model_id in enumerate(["M5", "M6"]):
        model_pred = predictions[predictions["model_id"].eq(model_id)]
        for col_idx, effort_label in enumerate(effort_order):
            ax = axes[row_idx, col_idx]
            sub = model_pred[model_pred["effort_label"].eq(effort_label)]
            if sub.empty:
                ax.axis("off")
                continue
            effort_col = EFFORT_LABEL_TO_COL[effort_label]
            frame_slice = frame[frame["effort_col"].eq(effort_col)].copy()
            add_effort_level_age_ribbons(ax, frame_slice, effort_value_col="effort_value", palette=palette)
            for level, group in sub.groupby("effort_level", sort=False):
                ax.plot(
                    group["age_months"],
                    group["predicted_sum_bits"],
                    linewidth=2.0,
                    color=palette.get(str(level)),
                    label=str(level),
                )
            ax.set_title(f"{model_id}: {effort_label}")
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
            if col_idx == 0:
                ax.set_ylabel("Predicted total bits")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Effort level", loc="lower center", ncol=3)
    fig.suptitle("M5/M6: Child-Adjusted Total Bits by Age and Effort Level", y=0.98)
    fig.tight_layout(rect=(0, 0.09, 1, 0.93))
    fig.savefig(fig_dir / "m5_m6_saturated_adjusted_age_predictions.png", dpi=240)
    fig.savefig(fig_dir / "m5_m6_saturated_adjusted_age_predictions.pdf")
    fig.savefig(fig_dir / "m5_m6_effort_level_adjusted_age_predictions.png", dpi=240)
    fig.savefig(fig_dir / "m5_m6_effort_level_adjusted_age_predictions.pdf")
    plt.close(fig)
    for model_id in ["M5", "M6"]:
        model_pred = predictions[predictions["model_id"].eq(model_id)]
        if model_pred.empty:
            continue
        fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6), sharey=True)
        axes = axes.flatten()
        for ax, effort_label in zip(axes, effort_order):
            sub = model_pred[model_pred["effort_label"].eq(effort_label)]
            if sub.empty:
                ax.axis("off")
                continue
            effort_col = EFFORT_LABEL_TO_COL[effort_label]
            frame_slice = frame[frame["effort_col"].eq(effort_col)].copy()
            add_effort_level_age_ribbons(ax, frame_slice, effort_value_col="effort_value", palette=palette)
            for level, group in sub.groupby("effort_level", sort=False):
                ax.plot(
                    group["age_months"],
                    group["predicted_sum_bits"],
                    linewidth=2.1,
                    color=palette.get(str(level)),
                    label=str(level),
                )
            ax.set_title(effort_label)
            ax.set_xlabel("Age in months")
            ax.grid(alpha=0.18)
        axes[-1].axis("off")
        axes[0].set_ylabel("Predicted total bits")
        axes[3].set_ylabel("Predicted total bits")
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, title="Effort level", loc="lower center", ncol=3)
        title = "M5: Context Entropy and Effort Level" if model_id == "M5" else "M6: Age, Context, and Effort-Level Interactions"
        fig.suptitle(title, y=0.99)
        fig.tight_layout(rect=(0, 0.10, 1, 0.94))
        stem = "m5_effort_level_adjusted_age_predictions" if model_id == "M5" else "m6_effort_level_adjusted_age_predictions"
        fig.savefig(fig_dir / f"{stem}.png", dpi=240)
        fig.savefig(fig_dir / f"{stem}.pdf")
        plt.close(fig)
    return predictions


def saturated_average_prediction_grid(bundle: SaturatedFitBundle, frame: pd.DataFrame, n_points: int = 90) -> pd.DataFrame:
    """Create M5/M6 age predictions averaged across low/mid/high effort levels."""

    if bundle.result is None or frame.empty:
        return pd.DataFrame()
    frame = frame[frame["effort_col"].eq(bundle.effort_col)].copy()
    if frame.empty:
        return pd.DataFrame()
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), n_points)
    levels = [level for level in ["low effort", "mid effort", "high effort"] if level in set(frame["effort_level"].astype(str))]
    child_ids = sorted(frame["child_id"].astype(str).unique())
    rows: list[pd.DataFrame] = []
    for level in levels:
        base = pd.DataFrame(
            {
                "age_months": ages,
                "age_c": ages - float(frame["age_months"].mean()),
                "context_entropy_c": 0.0,
                "effort_level": pd.Categorical(
                    [level] * len(ages),
                    categories=["low effort", "mid effort", "high effort"],
                    ordered=True,
                ),
            }
        )
        if "C(child_id)" in bundle.formula:
            for child_id in child_ids:
                child_frame = base.copy()
                child_frame["child_id"] = child_id
                child_frame["predicted_sum_bits"] = np.asarray(bundle.result.predict(child_frame), dtype=float)
                rows.append(child_frame.assign(effort_level_reference=level))
        else:
            pred = base.copy()
            pred["predicted_sum_bits"] = np.asarray(bundle.result.predict(base), dtype=float)
            rows.append(pred.assign(effort_level_reference=level))
    if not rows:
        return pd.DataFrame()
    pred = (
        pd.concat(rows, ignore_index=True)
        .groupby("age_months", as_index=False)["predicted_sum_bits"]
        .mean()
    )
    pred["model_id"] = bundle.model_id
    pred["model_label"] = bundle.model_label
    pred["effort_col"] = bundle.effort_col
    pred["effort_label"] = bundle.effort_label
    pred["effort_level_reference"] = "average across low/mid/high effort levels"
    pred["fixed_context_entropy"] = "mean context entropy"
    return pred


def plot_saturated_average_predictions(
    bundles: Sequence[SaturatedFitBundle],
    frame: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Plot M5/M6 predictions without splitting the line by effort level."""

    prediction_parts = [saturated_average_prediction_grid(bundle, frame) for bundle in bundles]
    predictions = pd.concat([part for part in prediction_parts if not part.empty], ignore_index=True) if prediction_parts else pd.DataFrame()
    if predictions.empty:
        return predictions
    palette = sns.color_palette("colorblind", n_colors=len(EFFORT_MEASURES))
    color_map = {label: palette[idx] for idx, (_, label) in enumerate(EFFORT_MEASURES)}
    fig, axes = plt.subplots(1, 2, figsize=(15.2, 6.0), sharey=True)
    for ax, model_id in zip(axes, ["M5", "M6"]):
        sub = predictions[predictions["model_id"].eq(model_id)]
        if sub.empty:
            ax.axis("off")
            continue
        add_overall_age_ribbon(ax, frame.drop_duplicates(subset=["score_id"]), alpha=0.10)
        for effort_label, group in sub.groupby("effort_label", sort=False):
            ax.plot(
                group["age_months"],
                group["predicted_sum_bits"],
                linewidth=2.2,
                color=color_map.get(str(effort_label)),
                label=str(effort_label),
            )
        ax.set_title(f"{model_id}: averaged over low/mid/high effort levels")
        ax.set_xlabel("Age in months")
        ax.grid(alpha=0.18)
    axes[0].set_ylabel("Predicted total bits")
    axes[1].legend(title="Effort unit defining levels", loc="upper left", bbox_to_anchor=(1.02, 1))
    fig.suptitle("M5/M6: No Split by Effort Level", y=0.99)
    fig.tight_layout(rect=(0, 0, 0.88, 0.93))
    fig.savefig(fig_dir / "m5_m6_effort_level_average_age_predictions.png", dpi=240)
    fig.savefig(fig_dir / "m5_m6_effort_level_average_age_predictions.pdf")
    plt.close(fig)
    return predictions


def plot_saturated_coefficients(coefs: pd.DataFrame, fig_dir: Path) -> None:
    """Plot selected M5/M6 coefficients."""

    if coefs.empty:
        return
    selected_terms = [
        "age_c",
        "context_entropy_c",
        "age_c:context_entropy_c",
        "C(effort_level)[T.mid effort]",
        "C(effort_level)[T.high effort]",
        "age_c:C(effort_level)[T.mid effort]",
        "age_c:C(effort_level)[T.high effort]",
        "context_entropy_c:C(effort_level)[T.mid effort]",
        "context_entropy_c:C(effort_level)[T.high effort]",
    ]
    plot_frame = coefs[coefs["term"].isin(selected_terms)].copy()
    if plot_frame.empty:
        return
    plot_frame["term"] = pd.Categorical(plot_frame["term"], selected_terms, ordered=True)
    plot_frame["row_label"] = plot_frame["model_id"].astype(str) + ": " + plot_frame["term"].astype(str)
    row_order = (
        plot_frame[["model_id", "term", "row_label"]]
        .drop_duplicates()
        .sort_values(["model_id", "term"])["row_label"]
        .tolist()
    )
    pivot = (
        plot_frame.pivot_table(index="row_label", columns="effort_label", values="estimate", aggfunc="first")
        .reindex(index=row_order, columns=[label for _, label in EFFORT_MEASURES])
    )
    fig, ax = plt.subplots(figsize=(13.6, max(5.6, 0.42 * len(pivot) + 1.8)))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap="vlag",
        center=0,
        annot=True,
        fmt=".3g",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Coefficient"},
    )
    ax.set_title("M5/M6 Selected Coefficients by Effort Version")
    ax.set_xlabel("Effort measure used to create low/mid/high levels")
    ax.set_ylabel("Model and term")
    fig.tight_layout()
    fig.savefig(fig_dir / "m5_m6_saturated_selected_coefficients.png", dpi=240)
    fig.savefig(fig_dir / "m5_m6_saturated_selected_coefficients.pdf")
    plt.close(fig)


def write_markdown_table(frame: pd.DataFrame, *, max_rows: int = 12, digits: int = 4) -> str:
    """Convert a small dataframe to a Markdown table."""

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
    body = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *body])


def format_p(value: float) -> str:
    """Compact p-value formatting."""

    if pd.isna(value):
        return ""
    if value < 0.001:
        return "<.001"
    return f"{value:.3f}"


def model_family_explanation(*, approach_id: str, model_family_id: str, effect_scale: str) -> str:
    """Return a short plain-language explanation for one model-family subsection."""

    if approach_id == "M1":
        question = "Does age predict total bits after controlling for effort, pooling all children together?"
        controls = "Controls effort only. It does not control stable child-to-child differences."
        key_term = "The age coefficient is the pooled age trend at a fixed utterance size."
    elif approach_id == "M2":
        question = "Does age predict total bits after controlling for effort and child-level dependence?"
        controls = "Controls effort and accounts for child identity or child-level clustering, depending on the version."
        key_term = "The age coefficient is the child-adjusted developmental trend at a fixed utterance size."
    elif approach_id == "M3":
        question = "Does the effort-to-information relation change with age?"
        controls = "Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity."
        key_term = "The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases."
    else:  # pragma: no cover - defensive guard for future model groups
        question = "What does this model ask?"
        controls = "See the formula."
        key_term = "See the coefficient table."

    family_notes: list[str] = []
    if "ols_cluster" in model_family_id:
        family_notes.append("The fitted line is ordinary least squares; only the standard errors and p-values are corrected for repeated utterances within child.")
    elif model_family_id.startswith("ols"):
        family_notes.append("Ordinary least squares gives additive bit-scale coefficients.")
    if "child_fe" in model_family_id:
        family_notes.append("Child fixed effects mean each child has their own baseline intercept.")
    if "age_slope" in model_family_id and "child_fe" in model_family_id:
        family_notes.append("The child age-slope term allows each child to have their own linear developmental slope.")
    if "glm_gaussian" in model_family_id:
        family_notes.append("Gaussian GLM is a GLM version of the linear model; predictions remain on the total-bits scale.")
    if "gamma_log" in model_family_id:
        family_notes.append("Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation.")
    if "gee" in model_family_id:
        family_notes.append("GEE estimates a population-average effect while clustering repeated utterances by child.")
    if "mixed_random_intercept" in model_family_id:
        family_notes.append("The mixed model adds a random child baseline; singular random-effect warnings mean this should be read as a sensitivity diagnostic.")
    if "mixed_random_age_slope" in model_family_id:
        family_notes.append("The mixed model lets child baselines and linear age slopes vary; convergence warnings should be treated as diagnostics.")
    if effect_scale == "log mean bits":
        family_notes.append("Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.")

    note_text = " ".join(family_notes)
    return f"""Question asked: {question}

Controls / structure: {controls}

How to read it: {key_term} {note_text}
"""


def model_version_table(fit_summary: pd.DataFrame, coef_summary: pd.DataFrame, *, model_id: str) -> pd.DataFrame:
    """Return one compact row per effort version for one model."""

    fits = fit_summary[fit_summary["model_id"].eq(model_id)][["effort_label", "formula", "r2", "rmse", "mae"]].copy()
    age = coef_summary[coef_summary["model_id"].eq(model_id) & coef_summary["term"].eq("age_months")][
        ["effort_label", "coef", "p_value", "ci_low", "ci_high"]
    ].rename(
        columns={
            "coef": "age_coef",
            "p_value": "age_p",
            "ci_low": "age_ci_low",
            "ci_high": "age_ci_high",
        }
    )
    effort = coef_summary[coef_summary["model_id"].eq(model_id) & coef_summary["term"].eq("effort_value")][
        ["effort_label", "coef", "p_value"]
    ].rename(columns={"coef": "effort_coef", "p_value": "effort_p"})
    out = fits.merge(age, on="effort_label", how="left").merge(effort, on="effort_label", how="left")
    out["age_p"] = out["age_p"].map(format_p)
    out["effort_p"] = out["effort_p"].map(format_p)
    return out[
        [
            "effort_label",
            "formula",
            "r2",
            "rmse",
            "age_coef",
            "age_ci_low",
            "age_ci_high",
            "age_p",
            "effort_coef",
            "effort_p",
        ]
    ]


def expanded_family_sections(expanded_summary: pd.DataFrame, *, approach_id: str) -> str:
    """Return Markdown subsections for each model-family version."""

    sub = expanded_summary[expanded_summary["approach_id"].eq(approach_id)].copy()
    if sub.empty:
        return "_No expanded model-family rows._"
    sections: list[str] = []
    family_order = sub[["model_family_id", "model_family_label", "readable_formula", "effect_scale"]].drop_duplicates()
    for _, family in family_order.iterrows():
        family_id = str(family["model_family_id"])
        family_rows = sub[sub["model_family_id"].eq(family_id)].copy()
        shown_cols = [
            "effort_label",
            "effect_scale",
            "status",
            "fitted_value_note",
            "r2_observed_fitted",
            "rmse",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
        ]
        if approach_id == "M3":
            shown_cols.extend(["age_effort_coef", "age_effort_p"])
        shown = family_rows[shown_cols].copy()
        shown["age_p"] = shown["age_p"].map(format_p)
        shown["effort_p"] = shown["effort_p"].map(format_p)
        if "age_effort_p" in shown.columns:
            shown["age_effort_p"] = shown["age_effort_p"].map(format_p)
        stem = expanded_plot_stem(approach_id, family_id)
        interaction_plot = ""
        if approach_id == "M3":
            interaction_stem = m3_interaction_plot_stem(family_id)
            interaction_plot = (
                f"\n![M3 {family['model_family_label']} low median high effort lines]"
                f"(../figs/m1_m2_utterance_information_deep_dive/{interaction_stem}.png)\n"
            )
        sections.append(
            f"""### Subvariant: {family['model_family_label']}

Formula:

```text
{family['readable_formula']}
```

Effect scale: `{family['effect_scale']}`

{model_family_explanation(approach_id=approach_id, model_family_id=family_id, effect_scale=str(family['effect_scale']))}

{write_markdown_table(shown, max_rows=20)}

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![{approach_id} {family['model_family_label']} adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/{stem}.png)
{interaction_plot}
"""
        )
    return "\n".join(sections)


def m4_subvariant_sections(m4_summary: pd.DataFrame) -> str:
    """Return Markdown subsections for each M4 context-entropy subvariant."""

    if m4_summary.empty:
        return "_No M4 rows._"
    sections: list[str] = []
    order = [spec["model_id"] for spec in M4_MODEL_SPECS]
    for model_id in order:
        rows = m4_summary[m4_summary["model_id"].eq(model_id)].copy()
        if rows.empty:
            continue
        first = rows.iloc[0]
        shown = rows[
            [
                "effort_label",
                "effect_scale",
                "status",
                "r2_observed_fitted",
                "age_coef",
                "age_p",
                "effort_coef",
                "effort_p",
                "entropy_coef",
                "entropy_p",
                "age_entropy_coef",
                "age_entropy_p",
                "age_effort_coef",
                "age_effort_p",
            ]
        ].copy()
        for col in ["age_p", "effort_p", "entropy_p", "age_entropy_p", "age_effort_p"]:
            shown[col] = shown[col].map(format_p)
        stem = f"m4_{str(model_id).lower()}_context_entropy_adjusted_predictions"
        sections.append(
            f"""### Subvariant: {first['model_label']}

Question asked: {first['question']}

Formula:

```text
{first['formula']}
```

How to read it: each row repeats this subvariant for one effort unit. The
`entropy_coef` column is the estimated change in total bits for a one-bit
increase in context entropy after the listed controls. Interaction columns are
empty unless that subvariant includes the corresponding interaction.

{write_markdown_table(shown, max_rows=20)}

Diagnostic view of this subvariant: each panel holds the effort unit at a
single median reference and draws low, median, and high context-entropy
reference lines. This is a plot of the fitted subvariant, not a separate model.

![{first['model_label']} adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/{stem}.png)
"""
        )
    return "\n".join(sections)


def saturated_subvariant_sections(saturated_summary: pd.DataFrame, *, model_id: str) -> str:
    """Return Markdown subsections for one M5/M6 model by effort source."""

    sub = saturated_summary[saturated_summary["model_id"].eq(model_id)].copy()
    if sub.empty:
        return "_No rows._"
    sections: list[str] = []
    for effort_label, rows in sub.groupby("effort_label", sort=False, observed=True):
        first = rows.iloc[0]
        shown = rows[
            [
                "effort_label",
                "effect_scale",
                "status",
                "r2_observed_fitted",
                "age_coef",
                "age_p",
                "context_entropy_coef",
                "context_entropy_p",
            ]
        ].copy()
        shown["age_p"] = shown["age_p"].map(format_p)
        shown["context_entropy_p"] = shown["context_entropy_p"].map(format_p)
        sections.append(
            f"""### Subvariant: {model_id} with effort levels from {effort_label}

Question asked: {first['question']}

Formula:

```text
{first['formula']}
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `{effort_label}` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

{write_markdown_table(shown, max_rows=5)}
"""
        )
    return "\n".join(sections)


def write_report(
    *,
    md_path: Path,
    html_path: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    audit: Mapping[str, pd.DataFrame],
    fit_summary: pd.DataFrame,
    coef_summary: pd.DataFrame,
    importance: pd.DataFrame,
    vif: pd.DataFrame,
    expanded_summary: pd.DataFrame,
    m4_summary: pd.DataFrame,
    m4_coefs: pd.DataFrame,
    m4_frame: pd.DataFrame,
    saturated_summary: pd.DataFrame,
    saturated_coefs: pd.DataFrame,
    saturated_frame: pd.DataFrame,
    context_overview_override: pd.DataFrame | None = None,
) -> None:
    """Write the M1-M6 internal review packet."""

    m1_versions = model_version_table(fit_summary, coef_summary, model_id="M1")
    m2_versions = model_version_table(fit_summary, coef_summary, model_id="M2")

    def primary_table(approach_id: str, model_family_id: str, *, interaction: bool = False) -> pd.DataFrame:
        cols = [
            "effort_label",
            "model_family_label",
            "effect_scale",
            "status",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
        ]
        if interaction:
            cols.extend(["age_effort_coef", "age_effort_p"])
        out = expanded_summary[
            expanded_summary["approach_id"].eq(approach_id)
            & expanded_summary["model_family_id"].eq(model_family_id)
        ][cols].copy()
        for col in ["age_p", "effort_p", "age_effort_p"]:
            if col in out.columns:
                out[col] = out[col].map(format_p)
        return out

    def sensitivity_table(approach_id: str, value_col: str) -> pd.DataFrame:
        sub = expanded_summary[expanded_summary["approach_id"].eq(approach_id)].copy()
        if sub.empty:
            return sub
        out = sub.groupby(["model_family_label", "effect_scale", "status"], observed=True).agg(
            median_r2=("r2_observed_fitted", "median"),
            median_value=(value_col, "median"),
            fit_rows=("effort_label", "count"),
        ).reset_index()
        return out.sort_values(["status", "median_r2"], ascending=[True, False])

    def coefficient_takeaway(rows: pd.DataFrame, coef_col: str, p_col: str, label: str) -> str:
        if rows.empty or coef_col not in rows.columns:
            return "No fitted rows were available for this model."
        valid = rows.copy()
        valid[coef_col] = pd.to_numeric(valid[coef_col], errors="coerce")
        if p_col in valid.columns:
            valid[p_col] = pd.to_numeric(valid[p_col].astype(str).replace({"<.001": "0.0005", "": np.nan}), errors="coerce")
        else:
            valid[p_col] = np.nan
        valid = valid.dropna(subset=[coef_col])
        if valid.empty:
            return "The fitted rows did not expose the coefficient needed for this takeaway."
        neg = int((valid[coef_col] < 0).sum())
        pos = int((valid[coef_col] > 0).sum())
        sig = int((valid[p_col] < 0.05).sum()) if p_col in valid.columns else 0
        direction = "mostly negative" if neg > pos else "mostly positive" if pos > neg else "mixed"
        return f"Primary result: the {label} coefficient is {direction} across effort versions ({neg} negative, {pos} positive; {sig}/{len(valid)} p<.05)."

    m1_primary = primary_table("M1", "ols_cluster")
    m2_primary = primary_table("M2", "ols_child_fe")
    m3_primary = primary_table("M3", "ols_child_fe_interaction", interaction=True)
    m1_sensitivity = sensitivity_table("M1", "age_coef")
    m2_sensitivity = sensitivity_table("M2", "age_coef")
    m3_sensitivity = sensitivity_table("M3", "age_effort_coef")
    m1_takeaway = coefficient_takeaway(m1_primary, "age_coef", "age_p", "age")
    m2_takeaway = coefficient_takeaway(m2_primary, "age_coef", "age_p", "age")
    m3_takeaway = coefficient_takeaway(m3_primary, "age_effort_coef", "age_effort_p", "age-by-effort interaction")

    important_short = (
        importance.sort_values(["model_id", "effort_label", "delta_r2_when_dropped"], ascending=[True, True, False])
        [["model_id", "effort_label", "importance_term", "delta_r2_when_dropped"]]
        .groupby(["model_id", "effort_label"], as_index=False, observed=True)
        .head(1)
    )
    m3_interaction_short = expanded_summary[
        expanded_summary["approach_id"].eq("M3")
        & expanded_summary["model_family_id"].isin(["ols_cluster_interaction", "ols_child_fe_interaction", "gee_gaussian_interaction"])
    ][
        [
            "model_family_label",
            "effort_label",
            "effect_scale",
            "r2_observed_fitted",
            "age_coef",
            "effort_coef",
            "age_effort_coef",
            "age_effort_p",
        ]
    ].copy()
    m3_interaction_short["age_effort_p"] = m3_interaction_short["age_effort_p"].map(format_p)
    version_comparison = m1_versions[["effort_label", "age_coef", "r2"]].rename(columns={"age_coef": "m1_age_coef", "r2": "m1_r2"}).merge(
        m2_versions[["effort_label", "age_coef", "r2"]].rename(columns={"age_coef": "m2_age_coef", "r2": "m2_r2"}),
        on="effort_label",
    )
    version_comparison["age_effect_change"] = version_comparison.apply(
        lambda row: "same sign" if np.sign(row["m1_age_coef"]) == np.sign(row["m2_age_coef"]) else "changes sign",
        axis=1,
    )
    notation = pd.DataFrame(
        [
            {
                "notation": "`effort`",
                "meaning": "One effort measure at a time: words, morphemes, syllables, or phonemes.",
                "fit_here": "yes",
            },
            {
                "notation": "`age * effort`",
                "meaning": "Shortcut for `age + effort + age:effort`.",
                "fit_here": "yes, M3",
            },
            {
                "notation": "`C(child_id)`",
                "meaning": "Child fixed intercepts. Each child gets their own baseline level of total bits; the age slope is still shared.",
                "fit_here": "yes, M2/M3",
            },
            {
                "notation": "`age:C(child_id)`",
                "meaning": "Child-specific fixed age slopes. Each child can have a different developmental slope.",
                "fit_here": "yes, one M2 and one M3 version",
            },
            {
                "notation": "`age:effort`",
                "meaning": "Age-by-effort interaction. Tests whether the effort-to-information relation changes with development.",
                "fit_here": "yes, M3",
            },
            {
                "notation": "`context_entropy_bits`",
                "meaning": "Mistral next-token entropy after the preceding caretaker context. Higher values mean the model is less certain about the next token.",
                "fit_here": "yes, M4",
            },
            {
                "notation": "`context_entropy_c`",
                "meaning": "Mean-centered context entropy. A one-unit increase is a one-bit increase relative to the sample mean.",
                "fit_here": "yes, M4",
            },
            {
                "notation": "`age:context_entropy`",
                "meaning": "Interaction testing whether the context-entropy effect changes over development.",
                "fit_here": "yes, M4",
            },
            {
                "notation": "`(1 | child_id)`",
                "meaning": "Mixed-model random intercept. Like child baselines, but estimated as a distribution rather than one dummy coefficient per child.",
                "fit_here": "yes, M2/M3 sensitivity",
            },
            {
                "notation": "`(age | child_id)`",
                "meaning": "Mixed-model random intercept plus random age slope. Children can differ in baseline and developmental slope.",
                "fit_here": "yes, M2/M3 sensitivity",
            },
        ]
    )
    model_vocabulary = pd.DataFrame(
        [
            {
                "term": "OLS",
                "meaning": "Ordinary linear regression. Coefficients are additive changes in total bits.",
            },
            {
                "term": "child-clustered SE",
                "meaning": "Same fitted OLS line, but standard errors and p-values allow utterances from the same child to be correlated.",
            },
            {
                "term": "GLM",
                "meaning": "Generalized linear model. It changes the outcome distribution/link, not the basic set of predictors.",
            },
            {
                "term": "Gaussian GLM",
                "meaning": "A GLM version of linear regression for a continuous outcome; predictions are on the bits scale.",
            },
            {
                "term": "Gamma/log link",
                "meaning": "Sensitivity model for positive continuous `sum_bits`; coefficients are on log expected bits, so predictions are easier to interpret than raw coefficients.",
            },
            {
                "term": "GEE",
                "meaning": "Population-average model that clusters observations by child and estimates robust uncertainty for repeated utterances.",
            },
            {
                "term": "mixed model",
                "meaning": "Model with child-level random effects. Here it tests whether conclusions survive explicit child-level dependence structure.",
            },
            {
                "term": "fixed at median effort",
                "meaning": "For prediction plots only: age varies, while utterance effort is set to the sample median so the line compares same-sized utterances. It does not refit or alter the model coefficients.",
            },
            {
                "term": "context entropy",
                "meaning": "A context-predictability measure. Here it is next-token entropy in bits, not sampled full-response entropy.",
            },
        ]
    )
    m4_show = m4_summary[
        [
            "model_id",
            "model_label",
            "effort_label",
            "outcome",
            "fit_type",
            "effect_scale",
            "status",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
            "entropy_coef",
            "entropy_p",
            "age_entropy_coef",
            "age_entropy_p",
            "age_effort_coef",
            "age_effort_p",
        ]
    ].copy() if not m4_summary.empty else pd.DataFrame()
    for col in ["age_p", "effort_p", "entropy_p", "age_entropy_p", "age_effort_p"]:
        if col in m4_show.columns:
            m4_show[col] = m4_show[col].map(format_p)
    m4_primary_show = m4_show[m4_show["model_id"].eq("M4a")].copy() if not m4_show.empty else pd.DataFrame()
    m4_key_coefs = m4_coefs[
        m4_coefs["term"].isin(["context_entropy_c", "age_c:context_entropy_c", "age_c", "effort_c", "age_c:effort_c"])
    ].copy() if not m4_coefs.empty else pd.DataFrame()
    if not m4_key_coefs.empty:
        m4_key_coefs["p_value"] = m4_key_coefs["p_value"].map(format_p)
    context_overview = (
        context_overview_override.copy()
        if context_overview_override is not None and not context_overview_override.empty
        else m4_context_overview(m4_frame)
    )
    saturated_show = saturated_summary[
        [
            "model_id",
            "model_label",
            "effort_label",
            "formula",
            "fit_type",
            "effect_scale",
            "status",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "context_entropy_coef",
            "context_entropy_p",
        ]
    ].copy() if not saturated_summary.empty else pd.DataFrame()
    for col in ["age_p", "context_entropy_p"]:
        if col in saturated_show.columns:
            saturated_show[col] = saturated_show[col].map(format_p)
    m5_show = saturated_show[saturated_show["model_id"].eq("M5")].copy() if not saturated_show.empty else pd.DataFrame()
    m6_show = saturated_show[saturated_show["model_id"].eq("M6")].copy() if not saturated_show.empty else pd.DataFrame()
    saturated_key_terms = [
        "age_c",
        "context_entropy_c",
        "age_c:context_entropy_c",
        "C(effort_level)[T.mid effort]",
        "C(effort_level)[T.high effort]",
        "age_c:C(effort_level)[T.mid effort]",
        "age_c:C(effort_level)[T.high effort]",
        "context_entropy_c:C(effort_level)[T.mid effort]",
        "context_entropy_c:C(effort_level)[T.high effort]",
    ]
    saturated_key_coefs = saturated_coefs[saturated_coefs["term"].isin(saturated_key_terms)].copy() if not saturated_coefs.empty else pd.DataFrame()
    if not saturated_key_coefs.empty:
        saturated_key_coefs["p_value"] = saturated_key_coefs["p_value"].map(format_p)
    m5_key_coefs = saturated_key_coefs[saturated_key_coefs["model_id"].eq("M5")].copy() if not saturated_key_coefs.empty else pd.DataFrame()
    m6_key_coefs = saturated_key_coefs[saturated_key_coefs["model_id"].eq("M6")].copy() if not saturated_key_coefs.empty else pd.DataFrame()
    m1_subvariant_sections = expanded_family_sections(expanded_summary, approach_id="M1")
    m2_subvariant_sections = expanded_family_sections(expanded_summary, approach_id="M2")
    m3_subvariant_sections = expanded_family_sections(expanded_summary, approach_id="M3")
    m4_subvariant_sections_text = m4_subvariant_sections(m4_summary)
    m5_subvariant_sections_text = saturated_subvariant_sections(saturated_summary, model_id="M5")
    m6_subvariant_sections_text = saturated_subvariant_sections(saturated_summary, model_id="M6")

    md = f"""# Internal Review: Utterance Information Models M1-M6

This is an internal modeling packet for utterance-level total information. It
does not edit the supervisor-facing report. The analysis stage fits the models
and writes CSV/PNG artifacts; the report stage only reads those artifacts.

Outcome throughout:

```text
sum_bits
```

Core rule: effort measures are not combined as continuous predictors in the
same regression. When effort is continuous, each model is repeated separately
for words, morphemes, CMU/pkg syllables, package syllables, and phonemes. When
effort is categorical, low/mid/high effort is created separately from one
effort unit at a time.

## Shared Reading Rules

Table columns used below:

- `effort_label`: which effort unit defines the model version.
- `effect_scale`: whether coefficients are additive bits or log expected bits.
- `r2_observed_fitted`: squared correspondence between observed and fitted total bits; higher means better in-sample fit.
- `age_coef`: expected change in total bits for one additional month, after the listed controls.
- `age_p`: p-value for `age_coef`.
- `effort_coef`: expected change in total bits for one additional effort unit, when effort is continuous.
- `effort_p`: p-value for `effort_coef`.
- `entropy_coef`: expected change in total bits for one additional bit of context entropy.
- `entropy_p`: p-value for `entropy_coef`.
- `age_effort_coef`: interaction term; whether the effort slope changes with age.

Plot rules:

- Raw grey age-bin means are descriptive and not controlled.
- Regression lines are controlled predictions.
- "Effort fixed at median" is only a plotting reference value. The fitted model still uses all observed utterances and all observed effort values.
- `C(child_id)` means child fixed intercepts: each child has its own baseline, but the displayed age slope is shared unless the formula explicitly includes child-specific age slopes.
- In subvariant line plots, the solid line is the fitted mean prediction and
  the shaded band is the model-based 95% confidence interval when statsmodels
  exposes one for that estimator. For OLS versus child-clustered OLS, the mean
  line is expected to be identical; only the uncertainty and p-values change.
- A **subvariant** is a real model change: different formula, estimator, link,
  child-dependence structure, or effort source.
- A **diagnostic view** is not a new model. It is the same fitted subvariant
  plotted with different reference values, such as median effort versus
  low/median/high effort lines.

## Why We Separate Effort Units

Words, morphemes, syllables, and phonemes are different effort proxies, but
they are highly correlated. Putting all of them into one continuous model makes
individual coefficients unstable and hard to interpret. This packet therefore
uses a repeated-model strategy rather than a single overloaded formula.

How to read the heatmap: values close to 1 mean two predictors move together.
That is exactly why the effort variables are not used simultaneously as
continuous covariates.

![Predictor correlations](../figs/m1_m2_utterance_information_deep_dive/predictor_correlation_heatmap.png)

## Model 1: Pooled Age + Continuous Effort

Formula:

```text
sum_bits ~ age + effort
```

Question: pooling all children together, does age predict total information
after controlling for utterance effort?

This is the weakest developmental model because it does not control stable
differences between children. It is useful as a baseline for seeing what goes
wrong when child identity is ignored.

### Model 1 Subvariants

Each subsection below is a real M1 subvariant because the estimator or
uncertainty model changes. The effort unit is still repeated separately inside
each subvariant.

{m1_subvariant_sections}

### Model 1 Diagnostic Views

How to read the plot: each line is a same-effort developmental trajectory for
one effort unit. The line changes age while holding that effort unit at its
median value for plotting.

![M1 adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png)

Companion view: this plot uses the same M1 formula but draws three reference
lines for each effort unit: low, median, and high effort. The shaded ribbons
show observed age-bin mean +/- standard error for the corresponding
low/mid/high effort group. These ribbons describe the data support around the
line; they are not formal model-confidence intervals.

![M1 low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m1_low_mid_high_effort_adjusted_age_predictions.png)

Table columns for M1: `formula` shows the fitted equation; `r2` is ordinary OLS
fit; `rmse` is prediction error in bits; `age_coef`/`age_p` are the age effect;
`effort_coef`/`effort_p` are the effort effect.

{write_markdown_table(m1_primary, max_rows=8)}

Takeaway: {m1_takeaway}

## Model 2: Age + Continuous Effort + Child Identity

Formula:

```text
sum_bits ~ age + effort + C(child_id)
```

Question: after controlling each child's stable baseline, does age predict
total information at the same utterance-effort level?

This is the cleaner version of M1 for developmental interpretation. It compares
age effects after removing stable between-child differences.

### Model 2 Subvariants

Each subsection below is a real M2 subvariant because the child-dependence
structure changes: fixed child intercepts, child-specific age slopes, GEE, or
mixed-effects formulations.

{m2_subvariant_sections}

### Model 2 Diagnostic Views

How to read the plot: effort is fixed for plotting as in M1, but predictions
also average over the fitted child baselines. A difference between M1 and M2
means the pooled trend was partly driven by which children appear at which
ages.

![M2 adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png)

Companion view: this is the same child-adjusted model, but with low, median,
and high continuous-effort reference lines. The shaded ribbons again show
observed age-bin mean +/- standard error for the matching low/mid/high effort
group.

![M2 low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m2_low_mid_high_effort_adjusted_age_predictions.png)

Table columns for M2 are the same as M1. The key difference is that the formula
contains `C(child_id)`, so `age_coef` is child-adjusted.

{write_markdown_table(m2_primary, max_rows=8)}

Takeaway: {m2_takeaway}

## Model 3: Age by Continuous Effort

Formula:

```text
sum_bits ~ age * effort + C(child_id)
```

Question: does the effort-information relation change with age?

The interaction `age:effort` asks whether one additional unit of effort carries
the same information consequence at different ages. This still keeps effort
units separate: one model for words, one for morphemes, one for each syllable
estimate, and one for phonemes.

### Model 3 Subvariants

Each subsection below is a real M3 subvariant because the estimator, child
structure, or link function changes while preserving the age-by-effort
scientific question.

{m3_subvariant_sections}

### Model 3 Diagnostic Views

How to read the plot: each panel is one effort unit. The three lines are low,
median, and high effort values for that unit. Non-parallel lines mean the age
trajectory differs by effort level.

![M3 child-adjusted interaction lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)

Companion view: this keeps effort at a single median reference value, so it is
closer to the M1/M2 line-plot style. Use it to check whether the low/mid/high
split is creating a visual impression that is not visible in the central
reference trajectory.

![M3 median effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png)

Table columns for M3 add `age_effort_coef` and `age_effort_p`. A negative
interaction means the additional bits associated with effort are smaller at
older ages than at younger ages.

{write_markdown_table(m3_primary, max_rows=8)}

Takeaway: {m3_takeaway}

## Model 4: Context Entropy Predicting Total Information

Primary formula:

```text
sum_bits ~ age + effort + context_entropy + C(child_id)
```

Question: does context entropy predict total utterance information after age,
effort, and child identity are controlled?

Here `context_entropy_bits` is Mistral next-token entropy after the preceding
caretaker context. It is measured in bits. Higher values mean the model is less
certain about the next token. This is a provisional context-predictability
measure, not sampled full-response entropy.

Context coverage summary:

{write_markdown_table(context_overview)}

### Model 4 Subvariants

Each subsection below is a real M4 subvariant because the context-entropy model
changes its estimator or formula. The diagnostic plots are shown separately for
M4a-M4e so the context-entropy alternatives are not hidden in one table.

{m4_subvariant_sections_text}

### Model 4 Diagnostic Views

How to read the descriptive plot: it shows raw trends by context entropy and
age stage. It is not the controlled model; it is a sanity check.

![M4 descriptive bins](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png)

How to read the adjusted plot: each panel is one effort unit. The three lines
show low, median, and high context entropy while effort and child identity are
controlled.

![M4 adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png)

Companion view: this holds context entropy at its median and varies continuous
effort instead. It checks whether M4's age trend is being driven by context
entropy references or by the effort reference.

![M4 effort-varied predictions](../figs/m1_m2_utterance_information_deep_dive/m4_effort_quantile_adjusted_predictions.png)

Table columns for M4 add `entropy_coef`/`entropy_p`. The table below shows only
the primary child-fixed-effect M4 version so the section stays readable.

{write_markdown_table(m4_primary_show, max_rows=8)}

## Model 5: Context Entropy + Low/Mid/High Effort Identity

Formula:

```text
sum_bits ~ age + context_entropy + C(effort_level) + C(child_id)
```

Question: does context entropy predict total information after we control child
identity and represent effort as a low/mid/high category rather than a
continuous count?

This model answers your effort-identity idea. The low/mid/high categories are
tertiles computed separately for each effort unit, so the words version uses
word-count tertiles, the phoneme version uses phoneme-count tertiles, and so
on.

### Model 5 Subvariants

Each subsection below is a real M5 subvariant because low/mid/high effort
identity is defined from a different effort unit. The low/mid/high split is
therefore one categorical effort strategy, not the only view of M5.

{m5_subvariant_sections_text}

### Model 5 Diagnostic Views

How to read the plot: each panel is one effort unit used to define low/mid/high
effort. Lines compare predicted total bits across age for those effort
categories, with context entropy set to its mean for plotting.

![M5 effort-level lines](../figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png)

Companion view: this averages over the low/mid/high effort levels instead of
splitting the plot by them. Use it to check whether the visible age trend is
specific to the tertile split or remains when the effort-level categories are
averaged over.

![M5 and M6 averaged effort-level lines](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png)

Table columns for M5: `effort_label` says which unit created the effort
tertiles; `age_coef` is the age effect; `context_entropy_coef` is the entropy
effect after effort category and child identity are controlled.

{write_markdown_table(m5_show, max_rows=8)}

## Model 6: Age, Context, and Effort-Level Interactions

Formula:

```text
sum_bits ~ age * context_entropy
         + age * C(effort_level)
         + context_entropy * C(effort_level)
         + C(child_id)
```

Question: do developmental trajectories differ by both context entropy and
low/mid/high effort level?

This is the more exploratory version of M5. It is intentionally flexible, but
still does not put all continuous effort measures into one model.

### Model 6 Subvariants

Each subsection below is a real M6 subvariant because low/mid/high effort
identity is defined from a different effort unit before interactions are fit.

{m6_subvariant_sections_text}

### Model 6 Diagnostic Views

How to read the plot: each panel is one effort unit. If the low/mid/high lines
separate or change slope differently over age, then the model is finding
evidence that developmental information trajectories differ by effort category.

![M6 effort-level interaction lines](../figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png)

Companion view: the averaged effort-level plot above also includes M6. This is
important because low/mid/high effort categories are only one discretization of
effort, so they should not be the sole basis for interpreting M6.

Table columns for M6 are the same as M5, but the formula includes interactions.
The compact table emphasizes the main age and context-entropy terms; the
interaction coefficients are in the coefficient CSV.

{write_markdown_table(m6_show, max_rows=8)}

How to read the coefficient heatmap: rows are selected M5/M6 terms and columns
are the effort units used to create low/mid/high categories. Red/blue direction
shows whether each coefficient is positive or negative.

![M5/M6 selected coefficients](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png)

## M1 vs M2 Sign Reversal

The important comparison is conceptual, not just numerical. M1 pools all
children. M2 controls child identity. If the age coefficient changes sign from
M1 to M2, the pooled age trend was mixing developmental change with which
children contributed data at which ages.

How to read the plot: the same effort units are shown for both models. M2 is
the child-adjusted version; M1 is the pooled version.

![Adjusted trajectories](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)

## Analysis Artifacts

The full sensitivity outputs remain available as CSV/PNG files. They are not
all printed in the report because the report is meant to be readable.

- M1/M2 core fits: `{output_dir / "model_fit_summary.csv"}`
- M1/M2 coefficients: `{output_dir / "model_coefficients.csv"}`
- M3 and sensitivity families: `{output_dir / "expanded_model_family_summary.csv"}`
- M4 context models: `{output_dir / "m4_context_entropy_model_summary.csv"}`
- M5/M6 effort-level models: `{output_dir / "m5_m6_saturated_model_summary.csv"}`
- M5/M6 coefficients: `{output_dir / "m5_m6_saturated_coefficients.csv"}`
- Predictions: `{output_dir / "adjusted_age_predictions.csv"}`
- Context predictions: `{output_dir / "m4_context_entropy_adjusted_predictions.csv"}`
- Effort-level predictions: `{output_dir / "m5_m6_saturated_adjusted_age_predictions.csv"}`

## Data Audit

Rows used in this report:

{write_markdown_table(audit["overview"])}

Rows by age bin:

{write_markdown_table(audit["by_age_bin"], max_rows=20)}
"""
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    """Read a CSV if present; return an empty frame otherwise."""

    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def m4_context_overview(m4_frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize context-entropy coverage for report rendering."""

    return pd.DataFrame(
        [
            {
                "rows_with_context_entropy": len(m4_frame),
                "unique_utterance_rows_with_context_entropy": m4_frame["score_id"].nunique() if not m4_frame.empty and "score_id" in m4_frame.columns else 0,
                "children": m4_frame["child_id"].nunique() if not m4_frame.empty else 0,
                "mean_context_entropy_bits": m4_frame["context_entropy_bits"].mean() if not m4_frame.empty and "context_entropy_bits" in m4_frame.columns else math.nan,
                "median_context_entropy_bits": m4_frame["context_entropy_bits"].median() if not m4_frame.empty and "context_entropy_bits" in m4_frame.columns else math.nan,
            }
        ]
    )


def run_packet_analysis(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    chunksize: int,
) -> Mapping[str, Path]:
    """Run expensive M1-M6 analyses and write tables/figures."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_modeling_rows(input_csv, context_k=context_k, chunksize=chunksize)
    audit_sample = frame.sample(n=min(5000, len(frame)), random_state=SEED).sort_values(["dataset", "child_id", "age_months"])
    audit_sample.to_csv(output_dir / "modeling_rows_audit_sample.csv", index=False)
    audit = audit_tables(frame, output_dir)
    bundles = fit_all_models(frame)
    fit_summary = model_fit_rows(bundles)
    coef_summary = coefficient_rows(bundles, frame)
    importance = variable_importance_rows(frame)
    predictions = pd.concat([prediction_grid_for_bundle(bundle, frame) for bundle in bundles], ignore_index=True)
    effort_quantile_predictions = plot_m1_m2_low_mid_high_effort_lines(bundles, frame, fig_dir)
    expanded_bundles = fit_expanded_models(frame)
    expanded_summary = expanded_fit_summary_rows(expanded_bundles)
    m4_bundles, m4_frame = fit_m4_models(frame)
    m4_summary = m4_summary_rows(m4_bundles)
    m4_coefs = m4_coefficient_rows(m4_bundles)
    saturated_bundles, saturated_frame = fit_saturated_models(frame)
    saturated_summary = saturated_summary_rows(saturated_bundles)
    saturated_coefs = saturated_coefficient_rows(saturated_bundles)

    fit_summary.to_csv(output_dir / "model_fit_summary.csv", index=False)
    coef_summary.to_csv(output_dir / "model_coefficients.csv", index=False)
    importance.to_csv(output_dir / "variable_importance_delta_r2.csv", index=False)
    predictions.to_csv(output_dir / "adjusted_age_predictions.csv", index=False)
    effort_quantile_predictions.to_csv(output_dir / "m1_m2_low_mid_high_effort_adjusted_age_predictions.csv", index=False)
    expanded_summary.to_csv(output_dir / "expanded_model_family_summary.csv", index=False)
    m4_summary.to_csv(output_dir / "m4_context_entropy_model_summary.csv", index=False)
    m4_coefs.to_csv(output_dir / "m4_context_entropy_coefficients.csv", index=False)
    m4_context_overview(m4_frame).to_csv(output_dir / "m4_context_entropy_overview.csv", index=False)
    saturated_summary.to_csv(output_dir / "m5_m6_saturated_model_summary.csv", index=False)
    saturated_coefs.to_csv(output_dir / "m5_m6_saturated_coefficients.csv", index=False)
    if not m4_frame.empty:
        m4_frame.sample(n=min(5000, len(m4_frame)), random_state=SEED).to_csv(
            output_dir / "m4_context_entropy_rows_audit_sample.csv",
            index=False,
        )
    if not saturated_frame.empty:
        saturated_frame.sample(n=min(5000, len(saturated_frame)), random_state=SEED).to_csv(
            output_dir / "m5_m6_saturated_rows_audit_sample.csv",
            index=False,
        )
    audit["vif"].to_csv(output_dir / "vif_diagnostic.csv", index=False)

    plot_predictor_correlation(frame, fig_dir)
    plot_coefficients(
        coef_summary,
        fig_dir,
        term="age_months",
        filename="m1_m2_age_coefficients_by_effort",
        ylabel="Age coefficient: bits per month",
        title="Age Effect After Controlling Utterance Size",
    )
    plot_coefficients(
        coef_summary,
        fig_dir,
        term="effort_value",
        filename="m1_m2_effort_coefficients_by_measure",
        ylabel="Effort coefficient: bits per unit",
        title="Effort Effect After Controlling Age",
    )
    plot_adjusted_age_predictions(predictions, frame, fig_dir)
    plot_variable_importance(importance, fig_dir)
    plot_residual_diagnostics(bundles, frame, fig_dir)
    plot_model_specific_coefficients(coef_summary, fig_dir, model_id="M1")
    plot_model_specific_coefficients(coef_summary, fig_dir, model_id="M2")
    expanded_predictions = plot_expanded_regression_lines(expanded_bundles, frame, fig_dir)
    expanded_predictions.to_csv(output_dir / "expanded_adjusted_age_predictions.csv", index=False)
    m3_interaction_predictions = plot_m3_interaction_regression_lines(expanded_bundles, frame, fig_dir)
    m3_interaction_predictions.to_csv(output_dir / "m3_interaction_adjusted_age_predictions.csv", index=False)
    plot_m4_context_entropy_bins(m4_frame, fig_dir)
    m4_predictions = plot_m4_adjusted_predictions(m4_bundles, m4_frame, fig_dir)
    m4_predictions.to_csv(output_dir / "m4_context_entropy_adjusted_predictions.csv", index=False)
    m4_effort_predictions = plot_m4_effort_quantile_predictions(m4_bundles, m4_frame, fig_dir)
    m4_effort_predictions.to_csv(output_dir / "m4_effort_quantile_adjusted_predictions.csv", index=False)
    plot_m4_coefficients(m4_summary, fig_dir)
    saturated_predictions = plot_saturated_predictions(saturated_bundles, saturated_frame, fig_dir)
    saturated_predictions.to_csv(output_dir / "m5_m6_saturated_adjusted_age_predictions.csv", index=False)
    saturated_average_predictions = plot_saturated_average_predictions(saturated_bundles, saturated_frame, fig_dir)
    saturated_average_predictions.to_csv(output_dir / "m5_m6_effort_level_average_age_predictions.csv", index=False)
    plot_saturated_coefficients(saturated_coefs, fig_dir)
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M1",
        value_col="age_coef",
        filename="m1_expanded_age_coefficients",
        title="M1 Age Coefficients Across Model Families",
        cbar_label="Age coefficient",
        center_zero=True,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M2",
        value_col="age_coef",
        filename="m2_expanded_age_coefficients",
        title="M2 Age Coefficients Across Model Families",
        cbar_label="Age coefficient",
        center_zero=True,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M1",
        value_col="r2_observed_fitted",
        filename="m1_expanded_r2",
        title="M1 Observed-vs-Fitted R2 Across Model Families",
        cbar_label="Observed-vs-fitted R2",
        center_zero=False,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M2",
        value_col="r2_observed_fitted",
        filename="m2_expanded_r2",
        title="M2 Observed-vs-Fitted R2 Across Model Families",
        cbar_label="Observed-vs-fitted R2",
        center_zero=False,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M3",
        value_col="age_effort_coef",
        filename="m3_expanded_interaction_coefficients",
        title="M3 Age-by-Effort Coefficients Across Model Families",
        cbar_label="Age-by-effort coefficient",
        center_zero=True,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M3",
        value_col="r2_observed_fitted",
        filename="m3_expanded_r2",
        title="M3 Observed-vs-Fitted R2 Across Model Families",
        cbar_label="Observed-vs-fitted R2",
        center_zero=False,
    )
    return {"output_dir": output_dir, "fig_dir": fig_dir}


def run_m5_m6_analysis(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    chunksize: int,
) -> Mapping[str, Path]:
    """Refit only the M5/M6 effort-level models and their plots."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_modeling_rows(input_csv, context_k=context_k, chunksize=chunksize)
    saturated_bundles, saturated_frame = fit_saturated_models(frame)
    saturated_summary = saturated_summary_rows(saturated_bundles)
    saturated_coefs = saturated_coefficient_rows(saturated_bundles)
    saturated_summary.to_csv(output_dir / "m5_m6_saturated_model_summary.csv", index=False)
    saturated_coefs.to_csv(output_dir / "m5_m6_saturated_coefficients.csv", index=False)
    if not saturated_frame.empty:
        saturated_frame.sample(n=min(5000, len(saturated_frame)), random_state=SEED).to_csv(
            output_dir / "m5_m6_saturated_rows_audit_sample.csv",
            index=False,
        )
    saturated_predictions = plot_saturated_predictions(saturated_bundles, saturated_frame, fig_dir)
    saturated_predictions.to_csv(output_dir / "m5_m6_saturated_adjusted_age_predictions.csv", index=False)
    saturated_average_predictions = plot_saturated_average_predictions(saturated_bundles, saturated_frame, fig_dir)
    saturated_average_predictions.to_csv(output_dir / "m5_m6_effort_level_average_age_predictions.csv", index=False)
    plot_saturated_coefficients(saturated_coefs, fig_dir)
    return {"output_dir": output_dir, "fig_dir": fig_dir}


def run_line_variant_analysis(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    chunksize: int,
) -> Mapping[str, Path]:
    """Refit only models needed for alternate regression-line views."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_modeling_rows(input_csv, context_k=context_k, chunksize=chunksize)
    bundles = fit_all_models(frame)
    effort_quantile_predictions = plot_m1_m2_low_mid_high_effort_lines(bundles, frame, fig_dir)
    effort_quantile_predictions.to_csv(output_dir / "m1_m2_low_mid_high_effort_adjusted_age_predictions.csv", index=False)

    m4_bundles, m4_frame = fit_m4_models(frame)
    m4_predictions = plot_m4_adjusted_predictions(m4_bundles, m4_frame, fig_dir)
    m4_predictions.to_csv(output_dir / "m4_context_entropy_adjusted_predictions.csv", index=False)
    m4_effort_predictions = plot_m4_effort_quantile_predictions(m4_bundles, m4_frame, fig_dir)
    m4_effort_predictions.to_csv(output_dir / "m4_effort_quantile_adjusted_predictions.csv", index=False)

    saturated_bundles, saturated_frame = fit_saturated_models(frame)
    saturated_predictions = plot_saturated_predictions(saturated_bundles, saturated_frame, fig_dir)
    saturated_predictions.to_csv(output_dir / "m5_m6_saturated_adjusted_age_predictions.csv", index=False)
    saturated_average_predictions = plot_saturated_average_predictions(saturated_bundles, saturated_frame, fig_dir)
    saturated_average_predictions.to_csv(output_dir / "m5_m6_effort_level_average_age_predictions.csv", index=False)
    plot_saturated_coefficients(saturated_coefficient_rows(saturated_bundles), fig_dir)
    return {"output_dir": output_dir, "fig_dir": fig_dir}


def run_expanded_plot_analysis(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    context_k: str,
    chunksize: int,
) -> Mapping[str, Path]:
    """Refit M1-M3 expanded subvariants and refresh their line plots."""

    sns.set_theme(style="whitegrid", context="talk")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frame = read_modeling_rows(input_csv, context_k=context_k, chunksize=chunksize)
    expanded_bundles = fit_expanded_models(frame)
    expanded_summary = expanded_fit_summary_rows(expanded_bundles)
    expanded_summary.to_csv(output_dir / "expanded_model_family_summary.csv", index=False)
    expanded_predictions = plot_expanded_regression_lines(expanded_bundles, frame, fig_dir)
    expanded_predictions.to_csv(output_dir / "expanded_adjusted_age_predictions.csv", index=False)
    m3_interaction_predictions = plot_m3_interaction_regression_lines(expanded_bundles, frame, fig_dir)
    m3_interaction_predictions.to_csv(output_dir / "m3_interaction_adjusted_age_predictions.csv", index=False)
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M1",
        value_col="age_coef",
        filename="m1_expanded_age_coefficients",
        title="M1 Age Coefficients Across Model Families",
        cbar_label="Age coefficient",
        center_zero=True,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M2",
        value_col="age_coef",
        filename="m2_expanded_age_coefficients",
        title="M2 Age Coefficients Across Model Families",
        cbar_label="Age coefficient",
        center_zero=True,
    )
    plot_expanded_heatmap(
        expanded_summary,
        fig_dir,
        approach_id="M3",
        value_col="age_effort_coef",
        filename="m3_expanded_interaction_coefficients",
        title="M3 Age-by-Effort Coefficients Across Model Families",
        cbar_label="Age-by-effort coefficient",
        center_zero=True,
    )
    return {"output_dir": output_dir, "fig_dir": fig_dir}


def render_packet_report_from_outputs(
    *,
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
    context_k: str,
) -> Mapping[str, Path]:
    """Render the M1-M6 report from existing analysis outputs only."""

    audit = {
        "overview": pd.read_csv(output_dir / "overview.csv"),
        "by_dataset": pd.read_csv(output_dir / "by_dataset.csv"),
        "by_age_bin": pd.read_csv(output_dir / "by_age_bin.csv"),
        "predictor_correlation": pd.read_csv(output_dir / "predictor_correlation.csv"),
        "vif": pd.read_csv(output_dir / "vif_diagnostic.csv"),
    }
    write_report(
        md_path=md_path,
        html_path=html_path,
        output_dir=output_dir,
        fig_dir=fig_dir,
        context_k=context_k,
        audit=audit,
        fit_summary=pd.read_csv(output_dir / "model_fit_summary.csv"),
        coef_summary=pd.read_csv(output_dir / "model_coefficients.csv"),
        importance=pd.read_csv(output_dir / "variable_importance_delta_r2.csv"),
        vif=pd.read_csv(output_dir / "vif_diagnostic.csv"),
        expanded_summary=pd.read_csv(output_dir / "expanded_model_family_summary.csv"),
        m4_summary=read_csv_if_exists(output_dir / "m4_context_entropy_model_summary.csv"),
        m4_coefs=read_csv_if_exists(output_dir / "m4_context_entropy_coefficients.csv"),
        m4_frame=pd.DataFrame(),
        saturated_summary=read_csv_if_exists(output_dir / "m5_m6_saturated_model_summary.csv"),
        saturated_coefs=read_csv_if_exists(output_dir / "m5_m6_saturated_coefficients.csv"),
        saturated_frame=pd.DataFrame(),
        context_overview_override=read_csv_if_exists(output_dir / "m4_context_entropy_overview.csv"),
    )
    return {"markdown": md_path, "html": html_path, "output_dir": output_dir, "fig_dir": fig_dir}


def build_packet(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    md_path: Path,
    html_path: Path,
    context_k: str,
    chunksize: int,
) -> Mapping[str, Path]:
    """Run analysis and render the M1-M6 report."""

    run_packet_analysis(input_csv=input_csv, output_dir=output_dir, fig_dir=fig_dir, context_k=context_k, chunksize=chunksize)
    return render_packet_report_from_outputs(output_dir=output_dir, fig_dir=fig_dir, md_path=md_path, html_path=html_path, context_k=context_k)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--context-k", default="k3")
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument(
        "--stage",
        choices=["all", "analysis", "m5m6", "expanded_plots", "line_variants", "report"],
        default="all",
        help="all reruns analyses and report; analysis writes all tables/figures; m5m6 refits only effort-level M5/M6 outputs; expanded_plots refits M1-M3 subvariants and their line plots; line_variants refits M1/M2 low-mid-high, M4, and M5/M6 line variants; report rebuilds Markdown/HTML from existing outputs.",
    )
    args = parser.parse_args(argv)
    if args.stage in {"all", "analysis"}:
        outputs = run_packet_analysis(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_k=args.context_k,
            chunksize=args.chunksize,
        )
        print(f"[OK] wrote/updated analysis tables under: {outputs['output_dir']}")
        print(f"[OK] wrote/updated figures under: {outputs['fig_dir']}")
    if args.stage == "m5m6":
        outputs = run_m5_m6_analysis(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_k=args.context_k,
            chunksize=args.chunksize,
        )
        print(f"[OK] wrote/updated M5/M6 tables under: {outputs['output_dir']}")
        print(f"[OK] wrote/updated M5/M6 figures under: {outputs['fig_dir']}")
    if args.stage == "line_variants":
        outputs = run_line_variant_analysis(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_k=args.context_k,
            chunksize=args.chunksize,
        )
        print(f"[OK] wrote/updated alternate line-variant tables under: {outputs['output_dir']}")
        print(f"[OK] wrote/updated alternate line-variant figures under: {outputs['fig_dir']}")
    if args.stage == "expanded_plots":
        outputs = run_expanded_plot_analysis(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_k=args.context_k,
            chunksize=args.chunksize,
        )
        print(f"[OK] wrote/updated M1-M3 expanded plot tables under: {outputs['output_dir']}")
        print(f"[OK] wrote/updated M1-M3 expanded plot figures under: {outputs['fig_dir']}")
    if args.stage in {"all", "report"}:
        outputs = render_packet_report_from_outputs(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            md_path=args.markdown,
            html_path=args.html,
            context_k=args.context_k,
        )
        print(f"[OK] wrote M1-M6 report HTML: {outputs['html']}")


if __name__ == "__main__":
    main()
