# Three-scorer performance comparison protocol

Date frozen: 2026-09-04, before aggregate Mistral/Qwen/TinyDialogues score
comparisons were inspected.

## Objective

Compare how much surprisal Mistral-7B-v0.3, Qwen3-14B, and the
TinyDialogues-trained SmolLM2-135M assign to exactly the same linguistic
targets. This is a bounded model-evaluation side analysis. It does not replace
the registered developmental analyses and it does not select a new primary
scientific scorer automatically.

The direct question is whether Qwen or TinyDialogues is more or less surprised
than Mistral on the project's data. Lower cross-entropy means that a model
assigns greater probability to the observed target on this evaluation corpus.

## Historical bridge

Two historical T7 analyses supply the visualization and aggregation logic:

1. `surprisal_computing/proj_1/src/plot_surprisal_vs_length.py` pooled child
   utterances and compared scorer surprisal at each utterance length.
2. `surprisal_computing/proj_1/src/plot_surprisal_vs_length_by_model_age_schemes.py`
   repeated that comparison within age bins.

The new analysis retains exact-length and age-stratified comparisons, but does
not use the historical token-weighted bits-per-model-token outcome as its
cross-model ranking criterion. Different tokenizers change both the number and
identity of tokens, so token-normalized perplexity is a tokenizer diagnostic,
not a fair primary comparison across these three scorers.

## Evaluation domains

### Primary domain: observed child utterances

- Sample: the 21 PBM children in Brown, Manchester, and Providence.
- Targets: real child utterances only.
- Contexts: `k0`, `k1`, `k2`, and `k3`; `k0` and `k3` are the principal
  endpoints.
- Inputs: the independently audited schema-v2 same-pass word-surprisal
  products for all three scorers.
- Pairing key: `target_occurrence_id` plus `context_window`.
- Inclusion: exact three-scorer intersection, `score_status == "scored"`,
  positive cleaned word count, positive Unicode character count, and finite
  score fields.

### Secondary domain: next-caregiver responses

- Sample: the frozen 413,084 primary caregiver-child-caregiver triads across
  the all-79 longitudinal sample.
- Targets: the exact same next-caregiver response for each scorer.
- Conditions: unconditional, base conversational context, and matched child
  turn.
- Pairing key: `response_pair_id`.
- Inclusion: `primary_eligible == 1`, scored status for the relevant condition,
  positive response word and character counts, and exact three-scorer target
  hash agreement.

This second domain is a role and corpus-coverage stress test. It does not turn
the evaluation into a general benchmark of English or human language.

## Estimands and ranking rule

The primary cross-tokenizer outcome is Unicode **bits per character** (BPC):

```text
sum target surprisal bits / number of Unicode characters in the target
```

Secondary outcomes are bits per cleaned lexical word (BPW), total utterance
bits, and model-token diagnostics. Per-model-token surprisal is never used to
rank models across tokenizers.

For each model and condition, report both:

- occurrence-weighted cross-entropy: total bits divided by the total common
  denominator;
- child-balanced cross-entropy: compute the micro-average within each child,
  then give each child equal weight.

The child-balanced BPC is the primary summary. A scorer is described as less
surprised than another on a domain/condition when the paired child-balanced
BPC difference has the corresponding sign. A strong ranking additionally
requires its 95% whole-child bootstrap interval to exclude zero. This rule is
applied to the planned Mistral comparisons; the analysis does not search over
metrics for a favorable ranking.

## Uncertainty and robustness

- Use 10,000 deterministic whole-child bootstrap resamples.
- Preserve exact scorer pairing inside every resample.
- Report paired per-utterance win shares, child win shares, Pearson score
  correlations, and a child-level Wilcoxon signed-rank sensitivity.
- Report exact-length cells (1--12 words, with 13+ shown separately), frozen
  additive age bins, corpus strata, and leave-one-corpus-out paired contrasts.
- Report the amount of contextual support (`k0 - k3`) separately from target
  cross-entropy.
- Show model parameter count only as a three-point descriptive comparison; do
  not fit or claim a scaling law.

## Interpretation limits

- Results establish relative cross-entropy only on the evaluated child-speech
  and caregiver-response targets, under the frozen text normalization,
  context construction, BOS policy, model revisions, and scoring code.
- Lower BPC is evidence of better predictive fit to these exact strings, not
  proof of better semantics, child knowledge, calibration for every use, or
  listener utility.
- TinyDialogues is child-domain trained; a favorable child-speech result may
  reflect domain match. Qwen and Mistral were trained on different and much
  broader corpora whose overlap with CHILDES is not fully known.
- Parameter count, tokenizer vocabulary, training data, architecture, dtype,
  and domain exposure are jointly confounded. No causal model-size claim is
  permitted.
- PBM is one discovery sample. The caregiver-response stress test broadens
  target role and corpus coverage but is not an independent benchmark corpus.
