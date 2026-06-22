# Route 1 Focused Candidate Regression-Line Gallery

This is a pre-supervisor evidence gallery for choosing the strongest Route 1 figures. It is intentionally plot-first and candidate-focused, not a dump of every M1-M15 Atlas section.

The report keeps the scientific target fixed: estimate conditional utterance information at fixed production effort from repeated utterances sampled from the same children across sessions and ages.

## Scope Lock

- Main Route 1 estimand: age-related change in `sum_bits` after conditioning on child production effort and other controls.
- This is communicative efficiency, not MLU. Raw total bits can increase with age simply because children say longer utterances.
- Main effort control: child production effort, shown here with the word-count effort axis already used in the fixed-effort Atlas.
- Parent/caretaker effort means the amount of preceding caretaker context production.
- Child identity matters because the same children are observed repeatedly across sessions; child fixed effects or child-level random effects are used to avoid treating children as interchangeable single rows.
- Tables are kept minimal. The central evidence objects are regression/fixed-effort age lines.
- Bits per token, such as `mean_bits_per_token` or `sum_bits / nb_words`, is a secondary rate outcome and is not the same question as conditional total bits at fixed effort.
- Raw observed-vs-fitted total-bit diagnostics are not promoted here because they mostly show the mechanical relation between length and total bits.
- Whenever an interaction appears below, the lower-level predictors are written explicitly.

## Estimator Rationale

- **OLS + child fixed effects + clustered SE:** main Atlas-compatible view; controls stable child identity and clusters uncertainty by child.
- **GEE Gaussian by child:** population-average repeated-measures check for a continuous bits outcome.
- **GEE Gamma/log by child:** robustness check for positive, skewed bit outcomes; interpret through prediction lines rather than raw coefficient scale.
- **GLM Gaussian and GLM Gamma/log:** distribution/link sensitivity checks where feasible.
- **MixedLM random child intercept:** lets each child have a different baseline information level.
- **MixedLM random child age slope:** lets each child have a different developmental trajectory; convergence warnings matter.
- **Month/session aggregation:** useful only as robustness against pseudo-replication, not as the main row-level result.

## Candidate Formula Family

The focused parent-effort family requested for model selection is about conditional information, not raw length growth:

```text
sum_bits ~ age_c + effort_c + C(child_id)
sum_bits ~ age_c + effort_c + parent_context_effort_c + C(child_id)
sum_bits ~ age_c + effort_c + age_c:effort_c + parent_context_effort_c + C(child_id)
sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:parent_context_effort_c + C(child_id)
sum_bits ~ age_c + effort_c + parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)
sum_bits ~ age_c + effort_c + parent_context_effort_c + age_c:effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)
```

Existing promising Atlas candidates are used when they match this logic or answer an adjacent necessary control question: M2, M3, M4a, M4c, M5, M6, M7, M11, and M15.

## Source Reports Used

- Real-child Atlas v2: [utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html)
- Source-specific Atlas v2 index: [utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.html](utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.html)
- Heldout prediction report: [utterance_information_route1_heldout_real_child_prediction_report.html](utterance_information_route1_heldout_real_child_prediction_report.html)
- Age-scrambling robustness report: [utterance_information_age_scrambling_robustness.html](utterance_information_age_scrambling_robustness.html)
- Caretaker Atlas v2: [utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html)

## Reading Rule

Each fixed-effort line is a row-level model prediction for utterance `sum_bits` at a fixed child-effort or caretaker-effort value. Read the slope as conditional information at the same effort level; do not read it as children simply producing longer utterances.

## Multiple Age Effects Can Coexist

The report keeps both effects visible because they answer different questions.

- **Pooled effort-only question:** if we control child production effort but do not control child identity, what is the age trend across the pooled corpus?
- **Child-controlled question:** within the repeated-measures design, after controlling stable child identity, what is the age trend at the same effort level?

### Pooled Effort-Only Contrast

**M1 row-level Atlas.** `sum_bits ~ age_c + effort_c`; age coefficient 0.0003 bits/month, p=0.993; observed-vs-fitted R2 0.6130.

**M1 fixed-effort slope read.** upward; 0.000 to 0.000 bits/month. In the row-level Atlas this is essentially flat/slightly upward, not the child-controlled decrease.

![M1 pooled effort-only fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m1_nb_words_fixed_effort_atlas.png)

**M1 balanced/scrambled robustness read.** age-bin/unit robustness observed age coefficient 0.0542; balanced bootstrap 95% interval [-0.0144, 0.0550], median 0.0205; observed inside; age-bin label scramble 95% interval [-0.0538, 0.0423], median 0.0026; observed outside, p=0.040; unit-age scramble 95% interval [-0.0165, 0.0170], median -0.0008; observed outside, p=0.010; within-child age scramble 95% interval [0.0599, 0.0823], median 0.0731; observed outside, p=1.000.

**M1 within-child scramble note.** The within-child age-scramble null is even more positive than the observed M1 slope. That is exactly why M1 is treated as a pooled/compositional contrast, not as the within-child communicative-efficiency result.

![M1 balanced and scrambled robustness lines](../figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png)

### Child-Controlled Contrast

**M2 row-level Atlas.** `sum_bits ~ age_c + effort_c + C(child_id)`; age coefficient -0.1225 bits/month, p=<.001; observed-vs-fitted R2 0.6259.

**M2 fixed-effort slope read.** downward; -0.122 to -0.122 bits/month.

![M2 child-identity fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m2_nb_words_fixed_effort_atlas.png)

**M2 balanced/scrambled robustness read.** age-bin/unit robustness observed age coefficient -0.0400; balanced bootstrap 95% interval [-0.1675, -0.0357], median -0.0867; observed inside; age-bin label scramble 95% interval [-0.0252, 0.0283], median 0.0002; observed outside, p=0.010; unit-age scramble 95% interval [-0.0131, 0.0133], median 0.0003; observed outside, p=0.010; within-child age scramble 95% interval [-0.0202, 0.0182], median -0.0009; observed outside, p=0.010.

![M2 balanced and scrambled robustness lines](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

**M3 row-level Atlas.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`; age coefficient -0.1216 bits/month, p=<.001; observed-vs-fitted R2 0.6259.

**M3 fixed-effort slope read.** downward; -0.157 to -0.115 bits/month.

![M3 age-by-effort fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png)

![M3 balanced and scrambled robustness lines](../figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png)

**Interpretation.** The pooled M1 effect is a real descriptive/compositional effect of the sampled corpus. The Route 1 efficiency claim is the child-controlled effect: at the same effort level, with child identity handled, the fixed-effort slopes go downward. Both belong in the model-selection report because they explain why controlling child identity changes the story.

## M2. Base fixed-effort child model

**Why this candidate is here.** Baseline candidate: asks the communicative-efficiency question directly by comparing conditional information at fixed child effort and stable child identity.

**Natural-language test.** At the same child effort level, are older sessions lower or higher in conditional utterance information for the same child identities?

**Row-level formula.** `sum_bits ~ age_c + effort_c + C(child_id)`

Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. The age coefficient is -0.122 bits/month (p=<.001) after the listed controls. Existing row-level Atlas fixed-effort slopes are downward: -0.122 to -0.122 bits/month across the fixed word-effort values.

### Real Child Regression Lines

![M2 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m2_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.122 to -0.122 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M2 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.178 to 0.178 bits/month

#### Unigram baseline

![M2 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.021 to -0.021 bits/month

#### Bigram baseline

![M2 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.022 to -0.022 bits/month

#### Trigram baseline

![M2 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.015 to -0.015 bits/month

#### LSTM k3 same-length baseline

![M2 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.046 to -0.046 bits/month

#### LSTM k4 same-length baseline

![M2 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.058 to -0.058 bits/month

#### LSTM k5 same-length baseline

![M2 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m2_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.061 to -0.061 bits/month

### Caretaker Contrast Regression Lines

![M2 caretaker contrast fixed-effort regression lines](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_words_fixed_effort_atlas.png)

**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.

### Repeated-Measurement Estimator Checks

Row-level repeated-measures sensitivity available: CS0: ols nonrobust (fit); CS0c: ols cluster_child (fit); CS1: ols cluster_child (fit); CS2: ols cluster_child (fit); CS3: gee_gaussian robust (fit); CS4: mixedlm random effects 1 (fit); CS5: mixedlm random effects ~age_c (fit); CS6: ols cluster_child (fit); CS7: ols cluster_child (fit).

### All-Estimator Screening Lines

![M2 all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m2_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M3. Child effort interaction model

**Why this candidate is here.** Tests the user's core interaction concern: older children generally produce longer utterances, so the model asks whether the age slope changes at different child-effort levels.

**Natural-language test.** Does the age-information relation depend on the child utterance effort level?

**Row-level formula.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(child_id)`

Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. The age coefficient is -0.122 bits/month (p=<.001) after the listed controls. Existing row-level Atlas fixed-effort slopes are downward: -0.157 to -0.115 bits/month across the fixed word-effort values.

### Real Child Regression Lines

![M3 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.157 to -0.115 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M3 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.161 to 0.261 bits/month

#### Unigram baseline

![M3 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.285 to 0.034 bits/month

#### Bigram baseline

![M3 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.245 to 0.024 bits/month

#### Trigram baseline

![M3 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.126 to 0.008 bits/month

#### LSTM k3 same-length baseline

![M3 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.242 to -0.006 bits/month

#### LSTM k4 same-length baseline

![M3 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.281 to -0.012 bits/month

#### LSTM k5 same-length baseline

![M3 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m3_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.251 to -0.021 bits/month

### Caretaker Contrast Regression Lines

![M3 caretaker contrast fixed-effort regression lines](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_words_fixed_effort_atlas.png)

**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.

### Repeated-Measurement Estimator Checks

Row-level repeated-measures sensitivity available: CS0: ols nonrobust (fit); CS0c: ols cluster_child (fit); CS1: ols cluster_child (fit); CS2: ols cluster_child (fit); CS3: gee_gaussian robust (fit); CS4: mixedlm random effects 1 (fit); CS5: mixedlm random effects ~age_c (fit); CS6: ols cluster_child (fit); CS7: ols cluster_child (fit).

### All-Estimator Screening Lines

![M3 all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m3_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M4a. Parent-context effort model

**Why this candidate is here.** Closest existing row-level Atlas candidate to the simple formula `sum_bits ~ age + child effort + parent effort + child identity`; it adds preceding parent/caretaker effort while keeping the age-by-child-effort term already used in the Atlas ladder.

**Natural-language test.** Does the age pattern remain after accounting for how much the parent/caretaker just said?

### Real Child Regression Lines

![M4a real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4a_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.154 to -0.109 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M4a Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.157 to 0.259 bits/month

#### Unigram baseline

![M4a Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.287 to 0.032 bits/month

#### Bigram baseline

![M4a Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.246 to 0.022 bits/month

#### Trigram baseline

![M4a Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.125 to 0.009 bits/month

#### LSTM k3 same-length baseline

![M4a LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.242 to -0.005 bits/month

#### LSTM k4 same-length baseline

![M4a LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.280 to -0.011 bits/month

#### LSTM k5 same-length baseline

![M4a LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4a_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.251 to -0.021 bits/month

### Caretaker Contrast Regression Lines

![M4a caretaker contrast fixed-effort regression lines](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4a_nb_words_fixed_effort_atlas.png)

**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.

### Repeated-Measurement Estimator Checks

Row-level repeated-measures sensitivity available: CS0: ols nonrobust (fit); CS0c: ols cluster_child (fit); CS1: ols cluster_child (fit); CS2: ols cluster_child (fit); CS3: gee_gaussian robust (fit); CS4: mixedlm random effects 1 (fit); CS5: mixedlm random effects ~age_c (fit); CS6: ols cluster_child (fit); CS7: ols cluster_child (fit).

## M4c. Question/form control model

**Why this candidate is here.** Checks whether the fixed-effort age pattern is just a question/statement or prompt-form artifact.

**Natural-language test.** Does the age effect survive broad context-form controls?

**Row-level formula.** `sum_bits ~ age_c + effort_c + age_c:effort_c + C(question_type) + C(child_id)`

Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. The age coefficient is -0.127 bits/month (p=<.001) after the listed controls. Existing row-level Atlas fixed-effort slopes are downward: -0.164 to -0.121 bits/month across the fixed word-effort values.

### Real Child Regression Lines

![M4c real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.164 to -0.121 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M4c Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.158 to 0.256 bits/month

#### Unigram baseline

![M4c Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.291 to 0.031 bits/month

#### Bigram baseline

![M4c Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.251 to 0.021 bits/month

#### Trigram baseline

![M4c Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.133 to 0.004 bits/month

#### LSTM k3 same-length baseline

![M4c LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.248 to -0.011 bits/month

#### LSTM k4 same-length baseline

![M4c LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.287 to -0.017 bits/month

#### LSTM k5 same-length baseline

![M4c LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.257 to -0.026 bits/month

### Caretaker Contrast Regression Lines

![M4c caretaker contrast fixed-effort regression lines](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4c_nb_words_fixed_effort_atlas.png)

**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.

### Repeated-Measurement Estimator Checks

Row-level repeated-measures sensitivity available: CS0: ols nonrobust (fit); CS0c: ols cluster_child (fit); CS1: ols cluster_child (fit); CS2: ols cluster_child (fit); CS3: gee_gaussian robust (fit); CS4: mixedlm random effects 1 (fit); CS5: mixedlm random effects ~age_c (fit); CS6: ols cluster_child (fit); CS7: ols cluster_child (fit).

### All-Estimator Screening Lines

![M4c all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m4c_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M5. Combined parent/context control model

**Why this candidate is here.** Promising fuller candidate: keeps child effort, parent effort, context entropy, question type, and child identity in one row-level model.

**Natural-language test.** Does the age pattern remain when the main parent-context and predictability controls are in the same model?

**Row-level formula.** `sum_bits ~ age_c + effort_c + age_c:effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + C(child_id)`

Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. The age coefficient is -0.122 bits/month (p=<.001) after the listed controls. Existing row-level Atlas fixed-effort slopes are downward: -0.149 to -0.118 bits/month across the fixed word-effort values.

### Real Child Regression Lines

![M5 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m5_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.149 to -0.118 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M5 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.159 to 0.268 bits/month

#### Unigram baseline

![M5 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.320 to 0.030 bits/month

#### Bigram baseline

![M5 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.269 to 0.018 bits/month

#### Trigram baseline

![M5 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.148 to 0.006 bits/month

#### LSTM k3 same-length baseline

![M5 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.277 to -0.010 bits/month

#### LSTM k4 same-length baseline

![M5 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.305 to -0.016 bits/month

#### LSTM k5 same-length baseline

![M5 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m5_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.281 to -0.027 bits/month

### Caretaker Contrast Regression Lines

![M5 caretaker contrast fixed-effort regression lines](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm5_nb_words_fixed_effort_atlas.png)

**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.

### Repeated-Measurement Estimator Checks

Row-level repeated-measures sensitivity available: CS0: ols nonrobust (fit); CS0c: ols cluster_child (fit); CS1: ols cluster_child (fit); CS2: ols cluster_child (fit); CS3: gee_gaussian robust (fit); CS4: mixedlm random effects 1 (fit); CS5: mixedlm random effects ~age_c (fit); CS6: ols cluster_child (fit); CS7: ols cluster_child (fit).

### All-Estimator Screening Lines

![M5 all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m5_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M6. Context entropy interaction model

**Why this candidate is here.** Promising robustness candidate from M1-M15: lets the relation with context entropy vary by age and child effort while preserving lower-order predictors.

**Natural-language test.** Is the age pattern robust when context predictability can interact with age and effort?

### Real Child Regression Lines

![M6 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m6_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.148 to -0.119 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M6 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.160 to 0.275 bits/month

#### Unigram baseline

![M6 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.311 to 0.029 bits/month

#### Bigram baseline

![M6 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.259 to 0.017 bits/month

#### Trigram baseline

![M6 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.135 to 0.005 bits/month

#### LSTM k3 same-length baseline

![M6 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.269 to -0.012 bits/month

#### LSTM k4 same-length baseline

![M6 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.299 to -0.018 bits/month

#### LSTM k5 same-length baseline

![M6 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m6_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.274 to -0.028 bits/month

### Caretaker Contrast Regression Lines

![M6 caretaker contrast fixed-effort regression lines](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_words_fixed_effort_atlas.png)

**Caretaker read.** This asks the analogous fixed-effort question for caretaker speech from the same developmental axis. It is a contrast for whether the child-age pattern also appears in adult/caretaker utterances.

### Repeated-Measurement Estimator Checks

Row-level repeated-measures sensitivity available: CS0: ols nonrobust (fit); CS0c: ols cluster_child (fit); CS1: ols cluster_child (fit); CS2: ols cluster_child (fit); CS3: gee_gaussian robust (fit); CS4: mixedlm random effects 1 (fit); CS5: mixedlm random effects ~age_c (fit); CS6: ols cluster_child (fit); CS7: ols cluster_child (fit).

## M7. Nonlinear age model

**Why this candidate is here.** Checks whether development is being forced into one straight line.

**Natural-language test.** Is the developmental pattern approximately linear, or does a curved age term matter?

**Row-level formula.** `sum_bits ~ age_c + effort_c + I(age_c ** 2) + C(child_id)`

Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. The age coefficient is -0.144 bits/month (p=0.002) after the listed controls. Existing row-level Atlas fixed-effort slopes are downward: -0.119 to -0.119 bits/month across the fixed word-effort values.

### Real Child Regression Lines

![M7 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m7_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.119 to -0.119 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M7 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.174 to 0.174 bits/month

#### Unigram baseline

![M7 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.019 to -0.019 bits/month

#### Bigram baseline

![M7 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.022 to -0.022 bits/month

#### Trigram baseline

![M7 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.015 to -0.015 bits/month

#### LSTM k3 same-length baseline

![M7 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.043 to -0.043 bits/month

#### LSTM k4 same-length baseline

![M7 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.055 to -0.055 bits/month

#### LSTM k5 same-length baseline

![M7 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m7_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.057 to -0.057 bits/month

### Repeated-Measurement Estimator Checks

No row-level all-estimator sensitivity table is currently available for this candidate. The fixed-effort source plots shown here are the OLS child-fixed-effect Atlas view.

## M11. Age by parent-context effort model

**Why this candidate is here.** Directly addresses whether children react differently to parent context effort as they age.

**Natural-language test.** Does the parent-context-effort relation change with child age?

### Real Child Regression Lines

![M11 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m11_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.139 to -0.117 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M11 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.160 to 0.271 bits/month

#### Unigram baseline

![M11 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.321 to 0.030 bits/month

#### Bigram baseline

![M11 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.267 to 0.019 bits/month

#### Trigram baseline

![M11 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.145 to 0.007 bits/month

#### LSTM k3 same-length baseline

![M11 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.276 to -0.010 bits/month

#### LSTM k4 same-length baseline

![M11 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.308 to -0.017 bits/month

#### LSTM k5 same-length baseline

![M11 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m11_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.280 to -0.027 bits/month

### Repeated-Measurement Estimator Checks

No row-level all-estimator sensitivity table is currently available for this candidate. The fixed-effort source plots shown here are the OLS child-fixed-effect Atlas view.

## M15. Rich interaction stress test

**Why this candidate is here.** Stress-test candidate, not the cleanest supervisor story: keeps the main age, child-effort, parent-effort, context-entropy, and context-form interactions together.

**Natural-language test.** Does the fixed-effort age pattern survive the richest currently available row-level interaction model?

**Row-level formula.** `sum_bits ~ age_c + effort_c + age_c:effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + effort_c:context_entropy_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + context_entropy_c:C(question_type) + C(child_id)`

Primary row-level result: the outcome is utterance-level `sum_bits`, not an aggregate mean. The age coefficient is -0.127 bits/month (p=<.001) after the listed controls. Existing row-level Atlas fixed-effort slopes are downward: -0.139 to -0.125 bits/month across the fixed word-effort values.

### Real Child Regression Lines

![M15 real child fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m15_nb_words_fixed_effort_atlas.png)

**Real-child read.** downward; -0.139 to -0.125 bits/month This is the main child-language plot for this candidate.

### Generated Baseline Regression Lines

#### Random matched-length baseline

![M15 Random matched-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** upward; 0.156 to 0.278 bits/month

#### Unigram baseline

![M15 Unigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.311 to 0.025 bits/month

#### Bigram baseline

![M15 Bigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.257 to 0.014 bits/month

#### Trigram baseline

![M15 Trigram baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** downward, upward; -0.132 to 0.002 bits/month

#### LSTM k3 same-length baseline

![M15 LSTM k3 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.267 to -0.014 bits/month

#### LSTM k4 same-length baseline

![M15 LSTM k4 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.301 to -0.022 bits/month

#### LSTM k5 same-length baseline

![M15 LSTM k5 same-length baseline fixed-effort regression lines](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m15_nb_words_fixed_effort_atlas.png)

**Line read.** downward; -0.274 to -0.031 bits/month

### Repeated-Measurement Estimator Checks

No row-level all-estimator sensitivity table is currently available for this candidate. The fixed-effort source plots shown here are the OLS child-fixed-effect Atlas view.

### All-Estimator Screening Lines

![M15 all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m15_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## Exact Parent-Effort Interaction Screening

## M5_no_question. Exact context-control model without question type

**Why this candidate is here.** Separates the parent/context controls from question type so question coding is not doing hidden work.

**Formula.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Status.** These are all-estimator screening artifacts for the requested parent-effort variants. They are useful for model choice, but the row-level source-specific Atlas should be regenerated for any variant promoted to the supervisor report.

### All-Estimator Screening Lines

![M5_no_question all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m5_no_question_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M5_age_effort_no_question. Age by child-effort interaction without question type

**Why this candidate is here.** Tests whether child effort changes the age relation while excluding question type.

**Formula.** `sum_bits ~ age_c + effort_c + age_c:effort_c + context_entropy_c + parent_context_effort_c + C(child_id)`

**Status.** These are all-estimator screening artifacts for the requested parent-effort variants. They are useful for model choice, but the row-level source-specific Atlas should be regenerated for any variant promoted to the supervisor report.

### All-Estimator Screening Lines

![M5_age_effort_no_question all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m5_age_effort_no_question_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M5_parent_reaction_no_question. Parent-reaction interaction model without question type

**Why this candidate is here.** Directly tests whether parent context effort relates differently to child bits by age and by child effort.

**Formula.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(child_id)`

**Status.** These are all-estimator screening artifacts for the requested parent-effort variants. They are useful for model choice, but the row-level source-specific Atlas should be regenerated for any variant promoted to the supervisor report.

### All-Estimator Screening Lines

![M5_parent_reaction_no_question all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m5_parent_reaction_no_question_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## M5_parent_reaction_question. Parent-reaction interaction model with question type

**Why this candidate is here.** Same parent-reaction test, but with question/form controls added.

**Formula.** `sum_bits ~ age_c + effort_c + context_entropy_c + parent_context_effort_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + C(question_type) + C(child_id)`

**Status.** These are all-estimator screening artifacts for the requested parent-effort variants. They are useful for model choice, but the row-level source-specific Atlas should be regenerated for any variant promoted to the supervisor report.

### All-Estimator Screening Lines

![M5_parent_reaction_question all-estimator fixed-effort screening lines](../figs/route1_best_model_robustness_package/m5_parent_reaction_question_aggregate_estimator_fixed_effort_age_lines.png)

**Estimator read.** This plot compares OLS fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log, MixedLM random intercept, and MixedLM random age slope on the same candidate formula. It is a fixed-effort screening/robustness plot for repeated utterance measurements, not a raw total-bits growth plot and not a replacement for the row-level source-specific Atlas line above.

## Heldout Prediction

These are the prediction plots that matter here: actual heldout child regression lines and PBM-trained predicted regression lines in the same panel.

![Heldout actual vs predicted regression lines](../figs/supervisor_candidate_report/heldout_pop_m4c_actual_vs_predicted_regression_lines.png)

**Heldout read.** These are the prediction plots that matter for generalization: actual heldout child regression lines and PBM-trained predicted regression lines in the same panel.

![Heldout calibration and residuals](../figs/supervisor_candidate_report/heldout_pop_m4c_calibration_residuals.png)

## Robustness Regression-Line Checks

![Age-scrambling regression-line robustness](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

![Age-scrambling outside-null heatmap](../figs/age_scrambling_robustness/robustness_outside_null_heatmap.png)

## Contrast Plots

![Source comparison fixed-effort slopes](../figs/supervisor_candidate_report/source_comparison_m4c_k3_words_slopes.png)

![Caretaker fixed-effort CM2](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_words_fixed_effort_atlas.png)

![Caretaker fixed-effort CM6](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_words_fixed_effort_atlas.png)

## Secondary Rate Outcome Status

`mean_bits_per_token` is available in the long scored dataset and can be modeled as a separate rate outcome. It should not be mixed into the main fixed-effort total-bits claim. The next rate-outcome check should reuse the strongest total-bits candidate formula and label the result as bits-per-token evidence.

## Saved Row-Level Artifacts

```text
results/route1_source_specific_corrected_fixed_effort_atlas/real/model_summary.csv
results/route1_source_specific_corrected_fixed_effort_atlas/real/fixed_slice_slopes.csv
results/route1_source_specific_corrected_fixed_effort_atlas/real/fixed_effort_predictions.csv.gz
results/route1_source_specific_corrected_fixed_effort_atlas
results/route1_caretaker_atlas/full_fit/caretaker_model_summary.csv
results/route1_heldout_real_child_prediction/heldout_prediction_fit_summary.csv
results/route1_corrected_baseline_atlas/full_child_structure_sensitivity/source_specific_model_summary.csv
figs/route1_best_model_robustness_package
```
