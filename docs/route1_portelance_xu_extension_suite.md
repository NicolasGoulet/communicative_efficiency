# Portelance/Xu Communicative-Efficiency Extension Suite

This is a sidecar analysis package for choosing paper-ready analyses. It does not modify the current supervisor-facing report.

The suite translates the Portelance/Xu discussion and the Pawar/Cychosz frequency-informativity template into concrete checks: effort as an outcome, frequency controls, adult-likeness/caretaker distance, equalized sampling, scrambled-age nulls, and effort-information tradeoff plots.

## Why These Analyses Matter

- **For Prof. Portelance:** these analyses connect the CHILDES/Mistral work to communicative efficiency as a tradeoff between informativeness, effort, and listener/learner context.
- **For Prof. Xu:** they operationalize the two-route framing: Route 1 asks about information at fixed effort; Route 2 asks whether context predicts effort itself.
- **For peer reviewers:** the suite adds controls for frequency, context effort, question type, unequal age-bin sampling, age-label artifacts, and adult/caretaker comparison baselines.

## Feature Status

| feature | status | artifact | peer_review_reason |
| --- | --- | --- | --- |
| Context uncertainty | implemented | context_entropy_bits in analysis rows | Tests whether effort/information effects are actually context-sensitive. |
| Context effort | implemented | context_effort_words | Controls for the amount of preceding caregiver material. |
| Question type | implemented, coarse | question_type | Questions can mechanically elicit different child response lengths. |
| Exact target recurrence / frequency bits | implemented | exact_target_frequency_bits from hash_frequency_predictors.csv.gz | Separates age effects from children/caretakers using more repeated conventional utterances. |
| Word-unigram and phone-bigram informativity | implemented in code, not full-run completed here | src/build_route1_frequency_informativity_predictors.py --mode text | Closest analogue to Pawar/Cychosz frequency-vs-informativity controls; full run needs a safer long text pass. |
| Full response-space entropy | pilot-only, not full scored | response_entropy pilot reports | Would directly quantify uncertainty over possible child responses, but full Mila-scale generation is still a separate run. |

## Main Status

- Implemented now: Route 2 effort models, exact-frequency Route 1 controls, adult-likeness plots, effort-information tradeoff plots, equalized bootstraps, scrambled-age nulls.
- Implemented as proxy now: exact target recurrence/frequency bits. This is the stable first frequency-control layer.
- Route 2 effort models are real-child models in this build. The finite k3 context-entropy row extract contains real child rows; caretaker/adult-likeness comparisons are still implemented through the fixed-effort ANCOVA artifacts.
- Equalized bootstrap plots use only age bins with at least 1,000 prepared rows, then sample up to 4,000 rows per included age bin. This avoids letting the sparse `060-065` context-entropy coverage force all bins down to 10 rows.
- Not fully scored now: full response-space entropy and full text/phone informativity predictors. The code path exists for text/phone predictors, but a full safe text pass remains a separate long run.

### Analysis Row Coverage

| source_label | 006-023 | 024-029 | 030-035 | 036-041 | 042-047 | 048-053 | 054-059 | 060-065 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Real child | 62,737 | 161,909 | 141,479 | 36,874 | 16,065 | 12,632 | 9,707 | 10 |

## Figure Gallery

### Route 2 Effort Outcome

#### Route 2 predicted words by context uncertainty

**Why this matters:** Tests the Portelance/Xu question of whether children modulate production effort according to how uncertain the preceding context is.

![Route 2 predicted words by context uncertainty](../figs/route1_portelance_xu_extension_suite/route2_predicted_nb_words_by_context_uncertainty.png)

#### Route 2 predicted morphemes by context uncertainty

**Why this matters:** Tests the Portelance/Xu question of whether children modulate production effort according to how uncertain the preceding context is.

![Route 2 predicted morphemes by context uncertainty](../figs/route1_portelance_xu_extension_suite/route2_predicted_nb_morphemes_by_context_uncertainty.png)

#### Route 2 predicted syllables: cmu/pkg by context uncertainty

**Why this matters:** Tests the Portelance/Xu question of whether children modulate production effort according to how uncertain the preceding context is.

![Route 2 predicted syllables: cmu/pkg by context uncertainty](../figs/route1_portelance_xu_extension_suite/route2_predicted_nb_syllables_cmu_or_pkg_by_context_uncertainty.png)

#### Route 2 predicted syllables: pkg by context uncertainty

**Why this matters:** Tests the Portelance/Xu question of whether children modulate production effort according to how uncertain the preceding context is.

![Route 2 predicted syllables: pkg by context uncertainty](../figs/route1_portelance_xu_extension_suite/route2_predicted_nb_syllables_pkg_by_context_uncertainty.png)

#### Route 2 predicted phonemes by context uncertainty

**Why this matters:** Tests the Portelance/Xu question of whether children modulate production effort according to how uncertain the preceding context is.

![Route 2 predicted phonemes by context uncertainty](../figs/route1_portelance_xu_extension_suite/route2_predicted_nb_phonemes_by_context_uncertainty.png)

#### Route 2 context-uncertainty coefficients

**Why this matters:** A positive context-uncertainty coefficient means higher contextual uncertainty predicts longer/more effortful productions, directly testing effort modulation.

![Route 2 context-uncertainty coefficients](../figs/route1_portelance_xu_extension_suite/route2_context_uncertainty_coefficients.png)

### Frequency-Controlled Route 1

#### Route 1 age coefficients with context/frequency controls

**Why this matters:** Shows whether the fixed-effort developmental effect survives controls motivated by frequency/informativity peer-review concerns.

![Route 1 age coefficients with context/frequency controls](../figs/route1_portelance_xu_extension_suite/route1_age_coefficients_with_context_frequency_controls.png)

#### Joint model incremental fit

**Why this matters:** Addresses the joint-inference idea: context and frequency should be evaluated together rather than as isolated single predictors.

![Joint model incremental fit](../figs/route1_portelance_xu_extension_suite/route1_joint_model_delta_r2.png)

### Adult-Likeness / Caretaker Distance

#### Caretaker-minus-real with-context information

**Why this matters:** Makes the adult-likeness claim explicit by tracking the signed distance between child behavior and caretaker behavior.

![Caretaker-minus-real with-context information](../figs/route1_portelance_xu_extension_suite/adult_likeness_caretaker_minus_real_sum_bits_k3.png)

#### Caretaker-minus-real context gain

**Why this matters:** Makes the adult-likeness claim explicit by tracking the signed distance between child behavior and caretaker behavior.

![Caretaker-minus-real context gain](../figs/route1_portelance_xu_extension_suite/adult_likeness_caretaker_minus_real_context_gain.png)

### Efficiency Tradeoff

#### Effort-information tradeoff space (Words)

**Why this matters:** Connects the project to communicative-efficiency theory by showing the observed effort/information region occupied by real children, controls, LSTMs, and caretakers.

![Effort-information tradeoff space (Words)](../figs/route1_portelance_xu_extension_suite/effort_information_tradeoff_nb_words.png)

#### Effort-information tradeoff space (Phonemes)

**Why this matters:** Connects the project to communicative-efficiency theory by showing the observed effort/information region occupied by real children, controls, LSTMs, and caretakers.

![Effort-information tradeoff space (Phonemes)](../figs/route1_portelance_xu_extension_suite/effort_information_tradeoff_nb_phonemes.png)

### Equalized Sampling

#### Equalized bootstrap: Bits per word

**Why this matters:** Follows the Pawar/Cychosz-style sampling concern: age trajectories should not be artifacts of unequal data volume across bins.

![Equalized bootstrap: Bits per word](../figs/route1_portelance_xu_extension_suite/equalized_bootstrap_bits_per_word.png)

#### Equalized bootstrap: Bits per phoneme

**Why this matters:** Follows the Pawar/Cychosz-style sampling concern: age trajectories should not be artifacts of unequal data volume across bins.

![Equalized bootstrap: Bits per phoneme](../figs/route1_portelance_xu_extension_suite/equalized_bootstrap_bits_per_phoneme.png)

#### Equalized bootstrap: Exact-target frequency bits

**Why this matters:** Follows the Pawar/Cychosz-style sampling concern: age trajectories should not be artifacts of unequal data volume across bins.

![Equalized bootstrap: Exact-target frequency bits](../figs/route1_portelance_xu_extension_suite/equalized_bootstrap_exact_target_frequency_bits.png)

#### Equalized bootstrap: Context entropy bits

**Why this matters:** Follows the Pawar/Cychosz-style sampling concern: age trajectories should not be artifacts of unequal data volume across bins.

![Equalized bootstrap: Context entropy bits](../figs/route1_portelance_xu_extension_suite/equalized_bootstrap_context_entropy_bits.png)

### Scrambled-Age Robustness

#### Scrambled-age null check: with-context information

**Why this matters:** Peer-review guardrail: developmental slopes should stand apart from age-label scrambling, not merely reflect binning or sampling structure.

![Scrambled-age null check: with-context information](../figs/route1_portelance_xu_extension_suite/scrambled_age_null_sum_bits_k3.png)

#### Scrambled-age null check: context gain

**Why this matters:** Peer-review guardrail: developmental slopes should stand apart from age-label scrambling, not merely reflect binning or sampling structure.

![Scrambled-age null check: context gain](../figs/route1_portelance_xu_extension_suite/scrambled_age_null_context_gain.png)

## Compact Tables

### Route 2 Context-Uncertainty Coefficients

Positive coefficients mean that more uncertain contexts predict more production effort. These are log-effort outcomes, so the sign is the key first reading.

| source_label | effort_label | coef | p | nobs |
| --- | --- | --- | --- | --- |
| Real child | Words | 0.002 | 0.428 | 81,717 |
| Real child | Morphemes | 0.004 | 0.134 | 81,717 |
| Real child | Syllables: CMU/pkg | 0.006 | 0.005 | 81,717 |
| Real child | Syllables: pkg | 0.007 | 0.002 | 81,717 |
| Real child | Phonemes | 0.009 | <.001 | 81,717 |

### Route 1 Joint Model Summary

The age coefficient is the fixed-effort developmental signal after adding context/frequency controls. `delta_r2_vs_base` shows what each added predictor family contributes over the base effort+child model.

| model_id | effort_label | age_coef | age_p | r2 | delta_r2_vs_base |
| --- | --- | --- | --- | --- | --- |
| base_effort_child | Words | -0.732 | 0.005 | 0.660 | 0.0000 |
| context_controls | Words | -0.662 | 0.014 | 0.661 | 8.32e-04 |
| frequency_control | Words | -0.572 | <.001 | 0.691 | 0.0308 |
| joint_context_frequency | Words | -0.511 | 0.002 | 0.691 | 0.0316 |
| joint_interactions | Words | -0.506 | 0.004 | 0.692 | 0.0320 |
| base_effort_child | Morphemes | -1.038 | <.001 | 0.652 | 0.0000 |
| context_controls | Morphemes | -0.970 | <.001 | 0.653 | 9.21e-04 |
| frequency_control | Morphemes | -0.811 | <.001 | 0.682 | 0.0300 |
| joint_context_frequency | Morphemes | -0.752 | <.001 | 0.683 | 0.0309 |
| joint_interactions | Morphemes | -0.744 | 0.002 | 0.683 | 0.0313 |
| base_effort_child | Syllables: CMU/pkg | -0.360 | 0.041 | 0.677 | 0.0000 |
| context_controls | Syllables: CMU/pkg | -0.302 | 0.086 | 0.678 | 8.37e-04 |
| frequency_control | Syllables: CMU/pkg | -0.258 | 0.033 | 0.701 | 0.0235 |
| joint_context_frequency | Syllables: CMU/pkg | -0.206 | 0.067 | 0.702 | 0.0244 |
| joint_interactions | Syllables: CMU/pkg | -0.203 | 0.166 | 0.702 | 0.0250 |
| base_effort_child | Syllables: pkg | -0.278 | 0.099 | 0.663 | 0.0000 |
| context_controls | Syllables: pkg | -0.221 | 0.181 | 0.664 | 8.49e-04 |
| frequency_control | Syllables: pkg | -0.173 | 0.181 | 0.689 | 0.0255 |
| joint_context_frequency | Syllables: pkg | -0.123 | 0.287 | 0.689 | 0.0265 |
| joint_interactions | Syllables: pkg | -0.119 | 0.488 | 0.690 | 0.0273 |
| base_effort_child | Phonemes | -0.493 | 0.028 | 0.672 | 0.0000 |
| context_controls | Phonemes | -0.434 | 0.048 | 0.673 | 9.17e-04 |
| frequency_control | Phonemes | -0.353 | 0.040 | 0.692 | 0.0200 |
| joint_context_frequency | Phonemes | -0.301 | 0.059 | 0.693 | 0.0210 |
| joint_interactions | Phonemes | -0.296 | 0.146 | 0.694 | 0.0218 |

### Scrambled-Age Null Summary

Observed slopes should sit outside or near the edge of scrambled-age null intervals if the developmental effect is not just an age-bin/sampling artifact.

| source_label | effort_label | outcome | observed_slope_per_6mo | null_lo | null_hi | empirical_p |
| --- | --- | --- | --- | --- | --- | --- |
| Caretaker | Words | sum_bits_k3 | 0.087 | -0.027 | 0.028 | 0.020 |
| Caretaker | Words | context_gain | -0.414 | -0.020 | 0.016 | 0.020 |
| Real child | Words | sum_bits_k3 | -0.560 | -0.050 | 0.042 | 0.020 |
| Real child | Words | context_gain | -0.172 | -0.024 | 0.024 | 0.020 |
| Caretaker | Morphemes | sum_bits_k3 | 0.137 | -0.019 | 0.035 | 0.020 |
| Caretaker | Morphemes | context_gain | -0.407 | -0.023 | 0.034 | 0.020 |
| Real child | Morphemes | sum_bits_k3 | -0.611 | -0.046 | 0.051 | 0.020 |
| Real child | Morphemes | context_gain | -0.204 | -0.032 | 0.026 | 0.020 |
| Caretaker | Syllables: CMU/pkg | sum_bits_k3 | 0.067 | -0.021 | 0.020 | 0.020 |
| Caretaker | Syllables: CMU/pkg | context_gain | -0.415 | -0.026 | 0.016 | 0.020 |
| Real child | Syllables: CMU/pkg | sum_bits_k3 | -0.292 | -0.052 | 0.029 | 0.020 |
| Real child | Syllables: CMU/pkg | context_gain | -0.134 | -0.028 | 0.017 | 0.020 |
| Caretaker | Syllables: pkg | sum_bits_k3 | 0.074 | -0.024 | 0.016 | 0.020 |
| Caretaker | Syllables: pkg | context_gain | -0.414 | -0.028 | 0.026 | 0.020 |
| Real child | Syllables: pkg | sum_bits_k3 | -0.218 | -0.049 | 0.039 | 0.020 |
| Real child | Syllables: pkg | context_gain | -0.133 | -0.021 | 0.024 | 0.020 |
| Caretaker | Phonemes | sum_bits_k3 | 0.067 | -0.015 | 0.022 | 0.020 |
| Caretaker | Phonemes | context_gain | -0.422 | -0.019 | 0.022 | 0.020 |
| Real child | Phonemes | sum_bits_k3 | -0.295 | -0.033 | 0.032 | 0.020 |
| Real child | Phonemes | context_gain | -0.163 | -0.026 | 0.021 | 0.020 |

## Saved Artifacts

```text
results/route1_portelance_xu_extension_suite/portelance_xu_k3_real_caretaker_analysis_rows.csv.gz
results/route1_portelance_xu_extension_suite/route2_effort_outcome_coefficients.csv
results/route1_portelance_xu_extension_suite/route2_effort_outcome_predictions.csv
results/route1_portelance_xu_extension_suite/route1_joint_model_coefficients.csv
results/route1_portelance_xu_extension_suite/route1_joint_model_summary.csv
results/route1_portelance_xu_extension_suite/equalized_age_bootstrap_samples.csv.gz
results/route1_portelance_xu_extension_suite/equalized_age_bootstrap_summary.csv
results/route1_portelance_xu_extension_suite/scrambled_age_null_slopes.csv
results/route1_portelance_xu_extension_suite/adult_likeness_caretaker_minus_real_adjusted_gaps.csv
results/route1_portelance_xu_extension_suite/adult_likeness_route2_context_entropy_coefficient_distance.csv
results/route1_portelance_xu_extension_suite/feature_status_for_peer_review.csv
results/route1_portelance_xu_extension_suite/figure_manifest.csv
```
