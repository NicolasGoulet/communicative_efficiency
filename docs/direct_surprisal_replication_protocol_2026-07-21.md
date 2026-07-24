# Frozen Direct-Surprisal Replication Protocol

Date frozen: 2026-07-21

Status: frozen before fitting or plotting the main estimates for the 58
non-PBM children.

## Scope

This protocol governs two related but distinct analyses:

1. a scorer-robustness replication on the Brown, Manchester, and Providence
   discovery sample (21 children), using TinyDialogues scores and the existing
   Mistral scores on exactly paired utterances; and
2. a sample replication using Mistral scores for the remaining 58 children in
   the other 10 strict-naturalistic corpora.

TinyDialogues on PBM is not an independent confirmation sample. The pooled
79-child estimate is descriptive and must not replace the separate non-PBM
confirmation estimate.

## Frozen Samples

Discovery sample:

- Brown, Manchester, and Providence;
- 21 children;
- reported separately for Mistral and TinyDialogues.

Confirmation sample:

- Belfast, Demetras1, Forrester, Kuczaj, Lara, MPI-EVA-Manchester, Post,
  Sachs, Weist, and Wells;
- 58 children;
- Mistral only in the current scored handoff.

Pooled descriptive sample:

- all 79 children across all 13 strict-naturalistic corpora;
- never labeled confirmatory.

## Frozen Eligibility Rules

The primary real-child k3 analysis includes rows satisfying all of the
following:

- role is child and target condition is `real`;
- age is finite and between 6 and 65 months inclusive;
- cleaned target contains at least one lexical word;
- target `sum_bits` is finite and `n_eval_tokens` is positive;
- k3 context text is nonempty;
- the context and target belong to the same child/session source contract.

The primary implementation must preserve explicit flags for rows excluded by
each rule. Initial/no-context turns remain available for k0 analyses but are
not treated as ordinary k3 context-bearing observations.

The current scored context is a preceding-caretaker window, not yet a fully
validated conversational-response label. Imitations, routines/reading,
backchannels, repairs, and nonadjacent turns will be retained as flags and
used in prespecified sensitivities after the sequence-label audit. Their later
availability must not silently change the frozen broad-sample result.

## Frozen Outcomes And Sign Conventions

Primary outcome:

- contextual real-child utterance surprisal at k3, `sum_bits_k3`, modeled at
  fixed lexical word effort. A negative age coefficient means older children
  produce targets that are more predictable to that scorer at the same
  measured word effort.

Primary decomposition/robustness outcomes:

- unconditional real-child utterance surprisal, `sum_bits_k0`;
- k3 context gain,
  `context_gain_k3 = sum_bits_k0 - sum_bits_k3`;
- positive context gain means the k3 preceding context raises the scorer's
  probability of the observed target relative to k0.

Secondary outcomes:

- k1 and k2 contextual surprisal and context gain;
- word-, character-, morpheme-, syllable-, and phoneme-normalized scores;
- real-minus-random/unigram/bigram/trigram paired candidate gaps;
- caretaker target trajectories, interpreted as caregiver input adaptation.

Raw bits per model token are never used as the primary cross-scorer comparison
because Mistral and TinyDialogues have different tokenizers. Cross-scorer
claims use within-model slopes/contrasts and word- or character-denominated
quantities.

## Frozen Primary Formulas

Define:

- `age_c = age_months - mean(age_months)` within the fitted sample;
- `word_count_exact_top12` as exact lexical word count for 1-11 words and a
  `12+` category otherwise;
- `child_key = dataset + "/" + child_id`.

For each scorer and sample, fit:

```text
P1: sum_bits_k3 ~ age_c + C(word_count_exact_top12) + C(child_key)
P2: sum_bits_k0 ~ age_c + C(word_count_exact_top12) + C(child_key)
P3: context_gain_k3 ~ age_c + C(word_count_exact_top12) + C(child_key)
```

The primary covariance estimate is child-clustered. The estimand is the
within-child developmental association at fixed exact/top-coded word effort.

Primary directional predictions:

- P1 age coefficient: negative;
- P3 age coefficient: positive;
- P2 is decomposition evidence and has no confirmatory directional decision
  rule.

The P1 confirmation succeeds only if the non-PBM estimate is negative and its
two-sided 95% child-level interval excludes zero. P3 is evaluated separately;
failure or reversal of P3 does not get rewritten as support for P1.

## Frozen Estimator Sensitivities

Apply the same mean structure, without selecting a preferred result after
inspection, using:

- utterance-level OLS with child fixed effects and child-clustered covariance;
- child-age-exact-word cells fit by weighted least squares;
- a within/between (Mundlak) specification;
- child-clustered Gaussian GEE;
- random-intercept and random-age-slope mixed models when identifiable;
- a child-resampling bootstrap for the primary coefficients.

All nonconvergence, singularity, separation, and covariance failures are saved
as audit rows. A failed sensitivity is not silently omitted.

## Frozen Nonlinearity And Onset Rule

The linear age coefficient is primary. Prespecified secondary age forms are:

- quadratic continuous age with the lower-order age term retained;
- the fixed age bins `006-023`, `024-029`, `030-035`, `036-041`, `042-047`,
  `048-053`, `054-059`, and `060-065`.

Onset is not the first nominally significant bin. The exploratory sustained
onset is the earliest post-reference bin for which the fixed-effort contrast
versus `006-023` is negative and all later adequately supported bins remain
negative under a simultaneous 95% child-bootstrap band. A bin requires at
least five children and three corpora in the confirmation sample. If no bin
passes, onset is reported as not established.

## Frozen Candidate Comparisons

For random, unigram, bigram, and trigram targets:

- compare the generated target with the real target from the same source row
  and context;
- define `candidate_minus_real_bits = generated_sum_bits - real_sum_bits`;
- verify exact source-row and context identity before pairing;
- fit gap-by-age models with child-clustered uncertainty and fixed effort;
- keep each candidate family separate before any pooled source interaction.

These generated candidates are not assumed to preserve the child's intended
meaning. They support scorer/baseline diagnostics, not Pareto-optimality
claims.

## Frozen TinyDialogues-Mistral Comparison

On exactly paired PBM rows, report:

- within-model P1/P2/P3 estimates and child-bootstrap intervals;
- the child-bootstrap difference in corresponding coefficients;
- paired rank and within-child-centered correlations;
- agreement in context-gain direction, candidate ordering, and child-specific
  slope signs;
- disagreement by age, corpus, child, target length, context length, lexical
  frequency, and scorer token count.

Agreement on PBM is evidence that the discovery pattern is less dependent on
one scorer. It is not sample replication.

## Frozen Missing-Data Handling

- Never impute missing surprisal outcomes.
- Preserve and report every exclusion reason.
- Patch the six literal-`nan` generated targets in the full-79 Mistral tree
  before final baseline comparisons, or exclude only those 24 target/context
  cells with an explicit audit. They do not affect real-child P1-P3 fits.
- Preserve context-unavailable rows for k0 and coverage reports; exclude them
  from k1/k2/k3 context-gain analyses.
- Recover the known Providence/Naima caretaker age only with an explicit
  provenance column; this does not affect primary child-target models.

## Multiplicity And Reporting

P1 and P3 are the two primary directional tests and are reported separately.
All context-window, candidate, alternative-effort, nonlinear, corpus, and
individual-child results are labeled secondary or exploratory. Exact p-values,
effect sizes, intervals, sample sizes, and all attempted fits are retained.

No result may be described as communicative success, listener utility,
meaning-preserving efficiency, or proof of optimization without a separately
validated outcome/candidate design.
