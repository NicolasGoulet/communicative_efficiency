# Quick Share: M1-M6 Utterance Information Models

This is the minimal shareable version. The fitting stage has already been run;
this file only renders saved model tables and plots.

Outcome:

```text
sum_bits
```

## What Changed In This Version

Every M1-M6 model is shown with **two effort strategies**:

- `continuous`: all utterance lengths stay in one numeric scale, and the model controls their differences directly.
- `effort_level`: utterances are grouped into low/mid/high effort within one effort unit, and those groups enter the model as categorical predictors.

The two strategies are fit separately. They are not the same model and they
should be compared as a robustness check.

## Model Map

| model | question | continuous effort formula | effort-level formula |
| --- | --- | --- | --- |
| M1 | Pooling all children, does age predict total bits after controlling utterance effort? | sum_bits ~ age + effort | sum_bits ~ age + effort_level |
| M2 | Does the developmental age effect remain after child identity is controlled? | sum_bits ~ age + effort + child identity | sum_bits ~ age + effort_level + child identity |
| M3 | Does the relation between effort and total bits change with age? | sum_bits ~ age * effort + child identity | sum_bits ~ age * effort_level + child identity |
| M4 | Does context entropy add predictive information beyond age, effort, and child identity? | sum_bits ~ age + effort + context_entropy + child identity | sum_bits ~ age + effort_level + context_entropy + child identity |
| M5 | Does the context-entropy effect on total bits change over development? | sum_bits ~ age * context_entropy + effort + child identity | sum_bits ~ age * context_entropy + effort_level + child identity |
| M6 | Do age, effort, and context entropy interact when predicting total bits? | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity |

## Shared Reading Rules

- Downward age lines mean lower predicted total bits as children get older, after the controls in that model.
- The top row of each plot is the continuous effort-control version.
- The bottom row of each plot is the low/mid/high effort-group version.
- Each column is a different effort unit: words, morphemes, two syllable strategies, or phonemes.
- When a top-row panel says `median = X`, that is only the value used to draw
  the prediction line. The model was still fit on all utterances with their
  actual observed effort values.
- `C(child_id)` means child fixed intercepts: each child gets their own baseline.
- Context entropy is Mistral next-token entropy in bits, not sampled full-response entropy.

## M1: Pooled age and effort

**Question.** Pooling all children, does age predict total bits after controlling utterance effort?

**Formulas.**

| effort_strategy | readable_formula | formula |
| --- | --- | --- |
| continuous | sum_bits ~ age + effort | sum_bits ~ age_c + effort_c |
| effort_level | sum_bits ~ age + effort_level | sum_bits ~ age_c + C(effort_level) |

**Quick takeaway.** continuous: 0 negative, 5 positive age coefficients; effort_level: 0 negative, 5 positive age coefficients.

**How to read the plot.** The top row uses the exact effort count as a numeric control. The bottom row uses the same effort unit to make low/mid/high effort groups. If both rows tell the same age story, the result is less dependent on the effort encoding. Shaded ribbons are model-based 95% confidence intervals when available.

![M1 dual effort predictions](../figs/m1_m6_dual_effort_quick_share/m1_dual_effort_predictions.png)

**Compact results.**

| effort_strategy | effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Morphemes | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  | fit |
| continuous | Words | 0.613 | 0.0003087 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  | fit |
| effort_level | Morphemes | 0.3898 | 0.1672 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | 0.4502 | 0.1537 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | 0.452 | 0.134 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | 0.4269 | 0.1638 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Words | 0.4211 | 0.1334 | 0.005 |  |  |  |  |  |  |  |  | fit |
## M2: Age and effort with child identity

**Question.** Does the developmental age effect remain after child identity is controlled?

**Formulas.**

| effort_strategy | readable_formula | formula |
| --- | --- | --- |
| continuous | sum_bits ~ age + effort + child identity | sum_bits ~ age_c + effort_c + C(child_id) |
| effort_level | sum_bits ~ age + effort_level + child identity | sum_bits ~ age_c + C(effort_level) + C(child_id) |

**Quick takeaway.** continuous: 5 negative, 0 positive age coefficients; effort_level: 0 negative, 5 positive age coefficients.

**How to read the plot.** The top row uses the exact effort count as a numeric control. The bottom row uses the same effort unit to make low/mid/high effort groups. If both rows tell the same age story, the result is less dependent on the effort encoding. Shaded ribbons are model-based 95% confidence intervals when available.

![M2 dual effort predictions](../figs/m1_m6_dual_effort_quick_share/m2_dual_effort_predictions.png)

**Compact results.**

| effort_strategy | effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Morphemes | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  | fit |
| continuous | Words | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  | fit |
| effort_level | Morphemes | 0.4064 | 0.117 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | 0.4622 | 0.08531 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | 0.4631 | 0.07177 | 0.005 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | 0.4398 | 0.1069 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Words | 0.4353 | 0.08168 | <.001 |  |  |  |  |  |  |  |  | fit |
## M3: Age by effort

**Question.** Does the relation between effort and total bits change with age?

**Formulas.**

| effort_strategy | readable_formula | formula |
| --- | --- | --- |
| continuous | sum_bits ~ age * effort + child identity | sum_bits ~ age_c * effort_c + C(child_id) |
| effort_level | sum_bits ~ age * effort_level + child identity | sum_bits ~ age_c * C(effort_level) + C(child_id) |

**Quick takeaway.** continuous: 5 negative, 0 positive age coefficients; effort_level: 5 negative, 0 positive age coefficients.

**How to read the plot.** For M3, the bottom row is especially important: non-parallel low/mid/high lines mean the age trend differs by effort level. The continuous row asks the same interaction question with the raw effort count. Shaded ribbons are model-based 95% confidence intervals when available.

![M3 dual effort predictions](../figs/m1_m6_dual_effort_quick_share/m3_dual_effort_predictions.png)

**Compact results.**

| effort_strategy | effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Morphemes | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  | 0.00228 | 0.727 |  |  | fit |
| continuous | Phonemes | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  | 0.002729 | 0.220 |  |  | fit |
| continuous | Syllables: CMU/pkg | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  | 0.00703 | 0.252 |  |  | fit |
| continuous | Syllables: pkg | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  | 0.009859 | 0.022 |  |  | fit |
| continuous | Words | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  | -0.003787 | 0.515 |  |  | fit |
| effort_level | Morphemes | 0.4122 | -0.0701 | 0.064 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | 0.4676 | -0.07701 | 0.009 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | 0.4688 | -0.06415 | 0.033 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | 0.4466 | -0.05571 | 0.073 |  |  |  |  |  |  |  |  | fit |
| effort_level | Words | 0.4401 | -0.0722 | 0.033 |  |  |  |  |  |  |  |  | fit |
## M4: Context entropy added

**Question.** Does context entropy add predictive information beyond age, effort, and child identity?

**Formulas.**

| effort_strategy | readable_formula | formula |
| --- | --- | --- |
| continuous | sum_bits ~ age + effort + context_entropy + child identity | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) |
| effort_level | sum_bits ~ age + effort_level + context_entropy + child identity | sum_bits ~ age_c + C(effort_level) + context_entropy_c + C(child_id) |

**Quick takeaway.** continuous: 5 negative, 0 positive age coefficients; effort_level: 0 negative, 5 positive age coefficients.

**How to read the plot.** The top row uses the exact effort count as a numeric control. The bottom row uses the same effort unit to make low/mid/high effort groups. If both rows tell the same age story, the result is less dependent on the effort encoding. Shaded ribbons are model-based 95% confidence intervals when available.

![M4 dual effort predictions](../figs/m1_m6_dual_effort_quick_share/m4_dual_effort_predictions.png)

**Compact results.**

| effort_strategy | effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Morphemes | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  | fit |
| continuous | Phonemes | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  | fit |
| continuous | Syllables: pkg | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  | fit |
| continuous | Words | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  | fit |
| effort_level | Morphemes | 0.4072 | 0.1197 | <.001 |  |  | -0.5201 | <.001 |  |  |  |  | fit |
| effort_level | Phonemes | 0.4633 | 0.08804 | <.001 |  |  | -0.5842 | <.001 |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | 0.4639 | 0.07374 | 0.005 |  |  | -0.5254 | <.001 |  |  |  |  | fit |
| effort_level | Syllables: pkg | 0.4407 | 0.1106 | <.001 |  |  | -0.5295 | <.001 |  |  |  |  | fit |
| effort_level | Words | 0.4363 | 0.0829 | <.001 |  |  | -0.4785 | <.001 |  |  |  |  | fit |
## M5: Age by context entropy

**Question.** Does the context-entropy effect on total bits change over development?

**Formulas.**

| effort_strategy | readable_formula | formula |
| --- | --- | --- |
| continuous | sum_bits ~ age * context_entropy + effort + child identity | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) |
| effort_level | sum_bits ~ age * context_entropy + effort_level + child identity | sum_bits ~ age_c * context_entropy_c + C(effort_level) + C(child_id) |

**Quick takeaway.** continuous: 5 negative, 0 positive age coefficients; effort_level: 0 negative, 5 positive age coefficients.

**How to read the plot.** The top row uses the exact effort count as a numeric control. The bottom row uses the same effort unit to make low/mid/high effort groups. If both rows tell the same age story, the result is less dependent on the effort encoding. Shaded ribbons are model-based 95% confidence intervals when available.

![M5 dual effort predictions](../figs/m1_m6_dual_effort_quick_share/m5_dual_effort_predictions.png)

**Compact results.**

| effort_strategy | effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Morphemes | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  | 0.004709 | 0.339 | fit |
| continuous | Phonemes | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  | 0.00465 | 0.407 | fit |
| continuous | Syllables: CMU/pkg | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  | 0.003955 | 0.478 | fit |
| continuous | Syllables: pkg | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  | 0.003946 | 0.481 | fit |
| continuous | Words | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  | 0.006141 | 0.284 | fit |
| effort_level | Morphemes | 0.4073 | 0.1181 | <.001 |  |  | -0.5173 | <.001 |  |  | 0.01404 | 0.032 | fit |
| effort_level | Phonemes | 0.4633 | 0.08694 | <.001 |  |  | -0.5823 | <.001 |  |  | 0.009479 | 0.207 | fit |
| effort_level | Syllables: CMU/pkg | 0.464 | 0.07276 | 0.006 |  |  | -0.5237 | <.001 |  |  | 0.008394 | 0.244 | fit |
| effort_level | Syllables: pkg | 0.4407 | 0.1096 | <.001 |  |  | -0.5279 | <.001 |  |  | 0.008078 | 0.237 | fit |
| effort_level | Words | 0.4364 | 0.08125 | <.001 |  |  | -0.4758 | <.001 |  |  | 0.01401 | 0.047 | fit |
## M6: Interaction-rich exploratory model

**Question.** Do age, effort, and context entropy interact when predicting total bits?

**Formulas.**

| effort_strategy | readable_formula | formula |
| --- | --- | --- |
| continuous | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | sum_bits ~ age_c * effort_c + age_c * context_entropy_c + effort_c * context_entropy_c + C(child_id) |
| effort_level | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | sum_bits ~ age_c * C(effort_level) + context_entropy_c * C(effort_level) + age_c * context_entropy_c + C(child_id) |

**Quick takeaway.** continuous: 5 negative, 0 positive age coefficients; effort_level: 5 negative, 0 positive age coefficients.

**How to read the plot.** For M6, the two rows are two ways of asking the interaction-rich question. Use it as an exploratory stress test, not as the cleanest primary model. Shaded ribbons are model-based 95% confidence intervals when available.

![M6 dual effort predictions](../figs/m1_m6_dual_effort_quick_share/m6_dual_effort_predictions.png)

**Compact results.**

| effort_strategy | effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Morphemes | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 | 0.003897 | 0.575 | 0.009103 | 0.070 | fit |
| continuous | Phonemes | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 | 0.003548 | 0.200 | 0.00833 | 0.086 | fit |
| continuous | Syllables: CMU/pkg | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 | 0.009024 | 0.154 | 0.00658 | 0.202 | fit |
| continuous | Syllables: pkg | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 | 0.01209 | 0.017 | 0.005176 | 0.277 | fit |
| continuous | Words | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 | -0.002441 | 0.726 | 0.009085 | 0.111 | fit |
| effort_level | Morphemes | 0.4133 | -0.07519 | 0.050 |  |  | -0.3338 | <.001 |  |  | 0.008115 | 0.060 | fit |
| effort_level | Phonemes | 0.469 | -0.08116 | 0.007 |  |  | -0.3343 | <.001 |  |  | 0.003877 | 0.432 | fit |
| effort_level | Syllables: CMU/pkg | 0.4699 | -0.06767 | 0.027 |  |  | -0.3802 | <.001 |  |  | 0.004033 | 0.442 | fit |
| effort_level | Syllables: pkg | 0.4478 | -0.05867 | 0.061 |  |  | -0.3742 | <.001 |  |  | 0.002937 | 0.532 | fit |
| effort_level | Words | 0.4413 | -0.0775 | 0.023 |  |  | -0.3592 | <.001 |  |  | 0.008538 | 0.072 | fit |


## Analysis Audit

| input_csv | context_k | rows | children | age_min | age_max | fitted_model_rows | prediction_rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz | k3 | 446985 | 21 | 11.13 | 62.4 | 60 | 10800 |

## Files

- Analysis tables: `results/m1_m6_dual_effort_quick_share/dual_model_summary.csv`
- Prediction rows: `results/m1_m6_dual_effort_quick_share/dual_model_predictions.csv`
- Figures: `figs/m1_m6_dual_effort_quick_share`
- This report: `docs/utterance_information_m1_m6_quick_share.html`
