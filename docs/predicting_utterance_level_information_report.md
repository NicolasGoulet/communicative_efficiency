# Predicting Informational Content at the Utterance Level

Working draft, June 2026

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

The analyses will focus on three related quantities:

- **total information per utterance**, measured with `sum_bits`;
- **information per unit of production effort**, where `sum_bits` is divided by the number of words, morphemes, phonemes or syllables in an utterance;
- **tokenizer-level sensitivity**, measured with `mean_bits_per_token`.

A follow-up document will be shared in the following days that will explore the analyses proposed by Professor Xu : how (and if) do contextual information predict utterance length / utterance effort. 

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

This is partly due to having very few utterances in these 6 months bins, but t is also consistent with well-established developmental changes in utterance length: around the second year, children increasingly move from single-word productions to multiword utterances, and mean length of utterance rises over early childhood.

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

These measures are also important because the generated baselines (discussed bellow) are
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

All these baselines use additive age-bins, where the size of their vocabulary is expended incrementally with each new age bin.

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

The planned LSTM comparison follows the same additive developmental logic as the
n-gram baselines. For each age bin, a different LSTM is trained on the current bin plus
all previous bins, then used to generate utterances only for the target bin.
This keeps the comparison aligned with the developmental information available
to the n-gram baselines.

The LSTM can listen to caretaker language, but it is only allowed to speak using the child-side vocabulary observed in the age-appropriate training data. 

The first LSTM comparison will use same-length generated utterances, so effort
is held constant relative to the real child utterance. A later free-length
variant can ask a different question: whether the model chooses a similar amount
of communicative effort when responding to the same caretaker context.


## Explanatory Models

This section of the document describes certain models that attempt to predict informational contents of child speech in naturalistic settings at the utterance level.

Additionally, SES metrics were not available systematically for all children and was particularly sparse for the PBM sample. 

The first modeling pass focuses on three closely related models. The outcome is
`sum_bits`, the total Mistral surprisal of the target child utterance in bits.

### Statistical Model Choice

These are linear regression models for a continuous outcome measured in bits.
They are fit with ordinary least squares in `statsmodels`. Because each child
contributes many utterances, uncertainty estimates use child-clustered robust
standard errors. Models 2 and 3 also include child fixed effects, which means
each child gets their own baseline intercept.

The first presentation uses linear regression because the outcome is continuous
and the coefficients remain directly interpretable in bits. This is not the
only model family we considered. Internal checks also explored Gaussian GEE
models grouped by child, GLM/Gamma variants for positive outcomes, and
mixed-effect models with random intercepts and random age slopes. GEE asks for
a population-average trend while accounting for within-child correlation;
mixed-effects models estimate child-level variation in baselines and slopes;
GLM/Gamma variants check whether the positivity/skew of total bits changes the
conclusion. These belong in the technical appendix, while the first
supervisor-facing result uses the more transparent model ladder below.

The model ladder is theory-driven rather than selected automatically. We do not
use stepwise selection or variable-importance ranking to choose predictors,
because the effort measures are strongly correlated with one another and
variable-importance measures can be unstable under multicollinearity. Instead,
words, morphemes, syllables, and phonemes are analyzed as separate effort
controls.

| Model family | Role in the current analysis |
| --- | --- |
| OLS / linear regression | Main displayed model family; gives directly interpretable changes in bits. |
| Child fixed effects | Controls stable child-to-child differences by giving each child their own intercept. |
| Child-clustered standard errors | Keeps the OLS mean structure but adjusts uncertainty for repeated utterances from the same child. |
| GEE grouped by child | Internal sensitivity check for population-average effects with correlated rows. |
| Mixed effects | Internal sensitivity check for random child intercepts and random age slopes; useful, but less stable here and less transparent for the first presentation. |
| GLM/Gamma variants | Internal sensitivity check for the fact that total bits are positive and skewed. |

The child term is not treated as a substantive discovery by itself. It is a
necessary adjustment for this unbalanced longitudinal design: different
children enter the corpus at different ages, leave at different ages, and
contribute different numbers of sessions. Model 2 asks whether the age pattern
remains after each child is allowed to have their own baseline level of
surprisal. This does not invent observations at ages where a child was not
recorded; it estimates the age trend from the observed developmental timeline
while preventing stable between-child differences from being mistaken for age.
The substantive finding is therefore not "children differ"; it is that the
same-effort age trajectory changes direction once the model accounts for those
stable child-to-child differences.

In the formulas below, `age_c` and `effort_c` are centered versions of age in
months and the effort count. The age coefficient therefore gives the expected
change in total bits for one additional month, after the model's controls.

### Model 1: Pooled Age and Effort

**Question.** If all children are pooled together, does age predict total
information after controlling for the amount of linguistic material in the
utterance?

**Formula.**

```text
sum_bits ~ age_c + effort_c
```

This model controls utterance effort, but it does not control stable
differences between children. It is therefore a useful baseline model, not the
main developmental model.

Model 1 gives a mixed developmental picture. With exact effort counts, the age
coefficient is not reliable for words or morphemes, and it is positive for the
two phonological effort measures that reach conventional significance. This
suggests that simply pooling all children is not enough to isolate the
developmental trajectory.

![Model 1 fixed-effort age trajectories](../figs/m1_m6_fixed_effort_slices/m1_top_frequency_12_fixed_effort_slices.png)

Each line shows the predicted age trajectory for one exact fixed effort value.
In Model 1, the trajectories are mostly flat or upward. This is the pooled
picture before controlling stable differences between children.

![Model 1 balanced and scrambled age checks](../figs/age_scrambling_robustness/m1_age_slope_robustness_intervals.png)

### Model 2: Age and Effort with Child Identity

**Question.** Does the developmental age effect remain after controlling for
the fact that different children have different baselines and are observed over
different age ranges?

**Formula.**

```text
sum_bits ~ age_c + effort_c + C(child_id)
```

Here `C(child_id)` is a fixed effect for each child. It lets each child have a
different intercept, so the age coefficient is no longer driven only by
between-child differences.

Model 2 changes the conclusion. After child identity is controlled, all five
effort measures show a negative age coefficient, and all five are statistically
reliable. This suggests that, at comparable effort, children's utterances
become less surprising to the model as they get older.

![Model 2 fixed-effort age trajectories](../figs/m1_m6_fixed_effort_slices/m2_top_frequency_12_fixed_effort_slices.png)

The same fixed-effort slices now turn downward. This is the clearest visual
evidence that the pooled model was hiding a within-child developmental pattern.

![Model 2 balanced and scrambled age checks](../figs/age_scrambling_robustness/m2_age_slope_robustness_intervals.png)

### Model 3: Age by Effort

**Question.** Does the relationship between effort and total information itself
change with age?

**Formula.**

```text
sum_bits ~ age_c * effort_c + C(child_id)
```

This model keeps the child fixed effects from Model 2 and adds the interaction
between age and effort. The interaction tests whether the slope relating effort
to total bits changes over development.

Model 3 is broadly consistent with Model 2. The age coefficients are negative
for all five effort measures and statistically reliable for four of five. The
age-by-effort interaction is small in most versions, so the main result is not
that effort suddenly has a completely different meaning over development.
Rather, once child identity is controlled, the age trajectory itself is
downward.

![Model 3 fixed-effort age trajectories](../figs/m1_m6_fixed_effort_slices/m3_top_frequency_12_fixed_effort_slices.png)

Model 3 preserves the downward pattern while asking whether the effort slope
itself changes with age. The interaction is not the main driver of the result;
the child-controlled age trajectory remains the central finding.

![Model 3 balanced and scrambled age checks](../figs/age_scrambling_robustness/m3_age_slope_robustness_intervals.png)

### Fixed-Effort Slice Check

The fitted models summarize the global effect of age after controlling effort
numerically. As an additional check, we also plot predicted age trajectories at
exact fixed effort values. These plots are easier to read: each line answers,
"what is the predicted age trajectory for utterances with this exact amount of
effort?"

For words and morphemes, the plotted fixed values are exact counts from 1 to
12. For syllables and phonemes, we first checked the observed distribution of
utterance lengths and then selected data-supported values. In the phoneme
panel, the plotted values are 2 through 13 phonemes: the twelve most frequent
exact phoneme counts in the current child-utterance sample. In the fuller atlas,
these same phoneme values are grouped as low representative sizes (2-5),
middle representative sizes (6-9), and high representative sizes (10-13).

The contrast between Models 1 and 2 is the core result. Model 1 does not
control child identity and gives upward or flat predicted trajectories. Model 2
controls child identity, and the predicted trajectory turns downward across the
fixed-effort slices. Across the full fixed-effort atlas, Model 2 shows negative
age slopes in 67 of 67 fixed-effort slices. Model 3 shows negative age slopes
in 63 of 67 fixed-effort slices.

| Model | Fixed-effort slices | Negative slices | Median slope per six months | Range |
| --- | --- | --- | --- | --- |
| M1 | 67 | 0/67 | 0.309 | 0.002 to 0.414 |
| M2 | 67 | 67/67 | -0.389 | -0.813 to -0.291 |
| M3 | 67 | 63/67 | -0.420 | -0.942 to 0.194 |

### Balanced and Scrambled Age Checks

The robustness analysis asks whether the observed age effects are stable under
two different kinds of checks.

First, a balanced bootstrap resamples the data so that age bins contribute more
evenly. This is a stability check, not a null test. If the observed slope falls
inside the balanced-bootstrap interval, it means the result is compatible with
balanced age-bin resampling.

Second, age-scrambling checks destroy the real developmental ordering. These
are null tests. The most important version scrambles age within each child,
which preserves child identity but breaks that child's developmental timeline.
If the observed slope is outside this scrambled null distribution, the real
developmental order is carrying information.

![Robustness summary for balanced and scrambled age checks](../figs/age_scrambling_robustness/robustness_outside_null_heatmap.png)

The model-specific robustness plots above show where the observed age slope
falls relative to balanced-bootstrap intervals and scrambled-age null
intervals. The heatmap gives the same information compactly across the model
family. The strongest result is again Models 2 and 3. For both models, the
observed negative age slopes are outside the scrambled null intervals in all
comparisons for the unit-level and within-child scrambling checks. This supports
the interpretation that the downward age trajectory is tied to real
developmental ordering, not just to arbitrary age labels.

The next three plots show the same robustness checks as regression-line
diagnostics. They are more visual than the interval plots: the observed line is
compared with balanced resamples and age-scrambled controls.

![Model 1 balanced and scrambled regression lines](../figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png)

![Model 2 balanced and scrambled regression lines](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

![Model 3 balanced and scrambled regression lines](../figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png)

| Model | Check | Comparisons | Observed negative | Outside 95% interval | Permutation p < .05 |
| --- | --- | --- | --- | --- | --- |
| M1 | Balanced bootstrap | 20 | 2/20 | 16/20 |  |
| M1 | Age-bin scramble | 20 | 2/20 | 16/20 | 16/20 |
| M1 | Unit-age scramble | 20 | 2/20 | 20/20 | 19/20 |
| M1 | Within-child scramble | 20 | 2/20 | 13/20 | 5/20 |
| M2 | Balanced bootstrap | 20 | 20/20 | 1/20 |  |
| M2 | Age-bin scramble | 20 | 20/20 | 20/20 | 19/20 |
| M2 | Unit-age scramble | 20 | 20/20 | 20/20 | 20/20 |
| M2 | Within-child scramble | 20 | 20/20 | 20/20 | 20/20 |
| M3 | Balanced bootstrap | 20 | 20/20 | 4/20 |  |
| M3 | Age-bin scramble | 20 | 20/20 | 20/20 | 18/20 |
| M3 | Unit-age scramble | 20 | 20/20 | 20/20 | 20/20 |
| M3 | Within-child scramble | 20 | 20/20 | 20/20 | 20/20 |

### Key takeways

- Total surprisal cannot be interpreted without effort controls, because older
  children produce longer utterances.
- Model 1 is not sufficient as a developmental model, because it pools children
  who cover different age ranges.
- Once child identity is controlled in Models 2 and 3, age has a consistently
  negative association with total surprisal at comparable effort.
- The fixed-effort slice checks show the same pattern visually: for Model 2,
  all 67 fixed-effort slices have downward age trajectories.
- The age-scrambling checks support the interpretation that the effect depends
  on real developmental ordering, especially when age is scrambled within
  child.

## Possible Next Steps 

### Using the full (still expending) data set

TODO DESCRIBE SUPER BRIEFLY THE NON-CLINICAL DATASET WE HAVE

TODO DESCRIBE SUPER BREIFLY THE CLINICAL DATASET WE HAVE

### Generate utterances with BabyLM-like architectures

An even stronger baseline would be have a BabyLM-like transformer architecture to generate utterances for each child utterance. To not have these models make inference on their training data, we train a new model for each corpus 

### Word-level surprisal

TODO DESCRIBE THIS IDEA
