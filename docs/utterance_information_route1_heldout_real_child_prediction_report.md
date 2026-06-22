# Heldout Real-Child Trajectory Prediction Report

This is the out-of-child robustness check: can models trained only on the scored PBM universe predict the real `sum_bits` trajectories of three unseen children?

The heldout children are `Forrester/Ella`, `Sachs/Naomi`, and `MPI-EVA-Manchester/Helen`. They were not part of the scored PBM training universe used for the Route 1 Atlas v2 model fits.

## 1. Why These Three Children

We selected the smallest non-PBM set that gives broad month coverage across the child-language age range while staying small enough to score and inspect carefully. The plot below deliberately shows PBM at the corpus level only, then each heldout child and the heldout union.

![Heldout coverage](../figs/route1_heldout_real_child_prediction/heldout_selection_pbm_corpus_coverage.png)

Read: the PBM rows show the training/scored universe by corpus; the heldout rows show why Ella, Naomi, and Helen are complementary. Ella covers early through late ages, Naomi fills much of the early/middle trajectory, and Helen densely covers the later months. Their union covers 50 integer months from 12 to 61 months.

## 2. Prediction Design

- Training data: PBM real-child scored rows from the Route 1 analysis dataset.
- Test data: heldout real utterances for Ella, Naomi, and Helen, scored on the PC and rsynced locally.
- Outcome: `sum_bits`, total information in the real child utterance.
- Estimator: `statsmodels.formula.api.ols` linear regression.
- Prediction target: population-level out-of-child prediction. `C(child_id)` fixed-effect models are not used for the main heldout prediction because a brand-new child has no fitted child intercept.
- Child adjustment used where possible: Mundlak-style within/between age models, which can predict unseen children because they use the child mean age rather than a child-specific intercept.
- Current predictor boundary: `context_entropy_bits` and response-space entropy are not yet computed for the heldout contexts, so entropy-dependent Atlas models are explicitly withheld from this report.

Models fit for this report:

| model_id | model | atlas analogue | formula |
| --- | --- | --- | --- |
| POP_M1 | Population age + effort | M1 without child fixed effects | sum_bits ~ age_c + effort_c |
| POP_M3 | Population age x effort | M3 without child fixed effects | sum_bits ~ age_c * effort_c |
| POP_M4A | Population age x effort + parent-context effort | M4a without child fixed effects | sum_bits ~ age_c * effort_c + parent_context_effort_c |
| POP_M4C | Population age x effort + question type | M4c without child fixed effects | sum_bits ~ age_c * effort_c + C(question_type) |
| POP_M7 | Population nonlinear age | M7 without child fixed effects | sum_bits ~ age_c + effort_c + I(age_c ** 2) |
| POP_M8 | Population nonlinear age x effort | M8 without child fixed effects | sum_bits ~ age_c * effort_c + I(age_c ** 2) + I(age_c ** 2):effort_c |
| MUND_M1 | Mundlak within/between age + effort | child-coverage-adjusted M1-like model | sum_bits ~ age_within_child_c + child_mean_age_c + effort_c |
| MUND_M3 | Mundlak within-age x effort | child-coverage-adjusted M3-like model | sum_bits ~ age_within_child_c * effort_c + child_mean_age_c |

## 3. Overall Heldout Prediction Metrics

The compact table below summarizes the main k3/word-count comparison across the three children. Lower MAE/RMSE is better; slope-sign matches count how many of the three children have the same actual and predicted developmental direction.

| model_id | model_label | mean_mae | mean_rmse | mean_corr | slope_sign_matches | child_rows |
| --- | --- | --- | --- | --- | --- | --- |
| POP_M4C | Population age x effort + question type | 9.709 | 13.525 | 0.766 | 3 | 3 |
| POP_M1 | Population age + effort | 9.784 | 13.585 | 0.762 | 3 | 3 |
| POP_M4A | Population age x effort + parent-context effort | 9.794 | 13.603 | 0.763 | 3 | 3 |
| POP_M8 | Population nonlinear age x effort | 9.851 | 13.604 | 0.762 | 3 | 3 |
| POP_M3 | Population age x effort | 9.789 | 13.605 | 0.762 | 3 | 3 |
| POP_M7 | Population nonlinear age | 9.867 | 13.636 | 0.761 | 3 | 3 |
| MUND_M1 | Mundlak within/between age + effort | 10.233 | 14.013 | 0.760 | 3 | 3 |
| MUND_M3 | Mundlak within-age x effort | 10.231 | 14.015 | 0.762 | 3 | 3 |

Full fit summary: `results/route1_heldout_real_child_prediction/heldout_prediction_fit_summary.csv`
Full metrics: `results/route1_heldout_real_child_prediction/heldout_prediction_metrics.csv`

## 4. Actual vs Predicted Trajectories

These plots use each child's actual heldout utterances and compare monthly mean actual `sum_bits` to monthly mean PBM-model predictions. This is not fixed-effort yet; it is the row-wise prediction sanity check.

### actual vs predicted k3 POP M3 nb words

![actual vs predicted k3 POP M3 nb words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M3_nb_words.png)

### actual vs predicted k3 POP M4A nb words

![actual vs predicted k3 POP M4A nb words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M4A_nb_words.png)

### actual vs predicted k3 POP M4C nb words

![actual vs predicted k3 POP M4C nb words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M4C_nb_words.png)

### actual vs predicted k3 MUND M3 nb words

![actual vs predicted k3 MUND M3 nb words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_MUND_M3_nb_words.png)

## 5. Fixed-Effort Trajectory Checks

These are the closest analogue to the Atlas fixed-effort plots. Lines are PBM-trained predictions at fixed effort levels. Points are heldout observed monthly means in the matching effort bands.

### fixed effort k3 POP M3 nb words

![fixed effort k3 POP M3 nb words](../figs/route1_heldout_real_child_prediction/fixed_effort_k3_POP_M3_nb_words.png)

### fixed effort k3 POP M4A nb words

![fixed effort k3 POP M4A nb words](../figs/route1_heldout_real_child_prediction/fixed_effort_k3_POP_M4A_nb_words.png)

### fixed effort k3 MUND M3 nb words

![fixed effort k3 MUND M3 nb words](../figs/route1_heldout_real_child_prediction/fixed_effort_k3_MUND_M3_nb_words.png)

### fixed effort k3 POP M3 nb morphemes

![fixed effort k3 POP M3 nb morphemes](../figs/route1_heldout_real_child_prediction/fixed_effort_k3_POP_M3_nb_morphemes.png)

### fixed effort k3 MUND M3 nb morphemes

![fixed effort k3 MUND M3 nb morphemes](../figs/route1_heldout_real_child_prediction/fixed_effort_k3_MUND_M3_nb_morphemes.png)

## 6. Interpretation Boundary

This report answers the first robustness question: the PBM-trained age/effort/context-size/question-type models can now be compared against real unseen-child trajectories. The honest limitation is that fixed child identity effects cannot be directly transported to new children; the Mundlak variants are the out-of-sample-compatible child-coverage adjustment.

The next predictor-enrichment step is to compute heldout `context_entropy_bits` and later response-space entropy for the same contexts. Once those are attached, the entropy-dependent M4b/M5/M6/M11-M15 families and Route 2 prediction models can be tested on the same heldout children.

## Saved Artifacts

```text
results/route1_heldout_real_child_prediction/heldout_scored_utterance_effort_long.csv.gz
results/route1_heldout_real_child_prediction/heldout_prediction_fit_summary.csv
results/route1_heldout_real_child_prediction/heldout_prediction_metrics.csv
results/route1_heldout_real_child_prediction/heldout_prediction_monthly.csv.gz
results/route1_heldout_real_child_prediction/heldout_fixed_effort_prediction_grid.csv.gz
results/route1_heldout_real_child_prediction/heldout_fixed_effort_observed_monthly.csv.gz
results/route1_heldout_real_child_prediction/heldout_selection_coverage_rows.csv
figs/route1_heldout_real_child_prediction
```

## Skipped Fits

Some model/context combinations are intentionally skipped, mostly because context models do not apply to k0.

| model_id | context_k | effort_label | status | error |
| --- | --- | --- | --- | --- |
| POP_M4A | k0 | Words | skipped | model needs context but context is k0 |
| POP_M4C | k0 | Words | skipped | model needs context but context is k0 |
| POP_M4A | k0 | Morphemes | skipped | model needs context but context is k0 |
| POP_M4C | k0 | Morphemes | skipped | model needs context but context is k0 |
