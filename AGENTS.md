# AGENTS.md

Persistent guidance for coding agents working in this repository.

This file is the high-level project compass. Lower-level tasks belong in
`TODO.md`; longer design discussion belongs in `docs/design.md`.

## Project Overview

Working title: **On Communicative Efficiency of Child Language Use**

This project studies communicative efficiency in child language using CHILDES /
CHAT transcript data. The broad aim is to relate:

- **informativeness**: TODO define current surprisal / likelihood measure
- **complexity or effort**: TODO define current length, morpheme, syllable, MLU measures
- **efficiency**: TODO define current ratio or regression-style metrics

Main corpora currently represented in the repo:

- Brown
- Manchester
- Providence
- Hall

## Repository Map

```text
communicative_efficiency/
|-- data/
|   |-- raw_data/
|   |   `-- Hall/
|   `-- preprocessed_data/
|       |-- Brown/
|       |-- Hall/
|       |-- Manchester/
|       |-- Providence/
|       `-- filelists/
|-- docs/
|   |-- datasets.md
|   |-- general-overview.md
|   |-- llm-models.md
|   |-- ngram-models.md
|   `-- guidelines/
|-- figs/
|   `-- utterance_distributions/
|-- results/
|-- src/
|-- tests/
|-- configs/
|-- scripts/
`-- notebooks/
```

## Important Source Files

- `src/prepare_datasets.py`: Stage 0 CHAT / CHILDES preprocessing. This is explored more in details in `design.md`
- `src/build_age_word_dicts.py`: age-binned vocabulary and count dictionaries.
- `src/add_random_and_unigram_utterances.py`: random, unigram, and bigram baseline utterance generation. It is important to note that every generated utterances using these models are of the same lenghts of a corresponding *real* generated utterance from a child. This means, for every given cleaned utterances we have in our data, we generate an utterance of the same length using a random, unigram and bigram model. 
- `src/create_contexts.py`: This script is for adding different context windows of *k* utterances for scoring utterances. The only utterances used are from caretakers (the parents, either MOT or FAT roles in the CHAT format). Right now, we are only considering k={1,2,3}. This means we are checking the effects of considering up to the three previous utterances of the caretakers in the context.  
- `src/create_context_caretakers.py`: This is the same as the previous script but for the utterances of parents.
- `src/new_create_parallel_data.py`: This file splits data into chunks of a 1000 utterances per csv file that are then sent to a computing cluster in order to score utterances.
- `src/plot_distributions.py`: distribution plots and summaries.

## How Agents Should Work Here

Before editing code:

1. Read this file.
2. Read `TODO.md`.
3. Read any relevant design/guideline docs under `docs/`.
4. Inspect the files directly involved in the requested task.

Default behavior:

- Make small, reviewable changes.
- Preserve raw data.
- Preserve row provenance wherever possible.
- Add or update tests for behavior changes.
- Prefer simple, explicit code over clever abstractions.
- Keep documentation synchronized when changing file formats or assumptions.

## Testing

Current simple unit-test command:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

TODO: Add any slower validation commands here.

## Project-Specific Constraints

- Do not overwrite raw CHILDES / CHAT data.
- Do not silently drop utterance rows without recording why.
- Do not invent scientific results or pretend a model was run.
- Do not hardcode machine-specific absolute paths.
- Do not treat context tokens as target tokens when computing target surprisal.
- Do not treat empty or punctuation-only utterances as normal scored utterances.
- Do not change output schemas without documenting the change.

## Human Decisions Needed

- TODO: authoritative cleaned utterance column.
- TODO: current active corpora.
- TODO: canonical age-bin sizes.
- TODO: scoring models to support.
- TODO: required output columns for scored files.
- TODO: policy for empty / punctuation-only cleaned utterances.

## Data handling rules

This is a data-heavy research project. Do not load or print entire datasets into the chat/context.

When inspecting data:
- Prefer `head`, `tail`, `wc -l`, `du -h`, and column/schema summaries.
- For CSV files, inspect `shape`, `columns`, `dtypes`, missing-value counts, and at most 20 example rows.
- Never run `cat` on large CSV/JSON/JSONL files.
- Never paste full datasets into Markdown files.
- Do not commit raw data unless explicitly instructed.
- Treat `data/raw_data/` as immutable.