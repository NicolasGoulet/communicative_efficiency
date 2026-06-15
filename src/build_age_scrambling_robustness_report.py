#!/usr/bin/env python3
"""Build Route 1 age-trajectory bootstrap and scrambling robustness reports.

This is a complementary validation workflow inspired by Pawar & Cychosz
(2025). It does not modify the original Route 1 dataset or existing M1-M6
reports. It asks whether the developmental age effects seen in utterance-level
information models survive balanced resampling and disappear when age structure
is deliberately broken.

The workflow has two stages:

``analysis``
    Read real child utterance rows, aggregate them to child-session-context
    units, fit M1-M6 continuous-effort analogs, and run balanced bootstrap plus
    age-scrambling refits.

``report``
    Render Markdown/HTML from saved CSV artifacts and figures only.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from build_m1_m2_utterance_information_deep_dive import AGE_BIN_ORDER, DEFAULT_INPUT, EFFORT_MEASURES
    from attach_context_entropy_to_route1_dataset import DEFAULT_ENTROPY_FEATURES, load_entropy_lookups
    from render_markdown_report import render_markdown_file
    from build_route1_analysis_dataset import (
        DEFAULT_MAIN_SCORED_ROOT,
        context_text_for_row,
        count_effort,
        iter_scored_files,
        parse_scored_file,
        parse_float,
    )
    from build_route1_report_assets import age_to_route1_bin, resolve_age_months
    from utterance_count_strategies import normalize_text
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import AGE_BIN_ORDER, DEFAULT_INPUT, EFFORT_MEASURES
    from src.attach_context_entropy_to_route1_dataset import DEFAULT_ENTROPY_FEATURES, load_entropy_lookups
    from src.render_markdown_report import render_markdown_file
    from src.build_route1_analysis_dataset import (
        DEFAULT_MAIN_SCORED_ROOT,
        context_text_for_row,
        count_effort,
        iter_scored_files,
        parse_scored_file,
        parse_float,
    )
    from src.build_route1_report_assets import age_to_route1_bin, resolve_age_months
    from src.utterance_count_strategies import normalize_text


DEFAULT_OUTPUT_DIR = Path("results/age_scrambling_robustness")
DEFAULT_FIG_DIR = Path("figs/age_scrambling_robustness")
DEFAULT_DOC_MD = Path("docs/utterance_information_age_scrambling_robustness.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_age_scrambling_robustness.html")
DEFAULT_CONTEXT_KS = ("k0", "k1", "k2", "k3")
DEFAULT_REPLICATES = 100
DEFAULT_BALANCED_UNITS_PER_BIN = 50
SEED = 20260615
DEFAULT_SOURCE = "scored-tree"
DEFAULT_UNIT_FRAME_INPUT = DEFAULT_OUTPUT_DIR / "age_scrambling_unit_frame.csv.gz"
SCORED_TREE_USECOLS = [
    "dataset",
    "child_id",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "context_col_used",
    "chi_utterance_clean",
    "sum_bits",
    "mean_bits_per_token",
    "n_eval_tokens",
]

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
    "context_entropy_bits",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
]

EFFORT_COLS = [col for col, _ in EFFORT_MEASURES]
EFFORT_LABELS = {col: label for col, label in EFFORT_MEASURES}


@dataclass(frozen=True)
class RobustModelSpec:
    """One continuous-effort M1-M6 robustness model."""

    model_id: str
    model_title: str
    question: str
    readable_formula: str
    needs_child_fe: bool
    needs_entropy: bool
    include_age_effort: bool = False
    include_age_entropy: bool = False
    include_effort_entropy: bool = False


MODEL_SPECS = [
    RobustModelSpec(
        model_id="M1",
        model_title="Pooled age and effort",
        question="Does age predict total bits after controlling production effort, pooling children?",
        readable_formula="mean_sum_bits ~ age + mean_effort",
        needs_child_fe=False,
        needs_entropy=False,
    ),
    RobustModelSpec(
        model_id="M2",
        model_title="Age and effort with child identity",
        question="Does the age effect remain after controlling each child's baseline?",
        readable_formula="mean_sum_bits ~ age + mean_effort + child identity",
        needs_child_fe=True,
        needs_entropy=False,
    ),
    RobustModelSpec(
        model_id="M3",
        model_title="Age by effort",
        question="Does the age effect change as production effort changes?",
        readable_formula="mean_sum_bits ~ age * mean_effort + child identity",
        needs_child_fe=True,
        needs_entropy=False,
        include_age_effort=True,
    ),
    RobustModelSpec(
        model_id="M4",
        model_title="Context entropy added",
        question="Does the age effect remain after effort, child identity, and context entropy are controlled?",
        readable_formula="mean_sum_bits ~ age + mean_effort + mean_context_entropy + child identity",
        needs_child_fe=True,
        needs_entropy=True,
    ),
    RobustModelSpec(
        model_id="M5",
        model_title="Age by context entropy",
        question="Does the context-entropy association change over developmental time?",
        readable_formula="mean_sum_bits ~ age * mean_context_entropy + mean_effort + child identity",
        needs_child_fe=True,
        needs_entropy=True,
        include_age_entropy=True,
    ),
    RobustModelSpec(
        model_id="M6",
        model_title="Interaction-rich stress test",
        question="Do age, effort, and context entropy interact when predicting total bits?",
        readable_formula=(
            "mean_sum_bits ~ age * mean_effort + age * mean_context_entropy + "
            "mean_effort * mean_context_entropy + child identity"
        ),
        needs_child_fe=True,
        needs_entropy=True,
        include_age_effort=True,
        include_age_entropy=True,
        include_effort_entropy=True,
    ),
]

ROBUSTNESS_METHODS = [
    ("balanced_bootstrap", "Balanced age-bin bootstrap"),
    ("age_bin_group_scramble", "Grouped age-bin label scramble"),
    ("unit_age_scramble", "Unit-level age scramble"),
    ("within_child_age_scramble", "Within-child age scramble"),
]

METHOD_EXPLANATIONS = [
    (
        "balanced_bootstrap",
        "Samples the same number of child-session-context units from every age bin, with replacement. "
        "This checks whether the age slope survives when dense bins cannot dominate.",
    ),
    (
        "age_bin_group_scramble",
        "Permutes whole age-bin labels. The data inside each original bin stay together, but the developmental ordering is broken.",
    ),
    (
        "unit_age_scramble",
        "Permutes age values across units. This preserves the overall age distribution but breaks the link between an utterance unit and its age.",
    ),
    (
        "within_child_age_scramble",
        "Permutes session ages within each child. This preserves each child's speech style and age range while breaking their true timeline.",
    ),
]


def split_csv(value: str | Sequence[str]) -> list[str]:
    """Parse comma-separated CLI values."""

    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 80, digits: int = 4) -> str:
    """Render a small dataframe as a Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    rendered = shown.astype(object).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]) or pd.api.types.is_integer_dtype(shown[col]):
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else f"{float(value):.{digits}g}")
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
    """Format a p-like value compactly."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def read_real_child_rows(
    input_csv: Path,
    *,
    context_ks: Sequence[str],
    chunksize: int,
) -> pd.DataFrame:
    """Read real child rows for selected context windows."""

    wanted_ks = set(context_ks)
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in set(USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        wanted = chunk[
            chunk["role"].eq("child")
            & chunk["target_variant"].eq("real")
            & chunk["context_k"].isin(wanted_ks)
        ].copy()
        if not wanted.empty:
            parts.append(wanted)
    if not parts:
        raise ValueError(f"no real child rows found in {input_csv} for context windows {sorted(wanted_ks)}")
    out = pd.concat(parts, ignore_index=True)
    for col in ["age_months", "sum_bits", "context_entropy_bits", *EFFORT_COLS]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["dataset", "child_id", "session_id", "age_months", "age_bin", "context_k", "sum_bits", *EFFORT_COLS])
    out = out[(out["age_months"] > 0) & (out["sum_bits"] > 0)].copy()
    for col in EFFORT_COLS:
        out = out[out[col] > 0].copy()
    out["age_bin"] = pd.Categorical(out["age_bin"], categories=AGE_BIN_ORDER, ordered=True)
    out["child_id"] = out["child_id"].astype(str)
    out["session_id"] = out["session_id"].astype(str)
    out["dataset"] = out["dataset"].astype(str)
    out["context_k"] = out["context_k"].astype(str)
    return out.reset_index(drop=True)


def read_csv_header(path: Path) -> list[str]:
    """Return the header of a CSV file without loading its rows."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            return []


def count_effort_columns(texts: pd.Series) -> pd.DataFrame:
    """Return selected effort columns for a series of cleaned utterances.

    Effort counting is cached by the lower-level Route 1 helper, and this
    wrapper also avoids recomputing counts for repeated strings within a file.
    """

    normalized = texts.map(normalize_text)
    unique_counts = {text: count_effort(text) for text in normalized.dropna().unique()}
    rows = []
    for text in normalized:
        counts = unique_counts.get(text)
        if counts is None:
            counts = count_effort("")
        rows.append(
            {
                "nb_words": counts.nb_words,
                "nb_morphemes": counts.nb_morphemes,
                "nb_syllables_cmu_or_pkg": counts.nb_syllables_cmu_or_pkg,
                "nb_syllables_pkg": counts.nb_syllables_pkg,
                "nb_phonemes": counts.nb_phonemes,
            }
        )
    return pd.DataFrame(rows, index=texts.index)


def entropy_bits_for_contexts(
    frame: pd.DataFrame,
    *,
    context_k: str,
    entropy_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    entropy_text_lookup: Mapping[str, Mapping[str, str]],
) -> tuple[pd.Series, pd.Series]:
    """Attach context next-token entropy to a scored-tree chunk.

    The entropy scorer deduplicated by text in some cases, so this mirrors the
    production join: first try `(context column, context text)`, then text-only
    fallback.
    """

    if context_k == "k0":
        return pd.Series([math.nan] * len(frame), index=frame.index), pd.Series(["no_context_k0"] * len(frame), index=frame.index)

    values: list[float] = []
    statuses: list[str] = []
    for row in frame.to_dict("records"):
        context_text, context_col = context_text_for_row(row, type("SpecProxy", (), {"context_k": context_k})())
        context_text = normalize_text(context_text)
        context_col = normalize_text(context_col or f"context_{context_k}")
        if not context_text:
            values.append(math.nan)
            statuses.append("empty_context")
            continue
        payload = entropy_lookup.get((context_col, context_text))
        status = "matched"
        if payload is None:
            payload = entropy_text_lookup.get(context_text)
            status = "matched_text_fallback" if payload is not None else "missing_entropy"
        if payload is None:
            values.append(math.nan)
            statuses.append(status)
            continue
        parsed_entropy = parse_float(payload.get("llm_next_entropy_bits", ""))
        values.append(parsed_entropy if parsed_entropy is not None else math.nan)
        statuses.append(status)
    return pd.Series(values, index=frame.index), pd.Series(statuses, index=frame.index)


def scored_tree_file_to_units(
    path: Path,
    *,
    scored_root: Path,
    score_source: str,
    context_ks: Sequence[str],
    entropy_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    entropy_text_lookup: Mapping[str, Mapping[str, str]],
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Read one split scored file and return child-session unit summaries."""

    spec = parse_scored_file(scored_root, path, score_source)
    audit: dict[str, object] = {
        "scored_file": str(path),
        "context_k": spec.context_k,
        "dataset": spec.dataset_dir,
        "child": spec.child_dir,
        "rows_read": 0,
        "rows_kept": 0,
        "rows_dropped": 0,
        "entropy_matched_rows": 0,
        "entropy_missing_rows": 0,
    }
    if spec.role != "child" or spec.target_variant != "real" or spec.context_k not in set(context_ks):
        return pd.DataFrame(), audit

    header = read_csv_header(path)
    usecols = [col for col in SCORED_TREE_USECOLS if col in set(header)]
    if "chi_utterance_clean" not in usecols or "sum_bits" not in usecols:
        audit["rows_dropped"] = audit["rows_read"]
        return pd.DataFrame(), audit

    df = pd.read_csv(path, usecols=usecols, dtype=str, keep_default_na=False, low_memory=False)
    audit["rows_read"] = int(len(df))
    if df.empty:
        return pd.DataFrame(), audit

    for col in ["dataset", "child_id", "session_id", "file", "line_no", "utt_id"]:
        if col not in df.columns:
            df[col] = ""
    df["dataset"] = df["dataset"].map(normalize_text).replace("", spec.dataset_dir)
    df["child_id"] = df["child_id"].map(normalize_text).replace("", spec.child_dir)
    df["session_id"] = df["session_id"].map(normalize_text)
    df["target_utterance_clean"] = df["chi_utterance_clean"].map(normalize_text)
    df["sum_bits"] = pd.to_numeric(df["sum_bits"], errors="coerce")
    age_resolved = df.apply(
        lambda row: resolve_age_months(row.get("age_months", ""), row.get("file", ""))[0],
        axis=1,
    )
    df["age_months"] = pd.to_numeric(age_resolved, errors="coerce")
    df["age_bin"] = df["age_months"].map(age_to_route1_bin)
    efforts = count_effort_columns(df["target_utterance_clean"])
    df = pd.concat([df, efforts], axis=1)
    df["context_k"] = spec.context_k
    df["context_entropy_bits"], df["context_entropy_join_status"] = entropy_bits_for_contexts(
        df,
        context_k=spec.context_k,
        entropy_lookup=entropy_lookup,
        entropy_text_lookup=entropy_text_lookup,
    )

    valid = (
        df["target_utterance_clean"].ne("")
        & df["sum_bits"].notna()
        & df["sum_bits"].gt(0)
        & df["age_months"].notna()
        & df["age_months"].gt(0)
        & df["age_bin"].notna()
    )
    for col in EFFORT_COLS:
        valid &= df[col].gt(0)
    kept = df.loc[valid].copy()
    audit["rows_kept"] = int(len(kept))
    audit["rows_dropped"] = int(len(df) - len(kept))
    audit["entropy_matched_rows"] = int(kept["context_entropy_bits"].notna().sum())
    audit["entropy_missing_rows"] = int(kept["context_entropy_bits"].isna().sum())
    if kept.empty:
        return pd.DataFrame(), audit

    group_cols = ["dataset", "child_id", "session_id", "age_months", "age_bin", "context_k"]
    agg: dict[str, tuple[str, str]] = {
        "n_utterances": ("sum_bits", "size"),
        "mean_sum_bits": ("sum_bits", "mean"),
        "median_sum_bits": ("sum_bits", "median"),
        "sd_sum_bits": ("sum_bits", "std"),
        "mean_context_entropy_bits": ("context_entropy_bits", "mean"),
        "n_context_entropy_nonblank": ("context_entropy_bits", lambda values: int(values.notna().sum())),
    }
    for col in EFFORT_COLS:
        agg[f"mean_{col}"] = (col, "mean")
        agg[f"median_{col}"] = (col, "median")
    units = kept.groupby(group_cols, observed=True, dropna=False).agg(**agg).reset_index()
    return units, audit


def build_units_from_scored_tree(
    *,
    scored_root: Path,
    score_source: str,
    entropy_features_csv: Path,
    context_ks: Sequence[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stream split scored files and build the small unit-level frame."""

    wanted_ks = set(context_ks)
    entropy_lookup, entropy_text_lookup, _ = load_entropy_lookups(entropy_features_csv)
    unit_parts: list[pd.DataFrame] = []
    audits: list[dict[str, object]] = []
    for spec in iter_scored_files(scored_root, score_source):
        if spec.role != "child" or spec.target_variant != "real" or spec.context_k not in wanted_ks:
            continue
        units, audit = scored_tree_file_to_units(
            spec.path,
            scored_root=scored_root,
            score_source=score_source,
            context_ks=context_ks,
            entropy_lookup=entropy_lookup,
            entropy_text_lookup=entropy_text_lookup,
        )
        audits.append(audit)
        if not units.empty:
            unit_parts.append(units)
    if not unit_parts:
        raise ValueError(f"no real child scored files found under {scored_root} for {sorted(wanted_ks)}")
    out = pd.concat(unit_parts, ignore_index=True)
    out["unit_id"] = (
        out["dataset"].astype(str)
        + "::"
        + out["child_id"].astype(str)
        + "::"
        + out["session_id"].astype(str)
        + "::"
        + out["context_k"].astype(str)
    )
    out["child_session_id"] = (
        out["dataset"].astype(str)
        + "::"
        + out["child_id"].astype(str)
        + "::"
        + out["session_id"].astype(str)
    )
    out["age_bin"] = pd.Categorical(out["age_bin"], categories=AGE_BIN_ORDER, ordered=True)
    out["age_bin_label"] = out["age_bin"].astype(str)
    out["age_bin_midpoint"] = out["age_bin_label"].map(age_bin_midpoint)
    return out.reset_index(drop=True), pd.DataFrame(audits)


def read_existing_unit_frame(path: Path, *, context_ks: Sequence[str]) -> pd.DataFrame:
    """Read a previously built unit frame for fast model refits."""

    if not path.exists():
        raise FileNotFoundError(f"unit frame does not exist: {path}")
    out = pd.read_csv(path)
    required = {
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "context_k",
        "n_utterances",
        "mean_sum_bits",
        "mean_context_entropy_bits",
        *[f"mean_{col}" for col in EFFORT_COLS],
    }
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"{path} is missing required unit-frame columns: {sorted(missing)}")
    out = out[out["context_k"].astype(str).isin(set(context_ks))].copy()
    for col in ["age_months", "n_utterances", "mean_sum_bits", "mean_context_entropy_bits", *[f"mean_{c}" for c in EFFORT_COLS]]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["age_bin"] = pd.Categorical(out["age_bin"].astype(str), categories=AGE_BIN_ORDER, ordered=True)
    out["age_bin_label"] = out.get("age_bin_label", out["age_bin"].astype(str)).astype(str)
    out["age_bin_midpoint"] = out.get("age_bin_midpoint", out["age_bin_label"].map(age_bin_midpoint))
    if "unit_id" not in out.columns:
        out["unit_id"] = (
            out["dataset"].astype(str)
            + "::"
            + out["child_id"].astype(str)
            + "::"
            + out["session_id"].astype(str)
            + "::"
            + out["context_k"].astype(str)
        )
    if "child_session_id" not in out.columns:
        out["child_session_id"] = (
            out["dataset"].astype(str)
            + "::"
            + out["child_id"].astype(str)
            + "::"
            + out["session_id"].astype(str)
        )
    return out.reset_index(drop=True)


def aggregate_to_units(rows: pd.DataFrame) -> pd.DataFrame:
    """Aggregate utterance rows to child-session-context units."""

    group_cols = ["dataset", "child_id", "session_id", "age_months", "age_bin", "context_k"]
    agg: dict[str, tuple[str, str]] = {
        "n_utterances": ("sum_bits", "size"),
        "mean_sum_bits": ("sum_bits", "mean"),
        "median_sum_bits": ("sum_bits", "median"),
        "sd_sum_bits": ("sum_bits", "std"),
        "mean_context_entropy_bits": ("context_entropy_bits", "mean"),
        "n_context_entropy_nonblank": ("context_entropy_bits", lambda values: int(pd.to_numeric(values, errors="coerce").notna().sum())),
    }
    for col in EFFORT_COLS:
        agg[f"mean_{col}"] = (col, "mean")
        agg[f"median_{col}"] = (col, "median")
    out = rows.groupby(group_cols, observed=True, dropna=False).agg(**agg).reset_index()
    out["unit_id"] = (
        out["dataset"].astype(str)
        + "::"
        + out["child_id"].astype(str)
        + "::"
        + out["session_id"].astype(str)
        + "::"
        + out["context_k"].astype(str)
    )
    out["child_session_id"] = (
        out["dataset"].astype(str)
        + "::"
        + out["child_id"].astype(str)
        + "::"
        + out["session_id"].astype(str)
    )
    out["age_bin"] = pd.Categorical(out["age_bin"], categories=AGE_BIN_ORDER, ordered=True)
    out["age_bin_label"] = out["age_bin"].astype(str)
    out["age_bin_midpoint"] = out["age_bin_label"].map(age_bin_midpoint)
    return out.reset_index(drop=True)


def age_bin_midpoint(age_bin: object) -> float:
    """Return midpoint for labels like 024-029."""

    text = str(age_bin)
    if "-" not in text:
        return math.nan
    left, right = text.split("-", 1)
    try:
        return (float(left) + float(right)) / 2
    except ValueError:
        return math.nan


def model_frame(units: pd.DataFrame, spec: RobustModelSpec, effort_col: str, context_k: str) -> pd.DataFrame:
    """Create a complete centered model frame for one model/effort/context."""

    effort_mean_col = f"mean_{effort_col}"
    out = units[units["context_k"].eq(context_k)].copy()
    needed = ["mean_sum_bits", "age_months", "child_id", effort_mean_col]
    if spec.needs_entropy:
        needed.append("mean_context_entropy_bits")
    out = out.dropna(subset=needed).copy()
    out = out[(out["mean_sum_bits"] > 0) & (out["age_months"] > 0) & (out[effort_mean_col] > 0)].copy()
    if spec.needs_entropy:
        out = out[out["mean_context_entropy_bits"] > 0].copy()
    if out.empty:
        return out
    out = out.rename(columns={effort_mean_col: "effort_value"}).copy()
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["effort_c"] = out["effort_value"] - out["effort_value"].mean()
    out["context_entropy_c"] = (
        out["mean_context_entropy_bits"] - out["mean_context_entropy_bits"].mean()
        if spec.needs_entropy
        else 0.0
    )
    out["child_id"] = out["child_id"].astype(str)
    return out.reset_index(drop=True)


def design_matrix(frame: pd.DataFrame, spec: RobustModelSpec) -> tuple[np.ndarray, list[str]]:
    """Build a numeric design matrix for fast repeated linear fits."""

    columns = [np.ones(len(frame), dtype=float)]
    names = ["Intercept"]
    columns.append(frame["age_c"].to_numpy(dtype=float))
    names.append("age_c")
    columns.append(frame["effort_c"].to_numpy(dtype=float))
    names.append("effort_c")
    if spec.needs_entropy:
        columns.append(frame["context_entropy_c"].to_numpy(dtype=float))
        names.append("context_entropy_c")
    if spec.include_age_effort:
        columns.append((frame["age_c"] * frame["effort_c"]).to_numpy(dtype=float))
        names.append("age_c:effort_c")
    if spec.include_age_entropy:
        columns.append((frame["age_c"] * frame["context_entropy_c"]).to_numpy(dtype=float))
        names.append("age_c:context_entropy_c")
    if spec.include_effort_entropy:
        columns.append((frame["effort_c"] * frame["context_entropy_c"]).to_numpy(dtype=float))
        names.append("effort_c:context_entropy_c")
    if spec.needs_child_fe:
        child_dummies = pd.get_dummies(frame["child_id"], prefix="child", drop_first=True, dtype=float)
        for col in child_dummies.columns:
            columns.append(child_dummies[col].to_numpy(dtype=float))
            names.append(str(col))
    return np.column_stack(columns), names


def fit_fast_age_model(frame: pd.DataFrame, spec: RobustModelSpec) -> dict[str, float | str]:
    """Fit one linear model and return key coefficients."""

    if len(frame) < 5 or frame["age_months"].nunique() < 2:
        return {"status": "skipped", "error": "too few rows or ages"}
    try:
        x, names = design_matrix(frame, spec)
        y = frame["mean_sum_bits"].to_numpy(dtype=float)
        beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
        fitted = x @ beta
        sst = float(np.sum((y - y.mean()) ** 2))
        r2 = math.nan if sst <= 0 else 1.0 - float(np.sum((y - fitted) ** 2)) / sst
        coefs = dict(zip(names, beta))
        return {
            "status": "fit",
            "error": "",
            "rank": int(rank),
            "n_predictors": len(names),
            "r2_observed_fitted": r2,
            "age_coef": float(coefs.get("age_c", math.nan)),
            "effort_coef": float(coefs.get("effort_c", math.nan)),
            "context_entropy_coef": float(coefs.get("context_entropy_c", math.nan)),
            "age_effort_coef": float(coefs.get("age_c:effort_c", math.nan)),
            "age_entropy_coef": float(coefs.get("age_c:context_entropy_c", math.nan)),
            "effort_entropy_coef": float(coefs.get("effort_c:context_entropy_c", math.nan)),
        }
    except Exception as exc:  # pragma: no cover - defensive real-data guard
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def sample_balanced_age_bins(frame: pd.DataFrame, *, rng: np.random.Generator, n_per_bin: int) -> pd.DataFrame:
    """Sample the same number of units per age bin, with replacement."""

    parts: list[pd.DataFrame] = []
    for _, group in frame.groupby("age_bin_label", sort=True):
        if group.empty:
            continue
        indices = rng.choice(group.index.to_numpy(), size=n_per_bin, replace=True)
        parts.append(frame.loc[indices])
    if not parts:
        return frame.iloc[0:0].copy()
    return pd.concat(parts, ignore_index=True)


def scramble_age_bin_groups(frame: pd.DataFrame, *, rng: np.random.Generator) -> pd.DataFrame:
    """Permute age-bin labels as whole groups and use bin midpoints as age."""

    out = frame.copy()
    labels = [label for label in AGE_BIN_ORDER if label in set(out["age_bin_label"])]
    if len(labels) < 2:
        return out
    shuffled = list(labels)
    rng.shuffle(shuffled)
    mapping = dict(zip(labels, shuffled))
    out["scrambled_age_bin_label"] = out["age_bin_label"].map(mapping).fillna(out["age_bin_label"])
    out["age_months"] = out["scrambled_age_bin_label"].map(age_bin_midpoint)
    out["age_bin_label"] = out["scrambled_age_bin_label"]
    return out.drop(columns=["scrambled_age_bin_label"])


def scramble_unit_ages(frame: pd.DataFrame, *, rng: np.random.Generator) -> pd.DataFrame:
    """Permute age values globally across units."""

    out = frame.copy()
    perm = rng.permutation(len(out))
    out["age_months"] = out["age_months"].to_numpy()[perm]
    out["age_bin_label"] = out["age_bin_label"].to_numpy()[perm]
    return out


def scramble_within_child_ages(frame: pd.DataFrame, *, rng: np.random.Generator) -> pd.DataFrame:
    """Permute session ages within each child while preserving child identity."""

    out = frame.copy()
    for _, child_index in out.groupby("child_id", sort=False).groups.items():
        idx = np.array(list(child_index))
        if len(idx) < 2:
            continue
        permuted = rng.permutation(idx)
        out.loc[idx, "age_months"] = out.loc[permuted, "age_months"].to_numpy()
        out.loc[idx, "age_bin_label"] = out.loc[permuted, "age_bin_label"].to_numpy()
    return out


def recenter_frame(frame: pd.DataFrame, spec: RobustModelSpec) -> pd.DataFrame:
    """Recenter predictors after resampling or scrambling."""

    out = frame.copy()
    out["age_c"] = out["age_months"] - out["age_months"].mean()
    out["effort_c"] = out["effort_value"] - out["effort_value"].mean()
    if spec.needs_entropy:
        out["context_entropy_c"] = out["mean_context_entropy_bits"] - out["mean_context_entropy_bits"].mean()
    else:
        out["context_entropy_c"] = 0.0
    return out


def robustness_refits(
    frame: pd.DataFrame,
    spec: RobustModelSpec,
    *,
    n_reps: int,
    balanced_units_per_bin: int,
    seed: int,
) -> pd.DataFrame:
    """Run balanced bootstrap and age-scrambling refits for one model frame."""

    rows: list[dict[str, object]] = []
    for rep in range(n_reps):
        rng = np.random.default_rng(seed + rep)
        variants = {
            "balanced_bootstrap": sample_balanced_age_bins(frame, rng=rng, n_per_bin=balanced_units_per_bin),
            "age_bin_group_scramble": scramble_age_bin_groups(frame, rng=rng),
            "unit_age_scramble": scramble_unit_ages(frame, rng=rng),
            "within_child_age_scramble": scramble_within_child_ages(frame, rng=rng),
        }
        for method, variant in variants.items():
            centered = recenter_frame(variant, spec)
            fit = fit_fast_age_model(centered, spec)
            rows.append(
                {
                    "robustness_method": method,
                    "replicate": rep,
                    **fit,
                }
            )
    return pd.DataFrame(rows)


def summarize_replicates(observed: pd.DataFrame, replicates: pd.DataFrame) -> pd.DataFrame:
    """Summarize bootstrap and permutation distributions around observed slopes."""

    rows: list[dict[str, object]] = []
    key_cols = ["context_k", "model_id", "effort_col", "effort_label"]
    for key, obs_group in observed.groupby(key_cols, sort=True):
        obs = obs_group.iloc[0]
        obs_age = float(obs["age_coef"])
        sub_all = replicates
        for col, value in zip(key_cols, key):
            sub_all = sub_all[sub_all[col].eq(value)]
        for method, method_label in ROBUSTNESS_METHODS:
            sub = sub_all[sub_all["robustness_method"].eq(method) & sub_all["status"].eq("fit")].copy()
            values = pd.to_numeric(sub["age_coef"], errors="coerce").dropna()
            if values.empty:
                rows.append(
                    {
                        **dict(zip(key_cols, key)),
                        "model_title": obs["model_title"],
                        "question": obs["question"],
                        "readable_formula": obs["readable_formula"],
                        "robustness_method": method,
                        "robustness_label": method_label,
                        "observed_age_coef": obs_age,
                        "n_fit_replicates": 0,
                    }
                )
                continue
            same_sign = float((np.sign(values) == np.sign(obs_age)).mean())
            row = {
                **dict(zip(key_cols, key)),
                "model_title": obs["model_title"],
                "question": obs["question"],
                "readable_formula": obs["readable_formula"],
                "robustness_method": method,
                "robustness_label": method_label,
                "observed_age_coef": obs_age,
                "n_fit_replicates": int(len(values)),
                "null_mean_age_coef": float(values.mean()),
                "null_sd_age_coef": float(values.std(ddof=1)) if len(values) > 1 else math.nan,
                "null_q025_age_coef": float(values.quantile(0.025)),
                "null_q500_age_coef": float(values.quantile(0.5)),
                "null_q975_age_coef": float(values.quantile(0.975)),
                "same_sign_share": same_sign,
                "observed_below_null_q025": bool(obs_age < values.quantile(0.025)),
                "observed_above_null_q975": bool(obs_age > values.quantile(0.975)),
                "observed_outside_null_95": bool(obs_age < values.quantile(0.025) or obs_age > values.quantile(0.975)),
                "two_sided_permutation_p": float((np.sum(np.abs(values) >= abs(obs_age)) + 1) / (len(values) + 1))
                if method != "balanced_bootstrap"
                else math.nan,
            }
            rows.append(row)
    return pd.DataFrame(rows)


def make_observed_rows(units: pd.DataFrame, context_ks: Sequence[str]) -> tuple[pd.DataFrame, dict[tuple[str, str, str], pd.DataFrame]]:
    """Fit observed model rows and return model frames for refits."""

    rows: list[dict[str, object]] = []
    frames: dict[tuple[str, str, str], pd.DataFrame] = {}
    for context_k in context_ks:
        for spec in MODEL_SPECS:
            if spec.needs_entropy and context_k == "k0":
                continue
            for effort_col, effort_label in EFFORT_MEASURES:
                frame = model_frame(units, spec, effort_col, context_k)
                frames[(context_k, spec.model_id, effort_col)] = frame
                fit = fit_fast_age_model(frame, spec) if not frame.empty else {"status": "empty", "error": "no complete rows"}
                rows.append(
                    {
                        "context_k": context_k,
                        "model_id": spec.model_id,
                        "model_title": spec.model_title,
                        "question": spec.question,
                        "readable_formula": spec.readable_formula,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "n_units": int(len(frame)),
                        "n_children": int(frame["child_id"].nunique()) if not frame.empty else 0,
                        "n_age_bins": int(frame["age_bin_label"].nunique()) if not frame.empty else 0,
                        "n_utterances": int(frame["n_utterances"].sum()) if not frame.empty else 0,
                        **fit,
                    }
                )
    return pd.DataFrame(rows), frames


def run_all_refits(
    observed: pd.DataFrame,
    frames: Mapping[tuple[str, str, str], pd.DataFrame],
    *,
    n_reps: int,
    balanced_units_per_bin: int,
    seed: int,
) -> pd.DataFrame:
    """Run all robustness refits for observed fit rows."""

    spec_by_id = {spec.model_id: spec for spec in MODEL_SPECS}
    pieces: list[pd.DataFrame] = []
    fit_rows = observed[observed["status"].eq("fit")].copy()
    for idx, row in fit_rows.reset_index(drop=True).iterrows():
        context_k = str(row["context_k"])
        model_id = str(row["model_id"])
        effort_col = str(row["effort_col"])
        frame = frames[(context_k, model_id, effort_col)]
        spec = spec_by_id[model_id]
        reps = robustness_refits(
            frame,
            spec,
            n_reps=n_reps,
            balanced_units_per_bin=balanced_units_per_bin,
            seed=seed + idx * 10_000,
        )
        for col in ["context_k", "model_id", "model_title", "question", "readable_formula", "effort_col", "effort_label"]:
            reps[col] = row[col]
        pieces.append(reps)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def support_tables(rows: pd.DataFrame, units: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return compact support audits."""

    age_support = (
        rows[rows["role"].eq("child") & rows["target_variant"].eq("real")]
        .groupby(["age_bin", "context_k"], observed=True)
        .agg(
            utterance_rows=("sum_bits", "size"),
            children=("child_id", "nunique"),
            sessions=("session_id", "nunique"),
        )
        .reset_index()
    )
    unit_support = (
        units.groupby(["age_bin_label", "context_k"], observed=True)
        .agg(
            units=("unit_id", "nunique"),
            children=("child_id", "nunique"),
            sessions=("child_session_id", "nunique"),
            utterances=("n_utterances", "sum"),
        )
        .reset_index()
    )
    audit = pd.DataFrame(
        [
            {
                "utterance_rows": int(len(rows)),
                "unit_rows": int(len(units)),
                "children": int(units["child_id"].nunique()),
                "datasets": int(units["dataset"].nunique()),
                "child_sessions": int(units["child_session_id"].nunique()),
                "context_windows": ",".join(sorted(units["context_k"].unique())),
                "age_bins": ",".join(str(x) for x in AGE_BIN_ORDER if x in set(units["age_bin_label"])),
            }
        ]
    )
    return audit, age_support, unit_support


def support_tables_from_units(
    units: pd.DataFrame,
    source_audit: pd.DataFrame,
    *,
    source: str,
    source_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return compact support audits from the streamed unit frame."""

    age_support = (
        units.groupby(["age_bin_label", "context_k"], observed=True)
        .agg(
            utterance_rows=("n_utterances", "sum"),
            children=("child_id", "nunique"),
            sessions=("child_session_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"age_bin_label": "age_bin"})
    )
    unit_support = (
        units.groupby(["age_bin_label", "context_k"], observed=True)
        .agg(
            units=("unit_id", "nunique"),
            children=("child_id", "nunique"),
            sessions=("child_session_id", "nunique"),
            utterances=("n_utterances", "sum"),
        )
        .reset_index()
    )
    audit = pd.DataFrame(
        [
            {
                "source": source,
                "source_path": str(source_path),
                "source_files_read": int(len(source_audit)),
                "source_rows_read": int(pd.to_numeric(source_audit.get("rows_read", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()),
                "source_rows_kept": int(pd.to_numeric(source_audit.get("rows_kept", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()),
                "source_rows_dropped": int(pd.to_numeric(source_audit.get("rows_dropped", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()),
                "unit_rows": int(len(units)),
                "children": int(units["child_id"].nunique()),
                "datasets": int(units["dataset"].nunique()),
                "child_sessions": int(units["child_session_id"].nunique()),
                "context_windows": ",".join(sorted(units["context_k"].unique())),
                "age_bins": ",".join(str(x) for x in AGE_BIN_ORDER if x in set(units["age_bin_label"])),
            }
        ]
    )
    return audit, age_support, unit_support


def plot_age_bin_support(unit_support: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot unit support by age bin and context window."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    plot = unit_support.copy()
    plot["age_bin_label"] = pd.Categorical(plot["age_bin_label"], categories=AGE_BIN_ORDER, ordered=True)
    plt.figure(figsize=(11, 5.5))
    sns.barplot(data=plot, x="age_bin_label", y="units", hue="context_k", palette="colorblind")
    plt.xlabel("Age bin")
    plt.ylabel("Child-session-context units")
    plt.title("Unit Support By Age Bin")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    path = fig_dir / "age_bin_unit_support.png"
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_observed_age_slopes(observed: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot observed age coefficients for all fitted models."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    plot = observed[observed["status"].eq("fit")].copy()
    plot["effort_label"] = pd.Categorical(plot["effort_label"], categories=[label for _, label in EFFORT_MEASURES], ordered=True)
    g = sns.relplot(
        data=plot,
        x="model_id",
        y="age_coef",
        hue="effort_label",
        col="context_k",
        kind="scatter",
        col_wrap=2,
        height=3.3,
        aspect=1.35,
        palette="colorblind",
        facet_kws={"sharey": True},
    )
    for ax in g.axes.flat:
        ax.axhline(0, color="#555555", linewidth=0.9, linestyle="--")
        ax.set_xlabel("Model")
        ax.set_ylabel("Observed age slope")
    g.fig.suptitle("Observed Unit-Level Age Slopes", y=1.03)
    path = fig_dir / "observed_age_slope_overview.png"
    g.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(g.fig)
    return path


def plot_robustness_heatmap(summary: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot whether observed age slopes fall outside null intervals."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    plot = summary.copy()
    plot["is_outside"] = plot["observed_outside_null_95"].astype(float)
    grouped = (
        plot.groupby(["model_id", "robustness_method"], observed=True)["is_outside"]
        .mean()
        .reset_index()
        .pivot(index="model_id", columns="robustness_method", values="is_outside")
        .reindex(index=[spec.model_id for spec in MODEL_SPECS], columns=[method for method, _ in ROBUSTNESS_METHODS])
    )
    plt.figure(figsize=(9, 4.8))
    sns.heatmap(grouped, vmin=0, vmax=1, annot=True, fmt=".2f", cmap="viridis", cbar_kws={"label": "Share outside null 95%"})
    plt.xlabel("Robustness method")
    plt.ylabel("Model")
    plt.title("How Often The Real Age Slope Beats The Null")
    plt.tight_layout()
    path = fig_dir / "robustness_outside_null_heatmap.png"
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_bootstrap_ci(summary: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot observed age slopes against balanced-bootstrap intervals."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    boot = summary[summary["robustness_method"].eq("balanced_bootstrap")].copy()
    boot = boot[boot["context_k"].isin(["k0", "k3"])].copy()
    boot["label"] = boot["model_id"] + " | " + boot["effort_label"]
    boot = boot.sort_values(["context_k", "model_id", "effort_label"])
    contexts = list(dict.fromkeys(boot["context_k"].tolist()))
    fig, axes = plt.subplots(1, len(contexts), figsize=(12, max(6, 0.24 * len(boot["label"].unique()))), sharey=True)
    if len(contexts) == 1:
        axes = [axes]
    for ax, context_k in zip(axes, contexts):
        sub = boot[boot["context_k"].eq(context_k)].copy()
        labels = sub["label"].tolist()
        y = np.arange(len(sub))
        ax.hlines(y, sub["null_q025_age_coef"], sub["null_q975_age_coef"], color="#7796b6", linewidth=2)
        ax.scatter(sub["observed_age_coef"], y, color="#c94f4f", s=24, label="observed")
        ax.axvline(0, color="#555555", linewidth=0.8, linestyle="--")
        ax.set_title(context_k)
        ax.set_xlabel("Age slope")
        ax.set_yticks(y)
        ax.set_yticklabels(labels if ax is axes[0] else [])
    axes[0].invert_yaxis()
    fig.suptitle("Observed Age Slopes vs Balanced-Bootstrap 95% Intervals", y=1.01)
    fig.tight_layout()
    path = fig_dir / "balanced_bootstrap_age_slope_ci.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_model_method_panels(summary: pd.DataFrame, fig_dir: Path) -> list[Path]:
    """Write one compact robustness interval plot per model."""

    paths: list[Path] = []
    for spec in MODEL_SPECS:
        sub = summary[summary["model_id"].eq(spec.model_id)].copy()
        if sub.empty:
            continue
        sub = sub[sub["context_k"].isin(["k0", "k3"])].copy() if spec.model_id in {"M1", "M2", "M3"} else sub[sub["context_k"].eq("k3")].copy()
        if sub.empty:
            continue
        sub["row_label"] = sub["context_k"] + " | " + sub["effort_label"] + " | " + sub["robustness_method"]
        sub = sub.sort_values(["context_k", "effort_label", "robustness_method"])
        fig, ax = plt.subplots(figsize=(11, max(5.5, 0.22 * len(sub))))
        y = np.arange(len(sub))
        ax.hlines(y, sub["null_q025_age_coef"], sub["null_q975_age_coef"], color="#8aa9a0", linewidth=1.9, alpha=0.85)
        ax.scatter(sub["observed_age_coef"], y, color="#c76f2c", s=18, label="observed")
        ax.scatter(sub["null_q500_age_coef"], y, color="#2f6f73", s=14, label="null median")
        ax.axvline(0, color="#555555", linewidth=0.8, linestyle="--")
        ax.set_yticks(y)
        ax.set_yticklabels(sub["row_label"])
        ax.invert_yaxis()
        ax.set_xlabel("Age slope")
        ax.set_title(f"{spec.model_id}: {spec.model_title}")
        ax.legend(loc="lower right")
        fig.tight_layout()
        path = fig_dir / f"{spec.model_id.lower()}_age_slope_robustness_intervals.png"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)
    return paths


def slope_line(
    *,
    age_grid: np.ndarray,
    center_age: float,
    center_y: float,
    slope: float,
) -> np.ndarray:
    """Return an anchored effect line for an age coefficient.

    The line is anchored at the observed unit-frame mean so the plot displays
    the slope itself, not arbitrary fixed-effect intercept choices.
    """

    return center_y + slope * (age_grid - center_age)


def model_line_anchor(units: pd.DataFrame, spec: RobustModelSpec, effort_col: str, context_k: str) -> tuple[float, float, pd.DataFrame]:
    """Return age/y anchors and raw bin means for one model view."""

    frame = model_frame(units, spec, effort_col, context_k)
    if frame.empty:
        return math.nan, math.nan, pd.DataFrame()
    raw = (
        frame.groupby("age_bin_label", observed=True)
        .agg(
            age_months=("age_months", "mean"),
            mean_sum_bits=("mean_sum_bits", "mean"),
            units=("unit_id", "nunique"),
        )
        .reset_index()
    )
    return float(frame["age_months"].mean()), float(frame["mean_sum_bits"].mean()), raw


def effect_line_bounds(
    row: pd.Series,
    *,
    age_grid: np.ndarray,
    center_age: float,
    center_y: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return median/lower/upper effect lines from slope quantiles."""

    median = slope_line(
        age_grid=age_grid,
        center_age=center_age,
        center_y=center_y,
        slope=float(row.get("null_q500_age_coef", math.nan)),
    )
    lower = slope_line(
        age_grid=age_grid,
        center_age=center_age,
        center_y=center_y,
        slope=float(row.get("null_q025_age_coef", math.nan)),
    )
    upper = slope_line(
        age_grid=age_grid,
        center_age=center_age,
        center_y=center_y,
        slope=float(row.get("null_q975_age_coef", math.nan)),
    )
    return median, lower, upper


def plot_clear_model_lines(
    units: pd.DataFrame,
    summary: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Create readable regression-line robustness plots for each M1-M6 model."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    age_grid = np.linspace(6, 65, 120)
    effort_pairs = list(EFFORT_MEASURES)
    spec_by_id = {spec.model_id: spec for spec in MODEL_SPECS}
    for spec in MODEL_SPECS:
        contexts = ["k3"] if spec.needs_entropy else ["k0", "k3"]
        fig, axes = plt.subplots(
            nrows=len(contexts) * 2,
            ncols=len(effort_pairs),
            figsize=(20, 6.0 * len(contexts)),
            sharex=True,
            sharey=False,
        )
        if len(contexts) * 2 == 1:
            axes = np.array([axes])
        axes = np.asarray(axes).reshape(len(contexts) * 2, len(effort_pairs))
        for context_idx, context_k in enumerate(contexts):
            for effort_idx, (effort_col, effort_label) in enumerate(effort_pairs):
                center_age, center_y, raw = model_line_anchor(units, spec, effort_col, context_k)
                if not math.isfinite(center_age) or not math.isfinite(center_y):
                    for row_offset in [0, 1]:
                        ax = axes[context_idx * 2 + row_offset, effort_idx]
                        ax.axis("off")
                    continue
                sub = summary[
                    summary["context_k"].eq(context_k)
                    & summary["model_id"].eq(spec.model_id)
                    & summary["effort_col"].eq(effort_col)
                ].copy()
                if sub.empty:
                    for row_offset in [0, 1]:
                        ax = axes[context_idx * 2 + row_offset, effort_idx]
                        ax.axis("off")
                    continue
                obs_slope = float(sub["observed_age_coef"].iloc[0])
                observed_line = slope_line(
                    age_grid=age_grid,
                    center_age=center_age,
                    center_y=center_y,
                    slope=obs_slope,
                )

                ax_boot = axes[context_idx * 2, effort_idx]
                boot = sub[sub["robustness_method"].eq("balanced_bootstrap")]
                if not boot.empty:
                    median, lower, upper = effect_line_bounds(
                        boot.iloc[0],
                        age_grid=age_grid,
                        center_age=center_age,
                        center_y=center_y,
                    )
                    ax_boot.fill_between(age_grid, lower, upper, color="#6c8fb3", alpha=0.22, linewidth=0)
                    ax_boot.plot(age_grid, median, color="#6c8fb3", linewidth=1.5, linestyle="--", label="balanced bootstrap median")
                ax_boot.plot(age_grid, observed_line, color="#b9473f", linewidth=2.2, label="observed age effect")
                if not raw.empty:
                    ax_boot.scatter(raw["age_months"], raw["mean_sum_bits"], s=np.clip(raw["units"] * 1.7, 12, 70), color="#777777", alpha=0.45, label="raw age-bin mean")
                ax_boot.axhline(center_y, color="#dddddd", linewidth=0.8)
                ax_boot.set_title(effort_label)
                ax_boot.set_ylabel(f"{context_k}\nbalanced")
                ax_boot.grid(alpha=0.18)

                ax_null = axes[context_idx * 2 + 1, effort_idx]
                null_colors = {
                    "age_bin_group_scramble": "#725aa5",
                    "unit_age_scramble": "#d28b36",
                    "within_child_age_scramble": "#2f8f6f",
                }
                null_labels = {
                    "age_bin_group_scramble": "bin-label scramble",
                    "unit_age_scramble": "unit-age scramble",
                    "within_child_age_scramble": "within-child scramble",
                }
                for method, color in null_colors.items():
                    null = sub[sub["robustness_method"].eq(method)]
                    if null.empty:
                        continue
                    median, lower, upper = effect_line_bounds(
                        null.iloc[0],
                        age_grid=age_grid,
                        center_age=center_age,
                        center_y=center_y,
                    )
                    ax_null.fill_between(age_grid, lower, upper, color=color, alpha=0.12, linewidth=0)
                    ax_null.plot(age_grid, median, color=color, linewidth=1.25, linestyle="--", label=null_labels[method])
                ax_null.plot(age_grid, observed_line, color="#b9473f", linewidth=2.2, label="observed age effect")
                if not raw.empty:
                    ax_null.scatter(raw["age_months"], raw["mean_sum_bits"], s=np.clip(raw["units"] * 1.7, 12, 70), color="#777777", alpha=0.35)
                ax_null.axhline(center_y, color="#dddddd", linewidth=0.8)
                ax_null.set_ylabel(f"{context_k}\nscrambled")
                ax_null.set_xlabel("Age in months")
                ax_null.grid(alpha=0.18)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        null_handles, null_labels = axes[min(1, axes.shape[0] - 1), 0].get_legend_handles_labels()
        label_to_handle = {label: handle for handle, label in zip([*handles, *null_handles], [*labels, *null_labels])}
        fig.legend(
            label_to_handle.values(),
            label_to_handle.keys(),
            loc="lower center",
            bbox_to_anchor=(0.5, -0.01),
            ncol=3,
            frameon=False,
        )
        fig.tight_layout(rect=[0, 0.05, 1, 1])
        path = fig_dir / f"{spec.model_id.lower()}_clear_robustness_regression_lines.png"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        rows.append(
            {
                "figure_id": path.stem,
                "path": str(path),
                "model_id": spec.model_id,
                "description": "Readable observed-vs-bootstrap and observed-vs-scrambled age-effect regression lines.",
            }
        )
    return pd.DataFrame(rows)


def build_figures(
    observed: pd.DataFrame,
    summary: pd.DataFrame,
    unit_support: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Build all report figures and return a manifest."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "figure_id": "age_bin_unit_support",
            "path": str(plot_age_bin_support(unit_support, fig_dir)),
            "description": "Child-session-context unit support by age bin and context window.",
        },
        {
            "figure_id": "observed_age_slope_overview",
            "path": str(plot_observed_age_slopes(observed, fig_dir)),
            "description": "Observed unit-level age slopes across models, effort units, and context windows.",
        },
        {
            "figure_id": "robustness_outside_null_heatmap",
            "path": str(plot_robustness_heatmap(summary, fig_dir)),
            "description": "Share of fitted rows where the observed age slope is outside the null 95% interval.",
        },
        {
            "figure_id": "balanced_bootstrap_age_slope_ci",
            "path": str(plot_bootstrap_ci(summary, fig_dir)),
            "description": "Observed age slopes compared with balanced-bootstrap 95% intervals.",
        },
    ]
    for path in plot_model_method_panels(summary, fig_dir):
        rows.append(
            {
                "figure_id": path.stem,
                "path": str(path),
                "description": "Per-model age-slope intervals for bootstrap and age-scrambling checks.",
            }
        )
    return pd.DataFrame(rows)


def build_age_scrambling_analysis(
    *,
    source: str = DEFAULT_SOURCE,
    input_csv: Path = DEFAULT_INPUT,
    scored_root: Path = DEFAULT_MAIN_SCORED_ROOT,
    entropy_features_csv: Path = DEFAULT_ENTROPY_FEATURES,
    unit_frame_input: Path = DEFAULT_UNIT_FRAME_INPUT,
    score_source: str = "pbm_mistral_patched_006_023",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
    context_ks: Sequence[str] = DEFAULT_CONTEXT_KS,
    chunksize: int = 500_000,
    n_reps: int = DEFAULT_REPLICATES,
    balanced_units_per_bin: int = DEFAULT_BALANCED_UNITS_PER_BIN,
    seed: int = SEED,
) -> dict[str, Path]:
    """Run the full robustness analysis and write artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    if source == "scored-tree":
        units, source_audit = build_units_from_scored_tree(
            scored_root=scored_root,
            score_source=score_source,
            entropy_features_csv=entropy_features_csv,
            context_ks=context_ks,
        )
        audit, age_support, unit_support = support_tables_from_units(
            units,
            source_audit,
            source=source,
            source_path=scored_root,
        )
    elif source == "unit-frame":
        units = read_existing_unit_frame(unit_frame_input, context_ks=context_ks)
        source_audit = pd.DataFrame(
            [
                {
                    "source": source,
                    "scored_file": str(unit_frame_input),
                    "rows_read": int(len(units)),
                    "rows_kept": int(len(units)),
                    "rows_dropped": 0,
                    "entropy_matched_rows": int(units["mean_context_entropy_bits"].notna().sum()),
                    "entropy_missing_rows": int(units["mean_context_entropy_bits"].isna().sum()),
                }
            ]
        )
        audit, age_support, unit_support = support_tables_from_units(
            units,
            source_audit,
            source=source,
            source_path=unit_frame_input,
        )
    elif source == "long-table":
        rows = read_real_child_rows(input_csv, context_ks=context_ks, chunksize=chunksize)
        units = aggregate_to_units(rows)
        source_audit = pd.DataFrame(
            [
                {
                    "source": source,
                    "scored_file": str(input_csv),
                    "rows_read": int(len(rows)),
                    "rows_kept": int(len(rows)),
                    "rows_dropped": 0,
                    "entropy_matched_rows": int(pd.to_numeric(rows.get("context_entropy_bits", pd.Series(dtype=float)), errors="coerce").notna().sum()),
                    "entropy_missing_rows": int(pd.to_numeric(rows.get("context_entropy_bits", pd.Series(dtype=float)), errors="coerce").isna().sum()),
                }
            ]
        )
        audit, age_support, unit_support = support_tables(rows, units)
        audit.insert(0, "source", source)
        audit.insert(1, "source_path", str(input_csv))
    else:
        raise ValueError(f"unknown source {source!r}; expected 'scored-tree', 'unit-frame', or 'long-table'")
    observed, frames = make_observed_rows(units, context_ks)
    replicates = run_all_refits(
        observed,
        frames,
        n_reps=n_reps,
        balanced_units_per_bin=balanced_units_per_bin,
        seed=seed,
    )
    summary = summarize_replicates(observed, replicates)
    figure_manifest = build_figures(observed, summary, unit_support, fig_dir)

    paths = {
        "unit_frame": output_dir / "age_scrambling_unit_frame.csv.gz",
        "audit": output_dir / "age_scrambling_audit.csv",
        "source_audit": output_dir / "age_scrambling_source_file_audit.csv",
        "age_support": output_dir / "age_scrambling_age_support.csv",
        "unit_support": output_dir / "age_scrambling_unit_support.csv",
        "observed": output_dir / "age_scrambling_observed_model_summary.csv",
        "replicates": output_dir / "age_scrambling_replicate_age_slopes.csv.gz",
        "summary": output_dir / "age_scrambling_robustness_summary.csv",
        "figures": output_dir / "age_scrambling_figure_manifest.csv",
    }
    units.to_csv(paths["unit_frame"], index=False)
    audit.to_csv(paths["audit"], index=False)
    source_audit.to_csv(paths["source_audit"], index=False)
    age_support.to_csv(paths["age_support"], index=False)
    unit_support.to_csv(paths["unit_support"], index=False)
    observed.to_csv(paths["observed"], index=False)
    replicates.to_csv(paths["replicates"], index=False)
    summary.to_csv(paths["summary"], index=False)
    figure_manifest.to_csv(paths["figures"], index=False)
    return paths


def read_required_csv(path: Path) -> pd.DataFrame:
    """Read a required CSV with a clear error."""

    if not path.exists():
        raise FileNotFoundError(f"Missing required robustness artifact: {path}")
    return pd.read_csv(path)


def image_md(path: str | Path, alt: str) -> str:
    """Return Markdown image syntax."""

    path = Path(path)
    if not path.exists():
        return f"_Missing plot: `{path}`_"
    return f"![{alt}](../{path.as_posix()})"


def compact_takeaway_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Return one compact row per model/method summarizing robustness."""

    out = (
        summary.groupby(["model_id", "robustness_method"], observed=True)
        .agg(
            rows=("observed_age_coef", "size"),
            negative_observed=("observed_age_coef", lambda values: int((pd.to_numeric(values, errors="coerce") < 0).sum())),
            outside_null_95=("observed_outside_null_95", "sum"),
            mean_same_sign_share=("same_sign_share", "mean"),
            median_permutation_p=("two_sided_permutation_p", "median"),
        )
        .reset_index()
    )
    out["outside_null_95"] = out["outside_null_95"].astype(int)
    out["median_permutation_p"] = out["median_permutation_p"].map(lambda value: "" if pd.isna(value) else format_p(value))
    return out


def source_context_summary(source_audit: pd.DataFrame) -> pd.DataFrame:
    """Summarize streamed source-file coverage by context window."""

    if source_audit.empty or "context_k" not in source_audit.columns:
        return source_audit
    numeric_cols = ["rows_read", "rows_kept", "rows_dropped", "entropy_matched_rows", "entropy_missing_rows"]
    out = (
        source_audit.groupby("context_k", observed=True)
        .agg(
            files=("scored_file", "nunique"),
            **{col: (col, "sum") for col in numeric_cols if col in source_audit.columns},
        )
        .reset_index()
    )
    return out


def robustness_card_table(summary: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return one small readable table for a model card."""

    preferred_contexts = ["k3"] if model_id in {"M4", "M5", "M6"} else ["k0", "k3"]
    sub = summary[summary["model_id"].eq(model_id) & summary["context_k"].isin(preferred_contexts)].copy()
    rows: list[dict[str, object]] = []
    for (context_k, effort_label), group in sub.groupby(["context_k", "effort_label"], observed=True):
        boot = group[group["robustness_method"].eq("balanced_bootstrap")]
        bin_scramble = group[group["robustness_method"].eq("age_bin_group_scramble")]
        unit_scramble = group[group["robustness_method"].eq("unit_age_scramble")]
        child_scramble = group[group["robustness_method"].eq("within_child_age_scramble")]
        if boot.empty:
            continue
        boot_row = boot.iloc[0]
        rows.append(
            {
                "context": context_k,
                "effort": effort_label,
                "observed age slope": float(boot_row["observed_age_coef"]),
                "balanced 95% slope interval": (
                    f"[{float(boot_row['null_q025_age_coef']):.3g}, "
                    f"{float(boot_row['null_q975_age_coef']):.3g}]"
                ),
                "balanced same-sign": float(boot_row["same_sign_share"]),
                "bin-label scramble p": "" if bin_scramble.empty else format_p(bin_scramble.iloc[0]["two_sided_permutation_p"]),
                "unit-age scramble p": "" if unit_scramble.empty else format_p(unit_scramble.iloc[0]["two_sided_permutation_p"]),
                "within-child scramble p": "" if child_scramble.empty else format_p(child_scramble.iloc[0]["two_sided_permutation_p"]),
            }
        )
    return pd.DataFrame(rows)


def selected_result_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Return a readable subset of robustness rows for the report."""

    cols = [
        "context_k",
        "model_id",
        "effort_label",
        "robustness_method",
        "observed_age_coef",
        "null_q025_age_coef",
        "null_q500_age_coef",
        "null_q975_age_coef",
        "same_sign_share",
        "two_sided_permutation_p",
        "observed_outside_null_95",
    ]
    out = summary[cols].copy()
    out = out[out["context_k"].isin(["k0", "k3"])]
    out["two_sided_permutation_p"] = out["two_sided_permutation_p"].map(lambda value: "" if pd.isna(value) else format_p(value))
    return out.sort_values(["model_id", "context_k", "effort_label", "robustness_method"])


def model_sections(summary: pd.DataFrame, figure_manifest: pd.DataFrame) -> str:
    """Return report sections for M1-M6."""

    lines: list[str] = []
    figure_paths = {row["figure_id"]: row["path"] for row in figure_manifest.to_dict("records")}
    for spec in MODEL_SPECS:
        sub = summary[summary["model_id"].eq(spec.model_id)].copy()
        if sub.empty:
            continue
        card = robustness_card_table(summary, spec.model_id)
        negative_share = float((pd.to_numeric(sub["observed_age_coef"], errors="coerce") < 0).mean())
        outside_share = float(sub["observed_outside_null_95"].astype(bool).mean())
        plot_id = f"{spec.model_id.lower()}_clear_robustness_regression_lines"
        lines.append(
            f"""## {spec.model_id}: {spec.model_title}

**Question.** {spec.question}

**Formula.** `{spec.readable_formula}`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

{image_md(figure_paths.get(plot_id, ""), f"{spec.model_id} clear robustness regression lines")}

**Quick read.** Across all fitted variants for this model,
{negative_share:.0%} of observed age slopes are negative, and
{outside_share:.0%} of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

{markdown_table(card, max_rows=20)}

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.
"""
        )
    return "\n".join(lines)


def build_age_scrambling_markdown(output_dir: Path, fig_dir: Path) -> str:
    """Build the Markdown report from saved artifacts."""

    audit = read_required_csv(output_dir / "age_scrambling_audit.csv")
    source_audit = read_required_csv(output_dir / "age_scrambling_source_file_audit.csv")
    units = pd.read_csv(output_dir / "age_scrambling_unit_frame.csv.gz")
    unit_support = read_required_csv(output_dir / "age_scrambling_unit_support.csv")
    observed = read_required_csv(output_dir / "age_scrambling_observed_model_summary.csv")
    summary = read_required_csv(output_dir / "age_scrambling_robustness_summary.csv")
    figure_manifest = read_required_csv(output_dir / "age_scrambling_figure_manifest.csv")
    clear_figures = plot_clear_model_lines(units, summary, fig_dir)
    if not clear_figures.empty:
        figure_manifest = pd.concat([figure_manifest, clear_figures], ignore_index=True)
        clear_figures.to_csv(output_dir / "age_scrambling_clear_figure_manifest.csv", index=False)
    figure_paths = {row["figure_id"]: row["path"] for row in figure_manifest.to_dict("records")}
    model_map = pd.DataFrame(
        [
            {
                "model_id": spec.model_id,
                "question": spec.question,
                "formula": spec.readable_formula,
                "context_windows": "k0-k3" if not spec.needs_entropy else "k1-k3 only",
            }
            for spec in MODEL_SPECS
        ]
    )
    methods = pd.DataFrame(METHOD_EXPLANATIONS, columns=["method", "meaning"])
    observed_compact = observed[
        [
            "context_k",
            "model_id",
            "effort_label",
            "n_units",
            "n_children",
            "n_age_bins",
            "age_coef",
            "r2_observed_fitted",
            "status",
        ]
    ].copy()
    observed_compact = observed_compact[observed_compact["context_k"].isin(["k0", "k3"])]
    source_by_context = source_context_summary(source_audit)
    method_short = pd.DataFrame(
        [
            {
                "check": "balanced bootstrap",
                "what it asks": "Does the age effect survive when every age bin contributes the same number of units?",
                "what would reassure us": "The real slope keeps the same direction and sits away from zero.",
            },
            {
                "check": "age-bin label scramble",
                "what it asks": "Could the trend appear if whole age-bin labels were assigned to the wrong bins?",
                "what would reassure us": "The real slope is stronger than these scrambled slopes.",
            },
            {
                "check": "unit-age scramble",
                "what it asks": "Could the trend appear after randomly disconnecting units from their true ages?",
                "what would reassure us": "The real slope is stronger than these scrambled slopes.",
            },
            {
                "check": "within-child age scramble",
                "what it asks": "Could the trend appear from child-specific style alone if each child's timeline is broken?",
                "what would reassure us": "The real slope is stronger than this within-child null.",
            },
        ]
    )
    md = f"""# Age-Trajectory Robustness: Balanced Bootstrap and Scrambling Controls

This is a complementary validation report for the utterance-level information
models. It asks a very specific question:

```text
Do the developmental age effects survive equalized age-bin sampling, and do
they weaken when we deliberately break the true age ordering?
```

This report does not replace the main M1-M6 model reports and it does not
modify any source data.

The design is inspired by Pawar and Cychosz (2025), who used equalized
age-bin samples and age-label scrambling controls to test whether a
developmental informativity trajectory was real rather than an artifact of bin
composition.

## Data And Unit

The analysis uses real child utterances only, then aggregates them to:

```text
child x session x context window
```

This is intentional. The scrambling tests should not pretend that millions of
utterance rows are independent. Each unit stores the mean total bits,
mean effort, mean context entropy when available, and the number of utterances
that contributed to that unit.

The default data path streams the split scored-result tree file by file and
then writes the compact unit frame. Future refits can use that unit frame
directly instead of rereading the scored files.

## Audit Summary

{markdown_table(audit)}

### Source Coverage By Context Window

{markdown_table(source_by_context, max_rows=20)}

**How to read this table.** `rows_read` is the number of scored real-child
utterance rows found in the split files. `rows_kept` is the number retained
before aggregation. `rows_dropped` should be zero. `entropy_matched_rows`
applies to k1-k3; k0 intentionally has no context entropy because no context is
provided.

{image_md(figure_paths.get("age_bin_unit_support", ""), "age-bin unit support")}

**How to read this plot.** Bars show how many child-session-context units are
available in each age bin. This makes clear where the developmental trajectory
has strong or weak support.

## Robustness Checks

{markdown_table(method_short, max_rows=10)}

## Model Map

{markdown_table(model_map, max_rows=10)}

## Overview Plot

{image_md(figure_paths.get("observed_age_slope_overview", ""), "observed age slope overview")}

**How to read this plot.** Each point is an observed age coefficient from a
unit-level model. Negative values mean predicted total Mistral bits decrease
with age after the model's controls. This is a map of the results; the model
sections below give the interpretable regression-line views.

## Compact Robustness Summary

{markdown_table(compact_takeaway_table(summary), max_rows=40)}

**How to read this table.** `outside_null_95` counts how many
model/effort/context rows had a real observed age coefficient outside the
2.5%-97.5% interval of the bootstrap or scrambling distribution. Higher values
mean the real age slope is less compatible with that null check.
`same_sign_share` is most useful for the balanced bootstrap: values near 1 mean
the age slope direction is stable under balanced age-bin resampling.

## Model Cards

The line plots below are effect-line visualizations. The underlying data are
not changed. Each line is anchored at the observed mean of the unit frame and
uses the fitted age coefficient to show the age effect. This avoids arbitrary
fixed-effect intercept choices while making the slope visually readable.

{model_sections(summary, figure_manifest)}

## Diagnostic Appendix

The following two plots are compact diagnostics for checking all models at
once. They are useful for debugging and overview, but the model-card plots
above are the primary human-readable views.

{image_md(figure_paths.get("robustness_outside_null_heatmap", ""), "robustness heatmap")}

{image_md(figure_paths.get("balanced_bootstrap_age_slope_ci", ""), "balanced bootstrap age slope intervals")}

### Compact Observed Model Rows

{markdown_table(observed_compact, max_rows=80)}

**How to read this table.** `age_coef` is the model's age slope. `r2` is the
share of unit-level variance explained by the fitted values in that model row.
This table is intentionally compact; full replicate slopes are saved as CSV.

## Files

- Unit-level frame: `{output_dir / "age_scrambling_unit_frame.csv.gz"}`
- Source-file audit: `{output_dir / "age_scrambling_source_file_audit.csv"}`
- Observed fits: `{output_dir / "age_scrambling_observed_model_summary.csv"}`
- Replicate slopes: `{output_dir / "age_scrambling_replicate_age_slopes.csv.gz"}`
- Robustness summary: `{output_dir / "age_scrambling_robustness_summary.csv"}`
- Figures: `{fig_dir}`
"""
    return md


def build_age_scrambling_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
    md_path: Path = DEFAULT_DOC_MD,
    html_path: Path = DEFAULT_DOC_HTML,
) -> dict[str, Path]:
    """Render Markdown and HTML from existing analysis artifacts."""

    md = build_age_scrambling_markdown(output_dir, fig_dir)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {"md": md_path, "html": html_path}


def build_age_scrambling_full(
    *,
    source: str = DEFAULT_SOURCE,
    input_csv: Path = DEFAULT_INPUT,
    scored_root: Path = DEFAULT_MAIN_SCORED_ROOT,
    entropy_features_csv: Path = DEFAULT_ENTROPY_FEATURES,
    unit_frame_input: Path = DEFAULT_UNIT_FRAME_INPUT,
    score_source: str = "pbm_mistral_patched_006_023",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
    md_path: Path = DEFAULT_DOC_MD,
    html_path: Path = DEFAULT_DOC_HTML,
    context_ks: Sequence[str] = DEFAULT_CONTEXT_KS,
    chunksize: int = 500_000,
    n_reps: int = DEFAULT_REPLICATES,
    balanced_units_per_bin: int = DEFAULT_BALANCED_UNITS_PER_BIN,
    seed: int = SEED,
) -> dict[str, Path]:
    """Run analysis and render report."""

    paths = build_age_scrambling_analysis(
        source=source,
        input_csv=input_csv,
        scored_root=scored_root,
        entropy_features_csv=entropy_features_csv,
        unit_frame_input=unit_frame_input,
        score_source=score_source,
        output_dir=output_dir,
        fig_dir=fig_dir,
        context_ks=context_ks,
        chunksize=chunksize,
        n_reps=n_reps,
        balanced_units_per_bin=balanced_units_per_bin,
        seed=seed,
    )
    paths.update(build_age_scrambling_report(output_dir=output_dir, fig_dir=fig_dir, md_path=md_path, html_path=html_path))
    return paths


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["analysis", "report", "full"], default="full")
    parser.add_argument("--source", choices=["scored-tree", "unit-frame", "long-table"], default=DEFAULT_SOURCE)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--scored-root", type=Path, default=DEFAULT_MAIN_SCORED_ROOT)
    parser.add_argument("--entropy-features-csv", type=Path, default=DEFAULT_ENTROPY_FEATURES)
    parser.add_argument("--unit-frame-input", type=Path, default=DEFAULT_UNIT_FRAME_INPUT)
    parser.add_argument("--score-source", default="pbm_mistral_patched_006_023")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--context-ks", default=",".join(DEFAULT_CONTEXT_KS))
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--n-reps", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--balanced-units-per-bin", type=int, default=DEFAULT_BALANCED_UNITS_PER_BIN)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)
    context_ks = split_csv(args.context_ks)
    if args.stage == "analysis":
        paths = build_age_scrambling_analysis(
            source=args.source,
            input_csv=args.input,
            scored_root=args.scored_root,
            entropy_features_csv=args.entropy_features_csv,
            unit_frame_input=args.unit_frame_input,
            score_source=args.score_source,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            context_ks=context_ks,
            chunksize=args.chunksize,
            n_reps=args.n_reps,
            balanced_units_per_bin=args.balanced_units_per_bin,
            seed=args.seed,
        )
    elif args.stage == "report":
        paths = build_age_scrambling_report(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            md_path=args.md,
            html_path=args.html,
        )
    else:
        paths = build_age_scrambling_full(
            source=args.source,
            input_csv=args.input,
            scored_root=args.scored_root,
            entropy_features_csv=args.entropy_features_csv,
            unit_frame_input=args.unit_frame_input,
            score_source=args.score_source,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            md_path=args.md,
            html_path=args.html,
            context_ks=context_ks,
            chunksize=args.chunksize,
            n_reps=args.n_reps,
            balanced_units_per_bin=args.balanced_units_per_bin,
            seed=args.seed,
        )
    for label, path in paths.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
