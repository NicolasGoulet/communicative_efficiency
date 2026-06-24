# Predicting Informational Content at the Utterance Level

Working draft, June 2026

## Introduction

This document describes an utterance-level analysis of communicative efficiency
in child language. The broad goal is to understand how children learn to package
information in speech while managing the effort required to produce it.

In this framing, communicative efficiency has two parts. The first is
**informativeness**: how much information an utterance conveys in context. The
second is **production effort**: how much linguistic material is produced to convey that
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

## Complexity / Production Effort

The first part of the analysis concerns the amount of linguistic material used
to produce an utterance. In this document, this is treated as production
effort. The central idea is simple: an utterance with more words, more
morphemes, more syllables, or more phonemes generally requires more material to
produce than a shorter utterance.

The primary effort measure is the number of lexical words in the cleaned target
utterance. This measure is easy to interpret and aligns directly with the
matched-length baseline design, since the random, n-gram, and LSTM
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
requiring a different amount of phonological or morphological effort. It is worthwhile to stress that this is production effort : complexity can also be addressed in the context of cognitive complexity.

## Information

### Surprisal

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

### Response Entropy (and Next-Token Context Entropy)

Another feature related to information is response entropy : for a given context, *how varied are the different possible answers* when sampling from a language model? Here, the language model used is the same one used for *scoring* surprisal : Mistral 7B params. 
Instead of sampling the entire set of possible answers (which is not computationally feasible), 100 answers are generated for each unique context-window, and not for each unique utterances.
This is because many utterances produced by children are said in a row.
The 100 generated answers should be understood as a Monte Carlo approximation to the distribution of possible responses given that context. If the same context window appears repeatedly in the corpus, sampling 100 new responses for every repeated occurrence would mostly duplicate the same conditioning event and would overweight common contexts. Sampling once per unique context window estimates `P(response | context)` for that context; the resulting entropy estimate can then be attached back to every corpus row where that context occurred.
At the time of writing these lines, GPUs are hard at work generating these utterances!

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

Additionally, as I write these lines I realize we could also use some of the sampled utterances necessary for context entropy as a new source of baseline comparison.


## Analyses and Results

We are now ready to describe results of various analyses. As stated at the start of this document, the following models are trying to predict the total sum of bits at the level of utterances. 

### Model 0 : Not controlling for effort 

The most naive approach is to consider only the average of bits per token per utterance through time. This reveals a developmental decrease in bits per tokens in utterances that is explained by the increase in mean-utterance-length.
Increase in MLU has two effects related to surprisal worth notting here : (1) the total amount of surprisal per utterance increases and (2) the average bit per token decreases, as larger context windows make subsequent tokens less unpredictable. 

The three descriptive plots below show this raw pattern before any effort or child-identity controls are introduced. Mean utterance length in words increases with age; mean total utterance surprisal also increases; mean bits per evaluated token tends to decline overall, although the raw trajectory is not perfectly monotonic in every late age bin.

<table class="plot-layout">
<tr>
<td><img src="../figs/supervisor_report_todo_plots/model0_mlu_words_by_age.png" alt="Model 0 descriptive mean utterance length"><div class="plot-caption">Mean utterance length</div></td>
<td><img src="../figs/supervisor_report_todo_plots/model0_sum_bits_by_age.png" alt="Model 0 descriptive total utterance bits"><div class="plot-caption">Total utterance information</div></td>
</tr>
<tr>
<td colspan="2" class="centered-cell"><img src="../figs/supervisor_report_todo_plots/model0_bits_per_token_by_age.png" alt="Model 0 descriptive bits per token"><div class="plot-caption">Information per evaluated token</div></td>
</tr>
</table>

### Model 1 : Only controlling for effort 

This slightly less naive models assumes independance between individual utterances, which is a wrong assumption : two utterance from the same child are likely to be more correlated than utterances from two different children. **This being said**, what do models predict when we only control for effort?

Controlling for effort here means comparing utterances at the same amount of produced linguistic material. In practice, this is done by adding one effort measure at a time to the regression, for example `sum_bits ~ age + nb_words` or `sum_bits ~ age + nb_phonemes`. The model asks whether age still predicts total utterance information after accounting for the fact that longer utterances naturally accumulate more bits.

The effort-only model is still intentionally incomplete because it treats every utterance as independent and does not account for repeated observations from the same child. In this version, the age slope is positive for morphemes, syllables, and phonemes, while the word-controlled slope is essentially flat. This suggests that effort control alone is not enough: between-child differences and corpus composition can still distort the developmental interpretation.

<table class="plot-layout">
<tr>
<td><img src="../figs/supervisor_report_todo_plots/model1_words_effort_only_predictions.png" alt="Model 1 effort-only fixed-effort predictions for word count"><div class="plot-caption">Words</div></td>
<td><img src="../figs/supervisor_report_todo_plots/model1_morphemes_effort_only_predictions.png" alt="Model 1 effort-only fixed-effort predictions for morpheme count"><div class="plot-caption">Morphemes</div></td>
</tr>
<tr>
<td><img src="../figs/supervisor_report_todo_plots/model1_syllables_cmu_pkg_effort_only_predictions.png" alt="Model 1 effort-only fixed-effort predictions for CMU/pkg syllable count"><div class="plot-caption">Syllables: CMU/pkg</div></td>
<td><img src="../figs/supervisor_report_todo_plots/model1_syllables_pkg_effort_only_predictions.png" alt="Model 1 effort-only fixed-effort predictions for package syllable count"><div class="plot-caption">Syllables: pkg</div></td>
</tr>
<tr>
<td colspan="2" class="centered-cell"><img src="../figs/supervisor_report_todo_plots/model1_phonemes_effort_only_predictions.png" alt="Model 1 effort-only fixed-effort predictions for phoneme count"><div class="plot-caption">Phonemes</div></td>
</tr>
</table>

### Model 2 : Controlling for child-identity

Of course each utterances are not independant observations. They are conversational turns from specific subjects over time. It therefore makes sense to control for the identity of children.


### Model 2 Details

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

<table class="plot-layout">
<tr>
<td><img src="../figs/m2_simple_plots/m2_words_fixed_effort_and_global_trend.png" alt="Model 2 fixed-effort predictions for word count"><div class="plot-caption">Words</div></td>
<td><img src="../figs/m2_simple_plots/m2_morphemes_fixed_effort_and_global_trend.png" alt="Model 2 fixed-effort predictions for morpheme count"><div class="plot-caption">Morphemes</div></td>
</tr>
<tr>
<td><img src="../figs/m2_simple_plots/m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png" alt="Model 2 fixed-effort predictions for CMU/pkg syllable count"><div class="plot-caption">Syllables: CMU/pkg</div></td>
<td><img src="../figs/m2_simple_plots/m2_syllables_pkg_fixed_effort_and_global_trend.png" alt="Model 2 fixed-effort predictions for package syllable count"><div class="plot-caption">Syllables: pkg</div></td>
</tr>
<tr>
<td colspan="2" class="centered-cell"><img src="../figs/m2_simple_plots/m2_phonemes_fixed_effort_and_global_trend.png" alt="Model 2 fixed-effort predictions for phoneme count"><div class="plot-caption">Phonemes</div></td>
</tr>
</table>

## Robustness Checks

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

### Model 3 : Does the age effect depend on utterance effort?

Model 3 is the next natural model after Model 2. Model 2 asks whether age
predicts total utterance information after controlling effort and child
identity. Model 3 adds the possibility that the developmental trajectory is not
identical at every utterance size.

The formula is:

```text
sum_bits ~ age + effort + age:effort + child identity
```

The interaction term `age:effort` asks whether the age slope is different for
shorter versus longer utterances. This is useful because the central concern is
not only whether older children produce lower predicted `sum_bits` at a fixed
effort level, but whether that fixed-effort pattern is similar for short,
medium, and longer utterances.

For the word-count version with three preceding caretaker utterances as
context, the main age effect remains negative: `-0.122` bits per month
(`p < .001`). The age-by-effort interaction is small in this version. The
fixed-effort plot is therefore the most useful way to read the model: it shows
whether the predicted age trajectory remains downward across different exact
word counts.

| Effort control | Age effect, bits/month | Age p | Age-by-effort effect | Model fit |
| -------------- | ---------------------- | ----- | -------------------- | --------- |
| Words | -0.122 | <.001 | -0.004 | R2 = 0.626 |
| Morphemes | -0.136 | .002 | 0.002 | R2 = 0.613 |
| Syllables: CMU/pkg | -0.066 | .027 | 0.007 | R2 = 0.646 |
| Syllables: pkg | -0.052 | .070 | 0.010 | R2 = 0.630 |
| Phonemes | -0.067 | .027 | 0.003 | R2 = 0.644 |

![Model 3 age-by-effort fixed-effort predictions](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png)

The main interpretation is conservative: allowing the effort slope to vary by
age does not remove the Model 2 pattern. The same-effort developmental trend is
still downward for the word-count version, and the model gives a more flexible
answer than Model 2 because it no longer forces every fixed-effort line to be
perfectly parallel.

The same age-scrambling robustness framework can also be used for Model 3. In
the current robustness plots, the observed Model 3 age pattern remains outside
the scrambled-age null ranges.

![Model 3 balanced and age-scrambled robustness checks](../figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png)

### Model 4 : Adding Both Context Controls

The next step is a single context-control model that combines the
parent-context effort and context-entropy predictors. No question-type
predictor is included.

```text
sum_bits ~ age + effort + age:effort
         + parent context effort + context entropy
         + child identity
```

This model asks whether the Model 3 pattern survives after controlling both how
much preceding caretaker speech is available and how uncertain the preceding
context is. For the word-count version, the age effect remains negative:
`-0.122` bits per month (`p < .001`; `n = 441,413`, `R2 = 0.627`).

To keep the interpretation readable, the useful individual-predictor readout is
the small table below.

| Predictor | Estimate | p | Interpretation |
| --------- | -------- | --- | -------------- |
| Age | -0.122 bits/month | <.001 | Older children have lower predicted `sum_bits` at the same effort and context values. |
| Effort | 6.376 bits/word | <.001 | Longer utterances still carry more total predicted information. |
| Age x effort | -0.003 bits/month/word | .707 | Little evidence that the age effect changes by utterance length in this version. |
| Parent context effort | -0.043 bits/preceding-caretaker word | <.001 | More preceding caretaker speech is associated with slightly lower child `sum_bits`, holding the other terms fixed. |
| Context entropy | -0.470 bits/entropy unit | <.001 | Higher measured context entropy has an independent negative association with child `sum_bits`; this should be interpreted cautiously as an utterance-level context control. |

![Model 4 union context fixed-effort predictions](../figs/supervisor_union_context_model/real_k3_m4ab_no_question_nb_words_fixed_effort_atlas.png)

The main message is that the fixed-effort age pattern is not explained away by
adding both context controls. Compared with Model 3, the word-count age effect
is essentially unchanged, while the two context predictors each contribute an
interpretable control term.

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

### Separate Word-Level Follow-Up

The current report should remain focused on utterance-level `sum_bits`. A
separate follow-up report can use the existing word-level surprisal table to
ask where the age effect comes from inside the utterance: early versus late
words, function versus content words, or particular lexical and morphological
positions. That is a useful second project, but it is not the main argument of
this supervisor report.
