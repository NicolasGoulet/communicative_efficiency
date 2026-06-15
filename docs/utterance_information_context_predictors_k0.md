# Context Predictor Permutations: k0

This internal report is separate from the previous M1-M6 reports. It asks
whether context predictors explain total child utterance information.

`k0` has no preceding context by definition, so entropy and context-size predictors are unavailable.

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
| k0 | context_nb_words | Context words | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_nb_morphemes | Context morphemes | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_nb_syllables_cmu_or_pkg | Context syllables: CMU/pkg | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_nb_syllables_pkg | Context syllables: pkg | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_nb_phonemes | Context phonemes | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_entropy_bits | Context entropy bits | 0 |  |  |  |  |  |

![k0 context size distribution](../figs/context_predictor_permutations/k0_context_size_distribution.png)

![k0 context predictors by age](../figs/context_predictor_permutations/k0_context_predictors_by_age.png)

## Model Fit Overview

How to read: the R2 plot shows fit; the delta-R2 plot shows how much context
predictors add beyond age, target effort, and child identity.

![k0 R2 by model family](../figs/context_predictor_permutations/k0_model_family_r2.png)

## Coefficient Views

How to read: coefficients are in Mistral bits. Negative entropy coefficients
mean higher context entropy is associated with lower target utterance bits after
controls; positive context-size coefficients mean longer preceding context is
associated with higher target utterance bits after controls.

![k0 entropy coefficients](../figs/context_predictor_permutations/k0_entropy_coefficients.png)

![k0 context size coefficients](../figs/context_predictor_permutations/k0_context_size_coefficients.png)

![k0 age coefficients](../figs/context_predictor_permutations/k0_age_coefficients.png)

## Top Context Effects

_No rows._

## Full Model Summary

| model_label | estimator | library | covariance | target_effort_label | context_size_label | status | n_obs | n_children | r2_observed_fitted | delta_r2_vs_baseline | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | std_context_entropy_beta | std_context_size_beta | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | fit | 446985 | 21 | 0.7252 | 0 | -0.1582 | <.001 | 7.127 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | No context-size predictor | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Words | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | fit | 446985 | 21 | 0.7204 | 0 | -0.1784 | <.001 | 6.195 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | No context-size predictor | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Morphemes | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | fit | 446985 | 21 | 0.7461 | 0 | -0.0907 | 0.003 | 5.848 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | No context-size predictor | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: CMU/pkg | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | fit | 446985 | 21 | 0.7303 | 0 | -0.07571 | 0.009 | 5.411 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | No context-size predictor | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Syllables: pkg | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Baseline controls | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | fit | 446985 | 21 | 0.7578 | 0 | -0.09847 | 0.001 | 2.352 | <.001 |  |  |  |  |  |  |  |
| Entropy only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | No context-size predictor | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Context size only | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context words | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context morphemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: CMU/pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context syllables: pkg | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |
| Entropy plus context size | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | Phonemes | Context phonemes | skipped | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | no complete rows |

## Hottest Takeaways For k0

- Baseline controls alone average R2=0.736 across target effort controls.

## Saved Outputs

```text
results/context_predictor_permutations/context_predictor_model_summary.csv
results/context_predictor_permutations/context_predictor_distribution.csv
results/context_predictor_permutations/context_predictors_by_age.csv
figs/context_predictor_permutations/
```
