# Bidirectional Dyadic Communicative-Efficiency Protocol

Status: **pre-fit protocol and agent handoff**, 2026-08-29. No coefficient from
the new turn-level adult-to-child or child-to-adult coupling models had been
inspected when this document was written. Existing marginal child, caregiver,
effort, and informativity results were already known, so this is not a pristine
preregistration of the broader project.

This is the canonical plan for the next local scientific-analysis lane. Keep
implementation details and decisions here; keep `AGENTS.md` concise and use
`TODO.md` only for the active checklist.

## Scientific object

The unit is an ordered conversational triad:

```text
caregiver input A_t  ->  child output C_t  ->  caregiver response A_t+1
```

The project asks whether effort, frequency, and scorer predictability are
adapted in both directions, and whether those coupling effects change with
child age. This extends Pawar and Cychosz's age-dependent caregiver-input
analysis from marginal age trajectories to turn-level dyadic accommodation.
It also connects the project's completed fixed-effort predictability and
response-demand analyses to the pending listener-relevant utility analysis.

The intended claim ladder is:

1. **Marginal development:** child and caregiver speech properties change with
   age. These trajectories mostly already exist.
2. **Conditional turn coupling:** properties of `A_t` predict `C_t`, and
   properties of `C_t` predict `A_t+1`, beyond age, effort, stable dyad
   differences, and the immediately preceding adult turn.
3. **Listener-relevant value:** `C_t` improves prediction of the actual
   `A_t+1` relative to the same earlier context without the child utterance and
   relative to a matched shuffled-child control.
4. **Reciprocal developmental adaptation:** the two directional couplings
   change with age and covary across children/dyads.

Only the conjunction of conditional effort allocation, fixed-effort
predictability, and downstream value supports a strong communicative-
efficiency interpretation. Shorter caregiver speech, lower child surprisal,
or a nonzero cross-lag coefficient alone is insufficient.

## Relationship to completed work

Do not refit completed marginal models merely to rename them dyadic:

- `results/utterance_informativity_analysis/` owns child/caregiver marginal
  `k0`, `k3`, context-support, recurrence, and age trajectories.
- `results/full79_joint_efficiency_analysis/` owns child effort adaptation to
  Qwen exact-string response entropy and the fixed-effort child-information
  surfaces.
- `results/bayesian_joint_adaptive_efficiency_20260828/` owns the completed
  focused trivariate child-level Bayesian synthesis.
- `docs/downstream_caregiver_response_efficiency_protocol.md` owns the frozen
  definition and confirmation rule for downstream predictive gain.

The new contribution is the exact temporal join and within-dyad coupling, not
another presentation of separate child and caregiver age curves.

## Authoritative inputs and readiness

| Object | Authoritative artifact | State and next action |
|---|---|---|
| Child Mistral `k0`-`k3` and effort | `results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz` | Ready; audit exact joins by dataset/child/file/line/text hash. |
| Caregiver Mistral `k0`-`k3` and effort | `results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz` | Ready; 1,470,154 source rows, with validity filtering inherited from the existing report. |
| Ordered turns and speaker codes | `results/conversational_eligibility/full79_child_conversational_flags.csv.gz` | Ready; contains previous/next main speaker, exact raw-line alignment, response-function candidates, and turn eligibility. |
| Frozen response handoff | `results/downstream_caregiver_response_handoff/full_20260827/` | Ready; 613,741 sensitivity rows and 413,084 strict caregiver-child-caregiver triads. |
| Qwen response demand and child cloud position | `results/full79_joint_efficiency_analysis/metrics/model_rows.parquet` | Ready for child-side demand controls; exact-string entropy is not semantic uncertainty. |
| Frequency/informativity comparators | `results/utterance_informativity_analysis/` and `results/route1_frequency_informativity_predictors/` | Reuse audited products. Empirical recurrence, Mistral `k0`, and contextual `k3` are distinct. |
| Five-condition caregiver-response scores | External compute run documented in `AGENTS.md` | **Not analysis-ready.** Require completed scorer archives and a local relocation audit before joining or inspecting results. |
| Repair/clarification/acknowledgement labels | Candidate flags plus the planned 325-row manual review | Candidate flags are descriptive only until manual validation passes. |

The downstream handoff omits explicit caregiver speaker columns, but its
source conversational-flags table contains `previous_main_speaker` and
`next_main_speaker`. Add these as a hash-audited sidecar; do not mutate the
frozen scoring handoff. The primary analysis remains **caregiver** speech. A
parent-only `MOT`/`FAT` analysis is a registered sensitivity only after CHAT
participant metadata verify those roles within each file.

## Measures and non-substitution rules

For `A_t`, `C_t`, and `A_t+1`, retain separate measures of:

- effort: words primary; morphemes, syllables, and phoneme proxies as validated
  sensitivities;
- unconditional form self-information: `k0 = -log2 p(u)`;
- contextual self-information: `k3 = -log2 p(u | preceding context)`;
- context support: `k0 - k3`;
- empirical exact-string or lexical frequency when supported;
- question, routine/reading, imitation/backchannel, repair, clarification, and
  acknowledgement indicators.

Never enter `k0`, `k3`, and `k0-k3` together in one linear predictor: they are
algebraically dependent. Use `k3` as the primary scorer-predictability
predictor at fixed exact/top-coded word effort. Fit `k0` and context support as
separately named decomposition models. Do not substitute bits per tokenizer
token for the primary total-bit fixed-effort estimand.

For every turn-level predictor `X`, separate momentary and stable variation:

```text
X_within  = X - child/session reference mean
X_between = child/dyad reference mean
```

The within component is the accommodation estimand. The between component
prevents stable differences between children, caregivers, recordings, or
corpora from masquerading as immediate modulation. Reference means and their
scope must be frozen in the analysis contract.

## Registered questions and hypotheses

### D1: caregiver input to child output

Does momentary caregiver input predict the child's next effort or fixed-effort
predictability, and does that relationship change with age?

- D1a primary outcome: child `k3` total bits with exact/top-coded child effort
  controlled.
- D1b complementary outcome: child word effort under a negative-binomial
  likelihood.
- Theory expects local alignment/facilitation, but competing accommodation
  mechanisms make the coefficient and age interaction two-sided.

### D2: child output to caregiver effort

Does child predictability modulate the length of the immediately following
caregiver response, beyond `A_t`, child age, and child effort?

- Primary outcome: `A_t+1` lexical word count.
- Theory-tracked direction: higher child `k3` surprisal is followed by greater
  caregiver effort.
- The primary test remains two-sided because successful contingent elaboration
  can also produce longer responses after highly predictable child speech.

### D3: child output to caregiver response function

Does higher child surprisal predict repair or clarification rather than
acknowledgement/contingent continuation? Fit this only after the manual label
gate. Response-function variables are outcomes or stratifiers, not ordinary
confounds in D2.

### D4: downstream predictive utility

Use the already frozen outcome:

```text
U(C_t; A_t+1, A_t)
  = -log2 p(A_t+1 | A_t)
    - [-log2 p(A_t+1 | A_t, C_t)]
```

Positive `U`, matched-child gain exceeding shuffled-child gain, and a positive
fixed-effort age slope in the other-58 confirmation sample are all required by
the downstream protocol. Report Mistral, TinyDialogues, and Qwen separately.

### D5: reciprocal developmental coordination

Estimate whether child-specific/dyad-specific `A_t -> C_t` and
`C_t -> A_t+1` slopes covary, and whether their population means change with
age. Correlation is coordinated variation, not proof of optimization or
causality.

## Frequentist lane

The frequentist lane owns the nonlinear population surfaces and the frozen
discovery/confirmation decisions. Use the same exclusions and formulas across
PBM discovery, other-58 confirmation, and all-79 descriptive scopes.

Register a bounded core inventory:

1. **F1 adult-to-child predictability:** robust GAMM/scaled-t model for child
   `k3`, with nonlinear age, caregiver `k3_within`, their interaction, both
   turns' effort controls, child/session structure, and corpus nuisance.
2. **F2 adult-to-child effort:** negative-binomial GAMM for child words from
   caregiver predictability/effort, age interaction, and conversational
   controls.
3. **F3 child-to-adult effort:** negative-binomial GAMM for response words from
   child `k3_within`, nonlinear age interaction, child effort, `A_t` effort and
   predictability, question type, child/session effects, and corpus nuisance.
4. **F4 response function:** logistic mixed models for validated repair and
   clarification outcomes; unavailable until manual validation.
5. **F5 downstream utility:** the opportunity-weighted, child-clustered model
   already frozen in the downstream protocol; unavailable until score intake.

Use separate `k0` and context-support decomposition fits for F1-F3. They are
registered sensitivities, not a combinatorial model zoo. Do not control the
primary response-length model for the realized response function, because it
may mediate the child-to-caregiver association.

Required uncertainty and robustness:

- child/session-aware covariance and whole-child bootstrap;
- leave-one-child and leave-one-corpus influence;
- supported-age predictions rather than endpoint extrapolation;
- equalized age-bin bootstraps modeled on Pawar and Cychosz;
- group-level and row-level age-label scrambling;
- within-age/session turn-pair shuffling for each directional coupling;
- comparison with unchanged marginal models, without outcome-selected
  replacement.

## Bayesian lane

Follow the methodological translation in
`docs/bayesian_route1_route2_program_2026-08-28.md` from Levshina's *A Bayesian
dawn in linguistics*:

- use partial pooling because child, caregiver, session, and corpus effects are
  heterogeneous;
- choose likelihoods appropriate to counts and robust continuous outcomes;
- make direct posterior statements about magnitude, direction, and practical
  equivalence;
- require prior predictive checks, synthetic recovery, sampler diagnostics,
  posterior predictive checks, and prior sensitivity;
- do not use Bayes factors as the primary decision rule;
- never construct priors from PBM point estimates. PBM is a sample label, not
  prior information.

Avoid another raw-row 100-plus-fit NUTS grid. The preferred bounded synthesis
is a multivariate child/dyad-level measurement-error model over jointly
estimated first-stage coefficients:

```text
theta_i = [adult_to_child_k3,
           adult_to_child_effort,
           child_to_adult_effort,
           child_to_adult_utility]

theta_hat_i ~ MVN(theta_i, V_i)
theta_i     ~ MVN(population + corpus/dyad effects, Sigma_between)
```

The first three coefficients can be fitted once the triad dataset passes its
audit. Append utility only after complete score intake. Recover the shared
session-clustered or joint-bootstrap covariance `V_i`; stop rather than assume
independent measurement errors if it cannot be estimated reliably.

The frequentist nonlinear models remain primary for detailed age surfaces.
The Bayesian model answers the additional joint question: how large are the
directional population effects, how heterogeneous are they, and do their
child-level slopes covary? Freeze standardized units, weakly regularizing
primary priors, skeptical/wider sensitivities, and effect-scale ROPEs before
posterior fitting. Pilot one real-data fit and project the complete inventory;
do not repeat the stopped 8,312-CPU-hour program.

## Dataset and sample contract

Build one immutable triad table with columns for `A_t`, `C_t`, and `A_t+1`.
Every joined text must match its normalized SHA-256 and exact
dataset/child/file/line identity. Record one-to-one multiplicities and reasons
for every excluded row.

Scopes:

- primary: 413,084 strict caregiver-child-caregiver triads;
- sensitivity: the broader 613,741 immediate-response rows;
- discovery: Brown, Manchester, and Providence;
- confirmation: the other ten strict-naturalistic corpora;
- descriptive: pooled all-79;
- parent-only sensitivity: metadata-validated mother/father turns only.

Before fitting any new coefficient, freeze a machine-readable contract with
input hashes, row identities, support/exclusion rules, formulas, directions,
ROPEs, priors, bootstrap seeds, and completion gates. The new coupling
coefficients are outcome-blind at protocol creation, but underlying marginal
outcomes were inspected previously; report that distinction.

## Execution order and compute map

### Local work that can start now

1. Implement and test the exact three-turn dataset/sidecar builder.
2. Audit speaker roles, join coverage, hashes, multiplicities, missingness,
   age/effort support, and within/between decompositions.
3. Freeze the final contract before exposing discovery coefficients.
4. Fit F1-F3 in PBM discovery, then run the unchanged other-58 confirmation
   and all-79 descriptive fits.
5. Run scrambles, bootstraps, and influence checks.
6. Fit the bounded Bayesian three-coefficient synthesis after synthetic and
   real-data runtime gates.

This requires no new neural scoring and should remain a bounded local CPU
analysis. Parent-response word effort is already in the handoff.

### Work blocked on existing external computation

1. Diagnose the failed downstream context-audit jobs in
   `compute_surprisal_mila`; resume from valid stage markers rather than rerun
   completed preparation/smoke/scoring work.
2. Finish all five conditions for each scorer and require
   `SURPRISAL_COMPLETE` and `ARCHIVE_READY`.
3. Rsync each compact archive locally and pass an independent relocation audit.
4. Only then construct `U`, fit F5, and extend the Bayesian synthesis with the
   utility coefficient.

Partial Mila waves and the local PBM TinyDialogues smoke/prototype directories
are not scientific results and must not be joined prematurely.

### Work blocked on measurement validation

1. Add caregiver speaker identity as an audited sidecar and verify parent
   roles from CHAT metadata.
2. Complete the frozen 325-row manual validation of repair, clarification,
   acknowledgement, imitation, and routine candidates.
3. Fit F4 and parent-only sensitivities only after their respective gates.

Semantic-cluster response entropy is a useful future measurement extension,
but it is not required for the primary bidirectional analysis.

## Planned implementation namespace

Use an isolated, staged namespace:

```text
configs/bidirectional_dyadic_efficiency_20260829/analysis_contract.json
results/bidirectional_dyadic_efficiency_20260829/
figs/bidirectional_dyadic_efficiency_20260829/
docs/bidirectional_dyadic_communicative_efficiency_report.md
docs/bidirectional_dyadic_communicative_efficiency_report.html
src/build_bidirectional_dyadic_efficiency_20260829.py
src/fit_bidirectional_dyadic_efficiency.R
```

Required stages:

```text
contract-draft -> dataset -> contract-freeze -> support
               -> frequentist -> frequentist-validation
               -> bayesian-smoke -> bayesian-fit -> bayesian-diagnostics
               -> utility-intake -> utility-models
               -> synthesis -> plots -> report -> audit
```

Stages blocked by absent utility scores must record `WAITING_FOR_AUDITED_SCORES`
without inventing placeholder values or marking the whole local lane failed.
Plot and report stages consume saved artifacts only. Final completion requires
hash-valid predecessors, zero unregistered model substitutions, passing
frequentist and Bayesian diagnostics, and an independent final audit marker.

## Interpretation contract for future agents

- Say **caregiver** unless participant metadata establish parent identity.
- Say **predicts**, **is followed by**, or **is consistent with accommodation**;
  do not say a child utterance causally changes the caregiver response.
- Lower surprisal is scorer predictability/conventionality, not more Shannon
  information or listener success.
- Shorter caregiver speech is not efficiency without preserved downstream
  gain or validated response-function evidence.
- Longer caregiver speech can be successful contingent elaboration; response
  length therefore has a two-sided primary decision rule.
- Separate frequency, `k0`, `k3`, context support, effort, and utility.
- Do not pool raw bits across tokenizers or use generated responses as
  meaning-preserving alternatives.
- Corpus is validation/nuisance structure, not the scientific question.
- Observational reciprocal coupling is not proof that either speaker optimizes
  a common objective.
