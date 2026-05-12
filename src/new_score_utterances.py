#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_parallel_surprisal.py
==========================

RAW SCORING ONLY for your *parallel_dataset* shards (no extra metrics).

This script is meant to be called by SLURM jobs where *all arguments are explicit*.
It scores ONE input CSV shard at a time and writes ONE output CSV.

NEW (2026-01-24):
-----------------
1) Multi-column scoring:
   Score multiple utterance columns in ONE pass (same LM + optional context).
   Example columns:
     - utterance_clean
     - random_model_utterance_bin6
     - unigram_model_utterance_bin6
     - bigram_model_utterance_bin6

   Output columns are suffixed per text column:
     mean_bits_per_token__utterance_clean
     sum_bits__utterance_clean
     n_eval_tokens__utterance_clean
     ...

2) Skip zero-count rows:
   By default, rows with word_count==0 OR morph_count==0 are NOT scored
   (they get NaN mean/sum and 0 eval tokens), to avoid wasting compute.

Key bugfix (2026-01):
--------------------
When scoring with context, some tokenizers produce a first target token whose
offset span starts BEFORE the utterance start (because it includes the leading
separator space, e.g. " world"). The previous boundary condition:

    token_start >= target_start

would exclude that token, causing 1-word utterances to have 0 eval tokens.

We now include tokens by OVERLAP with the target region:

    token_end > target_start

and clamp local offsets to >= 0 when storing token offsets.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ────────────────────────────────────────────────────────────────
# JSON safety (so lists/torch scalars serialize cleanly)
# ────────────────────────────────────────────────────────────────

_OriginalJSONEncoder = json.JSONEncoder


class _SafeJSONEncoder(_OriginalJSONEncoder):
    def default(self, obj):
        try:
            return _OriginalJSONEncoder.default(self, obj)
        except TypeError:
            return str(obj)


json.JSONEncoder = _SafeJSONEncoder


# ────────────────────────────────────────────────────────────────
# Optional re-cleaning (OFF by default)
# ────────────────────────────────────────────────────────────────

_TIMECODE_RE = re.compile(r"\x15\s*\d+(?:[_:]\d+)?\s*\x15")
_BRACKETS_RE = re.compile(r"\[[^\]]*]")
_PARENS_RE = re.compile(r"\([^)]*\)")
_ANGLE_RE = re.compile(r"<[^>]*>")
_UNTRANS_RE = re.compile(r"\b(?:xxx|yyy|www)\b", re.IGNORECASE)
_PLUS_MARKER_RE = re.compile(r"(?:(?<=\s)|^)\+(?:[/.\-]+|\S+)")
_AT_MARKER_RE = re.compile(r"(?:(?<=\s)|^)@[^\s]+")
_AMP_MARKER_RE = re.compile(r"(?:(?<=\s)|^)&[^\s]+")
_ZERO_MARKER_RE = re.compile(r"(?:(?<=\s)|^)0[^\s]*")
_SPACES_RE = re.compile(r"\s+")


def clean_for_lm(text: str) -> str:
    s = "" if text is None else str(text)
    s = _TIMECODE_RE.sub(" ", s)
    s = _BRACKETS_RE.sub(" ", s)
    s = _PARENS_RE.sub(" ", s)
    s = _ANGLE_RE.sub(" ", s)
    s = _UNTRANS_RE.sub(" ", s)
    s = _AT_MARKER_RE.sub(" ", s)
    s = _PLUS_MARKER_RE.sub(" ", s)
    s = _AMP_MARKER_RE.sub(" ", s)
    s = _ZERO_MARKER_RE.sub(" ", s)
    s = _SPACES_RE.sub(" ", s).strip()
    return s


def norm_ws(text: str) -> str:
    return _SPACES_RE.sub(" ", ("" if text is None else str(text))).strip()


# ────────────────────────────────────────────────────────────────
# Device + dtype selection
# ────────────────────────────────────────────────────────────────

def pick_device(device_opt: str) -> torch.device:
    device_opt = (device_opt or "auto").lower()
    if device_opt == "cpu":
        return torch.device("cpu")
    if device_opt == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested --device cuda but CUDA is not available.")
        return torch.device("cuda")
    if device_opt == "mps":
        if not (getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()):
            raise RuntimeError("Requested --device mps but MPS is not available.")
        return torch.device("mps")

    # auto
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def pick_dtype(dtype_opt: str, device: torch.device) -> torch.dtype:
    d = (dtype_opt or "auto").lower()
    if d == "fp32":
        return torch.float32
    if d == "fp16":
        return torch.float16
    if d == "bf16":
        return torch.bfloat16

    # auto
    if device.type == "cuda":
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    if device.type == "mps":
        return torch.float16
    return torch.float32


def load_model_and_tokenizer(model_name: str, device: torch.device, dtype: torch.dtype):
    tok = AutoTokenizer.from_pretrained(model_name, use_fast=True, trust_remote_code=True)

    added_pad = False
    if tok.pad_token_id is None:
        if tok.eos_token_id is not None:
            tok.pad_token = tok.eos_token
        else:
            tok.add_special_tokens({"pad_token": "[PAD]"})
            added_pad = True

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=dtype,
        trust_remote_code=True,
    )

    if added_pad:
        model.resize_token_embeddings(len(tok))

    if getattr(model.config, "pad_token_id", None) is None:
        model.config.pad_token_id = tok.pad_token_id
    if getattr(model.config, "return_dict", None) is not True:
        model.config.return_dict = True

    model = model.to(device=device)
    model.eval()

    n_params = sum(p.numel() for p in model.parameters())
    if device.type == "cuda":
        idx = device.index if device.index is not None else torch.cuda.current_device()
        total_gb = torch.cuda.get_device_properties(idx).total_memory / (1024**3)
        print(f"[INFO] Loaded {model_name} on {device} (dtype={dtype}, params={n_params:,}, VRAM≈{total_gb:.1f} GB)")
    else:
        print(f"[INFO] Loaded {model_name} on {device} (dtype={dtype}, params={n_params:,})")

    return tok, model


# ────────────────────────────────────────────────────────────────
# Core surprisal computation (target-span scoring)
# ────────────────────────────────────────────────────────────────

def _get_offsets_for_item(offset_mapping_item) -> List[Tuple[int, int]]:
    """
    offset_mapping_item can be:
      - a torch.Tensor of shape [T, 2]
      - or a list of (s,e)
    Return as a python list of (s,e) ints.
    """
    if offset_mapping_item is None:
        return []
    if hasattr(offset_mapping_item, "tolist"):
        return [(int(s), int(e)) for (s, e) in offset_mapping_item.tolist()]
    return [(int(s), int(e)) for (s, e) in offset_mapping_item]


@torch.no_grad()
def batch_target_surprisal(
    texts: List[str],
    target_starts: List[int],
    tokenizer,
    model,
    device: torch.device,
    units: str = "bits",
    max_length: Optional[int] = None,
    store_token_level: bool = False,
) -> List[Dict[str, Any]]:
    """
    Returns list of dicts per input:
      mean_units_per_token, n_valid_tokens, sum_units
      optionally token_units_per_target, token_offsets_per_target
    """
    if not texts:
        return []

    if len(target_starts) != len(texts):
        raise ValueError("len(target_starts) must match len(texts)")

    encoded = tokenizer(
        texts,
        return_tensors="pt",
        return_offsets_mapping=True,
        add_special_tokens=True,
        padding=True,
        truncation=(max_length is not None),
        max_length=max_length,
    )

    input_ids = encoded["input_ids"].to(device)
    attn = encoded["attention_mask"].to(device)
    offsets = encoded["offset_mapping"]  # CPU tensor or list-like

    out = model(input_ids, attention_mask=attn)
    logits = out.logits  # [B, T, V]

    logp = torch.log_softmax(logits, dim=-1)
    gold = input_ids[:, 1:]
    tok_logp = torch.gather(logp[:, :-1, :], 2, gold.unsqueeze(-1)).squeeze(-1)
    nll = -tok_logp  # nats
    ln2 = math.log(2.0)

    results: List[Dict[str, Any]] = []
    B = input_ids.size(0)

    for b in range(B):
        tgt_start = int(target_starts[b])

        # gold positions correspond to tokens 1..T-1 (predict token t from token t-1)
        am = attn[b, 1:].bool().cpu()  # [T-1] on CPU

        offsets_b_all = offsets[b]
        offsets_list_all = _get_offsets_for_item(offsets_b_all)  # len T
        offsets_gold = offsets_list_all[1:1 + am.size(0)]         # len T-1

        # include tokens by overlap with target region
        within: List[bool] = []
        for (s, e) in offsets_gold:
            if e <= s:
                within.append(False)
            else:
                within.append(e > tgt_start)

        within_mask = torch.tensor(within, dtype=torch.bool)
        mask = am & within_mask

        n_valid = int(mask.sum().item())
        if n_valid == 0:
            results.append({
                "mean_units_per_token": float("nan"),
                "n_valid_tokens": 0,
                "sum_units": float("nan"),
                "token_units_per_target": [] if store_token_level else None,
                "token_offsets_per_target": [] if store_token_level else None,
            })
            continue

        vals_nats = nll[b, : am.size(0)][mask.to(device)]
        vals_units = (vals_nats / ln2) if units == "bits" else vals_nats

        mean_u = float(vals_units.mean().item())
        sum_u = float(vals_units.sum().item())

        if store_token_level:
            offs_global = [offsets_gold[i] for i, ok in enumerate(mask.tolist()) if ok]
            offs_local = [(max(0, int(s - tgt_start)), max(0, int(e - tgt_start))) for (s, e) in offs_global]
            results.append({
                "mean_units_per_token": mean_u,
                "n_valid_tokens": n_valid,
                "sum_units": sum_u,
                "token_units_per_target": [float(x.item()) for x in vals_units],
                "token_offsets_per_target": offs_local,
            })
        else:
            results.append({
                "mean_units_per_token": mean_u,
                "n_valid_tokens": n_valid,
                "sum_units": sum_u,
            })

    return results


# ────────────────────────────────────────────────────────────────
# Main scoring for ONE shard
# ────────────────────────────────────────────────────────────────

def _parse_text_cols(text_col: str, text_cols: Optional[str]) -> List[str]:
    if text_cols and str(text_cols).strip():
        cols = [c.strip() for c in str(text_cols).split(",") if c.strip()]
        if not cols:
            raise ValueError("--text-cols was provided but parsed to an empty list.")
        return cols
    return [text_col]


def _suffix_for_col(col: str, multi: bool) -> str:
    return f"__{col}" if multi else ""


def score_shard(
    input_csv: Path,
    output_csv: Path,
    model_name: str,
    text_col: str,
    text_cols: Optional[str],
    context_col: Optional[str],
    strict_context_col: bool,
    units: str,
    batch_size: int,
    max_length: Optional[int],
    device_opt: str,
    dtype_opt: str,
    store_token_level: bool,
    apply_cleaning: bool,
    overwrite: bool,
    add_metadata: bool,
    # skip / eligibility controls
    word_count_col: str,
    morph_count_col: str,
    score_zero_counts: bool,
    min_word_count: int,
    min_morph_count: int,
) -> None:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists() and not overwrite:
        print(f"[SKIP] Output exists (use --overwrite): {output_csv}")
        return

    df = pd.read_csv(input_csv, sep=None, engine="python")
    if df.empty:
        # write an empty-but-schema-extended CSV
        df_out = df.copy()
        cols = _parse_text_cols(text_col, text_cols)
        multi = (len(cols) > 1)

        for c in cols:
            suf = _suffix_for_col(c, multi)
            if units == "bits":
                df_out[f"mean_bits_per_token{suf}"] = pd.Series(dtype=float)
                df_out[f"sum_bits{suf}"] = pd.Series(dtype=float)
            else:
                df_out[f"mean_nats_per_token{suf}"] = pd.Series(dtype=float)
                df_out[f"sum_nats{suf}"] = pd.Series(dtype=float)
            df_out[f"n_eval_tokens{suf}"] = pd.Series(dtype="Int64")

            if store_token_level:
                df_out[f"token_units_per_target{suf}"] = pd.Series(dtype=object)
                df_out[f"token_offsets_per_target{suf}"] = pd.Series(dtype=object)

        if add_metadata:
            df_out["model_used"] = model_name
            df_out["units_used"] = units
            df_out["text_cols_used"] = json.dumps(cols, ensure_ascii=False)
            df_out["context_col_used"] = (context_col or "")
            df_out["skip_zero_counts"] = (not score_zero_counts)
            df_out["min_word_count"] = int(min_word_count)
            df_out["min_morph_count"] = int(min_morph_count)

        df_out.to_csv(output_csv, index=False)
        print(f"[OK] Empty input -> wrote {output_csv}")
        return

    cols_to_score = _parse_text_cols(text_col, text_cols)
    multi = (len(cols_to_score) > 1)

    missing = [c for c in cols_to_score if c not in df.columns]
    if missing:
        raise KeyError(f"Missing text column(s) in {input_csv}: {missing}")

    if context_col and strict_context_col and (context_col not in df.columns):
        raise KeyError(f"Requested context column '{context_col}' not found in {input_csv}")

    use_context = bool(context_col) and (context_col in df.columns)

    # Eligibility mask (skip word_count==0 or morph_count==0 by default)
    if score_zero_counts:
        eligible_base = pd.Series([True] * len(df), index=df.index)
    else:
        if word_count_col not in df.columns or morph_count_col not in df.columns:
            raise KeyError(
                f"Need columns '{word_count_col}' and '{morph_count_col}' to skip zero-count rows. "
                f"Either add them to the shard, or pass --score-zero-counts."
            )
        wc = pd.to_numeric(df[word_count_col], errors="coerce").fillna(0)
        mc = pd.to_numeric(df[morph_count_col], errors="coerce").fillna(0)
        eligible_base = (wc >= int(min_word_count)) & (mc >= int(min_morph_count))

    device = pick_device(device_opt)
    dtype = pick_dtype(dtype_opt, device)
    tokenizer, model = load_model_and_tokenizer(model_name, device, dtype)

    # Precompute context strings once
    if use_context:
        ctx_raw = df[context_col].fillna("").astype(str).tolist()
        ctxs = [clean_for_lm(c) for c in ctx_raw] if apply_cleaning else [norm_ws(c) for c in ctx_raw]
    else:
        ctxs = [""] * len(df)

    df_out = df.copy()

    for col in cols_to_score:
        suf = _suffix_for_col(col, multi)

        texts_raw = df[col].fillna("").astype(str).tolist()
        texts = [clean_for_lm(t) for t in texts_raw] if apply_cleaning else [norm_ws(t) for t in texts_raw]

        # refine eligibility: also require non-empty text
        eligible = []
        for i in range(len(df)):
            eligible.append(bool(eligible_base.iloc[i]) and bool(texts[i]))

        idxs_to_score = [i for i, ok in enumerate(eligible) if ok]

        mean_list: List[float] = [float("nan")] * len(df)
        n_tok_list: List[int] = [0] * len(df)
        sum_list: List[float] = [float("nan")] * len(df)

        token_units_col: Optional[List[Optional[str]]] = None
        token_offs_col: Optional[List[Optional[str]]] = None
        if store_token_level:
            token_units_col = [None] * len(df)
            token_offs_col = [None] * len(df)

        # Build LM inputs + target starts ONLY for eligible rows
        lm_inputs: List[str] = []
        target_starts: List[int] = []

        for i in idxs_to_score:
            utt = texts[i]
            ctx = ctxs[i]
            if use_context and ctx:
                prefix = ctx + " "
                lm_inputs.append(prefix + utt)
                target_starts.append(len(prefix))
            else:
                lm_inputs.append(utt)
                target_starts.append(0)

        # Batch-score
        for start in range(0, len(idxs_to_score), max(1, batch_size)):
            batch_idxs = idxs_to_score[start:start + batch_size]
            local_slice = slice(start, start + len(batch_idxs))

            batch_texts = lm_inputs[local_slice]
            batch_starts = target_starts[local_slice]

            batch_res = batch_target_surprisal(
                batch_texts,
                batch_starts,
                tokenizer,
                model,
                device=device,
                units=units,
                max_length=max_length,
                store_token_level=store_token_level,
            )

            for j, res in enumerate(batch_res):
                i = batch_idxs[j]
                mean_list[i] = float(res["mean_units_per_token"])
                n_tok_list[i] = int(res["n_valid_tokens"])
                sum_list[i] = float(res["sum_units"])
                if store_token_level:
                    assert token_units_col is not None and token_offs_col is not None
                    token_units_col[i] = json.dumps(res.get("token_units_per_target", []), ensure_ascii=False)
                    token_offs_col[i] = json.dumps(res.get("token_offsets_per_target", []), ensure_ascii=False)

        # Optional sanity check: how many eligible non-empty utts got 0 tokens?
        n_weird = 0
        for i in idxs_to_score:
            if texts[i] and n_tok_list[i] == 0:
                n_weird += 1
        if n_weird:
            print(f"[WARN] {n_weird} eligible non-empty utterances in '{col}' ended up with 0 eval tokens (should be rare).")

        # Write output columns for this text col
        if units == "bits":
            df_out[f"mean_bits_per_token{suf}"] = mean_list
            df_out[f"sum_bits{suf}"] = sum_list
        else:
            df_out[f"mean_nats_per_token{suf}"] = mean_list
            df_out[f"sum_nats{suf}"] = sum_list
        df_out[f"n_eval_tokens{suf}"] = pd.Series(n_tok_list, dtype="Int64")

        if store_token_level:
            df_out[f"token_units_per_target{suf}"] = token_units_col
            df_out[f"token_offsets_per_target{suf}"] = token_offs_col

        print(
            f"[INFO] Scored col='{col}' | rows_total={len(df)} | eligible_scored={len(idxs_to_score)} | "
            f"skipped={(len(df)-len(idxs_to_score))} | context={'yes' if use_context else 'no'}"
        )

    if add_metadata:
        df_out["model_used"] = model_name
        df_out["units_used"] = units
        df_out["text_cols_used"] = json.dumps(cols_to_score, ensure_ascii=False)
        df_out["context_col_used"] = (context_col if (context_col and use_context) else "")
        df_out["skip_zero_counts"] = (not score_zero_counts)
        df_out["word_count_col_used"] = word_count_col
        df_out["morph_count_col_used"] = morph_count_col
        df_out["min_word_count"] = int(min_word_count)
        df_out["min_morph_count"] = int(min_morph_count)

    df_out.to_csv(output_csv, index=False)
    print(f"[OK] Wrote scored shard: {output_csv}  (rows={len(df_out)}, context={'yes' if use_context else 'no'})")


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

def build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="RAW surprisal scoring for one parallel_dataset shard CSV (optionally with context). Supports scoring multiple text columns."
    )
    p.add_argument("--input", required=True, help="Path to ONE shard CSV (input).")
    p.add_argument("--output", required=True, help="Path to output CSV (scored shard).")
    p.add_argument("--model", required=True, help="HF model id or local path.")
    p.add_argument("--units", choices=["bits", "nats"], default="bits")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--max-length", type=int, default=None, help="Optional max token length (HF truncation).")

    # Columns (single or multiple)
    p.add_argument(
        "--text-col",
        default="utterance_for_scoring",
        help="Single utterance column to score (ignored if --text-cols is provided).",
    )
    p.add_argument(
        "--text-cols",
        default=None,
        help="Comma-separated list of utterance columns to score in one pass. "
             "Example: utterance_clean,random_model_utterance_bin6,unigram_model_utterance_bin6,bigram_model_utterance_bin6",
    )
    p.add_argument("--context-col", default=None,
                   help="Optional context column (e.g., context_k1). If missing/not present, no-context scoring unless --strict-context-col is set.")
    p.add_argument("--strict-context-col", action="store_true",
                   help="Fail if --context-col was requested but the column is absent from the shard.")

    # Skip / eligibility (default: skip rows where word_count==0 OR morph_count==0)
    p.add_argument("--word-count-col", default="word_count", help="Column name for word counts.")
    p.add_argument("--morph-count-col", default="morph_count", help="Column name for morph counts.")
    p.add_argument("--min-word-count", type=int, default=1, help="Minimum word_count to score (default: 1).")
    p.add_argument("--min-morph-count", type=int, default=1, help="Minimum morph_count to score (default: 1).")
    p.add_argument(
        "--score-zero-counts",
        action="store_true",
        help="If set, do NOT skip rows with 0 counts (score everything that has non-empty text).",
    )

    # Compute controls
    p.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    p.add_argument("--dtype", choices=["auto", "fp32", "fp16", "bf16"], default="auto")
    p.add_argument("--store-token-level", action="store_true",
                   help="Store per-token units and offsets (JSON strings). Makes outputs larger.")
    p.add_argument("--apply-cleaning", action="store_true",
                   help="Re-apply canonical cleaning (OFF by default; your parallel_dataset is already cleaned).")

    # IO
    p.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists.")
    p.add_argument("--add-metadata", action="store_true",
                   help="Add columns describing model/units/text cols/context + skip policy.")

    return p


def main(argv=None) -> None:
    args = build_cli().parse_args(argv)

    score_shard(
        input_csv=Path(args.input).expanduser().resolve(),
        output_csv=Path(args.output).expanduser().resolve(),
        model_name=args.model,
        text_col=args.text_col,
        text_cols=args.text_cols,
        context_col=args.context_col,
        strict_context_col=bool(args.strict_context_col),
        units=args.units,
        batch_size=int(args.batch_size),
        max_length=args.max_length,
        device_opt=args.device,
        dtype_opt=args.dtype,
        store_token_level=bool(args.store_token_level),
        apply_cleaning=bool(args.apply_cleaning),
        overwrite=bool(args.overwrite),
        add_metadata=bool(args.add_metadata),
        word_count_col=args.word_count_col,
        morph_count_col=args.morph_count_col,
        score_zero_counts=bool(args.score_zero_counts),
        min_word_count=int(args.min_word_count),
        min_morph_count=int(args.min_morph_count),
    )


if __name__ == "__main__":
    main()