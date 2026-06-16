#!/usr/bin/env python3
"""Score Route 2 final-smoke response samples into entropy features.

This script consumes the final Route 2 generation-smoke artifacts. It does not
call a language model and it does not generate new samples. It computes
accepted-response entropy features, sample-size stability diagnostics, prompt
and temperature rank correlations, a chunked join smoke back to real child
utterance rows, tiny downstream sanity models, plots, and a Markdown/HTML
report.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

try:
    from build_response_entropy_manifest import context_id, normalize_context
    from render_markdown_report import render_markdown_file
    from summarize_response_entropy_samples import (
        empirical_entropy_bits,
        miller_madow_entropy_bits,
        response_effort_counts,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_response_entropy_manifest import context_id, normalize_context
    from src.render_markdown_report import render_markdown_file
    from src.summarize_response_entropy_samples import (
        empirical_entropy_bits,
        miller_madow_entropy_bits,
        response_effort_counts,
    )


DEFAULT_INPUT_DIR = Path("results/response_entropy_final_generation_smoke")
DEFAULT_ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/response_entropy_final_scoring_smoke")
DEFAULT_FIG_DIR = Path("figs/response_entropy_final_scoring_smoke")
DEFAULT_REPORT_MD = Path("docs/response_entropy_final_scoring_smoke.md")
DEFAULT_REPORT_HTML = Path("docs/response_entropy_final_scoring_smoke.html")
DEFAULT_SAMPLE_SIZES = (5, 10, 20, 25, 50)

QUALITY_FLAG_COLUMNS = [
    "empty_first_line_response",
    "speaker_label_inside_response",
    "metadata_or_prose_start",
    "repetition_loop",
    "no_end_of_turn_boundary_before_cap",
    "possible_context_copy",
    "very_long_first_line_response",
    "malformed_response",
]

REQUIRED_INPUT_FILES = [
    "accepted_samples.csv.gz",
    "all_attempts.csv.gz",
    "rejection_summary_by_setting.csv",
    "quality_flags_by_setting.csv",
    "smoke_manifest.csv",
]

ROUTE1_USECOLS = [
    "score_id",
    "utterance_id",
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "speaker",
    "role",
    "target_variant",
    "context_k",
    "context_col_used",
    "context_text",
    "target_utterance_clean",
    "nb_words",
    "nb_morphemes",
    "nb_syllables_cmu_or_pkg",
    "nb_syllables_pkg",
    "nb_phonemes",
]

SPACES_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^0-9A-Za-z'\s]+")


def split_int_csv(value: str | Sequence[int]) -> list[int]:
    """Parse comma-separated positive integers."""

    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
    else:
        parts = [str(part).strip() for part in value if str(part).strip()]
    out = sorted({int(part) for part in parts if int(part) > 0})
    return out


def coerce_float(value: object, default: float = math.nan) -> float:
    """Parse a numeric scalar, returning ``default`` when parsing fails."""

    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return default
    return float(parsed)


def coerce_int(value: object, default: int = 0) -> int:
    """Parse an integer scalar, returning ``default`` when parsing fails."""

    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return default
    return int(parsed)


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 30, digits: int = 4) -> str:
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
    sep = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, sep, *rows])


def normalize_response_type(text: object, *, mode: str) -> str:
    """Normalize one sampled response for response-type counting.

    ``exact`` preserves case and punctuation after whitespace collapse.
    ``casefold`` is punctuation-sensitive but ignores case.
    ``casefold_punct_stripped`` removes punctuation for a coarse sensitivity
    check.
    """

    if text is None or (isinstance(text, float) and math.isnan(text)):
        value = ""
    else:
        value = str(text)
    value = SPACES_RE.sub(" ", value).strip()
    if mode == "exact":
        pass
    elif mode == "casefold":
        value = value.casefold()
    elif mode == "casefold_punct_stripped":
        value = PUNCT_RE.sub(" ", value.casefold())
        value = SPACES_RE.sub(" ", value).strip()
    else:
        raise ValueError(f"unknown response normalization mode: {mode}")
    return value if value else "<EMPTY_RESPONSE>"


def response_entropy_summary(texts: Sequence[object], *, normalization: str, top_n: int = 20) -> dict[str, object]:
    """Return entropy and response-type summaries for a set of responses."""

    normalized = [normalize_response_type(text, mode=normalization) for text in texts]
    counts = Counter(normalized)
    sample_count = sum(counts.values())
    unique_count = len(counts)
    entropy = empirical_entropy_bits(counts)
    corrected = miller_madow_entropy_bits(entropy, unique_count=unique_count, sample_count=sample_count)
    top_response, top_count = counts.most_common(1)[0] if counts else ("", 0)
    log_sample = math.log2(sample_count) if sample_count > 1 else math.nan
    log_unique = math.log2(unique_count) if unique_count > 1 else math.nan
    return {
        "sample_count": sample_count,
        "unique_response_count": unique_count,
        "empirical_response_entropy_bits": entropy,
        "miller_madow_entropy_bits": corrected,
        "normalized_entropy_by_log_sample_count": entropy / log_sample
        if math.isfinite(log_sample) and log_sample > 0
        else math.nan,
        "response_evenness_observed_types": entropy / log_unique
        if math.isfinite(log_unique) and log_unique > 0
        else math.nan,
        "top_response_text": top_response,
        "top_response_count": int(top_count),
        "top_response_probability": top_count / sample_count if sample_count else math.nan,
        "response_type_counts_json": json.dumps(
            [{"response": response, "count": int(count)} for response, count in counts.most_common(top_n)],
            ensure_ascii=False,
        ),
    }


def safe_corr(left: pd.Series, right: pd.Series, *, method: str) -> float:
    """Return a correlation or NaN if there is too little variation."""

    frame = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(frame) < 2 or frame["left"].nunique() < 2 or frame["right"].nunique() < 2:
        return math.nan
    return float(frame["left"].corr(frame["right"], method=method))


def read_generation_smoke_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Read and validate final generation-smoke artifacts."""

    paths = {name: input_dir / name for name in REQUIRED_INPUT_FILES}
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing final generation-smoke artifact(s): " + ", ".join(missing))

    try:
        accepted = pd.read_csv(paths["accepted_samples.csv.gz"], dtype=str, keep_default_na=False, low_memory=False)
        attempts = pd.read_csv(paths["all_attempts.csv.gz"], dtype=str, keep_default_na=False, low_memory=False)
    except (EOFError, gzip.BadGzipFile, pd.errors.ParserError) as exc:
        raise RuntimeError(f"could not read gzipped generation-smoke samples under {input_dir}") from exc

    rejections = pd.read_csv(paths["rejection_summary_by_setting.csv"], dtype=str, keep_default_na=False, low_memory=False)
    quality = pd.read_csv(paths["quality_flags_by_setting.csv"], dtype=str, keep_default_na=False, low_memory=False)
    manifest = pd.read_csv(paths["smoke_manifest.csv"], dtype=str, keep_default_na=False, low_memory=False)

    required_accepted = {"setting_id", "context_id", "prompt_variant", "temperature", "sample_index", "sampled_response_text"}
    required_attempts = {"setting_id", "context_id", "prompt_variant", "temperature", "accepted", "sampled_response_text"}
    required_rejections = {"setting_id", "context_id", "prompt_variant", "temperature", "attempts", "accepted_samples"}
    for label, frame, required in [
        ("accepted_samples.csv.gz", accepted, required_accepted),
        ("all_attempts.csv.gz", attempts, required_attempts),
        ("rejection_summary_by_setting.csv", rejections, required_rejections),
    ]:
        missing_cols = required - set(frame.columns)
        if missing_cols:
            raise KeyError(f"{label} missing required columns: {sorted(missing_cols)}")

    for frame in [accepted, attempts, rejections, quality, manifest]:
        if "temperature" in frame.columns:
            frame["temperature_num"] = pd.to_numeric(frame["temperature"], errors="coerce")
        if "sample_index" in frame.columns:
            frame["sample_index_num"] = pd.to_numeric(frame["sample_index"], errors="coerce")
        if "attempt_index" in frame.columns:
            frame["attempt_index_num"] = pd.to_numeric(frame["attempt_index"], errors="coerce")
        for flag in QUALITY_FLAG_COLUMNS:
            if flag in frame.columns:
                frame[f"{flag}_int"] = pd.to_numeric(frame[flag], errors="coerce").fillna(0).astype(int)
    attempts["accepted_int"] = pd.to_numeric(attempts["accepted"], errors="coerce").fillna(0).astype(int)
    return {
        "accepted": accepted,
        "attempts": attempts,
        "rejections": rejections,
        "quality": quality,
        "manifest": manifest,
    }


def setting_metadata(attempts: pd.DataFrame) -> pd.DataFrame:
    """Return one metadata row per context-temperature-prompt setting."""

    cols = [
        "setting_id",
        "context_text",
        "context_word_count",
        "context_length_bucket",
        "prompt_template",
        "prompt_text",
        "temperature_num",
        "model_used",
        "max_new_tokens",
        "top_p",
        "top_k",
    ]
    available = [col for col in cols if col in attempts.columns]
    meta = attempts[available].drop_duplicates(subset=["setting_id"], keep="first").copy()
    return meta.rename(columns={"temperature_num": "temperature_from_attempts"})


def quality_rates_json(row: Mapping[str, object]) -> str:
    """Pack quality-rate columns into a compact JSON string."""

    payload = {}
    for key, value in row.items():
        if key.endswith("_attempt_rate") or key.endswith("_accepted_rate"):
            parsed = coerce_float(value)
            payload[key] = None if not math.isfinite(parsed) else parsed
    return json.dumps(payload, sort_keys=True)


def compute_entropy_features(
    *,
    accepted: pd.DataFrame,
    attempts: pd.DataFrame,
    rejections: pd.DataFrame,
    quality: pd.DataFrame,
    normalization: str,
) -> pd.DataFrame:
    """Compute one entropy-feature row per context/prompt/temperature setting."""

    meta = setting_metadata(attempts)
    accepted_groups = {setting_id: group.copy() for setting_id, group in accepted.groupby("setting_id", sort=False)}
    quality_by_setting = quality.drop_duplicates(subset=["setting_id"], keep="first").set_index("setting_id")
    rows: list[dict[str, object]] = []

    merged = rejections.merge(meta, on="setting_id", how="left")
    for _, rej in merged.sort_values(["temperature", "prompt_variant", "context_id"]).iterrows():
        setting_id = str(rej["setting_id"])
        group = accepted_groups.get(setting_id, pd.DataFrame())
        texts = group["sampled_response_text"].tolist() if "sampled_response_text" in group.columns else []
        primary = response_entropy_summary(texts, normalization=normalization)
        exact = response_entropy_summary(texts, normalization="exact")
        punct = response_entropy_summary(texts, normalization="casefold_punct_stripped")
        effort = pd.DataFrame([response_effort_counts(text) for text in texts])
        normalized_text_lengths = [len(SPACES_RE.sub(" ", str(text or "")).strip()) for text in texts]
        word_counts = effort["sample_word_count"] if "sample_word_count" in effort.columns else pd.Series(dtype=float)

        quality_row = quality_by_setting.loc[setting_id].to_dict() if setting_id in quality_by_setting.index else {}
        attempt_count = coerce_int(rej.get("attempts", ""))
        accepted_sample_count = coerce_int(rej.get("accepted_samples", len(texts)))
        rejection_count = coerce_int(rej.get("rejected_attempts", attempt_count - accepted_sample_count))

        row = {
            "setting_id": setting_id,
            "context_id": rej.get("context_id", ""),
            "normalized_context_id": context_id(normalize_context(rej.get("context_text", ""))),
            "context_id_matches_normalized_text": str(rej.get("context_id", ""))
            == context_id(normalize_context(rej.get("context_text", ""))),
            "context_text": rej.get("context_text", ""),
            "context_word_count": coerce_float(rej.get("context_word_count", "")),
            "context_length_bucket": rej.get("context_length_bucket", ""),
            "prompt_variant": rej.get("prompt_variant", ""),
            "temperature": coerce_float(rej.get("temperature", "")),
            "response_normalization_primary": normalization,
            "accepted_sample_count": accepted_sample_count,
            "attempt_count": attempt_count,
            "rejection_count": rejection_count,
            "rejection_rate": coerce_float(rej.get("rejection_rate", ""))
            if "rejection_rate" in rej
            else (rejection_count / attempt_count if attempt_count else math.nan),
            "target_accepted_samples": coerce_int(rej.get("target_accepted_samples", "")),
            "max_attempts_per_setting": coerce_int(rej.get("max_attempts_per_setting", "")),
            "reached_target": str(rej.get("reached_target", "")).lower() == "true",
            "unique_response_count": primary["unique_response_count"],
            "top_response_probability": primary["top_response_probability"],
            "empirical_response_entropy_bits": primary["empirical_response_entropy_bits"],
            "miller_madow_entropy_bits": primary["miller_madow_entropy_bits"],
            "normalized_entropy_by_log_sample_count": primary["normalized_entropy_by_log_sample_count"],
            "response_evenness_observed_types": primary["response_evenness_observed_types"],
            "top_response_text": primary["top_response_text"],
            "top_response_count": primary["top_response_count"],
            "response_type_counts_json": primary["response_type_counts_json"],
            "exact_unique_response_count": exact["unique_response_count"],
            "exact_empirical_response_entropy_bits": exact["empirical_response_entropy_bits"],
            "exact_miller_madow_entropy_bits": exact["miller_madow_entropy_bits"],
            "punctuation_folded_unique_response_count": punct["unique_response_count"],
            "punctuation_folded_empirical_response_entropy_bits": punct["empirical_response_entropy_bits"],
            "punctuation_folded_miller_madow_entropy_bits": punct["miller_madow_entropy_bits"],
            "mean_sample_words": float(word_counts.mean()) if len(word_counts) else math.nan,
            "median_sample_words": float(word_counts.median()) if len(word_counts) else math.nan,
            "p90_sample_words": float(word_counts.quantile(0.9)) if len(word_counts) else math.nan,
            "mean_sample_characters": float(pd.Series(normalized_text_lengths).mean())
            if normalized_text_lengths
            else math.nan,
            "mean_sample_morphemes_surface": float(effort["sample_morpheme_count_surface"].mean())
            if "sample_morpheme_count_surface" in effort.columns and len(effort)
            else math.nan,
            "mean_sample_syllables_pkg": float(effort["sample_syllable_count_pkg"].mean())
            if "sample_syllable_count_pkg" in effort.columns and len(effort)
            else math.nan,
            "quality_flag_rates": quality_rates_json(quality_row),
            "quality_flag_rates_json": quality_rates_json(quality_row),
            "model_used": rej.get("model_used", ""),
            "max_new_tokens": rej.get("max_new_tokens", ""),
            "top_p": rej.get("top_p", ""),
            "top_k": rej.get("top_k", ""),
        }
        for key, value in quality_row.items():
            if key.endswith("_attempt_rate") or key.endswith("_accepted_rate"):
                row[key] = coerce_float(value)
        rows.append(row)
    return pd.DataFrame(rows)


def entropy_for_group_prefix(group: pd.DataFrame, *, size: int | None, normalization: str) -> tuple[float, int]:
    """Return Miller-Madow entropy for a prefix of accepted samples."""

    ordered = group.sort_values(["sample_index_num", "attempt_index_num"], na_position="last")
    if size is not None:
        if len(ordered) < size:
            return math.nan, len(ordered)
        ordered = ordered.head(size)
    summary = response_entropy_summary(ordered["sampled_response_text"].tolist(), normalization=normalization)
    return coerce_float(summary["miller_madow_entropy_bits"]), int(summary["sample_count"])


def compute_stability_rows(
    accepted: pd.DataFrame,
    *,
    sample_sizes: Sequence[int],
    normalization: str,
    all_settings: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute context-setting sample-size and split-half stability rows."""

    rows: list[dict[str, object]] = []
    for (context_id_value, prompt_variant, temperature), group in accepted.groupby(
        ["context_id", "prompt_variant", "temperature_num"],
        sort=True,
        dropna=False,
    ):
        group = group.copy()
        full_entropy, full_n = entropy_for_group_prefix(group, size=None, normalization=normalization)
        row = {
            "setting_id": group["setting_id"].iloc[0],
            "context_id": context_id_value,
            "prompt_variant": prompt_variant,
            "temperature": float(temperature),
            "accepted_sample_count": int(len(group)),
            "entropy_full_bits": full_entropy,
            "stability_sample_sizes_requested": ",".join(str(size) for size in sample_sizes),
            "stability_sample_sizes_available": ",".join(str(size) for size in sample_sizes if len(group) >= size),
        }
        for size in sample_sizes:
            entropy, sample_count = entropy_for_group_prefix(group, size=size, normalization=normalization)
            row[f"entropy_first_{size}_bits"] = entropy
            row[f"sample_count_first_{size}"] = sample_count if len(group) >= size else len(group)

        ordered = group.sort_values(["sample_index_num", "attempt_index_num"], na_position="last")
        if len(ordered) >= 4:
            midpoint = len(ordered) // 2
            first = ordered.iloc[:midpoint]
            second = ordered.iloc[midpoint:]
            first_summary = response_entropy_summary(first["sampled_response_text"].tolist(), normalization=normalization)
            second_summary = response_entropy_summary(second["sampled_response_text"].tolist(), normalization=normalization)
            row["split_half_first_entropy_bits"] = first_summary["miller_madow_entropy_bits"]
            row["split_half_second_entropy_bits"] = second_summary["miller_madow_entropy_bits"]
            row["split_half_first_n"] = int(first_summary["sample_count"])
            row["split_half_second_n"] = int(second_summary["sample_count"])
            row["split_half_abs_diff_bits"] = abs(
                coerce_float(first_summary["miller_madow_entropy_bits"])
                - coerce_float(second_summary["miller_madow_entropy_bits"])
            )
        else:
            row["split_half_first_entropy_bits"] = math.nan
            row["split_half_second_entropy_bits"] = math.nan
            row["split_half_first_n"] = 0
            row["split_half_second_n"] = 0
            row["split_half_abs_diff_bits"] = math.nan
        rows.append(row)
    stability = pd.DataFrame(rows)
    if all_settings is None or all_settings.empty:
        return stability

    observed_ids = set(stability["setting_id"].astype(str)) if not stability.empty else set()
    missing = all_settings[~all_settings["setting_id"].astype(str).isin(observed_ids)].copy()
    if missing.empty:
        return stability
    missing_rows: list[dict[str, object]] = []
    for _, setting in missing.iterrows():
        row = {
            "setting_id": setting.get("setting_id", ""),
            "context_id": setting.get("context_id", ""),
            "prompt_variant": setting.get("prompt_variant", ""),
            "temperature": coerce_float(setting.get("temperature", "")),
            "accepted_sample_count": coerce_int(setting.get("accepted_sample_count", "")),
            "entropy_full_bits": coerce_float(setting.get("miller_madow_entropy_bits", "")),
            "stability_sample_sizes_requested": ",".join(str(size) for size in sample_sizes),
            "stability_sample_sizes_available": "",
            "split_half_first_entropy_bits": math.nan,
            "split_half_second_entropy_bits": math.nan,
            "split_half_first_n": 0,
            "split_half_second_n": 0,
            "split_half_abs_diff_bits": math.nan,
        }
        for size in sample_sizes:
            row[f"entropy_first_{size}_bits"] = math.nan
            row[f"sample_count_first_{size}"] = coerce_int(setting.get("accepted_sample_count", ""))
        missing_rows.append(row)
    return pd.concat([stability, pd.DataFrame(missing_rows)], ignore_index=True, sort=False)


def sample_size_rank_correlations(stability: pd.DataFrame, *, sample_sizes: Sequence[int]) -> pd.DataFrame:
    """Correlate prefix entropies with full-sample entropies."""

    rows: list[dict[str, object]] = []
    if stability.empty:
        return pd.DataFrame(rows)
    for size in sample_sizes:
        col = f"entropy_first_{size}_bits"
        if col not in stability.columns:
            continue
        for (prompt_variant, temperature), group in stability.groupby(["prompt_variant", "temperature"], sort=True):
            pair = group[[col, "entropy_full_bits"]].dropna()
            rows.append(
                {
                    "comparison_family": "sample_size_vs_full",
                    "prompt_variant": prompt_variant,
                    "temperature": float(temperature),
                    "sample_size": int(size),
                    "shared_settings": int(len(pair)),
                    "spearman_r": safe_corr(pair[col], pair["entropy_full_bits"], method="spearman"),
                    "pearson_r": safe_corr(pair[col], pair["entropy_full_bits"], method="pearson"),
                    "mean_abs_entropy_diff_bits": float((pair[col] - pair["entropy_full_bits"]).abs().mean())
                    if len(pair)
                    else math.nan,
                }
            )
    return pd.DataFrame(rows)


def split_half_reliability_summary(stability: pd.DataFrame) -> pd.DataFrame:
    """Summarize split-half reliability across contexts by prompt/temperature."""

    if stability.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for (prompt_variant, temperature), group in stability.groupby(["prompt_variant", "temperature"], sort=True):
        pair = group[["split_half_first_entropy_bits", "split_half_second_entropy_bits", "split_half_abs_diff_bits"]].dropna()
        rows.append(
            {
                "prompt_variant": prompt_variant,
                "temperature": float(temperature),
                "settings": int(len(pair)),
                "spearman_r": safe_corr(
                    pair["split_half_first_entropy_bits"],
                    pair["split_half_second_entropy_bits"],
                    method="spearman",
                ),
                "pearson_r": safe_corr(
                    pair["split_half_first_entropy_bits"],
                    pair["split_half_second_entropy_bits"],
                    method="pearson",
                ),
                "mean_abs_diff_bits": float(pair["split_half_abs_diff_bits"].mean()) if len(pair) else math.nan,
                "median_abs_diff_bits": float(pair["split_half_abs_diff_bits"].median()) if len(pair) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def temperature_correlations(features: pd.DataFrame) -> pd.DataFrame:
    """Compute rank correlations across temperatures."""

    rows: list[dict[str, object]] = []
    entropy_col = "miller_madow_entropy_bits"
    for prompt_variant, prompt_group in features.groupby("prompt_variant", sort=True):
        pivot = prompt_group.pivot_table(index="context_id", columns="temperature", values=entropy_col, aggfunc="first")
        for left, right in combinations(sorted(pivot.columns), 2):
            pair = pivot[[left, right]].dropna()
            rows.append(
                {
                    "comparison_family": "temperature_within_prompt",
                    "prompt_variant": prompt_variant,
                    "temperature_a": float(left),
                    "temperature_b": float(right),
                    "shared_contexts": int(len(pair)),
                    "spearman_r": safe_corr(pair[left], pair[right], method="spearman"),
                    "pearson_r": safe_corr(pair[left], pair[right], method="pearson"),
                    "mean_abs_entropy_diff_bits": float((pair[left] - pair[right]).abs().mean()) if len(pair) else math.nan,
                }
            )

    combined = features.copy()
    combined["context_prompt_id"] = combined["context_id"].astype(str) + "::" + combined["prompt_variant"].astype(str)
    pivot = combined.pivot_table(index="context_prompt_id", columns="temperature", values=entropy_col, aggfunc="first")
    for left, right in combinations(sorted(pivot.columns), 2):
        pair = pivot[[left, right]].dropna()
        rows.append(
            {
                "comparison_family": "temperature_all_prompts",
                "prompt_variant": "ALL",
                "temperature_a": float(left),
                "temperature_b": float(right),
                "shared_contexts": int(len(pair)),
                "spearman_r": safe_corr(pair[left], pair[right], method="spearman"),
                "pearson_r": safe_corr(pair[left], pair[right], method="pearson"),
                "mean_abs_entropy_diff_bits": float((pair[left] - pair[right]).abs().mean()) if len(pair) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def prompt_correlations(features: pd.DataFrame) -> pd.DataFrame:
    """Compute rank correlations across prompt variants."""

    rows: list[dict[str, object]] = []
    entropy_col = "miller_madow_entropy_bits"
    for temperature, temp_group in features.groupby("temperature", sort=True):
        pivot = temp_group.pivot_table(index="context_id", columns="prompt_variant", values=entropy_col, aggfunc="first")
        for left, right in combinations(sorted(pivot.columns), 2):
            pair = pivot[[left, right]].dropna()
            rows.append(
                {
                    "comparison_family": "prompt_within_temperature",
                    "temperature": float(temperature),
                    "prompt_variant_a": left,
                    "prompt_variant_b": right,
                    "shared_contexts": int(len(pair)),
                    "spearman_r": safe_corr(pair[left], pair[right], method="spearman"),
                    "pearson_r": safe_corr(pair[left], pair[right], method="pearson"),
                    "mean_abs_entropy_diff_bits": float((pair[left] - pair[right]).abs().mean()) if len(pair) else math.nan,
                }
            )

    combined = features.copy()
    combined["context_temperature_id"] = (
        combined["context_id"].astype(str) + "::T" + combined["temperature"].astype(str)
    )
    pivot = combined.pivot_table(index="context_temperature_id", columns="prompt_variant", values=entropy_col, aggfunc="first")
    for left, right in combinations(sorted(pivot.columns), 2):
        pair = pivot[[left, right]].dropna()
        rows.append(
            {
                "comparison_family": "prompt_all_temperatures",
                "temperature": "ALL",
                "prompt_variant_a": left,
                "prompt_variant_b": right,
                "shared_contexts": int(len(pair)),
                "spearman_r": safe_corr(pair[left], pair[right], method="spearman"),
                "pearson_r": safe_corr(pair[left], pair[right], method="pearson"),
                "mean_abs_entropy_diff_bits": float((pair[left] - pair[right]).abs().mean()) if len(pair) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def prepare_features_for_join(features: pd.DataFrame) -> pd.DataFrame:
    """Rename feature columns before expanding onto real child rows."""

    joined = features.copy()
    joined["join_context_id"] = joined["normalized_context_id"].where(
        joined["normalized_context_id"].astype(str).str.len().gt(0),
        joined["context_id"],
    )
    joined = joined.rename(
        columns={
            "context_id": "entropy_context_id",
            "context_text": "entropy_context_text",
            "context_word_count": "entropy_context_word_count",
            "miller_madow_entropy_bits": "response_entropy_bits",
            "empirical_response_entropy_bits": "response_entropy_empirical_bits",
            "accepted_sample_count": "response_entropy_accepted_sample_count",
            "attempt_count": "response_entropy_attempt_count",
            "rejection_count": "response_entropy_rejection_count",
            "rejection_rate": "response_entropy_rejection_rate",
            "unique_response_count": "response_entropy_unique_response_count",
            "top_response_probability": "response_entropy_top_response_probability",
            "mean_sample_words": "response_entropy_mean_sample_words",
            "median_sample_words": "response_entropy_median_sample_words",
            "p90_sample_words": "response_entropy_p90_sample_words",
            "mean_sample_characters": "response_entropy_mean_sample_characters",
        }
    )
    return joined


def load_route1_chunk(path: Path, *, chunksize: int):
    """Yield Route 1 chunks using only columns needed for the Route 2 smoke."""

    return pd.read_csv(
        path,
        usecols=lambda col: col in set(ROUTE1_USECOLS),
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )


def route2_real_child_filter(chunk: pd.DataFrame) -> pd.DataFrame:
    """Keep real child rows with nonempty preceding caretaker context."""

    required = {"role", "target_variant", "context_k", "context_text"}
    missing = required - set(chunk.columns)
    if missing:
        raise KeyError(f"Route 1 input missing required columns: {sorted(missing)}")
    out = chunk[
        chunk["role"].astype(str).eq("child")
        & chunk["target_variant"].astype(str).eq("real")
        & chunk["context_k"].astype(str).isin(["k1", "k2", "k3"])
    ].copy()
    out["context_text"] = out["context_text"].map(normalize_context)
    out = out[out["context_text"].astype(str).str.len().gt(0)].copy()
    if "nb_words" in out.columns:
        out = out[pd.to_numeric(out["nb_words"], errors="coerce").fillna(0).gt(0)].copy()
    out["route2_context_id"] = out["context_text"].map(context_id)
    out["context_word_count"] = out["context_text"].map(lambda value: len(str(value).split()))
    return out


def rename_route2_effort_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Rename real child effort columns for downstream Route 2 readability."""

    rename = {
        "nb_words": "real_child_words",
        "nb_morphemes": "real_child_morphemes",
        "nb_syllables_cmu_or_pkg": "real_child_syllables",
        "nb_syllables_pkg": "real_child_syllables_pkg",
        "nb_phonemes": "real_child_phonemes",
    }
    return frame.rename(columns={key: value for key, value in rename.items() if key in frame.columns})


def write_joined_chunk(path: Path, chunk: pd.DataFrame, *, first: bool) -> None:
    """Append one joined chunk to a CSV or CSV.GZ output."""

    path.parent.mkdir(parents=True, exist_ok=True)
    chunk.to_csv(path, mode="w" if first else "a", header=first, index=False, compression="infer")


def join_entropy_to_route2_smoke(
    *,
    route1_input: Path,
    features: pd.DataFrame,
    output_csv: Path,
    chunksize: int,
    max_output_rows: int | None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Chunk through real child rows and write matched rows expanded by settings."""

    join_features = prepare_features_for_join(features)
    sampled_context_ids = set(join_features["join_context_id"].astype(str))
    finite_feature_contexts = set(
        join_features[pd.to_numeric(join_features["response_entropy_bits"], errors="coerce").notna()][
            "join_context_id"
        ].astype(str)
    )

    eligible_rows = 0
    matched_rows = 0
    finite_entropy_source_rows = 0
    expanded_rows = 0
    missing_counter: Counter[str] = Counter()
    matched_counter: Counter[str] = Counter()
    context_text_lookup: dict[str, str] = {}
    context_k_by_id: dict[str, set[str]] = defaultdict(set)
    output_first = True
    truncated = False

    if output_csv.exists():
        output_csv.unlink()

    for chunk in load_route1_chunk(route1_input, chunksize=chunksize):
        real = route2_real_child_filter(chunk)
        if real.empty:
            continue
        eligible_rows += int(len(real))
        context_text_lookup.update(
            {
                str(row["route2_context_id"]): str(row["context_text"])
                for row in real[["route2_context_id", "context_text"]].drop_duplicates().to_dict("records")
            }
        )
        for cid, group in real.groupby("route2_context_id", sort=False):
            context_k_by_id[str(cid)].update(group["context_k"].astype(str).unique().tolist())

        is_matched = real["route2_context_id"].astype(str).isin(sampled_context_ids)
        matched = real[is_matched].copy()
        missing = real[~is_matched].copy()
        matched_rows += int(len(matched))
        finite_entropy_source_rows += int(matched["route2_context_id"].astype(str).isin(finite_feature_contexts).sum())
        if not missing.empty:
            missing_counter.update(missing["route2_context_id"].astype(str).value_counts().to_dict())
        if not matched.empty:
            matched_counter.update(matched["route2_context_id"].astype(str).value_counts().to_dict())
            matched = rename_route2_effort_columns(matched)
            expanded = matched.merge(
                join_features,
                left_on="route2_context_id",
                right_on="join_context_id",
                how="left",
                validate="many_to_many",
            )
            expanded["route2_entropy_join_status"] = expanded["response_entropy_bits"].notna().map(
                {True: "matched_finite_entropy", False: "matched_no_finite_entropy"}
            )
            expanded["route2_entropy_source"] = "final_generation_smoke_accepted_samples"
            if max_output_rows is not None and expanded_rows + len(expanded) > max_output_rows:
                remaining = max(int(max_output_rows - expanded_rows), 0)
                expanded = expanded.head(remaining).copy()
                truncated = True
            if not expanded.empty:
                write_joined_chunk(output_csv, expanded, first=output_first)
                output_first = False
                expanded_rows += int(len(expanded))
            if truncated:
                break

    if output_first:
        pd.DataFrame().to_csv(output_csv, index=False, compression="infer")

    summary = {
        "eligible_real_child_rows": eligible_rows,
        "matched_real_child_rows": matched_rows,
        "missing_real_child_rows": eligible_rows - matched_rows,
        "finite_entropy_source_rows": finite_entropy_source_rows,
        "expanded_join_rows_written": expanded_rows,
        "sampled_contexts_available": len(sampled_context_ids),
        "finite_entropy_contexts_available": len(finite_feature_contexts),
        "unique_matched_contexts": len(matched_counter),
        "unique_missing_contexts_observed": len(missing_counter),
        "output_truncated": truncated,
        "output_csv": str(output_csv),
    }
    audit = build_join_audit(
        summary=summary,
        missing_counter=missing_counter,
        matched_counter=matched_counter,
        context_text_lookup=context_text_lookup,
        context_k_by_id=context_k_by_id,
        features=features,
    )
    return audit, summary


def build_join_audit(
    *,
    summary: Mapping[str, object],
    missing_counter: Counter[str],
    matched_counter: Counter[str],
    context_text_lookup: Mapping[str, str],
    context_k_by_id: Mapping[str, set[str]],
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Build a long audit table for Route 2 feature joins."""

    rows: list[dict[str, object]] = []
    for metric, value in summary.items():
        rows.append({"audit_type": "summary", "metric": metric, "value": value})

    for cid, count in matched_counter.most_common(20):
        rows.append(
            {
                "audit_type": "top_matched_context",
                "context_id": cid,
                "real_child_rows": int(count),
                "context_k_values_observed": ";".join(sorted(context_k_by_id.get(cid, set()))),
                "context_text": context_text_lookup.get(cid, ""),
            }
        )

    for cid, count in missing_counter.most_common(20):
        rows.append(
            {
                "audit_type": "top_missing_context",
                "context_id": cid,
                "real_child_rows": int(count),
                "context_k_values_observed": ";".join(sorted(context_k_by_id.get(cid, set()))),
                "context_text": context_text_lookup.get(cid, ""),
            }
        )

    incomplete = features[
        pd.to_numeric(features.get("accepted_sample_count", pd.Series(dtype=float)), errors="coerce").lt(
            pd.to_numeric(features.get("target_accepted_samples", pd.Series(dtype=float)), errors="coerce")
        )
    ].copy()
    if not incomplete.empty:
        for _, row in incomplete.sort_values(["temperature", "prompt_variant", "context_id"]).iterrows():
            rows.append(
                {
                    "audit_type": "incomplete_entropy_setting",
                    "context_id": row.get("context_id", ""),
                    "context_text": row.get("context_text", ""),
                    "prompt_variant": row.get("prompt_variant", ""),
                    "temperature": row.get("temperature", ""),
                    "accepted_sample_count": row.get("accepted_sample_count", ""),
                    "target_accepted_samples": row.get("target_accepted_samples", ""),
                    "attempt_count": row.get("attempt_count", ""),
                    "rejection_rate": row.get("rejection_rate", ""),
                    "finite_entropy": pd.notna(pd.to_numeric(row.get("miller_madow_entropy_bits", math.nan), errors="coerce")),
                }
            )

    join_features = prepare_features_for_join(features)
    feature_counts = join_features.groupby("join_context_id").agg(
        feature_settings=("setting_id", "nunique"),
        finite_entropy_settings=("response_entropy_bits", lambda values: int(pd.to_numeric(values, errors="coerce").notna().sum())),
        prompt_variants=("prompt_variant", lambda values: ";".join(sorted(values.astype(str).unique()))),
        temperatures=("temperature", lambda values: ";".join(str(float(v)) for v in sorted(pd.to_numeric(values, errors="coerce").dropna().unique()))),
    )
    for cid, k_values in sorted(context_k_by_id.items()):
        if cid not in set(join_features["join_context_id"].astype(str)):
            continue
        counts = feature_counts.loc[cid].to_dict() if cid in feature_counts.index else {}
        rows.append(
            {
                "audit_type": "duplicate_context_window_check",
                "context_id": cid,
                "context_k_values_observed": ";".join(sorted(k_values)),
                "observed_context_k_count": len(k_values),
                "deduplicated_by_text": len(k_values) > 1,
                "feature_settings": counts.get("feature_settings", 0),
                "finite_entropy_settings": counts.get("finite_entropy_settings", 0),
                "prompt_variants": counts.get("prompt_variants", ""),
                "temperatures": counts.get("temperatures", ""),
                "context_text": context_text_lookup.get(cid, ""),
            }
        )
    return pd.DataFrame(rows)


def fit_tiny_sanity_models(joined_csv: Path, output_csv: Path) -> pd.DataFrame:
    """Fit tiny downstream smoke models by prompt/temperature and outcome."""

    if not joined_csv.exists() or joined_csv.stat().st_size == 0:
        out = pd.DataFrame([{"status": "skipped_empty_join_output"}])
        out.to_csv(output_csv, index=False)
        return out

    frame = pd.read_csv(joined_csv, dtype=str, keep_default_na=False, low_memory=False)
    if frame.empty:
        out = pd.DataFrame([{"status": "skipped_empty_join_output"}])
        out.to_csv(output_csv, index=False)
        return out

    numeric_cols = [
        "real_child_words",
        "real_child_morphemes",
        "real_child_syllables",
        "real_child_phonemes",
        "response_entropy_bits",
        "response_entropy_mean_sample_words",
        "context_word_count",
        "age_months",
        "temperature",
    ]
    for col in numeric_cols:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

    outcome_cols = [
        ("real_child_words", "real_child_words"),
        ("real_child_morphemes", "real_child_morphemes"),
        ("real_child_syllables", "real_child_syllables"),
        ("real_child_phonemes", "real_child_phonemes"),
    ]
    rows: list[dict[str, object]] = []
    predictors = ["response_entropy_bits", "response_entropy_mean_sample_words", "context_word_count", "age_months"]
    for (prompt_variant, temperature), group in frame.groupby(["prompt_variant", "temperature"], sort=True, dropna=False):
        for outcome, outcome_label in outcome_cols:
            if outcome not in group.columns:
                continue
            model_frame = group[[outcome, *predictors, "child_id", "route2_context_id"]].dropna().copy()
            model_frame = model_frame.rename(
                columns={
                    outcome: "outcome",
                    "response_entropy_bits": "response_entropy",
                    "response_entropy_mean_sample_words": "mean_sample_words",
                    "age_months": "age",
                }
            )
            formula = "outcome ~ response_entropy + mean_sample_words + context_word_count + age"
            base = {
                "prompt_variant": prompt_variant,
                "temperature": float(temperature) if pd.notna(temperature) else math.nan,
                "outcome": outcome_label,
                "formula": f"{outcome_label} ~ response_entropy + mean_sample_words + context_word_count + age",
                "n_rows": int(len(model_frame)),
                "n_children": int(model_frame["child_id"].nunique()) if "child_id" in model_frame.columns else 0,
                "n_contexts": int(model_frame["route2_context_id"].nunique())
                if "route2_context_id" in model_frame.columns
                else 0,
            }
            if len(model_frame) < 20 or model_frame["outcome"].nunique() < 2:
                rows.append({**base, "status": "skipped_insufficient_variation"})
                continue
            try:
                result = smf.ols(formula, data=model_frame).fit()
            except Exception as exc:  # pragma: no cover - depends on statsmodels internals
                rows.append({**base, "status": f"skipped_fit_error:{type(exc).__name__}"})
                continue
            for term in ["Intercept", "response_entropy", "mean_sample_words", "context_word_count", "age"]:
                rows.append(
                    {
                        **base,
                        "status": "fitted_smoke_only",
                        "term": term,
                        "estimate": float(result.params.get(term, math.nan)),
                        "std_error": float(result.bse.get(term, math.nan)),
                        "p_value": float(result.pvalues.get(term, math.nan)),
                        "r_squared": float(result.rsquared),
                        "aic": float(result.aic),
                    }
                )
    out = pd.DataFrame(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out


def matrix_from_pairwise(
    pairs: pd.DataFrame,
    *,
    family: str,
    row_col: str,
    col_col: str,
    value_col: str = "spearman_r",
) -> pd.DataFrame:
    """Build a symmetric matrix from pairwise correlation rows."""

    subset = pairs[pairs["comparison_family"].astype(str).eq(family)].copy()
    if subset.empty:
        return pd.DataFrame()
    labels = sorted(set(subset[row_col].astype(str)) | set(subset[col_col].astype(str)))
    matrix = pd.DataFrame(index=labels, columns=labels, dtype=float)
    for label in labels:
        matrix.loc[label, label] = 1.0
    for _, row in subset.iterrows():
        left = str(row[row_col])
        right = str(row[col_col])
        value = coerce_float(row[value_col])
        matrix.loc[left, right] = value
        matrix.loc[right, left] = value
    return matrix


def plot_outputs(
    *,
    features: pd.DataFrame,
    sample_size_corr: pd.DataFrame,
    temp_corr: pd.DataFrame,
    prompt_corr: pd.DataFrame,
    join_audit: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Write required scoring-smoke figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    finite = features[pd.to_numeric(features["miller_madow_entropy_bits"], errors="coerce").notna()].copy()
    if not finite.empty:
        plt.figure(figsize=(9, 5))
        sns.boxplot(data=finite, x="temperature", y="miller_madow_entropy_bits", hue="prompt_variant")
        plt.xlabel("Temperature")
        plt.ylabel("Response entropy (Miller-Madow bits)")
        plt.title("Entropy Distribution By Temperature")
        plt.tight_layout()
        path = fig_dir / "entropy_distribution_by_temperature.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Entropy distribution by temperature and prompt."})

        plt.figure(figsize=(8, 5))
        sns.scatterplot(
            data=finite,
            x="mean_sample_words",
            y="miller_madow_entropy_bits",
            hue="temperature",
            style="prompt_variant",
        )
        plt.xlabel("Mean sampled response length (words)")
        plt.ylabel("Response entropy (Miller-Madow bits)")
        plt.title("Entropy Versus Mean Sampled Response Length")
        plt.tight_layout()
        path = fig_dir / "entropy_vs_mean_sample_length.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Entropy versus expected sampled response length."})

    if not sample_size_corr.empty:
        plot_data = sample_size_corr[pd.to_numeric(sample_size_corr["shared_settings"], errors="coerce").gt(1)].copy()
        if not plot_data.empty:
            plot_data["setting_label"] = (
                plot_data["prompt_variant"].astype(str) + " T=" + plot_data["temperature"].astype(str)
            )
            plt.figure(figsize=(10, 5))
            sns.lineplot(data=plot_data, x="sample_size", y="spearman_r", hue="temperature", marker="o")
            plt.ylim(0, 1)
            plt.xlabel("Prefix accepted samples per setting")
            plt.ylabel("Spearman r versus full accepted sample")
            plt.title("Sample-Size Stability")
            plt.tight_layout()
            path = fig_dir / "sample_size_stability.png"
            plt.savefig(path, dpi=180)
            plt.close()
            rows.append({"figure_id": path.stem, "path": str(path), "description": "Rank stability of prefix entropies against full accepted samples."})

    temp_matrix = matrix_from_pairwise(
        temp_corr,
        family="temperature_all_prompts",
        row_col="temperature_a",
        col_col="temperature_b",
    )
    if not temp_matrix.empty:
        plt.figure(figsize=(7, 6))
        sns.heatmap(temp_matrix.astype(float), vmin=0, vmax=1, cmap="viridis", annot=True, fmt=".2f")
        plt.xlabel("Temperature")
        plt.ylabel("Temperature")
        plt.title("Temperature Rank-Correlation Heatmap")
        plt.tight_layout()
        path = fig_dir / "temperature_rank_correlation_heatmap.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Spearman context-ranking correlations across temperatures."})

    prompt_matrix = matrix_from_pairwise(
        prompt_corr,
        family="prompt_all_temperatures",
        row_col="prompt_variant_a",
        col_col="prompt_variant_b",
    )
    if not prompt_matrix.empty:
        plt.figure(figsize=(6.5, 5.5))
        sns.heatmap(prompt_matrix.astype(float), vmin=0, vmax=1, cmap="viridis", annot=True, fmt=".2f")
        plt.xlabel("Prompt variant")
        plt.ylabel("Prompt variant")
        plt.title("Prompt-Variant Rank-Correlation Heatmap")
        plt.tight_layout()
        path = fig_dir / "prompt_variant_rank_correlation_heatmap.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Spearman context-ranking correlations across prompt variants."})

    summary = join_audit[join_audit["audit_type"].astype(str).eq("summary")].copy()
    if not summary.empty:
        metrics = {
            str(row["metric"]): coerce_float(row["value"])
            for row in summary.to_dict("records")
            if str(row.get("metric", "")) in {"matched_real_child_rows", "missing_real_child_rows"}
        }
        if metrics:
            plt.figure(figsize=(7, 4.5))
            sns.barplot(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                hue=list(metrics.keys()),
                palette=["#4f8a8b", "#d08c60"],
                legend=False,
            )
            plt.ylabel("Real child rows")
            plt.xlabel("")
            plt.title("Joined Versus Missing Entropy Rows")
            plt.xticks(rotation=20, ha="right")
            plt.tight_layout()
            path = fig_dir / "joined_missing_entropy_audit.png"
            plt.savefig(path, dpi=180)
            plt.close()
            rows.append({"figure_id": path.stem, "path": str(path), "description": "Full-frame Route 2 join coverage for the 40-context smoke."})

    return pd.DataFrame(rows)


def image_md(figures: pd.DataFrame, figure_id: str, alt: str) -> str:
    """Return Markdown image syntax for a figure manifest row."""

    if figures.empty:
        return ""
    match = figures[figures["figure_id"].astype(str).eq(figure_id)]
    if match.empty:
        return ""
    path = Path(str(match["path"].iloc[0]))
    if not path.exists():
        return f"_Missing plot: `{path}`_"
    return f"![{alt}](../{path.as_posix()})"


def compact_input_summary(frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Summarize consumed generation-smoke inputs."""

    accepted = frames["accepted"]
    attempts = frames["attempts"]
    rejections = frames["rejections"]
    return pd.DataFrame(
        [
            {
                "artifact": "accepted_samples.csv.gz",
                "rows": len(accepted),
                "contexts": accepted["context_id"].nunique(),
                "settings": accepted["setting_id"].nunique(),
            },
            {
                "artifact": "all_attempts.csv.gz",
                "rows": len(attempts),
                "contexts": attempts["context_id"].nunique(),
                "settings": attempts["setting_id"].nunique(),
            },
            {
                "artifact": "rejection_summary_by_setting.csv",
                "rows": len(rejections),
                "contexts": rejections["context_id"].nunique(),
                "settings": rejections["setting_id"].nunique(),
            },
        ]
    )


def summary_metric(join_audit: pd.DataFrame, metric: str) -> float:
    """Read one numeric summary metric from the join audit."""

    subset = join_audit[
        join_audit["audit_type"].astype(str).eq("summary") & join_audit["metric"].astype(str).eq(metric)
    ]
    if subset.empty:
        return math.nan
    return coerce_float(subset["value"].iloc[0])


def decision_summary(
    *,
    features: pd.DataFrame,
    sample_size_corr: pd.DataFrame,
    temp_corr: pd.DataFrame,
    prompt_corr: pd.DataFrame,
    join_audit: pd.DataFrame,
) -> pd.DataFrame:
    """Create the explicit decision-output table requested by the prompt."""

    median_t05_t07 = temp_corr[
        (temp_corr["comparison_family"].astype(str).eq("temperature_within_prompt"))
        & (
            (
                pd.to_numeric(temp_corr["temperature_a"], errors="coerce").eq(0.5)
                & pd.to_numeric(temp_corr["temperature_b"], errors="coerce").eq(0.7)
            )
            | (
                pd.to_numeric(temp_corr["temperature_a"], errors="coerce").eq(0.7)
                & pd.to_numeric(temp_corr["temperature_b"], errors="coerce").eq(0.5)
            )
        )
    ]["spearman_r"]
    median_prompt = prompt_corr[prompt_corr["comparison_family"].astype(str).eq("prompt_within_temperature")][
        "spearman_r"
    ]
    max_accepted = int(pd.to_numeric(features["accepted_sample_count"], errors="coerce").max()) if not features.empty else 0
    min_reached = int((pd.to_numeric(features["accepted_sample_count"], errors="coerce") >= 20).sum()) if not features.empty else 0
    finite_settings = int(pd.to_numeric(features["miller_madow_entropy_bits"], errors="coerce").notna().sum())
    matched = summary_metric(join_audit, "matched_real_child_rows")
    missing = summary_metric(join_audit, "missing_real_child_rows")
    join_explainable = math.isfinite(matched) and math.isfinite(missing) and matched > 0
    sample_stability_20 = sample_size_corr[
        pd.to_numeric(sample_size_corr.get("sample_size", pd.Series(dtype=float)), errors="coerce").eq(20)
    ]["spearman_r"]
    rows = [
        {
            "question": "Is the entropy script ready to consume full Mila-scale samples?",
            "answer": "yes, as a CPU feature builder; full production still needs full sample artifacts",
            "evidence": f"wrote {finite_settings} finite entropy settings from final-smoke CSVs without regeneration",
        },
        {
            "question": "Are the generated samples stable enough for 100 accepted responses per context?",
            "answer": "not directly answerable from this final smoke",
            "evidence": f"final smoke has at most {max_accepted} accepted samples per setting; 100-sample stability must be checked on full/pilot samples",
        },
        {
            "question": "Do T=0.5 and T=0.7 give similar context rankings?",
            "answer": "mostly similar in this smoke" if coerce_float(median_t05_t07.median()) >= 0.75 else "moderately similar, worth keeping as sensitivity",
            "evidence": f"median within-prompt Spearman for T=0.5 versus T=0.7 = {coerce_float(median_t05_t07.median()):.3g}",
        },
        {
            "question": "Does prompt wording materially change the predictor?",
            "answer": "yes, enough to keep prompt wording visible as a design choice"
            if coerce_float(median_prompt.median()) < 0.8
            else "not strongly in this smoke, but keep prompt audit",
            "evidence": f"median prompt-within-temperature Spearman = {coerce_float(median_prompt.median()):.3g}",
        },
        {
            "question": "Are join gaps small and explainable?",
            "answer": "explainable but not small for the full frame, because this is a 40-context smoke",
            "evidence": f"matched real child rows = {matched:.0f}; missing full-frame rows = {missing:.0f}",
        },
        {
            "question": "What exact summary should be sent to supervisors?",
            "answer": "the measurement pipeline works; final-smoke entropy favors T=0.5 primary with T=0.7 sensitivity, but 20 samples cannot certify 100-sample production stability",
            "evidence": f"{min_reached}/480 settings reached 20 accepted samples; pathological incomplete settings remain auditable",
        },
        {
            "question": "Did first-20 stability prove full-sample stability?",
            "answer": "only within this small smoke cap",
            "evidence": f"median M=20 Spearman versus full = {coerce_float(sample_stability_20.median()):.3g}",
        },
        {
            "question": "Was k1/k2/k3 duplicate context text handled?",
            "answer": "yes, joins use the normalized context-text hash",
            "evidence": "duplicate context-window rows in the join audit share one entropy feature set by context text",
        },
    ]
    return pd.DataFrame(rows)


def build_report_markdown(
    *,
    output_dir: Path,
    fig_dir: Path,
    input_summary: pd.DataFrame,
    features: pd.DataFrame,
    stability: pd.DataFrame,
    sample_size_corr: pd.DataFrame,
    split_half: pd.DataFrame,
    temp_corr: pd.DataFrame,
    prompt_corr: pd.DataFrame,
    join_audit: pd.DataFrame,
    model_summary: pd.DataFrame,
    figures: pd.DataFrame,
    decisions: pd.DataFrame,
    sample_sizes_used: Sequence[int],
) -> str:
    """Build the final scoring-smoke report."""

    finite = features[pd.to_numeric(features["miller_madow_entropy_bits"], errors="coerce").notna()].copy()
    temp_summary = (
        finite.groupby("temperature")
        .agg(
            settings=("setting_id", "nunique"),
            mean_entropy_bits=("miller_madow_entropy_bits", "mean"),
            mean_unique_responses=("unique_response_count", "mean"),
            mean_top_probability=("top_response_probability", "mean"),
            mean_sample_words=("mean_sample_words", "mean"),
        )
        .reset_index()
        if not finite.empty
        else pd.DataFrame()
    )
    if "term" in model_summary.columns:
        entropy_terms = model_summary[model_summary["term"].astype(str).eq("response_entropy")].copy()
    else:
        entropy_terms = pd.DataFrame()
    entropy_terms = entropy_terms[
        [
            col
            for col in [
                "prompt_variant",
                "temperature",
                "outcome",
                "n_rows",
                "estimate",
                "std_error",
                "p_value",
                "r_squared",
                "status",
            ]
            if col in entropy_terms.columns
        ]
    ]
    join_summary = join_audit[join_audit["audit_type"].astype(str).eq("summary")][["metric", "value"]]
    duplicate_checks = join_audit[
        join_audit["audit_type"].astype(str).eq("duplicate_context_window_check")
        & pd.to_numeric(join_audit.get("observed_context_k_count", pd.Series(dtype=float)), errors="coerce").gt(1)
    ]

    return f"""# Route 2 Final Entropy Scoring Smoke

Created: 2026-06-16

This report scores the already generated final Route 2 response samples. No new
responses were generated. The entropy predictors below are computed from
accepted sampled child-turn strings, not from real child utterances.

## What Was Generated Versus What Was Scored

The generation smoke produced candidate child responses from Mistral. This
scoring smoke reads those artifacts, counts accepted response types, computes
entropy features, and joins those features back to real child rows for a small
plumbing model.

{markdown_table(input_summary, max_rows=10)}

## Entropy Formula

For each context, prompt variant, and temperature, accepted sampled responses
are normalized into response types. The empirical response entropy is:

```text
H(response | context) = - sum_r p_hat(r | c) log2 p_hat(r | c)
p_hat(r | c) = count(response_type = r) / accepted_sample_count
```

The primary predictor reported here is Miller-Madow corrected entropy in bits.
Settings with zero accepted samples remain in the feature table but have blank
entropy values.

## Normalization Choices

Primary type counting uses `casefold`: trim leading/trailing whitespace,
collapse internal whitespace, and ignore case while preserving punctuation.
The feature table also includes exact whitespace-normalized entropy and a
punctuation-stripped casefold sensitivity column.

## Entropy Features

{markdown_table(temp_summary, max_rows=20)}

{image_md(figures, "entropy_distribution_by_temperature", "entropy distribution by temperature")}

{image_md(figures, "entropy_vs_mean_sample_length", "entropy versus mean sampled length")}

## Sample-Size Stability

The final generation smoke targeted 20 accepted samples per setting, not 100.
Therefore the requested first-25/first-50 checks were adapted to available
prefix sizes:

```text
{", ".join(str(size) for size in sample_sizes_used)}
```

{markdown_table(sample_size_corr, max_rows=40)}

{markdown_table(split_half, max_rows=40)}

{image_md(figures, "sample_size_stability", "sample-size stability plot")}

## Temperature And Prompt Sensitivity

Temperature correlations compare context entropy rankings across temperatures
within the same prompt wrapper. Prompt correlations compare wrappers within the
same temperature.

{markdown_table(temp_corr[temp_corr["comparison_family"].astype(str).eq("temperature_within_prompt")], max_rows=30)}

{image_md(figures, "temperature_rank_correlation_heatmap", "temperature rank-correlation heatmap")}

{markdown_table(prompt_corr[prompt_corr["comparison_family"].astype(str).eq("prompt_within_temperature")], max_rows=30)}

{image_md(figures, "prompt_variant_rank_correlation_heatmap", "prompt variant rank-correlation heatmap")}

## Join Audit

The join uses the normalized context-text hash, not row position. The output
analysis smoke writes only matched real-child rows expanded over
prompt-temperature settings; the audit still counts the full eligible real
child frame so unsampled contexts remain visible.

{markdown_table(join_summary, max_rows=30)}

{image_md(figures, "joined_missing_entropy_audit", "joined versus missing entropy audit")}

Duplicate context-window checks show whether identical text appearing as k1,
k2, or k3 reused one deduplicated entropy feature set.

{markdown_table(duplicate_checks, max_rows=20)}

## Tiny Downstream Sanity Model

This is a plumbing check, not final science:

```text
real_child_words ~ response_entropy + mean_sample_words + context_word_count + age
```

The same smoke was attempted for morphemes, syllables, and phonemes when the
joined frame had enough variation.

{markdown_table(entropy_terms, max_rows=40)}

## Recommendation For Supervisor Meeting

Use this as evidence that the Route 2 measurement pipeline is now implemented:
accepted child-turn samples can be transformed into context-level response
entropy predictors and joined back to real child effort rows. The smoke remains
too small to certify 100 accepted responses per context; it is a final
pre-production feature and stability smoke, not the production analysis.

## Questions That Remain Before Full Production

- Should production use the `Caregiver`, `Parent`, or `Adult` wrapper, given
  the observed prompt sensitivity?
- Should T=0.5 be the primary estimate and T=0.7 a sensitivity estimate?
- Should contexts that repeatedly fail acceptance be excluded, resampled with a
  higher attempt cap, or retained as missing entropy?
- Should the production analysis average across prompts/temperatures or commit
  to one primary operational definition?

## Decision Output

{markdown_table(decisions, max_rows=20)}

## Output Files

- Feature table: `{output_dir / "context_response_entropy_features.csv"}`
- Stability table: `{output_dir / "context_response_entropy_stability.csv"}`
- Join audit: `{output_dir / "context_response_entropy_join_audit.csv"}`
- Temperature correlations: `{output_dir / "context_response_entropy_temperature_correlations.csv"}`
- Prompt correlations: `{output_dir / "context_response_entropy_prompt_correlations.csv"}`
- Joined analysis smoke: `{output_dir / "route2_analysis_smoke_with_entropy.csv.gz"}`
- Tiny model summary: `{output_dir / "route2_sanity_model_summary.csv"}`
- Manual review examples: `{output_dir / "manual_review_entropy_examples.csv"}`
- Figures: `{fig_dir}`
"""


def select_manual_review_examples(features: pd.DataFrame, accepted: pd.DataFrame, *, per_bucket: int = 20) -> pd.DataFrame:
    """Choose compact entropy examples for manual inspection."""

    if features.empty or accepted.empty:
        return pd.DataFrame()
    finite = features[pd.to_numeric(features["miller_madow_entropy_bits"], errors="coerce").notna()].copy()
    if finite.empty:
        return pd.DataFrame()
    picked_features = pd.concat(
        [
            finite.nsmallest(per_bucket, "miller_madow_entropy_bits"),
            finite.nlargest(per_bucket, "miller_madow_entropy_bits"),
            finite.nlargest(per_bucket, "rejection_rate"),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["setting_id"])
    sample_cols = [
        "setting_id",
        "sample_index",
        "quality_flags",
        "sampled_response_text",
        "raw_generated_text",
    ]
    sample_subset = accepted[[col for col in sample_cols if col in accepted.columns]].copy()
    sample_subset["sample_rank_for_review"] = sample_subset.groupby("setting_id").cumcount()
    sample_subset = sample_subset[sample_subset["sample_rank_for_review"] < 3].copy()
    out = picked_features[
        [
            "setting_id",
            "context_id",
            "context_text",
            "prompt_variant",
            "temperature",
            "accepted_sample_count",
            "rejection_rate",
            "unique_response_count",
            "top_response_probability",
            "miller_madow_entropy_bits",
            "mean_sample_words",
            "top_response_text",
        ]
    ].merge(sample_subset, on="setting_id", how="left")
    return out.sort_values(["temperature", "prompt_variant", "miller_madow_entropy_bits", "setting_id"])


def run_scoring_smoke(
    *,
    input_dir: Path,
    route1_input: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    normalization: str,
    sample_sizes: Sequence[int],
    chunksize: int,
    max_join_output_rows: int | None = None,
) -> dict[str, Path]:
    """Run the complete CPU-only entropy scoring smoke."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    frames = read_generation_smoke_inputs(input_dir)
    accepted = frames["accepted"]
    features = compute_entropy_features(
        accepted=accepted,
        attempts=frames["attempts"],
        rejections=frames["rejections"],
        quality=frames["quality"],
        normalization=normalization,
    )
    max_accepted = int(pd.to_numeric(features["accepted_sample_count"], errors="coerce").max()) if not features.empty else 0
    sample_sizes_used = [size for size in sample_sizes if size <= max_accepted]
    if not sample_sizes_used and max_accepted > 0:
        sample_sizes_used = [max_accepted]

    stability = compute_stability_rows(
        accepted,
        sample_sizes=sample_sizes_used,
        normalization=normalization,
        all_settings=features,
    )
    sample_corr = sample_size_rank_correlations(stability, sample_sizes=sample_sizes_used)
    split_half = split_half_reliability_summary(stability)
    temp_corr = temperature_correlations(features)
    prompt_corr = prompt_correlations(features)
    join_audit, _ = join_entropy_to_route2_smoke(
        route1_input=route1_input,
        features=features,
        output_csv=output_dir / "route2_analysis_smoke_with_entropy.csv.gz",
        chunksize=chunksize,
        max_output_rows=max_join_output_rows,
    )
    model_summary = fit_tiny_sanity_models(
        output_dir / "route2_analysis_smoke_with_entropy.csv.gz",
        output_dir / "route2_sanity_model_summary.csv",
    )
    manual_examples = select_manual_review_examples(features, accepted)
    figures = plot_outputs(
        features=features,
        sample_size_corr=sample_corr,
        temp_corr=temp_corr,
        prompt_corr=prompt_corr,
        join_audit=join_audit,
        fig_dir=fig_dir,
    )
    decisions = decision_summary(
        features=features,
        sample_size_corr=sample_corr,
        temp_corr=temp_corr,
        prompt_corr=prompt_corr,
        join_audit=join_audit,
    )

    paths = {
        "features": output_dir / "context_response_entropy_features.csv",
        "stability": output_dir / "context_response_entropy_stability.csv",
        "sample_size_correlations": output_dir / "context_response_entropy_sample_size_correlations.csv",
        "split_half": output_dir / "context_response_entropy_split_half_reliability.csv",
        "join_audit": output_dir / "context_response_entropy_join_audit.csv",
        "temperature_correlations": output_dir / "context_response_entropy_temperature_correlations.csv",
        "prompt_correlations": output_dir / "context_response_entropy_prompt_correlations.csv",
        "analysis_smoke": output_dir / "route2_analysis_smoke_with_entropy.csv.gz",
        "model_summary": output_dir / "route2_sanity_model_summary.csv",
        "manual_examples": output_dir / "manual_review_entropy_examples.csv",
        "figures": output_dir / "figure_manifest.csv",
        "decision_summary": output_dir / "route2_entropy_decision_summary.csv",
        "report_md": report_md,
        "report_html": report_html,
    }

    features.to_csv(paths["features"], index=False)
    stability.to_csv(paths["stability"], index=False)
    sample_corr.to_csv(paths["sample_size_correlations"], index=False)
    split_half.to_csv(paths["split_half"], index=False)
    join_audit.to_csv(paths["join_audit"], index=False)
    temp_corr.to_csv(paths["temperature_correlations"], index=False)
    prompt_corr.to_csv(paths["prompt_correlations"], index=False)
    manual_examples.to_csv(paths["manual_examples"], index=False)
    figures.to_csv(paths["figures"], index=False)
    decisions.to_csv(paths["decision_summary"], index=False)

    input_summary = compact_input_summary(frames)
    report = build_report_markdown(
        output_dir=output_dir,
        fig_dir=fig_dir,
        input_summary=input_summary,
        features=features,
        stability=stability,
        sample_size_corr=sample_corr,
        split_half=split_half,
        temp_corr=temp_corr,
        prompt_corr=prompt_corr,
        join_audit=join_audit,
        model_summary=model_summary,
        figures=figures,
        decisions=decisions,
        sample_sizes_used=sample_sizes_used,
    )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(report, encoding="utf-8")
    render_markdown_file(report_md, report_html)
    return paths


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--route1-input", type=Path, default=DEFAULT_ROUTE1_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--normalization", choices=["exact", "casefold", "casefold_punct_stripped"], default="casefold")
    parser.add_argument("--sample-sizes", default=",".join(str(size) for size in DEFAULT_SAMPLE_SIZES))
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--max-join-output-rows", type=int, default=None)
    args = parser.parse_args(argv)

    paths = run_scoring_smoke(
        input_dir=args.input_dir,
        route1_input=args.route1_input,
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        report_md=args.report_md,
        report_html=args.report_html,
        normalization=args.normalization,
        sample_sizes=split_int_csv(args.sample_sizes),
        chunksize=args.chunksize,
        max_join_output_rows=args.max_join_output_rows,
    )
    print(f"[OK] wrote entropy features to {paths['features']}")
    print(f"[OK] wrote joined Route 2 smoke to {paths['analysis_smoke']}")
    print(f"[OK] wrote report to {paths['report_html']}")


if __name__ == "__main__":
    main()
