# Scoring Guidelines

Rules for language-model scoring in this project.

## Core Rule

If model input contains context plus a target utterance, reported surprisal must
be computed only for target utterance tokens.

TODO: Define the exact target-token masking strategy.

## No-Context Scoring

TODO: Define how the target utterance is formatted when scored alone.

Required outputs under discussion:

- `sum_bits`
- `mean_bits_per_token`
- `n_eval_tokens`

TODO: Confirm final column names.

## Context Scoring

TODO: Define context construction.

Possible context conditions:

- previous caretaker utterance, `k = 1`
- previous caretaker utterances, `k = 2`
- previous caretaker utterances, `k = 3`

TODO: Define separator text between context and target.
TODO: Define how context rows are selected.

## Empty Or Invalid Utterances

TODO: Fill in final policy.

Suggested policy to decide:

- Skip utterances with no valid target tokens.
- Record a skip reason.
- Do not assign fake scores.

## Metadata To Preserve

TODO: Confirm required columns.

Likely required:

- dataset
- child
- session id
- speaker
- utterance id
- age
- original utterance
- cleaned utterance
- model name
- context condition
- scoring command or config id

## Numerical Conventions

TODO: Define base of logarithms, tokenization details, and rounding policy.
