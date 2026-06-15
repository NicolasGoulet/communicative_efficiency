# Internal Review: Utterance Information Models M1-M6

This is an internal modeling packet for utterance-level total information. It
does not edit the supervisor-facing report. The analysis stage fits the models
and writes CSV/PNG artifacts; the report stage only reads those artifacts.

Outcome throughout:

```text
sum_bits
```

Core rule: effort measures are not combined as continuous predictors in the
same regression. When effort is continuous, each model is repeated separately
for words, morphemes, CMU/pkg syllables, package syllables, and phonemes. When
effort is categorical, low/mid/high effort is created separately from one
effort unit at a time.

## Shared Reading Rules

Table columns used below:

- `effort_label`: which effort unit defines the model version.
- `effect_scale`: whether coefficients are additive bits or log expected bits.
- `r2_observed_fitted`: squared correspondence between observed and fitted total bits; higher means better in-sample fit.
- `age_coef`: expected change in total bits for one additional month, after the listed controls.
- `age_p`: p-value for `age_coef`.
- `effort_coef`: expected change in total bits for one additional effort unit, when effort is continuous.
- `effort_p`: p-value for `effort_coef`.
- `entropy_coef`: expected change in total bits for one additional bit of context entropy.
- `entropy_p`: p-value for `entropy_coef`.
- `age_effort_coef`: interaction term; whether the effort slope changes with age.

Plot rules:

- Raw grey age-bin means are descriptive and not controlled.
- Regression lines are controlled predictions.
- "Effort fixed at median" is only a plotting reference value. The fitted model still uses all observed utterances and all observed effort values.
- `C(child_id)` means child fixed intercepts: each child has its own baseline, but the displayed age slope is shared unless the formula explicitly includes child-specific age slopes.
- In subvariant line plots, the solid line is the fitted mean prediction and
  the shaded band is the model-based 95% confidence interval when statsmodels
  exposes one for that estimator. For OLS versus child-clustered OLS, the mean
  line is expected to be identical; only the uncertainty and p-values change.
- A **subvariant** is a real model change: different formula, estimator, link,
  child-dependence structure, or effort source.
- A **diagnostic view** is not a new model. It is the same fitted subvariant
  plotted with different reference values, such as median effort versus
  low/median/high effort lines.

## Why We Separate Effort Units

Words, morphemes, syllables, and phonemes are different effort proxies, but
they are highly correlated. Putting all of them into one continuous model makes
individual coefficients unstable and hard to interpret. This packet therefore
uses a repeated-model strategy rather than a single overloaded formula.

How to read the heatmap: values close to 1 mean two predictors move together.
That is exactly why the effort variables are not used simultaneously as
continuous covariates.

![Predictor correlations](../figs/m1_m2_utterance_information_deep_dive/predictor_correlation_heatmap.png)

## Model 1: Pooled Age + Continuous Effort

Formula:

```text
sum_bits ~ age + effort
```

Question: pooling all children together, does age predict total information
after controlling for utterance effort?

This is the weakest developmental model because it does not control stable
differences between children. It is useful as a baseline for seeing what goes
wrong when child identity is ignored.

### Model 1 Subvariants

Each subsection below is a real M1 subvariant because the estimator or
uncertainty model changes. The effort unit is still repeated separately inside
each subvariant.

### Subvariant: OLS

Formula:

```text
sum_bits ~ age + effort
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort, pooling all children together?

Controls / structure: Controls effort only. It does not control stable child-to-child differences.

How to read it: The age coefficient is the pooled age trend at a fixed utterance size. Ordinary least squares gives additive bit-scale coefficients.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.613 | 10.19 | 0.0003087 | 0.873 | 6.354 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.5978 | 10.39 | 0.009018 | <.001 | 5.446 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6345 | 9.901 | 0.05143 | <.001 | 5.212 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6177 | 10.13 | 0.06904 | <.001 | 4.822 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.632 | 9.936 | 0.0681 | <.001 | 2.07 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M1 OLS adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m1_ols_adjusted_age_lines.png)


### Subvariant: OLS, child-clustered SE

Formula:

```text
sum_bits ~ age + effort
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort, pooling all children together?

Controls / structure: Controls effort only. It does not control stable child-to-child differences.

How to read it: The age coefficient is the pooled age trend at a fixed utterance size. The fitted line is ordinary least squares; only the standard errors and p-values are corrected for repeated utterances within child.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.613 | 10.19 | 0.0003087 | 0.993 | 6.354 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.5978 | 10.39 | 0.009018 | 0.774 | 5.446 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6345 | 9.901 | 0.05143 | 0.053 | 5.212 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6177 | 10.13 | 0.06904 | 0.012 | 4.822 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.632 | 9.936 | 0.0681 | 0.012 | 2.07 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M1 OLS, child-clustered SE adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png)


### Subvariant: Gaussian GLM

Formula:

```text
sum_bits ~ age + effort
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort, pooling all children together?

Controls / structure: Controls effort only. It does not control stable child-to-child differences.

How to read it: The age coefficient is the pooled age trend at a fixed utterance size. Gaussian GLM is a GLM version of the linear model; predictions remain on the total-bits scale.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.613 | 10.19 | 0.0003087 | 0.873 | 6.354 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.5978 | 10.39 | 0.009018 | <.001 | 5.446 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6345 | 9.901 | 0.05143 | <.001 | 5.212 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6177 | 10.13 | 0.06904 | <.001 | 4.822 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.632 | 9.936 | 0.0681 | <.001 | 2.07 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M1 Gaussian GLM adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m1_glm_gaussian_adjusted_age_lines.png)


### Subvariant: Gamma GLM, log link

Formula:

```text
sum_bits ~ age + effort
```

Effect scale: `log mean bits`

Question asked: Does age predict total bits after controlling for effort, pooling all children together?

Controls / structure: Controls effort only. It does not control stable child-to-child differences.

How to read it: The age coefficient is the pooled age trend at a fixed utterance size. Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation. Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | full fitted values | -1.706e+07 | 6.765e+04 | -0.0007767 | <.001 | 0.2143 | <.001 |
| Morphemes | log mean bits | fit | full fitted values | -8.55e+09 | 1.514e+06 | -0.0006639 | <.001 | 0.1845 | <.001 |
| Syllables: CMU/pkg | log mean bits | fit | full fitted values | -2.041e+07 | 7.399e+04 | 0.0007068 | <.001 | 0.1794 | <.001 |
| Syllables: pkg | log mean bits | fit | full fitted values | -3.665e+06 | 3.135e+04 | 0.001311 | <.001 | 0.166 | <.001 |
| Phonemes | log mean bits | fit | full fitted values | -8.849e+10 | 4.872e+06 | 0.001138 | <.001 | 0.07251 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M1 Gamma GLM, log link adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m1_glm_gamma_log_adjusted_age_lines.png)



### Model 1 Diagnostic Views

How to read the plot: each line is a same-effort developmental trajectory for
one effort unit. The line changes age while holding that effort unit at its
median value for plotting.

![M1 adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png)

Companion view: this plot uses the same M1 formula but draws three reference
lines for each effort unit: low, median, and high effort. The shaded ribbons
show observed age-bin mean +/- standard error for the corresponding
low/mid/high effort group. These ribbons describe the data support around the
line; they are not formal model-confidence intervals.

![M1 low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m1_low_mid_high_effort_adjusted_age_predictions.png)

Table columns for M1: `formula` shows the fitted equation; `r2` is ordinary OLS
fit; `rmse` is prediction error in bits; `age_coef`/`age_p` are the age effect;
`effort_coef`/`effort_p` are the effort effect.

| effort_label | model_family_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | OLS, child-clustered SE | additive bits | fit | 0.613 | 0.0003087 | 0.993 | 6.354 | <.001 |
| Morphemes | OLS, child-clustered SE | additive bits | fit | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |
| Syllables: CMU/pkg | OLS, child-clustered SE | additive bits | fit | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |
| Syllables: pkg | OLS, child-clustered SE | additive bits | fit | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |
| Phonemes | OLS, child-clustered SE | additive bits | fit | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |

Takeaway: Primary result: the age coefficient is mostly positive across effort versions (0 negative, 5 positive; 2/5 p<.05).

## Model 2: Age + Continuous Effort + Child Identity

Formula:

```text
sum_bits ~ age + effort + C(child_id)
```

Question: after controlling each child's stable baseline, does age predict
total information at the same utterance-effort level?

This is the cleaner version of M1 for developmental interpretation. It compares
age effects after removing stable between-child differences.

### Model 2 Subvariants

Each subsection below is a real M2 subvariant because the child-dependence
structure changes: fixed child intercepts, child-specific age slopes, GEE, or
mixed-effects formulations.

### Subvariant: OLS + child fixed intercepts

Formula:

```text
sum_bits ~ age + effort + C(child_id)
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. Ordinary least squares gives additive bit-scale coefficients. Child fixed effects mean each child has their own baseline intercept.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6259 | 10.02 | -0.1225 | <.001 | 6.367 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.6131 | 10.19 | -0.1355 | <.001 | 5.489 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6459 | 9.746 | -0.06326 | 0.018 | 5.236 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6296 | 9.968 | -0.04846 | 0.049 | 4.831 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6443 | 9.767 | -0.06486 | 0.013 | 2.084 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 OLS + child fixed intercepts adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png)


### Subvariant: OLS + child fixed intercepts and age slopes

Formula:

```text
sum_bits ~ age + effort + C(child_id) + age:C(child_id)
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. Ordinary least squares gives additive bit-scale coefficients. Child fixed effects mean each child has their own baseline intercept. The child age-slope term allows each child to have their own linear developmental slope.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6277 | 9.993 | -0.1525 | <.001 | 6.386 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.6152 | 10.16 | -0.196 | <.001 | 5.508 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6474 | 9.725 | -0.09669 | <.001 | 5.245 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6308 | 9.951 | -0.08275 | <.001 | 4.837 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6456 | 9.75 | -0.0861 | <.001 | 2.087 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 OLS + child fixed intercepts and age slopes adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_age_slope_adjusted_age_lines.png)


### Subvariant: Gamma GLM, log link + child fixed intercepts

Formula:

```text
sum_bits ~ age + effort + C(child_id)
```

Effect scale: `log mean bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. Child fixed effects mean each child has their own baseline intercept. Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation. Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | full fitted values | -1.484e+07 | 6.309e+04 | -0.005295 | <.001 | 0.2142 | <.001 |
| Morphemes | log mean bits | fit | full fitted values | -9.437e+09 | 1.591e+06 | -0.005968 | <.001 | 0.1858 | <.001 |
| Syllables: CMU/pkg | log mean bits | fit | full fitted values | -1.964e+07 | 7.258e+04 | -0.003677 | <.001 | 0.1799 | <.001 |
| Syllables: pkg | log mean bits | fit | full fitted values | -3.211e+06 | 2.935e+04 | -0.003214 | <.001 | 0.1662 | <.001 |
| Phonemes | log mean bits | fit | full fitted values | -9.773e+10 | 5.12e+06 | -0.004147 | <.001 | 0.07297 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 Gamma GLM, log link + child fixed intercepts adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_glm_gamma_log_child_fe_adjusted_age_lines.png)


### Subvariant: Gaussian GEE, clustered by child

Formula:

```text
sum_bits ~ age + effort, grouped by child
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. GEE estimates a population-average effect while clustering repeated utterances by child.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6087 | 10.24 | -0.1224 | <.001 | 6.367 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.5923 | 10.46 | -0.1354 | <.001 | 5.489 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.631 | 9.949 | -0.06318 | 0.015 | 5.236 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6139 | 10.18 | -0.04838 | 0.044 | 4.831 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6273 | 9.999 | -0.06478 | 0.011 | 2.084 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 Gaussian GEE, clustered by child adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_gee_gaussian_adjusted_age_lines.png)


### Subvariant: Gamma GEE, log link, clustered by child

Formula:

```text
sum_bits ~ age + effort, grouped by child
```

Effect scale: `log mean bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation. GEE estimates a population-average effect while clustering repeated utterances by child. Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | full fitted values | -1.475e+07 | 6.29e+04 | -0.005415 | <.001 | 0.2138 | <.001 |
| Morphemes | log mean bits | fit | full fitted values | -9.764e+09 | 1.618e+06 | -0.006172 | <.001 | 0.1858 | <.001 |
| Syllables: CMU/pkg | log mean bits | fit | full fitted values | -2.117e+07 | 7.537e+04 | -0.003852 | <.001 | 0.1801 | <.001 |
| Syllables: pkg | log mean bits | fit | full fitted values | -3.49e+06 | 3.06e+04 | -0.003385 | 0.003 | 0.1662 | <.001 |
| Phonemes | log mean bits | fit | full fitted values | -1.09e+11 | 5.407e+06 | -0.004326 | <.001 | 0.07309 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 Gamma GEE, log link, clustered by child adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_gee_gamma_log_adjusted_age_lines.png)


### Subvariant: Linear mixed model, random child intercept

Formula:

```text
sum_bits ~ age + effort + (1 | child_id)
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. The mixed model adds a random child baseline; singular random-effect warnings mean this should be read as a sensitivity diagnostic.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | fixed effects only; random effects singular | -2.054 | 28.62 | -0.1225 | <.001 | 6.367 | <.001 |
| Morphemes | additive bits | fit | fixed effects only; random effects singular | -2.07 | 28.7 | -0.1355 | <.001 | 5.489 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | fixed effects only; random effects singular | -2.032 | 28.52 | -0.06326 | <.001 | 5.236 | <.001 |
| Syllables: pkg | additive bits | fit | fixed effects only; random effects singular | -2.049 | 28.6 | -0.04846 | <.001 | 4.831 | <.001 |
| Phonemes | additive bits | fit | fixed effects only; random effects singular | -2.035 | 28.53 | -0.06486 | <.001 | 2.084 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 Linear mixed model, random child intercept adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_intercept_adjusted_age_lines.png)


### Subvariant: Linear mixed model, random child age slope

Formula:

```text
sum_bits ~ age + effort + (age | child_id)
```

Effect scale: `additive bits`

Question asked: Does age predict total bits after controlling for effort and child-level dependence?

Controls / structure: Controls effort and accounts for child identity or child-level clustering, depending on the version.

How to read it: The age coefficient is the child-adjusted developmental trend at a fixed utterance size. The mixed model lets child baselines and linear age slopes vary; convergence warnings should be treated as diagnostics.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6277 | 9.993 | -0.1852 | <.001 | 6.386 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.6152 | 10.16 | -0.1958 | <.001 | 5.508 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6474 | 9.725 | -0.1149 | 0.003 | 5.245 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6308 | 9.951 | -0.08571 | 0.131 | 4.837 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6456 | 9.75 | -0.1064 | 0.003 | 2.087 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M2 Linear mixed model, random child age slope adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_age_slope_adjusted_age_lines.png)



### Model 2 Diagnostic Views

How to read the plot: effort is fixed for plotting as in M1, but predictions
also average over the fitted child baselines. A difference between M1 and M2
means the pooled trend was partly driven by which children appear at which
ages.

![M2 adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png)

Companion view: this is the same child-adjusted model, but with low, median,
and high continuous-effort reference lines. The shaded ribbons again show
observed age-bin mean +/- standard error for the matching low/mid/high effort
group.

![M2 low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m2_low_mid_high_effort_adjusted_age_predictions.png)

Table columns for M2 are the same as M1. The key difference is that the formula
contains `C(child_id)`, so `age_coef` is child-adjusted.

| effort_label | model_family_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | OLS + child fixed intercepts | additive bits | fit | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |
| Morphemes | OLS + child fixed intercepts | additive bits | fit | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |
| Syllables: CMU/pkg | OLS + child fixed intercepts | additive bits | fit | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |
| Syllables: pkg | OLS + child fixed intercepts | additive bits | fit | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |
| Phonemes | OLS + child fixed intercepts | additive bits | fit | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |

Takeaway: Primary result: the age coefficient is mostly negative across effort versions (5 negative, 0 positive; 5/5 p<.05).

## Model 3: Age by Continuous Effort

Formula:

```text
sum_bits ~ age * effort + C(child_id)
```

Question: does the effort-information relation change with age?

The interaction `age:effort` asks whether one additional unit of effort carries
the same information consequence at different ages. This still keeps effort
units separate: one model for words, one for morphemes, one for each syllable
estimate, and one for phonemes.

### Model 3 Subvariants

Each subsection below is a real M3 subvariant because the estimator, child
structure, or link function changes while preserving the age-by-effort
scientific question.

### Subvariant: OLS + age by effort interaction

Formula:

```text
sum_bits ~ age * effort
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Ordinary least squares gives additive bit-scale coefficients.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.613 | 10.19 | -0.001242 | 0.526 | 6.342 | <.001 | 0.003893 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.598 | 10.38 | 0.004168 | 0.037 | 5.416 | <.001 | 0.0103 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6348 | 9.897 | 0.04521 | <.001 | 5.181 | <.001 | 0.01174 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6181 | 10.12 | 0.06146 | <.001 | 4.787 | <.001 | 0.01407 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6322 | 9.932 | 0.06241 | <.001 | 2.059 | <.001 | 0.004518 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 OLS + age by effort interaction adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_adjusted_age_lines.png)

![M3 OLS + age by effort interaction low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_interaction_age_lines.png)


### Subvariant: OLS + interaction, child-clustered SE

Formula:

```text
sum_bits ~ age * effort
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. The fitted line is ordinary least squares; only the standard errors and p-values are corrected for repeated utterances within child.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.613 | 10.19 | -0.001242 | 0.970 | 6.342 | <.001 | 0.003893 | 0.422 |
| Morphemes | additive bits | fit | full fitted values | 0.598 | 10.38 | 0.004168 | 0.891 | 5.416 | <.001 | 0.0103 | 0.034 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6348 | 9.897 | 0.04521 | 0.070 | 5.181 | <.001 | 0.01174 | 0.023 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6181 | 10.12 | 0.06146 | 0.017 | 4.787 | <.001 | 0.01407 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6322 | 9.932 | 0.06241 | 0.014 | 2.059 | <.001 | 0.004518 | 0.008 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 OLS + interaction, child-clustered SE adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_adjusted_age_lines.png)

![M3 OLS + interaction, child-clustered SE low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png)


### Subvariant: Gaussian GLM + interaction

Formula:

```text
sum_bits ~ age * effort
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Gaussian GLM is a GLM version of the linear model; predictions remain on the total-bits scale.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.613 | 10.19 | -0.001242 | 0.526 | 6.342 | <.001 | 0.003893 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.598 | 10.38 | 0.004168 | 0.037 | 5.416 | <.001 | 0.0103 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6348 | 9.897 | 0.04521 | <.001 | 5.181 | <.001 | 0.01174 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6181 | 10.12 | 0.06146 | <.001 | 4.787 | <.001 | 0.01407 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6322 | 9.932 | 0.06241 | <.001 | 2.059 | <.001 | 0.004518 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Gaussian GLM + interaction adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_adjusted_age_lines.png)

![M3 Gaussian GLM + interaction low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_interaction_age_lines.png)


### Subvariant: Gamma GLM, log link + interaction

Formula:

```text
sum_bits ~ age * effort
```

Effect scale: `log mean bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation. Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | full fitted values | -7.589e+06 | 4.512e+04 | -0.0001478 | 0.055 | 0.219 | <.001 | -0.001715 | <.001 |
| Morphemes | log mean bits | fit | full fitted values | -3.583e+09 | 9.803e+05 | -0.0001157 | 0.138 | 0.188 | <.001 | -0.001265 | <.001 |
| Syllables: CMU/pkg | log mean bits | fit | full fitted values | -9.405e+06 | 5.023e+04 | 0.00132 | <.001 | 0.1825 | <.001 | -0.001299 | <.001 |
| Syllables: pkg | log mean bits | fit | full fitted values | -2.279e+06 | 2.473e+04 | 0.001832 | <.001 | 0.1684 | <.001 | -0.001072 | <.001 |
| Phonemes | log mean bits | fit | full fitted values | -2.867e+10 | 2.773e+06 | 0.001765 | <.001 | 0.07379 | <.001 | -0.0005489 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Gamma GLM, log link + interaction adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_adjusted_age_lines.png)

![M3 Gamma GLM, log link + interaction low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_interaction_age_lines.png)


### Subvariant: OLS + interaction + child fixed intercepts

Formula:

```text
sum_bits ~ age * effort + C(child_id)
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Ordinary least squares gives additive bit-scale coefficients. Child fixed effects mean each child has their own baseline intercept.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6259 | 10.02 | -0.1216 | <.001 | 6.379 | <.001 | -0.003787 | 0.515 |
| Morphemes | additive bits | fit | full fitted values | 0.6131 | 10.19 | -0.1362 | <.001 | 5.482 | <.001 | 0.00228 | 0.727 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.646 | 9.745 | -0.06586 | 0.017 | 5.217 | <.001 | 0.00703 | 0.252 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6298 | 9.965 | -0.05214 | 0.055 | 4.806 | <.001 | 0.009859 | 0.022 |
| Phonemes | additive bits | fit | full fitted values | 0.6444 | 9.766 | -0.06723 | 0.017 | 2.077 | <.001 | 0.002729 | 0.220 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 OLS + interaction + child fixed intercepts adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png)

![M3 OLS + interaction + child fixed intercepts low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)


### Subvariant: OLS + interaction + child fixed intercepts and age slopes

Formula:

```text
sum_bits ~ age * effort + C(child_id) + age:C(child_id)
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Ordinary least squares gives additive bit-scale coefficients. Child fixed effects mean each child has their own baseline intercept. The child age-slope term allows each child to have their own linear developmental slope.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6277 | 9.993 | -0.1448 | <.001 | 6.402 | <.001 | -0.005015 | 0.460 |
| Morphemes | additive bits | fit | full fitted values | 0.6152 | 10.16 | -0.2023 | <.001 | 5.498 | <.001 | 0.003415 | 0.628 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6475 | 9.724 | -0.1119 | <.001 | 5.223 | <.001 | 0.007986 | 0.239 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6311 | 9.948 | -0.1053 | <.001 | 4.806 | <.001 | 0.01146 | 0.015 |
| Phonemes | additive bits | fit | full fitted values | 0.6457 | 9.749 | -0.1008 | <.001 | 2.079 | <.001 | 0.003132 | 0.216 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 OLS + interaction + child fixed intercepts and age slopes adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png)

![M3 OLS + interaction + child fixed intercepts and age slopes low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png)


### Subvariant: Gamma GLM, log link + interaction + child fixed intercepts

Formula:

```text
sum_bits ~ age * effort + C(child_id)
```

Effect scale: `log mean bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Child fixed effects mean each child has their own baseline intercept. Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation. Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | full fitted values | -5.518e+06 | 3.847e+04 | -0.004859 | <.001 | 0.22 | <.001 | -0.002082 | <.001 |
| Morphemes | log mean bits | fit | full fitted values | -3.05e+09 | 9.045e+05 | -0.005556 | <.001 | 0.1902 | <.001 | -0.001637 | <.001 |
| Syllables: CMU/pkg | log mean bits | fit | full fitted values | -7.775e+06 | 4.567e+04 | -0.00319 | <.001 | 0.1837 | <.001 | -0.001555 | <.001 |
| Syllables: pkg | log mean bits | fit | full fitted values | -1.805e+06 | 2.2e+04 | -0.002794 | <.001 | 0.1691 | <.001 | -0.001311 | <.001 |
| Phonemes | log mean bits | fit | full fitted values | -2.596e+10 | 2.639e+06 | -0.003664 | <.001 | 0.0745 | <.001 | -0.0006472 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Gamma GLM, log link + interaction + child fixed intercepts adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png)

![M3 Gamma GLM, log link + interaction + child fixed intercepts low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png)


### Subvariant: Gaussian GEE + interaction, clustered by child

Formula:

```text
sum_bits ~ age * effort, grouped by child
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. GEE estimates a population-average effect while clustering repeated utterances by child.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6086 | 10.25 | -0.1215 | <.001 | 6.379 | <.001 | -0.003783 | 0.505 |
| Morphemes | additive bits | fit | full fitted values | 0.5924 | 10.46 | -0.1361 | <.001 | 5.482 | <.001 | 0.002283 | 0.720 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6313 | 9.945 | -0.06578 | 0.014 | 5.217 | <.001 | 0.007032 | 0.240 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6143 | 10.17 | -0.05206 | 0.050 | 4.806 | <.001 | 0.009861 | 0.019 |
| Phonemes | additive bits | fit | full fitted values | 0.6276 | 9.995 | -0.06714 | 0.014 | 2.077 | <.001 | 0.00273 | 0.209 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Gaussian GEE + interaction, clustered by child adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_adjusted_age_lines.png)

![M3 Gaussian GEE + interaction, clustered by child low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_interaction_age_lines.png)


### Subvariant: Gamma GEE, log link + interaction, clustered by child

Formula:

```text
sum_bits ~ age * effort, grouped by child
```

Effect scale: `log mean bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. Gamma/log is a sensitivity model for positive continuous bits; raw coefficients are on the log expected-bits scale, so the prediction plot is the clearest interpretation. GEE estimates a population-average effect while clustering repeated utterances by child. Because this version uses a log link, a positive coefficient means a multiplicative increase in expected bits, not an additive bit increase.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | full fitted values | -6.274e+06 | 4.103e+04 | -0.004872 | <.001 | 0.2206 | <.001 | -0.002085 | <.001 |
| Morphemes | log mean bits | fit | full fitted values | -3.732e+09 | 1.001e+06 | -0.005665 | <.001 | 0.1911 | <.001 | -0.001651 | <.001 |
| Syllables: CMU/pkg | log mean bits | fit | full fitted values | -9.342e+06 | 5.006e+04 | -0.003282 | <.001 | 0.1846 | <.001 | -0.001583 | <.001 |
| Syllables: pkg | log mean bits | fit | full fitted values | -2.174e+06 | 2.415e+04 | -0.00289 | 0.001 | 0.1698 | <.001 | -0.001324 | <.001 |
| Phonemes | log mean bits | fit | full fitted values | -3.432e+10 | 3.034e+06 | -0.003763 | <.001 | 0.07498 | <.001 | -0.0006511 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Gamma GEE, log link + interaction, clustered by child adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_adjusted_age_lines.png)

![M3 Gamma GEE, log link + interaction, clustered by child low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_interaction_age_lines.png)


### Subvariant: Linear mixed model + interaction, random child intercept

Formula:

```text
sum_bits ~ age * effort + (1 | child_id)
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. The mixed model adds a random child baseline; singular random-effect warnings mean this should be read as a sensitivity diagnostic.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6259 | 10.02 | -0.1214 | <.001 | 6.379 | <.001 | -0.003779 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.6131 | 10.19 | -0.136 | <.001 | 5.482 | <.001 | 0.002287 | 0.001 |
| Syllables: CMU/pkg | additive bits | fit | fixed effects only; random effects singular | -2.025 | 28.48 | -0.06586 | <.001 | 5.217 | <.001 | 0.00703 | <.001 |
| Syllables: pkg | additive bits | fit | fixed effects only; random effects singular | -2.038 | 28.55 | -0.05214 | <.001 | 4.806 | <.001 | 0.009859 | <.001 |
| Phonemes | additive bits | fit | fixed effects only; random effects singular | -2.029 | 28.5 | -0.06723 | <.001 | 2.077 | <.001 | 0.002729 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Linear mixed model + interaction, random child intercept adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_adjusted_age_lines.png)

![M3 Linear mixed model + interaction, random child intercept low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_interaction_age_lines.png)


### Subvariant: Linear mixed model + interaction, random child age slope

Formula:

```text
sum_bits ~ age * effort + (age | child_id)
```

Effect scale: `additive bits`

Question asked: Does the effort-to-information relation change with age?

Controls / structure: Controls the main effects of age and effort, then adds their interaction. Some versions also account for child identity.

How to read it: The `age_effort_coef` term is the interaction: whether the effort slope changes as age increases. The mixed model lets child baselines and linear age slopes vary; convergence warnings should be treated as diagnostics.


| effort_label | effect_scale | status | fitted_value_note | r2_observed_fitted | rmse | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | full fitted values | 0.6277 | 9.993 | -0.189 | <.001 | 6.402 | <.001 | -0.005014 | <.001 |
| Morphemes | additive bits | fit | full fitted values | 0.6152 | 10.16 | -0.1928 | <.001 | 5.497 | <.001 | 0.003414 | <.001 |
| Syllables: CMU/pkg | additive bits | fit | full fitted values | 0.6475 | 9.724 | -0.109 | 0.063 | 5.223 | <.001 | 0.00797 | <.001 |
| Syllables: pkg | additive bits | fit | full fitted values | 0.6311 | 9.948 | -0.07614 | 0.032 | 4.806 | <.001 | 0.01145 | <.001 |
| Phonemes | additive bits | fit | full fitted values | 0.6457 | 9.749 | -0.1004 | 0.005 | 2.079 | <.001 | 0.003128 | <.001 |

Diagnostic view of this subvariant: the line plot varies age while using a
single median effort reference for each effort unit. It is a plotting view of
the fitted subvariant, not another model. The shaded band is the model-based
95% confidence interval when statsmodels exposes one for that estimator.
Covariance-only subvariants can therefore have the same fitted line but
different uncertainty.

![M3 Linear mixed model + interaction, random child age slope adjusted age lines](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_adjusted_age_lines.png)

![M3 Linear mixed model + interaction, random child age slope low median high effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_interaction_age_lines.png)



### Model 3 Diagnostic Views

How to read the plot: each panel is one effort unit. The three lines are low,
median, and high effort values for that unit. Non-parallel lines mean the age
trajectory differs by effort level.

![M3 child-adjusted interaction lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)

Companion view: this keeps effort at a single median reference value, so it is
closer to the M1/M2 line-plot style. Use it to check whether the low/mid/high
split is creating a visual impression that is not visible in the central
reference trajectory.

![M3 median effort lines](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png)

Table columns for M3 add `age_effort_coef` and `age_effort_p`. A negative
interaction means the additional bits associated with effort are smaller at
older ages than at younger ages.

| effort_label | model_family_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | OLS + interaction + child fixed intercepts | additive bits | fit | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 | -0.003787 | 0.515 |
| Morphemes | OLS + interaction + child fixed intercepts | additive bits | fit | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 | 0.00228 | 0.727 |
| Syllables: CMU/pkg | OLS + interaction + child fixed intercepts | additive bits | fit | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 | 0.00703 | 0.252 |
| Syllables: pkg | OLS + interaction + child fixed intercepts | additive bits | fit | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 | 0.009859 | 0.022 |
| Phonemes | OLS + interaction + child fixed intercepts | additive bits | fit | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 | 0.002729 | 0.220 |

Takeaway: Primary result: the age-by-effort interaction coefficient is mostly positive across effort versions (1 negative, 4 positive; 1/5 p<.05).

## Model 4: Context Entropy Predicting Total Information

Primary formula:

```text
sum_bits ~ age + effort + context_entropy + C(child_id)
```

Question: does context entropy predict total utterance information after age,
effort, and child identity are controlled?

Here `context_entropy_bits` is Mistral next-token entropy after the preceding
caretaker context. It is measured in bits. Higher values mean the model is less
certain about the next token. This is a provisional context-predictability
measure, not sampled full-response entropy.

Context coverage summary:

| rows_with_context_entropy | unique_utterance_rows_with_context_entropy | children | mean_context_entropy_bits | median_context_entropy_bits |
| --- | --- | --- | --- | --- |
| 2207065 | 441413 | 21 | 6.343 | 6.382 |

### Model 4 Subvariants

Each subsection below is a real M4 subvariant because the context-entropy model
changes its estimator or formula. The diagnostic plots are shown separately for
M4a-M4e so the context-entropy alternatives are not hidden in one table.

### Subvariant: M4a: child FE + context entropy

Question asked: Does context entropy explain total child bits after age, effort, and child identity are controlled?

Formula:

```text
sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)
```

How to read it: each row repeats this subvariant for one effort unit. The
`entropy_coef` column is the estimated change in total bits for a one-bit
increase in context entropy after the listed controls. Interaction columns are
empty unless that subvariant includes the corresponding interaction.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_entropy_coef | age_entropy_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  |
| Morphemes | additive bits | fit | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  |
| Syllables: CMU/pkg | additive bits | fit | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |
| Syllables: pkg | additive bits | fit | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |
| Phonemes | additive bits | fit | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |

Diagnostic view of this subvariant: each panel holds the effort unit at a
single median reference and draws low, median, and high context-entropy
reference lines. This is a plot of the fitted subvariant, not a separate model.

![M4a: child FE + context entropy adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_m4a_context_entropy_adjusted_predictions.png)

### Subvariant: M4b: GEE + context entropy

Question asked: Does the same context-entropy effect appear in a population-average model clustered by child?

Formula:

```text
sum_bits ~ age_c + effort_c + context_entropy_c
```

How to read it: each row repeats this subvariant for one effort unit. The
`entropy_coef` column is the estimated change in total bits for a one-bit
increase in context entropy after the listed controls. Interaction columns are
empty unless that subvariant includes the corresponding interaction.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_entropy_coef | age_entropy_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | 0.6098 | -0.1268 | <.001 | 6.367 | <.001 | -0.4715 | <.001 |  |  |  |  |
| Morphemes | additive bits | fit | 0.5932 | -0.14 | <.001 | 5.488 | <.001 | -0.5122 | <.001 |  |  |  |  |
| Syllables: CMU/pkg | additive bits | fit | 0.6322 | -0.06438 | 0.011 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |
| Syllables: pkg | additive bits | fit | 0.6149 | -0.04795 | 0.034 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |
| Phonemes | additive bits | fit | 0.6287 | -0.06508 | 0.011 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |

Diagnostic view of this subvariant: each panel holds the effort unit at a
single median reference and draws low, median, and high context-entropy
reference lines. This is a plot of the fitted subvariant, not a separate model.

![M4b: GEE + context entropy adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_m4b_context_entropy_adjusted_predictions.png)

### Subvariant: M4c: Gamma/log GEE + context entropy

Question asked: Does the context-entropy effect survive a positive-continuous log-link sensitivity model?

Formula:

```text
sum_bits ~ age_c + effort_c + context_entropy_c
```

How to read it: each row repeats this subvariant for one effort unit. The
`entropy_coef` column is the estimated change in total bits for a one-bit
increase in context entropy after the listed controls. Interaction columns are
empty unless that subvariant includes the corresponding interaction.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_entropy_coef | age_entropy_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | log mean bits | fit | -1.784e+07 | -0.005747 | <.001 | 0.2153 | <.001 | -0.01973 | <.001 |  |  |  |  |
| Morphemes | log mean bits | fit | -1.232e+10 | -0.006534 | <.001 | 0.187 | <.001 | -0.02081 | <.001 |  |  |  |  |
| Syllables: CMU/pkg | log mean bits | fit | -2.542e+07 | -0.004073 | <.001 | 0.1812 | <.001 | -0.0216 | <.001 |  |  |  |  |
| Syllables: pkg | log mean bits | fit | -4.219e+06 | -0.003548 | 0.002 | 0.1672 | <.001 | -0.0215 | <.001 |  |  |  |  |
| Phonemes | log mean bits | fit | -1.394e+11 | -0.004539 | <.001 | 0.07359 | <.001 | -0.02295 | <.001 |  |  |  |  |

Diagnostic view of this subvariant: each panel holds the effort unit at a
single median reference and draws low, median, and high context-entropy
reference lines. This is a plot of the fitted subvariant, not a separate model.

![M4c: Gamma/log GEE + context entropy adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_m4c_context_entropy_adjusted_predictions.png)

### Subvariant: M4d: age by context entropy + child FE

Question asked: Does the context-entropy effect on total bits change with age after effort and child identity are controlled?

Formula:

```text
sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id)
```

How to read it: each row repeats this subvariant for one effort unit. The
`entropy_coef` column is the estimated change in total bits for a one-bit
increase in context entropy after the listed controls. Interaction columns are
empty unless that subvariant includes the corresponding interaction.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_entropy_coef | age_entropy_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 | 0.006141 | 0.284 |  |  |
| Morphemes | additive bits | fit | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 | 0.004709 | 0.339 |  |  |
| Syllables: CMU/pkg | additive bits | fit | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 | 0.003955 | 0.478 |  |  |
| Syllables: pkg | additive bits | fit | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 | 0.003946 | 0.481 |  |  |
| Phonemes | additive bits | fit | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 | 0.00465 | 0.407 |  |  |

Diagnostic view of this subvariant: each panel holds the effort unit at a
single median reference and draws low, median, and high context-entropy
reference lines. This is a plot of the fitted subvariant, not a separate model.

![M4d: age by context entropy + child FE adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_m4d_context_entropy_adjusted_predictions.png)

### Subvariant: M4e: M3 plus context entropy + child FE

Question asked: Does the age-by-effort interaction remain after adding context entropy and child identity?

Formula:

```text
sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id)
```

How to read it: each row repeats this subvariant for one effort unit. The
`entropy_coef` column is the estimated change in total bits for a one-bit
increase in context entropy after the listed controls. Interaction columns are
empty unless that subvariant includes the corresponding interaction.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_entropy_coef | age_entropy_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | 0.6266 | -0.1264 | <.001 | 6.374 | <.001 | -0.4715 | <.001 |  |  | -0.002583 | 0.720 |
| Morphemes | additive bits | fit | 0.6136 | -0.1409 | <.001 | 5.478 | <.001 | -0.5123 | <.001 |  |  | 0.003543 | 0.622 |
| Syllables: CMU/pkg | additive bits | fit | 0.6469 | -0.06733 | 0.015 | 5.212 | <.001 | -0.5399 | <.001 |  |  | 0.008716 | 0.179 |
| Syllables: pkg | additive bits | fit | 0.6307 | -0.0519 | 0.050 | 4.799 | <.001 | -0.541 | <.001 |  |  | 0.01187 | 0.023 |
| Phonemes | additive bits | fit | 0.6454 | -0.06773 | 0.018 | 2.075 | <.001 | -0.5812 | <.001 |  |  | 0.003377 | 0.239 |

Diagnostic view of this subvariant: each panel holds the effort unit at a
single median reference and draws low, median, and high context-entropy
reference lines. This is a plot of the fitted subvariant, not a separate model.

![M4e: M3 plus context entropy + child FE adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_m4e_context_entropy_adjusted_predictions.png)


### Model 4 Diagnostic Views

How to read the descriptive plot: it shows raw trends by context entropy and
age stage. It is not the controlled model; it is a sanity check.

![M4 descriptive bins](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png)

How to read the adjusted plot: each panel is one effort unit. The three lines
show low, median, and high context entropy while effort and child identity are
controlled.

![M4 adjusted predictions](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png)

Companion view: this holds context entropy at its median and varies continuous
effort instead. It checks whether M4's age trend is being driven by context
entropy references or by the effort reference.

![M4 effort-varied predictions](../figs/m1_m2_utterance_information_deep_dive/m4_effort_quantile_adjusted_predictions.png)

Table columns for M4 add `entropy_coef`/`entropy_p`. The table below shows only
the primary child-fixed-effect M4 version so the section stays readable.

| model_id | model_label | effort_label | outcome | fit_type | effect_scale | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_entropy_coef | age_entropy_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4a | M4a: child FE + context entropy | Words | sum_bits | ols_cluster | additive bits | fit | 441413 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  |
| M4a | M4a: child FE + context entropy | Morphemes | sum_bits | ols_cluster | additive bits | fit | 441413 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  |
| M4a | M4a: child FE + context entropy | Syllables: CMU/pkg | sum_bits | ols_cluster | additive bits | fit | 441413 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |
| M4a | M4a: child FE + context entropy | Syllables: pkg | sum_bits | ols_cluster | additive bits | fit | 441413 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |
| M4a | M4a: child FE + context entropy | Phonemes | sum_bits | ols_cluster | additive bits | fit | 441413 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |

## Model 5: Context Entropy + Low/Mid/High Effort Identity

Formula:

```text
sum_bits ~ age + context_entropy + C(effort_level) + C(child_id)
```

Question: does context entropy predict total information after we control child
identity and represent effort as a low/mid/high category rather than a
continuous count?

This model answers your effort-identity idea. The low/mid/high categories are
tertiles computed separately for each effort unit, so the words version uses
word-count tertiles, the phoneme version uses phoneme-count tertiles, and so
on.

### Model 5 Subvariants

Each subsection below is a real M5 subvariant because low/mid/high effort
identity is defined from a different effort unit. The low/mid/high split is
therefore one categorical effort strategy, not the only view of M5.

### Subvariant: M5 with effort levels from Words

Question asked: Does context entropy predict total information after child identity and low/mid/high effort level are controlled?

Formula:

```text
sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Words` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | 0.4363 | 0.0829 | <.001 | -0.4785 | <.001 |

### Subvariant: M5 with effort levels from Morphemes

Question asked: Does context entropy predict total information after child identity and low/mid/high effort level are controlled?

Formula:

```text
sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Morphemes` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | additive bits | fit | 0.4072 | 0.1197 | <.001 | -0.5201 | <.001 |

### Subvariant: M5 with effort levels from Syllables: CMU/pkg

Question asked: Does context entropy predict total information after child identity and low/mid/high effort level are controlled?

Formula:

```text
sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Syllables: CMU/pkg` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Syllables: CMU/pkg | additive bits | fit | 0.4639 | 0.07374 | 0.005 | -0.5254 | <.001 |

### Subvariant: M5 with effort levels from Syllables: pkg

Question asked: Does context entropy predict total information after child identity and low/mid/high effort level are controlled?

Formula:

```text
sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Syllables: pkg` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Syllables: pkg | additive bits | fit | 0.4407 | 0.1106 | <.001 | -0.5295 | <.001 |

### Subvariant: M5 with effort levels from Phonemes

Question asked: Does context entropy predict total information after child identity and low/mid/high effort level are controlled?

Formula:

```text
sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Phonemes` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Phonemes | additive bits | fit | 0.4633 | 0.08804 | <.001 | -0.5842 | <.001 |


### Model 5 Diagnostic Views

How to read the plot: each panel is one effort unit used to define low/mid/high
effort. Lines compare predicted total bits across age for those effort
categories, with context entropy set to its mean for plotting.

![M5 effort-level lines](../figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png)

Companion view: this averages over the low/mid/high effort levels instead of
splitting the plot by them. Use it to check whether the visible age trend is
specific to the tertile split or remains when the effort-level categories are
averaged over.

![M5 and M6 averaged effort-level lines](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png)

Table columns for M5: `effort_label` says which unit created the effort
tertiles; `age_coef` is the age effect; `context_entropy_coef` is the entropy
effect after effort category and child identity are controlled.

| model_id | model_label | effort_label | formula | fit_type | effect_scale | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5 | M5: context entropy + effort level + child FE | Words | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4363 | 0.0829 | <.001 | -0.4785 | <.001 |
| M5 | M5: context entropy + effort level + child FE | Morphemes | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4072 | 0.1197 | <.001 | -0.5201 | <.001 |
| M5 | M5: context entropy + effort level + child FE | Syllables: CMU/pkg | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4639 | 0.07374 | 0.005 | -0.5254 | <.001 |
| M5 | M5: context entropy + effort level + child FE | Syllables: pkg | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4407 | 0.1106 | <.001 | -0.5295 | <.001 |
| M5 | M5: context entropy + effort level + child FE | Phonemes | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4633 | 0.08804 | <.001 | -0.5842 | <.001 |

## Model 6: Age, Context, and Effort-Level Interactions

Formula:

```text
sum_bits ~ age * context_entropy
         + age * C(effort_level)
         + context_entropy * C(effort_level)
         + C(child_id)
```

Question: do developmental trajectories differ by both context entropy and
low/mid/high effort level?

This is the more exploratory version of M5. It is intentionally flexible, but
still does not put all continuous effort measures into one model.

### Model 6 Subvariants

Each subsection below is a real M6 subvariant because low/mid/high effort
identity is defined from a different effort unit before interactions are fit.

### Subvariant: M6 with effort levels from Words

Question asked: Do age, context entropy, and effort level interact when predicting total information?

Formula:

```text
sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Words` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Words | additive bits | fit | 0.4413 | -0.0775 | 0.023 | -0.3592 | <.001 |

### Subvariant: M6 with effort levels from Morphemes

Question asked: Do age, context entropy, and effort level interact when predicting total information?

Formula:

```text
sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Morphemes` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morphemes | additive bits | fit | 0.4133 | -0.07519 | 0.050 | -0.3338 | <.001 |

### Subvariant: M6 with effort levels from Syllables: CMU/pkg

Question asked: Do age, context entropy, and effort level interact when predicting total information?

Formula:

```text
sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Syllables: CMU/pkg` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Syllables: CMU/pkg | additive bits | fit | 0.4699 | -0.06767 | 0.027 | -0.3802 | <.001 |

### Subvariant: M6 with effort levels from Syllables: pkg

Question asked: Do age, context entropy, and effort level interact when predicting total information?

Formula:

```text
sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Syllables: pkg` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Syllables: pkg | additive bits | fit | 0.4478 | -0.05867 | 0.061 | -0.3742 | <.001 |

### Subvariant: M6 with effort levels from Phonemes

Question asked: Do age, context entropy, and effort level interact when predicting total information?

Formula:

```text
sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id)
```

How to read it: this is a real subvariant because the low/mid/high effort
identity is built from `Phonemes` only. The table shows whether age and
context entropy still predict total bits after that categorical effort identity
and child identity are controlled.

| effort_label | effect_scale | status | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Phonemes | additive bits | fit | 0.469 | -0.08116 | 0.007 | -0.3343 | <.001 |


### Model 6 Diagnostic Views

How to read the plot: each panel is one effort unit. If the low/mid/high lines
separate or change slope differently over age, then the model is finding
evidence that developmental information trajectories differ by effort category.

![M6 effort-level interaction lines](../figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png)

Companion view: the averaged effort-level plot above also includes M6. This is
important because low/mid/high effort categories are only one discretization of
effort, so they should not be the sole basis for interpreting M6.

Table columns for M6 are the same as M5, but the formula includes interactions.
The compact table emphasizes the main age and context-entropy terms; the
interaction coefficients are in the coefficient CSV.

| model_id | model_label | effort_label | formula | fit_type | effect_scale | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M6 | M6: age/context interactions + effort level + child FE | Words | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4413 | -0.0775 | 0.023 | -0.3592 | <.001 |
| M6 | M6: age/context interactions + effort level + child FE | Morphemes | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4133 | -0.07519 | 0.050 | -0.3338 | <.001 |
| M6 | M6: age/context interactions + effort level + child FE | Syllables: CMU/pkg | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4699 | -0.06767 | 0.027 | -0.3802 | <.001 |
| M6 | M6: age/context interactions + effort level + child FE | Syllables: pkg | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.4478 | -0.05867 | 0.061 | -0.3742 | <.001 |
| M6 | M6: age/context interactions + effort level + child FE | Phonemes | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | ols_cluster | additive bits | fit | 441413 | 21 | 0.469 | -0.08116 | 0.007 | -0.3343 | <.001 |

How to read the coefficient heatmap: rows are selected M5/M6 terms and columns
are the effort units used to create low/mid/high categories. Red/blue direction
shows whether each coefficient is positive or negative.

![M5/M6 selected coefficients](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png)

## M1 vs M2 Sign Reversal

The important comparison is conceptual, not just numerical. M1 pools all
children. M2 controls child identity. If the age coefficient changes sign from
M1 to M2, the pooled age trend was mixing developmental change with which
children contributed data at which ages.

How to read the plot: the same effort units are shown for both models. M2 is
the child-adjusted version; M1 is the pooled version.

![Adjusted trajectories](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)

## Analysis Artifacts

The full sensitivity outputs remain available as CSV/PNG files. They are not
all printed in the report because the report is meant to be readable.

- M1/M2 core fits: `results/m1_m2_utterance_information_deep_dive/model_fit_summary.csv`
- M1/M2 coefficients: `results/m1_m2_utterance_information_deep_dive/model_coefficients.csv`
- M3 and sensitivity families: `results/m1_m2_utterance_information_deep_dive/expanded_model_family_summary.csv`
- M4 context models: `results/m1_m2_utterance_information_deep_dive/m4_context_entropy_model_summary.csv`
- M5/M6 effort-level models: `results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_model_summary.csv`
- M5/M6 coefficients: `results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_coefficients.csv`
- Predictions: `results/m1_m2_utterance_information_deep_dive/adjusted_age_predictions.csv`
- Context predictions: `results/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.csv`
- Effort-level predictions: `results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.csv`

## Data Audit

Rows used in this report:

| rows | children | datasets | age_min | age_max | mean_sum_bits | median_sum_bits |
| --- | --- | --- | --- | --- | --- | --- |
| 446985 | 21 | 3 | 11.13 | 62.4 | 26.73 | 23.13 |

Rows by age bin:

| age_bin | rows | children | mean_sum_bits | mean_words | mean_morphemes | mean_syllables_cmu_or_pkg | mean_phonemes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 006-023 | 62816 | 17 | 23.13 | 1.999 | 2.206 | 2.601 | 6.487 |
| 024-029 | 162210 | 21 | 24.81 | 2.337 | 2.595 | 2.862 | 7.136 |
| 030-035 | 142447 | 20 | 26.8 | 2.794 | 3.116 | 3.353 | 8.361 |
| 036-041 | 37683 | 8 | 31.03 | 3.261 | 3.601 | 3.874 | 9.482 |
| 042-047 | 16345 | 5 | 32.89 | 3.786 | 4.24 | 4.508 | 11.04 |
| 048-053 | 12909 | 3 | 36.99 | 3.956 | 4.455 | 4.691 | 11.5 |
| 054-059 | 10033 | 2 | 37.77 | 4.133 | 4.681 | 4.909 | 12.07 |
| 060-065 | 2542 | 2 | 34.75 | 4.006 | 4.485 | 4.7 | 11.65 |
