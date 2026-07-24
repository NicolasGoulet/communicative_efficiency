# Corrected Cross-Fitted Bayes-Derived PBM Report

## Executive Result

The Bayes identity does not define a fundamentally different kind of surprisal. It rewrites the same conditional probability:

<div style="margin:1.2em auto;padding:0.9em 1.2em;max-width:760px;text-align:center;background:#f5f7f6;border-left:4px solid #2f6f73;font-family:Georgia,serif;font-size:1.18em" role="math">−log<sub>2</sub> <i>p</i>(<i>u</i> | <i>c</i>, <i>a</i>) = −log<sub>2</sub> <i>p</i>(<i>u</i> | <i>a</i>) − log<sub>2</sub>[<i>p</i>(<i>c</i> | <i>u</i>, <i>a</i>) / <i>p</i>(<i>c</i> | <i>a</i>)]</div>

Direct Mistral scoring estimates `p(u | c)` in one neural model. This corrected analysis instead estimates an age-conditioned utterance prior and a separate context-evidence term, then normalizes those scores over the five matched PBM candidates for each row. It is therefore an **alternative Bayes-derived candidate scorer**, not a replacement for Mistral and not unrestricted surprisal over all possible utterances.

After removing corpus leakage, the real child utterance has mean five-way candidate probability **40.0%**, is ranked first on **43.7%** of rows, and is in the top two on **68.6%**. Five-way chance for rank 1 is 20%. The prior alone ranks the real child first on 42.9%; adding context evidence raises this to 43.7%. Thus the corrected result is real, but it is driven primarily by the utterance prior, with a smaller incremental contribution from context compatibility.

## What Was Fixed

The previous n-gram pilot had three problems that prevent substantive interpretation: PBM rows occurred in its training data, `p(c)` was omitted, and an order-three reverse likelihood allowed only the candidate's final word to affect the first context token. The corrected estimator now:

- holds out the entire evaluated corpus—Brown, Manchester, or Providence—while training each fold;
- trains additively by age, using only the target age bin and earlier bins;
- maps unseen prior tokens to an explicit `<unk>` state;
- uses all candidate unigrams/bigrams and all retained context tokens in a contrastive matched-versus-shuffled evidence model;
- assigns neutral evidence to an empty context;
- writes separate prior, context-evidence, and combined score columns;
- normalizes the combined scores within each row's available real/random/unigram/bigram/trigram candidate set.

For candidate set `A_c`, the reported probability is

<div style="margin:1.2em auto;padding:0.9em 1.2em;max-width:820px;text-align:center;background:#f5f7f6;border-left:4px solid #2f6f73;font-family:Georgia,serif;font-size:1.12em" role="math"><i>q</i><sub>A</sub>(<i>u</i> | <i>c</i>, <i>a</i>) = 2<sup><i>S</i>(<i>u</i>,<i>c</i>,<i>a</i>)</sup> / Σ<sub><i>v</i>∈<i>A</i><sub>c</sub></sub> 2<sup><i>S</i>(<i>v</i>,<i>c</i>,<i>a</i>)</sup>, &nbsp; <i>S</i> = log<sub>2</sub> p̂(<i>u</i> | <i>a</i>) + Ê(<i>c</i>,<i>u</i>,<i>a</i>)</div>

Here `E_hat` is a contrastive estimate of the context likelihood ratio, not a literal neural sequence probability. Candidate-set Bayes surprisal is `-log2 q_A`.

## Audit And Held-Out Validation

The scorer wrote **2,232,524** rows. Every output group sums to one within floating-point tolerance, and all three corpus folds passed the predeclared held-out matched-versus-shuffled context check.

| held-out corpus | validation pairs | matched accuracy | matched − shuffled bits | passed | training rows | excluded own-corpus rows |
| --- | --- | --- | --- | --- | --- | --- |
| Brown | 39,069 | 62.2% | 0.281 | Yes | 1,047,663 | 92,555 |
| Manchester | 140,015 | 58.8% | 0.271 | Yes | 907,604 | 232,614 |
| Providence | 90,547 | 58.4% | 0.327 | Yes | 1,018,879 | 121,339 |

![Held-out context validation](../figs/corrected_pbm_bayes_report/heldout_context_validation.png)

The validation accuracy is modest rather than near-perfect. That is appropriate to report: the context term contains held-out lexical/discourse compatibility signal, but it is not a complete model of conversational meaning.

## PBM Candidate Results

| source | n | mean candidate probability | median candidate probability | rank-1 rate | prior bits/word | mean context evidence bits |
| --- | --- | --- | --- | --- | --- | --- |
| Real child | 446,508 | 40.0% | 21.3% | 43.7% | 11.521 | -0.008 |
| Random | 446,492 | 0.3% | 0.0% | 0.3% | 21.706 | -0.679 |
| Unigram | 446,508 | 11.1% | 0.0% | 11.2% | 13.967 | -0.519 |
| Bigram | 446,508 | 20.6% | 0.5% | 21.5% | 12.967 | -0.345 |
| Trigram | 446,508 | 28.0% | 3.1% | 30.8% | 12.268 | -0.206 |

The candidate probabilities are relative to this particular five-way set. The generated strings are matched-length controls, not meaning-preserving paraphrases, so the result establishes linguistic plausibility relative to these baselines—not communicative optimality.

## Where The Real-Child Advantage Comes From

Positive log2 Bayes factors favor the real child utterance over the paired baseline.

| baseline | n | prior logBF | context-evidence logBF | combined logBF | combined real-win rate | context-only real-win rate |
| --- | --- | --- | --- | --- | --- | --- |
| Random | 446,492 | 21.023 | 0.671 | 21.694 | 96.0% | 64.3% |
| Unigram | 446,508 | 7.038 | 0.511 | 7.549 | 73.0% | 61.5% |
| Bigram | 446,508 | 3.840 | 0.337 | 4.177 | 62.5% | 58.2% |
| Trigram | 446,508 | 1.647 | 0.198 | 1.845 | 51.5% | 55.4% |

![Prior and context components](../figs/corrected_pbm_bayes_report/paired_logbf_components.png)

Context evidence independently favors the real utterance more often than chance against every baseline, including 55.4% against the strongest trigram comparison. Nevertheless, the mean combined advantage is mostly prior-driven. This decomposition is the main scientific value of the Bayes route: it shows whether a candidate is favored because it resembles developmentally available child language, because it matches the caregiver context, or both.

Child-level bootstrap summaries, which weight children rather than millions of rows as the independent units, remain positive for all four comparisons:

| baseline | children | child-mean logBF | logBF 2.5% | logBF 97.5% | child-mean win rate | win 2.5% | win 97.5% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Random | 21 | 21.111 | 20.039 | 22.135 | 95.8% | 94.8% | 96.8% |
| Unigram | 21 | 7.234 | 6.519 | 7.854 | 72.6% | 70.4% | 74.3% |
| Bigram | 21 | 4.072 | 3.512 | 4.548 | 62.4% | 60.4% | 64.3% |
| Trigram | 21 | 1.889 | 1.414 | 2.320 | 51.4% | 49.0% | 53.5% |

For the trigram comparison, the child-level interval for the *proportion of rows won* crosses 50%, even though the child-mean log Bayes factor remains positive. The strong claim is therefore positive average evidence relative to the trigram—not a universal majority-win effect across children.

## Descriptive Developmental Pattern

| age bin | n | real probability | prior-only rank 1 | combined rank 1 | combined top 2 |
| --- | --- | --- | --- | --- | --- |
| 006-023 | 62,816 | 29.1% | 32.7% | 34.2% | 59.1% |
| 024-029 | 162,210 | 39.3% | 42.3% | 43.2% | 67.5% |
| 030-035 | 142,447 | 44.5% | 47.6% | 48.2% | 72.5% |
| 036-041 | 37,206 | 41.4% | 43.1% | 43.8% | 70.6% |
| 042-047 | 16,345 | 43.1% | 44.7% | 45.5% | 72.3% |
| 048-053 | 12,909 | 41.1% | 42.9% | 42.7% | 71.1% |
| 054-059 | 10,033 | 41.5% | 42.7% | 42.9% | 71.6% |
| 060-065 | 2,542 | 46.3% | 47.7% | 47.8% | 76.7% |

![Real-child rank by age](../figs/corrected_pbm_bayes_report/real_rank1_by_age.png)

The real-child rank improves from the youngest bin into the central PBM age range, but the later bins fluctuate and contain far fewer rows and children. This figure is descriptive. It is not a corrected onset analysis and should not be used to claim a precise month when Bayes sensitivity emerges.

Corpus-specific performance also remains heterogeneous:

| corpus | n | real probability | real rank-1 rate | real mean rank |
| --- | --- | --- | --- | --- |
| Brown | 92,555 | 37.3% | 39.2% | 2.111 |
| Manchester | 232,614 | 43.3% | 47.4% | 1.962 |
| Providence | 121,339 | 35.7% | 40.0% | 2.135 |

## Agreement With Direct Mistral Surprisal

For each paired comparison, the Mistral log advantage is the generated target's `sum_bits` minus the real target's `sum_bits`. The corrected Bayes advantage is the real combined score minus the generated combined score.

| baseline | n | gap correlation | sign agreement | mean Bayes logBF | mean Mistral logBF |
| --- | --- | --- | --- | --- | --- |
| Random | 446,492 | 0.628 | 94.0% | 21.694 | 34.403 |
| Unigram | 446,508 | 0.536 | 75.0% | 7.549 | 15.119 |
| Bigram | 446,508 | 0.374 | 66.4% | 4.177 | 10.082 |
| Trigram | 446,508 | 0.274 | 58.8% | 1.845 | 6.964 |

![Agreement with direct Mistral](../figs/corrected_pbm_bayes_report/alignment_with_direct_mistral.png)

Agreement is strongest for the deliberately poor random baseline and declines as the n-gram alternatives become more realistic. The two methods are related but non-identical: Mistral supplies a direct neural target probability, while the Bayes-derived model makes developmental prior and context evidence separately visible.

## Correct Interpretation

The corrected Bayes analysis answers:

> Among the real utterance and four matched PBM baseline strings, how strongly does an out-of-corpus, age-appropriate prior plus held-out context evidence favor each candidate?

It does **not** show that the real utterance maximizes communicative efficiency, carries more semantic information, or has a normalized posterior probability among all possible utterances. The candidate alternatives do not preserve intended meaning. Direct Mistral surprisal should remain the primary broad-coverage probability measure; the corrected Bayes score is a complementary decomposition and robustness analysis.

## Recommended Supervisor-Facing Result

The clean result to promote is:

> In leave-corpus-out, age-additive scoring, real PBM child utterances are ranked first among five matched candidates on 43.7% of rows, compared with 20% chance. The advantage is primarily explained by an age-appropriate utterance prior, while independently validated context evidence provides a smaller positive increment. The corrected Bayes and direct Mistral paired preferences agree most strongly for coarse baselines and only moderately for the strongest trigram alternative.

This result is suitable as a robustness/decomposition section. It should not replace the main fixed-effort Mistral analysis or the still-needed listener-utility and semantic-response-entropy analyses.

## Reproducibility

- Corrected scores: `results/corrected_pbm_bayes_v2/scores/pbm_crossfit_bayes_scores.csv.gz`
- Score audit: `results/corrected_pbm_bayes_v2/scores/pbm_crossfit_bayes_scores.audit.json`
- Direct-score join source: `results/bayes_information_report/pbm_bayes_mistral_complexity_joined.csv.gz`
- Compact tables: `results/corrected_pbm_bayes_report`
- Figures: `figs/corrected_pbm_bayes_report`
- Estimator: `leave_dataset_out_age_additive_prior_plus_contrastive_context_evidence`
- Normalization scope: `candidate_set_within_row`
- Output checksum: `68926da61716d2cb4ffcc4c5842a2d375c58d4a0d1751c4f797cfa04394271ca`
