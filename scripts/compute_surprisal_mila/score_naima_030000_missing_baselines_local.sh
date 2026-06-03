#!/usr/bin/env bash
# Score the tiny Providence/Naima 030000 generated-baseline patch locally.
#
# Expected setup from compute_surprisal_mila repo root:
#   tar -xzf /path/to/naima_030000_missing_baselines_scoring_patch_2026-06-03.tar.gz
#   MODEL=/path/or/hf/id DEVICE=cuda bash scripts/score_naima_030000_missing_baselines_local.sh

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PATCH_NAME="${PATCH_NAME:-naima_030000_missing_baselines}"
DATA_ROOT="${DATA_ROOT:-$PROJECT_ROOT/cleaned_data_patches/$PATCH_NAME/data/preprocessed_data}"
OUT_ROOT="${OUT_ROOT:-$PROJECT_ROOT/results/raw_surprisal_cleaned_${PATCH_NAME}_patch}"
MODEL="${MODEL:-mistralai/Mistral-7B-v0.3}"
TASKS_TSV="${TASKS_TSV:-$PROJECT_ROOT/slurm/tasks_${PATCH_NAME}_mistral.tsv}"

BATCH_SIZE="${BATCH_SIZE:-16}"
UNITS="${UNITS:-bits}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-auto}"
MAX_LENGTH="${MAX_LENGTH:-}"
OVERWRITE="${OVERWRITE:-0}"

cd "$PROJECT_ROOT"
mkdir -p "$(dirname "$TASKS_TSV")" "$OUT_ROOT"

if [[ ! -d "$DATA_ROOT" ]]; then
  echo "[ERROR] DATA_ROOT not found: $DATA_ROOT" >&2
  echo "        Extract the patch tarball from the compute_surprisal_mila repo root first." >&2
  exit 2
fi

uv run python src/build_cleaned_scoring_manifest.py \
  --data-root "$DATA_ROOT" \
  --output-root "$OUT_ROOT" \
  --manifest "$TASKS_TSV" \
  --bin 6 \
  --modes random,unigram,bigram,trigram \
  --context-cols context_k1,context_k2,context_k3 \
  --strict-context-col \
  --missing-policy error

task_count="$(awk -F'\t' 'NR > 1 {n++} END {print n + 0}' "$TASKS_TSV")"
if [[ "$task_count" -ne 16 ]]; then
  echo "[ERROR] Expected 16 patch tasks, got $task_count from $TASKS_TSV" >&2
  exit 2
fi

echo "[INFO] Scoring $task_count tasks from $TASKS_TSV"

tail -n +2 "$TASKS_TSV" | while IFS=$'\t' read -r task_id mode corpus child input_csv text_col context_col output_csv; do
  echo "[INFO] task=$task_id mode=$mode context=${context_col:-k0} output=$output_csv"
  if [[ -f "$output_csv" && "$OVERWRITE" != "1" ]]; then
    echo "[SKIP] exists: $output_csv"
    continue
  fi

  cmd=(uv run python src/new_score_utterances.py
    --input "$input_csv"
    --output "$output_csv"
    --model "$MODEL"
    --units "$UNITS"
    --batch-size "$BATCH_SIZE"
    --device "$DEVICE"
    --dtype "$DTYPE"
    --text-col "$text_col"
    --add-metadata
    --score-zero-counts
  )
  if [[ "$OVERWRITE" == "1" ]]; then
    cmd+=(--overwrite)
  fi
  if [[ -n "$MAX_LENGTH" ]]; then
    cmd+=(--max-length "$MAX_LENGTH")
  fi
  if [[ -n "$context_col" ]]; then
    cmd+=(--context-col "$context_col" --strict-context-col)
  fi

  "${cmd[@]}"
done

echo "[OK] Patch scores written under $OUT_ROOT"
