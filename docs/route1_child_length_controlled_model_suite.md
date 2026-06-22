# Child Informativeness At Fixed Utterance Effort

Generated on 2026-06-20.

This report is the child-only Route 1 modeling suite. The outcome is `sum_bits`, meaning total model-estimated information in the child utterance. Every scientific formula includes an explicit target-effort control or exact-length category control, because raw total bits are structurally entangled with utterance length and child MLU increases with age.

The report deliberately emphasizes regression-line plots rather than tables. The CSV artifacts contain the exact coefficients, p-values, fit metrics, fixed-effort prediction grids, and saved model paths.

## Scientific Contract

- We are not asking whether older children talk more. They do.
- We are asking whether, for utterances of the same size, older children produce utterances with more or less information.
- The fixed-effort lines are the main evidence because they hold utterance size constant.
- The exact-length formulas are the strongest MLU check because MLU cannot explain an age slope estimated inside one exact utterance length.
- A global age effect across lengths is interpretable only when it is model-adjusted or averaged over fixed-effort slices. A raw average across utterances would mostly rediscover MLU.
- Repeated utterances from the same children and sessions motivate GEE and mixed-model checks, not only OLS.

## Why This Is Not Just MLU

MLU is a change in the distribution of utterance lengths with age. The exact-length models remove that explanation by estimating age patterns while length is either fixed in the plotted slice or represented by exact length categories. In a two-word comparison, every utterance has two words; in a three-word comparison, every utterance has three words. MLU can change how often those lengths occur, but it cannot by itself create a developmental slope inside a fixed-length comparison.

## Statistical Strategy

Utterances are repeated observations nested in sessions and children. The estimator grid therefore includes a transparent row-level child fixed-effect model, session/exact-effort aggregate checks, GEE models grouped by child, Gamma/log positive-outcome checks, and mixed models with child and session random-effect structures. These are sensitivity layers around the same length-controlled scientific contrast.

## Run Summary

- Requested model fits: `189`.
- Successful fits: `189`.
- Skipped or failed fits: `0`. Details are saved in `model_summary.csv`.
- Children represented in successful fits: `21`.
- Sessions represented in successful fits: `983`.
- Observation/cell count range across successful fits: `26,457` to `446,985`.
- Mean fixed-effort age slope across saved prediction lines: `-0.475` bits per six months.
- Downward fixed-effort lines: `2,119`; upward fixed-effort lines: `149`.
- Primary exact-length slopes from F18-F21: `41` downward and `7` upward.
- Upward primary exact-length slopes occur at exact lengths: `8, 10, 11, 12`.
- The longest exact lengths are much sparser and should be read cautiously: 10 words=1,594 rows, 11 words=896 rows, 12 words=591 rows.

## Formula Guide

### F01: Age at fixed effort

**Question.** Does age predict total utterance information after utterance effort is held constant?

**Formula.** `sum_bits ~ age_c + effort_c`

**Meaning.** This is the minimum defensible Route 1 formula. The outcome is total bits for the child utterance, age is the developmental predictor, and effort is the utterance size control. A negative age line here means that, among utterances of the same size, older children produce utterances that are less surprising to the model.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F02: Age by effort

**Question.** Does the developmental age effect depend on how large the utterance is?

**Formula.** `sum_bits ~ age_c + effort_c + age_c:effort_c`

**Meaning.** This is the basic fixed-effort interaction model. It lets one-word, two-word, and longer utterances have different developmental slopes. This directly tests whether a single global age effect is hiding different fixed-length trajectories.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F03: Parent effort control

**Question.** Does preceding caretaker-context amount explain extra child utterance information?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c`

**Meaning.** This model keeps child utterance effort controlled and adds the amount of preceding caretaker context in the same effort unit. It asks whether a child utterance is more or less informative when it follows a longer local context.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F04: Age by parent effort

**Question.** Does the effect of preceding caretaker effort change with child age?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Meaning.** This model tests whether the relation between caretaker-context amount and child information is developmentally changing, while still comparing child utterances at matched target effort.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F05: Effort by parent effort

**Question.** Does preceding caretaker effort matter differently for short versus long child utterances?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + effort_c:parent_context_effort_c`

**Meaning.** This model asks whether the local context amount changes the slope linking child utterance size to child utterance information. It is a context-by-length check, not a raw length-growth check.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F06: Parent interaction stress test

**Question.** Do the age, target-effort, and parent-context-effort relations survive together?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c`

**Meaning.** This is the richer parent-context formula. It keeps the key fixed-effort age-by-effort term and checks whether parent context effort changes either the developmental trajectory or the effort-information relation.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F07: Question type control

**Question.** Does the age effect remain after broad preceding-context question type is controlled?

**Formula.** `sum_bits ~ age_c + effort_c + C(question_type)`

**Meaning.** This formula compares fixed-effort child utterances while accounting for whether the preceding context is not a question, a wh-question, a yes/no question, another question, or empty. It is a local discourse control.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F08: Context entropy control

**Question.** Does age still predict child utterance information after local context entropy is controlled?

**Formula.** `sum_bits ~ age_c + effort_c + context_entropy_c`

**Meaning.** This formula adds the available context-entropy feature. It separates the developmental fixed-effort age pattern from the fact that some contexts make upcoming language more predictable than others.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F09: All context controls

**Question.** Does the fixed-effort age effect remain after the main local-context controls are added together?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + context_entropy_c + C(question_type)`

**Meaning.** This is the compact contextual-control model. It estimates the age pattern at fixed child effort while simultaneously controlling caretaker context amount, context entropy, and broad question type.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F10: All context controls with age by effort

**Question.** Does the fixed-effort age-by-effort pattern remain after the main context controls are added?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:effort_c`

**Meaning.** This is a strong candidate headline formula because it keeps the fixed-length interpretation explicit and adds the major local-context confounds.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F11: Entropy interactions

**Question.** Does sensitivity to context entropy change with child age or child utterance effort?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + effort_c:context_entropy_c`

**Meaning.** This formula checks whether the context-entropy control is only an additive nuisance variable or whether entropy changes the developmental and fixed-effort slopes themselves.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F12: Full context interaction stress test

**Question.** Do the developmental fixed-effort results persist under a richer context-interaction stress test?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + age_c:context_entropy_c + effort_c:context_entropy_c + parent_context_effort_c:context_entropy_c`

**Meaning.** This is deliberately not the simplest interpretation model. It is a stress test for the claim that the age pattern is not just an artifact of parent context effort, entropy, or their interaction with child effort.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F13: Question interactions

**Question.** Does the developmental or entropy effect differ by broad preceding-context question type?

**Formula.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:C(question_type) + context_entropy_c:C(question_type)`

**Meaning.** This formula checks whether wh-questions, yes/no questions, and other contexts produce different fixed-effort developmental patterns.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F14: Curved age trajectory

**Question.** Is the fixed-effort developmental trajectory curved rather than straight?

**Formula.** `sum_bits ~ age_c + I(age_c ** 2) + effort_c`

**Meaning.** This formula keeps effort controlled but allows the age trajectory to bend. It is useful if the decline or increase in fixed-effort information is strongest at early ages and then flattens later.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F15: Curved age by effort

**Question.** Does the curved developmental trajectory differ across utterance sizes?

**Formula.** `sum_bits ~ age_c + I(age_c ** 2) + effort_c + age_c:effort_c + I(age_c ** 2):effort_c`

**Meaning.** This is the nonlinear version of the age-by-effort model. It checks whether one-word and longer utterances have different curved age trajectories.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F16: Age-bin trajectory

**Question.** Do developmental age-bin differences remain after target effort is controlled?

**Formula.** `sum_bits ~ C(age_bin) + effort_c`

**Meaning.** This formula avoids imposing a straight age slope. It compares age bins directly, while still holding utterance effort constant.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F17: Age-bin by effort

**Question.** Do age-bin differences depend on utterance effort?

**Formula.** `sum_bits ~ C(age_bin) + effort_c + C(age_bin):effort_c`

**Meaning.** This is the categorical-age version of the fixed-effort interaction model. It asks whether developmental differences look different for short and long utterances without assuming a linear age trend.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F18: Exact-length fixed effects

**Question.** Does age predict total information after each exact utterance length gets its own baseline?

**Formula.** `sum_bits ~ age_c + C(effort_value_int)`

**Meaning.** This model treats length as a category, not as a linear covariate. It removes the MLU explanation by comparing the age trajectory after arbitrary differences among exact word counts have been absorbed.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F19: Exact-length age slopes

**Question.** Do the age slopes remain downward inside exact utterance-length strata?

**Formula.** `sum_bits ~ age_c + C(effort_value_int) + age_c:C(effort_value_int)`

**Meaning.** This is the main MLU-proof formula. It estimates a separate age slope for each exact utterance length, so the developmental effect is read within same-length comparisons rather than across the changing MLU distribution.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F20: Exact-length fixed effects with context controls

**Question.** Does the exact-length age effect remain after the main local-context controls?

**Formula.** `sum_bits ~ age_c + C(effort_value_int) + parent_context_effort_c + context_entropy_c + C(question_type)`

**Meaning.** This model keeps exact length categorical and adds caretaker context effort, context entropy, and question type. It asks whether the same-length age trajectory survives the major local context controls.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

### F21: Exact-length age slopes with context controls

**Question.** Do exact-length age slopes remain after local-context controls?

**Formula.** `sum_bits ~ age_c + C(effort_value_int) + age_c:C(effort_value_int) + parent_context_effort_c + context_entropy_c + C(question_type)`

**Meaning.** This is the strongest current same-length formula. Each exact utterance length can have its own age slope, and the model still controls parent context effort, context entropy, question type, and child identity through the estimator.

**Length control.** This formula controls target effort either with `effort_c` or exact-length categories, so it does not interpret age through raw growth in MLU.

## Estimator Guide

### row_ols_fe_cluster

**Model.** Row-level OLS with child fixed intercepts and child-clustered SE

**What it does.** Fits the utterance-level model directly and adds one intercept for each child. Standard errors are clustered by child, so repeated utterances from the same child are not treated as independent for uncertainty.

**Why it is here.** This is the clearest fixed-effort baseline: it answers the Route 1 question on the original utterance rows while controlling child identity.

**Data scale.** `row`. **Covariance/dependence structure.** `cluster_child`.

### agg_ols_fe_cluster

**Model.** Session/effort-cell OLS with child fixed intercepts and child-clustered SE

**What it does.** Averages utterances into child-session-exact-effort-context cells, then fits OLS with child fixed intercepts and child-clustered standard errors.

**Why it is here.** It prevents sessions with many repeated utterances from dominating the analysis and checks that the row-level result is not just a high-row-count-session result.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `cluster_child`.

### agg_glm_gaussian

**Model.** Session/effort-cell Gaussian GLM with child fixed intercepts

**What it does.** Fits the same mean formula through the GLM framework with a Gaussian outcome distribution. It is close to OLS but uses the generalized-model machinery.

**Why it is here.** It is a bridge from ordinary regression to the generalized estimators used for positive skewed outcomes.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `model_based`.

### agg_glm_gamma_log

**Model.** Session/effort-cell Gamma/log GLM with child fixed intercepts

**What it does.** Fits positive total bits with a Gamma mean-variance relation and a log link, while keeping the same length-controlled formula and child fixed intercepts.

**Why it is here.** Total bits are positive and often right-skewed, so this checks whether the fixed-effort age result depends on a Gaussian error assumption.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `model_based`.

### agg_gee_gaussian

**Model.** Session/effort-cell Gaussian GEE grouped by child

**What it does.** Fits a population-average Gaussian model with an exchangeable working correlation for repeated cells from the same child. Child fixed intercepts remain in the mean model.

**Why it is here.** This estimates the mean relation while representing within-child dependence, which is essential for repeated utterances from the same children.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `exchangeable_child`.

### agg_gee_gamma_log

**Model.** Session/effort-cell Gamma/log GEE grouped by child

**What it does.** Combines a positive skewed Gamma/log mean with GEE's child-level working correlation.

**Why it is here.** This checks whether the positive-outcome GEE story agrees with the fixed-effort OLS and mixed-model stories.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `exchangeable_child`.

### agg_mixed_random_intercept

**Model.** Session/effort-cell mixed model with random child intercept

**What it does.** Fits a linear mixed model where each child has a random intercept rather than a fixed intercept.

**Why it is here.** This is the standard repeated-measures model when children are sampled units and the analysis should estimate child-to-child variability.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `random_child_intercept`.

### agg_mixed_random_age_slope

**Model.** Session/effort-cell mixed model with random child age slope

**What it does.** Allows children to differ both in their baseline information level and in their developmental age slope.

**Why it is here.** This is the main check for whether one average developmental line is hiding children with different age trajectories.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `random_child_intercept_age_slope`.

### agg_mixed_session_intercept

**Model.** Session/effort-cell mixed model with child and session intercepts

**What it does.** Adds a child random intercept and a session-level variance component.

**Why it is here.** The data are repeated utterances inside sessions inside children. This model asks whether the age effect survives after both levels are represented.

**Data scale.** `aggregate`. **Covariance/dependence structure.** `random_child_and_session_intercepts`.

## Regression Plots

### Model-free descriptive means within exact utterance lengths. This is a sanity check, not the adjusted inferential estimate.

![observed_exact_length_age_bins](../figs/route1_child_length_controlled_model_suite/observed_exact_length_age_bin_means.png)

### Age slopes estimated inside exact utterance-length comparisons. This is the direct check that the pattern is not produced by the age-related MLU shift.

![mlu_proof_exact_length_slopes](../figs/route1_child_length_controlled_model_suite/mlu_proof_exact_length_age_slopes.png)

### Mean slope in predicted total bits per six months, averaged across fixed-effort lines.

![slope_heatmap](../figs/route1_child_length_controlled_model_suite/slope_heatmap_formula_by_estimator.png)

### Observed-vs-fitted variance explained. For non-OLS estimators this is descriptive, not a classical OLS R2.

![variance_explained](../figs/route1_child_length_controlled_model_suite/variance_explained_by_formula_estimator.png)

### Control-dominance diagnostic. Large effort terms are treated as evidence that raw total bits are length-confounded, not as the substantive finding.

![variable_importance](../figs/route1_child_length_controlled_model_suite/variable_importance_standardized_coefficients.png)

### Primary fixed-effort lines

Each line is a model prediction at one exact utterance size. A downward line means predicted total bits decline with age when that size is held fixed. These are the key plots for separating communicative informativeness from raw MLU growth.

**F01: Age at fixed effort**

![F01](../figs/route1_child_length_controlled_model_suite/f01_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F02: Age by effort**

![F02](../figs/route1_child_length_controlled_model_suite/f02_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F03: Parent effort control**

![F03](../figs/route1_child_length_controlled_model_suite/f03_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F04: Age by parent effort**

![F04](../figs/route1_child_length_controlled_model_suite/f04_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F05: Effort by parent effort**

![F05](../figs/route1_child_length_controlled_model_suite/f05_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F06: Parent interaction stress test**

![F06](../figs/route1_child_length_controlled_model_suite/f06_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F07: Question type control**

![F07](../figs/route1_child_length_controlled_model_suite/f07_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F08: Context entropy control**

![F08](../figs/route1_child_length_controlled_model_suite/f08_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F09: All context controls**

![F09](../figs/route1_child_length_controlled_model_suite/f09_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F10: All context controls with age by effort**

![F10](../figs/route1_child_length_controlled_model_suite/f10_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F11: Entropy interactions**

![F11](../figs/route1_child_length_controlled_model_suite/f11_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F12: Full context interaction stress test**

![F12](../figs/route1_child_length_controlled_model_suite/f12_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F13: Question interactions**

![F13](../figs/route1_child_length_controlled_model_suite/f13_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F14: Curved age trajectory**

![F14](../figs/route1_child_length_controlled_model_suite/f14_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F15: Curved age by effort**

![F15](../figs/route1_child_length_controlled_model_suite/f15_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F16: Age-bin trajectory**

![F16](../figs/route1_child_length_controlled_model_suite/f16_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F17: Age-bin by effort**

![F17](../figs/route1_child_length_controlled_model_suite/f17_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F18: Exact-length fixed effects**

![F18](../figs/route1_child_length_controlled_model_suite/f18_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F19: Exact-length age slopes**

![F19](../figs/route1_child_length_controlled_model_suite/f19_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F20: Exact-length fixed effects with context controls**

![F20](../figs/route1_child_length_controlled_model_suite/f20_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

**F21: Exact-length age slopes with context controls**

![F21](../figs/route1_child_length_controlled_model_suite/f21_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

### Estimator comparison lines

These lines average over the plotted fixed-effort slices. This is the defensible version of a global effect across lengths: it is model-adjusted and length-controlled, not a raw mean over utterances of different sizes.

**F01: Age at fixed effort**

![F01 estimator comparison](../figs/route1_child_length_controlled_model_suite/f01_k3_nb_words_estimator_mean_lines.png)

**F02: Age by effort**

![F02 estimator comparison](../figs/route1_child_length_controlled_model_suite/f02_k3_nb_words_estimator_mean_lines.png)

**F03: Parent effort control**

![F03 estimator comparison](../figs/route1_child_length_controlled_model_suite/f03_k3_nb_words_estimator_mean_lines.png)

**F04: Age by parent effort**

![F04 estimator comparison](../figs/route1_child_length_controlled_model_suite/f04_k3_nb_words_estimator_mean_lines.png)

**F05: Effort by parent effort**

![F05 estimator comparison](../figs/route1_child_length_controlled_model_suite/f05_k3_nb_words_estimator_mean_lines.png)

**F06: Parent interaction stress test**

![F06 estimator comparison](../figs/route1_child_length_controlled_model_suite/f06_k3_nb_words_estimator_mean_lines.png)

**F07: Question type control**

![F07 estimator comparison](../figs/route1_child_length_controlled_model_suite/f07_k3_nb_words_estimator_mean_lines.png)

**F08: Context entropy control**

![F08 estimator comparison](../figs/route1_child_length_controlled_model_suite/f08_k3_nb_words_estimator_mean_lines.png)

**F09: All context controls**

![F09 estimator comparison](../figs/route1_child_length_controlled_model_suite/f09_k3_nb_words_estimator_mean_lines.png)

**F10: All context controls with age by effort**

![F10 estimator comparison](../figs/route1_child_length_controlled_model_suite/f10_k3_nb_words_estimator_mean_lines.png)

**F11: Entropy interactions**

![F11 estimator comparison](../figs/route1_child_length_controlled_model_suite/f11_k3_nb_words_estimator_mean_lines.png)

**F12: Full context interaction stress test**

![F12 estimator comparison](../figs/route1_child_length_controlled_model_suite/f12_k3_nb_words_estimator_mean_lines.png)

**F13: Question interactions**

![F13 estimator comparison](../figs/route1_child_length_controlled_model_suite/f13_k3_nb_words_estimator_mean_lines.png)

**F14: Curved age trajectory**

![F14 estimator comparison](../figs/route1_child_length_controlled_model_suite/f14_k3_nb_words_estimator_mean_lines.png)

**F15: Curved age by effort**

![F15 estimator comparison](../figs/route1_child_length_controlled_model_suite/f15_k3_nb_words_estimator_mean_lines.png)

**F16: Age-bin trajectory**

![F16 estimator comparison](../figs/route1_child_length_controlled_model_suite/f16_k3_nb_words_estimator_mean_lines.png)

**F17: Age-bin by effort**

![F17 estimator comparison](../figs/route1_child_length_controlled_model_suite/f17_k3_nb_words_estimator_mean_lines.png)

**F18: Exact-length fixed effects**

![F18 estimator comparison](../figs/route1_child_length_controlled_model_suite/f18_k3_nb_words_estimator_mean_lines.png)

**F19: Exact-length age slopes**

![F19 estimator comparison](../figs/route1_child_length_controlled_model_suite/f19_k3_nb_words_estimator_mean_lines.png)

**F20: Exact-length fixed effects with context controls**

![F20 estimator comparison](../figs/route1_child_length_controlled_model_suite/f20_k3_nb_words_estimator_mean_lines.png)

**F21: Exact-length age slopes with context controls**

![F21 estimator comparison](../figs/route1_child_length_controlled_model_suite/f21_k3_nb_words_estimator_mean_lines.png)

## Saved Artifacts

The reusable model memory for this run is saved on disk:

```text
results/route1_child_length_controlled_model_suite/model_summary.csv
results/route1_child_length_controlled_model_suite/coefficient_long.csv
results/route1_child_length_controlled_model_suite/fixed_effort_predictions.csv.gz
results/route1_child_length_controlled_model_suite/fixed_slice_slopes.csv
results/route1_child_length_controlled_model_suite/exact_length_observed_age_bin_means.csv
results/route1_child_length_controlled_model_suite/formula_definitions.csv
results/route1_child_length_controlled_model_suite/estimator_definitions.csv
results/route1_child_length_controlled_model_suite/models
figs/route1_child_length_controlled_model_suite
```

To regenerate only one layer later:

```bash
.venv/bin/python src/build_route1_child_length_controlled_model_suite.py --stage fit
.venv/bin/python src/build_route1_child_length_controlled_model_suite.py --stage plot
.venv/bin/python src/build_route1_child_length_controlled_model_suite.py --stage report
```
