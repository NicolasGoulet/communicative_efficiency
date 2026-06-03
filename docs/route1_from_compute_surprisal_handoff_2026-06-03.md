# Route 1 Handoff From `compute_surprisal_mila`

Date: 2026-06-03

This note was created from the scoring/HPC conversation by mistake after Nicolas clarified that this chat should remain focused on `compute_surprisal_mila`. No analysis code should be created here from that conversation. This file is only a handoff for the `communicative_efficiency` agent.

## Scope Nicolas Wants

Create a new supervisor-facing HTML document for **Route 1 only**.

Route 1 means: predicting utterance-level informational content in children over developmental time, including:

- total information in the utterance: `sum_bits`
- information per unit effort: especially `sum_bits / cleaned_target_word_count`
- tokenizer-level sensitivity: `mean_bits_per_token`

Do **not** include Route 2 entropy/KL results in this document.
Do **not** include the Levshina-style word-token route in this document.
Do **not** build a huge scattered dashboard. This should be a focused Route 1 report.

## Correct Data Source

Use the patched cleaned Mistral scoring tree:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023
```

This symlink points to the patched source of truth in `compute_surprisal_mila`:

```text
/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/raw_surprisal_cleaned_patched_006_023
```

Status already checked from the scoring repo:

- 504 scored CSVs are present.
- Coverage is 21 files for every combination of:
  - modes: `real`, `caretaker`, `random`, `unigram`, `bigram`, `trigram`
  - contexts: `k0`, `k1`, `k2`, `k3`
- The PBM 006-023 patch audit passed: 272 patch files applied, 1,005,056 patch rows matched, missing keys = 0, duplicate keys = 0, age-window errors = 0.
- The full patched local audit passed: expected files = 504, actual files = 504, missing = 0, malformed/problem files = 0.

## Target Text Columns

Recompute effort/length from the actual target text string. Do not trust old `word_count` or `morph_count` columns.

Use these target columns by mode:

| Mode | Target text column |
|---|---|
| `real` | `chi_utterance_clean` |
| `caretaker` | `caretaker_utterance_clean` |
| `random` | `random_model_utterance_bin6` |
| `unigram` | `unigram_model_utterance_bin6` |
| `bigram` | `bigram_model_utterance_bin6` |
| `trigram` | `trigram_model_utterance_bin6` |

Context windows can be parsed from the path:

```text
WITHOUT_context/k0
WITH_context/k1
WITH_context/k2
WITH_context/k3
```

The corresponding context text columns are `context_k1`, `context_k2`, and `context_k3`; `k0` has no preceding context.

## Suggested Report Structure

The new HTML should have these sections only:

1. **Route 1 scope**
   - State clearly that this document is about utterance-level information over age.
   - State explicitly that Route 2 entropy/KL and Route 3 word-token informativity are separate documents.

2. **Data source and audit status**
   - Mention the patched 504-file tree.
   - Show a small table of rows/files by `mode × context_window`.
   - Show real-child coverage by dataset and child.

3. **Outcome definitions**
   - `sum_bits = Σ_i -log2 P(token_i | context, previous target tokens)`
   - `bits_per_word = sum_bits / cleaned_target_word_count`
   - `bits_per_token = mean_bits_per_token`

4. **Focused descriptive plots**
   Suggested minimal set:
   - Real child `bits_per_word`, `bits_per_token`, and `sum_bits` over age by context window.
   - Real child `bits_per_word` over age stratified by cleaned target word-count bands.
   - Compact comparison of real/caretaker/random/unigram/bigram/trigram for one clean view, preferably `k3` and word counts 1-8.

5. **Staged explanatory models**
   Build models one block at a time and explain each block. The goal is not black-box prediction; it is explanatory modeling.

## Suggested Model Frame

Use utterance-level rows or child × age × context × target-length cells weighted by utterance count. The latter is probably more stable and easier to explain.

Core predictors:

- `age_years`: developmental time
- `child_key`: child fixed effect / repeated-observation control
- `target_word_count`: recomputed from the actual target string
- `context_window`: `k0`, `k1`, `k2`, `k3`
- `context_word_count`: recomputed from the context string, for context-size controls in k1-k3 analyses

Suggested staged formulas for each outcome (`sum_bits`, `bits_per_word`, `bits_per_token`):

```text
M0: outcome ~ child_key + target_word_count
M1: outcome ~ age_years + child_key + target_word_count
M2: outcome ~ age_years + context_window + child_key + target_word_count
M3: outcome ~ age_years * context_window + child_key + target_word_count
M4: k1-k3 only: outcome ~ age_years * context_window + log1p(context_word_count) + child_key + target_word_count
```

The main Route 1 claim should come from `bits_per_word`, because it asks whether information per production effort changes with age after controlling for target length and child identity.

## Important Interpretation Guardrails

- Do not say older children are more efficient just because `sum_bits` changes. Total bits is length-dependent.
- The most defensible first claim is about `bits_per_word` after target-length and child controls.
- `bits_per_token` is a tokenizer-level sensitivity check, not the cognitive effort measure.
- `context_window` comparisons should eventually include `context_word_count`, because k3 has more preceding text than k1.
- Descriptive trajectories are useful for intuition, but final claims should come from the staged models.

## What Was Checked In This Conversation

From the scoring repo conversation, the agent checked:

- `communicative_efficiency` git status was clean.
- The patched Mistral symlink exists and resolves correctly.
- The patched tree has 504 CSVs.
- Sample scored CSV headers confirm the target columns listed above.
- `communicative_efficiency` already has pandas/numpy/matplotlib/scikit-learn, but not statsmodels/seaborn in `pyproject.toml`. If adding dependencies, do it intentionally in the analysis repo, not from the scoring repo conversation.

## Nicolas Preference

Keep this report simple and readable for supervisors. Avoid giant tables of uninterpretable numbers. Every model result should state:

- outcome
- model type
- predictors/controls
- what the age term means
- whether length is controlled
- whether child identity is controlled
- whether context surface size is controlled
