# TinyDialogues PBM: Direct-Surprisal Replication

This report implements the frozen 2026-07-21 direct-surprisal protocol. A negative contextual-surprisal age coefficient means greater scorer predictability at the same exact/top-coded lexical word effort; it is not, by itself, proof of a normative efficiency optimum.

## Input And Sample Flow

Input wide table: `results/direct_surprisal_replication/tinydialogues_pbm/child_direct_surprisal_wide.csv.gz`

| scope | step | rows | children | corpora | sessions |
| --- | --- | --- | --- | --- | --- |
| pbm_discovery | source_rows | 446508.000 | 21.000 | 3.000 | 982.000 |
| pbm_discovery | age_006_065 | 446508.000 | 21.000 | 3.000 | 982.000 |
| pbm_discovery | nonempty_real_target | 446508.000 | 21.000 | 3.000 | 982.000 |
| pbm_discovery | finite_scored_real_k3 | 446508.000 | 21.000 | 3.000 | 982.000 |
| pbm_discovery | primary_context_bearing | 443848.000 | 21.000 | 3.000 | 981.000 |

## Frozen Primary Results

| scope | model_id | source_rows | children | corpora | age_estimate | age_ci_low | age_ci_high | age_p_value | protocol_result | fit_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | 443848.000 | 21.000 | 3.000 | -0.222 | -0.311 | -0.132 | 1.24e-06 | expected_direction_interval_excludes_zero | PASS |
| pbm_discovery | P2_k0_unconditional | 446508.000 | 21.000 | 3.000 | -0.254 | -0.339 | -0.168 | 6.00e-09 | decomposition_no_directional_rule | PASS |
| pbm_discovery | P3_k3_context_gain | 443848.000 | 21.000 | 3.000 | -0.032 | -0.050 | -0.014 | 5.43e-04 | contrary_direction_interval_excludes_zero | PASS |

Context gain is `sum_bits_k0 - sum_bits_k3`; positive values mean context made the observed target more probable under this scorer.

## Child Bootstrap

| scope | model_id | outcome | requested_reps | successful_reps | bootstrap_mean | bootstrap_se | bootstrap_ci_low | bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | 200.000 | 200.000 | -0.218 | 0.047 | -0.308 | -0.130 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | 200.000 | 200.000 | -0.035 | 0.009 | -0.051 | -0.018 |

## Frozen Age-Bin Contrasts

Contrasts use `006-023` as the reference at fixed exact/top-coded lexical word effort with child fixed effects and child-clustered covariance. They do not by themselves establish a sustained developmental onset.

| scope | model_id | term | estimate | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -2.118 | -3.627 | -0.610 | 0.006 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -3.764 | -5.320 | -2.207 | 2.15e-06 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -3.843 | -6.693 | -0.994 | 0.008 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -6.320 | -9.842 | -2.798 | 4.37e-04 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -5.418 | -8.034 | -2.802 | 4.93e-05 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -5.968 | -8.909 | -3.027 | 6.98e-05 |
| pbm_discovery | P1_k3_contextual_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -8.654 | -12.691 | -4.617 | 2.65e-05 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -2.456 | -4.065 | -0.847 | 0.003 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -4.301 | -5.928 | -2.673 | 2.22e-07 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -4.562 | -7.282 | -1.842 | 0.001 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -6.962 | -10.243 | -3.681 | 3.21e-05 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -6.262 | -8.782 | -3.743 | 1.11e-06 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -7.135 | -9.827 | -4.442 | 2.07e-07 |
| pbm_discovery | P2_k0_unconditional_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -9.907 | -13.530 | -6.283 | 8.38e-08 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.024-029] | -0.332 | -0.596 | -0.068 | 0.014 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.030-035] | -0.540 | -0.813 | -0.267 | 1.07e-04 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.036-041] | -0.692 | -1.030 | -0.353 | 6.17e-05 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.042-047] | -0.608 | -1.029 | -0.187 | 0.005 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.048-053] | -0.876 | -1.344 | -0.407 | 2.50e-04 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.054-059] | -1.126 | -1.584 | -0.668 | 1.46e-06 |
| pbm_discovery | P3_k3_context_gain_age_bins | C(age_bin, Treatment(reference='006-023'))[T.060-065] | -1.183 | -1.576 | -0.790 | 3.66e-09 |

## Fixed-Effort Population Lines

### pbm_discovery

![pbm_discovery population predictions](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/population_fixed_effort_lines.png)

## Estimator And Secondary-Outcome Audit

| scope | model_id | tier | estimator | age_estimate | age_ci_low | age_ci_high | age_p_value | fit_status | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | primary | exact_cell_wls_child_cluster | -0.222 | -0.311 | -0.132 | 1.24e-06 | PASS |  |
| pbm_discovery | P1_k3_contextual_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| pbm_discovery | P1_k3_contextual_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.272 | -0.391 | -0.153 | 7.06e-06 | PASS |  |
| pbm_discovery | P1_k3_contextual_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.221 | -0.313 | -0.130 | 2.09e-06 | PASS |  |
| pbm_discovery | P1_k3_contextual_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.226 | -0.311 | -0.141 | 1.86e-07 | PASS |  |
| pbm_discovery | P2_k0_unconditional | primary | exact_cell_wls_child_cluster | -0.254 | -0.339 | -0.168 | 6.00e-09 | PASS |  |
| pbm_discovery | P2_k0_unconditional_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| pbm_discovery | P3_k3_context_gain | primary | exact_cell_wls_child_cluster | -0.032 | -0.050 | -0.014 | 5.43e-04 | PASS |  |
| pbm_discovery | P3_k3_context_gain_age_bins | secondary_age_bins | exact_cell_wls_child_cluster |  |  |  |  | PASS |  |
| pbm_discovery | P3_k3_context_gain_quadratic | secondary_nonlinear | exact_cell_wls_child_cluster | -0.037 | -0.054 | -0.020 | 1.38e-05 | PASS |  |
| pbm_discovery | P3_k3_context_gain_mundlak | estimator_sensitivity | mundlak_wls_child_cluster | -0.031 | -0.049 | -0.013 | 8.22e-04 | PASS |  |
| pbm_discovery | P3_k3_context_gain_gee | estimator_sensitivity | exact_cell_gee_child_cluster | -0.035 | -0.056 | -0.014 | 0.001 | PASS |  |
| pbm_discovery | S1_k1_contextual | secondary | exact_cell_wls_child_cluster | -0.224 | -0.313 | -0.135 | 9.09e-07 | PASS |  |
| pbm_discovery | S2_k2_contextual | secondary | exact_cell_wls_child_cluster | -0.223 | -0.312 | -0.133 | 1.05e-06 | PASS |  |
| pbm_discovery | S3_k1_context_gain | secondary | exact_cell_wls_child_cluster | -0.030 | -0.047 | -0.013 | 4.88e-04 | PASS |  |
| pbm_discovery | S4_k2_context_gain | secondary | exact_cell_wls_child_cluster | -0.031 | -0.049 | -0.014 | 3.90e-04 | PASS |  |
| pbm_discovery | B1_random_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.681 | 0.473 | 0.890 | 1.45e-10 | PASS |  |
| pbm_discovery | B2_unigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.166 | 0.088 | 0.245 | 3.39e-05 | PASS |  |
| pbm_discovery | B3_bigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.118 | 0.050 | 0.186 | 7.10e-04 | PASS |  |
| pbm_discovery | B4_trigram_minus_real_k3 | secondary | exact_cell_wls_child_cluster | 0.099 | 0.048 | 0.150 | 1.33e-04 | PASS |  |

## Leave-One-Child And Leave-One-Corpus Influence

| scope | model_id | outcome | drop_level | drop_id | remaining_children | observed_age_estimate | leave_out_age_estimate | change_from_observed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Brown/Adam | 20.000 | -0.222 | -0.199 | 0.023 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Brown/Eve | 20.000 | -0.222 | -0.213 | 0.009 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Brown/Sarah | 20.000 | -0.222 | -0.250 | -0.028 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Anne | 20.000 | -0.222 | -0.222 | -1.31e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Aran | 20.000 | -0.222 | -0.223 | -0.001 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Becky | 20.000 | -0.222 | -0.222 | 1.68e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Carl | 20.000 | -0.222 | -0.216 | 0.006 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Dominic | 20.000 | -0.222 | -0.221 | 9.36e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Gail | 20.000 | -0.222 | -0.221 | 0.001 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Joel | 20.000 | -0.222 | -0.223 | -7.08e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/John | 20.000 | -0.222 | -0.222 | 1.73e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Liz | 20.000 | -0.222 | -0.220 | 0.002 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Nicole | 20.000 | -0.222 | -0.219 | 0.003 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Ruth | 20.000 | -0.222 | -0.221 | 4.41e-04 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Manchester/Warren | 20.000 | -0.222 | -0.220 | 0.001 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Alex | 20.000 | -0.222 | -0.230 | -0.009 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Ethan | 20.000 | -0.222 | -0.230 | -0.008 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Lily | 20.000 | -0.222 | -0.238 | -0.016 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Naima | 20.000 | -0.222 | -0.193 | 0.028 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/Violet | 20.000 | -0.222 | -0.230 | -0.008 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | child | Providence/William | 20.000 | -0.222 | -0.228 | -0.006 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | corpus | Brown | 18.000 | -0.222 | -0.220 | 0.002 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | corpus | Manchester | 9.000 | -0.222 | -0.214 | 0.008 |
| pbm_discovery | P1_k3_contextual | real_k3_sum_bits | corpus | Providence | 15.000 | -0.222 | -0.251 | -0.029 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Adam | 20.000 | -0.254 | -0.241 | 0.012 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Eve | 20.000 | -0.254 | -0.245 | 0.009 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Brown/Sarah | 20.000 | -0.254 | -0.283 | -0.029 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Anne | 20.000 | -0.254 | -0.253 | 0.001 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Aran | 20.000 | -0.254 | -0.255 | -8.20e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Becky | 20.000 | -0.254 | -0.253 | 6.10e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Carl | 20.000 | -0.254 | -0.250 | 0.004 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Dominic | 20.000 | -0.254 | -0.252 | 0.002 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Gail | 20.000 | -0.254 | -0.253 | 0.001 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Joel | 20.000 | -0.254 | -0.254 | 1.46e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/John | 20.000 | -0.254 | -0.253 | 2.67e-04 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Liz | 20.000 | -0.254 | -0.252 | 0.002 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Nicole | 20.000 | -0.254 | -0.250 | 0.004 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Ruth | 20.000 | -0.254 | -0.252 | 0.002 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Manchester/Warren | 20.000 | -0.254 | -0.251 | 0.002 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Alex | 20.000 | -0.254 | -0.262 | -0.008 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Ethan | 20.000 | -0.254 | -0.262 | -0.009 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Lily | 20.000 | -0.254 | -0.268 | -0.014 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Naima | 20.000 | -0.254 | -0.224 | 0.030 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/Violet | 20.000 | -0.254 | -0.262 | -0.008 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | child | Providence/William | 20.000 | -0.254 | -0.258 | -0.004 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | corpus | Brown | 18.000 | -0.254 | -0.269 | -0.015 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | corpus | Manchester | 9.000 | -0.254 | -0.237 | 0.016 |
| pbm_discovery | P2_k0_unconditional | real_k0_sum_bits | corpus | Providence | 15.000 | -0.254 | -0.277 | -0.023 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Adam | 20.000 | -0.032 | -0.043 | -0.011 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Eve | 20.000 | -0.032 | -0.033 | -4.01e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Brown/Sarah | 20.000 | -0.032 | -0.033 | -8.88e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Anne | 20.000 | -0.032 | -0.031 | 0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Aran | 20.000 | -0.032 | -0.032 | 2.70e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Becky | 20.000 | -0.032 | -0.032 | 4.50e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Carl | 20.000 | -0.032 | -0.034 | -0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Dominic | 20.000 | -0.032 | -0.032 | 6.59e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Gail | 20.000 | -0.032 | -0.032 | 1.71e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Joel | 20.000 | -0.032 | -0.031 | 8.60e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/John | 20.000 | -0.032 | -0.032 | 1.20e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Liz | 20.000 | -0.032 | -0.032 | 4.99e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Nicole | 20.000 | -0.032 | -0.031 | 8.55e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Ruth | 20.000 | -0.032 | -0.031 | 0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Manchester/Warren | 20.000 | -0.032 | -0.031 | 0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Alex | 20.000 | -0.032 | -0.032 | 5.45e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Ethan | 20.000 | -0.032 | -0.033 | -6.57e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Lily | 20.000 | -0.032 | -0.031 | 0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Naima | 20.000 | -0.032 | -0.030 | 0.002 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/Violet | 20.000 | -0.032 | -0.033 | -6.19e-04 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | child | Providence/William | 20.000 | -0.032 | -0.031 | 0.001 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | corpus | Brown | 18.000 | -0.032 | -0.049 | -0.016 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | corpus | Manchester | 9.000 | -0.032 | -0.024 | 0.009 |
| pbm_discovery | P3_k3_context_gain | real_context_gain_k3 | corpus | Providence | 15.000 | -0.032 | -0.027 | 0.006 |

## Individual Child Trajectories

Point size reflects the number of utterances in the child-session-age cell. Adjusted outcomes remove the fitted exact/top-coded word-count effect and put every observation on the two-word reference scale. A child line is drawn only when the support rule is met (at least three distinct ages, six months of span, and 100 utterances).

| scope | dataset | child_id | distinct_ages | age_span | utterances | slope_supported | adjusted_k3_bits_2_words_slope_per_month | adjusted_context_gain_k3_2_words_slope_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | Brown | Adam | 55.000 | 35.267 | 45734.000 | 1.000 | -0.257 | -0.006 |
| pbm_discovery | Brown | Eve | 10.000 | 9.000 | 11676.000 | 1.000 | -0.791 | 0.010 |
| pbm_discovery | Brown | Sarah | 135.000 | 34.033 | 33625.000 | 1.000 | -0.083 | -0.034 |
| pbm_discovery | Manchester | Anne | 35.000 | 11.100 | 20693.000 | 1.000 | -0.394 | -0.063 |
| pbm_discovery | Manchester | Aran | 33.000 | 11.533 | 17565.000 | 1.000 | -0.496 | 0.017 |
| pbm_discovery | Manchester | Becky | 34.000 | 11.267 | 24407.000 | 1.000 | -0.557 | -0.012 |
| pbm_discovery | Manchester | Carl | 33.000 | 11.767 | 25620.000 | 1.000 | -0.517 | 0.029 |
| pbm_discovery | Manchester | Dominic | 35.000 | 11.700 | 21919.000 | 1.000 | -0.208 | -0.078 |
| pbm_discovery | Manchester | Gail | 34.000 | 11.500 | 17271.000 | 1.000 | -0.504 | -0.026 |
| pbm_discovery | Manchester | Joel | 35.000 | 11.334 | 18696.000 | 1.000 | -0.348 | -0.066 |
| pbm_discovery | Manchester | John | 32.000 | 11.300 | 13694.000 | 1.000 | -0.453 | -0.051 |
| pbm_discovery | Manchester | Liz | 34.000 | 11.300 | 16657.000 | 1.000 | -0.888 | -0.025 |
| pbm_discovery | Manchester | Nicole | 32.000 | 11.500 | 17152.000 | 1.000 | -0.121 | -0.039 |
| pbm_discovery | Manchester | Ruth | 33.000 | 12.200 | 20817.000 | 1.000 | -0.080 | -0.118 |
| pbm_discovery | Manchester | Warren | 36.000 | 11.467 | 17151.000 | 1.000 | -0.526 | -0.079 |
| pbm_discovery | Providence | Alex | 51.000 | 24.633 | 19090.000 | 1.000 | 0.094 | -0.085 |
| pbm_discovery | Providence | Ethan | 50.000 | 23.900 | 13588.000 | 1.000 | -0.037 | -0.021 |
| pbm_discovery | Providence | Lily | 77.000 | 35.000 | 28000.000 | 1.000 | -0.159 | -0.041 |
| pbm_discovery | Providence | Naima | 86.000 | 34.466 | 33738.000 | 1.000 | -0.422 | -0.040 |
| pbm_discovery | Providence | Violet | 49.000 | 33.800 | 10788.000 | 1.000 | -0.091 | -0.021 |
| pbm_discovery | Providence | William | 44.000 | 24.200 | 15967.000 | 1.000 | -0.046 | -0.072 |

### pbm_discovery

#### Brown

##### Brown/Adam

![Brown/Adam trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/brown_adam.png)

##### Brown/Eve

![Brown/Eve trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/brown_eve.png)

##### Brown/Sarah

![Brown/Sarah trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/brown_sarah.png)

#### Manchester

##### Manchester/Anne

![Manchester/Anne trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_anne.png)

##### Manchester/Aran

![Manchester/Aran trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_aran.png)

##### Manchester/Becky

![Manchester/Becky trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_becky.png)

##### Manchester/Carl

![Manchester/Carl trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_carl.png)

##### Manchester/Dominic

![Manchester/Dominic trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_dominic.png)

##### Manchester/Gail

![Manchester/Gail trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_gail.png)

##### Manchester/Joel

![Manchester/Joel trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_joel.png)

##### Manchester/John

![Manchester/John trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_john.png)

##### Manchester/Liz

![Manchester/Liz trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_liz.png)

##### Manchester/Nicole

![Manchester/Nicole trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_nicole.png)

##### Manchester/Ruth

![Manchester/Ruth trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_ruth.png)

##### Manchester/Warren

![Manchester/Warren trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/manchester_warren.png)

#### Providence

##### Providence/Alex

![Providence/Alex trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/providence_alex.png)

##### Providence/Ethan

![Providence/Ethan trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/providence_ethan.png)

##### Providence/Lily

![Providence/Lily trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/providence_lily.png)

##### Providence/Naima

![Providence/Naima trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/providence_naima.png)

##### Providence/Violet

![Providence/Violet trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/providence_violet.png)

##### Providence/William

![Providence/William trajectory](../figs/direct_surprisal_replication/tinydialogues_pbm/pbm_discovery/children/providence_william.png)

## Interpretation Boundary

PBM results are discovery/scorer-robustness results. A pooled 79-child estimate is descriptive. Only the separately reported non-PBM estimate is the frozen sample confirmation. Generated n-gram candidates are not same-meaning alternatives, and caretaker trajectories reflect input adaptation.

## Saved Artifacts

- Model summaries: `results/direct_surprisal_replication/tinydialogues_pbm/models/model_summaries.csv`
- Coefficients: `results/direct_surprisal_replication/tinydialogues_pbm/models/coefficients_long.csv`
- Prediction grid: `results/direct_surprisal_replication/tinydialogues_pbm/models/prediction_grid.csv`
- Child trajectories: `results/direct_surprisal_replication/tinydialogues_pbm/models/child_age_session_trajectories.csv.gz`
- Child slopes: `results/direct_surprisal_replication/tinydialogues_pbm/models/child_slope_summary.csv`
- Leave-one-cluster-out estimates: `results/direct_surprisal_replication/tinydialogues_pbm/models/leave_one_cluster_out.csv`
- Child profile audit: `results/direct_surprisal_replication/tinydialogues_pbm/models/child_profile_audit.csv`
