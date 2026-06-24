# Alternate Draft: Predicting Utterance Information At Fixed Effort

Working inspiration draft, June 2026

This is not a replacement for the active supervisor-facing report. It is a
plot-first alternate structure for deciding what should move into
`predicting_utterance_level_information_report.md`.

The focus is the utterance-information analysis: given a produced child
utterance, how much information does it carry according to Mistral, and how
does that change with age after controlling for production effort?

## One-Page Story

The current result is strongest when phrased as a fixed-effort utterance
information result.

First, older children produce longer utterances, so raw total information is
not enough. Second, after we compare utterances at the same effort level and
control child identity, the age trajectory changes direction: older child
utterances are less surprising to the model at comparable production effort.
Third, preceding caretaker context lowers surprisal substantially, and the
context effect survives checks that control the amount of context text.

The supervisor-facing claim should therefore be:

```text
At comparable production effort, child utterances become more predictable to
the language model over development, and this pattern is partly explained by
the preceding conversational context.
```

This is narrower than "children communicate less information." It is a
model-based utterance predictability claim under effort control.

## What The Current Report Already Does Well

The active report already has a clear setup:

- corpus coverage and child trajectories;
- why production effort must be controlled;
- Model 0 raw descriptives;
- Model 1 effort-only comparisons;
- Model 2 child-identity controls;
- robustness using balanced age-bin and scrambled-age checks.

The main missing piece is that the report still reads like a sequence of
models, while the evidence now supports a cleaner plot-first story:

1. establish the raw length/information confound;
2. show the fixed-effort child-controlled result;
3. show that context changes the result;
4. show the context effect is not only context length;
5. show real children against baselines/caretakers;
6. show the pattern is visible within individual children;
7. put word-level surprisal in a separate "mechanism / next analysis" box.

## Proposed Main Text Figures

### 1. Main Fixed-Effort Information Trajectory

**Purpose:** Make this the central result figure. It directly shows
information per word over age, split by word-count band and context window.

**What it says:** The developmental slope is steepest when no preceding
context is provided. As more context is supplied, the same child utterances
become less surprising and the age slope becomes smaller.

![Model-predicted bits per word across age, length, and context](../../compute_surprisal_mila/figs/cleaned_analysis/route1_information_rate/word_count/real_bits_per_word_by_age_length_context.png)

Suggested caption:

> Predicted information per word for real child utterances, controlling child
> identity and exact word-count category. Each panel compares utterances of
> similar length, so the developmental pattern is not simply mean length of
> utterance increasing with age.

### 2. Context-Specific Age Coefficients

**Purpose:** Give the coefficient summary for Figure 1.

**What it says:** The age effect is negative in all context windows, strongest
without context and weaker when conversational context is supplied.

![Context-specific age slopes with child-clustered uncertainty](../../compute_surprisal_mila/figs/cleaned_analysis/route1_information_rate/word_count/real_bits_per_word_context_age_slopes_cluster.png)

Suggested caption:

> Age slopes from the fixed-effort model. The negative no-context slope means
> that, for comparable utterance lengths from the same child, older utterances
> are less surprising to Mistral. The smaller slopes with context suggest that
> part of the developmental change is already captured by the preceding
> discourse.

### 3. Context Gain Over Age

**Purpose:** Explain what context contributes.

**What it says:** Mistral assigns lower surprisal to the same target when it
sees preceding caretaker speech. This is target-dependent context gain, not a
pure context-only entropy measure.

![Context gain over age](../../compute_surprisal_mila/figs/cleaned_analysis/route1_information_rate/word_count/real_route1_context_gain_by_age.png)

Suggested caption:

> Context gain is the reduction in information per word when the model scores
> the same child utterance with preceding caretaker context instead of no
> context. Larger values mean the preceding discourse made the child utterance
> more predictable.

### 4. Context Gain By Actual Context Size

**Purpose:** Answer the likely objection that k3 works only because it contains
more words than k1.

**What it says:** Context-window differences remain visible within comparable
context-size ranges.

![Context gain by actual context word-count bin](../../compute_surprisal_mila/figs/cleaned_analysis/route1_context_size_controls/word_count/context_gain_by_context_word_count_bin.png)

Suggested caption:

> Context gain by the actual number of words in the preceding caretaker
> context. This separates the effect of having a broader discourse window from
> the simpler fact that broader windows usually contain more text.

### 5. Context-Gain Slopes With Context-Size Controls

**Purpose:** Put the context-size-control result in coefficient form.

**What it says:** The broad-context advantage is not eliminated after
controlling context word count, context character count, question status,
question type, child identity, age, and target word count.

![Context gain age slopes with and without context-size controls](../../compute_surprisal_mila/figs/cleaned_analysis/route1_context_size_controls/word_count/context_gain_age_slopes_size_control_comparison.png)

Suggested caption:

> Context-gain age slopes before and after surface context-size controls. The
> conservative interpretation is not that context size is irrelevant, but that
> broader context effects are not reducible to context length alone.

### 6. Outcome Sensitivity

**Purpose:** Keep total bits, bits per word, and bits per token conceptually
separate.

**What it says:** The developmental pattern is visible across normalizations,
but each outcome answers a slightly different question.

![Outcome sensitivity across normalizations](../../compute_surprisal_mila/figs/cleaned_analysis/route1_information_rate/word_count/real_route1_outcome_sensitivity_slopes.png)

Suggested caption:

> Age slopes under three information outcomes. Bits per word is the clearest
> production-effort normalization; bits per token is a tokenizer sensitivity
> check; total bits at fixed effort asks whether the whole utterance changes
> after effort is controlled.

### 7. Dataset Robustness

**Purpose:** Address Brown, Manchester, and Providence imbalance.

**What it says:** The adjusted developmental pattern should be shown by corpus
so that the supervisor can see whether a single dataset is carrying the result.

![Adjusted bits per word by dataset](../figs/utterance_information_model_proposals/model2_adjusted_bits_per_word_by_dataset.png)

Suggested caption:

> Dataset-specific adjusted trajectories. This plot is a guard against
> interpreting a compositional corpus effect as a general developmental effect.

### 8. Individual Child Trajectories

**Purpose:** Make the repeated-measures structure concrete.

**What it says:** The highlighted children were selected by coverage, not by
effect size. These are useful for meetings because they show actual
longitudinal cases.

![Individual real-child trajectories: k0 vs k3](../../compute_surprisal_mila/figs/cleaned_analysis/supervisor_communicative_efficiency/highlight_individual_surprisal_k0_k3.png)

Suggested caption:

> Length-standardized individual trajectories for the best-covered children.
> These plots are descriptive, not the main inferential model, but they show
> how the population-level pattern appears in concrete longitudinal records.

### 9. Real Children Versus Frequency Baselines

**Purpose:** Show that the real-child trajectory is not reproduced by simple
frequency or local-order baselines.

**What it says:** Random, unigram, bigram, and trigram comparisons should be
shown in word-count bands rather than pooled across all lengths.

![Real versus frequency and n-gram baselines](../../compute_surprisal_mila/figs/cleaned_analysis/lstm_stratified_surprisal/real_vs_frequency_word_count_bands_by_context.png)

Suggested caption:

> Real child utterances compared with same-length random and n-gram generated
> baselines. The panels keep word-count bands visible so the comparison remains
> tied to fixed production effort.

### 10. Real Children Versus LSTM Baselines

**Purpose:** Stop describing LSTM only as future work. The relevant comparison
exists and can be used as a stronger generated baseline.

**What it says:** The LSTM comparison asks whether a small child-language model
trained under developmental constraints reproduces the real-child information
trajectory better than n-gram baselines.

![Real versus LSTM baselines](../../compute_surprisal_mila/figs/cleaned_analysis/lstm_stratified_surprisal/real_vs_lstm_word_count_bands_by_context.png)

Suggested caption:

> Real child utterances compared with same-length LSTM generated utterances
> across context windows and word-count bands. This is a stronger baseline than
> random or n-gram generation because it can encode preceding caretaker context.

## Optional Appendix Figures

These are good evidence, but they may be too much for the main supervisor
report unless the report becomes a longer technical appendix.

### Exact-Effort Slopes

![Exact-effort age slopes](../figs/route1_exhaustive_ancova_gallery/real_exact_effort_age_slopes_sum_bits_k3.png)

Use this when answering: "Could the effect still be MLU?" The plot compares
within exact effort values.

### Scrambled-Age Robustness

![Model 2 balanced and age-scrambled robustness checks](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)

Use this when answering: "Could age bins or sample imbalance produce the
effect?"

### Real Versus Baseline Gaps

![Source-minus-real gap lines](../figs/route1_exhaustive_ancova_gallery/nb_words_sum_bits_k3_source_minus_real_gap_lines.png)

Use this when the report needs an intuitive baseline contrast: real child
utterances are the zero line, and each generated/caretaker source is shown as
an adjusted gap from real speech.

## Word-Level Surprisal: Use It, But Do Not Let It Blur The Main Claim

The exact word-level Mistral product exists. The local file in
`compute_surprisal_mila` contains:

| Quantity | Value |
| --- | ---: |
| Word rows | 16,506,760 |
| Unique source utterance rows | 1,111,346 |
| Context windows | k0, k1, k2, k3 |
| Real child word rows | 4,712,304 |
| Caretaker word rows | 11,794,456 |
| Datasets | Brown, Manchester, Providence |

The useful columns include:

```text
word_index
word
word_lower
word_sum_bits
word_mean_bits_per_subword
word_bits_per_char
word_bits_per_syllable
token_offsets_json
token_strings_json
token_bits_json
context_window
speaker_mode
child_key
age_months
```

This can absolutely be used, but it should be framed as a mechanism or
follow-up layer, not as the main utterance-level claim.

### Word-Level Question 1: Same Word, Different Contexts

Scientific question:

```text
When children use the same word at different ages, does that word appear in
more predictable or less predictable contexts?
```

Suggested model:

```text
word_sum_bits ~ age + C(word_lower) + C(child_id)
              + C(context_window) + C(word_position_bin)
```

Why it is useful:

This controls lexical identity. It asks whether the same word, not just a
different vocabulary mix, receives different contextual surprisal over
development.

Suggested plot:

```text
Age trajectory of word-identity-centered word surprisal
```

This would plot the residual:

```text
word_sum_bits - mean(word_sum_bits for that word)
```

by age and context window.

### Word-Level Question 2: Where In The Utterance Does The Effect Live?

Scientific question:

```text
Is the utterance-level age effect concentrated in the first word, later words,
or distributed across the utterance?
```

Suggested model:

```text
word_sum_bits ~ age * C(word_position_bin)
              + C(word_lower) + C(child_id) + C(context_window)
```

Suggested plot:

```text
Predicted word surprisal by age for first, middle, and final words
```

Why it is useful:

If the age effect is strongest on first words, that suggests improved context
fit at turn onset. If it is distributed across positions, the whole utterance
becomes more predictable.

### Word-Level Question 3: Form Cost And Informativity

Scientific question:

```text
Are more effortful word forms also more informative in these child-directed
dialogues?
```

Suggested outcomes:

```text
word_sum_bits
word_bits_per_syllable
word_bits_per_char
```

Suggested predictors:

```text
word_char_len
word_syllable_count
frequency or word fixed effects
speaker_mode
context_window
```

Why it is useful:

This is the closest bridge to the word-level informativity literature. It is a
separate analysis from the utterance-level supervisor story, but it can become
a strong appendix or next report.

## Replacement For The Current Possible Next Steps

The active report's current next-steps section should not say that LSTM or
word-level surprisal are merely future plans. They exist. A better ending is:

### Immediate Decisions For The Supervisor Version

1. Choose the main outcome language: total utterance information at fixed
   effort, bits per word, or both with separate labels.
2. Move the fixed-effort age-by-context figure and coefficient figure into the
   main results section.
3. Add the context-size-control plots immediately after the context-gain
   section.
4. Add one generated-baseline figure and one LSTM-baseline figure as controls,
   not as future work.
5. Add one individual-child trajectory figure for intuition, while keeping the
   population model as the formal evidence.

### Appendix Or Follow-Up Within The Same Project

1. Add exact-effort slopes as the strongest MLU-only rebuttal.
2. Add scrambled-age robustness as the strongest age-label/sampling rebuttal.
3. Summarize the word-level product with one lexical-identity-controlled plot.
4. Keep context-only entropy and response entropy in a separate report unless
   the supervisor specifically wants the production-effort-as-outcome route in
   the same document.

### Suggested Final Paragraph

The current analysis supports a fixed-effort utterance-information claim:
children's produced utterances become more predictable to the model over
development once production effort and child identity are controlled. The
effect is visible across effort measures, survives sampling and age-scrambling
checks, and can be compared against same-length generated baselines. The
context analyses show that preceding caretaker speech substantially lowers
target surprisal, even after controlling the amount of context text. The
word-level scored product is now available for a separate mechanism analysis:
it can test whether the same words are used in increasingly predictable
contexts over development and where inside the utterance the information
change occurs.
