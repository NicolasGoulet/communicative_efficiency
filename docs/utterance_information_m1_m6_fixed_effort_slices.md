# M1-M6 Fixed-Effort Slice Predictions

This report replaces the insufficient median-only view. It repeats the M1-M6
continuous-effort prediction stage across many exact fixed effort values.

Important: the models are still fit on all eligible real child utterances. The
fixed values only define the prediction lines.

Why the script refits: the previous reports saved coefficient CSVs and figures,
but not serialized model objects. To generate new prediction grids, we refit the
same formulas once per model/effort unit, then write new predictions. We do not
fit separate models for each fixed effort value.

## Outputs

```text
results/m1_m6_fixed_effort_slices/fixed_effort_model_summary.csv
results/m1_m6_fixed_effort_slices/marginal_adjusted_predictions.csv
results/m1_m6_fixed_effort_slices/fixed_effort_predictions.csv
results/m1_m6_fixed_effort_slices/selected_fixed_effort_values.csv
figs/m1_m6_fixed_effort_slices/
```

## Statistical Checkpoint

This follows the Advanced Data Analytics guidance checked on 2026-06-09:

- outcome is continuous (`sum_bits`);
- rows are repeated within children, so child identity must be handled in the
  model family or uncertainty structure;
- fitting and reporting are separated: run `--stage analysis` for models and
  predictions, and `--stage report` for Markdown/HTML only;
- the single global line is a **marginal adjusted prediction**, not a new
  inferential test;
- fixed-slice lines are conditional prediction views, not separate fitted
  models for each length.

## Selected Fixed Values

| plot_group | effort | values | n_values |
| --- | --- | --- | --- |
| granular_primary | Morphemes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 |
| granular_primary | Phonemes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 19 |
| granular_primary | Syllables: CMU/pkg | 1, 2, 3, 4, 5, 6, 7, 8 | 8 |
| granular_primary | Syllables: pkg | 1, 2, 3, 4, 5, 6, 7, 8 | 8 |
| granular_primary | Words | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 |
| primary_anchors_p25_p50_p75 | Morphemes | 1, 2, 4 | 3 |
| primary_anchors_p25_p50_p75 | Phonemes | 3, 7, 11 | 3 |
| primary_anchors_p25_p50_p75 | Syllables: CMU/pkg | 1, 3, 4 | 3 |
| primary_anchors_p25_p50_p75 | Syllables: pkg | 1, 3, 5 | 3 |
| primary_anchors_p25_p50_p75 | Words | 1, 2, 4 | 3 |
| top_frequency_12 | Morphemes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 |
| top_frequency_12 | Phonemes | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 12 |
| top_frequency_12 | Syllables: CMU/pkg | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 |
| top_frequency_12 | Syllables: pkg | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 |
| top_frequency_12 | Words | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 |
| wide_anchors_p10_p50_p90 | Morphemes | 1, 2, 6 | 3 |
| wide_anchors_p10_p50_p90 | Phonemes | 2, 7, 16 | 3 |
| wide_anchors_p10_p50_p90 | Syllables: CMU/pkg | 1, 3, 6 | 3 |
| wide_anchors_p10_p50_p90 | Syllables: pkg | 1, 3, 7 | 3 |
| wide_anchors_p10_p50_p90 | Words | 1, 2, 5 | 3 |

## Plot Readability Rule

The model predictions are computed for all selected fixed values. The figures
are capped for readability: dense granular panels display at most
8 representative values per effort unit. The full set
remains in `fixed_effort_predictions.csv`.

| plot_group | effort_label | displayed_fixed_values | n_displayed_values | n_all_values | display_note |
| --- | --- | --- | --- | --- | --- |
| granular_primary | Morphemes | 1, 3, 4, 6, 7, 9, 10, 12 | 8 | 12 | full values saved in prediction CSV |
| granular_primary | Phonemes | 1, 4, 6, 9, 11, 14, 16, 19 | 8 | 19 | full values saved in prediction CSV |
| granular_primary | Syllables: CMU/pkg | 1, 2, 3, 4, 5, 6, 7, 8 | 8 | 8 | all values displayed |
| granular_primary | Syllables: pkg | 1, 2, 3, 4, 5, 6, 7, 8 | 8 | 8 | all values displayed |
| granular_primary | Words | 1, 3, 4, 6, 7, 9, 10, 12 | 8 | 12 | full values saved in prediction CSV |
| primary_anchors_p25_p50_p75 | Morphemes | 1, 2, 4 | 3 | 3 | all values displayed |
| primary_anchors_p25_p50_p75 | Phonemes | 3, 7, 11 | 3 | 3 | all values displayed |
| primary_anchors_p25_p50_p75 | Syllables: CMU/pkg | 1, 3, 4 | 3 | 3 | all values displayed |
| primary_anchors_p25_p50_p75 | Syllables: pkg | 1, 3, 5 | 3 | 3 | all values displayed |
| primary_anchors_p25_p50_p75 | Words | 1, 2, 4 | 3 | 3 | all values displayed |
| top_frequency_12 | Morphemes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 | 12 | all values displayed |
| top_frequency_12 | Phonemes | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | 12 | 12 | all values displayed |
| top_frequency_12 | Syllables: CMU/pkg | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 | 12 | all values displayed |
| top_frequency_12 | Syllables: pkg | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 | 12 | all values displayed |
| top_frequency_12 | Words | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 12 | 12 | all values displayed |
| wide_anchors_p10_p50_p90 | Morphemes | 1, 2, 6 | 3 | 3 | all values displayed |
| wide_anchors_p10_p50_p90 | Phonemes | 2, 7, 16 | 3 | 3 | all values displayed |
| wide_anchors_p10_p50_p90 | Syllables: CMU/pkg | 1, 3, 6 | 3 | 3 | all values displayed |
| wide_anchors_p10_p50_p90 | Syllables: pkg | 1, 3, 7 | 3 | 3 | all values displayed |
| wide_anchors_p10_p50_p90 | Words | 1, 2, 5 | 3 | 3 | all values displayed |

## Model Summary

| model_id | effort_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Words | 446985 | 21 | 0.613 | 0.000309 | 0.993 | 6.35 | 0 |  |  |  |  |  |  |
| M1 | Morphemes | 446985 | 21 | 0.598 | 0.00902 | 0.774 | 5.45 | 2.68e-300 |  |  |  |  |  |  |
| M1 | Syllables: CMU/pkg | 446985 | 21 | 0.635 | 0.0514 | 0.0526 | 5.21 | 2.06e-264 |  |  |  |  |  |  |
| M1 | Syllables: pkg | 446985 | 21 | 0.618 | 0.069 | 0.0118 | 4.82 | 2.3e-306 |  |  |  |  |  |  |
| M1 | Phonemes | 446985 | 21 | 0.632 | 0.0681 | 0.0115 | 2.07 | 4.13e-239 |  |  |  |  |  |  |
| M2 | Words | 446985 | 21 | 0.626 | -0.122 | 4.42e-05 | 6.37 | 0 |  |  |  |  |  |  |
| M2 | Morphemes | 446985 | 21 | 0.613 | -0.136 | 0.000252 | 5.49 | 8.54e-271 |  |  |  |  |  |  |
| M2 | Syllables: CMU/pkg | 446985 | 21 | 0.646 | -0.0633 | 0.0177 | 5.24 | 4.14e-290 |  |  |  |  |  |  |
| M2 | Syllables: pkg | 446985 | 21 | 0.63 | -0.0485 | 0.0494 | 4.83 | 0 |  |  |  |  |  |  |
| M2 | Phonemes | 446985 | 21 | 0.644 | -0.0649 | 0.0135 | 2.08 | 8.23e-239 |  |  |  |  |  |  |
| M3 | Words | 446985 | 21 | 0.626 | -0.122 | 4.16e-05 | 6.38 | 0 |  |  | -0.00379 | 0.515 |  |  |
| M3 | Morphemes | 446985 | 21 | 0.613 | -0.136 | 0.000311 | 5.48 | 3.37e-275 |  |  | 0.00228 | 0.727 |  |  |
| M3 | Syllables: CMU/pkg | 446985 | 21 | 0.646 | -0.0659 | 0.017 | 5.22 | 4.14e-298 |  |  | 0.00703 | 0.252 |  |  |
| M3 | Syllables: pkg | 446985 | 21 | 0.63 | -0.0521 | 0.0554 | 4.81 | 0 |  |  | 0.00986 | 0.0218 |  |  |
| M3 | Phonemes | 446985 | 21 | 0.644 | -0.0672 | 0.0169 | 2.08 | 5.97e-269 |  |  | 0.00273 | 0.22 |  |  |
| M4 | Words | 441413 | 21 | 0.627 | -0.127 | 3.29e-05 | 6.37 | 0 | -0.472 | 8.14e-37 |  |  |  |  |
| M4 | Morphemes | 441413 | 21 | 0.614 | -0.14 | 0.000192 | 5.49 | 2.53e-258 | -0.512 | 4.22e-43 |  |  |  |  |
| M4 | Syllables: CMU/pkg | 441413 | 21 | 0.647 | -0.0645 | 0.0133 | 5.23 | 1.92e-281 | -0.54 | 7.26e-57 |  |  |  |  |
| M4 | Syllables: pkg | 441413 | 21 | 0.63 | -0.048 | 0.0384 | 4.83 | 0 | -0.541 | 2.56e-59 |  |  |  |  |
| M4 | Phonemes | 441413 | 21 | 0.645 | -0.0652 | 0.0128 | 2.08 | 2.45e-231 | -0.581 | 3.34e-70 |  |  |  |  |
| M5 | Words | 441413 | 21 | 0.627 | -0.128 | 4.34e-05 | 6.37 | 0 | -0.47 | 2.15e-41 |  |  | 0.00614 | 0.284 |
| M5 | Morphemes | 441413 | 21 | 0.614 | -0.141 | 0.000231 | 5.49 | 3.74e-258 | -0.511 | 1.78e-47 |  |  | 0.00471 | 0.339 |
| M5 | Syllables: CMU/pkg | 441413 | 21 | 0.647 | -0.0649 | 0.015 | 5.23 | 3.23e-281 | -0.539 | 1.57e-62 |  |  | 0.00396 | 0.478 |
| M5 | Syllables: pkg | 441413 | 21 | 0.63 | -0.0485 | 0.0422 | 4.83 | 0 | -0.54 | 2.2e-65 |  |  | 0.00395 | 0.481 |
| M5 | Phonemes | 441413 | 21 | 0.645 | -0.0657 | 0.0144 | 2.08 | 3.94e-231 | -0.581 | 4.07e-81 |  |  | 0.00465 | 0.407 |
| M6 | Words | 441413 | 21 | 0.627 | -0.127 | 4.76e-05 | 6.38 | 0 | -0.473 | 4.91e-39 | -0.00244 | 0.726 | 0.00908 | 0.111 |
| M6 | Morphemes | 441413 | 21 | 0.614 | -0.142 | 0.000332 | 5.48 | 4.19e-280 | -0.517 | 2.9e-42 | 0.0039 | 0.575 | 0.0091 | 0.0702 |
| M6 | Syllables: CMU/pkg | 441413 | 21 | 0.647 | -0.0679 | 0.0161 | 5.21 | 4.14e-305 | -0.543 | 8.61e-56 | 0.00902 | 0.154 | 0.00658 | 0.202 |
| M6 | Syllables: pkg | 441413 | 21 | 0.631 | -0.0523 | 0.0526 | 4.8 | 0 | -0.544 | 1.98e-59 | 0.0121 | 0.0173 | 0.00518 | 0.277 |
| M6 | Phonemes | 441413 | 21 | 0.646 | -0.0685 | 0.0186 | 2.08 | 5.41e-278 | -0.585 | 3.98e-65 | 0.00355 | 0.2 | 0.00833 | 0.0859 |

## M1: Pooled age and effort

Question: Pooling all children, does age predict total bits after controlling utterance effort?

### Global adjusted trend

How to read: this is the single global age trend after accounting for effort and child/context composition by averaging predictions over observed rows. It is not restricted to one length.

![M1 marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m1_marginal_adjusted_global_trends.png)

How to read: each line is a prediction from the same fitted model, but at a different exact fixed effort value. The model was fit on all utterance lengths; only the prediction slice changes.

### Top 12 most frequent exact effort sizes

![M1 top_frequency_12](../figs/m1_m6_fixed_effort_slices/m1_top_frequency_12_fixed_effort_slices.png)

### Words/morphemes 1-12; syllables/phonemes data-supported dense core

![M1 granular_primary](../figs/m1_m6_fixed_effort_slices/m1_granular_primary_fixed_effort_slices.png)

### Primary low/median/high fixed slices

![M1 primary_anchors_p25_p50_p75](../figs/m1_m6_fixed_effort_slices/m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png)

### Wide low/median/high fixed slices

![M1 wide_anchors_p10_p50_p90](../figs/m1_m6_fixed_effort_slices/m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png)

## M2: Age and effort with child identity

Question: Does the developmental age effect remain after child identity is controlled?

### Global adjusted trend

How to read: this is the single global age trend after accounting for effort and child/context composition by averaging predictions over observed rows. It is not restricted to one length.

![M2 marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m2_marginal_adjusted_global_trends.png)

How to read: each line is a prediction from the same fitted model, but at a different exact fixed effort value. The model was fit on all utterance lengths; only the prediction slice changes.

### Top 12 most frequent exact effort sizes

![M2 top_frequency_12](../figs/m1_m6_fixed_effort_slices/m2_top_frequency_12_fixed_effort_slices.png)

### Words/morphemes 1-12; syllables/phonemes data-supported dense core

![M2 granular_primary](../figs/m1_m6_fixed_effort_slices/m2_granular_primary_fixed_effort_slices.png)

### Primary low/median/high fixed slices

![M2 primary_anchors_p25_p50_p75](../figs/m1_m6_fixed_effort_slices/m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png)

### Wide low/median/high fixed slices

![M2 wide_anchors_p10_p50_p90](../figs/m1_m6_fixed_effort_slices/m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png)

## M3: Age by effort

Question: Does the relation between effort and total bits change with age?

### Global adjusted trend

How to read: this is the single global age trend after accounting for effort and child/context composition by averaging predictions over observed rows. It is not restricted to one length.

![M3 marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m3_marginal_adjusted_global_trends.png)

How to read: each line is a prediction from the same fitted model, but at a different exact fixed effort value. The model was fit on all utterance lengths; only the prediction slice changes.

### Top 12 most frequent exact effort sizes

![M3 top_frequency_12](../figs/m1_m6_fixed_effort_slices/m3_top_frequency_12_fixed_effort_slices.png)

### Words/morphemes 1-12; syllables/phonemes data-supported dense core

![M3 granular_primary](../figs/m1_m6_fixed_effort_slices/m3_granular_primary_fixed_effort_slices.png)

### Primary low/median/high fixed slices

![M3 primary_anchors_p25_p50_p75](../figs/m1_m6_fixed_effort_slices/m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png)

### Wide low/median/high fixed slices

![M3 wide_anchors_p10_p50_p90](../figs/m1_m6_fixed_effort_slices/m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png)

## M4: Context entropy added

Question: Does context entropy add predictive information beyond age, effort, and child identity?

### Global adjusted trend

How to read: this is the single global age trend after accounting for effort and child/context composition by averaging predictions over observed rows. It is not restricted to one length.

![M4 marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m4_marginal_adjusted_global_trends.png)

How to read: each line is a prediction from the same fitted model, but at a different exact fixed effort value. The model was fit on all utterance lengths; only the prediction slice changes.

### Top 12 most frequent exact effort sizes

![M4 top_frequency_12](../figs/m1_m6_fixed_effort_slices/m4_top_frequency_12_fixed_effort_slices.png)

### Words/morphemes 1-12; syllables/phonemes data-supported dense core

![M4 granular_primary](../figs/m1_m6_fixed_effort_slices/m4_granular_primary_fixed_effort_slices.png)

### Primary low/median/high fixed slices

![M4 primary_anchors_p25_p50_p75](../figs/m1_m6_fixed_effort_slices/m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png)

### Wide low/median/high fixed slices

![M4 wide_anchors_p10_p50_p90](../figs/m1_m6_fixed_effort_slices/m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png)

## M5: Age by context entropy

Question: Does the context-entropy effect on total bits change over development?

### Global adjusted trend

How to read: this is the single global age trend after accounting for effort and child/context composition by averaging predictions over observed rows. It is not restricted to one length.

![M5 marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m5_marginal_adjusted_global_trends.png)

How to read: each line is a prediction from the same fitted model, but at a different exact fixed effort value. The model was fit on all utterance lengths; only the prediction slice changes.

### Top 12 most frequent exact effort sizes

![M5 top_frequency_12](../figs/m1_m6_fixed_effort_slices/m5_top_frequency_12_fixed_effort_slices.png)

### Words/morphemes 1-12; syllables/phonemes data-supported dense core

![M5 granular_primary](../figs/m1_m6_fixed_effort_slices/m5_granular_primary_fixed_effort_slices.png)

### Primary low/median/high fixed slices

![M5 primary_anchors_p25_p50_p75](../figs/m1_m6_fixed_effort_slices/m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png)

### Wide low/median/high fixed slices

![M5 wide_anchors_p10_p50_p90](../figs/m1_m6_fixed_effort_slices/m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png)

## M6: Interaction-rich exploratory model

Question: Do age, effort, and context entropy interact when predicting total bits?

### Global adjusted trend

How to read: this is the single global age trend after accounting for effort and child/context composition by averaging predictions over observed rows. It is not restricted to one length.

![M6 marginal adjusted trend](../figs/m1_m6_fixed_effort_slices/m6_marginal_adjusted_global_trends.png)

How to read: each line is a prediction from the same fitted model, but at a different exact fixed effort value. The model was fit on all utterance lengths; only the prediction slice changes.

### Top 12 most frequent exact effort sizes

![M6 top_frequency_12](../figs/m1_m6_fixed_effort_slices/m6_top_frequency_12_fixed_effort_slices.png)

### Words/morphemes 1-12; syllables/phonemes data-supported dense core

![M6 granular_primary](../figs/m1_m6_fixed_effort_slices/m6_granular_primary_fixed_effort_slices.png)

### Primary low/median/high fixed slices

![M6 primary_anchors_p25_p50_p75](../figs/m1_m6_fixed_effort_slices/m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png)

### Wide low/median/high fixed slices

![M6 wide_anchors_p10_p50_p90](../figs/m1_m6_fixed_effort_slices/m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png)

