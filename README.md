# Communicative Efficiency

Working title: **On Communicative Efficiency of Child Language Use**

This repository studies communicative efficiency in child language using
CHILDES / CHAT transcript data.

This README is intentionally a skeleton. Fill it in as the project stabilizes.

## Project Goal

- The goal of this project is to study the developmental trajectory of children communicative efficiency by studying the changes in surprisal values of their utterances as they age and master more and more natural language production. 

- To do this, we rely on transcriptions from naturalistic speech settings.


## Repository Layout

```text
data/       raw and preprocessed data
docs/       project design, notes, roadmap, and agent guidance
src/        project source scripts
tests/      simple unit tests and editable examples
results/    generated analysis outputs
figs/       generated figures and plot summaries
configs/    future run/config files
scripts/    future workflow wrappers
notebooks/  exploratory notebooks
```

## Quick Start

TODO: Add setup instructions.

Current test command:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

## Documentation

- `AGENTS.md`: high-level instructions for coding agents.
- `TODO.md`: lower-level working task list.
- `docs/design.md`: scientific and technical design.
- `docs/roadmap.md`: phased roadmap.
- `docs/notes.md`: living project memory.
- `docs/guidelines/`: coding, scoring, and experiment rules.

## Data

TODO: Describe data access, raw-data policy, and expected folder layout.

Important principle: raw data should not be overwritten.

This project will usually have two types of data : raw data in the CHAT format from the CHILDES project that is never to be overwritten, only used by `preprocess_datasets.py` to generate our preprocessed data set. 

This preprocessed data is to be used in three ways : 

1. To be scored via surprisal 
2. To generate utterances using frequentists models (random language model, unigram and bigram models)
3. To generate utterances using LLMs that are trained on all datasets, holding out one, and trying to predict it. 

## Status

TODO: Summarize what currently works and what is experimental.
