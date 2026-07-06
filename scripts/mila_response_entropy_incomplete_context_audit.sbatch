#!/usr/bin/env bash
#SBATCH --job-name=respent_176_audit
#SBATCH --output=slurm/logs/respent_176_audit_%j.out
#SBATCH --error=slurm/logs/respent_176_audit_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --partition=long-cpu

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/mila/g/gouletn/compute_surprisal_mila}"
RUN_ROOT="${RUN_ROOT:-/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333}"
AUDIT_SEED="${AUDIT_SEED:-20260702}"
VALID_PER_INCOMPLETE="${VALID_PER_INCOMPLETE:-8}"
INVALID_PER_INCOMPLETE="${INVALID_PER_INCOMPLETE:-12}"
COMPLETE_CONTEXTS_SAMPLE="${COMPLETE_CONTEXTS_SAMPLE:-120}"
VALID_PER_COMPLETE="${VALID_PER_COMPLETE:-4}"
INVALID_PER_COMPLETE="${INVALID_PER_COMPLETE:-4}"
export RUN_ROOT AUDIT_SEED VALID_PER_INCOMPLETE INVALID_PER_INCOMPLETE COMPLETE_CONTEXTS_SAMPLE VALID_PER_COMPLETE INVALID_PER_COMPLETE

cd "$PROJECT_ROOT"

if command -v uv >/dev/null 2>&1; then
    PYTHON_CMD=(uv run python)
elif [[ -x .venv/bin/python ]]; then
    PYTHON_CMD=(.venv/bin/python)
else
    PYTHON_CMD=(python3)
fi

"${PYTHON_CMD[@]}" - <<'PY'
from __future__ import annotations

import os
import random
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(os.environ["RUN_ROOT"])
AUDIT_SEED = int(os.environ["AUDIT_SEED"])
VALID_PER_INCOMPLETE = int(os.environ["VALID_PER_INCOMPLETE"])
INVALID_PER_INCOMPLETE = int(os.environ["INVALID_PER_INCOMPLETE"])
COMPLETE_CONTEXTS_SAMPLE = int(os.environ["COMPLETE_CONTEXTS_SAMPLE"])
VALID_PER_COMPLETE = int(os.environ["VALID_PER_COMPLETE"])
INVALID_PER_COMPLETE = int(os.environ["INVALID_PER_COMPLETE"])

rng = random.Random(AUDIT_SEED)
out_dir = RUN_ROOT / "manual_review"
out_dir.mkdir(parents=True, exist_ok=True)

setting_summary_path = RUN_ROOT / "merged" / "setting_summary.csv.gz"
features_path = RUN_ROOT / "merged" / "context_response_entropy_features.csv.gz"
if not setting_summary_path.exists():
    raise FileNotFoundError(setting_summary_path)

summary = pd.read_csv(setting_summary_path, dtype=str, keep_default_na=False, low_memory=False)
features_cols = [
    "setting_id",
    "selected_sample_count",
    "valid_selected_count",
    "invalid_selected_count",
    "unique_response_count_valid_only",
    "empirical_response_entropy_bits_valid_only",
    "miller_madow_entropy_bits_valid_only",
    "top_response_text_selected",
    "top_response_probability_selected",
    "mean_sample_words_selected",
]
features = pd.read_csv(
    features_path,
    usecols=lambda col: col in set(features_cols),
    dtype=str,
    keep_default_na=False,
    low_memory=False,
) if features_path.exists() else pd.DataFrame(columns=features_cols)

summary["accepted_valid_samples_num"] = pd.to_numeric(summary["accepted_valid_samples"], errors="coerce").fillna(0).astype(int)
summary["target_valid_samples_num"] = pd.to_numeric(summary["target_valid_samples"], errors="coerce").fillna(0).astype(int)
summary["missing_valid_samples"] = (
    summary["target_valid_samples_num"] - summary["accepted_valid_samples_num"]
).clip(lower=0)
summary["is_incomplete"] = summary["reached_target_valid_samples"].astype(str).str.lower().ne("true")

incomplete = summary[summary["is_incomplete"]].copy()
complete = summary[~summary["is_incomplete"]].copy()

if not features.empty:
    incomplete = incomplete.merge(features, on="setting_id", how="left", validate="one_to_one")

summary_cols = [
    "setting_id",
    "shard_index",
    "context_id",
    "context_text",
    "context_word_count",
    "context_k_values",
    "prompt_variant",
    "temperature",
    "attempts",
    "accepted_valid_samples",
    "target_valid_samples",
    "missing_valid_samples",
    "invalid_attempts",
    "selected_samples",
    "invalid_fallback_selected",
    "reached_target_valid_samples",
    "exhausted_attempt_cap",
    "fallback_used",
    "rejection_rate",
    "empty_response_count",
    "no_boundary_before_cap_count",
    "repetition_loop_count",
    "metadata_or_prose_drift_count",
    "malformed_response_count",
    "speaker_label_inside_response_count",
    "other_quality_flag_count",
    "valid_selected_count",
    "invalid_selected_count",
    "unique_response_count_valid_only",
    "empirical_response_entropy_bits_valid_only",
    "miller_madow_entropy_bits_valid_only",
    "top_response_text_selected",
    "top_response_probability_selected",
    "mean_sample_words_selected",
]

for col in summary_cols:
    if col not in incomplete.columns:
        incomplete[col] = ""

incomplete_summary = incomplete[summary_cols].sort_values(
    ["missing_valid_samples", "attempts", "setting_id"],
    ascending=[False, False, True],
)

review_cols = [
    "setting_id",
    "shard_index",
    "context_id",
    "context_text",
    "prompt_variant",
    "temperature",
    "attempt_index",
    "accepted",
    "selected_kind",
    "rejection_reason",
    "quality_flags",
    "sampled_response_text",
    "raw_generated_text",
    "stopped_by_end_of_turn",
    "end_of_turn_marker",
    "hit_max_new_tokens",
    "generated_token_count",
    "empty_first_line_response",
    "speaker_label_inside_response",
    "metadata_or_prose_start",
    "repetition_loop",
    "no_end_of_turn_boundary_before_cap",
    "possible_context_copy",
    "very_long_first_line_response",
    "malformed_response",
]


def keep_cols(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in review_cols:
        if col not in out.columns:
            out[col] = ""
    return out[review_cols]


def sample_group(group: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if len(group) <= n:
        return group
    return group.sample(n=n, random_state=seed)


def concat_or_empty(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=review_cols)
    return pd.concat(frames, ignore_index=True)


def selected_path(shard_index: int) -> Path:
    return RUN_ROOT / "shard_outputs" / f"shard_{shard_index:05d}" / "selected_samples.csv.gz"


def attempts_path(shard_index: int) -> Path:
    return RUN_ROOT / "shard_outputs" / f"shard_{shard_index:05d}" / "all_attempts.csv.gz"


incomplete_ids = set(incomplete["setting_id"].astype(str))
incomplete_shards = sorted(set(pd.to_numeric(incomplete["shard_index"], errors="coerce").dropna().astype(int)))

incomplete_valid_frames: list[pd.DataFrame] = []
incomplete_invalid_selected_frames: list[pd.DataFrame] = []
incomplete_invalid_attempt_frames: list[pd.DataFrame] = []

for shard_index in incomplete_shards:
    spath = selected_path(shard_index)
    if spath.exists():
        selected = pd.read_csv(spath, dtype=str, keep_default_na=False, low_memory=False)
        selected = selected[selected["setting_id"].astype(str).isin(incomplete_ids)]
        valid = selected[selected["accepted"].astype(str).eq("1")]
        invalid_selected = selected[selected["accepted"].astype(str).ne("1")]
        if not valid.empty:
            for offset, (_, group) in enumerate(valid.groupby("setting_id", sort=False)):
                incomplete_valid_frames.append(
                    keep_cols(sample_group(group, VALID_PER_INCOMPLETE, AUDIT_SEED + shard_index + offset))
                )
        if not invalid_selected.empty:
            for offset, (_, group) in enumerate(invalid_selected.groupby("setting_id", sort=False)):
                incomplete_invalid_selected_frames.append(
                    keep_cols(sample_group(group, INVALID_PER_INCOMPLETE, AUDIT_SEED + 10_000 + shard_index + offset))
                )

    apath = attempts_path(shard_index)
    if apath.exists():
        by_setting: dict[str, list[pd.DataFrame]] = {}
        for chunk in pd.read_csv(apath, dtype=str, keep_default_na=False, chunksize=100000, low_memory=False):
            rejected = chunk[
                chunk["setting_id"].astype(str).isin(incomplete_ids)
                & chunk["accepted"].astype(str).ne("1")
            ]
            if rejected.empty:
                continue
            for setting_id, group in rejected.groupby("setting_id", sort=False):
                by_setting.setdefault(str(setting_id), []).append(
                    keep_cols(sample_group(group, min(4, len(group)), AUDIT_SEED + rng.randint(0, 10**9)))
                )
        for offset, (setting_id, frames) in enumerate(sorted(by_setting.items())):
            combined = pd.concat(frames, ignore_index=True)
            incomplete_invalid_attempt_frames.append(
                keep_cols(sample_group(combined, INVALID_PER_INCOMPLETE, AUDIT_SEED + 20_000 + offset))
            )

complete_sample = complete.sample(
    n=min(COMPLETE_CONTEXTS_SAMPLE, len(complete)),
    random_state=AUDIT_SEED,
) if not complete.empty else complete.copy()
complete_ids = set(complete_sample["setting_id"].astype(str))
complete_shards = sorted(set(pd.to_numeric(complete_sample["shard_index"], errors="coerce").dropna().astype(int)))

complete_valid_frames: list[pd.DataFrame] = []
complete_invalid_attempt_frames: list[pd.DataFrame] = []

for shard_index in complete_shards:
    spath = selected_path(shard_index)
    if spath.exists():
        selected = pd.read_csv(spath, dtype=str, keep_default_na=False, low_memory=False)
        selected = selected[
            selected["setting_id"].astype(str).isin(complete_ids)
            & selected["accepted"].astype(str).eq("1")
        ]
        if not selected.empty:
            for offset, (_, group) in enumerate(selected.groupby("setting_id", sort=False)):
                complete_valid_frames.append(
                    keep_cols(sample_group(group, VALID_PER_COMPLETE, AUDIT_SEED + 30_000 + shard_index + offset))
                )

    apath = attempts_path(shard_index)
    if apath.exists():
        by_setting: dict[str, list[pd.DataFrame]] = {}
        for chunk in pd.read_csv(apath, dtype=str, keep_default_na=False, chunksize=100000, low_memory=False):
            rejected = chunk[
                chunk["setting_id"].astype(str).isin(complete_ids)
                & chunk["accepted"].astype(str).ne("1")
            ]
            if rejected.empty:
                continue
            for setting_id, group in rejected.groupby("setting_id", sort=False):
                by_setting.setdefault(str(setting_id), []).append(
                    keep_cols(sample_group(group, min(2, len(group)), AUDIT_SEED + rng.randint(0, 10**9)))
                )
        for offset, (_, frames) in enumerate(sorted(by_setting.items())):
            combined = pd.concat(frames, ignore_index=True)
            complete_invalid_attempt_frames.append(
                keep_cols(sample_group(combined, INVALID_PER_COMPLETE, AUDIT_SEED + 40_000 + offset))
            )

paths = {
    "incomplete_summary": out_dir / "incomplete_176_setting_summary.csv",
    "incomplete_valid": out_dir / "incomplete_176_valid_samples_review.csv",
    "incomplete_invalid_selected": out_dir / "incomplete_176_invalid_selected_fallback_review.csv",
    "incomplete_invalid_attempts": out_dir / "incomplete_176_invalid_attempts_review.csv",
    "complete_context_sample": out_dir / "complete_contexts_comparison_setting_sample.csv",
    "complete_valid": out_dir / "complete_contexts_valid_samples_review.csv",
    "complete_invalid_attempts": out_dir / "complete_contexts_invalid_attempts_review.csv",
    "summary": out_dir / "incomplete_176_audit_summary.txt",
}

incomplete_summary.to_csv(paths["incomplete_summary"], index=False)
incomplete_valid = concat_or_empty(incomplete_valid_frames)
incomplete_invalid_selected = concat_or_empty(incomplete_invalid_selected_frames)
incomplete_invalid_attempts = concat_or_empty(incomplete_invalid_attempt_frames)
complete_valid = concat_or_empty(complete_valid_frames)
complete_invalid_attempts = concat_or_empty(complete_invalid_attempt_frames)

incomplete_valid.to_csv(paths["incomplete_valid"], index=False)
incomplete_invalid_selected.to_csv(paths["incomplete_invalid_selected"], index=False)
incomplete_invalid_attempts.to_csv(paths["incomplete_invalid_attempts"], index=False)
complete_sample.to_csv(paths["complete_context_sample"], index=False)
complete_valid.to_csv(paths["complete_valid"], index=False)
complete_invalid_attempts.to_csv(paths["complete_invalid_attempts"], index=False)

with paths["summary"].open("w", encoding="utf-8") as handle:
    handle.write("Incomplete response-entropy context audit\n")
    handle.write(f"run_root={RUN_ROOT}\n")
    handle.write(f"incomplete_contexts={len(incomplete):,}\n")
    handle.write(f"complete_contexts={len(complete):,}\n")
    handle.write(f"missing_valid_min={int(incomplete['missing_valid_samples'].min()) if len(incomplete) else 0}\n")
    handle.write(f"missing_valid_median={float(incomplete['missing_valid_samples'].median()) if len(incomplete) else 0:.1f}\n")
    handle.write(f"missing_valid_max={int(incomplete['missing_valid_samples'].max()) if len(incomplete) else 0}\n")
    handle.write(f"incomplete_valid_review_rows={len(incomplete_valid):,}\n")
    handle.write(f"incomplete_invalid_selected_review_rows={len(incomplete_invalid_selected):,}\n")
    handle.write(f"incomplete_invalid_attempt_review_rows={len(incomplete_invalid_attempts):,}\n")
    handle.write(f"complete_context_sample_rows={len(complete_sample):,}\n")
    handle.write(f"complete_valid_review_rows={len(complete_valid):,}\n")
    handle.write(f"complete_invalid_attempt_review_rows={len(complete_invalid_attempts):,}\n")
    handle.write("\nMissing valid samples distribution:\n")
    handle.write(incomplete["missing_valid_samples"].value_counts().sort_index().to_string())
    handle.write("\n\nIncomplete invalid attempt reasons in review:\n")
    if incomplete_invalid_attempts.empty:
        handle.write("(none)\n")
    else:
        handle.write(incomplete_invalid_attempts["rejection_reason"].value_counts(dropna=False).to_string())
        handle.write("\n")

print("===== INCOMPLETE RESPONSE ENTROPY CONTEXT AUDIT =====")
print(f"run_root={RUN_ROOT}")
print(f"incomplete_contexts={len(incomplete):,}")
print(f"complete_contexts={len(complete):,}")
print(f"missing_valid_min={int(incomplete['missing_valid_samples'].min()) if len(incomplete) else 0}")
print(f"missing_valid_median={float(incomplete['missing_valid_samples'].median()) if len(incomplete) else 0:.1f}")
print(f"missing_valid_max={int(incomplete['missing_valid_samples'].max()) if len(incomplete) else 0}")
print()
print("files:")
for path in paths.values():
    print(path)
print()
print("row_counts:")
print(f"incomplete_valid_review_rows={len(incomplete_valid):,}")
print(f"incomplete_invalid_selected_review_rows={len(incomplete_invalid_selected):,}")
print(f"incomplete_invalid_attempt_review_rows={len(incomplete_invalid_attempts):,}")
print(f"complete_context_sample_rows={len(complete_sample):,}")
print(f"complete_valid_review_rows={len(complete_valid):,}")
print(f"complete_invalid_attempt_review_rows={len(complete_invalid_attempts):,}")
print()
print("missing_valid_samples_distribution:")
print(incomplete["missing_valid_samples"].value_counts().sort_index().to_string())
print()
print("worst_20_incomplete_contexts:")
print(
    incomplete_summary[
        ["missing_valid_samples", "accepted_valid_samples", "attempts", "rejection_rate", "context_text"]
    ].head(20).to_string(index=False)
)
PY
