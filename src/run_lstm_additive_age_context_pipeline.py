#!/usr/bin/env python3
"""
Run additive age-bin LSTM generation for several caretaker-context windows.

This script is the PBM-focused orchestration layer for the apples-to-apples
LSTM baseline: for each target age bin, it trains on examples from that bin and
all earlier bins, then generates only the rows in the target bin. Separate
context settings such as k=3, k=4, and k=5 are trained independently.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from custom_age_bins import AgeBin, find_age_bin, floor_age_month, make_merged_early_bins, write_age_bins_config
from generate_lstm_utterances import (
    LSTMConfig,
    LSTMExample,
    Vocabulary,
    generate_tokens_with_lstm,
    limit_examples,
    save_config,
    save_vocab,
    set_seeds,
    train_lstm_model,
    with_terminal_punctuation,
    write_summary_csv,
)
from run_lstm_baseline_pipeline import (
    DEFAULT_BIG_DATASET_ROOT,
    DEFAULT_CONTEXT_FILENAME,
    DEFAULT_MANIFEST,
    build_examples_by_unit,
    discover_units_from_manifest,
    write_lstm_context_and_scoring_files_for_unit,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASETS = ("Brown", "Manchester", "Providence")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "lstm_baselines" / "pbm_additive_merged_006_023_k3_k4_k5"
DEFAULT_CONTEXTS = (3, 4, 5)
DEFAULT_CONTEXT_TOKEN_CAP = 60
DEFAULT_GENERATED_FILENAME = "chi.lstm_additive_generated.csv"
DEFAULT_CONTEXT_WITH_LSTM_FILENAME = "chi.shared_caretaker_contexts.with_lstm_additive.csv"
DEFAULT_SCORING_WITH_LSTM_FILENAME = "chi.surprisal_scoring_with_lstm_additive.csv"
DEFAULT_VARIANTS = ("same_length", "free_length")
VARIANT_LENGTH_MODES = {
    "same_length": "same_as_child",
    "free_length": "free_until_eos",
}
DIAGNOSTIC_SAMPLE_LIMIT = 12


def additive_column_name(context_utterances: int, variant: str) -> str:
    """Return a stable generated-utterance column name."""
    if variant not in VARIANT_LENGTH_MODES:
        raise ValueError(f"Unknown LSTM additive variant: {variant}")
    return f"lstm_additive_k{context_utterances}_{variant}_utterance"


def bin_end_age(age_bin: AgeBin) -> float:
    """Return the inclusive floating upper age used by existing filters."""
    return float(age_bin.end) + 0.999


def child_output_token_ids(examples: Sequence[LSTMExample], vocab: Vocabulary) -> List[int]:
    """Return vocabulary ids for child-side tokens observed in training examples."""
    token_ids = {
        vocab.token_to_id[token]
        for example in examples
        for token in example.child_tokens
        if token in vocab.token_to_id
    }
    if not token_ids:
        raise RuntimeError("No child-side output tokens were available for constrained LSTM generation.")
    return sorted(token_ids)


def example_bin(example: LSTMExample, bins: Sequence[AgeBin]) -> Optional[AgeBin]:
    """Return the configured age bin for one example."""
    return find_age_bin(example.age_months, bins)


def cumulative_train_examples(
    examples: Sequence[LSTMExample],
    *,
    first_start: int,
    age_bin: AgeBin,
) -> List[LSTMExample]:
    """Select examples from the first bin start through the target bin end."""
    out: List[LSTMExample] = []
    for example in examples:
        month = floor_age_month(example.age_months)
        if month is not None and first_start <= month <= age_bin.end:
            out.append(example)
    return out


def target_bin_examples(
    examples: Sequence[LSTMExample],
    *,
    bins: Sequence[AgeBin],
    age_bin: AgeBin,
) -> List[LSTMExample]:
    """Select examples whose age falls inside the target bin."""
    return [example for example in examples if example_bin(example, bins) == age_bin]


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    """Write indented UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def percentile(values: Sequence[int], q: float) -> float:
    """Return a simple nearest-rank percentile for diagnostics."""
    if not values:
        return math.nan
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return float(ordered[index])


def summarize_generation_diagnostics(stats: Mapping[Tuple[int, str, str], Dict[str, object]]) -> List[Dict[str, object]]:
    """Collapse generated-row statistics into one row per k/bin/variant."""
    rows: List[Dict[str, object]] = []
    for key in sorted(stats):
        context_utterances, age_bin, variant = key
        record = stats[key]
        generated_rows = int(record.get("generated_rows", 0))
        empty_rows = int(record.get("empty_generated_rows", 0))
        mismatches = int(record.get("same_length_mismatches", 0))
        real_lengths = list(record.get("real_token_lengths", []))
        generated_lengths = list(record.get("generated_token_lengths", []))
        rows.append(
            {
                "context_utterances": context_utterances,
                "age_bin": age_bin,
                "variant": variant,
                "generated_rows": generated_rows,
                "empty_generated_rows": empty_rows,
                "empty_generated_rate": empty_rows / generated_rows if generated_rows else math.nan,
                "same_length_mismatches": mismatches,
                "same_length_mismatch_rate": mismatches / generated_rows if generated_rows else math.nan,
                "real_token_mean": sum(real_lengths) / len(real_lengths) if real_lengths else math.nan,
                "real_token_p50": percentile(real_lengths, 0.50),
                "real_token_p90": percentile(real_lengths, 0.90),
                "generated_token_mean": sum(generated_lengths) / len(generated_lengths) if generated_lengths else math.nan,
                "generated_token_p50": percentile(generated_lengths, 0.50),
                "generated_token_p90": percentile(generated_lengths, 0.90),
            }
        )
    return rows


def write_diagnostic_plots(output_dir: Path) -> None:
    """Write static PNG/PDF diagnostics for training and generation outputs."""
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - plotting is a best-effort artifact
        print(f"[WARN] Could not import matplotlib for diagnostics: {exc}", flush=True)
        return

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    def savefig(name: str) -> None:
        for suffix in ("png", "pdf"):
            plt.savefig(plots_dir / f"{name}.{suffix}", bbox_inches="tight", dpi=180)
        plt.close()

    plan_path = output_dir / "additive_plan_summary.csv"
    training_path = output_dir / "training_summary.csv"
    generation_diag_path = output_dir / "generation_diagnostics.csv"

    if plan_path.exists():
        plan = pd.read_csv(plan_path)
        first_context = plan["context_utterances"].min()
        plan_one = plan[plan["context_utterances"] == first_context]
        plt.figure(figsize=(10, 5))
        x = range(len(plan_one))
        plt.plot(x, plan_one["train_examples_after_limit"], marker="o", label="cumulative training examples")
        plt.plot(x, plan_one["target_examples"], marker="s", label="target-bin rows")
        plt.xticks(list(x), plan_one["age_bin"], rotation=35, ha="right")
        plt.ylabel("Rows")
        plt.title("PBM Additive LSTM Data Schedule")
        plt.legend()
        plt.grid(alpha=0.25)
        savefig("additive_training_target_rows")

    if training_path.exists() and training_path.stat().st_size:
        training = pd.read_csv(training_path)
        if not training.empty:
            final_epoch = training.sort_values("epoch").groupby(["context_utterances", "age_bin"], as_index=False).tail(1)
            plt.figure(figsize=(10, 5))
            for context_utterances, group in final_epoch.groupby("context_utterances"):
                group = group.sort_values("age_bin")
                plt.plot(group["age_bin"], group["mean_cross_entropy"], marker="o", label=f"k={context_utterances}")
            plt.xticks(rotation=35, ha="right")
            plt.ylabel("Final mean cross-entropy")
            plt.title("LSTM Training Loss By Additive Age Bin")
            plt.legend()
            plt.grid(alpha=0.25)
            savefig("final_training_loss_by_age_bin")

            plt.figure(figsize=(10, 5))
            for context_utterances, group in final_epoch.groupby("context_utterances"):
                group = group.sort_values("age_bin")
                plt.plot(group["age_bin"], group["perplexity"], marker="o", label=f"k={context_utterances}")
            plt.xticks(rotation=35, ha="right")
            plt.ylabel("Final perplexity")
            plt.title("LSTM Training Perplexity By Additive Age Bin")
            plt.legend()
            plt.grid(alpha=0.25)
            savefig("final_training_perplexity_by_age_bin")

            plt.figure(figsize=(10, 5))
            for context_utterances, group in training.groupby("context_utterances"):
                group = group.sort_values(["age_bin", "epoch"])
                plt.plot(range(len(group)), group["mean_cross_entropy"], marker=".", label=f"k={context_utterances}")
            plt.xlabel("Model epochs ordered by age bin")
            plt.ylabel("Mean cross-entropy")
            plt.title("Training-Loss Trace Across Additive Models")
            plt.legend()
            plt.grid(alpha=0.25)
            savefig("training_loss_trace")

    if generation_diag_path.exists() and generation_diag_path.stat().st_size:
        diagnostics = pd.read_csv(generation_diag_path)
        if not diagnostics.empty:
            same = diagnostics[diagnostics["variant"] == "same_length"]
            plt.figure(figsize=(10, 5))
            for context_utterances, group in same.groupby("context_utterances"):
                group = group.sort_values("age_bin")
                plt.plot(group["age_bin"], group["same_length_mismatch_rate"], marker="o", label=f"k={context_utterances}")
            plt.xticks(rotation=35, ha="right")
            plt.ylabel("Mismatch rate")
            plt.title("Same-Length Generation Control Check")
            plt.legend()
            plt.grid(alpha=0.25)
            savefig("same_length_mismatch_rate")

            plt.figure(figsize=(10, 5))
            for (context_utterances, variant), group in diagnostics.groupby(["context_utterances", "variant"]):
                group = group.sort_values("age_bin")
                plt.plot(
                    group["age_bin"],
                    group["generated_token_mean"],
                    marker="o",
                    label=f"k={context_utterances} {variant}",
                )
            plt.xticks(rotation=35, ha="right")
            plt.ylabel("Mean generated word tokens")
            plt.title("Generated Lengths By Context Window And Age")
            plt.legend(ncol=2, fontsize=8)
            plt.grid(alpha=0.25)
            savefig("generated_token_lengths_by_age")


def generation_count(rows_by_index: Mapping[int, Mapping[str, str]], column: str) -> int:
    """Count non-empty generated strings for one column."""
    return sum(1 for row in rows_by_index.values() if str(row.get(column, "")).strip())


def write_generated_files(
    units,
    generated_by_unit: Mapping[Path, Mapping[int, Mapping[str, str]]],
    columns: Sequence[str],
    *,
    output_filename: str,
) -> List[Dict[str, object]]:
    """Write one per-child generated file containing all additive LSTM columns."""
    rows: List[Dict[str, object]] = []
    for unit in units:
        df = pd.read_csv(unit.chi_csv, dtype=str, keep_default_na=False, low_memory=False)
        for column in columns:
            df[column] = ""
        for row_index, generated_columns in generated_by_unit.get(unit.folder, {}).items():
            for column, value in generated_columns.items():
                if column in columns:
                    df.at[int(row_index), column] = value

        out_path = unit.folder / output_filename
        df.to_csv(out_path, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")
        summary = {
            "dataset": unit.dataset,
            "child_id": unit.child,
            "source_rows": len(df),
            "generated_csv": str(out_path),
        }
        unit_rows = generated_by_unit.get(unit.folder, {})
        for column in columns:
            summary[column] = generation_count(unit_rows, column)
        rows.append(summary)
    return rows


def write_unit_manifest(
    path: Path,
    units,
    generation_rows: Sequence[Mapping[str, object]],
    scoring_rows: Sequence[Mapping[str, object]],
    columns: Sequence[str],
) -> List[Dict[str, object]]:
    """Write one row per child folder summarizing additive LSTM outputs."""
    generation_by_child = {(row["dataset"], row["child_id"]): row for row in generation_rows}
    scoring_by_child = {(row["dataset"], row["child_id"]): row for row in scoring_rows}
    fieldnames = [
        "dataset",
        "child_id",
        "chi_csv",
        "caretakers_csv",
        "generated_csv",
        "context_with_lstm_csv",
        "scoring_with_lstm_csv",
        "source_rows",
        "scoring_rows",
        *columns,
    ]
    rows: List[Dict[str, object]] = []
    for unit in units:
        key = (unit.dataset, unit.child)
        generation = generation_by_child.get(key, {})
        scoring = scoring_by_child.get(key, {})
        row = {
            "dataset": unit.dataset,
            "child_id": unit.child,
            "chi_csv": str(unit.chi_csv),
            "caretakers_csv": str(unit.caretakers_csv or ""),
            "generated_csv": generation.get("generated_csv", ""),
            "context_with_lstm_csv": scoring.get("context_with_lstm_csv", ""),
            "scoring_with_lstm_csv": scoring.get("scoring_with_lstm_csv", ""),
            "source_rows": generation.get("source_rows", ""),
            "scoring_rows": scoring.get("scoring_rows", ""),
        }
        for column in columns:
            row[column] = generation.get(column, "")
        rows.append(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def run_additive_age_context_pipeline(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    datasets: Sequence[str] = DEFAULT_DATASETS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    context_utterances_values: Sequence[int] = DEFAULT_CONTEXTS,
    variants: Sequence[str] = DEFAULT_VARIANTS,
    generated_filename: str = DEFAULT_GENERATED_FILENAME,
    context_filename: str = DEFAULT_CONTEXT_FILENAME,
    context_output_filename: str = DEFAULT_CONTEXT_WITH_LSTM_FILENAME,
    scoring_output_filename: str = DEFAULT_SCORING_WITH_LSTM_FILENAME,
    dry_run: bool = False,
    max_train_examples_per_bin: Optional[int] = None,
    max_generate_rows_per_child_per_bin: Optional[int] = None,
    base_config: Optional[LSTMConfig] = None,
    bins: Optional[Sequence[AgeBin]] = None,
) -> Dict[str, object]:
    """Train additive age-bin LSTMs and write generated/scoring sibling files."""
    age_bins = list(bins or make_merged_early_bins(first_start=6, first_end=23, max_month=65))
    first_start = age_bins[0].start
    output_dir.mkdir(parents=True, exist_ok=True)
    set_seeds((base_config or LSTMConfig()).seed)

    for variant in variants:
        if variant not in VARIANT_LENGTH_MODES:
            raise ValueError(f"Unknown LSTM additive variant: {variant}")

    units = discover_units_from_manifest(manifest_path, datasets=datasets)
    if not units:
        raise RuntimeError(f"No child units found in {manifest_path} for datasets={datasets}")

    generated_columns = [
        additive_column_name(context_utterances, variant)
        for context_utterances in context_utterances_values
        for variant in variants
    ]
    write_json(
        output_dir / "run_config.json",
        {
            "manifest_path": str(manifest_path),
            "datasets": list(datasets),
            "context_utterances_values": list(context_utterances_values),
            "context_token_cap": (base_config.max_context_tokens if base_config else DEFAULT_CONTEXT_TOKEN_CAP),
            "variants": list(variants),
            "generated_columns": generated_columns,
            "additive_age_bins": [asdict(age_bin) | {"label": age_bin.label} for age_bin in age_bins],
            "dry_run": dry_run,
        },
    )
    write_age_bins_config(
        output_dir / "age_bins.json",
        bins=age_bins,
        strategy="merged_early_006_023_additive_lstm",
        count_basis="child_nonempty_utterances",
    )

    dry_rows: List[Dict[str, object]] = []
    training_rows: List[Dict[str, object]] = []
    model_rows: List[Dict[str, object]] = []
    generation_rows_by_bin: List[Dict[str, object]] = []
    generation_diagnostic_stats: Dict[Tuple[int, str, str], Dict[str, object]] = defaultdict(
        lambda: {
            "generated_rows": 0,
            "empty_generated_rows": 0,
            "same_length_mismatches": 0,
            "real_token_lengths": [],
            "generated_token_lengths": [],
        }
    )
    generation_sample_rows: List[Dict[str, object]] = []
    generation_sample_counts: Dict[Tuple[int, str, str], int] = defaultdict(int)
    generated_by_unit: Dict[Path, Dict[int, Dict[str, str]]] = defaultdict(lambda: defaultdict(dict))

    for context_utterances in context_utterances_values:
        context_config = replace(
            base_config
            or LSTMConfig(
                data_dir=str(DEFAULT_BIG_DATASET_ROOT / "preprocessed_data"),
                datasets=tuple(datasets),
                output_dir=str(output_dir),
                architecture="seq2seq_lstm",
                context_utterances=context_utterances,
                max_context_tokens=DEFAULT_CONTEXT_TOKEN_CAP,
                min_age_months=float(first_start),
                max_age_months=bin_end_age(age_bins[-1]),
                max_train_examples=max_train_examples_per_bin,
                max_generate_rows_per_child=max_generate_rows_per_child_per_bin,
                device="cuda",
            ),
            datasets=tuple(datasets),
            output_dir=str(output_dir),
            output_filename=generated_filename,
            output_column=additive_column_name(context_utterances, "same_length"),
            context_utterances=context_utterances,
            min_age_months=float(first_start),
            max_age_months=bin_end_age(age_bins[-1]),
            max_train_examples=max_train_examples_per_bin,
            max_generate_rows_per_child=max_generate_rows_per_child_per_bin,
        )

        examples_by_unit, all_examples = build_examples_by_unit(units, context_config)
        for age_bin in age_bins:
            train_examples = cumulative_train_examples(all_examples, first_start=first_start, age_bin=age_bin)
            limited_train_examples = limit_examples(train_examples, max_train_examples_per_bin, context_config.seed)
            target_examples_by_unit = {
                unit.folder: limit_examples(
                    target_bin_examples(examples_by_unit.get(unit.folder, []), bins=age_bins, age_bin=age_bin),
                    max_generate_rows_per_child_per_bin,
                    context_config.seed,
                )
                for unit in units
            }
            target_examples = [example for examples in target_examples_by_unit.values() for example in examples]
            bin_dir = output_dir / f"k{context_utterances}" / f"bin_{age_bin.label}"
            bin_config = replace(
                context_config,
                output_dir=str(bin_dir),
                max_age_months=bin_end_age(age_bin),
            )
            save_config(bin_dir / "config.json", bin_config)
            dry_rows.append(
                {
                    "context_utterances": context_utterances,
                    "age_bin": age_bin.label,
                    "train_examples_available": len(train_examples),
                    "train_examples_after_limit": len(limited_train_examples),
                    "target_examples": len(target_examples),
                    "output_dir": str(bin_dir),
                }
            )
            if dry_run:
                continue

            if not limited_train_examples:
                raise RuntimeError(f"No training examples for k={context_utterances}, bin={age_bin.label}")

            vocab = Vocabulary.build(
                (example.context_tokens + example.child_tokens for example in limited_train_examples),
                min_freq=bin_config.min_freq,
                max_vocab_size=bin_config.max_vocab_size,
            )
            allowed_output_token_ids = child_output_token_ids(limited_train_examples, vocab)
            save_vocab(bin_dir / "vocab.json", vocab)
            model, bin_training_rows = train_lstm_model(
                limited_train_examples,
                vocab,
                bin_config,
                bin_dir,
                batch_log_path=bin_dir / "batch_training_log.csv",
                log_every_batches=25,
                progress_prefix=f"k={context_utterances} bin={age_bin.label}",
            )
            final_training = bin_training_rows[-1] if bin_training_rows else {}
            model_rows.append(
                {
                    "context_utterances": context_utterances,
                    "age_bin": age_bin.label,
                    "output_dir": str(bin_dir),
                    "train_examples_available": len(train_examples),
                    "train_examples_after_limit": len(limited_train_examples),
                    "target_examples": len(target_examples),
                    "vocab_size": len(vocab.id_to_token),
                    "child_output_vocab_size": len(allowed_output_token_ids),
                    "trainable_parameters": final_training.get("trainable_parameters", ""),
                    "final_mean_cross_entropy": final_training.get("mean_cross_entropy", ""),
                    "final_perplexity": final_training.get("perplexity", ""),
                    "device": final_training.get("device", ""),
                    "model_pt": str(bin_dir / "model.pt"),
                    "batch_training_log": str(bin_dir / "batch_training_log.csv"),
                }
            )
            for row in bin_training_rows:
                training_rows.append(
                    {
                        "context_utterances": context_utterances,
                        "age_bin": age_bin.label,
                        "train_examples_available": len(train_examples),
                        **row,
                    }
                )
            write_summary_csv(bin_dir / "training_summary.csv", bin_training_rows)

            for unit in units:
                unit_examples = target_examples_by_unit.get(unit.folder, [])
                row_counts = {column: 0 for column in generated_columns}
                for example in unit_examples:
                    for variant in variants:
                        column = additive_column_name(context_utterances, variant)
                        variant_config = replace(
                            bin_config,
                            output_column=column,
                            generation_length_mode=VARIANT_LENGTH_MODES[variant],
                            max_generated_tokens=30 if variant == "free_length" else 50,
                            min_generated_tokens=1,
                        )
                        generated_tokens = generate_tokens_with_lstm(
                            model,
                            vocab,
                            example,
                            variant_config,
                            allowed_output_token_ids=allowed_output_token_ids,
                        )
                        generated_text = with_terminal_punctuation(generated_tokens, example.terminal_punct)
                        generated_by_unit[unit.folder][example.row_index][column] = generated_text
                        if generated_text.strip():
                            row_counts[column] += 1
                        diagnostic_key = (context_utterances, age_bin.label, variant)
                        diagnostic = generation_diagnostic_stats[diagnostic_key]
                        real_len = len(example.child_tokens)
                        generated_len = len(generated_tokens)
                        diagnostic["generated_rows"] = int(diagnostic["generated_rows"]) + 1
                        diagnostic["empty_generated_rows"] = int(diagnostic["empty_generated_rows"]) + (0 if generated_text.strip() else 1)
                        if variant == "same_length" and generated_len != real_len:
                            diagnostic["same_length_mismatches"] = int(diagnostic["same_length_mismatches"]) + 1
                        diagnostic["real_token_lengths"].append(real_len)
                        diagnostic["generated_token_lengths"].append(generated_len)
                        if generation_sample_counts[diagnostic_key] < DIAGNOSTIC_SAMPLE_LIMIT:
                            generation_sample_rows.append(
                                {
                                    "context_utterances": context_utterances,
                                    "age_bin": age_bin.label,
                                    "variant": variant,
                                    "dataset": unit.dataset,
                                    "child_id": unit.child,
                                    "row_index": example.row_index,
                                    "age_months": example.age_months,
                                    "real_child_tokens": " ".join(example.child_tokens),
                                    "generated_text": generated_text,
                                    "real_token_len": real_len,
                                    "generated_token_len": generated_len,
                                    "context_token_len": len(example.context_tokens),
                                    "context_tail": " ".join(example.context_tokens[-30:]),
                                }
                            )
                            generation_sample_counts[diagnostic_key] += 1

                generation_rows_by_bin.append(
                    {
                        "context_utterances": context_utterances,
                        "age_bin": age_bin.label,
                        "dataset": unit.dataset,
                        "child_id": unit.child,
                        "target_examples": len(unit_examples),
                        **row_counts,
                    }
                )

    write_summary_csv(output_dir / "additive_plan_summary.csv", dry_rows)
    if dry_run:
        return {
            "dry_run": True,
            "units": len(units),
            "contexts": list(context_utterances_values),
            "age_bins": [age_bin.label for age_bin in age_bins],
            "plan_rows": len(dry_rows),
            "output_dir": str(output_dir),
        }

    write_summary_csv(output_dir / "training_summary.csv", training_rows)
    write_summary_csv(output_dir / "model_run_manifest.csv", model_rows)
    write_summary_csv(output_dir / "generation_by_bin_summary.csv", generation_rows_by_bin)
    write_summary_csv(output_dir / "generation_diagnostics.csv", summarize_generation_diagnostics(generation_diagnostic_stats))
    write_summary_csv(output_dir / "generation_samples.csv", generation_sample_rows)
    generation_rows = write_generated_files(
        units,
        generated_by_unit,
        generated_columns,
        output_filename=generated_filename,
    )
    write_summary_csv(output_dir / "generation_summary.csv", generation_rows)
    scoring_rows = [
        write_lstm_context_and_scoring_files_for_unit(
            unit,
            generated_filename=generated_filename,
            context_filename=context_filename,
            context_output_filename=context_output_filename,
            scoring_output_filename=scoring_output_filename,
            lstm_columns=generated_columns,
        )
        for unit in units
    ]
    manifest_rows = write_unit_manifest(
        output_dir / "lstm_additive_pipeline_manifest.csv",
        units,
        generation_rows,
        scoring_rows,
        generated_columns,
    )
    write_diagnostic_plots(output_dir)
    return {
        "dry_run": False,
        "units": len(units),
        "contexts": list(context_utterances_values),
        "age_bins": [age_bin.label for age_bin in age_bins],
        "manifest_rows": len(manifest_rows),
        "output_dir": str(output_dir),
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Run PBM additive age-bin LSTM generation for k-context variants.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS))
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--contexts", nargs="+", type=int, default=list(DEFAULT_CONTEXTS))
    parser.add_argument("--variants", nargs="+", choices=sorted(VARIANT_LENGTH_MODES), default=list(DEFAULT_VARIANTS))
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--context_token_cap", type=int, default=DEFAULT_CONTEXT_TOKEN_CAP)
    parser.add_argument("--max_train_examples_per_bin", type=int, default=None)
    parser.add_argument("--max_generate_rows_per_child_per_bin", type=int, default=None)
    parser.add_argument("--embedding_dim", type=int, default=128)
    parser.add_argument("--hidden_dim", type=int, default=256)
    parser.add_argument("--num_layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--grad_clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--max_vocab_size", type=int, default=30000)
    parser.add_argument("--min_freq", type=int, default=1)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--generated_filename", default=DEFAULT_GENERATED_FILENAME)
    parser.add_argument("--context_filename", default=DEFAULT_CONTEXT_FILENAME)
    parser.add_argument("--context_output_filename", default=DEFAULT_CONTEXT_WITH_LSTM_FILENAME)
    parser.add_argument("--scoring_output_filename", default=DEFAULT_SCORING_WITH_LSTM_FILENAME)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entry point."""
    args = parse_args(argv)
    base_config = LSTMConfig(
        data_dir=str(DEFAULT_BIG_DATASET_ROOT / "preprocessed_data"),
        datasets=tuple(args.datasets),
        output_dir=str(args.output_dir),
        output_filename=args.generated_filename,
        architecture="seq2seq_lstm",
        context_utterances=args.contexts[0],
        max_context_tokens=args.context_token_cap,
        min_age_months=6.0,
        max_age_months=65.999,
        min_token_len=1,
        lowercase=True,
        min_freq=args.min_freq,
        max_vocab_size=args.max_vocab_size,
        embedding_dim=args.embedding_dim,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        grad_clip=args.grad_clip,
        seed=args.seed,
        temperature=args.temperature,
        top_k=args.top_k,
        device=args.device,
    )
    summary = run_additive_age_context_pipeline(
        manifest_path=args.manifest,
        datasets=args.datasets,
        output_dir=args.output_dir,
        context_utterances_values=args.contexts,
        variants=args.variants,
        generated_filename=args.generated_filename,
        context_filename=args.context_filename,
        context_output_filename=args.context_output_filename,
        scoring_output_filename=args.scoring_output_filename,
        dry_run=args.dry_run,
        max_train_examples_per_bin=args.max_train_examples_per_bin,
        max_generate_rows_per_child_per_bin=args.max_generate_rows_per_child_per_bin,
        base_config=base_config,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
