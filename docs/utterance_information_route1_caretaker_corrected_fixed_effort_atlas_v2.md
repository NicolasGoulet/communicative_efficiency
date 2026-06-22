# Route 1 Caretaker Corrected Fixed-Effort Atlas v2

This is the caretaker-target analogue of the corrected child/source atlases.
The developmental timeline is the focal child's age. The target utterance is the caretaker utterance, fit independently from the child real/random/ngram/LSTM source reports.

## Implementation

- Estimator: linear ordinary least squares regression.
- Library: `statsmodels.formula.api.ols`.
- Uncertainty: child/dyad-cluster robust standard errors.
- Outcome: caretaker `sum_bits`, the total information for the caretaker target utterance.
- Context: k0/k1/k2/k3 are fit independently; k0 correctly skips models that require preceding context effort or question type.
- Fixed slices: models are fit on all eligible rows; fixed effort values only define plotted prediction lines.

## Start Here

Each section below is one caretaker model. It starts with the model question, formula, regression type, library, uncertainty structure, and then the plots. Long tables are kept out of the report body and saved as CSV artifacts.

## Model Atlas

### CM1: Pooled age and caretaker effort

**Question.** Does child age predict caretaker utterance information after controlling caretaker effort?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c + caretaker_effort_c`

**Fitted formula.** `sum_bits ~ age_c + effort_c`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 20/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.712.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K0 plots

**Morphemes**

![k0 CM1 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 CM1 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 CM1 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 CM1 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 CM1 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm1_nb_words_fixed_effort_atlas.png)

#### K1 plots

**Morphemes**

![k1 CM1 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM1 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM1 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM1 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM1 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm1_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM1 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM1 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM1 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM1 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM1 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm1_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM1 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM1 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM1 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM1 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM1 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm1_nb_words_fixed_effort_atlas.png)

### CM2: Age and caretaker effort with dyad identity

**Question.** Does the child-age effect remain after dyad/family identity is controlled?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c + caretaker_effort_c + C(dyad_child_id)`

**Fitted formula.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 20/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.714.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K0 plots

**Morphemes**

![k0 CM2 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 CM2 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 CM2 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 CM2 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 CM2 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm2_nb_words_fixed_effort_atlas.png)

#### K1 plots

**Morphemes**

![k1 CM2 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM2 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM2 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM2 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM2 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm2_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM2 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM2 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM2 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM2 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM2 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm2_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM2 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM2 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM2 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM2 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM2 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_words_fixed_effort_atlas.png)

### CM3: Age by caretaker effort

**Question.** Does the caretaker effort-information relation change over the child's development?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id)`

**Fitted formula.** `sum_bits ~ age_c * effort_c + C(child_id)`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 20/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.714.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K0 plots

**Morphemes**

![k0 CM3 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k0 CM3 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k0 CM3 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k0 CM3 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k0 CM3 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k0_cm3_nb_words_fixed_effort_atlas.png)

#### K1 plots

**Morphemes**

![k1 CM3 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM3 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM3 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM3 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM3 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm3_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM3 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM3 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM3 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM3 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM3 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm3_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM3 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM3 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM3 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM3 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM3 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_words_fixed_effort_atlas.png)

### CM4a: Preceding-context effort added

**Question.** Does preceding conversational-context effort explain additional caretaker information?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) + preceding_context_caretaker_effort_c`

**Fitted formula.** `sum_bits ~ age_c * effort_c + C(child_id) + preceding_context_effort_c`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 15/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.692.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K1 plots

**Morphemes**

![k1 CM4a Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4a_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM4a Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4a_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM4a Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4a_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM4a Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4a_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM4a Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4a_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM4a Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4a_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM4a Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4a_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM4a Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4a_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM4a Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4a_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM4a Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4a_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM4a Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4a_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM4a Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4a_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM4a Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4a_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM4a Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4a_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM4a Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4a_nb_words_fixed_effort_atlas.png)

### CM4c: Question type added

**Question.** Does broad preceding-context question type explain additional caretaker information?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) + C(question_type)`

**Fitted formula.** `sum_bits ~ age_c * effort_c + C(child_id) + C(question_type)`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 15/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.687.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K1 plots

**Morphemes**

![k1 CM4c Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4c_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM4c Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4c_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM4c Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4c_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM4c Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4c_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM4c Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm4c_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM4c Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4c_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM4c Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4c_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM4c Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4c_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM4c Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4c_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM4c Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm4c_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM4c Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4c_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM4c Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4c_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM4c Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4c_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM4c Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4c_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM4c Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm4c_nb_words_fixed_effort_atlas.png)

### CM5: Context effort and question type

**Question.** Do context effort and question type matter after age, caretaker effort, and dyad identity?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) + preceding_context_caretaker_effort_c + C(question_type)`

**Fitted formula.** `sum_bits ~ age_c * effort_c + C(child_id) + preceding_context_effort_c + C(question_type)`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 15/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.693.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K1 plots

**Morphemes**

![k1 CM5 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm5_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM5 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm5_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM5 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm5_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM5 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm5_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM5 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm5_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM5 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm5_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM5 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm5_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM5 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm5_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM5 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm5_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM5 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm5_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM5 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm5_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM5 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm5_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM5 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm5_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM5 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm5_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM5 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm5_nb_words_fixed_effort_atlas.png)

### CM6: Context-effort interactions

**Question.** Does context-effort sensitivity change with child age or caretaker target effort?

**Conceptual formula.** `caretaker_sum_bits ~ child_age_c * caretaker_effort_c + C(dyad_child_id) + preceding_context_caretaker_effort_c + C(question_type) + child_age_c:preceding_context_caretaker_effort_c + caretaker_effort_c:preceding_context_caretaker_effort_c`

**Fitted formula.** `sum_bits ~ age_c * effort_c + C(child_id) + preceding_context_effort_c + C(question_type) + age_c:preceding_context_effort_c + effort_c:preceding_context_effort_c`

**Estimator.** Linear regression: ordinary least squares via `statsmodels.formula.api.ols`.

**Uncertainty.** Child/dyad-cluster robust standard errors.

**Outcome.** Caretaker `sum_bits`, the total information in the caretaker target utterance.

**Coverage.** 15/20 fitted combinations across K0, K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 668,903-668,903. Mean descriptive R2: 0.699.

**Plots below.** Each plot uses this same caretaker model family for one effort unit, then draws prediction lines at fixed observed caretaker-effort values.

#### K1 plots

**Morphemes**

![k1 CM6 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm6_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 CM6 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm6_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 CM6 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm6_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 CM6 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm6_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 CM6 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k1_cm6_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 CM6 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm6_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 CM6 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm6_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 CM6 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm6_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 CM6 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm6_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 CM6 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k2_cm6_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 CM6 Morphemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 CM6 Phonemes](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 CM6 Syllables: CMU/pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 CM6 Syllables: pkg](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 CM6 Words](../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm6_nb_words_fixed_effort_atlas.png)

## Skipped Or Failed Fits

Some requested model/context/effort combinations did not fit. This is expected for k0 models that require preceding context. Exact rows are saved in `caretaker_model_summary.csv`.

## Saved Tables And Artifacts

The long coefficient tables, fixed-effort prediction grids, slice definitions, and slope summaries are saved as CSV artifacts. They are intentionally not printed in this HTML report because the consultation layer is the model cards and plots above.

```text
results/route1_caretaker_atlas/full_fit/caretaker_model_summary.csv
results/route1_caretaker_atlas/full_fit/caretaker_coefficient_long.csv
results/route1_caretaker_atlas/full_fit/caretaker_fixed_effort_bin_definitions.csv
results/route1_caretaker_atlas/full_fit/caretaker_fixed_effort_predictions.csv.gz
results/route1_caretaker_atlas/full_fit/caretaker_fixed_slice_slopes.csv
results/route1_caretaker_atlas/full_fit/caretaker_figure_manifest.csv
figs/route1_caretaker_corrected_fixed_effort_atlas/
```