# AGENTS.md

Persistent guidance for coding agents working in this repository.

This file is the high-level project compass. Lower-level tasks belong in
`TODO.md`; longer design discussion belongs in `docs/design.md`; running notes
and decisions belong in `docs/notes.md`.

## Project Overview

Working title: **On Communicative Efficiency of Child Language Use**

This repository is for data preparation, cleaning, diagnostics, baseline
utterance generation, metadata, plots, and bundle creation for CHILDES / CHAT
communicative-efficiency analyses.

This repository is **not** the main place for large-scale LLM surprisal scoring.
Scoring is done in the separate Mila project, currently referred to as
`compute_surprisal_mila`. This repo may create scorer-ready bundles, but the
actual scoring runs and scored outputs should remain outside Git.

Broad scientific objects:

- **informativeness**: surprisal / likelihood, computed downstream in the Mila
  scoring project.
- **effort / complexity**: utterance length, morphemes, syllables, MLU-style
  measures, and related diagnostics prepared here.
- **efficiency**: downstream relation between informativeness and effort,
  expected to be analyzed in a future analysis-focused project.

## Current Active Data State

Current strict naturalistic big-cleaned bundle:

```text
data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

This bundle uses additive random/unigram/bigram/trigram dictionaries with one
first bin `006-023`, followed by 6-month bins:

```text
024-029, 030-035, 036-041, 042-047, 048-053, 054-059, 060-065
```

Strict naturalistic corpora in the current bundle:

- Belfast
- Brown
- Demetras1
- Forrester
- Kuczaj
- Lara
- MPI-EVA-Manchester
- Manchester
- Post
- Providence
- Sachs
- Weist
- Wells

Generated/scoring-ready row counts for this current bundle:

- 79 child folders
- 1,140,218 child scoring rows
- 1,470,154 caretaker scoring rows

The current data needed for LSTM generation should be transferred between
machines with `rsync`, not Git.

## Current LSTM Focus

Next likely work: run or modify the LSTM utterance-generation pipeline on a GPU
machine, then produce LSTM generated utterance columns for later surprisal
scoring in the Mila project.

Read these first:

1. `docs/lstm-baseline-pipeline.md`
2. `configs/lstm_baseline_16gb_smoke.json`
3. `configs/lstm_baseline_16gb_default.json`
4. `src/run_lstm_baseline_pipeline.py`
5. `src/generate_lstm_utterances.py`
6. `tests/test_lstm_baseline_pipeline.py`
7. `tests/test_lstm_generation.py`

The LSTM pipeline:

- trains a small word-level encoder-decoder LSTM;
- encodes bounded prior caretaker context;
- decodes child-like utterance baselines;
- supports same-length and free-length generation variants;
- writes generated LSTM sibling files and compact scoring-ready files;
- does not compute LLM surprisal.

Do not claim that an LSTM was trained unless a real training command was run and
the run artifacts exist.

## Repository Map

```text
communicative_efficiency/
|-- AGENTS.md
|-- TODO.md
|-- configs/
|   |-- lstm_baseline_16gb_default.json
|   `-- lstm_baseline_16gb_smoke.json
|-- data/                  # ignored by Git; transfer with rsync/Globus
|-- docs/
|   |-- datasets.md
|   |-- design.md
|   |-- general-overview.md
|   |-- llm-models.md
|   |-- lstm-baseline-pipeline.md
|   |-- ngram-models.md
|   |-- notes.md
|   |-- preprocessed_datasets.md
|   `-- project_deep_research_handoff.md
|-- figs/                  # ignored by Git unless explicitly needed elsewhere
|-- results/               # ignored by Git; generated outputs and bundles
|-- src/
|-- tests/
|-- scripts/
`-- notebooks/
```

## Important Source Files

- `src/prepare_datasets.py`: Stage 0 CHAT / CHILDES preprocessing.
- `src/create_big_cleaned_dataset.py`: consolidated strict-naturalistic bundle
  creation.
- `src/build_age_word_dicts.py`: additive age-binned vocabulary and count
  dictionaries.
- `src/add_random_and_unigram_utterances.py`: matched-length random, unigram,
  bigram, and trigram baseline utterance generation.
- `src/create_shared_caretaker_contexts.py`: role-specific caretaker context
  windows, currently `context_k1`, `context_k2`, `context_k3`.
- `src/create_minimal_surprisal_scoring_csvs.py`: compact child/caretaker
  scoring-ready CSVs.
- `src/create_pbm_early_baseline_rescoring_bundle.py`: PBM-only `006-023`
  generated-baseline handoff bundle for Mila rescoring.
- `src/generate_lstm_utterances.py`: word-level LSTM model code.
- `src/run_lstm_baseline_pipeline.py`: config-driven LSTM orchestration.
- `src/plot_distributions.py`: distribution plots and summaries.

## Data And Git Policy

Large data and generated outputs should not be pushed to Git.

Ignored by `.gitignore`:

- `data/`
- `results/`
- `figs/`
- generated PDFs/images under docs
- archives and tarballs
- model checkpoints
- local environments and caches

Use `rsync` or Globus for machine-to-machine data transfer. Use Git for:

- source code
- tests
- configs
- Markdown documentation
- lightweight project metadata

Important: if bulky files were already tracked before `.gitignore` was updated,
they must be removed from the Git index with `git rm --cached`; do not delete
local data unless explicitly asked.

## How Agents Should Work Here

Before editing code:

1. Read this file.
2. Read `TODO.md`.
3. Read relevant docs under `docs/`.
4. Inspect directly involved source files and tests.

Default behavior:

- Make small, reviewable changes.
- Preserve raw data.
- Preserve row provenance wherever possible.
- Add or update tests for behavior changes.
- Prefer simple, explicit code over clever abstractions.
- Keep documentation synchronized when changing file formats or assumptions.
- After meaningful work, update `TODO.md` and `docs/notes.md` with dates,
  commands, outputs, and verification.

## Testing

Current full unit-test command:

```bash
.venv/bin/python -m unittest discover -s tests
```

If `uv` is available, this also works:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

Latest known full-suite check on 2026-05-28: 145 tests passing.

## Project-Specific Constraints

- Do not overwrite raw CHILDES / CHAT data.
- Do not silently drop utterance rows without recording why.
- Do not invent scientific results or pretend a model was run.
- Do not treat context tokens as target tokens when computing target surprisal.
- Do not treat empty or punctuation-only utterances as normal scored utterances.
- Do not change output schemas without documenting the change.
- Do not run GPU LSTM training on the laptop.

## Data Handling Rules

This is a data-heavy research project. Do not load or print entire datasets into
the chat/context.

When inspecting data:

- Prefer `head`, `tail`, `wc -l`, `du -h`, and column/schema summaries.
- For CSV files, inspect shape, columns, dtypes, missing-value counts, and at
  most 20 example rows.
- Never run `cat` on large CSV/JSON/JSONL files.
- Never paste full datasets into Markdown files.
- Do not commit raw data unless explicitly instructed.
- Treat `data/raw_data/` as immutable.
