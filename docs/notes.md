# Notes

Living project memory: discoveries, decisions, bugs, commands that worked, and
current state. Prefer dated notes.

## Current State

TODO: Summarize what currently works.

Known current structure:

- Source code: `src/`
- Tests: `tests/`
- Preprocessed data: `data/preprocessed_data/`
- Raw Hall data: `data/raw_data/Hall/`
- Distribution figures: `figs/utterance_distributions/`

## Recent Decisions

- TODO: YYYY-MM-DD - Decision and reason.

## Commands That Worked

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

TODO: Add preprocessing, dictionary-building, and plotting commands as they are
confirmed.

## Known Bugs

- TODO: Add bug, path, symptom, and reproduction command.

## Open Questions

- TODO: Which cleaned utterance column is authoritative?
- TODO: Which corpora are active?
- TODO: Which baselines are active?
- TODO: What is the empty-utterance policy?

## Important Paths

- `src/prepare_datasets.py`
- `src/build_age_word_dicts.py`
- `src/add_random_and_unigram_utterances.py`
- `src/plot_distributions.py`
- `docs/ngram-models.md`
- `docs/llm-models.md`
