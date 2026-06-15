# Age-Trajectory Robustness: Balanced Bootstrap and Scrambling Controls

This is a complementary validation report for the utterance-level information
models. It asks a very specific question:

```text
Do the developmental age effects survive equalized age-bin sampling, and do
they weaken when we deliberately break the true age ordering?
```

This report does not replace the main M1-M6 model reports and it does not
modify any source data.

The design is inspired by Pawar and Cychosz (2025), who used equalized
age-bin samples and age-label scrambling controls to test whether a
developmental informativity trajectory was real rather than an artifact of bin
composition.

## Data And Unit

The analysis uses real child utterances only, then aggregates them to:

```text
child x session x context window
```

This is intentional. The scrambling tests should not pretend that millions of
utterance rows are independent. Each unit stores the mean total bits,
mean effort, mean context entropy when available, and the number of utterances
that contributed to that unit.

The default data path streams the split scored-result tree file by file and
then writes the compact unit frame. Future refits can use that unit frame
directly instead of rereading the scored files.

## Audit Summary

| source | source_path | source_files_read | source_rows_read | source_rows_kept | source_rows_dropped | unit_rows | children | datasets | child_sessions | context_windows | age_bins |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scored-tree | results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023 | 84 | 1.788e+06 | 1.788e+06 | 0 | 3932 | 21 | 3 | 983 | k0,k1,k2,k3 | 006-023,024-029,030-035,036-041,042-047,048-053,054-059,060-065 |

### Source Coverage By Context Window

| context_k | files | rows_read | rows_kept | rows_dropped | entropy_matched_rows | entropy_missing_rows |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | 21 | 4.47e+05 | 4.47e+05 | 0 | 0 | 4.47e+05 |
| k1 | 21 | 4.47e+05 | 4.47e+05 | 0 | 4.422e+05 | 4765 |
| k2 | 21 | 4.47e+05 | 4.47e+05 | 0 | 4.415e+05 | 5524 |
| k3 | 21 | 4.47e+05 | 4.47e+05 | 0 | 4.414e+05 | 5572 |

**How to read this table.** `rows_read` is the number of scored real-child
utterance rows found in the split files. `rows_kept` is the number retained
before aggregation. `rows_dropped` should be zero. `entropy_matched_rows`
applies to k1-k3; k0 intentionally has no context entropy because no context is
provided.

![age-bin unit support](../figs/age_scrambling_robustness/age_bin_unit_support.png)

**How to read this plot.** Bars show how many child-session-context units are
available in each age bin. This makes clear where the developmental trajectory
has strong or weak support.

## Robustness Checks

| check | what it asks | what would reassure us |
| --- | --- | --- |
| balanced bootstrap | Does the age effect survive when every age bin contributes the same number of units? | The real slope keeps the same direction and sits away from zero. |
| age-bin label scramble | Could the trend appear if whole age-bin labels were assigned to the wrong bins? | The real slope is stronger than these scrambled slopes. |
| unit-age scramble | Could the trend appear after randomly disconnecting units from their true ages? | The real slope is stronger than these scrambled slopes. |
| within-child age scramble | Could the trend appear from child-specific style alone if each child's timeline is broken? | The real slope is stronger than this within-child null. |

## Model Map

| model_id | question | formula | context_windows |
| --- | --- | --- | --- |
| M1 | Does age predict total bits after controlling production effort, pooling children? | mean_sum_bits ~ age + mean_effort | k0-k3 |
| M2 | Does the age effect remain after controlling each child's baseline? | mean_sum_bits ~ age + mean_effort + child identity | k0-k3 |
| M3 | Does the age effect change as production effort changes? | mean_sum_bits ~ age * mean_effort + child identity | k0-k3 |
| M4 | Does the age effect remain after effort, child identity, and context entropy are controlled? | mean_sum_bits ~ age + mean_effort + mean_context_entropy + child identity | k1-k3 only |
| M5 | Does the context-entropy association change over developmental time? | mean_sum_bits ~ age * mean_context_entropy + mean_effort + child identity | k1-k3 only |
| M6 | Do age, effort, and context entropy interact when predicting total bits? | mean_sum_bits ~ age * mean_effort + age * mean_context_entropy + mean_effort * mean_context_entropy + child identity | k1-k3 only |

## Overview Plot

![observed age slope overview](../figs/age_scrambling_robustness/observed_age_slope_overview.png)

**How to read this plot.** Each point is an observed age coefficient from a
unit-level model. Negative values mean predicted total Mistral bits decrease
with age after the model's controls. This is a map of the results; the model
sections below give the interpretable regression-line views.

## Compact Robustness Summary

| model_id | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | age_bin_group_scramble | 20 | 2 | 16 | 0.5115 | 0.010 |
| M1 | balanced_bootstrap | 20 | 2 | 16 | 0.866 |  |
| M1 | unit_age_scramble | 20 | 2 | 20 | 0.5195 | 0.010 |
| M1 | within_child_age_scramble | 20 | 2 | 13 | 0.9 | 0.812 |
| M2 | age_bin_group_scramble | 20 | 20 | 20 | 0.4895 | 0.010 |
| M2 | balanced_bootstrap | 20 | 20 | 1 | 0.996 |  |
| M2 | unit_age_scramble | 20 | 20 | 20 | 0.513 | 0.010 |
| M2 | within_child_age_scramble | 20 | 20 | 20 | 0.509 | 0.010 |
| M3 | age_bin_group_scramble | 20 | 20 | 20 | 0.5215 | 0.010 |
| M3 | balanced_bootstrap | 20 | 20 | 4 | 0.9975 |  |
| M3 | unit_age_scramble | 20 | 20 | 20 | 0.4845 | 0.010 |
| M3 | within_child_age_scramble | 20 | 20 | 20 | 0.455 | 0.010 |
| M4 | age_bin_group_scramble | 15 | 15 | 14 | 0.5207 | 0.020 |
| M4 | balanced_bootstrap | 15 | 15 | 4 | 0.9807 |  |
| M4 | unit_age_scramble | 15 | 15 | 15 | 0.51 | 0.010 |
| M4 | within_child_age_scramble | 15 | 15 | 15 | 0.498 | 0.010 |
| M5 | age_bin_group_scramble | 15 | 15 | 11 | 0.5173 | 0.030 |
| M5 | balanced_bootstrap | 15 | 15 | 2 | 0.9693 |  |
| M5 | unit_age_scramble | 15 | 15 | 15 | 0.4973 | 0.010 |
| M5 | within_child_age_scramble | 15 | 15 | 15 | 0.4227 | 0.010 |
| M6 | age_bin_group_scramble | 15 | 15 | 15 | 0.5173 | 0.010 |
| M6 | balanced_bootstrap | 15 | 15 | 0 | 0.9767 |  |
| M6 | unit_age_scramble | 15 | 15 | 15 | 0.4893 | 0.010 |
| M6 | within_child_age_scramble | 15 | 15 | 15 | 0.5293 | 0.010 |

**How to read this table.** `outside_null_95` counts how many
model/effort/context rows had a real observed age coefficient outside the
2.5%-97.5% interval of the bootstrap or scrambling distribution. Higher values
mean the real age slope is less compatible with that null check.
`same_sign_share` is most useful for the balanced bootstrap: values near 1 mean
the age slope direction is stable under balanced age-bin resampling.

## Model Cards

The line plots below are effect-line visualizations. The underlying data are
not changed. Each line is anchored at the observed mean of the unit frame and
uses the fitted age coefficient to show the age effect. This avoids arbitrary
fixed-effect intercept choices while making the slope visually readable.

## M1: Pooled age and effort

**Question.** Does age predict total bits after controlling production effort, pooling children?

**Formula.** `mean_sum_bits ~ age + mean_effort`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

![M1 clear robustness regression lines](../figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png)

**Quick read.** Across all fitted variants for this model,
10% of observed age slopes are negative, and
81% of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

| context | effort | observed age slope | balanced 95% slope interval | balanced same-sign | bin-label scramble p | unit-age scramble p | within-child scramble p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | Morphemes | -0.01707 | [-0.0556, -0.0122] | 1 | 0.277 | 0.010 | 1.000 |
| k0 | Phonemes | 0.03861 | [-0.000219, 0.0277] | 0.97 | 0.020 | 0.010 | 1.000 |
| k0 | Syllables: CMU/pkg | 0.02009 | [-0.0182, 0.014] | 0.45 | 0.238 | 0.010 | 1.000 |
| k0 | Syllables: pkg | 0.02073 | [-0.0211, 0.0132] | 0.36 | 0.129 | 0.010 | 1.000 |
| k0 | Words | -0.04465 | [-0.0783, -0.0362] | 1 | 0.010 | 0.010 | 0.010 |
| k3 | Morphemes | 0.08029 | [0.00708, 0.0663] | 0.99 | 0.010 | 0.010 | 0.861 |
| k3 | Phonemes | 0.1236 | [0.055, 0.112] | 1 | 0.010 | 0.010 | 0.020 |
| k3 | Syllables: CMU/pkg | 0.1067 | [0.0483, 0.0949] | 1 | 0.010 | 0.010 | 0.020 |
| k3 | Syllables: pkg | 0.1067 | [0.0416, 0.0959] | 1 | 0.010 | 0.010 | 0.020 |
| k3 | Words | 0.05422 | [-0.0144, 0.055] | 0.84 | 0.040 | 0.010 | 1.000 |

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.

## M2: Age and effort with child identity

**Question.** Does the age effect remain after controlling each child's baseline?

**Formula.** `mean_sum_bits ~ age + mean_effort + child identity`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

![M2 clear robustness regression lines](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

**Quick read.** Across all fitted variants for this model,
100% of observed age slopes are negative, and
76% of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

| context | effort | observed age slope | balanced 95% slope interval | balanced same-sign | bin-label scramble p | unit-age scramble p | within-child scramble p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | Morphemes | -0.1055 | [-0.178, -0.0902] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Phonemes | -0.09993 | [-0.164, -0.0892] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Syllables: CMU/pkg | -0.07624 | [-0.134, -0.0559] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Syllables: pkg | -0.07832 | [-0.139, -0.0808] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Words | -0.09487 | [-0.158, -0.082] | 1 | 0.010 | 0.010 | 0.010 |
| k3 | Morphemes | -0.04281 | [-0.178, -0.0289] | 0.99 | 0.010 | 0.010 | 0.010 |
| k3 | Phonemes | -0.04589 | [-0.175, -0.00246] | 0.97 | 0.010 | 0.010 | 0.010 |
| k3 | Syllables: CMU/pkg | -0.02933 | [-0.143, -0.00376] | 0.99 | 0.050 | 0.010 | 0.010 |
| k3 | Syllables: pkg | -0.03316 | [-0.152, -0.017] | 1 | 0.010 | 0.010 | 0.010 |
| k3 | Words | -0.03999 | [-0.168, -0.0357] | 1 | 0.010 | 0.010 | 0.010 |

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.

## M3: Age by effort

**Question.** Does the age effect change as production effort changes?

**Formula.** `mean_sum_bits ~ age * mean_effort + child identity`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

![M3 clear robustness regression lines](../figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png)

**Quick read.** Across all fitted variants for this model,
100% of observed age slopes are negative, and
80% of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

| context | effort | observed age slope | balanced 95% slope interval | balanced same-sign | bin-label scramble p | unit-age scramble p | within-child scramble p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | Morphemes | -0.08293 | [-0.165, -0.0855] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Phonemes | -0.07797 | [-0.155, -0.0725] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Syllables: CMU/pkg | -0.04857 | [-0.13, -0.049] | 1 | 0.030 | 0.010 | 0.010 |
| k0 | Syllables: pkg | -0.05405 | [-0.138, -0.0674] | 1 | 0.010 | 0.010 | 0.010 |
| k0 | Words | -0.07253 | [-0.154, -0.0664] | 1 | 0.010 | 0.010 | 0.010 |
| k3 | Morphemes | -0.05223 | [-0.212, -0.0314] | 1 | 0.010 | 0.010 | 0.010 |
| k3 | Phonemes | -0.05302 | [-0.179, -0.0154] | 1 | 0.010 | 0.010 | 0.010 |
| k3 | Syllables: CMU/pkg | -0.03086 | [-0.145, -0.00672] | 0.98 | 0.079 | 0.010 | 0.010 |
| k3 | Syllables: pkg | -0.03834 | [-0.147, -0.0247] | 1 | 0.030 | 0.010 | 0.010 |
| k3 | Words | -0.05013 | [-0.186, -0.0224] | 0.99 | 0.010 | 0.010 | 0.010 |

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.

## M4: Context entropy added

**Question.** Does the age effect remain after effort, child identity, and context entropy are controlled?

**Formula.** `mean_sum_bits ~ age + mean_effort + mean_context_entropy + child identity`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

![M4 clear robustness regression lines](../figs/age_scrambling_robustness/m4_clear_robustness_regression_lines.png)

**Quick read.** Across all fitted variants for this model,
100% of observed age slopes are negative, and
80% of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

| context | effort | observed age slope | balanced 95% slope interval | balanced same-sign | bin-label scramble p | unit-age scramble p | within-child scramble p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k3 | Morphemes | -0.0417 | [-0.23, 0.00245] | 0.97 | 0.040 | 0.010 | 0.010 |
| k3 | Phonemes | -0.04311 | [-0.203, -0.00345] | 0.98 | 0.030 | 0.010 | 0.010 |
| k3 | Syllables: CMU/pkg | -0.02597 | [-0.202, 0.0217] | 0.88 | 0.149 | 0.010 | 0.030 |
| k3 | Syllables: pkg | -0.02994 | [-0.156, -0.00262] | 0.98 | 0.040 | 0.010 | 0.010 |
| k3 | Words | -0.03831 | [-0.186, 0.0285] | 0.91 | 0.020 | 0.010 | 0.010 |

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.

## M5: Age by context entropy

**Question.** Does the context-entropy association change over developmental time?

**Formula.** `mean_sum_bits ~ age * mean_context_entropy + mean_effort + child identity`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

![M5 clear robustness regression lines](../figs/age_scrambling_robustness/m5_clear_robustness_regression_lines.png)

**Quick read.** Across all fitted variants for this model,
100% of observed age slopes are negative, and
72% of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

| context | effort | observed age slope | balanced 95% slope interval | balanced same-sign | bin-label scramble p | unit-age scramble p | within-child scramble p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k3 | Morphemes | -0.03644 | [-0.226, 0.0273] | 0.94 | 0.030 | 0.010 | 0.020 |
| k3 | Phonemes | -0.03788 | [-0.206, 0.012] | 0.95 | 0.050 | 0.010 | 0.010 |
| k3 | Syllables: CMU/pkg | -0.0214 | [-0.169, 0.022] | 0.88 | 0.297 | 0.010 | 0.050 |
| k3 | Syllables: pkg | -0.02499 | [-0.172, 0.0205] | 0.91 | 0.168 | 0.010 | 0.020 |
| k3 | Words | -0.03307 | [-0.181, 0.0223] | 0.86 | 0.059 | 0.010 | 0.010 |

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.

## M6: Interaction-rich stress test

**Question.** Do age, effort, and context entropy interact when predicting total bits?

**Formula.** `mean_sum_bits ~ age * mean_effort + age * mean_context_entropy + mean_effort * mean_context_entropy + child identity`

**Plain-language test.** The red line is the real age effect estimated from the
model. The blue ribbon asks whether that line survives when every age bin is
given equal influence. The purple/orange/green ribbons ask what kinds of lines
we get after breaking the true age ordering. If the red line is clearly steeper
or in a different direction than the scrambled ribbons, the developmental
ordering is doing real work.

![M6 clear robustness regression lines](../figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png)

**Quick read.** Across all fitted variants for this model,
100% of observed age slopes are negative, and
75% of model/effort/context/method checks put the observed
slope outside the corresponding null 95% interval.

**Compact result table.**

| context | effort | observed age slope | balanced 95% slope interval | balanced same-sign | bin-label scramble p | unit-age scramble p | within-child scramble p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k3 | Morphemes | -0.06312 | [-0.163, 0.0145] | 0.96 | 0.030 | 0.010 | 0.010 |
| k3 | Phonemes | -0.0569 | [-0.134, 0.0101] | 0.95 | 0.020 | 0.010 | 0.010 |
| k3 | Syllables: CMU/pkg | -0.03341 | [-0.101, 0.0406] | 0.87 | 0.079 | 0.010 | 0.010 |
| k3 | Syllables: pkg | -0.03902 | [-0.114, 0.00484] | 0.96 | 0.050 | 0.010 | 0.010 |
| k3 | Words | -0.05835 | [-0.113, 0.0204] | 0.93 | 0.030 | 0.010 | 0.010 |

**Table columns.** `observed age slope` is the estimated change in mean total
bits per additional month. Negative values mean lower predicted total bits with
age after the model's controls. `balanced 95% slope interval` is the 2.5%-97.5%
range across equal-age-bin bootstrap refits. `balanced same-sign` is the share
of bootstrap refits with the same slope direction as the observed model. The
three `scramble p` columns are permutation-style checks: small values mean the
observed slope is larger than expected after breaking the age structure.


## Diagnostic Appendix

The following two plots are compact diagnostics for checking all models at
once. They are useful for debugging and overview, but the model-card plots
above are the primary human-readable views.

![robustness heatmap](../figs/age_scrambling_robustness/robustness_outside_null_heatmap.png)

![balanced bootstrap age slope intervals](../figs/age_scrambling_robustness/balanced_bootstrap_age_slope_ci.png)

### Compact Observed Model Rows

| context_k | model_id | effort_label | n_units | n_children | n_age_bins | age_coef | r2_observed_fitted | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M1 | Words | 983 | 21 | 8 | -0.04465 | 0.9037 | fit |
| k0 | M1 | Morphemes | 983 | 21 | 8 | -0.01707 | 0.8926 | fit |
| k0 | M1 | Syllables: CMU/pkg | 983 | 21 | 8 | 0.02009 | 0.9217 | fit |
| k0 | M1 | Syllables: pkg | 983 | 21 | 8 | 0.02073 | 0.9209 | fit |
| k0 | M1 | Phonemes | 983 | 21 | 8 | 0.03861 | 0.9179 | fit |
| k0 | M2 | Words | 983 | 21 | 8 | -0.09487 | 0.9397 | fit |
| k0 | M2 | Morphemes | 983 | 21 | 8 | -0.1055 | 0.9373 | fit |
| k0 | M2 | Syllables: CMU/pkg | 983 | 21 | 8 | -0.07624 | 0.9502 | fit |
| k0 | M2 | Syllables: pkg | 983 | 21 | 8 | -0.07832 | 0.9521 | fit |
| k0 | M2 | Phonemes | 983 | 21 | 8 | -0.09993 | 0.9541 | fit |
| k0 | M3 | Words | 983 | 21 | 8 | -0.07253 | 0.941 | fit |
| k0 | M3 | Morphemes | 983 | 21 | 8 | -0.08293 | 0.9385 | fit |
| k0 | M3 | Syllables: CMU/pkg | 983 | 21 | 8 | -0.04857 | 0.9527 | fit |
| k0 | M3 | Syllables: pkg | 983 | 21 | 8 | -0.05405 | 0.9541 | fit |
| k0 | M3 | Phonemes | 983 | 21 | 8 | -0.07797 | 0.9556 | fit |
| k3 | M1 | Words | 983 | 21 | 8 | 0.05422 | 0.82 | fit |
| k3 | M1 | Morphemes | 983 | 21 | 8 | 0.08029 | 0.805 | fit |
| k3 | M1 | Syllables: CMU/pkg | 983 | 21 | 8 | 0.1067 | 0.8375 | fit |
| k3 | M1 | Syllables: pkg | 983 | 21 | 8 | 0.1067 | 0.8383 | fit |
| k3 | M1 | Phonemes | 983 | 21 | 8 | 0.1236 | 0.8311 | fit |
| k3 | M2 | Words | 983 | 21 | 8 | -0.03999 | 0.9004 | fit |
| k3 | M2 | Morphemes | 983 | 21 | 8 | -0.04281 | 0.8949 | fit |
| k3 | M2 | Syllables: CMU/pkg | 983 | 21 | 8 | -0.02933 | 0.9119 | fit |
| k3 | M2 | Syllables: pkg | 983 | 21 | 8 | -0.03316 | 0.9147 | fit |
| k3 | M2 | Phonemes | 983 | 21 | 8 | -0.04589 | 0.9124 | fit |
| k3 | M3 | Words | 983 | 21 | 8 | -0.05013 | 0.9006 | fit |
| k3 | M3 | Morphemes | 983 | 21 | 8 | -0.05223 | 0.8951 | fit |
| k3 | M3 | Syllables: CMU/pkg | 983 | 21 | 8 | -0.03086 | 0.9119 | fit |
| k3 | M3 | Syllables: pkg | 983 | 21 | 8 | -0.03834 | 0.9148 | fit |
| k3 | M3 | Phonemes | 983 | 21 | 8 | -0.05302 | 0.9126 | fit |
| k3 | M4 | Words | 976 | 21 | 8 | -0.03831 | 0.908 | fit |
| k3 | M4 | Morphemes | 976 | 21 | 8 | -0.0417 | 0.9026 | fit |
| k3 | M4 | Syllables: CMU/pkg | 976 | 21 | 8 | -0.02597 | 0.9185 | fit |
| k3 | M4 | Syllables: pkg | 976 | 21 | 8 | -0.02994 | 0.9218 | fit |
| k3 | M4 | Phonemes | 976 | 21 | 8 | -0.04311 | 0.9193 | fit |
| k3 | M5 | Words | 976 | 21 | 8 | -0.03307 | 0.9104 | fit |
| k3 | M5 | Morphemes | 976 | 21 | 8 | -0.03644 | 0.9052 | fit |
| k3 | M5 | Syllables: CMU/pkg | 976 | 21 | 8 | -0.0214 | 0.9214 | fit |
| k3 | M5 | Syllables: pkg | 976 | 21 | 8 | -0.02499 | 0.9241 | fit |
| k3 | M5 | Phonemes | 976 | 21 | 8 | -0.03788 | 0.9212 | fit |
| k3 | M6 | Words | 976 | 21 | 8 | -0.05835 | 0.9141 | fit |
| k3 | M6 | Morphemes | 976 | 21 | 8 | -0.06312 | 0.9084 | fit |
| k3 | M6 | Syllables: CMU/pkg | 976 | 21 | 8 | -0.03341 | 0.9236 | fit |
| k3 | M6 | Syllables: pkg | 976 | 21 | 8 | -0.03902 | 0.927 | fit |
| k3 | M6 | Phonemes | 976 | 21 | 8 | -0.0569 | 0.9248 | fit |

**How to read this table.** `age_coef` is the model's age slope. `r2` is the
share of unit-level variance explained by the fitted values in that model row.
This table is intentionally compact; full replicate slopes are saved as CSV.

## Files

- Unit-level frame: `results/age_scrambling_robustness/age_scrambling_unit_frame.csv.gz`
- Source-file audit: `results/age_scrambling_robustness/age_scrambling_source_file_audit.csv`
- Observed fits: `results/age_scrambling_robustness/age_scrambling_observed_model_summary.csv`
- Replicate slopes: `results/age_scrambling_robustness/age_scrambling_replicate_age_slopes.csv.gz`
- Robustness summary: `results/age_scrambling_robustness/age_scrambling_robustness_summary.csv`
- Figures: `figs/age_scrambling_robustness`
