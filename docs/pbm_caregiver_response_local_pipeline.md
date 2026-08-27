# PBM caregiver-response utility: local TinyDialogues run

This local CPU run reuses the exact existing TinyDialogues caregiver `k0` and
`k3` scores for the unconditional and base-context conditions. It scores only
the three new conditions for the 174,860 frozen PBM primary response pairs:
matched child, shuffled child, and child only.

```bash
# Prepare the resumable 9-contract PBM plan.
.venv/bin/python src/prepare_local_pbm_caregiver_response.py

# Real-model smoke; use the established scoring environment exactly.
../compute_surprisal_mila/.venv/bin/python \
  src/run_local_pbm_caregiver_response_scoring.py \
  --scope smoke --batch-size 16 --cpu-threads 8

# Resumable production scoring.
../compute_surprisal_mila/.venv/bin/python \
  src/run_local_pbm_caregiver_response_scoring.py \
  --scope production --batch-size 64 --cpu-threads 8

# Run after PBM_LOCAL_SCORING_COMPLETE exists.
.venv/bin/python src/build_pbm_caregiver_response_analysis.py \
  --bootstrap-reps 1000
```

The production scorer publishes each contract atomically and validates any
completed contract before skipping it on resume. The final analysis fits the
three scorer-specific PBM discovery outcomes separately and never pools raw
bits across tokenizers.
