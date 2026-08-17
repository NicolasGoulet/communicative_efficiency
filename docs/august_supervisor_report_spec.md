# August supervisor report v1: frozen evidence contract

Frozen on 2026-08-17 from repository commit
`ced13d9d81de7469a35080ed78daac2bd5d24cb6`. The authoritative
machine-readable contract is `configs/august_supervisor_report_v1.json`.
Downstream August stages may summarize, arrange, link, and render this evidence;
they may not inspect unregistered outcomes, fit or select models, generate new
plots, change an estimand, or reinterpret a registered direction.

## Status and schema contract

Every claim has a stable ID and exactly one role: `PROMOTED`, `SUPPORTING`,
`EXCLUDED`, or `PENDING`. Every claim also has exactly one evidence status:

- `SUPPORTED`: the audited result supports the registered within-claim reading;
- `QUALIFIED`: the result is usable only with its stated evidential or
  measurement qualification;
- `CONTRARY`: the audited direction is opposite the registered prediction;
- `DESCRIPTIVE`: the result is a non-causal description and is not evidence for
  a developmental or causal claim;
- `PENDING`: no admissible estimate exists because a named artifact or
  validation gate is missing.

Each JSON claim records its scientific question; exact sample role and scope;
row, child, session, and corpus counts where available; scorer and tokenizer
rule; estimand, outcome, formula or contrast, controls, and sign convention;
estimate, interval, and uncertainty method where numerical; evidence status;
canonical source artifact and SHA-256; required audit or completion marker;
mandatory interpretation and limitation language; destination section; and
figure eligibility. A null count means the audited artifact does not supply a
defensible exact count for that field. It is not permission to estimate one.

Numerical prose in later reports must resolve to one claim ID. The value and
uncertainty must be copied from that claim's hashed canonical artifact. A
missing or changed source hash, a failed marker, or a conflict between sources
is a blocker; it cannot be silently repaired by refitting, rounding from a
plot, or selecting a different result.

## Page contract

The three deliverables are frozen as:

- `docs/august_supervisor_index.html` — consultation landing page;
- `docs/august_supervisor_report.md` — copy-ready scientific source;
- `docs/august_supervisor_report.html` — rendered supervisor report.

They use the same ordered sections: executive scientific answer; utterance
predictability at fixed effort; word-level cross-scorer robustness;
response-space effort adaptation; corrected candidate-set Bayes evidence;
developmental onset; Hall historical snapshot; pending evidence and blockers;
interpretation guardrails; and audited technical resources.

The landing page and report must link to these existing resources:

| Resource | Frozen path |
|---|---|
| Direct-results explorer | `docs/direct_surprisal_results_explorer.html` |
| Word cross-scorer comparison | `docs/word_cross_scorer_comparison.html` |
| Hall snapshot | `docs/hall_snapshot_mistral_analysis.html` |
| Corrected Bayes report | `docs/corrected_pbm_bayes_report.html` |
| Sustained-onset report | `docs/direct_surprisal_onset_confirmation.html` |
| Child trajectories | `docs/paired_tinydialogues_mistral_child_trajectories.html` |
| Formal definitions | `docs/july_meeting_definitions.html` |
| Technical analysis inventory | `docs/complete_analysis_machine_index.html` |

Only already-audited figures associated with a claim marked `PRIMARY` or
`SUPPORTING` may be embedded. `EXCLUDED` and `PENDING` claims are not eligible
for inferential figures. Rendering consumes frozen artifacts and must not fit
models or generate plots.

## Locked readings

These readings are mandatory, not optional caveats:

| Reading ID | Frozen reading |
|---|---|
| `NONPBM_CONTEXTUAL_QUALIFIED` | Non-PBM contextual Mistral is negative and direction-consistent, but the frozen child-clustered primary interval crosses zero; confirmation was not achieved. |
| `NONPBM_BOOTSTRAP_SENSITIVITY` | The 1,000-replicate child bootstrap is sensitivity evidence beside the clustered primary interval, never a replacement for it. |
| `CONTEXT_GAIN_CONTRARY` | Utterance context-gain development is negative in TinyDialogues PBM, Mistral PBM, and Mistral non-PBM, contrary to the registered positive direction. |
| `PBM_CROSS_SCORER_ROBUSTNESS` | Repeating analyses with TinyDialogues, Qwen3-14B, and Mistral on the same 21 PBM children is scorer robustness, not independent-sample confirmation. |
| `TOKENIZER_MAGNITUDES_NOT_POOLED` | Raw bits and coefficient magnitudes are not pooled across tokenizers. |
| `SUSTAINED_ONSET_NOT_ESTABLISHED` | The frozen simultaneous-band rule establishes no sustained onset in PBM or non-PBM. |
| `EXACT_STRING_ENTROPY_LIMIT` | Exact-string response entropy depends on model, prompt, temperature, seed, sampling, and surface form; it is not semantic uncertainty. |
| `GENERATED_CANDIDATES_MEANING_LIMIT` | Random, n-gram, LSTM, and unconstrained LLM alternatives do not preserve the child's intended meaning. |
| `BAYES_FINITE_CANDIDATE_SET` | Corrected Bayes probabilities are normalized only over each row's available finite matched candidate set. |
| `HALL_SEPARATE_DESCRIPTIVE` | Hall is a separate historical, cross-sectional, descriptive, non-causal, and non-deficit snapshot—not an 80th longitudinal child or a 14th longitudinal corpus. |
| `WORD_NONPBM58_PENDING` | Remaining-58 same-pass word confirmation has not run. |
| `LISTENER_UTILITY_PENDING` | A validated downstream listener-utility outcome does not yet exist. |
| `CONVERSATIONAL_VALIDATION_PENDING` | Conversational eligibility remains at REVIEW pending manual validation. |
| `DECOUPLED_RESPONSE_CALIBRATION_PENDING` | Semantic, rarefaction, sampling-setting, and decoupled-generator calibration is missing. |
| `ALTERNATIVE_EFFORT_ONSET_PENDING` | Sustained-onset analyses using validated morpheme, syllable, and phoneme effort are missing. |

## Frozen claim registry

### Utterance-level fixed-effort evidence

| Claim ID | Role | Status | Required reading |
|---|---|---|---|
| `DIRECT_PBM_MISTRAL_CONTEXTUAL` | PROMOTED | SUPPORTED | PBM Mistral contextual surprisal decreases by 0.131 bits/month at fixed word effort (clustered 95% CI -0.179 to -0.083). This is predictability/conventionality, not listener utility or a normative optimum. |
| `DIRECT_PBM_TINY_CONTEXTUAL` | SUPPORTING | SUPPORTED | The negative P1 direction repeats under TinyDialogues (-0.222, clustered 95% CI -0.311 to -0.132) on the same PBM children. |
| `DIRECT_PAIRED_CONTEXTUAL_SCORER_DIFFERENCE` | SUPPORTING | QUALIFIED | On 443,848 exact paired rows, the Tiny-minus-Mistral P1 slope difference is -0.089 (paired bootstrap 95% interval -0.152 to -0.028); magnitude is scorer-calibration dependent. |
| `DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY` | PROMOTED | QUALIFIED | The 58-child primary slope is -0.062 bits/month with child-clustered 95% CI -0.132 to +0.007: direction-consistent, not confirmed. |
| `DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP` | SUPPORTING | QUALIFIED | The 1,000-child-bootstrap mean is -0.066 with percentile interval -0.157 to -0.011. It is sensitivity evidence and must not replace the primary clustered interval. |
| `DIRECT_PBM_MISTRAL_UNCONDITIONAL` | SUPPORTING | SUPPORTED | PBM unconditional Mistral surprisal decreases at fixed effort (-0.162, clustered 95% CI -0.211 to -0.112). |
| `DIRECT_PBM_TINY_UNCONDITIONAL` | SUPPORTING | SUPPORTED | PBM unconditional TinyDialogues surprisal also decreases (-0.254, clustered 95% CI -0.339 to -0.168), as same-sample robustness. |
| `DIRECT_NONPBM_MISTRAL_UNCONDITIONAL` | SUPPORTING | SUPPORTED | Non-PBM unconditional Mistral surprisal decreases (-0.089, clustered 95% CI -0.145 to -0.034), but this is not the registered P1 confirmation criterion. |
| `DIRECT_PBM_MISTRAL_CONTEXT_GAIN` | PROMOTED | CONTRARY | PBM Mistral k0-minus-k3 context gain declines with age (-0.030, clustered 95% CI -0.050 to -0.011), contrary to the registered positive direction. |
| `DIRECT_PBM_TINY_CONTEXT_GAIN` | SUPPORTING | CONTRARY | PBM TinyDialogues context gain also declines (-0.032, clustered 95% CI -0.050 to -0.014), a same-sample contrary-direction robustness result. |
| `DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN` | PROMOTED | CONTRARY | Non-PBM Mistral context gain declines (-0.028, clustered 95% CI -0.045 to -0.010), confirming an opposite sign rather than the registered positive hypothesis. |

PBM discovery and the 58-child non-PBM confirmation sample remain separate in
all text and displays. A lower direct target surprisal is a more predictable
target under the scorer; it is not “more Shannon information.” Unconditional
surprisal, contextual surprisal, and context gain are separate estimands.

### Word-level robustness

| Claim ID | Role | Status | Required reading |
|---|---|---|---|
| `WORD_CROSS_SCORER_PREDICTABILITY` | SUPPORTING | SUPPORTED | On the identical 1,032,963-occurrence PBM set, same-word k0 and k3 age effects are negative with interval support in all three separately fit scorers. |
| `WORD_LONGER_TYPES_CONTEXT_SUPPORT` | SUPPORTING | SUPPORTED | At centered age, longer word types receive more context support with direction and interval robustness in all three scorer-specific fits. |
| `WORD_CONTEXT_GAIN_SCORER_DEPENDENT` | SUPPORTING | QUALIFIED | Word-level context-gain development has mixed signs and only one scorer with clustered and bootstrap support; it is scorer-dependent. |

The three word archives share the same occurrence identity hash, but their
effects were fit separately. This is PBM scorer robustness. It neither pools
raw bits nor supplies the unrun remaining-58 word confirmation.

### Response-space and corrected Bayes evidence

| Claim ID | Role | Status | Required reading |
|---|---|---|---|
| `ROUTE2_RELATIVE_EFFORT_AGE` | SUPPORTING | QUALIFIED | In the final session GEE, relative child word effort rises by 0.089 words/month (95% CI 0.078 to 0.101); this is relative to a generated, potentially mediating reference. |
| `ROUTE2_AGE_ENTROPY_INTERACTION` | PROMOTED | CONTRARY | The age-by-exact-string-response-entropy interaction is -0.0248 (95% CI -0.0384 to -0.0112), opposite the simple increasing-length prediction. |
| `BAYES_REAL_CANDIDATE_SET_PROBABILITY` | SUPPORTING | SUPPORTED | The observed utterance ranks first on 43.7% of 446,508 real rows and has mean candidate-set probability 0.400, strictly within the available finite set. |
| `BAYES_HELDOUT_CONTEXT_VALIDATION` | SUPPORTING | SUPPORTED | Brown, Manchester, and Providence all pass the held-out matched-versus-shuffled context-evidence gate. |

The Route 2 findings are measurement-limited. Generated expected effort is a
model-based reference and possible mediator, not an ordinary automatic
confound. Corrected Bayes fixes the original overlap and weak-context defects,
but does not become a posterior over all possible utterances or replace direct
Mistral surprisal.

### Onset and Hall

| Claim ID | Role | Status | Required reading |
|---|---|---|---|
| `ONSET_PBM_SUSTAINED` | PROMOTED | QUALIFIED | With 1,000 child bootstraps and simultaneous max-absolute-studentized bands, PBM sustained onset is not established. |
| `ONSET_NONPBM_SUSTAINED` | PROMOTED | QUALIFIED | Under the same frozen rule, non-PBM sustained onset is not established. |
| `HALL_RACE_CLASS_INTERACTION` | SUPPORTING | DESCRIPTIVE | The primary Hall k0 race-by-class interaction is -3.516 Mistral bits (child-clustered 95% CI -5.730 to -1.302), a historical scorer-indexed description only. |
| `HALL_ADULT_CONTEXT_INTERACTION` | SUPPORTING | DESCRIPTIVE | The adult-adjacent k3 context-support interaction is -0.213 bits (95% CI -1.105 to 0.679), with an interval crossing zero. |
| `HALL_LOCKED_DOMAIN_SHIFT` | SUPPORTING | DESCRIPTIVE | Hall-minus-locked-current k0 is +3.037 bits (95% CI 2.041 to 4.032), evidence of domain/era/dialect/transcription sensitivity, not a causal cohort effect. |

The exact onset is not settled, and the earlier nominal 24–29-month contrast
cannot be promoted. Hall must never be described as a causal SES analysis,
linguistic deficit, inherent group efficiency difference, or longitudinal
developmental result. Setting, dialect, recording era, geography,
transcription, and language-model representation remain live explanations.

### Excluded interpretations

| Claim ID | Role | Status | Exclusion |
|---|---|---|---|
| `CROSS_TOKENIZER_MAGNITUDE_POOLING` | EXCLUDED | QUALIFIED | No pooled raw-bit or pooled coefficient claim across Mistral, Qwen3-14B, and TinyDialogues is admissible. |
| `RESPONSE_ENTROPY_SEMANTIC_CLAIM` | EXCLUDED | QUALIFIED | Exact-string entropy cannot be called semantic response uncertainty. |
| `GENERATED_CANDIDATE_MEANING_PRESERVATION` | EXCLUDED | QUALIFIED | Current generated alternatives cannot support intended-meaning, rational-choice, meaning-preserving, or Pareto-frontier claims. |

### Pending claims and blockers

| Claim ID | Role | Status | Verified blocker |
|---|---|---|---|
| `WORD_NONPBM58_CONFIRMATION` | PENDING | PENDING | The registered same-pass Mistral production is implemented but unrun; the preflight component is `BLOCKED`, with no audited score handoff or estimate. |
| `LISTENER_UTILITY_OUTCOME` | PENDING | PENDING | No validated downstream caregiver-response or repair/clarification/contingency outcome, frozen analysis, or completion marker exists. |
| `CONVERSATIONAL_MANUAL_VALIDATION` | PENDING | PENDING | The 1,140,218-row structural flag audit remains `REVIEW`; 18,172 eligible k1 mismatches require characterization and the 325-row stratified sample remains uncoded. |
| `DECOUPLED_RESPONSE_CALIBRATION` | PENDING | PENDING | Semantic clustering, rarefaction, prompt/temperature/seed sensitivities, and a decoupled generator are absent. |
| `ALTERNATIVE_EFFORT_ONSET` | PENDING | PENDING | The PASS onset audit covers word effort only; full-79 validated morpheme, syllable, and phoneme onset products do not exist. |

Pending evidence is displayed as pending, never converted to a null finding.
Resolution requires a registered artifact and PASS/COMPLETE marker. It does not
authorize a later stage to inspect an adjacent unregistered outcome.

## Artifact and marker audit

The claim-level JSON pins each canonical SHA-256 and marker. The principal
verified gates are:

- direct Mistral: 102 recorded model rows, 93 ordinary passes, eight
  singular/boundary sensitivities, one nonconverged mixed sensitivity, zero
  failed primary/direct fits, and 1,000 bootstrap/permutation replicates;
- direct TinyDialogues: 34 recorded model rows, 31 ordinary passes, three
  singular/boundary sensitivities, zero failures, and 1,000 replicates;
- paired direct analysis: 446,508-row immutable paired universe, 11 outcomes,
  1,000 paired child bootstraps, and `COMPLETE` model status;
- word comparison: local manifest `PASS`, three scorer-specific
  `COMPLETE_AND_AUDITED` markers, and shared primary occurrence identity
  SHA-256 `4b12305ba8ff6ec2fc96557b68aa6b921dd34bb6f0d05023fcf8451a93bcb437`;
- corrected Bayes: 2,232,524 candidate rows and all three held-out context
  validations passing;
- onset: `PASS`, 1,000 successful child bootstraps in both scopes, and
  `not_established` in both scopes;
- Hall: 20/20 registered models passed, 72 contrasts, 1,000 child bootstraps
  for five primary model families, nine audited figures, `PASS` final audit,
  zero problems, and `ANALYSIS_COMPLETE_AND_AUDITED` present.

The report is not permitted to turn an audit warning, singular sensitivity, or
missing marker into a result. The technical inventory is a navigation aid, not
an invitation to select among its 607 fitted rows.
