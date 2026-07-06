#!/usr/bin/env python3
"""Build the first Route 2 response-space table.

This joins actual real-child k3 utterance rows to the compact response-space
entropy and generated-response effort summaries produced in ``compute_surprisal_mila``.
It does not read the 26.8M generated samples and it does not score anything.
"""

from __future__ import annotations

import argparse
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

try:
    from build_response_entropy_manifest import context_id, normalize_context
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_response_entropy_manifest import context_id, normalize_context


DEFAULT_ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
DEFAULT_MILA_MERGED_DIR = Path(
    "../compute_surprisal_mila/mila_results/response_entropy_generation/20260618_164333/merged"
)
DEFAULT_OUTPUT = Path("results/route2_response_space/route2_child_response_space_effort_table.csv.gz")
DEFAULT_AUDIT_DIR = Path("results/route2_response_space")
DEFAULT_ROUTE1_CACHE = DEFAULT_AUDIT_DIR / "route2_real_child_k3_base_rows.csv.gz"
DEFAULT_EXCLUDED_ROUTE1_CACHE = DEFAULT_AUDIT_DIR / "route2_real_child_k3_excluded_empty_context_rows.csv.gz"
DEFAULT_PROMPT_VARIANT = "Caregiver"
DEFAULT_TEMPERATURE = 0.5

ROUTE1_USECOLS = [
    "score_source",
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "age_months_source",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "speaker",
    "role",
    "target_variant",
    "target_column",
    "target_utterance_clean",
    "target_text_hash",
    "context_condition",
    "context_k",
    "context_col_used",
    "context_text",
    "context_text_hash",
    "mean_bits_per_token",
    "sum_bits",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "effort_quality_flags",
    "model_used",
    "units_used",
    "text_cols_used",
    "context_entropy_join_status",
    "context_entropy_context_id",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "context_next_top5_mass",
    "context_next_top10_mass",
    "context_next_top50_mass",
    "context_next_argmax_bits",
    "context_entropy_model_used",
    "context_entropy_dtype_used",
    "context_entropy_max_length_used",
    "context_entropy_seed_used",
]

ROUTE1_NUMERIC_COLS = [
    "session_id",
    "age_months",
    "line_no",
    "utt_id",
    "mean_bits_per_token",
    "sum_bits",
    "n_eval_tokens",
    "bits_per_word",
    "bits_per_morpheme",
    "bits_per_syllable_cmu_or_pkg",
    "bits_per_syllable_pkg",
    "bits_per_phoneme",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
    "cmu_oov_word_count",
    "syllable_pkg_fallback_word_count",
    "g2p_fallback_word_count",
    "context_entropy_token_count",
    "context_entropy_bits",
    "context_next_top1_prob",
    "context_next_top5_mass",
    "context_next_top10_mass",
    "context_next_top50_mass",
    "context_next_argmax_bits",
]

ENTROPY_REQUIRED_COLS = {
    "setting_id",
    "context_id",
    "context_text",
    "prompt_variant",
    "temperature",
    "selected_sample_count",
    "valid_selected_count",
    "invalid_selected_count",
    "unique_response_count_valid_only",
    "empirical_response_entropy_bits_valid_only",
    "miller_madow_entropy_bits_valid_only",
}

ENTROPY_KEEP_RENAME = {
    "setting_id": "response_entropy_setting_id",
    "prompt_variant": "response_entropy_prompt_variant",
    "temperature": "response_entropy_temperature",
    "target_valid_samples": "response_target_valid_samples",
    "max_attempts_per_setting": "response_max_attempts_per_setting",
    "attempts": "response_attempts",
    "accepted_valid_samples": "response_accepted_valid_samples",
    "invalid_attempts": "response_invalid_attempts",
    "selected_samples": "response_selected_samples_reported",
    "invalid_fallback_selected": "response_invalid_fallback_selected_count",
    "reached_target_valid_samples": "response_reached_target_valid_samples",
    "exhausted_attempt_cap": "response_exhausted_attempt_cap",
    "fallback_used": "response_fallback_used",
    "rejection_rate": "response_rejection_rate",
    "selected_sample_count": "response_selected_sample_count",
    "valid_selected_count": "response_valid_selected_count",
    "invalid_selected_count": "response_invalid_selected_count",
    "unique_response_count_selected": "response_unique_response_count_selected",
    "unique_response_count_valid_only": "response_unique_response_count",
    "empirical_response_entropy_bits_selected": "response_entropy_empirical_bits_selected",
    "miller_madow_entropy_bits_selected": "response_entropy_bits_selected",
    "empirical_response_entropy_bits_valid_only": "response_entropy_empirical_bits",
    "miller_madow_entropy_bits_valid_only": "response_entropy_bits",
    "top_response_text_selected": "response_top_response_text_selected",
    "top_response_count_selected": "response_top_response_count_selected",
    "top_response_probability_selected": "response_top_probability_selected",
    "mean_sample_words_selected": "response_mean_sample_words_selected",
    "mean_sample_characters_selected": "response_mean_sample_characters_selected",
}

EFFORT_EXCLUDE_COLS = {
    "context_text",
    "valid_response_type_counts_json",
    "selected_word_count_hist_json",
}

EFFORT_BOOL_COLS = {
    "reached_target_valid_samples",
    "exhausted_attempt_cap",
    "fallback_used",
}


def numeric_temperature_match(series: pd.Series, temperature: float) -> pd.Series:
    """Return rows whose numeric temperature equals ``temperature``."""

    parsed = pd.to_numeric(series, errors="coerce")
    return (parsed - float(temperature)).abs() < 1e-9


def coerce_numeric_columns(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Convert present columns to numeric values in place and return ``frame``."""

    for col in columns:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def coerce_bool_columns(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Convert present columns to pandas BooleanDtype values in place."""

    truthy = {"1", "true", "t", "yes", "y"}
    falsy = {"0", "false", "f", "no", "n", ""}
    for col in columns:
        if col not in frame.columns:
            continue
        values = frame[col].astype(str).str.strip().str.lower()
        frame[col] = values.map(lambda value: True if value in truthy else (False if value in falsy else pd.NA)).astype(
            "boolean"
        )
    return frame


def require_columns(frame: pd.DataFrame, required: set[str], *, label: str) -> None:
    """Raise a clear error if ``frame`` is missing required columns."""

    missing = required - set(frame.columns)
    if missing:
        raise KeyError(f"{label} missing required columns: {sorted(missing)}")


def validate_unique_contexts(frame: pd.DataFrame, *, label: str) -> None:
    """Ensure the filtered context-level table has at most one row per context."""

    duplicates = frame["response_entropy_context_id"].duplicated(keep=False)
    if duplicates.any():
        examples = frame.loc[duplicates, "response_entropy_context_id"].head(10).tolist()
        raise ValueError(f"{label} has duplicate context ids after prompt/temperature filtering: {examples}")


def context_text_id_mismatches(frame: pd.DataFrame) -> int:
    """Count rows whose shipped context id does not match normalized context text."""

    if "context_text" not in frame.columns:
        return 0
    normalized_ids = frame["context_text"].map(context_id)
    return int((frame["context_id"].astype(str) != normalized_ids.astype(str)).sum())


def load_entropy_features(path: Path, *, prompt_variant: str, temperature: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load response entropy features for one prompt/temperature setting."""

    features = pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)
    require_columns(features, ENTROPY_REQUIRED_COLS, label=str(path))
    all_rows = len(features)
    mismatches = context_text_id_mismatches(features)
    filtered = features[
        features["prompt_variant"].astype(str).eq(prompt_variant)
        & numeric_temperature_match(features["temperature"], temperature)
    ].copy()
    if filtered.empty:
        raise RuntimeError(f"no response entropy rows for prompt={prompt_variant!r}, temperature={temperature}")

    keep = ["context_id", *[col for col in ENTROPY_KEEP_RENAME if col in filtered.columns]]
    out = filtered[keep].rename(columns={"context_id": "response_entropy_context_id", **ENTROPY_KEEP_RENAME})
    entropy_non_numeric = {
        "response_entropy_context_id",
        "response_entropy_setting_id",
        "response_entropy_prompt_variant",
        "response_top_response_text_selected",
        "response_reached_target_valid_samples",
        "response_exhausted_attempt_cap",
        "response_fallback_used",
    }
    coerce_numeric_columns(
        out,
        [col for col in out.columns if col.startswith("response_") and col not in entropy_non_numeric],
    )
    coerce_bool_columns(
        out,
        [
            "response_reached_target_valid_samples",
            "response_exhausted_attempt_cap",
            "response_fallback_used",
        ],
    )
    validate_unique_contexts(out, label=str(path))
    audit = {
        "entropy_rows_all_prompts_temperatures": all_rows,
        "entropy_rows_filtered": len(out),
        "entropy_context_id_text_mismatches_all": mismatches,
    }
    return out, audit


def effort_output_columns(frame: pd.DataFrame) -> list[str]:
    """Choose generated-effort columns to attach to each child row."""

    cols: list[str] = []
    for col in frame.columns:
        if col in EFFORT_EXCLUDE_COLS:
            continue
        if col == "context_id":
            cols.append(col)
            continue
        if col in {"setting_id", "prompt_variant", "temperature"}:
            cols.append(col)
            continue
        if col.endswith("_json") and col not in {
            "valid_word_count_hist_json",
            "invalid_selected_rejection_reason_counts_json",
        }:
            continue
        if col in {"shard_index", "context_word_count", "context_k_values", "datasets", "child_ids", "child_count", "n_target_rows"}:
            cols.append(col)
            continue
        if col.startswith(("valid_", "selected_", "invalid_", "target_", "max_", "attempts", "accepted_", "rejection_", "reached_", "exhausted_", "fallback_")):
            cols.append(col)
    return cols


def load_generated_effort_summary(
    path: Path,
    *,
    prompt_variant: str,
    temperature: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load generated-response effort summaries for one prompt/temperature."""

    effort = pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)
    required = {"context_id", "context_text", "prompt_variant", "temperature", "valid_sample_words_mean"}
    require_columns(effort, required, label=str(path))
    all_rows = len(effort)
    mismatches = context_text_id_mismatches(effort)
    filtered = effort[
        effort["prompt_variant"].astype(str).eq(prompt_variant)
        & numeric_temperature_match(effort["temperature"], temperature)
    ].copy()
    if filtered.empty:
        raise RuntimeError(f"no generated effort rows for prompt={prompt_variant!r}, temperature={temperature}")

    keep = effort_output_columns(filtered)
    out = filtered[keep].copy()
    rename = {
        col: f"generated_{col}"
        for col in out.columns
        if col != "context_id"
    }
    out = out.rename(columns={"context_id": "response_entropy_context_id", **rename})
    numeric_cols = [
        col
        for col in out.columns
        if col.startswith("generated_")
        and not col.endswith("_json")
        and col
        not in {
            "generated_setting_id",
            "generated_prompt_variant",
            "generated_context_k_values",
            "generated_datasets",
            "generated_child_ids",
            "generated_reached_target_valid_samples",
            "generated_exhausted_attempt_cap",
            "generated_fallback_used",
            "generated_invalid_selected_top_rejection_reason",
        }
    ]
    coerce_numeric_columns(out, numeric_cols)
    coerce_bool_columns(out, [f"generated_{col}" for col in EFFORT_BOOL_COLS])
    validate_unique_contexts(out, label=str(path))
    audit = {
        "generated_effort_rows_all_prompts_temperatures": all_rows,
        "generated_effort_rows_filtered": len(out),
        "generated_effort_context_id_text_mismatches_all": mismatches,
    }
    return out, audit


def iter_route1_real_child_rows(
    path: Path,
    *,
    chunksize: int,
    progress: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Stream the Route 1 long table and keep actual real-child k3 rows."""

    available_cols = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [col for col in ROUTE1_USECOLS if col in available_cols]
    missing = sorted(set(["score_id", "utterance_id", "role", "target_variant", "context_k", "context_text", "nb_words"]) - set(usecols))
    if missing:
        raise KeyError(f"{path} missing required Route 1 columns: {missing}")

    total_rows = 0
    eligible_before_context_filter = 0
    kept_rows = 0
    excluded_rows = 0
    chunks: list[pd.DataFrame] = []
    empty_context_chunks: list[pd.DataFrame] = []
    for chunk_index, chunk in enumerate(pd.read_csv(
        path,
        usecols=usecols,
        dtype=str,
        keep_default_na=False,
        chunksize=chunksize,
        low_memory=False,
    ), start=1):
        total_rows += len(chunk)
        wanted = chunk[
            chunk["role"].astype(str).eq("child")
            & chunk["target_variant"].astype(str).eq("real")
            & chunk["context_k"].astype(str).eq("k3")
        ].copy()
        eligible_before_context_filter += len(wanted)
        wanted["context_text"] = wanted["context_text"].map(normalize_context)
        empty_context = wanted[wanted["context_text"].astype(str).str.len() == 0].copy()
        if not empty_context.empty:
            empty_context["route2_exclusion_reason"] = "empty_context_text"
            coerce_numeric_columns(empty_context, ROUTE1_NUMERIC_COLS)
            empty_context_chunks.append(empty_context)
            excluded_rows += len(empty_context)
        wanted = wanted[wanted["context_text"].astype(str).str.len() > 0].copy()
        if not wanted.empty:
            wanted["response_entropy_context_id"] = wanted["context_text"].map(context_id)
            wanted["route2_context_word_count"] = wanted["context_text"].map(lambda text: len(str(text).split()))
            coerce_numeric_columns(wanted, ROUTE1_NUMERIC_COLS)
            chunks.append(wanted)
            kept_rows += len(wanted)
        if progress:
            print(
                "[route1] "
                f"chunk={chunk_index:,} scanned={total_rows:,} "
                f"kept={kept_rows:,} excluded_empty_context={excluded_rows:,}",
                flush=True,
            )

    out = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=[*usecols, "response_entropy_context_id"])
    empty_out = pd.concat(empty_context_chunks, ignore_index=True) if empty_context_chunks else pd.DataFrame(columns=[*usecols, "route2_exclusion_reason"])

    audit = route1_base_audit(
        out,
        empty_out,
        route1_rows_scanned=total_rows,
        route1_base_cache_used=False,
    )
    audit["eligible_real_child_k3_rows_before_nonempty_context_filter"] = eligible_before_context_filter
    return out, empty_out, audit


def route1_base_audit(
    rows: pd.DataFrame,
    excluded_empty_context_rows: pd.DataFrame,
    *,
    route1_rows_scanned: int,
    route1_base_cache_used: bool,
) -> dict[str, Any]:
    """Return row-count and uniqueness audit metrics for Route 1 base rows."""

    return {
        "route1_base_cache_used": route1_base_cache_used,
        "route1_rows_scanned": route1_rows_scanned,
        "eligible_real_child_k3_rows_before_nonempty_context_filter": len(rows) + len(excluded_empty_context_rows),
        "excluded_empty_context_rows": len(excluded_empty_context_rows),
        "eligible_real_child_k3_rows": len(rows),
        "eligible_unique_response_entropy_contexts": int(rows["response_entropy_context_id"].nunique()) if not rows.empty else 0,
        "eligible_unique_score_ids": int(rows["score_id"].nunique()) if "score_id" in rows.columns and not rows.empty else 0,
        "eligible_duplicate_score_id_rows": int(len(rows) - rows["score_id"].nunique()) if "score_id" in rows.columns and not rows.empty else 0,
        "eligible_unique_utterance_ids": int(rows["utterance_id"].nunique()) if "utterance_id" in rows.columns and not rows.empty else 0,
        "eligible_duplicate_utterance_id_rows": int(len(rows) - rows["utterance_id"].nunique()) if "utterance_id" in rows.columns and not rows.empty else 0,
    }


def load_route1_base_cache(
    route1_cache: Path,
    excluded_route1_cache: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Load cached real-child k3 Route 1 rows."""

    rows = pd.read_csv(route1_cache, dtype=str, keep_default_na=False, low_memory=False)
    required = {"score_id", "utterance_id", "context_text", "nb_words", "response_entropy_context_id"}
    require_columns(rows, required, label=str(route1_cache))
    coerce_numeric_columns(rows, ROUTE1_NUMERIC_COLS + ["route2_context_word_count"])
    if excluded_route1_cache.exists():
        excluded = pd.read_csv(excluded_route1_cache, dtype=str, keep_default_na=False, low_memory=False)
        coerce_numeric_columns(excluded, ROUTE1_NUMERIC_COLS)
    else:
        excluded = pd.DataFrame()
    audit = route1_base_audit(
        rows,
        excluded,
        route1_rows_scanned=0,
        route1_base_cache_used=True,
    )
    sidecar = route1_cache.with_name(route1_cache.name.replace(".csv.gz", "_audit.json"))
    if excluded.empty and sidecar.exists():
        try:
            sidecar_audit = json.loads(sidecar.read_text(encoding="utf-8"))
            excluded_count = int(sidecar_audit.get("excluded_empty_context_rows", 0))
            if excluded_count == 0:
                before = int(sidecar_audit.get("eligible_real_child_k3_rows_before_nonempty_context_filter", len(rows)))
                kept = int(sidecar_audit.get("eligible_real_child_k3_rows", len(rows)))
                excluded_count = max(0, before - kept)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            excluded_count = 0
        if excluded_count > 0:
            audit["excluded_empty_context_rows"] = excluded_count
            audit["eligible_real_child_k3_rows_before_nonempty_context_filter"] = len(rows) + excluded_count
            audit["excluded_empty_context_rows_loaded_from_cache_sidecar"] = True
    audit["excluded_empty_context_rows_cache_available"] = excluded_route1_cache.exists()
    audit["route1_base_cache"] = str(route1_cache)
    audit["excluded_empty_context_rows_cache"] = str(excluded_route1_cache)
    return rows, excluded, audit


def load_or_build_route1_base(
    route1_input: Path,
    *,
    chunksize: int,
    route1_cache: Path | None,
    excluded_route1_cache: Path | None,
    rebuild_route1_cache: bool,
    progress: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Load cached Route 1 base rows when possible; otherwise scan once."""

    if route1_cache is not None and route1_cache.exists() and not rebuild_route1_cache:
        if progress:
            print(f"[1/5] loading cached Route 1 base rows from {route1_cache}", flush=True)
        excluded_cache = excluded_route1_cache or route1_cache.with_name(
            route1_cache.name.replace(".csv.gz", "_excluded_empty_context_rows.csv.gz")
        )
        return load_route1_base_cache(route1_cache, excluded_cache)

    if progress:
        cache_msg = f"; cache will be written to {route1_cache}" if route1_cache is not None else ""
        print(f"[1/5] scanning Route 1 rows from {route1_input}{cache_msg}", flush=True)
    rows, excluded, audit = iter_route1_real_child_rows(route1_input, chunksize=chunksize, progress=progress)
    if route1_cache is not None:
        route1_cache.parent.mkdir(parents=True, exist_ok=True)
        rows.to_csv(route1_cache, index=False)
        sidecar = route1_cache.with_name(route1_cache.name.replace(".csv.gz", "_audit.json"))
        sidecar.write_text(json.dumps(audit, indent=2), encoding="utf-8")
        audit["route1_base_cache"] = str(route1_cache)
    if excluded_route1_cache is not None:
        excluded_route1_cache.parent.mkdir(parents=True, exist_ok=True)
        excluded.to_csv(excluded_route1_cache, index=False)
        audit["excluded_empty_context_rows_cache"] = str(excluded_route1_cache)
    return rows, excluded, audit


@lru_cache(maxsize=500_000)
def parse_word_count_hist(hist_json: str) -> tuple[tuple[int, int], ...]:
    """Parse one compact word-count histogram JSON into sorted pairs."""

    if not hist_json:
        return ()
    try:
        payload = json.loads(hist_json)
    except json.JSONDecodeError:
        return ()
    pairs: dict[int, int] = {}
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            value = item.get("value", item.get("word_count", item.get("words")))
            count = item.get("count", 0)
            try:
                word_count = int(float(value))
                pairs[word_count] = pairs.get(word_count, 0) + int(float(count))
            except (TypeError, ValueError):
                continue
    elif isinstance(payload, dict):
        for key, count in payload.items():
            try:
                word_count = int(float(key))
                pairs[word_count] = pairs.get(word_count, 0) + int(float(count))
            except (TypeError, ValueError):
                continue
    return tuple(sorted(pairs.items()))


def child_word_percentiles(child_words: object, hist_json: object) -> tuple[float, float, float]:
    """Return midrank, strict-less, and less-or-equal word-count percentiles."""

    child = pd.to_numeric(child_words, errors="coerce")
    if pd.isna(child):
        return math.nan, math.nan, math.nan
    child_value = float(child)
    hist = parse_word_count_hist(str(hist_json or ""))
    total = sum(count for _, count in hist)
    if total <= 0:
        return math.nan, math.nan, math.nan
    less = sum(count for words, count in hist if words < child_value)
    equal = sum(count for words, count in hist if words == child_value)
    strict_less = less / total
    less_equal = (less + equal) / total
    midrank = (less + 0.5 * equal) / total
    return midrank, strict_less, less_equal


def add_derived_predictors(table: pd.DataFrame) -> pd.DataFrame:
    """Add child-relative response-space effort predictors."""

    if "generated_valid_response_top_probability" in table.columns:
        table["response_top_probability"] = table["generated_valid_response_top_probability"]
    elif "response_top_probability_selected" in table.columns:
        table["response_top_probability"] = table["response_top_probability_selected"]
    else:
        table["response_top_probability"] = math.nan

    table["generated_expected_words"] = table.get("generated_valid_sample_words_mean", math.nan)
    table["generated_median_words"] = table.get("generated_valid_sample_words_median", math.nan)
    table["generated_p90_words"] = table.get("generated_valid_sample_words_p90", math.nan)
    table["valid_sample_count"] = table.get("generated_valid_sample_words_n", table.get("response_valid_selected_count", math.nan))
    table["fallback_used_for_context"] = table.get("generated_fallback_used", table.get("response_fallback_used", pd.NA))

    table["child_words_minus_generated_mean"] = table["nb_words"] - table["generated_expected_words"]
    table["child_words_minus_generated_median"] = table["nb_words"] - table["generated_median_words"]
    sd = pd.to_numeric(table.get("generated_valid_sample_words_sd", math.nan), errors="coerce")
    table["child_words_z_vs_generated"] = table["child_words_minus_generated_mean"] / sd.where(sd > 0)
    table["child_words_ratio_to_generated_mean"] = table["nb_words"] / table["generated_expected_words"].where(
        table["generated_expected_words"] > 0
    )

    if "generated_valid_word_count_hist_json" in table.columns:
        percentiles = [
            child_word_percentiles(child_words, hist)
            for child_words, hist in zip(table["nb_words"], table["generated_valid_word_count_hist_json"], strict=False)
        ]
        if percentiles:
            midrank, strict_less, less_equal = zip(*percentiles, strict=False)
            table["child_words_percentile_in_generated_distribution"] = list(midrank)
            table["child_words_cdf_lt_generated_distribution"] = list(strict_less)
            table["child_words_cdf_le_generated_distribution"] = list(less_equal)
        else:
            table["child_words_percentile_in_generated_distribution"] = math.nan
            table["child_words_cdf_lt_generated_distribution"] = math.nan
            table["child_words_cdf_le_generated_distribution"] = math.nan
    else:
        table["child_words_percentile_in_generated_distribution"] = math.nan
        table["child_words_cdf_lt_generated_distribution"] = math.nan
        table["child_words_cdf_le_generated_distribution"] = math.nan

    table["child_shorter_than_generated_median"] = (table["nb_words"] < table["generated_median_words"]).astype("boolean")
    table["child_longer_than_generated_p90"] = (table["nb_words"] > table["generated_p90_words"]).astype("boolean")

    if {"response_entropy_bits", "generated_valid_response_type_miller_madow_bits"}.issubset(table.columns):
        table["response_entropy_bits_delta_effort_summary"] = (
            table["response_entropy_bits"] - table["generated_valid_response_type_miller_madow_bits"]
        )
    return table


def merge_route2_table(
    *,
    route1_rows: pd.DataFrame,
    entropy_features: pd.DataFrame,
    generated_effort: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Join actual child rows to context-level Route 2 predictors."""

    start_rows = len(route1_rows)
    merged = route1_rows.merge(entropy_features, on="response_entropy_context_id", how="left", validate="many_to_one")
    after_entropy_rows = len(merged)
    merged = merged.merge(generated_effort, on="response_entropy_context_id", how="left", validate="many_to_one")
    after_effort_rows = len(merged)
    if after_entropy_rows != start_rows or after_effort_rows != start_rows:
        raise RuntimeError(
            "Route 2 join changed row count: "
            f"start={start_rows}, after_entropy={after_entropy_rows}, after_effort={after_effort_rows}"
        )
    merged = add_derived_predictors(merged)
    audit = {
        "route2_output_rows": len(merged),
        "matched_response_entropy_rows": int(merged["response_entropy_setting_id"].notna().sum())
        if "response_entropy_setting_id" in merged.columns
        else 0,
        "missing_response_entropy_rows": int(merged["response_entropy_setting_id"].isna().sum())
        if "response_entropy_setting_id" in merged.columns
        else len(merged),
        "matched_generated_effort_rows": int(merged["generated_setting_id"].notna().sum())
        if "generated_setting_id" in merged.columns
        else 0,
        "missing_generated_effort_rows": int(merged["generated_setting_id"].isna().sum())
        if "generated_setting_id" in merged.columns
        else len(merged),
        "fallback_used_rows": int(merged["fallback_used_for_context"].fillna(False).astype(bool).sum())
        if "fallback_used_for_context" in merged.columns
        else 0,
        "fallback_used_contexts": int(
            merged.loc[merged["fallback_used_for_context"].fillna(False).astype(bool), "response_entropy_context_id"].nunique()
        )
        if "fallback_used_for_context" in merged.columns
        else 0,
    }
    if "response_entropy_bits_delta_effort_summary" in merged.columns:
        delta = pd.to_numeric(merged["response_entropy_bits_delta_effort_summary"], errors="coerce").abs()
        audit["max_abs_response_entropy_bits_delta_effort_summary"] = float(delta.max()) if delta.notna().any() else math.nan
    return merged, audit


def audit_rows(metrics: dict[str, Any]) -> pd.DataFrame:
    """Format audit metrics as a small CSV table."""

    return pd.DataFrame(
        [{"metric": key, "value": value} for key, value in sorted(metrics.items())]
    )


def write_count_audits(table: pd.DataFrame, output_dir: Path) -> None:
    """Write row-count audits by age bin and dataset."""

    output_dir.mkdir(parents=True, exist_ok=True)
    for group_col, filename in [
        ("age_bin", "route2_response_space_counts_by_age_bin.csv"),
        ("dataset", "route2_response_space_counts_by_dataset.csv"),
    ]:
        if group_col not in table.columns:
            continue
        grouped = (
            table.groupby(group_col, dropna=False)
            .agg(
                rows=("score_id", "size"),
                unique_contexts=("response_entropy_context_id", "nunique"),
                missing_response_entropy_rows=("response_entropy_setting_id", lambda s: int(s.isna().sum()))
                if "response_entropy_setting_id" in table.columns
                else ("score_id", lambda s: 0),
                missing_generated_effort_rows=("generated_setting_id", lambda s: int(s.isna().sum()))
                if "generated_setting_id" in table.columns
                else ("score_id", lambda s: 0),
                fallback_used_rows=("fallback_used_for_context", lambda s: int(s.fillna(False).astype(bool).sum()))
                if "fallback_used_for_context" in table.columns
                else ("score_id", lambda s: 0),
            )
            .reset_index()
            .sort_values(group_col)
        )
        grouped.to_csv(output_dir / filename, index=False)


def review_columns(table: pd.DataFrame) -> list[str]:
    """Return compact columns for manual review samples."""

    wanted = [
        "review_bucket",
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
        "context_text",
        "target_utterance_clean",
        "nb_words",
        "sum_bits",
        "mean_bits_per_token",
        "context_entropy_bits",
        "response_entropy_context_id",
        "response_entropy_bits",
        "response_unique_response_count",
        "response_top_probability",
        "generated_expected_words",
        "generated_median_words",
        "generated_p90_words",
        "generated_valid_sample_words_sd",
        "child_words_minus_generated_mean",
        "child_words_z_vs_generated",
        "child_words_percentile_in_generated_distribution",
        "child_shorter_than_generated_median",
        "child_longer_than_generated_p90",
        "fallback_used_for_context",
        "valid_sample_count",
        "generated_invalid_selected_rows_observed",
        "generated_invalid_selected_top_rejection_reason",
        "generated_valid_word_count_hist_json",
    ]
    return [col for col in wanted if col in table.columns]


def make_manual_review_sample(table: pd.DataFrame, *, per_bucket: int, seed: int) -> pd.DataFrame:
    """Create a compact CSV for human inspection of joined rows."""

    pieces: list[pd.DataFrame] = []

    def add(label: str, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        sample = frame.head(per_bucket).copy()
        sample.insert(0, "review_bucket", label)
        pieces.append(sample)

    random_rows = table.sample(n=min(per_bucket, len(table)), random_state=seed) if len(table) else table
    add("random", random_rows)

    finite_entropy = table[pd.to_numeric(table.get("response_entropy_bits", pd.Series(dtype=float)), errors="coerce").notna()]
    if not finite_entropy.empty:
        add("high_response_entropy", finite_entropy.sort_values("response_entropy_bits", ascending=False))
        add("low_response_entropy", finite_entropy.sort_values("response_entropy_bits", ascending=True))

    finite_z = table[pd.to_numeric(table.get("child_words_z_vs_generated", pd.Series(dtype=float)), errors="coerce").notna()]
    if not finite_z.empty:
        add("child_much_shorter_than_generated", finite_z.sort_values("child_words_z_vs_generated", ascending=True))
        add("child_much_longer_than_generated", finite_z.sort_values("child_words_z_vs_generated", ascending=False))

    if "fallback_used_for_context" in table.columns:
        fallback = table[table["fallback_used_for_context"].fillna(False).astype(bool)].copy()
        add("fallback_context", fallback.sort_values(["response_entropy_context_id", "score_id"]))

    if not pieces:
        return pd.DataFrame(columns=review_columns(table))
    out = pd.concat(pieces, ignore_index=True, sort=False)
    cols = review_columns(out)
    return out[cols]


def write_schema(table: pd.DataFrame, output_dir: Path) -> None:
    """Write a lightweight schema/provenance JSON file."""

    schema = {
        "columns": [
            {
                "name": col,
                "dtype": str(table[col].dtype),
                "non_null_rows": int(table[col].notna().sum()),
            }
            for col in table.columns
        ],
        "primary_key_expectation": "one row per actual real-child k3 utterance row from the Route 1 long table",
        "context_key": "response_entropy_context_id = sha256(normalize_context(context_text))[:24]",
        "primary_response_entropy_column": "response_entropy_bits",
        "primary_generated_effort_column": "generated_expected_words",
    }
    (output_dir / "route2_response_space_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")


def build_route2_response_space_table(
    *,
    route1_input: Path,
    entropy_features_csv: Path,
    generated_effort_csv: Path,
    output_csv: Path,
    audit_dir: Path,
    prompt_variant: str,
    temperature: float,
    chunksize: int,
    review_per_bucket: int,
    seed: int,
    route1_cache: Path | None = None,
    excluded_route1_cache: Path | None = None,
    rebuild_route1_cache: bool = False,
    progress: bool = False,
) -> pd.DataFrame:
    """Build and write the Route 2 response-space effort table."""

    route1_rows, excluded_empty_context_rows, route1_audit = load_or_build_route1_base(
        route1_input,
        chunksize=chunksize,
        route1_cache=route1_cache,
        excluded_route1_cache=excluded_route1_cache,
        rebuild_route1_cache=rebuild_route1_cache,
        progress=progress,
    )
    if progress:
        print(f"[2/5] loading response entropy features from {entropy_features_csv}", flush=True)
    entropy_features, entropy_audit = load_entropy_features(
        entropy_features_csv,
        prompt_variant=prompt_variant,
        temperature=temperature,
    )
    if progress:
        print(f"[3/5] loading generated effort summary from {generated_effort_csv}", flush=True)
    generated_effort, generated_audit = load_generated_effort_summary(
        generated_effort_csv,
        prompt_variant=prompt_variant,
        temperature=temperature,
    )
    if progress:
        print("[4/5] joining and deriving child-relative predictors", flush=True)
    table, join_audit = merge_route2_table(
        route1_rows=route1_rows,
        entropy_features=entropy_features,
        generated_effort=generated_effort,
    )

    audit_dir.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    excluded_path = audit_dir / "route2_response_space_excluded_empty_context_rows.csv.gz"
    excluded_empty_context_rows.to_csv(excluded_path, index=False)
    if progress:
        print(f"[5/5] writing table to {output_csv}", flush=True)
    table.to_csv(output_csv, index=False)

    all_audit = {
        "route1_input": str(route1_input),
        "entropy_features_csv": str(entropy_features_csv),
        "generated_effort_csv": str(generated_effort_csv),
        "output_csv": str(output_csv),
        "excluded_empty_context_rows_csv": str(excluded_path),
        "prompt_variant": prompt_variant,
        "temperature": temperature,
        **route1_audit,
        **entropy_audit,
        **generated_audit,
        **join_audit,
    }
    audit_rows(all_audit).to_csv(audit_dir / "route2_response_space_join_audit.csv", index=False)
    write_count_audits(table, audit_dir)
    make_manual_review_sample(table, per_bucket=review_per_bucket, seed=seed).to_csv(
        audit_dir / "route2_response_space_manual_review_sample.csv",
        index=False,
    )
    write_schema(table, audit_dir)
    return table


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route1-input", type=Path, default=DEFAULT_ROUTE1_INPUT)
    parser.add_argument("--mila-merged-dir", type=Path, default=DEFAULT_MILA_MERGED_DIR)
    parser.add_argument("--entropy-features-csv", type=Path, default=None)
    parser.add_argument("--generated-effort-csv", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--route1-cache", type=Path, default=DEFAULT_ROUTE1_CACHE)
    parser.add_argument("--excluded-route1-cache", type=Path, default=DEFAULT_EXCLUDED_ROUTE1_CACHE)
    parser.add_argument(
        "--rebuild-route1-cache",
        action="store_true",
        help="Force a full scan of the Route 1 long table and overwrite the cached real-child k3 base rows.",
    )
    parser.add_argument("--prompt-variant", default=DEFAULT_PROMPT_VARIANT)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--review-per-bucket", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260702)
    args = parser.parse_args(argv)

    entropy_features_csv = args.entropy_features_csv or (args.mila_merged_dir / "context_response_entropy_features.csv.gz")
    generated_effort_csv = args.generated_effort_csv or (
        args.mila_merged_dir / "generated_response_effort_summary_by_context.csv.gz"
    )
    table = build_route2_response_space_table(
        route1_input=args.route1_input,
        entropy_features_csv=entropy_features_csv,
        generated_effort_csv=generated_effort_csv,
        output_csv=args.output,
        audit_dir=args.audit_dir,
        route1_cache=args.route1_cache,
        excluded_route1_cache=args.excluded_route1_cache,
        rebuild_route1_cache=args.rebuild_route1_cache,
        prompt_variant=args.prompt_variant,
        temperature=args.temperature,
        chunksize=args.chunksize,
        review_per_bucket=args.review_per_bucket,
        seed=args.seed,
        progress=True,
    )
    print(f"[OK] wrote {len(table):,} Route 2 child rows to {args.output}")
    print(f"[OK] wrote audits to {args.audit_dir}")


if __name__ == "__main__":
    main()
