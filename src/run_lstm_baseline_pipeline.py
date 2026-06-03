#!/usr/bin/env python3
"""
Run the LSTM baseline pipeline around an existing cleaned dataset.

This is the GPU-oriented orchestration layer for the LSTM baseline. It trains
one encoder-decoder LSTM from caregiver context to child utterance, generates
child baseline utterances, and writes scoring-ready CSVs with the LSTM columns
next to the existing random/unigram/bigram/trigram baselines.

The default paths target the current big-cleaned strict naturalistic dataset.
For this laptop, use --dry-run to validate inputs without training.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from build_age_word_dicts import ChildUnit
from custom_age_bins import (
    AgeBin,
    age_bins_to_dicts,
    find_age_bin,
    floor_age_month,
    load_age_bins_config,
    make_merged_early_bins,
)
from create_minimal_surprisal_scoring_csvs import (
    CHILD_OUTPUT_COLUMNS,
    child_scoring_row,
    text_or_empty,
    write_rows,
)
from generate_lstm_utterances import (
    GENERATION_LENGTH_MODES,
    LSTMConfig,
    LSTMExample,
    Vocabulary,
    generate_tokens_with_lstm,
    limit_examples,
    load_lstm_examples_for_unit,
    save_config,
    save_vocab,
    set_seeds,
    train_lstm_model,
    with_terminal_punctuation,
    write_summary_csv,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BIG_DATASET_ROOT = PROJECT_ROOT / "data" / "big_cleaned_dataset" / "default_naturalistic_merged_006_023"
DEFAULT_DATA_DIR = DEFAULT_BIG_DATASET_ROOT / "preprocessed_data"
DEFAULT_MANIFEST = DEFAULT_BIG_DATASET_ROOT / "manifest.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "lstm_baselines" / "default_naturalistic_merged_006_023"
DEFAULT_GENERATED_FILENAME = "chi.lstm_generated.csv"
DEFAULT_CONTEXT_WITH_LSTM_FILENAME = "chi.shared_caretaker_contexts.with_lstm.csv"
DEFAULT_SCORING_WITH_LSTM_FILENAME = "chi.surprisal_scoring_with_lstm.csv"
DEFAULT_CONTEXT_FILENAME = "chi.shared_caretaker_contexts.csv"
DEFAULT_SCORING_FILENAME = "chi.surprisal_scoring.csv"
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "lstm_baseline_16gb_default.json"
DEFAULT_AGE_BINS_CONFIG = DEFAULT_BIG_DATASET_ROOT / "age_ngram_dicts" / "merged_early_006_023" / "age_bins.json"

UNIT_MANIFEST_COLUMNS = [
    "dataset",
    "child_id",
    "chi_csv",
    "caretakers_csv",
    "generated_csv",
    "context_with_lstm_csv",
    "scoring_with_lstm_csv",
    "source_rows",
    "same_length_rows",
    "free_length_rows",
    "scoring_rows",
]


@dataclass(frozen=True)
class LSTMVariant:
    """One generation setting emitted from the trained LSTM."""

    name: str
    output_column: str
    generation_length_mode: str
    max_generated_tokens: int
    min_generated_tokens: int


@dataclass(frozen=True)
class LSTMAgeBinning:
    """How LSTM training/generation should be split by child age."""

    mode: str = "global"
    bins_config: Optional[str] = None
    strategy: str = "merged_early_006_023"


@dataclass(frozen=True)
class AdditiveBinRun:
    """One additive age-bin LSTM run."""

    age_bin: AgeBin
    train_examples: Tuple[LSTMExample, ...]
    target_examples: Tuple[LSTMExample, ...]


DEFAULT_VARIANTS = {
    "same_length": LSTMVariant(
        name="same_length",
        output_column="lstm_same_length_utterance",
        generation_length_mode="same_as_child",
        max_generated_tokens=50,
        min_generated_tokens=1,
    ),
    "free_length": LSTMVariant(
        name="free_length",
        output_column="lstm_free_length_utterance",
        generation_length_mode="free_until_eos",
        max_generated_tokens=30,
        min_generated_tokens=1,
    ),
}


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    """Read CSV dictionaries from a path."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def discover_units_from_manifest(manifest_path: Path, datasets: Optional[Sequence[str]] = None) -> List[ChildUnit]:
    """Return child units from a big-cleaned manifest."""
    dataset_filter = set(datasets) if datasets else None
    units: List[ChildUnit] = []
    for row in read_csv_rows(manifest_path):
        if dataset_filter and row["dataset"] not in dataset_filter:
            continue
        chi_csv = PROJECT_ROOT / row["chi_csv"]
        caretakers_csv = PROJECT_ROOT / row["caretakers_csv"] if row.get("caretakers_csv") else None
        units.append(
            ChildUnit(
                dataset=row["dataset"],
                child=row["child_id"],
                folder=chi_csv.parent,
                chi_csv=chi_csv,
                caretakers_csv=caretakers_csv,
            )
        )
    return units


def variant_from_mapping(mapping: Mapping[str, object]) -> LSTMVariant:
    """Build one LSTMVariant from a JSON mapping."""
    name = str(mapping.get("name", "")).strip()
    if not name:
        raise ValueError("Variant mapping requires a non-empty 'name'.")
    if name in DEFAULT_VARIANTS:
        base = asdict(DEFAULT_VARIANTS[name])
    else:
        base = {
            "name": name,
            "output_column": "",
            "generation_length_mode": "",
            "max_generated_tokens": 50,
            "min_generated_tokens": 1,
        }
    base.update(mapping)

    allowed = {field.name for field in fields(LSTMVariant)}
    unknown = sorted(set(base) - allowed)
    if unknown:
        raise ValueError(f"Unknown LSTM variant field(s): {unknown}")
    if base["generation_length_mode"] not in GENERATION_LENGTH_MODES:
        raise ValueError(
            f"Unknown generation_length_mode for variant {name!r}: {base['generation_length_mode']}"
        )
    if not str(base["output_column"]).strip():
        raise ValueError(f"Variant {name!r} requires a non-empty output_column.")
    return LSTMVariant(
        name=str(base["name"]),
        output_column=str(base["output_column"]),
        generation_length_mode=str(base["generation_length_mode"]),
        max_generated_tokens=int(base["max_generated_tokens"]),
        min_generated_tokens=int(base["min_generated_tokens"]),
    )


def normalize_variants(names: Sequence[object]) -> Tuple[LSTMVariant, ...]:
    """Return configured variants from CLI names or JSON variant mappings."""
    variants: List[LSTMVariant] = []
    for item in names:
        if isinstance(item, Mapping):
            variants.append(variant_from_mapping(item))
            continue
        name = str(item)
        if name not in DEFAULT_VARIANTS:
            raise ValueError(f"Unknown LSTM generation variant: {name}")
        variants.append(DEFAULT_VARIANTS[name])
    return tuple(variants)


def resolve_project_path(value: object) -> Path:
    """Resolve config paths relative to the project root unless absolute."""
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def lstm_config_from_mapping(mapping: Mapping[str, object], base_config: LSTMConfig) -> LSTMConfig:
    """Return an LSTMConfig with fields overridden from a JSON mapping."""
    valid_fields = {field.name for field in fields(LSTMConfig)}
    unknown = sorted(set(mapping) - valid_fields)
    if unknown:
        raise ValueError(f"Unknown LSTM config field(s): {unknown}")

    payload = asdict(base_config)
    payload.update(mapping)
    if "datasets" in payload and payload["datasets"] is not None:
        payload["datasets"] = tuple(payload["datasets"])
    return LSTMConfig(**payload)


def load_pipeline_config(path: Path) -> Dict[str, object]:
    """
    Load one JSON LSTM pipeline config.

    The config is intentionally plain JSON so it can be edited on the GPU
    machine without importing this repository as a package. Paths are resolved
    relative to PROJECT_ROOT unless absolute.
    """
    config_path = path.expanduser()
    with config_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"Expected object at top level of {path}")

    allowed_top_level = {
        "description",
        "manifest",
        "data_dir",
        "datasets",
        "output_dir",
        "variants",
        "context_filename",
        "generated_filename",
        "context_output_filename",
        "scoring_output_filename",
        "dry_run",
        "age_binning",
        "model",
    }
    unknown = sorted(set(raw) - allowed_top_level)
    if unknown:
        raise ValueError(f"Unknown pipeline config field(s): {unknown}")

    data_dir = resolve_project_path(raw.get("data_dir", DEFAULT_DATA_DIR))
    output_dir = resolve_project_path(raw.get("output_dir", DEFAULT_OUTPUT_DIR))
    model_mapping = raw.get("model", {})
    if not isinstance(model_mapping, dict):
        raise ValueError("Expected 'model' in config to be an object.")

    datasets_raw = raw.get("datasets")
    datasets = tuple(datasets_raw) if datasets_raw else tuple()
    base_config = LSTMConfig(
        data_dir=str(data_dir),
        datasets=datasets,
        output_dir=str(output_dir),
        output_filename=str(raw.get("generated_filename", DEFAULT_GENERATED_FILENAME)),
        output_column="lstm_same_length_utterance",
        architecture="seq2seq_lstm",
        context_utterances=3,
        max_context_tokens=60,
        min_age_months=6.0,
        max_age_months=65.999,
        generation_length_mode="same_as_child",
    )
    lstm_config = lstm_config_from_mapping(model_mapping, base_config)
    age_binning = age_binning_from_mapping(raw.get("age_binning", {}))

    return {
        "manifest_path": resolve_project_path(raw.get("manifest", DEFAULT_MANIFEST)),
        "data_dir": data_dir,
        "datasets": list(datasets) if datasets else None,
        "output_dir": output_dir,
        "variants": normalize_variants(raw.get("variants") or ["same_length", "free_length"]),
        "context_filename": str(raw.get("context_filename", DEFAULT_CONTEXT_FILENAME)),
        "generated_filename": str(raw.get("generated_filename", DEFAULT_GENERATED_FILENAME)),
        "context_output_filename": str(raw.get("context_output_filename", DEFAULT_CONTEXT_WITH_LSTM_FILENAME)),
        "scoring_output_filename": str(raw.get("scoring_output_filename", DEFAULT_SCORING_WITH_LSTM_FILENAME)),
        "dry_run": bool(raw.get("dry_run", False)),
        "config": lstm_config,
        "age_binning": age_binning,
    }


def age_binning_from_mapping(value: object) -> LSTMAgeBinning:
    """Build an age-binning config from JSON."""
    if value in (None, ""):
        return LSTMAgeBinning()
    if not isinstance(value, Mapping):
        raise ValueError("Expected 'age_binning' to be an object.")
    allowed = {"mode", "bins_config", "strategy"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"Unknown age_binning field(s): {unknown}")
    mode = str(value.get("mode", "global"))
    if mode not in {"global", "additive_age_bins"}:
        raise ValueError(f"Unknown LSTM age_binning mode: {mode}")
    bins_config = value.get("bins_config")
    return LSTMAgeBinning(
        mode=mode,
        bins_config=str(resolve_project_path(bins_config)) if bins_config else None,
        strategy=str(value.get("strategy", "merged_early_006_023")),
    )


def build_examples_by_unit(
    units: Sequence[ChildUnit],
    config: LSTMConfig,
) -> Tuple[Dict[Path, List[LSTMExample]], List[LSTMExample]]:
    """Load LSTM examples for all units."""
    examples_by_unit: Dict[Path, List[LSTMExample]] = {}
    all_examples: List[LSTMExample] = []
    for unit in units:
        examples = load_lstm_examples_for_unit(unit, config)
        examples_by_unit[unit.folder] = examples
        all_examples.extend(examples)
    return examples_by_unit, all_examples


def resolve_lstm_age_bins(age_binning: LSTMAgeBinning, config: LSTMConfig) -> List[AgeBin]:
    """Return the age bins for additive LSTM training."""
    if age_binning.mode == "global":
        return []
    if age_binning.bins_config:
        bins = load_age_bins_config(Path(age_binning.bins_config))
    elif age_binning.strategy == "merged_early_006_023":
        bins = make_merged_early_bins(max_month=int(config.max_age_months))
    else:
        raise ValueError(f"Unsupported additive LSTM age-bin strategy: {age_binning.strategy}")
    if not bins:
        raise ValueError("Additive LSTM age-binning requires at least one age bin.")
    return bins


def examples_in_target_bin(examples: Sequence[LSTMExample], age_bin: AgeBin) -> Tuple[LSTMExample, ...]:
    """Return examples whose floored age is inside one target bin."""
    return tuple(
        example
        for example in examples
        if (month := floor_age_month(example.age_months)) is not None and age_bin.contains_month(month)
    )


def examples_for_additive_training_bin(
    examples: Sequence[LSTMExample],
    age_bin: AgeBin,
    bins: Sequence[AgeBin],
) -> Tuple[LSTMExample, ...]:
    """Return cumulative examples from the first bin through the target bin."""
    first_start = bins[0].start
    return tuple(
        example
        for example in examples
        if (month := floor_age_month(example.age_months)) is not None
        and first_start <= month <= age_bin.end
    )


def build_additive_bin_runs(
    examples: Sequence[LSTMExample],
    bins: Sequence[AgeBin],
) -> List[AdditiveBinRun]:
    """Build cumulative training sets and target-generation sets for each bin."""
    runs: List[AdditiveBinRun] = []
    for age_bin in bins:
        runs.append(
            AdditiveBinRun(
                age_bin=age_bin,
                train_examples=examples_for_additive_training_bin(examples, age_bin, bins),
                target_examples=examples_in_target_bin(examples, age_bin),
            )
        )
    return runs


def variant_config(base_config: LSTMConfig, variant: LSTMVariant) -> LSTMConfig:
    """Return a config adjusted for one generation variant."""
    return replace(
        base_config,
        output_column=variant.output_column,
        generation_length_mode=variant.generation_length_mode,
        max_generated_tokens=variant.max_generated_tokens,
        min_generated_tokens=variant.min_generated_tokens,
    )


def write_multi_variant_generated_files(
    units: Sequence[ChildUnit],
    examples_by_unit: Dict[Path, List[LSTMExample]],
    model,
    vocab: Vocabulary,
    base_config: LSTMConfig,
    variants: Sequence[LSTMVariant],
    *,
    output_filename: str = DEFAULT_GENERATED_FILENAME,
) -> List[Dict[str, object]]:
    """Write one sibling generated CSV per child with all requested LSTM columns."""
    summaries: List[Dict[str, object]] = []
    for unit in units:
        df = pd.read_csv(unit.chi_csv, dtype=str, keep_default_na=False, low_memory=False)
        examples = limit_examples(
            examples_by_unit.get(unit.folder, []),
            base_config.max_generate_rows_per_child,
            base_config.seed,
        )
        row_counts = {variant.output_column: 0 for variant in variants}

        for variant in variants:
            df[variant.output_column] = ""
            config = variant_config(base_config, variant)
            for example in examples:
                generated_tokens = generate_tokens_with_lstm(model, vocab, example, config)
                generated = with_terminal_punctuation(generated_tokens, example.terminal_punct)
                df.at[example.row_index, variant.output_column] = generated
                if generated.strip():
                    row_counts[variant.output_column] += 1

        out_path = unit.folder / output_filename
        df.to_csv(out_path, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")
        summary = {
            "dataset": unit.dataset,
            "child_id": unit.child,
            "source_rows": len(df),
            "generated_csv": str(out_path),
        }
        summary.update(row_counts)
        summaries.append(summary)
    return summaries


def initialize_generated_frames(
    units: Sequence[ChildUnit],
    variants: Sequence[LSTMVariant],
    *,
    include_age_bin: bool,
) -> Dict[Path, pd.DataFrame]:
    """Return per-child source frames with empty LSTM output columns."""
    frames: Dict[Path, pd.DataFrame] = {}
    for unit in units:
        df = pd.read_csv(unit.chi_csv, dtype=str, keep_default_na=False, low_memory=False)
        for variant in variants:
            df[variant.output_column] = ""
        if include_age_bin:
            df["lstm_age_bin"] = ""
        frames[unit.folder] = df
    return frames


def fill_generated_frames_for_examples(
    frames: Dict[Path, pd.DataFrame],
    examples: Sequence[LSTMExample],
    *,
    model,
    vocab: Vocabulary,
    base_config: LSTMConfig,
    variants: Sequence[LSTMVariant],
    age_bin_label: str,
) -> Dict[str, int]:
    """Generate LSTM text for selected examples and fill existing frames."""
    row_counts = {variant.output_column: 0 for variant in variants}
    for variant in variants:
        config = variant_config(base_config, variant)
        for example in examples:
            df = frames[example.unit.folder]
            generated_tokens = generate_tokens_with_lstm(model, vocab, example, config)
            generated = with_terminal_punctuation(generated_tokens, example.terminal_punct)
            df.at[example.row_index, variant.output_column] = generated
            df.at[example.row_index, "lstm_age_bin"] = age_bin_label
            if generated.strip():
                row_counts[variant.output_column] += 1
    return row_counts


def write_generated_frames(
    units: Sequence[ChildUnit],
    frames: Dict[Path, pd.DataFrame],
    variants: Sequence[LSTMVariant],
    *,
    output_filename: str,
) -> List[Dict[str, object]]:
    """Write accumulated generated frames and summarize per child."""
    summaries: List[Dict[str, object]] = []
    for unit in units:
        df = frames[unit.folder]
        out_path = unit.folder / output_filename
        df.to_csv(out_path, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")
        summary = {
            "dataset": unit.dataset,
            "child_id": unit.child,
            "source_rows": len(df),
            "generated_csv": str(out_path),
        }
        for variant in variants:
            summary[variant.output_column] = int(df[variant.output_column].astype(str).str.strip().ne("").sum())
        summaries.append(summary)
    return summaries


def merge_lstm_columns_into_context(
    context_df: pd.DataFrame,
    generated_df: pd.DataFrame,
    lstm_columns: Sequence[str],
    extra_columns: Sequence[str] = (),
) -> pd.DataFrame:
    """Left-join LSTM columns into child shared-context rows without changing row count."""
    join_keys = ["dataset", "child_id", "session_id", "file", "line_no", "utt_id"]
    left = context_df.copy()
    right = generated_df.copy()
    for df in (left, right):
        for key in join_keys:
            if key not in df.columns:
                df[key] = ""
            df[key] = df[key].fillna("").astype(str)
    keep_columns = [*join_keys, *extra_columns, *lstm_columns]
    for column in [*extra_columns, *lstm_columns]:
        if column not in right.columns:
            right[column] = ""
    merged = left.merge(right[keep_columns], on=join_keys, how="left", validate="one_to_one")
    for column in [*extra_columns, *lstm_columns]:
        merged[column] = merged[column].fillna("").astype(str)
    if len(merged) != len(context_df):
        raise RuntimeError("Merging LSTM columns changed the number of context rows.")
    return merged


def build_child_scoring_rows_with_lstm(
    context_df: pd.DataFrame,
    lstm_columns: Sequence[str],
    *,
    extra_columns: Sequence[str] = (),
    drop_empty: bool = True,
) -> List[Dict[str, str]]:
    """Build compact child scoring rows with extra LSTM generated utterance columns."""
    rows: List[Dict[str, str]] = []
    for _, source_row in context_df.iterrows():
        row = child_scoring_row(source_row)
        for column in extra_columns:
            row[column] = text_or_empty(source_row.get(column, ""))
        for column in lstm_columns:
            row[column] = text_or_empty(source_row.get(column, ""))
        if drop_empty and not any(text_or_empty(row[column]) for column in ["chi_utterance_clean", *lstm_columns]):
            continue
        rows.append(row)
    return rows


def write_lstm_context_and_scoring_files_for_unit(
    unit: ChildUnit,
    *,
    generated_filename: str,
    context_filename: str,
    context_output_filename: str,
    scoring_output_filename: str,
    lstm_columns: Sequence[str],
    extra_columns: Sequence[str] = (),
) -> Dict[str, object]:
    """Merge generated LSTM utterances into context and scoring sibling files."""
    context_path = unit.folder / context_filename
    generated_path = unit.folder / generated_filename
    if not context_path.exists():
        raise FileNotFoundError(f"Missing context file: {context_path}")
    if not generated_path.exists():
        raise FileNotFoundError(f"Missing generated LSTM file: {generated_path}")

    context_df = pd.read_csv(context_path, dtype=str, keep_default_na=False, low_memory=False)
    generated_df = pd.read_csv(generated_path, dtype=str, keep_default_na=False, low_memory=False)
    merged_df = merge_lstm_columns_into_context(context_df, generated_df, lstm_columns, extra_columns)

    context_out = unit.folder / context_output_filename
    merged_df.to_csv(context_out, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")

    scoring_rows = build_child_scoring_rows_with_lstm(merged_df, lstm_columns, extra_columns=extra_columns, drop_empty=True)
    scoring_out = unit.folder / scoring_output_filename
    write_rows(scoring_out, [*CHILD_OUTPUT_COLUMNS, *extra_columns, *lstm_columns], scoring_rows)
    return {
        "dataset": unit.dataset,
        "child_id": unit.child,
        "context_with_lstm_csv": str(context_out),
        "scoring_with_lstm_csv": str(scoring_out),
        "scoring_rows": len(scoring_rows),
    }


def write_pipeline_manifest(
    path: Path,
    units: Sequence[ChildUnit],
    generation_rows: Sequence[Dict[str, object]],
    scoring_rows: Sequence[Dict[str, object]],
    variants: Sequence[LSTMVariant],
) -> List[Dict[str, object]]:
    """Write one row per child folder summarizing generated LSTM outputs."""
    by_child_generation = {(row["dataset"], row["child_id"]): row for row in generation_rows}
    by_child_scoring = {(row["dataset"], row["child_id"]): row for row in scoring_rows}
    rows: List[Dict[str, object]] = []
    for unit in units:
        key = (unit.dataset, unit.child)
        generation = by_child_generation.get(key, {})
        scoring = by_child_scoring.get(key, {})
        rows.append(
            {
                "dataset": unit.dataset,
                "child_id": unit.child,
                "chi_csv": str(unit.chi_csv),
                "caretakers_csv": str(unit.caretakers_csv or ""),
                "generated_csv": generation.get("generated_csv", ""),
                "context_with_lstm_csv": scoring.get("context_with_lstm_csv", ""),
                "scoring_with_lstm_csv": scoring.get("scoring_with_lstm_csv", ""),
                "source_rows": generation.get("source_rows", ""),
                "same_length_rows": generation.get("lstm_same_length_utterance", "")
                if any(variant.name == "same_length" for variant in variants)
                else "",
                "free_length_rows": generation.get("lstm_free_length_utterance", "")
                if any(variant.name == "free_length" for variant in variants)
                else "",
                "scoring_rows": scoring.get("scoring_rows", ""),
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=UNIT_MANIFEST_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_dry_run_summary(
    output_dir: Path,
    *,
    config: LSTMConfig,
    units: Sequence[ChildUnit],
    examples_by_unit: Dict[Path, List[LSTMExample]],
    train_examples: Sequence[LSTMExample],
    variants: Sequence[LSTMVariant],
    age_binning: LSTMAgeBinning = LSTMAgeBinning(),
    additive_bin_runs: Sequence[AdditiveBinRun] = (),
) -> Path:
    """Write a JSON summary when validating inputs without training."""
    payload = {
        "dry_run": True,
        "config": {**asdict(config), "datasets": list(config.datasets)},
        "variants": [asdict(variant) for variant in variants],
        "age_binning": asdict(age_binning),
        "n_units": len(units),
        "n_examples_total": sum(len(examples) for examples in examples_by_unit.values()),
        "n_train_examples_after_limit": len(train_examples),
        "units": [
            {
                "dataset": unit.dataset,
                "child_id": unit.child,
                "examples": len(examples_by_unit.get(unit.folder, [])),
                "chi_csv": str(unit.chi_csv),
                "caretakers_csv": str(unit.caretakers_csv or ""),
            }
            for unit in units
        ],
    }
    if additive_bin_runs:
        payload["n_cumulative_train_example_uses_across_bins"] = sum(len(run.train_examples) for run in additive_bin_runs)
        payload["additive_age_bins"] = [
            {
                "label": run.age_bin.label,
                "start": run.age_bin.start,
                "end": run.age_bin.end,
                "train_examples": len(run.train_examples),
                "target_examples": len(run.target_examples),
            }
            for run in additive_bin_runs
        ]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "dry_run_summary.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_additive_bin_manifest(
    path: Path,
    rows: Sequence[Dict[str, object]],
) -> None:
    """Write one summary row per additive LSTM age-bin model."""
    base_fieldnames = [
        "age_bin",
        "start",
        "end",
        "train_examples",
        "train_examples_after_limit",
        "target_examples",
        "vocab_size",
        "model_dir",
        "training_summary_csv",
    ]
    extra_fieldnames = sorted({key for row in rows for key in row if key not in base_fieldnames})
    fieldnames = [*base_fieldnames, *extra_fieldnames]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_additive_age_binned_lstm(
    *,
    units: Sequence[ChildUnit],
    examples_by_unit: Dict[Path, List[LSTMExample]],
    all_examples: Sequence[LSTMExample],
    output_dir: Path,
    variants: Sequence[LSTMVariant],
    context_filename: str,
    generated_filename: str,
    context_output_filename: str,
    scoring_output_filename: str,
    dry_run: bool,
    base_config: LSTMConfig,
    age_binning: LSTMAgeBinning,
) -> Dict[str, object]:
    """Train/generate one cumulative LSTM per target age bin."""
    bins = resolve_lstm_age_bins(age_binning, base_config)
    bin_runs = build_additive_bin_runs(all_examples, bins)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "age_bins.json").write_text(
        json.dumps({"strategy": age_binning.strategy, "bins": age_bins_to_dicts(bins)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if dry_run:
        dry_path = write_dry_run_summary(
            output_dir,
            config=base_config,
            units=units,
            examples_by_unit=examples_by_unit,
            train_examples=all_examples,
            variants=variants,
            age_binning=age_binning,
            additive_bin_runs=bin_runs,
        )
        return {
            "dry_run": True,
            "age_binning_mode": age_binning.mode,
            "units": len(units),
            "examples_total": len(all_examples),
            "age_bins": len(bin_runs),
            "summary_path": str(dry_path),
        }

    frames = initialize_generated_frames(units, variants, include_age_bin=True)
    bin_manifest_rows: List[Dict[str, object]] = []

    for run in bin_runs:
        if not run.target_examples:
            continue
        train_examples = limit_examples(run.train_examples, base_config.max_train_examples, base_config.seed)
        if not train_examples:
            raise RuntimeError(f"No LSTM training examples available for additive bin {run.age_bin.label}.")

        bin_dir = output_dir / f"bin_{run.age_bin.label}"
        bin_dir.mkdir(parents=True, exist_ok=True)
        bin_config = replace(
            base_config,
            output_dir=str(bin_dir),
            min_age_months=float(bins[0].start),
            max_age_months=float(run.age_bin.end + 0.999),
        )
        save_config(bin_dir / "config.json", bin_config)
        vocab = Vocabulary.build(
            (example.context_tokens + example.child_tokens for example in train_examples),
            min_freq=bin_config.min_freq,
            max_vocab_size=bin_config.max_vocab_size,
        )
        save_vocab(bin_dir / "vocab.json", vocab)
        model, training_rows = train_lstm_model(train_examples, vocab, bin_config, bin_dir)
        training_summary_path = bin_dir / "training_summary.csv"
        write_summary_csv(training_summary_path, training_rows)

        row_counts = fill_generated_frames_for_examples(
            frames,
            run.target_examples,
            model=model,
            vocab=vocab,
            base_config=bin_config,
            variants=variants,
            age_bin_label=run.age_bin.label,
        )
        bin_manifest_rows.append(
            {
                "age_bin": run.age_bin.label,
                "start": run.age_bin.start,
                "end": run.age_bin.end,
                "train_examples": len(run.train_examples),
                "train_examples_after_limit": len(train_examples),
                "target_examples": len(run.target_examples),
                "vocab_size": len(vocab.id_to_token),
                "model_dir": str(bin_dir),
                "training_summary_csv": str(training_summary_path),
                **row_counts,
            }
        )

    write_additive_bin_manifest(output_dir / "lstm_age_bin_manifest.csv", bin_manifest_rows)
    generation_rows = write_generated_frames(units, frames, variants, output_filename=generated_filename)
    write_summary_csv(output_dir / "generation_summary.csv", generation_rows)

    lstm_columns = [variant.output_column for variant in variants]
    scoring_rows = [
        write_lstm_context_and_scoring_files_for_unit(
            unit,
            generated_filename=generated_filename,
            context_filename=context_filename,
            context_output_filename=context_output_filename,
            scoring_output_filename=scoring_output_filename,
            lstm_columns=lstm_columns,
            extra_columns=("lstm_age_bin",),
        )
        for unit in units
    ]
    manifest_rows = write_pipeline_manifest(output_dir / "lstm_pipeline_manifest.csv", units, generation_rows, scoring_rows, variants)
    return {
        "dry_run": False,
        "age_binning_mode": age_binning.mode,
        "units": len(units),
        "examples_total": len(all_examples),
        "age_bins": len(bin_manifest_rows),
        "manifest_rows": len(manifest_rows),
        "output_dir": str(output_dir),
    }


def run_lstm_baseline_pipeline(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    data_dir: Path = DEFAULT_DATA_DIR,
    datasets: Optional[Sequence[str]] = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    variants: Sequence[LSTMVariant] = (DEFAULT_VARIANTS["same_length"], DEFAULT_VARIANTS["free_length"]),
    context_filename: str = DEFAULT_CONTEXT_FILENAME,
    generated_filename: str = DEFAULT_GENERATED_FILENAME,
    context_output_filename: str = DEFAULT_CONTEXT_WITH_LSTM_FILENAME,
    scoring_output_filename: str = DEFAULT_SCORING_WITH_LSTM_FILENAME,
    dry_run: bool = False,
    config: Optional[LSTMConfig] = None,
    age_binning: LSTMAgeBinning = LSTMAgeBinning(),
) -> Dict[str, object]:
    """Run or dry-run the LSTM baseline pipeline."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    dataset_names = tuple(datasets) if datasets else tuple()
    units = discover_units_from_manifest(manifest_path, datasets=datasets)
    if not units:
        raise RuntimeError(f"No child units found in {manifest_path}")

    base_config = config or LSTMConfig(
        data_dir=str(data_dir),
        datasets=dataset_names or tuple(sorted({unit.dataset for unit in units})),
        output_dir=str(output_dir),
        output_filename=generated_filename,
        output_column="lstm_same_length_utterance",
        architecture="seq2seq_lstm",
        context_utterances=3,
        max_context_tokens=60,
        min_age_months=6.0,
        max_age_months=65.999,
        generation_length_mode="same_as_child",
    )

    set_seeds(base_config.seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_config(output_dir / "config.json", base_config)
    (output_dir / "variants.json").write_text(
        json.dumps([asdict(variant) for variant in variants], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    examples_by_unit, all_examples = build_examples_by_unit(units, base_config)
    if age_binning.mode == "additive_age_bins":
        return run_additive_age_binned_lstm(
            units=units,
            examples_by_unit=examples_by_unit,
            all_examples=all_examples,
            output_dir=output_dir,
            variants=variants,
            context_filename=context_filename,
            generated_filename=generated_filename,
            context_output_filename=context_output_filename,
            scoring_output_filename=scoring_output_filename,
            dry_run=dry_run,
            base_config=base_config,
            age_binning=age_binning,
        )

    train_examples = limit_examples(all_examples, base_config.max_train_examples, base_config.seed)
    if not train_examples:
        raise RuntimeError("No LSTM training examples available after filtering.")

    if dry_run:
        dry_path = write_dry_run_summary(
            output_dir,
            config=base_config,
            units=units,
            examples_by_unit=examples_by_unit,
            train_examples=train_examples,
            variants=variants,
            age_binning=age_binning,
        )
        return {
            "dry_run": True,
            "units": len(units),
            "examples_total": len(all_examples),
            "train_examples": len(train_examples),
            "summary_path": str(dry_path),
        }

    vocab = Vocabulary.build(
        (example.context_tokens + example.child_tokens for example in train_examples),
        min_freq=base_config.min_freq,
        max_vocab_size=base_config.max_vocab_size,
    )
    save_vocab(output_dir / "vocab.json", vocab)
    model, training_rows = train_lstm_model(train_examples, vocab, base_config, output_dir)
    write_summary_csv(output_dir / "training_summary.csv", training_rows)

    generation_rows = write_multi_variant_generated_files(
        units,
        examples_by_unit,
        model,
        vocab,
        base_config,
        variants,
        output_filename=generated_filename,
    )
    write_summary_csv(output_dir / "generation_summary.csv", generation_rows)

    lstm_columns = [variant.output_column for variant in variants]
    scoring_rows = [
        write_lstm_context_and_scoring_files_for_unit(
            unit,
            generated_filename=generated_filename,
            context_filename=context_filename,
            context_output_filename=context_output_filename,
            scoring_output_filename=scoring_output_filename,
            lstm_columns=lstm_columns,
        )
        for unit in units
    ]
    manifest_rows = write_pipeline_manifest(output_dir / "lstm_pipeline_manifest.csv", units, generation_rows, scoring_rows, variants)

    return {
        "dry_run": False,
        "units": len(units),
        "examples_total": len(all_examples),
        "train_examples": len(train_examples),
        "manifest_rows": len(manifest_rows),
        "output_dir": str(output_dir),
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Train/generate LSTM baseline utterances for a big-cleaned dataset.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "Optional JSON pipeline config. When provided, the config supplies "
            "paths, model hyperparameters, and generation variants; --dry_run can "
            "still be used to force a no-training validation run."
        ),
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--data_dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--datasets", nargs="*", default=None)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--variants", nargs="+", choices=sorted(DEFAULT_VARIANTS), default=["same_length", "free_length"])
    parser.add_argument("--dry_run", action="store_true", help="Validate inputs and write dry_run_summary.json without training.")
    parser.add_argument("--context_filename", default=DEFAULT_CONTEXT_FILENAME)
    parser.add_argument("--generated_filename", default=DEFAULT_GENERATED_FILENAME)
    parser.add_argument("--context_output_filename", default=DEFAULT_CONTEXT_WITH_LSTM_FILENAME)
    parser.add_argument("--scoring_output_filename", default=DEFAULT_SCORING_WITH_LSTM_FILENAME)
    parser.add_argument("--architecture", default="seq2seq_lstm", choices=["seq2seq_lstm", "causal_lstm"])
    parser.add_argument("--context_utterances", type=int, default=3)
    parser.add_argument("--max_context_tokens", type=int, default=60)
    parser.add_argument("--min_age_months", type=float, default=6.0)
    parser.add_argument("--max_age_months", type=float, default=65.999)
    parser.add_argument("--min_token_len", type=int, default=1)
    parser.add_argument("--max_train_examples", type=int, default=None)
    parser.add_argument("--max_generate_rows_per_child", type=int, default=None)
    parser.add_argument("--min_freq", type=int, default=1)
    parser.add_argument("--max_vocab_size", type=int, default=30000)
    parser.add_argument("--embedding_dim", type=int, default=128)
    parser.add_argument("--hidden_dim", type=int, default=256)
    parser.add_argument("--num_layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--grad_clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--no_lowercase", action="store_true")
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace, datasets: Tuple[str, ...]) -> LSTMConfig:
    """Build LSTMConfig from CLI options."""
    return LSTMConfig(
        data_dir=str(args.data_dir),
        datasets=datasets,
        output_dir=str(args.output_dir),
        output_filename=args.generated_filename,
        output_column="lstm_same_length_utterance",
        architecture=args.architecture,
        context_utterances=args.context_utterances,
        max_context_tokens=args.max_context_tokens,
        min_age_months=args.min_age_months,
        max_age_months=args.max_age_months,
        min_token_len=args.min_token_len,
        lowercase=not args.no_lowercase,
        max_train_examples=args.max_train_examples,
        max_generate_rows_per_child=args.max_generate_rows_per_child,
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
        generation_length_mode="same_as_child",
        device=args.device,
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entry point."""
    args = parse_args(argv)
    if args.config is not None:
        settings = load_pipeline_config(args.config)
        summary = run_lstm_baseline_pipeline(
            manifest_path=settings["manifest_path"],
            data_dir=settings["data_dir"],
            datasets=settings["datasets"],
            output_dir=settings["output_dir"],
            variants=settings["variants"],
            context_filename=settings["context_filename"],
            generated_filename=settings["generated_filename"],
            context_output_filename=settings["context_output_filename"],
            scoring_output_filename=settings["scoring_output_filename"],
            dry_run=bool(args.dry_run or settings["dry_run"]),
            config=settings["config"],
            age_binning=settings["age_binning"],
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    variants = normalize_variants(args.variants)
    units = discover_units_from_manifest(args.manifest, datasets=args.datasets)
    datasets = tuple(args.datasets) if args.datasets else tuple(sorted({unit.dataset for unit in units}))
    config = config_from_args(args, datasets)
    summary = run_lstm_baseline_pipeline(
        manifest_path=args.manifest,
        data_dir=args.data_dir,
        datasets=args.datasets,
        output_dir=args.output_dir,
        variants=variants,
        context_filename=args.context_filename,
        generated_filename=args.generated_filename,
        context_output_filename=args.context_output_filename,
        scoring_output_filename=args.scoring_output_filename,
        dry_run=args.dry_run,
        config=config,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
