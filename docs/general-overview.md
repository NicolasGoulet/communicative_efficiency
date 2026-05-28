## General Introduction

This document serves as a `General Overview` of everything that was accomplished in this project thus far.

## Quick Overview

- Pipeline to score surprisal of utterances in naturalistic speech settings (mostly from CHILDES)
- We screened various small open-source LLMs. We selected the one that was the least surprised in general by children utterances -> Mistral with 7B.
- Can be scored with or without context. Context refers to utterances other than the one being scored
- When a context window is used, it is made of `k` utterances (right now we only considered $k={1,2,3}$)
- These utterances are exclusively sampled from caretakers utterances (mothers and fathers)
- We use precise rules for preprocessing the CHAT format described in a following section
- Right now, we only worked with Hall, Brown, Manchester, and Providence. These are English and non-clinical datasets.
- We also generate baseline utterances with frequentist models (random, unigram, bigram, and trigram), plus an experimental LSTM baseline, also described in a following section.
- This document ends with possible next steps for the short-term

## CHAT Format

CHAT transcripts contain both spoken utterances and transcription markup. For this project, we kept only the main utterance tiers for children and caretakers: `CHI`, `MOT`, and `FAT`.

For each utterance, we preserved:

- the original CHAT text in `utterance`;
- a cleaned version in `utterance_clean`;
- provenance information such as child, session, file, line number, speaker, and age.

In the cleaned version, we removed CHAT-specific markup that should not be treated as spoken lexical content, including:

- timecodes;
- bracketed annotations;
- parenthetical comments and pauses;
- retracing, overlap, and other `+` markers;
- omission markers such as `0` or `0word`;
- unintelligible material such as `xxx`, `yyy`, and `www`;
- unsupported special-form markers beginning with `@` or `&`.

Word-like CHAT special forms are preserved by stripping the marker suffix. This
includes family-specific forms, child-invented forms, dialect forms, babbling,
interjections, letters, letter plurals, multiple-letter strings, neologisms,
onomatopoeias, phonologically consistent forms, and word play.

Utterances with no remaining words after cleaning were excluded from scoring.
Operationally, diagnostic scripts treat an utterance as scorable when
`utterance_clean` contains at least one word token.

The derived script `src/special_forms_per_utterance.py` audits these forms in
raw CHAT data while using the same cleaning policy as preprocessing. It writes
per-utterance counts, marker summaries by dataset/speaker, marker summaries by
age bin, full observed `@` code summaries, and capped examples under
`results/special_forms/`.

The derived script `src/fillers_and_shortenings_per_utterance.py` gives the
same child-versus-caretaker portrait for filler-like tokens and parenthetical
shortenings.

## Generating Baseline Utterances

We generated baseline utterances to compare with true utterances from children. Here are the principles followed :

- For every utterance in our dataset, we generate an utterance of the same length (in words, not controlling for number of syllables or morphemes)
- We create vocabularies out of `k`-month bins, with $k=6$ as the current default.
- The bins are additive: each written bin contains that age window plus all previous age windows.
- For each 6-month window, we compute unigrams, bigrams, and trigrams. For the random language model, we simply sample from vocabularies by assigning the same probability to every word within that cumulative bin.
- For bigram and trigram counting/generation, the first child word can use the most recent prior caretaker utterance as context.
- The default LSTM baseline is encoder-decoder: the encoder reads a configurable tail of recent caretaker context and the decoder generates the child utterance.
- These vocabularies are built using all the curently used datasets (Brown, Manchester and Providence).

## Next Steps

- Expending to more datasets, both clinical and non-clinical (see attached document with list of plausible datasets to use for now)
- Generating baseline utterances with an LLM : for every dataset we use, train an LLM on every dataset except the currently considered one and generate utterances of the same length
- More thorough statistical analyses
- Testing with larger and larger models to see at which point they start being more surprised by natural language than their smaller counterparts.
