# Route 1 Corrected Fixed-Effort Atlas v2: lstm_additive_k4_same_length

This report rebuilds the old plot-heavy M1-M6 atlas style for one target source, with the corrected extended M1-M15 model ladder.
The model ladder is fit independently for this source, not pooled across real/generated conditions.

## Implementation

- Estimator: linear ordinary least squares regression.
- Library: `statsmodels.formula.api.ols` through the corrected Route 1 atlas code.
- Uncertainty: child-cluster robust standard errors for the primary child-adjusted models.
- Outcome: `sum_bits`, the total utterance information for this target source.
- Fixed slices: the model is fit on all eligible rows; fixed effort values only define plotted prediction lines.
- Context predictors in prediction slices are held at their fitted-data means; question type is held at its modal level.

## Start Here

Each section below is one model. It starts with the model question, formula, regression type, library, uncertainty structure, and then the plots. Long tables are kept out of the report body and saved as CSV artifacts.

## Model Atlas

### M1: Pooled age and effort

**Question.** Does age predict target information after controlling target effort, pooling children?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age + effort`

**Statsmodels formula.** `sum_bits ~ age_c + effort_c`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.791.

**Plain read.** Pooled age and effort baseline. Useful as a sanity check, but not sufficient for developmental interpretation because child identity is not controlled.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M1 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M1 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M1 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M1 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M1 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m1_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M1 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M1 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M1 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M1 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M1 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m1_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M1 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m1_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M1 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m1_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M1 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M1 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m1_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M1 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m1_nb_words_fixed_effort_atlas.png)

### M2: Age and effort with child identity

**Question.** Does the age effect remain after child identity is controlled?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age + effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c + effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.792.

**Plain read.** First child-adjusted model. This is the compact test of whether the age effect remains after target effort and child identity are controlled.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M2 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M2 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M2 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M2 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M2 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m2_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M2 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M2 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M2 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M2 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M2 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m2_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M2 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M2 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M2 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M2 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M2 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_words_fixed_effort_atlas.png)

### M3: Age by effort

**Question.** Does the effort-information relation change with age?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.793.

**Plain read.** Age-by-effort model. The fixed-effort plots are central here because they show whether the age trend depends on utterance size.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M3 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M3 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M3 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M3 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M3 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m3_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M3 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M3 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M3 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M3 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M3 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m3_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M3 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M3 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M3 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M3 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M3 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_words_fixed_effort_atlas.png)

### M4a: Parent-context effort added

**Question.** Does preceding caretaker effort explain additional target information?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.793.

**Plain read.** Adds preceding caretaker-context effort. This checks whether local context amount explains additional target information.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M4a Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4a_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M4a Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4a_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M4a Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4a_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M4a Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4a_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M4a Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4a_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M4a Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4a_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M4a Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4a_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M4a Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4a_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M4a Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4a_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M4a Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4a_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M4a Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4a_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M4a Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4a_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M4a Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4a_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M4a Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4a_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M4a Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4a_nb_words_fixed_effort_atlas.png)

### M4b: Context entropy added

**Question.** Does context entropy explain additional target information?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + context_entropy + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Adds context entropy. This checks whether the age pattern survives the available next-token context-entropy control.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M4b Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4b_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M4b Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4b_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M4b Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4b_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M4b Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4b_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M4b Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4b_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M4b Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4b_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M4b Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4b_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M4b Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4b_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M4b Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4b_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M4b Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4b_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M4b Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4b_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M4b Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4b_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M4b Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4b_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M4b Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4b_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M4b Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4b_nb_words_fixed_effort_atlas.png)

### M4c: Question type added

**Question.** Does preceding caretaker question type explain additional target information?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + C(question_type) + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + C(question_type) + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.795.

**Plain read.** Adds broad question type. This checks whether local interrogative structure explains additional target information.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M4c Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4c_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M4c Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4c_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M4c Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4c_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M4c Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4c_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M4c Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m4c_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M4c Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4c_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M4c Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4c_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M4c Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4c_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M4c Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4c_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M4c Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m4c_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M4c Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M4c Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M4c Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M4c Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M4c Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

### M5: All context controls

**Question.** Do parent effort, context entropy, and question type each matter after age, target effort, and child identity?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Combines context effort, context entropy, and question type with the age-by-effort child-adjusted model.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M5 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m5_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M5 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m5_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M5 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m5_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M5 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m5_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M5 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m5_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M5 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m5_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M5 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m5_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M5 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m5_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M5 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m5_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M5 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m5_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M5 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m5_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M5 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m5_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M5 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m5_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M5 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m5_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M5 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m5_nb_words_fixed_effort_atlas.png)

### M6: Context entropy interactions

**Question.** Does context-entropy sensitivity change with age or target effort?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:context_entropy + effort:context_entropy + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + effort_c:context_entropy_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Interaction stress test for age/effort with context entropy. Useful for robustness, not a first-pass headline by itself.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M6 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m6_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M6 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m6_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M6 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m6_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M6 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m6_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M6 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m6_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M6 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m6_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M6 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m6_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M6 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m6_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M6 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m6_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M6 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m6_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M6 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m6_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M6 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m6_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M6 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m6_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M6 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m6_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M6 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m6_nb_words_fixed_effort_atlas.png)

### M7: Nonlinear age

**Question.** Does a curved age trajectory explain target information beyond linear age and effort?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age + effort + I(age ** 2) + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c + effort_c + I(age_c ** 2) + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.792.

**Plain read.** Nonlinear age model. Checks whether a curved developmental trajectory fits better than a straight age slope.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M7 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m7_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M7 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m7_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M7 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m7_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M7 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m7_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M7 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m7_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M7 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m7_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M7 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m7_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M7 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m7_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M7 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m7_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M7 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m7_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M7 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m7_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M7 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m7_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M7 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m7_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M7 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m7_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M7 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m7_nb_words_fixed_effort_atlas.png)

### M8: Nonlinear age by effort

**Question.** Does the effort-information relation change along a curved age trajectory?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + I(age ** 2) + I(age ** 2):effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + I(age_c ** 2) + I(age_c ** 2):effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.794.

**Plain read.** Nonlinear age-by-effort model. Checks whether curved developmental change depends on target utterance effort.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M8 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m8_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M8 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m8_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M8 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m8_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M8 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m8_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M8 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m8_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M8 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m8_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M8 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m8_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M8 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m8_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M8 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m8_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M8 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m8_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M8 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m8_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M8 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m8_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M8 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m8_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M8 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m8_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M8 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m8_nb_words_fixed_effort_atlas.png)

### M9: Categorical age-bin trajectory

**Question.** Do age-bin differences remain after target effort and child identity are controlled?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ C(age_bin) + effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ C(age_bin) + effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.793.

**Plain read.** Categorical age-bin trajectory. Checks developmental shape without forcing one continuous age slope.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M9 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m9_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M9 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m9_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M9 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m9_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M9 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m9_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M9 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m9_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M9 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m9_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M9 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m9_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M9 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m9_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M9 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m9_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M9 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m9_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M9 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m9_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M9 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m9_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M9 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m9_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M9 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m9_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M9 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m9_nb_words_fixed_effort_atlas.png)

### M10: Age-bin by effort

**Question.** Does the effort-information relation differ across developmental age bins?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ C(age_bin) * effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ C(age_bin) * effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 446,508-446,508. Mean descriptive R2: 0.794.

**Plain read.** Age-bin-by-effort model. Checks whether age-bin differences vary across target effort.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M10 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m10_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M10 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m10_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M10 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m10_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M10 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m10_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M10 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m10_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M10 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m10_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M10 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m10_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M10 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m10_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M10 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m10_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M10 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m10_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M10 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m10_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M10 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m10_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M10 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m10_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M10 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m10_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M10 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m10_nb_words_fixed_effort_atlas.png)

### M11: Age by parent-context effort

**Question.** Does preceding caretaker effort matter differently across development?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:parent_context_effort + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:parent_context_effort_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Age-by-parent-context-effort model. Tests whether the age pattern changes with preceding context effort.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M11 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m11_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M11 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m11_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M11 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m11_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M11 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m11_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M11 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m11_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M11 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m11_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M11 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m11_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M11 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m11_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M11 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m11_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M11 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m11_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M11 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m11_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M11 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m11_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M11 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m11_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M11 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m11_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M11 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m11_nb_words_fixed_effort_atlas.png)

### M12: Age by question type

**Question.** Does the developmental trajectory differ by broad preceding caretaker question type?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:C(question_type) + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:C(question_type) + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Age-by-question-type model. Tests whether the age pattern differs across broad preceding-context question types.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M12 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m12_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M12 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m12_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M12 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m12_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M12 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m12_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M12 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m12_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M12 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m12_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M12 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m12_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M12 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m12_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M12 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m12_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M12 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m12_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M12 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m12_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M12 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m12_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M12 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m12_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M12 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m12_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M12 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m12_nb_words_fixed_effort_atlas.png)

### M13: Context entropy by question type

**Question.** Does context entropy matter differently after different broad caretaker question types?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + context_entropy:C(question_type) + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + context_entropy_c:C(question_type) + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Context-entropy-by-question-type model. Tests whether context entropy behaves differently by question type.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M13 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m13_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M13 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m13_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M13 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m13_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M13 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m13_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M13 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m13_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M13 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m13_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M13 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m13_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M13 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m13_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M13 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m13_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M13 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m13_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M13 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m13_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M13 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m13_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M13 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m13_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M13 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m13_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M13 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m13_nb_words_fixed_effort_atlas.png)

### M14: Parent effort by context entropy

**Question.** Do context entropy and preceding caretaker effort jointly predict target information?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + parent_context_effort:context_entropy + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + parent_context_effort_c:context_entropy_c + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Parent-context-effort-by-context-entropy model. Tests whether context amount and entropy carry separable information.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M14 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m14_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M14 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m14_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M14 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m14_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M14 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m14_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M14 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m14_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M14 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m14_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M14 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m14_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M14 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m14_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M14 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m14_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M14 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m14_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M14 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m14_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M14 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m14_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M14 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m14_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M14 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m14_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M14 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m14_nb_words_fixed_effort_atlas.png)

### M15: Expanded context interaction stress test

**Question.** Do the main context controls alter the age-effort trajectory under a larger interaction stress test?

**Regression type.** Linear regression / ordinary least squares.

**Library.** `statsmodels.formula.api.ols`; primary uncertainty uses child-cluster robust standard errors where available.

**Outcome.** `sum_bits`: total information of the target utterance for this source.

**Formula.** `sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:context_entropy + effort:context_entropy + age:parent_context_effort + effort:parent_context_effort + context_entropy:C(question_type) + C(child_id)`

**Statsmodels formula.** `sum_bits ~ age_c * effort_c + parent_context_effort_c + context_entropy_c + C(question_type) + age_c:context_entropy_c + effort_c:context_entropy_c + age_c:parent_context_effort_c + effort_c:parent_context_effort_c + context_entropy_c:C(question_type) + C(child_id)`

**Core controls.** `age_c`: child age in months, centered; `effort_c`: the centered effort measure named under each plot.

**Coverage.** 15/15 fitted combinations across K1, K2, K3; effort axes: Morphemes, Phonemes, Syllables: CMU/pkg, Syllables: pkg, Words. Observations per fitted combination: 441,413-442,111. Mean descriptive R2: 0.796.

**Plain read.** Expanded context interaction stress test. Checks the richest corrected interaction set in the current ladder.

**Plots below.** Each plot uses this same model family for one effort unit, then draws prediction lines at fixed observed effort values.

#### K1 plots

**Morphemes**

![k1 M15 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m15_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k1 M15 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m15_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k1 M15 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m15_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k1 M15 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m15_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k1 M15 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k1_m15_nb_words_fixed_effort_atlas.png)

#### K2 plots

**Morphemes**

![k2 M15 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m15_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k2 M15 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m15_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k2 M15 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m15_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k2 M15 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m15_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k2 M15 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k2_m15_nb_words_fixed_effort_atlas.png)

#### K3 plots

**Morphemes**

![k3 M15 Morphemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m15_nb_morphemes_fixed_effort_atlas.png)

**Phonemes**

![k3 M15 Phonemes](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m15_nb_phonemes_fixed_effort_atlas.png)

**Syllables: CMU/pkg**

![k3 M15 Syllables: CMU/pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m15_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)

**Syllables: pkg**

![k3 M15 Syllables: pkg](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m15_nb_syllables_pkg_fixed_effort_atlas.png)

**Words**

![k3 M15 Words](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m15_nb_words_fixed_effort_atlas.png)

## Model-Version And Estimator Sensitivity

The primary fixed-effort atlas above is the corrected source-specific M1-M15 ladder. This section records the saved model-version layer: child-structure variants, estimator variants, and formula versions that are available on disk.

### Corrected Child-Structure / Estimator Versions

_No corrected version-sensitivity rows are currently saved for `lstm_additive_k4_same_length` in `results/route1_corrected_baseline_atlas/full_child_structure_sensitivity/source_specific_model_summary.csv`._

## Saved Tables And Artifacts

The long coefficient tables, fixed-effort prediction grids, slice definitions, and slope summaries are saved as CSV artifacts. They are intentionally not printed in this HTML report because the consultation layer is the model cards and plots above.

## Saved Outputs

```text
results/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/model_summary.csv
results/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/coefficient_long.csv
results/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/fixed_effort_predictions.csv.gz
results/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/fixed_slice_slopes.csv
results/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/figure_manifest.csv
figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/
```