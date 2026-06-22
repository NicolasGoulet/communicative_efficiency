# Route 1 Exhaustive Group-Comparison ANCOVA Gallery

This is a pre-supervisor selection gallery. It is intentionally built for choosing figures and language for the later supervisor report. The current supervisor-facing report is not modified.

The central question is the Route 1 question: at the same production effort, do older children produce utterances that are less unpredictable in context? The answer in this gallery is yes for the main real-child adjusted means and mostly yes in exact-effort checks.

## What The ANCOVA Is Doing

This report uses ANCOVA-style models because raw ANOVA would mostly ask whether age bins differ in total information, without separating that from the fact that older children produce longer utterances. Here, effort is controlled directly.

The real-child age-bin model is fit separately for each effort scale:

```text
sum_bits_k3 ~ C(age_bin) + effort_z + C(child_id)
context_gain ~ C(age_bin) + effort_z + C(child_id)
```

`effort_z` is one effort measure at a time: words, morphemes, CMU/pkg syllables, package syllables, or phonemes. The plotted adjusted means are predictions at average effort for that scale, averaged over child identities. So these plots are not raw age means.

The source-comparison models use:

```text
outcome ~ C(source_label) * C(age_bin) + effort_z + C(child_id)
```

The exact-effort models use exact effort values instead of only average effort:

```text
outcome ~ C(age_bin) * C(exact_effort) + C(child_id)
```

These exact-effort panels are the strongest check against the objection that the result is just MLU or utterance-length growth.

## Main Reading

- **Real child same-effort information:** Across effort scales, the adjusted start-to-end change ranges from -5.46 to -3.19 bits; the fitted linear age slope ranges from -0.62 to -0.29 bits per 6 months.
- **Exact-effort support:** Across the top exact effort values and all five effort scales, 51/60 exact-effort age slopes are downward; median slopes by effort scale range from -0.44 to -0.15 bits per 6 months.
- **Real child context gain:** Across effort scales, the adjusted start-to-end change ranges from -1.98 to -1.52 bits; the fitted linear age slope ranges from -0.31 to -0.25 bits per 6 months.
- **Generated controls:** random, n-gram, and LSTM controls are source-specific comparisons. Random is most different; LSTMs are closest; n-grams sit in between.
- **Caretakers:** the caregiver/CDS comparison is not a direct replication of the phonological CDS paper. That paper asks whether caregiver speech becomes more phonologically informative with child age. This report asks whether caretaker utterances are more Mistral-surprising at fixed utterance effort in local conversational context.

## Relation To The Frequency/Informativity Paper

The paper excerpt argues that caregiver-directed speech becomes phonologically more informative/less redundant as children age, while phone frequencies are comparatively stable. That is a parent-input result at the phonological-structure level.

Our current Route 1 result is a child-output result at the utterance-information level: children's own utterances become less unpredictable in context at the same production effort. These can coexist. A plausible developmental story is that input to children may become less redundant as children can process more, while children’s own productions become more conventional and contextually recoverable as they learn the language.

This report therefore separates the two claims: real-child fixed-effort output trajectories are the main Route 1 evidence; caretaker trajectories are a comparison; and frequency/informativity predictors are being saved for later frequency-control models.

## Part I: Figure Gallery

The figures are the main product, but each figure now has a short card explaining the model, how to read it, and why it matters.

### Real Child Age

#### Real children adjusted With-context information

**What is controlled:** Each panel is a separate ANCOVA, `sum_bits_k3 ~ C(age_bin) + effort_z + C(child_id)`. The effort variable is the panel title, centered/scaled within that model; plotted means are at average effort and averaged over child identities.

**How to read it:** Downward lines mean that, at the same effort scale and child-adjusted baseline, older children are less unpredictable in the preceding caretaker context.

**What it says here:** Across effort scales, the adjusted start-to-end change ranges from -5.46 to -3.19 bits; the fitted linear age slope ranges from -0.62 to -0.29 bits per 6 months. This is the ANCOVA version of the Route 1 fixed-effort claim.

![Real children adjusted With-context information](../figs/route1_exhaustive_ancova_gallery/real_age_adjusted_sum_bits_k3_by_effort.png)

#### Real children adjusted Context gain

**What is controlled:** Same real-child ANCOVA structure, but the outcome is `context_gain = sum_bits_k0 - sum_bits_k3`.

**How to read it:** Higher values mean the preceding context reduces surprisal more. A downward line means the k0-to-k3 reduction is smaller for older children at matched effort.

**What it says here:** Across effort scales, the adjusted start-to-end change ranges from -1.98 to -1.52 bits; the fitted linear age slope ranges from -0.31 to -0.25 bits per 6 months. This suggests the developmental decrease in k3 bits is not simply because older children receive more helpful local context.

![Real children adjusted Context gain](../figs/route1_exhaustive_ancova_gallery/real_age_adjusted_context_gain_by_effort.png)

### Source Comparisons

**Important reading note:** in every source-minus-real plot, real child utterances are the reference line at `0`. The real utterance value has been subtracted away, so the colored lines are not raw surprisal. They answer: at the same controlled effort, how many bits above or below real child utterances is this control source?

For example, a random line at `+20` means the random utterances are estimated to be 20 bits more surprising than real child utterances in that age bin and effort-controlled model. An LSTM line near `+3` means the LSTM is much closer to real children. A caretaker line below `0` means caretaker utterances are estimated to be less surprising than real child utterances under this same fixed-effort contrast.

#### Real vs generated adjusted With-context information

**What is controlled:** Omnibus child-source ANCOVA, `sum_bits_k3 ~ C(source) * C(age_bin) + effort_z + C(child_id)`, fit separately for each effort scale.

**How to read it:** The real-child line is compared with matched generated sources at the same adjusted effort. If controls sit above real children, they are more unpredictable than real utterances under the same context.

**What it says here:** Random is far above real children; n-grams are closer but still generally more surprising; LSTMs are closest but do not remove the real-child developmental pattern. This supports source specificity.

![Real vs generated adjusted With-context information](../figs/route1_exhaustive_ancova_gallery/child_sources_adjusted_sum_bits_k3_by_effort.png)

#### Real vs generated adjusted Context gain

**What is controlled:** Same source-by-age ANCOVA, but the outcome is context gain rather than k3 information.

**How to read it:** This separates “the utterance is predictable with context” from “the source benefits from context.”

**What it says here:** The generated controls do not all exploit context like real children. This is useful for arguing that the result is not only a scoring artifact.

![Real vs generated adjusted Context gain](../figs/route1_exhaustive_ancova_gallery/child_sources_adjusted_context_gain_by_effort.png)

#### Source-minus-real With-context information heatmaps

**What is controlled:** Pairwise source-vs-real ANCOVAs control effort and child identity before taking source-minus-real adjusted means.

**How to read it:** Red/positive cells mean the source is more unpredictable than real child utterances; blue/negative cells mean less unpredictable.

**What it says here:** The generated baselines are mostly positive, especially random and unigram. This is the broad visual screen for which controls are most different from real children.

![Source-minus-real With-context information heatmaps](../figs/route1_exhaustive_ancova_gallery/source_minus_real_sum_bits_k3_heatmaps_by_effort.png)

#### Source-minus-real Context gain heatmaps

**What is controlled:** Pairwise source-vs-real ANCOVAs for context gain.

**How to read it:** Positive cells mean the source gains more from context than real children; negative cells mean less.

**What it says here:** This helps separate high surprisal from poor context use. Some sources are more surprising and also benefit differently from context.

![Source-minus-real Context gain heatmaps](../figs/route1_exhaustive_ancova_gallery/source_minus_real_context_gain_heatmaps_by_effort.png)

#### Words source-minus-real With-context information lines

**What is controlled:** The model first estimates adjusted with-context information for real child utterances and for one comparison source at the same age bin, child-adjusted baseline, and effort scale. It then subtracts the real-child adjusted mean.

**How to read it:** The black zero line is real child utterances. A positive value means the comparison source is that many bits more surprising than real child utterances at the same controlled effort. A negative value means it is less surprising than real child utterances. Upward lines mean the source is moving farther away from real children over development.

**What it says here:** For words, Random changes from 22.59 to 57.27 bits (delta 34.68); Trigram changes from 3.93 to 12.60 bits (delta 8.67); the closest LSTM at the last age bin is LSTM k4 with a 3.13 bit gap. Use these line plots to pick the clearest source-comparison figure.

![Words source-minus-real With-context information lines](../figs/route1_exhaustive_ancova_gallery/nb_words_sum_bits_k3_source_minus_real_gap_lines.png)

#### Morphemes source-minus-real With-context information lines

**What is controlled:** The model first estimates adjusted with-context information for real child utterances and for one comparison source at the same age bin, child-adjusted baseline, and effort scale. It then subtracts the real-child adjusted mean.

**How to read it:** The black zero line is real child utterances. A positive value means the comparison source is that many bits more surprising than real child utterances at the same controlled effort. A negative value means it is less surprising than real child utterances. Upward lines mean the source is moving farther away from real children over development.

**What it says here:** For morphemes, Random changes from 19.54 to 47.91 bits (delta 28.36); Trigram changes from 3.97 to 12.68 bits (delta 8.70); the closest LSTM at the last age bin is LSTM k4 with a 3.88 bit gap. Use these line plots to pick the clearest source-comparison figure.

![Morphemes source-minus-real With-context information lines](../figs/route1_exhaustive_ancova_gallery/nb_morphemes_sum_bits_k3_source_minus_real_gap_lines.png)

#### Syllables: CMU/pkg source-minus-real With-context information lines

**What is controlled:** The model first estimates adjusted with-context information for real child utterances and for one comparison source at the same age bin, child-adjusted baseline, and effort scale. It then subtracts the real-child adjusted mean.

**How to read it:** The black zero line is real child utterances. A positive value means the comparison source is that many bits more surprising than real child utterances at the same controlled effort. A negative value means it is less surprising than real child utterances. Upward lines mean the source is moving farther away from real children over development.

**What it says here:** For syllables: cmu/pkg, Random changes from 16.09 to 33.25 bits (delta 17.15); Trigram changes from 3.95 to 12.04 bits (delta 8.09); the closest LSTM at the last age bin is LSTM k4 with a 4.72 bit gap. Use these line plots to pick the clearest source-comparison figure.

![Syllables: CMU/pkg source-minus-real With-context information lines](../figs/route1_exhaustive_ancova_gallery/nb_syllables_cmu_or_pkg_sum_bits_k3_source_minus_real_gap_lines.png)

#### Syllables: pkg source-minus-real With-context information lines

**What is controlled:** The model first estimates adjusted with-context information for real child utterances and for one comparison source at the same age bin, child-adjusted baseline, and effort scale. It then subtracts the real-child adjusted mean.

**How to read it:** The black zero line is real child utterances. A positive value means the comparison source is that many bits more surprising than real child utterances at the same controlled effort. A negative value means it is less surprising than real child utterances. Upward lines mean the source is moving farther away from real children over development.

**What it says here:** For syllables: pkg, Random changes from 16.83 to 34.37 bits (delta 17.54); Trigram changes from 3.99 to 12.11 bits (delta 8.12); the closest LSTM at the last age bin is LSTM k4 with a 4.98 bit gap. Use these line plots to pick the clearest source-comparison figure.

![Syllables: pkg source-minus-real With-context information lines](../figs/route1_exhaustive_ancova_gallery/nb_syllables_pkg_sum_bits_k3_source_minus_real_gap_lines.png)

#### Phonemes source-minus-real With-context information lines

**What is controlled:** The model first estimates adjusted with-context information for real child utterances and for one comparison source at the same age bin, child-adjusted baseline, and effort scale. It then subtracts the real-child adjusted mean.

**How to read it:** The black zero line is real child utterances. A positive value means the comparison source is that many bits more surprising than real child utterances at the same controlled effort. A negative value means it is less surprising than real child utterances. Upward lines mean the source is moving farther away from real children over development.

**What it says here:** For phonemes, Random changes from 14.62 to 29.23 bits (delta 14.61); Trigram changes from 4.08 to 12.19 bits (delta 8.11); the closest LSTM at the last age bin is LSTM k4 with a 6.05 bit gap. Use these line plots to pick the clearest source-comparison figure.

![Phonemes source-minus-real With-context information lines](../figs/route1_exhaustive_ancova_gallery/nb_phonemes_sum_bits_k3_source_minus_real_gap_lines.png)

#### Words source-minus-real Context gain lines

**What is controlled:** The same source-minus-real subtraction, but for context gain instead of total with-context information.

**How to read it:** Zero is real child utterances. Positive values mean the comparison source gains more from context than real children; negative values mean it gains less from context.

**What it says here:** For words, the largest final absolute context-gain gap is Caretaker at 4.43 bits. These are secondary to the k3 information gap lines.

![Words source-minus-real Context gain lines](../figs/route1_exhaustive_ancova_gallery/nb_words_context_gain_source_minus_real_gap_lines.png)

#### Morphemes source-minus-real Context gain lines

**What is controlled:** The same source-minus-real subtraction, but for context gain instead of total with-context information.

**How to read it:** Zero is real child utterances. Positive values mean the comparison source gains more from context than real children; negative values mean it gains less from context.

**What it says here:** For morphemes, the largest final absolute context-gain gap is Random at -4.58 bits. These are secondary to the k3 information gap lines.

![Morphemes source-minus-real Context gain lines](../figs/route1_exhaustive_ancova_gallery/nb_morphemes_context_gain_source_minus_real_gap_lines.png)

#### Syllables: CMU/pkg source-minus-real Context gain lines

**What is controlled:** The same source-minus-real subtraction, but for context gain instead of total with-context information.

**How to read it:** Zero is real child utterances. Positive values mean the comparison source gains more from context than real children; negative values mean it gains less from context.

**What it says here:** For syllables: cmu/pkg, the largest final absolute context-gain gap is Random at -5.09 bits. These are secondary to the k3 information gap lines.

![Syllables: CMU/pkg source-minus-real Context gain lines](../figs/route1_exhaustive_ancova_gallery/nb_syllables_cmu_or_pkg_context_gain_source_minus_real_gap_lines.png)

#### Syllables: pkg source-minus-real Context gain lines

**What is controlled:** The same source-minus-real subtraction, but for context gain instead of total with-context information.

**How to read it:** Zero is real child utterances. Positive values mean the comparison source gains more from context than real children; negative values mean it gains less from context.

**What it says here:** For syllables: pkg, the largest final absolute context-gain gap is Random at -5.05 bits. These are secondary to the k3 information gap lines.

![Syllables: pkg source-minus-real Context gain lines](../figs/route1_exhaustive_ancova_gallery/nb_syllables_pkg_context_gain_source_minus_real_gap_lines.png)

#### Phonemes source-minus-real Context gain lines

**What is controlled:** The same source-minus-real subtraction, but for context gain instead of total with-context information.

**How to read it:** Zero is real child utterances. Positive values mean the comparison source gains more from context than real children; negative values mean it gains less from context.

**What it says here:** For phonemes, the largest final absolute context-gain gap is Random at -5.26 bits. These are secondary to the k3 information gap lines.

![Phonemes source-minus-real Context gain lines](../figs/route1_exhaustive_ancova_gallery/nb_phonemes_context_gain_source_minus_real_gap_lines.png)

### Caretaker/CDS Comparison

#### Real child vs caretaker adjusted With-context information

**What is controlled:** Pairwise ANCOVA for real child vs caretaker speech, `sum_bits_k3 ~ C(source) * C(age_bin) + effort_z + C(child_id)`, fit separately for each effort scale.

**How to read it:** This is not the same as the phonological CDS paper. That paper asks whether caregiver speech becomes more phonologically informative with child age; this plot asks whether caretaker utterances become more Mistral-surprising at the same utterance effort in our Route 1 setup.

**What it says here:** Caretaker k3 bits show this pattern: Across effort scales, the adjusted start-to-end change ranges from -1.30 to -0.91 bits; the fitted linear age slope ranges from -0.14 to -0.11 bits per 6 months. This does not reproduce the paper's phone-level CDS-informativity claim; it is a different outcome and a fixed-effort utterance-level contrast.

![Real child vs caretaker adjusted With-context information](../figs/route1_exhaustive_ancova_gallery/real_caretaker_adjusted_sum_bits_k3_by_effort.png)

#### Real child vs caretaker adjusted Context gain

**What is controlled:** Same real-vs-caretaker pairwise ANCOVA, with context gain as the outcome.

**How to read it:** This asks whether caretaker speech benefits more or less from local context across the child-age timeline.

**What it says here:** Caretaker context gain shows this pattern: Across effort scales, the adjusted start-to-end change ranges from -2.50 to -2.38 bits; the fitted linear age slope ranges from -0.32 to -0.30 bits per 6 months. Treat this as a caregiver contrast, not as a direct replication of the phonological CDS paper.

![Real child vs caretaker adjusted Context gain](../figs/route1_exhaustive_ancova_gallery/real_caretaker_adjusted_context_gain_by_effort.png)

### Model Tests

#### real_age_ancova term-test heatmap

**What is tested:** The age-bin term in `outcome ~ C(age_bin) + effort_z + C(child_id)`.

**How to read it:** Darker cells mean stronger FDR-adjusted evidence that age bins differ after effort and child identity are controlled.

**What it says here:** This is the table-like statistical confirmation of the real-child adjusted age plots.

![real_age_ancova term-test heatmap](../figs/route1_exhaustive_ancova_gallery/real_age_ancova_term_test_fdr_heatmap.png)

#### child_source_omnibus term-test heatmap

**What is tested:** Source, age bin, and source-by-age interaction in the generated-source omnibus ANCOVA.

**How to read it:** Strong source-by-age cells mean the developmental trajectory differs by source, not just by overall source level.

**What it says here:** This is the omnibus support for comparing real children against generated baselines.

![child_source_omnibus term-test heatmap](../figs/route1_exhaustive_ancova_gallery/child_source_omnibus_term_test_fdr_heatmap.png)

#### pairwise_source_ancova term-test heatmap

**What is tested:** Pairwise real-vs-source ANCOVA terms for each source and effort scale.

**How to read it:** Use this as an audit map for which comparisons have strong age/source/source-by-age terms.

**What it says here:** The strongest rows are candidates for supervisor-report figures; the heatmap itself is appendix material.

![pairwise_source_ancova term-test heatmap](../figs/route1_exhaustive_ancova_gallery/pairwise_source_ancova_term_test_fdr_heatmap.png)

### Exact Effort

#### Real exact-effort With-context information age slopes

**What is controlled:** Exact-effort ANCOVA, `sum_bits_k3 ~ C(age_bin) * C(exact_effort) + C(child_id)`, for the 12 most frequent exact effort values in each effort scale.

**How to read it:** Each cell is an age slope within one exact effort value. Downward cells mean older children are less unpredictable at the exact same effort value.

**What it says here:** Across the top exact effort values and all five effort scales, 51/60 exact-effort age slopes are downward; median slopes by effort scale range from -0.44 to -0.15 bits per 6 months. This is the strongest guard against the result being only MLU.

![Real exact-effort With-context information age slopes](../figs/route1_exhaustive_ancova_gallery/real_exact_effort_age_slopes_sum_bits_k3.png)

#### Words exact-effort source gap slopes for With-context information

**What is controlled:** Exact-effort source-vs-real models, so source gaps are compared inside exact effort values rather than at only average effort.

**How to read it:** Positive cells mean the source-real unpredictability gap grows with age at that exact effort value.

**What it says here:** These are candidate appendix figures for showing that source-specific effects are not just effort-distribution artifacts.

![Words exact-effort source gap slopes for With-context information](../figs/route1_exhaustive_ancova_gallery/nb_words_exact_source_real_gap_slopes_sum_bits_k3.png)

#### Morphemes exact-effort source gap slopes for With-context information

**What is controlled:** Exact-effort source-vs-real models, so source gaps are compared inside exact effort values rather than at only average effort.

**How to read it:** Positive cells mean the source-real unpredictability gap grows with age at that exact effort value.

**What it says here:** These are candidate appendix figures for showing that source-specific effects are not just effort-distribution artifacts.

![Morphemes exact-effort source gap slopes for With-context information](../figs/route1_exhaustive_ancova_gallery/nb_morphemes_exact_source_real_gap_slopes_sum_bits_k3.png)

#### Syllables: CMU/pkg exact-effort source gap slopes for With-context information

**What is controlled:** Exact-effort source-vs-real models, so source gaps are compared inside exact effort values rather than at only average effort.

**How to read it:** Positive cells mean the source-real unpredictability gap grows with age at that exact effort value.

**What it says here:** These are candidate appendix figures for showing that source-specific effects are not just effort-distribution artifacts.

![Syllables: CMU/pkg exact-effort source gap slopes for With-context information](../figs/route1_exhaustive_ancova_gallery/nb_syllables_cmu_or_pkg_exact_source_real_gap_slopes_sum_bits_k3.png)

#### Syllables: pkg exact-effort source gap slopes for With-context information

**What is controlled:** Exact-effort source-vs-real models, so source gaps are compared inside exact effort values rather than at only average effort.

**How to read it:** Positive cells mean the source-real unpredictability gap grows with age at that exact effort value.

**What it says here:** These are candidate appendix figures for showing that source-specific effects are not just effort-distribution artifacts.

![Syllables: pkg exact-effort source gap slopes for With-context information](../figs/route1_exhaustive_ancova_gallery/nb_syllables_pkg_exact_source_real_gap_slopes_sum_bits_k3.png)

#### Phonemes exact-effort source gap slopes for With-context information

**What is controlled:** Exact-effort source-vs-real models, so source gaps are compared inside exact effort values rather than at only average effort.

**How to read it:** Positive cells mean the source-real unpredictability gap grows with age at that exact effort value.

**What it says here:** These are candidate appendix figures for showing that source-specific effects are not just effort-distribution artifacts.

![Phonemes exact-effort source gap slopes for With-context information](../figs/route1_exhaustive_ancova_gallery/nb_phonemes_exact_source_real_gap_slopes_sum_bits_k3.png)

#### Real exact-effort Context gain age slopes

**What is controlled:** Same exact-effort model, but the outcome is context gain.

**How to read it:** Each cell shows whether context gain changes with age within the exact same effort value.

**What it says here:** Across the top exact effort values and all five effort scales, 56/60 exact-effort age slopes are downward; median slopes by effort scale range from -0.55 to -0.36 bits per 6 months. This is a secondary context-use check.

![Real exact-effort Context gain age slopes](../figs/route1_exhaustive_ancova_gallery/real_exact_effort_age_slopes_context_gain.png)

#### Words exact-effort source gap slopes for Context gain

**What is controlled:** Exact-effort source-vs-real models for context gain.

**How to read it:** These show whether source differences in context benefit grow or shrink within exact effort values.

**What it says here:** Use these only if the supervisor wants the context-gain story; they are not the primary fixed-effort information claim.

![Words exact-effort source gap slopes for Context gain](../figs/route1_exhaustive_ancova_gallery/nb_words_exact_source_real_gap_slopes_context_gain.png)

#### Morphemes exact-effort source gap slopes for Context gain

**What is controlled:** Exact-effort source-vs-real models for context gain.

**How to read it:** These show whether source differences in context benefit grow or shrink within exact effort values.

**What it says here:** Use these only if the supervisor wants the context-gain story; they are not the primary fixed-effort information claim.

![Morphemes exact-effort source gap slopes for Context gain](../figs/route1_exhaustive_ancova_gallery/nb_morphemes_exact_source_real_gap_slopes_context_gain.png)

#### Syllables: CMU/pkg exact-effort source gap slopes for Context gain

**What is controlled:** Exact-effort source-vs-real models for context gain.

**How to read it:** These show whether source differences in context benefit grow or shrink within exact effort values.

**What it says here:** Use these only if the supervisor wants the context-gain story; they are not the primary fixed-effort information claim.

![Syllables: CMU/pkg exact-effort source gap slopes for Context gain](../figs/route1_exhaustive_ancova_gallery/nb_syllables_cmu_or_pkg_exact_source_real_gap_slopes_context_gain.png)

#### Syllables: pkg exact-effort source gap slopes for Context gain

**What is controlled:** Exact-effort source-vs-real models for context gain.

**How to read it:** These show whether source differences in context benefit grow or shrink within exact effort values.

**What it says here:** Use these only if the supervisor wants the context-gain story; they are not the primary fixed-effort information claim.

![Syllables: pkg exact-effort source gap slopes for Context gain](../figs/route1_exhaustive_ancova_gallery/nb_syllables_pkg_exact_source_real_gap_slopes_context_gain.png)

#### Phonemes exact-effort source gap slopes for Context gain

**What is controlled:** Exact-effort source-vs-real models for context gain.

**How to read it:** These show whether source differences in context benefit grow or shrink within exact effort values.

**What it says here:** Use these only if the supervisor wants the context-gain story; they are not the primary fixed-effort information claim.

![Phonemes exact-effort source gap slopes for Context gain](../figs/route1_exhaustive_ancova_gallery/nb_phonemes_exact_source_real_gap_slopes_context_gain.png)

## Part II: Audit Tables

The tables are here only to make the figures auditable. The full tables are CSV artifacts; the Markdown shows compact previews.

### CSV Artifacts

- `results/route1_exhaustive_ancova_gallery/effort_cell_summary.csv.gz`: aggregate k0/k3/context-gain cells by source, child, session, age bin, and exact effort value.
- `results/route1_exhaustive_ancova_gallery/ancova_term_tests.csv`: Wald term tests for age, source, and source-by-age ANCOVA terms.
- `results/route1_exhaustive_ancova_gallery/adjusted_marginal_means.csv`: adjusted marginal means used in the line figures.
- `results/route1_exhaustive_ancova_gallery/source_real_adjusted_contrasts.csv`: source-minus-real adjusted contrasts by age bin.
- `results/route1_exhaustive_ancova_gallery/top_exact_effort_values.csv`: top 12 exact real-child effort values per effort scale.
- `results/route1_exhaustive_ancova_gallery/exact_effort_adjusted_means.csv`: exact-effort adjusted real-child means.
- `results/route1_exhaustive_ancova_gallery/exact_effort_source_real_gaps.csv`: exact-effort source-minus-real gaps.
- `results/route1_exhaustive_ancova_gallery/figure_manifest.csv`: figure inventory.
- `results/route1_frequency_informativity_predictors/hash_frequency_predictors.csv.gz`: joinable exact-target frequency predictors keyed by `target_text_hash`, created as the safe first frequency-control layer inspired by the phonological CDS paper.

### Weighted Cell Counts

| source_label | Morphemes | Phonemes | Syllables: CMU/pkg | Syllables: pkg | Words |
| --- | --- | --- | --- | --- | --- |
| Real child | 446,985 | 446,985 | 446,985 | 446,985 | 446,985 |
| Random | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| Unigram | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| Bigram | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| Trigram | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| LSTM k3 | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| LSTM k4 | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| LSTM k5 | 446,508 | 446,508 | 446,508 | 446,508 | 446,508 |
| Caretaker | 668,903 | 668,903 | 668,903 | 668,903 | 668,903 |

### Exact Effort Values Used

| effort_col | effort_label | effort_value | real_weighted_rows |
| --- | --- | --- | --- |
| nb_words | Words | 1 | 164,264 |
| nb_words | Words | 2 | 93,824 |
| nb_words | Words | 3 | 74,048 |
| nb_words | Words | 4 | 49,421 |
| nb_words | Words | 5 | 28,966 |
| nb_words | Words | 6 | 15,966 |
| nb_words | Words | 7 | 8,606 |
| nb_words | Words | 8 | 4,725 |
| nb_words | Words | 9 | 2,656 |
| nb_words | Words | 10 | 1,594 |
| nb_words | Words | 11 | 896 |
| nb_words | Words | 12 | 591 |
| nb_morphemes | Morphemes | 1 | 153,917 |
| nb_morphemes | Morphemes | 2 | 81,932 |
| nb_morphemes | Morphemes | 3 | 69,111 |
| nb_morphemes | Morphemes | 4 | 52,894 |
| nb_morphemes | Morphemes | 5 | 35,618 |
| nb_morphemes | Morphemes | 6 | 21,774 |
| nb_morphemes | Morphemes | 7 | 12,587 |
| nb_morphemes | Morphemes | 8 | 7,378 |
| nb_morphemes | Morphemes | 9 | 4,295 |
| nb_morphemes | Morphemes | 10 | 2,526 |
| nb_morphemes | Morphemes | 11 | 1,568 |
| nb_morphemes | Morphemes | 12 | 1,020 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 1 | 121,839 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 2 | 94,414 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 3 | 72,346 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 4 | 55,990 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 5 | 37,176 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 6 | 25,149 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 7 | 14,786 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 8 | 9,357 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 9 | 5,500 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 10 | 3,433 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 11 | 2,261 |
| nb_syllables_cmu_or_pkg | Syllables: CMU/pkg | 12 | 1,468 |
| nb_syllables_pkg | Syllables: pkg | 1 | 116,868 |
| nb_syllables_pkg | Syllables: pkg | 2 | 87,470 |
| nb_syllables_pkg | Syllables: pkg | 3 | 67,784 |
| nb_syllables_pkg | Syllables: pkg | 4 | 57,850 |
| nb_syllables_pkg | Syllables: pkg | 5 | 40,416 |
| nb_syllables_pkg | Syllables: pkg | 6 | 28,337 |
| nb_syllables_pkg | Syllables: pkg | 7 | 17,456 |
| nb_syllables_pkg | Syllables: pkg | 8 | 11,345 |
| nb_syllables_pkg | Syllables: pkg | 9 | 6,545 |
| nb_syllables_pkg | Syllables: pkg | 10 | 4,337 |
| nb_syllables_pkg | Syllables: pkg | 11 | 2,639 |
| nb_syllables_pkg | Syllables: pkg | 12 | 1,836 |
| nb_phonemes | Phonemes | 2 | 58,082 |
| nb_phonemes | Phonemes | 3 | 46,836 |
| nb_phonemes | Phonemes | 4 | 36,656 |
| nb_phonemes | Phonemes | 5 | 33,496 |
| nb_phonemes | Phonemes | 6 | 32,426 |
| nb_phonemes | Phonemes | 7 | 32,405 |
| nb_phonemes | Phonemes | 8 | 29,827 |
| nb_phonemes | Phonemes | 9 | 24,255 |
| nb_phonemes | Phonemes | 10 | 22,351 |
| nb_phonemes | Phonemes | 11 | 20,107 |
| nb_phonemes | Phonemes | 12 | 17,339 |
| nb_phonemes | Phonemes | 13 | 14,198 |

### Strongest Adjusted Source-Real Gaps

| source | effort | outcome | age bin | source-real | real adj | source adj |
| --- | --- | --- | --- | --- | --- | --- |
| Bigram | Morphemes | Context gain | 030-035 | -3.11 | 13.82 | 10.71 |
| Bigram | Phonemes | Context gain | 030-035 | -3.14 | 13.86 | 10.72 |
| Bigram | Syllables: CMU/pkg | Context gain | 030-035 | -3.15 | 13.88 | 10.73 |
| Bigram | Syllables: pkg | Context gain | 030-035 | -3.15 | 13.88 | 10.73 |
| Bigram | Words | Context gain | 030-035 | -3.12 | 13.83 | 10.72 |
| Caretaker | Morphemes | Context gain | 054-059 | 4.89 | 12.15 | 17.05 |
| Caretaker | Phonemes | Context gain | 054-059 | 4.72 | 12.34 | 17.06 |
| Caretaker | Syllables: CMU/pkg | Context gain | 054-059 | 4.82 | 12.31 | 17.13 |
| Caretaker | Syllables: pkg | Context gain | 054-059 | 4.82 | 12.32 | 17.15 |
| Caretaker | Words | Context gain | 054-059 | 4.89 | 12.20 | 17.09 |
| LSTM k3 | Morphemes | Context gain | 006-023 | -2.86 | 13.96 | 11.10 |
| LSTM k3 | Phonemes | Context gain | 006-023 | -2.68 | 13.72 | 11.05 |
| LSTM k3 | Syllables: CMU/pkg | Context gain | 006-023 | -2.78 | 13.73 | 10.95 |
| LSTM k3 | Syllables: pkg | Context gain | 006-023 | -2.82 | 13.72 | 10.90 |
| LSTM k3 | Words | Context gain | 006-023 | -2.92 | 13.90 | 10.98 |
| LSTM k4 | Morphemes | Context gain | 006-023 | -2.90 | 13.96 | 11.07 |
| LSTM k4 | Phonemes | Context gain | 006-023 | -2.71 | 13.73 | 11.02 |
| LSTM k4 | Syllables: CMU/pkg | Context gain | 006-023 | -2.80 | 13.73 | 10.93 |
| LSTM k4 | Syllables: pkg | Context gain | 006-023 | -2.83 | 13.72 | 10.89 |
| LSTM k4 | Words | Context gain | 006-023 | -2.96 | 13.91 | 10.94 |
| LSTM k5 | Morphemes | Context gain | 006-023 | -2.78 | 13.98 | 11.20 |
| LSTM k5 | Phonemes | Context gain | 006-023 | -2.58 | 13.74 | 11.16 |
| LSTM k5 | Syllables: CMU/pkg | Context gain | 006-023 | -2.68 | 13.74 | 11.06 |
| LSTM k5 | Syllables: pkg | Context gain | 006-023 | -2.71 | 13.73 | 11.02 |
| LSTM k5 | Words | Context gain | 006-023 | -2.84 | 13.91 | 11.07 |
| Random | Morphemes | Context gain | 030-035 | -6.40 | 13.98 | 7.59 |
| Random | Phonemes | Context gain | 030-035 | -6.82 | 14.21 | 7.39 |
| Random | Syllables: CMU/pkg | Context gain | 030-035 | -6.69 | 14.16 | 7.47 |
| Random | Syllables: pkg | Context gain | 030-035 | -6.67 | 14.15 | 7.47 |
| Random | Words | Context gain | 030-035 | -6.10 | 13.84 | 7.74 |
| Trigram | Morphemes | Context gain | 030-035 | -2.08 | 13.82 | 11.74 |
| Trigram | Phonemes | Context gain | 030-035 | -2.09 | 13.86 | 11.76 |
| Trigram | Syllables: CMU/pkg | Context gain | 030-035 | -2.11 | 13.88 | 11.77 |
| Trigram | Syllables: pkg | Context gain | 030-035 | -2.11 | 13.88 | 11.77 |
| Trigram | Words | Context gain | 030-035 | -2.09 | 13.83 | 11.75 |
| Unigram | Morphemes | Context gain | 006-023 | -4.54 | 13.91 | 9.37 |
| Unigram | Phonemes | Context gain | 030-035 | -4.56 | 13.88 | 9.32 |
| Unigram | Syllables: CMU/pkg | Context gain | 030-035 | -4.56 | 13.89 | 9.33 |
| Unigram | Syllables: pkg | Context gain | 030-035 | -4.56 | 13.89 | 9.33 |
| Unigram | Words | Context gain | 006-023 | -4.55 | 13.87 | 9.32 |
| Bigram | Morphemes | With-context information | 060-065 | 16.76 | 21.07 | 37.83 |
| Bigram | Phonemes | With-context information | 060-065 | 15.76 | 22.92 | 38.68 |
| Bigram | Syllables: CMU/pkg | With-context information | 060-065 | 15.65 | 23.14 | 38.78 |
| Bigram | Syllables: pkg | With-context information | 060-065 | 15.70 | 23.18 | 38.88 |
| Bigram | Words | With-context information | 060-065 | 16.64 | 21.12 | 37.77 |
| Caretaker | Morphemes | With-context information | 048-053 | -7.50 | 33.57 | 26.07 |
| Caretaker | Phonemes | With-context information | 048-053 | -8.42 | 34.37 | 25.95 |
| Caretaker | Syllables: CMU/pkg | With-context information | 048-053 | -7.94 | 34.11 | 26.16 |
| Caretaker | Syllables: pkg | With-context information | 048-053 | -7.85 | 34.17 | 26.32 |
| Caretaker | Words | With-context information | 048-053 | -7.49 | 33.57 | 26.08 |
| LSTM k3 | Morphemes | With-context information | 060-065 | 4.84 | 23.00 | 27.84 |
| LSTM k3 | Phonemes | With-context information | 060-065 | 6.67 | 22.90 | 29.58 |
| LSTM k3 | Syllables: CMU/pkg | With-context information | 042-047 | 5.78 | 23.62 | 29.40 |
| LSTM k3 | Syllables: pkg | With-context information | 060-065 | 5.58 | 23.71 | 29.29 |
| LSTM k3 | Words | With-context information | 060-065 | 3.92 | 23.43 | 27.36 |
| LSTM k4 | Morphemes | With-context information | 042-047 | 4.57 | 23.36 | 27.93 |
| LSTM k4 | Phonemes | With-context information | 042-047 | 6.29 | 23.25 | 29.54 |
| LSTM k4 | Syllables: CMU/pkg | With-context information | 042-047 | 5.56 | 23.59 | 29.14 |
| LSTM k4 | Syllables: pkg | With-context information | 042-047 | 5.26 | 24.02 | 29.27 |
| LSTM k4 | Words | With-context information | 042-047 | 3.66 | 23.79 | 27.45 |

### Strongest Term Tests

| model | comparison | outcome | effort | term | p | FDR p |
| --- | --- | --- | --- | --- | --- | --- |
| child_source_omnibus | Real vs generated child sources | Context gain | Syllables: CMU/pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Unigram | With-context information | Words | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Unigram | With-context information | Phonemes | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Unigram | With-context information | Syllables: pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Unigram | With-context information | Syllables: CMU/pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Bigram | With-context information | Words | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Trigram | With-context information | Phonemes | C(source_label):C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | With-context information | Words | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Bigram | With-context information | Phonemes | C(source_label):C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | Context gain | Syllables: CMU/pkg | C(source_label) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | Context gain | Words | C(source_label) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | Context gain | Morphemes | C(source_label) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | Context gain | Syllables: pkg | C(source_label) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Trigram | With-context information | Words | C(source_label):C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | Context gain | Phonemes | C(source_label) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Trigram | With-context information | Syllables: CMU/pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Bigram | With-context information | Syllables: pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Trigram | With-context information | Morphemes | C(source_label):C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | With-context information | Morphemes | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Random | With-context information | Phonemes | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Random | With-context information | Phonemes | C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | With-context information | Syllables: CMU/pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Bigram | With-context information | Morphemes | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Bigram | With-context information | Syllables: CMU/pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Unigram | With-context information | Morphemes | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Random | With-context information | Syllables: pkg | C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | With-context information | Phonemes | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Trigram | With-context information | Syllables: pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| child_source_omnibus | Real vs generated child sources | With-context information | Syllables: pkg | C(source_label):C(age_bin) | <.001 | <.001 |
| pairwise_source_ancova | Real vs Random | With-context information | Syllables: CMU/pkg | C(age_bin) | <.001 | <.001 |

## Reading Notes

- Positive source-minus-real values mean the comparison source is more surprising than real child utterances after the model adjustment.
- The exact-effort heatmaps are the most direct guard against a pure MLU explanation because they avoid mixing different utterance sizes.
- These are candidate-selection figures. The final supervisor report should pick a much smaller subset.
- A separate predictor layer should be used for paper-style frequency controls. The safe first layer now exists as exact-target hash frequency; lexical frequency, phone unigram frequency, and phone-sequence informativity need a safer text-streaming pass because pandas' C parser segfaulted on the large text column in this environment.
