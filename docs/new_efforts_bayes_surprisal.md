# Bayes-Decomposed Surprisal

The Bayes-style score uses the working decomposition:

```text
bits(u, c) = -log2 p(u) - log2 p(c | u)
```

The normalizer `p(c)` is not estimated yet, so this is an **unnormalized decomposition score**. It is most defensible right now for same-context candidate comparisons.

## Source-Level Patterns

| source | n | bayes_bits_per_token_mean | bayes_prior_bits_per_token_mean | bayes_context_bits_mean | mistral_bits_per_token_mean |
| --- | --- | --- | --- | --- | --- |
| Real child | 446508.000 | 71.752 | 10.743 | 106.054 | 6.493 |
| Random | 446492.000 | 86.396 | 22.818 | 110.371 | 9.843 |
| Unigram | 446508.000 | 76.154 | 14.428 | 107.169 | 9.524 |
| Bigram | 446508.000 | 74.782 | 13.133 | 107.089 | 8.453 |
| Trigram | 446508.000 | 73.730 | 12.203 | 106.937 | 7.792 |

![Bayes bits per token by age and source](../figs/bayes_information_report/bayes_bits_per_token_by_age_source.png)

![Direct Mistral bits per token by age and source](../figs/bayes_information_report/mistral_bits_per_token_by_age_source.png)

![Bayes components by age and source](../figs/bayes_information_report/bayes_component_bits_by_age_source.png)

## Paired Real-Versus-Baseline Checks

Positive gaps mean the generated baseline is higher-bit than the real child utterance in the same context.

| source | n | delta_bayes_bits_per_token_vs_real_mean | delta_mistral_bits_per_token_vs_real_mean | delta_words_vs_real_mean |
| --- | --- | --- | --- | --- |
| Random | 446492.000 | 14.646 | 3.351 | -2.40e-04 |
| Unigram | 446508.000 | 4.402 | 3.031 | -2.24e-06 |
| Bigram | 446508.000 | 3.030 | 1.960 | 2.24e-06 |
| Trigram | 446508.000 | 1.978 | 1.300 | -2.24e-06 |

![Paired Bayes gaps](../figs/bayes_information_report/paired_bayes_gap_by_age.png)

![Paired Mistral gaps](../figs/bayes_information_report/paired_mistral_gap_by_age.png)

## Real Child Advantage Percentiles

| age_bin | n | real_bayes_advantage_pct | real_mistral_advantage_pct |
| --- | --- | --- | --- |
| 006-023 | 62816.00 | 69.84 | 69.90 |
| 024-029 | 162210.00 | 76.65 | 74.71 |
| 030-035 | 142447.00 | 79.94 | 79.79 |
| 036-041 | 37206.00 | 79.61 | 79.65 |
| 042-047 | 16345.00 | 80.96 | 83.76 |
| 048-053 | 12909.00 | 81.36 | 81.38 |
| 054-059 | 10033.00 | 81.22 | 82.70 |
| 060-065 | 2542.00 | 83.13 | 85.27 |

![Real child advantage percentiles](../figs/bayes_information_report/real_advantage_percentiles_by_age.png)

## Relationship To Direct Mistral

| source_model | n | pearson_bayes_mistral_per_token | spearman_bayes_mistral_per_token | pearson_prior_mistral_per_token | pearson_context_mistral_total |
| --- | --- | --- | --- | --- | --- |
| real | 446508.000 | 0.053 | 0.046 | 0.349 | 0.006 |
| random | 446492.000 | -0.074 | -0.108 | -0.112 | 0.062 |
| unigram | 446508.000 | -0.144 | -0.183 | 0.066 | 0.063 |
| bigram | 446508.000 | -0.038 | -0.069 | 0.051 | 0.064 |
| trigram | 446508.000 | -0.044 | -0.073 | 0.078 | 0.043 |

![Bayes versus direct Mistral](../figs/bayes_information_report/bayes_vs_mistral_scatter.png)

## First Model Checks

| model | formula | n | r2 |
| --- | --- | --- | --- |
| Direct surprisal from Bayes score | mistral_bits_per_token ~ bayes_bits_per_token + orthographic_word_count + C(source_model) + C(age_bin) | 249998.000 | 0.229 |
| Direct surprisal from Bayes components | mistral_bits_per_token ~ bayes_prior_bits_per_token + bayes_context_bits + orthographic_word_count + C(source_model) + C(age_bin) | 249998.000 | 0.236 |
| Real-child direct surprisal with lexical complexity | mistral_bits_per_token ~ bayes_prior_bits_per_token + bayes_context_bits + orthographic_word_count + lexical_cumulative_child_vocab_size + lexical_cumulative_child_ttr + C(age_bin) + C(child_id) | 250000.000 | 0.157 |
| Paired baseline gap alignment | delta_mistral_bits_per_token_vs_real ~ delta_bayes_bits_per_token_vs_real + delta_words_vs_real + C(source_model) + C(age_bin) | 249998.000 | 0.104 |
