# Downstream Caregiver-Response Efficiency Protocol

Status: frozen outcome-blind protocol, 2026-08-27. No downstream response
surprisal score or developmental coefficient had been inspected when this
contract was written.

## Scientific estimand

For a child utterance `u`, its preceding caregiver context `c`, and the
immediately following caregiver response `r`, define scorer-specific
downstream predictive gain as

```text
U(u; r, c) = -log2 p(r | c) - [-log2 p(r | c, u)]
           = log2 p(r | c, u) - log2 p(r | c).
```

Positive `U` means that adding the observed child utterance makes the actual
next caregiver response more predictable under that scorer. This is a
listener-relevant downstream proxy. It is not a direct measure of human
comprehension, communicative success, intended meaning, or causal influence.

The primary efficiency question is **utility at fixed production effort**:
does `U` increase with child age when child utterance effort is controlled?
The complementary secondary question is effort at fixed `U`. Information to
effort ratios are not primary because denominator coupling can manufacture
trends.

## Frozen samples

- Source: all 1,140,218 scorer-ready strict-naturalistic child rows aligned to
  immutable raw CHAT main tiers.
- Primary: 413,084 audited caregiver-child-caregiver triads. The child turn
  immediately follows an allowed caregiver, the next main tier is a nonempty
  allowed-caregiver response, the saved k1 context matches the raw nearest
  caregiver, and the frozen k3 caregiver context is nonempty.
- Discovery: Brown, Manchester, and Providence; 174,860 primary triads.
- Confirmation: the other ten strict-naturalistic corpora; 238,224 primary
  triads. Do not pool discovery into this estimate.
- Sensitivity: 613,741 child turns with an immediate nonempty caregiver
  response and nonempty frozen preceding k3 context, including child-initiated
  turns and rows outside the strict primary triad rule.
- Candidate imitation, routine, backchannel, repair, clarification, and
  acknowledgement labels are not primary exclusions. They remain descriptive
  until the 325-row stratified manual validation sample is coded.

The 9,582 strict triads whose saved k1 text does not match the raw nearest
caregiver are excluded from the primary sample and retained only where the
broader sensitivity definition permits them.

## Frozen scoring conditions

The same caregiver response target is scored separately under each condition:

1. `unconditional`: no context;
2. `base_context`: preceding frozen caregiver k3 context `c`;
3. `matched_child`: the same `c` followed by the observed child utterance `u`;
4. `shuffled_child`: the same `c` followed by a deterministic negative-control
   child utterance matched on dataset, age bin, and exact lexical word count;
5. `child_only`: the observed `u` without the earlier caregiver context.

The primary outcome is `base_context_bits - matched_child_bits`. The required
negative-control validation is `shuffled_child_bits - matched_child_bits`.
The child-only gain, `unconditional_bits - child_only_bits`, is secondary.
Shuffling is a validation device, not a meaning-preserving alternative and not
a counterfactual claim about what the child could have said.

Mistral-7B-v0.3, TinyDialogues, and Qwen3-14B are fit and reported separately.
Raw bits and raw coefficient magnitudes are never pooled across tokenizers.

## Frozen primary model

Within each scorer and scientific scope, aggregate opportunity-weighted cells
by child, age bin, exact/top-coded child word count, and exact/top-coded
caregiver-response word count. Fit weighted least squares with covariance
clustered by child:

```text
mean_downstream_gain ~ age_months_centered
                     + C(child_words_top12)
                     + C(response_words_top12)
                     + C(child_key)
```

The PBM Mistral fit is discovery. Confirmation requires a positive age
coefficient whose child-clustered 95% interval excludes zero in the other 58
children. TinyDialogues and Qwen are scorer-robustness analyses, even when
they use the confirmation children. The same model on matched-over-shuffled
gain is a required construct-validation companion.

Secondary models may add nonlinear age, context effort, preceding question
type, child-only gain, and the broader sensitivity sample. They cannot replace
the frozen primary result. Whole-child bootstrap and leave-one-child/corpus
influence checks are required before reporting a stable developmental claim.

## Interpretation boundary

Evidence for increasing communicative efficiency requires all of the
following: positive matched downstream gain, matched gain exceeding the
shuffled negative control, and a positive fixed-effort developmental slope
that survives the independent confirmation and influence checks. Failure at
any gate is reported as failure to establish this operationalization—not
silently replaced by child-target conventionality.
