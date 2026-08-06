#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export CUDA_VISIBLE_DEVICES=""
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-complete-analysis-unattended}"

# This component remains registered and visible in synthesis, but cannot run
# until the 232 non-PBM58 same-pass word-score contracts exist on Mila.
BLOCKED_COMPONENTS="word_mistral_nonpbm58"
READY_COMPONENTS="direct_tinydialogues_pbm,direct_mistral_full79,paired_direct_tiny_mistral,route1_model_atlas,route2_response_space,route2_relative_effort,word_mistral_pbm,word_qwen_pbm,word_tinydialogues_pbm,word_cross_scorer_pbm,scientific_answer_synthesis,corrected_pbm_bayes,direct_sustained_onset"

echo "gate=full_repository_tests blocked_components=${BLOCKED_COMPONENTS}"
.venv/bin/python -m unittest discover -s tests

echo "gate=passed action=run_all_ready_analysis_components"
.venv/bin/python src/build_complete_analysis_machine.py \
  --stage all \
  --components "${READY_COMPONENTS}"

git diff --check
test -f results/current_scientific_synthesis/manifest.json
test -f docs/current_scientific_synthesis.html
echo "status=COMPLETE_AND_AUDITED"
