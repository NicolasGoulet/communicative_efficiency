#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MILA_HOST="${MILA_HOST:-gouletn@login.server.mila.quebec}"
REMOTE_PROJECT="${REMOTE_PROJECT:-/home/mila/g/gouletn/compute_surprisal_mila}"
RUN_ROOT="${RUN_ROOT:-/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333}"
REVIEW_SHARDS="${REVIEW_SHARDS:-64}"
MAX_ACCEPTED_ROWS="${MAX_ACCEPTED_ROWS:-160}"
MAX_REJECTED_PER_REASON="${MAX_REJECTED_PER_REASON:-60}"
MAX_FALLBACK_ROWS="${MAX_FALLBACK_ROWS:-500}"

LOCAL_SBATCH="$SCRIPT_DIR/mila_response_entropy_manual_review.sbatch"
REMOTE_SBATCH="$REMOTE_PROJECT/slurm/mila_response_entropy_manual_review.sbatch"

echo "==> Copying review Slurm script to Mila"
rsync -avhP "$LOCAL_SBATCH" "$MILA_HOST:$REMOTE_SBATCH"

echo "==> Submitting CPU review job"
JOB_ID="$(
  ssh "$MILA_HOST" \
    "cd '$REMOTE_PROJECT' && RUN_ROOT='$RUN_ROOT' REVIEW_SHARDS='$REVIEW_SHARDS' MAX_ACCEPTED_ROWS='$MAX_ACCEPTED_ROWS' MAX_REJECTED_PER_REASON='$MAX_REJECTED_PER_REASON' MAX_FALLBACK_ROWS='$MAX_FALLBACK_ROWS' sbatch --parsable 'slurm/$(basename "$REMOTE_SBATCH")'"
)"

echo "REVIEW_JOB=$JOB_ID"
echo "RUN_ROOT=$RUN_ROOT"
echo
echo "==> Waiting for review job to finish"
ssh "$MILA_HOST" "
  cd '$REMOTE_PROJECT'
  while squeue -j '$JOB_ID' -h | grep -q .; do
    squeue -j '$JOB_ID' -o '%.18i %.14P %.18j %.3t %.12M %.30R'
    sleep 20
  done
  echo '===== REVIEW OUTPUT ====='
  cat 'slurm/logs/respent_review_${JOB_ID}.out'
  echo '===== REVIEW ERRORS ====='
  cat 'slurm/logs/respent_review_${JOB_ID}.err' 2>/dev/null || true
"

cat <<EOF

Next, pull the review CSVs back to the laptop:
  scripts/response_entropy_pull_outputs_from_mila.sh
EOF
