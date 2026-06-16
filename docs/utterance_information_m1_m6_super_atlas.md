# Exhaustive Internal M1-M6 Model Atlas

This is an internal source report for cherry-picking into the supervisor-facing writeup. It is intentionally broader than a polished manuscript section: it pulls together the M1-M6 model ladder, estimator-sensitivity checks, fixed-effort slices, context-window variants, and age-scrambling robustness checks.

It does not pretend that every model is equally central. The report separates the primary scientific interpretation from sensitivity checks and clearly states when a model is ordinary least squares, when child identity is a fixed effect, when uncertainty is child-clustered, and when a GEE/GLM/MixedLM sensitivity was used.

Outcome throughout the M1-M6 ladder:

```text
sum_bits
```

Primary practical reading rule: the most supervisor-ready result is still the child-adjusted fixed-effort story, especially M2 and the fixed-effort slices. M3-M6 are valuable for stress-testing and for deciding which nuance belongs in the dissertation/report, but they should not all become headline claims.

## Coverage Snapshot

| model | dual_rows | estimator_sensitivity_rows | context_rows | robustness_rows | figure_rows |
| --- | --- | --- | --- | --- | --- |
| M1 | 10 | 20 | 20 | 80 | 46 |
| M2 | 10 | 35 | 20 | 80 | 54 |
| M3 | 10 | 55 | 20 | 80 | 57 |
| M4 | 10 | 0 | 60 | 60 | 67 |
| M5 | 10 | 0 | 60 | 60 | 63 |
| M6 | 10 | 0 | 60 | 60 | 63 |

## Source Artifacts

| artifact_id | label | path | exists | rows | columns | first_columns |
| --- | --- | --- | --- | --- | --- | --- |
| deep_fit | M1/M2 primary fit summary | results/m1_m2_utterance_information_deep_dive/model_fit_summary.csv | True | 10 | 14 | model_id, model_label, effort_col, effort_label, formula, n_obs, n_children, r2 |
| deep_coef | M1/M2 primary coefficient table | results/m1_m2_utterance_information_deep_dive/model_coefficients.csv | True | 20 | 13 | model_id, model_label, effort_col, effort_label, term, term_label, original_col, coef |
| expanded | M1-M3 estimator-family sensitivity summary | results/m1_m2_utterance_information_deep_dive/expanded_model_family_summary.csv | True | 110 | 24 | approach_id, model_family_id, model_family_label, effort_col, effort_label, readable_formula, fit_type, effect_scale |
| m4_context | M4 context-entropy sensitivity summary | results/m1_m2_utterance_information_deep_dive/m4_context_entropy_model_summary.csv | True | 25 | 24 | model_id, model_label, question, formula, fit_type, effort_col, effort_label, outcome |
| m5_m6_saturated | M5/M6 effort-level exploratory summary | results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_model_summary.csv | True | 10 | 17 | model_id, model_label, question, formula, fit_type, effect_scale, effort_col, effort_label |
| dual | M1-M6 continuous and effort-level model summary | results/m1_m6_dual_effort_quick_share/dual_model_summary.csv | True | 60 | 39 | model_id, model_title, question, effort_strategy, effort_col, effort_label, formula, readable_formula |
| fixed_summary | M1-M6 fixed-effort continuous model summary | results/m1_m6_fixed_effort_slices/fixed_effort_model_summary.csv | True | 30 | 39 | model_id, model_title, question, effort_strategy, effort_col, effort_label, formula, readable_formula |
| fixed_predictions | M1-M6 fixed-effort prediction rows | results/m1_m6_fixed_effort_slices/fixed_effort_predictions.csv | True | 8.046e+04 | 22 | age_months, age_c, effort_value, effort_c, context_entropy_bits, context_entropy_c, predicted_sum_bits, pred_ci_low |
| atlas_fit | M1-M6 fixed-effort atlas fit summary | results/m1_m6_fixed_effort_atlas/atlas_model_fit_summary.csv | True | 6 | 8 | model_id, mean_r2_observed_fitted, min_r2_observed_fitted, max_r2_observed_fitted, significant_age_slopes_p_lt_05, negative_age_slopes, positive_age_slopes, effort_units_tested |
| atlas_slopes | M1-M6 fixed-effort atlas slice slopes | results/m1_m6_fixed_effort_atlas/atlas_fixed_slice_slopes.csv | True | 402 | 9 | model_id, model_title, effort_col, effort_label, atlas_bin, fixed_effort_value, slope_bits_per_month, slope_bits_per_6_months |
| atlas_manifest | M1-M6 fixed-effort atlas figure manifest | results/m1_m6_fixed_effort_atlas/atlas_figure_manifest.csv | True | 30 | 4 | model_id, effort_col, effort_label, figure |
| context_m1_m6 | Context-window M1-M6 model summary | results/context_m1_m6_fixed_effort_atlas/context_m1_m6_model_summary.csv | True | 240 | 43 | context_k, model_id, model_family, model_label, context_variant, question, effort_col, effort_label |
| context_m1_m6_slopes | Context-window M1-M6 fixed-slice slopes | results/context_m1_m6_fixed_effort_atlas/context_m1_m6_slice_slopes.csv | True | 2340 | 11 | context_k, model_id, model_family, model_label, context_variant, effort_col, effort_label, atlas_bin |
| context_m1_m6_manifest | Context-window M1-M6 figure manifest | results/context_m1_m6_fixed_effort_atlas/context_m1_m6_figure_manifest.csv | True | 195 | 8 | context_k, model_id, model_family, model_label, context_variant, effort_col, effort_label, figure |
| context_fixed | Context-predictor adjunct model summary | results/context_fixed_effort_atlas/context_fixed_effort_model_summary.csv | True | 80 | 26 | context_k, model_id, model_label, question, effort_col, effort_label, context_size_col, context_size_label |
| context_fixed_manifest | Context-predictor adjunct figure manifest | results/context_fixed_effort_atlas/context_fixed_effort_figure_manifest.csv | True | 65 | 6 | context_k, model_id, model_label, effort_col, effort_label, figure |
| robustness | Age-bin bootstrap and scrambling summary | results/age_scrambling_robustness/age_scrambling_robustness_summary.csv | True | 420 | 21 | context_k, model_id, effort_col, effort_label, model_title, question, readable_formula, robustness_method |
| robustness_figures | Age-bin robustness figure manifest | results/age_scrambling_robustness/age_scrambling_figure_manifest.csv | True | 10 | 3 | figure_id, path, description |
| robustness_clear_figures | Clear robustness figure manifest | results/age_scrambling_robustness/age_scrambling_clear_figure_manifest.csv | True | 6 | 4 | figure_id, path, model_id, description |

## Model Ladder

| model | title | readable formula | primary scientific role |
| --- | --- | --- | --- |
| M1 | Pooled age and effort | sum_bits ~ age + effort | M1 is a baseline and a warning light. It shows the age-effort association before accounting for stable differences between children or corpora. |
| M2 | Age and effort with child identity | sum_bits ~ age + effort + C(child_id) | M2 is the cleanest first candidate for the supervisor-facing result: it asks whether same-child developmental change predicts total bits at fixed effort. |
| M3 | Age by effort | sum_bits ~ age * effort + C(child_id) | M3 tells us whether a single age slope hides different trajectories for short versus long utterances. |
| M4 | Context predictor added | sum_bits ~ age + effort + context predictor + C(child_id) | M4 asks whether the developmental result survives a control for how predictable the next-token context is. |
| M5 | Age by context predictor | sum_bits ~ age * context predictor + effort + C(child_id) | M5 is about developmental context sensitivity: whether older children show a different relation between context predictability and produced information. |
| M6 | Interaction-rich stress test | sum_bits ~ age * effort + age * context + effort * context + C(child_id) | M6 is a robustness stress test: it asks whether the simpler M2-M5 stories collapse under richer interactions. |

## Estimator And Library Guide

| label | library/object | what it is | where used | dependence handling |
| --- | --- | --- | --- | --- |
| OLS | `statsmodels.formula.api.ols` | ordinary linear regression on additive total bits | M1 baseline; primary M1-M6 atlas fits after adding child fixed effects where specified | none unless cluster covariance or `C(child_id)` is added |
| OLS + child-clustered SE | `fit(cov_type='cluster', cov_kwds={'groups': child_id})` | same OLS fitted line with standard errors adjusted for repeated utterances within child | primary dual-effort, fixed-effort, context atlas, and many deep-dive rows | affects uncertainty/p-values, not fitted means |
| Child fixed intercepts | `C(child_id)` in statsmodels formulas | one intercept per child | primary M2-M6 formulas | controls stable child baselines; it is not a random effect |
| Child fixed age slopes | `age_c:C(child_id)` | one linear age slope adjustment per child | M2/M3 sensitivity checks | diagnostic for child-specific developmental slopes |
| Gaussian GLM | `statsmodels.formula.api.glm(..., family=Gaussian())` | GLM version of the additive-bit linear model | M1-M3 sensitivity rows | no child dependence unless formula includes child terms |
| Gamma GLM, log link | `statsmodels.formula.api.glm(..., family=Gamma(link=Log()))` | positive-outcome sensitivity model; coefficients are on log expected bits | M1-M3 and M4 sensitivity rows | no child dependence unless formula includes child terms |
| GEE Gaussian/Gamma | `statsmodels.formula.api.gee(..., groups='child_id')` | population-average model clustered by child | M2/M3 and M4 sensitivity rows | models within-child correlation through GEE clustering |
| MixedLM random child intercept/slope | `statsmodels` mixed linear model | linear mixed model with random child intercept and sometimes random age slope | M2/M3 sensitivity rows only | random effects; several rows are singular/warning-prone, so use as diagnostics |

## Cross-Atlas Overview Plots

The following plots were built for this report from saved outputs. They are a quick way to see the shape of the result before entering the exhaustive model sections.

![M1-M6 continuous-effort models: age coefficients](../figs/m1_m6_super_atlas/dual_continuous_age_coefficients.png)
*M1-M6 continuous-effort models: age coefficients*

![M1-M6 effort-level models: age coefficients](../figs/m1_m6_super_atlas/dual_effort_level_age_coefficients.png)
*M1-M6 effort-level models: age coefficients*

![M1-M6 continuous-effort R2 heatmap.](../figs/m1_m6_super_atlas/dual_continuous_r2.png)
*M1-M6 continuous-effort R2 heatmap.*

![M1-M3 estimator-family age coefficient scatterplot.](../figs/m1_m6_super_atlas/estimator_variant_age_coefficients.png)
*M1-M3 estimator-family age coefficient scatterplot.*

![Context-window age coefficient heatmap.](../figs/m1_m6_super_atlas/context_m1_m6_age_coefficients.png)
*Context-window age coefficient heatmap.*

![Context-window R2 heatmap.](../figs/m1_m6_super_atlas/context_m1_m6_r2.png)
*Context-window R2 heatmap.*

![Signed significance counts for context-predictor terms.](../figs/m1_m6_super_atlas/context_predictor_significance_counts.png)
*Signed significance counts for context-predictor terms.*

![Share of fixed-effort slices with negative age slopes.](../figs/m1_m6_super_atlas/fixed_slice_negative_share.png)
*Share of fixed-effort slices with negative age slopes.*

![Context fixed-slice negative slope share.](../figs/m1_m6_super_atlas/context_fixed_slice_negative_share.png)
*Context fixed-slice negative slope share.*

![Robustness outside-null summary heatmap.](../figs/m1_m6_super_atlas/robustness_outside_null_summary.png)
*Robustness outside-null summary heatmap.*

![Figure counts by source atlas.](../figs/m1_m6_super_atlas/figure_inventory_by_source.png)
*Figure counts by source atlas.*


## How To Use This Report

Read M2 first if the goal is the supervisor-facing narrative. Then use M3 to ask whether effort-specific slopes matter, M4 to ask whether context predictability changes the interpretation, M5 to ask whether context sensitivity changes with age, and M6 as the saturation/stress-test layer.

Figure coverage by source is: context_adjunct=65, context_m1_m6=195, deep_dive=64, dual_effort=6, fixed_atlas=32, fixed_slices=30, m2_simple=5, robustness=16. PNG files are embedded; PDF duplicates are not.


## M1: Pooled age and effort

**Scientific question.** Pooling children, does age predict utterance total information after controlling utterance effort?

**Readable formula.** `sum_bits ~ age + effort`

**Exact implementation note.** Main OLS code uses centered `age_c` and `effort_c`; the centered form has the same slope interpretation.

**Estimator/library.** Ordinary least squares via `statsmodels.formula.api.ols` is the baseline. Sensitivity rows also include Gaussian GLM, Gamma GLM with log link, and child-clustered OLS standard errors.

**Fixed/random effects.** No child fixed effects and no random effects in the primary M1. Child clustering changes uncertainty only.

**Scientific meaning.** M1 is a baseline and a warning light. It shows the age-effort association before accounting for stable differences between children or corpora.

**Main caveat.** Do not use M1 alone as the developmental claim: pooled child coverage can make age look like child/corpus composition.

**Computed take-away across saved artifacts.** continuous-effort age signs: 0 negative, 5 positive across 5 effort units; fixed-effort slices: 0% negative age slopes; context-window atlas age signs: 7 negative, 13 positive across 20 rows; robustness outside-null share: 81%.


### Dual Effort Summary

This table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  | fit |
| effort_level | Words | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.4211 | 0.1334 | 0.005 |  |  |  |  |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.3898 | 0.1672 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.452 | 0.134 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.4269 | 0.1638 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.4502 | 0.1537 | <.001 |  |  |  |  |  |  |  |  | fit |

### Estimator Sensitivity Rows

These are the non-simple-OLS variants from the deep-dive packet. Use them to check whether the age conclusion depends on estimator family, child clustering, child fixed effects, GEE clustering, Gamma/log scaling, or mixed/random-effect structure.

| model_family_label | fit_type | effect_scale | effort_label | readable_formula | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -8.55e+09 | -6.64e-04 | <.001 | 0.1845 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -8.849e+10 | 0.001138 | <.001 | 0.07251 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -2.041e+07 | 7.07e-04 | <.001 | 0.1794 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -3.665e+06 | 0.001311 | <.001 | 0.166 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -1.706e+07 | -7.77e-04 | <.001 | 0.2143 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.5978 | 0.009018 | <.001 | 5.446 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.632 | 0.0681 | <.001 | 2.07 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6345 | 0.05143 | <.001 | 5.212 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6177 | 0.06904 | <.001 | 4.822 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.873 | 6.354 | <.001 |  |  |
| OLS | ols | additive bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.5978 | 0.009018 | <.001 | 5.446 | <.001 |  |  |
| OLS | ols | additive bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.632 | 0.0681 | <.001 | 2.07 | <.001 |  |  |
| OLS | ols | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6345 | 0.05143 | <.001 | 5.212 | <.001 |  |  |
| OLS | ols | additive bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6177 | 0.06904 | <.001 | 4.822 | <.001 |  |  |
| OLS | ols | additive bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.873 | 6.354 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |

### Context-Window M1-M6 Atlas Rows

These rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7122 | -0.06145 | 0.005 | 6.17 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7522 | 0.005929 | 0.707 | 2.343 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7414 | -0.008835 | 0.569 | 5.841 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.725 | 0.009849 | 0.508 | 5.418 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7189 | -0.06724 | 0.005 | 7.138 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6268 | -0.02637 | 0.382 | 5.731 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6649 | 0.03523 | 0.161 | 2.182 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6644 | 0.01867 | 0.449 | 5.479 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6482 | 0.03667 | 0.153 | 5.076 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6395 | -0.03427 | 0.294 | 6.668 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6074 | -0.003091 | 0.921 | 5.537 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6426 | 0.05686 | 0.032 | 2.105 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6445 | 0.04012 | 0.126 | 5.298 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6279 | 0.05785 | 0.032 | 4.903 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6218 | -0.01155 | 0.727 | 6.455 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  |  |  |  |  |

### Age-Bin Bootstrap And Scrambling Robustness

Rows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | age_bin_group_scramble | 5 | 2 | 2 | 0.544 | 0.129 |
| k0 | balanced_bootstrap | 5 | 2 | 3 | 0.756 |  |
| k0 | unit_age_scramble | 5 | 2 | 5 | 0.526 | 0.010 |
| k0 | within_child_age_scramble | 5 | 2 | 5 | 0.6 | 1.000 |
| k1 | age_bin_group_scramble | 5 | 0 | 4 | 0.502 | 0.010 |
| k1 | balanced_bootstrap | 5 | 0 | 4 | 0.818 |  |
| k1 | unit_age_scramble | 5 | 0 | 5 | 0.518 | 0.010 |
| k1 | within_child_age_scramble | 5 | 0 | 2 | 1 | 0.762 |
| k2 | age_bin_group_scramble | 5 | 0 | 5 | 0.486 | 0.010 |
| k2 | balanced_bootstrap | 5 | 0 | 5 | 0.924 |  |
| k2 | unit_age_scramble | 5 | 0 | 5 | 0.508 | 0.010 |
| k2 | within_child_age_scramble | 5 | 0 | 2 | 1 | 0.099 |
| k3 | age_bin_group_scramble | 5 | 0 | 5 | 0.514 | 0.010 |
| k3 | balanced_bootstrap | 5 | 0 | 4 | 0.966 |  |
| k3 | unit_age_scramble | 5 | 0 | 5 | 0.526 | 0.010 |
| k3 | within_child_age_scramble | 5 | 0 | 4 | 1 | 0.020 |

### All Plots For M1

#### M1-M6 context-window fixed-effort atlas plots

![k0_m1_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_morphemes_fixed_effort_atlas.png)
*k0_m1_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_m1_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_phonemes_fixed_effort_atlas.png)
*k0_m1_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_m1_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_m1_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_m1_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_words_fixed_effort_atlas.png)
*k0_m1_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_m1_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_morphemes_fixed_effort_atlas.png)
*k1_m1_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m1_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_phonemes_fixed_effort_atlas.png)
*k1_m1_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m1_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m1_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m1_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_words_fixed_effort_atlas.png)
*k1_m1_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m1_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_morphemes_fixed_effort_atlas.png)
*k2_m1_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m1_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_phonemes_fixed_effort_atlas.png)
*k2_m1_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m1_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m1_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m1_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_words_fixed_effort_atlas.png)
*k2_m1_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m1_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_morphemes_fixed_effort_atlas.png)
*k3_m1_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m1_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_phonemes_fixed_effort_atlas.png)
*k3_m1_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m1_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m1_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m1_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_words_fixed_effort_atlas.png)
*k3_m1_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m1_coefficients_by_effort_version.png](../figs/m1_m2_utterance_information_deep_dive/m1_coefficients_by_effort_version.png)
*m1_coefficients_by_effort_version.png*

![m1_expanded_age_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m1_expanded_age_coefficients.png)
*m1_expanded_age_coefficients.png*

![m1_expanded_r2.png](../figs/m1_m2_utterance_information_deep_dive/m1_expanded_r2.png)
*m1_expanded_r2.png*

![m1_glm_gamma_log_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_glm_gamma_log_adjusted_age_lines.png)
*m1_glm_gamma_log_adjusted_age_lines.png*

![m1_glm_gaussian_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_glm_gaussian_adjusted_age_lines.png)
*m1_glm_gaussian_adjusted_age_lines.png*

![m1_low_mid_high_effort_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m1_low_mid_high_effort_adjusted_age_predictions.png)
*m1_low_mid_high_effort_adjusted_age_predictions.png*

![m1_m2_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)
*m1_m2_adjusted_age_predictions.png*

![m1_m2_age_coefficients_by_effort.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_age_coefficients_by_effort.png)
*m1_m2_age_coefficients_by_effort.png*

![m1_m2_delta_r2_variable_importance.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png)
*m1_m2_delta_r2_variable_importance.png*

![m1_m2_effort_coefficients_by_measure.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_effort_coefficients_by_measure.png)
*m1_m2_effort_coefficients_by_measure.png*

![m1_m2_residual_diagnostics_words.png / Words](../figs/m1_m2_utterance_information_deep_dive/m1_m2_residual_diagnostics_words.png)
*m1_m2_residual_diagnostics_words.png; Words*

![m1_ols_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_ols_adjusted_age_lines.png)
*m1_ols_adjusted_age_lines.png*

![m1_ols_cluster_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png)
*m1_ols_cluster_adjusted_age_lines.png*

#### M1-M6 continuous versus effort-level plots

![m1_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m1_dual_effort_predictions.png)
*m1_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m1_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m1_nb_morphemes_atlas_bins.png)
*m1_nb_morphemes_atlas_bins.png; Morphemes*

![m1_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m1_nb_phonemes_atlas_bins.png)
*m1_nb_phonemes_atlas_bins.png; Phonemes*

![m1_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m1_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m1_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_pkg_atlas_bins.png)
*m1_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m1_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m1_nb_words_atlas_bins.png)
*m1_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m1_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_granular_primary_fixed_effort_slices.png)
*m1_granular_primary_fixed_effort_slices.png*

![m1_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m1_marginal_adjusted_global_trends.png)
*m1_marginal_adjusted_global_trends.png*

![m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m1_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_top_frequency_12_fixed_effort_slices.png)
*m1_top_frequency_12_fixed_effort_slices.png*

![m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m1_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m1_age_slope_robustness_intervals.png)
*m1_age_slope_robustness_intervals.png*

![m1_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png)
*m1_clear_robustness_regression_lines.png*


## M2: Age and effort with child identity

**Scientific question.** Does the age effect remain after controlling utterance effort and each child's baseline?

**Readable formula.** `sum_bits ~ age + effort + C(child_id)`

**Exact implementation note.** Most M2 atlas rows use centered `age_c`, centered effort, and `C(child_id)` fixed intercepts.

**Estimator/library.** Primary M2 is ordinary least squares with child fixed intercepts and child-cluster robust standard errors in statsmodels.

**Fixed/random effects.** `C(child_id)` is a fixed effect, not a random effect. Sensitivity checks additionally tried GEE and MixedLM random child intercept/slope variants.

**Scientific meaning.** M2 is the cleanest first candidate for the supervisor-facing result: it asks whether same-child developmental change predicts total bits at fixed effort.

**Main caveat.** The shared age slope is still linear and averaged over children. Child-specific slope variants are diagnostics, not the primary simple story.

**Computed take-away across saved artifacts.** continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 100% negative age slopes; context-window atlas age signs: 20 negative, 0 positive across 20 rows; robustness outside-null share: 76%.


### Dual Effort Summary

This table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  | fit |
| effort_level | Words | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4353 | 0.08168 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4064 | 0.117 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4631 | 0.07177 | 0.005 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4398 | 0.1069 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4622 | 0.08531 | <.001 |  |  |  |  |  |  |  |  | fit |

### Estimator Sensitivity Rows

These are the non-simple-OLS variants from the deep-dive packet. Use them to check whether the age conclusion depends on estimator family, child clustering, child fixed effects, GEE clustering, Gamma/log scaling, or mixed/random-effect structure.

| model_family_label | fit_type | effect_scale | effort_label | readable_formula | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Morphemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -9.764e+09 | -0.006172 | <.001 | 0.1858 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Phonemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -1.09e+11 | -0.004326 | <.001 | 0.07309 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -2.117e+07 | -0.003852 | <.001 | 0.1801 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -3.49e+06 | -0.003385 | 0.003 | 0.1662 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Words | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -1.475e+07 | -0.005415 | <.001 | 0.2138 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -9.437e+09 | -0.005968 | <.001 | 0.1858 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -9.773e+10 | -0.004147 | <.001 | 0.07297 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -1.964e+07 | -0.003677 | <.001 | 0.1799 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -3.211e+06 | -0.003214 | <.001 | 0.1662 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Words | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -1.484e+07 | -0.005295 | <.001 | 0.2142 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Morphemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.5923 | -0.1354 | <.001 | 5.489 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Phonemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.6273 | -0.06478 | 0.011 | 2.084 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.631 | -0.06318 | 0.015 | 5.236 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Syllables: pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.6139 | -0.04838 | 0.044 | 4.831 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Words | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.6087 | -0.1224 | <.001 | 6.367 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Morphemes | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.1958 | <.001 | 5.508 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Phonemes | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6456 | -0.1064 | 0.003 | 2.087 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6474 | -0.1149 | 0.003 | 5.245 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6308 | -0.08571 | 0.131 | 4.837 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Words | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.1852 | <.001 | 6.386 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Morphemes | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.07 | -0.1355 | <.001 | 5.489 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Phonemes | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.035 | -0.06486 | <.001 | 2.084 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.032 | -0.06326 | <.001 | 5.236 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.049 | -0.04846 | <.001 | 4.831 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Words | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.054 | -0.1225 | <.001 | 6.367 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Morphemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Phonemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Words | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Morphemes | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.196 | <.001 | 5.508 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Phonemes | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6456 | -0.0861 | <.001 | 2.087 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6474 | -0.09669 | <.001 | 5.245 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6308 | -0.08275 | <.001 | 4.837 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Words | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.1525 | <.001 | 6.386 | <.001 |  |  |

### Context-Window M1-M6 Atlas Rows

These rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7204 | -0.1784 | <.001 | 6.195 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7578 | -0.09847 | 0.001 | 2.352 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7461 | -0.0907 | 0.003 | 5.848 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7303 | -0.07571 | 0.009 | 5.411 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7252 | -0.1582 | <.001 | 7.127 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.639 | -0.1585 | <.001 | 5.772 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6743 | -0.08519 | <.001 | 2.196 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6729 | -0.08207 | <.001 | 5.502 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6572 | -0.06724 | 0.001 | 5.084 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6495 | -0.1431 | <.001 | 6.677 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6217 | -0.1425 | <.001 | 5.581 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6542 | -0.07096 | 0.005 | 2.12 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6551 | -0.06903 | 0.007 | 5.323 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.639 | -0.0542 | 0.021 | 4.914 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6338 | -0.1287 | <.001 | 6.468 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  |  |  |  |  |

### Age-Bin Bootstrap And Scrambling Robustness

Rows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | age_bin_group_scramble | 5 | 5 | 5 | 0.472 | 0.010 |
| k0 | balanced_bootstrap | 5 | 5 | 1 | 1 |  |
| k0 | unit_age_scramble | 5 | 5 | 5 | 0.554 | 0.010 |
| k0 | within_child_age_scramble | 5 | 5 | 5 | 0.502 | 0.010 |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.494 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 0 | 0.998 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.484 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.504 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.492 | 0.010 |
| k2 | balanced_bootstrap | 5 | 5 | 0 | 0.996 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.494 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.516 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 5 | 0.5 | 0.010 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.99 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.52 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.514 | 0.010 |

### All Plots For M2

#### M1-M6 context-window fixed-effort atlas plots

![k0_m2_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_morphemes_fixed_effort_atlas.png)
*k0_m2_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_m2_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_phonemes_fixed_effort_atlas.png)
*k0_m2_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_m2_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_m2_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_m2_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_words_fixed_effort_atlas.png)
*k0_m2_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_m2_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_morphemes_fixed_effort_atlas.png)
*k1_m2_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m2_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_phonemes_fixed_effort_atlas.png)
*k1_m2_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m2_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m2_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m2_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_words_fixed_effort_atlas.png)
*k1_m2_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m2_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_morphemes_fixed_effort_atlas.png)
*k2_m2_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m2_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_phonemes_fixed_effort_atlas.png)
*k2_m2_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m2_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m2_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m2_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_words_fixed_effort_atlas.png)
*k2_m2_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m2_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_morphemes_fixed_effort_atlas.png)
*k3_m2_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m2_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_phonemes_fixed_effort_atlas.png)
*k3_m2_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m2_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m2_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m2_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_words_fixed_effort_atlas.png)
*k3_m2_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m1_m2_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)
*m1_m2_adjusted_age_predictions.png*

![m1_m2_age_coefficients_by_effort.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_age_coefficients_by_effort.png)
*m1_m2_age_coefficients_by_effort.png*

![m1_m2_delta_r2_variable_importance.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png)
*m1_m2_delta_r2_variable_importance.png*

![m1_m2_effort_coefficients_by_measure.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_effort_coefficients_by_measure.png)
*m1_m2_effort_coefficients_by_measure.png*

![m1_m2_residual_diagnostics_words.png / Words](../figs/m1_m2_utterance_information_deep_dive/m1_m2_residual_diagnostics_words.png)
*m1_m2_residual_diagnostics_words.png; Words*

![m2_coefficients_by_effort_version.png](../figs/m1_m2_utterance_information_deep_dive/m2_coefficients_by_effort_version.png)
*m2_coefficients_by_effort_version.png*

![m2_expanded_age_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m2_expanded_age_coefficients.png)
*m2_expanded_age_coefficients.png*

![m2_expanded_r2.png](../figs/m1_m2_utterance_information_deep_dive/m2_expanded_r2.png)
*m2_expanded_r2.png*

![m2_gee_gamma_log_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_gee_gamma_log_adjusted_age_lines.png)
*m2_gee_gamma_log_adjusted_age_lines.png*

![m2_gee_gaussian_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_gee_gaussian_adjusted_age_lines.png)
*m2_gee_gaussian_adjusted_age_lines.png*

![m2_glm_gamma_log_child_fe_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_glm_gamma_log_child_fe_adjusted_age_lines.png)
*m2_glm_gamma_log_child_fe_adjusted_age_lines.png*

![m2_low_mid_high_effort_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m2_low_mid_high_effort_adjusted_age_predictions.png)
*m2_low_mid_high_effort_adjusted_age_predictions.png*

![m2_mixed_random_age_slope_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_age_slope_adjusted_age_lines.png)
*m2_mixed_random_age_slope_adjusted_age_lines.png*

![m2_mixed_random_intercept_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_intercept_adjusted_age_lines.png)
*m2_mixed_random_intercept_adjusted_age_lines.png*

![m2_ols_child_fe_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png)
*m2_ols_child_fe_adjusted_age_lines.png*

![m2_ols_child_fe_age_slope_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_age_slope_adjusted_age_lines.png)
*m2_ols_child_fe_age_slope_adjusted_age_lines.png*

#### M1-M6 continuous versus effort-level plots

![m2_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m2_dual_effort_predictions.png)
*m2_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m2_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m2_nb_morphemes_atlas_bins.png)
*m2_nb_morphemes_atlas_bins.png; Morphemes*

![m2_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m2_nb_phonemes_atlas_bins.png)
*m2_nb_phonemes_atlas_bins.png; Phonemes*

![m2_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m2_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m2_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_pkg_atlas_bins.png)
*m2_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m2_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m2_nb_words_atlas_bins.png)
*m2_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m2_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_granular_primary_fixed_effort_slices.png)
*m2_granular_primary_fixed_effort_slices.png*

![m2_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m2_marginal_adjusted_global_trends.png)
*m2_marginal_adjusted_global_trends.png*

![m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m2_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_top_frequency_12_fixed_effort_slices.png)
*m2_top_frequency_12_fixed_effort_slices.png*

![m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Supervisor-facing Model 2 simple plots

![m2_morphemes_fixed_effort_and_global_trend.png / Morphemes](../figs/m2_simple_plots/m2_morphemes_fixed_effort_and_global_trend.png)
*m2_morphemes_fixed_effort_and_global_trend.png; Morphemes*

![m2_phonemes_fixed_effort_and_global_trend.png / Phonemes](../figs/m2_simple_plots/m2_phonemes_fixed_effort_and_global_trend.png)
*m2_phonemes_fixed_effort_and_global_trend.png; Phonemes*

![m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png / Syllables: CMU/pkg](../figs/m2_simple_plots/m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png)
*m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png; Syllables: CMU/pkg*

![m2_syllables_pkg_fixed_effort_and_global_trend.png / Syllables: pkg](../figs/m2_simple_plots/m2_syllables_pkg_fixed_effort_and_global_trend.png)
*m2_syllables_pkg_fixed_effort_and_global_trend.png; Syllables: pkg*

![m2_words_fixed_effort_and_global_trend.png / Words](../figs/m2_simple_plots/m2_words_fixed_effort_and_global_trend.png)
*m2_words_fixed_effort_and_global_trend.png; Words*

#### Age-bin bootstrap and scrambling robustness plots

![m2_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m2_age_slope_robustness_intervals.png)
*m2_age_slope_robustness_intervals.png*

![m2_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)
*m2_clear_robustness_regression_lines.png*


## M3: Age by effort

**Scientific question.** Does the developmental age effect depend on utterance effort?

**Readable formula.** `sum_bits ~ age * effort + C(child_id)`

**Exact implementation note.** Continuous-effort M3 uses centered `age_c * effort_c`; effort-level M3 uses `age_c * C(effort_level)`.

**Estimator/library.** Primary M3 atlas rows are OLS with child fixed intercepts and child-cluster robust standard errors. Deep-dive sensitivity rows include OLS, GLM, GEE, and MixedLM variants.

**Fixed/random effects.** Primary M3 uses child fixed intercepts. MixedLM variants with random intercepts/slopes are sensitivity checks and can be singular.

**Scientific meaning.** M3 tells us whether a single age slope hides different trajectories for short versus long utterances.

**Main caveat.** Interaction coefficients are harder to interpret than fixed-effort slices. Prefer the fixed-slice plots when explaining M3.

**Computed take-away across saved artifacts.** continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 94% negative age slopes; context-window atlas age signs: 20 negative, 0 positive across 20 rows; robustness outside-null share: 80%.


### Dual Effort Summary

This table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  | -0.003787 | 0.515 |  |  | fit |
| continuous | Morphemes | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  | 0.00228 | 0.727 |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  | 0.00703 | 0.252 |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  | 0.009859 | 0.022 |  |  | fit |
| continuous | Phonemes | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  | 0.002729 | 0.220 |  |  | fit |
| effort_level | Words | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4401 | -0.0722 | 0.033 |  |  |  |  |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4122 | -0.0701 | 0.064 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4688 | -0.06415 | 0.033 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4466 | -0.05571 | 0.073 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4676 | -0.07701 | 0.009 |  |  |  |  |  |  |  |  | fit |

### Estimator Sensitivity Rows

These are the non-simple-OLS variants from the deep-dive packet. Use them to check whether the age conclusion depends on estimator family, child clustering, child fixed effects, GEE clustering, Gamma/log scaling, or mixed/random-effect structure.

| model_family_label | fit_type | effect_scale | effort_label | readable_formula | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Morphemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -3.732e+09 | -0.005665 | <.001 | 0.1911 | <.001 | -0.001651 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Phonemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -3.432e+10 | -0.003763 | <.001 | 0.07498 | <.001 | -6.51e-04 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -9.342e+06 | -0.003282 | <.001 | 0.1846 | <.001 | -0.001583 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -2.174e+06 | -0.00289 | 0.001 | 0.1698 | <.001 | -0.001324 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Words | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -6.274e+06 | -0.004872 | <.001 | 0.2206 | <.001 | -0.002085 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -3.583e+09 | -1.16e-04 | 0.138 | 0.188 | <.001 | -0.001265 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -2.867e+10 | 0.001765 | <.001 | 0.07379 | <.001 | -5.49e-04 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -9.405e+06 | 0.00132 | <.001 | 0.1825 | <.001 | -0.001299 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -2.279e+06 | 0.001832 | <.001 | 0.1684 | <.001 | -0.001072 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -7.589e+06 | -1.48e-04 | 0.055 | 0.219 | <.001 | -0.001715 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -3.05e+09 | -0.005556 | <.001 | 0.1902 | <.001 | -0.001637 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -2.596e+10 | -0.003664 | <.001 | 0.0745 | <.001 | -6.47e-04 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -7.775e+06 | -0.00319 | <.001 | 0.1837 | <.001 | -0.001555 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -1.805e+06 | -0.002794 | <.001 | 0.1691 | <.001 | -0.001311 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Words | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -5.518e+06 | -0.004859 | <.001 | 0.22 | <.001 | -0.002082 | <.001 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Morphemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.5924 | -0.1361 | <.001 | 5.482 | <.001 | 0.002283 | 0.720 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Phonemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6276 | -0.06714 | 0.014 | 2.077 | <.001 | 0.00273 | 0.209 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6313 | -0.06578 | 0.014 | 5.217 | <.001 | 0.007032 | 0.240 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Syllables: pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6143 | -0.05206 | 0.050 | 4.806 | <.001 | 0.009861 | 0.019 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Words | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6086 | -0.1215 | <.001 | 6.379 | <.001 | -0.003783 | 0.505 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.598 | 0.004168 | 0.037 | 5.416 | <.001 | 0.0103 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6322 | 0.06241 | <.001 | 2.059 | <.001 | 0.004518 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6348 | 0.04521 | <.001 | 5.181 | <.001 | 0.01174 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6181 | 0.06146 | <.001 | 4.787 | <.001 | 0.01407 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.613 | -0.001242 | 0.526 | 6.342 | <.001 | 0.003893 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Morphemes | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.1928 | <.001 | 5.497 | <.001 | 0.003414 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Phonemes | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6457 | -0.1004 | 0.005 | 2.079 | <.001 | 0.003128 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6475 | -0.109 | 0.063 | 5.223 | <.001 | 0.00797 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6311 | -0.07614 | 0.032 | 4.806 | <.001 | 0.01145 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Words | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.189 | <.001 | 6.402 | <.001 | -0.005014 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Morphemes | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | 0.6131 | -0.136 | <.001 | 5.482 | <.001 | 0.002287 | 0.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Phonemes | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.029 | -0.06723 | <.001 | 2.077 | <.001 | 0.002729 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.025 | -0.06586 | <.001 | 5.217 | <.001 | 0.00703 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.038 | -0.05214 | <.001 | 4.806 | <.001 | 0.009859 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Words | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | 0.6259 | -0.1214 | <.001 | 6.379 | <.001 | -0.003779 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.598 | 0.004168 | 0.037 | 5.416 | <.001 | 0.0103 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6322 | 0.06241 | <.001 | 2.059 | <.001 | 0.004518 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6348 | 0.04521 | <.001 | 5.181 | <.001 | 0.01174 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6181 | 0.06146 | <.001 | 4.787 | <.001 | 0.01407 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.613 | -0.001242 | 0.526 | 6.342 | <.001 | 0.003893 | <.001 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Morphemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 | 0.00228 | 0.727 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Phonemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 | 0.002729 | 0.220 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 | 0.00703 | 0.252 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 | 0.009859 | 0.022 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Words | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 | -0.003787 | 0.515 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Morphemes | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.2023 | <.001 | 5.498 | <.001 | 0.003415 | 0.628 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Phonemes | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6457 | -0.1008 | <.001 | 2.079 | <.001 | 0.003132 | 0.216 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6475 | -0.1119 | <.001 | 5.223 | <.001 | 0.007986 | 0.239 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6311 | -0.1053 | <.001 | 4.806 | <.001 | 0.01146 | 0.015 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Words | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.1448 | <.001 | 6.402 | <.001 | -0.005015 | 0.460 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.598 | 0.004168 | 0.891 | 5.416 | <.001 | 0.0103 | 0.034 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6322 | 0.06241 | 0.014 | 2.059 | <.001 | 0.004518 | 0.008 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6348 | 0.04521 | 0.070 | 5.181 | <.001 | 0.01174 | 0.023 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6181 | 0.06146 | 0.017 | 4.787 | <.001 | 0.01407 | <.001 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.613 | -0.001242 | 0.970 | 6.342 | <.001 | 0.003893 | 0.422 |

### Context-Window M1-M6 Atlas Rows

These rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7211 | -0.1727 | <.001 | 6.256 | <.001 |  |  |  |  | -0.02036 | 0.010 |  |  |  |  |
| k0 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7581 | -0.094 | 0.002 | 2.366 | <.001 |  |  |  |  | -0.005153 | 0.071 |  |  |  |  |
| k0 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7463 | -0.08636 | 0.002 | 5.88 | <.001 |  |  |  |  | -0.01175 | 0.110 |  |  |  |  |
| k0 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7305 | -0.07272 | 0.009 | 5.431 | <.001 |  |  |  |  | -0.007984 | 0.121 |  |  |  |  |
| k0 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7263 | -0.1515 | <.001 | 7.217 | <.001 |  |  |  |  | -0.02929 | <.001 |  |  |  |  |
| k1 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.639 | -0.1576 | <.001 | 5.782 | <.001 |  |  |  |  | -0.003203 | 0.612 |  |  |  |  |
| k1 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6743 | -0.08562 | <.001 | 2.195 | <.001 |  |  |  |  | 4.94e-04 | 0.820 |  |  |  |  |
| k1 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6729 | -0.0827 | <.001 | 5.498 | <.001 |  |  |  |  | 0.001689 | 0.768 |  |  |  |  |
| k1 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6573 | -0.069 | 0.002 | 5.071 | <.001 |  |  |  |  | 0.004698 | 0.233 |  |  |  |  |
| k1 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6497 | -0.1408 | <.001 | 6.709 | <.001 |  |  |  |  | -0.01004 | 0.079 |  |  |  |  |
| k2 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6217 | -0.1427 | <.001 | 5.579 | <.001 |  |  |  |  | 6.28e-04 | 0.922 |  |  |  |  |
| k2 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6542 | -0.07275 | 0.007 | 2.115 | <.001 |  |  |  |  | 0.00207 | 0.347 |  |  |  |  |
| k2 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6552 | -0.07101 | 0.007 | 5.309 | <.001 |  |  |  |  | 0.005351 | 0.370 |  |  |  |  |
| k2 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6391 | -0.05728 | 0.026 | 4.893 | <.001 |  |  |  |  | 0.00822 | 0.048 |  |  |  |  |
| k2 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6339 | -0.1274 | <.001 | 6.486 | <.001 |  |  |  |  | -0.005741 | 0.318 |  |  |  |  |
| k3 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  |  |  | 0.00228 | 0.727 |  |  |  |  |
| k3 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  |  |  | 0.002729 | 0.220 |  |  |  |  |
| k3 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  |  |  | 0.00703 | 0.252 |  |  |  |  |
| k3 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  |  |  | 0.009859 | 0.022 |  |  |  |  |
| k3 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  |  |  | -0.003787 | 0.515 |  |  |  |  |

### Age-Bin Bootstrap And Scrambling Robustness

Rows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | age_bin_group_scramble | 5 | 5 | 5 | 0.51 | 0.010 |
| k0 | balanced_bootstrap | 5 | 5 | 3 | 1 |  |
| k0 | unit_age_scramble | 5 | 5 | 5 | 0.496 | 0.010 |
| k0 | within_child_age_scramble | 5 | 5 | 5 | 0.318 | 0.010 |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.528 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 0 | 0.998 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.492 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.498 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.524 | 0.020 |
| k2 | balanced_bootstrap | 5 | 5 | 1 | 0.998 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.49 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.494 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 5 | 0.524 | 0.010 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.994 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.46 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.51 | 0.010 |

### All Plots For M3

#### M1-M6 context-window fixed-effort atlas plots

![k0_m3_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_morphemes_fixed_effort_atlas.png)
*k0_m3_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_m3_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_phonemes_fixed_effort_atlas.png)
*k0_m3_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_m3_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_m3_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_m3_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_words_fixed_effort_atlas.png)
*k0_m3_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_m3_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_morphemes_fixed_effort_atlas.png)
*k1_m3_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m3_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_phonemes_fixed_effort_atlas.png)
*k1_m3_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m3_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m3_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m3_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_words_fixed_effort_atlas.png)
*k1_m3_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m3_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_morphemes_fixed_effort_atlas.png)
*k2_m3_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m3_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_phonemes_fixed_effort_atlas.png)
*k2_m3_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m3_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m3_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m3_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_words_fixed_effort_atlas.png)
*k2_m3_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m3_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_morphemes_fixed_effort_atlas.png)
*k3_m3_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m3_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_phonemes_fixed_effort_atlas.png)
*k3_m3_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m3_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m3_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m3_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_words_fixed_effort_atlas.png)
*k3_m3_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m3_expanded_interaction_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png)
*m3_expanded_interaction_coefficients.png*

![m3_expanded_r2.png](../figs/m1_m2_utterance_information_deep_dive/m3_expanded_r2.png)
*m3_expanded_r2.png*

![m3_gee_gamma_log_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_adjusted_age_lines.png)
*m3_gee_gamma_log_interaction_adjusted_age_lines.png*

![m3_gee_gamma_log_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_interaction_age_lines.png)
*m3_gee_gamma_log_interaction_interaction_age_lines.png*

![m3_gee_gaussian_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_adjusted_age_lines.png)
*m3_gee_gaussian_interaction_adjusted_age_lines.png*

![m3_gee_gaussian_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_interaction_age_lines.png)
*m3_gee_gaussian_interaction_interaction_age_lines.png*

![m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png)
*m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png*

![m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png)
*m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png*

![m3_glm_gamma_log_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_adjusted_age_lines.png)
*m3_glm_gamma_log_interaction_adjusted_age_lines.png*

![m3_glm_gamma_log_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_interaction_age_lines.png)
*m3_glm_gamma_log_interaction_interaction_age_lines.png*

![m3_glm_gaussian_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_adjusted_age_lines.png)
*m3_glm_gaussian_interaction_adjusted_age_lines.png*

![m3_glm_gaussian_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_interaction_age_lines.png)
*m3_glm_gaussian_interaction_interaction_age_lines.png*

![m3_mixed_random_age_slope_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_adjusted_age_lines.png)
*m3_mixed_random_age_slope_interaction_adjusted_age_lines.png*

![m3_mixed_random_age_slope_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_interaction_age_lines.png)
*m3_mixed_random_age_slope_interaction_interaction_age_lines.png*

![m3_mixed_random_intercept_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_adjusted_age_lines.png)
*m3_mixed_random_intercept_interaction_adjusted_age_lines.png*

![m3_mixed_random_intercept_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_interaction_age_lines.png)
*m3_mixed_random_intercept_interaction_interaction_age_lines.png*

![m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png)
*m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png*

![m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png)
*m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png*

![m3_ols_child_fe_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png)
*m3_ols_child_fe_interaction_adjusted_age_lines.png*

![m3_ols_child_fe_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)
*m3_ols_child_fe_interaction_interaction_age_lines.png*

![m3_ols_cluster_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_adjusted_age_lines.png)
*m3_ols_cluster_interaction_adjusted_age_lines.png*

![m3_ols_cluster_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png)
*m3_ols_cluster_interaction_interaction_age_lines.png*

![m3_ols_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_adjusted_age_lines.png)
*m3_ols_interaction_adjusted_age_lines.png*

![m3_ols_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_interaction_age_lines.png)
*m3_ols_interaction_interaction_age_lines.png*

#### M1-M6 continuous versus effort-level plots

![m3_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m3_dual_effort_predictions.png)
*m3_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m3_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m3_nb_morphemes_atlas_bins.png)
*m3_nb_morphemes_atlas_bins.png; Morphemes*

![m3_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m3_nb_phonemes_atlas_bins.png)
*m3_nb_phonemes_atlas_bins.png; Phonemes*

![m3_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m3_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m3_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_pkg_atlas_bins.png)
*m3_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m3_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m3_nb_words_atlas_bins.png)
*m3_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m3_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_granular_primary_fixed_effort_slices.png)
*m3_granular_primary_fixed_effort_slices.png*

![m3_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m3_marginal_adjusted_global_trends.png)
*m3_marginal_adjusted_global_trends.png*

![m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m3_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_top_frequency_12_fixed_effort_slices.png)
*m3_top_frequency_12_fixed_effort_slices.png*

![m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m3_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m3_age_slope_robustness_intervals.png)
*m3_age_slope_robustness_intervals.png*

![m3_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png)
*m3_clear_robustness_regression_lines.png*


## M4: Context predictor added

**Scientific question.** Does context entropy, matched context size, or both explain total information beyond age, target effort, and child identity?

**Readable formula.** `sum_bits ~ age + effort + context predictor + C(child_id)`

**Exact implementation note.** Context atlas variants are M4E, M4S, and M4ES for entropy, context size, and entropy plus size.

**Estimator/library.** The context M1-M6 atlas uses ordinary least squares via `statsmodels.formula.api.ols` with child-cluster robust standard errors.

**Fixed/random effects.** Child identity is represented as fixed intercepts in primary M4. The earlier M4 deep dive also includes Gaussian and Gamma GEE sensitivity models clustered by child.

**Scientific meaning.** M4 asks whether the developmental result survives a control for how predictable the next-token context is.

**Main caveat.** The context feature here is next-token context entropy from the scored feature pipeline, not full response-level entropy.

**Computed take-away across saved artifacts.** continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 100% negative age slopes; context-window atlas age signs: 45 negative, 0 positive across 45 rows; robustness outside-null share: 80%.


### Dual Effort Summary

This table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  | fit |
| effort_level | Words | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4363 | 0.0829 | <.001 |  |  | -0.4785 | <.001 |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4072 | 0.1197 | <.001 |  |  | -0.5201 | <.001 |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4639 | 0.07374 | 0.005 |  |  | -0.5254 | <.001 |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4407 | 0.1106 | <.001 |  |  | -0.5295 | <.001 |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4633 | 0.08804 | <.001 |  |  | -0.5842 | <.001 |  |  |  |  | fit |

### M4 Context-Entropy Deep-Dive Rows

These rows include OLS/clustered, GEE, and Gamma/log variants for the context-entropy addition.

| model_id | model_label | fit_type | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | entropy_coef | entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4a | M4a: child FE + context entropy | ols_cluster | Words | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | -0.4716 | <.001 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Words | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6098 | -0.1268 | <.001 | -0.4715 | <.001 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Words | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -1.784e+07 | -0.005747 | <.001 | -0.01973 | <.001 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Words | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | -0.4704 | <.001 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Words | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1264 | <.001 | -0.4715 | <.001 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Morphemes | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | -0.5123 | <.001 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Morphemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.5932 | -0.14 | <.001 | -0.5122 | <.001 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Morphemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -1.232e+10 | -0.006534 | <.001 | -0.02081 | <.001 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Morphemes | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | -0.5113 | <.001 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Morphemes | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1409 | <.001 | -0.5123 | <.001 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | -0.5398 | <.001 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Syllables: CMU/pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6322 | -0.06438 | 0.011 | -0.5398 | <.001 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Syllables: CMU/pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -2.542e+07 | -0.004073 | <.001 | -0.0216 | <.001 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | -0.5391 | <.001 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6469 | -0.06733 | 0.015 | -0.5399 | <.001 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Syllables: pkg | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | -0.541 | <.001 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Syllables: pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6149 | -0.04795 | 0.034 | -0.541 | <.001 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Syllables: pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -4.219e+06 | -0.003548 | 0.002 | -0.0215 | <.001 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | -0.5403 | <.001 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6307 | -0.0519 | 0.050 | -0.541 | <.001 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Phonemes | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | -0.5814 | <.001 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Phonemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6287 | -0.06508 | 0.011 | -0.5814 | <.001 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Phonemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -1.394e+11 | -0.004539 | <.001 | -0.02295 | <.001 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Phonemes | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | -0.5805 | <.001 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Phonemes | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6454 | -0.06773 | 0.018 | -0.5812 | <.001 | fit |

### Context-Window M1-M6 Atlas Rows

These rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6388 | -0.1636 | <.001 | 5.773 | <.001 | 0.06736 | 0.206 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6743 | -0.08687 | <.001 | 2.196 | <.001 | 0.02783 | 0.548 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6728 | -0.08435 | <.001 | 5.502 | <.001 | 0.06356 | 0.204 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6571 | -0.06823 | <.001 | 5.083 | <.001 | 0.04786 | 0.346 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6495 | -0.1481 | <.001 | 6.68 | <.001 | 0.05917 | 0.274 |  |  |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6397 | -0.1576 | <.001 | 5.772 | <.001 | -0.0464 | 0.357 | -0.1462 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6751 | -0.08125 | <.001 | 2.195 | <.001 | -0.06489 | 0.143 | -0.04865 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6737 | -0.07842 | <.001 | 5.501 | <.001 | -0.03417 | 0.477 | -0.1285 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.658 | -0.06222 | 0.002 | 5.081 | <.001 | -0.05367 | 0.281 | -0.1244 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6506 | -0.1414 | <.001 | 6.679 | <.001 | -0.06001 | 0.247 | -0.1813 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6403 | -0.1562 | <.001 | 5.767 | <.001 |  |  | -0.1421 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6755 | -0.08311 | <.001 | 2.194 | <.001 |  |  | -0.04665 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6741 | -0.07966 | <.001 | 5.497 | <.001 |  |  | -0.1263 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6585 | -0.06479 | 0.002 | 5.078 | <.001 |  |  | -0.1208 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.651 | -0.1402 | <.001 | 6.671 | <.001 |  |  | -0.175 | <.001 |  |  |  |  |  |  |
| k2 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.622 | -0.1458 | <.001 | 5.582 | <.001 | -0.4256 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6549 | -0.06995 | 0.006 | 2.12 | <.001 | -0.4942 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6557 | -0.06891 | 0.006 | 5.324 | <.001 | -0.4558 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6396 | -0.05248 | 0.017 | 4.913 | <.001 | -0.4543 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6343 | -0.1318 | <.001 | 6.47 | <.001 | -0.4107 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6223 | -0.142 | <.001 | 5.582 | <.001 | -0.4253 | <.001 | -0.05438 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6551 | -0.0665 | 0.008 | 2.12 | <.001 | -0.4898 | <.001 | -0.01751 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.656 | -0.06519 | 0.009 | 5.324 | <.001 | -0.4521 | <.001 | -0.04709 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6399 | -0.04875 | 0.027 | 4.913 | <.001 | -0.4506 | <.001 | -0.04487 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6347 | -0.1273 | <.001 | 6.47 | <.001 | -0.4087 | <.001 | -0.06994 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6227 | -0.1433 | <.001 | 5.577 | <.001 |  |  | -0.05554 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6552 | -0.0717 | 0.005 | 2.118 | <.001 |  |  | -0.01841 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6561 | -0.06963 | 0.007 | 5.319 | <.001 |  |  | -0.04898 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.64 | -0.05479 | 0.021 | 4.909 | <.001 |  |  | -0.04671 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.635 | -0.1289 | <.001 | 6.464 | <.001 |  |  | -0.07164 | <.001 |  |  |  |  |  |  |
| k3 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6138 | -0.1369 | <.001 | 5.489 | <.001 | -0.5111 | <.001 | -0.03298 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6455 | -0.06221 | 0.016 | 2.084 | <.001 | -0.577 | <.001 | -0.0106 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6469 | -0.06126 | 0.018 | 5.235 | <.001 | -0.5362 | <.001 | -0.02838 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6306 | -0.04483 | 0.052 | 4.829 | <.001 | -0.537 | <.001 | -0.02722 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6268 | -0.123 | <.001 | 6.368 | <.001 | -0.4699 | <.001 | -0.0427 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6142 | -0.1375 | <.001 | 5.485 | <.001 |  |  | -0.03407 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6455 | -0.06667 | 0.013 | 2.082 | <.001 |  |  | -0.01139 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6471 | -0.06497 | 0.016 | 5.232 | <.001 |  |  | -0.02985 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6308 | -0.05014 | 0.044 | 4.827 | <.001 |  |  | -0.0288 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6272 | -0.1239 | <.001 | 6.363 | <.001 |  |  | -0.04386 | <.001 |  |  |  |  |  |  |

### Age-Bin Bootstrap And Scrambling Robustness

Rows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.552 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 3 | 1 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.498 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.516 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.48 | 0.010 |
| k2 | balanced_bootstrap | 5 | 5 | 1 | 0.998 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.542 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.51 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 4 | 0.53 | 0.040 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.944 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.49 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.468 | 0.010 |

### All Plots For M4

#### M1-M6 context-window fixed-effort atlas plots

![k1_m4e_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_morphemes_fixed_effort_atlas.png)
*k1_m4e_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m4e_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_phonemes_fixed_effort_atlas.png)
*k1_m4e_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m4e_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_words_fixed_effort_atlas.png)
*k1_m4e_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m4es_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_morphemes_fixed_effort_atlas.png)
*k1_m4es_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m4es_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_phonemes_fixed_effort_atlas.png)
*k1_m4es_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m4es_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_words_fixed_effort_atlas.png)
*k1_m4es_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m4s_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_morphemes_fixed_effort_atlas.png)
*k1_m4s_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m4s_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_phonemes_fixed_effort_atlas.png)
*k1_m4s_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m4s_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_words_fixed_effort_atlas.png)
*k1_m4s_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m4e_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_morphemes_fixed_effort_atlas.png)
*k2_m4e_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m4e_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_phonemes_fixed_effort_atlas.png)
*k2_m4e_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m4e_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_words_fixed_effort_atlas.png)
*k2_m4e_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m4es_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_morphemes_fixed_effort_atlas.png)
*k2_m4es_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m4es_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_phonemes_fixed_effort_atlas.png)
*k2_m4es_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m4es_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_words_fixed_effort_atlas.png)
*k2_m4es_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m4s_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_morphemes_fixed_effort_atlas.png)
*k2_m4s_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m4s_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_phonemes_fixed_effort_atlas.png)
*k2_m4s_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m4s_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_words_fixed_effort_atlas.png)
*k2_m4s_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m4e_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_morphemes_fixed_effort_atlas.png)
*k3_m4e_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m4e_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_phonemes_fixed_effort_atlas.png)
*k3_m4e_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m4e_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_words_fixed_effort_atlas.png)
*k3_m4e_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m4es_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_morphemes_fixed_effort_atlas.png)
*k3_m4es_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m4es_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_phonemes_fixed_effort_atlas.png)
*k3_m4es_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m4es_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_words_fixed_effort_atlas.png)
*k3_m4es_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m4s_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_morphemes_fixed_effort_atlas.png)
*k3_m4s_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m4s_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_phonemes_fixed_effort_atlas.png)
*k3_m4s_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m4s_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_words_fixed_effort_atlas.png)
*k3_m4s_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m4_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png)
*m4_context_entropy_adjusted_predictions.png*

![m4_context_entropy_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_coefficients.png)
*m4_context_entropy_coefficients.png*

![m4_context_entropy_descriptive_bins.png](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png)
*m4_context_entropy_descriptive_bins.png*

![m4_effort_quantile_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_effort_quantile_adjusted_predictions.png)
*m4_effort_quantile_adjusted_predictions.png*

![m4_m4a_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4a_context_entropy_adjusted_predictions.png)
*m4_m4a_context_entropy_adjusted_predictions.png*

![m4_m4b_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4b_context_entropy_adjusted_predictions.png)
*m4_m4b_context_entropy_adjusted_predictions.png*

![m4_m4c_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4c_context_entropy_adjusted_predictions.png)
*m4_m4c_context_entropy_adjusted_predictions.png*

![m4_m4d_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4d_context_entropy_adjusted_predictions.png)
*m4_m4d_context_entropy_adjusted_predictions.png*

![m4_m4e_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4e_context_entropy_adjusted_predictions.png)
*m4_m4e_context_entropy_adjusted_predictions.png*

#### M1-M6 continuous versus effort-level plots

![m4_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m4_dual_effort_predictions.png)
*m4_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m4_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m4_nb_morphemes_atlas_bins.png)
*m4_nb_morphemes_atlas_bins.png; Morphemes*

![m4_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m4_nb_phonemes_atlas_bins.png)
*m4_nb_phonemes_atlas_bins.png; Phonemes*

![m4_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m4_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m4_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_pkg_atlas_bins.png)
*m4_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m4_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m4_nb_words_atlas_bins.png)
*m4_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m4_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_granular_primary_fixed_effort_slices.png)
*m4_granular_primary_fixed_effort_slices.png*

![m4_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m4_marginal_adjusted_global_trends.png)
*m4_marginal_adjusted_global_trends.png*

![m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m4_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_top_frequency_12_fixed_effort_slices.png)
*m4_top_frequency_12_fixed_effort_slices.png*

![m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m4_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m4_age_slope_robustness_intervals.png)
*m4_age_slope_robustness_intervals.png*

![m4_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m4_clear_robustness_regression_lines.png)
*m4_clear_robustness_regression_lines.png*


## M5: Age by context predictor

**Scientific question.** Does the context-predictor association itself change with age?

**Readable formula.** `sum_bits ~ age * context predictor + effort + C(child_id)`

**Exact implementation note.** Context atlas variants are M5E, M5S, and M5ES for age by entropy, age by context size, and both interactions.

**Estimator/library.** Primary atlas rows are OLS with child fixed intercepts and child-cluster robust standard errors.

**Fixed/random effects.** No random effects in the primary M5 atlas. Child baselines are fixed intercepts.

**Scientific meaning.** M5 is about developmental context sensitivity: whether older children show a different relation between context predictability and produced information.

**Main caveat.** Treat M5 as explanatory/exploratory unless the interaction is stable across context windows and effort measures.

**Computed take-away across saved artifacts.** continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 100% negative age slopes; context-window atlas age signs: 45 negative, 0 positive across 45 rows; robustness outside-null share: 72%.


### Dual Effort Summary

This table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  | 0.006141 | 0.284 | fit |
| continuous | Morphemes | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  | 0.004709 | 0.339 | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  | 0.003955 | 0.478 | fit |
| continuous | Syllables: pkg | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  | 0.003946 | 0.481 | fit |
| continuous | Phonemes | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  | 0.00465 | 0.407 | fit |
| effort_level | Words | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4364 | 0.08125 | <.001 |  |  | -0.4758 | <.001 |  |  | 0.01401 | 0.047 | fit |
| effort_level | Morphemes | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4073 | 0.1181 | <.001 |  |  | -0.5173 | <.001 |  |  | 0.01404 | 0.032 | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.464 | 0.07276 | 0.006 |  |  | -0.5237 | <.001 |  |  | 0.008394 | 0.244 | fit |
| effort_level | Syllables: pkg | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4407 | 0.1096 | <.001 |  |  | -0.5279 | <.001 |  |  | 0.008078 | 0.237 | fit |
| effort_level | Phonemes | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4633 | 0.08694 | <.001 |  |  | -0.5823 | <.001 |  |  | 0.009479 | 0.207 | fit |

### Effort-Level Context Exploratory Rows

These are the earlier M5/M6 low/mid/high effort-level context models. They are useful but less clean than the fixed-effort atlas when explaining effort-specific trajectories.

| model_id | model_label | fit_type | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Words | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4363 | 0.0829 | <.001 | -0.4785 | <.001 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Morphemes | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4072 | 0.1197 | <.001 | -0.5201 | <.001 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4639 | 0.07374 | 0.005 | -0.5254 | <.001 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4407 | 0.1106 | <.001 | -0.5295 | <.001 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Phonemes | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4633 | 0.08804 | <.001 | -0.5842 | <.001 | fit |

### Context-Window M1-M6 Atlas Rows

These rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6389 | -0.1647 | <.001 | 5.772 | <.001 | 0.07772 | 0.230 |  |  |  |  | 0.01791 | 0.005 |  |  |
| k1 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6744 | -0.08788 | <.001 | 2.196 | <.001 | 0.03693 | 0.502 |  |  |  |  | 0.01573 | 0.002 |  |  |
| k1 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6729 | -0.08541 | <.001 | 5.502 | <.001 | 0.07299 | 0.219 |  |  |  |  | 0.0163 | 0.002 |  |  |
| k1 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6572 | -0.06928 | <.001 | 5.082 | <.001 | 0.05728 | 0.331 |  |  |  |  | 0.01629 | <.001 |  |  |
| k1 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6496 | -0.1491 | <.001 | 6.68 | <.001 | 0.06788 | 0.288 |  |  |  |  | 0.01505 | 0.018 |  |  |
| k1 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6399 | -0.1584 | <.001 | 5.772 | <.001 | -0.03454 | 0.558 | -0.1459 | <.001 |  |  | 0.0173 | <.001 | -0.002025 | 0.247 |
| k1 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6752 | -0.0821 | <.001 | 2.195 | <.001 | -0.05507 | 0.273 | -0.04867 | <.001 |  |  | 0.01587 | <.001 | -3.34e-04 | 0.624 |
| k1 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6738 | -0.07929 | <.001 | 5.501 | <.001 | -0.0241 | 0.661 | -0.1286 | <.001 |  |  | 0.0164 | <.001 | -8.26e-04 | 0.669 |
| k1 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6581 | -0.0631 | 0.001 | 5.081 | <.001 | -0.04358 | 0.428 | -0.1245 | <.001 |  |  | 0.01639 | <.001 | -8.06e-04 | 0.648 |
| k1 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6507 | -0.1421 | <.001 | 6.679 | <.001 | -0.05053 | 0.396 | -0.1811 | <.001 |  |  | 0.01498 | 0.003 | -0.001203 | 0.624 |
| k1 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6403 | -0.1553 | <.001 | 5.766 | <.001 |  |  | -0.1408 | <.001 |  |  |  |  | -0.002978 | 0.156 |
| k1 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6755 | -0.08255 | <.001 | 2.193 | <.001 |  |  | -0.04623 | <.001 |  |  |  |  | -6.97e-04 | 0.338 |
| k1 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6741 | -0.07905 | <.001 | 5.496 | <.001 |  |  | -0.1253 | <.001 |  |  |  |  | -0.001844 | 0.347 |
| k1 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6585 | -0.06415 | 0.003 | 5.077 | <.001 |  |  | -0.1198 | <.001 |  |  |  |  | -0.001897 | 0.269 |
| k1 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.651 | -0.1396 | <.001 | 6.671 | <.001 |  |  | -0.174 | <.001 |  |  |  |  | -0.002223 | 0.401 |
| k2 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.622 | -0.1469 | <.001 | 5.582 | <.001 | -0.423 | <.001 |  |  |  |  | 0.01127 | <.001 |  |  |
| k2 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6549 | -0.07082 | 0.005 | 2.121 | <.001 | -0.492 | <.001 |  |  |  |  | 0.009362 | 0.002 |  |  |
| k2 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6557 | -0.06976 | 0.005 | 5.324 | <.001 | -0.4537 | <.001 |  |  |  |  | 0.009102 | 0.003 |  |  |
| k2 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6396 | -0.0533 | 0.016 | 4.913 | <.001 | -0.4522 | <.001 |  |  |  |  | 0.008871 | 0.003 |  |  |
| k2 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6343 | -0.1327 | <.001 | 6.47 | <.001 | -0.4085 | <.001 |  |  |  |  | 0.009403 | <.001 |  |  |
| k2 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6224 | -0.1411 | <.001 | 5.581 | <.001 | -0.4216 | <.001 | -0.05295 | <.001 |  |  | 0.01227 | <.001 | -0.004267 | 0.009 |
| k2 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6552 | -0.06565 | 0.009 | 2.12 | <.001 | -0.4861 | <.001 | -0.01697 | <.001 |  |  | 0.01074 | <.001 | -0.001234 | 0.009 |
| k2 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6561 | -0.06422 | 0.010 | 5.323 | <.001 | -0.4485 | <.001 | -0.04591 | <.001 |  |  | 0.01044 | <.001 | -0.003029 | 0.014 |
| k2 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.64 | -0.04782 | 0.031 | 4.912 | <.001 | -0.447 | <.001 | -0.04373 | <.001 |  |  | 0.0102 | <.001 | -0.002896 | 0.015 |
| k2 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6348 | -0.1263 | <.001 | 6.47 | <.001 | -0.405 | <.001 | -0.0683 | <.001 |  |  | 0.01073 | <.001 | -0.004204 | 0.019 |
| k2 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6228 | -0.1409 | <.001 | 5.576 | <.001 |  |  | -0.0541 | <.001 |  |  |  |  | -0.00417 | 0.010 |
| k2 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6552 | -0.06955 | 0.007 | 2.118 | <.001 |  |  | -0.01782 | <.001 |  |  |  |  | -0.001223 | 0.009 |
| k2 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6562 | -0.06748 | 0.009 | 5.318 | <.001 |  |  | -0.0477 | <.001 |  |  |  |  | -0.003028 | 0.011 |
| k2 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6401 | -0.05265 | 0.025 | 4.909 | <.001 |  |  | -0.04546 | <.001 |  |  |  |  | -0.002931 | 0.011 |
| k2 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6351 | -0.1266 | <.001 | 6.463 | <.001 |  |  | -0.0699 | <.001 |  |  |  |  | -0.004125 | 0.017 |
| k3 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  |  |  | 0.004709 | 0.339 |  |  |
| k3 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  |  |  | 0.00465 | 0.407 |  |  |
| k3 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  |  |  | 0.003955 | 0.478 |  |  |
| k3 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  |  |  | 0.003946 | 0.481 |  |  |
| k3 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  |  |  | 0.006141 | 0.284 |  |  |
| k3 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.614 | -0.1347 | <.001 | 5.488 | <.001 | -0.51 | <.001 | -0.0319 | <.001 |  |  | 0.005694 | 0.244 | -0.003641 | 0.006 |
| k3 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6456 | -0.06036 | 0.024 | 2.084 | <.001 | -0.5753 | <.001 | -0.01013 | <.001 |  |  | 0.006003 | 0.281 | -0.001034 | 0.005 |
| k3 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.647 | -0.05921 | 0.026 | 5.234 | <.001 | -0.5345 | <.001 | -0.02733 | <.001 |  |  | 0.005245 | 0.346 | -0.002541 | 0.007 |
| k3 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6307 | -0.04287 | 0.071 | 4.828 | <.001 | -0.5354 | <.001 | -0.02626 | <.001 |  |  | 0.005242 | 0.343 | -0.002424 | 0.006 |
| k3 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6269 | -0.121 | <.001 | 6.367 | <.001 | -0.4679 | <.001 | -0.04139 | <.001 |  |  | 0.00728 | 0.202 | -0.003595 | 0.010 |
| k3 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6144 | -0.1345 | <.001 | 5.484 | <.001 |  |  | -0.03311 | <.001 |  |  |  |  | -0.003561 | 0.006 |
| k3 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6457 | -0.06397 | 0.017 | 2.082 | <.001 |  |  | -0.01094 | <.001 |  |  |  |  | -0.001031 | 0.006 |
| k3 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6472 | -0.06226 | 0.022 | 5.231 | <.001 |  |  | -0.02888 | <.001 |  |  |  |  | -0.00253 | 0.006 |
| k3 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6309 | -0.04746 | 0.056 | 4.826 | <.001 |  |  | -0.02789 | <.001 |  |  |  |  | -0.002428 | 0.006 |
| k3 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6274 | -0.121 | <.001 | 6.362 | <.001 |  |  | -0.04263 | <.001 |  |  |  |  | -0.003511 | 0.009 |

### Age-Bin Bootstrap And Scrambling Robustness

Rows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.528 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 1 | 1 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.496 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.518 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 3 | 0.536 | 0.040 |
| k2 | balanced_bootstrap | 5 | 5 | 1 | 1 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.51 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.424 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 3 | 0.488 | 0.059 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.908 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.486 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.326 | 0.020 |

### All Plots For M5

#### M1-M6 context-window fixed-effort atlas plots

![k1_m5e_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_morphemes_fixed_effort_atlas.png)
*k1_m5e_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m5e_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_phonemes_fixed_effort_atlas.png)
*k1_m5e_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m5e_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_words_fixed_effort_atlas.png)
*k1_m5e_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m5es_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_morphemes_fixed_effort_atlas.png)
*k1_m5es_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m5es_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_phonemes_fixed_effort_atlas.png)
*k1_m5es_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m5es_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_words_fixed_effort_atlas.png)
*k1_m5es_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m5s_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_morphemes_fixed_effort_atlas.png)
*k1_m5s_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m5s_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_phonemes_fixed_effort_atlas.png)
*k1_m5s_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m5s_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_words_fixed_effort_atlas.png)
*k1_m5s_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m5e_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_morphemes_fixed_effort_atlas.png)
*k2_m5e_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m5e_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_phonemes_fixed_effort_atlas.png)
*k2_m5e_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m5e_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_words_fixed_effort_atlas.png)
*k2_m5e_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m5es_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_morphemes_fixed_effort_atlas.png)
*k2_m5es_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m5es_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_phonemes_fixed_effort_atlas.png)
*k2_m5es_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m5es_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_words_fixed_effort_atlas.png)
*k2_m5es_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m5s_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_morphemes_fixed_effort_atlas.png)
*k2_m5s_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m5s_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_phonemes_fixed_effort_atlas.png)
*k2_m5s_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m5s_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_words_fixed_effort_atlas.png)
*k2_m5s_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m5e_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_morphemes_fixed_effort_atlas.png)
*k3_m5e_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m5e_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_phonemes_fixed_effort_atlas.png)
*k3_m5e_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m5e_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_words_fixed_effort_atlas.png)
*k3_m5e_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m5es_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_morphemes_fixed_effort_atlas.png)
*k3_m5es_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m5es_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_phonemes_fixed_effort_atlas.png)
*k3_m5es_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m5es_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_words_fixed_effort_atlas.png)
*k3_m5es_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m5s_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_morphemes_fixed_effort_atlas.png)
*k3_m5s_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m5s_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_phonemes_fixed_effort_atlas.png)
*k3_m5s_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m5s_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_words_fixed_effort_atlas.png)
*k3_m5s_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m5_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png)
*m5_effort_level_adjusted_age_predictions.png*

![m5_m6_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_adjusted_age_predictions.png)
*m5_m6_effort_level_adjusted_age_predictions.png*

![m5_m6_effort_level_average_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png)
*m5_m6_effort_level_average_age_predictions.png*

![m5_m6_saturated_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png)
*m5_m6_saturated_adjusted_age_predictions.png*

![m5_m6_saturated_selected_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png)
*m5_m6_saturated_selected_coefficients.png*

#### M1-M6 continuous versus effort-level plots

![m5_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m5_dual_effort_predictions.png)
*m5_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m5_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m5_nb_morphemes_atlas_bins.png)
*m5_nb_morphemes_atlas_bins.png; Morphemes*

![m5_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m5_nb_phonemes_atlas_bins.png)
*m5_nb_phonemes_atlas_bins.png; Phonemes*

![m5_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m5_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m5_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_pkg_atlas_bins.png)
*m5_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m5_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m5_nb_words_atlas_bins.png)
*m5_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m5_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_granular_primary_fixed_effort_slices.png)
*m5_granular_primary_fixed_effort_slices.png*

![m5_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m5_marginal_adjusted_global_trends.png)
*m5_marginal_adjusted_global_trends.png*

![m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m5_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_top_frequency_12_fixed_effort_slices.png)
*m5_top_frequency_12_fixed_effort_slices.png*

![m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m5_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m5_age_slope_robustness_intervals.png)
*m5_age_slope_robustness_intervals.png*

![m5_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m5_clear_robustness_regression_lines.png)
*m5_clear_robustness_regression_lines.png*


## M6: Interaction-rich stress test

**Scientific question.** Do age, target effort, and context predictors interact when predicting total information?

**Readable formula.** `sum_bits ~ age * effort + age * context + effort * context + C(child_id)`

**Exact implementation note.** Context atlas variants are M6E, M6S, and M6ES; the most saturated ES version also includes entropy by context-size interaction.

**Estimator/library.** Primary atlas rows are OLS with child fixed intercepts and child-cluster robust standard errors.

**Fixed/random effects.** No random effects in the primary M6 atlas. Mixed/random-effect evidence belongs to the M1-M3 sensitivity family only.

**Scientific meaning.** M6 is a robustness stress test: it asks whether the simpler M2-M5 stories collapse under richer interactions.

**Main caveat.** This model is easiest to overinterpret. Multicollinearity and interaction saturation mean plots and sign stability matter more than any single coefficient.

**Computed take-away across saved artifacts.** continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 90% negative age slopes; context-window atlas age signs: 45 negative, 0 positive across 45 rows; robustness outside-null share: 75%.


### Dual Effort Summary

This table contains the continuous-effort and low/mid/high effort-level versions from the M1-M6 quick-share analysis. They are ordinary least-squares fits with child-cluster robust standard errors; M2-M6 include child fixed intercepts where the formula says `C(child_id)`.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 | -0.002441 | 0.726 | 0.009085 | 0.111 | fit |
| continuous | Morphemes | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 | 0.003897 | 0.575 | 0.009103 | 0.070 | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 | 0.009024 | 0.154 | 0.00658 | 0.202 | fit |
| continuous | Syllables: pkg | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 | 0.01209 | 0.017 | 0.005176 | 0.277 | fit |
| continuous | Phonemes | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 | 0.003548 | 0.200 | 0.00833 | 0.086 | fit |
| effort_level | Words | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4413 | -0.0775 | 0.023 |  |  | -0.3592 | <.001 |  |  | 0.008538 | 0.072 | fit |
| effort_level | Morphemes | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4133 | -0.07519 | 0.050 |  |  | -0.3338 | <.001 |  |  | 0.008115 | 0.060 | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4699 | -0.06767 | 0.027 |  |  | -0.3802 | <.001 |  |  | 0.004033 | 0.442 | fit |
| effort_level | Syllables: pkg | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4478 | -0.05867 | 0.061 |  |  | -0.3742 | <.001 |  |  | 0.002937 | 0.532 | fit |
| effort_level | Phonemes | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.469 | -0.08116 | 0.007 |  |  | -0.3343 | <.001 |  |  | 0.003877 | 0.432 | fit |

### Effort-Level Context Exploratory Rows

These are the earlier M5/M6 low/mid/high effort-level context models. They are useful but less clean than the fixed-effort atlas when explaining effort-specific trajectories.

| model_id | model_label | fit_type | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Words | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4413 | -0.0775 | 0.023 | -0.3592 | <.001 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Morphemes | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4133 | -0.07519 | 0.050 | -0.3338 | <.001 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4699 | -0.06767 | 0.027 | -0.3802 | <.001 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4478 | -0.05867 | 0.061 | -0.3742 | <.001 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Phonemes | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.469 | -0.08116 | 0.007 | -0.3343 | <.001 | fit |

### Context-Window M1-M6 Atlas Rows

These rows cover k0/k1/k2/k3 where available. M4-M6 have entropy, matched context-size, and entropy-plus-size variants (`E`, `S`, `ES`). The estimator is ordinary least squares in statsmodels with child-cluster robust standard errors.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.639 | -0.1639 | <.001 | 5.773 | <.001 | 0.082 | 0.172 |  |  | -0.001998 | 0.775 | 0.01332 | 0.030 |  |  |
| k1 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6744 | -0.08865 | <.001 | 2.192 | <.001 | 0.0396 | 0.435 |  |  | 0.001076 | 0.696 | 0.01283 | 0.011 |  |  |
| k1 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6731 | -0.08642 | <.001 | 5.49 | <.001 | 0.07668 | 0.157 |  |  | 0.003309 | 0.583 | 0.01262 | 0.018 |  |  |
| k1 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6574 | -0.07135 | <.001 | 5.062 | <.001 | 0.06127 | 0.241 |  |  | 0.006345 | 0.187 | 0.01204 | 0.012 |  |  |
| k1 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6497 | -0.1471 | <.001 | 6.702 | <.001 | 0.07117 | 0.244 |  |  | -0.008804 | 0.213 | 0.01165 | 0.057 |  |  |
| k1 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6415 | -0.1619 | <.001 | 5.802 | <.001 | -0.0727 | 0.219 | -0.129 | <.001 | -0.002118 | 0.758 | 0.01743 | <.001 | 0.003243 | 0.142 |
| k1 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6769 | -0.08725 | <.001 | 2.203 | <.001 | -0.08079 | 0.109 | -0.04256 | <.001 | 0.001092 | 0.690 | 0.01652 | <.001 | 0.001271 | 0.160 |
| k1 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6755 | -0.08461 | <.001 | 5.517 | <.001 | -0.0493 | 0.374 | -0.1147 | <.001 | 0.003331 | 0.558 | 0.01641 | <.001 | 0.003345 | 0.212 |
| k1 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6598 | -0.06931 | 0.001 | 5.086 | <.001 | -0.07058 | 0.200 | -0.1106 | <.001 | 0.006357 | 0.169 | 0.01566 | <.001 | 0.002883 | 0.208 |
| k1 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6522 | -0.1444 | <.001 | 6.734 | <.001 | -0.07778 | 0.204 | -0.1649 | <.001 | -0.00876 | 0.215 | 0.01618 | 0.003 | 0.004946 | 0.105 |
| k1 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6418 | -0.159 | <.001 | 5.799 | <.001 |  |  | -0.1274 | <.001 | -0.002851 | 0.642 |  |  | 0.002052 | 0.403 |
| k1 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6771 | -0.08757 | <.001 | 2.201 | <.001 |  |  | -0.04115 | <.001 | 6.43e-04 | 0.773 |  |  | 8.18e-04 | 0.370 |
| k1 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6757 | -0.0842 | <.001 | 5.516 | <.001 |  |  | -0.1132 | <.001 | 0.002148 | 0.685 |  |  | 0.002167 | 0.406 |
| k1 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6601 | -0.0703 | 0.002 | 5.087 | <.001 |  |  | -0.1083 | <.001 | 0.005177 | 0.169 |  |  | 0.001678 | 0.433 |
| k1 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6525 | -0.1417 | <.001 | 6.729 | <.001 |  |  | -0.1604 | <.001 | -0.009531 | 0.103 |  |  | 0.00362 | 0.244 |
| k2 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.622 | -0.1475 | <.001 | 5.578 | <.001 | -0.4253 | <.001 |  |  | 0.001876 | 0.791 | 0.01352 | <.001 |  |  |
| k2 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.655 | -0.07308 | 0.008 | 2.114 | <.001 | -0.4947 | <.001 |  |  | 0.00278 | 0.328 | 0.01224 | <.001 |  |  |
| k2 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6559 | -0.0722 | 0.006 | 5.307 | <.001 | -0.4554 | <.001 |  |  | 0.007145 | 0.258 | 0.01096 | <.001 |  |  |
| k2 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6398 | -0.05665 | 0.024 | 4.889 | <.001 | -0.4527 | <.001 |  |  | 0.01025 | 0.045 | 0.009547 | 0.003 |  |  |
| k2 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6343 | -0.132 | <.001 | 6.486 | <.001 | -0.411 | <.001 |  |  | -0.00449 | 0.532 | 0.01205 | <.001 |  |  |
| k2 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6242 | -0.1475 | <.001 | 5.614 | <.001 | -0.4449 | <.001 | -0.04179 | <.001 | 0.002631 | 0.703 | 0.01435 | <.001 | -6.65e-04 | 0.666 |
| k2 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6572 | -0.07354 | 0.007 | 2.128 | <.001 | -0.5063 | <.001 | -0.01272 | <.001 | 0.00307 | 0.280 | 0.01308 | <.001 | -2.02e-04 | 0.674 |
| k2 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.658 | -0.07228 | 0.006 | 5.343 | <.001 | -0.4678 | <.001 | -0.03553 | <.001 | 0.007791 | 0.179 | 0.0118 | <.001 | -3.22e-04 | 0.821 |
| k2 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6417 | -0.05626 | 0.023 | 4.918 | <.001 | -0.4657 | <.001 | -0.03415 | <.001 | 0.01085 | 0.028 | 0.01046 | 0.002 | -6.31e-04 | 0.607 |
| k2 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6364 | -0.1312 | <.001 | 6.525 | <.001 | -0.4245 | <.001 | -0.05664 | <.001 | -0.00354 | 0.623 | 0.01304 | <.001 | -1.54e-05 | 0.993 |
| k2 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6246 | -0.1469 | <.001 | 5.611 | <.001 |  |  | -0.04444 | <.001 | 0.001426 | 0.811 |  |  | -6.48e-04 | 0.657 |
| k2 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6571 | -0.07708 | 0.005 | 2.127 | <.001 |  |  | -0.01405 | <.001 | 0.002379 | 0.274 |  |  | -2.12e-04 | 0.638 |
| k2 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6581 | -0.07513 | 0.004 | 5.341 | <.001 |  |  | -0.0386 | <.001 | 0.006098 | 0.244 |  |  | -3.74e-04 | 0.777 |
| k2 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6418 | -0.06081 | 0.018 | 4.918 | <.001 |  |  | -0.03724 | <.001 | 0.008955 | 0.018 |  |  | -7.19e-04 | 0.524 |
| k2 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6367 | -0.131 | <.001 | 6.522 | <.001 |  |  | -0.05973 | <.001 | -0.004747 | 0.403 |  |  | -1.65e-05 | 0.992 |
| k3 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 |  |  | 0.003897 | 0.575 | 0.009103 | 0.070 |  |  |
| k3 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 |  |  | 0.003548 | 0.200 | 0.00833 | 0.086 |  |  |
| k3 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 |  |  | 0.009024 | 0.154 | 0.00658 | 0.202 |  |  |
| k3 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 |  |  | 0.01209 | 0.017 | 0.005176 | 0.277 |  |  |
| k3 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 |  |  | -0.002441 | 0.726 | 0.009085 | 0.111 |  |  |
| k3 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6159 | -0.1426 | <.001 | 5.526 | <.001 | -0.541 | <.001 | -0.02502 | <.001 | 0.004933 | 0.457 | 0.01042 | 0.043 | -9.73e-04 | 0.384 |
| k3 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6476 | -0.06946 | 0.014 | 2.093 | <.001 | -0.6018 | <.001 | -0.007348 | 0.004 | 0.00395 | 0.151 | 0.009755 | 0.051 | -3.01e-04 | 0.398 |
| k3 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6489 | -0.06831 | 0.014 | 5.256 | <.001 | -0.5605 | <.001 | -0.02076 | 0.003 | 0.009957 | 0.081 | 0.008035 | 0.129 | -6.68e-04 | 0.524 |
| k3 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6325 | -0.05205 | 0.049 | 4.835 | <.001 | -0.5613 | <.001 | -0.02054 | <.001 | 0.0129 | 0.008 | 0.006645 | 0.174 | -9.17e-04 | 0.303 |
| k3 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6285 | -0.127 | <.001 | 6.425 | <.001 | -0.4939 | <.001 | -0.03458 | <.001 | -0.001189 | 0.864 | 0.01057 | 0.071 | -5.50e-04 | 0.679 |
| k3 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6162 | -0.1419 | <.001 | 5.523 | <.001 |  |  | -0.02546 | <.001 | 0.003169 | 0.589 |  |  | -9.64e-04 | 0.360 |
| k3 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6476 | -0.07269 | 0.010 | 2.092 | <.001 |  |  | -0.007942 | 0.002 | 0.003091 | 0.148 |  |  | -3.11e-04 | 0.366 |
| k3 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.649 | -0.07096 | 0.010 | 5.255 | <.001 |  |  | -0.02175 | 0.002 | 0.007908 | 0.133 |  |  | -6.95e-04 | 0.481 |
| k3 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6326 | -0.05648 | 0.037 | 4.836 | <.001 |  |  | -0.02169 | <.001 | 0.01067 | 0.006 |  |  | -9.51e-04 | 0.257 |
| k3 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6289 | -0.1264 | <.001 | 6.423 | <.001 |  |  | -0.03497 | <.001 | -0.002699 | 0.629 |  |  | -5.52e-04 | 0.660 |

### Age-Bin Bootstrap And Scrambling Robustness

Rows summarize the age-balanced bootstrap and age-scrambling checks. These are not new utterance-level regressions; they refit model analogs on child-session-context units to ask whether age ordering is doing real work.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.48 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 0 | 1 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.456 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.52 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.53 | 0.010 |
| k2 | balanced_bootstrap | 5 | 5 | 0 | 0.996 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.496 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.514 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 5 | 0.542 | 0.030 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.934 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.516 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.554 | 0.010 |

### All Plots For M6

#### M1-M6 context-window fixed-effort atlas plots

![k1_m6e_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_morphemes_fixed_effort_atlas.png)
*k1_m6e_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m6e_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_phonemes_fixed_effort_atlas.png)
*k1_m6e_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m6e_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_words_fixed_effort_atlas.png)
*k1_m6e_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m6es_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_morphemes_fixed_effort_atlas.png)
*k1_m6es_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m6es_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_phonemes_fixed_effort_atlas.png)
*k1_m6es_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m6es_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_words_fixed_effort_atlas.png)
*k1_m6es_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m6s_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_morphemes_fixed_effort_atlas.png)
*k1_m6s_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m6s_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_phonemes_fixed_effort_atlas.png)
*k1_m6s_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m6s_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_words_fixed_effort_atlas.png)
*k1_m6s_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m6e_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_morphemes_fixed_effort_atlas.png)
*k2_m6e_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m6e_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_phonemes_fixed_effort_atlas.png)
*k2_m6e_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m6e_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_words_fixed_effort_atlas.png)
*k2_m6e_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m6es_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_morphemes_fixed_effort_atlas.png)
*k2_m6es_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m6es_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_phonemes_fixed_effort_atlas.png)
*k2_m6es_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m6es_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_words_fixed_effort_atlas.png)
*k2_m6es_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m6s_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_morphemes_fixed_effort_atlas.png)
*k2_m6s_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m6s_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_phonemes_fixed_effort_atlas.png)
*k2_m6s_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m6s_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_words_fixed_effort_atlas.png)
*k2_m6s_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m6e_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_morphemes_fixed_effort_atlas.png)
*k3_m6e_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m6e_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_phonemes_fixed_effort_atlas.png)
*k3_m6e_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m6e_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_words_fixed_effort_atlas.png)
*k3_m6e_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m6es_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_morphemes_fixed_effort_atlas.png)
*k3_m6es_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m6es_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_phonemes_fixed_effort_atlas.png)
*k3_m6es_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m6es_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_words_fixed_effort_atlas.png)
*k3_m6es_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m6s_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_morphemes_fixed_effort_atlas.png)
*k3_m6s_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m6s_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_phonemes_fixed_effort_atlas.png)
*k3_m6s_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m6s_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_words_fixed_effort_atlas.png)
*k3_m6s_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m5_m6_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_adjusted_age_predictions.png)
*m5_m6_effort_level_adjusted_age_predictions.png*

![m5_m6_effort_level_average_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png)
*m5_m6_effort_level_average_age_predictions.png*

![m5_m6_saturated_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png)
*m5_m6_saturated_adjusted_age_predictions.png*

![m5_m6_saturated_selected_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png)
*m5_m6_saturated_selected_coefficients.png*

![m6_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png)
*m6_effort_level_adjusted_age_predictions.png*

#### M1-M6 continuous versus effort-level plots

![m6_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m6_dual_effort_predictions.png)
*m6_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m6_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m6_nb_morphemes_atlas_bins.png)
*m6_nb_morphemes_atlas_bins.png; Morphemes*

![m6_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m6_nb_phonemes_atlas_bins.png)
*m6_nb_phonemes_atlas_bins.png; Phonemes*

![m6_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m6_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m6_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_pkg_atlas_bins.png)
*m6_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m6_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m6_nb_words_atlas_bins.png)
*m6_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m6_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_granular_primary_fixed_effort_slices.png)
*m6_granular_primary_fixed_effort_slices.png*

![m6_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m6_marginal_adjusted_global_trends.png)
*m6_marginal_adjusted_global_trends.png*

![m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m6_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_top_frequency_12_fixed_effort_slices.png)
*m6_top_frequency_12_fixed_effort_slices.png*

![m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m6_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m6_age_slope_robustness_intervals.png)
*m6_age_slope_robustness_intervals.png*

![m6_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png)
*m6_clear_robustness_regression_lines.png*


## Appendix A: Context-Predictor Adjunct Atlas

This CF0-CF3 atlas is adjacent to the M1-M6 ladder. It is especially useful for separating target effort, context entropy, and matched context-window size before interpreting M4-M6.

| context_k | model_id | model_label | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7252 | -0.1582 | <.001 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7204 | -0.1784 | <.001 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7461 | -0.0907 | 0.003 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7303 | -0.07571 | 0.009 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7578 | -0.09847 | 0.001 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k1 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6495 | -0.1431 | <.001 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6495 | -0.1481 | <.001 | 0.05917 | 0.274 |  |  | fit |
| k1 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.651 | -0.1402 | <.001 |  |  | -0.175 | <.001 | fit |
| k1 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6506 | -0.1414 | <.001 | -0.06001 | 0.247 | -0.1813 | <.001 | fit |
| k1 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.639 | -0.1585 | <.001 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6388 | -0.1636 | <.001 | 0.06736 | 0.206 |  |  | fit |
| k1 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6403 | -0.1562 | <.001 |  |  | -0.1421 | <.001 | fit |
| k1 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6397 | -0.1576 | <.001 | -0.0464 | 0.357 | -0.1462 | <.001 | fit |
| k1 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6729 | -0.08207 | <.001 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6728 | -0.08435 | <.001 | 0.06356 | 0.204 |  |  | fit |
| k1 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6741 | -0.07966 | <.001 |  |  | -0.1263 | <.001 | fit |
| k1 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6737 | -0.07842 | <.001 | -0.03417 | 0.477 | -0.1285 | <.001 | fit |
| k1 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6572 | -0.06724 | 0.001 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6571 | -0.06823 | <.001 | 0.04786 | 0.346 |  |  | fit |
| k1 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6585 | -0.06479 | 0.002 |  |  | -0.1208 | <.001 | fit |
| k1 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.658 | -0.06222 | 0.002 | -0.05367 | 0.281 | -0.1244 | <.001 | fit |
| k1 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6743 | -0.08519 | <.001 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6743 | -0.08687 | <.001 | 0.02783 | 0.548 |  |  | fit |
| k1 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6755 | -0.08311 | <.001 |  |  | -0.04665 | <.001 | fit |
| k1 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6751 | -0.08125 | <.001 | -0.06489 | 0.143 | -0.04865 | <.001 | fit |
| k2 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6338 | -0.1287 | <.001 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6343 | -0.1318 | <.001 | -0.4107 | <.001 |  |  | fit |
| k2 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.635 | -0.1289 | <.001 |  |  | -0.07164 | <.001 | fit |
| k2 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6347 | -0.1273 | <.001 | -0.4087 | <.001 | -0.06994 | <.001 | fit |
| k2 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6217 | -0.1425 | <.001 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.622 | -0.1458 | <.001 | -0.4256 | <.001 |  |  | fit |
| k2 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6227 | -0.1433 | <.001 |  |  | -0.05554 | <.001 | fit |
| k2 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6223 | -0.142 | <.001 | -0.4253 | <.001 | -0.05438 | <.001 | fit |
| k2 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6551 | -0.06903 | 0.007 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6557 | -0.06891 | 0.006 | -0.4558 | <.001 |  |  | fit |
| k2 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6561 | -0.06963 | 0.007 |  |  | -0.04898 | <.001 | fit |
| k2 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.656 | -0.06519 | 0.009 | -0.4521 | <.001 | -0.04709 | <.001 | fit |
| k2 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.639 | -0.0542 | 0.021 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6396 | -0.05248 | 0.017 | -0.4543 | <.001 |  |  | fit |
| k2 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.64 | -0.05479 | 0.021 |  |  | -0.04671 | <.001 | fit |
| k2 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6399 | -0.04875 | 0.027 | -0.4506 | <.001 | -0.04487 | <.001 | fit |
| k2 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6542 | -0.07096 | 0.005 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6549 | -0.06995 | 0.006 | -0.4942 | <.001 |  |  | fit |
| k2 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6552 | -0.0717 | 0.005 |  |  | -0.01841 | <.001 | fit |
| k2 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6551 | -0.0665 | 0.008 | -0.4898 | <.001 | -0.01751 | <.001 | fit |
| k3 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | -0.4716 | <.001 |  |  | fit |
| k3 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6272 | -0.1239 | <.001 |  |  | -0.04386 | <.001 | fit |
| k3 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6268 | -0.123 | <.001 | -0.4699 | <.001 | -0.0427 | <.001 | fit |
| k3 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | -0.5123 | <.001 |  |  | fit |
| k3 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6142 | -0.1375 | <.001 |  |  | -0.03407 | <.001 | fit |
| k3 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6138 | -0.1369 | <.001 | -0.5111 | <.001 | -0.03298 | <.001 | fit |
| k3 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | -0.5398 | <.001 |  |  | fit |
| k3 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6471 | -0.06497 | 0.016 |  |  | -0.02985 | <.001 | fit |
| k3 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6469 | -0.06126 | 0.018 | -0.5362 | <.001 | -0.02838 | <.001 | fit |
| k3 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | -0.541 | <.001 |  |  | fit |
| k3 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6308 | -0.05014 | 0.044 |  |  | -0.0288 | <.001 | fit |
| k3 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6306 | -0.04483 | 0.052 | -0.537 | <.001 | -0.02722 | <.001 | fit |
| k3 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | -0.5814 | <.001 |  |  | fit |
| k3 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6455 | -0.06667 | 0.013 |  |  | -0.01139 | <.001 | fit |
| k3 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6455 | -0.06221 | 0.016 | -0.577 | <.001 | -0.0106 | <.001 | fit |

### Context Adjunct Plots

#### Context-predictor adjunct fixed-effort atlas plots

![k0_cf0_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_fixed_effort_atlas/k0_cf0_nb_morphemes_fixed_effort_atlas.png)
*k0_cf0_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_cf0_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_fixed_effort_atlas/k0_cf0_nb_phonemes_fixed_effort_atlas.png)
*k0_cf0_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_cf0_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_fixed_effort_atlas/k0_cf0_nb_words_fixed_effort_atlas.png)
*k0_cf0_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_cf0_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf0_nb_morphemes_fixed_effort_atlas.png)
*k1_cf0_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf0_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf0_nb_phonemes_fixed_effort_atlas.png)
*k1_cf0_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf0_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf0_nb_words_fixed_effort_atlas.png)
*k1_cf0_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_cf1_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf1_nb_morphemes_fixed_effort_atlas.png)
*k1_cf1_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf1_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf1_nb_phonemes_fixed_effort_atlas.png)
*k1_cf1_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf1_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf1_nb_words_fixed_effort_atlas.png)
*k1_cf1_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_cf2_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf2_nb_morphemes_fixed_effort_atlas.png)
*k1_cf2_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf2_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf2_nb_phonemes_fixed_effort_atlas.png)
*k1_cf2_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf2_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf2_nb_words_fixed_effort_atlas.png)
*k1_cf2_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_cf3_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf3_nb_morphemes_fixed_effort_atlas.png)
*k1_cf3_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf3_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf3_nb_phonemes_fixed_effort_atlas.png)
*k1_cf3_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf3_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf3_nb_words_fixed_effort_atlas.png)
*k1_cf3_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_cf0_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf0_nb_morphemes_fixed_effort_atlas.png)
*k2_cf0_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf0_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf0_nb_phonemes_fixed_effort_atlas.png)
*k2_cf0_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf0_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf0_nb_words_fixed_effort_atlas.png)
*k2_cf0_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_cf1_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf1_nb_morphemes_fixed_effort_atlas.png)
*k2_cf1_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf1_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf1_nb_phonemes_fixed_effort_atlas.png)
*k2_cf1_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf1_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf1_nb_words_fixed_effort_atlas.png)
*k2_cf1_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_cf2_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf2_nb_morphemes_fixed_effort_atlas.png)
*k2_cf2_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf2_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf2_nb_phonemes_fixed_effort_atlas.png)
*k2_cf2_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf2_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf2_nb_words_fixed_effort_atlas.png)
*k2_cf2_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_cf3_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf3_nb_morphemes_fixed_effort_atlas.png)
*k2_cf3_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf3_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf3_nb_phonemes_fixed_effort_atlas.png)
*k2_cf3_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf3_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf3_nb_words_fixed_effort_atlas.png)
*k2_cf3_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_cf0_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf0_nb_morphemes_fixed_effort_atlas.png)
*k3_cf0_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf0_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf0_nb_phonemes_fixed_effort_atlas.png)
*k3_cf0_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf0_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf0_nb_words_fixed_effort_atlas.png)
*k3_cf0_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_cf1_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf1_nb_morphemes_fixed_effort_atlas.png)
*k3_cf1_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf1_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf1_nb_phonemes_fixed_effort_atlas.png)
*k3_cf1_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf1_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf1_nb_words_fixed_effort_atlas.png)
*k3_cf1_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_cf2_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf2_nb_morphemes_fixed_effort_atlas.png)
*k3_cf2_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf2_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf2_nb_phonemes_fixed_effort_atlas.png)
*k3_cf2_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf2_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf2_nb_words_fixed_effort_atlas.png)
*k3_cf2_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_cf3_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf3_nb_morphemes_fixed_effort_atlas.png)
*k3_cf3_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf3_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf3_nb_phonemes_fixed_effort_atlas.png)
*k3_cf3_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf3_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf3_nb_words_fixed_effort_atlas.png)
*k3_cf3_nb_words_fixed_effort_atlas.png; k3; Words*


## Appendix B: New Cross-Atlas Overview Plots

![M1-M6 continuous-effort models: age coefficients](../figs/m1_m6_super_atlas/dual_continuous_age_coefficients.png)
*M1-M6 continuous-effort models: age coefficients*

![M1-M6 effort-level models: age coefficients](../figs/m1_m6_super_atlas/dual_effort_level_age_coefficients.png)
*M1-M6 effort-level models: age coefficients*

![M1-M6 continuous-effort R2 heatmap.](../figs/m1_m6_super_atlas/dual_continuous_r2.png)
*M1-M6 continuous-effort R2 heatmap.*

![M1-M3 estimator-family age coefficient scatterplot.](../figs/m1_m6_super_atlas/estimator_variant_age_coefficients.png)
*M1-M3 estimator-family age coefficient scatterplot.*

![Context-window age coefficient heatmap.](../figs/m1_m6_super_atlas/context_m1_m6_age_coefficients.png)
*Context-window age coefficient heatmap.*

![Context-window R2 heatmap.](../figs/m1_m6_super_atlas/context_m1_m6_r2.png)
*Context-window R2 heatmap.*

![Signed significance counts for context-predictor terms.](../figs/m1_m6_super_atlas/context_predictor_significance_counts.png)
*Signed significance counts for context-predictor terms.*

![Share of fixed-effort slices with negative age slopes.](../figs/m1_m6_super_atlas/fixed_slice_negative_share.png)
*Share of fixed-effort slices with negative age slopes.*

![Context fixed-slice negative slope share.](../figs/m1_m6_super_atlas/context_fixed_slice_negative_share.png)
*Context fixed-slice negative slope share.*

![Robustness outside-null summary heatmap.](../figs/m1_m6_super_atlas/robustness_outside_null_summary.png)
*Robustness outside-null summary heatmap.*

![Figure counts by source atlas.](../figs/m1_m6_super_atlas/figure_inventory_by_source.png)
*Figure counts by source atlas.*


## Appendix C: Complete Figure Inventory

The report embeds PNGs only. PDF duplicates remain in the figure folders but are intentionally not embedded here.

| source_id | source_label | figures |
| --- | --- | --- |
| context_m1_m6 | M1-M6 context-window fixed-effort atlas plots | 195 |
| context_adjunct | Context-predictor adjunct fixed-effort atlas plots | 65 |
| deep_dive | M1-M3 estimator deep dive plus early M4-M6 plots | 64 |
| fixed_atlas | M1-M6 fixed-effort atlas plots | 32 |
| fixed_slices | M1-M6 fixed-effort slice plots | 30 |
| robustness | Age-bin bootstrap and scrambling robustness plots | 16 |
| dual_effort | M1-M6 continuous versus effort-level plots | 6 |
| m2_simple | Supervisor-facing Model 2 simple plots | 5 |

| source_id | filename | models | context_k | effort_label | path |
| --- | --- | --- | --- | --- | --- |
| deep_dive | m1_coefficients_by_effort_version.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_coefficients_by_effort_version.png |
| deep_dive | m1_expanded_age_coefficients.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_expanded_age_coefficients.png |
| deep_dive | m1_expanded_r2.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_expanded_r2.png |
| deep_dive | m1_glm_gamma_log_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_glm_gamma_log_adjusted_age_lines.png |
| deep_dive | m1_glm_gaussian_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_glm_gaussian_adjusted_age_lines.png |
| deep_dive | m1_low_mid_high_effort_adjusted_age_predictions.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_low_mid_high_effort_adjusted_age_predictions.png |
| deep_dive | m1_m2_adjusted_age_predictions.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png |
| deep_dive | m1_m2_age_coefficients_by_effort.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_age_coefficients_by_effort.png |
| deep_dive | m1_m2_delta_r2_variable_importance.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png |
| deep_dive | m1_m2_effort_coefficients_by_measure.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_effort_coefficients_by_measure.png |
| deep_dive | m1_m2_residual_diagnostics_words.png | M1;M2 |  | Words | figs/m1_m2_utterance_information_deep_dive/m1_m2_residual_diagnostics_words.png |
| deep_dive | m1_ols_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_ols_adjusted_age_lines.png |
| deep_dive | m1_ols_cluster_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png |
| deep_dive | m2_coefficients_by_effort_version.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_coefficients_by_effort_version.png |
| deep_dive | m2_expanded_age_coefficients.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_expanded_age_coefficients.png |
| deep_dive | m2_expanded_r2.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_expanded_r2.png |
| deep_dive | m2_gee_gamma_log_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_gee_gamma_log_adjusted_age_lines.png |
| deep_dive | m2_gee_gaussian_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_gee_gaussian_adjusted_age_lines.png |
| deep_dive | m2_glm_gamma_log_child_fe_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_glm_gamma_log_child_fe_adjusted_age_lines.png |
| deep_dive | m2_low_mid_high_effort_adjusted_age_predictions.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_low_mid_high_effort_adjusted_age_predictions.png |
| deep_dive | m2_mixed_random_age_slope_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_age_slope_adjusted_age_lines.png |
| deep_dive | m2_mixed_random_intercept_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_intercept_adjusted_age_lines.png |
| deep_dive | m2_ols_child_fe_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png |
| deep_dive | m2_ols_child_fe_age_slope_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_age_slope_adjusted_age_lines.png |
| deep_dive | m3_expanded_interaction_coefficients.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png |
| deep_dive | m3_expanded_r2.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_expanded_r2.png |
| deep_dive | m3_gee_gamma_log_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_adjusted_age_lines.png |
| deep_dive | m3_gee_gamma_log_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_interaction_age_lines.png |
| deep_dive | m3_gee_gaussian_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_adjusted_age_lines.png |
| deep_dive | m3_gee_gaussian_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_interaction_age_lines.png |
| deep_dive | m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png |
| deep_dive | m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png |
| deep_dive | m3_glm_gamma_log_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_adjusted_age_lines.png |
| deep_dive | m3_glm_gamma_log_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_interaction_age_lines.png |
| deep_dive | m3_glm_gaussian_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_adjusted_age_lines.png |
| deep_dive | m3_glm_gaussian_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_interaction_age_lines.png |
| deep_dive | m3_mixed_random_age_slope_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_adjusted_age_lines.png |
| deep_dive | m3_mixed_random_age_slope_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_interaction_age_lines.png |
| deep_dive | m3_mixed_random_intercept_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_adjusted_age_lines.png |
| deep_dive | m3_mixed_random_intercept_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_child_fe_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_child_fe_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_cluster_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_cluster_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_interaction_age_lines.png |
| deep_dive | m4_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png |
| deep_dive | m4_context_entropy_coefficients.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_coefficients.png |
| deep_dive | m4_context_entropy_descriptive_bins.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png |
| deep_dive | m4_effort_quantile_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_effort_quantile_adjusted_predictions.png |
| deep_dive | m4_m4a_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4a_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4b_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4b_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4c_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4c_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4d_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4d_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4e_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4e_context_entropy_adjusted_predictions.png |
| deep_dive | m5_effort_level_adjusted_age_predictions.png | M5 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png |
| deep_dive | m5_m6_effort_level_adjusted_age_predictions.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_adjusted_age_predictions.png |
| deep_dive | m5_m6_effort_level_average_age_predictions.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png |
| deep_dive | m5_m6_saturated_adjusted_age_predictions.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png |
| deep_dive | m5_m6_saturated_selected_coefficients.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png |
| deep_dive | m6_effort_level_adjusted_age_predictions.png | M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png |
| deep_dive | predictor_correlation_heatmap.png |  |  |  | figs/m1_m2_utterance_information_deep_dive/predictor_correlation_heatmap.png |
| dual_effort | m1_dual_effort_predictions.png | M1 |  |  | figs/m1_m6_dual_effort_quick_share/m1_dual_effort_predictions.png |
| dual_effort | m2_dual_effort_predictions.png | M2 |  |  | figs/m1_m6_dual_effort_quick_share/m2_dual_effort_predictions.png |
| dual_effort | m3_dual_effort_predictions.png | M3 |  |  | figs/m1_m6_dual_effort_quick_share/m3_dual_effort_predictions.png |
| dual_effort | m4_dual_effort_predictions.png | M4 |  |  | figs/m1_m6_dual_effort_quick_share/m4_dual_effort_predictions.png |
| dual_effort | m5_dual_effort_predictions.png | M5 |  |  | figs/m1_m6_dual_effort_quick_share/m5_dual_effort_predictions.png |
| dual_effort | m6_dual_effort_predictions.png | M6 |  |  | figs/m1_m6_dual_effort_quick_share/m6_dual_effort_predictions.png |
| fixed_slices | m1_granular_primary_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_granular_primary_fixed_effort_slices.png |
| fixed_slices | m1_marginal_adjusted_global_trends.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_marginal_adjusted_global_trends.png |
| fixed_slices | m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m1_top_frequency_12_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m2_granular_primary_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_granular_primary_fixed_effort_slices.png |
| fixed_slices | m2_marginal_adjusted_global_trends.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_marginal_adjusted_global_trends.png |
| fixed_slices | m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m2_top_frequency_12_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m3_granular_primary_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_granular_primary_fixed_effort_slices.png |
| fixed_slices | m3_marginal_adjusted_global_trends.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_marginal_adjusted_global_trends.png |
| fixed_slices | m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m3_top_frequency_12_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m4_granular_primary_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_granular_primary_fixed_effort_slices.png |
| fixed_slices | m4_marginal_adjusted_global_trends.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_marginal_adjusted_global_trends.png |
| fixed_slices | m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m4_top_frequency_12_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m5_granular_primary_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_granular_primary_fixed_effort_slices.png |
| fixed_slices | m5_marginal_adjusted_global_trends.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_marginal_adjusted_global_trends.png |
| fixed_slices | m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m5_top_frequency_12_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m6_granular_primary_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_granular_primary_fixed_effort_slices.png |
| fixed_slices | m6_marginal_adjusted_global_trends.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_marginal_adjusted_global_trends.png |
| fixed_slices | m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m6_top_frequency_12_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_atlas | atlas_effort_bin_distribution.png |  |  |  | figs/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution.png |
| fixed_atlas | atlas_effort_bin_distribution_by_age.png |  |  |  | figs/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution_by_age.png |
| fixed_atlas | m1_nb_morphemes_atlas_bins.png | M1 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m1_nb_morphemes_atlas_bins.png |
| fixed_atlas | m1_nb_phonemes_atlas_bins.png | M1 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m1_nb_phonemes_atlas_bins.png |
| fixed_atlas | m1_nb_syllables_cmu_or_pkg_atlas_bins.png | M1 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m1_nb_syllables_pkg_atlas_bins.png | M1 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m1_nb_words_atlas_bins.png | M1 |  | Words | figs/m1_m6_fixed_effort_atlas/m1_nb_words_atlas_bins.png |
| fixed_atlas | m2_nb_morphemes_atlas_bins.png | M2 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m2_nb_morphemes_atlas_bins.png |
| fixed_atlas | m2_nb_phonemes_atlas_bins.png | M2 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m2_nb_phonemes_atlas_bins.png |
| fixed_atlas | m2_nb_syllables_cmu_or_pkg_atlas_bins.png | M2 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m2_nb_syllables_pkg_atlas_bins.png | M2 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m2_nb_words_atlas_bins.png | M2 |  | Words | figs/m1_m6_fixed_effort_atlas/m2_nb_words_atlas_bins.png |
| fixed_atlas | m3_nb_morphemes_atlas_bins.png | M3 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m3_nb_morphemes_atlas_bins.png |
| fixed_atlas | m3_nb_phonemes_atlas_bins.png | M3 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m3_nb_phonemes_atlas_bins.png |
| fixed_atlas | m3_nb_syllables_cmu_or_pkg_atlas_bins.png | M3 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m3_nb_syllables_pkg_atlas_bins.png | M3 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m3_nb_words_atlas_bins.png | M3 |  | Words | figs/m1_m6_fixed_effort_atlas/m3_nb_words_atlas_bins.png |
| fixed_atlas | m4_nb_morphemes_atlas_bins.png | M4 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m4_nb_morphemes_atlas_bins.png |
| fixed_atlas | m4_nb_phonemes_atlas_bins.png | M4 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m4_nb_phonemes_atlas_bins.png |
| fixed_atlas | m4_nb_syllables_cmu_or_pkg_atlas_bins.png | M4 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m4_nb_syllables_pkg_atlas_bins.png | M4 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m4_nb_words_atlas_bins.png | M4 |  | Words | figs/m1_m6_fixed_effort_atlas/m4_nb_words_atlas_bins.png |
| fixed_atlas | m5_nb_morphemes_atlas_bins.png | M5 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m5_nb_morphemes_atlas_bins.png |
| fixed_atlas | m5_nb_phonemes_atlas_bins.png | M5 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m5_nb_phonemes_atlas_bins.png |
| fixed_atlas | m5_nb_syllables_cmu_or_pkg_atlas_bins.png | M5 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m5_nb_syllables_pkg_atlas_bins.png | M5 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m5_nb_words_atlas_bins.png | M5 |  | Words | figs/m1_m6_fixed_effort_atlas/m5_nb_words_atlas_bins.png |
| fixed_atlas | m6_nb_morphemes_atlas_bins.png | M6 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m6_nb_morphemes_atlas_bins.png |
| fixed_atlas | m6_nb_phonemes_atlas_bins.png | M6 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m6_nb_phonemes_atlas_bins.png |
| fixed_atlas | m6_nb_syllables_cmu_or_pkg_atlas_bins.png | M6 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m6_nb_syllables_pkg_atlas_bins.png | M6 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m6_nb_words_atlas_bins.png | M6 |  | Words | figs/m1_m6_fixed_effort_atlas/m6_nb_words_atlas_bins.png |
| context_m1_m6 | k0_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k0 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k0 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k0 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k0 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_words_fixed_effort_atlas.png | M1 | k0 | Words | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k0 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k0 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k0 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k0 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_words_fixed_effort_atlas.png | M2 | k0 | Words | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k0 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k0 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k0 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k0 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_words_fixed_effort_atlas.png | M3 | k0 | Words | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_words_fixed_effort_atlas.png | M1 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_words_fixed_effort_atlas.png | M2 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_words_fixed_effort_atlas.png | M3 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_morphemes_fixed_effort_atlas.png | M4 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_phonemes_fixed_effort_atlas.png | M4 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_words_fixed_effort_atlas.png | M4 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_morphemes_fixed_effort_atlas.png | M4 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_phonemes_fixed_effort_atlas.png | M4 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_words_fixed_effort_atlas.png | M4 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_morphemes_fixed_effort_atlas.png | M4 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_phonemes_fixed_effort_atlas.png | M4 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_words_fixed_effort_atlas.png | M4 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_morphemes_fixed_effort_atlas.png | M5 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_phonemes_fixed_effort_atlas.png | M5 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_words_fixed_effort_atlas.png | M5 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_morphemes_fixed_effort_atlas.png | M5 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_phonemes_fixed_effort_atlas.png | M5 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_words_fixed_effort_atlas.png | M5 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_morphemes_fixed_effort_atlas.png | M5 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_phonemes_fixed_effort_atlas.png | M5 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_words_fixed_effort_atlas.png | M5 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_morphemes_fixed_effort_atlas.png | M6 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_phonemes_fixed_effort_atlas.png | M6 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_words_fixed_effort_atlas.png | M6 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_morphemes_fixed_effort_atlas.png | M6 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_phonemes_fixed_effort_atlas.png | M6 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_words_fixed_effort_atlas.png | M6 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_morphemes_fixed_effort_atlas.png | M6 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_phonemes_fixed_effort_atlas.png | M6 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_words_fixed_effort_atlas.png | M6 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_words_fixed_effort_atlas.png | M1 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_words_fixed_effort_atlas.png | M2 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_words_fixed_effort_atlas.png | M3 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_morphemes_fixed_effort_atlas.png | M4 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_phonemes_fixed_effort_atlas.png | M4 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_words_fixed_effort_atlas.png | M4 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_morphemes_fixed_effort_atlas.png | M4 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_phonemes_fixed_effort_atlas.png | M4 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_words_fixed_effort_atlas.png | M4 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_morphemes_fixed_effort_atlas.png | M4 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_phonemes_fixed_effort_atlas.png | M4 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_words_fixed_effort_atlas.png | M4 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_morphemes_fixed_effort_atlas.png | M5 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_phonemes_fixed_effort_atlas.png | M5 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_words_fixed_effort_atlas.png | M5 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_morphemes_fixed_effort_atlas.png | M5 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_phonemes_fixed_effort_atlas.png | M5 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_words_fixed_effort_atlas.png | M5 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_morphemes_fixed_effort_atlas.png | M5 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_phonemes_fixed_effort_atlas.png | M5 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_words_fixed_effort_atlas.png | M5 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_morphemes_fixed_effort_atlas.png | M6 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_phonemes_fixed_effort_atlas.png | M6 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_words_fixed_effort_atlas.png | M6 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_morphemes_fixed_effort_atlas.png | M6 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_phonemes_fixed_effort_atlas.png | M6 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_words_fixed_effort_atlas.png | M6 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_morphemes_fixed_effort_atlas.png | M6 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_phonemes_fixed_effort_atlas.png | M6 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_words_fixed_effort_atlas.png | M6 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_words_fixed_effort_atlas.png | M1 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_words_fixed_effort_atlas.png | M2 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_words_fixed_effort_atlas.png | M3 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_morphemes_fixed_effort_atlas.png | M4 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_phonemes_fixed_effort_atlas.png | M4 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_words_fixed_effort_atlas.png | M4 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_morphemes_fixed_effort_atlas.png | M4 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_phonemes_fixed_effort_atlas.png | M4 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_words_fixed_effort_atlas.png | M4 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_morphemes_fixed_effort_atlas.png | M4 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_phonemes_fixed_effort_atlas.png | M4 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_words_fixed_effort_atlas.png | M4 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_morphemes_fixed_effort_atlas.png | M5 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_phonemes_fixed_effort_atlas.png | M5 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_words_fixed_effort_atlas.png | M5 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_morphemes_fixed_effort_atlas.png | M5 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_phonemes_fixed_effort_atlas.png | M5 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_words_fixed_effort_atlas.png | M5 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_morphemes_fixed_effort_atlas.png | M5 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_phonemes_fixed_effort_atlas.png | M5 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_words_fixed_effort_atlas.png | M5 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_morphemes_fixed_effort_atlas.png | M6 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_phonemes_fixed_effort_atlas.png | M6 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_words_fixed_effort_atlas.png | M6 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_morphemes_fixed_effort_atlas.png | M6 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_phonemes_fixed_effort_atlas.png | M6 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_words_fixed_effort_atlas.png | M6 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_morphemes_fixed_effort_atlas.png | M6 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_phonemes_fixed_effort_atlas.png | M6 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_words_fixed_effort_atlas.png | M6 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_words_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_morphemes_fixed_effort_atlas.png |  | k0 | Morphemes | figs/context_fixed_effort_atlas/k0_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_phonemes_fixed_effort_atlas.png |  | k0 | Phonemes | figs/context_fixed_effort_atlas/k0_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k0 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k0 | Syllables: pkg | figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_words_fixed_effort_atlas.png |  | k0 | Words | figs/context_fixed_effort_atlas/k0_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf1_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf1_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf1_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf2_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf2_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf2_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf3_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf3_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf3_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf1_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf1_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf1_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf2_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf2_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf2_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf3_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf3_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf3_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf1_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf1_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf1_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf2_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf2_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf2_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf3_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf3_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf3_nb_words_fixed_effort_atlas.png |
| robustness | age_bin_unit_support.png |  |  |  | figs/age_scrambling_robustness/age_bin_unit_support.png |
| robustness | balanced_bootstrap_age_slope_ci.png |  |  |  | figs/age_scrambling_robustness/balanced_bootstrap_age_slope_ci.png |
| robustness | m1_age_slope_robustness_intervals.png | M1 |  |  | figs/age_scrambling_robustness/m1_age_slope_robustness_intervals.png |
| robustness | m1_clear_robustness_regression_lines.png | M1 |  |  | figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png |
| robustness | m2_age_slope_robustness_intervals.png | M2 |  |  | figs/age_scrambling_robustness/m2_age_slope_robustness_intervals.png |
| robustness | m2_clear_robustness_regression_lines.png | M2 |  |  | figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png |
| robustness | m3_age_slope_robustness_intervals.png | M3 |  |  | figs/age_scrambling_robustness/m3_age_slope_robustness_intervals.png |
| robustness | m3_clear_robustness_regression_lines.png | M3 |  |  | figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png |
| robustness | m4_age_slope_robustness_intervals.png | M4 |  |  | figs/age_scrambling_robustness/m4_age_slope_robustness_intervals.png |
| robustness | m4_clear_robustness_regression_lines.png | M4 |  |  | figs/age_scrambling_robustness/m4_clear_robustness_regression_lines.png |
| robustness | m5_age_slope_robustness_intervals.png | M5 |  |  | figs/age_scrambling_robustness/m5_age_slope_robustness_intervals.png |
| robustness | m5_clear_robustness_regression_lines.png | M5 |  |  | figs/age_scrambling_robustness/m5_clear_robustness_regression_lines.png |
| robustness | m6_age_slope_robustness_intervals.png | M6 |  |  | figs/age_scrambling_robustness/m6_age_slope_robustness_intervals.png |
| robustness | m6_clear_robustness_regression_lines.png | M6 |  |  | figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png |
| robustness | observed_age_slope_overview.png |  |  |  | figs/age_scrambling_robustness/observed_age_slope_overview.png |
| robustness | robustness_outside_null_heatmap.png |  |  |  | figs/age_scrambling_robustness/robustness_outside_null_heatmap.png |
| m2_simple | m2_morphemes_fixed_effort_and_global_trend.png | M2 |  | Morphemes | figs/m2_simple_plots/m2_morphemes_fixed_effort_and_global_trend.png |
| m2_simple | m2_phonemes_fixed_effort_and_global_trend.png | M2 |  | Phonemes | figs/m2_simple_plots/m2_phonemes_fixed_effort_and_global_trend.png |
| m2_simple | m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png | M2 |  | Syllables: CMU/pkg | figs/m2_simple_plots/m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png |
| m2_simple | m2_syllables_pkg_fixed_effort_and_global_trend.png | M2 |  | Syllables: pkg | figs/m2_simple_plots/m2_syllables_pkg_fixed_effort_and_global_trend.png |
| m2_simple | m2_words_fixed_effort_and_global_trend.png | M2 |  | Words | figs/m2_simple_plots/m2_words_fixed_effort_and_global_trend.png |