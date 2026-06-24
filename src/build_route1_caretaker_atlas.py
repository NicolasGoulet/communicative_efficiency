#!/usr/bin/env python3
"""Caretaker analogue of the corrected Route 1 atlas.

This module prepares and fits an entropy-free caretaker target atlas:

    caretaker sum_bits ~ child age + caretaker effort + context controls

It is intentionally separate from ``build_route1_corrected_baseline_atlas``.
The child/baseline atlas treats caretakers as context or as an optional role
comparison; this script treats caretaker utterances as their own target family.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_route1_analysis_dataset import count_effort
    from build_route1_corrected_baseline_atlas import (
        EFFORT_SPECS,
        QUESTION_TYPE_ORDER,
        EffortSpec,
        markdown_table,
        parse_max_rows,
        question_type,
        selected_effort_specs,
        slugify,
        split_csv,
    )
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.build_route1_analysis_dataset import count_effort
    from src.build_route1_corrected_baseline_atlas import (
        EFFORT_SPECS,
        QUESTION_TYPE_ORDER,
        EffortSpec,
        markdown_table,
        parse_max_rows,
        question_type,
        selected_effort_specs,
        slugify,
        split_csv,
    )
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_caretaker_atlas")
DEFAULT_FIG_DIR = Path("figs/route1_caretaker_corrected_fixed_effort_atlas")
DEFAULT_DOC_DIR = Path("docs")
DEFAULT_CONTEXT_KS = ("k0", "k1", "k2", "k3")
DEFAULT_MODEL_IDS = ("CM1", "CM2", "CM3", "CM4a", "CM4c", "CM5", "CM6")

CARETAKER_COEFFICIENT_NAMES = (
    ("age_c", "age_coef", "age_p"),
    ("effort_c", "effort_coef", "effort_p"),
    ("preceding_context_effort_c", "preceding_context_effort_coef", "preceding_context_effort_p"),
    ("age_c:effort_c", "age_effort_coef", "age_effort_p"),
    ("age_c:preceding_context_effort_c", "age_preceding_context_effort_coef", "age_preceding_context_effort_p"),
    ("effort_c:preceding_context_effort_c", "effort_preceding_context_effort_coef", "effort_preceding_context_effort_p"),
)


@dataclass(frozen=True)
class CaretakerModelFamily:
    model_id: str
    label: str
    question: str
    needs_context_effort: bool = False
    needs_question_type: bool = False
    includes_age_effort_interaction: bool = False
    includes_context_effort_interactions: bool = False


@dataclass(frozen=True)
class CaretakerModelSpec:
    model_id: str
    model_label: str
    question: str
    context_k: str
    effort_col: str
    effort_label: str
    context_effort_col: str
    readable_formula: str
    statsmodels_formula: str
    needs_context_effort: bool
    needs_question_type: bool
    stage: str


CARETAKER_MODEL_FAMILIES = (
    CaretakerModelFamily(
        model_id="CM1",
        label="Pooled age and caretaker effort",
        question="Does child age predict caretaker utterance information after controlling caretaker effort?",
    ),
    CaretakerModelFamily(
        model_id="CM2",
        label="Age and caretaker effort with dyad identity",
        question="Does the child-age effect remain after dyad/family identity is controlled?",
    ),
    CaretakerModelFamily(
        model_id="CM3",
        label="Age by caretaker effort",
        question="Does the caretaker effort-information relation change over the child's development?",
        includes_age_effort_interaction=True,
    ),
    CaretakerModelFamily(
        model_id="CM4a",
        label="Preceding-context effort added",
        question="Does preceding conversational-context effort explain additional caretaker information?",
        needs_context_effort=True,
        includes_age_effort_interaction=True,
    ),
    CaretakerModelFamily(
        model_id="CM4c",
        label="Question type added",
        question="Does broad preceding-context question type explain additional caretaker information?",
        needs_question_type=True,
        includes_age_effort_interaction=True,
    ),
    CaretakerModelFamily(
        model_id="CM5",
        label="Context effort and question type",
        question="Do context effort and question type matter after age, caretaker effort, and dyad identity?",
        needs_context_effort=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
    ),
    CaretakerModelFamily(
        model_id="CM6",
        label="Context-effort interactions",
        question="Does context-effort sensitivity change with child age or caretaker target effort?",
        needs_context_effort=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_context_effort_interactions=True,
    ),
)


def caretaker_model_family(model_id: str) -> CaretakerModelFamily:
    for family in CARETAKER_MODEL_FAMILIES:
        if family.model_id == model_id:
            return family
    raise KeyError(f"Unknown caretaker model id: {model_id}")


def caretaker_needed_columns() -> set[str]:
    return {
        "score_id",
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "speaker",
        "role",
        "target_variant",
        "target_source",
        "context_k",
        "context_text",
        "sum_bits",
        *[spec.effort_col for spec in EFFORT_SPECS],
    }


def coerce_numeric(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def string_column(frame: pd.DataFrame, column: str, default: str = "") -> pd.Series:
    """Return a string-valued column, using a same-index default when absent."""

    if column in frame.columns:
        return frame[column].astype(str)
    return pd.Series(default, index=frame.index, dtype=str)


def format_p(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def param_value(result: object, name: str, attr: str = "params") -> float:
    """Extract a named fitted value from statsmodels results."""

    if result is None or not hasattr(result, attr):
        return math.nan
    values = getattr(result, attr)
    try:
        if hasattr(values, "get"):
            return float(values.get(name, math.nan))
        names = list(getattr(result.model, "exog_names", []))
        return float(values[names.index(name)]) if name in names else math.nan
    except Exception:
        return math.nan


def prediction_summary_frame(result: object, new_frame: pd.DataFrame) -> pd.DataFrame:
    """Return predicted caretaker means and model-confidence bands."""

    try:
        summary = result.get_prediction(new_frame).summary_frame(alpha=0.05)
    except Exception:
        pred = np.asarray(result.predict(new_frame), dtype=float)
        return pd.DataFrame({"predicted_sum_bits": pred, "pred_ci_low": np.nan, "pred_ci_high": np.nan})
    mean_col = "mean" if "mean" in summary.columns else "predicted_mean" if "predicted_mean" in summary.columns else None
    low_col = "mean_ci_lower" if "mean_ci_lower" in summary.columns else "ci_lower" if "ci_lower" in summary.columns else None
    high_col = "mean_ci_upper" if "mean_ci_upper" in summary.columns else "ci_upper" if "ci_upper" in summary.columns else None
    return pd.DataFrame(
        {
            "predicted_sum_bits": np.asarray(summary[mean_col], dtype=float)
            if mean_col
            else np.asarray(result.predict(new_frame), dtype=float),
            "pred_ci_low": np.asarray(summary[low_col], dtype=float) if low_col else np.nan,
            "pred_ci_high": np.asarray(summary[high_col], dtype=float) if high_col else np.nan,
        }
    )


def coefficient_long_table(result: object, spec: CaretakerModelSpec) -> pd.DataFrame:
    """Return one row per fitted caretaker coefficient."""

    if result is None or not hasattr(result, "params"):
        return pd.DataFrame()
    params = getattr(result, "params")
    names = list(params.index) if hasattr(params, "index") else list(getattr(result.model, "exog_names", []))
    pvalues = getattr(result, "pvalues", None)
    try:
        conf = result.conf_int()
    except Exception:
        conf = None
    rows: list[dict[str, object]] = []
    for idx, term in enumerate(names):
        try:
            estimate = float(params[term]) if hasattr(params, "__getitem__") and term in params else float(params[idx])
        except Exception:
            estimate = math.nan
        try:
            p_value = float(pvalues[term]) if hasattr(pvalues, "__getitem__") and term in pvalues else float(pvalues[idx])
        except Exception:
            p_value = math.nan
        ci_low = math.nan
        ci_high = math.nan
        if conf is not None:
            try:
                if hasattr(conf, "loc"):
                    ci_low = float(conf.loc[term].iloc[0])
                    ci_high = float(conf.loc[term].iloc[1])
                else:
                    ci_low = float(conf[idx][0])
                    ci_high = float(conf[idx][1])
            except Exception:
                pass
        rows.append(
            {
                "role": "caretaker",
                "target_source": "caretaker",
                "context_k": spec.context_k,
                "effort_col": spec.effort_col,
                "effort_label": spec.effort_label,
                "model_id": spec.model_id,
                "model_label": spec.model_label,
                "term": str(term),
                "estimate": estimate,
                "p_value": p_value,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "is_child_fixed_effect": str(term).startswith("C(child_id)"),
                "is_question_type_term": "question_type" in str(term),
            }
        )
    return pd.DataFrame(rows)


def context_effort_counts(text: object) -> dict[str, int]:
    counts = count_effort("" if pd.isna(text) else str(text))
    return {
        "preceding_context_nb_words": counts.nb_words,
        "preceding_context_nb_morphemes": counts.nb_morphemes,
        "preceding_context_nb_syllables_cmu_or_pkg": counts.nb_syllables_cmu_or_pkg,
        "preceding_context_nb_syllables_pkg": counts.nb_syllables_pkg,
        "preceding_context_nb_phonemes": counts.nb_phonemes,
    }


def add_caretaker_predictors(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "target_source" not in out.columns:
        out["target_source"] = out.get("target_variant", "").astype(str)
    out["target_source"] = out["target_source"].replace("", "caretaker")
    if "context_text" not in out.columns:
        out["context_text"] = ""

    unique_contexts = out["context_text"].fillna("").astype(str).drop_duplicates()
    context_lookup = {text: context_effort_counts(text) for text in unique_contexts}
    context_frame = pd.DataFrame.from_dict(context_lookup, orient="index")
    if context_frame.empty:
        for spec in EFFORT_SPECS:
            out[f"preceding_context_{spec.effort_col}"] = 0
    else:
        context_frame.index.name = "context_text"
        out = out.merge(context_frame.reset_index(), on="context_text", how="left")
    out["question_type"] = out["context_text"].fillna("").astype(str).map(question_type)
    return out


def read_caretaker_rows(
    input_csv: Path,
    *,
    chunksize: int,
    max_rows: int | None = None,
    context_ks: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Read only caretaker target rows, filtering by role inside each chunk."""

    parts: list[pd.DataFrame] = []
    rows_kept = 0
    wanted_contexts = set(context_ks or [])
    usecols = caretaker_needed_columns()
    reader = pd.read_csv(
        input_csv,
        usecols=lambda col: col in usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    try:
        for chunk in reader:
            if "role" not in chunk.columns:
                continue
            chunk = chunk[chunk["role"].astype(str).eq("caretaker")].copy()
            if "target_source" not in chunk.columns:
                chunk["target_source"] = chunk.get("target_variant", "").astype(str)
            chunk = chunk[
                chunk["target_source"].astype(str).isin(["caretaker", ""])
                | chunk.get("target_variant", pd.Series("", index=chunk.index)).astype(str).eq("caretaker")
            ].copy()
            if wanted_contexts:
                chunk = chunk[chunk["context_k"].astype(str).isin(wanted_contexts)].copy()
            if chunk.empty:
                continue
            if max_rows is not None:
                remaining = max_rows - rows_kept
                if remaining <= 0:
                    break
                chunk = chunk.head(remaining).copy()
            rows_kept += len(chunk)
            parts.append(chunk)
            if max_rows is not None and rows_kept >= max_rows:
                break
    finally:
        reader.close()
    if not parts:
        return pd.DataFrame(columns=sorted(usecols))
    return pd.concat(parts, ignore_index=True)


def read_caretaker_rows_balanced_by_context(
    input_csv: Path,
    *,
    chunksize: int,
    max_rows_per_context: int,
    context_ks: Sequence[str],
    max_rows_per_child_context: int | None = None,
) -> pd.DataFrame:
    """Read a bounded caretaker sample for each context in one pass.

    When ``max_rows_per_child_context`` is set, the sample is also capped within
    each ``context_k``/``child_id`` pair so smoke fits do not accidentally come
    from a single large dyad.
    """

    wanted_contexts = tuple(context_ks)
    if not wanted_contexts:
        return read_caretaker_rows(input_csv, chunksize=chunksize, max_rows=max_rows_per_context)

    parts: list[pd.DataFrame] = []
    rows_kept = {context_k: 0 for context_k in wanted_contexts}
    child_context_rows_kept: dict[tuple[str, str], int] = {}
    usecols = caretaker_needed_columns()
    reader = pd.read_csv(
        input_csv,
        usecols=lambda col: col in usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    try:
        for chunk in reader:
            if "role" not in chunk.columns:
                continue
            chunk = chunk[chunk["role"].astype(str).eq("caretaker")].copy()
            if "target_source" not in chunk.columns:
                chunk["target_source"] = chunk.get("target_variant", "").astype(str)
            chunk = chunk[
                chunk["target_source"].astype(str).isin(["caretaker", ""])
                | chunk.get("target_variant", pd.Series("", index=chunk.index)).astype(str).eq("caretaker")
            ].copy()
            if chunk.empty:
                continue
            for context_k in wanted_contexts:
                remaining = max_rows_per_context - rows_kept[context_k]
                if remaining <= 0:
                    continue
                subset = chunk[chunk["context_k"].astype(str).eq(context_k)].copy()
                if subset.empty:
                    continue
                if "child_id" not in subset.columns:
                    subset["child_id"] = ""
                if max_rows_per_child_context is None:
                    subset = subset.head(remaining).copy()
                    rows_kept[context_k] += len(subset)
                    parts.append(subset)
                    continue
                for child_id, child_group in subset.groupby("child_id", sort=False, dropna=False):
                    remaining = max_rows_per_context - rows_kept[context_k]
                    if remaining <= 0:
                        break
                    key = (context_k, str(child_id))
                    child_remaining = max_rows_per_child_context - child_context_rows_kept.get(key, 0)
                    if child_remaining <= 0:
                        continue
                    taken = child_group.head(min(remaining, child_remaining)).copy()
                    if taken.empty:
                        continue
                    child_context_rows_kept[key] = child_context_rows_kept.get(key, 0) + len(taken)
                    rows_kept[context_k] += len(taken)
                    parts.append(taken)
            if all(count >= max_rows_per_context for count in rows_kept.values()):
                break
    finally:
        reader.close()
    if not parts:
        return pd.DataFrame(columns=sorted(usecols))
    return pd.concat(parts, ignore_index=True)


def audit_caretaker_rows(
    input_csv: Path,
    *,
    output_dir: Path,
    chunksize: int,
    max_rows: int | None = None,
    context_ks: Sequence[str] | None = None,
) -> Mapping[str, Path]:
    """Stream a full caretaker availability audit without retaining all rows."""

    output_dir.mkdir(parents=True, exist_ok=True)
    wanted_contexts = set(context_ks or [])
    usecols = caretaker_needed_columns()
    by_context: dict[str, dict[str, object]] = {}
    by_child_context: dict[tuple[str, str], dict[str, object]] = {}
    rows_seen = 0
    reader = pd.read_csv(
        input_csv,
        usecols=lambda col: col in usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    try:
        for chunk in reader:
            if "role" not in chunk.columns:
                continue
            chunk = chunk[chunk["role"].astype(str).eq("caretaker")].copy()
            if "target_source" not in chunk.columns:
                chunk["target_source"] = chunk.get("target_variant", "").astype(str)
            chunk = chunk[
                chunk["target_source"].astype(str).isin(["caretaker", ""])
                | chunk.get("target_variant", pd.Series("", index=chunk.index)).astype(str).eq("caretaker")
            ].copy()
            if wanted_contexts:
                chunk = chunk[chunk["context_k"].astype(str).isin(wanted_contexts)].copy()
            if max_rows is not None:
                remaining = max_rows - rows_seen
                if remaining <= 0:
                    break
                chunk = chunk.head(remaining).copy()
            rows_seen += len(chunk)
            if chunk.empty:
                continue
            chunk = coerce_numeric(chunk, ["age_months", "sum_bits", *[spec.effort_col for spec in EFFORT_SPECS]])
            for context_k, group in chunk.groupby("context_k", dropna=False):
                record = by_context.setdefault(
                    str(context_k),
                    {
                        "context_k": str(context_k),
                        "rows": 0,
                        "children": set(),
                        "speakers": set(),
                        "sessions": set(),
                        "missing_age_rows": 0,
                        "missing_sum_bits_rows": 0,
                        "blank_context_rows": 0,
                        **{f"missing_{spec.effort_col}_rows": 0 for spec in EFFORT_SPECS},
                    },
                )
                record["rows"] = int(record["rows"]) + len(group)
                record["children"].update(string_column(group, "child_id"))
                record["speakers"].update(string_column(group, "speaker"))
                record["sessions"].update(string_column(group, "session_id"))
                record["missing_age_rows"] = int(record["missing_age_rows"]) + int(group["age_months"].isna().sum())
                record["missing_sum_bits_rows"] = int(record["missing_sum_bits_rows"]) + int(group["sum_bits"].isna().sum())
                record["blank_context_rows"] = int(record["blank_context_rows"]) + int(
                    string_column(group, "context_text").eq("").sum()
                )
                for spec in EFFORT_SPECS:
                    record[f"missing_{spec.effort_col}_rows"] = int(record[f"missing_{spec.effort_col}_rows"]) + int(
                        group[spec.effort_col].isna().sum()
                    )
            for (child_id, context_k), group in chunk.groupby(["child_id", "context_k"], dropna=False):
                record = by_child_context.setdefault(
                    (str(child_id), str(context_k)),
                    {
                        "child_id": str(child_id),
                        "context_k": str(context_k),
                        "rows": 0,
                        "sessions": set(),
                        "speakers": set(),
                    },
                )
                record["rows"] = int(record["rows"]) + len(group)
                record["sessions"].update(string_column(group, "session_id"))
                record["speakers"].update(string_column(group, "speaker"))
    finally:
        reader.close()

    context_rows = []
    for record in by_context.values():
        row = dict(record)
        row["children"] = len(row["children"])
        row["speakers"] = len({speaker for speaker in row["speakers"] if speaker})
        row["sessions"] = len(row["sessions"])
        context_rows.append(row)
    child_rows = []
    for record in by_child_context.values():
        row = dict(record)
        row["sessions"] = len(row["sessions"])
        row["speakers"] = len({speaker for speaker in row["speakers"] if speaker})
        child_rows.append(row)

    context_audit = pd.DataFrame(context_rows).sort_values("context_k") if context_rows else pd.DataFrame()
    child_context_audit = (
        pd.DataFrame(child_rows).sort_values(["context_k", "child_id"]) if child_rows else pd.DataFrame()
    )
    paths = {
        "context_audit": output_dir / "caretaker_context_audit.csv",
        "child_context_audit": output_dir / "caretaker_child_context_audit.csv",
    }
    context_audit.to_csv(paths["context_audit"], index=False)
    child_context_audit.to_csv(paths["child_context_audit"], index=False)
    return paths


def build_caretaker_model_spec(
    *,
    family: CaretakerModelFamily,
    effort: EffortSpec,
    context_k: str,
    stage: str,
) -> CaretakerModelSpec:
    age_term = "age_c"
    effort_term = "effort_c"
    terms: list[str]
    if family.includes_age_effort_interaction:
        terms = [f"{age_term} * {effort_term}", "C(child_id)"]
    elif family.model_id == "CM1":
        terms = [age_term, effort_term]
    else:
        terms = [age_term, effort_term, "C(child_id)"]
    if family.needs_context_effort:
        terms.append("preceding_context_effort_c")
    if family.needs_question_type:
        terms.append("C(question_type)")
    if family.includes_context_effort_interactions:
        terms.append("age_c:preceding_context_effort_c")
        terms.append("effort_c:preceding_context_effort_c")
    formula = "sum_bits ~ " + " + ".join(terms)
    readable = (
        formula.replace("sum_bits", "caretaker_sum_bits")
        .replace("age_c", "child_age_c")
        .replace("effort_c", "caretaker_effort_c")
        .replace("child_id", "dyad_child_id")
    )
    return CaretakerModelSpec(
        model_id=family.model_id,
        model_label=family.label,
        question=family.question,
        context_k=context_k,
        effort_col=effort.effort_col,
        effort_label=effort.effort_label,
        context_effort_col=f"preceding_context_{effort.effort_col}",
        readable_formula=readable,
        statsmodels_formula=formula,
        needs_context_effort=family.needs_context_effort,
        needs_question_type=family.needs_question_type,
        stage=stage,
    )


def build_caretaker_manifest(
    *,
    context_ks: Sequence[str] = DEFAULT_CONTEXT_KS,
    effort_specs: Sequence[EffortSpec] = EFFORT_SPECS,
    model_ids: Sequence[str] = DEFAULT_MODEL_IDS,
    stage: str = "caretaker_fit",
) -> pd.DataFrame:
    rows = []
    families = [caretaker_model_family(model_id) for model_id in model_ids]
    for context_k in context_ks:
        for effort in effort_specs:
            for family in families:
                rows.append(asdict(build_caretaker_model_spec(family=family, effort=effort, context_k=context_k, stage=stage)))
    return pd.DataFrame(rows)


def prepare_caretaker_model_frame(frame: pd.DataFrame, spec: CaretakerModelSpec) -> tuple[pd.DataFrame, str]:
    data = add_caretaker_predictors(frame)
    for col in ["role", "target_source", "context_k", "child_id"]:
        if col not in data.columns:
            data[col] = ""
    data = data[data["role"].astype(str).eq("caretaker")].copy()
    data = data[
        data["target_source"].astype(str).isin(["caretaker", ""])
        | data.get("target_variant", pd.Series("", index=data.index)).astype(str).eq("caretaker")
    ].copy()
    data = data[data["context_k"].astype(str).eq(spec.context_k)].copy()
    if data.empty:
        return data, "no caretaker rows for context"

    for col in ["sum_bits", "age_months", spec.effort_col, spec.context_effort_col]:
        if col not in data.columns:
            data[col] = math.nan
    data = coerce_numeric(data, ["sum_bits", "age_months", spec.effort_col, spec.context_effort_col])
    data["effort_value"] = data[spec.effort_col]
    data["preceding_context_effort_value"] = data[spec.context_effort_col]
    required = ["sum_bits", "age_months", "effort_value", "child_id"]
    if spec.needs_context_effort:
        required.append("preceding_context_effort_value")
    if spec.needs_question_type:
        required.append("question_type")
    data = data.dropna(subset=required).copy()
    data = data[(data["sum_bits"] > 0) & (data["age_months"] > 0) & (data["effort_value"] > 0)].copy()
    if data.empty:
        return data, "no complete caretaker rows"
    if data["child_id"].nunique() < 2:
        return data, "fewer than two dyads"

    data["age_c"] = data["age_months"] - data["age_months"].mean()
    data["effort_c"] = data["effort_value"] - data["effort_value"].mean()
    data["preceding_context_effort_c"] = (
        data["preceding_context_effort_value"] - data["preceding_context_effort_value"].mean()
        if spec.needs_context_effort
        else 0.0
    )
    data["child_id"] = data["child_id"].astype(str)
    data["question_type"] = pd.Categorical(data["question_type"].astype(str), categories=QUESTION_TYPE_ORDER)

    variation_problem = caretaker_variation_check(data, spec)
    if variation_problem:
        return data, variation_problem
    return data.reset_index(drop=True), ""


def caretaker_variation_check(frame: pd.DataFrame, spec: CaretakerModelSpec) -> str:
    checks = [
        ("age_c", "child age has no variation"),
        ("effort_c", "caretaker target effort has no variation"),
    ]
    if spec.needs_context_effort:
        checks.append(("preceding_context_effort_c", "preceding context effort has no variation"))
    for col, message in checks:
        if col in frame and pd.to_numeric(frame[col], errors="coerce").std(ddof=0) <= 0:
            return message
    if spec.needs_question_type and frame["question_type"].nunique(dropna=True) < 2:
        return "question type has fewer than two levels"
    return ""


def fit_caretaker_spec_row(frame: pd.DataFrame, spec: CaretakerModelSpec) -> tuple[dict[str, object], object | None, pd.DataFrame]:
    model_frame, prepare_error = prepare_caretaker_model_frame(frame, spec)
    summary = asdict(spec)
    summary.update(
        {
            "role": "caretaker",
            "target_source": "caretaker",
            "n_obs": int(len(model_frame)),
            "n_dyads": int(model_frame["child_id"].nunique()) if "child_id" in model_frame else 0,
            "n_speakers": int(model_frame["speaker"].nunique()) if "speaker" in model_frame else 0,
            "status": "skipped" if prepare_error else "fit",
            "error": prepare_error,
            "r2": math.nan,
            "aic": math.nan,
            "bic": math.nan,
        }
    )
    for _, coef_col, p_col in CARETAKER_COEFFICIENT_NAMES:
        summary[coef_col] = math.nan
        summary[p_col] = math.nan
    if prepare_error:
        return summary, None, model_frame
    try:
        result = smf.ols(spec.statsmodels_formula, data=model_frame).fit(
            cov_type="cluster",
            cov_kwds={"groups": model_frame["child_id"]},
        )
    except Exception as exc:  # pragma: no cover - real-data guard
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        return summary, None, model_frame
    summary["r2"] = float(getattr(result, "rsquared", math.nan))
    summary["aic"] = float(getattr(result, "aic", math.nan))
    summary["bic"] = float(getattr(result, "bic", math.nan))
    for param_name, coef_col, p_col in CARETAKER_COEFFICIENT_NAMES:
        summary[coef_col] = param_value(result, param_name)
        summary[p_col] = param_value(result, param_name, "pvalues")
    return summary, result, model_frame


def split_ordered_values(values: Sequence[int]) -> list[tuple[str, list[int]]]:
    ordered = sorted({int(value) for value in values if int(value) > 0})
    chunks = np.array_split(np.array(ordered), 3) if ordered else []
    labels = ["low representative sizes", "middle representative sizes", "high representative sizes"]
    return [(label, [int(value) for value in chunk.tolist()]) for label, chunk in zip(labels, chunks) if len(chunk)]


def caretaker_fixed_effort_bins(frame: pd.DataFrame, *, context_k: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in EFFORT_SPECS:
        effort_col = spec.effort_col
        if effort_col in {"nb_words", "nb_morphemes"}:
            bins = [
                ("1-4", [1, 2, 3, 4], "Exact fixed values 1-4."),
                ("5-8", [5, 6, 7, 8], "Exact fixed values 5-8."),
                ("9-12", [9, 10, 11, 12], "Exact fixed values 9-12."),
            ]
        else:
            counts = pd.to_numeric(frame[effort_col], errors="coerce").dropna().astype(int).value_counts().head(12)
            bins = [
                (label, values, "Ordered split of the 12 most frequent observed exact values.")
                for label, values in split_ordered_values(counts.index.astype(int).tolist())
            ]
        for atlas_bin, values, rule in bins:
            support = frame[pd.to_numeric(frame[effort_col], errors="coerce").isin(values)]
            rows.append(
                {
                    "context_k": context_k,
                    "effort_col": effort_col,
                    "effort_label": spec.effort_label,
                    "atlas_bin": atlas_bin,
                    "fixed_values": ", ".join(str(value) for value in values),
                    "n_fixed_values": len(values),
                    "support_rows": int(len(support)),
                    "support_dyads": int(support["child_id"].nunique()) if not support.empty and "child_id" in support else 0,
                    "rule": rule,
                }
            )
    return pd.DataFrame(rows)


def average_child_predictions(
    result: object,
    base: pd.DataFrame,
    child_ids: Sequence[str],
    *,
    has_child_id: bool,
) -> pd.DataFrame:
    if not has_child_id:
        pred = prediction_summary_frame(result, base)
        return pd.concat([base.reset_index(drop=True), pred.reset_index(drop=True)], axis=1)
    parts: list[pd.DataFrame] = []
    for child_id in child_ids:
        child_frame = base.copy()
        child_frame["child_id"] = child_id
        pred = prediction_summary_frame(result, child_frame)
        parts.append(pd.concat([child_frame.reset_index(drop=True), pred.reset_index(drop=True)], axis=1))
    combined = pd.concat(parts, ignore_index=True)
    group_cols = ["age_months", "fixed_effort_value", "atlas_bin", "model_id", "effort_col"]
    return (
        combined.groupby(group_cols, as_index=False)[["predicted_sum_bits", "pred_ci_low", "pred_ci_high"]]
        .mean()
        .copy()
    )


def fixed_effort_prediction_rows(
    model_frame: pd.DataFrame,
    result: object,
    spec: CaretakerModelSpec,
    bin_defs: pd.DataFrame,
    *,
    n_points: int,
) -> pd.DataFrame:
    if model_frame.empty or result is None:
        return pd.DataFrame()
    ages = pd.to_numeric(model_frame["age_months"], errors="coerce").dropna()
    if ages.empty:
        return pd.DataFrame()
    age_grid = pd.Series(np.linspace(float(ages.quantile(0.02)), float(ages.quantile(0.98)), n_points))
    child_ids = sorted(model_frame["child_id"].astype(str).unique())
    modal_question = str(model_frame["question_type"].mode().iloc[0]) if "question_type" in model_frame else "not question"
    mean_age = float(model_frame["age_months"].mean())
    mean_effort = float(model_frame["effort_value"].mean())
    mean_context_effort = float(model_frame["preceding_context_effort_value"].mean()) if spec.needs_context_effort else 0.0
    rows: list[pd.DataFrame] = []
    for item in bin_defs[bin_defs["effort_col"].eq(spec.effort_col)].to_dict("records"):
        values = [int(value.strip()) for value in str(item["fixed_values"]).split(",") if value.strip()]
        for effort in values:
            base = pd.DataFrame(
                {
                    "age_months": age_grid,
                    "age_c": age_grid - mean_age,
                    "effort_value": effort,
                    "effort_c": effort - mean_effort,
                    "preceding_context_effort_value": mean_context_effort,
                    "preceding_context_effort_c": 0.0,
                    "question_type": pd.Categorical([modal_question] * len(age_grid), categories=QUESTION_TYPE_ORDER),
                    "fixed_effort_value": int(effort),
                    "atlas_bin": str(item["atlas_bin"]),
                    "model_id": spec.model_id,
                    "effort_col": spec.effort_col,
                }
            )
            pred = average_child_predictions(
                result,
                base,
                child_ids,
                has_child_id="C(child_id)" in spec.statsmodels_formula,
            )
            rows.append(pred)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["role"] = "caretaker"
    out["target_source"] = "caretaker"
    out["model_id"] = spec.model_id
    out["model_label"] = spec.model_label
    out["context_k"] = spec.context_k
    out["effort_col"] = spec.effort_col
    out["effort_label"] = spec.effort_label
    return out


def run_caretaker_smoke_fit(
    *,
    input_csv: Path,
    output_dir: Path,
    max_rows: int,
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    if max_rows is not None and len(context_ks) > 1:
        frame = read_caretaker_rows_balanced_by_context(
            input_csv,
            chunksize=chunksize,
            max_rows_per_context=max_rows,
            context_ks=context_ks,
            max_rows_per_child_context=max(1, max_rows // 5),
        )
    else:
        frame = read_caretaker_rows(input_csv, chunksize=chunksize, max_rows=max_rows, context_ks=context_ks)
    effort_specs = selected_effort_specs(effort_cols)
    specs = [
        build_caretaker_model_spec(
            family=caretaker_model_family(model_id),
            effort=effort,
            context_k=context_k,
            stage="bounded_caretaker_smoke_fit",
        )
        for context_k in context_ks
        for effort in effort_specs
        for model_id in model_ids
    ]
    rows = []
    predictions = []
    bin_defs = caretaker_fixed_effort_bins(frame, context_k="smoke")
    for spec in specs:
        row, result, model_frame = fit_caretaker_spec_row(frame, spec)
        rows.append(row)
        if row["status"] == "fit":
            pred = fixed_effort_prediction_rows(model_frame, result, spec, bin_defs, n_points=12)
            if not pred.empty:
                predictions.append(pred)
    summary = pd.DataFrame(rows)
    summary.to_csv(output_dir / "caretaker_smoke_fit_summary.csv", index=False)
    if predictions:
        pd.concat(predictions, ignore_index=True).to_csv(output_dir / "caretaker_smoke_fixed_effort_predictions.csv", index=False)
    return summary


def run_caretaker_fit_atlas(
    *,
    input_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    doc_dir: Path,
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
    max_rows: int | None,
    n_points: int,
    render_pdf_file: bool,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    effort_specs = selected_effort_specs(effort_cols)
    all_summaries = []
    all_predictions = []
    all_coefficients = []
    all_bin_defs = []
    for context_k in context_ks:
        frame = read_caretaker_rows(input_csv, chunksize=chunksize, max_rows=max_rows, context_ks=(context_k,))
        bin_defs = caretaker_fixed_effort_bins(frame, context_k=context_k)
        all_bin_defs.append(bin_defs)
        specs = [
            build_caretaker_model_spec(
                family=caretaker_model_family(model_id),
                effort=effort,
                context_k=context_k,
                stage="caretaker_fit",
            )
            for effort in effort_specs
            for model_id in model_ids
        ]
        rows = []
        predictions = []
        coefficients = []
        for spec in specs:
            row, result, model_frame = fit_caretaker_spec_row(frame, spec)
            rows.append(row)
            if row["status"] == "fit":
                coef = coefficient_long_table(result, spec)
                if not coef.empty:
                    coefficients.append(coef)
                pred = fixed_effort_prediction_rows(model_frame, result, spec, bin_defs, n_points=n_points)
                if not pred.empty:
                    predictions.append(pred)
                try:
                    result.remove_data()
                except Exception:
                    pass
        context_summary = pd.DataFrame(rows)
        context_summary.to_csv(output_dir / f"caretaker_{slugify(context_k)}_model_summary.csv", index=False)
        all_summaries.append(context_summary)
        if coefficients:
            context_coefficients = pd.concat(coefficients, ignore_index=True)
            context_coefficients.to_csv(output_dir / f"caretaker_{slugify(context_k)}_coefficient_long.csv", index=False)
            all_coefficients.append(context_coefficients)
        if predictions:
            context_predictions = pd.concat(predictions, ignore_index=True)
            context_predictions.to_csv(output_dir / f"caretaker_{slugify(context_k)}_fixed_effort_predictions.csv", index=False)
            all_predictions.append(context_predictions)
    summary = pd.concat(all_summaries, ignore_index=True) if all_summaries else pd.DataFrame()
    coefficients = pd.concat(all_coefficients, ignore_index=True) if all_coefficients else pd.DataFrame()
    summary.to_csv(output_dir / "caretaker_model_summary.csv", index=False)
    coefficients.to_csv(output_dir / "caretaker_coefficient_long.csv", index=False)
    bin_defs_all = pd.concat(all_bin_defs, ignore_index=True) if all_bin_defs else pd.DataFrame()
    bin_defs_all.to_csv(output_dir / "caretaker_fixed_effort_bin_definitions.csv", index=False)
    if all_predictions:
        predictions_all = pd.concat(all_predictions, ignore_index=True)
    else:
        predictions_all = pd.DataFrame()
    predictions_all.to_csv(output_dir / "caretaker_fixed_effort_predictions.csv.gz", index=False)
    figure_manifest = plot_caretaker_fixed_predictions(predictions_all, fig_dir=fig_dir)
    slopes = caretaker_fixed_slice_slopes(predictions_all)
    slopes.to_csv(output_dir / "caretaker_fixed_slice_slopes.csv", index=False)
    figure_manifest.to_csv(output_dir / "caretaker_figure_manifest.csv", index=False)
    audit = pd.DataFrame(
        [
            {
                "role": "caretaker",
                "model_rows": len(summary),
                "fit_rows": int(summary["status"].eq("fit").sum()) if not summary.empty else 0,
                "coefficient_rows": len(coefficients),
                "prediction_rows": len(predictions_all),
                "figure_rows": len(figure_manifest),
            }
        ]
    )
    audit.to_csv(output_dir / "caretaker_audit.csv", index=False)
    report_path = output_dir / "reports" / "caretaker_corrected_fixed_effort_atlas_v2.md"
    write_caretaker_report(
        summary,
        report_path,
        bin_defs=bin_defs_all,
        coefficients=coefficients,
        figure_manifest=figure_manifest,
        slopes=slopes,
        output_dir=output_dir,
        fig_dir=fig_dir,
    )
    render_markdown_file(report_path, report_path.with_suffix(".html"))
    if render_pdf_file:
        render_pdf(report_path.with_suffix(".html"), report_path.with_suffix(".pdf"))
    doc_path = doc_dir / "utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.md"
    write_caretaker_report(
        summary,
        doc_path,
        bin_defs=bin_defs_all,
        coefficients=coefficients,
        figure_manifest=figure_manifest,
        slopes=slopes,
        output_dir=output_dir,
        fig_dir=fig_dir,
    )
    render_markdown_file(doc_path, doc_path.with_suffix(".html"))
    if render_pdf_file:
        render_pdf(doc_path.with_suffix(".html"), doc_path.with_suffix(".pdf"))
    return summary


def run_caretaker_report_atlas(
    *,
    output_dir: Path,
    fig_dir: Path,
    doc_dir: Path,
    render_pdf_file: bool,
) -> pd.DataFrame:
    """Rebuild caretaker reports from saved artifacts without refitting."""

    required = {
        "summary": output_dir / "caretaker_model_summary.csv",
        "coefficients": output_dir / "caretaker_coefficient_long.csv",
        "bin_defs": output_dir / "caretaker_fixed_effort_bin_definitions.csv",
        "slopes": output_dir / "caretaker_fixed_slice_slopes.csv",
        "figure_manifest": output_dir / "caretaker_figure_manifest.csv",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing saved caretaker artifacts for report-only stage: {missing}")
    summary = pd.read_csv(required["summary"])
    coefficients = pd.read_csv(required["coefficients"])
    bin_defs = pd.read_csv(required["bin_defs"])
    slopes = pd.read_csv(required["slopes"])
    figure_manifest = pd.read_csv(required["figure_manifest"])
    report_path = output_dir / "reports" / "caretaker_corrected_fixed_effort_atlas_v2.md"
    write_caretaker_report(
        summary,
        report_path,
        bin_defs=bin_defs,
        coefficients=coefficients,
        figure_manifest=figure_manifest,
        slopes=slopes,
        output_dir=output_dir,
        fig_dir=fig_dir,
    )
    render_markdown_file(report_path, report_path.with_suffix(".html"))
    if render_pdf_file:
        render_pdf(report_path.with_suffix(".html"), report_path.with_suffix(".pdf"))
    doc_path = doc_dir / "utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.md"
    write_caretaker_report(
        summary,
        doc_path,
        bin_defs=bin_defs,
        coefficients=coefficients,
        figure_manifest=figure_manifest,
        slopes=slopes,
        output_dir=output_dir,
        fig_dir=fig_dir,
    )
    render_markdown_file(doc_path, doc_path.with_suffix(".html"))
    if render_pdf_file:
        render_pdf(doc_path.with_suffix(".html"), doc_path.with_suffix(".pdf"))
    return summary


def plot_caretaker_fixed_predictions(predictions: pd.DataFrame, *, fig_dir: Path) -> pd.DataFrame:
    """Plot caretaker fixed-effort atlas figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return pd.DataFrame()
    group_cols = ["target_source", "context_k", "model_id", "model_label", "effort_col", "effort_label"]
    for keys, group in predictions.groupby(group_cols, sort=True):
        source, context_k, model_id, model_label, effort_col, effort_label = keys
        bins = list(group["atlas_bin"].drop_duplicates())
        fig, axes = plt.subplots(1, len(bins), figsize=(5.8 * len(bins), 4.9), sharey=True)
        if len(bins) == 1:
            axes = [axes]
        for ax, atlas_bin in zip(axes, bins):
            panel = group[group["atlas_bin"].eq(atlas_bin)].copy()
            values = sorted(int(value) for value in panel["fixed_effort_value"].unique())
            palette = sns.color_palette("viridis", n_colors=max(1, len(values)))
            color_map = {value: palette[idx] for idx, value in enumerate(values)}
            for fixed_value, line in panel.groupby("fixed_effort_value", sort=True):
                color = color_map[int(fixed_value)]
                ax.plot(line["age_months"], line["predicted_sum_bits"], color=color, linewidth=2.0, label=str(int(fixed_value)))
                if line[["pred_ci_low", "pred_ci_high"]].notna().all(axis=None):
                    ax.fill_between(
                        line["age_months"].to_numpy(dtype=float),
                        line["pred_ci_low"].to_numpy(dtype=float),
                        line["pred_ci_high"].to_numpy(dtype=float),
                        color=color,
                        alpha=0.18,
                        linewidth=0,
                    )
                    ax.plot(
                        line["age_months"],
                        line["pred_ci_low"],
                        color=color,
                        linewidth=0.8,
                        alpha=0.45,
                    )
                    ax.plot(
                        line["age_months"],
                        line["pred_ci_high"],
                        color=color,
                        linewidth=0.8,
                        alpha=0.45,
                    )
            ax.set_title(atlas_bin)
            ax.set_xlabel("Child age in months")
            ax.grid(alpha=0.18)
            ax.legend(title="Fixed value", fontsize=8, title_fontsize=9)
        axes[0].set_ylabel("Predicted caretaker total bits")
        fig.suptitle(f"{source} | {context_k.upper()} {model_id}: {model_label} | {effort_label}", y=1.05)
        fig.tight_layout()
        filename = f"caretaker_{context_k}_{model_id.lower()}_{slugify(effort_col)}_fixed_effort_atlas.png"
        out = fig_dir / filename
        fig.savefig(out, dpi=210, bbox_inches="tight")
        fig.savefig(fig_dir / filename.replace(".png", ".pdf"), bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "target_source": source,
                "context_k": context_k,
                "model_id": model_id,
                "model_label": model_label,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "figure": str(out),
            }
        )
    return pd.DataFrame(rows)


def caretaker_fixed_slice_slopes(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive slopes from plotted caretaker fixed-effort lines."""

    if predictions.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    keys = [
        "target_source",
        "context_k",
        "model_id",
        "model_label",
        "effort_col",
        "effort_label",
        "atlas_bin",
        "fixed_effort_value",
    ]
    for key, group in predictions.groupby(keys, sort=True):
        source, context_k, model_id, model_label, effort_col, effort_label, atlas_bin, fixed_value = key
        ages = group["age_months"].to_numpy(dtype=float)
        bits = group["predicted_sum_bits"].to_numpy(dtype=float)
        slope = float(np.polyfit(ages, bits, 1)[0]) if len(np.unique(ages)) >= 2 else math.nan
        rows.append(
            {
                "target_source": source,
                "context_k": context_k,
                "model_id": model_id,
                "model_label": model_label,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "atlas_bin": atlas_bin,
                "fixed_effort_value": int(fixed_value),
                "slope_bits_per_month": slope,
                "slope_bits_per_6_months": slope * 6 if math.isfinite(slope) else math.nan,
                "direction": "downward" if slope < 0 else "upward" if slope > 0 else "flat",
            }
        )
    return pd.DataFrame(rows)


def caretaker_slope_summary(slopes: pd.DataFrame) -> pd.DataFrame:
    if slopes.empty:
        return pd.DataFrame()
    return (
        slopes.groupby(["target_source", "context_k", "model_id", "model_label", "effort_label", "atlas_bin"], observed=True)
        .agg(
            n_fixed_slices=("fixed_effort_value", "nunique"),
            negative_slices=("slope_bits_per_month", lambda values: int((values < 0).sum())),
            positive_slices=("slope_bits_per_month", lambda values: int((values > 0).sum())),
            mean_slope_bits_per_month=("slope_bits_per_month", "mean"),
            min_slope_bits_per_month=("slope_bits_per_month", "min"),
            max_slope_bits_per_month=("slope_bits_per_month", "max"),
        )
        .reset_index()
    )


def caretaker_fit_overview(summary: pd.DataFrame) -> pd.DataFrame:
    fitted = summary[summary["status"].eq("fit")].copy()
    if fitted.empty:
        return pd.DataFrame()
    return (
        fitted.groupby(["target_source", "context_k", "model_id", "model_label"], observed=True)
        .agg(
            fitted_rows=("status", "size"),
            mean_r2=("r2", "mean"),
            negative_age_coef_rows=("age_coef", lambda values: int((pd.to_numeric(values, errors="coerce") < 0).sum())),
            significant_age_rows=("age_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_effort_rows=("effort_p", lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum())),
            significant_context_effort_rows=(
                "preceding_context_effort_p",
                lambda values: int((pd.to_numeric(values, errors="coerce") < 0.05).sum()),
            ),
        )
        .reset_index()
    )


def caretaker_coefficient_table(summary: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "target_source",
        "context_k",
        "model_id",
        "model_label",
        "effort_label",
        "n_obs",
        "n_dyads",
        "n_speakers",
        "r2",
        "age_coef",
        "age_p",
        "effort_coef",
        "effort_p",
        "preceding_context_effort_coef",
        "preceding_context_effort_p",
        "age_effort_coef",
        "age_effort_p",
        "age_preceding_context_effort_coef",
        "age_preceding_context_effort_p",
        "effort_preceding_context_effort_coef",
        "effort_preceding_context_effort_p",
    ]
    out = summary[summary["status"].eq("fit")][[col for col in cols if col in summary.columns]].copy()
    for col in [column for column in out.columns if column.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def caretaker_formula_table(summary: pd.DataFrame) -> pd.DataFrame:
    cols = ["model_id", "model_label", "question", "readable_formula", "statsmodels_formula"]
    out = summary[cols].drop_duplicates("model_id").copy()
    order = {model_id: idx for idx, model_id in enumerate(DEFAULT_MODEL_IDS)}
    out["_order"] = out["model_id"].map(order).fillna(len(order))
    return out.sort_values(["_order", "model_id"]).drop(columns=["_order"]).reset_index(drop=True)


def caretaker_model_reader_card(summary: pd.DataFrame, model_id: str) -> list[str]:
    rows = summary[summary["model_id"].astype(str).eq(model_id)].copy()
    if rows.empty:
        return []
    row = rows.iloc[0]
    fitted = rows[rows["status"].eq("fit")].copy()
    contexts = ", ".join(str(value).upper() for value in sorted(rows["context_k"].dropna().unique()))
    efforts = ", ".join(str(value) for value in sorted(rows["effort_label"].dropna().unique()))
    if not fitted.empty and "n_obs" in fitted:
        n_obs_text = f"{int(fitted['n_obs'].min()):,}-{int(fitted['n_obs'].max()):,}"
    else:
        n_obs_text = "not available"
    if not fitted.empty and "r2" in fitted:
        mean_r2 = float(fitted["r2"].mean())
        r2_text = f"{mean_r2:.3f}" if math.isfinite(mean_r2) else "not available"
    else:
        r2_text = "not available"
    return [
        f"### {model_id}: {row['model_label']}",
        "",
        f"**Question.** {row['question']}",
        "",
        f"**Conceptual formula.** `{row['readable_formula']}`",
        "",
        f"**Fitted formula.** `{row['statsmodels_formula']}`",
        "",
        "**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.",
        "",
        "**Uncertainty.** Child/dyad-cluster robust standard errors.",
        "",
        "**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.",
        "",
        f"**Coverage.** {len(fitted)}/{len(rows)} fitted combinations across {contexts}; effort axes: {efforts}. Observations per fitted combination: {n_obs_text}. Mean descriptive R2: {r2_text}.",
        "",
        "**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.",
        "",
    ]


def relative_to_report(report_path: Path, figure_path: str) -> str:
    report_base = report_path if report_path.suffix == "" else report_path.parent
    try:
        return os.path.relpath(Path(figure_path).resolve(), start=report_base.resolve()).replace(os.sep, "/")
    except ValueError:
        return Path(figure_path).resolve().as_posix()


def render_pdf(html_path: Path, pdf_path: Path) -> bool:
    import shutil
    import subprocess

    browser = shutil.which("brave-browser") or shutil.which("google-chrome")
    if not browser:
        return False
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            browser,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path.resolve()}",
            f"file://{html_path.resolve()}",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def write_caretaker_report(
    summary: pd.DataFrame,
    path: Path,
    *,
    bin_defs: pd.DataFrame,
    coefficients: pd.DataFrame,
    figure_manifest: pd.DataFrame,
    slopes: pd.DataFrame,
    output_dir: Path,
    fig_dir: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    skipped = summary[summary["status"].ne("fit")].copy()
    lines = [
        "# Route 1 Caretaker Corrected Fixed-Effort Atlas v2",
        "",
        "This is the caretaker-target analogue of the corrected child/source atlases.",
        "The developmental timeline is the focal child's age. The target utterance is the caretaker utterance, fit independently from the child real/random/ngram/LSTM source reports.",
        "",
        "## Implementation",
        "",
        "- Estimator: linear ordinary least squares regression.",
        "- Library: `statsmodels.formula.api.ols`.",
        "- Uncertainty: child/dyad-cluster robust standard errors.",
        "- Outcome: caretaker `sum_bits`, the total information for the caretaker target utterance.",
        "- Context: k0/k1/k2/k3 are fit independently; k0 correctly skips models that require preceding context effort or question type.",
        "- Fixed slices: models are fit on all eligible rows; fixed effort values only define plotted prediction lines.",
        "",
        "## Start Here",
        "",
        "Each section below is one caretaker model. It starts with the model question, formula, regression type, library, uncertainty structure, and then the plots. Long tables are kept out of the report body and saved as CSV artifacts.",
        "",
        "## Model Atlas",
        "",
    ]
    model_order = [model_id for model_id in DEFAULT_MODEL_IDS if model_id in set(summary["model_id"].astype(str))]
    for model_id in model_order:
        model_figs_all = figure_manifest[figure_manifest["model_id"].astype(str).eq(model_id)].copy() if not figure_manifest.empty else pd.DataFrame()
        if model_figs_all.empty:
            lines.extend(caretaker_model_reader_card(summary, model_id))
            continue
        lines.extend(caretaker_model_reader_card(summary, model_id))
        for context_k in DEFAULT_CONTEXT_KS:
            model_figs = model_figs_all[model_figs_all["context_k"].eq(context_k)].copy()
            if model_figs.empty:
                continue
            lines.extend([f"#### {context_k.upper()} plots", ""])
            for row in model_figs.sort_values("effort_label").to_dict("records"):
                rel = relative_to_report(path, str(row["figure"]))
                lines.extend([f"**{row['effort_label']}**", "", f"![{context_k} {model_id} {row['effort_label']}]({rel})", ""])
    if not skipped.empty:
        lines.extend(
            [
                "## Skipped Or Failed Fits",
                "",
                "Some requested model/context/effort combinations did not fit. This is expected for k0 models that require preceding context. Exact rows are saved in `caretaker_model_summary.csv`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Saved Tables And Artifacts",
            "",
            "The long coefficient tables, fixed-effort prediction grids, slice definitions, and slope summaries are saved as CSV artifacts. They are intentionally not printed in this HTML report because the consultation layer is the model cards and plots above.",
            "",
            "```text",
            str(output_dir / "caretaker_model_summary.csv"),
            str(output_dir / "caretaker_coefficient_long.csv"),
            str(output_dir / "caretaker_fixed_effort_bin_definitions.csv"),
            str(output_dir / "caretaker_fixed_effort_predictions.csv.gz"),
            str(output_dir / "caretaker_fixed_slice_slopes.csv"),
            str(output_dir / "caretaker_figure_manifest.csv"),
            f"{fig_dir}/",
            "```",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_caretaker_launch_commands(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Caretaker Atlas Launch Commands

Run these only after focused tests and preflight pass.

## Full Caretaker Fit

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_caretaker_atlas.py \\
  --stage fit-atlas \\
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz \\
  --output-dir results/route1_caretaker_atlas/full_fit \\
  --fig-dir figs/route1_caretaker_corrected_fixed_effort_atlas \\
  --doc-dir docs \\
  --context-ks k0,k1,k2,k3 \\
  --effort-cols all \\
  --model-ids all \\
  --max-rows 0 \\
  --chunksize 250000 \\
  --n-points 60
```

This is entropy-free and caretaker-target only.
""",
        encoding="utf-8",
    )


def run_caretaker_preflight(
    *,
    input_csv: Path,
    output_dir: Path,
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
    max_rows: int | None,
) -> Mapping[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = audit_caretaker_rows(
        input_csv,
        output_dir=output_dir,
        chunksize=chunksize,
        max_rows=max_rows,
        context_ks=context_ks,
    )
    manifest = build_caretaker_manifest(
        context_ks=context_ks,
        effort_specs=selected_effort_specs(effort_cols),
        model_ids=model_ids,
        stage="caretaker_preflight",
    )
    manifest_path = output_dir / "caretaker_model_manifest.csv"
    family_path = output_dir / "caretaker_model_family_definitions.csv"
    launch_path = output_dir / "CARETAKER_FULL_RUN_COMMANDS.md"
    manifest.to_csv(manifest_path, index=False)
    pd.DataFrame([asdict(family) for family in CARETAKER_MODEL_FAMILIES]).to_csv(family_path, index=False)
    write_caretaker_launch_commands(launch_path)
    paths = dict(paths)
    paths.update({"manifest": manifest_path, "model_families": family_path, "launch_commands": launch_path})
    return paths


def normalize_model_ids(model_ids: Sequence[str]) -> tuple[str, ...]:
    if tuple(model_ids) == ("all",):
        return DEFAULT_MODEL_IDS
    return tuple(model_ids)


def normalize_effort_cols(effort_cols: Sequence[str]) -> tuple[str, ...]:
    if tuple(effort_cols) == ("all",):
        return tuple(spec.effort_col for spec in EFFORT_SPECS)
    return tuple(effort_cols)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["preflight", "smoke-fit", "fit-atlas", "report"], default="preflight")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--context-ks", default=",".join(DEFAULT_CONTEXT_KS))
    parser.add_argument("--effort-cols", default="nb_words")
    parser.add_argument("--model-ids", default="CM1,CM2,CM3")
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--max-rows", type=int, default=50_000)
    parser.add_argument("--n-points", type=int, default=60)
    parser.add_argument("--no-pdf", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    context_ks = split_csv(args.context_ks)
    effort_cols = normalize_effort_cols(split_csv(args.effort_cols))
    model_ids = normalize_model_ids(split_csv(args.model_ids))
    max_rows = parse_max_rows(args.max_rows)
    if args.stage == "preflight":
        paths = run_caretaker_preflight(
            input_csv=args.input,
            output_dir=args.output_dir,
            context_ks=context_ks,
            effort_cols=effort_cols,
            model_ids=model_ids,
            chunksize=args.chunksize,
            max_rows=max_rows,
        )
        for label, path in paths.items():
            print(f"[OK] {label}: {path}")
        return
    if args.stage == "smoke-fit":
        summary = run_caretaker_smoke_fit(
            input_csv=args.input,
            output_dir=args.output_dir,
            max_rows=max_rows or 50_000,
            context_ks=context_ks,
            effort_cols=effort_cols,
            model_ids=model_ids,
            chunksize=args.chunksize,
        )
        print(f"[OK] caretaker smoke model rows: {len(summary)}")
        print(f"[OK] summary: {args.output_dir / 'caretaker_smoke_fit_summary.csv'}")
        return
    if args.stage == "fit-atlas":
        summary = run_caretaker_fit_atlas(
            input_csv=args.input,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            doc_dir=args.doc_dir,
            context_ks=context_ks,
            effort_cols=effort_cols,
            model_ids=model_ids,
            chunksize=args.chunksize,
            max_rows=max_rows,
            n_points=args.n_points,
            render_pdf_file=not args.no_pdf,
        )
        print(f"[OK] caretaker fit rows: {len(summary)}")
        print(f"[OK] summary: {args.output_dir / 'caretaker_model_summary.csv'}")
        return
    if args.stage == "report":
        summary = run_caretaker_report_atlas(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            doc_dir=args.doc_dir,
            render_pdf_file=not args.no_pdf,
        )
        print(f"[OK] caretaker report rows: {len(summary)}")
        print(f"[OK] report: {args.doc_dir / 'utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.md'}")
        return


if __name__ == "__main__":
    main()
