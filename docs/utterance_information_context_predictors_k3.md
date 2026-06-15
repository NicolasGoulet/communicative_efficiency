# Context Predictor Permutations: k3

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
| k3 | context_nb_words | Context words | 446985 | 13 | 12 | 16 | 21 | 122 |
| k3 | context_nb_morphemes | Context morphemes | 446985 | 15 | 14 | 19 | 24 | 135 |
| k3 | context_nb_syllables_cmu_or_pkg | Context syllables: CMU/pkg | 446985 | 15.8 | 15 | 20 | 25 | 150 |
| k3 | context_nb_syllables_pkg | Context syllables: pkg | 446985 | 16.7 | 15 | 21 | 27 | 165 |
| k3 | context_nb_phonemes | Context phonemes | 446985 | 39.8 | 37 | 50 | 64 | 381 |
| k3 | context_entropy_bits | Context entropy bits | 441413 | 6.34 | 6.38 | 6.92 | 7.42 | 11 |

![k3 context size distribution](../figs/context_predictor_permutations/k3_context_size_distribution.png)

![k3 context predictors by age](../figs/context_predictor_permutations/k3_context_predictors_by_age.png)

## Model Fit Overview

How to read: the R2 plot shows fit; the delta-R2 plot shows how much context
predictors add beyond age, target effort, and child identity.

![k3 R2 by model family](../figs/context_predictor_permutations/k3_model_family_r2.png)

## Coefficient Views

How to read: coefficients are in Mistral bits. Negative entropy coefficients
mean higher context entropy is associated with lower target utterance bits after
controls; positive context-size coefficients mean longer preceding context is
associated with higher target utterance bits after controls.

![k3 entropy coefficients](../figs/context_predictor_permutations/k3_entropy_coefficients.png)

![k3 context size coefficients](../figs/context_predictor_permutations/k3_context_size_coefficients.png)

![k3 age coefficients](../figs/context_predictor_permutations/k3_age_coefficients.png)

## Top Context Effects

| model_label | target_effort_label | context_size_label | r2_observed_fitted | delta_r2_vs_baseline | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Context size only | Words | Context words | 0.6272 | 0.001331 |  |  | -0.04386 | <.001 |  | -0.01684 |
| Context size only | Words | Context syllables: pkg | 0.6272 | 0.001268 |  |  | -0.02927 | <.001 |  | -0.01473 |
| Context size only | Words | Context phonemes | 0.6272 | 0.00126 |  |  | -0.01195 | <.001 |  | -0.01442 |
| Context size only | Words | Context morphemes | 0.6272 | 0.001253 |  |  | -0.03178 | <.001 |  | -0.01406 |
| Context size only | Syllables: CMU/pkg | Context syllables: pkg | 0.6471 | 0.001245 |  |  | -0.0287 | <.001 |  | -0.01444 |
| Context size only | Words | Context syllables: CMU/pkg | 0.6271 | 0.00124 |  |  | -0.02866 | <.001 |  | -0.01366 |
| Context size only | Syllables: CMU/pkg | Context syllables: CMU/pkg | 0.6471 | 0.001239 |  |  | -0.02985 | <.001 |  | -0.01423 |
| Context size only | Syllables: pkg | Context syllables: pkg | 0.6308 | 0.001219 |  |  | -0.0288 | <.001 |  | -0.01449 |
| Context size only | Syllables: CMU/pkg | Context phonemes | 0.6471 | 0.001218 |  |  | -0.01107 | <.001 |  | -0.01336 |
| Context size only | Phonemes | Context phonemes | 0.6455 | 0.001207 |  |  | -0.01139 | <.001 |  | -0.01374 |
| Context size only | Phonemes | Context syllables: pkg | 0.6455 | 0.001177 |  |  | -0.02487 | <.001 |  | -0.01252 |
| Context size only | Morphemes | Context words | 0.6142 | 0.001158 |  |  | -0.0398 | <.001 |  | -0.01528 |

## Full Model Summary

| model_label | estimator | library | covariance | target_effort_label | context_size_label | status | n_obs | n_children | r2_observed_fitted | delta_r2_vs_baseline | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 446985 | 21 | 0.6259 | 0 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 441413 | 21 | 0.6266 | 0.0006598 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  | -0.02654 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | fit | 444325 | 21 | 0.6272 | 0.001331 | -0.1239 | <.001 | 6.363 | <.001 |  |  | -0.04386 | <.001 |  | -0.01684 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | fit | 444325 | 21 | 0.6272 | 0.001253 | -0.1247 | <.001 | 6.363 | <.001 |  |  | -0.03178 | <.001 |  | -0.01406 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6271 | 0.00124 | -0.1246 | <.001 | 6.362 | <.001 |  |  | -0.02866 | <.001 |  | -0.01366 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | fit | 444325 | 21 | 0.6272 | 0.001268 | -0.1244 | <.001 | 6.362 | <.001 |  |  | -0.02927 | <.001 |  | -0.01473 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | fit | 444325 | 21 | 0.6272 | 0.00126 | -0.1245 | <.001 | 6.362 | <.001 |  |  | -0.01195 | <.001 |  | -0.01442 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | fit | 441413 | 21 | 0.6268 | 0.000908 | -0.123 | <.001 | 6.368 | <.001 | -0.4699 | <.001 | -0.0427 | <.001 | -0.02645 | -0.01644 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | fit | 441413 | 21 | 0.6267 | 0.000832 | -0.1239 | <.001 | 6.368 | <.001 | -0.4705 | <.001 | -0.0308 | <.001 | -0.02648 | -0.01367 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | fit | 441413 | 21 | 0.6267 | 0.0008124 | -0.1238 | <.001 | 6.367 | <.001 | -0.4681 | <.001 | -0.0271 | <.001 | -0.02634 | -0.01295 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | fit | 441413 | 21 | 0.6267 | 0.0008384 | -0.1236 | <.001 | 6.367 | <.001 | -0.4675 | <.001 | -0.02775 | <.001 | -0.02631 | -0.014 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | fit | 441413 | 21 | 0.6267 | 0.0008277 | -0.1237 | <.001 | 6.367 | <.001 | -0.4669 | <.001 | -0.01121 | <.001 | -0.02628 | -0.01356 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 446985 | 21 | 0.6131 | 0 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 441413 | 21 | 0.6136 | 0.0005117 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  | -0.02883 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | fit | 444325 | 21 | 0.6142 | 0.001158 | -0.1372 | <.001 | 5.484 | <.001 |  |  | -0.0398 | <.001 |  | -0.01528 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | fit | 444325 | 21 | 0.6142 | 0.001153 | -0.1375 | <.001 | 5.485 | <.001 |  |  | -0.03407 | <.001 |  | -0.01508 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6142 | 0.001096 | -0.1377 | <.001 | 5.484 | <.001 |  |  | -0.0271 | <.001 |  | -0.01291 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | fit | 444325 | 21 | 0.6142 | 0.001121 | -0.1375 | <.001 | 5.484 | <.001 |  |  | -0.02772 | <.001 |  | -0.01395 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | fit | 444325 | 21 | 0.6142 | 0.001136 | -0.1374 | <.001 | 5.484 | <.001 |  |  | -0.01204 | <.001 |  | -0.01452 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | fit | 441413 | 21 | 0.6138 | 0.0007137 | -0.1366 | <.001 | 5.488 | <.001 | -0.5108 | <.001 | -0.03853 | <.001 | -0.02875 | -0.01483 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | fit | 441413 | 21 | 0.6138 | 0.0007092 | -0.1369 | <.001 | 5.489 | <.001 | -0.5111 | <.001 | -0.03298 | <.001 | -0.02876 | -0.01464 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | fit | 441413 | 21 | 0.6137 | 0.0006458 | -0.1372 | <.001 | 5.488 | <.001 | -0.509 | <.001 | -0.0254 | <.001 | -0.02865 | -0.01214 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | fit | 441413 | 21 | 0.6138 | 0.0006689 | -0.137 | <.001 | 5.488 | <.001 | -0.5084 | <.001 | -0.02603 | <.001 | -0.02861 | -0.01314 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | fit | 441413 | 21 | 0.6138 | 0.0006798 | -0.137 | <.001 | 5.488 | <.001 | -0.5076 | <.001 | -0.01122 | <.001 | -0.02857 | -0.01357 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 446985 | 21 | 0.6459 | 0 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 441413 | 21 | 0.6468 | 0.0008711 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  | -0.03038 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | fit | 444325 | 21 | 0.647 | 0.001156 | -0.06578 | 0.015 | 5.231 | <.001 |  |  | -0.02728 | <.001 |  | -0.01047 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | fit | 444325 | 21 | 0.647 | 0.001128 | -0.0663 | 0.014 | 5.231 | <.001 |  |  | -0.02003 | 0.001 |  | -0.008864 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6471 | 0.001239 | -0.06497 | 0.016 | 5.232 | <.001 |  |  | -0.02985 | <.001 |  | -0.01423 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | fit | 444325 | 21 | 0.6471 | 0.001245 | -0.06495 | 0.016 | 5.232 | <.001 |  |  | -0.0287 | <.001 |  | -0.01444 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | fit | 444325 | 21 | 0.6471 | 0.001218 | -0.0652 | 0.016 | 5.231 | <.001 |  |  | -0.01107 | <.001 |  | -0.01336 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | fit | 441413 | 21 | 0.6469 | 0.0009654 | -0.06203 | 0.016 | 5.234 | <.001 | -0.5388 | <.001 | -0.02631 | <.001 | -0.03032 | -0.01013 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | fit | 441413 | 21 | 0.6468 | 0.0009381 | -0.06254 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 | -0.01921 | 0.002 | -0.03034 | -0.008522 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | fit | 441413 | 21 | 0.6469 | 0.001039 | -0.06126 | 0.018 | 5.235 | <.001 | -0.5362 | <.001 | -0.02838 | <.001 | -0.03018 | -0.01357 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | fit | 441413 | 21 | 0.6469 | 0.001043 | -0.06127 | 0.018 | 5.235 | <.001 | -0.5358 | <.001 | -0.02719 | <.001 | -0.03016 | -0.01372 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | fit | 441413 | 21 | 0.6469 | 0.001014 | -0.06157 | 0.017 | 5.235 | <.001 | -0.5355 | <.001 | -0.01032 | <.001 | -0.03014 | -0.01249 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 446985 | 21 | 0.6296 | 0 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 441413 | 21 | 0.6304 | 0.0008447 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  | -0.03045 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | fit | 444325 | 21 | 0.6307 | 0.001105 | -0.05128 | 0.039 | 4.826 | <.001 |  |  | -0.02392 | <.001 |  | -0.009183 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | fit | 444325 | 21 | 0.6307 | 0.001076 | -0.05185 | 0.037 | 4.826 | <.001 |  |  | -0.0163 | 0.005 |  | -0.007212 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6307 | 0.001152 | -0.05073 | 0.042 | 4.827 | <.001 |  |  | -0.0245 | <.001 |  | -0.01168 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | fit | 444325 | 21 | 0.6308 | 0.001219 | -0.05014 | 0.044 | 4.827 | <.001 |  |  | -0.0288 | <.001 |  | -0.01449 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | fit | 444325 | 21 | 0.6307 | 0.001155 | -0.05074 | 0.042 | 4.826 | <.001 |  |  | -0.009772 | <.001 |  | -0.01179 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | fit | 441413 | 21 | 0.6305 | 0.0009156 | -0.04591 | 0.045 | 4.828 | <.001 | -0.5402 | <.001 | -0.02282 | <.001 | -0.0304 | -0.008785 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | fit | 441413 | 21 | 0.6305 | 0.0008876 | -0.04649 | 0.043 | 4.828 | <.001 | -0.5405 | <.001 | -0.01537 | 0.006 | -0.03042 | -0.006821 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | fit | 441413 | 21 | 0.6305 | 0.0009544 | -0.04541 | 0.049 | 4.829 | <.001 | -0.5381 | <.001 | -0.02297 | <.001 | -0.03028 | -0.01098 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | fit | 441413 | 21 | 0.6306 | 0.001017 | -0.04483 | 0.052 | 4.829 | <.001 | -0.537 | <.001 | -0.02722 | <.001 | -0.03022 | -0.01374 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | fit | 441413 | 21 | 0.6305 | 0.0009524 | -0.0455 | 0.048 | 4.829 | <.001 | -0.5373 | <.001 | -0.00898 | <.001 | -0.03024 | -0.01087 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 446985 | 21 | 0.6443 | 0 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 441413 | 21 | 0.6453 | 0.0009737 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  | -0.03272 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | fit | 444325 | 21 | 0.6455 | 0.001112 | -0.06763 | 0.011 | 2.082 | <.001 |  |  | -0.02389 | <.001 |  | -0.00917 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | fit | 444325 | 21 | 0.6454 | 0.0011 | -0.06794 | 0.011 | 2.082 | <.001 |  |  | -0.01915 | 0.002 |  | -0.008473 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6455 | 0.001155 | -0.06712 | 0.012 | 2.082 | <.001 |  |  | -0.02417 | <.001 |  | -0.01152 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | fit | 444325 | 21 | 0.6455 | 0.001177 | -0.06692 | 0.013 | 2.082 | <.001 |  |  | -0.02487 | <.001 |  | -0.01252 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | fit | 444325 | 21 | 0.6455 | 0.001207 | -0.06667 | 0.013 | 2.082 | <.001 |  |  | -0.01139 | <.001 |  | -0.01374 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | fit | 441413 | 21 | 0.6454 | 0.001045 | -0.06305 | 0.015 | 2.084 | <.001 | -0.5805 | <.001 | -0.02283 | <.001 | -0.03267 | -0.008788 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | fit | 441413 | 21 | 0.6454 | 0.001034 | -0.06335 | 0.014 | 2.084 | <.001 | -0.5808 | <.001 | -0.01825 | 0.003 | -0.03269 | -0.0081 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | fit | 441413 | 21 | 0.6454 | 0.00108 | -0.06259 | 0.016 | 2.084 | <.001 | -0.5785 | <.001 | -0.02261 | <.001 | -0.03256 | -0.01081 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | fit | 441413 | 21 | 0.6454 | 0.001099 | -0.06242 | 0.016 | 2.084 | <.001 | -0.578 | <.001 | -0.02327 | <.001 | -0.03253 | -0.01175 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | fit | 441413 | 21 | 0.6455 | 0.001124 | -0.06221 | 0.016 | 2.084 | <.001 | -0.577 | <.001 | -0.0106 | <.001 | -0.03248 | -0.01282 |  |

## Hottest Takeaways For k3

- Baseline controls alone average R2=0.632 across target effort controls.
- Best context addition: Context size only with Words and Context words, delta R2=0.0013.
- Entropy appears in 30 fitted rows: 30 have p<.05 and 30 have negative coefficients.
- Context size appears in 50 fitted rows: 50 have p<.05 and 0 have positive coefficients.

## Saved Outputs

```text
results/context_predictor_permutations/context_predictor_model_summary.csv
results/context_predictor_permutations/context_predictor_distribution.csv
results/context_predictor_permutations/context_predictors_by_age.csv
figs/context_predictor_permutations/
```
