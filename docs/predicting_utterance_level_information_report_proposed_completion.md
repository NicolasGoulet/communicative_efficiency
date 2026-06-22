# Predicting Informational Content at the Utterance Level: Proposed Completion Draft

Proposed completion draft, June 2026

This side draft starts from the current supervisor-facing report and adds candidate completion text. The current supervisor-facing report files were not modified.

## Introduction

This document describes an utterance-level analysis of communicative efficiency
in child language. The broad goal is to understand how children learn to package
information in speech while managing the effort required to produce it. 

In this framing, communicative efficiency has two parts. The first is
**informativeness**: how much information an utterance conveys in context. The
second is **effort**: how much linguistic material is produced to convey that
information. A developmental increase in total surprisal is not meaningful on
its own if it simply reflects that older children produce longer utterances.
For this reason, the analyses must compare informational content while
controlling for utterance length and other effort-related properties.

The analyses focus on three related quantities:

- **total information per utterance**, measured with `sum_bits`;
- **information per unit of production effort**, where `sum_bits` is divided by the number of words, morphemes, phonemes or syllables in an utterance;
- **tokenizer-level sensitivity**, measured with `mean_bits_per_token`.

A follow-up analysis asks a complementary question: whether contextual
uncertainty predicts the length or effort of the child's response.

## Current Primary Result: Model 2

The clearest current model is Model 2:

```text
total utterance information ~ age + production effort + child identity
```

The outcome is total utterance information in bits. Age is measured in months.
Production effort is tested five ways: words, surface morphemes, two syllable
estimates, and phonemes. Child identity is included so that each child has
their own baseline level of predicted information.

This model uses 446,985 real child utterances from 21 children, scored with the
preceding three caretaker utterances as context. Across all five effort
controls, the age coefficient is negative. In plain language: for the same
amount of linguistic material, and within the child-adjusted comparison,
older children's utterances are predicted to contain less Mistral surprisal.

That should not be interpreted as children "communicating less." A safer
interpretation is that older children produce utterances that are more
predictable in their conversational context after production effort and stable
between-child differences are controlled. This is consistent with development
toward more conventional, contextually recoverable, or adult-like language use.

## Analysis Sample

The initial analysis uses three longitudinal naturalistic caregiver-child
corpora from CHILDES: Providence, Brown, and Manchester. Together, these corpora
provide dense developmental trajectories for 21 children, with both child
speech and caretaker speech scored under the same Mistral-based surprisal
framework.

The first comparisons focus on real child utterances, caretaker utterances, and
matched-length baseline utterances. These comparisons are meant to tell us
whether children's utterances are merely becoming longer over time, or whether
they are changing in how efficiently they use linguistic material to carry
information.

## Developmental Age Bins

For descriptive plots and age-binned summaries, the first age bin combines the
early months:

- `006-023` months

This is partly due to having very few utterances in these 6-month bins, but it
is also consistent with well-established developmental changes in utterance
length: around the second year, children increasingly move from single-word
productions to multiword utterances, and mean length of utterance rises over
early childhood.

The following bins are six-month intervals:

- `024-029`
- `030-035`
- `036-041`
- `042-047`
- `048-053`
- `054-059`
- `060-065`

This binning scheme gives enough support to the youngest period while retaining
six-month developmental resolution afterward. All scored child and caretaker
utterances in the current analysis sample are assigned to one of these bins.

## Utterance Coverage by Age

The current analysis sample contains 446,985 child utterances and 668,903
caretaker utterances. The table below shows their distribution across
developmental age bins.

| Age bin | Caretaker utterances | Child utterances |
| ------- | -------------------- | ---------------- |
| 006-023 | 150,345              | 62,816           |
| 024-029 | 249,127              | 162,210          |
| 030-035 | 199,242              | 142,447          |
| 036-041 | 37,663               | 37,683           |
| 042-047 | 18,374               | 16,345           |
| 048-053 | 7,910                | 12,909           |
| 054-059 | 5,226                | 10,033           |
| 060-065 | 1,016                | 2,542            |

![Total child and caretaker utterances by developmental age bin](../figs/utterance_information/total_utterances_by_age_bin.png)

Most utterances fall between 6 and 35 months, especially because Manchester is
dense in the early-to-middle toddler range. The later bins remain useful, but
they contain fewer observations, particularly for caretakers in the oldest bin.
This should be kept in mind when interpreting age-binned descriptive summaries.

The contribution of each corpus also changes across developmental time:

![Corpus contribution to utterance counts by age bin](../figs/utterance_information/utterances_by_age_bin_and_corpus.png)

This uneven corpus contribution is expected for longitudinal CHILDES data. 

## Corpora and Children

The current Providence/Brown/Manchester analysis set contains 21 children.

| Corpus     | Children | Child utterances | Caretaker utterances | Child age range | Transcript files |
| ---------- | -------- | ---------------- | -------------------- | --------------- | ---------------- |
| Brown      | 3        | 92,555           | 64,206               | 18.0-62.4       | 214              |
| Manchester | 12       | 232,614          | 342,246              | 20.7-36.3       | 408              |
| Providence | 6        | 121,816          | 262,451              | 11.1-48.1       | 361              |
| Total      | 21       | 446,985          | 668,903              | 11.1-62.4       | 983              |

### Brown

Brown contributes three children. Eve covers the earliest Brown range, from
about 18 to 27 months. Adam and Sarah contribute longer developmental
trajectories extending into the 60-month range. Brown is therefore especially
important for the later bins.

### Manchester

Manchester contributes 12 children and the largest number of child utterances
in the current analysis set. Its developmental window is narrower, roughly 21
to 36 months, but it is dense within that period. Manchester is therefore a
major contributor to the early and middle bins.

### Providence

Providence contributes six children, with the earliest scored rows beginning
around 11 months. Some Providence children extend into the late 40-month range.
This corpus is important for the earliest developmental bin and for linking the
infant/toddler range to later preschool ages.

![Developmental coverage of individual children](../figs/utterance_information/child_developmental_coverage.png)

This child-level structure is central to the modeling strategy. The same child
contributes many utterances over time, so rows should not be treated as
independent observations from unrelated speakers. At minimum, child identity
must be controlled. Later models may also aggregate by child, age bin, context
window, and utterance-length band to make the repeated-observation structure
more explicit.

## Complexity / Effort

The first part of the analysis concerns the amount of linguistic material used
to produce an utterance. In this document, this is treated as production
effort. The central idea is simple: an utterance with more words, more
morphemes, more syllables, or more phonemes generally requires more material to
produce than a shorter utterance.

The primary effort measure is the number of lexical words in the cleaned target
utterance. This measure is easy to interpret and aligns directly with the
matched-length baseline design, since the random, n-gram, and same-length LSTM
baselines are generated with the same number of words as the corresponding
child utterance.

Word count is not the only possible measure of effort. Two utterances can have
the same number of words but differ in morphological or phonological
complexity. The current effort measures are computed from the cleaned target
string submitted for surprisal scoring:

- **Words**: lexical orthographic tokens counted with a local regex tokenizer;
  punctuation is excluded.
- **Morphemes**: `auto_morphemes_surface`, a surface-aligned heuristic computed
  from the cleaned utterance, not from CHILDES `%mor` tiers.
- **Syllables**: two retained estimates, since after manual validation no clear winner was identified, `auto_syllables_cmu_or_pkg` and `auto_syllables_pkg`.
  The first uses CMUdict ARPABET vowel nuclei when available and the `syllables` package for OOV forms, while the second uses the `syllables` package throughout.
- **Phonemes**: `auto_phonemes_cmu_or_g2p`; CMUdict ARPABET phone counts are
  used for dictionary-covered words, with `g2p-en` applied to OOV forms as
  written.

These measures are also important because the generated baselines discussed below are
matched to children in word count, but not necessarily in morphemes, syllables,
or phonemes. A baseline may therefore use the same number of words while still
requiring a different amount of phonological or morphological effort.

## Information

The second part of the analysis concerns informational content. Information is
measured with Mistral surprisal in bits. Higher surprisal means that the model
found the produced utterance less predictable in context, i.e. it contained *more information*; lower surprisal means
that the utterance was more predictable, i.e. it contained *less information*.

The main information measure is total utterance surprisal, `sum_bits`. This is
the total amount of information assigned to the produced target utterance under
the model. Because longer utterances naturally tend to accumulate more bits and also tend to make individual tokens less surprising,
total information must be interpreted alongside effort.

The analysis therefore also considers information per unit of effort. The
simplest version is bits per lexical word, but the same logic can be extended
to morphemes, syllables, or phonemes. These ratios ask whether children are
packing more or less information into the linguistic material they produce.

Context is part of the interpretation. The same target utterance can be scored
without preceding context or with one, two, or three previous caretaker
utterances. This lets us ask whether developmental changes in surprisal reflect
the utterance alone, the conversational context, or the relationship between
the two.

Context entropy is also measured in bits, but it captures a different object
from target surprisal. Surprisal measures the information in the utterance that
was actually produced. Context entropy measures the model's uncertainty about
what could come next after the preceding context. This can later be used to ask
whether children produce longer or more informative utterances in contexts that
are themselves more uncertain. It can also be used as a predictor of the informational contents of an utterance. 

## Comparison Baselines

To interpret children’s communicative efficiency, it is useful to compare their utterances to baseline language models. The current baselines are designed to ask: given the same number of words per utterance and access to the same age-binned vocabulary, how do baseline-generated utterances differ from children’s actual utterances in informational content and communicative efficiency?

All these baselines use additive age-bins, where the size of their vocabulary is expanded incrementally with each new age bin.

### Random Baseline

For each age bin, the random baseline samples uniformly from the corresponding additive vocabulary, without using word frequency, local word order, or conversational context.

### N-Gram Baselines

The unigram baseline samples from word frequencies. The bigram and trigram
baselines additionally use local word dependencies. At utterance boundaries,
they use the immediately preceding caretaker speech as context for the first
generated child words, so that the baseline is not completely blind to the
conversation turn it is responding to (this is also done when creating the dictionaries of bigrams and trigrams).

### LSTM Baseline

The LSTM baseline is designed as a stronger comparison than the frequency-based
models while remaining much simpler than a large language model. It uses an
encoder-decoder architecture: the encoder reads a bounded window of preceding
caretaker speech, and the decoder generates a child-like response.

The current LSTM comparison follows the same additive developmental logic as the
n-gram baselines. For each age bin, a different LSTM is trained on the current bin plus
all previous bins, then used to generate utterances only for the target bin.
This keeps the comparison aligned with the developmental information available
to the n-gram baselines.

The LSTM can listen to caretaker language, but it is only allowed to speak using the child-side vocabulary observed in the age-appropriate training data. 

The current LSTM comparison uses same-length generated utterances, so effort
is held constant relative to the real child utterance. A later free-length
variant can ask a different question: whether the model chooses a similar amount
of communicative effort when responding to the same caretaker context.


## Model 2 Details

Model 2 is the main result to interpret at this stage because it controls both
production effort and child identity. The formula is:

```text
sum_bits ~ age + effort + child identity
```

The model is fit separately for each effort measure. This avoids putting words,
morphemes, syllables, and phonemes in the same regression, where they would be
highly correlated measures of the same underlying utterance size.

The displayed version is an ordinary linear regression. The coefficient for age
is in bits per month after effort and child identity are controlled. The
coefficient for effort is the expected increase in total bits for one
additional unit of that effort measure. The uncertainty estimates use
child-clustered robust standard errors to account for repeated utterances from
the same child. SES is not included in this version because systematic SES
metadata are not available for all children in the current sample.

| Effort control | Age effect, bits/month | Age p | Age effect, bits/6 months | Effort effect, bits/unit | Model fit |
| -------------- | ---------------------- | ----- | ------------------------- | ------------------------ | --------- |
| Words | -0.122 | <.001 | -0.735 | 6.367 | R2 = 0.626 |
| Morphemes | -0.136 | <.001 | -0.813 | 5.489 | R2 = 0.613 |
| Syllables: CMU/pkg | -0.063 | 0.018 | -0.380 | 5.236 | R2 = 0.646 |
| Syllables: pkg | -0.048 | 0.049 | -0.291 | 4.831 | R2 = 0.630 |
| Phonemes | -0.065 | 0.013 | -0.389 | 2.084 | R2 = 0.644 |

All five age effects are negative and statistically reliable at conventional
levels. The word and morpheme versions are the most direct to interpret. The
phoneme and syllable versions show that the result is not limited to
orthographic word count.

The effort effects are large and positive, as expected: longer or more complex
utterances carry more total information. The important point is that age still
has a negative association with total information after this effort effect is
controlled.

### Fixed-Effort Predictions

The figures below show the fitted Model 2 age trajectory while holding effort
fixed. Within each figure, the colored lines are exact fixed effort levels and
the black line is the global adjusted trend. Because Model 2 does not include
an age-by-effort interaction, the fixed-effort lines are parallel; the point of
the plots is to show that the downward age trend is present at comparable
utterance sizes.

![Model 2 fixed-effort predictions for word count](../figs/m2_simple_plots/m2_words_fixed_effort_and_global_trend.png)

![Model 2 fixed-effort predictions for morpheme count](../figs/m2_simple_plots/m2_morphemes_fixed_effort_and_global_trend.png)

![Model 2 fixed-effort predictions for CMU/pkg syllable count](../figs/m2_simple_plots/m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png)

![Model 2 fixed-effort predictions for package syllable count](../figs/m2_simple_plots/m2_syllables_pkg_fixed_effort_and_global_trend.png)

![Model 2 fixed-effort predictions for phoneme count](../figs/m2_simple_plots/m2_phonemes_fixed_effort_and_global_trend.png)

### Robustness Checks

The main Model 2 table above is fit at the utterance level with the preceding
three caretaker utterances as context. A complementary robustness analysis uses
the same context window but aggregates the data into child-session-context
units, then tests whether the age effect survives balanced resampling and
age-label scrambling. Because this robustness analysis uses an aggregated
frame, its coefficients are not numerically identical to the utterance-level
coefficients, but the direction of the result is the same.

Balanced age-bin bootstraps keep the estimated age effect negative for all five
effort controls:

| Effort control | Aggregated age effect | Balanced bootstrap 95% range |
| -------------- | --------------------- | ----------------------------- |
| Words | -0.040 | -0.168 to -0.036 |
| Morphemes | -0.043 | -0.178 to -0.029 |
| Syllables: CMU/pkg | -0.029 | -0.143 to -0.004 |
| Syllables: pkg | -0.033 | -0.152 to -0.017 |
| Phonemes | -0.046 | -0.175 to -0.002 |

The same aggregated Model 2 effect was also compared against three scrambled
age controls: grouped age-bin label scrambling, unit-level age scrambling, and
within-child age scrambling. For every effort measure and every scrambling
scheme, the observed age effect fell outside the scrambled null 95% interval.
With 100 scramble replicates, the resulting two-sided permutation value was
at or below 0.050 in each case, and approximately 0.010 in nearly all cases.

![Model 2 balanced and age-scrambled robustness checks](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

### Interpretation

Model 2 supports a conservative claim:

```text
After controlling production effort and child identity, older child utterances
have lower predicted total surprisal than younger child utterances.
```

This is an informativeness result, not yet a full communicative-efficiency
result. It says that the informational content of the produced utterance
changes with age after effort is controlled. It does not yet show whether
children choose longer or shorter utterances because a context is more or less
predictable.

That second question needs a model where effort is the outcome, for example:

```text
production effort ~ age + context uncertainty + child identity
```

The next context-uncertainty measure should ideally be response-level: instead
of measuring uncertainty about only the next token, it should estimate how many
plausible complete child responses the preceding caretaker context allows.

## Proposed Completion v2: Model-Rich Route 1 Synthesis

This section is a proposed replacement for the weaker completion draft. It is intentionally model-rich: it promotes the strongest current analyses, shows what each model family contributes, and keeps the original supervisor-facing report untouched.

The fixed scientific target remains: estimate conditional utterance information at fixed production effort, using repeated child utterances sampled across sessions and ages. The key distinction is that raw total bits can rise with utterance length, while the main developmental claim is about fitted information at the same effort level.

### What Should Be Promoted

I would promote the evidence in this order:

1. **Primary row-level fixed-effort model:** age + child effort + child identity, with child-clustered uncertainty.
2. **Exact-length proof:** exact word-count categories and exact-length age slopes, showing the result is not just MLU.
3. **Context/confound controls:** parent-context effort, context entropy, question type, and richer interactions.
4. **Estimator-family checks:** OLS, GEE, GLM, Gamma/log, and MixedLM variants on session/effort cells.
5. **Age-label robustness:** balanced bootstrap and scrambled-age nulls.
6. **Source specificity:** real children versus random, n-gram, LSTM, and caretaker targets.
7. **Heldout prediction:** actual heldout child regression lines versus PBM-trained predicted lines.

### Main Row-Level Model Ladder

The table below is the current real-child k3/word model ladder. It is more important than a single Model 2 paragraph because it shows the age effect surviving the main confound controls. M1 is the pooled sanity check. M2 adds child identity and becomes the primary simple model. M4a/M4b/M4c add parent effort, context entropy, and question type. M5/M6 combine context controls. M15 is the richest current interaction stress test.

| model | role | R2 | delta R2 vs M2 | age bits/month | age p | effort bits/word | parent effort | context entropy | age x effort |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Pooled age and effort | 0.613 | -0.013 | 3.09e-04 | 0.993 | 6.354 |  |  |  |
| M2 | Age and effort with child identity | 0.626 | 0.000 | -0.122 | <.001 | 6.367 |  |  |  |
| M3 | Age by effort | 0.626 | 1.83e-05 | -0.122 | <.001 | 6.379 |  |  | -0.004 |
| M4a | Parent-context effort added | 0.627 | 7.01e-04 | -0.116 | <.001 | 6.381 | -0.070 |  | -0.004 |
| M4b | Context entropy added | 0.627 | 6.68e-04 | -0.126 | <.001 | 6.374 |  | -0.471 | -0.003 |
| M4c | Question type added | 0.630 | 0.004 | -0.127 | <.001 | 6.378 |  |  | -0.004 |
| M5 | All context controls | 0.627 | 9.47e-04 | -0.122 | <.001 | 6.376 | -0.044 | -0.468 | -0.003 |
| M6 | Context entropy interactions | 0.627 | 9.75e-04 | -0.123 | <.001 | 6.377 | -0.044 | -0.469 | -0.003 |
| M7 | Nonlinear age | 0.626 | 1.87e-04 | -0.144 | 0.002 | 6.377 |  |  |  |
| M8 | Nonlinear age by effort | 0.626 | 3.15e-04 | -0.152 | <.001 | 6.390 |  |  | -0.016 |
| M9 | Categorical age-bin trajectory | 0.626 | 2.59e-04 |  |  | 6.355 |  |  |  |
| M10 | Age-bin by effort | 0.627 | 6.17e-04 |  |  | 6.421 |  |  |  |
| M15 | Expanded context interaction stress test | 0.629 | 0.003 | -0.127 | <.001 | 6.424 | -0.034 | -0.321 | -0.001 |

![Real-child model ladder R2 and delta R2](../figs/route1_candidate_evidence_gallery/real_k3_words_model_ladder_r2_importance.png)

The clean read is that the age coefficient stays negative once child identity and effort are controlled. Question type improves fit among the simple confound controls; context entropy and parent-context effort matter, but they do not erase the developmental fixed-effort result. The richest stress model still estimates a negative age coefficient.

### Fixed-Effort Lines To Show First

These are the plots I should have put into the proposed completion. They are not raw age means. They are fitted lines asking what happens to predicted k3 `sum_bits` when word count is held fixed.

![F01 row-level fixed-effort lines](../figs/route1_child_length_controlled_model_suite/f01_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

![F07 question-type controlled fixed-effort lines](../figs/route1_child_length_controlled_model_suite/f07_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

![F12 full context-interaction stress-test fixed-effort lines](../figs/route1_child_length_controlled_model_suite/f12_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

F01 is the minimal defensible fixed-effort model. F07 adds question type. F12 is a richer context-interaction stress test. The reason to show all three is that the downward fixed-effort story is not limited to the simplest model.

### Exact-Length Proof That This Is Not Just MLU

This is the missing proof layer. The exact-length models replace continuous word count with exact word-count categories. F18 and F20 absorb exact length baselines. F19 and F21 allow separate age slopes inside exact word counts. The well-supported short and middle lengths remain mostly downward.

| formula | min slope/6mo | max slope/6mo | downward lines | upward lengths |
| --- | --- | --- | --- | --- |
| F18: Exact-length fixed effects | -0.758 | -0.758 | 12/12 | none |
| F19: Exact-length age slopes | -1.043 | 0.918 | 9/12 | 10, 11, 12 |
| F20: Exact-length fixed effects with context controls | -0.763 | -0.763 | 12/12 | none |
| F21: Exact-length age slopes with context controls | -1.057 | 1.199 | 8/12 | 8, 10, 11, 12 |

![Exact-length age-slope proof plot](../figs/route1_child_length_controlled_model_suite/mlu_proof_exact_length_age_slopes.png)

![F19 exact-length age slopes](../figs/route1_child_length_controlled_model_suite/f19_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

![F21 exact-length age slopes with context controls](../figs/route1_child_length_controlled_model_suite/f21_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png)

This is where the report can answer the MLU objection directly: even after exact word-count categories are absorbed, the developmental trend is mostly downward. The upward lines are concentrated at sparse longer lengths, so they should be discussed as support-limited rather than promoted as the main signal.

### Full Length-Controlled Model Suite

The side draft should show that this is not one cherry-picked model. The length-controlled suite fits 21 formulas with row-level and aggregate/repeated-measures estimators. The row-level fixed-effect models all fit 446,985 utterances; aggregate models use session/effort cells.

| formula | tier | row R2 | agg GEE R2 | mixed age R2 | row slope directions |
| --- | --- | --- | --- | --- | --- |
| F01: Age at fixed effort | core | 0.626 | 0.774 | 0.775 | 12 down / 12 |
| F02: Age by effort | core | 0.626 | 0.774 | 0.775 | 12 down / 12 |
| F03: Parent effort control | core | 0.627 | 0.778 | 0.780 | 12 down / 12 |
| F04: Age by parent effort | core | 0.627 | 0.778 | 0.780 | 12 down / 12 |
| F05: Effort by parent effort | core | 0.628 | 0.778 | 0.780 | 12 down / 12 |
| F06: Parent interaction stress test | core | 0.628 | 0.779 | 0.780 | 12 down / 12 |
| F07: Question type control | core | 0.630 | 0.781 | 0.783 | 12 down / 12 |
| F08: Context entropy control | core | 0.627 | 0.781 | 0.782 | 12 down / 12 |
| F09: All context controls | core | 0.627 | 0.781 | 0.783 | 12 down / 12 |
| F10: All context controls with age by effort | core | 0.627 | 0.781 | 0.783 | 12 down / 12 |
| F11: Entropy interactions | extended | 0.627 | 0.781 | 0.783 | 12 down / 12 |
| F12: Full context interaction stress test | extended | 0.629 | 0.781 | 0.783 | 12 down / 12 |
| F13: Question interactions | extended | 0.627 | 0.782 | 0.783 | 12 down / 12 |
| F14: Curved age trajectory | extended | 0.626 | 0.774 | 0.775 | 12 down / 12 |
| F15: Curved age by effort | extended | 0.626 | 0.774 | 0.775 | 12 down / 12 |
| F16: Age-bin trajectory | extended | 0.626 | 0.775 | 0.776 | 12 down / 12 |
| F17: Age-bin by effort | extended | 0.627 | 0.779 | 0.781 | 12 down / 12 |
| F18: Exact-length fixed effects | mlu_proof | 0.635 | 0.803 | 0.805 | 12 down / 12 |
| F19: Exact-length age slopes | mlu_proof | 0.636 | 0.806 | 0.808 | 9 down / 12 |
| F20: Exact-length fixed effects with context controls | mlu_proof | 0.637 | 0.812 | 0.814 | 12 down / 12 |
| F21: Exact-length age slopes with context controls | mlu_proof | 0.637 | 0.816 | 0.817 | 8 down / 12 |

![Formula by estimator slope heatmap](../figs/route1_child_length_controlled_model_suite/slope_heatmap_formula_by_estimator.png)

![Variance explained by formula and estimator](../figs/route1_child_length_controlled_model_suite/variance_explained_by_formula_estimator.png)

### Estimator-Family Checks

The estimator-family layer is appendix material, but it is powerful. It shows which conclusions are stable across OLS with child fixed effects, GEE, GLM, Gamma/log, and mixed-effects models. This should be used to defend the analysis if a supervisor asks whether ordinary OLS is too fragile for repeated utterance data.

| estimator | frame | fit formulas | median R2 | max R2 | median n |
| --- | --- | --- | --- | --- | --- |
| Row-level OLS with child fixed intercepts and child-clustered SE | row | 21 | 0.627 | 0.637 | 446,985 |
| Session/effort-cell OLS with child fixed intercepts and child-clustered SE | aggregate | 21 | 0.781 | 0.816 | 27,583 |
| Session/effort-cell Gaussian GEE grouped by child | aggregate | 21 | 0.781 | 0.816 | 27,583 |
| Session/effort-cell Gamma/log GEE grouped by child | aggregate | 21 | 0.003 | 0.815 | 27,583 |
| Session/effort-cell Gaussian GLM with child fixed intercepts | aggregate | 21 | 0.781 | 0.816 | 27,583 |
| Session/effort-cell Gamma/log GLM with child fixed intercepts | aggregate | 21 | 0.003 | 0.815 | 27,583 |
| Session/effort-cell mixed model with random child intercept | aggregate | 21 | 0.768 | 0.806 | 27,583 |
| Session/effort-cell mixed model with random child age slope | aggregate | 21 | 0.782 | 0.817 | 27,583 |
| Session/effort-cell mixed model with child and session intercepts | aggregate | 21 | 0.795 | 0.828 | 27,583 |

![Aggregate estimator age-effect forest](../figs/route1_best_model_robustness_package/aggregate_estimator_age_effect_forest.png)

![M15 aggregate estimator fixed-effort lines](../figs/route1_best_model_robustness_package/m15_aggregate_estimator_fixed_effort_age_lines.png)

Important caveat: the aggregate estimator screen is not the same estimand as the row-level fixed-effort Atlas. It is a repeated-measures sensitivity screen over session/effort cells. It belongs as robustness, not as the lead result.

### Age Scrambling And Balanced Bootstrap

This is the best defense against the claim that the result is just age-bin composition or child/session imbalance. For the k3/word checks, observed slopes are compared with balanced and scrambled-age nulls.

| model | check | observed age | null 95% | outside null | p |
| --- | --- | --- | --- | --- | --- |
| M2 | Balanced age-bin bootstrap | -0.040 | -0.168 to -0.036 | no |  |
| M2 | Grouped age-bin label scramble | -0.040 | -0.025 to 0.028 | yes | 0.010 |
| M2 | Unit-level age scramble | -0.040 | -0.013 to 0.013 | yes | 0.010 |
| M2 | Within-child age scramble | -0.040 | -0.020 to 0.018 | yes | 0.010 |
| M3 | Balanced age-bin bootstrap | -0.050 | -0.186 to -0.022 | no |  |
| M3 | Grouped age-bin label scramble | -0.050 | -0.025 to 0.027 | yes | 0.010 |
| M3 | Unit-level age scramble | -0.050 | -0.010 to 0.012 | yes | 0.010 |
| M3 | Within-child age scramble | -0.050 | -0.020 to 0.014 | yes | 0.010 |
| M4 | Balanced age-bin bootstrap | -0.038 | -0.186 to 0.028 | no |  |
| M4 | Grouped age-bin label scramble | -0.038 | -0.032 to 0.037 | yes | 0.020 |
| M4 | Unit-level age scramble | -0.038 | -0.010 to 0.010 | yes | 0.010 |
| M4 | Within-child age scramble | -0.038 | -0.020 to 0.025 | yes | 0.010 |
| M5 | Balanced age-bin bootstrap | -0.033 | -0.181 to 0.022 | no |  |
| M5 | Grouped age-bin label scramble | -0.033 | -0.032 to 0.030 | yes | 0.059 |
| M5 | Unit-level age scramble | -0.033 | -0.014 to 0.013 | yes | 0.010 |
| M5 | Within-child age scramble | -0.033 | -0.013 to 0.026 | yes | 0.010 |
| M6 | Balanced age-bin bootstrap | -0.058 | -0.113 to 0.020 | no |  |
| M6 | Grouped age-bin label scramble | -0.058 | -0.044 to 0.033 | yes | 0.030 |
| M6 | Unit-level age scramble | -0.058 | -0.012 to 0.012 | yes | 0.010 |
| M6 | Within-child age scramble | -0.058 | -0.018 to 0.022 | yes | 0.010 |

![M2 balanced and age-scrambled robustness](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

![M6 balanced and age-scrambled robustness](../figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png)

![Age-scrambling robustness heatmap](../figs/age_scrambling_robustness/robustness_outside_null_heatmap.png)

### Source Specificity: Real Children Versus Baselines And Caretakers

The source-specific layer answers whether the real-child line is a property of real child speech or a mechanical artifact of the scoring pipeline. Random goes in the opposite direction. N-grams and LSTMs are closer but flatter. Caretakers also differ from the child trajectory.

| comparison source | real slope | source slope | source - real | source downward lines |
| --- | --- | --- | --- | --- |
| Random | -0.735 | 1.068 | 1.803 | 0/12 |
| Unigram | -0.735 | -0.125 | 0.610 | 12/12 |
| Bigram | -0.735 | -0.134 | 0.601 | 12/12 |
| Trigram | -0.735 | -0.092 | 0.643 | 12/12 |
| LSTM k3 | -0.735 | -0.279 | 0.456 | 12/12 |
| LSTM k4 | -0.735 | -0.351 | 0.384 | 12/12 |
| LSTM k5 | -0.735 | -0.363 | 0.372 | 12/12 |
| Caretaker | -0.735 | 0.172 | 0.907 | 0/12 |

![M4c source comparison slopes](../figs/route1_candidate_evidence_gallery/source_comparison_m4c_k3_words_slopes.png)

The visual evidence should be shown source by source. For each comparison, the first panel contrasts no context (`k0`) with caretaker context (`k3`), the second panel plots the context gain through age, the third focuses only on the with-context condition, and the regression panels show the fixed-word-count model comparison.

#### Real vs Random

![Real vs Random k0 versus k3 age means](../figs/route1_real_vs_controls_context_report/random_k0_vs_k3_age_means.png)

![Real vs Random context gain through age](../figs/route1_real_vs_controls_context_report/random_context_gain_by_age.png)

![Real vs Random with-context k3 focus](../figs/route1_real_vs_controls_context_report/random_k3_with_context_focus.png)

![Real vs Random fixed-word regression lines](../figs/route1_real_vs_controls_context_report/random_m2_k3_fixed_word_regression_lines.png)

![Real vs Random fixed-word source-minus-real regression gaps](../figs/route1_real_vs_controls_context_report/random_m2_k3_fixed_word_regression_gaps.png)

![Real vs Random model slope differences](../figs/route1_real_vs_controls_context_report/random_k3_word_model_slope_differences.png)

#### Real vs Unigram

![Real vs Unigram k0 versus k3 age means](../figs/route1_real_vs_controls_context_report/unigram_k0_vs_k3_age_means.png)

![Real vs Unigram context gain through age](../figs/route1_real_vs_controls_context_report/unigram_context_gain_by_age.png)

![Real vs Unigram with-context k3 focus](../figs/route1_real_vs_controls_context_report/unigram_k3_with_context_focus.png)

![Real vs Unigram fixed-word regression lines](../figs/route1_real_vs_controls_context_report/unigram_m2_k3_fixed_word_regression_lines.png)

![Real vs Unigram fixed-word source-minus-real regression gaps](../figs/route1_real_vs_controls_context_report/unigram_m2_k3_fixed_word_regression_gaps.png)

![Real vs Unigram model slope differences](../figs/route1_real_vs_controls_context_report/unigram_k3_word_model_slope_differences.png)

#### Real vs Bigram

![Real vs Bigram k0 versus k3 age means](../figs/route1_real_vs_controls_context_report/bigram_k0_vs_k3_age_means.png)

![Real vs Bigram context gain through age](../figs/route1_real_vs_controls_context_report/bigram_context_gain_by_age.png)

![Real vs Bigram with-context k3 focus](../figs/route1_real_vs_controls_context_report/bigram_k3_with_context_focus.png)

![Real vs Bigram fixed-word regression lines](../figs/route1_real_vs_controls_context_report/bigram_m2_k3_fixed_word_regression_lines.png)

![Real vs Bigram fixed-word source-minus-real regression gaps](../figs/route1_real_vs_controls_context_report/bigram_m2_k3_fixed_word_regression_gaps.png)

![Real vs Bigram model slope differences](../figs/route1_real_vs_controls_context_report/bigram_k3_word_model_slope_differences.png)

#### Real vs Trigram

![Real vs Trigram k0 versus k3 age means](../figs/route1_real_vs_controls_context_report/trigram_k0_vs_k3_age_means.png)

![Real vs Trigram context gain through age](../figs/route1_real_vs_controls_context_report/trigram_context_gain_by_age.png)

![Real vs Trigram with-context k3 focus](../figs/route1_real_vs_controls_context_report/trigram_k3_with_context_focus.png)

![Real vs Trigram fixed-word regression lines](../figs/route1_real_vs_controls_context_report/trigram_m2_k3_fixed_word_regression_lines.png)

![Real vs Trigram fixed-word source-minus-real regression gaps](../figs/route1_real_vs_controls_context_report/trigram_m2_k3_fixed_word_regression_gaps.png)

![Real vs Trigram model slope differences](../figs/route1_real_vs_controls_context_report/trigram_k3_word_model_slope_differences.png)

#### Real vs LSTM family

![Real vs LSTM family k0 versus k3 age means](../figs/route1_real_vs_controls_context_report/lstm_k0_vs_k3_age_means.png)

![Real vs LSTM family context gain through age](../figs/route1_real_vs_controls_context_report/lstm_context_gain_by_age.png)

![Real vs LSTM family with-context k3 focus](../figs/route1_real_vs_controls_context_report/lstm_k3_with_context_focus.png)

![Real vs LSTM family fixed-word regression lines](../figs/route1_real_vs_controls_context_report/lstm_m2_k3_fixed_word_regression_lines.png)

![Real vs LSTM family fixed-word source-minus-real regression gaps](../figs/route1_real_vs_controls_context_report/lstm_m2_k3_fixed_word_regression_gaps.png)

![Real vs LSTM family model slope differences](../figs/route1_real_vs_controls_context_report/lstm_k3_word_model_slope_differences.png)

#### Real vs Caretakers

![Real vs Caretakers k0 versus k3 age means](../figs/route1_real_vs_controls_context_report/caretaker_k0_vs_k3_age_means.png)

![Real vs Caretakers context gain through age](../figs/route1_real_vs_controls_context_report/caretaker_context_gain_by_age.png)

![Real vs Caretakers with-context k3 focus](../figs/route1_real_vs_controls_context_report/caretaker_k3_with_context_focus.png)

![Real vs Caretakers fixed-word regression lines](../figs/route1_real_vs_controls_context_report/caretaker_m2_k3_fixed_word_regression_lines.png)

![Real vs Caretakers fixed-word source-minus-real regression gaps](../figs/route1_real_vs_controls_context_report/caretaker_m2_k3_fixed_word_regression_gaps.png)

![Real vs Caretakers model slope differences](../figs/route1_real_vs_controls_context_report/caretaker_k3_word_model_slope_differences.png)

The source-specific M4c Atlas panels are useful appendix figures because they put each source into the same corrected fixed-effort plotting grammar.

![Real child source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png)

![Random source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4c_nb_words_fixed_effort_atlas.png)

![Unigram source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4c_nb_words_fixed_effort_atlas.png)

![Bigram source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4c_nb_words_fixed_effort_atlas.png)

![Trigram source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4c_nb_words_fixed_effort_atlas.png)

![LSTM k3 source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

![LSTM k4 source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

![LSTM k5 source-specific M4c Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png)

Descriptive context means are still useful for orientation, but they are not the main inference because they are not fixed-effort regression estimates.

| source | rows | mean_k0 | mean_k3 | context_gain | mean_words |
| --- | --- | --- | --- | --- | --- |
| Real child | 446,985 | 40.33 | 26.73 | 13.61 | 2.66 |
| Random | 446,508 | 68.96 | 61.11 | 7.85 | 2.66 |
| Unigram | 446,508 | 51.17 | 41.83 | 9.34 | 2.66 |
| Bigram | 446,508 | 47.59 | 36.79 | 10.79 | 2.66 |
| Trigram | 446,508 | 45.54 | 33.68 | 11.86 | 2.66 |
| LSTM k3 | 446,508 | 39.79 | 28.42 | 11.37 | 2.66 |
| LSTM k4 | 446,508 | 39.98 | 28.51 | 11.47 | 2.66 |
| LSTM k5 | 446,508 | 39.96 | 28.51 | 11.45 | 2.66 |
| Caretaker | 668,903 | 49.41 | 30.00 | 19.41 | 4.42 |

The paired generated-control models use the same original child utterance as the comparison unit. Positive k3 gaps mean that the generated control is more surprising than the real child utterance in the same context.

| source | test | mean | age slope | p | n |
| --- | --- | --- | --- | --- | --- |
| Random | k3 source-real gap | 34.402 | 0.302 | <.001 | 446,508 |
| Random | context-gain source-real gap | -5.759 | 0.009 | 0.512 | 446,508 |
| Unigram | k3 source-real gap | 15.119 | 0.103 | <.001 | 446,508 |
| Unigram | context-gain source-real gap | -4.269 | 0.018 | 0.109 | 446,508 |
| Bigram | k3 source-real gap | 10.082 | 0.102 | <.001 | 446,508 |
| Bigram | context-gain source-real gap | -2.814 | 3.15e-04 | 0.982 | 446,508 |
| Trigram | k3 source-real gap | 6.964 | 0.109 | <.001 | 446,508 |
| Trigram | context-gain source-real gap | -1.747 | -0.013 | 0.325 | 446,508 |
| LSTM k3 | k3 source-real gap | 1.707 | 0.078 | 0.020 | 446,508 |
| LSTM k3 | context-gain source-real gap | -2.241 | 0.026 | 0.028 | 446,508 |
| LSTM k4 | k3 source-real gap | 1.798 | 0.066 | 0.066 | 446,508 |
| LSTM k4 | context-gain source-real gap | -2.142 | 0.033 | 0.002 | 446,508 |
| LSTM k5 | k3 source-real gap | 1.799 | 0.064 | 0.074 | 446,508 |
| LSTM k5 | context-gain source-real gap | -2.159 | 0.033 | 0.003 | 446,508 |

Caretakers are a different comparison because they are not generated alternatives for the same child row. They ask whether adult speech in the same families has the same child-age trajectory.

| outcome | real mean | caretaker mean | source x age | p | n |
| --- | --- | --- | --- | --- | --- |
| sum_bits_k3 | 26.726 | 29.998 | -0.033 | 0.327 | 1,115,888 |
| context_gain | 13.607 | 19.410 | -0.005 | 0.817 | 1,115,888 |

### Heldout Children

The heldout panel is not the cleanest proof, but it is important because it makes generalization inspectable. Black lines are actual heldout child trends; dashed teal lines are PBM-trained predictions.

| child | effort band | actual slope/month | predicted slope/month | month points |
| --- | --- | --- | --- | --- |
| Forrester/Ella | 1-4 | 0.027 | -0.014 | 25 |
| Forrester/Ella | 5-8 | -0.419 | -2.47e-04 | 25 |
| Forrester/Ella | 9-12 | -1.239 | 0.014 | 14 |
| Sachs/Naomi | 1-4 | 0.115 | -0.014 | 24 |
| Sachs/Naomi | 5-8 | 0.028 | -2.47e-04 | 21 |
| Sachs/Naomi | 9-12 | 0.829 | 0.014 | 14 |
| MPI-EVA-Manchester/Helen | 1-4 | 0.048 | -0.014 | 26 |
| MPI-EVA-Manchester/Helen | 5-8 | -0.082 | -2.47e-04 | 26 |
| MPI-EVA-Manchester/Helen | 9-12 | -0.069 | 0.014 | 26 |

![Heldout actual versus predicted regression lines](../figs/route1_candidate_evidence_gallery/heldout_pop_m4c_actual_vs_predicted_regression_lines.png)

![Heldout calibration and residual diagnostics](../figs/route1_candidate_evidence_gallery/heldout_pop_m4c_calibration_residuals.png)

### Candidate Supervisor Claim

> At the same production-effort level, older children produce utterances that are more predictable in context than younger children. This fixed-effort developmental decrease appears in the primary row-level child-identity model, survives major context/form controls, remains visible in exact-length checks for well-supported word counts, is defended by age-scrambling robustness, and differs from random, n-gram, LSTM, and caretaker comparison patterns.

The claim must stay conditional. It is not saying older children communicate less overall. Older children often produce longer utterances, and longer utterances carry more total bits. The claim is that among utterances of comparable effort, the model finds older children's utterances more contextually predictable.

### What To Cut Or Keep For The Final Supervisor Version

Keep in the main text: one primary fixed-effort figure, the exact-length proof figure, one compact model-ladder table, one age-scrambling figure, and one source-comparison figure.

Move to appendix: the full F01-F21 table, the estimator-family table, heldout calibration, all paired source-gap model tables, and individual source-specific Atlas figures.

Do not overclaim yet: Route 2 effort choice. The current report controls effort; it does not yet prove that children choose effort as a function of response-space context uncertainty.

## Possible Next Steps

### Expand Beyond the Initial Three Corpora

The present report focuses on Providence, Brown, and Manchester because they
form the current dense longitudinal analysis set. The larger naturalistic
dataset now includes additional caregiver-child corpora and can be used to ask
whether the Model 2 pattern generalizes beyond these three corpora. Clinical
and control corpora are also available, but they should be handled as a
separate extension because their sampling designs differ from naturalistic
home-interaction data.

### Stronger Generated Baselines

The same-length random and n-gram baselines are useful because they control
utterance length and developmental vocabulary access. A stronger generated
baseline would use a small child-language model, such as an LSTM or BabyLM-like
transformer, trained under the same developmental constraints. This would test
whether the child pattern differs from a model that has learned more than local
word frequencies.

### Word-Level Surprisal

The current result uses total utterance information. Word-level surprisal would
make it possible to ask where the age effect comes from inside the utterance:
early versus late words, function versus content words, or particular lexical
and morphological positions. This would help distinguish a broad utterance-level
predictability effect from a small number of highly surprising words.
