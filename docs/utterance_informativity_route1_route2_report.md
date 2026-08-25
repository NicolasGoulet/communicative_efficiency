# Utterance Informativity: Route 1 and Route 2

This report treats utterances as the primary unit. It leverages the distinction
between unconditional frequency and contextual predictability without
reproducing a phone-level analysis.

## Definitions

```text
k0 = -log2 p_Mistral(utterance)
k3 = -log2 p_Mistral(utterance | preceding three utterances)
context support = k0 - k3
```

One occurrence's k3 score is contextual self-information. The developmental
informativity summaries below are adjusted mean k3 scores after every age bin
is standardized to the same pooled exact/top-coded word-effort distribution.
Lower values mean greater Mistral predictability, not more meaning transmitted.

The total-bit models retain 1,122,396 child and
1,467,432 caregiver utterances. The
k0-versus-k3 density coupling requires identical positive evaluation-token
counts and therefore uses 1,121,627 child
and 1,466,777 caregiver rows; the
769 and
655 excluded rows remain in
the valid total-bit analyses.

## Existing Route 1 models retained

| scope | model_id | tier | age_estimate | age_ci_low | age_ci_high | fit_status | protocol_result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | primary | -0.1313 | -0.1792 | -0.0834 | PASS | expected_direction_interval_excludes_zero |
| pbm_discovery | P2_k0_unconditional | primary | -0.1617 | -0.2113 | -0.112 | PASS | decomposition_no_directional_rule |
| pbm_discovery | P3_k3_context_gain | primary | -0.03048 | -0.05029 | -0.01066 | PASS | contrary_direction_interval_excludes_zero |
| non_pbm_confirmation | P1_k3_contextual | primary | -0.06225 | -0.1318 | 0.007303 | PASS | expected_direction_interval_includes_zero |
| non_pbm_confirmation | P2_k0_unconditional | primary | -0.08918 | -0.1445 | -0.03386 | PASS | decomposition_no_directional_rule |
| non_pbm_confirmation | P3_k3_context_gain | primary | -0.02776 | -0.04529 | -0.01024 | PASS | contrary_direction_interval_excludes_zero |
| all79_descriptive | P1_k3_contextual | primary | -0.07967 | -0.1344 | -0.02492 | PASS | expected_direction_interval_excludes_zero |
| all79_descriptive | P2_k0_unconditional | primary | -0.1075 | -0.156 | -0.05902 | PASS | decomposition_no_directional_rule |
| all79_descriptive | P3_k3_context_gain | primary | -0.0287 | -0.04097 | -0.01643 | PASS | contrary_direction_interval_excludes_zero |
| pbm_discovery | C1_caretaker_k3_contextual | caretaker_input | 0.04129 | -0.006881 | 0.08946 | PASS | secondary_no_decision_rule |
| pbm_discovery | C2_caretaker_k0_unconditional | caretaker_input | -0.03868 | -0.08691 | 0.009544 | PASS | secondary_no_decision_rule |
| pbm_discovery | C3_caretaker_k3_context_gain | caretaker_input | -0.07988 | -0.09838 | -0.06137 | PASS | secondary_no_decision_rule |
| non_pbm_confirmation | C1_caretaker_k3_contextual | caretaker_input | 0.001123 | -0.04406 | 0.04631 | PASS | secondary_no_decision_rule |
| non_pbm_confirmation | C2_caretaker_k0_unconditional | caretaker_input | -0.05417 | -0.09724 | -0.0111 | PASS | secondary_no_decision_rule |
| non_pbm_confirmation | C3_caretaker_k3_context_gain | caretaker_input | -0.0552 | -0.07753 | -0.03286 | PASS | secondary_no_decision_rule |
| all79_descriptive | C1_caretaker_k3_contextual | caretaker_input | 0.01808 | -0.01288 | 0.04904 | PASS | secondary_no_decision_rule |
| all79_descriptive | C2_caretaker_k0_unconditional | caretaker_input | -0.04768 | -0.07852 | -0.01685 | PASS | secondary_no_decision_rule |
| all79_descriptive | C3_caretaker_k3_context_gain | caretaker_input | -0.06566 | -0.08127 | -0.05004 | PASS | secondary_no_decision_rule |

These are the frozen fixed-effort P1/P2/P3 child models and C1/C2/C3 caregiver
comparisons. The new terminology does not change their original outcomes,
sample roles, intervals, or protocol decisions.

## Effort-standardized utterance informativity

| role | estimand | age_bin | estimate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| child | contextual informativity (k3) | 006-023 | 29.51 | 28.9 | 30.11 |
| child | contextual informativity (k3) | 024-029 | 29.18 | 28.57 | 29.78 |
| child | contextual informativity (k3) | 030-035 | 27.91 | 27.55 | 28.26 |
| child | contextual informativity (k3) | 036-041 | 27.45 | 26.96 | 27.93 |
| child | contextual informativity (k3) | 042-047 | 26.97 | 26.1 | 27.85 |
| child | contextual informativity (k3) | 048-053 | 27.47 | 27.01 | 27.92 |
| child | contextual informativity (k3) | 054-059 | 27.46 | 26.92 | 28 |
| child | contextual informativity (k3) | 060-065 | 26.29 | 25.57 | 27.01 |
| child | unconditional form information (k0) | 006-023 | 42.53 | 41.88 | 43.17 |
| child | unconditional form information (k0) | 024-029 | 42.05 | 41.61 | 42.49 |
| child | unconditional form information (k0) | 030-035 | 40.8 | 40.4 | 41.19 |
| child | unconditional form information (k0) | 036-041 | 40.13 | 39.82 | 40.44 |
| child | unconditional form information (k0) | 042-047 | 39.28 | 38.5 | 40.06 |
| child | unconditional form information (k0) | 048-053 | 39.6 | 39.17 | 40.03 |
| child | unconditional form information (k0) | 054-059 | 39.37 | 38.71 | 40.04 |
| child | unconditional form information (k0) | 060-065 | 38.21 | 37.47 | 38.95 |
| child | context support (k0-k3) | 006-023 | 13.02 | 12.66 | 13.38 |
| child | context support (k0-k3) | 024-029 | 12.87 | 12.65 | 13.08 |
| child | context support (k0-k3) | 030-035 | 12.89 | 12.75 | 13.03 |
| child | context support (k0-k3) | 036-041 | 12.68 | 12.39 | 12.98 |
| child | context support (k0-k3) | 042-047 | 12.31 | 12.11 | 12.5 |
| child | context support (k0-k3) | 048-053 | 12.13 | 11.89 | 12.38 |
| child | context support (k0-k3) | 054-059 | 11.92 | 11.61 | 12.23 |
| child | context support (k0-k3) | 060-065 | 11.92 | 11.7 | 12.14 |
| caretaker | contextual informativity (k3) | 006-023 | 30.51 | 30.03 | 30.99 |
| caretaker | contextual informativity (k3) | 024-029 | 30.68 | 30.29 | 31.07 |
| caretaker | contextual informativity (k3) | 030-035 | 30.58 | 30.31 | 30.85 |
| caretaker | contextual informativity (k3) | 036-041 | 30.43 | 30.13 | 30.73 |
| caretaker | contextual informativity (k3) | 042-047 | 30.98 | 30.59 | 31.37 |
| caretaker | contextual informativity (k3) | 048-053 | 31 | 30.68 | 31.31 |
| caretaker | contextual informativity (k3) | 054-059 | 31.42 | 30.75 | 32.09 |
| caretaker | contextual informativity (k3) | 060-065 | 31.26 | 30.89 | 31.63 |
| caretaker | unconditional form information (k0) | 006-023 | 49.4 | 48.87 | 49.92 |
| caretaker | unconditional form information (k0) | 024-029 | 49.04 | 48.72 | 49.35 |
| caretaker | unconditional form information (k0) | 030-035 | 48.44 | 48.12 | 48.77 |
| caretaker | unconditional form information (k0) | 036-041 | 48.03 | 47.78 | 48.28 |
| caretaker | unconditional form information (k0) | 042-047 | 48.06 | 47.58 | 48.54 |
| caretaker | unconditional form information (k0) | 048-053 | 47.98 | 47.61 | 48.36 |
| caretaker | unconditional form information (k0) | 054-059 | 48.05 | 47.43 | 48.68 |
| caretaker | unconditional form information (k0) | 060-065 | 47.71 | 47.33 | 48.09 |
| caretaker | context support (k0-k3) | 006-023 | 18.89 | 18.63 | 19.15 |
| caretaker | context support (k0-k3) | 024-029 | 18.36 | 18.13 | 18.59 |
| caretaker | context support (k0-k3) | 030-035 | 17.86 | 17.71 | 18.01 |
| caretaker | context support (k0-k3) | 036-041 | 17.6 | 17.23 | 17.96 |
| caretaker | context support (k0-k3) | 042-047 | 17.08 | 16.74 | 17.42 |
| caretaker | context support (k0-k3) | 048-053 | 16.99 | 16.51 | 17.46 |
| caretaker | context support (k0-k3) | 054-059 | 16.63 | 16.3 | 16.97 |
| caretaker | context support (k0-k3) | 060-065 | 16.45 | 16.13 | 16.77 |

Formula for each saved outcome:

```text
cell mean ~ age bin + exact/top-coded word count + child identity
```

The estimates average the fitted cells over the same scope/role-pooled effort
distribution and the same scope-specific child reference population.

## Developmental frequency-informativity coupling

| role | analysis_scope | estimate | std_error | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| child | pbm_discovery | 0.006503 | 0.007877 | -0.008936 | 0.02194 | 0.4091 |
| child | non_pbm_confirmation | -0.006051 | 0.002951 | -0.01184 | -0.0002671 | 0.04032 |
| child | all79_descriptive | -0.01126 | 0.003264 | -0.01766 | -0.004864 | 0.00056 |
| caretaker | pbm_discovery | 0.002946 | 0.004209 | -0.005304 | 0.0112 | 0.484 |
| caretaker | non_pbm_confirmation | -3.859e-05 | 0.0048 | -0.009446 | 0.009369 | 0.9936 |
| caretaker | all79_descriptive | -9.277e-05 | 0.003435 | -0.006825 | 0.006639 | 0.9785 |

The displayed term is `age:k0 density` from the registered nonlinear cell
model. It asks whether unconditional and contextual scorer predictability
become more or less coupled with age. Shared Mistral scoring creates mechanical
association between k0 and k3, so the interaction and separate context-support
trajectory are the relevant quantities.

## Existing Route 2 and joint models retained

| analysis_scope | model_id | outcome | family | n_rows | deviance_explained | status |
| --- | --- | --- | --- | --- | --- | --- |
| all79 | m1_length_primary | child_words | negative_binomial | 1122396 | 0.1368 | PASS |
| all79 | m2_length_qwen_reference | child_words | negative_binomial | 1122396 | 0.1375 | PASS |
| all79 | m3_information_k3_total | child_k3_sum_bits | scaled_t | 1122396 | 0.5072 | PASS |
| all79 | m3b_information_k3_per_token | child_k3_bits_per_token | scaled_t | 1122396 | 0.06485 | PASS |
| all79 | m3c_information_k0_total | child_k0_sum_bits | scaled_t | 1122396 | 0.5696 | PASS |
| all79 | m3d_context_support | child_context_support_bits | scaled_t | 1122396 | 0.04422 | PASS |
| all79 | m4_effort_percentile | effort_percentile_open | beta | 1122396 | 0.1977 | PASS |
| all79 | m5_exact_length_k3_gap | child_minus_exact_length_qwen_median_k3 | scaled_t | 525873 | 0.1395 | PASS |
| pbm_discovery | m1_length_primary | child_words | negative_binomial | 444325 | 0.1804 | PASS |
| pbm_discovery | m3_information_k3_total | child_k3_sum_bits | scaled_t | 444325 | 0.5027 | PASS |
| pbm_discovery | m4_effort_percentile | effort_percentile_open | beta | 444325 | 0.2129 | PASS |
| non_pbm_confirmation | m1_length_primary | child_words | negative_binomial | 678071 | 0.1075 | PASS |
| non_pbm_confirmation | m3_information_k3_total | child_k3_sum_bits | scaled_t | 678071 | 0.5121 | PASS |
| non_pbm_confirmation | m4_effort_percentile | effort_percentile_open | beta | 678071 | 0.1888 | PASS |

Route 2 remains the effort-adaptation analysis. Raw effort (`m1`), the separate
Qwen expected-length sensitivity (`m2`), generated-relative effort percentile
(`m4`), and exact-length information calibration (`m5`) are distinct
estimands. Same-length n-gram or LSTM candidates are not effort baselines.

## Recurrent exact utterance types

The table below uses exact strings with at least 100 occurrences, 10 children,
and 3 corpora. Type informativity is mean k3 across attested contexts.

| role | target_text | occurrences | children | corpora | word_count | empirical_frequency_bits | mean_k3_total_bits | mean_context_support_bits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| caretaker | oh. | 29969 | 74 | 12 | 1 | 5.614 | 11.09 | 12.06 |
| caretaker | yeah. | 27220 | 64 | 12 | 1 | 5.752 | 10.21 | 15.28 |
| caretaker | no. | 26861 | 78 | 12 | 1 | 5.772 | 9.687 | 12.29 |
| caretaker | okay. | 17804 | 48 | 12 | 1 | 6.365 | 9.698 | 14.45 |
| caretaker | yes. | 13104 | 77 | 12 | 1 | 6.807 | 10.06 | 12.89 |
| caretaker | right. | 12287 | 68 | 12 | 1 | 6.9 | 11.75 | 13.5 |
| caretaker | mhm. | 8433 | 40 | 9 | 1 | 7.443 | 16.18 | 15.58 |
| caretaker | what? | 7170 | 75 | 12 | 1 | 7.677 | 10.96 | 12.59 |
| caretaker | that's right. | 6707 | 69 | 12 | 2 | 7.773 | 13.09 | 16 |
| caretaker | well. | 5680 | 51 | 11 | 1 | 8.013 | 12.17 | 10.85 |
| caretaker | that's it. | 5501 | 60 | 11 | 2 | 8.059 | 12.93 | 16.72 |
| caretaker | come on. | 5313 | 70 | 12 | 2 | 8.11 | 12.17 | 16.92 |
| caretaker | there. | 4963 | 66 | 12 | 1 | 8.208 | 12.41 | 12.9 |
| caretaker | look. | 4751 | 66 | 12 | 1 | 8.271 | 12.45 | 14.06 |
| caretaker | hm? | 4494 | 40 | 12 | 1 | 8.351 | 15.25 | 17.25 |
| child | yeah. | 59426 | 69 | 12 | 1 | 4.239 | 10.4 | 15.09 |
| child | no. | 40434 | 78 | 12 | 1 | 4.795 | 9.795 | 12.18 |
| child | yes. | 16019 | 78 | 12 | 1 | 6.131 | 9.804 | 13.14 |
| child | oh. | 15688 | 77 | 12 | 1 | 6.161 | 11.46 | 11.7 |
| child | there. | 7087 | 74 | 12 | 1 | 7.307 | 13.47 | 11.84 |
| child | what? | 6574 | 71 | 12 | 1 | 7.416 | 11.89 | 11.66 |
| child | look. | 6160 | 75 | 11 | 1 | 7.509 | 14.05 | 12.45 |
| child | why? | 5220 | 62 | 12 | 1 | 7.748 | 12.26 | 12.5 |
| child | mhm. | 5140 | 38 | 10 | 1 | 7.771 | 17.1 | 14.66 |
| child | Mummy. | 4983 | 52 | 8 | 1 | 7.815 | 22.98 | 4.023 |
| child | okay. | 4417 | 50 | 12 | 1 | 7.989 | 10.13 | 14.01 |
| child | um. | 3262 | 63 | 11 | 1 | 8.427 | 14.11 | 11.86 |
| child | huh? | 3168 | 39 | 11 | 1 | 8.469 | 13.03 | 13.22 |
| child | I don't know. | 3017 | 60 | 12 | 3 | 8.539 | 13.43 | 9.103 |
| child | what's that? | 2905 | 67 | 11 | 2 | 8.594 | 14.34 | 13.96 |

## Interpretation limits

- Lower k3 means greater scorer predictability, not greater Shannon information
  transmitted.
- k0 is unconditional Mistral self-information, not empirical frequency. The
  recurrent table contains the separate empirical recurrence measure.
- The analysis does not measure semantic informativeness or listener utility.
- Exact-string Qwen entropy is not semantic response uncertainty.
- Generated responses are not meaning-preserving alternatives.
- PBM discovery, non-PBM confirmation, and all-79 descriptive estimates remain
  separate.
