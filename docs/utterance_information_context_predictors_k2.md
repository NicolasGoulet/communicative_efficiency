# Context Predictor Permutations: k2

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
| k2 | context_nb_words | Context words | 446985 | 8.74 | 8 | 11 | 15 | 114 |
| k2 | context_nb_morphemes | Context morphemes | 446985 | 10.1 | 9 | 13 | 17 | 122 |
| k2 | context_nb_syllables_cmu_or_pkg | Context syllables: CMU/pkg | 446985 | 10.6 | 10 | 14 | 18 | 131 |
| k2 | context_nb_syllables_pkg | Context syllables: pkg | 446985 | 11.2 | 10 | 14 | 19 | 138 |
| k2 | context_nb_phonemes | Context phonemes | 446985 | 26.8 | 24 | 34 | 46 | 341 |
| k2 | context_entropy_bits | Context entropy bits | 441461 | 6 | 6 | 6.64 | 7.25 | 11.3 |

![k2 context size distribution](../figs/context_predictor_permutations/k2_context_size_distribution.png)

![k2 context predictors by age](../figs/context_predictor_permutations/k2_context_predictors_by_age.png)

## Model Fit Overview

How to read: the R2 plot shows fit; the delta-R2 plot shows how much context
predictors add beyond age, target effort, and child identity.

![k2 R2 by model family](../figs/context_predictor_permutations/k2_model_family_r2.png)

## Coefficient Views

How to read: coefficients are in Mistral bits. Negative entropy coefficients
mean higher context entropy is associated with lower target utterance bits after
controls; positive context-size coefficients mean longer preceding context is
associated with higher target utterance bits after controls.

![k2 entropy coefficients](../figs/context_predictor_permutations/k2_entropy_coefficients.png)

![k2 context size coefficients](../figs/context_predictor_permutations/k2_context_size_coefficients.png)

![k2 age coefficients](../figs/context_predictor_permutations/k2_age_coefficients.png)

## Top Context Effects

| model_label | target_effort_label | context_size_label | r2_observed_fitted | delta_r2_vs_baseline | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Context size only | Words | Context words | 0.635 | 0.001178 |  |  | -0.07164 | <.001 |  | -0.02112 |
| Context size only | Words | Context syllables: pkg | 0.6349 | 0.001094 |  |  | -0.04905 | <.001 |  | -0.01894 |
| Context size only | Words | Context phonemes | 0.6349 | 0.001087 |  |  | -0.02024 | <.001 |  | -0.01873 |
| Context size only | Words | Context morphemes | 0.6349 | 0.001068 |  |  | -0.0532 | <.001 |  | -0.01813 |
| Context size only | Words | Context syllables: CMU/pkg | 0.6349 | 0.001061 |  |  | -0.04926 | <.001 |  | -0.01798 |
| Context size only | Syllables: CMU/pkg | Context syllables: pkg | 0.6561 | 0.001044 |  |  | -0.04663 | <.001 |  | -0.01801 |
| Context size only | Syllables: CMU/pkg | Context syllables: CMU/pkg | 0.6561 | 0.001039 |  |  | -0.04898 | <.001 |  | -0.01788 |
| Context size only | Syllables: pkg | Context syllables: pkg | 0.64 | 0.001031 |  |  | -0.04671 | <.001 |  | -0.01804 |
| Context size only | Syllables: CMU/pkg | Context phonemes | 0.6561 | 0.00101 |  |  | -0.01835 | <.001 |  | -0.01697 |
| Context size only | Morphemes | Context words | 0.6227 | 0.0009996 |  |  | -0.0655 | <.001 |  | -0.01931 |
| Context size only | Phonemes | Context phonemes | 0.6552 | 0.0009952 |  |  | -0.01841 | <.001 |  | -0.01703 |
| Context size only | Morphemes | Context morphemes | 0.6227 | 0.0009866 |  |  | -0.05554 | <.001 |  | -0.01892 |

## Full Model Summary

| model_label | estimator | library | covariance | target_effort_label | context_size_label | status | n_obs | n_children | r2_observed_fitted | delta_r2_vs_baseline | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 446985 | 21 | 0.6338 | 0 | -0.1287 | <.001 | 6.468 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 441461 | 21 | 0.6343 | 0.0004413 | -0.1318 | <.001 | 6.47 | <.001 | -0.4107 | <.001 |  |  | -0.02595 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | fit | 444325 | 21 | 0.635 | 0.001178 | -0.1289 | <.001 | 6.464 | <.001 |  |  | -0.07164 | <.001 |  | -0.02112 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | fit | 444325 | 21 | 0.6349 | 0.001068 | -0.1298 | <.001 | 6.464 | <.001 |  |  | -0.0532 | <.001 |  | -0.01813 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6349 | 0.001061 | -0.1296 | <.001 | 6.464 | <.001 |  |  | -0.04926 | <.001 |  | -0.01798 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | fit | 444325 | 21 | 0.6349 | 0.001094 | -0.1295 | <.001 | 6.463 | <.001 |  |  | -0.04905 | <.001 |  | -0.01894 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | fit | 444325 | 21 | 0.6349 | 0.001087 | -0.1295 | <.001 | 6.463 | <.001 |  |  | -0.02024 | <.001 |  | -0.01873 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | fit | 441461 | 21 | 0.6347 | 0.0008435 | -0.1273 | <.001 | 6.47 | <.001 | -0.4087 | <.001 | -0.06994 | <.001 | -0.02583 | -0.02066 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | fit | 441461 | 21 | 0.6346 | 0.0007412 | -0.1282 | <.001 | 6.471 | <.001 | -0.4104 | <.001 | -0.05217 | <.001 | -0.02593 | -0.01782 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | fit | 441461 | 21 | 0.6346 | 0.0007227 | -0.1281 | <.001 | 6.47 | <.001 | -0.4069 | <.001 | -0.04739 | <.001 | -0.02572 | -0.01733 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | fit | 441461 | 21 | 0.6346 | 0.0007564 | -0.1279 | <.001 | 6.47 | <.001 | -0.4068 | <.001 | -0.04737 | <.001 | -0.02571 | -0.01833 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | fit | 441461 | 21 | 0.6346 | 0.0007449 | -0.128 | <.001 | 6.47 | <.001 | -0.4059 | <.001 | -0.0194 | <.001 | -0.02565 | -0.01799 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 446985 | 21 | 0.6217 | 0 | -0.1425 | <.001 | 5.581 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 441461 | 21 | 0.622 | 0.0002391 | -0.1458 | <.001 | 5.582 | <.001 | -0.4256 | <.001 |  |  | -0.0269 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | fit | 444325 | 21 | 0.6227 | 0.0009996 | -0.143 | <.001 | 5.576 | <.001 |  |  | -0.0655 | <.001 |  | -0.01931 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | fit | 444325 | 21 | 0.6227 | 0.0009866 | -0.1433 | <.001 | 5.577 | <.001 |  |  | -0.05554 | <.001 |  | -0.01892 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6226 | 0.0009202 | -0.1435 | <.001 | 5.576 | <.001 |  |  | -0.04668 | <.001 |  | -0.01704 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | fit | 444325 | 21 | 0.6227 | 0.000951 | -0.1433 | <.001 | 5.576 | <.001 |  |  | -0.04652 | <.001 |  | -0.01797 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | fit | 444325 | 21 | 0.6227 | 0.0009719 | -0.1432 | <.001 | 5.576 | <.001 |  |  | -0.02007 | <.001 |  | -0.01857 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | fit | 441461 | 21 | 0.6223 | 0.000572 | -0.1417 | <.001 | 5.581 | <.001 | -0.4238 | <.001 | -0.06363 | <.001 | -0.02678 | -0.01879 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | fit | 441461 | 21 | 0.6223 | 0.000565 | -0.142 | <.001 | 5.582 | <.001 | -0.4253 | <.001 | -0.05438 | <.001 | -0.02688 | -0.01857 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | fit | 441461 | 21 | 0.6222 | 0.0004892 | -0.1423 | <.001 | 5.581 | <.001 | -0.4221 | <.001 | -0.04468 | <.001 | -0.02667 | -0.01634 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | fit | 441461 | 21 | 0.6222 | 0.0005194 | -0.1421 | <.001 | 5.581 | <.001 | -0.4219 | <.001 | -0.04468 | <.001 | -0.02666 | -0.01729 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | fit | 441461 | 21 | 0.6222 | 0.0005349 | -0.142 | <.001 | 5.581 | <.001 | -0.4209 | <.001 | -0.01915 | <.001 | -0.0266 | -0.01776 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 446985 | 21 | 0.6551 | 0 | -0.06903 | 0.007 | 5.323 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 441461 | 21 | 0.6557 | 0.0006248 | -0.06891 | 0.006 | 5.324 | <.001 | -0.4558 | <.001 |  |  | -0.0288 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | fit | 444325 | 21 | 0.656 | 0.0009273 | -0.07034 | 0.006 | 5.318 | <.001 |  |  | -0.04782 | <.001 |  | -0.01409 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | fit | 444325 | 21 | 0.656 | 0.000884 | -0.0709 | 0.006 | 5.319 | <.001 |  |  | -0.03623 | <.001 |  | -0.01235 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6561 | 0.001039 | -0.06963 | 0.007 | 5.319 | <.001 |  |  | -0.04898 | <.001 |  | -0.01788 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | fit | 444325 | 21 | 0.6561 | 0.001044 | -0.06962 | 0.007 | 5.319 | <.001 |  |  | -0.04663 | <.001 |  | -0.01801 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | fit | 444325 | 21 | 0.6561 | 0.00101 | -0.06983 | 0.007 | 5.319 | <.001 |  |  | -0.01835 | <.001 |  | -0.01697 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | fit | 441461 | 21 | 0.6559 | 0.0007997 | -0.06588 | 0.008 | 5.323 | <.001 | -0.4545 | <.001 | -0.04612 | <.001 | -0.02872 | -0.01362 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | fit | 441461 | 21 | 0.6559 | 0.0007613 | -0.0664 | 0.007 | 5.323 | <.001 | -0.4556 | <.001 | -0.0352 | <.001 | -0.02879 | -0.01202 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | fit | 441461 | 21 | 0.656 | 0.0009026 | -0.06519 | 0.009 | 5.324 | <.001 | -0.4521 | <.001 | -0.04709 | <.001 | -0.02857 | -0.01723 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | fit | 441461 | 21 | 0.656 | 0.0009078 | -0.06519 | 0.009 | 5.323 | <.001 | -0.4521 | <.001 | -0.04489 | <.001 | -0.02857 | -0.01738 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | fit | 441461 | 21 | 0.656 | 0.0008703 | -0.06548 | 0.008 | 5.323 | <.001 | -0.4515 | <.001 | -0.01745 | <.001 | -0.02853 | -0.01618 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 446985 | 21 | 0.639 | 0 | -0.0542 | 0.021 | 4.914 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 441461 | 21 | 0.6396 | 0.000602 | -0.05248 | 0.017 | 4.913 | <.001 | -0.4543 | <.001 |  |  | -0.02871 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | fit | 444325 | 21 | 0.6398 | 0.0008781 | -0.05582 | 0.018 | 4.909 | <.001 |  |  | -0.04306 | <.001 |  | -0.01269 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | fit | 444325 | 21 | 0.6398 | 0.0008324 | -0.05643 | 0.017 | 4.909 | <.001 |  |  | -0.03109 | <.001 |  | -0.0106 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6399 | 0.0009449 | -0.05534 | 0.019 | 4.909 | <.001 |  |  | -0.04186 | <.001 |  | -0.01528 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | fit | 444325 | 21 | 0.64 | 0.001031 | -0.05479 | 0.021 | 4.909 | <.001 |  |  | -0.04671 | <.001 |  | -0.01804 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | fit | 444325 | 21 | 0.6399 | 0.0009473 | -0.05534 | 0.019 | 4.909 | <.001 |  |  | -0.01658 | <.001 |  | -0.01534 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | fit | 441461 | 21 | 0.6397 | 0.0007414 | -0.04975 | 0.023 | 4.912 | <.001 | -0.4531 | <.001 | -0.04118 | <.001 | -0.02863 | -0.01216 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | fit | 441461 | 21 | 0.6397 | 0.0007005 | -0.05032 | 0.022 | 4.913 | <.001 | -0.4541 | <.001 | -0.0299 | <.001 | -0.02869 | -0.01021 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | fit | 441461 | 21 | 0.6398 | 0.0008012 | -0.04929 | 0.025 | 4.913 | <.001 | -0.4511 | <.001 | -0.03987 | <.001 | -0.02851 | -0.01459 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | fit | 441461 | 21 | 0.6399 | 0.0008847 | -0.04875 | 0.027 | 4.913 | <.001 | -0.4506 | <.001 | -0.04487 | <.001 | -0.02847 | -0.01737 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | fit | 441461 | 21 | 0.6398 | 0.0007988 | -0.04938 | 0.025 | 4.913 | <.001 | -0.4504 | <.001 | -0.01562 | <.001 | -0.02846 | -0.01448 |  |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 446985 | 21 | 0.6542 | 0 | -0.07096 | 0.005 | 2.12 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 441461 | 21 | 0.6549 | 0.0007242 | -0.06995 | 0.006 | 2.12 | <.001 | -0.4942 | <.001 |  |  | -0.03123 |  |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | fit | 444325 | 21 | 0.655 | 0.0008686 | -0.07258 | 0.005 | 2.118 | <.001 |  |  | -0.04218 | <.001 |  | -0.01243 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | fit | 444325 | 21 | 0.655 | 0.0008507 | -0.07292 | 0.005 | 2.118 | <.001 |  |  | -0.03414 | <.001 |  | -0.01163 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | fit | 444325 | 21 | 0.6551 | 0.0009288 | -0.07213 | 0.005 | 2.118 | <.001 |  |  | -0.04062 | <.001 |  | -0.01483 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | fit | 444325 | 21 | 0.6551 | 0.0009555 | -0.07195 | 0.005 | 2.118 | <.001 |  |  | -0.04078 | <.001 |  | -0.01575 |  |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | fit | 444325 | 21 | 0.6552 | 0.0009952 | -0.0717 | 0.005 | 2.118 | <.001 |  |  | -0.01841 | <.001 |  | -0.01703 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | fit | 441461 | 21 | 0.655 | 0.0008593 | -0.06726 | 0.007 | 2.12 | <.001 | -0.493 | <.001 | -0.04053 | <.001 | -0.03115 | -0.01197 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | fit | 441461 | 21 | 0.655 | 0.0008456 | -0.06757 | 0.007 | 2.12 | <.001 | -0.4939 | <.001 | -0.03319 | <.001 | -0.03121 | -0.01133 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | fit | 441461 | 21 | 0.6551 | 0.0009123 | -0.06684 | 0.008 | 2.12 | <.001 | -0.4911 | <.001 | -0.03875 | <.001 | -0.03103 | -0.01417 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | fit | 441461 | 21 | 0.6551 | 0.0009383 | -0.06668 | 0.008 | 2.12 | <.001 | -0.4909 | <.001 | -0.03905 | <.001 | -0.03102 | -0.01511 |  |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | fit | 441461 | 21 | 0.6551 | 0.0009716 | -0.0665 | 0.008 | 2.12 | <.001 | -0.4898 | <.001 | -0.01751 | <.001 | -0.03096 | -0.01624 |  |

## Hottest Takeaways For k2

- Baseline controls alone average R2=0.641 across target effort controls.
- Best context addition: Context size only with Words and Context words, delta R2=0.0012.
- Entropy appears in 30 fitted rows: 30 have p<.05 and 30 have negative coefficients.
- Context size appears in 50 fitted rows: 50 have p<.05 and 0 have positive coefficients.

## Saved Outputs

```text
results/context_predictor_permutations/context_predictor_model_summary.csv
results/context_predictor_permutations/context_predictor_distribution.csv
results/context_predictor_permutations/context_predictors_by_age.csv
figs/context_predictor_permutations/
```
