# Mistral full-79: Direct-Surprisal Replication

This report implements the frozen 2026-07-21 direct-surprisal protocol. A negative contextual-surprisal age coefficient means greater scorer predictability at the same exact/top-coded lexical word effort; it is not, by itself, proof of a normative efficiency optimum.

## Input And Sample Flow

Input wide table: `results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz`

| scope | step | rows | children | corpora | sessions |
| --- | --- | --- | --- | --- | --- |
| pbm_discovery | source_rows | 446985.000 | 21.000 | 3.000 | 983.000 |
| pbm_discovery | age_006_065 | 446985.000 | 21.000 | 3.000 | 983.000 |
| pbm_discovery | nonempty_real_target | 446985.000 | 21.000 | 3.000 | 983.000 |
| pbm_discovery | finite_scored_real_k3 | 446985.000 | 21.000 | 3.000 | 983.000 |
| pbm_discovery | primary_context_bearing | 444325.000 | 21.000 | 3.000 | 982.000 |
| non_pbm_confirmation | source_rows | 693710.000 | 58.000 | 10.000 | 1770.000 |
| non_pbm_confirmation | age_006_065 | 693710.000 | 58.000 | 10.000 | 1770.000 |
| non_pbm_confirmation | nonempty_real_target | 693710.000 | 58.000 | 10.000 | 1770.000 |
| non_pbm_confirmation | finite_scored_real_k3 | 693710.000 | 58.000 | 10.000 | 1770.000 |
| non_pbm_confirmation | primary_context_bearing | 678071.000 | 58.000 | 10.000 | 1737.000 |
| all79_descriptive | source_rows | 1140695.000 | 79.000 | 13.000 | 2753.000 |
| all79_descriptive | age_006_065 | 1140695.000 | 79.000 | 13.000 | 2753.000 |
| all79_descriptive | nonempty_real_target | 1140695.000 | 79.000 | 13.000 | 2753.000 |
| all79_descriptive | finite_scored_real_k3 | 1140695.000 | 79.000 | 13.000 | 2753.000 |
| all79_descriptive | primary_context_bearing | 1122396.000 | 79.000 | 13.000 | 2719.000 |

## Frozen Primary Results

| scope | model_id | source_rows | children | corpora | age_estimate | age_ci_low | age_ci_high | age_p_value | protocol_result | fit_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | 444325.000 | 21.000 | 3.000 | -0.131 | -0.179 | -0.083 | 7.70e-08 | expected_direction_interval_excludes_zero | PASS |
| pbm_discovery | P2_k0_unconditional | 446985.000 | 21.000 | 3.000 | -0.162 | -0.211 | -0.112 | 1.81e-10 | decomposition_no_directional_rule | PASS |
| pbm_discovery | P3_k3_context_gain | 444325.000 | 21.000 | 3.000 | -0.030 | -0.050 | -0.011 | 0.003 | contrary_direction_interval_excludes_zero | PASS |
| non_pbm_confirmation | P1_k3_contextual | 678071.000 | 58.000 | 10.000 | -0.062 | -0.132 | 0.007 | 0.079 | expected_direction_interval_includes_zero | PASS |
| non_pbm_confirmation | P2_k0_unconditional | 693710.000 | 58.000 | 10.000 | -0.089 | -0.145 | -0.034 | 0.002 | decomposition_no_directional_rule | PASS |
| non_pbm_confirmation | P3_k3_context_gain | 678071.000 | 58.000 | 10.000 | -0.028 | -0.045 | -0.010 | 0.002 | contrary_direction_interval_excludes_zero | PASS |
| all79_descriptive | P1_k3_contextual | 1122396.000 | 79.000 | 13.000 | -0.080 | -0.134 | -0.025 | 0.004 | expected_direction_interval_excludes_zero | PASS |
| all79_descriptive | P2_k0_unconditional | 1140695.000 | 79.000 | 13.000 | -0.108 | -0.156 | -0.059 | 1.39e-05 | decomposition_no_directional_rule | PASS |
| all79_descriptive | P3_k3_context_gain | 1122396.000 | 79.000 | 13.000 | -0.029 | -0.041 | -0.016 | 4.55e-06 | contrary_direction_interval_excludes_zero | PASS |

Context gain is `sum_bits_k0 - sum_bits_k3`; positive values mean context made the observed target more probable under this scorer.

## Child Bootstrap

| scope | model_id | outcome | requested_reps | successful_reps | bootstrap_mean | bootstrap_se | bootstrap_ci_low | bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | 200.000 | 200.000 | -0.081 | 0.029 | -0.141 | -0.039 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | 200.000 | 200.000 | -0.028 | 0.007 | -0.040 | -0.015 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | 200.000 | 200.000 | -0.065 | 0.036 | -0.152 | -0.014 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | 200.000 | 200.000 | -0.028 | 0.009 | -0.046 | -0.010 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | 200.000 | 200.000 | -0.130 | 0.025 | -0.178 | -0.080 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | 200.000 | 200.000 | -0.027 | 0.013 | -0.045 | 0.007 |

## Frozen Age-Bin Contrasts

Contrasts use `006-023` as the reference at fixed exact/top-coded lexical word effort with child fixed effects and child-clustered covariance. They do not by themselves establish a sustained developmental onset.

| scope | model_id | term | estimate | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.897 | -1.553 | -0.241 | 0.007 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -2.031 | -2.840 | -1.222 | 8.74e-07 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -1.934 | -3.658 | -0.210 | 0.028 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -4.215 | -6.958 | -1.472 | 0.003 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -2.647 | -4.082 | -1.213 | 2.98e-04 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -3.275 | -4.685 | -1.865 | 5.29e-06 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -5.378 | -8.103 | -2.652 | 1.10e-04 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.973 | -1.705 | -0.240 | 0.009 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -2.035 | -2.865 | -1.206 | 1.53e-06 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -2.659 | -4.481 | -0.837 | 0.004 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -4.760 | -7.110 | -2.410 | 7.19e-05 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -3.804 | -5.250 | -2.358 | 2.52e-07 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -4.823 | -6.301 | -3.345 | 1.61e-10 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -6.883 | -10.045 | -3.720 | 2.00e-05 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.074 | -0.577 | 0.429 | 0.772 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -0.008 | -0.634 | 0.618 | 0.980 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -0.711 | -1.416 | -0.006 | 0.048 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -0.515 | -1.200 | 0.171 | 0.141 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -1.207 | -1.861 | -0.554 | 2.94e-04 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -1.538 | -2.237 | -0.839 | 1.61e-05 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -1.400 | -2.307 | -0.492 | 0.003 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | 0.413 | -0.891 | 1.717 | 0.534 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -1.158 | -2.459 | 0.143 | 0.081 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -1.603 | -2.814 | -0.393 | 0.009 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -1.639 | -2.929 | -0.350 | 0.013 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -1.398 | -2.628 | -0.168 | 0.026 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -1.308 | -2.619 | 0.003 | 0.050 |
| non_pbm_confirmation | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -2.418 | -3.644 | -1.191 | 1.12e-04 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.009 | -0.956 | 0.938 | 0.986 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -1.632 | -2.869 | -0.395 | 0.010 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -2.074 | -3.067 | -1.082 | 4.17e-05 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -2.563 | -3.713 | -1.414 | 1.24e-05 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -2.411 | -3.444 | -1.379 | 4.71e-06 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -2.495 | -3.591 | -1.399 | 8.18e-06 |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -3.631 | -4.650 | -2.612 | 2.88e-12 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.366 | -1.123 | 0.390 | 0.343 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -0.408 | -1.026 | 0.211 | 0.197 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -0.427 | -1.064 | 0.210 | 0.189 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -0.898 | -1.534 | -0.263 | 0.006 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -0.960 | -1.629 | -0.292 | 0.005 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -1.131 | -1.862 | -0.399 | 0.002 |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -1.173 | -1.820 | -0.526 | 3.79e-04 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.329 | -1.016 | 0.358 | 0.348 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -1.602 | -2.340 | -0.863 | 2.12e-05 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -2.062 | -2.974 | -1.150 | 9.29e-06 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -2.534 | -3.838 | -1.231 | 1.39e-04 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -2.043 | -2.979 | -1.107 | 1.88e-05 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -2.052 | -3.080 | -1.024 | 9.16e-05 |
| all79_descriptive | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -3.218 | -4.397 | -2.040 | 8.76e-08 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.498 | -1.113 | 0.116 | 0.112 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -1.753 | -2.556 | -0.951 | 1.83e-05 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -2.406 | -3.258 | -1.554 | 3.07e-08 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -3.245 | -4.474 | -2.015 | 2.31e-07 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -2.929 | -3.883 | -1.975 | 1.77e-09 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -3.168 | -4.299 | -2.037 | 4.02e-08 |
| all79_descriptive | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -4.336 | -5.554 | -3.119 | 2.93e-12 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.154 | -0.596 | 0.289 | 0.496 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -0.131 | -0.586 | 0.325 | 0.574 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -0.338 | -0.819 | 0.143 | 0.169 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -0.714 | -1.152 | -0.276 | 0.001 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -0.886 | -1.361 | -0.411 | 2.54e-04 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -1.102 | -1.624 | -0.580 | 3.51e-05 |
| all79_descriptive | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -1.100 | -1.551 | -0.649 | 1.75e-06 |

## Fixed-Effort Population Lines

### pbm_discovery

![pbm_discovery population predictions](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/population_fixed_effort_lines.png)

### non_pbm_confirmation

![non_pbm_confirmation population predictions](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/population_fixed_effort_lines.png)

### all79_descriptive

![all79_descriptive population predictions](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/population_fixed_effort_lines.png)

## Estimator And Secondary-Outcome Audit

| scope | model_id | tier | estimator | age_estimate | age_ci_low | age_ci_high | age_p_value | fit_status | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | primary | exact_cell_wls_child_cluster | -0.131 | -0.179 | -0.083 | 7.70e-08 | PASS |  |
| pbm_discovery | P1_k3_contextual_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| pbm_discovery | P1_k3_contextual_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.155 | -0.228 | -0.082 | 2.89e-05 | PASS |  |
| pbm_discovery | P1_k3_contextual_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.133 | -0.182 | -0.084 | 8.42e-08 | PASS |  |
| pbm_discovery | P1_k3_contextual_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.152 | -0.200 | -0.104 | 5.74e-10 | PASS |  |
| pbm_discovery | P2_k0_unconditional | primary | exact_cell_wls_child_cluster | -0.162 | -0.211 | -0.112 | 1.81e-10 | PASS |  |
| pbm_discovery | P2_k0_unconditional_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| pbm_discovery | P3_k3_context_gain | primary | exact_cell_wls_child_cluster | -0.030 | -0.050 | -0.011 | 0.003 | PASS |  |
| pbm_discovery | P3_k3_context_gain_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| pbm_discovery | P3_k3_context_gain_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.018 | -0.045 | 0.010 | 0.209 | PASS |  |
| pbm_discovery | P3_k3_context_gain_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.030 | -0.050 | -0.011 | 0.003 | PASS |  |
| pbm_discovery | P3_k3_context_gain_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.015 |  |  |  | PASS |  |
| pbm_discovery | S1_k1_contextual | secondary | exact_cell_wls_child_cluster | -0.152 | -0.196 | -0.107 | 2.36e-11 | PASS |  |
| pbm_discovery | S2_k2_contextual | secondary | exact_cell_wls_child_cluster | -0.137 | -0.184 | -0.091 | 8.49e-09 | PASS |  |
| pbm_discovery | S3_k1_context_gain | secondary | exact_cell_wls_child_cluster | -0.010 | -0.034 | 0.013 | 0.394 | PASS |  |
| pbm_discovery | S4_k2_context_gain | secondary | exact_cell_wls_child_cluster | -0.025 | -0.045 | -0.005 | 0.016 | PASS |  |
| pbm_discovery | B1_random_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.404 | 0.300 | 0.508 | 2.14e-14 | PASS |  |
| pbm_discovery | B2_unigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.076 | 0.021 | 0.131 | 0.007 | PASS |  |
| pbm_discovery | B3_bigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.069 | 0.025 | 0.114 | 0.002 | PASS |  |
| pbm_discovery | B4_trigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.082 | 0.051 | 0.113 | 3.15e-07 | PASS |  |
| non_pbm_confirmation | P1_k3_contextual | primary | exact_cell_wls_child_cluster | -0.062 | -0.132 | 0.007 | 0.079 | PASS |  |
| non_pbm_confirmation | P1_k3_contextual_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| non_pbm_confirmation | P1_k3_contextual_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.089 | -0.160 | -0.018 | 0.014 | PASS |  |
| non_pbm_confirmation | P1_k3_contextual_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.062 | -0.131 | 0.007 | 0.080 | PASS |  |
| non_pbm_confirmation | P1_k3_contextual_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.104 |  |  |  | PASS |  |
| non_pbm_confirmation | P2_k0_unconditional | primary | exact_cell_wls_child_cluster | -0.089 | -0.145 | -0.034 | 0.002 | PASS |  |
| non_pbm_confirmation | P2_k0_unconditional_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| non_pbm_confirmation | P3_k3_context_gain | primary | exact_cell_wls_child_cluster | -0.028 | -0.045 | -0.010 | 0.002 | PASS |  |
| non_pbm_confirmation | P3_k3_context_gain_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| non_pbm_confirmation | P3_k3_context_gain_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.024 | -0.048 | 4.04e-04 | 0.054 | PASS |  |
| non_pbm_confirmation | P3_k3_context_gain_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.028 | -0.045 | -0.010 | 0.002 | PASS |  |
| non_pbm_confirmation | P3_k3_context_gain_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.016 |  |  |  | PASS |  |
| non_pbm_confirmation | S1_k1_contextual | secondary | exact_cell_wls_child_cluster | -0.078 | -0.152 | -0.004 | 0.039 | PASS |  |
| non_pbm_confirmation | S2_k2_contextual | secondary | exact_cell_wls_child_cluster | -0.071 | -0.141 | -1.14e-04 | 0.050 | PASS |  |
| non_pbm_confirmation | S3_k1_context_gain | secondary | exact_cell_wls_child_cluster | -0.012 | -0.031 | 0.006 | 0.199 | PASS |  |
| non_pbm_confirmation | S4_k2_context_gain | secondary | exact_cell_wls_child_cluster | -0.019 | -0.037 | -0.002 | 0.027 | PASS |  |
| non_pbm_confirmation | B1_random_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.221 | 0.082 | 0.360 | 0.002 | PASS |  |
| non_pbm_confirmation | B2_unigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.034 | -0.021 | 0.089 | 0.231 | PASS |  |
| non_pbm_confirmation | B3_bigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.026 | -0.025 | 0.076 | 0.320 | PASS |  |
| non_pbm_confirmation | B4_trigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.026 | -0.020 | 0.072 | 0.273 | PASS |  |
| all79_descriptive | P1_k3_contextual | primary | exact_cell_wls_child_cluster | -0.080 | -0.134 | -0.025 | 0.004 | PASS |  |
| all79_descriptive | P1_k3_contextual_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| all79_descriptive | P1_k3_contextual_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.109 | -0.166 | -0.052 | 1.67e-04 | PASS |  |
| all79_descriptive | P1_k3_contextual_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.080 | -0.135 | -0.025 | 0.004 | PASS |  |
| all79_descriptive | P1_k3_contextual_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.123 | -0.165 | -0.081 | 1.06e-08 | PASS |  |
| all79_descriptive | P2_k0_unconditional | primary | exact_cell_wls_child_cluster | -0.108 | -0.156 | -0.059 | 1.39e-05 | PASS |  |
| all79_descriptive | P2_k0_unconditional_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| all79_descriptive | P3_k3_context_gain | primary | exact_cell_wls_child_cluster | -0.029 | -0.041 | -0.016 | 4.55e-06 | PASS |  |
| all79_descriptive | P3_k3_context_gain_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| all79_descriptive | P3_k3_context_gain_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.022 | -0.038 | -0.006 | 0.008 | PASS |  |
| all79_descriptive | P3_k3_context_gain_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.029 | -0.041 | -0.016 | 6.48e-06 | PASS |  |
| all79_descriptive | P3_k3_context_gain_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.016 |  |  |  | PASS |  |
| all79_descriptive | S1_k1_contextual | secondary | exact_cell_wls_child_cluster | -0.097 | -0.156 | -0.039 | 0.001 | PASS |  |
| all79_descriptive | S2_k2_contextual | secondary | exact_cell_wls_child_cluster | -0.087 | -0.143 | -0.032 | 0.002 | PASS |  |
| all79_descriptive | S3_k1_context_gain | secondary | exact_cell_wls_child_cluster | -0.011 | -0.025 | 0.003 | 0.114 | PASS |  |
| all79_descriptive | S4_k2_context_gain | secondary | exact_cell_wls_child_cluster | -0.021 | -0.033 | -0.009 | 8.91e-04 | PASS |  |
| all79_descriptive | B1_random_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.270 | 0.150 | 0.391 | 1.05e-05 | PASS |  |
| all79_descriptive | B2_unigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.043 | 9.60e-04 | 0.085 | 0.045 | PASS |  |
| all79_descriptive | B3_bigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.037 | -0.001 | 0.074 | 0.057 | PASS |  |
| all79_descriptive | B4_trigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.040 | 0.005 | 0.075 | 0.026 | PASS |  |

## Leave-One-Child And Leave-One-Corpus Influence

| scope | model_id | outcome | drop_level | drop_id | remaining_children | observed_age_estimate | leave_out_age_estimate | change_from_observed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Brown/Adam | 20.000 | -0.131 | -0.116 | 0.015 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Brown/Eve | 20.000 | -0.131 | -0.129 | 0.002 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Brown/Sarah | 20.000 | -0.131 | -0.139 | -0.008 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Anne | 20.000 | -0.131 | -0.130 | 0.001 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Aran | 20.000 | -0.131 | -0.126 | 0.006 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Becky | 20.000 | -0.131 | -0.131 | 6.96e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Carl | 20.000 | -0.131 | -0.132 | -6.26e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Dominic | 20.000 | -0.131 | -0.131 | -2.01e-05 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Gail | 20.000 | -0.131 | -0.128 | 0.003 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Joel | 20.000 | -0.131 | -0.131 | 4.22e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/John | 20.000 | -0.131 | -0.130 | 0.002 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Liz | 20.000 | -0.131 | -0.129 | 0.002 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Nicole | 20.000 | -0.131 | -0.131 | 6.32e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Ruth | 20.000 | -0.131 | -0.124 | 0.007 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Warren | 20.000 | -0.131 | -0.130 | 0.001 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Alex | 20.000 | -0.131 | -0.141 | -0.009 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Ethan | 20.000 | -0.131 | -0.136 | -0.005 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Lily | 20.000 | -0.131 | -0.141 | -0.010 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Naima | 20.000 | -0.131 | -0.128 | 0.003 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Violet | 20.000 | -0.131 | -0.139 | -0.008 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/William | 20.000 | -0.131 | -0.137 | -0.006 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | corpus | Brown | 18.000 | -0.131 | -0.119 | 0.012 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | corpus | Manchester | 9.000 | -0.131 | -0.104 | 0.028 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | corpus | Providence | 15.000 | -0.131 | -0.181 | -0.050 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Adam | 20.000 | -0.162 | -0.140 | 0.021 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Eve | 20.000 | -0.162 | -0.159 | 0.003 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Sarah | 20.000 | -0.162 | -0.167 | -0.005 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Anne | 20.000 | -0.162 | -0.160 | 0.001 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Aran | 20.000 | -0.162 | -0.160 | 0.001 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Becky | 20.000 | -0.162 | -0.161 | 7.04e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Carl | 20.000 | -0.162 | -0.158 | 0.003 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Dominic | 20.000 | -0.162 | -0.161 | 0.001 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Gail | 20.000 | -0.162 | -0.160 | 0.001 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Joel | 20.000 | -0.162 | -0.162 | -2.11e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/John | 20.000 | -0.162 | -0.161 | 4.92e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Liz | 20.000 | -0.162 | -0.161 | 3.49e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Nicole | 20.000 | -0.162 | -0.162 | -7.36e-05 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Ruth | 20.000 | -0.162 | -0.159 | 0.003 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Warren | 20.000 | -0.162 | -0.161 | 9.72e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Alex | 20.000 | -0.162 | -0.173 | -0.012 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Ethan | 20.000 | -0.162 | -0.167 | -0.006 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Lily | 20.000 | -0.162 | -0.169 | -0.008 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Naima | 20.000 | -0.162 | -0.156 | 0.006 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Violet | 20.000 | -0.162 | -0.168 | -0.006 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/William | 20.000 | -0.162 | -0.166 | -0.005 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | corpus | Brown | 18.000 | -0.162 | -0.136 | 0.026 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | corpus | Manchester | 9.000 | -0.162 | -0.147 | 0.015 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | corpus | Providence | 15.000 | -0.162 | -0.206 | -0.045 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Adam | 20.000 | -0.030 | -0.024 | 0.006 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Eve | 20.000 | -0.030 | -0.030 | 6.59e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Sarah | 20.000 | -0.030 | -0.028 | 0.003 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Anne | 20.000 | -0.030 | -0.031 | -2.80e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Aran | 20.000 | -0.030 | -0.035 | -0.004 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Becky | 20.000 | -0.030 | -0.030 | 8.99e-06 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Carl | 20.000 | -0.030 | -0.027 | 0.004 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Dominic | 20.000 | -0.030 | -0.029 | 0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Gail | 20.000 | -0.030 | -0.032 | -0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Joel | 20.000 | -0.030 | -0.031 | -6.34e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/John | 20.000 | -0.030 | -0.032 | -0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Liz | 20.000 | -0.030 | -0.033 | -0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Nicole | 20.000 | -0.030 | -0.031 | -8.23e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Ruth | 20.000 | -0.030 | -0.034 | -0.004 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Warren | 20.000 | -0.030 | -0.031 | -3.14e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Alex | 20.000 | -0.030 | -0.033 | -0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Ethan | 20.000 | -0.030 | -0.032 | -0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Lily | 20.000 | -0.030 | -0.029 | 0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Naima | 20.000 | -0.030 | -0.028 | 0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Violet | 20.000 | -0.030 | -0.029 | 0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/William | 20.000 | -0.030 | -0.030 | 9.05e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | corpus | Brown | 18.000 | -0.030 | -0.016 | 0.014 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | corpus | Manchester | 9.000 | -0.030 | -0.043 | -0.013 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | corpus | Providence | 15.000 | -0.030 | -0.026 | 0.005 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Barbara | 57.000 | -0.062 | -0.062 | -7.31e-06 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Conor | 57.000 | -0.062 | -0.062 | 1.63e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Courtney | 57.000 | -0.062 | -0.062 | 1.27e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/David | 57.000 | -0.062 | -0.063 | -2.91e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/John | 57.000 | -0.062 | -0.063 | -2.70e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Michelle | 57.000 | -0.062 | -0.064 | -0.002 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Rachel | 57.000 | -0.062 | -0.062 | 2.46e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Stuart | 57.000 | -0.062 | -0.062 | 2.79e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Demetras1/Trevor | 57.000 | -0.062 | -0.057 | 0.006 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Forrester/Ella | 57.000 | -0.062 | -0.062 | 1.27e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Kuczaj/Abe | 57.000 | -0.062 | -0.062 | -1.20e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Lara/Lara | 57.000 | -0.062 | -0.059 | 0.003 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Eleanor | 57.000 | -0.062 | -0.064 | -0.001 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Fraser | 57.000 | -0.062 | -0.031 | 0.031 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Gina | 57.000 | -0.062 | -0.074 | -0.012 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Helen | 57.000 | -0.062 | -0.088 | -0.025 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Post/Lew | 57.000 | -0.062 | -0.062 | -4.30e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Post/She | 57.000 | -0.062 | -0.062 | 3.16e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Post/Tow | 57.000 | -0.062 | -0.062 | -1.03e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Sachs/Naomi | 57.000 | -0.062 | -0.066 | -0.004 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Weist/Ben | 57.000 | -0.062 | -0.062 | 6.94e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Weist/Emily | 57.000 | -0.062 | -0.062 | 6.31e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Weist/Emma | 57.000 | -0.062 | -0.064 | -0.001 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Weist/Jillian | 57.000 | -0.062 | -0.062 | 4.10e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Weist/Matt | 57.000 | -0.062 | -0.065 | -0.003 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Weist/Roman | 57.000 | -0.062 | -0.063 | -5.36e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Abigail | 57.000 | -0.062 | -0.062 | 5.61e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Benjamin | 57.000 | -0.062 | -0.062 | -2.12e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Betty | 57.000 | -0.062 | -0.062 | 2.10e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Darren | 57.000 | -0.062 | -0.063 | -0.001 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Debbie | 57.000 | -0.062 | -0.062 | 1.07e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Ellen | 57.000 | -0.062 | -0.062 | 4.37e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Elspeth | 57.000 | -0.062 | -0.062 | 6.23e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Frances | 57.000 | -0.062 | -0.063 | -3.81e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Gary | 57.000 | -0.062 | -0.063 | -3.66e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Gavin | 57.000 | -0.062 | -0.062 | 7.41e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Geoffrey | 57.000 | -0.062 | -0.062 | -1.38e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Gerald | 57.000 | -0.062 | -0.062 | 4.47e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Harriet | 57.000 | -0.062 | -0.063 | -4.12e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Iris | 57.000 | -0.062 | -0.063 | -4.11e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Jack | 57.000 | -0.062 | -0.062 | 2.89e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Jason | 57.000 | -0.062 | -0.062 | 3.39e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Jonathan | 57.000 | -0.062 | -0.063 | -7.76e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Laura | 57.000 | -0.062 | -0.062 | 1.10e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Lee | 57.000 | -0.062 | -0.062 | 2.98e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Martin | 57.000 | -0.062 | -0.062 | 2.58e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Nancy | 57.000 | -0.062 | -0.062 | 1.77e-07 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Neil | 57.000 | -0.062 | -0.062 | 9.88e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Neville | 57.000 | -0.062 | -0.062 | 2.24e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Olivia | 57.000 | -0.062 | -0.062 | 9.47e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Penny | 57.000 | -0.062 | -0.062 | 3.68e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Rosie | 57.000 | -0.062 | -0.062 | 5.56e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Samantha | 57.000 | -0.062 | -0.062 | -3.65e-06 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Sean | 57.000 | -0.062 | -0.062 | -1.00e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Sheila | 57.000 | -0.062 | -0.063 | -2.92e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Simon | 57.000 | -0.062 | -0.062 | 6.39e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Stella | 57.000 | -0.062 | -0.062 | 3.63e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | child | Wells/Tony | 57.000 | -0.062 | -0.062 | 2.15e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Belfast | 50.000 | -0.062 | -0.064 | -0.002 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Demetras1 | 57.000 | -0.062 | -0.057 | 0.006 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Forrester | 57.000 | -0.062 | -0.062 | 1.27e-05 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Kuczaj | 57.000 | -0.062 | -0.062 | -1.20e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Lara | 57.000 | -0.062 | -0.059 | 0.003 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | MPI-EVA-Manchester | 54.000 | -0.062 | -0.068 | -0.006 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Post | 55.000 | -0.062 | -0.062 | 1.71e-04 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Sachs | 57.000 | -0.062 | -0.066 | -0.004 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Weist | 52.000 | -0.062 | -0.066 | -0.004 |
| non_pbm_confirmation | P1_k3_contextual | real_k3_sum_bits | corpus | Wells | 26.000 | -0.062 | -0.062 | 4.04e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Barbara | 57.000 | -0.089 | -0.089 | 2.18e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Conor | 57.000 | -0.089 | -0.089 | 4.30e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Courtney | 57.000 | -0.089 | -0.089 | 3.42e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/David | 57.000 | -0.089 | -0.089 | 4.22e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/John | 57.000 | -0.089 | -0.089 | -2.74e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Michelle | 57.000 | -0.089 | -0.090 | -9.40e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Rachel | 57.000 | -0.089 | -0.089 | 2.84e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Stuart | 57.000 | -0.089 | -0.089 | 1.22e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Demetras1/Trevor | 57.000 | -0.089 | -0.084 | 0.005 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Forrester/Ella | 57.000 | -0.089 | -0.090 | -8.63e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Kuczaj/Abe | 57.000 | -0.089 | -0.086 | 0.003 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Lara/Lara | 57.000 | -0.089 | -0.086 | 0.003 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Eleanor | 57.000 | -0.089 | -0.088 | 0.002 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Fraser | 57.000 | -0.089 | -0.066 | 0.023 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Gina | 57.000 | -0.089 | -0.099 | -0.010 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Helen | 57.000 | -0.089 | -0.111 | -0.022 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Post/Lew | 57.000 | -0.089 | -0.089 | -1.98e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Post/She | 57.000 | -0.089 | -0.089 | 3.95e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Post/Tow | 57.000 | -0.089 | -0.089 | -1.27e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Sachs/Naomi | 57.000 | -0.089 | -0.090 | -5.59e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Ben | 57.000 | -0.089 | -0.088 | 8.31e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Emily | 57.000 | -0.089 | -0.089 | -1.89e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Emma | 57.000 | -0.089 | -0.090 | -0.001 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Jillian | 57.000 | -0.089 | -0.089 | 5.29e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Matt | 57.000 | -0.089 | -0.092 | -0.003 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Roman | 57.000 | -0.089 | -0.093 | -0.003 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Abigail | 57.000 | -0.089 | -0.089 | 5.19e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Benjamin | 57.000 | -0.089 | -0.090 | -3.29e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Betty | 57.000 | -0.089 | -0.089 | 4.84e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Darren | 57.000 | -0.089 | -0.090 | -0.001 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Debbie | 57.000 | -0.089 | -0.089 | 5.24e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Ellen | 57.000 | -0.089 | -0.089 | 1.17e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Elspeth | 57.000 | -0.089 | -0.089 | 8.96e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Frances | 57.000 | -0.089 | -0.090 | -3.39e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Gary | 57.000 | -0.089 | -0.089 | -3.05e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Gavin | 57.000 | -0.089 | -0.089 | 2.47e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Geoffrey | 57.000 | -0.089 | -0.090 | -4.62e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Gerald | 57.000 | -0.089 | -0.089 | 2.50e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Harriet | 57.000 | -0.089 | -0.090 | -4.90e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Iris | 57.000 | -0.089 | -0.090 | -3.86e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Jack | 57.000 | -0.089 | -0.089 | 1.39e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Jason | 57.000 | -0.089 | -0.089 | -7.43e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Jonathan | 57.000 | -0.089 | -0.089 | 2.40e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Laura | 57.000 | -0.089 | -0.089 | 7.63e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Lee | 57.000 | -0.089 | -0.089 | 1.14e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Martin | 57.000 | -0.089 | -0.089 | 3.51e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Nancy | 57.000 | -0.089 | -0.089 | 2.51e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Neil | 57.000 | -0.089 | -0.089 | 1.25e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Neville | 57.000 | -0.089 | -0.089 | 1.59e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Olivia | 57.000 | -0.089 | -0.089 | -4.23e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Penny | 57.000 | -0.089 | -0.089 | 2.11e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Rosie | 57.000 | -0.089 | -0.089 | 1.09e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Samantha | 57.000 | -0.089 | -0.089 | 6.10e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Sean | 57.000 | -0.089 | -0.089 | -4.86e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Sheila | 57.000 | -0.089 | -0.089 | -2.69e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Simon | 57.000 | -0.089 | -0.089 | -3.54e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Stella | 57.000 | -0.089 | -0.089 | 2.83e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Tony | 57.000 | -0.089 | -0.089 | 2.33e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Belfast | 50.000 | -0.089 | -0.089 | -8.81e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Demetras1 | 57.000 | -0.089 | -0.084 | 0.005 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Forrester | 57.000 | -0.089 | -0.090 | -8.63e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Kuczaj | 57.000 | -0.089 | -0.086 | 0.003 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Lara | 57.000 | -0.089 | -0.086 | 0.003 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | MPI-EVA-Manchester | 54.000 | -0.089 | -0.096 | -0.007 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Post | 55.000 | -0.089 | -0.089 | 7.05e-05 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Sachs | 57.000 | -0.089 | -0.090 | -5.59e-04 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Weist | 52.000 | -0.089 | -0.096 | -0.007 |
| non_pbm_confirmation | P2_k0_unconditional | real_k0_sum_bits | corpus | Wells | 26.000 | -0.089 | -0.091 | -0.002 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Barbara | 57.000 | -0.028 | -0.028 | 2.39e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Conor | 57.000 | -0.028 | -0.028 | -1.35e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Courtney | 57.000 | -0.028 | -0.028 | -1.08e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/David | 57.000 | -0.028 | -0.027 | 2.80e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/John | 57.000 | -0.028 | -0.028 | -1.60e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Michelle | 57.000 | -0.028 | -0.027 | 8.28e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Rachel | 57.000 | -0.028 | -0.028 | 4.88e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Stuart | 57.000 | -0.028 | -0.028 | -2.37e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Demetras1/Trevor | 57.000 | -0.028 | -0.028 | -1.12e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Forrester/Ella | 57.000 | -0.028 | -0.029 | -0.001 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Kuczaj/Abe | 57.000 | -0.028 | -0.025 | 0.003 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Lara/Lara | 57.000 | -0.028 | -0.028 | -6.44e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Eleanor | 57.000 | -0.028 | -0.025 | 0.003 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Fraser | 57.000 | -0.028 | -0.035 | -0.008 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Gina | 57.000 | -0.028 | -0.026 | 0.001 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Helen | 57.000 | -0.028 | -0.026 | 0.002 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Post/Lew | 57.000 | -0.028 | -0.028 | -1.64e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Post/She | 57.000 | -0.028 | -0.028 | 9.83e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Post/Tow | 57.000 | -0.028 | -0.028 | -3.09e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Sachs/Naomi | 57.000 | -0.028 | -0.025 | 0.003 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Ben | 57.000 | -0.028 | -0.028 | 1.74e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Emily | 57.000 | -0.028 | -0.028 | 2.59e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Emma | 57.000 | -0.028 | -0.027 | 5.87e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Jillian | 57.000 | -0.028 | -0.028 | 1.54e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Matt | 57.000 | -0.028 | -0.028 | -1.35e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Roman | 57.000 | -0.028 | -0.030 | -0.002 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Abigail | 57.000 | -0.028 | -0.028 | -1.22e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Benjamin | 57.000 | -0.028 | -0.028 | -3.28e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Betty | 57.000 | -0.028 | -0.028 | 5.44e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Darren | 57.000 | -0.028 | -0.028 | -4.70e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Debbie | 57.000 | -0.028 | -0.028 | -7.48e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Ellen | 57.000 | -0.028 | -0.028 | -3.45e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Elspeth | 57.000 | -0.028 | -0.028 | -5.84e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Frances | 57.000 | -0.028 | -0.028 | 5.48e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Gary | 57.000 | -0.028 | -0.028 | 1.37e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Gavin | 57.000 | -0.028 | -0.028 | -5.17e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Geoffrey | 57.000 | -0.028 | -0.028 | -3.25e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Gerald | 57.000 | -0.028 | -0.028 | -1.77e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Harriet | 57.000 | -0.028 | -0.028 | -1.19e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Iris | 57.000 | -0.028 | -0.028 | 1.05e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Jack | 57.000 | -0.028 | -0.028 | -1.51e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Jason | 57.000 | -0.028 | -0.028 | -4.11e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Jonathan | 57.000 | -0.028 | -0.027 | 7.84e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Laura | 57.000 | -0.028 | -0.028 | -2.96e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Lee | 57.000 | -0.028 | -0.028 | -2.64e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Martin | 57.000 | -0.028 | -0.028 | 1.38e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Nancy | 57.000 | -0.028 | -0.028 | 3.78e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Neil | 57.000 | -0.028 | -0.028 | 1.95e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Neville | 57.000 | -0.028 | -0.028 | -5.67e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Olivia | 57.000 | -0.028 | -0.028 | -1.58e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Penny | 57.000 | -0.028 | -0.028 | -1.49e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Rosie | 57.000 | -0.028 | -0.028 | -4.88e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Samantha | 57.000 | -0.028 | -0.028 | 6.58e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Sean | 57.000 | -0.028 | -0.028 | -3.28e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Sheila | 57.000 | -0.028 | -0.028 | 3.72e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Simon | 57.000 | -0.028 | -0.028 | -8.30e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Stella | 57.000 | -0.028 | -0.028 | -1.84e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Tony | 57.000 | -0.028 | -0.028 | 2.60e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Belfast | 50.000 | -0.028 | -0.027 | 9.03e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Demetras1 | 57.000 | -0.028 | -0.028 | -1.12e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Forrester | 57.000 | -0.028 | -0.029 | -0.001 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Kuczaj | 57.000 | -0.028 | -0.025 | 0.003 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Lara | 57.000 | -0.028 | -0.028 | -6.44e-04 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | MPI-EVA-Manchester | 54.000 | -0.028 | -0.030 | -0.002 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Post | 55.000 | -0.028 | -0.028 | -9.62e-05 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Sachs | 57.000 | -0.028 | -0.025 | 0.003 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Weist | 52.000 | -0.028 | -0.029 | -0.001 |
| non_pbm_confirmation | P3_k3_context_gain | real_context_gain_k3 | corpus | Wells | 26.000 | -0.028 | -0.031 | -0.003 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Barbara | 78.000 | -0.080 | -0.080 | -6.21e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Conor | 78.000 | -0.080 | -0.080 | 9.07e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Courtney | 78.000 | -0.080 | -0.080 | 7.90e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/David | 78.000 | -0.080 | -0.080 | -1.88e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/John | 78.000 | -0.080 | -0.080 | -2.19e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Michelle | 78.000 | -0.080 | -0.081 | -0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Rachel | 78.000 | -0.080 | -0.079 | 1.85e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Belfast/Stuart | 78.000 | -0.080 | -0.080 | 1.59e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Brown/Adam | 78.000 | -0.080 | -0.073 | 0.006 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Brown/Eve | 78.000 | -0.080 | -0.079 | 7.74e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Brown/Sarah | 78.000 | -0.080 | -0.079 | 1.79e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Demetras1/Trevor | 78.000 | -0.080 | -0.076 | 0.004 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Forrester/Ella | 78.000 | -0.080 | -0.079 | 2.10e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Kuczaj/Abe | 78.000 | -0.080 | -0.081 | -0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Lara/Lara | 78.000 | -0.080 | -0.078 | 0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Eleanor | 78.000 | -0.080 | -0.082 | -0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Fraser | 78.000 | -0.080 | -0.061 | 0.019 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Gina | 78.000 | -0.080 | -0.090 | -0.010 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | MPI-EVA-Manchester/Helen | 78.000 | -0.080 | -0.102 | -0.022 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Anne | 78.000 | -0.080 | -0.079 | 8.77e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Aran | 78.000 | -0.080 | -0.077 | 0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Becky | 78.000 | -0.080 | -0.079 | 7.36e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Carl | 78.000 | -0.080 | -0.079 | 1.97e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Dominic | 78.000 | -0.080 | -0.080 | -4.12e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Gail | 78.000 | -0.080 | -0.079 | 0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Joel | 78.000 | -0.080 | -0.079 | 5.86e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/John | 78.000 | -0.080 | -0.079 | 8.37e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Liz | 78.000 | -0.080 | -0.078 | 0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Nicole | 78.000 | -0.080 | -0.080 | 1.21e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Ruth | 78.000 | -0.080 | -0.078 | 0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Warren | 78.000 | -0.080 | -0.079 | 7.26e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Post/Lew | 78.000 | -0.080 | -0.080 | -4.00e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Post/She | 78.000 | -0.080 | -0.079 | 2.08e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Post/Tow | 78.000 | -0.080 | -0.080 | -7.21e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Providence/Alex | 78.000 | -0.080 | -0.082 | -0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Providence/Ethan | 78.000 | -0.080 | -0.081 | -8.54e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Providence/Lily | 78.000 | -0.080 | -0.081 | -9.30e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Providence/Naima | 78.000 | -0.080 | -0.077 | 0.003 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Providence/Violet | 78.000 | -0.080 | -0.081 | -0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Providence/William | 78.000 | -0.080 | -0.081 | -0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Sachs/Naomi | 78.000 | -0.080 | -0.082 | -0.003 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Weist/Ben | 78.000 | -0.080 | -0.079 | 4.92e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Weist/Emily | 78.000 | -0.080 | -0.080 | 4.66e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Weist/Emma | 78.000 | -0.080 | -0.081 | -0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Weist/Jillian | 78.000 | -0.080 | -0.079 | 2.96e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Weist/Matt | 78.000 | -0.080 | -0.082 | -0.003 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Weist/Roman | 78.000 | -0.080 | -0.080 | -4.48e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Abigail | 78.000 | -0.080 | -0.080 | 1.01e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Benjamin | 78.000 | -0.080 | -0.080 | -6.25e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Betty | 78.000 | -0.080 | -0.080 | 1.47e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Darren | 78.000 | -0.080 | -0.080 | -7.04e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Debbie | 78.000 | -0.080 | -0.080 | 3.50e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Ellen | 78.000 | -0.080 | -0.079 | 2.77e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Elspeth | 78.000 | -0.080 | -0.079 | 3.51e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Frances | 78.000 | -0.080 | -0.080 | -3.05e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Gary | 78.000 | -0.080 | -0.080 | -3.08e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Gavin | 78.000 | -0.080 | -0.079 | 4.13e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Geoffrey | 78.000 | -0.080 | -0.080 | -1.65e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Gerald | 78.000 | -0.080 | -0.079 | 2.27e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Harriet | 78.000 | -0.080 | -0.080 | -2.89e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Iris | 78.000 | -0.080 | -0.080 | -3.14e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Jack | 78.000 | -0.080 | -0.080 | 1.58e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Jason | 78.000 | -0.080 | -0.079 | 1.90e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Jonathan | 78.000 | -0.080 | -0.080 | -6.06e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Laura | 78.000 | -0.080 | -0.080 | 7.13e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Lee | 78.000 | -0.080 | -0.080 | 1.71e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Martin | 78.000 | -0.080 | -0.080 | 1.40e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Nancy | 78.000 | -0.080 | -0.080 | -2.57e-06 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Neil | 78.000 | -0.080 | -0.080 | 6.53e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Neville | 78.000 | -0.080 | -0.080 | 1.41e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Olivia | 78.000 | -0.080 | -0.080 | 5.83e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Penny | 78.000 | -0.080 | -0.080 | 2.10e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Rosie | 78.000 | -0.080 | -0.080 | 3.68e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Samantha | 78.000 | -0.080 | -0.080 | -1.23e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Sean | 78.000 | -0.080 | -0.080 | -1.16e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Sheila | 78.000 | -0.080 | -0.080 | -1.94e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Simon | 78.000 | -0.080 | -0.080 | 3.75e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Stella | 78.000 | -0.080 | -0.080 | 1.81e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | child | Wells/Tony | 78.000 | -0.080 | -0.080 | 1.43e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Belfast | 71.000 | -0.080 | -0.081 | -0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Brown | 76.000 | -0.080 | -0.072 | 0.008 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Demetras1 | 78.000 | -0.080 | -0.076 | 0.004 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Forrester | 78.000 | -0.080 | -0.079 | 2.10e-04 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Kuczaj | 78.000 | -0.080 | -0.081 | -0.001 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Lara | 78.000 | -0.080 | -0.078 | 0.002 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | MPI-EVA-Manchester | 75.000 | -0.080 | -0.101 | -0.021 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Manchester | 67.000 | -0.080 | -0.068 | 0.011 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Post | 76.000 | -0.080 | -0.080 | 9.60e-05 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Providence | 73.000 | -0.080 | -0.084 | -0.005 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Sachs | 78.000 | -0.080 | -0.082 | -0.003 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Weist | 73.000 | -0.080 | -0.083 | -0.003 |
| all79_descriptive | P1_k3_contextual | real_k3_sum_bits | corpus | Wells | 47.000 | -0.080 | -0.080 | -5.97e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Barbara | 78.000 | -0.108 | -0.107 | 7.03e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Conor | 78.000 | -0.108 | -0.108 | -3.78e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Courtney | 78.000 | -0.108 | -0.108 | 8.57e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/David | 78.000 | -0.108 | -0.107 | 2.55e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/John | 78.000 | -0.108 | -0.108 | -2.35e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Michelle | 78.000 | -0.108 | -0.108 | -7.12e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Rachel | 78.000 | -0.108 | -0.107 | 2.16e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Belfast/Stuart | 78.000 | -0.108 | -0.107 | 3.70e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Adam | 78.000 | -0.108 | -0.099 | 0.008 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Eve | 78.000 | -0.108 | -0.107 | 9.22e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Sarah | 78.000 | -0.108 | -0.106 | 0.001 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Demetras1/Trevor | 78.000 | -0.108 | -0.104 | 0.004 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Forrester/Ella | 78.000 | -0.108 | -0.108 | -2.77e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Kuczaj/Abe | 78.000 | -0.108 | -0.107 | 2.66e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Lara/Lara | 78.000 | -0.108 | -0.106 | 0.001 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Eleanor | 78.000 | -0.108 | -0.108 | -4.23e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Fraser | 78.000 | -0.108 | -0.093 | 0.014 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Gina | 78.000 | -0.108 | -0.117 | -0.009 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | MPI-EVA-Manchester/Helen | 78.000 | -0.108 | -0.128 | -0.020 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Anne | 78.000 | -0.108 | -0.107 | 7.37e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Aran | 78.000 | -0.108 | -0.107 | 8.55e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Becky | 78.000 | -0.108 | -0.107 | 8.46e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Carl | 78.000 | -0.108 | -0.106 | 0.001 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Dominic | 78.000 | -0.108 | -0.107 | 2.80e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Gail | 78.000 | -0.108 | -0.107 | 6.98e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Joel | 78.000 | -0.108 | -0.107 | 3.65e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/John | 78.000 | -0.108 | -0.107 | 5.08e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Liz | 78.000 | -0.108 | -0.107 | 6.02e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Nicole | 78.000 | -0.108 | -0.108 | -1.34e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Ruth | 78.000 | -0.108 | -0.107 | 6.92e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Warren | 78.000 | -0.108 | -0.107 | 5.54e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Post/Lew | 78.000 | -0.108 | -0.108 | -1.41e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Post/She | 78.000 | -0.108 | -0.107 | 2.58e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Post/Tow | 78.000 | -0.108 | -0.108 | -1.04e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Alex | 78.000 | -0.108 | -0.110 | -0.003 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Ethan | 78.000 | -0.108 | -0.109 | -0.001 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Lily | 78.000 | -0.108 | -0.108 | -4.11e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Naima | 78.000 | -0.108 | -0.105 | 0.003 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Violet | 78.000 | -0.108 | -0.109 | -0.001 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Providence/William | 78.000 | -0.108 | -0.108 | -7.59e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Sachs/Naomi | 78.000 | -0.108 | -0.108 | -8.74e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Ben | 78.000 | -0.108 | -0.107 | 6.00e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Emily | 78.000 | -0.108 | -0.108 | -2.17e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Emma | 78.000 | -0.108 | -0.108 | -9.51e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Jillian | 78.000 | -0.108 | -0.107 | 3.50e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Matt | 78.000 | -0.108 | -0.110 | -0.002 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Weist/Roman | 78.000 | -0.108 | -0.110 | -0.002 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Abigail | 78.000 | -0.108 | -0.108 | -4.05e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Benjamin | 78.000 | -0.108 | -0.108 | -2.77e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Betty | 78.000 | -0.108 | -0.107 | 2.64e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Darren | 78.000 | -0.108 | -0.108 | -7.10e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Debbie | 78.000 | -0.108 | -0.108 | -1.53e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Ellen | 78.000 | -0.108 | -0.108 | -8.55e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Elspeth | 78.000 | -0.108 | -0.108 | -7.54e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Frances | 78.000 | -0.108 | -0.108 | -2.82e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Gary | 78.000 | -0.108 | -0.108 | -2.76e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Gavin | 78.000 | -0.108 | -0.107 | 8.24e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Geoffrey | 78.000 | -0.108 | -0.108 | -3.96e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Gerald | 78.000 | -0.108 | -0.107 | 8.98e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Harriet | 78.000 | -0.108 | -0.108 | -3.51e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Iris | 78.000 | -0.108 | -0.108 | -3.02e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Jack | 78.000 | -0.108 | -0.107 | 6.31e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Jason | 78.000 | -0.108 | -0.108 | -8.31e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Jonathan | 78.000 | -0.108 | -0.108 | -7.70e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Laura | 78.000 | -0.108 | -0.107 | 4.75e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Lee | 78.000 | -0.108 | -0.108 | 5.33e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Martin | 78.000 | -0.108 | -0.107 | 1.79e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Nancy | 78.000 | -0.108 | -0.107 | 1.38e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Neil | 78.000 | -0.108 | -0.107 | 8.27e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Neville | 78.000 | -0.108 | -0.107 | 9.76e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Olivia | 78.000 | -0.108 | -0.108 | -3.83e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Penny | 78.000 | -0.108 | -0.108 | 8.41e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Rosie | 78.000 | -0.108 | -0.108 | 7.50e-06 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Samantha | 78.000 | -0.108 | -0.107 | 2.79e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Sean | 78.000 | -0.108 | -0.108 | -3.80e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Sheila | 78.000 | -0.108 | -0.108 | -1.81e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Simon | 78.000 | -0.108 | -0.108 | -2.77e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Stella | 78.000 | -0.108 | -0.107 | 1.41e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | child | Wells/Tony | 78.000 | -0.108 | -0.107 | 1.57e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Belfast | 71.000 | -0.108 | -0.108 | -3.67e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Brown | 76.000 | -0.108 | -0.096 | 0.011 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Demetras1 | 78.000 | -0.108 | -0.104 | 0.004 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Forrester | 78.000 | -0.108 | -0.108 | -2.77e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Kuczaj | 78.000 | -0.108 | -0.107 | 2.66e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Lara | 78.000 | -0.108 | -0.106 | 0.001 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | MPI-EVA-Manchester | 75.000 | -0.108 | -0.129 | -0.022 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Manchester | 67.000 | -0.108 | -0.100 | 0.008 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Post | 76.000 | -0.108 | -0.107 | 1.28e-05 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Providence | 73.000 | -0.108 | -0.112 | -0.004 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Sachs | 78.000 | -0.108 | -0.108 | -8.74e-04 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Weist | 73.000 | -0.108 | -0.113 | -0.005 |
| all79_descriptive | P2_k0_unconditional | real_k0_sum_bits | corpus | Wells | 47.000 | -0.108 | -0.110 | -0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Barbara | 78.000 | -0.029 | -0.029 | 1.38e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Conor | 78.000 | -0.029 | -0.029 | -1.04e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Courtney | 78.000 | -0.029 | -0.029 | -8.17e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/David | 78.000 | -0.029 | -0.029 | 1.71e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/John | 78.000 | -0.029 | -0.029 | -2.42e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Michelle | 78.000 | -0.029 | -0.028 | 5.29e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Rachel | 78.000 | -0.029 | -0.029 | 3.72e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Belfast/Stuart | 78.000 | -0.029 | -0.029 | -1.76e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Adam | 78.000 | -0.029 | -0.027 | 0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Eve | 78.000 | -0.029 | -0.029 | 1.69e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Sarah | 78.000 | -0.029 | -0.028 | 0.001 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Demetras1/Trevor | 78.000 | -0.029 | -0.029 | -2.94e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Forrester/Ella | 78.000 | -0.029 | -0.029 | -5.45e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Kuczaj/Abe | 78.000 | -0.029 | -0.027 | 0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Lara/Lara | 78.000 | -0.029 | -0.029 | -5.58e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Eleanor | 78.000 | -0.029 | -0.027 | 0.001 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Fraser | 78.000 | -0.029 | -0.033 | -0.004 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Gina | 78.000 | -0.029 | -0.028 | 5.37e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | MPI-EVA-Manchester/Helen | 78.000 | -0.029 | -0.028 | 7.86e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Anne | 78.000 | -0.029 | -0.029 | -1.20e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Aran | 78.000 | -0.029 | -0.030 | -0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Becky | 78.000 | -0.029 | -0.029 | 1.31e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Carl | 78.000 | -0.029 | -0.027 | 0.001 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Dominic | 78.000 | -0.029 | -0.028 | 3.26e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Gail | 78.000 | -0.029 | -0.029 | -3.71e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Joel | 78.000 | -0.029 | -0.029 | -2.13e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/John | 78.000 | -0.029 | -0.029 | -3.07e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Liz | 78.000 | -0.029 | -0.029 | -5.88e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Nicole | 78.000 | -0.029 | -0.029 | -1.72e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Ruth | 78.000 | -0.029 | -0.030 | -0.001 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Warren | 78.000 | -0.029 | -0.029 | -1.59e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Post/Lew | 78.000 | -0.029 | -0.029 | -1.06e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Post/She | 78.000 | -0.029 | -0.029 | 6.00e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Post/Tow | 78.000 | -0.029 | -0.029 | -3.60e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Alex | 78.000 | -0.029 | -0.029 | -7.45e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Ethan | 78.000 | -0.029 | -0.029 | -5.21e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Lily | 78.000 | -0.029 | -0.028 | 4.72e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Naima | 78.000 | -0.029 | -0.028 | 3.92e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Violet | 78.000 | -0.029 | -0.028 | 5.61e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Providence/William | 78.000 | -0.029 | -0.028 | 2.76e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Sachs/Naomi | 78.000 | -0.029 | -0.027 | 0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Ben | 78.000 | -0.029 | -0.029 | 1.32e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Emily | 78.000 | -0.029 | -0.029 | 1.53e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Emma | 78.000 | -0.029 | -0.028 | 3.69e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Jillian | 78.000 | -0.029 | -0.029 | 7.98e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Matt | 78.000 | -0.029 | -0.029 | 3.80e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Weist/Roman | 78.000 | -0.029 | -0.030 | -0.001 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Abigail | 78.000 | -0.029 | -0.029 | -1.87e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Benjamin | 78.000 | -0.029 | -0.029 | -2.25e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Betty | 78.000 | -0.029 | -0.029 | 3.52e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Darren | 78.000 | -0.029 | -0.029 | -3.58e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Debbie | 78.000 | -0.029 | -0.029 | -5.25e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Ellen | 78.000 | -0.029 | -0.029 | -2.33e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Elspeth | 78.000 | -0.029 | -0.029 | -3.95e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Frances | 78.000 | -0.029 | -0.029 | 3.37e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Gary | 78.000 | -0.029 | -0.029 | 3.49e-06 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Gavin | 78.000 | -0.029 | -0.029 | -3.49e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Geoffrey | 78.000 | -0.029 | -0.029 | -2.27e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Gerald | 78.000 | -0.029 | -0.029 | -1.19e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Harriet | 78.000 | -0.029 | -0.029 | -8.18e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Iris | 78.000 | -0.029 | -0.029 | 5.52e-06 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Jack | 78.000 | -0.029 | -0.029 | -9.64e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Jason | 78.000 | -0.029 | -0.029 | -2.71e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Jonathan | 78.000 | -0.029 | -0.028 | 5.17e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Laura | 78.000 | -0.029 | -0.029 | -2.08e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Lee | 78.000 | -0.029 | -0.029 | -1.68e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Martin | 78.000 | -0.029 | -0.029 | 7.23e-06 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Nancy | 78.000 | -0.029 | -0.029 | 2.44e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Neil | 78.000 | -0.029 | -0.029 | 1.22e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Neville | 78.000 | -0.029 | -0.029 | -3.96e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Olivia | 78.000 | -0.029 | -0.029 | -1.10e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Penny | 78.000 | -0.029 | -0.029 | -1.24e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Rosie | 78.000 | -0.029 | -0.029 | -3.18e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Samantha | 78.000 | -0.029 | -0.029 | 4.04e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Sean | 78.000 | -0.029 | -0.029 | -2.23e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Sheila | 78.000 | -0.029 | -0.029 | 2.53e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Simon | 78.000 | -0.029 | -0.029 | -5.38e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Stella | 78.000 | -0.029 | -0.029 | -1.13e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | child | Wells/Tony | 78.000 | -0.029 | -0.029 | 1.72e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Belfast | 71.000 | -0.029 | -0.028 | 4.88e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Brown | 76.000 | -0.029 | -0.025 | 0.004 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Demetras1 | 78.000 | -0.029 | -0.029 | -2.94e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Forrester | 78.000 | -0.029 | -0.029 | -5.45e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Kuczaj | 78.000 | -0.029 | -0.027 | 0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Lara | 78.000 | -0.029 | -0.029 | -5.58e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | MPI-EVA-Manchester | 75.000 | -0.029 | -0.030 | -0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Manchester | 67.000 | -0.029 | -0.032 | -0.003 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Post | 76.000 | -0.029 | -0.029 | -8.16e-05 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Providence | 73.000 | -0.029 | -0.028 | 3.52e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Sachs | 78.000 | -0.029 | -0.027 | 0.002 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Weist | 73.000 | -0.029 | -0.029 | -6.62e-04 |
| all79_descriptive | P3_k3_context_gain | real_context_gain_k3 | corpus | Wells | 47.000 | -0.029 | -0.031 | -0.002 |

## Individual Child Trajectories

Point size reflects the number of utterances in the child-session-age cell. Adjusted outcomes remove the fitted exact/top-coded word-count effect and put every observation on the two-word reference scale. A child line is drawn only when the support rule is met (at least three distinct ages, six months of span, and 100 utterances).

| scope | dataset | child_id | distinct_ages | age_span | utterances | slope_supported | adjusted_k3_bits_2_words_slope_per_month | adjusted_context_gain_k3_2_words_slope_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | Brown | Adam | 55.000 | 35.267 | 45734.000 | 1.000 | -0.149 | -0.054 |
| pbm_discovery | Brown | Eve | 10.000 | 9.000 | 11676.000 | 1.000 | -0.293 | -0.078 |
| pbm_discovery | Brown | Sarah | 135.000 | 34.033 | 33625.000 | 1.000 | -0.088 | -0.050 |
| pbm_discovery | Manchester | Anne | 35.000 | 11.100 | 20693.000 | 1.000 | -0.289 | 0.008 |
| pbm_discovery | Manchester | Aran | 33.000 | 11.533 | 17565.000 | 1.000 | -0.692 | 0.330 |
| pbm_discovery | Manchester | Becky | 34.000 | 11.267 | 24407.000 | 1.000 | -0.256 | -0.083 |
| pbm_discovery | Manchester | Carl | 33.000 | 11.767 | 25620.000 | 1.000 | -0.119 | -0.203 |
| pbm_discovery | Manchester | Dominic | 35.000 | 11.700 | 21919.000 | 1.000 | 0.012 | -0.092 |
| pbm_discovery | Manchester | Gail | 34.000 | 11.500 | 17271.000 | 1.000 | -0.305 | 0.010 |
| pbm_discovery | Manchester | Joel | 35.000 | 11.334 | 18696.000 | 1.000 | -0.298 | 0.023 |
| pbm_discovery | Manchester | John | 32.000 | 11.300 | 13694.000 | 1.000 | -0.389 | 0.029 |
| pbm_discovery | Manchester | Liz | 34.000 | 11.300 | 16657.000 | 1.000 | -0.532 | 0.084 |
| pbm_discovery | Manchester | Nicole | 32.000 | 11.500 | 17152.000 | 1.000 | -0.029 | -0.027 |
| pbm_discovery | Manchester | Ruth | 33.000 | 12.200 | 20817.000 | 1.000 | -0.285 | 0.180 |
| pbm_discovery | Manchester | Warren | 36.000 | 11.467 | 17151.000 | 1.000 | -0.256 | 0.040 |
| pbm_discovery | Providence | Alex | 51.000 | 24.633 | 19090.000 | 1.000 | 0.033 | 0.020 |
| pbm_discovery | Providence | Ethan | 50.000 | 23.900 | 13588.000 | 1.000 | -0.068 | 0.024 |
| pbm_discovery | Providence | Lily | 77.000 | 35.000 | 28000.000 | 1.000 | -0.078 | -0.038 |
| pbm_discovery | Providence | Naima | 87.000 | 34.466 | 34215.000 | 1.000 | -0.162 | -0.017 |
| pbm_discovery | Providence | Violet | 49.000 | 33.800 | 10788.000 | 1.000 | 0.031 | -0.081 |
| pbm_discovery | Providence | William | 44.000 | 24.200 | 15967.000 | 1.000 | -0.051 | -0.048 |
| non_pbm_confirmation | Belfast | Barbara | 14.000 | 21.300 | 2873.000 | 1.000 | -0.049 | -0.112 |
| non_pbm_confirmation | Belfast | Conor | 13.000 | 9.700 | 3458.000 | 1.000 | -0.098 | 0.059 |
| non_pbm_confirmation | Belfast | Courtney | 7.000 | 8.367 | 2280.000 | 1.000 | -0.095 | 0.085 |
| non_pbm_confirmation | Belfast | David | 12.000 | 23.267 | 1897.000 | 1.000 | 0.026 | -0.109 |
| non_pbm_confirmation | Belfast | John | 7.000 | 10.066 | 1988.000 | 1.000 | 0.265 | -0.074 |
| non_pbm_confirmation | Belfast | Michelle | 14.000 | 23.700 | 3490.000 | 1.000 | 0.236 | -0.166 |
| non_pbm_confirmation | Belfast | Rachel | 9.000 | 8.267 | 1604.000 | 1.000 | -0.383 | -0.111 |
| non_pbm_confirmation | Belfast | Stuart | 10.000 | 11.733 | 3820.000 | 1.000 | -0.184 | 0.079 |
| non_pbm_confirmation | Demetras1 | Trevor | 25.000 | 23.000 | 6802.000 | 1.000 | -0.436 | -7.39e-04 |
| non_pbm_confirmation | Forrester | Ella | 34.000 | 47.967 | 6590.000 | 1.000 | -0.003 | 0.048 |
| non_pbm_confirmation | Kuczaj | Abe | 207.000 | 31.567 | 36873.000 | 1.000 | -0.074 | -0.067 |
| non_pbm_confirmation | Lara | Lara | 117.000 | 18.400 | 48364.000 | 1.000 | -0.206 | -0.020 |
| non_pbm_confirmation | MPI-EVA-Manchester | Eleanor | 107.000 | 12.933 | 85004.000 | 1.000 | -0.024 | -0.092 |
| non_pbm_confirmation | MPI-EVA-Manchester | Fraser | 107.000 | 13.067 | 149932.000 | 1.000 | -0.321 | 0.059 |
| non_pbm_confirmation | MPI-EVA-Manchester | Gina | 118.000 | 19.934 | 71593.000 | 1.000 | 0.030 | -0.054 |
| non_pbm_confirmation | MPI-EVA-Manchester | Helen | 181.000 | 25.566 | 154078.000 | 1.000 | -0.018 | -0.033 |
| non_pbm_confirmation | Post | Lew | 10.000 | 9.566 | 2439.000 | 1.000 | -0.041 | 0.178 |
| non_pbm_confirmation | Post | She | 10.000 | 9.667 | 2599.000 | 1.000 | -0.376 | -0.147 |
| non_pbm_confirmation | Post | Tow | 10.000 | 9.933 | 2988.000 | 1.000 | 0.053 | -0.041 |
| non_pbm_confirmation | Sachs | Naomi | 92.000 | 42.133 | 16021.000 | 1.000 | -0.004 | -0.083 |
| non_pbm_confirmation | Weist | Ben | 11.000 | 11.500 | 3340.000 | 1.000 | -0.275 | -0.090 |
| non_pbm_confirmation | Weist | Emily | 3.000 | 6.567 | 759.000 | 1.000 | -0.244 | -0.319 |
| non_pbm_confirmation | Weist | Emma | 26.000 | 21.333 | 6069.000 | 1.000 | 0.139 | -0.112 |
| non_pbm_confirmation | Weist | Jillian | 22.000 | 8.967 | 5467.000 | 1.000 | -0.091 | -0.270 |
| non_pbm_confirmation | Weist | Matt | 57.000 | 32.834 | 11093.000 | 1.000 | 0.019 | -0.003 |
| non_pbm_confirmation | Weist | Roman | 40.000 | 29.000 | 10583.000 | 1.000 | 0.009 | 0.049 |
| non_pbm_confirmation | Wells | Abigail | 10.000 | 38.067 | 1116.000 | 1.000 | -0.070 | -0.030 |
| non_pbm_confirmation | Wells | Benjamin | 10.000 | 43.100 | 1435.000 | 1.000 | -0.057 | 0.018 |
| non_pbm_confirmation | Wells | Betty | 8.000 | 20.967 | 1660.000 | 1.000 | -0.125 | -0.059 |
| non_pbm_confirmation | Wells | Darren | 10.000 | 40.133 | 1561.000 | 1.000 | 0.073 | -0.025 |
| non_pbm_confirmation | Wells | Debbie | 10.000 | 29.633 | 1381.000 | 1.000 | -0.104 | -0.007 |
| non_pbm_confirmation | Wells | Ellen | 9.000 | 24.166 | 2092.000 | 1.000 | -0.160 | 0.053 |
| non_pbm_confirmation | Wells | Elspeth | 10.000 | 42.100 | 1195.000 | 1.000 | -0.147 | 0.050 |
| non_pbm_confirmation | Wells | Frances | 10.000 | 40.234 | 1486.000 | 1.000 | -0.006 | -0.037 |
| non_pbm_confirmation | Wells | Gary | 10.000 | 39.000 | 1879.000 | 1.000 | -0.017 | -0.032 |
| non_pbm_confirmation | Wells | Gavin | 9.000 | 38.900 | 1739.000 | 1.000 | -0.139 | 0.029 |
| non_pbm_confirmation | Wells | Geoffrey | 9.000 | 41.733 | 1153.000 | 1.000 | -0.043 | 0.015 |
| non_pbm_confirmation | Wells | Gerald | 9.000 | 38.967 | 1554.000 | 1.000 | -0.117 | -0.005 |
| non_pbm_confirmation | Wells | Harriet | 10.000 | 40.033 | 1380.000 | 1.000 | 0.030 | -0.006 |
| non_pbm_confirmation | Wells | Iris | 10.000 | 38.133 | 1543.000 | 1.000 | -0.011 | -0.031 |
| non_pbm_confirmation | Wells | Jack | 10.000 | 39.166 | 2146.000 | 1.000 | -0.101 | -0.005 |
| non_pbm_confirmation | Wells | Jason | 10.000 | 42.633 | 1291.000 | 1.000 | -0.107 | 0.030 |
| non_pbm_confirmation | Wells | Jonathan | 10.000 | 37.300 | 2289.000 | 1.000 | 0.013 | -0.106 |
| non_pbm_confirmation | Wells | Laura | 9.000 | 24.034 | 838.000 | 1.000 | -0.120 | -0.015 |
| non_pbm_confirmation | Wells | Lee | 8.000 | 24.034 | 416.000 | 1.000 | -0.111 | 0.020 |
| non_pbm_confirmation | Wells | Martin | 9.000 | 24.066 | 563.000 | 1.000 | -0.075 | -0.045 |
| non_pbm_confirmation | Wells | Nancy | 8.000 | 21.033 | 445.000 | 1.000 | -0.051 | -0.109 |
| non_pbm_confirmation | Wells | Neil | 8.000 | 23.900 | 647.000 | 1.000 | -0.135 | -0.047 |
| non_pbm_confirmation | Wells | Neville | 9.000 | 24.067 | 1003.000 | 1.000 | -0.182 | -6.87e-04 |
| non_pbm_confirmation | Wells | Olivia | 9.000 | 23.733 | 848.000 | 1.000 | -0.117 | 0.070 |
| non_pbm_confirmation | Wells | Penny | 9.000 | 23.567 | 746.000 | 1.000 | -0.064 | -0.021 |
| non_pbm_confirmation | Wells | Rosie | 9.000 | 23.367 | 243.000 | 1.000 | -0.230 | 0.139 |
| non_pbm_confirmation | Wells | Samantha | 9.000 | 24.167 | 645.000 | 1.000 | -0.056 | -0.088 |
| non_pbm_confirmation | Wells | Sean | 9.000 | 23.933 | 326.000 | 1.000 | -0.037 | 0.030 |
| non_pbm_confirmation | Wells | Sheila | 8.000 | 21.766 | 610.000 | 1.000 | 0.323 | -0.073 |
| non_pbm_confirmation | Wells | Simon | 9.000 | 24.033 | 518.000 | 1.000 | -0.111 | 0.044 |
| non_pbm_confirmation | Wells | Stella | 8.000 | 23.733 | 686.000 | 1.000 | -0.095 | -0.002 |
| non_pbm_confirmation | Wells | Tony | 9.000 | 24.400 | 633.000 | 1.000 | -0.256 | -0.059 |
| all79_descriptive | Belfast | Barbara | 14.000 | 21.300 | 2873.000 | 1.000 | -0.053 | -0.111 |
| all79_descriptive | Belfast | Conor | 13.000 | 9.700 | 3458.000 | 1.000 | -0.102 | 0.059 |
| all79_descriptive | Belfast | Courtney | 7.000 | 8.367 | 2280.000 | 1.000 | -0.096 | 0.085 |
| all79_descriptive | Belfast | David | 12.000 | 23.267 | 1897.000 | 1.000 | 0.008 | -0.109 |
| all79_descriptive | Belfast | John | 7.000 | 10.066 | 1988.000 | 1.000 | 0.273 | -0.074 |
| all79_descriptive | Belfast | Michelle | 14.000 | 23.700 | 3490.000 | 1.000 | 0.229 | -0.165 |
| all79_descriptive | Belfast | Rachel | 9.000 | 8.267 | 1604.000 | 1.000 | -0.377 | -0.111 |
| all79_descriptive | Belfast | Stuart | 10.000 | 11.733 | 3820.000 | 1.000 | -0.194 | 0.080 |
| all79_descriptive | Brown | Adam | 55.000 | 35.267 | 45734.000 | 1.000 | -0.119 | -0.056 |
| all79_descriptive | Brown | Eve | 10.000 | 9.000 | 11676.000 | 1.000 | -0.220 | -0.079 |
| all79_descriptive | Brown | Sarah | 135.000 | 34.033 | 33625.000 | 1.000 | -0.065 | -0.051 |
| all79_descriptive | Demetras1 | Trevor | 25.000 | 23.000 | 6802.000 | 1.000 | -0.439 | -3.60e-04 |
| all79_descriptive | Forrester | Ella | 34.000 | 47.967 | 6590.000 | 1.000 | -0.015 | 0.047 |
| all79_descriptive | Kuczaj | Abe | 207.000 | 31.567 | 36873.000 | 1.000 | -0.079 | -0.066 |
| all79_descriptive | Lara | Lara | 117.000 | 18.400 | 48364.000 | 1.000 | -0.223 | -0.020 |
| all79_descriptive | MPI-EVA-Manchester | Eleanor | 107.000 | 12.933 | 85004.000 | 1.000 | -0.027 | -0.092 |
| all79_descriptive | MPI-EVA-Manchester | Fraser | 107.000 | 13.067 | 149932.000 | 1.000 | -0.338 | 0.060 |
| all79_descriptive | MPI-EVA-Manchester | Gina | 118.000 | 19.934 | 71593.000 | 1.000 | 0.024 | -0.054 |
| all79_descriptive | MPI-EVA-Manchester | Helen | 181.000 | 25.566 | 154078.000 | 1.000 | -0.021 | -0.033 |
| all79_descriptive | Manchester | Anne | 35.000 | 11.100 | 20693.000 | 1.000 | -0.249 | 0.009 |
| all79_descriptive | Manchester | Aran | 33.000 | 11.533 | 17565.000 | 1.000 | -0.641 | 0.330 |
| all79_descriptive | Manchester | Becky | 34.000 | 11.267 | 24407.000 | 1.000 | -0.207 | -0.080 |
| all79_descriptive | Manchester | Carl | 33.000 | 11.767 | 25620.000 | 1.000 | -0.073 | -0.202 |
| all79_descriptive | Manchester | Dominic | 35.000 | 11.700 | 21919.000 | 1.000 | 0.061 | -0.090 |
| all79_descriptive | Manchester | Gail | 34.000 | 11.500 | 17271.000 | 1.000 | -0.261 | 0.010 |
| all79_descriptive | Manchester | Joel | 35.000 | 11.334 | 18696.000 | 1.000 | -0.252 | 0.026 |
| all79_descriptive | Manchester | John | 32.000 | 11.300 | 13694.000 | 1.000 | -0.352 | 0.031 |
| all79_descriptive | Manchester | Liz | 34.000 | 11.300 | 16657.000 | 1.000 | -0.462 | 0.085 |
| all79_descriptive | Manchester | Nicole | 32.000 | 11.500 | 17152.000 | 1.000 | 0.008 | -0.022 |
| all79_descriptive | Manchester | Ruth | 33.000 | 12.200 | 20817.000 | 1.000 | -0.240 | 0.181 |
| all79_descriptive | Manchester | Warren | 36.000 | 11.467 | 17151.000 | 1.000 | -0.208 | 0.037 |
| all79_descriptive | Post | Lew | 10.000 | 9.566 | 2439.000 | 1.000 | -0.054 | 0.174 |
| all79_descriptive | Post | She | 10.000 | 9.667 | 2599.000 | 1.000 | -0.397 | -0.148 |
| all79_descriptive | Post | Tow | 10.000 | 9.933 | 2988.000 | 1.000 | 0.019 | -0.043 |
| all79_descriptive | Providence | Alex | 51.000 | 24.633 | 19090.000 | 1.000 | 0.061 | 0.022 |
| all79_descriptive | Providence | Ethan | 50.000 | 23.900 | 13588.000 | 1.000 | -0.034 | 0.027 |
| all79_descriptive | Providence | Lily | 77.000 | 35.000 | 28000.000 | 1.000 | -0.055 | -0.038 |
| all79_descriptive | Providence | Naima | 87.000 | 34.466 | 34215.000 | 1.000 | -0.126 | -0.021 |
| all79_descriptive | Providence | Violet | 49.000 | 33.800 | 10788.000 | 1.000 | 0.052 | -0.082 |
| all79_descriptive | Providence | William | 44.000 | 24.200 | 15967.000 | 1.000 | -0.020 | -0.045 |
| all79_descriptive | Sachs | Naomi | 92.000 | 42.133 | 16021.000 | 1.000 | -0.016 | -0.083 |
| all79_descriptive | Weist | Ben | 11.000 | 11.500 | 3340.000 | 1.000 | -0.280 | -0.087 |
| all79_descriptive | Weist | Emily | 3.000 | 6.567 | 759.000 | 1.000 | -0.255 | -0.317 |
| all79_descriptive | Weist | Emma | 26.000 | 21.333 | 6069.000 | 1.000 | 0.140 | -0.111 |
| all79_descriptive | Weist | Jillian | 22.000 | 8.967 | 5467.000 | 1.000 | -0.115 | -0.270 |
| all79_descriptive | Weist | Matt | 57.000 | 32.834 | 11093.000 | 1.000 | 0.014 | -0.002 |
| all79_descriptive | Weist | Roman | 40.000 | 29.000 | 10583.000 | 1.000 | 0.003 | 0.051 |
| all79_descriptive | Wells | Abigail | 10.000 | 38.067 | 1116.000 | 1.000 | -0.080 | -0.030 |
| all79_descriptive | Wells | Benjamin | 10.000 | 43.100 | 1435.000 | 1.000 | -0.065 | 0.018 |
| all79_descriptive | Wells | Betty | 8.000 | 20.967 | 1660.000 | 1.000 | -0.143 | -0.060 |
| all79_descriptive | Wells | Darren | 10.000 | 40.133 | 1561.000 | 1.000 | 0.064 | -0.026 |
| all79_descriptive | Wells | Debbie | 10.000 | 29.633 | 1381.000 | 1.000 | -0.110 | -0.008 |
| all79_descriptive | Wells | Ellen | 9.000 | 24.166 | 2092.000 | 1.000 | -0.174 | 0.052 |
| all79_descriptive | Wells | Elspeth | 10.000 | 42.100 | 1195.000 | 1.000 | -0.153 | 0.050 |
| all79_descriptive | Wells | Frances | 10.000 | 40.234 | 1486.000 | 1.000 | -0.014 | -0.038 |
| all79_descriptive | Wells | Gary | 10.000 | 39.000 | 1879.000 | 1.000 | -0.025 | -0.032 |
| all79_descriptive | Wells | Gavin | 9.000 | 38.900 | 1739.000 | 1.000 | -0.144 | 0.029 |
| all79_descriptive | Wells | Geoffrey | 9.000 | 41.733 | 1153.000 | 1.000 | -0.047 | 0.015 |
| all79_descriptive | Wells | Gerald | 9.000 | 38.967 | 1554.000 | 1.000 | -0.124 | -0.005 |
| all79_descriptive | Wells | Harriet | 10.000 | 40.033 | 1380.000 | 1.000 | 0.018 | -0.006 |
| all79_descriptive | Wells | Iris | 10.000 | 38.133 | 1543.000 | 1.000 | -0.021 | -0.032 |
| all79_descriptive | Wells | Jack | 10.000 | 39.166 | 2146.000 | 1.000 | -0.112 | -0.006 |
| all79_descriptive | Wells | Jason | 10.000 | 42.633 | 1291.000 | 1.000 | -0.117 | 0.029 |
| all79_descriptive | Wells | Jonathan | 10.000 | 37.300 | 2289.000 | 1.000 | 0.006 | -0.106 |
| all79_descriptive | Wells | Laura | 9.000 | 24.034 | 838.000 | 1.000 | -0.135 | -0.017 |
| all79_descriptive | Wells | Lee | 8.000 | 24.034 | 416.000 | 1.000 | -0.124 | 0.017 |
| all79_descriptive | Wells | Martin | 9.000 | 24.066 | 563.000 | 1.000 | -0.088 | -0.046 |
| all79_descriptive | Wells | Nancy | 8.000 | 21.033 | 445.000 | 1.000 | -0.067 | -0.111 |
| all79_descriptive | Wells | Neil | 8.000 | 23.900 | 647.000 | 1.000 | -0.153 | -0.048 |
| all79_descriptive | Wells | Neville | 9.000 | 24.067 | 1003.000 | 1.000 | -0.199 | -6.66e-04 |
| all79_descriptive | Wells | Olivia | 9.000 | 23.733 | 848.000 | 1.000 | -0.132 | 0.070 |
| all79_descriptive | Wells | Penny | 9.000 | 23.567 | 746.000 | 1.000 | -0.072 | -0.021 |
| all79_descriptive | Wells | Rosie | 9.000 | 23.367 | 243.000 | 1.000 | -0.241 | 0.136 |
| all79_descriptive | Wells | Samantha | 9.000 | 24.167 | 645.000 | 1.000 | -0.066 | -0.088 |
| all79_descriptive | Wells | Sean | 9.000 | 23.933 | 326.000 | 1.000 | -0.039 | 0.031 |
| all79_descriptive | Wells | Sheila | 8.000 | 21.766 | 610.000 | 1.000 | 0.316 | -0.075 |
| all79_descriptive | Wells | Simon | 9.000 | 24.033 | 518.000 | 1.000 | -0.125 | 0.043 |
| all79_descriptive | Wells | Stella | 8.000 | 23.733 | 686.000 | 1.000 | -0.113 | -0.002 |
| all79_descriptive | Wells | Tony | 9.000 | 24.400 | 633.000 | 1.000 | -0.269 | -0.060 |

### all79_descriptive

#### Belfast

##### Belfast/Barbara

![Belfast/Barbara trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_barbara.png)

##### Belfast/Conor

![Belfast/Conor trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_conor.png)

##### Belfast/Courtney

![Belfast/Courtney trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_courtney.png)

##### Belfast/David

![Belfast/David trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_david.png)

##### Belfast/John

![Belfast/John trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_john.png)

##### Belfast/Michelle

![Belfast/Michelle trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_michelle.png)

##### Belfast/Rachel

![Belfast/Rachel trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_rachel.png)

##### Belfast/Stuart

![Belfast/Stuart trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/belfast_stuart.png)

#### Brown

##### Brown/Adam

![Brown/Adam trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/brown_adam.png)

##### Brown/Eve

![Brown/Eve trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/brown_eve.png)

##### Brown/Sarah

![Brown/Sarah trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/brown_sarah.png)

#### Demetras1

##### Demetras1/Trevor

![Demetras1/Trevor trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/demetras1_trevor.png)

#### Forrester

##### Forrester/Ella

![Forrester/Ella trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/forrester_ella.png)

#### Kuczaj

##### Kuczaj/Abe

![Kuczaj/Abe trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/kuczaj_abe.png)

#### Lara

##### Lara/Lara

![Lara/Lara trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/lara_lara.png)

#### MPI-EVA-Manchester

##### MPI-EVA-Manchester/Eleanor

![MPI-EVA-Manchester/Eleanor trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/mpi_eva_manchester_eleanor.png)

##### MPI-EVA-Manchester/Fraser

![MPI-EVA-Manchester/Fraser trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/mpi_eva_manchester_fraser.png)

##### MPI-EVA-Manchester/Gina

![MPI-EVA-Manchester/Gina trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/mpi_eva_manchester_gina.png)

##### MPI-EVA-Manchester/Helen

![MPI-EVA-Manchester/Helen trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/mpi_eva_manchester_helen.png)

#### Manchester

##### Manchester/Anne

![Manchester/Anne trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_anne.png)

##### Manchester/Aran

![Manchester/Aran trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_aran.png)

##### Manchester/Becky

![Manchester/Becky trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_becky.png)

##### Manchester/Carl

![Manchester/Carl trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_carl.png)

##### Manchester/Dominic

![Manchester/Dominic trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_dominic.png)

##### Manchester/Gail

![Manchester/Gail trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_gail.png)

##### Manchester/Joel

![Manchester/Joel trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_joel.png)

##### Manchester/John

![Manchester/John trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_john.png)

##### Manchester/Liz

![Manchester/Liz trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_liz.png)

##### Manchester/Nicole

![Manchester/Nicole trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_nicole.png)

##### Manchester/Ruth

![Manchester/Ruth trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_ruth.png)

##### Manchester/Warren

![Manchester/Warren trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/manchester_warren.png)

#### Post

##### Post/Lew

![Post/Lew trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/post_lew.png)

##### Post/She

![Post/She trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/post_she.png)

##### Post/Tow

![Post/Tow trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/post_tow.png)

#### Providence

##### Providence/Alex

![Providence/Alex trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/providence_alex.png)

##### Providence/Ethan

![Providence/Ethan trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/providence_ethan.png)

##### Providence/Lily

![Providence/Lily trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/providence_lily.png)

##### Providence/Naima

![Providence/Naima trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/providence_naima.png)

##### Providence/Violet

![Providence/Violet trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/providence_violet.png)

##### Providence/William

![Providence/William trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/providence_william.png)

#### Sachs

##### Sachs/Naomi

![Sachs/Naomi trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/sachs_naomi.png)

#### Weist

##### Weist/Ben

![Weist/Ben trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/weist_ben.png)

##### Weist/Emily

![Weist/Emily trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/weist_emily.png)

##### Weist/Emma

![Weist/Emma trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/weist_emma.png)

##### Weist/Jillian

![Weist/Jillian trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/weist_jillian.png)

##### Weist/Matt

![Weist/Matt trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/weist_matt.png)

##### Weist/Roman

![Weist/Roman trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/weist_roman.png)

#### Wells

##### Wells/Abigail

![Wells/Abigail trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_abigail.png)

##### Wells/Benjamin

![Wells/Benjamin trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_benjamin.png)

##### Wells/Betty

![Wells/Betty trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_betty.png)

##### Wells/Darren

![Wells/Darren trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_darren.png)

##### Wells/Debbie

![Wells/Debbie trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_debbie.png)

##### Wells/Ellen

![Wells/Ellen trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_ellen.png)

##### Wells/Elspeth

![Wells/Elspeth trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_elspeth.png)

##### Wells/Frances

![Wells/Frances trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_frances.png)

##### Wells/Gary

![Wells/Gary trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_gary.png)

##### Wells/Gavin

![Wells/Gavin trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_gavin.png)

##### Wells/Geoffrey

![Wells/Geoffrey trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_geoffrey.png)

##### Wells/Gerald

![Wells/Gerald trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_gerald.png)

##### Wells/Harriet

![Wells/Harriet trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_harriet.png)

##### Wells/Iris

![Wells/Iris trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_iris.png)

##### Wells/Jack

![Wells/Jack trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_jack.png)

##### Wells/Jason

![Wells/Jason trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_jason.png)

##### Wells/Jonathan

![Wells/Jonathan trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_jonathan.png)

##### Wells/Laura

![Wells/Laura trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_laura.png)

##### Wells/Lee

![Wells/Lee trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_lee.png)

##### Wells/Martin

![Wells/Martin trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_martin.png)

##### Wells/Nancy

![Wells/Nancy trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_nancy.png)

##### Wells/Neil

![Wells/Neil trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_neil.png)

##### Wells/Neville

![Wells/Neville trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_neville.png)

##### Wells/Olivia

![Wells/Olivia trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_olivia.png)

##### Wells/Penny

![Wells/Penny trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_penny.png)

##### Wells/Rosie

![Wells/Rosie trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_rosie.png)

##### Wells/Samantha

![Wells/Samantha trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_samantha.png)

##### Wells/Sean

![Wells/Sean trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_sean.png)

##### Wells/Sheila

![Wells/Sheila trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_sheila.png)

##### Wells/Simon

![Wells/Simon trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_simon.png)

##### Wells/Stella

![Wells/Stella trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_stella.png)

##### Wells/Tony

![Wells/Tony trajectory](../figs/direct_surprisal_replication/mistral_full79/all79_descriptive/children/wells_tony.png)

### non_pbm_confirmation

#### Belfast

##### Belfast/Barbara

![Belfast/Barbara trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_barbara.png)

##### Belfast/Conor

![Belfast/Conor trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_conor.png)

##### Belfast/Courtney

![Belfast/Courtney trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_courtney.png)

##### Belfast/David

![Belfast/David trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_david.png)

##### Belfast/John

![Belfast/John trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_john.png)

##### Belfast/Michelle

![Belfast/Michelle trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_michelle.png)

##### Belfast/Rachel

![Belfast/Rachel trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_rachel.png)

##### Belfast/Stuart

![Belfast/Stuart trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/belfast_stuart.png)

#### Demetras1

##### Demetras1/Trevor

![Demetras1/Trevor trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/demetras1_trevor.png)

#### Forrester

##### Forrester/Ella

![Forrester/Ella trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/forrester_ella.png)

#### Kuczaj

##### Kuczaj/Abe

![Kuczaj/Abe trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/kuczaj_abe.png)

#### Lara

##### Lara/Lara

![Lara/Lara trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/lara_lara.png)

#### MPI-EVA-Manchester

##### MPI-EVA-Manchester/Eleanor

![MPI-EVA-Manchester/Eleanor trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/mpi_eva_manchester_eleanor.png)

##### MPI-EVA-Manchester/Fraser

![MPI-EVA-Manchester/Fraser trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/mpi_eva_manchester_fraser.png)

##### MPI-EVA-Manchester/Gina

![MPI-EVA-Manchester/Gina trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/mpi_eva_manchester_gina.png)

##### MPI-EVA-Manchester/Helen

![MPI-EVA-Manchester/Helen trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/mpi_eva_manchester_helen.png)

#### Post

##### Post/Lew

![Post/Lew trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/post_lew.png)

##### Post/She

![Post/She trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/post_she.png)

##### Post/Tow

![Post/Tow trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/post_tow.png)

#### Sachs

##### Sachs/Naomi

![Sachs/Naomi trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/sachs_naomi.png)

#### Weist

##### Weist/Ben

![Weist/Ben trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/weist_ben.png)

##### Weist/Emily

![Weist/Emily trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/weist_emily.png)

##### Weist/Emma

![Weist/Emma trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/weist_emma.png)

##### Weist/Jillian

![Weist/Jillian trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/weist_jillian.png)

##### Weist/Matt

![Weist/Matt trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/weist_matt.png)

##### Weist/Roman

![Weist/Roman trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/weist_roman.png)

#### Wells

##### Wells/Abigail

![Wells/Abigail trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_abigail.png)

##### Wells/Benjamin

![Wells/Benjamin trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_benjamin.png)

##### Wells/Betty

![Wells/Betty trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_betty.png)

##### Wells/Darren

![Wells/Darren trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_darren.png)

##### Wells/Debbie

![Wells/Debbie trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_debbie.png)

##### Wells/Ellen

![Wells/Ellen trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_ellen.png)

##### Wells/Elspeth

![Wells/Elspeth trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_elspeth.png)

##### Wells/Frances

![Wells/Frances trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_frances.png)

##### Wells/Gary

![Wells/Gary trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_gary.png)

##### Wells/Gavin

![Wells/Gavin trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_gavin.png)

##### Wells/Geoffrey

![Wells/Geoffrey trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_geoffrey.png)

##### Wells/Gerald

![Wells/Gerald trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_gerald.png)

##### Wells/Harriet

![Wells/Harriet trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_harriet.png)

##### Wells/Iris

![Wells/Iris trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_iris.png)

##### Wells/Jack

![Wells/Jack trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_jack.png)

##### Wells/Jason

![Wells/Jason trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_jason.png)

##### Wells/Jonathan

![Wells/Jonathan trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_jonathan.png)

##### Wells/Laura

![Wells/Laura trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_laura.png)

##### Wells/Lee

![Wells/Lee trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_lee.png)

##### Wells/Martin

![Wells/Martin trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_martin.png)

##### Wells/Nancy

![Wells/Nancy trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_nancy.png)

##### Wells/Neil

![Wells/Neil trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_neil.png)

##### Wells/Neville

![Wells/Neville trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_neville.png)

##### Wells/Olivia

![Wells/Olivia trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_olivia.png)

##### Wells/Penny

![Wells/Penny trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_penny.png)

##### Wells/Rosie

![Wells/Rosie trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_rosie.png)

##### Wells/Samantha

![Wells/Samantha trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_samantha.png)

##### Wells/Sean

![Wells/Sean trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_sean.png)

##### Wells/Sheila

![Wells/Sheila trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_sheila.png)

##### Wells/Simon

![Wells/Simon trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_simon.png)

##### Wells/Stella

![Wells/Stella trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_stella.png)

##### Wells/Tony

![Wells/Tony trajectory](../figs/direct_surprisal_replication/mistral_full79/non_pbm_confirmation/children/wells_tony.png)

### pbm_discovery

#### Brown

##### Brown/Adam

![Brown/Adam trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/brown_adam.png)

##### Brown/Eve

![Brown/Eve trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/brown_eve.png)

##### Brown/Sarah

![Brown/Sarah trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/brown_sarah.png)

#### Manchester

##### Manchester/Anne

![Manchester/Anne trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_anne.png)

##### Manchester/Aran

![Manchester/Aran trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_aran.png)

##### Manchester/Becky

![Manchester/Becky trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_becky.png)

##### Manchester/Carl

![Manchester/Carl trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_carl.png)

##### Manchester/Dominic

![Manchester/Dominic trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_dominic.png)

##### Manchester/Gail

![Manchester/Gail trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_gail.png)

##### Manchester/Joel

![Manchester/Joel trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_joel.png)

##### Manchester/John

![Manchester/John trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_john.png)

##### Manchester/Liz

![Manchester/Liz trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_liz.png)

##### Manchester/Nicole

![Manchester/Nicole trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_nicole.png)

##### Manchester/Ruth

![Manchester/Ruth trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_ruth.png)

##### Manchester/Warren

![Manchester/Warren trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/manchester_warren.png)

#### Providence

##### Providence/Alex

![Providence/Alex trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/providence_alex.png)

##### Providence/Ethan

![Providence/Ethan trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/providence_ethan.png)

##### Providence/Lily

![Providence/Lily trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/providence_lily.png)

##### Providence/Naima

![Providence/Naima trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/providence_naima.png)

##### Providence/Violet

![Providence/Violet trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/providence_violet.png)

##### Providence/William

![Providence/William trajectory](../figs/direct_surprisal_replication/mistral_full79/pbm_discovery/children/providence_william.png)

## Interpretation Boundary

PBM results are discovery/scorer-robustness results. A pooled 79-child estimate is descriptive. Only the separately reported non-PBM estimate is the frozen sample confirmation. Generated n-gram candidates are not same-meaning alternatives, and caretaker trajectories reflect input adaptation.

## Saved Artifacts

- Model summaries: `results/direct_surprisal_replication/mistral_full79/models/model_summaries.csv`
- Coefficients: `results/direct_surprisal_replication/mistral_full79/models/coefficients_long.csv`
- Prediction grid: `results/direct_surprisal_replication/mistral_full79/models/prediction_grid.csv`
- Child trajectories: `results/direct_surprisal_replication/mistral_full79/models/child_age_session_trajectories.csv.gz`
- Child slopes: `results/direct_surprisal_replication/mistral_full79/models/child_slope_summary.csv`
- Leave-one-cluster-out estimates: `results/direct_surprisal_replication/mistral_full79/models/leave_one_cluster_out.csv`
- Child profile audit: `results/direct_surprisal_replication/mistral_full79/models/child_profile_audit.csv`
