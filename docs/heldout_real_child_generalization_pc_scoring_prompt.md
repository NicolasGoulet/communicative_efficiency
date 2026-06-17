# PC Agent Prompt: Score Heldout Real Children

You are working on the PC/GPU machine in:

```text
/home/alkan/Portelance/compute_surprisal_mila
```

Goal: score real utterances only for the heldout children
`Forrester/Ella`, `Sachs/Naomi`, and `MPI-EVA-Manchester/Helen`.

Do not generate or score random/unigram/bigram/trigram/LSTM baselines in this
task. This is the out-of-child generalization scoring pass.

## Setup

From the `compute_surprisal_mila` repo root:

```bash
mkdir -p cleaned_data_patches new_data
tar -xzf new_data/heldout_real_child_generalization_2026-06-16.tar.gz -C cleaned_data_patches
DRY_RUN=1 bash cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/score_heldout_real_children_local.sh
```

The dry run must report exactly 12 tasks:

```text
3 children x 1 real mode x 4 contexts = 12 tasks
```

## Launch In Background

```bash
cd /home/alkan/Portelance/compute_surprisal_mila
mkdir -p results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs
nohup env \
  MODEL=mistralai/Mistral-7B-v0.3 \
  DEVICE=cuda \
  DTYPE=auto \
  BATCH_SIZE=16 \
  bash cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/score_heldout_real_children_local.sh \
  > results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.log \
  2>&1 < /dev/null &
echo $! > results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.pid
cat results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.pid
```

After launching, stop monitoring continuously. Give the user these status
commands:

```bash
cd /home/alkan/Portelance/compute_surprisal_mila
cat results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.pid
tail -n 80 results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.log
find results/raw_surprisal_heldout_real_child_generalization_2026-06-16 -name '*.scored.csv' | wc -l
find results/raw_surprisal_heldout_real_child_generalization_2026-06-16 -name '*.scored.csv' -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' | sort
```

Expected completed scored files: 12.

## Completion Audit

When the background run finishes:

```bash
.venv/bin/python cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/audit_heldout_real_child_scores.py \
  --out-root results/raw_surprisal_heldout_real_child_generalization_2026-06-16 \
  --expected-files 12
```

Do not claim the scoring is complete unless the audit passes.
