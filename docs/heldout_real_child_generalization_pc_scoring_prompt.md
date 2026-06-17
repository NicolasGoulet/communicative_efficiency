# Laptop-Orchestrated Prompt: Score Heldout Real Children On The PC

You are starting from the laptop repository:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency
```

The GPU/scoring machine is reachable over SSH:

```text
alkan@192.168.7.217
```

The scoring repository on the PC is:

```text
/home/alkan/Portelance/compute_surprisal_mila
```

Goal: score real utterances only for the heldout children
`Forrester/Ella`, `Sachs/Naomi`, and `MPI-EVA-Manchester/Helen`.

Do not generate or score random/unigram/bigram/trigram/LSTM baselines in this
task. This is the out-of-child generalization scoring pass.

## First: Sync Code And Bundle

From the laptop, make sure the local communicative-efficiency commit containing
this handoff is pushed, then pull it on the PC. Preserve PC worktree edits;
do not reset or clean:

```bash
git status --short
git push origin main
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/communicative_efficiency && git pull --autostash --ff-only origin main'
```

Also pull the scorer repo on the PC if possible. If this fails due to conflicts,
stop and report the conflict; do not overwrite PC edits:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && git pull --autostash --ff-only origin main'
```

Sync the already-built bundle and this prompt to the scorer repo:

```bash
rsync -avhP \
  results/scoring_bundles/heldout_real_child_generalization_2026-06-16.tar.gz \
  docs/heldout_real_child_generalization_pc_scoring_prompt.md \
  alkan@192.168.7.217:/home/alkan/Portelance/compute_surprisal_mila/new_data/
```

## Remote Dry Run

From the laptop, run the scorer-side dry run over SSH:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && mkdir -p cleaned_data_patches && tar -xzf new_data/heldout_real_child_generalization_2026-06-16.tar.gz -C cleaned_data_patches && DRY_RUN=1 bash cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/score_heldout_real_children_local.sh'
```

The dry run must report exactly 12 tasks:

```text
3 children x 1 real mode x 4 contexts = 12 tasks
```

## Launch In Background

Launch from the laptop by starting the PC job over SSH:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && mkdir -p results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs && nohup env MODEL=mistralai/Mistral-7B-v0.3 DEVICE=cuda DTYPE=auto BATCH_SIZE=16 bash cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/score_heldout_real_children_local.sh > results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.log 2>&1 < /dev/null & echo $! > results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.pid && cat results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.pid'
```

After launching, stop monitoring continuously. Give the user these status
commands, which are also run from the laptop:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && cat results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.pid'
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && tail -n 80 results/raw_surprisal_heldout_real_child_generalization_2026-06-16/logs/score_heldout_real_children.log'
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && find results/raw_surprisal_heldout_real_child_generalization_2026-06-16 -name "*.scored.csv" | wc -l'
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && find results/raw_surprisal_heldout_real_child_generalization_2026-06-16 -name "*.scored.csv" -printf "%TY-%Tm-%Td %TH:%TM %s %p\n" | sort'
```

Expected completed scored files: 12.

## Completion Audit

When the background run finishes, run the audit over SSH from the laptop:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && .venv/bin/python cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/audit_heldout_real_child_scores.py --out-root results/raw_surprisal_heldout_real_child_generalization_2026-06-16 --expected-files 12'
```

Do not claim the scoring is complete unless the audit passes.
