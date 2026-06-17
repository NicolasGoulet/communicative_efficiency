#!/usr/bin/env zsh
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/alkan/Portelance/communicative_efficiency}"
WAIT_PID="${WAIT_PID:-9317}"
OUTPUT_DIR="results/response_entropy_pilot_grid"

cd "$PROJECT_ROOT"

while kill -0 "$WAIT_PID" 2>/dev/null; do
  sleep 30
done

echo "[WATCHDOG] starting detached resume at $(date)"

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/sample_context_responses.py \
  --manifest "$OUTPUT_DIR/pilot_generation_manifest.csv" \
  --output "$OUTPUT_DIR/pilot_response_samples_clean.csv.gz" \
  --model mistralai/Mistral-7B-v0.3 \
  --temperatures 1.6 \
  --samples-per-context 100 \
  --batch-contexts 2 \
  --batch-samples 16 \
  --max-new-tokens 24 \
  --top-p 0.95 \
  --top-k 0 \
  --dtype bfloat16 \
  --device auto

echo "[WATCHDOG] finished detached resume at $(date)"
