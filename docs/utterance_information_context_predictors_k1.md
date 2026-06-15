# Context Predictor Permutations: k1

This internal report is separate from the previous M1-M6 reports. It asks
whether context predictors explain total child utterance information.

Context predictors are computed from the preceding caretaker context text for this k window.

## Model Question

Outcome:

```text
sum_bits
```

Baseline controls:

```text
age + target utterance effort + child identity
```

Context predictor permutations:

```text
C0: no context predictor
C1: context entropy only
C2: context-window size only
C3: context entropy + context-window size
```

Implementation details for every fitted row:

```text
Estimator: linear ordinary least squares regression
Library: statsmodels.formula.api.ols
Uncertainty: child-cluster robust standard errors, cov_type='cluster'
Cluster unit: child_id
```

This means the fitted mean is linear in the listed predictors. The p-values and
confidence intervals are adjusted for repeated observations within children by
clustering the covariance matrix at the child level. This is not a GEE, GLM, or
mixed-effects model; those would be separate estimator subvariants.

The target utterance effort unit and context-window size unit are varied
separately. That means, for example, one row may control target utterance
phonemes while using context-window words as the context-size predictor.

## Table Column Guide

| column | how_to_interpret |
| --- | --- |
| model_label | Which context-predictor permutation is being fit. |
| estimator | The model family. Here this is linear OLS for every fitted row. |
| library | The Python implementation used to fit the model. |
| covariance | How standard errors and p-values are computed. |
| target_effort_label | Which target utterance effort unit is controlled. |
| context_size_label | Which context-window size unit is used; blank when the model has no context-size predictor. |
| r2_observed_fitted | In-sample fitted-versus-observed R2. |
| delta_r2_vs_baseline | Extra R2 relative to the same target-effort baseline with no context predictor. |
| context_entropy_coef | Estimated bit change for a one-bit increase in context entropy. |
| context_size_coef | Estimated bit change for one additional context-size unit. |
| std_context_entropy_beta | Standardized entropy coefficient, useful for scale comparison. |
| std_context_size_beta | Standardized context-size coefficient, useful for scale comparison. |

## Context Predictor Distributions

How to read: these tables and plots describe the context window itself, not the
target utterance. For `k0`, context sizes are zero and entropy is unavailable.

| context_k | measure_col | measure_label | rows | mean | median | p75 | p90 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k1 | context_nb_words | Context words | 446985 | 4.46 | 4 | 6 | 9 | 109 |
| k1 | context_nb_morphemes | Context morphemes | 446985 | 5.13 | 4 | 7 | 10 | 117 |
| k1 | context_nb_syllables_cmu_or_pkg | Context syllables: CMU/pkg | 446985 | 5.42 | 5 | 7 | 10 | 125 |
| k1 | context_nb_syllables_pkg | Context syllables: pkg | 446985 | 5.71 | 5 | 8 | 11 | 132 |
| k1 | context_nb_phonemes | Context phonemes | 446985 | 13.7 | 12 | 19 | 26 | 326 |
| k1 | context_entropy_bits | Context entropy bits | 442220 | 5.71 | 5.67 | 6.49 | 7.32 | 11.2 |

![k1 context size distribution](../figs/context_predictor_permutations/k1_context_size_distribution.png)

![k1 context predictors by age](../figs/context_predictor_permutations/k1_context_predictors_by_age.png)

## Model Fit Overview

How to read: the R2 plot shows fit; the delta-R2 plot shows how much context
predictors add beyond age, target effort, and child identity.

![k1 R2 by model family](../figs/context_predictor_permutations/k1_model_family_r2.png)

## Coefficient Views

How to read: coefficients are in Mistral bits. Negative entropy coefficients
mean higher context entropy is associated with lower target utterance bits after
controls; positive context-size coefficients mean longer preceding context is
associated with higher target utterance bits after controls.

![k1 entropy coefficients](../figs/context_predictor_permutations/k1_entropy_coefficients.png)

![k1 context size coefficients](../figs/context_predictor_permutations/k1_context_size_coefficients.png)

![k1 age coefficients](../figs/context_predictor_permutations/k1_age_coefficients.png)

## Top Context Effects

| model_label | target_effort_label | context_size_label | r2_observed_fitted | delta_r2_vs_baseline | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Context size only | Words | Context words | 0.651 | 0.001487 |  |  | -0.175 | <.001 |  | -0.03416 |
| Context size only | Words | Context syllables: pkg | 0.6509 | 0.001322 |  |  | -0.1242 | <.001 |  | -0.03161 |
| Context size only | Words | Context morphemes | 0.6509 | 0.001312 |  |  | -0.1391 | <.001 |  | -0.0314 |
| Context size only | Morphemes | Context words | 0.6403 | 0.001287 |  |  | -0.1658 | <.001 |  | -0.03237 |
| Context size only | Words | Context phonemes | 0.6508 | 0.001283 |  |  | -0.0508 | <.001 |  | -0.03097 |
| Context size only | Morphemes | Context morphemes | 0.6403 | 0.001269 |  |  | -0.1421 | <.001 |  | -0.03208 |
| Context size only | Syllables: CMU/pkg | Context syllables: pkg | 0.6741 | 0.001259 |  |  | -0.1215 | <.001 |  | -0.03093 |
| Context size only | Syllables: pkg | Context syllables: pkg | 0.6585 | 0.001253 |  |  | -0.1208 | <.001 |  | -0.03075 |
| Context size only | Words | Context syllables: CMU/pkg | 0.6508 | 0.001244 |  |  | -0.126 | <.001 |  | -0.03032 |
| Context size only | Syllables: CMU/pkg | Context syllables: CMU/pkg | 0.6741 | 0.001226 |  |  | -0.1263 | <.001 |  | -0.03038 |
| Context size only | Morphemes | Context phonemes | 0.6402 | 0.00118 |  |  | -0.05028 | <.001 |  | -0.03065 |
| Context size only | Syllables: CMU/pkg | Context phonemes | 0.6741 | 0.001174 |  |  | -0.04836 | <.001 |  | -0.02948 |

## Full Model Summary

| model_label | estimator | library | covariance | target_effort_label | context_size_label | status | n_obs | n_children | r2_observed_fitted | delta_r2_vs_baseline | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 446985 | 21 | 0.6495 | 0 | -0.1431 | <.001 | 6.677 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 442220 | 21 | 0.6495 | -5.696e-05 | -0.1481 | <.001 | 6.68 | <.001 | 0.05917 | 0.274 |  |  | 0.004744 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | fit | 444325 | 21 | 0.651 | 0.001487 | -0.1402 | <.001 | 6.671 | <.001 |  |  | -0.175 | <.001 |  | -0.03416 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | fit | 444325 | 21 | 0.6509 | 0.001312 | -0.141 | <.001 | 6.672 | <.001 |  |  | -0.1391 | <.001 |  | -0.0314 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6508 | 0.001244 | -0.141 | <.001 | 6.671 | <.001 |  |  | -0.126 | <.001 |  | -0.03032 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | fit | 444325 | 21 | 0.6509 | 0.001322 | -0.1408 | <.001 | 6.671 | <.001 |  |  | -0.1242 | <.001 |  | -0.03161 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | fit | 444325 | 21 | 0.6508 | 0.001283 | -0.1409 | <.001 | 6.671 | <.001 |  |  | -0.0508 | <.001 |  | -0.03097 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | fit | 442220 | 21 | 0.6506 | 0.001066 | -0.1414 | <.001 | 6.679 | <.001 | -0.06001 | 0.247 | -0.1813 | <.001 | -0.004811 | -0.0354 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | fit | 442220 | 21 | 0.6504 | 0.0008886 | -0.1422 | <.001 | 6.68 | <.001 | -0.05292 | 0.302 | -0.1441 | <.001 | -0.004242 | -0.03253 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | fit | 442220 | 21 | 0.6504 | 0.0008115 | -0.1422 | <.001 | 6.679 | <.001 | -0.03889 | 0.437 | -0.1289 | <.001 | -0.003118 | -0.03103 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | fit | 442220 | 21 | 0.6504 | 0.0008957 | -0.142 | <.001 | 6.679 | <.001 | -0.04511 | 0.371 | -0.1277 | <.001 | -0.003616 | -0.03252 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | fit | 442220 | 21 | 0.6504 | 0.000855 | -0.1421 | <.001 | 6.679 | <.001 | -0.04016 | 0.420 | -0.0521 | <.001 | -0.00322 | -0.03176 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 446985 | 21 | 0.639 | 0 | -0.1585 | <.001 | 5.772 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 442220 | 21 | 0.6388 | -0.0002362 | -0.1636 | <.001 | 5.773 | <.001 | 0.06736 | 0.206 |  |  | 0.0054 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | fit | 444325 | 21 | 0.6403 | 0.001287 | -0.1558 | <.001 | 5.765 | <.001 |  |  | -0.1658 | <.001 |  | -0.03237 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | fit | 444325 | 21 | 0.6403 | 0.001269 | -0.1562 | <.001 | 5.767 | <.001 |  |  | -0.1421 | <.001 |  | -0.03208 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6401 | 0.001103 | -0.1564 | <.001 | 5.766 | <.001 |  |  | -0.1219 | <.001 |  | -0.02932 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | fit | 444325 | 21 | 0.6402 | 0.001173 | -0.1562 | <.001 | 5.765 | <.001 |  |  | -0.1199 | <.001 |  | -0.03053 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | fit | 444325 | 21 | 0.6402 | 0.00118 | -0.1562 | <.001 | 5.766 | <.001 |  |  | -0.05028 | <.001 |  | -0.03065 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | fit | 442220 | 21 | 0.6397 | 0.0007528 | -0.1571 | <.001 | 5.771 | <.001 | -0.04444 | 0.384 | -0.1701 | <.001 | -0.003563 | -0.03321 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | fit | 442220 | 21 | 0.6397 | 0.0007377 | -0.1576 | <.001 | 5.772 | <.001 | -0.0464 | 0.357 | -0.1462 | <.001 | -0.00372 | -0.03302 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | fit | 442220 | 21 | 0.6396 | 0.0005611 | -0.1578 | <.001 | 5.771 | <.001 | -0.02659 | 0.589 | -0.1235 | <.001 | -0.002131 | -0.02973 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | fit | 442220 | 21 | 0.6396 | 0.000636 | -0.1576 | <.001 | 5.771 | <.001 | -0.0324 | 0.513 | -0.1222 | <.001 | -0.002598 | -0.03112 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | fit | 442220 | 21 | 0.6396 | 0.0006428 | -0.1577 | <.001 | 5.771 | <.001 | -0.03015 | 0.540 | -0.05115 | <.001 | -0.002417 | -0.03118 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 446985 | 21 | 0.6729 | 0 | -0.08207 | <.001 | 5.502 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 442220 | 21 | 0.6728 | -3.878e-05 | -0.08435 | <.001 | 5.502 | <.001 | 0.06356 | 0.204 |  |  | 0.005096 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | fit | 444325 | 21 | 0.674 | 0.001084 | -0.08001 | <.001 | 5.496 | <.001 |  |  | -0.1425 | <.001 |  | -0.02781 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | fit | 444325 | 21 | 0.6739 | 0.001001 | -0.08059 | <.001 | 5.496 | <.001 |  |  | -0.1162 | <.001 |  | -0.02623 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6741 | 0.001226 | -0.07966 | <.001 | 5.497 | <.001 |  |  | -0.1263 | <.001 |  | -0.03038 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | fit | 444325 | 21 | 0.6741 | 0.001259 | -0.07959 | <.001 | 5.496 | <.001 |  |  | -0.1215 | <.001 |  | -0.03093 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | fit | 444325 | 21 | 0.6741 | 0.001174 | -0.07984 | <.001 | 5.496 | <.001 |  |  | -0.04836 | <.001 |  | -0.02948 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | fit | 442220 | 21 | 0.6736 | 0.0006811 | -0.07877 | <.001 | 5.5 | <.001 | -0.03177 | 0.521 | -0.1451 | <.001 | -0.002547 | -0.02834 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | fit | 442220 | 21 | 0.6735 | 0.0005985 | -0.07938 | <.001 | 5.501 | <.001 | -0.0284 | 0.562 | -0.1183 | <.001 | -0.002277 | -0.02671 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | fit | 442220 | 21 | 0.6737 | 0.0008238 | -0.07842 | <.001 | 5.501 | <.001 | -0.03417 | 0.477 | -0.1285 | <.001 | -0.002739 | -0.03092 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | fit | 442220 | 21 | 0.6737 | 0.0008613 | -0.07835 | <.001 | 5.501 | <.001 | -0.03778 | 0.435 | -0.1242 | <.001 | -0.003029 | -0.03161 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | fit | 442220 | 21 | 0.6737 | 0.0007731 | -0.07868 | <.001 | 5.501 | <.001 | -0.03014 | 0.527 | -0.04916 | <.001 | -0.002416 | -0.02997 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 446985 | 21 | 0.6572 | 0 | -0.06724 | 0.001 | 5.084 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 442220 | 21 | 0.6571 | -0.0001018 | -0.06823 | <.001 | 5.083 | <.001 | 0.04786 | 0.346 |  |  | 0.003837 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | fit | 444325 | 21 | 0.6582 | 0.001002 | -0.06547 | 0.002 | 5.077 | <.001 |  |  | -0.134 | <.001 |  | -0.02615 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | fit | 444325 | 21 | 0.6581 | 0.0009085 | -0.0661 | 0.002 | 5.078 | <.001 |  |  | -0.1073 | <.001 |  | -0.02422 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6583 | 0.00108 | -0.06529 | 0.002 | 5.078 | <.001 |  |  | -0.1151 | <.001 |  | -0.02768 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | fit | 444325 | 21 | 0.6585 | 0.001253 | -0.06479 | 0.002 | 5.078 | <.001 |  |  | -0.1208 | <.001 |  | -0.03075 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | fit | 444325 | 21 | 0.6583 | 0.00108 | -0.06532 | 0.002 | 5.078 | <.001 |  |  | -0.04541 | <.001 |  | -0.02768 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | fit | 442220 | 21 | 0.6578 | 0.0005427 | -0.06292 | 0.002 | 5.08 | <.001 | -0.04232 | 0.402 | -0.1373 | <.001 | -0.003393 | -0.02681 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | fit | 442220 | 21 | 0.6577 | 0.0004475 | -0.06357 | 0.002 | 5.081 | <.001 | -0.03749 | 0.451 | -0.1098 | <.001 | -0.003006 | -0.0248 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | fit | 442220 | 21 | 0.6578 | 0.00062 | -0.06274 | 0.002 | 5.081 | <.001 | -0.0415 | 0.395 | -0.1175 | <.001 | -0.003327 | -0.02829 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | fit | 442220 | 21 | 0.658 | 0.0008016 | -0.06222 | 0.002 | 5.081 | <.001 | -0.05367 | 0.281 | -0.1244 | <.001 | -0.004303 | -0.03167 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | fit | 442220 | 21 | 0.6578 | 0.0006207 | -0.06284 | 0.002 | 5.081 | <.001 | -0.04051 | 0.405 | -0.04637 | <.001 | -0.003248 | -0.02827 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 446985 | 21 | 0.6743 | 0 | -0.08519 | <.001 | 2.196 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 442220 | 21 | 0.6743 | -6.875e-05 | -0.08687 | <.001 | 2.196 | <.001 | 0.02783 | 0.548 |  |  | 0.002231 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | fit | 444325 | 21 | 0.6753 | 0.0009426 | -0.08358 | <.001 | 2.193 | <.001 |  |  | -0.1284 | <.001 |  | -0.02507 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | fit | 444325 | 21 | 0.6753 | 0.0009097 | -0.08399 | <.001 | 2.194 | <.001 |  |  | -0.108 | <.001 |  | -0.02438 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6754 | 0.001009 | -0.08342 | <.001 | 2.194 | <.001 |  |  | -0.1099 | <.001 |  | -0.02645 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | fit | 444325 | 21 | 0.6754 | 0.001074 | -0.08323 | <.001 | 2.193 | <.001 |  |  | -0.1087 | <.001 |  | -0.02768 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | fit | 444325 | 21 | 0.6755 | 0.001115 | -0.08311 | <.001 | 2.194 | <.001 |  |  | -0.04665 | <.001 |  | -0.02843 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | fit | 442220 | 21 | 0.6749 | 0.0005484 | -0.08166 | <.001 | 2.195 | <.001 | -0.06041 | 0.187 | -0.1344 | <.001 | -0.004843 | -0.02624 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | fit | 442220 | 21 | 0.6749 | 0.0005159 | -0.08208 | <.001 | 2.195 | <.001 | -0.06023 | 0.183 | -0.1133 | <.001 | -0.004829 | -0.02558 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | fit | 442220 | 21 | 0.675 | 0.0006148 | -0.08151 | <.001 | 2.195 | <.001 | -0.05913 | 0.183 | -0.1144 | <.001 | -0.00474 | -0.02753 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | fit | 442220 | 21 | 0.675 | 0.0006858 | -0.08131 | <.001 | 2.195 | <.001 | -0.06492 | 0.147 | -0.1137 | <.001 | -0.005205 | -0.02895 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | fit | 442220 | 21 | 0.6751 | 0.0007265 | -0.08125 | <.001 | 2.195 | <.001 | -0.06489 | 0.143 | -0.04865 | <.001 | -0.005203 | -0.02966 |  |

## Hottest Takeaways For k1

- Baseline controls alone average R2=0.659 across target effort controls.
- Best context addition: Context size only with Words and Context words, delta R2=0.0015.
- Entropy appears in 30 fitted rows: 0 have p<.05 and 25 have negative coefficients.
- Context size appears in 50 fitted rows: 50 have p<.05 and 0 have positive coefficients.

## Saved Outputs

```text
results/context_predictor_permutations/context_predictor_model_summary.csv
results/context_predictor_permutations/context_predictor_distribution.csv
results/context_predictor_permutations/context_predictors_by_age.csv
figs/context_predictor_permutations/
```
