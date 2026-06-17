#!/usr/bin/env python3
"""Sample full model responses for context-level empirical entropy.

This script is GPU-ready but intentionally not run automatically on the
laptop. It reads the manifest from ``build_response_entropy_manifest.py`` and
writes one row per sampled response.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import time
from pathlib import Path
from typing import Sequence

import pandas as pd
import torch


DEFAULT_MANIFEST = Path("results/response_level_context_entropy/context_response_sampling_manifest.csv")
DEFAULT_OUTPUT = Path("results/response_level_context_entropy/context_response_samples.csv.gz")
DEFAULT_PROMPT_TEMPLATE = "Caregiver: {context}\nChild:"
DEFAULT_STOP_STRINGS = ["\nCaregiver:", "\nParent:", "\nAdult:", "\nChild:", "\nCHI:", "\n"]
OUTPUT_COLUMNS = [
    "context_id",
    "manifest_row",
    "context_text",
    "prompt_text",
    "temperature",
    "sample_index",
    "raw_generated_text",
    "sampled_response_text",
    "generated_token_count",
    "hit_max_new_tokens",
    "stopped_by_speaker_boundary",
    "speaker_boundary_marker",
    "empty_response",
    "model_used",
    "max_new_tokens",
    "top_p",
    "top_k",
    "seed_used",
]


def parse_float_csv(value: str) -> list[float]:
    """Parse comma-separated float values."""

    return [float(part.strip()) for part in value.split(",") if part.strip()]


def format_prompt(context: str, template: str) -> str:
    """Insert one context into the audited prompt template."""

    return template.replace("{context}", str(context))


def clean_generated_response(text: str) -> str:
    """Trim common response boundaries from decoded sampled text."""

    value = str(text).strip()
    for marker in DEFAULT_STOP_STRINGS:
        if marker in value:
            value = value.split(marker, 1)[0].strip()
    return value


def clean_generated_response_with_audit(text: str, *, stop_strings: Sequence[str] = DEFAULT_STOP_STRINGS) -> tuple[str, bool, str]:
    """Trim response text and report whether a speaker boundary was found."""

    raw = str(text)
    first_marker = ""
    first_position: int | None = None
    for marker in stop_strings:
        position = raw.find(marker)
        if position >= 0 and (first_position is None or position < first_position):
            first_position = position
            first_marker = marker
    if first_position is None:
        return raw.strip(), False, ""
    marker_label = "\\n" if first_marker == "\n" else first_marker.strip()
    return raw[:first_position].strip(), True, marker_label


def model_input_device(model) -> torch.device:
    """Return the device that should receive tokenizer inputs."""

    try:
        return next(model.parameters()).device
    except StopIteration:  # pragma: no cover - defensive for unusual wrappers
        return torch.device("cpu")


def generated_token_ids(output_ids, *, prompt_token_width: int):
    """Return only generated token ids after the padded prompt width."""

    return output_ids[int(prompt_token_width) :]


def resolve_model_source(model_name: str, model_dir: Path | None) -> tuple[str, str | None]:
    """Return the Hugging Face source and optional cache directory.

    ``model_dir`` can either be a direct local model snapshot containing
    ``config.json`` or a cache directory. If omitted, Transformers uses the
    user's shared Hugging Face cache, avoiding project-local duplicate weights.
    """

    if model_dir is None:
        return model_name, None
    if (model_dir / "config.json").exists():
        return str(model_dir), None
    return model_name, str(model_dir)


def load_transformers_model(model_name: str, *, device: str, dtype: str, model_dir: Path | None):
    """Load a causal LM and tokenizer lazily so importing this script is cheap."""

    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch_dtype = "auto"
    if dtype == "float16":
        torch_dtype = torch.float16
    elif dtype == "bfloat16":
        torch_dtype = torch.bfloat16
    elif dtype == "float32":
        torch_dtype = torch.float32

    model_source, cache_dir = resolve_model_source(model_name, model_dir)
    tokenizer = AutoTokenizer.from_pretrained(model_source, cache_dir=cache_dir)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        model_source,
        cache_dir=cache_dir,
        torch_dtype=torch_dtype,
        device_map=device if device == "auto" else None,
    )
    if device != "auto":
        model.to(torch.device(device))
    model.eval()
    return tokenizer, model


@torch.no_grad()
def sample_for_contexts(
    batch: pd.DataFrame,
    *,
    tokenizer,
    model,
    prompt_template: str,
    temperature: float,
    samples_per_context: int,
    batch_samples: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    seed: int,
    model_name: str,
) -> list[dict[str, object]]:
    """Sample repeated responses for a batch of contexts."""

    prompts = [format_prompt(text, prompt_template) for text in batch["context_text"].astype(str).tolist()]
    repeated_prompts = [prompt for prompt in prompts for _ in range(samples_per_context)]
    repeated_rows = [row for _, row in batch.iterrows() for _ in range(samples_per_context)]
    sample_indices = [idx for _ in prompts for idx in range(samples_per_context)]

    rows: list[dict[str, object]] = []
    input_device = model_input_device(model)
    for offset in range(0, len(repeated_prompts), batch_samples):
        prompt_batch = repeated_prompts[offset : offset + batch_samples]
        row_batch = repeated_rows[offset : offset + batch_samples]
        sample_index_batch = sample_indices[offset : offset + batch_samples]
        torch.manual_seed(seed + offset)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed + offset)
        encoded = tokenizer(prompt_batch, return_tensors="pt", padding=True).to(input_device)
        prompt_token_width = int(encoded["input_ids"].shape[1])
        outputs = model.generate(
            **encoded,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_new_tokens=max_new_tokens,
            num_return_sequences=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            renormalize_logits=True,
        )
        for output_ids, source_row, sample_index, prompt in zip(outputs, row_batch, sample_index_batch, prompt_batch):
            generated_ids = generated_token_ids(output_ids, prompt_token_width=prompt_token_width)
            raw_generated = tokenizer.decode(generated_ids, skip_special_tokens=True)
            response, stopped_by_boundary, stop_marker = clean_generated_response_with_audit(raw_generated)
            rows.append(
                {
                    "context_id": source_row["context_id"],
                    "manifest_row": source_row.get("manifest_row", ""),
                    "context_text": source_row["context_text"],
                    "prompt_text": prompt,
                    "temperature": temperature,
                    "sample_index": sample_index,
                    "raw_generated_text": raw_generated,
                    "sampled_response_text": response,
                    "generated_token_count": int(len(generated_ids)),
                    "hit_max_new_tokens": int(len(generated_ids) >= max_new_tokens),
                    "stopped_by_speaker_boundary": int(stopped_by_boundary),
                    "speaker_boundary_marker": stop_marker,
                    "empty_response": int(response.strip() == ""),
                    "model_used": model_name,
                    "max_new_tokens": max_new_tokens,
                    "top_p": top_p,
                    "top_k": top_k,
                    "seed_used": seed + offset,
                }
            )
    return rows


def completed_context_temperatures(output_csv: Path, samples_per_context: int) -> set[tuple[str, float]]:
    """Return context/temperature pairs already fully written to output."""

    if not output_csv.exists():
        return set()
    sample_indices: dict[tuple[str, float], set[int]] = {}
    try:
        reader = pd.read_csv(
            output_csv,
            usecols=["context_id", "temperature", "sample_index"],
            chunksize=100_000,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="skip",
        )
        for chunk in reader:
            chunk["temperature_numeric"] = pd.to_numeric(chunk["temperature"], errors="coerce")
            chunk["sample_index_numeric"] = pd.to_numeric(chunk["sample_index"], errors="coerce")
            chunk = chunk.dropna(subset=["temperature_numeric", "sample_index_numeric"])
            for (context_id, temperature), group in chunk.groupby(["context_id", "temperature_numeric"], dropna=False):
                if pd.isna(temperature) or context_id == "":
                    continue
                key = (str(context_id), float(temperature))
                sample_indices.setdefault(key, set()).update(group["sample_index_numeric"].astype(int).tolist())
    except (EOFError, gzip.BadGzipFile, pd.errors.EmptyDataError):
        return set()
    return {key for key, indices in sample_indices.items() if len(indices) >= samples_per_context}


def append_rows(output_csv: Path, rows: list[dict[str, object]]) -> int:
    """Append sampled rows immediately so long GPU runs are resumable."""

    if not rows:
        return 0
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    for column in OUTPUT_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[OUTPUT_COLUMNS]
    write_header = not output_csv.exists() or output_csv.stat().st_size == 0
    if output_csv.suffix == ".gz":
        with gzip.open(output_csv, "at", newline="") as handle:
            frame.to_csv(handle, index=False, header=write_header, quoting=csv.QUOTE_ALL, lineterminator="\n")
    else:
        frame.to_csv(output_csv, index=False, mode="a", header=write_header, quoting=csv.QUOTE_ALL, lineterminator="\n")
    return len(frame)


def sample_responses(
    *,
    manifest_csv: Path,
    output_csv: Path,
    model_name: str,
    temperatures: Sequence[float],
    samples_per_context: int,
    batch_contexts: int,
    batch_samples: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    prompt_template: str,
    device: str,
    dtype: str,
    model_dir: Path | None,
    max_contexts: int | None,
    seed: int,
    resume: bool,
) -> pd.DataFrame:
    """Sample responses and write a long response-sample CSV."""

    manifest = pd.read_csv(manifest_csv, dtype=str, keep_default_na=False)
    if max_contexts is not None:
        manifest = manifest.head(max_contexts).copy()
    required = {"context_id", "context_text"}
    missing = required - set(manifest.columns)
    if missing:
        raise KeyError(f"{manifest_csv} missing required columns: {sorted(missing)}")
    if batch_samples < 1:
        raise ValueError("--batch-samples must be >= 1")

    tokenizer, model = load_transformers_model(model_name, device=device, dtype=dtype, model_dir=model_dir)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    completed = completed_context_temperatures(output_csv, samples_per_context) if resume else set()
    if completed:
        print(f"[INFO] resuming with {len(completed):,} completed context-temperature pairs")
    start_time = time.time()
    written_rows = 0
    for temperature in temperatures:
        for start in range(0, len(manifest), batch_contexts):
            batch = manifest.iloc[start : start + batch_contexts].copy()
            batch = batch[
                ~batch["context_id"].astype(str).map(lambda context_id: (context_id, float(temperature)) in completed)
            ].copy()
            if batch.empty:
                done = min(start + batch_contexts, len(manifest))
                print(f"[INFO] temp={temperature} contexts={done:,}/{len(manifest):,} already_done")
                continue
            rows = sample_for_contexts(
                batch,
                tokenizer=tokenizer,
                model=model,
                prompt_template=prompt_template,
                temperature=float(temperature),
                samples_per_context=samples_per_context,
                batch_samples=batch_samples,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                top_k=top_k,
                seed=seed + int(round(float(temperature) * 1000)) + start,
                model_name=model_name,
            )
            written_rows += append_rows(output_csv, rows)
            done = min(start + batch_contexts, len(manifest))
            print(f"[INFO] temp={temperature} contexts={done:,}/{len(manifest):,} rows_written={written_rows:,}")
    print(f"[BENCH] elapsed_seconds={time.time() - start_time:.1f}")
    print(f"[OK] wrote/appended {written_rows:,} new samples to {output_csv}")
    if output_csv.exists():
        return pd.read_csv(output_csv)
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperatures", default="0.7,1.0,1.3")
    parser.add_argument("--samples-per-context", type=int, default=100)
    parser.add_argument("--batch-contexts", type=int, default=2)
    parser.add_argument("--batch-samples", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=24)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="auto")
    parser.add_argument("--model-dir", type=Path, default=None)
    parser.add_argument("--max-contexts", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260605)
    parser.add_argument("--no-resume", action="store_true", help="Ignore existing output rows and append a fresh run.")
    args = parser.parse_args(argv)
    sample_responses(
        manifest_csv=args.manifest,
        output_csv=args.output,
        model_name=args.model,
        temperatures=parse_float_csv(args.temperatures),
        samples_per_context=args.samples_per_context,
        batch_contexts=args.batch_contexts,
        batch_samples=args.batch_samples,
        max_new_tokens=args.max_new_tokens,
        top_p=args.top_p,
        top_k=args.top_k,
        prompt_template=args.prompt_template,
        device=args.device,
        dtype=args.dtype,
        model_dir=args.model_dir,
        max_contexts=args.max_contexts,
        seed=args.seed,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
