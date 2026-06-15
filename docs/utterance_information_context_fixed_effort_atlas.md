# Context Predictors: Fixed-Effort Atlas

This internal report adds the fixed-effort slice views that were missing from the context-predictor reports.
The models are fit on all eligible utterances. The fixed effort values only define the plotted prediction slices.

## Model Families

| id | question | formula |
| --- | --- | --- |
| CF0 | What is the age trajectory at fixed target effort, before adding context predictors? | `sum_bits ~ age_c + target_effort_c + C(child_id)` |
| CF1 | Does the fixed-effort age trajectory remain after controlling context entropy? | `sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)` |
| CF2 | Does the fixed-effort age trajectory remain after controlling the matching context-size unit? | `sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)` |
| CF3 | Does the fixed-effort age trajectory remain after controlling both context entropy and matching context size? | `sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)` |

Implementation for all fitted rows: linear OLS via `statsmodels.formula.api.ols`, with child-cluster robust standard errors (`cov_type='cluster'`, cluster unit `child_id`).
Context-size models use the context-size unit that matches the target effort unit: target words use context words, target phonemes use context phonemes, and so on. The broader coefficient report still contains every cross-unit context-size permutation.

## Fixed-Effort Slice Definitions

For words and morphemes, the panels are exact fixed values 1-4, 5-8, and 9-12. For syllables and phonemes, the panels are the 12 most frequent exact values split into three ordered groups of four, matching the earlier fixed-effort atlas logic.

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

## Model Overview

How to read: `negative_age_coef_rows` counts how many effort-unit rows have a negative fitted age coefficient. `significant_age_rows` counts how many have p<.05 for age. R2 is in-sample fitted-versus-observed fit.

| context_k | model_id | model_label | fitted_rows | mean_r2 | negative_age_coef_rows | significant_age_rows |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | CF0 | Baseline controls | 5 | 0.736 | 5 | 5 |
| k1 | CF0 | Baseline controls | 5 | 0.6586 | 5 | 5 |
| k1 | CF1 | Entropy only | 5 | 0.6585 | 5 | 5 |
| k1 | CF2 | Matched context size only | 5 | 0.6599 | 5 | 5 |
| k1 | CF3 | Entropy plus matched context size | 5 | 0.6594 | 5 | 5 |
| k2 | CF0 | Baseline controls | 5 | 0.6408 | 5 | 5 |
| k2 | CF1 | Entropy only | 5 | 0.6413 | 5 | 5 |
| k2 | CF2 | Matched context size only | 5 | 0.6418 | 5 | 5 |
| k2 | CF3 | Entropy plus matched context size | 5 | 0.6416 | 5 | 5 |
| k3 | CF0 | Baseline controls | 5 | 0.6318 | 5 | 5 |
| k3 | CF1 | Entropy only | 5 | 0.6325 | 5 | 5 |
| k3 | CF2 | Matched context size only | 5 | 0.633 | 5 | 5 |
| k3 | CF3 | Entropy plus matched context size | 5 | 0.6327 | 5 | 4 |

## Coefficient Table

How to read: coefficients are in Mistral bits. `age_coef` is bits per month after the listed controls. `target_effort_coef` is bits per added target effort unit. `context_entropy_coef` is bits per additional entropy bit. `context_size_coef` is bits per additional matched context-size unit.

| context_k | model_id | model_label | effort_label | context_size_label | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | CF0 | Baseline controls | Words |  | 4.47e+05 | 21 | 0.7252 | -0.1582 | <.001 | 7.127 | <.001 |  |  |  |  |
| k0 | CF0 | Baseline controls | Morphemes |  | 4.47e+05 | 21 | 0.7204 | -0.1784 | <.001 | 6.195 | <.001 |  |  |  |  |
| k0 | CF0 | Baseline controls | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.7461 | -0.0907 | 0.003 | 5.848 | <.001 |  |  |  |  |
| k0 | CF0 | Baseline controls | Syllables: pkg |  | 4.47e+05 | 21 | 0.7303 | -0.07571 | 0.009 | 5.411 | <.001 |  |  |  |  |
| k0 | CF0 | Baseline controls | Phonemes |  | 4.47e+05 | 21 | 0.7578 | -0.09847 | 0.001 | 2.352 | <.001 |  |  |  |  |
| k1 | CF0 | Baseline controls | Words |  | 4.47e+05 | 21 | 0.6495 | -0.1431 | <.001 | 6.677 | <.001 |  |  |  |  |
| k1 | CF1 | Entropy only | Words |  | 4.422e+05 | 21 | 0.6495 | -0.1481 | <.001 | 6.68 | <.001 | 0.05917 | 0.274 |  |  |
| k1 | CF2 | Matched context size only | Words | Context words | 4.443e+05 | 21 | 0.651 | -0.1402 | <.001 | 6.671 | <.001 |  |  | -0.175 | <.001 |
| k1 | CF3 | Entropy plus matched context size | Words | Context words | 4.422e+05 | 21 | 0.6506 | -0.1414 | <.001 | 6.679 | <.001 | -0.06001 | 0.247 | -0.1813 | <.001 |
| k1 | CF0 | Baseline controls | Morphemes |  | 4.47e+05 | 21 | 0.639 | -0.1585 | <.001 | 5.772 | <.001 |  |  |  |  |
| k1 | CF1 | Entropy only | Morphemes |  | 4.422e+05 | 21 | 0.6388 | -0.1636 | <.001 | 5.773 | <.001 | 0.06736 | 0.206 |  |  |
| k1 | CF2 | Matched context size only | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6403 | -0.1562 | <.001 | 5.767 | <.001 |  |  | -0.1421 | <.001 |
| k1 | CF3 | Entropy plus matched context size | Morphemes | Context morphemes | 4.422e+05 | 21 | 0.6397 | -0.1576 | <.001 | 5.772 | <.001 | -0.0464 | 0.357 | -0.1462 | <.001 |
| k1 | CF0 | Baseline controls | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6729 | -0.08207 | <.001 | 5.502 | <.001 |  |  |  |  |
| k1 | CF1 | Entropy only | Syllables: CMU/pkg |  | 4.422e+05 | 21 | 0.6728 | -0.08435 | <.001 | 5.502 | <.001 | 0.06356 | 0.204 |  |  |
| k1 | CF2 | Matched context size only | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6741 | -0.07966 | <.001 | 5.497 | <.001 |  |  | -0.1263 | <.001 |
| k1 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.422e+05 | 21 | 0.6737 | -0.07842 | <.001 | 5.501 | <.001 | -0.03417 | 0.477 | -0.1285 | <.001 |
| k1 | CF0 | Baseline controls | Syllables: pkg |  | 4.47e+05 | 21 | 0.6572 | -0.06724 | 0.001 | 5.084 | <.001 |  |  |  |  |
| k1 | CF1 | Entropy only | Syllables: pkg |  | 4.422e+05 | 21 | 0.6571 | -0.06823 | <.001 | 5.083 | <.001 | 0.04786 | 0.346 |  |  |
| k1 | CF2 | Matched context size only | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6585 | -0.06479 | 0.002 | 5.078 | <.001 |  |  | -0.1208 | <.001 |
| k1 | CF3 | Entropy plus matched context size | Syllables: pkg | Context syllables: pkg | 4.422e+05 | 21 | 0.658 | -0.06222 | 0.002 | 5.081 | <.001 | -0.05367 | 0.281 | -0.1244 | <.001 |
| k1 | CF0 | Baseline controls | Phonemes |  | 4.47e+05 | 21 | 0.6743 | -0.08519 | <.001 | 2.196 | <.001 |  |  |  |  |
| k1 | CF1 | Entropy only | Phonemes |  | 4.422e+05 | 21 | 0.6743 | -0.08687 | <.001 | 2.196 | <.001 | 0.02783 | 0.548 |  |  |
| k1 | CF2 | Matched context size only | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6755 | -0.08311 | <.001 | 2.194 | <.001 |  |  | -0.04665 | <.001 |
| k1 | CF3 | Entropy plus matched context size | Phonemes | Context phonemes | 4.422e+05 | 21 | 0.6751 | -0.08125 | <.001 | 2.195 | <.001 | -0.06489 | 0.143 | -0.04865 | <.001 |
| k2 | CF0 | Baseline controls | Words |  | 4.47e+05 | 21 | 0.6338 | -0.1287 | <.001 | 6.468 | <.001 |  |  |  |  |
| k2 | CF1 | Entropy only | Words |  | 4.415e+05 | 21 | 0.6343 | -0.1318 | <.001 | 6.47 | <.001 | -0.4107 | <.001 |  |  |
| k2 | CF2 | Matched context size only | Words | Context words | 4.443e+05 | 21 | 0.635 | -0.1289 | <.001 | 6.464 | <.001 |  |  | -0.07164 | <.001 |
| k2 | CF3 | Entropy plus matched context size | Words | Context words | 4.415e+05 | 21 | 0.6347 | -0.1273 | <.001 | 6.47 | <.001 | -0.4087 | <.001 | -0.06994 | <.001 |
| k2 | CF0 | Baseline controls | Morphemes |  | 4.47e+05 | 21 | 0.6217 | -0.1425 | <.001 | 5.581 | <.001 |  |  |  |  |
| k2 | CF1 | Entropy only | Morphemes |  | 4.415e+05 | 21 | 0.622 | -0.1458 | <.001 | 5.582 | <.001 | -0.4256 | <.001 |  |  |
| k2 | CF2 | Matched context size only | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6227 | -0.1433 | <.001 | 5.577 | <.001 |  |  | -0.05554 | <.001 |
| k2 | CF3 | Entropy plus matched context size | Morphemes | Context morphemes | 4.415e+05 | 21 | 0.6223 | -0.142 | <.001 | 5.582 | <.001 | -0.4253 | <.001 | -0.05438 | <.001 |
| k2 | CF0 | Baseline controls | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6551 | -0.06903 | 0.007 | 5.323 | <.001 |  |  |  |  |
| k2 | CF1 | Entropy only | Syllables: CMU/pkg |  | 4.415e+05 | 21 | 0.6557 | -0.06891 | 0.006 | 5.324 | <.001 | -0.4558 | <.001 |  |  |
| k2 | CF2 | Matched context size only | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6561 | -0.06963 | 0.007 | 5.319 | <.001 |  |  | -0.04898 | <.001 |
| k2 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.415e+05 | 21 | 0.656 | -0.06519 | 0.009 | 5.324 | <.001 | -0.4521 | <.001 | -0.04709 | <.001 |
| k2 | CF0 | Baseline controls | Syllables: pkg |  | 4.47e+05 | 21 | 0.639 | -0.0542 | 0.021 | 4.914 | <.001 |  |  |  |  |
| k2 | CF1 | Entropy only | Syllables: pkg |  | 4.415e+05 | 21 | 0.6396 | -0.05248 | 0.017 | 4.913 | <.001 | -0.4543 | <.001 |  |  |
| k2 | CF2 | Matched context size only | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.64 | -0.05479 | 0.021 | 4.909 | <.001 |  |  | -0.04671 | <.001 |
| k2 | CF3 | Entropy plus matched context size | Syllables: pkg | Context syllables: pkg | 4.415e+05 | 21 | 0.6399 | -0.04875 | 0.027 | 4.913 | <.001 | -0.4506 | <.001 | -0.04487 | <.001 |
| k2 | CF0 | Baseline controls | Phonemes |  | 4.47e+05 | 21 | 0.6542 | -0.07096 | 0.005 | 2.12 | <.001 |  |  |  |  |
| k2 | CF1 | Entropy only | Phonemes |  | 4.415e+05 | 21 | 0.6549 | -0.06995 | 0.006 | 2.12 | <.001 | -0.4942 | <.001 |  |  |
| k2 | CF2 | Matched context size only | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6552 | -0.0717 | 0.005 | 2.118 | <.001 |  |  | -0.01841 | <.001 |
| k2 | CF3 | Entropy plus matched context size | Phonemes | Context phonemes | 4.415e+05 | 21 | 0.6551 | -0.0665 | 0.008 | 2.12 | <.001 | -0.4898 | <.001 | -0.01751 | <.001 |
| k3 | CF0 | Baseline controls | Words |  | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |
| k3 | CF1 | Entropy only | Words |  | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |
| k3 | CF2 | Matched context size only | Words | Context words | 4.443e+05 | 21 | 0.6272 | -0.1239 | <.001 | 6.363 | <.001 |  |  | -0.04386 | <.001 |
| k3 | CF3 | Entropy plus matched context size | Words | Context words | 4.414e+05 | 21 | 0.6268 | -0.123 | <.001 | 6.368 | <.001 | -0.4699 | <.001 | -0.0427 | <.001 |
| k3 | CF0 | Baseline controls | Morphemes |  | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |
| k3 | CF1 | Entropy only | Morphemes |  | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |
| k3 | CF2 | Matched context size only | Morphemes | Context morphemes | 4.443e+05 | 21 | 0.6142 | -0.1375 | <.001 | 5.485 | <.001 |  |  | -0.03407 | <.001 |
| k3 | CF3 | Entropy plus matched context size | Morphemes | Context morphemes | 4.414e+05 | 21 | 0.6138 | -0.1369 | <.001 | 5.489 | <.001 | -0.5111 | <.001 | -0.03298 | <.001 |
| k3 | CF0 | Baseline controls | Syllables: CMU/pkg |  | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |
| k3 | CF1 | Entropy only | Syllables: CMU/pkg |  | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |
| k3 | CF2 | Matched context size only | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.443e+05 | 21 | 0.6471 | -0.06497 | 0.016 | 5.232 | <.001 |  |  | -0.02985 | <.001 |
| k3 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | Context syllables: CMU/pkg | 4.414e+05 | 21 | 0.6469 | -0.06126 | 0.018 | 5.235 | <.001 | -0.5362 | <.001 | -0.02838 | <.001 |
| k3 | CF0 | Baseline controls | Syllables: pkg |  | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |
| k3 | CF1 | Entropy only | Syllables: pkg |  | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |
| k3 | CF2 | Matched context size only | Syllables: pkg | Context syllables: pkg | 4.443e+05 | 21 | 0.6308 | -0.05014 | 0.044 | 4.827 | <.001 |  |  | -0.0288 | <.001 |
| k3 | CF3 | Entropy plus matched context size | Syllables: pkg | Context syllables: pkg | 4.414e+05 | 21 | 0.6306 | -0.04483 | 0.052 | 4.829 | <.001 | -0.537 | <.001 | -0.02722 | <.001 |
| k3 | CF0 | Baseline controls | Phonemes |  | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |
| k3 | CF1 | Entropy only | Phonemes |  | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |
| k3 | CF2 | Matched context size only | Phonemes | Context phonemes | 4.443e+05 | 21 | 0.6455 | -0.06667 | 0.013 | 2.082 | <.001 |  |  | -0.01139 | <.001 |
| k3 | CF3 | Entropy plus matched context size | Phonemes | Context phonemes | 4.414e+05 | 21 | 0.6455 | -0.06221 | 0.016 | 2.084 | <.001 | -0.577 | <.001 | -0.0106 | <.001 |

## Fixed-Effort Slope Summary

How to read: these slopes are descriptive summaries of the plotted prediction lines, not separate inferential models. Inference comes from the coefficient table above.

| context_k | model_id | model_label | effort_label | atlas_bin | n_fixed_slices | negative_slices | positive_slices | mean_slope_bits_per_month | min_slope_bits_per_month | max_slope_bits_per_month |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | CF0 | Baseline controls | Morphemes | 1-4 | 4 | 4 | 0 | -0.1784 | -0.1784 | -0.1784 |
| k0 | CF0 | Baseline controls | Morphemes | 5-8 | 4 | 4 | 0 | -0.1784 | -0.1784 | -0.1784 |
| k0 | CF0 | Baseline controls | Morphemes | 9-12 | 4 | 4 | 0 | -0.1784 | -0.1784 | -0.1784 |
| k0 | CF0 | Baseline controls | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.09847 | -0.09847 | -0.09847 |
| k0 | CF0 | Baseline controls | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.09847 | -0.09847 | -0.09847 |
| k0 | CF0 | Baseline controls | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.09847 | -0.09847 | -0.09847 |
| k0 | CF0 | Baseline controls | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.0907 | -0.0907 | -0.0907 |
| k0 | CF0 | Baseline controls | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.0907 | -0.0907 | -0.0907 |
| k0 | CF0 | Baseline controls | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.0907 | -0.0907 | -0.0907 |
| k0 | CF0 | Baseline controls | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07571 | -0.07571 | -0.07571 |
| k0 | CF0 | Baseline controls | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07571 | -0.07571 | -0.07571 |
| k0 | CF0 | Baseline controls | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07571 | -0.07571 | -0.07571 |
| k0 | CF0 | Baseline controls | Words | 1-4 | 4 | 4 | 0 | -0.1582 | -0.1582 | -0.1582 |
| k0 | CF0 | Baseline controls | Words | 5-8 | 4 | 4 | 0 | -0.1582 | -0.1582 | -0.1582 |
| k0 | CF0 | Baseline controls | Words | 9-12 | 4 | 4 | 0 | -0.1582 | -0.1582 | -0.1582 |
| k1 | CF0 | Baseline controls | Morphemes | 1-4 | 4 | 4 | 0 | -0.1585 | -0.1585 | -0.1585 |
| k1 | CF0 | Baseline controls | Morphemes | 5-8 | 4 | 4 | 0 | -0.1585 | -0.1585 | -0.1585 |
| k1 | CF0 | Baseline controls | Morphemes | 9-12 | 4 | 4 | 0 | -0.1585 | -0.1585 | -0.1585 |
| k1 | CF0 | Baseline controls | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08519 | -0.08519 | -0.08519 |
| k1 | CF0 | Baseline controls | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08519 | -0.08519 | -0.08519 |
| k1 | CF0 | Baseline controls | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08519 | -0.08519 | -0.08519 |
| k1 | CF0 | Baseline controls | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08207 | -0.08207 | -0.08207 |
| k1 | CF0 | Baseline controls | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.08207 | -0.08207 | -0.08207 |
| k1 | CF0 | Baseline controls | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.08207 | -0.08207 | -0.08207 |
| k1 | CF0 | Baseline controls | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k1 | CF0 | Baseline controls | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k1 | CF0 | Baseline controls | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06724 | -0.06724 | -0.06724 |
| k1 | CF0 | Baseline controls | Words | 1-4 | 4 | 4 | 0 | -0.1431 | -0.1431 | -0.1431 |
| k1 | CF0 | Baseline controls | Words | 5-8 | 4 | 4 | 0 | -0.1431 | -0.1431 | -0.1431 |
| k1 | CF0 | Baseline controls | Words | 9-12 | 4 | 4 | 0 | -0.1431 | -0.1431 | -0.1431 |
| k1 | CF1 | Entropy only | Morphemes | 1-4 | 4 | 4 | 0 | -0.1636 | -0.1636 | -0.1636 |
| k1 | CF1 | Entropy only | Morphemes | 5-8 | 4 | 4 | 0 | -0.1636 | -0.1636 | -0.1636 |
| k1 | CF1 | Entropy only | Morphemes | 9-12 | 4 | 4 | 0 | -0.1636 | -0.1636 | -0.1636 |
| k1 | CF1 | Entropy only | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08687 | -0.08687 | -0.08687 |
| k1 | CF1 | Entropy only | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08687 | -0.08687 | -0.08687 |
| k1 | CF1 | Entropy only | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08687 | -0.08687 | -0.08687 |
| k1 | CF1 | Entropy only | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.08435 | -0.08435 | -0.08435 |
| k1 | CF1 | Entropy only | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.08435 | -0.08435 | -0.08435 |
| k1 | CF1 | Entropy only | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.08435 | -0.08435 | -0.08435 |
| k1 | CF1 | Entropy only | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06823 | -0.06823 | -0.06823 |
| k1 | CF1 | Entropy only | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06823 | -0.06823 | -0.06823 |
| k1 | CF1 | Entropy only | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06823 | -0.06823 | -0.06823 |
| k1 | CF1 | Entropy only | Words | 1-4 | 4 | 4 | 0 | -0.1481 | -0.1481 | -0.1481 |
| k1 | CF1 | Entropy only | Words | 5-8 | 4 | 4 | 0 | -0.1481 | -0.1481 | -0.1481 |
| k1 | CF1 | Entropy only | Words | 9-12 | 4 | 4 | 0 | -0.1481 | -0.1481 | -0.1481 |
| k1 | CF2 | Matched context size only | Morphemes | 1-4 | 4 | 4 | 0 | -0.1562 | -0.1562 | -0.1562 |
| k1 | CF2 | Matched context size only | Morphemes | 5-8 | 4 | 4 | 0 | -0.1562 | -0.1562 | -0.1562 |
| k1 | CF2 | Matched context size only | Morphemes | 9-12 | 4 | 4 | 0 | -0.1562 | -0.1562 | -0.1562 |
| k1 | CF2 | Matched context size only | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08311 | -0.08311 | -0.08311 |
| k1 | CF2 | Matched context size only | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08311 | -0.08311 | -0.08311 |
| k1 | CF2 | Matched context size only | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08311 | -0.08311 | -0.08311 |
| k1 | CF2 | Matched context size only | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07966 | -0.07966 | -0.07966 |
| k1 | CF2 | Matched context size only | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07966 | -0.07966 | -0.07966 |
| k1 | CF2 | Matched context size only | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07966 | -0.07966 | -0.07966 |
| k1 | CF2 | Matched context size only | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06479 | -0.06479 | -0.06479 |
| k1 | CF2 | Matched context size only | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06479 | -0.06479 | -0.06479 |
| k1 | CF2 | Matched context size only | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06479 | -0.06479 | -0.06479 |
| k1 | CF2 | Matched context size only | Words | 1-4 | 4 | 4 | 0 | -0.1402 | -0.1402 | -0.1402 |
| k1 | CF2 | Matched context size only | Words | 5-8 | 4 | 4 | 0 | -0.1402 | -0.1402 | -0.1402 |
| k1 | CF2 | Matched context size only | Words | 9-12 | 4 | 4 | 0 | -0.1402 | -0.1402 | -0.1402 |
| k1 | CF3 | Entropy plus matched context size | Morphemes | 1-4 | 4 | 4 | 0 | -0.1576 | -0.1576 | -0.1576 |
| k1 | CF3 | Entropy plus matched context size | Morphemes | 5-8 | 4 | 4 | 0 | -0.1576 | -0.1576 | -0.1576 |
| k1 | CF3 | Entropy plus matched context size | Morphemes | 9-12 | 4 | 4 | 0 | -0.1576 | -0.1576 | -0.1576 |
| k1 | CF3 | Entropy plus matched context size | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.08125 | -0.08125 | -0.08125 |
| k1 | CF3 | Entropy plus matched context size | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.08125 | -0.08125 | -0.08125 |
| k1 | CF3 | Entropy plus matched context size | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.08125 | -0.08125 | -0.08125 |
| k1 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.07842 | -0.07842 | -0.07842 |
| k1 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.07842 | -0.07842 | -0.07842 |
| k1 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.07842 | -0.07842 | -0.07842 |
| k1 | CF3 | Entropy plus matched context size | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06222 | -0.06222 | -0.06222 |
| k1 | CF3 | Entropy plus matched context size | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06222 | -0.06222 | -0.06222 |
| k1 | CF3 | Entropy plus matched context size | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06222 | -0.06222 | -0.06222 |
| k1 | CF3 | Entropy plus matched context size | Words | 1-4 | 4 | 4 | 0 | -0.1414 | -0.1414 | -0.1414 |
| k1 | CF3 | Entropy plus matched context size | Words | 5-8 | 4 | 4 | 0 | -0.1414 | -0.1414 | -0.1414 |
| k1 | CF3 | Entropy plus matched context size | Words | 9-12 | 4 | 4 | 0 | -0.1414 | -0.1414 | -0.1414 |
| k2 | CF0 | Baseline controls | Morphemes | 1-4 | 4 | 4 | 0 | -0.1425 | -0.1425 | -0.1425 |
| k2 | CF0 | Baseline controls | Morphemes | 5-8 | 4 | 4 | 0 | -0.1425 | -0.1425 | -0.1425 |
| k2 | CF0 | Baseline controls | Morphemes | 9-12 | 4 | 4 | 0 | -0.1425 | -0.1425 | -0.1425 |
| k2 | CF0 | Baseline controls | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.07096 | -0.07096 | -0.07096 |
| k2 | CF0 | Baseline controls | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.07096 | -0.07096 | -0.07096 |
| k2 | CF0 | Baseline controls | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.07096 | -0.07096 | -0.07096 |
| k2 | CF0 | Baseline controls | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06903 | -0.06903 | -0.06903 |
| k2 | CF0 | Baseline controls | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06903 | -0.06903 | -0.06903 |
| k2 | CF0 | Baseline controls | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06903 | -0.06903 | -0.06903 |
| k2 | CF0 | Baseline controls | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.0542 | -0.0542 | -0.0542 |
| k2 | CF0 | Baseline controls | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.0542 | -0.0542 | -0.0542 |
| k2 | CF0 | Baseline controls | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.0542 | -0.0542 | -0.0542 |
| k2 | CF0 | Baseline controls | Words | 1-4 | 4 | 4 | 0 | -0.1287 | -0.1287 | -0.1287 |
| k2 | CF0 | Baseline controls | Words | 5-8 | 4 | 4 | 0 | -0.1287 | -0.1287 | -0.1287 |
| k2 | CF0 | Baseline controls | Words | 9-12 | 4 | 4 | 0 | -0.1287 | -0.1287 | -0.1287 |
| k2 | CF1 | Entropy only | Morphemes | 1-4 | 4 | 4 | 0 | -0.1458 | -0.1458 | -0.1458 |
| k2 | CF1 | Entropy only | Morphemes | 5-8 | 4 | 4 | 0 | -0.1458 | -0.1458 | -0.1458 |
| k2 | CF1 | Entropy only | Morphemes | 9-12 | 4 | 4 | 0 | -0.1458 | -0.1458 | -0.1458 |
| k2 | CF1 | Entropy only | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.06995 | -0.06995 | -0.06995 |
| k2 | CF1 | Entropy only | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.06995 | -0.06995 | -0.06995 |
| k2 | CF1 | Entropy only | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.06995 | -0.06995 | -0.06995 |
| k2 | CF1 | Entropy only | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06891 | -0.06891 | -0.06891 |
| k2 | CF1 | Entropy only | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06891 | -0.06891 | -0.06891 |
| k2 | CF1 | Entropy only | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06891 | -0.06891 | -0.06891 |
| k2 | CF1 | Entropy only | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.05248 | -0.05248 | -0.05248 |
| k2 | CF1 | Entropy only | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.05248 | -0.05248 | -0.05248 |
| k2 | CF1 | Entropy only | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.05248 | -0.05248 | -0.05248 |
| k2 | CF1 | Entropy only | Words | 1-4 | 4 | 4 | 0 | -0.1318 | -0.1318 | -0.1318 |
| k2 | CF1 | Entropy only | Words | 5-8 | 4 | 4 | 0 | -0.1318 | -0.1318 | -0.1318 |
| k2 | CF1 | Entropy only | Words | 9-12 | 4 | 4 | 0 | -0.1318 | -0.1318 | -0.1318 |
| k2 | CF2 | Matched context size only | Morphemes | 1-4 | 4 | 4 | 0 | -0.1433 | -0.1433 | -0.1433 |
| k2 | CF2 | Matched context size only | Morphemes | 5-8 | 4 | 4 | 0 | -0.1433 | -0.1433 | -0.1433 |
| k2 | CF2 | Matched context size only | Morphemes | 9-12 | 4 | 4 | 0 | -0.1433 | -0.1433 | -0.1433 |
| k2 | CF2 | Matched context size only | Phonemes | 1-4 representative ranks | 4 | 4 | 0 | -0.0717 | -0.0717 | -0.0717 |
| k2 | CF2 | Matched context size only | Phonemes | 5-8 representative ranks | 4 | 4 | 0 | -0.0717 | -0.0717 | -0.0717 |
| k2 | CF2 | Matched context size only | Phonemes | 9-12 representative ranks | 4 | 4 | 0 | -0.0717 | -0.0717 | -0.0717 |
| k2 | CF2 | Matched context size only | Syllables: CMU/pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.06963 | -0.06963 | -0.06963 |
| k2 | CF2 | Matched context size only | Syllables: CMU/pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.06963 | -0.06963 | -0.06963 |
| k2 | CF2 | Matched context size only | Syllables: CMU/pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.06963 | -0.06963 | -0.06963 |
| k2 | CF2 | Matched context size only | Syllables: pkg | 1-4 representative ranks | 4 | 4 | 0 | -0.05479 | -0.05479 | -0.05479 |
| k2 | CF2 | Matched context size only | Syllables: pkg | 5-8 representative ranks | 4 | 4 | 0 | -0.05479 | -0.05479 | -0.05479 |
| k2 | CF2 | Matched context size only | Syllables: pkg | 9-12 representative ranks | 4 | 4 | 0 | -0.05479 | -0.05479 | -0.05479 |
| k2 | CF2 | Matched context size only | Words | 1-4 | 4 | 4 | 0 | -0.1289 | -0.1289 | -0.1289 |
| k2 | CF2 | Matched context size only | Words | 5-8 | 4 | 4 | 0 | -0.1289 | -0.1289 | -0.1289 |
| k2 | CF2 | Matched context size only | Words | 9-12 | 4 | 4 | 0 | -0.1289 | -0.1289 | -0.1289 |

## Fixed-Effort Prediction Figures

How to read every figure: each colored line is one exact fixed effort value. The shaded ribbon is the model confidence band for the fitted mean line. The context predictors are held at their model-frame mean for the prediction slice, so the plot isolates age at fixed target effort under average context conditions.

### K0

#### CF0: Baseline controls

**Morphemes**

![k0 CF0 Morphemes](../figs/context_fixed_effort_atlas/k0_cf0_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 CF0 Phonemes](../figs/context_fixed_effort_atlas/k0_cf0_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 CF0 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 CF0 Syllables: pkg](../figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 CF0 Words](../figs/context_fixed_effort_atlas/k0_cf0_nb_words_fixed_effort_atlas.png)

### K1

#### CF0: Baseline controls

**Morphemes**

![k1 CF0 Morphemes](../figs/context_fixed_effort_atlas/k1_cf0_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CF0 Phonemes](../figs/context_fixed_effort_atlas/k1_cf0_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CF0 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CF0 Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CF0 Words](../figs/context_fixed_effort_atlas/k1_cf0_nb_words_fixed_effort_atlas.png)

#### CF1: Entropy only

**Morphemes**

![k1 CF1 Morphemes](../figs/context_fixed_effort_atlas/k1_cf1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CF1 Phonemes](../figs/context_fixed_effort_atlas/k1_cf1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CF1 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CF1 Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CF1 Words](../figs/context_fixed_effort_atlas/k1_cf1_nb_words_fixed_effort_atlas.png)

#### CF2: Matched context size only

**Morphemes**

![k1 CF2 Morphemes](../figs/context_fixed_effort_atlas/k1_cf2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CF2 Phonemes](../figs/context_fixed_effort_atlas/k1_cf2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CF2 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CF2 Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CF2 Words](../figs/context_fixed_effort_atlas/k1_cf2_nb_words_fixed_effort_atlas.png)

#### CF3: Entropy plus matched context size

**Morphemes**

![k1 CF3 Morphemes](../figs/context_fixed_effort_atlas/k1_cf3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CF3 Phonemes](../figs/context_fixed_effort_atlas/k1_cf3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CF3 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CF3 Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CF3 Words](../figs/context_fixed_effort_atlas/k1_cf3_nb_words_fixed_effort_atlas.png)

### K2

#### CF0: Baseline controls

**Morphemes**

![k2 CF0 Morphemes](../figs/context_fixed_effort_atlas/k2_cf0_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CF0 Phonemes](../figs/context_fixed_effort_atlas/k2_cf0_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CF0 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CF0 Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CF0 Words](../figs/context_fixed_effort_atlas/k2_cf0_nb_words_fixed_effort_atlas.png)

#### CF1: Entropy only

**Morphemes**

![k2 CF1 Morphemes](../figs/context_fixed_effort_atlas/k2_cf1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CF1 Phonemes](../figs/context_fixed_effort_atlas/k2_cf1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CF1 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CF1 Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CF1 Words](../figs/context_fixed_effort_atlas/k2_cf1_nb_words_fixed_effort_atlas.png)

#### CF2: Matched context size only

**Morphemes**

![k2 CF2 Morphemes](../figs/context_fixed_effort_atlas/k2_cf2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CF2 Phonemes](../figs/context_fixed_effort_atlas/k2_cf2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CF2 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CF2 Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CF2 Words](../figs/context_fixed_effort_atlas/k2_cf2_nb_words_fixed_effort_atlas.png)

#### CF3: Entropy plus matched context size

**Morphemes**

![k2 CF3 Morphemes](../figs/context_fixed_effort_atlas/k2_cf3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CF3 Phonemes](../figs/context_fixed_effort_atlas/k2_cf3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CF3 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CF3 Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CF3 Words](../figs/context_fixed_effort_atlas/k2_cf3_nb_words_fixed_effort_atlas.png)

### K3

#### CF0: Baseline controls

**Morphemes**

![k3 CF0 Morphemes](../figs/context_fixed_effort_atlas/k3_cf0_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CF0 Phonemes](../figs/context_fixed_effort_atlas/k3_cf0_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CF0 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CF0 Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CF0 Words](../figs/context_fixed_effort_atlas/k3_cf0_nb_words_fixed_effort_atlas.png)

#### CF1: Entropy only

**Morphemes**

![k3 CF1 Morphemes](../figs/context_fixed_effort_atlas/k3_cf1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CF1 Phonemes](../figs/context_fixed_effort_atlas/k3_cf1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CF1 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CF1 Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CF1 Words](../figs/context_fixed_effort_atlas/k3_cf1_nb_words_fixed_effort_atlas.png)

#### CF2: Matched context size only

**Morphemes**

![k3 CF2 Morphemes](../figs/context_fixed_effort_atlas/k3_cf2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CF2 Phonemes](../figs/context_fixed_effort_atlas/k3_cf2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CF2 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CF2 Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CF2 Words](../figs/context_fixed_effort_atlas/k3_cf2_nb_words_fixed_effort_atlas.png)

#### CF3: Entropy plus matched context size

**Morphemes**

![k3 CF3 Morphemes](../figs/context_fixed_effort_atlas/k3_cf3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CF3 Phonemes](../figs/context_fixed_effort_atlas/k3_cf3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CF3 Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CF3 Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CF3 Words](../figs/context_fixed_effort_atlas/k3_cf3_nb_words_fixed_effort_atlas.png)

## Skipped Rows

These are expected mainly for `k0`, where there are no context predictors to fit.

| context_k | model_id | model_label | effort_label | status | error |
| --- | --- | --- | --- | --- | --- |
| k0 | CF1 | Entropy only | Words | skipped | k0 has no context predictors |
| k0 | CF2 | Matched context size only | Words | skipped | k0 has no context predictors |
| k0 | CF3 | Entropy plus matched context size | Words | skipped | k0 has no context predictors |
| k0 | CF1 | Entropy only | Morphemes | skipped | k0 has no context predictors |
| k0 | CF2 | Matched context size only | Morphemes | skipped | k0 has no context predictors |
| k0 | CF3 | Entropy plus matched context size | Morphemes | skipped | k0 has no context predictors |
| k0 | CF1 | Entropy only | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | CF2 | Matched context size only | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | skipped | k0 has no context predictors |
| k0 | CF1 | Entropy only | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | CF2 | Matched context size only | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | CF3 | Entropy plus matched context size | Syllables: pkg | skipped | k0 has no context predictors |
| k0 | CF1 | Entropy only | Phonemes | skipped | k0 has no context predictors |
| k0 | CF2 | Matched context size only | Phonemes | skipped | k0 has no context predictors |
| k0 | CF3 | Entropy plus matched context size | Phonemes | skipped | k0 has no context predictors |

## Saved Outputs

```text
results/context_fixed_effort_atlas/context_fixed_effort_model_summary.csv
results/context_fixed_effort_atlas/context_fixed_effort_bin_definitions.csv
results/context_fixed_effort_atlas/context_fixed_effort_predictions.csv.gz
results/context_fixed_effort_atlas/context_fixed_effort_slice_slopes.csv
results/context_fixed_effort_atlas/context_fixed_effort_figure_manifest.csv
figs/context_fixed_effort_atlas/
```