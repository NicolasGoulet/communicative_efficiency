# Bayes-Decomposed Informativeness Working Report

> **Superseded methods pilot (2026-07-13).** This report uses the original overlapping-training reverse-trigram score and must not support substantive claims. See the [corrected cross-fitted PBM Bayes report](corrected_pbm_bayes_report.html), which holds out each evaluated corpus, trains additively by age, validates whole-utterance context evidence, and normalizes within matched candidate sets.

This is a working report for the new Bayes-style information family. It is intentionally separate from the supervisor-facing July pages for now. The goal is to check whether the decomposition score behaves sensibly before we decide which results deserve promotion.

## What Was Scored

The Bayes table uses the decomposition

```text
log2 score(u, c) = log2 p(u) + log2 p(c | u)
bits = -log2 score(u, c)
```

The normalizer `p(c)` has **not** been estimated. That means these are unnormalized decomposition bits, useful for comparing candidate utterances in the same context and for exploratory analyses, but not a fully normalized posterior probability.

Inputs:

- Bayes scores: `results/mila_modular_runs_2026_07_08/products/pbm_ngram_bayes_scores/pbm_ngram_bayes_scores.csv.gz`
- Complexity predictors: `results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/pbm_candidate_complexity.csv.gz`
- Direct contextual Mistral scores: `results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz`
- Joined analysis table: `results/bayes_information_report/pbm_bayes_mistral_complexity_joined.csv.gz`

## Audit

| source_model | bayes_rows | mistral_raw_rows | joined_rows | missing_mistral_rows | missing_complexity_rows |
| --- | --- | --- | --- | --- | --- |
| real | 446508.000 | 446985.000 | 446508.000 | 0.000 | 0.000 |
| random | 446492.000 | 446508.000 | 446492.000 | 0.000 | 0.000 |
| unigram | 446508.000 | 446508.000 | 446508.000 | 0.000 | 0.000 |
| bigram | 446508.000 | 446508.000 | 446508.000 | 0.000 | 0.000 |
| trigram | 446508.000 | 446508.000 | 446508.000 | 0.000 | 0.000 |

The join is clean enough for working analyses: Bayes and complexity products match exactly, and the direct Mistral table joins by `row_uid + source_model`. The `random` source has 16 fewer Bayes/complexity rows because empty generated random candidates were removed before scoring.

## Source-Level Patterns

| source | n | bayes_bits_per_token_mean | bayes_prior_bits_per_token_mean | bayes_context_bits_mean | mistral_bits_per_token_mean | orthographic_word_count_mean |
| --- | --- | --- | --- | --- | --- | --- |
| Real child | 446508.000 | 71.752 | 10.743 | 106.054 | 6.493 | 2.661 |
| Random | 446492.000 | 86.396 | 22.818 | 110.371 | 9.843 | 2.661 |
| Unigram | 446508.000 | 76.154 | 14.428 | 107.169 | 9.524 | 2.661 |
| Bigram | 446508.000 | 74.782 | 13.133 | 107.089 | 8.453 | 2.661 |
| Trigram | 446508.000 | 73.730 | 12.203 | 106.937 | 7.792 | 2.661 |

Lower bits mean the model finds the utterance more expected or compatible. The most important comparison is not raw total bits alone, because utterance length matters; the main plots use bits per token where possible.

![Bayes bits per token by age and source](../figs/bayes_information_report/bayes_bits_per_token_by_age_source.png)

![Direct Mistral bits per token by age and source](../figs/bayes_information_report/mistral_bits_per_token_by_age_source.png)

![Bayes prior component by age and source](../figs/bayes_information_report/bayes_component_bits_by_age_source.png)

## Does Bayes Agree With Direct Mistral Surprisal?

| source_model | n | pearson_bayes_mistral_per_token | spearman_bayes_mistral_per_token | pearson_prior_mistral_per_token | pearson_context_mistral_total |
| --- | --- | --- | --- | --- | --- |
| real | 446508.000 | 0.053 | 0.046 | 0.349 | 0.006 |
| random | 446492.000 | -0.074 | -0.108 | -0.112 | 0.062 |
| unigram | 446508.000 | -0.144 | -0.183 | 0.066 | 0.063 |
| bigram | 446508.000 | -0.038 | -0.069 | 0.051 | 0.064 |
| trigram | 446508.000 | -0.044 | -0.073 | 0.078 | 0.043 |

![Bayes versus direct Mistral scatter](../figs/bayes_information_report/bayes_vs_mistral_scatter.png)

The decomposition and direct Mistral scores are not supposed to be identical. They use different estimators: the Bayes pilot uses count-based `p(u)` and reverse discourse `p(c | u)`, while direct Mistral estimates contextual target surprisal more directly. Agreement is therefore evidence of convergence; disagreement is scientifically informative rather than automatically a bug.

## Paired Real-Versus-Baseline Checks

Each generated baseline is paired to the same real child row and same context. Positive values below mean the generated baseline has more bits than the real child utterance.

| source | n | delta_bayes_bits_per_token_vs_real_mean | delta_mistral_bits_per_token_vs_real_mean | delta_words_vs_real_mean |
| --- | --- | --- | --- | --- |
| Random | 446492.000 | 14.646 | 3.351 | -2.40e-04 |
| Unigram | 446508.000 | 4.402 | 3.031 | -2.24e-06 |
| Bigram | 446508.000 | 3.030 | 1.960 | 2.24e-06 |
| Trigram | 446508.000 | 1.978 | 1.300 | -2.24e-06 |

![Paired Bayes gaps](../figs/bayes_information_report/paired_bayes_gap_by_age.png)

![Paired Mistral gaps](../figs/bayes_information_report/paired_mistral_gap_by_age.png)

The same-context percentile view asks: among random/unigram/bigram/trigram alternatives for a row, what fraction have higher bits than the real child utterance?

| age_bin | n | real_bayes_worse_pct | real_mistral_worse_pct |
| --- | --- | --- | --- |
| 006-023 | 62816.00 | 69.84 | 69.90 |
| 024-029 | 162210.00 | 76.65 | 74.71 |
| 030-035 | 142447.00 | 79.94 | 79.79 |
| 036-041 | 37206.00 | 79.61 | 79.65 |
| 042-047 | 16345.00 | 80.96 | 83.76 |
| 048-053 | 12909.00 | 81.36 | 81.38 |
| 054-059 | 10033.00 | 81.22 | 82.70 |
| 060-065 | 2542.00 | 83.13 | 85.27 |

![Real-child advantage percentiles](../figs/bayes_information_report/real_advantage_percentiles_by_age.png)

## Complexity And Effort

The new complexity repo adds orthographic MLU-style predictors, syllable/phoneme proxies, and lexical trajectory fields. These are not a replacement for the previous effort measures; they are extra controls and developmental descriptors.

![Real child complexity trajectories](../figs/bayes_information_report/real_child_complexity_trajectories.png)

## First Regression Models

These are working models using heteroskedasticity-robust standard errors on a stratified sample where needed. They are meant to guide the next report iteration, not to be the final inferential specification.

| model | formula | n | r2 |
| --- | --- | --- | --- |
| Direct surprisal from Bayes score | mistral_bits_per_token ~ bayes_bits_per_token + orthographic_word_count + C(source_model) + C(age_bin) | 249998.000 | 0.229 |
| Direct surprisal from Bayes components | mistral_bits_per_token ~ bayes_prior_bits_per_token + bayes_context_bits + orthographic_word_count + C(source_model) + C(age_bin) | 249998.000 | 0.236 |
| Real-child direct surprisal with lexical complexity | mistral_bits_per_token ~ bayes_prior_bits_per_token + bayes_context_bits + orthographic_word_count + lexical_cumulative_child_vocab_size + lexical_cumulative_child_ttr + C(age_bin) + C(child_id) | 250000.000 | 0.157 |
| Paired baseline gap alignment | delta_mistral_bits_per_token_vs_real ~ delta_bayes_bits_per_token_vs_real + delta_words_vs_real + C(source_model) + C(age_bin) | 249998.000 | 0.104 |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Direct surprisal from Bayes score | bayes_bits_per_token | -8.32e-04 | 1.21e-04 | 5.75e-12 |
| Direct surprisal from Bayes score | orthographic_word_count | 0.0501 | 0.0029 | 2.63e-65 |
| Direct surprisal from Bayes components | bayes_prior_bits_per_token | 0.0452 | 0.0011 | 0.0000 |
| Direct surprisal from Bayes components | bayes_context_bits | 3.54e-04 | 8.71e-05 | 4.74e-05 |
| Direct surprisal from Bayes components | orthographic_word_count | 0.0859 | 0.0026 | 1.01e-242 |
| Real-child direct surprisal with lexical complexity | bayes_prior_bits_per_token | 0.1758 | 0.0013 | 0.0000 |
| Real-child direct surprisal with lexical complexity | bayes_context_bits | -0.0011 | 9.38e-05 | 1.35e-32 |
| Real-child direct surprisal with lexical complexity | orthographic_word_count | -0.0277 | 0.0020 | 1.39e-44 |
| Real-child direct surprisal with lexical complexity | lexical_cumulative_child_vocab_size | -2.03e-04 | 1.61e-05 | 2.29e-36 |
| Real-child direct surprisal with lexical complexity | lexical_cumulative_child_ttr | 0.2821 | 0.1466 | 0.0544 |
| Paired baseline gap alignment | delta_bayes_bits_per_token_vs_real | 0.0738 | 8.49e-04 | 0.0000 |
| Paired baseline gap alignment | delta_words_vs_real | 0.8811 | 0.5281 | 0.0952 |

## Current Scientific Read

1. The Bayes products are runnable and joinable with the existing direct Mistral route.
2. The decomposition gives us two interpretable components: a prior/utterance-family term `p(u)` and a context-compatibility term `p(c | u)`.
3. The paired real-versus-baseline view is the most defensible immediate use: for the same child moment and context, ask whether the real utterance is favored relative to generated alternatives.
4. The Bayes score should stay labeled as an unnormalized decomposition score until we estimate or explicitly condition away `p(c)`.

## Next Decisions

- Decide whether the first supervisor-facing use should show paired real-versus-baseline gaps, correlations with Mistral, or complexity-controlled real-child developmental models.
- Add a sensitivity where Bayes `p(u)` is trained PBM-only rather than full-79, to show the full-79 result is not an artifact of training scope.
- Add the neural likelihood route only after the count-based decomposition has been explained and stabilized.
