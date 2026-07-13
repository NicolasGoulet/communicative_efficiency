# When CE Kicks In

This page answers the supervisor question about timing: not just whether there is a downward trend, but **when the signal becomes detectable**.

## Key Read

- The fixed-word-count age-bin decrease is detectable by `024-029`.
- Context entropy modulation is detectable already in `006-023`.
- Parent-context-word modulation becomes detectable in `024-029`.
- Same-context real-vs-baseline advantages are already positive in `006-023`.

## Onset Summary

| signal | operational_definition | earliest_age_bin | estimate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| Continuous fixed-word-count age slope | utterance-level OLS with child fixed effects, exact/top-coded word-count controls, child-clustered SEs | whole range | -0.132 | -0.180 | -0.083 |
| Earliest exact-word-count age-bin decrease | age-bin model relative to 006-023 with child fixed effects and exact/top-coded word-count controls | 024-029 | -0.913 | -1.584 | -0.243 |
| context entropy modulation | age-specific regression coefficient predicting child total bits | 006-023 | -0.435 |  |  |
| parent context words modulation | age-specific regression coefficient predicting child total bits | 024-029 | -0.028 |  |  |
| Direct Mistral paired gap against trigram | same-context generated baseline minus real child bits/token; positive means real child has lower bits | 006-023 | 0.745 | 0.576 | 0.913 |
| Bayes decomposition paired gap against trigram | same-context generated baseline minus real child bits/token; positive means real child has lower bits | 006-023 | 1.604 | 1.055 | 2.154 |

![Onset signal map](../figs/developmental_onset_report/onset_signal_map.png)

## Fixed-Effort Age-Bin Model

| age_bin | estimate_vs_006_023 | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- |
| 006-023 | 0.0000 |  |  |  |
| 024-029 | -0.9133 | -1.5839 | -0.2427 | 0.0076 |
| 030-035 | -2.0527 | -2.8777 | -1.2276 | 1.08e-06 |
| 036-041 | -2.0425 | -3.8048 | -0.2802 | 0.0231 |
| 042-047 | -4.2539 | -7.0300 | -1.4777 | 0.0027 |
| 048-053 | -2.6895 | -4.1492 | -1.2299 | 3.05e-04 |
| 054-059 | -3.3198 | -4.7708 | -1.8687 | 7.33e-06 |
| 060-065 | -8.4282 | -9.9811 | -6.8754 | 1.99e-26 |

![Controlled real child age effects](../figs/developmental_onset_report/controlled_real_child_age_effects.png)

## Change-Point Scan

| breakpoint_month | delta_aic_vs_best | r2 | age_slope | post_break_slope_change | post_break_p |
| --- | --- | --- | --- | --- | --- |
| 44.5 | 0.0000 | 0.6285 | -0.1731 | 0.2237 | 0.0110 |

![Piecewise change-point scan](../figs/developmental_onset_report/piecewise_changepoint_scan.png)

## Paired Baseline Onset

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

![Paired real advantage onset](../figs/developmental_onset_report/paired_real_advantage_onset.png)

## Context Modulation

| outcome | predictor | earliest_age_bin_ci_negative | negative_estimate_at_onset | earliest_age_bin_ci_positive | positive_estimate_at_onset |
| --- | --- | --- | --- | --- | --- |
| child sum_bits | context entropy | 006-023 | -0.435 |  |  |
| child sum_bits | parent context words | 024-029 | -0.028 |  |  |
| child word count | context entropy |  |  | 024-029 | 0.025 |
| child word count | parent context words |  |  | 006-023 | 0.013 |

![Context modulation onset](../figs/developmental_onset_report/context_modulation_onset.png)
