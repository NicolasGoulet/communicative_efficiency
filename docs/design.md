# Project Design

Human-facing design notes for the communicative-efficiency project.

This file can be longer and more scientific than `AGENTS.md`. Use it to record
the concepts, assumptions, and analysis choices that should guide coding work.

## Project Motivation

The goal of this project is to study the developmental trajectory of communicative efficiency in children. TODO COMPLETE.  

## Core Concepts

### Informativeness

TODO: Define how informativeness is currently measured.

Possible measure family:

- token surprisal
- utterance total surprisal
- mean bits per evaluated token

### Complexity / Effort

WORK IN PROGRESS : This section is not complete yet, but it describes our current approaches to modeling complexity and effort.

There are many possible ways of quantifying effort based on text, right now we are using :

- word count : This is the most straightforward : the effort needed to produce an utterance is the sum of the used words
- morpheme count : A bit more refined : the effort needed to produce an utterance is the sum of the produced morphemes
- syllable count :  
- token count : This is not really relevant but is implicitely considered / used. After all, we are taking our utterances and tokenizing them using our used LLM's tokenizer. We are preserving the relation between the original word and its tokens.

### Efficiency

TODO: Define the current efficiency metric or analysis model.

Possible measure family:

- surprisal per word
- surprisal per morpheme
- bits per syllable
- model-based relation between informativeness and complexity

## Data Sources

Current corpora visible in this repo:

- Brown
- Manchester
- Providence
- Hall

For the moment,  we are only using Brown, Manchester and Providence, but we plan on adding and ussing many more data sources.

## Preprocessing Assumptions

Authoritative preprocessing script:

- `src/prepare_datasets.py`

Current output families:

- child utterances
- mother utterances
- father utterances
- combined caretaker utterances
- child/session metadata

### Handling the CHAT format

The preprocessing keeps two versions of each utterance:

- `utterance`: the original CHAT main-tier text.
- `utterance_clean`: a cleaned version used for word counts, syllable counts, and later scoring.

The goal is to remove CHAT transcription markers without losing actual spoken words.

Current rules:

- Keep only `CHI`, `MOT`, and `FAT` speaker tiers.
- Merge `MOT` and `FAT` into a combined caretaker file.
- Remove timecodes, bracketed annotations, parenthetical comments, and untranscribed forms like `xxx`, `yyy`, and `www`.
- Keep the words inside `<...>` but remove the angle brackets.
- Remove CHAT marker tokens starting with `+`, `@`, `&`, or `0`.
- Use a strict `@` policy:
  - keep `word@c`, `word@b`, and `word@o` as `word`;
  - drop other `@` forms.
- Compute word and syllable counts from `utterance_clean`, not from the raw utterance.
- Use `%mor:` tiers to compute `morph_count` when available.
- Preserve provenance columns such as `child_id`, `session_id`, `file`, and `line_no`.

## Scoring Protocol

TODO: Fill this in before implementing serious scoring changes.

Important principle:

When context is provided to a model, context tokens may appear in the input, but
reported surprisal should be computed only over the target utterance.

## Context Conditions

Context windows will always consider only the `k` previous utterances of the caretakers (either the mother or the father).

The currently used values of `k` when scoring the utterances of children, the baselines counterpart (produced by frequentist models) and the utterances of caretakers themselves are : 0 (no context), 1, 2 and 3.

## Baselines

Current baseline families represented in source code:

- random utterance generation
- unigram utterance generation
- bigram utterance generation

But soon we will add : 

- LLM model generation : for each existing dataset, we train a simple LLM (most probably an architecture from the BabyLM challenge). We then train it on every data BUT the currently considered dataset. We then generate for each utterance an utterance of the same length but generated with the trained LLM. It remains to be determined what will be the logic for determining the used vocabulary of the output head.

## Planned Analyses

TODO: Describe the analysis plan.

## Open Scientific Questions

- TODO: What does "efficiency" mean for the first paper draft?
- TODO: Which complexity measure is primary?
- TODO: Are age effects analyzed continuously, by bins, or both?
- TODO: Which corpora are included in the main analysis?

## Data Provenance Requirements

Every analysis row should preserve enough information to recover:

- dataset / corpus
- child
- session
- speaker category
- utterance id or row id
- child age, if available
- original utterance
- cleaned utterance

TODO: Write exact required columns.
