# Developmental Predictability and Production Effort in Child Language

Current synthesis, 22 July 2026

## Executive Summary

This project asks whether children's utterances change developmentally in how
predictable they are at a fixed amount of production effort, and whether
children adapt their effort to uncertainty in the preceding conversational
context.

The strongest current result is narrow but robust: in the three-corpus
discovery sample, older children's observed utterances receive lower neural
surprisal at the same lexical word count. This means that the scorers find
older children's forms more predictable or conventional at fixed measured
effort. The result appears with both Mistral and TinyDialogues and is stable
across several repeated-measures estimators.

The independent 58-child Mistral confirmation estimate points in the same
direction, but its frozen primary child-clustered 95% interval includes zero.
The prespecified child-bootstrap sensitivity excludes zero. We therefore
report directional consistency and sensitivity evidence, but the primary
confirmation criterion was not met.

Two other findings qualify the simple efficiency story. First, the contextual
support provided to the observed utterance decreases with age under both
scorers, contrary to the predicted positive direction. Second, the current
response-space analysis does not support the prediction that older children
increasingly lengthen their responses as sampled response uncertainty rises.

These results are consistent with developmental conventionalization or
adaptation of linguistic form. They do not by themselves show that children
optimize a single communicative-efficiency objective. A stronger claim will
require a listener-relevant outcome, a validated conversational-response
sample, and better calibration of response uncertainty.

![Primary fixed-effort developmental estimates](../figs/direct_surprisal_replication/mistral_full79/modular_visual/headline_primary_age_slopes.png)

*Points are fixed-effort age coefficients. Horizontal bands are 95% intervals
from the displayed child-clustered models. The pooled 79-child estimate is
descriptive because it combines discovery and confirmation children.*

## Scientific Questions

The current evidence addresses three distinct quantities. Keeping them
separate prevents a change in form frequency from being mistaken for a change
in contextual support.

1. **Contextual target surprisal:**
   `−log2 p(utterance | three preceding caregiver turns)`. Lower values mean
   that the observed utterance is more predictable to the scorer in context.
2. **Unconditional target surprisal:** `−log2 p(utterance)`. Lower values mean
   that the utterance form itself is more probable to the scorer without the
   conversational context.
3. **Context gain:** unconditional minus contextual surprisal. Positive values
   mean that the preceding context makes the observed utterance more probable.

The primary developmental question is whether contextual target surprisal
changes with age while lexical word count and child identity are held fixed.
This is an information-at-fixed-effort analysis. It is not an
information/effort ratio and does not assume that either maximum or minimum
surprisal is intrinsically optimal.

A complementary analysis asks whether the child's production effort changes
with uncertainty over model-generated responses to the same caregiver
context. Raw child effort and effort relative to a generated response
distribution are different outcomes and are kept separate.

## Samples and Scorers

The discovery sample contains 21 longitudinally observed children from Brown,
Manchester, and Providence. The independent confirmation sample contains the
remaining 58 children from 10 other strict-naturalistic corpora. The combined
descriptive sample contains 79 children from 13 corpora.

Mistral scores are available for all 79 children. The completed score tree
covers real child utterances, caregiver utterances, and same-length random,
unigram, bigram, and trigram candidates, each scored without context and with
one, two, or three preceding caregiver turns. Six generated strings are blank,
creating 24 flagged baseline cells; no real-child score is missing.

TinyDialogues scores are available for the same six conditions and four
context settings in the 21-child discovery sample. TinyDialogues is therefore
a scorer-robustness analysis on the discovery children, not an independent
sample confirmation. Its tokenizer and score scale differ from Mistral's, so
cross-scorer conclusions use within-model slopes, contrasts, rankings, and
exactly paired rows rather than raw bits per model token.

## Frozen Primary Analysis

The discovery/confirmation protocol was dated before the non-discovery
estimates were fit. The primary model uses the real child utterance with three
preceding caregiver turns and compares age at exact or top-coded lexical word
counts. Child identity is included, and uncertainty is clustered by child.
The primary linear coefficient is measured in scorer bits per month at fixed
word effort.

Prespecified sensitivities include unconditional surprisal, context gain,
quadratic age, fixed age bins, within/between-child models, generalized
estimating equations, mixed models, child and corpus bootstrap, age
permutation, tail trimming, and leave-one-child/corpus influence analyses.
Warning-bearing mixed fits are retained as sensitivities rather than replacing
the primary model.

## Direct-Surprisal Results

| Scorer and sample | Contextual slope | Unconditional slope | Context-gain slope | Protocol reading |
| --- | ---: | ---: | ---: | --- |
| TinyDialogues, discovery 21 | −0.222 [−0.311, −0.132] | −0.254 [−0.339, −0.168] | −0.032 [−0.050, −0.014] | scorer robustness supports the fixed-effort discovery; context-gain direction is contrary |
| Mistral, discovery 21 | −0.131 [−0.179, −0.083] | −0.162 [−0.211, −0.112] | −0.030 [−0.050, −0.011] | discovery result reproduced; context-gain direction is contrary |
| Mistral, confirmation 58 | −0.062 [−0.132, 0.007] | −0.089 [−0.145, −0.034] | −0.028 [−0.045, −0.010] | primary contextual interval crosses zero; context-gain direction is contrary |
| Mistral, all 79 | −0.080 [−0.134, −0.025] | −0.108 [−0.156, −0.059] | −0.029 [−0.041, −0.016] | descriptive only |

Values are fixed-effort age slopes in scorer bits per month with 95%
child-clustered intervals. Because scorer calibrations differ, magnitudes
should not be compared as if one bit had the same empirical scale across
models.

### Primary result

Both scorers find a negative contextual-surprisal slope in the discovery
sample. On the exact 446,508-row paired intersection, the TinyDialogues slope
is 0.089 bits/month more negative than the Mistral slope; the paired
child-bootstrap interval is `[−0.152, −0.028]`. Thus the direction is robust to
the scorer, while the magnitude is scorer-dependent. Supported child-specific
slope signs agree across scorers for 18 of 21 children.

![Paired developmental slopes across scorers](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_all_outcome_slopes.png)

### Confirmation result

The 58-child contextual-surprisal coefficient is negative, but the frozen
primary interval includes zero. Its prespecified child-bootstrap interval is
`[−0.152, −0.014]`. Both uncertainty summaries are informative: the clustered
primary analysis does not meet the decision rule, while the bootstrap shows
that the conclusion is sensitive to how uncertainty across children is
estimated. The pooled 79-child coefficient cannot be substituted for the
confirmation estimate.

### Context support

Context gain is defined as unconditional minus contextual surprisal. Its age
slope is negative for TinyDialogues discovery, Mistral discovery, Mistral
confirmation, and the pooled descriptive sample. The context still generally
helps predict observed utterances, but that incremental support does not grow
with age in the predicted direction. The developmental decline in
unconditional surprisal is larger than the decline in contextual surprisal.

This distinguishes two phenomena: older children's forms become more probable
to the scorer overall, while the measured incremental contribution of the
preceding context becomes smaller. A broad claim about improved contextual use
would therefore be unsupported by the present result.

### Individual and corpus variation

All 21 TinyDialogues profiles and all 79 Mistral profiles were inspected
through child-age-session trajectories. The analysis also includes supported
child-specific slopes, corpus and child leave-out estimates, corpus bootstrap,
and mixed-model sensitivity checks. Individual trajectories vary, and some
children show slope reversals. The population result should not be presented
as a universal developmental law for every child.

![Distribution of child-specific slopes](../figs/direct_surprisal_replication/mistral_full79/modular_visual/child_slope_distribution.png)

## Generated Baseline Comparisons

Random, unigram, bigram, trigram, and additive LSTM candidates provide
reference distributions over forms. The n-gram and LSTM generators are trained
with additive age bins so that a target-age candidate does not use vocabulary
from later ages. The PBM additive LSTM generation and Mistral scoring are
complete; they are no longer planned work.

The candidate comparisons are useful for asking how real utterances differ
from age-appropriate generated strings at the same word count. They do not
hold intended meaning constant. Consequently, they cannot establish that the
observed child utterance is Pareto-optimal or more efficient than a
meaning-preserving alternative.

Across the paired neural-scorer analysis, trigram, bigram, unigram, and random
candidates retain the same closest-to-farthest ordering in every age bin under
both scorers. This ordering is a scorer-robust descriptive result about the
candidate sets, not a semantic-choice result.

![Generated candidate gaps across scorers](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_candidate_gap_ordering.png)

## Corrected Bayes-Derived Candidate Analysis

The corrected Bayes analysis decomposes each candidate's score into an
age-appropriate utterance prior and a separate whole-utterance context-evidence
term. Training is leave-corpus-out, uses additive age bins, handles unknown
tokens explicitly, and normalizes only over the five matched candidates:
real, random, unigram, bigram, and trigram.

All three held-out corpus folds pass the preregistered matched-versus-shuffled
context validation. Across the 2,232,524 candidate rows, the real child
utterance has mean five-way probability 40.0%, ranks first on 43.7% of source
rows, and ranks in the top two on 68.6%. Five-way chance for first place is
20%. The prior alone ranks the real utterance first on 42.9%; context evidence
raises this to 43.7%. The combined advantage is therefore driven mainly by the
developmentally appropriate utterance prior, with a smaller validated context
increment.

![Held-out context validation for the Bayes-derived scorer](../figs/corrected_pbm_bayes_report/heldout_context_validation.png)

This is a candidate-set probability, not a normalized posterior over every
possible utterance. It does not show that the real utterance carries more
semantic information or maximizes communicative efficiency. Direct neural
surprisal remains the broad-coverage primary measure; the Bayes-derived score
is a complementary decomposition.

## Effort Relative to a Generated Response Space

For each unique caregiver context, the response-space analysis samples 100
Mistral responses and estimates exact-string response entropy plus the
generated distribution of response lengths. Approximately 444,000 PBM child
utterances can then be located relative to the generated length distribution
for their caregiver context. The 176 incomplete/fallback contexts remain
explicitly flagged, and excluding their matched child rows does not change the
headline estimates.

The final repeated-measures models compare child effort with generated expected
effort, response entropy, caregiver-context length, next-token context entropy,
age, and the age-by-response-entropy interaction. Older children move toward
the generated length distribution on average. However, that developmental
movement is weaker in contexts with higher sampled response entropy for the
principal residual and percentile outcomes. This is opposite to the simple
prediction that older children increasingly invest more effort when the model
response space is more uncertain.

![Age and sampled response entropy in the relative-effort model](../figs/route2_relative_effort_model_suite/percentile_in_gen_distribution_r2m5_age_by_entropy_prediction_lines.png)

*Lines are model predictions at selected response-entropy values. Any shaded
bands are 95% fitted-mean intervals, not prediction intervals for individual
utterances.*

This result may be substantive, but it may also reflect the current measure.
Exact-string entropy depends on the model, prompt, temperature, number of
samples, and surface-form variation. The generated responses are
context-conditioned alternatives, not same-meaning paraphrases. Semantic
clustering, rarefaction, prompt/seed/temperature stability, and a decoupled
generator are required before strong interpretation.

## Developmental Onset

The earlier PBM row-level analysis placed the first nominal fixed-effort
age-bin decrease by 24–29 months. The frozen sustained-onset analysis now adds
1,000 child-bootstrap replicates and a simultaneous max-|t| band over every
post-reference contrast. It does not establish a sustained onset in either the
PBM discovery or non-PBM confirmation sample.

In PBM, the 24–29 simultaneous upper bound is just above zero and the 36–41
bound also crosses zero; later bins lack the required three-corpus support. In
the non-PBM sample, 36–41 is the only age bin whose simultaneous upper bound is
below zero, but later adequately supported bins cross zero. It therefore fails
the rule that every later adequately supported bin must remain negative.

The current evidence supports a linear developmental association, not a
replicated exact onset. The simultaneous analysis uses lexical word effort;
validated full-79 morpheme, syllable, and phoneme controls remain pending.

## What the Evidence Supports

The current evidence supports the following statement:

> In longitudinal naturalistic child speech, observed utterance forms become
> more predictable to two neural language models with age at the same measured
> lexical effort in the three-corpus discovery sample. The independent
> Mistral confirmation estimate points in the same direction but does not meet
> the frozen primary interval criterion. Context support and sampled
> response-uncertainty adaptation do not follow their predicted developmental
> directions.

It does not yet support the claim that children optimize a single normative
communicative-efficiency objective. That broader claim requires evidence that
connects the child's utterance to a listener-relevant outcome, such as improved
prediction of the next caregiver response, contingent continuation, or reduced
repair and clarification.

## Remaining Validation Before a Stronger Claim

- Manually validate the constructed structural sample of genuine child
  responses to immediately preceding caregiver turns and adjudicate the
  retained `context_k1` mismatches. Preserve flags for child-initiated speech,
  imitation, routines/reading, backchannels, questions, and repairs.
- Repeat the completed child-bootstrap sustained-onset analysis with validated
  full-79 morpheme, syllable, and phoneme effort measures.
- Prototype downstream caregiver-response predictive gain and validated
  repair, clarification, acknowledgement, and contingent-continuation labels.
- Calibrate sampled response uncertainty using semantic clusters, coverage and
  rarefaction, seeds, prompts, temperatures, and a decoupled generator.
- Audit morphology, phonological proxies, lexical diversity/rarity, and
  dependency parsing by corpus, child, age, and session before using them as
  primary controls.
- Complete the full-79 same-length LSTM generation/scoring extension if the
  additional baseline coverage remains a priority. It is not required for the
  already completed direct-Mistral confirmation analysis.

## Consultation Materials

- [Interactive results explorer](direct_surprisal_results_explorer.html)
- [Frozen discovery/confirmation protocol](direct_surprisal_replication_protocol_2026-07-21.md)
- [TinyDialogues–Mistral paired visual comparison](paired_tinydialogues_mistral_visual_summary.html)
- [Corrected Bayes-derived candidate report](corrected_pbm_bayes_report.html)
- [Sustained-onset confirmation](direct_surprisal_onset_confirmation.html)
- [Formal mathematical definitions](july_meeting_definitions.html)
