# M1-M6 Context Fixed-Effort Atlas

This is the long internal report that repeats the full M1-M6 model ladder across k0/k1/k2/k3 and fixed-effort slices.
It is intentionally exhaustive so pieces can later be selected for the supervisor-facing report.

## Implementation

- Estimator: linear ordinary least squares regression.
- Library: `statsmodels.formula.api.ols`.
- Uncertainty: child-cluster robust standard errors with `cov_type='cluster'` and `child_id` as the cluster.
- Outcome: `sum_bits`, the Mistral total information for the target utterance under the current scoring context.
- Fixed slices: the model is fit on all eligible rows; fixed effort values only define the plotted prediction lines.
- Context size: when included, it is matched to the target effort unit, so target words use context words, target phonemes use context phonemes, etc.

## Model Formulas

How to read: `target_effort_c`, `context_entropy_c`, and `context_size_c` are centered numeric predictors. `C(child_id)` controls child identity. Models with context predictors are not fit for `k0` because `k0` has no context.

| model_id | model_family | model_label | context_variant | question | formula |
| --- | --- | --- | --- | --- | --- |
| M1 | M1 | Pooled age and effort | none | Pooling all children, does age predict total bits after controlling target utterance effort? | sum_bits ~ age_c + target_effort_c |
| M2 | M2 | Age and effort with child identity | none | Does the developmental age effect remain after child identity is controlled? | sum_bits ~ age_c + target_effort_c + C(child_id) |
| M3 | M3 | Age by effort | none | Does the age trend change across target-effort values? | sum_bits ~ age_c * target_effort_c + C(child_id) |
| M4E | M4 | Context entropy added | entropy | Does entropy add predictive information beyond age, target effort, and child identity? | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |
| M4S | M4 | Matched context size added | context_size | Does matched context-window size add predictive information beyond age, target effort, and child identity? | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |
| M4ES | M4 | Entropy plus matched context size | entropy_plus_size | Do entropy and matched context size explain distinct variance when entered together? | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |
| M5E | M5 | Age by context entropy | entropy | Does the entropy association change over developmental time? | sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id) |
| M5S | M5 | Age by matched context size | context_size | Does the matched context-size association change over developmental time? | sum_bits ~ age_c * context_size_c + target_effort_c + C(child_id) |
| M5ES | M5 | Age by entropy and size | entropy_plus_size | Do entropy and context-size age interactions both contribute? | sum_bits ~ age_c * context_entropy_c + age_c * context_size_c + target_effort_c + C(child_id) |
| M6E | M6 | Effort and entropy interactions | entropy | Do age, target effort, and entropy interact when predicting total bits? | sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id) |
| M6S | M6 | Effort and context-size interactions | context_size | Do age, target effort, and matched context size interact when predicting total bits? | sum_bits ~ age_c * target_effort_c + age_c * context_size_c + target_effort_c * context_size_c + C(child_id) |
| M6ES | M6 | Interaction-rich entropy and size model | entropy_plus_size | Do the interaction patterns survive when both context entropy and context size are present? | sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + age_c * context_size_c + target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id) |

## Fixed-Effort Slice Definitions

Words and morphemes use exact 1-4, 5-8, and 9-12 panels. Syllables and phonemes use the 12 most frequent exact values split into three ordered representative panels.

| context_k | effort_label | atlas_bin | fixed_values | support_rows | support_children | rule |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | Words | 1-4 | 1, 2, 3, 4 | 381557 | 21 | Exact requested fixed values 1-4. |
| k0 | Words | 5-8 | 5, 6, 7, 8 | 58263 | 21 | Exact requested fixed values 5-8. |
| k0 | Words | 9-12 | 9, 10, 11, 12 | 5737 | 21 | Exact requested fixed values 9-12. |
| k0 | Morphemes | 1-4 | 1, 2, 3, 4 | 357854 | 21 | Exact requested fixed values 1-4. |
| k0 | Morphemes | 5-8 | 5, 6, 7, 8 | 77357 | 21 | Exact requested fixed values 5-8. |
| k0 | Morphemes | 9-12 | 9, 10, 11, 12 | 9409 | 21 | Exact requested fixed values 9-12. |
| k0 | Syllables: CMU/pkg | 1-4 representative ranks | 1, 2, 3, 4 | 344589 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Syllables: CMU/pkg | 5-8 representative ranks | 5, 6, 7, 8 | 86468 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Syllables: CMU/pkg | 9-12 representative ranks | 9, 10, 11, 12 | 12662 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Syllables: pkg | 1-4 representative ranks | 1, 2, 3, 4 | 329972 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Syllables: pkg | 5-8 representative ranks | 5, 6, 7, 8 | 97554 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Syllables: pkg | 9-12 representative ranks | 9, 10, 11, 12 | 15357 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Phonemes | 1-4 representative ranks | 2, 3, 4, 5 | 175070 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Phonemes | 5-8 representative ranks | 6, 7, 8, 9 | 118913 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k0 | Phonemes | 9-12 representative ranks | 10, 11, 12, 13 | 73995 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Words | 1-4 | 1, 2, 3, 4 | 381557 | 21 | Exact requested fixed values 1-4. |
| k1 | Words | 5-8 | 5, 6, 7, 8 | 58263 | 21 | Exact requested fixed values 5-8. |
| k1 | Words | 9-12 | 9, 10, 11, 12 | 5737 | 21 | Exact requested fixed values 9-12. |
| k1 | Morphemes | 1-4 | 1, 2, 3, 4 | 357854 | 21 | Exact requested fixed values 1-4. |
| k1 | Morphemes | 5-8 | 5, 6, 7, 8 | 77357 | 21 | Exact requested fixed values 5-8. |
| k1 | Morphemes | 9-12 | 9, 10, 11, 12 | 9409 | 21 | Exact requested fixed values 9-12. |
| k1 | Syllables: CMU/pkg | 1-4 representative ranks | 1, 2, 3, 4 | 344589 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Syllables: CMU/pkg | 5-8 representative ranks | 5, 6, 7, 8 | 86468 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Syllables: CMU/pkg | 9-12 representative ranks | 9, 10, 11, 12 | 12662 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Syllables: pkg | 1-4 representative ranks | 1, 2, 3, 4 | 329972 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Syllables: pkg | 5-8 representative ranks | 5, 6, 7, 8 | 97554 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Syllables: pkg | 9-12 representative ranks | 9, 10, 11, 12 | 15357 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Phonemes | 1-4 representative ranks | 2, 3, 4, 5 | 175070 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Phonemes | 5-8 representative ranks | 6, 7, 8, 9 | 118913 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k1 | Phonemes | 9-12 representative ranks | 10, 11, 12, 13 | 73995 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Words | 1-4 | 1, 2, 3, 4 | 381557 | 21 | Exact requested fixed values 1-4. |
| k2 | Words | 5-8 | 5, 6, 7, 8 | 58263 | 21 | Exact requested fixed values 5-8. |
| k2 | Words | 9-12 | 9, 10, 11, 12 | 5737 | 21 | Exact requested fixed values 9-12. |
| k2 | Morphemes | 1-4 | 1, 2, 3, 4 | 357854 | 21 | Exact requested fixed values 1-4. |
| k2 | Morphemes | 5-8 | 5, 6, 7, 8 | 77357 | 21 | Exact requested fixed values 5-8. |
| k2 | Morphemes | 9-12 | 9, 10, 11, 12 | 9409 | 21 | Exact requested fixed values 9-12. |
| k2 | Syllables: CMU/pkg | 1-4 representative ranks | 1, 2, 3, 4 | 344589 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Syllables: CMU/pkg | 5-8 representative ranks | 5, 6, 7, 8 | 86468 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Syllables: CMU/pkg | 9-12 representative ranks | 9, 10, 11, 12 | 12662 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Syllables: pkg | 1-4 representative ranks | 1, 2, 3, 4 | 329972 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Syllables: pkg | 5-8 representative ranks | 5, 6, 7, 8 | 97554 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Syllables: pkg | 9-12 representative ranks | 9, 10, 11, 12 | 15357 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Phonemes | 1-4 representative ranks | 2, 3, 4, 5 | 175070 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Phonemes | 5-8 representative ranks | 6, 7, 8, 9 | 118913 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k2 | Phonemes | 9-12 representative ranks | 10, 11, 12, 13 | 73995 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Words | 1-4 | 1, 2, 3, 4 | 381557 | 21 | Exact requested fixed values 1-4. |
| k3 | Words | 5-8 | 5, 6, 7, 8 | 58263 | 21 | Exact requested fixed values 5-8. |
| k3 | Words | 9-12 | 9, 10, 11, 12 | 5737 | 21 | Exact requested fixed values 9-12. |
| k3 | Morphemes | 1-4 | 1, 2, 3, 4 | 357854 | 21 | Exact requested fixed values 1-4. |
| k3 | Morphemes | 5-8 | 5, 6, 7, 8 | 77357 | 21 | Exact requested fixed values 5-8. |
| k3 | Morphemes | 9-12 | 9, 10, 11, 12 | 9409 | 21 | Exact requested fixed values 9-12. |
| k3 | Syllables: CMU/pkg | 1-4 representative ranks | 1, 2, 3, 4 | 344589 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Syllables: CMU/pkg | 5-8 representative ranks | 5, 6, 7, 8 | 86468 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Syllables: CMU/pkg | 9-12 representative ranks | 9, 10, 11, 12 | 12662 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Syllables: pkg | 1-4 representative ranks | 1, 2, 3, 4 | 329972 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Syllables: pkg | 5-8 representative ranks | 5, 6, 7, 8 | 97554 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Syllables: pkg | 9-12 representative ranks | 9, 10, 11, 12 | 15357 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Phonemes | 1-4 representative ranks | 2, 3, 4, 5 | 175070 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Phonemes | 5-8 representative ranks | 6, 7, 8, 9 | 118913 | 21 | Ordered split of the 12 most frequent observed exact values. |
| k3 | Phonemes | 9-12 representative ranks | 10, 11, 12, 13 | 73995 | 21 | Ordered split of the 12 most frequent observed exact values. |

## Fit Overview

How to read: `mean_r2` is in-sample fit across the effort-unit rows for that model. `negative_age_coef_rows` and `significant_age_rows` summarize the direction and p<.05 evidence for age within each model/context.

| context_k | model_id | model_family | model_label | context_variant | fitted_rows | mean_r2 | negative_age_coef_rows | significant_age_rows | significant_entropy_rows | significant_context_size_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M1 | M1 | Pooled age and effort | none | 5 | 0.7299 | 3 | 2 | 0 | 0 |
| k0 | M2 | M2 | Age and effort with child identity | none | 5 | 0.736 | 5 | 5 | 0 | 0 |
| k0 | M3 | M3 | Age by effort | none | 5 | 0.7364 | 5 | 5 | 0 | 0 |
| k1 | M1 | M1 | Pooled age and effort | none | 5 | 0.6488 | 2 | 0 | 0 | 0 |
| k1 | M2 | M2 | Age and effort with child identity | none | 5 | 0.6586 | 5 | 5 | 0 | 0 |
| k1 | M3 | M3 | Age by effort | none | 5 | 0.6586 | 5 | 5 | 0 | 0 |
| k1 | M4E | M4 | Context entropy added | entropy | 5 | 0.6585 | 5 | 5 | 0 | 0 |
| k1 | M4ES | M4 | Entropy plus matched context size | entropy_plus_size | 5 | 0.6594 | 5 | 5 | 0 | 5 |
| k1 | M4S | M4 | Matched context size added | context_size | 5 | 0.6599 | 5 | 5 | 0 | 5 |
| k1 | M5E | M5 | Age by context entropy | entropy | 5 | 0.6586 | 5 | 5 | 0 | 0 |
| k1 | M5ES | M5 | Age by entropy and size | entropy_plus_size | 5 | 0.6595 | 5 | 5 | 0 | 5 |
| k1 | M5S | M5 | Age by matched context size | context_size | 5 | 0.6599 | 5 | 5 | 0 | 5 |
| k1 | M6E | M6 | Effort and entropy interactions | entropy | 5 | 0.6587 | 5 | 5 | 0 | 0 |
| k1 | M6ES | M6 | Interaction-rich entropy and size model | entropy_plus_size | 5 | 0.6612 | 5 | 5 | 0 | 5 |
| k1 | M6S | M6 | Effort and context-size interactions | context_size | 5 | 0.6614 | 5 | 5 | 0 | 5 |
| k2 | M1 | M1 | Pooled age and effort | none | 5 | 0.6288 | 2 | 2 | 0 | 0 |
| k2 | M2 | M2 | Age and effort with child identity | none | 5 | 0.6408 | 5 | 5 | 0 | 0 |
| k2 | M3 | M3 | Age by effort | none | 5 | 0.6408 | 5 | 5 | 0 | 0 |
| k2 | M4E | M4 | Context entropy added | entropy | 5 | 0.6413 | 5 | 5 | 5 | 0 |
| k2 | M4ES | M4 | Entropy plus matched context size | entropy_plus_size | 5 | 0.6416 | 5 | 5 | 5 | 5 |
| k2 | M4S | M4 | Matched context size added | context_size | 5 | 0.6418 | 5 | 5 | 0 | 5 |
| k2 | M5E | M5 | Age by context entropy | entropy | 5 | 0.6413 | 5 | 5 | 5 | 0 |
| k2 | M5ES | M5 | Age by entropy and size | entropy_plus_size | 5 | 0.6417 | 5 | 5 | 5 | 5 |
| k2 | M5S | M5 | Age by matched context size | context_size | 5 | 0.6419 | 5 | 5 | 0 | 5 |
| k2 | M6E | M6 | Effort and entropy interactions | entropy | 5 | 0.6414 | 5 | 5 | 5 | 0 |
| k2 | M6ES | M6 | Interaction-rich entropy and size model | entropy_plus_size | 5 | 0.6435 | 5 | 5 | 5 | 5 |
| k2 | M6S | M6 | Effort and context-size interactions | context_size | 5 | 0.6436 | 5 | 5 | 0 | 5 |
| k3 | M1 | M1 | Pooled age and effort | none | 5 | 0.619 | 0 | 2 | 0 | 0 |
| k3 | M2 | M2 | Age and effort with child identity | none | 5 | 0.6318 | 5 | 5 | 0 | 0 |
| k3 | M3 | M3 | Age by effort | none | 5 | 0.6318 | 5 | 4 | 0 | 0 |
| k3 | M4E | M4 | Context entropy added | entropy | 5 | 0.6325 | 5 | 5 | 5 | 0 |
| k3 | M4ES | M4 | Entropy plus matched context size | entropy_plus_size | 5 | 0.6327 | 5 | 4 | 5 | 5 |
| k3 | M4S | M4 | Matched context size added | context_size | 5 | 0.633 | 5 | 5 | 0 | 5 |
| k3 | M5E | M5 | Age by context entropy | entropy | 5 | 0.6325 | 5 | 5 | 5 | 0 |
| k3 | M5ES | M5 | Age by entropy and size | entropy_plus_size | 5 | 0.6328 | 5 | 4 | 5 | 5 |
| k3 | M5S | M5 | Age by matched context size | context_size | 5 | 0.6331 | 5 | 4 | 0 | 5 |
| k3 | M6E | M6 | Effort and entropy interactions | entropy | 5 | 0.6327 | 5 | 4 | 5 | 0 |
| k3 | M6ES | M6 | Interaction-rich entropy and size model | entropy_plus_size | 5 | 0.6347 | 5 | 5 | 5 | 5 |
| k3 | M6S | M6 | Effort and context-size interactions | context_size | 5 | 0.6349 | 5 | 5 | 0 | 5 |

## Coefficient Table

How to read: coefficients are in Mistral bits. `age_coef` is bits/month after the listed controls. Interaction columns say how one slope changes as the interacting predictor increases. P-values are child-cluster robust.

| context_k | model_id | model_label | context_variant | effort_label | context_size_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | effort_entropy_coef | effort_entropy_p | age_context_size_coef | age_context_size_p | effort_context_size_coef | effort_context_size_p | entropy_context_size_coef | entropy_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M1 | Pooled age and effort | none | Words |  | 4.47e+05 | 21 | 0.7189 | -0.06724 | 0.005 | 7.138 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | Age and effort with child identity | none | Words |  | 4.47e+05 | 21 | 0.7252 | -0.1582 | <.001 | 7.127 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M3 | Age by effort | none | Words |  | 4.47e+05 | 21 | 0.7263 | -0.1515 | <.001 | 7.217 | <.001 |  |  |  |  | -0.02929 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | Pooled age and effort | none | Morphemes |  | 4.47e+05 | 21 | 0.7122 | -0.06145 | 0.005 | 6.17 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | Age and effort with child identity | none | Morphemes |  | 4.47e+05 | 21 | 0.7204 | -0.1784 | <.001 | 6.195 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M3 | Age by effort | none | Morphemes |  | 4.47e+05 | 21 | 0.7211 | -0.1727 | <.001 | 6.256 | <.001 |  |  |  |  | -0.02036 | 0.010 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | Pooled age and effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.7414 | -0.008835 | 0.569 | 5.841 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | Age and effort with child identity | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.7461 | -0.0907 | 0.003 | 5.848 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M3 | Age by effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.7463 | -0.08636 | 0.002 | 5.88 | <.001 |  |  |  |  | -0.01175 | 0.110 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | Pooled age and effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.725 | 0.009849 | 0.508 | 5.418 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | Age and effort with child identity | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.7303 | -0.07571 | 0.009 | 5.411 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M3 | Age by effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.7305 | -0.07272 | 0.009 | 5.431 | <.001 |  |  |  |  | -0.007984 | 0.121 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | Pooled age and effort | none | Phonemes |  | 4.47e+05 | 21 | 0.7522 | 0.005929 | 0.707 | 2.343 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | Age and effort with child identity | none | Phonemes |  | 4.47e+05 | 21 | 0.7578 | -0.09847 | 0.001 | 2.352 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M3 | Age by effort | none | Phonemes |  | 4.47e+05 | 21 | 0.7581 | -0.094 | 0.002 | 2.366 | <.001 |  |  |  |  | -0.005153 | 0.071 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | Pooled age and effort | none | Words |  | 4.47e+05 | 21 | 0.6395 | -0.03427 | 0.294 | 6.668 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | Age and effort with child identity | none | Words |  | 4.47e+05 | 21 | 0.6495 | -0.1431 | <.001 | 6.677 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M3 | Age by effort | none | Words |  | 4.47e+05 | 21 | 0.6497 | -0.1408 | <.001 | 6.709 | <.001 |  |  |  |  | -0.01004 | 0.079 |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | Context entropy added | entropy | Words |  | 4.422e+05 | 21 | 0.6495 | -0.1481 | <.001 | 6.68 | <.001 | 0.05917 | 0.274 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4S | Matched context size added | context_size | Words | Context words | 4.443e+05 | 21 | 0.651 | -0.1402 | <.001 | 6.671 | <.001 |  |  | -0.175 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4ES | Entropy plus matched context size | entropy_plus_size | Words | Context words | 4.422e+05 | 21 | 0.6506 | -0.1414 | <.001 | 6.679 | <.001 | -0.06001 | 0.247 | -0.1813 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | Age by context entropy | entropy | Words |  | 4.422e+05 | 21 | 0.6496 | -0.1491 | <.001 | 6.68 | <.001 | 0.06788 | 0.288 |  |  |  |  | 0.01505 | 0.018 |  |  |  |  |  |  |  |  |
| k1 | M5S | Age by matched context size | context_size | Words | Context words | 4.443e+05 | 21 | 0.651 | -0.1396 | <.001 | 6.671 | <.001 |  |  | -0.174 | <.001 |  |  |  |  |  |  | -0.002223 | 0.401 |  |  |  |  |
| k1 | M5ES | Age by entropy and size | entropy_plus_size | Words | Context words | 4.422e+05 | 21 | 0.6507 | -0.1421 | <.001 | 6.679 | <.001 | -0.05053 | 0.396 | -0.1811 | <.001 |  |  | 0.01498 | 0.003 |  |  | -0.001203 | 0.624 |  |  |  |  |
| k1 | M6E | Effort and entropy interactions | entropy | Words |  | 4.422e+05 | 21 | 0.6497 | -0.1471 | <.001 | 6.702 | <.001 | 0.07117 | 0.244 |  |  | -0.008804 | 0.213 | 0.01165 | 0.057 | 0.05147 | 0.043 |  |  |  |  |  |  |
| k1 | M6S | Effort and context-size interactions | context_size | Words | Context words | 4.443e+05 | 21 | 0.6525 | -0.1417 | <.001 | 6.729 | <.001 |  |  | -0.1604 | <.001 | -0.009531 | 0.103 |  |  |  |  | 0.00362 | 0.244 | -0.08664 | <.001 |  |  |
| k1 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Words | Context words | 4.422e+05 | 21 | 0.6522 | -0.1444 | <.001 | 6.734 | <.001 | -0.07778 | 0.204 | -0.1649 | <.001 | -0.00876 | 0.215 | 0.01618 | 0.003 | -0.007811 | 0.765 | 0.004946 | 0.105 | -0.08626 | <.001 | -0.04228 | <.001 |
| k1 | M1 | Pooled age and effort | none | Morphemes |  | 4.47e+05 | 21 | 0.6268 | -0.02637 | 0.382 | 5.731 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | Age and effort with child identity | none | Morphemes |  | 4.47e+05 | 21 | 0.639 | -0.1585 | <.001 | 5.772 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M3 | Age by effort | none | Morphemes |  | 4.47e+05 | 21 | 0.639 | -0.1576 | <.001 | 5.782 | <.001 |  |  |  |  | -0.003203 | 0.612 |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | Context entropy added | entropy | Morphemes |  | 4.422e+05 | 21 | 0.6388 | -0.1636 | <.001 | 5.773 | <.001 | 0.06736 | 0.206 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4S | Matched context size added | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6403 | -0.1562 | <.001 | 5.767 | <.001 |  |  | -0.1421 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4ES | Entropy plus matched context size | entropy_plus_size | Morphemes | Context morphemes | 4.422e+05 | 21 | 0.6397 | -0.1576 | <.001 | 5.772 | <.001 | -0.0464 | 0.357 | -0.1462 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | Age by context entropy | entropy | Morphemes |  | 4.422e+05 | 21 | 0.6389 | -0.1647 | <.001 | 5.772 | <.001 | 0.07772 | 0.230 |  |  |  |  | 0.01791 | 0.005 |  |  |  |  |  |  |  |  |
| k1 | M5S | Age by matched context size | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6403 | -0.1553 | <.001 | 5.766 | <.001 |  |  | -0.1408 | <.001 |  |  |  |  |  |  | -0.002978 | 0.156 |  |  |  |  |
| k1 | M5ES | Age by entropy and size | entropy_plus_size | Morphemes | Context morphemes | 4.422e+05 | 21 | 0.6399 | -0.1584 | <.001 | 5.772 | <.001 | -0.03454 | 0.558 | -0.1459 | <.001 |  |  | 0.0173 | <.001 |  |  | -0.002025 | 0.247 |  |  |  |  |
| k1 | M6E | Effort and entropy interactions | entropy | Morphemes |  | 4.422e+05 | 21 | 0.639 | -0.1639 | <.001 | 5.773 | <.001 | 0.082 | 0.172 |  |  | -0.001998 | 0.775 | 0.01332 | 0.030 | 0.05922 | 0.004 |  |  |  |  |  |  |
| k1 | M6S | Effort and context-size interactions | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6418 | -0.159 | <.001 | 5.799 | <.001 |  |  | -0.1274 | <.001 | -0.002851 | 0.642 |  |  |  |  | 0.002052 | 0.403 | -0.06803 | <.001 |  |  |
| k1 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Morphemes | Context morphemes | 4.422e+05 | 21 | 0.6415 | -0.1619 | <.001 | 5.802 | <.001 | -0.0727 | 0.219 | -0.129 | <.001 | -0.002118 | 0.758 | 0.01743 | <.001 | 0.005543 | 0.775 | 0.003243 | 0.142 | -0.06664 | <.001 | -0.04886 | <.001 |
| k1 | M1 | Pooled age and effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6644 | 0.01867 | 0.449 | 5.479 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | Age and effort with child identity | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6729 | -0.08207 | <.001 | 5.502 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M3 | Age by effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6729 | -0.0827 | <.001 | 5.498 | <.001 |  |  |  |  | 0.001689 | 0.768 |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | Context entropy added | entropy | Syllables: CMU/pkg |  | 4.422e+05 | 21 | 0.6728 | -0.08435 | <.001 | 5.502 | <.001 | 0.06356 | 0.204 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4S | Matched context size added | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6741 | -0.07966 | <.001 | 5.497 | <.001 |  |  | -0.1263 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4ES | Entropy plus matched context size | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.422e+05 | 21 | 0.6737 | -0.07842 | <.001 | 5.501 | <.001 | -0.03417 | 0.477 | -0.1285 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | Age by context entropy | entropy | Syllables: CMU/pkg |  | 4.422e+05 | 21 | 0.6729 | -0.08541 | <.001 | 5.502 | <.001 | 0.07299 | 0.219 |  |  |  |  | 0.0163 | 0.002 |  |  |  |  |  |  |  |  |
| k1 | M5S | Age by matched context size | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6741 | -0.07905 | <.001 | 5.496 | <.001 |  |  | -0.1253 | <.001 |  |  |  |  |  |  | -0.001844 | 0.347 |  |  |  |  |
| k1 | M5ES | Age by entropy and size | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.422e+05 | 21 | 0.6738 | -0.07929 | <.001 | 5.501 | <.001 | -0.0241 | 0.661 | -0.1286 | <.001 |  |  | 0.0164 | <.001 |  |  | -0.0008261 | 0.669 |  |  |  |  |
| k1 | M6E | Effort and entropy interactions | entropy | Syllables: CMU/pkg |  | 4.422e+05 | 21 | 0.6731 | -0.08642 | <.001 | 5.49 | <.001 | 0.07668 | 0.157 |  |  | 0.003309 | 0.583 | 0.01262 | 0.018 | 0.04969 | <.001 |  |  |  |  |  |  |
| k1 | M6S | Effort and context-size interactions | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6757 | -0.0842 | <.001 | 5.516 | <.001 |  |  | -0.1132 | <.001 | 0.002148 | 0.685 |  |  |  |  | 0.002167 | 0.406 | -0.06063 | <.001 |  |  |
| k1 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.422e+05 | 21 | 0.6755 | -0.08461 | <.001 | 5.517 | <.001 | -0.0493 | 0.374 | -0.1147 | <.001 | 0.003331 | 0.558 | 0.01641 | <.001 | 0.001874 | 0.901 | 0.003345 | 0.212 | -0.05992 | <.001 | -0.03363 | <.001 |
| k1 | M1 | Pooled age and effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6482 | 0.03667 | 0.153 | 5.076 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | Age and effort with child identity | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6572 | -0.06724 | 0.001 | 5.084 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M3 | Age by effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6573 | -0.069 | 0.002 | 5.071 | <.001 |  |  |  |  | 0.004698 | 0.233 |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | Context entropy added | entropy | Syllables: pkg |  | 4.422e+05 | 21 | 0.6571 | -0.06823 | <.001 | 5.083 | <.001 | 0.04786 | 0.346 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4S | Matched context size added | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6585 | -0.06479 | 0.002 | 5.078 | <.001 |  |  | -0.1208 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4ES | Entropy plus matched context size | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.422e+05 | 21 | 0.658 | -0.06222 | 0.002 | 5.081 | <.001 | -0.05367 | 0.281 | -0.1244 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | Age by context entropy | entropy | Syllables: pkg |  | 4.422e+05 | 21 | 0.6572 | -0.06928 | <.001 | 5.082 | <.001 | 0.05728 | 0.331 |  |  |  |  | 0.01629 | <.001 |  |  |  |  |  |  |  |  |
| k1 | M5S | Age by matched context size | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6585 | -0.06415 | 0.003 | 5.077 | <.001 |  |  | -0.1198 | <.001 |  |  |  |  |  |  | -0.001897 | 0.269 |  |  |  |  |
| k1 | M5ES | Age by entropy and size | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.422e+05 | 21 | 0.6581 | -0.0631 | 0.001 | 5.081 | <.001 | -0.04358 | 0.428 | -0.1245 | <.001 |  |  | 0.01639 | <.001 |  |  | -0.0008058 | 0.648 |  |  |  |  |
| k1 | M6E | Effort and entropy interactions | entropy | Syllables: pkg |  | 4.422e+05 | 21 | 0.6574 | -0.07135 | <.001 | 5.062 | <.001 | 0.06127 | 0.241 |  |  | 0.006345 | 0.187 | 0.01204 | 0.012 | 0.05472 | <.001 |  |  |  |  |  |  |
| k1 | M6S | Effort and context-size interactions | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6601 | -0.0703 | 0.002 | 5.087 | <.001 |  |  | -0.1083 | <.001 | 0.005177 | 0.169 |  |  |  |  | 0.001678 | 0.433 | -0.05305 | <.001 |  |  |
| k1 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.422e+05 | 21 | 0.6598 | -0.06931 | 0.001 | 5.086 | <.001 | -0.07058 | 0.200 | -0.1106 | <.001 | 0.006357 | 0.169 | 0.01566 | <.001 | 0.01019 | 0.406 | 0.002883 | 0.208 | -0.05183 | <.001 | -0.03327 | <.001 |
| k1 | M1 | Pooled age and effort | none | Phonemes |  | 4.47e+05 | 21 | 0.6649 | 0.03523 | 0.161 | 2.182 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | Age and effort with child identity | none | Phonemes |  | 4.47e+05 | 21 | 0.6743 | -0.08519 | <.001 | 2.196 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M3 | Age by effort | none | Phonemes |  | 4.47e+05 | 21 | 0.6743 | -0.08562 | <.001 | 2.195 | <.001 |  |  |  |  | 0.0004941 | 0.820 |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | Context entropy added | entropy | Phonemes |  | 4.422e+05 | 21 | 0.6743 | -0.08687 | <.001 | 2.196 | <.001 | 0.02783 | 0.548 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4S | Matched context size added | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6755 | -0.08311 | <.001 | 2.194 | <.001 |  |  | -0.04665 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4ES | Entropy plus matched context size | entropy_plus_size | Phonemes | Context phonemes | 4.422e+05 | 21 | 0.6751 | -0.08125 | <.001 | 2.195 | <.001 | -0.06489 | 0.143 | -0.04865 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | Age by context entropy | entropy | Phonemes |  | 4.422e+05 | 21 | 0.6744 | -0.08788 | <.001 | 2.196 | <.001 | 0.03693 | 0.502 |  |  |  |  | 0.01573 | 0.002 |  |  |  |  |  |  |  |  |
| k1 | M5S | Age by matched context size | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6755 | -0.08255 | <.001 | 2.193 | <.001 |  |  | -0.04623 | <.001 |  |  |  |  |  |  | -0.0006969 | 0.338 |  |  |  |  |
| k1 | M5ES | Age by entropy and size | entropy_plus_size | Phonemes | Context phonemes | 4.422e+05 | 21 | 0.6752 | -0.0821 | <.001 | 2.195 | <.001 | -0.05507 | 0.273 | -0.04867 | <.001 |  |  | 0.01587 | <.001 |  |  | -0.0003338 | 0.624 |  |  |  |  |
| k1 | M6E | Effort and entropy interactions | entropy | Phonemes |  | 4.422e+05 | 21 | 0.6744 | -0.08865 | <.001 | 2.192 | <.001 | 0.0396 | 0.435 |  |  | 0.001076 | 0.696 | 0.01283 | 0.011 | 0.01619 | 0.011 |  |  |  |  |  |  |
| k1 | M6S | Effort and context-size interactions | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6771 | -0.08757 | <.001 | 2.201 | <.001 |  |  | -0.04115 | <.001 | 0.0006425 | 0.773 |  |  |  |  | 0.0008178 | 0.370 | -0.009491 | <.001 |  |  |
| k1 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Phonemes | Context phonemes | 4.422e+05 | 21 | 0.6769 | -0.08725 | <.001 | 2.203 | <.001 | -0.08079 | 0.109 | -0.04256 | <.001 | 0.001092 | 0.690 | 0.01652 | <.001 | -0.003187 | 0.595 | 0.001271 | 0.160 | -0.009486 | <.001 | -0.01357 | <.001 |
| k2 | M1 | Pooled age and effort | none | Words |  | 4.47e+05 | 21 | 0.6218 | -0.01155 | 0.727 | 6.455 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | Age and effort with child identity | none | Words |  | 4.47e+05 | 21 | 0.6338 | -0.1287 | <.001 | 6.468 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M3 | Age by effort | none | Words |  | 4.47e+05 | 21 | 0.6339 | -0.1274 | <.001 | 6.486 | <.001 |  |  |  |  | -0.005741 | 0.318 |  |  |  |  |  |  |  |  |  |  |
| k2 | M4E | Context entropy added | entropy | Words |  | 4.415e+05 | 21 | 0.6343 | -0.1318 | <.001 | 6.47 | <.001 | -0.4107 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4S | Matched context size added | context_size | Words | Context words | 4.443e+05 | 21 | 0.635 | -0.1289 | <.001 | 6.464 | <.001 |  |  | -0.07164 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4ES | Entropy plus matched context size | entropy_plus_size | Words | Context words | 4.415e+05 | 21 | 0.6347 | -0.1273 | <.001 | 6.47 | <.001 | -0.4087 | <.001 | -0.06994 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M5E | Age by context entropy | entropy | Words |  | 4.415e+05 | 21 | 0.6343 | -0.1327 | <.001 | 6.47 | <.001 | -0.4085 | <.001 |  |  |  |  | 0.009403 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M5S | Age by matched context size | context_size | Words | Context words | 4.443e+05 | 21 | 0.6351 | -0.1266 | <.001 | 6.463 | <.001 |  |  | -0.0699 | <.001 |  |  |  |  |  |  | -0.004125 | 0.017 |  |  |  |  |
| k2 | M5ES | Age by entropy and size | entropy_plus_size | Words | Context words | 4.415e+05 | 21 | 0.6348 | -0.1263 | <.001 | 6.47 | <.001 | -0.405 | <.001 | -0.0683 | <.001 |  |  | 0.01073 | <.001 |  |  | -0.004204 | 0.019 |  |  |  |  |
| k2 | M6E | Effort and entropy interactions | entropy | Words |  | 4.415e+05 | 21 | 0.6343 | -0.132 | <.001 | 6.486 | <.001 | -0.411 | <.001 |  |  | -0.00449 | 0.532 | 0.01205 | <.001 | -0.03533 | 0.025 |  |  |  |  |  |  |
| k2 | M6S | Effort and context-size interactions | context_size | Words | Context words | 4.443e+05 | 21 | 0.6367 | -0.131 | <.001 | 6.522 | <.001 |  |  | -0.05973 | <.001 | -0.004747 | 0.403 |  |  |  |  | -1.653e-05 | 0.992 | -0.06081 | <.001 |  |  |
| k2 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Words | Context words | 4.415e+05 | 21 | 0.6364 | -0.1312 | <.001 | 6.525 | <.001 | -0.4245 | <.001 | -0.05664 | <.001 | -0.00354 | 0.623 | 0.01304 | <.001 | -0.02386 | 0.137 | -1.545e-05 | 0.993 | -0.06014 | <.001 | -0.01932 | <.001 |
| k2 | M1 | Pooled age and effort | none | Morphemes |  | 4.47e+05 | 21 | 0.6074 | -0.003091 | 0.921 | 5.537 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | Age and effort with child identity | none | Morphemes |  | 4.47e+05 | 21 | 0.6217 | -0.1425 | <.001 | 5.581 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M3 | Age by effort | none | Morphemes |  | 4.47e+05 | 21 | 0.6217 | -0.1427 | <.001 | 5.579 | <.001 |  |  |  |  | 0.0006276 | 0.922 |  |  |  |  |  |  |  |  |  |  |
| k2 | M4E | Context entropy added | entropy | Morphemes |  | 4.415e+05 | 21 | 0.622 | -0.1458 | <.001 | 5.582 | <.001 | -0.4256 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4S | Matched context size added | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6227 | -0.1433 | <.001 | 5.577 | <.001 |  |  | -0.05554 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4ES | Entropy plus matched context size | entropy_plus_size | Morphemes | Context morphemes | 4.415e+05 | 21 | 0.6223 | -0.142 | <.001 | 5.582 | <.001 | -0.4253 | <.001 | -0.05438 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M5E | Age by context entropy | entropy | Morphemes |  | 4.415e+05 | 21 | 0.622 | -0.1469 | <.001 | 5.582 | <.001 | -0.423 | <.001 |  |  |  |  | 0.01127 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M5S | Age by matched context size | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6228 | -0.1409 | <.001 | 5.576 | <.001 |  |  | -0.0541 | <.001 |  |  |  |  |  |  | -0.00417 | 0.010 |  |  |  |  |
| k2 | M5ES | Age by entropy and size | entropy_plus_size | Morphemes | Context morphemes | 4.415e+05 | 21 | 0.6224 | -0.1411 | <.001 | 5.581 | <.001 | -0.4216 | <.001 | -0.05295 | <.001 |  |  | 0.01227 | <.001 |  |  | -0.004267 | 0.009 |  |  |  |  |
| k2 | M6E | Effort and entropy interactions | entropy | Morphemes |  | 4.415e+05 | 21 | 0.622 | -0.1475 | <.001 | 5.578 | <.001 | -0.4253 | <.001 |  |  | 0.001876 | 0.791 | 0.01352 | <.001 | -0.03127 | 0.057 |  |  |  |  |  |  |
| k2 | M6S | Effort and context-size interactions | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6246 | -0.1469 | <.001 | 5.611 | <.001 |  |  | -0.04444 | <.001 | 0.001426 | 0.811 |  |  |  |  | -0.0006482 | 0.657 | -0.04815 | <.001 |  |  |
| k2 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Morphemes | Context morphemes | 4.415e+05 | 21 | 0.6242 | -0.1475 | <.001 | 5.614 | <.001 | -0.4449 | <.001 | -0.04179 | <.001 | 0.002631 | 0.703 | 0.01435 | <.001 | -0.02245 | 0.189 | -0.0006653 | 0.666 | -0.04765 | <.001 | -0.01962 | <.001 |
| k2 | M1 | Pooled age and effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6445 | 0.04012 | 0.126 | 5.298 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | Age and effort with child identity | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6551 | -0.06903 | 0.007 | 5.323 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M3 | Age by effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6552 | -0.07101 | 0.007 | 5.309 | <.001 |  |  |  |  | 0.005351 | 0.370 |  |  |  |  |  |  |  |  |  |  |
| k2 | M4E | Context entropy added | entropy | Syllables: CMU/pkg |  | 4.415e+05 | 21 | 0.6557 | -0.06891 | 0.006 | 5.324 | <.001 | -0.4558 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4S | Matched context size added | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6561 | -0.06963 | 0.007 | 5.319 | <.001 |  |  | -0.04898 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4ES | Entropy plus matched context size | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.415e+05 | 21 | 0.656 | -0.06519 | 0.009 | 5.324 | <.001 | -0.4521 | <.001 | -0.04709 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M5E | Age by context entropy | entropy | Syllables: CMU/pkg |  | 4.415e+05 | 21 | 0.6557 | -0.06976 | 0.005 | 5.324 | <.001 | -0.4537 | <.001 |  |  |  |  | 0.009102 | 0.003 |  |  |  |  |  |  |  |  |
| k2 | M5S | Age by matched context size | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6562 | -0.06748 | 0.009 | 5.318 | <.001 |  |  | -0.0477 | <.001 |  |  |  |  |  |  | -0.003028 | 0.011 |  |  |  |  |
| k2 | M5ES | Age by entropy and size | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.415e+05 | 21 | 0.6561 | -0.06422 | 0.010 | 5.323 | <.001 | -0.4485 | <.001 | -0.04591 | <.001 |  |  | 0.01044 | <.001 |  |  | -0.003029 | 0.014 |  |  |  |  |
| k2 | M6E | Effort and entropy interactions | entropy | Syllables: CMU/pkg |  | 4.415e+05 | 21 | 0.6559 | -0.0722 | 0.006 | 5.307 | <.001 | -0.4554 | <.001 |  |  | 0.007145 | 0.258 | 0.01096 | <.001 | -0.03437 | 0.020 |  |  |  |  |  |  |
| k2 | M6S | Effort and context-size interactions | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6581 | -0.07513 | 0.004 | 5.341 | <.001 |  |  | -0.0386 | <.001 | 0.006098 | 0.244 |  |  |  |  | -0.0003736 | 0.777 | -0.04222 | <.001 |  |  |
| k2 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.415e+05 | 21 | 0.658 | -0.07228 | 0.006 | 5.343 | <.001 | -0.4678 | <.001 | -0.03553 | <.001 | 0.007791 | 0.179 | 0.0118 | <.001 | -0.02086 | 0.166 | -0.0003223 | 0.821 | -0.04178 | <.001 | -0.01604 | <.001 |
| k2 | M1 | Pooled age and effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6279 | 0.05785 | 0.032 | 4.903 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | Age and effort with child identity | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.639 | -0.0542 | 0.021 | 4.914 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M3 | Age by effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6391 | -0.05728 | 0.026 | 4.893 | <.001 |  |  |  |  | 0.00822 | 0.048 |  |  |  |  |  |  |  |  |  |  |
| k2 | M4E | Context entropy added | entropy | Syllables: pkg |  | 4.415e+05 | 21 | 0.6396 | -0.05248 | 0.017 | 4.913 | <.001 | -0.4543 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4S | Matched context size added | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.64 | -0.05479 | 0.021 | 4.909 | <.001 |  |  | -0.04671 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4ES | Entropy plus matched context size | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.415e+05 | 21 | 0.6399 | -0.04875 | 0.027 | 4.913 | <.001 | -0.4506 | <.001 | -0.04487 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M5E | Age by context entropy | entropy | Syllables: pkg |  | 4.415e+05 | 21 | 0.6396 | -0.0533 | 0.016 | 4.913 | <.001 | -0.4522 | <.001 |  |  |  |  | 0.008871 | 0.003 |  |  |  |  |  |  |  |  |
| k2 | M5S | Age by matched context size | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6401 | -0.05265 | 0.025 | 4.909 | <.001 |  |  | -0.04546 | <.001 |  |  |  |  |  |  | -0.002931 | 0.011 |  |  |  |  |
| k2 | M5ES | Age by entropy and size | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.415e+05 | 21 | 0.64 | -0.04782 | 0.031 | 4.912 | <.001 | -0.447 | <.001 | -0.04373 | <.001 |  |  | 0.0102 | <.001 |  |  | -0.002896 | 0.015 |  |  |  |  |
| k2 | M6E | Effort and entropy interactions | entropy | Syllables: pkg |  | 4.415e+05 | 21 | 0.6398 | -0.05665 | 0.024 | 4.889 | <.001 | -0.4527 | <.001 |  |  | 0.01025 | 0.045 | 0.009547 | 0.003 | -0.02111 | 0.110 |  |  |  |  |  |  |
| k2 | M6S | Effort and context-size interactions | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6418 | -0.06081 | 0.018 | 4.918 | <.001 |  |  | -0.03724 | <.001 | 0.008955 | 0.018 |  |  |  |  | -0.0007188 | 0.524 | -0.03522 | <.001 |  |  |
| k2 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.415e+05 | 21 | 0.6417 | -0.05626 | 0.023 | 4.918 | <.001 | -0.4657 | <.001 | -0.03415 | <.001 | 0.01085 | 0.028 | 0.01046 | 0.002 | -0.008991 | 0.514 | -0.0006313 | 0.607 | -0.03491 | <.001 | -0.01579 | <.001 |
| k2 | M1 | Pooled age and effort | none | Phonemes |  | 4.47e+05 | 21 | 0.6426 | 0.05686 | 0.032 | 2.105 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | Age and effort with child identity | none | Phonemes |  | 4.47e+05 | 21 | 0.6542 | -0.07096 | 0.005 | 2.12 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M3 | Age by effort | none | Phonemes |  | 4.47e+05 | 21 | 0.6542 | -0.07275 | 0.007 | 2.115 | <.001 |  |  |  |  | 0.00207 | 0.347 |  |  |  |  |  |  |  |  |  |  |
| k2 | M4E | Context entropy added | entropy | Phonemes |  | 4.415e+05 | 21 | 0.6549 | -0.06995 | 0.006 | 2.12 | <.001 | -0.4942 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4S | Matched context size added | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6552 | -0.0717 | 0.005 | 2.118 | <.001 |  |  | -0.01841 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M4ES | Entropy plus matched context size | entropy_plus_size | Phonemes | Context phonemes | 4.415e+05 | 21 | 0.6551 | -0.0665 | 0.008 | 2.12 | <.001 | -0.4898 | <.001 | -0.01751 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k2 | M5E | Age by context entropy | entropy | Phonemes |  | 4.415e+05 | 21 | 0.6549 | -0.07082 | 0.005 | 2.121 | <.001 | -0.492 | <.001 |  |  |  |  | 0.009362 | 0.002 |  |  |  |  |  |  |  |  |
| k2 | M5S | Age by matched context size | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6552 | -0.06955 | 0.007 | 2.118 | <.001 |  |  | -0.01782 | <.001 |  |  |  |  |  |  | -0.001223 | 0.009 |  |  |  |  |
| k2 | M5ES | Age by entropy and size | entropy_plus_size | Phonemes | Context phonemes | 4.415e+05 | 21 | 0.6552 | -0.06565 | 0.009 | 2.12 | <.001 | -0.4861 | <.001 | -0.01697 | <.001 |  |  | 0.01074 | <.001 |  |  | -0.001234 | 0.009 |  |  |  |  |
| k2 | M6E | Effort and entropy interactions | entropy | Phonemes |  | 4.415e+05 | 21 | 0.655 | -0.07308 | 0.008 | 2.114 | <.001 | -0.4947 | <.001 |  |  | 0.00278 | 0.328 | 0.01224 | <.001 | -0.02031 | 0.001 |  |  |  |  |  |  |
| k2 | M6S | Effort and context-size interactions | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6571 | -0.07708 | 0.005 | 2.127 | <.001 |  |  | -0.01405 | <.001 | 0.002379 | 0.274 |  |  |  |  | -0.0002119 | 0.638 | -0.006648 | <.001 |  |  |
| k2 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Phonemes | Context phonemes | 4.415e+05 | 21 | 0.6572 | -0.07354 | 0.007 | 2.128 | <.001 | -0.5063 | <.001 | -0.01272 | <.001 | 0.00307 | 0.280 | 0.01308 | <.001 | -0.01501 | 0.025 | -0.0002018 | 0.674 | -0.006575 | <.001 | -0.006042 | <.001 |
| k3 | M1 | Pooled age and effort | none | Words |  | 4.47e+05 | 21 | 0.613 | 0.0003087 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | Age and effort with child identity | none | Words |  | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M3 | Age by effort | none | Words |  | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  |  |  | -0.003787 | 0.515 |  |  |  |  |  |  |  |  |  |  |
| k3 | M4E | Context entropy added | entropy | Words |  | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4S | Matched context size added | context_size | Words | Context words | 4.443e+05 | 21 | 0.6272 | -0.1239 | <.001 | 6.363 | <.001 |  |  | -0.04386 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4ES | Entropy plus matched context size | entropy_plus_size | Words | Context words | 4.414e+05 | 21 | 0.6268 | -0.123 | <.001 | 6.368 | <.001 | -0.4699 | <.001 | -0.0427 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M5E | Age by context entropy | entropy | Words |  | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  |  |  | 0.006141 | 0.284 |  |  |  |  |  |  |  |  |
| k3 | M5S | Age by matched context size | context_size | Words | Context words | 4.443e+05 | 21 | 0.6274 | -0.121 | <.001 | 6.362 | <.001 |  |  | -0.04263 | <.001 |  |  |  |  |  |  | -0.003511 | 0.009 |  |  |  |  |
| k3 | M5ES | Age by entropy and size | entropy_plus_size | Words | Context words | 4.414e+05 | 21 | 0.6269 | -0.121 | <.001 | 6.367 | <.001 | -0.4679 | <.001 | -0.04139 | <.001 |  |  | 0.00728 | 0.202 |  |  | -0.003595 | 0.010 |  |  |  |  |
| k3 | M6E | Effort and entropy interactions | entropy | Words |  | 4.414e+05 | 21 | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 |  |  | -0.002441 | 0.726 | 0.009085 | 0.111 | -0.04062 | 0.353 |  |  |  |  |  |  |
| k3 | M6S | Effort and context-size interactions | context_size | Words | Context words | 4.443e+05 | 21 | 0.6289 | -0.1264 | <.001 | 6.423 | <.001 |  |  | -0.03497 | <.001 | -0.002699 | 0.629 |  |  |  |  | -0.0005524 | 0.660 | -0.04583 | <.001 |  |  |
| k3 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Words | Context words | 4.414e+05 | 21 | 0.6285 | -0.127 | <.001 | 6.425 | <.001 | -0.4939 | <.001 | -0.03458 | <.001 | -0.001189 | 0.864 | 0.01057 | 0.071 | -0.03719 | 0.383 | -0.0005501 | 0.679 | -0.04591 | <.001 | -0.01686 | 0.009 |
| k3 | M1 | Pooled age and effort | none | Morphemes |  | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | Age and effort with child identity | none | Morphemes |  | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M3 | Age by effort | none | Morphemes |  | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  |  |  | 0.00228 | 0.727 |  |  |  |  |  |  |  |  |  |  |
| k3 | M4E | Context entropy added | entropy | Morphemes |  | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4S | Matched context size added | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6142 | -0.1375 | <.001 | 5.485 | <.001 |  |  | -0.03407 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4ES | Entropy plus matched context size | entropy_plus_size | Morphemes | Context morphemes | 4.414e+05 | 21 | 0.6138 | -0.1369 | <.001 | 5.489 | <.001 | -0.5111 | <.001 | -0.03298 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M5E | Age by context entropy | entropy | Morphemes |  | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  |  |  | 0.004709 | 0.339 |  |  |  |  |  |  |  |  |
| k3 | M5S | Age by matched context size | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6144 | -0.1345 | <.001 | 5.484 | <.001 |  |  | -0.03311 | <.001 |  |  |  |  |  |  | -0.003561 | 0.006 |  |  |  |  |
| k3 | M5ES | Age by entropy and size | entropy_plus_size | Morphemes | Context morphemes | 4.414e+05 | 21 | 0.614 | -0.1347 | <.001 | 5.488 | <.001 | -0.51 | <.001 | -0.0319 | <.001 |  |  | 0.005694 | 0.244 |  |  | -0.003641 | 0.006 |  |  |  |  |
| k3 | M6E | Effort and entropy interactions | entropy | Morphemes |  | 4.414e+05 | 21 | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 |  |  | 0.003897 | 0.575 | 0.009103 | 0.070 | -0.0649 | 0.170 |  |  |  |  |  |  |
| k3 | M6S | Effort and context-size interactions | context_size | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6162 | -0.1419 | <.001 | 5.523 | <.001 |  |  | -0.02546 | <.001 | 0.003169 | 0.589 |  |  |  |  | -0.0009642 | 0.360 | -0.03759 | <.001 |  |  |
| k3 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Morphemes | Context morphemes | 4.414e+05 | 21 | 0.6159 | -0.1426 | <.001 | 5.526 | <.001 | -0.541 | <.001 | -0.02502 | <.001 | 0.004933 | 0.457 | 0.01042 | 0.043 | -0.06195 | 0.183 | -0.0009726 | 0.384 | -0.03768 | <.001 | -0.01521 | 0.006 |
| k3 | M1 | Pooled age and effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | Age and effort with child identity | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M3 | Age by effort | none | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  |  |  | 0.00703 | 0.252 |  |  |  |  |  |  |  |  |  |  |
| k3 | M4E | Context entropy added | entropy | Syllables: CMU/pkg |  | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4S | Matched context size added | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6471 | -0.06497 | 0.016 | 5.232 | <.001 |  |  | -0.02985 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4ES | Entropy plus matched context size | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.414e+05 | 21 | 0.6469 | -0.06126 | 0.018 | 5.235 | <.001 | -0.5362 | <.001 | -0.02838 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M5E | Age by context entropy | entropy | Syllables: CMU/pkg |  | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  |  |  | 0.003955 | 0.478 |  |  |  |  |  |  |  |  |
| k3 | M5S | Age by matched context size | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6472 | -0.06226 | 0.022 | 5.231 | <.001 |  |  | -0.02888 | <.001 |  |  |  |  |  |  | -0.00253 | 0.006 |  |  |  |  |
| k3 | M5ES | Age by entropy and size | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.414e+05 | 21 | 0.647 | -0.05921 | 0.026 | 5.234 | <.001 | -0.5345 | <.001 | -0.02733 | <.001 |  |  | 0.005245 | 0.346 |  |  | -0.002541 | 0.007 |  |  |  |  |
| k3 | M6E | Effort and entropy interactions | entropy | Syllables: CMU/pkg |  | 4.414e+05 | 21 | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 |  |  | 0.009024 | 0.154 | 0.00658 | 0.202 | -0.05444 | 0.123 |  |  |  |  |  |  |
| k3 | M6S | Effort and context-size interactions | context_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.649 | -0.07096 | 0.010 | 5.255 | <.001 |  |  | -0.02175 | 0.002 | 0.007908 | 0.133 |  |  |  |  | -0.0006949 | 0.481 | -0.03138 | <.001 |  |  |
| k3 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.414e+05 | 21 | 0.6489 | -0.06831 | 0.014 | 5.256 | <.001 | -0.5605 | <.001 | -0.02076 | 0.003 | 0.009957 | 0.081 | 0.008035 | 0.129 | -0.04894 | 0.159 | -0.0006681 | 0.524 | -0.03142 | <.001 | -0.01177 | 0.017 |
| k3 | M1 | Pooled age and effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | Age and effort with child identity | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M3 | Age by effort | none | Syllables: pkg |  | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  |  |  | 0.009859 | 0.022 |  |  |  |  |  |  |  |  |  |  |
| k3 | M4E | Context entropy added | entropy | Syllables: pkg |  | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4S | Matched context size added | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6308 | -0.05014 | 0.044 | 4.827 | <.001 |  |  | -0.0288 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4ES | Entropy plus matched context size | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.414e+05 | 21 | 0.6306 | -0.04483 | 0.052 | 4.829 | <.001 | -0.537 | <.001 | -0.02722 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M5E | Age by context entropy | entropy | Syllables: pkg |  | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  |  |  | 0.003946 | 0.481 |  |  |  |  |  |  |  |  |
| k3 | M5S | Age by matched context size | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6309 | -0.04746 | 0.056 | 4.826 | <.001 |  |  | -0.02789 | <.001 |  |  |  |  |  |  | -0.002428 | 0.006 |  |  |  |  |
| k3 | M5ES | Age by entropy and size | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.414e+05 | 21 | 0.6307 | -0.04287 | 0.071 | 4.828 | <.001 | -0.5354 | <.001 | -0.02626 | <.001 |  |  | 0.005242 | 0.343 |  |  | -0.002424 | 0.006 |  |  |  |  |
| k3 | M6E | Effort and entropy interactions | entropy | Syllables: pkg |  | 4.414e+05 | 21 | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 |  |  | 0.01209 | 0.017 | 0.005176 | 0.277 | -0.04038 | 0.200 |  |  |  |  |  |  |
| k3 | M6S | Effort and context-size interactions | context_size | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6326 | -0.05648 | 0.037 | 4.836 | <.001 |  |  | -0.02169 | <.001 | 0.01067 | 0.006 |  |  |  |  | -0.0009513 | 0.257 | -0.02589 | <.001 |  |  |
| k3 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Syllables: pkg | Context syllables: pkg | 4.414e+05 | 21 | 0.6325 | -0.05205 | 0.049 | 4.835 | <.001 | -0.5613 | <.001 | -0.02054 | <.001 | 0.0129 | 0.008 | 0.006645 | 0.174 | -0.03441 | 0.264 | -0.0009172 | 0.303 | -0.02593 | <.001 | -0.01211 | 0.013 |
| k3 | M1 | Pooled age and effort | none | Phonemes |  | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | Age and effort with child identity | none | Phonemes |  | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M3 | Age by effort | none | Phonemes |  | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  |  |  | 0.002729 | 0.220 |  |  |  |  |  |  |  |  |  |  |
| k3 | M4E | Context entropy added | entropy | Phonemes |  | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4S | Matched context size added | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6455 | -0.06667 | 0.013 | 2.082 | <.001 |  |  | -0.01139 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M4ES | Entropy plus matched context size | entropy_plus_size | Phonemes | Context phonemes | 4.414e+05 | 21 | 0.6455 | -0.06221 | 0.016 | 2.084 | <.001 | -0.577 | <.001 | -0.0106 | <.001 |  |  |  |  |  |  |  |  |  |  |  |  |
| k3 | M5E | Age by context entropy | entropy | Phonemes |  | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  |  |  | 0.00465 | 0.407 |  |  |  |  |  |  |  |  |
| k3 | M5S | Age by matched context size | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6457 | -0.06397 | 0.017 | 2.082 | <.001 |  |  | -0.01094 | <.001 |  |  |  |  |  |  | -0.001031 | 0.006 |  |  |  |  |
| k3 | M5ES | Age by entropy and size | entropy_plus_size | Phonemes | Context phonemes | 4.414e+05 | 21 | 0.6456 | -0.06036 | 0.024 | 2.084 | <.001 | -0.5753 | <.001 | -0.01013 | <.001 |  |  | 0.006003 | 0.281 |  |  | -0.001034 | 0.005 |  |  |  |  |
| k3 | M6E | Effort and entropy interactions | entropy | Phonemes |  | 4.414e+05 | 21 | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 |  |  | 0.003548 | 0.200 | 0.00833 | 0.086 | -0.02895 | 0.122 |  |  |  |  |  |  |
| k3 | M6S | Effort and context-size interactions | context_size | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6476 | -0.07269 | 0.010 | 2.092 | <.001 |  |  | -0.007942 | 0.002 | 0.003091 | 0.148 |  |  |  |  | -0.0003109 | 0.366 | -0.005093 | <.001 |  |  |
| k3 | M6ES | Interaction-rich entropy and size model | entropy_plus_size | Phonemes | Context phonemes | 4.414e+05 | 21 | 0.6476 | -0.06946 | 0.014 | 2.093 | <.001 | -0.6018 | <.001 | -0.007348 | 0.004 | 0.00395 | 0.151 | 0.009755 | 0.051 | -0.02671 | 0.143 | -0.0003008 | 0.398 | -0.0051 | <.001 | -0.004074 | 0.023 |

## Fixed-Slice Slope Summary

How to read: these are descriptive slopes computed from plotted prediction lines, not separate inferential models. Inference comes from the coefficient table.

| context_k | model_id | model_label | effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | mean_slope_bits_per_month | min_slope_bits_per_month | max_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M1 | Pooled age and effort | Morphemes | 1-4 | 4 | 4 | 0 | -0.06145 | -0.06145 | -0.06145 |
| k0 | M1 | Pooled age and effort | Morphemes | 5-8 | 4 | 4 | 0 | -0.06145 | -0.06145 | -0.06145 |
| k0 | M1 | Pooled age and effort | Morphemes | 9-12 | 4 | 4 | 0 | -0.06145 | -0.06145 | -0.06145 |
| k0 | M1 | Pooled age and effort | Phonemes | 1-4 representative ranks | 4 | 0 | 4 | 0.005929 | 0.005929 | 0.005929 |
| k0 | M1 | Pooled age and effort | Phonemes | 5-8 representative ranks | 4 | 0 | 4 | 0.005929 | 0.005929 | 0.005929 |
| k0 | M1 | Pooled age and effort | Phonemes | 9-12 representative ranks | 4 | 0 | 4 | 0.005929 | 0.005929 | 0.005929 |
| k0 | M1 | Pooled age and effort | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.008835 | -0.008835 | -0.008835 |
| k0 | M1 | Pooled age and effort | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.008835 | -0.008835 | -0.008835 |
| k0 | M1 | Pooled age and effort | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.008835 | -0.008835 | -0.008835 |
| k0 | M1 | Pooled age and effort | Syllables: pkg | 1-4 representative ranks | 4 | 0 | 4 | 0.009849 | 0.009849 | 0.009849 |
| k0 | M1 | Pooled age and effort | Syllables: pkg | 5-8 representative ranks | 4 | 0 | 4 | 0.009849 | 0.009849 | 0.009849 |
| k0 | M1 | Pooled age and effort | Syllables: pkg | 9-12 representative ranks | 4 | 0 | 4 | 0.009849 | 0.009849 | 0.009849 |
| k0 | M1 | Pooled age and effort | Words | 1-4 | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k0 | M1 | Pooled age and effort | Words | 5-8 | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k0 | M1 | Pooled age and effort | Words | 9-12 | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k0 | M2 | Age and effort with child identity | Morphemes | 1-4 | 4 | 4 | 0 | -0.1784 | -0.1784 | -0.1784 |
| k0 | M2 | Age and effort with child identity | Morphemes | 5-8 | 4 | 4 | 0 | -0.1784 | -0.1784 | -0.1784 |
| k0 | M2 | Age and effort with child identity | Morphemes | 9-12 | 4 | 4 | 0 | -0.1784 | -0.1784 | -0.1784 |
| k0 | M2 | Age and effort with child identity | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.09847 | -0.09847 | -0.09847 |
| k0 | M2 | Age and effort with child identity | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.09847 | -0.09847 | -0.09847 |
| k0 | M2 | Age and effort with child identity | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.09847 | -0.09847 | -0.09847 |
| k0 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.0907 | -0.0907 | -0.0907 |
| k0 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.0907 | -0.0907 | -0.0907 |
| k0 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.0907 | -0.0907 | -0.0907 |
| k0 | M2 | Age and effort with child identity | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07571 | -0.07571 | -0.07571 |
| k0 | M2 | Age and effort with child identity | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07571 | -0.07571 | -0.07571 |
| k0 | M2 | Age and effort with child identity | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07571 | -0.07571 | -0.07571 |
| k0 | M2 | Age and effort with child identity | Words | 1-4 | 4 | 4 | 0 | -0.1582 | -0.1582 | -0.1582 |
| k0 | M2 | Age and effort with child identity | Words | 5-8 | 4 | 4 | 0 | -0.1582 | -0.1582 | -0.1582 |
| k0 | M2 | Age and effort with child identity | Words | 9-12 | 4 | 4 | 0 | -0.1582 | -0.1582 | -0.1582 |
| k0 | M3 | Age by effort | Morphemes | 1-4 | 4 | 4 | 0 | -0.1633 | -0.1938 | -0.1327 |
| k0 | M3 | Age by effort | Morphemes | 5-8 | 4 | 4 | 0 | -0.2447 | -0.2753 | -0.2142 |
| k0 | M3 | Age by effort | Morphemes | 9-12 | 4 | 4 | 0 | -0.3262 | -0.3567 | -0.2956 |
| k0 | M3 | Age by effort | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.07062 | -0.07835 | -0.06289 |
| k0 | M3 | Age by effort | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.09123 | -0.09896 | -0.0835 |
| k0 | M3 | Age by effort | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.1118 | -0.1196 | -0.1041 |
| k0 | M3 | Age by effort | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07771 | -0.09533 | -0.06009 |
| k0 | M3 | Age by effort | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.1247 | -0.1423 | -0.1071 |
| k0 | M3 | Age by effort | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.1717 | -0.1893 | -0.1541 |
| k0 | M3 | Age by effort | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06532 | -0.07729 | -0.05334 |
| k0 | M3 | Age by effort | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.09725 | -0.1092 | -0.08528 |
| k0 | M3 | Age by effort | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.1292 | -0.1412 | -0.1172 |
| k0 | M3 | Age by effort | Words | 1-4 | 4 | 4 | 0 | -0.1467 | -0.1906 | -0.1028 |
| k0 | M3 | Age by effort | Words | 5-8 | 4 | 4 | 0 | -0.2639 | -0.3078 | -0.2199 |
| k0 | M3 | Age by effort | Words | 9-12 | 4 | 4 | 0 | -0.381 | -0.425 | -0.3371 |
| k1 | M1 | Pooled age and effort | Morphemes | 1-4 | 4 | 4 | 0 | -0.02637 | -0.02637 | -0.02637 |
| k1 | M1 | Pooled age and effort | Morphemes | 5-8 | 4 | 4 | 0 | -0.02637 | -0.02637 | -0.02637 |
| k1 | M1 | Pooled age and effort | Morphemes | 9-12 | 4 | 4 | 0 | -0.02637 | -0.02637 | -0.02637 |
| k1 | M1 | Pooled age and effort | Phonemes | 1-4 representative ranks | 4 | 0 | 4 | 0.03523 | 0.03523 | 0.03523 |
| k1 | M1 | Pooled age and effort | Phonemes | 5-8 representative ranks | 4 | 0 | 4 | 0.03523 | 0.03523 | 0.03523 |
| k1 | M1 | Pooled age and effort | Phonemes | 9-12 representative ranks | 4 | 0 | 4 | 0.03523 | 0.03523 | 0.03523 |
| k1 | M1 | Pooled age and effort | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 0 | 4 | 0.01867 | 0.01867 | 0.01867 |
| k1 | M1 | Pooled age and effort | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 0 | 4 | 0.01867 | 0.01867 | 0.01867 |
| k1 | M1 | Pooled age and effort | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 0 | 4 | 0.01867 | 0.01867 | 0.01867 |
| k1 | M1 | Pooled age and effort | Syllables: pkg | 1-4 representative ranks | 4 | 0 | 4 | 0.03667 | 0.03667 | 0.03667 |
| k1 | M1 | Pooled age and effort | Syllables: pkg | 5-8 representative ranks | 4 | 0 | 4 | 0.03667 | 0.03667 | 0.03667 |
| k1 | M1 | Pooled age and effort | Syllables: pkg | 9-12 representative ranks | 4 | 0 | 4 | 0.03667 | 0.03667 | 0.03667 |
| k1 | M1 | Pooled age and effort | Words | 1-4 | 4 | 4 | 0 | -0.03427 | -0.03427 | -0.03427 |
| k1 | M1 | Pooled age and effort | Words | 5-8 | 4 | 4 | 0 | -0.03427 | -0.03427 | -0.03427 |
| k1 | M1 | Pooled age and effort | Words | 9-12 | 4 | 4 | 0 | -0.03427 | -0.03427 | -0.03427 |
| k1 | M2 | Age and effort with child identity | Morphemes | 1-4 | 4 | 4 | 0 | -0.1585 | -0.1585 | -0.1585 |
| k1 | M2 | Age and effort with child identity | Morphemes | 5-8 | 4 | 4 | 0 | -0.1585 | -0.1585 | -0.1585 |
| k1 | M2 | Age and effort with child identity | Morphemes | 9-12 | 4 | 4 | 0 | -0.1585 | -0.1585 | -0.1585 |
| k1 | M2 | Age and effort with child identity | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08519 | -0.08519 | -0.08519 |
| k1 | M2 | Age and effort with child identity | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08519 | -0.08519 | -0.08519 |
| k1 | M2 | Age and effort with child identity | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08519 | -0.08519 | -0.08519 |
| k1 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08207 | -0.08207 | -0.08207 |
| k1 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.08207 | -0.08207 | -0.08207 |
| k1 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.08207 | -0.08207 | -0.08207 |
| k1 | M2 | Age and effort with child identity | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k1 | M2 | Age and effort with child identity | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k1 | M2 | Age and effort with child identity | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k1 | M2 | Age and effort with child identity | Words | 1-4 | 4 | 4 | 0 | -0.1431 | -0.1431 | -0.1431 |
| k1 | M2 | Age and effort with child identity | Words | 5-8 | 4 | 4 | 0 | -0.1431 | -0.1431 | -0.1431 |
| k1 | M2 | Age and effort with child identity | Words | 9-12 | 4 | 4 | 0 | -0.1431 | -0.1431 | -0.1431 |
| k1 | M3 | Age by effort | Morphemes | 1-4 | 4 | 4 | 0 | -0.1561 | -0.1609 | -0.1513 |
| k1 | M3 | Age by effort | Morphemes | 5-8 | 4 | 4 | 0 | -0.1689 | -0.1737 | -0.1641 |
| k1 | M3 | Age by effort | Morphemes | 9-12 | 4 | 4 | 0 | -0.1817 | -0.1865 | -0.1769 |
| k1 | M3 | Age by effort | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08787 | -0.08861 | -0.08712 |
| k1 | M3 | Age by effort | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08589 | -0.08663 | -0.08515 |
| k1 | M3 | Age by effort | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08391 | -0.08465 | -0.08317 |
| k1 | M3 | Age by effort | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08394 | -0.08647 | -0.08141 |
| k1 | M3 | Age by effort | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07718 | -0.07972 | -0.07465 |
| k1 | M3 | Age by effort | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07042 | -0.07296 | -0.06789 |
| k1 | M3 | Age by effort | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07335 | -0.0804 | -0.06631 |
| k1 | M3 | Age by effort | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.05456 | -0.06161 | -0.04751 |
| k1 | M3 | Age by effort | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.03577 | -0.04282 | -0.02872 |
| k1 | M3 | Age by effort | Words | 1-4 | 4 | 4 | 0 | -0.1391 | -0.1542 | -0.1241 |
| k1 | M3 | Age by effort | Words | 5-8 | 4 | 4 | 0 | -0.1793 | -0.1944 | -0.1642 |
| k1 | M3 | Age by effort | Words | 9-12 | 4 | 4 | 0 | -0.2195 | -0.2345 | -0.2044 |
| k1 | M4E | Context entropy added | Morphemes | 1-4 | 4 | 4 | 0 | -0.1636 | -0.1636 | -0.1636 |
| k1 | M4E | Context entropy added | Morphemes | 5-8 | 4 | 4 | 0 | -0.1636 | -0.1636 | -0.1636 |
| k1 | M4E | Context entropy added | Morphemes | 9-12 | 4 | 4 | 0 | -0.1636 | -0.1636 | -0.1636 |
| k1 | M4E | Context entropy added | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08687 | -0.08687 | -0.08687 |
| k1 | M4E | Context entropy added | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08687 | -0.08687 | -0.08687 |
| k1 | M4E | Context entropy added | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08687 | -0.08687 | -0.08687 |
| k1 | M4E | Context entropy added | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08435 | -0.08435 | -0.08435 |
| k1 | M4E | Context entropy added | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.08435 | -0.08435 | -0.08435 |
| k1 | M4E | Context entropy added | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.08435 | -0.08435 | -0.08435 |
| k1 | M4E | Context entropy added | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06823 | -0.06823 | -0.06823 |
| k1 | M4E | Context entropy added | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06823 | -0.06823 | -0.06823 |
| k1 | M4E | Context entropy added | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06823 | -0.06823 | -0.06823 |
| k1 | M4E | Context entropy added | Words | 1-4 | 4 | 4 | 0 | -0.1481 | -0.1481 | -0.1481 |
| k1 | M4E | Context entropy added | Words | 5-8 | 4 | 4 | 0 | -0.1481 | -0.1481 | -0.1481 |
| k1 | M4E | Context entropy added | Words | 9-12 | 4 | 4 | 0 | -0.1481 | -0.1481 | -0.1481 |
| k1 | M4ES | Entropy plus matched context size | Morphemes | 1-4 | 4 | 4 | 0 | -0.1576 | -0.1576 | -0.1576 |
| k1 | M4ES | Entropy plus matched context size | Morphemes | 5-8 | 4 | 4 | 0 | -0.1576 | -0.1576 | -0.1576 |
| k1 | M4ES | Entropy plus matched context size | Morphemes | 9-12 | 4 | 4 | 0 | -0.1576 | -0.1576 | -0.1576 |
| k1 | M4ES | Entropy plus matched context size | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08125 | -0.08125 | -0.08125 |
| k1 | M4ES | Entropy plus matched context size | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08125 | -0.08125 | -0.08125 |
| k1 | M4ES | Entropy plus matched context size | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08125 | -0.08125 | -0.08125 |
| k1 | M4ES | Entropy plus matched context size | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07842 | -0.07842 | -0.07842 |
| k1 | M4ES | Entropy plus matched context size | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07842 | -0.07842 | -0.07842 |
| k1 | M4ES | Entropy plus matched context size | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07842 | -0.07842 | -0.07842 |
| k1 | M4ES | Entropy plus matched context size | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06222 | -0.06222 | -0.06222 |
| k1 | M4ES | Entropy plus matched context size | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06222 | -0.06222 | -0.06222 |
| k1 | M4ES | Entropy plus matched context size | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06222 | -0.06222 | -0.06222 |
| k1 | M4ES | Entropy plus matched context size | Words | 1-4 | 4 | 4 | 0 | -0.1414 | -0.1414 | -0.1414 |
| k1 | M4ES | Entropy plus matched context size | Words | 5-8 | 4 | 4 | 0 | -0.1414 | -0.1414 | -0.1414 |
| k1 | M4ES | Entropy plus matched context size | Words | 9-12 | 4 | 4 | 0 | -0.1414 | -0.1414 | -0.1414 |
| k1 | M4S | Matched context size added | Morphemes | 1-4 | 4 | 4 | 0 | -0.1562 | -0.1562 | -0.1562 |
| k1 | M4S | Matched context size added | Morphemes | 5-8 | 4 | 4 | 0 | -0.1562 | -0.1562 | -0.1562 |
| k1 | M4S | Matched context size added | Morphemes | 9-12 | 4 | 4 | 0 | -0.1562 | -0.1562 | -0.1562 |
| k1 | M4S | Matched context size added | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08311 | -0.08311 | -0.08311 |
| k1 | M4S | Matched context size added | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08311 | -0.08311 | -0.08311 |
| k1 | M4S | Matched context size added | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08311 | -0.08311 | -0.08311 |
| k1 | M4S | Matched context size added | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07966 | -0.07966 | -0.07966 |
| k1 | M4S | Matched context size added | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07966 | -0.07966 | -0.07966 |
| k1 | M4S | Matched context size added | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07966 | -0.07966 | -0.07966 |
| k1 | M4S | Matched context size added | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06479 | -0.06479 | -0.06479 |
| k1 | M4S | Matched context size added | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06479 | -0.06479 | -0.06479 |
| k1 | M4S | Matched context size added | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06479 | -0.06479 | -0.06479 |
| k1 | M4S | Matched context size added | Words | 1-4 | 4 | 4 | 0 | -0.1402 | -0.1402 | -0.1402 |
| k1 | M4S | Matched context size added | Words | 5-8 | 4 | 4 | 0 | -0.1402 | -0.1402 | -0.1402 |
| k1 | M4S | Matched context size added | Words | 9-12 | 4 | 4 | 0 | -0.1402 | -0.1402 | -0.1402 |
| k1 | M5E | Age by context entropy | Morphemes | 1-4 | 4 | 4 | 0 | -0.1647 | -0.1647 | -0.1647 |
| k1 | M5E | Age by context entropy | Morphemes | 5-8 | 4 | 4 | 0 | -0.1647 | -0.1647 | -0.1647 |
| k1 | M5E | Age by context entropy | Morphemes | 9-12 | 4 | 4 | 0 | -0.1647 | -0.1647 | -0.1647 |
| k1 | M5E | Age by context entropy | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08788 | -0.08788 | -0.08788 |
| k1 | M5E | Age by context entropy | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08788 | -0.08788 | -0.08788 |
| k1 | M5E | Age by context entropy | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08788 | -0.08788 | -0.08788 |
| k1 | M5E | Age by context entropy | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08541 | -0.08541 | -0.08541 |
| k1 | M5E | Age by context entropy | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.08541 | -0.08541 | -0.08541 |
| k1 | M5E | Age by context entropy | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.08541 | -0.08541 | -0.08541 |
| k1 | M5E | Age by context entropy | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06928 | -0.06928 | -0.06928 |
| k1 | M5E | Age by context entropy | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06928 | -0.06928 | -0.06928 |
| k1 | M5E | Age by context entropy | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06928 | -0.06928 | -0.06928 |
| k1 | M5E | Age by context entropy | Words | 1-4 | 4 | 4 | 0 | -0.1491 | -0.1491 | -0.1491 |
| k1 | M5E | Age by context entropy | Words | 5-8 | 4 | 4 | 0 | -0.1491 | -0.1491 | -0.1491 |
| k1 | M5E | Age by context entropy | Words | 9-12 | 4 | 4 | 0 | -0.1491 | -0.1491 | -0.1491 |
| k1 | M5ES | Age by entropy and size | Morphemes | 1-4 | 4 | 4 | 0 | -0.1584 | -0.1584 | -0.1584 |
| k1 | M5ES | Age by entropy and size | Morphemes | 5-8 | 4 | 4 | 0 | -0.1584 | -0.1584 | -0.1584 |
| k1 | M5ES | Age by entropy and size | Morphemes | 9-12 | 4 | 4 | 0 | -0.1584 | -0.1584 | -0.1584 |
| k1 | M5ES | Age by entropy and size | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.0821 | -0.0821 | -0.0821 |
| k1 | M5ES | Age by entropy and size | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.0821 | -0.0821 | -0.0821 |
| k1 | M5ES | Age by entropy and size | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.0821 | -0.0821 | -0.0821 |
| k1 | M5ES | Age by entropy and size | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07929 | -0.07929 | -0.07929 |
| k1 | M5ES | Age by entropy and size | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07929 | -0.07929 | -0.07929 |
| k1 | M5ES | Age by entropy and size | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07929 | -0.07929 | -0.07929 |
| k1 | M5ES | Age by entropy and size | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.0631 | -0.0631 | -0.0631 |
| k1 | M5ES | Age by entropy and size | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.0631 | -0.0631 | -0.0631 |
| k1 | M5ES | Age by entropy and size | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.0631 | -0.0631 | -0.0631 |
| k1 | M5ES | Age by entropy and size | Words | 1-4 | 4 | 4 | 0 | -0.1421 | -0.1421 | -0.1421 |
| k1 | M5ES | Age by entropy and size | Words | 5-8 | 4 | 4 | 0 | -0.1421 | -0.1421 | -0.1421 |
| k1 | M5ES | Age by entropy and size | Words | 9-12 | 4 | 4 | 0 | -0.1421 | -0.1421 | -0.1421 |
| k1 | M5S | Age by matched context size | Morphemes | 1-4 | 4 | 4 | 0 | -0.1553 | -0.1553 | -0.1553 |
| k1 | M5S | Age by matched context size | Morphemes | 5-8 | 4 | 4 | 0 | -0.1553 | -0.1553 | -0.1553 |
| k1 | M5S | Age by matched context size | Morphemes | 9-12 | 4 | 4 | 0 | -0.1553 | -0.1553 | -0.1553 |
| k1 | M5S | Age by matched context size | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08255 | -0.08255 | -0.08255 |
| k1 | M5S | Age by matched context size | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08255 | -0.08255 | -0.08255 |
| k1 | M5S | Age by matched context size | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08255 | -0.08255 | -0.08255 |
| k1 | M5S | Age by matched context size | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07905 | -0.07905 | -0.07905 |
| k1 | M5S | Age by matched context size | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07905 | -0.07905 | -0.07905 |
| k1 | M5S | Age by matched context size | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07905 | -0.07905 | -0.07905 |
| k1 | M5S | Age by matched context size | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06415 | -0.06415 | -0.06415 |
| k1 | M5S | Age by matched context size | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06415 | -0.06415 | -0.06415 |
| k1 | M5S | Age by matched context size | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06415 | -0.06415 | -0.06415 |
| k1 | M5S | Age by matched context size | Words | 1-4 | 4 | 4 | 0 | -0.1396 | -0.1396 | -0.1396 |
| k1 | M5S | Age by matched context size | Words | 5-8 | 4 | 4 | 0 | -0.1396 | -0.1396 | -0.1396 |
| k1 | M5S | Age by matched context size | Words | 9-12 | 4 | 4 | 0 | -0.1396 | -0.1396 | -0.1396 |
| k1 | M6E | Effort and entropy interactions | Morphemes | 1-4 | 4 | 4 | 0 | -0.163 | -0.166 | -0.16 |
| k1 | M6E | Effort and entropy interactions | Morphemes | 5-8 | 4 | 4 | 0 | -0.171 | -0.174 | -0.168 |
| k1 | M6E | Effort and entropy interactions | Morphemes | 9-12 | 4 | 4 | 0 | -0.179 | -0.182 | -0.176 |
| k1 | M6E | Effort and entropy interactions | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.09351 | -0.09512 | -0.09189 |
| k1 | M6E | Effort and entropy interactions | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.0892 | -0.09082 | -0.08759 |
| k1 | M6E | Effort and entropy interactions | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.0849 | -0.08651 | -0.08328 |
| k1 | M6E | Effort and entropy interactions | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08882 | -0.09379 | -0.08386 |
| k1 | M6E | Effort and entropy interactions | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07559 | -0.08055 | -0.07062 |
| k1 | M6E | Effort and entropy interactions | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06235 | -0.06732 | -0.05739 |
| k1 | M6E | Effort and entropy interactions | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07716 | -0.08668 | -0.06765 |
| k1 | M6E | Effort and entropy interactions | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.05178 | -0.0613 | -0.04227 |
| k1 | M6E | Effort and entropy interactions | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.0264 | -0.03592 | -0.01688 |
| k1 | M6E | Effort and entropy interactions | Words | 1-4 | 4 | 4 | 0 | -0.1457 | -0.1589 | -0.1325 |
| k1 | M6E | Effort and entropy interactions | Words | 5-8 | 4 | 4 | 0 | -0.1809 | -0.1941 | -0.1677 |
| k1 | M6E | Effort and entropy interactions | Words | 9-12 | 4 | 4 | 0 | -0.2162 | -0.2294 | -0.203 |
| k1 | M6ES | Interaction-rich entropy and size model | Morphemes | 1-4 | 4 | 4 | 0 | -0.1609 | -0.1641 | -0.1577 |
| k1 | M6ES | Interaction-rich entropy and size model | Morphemes | 5-8 | 4 | 4 | 0 | -0.1694 | -0.1726 | -0.1662 |
| k1 | M6ES | Interaction-rich entropy and size model | Morphemes | 9-12 | 4 | 4 | 0 | -0.1779 | -0.181 | -0.1747 |
| k1 | M6ES | Interaction-rich entropy and size model | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.09217 | -0.09381 | -0.09054 |
| k1 | M6ES | Interaction-rich entropy and size model | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08781 | -0.08944 | -0.08617 |
| k1 | M6ES | Interaction-rich entropy and size model | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08344 | -0.08508 | -0.0818 |
| k1 | M6ES | Interaction-rich entropy and size model | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08703 | -0.09202 | -0.08203 |
| k1 | M6ES | Interaction-rich entropy and size model | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.0737 | -0.0787 | -0.0687 |
| k1 | M6ES | Interaction-rich entropy and size model | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06037 | -0.06537 | -0.05538 |
| k1 | M6ES | Interaction-rich entropy and size model | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07514 | -0.08468 | -0.06561 |
| k1 | M6ES | Interaction-rich entropy and size model | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.04971 | -0.05925 | -0.04018 |
| k1 | M6ES | Interaction-rich entropy and size model | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.02428 | -0.03382 | -0.01475 |
| k1 | M6ES | Interaction-rich entropy and size model | Words | 1-4 | 4 | 4 | 0 | -0.1431 | -0.1562 | -0.1299 |
| k1 | M6ES | Interaction-rich entropy and size model | Words | 5-8 | 4 | 4 | 0 | -0.1781 | -0.1913 | -0.165 |
| k1 | M6ES | Interaction-rich entropy and size model | Words | 9-12 | 4 | 4 | 0 | -0.2132 | -0.2263 | -0.2 |
| k1 | M6S | Effort and context-size interactions | Morphemes | 1-4 | 4 | 4 | 0 | -0.1577 | -0.162 | -0.1534 |
| k1 | M6S | Effort and context-size interactions | Morphemes | 5-8 | 4 | 4 | 0 | -0.1691 | -0.1734 | -0.1648 |
| k1 | M6S | Effort and context-size interactions | Morphemes | 9-12 | 4 | 4 | 0 | -0.1805 | -0.1848 | -0.1762 |
| k1 | M6S | Effort and context-size interactions | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.09048 | -0.09145 | -0.08952 |
| k1 | M6S | Effort and context-size interactions | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08791 | -0.08888 | -0.08695 |
| k1 | M6S | Effort and context-size interactions | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08534 | -0.08631 | -0.08438 |
| k1 | M6S | Effort and context-size interactions | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08578 | -0.089 | -0.08256 |
| k1 | M6S | Effort and context-size interactions | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07718 | -0.08041 | -0.07396 |
| k1 | M6S | Effort and context-size interactions | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06859 | -0.07181 | -0.06537 |
| k1 | M6S | Effort and context-size interactions | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07509 | -0.08286 | -0.06732 |
| k1 | M6S | Effort and context-size interactions | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.05438 | -0.06215 | -0.04661 |
| k1 | M6S | Effort and context-size interactions | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.03367 | -0.04144 | -0.0259 |
| k1 | M6S | Effort and context-size interactions | Words | 1-4 | 4 | 4 | 0 | -0.1402 | -0.1545 | -0.1259 |
| k1 | M6S | Effort and context-size interactions | Words | 5-8 | 4 | 4 | 0 | -0.1783 | -0.1926 | -0.164 |
| k1 | M6S | Effort and context-size interactions | Words | 9-12 | 4 | 4 | 0 | -0.2165 | -0.2307 | -0.2022 |
| k2 | M1 | Pooled age and effort | Morphemes | 1-4 | 4 | 4 | 0 | -0.003091 | -0.003091 | -0.003091 |
| k2 | M1 | Pooled age and effort | Morphemes | 5-8 | 4 | 4 | 0 | -0.003091 | -0.003091 | -0.003091 |
| k2 | M1 | Pooled age and effort | Morphemes | 9-12 | 4 | 4 | 0 | -0.003091 | -0.003091 | -0.003091 |
| k2 | M1 | Pooled age and effort | Phonemes | 1-4 representative ranks | 4 | 0 | 4 | 0.05686 | 0.05686 | 0.05686 |
| k2 | M1 | Pooled age and effort | Phonemes | 5-8 representative ranks | 4 | 0 | 4 | 0.05686 | 0.05686 | 0.05686 |
| k2 | M1 | Pooled age and effort | Phonemes | 9-12 representative ranks | 4 | 0 | 4 | 0.05686 | 0.05686 | 0.05686 |
| k2 | M1 | Pooled age and effort | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 0 | 4 | 0.04012 | 0.04012 | 0.04012 |
| k2 | M1 | Pooled age and effort | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 0 | 4 | 0.04012 | 0.04012 | 0.04012 |
| k2 | M1 | Pooled age and effort | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 0 | 4 | 0.04012 | 0.04012 | 0.04012 |
| k2 | M1 | Pooled age and effort | Syllables: pkg | 1-4 representative ranks | 4 | 0 | 4 | 0.05785 | 0.05785 | 0.05785 |
| k2 | M1 | Pooled age and effort | Syllables: pkg | 5-8 representative ranks | 4 | 0 | 4 | 0.05785 | 0.05785 | 0.05785 |
| k2 | M1 | Pooled age and effort | Syllables: pkg | 9-12 representative ranks | 4 | 0 | 4 | 0.05785 | 0.05785 | 0.05785 |
| k2 | M1 | Pooled age and effort | Words | 1-4 | 4 | 4 | 0 | -0.01155 | -0.01155 | -0.01155 |
| k2 | M1 | Pooled age and effort | Words | 5-8 | 4 | 4 | 0 | -0.01155 | -0.01155 | -0.01155 |
| k2 | M1 | Pooled age and effort | Words | 9-12 | 4 | 4 | 0 | -0.01155 | -0.01155 | -0.01155 |
| k2 | M2 | Age and effort with child identity | Morphemes | 1-4 | 4 | 4 | 0 | -0.1425 | -0.1425 | -0.1425 |
| k2 | M2 | Age and effort with child identity | Morphemes | 5-8 | 4 | 4 | 0 | -0.1425 | -0.1425 | -0.1425 |
| k2 | M2 | Age and effort with child identity | Morphemes | 9-12 | 4 | 4 | 0 | -0.1425 | -0.1425 | -0.1425 |
| k2 | M2 | Age and effort with child identity | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.07096 | -0.07096 | -0.07096 |
| k2 | M2 | Age and effort with child identity | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.07096 | -0.07096 | -0.07096 |
| k2 | M2 | Age and effort with child identity | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.07096 | -0.07096 | -0.07096 |
| k2 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06903 | -0.06903 | -0.06903 |
| k2 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06903 | -0.06903 | -0.06903 |
| k2 | M2 | Age and effort with child identity | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06903 | -0.06903 | -0.06903 |
| k2 | M2 | Age and effort with child identity | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.0542 | -0.0542 | -0.0542 |
| k2 | M2 | Age and effort with child identity | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.0542 | -0.0542 | -0.0542 |
| k2 | M2 | Age and effort with child identity | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.0542 | -0.0542 | -0.0542 |
| k2 | M2 | Age and effort with child identity | Words | 1-4 | 4 | 4 | 0 | -0.1287 | -0.1287 | -0.1287 |
| k2 | M2 | Age and effort with child identity | Words | 5-8 | 4 | 4 | 0 | -0.1287 | -0.1287 | -0.1287 |
| k2 | M2 | Age and effort with child identity | Words | 9-12 | 4 | 4 | 0 | -0.1287 | -0.1287 | -0.1287 |
| k2 | M3 | Age by effort | Morphemes | 1-4 | 4 | 4 | 0 | -0.143 | -0.1439 | -0.1421 |
| k2 | M3 | Age by effort | Morphemes | 5-8 | 4 | 4 | 0 | -0.1405 | -0.1414 | -0.1395 |
| k2 | M3 | Age by effort | Morphemes | 9-12 | 4 | 4 | 0 | -0.138 | -0.1389 | -0.137 |
| k2 | M3 | Age by effort | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08214 | -0.08525 | -0.07904 |
| k2 | M3 | Age by effort | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.07386 | -0.07697 | -0.07076 |

## Figures

How to read every figure: each colored line is an exact fixed effort value. The shaded band is the model-confidence band for the fitted mean. Context predictors in prediction slices are held at their fitted-data means, so the line isolates age at fixed target effort under average context conditions.

### K0

#### M1

##### M1: Pooled age and effort

Formula: `sum_bits ~ age_c + target_effort_c`

Context variant: `none`

**Morphemes**

![k0 M1 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 M1 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 M1 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 M1 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 M1 Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_words_fixed_effort_atlas.png)

#### M2

##### M2: Age and effort with child identity

Formula: `sum_bits ~ age_c + target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k0 M2 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 M2 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 M2 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 M2 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 M2 Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_words_fixed_effort_atlas.png)

#### M3

##### M3: Age by effort

Formula: `sum_bits ~ age_c * target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k0 M3 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 M3 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 M3 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 M3 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 M3 Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_words_fixed_effort_atlas.png)

### K1

#### M1

##### M1: Pooled age and effort

Formula: `sum_bits ~ age_c + target_effort_c`

Context variant: `none`

**Morphemes**

![k1 M1 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M1 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M1 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M1 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M1 Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_words_fixed_effort_atlas.png)

#### M2

##### M2: Age and effort with child identity

Formula: `sum_bits ~ age_c + target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k1 M2 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M2 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M2 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M2 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M2 Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_words_fixed_effort_atlas.png)

#### M3

##### M3: Age by effort

Formula: `sum_bits ~ age_c * target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k1 M3 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M3 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M3 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M3 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M3 Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_words_fixed_effort_atlas.png)

#### M4

##### M4E: Context entropy added

Formula: `sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k1 M4E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M4E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M4E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M4E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M4E Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_words_fixed_effort_atlas.png)

##### M4ES: Entropy plus matched context size

Formula: `sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k1 M4ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M4ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M4ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M4ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M4ES Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_words_fixed_effort_atlas.png)

##### M4S: Matched context size added

Formula: `sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k1 M4S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M4S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M4S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M4S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M4S Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_words_fixed_effort_atlas.png)

#### M5

##### M5E: Age by context entropy

Formula: `sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k1 M5E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M5E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M5E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M5E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M5E Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_words_fixed_effort_atlas.png)

##### M5ES: Age by entropy and size

Formula: `sum_bits ~ age_c * context_entropy_c + age_c * context_size_c + target_effort_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k1 M5ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M5ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M5ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M5ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M5ES Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_words_fixed_effort_atlas.png)

##### M5S: Age by matched context size

Formula: `sum_bits ~ age_c * context_size_c + target_effort_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k1 M5S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M5S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M5S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M5S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M5S Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_words_fixed_effort_atlas.png)

#### M6

##### M6E: Effort and entropy interactions

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k1 M6E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M6E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M6E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M6E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M6E Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_words_fixed_effort_atlas.png)

##### M6ES: Interaction-rich entropy and size model

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + age_c * context_size_c + target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k1 M6ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M6ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M6ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M6ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M6ES Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_words_fixed_effort_atlas.png)

##### M6S: Effort and context-size interactions

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_size_c + target_effort_c * context_size_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k1 M6S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M6S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M6S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M6S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M6S Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_words_fixed_effort_atlas.png)

### K2

#### M1

##### M1: Pooled age and effort

Formula: `sum_bits ~ age_c + target_effort_c`

Context variant: `none`

**Morphemes**

![k2 M1 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M1 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M1 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M1 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M1 Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_words_fixed_effort_atlas.png)

#### M2

##### M2: Age and effort with child identity

Formula: `sum_bits ~ age_c + target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k2 M2 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M2 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M2 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M2 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M2 Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_words_fixed_effort_atlas.png)

#### M3

##### M3: Age by effort

Formula: `sum_bits ~ age_c * target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k2 M3 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M3 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M3 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M3 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M3 Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_words_fixed_effort_atlas.png)

#### M4

##### M4E: Context entropy added

Formula: `sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k2 M4E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M4E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M4E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M4E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M4E Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_words_fixed_effort_atlas.png)

##### M4ES: Entropy plus matched context size

Formula: `sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k2 M4ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M4ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M4ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M4ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M4ES Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_words_fixed_effort_atlas.png)

##### M4S: Matched context size added

Formula: `sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k2 M4S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M4S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M4S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M4S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M4S Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_words_fixed_effort_atlas.png)

#### M5

##### M5E: Age by context entropy

Formula: `sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k2 M5E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M5E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M5E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M5E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M5E Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_words_fixed_effort_atlas.png)

##### M5ES: Age by entropy and size

Formula: `sum_bits ~ age_c * context_entropy_c + age_c * context_size_c + target_effort_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k2 M5ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M5ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M5ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M5ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M5ES Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_words_fixed_effort_atlas.png)

##### M5S: Age by matched context size

Formula: `sum_bits ~ age_c * context_size_c + target_effort_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k2 M5S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M5S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M5S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M5S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M5S Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_words_fixed_effort_atlas.png)

#### M6

##### M6E: Effort and entropy interactions

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k2 M6E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M6E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M6E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M6E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M6E Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_words_fixed_effort_atlas.png)

##### M6ES: Interaction-rich entropy and size model

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + age_c * context_size_c + target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k2 M6ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M6ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M6ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M6ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M6ES Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_words_fixed_effort_atlas.png)

##### M6S: Effort and context-size interactions

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_size_c + target_effort_c * context_size_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k2 M6S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M6S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M6S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M6S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M6S Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_words_fixed_effort_atlas.png)

### K3

#### M1

##### M1: Pooled age and effort

Formula: `sum_bits ~ age_c + target_effort_c`

Context variant: `none`

**Morphemes**

![k3 M1 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M1 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M1 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M1 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M1 Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_words_fixed_effort_atlas.png)

#### M2

##### M2: Age and effort with child identity

Formula: `sum_bits ~ age_c + target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k3 M2 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M2 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M2 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M2 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M2 Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_words_fixed_effort_atlas.png)

#### M3

##### M3: Age by effort

Formula: `sum_bits ~ age_c * target_effort_c + C(child_id)`

Context variant: `none`

**Morphemes**

![k3 M3 Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M3 Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M3 Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M3 Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M3 Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_words_fixed_effort_atlas.png)

#### M4

##### M4E: Context entropy added

Formula: `sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k3 M4E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M4E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M4E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M4E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M4E Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_words_fixed_effort_atlas.png)

##### M4ES: Entropy plus matched context size

Formula: `sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k3 M4ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M4ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M4ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M4ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M4ES Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_words_fixed_effort_atlas.png)

##### M4S: Matched context size added

Formula: `sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k3 M4S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M4S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M4S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M4S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M4S Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_words_fixed_effort_atlas.png)

#### M5

##### M5E: Age by context entropy

Formula: `sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k3 M5E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M5E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M5E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M5E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M5E Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_words_fixed_effort_atlas.png)

##### M5ES: Age by entropy and size

Formula: `sum_bits ~ age_c * context_entropy_c + age_c * context_size_c + target_effort_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k3 M5ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M5ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M5ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M5ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M5ES Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_words_fixed_effort_atlas.png)

##### M5S: Age by matched context size

Formula: `sum_bits ~ age_c * context_size_c + target_effort_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k3 M5S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M5S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M5S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M5S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M5S Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_words_fixed_effort_atlas.png)

#### M6

##### M6E: Effort and entropy interactions

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id)`

Context variant: `entropy`

**Morphemes**

![k3 M6E Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M6E Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M6E Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M6E Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M6E Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_words_fixed_effort_atlas.png)

##### M6ES: Interaction-rich entropy and size model

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + age_c * context_size_c + target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id)`

Context variant: `entropy_plus_size`

**Morphemes**

![k3 M6ES Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M6ES Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M6ES Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M6ES Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M6ES Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_words_fixed_effort_atlas.png)

##### M6S: Effort and context-size interactions

Formula: `sum_bits ~ age_c * target_effort_c + age_c * context_size_c + target_effort_c * context_size_c + C(child_id)`

Context variant: `context_size`

**Morphemes**

![k3 M6S Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M6S Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M6S Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M6S Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M6S Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_words_fixed_effort_atlas.png)

## Skipped Rows

Expected skipped rows are mostly k0 context variants: k0 has no context entropy or context size.

| context_k | model_id | model_label | effort_label | status | error |
| --- | --- | --- | --- | --- | --- |
| k0 | M4E | Context entropy added | Words | skipped | k0 has no context predictors |
| k0 | M4S | Matched context size added | Words | skipped | k0 has no context predictors |
| k0 | M4ES | Entropy plus matched context size | Words | skipped | k0 has no context predictors |
| k0 | M5E | Age by context entropy | Words | skipped | k0 has no context predictors |
| k0 | M5S | Age by matched context size | Words | skipped | k0 has no context predictors |
| k0 | M5ES | Age by entropy and size | Words | skipped | k0 has no context predictors |
| k0 | M6E | Effort and entropy interactions | Words | skipped | k0 has no context predictors |
| k0 | M6S | Effort and context-size interactions | Words | skipped | k0 has no context predictors |
| k0 | M6ES | Interaction-rich entropy and size model | Words | skipped | k0 has no context predictors |
| k0 | M4E | Context entropy added | Morphemes | skipped | k0 has no context predictors |
| k0 | M4S | Matched context size added | Morphemes | skipped | k0 has no context predictors |
| k0 | M4ES | Entropy plus matched context size | Morphemes | skipped | k0 has no context predictors |
| k0 | M5E | Age by context entropy | Morphemes | skipped | k0 has no context predictors |
| k0 | M5S | Age by matched context size | Morphemes | skipped | k0 has no context predictors |
| k0 | M5ES | Age by entropy and size | Morphemes | skipped | k0 has no context predictors |
| k0 | M6E | Effort and entropy interactions | Morphemes | skipped | k0 has no context predictors |
| k0 | M6S | Effort and context-size interactions | Morphemes | skipped | k0 has no context predictors |
| k0 | M6ES | Interaction-rich entropy and size model | Morphemes | skipped | k0 has no context predictors |
| k0 | M4E | Context entropy added | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M4S | Matched context size added | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M4ES | Entropy plus matched context size | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M5E | Age by context entropy | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M5S | Age by matched context size | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M5ES | Age by entropy and size | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M6E | Effort and entropy interactions | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M6S | Effort and context-size interactions | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M6ES | Interaction-rich entropy and size model | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | M4E | Context entropy added | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M4S | Matched context size added | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M4ES | Entropy plus matched context size | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M5E | Age by context entropy | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M5S | Age by matched context size | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M5ES | Age by entropy and size | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M6E | Effort and entropy interactions | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M6S | Effort and context-size interactions | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M6ES | Interaction-rich entropy and size model | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | M4E | Context entropy added | Phonemes | skipped | k0 has no context predictors |
| k0 | M4S | Matched context size added | Phonemes | skipped | k0 has no context predictors |
| k0 | M4ES | Entropy plus matched context size | Phonemes | skipped | k0 has no context predictors |
| k0 | M5E | Age by context entropy | Phonemes | skipped | k0 has no context predictors |
| k0 | M5S | Age by matched context size | Phonemes | skipped | k0 has no context predictors |
| k0 | M5ES | Age by entropy and size | Phonemes | skipped | k0 has no context predictors |
| k0 | M6E | Effort and entropy interactions | Phonemes | skipped | k0 has no context predictors |
| k0 | M6S | Effort and context-size interactions | Phonemes | skipped | k0 has no context predictors |
| k0 | M6ES | Interaction-rich entropy and size model | Phonemes | skipped | k0 has no context predictors |

## Saved Outputs

```text
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_model_summary.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_bin_definitions.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_predictions.csv.gz
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_slice_slopes.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_figure_manifest.csv
figs/context_m1_m6_fixed_effort_atlas/
```