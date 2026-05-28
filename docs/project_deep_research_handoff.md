# Project Deep-Research Handoff

Last updated: 2026-05-21.

This document summarizes the current state of the project **On Communicative
Efficiency of Child Language Use**. It is meant as a standalone technical and
scientific handoff for a deep-research agent. It distinguishes what is already
implemented from what is conceptual, provisional, or not yet rerun after the
recent corpus expansion.

## 1. Executive Summary

The project studies communicative efficiency in child language using CHILDES /
CHAT transcript data. The core question is whether children, as they develop,
produce utterances that increasingly balance:

- **informativeness**: how much information or surprisal an utterance carries
  given its context;
- **complexity / effort**: how much linguistic material the utterance requires,
  measured with word, morpheme, syllable, or token counts;
- **efficiency**: the relation between information conveyed and effort used,
  especially when prior caretaker context makes parts of a message predictable.

The implemented pipeline currently does five major things:

1. Preprocesses CHAT transcripts into cleaned child and caretaker utterance CSVs.
2. Audits CHAT-specific phenomena such as special `@` forms, fillers, and
   parenthetical shortenings.
3. Builds additive age-binned random, unigram, bigram, and trigram baselines.
4. Generates same-length baseline utterances for real child utterances.
5. Creates caretaker-context and compact scoring CSVs for later surprisal
   scoring.

The project recently expanded from the original Brown / Manchester / Providence
core to a much larger set of English CHILDES corpora. The newest corpora are
Stage 0 preprocessed, but **the n-gram vocabularies, generated utterances,
context files, and minimal scoring files have not yet been regenerated for the
expanded corpus set**.

## 2. Research Framing

The external research review files are:

- `/home/apaixonada/Downloads/deep-research-report.md`
- `/home/apaixonada/Downloads/Communicative Efficiency in Child Language.pdf`

Both frame the project around a literature gap: existing work supports
communicative efficiency in children and caregiver speech, but direct large-scale
corpus evidence for children’s own spontaneous production is still limited.

The closest theoretical framing is:

- Efficient communication is not simply shorter speech. It is the conditional
  trade-off between production effort and successful recoverability.
- A short child response can reflect efficiency, but it can also reflect
  limited grammatical development, constrained question type, imitation,
  routine interaction, or low productivity.
- A stronger efficiency claim requires showing that children become
  **selectively brief or less explicit when context supports recovery**, and
  more explicit or less compressed when context does not.
- LM surprisal should be treated as one operationalization of contextual support,
  not as the only possible definition of informativeness.

The research review recommends broader outcomes than length alone:

- utterance length;
- MLU-like measures;
- referential explicitness;
- pronoun versus noun choice;
- optional omission;
- compression relative to context.

Current code is mostly built around utterance-level text, length/complexity
counts, and LM surprisal. Referential explicitness and omission coding are
conceptual future directions, not currently implemented.

## 3. Repository Map

Important top-level locations:

```text
communicative_efficiency/
|-- data/
|   |-- raw_data/
|   |-- zip_files/
|   `-- preprocessed_data/
|-- docs/
|-- figs/
|-- results/
|-- src/
|-- tests/
|-- pyproject.toml
|-- uv.lock
|-- TODO.md
`-- AGENTS.md
```

Current Python dependencies in `pyproject.toml`:

- `matplotlib`
- `numpy`
- `pandas`
- `scikit-learn`
- `scipy`
- `torch`

The current simple test command is:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

The last full test run during this development sequence passed with **100
tests**.

## 4. Current Dataset Status

The canonical current dataset status document is:

```text
docs/preprocessed_datasets.md
```

The current age-bin count tables are:

```text
results/utterance_age_tables/
```

### 4.1 Current Corpus Groups

The auditable grouping file is:

```text
results/corpus_groups/dataset_group_assignments.csv
```

Current groups:

- `naturalistic_caregiver_child`: strict default naturalistic caregiver-child
  corpora.
- `caregiver_child_structured_observation`: non-clinical caregiver-child data
  that should be kept separate from the stricter naturalistic default.
- `clinical_probe`: clinical or probe-style data kept separate from
  naturalistic analyses.
- `pending_download` or other non-default categories for corpora not currently
  usable.

### 4.2 Stage 0 Preprocessed Datasets

Stage 0 means that per-child `chi.csv` and `caretakers.csv` files exist under
`data/preprocessed_data/<Dataset>/<Child>/`.

| Dataset | Group | Strict Default | Child Folders | Child Non-Empty | Caretaker Non-Empty | Missing Child Age | Missing Caretaker Age | Downstream N-Gram/Context/Scoring? |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Belfast | naturalistic_caregiver_child | yes | 8 | 22,942 | 32,082 | 0 | 0 | no |
| Brown | naturalistic_caregiver_child | yes | 3 | 92,555 | 64,206 | 0 | 0 | yes |
| Champaign | caregiver_child_structured_observation | no | 44 | 106,349 | 141,136 | 0 | 0 | no |
| Cummings | clinical_probe | no | 21 | 22,183 | 0 | 0 | 0 | no |
| Demetras1 | naturalistic_caregiver_child | yes | 1 | 6,842 | 8,270 | 0 | 0 | no |
| EHS | caregiver_child_structured_observation | no | 126 | 45,930 | 109,720 | 46 | 59 | no |
| Forrester | naturalistic_caregiver_child | yes | 1 | 6,664 | 8,890 | 0 | 0 | no |
| Kuczaj | naturalistic_caregiver_child | yes | 1 | 37,109 | 28,223 | 0 | 0 | no |
| Lara | naturalistic_caregiver_child | yes | 1 | 49,328 | 81,449 | 0 | 0 | no |
| MPI-EVA-Manchester | naturalistic_caregiver_child | yes | 4 | 462,100 | 546,929 | 0 | 0 | no |
| Manchester | naturalistic_caregiver_child | yes | 12 | 232,614 | 342,246 | 0 | 0 | yes |
| Post | naturalistic_caregiver_child | yes | 3 | 8,068 | 18,387 | 0 | 0 | no |
| Providence | naturalistic_caregiver_child | yes | 6 | 121,816 | 262,451 | 626 | 522 | yes |
| Sachs | naturalistic_caregiver_child | yes | 1 | 16,344 | 11,977 | 0 | 0 | no |
| Weist | naturalistic_caregiver_child | yes | 6 | 46,347 | 33,556 | 0 | 0 | no |
| Wells | naturalistic_caregiver_child | yes | 32 | 37,967 | 31,488 | 0 | 0 | no |

Totals across Stage 0 preprocessed data:

- child folders: 270
- child rows: 1,518,309
- non-empty cleaned child utterances: 1,315,158
- caretaker rows: 1,789,736
- non-empty cleaned caretaker utterances: 1,721,010
- child rows missing `age_months`: 672
- caretaker rows missing `age_months`: 581
- CSV row-width issues: 0
- blank-header files: 0

### 4.3 Not Currently Preprocessed

- **Thomas**: discussed as a strict candidate, but `Thomas.zip` was not present
  in `data/zip_files` at the last check.
- **Hall**: listed in the broader project overview, but there is no current
  `data/preprocessed_data/Hall/` directory in this checkout.

### 4.4 Child Versus Caretaker Age-Bin Distribution

Counts below are non-empty cleaned utterances with usable `age_months`. Bins are
6-month bins. For example, `024-029` means 24 through 29 months.

| Age Bin | Child Utterances | Caretaker Utterances | Total |
| --- | ---: | ---: | ---: |
| 006-011 | 148 | 2,665 | 2,813 |
| 012-017 | 12,649 | 70,749 | 83,398 |
| 018-023 | 86,318 | 176,594 | 262,912 |
| 024-029 | 349,855 | 491,618 | 841,473 |
| 030-035 | 321,362 | 417,307 | 738,669 |
| 036-041 | 258,606 | 288,387 | 546,993 |
| 042-047 | 88,118 | 87,451 | 175,569 |
| 048-053 | 96,527 | 95,968 | 192,495 |
| 054-059 | 56,199 | 46,726 | 102,925 |
| 060-065 | 33,700 | 36,435 | 70,135 |
| 066-071 | 6,889 | 5,766 | 12,655 |
| 072-077 | 1,171 | 596 | 1,767 |
| 078-083 | 1,455 | 182 | 1,637 |
| 084-089 | 1,642 | 0 | 1,642 |

Full per-dataset tables live in:

```text
results/utterance_age_tables/all_preprocessed_utterance_age_bin_tables.md
results/utterance_age_tables/all_preprocessed_by_dataset_child_vs_caretaker_by_age_bin_6m_long.csv
results/utterance_age_tables/all_preprocessed_by_dataset_child_vs_caretaker_by_age_bin_6m_wide.csv
```

## 5. Stage 0 CHAT Preprocessing

Main scripts:

```text
src/cleaning.py
src/prepare_datasets.py
```

### 5.1 Output Structure

For each dataset and child-like unit, Stage 0 writes:

```text
data/preprocessed_data/<DATASET>/<CHILD>/chi.csv
data/preprocessed_data/<DATASET>/<CHILD>/caretakers.csv
data/preprocessed_data/<DATASET>/<CHILD>/testing.csv     # only when --testing
```

`chi.csv` contains only child rows. `caretakers.csv` contains caretaker rows.
`testing.csv`, when present, contains the combined rows for manual inspection.

Current Stage 0 columns:

```text
dataset
child_id
source_group
session_id
age_raw
age_months
sex
file
line_no
reference_line
utt_id
utt_id_role
speaker
utterance
utterance_clean
cleaned_is_empty
```

`reference_line` is formatted as `<file>:<line_no>`.

### 5.2 Cleaning Policy

The project preserves both:

- `utterance`: original CHAT main-tier text;
- `utterance_clean`: cleaned text for downstream analysis.

Rows are **not silently dropped** during Stage 0. If cleaning removes all
lexical material, `utterance_clean` is blank and `cleaned_is_empty` is set.

Current cleaning behavior:

- remove CHAT timecodes;
- remove bracketed annotations;
- remove parenthetical pauses/comments;
- unwrap `<...>` spans while preserving the words inside;
- remove unintelligible `xxx`, `yyy`, `www`;
- remove unsupported `+`, `@`, `&`, and `0` marker tokens;
- preserve common filler markers such as `&-uh`, `&-um`, `&-er`, `&-eh` by
  converting them to lexical filler forms;
- preserve terminal `.`, `!`, `?` when recoverable after CHAT timing markup.

Current strict `@` special-form policy keeps the lexical base of:

- `@b`: babbling
- `@c`: child-invented form
- `@d`: dialect form
- `@f`: family-specific form
- `@i`: interjection / interaction
- `@k`: multiple letters or strings of letters
- `@l`: letter
- `@ls`: letter plural
- `@n`: neologism / over-regularization
- `@o`: onomatopoeia
- `@p`: phonologically consistent form
- `@wp`: word play

Other `@` forms are dropped from the cleaned text.

### 5.3 Scorable Utterance Rule

The operational scorable rule used in diagnostics is:

```text
utterance_clean contains at least one word token
```

Punctuation-only and empty-cleaned rows are not treated as normal scoring
targets.

### 5.4 Dataset-Specific Preprocessing Notes

- `Hall` has special historical layout support in code, but is not currently
  preprocessed in this checkout.
- `MPI-EVA-Manchester` uses filename-age fallback for files with blank CHI `@ID`
  age.
- `Champaign` and `EHS` use measurement-folder or header-comment age fallbacks.
- `Lara` includes `ELS` as a grandmother speaker; preprocessing keeps `ELS` in
  `caretakers.csv` alongside `MOT` and `FAT`.
- Direct-root corpora such as `Lara`, `Sachs`, `Kuczaj`, `Demetras1`, and
  `Forrester` are grouped as one child-like unit even when `.cha` files live
  directly under the corpus root.

## 6. Diagnostic Analyses For Special Forms, Fillers, And Shortenings

Main scripts:

```text
src/special_forms_per_utterance.py
src/fillers_and_shortenings_per_utterance.py
src/build_preprocessing_variant_probe.py
src/plot_diagnostic_analyses.py
```

These diagnostics were run for:

```text
Brown, Manchester, Providence
CHI, MOT, FAT
```

Main figure folder:

```text
figs/diagnostic_analyses/brown_manchester_providence_chi_mot_fat/
```

Recommended figures from the generated README:

- `overview_utterance_rates_child_vs_caretakers.png`
- `dataset_utterance_rates_child_vs_caretakers.png`
- `special_marker_rates_child_vs_caretakers.png`
- `filler_type_rates_child_vs_caretakers.png`
- `shortening_top_parenthetical_texts.png`
- `age_bin_counts_and_phenomenon_rates.png`
- `phenomenon_age_trajectories_child_vs_caretakers.png`
- `age_bin_scorable_utterance_counts.png`
- `special_marker_age_trajectories.png`
- `filler_age_trajectories.png`
- `shortening_age_trajectories.png`
- `variant_probe_category_counts.png`
- `variant_probe_word_count_distributions.png`

Interpretation notes:

- Rates use scorable utterances as denominators.
- `CHILD` means `CHI`.
- `CARETAKERS` merges caretaker tiers.
- Age trajectories are not continuous curves; each dot is the midpoint of a
  6-month age bin.

Current diagnostic limitation: these diagnostic outputs predate the full strict
corpus expansion. They should be rerun if the research report needs the expanded
datasets.

## 7. Complexity / Effort Counts

Main script:

```text
src/utterance_count_strategies.py
```

Purpose:

- provide transparent heuristic counters for words, morphemes, and syllables;
- create a validation probe of real cleaned utterances where strategies can be
  compared manually.

The script is explicitly heuristic, not an authoritative MOR replacement.

Current count strategies:

- word count by regex tokens;
- word count by whitespace tokens containing letters;
- morpheme count as one morpheme per word;
- morpheme count with common clitic/contraction splitting;
- morpheme count with simple suffix heuristics;
- syllable count by vowel groups with `y`;
- syllable count with silent-final-e adjustment;
- syllable count with consonant+`le` adjustment;
- syllable count without treating `y` as a vowel.

Validation output:

```text
results/count_validation/utterance_count_strategy_probe.csv
```

This file contains 100 real cleaned utterances selected to help manually inspect
where strategies agree or disagree.

## 8. N-Gram Vocabulary And Baseline Generation

Main docs:

```text
docs/ngram-models.md
```

Main scripts:

```text
src/build_age_word_dicts.py
src/add_random_and_unigram_utterances.py
```

### 8.1 Core Principle

The project creates same-length generated baselines for child utterances:

- random model;
- unigram model;
- bigram model;
- trigram model.

For every real child utterance of length `L`, the model generates an utterance
of length `L`. This controls word-count effort when comparing surprisal between
real child utterances and generated baselines.

### 8.2 Age Bins

Default age-bin size:

```text
6 months
```

Bins are additive. A bin such as `030-035` includes the current age bin plus all
earlier bins in the same dictionary scope.

### 8.3 Current N-Gram Context Logic

Only child tokens are prediction targets for the child baseline models, but the
latest prior caretaker utterance supplies left context for utterance-initial
child words.

For a caretaker utterance ending:

```text
p2 p1
```

and a child utterance:

```text
c1 c2 c3
```

the bigram observations are:

```text
p1 c1
c1 c2
c2 c3
```

The trigram observations are:

```text
p2 p1 c1
p1 c1 c2
c1 c2 c3
```

At generation time, the same boundary logic is used. If a context is unseen, the
trigram model backs off to bigram; the bigram model backs off to unigram.

### 8.4 Generated N-Gram File Schema

Output file:

```text
data/preprocessed_data/<DATASET>/<CHILD>/chi.ngram_generated.csv
```

Key generated columns for 6-month bins:

```text
random_model_utterance_bin6
unigram_model_utterance_bin6
bigram_model_utterance_bin6
trigram_model_utterance_bin6
```

Context-debugging columns:

```text
caretaker_context_p2
caretaker_context_p1
caretaker_context_last_two
```

The generated CSV deliberately omits `utt_id_role` to avoid spreadsheet
alignment confusion.

### 8.5 Current N-Gram Readiness

Generated n-gram files currently exist only for:

- Brown
- Manchester
- Providence

They were created before the latest strict naturalistic corpus expansion.
Therefore, the current generated baselines and current n-gram vocabularies
should be treated as **old-core-corpora outputs**, not final expanded-corpus
outputs.

The next necessary step for expanded-corpus experiments is to rerun:

1. age-binned dictionary building;
2. random/unigram/bigram/trigram generation;
3. context file creation;
4. compact scoring CSV export.

## 9. LSTM Generation Baseline

Main docs:

```text
docs/llm-models.md
```

Main script:

```text
src/generate_lstm_utterances.py
```

Current status:

- The script exists and has unit tests.
- PyTorch is installed through `uv`.
- Brown-only smoke generation has been run.
- The smoke outputs are not scientific results.

Architectures:

- `seq2seq_lstm`: default encoder-decoder model. The encoder receives caretaker
  context tokens; the decoder generates child utterance tokens.
- `causal_lstm`: prefix-style comparison. Caretaker context precedes `<bos>`,
  but context tokens are masked out of the loss.

Length modes:

- `same_as_child`: matched-length generation, directly comparable to n-gram
  baselines.
- `free_until_eos`: model chooses when to stop, useful for studying whether a
  model selects similar response length / communicative effort from context.

Important flags:

- `--architecture`
- `--context_utterances`
- `--max_context_tokens`
- `--max_train_examples`
- `--max_generate_rows_per_child`
- `--generation_length_mode`
- `--max_generated_tokens`
- `--min_generated_tokens`
- `--embedding_dim`
- `--hidden_dim`
- `--num_layers`
- `--dropout`
- `--temperature`
- `--top_k`

## 10. Caretaker Context Files

Main script:

```text
src/create_shared_caretaker_contexts.py
```

Outputs:

```text
chi.shared_caretaker_contexts.csv
caretakers.shared_caretaker_contexts.csv
```

For every real child or caretaker row, context columns are:

```text
context_k1
context_k2
context_k3
```

These are the last up-to-k prior caretaker utterances in the same child/session.
The current row is never included in its own context.

Current context files exist only for:

- Brown
- Manchester
- Providence

They have not yet been regenerated for the expanded corpus set.

## 11. Minimal Surprisal Scoring Files

Main script:

```text
src/create_minimal_surprisal_scoring_csvs.py
```

Inputs:

```text
chi.shared_caretaker_contexts.csv
caretakers.shared_caretaker_contexts.csv
```

Outputs:

```text
chi.surprisal_scoring.csv
caretakers.surprisal_scoring.csv
```

Child scoring columns:

```text
dataset
child_id
source_group
session_id
age_months
file
line_no
utt_id
context_k1
context_k2
context_k3
chi_utterance_clean
random_model_utterance_bin6
unigram_model_utterance_bin6
bigram_model_utterance_bin6
trigram_model_utterance_bin6
```

Caretaker scoring columns:

```text
dataset
child_id
source_group
session_id
age_months
file
line_no
utt_id
speaker
context_k1
context_k2
context_k3
caretaker_utterance_clean
```

Current compact scoring files exist only for:

- Brown
- Manchester
- Providence

They have not yet been generated for the expanded corpus set.

## 12. Surprisal Scoring

Main docs:

```text
docs/llm-models.md
docs/current_results.md
```

Main scoring script:

```text
src/new_score_utterances.py
```

Current conceptual scoring definition:

For token `x_i`, surprisal is:

```text
S(x_i) = -log2 P(x_i | x_<i)
```

For an utterance, total surprisal is the sum over evaluated target tokens.
Mean surprisal is total surprisal divided by the number of evaluated target
tokens.

Key output-style metrics:

```text
sum_bits
mean_bits_per_token
n_eval_tokens
```

Important scoring principle:

```text
When context is supplied to the model, context tokens condition the model, but
only target utterance tokens are scored.
```

The scoring script supports:

- scoring one shard at a time;
- scoring multiple text columns in one pass;
- optional context;
- target-span scoring so context tokens are not counted;
- skipping zero-word or zero-morpheme rows;
- token-level output when requested.

The project previously screened small open-source LMs. The historical notes say
Mistral 7B was least surprised by child utterances among the tested models, with
a BabyLM 100M model as a close smaller contender. These are project notes, not a
freshly rerun benchmark.

## 13. Current Results And Figures

### 13.1 Older Surprisal Findings

Documented in:

```text
docs/current_results.md
```

High-level takeaways from older results:

- If utterance length is not controlled, average surprisal patterns can mirror
  MLU development. This makes length control essential.
- Mistral 7B appeared less surprised by child utterances than smaller tested
  models, though size may confound that comparison.
- Children appeared more context-reactive than random/unigram/bigram/trigram
  frequentist baselines in older Brown/Manchester/Providence outputs.
- Child versus caretaker comparisons suggested caretaker speech is generally
  less surprising under similar contexts, but these comparisons are not paired
  utterance comparisons.

These results should be treated as historical/provisional because the pipeline
and corpus set have changed substantially.

### 13.2 Diagnostic Figures

Folder:

```text
figs/diagnostic_analyses/brown_manchester_providence_chi_mot_fat/
```

These show rates and age trajectories for:

- special CHAT forms;
- fillers;
- shortenings;
- age-bin scorable utterance counts;
- preprocessing-variant probes.

### 13.3 Corpus Distribution Figures

Recent strict naturalistic outputs:

```text
figs/utterance_distributions_strict_naturalistic_parent_child/
```

Important files:

```text
figs/utterance_distributions_strict_naturalistic_parent_child/ALL_DATASETS/utterance_counts_by_age_bin_6m.csv
figs/utterance_distributions_strict_naturalistic_parent_child/ALL_DATASETS/previous_vs_new_strict_downloads_age_bin_counts_6m.csv
figs/utterance_distributions_strict_naturalistic_parent_child/ALL_DATASETS/caretaker_previous_vs_new_strict_downloads_age_bin_counts_6m.csv
```

All-preprocessed age tables:

```text
results/utterance_age_tables/
```

## 14. Current Source File Inventory

Main active files:

| File | Role |
| --- | --- |
| `src/cleaning.py` | Focused CHAT main-tier cleaning policy. |
| `src/prepare_datasets.py` | Stage 0 corpus discovery, metadata extraction, `chi.csv` / `caretakers.csv` writing. |
| `src/special_forms_per_utterance.py` | Diagnostic counts for CHAT `@` special forms. |
| `src/fillers_and_shortenings_per_utterance.py` | Diagnostic counts for fillers and parenthetical shortenings. |
| `src/build_preprocessing_variant_probe.py` | Real-data probe set for comparing preprocessing variants. |
| `src/plot_diagnostic_analyses.py` | Figures from diagnostic CSVs. |
| `src/utterance_count_strategies.py` | Word, morpheme, syllable heuristic counters and validation probe. |
| `src/plot_distributions.py` | Corpus distribution plots and age-bin summaries. |
| `src/build_age_word_dicts.py` | Additive age-binned unigram, bigram, trigram count dictionaries. |
| `src/add_random_and_unigram_utterances.py` | Random/unigram/bigram/trigram same-length child baseline generation. |
| `src/generate_lstm_utterances.py` | Experimental word-level LSTM child utterance generation. |
| `src/create_shared_caretaker_contexts.py` | Role-specific caretaker context windows for child and caretaker rows. |
| `src/create_minimal_surprisal_scoring_csvs.py` | Compact per-child scoring CSV exports. |
| `src/new_create_parallel_data.py` | Older/chunking-style parallel scoring data export logic. |
| `src/new_score_utterances.py` | LM surprisal scoring over one CSV shard. |

Older or less-central files still present:

- `src/create_contexts.py`
- `src/create_context_caretakers.py`
- `src/create_contexts_slurm_data_chi.py`
- `src/create_contexts_slurm_data_caretakers.py`
- `src/add_random_model_utterances_multi.py`
- `src/patch_caretakers_age_months.py`

These should be inspected before reuse; newer scripts often supersede older
versions.

## 15. Reproducibility And Data Handling Rules

Important project constraints from `AGENTS.md`:

- Do not overwrite raw CHILDES / CHAT data.
- Do not silently drop utterance rows without recording why.
- Preserve row provenance wherever possible.
- Do not treat context tokens as target tokens when computing target surprisal.
- Do not treat empty or punctuation-only utterances as normal scored utterances.
- Do not change output schemas without documenting the change.
- Do not invent scientific results or claim a model was run when it was not.

Data handling norms:

- Avoid printing or loading entire data files into chat.
- Inspect large CSVs with shape, columns, missing counts, and small samples.
- Treat `data/raw_data/` as immutable.

## 16. What Is Ready Versus Not Ready

Ready now:

- Stage 0 cleaned utterance analyses over all currently preprocessed datasets.
- Child/caretaker distribution tables by age bin.
- Strict naturalistic distribution summaries.
- Diagnostic figure set for Brown/Manchester/Providence.
- Old-core n-gram generated baselines for Brown/Manchester/Providence.
- Old-core shared caretaker-context and minimal scoring files for
  Brown/Manchester/Providence.

Not yet ready:

- Expanded-corpus n-gram dictionaries.
- Expanded-corpus random/unigram/bigram/trigram generated utterances.
- Expanded-corpus shared context files.
- Expanded-corpus compact surprisal scoring CSVs.
- Expanded-corpus diagnostic plots for special forms, fillers, and shortenings.
- Any final statistical model claiming developmental communicative-efficiency
  effects across the expanded corpora.
- LSTM generation results beyond small smoke tests.
- Any final BabyLM-style or held-out-corpus LLM generation experiment.

## 17. Recommended Next Technical Steps

If the next agent is continuing implementation, the most coherent technical
sequence is:

1. Decide the active corpus set:
   - strict naturalistic only;
   - strict plus structured-observational;
   - include/exclude clinical/probe data.
2. Rerun additive n-gram dictionary building on the selected corpus set.
3. Regenerate `chi.ngram_generated.csv` for all selected child folders.
4. Verify length matching and CSV schema sanity.
5. Recreate shared caretaker context files for child and caretaker rows.
6. Recreate compact surprisal scoring CSVs.
7. Build/update Slurm or Globus-ready scoring shards if needed.
8. Score real and generated utterances under the chosen LM.
9. Analyze:
   - child real versus generated controls;
   - child versus caretaker;
   - age-bin trajectories;
   - effect of context window size;
   - effect of effort controls.

## 18. Recommended Next Research Questions

The deep-research agent should help refine:

- What should be the primary efficiency outcome?
- Should the first analysis focus on surprisal per token, total surprisal,
  residualized surprisal, or surprisal relative to a matched-length baseline?
- How should effort be operationalized: words, morphemes, syllables, model
  tokens, or multiple robustness checks?
- Should age be modeled continuously, by 6-month bins, or both?
- How should responsive turns be filtered or categorized by prompt type?
- How should yes/no responses, fillers, special forms, and shortenings be
  treated in the main analysis versus robustness checks?
- Should structured-observational corpora such as EHS and Champaign be excluded
  from the main naturalistic analysis, included as robustness checks, or modeled
  with corpus-type effects?
- How should clinical/probe corpora such as Cummings be used, if at all?
- Which LM should be used for final surprisal scoring, and should scoring be
  repeated with multiple LMs?

## 19. Main Risks And Confounds

Scientific risks:

- Short utterances may reflect developmental limitation rather than efficiency.
- Yes/no questions and other prompt types can mechanically elicit short answers.
- Repetition and imitation can look efficient but may not be generative
  production.
- Corpus heterogeneity is large: home play, structured observation, clinical
  probe, and cross-corpus transcription conventions differ.
- Surprisal is sensitive to the scoring model and context definition.
- Frequency, informativity, and contextual predictability are related but not
  interchangeable.
- Caretaker speech and child speech are not directly comparable unless analyses
  carefully control for length, context, and turn type.

Technical risks:

- Expanded corpora are Stage 0 ready but downstream generated/scoring artifacts
  are stale or missing.
- Some rows have missing age and cannot be assigned to age bins.
- The current cleaning policy strips parenthetical shortenings; separate
  diagnostics exist, but final treatment is still a scientific decision.
- Filler detection is imperfect because fillers may appear both with CHAT
  markers and as ordinary tokens.
- Some older scripts exist alongside newer replacements; use the documented
  newer pipeline unless an older script is intentionally revived.

## 20. High-Value Files For A Deep-Research Agent To Read

Start here:

```text
docs/project_deep_research_handoff.md
docs/preprocessed_datasets.md
results/utterance_age_tables/all_preprocessed_utterance_age_bin_tables.md
docs/design.md
docs/general-overview.md
docs/ngram-models.md
docs/llm-models.md
docs/current_results.md
docs/notes.md
TODO.md
```

Then inspect code:

```text
src/cleaning.py
src/prepare_datasets.py
src/build_age_word_dicts.py
src/add_random_and_unigram_utterances.py
src/create_shared_caretaker_contexts.py
src/create_minimal_surprisal_scoring_csvs.py
src/new_score_utterances.py
```

Then inspect external research framing:

```text
/home/apaixonada/Downloads/deep-research-report.md
/home/apaixonada/Downloads/Communicative Efficiency in Child Language.pdf
```

## 21. Short Version For The Next Agent

This project is now data-rich but pipeline-asymmetric. Stage 0 preprocessing has
been expanded to many corpora, but the generated baselines and scoring-ready
files still reflect the older Brown/Manchester/Providence core. The next major
technical milestone is to rerun the entire generation/context/scoring-prep
pipeline on a clearly chosen active corpus set, then score those real and
generated utterances under the selected LM while keeping context tokens out of
target surprisal. The next major scientific milestone is to define an efficiency
metric robust enough to distinguish true context-sensitive compression from
developmental shortness, prompt constraints, and corpus artifacts.
