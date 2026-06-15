# Context Predictor Permutations: K0-K3 Comparison

This report compares the four scoring-context settings. It does not replace the
older M1-M6 reports; it is a new context-predictor sensitivity report.

## How To Read The Comparison

- `k0` is the no-context scorer condition. It can fit the baseline controls but
  cannot fit context entropy or context-size models because there is no context.
- `k1`, `k2`, and `k3` use increasingly larger preceding caretaker context
  windows.
- `mean_delta_r2` is the average added in-sample R2 relative to the no-context
  predictor baseline with the same target effort control.
- These are not held-out predictive scores; they are fit diagnostics and
  inferential screens for the current model family.

Implementation for all rows in this report:

```text
Estimator: linear OLS regression
Library: statsmodels.formula.api.ols
Uncertainty: child-cluster robust standard errors, cov_type='cluster'
Cluster unit: child_id
```

So these are linear child-clustered OLS screens, not GEE/GLM/mixed-model fits.

## Fit Summary By K

| context_k | model_label | fitted_rows | mean_r2 | mean_delta_r2 | significant_entropy | significant_context_size |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | Baseline controls | 5 | 0.736 | 0 | 0 | 0 |
| k1 | Baseline controls | 5 | 0.6586 | 0 | 0 | 0 |
| k1 | Context size only | 25 | 0.6597 | 0.001151 | 0 | 25 |
| k1 | Entropy only | 5 | 0.6585 | -0.0001005 | 0 | 0 |
| k1 | Entropy plus context size | 25 | 0.6593 | 0.0007084 | 0 | 25 |
| k2 | Baseline controls | 5 | 0.6408 | 0 | 0 | 0 |
| k2 | Context size only | 25 | 0.6417 | 0.0009782 | 0 | 25 |
| k2 | Entropy only | 5 | 0.6413 | 0.0005263 | 5 | 0 |
| k2 | Entropy plus context size | 25 | 0.6415 | 0.0007674 | 25 | 25 |
| k3 | Baseline controls | 5 | 0.6318 | 0 | 0 | 0 |
| k3 | Context size only | 25 | 0.6329 | 0.001178 | 0 | 25 |
| k3 | Entropy only | 5 | 0.6325 | 0.0007722 | 5 | 0 |
| k3 | Entropy plus context size | 25 | 0.6327 | 0.0009097 | 25 | 25 |

## Context Predictor Magnitudes By K

| context_k | measure_col | measure_label | rows | mean | median | p75 | p90 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | context_nb_words | Context words | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_nb_phonemes | Context phonemes | 446985 | 0 | 0 | 0 | 0 | 0 |
| k0 | context_entropy_bits | Context entropy bits | 0 |  |  |  |  |  |
| k1 | context_nb_words | Context words | 446985 | 4.46 | 4 | 6 | 9 | 109 |
| k1 | context_nb_phonemes | Context phonemes | 446985 | 13.7 | 12 | 19 | 26 | 326 |
| k1 | context_entropy_bits | Context entropy bits | 442220 | 5.71 | 5.67 | 6.49 | 7.32 | 11.2 |
| k2 | context_nb_words | Context words | 446985 | 8.74 | 8 | 11 | 15 | 114 |
| k2 | context_nb_phonemes | Context phonemes | 446985 | 26.8 | 24 | 34 | 46 | 341 |
| k2 | context_entropy_bits | Context entropy bits | 441461 | 6 | 6 | 6.64 | 7.25 | 11.3 |
| k3 | context_nb_words | Context words | 446985 | 13 | 12 | 16 | 21 | 122 |
| k3 | context_nb_phonemes | Context phonemes | 446985 | 39.8 | 37 | 50 | 64 | 381 |
| k3 | context_entropy_bits | Context entropy bits | 441413 | 6.34 | 6.38 | 6.92 | 7.42 | 11 |

## Cross-K Plots

How to read: the first plot asks whether adding context predictors increases
fit differently for k1/k2/k3. The second plot asks whether entropy and size
coefficients change as the context window grows. The third plot confirms that
context windows mechanically grow from k1 to k3.

![R2 comparison](../figs/context_predictor_permutations/compare_k_model_family_r2.png)

![Coefficient comparison](../figs/context_predictor_permutations/compare_k_context_coefficients.png)

![Context predictor distribution comparison](../figs/context_predictor_permutations/compare_k_context_predictor_distributions.png)

## Saved Outputs

```text
results/context_predictor_permutations/context_predictor_model_summary.csv
results/context_predictor_permutations/context_predictor_distribution.csv
results/context_predictor_permutations/context_predictors_by_age.csv
figs/context_predictor_permutations/
```
