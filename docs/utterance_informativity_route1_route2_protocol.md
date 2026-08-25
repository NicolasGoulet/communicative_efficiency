# Utterance Informativity Extension: Route 1 and Route 2 Agent Protocol

Status: frozen implementation contract, 2026-08-25.

This is the durable agent-facing protocol for leveraging the
frequency/informativity literature at the **utterance level**. It does not
reproduce Pawar and Cychosz's phone-level estimator. Future agents must read
this file before changing the utterance-informativity models, aggregations, or
report language.

## Scientific objective

The project retains Professor Xu's two complementary questions:

1. **Route 1 — utterance information at constrained production effort:** at
   the same measured effort, how do unconditional utterance surprisal,
   contextual utterance surprisal, and context support change with child age?
2. **Route 2 — effort adaptation:** given the preceding context and its
   generated response distribution, when do children shorten or lengthen their
   responses, both in raw units and relative to a generated effort reference?

The informativity extension belongs primarily to Route 1. It borrows one
conceptual move from the frequency/informativity literature: unconditional
frequency and average contextual predictability are related but should not be
collapsed. It does not change the primary unit from utterances to phones or
words.

Word-level informativity remains a secondary lexical decomposition owned by
`developmental_word_information`. It is not the primary analysis described
here.

## Definitions

For observed utterance occurrence `i`, target utterance `u_i`, and preceding
three-utterance context `c_i`:

```text
S0_i = -log2 p_Mistral(u_i)
S3_i = -log2 p_Mistral(u_i | c_i)
G_i  = S0_i - S3_i
```

Interpretation:

- `S0` is unconditional scorer self-information. It is a smoothed,
  model-based analogue of form rarity/conventionality, not an empirical string
  count and not a semantic-frequency measure.
- `S3` is contextual scorer self-information for one occurrence. Lower values
  mean that Mistral assigns the observed form greater probability in its
  context.
- `G` is context support: the reduction in target self-information when the
  context is supplied. Positive values mean that context supports the target.

Do not call a single occurrence's `S3` value type-level informativity. The
protocol defines two utterance-level aggregate informativity objects below.

### Population utterance informativity

For age group `a`, speaker role `r`, and a shared reference distribution over
measured effort `q_ref(e)`:

```text
I3(a, r) = sum_e q_ref(e) E[S3 | age=a, role=r, effort=e]
I0(a, r) = sum_e q_ref(e) E[S0 | age=a, role=r, effort=e]
IG(a, r) = sum_e q_ref(e) E[G  | age=a, role=r, effort=e]
```

These are regression-standardized developmental summaries. They answer what
the mean scorer-indexed utterance self-information would be if every age group
shared the same exact/top-coded word-effort distribution. Stable child
identity is controlled in the fitted cell model and averaged over the
scope-specific child reference population.

This is the primary utterance-level adaptation of average contextual
informativity.

### Recurrent exact-utterance informativity

For a sufficiently recurrent exact normalized utterance type `u`:

```text
I_type(u) = mean_{i: u_i=u} S3_i
```

This is the closest literal utterance-type analogue of average
informativity. It is secondary because most complete utterance strings are
rare or unique.

The default support gate is:

```text
at least 100 occurrences
at least 10 children
at least 3 corpora
```

The output must retain the exact support counts, mean `S0`, mean `S3`, mean
context support, empirical recurrence bits, word count, and scorer-token
density measures. Results outside this gate may be shown only as explicitly
labelled sparse descriptives.

## Authoritative inputs

Child utterances:

```text
results/direct_surprisal_replication/mistral_full79/
  child_direct_surprisal_wide.csv.gz
```

Caregiver utterances:

```text
results/direct_surprisal_replication/mistral_full79/
  caretaker_direct_surprisal_wide.csv.gz
```

Existing Route 1 model inventory:

```text
results/direct_surprisal_replication/mistral_full79/modular/models/
  model_summaries.csv
```

Existing Route 2 and joint-cloud model inventory:

```text
results/full79_joint_efficiency_analysis/models/
  combined_model_registry.csv
```

The all-79 Qwen response-space handoff is already complete. No generation or
Mistral scoring is needed for this extension.

## Frozen sample roles

Never replace the registered sample roles with an outcome-selected split:

```text
PBM discovery:
  Brown, Manchester, Providence — 21 children

Non-PBM confirmation:
  the other 10 strict-naturalistic corpora — 58 children

All-79 descriptive:
  all 13 corpora — 79 children
```

Fit children and caregivers separately. Caregiver turns are indexed by the
target child's age and identity; they are not child productions.

## Existing models that must be reused

Do not refit these merely to rename them informativity.

### Route 1 direct models

- `P1_k3_contextual`: contextual total utterance surprisal at fixed exact or
  top-coded word effort.
- `P2_k0_unconditional`: unconditional total utterance surprisal at fixed
  effort.
- `P3_k3_context_gain`: context support at fixed effort.
- `C1`, `C2`, and `C3`: the corresponding caregiver comparisons.
- Registered nonlinear, age-bin, Mundlak, GEE, tail, effort, bootstrap,
  influence, and onset sensitivities remain attached to these fits.

The PBM P1 estimate is negative. The non-PBM primary clustered interval
crosses zero, so the frozen confirmation rule was not met. P3 is negative in
both samples, contrary to the original positive direction. Re-labelling these
outcomes as informativity must not change those results.

### Route 2 and joint-cloud models

- `m1_length_primary`: raw child word effort from age, exact-string response
  entropy, their nonlinear interaction, context length, child effects, and
  corpus.
- `m2_length_qwen_reference`: a separate generated-reference sensitivity that
  adds Qwen expected word effort.
- `m4_effort_percentile`: child effort position in the same-context Qwen
  length distribution.
- `m5_exact_length_k3_gap`: child-minus-Qwen k3 gap among generated responses
  with the same exact word length.
- `m3`, `m3b`, `m3c`, and `m3d`: nonlinear joint-suite versions of k3 total,
  k3 per scorer token, k0 total, and context support.

Raw child effort and generated-relative effort are different estimands. Do not
condition every Route 2 model on generated expected length, and do not use
same-length random, n-gram, or LSTM baselines to test effort adaptation.

## New registered models

### U1–U4: effort-standardized informativity summaries

Fit one opportunity-weighted child-cell WLS model for each outcome:

```text
k3_total_mean
k0_total_mean
context_gain_total_mean
k3_bits_per_model_token_mean   # secondary density sensitivity
```

Formula:

```text
outcome_mean ~ age_bin + exact_or_topcoded_word_count + child_identity
```

Use child-clustered covariance. Then g-standardize each age bin over the
scope/role-pooled word-effort distribution and the scope-specific child
reference population. Save estimates, standard errors, 95% intervals, the
reference effort weights, and support.

The density sensitivity uses Mistral evaluation tokens. Do not relabel it as
bits per word, phoneme, morpheme, or syllable.

### U5: developmental frequency–informativity coupling

Aggregate rows to child × age bin × exact/top-coded word effort × 0.5-bit k0
density cells, retaining opportunity counts. Fit separately by role and sample
scope:

```text
k3_density ~ age
           + age^2
           + k0_density
           + k0_density^2
           + age:k0_density
           + exact_or_topcoded_word_count
           + child_identity
```

Use opportunity-weighted WLS and child-clustered covariance. The registered
developmental coefficient is `age:k0_density`. Also save the adjusted k3
difference between the scope-specific k0 p10 and p90 at every frozen age bin.

This model asks whether conditional and unconditional scorer predictability
become more or less coupled with age. It does not show that children transmit
more meaning, and the common scorer creates mechanical association between k0
and k3. The age interaction and separate context-support trajectory are more
informative than the raw k0–k3 correlation.

### U6: recurrent utterance-type table

Create the supported type table defined above. A small HC3 type-level model may
be used only as an exploratory description:

```text
mean_k3_density ~ empirical_recurrence_bits
                + mean_k0_density
                + word_count
```

The table is the principal U6 product; no type-level regression is required
for completion.

## Age bins

Use the project's established bins so figures align with the existing Route 1
and Route 2 plots:

```text
006-023
024-029
030-035
036-041
042-047
048-053
054-059
060-065
```

The first bin is wider. This must remain visible. Continuous-age and nonlinear
existing fits are required context for interpreting the categorical summaries.

## Word-level addition

Word-level informativity is a useful secondary decomposition, but its current
analysis-ready scope is PBM21 under Mistral, Qwen, and TinyDialogues. Those
scorers must remain separate. Do not describe the three-scorer PBM result as an
independent-sample confirmation.

An utterance-level lexical-profile extension may use out-of-fold expected
word-type informativity, lexical rarity, and form-cost summaries. It must not
predict utterance `sum_bits` with the same utterance's raw word surprisals,
which would be tautological.

## Outputs

The staged workflow is:

```text
datasets -> models -> report -> audit
```

Output namespace:

```text
results/utterance_informativity_analysis/
docs/utterance_informativity_route1_route2_report.md
docs/utterance_informativity_route1_route2_report.html
```

Required saved products:

```text
datasets/model_cells.csv.gz
datasets/recurrent_utterance_types.csv.gz
datasets/dataset_manifest.json
models/model_registry.csv
models/standardized_age_informativity.csv
models/frequency_informativity_coefficients.csv
models/frequency_informativity_age_contrasts.csv
models/existing_route1_inventory.csv
models/existing_route2_inventory.csv
models/models_manifest.json
audit/final_audit.json
UTTERANCE_INFORMATIVITY_COMPLETE_AND_AUDITED
```

Every manifest must bind inputs and outputs by SHA-256, row counts, sample
scope, and estimand labels. Reporting reads only frozen outputs and performs no
fitting.

## Interpretation guardrails

- Lower k3 means greater scorer predictability, not greater Shannon
  information transmitted.
- Higher adjusted mean k3 may be called greater model-based utterance
  informativity only when the aggregation and effort standardization are
  stated.
- Do not call k0 empirical utterance frequency. It is unconditional Mistral
  self-information. The recurrent-type table contains the separate empirical
  recurrence measure.
- Do not infer semantic informativeness, listener utility, communicative
  success, or an optimized objective from these measures alone.
- Do not describe Qwen candidates as meaning-preserving alternatives.
- Do not interpret exact-string response entropy as semantic uncertainty.
- Do not pool child and caregiver targets or raw scores from different
  scorers.
- Preserve contrary-direction and interval-crossing results.
- Preserve PBM discovery, non-PBM confirmation, and all-79 descriptive labels.

## Completion gate

The final marker may be written only when:

1. both authoritative wide tables pass schema and hash audits;
2. child and caregiver cells cover all available registered age bins and sample
   scopes;
3. U1–U5 fits pass and save finite estimates and uncertainty;
4. U6 support thresholds and exact-string identities are audited;
5. existing Route 1 P1/P2/P3 and Route 2 M1/M2/M4/M5 inventories are present
   and retain their original fit statuses;
6. report values are read from saved artifacts;
7. all output hashes, links, and interpretation labels pass the independent
   audit;
8. focused and repository compatibility tests pass.
