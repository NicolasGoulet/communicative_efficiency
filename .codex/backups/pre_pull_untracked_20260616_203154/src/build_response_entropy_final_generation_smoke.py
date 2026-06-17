#!/usr/bin/env python3
"""Run the final Route 2 response-generation smoke test.

This script prepares a small balanced prompt manifest, samples child-turn
responses from Mistral with true end-of-turn stopping, logs every accepted and
rejected attempt, and renders the pre-Slurm smoke report.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
import time
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import torch
from transformers import StoppingCriteria, StoppingCriteriaList

try:
    from render_markdown_report import render_markdown_file
    from sample_context_responses import load_transformers_model, model_input_device
    from summarize_response_entropy_samples import (
        canonical_response,
        empirical_entropy_bits,
        miller_madow_entropy_bits,
        response_effort_counts,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.render_markdown_report import render_markdown_file
    from src.sample_context_responses import load_transformers_model, model_input_device
    from src.summarize_response_entropy_samples import (
        canonical_response,
        empirical_entropy_bits,
        miller_madow_entropy_bits,
        response_effort_counts,
    )


DEFAULT_INPUT_MANIFEST = Path("results/response_entropy_pilot_grid/pilot_generation_manifest.csv")
DEFAULT_OUTPUT_DIR = Path("results/response_entropy_final_generation_smoke")
DEFAULT_FIG_DIR = Path("figs/response_entropy_final_generation_smoke")
DEFAULT_REPORT_MD = Path("docs/response_entropy_final_generation_smoke.md")
DEFAULT_REPORT_HTML = Path("docs/response_entropy_final_generation_smoke.html")
DEFAULT_MODEL = "mistralai/Mistral-7B-v0.3"
DEFAULT_TEMPERATURES = (0.3, 0.5, 0.7, 1.0)
DEFAULT_STOP_STRINGS = ("\nCaregiver:", "\nParent:", "\nAdult:", "\nChild:", "\nCHI:", "\n")
DEFAULT_PROMPT_VARIANTS: Mapping[str, str] = {
    "Caregiver": "Caregiver: {context}\nChild:",
    "Parent": "Parent: {context}\nChild:",
    "Adult": "Adult: {context}\nChild:",
}
DEFAULT_SEED = 20260616

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

REJECTION_REASONS = [
    "empty_response",
    "no_boundary_before_cap",
    "repetition_loop",
    "metadata_or_prose_drift",
    "malformed_response",
    "speaker_label_inside_response",
    "other_quality_flag",
]

ATTEMPT_COLUMNS = [
    "setting_id",
    "smoke_manifest_row",
    "smoke_context_row",
    "source_manifest_row",
    "context_id",
    "context_text",
    "context_word_count",
    "context_length_bucket",
    "prompt_variant",
    "prompt_template",
    "prompt_text",
    "temperature",
    "attempt_index",
    "accepted",
    "sample_index",
    "attempts_needed_for_acceptance",
    "rejection_reason",
    "quality_flags",
    *QUALITY_FLAG_COLUMNS,
    "raw_generated_text",
    "sampled_response_text",
    "generated_token_count",
    "hit_max_new_tokens",
    "stopped_by_end_of_turn",
    "end_of_turn_marker",
    "model_used",
    "max_new_tokens",
    "top_p",
    "top_k",
    "seed_used",
    "target_accepted_samples",
    "max_attempts_per_setting",
]

ACCEPTED_COLUMNS = [
    "setting_id",
    "smoke_manifest_row",
    "smoke_context_row",
    "source_manifest_row",
    "context_id",
    "context_text",
    "context_word_count",
    "context_length_bucket",
    "prompt_variant",
    "prompt_template",
    "prompt_text",
    "temperature",
    "sample_index",
    "attempt_index",
    "attempts_needed_for_acceptance",
    "quality_flags",
    *QUALITY_FLAG_COLUMNS,
    "raw_generated_text",
    "sampled_response_text",
    "generated_token_count",
    "hit_max_new_tokens",
    "stopped_by_end_of_turn",
    "end_of_turn_marker",
    "model_used",
    "max_new_tokens",
    "top_p",
    "top_k",
    "seed_used",
]

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['_-][A-Za-z0-9]+)?")
SPACES_RE = re.compile(r"\s+")
SPEAKER_LABEL_RE = re.compile(r"(?i)(?:^|\s)(caregiver|parent|adult|child|chi)\s*:")
METADATA_START_RE = re.compile(
    r"(?is)^\s*(?:[#\[\{\(]|transcript\b|scene\b|note\b|title\b|chapter\b|"
    r"example\b|prompt\b|response\b|as an ai\b|the child\b|the caregiver\b|"
    r"caregiver says\b|child says\b)"
)


class EndOfTurnStoppingCriteria(StoppingCriteria):
    """Stop each sequence once its generated suffix contains a turn boundary."""

    def __init__(self, tokenizer, *, prompt_token_width: int, stop_strings: Sequence[str]):
        super().__init__()
        self.tokenizer = tokenizer
        self.prompt_token_width = int(prompt_token_width)
        self.stop_strings = tuple(stop_strings)

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> torch.BoolTensor:
        decisions: list[bool] = []
        for row in input_ids:
            generated = row[self.prompt_token_width :]
            if len(generated) == 0:
                decisions.append(False)
                continue
            text = self.tokenizer.decode(generated, skip_special_tokens=True)
            decisions.append(any(marker in text for marker in self.stop_strings))
        return torch.tensor(decisions, dtype=torch.bool, device=input_ids.device)


def parse_float_csv(value: str | Sequence[float]) -> list[float]:
    """Parse comma-separated floats."""

    if isinstance(value, str):
        return [float(part.strip()) for part in value.split(",") if part.strip()]
    return [float(part) for part in value]


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 80, digits: int = 4) -> str:
    """Render a compact Markdown table."""

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


def context_length_bucket(word_count: int | float | str) -> str:
    """Return a compact context-length bucket label."""

    value = pd.to_numeric(word_count, errors="coerce")
    if pd.isna(value):
        return "unknown"
    count = int(value)
    if count <= 1:
        return "01_one_word"
    if count <= 4:
        return "02_two_to_four"
    if count <= 9:
        return "03_five_to_nine"
    return "04_ten_plus"


def first_end_of_turn_boundary(text: object, *, stop_strings: Sequence[str] = DEFAULT_STOP_STRINGS) -> tuple[int, str]:
    """Return the first boundary position and marker label, or ``(-1, "")``."""

    raw = str(text or "")
    best_position: int | None = None
    best_marker = ""
    for marker in stop_strings:
        position = raw.find(marker)
        if position < 0:
            continue
        if best_position is None or position < best_position or (
            position == best_position and len(marker) > len(best_marker)
        ):
            best_position = position
            best_marker = marker
    if best_position is None:
        return -1, ""
    return best_position, best_marker.replace("\n", "\\n")


def trim_at_end_of_turn(text: object, *, stop_strings: Sequence[str] = DEFAULT_STOP_STRINGS) -> tuple[str, bool, str]:
    """Trim generated text at the first end-of-turn marker."""

    raw = str(text or "")
    position, marker = first_end_of_turn_boundary(raw, stop_strings=stop_strings)
    if position < 0:
        return raw.strip(), False, ""
    return raw[:position].strip(), True, marker


def word_tokens(text: object) -> list[str]:
    """Return word-like tokens for deterministic quality checks."""

    return WORD_RE.findall(str(text or ""))


def normalize_for_copy(text: object) -> str:
    """Normalize text for possible context-copy detection."""

    value = str(text or "").casefold()
    value = re.sub(r"[^a-z0-9'\s]+", " ", value)
    return SPACES_RE.sub(" ", value).strip()


def has_repetition_loop(text: object) -> bool:
    """Detect obvious unigram or short-phrase repetition loops."""

    tokens = [token.casefold() for token in word_tokens(text)]
    if len(tokens) < 6:
        return False
    for ngram_size, threshold in ((1, 6), (2, 4), (3, 3)):
        previous: tuple[str, ...] | None = None
        run = 0
        for idx in range(0, len(tokens) - ngram_size + 1, ngram_size):
            current = tuple(tokens[idx : idx + ngram_size])
            if current == previous:
                run += 1
            else:
                previous = current
                run = 1
            if run >= threshold:
                return True
    return False


def possible_context_copy(response: object, context: object) -> bool:
    """Flag responses that may be copied from the caregiver context."""

    response_norm = normalize_for_copy(response)
    context_norm = normalize_for_copy(context)
    if not response_norm or not context_norm:
        return False
    if response_norm == context_norm:
        return True
    if len(response_norm) >= 15 and (response_norm in context_norm or context_norm in response_norm):
        return True
    return False


def classify_quality(
    *,
    raw_generated_text: object,
    sampled_response_text: object,
    context_text: object,
    hit_max_new_tokens: bool,
    stopped_by_end_of_turn: bool,
) -> dict[str, object]:
    """Return deterministic quality flags and the rejection reason."""

    response = str(sampled_response_text or "").strip()
    flags = {
        "empty_first_line_response": response == "",
        "speaker_label_inside_response": bool(SPEAKER_LABEL_RE.search(response)),
        "metadata_or_prose_start": bool(METADATA_START_RE.search(response)),
        "repetition_loop": has_repetition_loop(response),
        "no_end_of_turn_boundary_before_cap": bool(hit_max_new_tokens and not stopped_by_end_of_turn),
        "possible_context_copy": possible_context_copy(response, context_text),
        "very_long_first_line_response": len(word_tokens(response)) > 20 or len(response) > 160,
        "malformed_response": bool(response) and not bool(word_tokens(response)),
    }
    reason = ""
    if flags["empty_first_line_response"]:
        reason = "empty_response"
    elif flags["no_end_of_turn_boundary_before_cap"]:
        reason = "no_boundary_before_cap"
    elif flags["repetition_loop"]:
        reason = "repetition_loop"
    elif flags["metadata_or_prose_start"]:
        reason = "metadata_or_prose_drift"
    elif flags["malformed_response"]:
        reason = "malformed_response"
    elif flags["speaker_label_inside_response"]:
        reason = "speaker_label_inside_response"
    elif flags["very_long_first_line_response"]:
        reason = "other_quality_flag"

    quality_flags = ";".join(column for column in QUALITY_FLAG_COLUMNS if flags[column])
    return {
        **{column: int(flags[column]) for column in QUALITY_FLAG_COLUMNS},
        "quality_flags": quality_flags,
        "rejection_reason": reason,
        "accepted": int(reason == ""),
    }


def format_prompt(context: object, template: str) -> str:
    """Insert a context into a prompt template."""

    return str(template).replace("{context}", str(context))


def build_setting_id(context_id: str, prompt_variant: str, temperature: float) -> str:
    """Return a stable context-prompt-temperature setting identifier."""

    return f"{context_id}::{prompt_variant}::T{float(temperature):g}"


def build_smoke_manifest(
    *,
    input_manifest: Path,
    output_dir: Path,
    contexts_per_bucket: int,
    prompt_variants: Mapping[str, str],
    temperatures: Sequence[float],
    accepted_samples_per_setting: int,
    max_attempts_per_setting: int,
    max_new_tokens: int,
    seed: int,
    model_name: str,
) -> dict[str, Path]:
    """Select 40 balanced contexts and expand them across prompt variants."""

    output_dir.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(input_manifest, dtype=str, keep_default_na=False)
    required = {"context_id", "context_text", "context_word_count"}
    missing = required - set(source.columns)
    if missing:
        raise KeyError(f"{input_manifest} missing required columns: {sorted(missing)}")

    source = source.copy()
    source["context_word_count_numeric"] = pd.to_numeric(source["context_word_count"], errors="coerce")
    source["context_length_bucket"] = source["context_word_count_numeric"].map(context_length_bucket)

    selected_parts: list[pd.DataFrame] = []
    audit_rows: list[dict[str, object]] = []
    for bucket_index, (bucket, group) in enumerate(sorted(source.groupby("context_length_bucket"), key=lambda item: item[0])):
        group = group.sort_values(["context_word_count_numeric", "context_id"]).copy()
        take = min(contexts_per_bucket, len(group))
        selected = group.sample(n=take, random_state=seed + bucket_index).sort_values(
            ["context_word_count_numeric", "context_id"]
        )
        selected_parts.append(selected)
        audit_rows.append(
            {
                "audit_scope": "context_bucket",
                "context_length_bucket": bucket,
                "available_contexts": int(len(group)),
                "selected_base_contexts": int(take),
                "prompt_variants": len(prompt_variants),
                "temperatures": ",".join(str(float(t)) for t in temperatures),
                "accepted_samples_per_setting": int(accepted_samples_per_setting),
                "max_attempts_per_setting": int(max_attempts_per_setting),
                "planned_accepted_samples": int(take * len(prompt_variants) * len(temperatures) * accepted_samples_per_setting),
                "max_attempt_rows": int(take * len(prompt_variants) * len(temperatures) * max_attempts_per_setting),
            }
        )
    selected_contexts = pd.concat(selected_parts, ignore_index=True)
    selected_contexts.insert(0, "smoke_context_row", range(len(selected_contexts)))

    expanded_rows: list[dict[str, object]] = []
    for context_row in selected_contexts.to_dict("records"):
        source_manifest_row = context_row.get("manifest_row", context_row.get("smoke_context_row", ""))
        for prompt_variant, template in prompt_variants.items():
            row = dict(context_row)
            row.update(
                {
                    "source_manifest_row": source_manifest_row,
                    "prompt_variant": prompt_variant,
                    "prompt_template": template,
                    "prompt_text": format_prompt(context_row["context_text"], template),
                    "smoke_seed": int(seed),
                    "target_accepted_samples": int(accepted_samples_per_setting),
                    "max_attempts_per_setting": int(max_attempts_per_setting),
                    "max_new_tokens": int(max_new_tokens),
                    "temperatures": ",".join(str(float(t)) for t in temperatures),
                    "model_used": model_name,
                }
            )
            expanded_rows.append(row)
    manifest = pd.DataFrame(expanded_rows)
    manifest.insert(0, "smoke_manifest_row", range(len(manifest)))

    total_base_contexts = int(selected_contexts["context_id"].nunique())
    audit_rows.append(
        {
            "audit_scope": "total",
            "context_length_bucket": "all",
            "available_contexts": int(source["context_id"].nunique()),
            "selected_base_contexts": total_base_contexts,
            "prompt_variants": len(prompt_variants),
            "temperatures": ",".join(str(float(t)) for t in temperatures),
            "accepted_samples_per_setting": int(accepted_samples_per_setting),
            "max_attempts_per_setting": int(max_attempts_per_setting),
            "planned_accepted_samples": int(total_base_contexts * len(prompt_variants) * len(temperatures) * accepted_samples_per_setting),
            "max_attempt_rows": int(total_base_contexts * len(prompt_variants) * len(temperatures) * max_attempts_per_setting),
        }
    )

    paths = {
        "manifest": output_dir / "smoke_manifest.csv",
        "audit": output_dir / "smoke_manifest_audit.csv",
        "spec": output_dir / "smoke_method_spec.json",
    }
    manifest.to_csv(paths["manifest"], index=False)
    pd.DataFrame(audit_rows).to_csv(paths["audit"], index=False)
    spec = {
        "source_manifest": str(input_manifest),
        "unique_base_contexts": total_base_contexts,
        "manifest_rows_context_prompt": int(len(manifest)),
        "temperatures": [float(value) for value in temperatures],
        "prompt_variants": dict(prompt_variants),
        "accepted_samples_per_context_temperature_prompt": int(accepted_samples_per_setting),
        "max_attempts_per_context_temperature_prompt": int(max_attempts_per_setting),
        "max_new_tokens": int(max_new_tokens),
        "stop_strings": list(DEFAULT_STOP_STRINGS),
        "top_p": 0.95,
        "top_k": 0,
        "model": model_name,
        "seed": int(seed),
    }
    paths["spec"].write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return paths


def output_path(output_dir: Path, name: str) -> Path:
    """Return a path under the smoke output directory."""

    return output_dir / name


def append_rows(path: Path, rows: list[dict[str, object]], columns: Sequence[str]) -> int:
    """Append rows to a CSV or CSV.GZ with a fixed schema."""

    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[list(columns)]
    write_header = not path.exists() or path.stat().st_size == 0
    if path.suffix == ".gz":
        with gzip.open(path, "at", encoding="utf-8", newline="") as handle:
            frame.to_csv(handle, index=False, header=write_header, quoting=csv.QUOTE_ALL, lineterminator="\n")
    else:
        frame.to_csv(path, index=False, mode="a", header=write_header, quoting=csv.QUOTE_ALL, lineterminator="\n")
    return len(frame)


def existing_setting_state(output_dir: Path) -> dict[str, dict[str, int]]:
    """Return accepted counts and resume counters for existing outputs."""

    all_attempts_path = output_path(output_dir, "all_attempts.csv.gz")
    if not all_attempts_path.exists():
        return {}
    try:
        attempts = pd.read_csv(
            all_attempts_path,
            usecols=["setting_id", "attempt_index", "accepted"],
            dtype=str,
            keep_default_na=False,
            on_bad_lines="skip",
        )
    except (EOFError, gzip.BadGzipFile, pd.errors.EmptyDataError, ValueError):
        return {}
    attempts["attempt_index_num"] = pd.to_numeric(attempts["attempt_index"], errors="coerce")
    attempts["accepted_int"] = pd.to_numeric(attempts["accepted"], errors="coerce").fillna(0).astype(int)
    state: dict[str, dict[str, int]] = {}
    for setting_id, group in attempts.groupby("setting_id", dropna=False):
        ordered = group.dropna(subset=["attempt_index_num"]).sort_values("attempt_index_num")
        if ordered.empty:
            continue
        accepted_count = int(ordered["accepted_int"].sum())
        max_attempt_index = int(ordered["attempt_index_num"].max())
        accepted_attempts = ordered.loc[ordered["accepted_int"] == 1, "attempt_index_num"]
        last_accept = int(accepted_attempts.max()) if not accepted_attempts.empty else -1
        state[str(setting_id)] = {
            "accepted_count": accepted_count,
            "next_attempt_index": max_attempt_index + 1,
            "attempts_since_last_accept": max_attempt_index - last_accept if last_accept >= 0 else max_attempt_index + 1,
        }
    return state


@torch.no_grad()
def generate_attempt_batch(
    *,
    setting: Mapping[str, object],
    tokenizer,
    model,
    temperature: float,
    n_attempts: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    seed: int,
    model_name: str,
    stop_strings: Sequence[str],
) -> list[dict[str, object]]:
    """Generate one batch of attempts for a context-prompt-temperature setting."""

    prompts = [str(setting["prompt_text"])] * int(n_attempts)
    input_device = model_input_device(model)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    encoded = tokenizer(prompts, return_tensors="pt", padding=True).to(input_device)
    prompt_token_width = int(encoded["input_ids"].shape[1])
    stopping_criteria = StoppingCriteriaList(
        [EndOfTurnStoppingCriteria(tokenizer, prompt_token_width=prompt_token_width, stop_strings=stop_strings)]
    )
    outputs = model.generate(
        **encoded,
        do_sample=True,
        temperature=float(temperature),
        top_p=float(top_p),
        top_k=int(top_k),
        max_new_tokens=int(max_new_tokens),
        num_return_sequences=1,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
        renormalize_logits=True,
        stopping_criteria=stopping_criteria,
    )
    rows: list[dict[str, object]] = []
    for output_ids in outputs:
        generated_ids = output_ids[prompt_token_width:]
        raw_generated = tokenizer.decode(generated_ids, skip_special_tokens=True)
        response, stopped, marker = trim_at_end_of_turn(raw_generated, stop_strings=stop_strings)
        generated_token_count = int(len(generated_ids))
        hit_max = int((not stopped) and generated_token_count >= int(max_new_tokens))
        quality = classify_quality(
            raw_generated_text=raw_generated,
            sampled_response_text=response,
            context_text=setting["context_text"],
            hit_max_new_tokens=bool(hit_max),
            stopped_by_end_of_turn=bool(stopped),
        )
        rows.append(
            {
                **quality,
                "raw_generated_text": raw_generated,
                "sampled_response_text": response,
                "generated_token_count": generated_token_count,
                "hit_max_new_tokens": hit_max,
                "stopped_by_end_of_turn": int(stopped),
                "end_of_turn_marker": marker,
                "model_used": model_name,
                "max_new_tokens": int(max_new_tokens),
                "top_p": float(top_p),
                "top_k": int(top_k),
                "seed_used": int(seed),
            }
        )
    return rows


def setting_base_row(setting: Mapping[str, object], *, temperature: float) -> dict[str, object]:
    """Return setting metadata shared by every attempt row."""

    context_word_count = setting.get("context_word_count", setting.get("context_word_count_numeric", ""))
    return {
        "setting_id": build_setting_id(str(setting["context_id"]), str(setting["prompt_variant"]), float(temperature)),
        "smoke_manifest_row": setting.get("smoke_manifest_row", ""),
        "smoke_context_row": setting.get("smoke_context_row", ""),
        "source_manifest_row": setting.get("source_manifest_row", setting.get("manifest_row", "")),
        "context_id": setting["context_id"],
        "context_text": setting["context_text"],
        "context_word_count": context_word_count,
        "context_length_bucket": setting.get("context_length_bucket", context_length_bucket(context_word_count)),
        "prompt_variant": setting["prompt_variant"],
        "prompt_template": setting["prompt_template"],
        "prompt_text": setting["prompt_text"],
        "temperature": float(temperature),
        "target_accepted_samples": setting.get("target_accepted_samples", ""),
        "max_attempts_per_setting": setting.get("max_attempts_per_setting", ""),
    }


def sample_final_smoke(
    *,
    output_dir: Path,
    manifest_csv: Path,
    model_name: str,
    temperatures: Sequence[float],
    accepted_samples_per_setting: int,
    max_attempts_per_setting: int,
    batch_attempts: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    device: str,
    dtype: str,
    model_dir: Path | None,
    seed: int,
    stop_strings: Sequence[str] = DEFAULT_STOP_STRINGS,
) -> dict[str, Path]:
    """Sample until each setting reaches the target accepted responses or cap."""

    manifest = pd.read_csv(manifest_csv, dtype=str, keep_default_na=False)
    required = {"context_id", "context_text", "prompt_variant", "prompt_template", "prompt_text"}
    missing = required - set(manifest.columns)
    if missing:
        raise KeyError(f"{manifest_csv} missing required columns: {sorted(missing)}")
    if batch_attempts < 1:
        raise ValueError("batch_attempts must be >= 1")

    output_dir.mkdir(parents=True, exist_ok=True)
    all_attempts_path = output_path(output_dir, "all_attempts.csv.gz")
    accepted_path = output_path(output_dir, "accepted_samples.csv.gz")
    state = existing_setting_state(output_dir)
    tokenizer, model = load_transformers_model(model_name, device=device, dtype=dtype, model_dir=model_dir)

    start_time = time.time()
    total_new_attempts = 0
    total_new_accepted = 0
    settings_total = len(manifest) * len(temperatures)
    setting_counter = 0
    for setting in manifest.to_dict("records"):
        for temperature in temperatures:
            setting_counter += 1
            base = setting_base_row(setting, temperature=float(temperature))
            setting_id = str(base["setting_id"])
            setting_state = state.get(
                setting_id,
                {"accepted_count": 0, "next_attempt_index": 0, "attempts_since_last_accept": 0},
            )
            accepted_count = int(setting_state["accepted_count"])
            attempt_index = int(setting_state["next_attempt_index"])
            attempts_since_accept = int(setting_state["attempts_since_last_accept"])
            if accepted_count >= accepted_samples_per_setting:
                print(f"[INFO] setting {setting_counter:,}/{settings_total:,} already complete: {setting_id}")
                continue
            while accepted_count < accepted_samples_per_setting and attempt_index < max_attempts_per_setting:
                n_attempts = min(
                    int(batch_attempts),
                    int(max_attempts_per_setting - attempt_index),
                    int(accepted_samples_per_setting - accepted_count),
                )
                if n_attempts <= 0:
                    break
                batch_seed = int(seed + setting_counter * 100_000 + int(round(float(temperature) * 1000)) + attempt_index)
                generated_rows = generate_attempt_batch(
                    setting=setting,
                    tokenizer=tokenizer,
                    model=model,
                    temperature=float(temperature),
                    n_attempts=n_attempts,
                    max_new_tokens=max_new_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    seed=batch_seed,
                    model_name=model_name,
                    stop_strings=stop_strings,
                )
                attempt_rows: list[dict[str, object]] = []
                accepted_rows: list[dict[str, object]] = []
                for generated in generated_rows:
                    attempts_since_accept += 1
                    is_accepted = int(generated["accepted"]) == 1
                    row = {
                        **base,
                        **generated,
                        "attempt_index": attempt_index,
                        "sample_index": accepted_count if is_accepted else "",
                        "attempts_needed_for_acceptance": attempts_since_accept if is_accepted else "",
                        "target_accepted_samples": int(accepted_samples_per_setting),
                        "max_attempts_per_setting": int(max_attempts_per_setting),
                    }
                    attempt_rows.append(row)
                    if is_accepted:
                        accepted_rows.append(row)
                        accepted_count += 1
                        attempts_since_accept = 0
                    attempt_index += 1
                total_new_attempts += append_rows(all_attempts_path, attempt_rows, ATTEMPT_COLUMNS)
                total_new_accepted += append_rows(accepted_path, accepted_rows, ACCEPTED_COLUMNS)
            status = "complete" if accepted_count >= accepted_samples_per_setting else "incomplete"
            print(
                f"[INFO] setting {setting_counter:,}/{settings_total:,} {status}: "
                f"{setting_id} accepted={accepted_count}/{accepted_samples_per_setting} attempts={attempt_index}"
            )
    print(f"[BENCH] elapsed_seconds={time.time() - start_time:.1f}")
    print(f"[OK] new attempts={total_new_attempts:,} new accepted={total_new_accepted:,}")
    return {"all_attempts": all_attempts_path, "accepted_samples": accepted_path}


def read_smoke_outputs(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read all attempt and accepted sample outputs."""

    attempts_path = output_path(output_dir, "all_attempts.csv.gz")
    accepted_path = output_path(output_dir, "accepted_samples.csv.gz")
    if not attempts_path.exists():
        raise FileNotFoundError(attempts_path)
    if not accepted_path.exists():
        raise FileNotFoundError(accepted_path)
    attempts = pd.read_csv(attempts_path, dtype=str, keep_default_na=False, low_memory=False, on_bad_lines="skip")
    accepted = pd.read_csv(accepted_path, dtype=str, keep_default_na=False, low_memory=False, on_bad_lines="skip")
    for frame in (attempts, accepted):
        for column in ["temperature", "attempt_index", "sample_index", "generated_token_count"]:
            if column in frame.columns:
                frame[f"{column}_num"] = pd.to_numeric(frame[column], errors="coerce")
        for column in ["accepted", "hit_max_new_tokens", "stopped_by_end_of_turn", *QUALITY_FLAG_COLUMNS]:
            if column in frame.columns:
                frame[f"{column}_int"] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype(int)
    return attempts, accepted


def summarize_rejections(attempts: pd.DataFrame) -> pd.DataFrame:
    """Summarize accepted/rejected attempt counts by setting."""

    rows: list[dict[str, object]] = []
    group_cols = ["setting_id", "context_id", "prompt_variant", "temperature_num"]
    for keys, group in attempts.groupby(group_cols, dropna=False, sort=True):
        setting_id, context_id, prompt_variant, temperature = keys
        attempts_n = int(len(group))
        accepted_n = int(group["accepted_int"].sum())
        rejected_n = int(attempts_n - accepted_n)
        target = pd.to_numeric(group.get("target_accepted_samples", pd.Series(dtype=str)), errors="coerce").dropna()
        max_attempts = pd.to_numeric(group.get("max_attempts_per_setting", pd.Series(dtype=str)), errors="coerce").dropna()
        row = {
            "setting_id": setting_id,
            "context_id": context_id,
            "prompt_variant": prompt_variant,
            "temperature": float(temperature),
            "attempts": attempts_n,
            "accepted_samples": accepted_n,
            "rejected_attempts": rejected_n,
            "rejection_rate": rejected_n / attempts_n if attempts_n else math.nan,
            "target_accepted_samples": int(target.iloc[0]) if len(target) else "",
            "max_attempts_per_setting": int(max_attempts.iloc[0]) if len(max_attempts) else "",
            "reached_target": bool(len(target) and accepted_n >= int(target.iloc[0])),
            "mean_attempts_per_accepted": attempts_n / accepted_n if accepted_n else math.nan,
        }
        rejected = group[group["accepted_int"] == 0]
        for reason in REJECTION_REASONS:
            count = int((rejected["rejection_reason"] == reason).sum())
            row[f"{reason}_count"] = count
            row[f"{reason}_rate"] = count / attempts_n if attempts_n else math.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["temperature", "prompt_variant", "context_id"]).reset_index(drop=True)


def summarize_quality_flags(attempts: pd.DataFrame) -> pd.DataFrame:
    """Summarize quality-flag rates by setting."""

    rows: list[dict[str, object]] = []
    group_cols = ["setting_id", "context_id", "prompt_variant", "temperature_num"]
    for keys, group in attempts.groupby(group_cols, dropna=False, sort=True):
        setting_id, context_id, prompt_variant, temperature = keys
        accepted = group[group["accepted_int"] == 1]
        row = {
            "setting_id": setting_id,
            "context_id": context_id,
            "prompt_variant": prompt_variant,
            "temperature": float(temperature),
            "attempts": int(len(group)),
            "accepted_samples": int(len(accepted)),
        }
        for flag in QUALITY_FLAG_COLUMNS:
            flag_col = f"{flag}_int"
            row[f"{flag}_attempt_rate"] = float(group[flag_col].mean()) if flag_col in group.columns and len(group) else math.nan
            row[f"{flag}_accepted_rate"] = (
                float(accepted[flag_col].mean()) if flag_col in accepted.columns and len(accepted) else math.nan
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["temperature", "prompt_variant", "context_id"]).reset_index(drop=True)


def safe_corr(left: pd.Series, right: pd.Series, *, method: str) -> float:
    """Return a correlation or NaN when too few nonconstant pairs exist."""

    frame = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(frame) < 2 or frame["left"].nunique() < 2 or frame["right"].nunique() < 2:
        return math.nan
    return float(frame["left"].corr(frame["right"], method=method))


def accepted_entropy_features(accepted: pd.DataFrame, *, normalization: str) -> pd.DataFrame:
    """Compute empirical response entropy by context, prompt variant, and temperature."""

    rows: list[dict[str, object]] = []
    group_cols = ["context_id", "prompt_variant", "temperature_num"]
    for keys, group in accepted.groupby(group_cols, dropna=False, sort=True):
        context_id, prompt_variant, temperature = keys
        texts = group["sampled_response_text"].tolist()
        counts = Counter(canonical_response(text, mode=normalization) for text in texts)
        sample_count = sum(counts.values())
        entropy = empirical_entropy_bits(counts)
        corrected = miller_madow_entropy_bits(entropy, unique_count=len(counts), sample_count=sample_count)
        effort = pd.DataFrame([response_effort_counts(text) for text in texts])
        top_response, top_count = counts.most_common(1)[0] if counts else ("", 0)
        first = group.iloc[0]
        rows.append(
            {
                "context_id": context_id,
                "context_text": first.get("context_text", ""),
                "context_word_count": first.get("context_word_count", ""),
                "context_length_bucket": first.get("context_length_bucket", ""),
                "prompt_variant": prompt_variant,
                "temperature": float(temperature),
                "sample_count": sample_count,
                "unique_response_count": len(counts),
                "response_entropy_mle_bits": entropy,
                "response_entropy_miller_madow_bits": corrected,
                "top_response_text": top_response,
                "top_response_count": int(top_count),
                "top_response_probability": top_count / sample_count if sample_count else math.nan,
                "mean_sample_word_count": float(effort["sample_word_count"].mean()) if not effort.empty else math.nan,
                "mean_sample_morpheme_count_surface": float(effort["sample_morpheme_count_surface"].mean()) if not effort.empty else math.nan,
                "mean_sample_syllable_count_pkg": float(effort["sample_syllable_count_pkg"].mean()) if not effort.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def rank_correlations(features: pd.DataFrame) -> pd.DataFrame:
    """Compute pairwise rank correlations across prompt-temperature settings."""

    if features.empty:
        return pd.DataFrame()
    features = features.copy()
    features["setting_label"] = features.apply(
        lambda row: f"{row['prompt_variant']}_T{float(row['temperature']):g}",
        axis=1,
    )
    pivot = features.pivot_table(
        index="context_id",
        columns="setting_label",
        values="response_entropy_miller_madow_bits",
        aggfunc="first",
    )
    setting_meta = (
        features[["setting_label", "prompt_variant", "temperature"]]
        .drop_duplicates()
        .set_index("setting_label")
        .to_dict("index")
    )
    rows: list[dict[str, object]] = []
    for left, right in combinations(sorted(pivot.columns), 2):
        left_meta = setting_meta[left]
        right_meta = setting_meta[right]
        pair = pivot[[left, right]].dropna()
        if left_meta["temperature"] == right_meta["temperature"] and left_meta["prompt_variant"] != right_meta["prompt_variant"]:
            family = "prompt_within_temperature"
        elif left_meta["prompt_variant"] == right_meta["prompt_variant"] and left_meta["temperature"] != right_meta["temperature"]:
            family = "temperature_within_prompt"
        else:
            family = "cross_prompt_temperature"
        rows.append(
            {
                "comparison_family": family,
                "setting_a": left,
                "setting_a_prompt_variant": left_meta["prompt_variant"],
                "setting_a_temperature": float(left_meta["temperature"]),
                "setting_b": right,
                "setting_b_prompt_variant": right_meta["prompt_variant"],
                "setting_b_temperature": float(right_meta["temperature"]),
                "shared_contexts": int(len(pair)),
                "spearman_r": safe_corr(pair[left], pair[right], method="spearman"),
                "pearson_r": safe_corr(pair[left], pair[right], method="pearson"),
                "mean_abs_entropy_diff_bits": float((pair[left] - pair[right]).abs().mean()) if len(pair) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def aggregate_temperature_summary(rejections: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """Summarize quality and entropy by temperature."""

    if rejections.empty:
        return pd.DataFrame()
    rej = (
        rejections.groupby("temperature", dropna=False)
        .agg(
            settings=("setting_id", "nunique"),
            attempts=("attempts", "sum"),
            accepted_samples=("accepted_samples", "sum"),
            rejected_attempts=("rejected_attempts", "sum"),
            incomplete_settings=("reached_target", lambda values: int((~values.astype(bool)).sum())),
            mean_attempts_per_accepted=("mean_attempts_per_accepted", "mean"),
        )
        .reset_index()
    )
    rej["rejection_rate"] = rej["rejected_attempts"] / rej["attempts"]
    if not features.empty:
        entropy = (
            features.groupby("temperature", dropna=False)
            .agg(
                mean_entropy_mm_bits=("response_entropy_miller_madow_bits", "mean"),
                sd_entropy_mm_bits=("response_entropy_miller_madow_bits", "std"),
                mean_unique_response_count=("unique_response_count", "mean"),
                mean_top_response_probability=("top_response_probability", "mean"),
                mean_sample_word_count=("mean_sample_word_count", "mean"),
            )
            .reset_index()
        )
        rej = rej.merge(entropy, on="temperature", how="left")
    return rej.sort_values("temperature").reset_index(drop=True)


def aggregate_prompt_summary(rejections: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """Summarize quality and entropy by prompt variant."""

    if rejections.empty:
        return pd.DataFrame()
    out = (
        rejections.groupby("prompt_variant", dropna=False)
        .agg(
            settings=("setting_id", "nunique"),
            attempts=("attempts", "sum"),
            accepted_samples=("accepted_samples", "sum"),
            rejected_attempts=("rejected_attempts", "sum"),
            incomplete_settings=("reached_target", lambda values: int((~values.astype(bool)).sum())),
            mean_attempts_per_accepted=("mean_attempts_per_accepted", "mean"),
        )
        .reset_index()
    )
    out["rejection_rate"] = out["rejected_attempts"] / out["attempts"]
    if not features.empty:
        entropy = (
            features.groupby("prompt_variant", dropna=False)
            .agg(
                mean_entropy_mm_bits=("response_entropy_miller_madow_bits", "mean"),
                sd_entropy_mm_bits=("response_entropy_miller_madow_bits", "std"),
                mean_unique_response_count=("unique_response_count", "mean"),
                mean_top_response_probability=("top_response_probability", "mean"),
                mean_sample_word_count=("mean_sample_word_count", "mean"),
            )
            .reset_index()
        )
        out = out.merge(entropy, on="prompt_variant", how="left")
    return out.sort_values("prompt_variant").reset_index(drop=True)


def select_manual_examples(attempts: pd.DataFrame, *, per_type: int = 12) -> pd.DataFrame:
    """Pick compact good/review/rejected examples for manual inspection."""

    columns = [
        "example_type",
        "review_reason",
        "context_id",
        "prompt_variant",
        "temperature",
        "attempt_index",
        "sample_index",
        "quality_flags",
        "rejection_reason",
        "context_text",
        "sampled_response_text",
        "raw_generated_text",
    ]
    rows: list[pd.DataFrame] = []
    accepted = attempts[attempts["accepted_int"] == 1].copy()
    rejected = attempts[attempts["accepted_int"] == 0].copy()
    if not accepted.empty:
        good = accepted[accepted["quality_flags"].astype(str) == ""].head(per_type).copy()
        good["example_type"] = "good"
        good["review_reason"] = ""
        rows.append(good)
        review_mask = accepted["possible_context_copy_int"].eq(1) | accepted["very_long_first_line_response_int"].eq(1)
        review = accepted[review_mask].head(per_type).copy()
        review["example_type"] = "review"
        review["review_reason"] = review["quality_flags"]
        rows.append(review)
    if not rejected.empty:
        rejected_parts = []
        for reason, group in rejected.groupby("rejection_reason", sort=True):
            picked = group.head(max(1, per_type // max(1, rejected["rejection_reason"].nunique()))).copy()
            picked["example_type"] = "rejected"
            picked["review_reason"] = reason
            rejected_parts.append(picked)
        if rejected_parts:
            rows.append(pd.concat(rejected_parts, ignore_index=True).head(per_type))
    if not rows:
        return pd.DataFrame(columns=columns)
    out = pd.concat(rows, ignore_index=True)
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return out[columns]


def plot_smoke_outputs(
    *,
    fig_dir: Path,
    temperature_summary: pd.DataFrame,
    prompt_summary: pd.DataFrame,
    quality: pd.DataFrame,
    features: pd.DataFrame,
    correlations: pd.DataFrame,
) -> pd.DataFrame:
    """Write final-smoke diagnostic figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    if not temperature_summary.empty:
        plt.figure(figsize=(8, 5))
        sns.barplot(data=temperature_summary, x="temperature", y="rejection_rate", color="#6d9dc5")
        plt.ylim(0, max(0.05, min(1.0, float(temperature_summary["rejection_rate"].max()) * 1.25 + 0.02)))
        plt.xlabel("Temperature")
        plt.ylabel("Rejected attempts / all attempts")
        plt.title("Rejection Rate By Temperature")
        plt.tight_layout()
        path = fig_dir / "final_smoke_rejection_rate_by_temperature.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Rejected-attempt rate by temperature."})

    if not features.empty:
        plt.figure(figsize=(9, 5))
        sns.boxplot(data=features, x="temperature", y="response_entropy_miller_madow_bits", hue="prompt_variant")
        plt.xlabel("Temperature")
        plt.ylabel("Accepted-response entropy (bits)")
        plt.title("Accepted Response Entropy By Temperature And Prompt")
        plt.tight_layout()
        path = fig_dir / "final_smoke_entropy_by_temperature_prompt.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Entropy distribution by temperature and prompt variant."})

    if not quality.empty:
        flag_cols = [
            "empty_first_line_response_attempt_rate",
            "no_end_of_turn_boundary_before_cap_attempt_rate",
            "repetition_loop_attempt_rate",
            "metadata_or_prose_start_attempt_rate",
            "possible_context_copy_attempt_rate",
        ]
        available = [col for col in flag_cols if col in quality.columns]
        if available:
            quality_long = quality.melt(
                id_vars=["temperature", "prompt_variant"],
                value_vars=available,
                var_name="quality_flag",
                value_name="rate",
            )
            quality_long["quality_flag"] = quality_long["quality_flag"].str.replace("_attempt_rate", "", regex=False)
            quality_agg = quality_long.groupby(["temperature", "quality_flag"], as_index=False)["rate"].mean()
            plt.figure(figsize=(10, 5))
            sns.lineplot(data=quality_agg, x="temperature", y="rate", hue="quality_flag", marker="o")
            plt.xlabel("Temperature")
            plt.ylabel("Mean attempt flag rate")
            plt.title("Quality Flags By Temperature")
            plt.tight_layout()
            path = fig_dir / "final_smoke_quality_flags_by_temperature.png"
            plt.savefig(path, dpi=180)
            plt.close()
            rows.append({"figure_id": path.stem, "path": str(path), "description": "Automatic quality flag rates by temperature."})

    prompt_corr = correlations[correlations.get("comparison_family", pd.Series(dtype=str)) == "prompt_within_temperature"].copy()
    if not prompt_corr.empty:
        matrix = prompt_corr.pivot_table(
            index="setting_a",
            columns="setting_b",
            values="spearman_r",
            aggfunc="first",
        )
        plt.figure(figsize=(max(7, 0.5 * len(matrix.columns)), max(5, 0.35 * len(matrix.index))))
        sns.heatmap(matrix, vmin=0, vmax=1, annot=True, fmt=".2f", cmap="viridis")
        plt.title("Prompt-Variant Rank Correlations")
        plt.tight_layout()
        path = fig_dir / "final_smoke_prompt_rank_correlations.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Spearman rank correlations between prompt variants."})

    return pd.DataFrame(rows)


def figure_md(figures: pd.DataFrame, figure_id: str, alt: str) -> str:
    """Return Markdown for a figure if it exists."""

    if figures.empty:
        return ""
    match = figures[figures["figure_id"] == figure_id]
    if match.empty:
        return ""
    path = Path(str(match["path"].iloc[0]))
    if not path.exists():
        return f"_Missing plot: `{path}`_"
    return f"![{alt}](../{path.as_posix()})"


def median_prompt_stability(correlations: pd.DataFrame, temperature: float) -> float:
    """Return median prompt rank-correlation at one temperature."""

    if correlations.empty:
        return math.nan
    subset = correlations[
        (correlations["comparison_family"] == "prompt_within_temperature")
        & (pd.to_numeric(correlations["setting_a_temperature"], errors="coerce") == float(temperature))
        & (pd.to_numeric(correlations["setting_b_temperature"], errors="coerce") == float(temperature))
    ]
    return float(pd.to_numeric(subset["spearman_r"], errors="coerce").median()) if not subset.empty else math.nan


def rate_for_temperature(summary: pd.DataFrame, temperature: float, column: str) -> float:
    """Read one numeric value from the temperature summary."""

    if summary.empty or column not in summary.columns:
        return math.nan
    match = summary[pd.to_numeric(summary["temperature"], errors="coerce") == float(temperature)]
    if match.empty:
        return math.nan
    return float(match[column].iloc[0])


def decision_output(temperature_summary: pd.DataFrame, correlations: pd.DataFrame) -> str:
    """Build the required decision-output section from smoke diagnostics."""

    rejection_05 = rate_for_temperature(temperature_summary, 0.5, "rejection_rate")
    rejection_07 = rate_for_temperature(temperature_summary, 0.7, "rejection_rate")
    rejection_03 = rate_for_temperature(temperature_summary, 0.3, "rejection_rate")
    rejection_10 = rate_for_temperature(temperature_summary, 1.0, "rejection_rate")
    prompt_05 = median_prompt_stability(correlations, 0.5)
    prompt_07 = median_prompt_stability(correlations, 0.7)
    prompt_all = correlations.loc[
        correlations.get("comparison_family", pd.Series(dtype=str)) == "prompt_within_temperature",
        "spearman_r",
    ]
    prompt_median = float(pd.to_numeric(prompt_all, errors="coerce").median()) if len(prompt_all) else math.nan

    justify_primary = (
        math.isfinite(rejection_05)
        and math.isfinite(rejection_07)
        and rejection_05 <= 0.10
        and rejection_07 <= 0.10
        and (not math.isfinite(prompt_median) or prompt_median >= 0.60)
    )
    t03_useful = math.isfinite(rejection_03) and rejection_03 <= 0.10
    t10_exclude = math.isfinite(rejection_10) and rejection_10 > max(0.10, rejection_07 * 1.5 if math.isfinite(rejection_07) else 0.10)
    production_rates_ok = (
        math.isfinite(rejection_05)
        and math.isfinite(rejection_07)
        and rejection_05 <= 0.10
        and rejection_07 <= 0.10
    )
    prompt_stable = not math.isfinite(prompt_median) or prompt_median >= 0.60

    def fmt(value: float) -> str:
        return "NA" if not math.isfinite(value) else f"{100 * value:.1f}%"

    incomplete_total = int(temperature_summary["incomplete_settings"].sum()) if "incomplete_settings" in temperature_summary.columns else 0

    return f"""## Decision Output

**Can we justify T=0.5 primary and T=0.7 sensitivity?**
{"Yes, as a smoke-test recommendation." if justify_primary else "Not yet as a clean recommendation from this smoke alone."}
Observed rejection rates were T=0.5 `{fmt(rejection_05)}` and T=0.7 `{fmt(rejection_07)}`;
median prompt rank stability was T=0.5 `{prompt_05:.3g}` and T=0.7 `{prompt_07:.3g}`.
The smoke did have `{incomplete_total}` incomplete context-temperature-prompt
settings, so production should keep the same attempt-cap audit and flag
pathological contexts rather than silently filling them.

**Does T=0.3 add useful conservative information?**
{"Yes: it is structurally clean enough to keep as a conservative diagnostic." if t03_useful else "Not clearly: inspect its entropy spread and examples before keeping it."}
Its rejection rate was `{fmt(rejection_03)}`.

**Should T=1.0 be excluded or kept as an optional diagnostic?**
{"Exclude from production unless supervisors explicitly ask for it; keep only as an optional diagnostic." if t10_exclude else "Keep as an optional diagnostic only, not as the primary production setting."}
Its rejection rate was `{fmt(rejection_10)}`.

**Are rejection rates low enough for production?**
{"Yes for the proposed T=0.5/T=0.7 production pair, assuming supervisor approval of the rejection policy." if production_rates_ok else "No or not yet; production should wait for lower rejection rates or a revised quality policy."}

**Are prompt-variant rankings stable enough?**
{"Yes at smoke-test resolution." if prompt_stable else "Not yet; prompt wording changes the context ranking enough to require supervisor discussion."}
Median prompt-within-temperature Spearman correlation across the smoke was `{prompt_median:.3g}`.

**What exact questions should be asked of supervisors?**

1. Is the transcript prompt wrapper acceptable: `Caregiver/Parent/Adult: {{context}}` followed by `Child:`?
2. Should response entropy be estimated over accepted valid child-turn samples only, with rejected attempts reported?
3. Should possible context-copy responses be kept as flagged valid samples, or excluded?
4. Is T=0.5 primary plus T=0.7 sensitivity sufficient for production?
5. Should T=0.3 remain as a conservative diagnostic, and should T=1.0 be excluded unless requested?
"""


def short_text(value: object, limit: int = 120) -> str:
    """Shorten text for report tables."""

    text = SPACES_RE.sub(" ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "..."


def build_report_markdown(
    *,
    output_dir: Path,
    figures: pd.DataFrame,
    manifest_audit: pd.DataFrame,
    temperature_summary: pd.DataFrame,
    prompt_summary: pd.DataFrame,
    rejections: pd.DataFrame,
    quality: pd.DataFrame,
    correlations: pd.DataFrame,
    examples: pd.DataFrame,
) -> str:
    """Build the final smoke Markdown report."""

    prompt_corr = correlations[correlations.get("comparison_family", pd.Series(dtype=str)) == "prompt_within_temperature"].copy()
    temp_corr = correlations[correlations.get("comparison_family", pd.Series(dtype=str)) == "temperature_within_prompt"].copy()
    quality_cols = [
        "setting_id",
        "empty_first_line_response_attempt_rate",
        "no_end_of_turn_boundary_before_cap_attempt_rate",
        "repetition_loop_attempt_rate",
        "metadata_or_prose_start_attempt_rate",
        "possible_context_copy_attempt_rate",
        "very_long_first_line_response_attempt_rate",
    ]
    quality_small = quality[[col for col in quality_cols if col in quality.columns]].head(20) if not quality.empty else quality
    incomplete = rejections[~rejections["reached_target"].astype(bool)].copy() if not rejections.empty else pd.DataFrame()
    incomplete_brief = incomplete[
        [
            "context_id",
            "prompt_variant",
            "temperature",
            "attempts",
            "accepted_samples",
            "rejected_attempts",
            "rejection_rate",
            "repetition_loop_count",
            "no_boundary_before_cap_count",
            "other_quality_flag_count",
        ]
    ] if not incomplete.empty else incomplete
    example_cols = [
        "example_type",
        "review_reason",
        "prompt_variant",
        "temperature",
        "quality_flags",
        "rejection_reason",
        "context_text",
        "sampled_response_text",
    ]
    examples_report = examples.copy()
    for col in ["context_text", "sampled_response_text"]:
        if col in examples_report.columns:
            examples_report[col] = examples_report[col].map(short_text)
    examples_report = examples_report[[col for col in example_cols if col in examples_report.columns]]

    return f"""# Route 2 Final Generation Smoke

Created: 2026-06-16

This is the final pre-Slurm response-generation smoke. It is generation and
sampling only, not entropy scoring. The downstream entropy feature script
should consume the accepted samples after this smoke is approved.

## Method And Prompt Definition

For each caregiver context, the sampler repeatedly prompts base Mistral with a
transcript-style wrapper and keeps one generated child conversational turn.
The smoke tests three wrappers:

```text
Caregiver: {{context}}
Child:

Parent: {{context}}
Child:

Adult: {{context}}
Child:
```

Generation uses true end-of-turn stopping during decoding. Decoding stops as
soon as the generated suffix contains one of:

```text
\\n
\\nCaregiver:
\\nParent:
\\nAdult:
\\nChild:
\\nCHI:
```

`max_new_tokens=96` is only a safety cap. Attempts are accepted only if the
first generated child-turn response passes deterministic structural checks.
Possible context copies are kept as accepted review-flagged samples, not
silently removed.

Manifest audit:

{markdown_table(manifest_audit, max_rows=20)}

## Temperature Results

{markdown_table(temperature_summary, max_rows=20)}

{figure_md(figures, "final_smoke_rejection_rate_by_temperature", "rejection rate by temperature")}

{figure_md(figures, "final_smoke_entropy_by_temperature_prompt", "entropy by temperature and prompt")}

## Prompt Robustness Results

Prompt-variant rank correlations compare context-level accepted-response
entropy estimates across `Caregiver`, `Parent`, and `Adult` wrappers at the
same temperature.

{markdown_table(prompt_corr, max_rows=40)}

Temperature rank correlations compare entropy rankings across temperatures
within the same prompt wrapper.

{markdown_table(temp_corr, max_rows=40)}

{figure_md(figures, "final_smoke_prompt_rank_correlations", "prompt rank correlations")}

Prompt summary:

{markdown_table(prompt_summary, max_rows=20)}

## Rejection Rates

The table below is one row per context-temperature-prompt setting.

{markdown_table(rejections, max_rows=40)}

Incomplete settings that hit the attempt cap before reaching 20 accepted
responses:

{markdown_table(incomplete_brief, max_rows=20)}

## Quality Flag Rates

Quality flags are deterministic. The attempt-rate columns summarize all
attempts; accepted-rate columns in the CSV summarize accepted samples only.

{markdown_table(quality_small, max_rows=40)}

{figure_md(figures, "final_smoke_quality_flags_by_temperature", "quality flags by temperature")}

## Examples: Good / Review / Rejected

{markdown_table(examples_report, max_rows=60)}

## Recommendation For Supervisor Meeting

Use this smoke to ask supervisors to approve the operational definition before
Mila-scale production: response entropy over valid one-turn child-response
samples, with rejected attempts retained as diagnostics. The strongest
production candidate remains T=0.5 as primary and T=0.7 as sensitivity if their
rejection rates and prompt rankings remain stable in the tables above.

## Remaining Risks Before Slurm

- Accepted-only entropy conditions on the quality filter; this is defensible
  only because rejection rates are explicitly reported.
- Prompt wrappers can change the measurement object, so prompt-rank stability
  should be reviewed before choosing one production wrapper.
- M=20 is a smoke size. Production still needs a larger accepted sample count
  and a Slurm completion audit.
- Context-copy responses may be valid child-like repetitions or model copying;
  supervisors should decide whether flagged copies remain in production entropy.

## Files

- Accepted samples: `{output_dir / "accepted_samples.csv.gz"}`
- All attempts: `{output_dir / "all_attempts.csv.gz"}`
- Rejection summary: `{output_dir / "rejection_summary_by_setting.csv"}`
- Quality flags: `{output_dir / "quality_flags_by_setting.csv"}`
- Prompt/temperature rank correlations: `{output_dir / "prompt_temperature_rank_correlations.csv"}`
- Manual review examples: `{output_dir / "manual_review_examples.csv"}`
- Smoke manifest: `{output_dir / "smoke_manifest.csv"}`
- Smoke manifest audit: `{output_dir / "smoke_manifest_audit.csv"}`

{decision_output(temperature_summary, correlations)}
"""


def summarize_final_smoke(
    *,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    normalization: str = "casefold",
) -> dict[str, Path]:
    """Build required summary tables and the final report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    attempts, accepted = read_smoke_outputs(output_dir)
    rejections = summarize_rejections(attempts)
    quality = summarize_quality_flags(attempts)
    features = accepted_entropy_features(accepted, normalization=normalization)
    correlations = rank_correlations(features)
    temperature_summary = aggregate_temperature_summary(rejections, features)
    prompt_summary = aggregate_prompt_summary(rejections, features)
    examples = select_manual_examples(attempts)
    figures = plot_smoke_outputs(
        fig_dir=fig_dir,
        temperature_summary=temperature_summary,
        prompt_summary=prompt_summary,
        quality=quality,
        features=features,
        correlations=correlations,
    )
    audit_path = output_path(output_dir, "smoke_manifest_audit.csv")
    manifest_audit = pd.read_csv(audit_path) if audit_path.exists() else pd.DataFrame()

    paths = {
        "rejections": output_path(output_dir, "rejection_summary_by_setting.csv"),
        "quality": output_path(output_dir, "quality_flags_by_setting.csv"),
        "features": output_path(output_dir, "accepted_entropy_by_context_setting.csv"),
        "correlations": output_path(output_dir, "prompt_temperature_rank_correlations.csv"),
        "temperature_summary": output_path(output_dir, "temperature_summary.csv"),
        "prompt_summary": output_path(output_dir, "prompt_variant_summary.csv"),
        "examples": output_path(output_dir, "manual_review_examples.csv"),
        "figures": output_path(output_dir, "figure_manifest.csv"),
        "report_md": report_md,
        "report_html": report_html,
    }
    rejections.to_csv(paths["rejections"], index=False)
    quality.to_csv(paths["quality"], index=False)
    features.to_csv(paths["features"], index=False)
    correlations.to_csv(paths["correlations"], index=False)
    temperature_summary.to_csv(paths["temperature_summary"], index=False)
    prompt_summary.to_csv(paths["prompt_summary"], index=False)
    examples.to_csv(paths["examples"], index=False)
    figures.to_csv(paths["figures"], index=False)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    markdown = build_report_markdown(
        output_dir=output_dir,
        figures=figures,
        manifest_audit=manifest_audit,
        temperature_summary=temperature_summary,
        prompt_summary=prompt_summary,
        rejections=rejections,
        quality=quality,
        correlations=correlations,
        examples=examples,
    )
    report_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(report_md, report_html)
    return paths


def build_cli() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["manifest", "generate", "summarize", "all"], default="all")
    parser.add_argument("--input-manifest", type=Path, default=DEFAULT_INPUT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--contexts-per-bucket", type=int, default=10)
    parser.add_argument("--temperatures", default=",".join(str(value) for value in DEFAULT_TEMPERATURES))
    parser.add_argument("--accepted-samples-per-setting", type=int, default=20)
    parser.add_argument("--max-attempts-per-setting", type=int, default=60)
    parser.add_argument("--batch-attempts", type=int, default=16)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="auto")
    parser.add_argument("--model-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--normalization", choices=["exact", "casefold"], default="casefold")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Run the requested smoke stage."""

    parser = build_cli()
    args = parser.parse_args(argv)
    temperatures = parse_float_csv(args.temperatures)
    paths: dict[str, Path] = {}
    if args.stage in {"manifest", "all"}:
        paths.update(
            build_smoke_manifest(
                input_manifest=args.input_manifest,
                output_dir=args.output_dir,
                contexts_per_bucket=args.contexts_per_bucket,
                prompt_variants=DEFAULT_PROMPT_VARIANTS,
                temperatures=temperatures,
                accepted_samples_per_setting=args.accepted_samples_per_setting,
                max_attempts_per_setting=args.max_attempts_per_setting,
                max_new_tokens=args.max_new_tokens,
                seed=args.seed,
                model_name=args.model,
            )
        )
    if args.stage in {"generate", "all"}:
        manifest_csv = args.output_dir / "smoke_manifest.csv"
        paths.update(
            sample_final_smoke(
                output_dir=args.output_dir,
                manifest_csv=manifest_csv,
                model_name=args.model,
                temperatures=temperatures,
                accepted_samples_per_setting=args.accepted_samples_per_setting,
                max_attempts_per_setting=args.max_attempts_per_setting,
                batch_attempts=args.batch_attempts,
                max_new_tokens=args.max_new_tokens,
                top_p=args.top_p,
                top_k=args.top_k,
                device=args.device,
                dtype=args.dtype,
                model_dir=args.model_dir,
                seed=args.seed,
            )
        )
    if args.stage in {"summarize", "all"}:
        paths.update(
            summarize_final_smoke(
                output_dir=args.output_dir,
                fig_dir=args.fig_dir,
                report_md=args.report_md,
                report_html=args.report_html,
                normalization=args.normalization,
            )
        )
    for key, path in paths.items():
        print(f"[OK] {key}: {path}")


if __name__ == "__main__":
    main()
