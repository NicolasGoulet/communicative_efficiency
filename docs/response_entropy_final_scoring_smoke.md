# Route 2 Final Entropy Scoring Smoke

Created: 2026-06-16

This report scores the already generated final Route 2 response samples. No new
responses were generated. The entropy predictors below are computed from
accepted sampled child-turn strings, not from real child utterances.

## What Was Generated Versus What Was Scored

The generation smoke produced candidate child responses from Mistral. This
scoring smoke reads those artifacts, counts accepted response types, computes
entropy features, and joins those features back to real child rows for a small
plumbing model.

| artifact | rows | contexts | settings |
| --- | --- | --- | --- |
| accepted_samples.csv.gz | 9512 | 40 | 478 |
| all_attempts.csv.gz | 1.02e+04 | 40 | 480 |
| rejection_summary_by_setting.csv | 480 | 40 | 480 |

## Entropy Formula

For each context, prompt variant, and temperature, accepted sampled responses
are normalized into response types. The empirical response entropy is:

```text
H(response | context) = - sum_r p_hat(r | c) log2 p_hat(r | c)
p_hat(r | c) = count(response_type = r) / accepted_sample_count
```

The primary predictor reported here is Miller-Madow corrected entropy in bits.
Settings with zero accepted samples remain in the feature table but have blank
entropy values.

## Normalization Choices

Primary type counting uses `casefold`: trim leading/trailing whitespace,
collapse internal whitespace, and ignore case while preserving punctuation.
The feature table also includes exact whitespace-normalized entropy and a
punctuation-stripped casefold sensitivity column.

## Entropy Features

| temperature | settings | mean_entropy_bits | mean_unique_responses | mean_top_probability | mean_sample_words |
| --- | --- | --- | --- | --- | --- |
| 0.3 | 118 | 2.274 | 7.356 | 0.5133 | 3.641 |
| 0.5 | 120 | 3.326 | 11.64 | 0.3486 | 3.787 |
| 0.7 | 120 | 4.062 | 15.08 | 0.2322 | 4.016 |
| 1 | 120 | 4.766 | 18.67 | 0.1013 | 5.122 |

![entropy distribution by temperature](../figs/response_entropy_final_scoring_smoke/entropy_distribution_by_temperature.png)

![entropy versus mean sampled length](../figs/response_entropy_final_scoring_smoke/entropy_vs_mean_sample_length.png)

## Sample-Size Stability

The final generation smoke targeted 20 accepted samples per setting, not 100.
Therefore the requested first-25/first-50 checks were adapted to available
prefix sizes:

```text
5, 10, 20
```

| comparison_family | prompt_variant | temperature | sample_size | shared_settings | spearman_r | pearson_r | mean_abs_entropy_diff_bits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sample_size_vs_full | Adult | 0.3 | 5 | 39 | 0.907 | 0.9015 | 0.7074 |
| sample_size_vs_full | Adult | 0.5 | 5 | 40 | 0.8202 | 0.8285 | 1.122 |
| sample_size_vs_full | Adult | 0.7 | 5 | 40 | 0.6461 | 0.777 | 1.451 |
| sample_size_vs_full | Adult | 1 | 5 | 40 | 0.5687 | 0.6339 | 1.935 |
| sample_size_vs_full | Caregiver | 0.3 | 5 | 39 | 0.8601 | 0.8825 | 0.6984 |
| sample_size_vs_full | Caregiver | 0.5 | 5 | 40 | 0.7769 | 0.775 | 1.378 |
| sample_size_vs_full | Caregiver | 0.7 | 5 | 40 | 0.6674 | 0.8564 | 1.407 |
| sample_size_vs_full | Caregiver | 1 | 5 | 40 | 0.5105 | 0.8027 | 1.937 |
| sample_size_vs_full | Parent | 0.3 | 5 | 39 | 0.8279 | 0.8449 | 0.8077 |
| sample_size_vs_full | Parent | 0.5 | 5 | 40 | 0.698 | 0.8173 | 1.25 |
| sample_size_vs_full | Parent | 0.7 | 5 | 40 | 0.8552 | 0.9652 | 1.62 |
| sample_size_vs_full | Parent | 1 | 5 | 40 | 0.5294 | 0.6272 | 1.984 |
| sample_size_vs_full | Adult | 0.3 | 10 | 39 | 0.9755 | 0.9708 | 0.323 |
| sample_size_vs_full | Adult | 0.5 | 10 | 39 | 0.9516 | 0.9542 | 0.5764 |
| sample_size_vs_full | Adult | 0.7 | 10 | 40 | 0.8653 | 0.932 | 0.7276 |
| sample_size_vs_full | Adult | 1 | 10 | 40 | 0.9333 | 0.9417 | 0.9511 |
| sample_size_vs_full | Caregiver | 0.3 | 10 | 39 | 0.9368 | 0.9518 | 0.3277 |
| sample_size_vs_full | Caregiver | 0.5 | 10 | 39 | 0.9429 | 0.9556 | 0.6522 |
| sample_size_vs_full | Caregiver | 0.7 | 10 | 40 | 0.857 | 0.9542 | 0.6941 |
| sample_size_vs_full | Caregiver | 1 | 10 | 40 | 0.7865 | 0.9826 | 0.9297 |
| sample_size_vs_full | Parent | 0.3 | 10 | 39 | 0.9661 | 0.9662 | 0.3691 |
| sample_size_vs_full | Parent | 0.5 | 10 | 40 | 0.9217 | 0.9577 | 0.5387 |
| sample_size_vs_full | Parent | 0.7 | 10 | 40 | 0.9154 | 0.9702 | 0.8077 |
| sample_size_vs_full | Parent | 1 | 10 | 40 | 0.7649 | 0.9754 | 0.9626 |
| sample_size_vs_full | Adult | 0.3 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Adult | 0.5 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Adult | 0.7 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Adult | 1 | 20 | 40 | 1 | 1 | 0 |
| sample_size_vs_full | Caregiver | 0.3 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Caregiver | 0.5 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Caregiver | 0.7 | 20 | 40 | 1 | 1 | 0 |
| sample_size_vs_full | Caregiver | 1 | 20 | 40 | 1 | 1 | 0 |
| sample_size_vs_full | Parent | 0.3 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Parent | 0.5 | 20 | 39 | 1 | 1 | 0 |
| sample_size_vs_full | Parent | 0.7 | 20 | 40 | 1 | 1 | 0 |
| sample_size_vs_full | Parent | 1 | 20 | 40 | 1 | 1 | 0 |

| prompt_variant | temperature | settings | spearman_r | pearson_r | mean_abs_diff_bits | median_abs_diff_bits |
| --- | --- | --- | --- | --- | --- | --- |
| Adult | 0.3 | 39 | 0.8807 | 0.8851 | 0.427 | 0.2721 |
| Adult | 0.5 | 40 | 0.8385 | 0.8493 | 0.4631 | 0.3099 |
| Adult | 0.7 | 40 | 0.6307 | 0.7613 | 0.4164 | 0.325 |
| Adult | 1 | 40 | 0.763 | 0.8107 | 0.07681 | 0 |
| Caregiver | 0.3 | 39 | 0.8292 | 0.8523 | 0.4602 | 0.2721 |
| Caregiver | 0.5 | 40 | 0.8119 | 0.8528 | 0.4265 | 0.2721 |
| Caregiver | 0.7 | 40 | 0.6742 | 0.8674 | 0.3243 | 0.2721 |
| Caregiver | 1 | 40 | 0.6546 | 0.9694 | 0.05631 | 0 |
| Parent | 0.3 | 39 | 0.9187 | 0.9128 | 0.4016 | 0.2781 |
| Parent | 0.5 | 40 | 0.7915 | 0.8608 | 0.3981 | 0.2721 |
| Parent | 0.7 | 40 | 0.7592 | 0.8862 | 0.2984 | 0.2721 |
| Parent | 1 | 40 | 0.6894 | 0.9267 | 0.06623 | 0 |

![sample-size stability plot](../figs/response_entropy_final_scoring_smoke/sample_size_stability.png)

## Temperature And Prompt Sensitivity

Temperature correlations compare context entropy rankings across temperatures
within the same prompt wrapper. Prompt correlations compare wrappers within the
same temperature.

| comparison_family | prompt_variant | temperature_a | temperature_b | shared_contexts | spearman_r | pearson_r | mean_abs_entropy_diff_bits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| temperature_within_prompt | Adult | 0.3 | 0.5 | 39 | 0.8555 | 0.8408 | 0.9811 |
| temperature_within_prompt | Adult | 0.3 | 0.7 | 39 | 0.6838 | 0.6274 | 1.955 |
| temperature_within_prompt | Adult | 0.3 | 1 | 39 | 0.3607 | 0.3414 | 2.702 |
| temperature_within_prompt | Adult | 0.5 | 0.7 | 40 | 0.812 | 0.806 | 1.042 |
| temperature_within_prompt | Adult | 0.5 | 1 | 40 | 0.5753 | 0.5266 | 1.745 |
| temperature_within_prompt | Adult | 0.7 | 1 | 40 | 0.7661 | 0.7865 | 0.7447 |
| temperature_within_prompt | Caregiver | 0.3 | 0.5 | 39 | 0.9088 | 0.9216 | 1.169 |
| temperature_within_prompt | Caregiver | 0.3 | 0.7 | 39 | 0.809 | 0.7965 | 1.77 |
| temperature_within_prompt | Caregiver | 0.3 | 1 | 39 | 0.5216 | 0.4132 | 2.435 |
| temperature_within_prompt | Caregiver | 0.5 | 0.7 | 40 | 0.8149 | 0.8927 | 0.6833 |
| temperature_within_prompt | Caregiver | 0.5 | 1 | 40 | 0.6143 | 0.5746 | 1.294 |
| temperature_within_prompt | Caregiver | 0.7 | 1 | 40 | 0.5614 | 0.7128 | 0.6877 |
| temperature_within_prompt | Parent | 0.3 | 0.5 | 40 | 0.9028 | 0.8666 | 1.059 |
| temperature_within_prompt | Parent | 0.3 | 0.7 | 40 | 0.7411 | 0.7072 | 1.626 |
| temperature_within_prompt | Parent | 0.3 | 1 | 40 | 0.5701 | 0.4567 | 2.329 |
| temperature_within_prompt | Parent | 0.5 | 0.7 | 40 | 0.8229 | 0.8947 | 0.6551 |
| temperature_within_prompt | Parent | 0.5 | 1 | 40 | 0.7035 | 0.6695 | 1.279 |
| temperature_within_prompt | Parent | 0.7 | 1 | 40 | 0.6963 | 0.8113 | 0.7085 |

![temperature rank-correlation heatmap](../figs/response_entropy_final_scoring_smoke/temperature_rank_correlation_heatmap.png)

| comparison_family | temperature | prompt_variant_a | prompt_variant_b | shared_contexts | spearman_r | pearson_r | mean_abs_entropy_diff_bits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| prompt_within_temperature | 0.3 | Adult | Caregiver | 39 | 0.605 | 0.6216 | 0.9223 |
| prompt_within_temperature | 0.3 | Adult | Parent | 39 | 0.4867 | 0.5165 | 1.069 |
| prompt_within_temperature | 0.3 | Caregiver | Parent | 39 | 0.6187 | 0.617 | 0.909 |
| prompt_within_temperature | 0.5 | Adult | Caregiver | 40 | 0.7439 | 0.7319 | 0.8365 |
| prompt_within_temperature | 0.5 | Adult | Parent | 40 | 0.7321 | 0.7155 | 0.8967 |
| prompt_within_temperature | 0.5 | Caregiver | Parent | 40 | 0.7674 | 0.8208 | 0.5416 |
| prompt_within_temperature | 0.7 | Adult | Caregiver | 40 | 0.7323 | 0.7532 | 0.537 |
| prompt_within_temperature | 0.7 | Adult | Parent | 40 | 0.7186 | 0.7551 | 0.5461 |
| prompt_within_temperature | 0.7 | Caregiver | Parent | 40 | 0.7869 | 0.8236 | 0.4273 |
| prompt_within_temperature | 1.0 | Adult | Caregiver | 40 | 0.5797 | 0.2982 | 0.29 |
| prompt_within_temperature | 1.0 | Adult | Parent | 40 | 0.6668 | 0.4069 | 0.2189 |
| prompt_within_temperature | 1.0 | Caregiver | Parent | 40 | 0.5916 | 0.8992 | 0.178 |

![prompt variant rank-correlation heatmap](../figs/response_entropy_final_scoring_smoke/prompt_variant_rank_correlation_heatmap.png)

## Join Audit

The join uses the normalized context-text hash, not row position. The output
analysis smoke writes only matched real-child rows expanded over
prompt-temperature settings; the audit still counts the full eligible real
child frame so unsampled contexts remain visible.

| metric | value |
| --- | --- |
| eligible_real_child_rows | 1332975 |
| matched_real_child_rows | 519 |
| missing_real_child_rows | 1332456 |
| finite_entropy_source_rows | 519 |
| expanded_join_rows_written | 6228 |
| sampled_contexts_available | 40 |
| finite_entropy_contexts_available | 40 |
| unique_matched_contexts | 40 |
| unique_missing_contexts_observed | 700608 |
| output_truncated | False |
| output_csv | results/response_entropy_final_scoring_smoke/route2_analysis_smoke_with_entropy.csv.gz |

![joined versus missing entropy audit](../figs/response_entropy_final_scoring_smoke/joined_missing_entropy_audit.png)

Duplicate context-window checks show whether identical text appearing as k1,
k2, or k3 reused one deduplicated entropy feature set.

| audit_type | metric | value | context_id | real_child_rows | context_k_values_observed | context_text | prompt_variant | temperature | accepted_sample_count | target_accepted_samples | attempt_count | rejection_rate | finite_entropy | observed_context_k_count | deduplicated_by_text | feature_settings | finite_entropy_settings | prompt_variants | temperatures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| duplicate_context_window_check |  |  | 5159122a0ac41bf1eab0e9de |  | k1;k2;k3 | well. |  |  |  |  |  |  |  | 3 | True | 12 | 12 | Adult;Caregiver;Parent | 0.3;0.5;0.7;1.0 |

## Tiny Downstream Sanity Model

This is a plumbing check, not final science:

```text
real_child_words ~ response_entropy + mean_sample_words + context_word_count + age
```

The same smoke was attempted for morphemes, syllables, and phonemes when the
joined frame had enough variation.

| prompt_variant | temperature | outcome | n_rows | estimate | std_error | p_value | r_squared | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 0.3 | real_child_words | 517 | -0.4897 | 0.1041 | 3.261e-06 | 0.1065 | fitted_smoke_only |
| Adult | 0.3 | real_child_morphemes | 517 | -0.5643 | 0.1158 | 1.469e-06 | 0.1127 | fitted_smoke_only |
| Adult | 0.3 | real_child_syllables | 517 | -0.6237 | 0.134 | 4.164e-06 | 0.08929 | fitted_smoke_only |
| Adult | 0.3 | real_child_phonemes | 517 | -1.359 | 0.3331 | 5.238e-05 | 0.07158 | fitted_smoke_only |
| Adult | 0.5 | real_child_words | 519 | -0.5276 | 0.1003 | 2.093e-07 | 0.1157 | fitted_smoke_only |
| Adult | 0.5 | real_child_morphemes | 519 | -0.6004 | 0.1116 | 1.13e-07 | 0.122 | fitted_smoke_only |
| Adult | 0.5 | real_child_syllables | 519 | -0.6476 | 0.1296 | 7.955e-07 | 0.09251 | fitted_smoke_only |
| Adult | 0.5 | real_child_phonemes | 519 | -1.508 | 0.3214 | 3.46e-06 | 0.07886 | fitted_smoke_only |
| Adult | 0.7 | real_child_words | 519 | -0.1464 | 0.09471 | 0.1228 | 0.07167 | fitted_smoke_only |
| Adult | 0.7 | real_child_morphemes | 519 | -0.186 | 0.1055 | 0.07828 | 0.07734 | fitted_smoke_only |
| Adult | 0.7 | real_child_syllables | 519 | -0.1628 | 0.1221 | 0.1829 | 0.05176 | fitted_smoke_only |
| Adult | 0.7 | real_child_phonemes | 519 | -0.3714 | 0.3021 | 0.2195 | 0.04217 | fitted_smoke_only |
| Adult | 1 | real_child_words | 519 | -0.2844 | 0.3219 | 0.3774 | 0.08173 | fitted_smoke_only |
| Adult | 1 | real_child_morphemes | 519 | -0.3929 | 0.3581 | 0.2731 | 0.08883 | fitted_smoke_only |
| Adult | 1 | real_child_syllables | 519 | -0.5221 | 0.414 | 0.2078 | 0.06647 | fitted_smoke_only |
| Adult | 1 | real_child_phonemes | 519 | -1.106 | 1.026 | 0.2819 | 0.05313 | fitted_smoke_only |
| Caregiver | 0.3 | real_child_words | 517 | -0.6391 | 0.1419 | 8.283e-06 | 0.1049 | fitted_smoke_only |
| Caregiver | 0.3 | real_child_morphemes | 517 | -0.6821 | 0.1586 | 2.031e-05 | 0.1039 | fitted_smoke_only |
| Caregiver | 0.3 | real_child_syllables | 517 | -0.7634 | 0.1833 | 3.638e-05 | 0.08277 | fitted_smoke_only |
| Caregiver | 0.3 | real_child_phonemes | 517 | -1.686 | 0.4548 | 0.0002325 | 0.06765 | fitted_smoke_only |
| Caregiver | 0.5 | real_child_words | 519 | -0.4782 | 0.1638 | 0.003648 | 0.08298 | fitted_smoke_only |
| Caregiver | 0.5 | real_child_morphemes | 519 | -0.4569 | 0.1829 | 0.01278 | 0.08317 | fitted_smoke_only |
| Caregiver | 0.5 | real_child_syllables | 519 | -0.5673 | 0.2112 | 0.007467 | 0.06243 | fitted_smoke_only |
| Caregiver | 0.5 | real_child_phonemes | 519 | -1.223 | 0.5235 | 0.01986 | 0.04955 | fitted_smoke_only |
| Caregiver | 0.7 | real_child_words | 519 | -0.4432 | 0.17 | 0.009408 | 0.08299 | fitted_smoke_only |
| Caregiver | 0.7 | real_child_morphemes | 519 | -0.4342 | 0.1896 | 0.02244 | 0.08582 | fitted_smoke_only |
| Caregiver | 0.7 | real_child_syllables | 519 | -0.384 | 0.22 | 0.08146 | 0.05673 | fitted_smoke_only |
| Caregiver | 0.7 | real_child_phonemes | 519 | -0.9509 | 0.5444 | 0.08129 | 0.04676 | fitted_smoke_only |
| Caregiver | 1 | real_child_words | 519 | 0.4446 | 0.2302 | 0.05396 | 0.09854 | fitted_smoke_only |
| Caregiver | 1 | real_child_morphemes | 519 | 0.4756 | 0.2563 | 0.06413 | 0.1037 | fitted_smoke_only |
| Caregiver | 1 | real_child_syllables | 519 | 0.6136 | 0.2964 | 0.03889 | 0.08169 | fitted_smoke_only |
| Caregiver | 1 | real_child_phonemes | 519 | 1.589 | 0.7362 | 0.03132 | 0.06512 | fitted_smoke_only |
| Parent | 0.3 | real_child_words | 519 | -0.2562 | 0.09126 | 0.005176 | 0.0944 | fitted_smoke_only |
| Parent | 0.3 | real_child_morphemes | 519 | -0.2947 | 0.1016 | 0.003889 | 0.09965 | fitted_smoke_only |
| Parent | 0.3 | real_child_syllables | 519 | -0.2968 | 0.1177 | 0.01194 | 0.07483 | fitted_smoke_only |
| Parent | 0.3 | real_child_phonemes | 519 | -0.6103 | 0.2924 | 0.03733 | 0.05758 | fitted_smoke_only |
| Parent | 0.5 | real_child_words | 519 | -0.2692 | 0.1103 | 0.01497 | 0.09161 | fitted_smoke_only |
| Parent | 0.5 | real_child_morphemes | 519 | -0.3032 | 0.1227 | 0.01382 | 0.09769 | fitted_smoke_only |
| Parent | 0.5 | real_child_syllables | 519 | -0.2828 | 0.1423 | 0.04744 | 0.07001 | fitted_smoke_only |
| Parent | 0.5 | real_child_phonemes | 519 | -0.6177 | 0.3531 | 0.08086 | 0.05508 | fitted_smoke_only |

## Recommendation For Supervisor Meeting

Use this as evidence that the Route 2 measurement pipeline is now implemented:
accepted child-turn samples can be transformed into context-level response
entropy predictors and joined back to real child effort rows. The smoke remains
too small to certify 100 accepted responses per context; it is a final
pre-production feature and stability smoke, not the production analysis.

## Questions That Remain Before Full Production

- Should production use the `Caregiver`, `Parent`, or `Adult` wrapper, given
  the observed prompt sensitivity?
- Should T=0.5 be the primary estimate and T=0.7 a sensitivity estimate?
- Should contexts that repeatedly fail acceptance be excluded, resampled with a
  higher attempt cap, or retained as missing entropy?
- Should the production analysis average across prompts/temperatures or commit
  to one primary operational definition?

## Decision Output

| question | answer | evidence |
| --- | --- | --- |
| Is the entropy script ready to consume full Mila-scale samples? | yes, as a CPU feature builder; full production still needs full sample artifacts | wrote 478 finite entropy settings from final-smoke CSVs without regeneration |
| Are the generated samples stable enough for 100 accepted responses per context? | not directly answerable from this final smoke | final smoke has at most 20 accepted samples per setting; 100-sample stability must be checked on full/pilot samples |
| Do T=0.5 and T=0.7 give similar context rankings? | mostly similar in this smoke | median within-prompt Spearman for T=0.5 versus T=0.7 = 0.815 |
| Does prompt wording materially change the predictor? | yes, enough to keep prompt wording visible as a design choice | median prompt-within-temperature Spearman = 0.693 |
| Are join gaps small and explainable? | explainable but not small for the full frame, because this is a 40-context smoke | matched real child rows = 519; missing full-frame rows = 1332456 |
| What exact summary should be sent to supervisors? | the measurement pipeline works; final-smoke entropy favors T=0.5 primary with T=0.7 sensitivity, but 20 samples cannot certify 100-sample production stability | 473/480 settings reached 20 accepted samples; pathological incomplete settings remain auditable |
| Did first-20 stability prove full-sample stability? | only within this small smoke cap | median M=20 Spearman versus full = 1 |
| Was k1/k2/k3 duplicate context text handled? | yes, joins use the normalized context-text hash | duplicate context-window rows in the join audit share one entropy feature set by context text |

## Output Files

- Feature table: `results/response_entropy_final_scoring_smoke/context_response_entropy_features.csv`
- Stability table: `results/response_entropy_final_scoring_smoke/context_response_entropy_stability.csv`
- Join audit: `results/response_entropy_final_scoring_smoke/context_response_entropy_join_audit.csv`
- Temperature correlations: `results/response_entropy_final_scoring_smoke/context_response_entropy_temperature_correlations.csv`
- Prompt correlations: `results/response_entropy_final_scoring_smoke/context_response_entropy_prompt_correlations.csv`
- Joined analysis smoke: `results/response_entropy_final_scoring_smoke/route2_analysis_smoke_with_entropy.csv.gz`
- Tiny model summary: `results/response_entropy_final_scoring_smoke/route2_sanity_model_summary.csv`
- Manual review examples: `results/response_entropy_final_scoring_smoke/manual_review_entropy_examples.csv`
- Figures: `figs/response_entropy_final_scoring_smoke`
