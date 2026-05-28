# LSTM PC Handoff

Date: 2026-05-28

Purpose: hand off the current state to an agent running on the local GPU PC.
The next step is to generate LSTM baseline utterances, not to score surprisal.

## Machine Context

Laptop project path used in recent work:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency
```

PC project path reported by the user:

```text
/home/alkan/Portelance/communicative_efficiency
```

PC host/IP observed on 2026-05-28:

```text
alkan-MS-7C02
192.168.7.217
```

The PC has SSH running on port 22. Data should move by `rsync`, not Git.

## Git Versus Data

Use Git for:

- source code
- tests
- configs
- Markdown docs

Use `rsync` / Globus for:

- `data/`
- `results/`
- `figs/`
- tarballs
- model checkpoints

`.gitignore` was updated on 2026-05-28 to ignore bulky generated/data paths.
If bulky files were already tracked before this update, remove them from the Git
index with `git rm --cached` while keeping local files.

## Required Data For LSTM Generation

The LSTM pipeline expects the current merged-early big-cleaned bundle:

```text
data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

From the laptop, transfer it to the PC with:

```bash
rsync -avhP --info=progress2 --partial --append-verify \
  /home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/ \
  alkan@192.168.7.217:/home/alkan/Portelance/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

On the PC, verify with:

```bash
du -sh /home/alkan/Portelance/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023
ls /home/alkan/Portelance/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023
```

## LSTM Model To Run

Main model:

- word-level encoder-decoder LSTM
- encoder input: bounded prior caretaker context
- decoder output: child-like utterance
- default context: last 3 caretaker utterances, capped at 60 tokens
- no pretrained language model
- not a surprisal scorer

Read:

- `docs/lstm-baseline-pipeline.md`
- `configs/lstm_baseline_16gb_smoke.json`
- `configs/lstm_baseline_16gb_default.json`
- `src/run_lstm_baseline_pipeline.py`
- `src/generate_lstm_utterances.py`

## Commands On The PC

Dry-run validation, no training:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_default.json \
  --dry_run
```

Small GPU smoke run:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_smoke.json
```

Full GPU run:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_default.json
```

## Expected Outputs

Run-level output folder from the default config:

```text
results/lstm_baselines/default_naturalistic_merged_006_023_seq2seq_ctx3/
```

Expected run-level artifacts:

- `config.json`
- `variants.json`
- `vocab.json`
- `model.pt`
- `training_summary.csv`
- `generation_summary.csv`
- `lstm_pipeline_manifest.csv`

Expected per-child sibling files:

- `chi.lstm_generated.csv`
- `chi.shared_caretaker_contexts.with_lstm.csv`
- `chi.surprisal_scoring_with_lstm.csv`

These are generated baselines and scoring-ready inputs. They should later be
sent to the Mila scoring project for actual surprisal computation.

## After Running Or Modifying

The PC agent should update:

- `TODO.md`
- `docs/notes.md`
- `docs/lstm-baseline-pipeline.md` if model logic or config meanings changed

Record:

- exact command run
- config file used
- hardware/device
- whether it was smoke or full run
- row counts / generated rows
- output paths
- any training losses
- any failed or interrupted run

Do not claim a model was trained unless `model.pt`, `training_summary.csv`, and
generation outputs actually exist.
