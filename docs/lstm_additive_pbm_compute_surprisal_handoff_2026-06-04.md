# PBM Additive LSTM Handoff To `compute_surprisal_mila`

Date: 2026-06-04

This note is for the agent working in:

```text
/home/alkan/Portelance/compute_surprisal_mila
```

The LSTM training and utterance generation happened locally in:

```text
/home/alkan/Portelance/communicative_efficiency
```

Scoring should happen in `compute_surprisal_mila`, not in this repository.

## What Was Generated

This is a new PBM-only additive age-bin LSTM baseline run.

Corpora:

```text
Brown
Manchester
Providence
```

Age bins:

```text
006-023
024-029
030-035
036-041
042-047
048-053
054-059
060-065
```

Context conditions:

```text
k3, k4, k5 previous caretaker utterances
```

Generation variant:

```text
same_length only
```

Same-length means each generated utterance has the same number of word tokens as
the real child utterance on that row.

## Training Design

There is one LSTM per context condition and target age bin:

```text
3 context conditions x 8 age bins = 24 models
```

For each target age bin, training data are cumulative/additive:

```text
006-023 model: train on 006-023
024-029 model: train on 006-023 + 024-029
030-035 model: train on 006-023 + 024-029 + 030-035
...
060-065 model: train on all PBM rows from 006 through 065
```

The generated rows for a model are only the rows in that model's target bin.

The LSTM is a word-level encoder-decoder model:

```text
previous caretaker context -> generated child-like utterance
```

Input/output vocabulary contract:

```text
shared model vocabulary = caretaker context tokens + child target tokens
allowed generated output vocabulary = child target tokens only
```

So caretaker-only words can condition generation, but cannot be emitted as
generated child baseline words unless they also appeared in child utterances in
the cumulative training data for that model.

## Run Command

The completed run used:

```bash
.venv/bin/python src/run_lstm_additive_age_context_pipeline.py \
  --output_dir results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03 \
  --datasets Brown Manchester Providence \
  --contexts 3 4 5 \
  --variants same_length \
  --epochs 20 \
  --embedding_dim 256 \
  --hidden_dim 512 \
  --num_layers 2 \
  --dropout 0.2 \
  --batch_size 256 \
  --max_vocab_size 30000 \
  --device cuda
```

Run artifact directory:

```text
/home/alkan/Portelance/communicative_efficiency/results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03
```

Important run-level files:

```text
model_run_manifest.csv
training_summary.csv
generation_summary.csv
generation_diagnostics.csv
generation_samples.csv
lstm_additive_pipeline_manifest.csv
plots/*.png
plots/*.pdf
```

Each of the 24 model folders contains:

```text
model.pt
vocab.json
config.json
training_summary.csv
batch_training_log.csv
```

## Completed Run Validation

The run completed successfully.

```text
model checkpoints: 24
diagnostic rows: 24
generated rows across k/bin diagnostics: 1,339,524
empty generated rows: 0
same-length mismatches: 0
PBM child scorer-ready files: 21
generated rows per LSTM column: 446,508
```

Generated columns:

```text
lstm_additive_k3_same_length_utterance
lstm_additive_k4_same_length_utterance
lstm_additive_k5_same_length_utterance
```

The model manifest includes both:

```text
vocab_size
child_output_vocab_size
```

`vocab_size` is the shared model vocabulary. `child_output_vocab_size` is the
child-side vocabulary used to constrain generated outputs.

## Files To Retrieve For Scoring

The scorer-ready CSVs live here:

```text
/home/alkan/Portelance/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/preprocessed_data/{Brown,Manchester,Providence}/{child}/chi.surprisal_scoring_with_lstm_additive.csv
```

There are 21 files total.

Example:

```text
/home/alkan/Portelance/communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/preprocessed_data/Brown/Adam/chi.surprisal_scoring_with_lstm_additive.csv
```

Expected header:

```text
dataset
child_id
source_group
session_id
age_months
file
line_no
utt_id
context_k1
context_k2
context_k3
chi_utterance_clean
random_model_utterance_bin6
unigram_model_utterance_bin6
bigram_model_utterance_bin6
trigram_model_utterance_bin6
lstm_additive_k3_same_length_utterance
lstm_additive_k4_same_length_utterance
lstm_additive_k5_same_length_utterance
```

The new LSTM columns are already inserted beside the existing generated
baseline columns.

## Scoring Contract

Score only in `compute_surprisal_mila`.

For each target utterance column, score it under each row-matched scoring
context:

```text
context_k1
context_k2
context_k3
```

Target columns to score for this handoff:

```text
lstm_additive_k3_same_length_utterance
lstm_additive_k4_same_length_utterance
lstm_additive_k5_same_length_utterance
```

Do not confuse generation k with scoring context k:

```text
generation k3/k4/k5 = how much caretaker context the LSTM generator saw
scoring context_k1/k2/k3 = what the surprisal model conditions on
```

For example, `lstm_additive_k5_same_length_utterance` still needs to be scored
three times:

```text
under context_k1
under context_k2
under context_k3
```

Do not include context tokens in target surprisal. Preserve row provenance:

```text
dataset
child_id
session_id
file
line_no
utt_id
age_months
source target column
source context column
```

## Suggested Retrieval Destination

A destination folder was created earlier in `compute_surprisal_mila`:

```text
/home/alkan/Portelance/compute_surprisal_mila/data/lstm_additive_pbm_006_065_k3_k4_k5_same_length
```

The scoring agent can copy or symlink the 21 scorer-ready CSVs into that folder,
or build a manifest pointing back to their absolute paths in
`communicative_efficiency`.

## Quick Audit Commands

From `communicative_efficiency`, verify the source artifacts:

```bash
OUT=results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03

find "$OUT" -path '*/model.pt' | wc -l

.venv/bin/python - <<'PY'
import csv
from pathlib import Path

out = Path("results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03")
diag = list(csv.DictReader((out / "generation_diagnostics.csv").open()))
summary = list(csv.DictReader((out / "generation_summary.csv").open()))
manifest = list(csv.DictReader((out / "model_run_manifest.csv").open()))

print("models", len(manifest))
print("diagnostic_rows", len(diag))
print("empty_generated_rows", sum(int(r["empty_generated_rows"]) for r in diag))
print("same_length_mismatches", sum(int(r["same_length_mismatches"]) for r in diag))
for col in [
    "lstm_additive_k3_same_length_utterance",
    "lstm_additive_k4_same_length_utterance",
    "lstm_additive_k5_same_length_utterance",
]:
    print(col, sum(int(r.get(col, 0) or 0) for r in summary))
print("has_child_output_vocab_size", "child_output_vocab_size" in manifest[0])
PY
```

Expected:

```text
24 model checkpoints
models 24
diagnostic_rows 24
empty_generated_rows 0
same_length_mismatches 0
446,508 generated rows per LSTM column
has_child_output_vocab_size True
```
