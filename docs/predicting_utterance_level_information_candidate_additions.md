# Candidate Additions For The Supervisor-Facing Report

This is a staging report. It summarizes recent side analyses and proposes what should be added to the supervisor-facing report later. It does **not** modify `docs/predicting_utterance_level_information_report.md`.

## Recommendation In One Page

I would add three things to the supervisor-facing report main text and keep the rest as appendix or future-work material:

1. **Main fixed-effort ANCOVA result:** same effort, older children are less unpredictable in context.
2. **Source and frequency controls:** random/ngram/LSTM controls do not explain the real-child pattern, and the age effect remains negative after exact-frequency/context controls.
3. **Reviewer robustness:** exact-effort slopes and scrambled-age nulls show the effect is not just MLU, binning, or sampling structure.

I would add Route 2 effort-as-outcome as an exploratory final subsection, not as a primary result yet.

## New Predictors And What They Mean

| predictor | built from | interpretation | why it matters |
| --- | --- | --- | --- |
| production effort | `nb_words`, `nb_morphemes`, syllable counts, `nb_phonemes` | How much linguistic material the target utterance contains. | Separates information growth from the fact that older children simply say more. |
| exact effort value | Exact observed word/morpheme/syllable/phoneme counts | Same-effort comparison inside one exact length value. | Strongest guard against an MLU-only critique. |
| context_entropy_bits | Mistral entropy over the next token after the preceding caretaker context | How uncertain the context is before the child speaks. | Operationalizes the Route 2/Xu idea that contextual uncertainty should affect production effort. |
| context_effort_words | Word count of the preceding context text | How much caregiver material preceded the target. | Controls for longer caregiver contexts mechanically giving more information. |
| question_type | Transparent rule-based parser of the last context line | Statement/fragment, yes-no question, wh-question, other question. | Questions can elicit longer/shorter child responses independent of efficiency. |
| exact_target_frequency_bits | -log2 smoothed recurrence of the target utterance hash in the real+caretaker reference set | Higher values mean the exact utterance is rarer/less conventional. | Addresses the Pawar/Cychosz frequency-vs-informativity concern using a stable first frequency-control layer. |
| source-minus-real gap | Adjusted source mean minus adjusted real-child mean | Real child utterances are zero; positive values are more surprising than real. | Makes random/ngram/LSTM/caretaker controls interpretable against the real-child baseline. |
| context gain | `sum_bits_k0 - sum_bits_k3` | How much local context reduces target uncertainty. | Separates being predictable in context from being low-information overall. |

## What The Refreshed Models Say

- **Core Route 1 fixed-effort result:** adjusted k3 information changes from -5.46 to -3.19 bits from first to last age bin across effort scales.
- **Exact-effort check:** 51/60 top exact-effort slopes are downward.
- **Frequency control:** exact-target frequency bits improve model fit by 0.0200 to 0.0308 R2 over the base effort+child model, while age coefficients remain negative.
- **Joint context+frequency control:** age coefficients remain negative across all effort measures; delta R2 ranges from 0.0210 to 0.0316.
- **Route 2 effort outcome:** context-uncertainty coefficients are positive for all five effort scales and p<.05 for 3/5 effort scales in this real-child extract.
- **Scrambled-age robustness:** real-child observed k3 slopes are outside the 95% scrambled null range for 5/5 effort scales.

## Candidate Figure Manifest

| candidate | placement | claim | caveat |
| --- | --- | --- | --- |
| Main Route 1 ANCOVA: fixed-effort information decreases with age | Main text candidate | At the same production effort and child-adjusted baseline, older children produce less Mistral-surprising utterances in context. |  |
| Exact-effort Route 1 slopes | Main text or appendix | The same downward tendency appears inside exact effort values. |  |
| Real vs generated controls | Main text candidate | Random, n-gram, and LSTM controls do not reproduce the real-child trajectory; LSTMs are closest, random is farthest. |  |
| Source-minus-real control gaps | Main text or appendix | Real child utterances are the zero line; controls sit above or below real children after effort control. |  |
| Frequency-controlled Route 1 age coefficients | Main text robustness candidate | The age effect remains negative after adding context and exact-target frequency controls. | Exact recurrence is a stable proxy; full phone/word informativity controls are not fully scored yet. |
| Incremental value of context and frequency controls | Appendix or short robustness paragraph | Frequency/conventionality explains meaningful variance but does not eliminate the Route 1 age effect. |  |
| Scrambled-age null check | Main text robustness candidate | Observed developmental slopes are separated from slopes obtained after scrambling age labels. | Current null uses 50 permutations; increase for final paper if this becomes a central claim. |
| Equalized age-bin bootstrap | Appendix robustness candidate | Age-bin trends survive a Pawar/Cychosz-style equalized sampling check. | Bins with fewer than 1,000 prepared rows are excluded from this check. |
| Route 2 effort-as-outcome coefficients | Exploratory section | Higher context uncertainty predicts more production effort most clearly for phoneme/syllable measures. | Real-child only in the current finite context-entropy extract; do not present as caretaker-comparative yet. |
| Caretaker-minus-real fixed-effort contrast | Optional contrast, not main claim | Caretaker speech is a comparison condition, not a direct replication of the phonological CDS paper. |  |

## Figure-By-Figure Candidate Additions

### Main Route 1 ANCOVA: fixed-effort information decreases with age

**Recommended placement:** Main text candidate

**Claim it supports:** At the same production effort and child-adjusted baseline, older children produce less Mistral-surprising utterances in context.

**Model/predictors:** `sum_bits_k3 ~ C(age_bin) + effort_z + C(child_id)`, fit separately for each effort scale.

**Why it is relevant:** This is the cleanest supervisor-facing version of the central Route 1 result.

![Main Route 1 ANCOVA: fixed-effort information decreases with age](../figs/route1_exhaustive_ancova_gallery/real_age_adjusted_sum_bits_k3_by_effort.png)

### Exact-effort Route 1 slopes

**Recommended placement:** Main text or appendix

**Claim it supports:** The same downward tendency appears inside exact effort values.

**Model/predictors:** `sum_bits_k3 ~ C(age_bin) * C(exact_effort) + C(child_id)`.

**Why it is relevant:** This is the strongest defense against the claim that the effect is only utterance-length/MLU growth.

![Exact-effort Route 1 slopes](../figs/route1_exhaustive_ancova_gallery/real_exact_effort_age_slopes_sum_bits_k3.png)

### Real vs generated controls

**Recommended placement:** Main text candidate

**Claim it supports:** Random, n-gram, and LSTM controls do not reproduce the real-child trajectory; LSTMs are closest, random is farthest.

**Model/predictors:** `sum_bits_k3 ~ C(source) * C(age_bin) + effort_z + C(child_id)`.

**Why it is relevant:** This shows the effect is source-specific, not just a scorer artifact or length matching artifact.

![Real vs generated controls](../figs/route1_exhaustive_ancova_gallery/child_sources_adjusted_sum_bits_k3_by_effort.png)

### Source-minus-real control gaps

**Recommended placement:** Main text or appendix

**Claim it supports:** Real child utterances are the zero line; controls sit above or below real children after effort control.

**Model/predictors:** Pairwise source-vs-real ANCOVAs; plotted value is adjusted source mean minus adjusted real-child mean.

**Why it is relevant:** This is the most intuitive way to explain what the controls mean.

![Source-minus-real control gaps](../figs/route1_exhaustive_ancova_gallery/nb_words_sum_bits_k3_source_minus_real_gap_lines.png)

### Frequency-controlled Route 1 age coefficients

**Recommended placement:** Main text robustness candidate

**Claim it supports:** The age effect remains negative after adding context and exact-target frequency controls.

**Model/predictors:** `sum_bits ~ age + effort + context_entropy + context_effort + question_type + exact_target_frequency_bits + C(child_id)`.

**Why it is relevant:** This addresses the Pawar/Cychosz frequency-vs-informativity concern and a likely peer-review question.

**Caveat:** Exact recurrence is a stable proxy; full phone/word informativity controls are not fully scored yet.

![Frequency-controlled Route 1 age coefficients](../figs/route1_portelance_xu_extension_suite/route1_age_coefficients_with_context_frequency_controls.png)

### Incremental value of context and frequency controls

**Recommended placement:** Appendix or short robustness paragraph

**Claim it supports:** Frequency/conventionality explains meaningful variance but does not eliminate the Route 1 age effect.

**Model/predictors:** Nested OLS models with child fixed effects and clustered standard errors.

**Why it is relevant:** Useful for explaining why frequency is not ignored, while keeping the main narrative clean.

![Incremental value of context and frequency controls](../figs/route1_portelance_xu_extension_suite/route1_joint_model_delta_r2.png)

### Scrambled-age null check

**Recommended placement:** Main text robustness candidate

**Claim it supports:** Observed developmental slopes are separated from slopes obtained after scrambling age labels.

**Model/predictors:** Weighted partial age slopes from effort-cell summaries, controlling effort and child identity.

**Why it is relevant:** Direct peer-review guardrail against age-bin/sampling artifacts.

**Caveat:** Current null uses 50 permutations; increase for final paper if this becomes a central claim.

![Scrambled-age null check](../figs/route1_portelance_xu_extension_suite/scrambled_age_null_sum_bits_k3.png)

### Equalized age-bin bootstrap

**Recommended placement:** Appendix robustness candidate

**Claim it supports:** Age-bin trends survive a Pawar/Cychosz-style equalized sampling check.

**Model/predictors:** 100 bootstrap samples per included age bin, up to 4,000 rows per bin, preserving observed rows.

**Why it is relevant:** Shows that the trend is not simply because some age bins have much more data.

**Caveat:** Bins with fewer than 1,000 prepared rows are excluded from this check.

![Equalized age-bin bootstrap](../figs/route1_portelance_xu_extension_suite/equalized_bootstrap_bits_per_word.png)

### Route 2 effort-as-outcome coefficients

**Recommended placement:** Exploratory section

**Claim it supports:** Higher context uncertainty predicts more production effort most clearly for phoneme/syllable measures.

**Model/predictors:** `log(effort) ~ age + context_entropy + context_effort + question_type + age:context_entropy + C(child_id)`.

**Why it is relevant:** This directly operationalizes the Xu email idea that children may shorten/lengthen depending on context.

**Caveat:** Real-child only in the current finite context-entropy extract; do not present as caretaker-comparative yet.

![Route 2 effort-as-outcome coefficients](../figs/route1_portelance_xu_extension_suite/route2_context_uncertainty_coefficients.png)

### Caretaker-minus-real fixed-effort contrast

**Recommended placement:** Optional contrast, not main claim

**Claim it supports:** Caretaker speech is a comparison condition, not a direct replication of the phonological CDS paper.

**Model/predictors:** Caretaker-minus-real adjusted means from the pairwise ANCOVA artifacts.

**Why it is relevant:** Useful for preventing overclaiming and for showing where child output sits relative to adult input.

![Caretaker-minus-real fixed-effort contrast](../figs/route1_portelance_xu_extension_suite/adult_likeness_caretaker_minus_real_sum_bits_k3.png)

## Compact Evidence Tables

### Real-Child Fixed-Effort ANCOVA Summary

| effort | start_bits | end_bits | start_to_end_delta | slope_bits_per_6mo |
| --- | --- | --- | --- | --- |
| Morphemes | 27.81 | 22.35 | -5.46 | -0.62 |
| Phonemes | 27.01 | 23.36 | -3.65 | -0.36 |
| Syllables: CMU/pkg | 27.03 | 23.69 | -3.35 | -0.34 |
| Syllables: pkg | 26.81 | 23.61 | -3.19 | -0.29 |
| Words | 27.72 | 22.62 | -5.10 | -0.55 |

### Exact-Effort Slope Summary

| effort | downward_exact_efforts | total_exact_efforts | median_slope |
| --- | --- | --- | --- |
| Morphemes | 11 | 12 | -0.42 |
| Phonemes | 12 | 12 | -0.36 |
| Syllables: CMU/pkg | 9 | 12 | -0.24 |
| Syllables: pkg | 9 | 12 | -0.15 |
| Words | 10 | 12 | -0.44 |

### Words Source-Minus-Real Gap Summary

| source | first_bin_gap_bits | last_bin_gap_bits | gap_change_bits |
| --- | --- | --- | --- |
| Caretaker | -4.67 | -5.47 | -0.81 |
| LSTM k4 | 1.96 | 3.13 | 1.17 |
| Random | 22.59 | 57.27 | 34.68 |
| Trigram | 3.93 | 12.60 | 8.67 |

### Route 1 Joint Model Summary

| model_id | effort_label | age_coef_fmt | age_p_fmt | delta_r2_fmt |
| --- | --- | --- | --- | --- |
| base_effort_child | Words | -0.732 | 0.005 | 0.0000 |
| frequency_control | Words | -0.572 | <.001 | 0.0308 |
| joint_context_frequency | Words | -0.511 | 0.002 | 0.0316 |
| base_effort_child | Morphemes | -1.038 | <.001 | 0.0000 |
| frequency_control | Morphemes | -0.811 | <.001 | 0.0300 |
| joint_context_frequency | Morphemes | -0.752 | <.001 | 0.0309 |
| base_effort_child | Syllables: CMU/pkg | -0.360 | 0.041 | 0.0000 |
| frequency_control | Syllables: CMU/pkg | -0.258 | 0.033 | 0.0235 |
| joint_context_frequency | Syllables: CMU/pkg | -0.206 | 0.067 | 0.0244 |
| base_effort_child | Syllables: pkg | -0.278 | 0.099 | 0.0000 |
| frequency_control | Syllables: pkg | -0.173 | 0.181 | 0.0255 |
| joint_context_frequency | Syllables: pkg | -0.123 | 0.287 | 0.0265 |
| base_effort_child | Phonemes | -0.493 | 0.028 | 0.0000 |
| frequency_control | Phonemes | -0.353 | 0.040 | 0.0200 |
| joint_context_frequency | Phonemes | -0.301 | 0.059 | 0.0210 |

### Route 2 Context-Uncertainty Coefficients

| effort_label | coef_fmt | p_fmt | age_interaction_coef_fmt | age_interaction_p_fmt |
| --- | --- | --- | --- | --- |
| Words | 0.0019 | 0.428 | -0.0031 | 0.082 |
| Morphemes | 0.0035 | 0.134 | -0.0036 | 0.052 |
| Syllables: CMU/pkg | 0.0060 | 0.005 | -0.0036 | 0.042 |
| Syllables: pkg | 0.0068 | 0.002 | -0.0040 | 0.026 |
| Phonemes | 0.0094 | <.001 | -0.0052 | 0.024 |

### Scrambled-Age Null Summary

| source_label | effort_label | observed_fmt | null_range | empirical_p_fmt | outside_null_95 |
| --- | --- | --- | --- | --- | --- |
| Caretaker | Words | 0.087 | [-0.027, 0.028] | 0.020 | True |
| Real child | Words | -0.560 | [-0.050, 0.042] | 0.020 | True |
| Caretaker | Morphemes | 0.137 | [-0.019, 0.035] | 0.020 | True |
| Real child | Morphemes | -0.611 | [-0.046, 0.051] | 0.020 | True |
| Caretaker | Syllables: CMU/pkg | 0.067 | [-0.021, 0.020] | 0.020 | True |
| Real child | Syllables: CMU/pkg | -0.292 | [-0.052, 0.029] | 0.020 | True |
| Caretaker | Syllables: pkg | 0.074 | [-0.024, 0.016] | 0.020 | True |
| Real child | Syllables: pkg | -0.218 | [-0.049, 0.039] | 0.020 | True |
| Caretaker | Phonemes | 0.067 | [-0.015, 0.022] | 0.020 | True |
| Real child | Phonemes | -0.295 | [-0.033, 0.032] | 0.020 | True |

## Feature Status / Do Not Overclaim

| feature | status | artifact | peer_review_reason |
| --- | --- | --- | --- |
| Context uncertainty | implemented | context_entropy_bits in analysis rows | Tests whether effort/information effects are actually context-sensitive. |
| Context effort | implemented | context_effort_words | Controls for the amount of preceding caregiver material. |
| Question type | implemented, coarse | question_type | Questions can mechanically elicit different child response lengths. |
| Exact target recurrence / frequency bits | implemented | exact_target_frequency_bits from hash_frequency_predictors.csv.gz | Separates age effects from children/caretakers using more repeated conventional utterances. |
| Word-unigram and phone-bigram informativity | implemented in code, not full-run completed here | src/build_route1_frequency_informativity_predictors.py --mode text | Closest analogue to Pawar/Cychosz frequency-vs-informativity controls; full run needs a safer long text pass. |
| Full response-space entropy | pilot-only, not full scored | response_entropy pilot reports | Would directly quantify uncertainty over possible child responses, but full Mila-scale generation is still a separate run. |

## Suggested Insertions For The Future Supervisor Report

### Main Result Paragraph

> At fixed production effort, older children's utterances are less unpredictable in their local conversational context. This pattern holds across effort definitions and is supported by exact-effort checks, so it is not simply an utterance-length or MLU artifact.

### Controls Paragraph

> The developmental pattern is source-specific: generated controls remain more surprising than real child utterances at matched effort, with random controls farthest away and LSTM controls closest. The age effect also remains negative after adding context uncertainty, context effort, question type, and exact-target frequency controls.

### Robustness Paragraph

> Scrambled-age checks and equalized age-bin bootstraps support the interpretation that the effect is developmental rather than a byproduct of age-bin size or sampling structure.

### Exploratory Route 2 Paragraph

> As a complementary exploratory analysis, context uncertainty weakly predicts child production effort, especially for phoneme and syllable effort. This supports the planned Route 2 question, but the current context-entropy extract is real-child only, so it should not yet be framed as a full child-vs-caretaker comparison.

## Saved Companion Files

```text
results/route1_portelance_xu_extension_suite/candidate_additions/candidate_additions_manifest.csv
results/route1_portelance_xu_extension_suite/candidate_additions/candidate_predictor_dictionary.csv
```
