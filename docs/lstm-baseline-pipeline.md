# LSTM Baseline Pipeline

This pipeline prepares a neural baseline that is stronger than the random,
unigram, bigram, and trigram baselines, but deliberately much weaker and more
bounded than an LLM.

It is not a surprisal scorer. It generates child-like utterance baselines that
can later be sent to the separate Mila scoring project.

## High-Level Scientific Description

Question:

> Given recent caretaker speech, what child utterance would a small recurrent
> model produce?

Default model:

- architecture: word-level encoder-decoder LSTM
- training scope: one additive model per target age bin
- encoder input: the last `k` prior caretaker utterances
- context cap: only the last `max_context_tokens` context tokens are kept
- decoder input during training: `<bos>` plus the child utterance prefix
- decoder target during training: the child utterance plus `<eos>`
- generation input: caretaker context encoded once, then autoregressive decoding
  from `<bos>`

The default architecture is `seq2seq_lstm`. A legacy `causal_lstm` option is
also available, but the encoder-decoder model is the one to describe as the main
baseline.

## Additive Age-Bin Logic

The fair LSTM baseline now mirrors the developmental information constraint used
by the random/unigram/bigram/trigram baselines.

Default bins:

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

For each target bin, the pipeline trains a separate LSTM:

| Target bin | LSTM training examples | Generated rows |
| --- | --- | --- |
| `006-023` | child examples in `006-023` | rows in `006-023` |
| `024-029` | child examples in `006-023` plus `024-029` | rows in `024-029` |
| `030-035` | child examples through `030-035` | rows in `030-035` |
| later bins | all previous bins plus current bin | rows in current bin only |

This means the model used for an early child utterance never trains on later
developmental data. The current bin is included, matching the additive
vocabulary/count logic used by the n-gram baselines.

The JSON config controls this with:

```json
"age_binning": {
  "mode": "additive_age_bins",
  "bins_config": "data/big_cleaned_dataset/default_naturalistic_merged_006_023/age_ngram_dicts/merged_early_006_023/age_bins.json",
  "strategy": "merged_early_006_023"
}
```

A legacy/exploratory global run remains possible with `"mode": "global"`, but
that should not be used as the main fair comparison to the additive n-gram
baselines.

## Why This Is Not An LLM Baseline

The model is intentionally small and bounded:

- word-level vocabulary, not subword LLM vocabulary
- LSTM recurrence, not transformer attention
- no pretrained language knowledge
- finite caretaker context window
- trained only on the prepared CHILDES-derived data available to the target age
  bin

This makes it useful as a middle baseline: more context-sensitive than n-grams,
but much less powerful than Mistral or another pretrained LLM.

## Current Data Source

Default config uses the current strict naturalistic merged-early bundle:

- `data/big_cleaned_dataset/default_naturalistic_merged_006_023/manifest.csv`
- `data/big_cleaned_dataset/default_naturalistic_merged_006_023/preprocessed_data/`

Age range:

- `006` through `065.999` months

Default datasets:

- all strict naturalistic datasets in the big-cleaned manifest

## Generated Variants

The same trained model can generate multiple utterance variants:

- `lstm_same_length_utterance`: generates exactly the same number of word tokens
  as the paired real child utterance. This is the cleanest length-controlled
  comparison.
- `lstm_free_length_utterance`: generates until `<eos>` or a token cap. This is
  useful for asking whether the model chooses similar response lengths from
  caretaker context.

The variant definitions live in the JSON config, so the output column names,
generation length mode, max token cap, and minimum generated length can be
changed without editing source code.

## Config Files

Full GPU-oriented default:

- `configs/lstm_baseline_16gb_default.json`

PBM-only additive run for fair comparison against PBM-trained n-gram baselines:

- `configs/lstm_baseline_16gb_pbm_additive.json`

Small GPU smoke run:

- `configs/lstm_baseline_16gb_smoke.json`

Important knobs:

- `age_binning.mode`: default `additive_age_bins`
- `age_binning.bins_config`: JSON age-bin file shared with the n-gram baselines
- `context_utterances`: how many previous caretaker utterances are eligible
- `max_context_tokens`: maximum context tokens after flattening caretaker turns
- `embedding_dim`
- `hidden_dim`
- `num_layers`
- `dropout`
- `epochs`
- `batch_size`
- `learning_rate`
- `max_vocab_size`
- `temperature`
- `top_k`
- `variants`

For a 16GB VRAM local GPU, start with the smoke config. If memory is stable,
then run the default config.

## Commands

Do not run this on the laptop for training. Run on the GPU machine.

Smoke run:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_smoke.json
```

Full run:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_default.json
```

PBM-only run:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_pbm_additive.json
```

Dry-run validation, with no training:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_default.json \
  --dry_run
```

PBM-only dry run:

```bash
.venv/bin/python src/run_lstm_baseline_pipeline.py \
  --config configs/lstm_baseline_16gb_pbm_additive.json \
  --dry_run
```

## Outputs

The pipeline writes run-level artifacts:

- `config.json`
- `variants.json`
- `age_bins.json`
- `lstm_age_bin_manifest.csv`
- `generation_summary.csv`
- `lstm_pipeline_manifest.csv`

For each additive age bin, it writes:

- `bin_<AGE-BIN>/config.json`
- `bin_<AGE-BIN>/vocab.json`
- `bin_<AGE-BIN>/model.pt`
- `bin_<AGE-BIN>/training_summary.csv`

It also writes sibling files in each child folder:

- `chi.lstm_generated.csv`
- `chi.shared_caretaker_contexts.with_lstm.csv`
- `chi.surprisal_scoring_with_lstm.csv`

The final scoring file keeps:

- `context_k1`
- `context_k2`
- `context_k3`
- real child utterance
- random/unigram/bigram/trigram baselines
- LSTM generated columns
- `lstm_age_bin` provenance column

These files are inputs to the separate Mila scoring project. This repository
does not perform the actual large-scale surprisal scoring.

## Supervisor-Safe Summary

In one sentence:

> We train small word-level encoder-decoder LSTMs under additive developmental
> age-bin constraints: each model maps bounded recent caretaker context to the
> next child utterance using only training examples from the target bin and
> earlier bins, then generates child-like baseline utterances for rows in the
> target bin.

What is conditioned on:

- only prior caretaker utterances
- not future speech
- not the target child utterance at generation time

What is predicted:

- a child utterance baseline

What it controls:

- same-length variant controls production length
- free-length variant tests whether the model chooses similar utterance lengths
- additive age-bin training controls developmental information leakage

Why context is bounded:

- prevents the model from using an unbounded conversation history
- keeps it conceptually between n-grams and LLMs
