# Experiment Guidelines

Rules for running experiments and saving outputs.

## Output Locations

TODO: Define canonical output roots.

Candidate folders already present:

- `results/`
- `figs/utterance_distributions/`

## Naming Conventions

TODO: Define naming conventions for:

- scoring runs
- model names
- context sizes
- age bins
- baseline types
- dates or run ids

## Reproducibility Metadata

Each serious run should save:

- command used
- git commit or diff status
- config file, if any
- model name
- random seed
- input data paths
- output schema/version

TODO: Decide metadata file format.

## Random Seeds

TODO: Define default seed policy for random / unigram / bigram generation.

## Overwrite Policy

TODO: Decide whether runs may overwrite previous results.

Suggested default:

- Never overwrite important outputs without an explicit flag.
- Prefer timestamped or named run folders.

## Validation Before Analysis

TODO: Define checks to run before trusting a result file.

Possible checks:

- no target rows with `n_eval_tokens == 0`
- no punctuation-only target rows treated as normal scored rows
- required metadata columns present
- no context tokens counted as target tokens
