# Supervisor Formula Estimator Sensitivity

Generated on 2026-06-23.

This side report does exactly one thing: it takes the four formulas currently used in the supervisor-facing report and fits estimator variants around those formulas. It does not include exact-length F19/F21 models, generated baselines, caretaker contrasts, question-type variants, or session-level random intercepts.

All plots here use real child k3 rows and word count as the effort measure, because that is the version used for the current Model 3 and Model 4 supervisor plots. The aggregate estimators use child-age-exact-word cells, not session-ID cells.

Fit status counts: `{'fit': 20}`.

## The Four Formulas

| Model | Formula | Estimator adaptation note |
| --- | --- | --- |
| M1 | `sum_bits ~ age + effort` | No child identity in the mean formula. |
| M2 | `sum_bits ~ age + effort + child identity` | OLS/GEE use fixed child intercepts; MixedLM adapts child identity to random child intercepts. |
| M3 | `sum_bits ~ age + effort + age:effort + child identity` | OLS/GEE use fixed child intercepts; MixedLM adapts child identity to random child intercepts. |
| M4 | `sum_bits ~ age + effort + age:effort + parent context effort + context entropy + child identity` | OLS/GEE use fixed child intercepts; MixedLM adapts child identity to random child intercepts. |

## How To Read These Plots

Each panel is a different estimator or repeated-measures structure. Within a panel, the colored lines are predictions at exact fixed word counts from 1 to 12. The clean question is whether the same formula gives the same age-line direction after the estimator changes.

No panel uses `session_id` as a predictor, grouping factor, or random intercept. The row-level panels fit utterance rows directly. The cell-level panels average repeated rows inside child-age-word cells before fitting OLS/GEE/MixedLM checks. MixedLM panels use child random intercepts only.

Do not compare the vertical intercepts too aggressively across estimator families. Some panels are row-level predictions averaged over fixed child intercepts; others are population-average GEE or mixed-model fixed-effect predictions. The slope direction and flattening/steepening are the main comparison.

## Exact Formula Used In Each Panel

The table below separates the fixed-effects mean formula from the estimator structure. This is the part to audit if a plot looks surprising.

| formula_id | estimator_id | readable_formula | adaptation_note | n_obs | n_source_rows |
| --- | --- | --- | --- | --- | --- |
| M1 | row_ols_plain | sum_bits ~ age + target_effort | Exact fixed-effect mean formula; child grouping only affects uncertainty/correlation. | 446985 | 446985 |
| M1 | row_ols_cluster | sum_bits ~ age + target_effort | Exact fixed-effect mean formula; child grouping only affects uncertainty/correlation. | 446985 | 446985 |
| M1 | age_word_ols_cluster | sum_bits ~ age + target_effort | Exact fixed-effect mean formula; child grouping only affects uncertainty/correlation. | 27109 | 446985 |
| M1 | age_word_gee_gaussian | sum_bits ~ age + target_effort | Exact fixed-effect mean formula; child grouping only affects uncertainty/correlation. | 27109 | 446985 |
| M1 | age_word_gee_gamma_log | sum_bits ~ age + target_effort | Exact fixed-effect mean formula; child grouping only affects uncertainty/correlation. | 27109 | 446985 |
| M2 | row_ols_fe_cluster | sum_bits ~ age + target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 446985 | 446985 |
| M2 | age_word_ols_fe_cluster | sum_bits ~ age + target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 27109 | 446985 |
| M2 | age_word_gee_gaussian_fe | sum_bits ~ age + target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 27109 | 446985 |
| M2 | age_word_gee_gamma_log_fe | sum_bits ~ age + target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 27109 | 446985 |
| M2 | age_word_mixed_random_intercept | sum_bits ~ age + target_effort | Child identity adapted from fixed intercepts to random child intercepts. | 27109 | 446985 |
| M3 | row_ols_fe_cluster | sum_bits ~ age + target_effort + age:target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 446985 | 446985 |
| M3 | age_word_ols_fe_cluster | sum_bits ~ age + target_effort + age:target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 27109 | 446985 |
| M3 | age_word_gee_gaussian_fe | sum_bits ~ age + target_effort + age:target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 27109 | 446985 |
| M3 | age_word_gee_gamma_log_fe | sum_bits ~ age + target_effort + age:target_effort + C(child_id) | Exact child-identity formula using fixed child intercepts. | 27109 | 446985 |
| M3 | age_word_mixed_random_intercept | sum_bits ~ age + target_effort + age:target_effort | Child identity adapted from fixed intercepts to random child intercepts. | 27109 | 446985 |
| M4 | row_ols_fe_cluster | sum_bits ~ age + target_effort + age:target_effort + parent_context_target_effort + context_entropy + C(child_id) | Exact child-identity formula using fixed child intercepts. | 441413 | 441413 |
| M4 | age_word_ols_fe_cluster | sum_bits ~ age + target_effort + age:target_effort + parent_context_target_effort + context_entropy + C(child_id) | Exact child-identity formula using fixed child intercepts. | 25989 | 441413 |
| M4 | age_word_gee_gaussian_fe | sum_bits ~ age + target_effort + age:target_effort + parent_context_target_effort + context_entropy + C(child_id) | Exact child-identity formula using fixed child intercepts. | 25989 | 441413 |
| M4 | age_word_gee_gamma_log_fe | sum_bits ~ age + target_effort + age:target_effort + parent_context_target_effort + context_entropy + C(child_id) | Exact child-identity formula using fixed child intercepts. | 25989 | 441413 |
| M4 | age_word_mixed_random_intercept | sum_bits ~ age + target_effort + age:target_effort + parent_context_target_effort + context_entropy | Child identity adapted from fixed intercepts to random child intercepts. | 25989 | 441413 |

## Main Plots

### M1: Only controlling for effort

![M1 fixed-word estimator panels](../figs/supervisor_formula_estimator_sensitivity/m1_fixed_word_estimator_panels.png)

### M2: Effort plus child identity

![M2 fixed-word estimator panels](../figs/supervisor_formula_estimator_sensitivity/m2_fixed_word_estimator_panels.png)

### M3: Age by effort plus child identity

![M3 fixed-word estimator panels](../figs/supervisor_formula_estimator_sensitivity/m3_fixed_word_estimator_panels.png)

### M4: Both context controls, no question type

![M4 fixed-word estimator panels](../figs/supervisor_formula_estimator_sensitivity/m4_fixed_word_estimator_panels.png)

## Slope Heatmap

This heatmap gives the same information numerically: each cell is the age slope in predicted bits per six months at that fixed word count.

![Fixed-word slope heatmap](../figs/supervisor_formula_estimator_sensitivity/fixed_word_slope_heatmap.png)

## Representative Slopes

For quick reading, here are the slopes at 2, 6, and 10 words. Units are predicted bits per six months.

| formula_id | estimator_id | 2 | 6 | 10 |
| --- | --- | --- | --- | --- |
| M1 | age_word_gee_gamma_log | -0.344 | -0.583 | -0.990 |
| M1 | age_word_gee_gaussian | -0.280 | -0.280 | -0.280 |
| M1 | age_word_ols_cluster | 0.598 | 0.598 | 0.598 |
| M1 | row_ols_cluster | 0.002 | 0.002 | 0.002 |
| M1 | row_ols_plain | 0.002 | 0.002 | 0.002 |
| M2 | age_word_gee_gamma_log_fe | -0.305 | -0.517 | -0.875 |
| M2 | age_word_gee_gaussian_fe | -0.287 | -0.287 | -0.287 |
| M2 | age_word_mixed_random_intercept | -0.287 | -0.287 | -0.287 |
| M2 | age_word_ols_fe_cluster | -0.287 | -0.287 | -0.287 |
| M2 | row_ols_fe_cluster | -0.735 | -0.735 | -0.735 |
| M3 | age_word_gee_gamma_log_fe | 0.126 | -0.779 | -2.968 |
| M3 | age_word_gee_gaussian_fe | -0.344 | -0.267 | -0.189 |
| M3 | age_word_mixed_random_intercept | -0.344 | -0.267 | -0.189 |
| M3 | age_word_ols_fe_cluster | -0.344 | -0.267 | -0.189 |
| M3 | row_ols_fe_cluster | -0.714 | -0.805 | -0.896 |
| M4 | age_word_gee_gamma_log_fe | 0.100 | -0.815 | -3.054 |
| M4 | age_word_gee_gaussian_fe | -0.324 | -0.213 | -0.102 |
| M4 | age_word_mixed_random_intercept | -0.324 | -0.213 | -0.102 |
| M4 | age_word_ols_fe_cluster | -0.324 | -0.213 | -0.102 |
| M4 | row_ols_fe_cluster | -0.724 | -0.790 | -0.857 |

## Saved Artifacts

```text
results/supervisor_formula_estimator_sensitivity/model_summary.csv
results/supervisor_formula_estimator_sensitivity/coefficient_long.csv
results/supervisor_formula_estimator_sensitivity/fixed_effort_predictions.csv.gz
results/supervisor_formula_estimator_sensitivity/fixed_slice_slopes.csv
results/supervisor_formula_estimator_sensitivity/representative_fixed_word_slopes.csv
results/supervisor_formula_estimator_sensitivity/formula_definitions.csv
results/supervisor_formula_estimator_sensitivity/estimator_definitions.csv
results/supervisor_formula_estimator_sensitivity/figure_manifest.csv
figs/supervisor_formula_estimator_sensitivity
```
