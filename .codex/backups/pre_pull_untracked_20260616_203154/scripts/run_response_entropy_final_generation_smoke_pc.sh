#!/usr/bin/env zsh
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/alkan/Portelance/communicative_efficiency}"
OUTPUT_DIR="${OUTPUT_DIR:-results/response_entropy_final_generation_smoke}"
FIG_DIR="${FIG_DIR:-figs/response_entropy_final_generation_smoke}"
REPORT_MD="${REPORT_MD:-docs/response_entropy_final_generation_smoke.md}"
REPORT_HTML="${REPORT_HTML:-docs/response_entropy_final_generation_smoke.html}"
MODEL_NAME="${MODEL_NAME:-mistralai/Mistral-7B-v0.3}"
TEMPERATURES="${TEMPERATURES:-0.3,0.5,0.7,1.0}"
ACCEPTED_SAMPLES_PER_SETTING="${ACCEPTED_SAMPLES_PER_SETTING:-20}"
MAX_ATTEMPTS_PER_SETTING="${MAX_ATTEMPTS_PER_SETTING:-60}"
BATCH_ATTEMPTS="${BATCH_ATTEMPTS:-16}"

cd "$PROJECT_ROOT"
mkdir -p "$OUTPUT_DIR" "$FIG_DIR" "$(dirname "$REPORT_MD")"

echo "[FINAL_SMOKE] start $(date)"
echo "[FINAL_SMOKE] output=$OUTPUT_DIR temperatures=$TEMPERATURES accepted=$ACCEPTED_SAMPLES_PER_SETTING max_attempts=$MAX_ATTEMPTS_PER_SETTING"

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_response_entropy_final_generation_smoke.py \
  --stage all \
  --input-manifest results/response_entropy_pilot_grid/pilot_generation_manifest.csv \
  --output-dir "$OUTPUT_DIR" \
  --fig-dir "$FIG_DIR" \
  --report-md "$REPORT_MD" \
  --report-html "$REPORT_HTML" \
  --contexts-per-bucket 10 \
  --temperatures "$TEMPERATURES" \
  --accepted-samples-per-setting "$ACCEPTED_SAMPLES_PER_SETTING" \
  --max-attempts-per-setting "$MAX_ATTEMPTS_PER_SETTING" \
  --batch-attempts "$BATCH_ATTEMPTS" \
  --max-new-tokens 96 \
  --top-p 0.95 \
  --top-k 0 \
  --model "$MODEL_NAME" \
  --dtype bfloat16 \
  --device auto

echo "[FINAL_SMOKE] done $(date)"
