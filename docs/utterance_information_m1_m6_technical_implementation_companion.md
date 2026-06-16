# M1-M6 Technical Implementation Companion

This companion explains the modeling mechanics behind the interpreted M1-M6 atlas. It is written for moments when the formulas, estimators, fixed effects, clustered standard errors, interactions, or Route 1 versus Route 2 distinction feel muddy.

No new models are fit here. Proposed additions are explicitly marked as proposed/not yet run.

## Route 1 And Route 2

Route 1 is the current utterance-information analysis:

```text
informativeness ~ age + effort + controls
```

The outcome is `sum_bits`, the total Mistral surprisal of the target utterance. Route 1 asks whether the information in what the child actually said changes with age after production effort is controlled.

Route 2 is the future effort-choice analysis:

```text
effort_or_length ~ age + context_uncertainty + controls
```

Route 2 asks whether the context leads children to choose shorter or longer responses. It needs a context-level predictor such as response-space entropy, not only target-utterance surprisal.

## Core Variables

- `sum_bits`: total target-utterance information in Mistral bits.
- `age_c`: child age in months, centered by subtracting a reference mean.
- `target_effort_c`: one effort measure, centered. Effort is words, morphemes, syllables, or phonemes.
- `context_entropy_c`: current next-token context entropy, centered.
- `context_size_c`: matched surface size of the context window, centered.
- `C(child_id)`: child fixed intercepts in a statsmodels formula.

## What Is OLS?

Ordinary least squares is ordinary linear regression. It fits a line or plane by choosing coefficients that minimize squared residuals:

```text
observed sum_bits - predicted sum_bits
```

In these reports, OLS coefficients are on the additive bits scale. If the M2 word-count age coefficient is about `-0.122`, the model predicts about 0.122 fewer total bits per additional month for same-word-count utterances after child identity is controlled.

Library used:

```text
statsmodels.formula.api.ols
```

## What Is A GLM?

A generalized linear model keeps the idea of a linear predictor but allows a different outcome distribution and link function. A Gaussian GLM with identity link is very close to ordinary linear regression. A Gamma/log GLM is different: it is for positive continuous outcomes and models the log expected outcome.

In a Gamma/log model, a coefficient is not "bits per month" directly. It is a change in log expected bits. Use prediction plots for intuition.

Library used:

```text
statsmodels.formula.api.glm
```

## What Is GEE?

Generalized estimating equations fit population-average regression models while accounting for clustered/repeated observations. In this project, the cluster is child. GEE is useful because utterance rows from the same child are correlated.

Library used:

```text
statsmodels.formula.api.gee(..., groups='child_id')
```

GEE is a sensitivity family here, not the primary supervisor-facing model.

## What Is MixedLM?

MixedLM is a linear mixed model. It can include random effects such as a random child intercept or a random child age slope. A random intercept lets children vary around a population baseline. A random age slope lets children vary in developmental trajectory.

Library used:

```text
statsmodels mixed linear model
```

Mixed models are useful for correlated longitudinal data, but they can be singular or unstable when the data do not support all random-effect terms. In this project they are diagnostics rather than the current headline model.

## Fixed Effects

A fixed effect estimates a separate coefficient for each level of a categorical variable. `C(child_id)` gives every child their own intercept. This controls stable child-level differences such as baseline verbosity, transcription style, corpus membership, or general predictability.

In M2-M6, child fixed intercepts mean the age slope is estimated after each child has a personal baseline.

## Random Effects

A random effect treats child-specific deviations as drawn from a population distribution. Random effects are useful when we want child-specific intercepts or slopes but also want shrinkage toward the population mean.

Random effects answer a different question from fixed effects. They are not simply "better fixed effects"; they encode a different statistical assumption.

## Clustered Standard Errors

Child-clustered standard errors adjust uncertainty for repeated utterances from the same child. They do not change the fitted line. They change standard errors, confidence intervals, and p-values.

This is why OLS and child-clustered OLS can have identical plotted mean lines but different shaded confidence bands and p-values.

## What Is An Interaction?

An interaction means the effect of one predictor depends on another predictor.

Age x effort:

```text
sum_bits ~ age_c * effort_c
```

asks whether the age slope differs for short versus long utterances.

Age x effort level:

```text
sum_bits ~ age_c * C(effort_level)
```

asks whether low, mid, and high effort groups have different age slopes.

Age x context entropy:

```text
sum_bits ~ age_c * context_entropy_c
```

asks whether the context-entropy association changes with age.

Effort x context entropy:

```text
sum_bits ~ effort_c * context_entropy_c
```

asks whether the relation between effort and total information differs in high-entropy contexts.

## Why Center Variables?

Centering subtracts a reference mean from a numeric predictor. It does not change model fit or slopes for simple main effects. It makes the intercept and interaction main effects easier to read.

With centered variables, an age coefficient in an interaction model is the age slope at average effort/context entropy, not at effort zero.

## Why Separate Effort Units?

Words, morphemes, syllables, and phonemes are highly correlated. Putting all of them in one regression makes the coefficients unstable and hard to interpret. The current strategy fits parallel models, one effort unit at a time.

That means a "Words" row and a "Morphemes" row are separate models asking the same question under different effort definitions.

## What R2 Means Here

`r2_observed_fitted` is an in-sample correspondence between observed and fitted `sum_bits`. It is useful for descriptive fit. It is not held-out predictive accuracy and should not be treated as proof that the model will generalize to new corpora.

## What P-Values Mean Here

A p-value describes how surprising a coefficient estimate would be under a null model, given the model assumptions and uncertainty calculation. It is not an effect size, not a probability the hypothesis is true, and not a model-selection device by itself.

For clustered child data, p-values are more credible when uncertainty respects child clustering or when robustness checks agree.

## Model-Based Predictions

Model-based prediction plots show fitted expected `sum_bits` under specified values of age, effort, context, and child structure. They are not raw averages. Fixed-effort slice plots hold effort at exact values so the age trend is not merely driven by older children producing longer utterances.

## Robustness And Scrambling Tests

Balanced bootstrap checks whether an age effect survives when age bins contribute equalized samples. Age scrambling checks whether the observed developmental slope depends on true age ordering. If the real slope is outside the scrambled null range, the age structure is doing real work.

The current robustness report aggregates to child-session-context units to reduce the illusion that hundreds of thousands of utterance rows are independent.

## Aggregating To Child-Session-Context Units

Aggregation changes the observational unit from utterance rows to:

```text
child x session x context window
```

This reduces row-level dependence and makes robustness tests more conservative. It also means coefficients will not exactly match utterance-level models.

## Is Child Identity Control Too Strong?

Short answer: child identity control is appropriate and scientifically useful here, but it changes the question. It is not automatically "better" in every sense.

M1 asks a pooled question: across all rows, does age predict total information after effort control? Because children and corpora occupy different age ranges, M1 can confound development with which child, corpus, transcription style, and recording context happens to contribute data at a given age. This is why M1 is useful as a warning light rather than as the primary result.

M2 adds child fixed intercepts. That means each child receives a separate baseline level of predicted information, while the model estimates one shared age slope. In plain terms, M2 asks whether the age effect remains after removing stable child-to-child baseline differences. This is a conservative move if the target is within-child developmental change.

The worry is real: if children occupy different age ranges, child fixed effects discard between-child age composition. Some of that between-child variation may reflect meaningful developmental structure, but it is inseparable from corpus and child composition unless modeled carefully. M2 therefore answers a narrower question than "do older children in the dataset differ from younger children?" It answers "within the child-adjusted comparison, is later age associated with different target information at fixed effort?"

Child fixed effects can be too restrictive if the scientific estimand is a population developmental trajectory that legitimately includes between-child differences. They can also leave weak support where a child's age range is short or where older ages are represented by only a few children. They do not solve time-varying confounding, caregiver style changes, topic/task changes, or sparse age-bin support.

The right interpretation is therefore balanced:

- M1 is vulnerable to child/corpus composition.
- M2 is more conservative for within-child development.
- M2 can be too narrow if we also care about between-child developmental differences.
- Random slopes, within/between decomposition, age-overlap restrictions, corpus controls, age-bin balancing, and leave-one-child/corpus-out checks should be added before making a final dissertation-level causal/developmental claim.

Recommended next formulas are listed in the technical companion. None of those additions are claimed as results in this v2 report unless they already exist in saved artifacts.


## Current M2 Result In Mechanical Terms

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  | fit |

M2 is an OLS model with child fixed intercepts. Its uncertainty in the supervisor-facing report uses child-clustered robust standard errors. It answers a within-child-adjusted Route 1 question: for the same effort and child baseline, how does target utterance information change with age?

## Route 2 Length Prediction Bridge

Route 2 should use effort as the outcome. The conceptual formula is:

```text
production_effort ~ age + response_entropy + expected_model_response_length + context_size + question_type + child controls
```

Why Route 2 differs from Route 1:

- Route 1 asks how much information is in the utterance after effort is controlled.
- Route 2 asks how much effort the child chooses after context uncertainty is measured.
- Route 1 can use `sum_bits` as the outcome.
- Route 2 needs a context-level uncertainty measure available before the child speaks.

The current next-token entropy feature is only a provisional bridge. Response-space entropy from sampled full responses is a better match for the Route 2 hypothesis.

## Proposed Additions

| proposal | formula | why | status |
| --- | --- | --- | --- |
| within-child centered age | sum_bits ~ age_within_child + effort + C(child_id) | Directly estimates within-child change while preserving each child's baseline. | proposed/not yet run in this v2 synthesis |
| within/between age decomposition | sum_bits ~ age_within_child + child_mean_age + effort + corpus | Separates within-child development from between-child/corpus age composition. | proposed/not yet run in this v2 synthesis |
| age-overlap restricted subset | same as M2/M3 after restricting to age months shared by multiple children/corpora | Checks whether the M2 slope is driven by children who occupy unique age ranges. | proposed/not yet run in this v2 synthesis |
| age-bin balanced model | M2/M3 on equalized age-bin samples or child-session-context units | Reduces leverage of dense toddler bins and follows Pawar-style stability logic. | partially addressed by existing age-scrambling robustness; further utterance-level version not yet run |
| corpus fixed effects | sum_bits ~ age + effort + C(child_id) + C(dataset) | Tests whether corpus/transcription context explains part of the child-adjusted trend. | proposed/not yet run in this v2 synthesis |
| child random intercept plus random age slope | MixedLM: sum_bits ~ age + effort, groups=child_id, re_formula='~age' | Allows children to have different developmental slopes and shrinks noisy child-specific estimates. | M2/M3 sensitivity exists; fuller overlap/balancing interpretation still proposed |
| Route 2 effort outcome bridge | effort ~ age + response_entropy + expected_model_response_length + context_size + C(child_id) | Tests whether contextual uncertainty predicts how much children choose to say. | proposed; response-space entropy pilot exists but production features are not yet the primary analysis |

## Implementation Cheat Sheet

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

## Practical Reading Order

1. Read M2 first.
2. Check the M2 fixed-effort plots.
3. Check M2 balanced/scrambled robustness.
4. Use M3 only for age-by-effort nuance.
5. Use M4 to explain context-control robustness.
6. Treat M5/M6 as exploratory unless their interactions become stable in future runs.
