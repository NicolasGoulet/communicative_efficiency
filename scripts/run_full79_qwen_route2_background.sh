#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RUN_LABEL="naturalistic_79_children_qwen3_14b_response_samples_k3_t1_untruncated"
RUN_ID="20260716_185726"
REMOTE_RUN="mila:/network/scratch/g/gouletn/compute_surprisal_mila/response_generation/${RUN_LABEL}/${RUN_ID}/"
REMOTE_MARKER="mila:~/compute_surprisal_mila/reports/response_generation/${RUN_LABEL}/${RUN_ID}/PRODUCTION_COMPLETE"
LOCAL_RUN="${PROJECT_ROOT}/results/external/compute_surprisal_mila/response_generation/${RUN_LABEL}/${RUN_ID}"
OUTPUT_DIR="${PROJECT_ROOT}/results/full79_qwen_route2_analysis"
INPUT_WIDE="${PROJECT_ROOT}/results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz"
COMPUTE_REPO="${PROJECT_ROOT}/../compute_surprisal_mila"
SYNC_FIRST=0
FOREGROUND=0

usage() {
  cat <<'EOF'
Usage: scripts/run_full79_qwen_route2_background.sh [--sync] [--foreground]

  --sync        Retrieve the already-completed Qwen run and completion marker
                from Mila before launching. This may request Mila OTP.
  --foreground  Run in the current terminal instead of nohup.

Without --sync, the launcher refuses to start unless the audited Qwen handoff
is already present locally. It never regenerates the 64,552,400 responses.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sync)
      SYNC_FIRST=1
      ;;
    --foreground)
      FOREGROUND=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

mkdir -p "$LOCAL_RUN" "$OUTPUT_DIR/logs"

if [[ "$SYNC_FIRST" -eq 1 ]]; then
  echo "[sync] retrieving completed Qwen run ${RUN_ID}"
  rsync -avhP "$REMOTE_RUN" "$LOCAL_RUN/"
  echo "[sync] retrieving authoritative PRODUCTION_COMPLETE marker"
  rsync -avhP "$REMOTE_MARKER" "$LOCAL_RUN/PRODUCTION_COMPLETE"
fi

[[ -s "$LOCAL_RUN/PRODUCTION_COMPLETE" ]] || {
  echo "[ERROR] audited Qwen handoff is not local: $LOCAL_RUN" >&2
  echo "Run this launcher once with --sync and enter the Mila OTP when prompted." >&2
  exit 2
}
[[ -s "$INPUT_WIDE" ]] || {
  echo "[ERROR] full-79 real-child table is missing: $INPUT_WIDE" >&2
  exit 2
}
[[ -x "$PROJECT_ROOT/.venv/bin/python" ]] || {
  echo "[ERROR] project Python is missing: $PROJECT_ROOT/.venv/bin/python" >&2
  exit 2
}

PID_FILE="$OUTPUT_DIR/background.pid"
LOG_FILE="$OUTPUT_DIR/logs/full79_qwen_route2.log"
if [[ -s "$PID_FILE" ]]; then
  OLD_PID="$(tr -dc '0-9' < "$PID_FILE")"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[ERROR] full-79 Route 2 is already running with PID $OLD_PID" >&2
    exit 2
  fi
fi

COMMAND=(
  "$PROJECT_ROOT/.venv/bin/python"
  "$PROJECT_ROOT/src/build_full79_qwen_route2_analysis.py"
  --stage all
  --qwen-run-root "$LOCAL_RUN"
  --generation-marker "$LOCAL_RUN/PRODUCTION_COMPLETE"
  --input-wide "$INPUT_WIDE"
  --output-dir "$OUTPUT_DIR"
  --compute-repo "$COMPUTE_REPO"
)

if [[ "$FOREGROUND" -eq 1 ]]; then
  echo "[run] foreground log will stream in this terminal"
  MPLCONFIGDIR="$OUTPUT_DIR/matplotlib" "${COMMAND[@]}"
  exit $?
fi

echo "[run] starting full-79 Route 2 in the background"
nohup env MPLCONFIGDIR="$OUTPUT_DIR/matplotlib" "${COMMAND[@]}" >"$LOG_FILE" 2>&1 </dev/null &
BACKGROUND_PID=$!
printf '%s\n' "$BACKGROUND_PID" > "$PID_FILE"

echo "[started] pid=$BACKGROUND_PID"
echo "[log] $LOG_FILE"
echo "[marker] $OUTPUT_DIR/FULL79_QWEN_ROUTE2_COMPLETE_AND_AUDITED"
echo "[watch] tail -n 60 -f '$LOG_FILE'"
