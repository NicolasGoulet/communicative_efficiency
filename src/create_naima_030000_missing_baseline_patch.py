#!/usr/bin/env python3
"""Create a scorer patch for Providence/Naima 030000 missing baselines.

The main cleaned Mistral tree contains real child scores for
``Providence/Naima/030000.cha`` but blank generated-baseline text/scores for
random, unigram, bigram, and trigram.  The blank baseline text came from a
missing ``age_months`` value in the old scorer input.  This script recovers the
age from the CHAT filename (``030000`` -> 36.0 months), generates same-length
baseline utterances from the current additive ``036-041`` dictionaries, and
writes a small cleaned-data-style patch tree for local Mistral scoring.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import sys
import tarfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:  # pragma: no cover - exercised by CLI execution
    from add_random_and_unigram_utterances import (
        BigramSampler,
        TrigramSampler,
        UniformSampler,
        WeightedSampler,
        _ALLOWED_AT_TAGS_DEFAULT,
        load_bigram_probs,
        load_trigram_probs,
        load_unigram_counts,
        load_vocab,
        terminal_punctuation,
        with_terminal_punctuation,
    )
    from build_route1_report_assets import resolve_age_months
    from custom_age_bins import AgeBin, find_age_bin, load_age_bins_config
    from utterance_count_strategies import word_tokens_regex
except ImportError:  # pragma: no cover - exercised by unit-test package imports
    from .add_random_and_unigram_utterances import (
        BigramSampler,
        TrigramSampler,
        UniformSampler,
        WeightedSampler,
        _ALLOWED_AT_TAGS_DEFAULT,
        load_bigram_probs,
        load_trigram_probs,
        load_unigram_counts,
        load_vocab,
        terminal_punctuation,
        with_terminal_punctuation,
    )
    from .build_route1_report_assets import resolve_age_months
    from .custom_age_bins import AgeBin, find_age_bin, load_age_bins_config
    from .utterance_count_strategies import word_tokens_regex


DEFAULT_SCORED_REAL_K0 = Path(
    "results/external/compute_surprisal_mila/"
    "raw_surprisal_cleaned_mistral_patched_006_023/"
    "WITHOUT_context/k0/mistralai__Mistral-7B-v0.3/"
    "Providence/Naima/chi.surprisal_scoring__real.scored.csv"
)
DEFAULT_DICT_ROOT = Path(
    "data/big_cleaned_dataset/default_naturalistic_merged_006_023/"
    "age_ngram_dicts/merged_early_006_023"
)
DEFAULT_OUTPUT_ROOT = Path(
    "results/scoring_patches/cleaned_data_patches/"
    "naima_030000_missing_baselines"
)
DEFAULT_TARBALL = Path(
    "results/scoring_bundles/"
    "naima_030000_missing_baselines_scoring_patch_2026-06-03.tar.gz"
)

PATCH_FILE = "Naima/030000.cha"
PATCH_DATASET = "Providence"
PATCH_CHILD = "Naima"
SOURCE_FILENAME = "chi.surprisal_scoring.csv"
BASELINE_COLUMNS = (
    "random_model_utterance_bin6",
    "unigram_model_utterance_bin6",
    "bigram_model_utterance_bin6",
    "trigram_model_utterance_bin6",
)
OUTPUT_COLUMNS = (
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "chi_utterance_clean",
    *BASELINE_COLUMNS,
)
KEY_COLUMNS = ("dataset", "child_id", "file", "line_no", "utt_id")


@dataclass(frozen=True)
class PatchSummary:
    """Metadata written next to the scorer patch."""

    created_at: str
    source_scored_real_k0: str
    dictionary_root: str
    dictionary_age_bin: str
    output_csv: str
    rows_written: int
    missing_source_age_rows: int
    generated_columns: tuple[str, ...]


def word_tokens_lower(text: object) -> list[str]:
    """Return lowercased word tokens used for generation length/context."""

    return [token.lower() for token in word_tokens_regex(text)]


def age_bin_for_row(row: Mapping[str, object], bins: Sequence[AgeBin]) -> tuple[float, str]:
    """Resolve the row age and map it to a configured additive age bin."""

    age_months, source = resolve_age_months(row.get("age_months", ""), row.get("file", ""))
    if age_months is None:
        raise ValueError(f"Could not resolve age for row file={row.get('file')} line_no={row.get('line_no')}")
    age_bin = find_age_bin(float(age_months), bins)
    if age_bin is None:
        raise ValueError(f"Resolved age {age_months} from {source} is outside configured bins.")
    return float(age_months), age_bin.label


def load_samplers(dict_root: Path, label: str) -> tuple[UniformSampler, WeightedSampler, BigramSampler, TrigramSampler]:
    """Load random/unigram/bigram/trigram samplers for one age-bin label."""

    allowed = set(_ALLOWED_AT_TAGS_DEFAULT)
    vocab = load_vocab(
        dict_root,
        label,
        allowed_at_tags=allowed,
        drop_chat_markers=True,
        drop_angle_artifacts=True,
    )
    unigram_counts = load_unigram_counts(
        dict_root,
        label,
        allowed_at_tags=allowed,
        drop_chat_markers=True,
        drop_angle_artifacts=True,
    )
    unigram = WeightedSampler(unigram_counts)
    bigram = BigramSampler(load_bigram_probs(dict_root, label), unigram)
    trigram = TrigramSampler(load_trigram_probs(dict_root, label), bigram, unigram)
    return UniformSampler(vocab), unigram, bigram, trigram


def generate_baselines_for_row(
    row: Mapping[str, object],
    *,
    rng: random.Random,
    samplers: tuple[UniformSampler, WeightedSampler, BigramSampler, TrigramSampler],
) -> dict[str, str]:
    """Generate all four same-word-count baseline utterances for one row."""

    target = row.get("chi_utterance_clean", "")
    n_tokens = len(word_tokens_regex(target))
    if n_tokens <= 0:
        raise ValueError(f"Patch row is not scorable: line_no={row.get('line_no')} utt_id={row.get('utt_id')}")

    punct = terminal_punctuation(target)
    previous_caretaker_tokens = word_tokens_lower(row.get("context_k1", ""))
    uniform, unigram, bigram, trigram = samplers
    return {
        "random_model_utterance_bin6": with_terminal_punctuation(uniform.sample_n(rng, n_tokens), punct),
        "unigram_model_utterance_bin6": with_terminal_punctuation(unigram.sample_n(rng, n_tokens), punct),
        "bigram_model_utterance_bin6": with_terminal_punctuation(
            bigram.sample_sequence(rng, n_tokens, previous_caretaker_tokens),
            punct,
        ),
        "trigram_model_utterance_bin6": with_terminal_punctuation(
            trigram.sample_sequence(rng, n_tokens, previous_caretaker_tokens),
            punct,
        ),
    }


def select_patch_rows(scored_real_k0: Path, target_file: str = PATCH_FILE) -> pd.DataFrame:
    """Read the scored real-child file and select the missing-baseline session."""

    df = pd.read_csv(scored_real_k0, dtype=str, keep_default_na=False, low_memory=False)
    missing = [column for column in OUTPUT_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{scored_real_k0} is missing required columns: {missing}")

    rows = df[df["file"].eq(target_file)].copy()
    rows = rows[rows["chi_utterance_clean"].astype(str).str.strip().ne("")].copy()
    if rows.empty:
        raise ValueError(f"No scorable rows found for {target_file} in {scored_real_k0}")
    duplicated = rows.duplicated(list(KEY_COLUMNS)).sum()
    if duplicated:
        raise ValueError(f"Duplicate patch keys found for {target_file}: {duplicated}")
    return rows


def build_patch_dataframe(
    *,
    scored_real_k0: Path,
    dict_root: Path,
    target_file: str = PATCH_FILE,
    seed: int = 123,
) -> tuple[pd.DataFrame, str, int]:
    """Return a 477-row cleaned-data-style scorer input with generated baselines."""

    bins = load_age_bins_config(dict_root / "age_bins.json")
    if not bins:
        raise ValueError(f"Dictionary root has no custom age_bins.json: {dict_root}")

    rows = select_patch_rows(scored_real_k0, target_file=target_file)
    first_age, label = age_bin_for_row(rows.iloc[0].to_dict(), bins)
    samplers = load_samplers(dict_root, label)
    rng = random.Random(seed)

    out_rows: list[dict[str, object]] = []
    missing_source_age_rows = 0
    for _, row_series in rows.iterrows():
        row = row_series.to_dict()
        age_months, row_label = age_bin_for_row(row, bins)
        if row_label != label:
            raise ValueError(f"Patch rows span multiple age bins: {label} and {row_label}")
        if not str(row.get("age_months", "")).strip():
            missing_source_age_rows += 1

        output_row = {column: row.get(column, "") for column in OUTPUT_COLUMNS}
        output_row["age_months"] = f"{age_months:.3f}".rstrip("0").rstrip(".")
        output_row.update(generate_baselines_for_row(row, rng=rng, samplers=samplers))
        out_rows.append(output_row)

    output = pd.DataFrame(out_rows, columns=list(OUTPUT_COLUMNS))
    if output.empty:
        raise ValueError("Patch generation produced no rows.")
    if output[list(BASELINE_COLUMNS)].fillna("").astype(str).apply(lambda s: s.str.strip().eq("")).any().any():
        raise ValueError("Patch generation produced blank baseline utterances.")
    if first_age != 36.0:
        raise ValueError(f"Expected filename fallback age 36.0 months, got {first_age}")
    return output, label, missing_source_age_rows


def safe_rmtree(path: Path) -> None:
    """Remove a generated output directory after a conservative path check."""

    resolved = path.resolve()
    if resolved == Path("/") or len(resolved.parts) < 5:
        raise ValueError(f"Refusing to remove suspiciously broad path: {resolved}")
    shutil.rmtree(resolved)


def write_patch(
    *,
    output_root: Path,
    scored_real_k0: Path,
    dict_root: Path,
    seed: int,
    overwrite: bool,
) -> PatchSummary:
    """Write patch CSV, manifest, and README."""

    if output_root.exists():
        if not overwrite:
            raise FileExistsError(f"Output root exists: {output_root}. Use --overwrite.")
        safe_rmtree(output_root)

    df, age_bin_label, missing_source_age_rows = build_patch_dataframe(
        scored_real_k0=scored_real_k0,
        dict_root=dict_root,
        seed=seed,
    )

    output_csv = output_root / "data" / "preprocessed_data" / PATCH_DATASET / PATCH_CHILD / SOURCE_FILENAME
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")

    summary = PatchSummary(
        created_at=datetime.now().isoformat(timespec="seconds"),
        source_scored_real_k0=str(scored_real_k0),
        dictionary_root=str(dict_root),
        dictionary_age_bin=age_bin_label,
        output_csv=str(output_csv),
        rows_written=len(df),
        missing_source_age_rows=missing_source_age_rows,
        generated_columns=BASELINE_COLUMNS,
    )

    manifest = output_root / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(summary)), lineterminator="\n")
        writer.writeheader()
        writer.writerow(asdict(summary))

    readme = output_root / "README.md"
    readme.write_text(
        "# Naima 030000 Missing Generated-Baseline Patch\n\n"
        "This patch contains exactly the scorable child rows from "
        "`Providence/Naima/030000.cha` whose generated-baseline text/scores were "
        "blank in the cleaned Mistral scored tree. The age is recovered from the "
        "CHAT filename (`030000` -> 36.0 months), so generated baselines use the "
        "current additive `036-041` n-gram dictionaries.\n\n"
        f"```json\n{json.dumps(asdict(summary), indent=2, sort_keys=True)}\n```\n",
        encoding="utf-8",
    )
    return summary


def create_tarball(output_root: Path, tarball: Path) -> None:
    """Create a handoff tarball that extracts under cleaned_data_patches/."""

    tarball.parent.mkdir(parents=True, exist_ok=True)
    arcname = Path("cleaned_data_patches") / output_root.name
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(output_root, arcname=arcname)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored-real-k0", type=Path, default=DEFAULT_SCORED_REAL_K0)
    parser.add_argument("--dict-root", type=Path, default=DEFAULT_DICT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--tarball", type=Path, default=DEFAULT_TARBALL)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-tarball", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    scored_real_k0 = args.scored_real_k0.expanduser().resolve()
    dict_root = args.dict_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    tarball = args.tarball.expanduser().resolve()

    if not scored_real_k0.is_file():
        raise SystemExit(f"ERROR: scored real k0 file not found: {scored_real_k0}")
    if not dict_root.is_dir():
        raise SystemExit(f"ERROR: dictionary root not found: {dict_root}")

    summary = write_patch(
        output_root=output_root,
        scored_real_k0=scored_real_k0,
        dict_root=dict_root,
        seed=args.seed,
        overwrite=bool(args.overwrite),
    )
    print(f"[OK] Wrote {summary.rows_written} rows to {summary.output_csv}")
    print(f"[OK] Generated baseline dictionary bin: {summary.dictionary_age_bin}")

    if not args.no_tarball:
        create_tarball(output_root, tarball)
        print(f"[OK] Wrote tarball: {tarball}")


if __name__ == "__main__":
    main()
