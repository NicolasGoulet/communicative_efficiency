# Developmental Onset Of Communicative Efficiency

This is a working report for the new question raised in the latest supervisor discussion: not just whether the trajectory trends downward, but **when in developmental time the communicative-efficiency signal becomes detectable**.

## Transcript Anchor

The June 4 meeting transcript frames this as a control-and-timing problem. Around the 20-30 minute chunk, the discussion moves from simple averages to whether there is a decrease in surprisal when we control for the exact children and utterance length. That is the standard used here.

This report therefore treats "kick-in" as an operational question, not a single magical month.

## Analysis Scope

Inputs:

- Real child timing table: `results/yang_followup/yang_followup_analysis_rows.csv.gz`
- Context-modulation age-bin coefficients: `results/yang_followup/age_bin_modulation_coefficients.csv`
- Paired Bayes/Mistral baseline gaps: `results/bayes_information_report/paired_baseline_minus_real_gaps.csv.gz`
- PBM complexity age-bin summaries: `results/mila_modular_runs_2026_07_08/products/pbm_complexity_predictors/pbm_real_complexity_age_bin_summary.csv.gz`

Audit:

| child_age_cells | children | datasets | utterance_rows | first_age_bin | last_age_bin |
| --- | --- | --- | --- | --- | --- |
| 77.00 | 21.00 | 3.00 | 441413.00 | 006-023 | 060-065 |

The headline timing model is utterance-level because that matches the earlier Route 1 evidence: child identity is controlled, word-count effort is held fixed with exact/top-coded word-count bins, and uncertainty is clustered by child. A stricter child-by-age-bin aggregate is included as a sensitivity check because it changes the weighting and has only 77 cells.

## What Counts As "Kick-In"

I compute three complementary timing signals:

1. **Controlled real-child trajectory:** age-bin effects on real child Mistral bits after controlling for child identity and fixed word-count effort.
2. **Paired real advantage:** generated baseline minus real child bits/token in the same context. Positive values mean the real child utterance is lower-bit than the generated alternative.
3. **Context modulation:** age-specific coefficients showing whether richer caregiver context predicts lower child total bits.

I also plot MLU and vocabulary timing beside these signals, because a reviewer will ask whether any CE onset is just grammatical or lexical growth.

## High-Level Onset Read

| signal | operational_definition | earliest_age_bin | estimate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| Continuous fixed-word-count age slope | utterance-level OLS with child fixed effects, exact/top-coded word-count controls, child-clustered SEs | whole range | -0.132 | -0.180 | -0.083 |
| Earliest exact-word-count age-bin decrease | age-bin model relative to 006-023 with child fixed effects and exact/top-coded word-count controls | 024-029 | -0.913 | -1.584 | -0.243 |
| context entropy modulation | age-specific regression coefficient predicting child total bits | 006-023 | -0.435 |  |  |
| parent context words modulation | age-specific regression coefficient predicting child total bits | 024-029 | -0.028 |  |  |
| Direct Mistral paired gap against trigram | same-context generated baseline minus real child bits/token; positive means real child has lower bits | 006-023 | 0.745 | 0.576 | 0.913 |
| Bayes decomposition paired gap against trigram | same-context generated baseline minus real child bits/token; positive means real child has lower bits | 006-023 | 1.604 | 1.055 | 2.154 |

![Onset signal map](../figs/developmental_onset_report/onset_signal_map.png)

## Controlled Real-Child Age Effects

The main model here is the same family as the earlier downward-trend evidence: utterance-level total bits, child fixed effects, and fixed word-count effort. Word counts are exact up to 11 words and top-coded as `12_plus` for rare longer child utterances. Coefficients are differences from `006-023`; negative values mean lower bits than the earliest bin at the same word-count level.

Model audit:

| model | formula | n_obs | n_children | r2 | aic | age_coef_bits_per_month | age_ci_low | age_ci_high | age_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_age_exact_word_count | sum_bits ~ age_c + C(word_count_bin) + C(child_id) | 441413.0000 | 21.0000 | 0.6281 | 3279029.0702 | -0.1316 | -0.1802 | -0.0830 | 1.10e-07 |
| age_bin_exact_word_count | sum_bits ~ C(age_bin) + C(word_count_bin) + C(child_id) | 441413.0000 | 21.0000 | 0.6283 | 3278718.2228 |  |  |  |  |

| outcome | age_bin | estimate_vs_006_023 | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- |
| sum_bits_exact_word_count | 006-023 | 0.0000 |  |  |  |
| sum_bits_exact_word_count | 024-029 | -0.9133 | -1.5839 | -0.2427 | 0.0076 |
| sum_bits_exact_word_count | 030-035 | -2.0527 | -2.8777 | -1.2276 | 1.08e-06 |
| sum_bits_exact_word_count | 036-041 | -2.0425 | -3.8048 | -0.2802 | 0.0231 |
| sum_bits_exact_word_count | 042-047 | -4.2539 | -7.0300 | -1.4777 | 0.0027 |
| sum_bits_exact_word_count | 048-053 | -2.6895 | -4.1492 | -1.2299 | 3.05e-04 |
| sum_bits_exact_word_count | 054-059 | -3.3198 | -4.7708 | -1.8687 | 7.33e-06 |
| sum_bits_exact_word_count | 060-065 | -8.4282 | -9.9811 | -6.8754 | 1.99e-26 |

![Controlled age effects](../figs/developmental_onset_report/controlled_real_child_age_effects.png)

Sensitivity check: when the data are first collapsed to child-by-age-bin cells and then modeled with mean word count, the simple age-bin effect is not the same. This is useful caution for peer review: the onset claim should be tied to the utterance-level fixed-effort model, and the child-age aggregate should be reported as a weighting sensitivity rather than ignored.

| outcome | formula | n_child_age_cells | r2 | aic |
| --- | --- | --- | --- | --- |
| mean_sum_bits | mean_sum_bits ~ mean_words + C(child_id) + C(age_bin) | 77.0000 | 0.9813 | 240.9756 |
| mean_bits_per_word | mean_bits_per_word ~ mean_words + C(child_id) + C(age_bin) | 77.0000 | 0.9133 | 157.6221 |

| outcome | age_bin | estimate_vs_006_023 | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- |
| mean_sum_bits | 006-023 | 0.0000 |  |  |  |
| mean_sum_bits | 024-029 | 1.4138 | 0.0539 | 2.7738 | 0.0416 |
| mean_sum_bits | 030-035 | 1.8327 | -0.1059 | 3.7713 | 0.0639 |
| mean_sum_bits | 036-041 | 3.1723 | 0.6815 | 5.6632 | 0.0126 |
| mean_sum_bits | 042-047 | 1.9685 | -1.5838 | 5.5208 | 0.2774 |
| mean_sum_bits | 048-053 | 4.8050 | 0.3137 | 9.2962 | 0.0360 |
| mean_sum_bits | 054-059 | 4.6370 | 0.6372 | 8.6369 | 0.0231 |
| mean_sum_bits | 060-065 | 0.1216 | -39.7302 | 39.9733 | 0.9952 |
| mean_bits_per_word | 006-023 | 0.0000 |  |  |  |
| mean_bits_per_word | 024-029 | 0.3676 | -0.3268 | 1.0620 | 0.2995 |
| mean_bits_per_word | 030-035 | 0.4528 | -0.5290 | 1.4345 | 0.3660 |
| mean_bits_per_word | 036-041 | 1.0662 | -0.3476 | 2.4799 | 0.1394 |
| mean_bits_per_word | 042-047 | 1.1441 | -0.8312 | 3.1195 | 0.2563 |
| mean_bits_per_word | 048-053 | 2.0739 | -0.3313 | 4.4792 | 0.0910 |
| mean_bits_per_word | 054-059 | 2.3314 | -0.0040 | 4.6669 | 0.0504 |
| mean_bits_per_word | 060-065 | 0.6017 | -128.3359 | 129.5394 | 0.9927 |

## Change-Point Scan

The change-point scan is deliberately simple: fit a linear utterance-level fixed-word-count age model and a set of piecewise linear models with candidate breakpoints. This does not prove a biological phase transition, but it tells us where the descriptive elbow is strongest under this model family.

Best-supported breakpoint rows:

| outcome | breakpoint_month | aic | delta_aic_vs_best | r2 | age_slope | post_break_slope_change | post_break_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Total bits with exact word-count control | 44.5000 | 3278532.3180 | 0.0000 | 0.6285 | -0.1731 | 0.2237 | 0.0110 |

Full change-point table:

| outcome | breakpoint_month | delta_aic_vs_best | r2 | age_slope | post_break_slope_change | post_break_p |
| --- | --- | --- | --- | --- | --- | --- |
| sum_bits_exact_word_count | linear_no_break | 496.7522 | 0.6281 | -0.1316 |  |  |
| sum_bits_exact_word_count | 23.0 | 460.9804 | 0.6281 | -0.2206 | 0.0958 | 0.5587 |
| sum_bits_exact_word_count | 26.5 | 370.4760 | 0.6282 | -0.2243 | 0.1118 | 0.1530 |
| sum_bits_exact_word_count | 29.0 | 292.5280 | 0.6282 | -0.2124 | 0.1120 | 0.0449 |
| sum_bits_exact_word_count | 32.5 | 115.1357 | 0.6284 | -0.2028 | 0.1292 | 0.0038 |
| sum_bits_exact_word_count | 35.0 | 113.1541 | 0.6284 | -0.1894 | 0.1281 | 0.0014 |
| sum_bits_exact_word_count | 38.5 | 163.3770 | 0.6284 | -0.1766 | 0.1313 | 0.0071 |
| sum_bits_exact_word_count | 44.5 | 0.0000 | 0.6285 | -0.1731 | 0.2237 | 0.0110 |
| sum_bits_exact_word_count | 50.5 | 212.2467 | 0.6283 | -0.1547 | 0.3155 | 0.0044 |

![Change-point scan](../figs/developmental_onset_report/piecewise_changepoint_scan.png)

## Paired Real-Versus-Baseline Timing

These are child-age-cell summaries of same-context generated baselines. Positive means the baseline has higher bits/token than the real child response.

| signal | source_model | earliest_age_bin_ci_positive | estimate_at_onset | ci_low_at_onset | ci_high_at_onset |
| --- | --- | --- | --- | --- | --- |
| Direct Mistral paired gap | random | 006-023 | 2.864 | 2.547 | 3.180 |
| Bayes decomposition paired gap | random | 006-023 | 13.981 | 12.728 | 15.234 |
| Direct Mistral paired gap | unigram | 006-023 | 2.306 | 1.995 | 2.616 |
| Bayes decomposition paired gap | unigram | 006-023 | 3.702 | 2.802 | 4.601 |
| Direct Mistral paired gap | bigram | 006-023 | 1.348 | 1.093 | 1.603 |
| Bayes decomposition paired gap | bigram | 006-023 | 2.533 | 1.751 | 3.316 |
| Direct Mistral paired gap | trigram | 006-023 | 0.745 | 0.576 | 0.913 |
| Bayes decomposition paired gap | trigram | 006-023 | 1.604 | 1.055 | 2.154 |

![Paired baseline gaps](../figs/developmental_onset_report/paired_real_advantage_onset.png)

## Context-Modulation Timing

This is the closest direct answer to the meeting concern about whether context begins to matter at a particular developmental point. Negative coefficients mean higher context entropy or longer parent context predicts lower child total bits within that age bin, after the controls used in the Yang follow-up analysis.

| outcome | predictor | earliest_age_bin_ci_negative | negative_estimate_at_onset | earliest_age_bin_ci_positive | positive_estimate_at_onset |
| --- | --- | --- | --- | --- | --- |
| child sum_bits | context entropy | 006-023 | -0.435 |  |  |
| child sum_bits | parent context words | 024-029 | -0.028 |  |  |
| child word count | context entropy |  |  | 024-029 | 0.025 |
| child word count | parent context words |  |  | 006-023 | 0.013 |

![Context modulation timing](../figs/developmental_onset_report/context_modulation_onset.png)

## Complexity Timing As A Check

These are descriptive child-age-bin summaries for MLU-style and lexical predictors. They should be treated as timing controls and developmental descriptors, not as substitutes for information-theoretic CE.

| age_bin | n_cells | mean_words_per_utterance_mean | mean_words_per_utterance_ci_low | mean_words_per_utterance_ci_high | age_bin_vocab_size_mean | age_bin_vocab_size_ci_low | age_bin_vocab_size_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 006-023 | 17.000 | 1.727 | 1.548 | 1.907 | 651.706 | 380.975 | 922.436 |
| 024-029 | 21.000 | 2.349 | 2.093 | 2.606 | 1173.476 | 980.865 | 1366.088 |
| 030-035 | 20.000 | 2.840 | 2.609 | 3.071 | 1372.550 | 1209.493 | 1535.607 |
| 036-041 | 8.000 | 3.193 | 2.829 | 3.557 | 1170.500 | 765.864 | 1575.136 |
| 042-047 | 5.000 | 3.875 | 3.341 | 4.409 | 1192.000 | 807.030 | 1576.970 |
| 048-053 | 3.000 | 3.703 | 2.781 | 4.624 | 1270.333 | 347.651 | 2193.016 |
| 054-059 | 2.000 | 4.156 | 3.342 | 4.970 | 1661.500 | 1405.720 | 1917.280 |
| 060-065 | 2.000 | 4.068 | 3.112 | 5.023 | 710.500 | 658.560 | 762.440 |

Adjusted complexity effects relative to `006-023`:

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

![Complexity timing](../figs/developmental_onset_report/complexity_timing_checks.png)

## Current Scientific Read

- The safest phrasing is not "CE starts at exactly month X." The defensible claim is: **the fixed-word-count age-bin decrease is already detectable by 024-029, context-entropy modulation is visible in 006-023, and parent-context-word modulation becomes detectable in 024-029.**
- For supervisor-facing material, the strongest presentation is likely an onset map plus one controlled age-effect plot and one paired real-versus-trigram plot.
- Before promotion to the July report, the next robustness step should bootstrap by child and repeat the onset table for alternative effort controls: words, morphemes, syllables, and phoneme proxies.

## Outputs

- Working tables: `results/developmental_onset_report/`
- Figures: `figs/developmental_onset_report/`
- HTML report: `docs/developmental_onset_working_report.html`
