# Focused Bayesian Joint Adaptive-Efficiency Protocol

Status: frozen post-hoc analysis contract, 2026-08-28.

## Scientific question

This analysis returns to the motivating communicative-efficiency question:
does the developing child allocate production effort according to contextual
demand while also producing increasingly predictable forms at a fixed amount
of effort?

Corpus comparisons are not the scientific object. Corpus enters only as
background hierarchical structure. Brown, Manchester, and Providence retain
their discovery label, but their estimates do not define the Bayesian priors.

## Hypotheses

- **H1, demand-sensitive production:** at 42 months, greater exact-string
  response entropy predicts greater child effort.
- **H2, developmental calibration:** the response-entropy/effort association
  changes with age. Its direction is estimated two-sided because the existing
  nonlinear analysis and developmental reversal have already been inspected.
- **H3, fixed-effort form development:** contextual utterance surprisal
  decreases with age when exact/top-coded child word effort is controlled.
- **H4, coordinated development:** child variation in H3 covaries with child
  variation in H2. The efficiency-motivated direction is negative: more
  negative fixed-effort surprisal slopes accompany more positive changes in
  demand-sensitive effort. This remains a post-hoc association.

## First-stage child estimates

The shared audited utterance table supplies 1,122,396 context-bearing child
utterances. For every eligible child, estimate:

```text
k3_bits ~ age_z + C(word_count_top12)

log(1 + child_words) ~ age_z * response_entropy_z
                     + caregiver_context_words_z
```

`age_z` is age in six-month units centered at 42 months. The three retained
coefficients are the fixed-effort k3 age slope, the response-entropy effort
slope at 42 months, and the age-by-response-entropy slope. Their full 3 x 3
estimation covariance is obtained from the two equations' shared
session-clustered sandwich scores. This preserves cross-outcome estimation
dependence without fitting 1.1 million observations with NUTS.

Children require at least five recording sessions. The rule excludes only
Weist/Emily, who has three sessions; it is an identifiability rule for a
child-specific developmental covariance, not an outcome-based exclusion.

## Bayesian joint model

Let `b_hat_j` be the three estimated coefficients for child `j` and `V_j`
their known session-clustered estimation covariance:

```text
b_hat_j ~ MVN(theta_j, V_j)
theta_j ~ MVN(mu + corpus_effect[corpus_j], Sigma_child)
```

The primary outputs are the three population means, their effect-scale
posterior probabilities and ROPE probabilities, and the three between-child
correlations. A wider-prior fit and leave-one-corpus refits assess prior and
corpus influence without turning the corpus split into the scientific story.

The regularizing and wider-prior inferential fits must have maximum R-hat
below 1.01 and at least 400 bulk and tail effective samples across all saved
parameters. The deliberately half-length leave-one-corpus refits are gated on
the four registered scientific outputs (three population means and the H4
correlation) at R-hat below 1.015 and at least 400 bulk and tail effective
samples. Every all-parameter diagnostic remains saved. All fits require zero
divergences, zero treedepth saturation, and minimum BFMI above 0.3.

## Interpretation boundary

The effort outcome is `log(1 + words)`, and the information outcome is Mistral
self-information. Neither is listener utility. The joint model can establish
coordinated developmental calibration under these measurements; it cannot
show a normative optimum, causal adaptation, intended-meaning preservation,
or communicative success. The frozen downstream caregiver-response gain is the
decisive future utility test.
