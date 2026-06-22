# Route 1 Formula-Permutation Estimator Report

This is an internal model-selection report for Route 1. It is organized around formulas, not around a compact aggregate grid.

The key question is: at the same production-effort level, do children's utterances contain more or less surprisal as they get older? The primary evidence for that question is the row-level fixed-effort Atlas: separate lines for fixed word counts, plus the global average across those fixed-size lines.

## Non-Negotiable Controls

- Every formula includes age at session.
- Every formula includes child utterance effort.
- Every fixed-effect estimator includes `C(child_id)`.
- MixedLM controls child identity with random child intercepts, and the random-slope version also allows child-specific age trajectories.
- GEE models include `C(child_id)` in the mean model and cluster by child, so they handle both child identity and within-child repeated measurements.

## Outcome And Repeated-Measurement Frame

- Scientific outcome: `sum_bits`, the total information in one utterance.
- Estimator-grid outcome used here: `mean_sum_bits`, the mean utterance `sum_bits` in child-session/effort-band cells. This makes GEE/GLM/MixedLM screening tractable and reduces row-level pseudo-replication.
- Primary row-level Atlas plots remain the evidence to promote later; this report is for choosing which formulas deserve row-level promotion.
- Read age coefficients as conditional information at fixed effort and controls, not as raw growth in utterance length.
- If a row-level fixed-effort plot and an aggregate estimator-screen plot visually disagree, treat the row-level fixed-effort plot as the scientific Route 1 answer. The aggregate plot is an estimator-sensitivity screen, not the main result.

## Formula Grid

The grid starts from:

`sum_bits ~ age_c + effort_c + C(child_id)`

Then it toggles context entropy, parent/caretaker context effort, question/form type, `age_c:effort_c`, `age_c:context_entropy_c`, and `age_c:parent_context_effort_c`. Interactions are only fit when the lower-level predictors are also present.

Total formulas fit: **36**. Estimator families per formula: **7**.

## Cross-Formula Plots

![Nested delta R2 across formula permutations](../figs/route1_formula_permutation_estimator_report/formula_nested_delta_r2_top24.png)

**Variable-importance read.** This is not causal importance. It shows which added controls/interactions improve observed-vs-fitted R2 relative to the base age + effort + child-identity formula.

![Age effect forest across estimator families](../figs/route1_formula_permutation_estimator_report/formula_age_effect_forest_top18.png)

**Age-effect read.** Additive-bit and log-mean-bit estimators are separated because their coefficients are on different scales. Prediction lines are safer than comparing raw log and additive coefficients directly.

## Important Interpretation Guardrail

The formula grid below includes an aggregate repeated-measures screen, so formulas can look better by R2 while still showing a positive aggregate age coefficient. That does **not** by itself mean older children are less efficient. The communicative-efficiency claim is read from row-level fixed-effort Atlas plots and the global fixed-effort summaries. Use the aggregate estimator screen to choose formulas and assess estimator sensitivity; do not treat it as the scientific conclusion.

## Source Reports Used

- Row-level real-child Atlas: [utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html)
- Heldout prediction report: [utterance_information_route1_heldout_real_child_prediction_report.html](utterance_information_route1_heldout_real_child_prediction_report.html)
- Caretaker contrast report: [utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html)

## Formula Deep Dives

Every formula below has one section, and each section has one subsection per estimator family. Sections are ordered in formula-grid order so the simpler controls and interactions are readable before the richer permutations.

## F01. age + child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7869; delta vs base F01 = 0.00000.

### Primary Row-Level Fixed-Effort Atlas

![F01 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m2_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M2`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.122, range -0.122 to -0.122 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F01 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f01_m2_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F01_estimator_lines](../figs/route1_formula_permutation_estimator_report/f01_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F01_term_forest](../figs/route1_formula_permutation_estimator_report/f01_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1585, p=0.071. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1127, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1585, p=0.063. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1127, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1889. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.150. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1585, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1127, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1889. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7729. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1585, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1127, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7730. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1737, p=0.869. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1128, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 87.811558; The Hessian matrix at the estimated parameter values is not positive definite.

## F02. age + child effort with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7877; delta vs base F01 = 0.00076.

### Primary Row-Level Fixed-Effort Atlas

![F02 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M3`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.136, range -0.157 to -0.115 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F02 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f02_m3_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F02_estimator_lines](../figs/route1_formula_permutation_estimator_report/f02_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F02_term_forest](../figs/route1_formula_permutation_estimator_report/f02_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7877. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1590, p=0.074. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0897, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0166, p=0.095. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7877. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1590, p=0.066. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0897, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0166, p=0.086. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1805. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.121. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7877. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1590, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0897, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0166, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1805. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7736. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1614, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0909, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0164, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7738. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2082, p=0.843. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0820, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0192, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 92.071488; The Hessian matrix at the estimated parameter values is not positive definite.

## F03. age + child effort + question/form type

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and question/form type?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + C(question_type)`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00019.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F03_estimator_lines](../figs/route1_formula_permutation_estimator_report/f03_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F03_term_forest](../figs/route1_formula_permutation_estimator_report/f03_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1593, p=0.059. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1593, p=0.052. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0029, p=0.162. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1108, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1593, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0029, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1108, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7729. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1593, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7731. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1793, p=0.865. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0962, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F04. age + child effort + question/form type with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7879; delta vs base F01 = 0.00096.

### Primary Row-Level Fixed-Effort Atlas

![F04 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M4c`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.142, range -0.164 to -0.121 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F04 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f04_m4c_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F04_estimator_lines](../figs/route1_formula_permutation_estimator_report/f04_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F04_term_forest](../figs/route1_formula_permutation_estimator_report/f04_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1598, p=0.063. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0733, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.094. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1598, p=0.055. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0733, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.084. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1789. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0029, p=0.128. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1118, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1598, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0733, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1789. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0029, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1118, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7736. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1598, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0733, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7738. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2143, p=0.839. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0647, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0194, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F05. age + child effort + parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7870; delta vs base F01 = 0.00007.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F05_estimator_lines](../figs/route1_formula_permutation_estimator_report/f05_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F05_term_forest](../figs/route1_formula_permutation_estimator_report/f05_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7870. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1637, p=0.066. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1163, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0720, p=0.394. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7870. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1637, p=0.058. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1163, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0720, p=0.381. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1875. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.148. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0006, p=0.608. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7870. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1637, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1163, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0720, p=0.326. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1875. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0006, p=0.671. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7728. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1660, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1168, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0641, p=0.375. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7729. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1778, p=0.867. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1162, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0566, p=0.428. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 90.699991; The Hessian matrix at the estimated parameter values is not positive definite.

## F06. age + child effort + parent context effort with age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00015.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F06_estimator_lines](../figs/route1_formula_permutation_estimator_report/f06_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F06_term_forest](../figs/route1_formula_permutation_estimator_report/f06_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1651, p=0.066. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1137, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0719, p=0.455. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0068, p=0.293. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1651, p=0.058. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1137, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0719, p=0.442. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0068, p=0.279. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.148. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1115, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0005, p=0.794. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0006, p=0.003. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1651, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1137, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0719, p=0.326. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0068, p=0.303. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1115, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0005, p=0.707. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0006, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7730. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1672, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1142, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0644, p=0.372. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0067, p=0.304. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7730. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1734, p=0.869. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1146, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0564, p=0.430. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0058, p=0.384. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F07. age + child effort + parent context effort with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7877; delta vs base F01 = 0.00081.

### Primary Row-Level Fixed-Effort Atlas

![F07 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4a_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M4a`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.131, range -0.154 to -0.109 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F07 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f07_m4a_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F07_estimator_lines](../figs/route1_formula_permutation_estimator_report/f07_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F07_term_forest](../figs/route1_formula_permutation_estimator_report/f07_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7877. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1635, p=0.069. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0931, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0164, p=0.103. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0605, p=0.465. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7877. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1635, p=0.062. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0931, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0164, p=0.094. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0605, p=0.452. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1784. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.118. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0009, p=0.374. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7877. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1635, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0931, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0164, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0605, p=0.409. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1784. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0009, p=0.487. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7735. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1635, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0931, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0164, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0605, p=0.407. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7737. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2108, p=0.842. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0848, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0190, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0416, p=0.561. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 94.433797; The Hessian matrix at the estimated parameter values is not positive definite.

## F08. age + child effort + parent context effort with age x child effort, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7879; delta vs base F01 = 0.00099.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F08_estimator_lines](../figs/route1_formula_permutation_estimator_report/f08_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F08_term_forest](../figs/route1_formula_permutation_estimator_report/f08_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1655, p=0.071. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0873, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0177, p=0.078. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0594, p=0.554. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0103, p=0.089. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1655, p=0.063. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0873, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0177, p=0.070. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0594, p=0.542. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0103, p=0.080. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1787. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.124. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1124, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0007, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0008, p=0.664. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0004, p=0.026. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1655, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0873, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0177, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0594, p=0.417. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0103, p=0.121. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1787. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1124, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0007, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0008, p=0.561. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0004, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7738. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1668, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0885, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0175, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0522, p=0.470. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0102, p=0.124. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7739. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2056, p=0.845. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0803, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0202, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0404, p=0.572. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0095, p=0.158. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 91.645403; The Hessian matrix at the estimated parameter values is not positive definite.

## F09. age + child effort + parent context effort + question/form type

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort, question/form type?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type)`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7872; delta vs base F01 = 0.00028.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F09_estimator_lines](../figs/route1_formula_permutation_estimator_report/f09_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F09_term_forest](../figs/route1_formula_permutation_estimator_report/f09_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7872. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1651, p=0.052. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1001, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0787, p=0.317. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7872. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1651, p=0.045. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1001, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0787, p=0.303. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1859. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0029, p=0.159. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0005, p=0.626. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7872. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1651, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1001, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0787, p=0.284. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1859. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0029, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0005, p=0.692. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7729. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1674, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1027, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0705, p=0.330. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7730. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1840, p=0.862. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0997, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0621, p=0.386. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 94.046926; The Hessian matrix at the estimated parameter values is not positive definite.

## F10. age + child effort + parent context effort + question/form type with age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7873; delta vs base F01 = 0.00037.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F10_estimator_lines](../figs/route1_formula_permutation_estimator_report/f10_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F10_term_forest](../figs/route1_formula_permutation_estimator_report/f10_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1666, p=0.051. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0974, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0789, p=0.381. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0072, p=0.261. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1666, p=0.044. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0974, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0789, p=0.367. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0072, p=0.247. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1852. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.157. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1107, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0005, p=0.789. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0006, p=0.002. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1666, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0974, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0789, p=0.283. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0072, p=0.278. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1852. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1107, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0005, p=0.714. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0006, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7729. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1666, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0974, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0789, p=0.280. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0072, p=0.275. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7731. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1796, p=0.865. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0979, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0620, p=0.386. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0062, p=0.357. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F11. age + child effort + parent context effort + question/form type with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7879; delta vs base F01 = 0.00103.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F11_estimator_lines](../figs/route1_formula_permutation_estimator_report/f11_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F11_term_forest](../figs/route1_formula_permutation_estimator_report/f11_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=0.056. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0767, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0165, p=0.103. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0672, p=0.387. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=0.049. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0767, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0165, p=0.093. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0672, p=0.373. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1769. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.125. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0009, p=0.367. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7879. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0767, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0165, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0672, p=0.360. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1769. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0009, p=0.502. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7736. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1662, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0798, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0164, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0590, p=0.414. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7737. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2175, p=0.838. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0677, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0192, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0472, p=0.509. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F12. age + child effort + parent context effort + question/form type with age x child effort, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7881; delta vs base F01 = 0.00122.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F12_estimator_lines](../figs/route1_formula_permutation_estimator_report/f12_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F12_term_forest](../figs/route1_formula_permutation_estimator_report/f12_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7881. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1670, p=0.056. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0706, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=0.075. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0665, p=0.480. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0107, p=0.062. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7881. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1670, p=0.049. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0706, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=0.067. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0665, p=0.467. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0107, p=0.055. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1776. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.129. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1117, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0007, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0008, p=0.650. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0004, p=0.022. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7881. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1670, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0706, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0665, p=0.364. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0107, p=0.107. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1776. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1117, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0007, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0008, p=0.567. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0004, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7738. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1670, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0706, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0665, p=0.362. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0107, p=0.105. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,871 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7740. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2124, p=0.840. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0629, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0204, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0462, p=0.518. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0100, p=0.141. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 95.115506; The Hessian matrix at the estimated parameter values is not positive definite.

## F13. age + child effort + context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7862; delta vs base F01 = -0.00073.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F13_estimator_lines](../figs/route1_formula_permutation_estimator_report/f13_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F13_term_forest](../figs/route1_formula_permutation_estimator_report/f13_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1631, p=0.075. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0960, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0759, p=0.182. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1631, p=0.067. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0960, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0759, p=0.170. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1866. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.144. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0216, p=0.120. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1631, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0960, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0759, p=0.052. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1866. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0216, p=0.038. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1631, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0960, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0759, p=0.051. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1713, p=0.869. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0982, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9138, p=0.096. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F14. age + child effort + context entropy with age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7863; delta vs base F01 = -0.00060.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F14_estimator_lines](../figs/route1_formula_permutation_estimator_report/f14_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F14_term_forest](../figs/route1_formula_permutation_estimator_report/f14_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1669, p=0.078. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0896, p=0.195. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0691, p=0.416. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1669, p=0.070. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0896, p=0.182. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0691, p=0.403. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1857. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.128. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0218, p=0.178. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0031, p=0.012. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1669, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0896, p=0.049. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0691, p=0.179. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1857. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0218, p=0.036. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0031, p=0.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1669, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0966, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0896, p=0.048. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0691, p=0.177. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1689, p=0.870. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0997, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9296, p=0.091. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0771, p=0.135. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 85.478716; The Hessian matrix at the estimated parameter values is not positive definite.

## F15. age + child effort + context entropy with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7869; delta vs base F01 = 0.00000.

### Primary Row-Level Fixed-Effort Atlas

![F15 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4b_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M4b`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.136, range -0.151 to -0.122 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F15 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f15_m4b_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F15_estimator_lines](../figs/route1_formula_permutation_estimator_report/f15_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F15_term_forest](../figs/route1_formula_permutation_estimator_report/f15_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1650, p=0.077. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0727, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.107. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0446, p=0.195. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1650, p=0.069. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0727, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.097. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0446, p=0.182. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1802. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.127. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0230, p=0.082. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1650, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0727, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0446, p=0.058. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1802. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0230, p=0.025. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7725. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1650, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0727, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0446, p=0.057. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7726. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2041, p=0.844. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0680, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0191, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.8869, p=0.106. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 90.147102; The Hessian matrix at the estimated parameter values is not positive definite.

## F16. age + child effort + context entropy with age x child effort, age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00018.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F16_estimator_lines](../figs/route1_formula_permutation_estimator_report/f16_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F16_term_forest](../figs/route1_formula_permutation_estimator_report/f16_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1694, p=0.080. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0728, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.103. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0594, p=0.212. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0791, p=0.359. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1694, p=0.071. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0728, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.093. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0594, p=0.199. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0791, p=0.345. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1798. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.116. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0237, p=0.112. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0025, p=0.040. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1694, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0728, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0594, p=0.055. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0791, p=0.124. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1798. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0237, p=0.021. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0025, p=0.010. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7726. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1711, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0742, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0171, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0088, p=0.067. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0769, p=0.134. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2021, p=0.845. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0690, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0194, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9037, p=0.099. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0846, p=0.101. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 89.524350; The Hessian matrix at the estimated parameter values is not positive definite.

## F17. age + child effort + context entropy + question/form type

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, question/form type?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type)`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7864; delta vs base F01 = -0.00052.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F17_estimator_lines](../figs/route1_formula_permutation_estimator_report/f17_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F17_term_forest](../figs/route1_formula_permutation_estimator_report/f17_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=0.062. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0799, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1344, p=0.169. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=0.054. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0799, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1344, p=0.156. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1854. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.154. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0216, p=0.126. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0799, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1344, p=0.041. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1854. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0216, p=0.038. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0799, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1344, p=0.040. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7720. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1778, p=0.864. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0818, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9747, p=0.077. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F18. age + child effort + context entropy + question/form type with age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7865; delta vs base F01 = -0.00039.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F18_estimator_lines](../figs/route1_formula_permutation_estimator_report/f18_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F18_term_forest](../figs/route1_formula_permutation_estimator_report/f18_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1682, p=0.064. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0810, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1479, p=0.189. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.427. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1682, p=0.056. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0810, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1479, p=0.176. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.413. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1845. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.136. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0217, p=0.188. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0030, p=0.017. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1682, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0810, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1479, p=0.038. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.189. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1845. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0217, p=0.037. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0030, p=0.002. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1682, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0810, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1479, p=0.037. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.187. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7720. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1755, p=0.865. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0838, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9901, p=0.072. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0757, p=0.143. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 87.874836; The Hessian matrix at the estimated parameter values is not positive definite.

## F19. age + child effort + context entropy + question/form type with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00022.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F19_estimator_lines](../figs/route1_formula_permutation_estimator_report/f19_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F19_term_forest](../figs/route1_formula_permutation_estimator_report/f19_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1662, p=0.065. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0567, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.106. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1036, p=0.181. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1662, p=0.057. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0567, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.096. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1036, p=0.168. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1791. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.132. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0229, p=0.089. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1662, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0567, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1036, p=0.046. In this estimator, that is higher expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1791. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0229, p=0.026. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7726. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1662, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0567, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1036, p=0.045. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2111, p=0.839. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0513, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0192, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9494, p=0.084. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 93.074910; The Hessian matrix at the estimated parameter values is not positive definite.

## F20. age + child effort + context entropy + question/form type with age x child effort, age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7873; delta vs base F01 = 0.00040.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F20_estimator_lines](../figs/route1_formula_permutation_estimator_report/f20_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F20_term_forest](../figs/route1_formula_permutation_estimator_report/f20_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=0.066. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.102. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1182, p=0.207. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0776, p=0.368. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=0.059. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.092. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1182, p=0.194. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0776, p=0.354. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1787. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.120. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0235, p=0.122. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0024, p=0.051. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1182, p=0.043. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0776, p=0.131. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1787. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0235, p=0.022. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0024, p=0.012. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1722, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0608, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0172, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0683, p=0.053. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0757, p=0.140. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7728. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2091, p=0.840. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0529, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0196, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9660, p=0.079. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0831, p=0.107. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F21. age + child effort + context entropy + parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7862; delta vs base F01 = -0.00073.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F21_estimator_lines](../figs/route1_formula_permutation_estimator_report/f21_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F21_term_forest](../figs/route1_formula_permutation_estimator_report/f21_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=0.080. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0969, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0799, p=0.181. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0172, p=0.863. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=0.072. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0969, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0799, p=0.169. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0172, p=0.859. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1878. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.156. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0215, p=0.124. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0005, p=0.604. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0969, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0799, p=0.051. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0172, p=0.820. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1878. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0215, p=0.039. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0005, p=0.709. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1644, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0969, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0799, p=0.050. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0172, p=0.819. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1715, p=0.869. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0983, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9140, p=0.096. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0024, p=0.974. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 86.457956; The Hessian matrix at the estimated parameter values is not positive definite.

## F22. age + child effort + context entropy + parent context effort with age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7862; delta vs base F01 = -0.00073.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F22_estimator_lines](../figs/route1_formula_permutation_estimator_report/f22_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F22_term_forest](../figs/route1_formula_permutation_estimator_report/f22_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=0.080. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0963, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0747, p=0.188. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0175, p=0.865. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0015, p=0.869. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=0.072. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0963, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0747, p=0.175. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0175, p=0.861. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0015, p=0.865. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.149. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1114, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0199, p=0.161. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0004, p=0.827. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=0.026. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7862. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0963, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0747, p=0.052. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0175, p=0.816. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0015, p=0.836. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1114, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0199, p=0.056. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0004, p=0.754. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1648, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0963, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0747, p=0.051. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0175, p=0.815. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0015, p=0.835. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1714, p=0.869. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0983, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9135, p=0.097. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0024, p=0.974. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0001, p=0.989. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 86.637370; The Hessian matrix at the estimated parameter values is not positive definite.

## F23. age + child effort + context entropy + parent context effort with age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7863; delta vs base F01 = -0.00059.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F23_estimator_lines](../figs/route1_formula_permutation_estimator_report/f23_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F23_term_forest](../figs/route1_formula_permutation_estimator_report/f23_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1685, p=0.083. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0978, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0947, p=0.192. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0215, p=0.831. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0697, p=0.413. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1685, p=0.074. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0978, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0947, p=0.179. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0215, p=0.827. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0697, p=0.400. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1866. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.139. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0217, p=0.180. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0004, p=0.719. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0031, p=0.013. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1685, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0978, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0947, p=0.048. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0215, p=0.776. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0697, p=0.175. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1866. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1116, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0217, p=0.037. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0004, p=0.785. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0031, p=0.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1685, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0978, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0947, p=0.047. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0215, p=0.775. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0697, p=0.173. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1694, p=0.870. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1001, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9309, p=0.090. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0071, p=0.923. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0773, p=0.135. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F24. age + child effort + context entropy + parent context effort with age x context entropy, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7863; delta vs base F01 = -0.00059.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F24_estimator_lines](../figs/route1_formula_permutation_estimator_report/f24_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F24_term_forest](../figs/route1_formula_permutation_estimator_report/f24_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=0.083. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0977, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0935, p=0.201. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0216, p=0.833. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0694, p=0.426. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.972. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=0.074. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0977, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0935, p=0.188. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0216, p=0.828. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0694, p=0.413. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.971. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1855. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0034, p=0.135. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1114, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0201, p=0.217. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0003, p=0.875. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0026, p=0.026. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=0.037. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0977, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0935, p=0.048. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0216, p=0.775. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0694, p=0.180. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.964. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1855. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0034, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1114, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0201, p=0.053. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0003, p=0.823. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0026, p=0.007. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0977, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0935, p=0.047. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0216, p=0.774. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0694, p=0.178. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.964. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1701, p=0.870. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.1005, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9345, p=0.090. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0070, p=0.925. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0781, p=0.133. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient 0.0011, p=0.884. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F25. age + child effort + context entropy + parent context effort with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7869; delta vs base F01 = 0.00000.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F25_estimator_lines](../figs/route1_formula_permutation_estimator_report/f25_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F25_term_forest](../figs/route1_formula_permutation_estimator_report/f25_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1653, p=0.083. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0729, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.109. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0453, p=0.195. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0027, p=0.977. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1653, p=0.074. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0729, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.099. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0453, p=0.182. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0027, p=0.977. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1803. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.136. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0230, p=0.083. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0001, p=0.947. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1653, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0729, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0168, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0453, p=0.058. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0027, p=0.971. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1803. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0230, p=0.025. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0001, p=0.958. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7725. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1664, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0739, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0167, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9932, p=0.071. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0041, p=0.956. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7726. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2031, p=0.845. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0668, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0191, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.8830, p=0.108. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0157, p=0.831. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F26. age + child effort + context entropy + parent context effort with age x child effort, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7869; delta vs base F01 = 0.00004.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F26_estimator_lines](../figs/route1_formula_permutation_estimator_report/f26_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F26_term_forest](../figs/route1_formula_permutation_estimator_report/f26_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1665, p=0.084. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0699, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0175, p=0.094. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0261, p=0.207. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0034, p=0.974. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0051, p=0.554. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1665, p=0.075. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0699, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0175, p=0.085. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0261, p=0.194. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0034, p=0.974. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0051, p=0.543. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1803. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.137. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1124, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0218, p=0.106. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0001, p=0.955. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.141. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7869. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1665, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0699, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0175, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0261, p=0.064. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0034, p=0.964. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0051, p=0.478. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1803. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1124, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0218, p=0.034. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0001, p=0.940. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.008. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7725. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1665, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0699, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0175, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0261, p=0.062. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0034, p=0.964. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0051, p=0.476. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2011, p=0.846. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0649, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0196, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.8694, p=0.114. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0154, p=0.834. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0038, p=0.603. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 88.972480; The Hessian matrix at the estimated parameter values is not positive definite.

## F27. age + child effort + context entropy + parent context effort with age x child effort, age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00018.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F27_estimator_lines](../figs/route1_formula_permutation_estimator_report/f27_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F27_term_forest](../figs/route1_formula_permutation_estimator_report/f27_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1700, p=0.085. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0732, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0173, p=0.105. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0612, p=0.210. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0072, p=0.941. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0793, p=0.359. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1700, p=0.076. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0732, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0173, p=0.095. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0612, p=0.197. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0072, p=0.940. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0793, p=0.345. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1797. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.125. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0237, p=0.110. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.970. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0025, p=0.042. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1700, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0732, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0173, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0612, p=0.055. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0072, p=0.924. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0793, p=0.123. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1797. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1126, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0237, p=0.021. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.975. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0025, p=0.010. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7725. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1700, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0732, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0173, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0612, p=0.054. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0072, p=0.923. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0793, p=0.121. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2014, p=0.846. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0682, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0195, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9009, p=0.101. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0109, p=0.882. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0843, p=0.102. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 89.446076; The Hessian matrix at the estimated parameter values is not positive definite.

## F28. age + child effort + context entropy + parent context effort with age x child effort, age x context entropy, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00020.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F28_estimator_lines](../figs/route1_formula_permutation_estimator_report/f28_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F28_term_forest](../figs/route1_formula_permutation_estimator_report/f28_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1708, p=0.086. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0709, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0178, p=0.091. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0458, p=0.225. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0076, p=0.943. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0762, p=0.384. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0039, p=0.655. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1708, p=0.077. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0709, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0178, p=0.082. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0458, p=0.212. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0076, p=0.941. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0762, p=0.370. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0039, p=0.645. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1797. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.126. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1124, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0224, p=0.139. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.995. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0022, p=0.058. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.173. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1708, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0709, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0178, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0458, p=0.059. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0076, p=0.920. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0762, p=0.141. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0039, p=0.589. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1797. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1124, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0224, p=0.029. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.993. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0022, p=0.022. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.018. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7726. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1718, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0720, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0176, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9940, p=0.071. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0007, p=0.993. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0739, p=0.153. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0038, p=0.595. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7728. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2001, p=0.846. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0669, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0198, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.8911, p=0.105. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0107, p=0.884. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0824, p=0.112. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0026, p=0.722. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 88.897115; The Hessian matrix at the estimated parameter values is not positive definite.

## F29. age + child effort + context entropy + parent context effort + question/form type

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type)`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7864; delta vs base F01 = -0.00051.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F29_estimator_lines](../figs/route1_formula_permutation_estimator_report/f29_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F29_term_forest](../figs/route1_formula_permutation_estimator_report/f29_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1663, p=0.064. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0811, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1411, p=0.166. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0257, p=0.782. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1663, p=0.056. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0811, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1411, p=0.154. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0257, p=0.775. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.165. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1108, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0215, p=0.130. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0004, p=0.676. In this estimator, that is higher expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1663, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0811, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1411, p=0.040. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0257, p=0.734. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1863. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1108, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0215, p=0.040. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0004, p=0.765. In this estimator, that is higher expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1663, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0811, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1411, p=0.039. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0257, p=0.732. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7720. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1785, p=0.864. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0823, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9765, p=0.076. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0090, p=0.903. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 89.440161; The Hessian matrix at the estimated parameter values is not positive definite.

## F30. age + child effort + context entropy + parent context effort + question/form type with age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7864; delta vs base F01 = -0.00050.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F30_estimator_lines](../figs/route1_formula_permutation_estimator_report/f30_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F30_term_forest](../figs/route1_formula_permutation_estimator_report/f30_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1668, p=0.063. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0802, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1346, p=0.172. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0262, p=0.787. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0021, p=0.811. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1668, p=0.055. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0802, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1346, p=0.160. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0262, p=0.781. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0021, p=0.806. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1854. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.156. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1107, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0200, p=0.165. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0003, p=0.869. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=0.022. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7864. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1668, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0802, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1346, p=0.041. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0262, p=0.728. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0021, p=0.772. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1854. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1107, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0200, p=0.055. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0003, p=0.819. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7718. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1668, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0802, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1346, p=0.040. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0262, p=0.727. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0021, p=0.770. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7720. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1780, p=0.864. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0821, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9743, p=0.077. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0091, p=0.901. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0006, p=0.930. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F31. age + child effort + context entropy + parent context effort + question/form type with age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7865; delta vs base F01 = -0.00037.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F31_estimator_lines](../figs/route1_formula_permutation_estimator_report/f31_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F31_term_forest](../figs/route1_formula_permutation_estimator_report/f31_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1705, p=0.066. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0824, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1559, p=0.185. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0298, p=0.751. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0683, p=0.422. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1705, p=0.058. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0824, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1559, p=0.172. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0298, p=0.743. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0683, p=0.408. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1851. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.146. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0216, p=0.189. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0003, p=0.787. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0030, p=0.017. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1705, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0824, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1559, p=0.037. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0298, p=0.693. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0683, p=0.184. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1851. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1109, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0216, p=0.039. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0003, p=0.839. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0030, p=0.002. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1705, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0824, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1559, p=0.036. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0298, p=0.692. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0683, p=0.182. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7720. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1764, p=0.865. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0846, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9931, p=0.072. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0135, p=0.855. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0760, p=0.141. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 88.879924; The Hessian matrix at the estimated parameter values is not positive definite.

## F32. age + child effort + context entropy + parent context effort + question/form type with age x context entropy, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7865; delta vs base F01 = -0.00037.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F32_estimator_lines](../figs/route1_formula_permutation_estimator_report/f32_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F32_term_forest](../figs/route1_formula_permutation_estimator_report/f32_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=0.065. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0820, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1527, p=0.193. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0300, p=0.755. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.440. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0009, p=0.917. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=0.057. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0820, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1527, p=0.180. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0300, p=0.748. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.427. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0009, p=0.914. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1845. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0034, p=0.142. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1107, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0202, p=0.222. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0002, p=0.916. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0025, p=0.035. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=0.030. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7865. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0820, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1527, p=0.038. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0300, p=0.691. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.193. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0009, p=0.895. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1845. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0034, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1107, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0202, p=0.053. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0002, p=0.885. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0025, p=0.009. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0005, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7719. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1707, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0820, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1527, p=0.037. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0300, p=0.690. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0675, p=0.191. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0009, p=0.894. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7720. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1767, p=0.865. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0848, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9946, p=0.071. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0133, p=0.856. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0764, p=0.142. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient 0.0005, p=0.945. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 89.235888; The Hessian matrix at the estimated parameter values is not positive definite.

## F33. age + child effort + context entropy + parent context effort + question/form type with age x child effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7871; delta vs base F01 = 0.00022.

### Primary Row-Level Fixed-Effort Atlas

![F33 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m5_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M5`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.133, range -0.149 to -0.118 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F33 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f33_m5_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F33_estimator_lines](../figs/route1_formula_permutation_estimator_report/f33_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F33_term_forest](../figs/route1_formula_permutation_estimator_report/f33_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1671, p=0.067. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.109. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1067, p=0.179. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0113, p=0.901. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1671, p=0.059. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.099. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1067, p=0.167. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0113, p=0.898. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1790. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=0.141. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0229, p=0.089. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.973. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7871. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1671, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1067, p=0.046. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0113, p=0.881. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1790. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0030, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0229, p=0.026. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.979. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7725. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1671, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0573, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0169, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1067, p=0.045. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0113, p=0.881. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2105, p=0.840. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0507, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0193, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9468, p=0.085. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0089, p=0.903. In this estimator, that is higher expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 93.130080; The Hessian matrix at the estimated parameter values is not positive definite.

## F34. age + child effort + context entropy + parent context effort + question/form type with age x child effort, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7872; delta vs base F01 = 0.00027.

### Primary Row-Level Fixed-Effort Atlas

![F34 exact row-level Atlas fixed-effort lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m11_nb_words_fixed_effort_atlas.png)

**Fixed-size read.** This is the direct same-effort plot for the exact existing Atlas model `M11`. Each line fixes child effort to a word-count value and follows predicted `sum_bits` over age.

**Slope read.** Across fixed word-count values, the row-level fixed-effort slopes are downward: mean -0.128, range -0.139 to -0.117 bits/month.

### Global Fixed-Effort Summary Across Fixed Sizes

![F34 global fixed-effort summary](../figs/route1_formula_permutation_estimator_report/f34_m11_row_level_global_fixed_effort_summary.png)

**Global same-effort read.** The black line averages the row-level fixed-word-count prediction lines, unweighted across fixed word counts. This is the compact answer to whether conditional `sum_bits` goes up or down over age when effort is held fixed.

![F34_estimator_lines](../figs/route1_formula_permutation_estimator_report/f34_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F34_term_forest](../figs/route1_formula_permutation_estimator_report/f34_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7872. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=0.067. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0537, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0176, p=0.091. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0870, p=0.191. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0122, p=0.903. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0057, p=0.480. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7872. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=0.059. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0537, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0176, p=0.082. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0870, p=0.178. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0122, p=0.900. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0057, p=0.467. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1792. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=0.140. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1117, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0218, p=0.111. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.993. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.127. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7872. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0537, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0176, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0870, p=0.050. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0122, p=0.871. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0057, p=0.425. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1792. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0031, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1117, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0218, p=0.034. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0000, p=0.990. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.009. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7726. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1686, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0537, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0176, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0870, p=0.049. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0122, p=0.871. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0057, p=0.423. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular; The random effects covariance matrix is singular.; The MLE may be on the boundary of the parameter space.; The random effects covariance matrix is singular.

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7728. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2084, p=0.841. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0483, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0197, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9324, p=0.090. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0084, p=0.909. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0044, p=0.547. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F35. age + child effort + context entropy + parent context effort + question/form type with age x child effort, age x context entropy

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7873; delta vs base F01 = 0.00040.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F35_estimator_lines](../figs/route1_formula_permutation_estimator_report/f35_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F35_term_forest](../figs/route1_formula_permutation_estimator_report/f35_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1718, p=0.069. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0581, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.105. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1225, p=0.204. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0156, p=0.865. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0780, p=0.366. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1718, p=0.061. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0581, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.095. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1225, p=0.190. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0156, p=0.861. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0780, p=0.351. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1784. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=0.129. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0236, p=0.119. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0001, p=0.894. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0024, p=0.053. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1718, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0581, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0174, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1225, p=0.043. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0156, p=0.837. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0780, p=0.130. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1784. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0032, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1119, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0236, p=0.022. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0001, p=0.916. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0024, p=0.012. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7727. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1728, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0613, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0172, p=0.002. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0705, p=0.052. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0077, p=0.917. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0759, p=0.140. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7728. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2088, p=0.841. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0526, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0196, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9645, p=0.079. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0044, p=0.953. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0830, p=0.108. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** The Hessian matrix at the estimated parameter values is not positive definite.

## F36. age + child effort + context entropy + parent context effort + question/form type with age x child effort, age x context entropy, age x parent context effort

**Natural-language test.** Does child age predict total utterance information at fixed child effort after controlling child identity and context entropy, parent context effort, question/form type; and do the listed age interactions change that relation?

**Child-fixed-effect formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Random-effect / population formula.**

`sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit read.** OLS child-fixed-effect R2 = 0.7873; delta vs base F01 = 0.00043.

### Primary Row-Level Fixed-Effort Atlas

_No exact row-level Atlas plot exists yet for this exact formula permutation. Use this section as an aggregate estimator screen only until this formula is refit row-level._

![F36_estimator_lines](../figs/route1_formula_permutation_estimator_report/f36_aggregate_estimator_screen_age_lines.png)

**Aggregate estimator-screen read. Each line is the child-session/effort-band aggregate prediction from a different estimator family at median effort/context. This is not the primary same-effort Atlas result.**

![F36_term_forest](../figs/route1_formula_permutation_estimator_report/f36_term_effect_forest.png)

**Predictor-relation read. This forest shows age, effort, context, and interaction terms across estimators.**

### OLS + child fixed effects + clustered SE

**Why this estimator is here.** C(child_id), covariance clustered by child. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1728, p=0.068. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0552, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=0.089. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1061, p=0.217. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0161, p=0.871. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0743, p=0.397. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0045, p=0.582. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gaussian, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1728, p=0.060. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0552, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=0.080. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1061, p=0.203. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0161, p=0.867. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0743, p=0.383. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0045, p=0.571. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GEE Gamma/log, clustered by child

**Why this estimator is here.** population-average GEE grouped by child; C(child_id) also included in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1787. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=0.129. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1117, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0224, p=0.146. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0001, p=0.943. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0021, p=0.073. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.156. In this estimator, that is lower expected sum_bits on the log-mean scale.

### GLM Gaussian

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7873. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1728, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0552, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0179, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.1061, p=0.046. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0161, p=0.831. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0743, p=0.152. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0045, p=0.527. In this estimator, that is lower expected sum_bits on the additive-bit scale.

### GLM Gamma/log

**Why this estimator is here.** child fixed effects in the mean model. Outcome scale: log mean bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c + C(child_id)`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.1787. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.0033, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 0.1117, p=<.001. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient -0.0008, p=<.001. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.0224, p=0.030. In this estimator, that is higher expected sum_bits on the log-mean scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0001, p=0.928. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0021, p=0.027. In this estimator, that is lower expected sum_bits on the log-mean scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0003, p=0.019. In this estimator, that is lower expected sum_bits on the log-mean scale.

### MixedLM random child intercept

**Why this estimator is here.** random child intercept. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7728. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.1737, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0585, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0177, p=0.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 1.0545, p=0.056. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient -0.0085, p=0.909. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0723, p=0.162. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0045, p=0.531. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Random effects covariance is singular

### MixedLM random child age slope

**Why this estimator is here.** random child intercept and age slope. Outcome scale: additive bits.

**Formula used.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(question_type) + age_c:effort_c + age_c:context_entropy_c + age_c:parent_context_effort_c`

**Aggregate screen fit.** 2,838 child-session/effort-band rows, 21 children; observed-vs-fitted R2 = 0.7729. This subsection is estimator sensitivity, not the primary row-level fixed-effort answer.

**Predictor read for the aggregate sensitivity screen.**

- **Age at session.** `age_c` estimates older session age; coefficient 0.2073, p=0.842. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Child utterance effort.** `effort_c` estimates more child production effort; coefficient 5.0508, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x child effort.** `age_c:effort_c` estimates the child-effort slope changing with age; coefficient 0.0199, p=<.001. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Context entropy.** `context_entropy_c` estimates a less predictable prior context; coefficient 0.9534, p=0.083. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Parent context effort.** `parent_context_effort_c` estimates more parent/caretaker effort in the prior context; coefficient 0.0041, p=0.955. In this estimator, that is higher expected sum_bits on the additive-bit scale.
- **Age x context entropy.** `age_c:context_entropy_c` estimates the context-entropy relation changing with age; coefficient -0.0806, p=0.120. In this estimator, that is lower expected sum_bits on the additive-bit scale.
- **Age x parent context effort.** `age_c:parent_context_effort_c` estimates the parent-context-effort relation changing with age; coefficient -0.0032, p=0.660. In this estimator, that is lower expected sum_bits on the additive-bit scale.

**Caution.** Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 91.753826; The Hessian matrix at the estimated parameter values is not positive definite.

## Complete Formula Grid Location

The full 36-formula by 7-estimator grid is also saved here for sorting/filtering outside the prose report:

```text
results/route1_formula_permutation_estimator_report/formula_estimator_summary.csv
results/route1_formula_permutation_estimator_report/formula_key_term_relation_summary.csv
results/route1_formula_permutation_estimator_report/formula_fixed_effort_predictions.csv
results/route1_formula_permutation_estimator_report/formula_fitted_values.csv.gz
results/route1_formula_permutation_estimator_report/formula_ols_fe_nested_r2.csv
results/route1_formula_permutation_estimator_report/row_level_global_fixed_effort_summaries.csv
figs/route1_formula_permutation_estimator_report
```

## Heldout Children

The heldout prediction artifacts are row-level PBM-trained population/Mundlak models for Forrester/Ella, Sachs/Naomi, and MPI-EVA-Manchester/Helen. These models cannot use `C(child_id)` for unseen children, so they use population or Mundlak-compatible analogues of the Route 1 formulas.

**Best available heldout-compatible k3/word candidates by mean RMSE.**

- `POP_M4C` (Population age x effort + question type): mean RMSE 13.525, mean MAE 9.709, same-slope share 1.00.
- `POP_M1` (Population age + effort): mean RMSE 13.585, mean MAE 9.784, same-slope share 1.00.
- `POP_M4A` (Population age x effort + parent-context effort): mean RMSE 13.603, mean MAE 9.794, same-slope share 1.00.
- `POP_M8` (Population nonlinear age x effort): mean RMSE 13.604, mean MAE 9.851, same-slope share 1.00.
- `POP_M3` (Population age x effort): mean RMSE 13.605, mean MAE 9.789, same-slope share 1.00.

![actual_vs_predicted_k3_POP_M4C_nb_words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M4C_nb_words.png)

![actual_vs_predicted_k3_POP_M4A_nb_words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M4A_nb_words.png)

![actual_vs_predicted_k3_POP_M3_nb_words](../figs/route1_heldout_real_child_prediction/actual_vs_predicted_k3_POP_M3_nb_words.png)

![heldout_pop_m4c_actual_vs_predicted_regression_lines](../figs/supervisor_candidate_report/heldout_pop_m4c_actual_vs_predicted_regression_lines.png)

**Heldout read.** The heldout panels compare actual unseen-child age trajectories with PBM-trained predicted trajectories. This is the right prediction check; it is separate from the child-fixed-effect models because an unseen child cannot have a fitted child dummy.

## Baseline And Caretaker Contrast Pointers

![Row-level real child M3](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png)

![Row-level real child M5](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m5_nb_words_fixed_effort_atlas.png)

![Caretaker CM2](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_words_fixed_effort_atlas.png)

![Caretaker CM6](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_words_fixed_effort_atlas.png)
