# Route 1 Candidate Evidence Gallery v0

This is **not** the supervisor report. It is a selectable gallery of promising Route 1 plots, checks, and exact effect sentences to inspect before deciding what goes into the supervisor-facing narrative.

## What This File Is For

- Pull the best candidates from every Route 1 Atlas/report family.
- Put actual plots next to literal one-line effect interpretations.
- Separate promising evidence from cautions and robustness checks.
- Make it easy to choose what to promote into the final supervisor report.

## Source Reports

- Real child Atlas v2: [utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html)
- Source-specific Atlas v2 index: [utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.html](utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.html)
- Heldout child prediction report: [utterance_information_route1_heldout_real_child_prediction_report.html](utterance_information_route1_heldout_real_child_prediction_report.html)
- Caretaker Atlas v2: [utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html)
- Age-scrambling robustness: [utterance_information_age_scrambling_robustness.html](utterance_information_age_scrambling_robustness.html)
- Technical model companion: [utterance_information_m1_m6_technical_implementation_companion.html](utterance_information_m1_m6_technical_implementation_companion.html)

## How To Read An Atlas Line

A fixed-effort Atlas line is a fitted regression prediction, not a raw average.

- **Downward age line:** at the same effort level, older children are predicted to carry less `sum_bits`.
- **Upward age line:** at the same effort level, older children are predicted to carry more `sum_bits`.
- **Separated effort bands:** longer utterances carry more total information, so effort must be controlled.
- **Actual-vs-predicted heldout line:** black is the real heldout trajectory; teal dashed is the PBM-trained model's predicted trajectory.

## Fast Pick List

| Use status | Candidate | Why |
| --- | --- | --- |
| Strong candidate | C01 Real child fixed-effort line | Cleanest Route 1 developmental story. |
| Strong candidate | C02 Source comparison | Shows real/random/generated baselines on same slope scale. |
| Strong candidate | C05 Age-scrambling robustness | Defends against age-bin composition artifacts. |
| Diagnostic candidate | C07 Heldout actual vs predicted | Direct generalization check, currently mixed. |
| Context bridge | C04 Context controls | Links to email confounds without overclaiming Route 2. |
| Contrast candidate | C09 Caretaker contrast | Helps show child result is not automatic in adult speech. |

## C01. Real child fixed-effort developmental line

**Artifact family:** Route 1 real-child Atlas v2

**What to inspect:** Start with the k3/M4c/words fixed-effort Atlas plot, because it controls child identity, effort, and broad question type.

**Effect one-liner:** age -> lower sum_bits at the same word count: M4c estimates -0.127 bits/month for real child speech.

**Variable importance / predictor relation:** Effort dominates the outcome, child identity matters, and M4c is the clean confound-control candidate among the simple Atlas v2 models.

**Why promising:** This is the cleanest Route 1 story candidate: developmental trend after effort and child identity are controlled.

**Caution before supervisor report:** Do not present it alone; pair it with source comparison and robustness cards so it is not just one fitted line.

![C01 real_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png)

![C01 real_k3_words_model_ladder_r2_importance.png](../figs/route1_candidate_evidence_gallery/real_k3_words_model_ladder_r2_importance.png)

| model | what changed | R2 | delta R2 vs M2 | age effect | effort effect | context entropy | context effort |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Pooled age + effort sanity check; not the main developmental claim. | 0.6130 | -0.0129 | 0.000 bits/month (p=0.993) | 6.35 bits/word (p=<.001) |  (p=) |  (p=) |
| M2 | Primary controlled line: age + effort with child identity fixed effects. | 0.6259 | 0.0000 | -0.122 bits/month (p=<.001) | 6.37 bits/word (p=<.001) |  (p=) |  (p=) |
| M3 | Checks whether the age line changes across effort levels. | 0.6259 | 0.0000 | -0.122 bits/month (p=<.001) | 6.38 bits/word (p=<.001) |  (p=) |  (p=) |
| M4a | Adds preceding caretaker/context effort as a confound control. | 0.6266 | 0.0007 | -0.116 bits/month (p=<.001) | 6.38 bits/word (p=<.001) |  (p=) | -0.070 (p=<.001) |
| M4b | Adds next-token context entropy as a contextual predictability control. | 0.6266 | 0.0007 | -0.126 bits/month (p=<.001) | 6.37 bits/word (p=<.001) | -0.471 (p=<.001) |  (p=) |
| M4c | Adds broad question type, a key context-form confound from the email. | 0.6297 | 0.0038 | -0.127 bits/month (p=<.001) | 6.38 bits/word (p=<.001) |  (p=) |  (p=) |
| M5 | Combines context effort, context entropy, and question type. | 0.6269 | 0.0009 | -0.122 bits/month (p=<.001) | 6.38 bits/word (p=<.001) | -0.468 (p=<.001) | -0.044 (p=<.001) |
| M6 | Tests whether context entropy changes the age/effort relation. | 0.6269 | 0.0010 | -0.123 bits/month (p=<.001) | 6.38 bits/word (p=<.001) | -0.469 (p=<.001) | -0.044 (p=<.001) |
| M15 | Richest current context-interaction stress test. | 0.6285 | 0.0026 | -0.127 bits/month (p=<.001) | 6.42 bits/word (p=<.001) | -0.321 (p=<.001) | -0.034 (p=<.001) |

| arrow | effect | number |
| --- | --- | --- |
| age ↓ | Older children carry less total information at the same word count, after child identity and question type are controlled. | -0.127 bits/month; p=<.001 |
| effort ↑ | Longer utterances carry much more information; this is the mechanical predictor we must hold fixed. | 6.38 bits per extra word; p=<.001 |
| age × effort ≈ flat | In real child speech, the age slope is not strongly different across word-count levels in this model. | -0.0038 bits/month/word; p=0.522 |
| context entropy ↓ | Next-token context entropy is a meaningful control here, but it is not the final Route 2 response-space entropy claim. | -0.469 bits; p=<.001 |
| parent context effort ↓ | Longer preceding caretaker context slightly lowers child utterance information at fixed child effort. | -0.044 bits/context word; p=<.001 |
| question type matters | Question/statement form improves fit, so it belongs as a confound before telling the developmental story. | M4c has the best simple k3/word R2 among the context-control candidates. |

## C02. Every source atlas on the same slope scale

**Artifact family:** Route 1 source-specific Atlas v2

**What to inspect:** Compare the fixed-effort M4c k3/word slopes across real, random, n-gram, and LSTM source atlases.

**Effect one-liner:** real child slopes go down; random slopes go up; n-gram/LSTM baselines mostly go down but differ by effort band.

**Variable importance / predictor relation:** This card is not a predictor-importance card; it is a baseline specificity check for the age slope.

**Why promising:** It shows the real-child line is not an artifact of using any generated target or of the plotting code.

**Caution before supervisor report:** Generated baselines are not psychological controls; use them as sanity checks, not as direct alternative children.

![C02 source_comparison_m4c_k3_words_slopes.png](../figs/route1_candidate_evidence_gallery/source_comparison_m4c_k3_words_slopes.png)

| source atlas | 1-4 words | 5-8 words | 9-12 words | plot | atlas |
| --- | --- | --- | --- | --- | --- |
| Real child | -0.76 | -0.85 | -0.95 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html) |
| Random | +1.03 | +1.24 | +1.46 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_random_corrected_fixed_effort_atlas_v2.html) |
| Unigram | -0.08 | -0.78 | -1.48 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_unigram_corrected_fixed_effort_atlas_v2.html) |
| Bigram | -0.10 | -0.69 | -1.28 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_bigram_corrected_fixed_effort_atlas_v2.html) |
| Trigram | -0.09 | -0.39 | -0.68 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_trigram_corrected_fixed_effort_atlas_v2.html) |
| LSTM k3 | -0.26 | -0.78 | -1.29 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_lstm_additive_k3_same_length_corrected_fixed_effort_atlas_v2.html) |
| LSTM k4 | -0.32 | -0.91 | -1.50 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_lstm_additive_k4_same_length_corrected_fixed_effort_atlas_v2.html) |
| LSTM k5 | -0.34 | -0.85 | -1.35 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_lstm_additive_k5_same_length_corrected_fixed_effort_atlas_v2.html) |

## C03. One selected plot from each source-specific Atlas

**Artifact family:** Real, random, unigram, bigram, trigram, LSTM k3/k4/k5 Atlas v2 reports

**What to inspect:** Use this as the visual menu: one M4c/k3/words fixed-effort plot per source-specific Atlas.

**Effect one-liner:** the same formula produces different age-line shapes depending on whether the target is real child speech or a baseline.

**Variable importance / predictor relation:** Formula is held constant here, so differences are about target source behavior, not model specification.

**Why promising:** This directly satisfies the 'pull from every atlas' requirement without burying you in hundreds of plots.

**Caution before supervisor report:** If one source looks interesting, open the full source Atlas before promoting it.

![C03 real_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 random_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 unigram_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 bigram_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 trigram_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

![C03 lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

| source atlas | 1-4 words | 5-8 words | 9-12 words | plot | atlas |
| --- | --- | --- | --- | --- | --- |
| Real child | -0.76 | -0.85 | -0.95 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html) |
| Random | +1.03 | +1.24 | +1.46 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_random_corrected_fixed_effort_atlas_v2.html) |
| Unigram | -0.08 | -0.78 | -1.48 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_unigram_corrected_fixed_effort_atlas_v2.html) |
| Bigram | -0.10 | -0.69 | -1.28 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_bigram_corrected_fixed_effort_atlas_v2.html) |
| Trigram | -0.09 | -0.39 | -0.68 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_trigram_corrected_fixed_effort_atlas_v2.html) |
| LSTM k3 | -0.26 | -0.78 | -1.29 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_lstm_additive_k3_same_length_corrected_fixed_effort_atlas_v2.html) |
| LSTM k4 | -0.32 | -0.91 | -1.50 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_lstm_additive_k4_same_length_corrected_fixed_effort_atlas_v2.html) |
| LSTM k5 | -0.34 | -0.85 | -1.35 | [plot](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png) | [html](utterance_information_route1_lstm_additive_k5_same_length_corrected_fixed_effort_atlas_v2.html) |

## C04. Context controls and confounds from the email

**Artifact family:** Context M1-M6 Atlas plus real Atlas v2

**What to inspect:** Check whether context entropy and context size change the age/effort story.

**Effect one-liner:** context entropy is a meaningful control in Route 1, but it is not yet the Route 2 claim about choosing utterance length.

**Variable importance / predictor relation:** In the real k3/word ladder, adding context controls changes R2 modestly compared with the effort and child-identity base.

**Why promising:** This is the bridge from the current Route 1 report to the email's stronger context-predictability story.

**Caution before supervisor report:** Do not overclaim optimization from this card; it controls context predictability but does not yet model effort choice.

![C04 k3_m6e_nb_words_fixed_effort_atlas.png](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_words_fixed_effort_atlas.png)

![C04 k3_m6es_nb_words_fixed_effort_atlas.png](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_words_fixed_effort_atlas.png)

![C04 pbm_real_k3_predictor_correlation_heatmap.png](../figs/route1_candidate_evidence_gallery/pbm_real_k3_predictor_correlation_heatmap.png)

| model | formula | R2 | age | target effort | context entropy | context size |
| --- | --- | --- | --- | --- | --- | --- |
| M4E | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 0.6266 | -0.127 (p=<.001) | 6.37 (p=<.001) | -0.472 (p=<.001) |  (p=) |
| M4ES | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 0.6268 | -0.123 (p=<.001) | 6.37 (p=<.001) | -0.470 (p=<.001) | -0.043 (p=<.001) |
| M6E | sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id) | 0.6266 | -0.127 (p=<.001) | 6.38 (p=<.001) | -0.473 (p=<.001) |  (p=) |
| M6ES | sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + age_c * context_size_c + target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id) | 0.6285 | -0.127 (p=<.001) | 6.42 (p=<.001) | -0.494 (p=<.001) | -0.035 (p=<.001) |

## C05. Age-scrambling and age-bin robustness

**Artifact family:** Age scrambling robustness report

**What to inspect:** Check whether observed age slopes sit outside shuffled or balanced-bootstrap age-label nulls.

**Effect one-liner:** the useful claim is not just 'a line exists'; it must be stronger than age-label artifacts.

**Variable importance / predictor relation:** Robustness varies by model; use the table to decide which model is sturdy enough for the supervisor report.

**Why promising:** This is the best defense against 'is this just age-bin composition?'

**Caution before supervisor report:** Some checks may be mixed; only promote models whose observed slope behaves well under the relevant null.

![C05 m2_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

![C05 m6_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png)

![C05 robustness_outside_null_heatmap.png](../figs/age_scrambling_robustness/robustness_outside_null_heatmap.png)

| model | check | observed age | null 95% interval | outside null? | p |
| --- | --- | --- | --- | --- | --- |
| M2 | Balanced age-bin bootstrap | -0.040 | [-0.168, -0.036] | False |  |
| M2 | Grouped age-bin label scramble | -0.040 | [-0.025, 0.028] | True | 0.010 |
| M2 | Unit-level age scramble | -0.040 | [-0.013, 0.013] | True | 0.010 |
| M2 | Within-child age scramble | -0.040 | [-0.020, 0.018] | True | 0.010 |
| M3 | Balanced age-bin bootstrap | -0.050 | [-0.186, -0.022] | False |  |
| M3 | Grouped age-bin label scramble | -0.050 | [-0.025, 0.027] | True | 0.010 |
| M3 | Unit-level age scramble | -0.050 | [-0.010, 0.012] | True | 0.010 |
| M3 | Within-child age scramble | -0.050 | [-0.020, 0.014] | True | 0.010 |
| M4 | Balanced age-bin bootstrap | -0.038 | [-0.186, 0.028] | False |  |
| M4 | Grouped age-bin label scramble | -0.038 | [-0.032, 0.037] | True | 0.020 |
| M4 | Unit-level age scramble | -0.038 | [-0.010, 0.010] | True | 0.010 |
| M4 | Within-child age scramble | -0.038 | [-0.020, 0.025] | True | 0.010 |
| M5 | Balanced age-bin bootstrap | -0.033 | [-0.181, 0.022] | False |  |
| M5 | Grouped age-bin label scramble | -0.033 | [-0.032, 0.030] | True | 0.059 |
| M5 | Unit-level age scramble | -0.033 | [-0.014, 0.013] | True | 0.010 |
| M5 | Within-child age scramble | -0.033 | [-0.013, 0.026] | True | 0.010 |
| M6 | Balanced age-bin bootstrap | -0.058 | [-0.113, 0.020] | False |  |
| M6 | Grouped age-bin label scramble | -0.058 | [-0.044, 0.033] | True | 0.030 |
| M6 | Unit-level age scramble | -0.058 | [-0.012, 0.012] | True | 0.010 |
| M6 | Within-child age scramble | -0.058 | [-0.018, 0.022] | True | 0.010 |

## C06. Estimator-family checks: OLS, GEE, GLM, MixedLM

**Artifact family:** M1/M2/M3 deep dive

**What to inspect:** Compare adjusted age lines across OLS with fixed effects, clustered SE, GEE, GLM, and mixed-effects variants.

**Effect one-liner:** the candidate age story is stronger if the line direction does not depend on one estimator.

**Variable importance / predictor relation:** Old deep-dive delta-R2 shows effort explains far more raw variance than age, which is exactly why fixed-effort plotting is necessary.

**Why promising:** This gives the methods backup: the story is not just a single OLS table.

**Caution before supervisor report:** Use these as checks/appendix material unless a model-family contrast becomes central.

![C06 m2_ols_child_fe_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png)

![C06 m2_mixed_random_age_slope_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_age_slope_adjusted_age_lines.png)

![C06 m3_gee_gaussian_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_adjusted_age_lines.png)

![C06 m1_m2_delta_r2_variable_importance.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png)

| model_id | model_label | effort_col | effort_label | importance_term | full_r2 | reduced_r2 | delta_r2_when_dropped |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | M1: age + effort | nb_words | Words | Words | 0.6129770457378894 | 0.0450766913754767 | 0.5679003543624126 |
| M1 | M1: age + effort | nb_words | Words | Age in months | 0.6129770457378894 | 0.612977023580856 | 2.2157033319203382e-08 |
| M2 | M2: age + effort + child identity | nb_words | Words | Words | 0.6259086571579606 | 0.0924273121982121 | 0.5334813449597485 |
| M2 | M2: age + effort + child identity | nb_words | Words | Child identity | 0.6259086571579606 | 0.6129770457378894 | 0.0129316114200712 |
| M2 | M2: age + effort + child identity | nb_words | Words | Age in months | 0.6259086571579606 | 0.6240329079059622 | 0.0018757492519984 |

## C07. Heldout children: actual regression line vs predicted regression line

**Artifact family:** Heldout real child prediction report

**What to inspect:** Black dots/line are actual heldout child monthly data; teal dashed line is PBM-trained prediction at the same child and effort band.

**Effect one-liner:** this asks whether a PBM-trained Route 1 model predicts the shape of unseen children's information trajectories.

**Variable importance / predictor relation:** Prediction uses population PBM models because heldout children cannot use child fixed effects learned from themselves.

**Why promising:** This is the generalization check you wanted: actual line and predicted line are literally in the same panel.

**Caution before supervisor report:** Current heldout fixed-effort slopes are mixed by child and band, so this is a diagnostic candidate, not yet the cleanest proof.

![C07 heldout_pop_m4c_actual_vs_predicted_regression_lines.png](../figs/route1_candidate_evidence_gallery/heldout_pop_m4c_actual_vs_predicted_regression_lines.png)

![C07 heldout_pop_m4c_calibration_residuals.png](../figs/route1_candidate_evidence_gallery/heldout_pop_m4c_calibration_residuals.png)

| child_key | effort_band | actual_slope_bits_per_month | predicted_slope_bits_per_month | actual_month_points |
| --- | --- | --- | --- | --- |
| Forrester/Ella | 1-4 | 0.0270012292327988 | -0.0140398757396908 | 25 |
| Forrester/Ella | 5-8 | -0.4186608170105513 | -0.0002467981761615 | 25 |
| Forrester/Ella | 9-12 | -1.2387577536068777 | 0.0135462793873675 | 14 |
| Sachs/Naomi | 1-4 | 0.1146939748090093 | -0.0140398757396904 | 24 |
| Sachs/Naomi | 5-8 | 0.0282044151825889 | -0.0002467981761605 | 21 |
| Sachs/Naomi | 9-12 | 0.8291591365210335 | 0.0135462793873688 | 14 |
| MPI-EVA-Manchester/Helen | 1-4 | 0.0475976291643852 | -0.0140398757396904 | 26 |
| MPI-EVA-Manchester/Helen | 5-8 | -0.0824757391384523 | -0.0002467981761613 | 26 |
| MPI-EVA-Manchester/Helen | 9-12 | -0.069148974089826 | 0.013546279387368 | 26 |

## C08. Heldout child selection coverage

**Artifact family:** Heldout child selection/corpus coverage

**What to inspect:** Use this only to explain why Ella, Naomi, and Helen were selected.

**Effect one-liner:** the selected three children cover a broad month range while staying outside the PBM training set.

**Variable importance / predictor relation:** No predictor importance; this is a sampling/support argument.

**Why promising:** It prevents the heldout section from looking arbitrary.

**Caution before supervisor report:** This belongs before prediction results, not as evidence of communicative efficiency.

![C08 heldout_selection_pbm_corpus_coverage.png](../figs/route1_heldout_real_child_prediction/heldout_selection_pbm_corpus_coverage.png)

![C08 pbm_reference_and_heldout_candidate_options.png](../figs/big_cleaned_dataset/default_naturalistic_merged_006_023/pbm_reference_and_heldout_candidate_options.png)

## C09. Caretaker contrast

**Artifact family:** Caretaker Route 1 Atlas v2

**What to inspect:** Compare parent/caretaker fixed-effort age lines to the child lines.

**Effect one-liner:** caretaker information does not show the same clean child-age downward story after dyad and effort controls.

**Variable importance / predictor relation:** Caretaker effort dominates caretaker sum_bits; child age is weak or model-dependent in the selected k3/word controls.

**Why promising:** This makes the child result more interpretable: the developmental pattern is not automatically present for adult speech in the same sessions.

**Caution before supervisor report:** The caretaker report answers a different question: adult speech as a function of child age, not adult language development.

![C09 caretaker_k3_cm2_nb_words_fixed_effort_atlas.png](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_words_fixed_effort_atlas.png)

![C09 caretaker_k3_cm6_nb_words_fixed_effort_atlas.png](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_words_fixed_effort_atlas.png)

| model | formula | R2 | age effect | effort effect | context effort | age x effort |
| --- | --- | --- | --- | --- | --- | --- |
| CM2 | caretaker_sum_bits ~ child_age_c + caretaker_effort_c + C(dyad_child_id) | 0.6607 | 0.029 bits/month (p=0.274) | 4.74 bits/word (p=<.001) |  (p=) |  (p=) |
| CM3 | caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) | 0.6607 | 0.028 bits/month (p=0.266) | 4.74 bits/word (p=<.001) |  (p=) | 0.0018 (p=0.722) |
| CM4c | caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) + C(question_type) | 0.6624 | 0.025 bits/month (p=0.325) | 4.74 bits/word (p=<.001) |  (p=) | 0.0019 (p=0.703) |
| CM6 | caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) + preceding_context_caretaker_effort_c + C(question_type) + child_age_c:preceding_context_caretaker_effort_c + caretaker_effort_c:preceding_context_caretaker_effort_c | 0.6716 | 0.048 bits/month (p=0.065) | 4.90 bits/word (p=<.001) | -0.169 (p=<.001) | 0.0058 (p=0.286) |

## C10. Child vs caretaker size-controlled descriptive contrast

**Artifact family:** Meeting size-controlled plots

**What to inspect:** Use these as descriptive support before or after the model-based child/caretaker contrast.

**Effect one-liner:** child and caretaker information differ even when utterance size is held constant descriptively.

**Variable importance / predictor relation:** No model predictor importance; this is a descriptive exact-size comparison.

**Why promising:** It is easy to understand visually and may help introduce why fixed effort matters.

**Caution before supervisor report:** It is not a substitute for the regression-controlled Atlas result.

![C10 exact_words_child_vs_caretaker.png](../figs/meeting_size_controlled_plots/exact_words_child_vs_caretaker.png)

![C10 child_vs_caretaker_bits_per_word_by_size.png](../figs/meeting_size_controlled_plots/child_vs_caretaker_bits_per_word_by_size.png)

## Model Card Menu: M1-M15

These are implementation-level cards from the current Route 1 Atlas v2 ladder. I do **not** find a real implemented M16 artifact in the current ladder, so this gallery does not invent one.

| model | question | formula | plain-language role |
| --- | --- | --- | --- |
| M1 | Does age predict target information after controlling target effort, pooling children? | sum_bits ~ age + effort | Pooled age + effort sanity check; not the main developmental claim. |
| M2 | Does the age effect remain after child identity is controlled? | sum_bits ~ age + effort + C(child_id) | Primary controlled line: age + effort with child identity fixed effects. |
| M3 | Does the effort-information relation change with age? | sum_bits ~ age * effort + C(child_id) | Checks whether the age line changes across effort levels. |
| M4a | Does preceding caretaker effort explain additional target information? | sum_bits ~ age * effort + parent_context_effort + C(child_id) | Adds preceding caretaker/context effort as a confound control. |
| M4b | Does context entropy explain additional target information? | sum_bits ~ age * effort + context_entropy + C(child_id) | Adds next-token context entropy as a contextual predictability control. |
| M4c | Does preceding caretaker question type explain additional target information? | sum_bits ~ age * effort + C(question_type) + C(child_id) | Adds broad question type, a key context-form confound from the email. |
| M5 | Do parent effort, context entropy, and question type each matter after age, target effort, and child identity? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + C(child_id) | Combines context effort, context entropy, and question type. |
| M6 | Does context-entropy sensitivity change with age or target effort? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:context_entropy + effort:context_entropy + C(child_id) | Tests whether context entropy changes the age/effort relation. |
| M7 | Does a curved age trajectory explain target information beyond linear age and effort? | sum_bits ~ age + effort + I(age ** 2) + C(child_id) | Nonlinear age check: age plus age squared. |
| M8 | Does the effort-information relation change along a curved age trajectory? | sum_bits ~ age * effort + I(age ** 2) + I(age ** 2):effort + C(child_id) | Nonlinear age-by-effort check. |
| M9 | Do age-bin differences remain after target effort and child identity are controlled? | sum_bits ~ C(age_bin) + effort + C(child_id) | Categorical age-bin check rather than one straight age slope. |
| M10 | Does the effort-information relation differ across developmental age bins? | sum_bits ~ C(age_bin) * effort + C(child_id) | Age-bin-by-effort check. |
| M11 | Does preceding caretaker effort matter differently across development? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:parent_context_effort + C(child_id) | Age-by-parent-context-effort interaction check. |
| M12 | Does the developmental trajectory differ by broad preceding caretaker question type? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:C(question_type) + C(child_id) | Age-by-question-type interaction check. |
| M13 | Does context entropy matter differently after different broad caretaker question types? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + context_entropy:C(question_type) + C(child_id) | Context-entropy-by-question-type interaction check. |
| M14 | Do context entropy and preceding caretaker effort jointly predict target information? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + parent_context_effort:context_entropy + C(child_id) | Parent-context-effort-by-context-entropy interaction check. |
| M15 | Do the main context controls alter the age-effort trajectory under a larger interaction stress test? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:context_entropy + effort:context_entropy + age:parent_context_effort + effort:parent_context_effort + context_entropy:C(question_type) + C(child_id) | Richest current context-interaction stress test. |

## Effect Sentence Menu

| arrow | effect | number |
| --- | --- | --- |
| age ↓ | Older children carry less total information at the same word count, after child identity and question type are controlled. | -0.127 bits/month; p=<.001 |
| effort ↑ | Longer utterances carry much more information; this is the mechanical predictor we must hold fixed. | 6.38 bits per extra word; p=<.001 |
| age × effort ≈ flat | In real child speech, the age slope is not strongly different across word-count levels in this model. | -0.0038 bits/month/word; p=0.522 |
| context entropy ↓ | Next-token context entropy is a meaningful control here, but it is not the final Route 2 response-space entropy claim. | -0.469 bits; p=<.001 |
| parent context effort ↓ | Longer preceding caretaker context slightly lowers child utterance information at fixed child effort. | -0.044 bits/context word; p=<.001 |
| question type matters | Question/statement form improves fit, so it belongs as a confound before telling the developmental story. | M4c has the best simple k3/word R2 among the context-control candidates. |

## Saved Artifacts

```text
results/route1_candidate_evidence_gallery/candidate_evidence_cards.csv
results/route1_candidate_evidence_gallery/selected_source_atlas_cards.csv
results/route1_candidate_evidence_gallery/selected_caretaker_k3_words_models.csv
results/route1_candidate_evidence_gallery/selected_age_scrambling_robustness_k3_words.csv
results/route1_candidate_evidence_gallery/selected_old_deep_dive_variable_importance_words.csv
results/route1_candidate_evidence_gallery/selected_context_m1_m6_k3_words_models.csv
results/route1_candidate_evidence_gallery/heldout_pop_m4c_actual_vs_predicted_regression_slopes.csv
results/route1_candidate_evidence_gallery/pbm_real_k3_predictor_correlations.csv
results/route1_candidate_evidence_gallery/source_comparison_m4c_k3_words_slopes.csv
figs/route1_candidate_evidence_gallery
```
