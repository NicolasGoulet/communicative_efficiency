# Project Design

Human-facing design notes for the communicative-efficiency project.

This file can be longer and more scientific than `AGENTS.md`. Use it to record
the concepts, assumptions, and analysis choices that should guide coding work.

## Project Motivation

The goal of this project is to study the developmental trajectory of communicative efficiency in children. TODO COMPLETE.  

## Core Concepts

### Informativeness

The initial project formulation distinguishes at least three related
informativeness families. We should keep them separate in code, tables, and
reports.

1. **Unconditional utterance prior, p(u).** A child utterance is informative
   when it is less expected under an utterance model. This can be approximated
   with n-gram models:

```text
p(u) = p(w1) * p(w2 | w1) * p(w3 | w2, w1) * ...
```

   In practice, we use truncated models such as unigram, bigram, and trigram
   baselines. Neural language models can provide the same family of measure.

2. **Direct contextual utterance probability, p(u | c).** A child utterance is
   informative relative to the caretaker context `c` in which it occurs. This
   is the family used by the current Mistral contextual surprisal work: context
   tokens condition the model, but reported target surprisal is computed only
   over the child utterance tokens.

3. **Bayes decomposition of contextual probability.** The initial formulation
   also proposes:

```text
p(u | c) = p(c | u) * p(u) / p(c)
```

   Equivalently, for comparing candidate utterances within the same fixed
   context `c`, the context normalizer `p(c)` is constant and the ranking can
   be approximated by:

```text
log p(u | c) = log p(c | u) + log p(u) + constant_for_c
```

   This is not the same product as our direct Mistral `p(u | c)` scoring. It
   requires a separate estimate of the utterance prior `p(u)` and a separate
   estimate of the context likelihood or discourse fit term `p(c | u)`. The
   prior can initially come from additive age-bin n-gram or LSTM models. The
   likelihood term needs its own method, for example a reverse discourse model
   that estimates how compatible a caretaker context is with a candidate child
   utterance.

Current measured informativeness columns are:

- token surprisal
- utterance total surprisal
- mean bits per evaluated token
- direct contextual surprisal under the selected scorer/context window

### Complexity / Effort

WORK IN PROGRESS: This section describes the current and planned approaches to
modeling complexity and production effort. The initial project document
explicitly named MLU-style complexity as part of the original formulation, so
this should be treated as core rather than as later polish.

There are many possible ways of quantifying effort based on text, right now we are using :

- word count: the simplest orthographic MLU-style measure.
- morpheme count: a more refined MLU-style grammatical effort measure when
  CHAT morphology is available or recoverable.
- syllable count: a phonological/phonotactic effort proxy.
- phoneme count and phonotactic shape: planned measures for spoken-form effort.
- token count: implicit in LLM scoring because each utterance is tokenized by
  the scorer. It is useful as a scoring diagnostic but should not replace
  child-language effort measures.

Additional complexity families from the initial formulation and later notes:

- **Orthographic MLU:** mean words or characters per utterance. This is easy,
  CPU-only, and already partly represented by word and character counts.
- **Grammatical MLU:** mean morphemes per utterance, approximating grammatical
  complexity in child language.
- **Phonological/phonotactic complexity:** syllables, phonemes, syllable
  structure, and related child-language measures such as word complexity or
  mean babbling level where the data support them.
- **Dependency length / syntactic complexity:** dependency distance, number of
  dependencies, parse depth, or related parser-derived measures. This needs a
  feasibility audit because toddler utterances and CHAT transcripts can be hard
  for general parsers.
- **Lexical complexity:** vocabulary size, age-bin type counts, type-token
  ratio, moving-average lexical diversity, lexical rarity, and possibly
  age-conditioned word frequency. This is distinct from utterance length.

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

- `chi.csv`: child utterances.
- `caretakers.csv`: mother and father utterances merged in CHAT order.
- `testing.csv`: optional combined CHI/MOT/FAT inspection file written only
  when `prepare_datasets.py --testing` is used.

Current preprocessing split:

- `src/cleaning.py` owns the CHAT utterance cleaning policy.
- `src/prepare_datasets.py` owns corpus/file discovery and CSV writing, and
  calls `cleaning.py` for raw-to-cleaned utterance conversion.
- `prepare_datasets.py` does not compute word counts, syllable counts,
  morpheme counts, contexts, generated utterances, or scoring inputs.
- Current CSV columns are: `dataset`, `child_id`, `source_group`,
  `session_id`, `age_raw`, `age_months`, `sex`, `file`, `line_no`,
  `reference_line`, `utt_id`, `utt_id_role`, `speaker`, `utterance`,
  `utterance_clean`, `cleaned_is_empty`.
- `reference_line` is formatted as `<file>:<line_no>` and is included in the
  split files and the combined `testing.csv` so row provenance can be audited.
- All CHI/MOT/FAT main-tier rows are kept in preprocessing output. Rows whose
  cleaned utterance is empty keep an empty `utterance_clean` value and are
  marked with `cleaned_is_empty` instead of being silently dropped.

CSV text fields are quoted on write so CHILDES age strings such as `1;04.27`
do not get split into extra spreadsheet columns by importers that also enable
semicolon separators.

### Handling the CHAT format

The preprocessing keeps two versions of each utterance:

- `utterance`: the original CHAT main-tier text.
- `utterance_clean`: a cleaned version for later scoring and downstream
  preprocessing.

The goal is to remove CHAT transcription markers without losing actual spoken words.
A scorable utterance is one whose cleaned form contains at least one word token;
utterances that clean to empty text or punctuation-only text are not treated as
normal scoring targets.

Current rules:

- Keep only `CHI`, `MOT`, and `FAT` speaker tiers.
- Merge `MOT` and `FAT` into a combined caretaker file.
- Remove timecodes, bracketed annotations, parenthetical comments, and untranscribed forms like `xxx`, `yyy`, and `www`.
- Keep the words inside `<...>` but remove the angle brackets.
- Remove unsupported CHAT marker tokens starting with `+`, `@`, `&`, or `0`.
- Use a strict `@` policy:
  - keep the lexical base of word-like special forms marked with `@b`, `@c`,
    `@d`, `@f`, `@i`, `@n`, `@o`, `@p`, and `@wp`;
  - keep letter forms marked with `@k`, `@l`, and `@ls` as their lexical base,
    since letters are valid discourse in games, spelling talk, and similar
    contexts;
  - drop other `@` forms.
- Preserve provenance columns such as `child_id`, `session_id`, `file`, and `line_no`.

### Special-form diagnostics

`src/special_forms_per_utterance.py` is the current diagnostic script for
checking how often CHAT special `@` forms occur in utterances that would be
used downstream. It reads raw CHAT files through the same discovery and
cleaning path as `prepare_datasets.py`, excludes empty-cleaned utterances by
default, requires at least one cleaned word by default, and writes derived CSV
reports under `results/special_forms/`.

The default target markers are `@b`, `@c`, `@d`, `@f`, `@i`, `@k`, `@l`,
`@ls`, `@n`, `@o`, `@p`, and `@wp`. The script also records other observed
full `@` codes in `special_forms_by_full_code.csv` so unsupported or unexpected
forms can be audited separately from the target marker set.

Reports include both individual speaker tiers and the project-level
`speaker_group` split: `CHILD` for `CHI`, and `CARETAKERS` for `MOT`/`FAT`.

`src/fillers_and_shortenings_per_utterance.py` performs the same style of
diagnostic for filler-like tokens and parenthetical shortenings such as
`y(ou)`, `an(d)`, and `(be)cause`. It writes per-utterance counts, child versus
caretaker summaries, age-bin summaries, and capped examples under
`results/fillers_shortenings/`.

`src/build_preprocessing_variant_probe.py` builds a small real-data probe set
for surprisal sensitivity checks. It selects compact utterances from raw CHAT
data and writes multiple scoring variants for each example, including current
cleaning, raw CHAT text, expanded parenthetical shortenings, filler removal,
preserved `@` suffixes, and dropped special-form tokens. The long-form CSV uses
`utterance_for_scoring` as the text column and includes `word_count` and
`morph_count` only so the current scoring script can apply its normal
eligibility checks.

`src/plot_diagnostic_analyses.py` turns the diagnostic CSVs into PNG/PDF
figures under `figs/diagnostic_analyses/`, including overview child-versus-
caretaker rates, dataset comparisons, marker/type breakdowns, age trajectories,
and preprocessing-probe summaries.

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
- trigram utterance generation
- LSTM utterance generation

The age-binned n-gram dictionaries are additive: each written bin contains the
current age window plus all earlier age windows in the same scope. Bigram and
trigram counts for child utterances use the latest prior caretaker utterance in
the same session as left context for utterance-initial child words.

The LSTM baseline in `src/generate_lstm_utterances.py` is a small neural
generation baseline. Its default architecture is `seq2seq_lstm`: an encoder
reads a configurable amount of previous caretaker context, and a decoder
generates the child utterance. The previous prefix-style version remains
available as `causal_lstm`; in that architecture, context tokens are included
before `<bos>` and masked out of the training loss. Both architectures generate
same-length child utterances. This script is meant to be easier to revise than
the final BabyLM-style generator.

Still planned:

- LLM model generation: for each existing dataset, we train a simple LLM (most probably an architecture from the BabyLM challenge). We then train it on every data BUT the currently considered dataset. We then generate for each utterance an utterance of the same length but generated with the trained LLM. It remains to be determined what will be the logic for determining the used vocabulary of the output head.

## Compute Placement And Repo Boundaries

This repository remains the project brain: data links, bundle creation,
analysis tables, supervisor-facing reports, and compact local diagnostics.
Large scoring and generation runs should live in smaller cluster-oriented
repositories.

Existing boundary:

- `compute_surprisal_mila`: Mila/HPC repo for Mistral and other neural
  surprisal scoring. This repo should receive only compact audited outputs via
  symlink or rsync.

New local sibling repos:

- `generate_baselines_mila`: cluster-ready baseline generation only. It should
  generate random, unigram, bigram, trigram, LSTM, and future generator
  utterances from scorer-ready inputs. It should not compute final Mistral
  surprisal.
- `bayes_efficiency_mila`: Bayes decomposition repo, especially `p(c | u)`
  likelihood scoring and posterior-style tables. This is conceptually
  different from direct target-token surprisal.
- `child_complexity_predictors`: lightweight predictor extraction repo for
  MLU, morphemes, syllables, phonemes, dependency length, and vocabulary-size
  predictors. This is CPU-first and should export compact tables back into
  this repo.

Compute classes:

- **CPU-only / CPU-first:** n-gram count dictionaries, random/unigram/bigram/
  trigram generation, word/character MLU, vocabulary-size predictors, lexical
  diversity, most aggregation, joins, audits, and plotting.
- **CPU-feasible but GPU-optimized:** LSTM training and generation, neural
  dependency parsing if selected, and small neural language-model experiments.
  These can run on CPU for smoke tests, but production should use Mila GPUs.
- **Mila GPU / cluster scoring:** Mistral scoring, large LLM generation,
  sampled-response cloud scoring, and any large neural estimate of `p(c | u)`.

## Planned Analyses

TODO: Describe the analysis plan.

## Open Scientific Questions

- TODO: What does "efficiency" mean for the first paper draft?
- TODO: Which complexity measure is primary?
- TODO: Should the main informativeness result be direct `p(u | c)`, Bayes
  decomposed `p(c | u) * p(u)`, or a transparent comparison of both?
- TODO: How should `p(c | u)` be approximated without pretending that the
  caretaker context temporally follows the child utterance?
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
