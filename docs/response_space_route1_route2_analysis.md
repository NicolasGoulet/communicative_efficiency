# Response-Space Route 1 / Route 2 Analysis

This is a focused first-pass analysis using the production response-space entropy run.
It does not score generated responses and does not claim that generated samples are same-meaning paraphrases.

## Inputs

- Child-row response-space table: `results/route2_response_space/route2_child_response_space_effort_table.csv.gz`
- Output directory: `results/route2_response_space_analysis`
- Figure directory: `figs/route2_response_space_analysis`

## Audit

Scope warning: this response-space analysis currently covers `21` children across `3` datasets. It is the production response-space subset available right now, not the full 79-child cleaned bundle.

| metric | value |
| --- | --- |
| input_rows | 4.443e+05 |
| unique_score_ids | 4.443e+05 |
| unique_utterance_ids | 4.443e+05 |
| unique_children | 21 |
| unique_datasets | 3 |
| unique_response_entropy_contexts | 2.687e+05 |
| fallback_rows | 218 |
| fallback_contexts | 176 |
| missing_context_entropy_rows | 2912 |
| context_predictor_rows | 2.687e+05 |
| utterance_predictor_rows | 4.443e+05 |
| fit_models | 48 |

## Figures

### Route 2 child length percentile by age

![Route 2 child length percentile by age](../figs/route2_response_space_analysis/route2_child_length_percentile_by_age.png)

### Route 2 expected generated length and actual child length by age

![Route 2 expected generated length and actual child length by age](../figs/route2_response_space_analysis/route2_actual_vs_generated_words_by_age.png)

### Route 2 response entropy by age

![Route 2 response entropy by age](../figs/route2_response_space_analysis/route2_response_entropy_by_age.png)

### Route 2 child length residual versus response entropy

![Route 2 child length residual versus response entropy](../figs/route2_response_space_analysis/route2_length_residual_vs_response_entropy.png)

### Response-space model coefficients

![Response-space model coefficients](../figs/route2_response_space_analysis/response_space_key_coefficients.png)

### Prediction lines: route2_nb_words_effort_choice

![Prediction lines: route2_nb_words_effort_choice](../figs/route2_response_space_analysis/route2_nb_words_effort_choice_prediction_lines.png)

### Prediction lines: route1_sum_bits_response_space_enriched

![Prediction lines: route1_sum_bits_response_space_enriched](../figs/route2_response_space_analysis/route1_sum_bits_response_space_enriched_prediction_lines.png)

### Prediction lines: route1_mean_bits_per_token_response_space_enriched

![Prediction lines: route1_mean_bits_per_token_response_space_enriched](../figs/route2_response_space_analysis/route1_mean_bits_per_token_response_space_enriched_prediction_lines.png)

## Model Summary

| family | model_id | estimator_id | level | outcome | status | n | children | descriptive_fitted_r2 | exclude_fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route2_effort_choice | route2_nb_words_effort_choice | row_ols_child_fe_cluster | utterance | nb_words | fit | 4.414e+05 | 21 | 0.1358 | 0 |
| route2_effort_choice | route2_nb_words_effort_choice | session_gee_exchangeable | child_session | nb_words | fit | 976 | 21 | 0.4337 | 0 |
| route2_effort_choice | route2_nb_words_effort_choice | session_mundlak_gee | child_session | nb_words | fit | 976 | 21 | 0.5752 | 0 |
| route2_effort_choice | route2_nb_words_effort_choice | session_mixedlm_random_age | child_session | nb_words | fit | 976 | 21 | 0.7845 | 0 |
| route2_effort_choice_no_fallback | route2_nb_words_effort_choice_no_fallback | row_ols_child_fe_cluster | utterance | nb_words | fit | 4.412e+05 | 21 | 0.1358 | 1 |
| route2_effort_choice_no_fallback | route2_nb_words_effort_choice_no_fallback | session_gee_exchangeable | child_session | nb_words | fit | 976 | 21 | 0.4339 | 1 |
| route2_effort_choice_no_fallback | route2_nb_words_effort_choice_no_fallback | session_mundlak_gee | child_session | nb_words | fit | 976 | 21 | 0.5756 | 1 |
| route2_effort_choice_no_fallback | route2_nb_words_effort_choice_no_fallback | session_mixedlm_random_age | child_session | nb_words | fit | 976 | 21 | 0.7845 | 1 |
| route2_effort_choice | route2_nb_morphemes_effort_choice | row_ols_child_fe_cluster | utterance | nb_morphemes | fit | 4.414e+05 | 21 | 0.1431 | 0 |
| route2_effort_choice | route2_nb_morphemes_effort_choice | session_gee_exchangeable | child_session | nb_morphemes | fit | 976 | 21 | 0.401 | 0 |
| route2_effort_choice | route2_nb_morphemes_effort_choice | session_mundlak_gee | child_session | nb_morphemes | fit | 976 | 21 | 0.5749 | 0 |
| route2_effort_choice | route2_nb_morphemes_effort_choice | session_mixedlm_random_age | child_session | nb_morphemes | fit | 976 | 21 | 0.7973 | 0 |
| route2_effort_choice_no_fallback | route2_nb_morphemes_effort_choice_no_fallback | row_ols_child_fe_cluster | utterance | nb_morphemes | fit | 4.412e+05 | 21 | 0.1432 | 1 |
| route2_effort_choice_no_fallback | route2_nb_morphemes_effort_choice_no_fallback | session_gee_exchangeable | child_session | nb_morphemes | fit | 976 | 21 | 0.4012 | 1 |
| route2_effort_choice_no_fallback | route2_nb_morphemes_effort_choice_no_fallback | session_mundlak_gee | child_session | nb_morphemes | fit | 976 | 21 | 0.5753 | 1 |
| route2_effort_choice_no_fallback | route2_nb_morphemes_effort_choice_no_fallback | session_mixedlm_random_age | child_session | nb_morphemes | fit | 976 | 21 | 0.7974 | 1 |
| route2_effort_choice | route2_nb_syllables_pkg_effort_choice | row_ols_child_fe_cluster | utterance | nb_syllables_pkg | fit | 4.414e+05 | 21 | 0.1168 | 0 |
| route2_effort_choice | route2_nb_syllables_pkg_effort_choice | session_gee_exchangeable | child_session | nb_syllables_pkg | fit | 976 | 21 | 0.3032 | 0 |
| route2_effort_choice | route2_nb_syllables_pkg_effort_choice | session_mundlak_gee | child_session | nb_syllables_pkg | fit | 976 | 21 | 0.4742 | 0 |
| route2_effort_choice | route2_nb_syllables_pkg_effort_choice | session_mixedlm_random_age | child_session | nb_syllables_pkg | fit | 976 | 21 | 0.7406 | 0 |
| route2_effort_choice_no_fallback | route2_nb_syllables_pkg_effort_choice_no_fallback | row_ols_child_fe_cluster | utterance | nb_syllables_pkg | fit | 4.412e+05 | 21 | 0.1168 | 1 |
| route2_effort_choice_no_fallback | route2_nb_syllables_pkg_effort_choice_no_fallback | session_gee_exchangeable | child_session | nb_syllables_pkg | fit | 976 | 21 | 0.3035 | 1 |
| route2_effort_choice_no_fallback | route2_nb_syllables_pkg_effort_choice_no_fallback | session_mundlak_gee | child_session | nb_syllables_pkg | fit | 976 | 21 | 0.4745 | 1 |
| route2_effort_choice_no_fallback | route2_nb_syllables_pkg_effort_choice_no_fallback | session_mixedlm_random_age | child_session | nb_syllables_pkg | fit | 976 | 21 | 0.7406 | 1 |
| route2_effort_choice | route2_nb_phonemes_effort_choice | row_ols_child_fe_cluster | utterance | nb_phonemes | fit | 4.414e+05 | 21 | 0.1227 | 0 |
| route2_effort_choice | route2_nb_phonemes_effort_choice | session_gee_exchangeable | child_session | nb_phonemes | fit | 976 | 21 | 0.2924 | 0 |
| route2_effort_choice | route2_nb_phonemes_effort_choice | session_mundlak_gee | child_session | nb_phonemes | fit | 976 | 21 | 0.5014 | 0 |
| route2_effort_choice | route2_nb_phonemes_effort_choice | session_mixedlm_random_age | child_session | nb_phonemes | fit | 976 | 21 | 0.7754 | 0 |
| route2_effort_choice_no_fallback | route2_nb_phonemes_effort_choice_no_fallback | row_ols_child_fe_cluster | utterance | nb_phonemes | fit | 4.412e+05 | 21 | 0.1227 | 1 |
| route2_effort_choice_no_fallback | route2_nb_phonemes_effort_choice_no_fallback | session_gee_exchangeable | child_session | nb_phonemes | fit | 976 | 21 | 0.2925 | 1 |
| route2_effort_choice_no_fallback | route2_nb_phonemes_effort_choice_no_fallback | session_mundlak_gee | child_session | nb_phonemes | fit | 976 | 21 | 0.5016 | 1 |
| route2_effort_choice_no_fallback | route2_nb_phonemes_effort_choice_no_fallback | session_mixedlm_random_age | child_session | nb_phonemes | fit | 976 | 21 | 0.7754 | 1 |
| route1_information_response_space_enriched | route1_sum_bits_response_space_enriched | row_ols_child_fe_cluster | utterance | sum_bits | fit | 4.414e+05 | 21 | 0.6284 | 0 |
| route1_information_response_space_enriched | route1_sum_bits_response_space_enriched | session_gee_exchangeable | child_session | sum_bits | fit | 976 | 21 | 0.8388 | 0 |
| route1_information_response_space_enriched | route1_sum_bits_response_space_enriched | session_mundlak_gee | child_session | sum_bits | fit | 976 | 21 | 0.867 | 0 |
| route1_information_response_space_enriched | route1_sum_bits_response_space_enriched | session_mixedlm_random_age | child_session | sum_bits | fit | 976 | 21 | 0.9353 | 0 |
| route1_information_age_entropy_interaction | route1_sum_bits_age_by_response_entropy | row_ols_child_fe_cluster | utterance | sum_bits | fit | 4.414e+05 | 21 | 0.6284 | 0 |
| route1_information_age_entropy_interaction | route1_sum_bits_age_by_response_entropy | session_gee_exchangeable | child_session | sum_bits | fit | 976 | 21 | 0.8382 | 0 |
| route1_information_age_entropy_interaction | route1_sum_bits_age_by_response_entropy | session_mundlak_gee | child_session | sum_bits | fit | 976 | 21 | 0.8671 | 0 |
| route1_information_age_entropy_interaction | route1_sum_bits_age_by_response_entropy | session_mixedlm_random_age | child_session | sum_bits | fit | 976 | 21 | 0.9353 | 0 |
| route1_information_response_space_enriched | route1_mean_bits_per_token_response_space_enriched | row_ols_child_fe_cluster | utterance | mean_bits_per_token | fit | 4.414e+05 | 21 | 0.05703 | 0 |
| route1_information_response_space_enriched | route1_mean_bits_per_token_response_space_enriched | session_gee_exchangeable | child_session | mean_bits_per_token | fit | 976 | 21 | 0.1456 | 0 |
| route1_information_response_space_enriched | route1_mean_bits_per_token_response_space_enriched | session_mundlak_gee | child_session | mean_bits_per_token | fit | 976 | 21 | 0.2308 | 0 |
| route1_information_response_space_enriched | route1_mean_bits_per_token_response_space_enriched | session_mixedlm_random_age | child_session | mean_bits_per_token | fit | 976 | 21 | 0.6372 | 0 |
| route1_information_age_entropy_interaction | route1_mean_bits_per_token_age_by_response_entropy | row_ols_child_fe_cluster | utterance | mean_bits_per_token | fit | 4.414e+05 | 21 | 0.05713 | 0 |
| route1_information_age_entropy_interaction | route1_mean_bits_per_token_age_by_response_entropy | session_gee_exchangeable | child_session | mean_bits_per_token | fit | 976 | 21 | 0.1636 | 0 |
| route1_information_age_entropy_interaction | route1_mean_bits_per_token_age_by_response_entropy | session_mundlak_gee | child_session | mean_bits_per_token | fit | 976 | 21 | 0.2493 | 0 |
| route1_information_age_entropy_interaction | route1_mean_bits_per_token_age_by_response_entropy | session_mixedlm_random_age | child_session | mean_bits_per_token | fit | 976 | 21 | 0.6446 | 0 |

## Key Response-Space Coefficients

| family | outcome | model_id | term | estimate | std_error | p_value | conf_low | conf_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_months_c | -0.04121 | 0.0072 | 1.041e-08 | -0.05532 | -0.0271 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_months_c | -0.009159 | 0.009539 | 0.337 | -0.02786 | 0.009538 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_months_c | -0.04514 | 0.01283 | 0.0004348 | -0.07029 | -0.01999 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_months_c:response_entropy_bits_c | -0.002581 | 0.00116 | 0.02601 | -0.004854 | -0.0003086 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_months_c:response_entropy_bits_c | -0.03276 | 0.008865 | 0.0002197 | -0.05014 | -0.01538 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_months_c:response_entropy_bits_c | -0.02193 | 0.004753 | 3.947e-06 | -0.03125 | -0.01262 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_within_child_c | -0.01259 | 0.009966 | 0.2064 | -0.03213 | 0.006942 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | age_within_child_c:response_entropy_bits_c | -0.03892 | 0.0144 | 0.006873 | -0.06715 | -0.0107 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | child_mean_age_c | 0.01452 | 0.02174 | 0.5042 | -0.02808 | 0.05712 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | context_entropy_bits_c | -0.1671 | 0.01158 | 3.475e-47 | -0.1898 | -0.1444 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | context_entropy_bits_c | 0.6528 | 0.2709 | 0.01598 | 0.1217 | 1.184 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | context_entropy_bits_c | 0.6128 | 0.2737 | 0.02515 | 0.07639 | 1.149 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | context_entropy_bits_c | 0.6217 | 0.08628 | 5.806e-13 | 0.4526 | 0.7908 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | generated_expected_words_c | 0.06745 | 0.00704 | 9.574e-22 | 0.05365 | 0.08125 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | generated_expected_words_c | -0.08817 | 0.1009 | 0.3822 | -0.2859 | 0.1096 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | generated_expected_words_c | -0.08776 | 0.1046 | 0.4016 | -0.2928 | 0.1173 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | generated_expected_words_c | 0.001254 | 0.07599 | 0.9868 | -0.1477 | 0.1502 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | nb_words_c | -0.09208 | 0.01938 | 2.014e-06 | -0.1301 | -0.0541 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | nb_words_c | -0.3219 | 0.07413 | 1.411e-05 | -0.4672 | -0.1766 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | nb_words_c | -0.292 | 0.07596 | 0.0001208 | -0.4409 | -0.1431 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | nb_words_c | -0.2407 | 0.03272 | 1.904e-13 | -0.3048 | -0.1765 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | response_entropy_bits_c | 0.1112 | 0.008538 | 9.179e-39 | 0.09444 | 0.1279 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | response_entropy_bits_c | 0.4659 | 0.1794 | 0.009394 | 0.1143 | 0.8175 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | response_entropy_bits_c | 0.4113 | 0.1663 | 0.0134 | 0.08533 | 0.7372 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | response_entropy_bits_c | 0.4013 | 0.09465 | 2.239e-05 | 0.2158 | 0.5868 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | route2_context_word_count_c | -0.006145 | 0.002326 | 0.008245 | -0.0107 | -0.001586 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | route2_context_word_count_c | -0.02179 | 0.01362 | 0.1095 | -0.04848 | 0.004896 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | route2_context_word_count_c | -0.02064 | 0.01326 | 0.1196 | -0.04663 | 0.005352 |
| route1_information_age_entropy_interaction | mean_bits_per_token | route1_mean_bits_per_token_age_by_response_entropy | route2_context_word_count_c | -0.02906 | 0.009796 | 0.003016 | -0.04826 | -0.009856 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_months_c | -0.1257 | 0.02962 | 2.188e-05 | -0.1838 | -0.06767 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_months_c | -0.03355 | 0.03733 | 0.3688 | -0.1067 | 0.03962 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_months_c | -0.1126 | 0.03822 | 0.003224 | -0.1875 | -0.03767 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_months_c:response_entropy_bits_c | -0.005002 | 0.003862 | 0.1953 | -0.01257 | 0.002568 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_months_c:response_entropy_bits_c | -0.04129 | 0.01525 | 0.006778 | -0.07118 | -0.0114 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_months_c:response_entropy_bits_c | -0.01504 | 0.01742 | 0.3878 | -0.04918 | 0.01909 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_within_child_c | -0.04241 | 0.0372 | 0.2543 | -0.1153 | 0.03051 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | age_within_child_c:response_entropy_bits_c | -0.04797 | 0.01861 | 0.009926 | -0.08444 | -0.01151 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | child_mean_age_c | 0.1103 | 0.08317 | 0.1847 | -0.05269 | 0.2734 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | context_entropy_bits_c | -0.5055 | 0.03648 | 1.144e-43 | -0.577 | -0.434 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | context_entropy_bits_c | 2.34 | 0.3464 | 1.427e-11 | 1.661 | 3.019 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | context_entropy_bits_c | 2.265 | 0.3447 | 5.02e-11 | 1.589 | 2.94 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | context_entropy_bits_c | 2.186 | 0.3161 | 4.668e-12 | 1.566 | 2.805 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | generated_expected_words_c | 0.1626 | 0.01837 | 8.546e-19 | 0.1266 | 0.1986 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | generated_expected_words_c | -0.8016 | 0.325 | 0.01363 | -1.438 | -0.1647 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | generated_expected_words_c | -0.7684 | 0.3263 | 0.01852 | -1.408 | -0.1289 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | generated_expected_words_c | -0.589 | 0.2786 | 0.0345 | -1.135 | -0.04295 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | nb_words_c | 6.349 | 0.1585 | 0 | 6.039 | 6.66 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | nb_words_c | 5.569 | 0.2803 | 8.212e-88 | 5.02 | 6.118 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | nb_words_c | 5.637 | 0.276 | 1.047e-92 | 5.096 | 6.178 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | nb_words_c | 5.796 | 0.1204 | 0 | 5.56 | 6.032 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | response_entropy_bits_c | 0.3742 | 0.02889 | 2.226e-38 | 0.3176 | 0.4309 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | response_entropy_bits_c | 2.235 | 0.4545 | 8.724e-07 | 1.345 | 3.126 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | response_entropy_bits_c | 2.187 | 0.4685 | 3.045e-06 | 1.269 | 3.105 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | response_entropy_bits_c | 2.029 | 0.347 | 4.953e-09 | 1.349 | 2.709 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | route2_context_word_count_c | -0.06371 | 0.008609 | 1.361e-13 | -0.08058 | -0.04683 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | route2_context_word_count_c | -0.09844 | 0.07298 | 0.1774 | -0.2415 | 0.0446 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | route2_context_word_count_c | -0.09541 | 0.0737 | 0.1955 | -0.2399 | 0.04904 |
| route1_information_age_entropy_interaction | sum_bits | route1_sum_bits_age_by_response_entropy | route2_context_word_count_c | -0.1104 | 0.03598 | 0.002155 | -0.1809 | -0.03986 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | age_months_c | -0.04147 | 0.007281 | 1.23e-08 | -0.05574 | -0.0272 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | age_months_c | -0.01457 | 0.009663 | 0.1316 | -0.03351 | 0.004369 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | age_months_c | -0.04716 | 0.01311 | 0.0003216 | -0.07286 | -0.02147 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | age_within_child_c | -0.01589 | 0.01007 | 0.1146 | -0.03562 | 0.00385 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | child_mean_age_c | 0.01169 | 0.02049 | 0.5682 | -0.02846 | 0.05185 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | context_entropy_bits_c | -0.1672 | 0.01154 | 1.647e-47 | -0.1898 | -0.1445 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | context_entropy_bits_c | 0.6484 | 0.3209 | 0.04335 | 0.01936 | 1.277 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | context_entropy_bits_c | 0.638 | 0.32 | 0.04616 | 0.01086 | 1.265 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | context_entropy_bits_c | 0.6174 | 0.0872 | 1.436e-12 | 0.4465 | 0.7884 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | generated_expected_words_c | 0.0669 | 0.007058 | 2.566e-21 | 0.05307 | 0.08073 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | generated_expected_words_c | -0.1098 | 0.1021 | 0.282 | -0.3098 | 0.09023 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | generated_expected_words_c | -0.1018 | 0.102 | 0.3181 | -0.3017 | 0.09804 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | generated_expected_words_c | -0.001464 | 0.07678 | 0.9848 | -0.1519 | 0.149 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | nb_words_c | -0.09209 | 0.01938 | 2.026e-06 | -0.1301 | -0.0541 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | nb_words_c | -0.2777 | 0.07699 | 0.0003105 | -0.4285 | -0.1268 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | nb_words_c | -0.2698 | 0.07703 | 0.0004611 | -0.4208 | -0.1188 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | nb_words_c | -0.2149 | 0.03258 | 4.259e-11 | -0.2787 | -0.151 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | response_entropy_bits_c | 0.1125 | 0.009187 | 1.88e-34 | 0.09446 | 0.1305 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | response_entropy_bits_c | 0.5313 | 0.1961 | 0.00675 | 0.1469 | 0.9156 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | response_entropy_bits_c | 0.5374 | 0.199 | 0.006912 | 0.1475 | 0.9274 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | response_entropy_bits_c | 0.4235 | 0.09552 | 9.254e-06 | 0.2363 | 0.6107 |
| route1_information_response_space_enriched | mean_bits_per_token | route1_mean_bits_per_token_response_space_enriched | route2_context_word_count_c | -0.006187 | 0.002329 | 0.007893 | -0.01075 | -0.001622 |

## Interpretation Boundary

- Route 2 effort-choice models ask whether actual child effort varies with response-space uncertainty and generated expected effort for the same context.
- Route 1 enriched models ask whether actual child information is associated with response-space predictors after child effort and context controls.
- The full communicative-efficiency cloud still requires scoring generated responses on Mila.
