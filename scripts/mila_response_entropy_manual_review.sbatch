#!/usr/bin/env bash
#SBATCH --job-name=respent_review
#SBATCH --output=slurm/logs/respent_review_%j.out
#SBATCH --error=slurm/logs/respent_review_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --partition=long-cpu

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/mila/g/gouletn/compute_surprisal_mila}"
RUN_ROOT="${RUN_ROOT:-/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333}"
REVIEW_SHARDS="${REVIEW_SHARDS:-64}"
MAX_ACCEPTED_ROWS="${MAX_ACCEPTED_ROWS:-160}"
MAX_REJECTED_PER_REASON="${MAX_REJECTED_PER_REASON:-60}"
MAX_FALLBACK_ROWS="${MAX_FALLBACK_ROWS:-500}"
REVIEW_SEED="${REVIEW_SEED:-20260702}"

cd "$PROJECT_ROOT"

python3 - <<'PY'
from __future__ import annotations

import os
import random
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(os.environ["RUN_ROOT"])
REVIEW_SHARDS = int(os.environ["REVIEW_SHARDS"])
MAX_ACCEPTED_ROWS = int(os.environ["MAX_ACCEPTED_ROWS"])
MAX_REJECTED_PER_REASON = int(os.environ["MAX_REJECTED_PER_REASON"])
MAX_FALLBACK_ROWS = int(os.environ["MAX_FALLBACK_ROWS"])
REVIEW_SEED = int(os.environ["REVIEW_SEED"])

OUT = RUN_ROOT / "manual_review"
OUT.mkdir(parents=True, exist_ok=True)

rng = random.Random(REVIEW_SEED)
shard_dirs = sorted((RUN_ROOT / "shard_outputs").glob("shard_*"))
if not shard_dirs:
    raise SystemExit(f"no shard output directories found under {RUN_ROOT / 'shard_outputs'}")

sampled_shards = sorted(rng.sample(shard_dirs, min(REVIEW_SHARDS, len(shard_dirs))))

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
    for column in review_cols:
        if column not in out.columns:
            out[column] = ""
    return out[review_cols]


def sample_frame(frame: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if frame.empty or len(frame) <= n:
        return frame
    return frame.sample(n=n, random_state=seed)


def concat_or_empty(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=review_cols)
    return pd.concat(frames, ignore_index=True)


accepted_frames: list[pd.DataFrame] = []
rejected_by_reason: dict[str, list[pd.DataFrame]] = {}

for shard in sampled_shards:
    selected_path = shard / "selected_samples.csv.gz"
    if selected_path.exists():
        selected = pd.read_csv(selected_path, dtype=str, keep_default_na=False, low_memory=False)
        accepted = selected[selected["accepted"].astype(str).eq("1")]
        if not accepted.empty:
            accepted_frames.append(
                keep_cols(accepted.sample(min(5, len(accepted)), random_state=rng.randint(0, 10**9)))
            )

    attempts_path = shard / "all_attempts.csv.gz"
    if attempts_path.exists():
        for chunk in pd.read_csv(
            attempts_path,
            dtype=str,
            keep_default_na=False,
            chunksize=100000,
            low_memory=False,
        ):
            rejected = chunk[chunk["accepted"].astype(str).ne("1")]
            if rejected.empty:
                continue
            for reason, group in rejected.groupby("rejection_reason", dropna=False):
                reason_key = str(reason or "<blank>")
                rejected_by_reason.setdefault(reason_key, []).append(
                    keep_cols(group.sample(min(3, len(group)), random_state=rng.randint(0, 10**9)))
                )


accepted_review = sample_frame(concat_or_empty(accepted_frames), MAX_ACCEPTED_ROWS, REVIEW_SEED + 1)

reason_reviews: list[pd.DataFrame] = []
for index, (reason, frames) in enumerate(sorted(rejected_by_reason.items())):
    combined = concat_or_empty(frames)
    reason_reviews.append(sample_frame(combined, MAX_REJECTED_PER_REASON, REVIEW_SEED + 100 + index))
rejected_review = concat_or_empty(reason_reviews)

setting_summary_path = RUN_ROOT / "merged" / "setting_summary.csv.gz"
fallback_review = pd.DataFrame(columns=review_cols)
fallback_setting_count = 0
fallback_selected_rows_total = 0
if setting_summary_path.exists():
    setting_summary = pd.read_csv(setting_summary_path, dtype=str, keep_default_na=False, low_memory=False)
    fallback_summary = setting_summary[setting_summary["fallback_used"].astype(str).str.lower().eq("true")]
    fallback_setting_count = len(fallback_summary)
    fallback_ids = set(fallback_summary["setting_id"].astype(str))
    fallback_shards = sorted(set(pd.to_numeric(fallback_summary["shard_index"], errors="coerce").dropna().astype(int)))
    fallback_frames: list[pd.DataFrame] = []
    for shard_index in fallback_shards:
        path = RUN_ROOT / "shard_outputs" / f"shard_{shard_index:05d}" / "selected_samples.csv.gz"
        if not path.exists():
            continue
        selected = pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)
        fallback = selected[
            selected["setting_id"].astype(str).isin(fallback_ids)
            & selected["accepted"].astype(str).ne("1")
        ]
        if not fallback.empty:
            fallback_frames.append(keep_cols(fallback))
    fallback_all = concat_or_empty(fallback_frames)
    fallback_selected_rows_total = len(fallback_all)
    fallback_review = sample_frame(fallback_all, MAX_FALLBACK_ROWS, REVIEW_SEED + 2)


accepted_path = OUT / "accepted_selected_review.csv"
rejected_path = OUT / "rejected_attempts_by_reason_review.csv"
fallback_path = OUT / "invalid_fallback_selected_review.csv"
summary_path = OUT / "manual_review_summary.txt"

accepted_review.to_csv(accepted_path, index=False)
rejected_review.to_csv(rejected_path, index=False)
fallback_review.to_csv(fallback_path, index=False)

with summary_path.open("w", encoding="utf-8") as handle:
    handle.write("Response-entropy manual review extract\n")
    handle.write(f"run_root={RUN_ROOT}\n")
    handle.write(f"sampled_shards={len(sampled_shards)} / {len(shard_dirs)}\n")
    handle.write(f"accepted_review_rows={len(accepted_review)}\n")
    handle.write(f"rejected_review_rows={len(rejected_review)}\n")
    handle.write(f"fallback_settings_total={fallback_setting_count}\n")
    handle.write(f"fallback_invalid_selected_rows_total={fallback_selected_rows_total}\n")
    handle.write(f"fallback_review_rows={len(fallback_review)}\n")
    handle.write("\nRejected reasons in review:\n")
    if rejected_review.empty:
        handle.write("(none)\n")
    else:
        handle.write(rejected_review["rejection_reason"].value_counts(dropna=False).to_string())
        handle.write("\n")

print("===== RESPONSE ENTROPY MANUAL REVIEW EXTRACT =====")
print(f"run_root={RUN_ROOT}")
print(f"sampled_shards={len(sampled_shards)} / {len(shard_dirs)}")
print()
print("files:")
print(accepted_path)
print(rejected_path)
print(fallback_path)
print(summary_path)
print()
print("row_counts:")
print(f"accepted_review_rows={len(accepted_review)}")
print(f"rejected_review_rows={len(rejected_review)}")
print(f"fallback_settings_total={fallback_setting_count}")
print(f"fallback_invalid_selected_rows_total={fallback_selected_rows_total}")
print(f"fallback_review_rows={len(fallback_review)}")
print()
print("rejected_reasons_in_review:")
if rejected_review.empty:
    print("(none)")
else:
    print(rejected_review["rejection_reason"].value_counts(dropna=False).to_string())
print()
print("accepted_preview:")
if accepted_review.empty:
    print("(none)")
else:
    print(accepted_review[["context_text", "sampled_response_text"]].head(15).to_string(index=False))
print()
print("rejected_preview:")
if rejected_review.empty:
    print("(none)")
else:
    print(
        rejected_review[
            ["rejection_reason", "quality_flags", "context_text", "sampled_response_text"]
        ].head(20).to_string(index=False)
    )
PY
