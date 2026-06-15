#!/usr/bin/env python3
"""Sample full model responses for context-level empirical entropy.

This script is GPU-ready but intentionally not run automatically on the
laptop. It reads the manifest from ``build_response_entropy_manifest.py`` and
writes one row per sampled response.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Sequence

import pandas as pd
import torch


DEFAULT_MANIFEST = Path("results/response_level_context_entropy/context_response_sampling_manifest.csv")
DEFAULT_OUTPUT = Path("results/response_level_context_entropy/context_response_samples.csv.gz")
DEFAULT_PROMPT_TEMPLATE = "Caregiver: {context}\nChild:"
DEFAULT_STOP_STRINGS = ["\nCaregiver:", "\nParent:", "\nAdult:", "\nChild:", "\nCHI:"]


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
    return raw[:first_position].strip(), True, first_marker.strip()


def model_input_device(model) -> torch.device:
    """Return the device that should receive tokenizer inputs."""

    try:
        return next(model.parameters()).device
    except StopIteration:  # pragma: no cover - defensive for unusual wrappers
        return torch.device("cpu")


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

    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(model_dir) if model_dir else None)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=str(model_dir) if model_dir else None,
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

    input_device = model_input_device(model)
    generator = torch.Generator(device=input_device)
    generator.manual_seed(seed)
    encoded = tokenizer(repeated_prompts, return_tensors="pt", padding=True).to(input_device)
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
        generator=generator,
    )
    input_lengths = encoded["attention_mask"].sum(dim=1).detach().cpu().tolist()
    rows: list[dict[str, object]] = []
    for output_ids, input_len, source_row, sample_index, prompt in zip(outputs, input_lengths, repeated_rows, sample_indices, repeated_prompts):
        generated_ids = output_ids[int(input_len) :]
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
                "seed_used": seed,
            }
        )
    return rows


def sample_responses(
    *,
    manifest_csv: Path,
    output_csv: Path,
    model_name: str,
    temperatures: Sequence[float],
    samples_per_context: int,
    batch_contexts: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    prompt_template: str,
    device: str,
    dtype: str,
    model_dir: Path | None,
    max_contexts: int | None,
    seed: int,
) -> pd.DataFrame:
    """Sample responses and write a long response-sample CSV."""

    manifest = pd.read_csv(manifest_csv, dtype=str, keep_default_na=False)
    if max_contexts is not None:
        manifest = manifest.head(max_contexts).copy()
    required = {"context_id", "context_text"}
    missing = required - set(manifest.columns)
    if missing:
        raise KeyError(f"{manifest_csv} missing required columns: {sorted(missing)}")

    tokenizer, model = load_transformers_model(model_name, device=device, dtype=dtype, model_dir=model_dir)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    all_rows: list[pd.DataFrame] = []
    start_time = time.time()
    for temperature in temperatures:
        for start in range(0, len(manifest), batch_contexts):
            batch = manifest.iloc[start : start + batch_contexts].copy()
            rows = sample_for_contexts(
                batch,
                tokenizer=tokenizer,
                model=model,
                prompt_template=prompt_template,
                temperature=float(temperature),
                samples_per_context=samples_per_context,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                top_k=top_k,
                seed=seed + int(round(float(temperature) * 1000)) + start,
                model_name=model_name,
            )
            all_rows.append(pd.DataFrame(rows))
            done = min(start + batch_contexts, len(manifest))
            print(f"[INFO] temp={temperature} contexts={done:,}/{len(manifest):,}")
    out = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    out.to_csv(output_csv, index=False)
    print(f"[BENCH] elapsed_seconds={time.time() - start_time:.1f}")
    print(f"[OK] wrote {len(out):,} samples to {output_csv}")
    return out


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperatures", default="0.7,1.0,1.3")
    parser.add_argument("--samples-per-context", type=int, default=100)
    parser.add_argument("--batch-contexts", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=24)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="auto")
    parser.add_argument("--model-dir", type=Path, default=Path("results/response_level_context_entropy/model_cache"))
    parser.add_argument("--max-contexts", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260605)
    args = parser.parse_args(argv)
    sample_responses(
        manifest_csv=args.manifest,
        output_csv=args.output,
        model_name=args.model,
        temperatures=parse_float_csv(args.temperatures),
        samples_per_context=args.samples_per_context,
        batch_contexts=args.batch_contexts,
        max_new_tokens=args.max_new_tokens,
        top_p=args.top_p,
        top_k=args.top_k,
        prompt_template=args.prompt_template,
        device=args.device,
        dtype=args.dtype,
        model_dir=args.model_dir,
        max_contexts=args.max_contexts,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
