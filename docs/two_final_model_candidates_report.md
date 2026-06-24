# Two Possible Final Models To Discuss

This is a side report for choosing the final model direction. It is not the
current supervisor-facing report.

The first four models form the cumulative core:

```text
M1: sum_bits ~ age + effort
M2: sum_bits ~ age + effort + child identity
M3: sum_bits ~ age + effort + age:effort + child identity
M4: sum_bits ~ age + effort + age:effort
               + parent context effort + context entropy
               + child identity
```

The question for the final model is what we want the last step to add. I see
two clean options.

## How Size Is Controlled

The size issue is the central design problem. Raw total `sum_bits` is strongly
tied to utterance length: older children tend to produce longer utterances, and
longer utterances mechanically accumulate more total bits. So a raw age trend
would mostly rediscover MLU.

We control size in three related ways.

### 1. Effort As A Covariate

The basic model includes a child-utterance effort term:

```text
sum_bits ~ age + effort + ...
```

For the word-count version, this means the age coefficient is interpreted after
adjusting for the number of words in the child utterance. The same logic can be
repeated with morphemes, syllables, or phonemes.

This is not the same as saying all utterances have the same length. It means
the regression estimates the age relation after accounting for the expected
increase in `sum_bits` associated with effort.

### 2. Fixed-Effort Prediction Lines

The plots make the size control more concrete. A line labelled `5` words is
not a raw average of all utterances at that age. It is the model prediction for
utterances held at exactly 5 words while age changes.

So the visual question is:

> At the same utterance size, does predicted `sum_bits` go up or down with age?

This is why the fixed-effort plots are more important than raw age averages.

### 3. Exact-Length Models

The strongest MLU check uses exact length as a category:

```text
sum_bits ~ age + C(exact word count) + age:C(exact word count) + ...
```

This lets each exact word count have its own baseline and, in the interaction
version, its own age slope. MLU cannot explain a slope estimated inside the
two-word stratum, the three-word stratum, and so on, because every utterance in
that comparison has the same word count.

In the already-fit exact-length model without context controls, the primary
row-level estimator has downward age slopes for `9/12` exact word lengths. The
upward slopes are concentrated in sparser longer lengths (`10-12` words).

![Exact-length age slopes](../figs/route1_child_length_controlled_model_suite/mlu_proof_exact_length_age_slopes.png)

![Exact-length estimator comparison](../figs/route1_child_length_controlled_model_suite/f19_k3_nb_words_estimator_mean_lines.png)

## Why Not Just Plain OLS?

Plain OLS with independent errors would be too naive because the data are
repeated utterances from the same children, nested in sessions across time.
Rows from the same child are correlated, and sessions with many utterances can
otherwise dominate the analysis.

The current main estimator is not naive OLS. It is:

```text
OLS + child fixed intercepts + child-clustered standard errors
```

That does three things:

| Component | What it does |
| --- | --- |
| OLS mean model | Keeps coefficients and fixed-effort predictions easy to interpret on the additive bits scale. |
| Child fixed intercepts | Controls stable differences between children, corpora, and child baselines. |
| Child-clustered SE | Adjusts uncertainty because utterances from the same child are not independent. |

But it is still reasonable to ask whether a repeated-measures estimator should
be preferred. We already fit those checks in the child-length-controlled model
suite.

| Estimator family | What it adds |
| --- | --- |
| Session/effort-cell OLS | Aggregates utterances into child-session-exact-effort cells so high-row-count sessions have less leverage. |
| GEE grouped by child | Estimates a population-average relation while modeling within-child dependence. |
| Gamma/log GLM or GEE | Checks whether results depend on Gaussian errors for positive, right-skewed total bits. |
| MixedLM random child intercept | Treats child baselines as random effects rather than fixed intercepts. |
| MixedLM random age slope | Lets children differ in developmental slope; useful but sometimes unstable. |
| MixedLM child + session intercepts | Represents utterances nested inside sessions inside children. |

My current read is:

> Use OLS with child fixed effects and child-clustered SE for the main
> supervisor-facing line because it is transparent. Use GEE and mixed models as
> repeated-measures robustness checks. Do not defend plain independent-row OLS.

The existing estimator grid supports this strategy, but with an important
qualification. In the exact-length models, short and middle word-count slices
remain downward across the displayed OLS-cluster, GEE, Gamma/log, random
intercept, and session-intercept variants. The longer exact-length slices are
more mixed. That is not a reason to hide the exact-length model; it is exactly
why it is useful. It shows where the fixed-effort effect is stable and where
the developmental pattern may differ for longer utterances. The random-age-slope
mixed model is less stable and should be treated as diagnostic rather than
headline evidence.

![Estimator slope heatmap](../figs/route1_child_length_controlled_model_suite/slope_heatmap_formula_by_estimator.png)

![Variance explained by formula and estimator](../figs/route1_child_length_controlled_model_suite/variance_explained_by_formula_estimator.png)

## Same Fixed-Effort Plots With Other Estimators

The plots below use the same visual logic as the supervisor-facing report:
predicted `sum_bits` is plotted through age while the child utterance is held
at a fixed word count. To avoid a noisy wall of lines, each panel shows three
representative lengths: 2, 6, and 10 words.

The panels are different estimator/repeated-measures structures. The important
comparison is the slope shape inside each panel. The absolute vertical
intercepts are not always directly comparable across estimator families because
some models predict population-average lines and others include different
fixed/random intercept structures.

| Plot | What it corresponds to |
| --- | --- |
| F01 | Model 2 analogue: age + effort + child identity. |
| F02 | Model 3 analogue: adds `age:effort`. |
| F10 | Closest already-fit estimator-grid analogue to the context-control model; it includes parent context effort, context entropy, `age:effort`, child identity, and question type. |
| F19 | Exact-length no-question MLU check. |
| F21 | Exact-length context-control MLU check; this already-fit grid includes question type. |

The exact no-question M4 union model that we put in the supervisor-facing
report exists as the primary row-level model. The full estimator-grid version
available here is not exactly the same because it includes question type, so I
would present it as a robustness analogue rather than as the preferred M4
formula.

![M2 analogue fixed-word estimator panels](../figs/two_final_model_candidates_report/f01_m2_analogue_fixed_word_estimator_panels.png)

![M3 analogue fixed-word estimator panels](../figs/two_final_model_candidates_report/f02_m3_analogue_fixed_word_estimator_panels.png)

![Context-control fixed-word estimator panels](../figs/two_final_model_candidates_report/f10_context_controls_fixed_word_estimator_panels.png)

![Exact-length fixed-word estimator panels](../figs/two_final_model_candidates_report/f19_exact_length_fixed_word_estimator_panels.png)

![Exact-length context-control fixed-word estimator panels](../figs/two_final_model_candidates_report/f21_exact_length_context_fixed_word_estimator_panels.png)

The visual read is that M2, M3, and the context-control analogue keep the same
basic fixed-effort story across the repeated-measures checks: the age lines are
usually downward, even if the aggregate/GEE/mixed versions flatten the effect
relative to the row-level child-fixed-effect model. The exact-length plots are
the strongest guard against the "this is just MLU" critique, but they also show
a real boundary condition: the 2-word and 6-word slices are downward across the
displayed estimators, while the 10-word slice is upward in most additive-scale
exact-length variants. I would describe that directly. The claim should not be
"every exact length decreases." The cleaner claim is "the effect is robust for
short and middle same-length utterances, while longer exact-length utterances
may follow a different developmental trajectory."

The plotted slope values are saved here:

```text
results/two_final_model_candidates_report/fixed_word_estimator_panel_slopes.csv
```

## Candidate A: Context As Mechanism

### What This Adds After Model 4

Model 4 treats context variables as controls. It asks whether the age effect
remains after accounting for context length and context uncertainty.

The mechanism version asks a stronger question:

> Does the developmental age effect itself change depending on context
> uncertainty?

That is a different claim. It moves from "the age effect survives context
controls" to "context may shape the developmental effect."

### Clean Formula

```text
sum_bits ~ age + effort + age:effort
         + parent context effort + context entropy
         + age:context entropy
         + child identity
```

I would keep this version free of question type. The important new term is
`age:context entropy`.

### What Each New Predictor Is Doing

| Predictor | Role |
| --- | --- |
| Parent context effort | Controls how much linguistic material is available in the fixed k3 context. |
| Context entropy | Controls how uncertain the preceding context is. |
| Age x context entropy | Tests whether the age slope differs in more versus less uncertain contexts. |

### What I Would Show

I would not lead with a big coefficient table. I would show:

1. A small formula box showing that this is Model 4 plus `age:context entropy`.
2. One compact coefficient card for `age`, `context entropy`, and
   `age:context entropy`.
3. One plot with predicted `sum_bits` by age at fixed word counts, split into
   low, medium, and high context-entropy settings.

The plot would answer the model visually:

> Are the age lines equally downward in all contexts, or is the developmental
> decrease stronger in some context-entropy settings?

### Already-Fit Estimator Versions

The closest already-fit no-question mechanism screen is formula `F27` in the
formula-permutation estimator report:

```text
mean_sum_bits ~ age + effort + age:effort
              + parent context effort + context entropy
              + age:context entropy
              + child identity
```

This is an aggregate child-session/effort-band estimator screen rather than the
primary row-level supervisor model, but it is useful because it has OLS-cluster,
GEE, Gamma/log, and MixedLM versions already fit.

| Estimator | Scale | Age x context entropy | p | Read |
| --- | --- | ---: | ---: | --- |
| OLS + child FE + clustered SE | additive bits | -0.079 | .359 | No strong evidence for mechanism. |
| GEE Gaussian | additive bits | -0.079 | .345 | Same substantive read as OLS-cluster. |
| GEE Gamma/log | log mean bits | -0.0025 | .042 | Suggests a small negative interaction on the log scale. |
| GLM Gamma/log | log mean bits | -0.0025 | .010 | Same direction on the log scale. |
| MixedLM random child intercept | additive bits | -0.079 | .121 | Same direction, not conventionally clear. |
| MixedLM random age slope | additive bits | -0.084 | .102 | Same direction, but random-slope models are diagnostic. |

![F27 estimator age lines](../figs/route1_formula_permutation_estimator_report/f27_aggregate_estimator_screen_age_lines.png)

![F27 fixed-effort estimator lines](../figs/route1_formula_permutation_estimator_report/f27_aggregate_estimator_fixed_effort_age_lines.png)

![F27 term effect forest](../figs/route1_formula_permutation_estimator_report/f27_term_effect_forest.png)

This makes Candidate A scientifically interesting but not the cleanest final
slide. The interaction direction is mostly negative, but it is not uniformly
strong across estimators, and the screen is aggregate rather than the exact
row-level no-question model.

### How I Would Describe It

I would say:

> The previous model showed that the developmental decrease in utterance-level
> information is not explained away by context length or context entropy. This
> model asks whether context uncertainty changes the developmental slope itself.
> In other words, context is no longer only a control variable; it becomes a
> candidate mechanism.

### What It Would Mean

If `age:context entropy` is near zero:

> The age effect appears fairly stable across context-entropy levels. That would
> support the simpler Model 4 interpretation.

If `age:context entropy` is clearly nonzero:

> The developmental change depends on the kind of context. Then the final story
> should become more mechanistic: children may become especially efficient in
> some context types but not others.

### Main Caveat

This should not be overclaimed as the final response-space entropy story.
Current context entropy is a useful context-predictability control, but it is
not the same as estimating the full distribution of possible child responses.

## Candidate B: Real Children Versus Baselines

### What This Adds After Model 4

Models 1-4 ask whether real child utterances show a developmental fixed-effort
age effect.

The source-comparison model asks a different final question:

> Is the real-child developmental trajectory different from matched generated
> baselines and caretaker speech?

This is not a mechanism model. It is a specificity model. It asks whether the
real child pattern is special, or whether the same pattern appears in random,
n-gram, LSTM, or caretaker controls.

### Clean Formula Options

For paired generated baselines, the cleanest version is often a gap model:

```text
source_minus_real_sum_bits ~ age + effort + child identity
```

where:

```text
source_minus_real_sum_bits = generated_or_control_sum_bits - real_child_sum_bits
```

A direct pooled version is:

```text
sum_bits ~ source + age + effort
         + source:age + source:effort + age:effort
         + source:age:effort
         + child identity
```

The important terms are `source:age` and `source:age:effort`: they ask whether
the developmental slope differs by source at the same production effort.

### What Each New Predictor Is Doing

| Predictor | Role |
| --- | --- |
| Source | Distinguishes real child utterances, generated controls, LSTM controls, and caretaker speech. |
| Source x age | Tests whether the developmental trajectory differs by source. |
| Source x age x effort | Tests whether source differences in developmental trajectory depend on utterance length. |
| Source-minus-real gap | A paired way to ask how far each control is from the real utterance in the same context. |

### Current Evidence Already Available

The existing real-vs-controls report already contains a usable fixed-effort
comparison layer. Under the simple identity-plus-effort comparison, the real
child fixed-effort slope is downward for all 12 fixed word-count lines:

| Source | Real slope, bits/6 months | Source slope, bits/6 months | Source minus real slope | Direction read |
| --- | ---: | ---: | ---: | --- |
| Random | -0.735 | 1.068 | 1.803 | Random goes upward while real children go downward. |
| Unigram | -0.735 | -0.125 | 0.610 | Unigram decreases, but much less than real children. |
| Bigram | -0.735 | -0.134 | 0.601 | Bigram decreases, but much less than real children. |
| Trigram | -0.735 | -0.092 | 0.643 | Trigram decreases, but much less than real children. |
| LSTM k3 | -0.735 | -0.279 | 0.456 | LSTM decreases, but less than real children. |
| LSTM k4 | -0.735 | -0.351 | 0.384 | LSTM decreases, but less than real children. |
| LSTM k5 | -0.735 | -0.363 | 0.372 | LSTM decreases, but less than real children. |
| Caretaker | -0.735 | 0.172 | 0.907 | Caretaker speech goes upward while real children go downward. |

![Real versus random fixed-effort lines](../figs/route1_real_vs_controls_context_report/random_m2_k3_fixed_word_regression_lines.png)

![Real versus LSTM fixed-effort lines](../figs/route1_real_vs_controls_context_report/lstm_m2_k3_fixed_word_regression_lines.png)

![Real versus caretaker fixed-effort lines](../figs/route1_real_vs_controls_context_report/caretaker_m2_k3_fixed_word_regression_lines.png)

There is also an exact-effort/source-comparison layer from the exhaustive
ANCOVA gallery. This is not a GEE/Mixed estimator grid, but it is another
already-fit way of protecting the source comparison from the MLU objection:
the source-minus-real gaps are estimated inside exact effort values and across
effort scales.

![Source-by-age term tests](../figs/route1_exhaustive_ancova_gallery/child_source_omnibus_term_test_fdr_heatmap.png)

![Exact-effort source-minus-real slopes](../figs/route1_exhaustive_ancova_gallery/nb_words_exact_source_real_gap_slopes_sum_bits_k3.png)

### What I Would Show

I would show:

1. One fixed-effort line plot comparing real children to a weak control
   such as random.
2. One fixed-effort line plot comparing real children to a stronger control
   such as LSTM.
3. One compact slope-difference table across all controls.

The plot logic is simple:

> At the same word count, does the real-child line move through age differently
> from the lines produced by matched controls?

### How I Would Describe It

I would say:

> The first four models establish the fixed-effort developmental pattern within
> real child speech. This final model asks whether that pattern is specific to
> real child utterances. Generated controls and caretaker speech are scored in
> the same framework, so if the same developmental trajectory appears
> everywhere, the result may be a scoring or length artifact. If the real-child
> trajectory differs, then the pattern is more plausibly tied to children's
> actual language use.

### What It Would Mean

If controls look like real children:

> The developmental slope may reflect scoring mechanics, changing vocabulary
> distributions, or shared corpus structure rather than something specific to
> child utterance choice.

If real children differ from controls:

> The result is stronger: it is not just that fixed-effort `sum_bits` decreases
> with age, but that the real-child trajectory is sharper or differently shaped
> than plausible generated or caretaker alternatives.

### Main Caveat

This does not explain why the real-child pattern happens. It tests whether the
pattern is source-specific. If we choose this as the final model, the report
ends with specificity, not mechanism.

The current source-comparison evidence is strongest as fixed-effort OLS/ANCOVA
and paired-gap evidence. A full GEE/Mixed source-comparison estimator grid would
be a good next robustness layer if Candidate B becomes the final model, but the
already-fit figures are enough to decide whether this direction belongs in the
supervisor report.

## Recommendation

I would choose the final model based on the meeting goal:

| If the final question is... | Choose... | Why |
| --- | --- | --- |
| "Why might the age effect happen?" | Candidate A: context as mechanism | It tests whether context uncertainty changes the age slope. |
| "Is the child pattern real or just an artifact?" | Candidate B: real versus baselines | It tests whether real children differ from generated and caretaker controls. |

My preference for a first supervisor-facing report would be Candidate B. It is
easier to explain, already has strong saved figures, and directly protects the
core claim from the criticism that the pattern is just a length/scoring
artifact. Candidate A is scientifically interesting, but it depends more heavily
on how comfortable we are with the current context-entropy predictor.
