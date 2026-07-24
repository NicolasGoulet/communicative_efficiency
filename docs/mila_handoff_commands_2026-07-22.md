# Mila Handoff Commands

Prepared on 22 July 2026. These are the remote actions intentionally left for
the user. Run commands in the section whose heading says either **laptop** or
**Mila**. Do not run an `rsync` command from a Mila login node.

Before the LSTM section, review and merge the draft pull request at
<https://github.com/NicolasGoulet/generate_baselines_mila/pull/1>, or use the
audited branch and exact commit shown below.

## 1. Retrieve the Missing Mistral Full-79 Completion Evidence — Laptop

Create the ignored local report destination:

```bash
mkdir -p '/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/reports/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955'
```

Retrieve the compact final report:

```bash
rsync -avhP 'mila:~/compute_surprisal_mila/reports/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/' '/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/reports/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/'
```

Retrieve the authoritative final marker beside the already-local archive:

```bash
rsync -avhP 'mila:/network/scratch/g/gouletn/compute_surprisal_mila/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/COMPLETE' '/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/COMPLETE'
```

Verify both products:

```bash
grep -Fx 'COMPLETE_AND_AUDITED' '/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/COMPLETE'
find '/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/reports/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955' -maxdepth 2 -type f -print
```

The already-local scored archive must retain this checksum:

```bash
printf '%s  %s\n' 'ff0bf42754fc6ccb8278db7a588cef1083ca18a944032b9ce9e1179341448a81' '/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/naturalistic_79_children_fp16_scored_csvs.tar.gz' | sha256sum -c -
```

## 2. Ensure the Full-79 Input Bundle Is on Mila — Mila

After logging in, create the authoritative scratch destination:

```bash
mkdir -p "$SCRATCH/communicative_efficiency_data/big_cleaned_dataset/default_naturalistic_merged_006_023"
```

Log out or open a separate laptop terminal before the next command.

## 3. Upload or Refresh the Full-79 Input Bundle — Laptop

The trailing slashes mean “synchronize the directory contents.” Re-running
this command is safe and resumes partial transfers:

```bash
rsync -avhP '/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/' 'mila:/network/scratch/g/gouletn/communicative_efficiency_data/big_cleaned_dataset/default_naturalistic_merged_006_023/'
```

The local source has 629 files, an 80-line manifest containing 79 child rows,
and these two contract hashes:

```text
9d14ed7fdbf6c2957ef3d63a5cb366f3174a3d007c6d02044aaaf69d7a6429de  manifest.csv
9cd5442ce270048c4842b279df0d8460bcd7fed28c5f293ec45727bcf12ed87c  age_ngram_dicts/merged_early_006_023/age_bins.json
```

## 4. Verify the Uploaded Bundle — Mila

```bash
cd "$SCRATCH/communicative_efficiency_data/big_cleaned_dataset/default_naturalistic_merged_006_023"
test "$(find . -type f | wc -l)" -eq 629
test "$(wc -l < manifest.csv)" -eq 80
printf '%s  %s\n' '9d14ed7fdbf6c2957ef3d63a5cb366f3174a3d007c6d02044aaaf69d7a6429de' 'manifest.csv' | sha256sum -c -
printf '%s  %s\n' '9cd5442ce270048c4842b279df0d8460bcd7fed28c5f293ec45727bcf12ed87c' 'age_ngram_dicts/merged_early_006_023/age_bins.json' | sha256sum -c -
```

Stop here if any check fails.

## 5. Put the Audited LSTM Code on Mila — Mila

The production implementation is frozen at commit
`134f4df4eb3bc60df93fe1dfee72811012b08ea2` on branch
`agent/full79-lstm-production`.

For an existing checkout:

```bash
cd "$HOME/communicative_efficiency_repos/generate_baselines_mila"
git status --short
git fetch origin agent/full79-lstm-production
git switch agent/full79-lstm-production || git switch --track origin/agent/full79-lstm-production
git pull --ff-only
test "$(git rev-parse HEAD)" = '134f4df4eb3bc60df93fe1dfee72811012b08ea2'
```

If the repository is absent, clone it and then select the branch:

```bash
mkdir -p "$HOME/communicative_efficiency_repos"
cd "$HOME/communicative_efficiency_repos"
git clone --branch agent/full79-lstm-production --single-branch git@github.com:NicolasGoulet/generate_baselines_mila.git
cd generate_baselines_mila
test "$(git rev-parse HEAD)" = '134f4df4eb3bc60df93fe1dfee72811012b08ea2'
```

Do not continue from a dirty checkout or a different commit.

## 6. Re-run the Local/CPU Gates on Mila — Mila

Select the CUDA-enabled Python environment explicitly:

```bash
cd "$HOME/communicative_efficiency_repos/generate_baselines_mila"
export PYTHON_CMD="$HOME/venvs/generate-baselines/bin/python"
"$PYTHON_CMD" -c 'import torch; print(torch.__version__, torch.backends.cuda.is_built())'
```

The second printed value must be `True`. Then run:

```bash
PYTHONPYCACHEPREFIX="$SCRATCH/generate_baselines_mila/preflight_pycache" PYTHONPATH=src "$PYTHON_CMD" -m unittest discover -s tests
bash -n slurm/*.sbatch slurm/*.sh
git diff --check
git status --short
```

Expected unit-test result for the frozen commit: 13 tests pass and two
environment-dependent tests may be skipped.

Inspect Mila's live partitions and GPU resources instead of assuming they are
unchanged:

```bash
sinfo -o '%P %a %l %G'
```

Validate the same resource family used by the production wrapper with a tiny
allocation. This command requests exactly one task and one GPU:

```bash
srun --partition=long --ntasks=1 --gres=gpu:1 --cpus-per-task=1 --mem=4G --time=00:05:00 "$PYTHON_CMD" -c 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'
```

Stop if `long`, `long-cpu`, or `gpu:1` is not valid on the current cluster, or
if CUDA is unavailable. Adjust the reviewed wrapper in Git rather than
silently improvising a different production command.

## 7. Submit the Smoke-Gated Full-79 LSTM DAG — Mila

Use the fixed run ID below so every later retrieval path is exact. The
submitter refuses to reuse an existing run root.

```bash
cd "$HOME/communicative_efficiency_repos/generate_baselines_mila"
export PYTHON_CMD="$HOME/venvs/generate-baselines/bin/python"
export RUN_ID='20260722_full79_lstm_v1'
export RUN_ROOT="$SCRATCH/generate_baselines_mila/full79_lstm_additive_k3_same_length/$RUN_ID"
export MAX_CONCURRENT=3
export GPU_GRES='gpu:1'
test ! -e "$RUN_ROOT"
bash slurm/submit_full_79_lstm.sh "$SCRATCH/communicative_efficiency_data/big_cleaned_dataset/default_naturalistic_merged_006_023"
```

The submitter creates seven dependent jobs: preparation, exact-wrapper GPU
smoke, wave 1, wave-1 audit, wave 2, wave-2 audit, and final audit. Every job
requests `--ntasks=1`; production uses only the `--gres` GPU family.

## 8. Monitor and Verify the DAG — Mila

Use the job IDs printed by the submitter:

```bash
squeue -u "$USER"
sacct -j '<comma-separated printed job IDs>' --format=JobID,JobName%32,State,ExitCode,Elapsed,AllocTRES%60
```

An empty queue is not completion. After the final audit reports `COMPLETED`,
verify the run marker and compact reports:

```bash
grep -Fx 'COMPLETE_AND_AUDITED' "$SCRATCH/generate_baselines_mila/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/COMPLETE_AND_AUDITED"
find "$SCRATCH/generate_baselines_mila/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/reports" -maxdepth 2 -type f -print
du -sh "$SCRATCH/generate_baselines_mila/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1"
```

If a stage fails, inspect its `.out` and `.err` logs and rerun the reviewed
submitter only after determining why. The output audit allows validated
production cells to be skipped, but the top-level submitter deliberately
requires a fresh run root; do not delete or overwrite the failed run.

## 9. Retrieve the Complete LSTM Run — Laptop

Create an ignored archive destination:

```bash
mkdir -p '/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila/results/mila_runs/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1'
```

Retrieve manifests, prepared inputs, generated CSVs, checkpoints,
vocabularies, audits, reports, smoke artifacts, and markers. Only disposable
Python bytecode is excluded:

```bash
rsync -avhP --exclude 'pycache/' 'mila:/network/scratch/g/gouletn/generate_baselines_mila/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/' '/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila/results/mila_runs/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/'
```

Also place the compact report product in the main analysis repository:

```bash
mkdir -p '/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/results/mila_modular_runs_2026_07_08/products/full79_lstm_reports/20260722_full79_lstm_v1'
rsync -avhP 'mila:/network/scratch/g/gouletn/generate_baselines_mila/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/reports/' '/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/results/mila_modular_runs_2026_07_08/products/full79_lstm_reports/20260722_full79_lstm_v1/'
```

Verify the final local marker and perform a checksum dry-run against Mila. A
quiet second command means the retrieved files match; it does not delete
anything:

```bash
grep -Fx 'COMPLETE_AND_AUDITED' '/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila/results/mila_runs/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/COMPLETE_AND_AUDITED'
rsync -avhPnc --exclude 'pycache/' 'mila:/network/scratch/g/gouletn/generate_baselines_mila/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/' '/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila/results/mila_runs/full79_lstm_additive_k3_same_length/20260722_full79_lstm_v1/'
```

## 10. Deliberate Stop Point

The commands above complete and retrieve **LSTM training and generation**.
They do not score the new LSTM utterances with Mistral. The full-79 LSTM
scoring bundle and its `compute_surprisal_mila` smoke-gated submission wrapper
have not yet been implemented and audited. Do not substitute an ad hoc scoring
command or claim that full-79 LSTM surprisal exists.

Likewise, do not launch the six-cell generated-baseline patch, semantic
response-entropy calibration, listener-utility scoring, or the interrupted
Qwen response-generation run from this sheet. Each requires its own reviewed
input contract, smoke gate, output audit, and retrieval commands.
