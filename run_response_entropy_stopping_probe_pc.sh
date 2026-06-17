#!/usr/bin/env zsh
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/alkan/Portelance/communicative_efficiency}"
OUTPUT_DIR="${OUTPUT_DIR:-results/response_entropy_stopping_probe}"
FIG_DIR="${FIG_DIR:-figs/response_entropy_stopping_probe}"
REPORT_MD="${REPORT_MD:-docs/response_entropy_stopping_probe.md}"
REPORT_HTML="${REPORT_HTML:-docs/response_entropy_stopping_probe.html}"
TEMPERATURES="${TEMPERATURES:-0.5,0.7,1.0}"
MAX_NEW_TOKENS_VALUES="${MAX_NEW_TOKENS_VALUES:-12 24 48 96}"
SAMPLES_PER_CONTEXT="${SAMPLES_PER_CONTEXT:-10}"
CONTEXTS_PER_BUCKET="${CONTEXTS_PER_BUCKET:-10}"
BATCH_CONTEXTS="${BATCH_CONTEXTS:-2}"
BATCH_SAMPLES="${BATCH_SAMPLES:-16}"
MODEL_NAME="${MODEL_NAME:-mistralai/Mistral-7B-v0.3}"

cd "$PROJECT_ROOT"
mkdir -p "$OUTPUT_DIR" "$FIG_DIR"

echo "[STOPPING_PROBE] start $(date)"
echo "[STOPPING_PROBE] grid: contexts_per_bucket=$CONTEXTS_PER_BUCKET temperatures=$TEMPERATURES max_new_tokens=($MAX_NEW_TOKENS_VALUES) samples_per_context=$SAMPLES_PER_CONTEXT"

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_response_entropy_stopping_probe.py \
  --stage manifest \
  --input-manifest results/response_entropy_pilot_grid/pilot_generation_manifest.csv \
  --output-dir "$OUTPUT_DIR" \
  --fig-dir "$FIG_DIR" \
  --contexts-per-bucket "$CONTEXTS_PER_BUCKET" \
  --temperatures "$TEMPERATURES" \
  --max-new-tokens "${MAX_NEW_TOKENS_VALUES// /,}" \
  --samples-per-context "$SAMPLES_PER_CONTEXT"

for cap in ${(z)MAX_NEW_TOKENS_VALUES}; do
  echo "[STOPPING_PROBE] generating max_new_tokens=$cap at $(date)"
  MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/sample_context_responses.py \
    --manifest "$OUTPUT_DIR/stopping_probe_manifest.csv" \
    --output "$OUTPUT_DIR/stopping_probe_samples_max${cap}.csv.gz" \
    --model "$MODEL_NAME" \
    --temperatures "$TEMPERATURES" \
    --samples-per-context "$SAMPLES_PER_CONTEXT" \
    --batch-contexts "$BATCH_CONTEXTS" \
    --batch-samples "$BATCH_SAMPLES" \
    --max-new-tokens "$cap" \
    --top-p 0.95 \
    --top-k 0 \
    --dtype bfloat16 \
    --device auto
done

echo "[STOPPING_PROBE] summarizing $(date)"
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_response_entropy_stopping_probe.py \
  --stage summarize \
  --output-dir "$OUTPUT_DIR" \
  --fig-dir "$FIG_DIR" \
  --report-md "$REPORT_MD" \
  --report-html "$REPORT_HTML"

echo "[STOPPING_PROBE] done $(date)"
