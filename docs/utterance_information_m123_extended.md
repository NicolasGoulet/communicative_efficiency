# Extended Internal Review: Utterance Information Models M1-M3

This report is a more explicit companion to the M1/M2/M3 deep dive. It does not
introduce new fitted models; it makes the current results easier to explain.

## Literature Anchors

- Communicative-efficiency work on children motivates testing whether children
  shorten or lengthen messages when context makes a shorter message sufficient.
- Work on child-directed and learner-directed speech motivates comparing
  children and caretakers, and treating redundancy as potentially adaptive.
- The Wang et al. word-formation paper motivates interaction models: different
  information sources can jointly constrain efficient form choice, so
  age-by-effort and age-by-context interactions are not decorative terms.

## What The Three Models Ask

| model | formula template | question |
| --- | --- | --- |
| M1 | `sum_bits ~ age + effort` | In the pooled child data, does age predict total bits after utterance size is controlled? |
| M2 | `sum_bits ~ age + effort + child identity` | Within a child-adjusted developmental frame, does age predict total bits after utterance size is controlled? |
| M3 | `sum_bits ~ age * effort` | Does the amount of information associated with each unit of effort itself change with age? |

All effort measures are kept separate. This is a scientific constraint, not a
coding convenience: the effort measures are strongly collinear.

## Why The Fixed-Median Prediction Lines Exist

Regression lines over age need one concrete utterance size. When a plot says
"effort fixed at median X", the fitted model has **not** been changed. The
line asks what the fitted model predicts as age varies for a typical utterance
with that effort value. This is the visual version of "controlling for
utterance size."

## Effort Collinearity

| predictor | r2_from_other_predictors | vif |
| --- | --- | --- |
| age_months | 0.08399 | 1.092 |
| nb_words | 0.9596 | 24.76 |
| nb_morphemes | 0.9555 | 22.48 |
| nb_syllables_cmu_or_pkg | 0.9711 | 34.61 |
| nb_syllables_pkg | 0.9602 | 25.15 |
| nb_phonemes | 0.9581 | 23.84 |

![Predictor correlations](../figs/m1_m2_utterance_information_deep_dive/predictor_correlation_heatmap.png)

## M1 Versus M2: The Important Sign Flip

| effort_label | M1 | M2 | interpretation | m1_r2 | m2_r2 |
| --- | --- | --- | --- | --- | --- |
| Morphemes | 0.009018 | -0.1355 | direction changes after child identity is added | 0.5978 | 0.6131 |
| Phonemes | 0.0681 | -0.06486 | direction changes after child identity is added | 0.632 | 0.6443 |
| Syllables: CMU/pkg | 0.05143 | -0.06326 | direction changes after child identity is added | 0.6345 | 0.6459 |
| Syllables: pkg | 0.06904 | -0.04846 | direction changes after child identity is added | 0.6177 | 0.6296 |
| Words | 0.0003087 | -0.1225 | direction changes after child identity is added | 0.613 | 0.6259 |

Interpretation: M1 is a pooled model and can mix within-child development with
which children contribute data at which ages. M2 adds child identity and is
therefore closer to the developmental question. In the current results, the
child-adjusted models show a downward developmental age effect across all
effort versions, whereas the pooled model does not.

![M1/M2 adjusted trajectories](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)

## M3 Interaction Focus

| model_family_label | effort_label | r2_observed_fitted | age_coef | effort_coef | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- |
| OLS + interaction, child-clustered SE | Words | 0.613 | -0.001242 | 6.342 | 0.003893 | 0.422 |
| OLS + interaction + child fixed intercepts | Words | 0.6259 | -0.1216 | 6.379 | -0.003787 | 0.515 |
| Gaussian GEE + interaction, clustered by child | Words | 0.6086 | -0.1215 | 6.379 | -0.003783 | 0.505 |
| OLS + interaction, child-clustered SE | Morphemes | 0.598 | 0.004168 | 5.416 | 0.0103 | 0.034 |
| OLS + interaction + child fixed intercepts | Morphemes | 0.6131 | -0.1362 | 5.482 | 0.00228 | 0.727 |
| Gaussian GEE + interaction, clustered by child | Morphemes | 0.5924 | -0.1361 | 5.482 | 0.002283 | 0.720 |
| OLS + interaction, child-clustered SE | Syllables: CMU/pkg | 0.6348 | 0.04521 | 5.181 | 0.01174 | 0.023 |
| OLS + interaction + child fixed intercepts | Syllables: CMU/pkg | 0.646 | -0.06586 | 5.217 | 0.00703 | 0.252 |
| Gaussian GEE + interaction, clustered by child | Syllables: CMU/pkg | 0.6313 | -0.06578 | 5.217 | 0.007032 | 0.240 |
| OLS + interaction, child-clustered SE | Syllables: pkg | 0.6181 | 0.06146 | 4.787 | 0.01407 | <.001 |
| OLS + interaction + child fixed intercepts | Syllables: pkg | 0.6298 | -0.05214 | 4.806 | 0.009859 | 0.022 |
| Gaussian GEE + interaction, clustered by child | Syllables: pkg | 0.6143 | -0.05206 | 4.806 | 0.009861 | 0.019 |
| OLS + interaction, child-clustered SE | Phonemes | 0.6322 | 0.06241 | 2.059 | 0.004518 | 0.008 |
| OLS + interaction + child fixed intercepts | Phonemes | 0.6444 | -0.06723 | 2.077 | 0.002729 | 0.220 |
| Gaussian GEE + interaction, clustered by child | Phonemes | 0.6276 | -0.06714 | 2.077 | 0.00273 | 0.209 |

The interaction coefficient is `age_effort_coef`. For additive-bit models,
positive values mean the effort-to-information slope increases with age;
negative values mean it decreases with age. For Gamma/log-link models, read
the prediction plots first because coefficients are on the log expected-bits
scale.

![M3 interaction coefficients](../figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png)

![M3 OLS interaction lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png)

![M3 child fixed-effect interaction lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)

## Fit Status And Caveats

| approach_id | status | fits |
| --- | --- | --- |
| M1 | fit | 20 |
| M2 | fit | 35 |
| M3 | fit | 55 |

Mixed-model singularity warnings are not hidden. They mean that a random-effect
variance was estimated at or near the boundary, so these fits are sensitivity
diagnostics rather than the primary evidence. The stable primary ladder remains:
pooled OLS, child-clustered OLS, child fixed effects, and GEE.

## Age-Bin Coverage

| age_bin | rows | children | mean_sum_bits | mean_words | mean_morphemes | mean_syllables_cmu_or_pkg | mean_phonemes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 006-023 | 62816 | 17 | 23.13 | 1.999 | 2.206 | 2.601 | 6.487 |
| 024-029 | 162210 | 21 | 24.81 | 2.337 | 2.595 | 2.862 | 7.136 |
| 030-035 | 142447 | 20 | 26.8 | 2.794 | 3.116 | 3.353 | 8.361 |
| 036-041 | 37683 | 8 | 31.03 | 3.261 | 3.601 | 3.874 | 9.482 |
| 042-047 | 16345 | 5 | 32.89 | 3.786 | 4.24 | 4.508 | 11.04 |
| 048-053 | 12909 | 3 | 36.99 | 3.956 | 4.455 | 4.691 | 11.5 |
| 054-059 | 10033 | 2 | 37.77 | 4.133 | 4.681 | 4.909 | 12.07 |
| 060-065 | 2542 | 2 | 34.75 | 4.006 | 4.485 | 4.7 | 11.65 |

## Output Tables

- `results/utterance_information_m123_extended/m1_m2_sign_flip_table.csv`
- `results/utterance_information_m123_extended/m3_interaction_focus.csv`
- `results/utterance_information_m123_extended/selected_age_effects.csv`
