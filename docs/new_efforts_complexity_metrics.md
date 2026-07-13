# Complexity Metrics

The new complexity layer gives us more than raw word count. It adds MLU-style predictors, syllable and phoneme proxies, and lexical trajectory summaries that can be used as controls or developmental descriptors.

## What These Metrics Are For

- Use MLU and syllable/phoneme proxies to check whether information effects are just production-complexity effects.
- Use vocabulary and TTR measures to approximate lexical complexity over time.
- Keep these separate from the information measure itself: complexity is a predictor/control, not the same object as surprisal.

## Real Child Complexity By Age Bin

| age_bin | n_cells | mean_words_per_utterance_mean | mean_words_per_utterance_ci_low | mean_words_per_utterance_ci_high | mean_syllables_per_utterance_mean | age_bin_vocab_size_mean | age_bin_ttr_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 006-023 | 17.000 | 1.727 | 1.548 | 1.907 | 2.165 | 651.706 | 0.128 |
| 024-029 | 21.000 | 2.349 | 2.093 | 2.606 | 2.858 | 1173.476 | 0.073 |
| 030-035 | 20.000 | 2.840 | 2.609 | 3.071 | 3.399 | 1372.550 | 0.074 |
| 036-041 | 8.000 | 3.193 | 2.829 | 3.557 | 3.817 | 1170.500 | 0.109 |
| 042-047 | 5.000 | 3.875 | 3.341 | 4.409 | 4.662 | 1192.000 | 0.119 |
| 048-053 | 3.000 | 3.703 | 2.781 | 4.624 | 4.403 | 1270.333 | 0.127 |
| 054-059 | 2.000 | 4.156 | 3.342 | 4.970 | 4.937 | 1661.500 | 0.081 |
| 060-065 | 2.000 | 4.068 | 3.112 | 5.023 | 4.830 | 710.500 | 0.140 |

![Complexity timing checks](../figs/developmental_onset_report/complexity_timing_checks.png)

## Adjusted Complexity Effects

| outcome | age_bin | estimate_vs_006_023 | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- |
| mean_words_per_utterance | 006-023 | 0.0000 |  |  |  |
| mean_words_per_utterance | 024-029 | 0.8056 | 0.5527 | 1.0584 | 4.25e-10 |
| mean_words_per_utterance | 030-035 | 1.3660 | 1.0984 | 1.6335 | 1.41e-23 |
| mean_words_per_utterance | 036-041 | 1.8466 | 1.4209 | 2.2724 | 1.88e-17 |
| mean_words_per_utterance | 042-047 | 2.2603 | 1.7913 | 2.7293 | 3.55e-21 |
| mean_words_per_utterance | 048-053 | 2.7138 | 2.0684 | 3.3592 | 1.70e-16 |
| mean_words_per_utterance | 054-059 | 2.8948 | 2.4904 | 3.2992 | 1.02e-44 |
| mean_words_per_utterance | 060-065 | 2.7961 | 2.3241 | 3.2681 | 3.68e-31 |
| mean_syllables_per_utterance | 006-023 | 0.0000 |  |  |  |
| mean_syllables_per_utterance | 024-029 | 0.8852 | 0.6740 | 1.0965 | 2.15e-16 |
| mean_syllables_per_utterance | 030-035 | 1.5116 | 1.2772 | 1.7460 | 1.28e-36 |
| mean_syllables_per_utterance | 036-041 | 2.0152 | 1.6069 | 2.4235 | 3.91e-22 |
| mean_syllables_per_utterance | 042-047 | 2.5250 | 2.0608 | 2.9893 | 1.56e-26 |
| mean_syllables_per_utterance | 048-053 | 3.0840 | 2.3661 | 3.8020 | 3.78e-17 |
| mean_syllables_per_utterance | 054-059 | 3.3086 | 2.8903 | 3.7268 | 3.21e-54 |
| mean_syllables_per_utterance | 060-065 | 3.1816 | 2.5461 | 3.8170 | 9.92e-23 |
| age_bin_vocab_size | 006-023 | 0.0000 |  |  |  |
| age_bin_vocab_size | 024-029 | 89.5159 | -105.6091 | 284.6409 | 0.3686 |
| age_bin_vocab_size | 030-035 | 328.7388 | 159.3183 | 498.1593 | 1.43e-04 |
| age_bin_vocab_size | 036-041 | 485.1923 | 179.9707 | 790.4139 | 0.0018 |
| age_bin_vocab_size | 042-047 | 477.1112 | 123.4675 | 830.7548 | 0.0082 |
| age_bin_vocab_size | 048-053 | 633.3577 | 322.2665 | 944.4489 | 6.60e-05 |
| age_bin_vocab_size | 054-059 | 690.6259 | 251.3534 | 1129.8984 | 0.0021 |
| age_bin_vocab_size | 060-065 | 534.0541 | 215.5982 | 852.5101 | 0.0010 |

## Complexity In The Candidate Cloud

| source | orthographic_word_count_mean | estimated_syllable_count_mean | mistral_bits_per_token_mean | bayes_bits_per_token_mean |
| --- | --- | --- | --- | --- |
| Real child | 2.661 | 3.220 | 6.493 | 71.752 |
| Random | 2.661 | 4.813 | 9.843 | 86.396 |
| Unigram | 2.661 | 3.239 | 9.524 | 76.154 |
| Bigram | 2.661 | 3.240 | 8.453 | 74.782 |
| Trigram | 2.661 | 3.233 | 7.792 | 73.730 |

![Real child lexical complexity trajectories](../figs/bayes_information_report/real_child_complexity_trajectories.png)
