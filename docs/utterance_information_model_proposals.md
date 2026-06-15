# Utterance-Level Information: Model Proposal Review

Working modeling packet, generated 2026-06-04.

This is a separate review document. It is not the supervisor-facing report. The
goal is to compare candidate model forms before deciding what belongs in the
main document.

## Modeling Principles Used

The model set follows the Advanced Data Analytics course guidance:

- start from the response variable and data-generating structure;
- audit predictor correlations and multicollinearity before interpreting
  regression coefficients;
- begin with a simple baseline model;
- respect repeated observations within children using clustered standard
  errors, mixed models, or GEE;
- treat flexible or more complex models as additions only when they answer a
  real scientific question.

## Current Data Extract

| table | rows | children |
| --- | --- | --- |
| real_rows_all_contexts | 1787940 | 21 |
| baseline_k3_rows | 2233017 | 21 |
| real_sample | 93600 | 21 |
| baseline_sample | 62400 | 21 |
| caretaker_k3_rows | 668903 | 21 |
| caretaker_sample | 12480 | 21 |
| context_entropy_sample | 57556 | 21 |

The working rows come from the scored PBM utterance-information long table.
Preliminary fits use
deterministic stratified samples so that model forms can be checked quickly
without treating a 6GB CSV as the day-to-day modeling object. Final analysis
tables should be materialized as compact Parquet/DuckDB tables or smaller CSVs.

## Unit Labels

`dataset` means the source corpus or collection: Brown, Manchester, or
Providence. It is not a child identifier. `child_id` is the individual child.
The primary proposal below does **not** center dataset/corpus fixed effects,
because the first scientific question is developmental and child-level rather
than corpus-comparison. Dataset/corpus can still be added later as a robustness
check if the timeline differences across Brown, Manchester, and Providence look
like they are driving an apparent developmental trend.

## Source-File Sanity Check

The scored long table is checked against the symlinked scored CSV tree before
the plots and models are interpreted. Source comparison status:
**matched**.

| check | value | status |
| --- | --- | --- |
| scored_csv_files | 504 | ok |
| source_scored_rows | 11607680 | ok |
| source_raw_rows | 11615312 | ok |
| source_unscored_or_blank_rows | 7632 | documented |
| long_table_rows | 11607680 | ok |
| source_vs_long_mismatched_groups | 0 | ok |
| context_entropy_feature_rows | 1675520 | ok |

The source tree contains a small set of raw placeholder rows that have no
generated target and no finite surprisal. These are documented above as
`source_unscored_or_blank_rows`; they are not analysis rows and are not counted
as mismatches.

Context entropy source files:

| file | exists | rows |
| --- | --- | --- |
| results/external/compute_surprisal_mila/context_entropy_mistral/context_entropy_manifest.csv.gz | True | 1675520 |
| results/external/compute_surprisal_mila/context_entropy_mistral/context_entropy_features.csv.gz | True | 1675520 |

Context entropy join status for real child rows:

| role | target_variant | context_k | context_entropy_join_status | rows |
| --- | --- | --- | --- | --- |
| child | real | k1 | empty_context | 2660 |
| child | real | k1 | matched | 442220 |
| child | real | k1 | missing_entropy | 2105 |
| child | real | k2 | empty_context | 2660 |
| child | real | k2 | matched | 440538 |
| child | real | k2 | matched_text_fallback | 923 |
| child | real | k2 | missing_entropy | 2864 |
| child | real | k3 | empty_context | 2660 |
| child | real | k3 | matched | 439259 |
| child | real | k3 | matched_text_fallback | 2154 |
| child | real | k3 | missing_entropy | 2912 |

Source/long-table mismatches, if any:

_No rows._

## Predictor Correlation and Multicollinearity

![Predictor correlation heatmap](../figs/utterance_information_model_proposals/predictor_correlation_heatmap.png)

Main VIF warning: **nb_syllables_cmu_or_pkg, nb_morphemes, nb_syllables_pkg, nb_words, nb_phonemes**.

| predictor | r_squared_from_other_predictors | vif |
| --- | --- | --- |
| nb_syllables_cmu_or_pkg | 0.972 | 35.382 |
| nb_morphemes | 0.961 | 25.752 |
| nb_syllables_pkg | 0.960 | 25.028 |
| nb_words | 0.960 | 24.771 |
| nb_phonemes | 0.958 | 23.952 |
| n_eval_tokens | 0.883 | 8.564 |
| age_months | 0.086 | 1.094 |
| context_entropy_bits | 0.005 | 1.005 |

The effort predictors are intentionally redundant: words, morphemes,
syllables, phonemes, and tokenizer tokens all measure related aspects of
utterance size. The safest strategy is not to put all effort measures into a
single inferential model. Instead, use one primary effort scale, then run
parallel sensitivity models with alternative denominators.

The sensitivity analyses below therefore ask the same utterance-level question
several times, swapping the effort control one at a time: words, surface
morphemes, two syllable estimates, and phonemes.

Frequency predictors are not yet present in the current utterance-information table. The
recommended next addition is a target-level or utterance-level frequency
summary from the same additive age-bin vocabulary used by the baselines, such
as mean log word frequency or mean negative log frequency.

## Descriptive Plots

These plots are descriptive summaries, not final inferential controls. In
particular, the mean total-bits plot does **not** control for utterance size:
it shows how much information is in the whole utterance as utterances actually
occur. Because children produce longer utterances as they age, this plot can
mix developmental change in information with developmental change in
utterance length. The controlled/model-based plots below fix or adjust for
length using `nb_words` or `log_nb_words`.

![Real child bits per word by age and context](../figs/utterance_information_model_proposals/real_child_bits_per_word_by_age_context.png)

![Real child total bits by age and context](../figs/utterance_information_model_proposals/real_child_sum_bits_by_age_context.png)

![Real versus generated baselines](../figs/utterance_information_model_proposals/baseline_bits_per_word_by_age.png)

![Context entropy and target information](../figs/utterance_information_model_proposals/context_entropy_vs_bits_per_word.png)

## Five Candidate Models

### Model 1: Simple OLS Baseline

Formula:

```text
sum_bits ~ age_scaled + nb_words
```

Use: first sanity check for total information while controlling the most direct
length measure. Standard errors are clustered by child. This model does not
include context; it uses the no-context `k0` scoring condition as a baseline.

![M1 adjusted total bits](../figs/utterance_information_model_proposals/model1_adjusted_total_bits_by_age.png)

### Model 2: Effort-Controlled OLS

Formula:

```text
bits_per_word ~ age_scaled + age_scaled_sq + log_nb_words
```

Use: interpretable developmental curve for information per word with a minimal
residual word-length control. This fixes the scoring context to `k3`, so
context window is held constant by design.

![M2 adjusted bits per word](../figs/utterance_information_model_proposals/model2_adjusted_bits_per_word.png)

### Model 3: Linear Mixed Model With Child Random Intercepts

Formula:

```text
bits_per_word ~ age_scaled + log_nb_words
random: 1 | child_id
```

Use: same fixed effects as Model 2, but child baselines are allowed to differ.
This addresses repeated utterances within the same child.

![M3 child random intercepts](../figs/utterance_information_model_proposals/model3_child_random_intercepts.png)

If statsmodels reports a singular random-effect covariance for this model, that
does not mean child differences should be ignored. It means this random-effect
parameterization is unstable for the current pilot specification. The
child-control ladder below therefore includes child fixed effects and GEE
grouping by child as stable alternatives.

### Model 4: Linear Mixed Model With Child-Specific Age Slopes

Formula:

```text
bits_per_word ~ age_scaled + log_nb_words
random: 1 + age_scaled | child_id
```

Use: tests whether developmental trajectories differ across children, not just
their overall levels. The current pilot fit did not converge, so this plot is a
diagnostic proposal rather than an interpretable result.

![M4 random slope pilot](../figs/utterance_information_model_proposals/model4_random_slope_pilot.png)

### Model 5: Correlated-Data GLM/GEE Baseline Comparison

Formula:

```text
sum_bits ~ age_scaled * C(target_variant) + nb_words
family: Gamma(log), child-level exchangeable correlation
```

Use: compares real child utterances against random, unigram, bigram, and
trigram baselines while respecting child-level clustering. This is a
population-averaged GLM/GEE version of the GLMM question; if supervisors want
subject-specific random effects for this positive outcome, the final version
can be fit as a Gamma GLMM in R/glmmTMB.

![M5 adjusted baseline predictions](../figs/utterance_information_model_proposals/model5_adjusted_baseline_predictions.png)

## Context Extension

The context-only entropy feature is available for most child-context rows and
is measured in bits. The remaining missing context rows are isolated for patch
scoring; until that patch is merged, context-entropy models should use matched
or text-fallback matched rows only. A
natural extension is:

```text
bits_per_word ~ age_scaled + log_nb_words + context_entropy_bits + C(context_k)
cluster: child_id
```

This asks whether more uncertain contexts elicit child utterances with
different information density.

![Candidate fitted developmental curves](../figs/utterance_information_model_proposals/candidate_model_fitted_age_curves.png)

## Preliminary Fit Status

| model | status | n_obs | n_children | r_squared | aic | bic | formula | log_likelihood | random_effects | sample_note | qic | family | cov_struct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 OLS total bits | fit | 23400 | 21 | 0.745 | 167056.951 | 167081.133 | sum_bits ~ age_scaled + nb_words |  |  |  |  |  |  |
| M2 OLS efficiency controls | fit | 23400 | 21 | 0.251 | 140569.331 | 140601.573 | bits_per_word ~ age_scaled + age_scaled_sq + log_nb_words |  |  |  |  |  |  |
| M3 LMM child random intercept | fit_converged | 23400 | 21 |  | -inf | -inf | bits_per_word ~ age_scaled + log_nb_words | inf | 1 |  |  |  |  |
| M4 LMM child random intercept + age slope | fit_not_converged | 9360 | 21 |  | 56210.441 | 56260.451 | bits_per_word ~ age_scaled + log_nb_words | -28098.221 | 1 + age_scaled | balanced 120 rows per child-age-bin where available |  |  |  |
| M5 Gamma GEE baseline comparison | fit | 62400 | 21 |  |  |  | sum_bits ~ age_scaled * C(target_variant) + nb_words |  |  |  | 298154217102.593 | Gamma | Exchangeable |
| Context extension Gaussian GEE | fit | 57556 | 21 |  |  |  | bits_per_word ~ age_scaled + log_nb_words + context_entropy_bits + C(context_k) |  |  |  | 57174.635 | Gaussian | Exchangeable |

## Selected Coefficients

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| M1 OLS total bits | Intercept | 21.288 | 0.283 | 0.000 |
| M1 OLS total bits | age_scaled | -0.478 | 0.102 | 0.000 |
| M1 OLS total bits | nb_words | 7.079 | 0.090 | 0.000 |
| M2 OLS efficiency controls | Intercept | 14.645 | 0.248 | 0.000 |
| M2 OLS efficiency controls | age_scaled | -0.373 | 0.148 | 0.012 |
| M2 OLS efficiency controls | age_scaled_sq | 0.154 | 0.056 | 0.006 |
| M2 OLS efficiency controls | log_nb_words | -3.994 | 0.147 | 0.000 |
| M3 LMM child random intercept | Intercept | -0.000 | 515595.489 | 1.000 |
| M3 LMM child random intercept | age_scaled | -0.372 | 0.037 | 0.000 |
| M3 LMM child random intercept | log_nb_words | -4.077 | 0.050 | 0.000 |
| M3 LMM child random intercept | Group Var | 0.000 |  |  |
| M4 LMM child random intercept + age slope | Intercept | 14.626 | 0.264 | 0.000 |
| M4 LMM child random intercept + age slope | age_scaled | -0.810 | 0.235 | 0.001 |
| M4 LMM child random intercept + age slope | log_nb_words | -4.108 | 0.081 | 0.000 |
| M4 LMM child random intercept + age slope | Group Var | 0.054 | 0.124 | 0.664 |
| M4 LMM child random intercept + age slope | Group x age_scaled Cov | -0.002 | 0.024 | 0.927 |
| M4 LMM child random intercept + age slope | age_scaled Var | 0.040 | 0.016 | 0.011 |
| M5 Gamma GEE baseline comparison | Intercept | 2.530 | 0.026 | 0.000 |
| M5 Gamma GEE baseline comparison | C(target_variant)[T.random] | 0.749 | 0.017 | 0.000 |
| M5 Gamma GEE baseline comparison | C(target_variant)[T.unigram] | 0.396 | 0.016 | 0.000 |
| M5 Gamma GEE baseline comparison | C(target_variant)[T.bigram] | 0.275 | 0.015 | 0.000 |
| M5 Gamma GEE baseline comparison | C(target_variant)[T.trigram] | 0.196 | 0.012 | 0.000 |
| M5 Gamma GEE baseline comparison | C(target_variant)[T.caretaker] | 0.000 | 0.000 | 0.000 |
| M5 Gamma GEE baseline comparison | age_scaled | -0.034 | 0.008 | 0.000 |
| M5 Gamma GEE baseline comparison | age_scaled:C(target_variant)[T.random] | 0.073 | 0.011 | 0.000 |
| M5 Gamma GEE baseline comparison | age_scaled:C(target_variant)[T.unigram] | 0.040 | 0.008 | 0.000 |
| M5 Gamma GEE baseline comparison | age_scaled:C(target_variant)[T.bigram] | 0.035 | 0.008 | 0.000 |
| M5 Gamma GEE baseline comparison | age_scaled:C(target_variant)[T.trigram] | 0.035 | 0.007 | 0.000 |
| M5 Gamma GEE baseline comparison | age_scaled:C(target_variant)[T.caretaker] | 0.000 | 0.000 |  |
| M5 Gamma GEE baseline comparison | nb_words | 0.247 | 0.009 | 0.000 |
| Context extension Gaussian GEE | Intercept | 13.849 | 1351267.878 | 1.000 |
| Context extension Gaussian GEE | C(context_k)[T.k1] | 4.533 | 1116226.993 | 1.000 |
| Context extension Gaussian GEE | C(context_k)[T.k2] | 3.146 | 1612205.874 | 1.000 |
| Context extension Gaussian GEE | C(context_k)[T.k3] | 2.346 |  |  |
| Context extension Gaussian GEE | age_scaled | -0.393 | 0.113 | 0.000 |
| Context extension Gaussian GEE | log_nb_words | -4.732 | 0.156 | 0.000 |
| Context extension Gaussian GEE | context_entropy_bits | -0.147 | 0.030 | 0.000 |

## Compact Model Statistics

Short version:

| model | status | r2 | r2_type | p_age |
| --- | --- | --- | --- | --- |
| M1 OLS total bits | fit | 0.745 | OLS R2 | 0.000 |
| M2 OLS efficiency controls | fit | 0.251 | OLS R2 | 0.012 |
| M3 LMM child random intercept | fit_converged |  | descriptive fitted-observed R2 | 0.000 |
| M4 LMM child random intercept + age slope | fit_not_converged | 0.282 | descriptive fitted-observed R2 | 0.001 |
| M5 Gamma GEE baseline comparison | fit | 0.016 | descriptive fitted-observed R2 | 0.000 |
| Context extension Gaussian GEE | fit | 0.339 | descriptive fitted-observed R2 | 0.000 |

Full version:

| model_key | model | outcome | controlled_for | context | status | r2 | r2_type | p_age_scaled | p_age_scaled_sq | p_nb_words | p_log_nb_words | p_context_entropy_bits | min_p_target_variant | min_p_age_by_variant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m1 | M1 OLS total bits | sum_bits | nb_words | k0/no context | fit | 0.745 | OLS R2 | 0.000 |  | 0.000 |  |  |  |  |
| m2 | M2 OLS efficiency controls | bits_per_word | log_nb_words | k3 fixed | fit | 0.251 | OLS R2 | 0.012 | 0.006 |  | 0.000 |  |  |  |
| m3 | M3 LMM child random intercept | bits_per_word | log_nb_words + child random intercept | k3 fixed | fit_converged |  | descriptive fitted-observed R2 | 0.000 |  |  | 0.000 |  |  |  |
| m4 | M4 LMM child random intercept + age slope | bits_per_word | log_nb_words + child random intercept/slope | k3 fixed | fit_not_converged | 0.282 | descriptive fitted-observed R2 | 0.001 |  |  | 0.000 |  |  |  |
| m5 | M5 Gamma GEE baseline comparison | sum_bits | nb_words + target variant + child-clustered correlation | k3 fixed | fit | 0.016 | descriptive fitted-observed R2 | 0.000 |  | 0.000 |  |  | 0.000 | 0.000 |
| context_extension | Context extension Gaussian GEE | bits_per_word | log_nb_words + context_entropy_bits + context_k | k1/k2/k3 matched entropy rows | fit | 0.339 | descriptive fitted-observed R2 | 0.000 |  |  | 0.000 | 0.000 |  |  |

## Child-Control Ladder

Because individual children can differ systematically, the primary
developmental question should be checked in both simple and child-controlled
forms. This ladder uses real child utterances only, keeps age in every model,
and controls for one effort measure at a time:

- `OLS: age + effort`: simple length-controlled model, child-clustered standard
  errors but no child term;
- `OLS: age + effort + child fixed effects`: directly controls for each
  child's baseline level;
- `GEE: age + effort grouped by child`: population-averaged model with
  child-level correlation.

![Child control ladder](../figs/utterance_information_model_proposals/child_control_ladder_r2_age_pvalues.png)

| effort_control | effort_label | child_control | child_control_label | status | n_obs | n_children | r2 | r2_type | p_age | p_effort | formula | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nb_words | Words | length_age_only | OLS: age + effort | fit | 23400 | 21 | 0.631 | OLS R2 | 0.711 | 0.000 | sum_bits ~ age_scaled + effort_value | no child term; child-clustered SE |
| nb_words | Words | child_fixed_effects | OLS: age + effort + child fixed effects | fit | 23400 | 21 | 0.642 | OLS R2 | 0.020 | 0.000 | sum_bits ~ age_scaled + effort_value + C(child_id) | child fixed effects; child-clustered SE |
| nb_words | Words | gee_child_exchangeable | GEE: age + effort grouped by child | fit | 23400 | 21 | 0.629 | descriptive fitted-observed R2 | 0.016 | 0.000 | sum_bits ~ age_scaled + effort_value | child exchangeable correlation |
| nb_morphemes | Morphemes | length_age_only | OLS: age + effort | fit | 23400 | 21 | 0.617 | OLS R2 | 0.834 | 0.000 | sum_bits ~ age_scaled + effort_value | no child term; child-clustered SE |
| nb_morphemes | Morphemes | child_fixed_effects | OLS: age + effort + child fixed effects | fit | 23400 | 21 | 0.631 | OLS R2 | 0.029 | 0.000 | sum_bits ~ age_scaled + effort_value + C(child_id) | child fixed effects; child-clustered SE |
| nb_morphemes | Morphemes | gee_child_exchangeable | GEE: age + effort grouped by child | fit | 23400 | 21 | 0.615 | descriptive fitted-observed R2 | 0.024 | 0.000 | sum_bits ~ age_scaled + effort_value | child exchangeable correlation |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | length_age_only | OLS: age + effort | fit | 23400 | 21 | 0.647 | OLS R2 | 0.384 | 0.000 | sum_bits ~ age_scaled + effort_value | no child term; child-clustered SE |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | child_fixed_effects | OLS: age + effort + child fixed effects | fit | 23400 | 21 | 0.659 | OLS R2 | 0.162 | 0.000 | sum_bits ~ age_scaled + effort_value + C(child_id) | child fixed effects; child-clustered SE |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | gee_child_exchangeable | GEE: age + effort grouped by child | fit | 23400 | 21 | 0.646 | descriptive fitted-observed R2 | 0.150 | 0.000 | sum_bits ~ age_scaled + effort_value | child exchangeable correlation |
| nb_syllables_pkg | Syllables: pkg | length_age_only | OLS: age + effort | fit | 23400 | 21 | 0.629 | OLS R2 | 0.089 | 0.000 | sum_bits ~ age_scaled + effort_value | no child term; child-clustered SE |
| nb_syllables_pkg | Syllables: pkg | child_fixed_effects | OLS: age + effort + child fixed effects | fit | 23400 | 21 | 0.641 | OLS R2 | 0.286 | 0.000 | sum_bits ~ age_scaled + effort_value + C(child_id) | child fixed effects; child-clustered SE |
| nb_syllables_pkg | Syllables: pkg | gee_child_exchangeable | GEE: age + effort grouped by child | fit | 23400 | 21 | 0.627 | descriptive fitted-observed R2 | 0.275 | 0.000 | sum_bits ~ age_scaled + effort_value | child exchangeable correlation |
| nb_phonemes | Phonemes | length_age_only | OLS: age + effort | fit | 23400 | 21 | 0.643 | OLS R2 | 0.202 | 0.000 | sum_bits ~ age_scaled + effort_value | no child term; child-clustered SE |
| nb_phonemes | Phonemes | child_fixed_effects | OLS: age + effort + child fixed effects | fit | 23400 | 21 | 0.655 | OLS R2 | 0.098 | 0.000 | sum_bits ~ age_scaled + effort_value + C(child_id) | child fixed effects; child-clustered SE |
| nb_phonemes | Phonemes | gee_child_exchangeable | GEE: age + effort grouped by child | fit | 23400 | 21 | 0.640 | descriptive fitted-observed R2 | 0.089 | 0.000 | sum_bits ~ age_scaled + effort_value | child exchangeable correlation |

## Effort-Control Sensitivity At The Utterance Level

These plots use total utterance bits as the outcome and control for only one
effort measure at a time. This avoids putting highly collinear measures in the
same model while still showing whether the age trajectory depends on the chosen
effort granularity.

Child real utterances and generated baselines only:

![Effort sensitivity child short](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_and_baselines_short.png)

![Effort sensitivity child full](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_and_baselines_full.png)

Child real utterances, generated baselines, and caretakers:

![Effort sensitivity with caretakers short](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_baselines_and_caretaker_short.png)

![Effort sensitivity with caretakers full](../figs/utterance_information_model_proposals/effort_sensitivity_child_real_baselines_and_caretaker_full.png)

Short effort-control statistics:

| scope_label | effort_label | status | r2 | p_age | p_effort | min_p_group | min_p_age_by_group |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Child real + generated baselines | Words | fit | 0.822 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines | Morphemes | fit | 0.828 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines | Syllables: CMU/pkg | fit | 0.867 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines | Syllables: pkg | fit | 0.858 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines | Phonemes | fit | 0.879 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines + caretakers | Words | fit | 0.741 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines + caretakers | Morphemes | fit | 0.750 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines + caretakers | Syllables: CMU/pkg | fit | 0.799 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines + caretakers | Syllables: pkg | fit | 0.790 | 0.000 | 0.000 | 0.000 | 0.000 |
| Child real + generated baselines + caretakers | Phonemes | fit | 0.809 | 0.000 | 0.000 | 0.000 | 0.000 |

Full effort-control statistics:

| scope | scope_label | effort_control | effort_label | status | n_obs | n_children | r2 | r2_type | p_age | p_effort | min_p_group | min_p_age_by_group | formula |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| child_real_and_baselines | Child real + generated baselines | nb_words | Words | fit | 62400 | 21 | 0.822 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_and_baselines | Child real + generated baselines | nb_morphemes | Morphemes | fit | 62400 | 21 | 0.828 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_and_baselines | Child real + generated baselines | nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | fit | 62400 | 21 | 0.867 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_and_baselines | Child real + generated baselines | nb_syllables_pkg | Syllables: pkg | fit | 62400 | 21 | 0.858 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_and_baselines | Child real + generated baselines | nb_phonemes | Phonemes | fit | 62400 | 21 | 0.879 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_baselines_and_caretaker | Child real + generated baselines + caretakers | nb_words | Words | fit | 74880 | 21 | 0.741 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_baselines_and_caretaker | Child real + generated baselines + caretakers | nb_morphemes | Morphemes | fit | 74880 | 21 | 0.750 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_baselines_and_caretaker | Child real + generated baselines + caretakers | nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | fit | 74880 | 21 | 0.799 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_baselines_and_caretaker | Child real + generated baselines + caretakers | nb_syllables_pkg | Syllables: pkg | fit | 74880 | 21 | 0.790 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |
| child_real_baselines_and_caretaker | Child real + generated baselines + caretakers | nb_phonemes | Phonemes | fit | 74880 | 21 | 0.809 | OLS R2 | 0.000 | 0.000 | 0.000 | 0.000 | sum_bits ~ age_scaled * C(comparison_group) + effort_value |

## What Should Go Into The Real Report?

Recommended first pass:

1. Use Model 2 as the simple interpretive baseline.
2. Use Model 3 as the first main child-aware model.
3. Treat Model 4 as a developmental-trajectory candidate, but refit it more
   carefully before using it inferentially because the statsmodels pilot did
   not converge.
4. Use Model 5 for real-versus-baseline comparisons.
5. Keep context entropy as a follow-up once the small entropy patch is scored.
6. Do not include all effort predictors in the same model because the VIF
   diagnostics show that they are measuring strongly overlapping quantities.

Outputs written under:

```text
results/utterance_information_model_proposals
figs/utterance_information_model_proposals
```
