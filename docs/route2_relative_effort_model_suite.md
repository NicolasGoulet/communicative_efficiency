# Route 2 Relative-Effort Model Suite

This is the Route 2 effort-choice suite built from the production response-space run.
It asks whether real child utterance effort is short, typical, or long relative to the generated response-space length distribution for the same caregiver context.

It does not score generated responses for surprisal and does not claim generated samples are same-meaning paraphrases.

## Inputs

- Child-row response-space table: `results/route2_response_space/route2_child_response_space_effort_table.csv.gz`
- Output directory: `results/route2_relative_effort_model_suite`
- Figure directory: `figs/route2_relative_effort_model_suite`

## Audit

This suite covers `444325` child utterance rows, `268712` unique response-space contexts, `21` children, and `3` datasets.

| metric | value |
| --- | --- |
| input_rows | 4.443e+05 |
| modelable_rows_percentile | 4.443e+05 |
| unique_score_ids | 4.443e+05 |
| unique_utterance_ids | 4.443e+05 |
| unique_children | 21 |
| unique_datasets | 3 |
| unique_response_entropy_contexts | 2.687e+05 |
| fallback_rows | 218 |
| fallback_contexts | 176 |
| fit_models | 144 |
| failed_or_no_fit_models | 0 |

## Headline Results

The descriptive Route 2 result is strong: real child utterances are usually shorter than the generated response-space distribution for the same caregiver context, and this gap shrinks with age.
In the youngest bin, children are on average about 2.28 words below the generated mean and around the 25th percentile of the generated length distribution; by later bins they are closer to the generated distribution but still below its center.

| age_bin | child_words_minus_generated_mean | child_percentile | shorter_than_generated_median | longer_than_generated_p90 |
| --- | --- | --- | --- | --- |
| 006-023 | -2.277 | 0.2475 | 0.721 | 0.01758 |
| 024-029 | -1.927 | 0.301 | 0.6501 | 0.0288 |
| 030-035 | -1.548 | 0.3492 | 0.5879 | 0.04491 |
| 042-047 | -0.8286 | 0.4264 | 0.499 | 0.08223 |
| 048-053 | -0.7613 | 0.4411 | 0.4849 | 0.08312 |
| 060-065 | -0.7885 | 0.435 | 0.5059 | 0.07935 |

Response entropy has a large descriptive gradient: low-entropy contexts place child utterances near or above the generated midpoint, while high-entropy contexts place them far below it.

| response_entropy_bits_mean | n | child_words_minus_generated_mean | child_words_percentile_mean | shorter_than_generated_median_rate | longer_than_generated_p90_rate |
| --- | --- | --- | --- | --- | --- |
| 1.968 | 2.225e+04 | -0.03374 | 0.5495 | 0.2103 | 0.2233 |
| 2.992 | 2.219e+04 | -0.3796 | 0.4966 | 0.2427 | 0.1016 |
| 3.518 | 2.221e+04 | -0.6891 | 0.4499 | 0.3076 | 0.06545 |
| 6.488 | 2.221e+04 | -2.527 | 0.2339 | 0.8002 | 0.01549 |
| 6.667 | 2.223e+04 | -2.738 | 0.2159 | 0.8247 | 0.01354 |
| 6.937 | 2.22e+04 | -3.211 | 0.1872 | 0.8558 | 0.01324 |

The primary inferential check is the final child-session GEE model, with age, response entropy, generated expected effort, context length, context entropy, and the age x response-entropy interaction.
In that model, age predicts movement toward the generated distribution; generated expected effort predicts stronger child-shortening relative to the generated distribution; and the age x response-entropy interaction shows that developmental catch-up is weaker in higher-response-entropy contexts.
For the binary outcomes, the GEE coefficients are linear-probability changes in child-session rates.

| outcome | term | estimate | std_error | p_value | conf_low | conf_high |
| --- | --- | --- | --- | --- | --- | --- |
| child_longer_than_generated_p90 | age_months_c | 0.00383 | 0.0004281 | 3.721e-19 | 0.002991 | 0.004669 |
| child_longer_than_generated_p90 | age_months_c:response_entropy_bits_c | -0.001612 | 0.0003189 | 4.269e-07 | -0.002237 | -0.0009874 |
| child_longer_than_generated_p90 | context_entropy_bits_c | 1.162e-05 | 0.00612 | 0.9985 | -0.01198 | 0.01201 |
| child_longer_than_generated_p90 | generated_expected_words_c | -0.01659 | 0.005466 | 0.00241 | -0.0273 | -0.005873 |
| child_longer_than_generated_p90 | response_entropy_bits_c | -0.02486 | 0.004193 | 3.033e-09 | -0.03308 | -0.01664 |
| child_longer_than_generated_p90 | route2_context_word_count_c | 0.002845 | 0.000815 | 0.0004816 | 0.001248 | 0.004442 |
| child_shorter_than_generated_median | age_months_c | -0.01417 | 0.001063 | 1.517e-40 | -0.01625 | -0.01208 |
| child_shorter_than_generated_median | age_months_c:response_entropy_bits_c | 0.004251 | 0.0007948 | 8.882e-08 | 0.002693 | 0.005809 |
| child_shorter_than_generated_median | context_entropy_bits_c | 0.01879 | 0.01166 | 0.107 | -0.004061 | 0.04165 |
| child_shorter_than_generated_median | generated_expected_words_c | 0.1256 | 0.02034 | 6.688e-10 | 0.08571 | 0.1654 |
| child_shorter_than_generated_median | response_entropy_bits_c | 0.02627 | 0.02754 | 0.3402 | -0.02771 | 0.08024 |
| child_shorter_than_generated_median | route2_context_word_count_c | -0.01038 | 0.002309 | 6.971e-06 | -0.0149 | -0.005851 |
| child_words_minus_generated_mean | age_months_c | 0.08949 | 0.006005 | 3.145e-50 | 0.07772 | 0.1013 |
| child_words_minus_generated_mean | age_months_c:response_entropy_bits_c | -0.02478 | 0.006941 | 0.0003579 | -0.03838 | -0.01117 |
| child_words_minus_generated_mean | context_entropy_bits_c | -0.2063 | 0.0602 | 0.0006114 | -0.3243 | -0.08829 |
| child_words_minus_generated_mean | generated_expected_words_c | -0.9408 | 0.0717 | 2.47e-39 | -1.081 | -0.8003 |
| child_words_minus_generated_mean | response_entropy_bits_c | -0.001641 | 0.1149 | 0.9886 | -0.2268 | 0.2235 |
| child_words_minus_generated_mean | route2_context_word_count_c | 0.0344 | 0.01688 | 0.04152 | 0.001322 | 0.06747 |
| child_words_percentile_in_generated_distribution | age_months_c | 0.01075 | 0.0008856 | 6.129e-34 | 0.009019 | 0.01249 |
| child_words_percentile_in_generated_distribution | age_months_c:response_entropy_bits_c | -0.003412 | 0.000635 | 7.694e-08 | -0.004657 | -0.002168 |
| child_words_percentile_in_generated_distribution | context_entropy_bits_c | -0.001787 | 0.01097 | 0.8706 | -0.02329 | 0.01972 |
| child_words_percentile_in_generated_distribution | generated_expected_words_c | -0.07324 | 0.01547 | 2.179e-06 | -0.1036 | -0.04293 |
| child_words_percentile_in_generated_distribution | response_entropy_bits_c | -0.00716 | 0.02229 | 0.748 | -0.05084 | 0.03652 |
| child_words_percentile_in_generated_distribution | route2_context_word_count_c | 0.007066 | 0.001551 | 5.192e-06 | 0.004027 | 0.0101 |

The no-fallback sensitivity check preserves the core final-model estimates.

| outcome | term | estimate | p_value | conf_low | conf_high |
| --- | --- | --- | --- | --- | --- |
| child_longer_than_generated_p90 | age_months_c:response_entropy_bits_c | -0.001612 | 4.534e-07 | -0.002238 | -0.0009858 |
| child_longer_than_generated_p90 | generated_expected_words_c | -0.01676 | 0.002281 | -0.02753 | -0.005994 |
| child_longer_than_generated_p90 | response_entropy_bits_c | -0.02475 | 3.007e-09 | -0.03293 | -0.01657 |
| child_shorter_than_generated_median | age_months_c:response_entropy_bits_c | 0.004268 | 1.335e-07 | 0.002682 | 0.005854 |
| child_shorter_than_generated_median | generated_expected_words_c | 0.1255 | 7.963e-10 | 0.08547 | 0.1655 |
| child_shorter_than_generated_median | response_entropy_bits_c | 0.02655 | 0.3394 | -0.02792 | 0.08102 |
| child_words_minus_generated_mean | age_months_c:response_entropy_bits_c | -0.02478 | 0.000344 | -0.03835 | -0.01121 |
| child_words_minus_generated_mean | generated_expected_words_c | -0.9365 | 3.293e-36 | -1.083 | -0.7904 |
| child_words_minus_generated_mean | response_entropy_bits_c | -0.00607 | 0.9585 | -0.2346 | 0.2225 |
| child_words_percentile_in_generated_distribution | age_months_c:response_entropy_bits_c | -0.003422 | 7.657e-08 | -0.00467 | -0.002174 |
| child_words_percentile_in_generated_distribution | generated_expected_words_c | -0.07305 | 3.496e-06 | -0.1039 | -0.04219 |
| child_words_percentile_in_generated_distribution | response_entropy_bits_c | -0.007428 | 0.7426 | -0.05177 | 0.03691 |

## Model Ladder

The main models are fit separately for each context-relative effort outcome:

- R2-M1: age + child identity.
- R2-M2: R2-M1 plus response entropy.
- R2-M3: age plus generated expected effort, context length, context entropy, and child identity.
- R2-M4: R2-M3 plus response entropy.
- R2-M5: R2-M4 plus age x response entropy.

Estimator checks include row-level child-fixed-effect clustered models, child-session GEE, child-session Mundlak GEE, and child-session mixed models with random age slopes where stable.

## Figures

### Route 2 relative effort by age

![Route 2 relative effort by age](../figs/route2_relative_effort_model_suite/route2_relative_effort_by_age.png)

### Route 2 relative effort by response entropy

![Route 2 relative effort by response entropy](../figs/route2_relative_effort_model_suite/route2_relative_effort_by_response_entropy.png)

### Route 2 final-model coefficients

![Route 2 final-model coefficients](../figs/route2_relative_effort_model_suite/route2_relative_effort_final_model_coefficients.png)

### Prediction lines: child_words_minus_generated_mean

![Prediction lines: child_words_minus_generated_mean](../figs/route2_relative_effort_model_suite/minus_gen_mean_r2m5_age_by_entropy_prediction_lines.png)

### Prediction lines: child_words_percentile_in_generated_distribution

![Prediction lines: child_words_percentile_in_generated_distribution](../figs/route2_relative_effort_model_suite/percentile_in_gen_distribution_r2m5_age_by_entropy_prediction_lines.png)

### Prediction lines: child_shorter_than_generated_median

![Prediction lines: child_shorter_than_generated_median](../figs/route2_relative_effort_model_suite/child_shorter_than_gen_median_r2m5_age_by_entropy_prediction_lines.png)

### Prediction lines: child_longer_than_generated_p90

![Prediction lines: child_longer_than_generated_p90](../figs/route2_relative_effort_model_suite/child_longer_than_gen_p90_r2m5_age_by_entropy_prediction_lines.png)

## Age-Bin Descriptives

| age_bin | age_bin_mid | metric | n | mean | median | sd | se | p10 | p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 006-023 | 14.5 | child_longer_than_generated_p90 | 6.274e+04 | 0.01758 | 0 | 0.1314 | 0.0005247 | 0 | 0 |
| 006-023 | 14.5 | child_shorter_than_generated_median | 6.274e+04 | 0.721 | 1 | 0.4485 | 0.001791 | 0 | 1 |
| 006-023 | 14.5 | child_words_minus_generated_mean | 6.274e+04 | -2.277 | -2.33 | 2.046 | 0.008169 | -4.59 | 0.01 |
| 006-023 | 14.5 | child_words_percentile_in_generated_distribution | 6.274e+04 | 0.2475 | 0.17 | 0.2426 | 0.0009686 | 0.01 | 0.63 |
| 006-023 | 14.5 | child_words_ratio_to_generated_mean | 6.274e+04 | 0.5327 | 0.4008 | 0.4606 | 0.001839 | 0.1883 | 1.005 |
| 006-023 | 14.5 | child_words_z_vs_generated | 6.266e+04 | -0.8695 | -0.9385 | 0.9278 | 0.003706 | -1.687 | 0.004668 |
| 006-023 | 14.5 | generated_expected_words | 6.274e+04 | 4.276 | 4.2 | 1.568 | 0.006258 | 2.36 | 6.18 |
| 006-023 | 14.5 | nb_words | 6.274e+04 | 1.999 | 2 | 1.428 | 0.005701 | 1 | 4 |
| 006-023 | 14.5 | response_entropy_bits | 6.274e+04 | 5.053 | 5.285 | 1.263 | 0.005042 | 3.265 | 6.5 |
| 024-029 | 26.5 | child_longer_than_generated_p90 | 1.619e+05 | 0.0288 | 0 | 0.1672 | 0.0004156 | 0 | 0 |
| 024-029 | 26.5 | child_shorter_than_generated_median | 1.619e+05 | 0.6501 | 1 | 0.4769 | 0.001185 | 0 | 1 |
| 024-029 | 26.5 | child_words_minus_generated_mean | 1.619e+05 | -1.927 | -2.05 | 2.201 | 0.005469 | -4.42 | 0.672 |
| 024-029 | 26.5 | child_words_percentile_in_generated_distribution | 1.619e+05 | 0.301 | 0.23 | 0.2643 | 0.0006568 | 0.02 | 0.725 |
| 024-029 | 26.5 | child_words_ratio_to_generated_mean | 1.619e+05 | 0.6287 | 0.4706 | 0.5621 | 0.001397 | 0.1957 | 1.223 |
| 024-029 | 26.5 | child_words_z_vs_generated | 1.617e+05 | -0.6917 | -0.7998 | 0.9909 | 0.002465 | -1.59 | 0.3037 |
| 024-029 | 26.5 | generated_expected_words | 1.619e+05 | 4.264 | 4.23 | 1.557 | 0.003871 | 2.27 | 6.19 |
| 024-029 | 26.5 | nb_words | 1.619e+05 | 2.336 | 2 | 1.679 | 0.004174 | 1 | 4 |
| 024-029 | 26.5 | response_entropy_bits | 1.619e+05 | 5.067 | 5.304 | 1.288 | 0.003201 | 3.218 | 6.543 |
| 030-035 | 32.5 | child_longer_than_generated_p90 | 1.415e+05 | 0.04491 | 0 | 0.2071 | 0.0005506 | 0 | 0 |
| 030-035 | 32.5 | child_shorter_than_generated_median | 1.415e+05 | 0.5879 | 1 | 0.4922 | 0.001309 | 0 | 1 |
| 030-035 | 32.5 | child_words_minus_generated_mean | 1.415e+05 | -1.548 | -1.74 | 2.532 | 0.006733 | -4.36 | 1.5 |
| 030-035 | 32.5 | child_words_percentile_in_generated_distribution | 1.415e+05 | 0.3492 | 0.285 | 0.2861 | 0.0007608 | 0.025 | 0.81 |
| 030-035 | 32.5 | child_words_ratio_to_generated_mean | 1.415e+05 | 0.7413 | 0.5535 | 0.6892 | 0.001832 | 0.2 | 1.474 |
| 030-035 | 32.5 | child_words_z_vs_generated | 1.413e+05 | -0.513 | -0.6767 | 1.153 | 0.003067 | -1.535 | 0.6656 |
| 030-035 | 32.5 | generated_expected_words | 1.415e+05 | 4.344 | 4.3 | 1.597 | 0.004246 | 2.3 | 6.3 |
| 030-035 | 32.5 | nb_words | 1.415e+05 | 2.797 | 2 | 2.075 | 0.005516 | 1 | 5 |
| 030-035 | 32.5 | response_entropy_bits | 1.415e+05 | 5.115 | 5.368 | 1.291 | 0.003432 | 3.264 | 6.579 |
| 036-041 | 38.5 | child_longer_than_generated_p90 | 3.735e+04 | 0.06128 | 0 | 0.2399 | 0.001241 | 0 | 0 |
| 036-041 | 38.5 | child_shorter_than_generated_median | 3.735e+04 | 0.5429 | 1 | 0.4982 | 0.002578 | 0 | 1 |
| 036-041 | 38.5 | child_words_minus_generated_mean | 3.735e+04 | -1.205 | -1.43 | 2.738 | 0.01417 | -4.21 | 2.04 |
| 036-041 | 38.5 | child_words_percentile_in_generated_distribution | 3.735e+04 | 0.3883 | 0.335 | 0.2994 | 0.001549 | 0.03 | 0.85 |
| 036-041 | 38.5 | child_words_ratio_to_generated_mean | 3.735e+04 | 0.832 | 0.6479 | 0.7346 | 0.003801 | 0.2119 | 1.618 |
| 036-041 | 38.5 | child_words_z_vs_generated | 3.73e+04 | -0.3654 | -0.5576 | 1.214 | 0.006286 | -1.478 | 0.9111 |
| 036-041 | 38.5 | generated_expected_words | 3.735e+04 | 4.466 | 4.42 | 1.611 | 0.008338 | 2.44 | 6.41 |
| 036-041 | 38.5 | nb_words | 3.735e+04 | 3.261 | 3 | 2.334 | 0.01208 | 1 | 6 |
| 036-041 | 38.5 | response_entropy_bits | 3.735e+04 | 5.22 | 5.487 | 1.253 | 0.006484 | 3.426 | 6.606 |
| 042-047 | 44.5 | child_longer_than_generated_p90 | 1.606e+04 | 0.08223 | 0 | 0.2747 | 0.002167 | 0 | 0 |
| 042-047 | 44.5 | child_shorter_than_generated_median | 1.606e+04 | 0.499 | 0 | 0.5 | 0.003945 | 0 | 1 |
| 042-047 | 44.5 | child_words_minus_generated_mean | 1.606e+04 | -0.8286 | -1.13 | 2.968 | 0.02342 | -4.07 | 2.74 |
| 042-047 | 44.5 | child_words_percentile_in_generated_distribution | 1.606e+04 | 0.4264 | 0.385 | 0.3089 | 0.002437 | 0.04 | 0.89 |
| 042-047 | 44.5 | child_words_ratio_to_generated_mean | 1.606e+04 | 0.9256 | 0.7366 | 0.8213 | 0.00648 | 0.2222 | 1.774 |
| 042-047 | 44.5 | child_words_z_vs_generated | 1.605e+04 | -0.2022 | -0.4379 | 1.336 | 0.01054 | -1.408 | 1.205 |
| 042-047 | 44.5 | generated_expected_words | 1.606e+04 | 4.611 | 4.57 | 1.583 | 0.01249 | 2.61 | 6.56 |
| 042-047 | 44.5 | nb_words | 1.606e+04 | 3.783 | 3 | 2.652 | 0.02093 | 1 | 7 |
| 042-047 | 44.5 | response_entropy_bits | 1.606e+04 | 5.278 | 5.51 | 1.225 | 0.009668 | 3.566 | 6.633 |
| 048-053 | 50.5 | child_longer_than_generated_p90 | 1.263e+04 | 0.08312 | 0 | 0.2761 | 0.002456 | 0 | 0 |
| 048-053 | 50.5 | child_shorter_than_generated_median | 1.263e+04 | 0.4849 | 0 | 0.4998 | 0.004447 | 0 | 1 |
| 048-053 | 50.5 | child_words_minus_generated_mean | 1.263e+04 | -0.7613 | -1.02 | 2.892 | 0.02573 | -4.079 | 2.83 |
| 048-053 | 50.5 | child_words_percentile_in_generated_distribution | 1.263e+04 | 0.4411 | 0.41 | 0.3144 | 0.002797 | 0.035 | 0.895 |
| 048-053 | 50.5 | child_words_ratio_to_generated_mean | 1.263e+04 | 0.9474 | 0.7692 | 0.772 | 0.006868 | 0.2227 | 1.812 |
| 048-053 | 50.5 | child_words_z_vs_generated | 1.262e+04 | -0.1704 | -0.3916 | 1.341 | 0.01194 | -1.392 | 1.241 |
| 048-053 | 50.5 | generated_expected_words | 1.263e+04 | 4.717 | 4.72 | 1.534 | 0.01365 | 2.74 | 6.57 |
| 048-053 | 50.5 | nb_words | 1.263e+04 | 3.956 | 4 | 2.531 | 0.02252 | 1 | 7 |
| 048-053 | 50.5 | response_entropy_bits | 1.263e+04 | 5.383 | 5.666 | 1.242 | 0.01105 | 3.624 | 6.731 |
| 054-059 | 56.5 | child_longer_than_generated_p90 | 9707 | 0.09385 | 0 | 0.2916 | 0.00296 | 0 | 0 |
| 054-059 | 56.5 | child_shorter_than_generated_median | 9707 | 0.4933 | 0 | 0.5 | 0.005075 | 0 | 1 |
| 054-059 | 56.5 | child_words_minus_generated_mean | 9707 | -0.6713 | -0.99 | 3.015 | 0.0306 | -4.124 | 3.1 |
| 054-059 | 56.5 | child_words_percentile_in_generated_distribution | 9707 | 0.4448 | 0.41 | 0.3145 | 0.003192 | 0.04 | 0.905 |
| 054-059 | 56.5 | child_words_ratio_to_generated_mean | 9707 | 0.9532 | 0.7788 | 0.754 | 0.007653 | 0.2237 | 1.818 |
| 054-059 | 56.5 | child_words_z_vs_generated | 9707 | -0.154 | -0.3791 | 1.312 | 0.01332 | -1.399 | 1.312 |
| 054-059 | 56.5 | generated_expected_words | 9707 | 4.813 | 4.8 | 1.47 | 0.01492 | 2.94 | 6.56 |
| 054-059 | 56.5 | nb_words | 9707 | 4.142 | 4 | 2.699 | 0.02739 | 1 | 7 |
| 054-059 | 56.5 | response_entropy_bits | 9707 | 5.49 | 5.762 | 1.167 | 0.01185 | 3.824 | 6.729 |
| 060-065 | 62.5 | child_longer_than_generated_p90 | 2445 | 0.07935 | 0 | 0.2703 | 0.005467 | 0 | 0 |
| 060-065 | 62.5 | child_shorter_than_generated_median | 2445 | 0.5059 | 1 | 0.5001 | 0.01011 | 0 | 1 |
| 060-065 | 62.5 | child_words_minus_generated_mean | 2445 | -0.7885 | -1.09 | 3.02 | 0.06108 | -4.242 | 3.056 |
| 060-065 | 62.5 | child_words_percentile_in_generated_distribution | 2445 | 0.435 | 0.42 | 0.3093 | 0.006255 | 0.035 | 0.888 |
| 060-065 | 62.5 | child_words_ratio_to_generated_mean | 2445 | 0.9462 | 0.7653 | 0.7801 | 0.01578 | 0.2146 | 1.834 |
| 060-065 | 62.5 | child_words_z_vs_generated | 2445 | -0.1342 | -0.3679 | 1.832 | 0.03704 | -1.401 | 1.187 |
| 060-065 | 62.5 | generated_expected_words | 2445 | 4.813 | 4.75 | 1.492 | 0.03018 | 2.9 | 6.7 |
| 060-065 | 62.5 | nb_words | 2445 | 4.025 | 4 | 2.647 | 0.05353 | 1 | 7 |
| 060-065 | 62.5 | response_entropy_bits | 2445 | 5.476 | 5.627 | 1.189 | 0.02404 | 3.873 | 6.844 |

## Fit Summary

| model_label | model_id | estimator_id | level | outcome | outcome_type | status | n | children | descriptive_fitted_r2 | exclude_fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R2-M1 age + child identity | minus_gen_mean_r2m1_age_child | row_ols_child_fe_cluster | utterance | child_words_minus_generated_mean | continuous | fit | 4.443e+05 | 21 | 0.05729 | 0 |
| R2-M1 age + child identity | minus_gen_mean_r2m1_age_child | session_gee_exchangeable | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.2434 | 0 |
| R2-M1 age + child identity | minus_gen_mean_r2m1_age_child | session_mundlak_gee | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.4458 | 0 |
| R2-M1 age + child identity | minus_gen_mean_r2m1_age_child | session_mixedlm_random_age | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.6578 | 0 |
| R2-M2 add response entropy | minus_gen_mean_r2m2_response_entropy | row_ols_child_fe_cluster | utterance | child_words_minus_generated_mean | continuous | fit | 4.443e+05 | 21 | 0.171 | 0 |
| R2-M2 add response entropy | minus_gen_mean_r2m2_response_entropy | session_gee_exchangeable | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.2034 | 0 |
| R2-M2 add response entropy | minus_gen_mean_r2m2_response_entropy | session_mundlak_gee | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.4316 | 0 |
| R2-M2 add response entropy | minus_gen_mean_r2m2_response_entropy | session_mixedlm_random_age | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.6772 | 0 |
| R2-M3 context demand controls | minus_gen_mean_r2m3_context_demand | row_ols_child_fe_cluster | utterance | child_words_minus_generated_mean | continuous | fit | 4.414e+05 | 21 | 0.4167 | 0 |
| R2-M3 context demand controls | minus_gen_mean_r2m3_context_demand | session_gee_exchangeable | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.273 | 0 |
| R2-M3 context demand controls | minus_gen_mean_r2m3_context_demand | session_mundlak_gee | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.4551 | 0 |
| R2-M3 context demand controls | minus_gen_mean_r2m3_context_demand | session_mixedlm_random_age | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.723 | 0 |
| R2-M4 response entropy + context demand | minus_gen_mean_r2m4_full_controls | row_ols_child_fe_cluster | utterance | child_words_minus_generated_mean | continuous | fit | 4.414e+05 | 21 | 0.417 | 0 |
| R2-M4 response entropy + context demand | minus_gen_mean_r2m4_full_controls | session_gee_exchangeable | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.2735 | 0 |
| R2-M4 response entropy + context demand | minus_gen_mean_r2m4_full_controls | session_mundlak_gee | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.4551 | 0 |
| R2-M4 response entropy + context demand | minus_gen_mean_r2m4_full_controls | session_mixedlm_random_age | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.7236 | 0 |
| R2-M5 age x response entropy | minus_gen_mean_r2m5_age_by_entropy | row_ols_child_fe_cluster | utterance | child_words_minus_generated_mean | continuous | fit | 4.414e+05 | 21 | 0.417 | 0 |
| R2-M5 age x response entropy | minus_gen_mean_r2m5_age_by_entropy | session_gee_exchangeable | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.2944 | 0 |
| R2-M5 age x response entropy | minus_gen_mean_r2m5_age_by_entropy | session_mundlak_gee | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.4489 | 0 |
| R2-M5 age x response entropy | minus_gen_mean_r2m5_age_by_entropy | session_mixedlm_random_age | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.7321 | 0 |
| R2-M5 age x response entropy, no fallback contexts | minus_gen_mean_r2m5_age_by_entropy_no_fallback | row_ols_child_fe_cluster | utterance | child_words_minus_generated_mean | continuous | fit | 4.412e+05 | 21 | 0.4161 | 1 |
| R2-M5 age x response entropy, no fallback contexts | minus_gen_mean_r2m5_age_by_entropy_no_fallback | session_gee_exchangeable | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.2947 | 1 |
| R2-M5 age x response entropy, no fallback contexts | minus_gen_mean_r2m5_age_by_entropy_no_fallback | session_mundlak_gee | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.4493 | 1 |
| R2-M5 age x response entropy, no fallback contexts | minus_gen_mean_r2m5_age_by_entropy_no_fallback | session_mixedlm_random_age | child_session | child_words_minus_generated_mean | continuous | fit | 976 | 21 | 0.7321 | 1 |
| R2-M1 age + child identity | z_vs_generated_r2m1_age_child | row_ols_child_fe_cluster | utterance | child_words_z_vs_generated | continuous | fit | 4.437e+05 | 21 | 0.05849 | 0 |
| R2-M1 age + child identity | z_vs_generated_r2m1_age_child | session_gee_exchangeable | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.2454 | 0 |
| R2-M1 age + child identity | z_vs_generated_r2m1_age_child | session_mundlak_gee | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.4785 | 0 |
| R2-M1 age + child identity | z_vs_generated_r2m1_age_child | session_mixedlm_random_age | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.6717 | 0 |
| R2-M2 add response entropy | z_vs_generated_r2m2_response_entropy | row_ols_child_fe_cluster | utterance | child_words_z_vs_generated | continuous | fit | 4.437e+05 | 21 | 0.1336 | 0 |
| R2-M2 add response entropy | z_vs_generated_r2m2_response_entropy | session_gee_exchangeable | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.2165 | 0 |
| R2-M2 add response entropy | z_vs_generated_r2m2_response_entropy | session_mundlak_gee | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.4643 | 0 |
| R2-M2 add response entropy | z_vs_generated_r2m2_response_entropy | session_mixedlm_random_age | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.6777 | 0 |
| R2-M3 context demand controls | z_vs_generated_r2m3_context_demand | row_ols_child_fe_cluster | utterance | child_words_z_vs_generated | continuous | fit | 4.408e+05 | 21 | 0.2476 | 0 |
| R2-M3 context demand controls | z_vs_generated_r2m3_context_demand | session_gee_exchangeable | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.3316 | 0 |
| R2-M3 context demand controls | z_vs_generated_r2m3_context_demand | session_mundlak_gee | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.5084 | 0 |
| R2-M3 context demand controls | z_vs_generated_r2m3_context_demand | session_mixedlm_random_age | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.6979 | 0 |
| R2-M4 response entropy + context demand | z_vs_generated_r2m4_full_controls | row_ols_child_fe_cluster | utterance | child_words_z_vs_generated | continuous | fit | 4.408e+05 | 21 | 0.2485 | 0 |
| R2-M4 response entropy + context demand | z_vs_generated_r2m4_full_controls | session_gee_exchangeable | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.3315 | 0 |
| R2-M4 response entropy + context demand | z_vs_generated_r2m4_full_controls | session_mundlak_gee | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.5084 | 0 |
| R2-M4 response entropy + context demand | z_vs_generated_r2m4_full_controls | session_mixedlm_random_age | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.6991 | 0 |
| R2-M5 age x response entropy | z_vs_generated_r2m5_age_by_entropy | row_ols_child_fe_cluster | utterance | child_words_z_vs_generated | continuous | fit | 4.408e+05 | 21 | 0.25 | 0 |
| R2-M5 age x response entropy | z_vs_generated_r2m5_age_by_entropy | session_gee_exchangeable | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.3828 | 0 |
| R2-M5 age x response entropy | z_vs_generated_r2m5_age_by_entropy | session_mundlak_gee | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.5119 | 0 |
| R2-M5 age x response entropy | z_vs_generated_r2m5_age_by_entropy | session_mixedlm_random_age | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.7201 | 0 |
| R2-M5 age x response entropy, no fallback contexts | z_vs_generated_r2m5_age_by_entropy_no_fallback | row_ols_child_fe_cluster | utterance | child_words_z_vs_generated | continuous | fit | 4.406e+05 | 21 | 0.2497 | 1 |
| R2-M5 age x response entropy, no fallback contexts | z_vs_generated_r2m5_age_by_entropy_no_fallback | session_gee_exchangeable | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.3832 | 1 |
| R2-M5 age x response entropy, no fallback contexts | z_vs_generated_r2m5_age_by_entropy_no_fallback | session_mundlak_gee | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.513 | 1 |
| R2-M5 age x response entropy, no fallback contexts | z_vs_generated_r2m5_age_by_entropy_no_fallback | session_mixedlm_random_age | child_session | child_words_z_vs_generated | continuous | fit | 976 | 21 | 0.7208 | 1 |
| R2-M1 age + child identity | percentile_in_gen_distribution_r2m1_age_child | row_ols_child_fe_cluster | utterance | child_words_percentile_in_generated_distribution | continuous | fit | 4.443e+05 | 21 | 0.06373 | 0 |
| R2-M1 age + child identity | percentile_in_gen_distribution_r2m1_age_child | session_gee_exchangeable | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.2568 | 0 |
| R2-M1 age + child identity | percentile_in_gen_distribution_r2m1_age_child | session_mundlak_gee | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.5406 | 0 |
| R2-M1 age + child identity | percentile_in_gen_distribution_r2m1_age_child | session_mixedlm_random_age | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.7347 | 0 |
| R2-M2 add response entropy | percentile_in_gen_distribution_r2m2_response_entropy | row_ols_child_fe_cluster | utterance | child_words_percentile_in_generated_distribution | continuous | fit | 4.443e+05 | 21 | 0.1884 | 0 |
| R2-M2 add response entropy | percentile_in_gen_distribution_r2m2_response_entropy | session_gee_exchangeable | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.2291 | 0 |
| R2-M2 add response entropy | percentile_in_gen_distribution_r2m2_response_entropy | session_mundlak_gee | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.5274 | 0 |
| R2-M2 add response entropy | percentile_in_gen_distribution_r2m2_response_entropy | session_mixedlm_random_age | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.7406 | 0 |
| R2-M3 context demand controls | percentile_in_gen_distribution_r2m3_context_demand | row_ols_child_fe_cluster | utterance | child_words_percentile_in_generated_distribution | continuous | fit | 4.414e+05 | 21 | 0.2979 | 0 |
| R2-M3 context demand controls | percentile_in_gen_distribution_r2m3_context_demand | session_gee_exchangeable | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.3443 | 0 |
| R2-M3 context demand controls | percentile_in_gen_distribution_r2m3_context_demand | session_mundlak_gee | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.5712 | 0 |
| R2-M3 context demand controls | percentile_in_gen_distribution_r2m3_context_demand | session_mixedlm_random_age | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.7636 | 0 |
| R2-M4 response entropy + context demand | percentile_in_gen_distribution_r2m4_full_controls | row_ols_child_fe_cluster | utterance | child_words_percentile_in_generated_distribution | continuous | fit | 4.414e+05 | 21 | 0.3061 | 0 |
| R2-M4 response entropy + context demand | percentile_in_gen_distribution_r2m4_full_controls | session_gee_exchangeable | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.3443 | 0 |
| R2-M4 response entropy + context demand | percentile_in_gen_distribution_r2m4_full_controls | session_mundlak_gee | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.5713 | 0 |
| R2-M4 response entropy + context demand | percentile_in_gen_distribution_r2m4_full_controls | session_mixedlm_random_age | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.7637 | 0 |
| R2-M5 age x response entropy | percentile_in_gen_distribution_r2m5_age_by_entropy | row_ols_child_fe_cluster | utterance | child_words_percentile_in_generated_distribution | continuous | fit | 4.414e+05 | 21 | 0.3061 | 0 |
| R2-M5 age x response entropy | percentile_in_gen_distribution_r2m5_age_by_entropy | session_gee_exchangeable | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.3777 | 0 |
| R2-M5 age x response entropy | percentile_in_gen_distribution_r2m5_age_by_entropy | session_mundlak_gee | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.5714 | 0 |
| R2-M5 age x response entropy | percentile_in_gen_distribution_r2m5_age_by_entropy | session_mixedlm_random_age | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.7689 | 0 |
| R2-M5 age x response entropy, no fallback contexts | percentile_in_gen_distribution_r2m5_age_by_entropy_no_fallback | row_ols_child_fe_cluster | utterance | child_words_percentile_in_generated_distribution | continuous | fit | 4.412e+05 | 21 | 0.3062 | 1 |
| R2-M5 age x response entropy, no fallback contexts | percentile_in_gen_distribution_r2m5_age_by_entropy_no_fallback | session_gee_exchangeable | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.378 | 1 |
| R2-M5 age x response entropy, no fallback contexts | percentile_in_gen_distribution_r2m5_age_by_entropy_no_fallback | session_mundlak_gee | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.5716 | 1 |
| R2-M5 age x response entropy, no fallback contexts | percentile_in_gen_distribution_r2m5_age_by_entropy_no_fallback | session_mixedlm_random_age | child_session | child_words_percentile_in_generated_distribution | continuous | fit | 976 | 21 | 0.769 | 1 |
| R2-M1 age + child identity | ratio_to_gen_mean_r2m1_age_child | row_ols_child_fe_cluster | utterance | child_words_ratio_to_generated_mean | continuous | fit | 4.443e+05 | 21 | 0.06475 | 0 |
| R2-M1 age + child identity | ratio_to_gen_mean_r2m1_age_child | session_gee_exchangeable | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.2361 | 0 |
| R2-M1 age + child identity | ratio_to_gen_mean_r2m1_age_child | session_mundlak_gee | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.4829 | 0 |
| R2-M1 age + child identity | ratio_to_gen_mean_r2m1_age_child | session_mixedlm_random_age | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.7129 | 0 |
| R2-M2 add response entropy | ratio_to_gen_mean_r2m2_response_entropy | row_ols_child_fe_cluster | utterance | child_words_ratio_to_generated_mean | continuous | fit | 4.443e+05 | 21 | 0.1632 | 0 |
| R2-M2 add response entropy | ratio_to_gen_mean_r2m2_response_entropy | session_gee_exchangeable | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.2025 | 0 |
| R2-M2 add response entropy | ratio_to_gen_mean_r2m2_response_entropy | session_mundlak_gee | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.4658 | 0 |
| R2-M2 add response entropy | ratio_to_gen_mean_r2m2_response_entropy | session_mixedlm_random_age | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.7192 | 0 |
| R2-M3 context demand controls | ratio_to_gen_mean_r2m3_context_demand | row_ols_child_fe_cluster | utterance | child_words_ratio_to_generated_mean | continuous | fit | 4.414e+05 | 21 | 0.2178 | 0 |
| R2-M3 context demand controls | ratio_to_gen_mean_r2m3_context_demand | session_gee_exchangeable | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.3084 | 0 |
| R2-M3 context demand controls | ratio_to_gen_mean_r2m3_context_demand | session_mundlak_gee | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.5049 | 0 |
| R2-M3 context demand controls | ratio_to_gen_mean_r2m3_context_demand | session_mixedlm_random_age | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.7346 | 0 |
| R2-M4 response entropy + context demand | ratio_to_gen_mean_r2m4_full_controls | row_ols_child_fe_cluster | utterance | child_words_ratio_to_generated_mean | continuous | fit | 4.414e+05 | 21 | 0.229 | 0 |
| R2-M4 response entropy + context demand | ratio_to_gen_mean_r2m4_full_controls | session_gee_exchangeable | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.3073 | 0 |
| R2-M4 response entropy + context demand | ratio_to_gen_mean_r2m4_full_controls | session_mundlak_gee | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.5053 | 0 |
| R2-M4 response entropy + context demand | ratio_to_gen_mean_r2m4_full_controls | session_mixedlm_random_age | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.7349 | 0 |
| R2-M5 age x response entropy | ratio_to_gen_mean_r2m5_age_by_entropy | row_ols_child_fe_cluster | utterance | child_words_ratio_to_generated_mean | continuous | fit | 4.414e+05 | 21 | 0.2319 | 0 |
| R2-M5 age x response entropy | ratio_to_gen_mean_r2m5_age_by_entropy | session_gee_exchangeable | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.3484 | 0 |
| R2-M5 age x response entropy | ratio_to_gen_mean_r2m5_age_by_entropy | session_mundlak_gee | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.5031 | 0 |
| R2-M5 age x response entropy | ratio_to_gen_mean_r2m5_age_by_entropy | session_mixedlm_random_age | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.7489 | 0 |
| R2-M5 age x response entropy, no fallback contexts | ratio_to_gen_mean_r2m5_age_by_entropy_no_fallback | row_ols_child_fe_cluster | utterance | child_words_ratio_to_generated_mean | continuous | fit | 4.412e+05 | 21 | 0.2319 | 1 |
| R2-M5 age x response entropy, no fallback contexts | ratio_to_gen_mean_r2m5_age_by_entropy_no_fallback | session_gee_exchangeable | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.3487 | 1 |
| R2-M5 age x response entropy, no fallback contexts | ratio_to_gen_mean_r2m5_age_by_entropy_no_fallback | session_mundlak_gee | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.5034 | 1 |
| R2-M5 age x response entropy, no fallback contexts | ratio_to_gen_mean_r2m5_age_by_entropy_no_fallback | session_mixedlm_random_age | child_session | child_words_ratio_to_generated_mean | continuous | fit | 976 | 21 | 0.7489 | 1 |
| R2-M1 age + child identity | child_shorter_than_gen_median_r2m1_age_child | row_logit_child_fe_cluster | utterance | child_shorter_than_generated_median | binary | fit | 4.443e+05 | 21 | 0.03162 | 0 |
| R2-M1 age + child identity | child_shorter_than_gen_median_r2m1_age_child | session_gee_exchangeable | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.2101 | 0 |
| R2-M1 age + child identity | child_shorter_than_gen_median_r2m1_age_child | session_mundlak_gee | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.5172 | 0 |
| R2-M1 age + child identity | child_shorter_than_gen_median_r2m1_age_child | session_mixedlm_random_age | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.6931 | 0 |
| R2-M2 add response entropy | child_shorter_than_gen_median_r2m2_response_entropy | row_logit_child_fe_cluster | utterance | child_shorter_than_generated_median | binary | fit | 4.443e+05 | 21 | 0.2019 | 0 |
| R2-M2 add response entropy | child_shorter_than_gen_median_r2m2_response_entropy | session_gee_exchangeable | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.1769 | 0 |
| R2-M2 add response entropy | child_shorter_than_gen_median_r2m2_response_entropy | session_mundlak_gee | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.5123 | 0 |
| R2-M2 add response entropy | child_shorter_than_gen_median_r2m2_response_entropy | session_mixedlm_random_age | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.7125 | 0 |
| R2-M3 context demand controls | child_shorter_than_gen_median_r2m3_context_demand | row_logit_child_fe_cluster | utterance | child_shorter_than_generated_median | binary | fit | 4.414e+05 | 21 | 0.3385 | 0 |
| R2-M3 context demand controls | child_shorter_than_gen_median_r2m3_context_demand | session_gee_exchangeable | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.3366 | 0 |
| R2-M3 context demand controls | child_shorter_than_gen_median_r2m3_context_demand | session_mundlak_gee | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.5785 | 0 |
| R2-M3 context demand controls | child_shorter_than_gen_median_r2m3_context_demand | session_mixedlm_random_age | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.75 | 0 |
| R2-M4 response entropy + context demand | child_shorter_than_gen_median_r2m4_full_controls | row_logit_child_fe_cluster | utterance | child_shorter_than_generated_median | binary | fit | 4.414e+05 | 21 | 0.3419 | 0 |
| R2-M4 response entropy + context demand | child_shorter_than_gen_median_r2m4_full_controls | session_gee_exchangeable | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.3349 | 0 |
| R2-M4 response entropy + context demand | child_shorter_than_gen_median_r2m4_full_controls | session_mundlak_gee | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.5784 | 0 |
| R2-M4 response entropy + context demand | child_shorter_than_gen_median_r2m4_full_controls | session_mixedlm_random_age | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.7496 | 0 |
| R2-M5 age x response entropy | child_shorter_than_gen_median_r2m5_age_by_entropy | row_logit_child_fe_cluster | utterance | child_shorter_than_generated_median | binary | fit | 4.414e+05 | 21 | 0.3425 | 0 |
| R2-M5 age x response entropy | child_shorter_than_gen_median_r2m5_age_by_entropy | session_gee_exchangeable | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.3687 | 0 |
| R2-M5 age x response entropy | child_shorter_than_gen_median_r2m5_age_by_entropy | session_mundlak_gee | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.5806 | 0 |
| R2-M5 age x response entropy | child_shorter_than_gen_median_r2m5_age_by_entropy | session_mixedlm_random_age | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.7573 | 0 |
| R2-M5 age x response entropy, no fallback contexts | child_shorter_than_gen_median_r2m5_age_by_entropy_no_fallback | row_logit_child_fe_cluster | utterance | child_shorter_than_generated_median | binary | fit | 4.412e+05 | 21 | 0.3425 | 1 |
| R2-M5 age x response entropy, no fallback contexts | child_shorter_than_gen_median_r2m5_age_by_entropy_no_fallback | session_gee_exchangeable | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.3689 | 1 |
| R2-M5 age x response entropy, no fallback contexts | child_shorter_than_gen_median_r2m5_age_by_entropy_no_fallback | session_mundlak_gee | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.5808 | 1 |
| R2-M5 age x response entropy, no fallback contexts | child_shorter_than_gen_median_r2m5_age_by_entropy_no_fallback | session_mixedlm_random_age | child_session | child_shorter_than_generated_median | binary | fit | 976 | 21 | 0.7573 | 1 |

## Final-Model Key Coefficients

| outcome | model_label | estimator_id | term | estimate | std_error | p_value | conf_low | conf_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | row_logit_child_fe_cluster | age_months_c | 0.1002 | 0.01001 | 1.341e-23 | 0.08061 | 0.1198 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | row_logit_child_fe_cluster | age_months_c:response_entropy_bits_c | 0.006882 | 0.002695 | 0.01066 | 0.0016 | 0.01216 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | row_logit_child_fe_cluster | context_entropy_bits_c | 0.03518 | 0.01228 | 0.004178 | 0.01111 | 0.05926 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | row_logit_child_fe_cluster | generated_expected_words_c | -0.7007 | 0.07409 | 3.131e-21 | -0.846 | -0.5555 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | row_logit_child_fe_cluster | response_entropy_bits_c | -0.3162 | 0.03338 | 2.697e-21 | -0.3816 | -0.2508 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | row_logit_child_fe_cluster | route2_context_word_count_c | -0.0002222 | 0.002613 | 0.9322 | -0.005344 | 0.004899 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_gee_exchangeable | age_months_c | 0.00383 | 0.0004281 | 3.721e-19 | 0.002991 | 0.004669 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_gee_exchangeable | age_months_c:response_entropy_bits_c | -0.001612 | 0.0003189 | 4.269e-07 | -0.002237 | -0.0009874 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_gee_exchangeable | context_entropy_bits_c | 1.162e-05 | 0.00612 | 0.9985 | -0.01198 | 0.01201 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_gee_exchangeable | generated_expected_words_c | -0.01659 | 0.005466 | 0.00241 | -0.0273 | -0.005873 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_gee_exchangeable | response_entropy_bits_c | -0.02486 | 0.004193 | 3.033e-09 | -0.03308 | -0.01664 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_gee_exchangeable | route2_context_word_count_c | 0.002845 | 0.000815 | 0.0004816 | 0.001248 | 0.004442 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mixedlm_random_age | age_months_c | 0.00376 | 0.0003478 | 3.032e-27 | 0.003079 | 0.004442 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mixedlm_random_age | age_months_c:response_entropy_bits_c | -0.001784 | 0.0002886 | 6.309e-10 | -0.00235 | -0.001219 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mixedlm_random_age | context_entropy_bits_c | 0.003934 | 0.005274 | 0.4558 | -0.006403 | 0.01427 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mixedlm_random_age | generated_expected_words_c | -0.01556 | 0.004636 | 0.0007883 | -0.02465 | -0.006475 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mixedlm_random_age | response_entropy_bits_c | -0.02101 | 0.005807 | 0.0002958 | -0.0324 | -0.009634 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mixedlm_random_age | route2_context_word_count_c | 0.002624 | 0.0006004 | 1.238e-05 | 0.001448 | 0.003801 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | age_within_child_c | 0.003821 | 0.0004134 | 2.366e-20 | 0.003011 | 0.004632 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | age_within_child_c:response_entropy_bits_c | -0.001698 | 0.0005708 | 0.002926 | -0.002817 | -0.0005796 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | child_mean_age_c | 0.001118 | 0.0008311 | 0.1785 | -0.0005108 | 0.002747 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | context_entropy_bits_c | -0.0009578 | 0.005467 | 0.8609 | -0.01167 | 0.009757 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | generated_expected_words_c | -0.01666 | 0.005689 | 0.003411 | -0.02781 | -0.005507 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | response_entropy_bits_c | -0.02732 | 0.007542 | 0.0002915 | -0.0421 | -0.01254 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy | session_mundlak_gee | route2_context_word_count_c | 0.002948 | 0.0008594 | 0.0006029 | 0.001264 | 0.004632 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | age_months_c | 0.1002 | 0.01002 | 1.402e-23 | 0.08061 | 0.1199 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | age_months_c:response_entropy_bits_c | 0.006872 | 0.002694 | 0.01074 | 0.001592 | 0.01215 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | context_entropy_bits_c | 0.03563 | 0.01248 | 0.004314 | 0.01116 | 0.0601 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | generated_expected_words_c | -0.7012 | 0.07406 | 2.849e-21 | -0.8464 | -0.5561 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | response_entropy_bits_c | -0.3158 | 0.03327 | 2.317e-21 | -0.381 | -0.2505 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | route2_context_word_count_c | -0.0002789 | 0.002634 | 0.9157 | -0.005441 | 0.004883 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | age_months_c | 0.003833 | 0.000428 | 3.366e-19 | 0.002994 | 0.004672 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | age_months_c:response_entropy_bits_c | -0.001612 | 0.0003195 | 4.534e-07 | -0.002238 | -0.0009858 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | context_entropy_bits_c | 9.794e-06 | 0.006097 | 0.9987 | -0.01194 | 0.01196 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | generated_expected_words_c | -0.01676 | 0.005494 | 0.002281 | -0.02753 | -0.005994 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | response_entropy_bits_c | -0.02475 | 0.004173 | 3.007e-09 | -0.03293 | -0.01657 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | route2_context_word_count_c | 0.002853 | 0.0008199 | 0.0005015 | 0.001246 | 0.00446 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | age_months_c | 0.003763 | 0.0003484 | 3.335e-27 | 0.003081 | 0.004446 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | age_months_c:response_entropy_bits_c | -0.001787 | 0.0002889 | 6.098e-10 | -0.002354 | -0.001221 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | context_entropy_bits_c | 0.003887 | 0.005278 | 0.4614 | -0.006456 | 0.01423 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | generated_expected_words_c | -0.01582 | 0.00466 | 0.0006862 | -0.02495 | -0.006687 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | response_entropy_bits_c | -0.02079 | 0.00582 | 0.0003542 | -0.0322 | -0.009383 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | route2_context_word_count_c | 0.002635 | 0.0006013 | 1.175e-05 | 0.001457 | 0.003814 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | age_within_child_c | 0.003825 | 0.0004131 | 2.067e-20 | 0.003015 | 0.004634 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | age_within_child_c:response_entropy_bits_c | -0.0017 | 0.0005733 | 0.003018 | -0.002824 | -0.0005767 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | child_mean_age_c | 0.001118 | 0.0008332 | 0.1797 | -0.0005153 | 0.002751 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | context_entropy_bits_c | -0.000954 | 0.005452 | 0.8611 | -0.01164 | 0.009732 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | generated_expected_words_c | -0.01685 | 0.005713 | 0.00319 | -0.02804 | -0.005649 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | response_entropy_bits_c | -0.0272 | 0.007473 | 0.0002729 | -0.04185 | -0.01255 |
| child_longer_than_generated_p90 | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | route2_context_word_count_c | 0.002956 | 0.0008635 | 0.0006183 | 0.001264 | 0.004649 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | row_logit_child_fe_cluster | age_months_c | -0.08983 | 0.008666 | 3.527e-25 | -0.1068 | -0.07285 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | row_logit_child_fe_cluster | age_months_c:response_entropy_bits_c | -0.01103 | 0.001913 | 8.21e-09 | -0.01478 | -0.007279 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | row_logit_child_fe_cluster | context_entropy_bits_c | 0.01433 | 0.006914 | 0.0382 | 0.0007796 | 0.02788 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | row_logit_child_fe_cluster | generated_expected_words_c | 0.9635 | 0.05281 | 2.286e-74 | 0.8599 | 1.067 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | row_logit_child_fe_cluster | response_entropy_bits_c | 0.2276 | 0.01385 | 1.057e-60 | 0.2005 | 0.2548 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | row_logit_child_fe_cluster | route2_context_word_count_c | -0.03169 | 0.003794 | 6.638e-17 | -0.03913 | -0.02425 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_gee_exchangeable | age_months_c | -0.01417 | 0.001063 | 1.517e-40 | -0.01625 | -0.01208 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_gee_exchangeable | age_months_c:response_entropy_bits_c | 0.004251 | 0.0007948 | 8.882e-08 | 0.002693 | 0.005809 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_gee_exchangeable | context_entropy_bits_c | 0.01879 | 0.01166 | 0.107 | -0.004061 | 0.04165 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_gee_exchangeable | generated_expected_words_c | 0.1256 | 0.02034 | 6.688e-10 | 0.08571 | 0.1654 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_gee_exchangeable | response_entropy_bits_c | 0.02627 | 0.02754 | 0.3402 | -0.02771 | 0.08024 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_gee_exchangeable | route2_context_word_count_c | -0.01038 | 0.002309 | 6.971e-06 | -0.0149 | -0.005851 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mixedlm_random_age | age_months_c | -0.01693 | 0.001003 | 6.986e-64 | -0.0189 | -0.01496 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mixedlm_random_age | age_months_c:response_entropy_bits_c | 0.003402 | 0.0006609 | 2.636e-07 | 0.002107 | 0.004698 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mixedlm_random_age | context_entropy_bits_c | 0.01697 | 0.01227 | 0.1667 | -0.007079 | 0.04102 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mixedlm_random_age | generated_expected_words_c | 0.1189 | 0.01078 | 2.859e-28 | 0.09777 | 0.14 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mixedlm_random_age | response_entropy_bits_c | 0.02584 | 0.01348 | 0.05531 | -0.0005868 | 0.05226 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mixedlm_random_age | route2_context_word_count_c | -0.01022 | 0.001395 | 2.384e-13 | -0.01295 | -0.007485 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | age_within_child_c | -0.01408 | 0.001031 | 1.994e-42 | -0.0161 | -0.01206 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | age_within_child_c:response_entropy_bits_c | 0.004989 | 0.001359 | 0.0002408 | 0.002326 | 0.007652 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | child_mean_age_c | -0.004866 | 0.002355 | 0.03876 | -0.009482 | -0.0002514 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | context_entropy_bits_c | 0.02369 | 0.01055 | 0.02467 | 0.003023 | 0.04437 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | generated_expected_words_c | 0.1248 | 0.02102 | 2.893e-09 | 0.08359 | 0.166 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | response_entropy_bits_c | 0.03285 | 0.02148 | 0.1262 | -0.009249 | 0.07494 |
| child_shorter_than_generated_median | R2-M5 age x response entropy | session_mundlak_gee | route2_context_word_count_c | -0.0109 | 0.002333 | 2.983e-06 | -0.01547 | -0.006327 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | age_months_c | -0.08985 | 0.008666 | 3.468e-25 | -0.1068 | -0.07286 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | age_months_c:response_entropy_bits_c | -0.01103 | 0.001916 | 8.648e-09 | -0.01478 | -0.007272 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | context_entropy_bits_c | 0.01435 | 0.006929 | 0.03831 | 0.0007728 | 0.02793 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | generated_expected_words_c | 0.9637 | 0.05278 | 1.775e-74 | 0.8602 | 1.067 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | response_entropy_bits_c | 0.2275 | 0.01385 | 1.199e-60 | 0.2004 | 0.2547 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | row_logit_child_fe_cluster | route2_context_word_count_c | -0.03169 | 0.003806 | 8.431e-17 | -0.03915 | -0.02423 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | age_months_c | -0.01417 | 0.001061 | 1.098e-40 | -0.01625 | -0.01209 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | age_months_c:response_entropy_bits_c | 0.004268 | 0.0008092 | 1.335e-07 | 0.002682 | 0.005854 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | context_entropy_bits_c | 0.01866 | 0.01174 | 0.1118 | -0.004343 | 0.04167 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | generated_expected_words_c | 0.1255 | 0.02042 | 7.963e-10 | 0.08547 | 0.1655 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | response_entropy_bits_c | 0.02655 | 0.02779 | 0.3394 | -0.02792 | 0.08102 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_gee_exchangeable | route2_context_word_count_c | -0.01039 | 0.002314 | 7.043e-06 | -0.01493 | -0.005859 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | age_months_c | -0.01693 | 0.001003 | 5.996e-64 | -0.0189 | -0.01497 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | age_months_c:response_entropy_bits_c | 0.003414 | 0.0006613 | 2.434e-07 | 0.002118 | 0.00471 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | context_entropy_bits_c | 0.01688 | 0.01228 | 0.1692 | -0.007183 | 0.04094 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | generated_expected_words_c | 0.1186 | 0.01084 | 7.166e-28 | 0.09735 | 0.1398 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | response_entropy_bits_c | 0.0263 | 0.01351 | 0.05151 | -0.0001718 | 0.05278 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mixedlm_random_age | route2_context_word_count_c | -0.01024 | 0.001397 | 2.28e-13 | -0.01298 | -0.007502 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | age_within_child_c | -0.01408 | 0.00103 | 1.422e-42 | -0.0161 | -0.01206 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | age_within_child_c:response_entropy_bits_c | 0.00503 | 0.001383 | 0.0002753 | 0.00232 | 0.00774 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | child_mean_age_c | -0.004865 | 0.002357 | 0.03902 | -0.009485 | -0.0002453 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | context_entropy_bits_c | 0.02359 | 0.01062 | 0.02628 | 0.002782 | 0.0444 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | generated_expected_words_c | 0.1247 | 0.02109 | 3.329e-09 | 0.0834 | 0.1661 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | response_entropy_bits_c | 0.03317 | 0.02151 | 0.1231 | -0.008994 | 0.07534 |
| child_shorter_than_generated_median | R2-M5 age x response entropy, no fallback contexts | session_mundlak_gee | route2_context_word_count_c | -0.01092 | 0.002336 | 2.947e-06 | -0.01549 | -0.00634 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | row_ols_child_fe_cluster | age_months_c | 0.0928 | 0.006735 | 3.39e-43 | 0.0796 | 0.106 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | row_ols_child_fe_cluster | age_months_c:response_entropy_bits_c | 0.0001824 | 0.000774 | 0.8137 | -0.001334 | 0.001699 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | row_ols_child_fe_cluster | context_entropy_bits_c | 0.008337 | 0.004655 | 0.07332 | -0.0007873 | 0.01746 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | row_ols_child_fe_cluster | generated_expected_words_c | -0.9525 | 0.004439 | 0 | -0.9612 | -0.9438 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | row_ols_child_fe_cluster | response_entropy_bits_c | 0.03524 | 0.005729 | 7.681e-10 | 0.02401 | 0.04647 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | row_ols_child_fe_cluster | route2_context_word_count_c | -0.001596 | 0.002014 | 0.4279 | -0.005543 | 0.00235 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_gee_exchangeable | age_months_c | 0.08949 | 0.006005 | 3.145e-50 | 0.07772 | 0.1013 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_gee_exchangeable | age_months_c:response_entropy_bits_c | -0.02478 | 0.006941 | 0.0003579 | -0.03838 | -0.01117 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_gee_exchangeable | context_entropy_bits_c | -0.2063 | 0.0602 | 0.0006114 | -0.3243 | -0.08829 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_gee_exchangeable | generated_expected_words_c | -0.9408 | 0.0717 | 2.47e-39 | -1.081 | -0.8003 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_gee_exchangeable | response_entropy_bits_c | -0.001641 | 0.1149 | 0.9886 | -0.2268 | 0.2235 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_gee_exchangeable | route2_context_word_count_c | 0.0344 | 0.01688 | 0.04152 | 0.001322 | 0.06747 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mixedlm_random_age | age_months_c | 0.1018 | 0.006238 | 6.998e-60 | 0.08958 | 0.114 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mixedlm_random_age | age_months_c:response_entropy_bits_c | -0.02442 | 0.004538 | 7.375e-08 | -0.03331 | -0.01553 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mixedlm_random_age | context_entropy_bits_c | -0.1668 | 0.08434 | 0.04801 | -0.3321 | -0.001457 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mixedlm_random_age | generated_expected_words_c | -0.9214 | 0.07419 | 2.076e-35 | -1.067 | -0.776 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mixedlm_random_age | response_entropy_bits_c | 0.04414 | 0.0927 | 0.634 | -0.1375 | 0.2258 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mixedlm_random_age | route2_context_word_count_c | 0.0322 | 0.009598 | 0.0007939 | 0.01339 | 0.05101 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mundlak_gee | age_within_child_c | 0.08903 | 0.005645 | 4.827e-56 | 0.07796 | 0.1001 |
| child_words_minus_generated_mean | R2-M5 age x response entropy | session_mundlak_gee | age_within_child_c:response_entropy_bits_c | -0.02258 | 0.01224 | 0.06518 | -0.04657 | 0.00142 |

## Interpretation Boundary

- The headline Route 2 outcome is context-relative effort, especially child word-count percentile or residual against the generated response-space length distribution.
- Raw child length still matters, but the relative outcomes are stronger because they condition on what the model generated for the same caregiver context.
- The response-space run currently covers Brown, Manchester, and Providence children, not the full 79-child cleaned bundle.
- Fallback contexts are rare and are handled by final-model no-fallback sensitivity checks.
