# Exhaustive Fixed-Effort Atlas For M1-M6

This is an internal review report. It replaces median-only interpretation with
three complementary views:

1. coefficient tables for the fitted M1-M6 models;
2. global marginal adjusted age trends that average over observed effort,
   children, and context rows;
3. exact fixed-effort slices grouped into readable panels.

The report does **not** refit models. It reads:

```text
results/m1_m6_fixed_effort_slices/fixed_effort_model_summary.csv
results/m1_m6_fixed_effort_slices/marginal_adjusted_predictions.csv
results/m1_m6_fixed_effort_slices/fixed_effort_predictions.csv
results/m1_m6_fixed_effort_slices/selected_fixed_effort_values.csv
```

## Statistical Framing

This follows the Advanced Data Analytics guidance checked locally on
2026-06-09:

- `sum_bits` is a continuous outcome;
- utterances are repeated within children, so child identity matters;
- prediction summaries and inference are separate objects;
- effort measures are highly correlated, so each model uses one effort unit at
  a time;
- fixed-effort slices are prediction views, not separate fitted models.

The surprising/core result to watch is the sign change after child identity is
controlled: pooled models can look weak or upward, while child-adjusted models
show a downward age trend, meaning children become less surprising over time
after effort and child identity are controlled.

## Table Column Guide

| column | how_to_interpret |
| --- | --- |
| model_id | Which model family is being summarized, M1 through M6. |
| effort_label | Which effort unit is controlled in that model row: words, morphemes, syllables, or phonemes. |
| n_obs | Number of utterance rows used to fit that model. |
| n_children | Number of distinct children represented in the fitted rows. |
| r2_observed_fitted | In-sample correspondence between observed and fitted total bits; higher means better descriptive fit. |
| age_coef | Estimated monthly age slope for total bits after the controls in that formula. Negative means predicted total bits decrease with age. |
| age_p | p-value for the age slope. Use it as inferential support, not as the visual effect size. |
| effort_coef | Estimated change in total bits for one additional effort unit when effort is continuous. |
| effort_p | p-value for the effort slope. |
| entropy_coef | Estimated change in total bits for one additional bit of next-token context entropy. |
| entropy_p | p-value for the context-entropy slope. |
| age_effort_coef | Interaction: how much the age slope changes for each additional effort unit. |
| age_effort_p | p-value for the age-by-effort interaction. |
| age_entropy_coef | Interaction: how much the age slope changes for each additional bit of context entropy. |
| age_entropy_p | p-value for the age-by-entropy interaction. |
| effort_entropy_coef | Interaction: how much the effort slope changes as context entropy increases. |
| effort_entropy_p | p-value for the effort-by-entropy interaction. |

## Age-Slope Summary

| model_id | negative_age_slopes | positive_age_slopes | significant_age_slopes_p_lt_05 | tested_effort_units | age_coef_min | age_coef_max |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | 0 | 5 | 2 | 5 | 0.000309 | 0.069 |
| M2 | 5 | 0 | 5 | 5 | -0.136 | -0.0485 |
| M3 | 5 | 0 | 4 | 5 | -0.136 | -0.0521 |
| M4 | 5 | 0 | 5 | 5 | -0.14 | -0.048 |
| M5 | 5 | 0 | 5 | 5 | -0.141 | -0.0485 |
| M6 | 5 | 0 | 4 | 5 | -0.142 | -0.0523 |

## Variance Explained Summary

How to read: `mean_r2_observed_fitted` is the average in-sample R2 across the
five effort-unit versions of a model. It describes how much observed variation
in total utterance bits is captured by the fitted predictors in these rows. It
is not held-out predictive accuracy.

| model_id | mean_r2_observed_fitted | min_r2_observed_fitted | max_r2_observed_fitted | significant_age_slopes_p_lt_05 | negative_age_slopes | positive_age_slopes | effort_units_tested |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | 0.619 | 0.598 | 0.635 | 2 | 0 | 5 | 5 |
| M2 | 0.632 | 0.613 | 0.646 | 5 | 5 | 0 | 5 |
| M3 | 0.632 | 0.613 | 0.646 | 4 | 5 | 0 | 5 |
| M4 | 0.633 | 0.614 | 0.647 | 5 | 5 | 0 | 5 |
| M5 | 0.633 | 0.614 | 0.647 | 5 | 5 | 0 | 5 |
| M6 | 0.633 | 0.614 | 0.647 | 4 | 5 | 0 | 5 |

## Predictor Significance Summary

How to read: each row asks whether a predictor is significant across the
effort-unit versions where it appears. `significant_p_lt_05` counts how many
effort-unit models have p<.05 for that predictor. `coef_min` and `coef_max`
show the range of estimated coefficients across effort units.

| model_id | predictor | what_it_represents | tested_effort_units | significant_p_lt_05 | negative_significant | positive_significant | coef_min | coef_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | age | developmental time, measured in months | 5 | 2 | 0 | 2 | 0.000309 | 0.069 |
| M1 | effort | utterance production effort in the current effort unit | 5 | 5 | 0 | 5 | 2.07 | 6.35 |
| M2 | age | developmental time, measured in months | 5 | 5 | 5 | 0 | -0.136 | -0.0485 |
| M2 | effort | utterance production effort in the current effort unit | 5 | 5 | 0 | 5 | 2.08 | 6.37 |
| M3 | age | developmental time, measured in months | 5 | 4 | 4 | 0 | -0.136 | -0.0521 |
| M3 | effort | utterance production effort in the current effort unit | 5 | 5 | 0 | 5 | 2.08 | 6.38 |
| M3 | age_by_effort | whether the age trend changes as effort increases | 5 | 1 | 0 | 1 | -0.00379 | 0.00986 |
| M4 | age | developmental time, measured in months | 5 | 5 | 5 | 0 | -0.14 | -0.048 |
| M4 | effort | utterance production effort in the current effort unit | 5 | 5 | 0 | 5 | 2.08 | 6.37 |
| M4 | context_entropy | next-token context entropy in bits | 5 | 5 | 5 | 0 | -0.581 | -0.472 |
| M5 | age | developmental time, measured in months | 5 | 5 | 5 | 0 | -0.141 | -0.0485 |
| M5 | effort | utterance production effort in the current effort unit | 5 | 5 | 0 | 5 | 2.08 | 6.37 |
| M5 | context_entropy | next-token context entropy in bits | 5 | 5 | 5 | 0 | -0.581 | -0.47 |
| M5 | age_by_context_entropy | whether the age trend changes as context entropy increases | 5 | 0 | 0 | 0 | 0.00395 | 0.00614 |
| M6 | age | developmental time, measured in months | 5 | 4 | 4 | 0 | -0.142 | -0.0523 |
| M6 | effort | utterance production effort in the current effort unit | 5 | 5 | 0 | 5 | 2.08 | 6.38 |
| M6 | context_entropy | next-token context entropy in bits | 5 | 5 | 5 | 0 | -0.585 | -0.473 |
| M6 | age_by_effort | whether the age trend changes as effort increases | 5 | 1 | 0 | 1 | -0.00244 | 0.0121 |
| M6 | age_by_context_entropy | whether the age trend changes as context entropy increases | 5 | 0 | 0 | 0 | 0.00518 | 0.0091 |
| M6 | effort_by_context_entropy | whether the effort slope changes as context entropy increases | 5 | 0 | 0 | 0 | -0.0649 | -0.0289 |

## Effort Bin Definitions

| effort_col | effort_label | atlas_bin | fixed_values | n_fixed_values | rule |
| --- | --- | --- | --- | --- | --- |
| nb_words | Words | 1-4 | 1, 2, 3, 4 | 4 | Exact values 1-4. |
| nb_words | Words | 5-8 | 5, 6, 7, 8 | 4 | Exact values 5-8. |
| nb_words | Words | 9-12 | 9, 10, 11, 12 | 4 | Exact values 9-12. |
| nb_morphemes | Morphemes | 1-4 | 1, 2, 3, 4 | 4 | Exact values 1-4. |
| nb_morphemes | Morphemes | 5-8 | 5, 6, 7, 8 | 4 | Exact values 5-8. |
| nb_morphemes | Morphemes | 9-12 | 9, 10, 11, 12 | 4 | Exact values 9-12. |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | low representative sizes | 1, 2, 3, 4 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | middle representative sizes | 5, 6, 7, 8 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | high representative sizes | 9, 10, 11, 12 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_syllables_pkg | Syllables: pkg | low representative sizes | 1, 2, 3, 4 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_syllables_pkg | Syllables: pkg | middle representative sizes | 5, 6, 7, 8 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_syllables_pkg | Syllables: pkg | high representative sizes | 9, 10, 11, 12 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_phonemes | Phonemes | low representative sizes | 2, 3, 4, 5 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_phonemes | Phonemes | middle representative sizes | 6, 7, 8, 9 | 4 | Ordered split of the 12 most frequent exact effort values. |
| nb_phonemes | Phonemes | high representative sizes | 10, 11, 12, 13 | 4 | Ordered split of the 12 most frequent exact effort values. |

## Effort Bin Row Support

The next table and plots show how many real child utterances support each bin.
This matters because fixed-effort slices should be interpreted more cautiously
when they represent fewer rows or fewer age bins.

| effort_label | atlas_bin | fixed_values | rows | pct_effort_rows | n_children_max | n_age_bins_max |
| --- | --- | --- | --- | --- | --- | --- |
| Words | 1-4 | 1, 2, 3, 4 | 381557 | 0.854 | 21 | 8 |
| Words | 5-8 | 5, 6, 7, 8 | 58263 | 0.13 | 21 | 8 |
| Words | 9-12 | 9, 10, 11, 12 | 5737 | 0.0128 | 21 | 8 |
| Morphemes | 1-4 | 1, 2, 3, 4 | 357854 | 0.801 | 21 | 8 |
| Morphemes | 5-8 | 5, 6, 7, 8 | 77357 | 0.173 | 21 | 8 |
| Morphemes | 9-12 | 9, 10, 11, 12 | 9409 | 0.021 | 21 | 8 |
| Syllables: CMU/pkg | low representative sizes | 1, 2, 3, 4 | 344589 | 0.771 | 21 | 8 |
| Syllables: CMU/pkg | middle representative sizes | 5, 6, 7, 8 | 86468 | 0.193 | 21 | 8 |
| Syllables: CMU/pkg | high representative sizes | 9, 10, 11, 12 | 12662 | 0.0283 | 21 | 8 |
| Syllables: pkg | low representative sizes | 1, 2, 3, 4 | 329972 | 0.738 | 21 | 8 |
| Syllables: pkg | middle representative sizes | 5, 6, 7, 8 | 97554 | 0.218 | 21 | 8 |
| Syllables: pkg | high representative sizes | 9, 10, 11, 12 | 15357 | 0.0344 | 21 | 8 |
| Phonemes | low representative sizes | 2, 3, 4, 5 | 175070 | 0.392 | 21 | 8 |
| Phonemes | middle representative sizes | 6, 7, 8, 9 | 118913 | 0.266 | 21 | 8 |
| Phonemes | high representative sizes | 10, 11, 12, 13 | 73995 | 0.166 | 21 | 8 |

![Atlas effort bin distribution](../figs/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution.png)

![Atlas effort bin distribution by age](../figs/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution_by_age.png)

## Model Sections

## M1: Pooled age and effort

**Question.** Pooling all children, does age predict total bits after controlling utterance effort?

**Formula.** `sum_bits ~ age + effort`

**Takeaway.** Pooled model. Useful as a baseline, but not sufficient for developmental interpretation because it ignores child identity. In this run, 0/5 effort-unit age slopes are negative, 5/5 are positive, and 2/5 age slopes have p<.05.

**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Words | 446985 | 21 | 0.613 | 0.000309 | 0.993 | 6.35 | <.001 |  |  |  |  |  |  |  |  |
| M1 | Morphemes | 446985 | 21 | 0.598 | 0.00902 | 0.774 | 5.45 | <.001 |  |  |  |  |  |  |  |  |
| M1 | Syllables: CMU/pkg | 446985 | 21 | 0.635 | 0.0514 | 0.053 | 5.21 | <.001 |  |  |  |  |  |  |  |  |
| M1 | Syllables: pkg | 446985 | 21 | 0.618 | 0.069 | 0.012 | 4.82 | <.001 |  |  |  |  |  |  |  |  |
| M1 | Phonemes | 446985 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  |  |  |

**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.

| effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | min_slope_bits_per_month | max_slope_bits_per_month | mean_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | 1-4 | 4 | 0 | 4 | 0.00902 | 0.00902 | 0.00902 |
| Morphemes | 5-8 | 4 | 0 | 4 | 0.00902 | 0.00902 | 0.00902 |
| Morphemes | 9-12 | 4 | 0 | 4 | 0.00902 | 0.00902 | 0.00902 |
| Phonemes |  | 7 | 0 | 7 | 0.0681 | 0.0681 | 0.0681 |
| Phonemes | high representative sizes | 4 | 0 | 4 | 0.0681 | 0.0681 | 0.0681 |
| Phonemes | low representative sizes | 4 | 0 | 4 | 0.0681 | 0.0681 | 0.0681 |
| Phonemes | middle representative sizes | 4 | 0 | 4 | 0.0681 | 0.0681 | 0.0681 |
| Syllables: CMU/pkg | high representative sizes | 4 | 0 | 4 | 0.0514 | 0.0514 | 0.0514 |
| Syllables: CMU/pkg | low representative sizes | 4 | 0 | 4 | 0.0514 | 0.0514 | 0.0514 |
| Syllables: CMU/pkg | middle representative sizes | 4 | 0 | 4 | 0.0514 | 0.0514 | 0.0514 |
| Syllables: pkg | high representative sizes | 4 | 0 | 4 | 0.069 | 0.069 | 0.069 |
| Syllables: pkg | low representative sizes | 4 | 0 | 4 | 0.069 | 0.069 | 0.069 |
| Syllables: pkg | middle representative sizes | 4 | 0 | 4 | 0.069 | 0.069 | 0.069 |
| Words | 1-4 | 4 | 0 | 4 | 0.000309 | 0.000309 | 0.000309 |
| Words | 5-8 | 4 | 0 | 4 | 0.000309 | 0.000309 | 0.000309 |
| Words | 9-12 | 4 | 0 | 4 | 0.000309 | 0.000309 | 0.000309 |

### Global marginal adjusted trend

How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?

![M1 global marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m1_marginal_adjusted_global_trends.png)


### Fixed effort slices by effort unit

Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.

#### Words

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M1 Words fixed slices](../figs/m1_m6_fixed_effort_atlas/m1_nb_words_atlas_bins.png)

#### Morphemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M1 Morphemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m1_nb_morphemes_atlas_bins.png)

#### Syllables: CMU/pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M1 Syllables: CMU/pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_cmu_or_pkg_atlas_bins.png)

#### Syllables: pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M1 Syllables: pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_pkg_atlas_bins.png)

#### Phonemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M1 Phonemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m1_nb_phonemes_atlas_bins.png)

## M2: Age and effort with child identity

**Question.** Does the developmental age effect remain after child identity is controlled?

**Formula.** `sum_bits ~ age + effort + child identity`

**Takeaway.** First primary child-adjusted model. If age slopes are negative here, the developmental trend remains after controlling effort and child identity. In this run, 5/5 effort-unit age slopes are negative, 0/5 are positive, and 5/5 age slopes have p<.05.

**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M2 | Words | 446985 | 21 | 0.626 | -0.122 | <.001 | 6.37 | <.001 |  |  |  |  |  |  |  |  |
| M2 | Morphemes | 446985 | 21 | 0.613 | -0.136 | <.001 | 5.49 | <.001 |  |  |  |  |  |  |  |  |
| M2 | Syllables: CMU/pkg | 446985 | 21 | 0.646 | -0.0633 | 0.018 | 5.24 | <.001 |  |  |  |  |  |  |  |  |
| M2 | Syllables: pkg | 446985 | 21 | 0.63 | -0.0485 | 0.049 | 4.83 | <.001 |  |  |  |  |  |  |  |  |
| M2 | Phonemes | 446985 | 21 | 0.644 | -0.0649 | 0.013 | 2.08 | <.001 |  |  |  |  |  |  |  |  |

**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.

| effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | min_slope_bits_per_month | max_slope_bits_per_month | mean_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | 1-4 | 4 | 4 | 0 | -0.136 | -0.136 | -0.136 |
| Morphemes | 5-8 | 4 | 4 | 0 | -0.136 | -0.136 | -0.136 |
| Morphemes | 9-12 | 4 | 4 | 0 | -0.136 | -0.136 | -0.136 |
| Phonemes |  | 7 | 7 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Phonemes | high representative sizes | 4 | 4 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Phonemes | low representative sizes | 4 | 4 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Phonemes | middle representative sizes | 4 | 4 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Syllables: CMU/pkg | high representative sizes | 4 | 4 | 0 | -0.0633 | -0.0633 | -0.0633 |
| Syllables: CMU/pkg | low representative sizes | 4 | 4 | 0 | -0.0633 | -0.0633 | -0.0633 |
| Syllables: CMU/pkg | middle representative sizes | 4 | 4 | 0 | -0.0633 | -0.0633 | -0.0633 |
| Syllables: pkg | high representative sizes | 4 | 4 | 0 | -0.0485 | -0.0485 | -0.0485 |
| Syllables: pkg | low representative sizes | 4 | 4 | 0 | -0.0485 | -0.0485 | -0.0485 |
| Syllables: pkg | middle representative sizes | 4 | 4 | 0 | -0.0485 | -0.0485 | -0.0485 |
| Words | 1-4 | 4 | 4 | 0 | -0.122 | -0.122 | -0.122 |
| Words | 5-8 | 4 | 4 | 0 | -0.122 | -0.122 | -0.122 |
| Words | 9-12 | 4 | 4 | 0 | -0.122 | -0.122 | -0.122 |

### Global marginal adjusted trend

How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?

![M2 global marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m2_marginal_adjusted_global_trends.png)


### Fixed effort slices by effort unit

Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.

#### Words

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M2 Words fixed slices](../figs/m1_m6_fixed_effort_atlas/m2_nb_words_atlas_bins.png)

#### Morphemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M2 Morphemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m2_nb_morphemes_atlas_bins.png)

#### Syllables: CMU/pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M2 Syllables: CMU/pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_cmu_or_pkg_atlas_bins.png)

#### Syllables: pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M2 Syllables: pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_pkg_atlas_bins.png)

#### Phonemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M2 Phonemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m2_nb_phonemes_atlas_bins.png)

## M3: Age by effort

**Question.** Does the relation between effort and total bits change with age?

**Formula.** `sum_bits ~ age * effort + child identity`

**Takeaway.** Checks whether the age trend changes across effort values. The fixed-slice plots are especially important here. In this run, 5/5 effort-unit age slopes are negative, 0/5 are positive, and 4/5 age slopes have p<.05.

**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M3 | Words | 446985 | 21 | 0.626 | -0.122 | <.001 | 6.38 | <.001 |  |  | -0.00379 | 0.515 |  |  |  |  |
| M3 | Morphemes | 446985 | 21 | 0.613 | -0.136 | <.001 | 5.48 | <.001 |  |  | 0.00228 | 0.727 |  |  |  |  |
| M3 | Syllables: CMU/pkg | 446985 | 21 | 0.646 | -0.0659 | 0.017 | 5.22 | <.001 |  |  | 0.00703 | 0.252 |  |  |  |  |
| M3 | Syllables: pkg | 446985 | 21 | 0.63 | -0.0521 | 0.055 | 4.81 | <.001 |  |  | 0.00986 | 0.022 |  |  |  |  |
| M3 | Phonemes | 446985 | 21 | 0.644 | -0.0672 | 0.017 | 2.08 | <.001 |  |  | 0.00273 | 0.220 |  |  |  |  |

**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.

| effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | min_slope_bits_per_month | max_slope_bits_per_month | mean_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | 1-4 | 4 | 4 | 0 | -0.141 | -0.134 | -0.137 |
| Morphemes | 5-8 | 4 | 4 | 0 | -0.132 | -0.125 | -0.128 |
| Morphemes | 9-12 | 4 | 4 | 0 | -0.122 | -0.116 | -0.119 |
| Phonemes |  | 7 | 7 | 0 | -0.0864 | -0.0373 | -0.0502 |
| Phonemes | high representative sizes | 4 | 4 | 0 | -0.0619 | -0.0537 | -0.0578 |
| Phonemes | low representative sizes | 4 | 4 | 0 | -0.0837 | -0.0755 | -0.0796 |
| Phonemes | middle representative sizes | 4 | 4 | 0 | -0.0728 | -0.0646 | -0.0687 |
| Syllables: CMU/pkg | high representative sizes | 4 | 4 | 0 | -0.0253 | -0.00425 | -0.0148 |
| Syllables: CMU/pkg | low representative sizes | 4 | 4 | 0 | -0.0816 | -0.0605 | -0.071 |
| Syllables: CMU/pkg | middle representative sizes | 4 | 4 | 0 | -0.0535 | -0.0324 | -0.0429 |
| Syllables: pkg | high representative sizes | 4 | 0 | 4 | 0.0028 | 0.0324 | 0.0176 |
| Syllables: pkg | low representative sizes | 4 | 4 | 0 | -0.0761 | -0.0465 | -0.0613 |
| Syllables: pkg | middle representative sizes | 4 | 4 | 0 | -0.0366 | -0.00706 | -0.0219 |
| Words | 1-4 | 4 | 4 | 0 | -0.127 | -0.115 | -0.121 |
| Words | 5-8 | 4 | 4 | 0 | -0.142 | -0.13 | -0.136 |
| Words | 9-12 | 4 | 4 | 0 | -0.157 | -0.146 | -0.151 |

### Global marginal adjusted trend

How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?

![M3 global marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m3_marginal_adjusted_global_trends.png)


### Fixed effort slices by effort unit

Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.

#### Words

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M3 Words fixed slices](../figs/m1_m6_fixed_effort_atlas/m3_nb_words_atlas_bins.png)

#### Morphemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M3 Morphemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m3_nb_morphemes_atlas_bins.png)

#### Syllables: CMU/pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M3 Syllables: CMU/pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_cmu_or_pkg_atlas_bins.png)

#### Syllables: pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M3 Syllables: pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_pkg_atlas_bins.png)

#### Phonemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M3 Phonemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m3_nb_phonemes_atlas_bins.png)

## M4: Context entropy added

**Question.** Does context entropy add predictive information beyond age, effort, and child identity?

**Formula.** `sum_bits ~ age + effort + context_entropy + child identity`

**Takeaway.** Adds provisional next-token context entropy. This asks whether the child-adjusted age pattern survives context-predictability control. In this run, 5/5 effort-unit age slopes are negative, 0/5 are positive, and 5/5 age slopes have p<.05.

**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | Words | 441413 | 21 | 0.627 | -0.127 | <.001 | 6.37 | <.001 | -0.472 | <.001 |  |  |  |  |  |  |
| M4 | Morphemes | 441413 | 21 | 0.614 | -0.14 | <.001 | 5.49 | <.001 | -0.512 | <.001 |  |  |  |  |  |  |
| M4 | Syllables: CMU/pkg | 441413 | 21 | 0.647 | -0.0645 | 0.013 | 5.23 | <.001 | -0.54 | <.001 |  |  |  |  |  |  |
| M4 | Syllables: pkg | 441413 | 21 | 0.63 | -0.048 | 0.038 | 4.83 | <.001 | -0.541 | <.001 |  |  |  |  |  |  |
| M4 | Phonemes | 441413 | 21 | 0.645 | -0.0652 | 0.013 | 2.08 | <.001 | -0.581 | <.001 |  |  |  |  |  |  |

**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.

| effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | min_slope_bits_per_month | max_slope_bits_per_month | mean_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | 1-4 | 4 | 4 | 0 | -0.14 | -0.14 | -0.14 |
| Morphemes | 5-8 | 4 | 4 | 0 | -0.14 | -0.14 | -0.14 |
| Morphemes | 9-12 | 4 | 4 | 0 | -0.14 | -0.14 | -0.14 |
| Phonemes |  | 7 | 7 | 0 | -0.0652 | -0.0652 | -0.0652 |
| Phonemes | high representative sizes | 4 | 4 | 0 | -0.0652 | -0.0652 | -0.0652 |
| Phonemes | low representative sizes | 4 | 4 | 0 | -0.0652 | -0.0652 | -0.0652 |
| Phonemes | middle representative sizes | 4 | 4 | 0 | -0.0652 | -0.0652 | -0.0652 |
| Syllables: CMU/pkg | high representative sizes | 4 | 4 | 0 | -0.0645 | -0.0645 | -0.0645 |
| Syllables: CMU/pkg | low representative sizes | 4 | 4 | 0 | -0.0645 | -0.0645 | -0.0645 |
| Syllables: CMU/pkg | middle representative sizes | 4 | 4 | 0 | -0.0645 | -0.0645 | -0.0645 |
| Syllables: pkg | high representative sizes | 4 | 4 | 0 | -0.048 | -0.048 | -0.048 |
| Syllables: pkg | low representative sizes | 4 | 4 | 0 | -0.048 | -0.048 | -0.048 |
| Syllables: pkg | middle representative sizes | 4 | 4 | 0 | -0.048 | -0.048 | -0.048 |
| Words | 1-4 | 4 | 4 | 0 | -0.127 | -0.127 | -0.127 |
| Words | 5-8 | 4 | 4 | 0 | -0.127 | -0.127 | -0.127 |
| Words | 9-12 | 4 | 4 | 0 | -0.127 | -0.127 | -0.127 |

### Global marginal adjusted trend

How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?

![M4 global marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m4_marginal_adjusted_global_trends.png)


### Fixed effort slices by effort unit

Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.

#### Words

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M4 Words fixed slices](../figs/m1_m6_fixed_effort_atlas/m4_nb_words_atlas_bins.png)

#### Morphemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M4 Morphemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m4_nb_morphemes_atlas_bins.png)

#### Syllables: CMU/pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M4 Syllables: CMU/pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_cmu_or_pkg_atlas_bins.png)

#### Syllables: pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M4 Syllables: pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_pkg_atlas_bins.png)

#### Phonemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M4 Phonemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m4_nb_phonemes_atlas_bins.png)

## M5: Age by context entropy

**Question.** Does the context-entropy effect on total bits change over development?

**Formula.** `sum_bits ~ age * context_entropy + effort + child identity`

**Takeaway.** Tests whether the entropy association changes with age. Treat this as context-sensitivity evidence only if the interaction is stable. In this run, 5/5 effort-unit age slopes are negative, 0/5 are positive, and 5/5 age slopes have p<.05.

**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5 | Words | 441413 | 21 | 0.627 | -0.128 | <.001 | 6.37 | <.001 | -0.47 | <.001 |  |  | 0.00614 | 0.284 |  |  |
| M5 | Morphemes | 441413 | 21 | 0.614 | -0.141 | <.001 | 5.49 | <.001 | -0.511 | <.001 |  |  | 0.00471 | 0.339 |  |  |
| M5 | Syllables: CMU/pkg | 441413 | 21 | 0.647 | -0.0649 | 0.015 | 5.23 | <.001 | -0.539 | <.001 |  |  | 0.00396 | 0.478 |  |  |
| M5 | Syllables: pkg | 441413 | 21 | 0.63 | -0.0485 | 0.042 | 4.83 | <.001 | -0.54 | <.001 |  |  | 0.00395 | 0.481 |  |  |
| M5 | Phonemes | 441413 | 21 | 0.645 | -0.0657 | 0.014 | 2.08 | <.001 | -0.581 | <.001 |  |  | 0.00465 | 0.407 |  |  |

**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.

| effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | min_slope_bits_per_month | max_slope_bits_per_month | mean_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | 1-4 | 4 | 4 | 0 | -0.141 | -0.141 | -0.141 |
| Morphemes | 5-8 | 4 | 4 | 0 | -0.141 | -0.141 | -0.141 |
| Morphemes | 9-12 | 4 | 4 | 0 | -0.141 | -0.141 | -0.141 |
| Phonemes |  | 7 | 7 | 0 | -0.0657 | -0.0657 | -0.0657 |
| Phonemes | high representative sizes | 4 | 4 | 0 | -0.0657 | -0.0657 | -0.0657 |
| Phonemes | low representative sizes | 4 | 4 | 0 | -0.0657 | -0.0657 | -0.0657 |
| Phonemes | middle representative sizes | 4 | 4 | 0 | -0.0657 | -0.0657 | -0.0657 |
| Syllables: CMU/pkg | high representative sizes | 4 | 4 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Syllables: CMU/pkg | low representative sizes | 4 | 4 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Syllables: CMU/pkg | middle representative sizes | 4 | 4 | 0 | -0.0649 | -0.0649 | -0.0649 |
| Syllables: pkg | high representative sizes | 4 | 4 | 0 | -0.0485 | -0.0485 | -0.0485 |
| Syllables: pkg | low representative sizes | 4 | 4 | 0 | -0.0485 | -0.0485 | -0.0485 |
| Syllables: pkg | middle representative sizes | 4 | 4 | 0 | -0.0485 | -0.0485 | -0.0485 |
| Words | 1-4 | 4 | 4 | 0 | -0.128 | -0.128 | -0.128 |
| Words | 5-8 | 4 | 4 | 0 | -0.128 | -0.128 | -0.128 |
| Words | 9-12 | 4 | 4 | 0 | -0.128 | -0.128 | -0.128 |

### Global marginal adjusted trend

How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?

![M5 global marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m5_marginal_adjusted_global_trends.png)


### Fixed effort slices by effort unit

Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.

#### Words

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M5 Words fixed slices](../figs/m1_m6_fixed_effort_atlas/m5_nb_words_atlas_bins.png)

#### Morphemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M5 Morphemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m5_nb_morphemes_atlas_bins.png)

#### Syllables: CMU/pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M5 Syllables: CMU/pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_cmu_or_pkg_atlas_bins.png)

#### Syllables: pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M5 Syllables: pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_pkg_atlas_bins.png)

#### Phonemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M5 Phonemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m5_nb_phonemes_atlas_bins.png)

## M6: Interaction-rich exploratory model

**Question.** Do age, effort, and context entropy interact when predicting total bits?

**Formula.** `sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity`

**Takeaway.** Interaction-rich stress test. Useful for robustness, but the interactions should not become the central claim unless they are stable. In this run, 5/5 effort-unit age slopes are negative, 0/5 are positive, and 4/5 age slopes have p<.05.

**How to read the coefficient table.** The table rows are separate models, one per effort unit. The age coefficient is the monthly slope after the controls in the formula. Negative age coefficients mean lower predicted total bits with age after that effort control.

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M6 | Words | 441413 | 21 | 0.627 | -0.127 | <.001 | 6.38 | <.001 | -0.473 | <.001 | -0.00244 | 0.726 | 0.00908 | 0.111 | -0.0406 | 0.353 |
| M6 | Morphemes | 441413 | 21 | 0.614 | -0.142 | <.001 | 5.48 | <.001 | -0.517 | <.001 | 0.0039 | 0.575 | 0.0091 | 0.070 | -0.0649 | 0.170 |
| M6 | Syllables: CMU/pkg | 441413 | 21 | 0.647 | -0.0679 | 0.016 | 5.21 | <.001 | -0.543 | <.001 | 0.00902 | 0.154 | 0.00658 | 0.202 | -0.0544 | 0.123 |
| M6 | Syllables: pkg | 441413 | 21 | 0.631 | -0.0523 | 0.053 | 4.8 | <.001 | -0.544 | <.001 | 0.0121 | 0.017 | 0.00518 | 0.277 | -0.0404 | 0.200 |
| M6 | Phonemes | 441413 | 21 | 0.646 | -0.0685 | 0.019 | 2.08 | <.001 | -0.585 | <.001 | 0.00355 | 0.200 | 0.00833 | 0.086 | -0.0289 | 0.122 |

**How to read the fixed-slice slope table.** These are descriptive slopes computed from the plotted prediction lines. `mean_slope_bits_per_month` says how many predicted Mistral bits the line changes per month inside that atlas bin. This table is not a separate fitted model and has no p-values; inference is in the coefficient table above.

| effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | min_slope_bits_per_month | max_slope_bits_per_month | mean_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | 1-4 | 4 | 4 | 0 | -0.149 | -0.138 | -0.143 |
| Morphemes | 5-8 | 4 | 4 | 0 | -0.134 | -0.122 | -0.128 |
| Morphemes | 9-12 | 4 | 4 | 0 | -0.118 | -0.106 | -0.112 |
| Phonemes |  | 7 | 7 | 0 | -0.0933 | -0.0295 | -0.0462 |
| Phonemes | high representative sizes | 4 | 4 | 0 | -0.0614 | -0.0507 | -0.0561 |
| Phonemes | low representative sizes | 4 | 4 | 0 | -0.0898 | -0.0791 | -0.0844 |
| Phonemes | middle representative sizes | 4 | 4 | 0 | -0.0756 | -0.0649 | -0.0703 |
| Syllables: CMU/pkg | high representative sizes | 4 | 2 | 2 | -0.0158 | 0.0113 | -0.00223 |
| Syllables: CMU/pkg | low representative sizes | 4 | 4 | 0 | -0.088 | -0.0609 | -0.0744 |
| Syllables: CMU/pkg | middle representative sizes | 4 | 4 | 0 | -0.0519 | -0.0248 | -0.0383 |
| Syllables: pkg | high representative sizes | 4 | 0 | 4 | 0.0152 | 0.0515 | 0.0334 |
| Syllables: pkg | low representative sizes | 4 | 4 | 0 | -0.0815 | -0.0452 | -0.0634 |
| Syllables: pkg | middle representative sizes | 4 | 3 | 1 | -0.0332 | 0.00313 | -0.015 |
| Words | 1-4 | 4 | 4 | 0 | -0.131 | -0.123 | -0.127 |
| Words | 5-8 | 4 | 4 | 0 | -0.14 | -0.133 | -0.137 |
| Words | 9-12 | 4 | 4 | 0 | -0.15 | -0.143 | -0.146 |

### Global marginal adjusted trend

How to read: this is the single global adjusted line. It averages predictions over observed effort values, children, and context rows, so it is not a one-length-only plot. It is the best compact answer to the question: after the model controls, what is the overall developmental direction?

![M6 global marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m6_marginal_adjusted_global_trends.png)


### Fixed effort slices by effort unit

Each figure below uses the same fitted model, but shows conditional predictions for exact fixed effort values. For words and morphemes the panels are 1-4, 5-8, and 9-12. For syllables and phonemes the panels split the 12 most frequent observed values into low/middle/high representative groups.

#### Words

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M6 Words fixed slices](../figs/m1_m6_fixed_effort_atlas/m6_nb_words_atlas_bins.png)

#### Morphemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M6 Morphemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m6_nb_morphemes_atlas_bins.png)

#### Syllables: CMU/pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M6 Syllables: CMU/pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_cmu_or_pkg_atlas_bins.png)

#### Syllables: pkg

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M6 Syllables: pkg fixed slices](../figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_pkg_atlas_bins.png)

#### Phonemes

How to read: each colored line is an exact fixed effort value. The model was fit on all eligible utterances; only the plotted prediction slice changes. The shaded ribbon is the model confidence band for the fitted mean line, not the full spread of observed utterances.

![M6 Phonemes fixed slices](../figs/m1_m6_fixed_effort_atlas/m6_nb_phonemes_atlas_bins.png)


## Hottest Takeaways For The Research Question

- The largest descriptive fit is M6 with mean in-sample R2=0.633 across effort units. This is variance explained by the fitted predictors in the current data, not held-out prediction accuracy.
- Adding child identity changes the developmental conclusion: M1 has 0/5 negative age slopes, while M2 has 5/5. That is the core reason child-adjusted models are scientifically central here.
- Age is significant in 25/30 fitted model-effort rows, with 23 significant negative coefficients. Negative means lower predicted total bits with development after the controls in that formula.
- Context entropy is significant in 15/15 rows where it is included. This supports keeping context information as a candidate control/predictor, but it remains tied to the current entropy-estimation method.
- Across the plotted fixed-effort slices, 324/402 exact conditional age trajectories slope downward. These slice slopes are descriptive prediction summaries, useful for checking whether the global conclusion depends on a particular effort value.

## Saved Atlas Outputs

```text
results/m1_m6_fixed_effort_atlas/atlas_effort_bin_definitions.csv
results/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution.csv
results/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution_by_age.csv
results/m1_m6_fixed_effort_atlas/atlas_model_fit_summary.csv
results/m1_m6_fixed_effort_atlas/atlas_predictor_significance_summary.csv
results/m1_m6_fixed_effort_atlas/atlas_fixed_slice_slopes.csv
results/m1_m6_fixed_effort_atlas/atlas_figure_manifest.csv
figs/m1_m6_fixed_effort_atlas/
```
