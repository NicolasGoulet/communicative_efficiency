#!/usr/bin/env bash
set -euo pipefail

MILA_HOST="${MILA_HOST:-gouletn@login.server.mila.quebec}"
RUN_ROOT="${RUN_ROOT:-/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333}"
LOCAL_ROOT="${LOCAL_ROOT:-/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/response_entropy_generation/20260618_164333}"

mkdir -p "$LOCAL_ROOT/manifests" "$LOCAL_ROOT/merged" "$LOCAL_ROOT/manual_review"

echo "==> Pulling run config"
rsync -avhP "$MILA_HOST:$RUN_ROOT/run_config.json" "$LOCAL_ROOT/"

echo "==> Pulling manifest provenance"
rsync -avhP \
  "$MILA_HOST:$RUN_ROOT/manifests/manifest_audit.csv" \
  "$MILA_HOST:$RUN_ROOT/manifests/production_manifest.csv" \
  "$LOCAL_ROOT/manifests/"

echo "==> Pulling compact merged entropy outputs"
rsync -avhP "$MILA_HOST:$RUN_ROOT/merged/" "$LOCAL_ROOT/merged/"

echo "==> Pulling manual review extracts, if present"
rsync -avhP "$MILA_HOST:$RUN_ROOT/manual_review/" "$LOCAL_ROOT/manual_review/" || true

cat <<EOF

Pulled response-entropy outputs to:
  $LOCAL_ROOT

Main analysis table:
  $LOCAL_ROOT/merged/context_response_entropy_features.csv.gz

Manual review files:
  $LOCAL_ROOT/manual_review/accepted_selected_review.csv
  $LOCAL_ROOT/manual_review/rejected_attempts_by_reason_review.csv
  $LOCAL_ROOT/manual_review/invalid_fallback_selected_review.csv
  $LOCAL_ROOT/manual_review/manual_review_summary.txt
EOF
