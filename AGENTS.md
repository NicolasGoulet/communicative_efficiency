# AGENTS.md

Persistent guidance for coding agents working in this repository.

This file is the high-level project compass. Lower-level tasks belong in
`TODO.md`; longer design discussion belongs in `docs/design.md`; running notes
and decisions belong in `docs/notes.md`.

## Project Overview

Working title: **On Communicative Efficiency of Child Language Use**

This repository is the local **brain, analysis, and reporting repository** for
the project. It owns CHILDES / CHAT preparation and cleaning, scorer-ready
bundles, analysis-ready tables, statistical models, diagnostics, metadata,
plots, and supervisor-facing reports.

This repository is **not** the main place for large-scale LLM surprisal
scoring. Direct Mistral scoring and HPC audits belong in the sibling
`compute_surprisal_mila` repository. Baseline generation, Bayes-decomposition
execution, and complexity extraction also have lightweight sibling execution
repositories. This repo receives compact, audited products from them and owns
the scientific synthesis. Large outputs remain outside Git.

Broad scientific objects:

- **model-based predictability / self-information**: direct contextual
  Mistral or TinyDialogues surprisal `-log2 p(u | c)`, unconditional utterance
  surprisal `-log2 p(u)`, their context-gain difference, and exploratory
  Bayes-decomposition scores based on `p(u) p(c | u)`;
- **listener-relevant utility**: not yet a validated primary product; proposed
  measures include downstream caregiver-response predictive gain and coded
  repair, clarification, acknowledgement, or contingent continuation;
- **effort / complexity**: utterance length, morphemes, syllables, MLU-style
  measures, phoneme proxies, lexical trajectories, and related diagnostics;
- **efficiency**: currently studied through two complementary questions:
  information at fixed production effort, and production effort relative to
  contextual predictability / a generated response space.

The project currently has four primary analysis tracks. Use these plain names
instead of assuming that an internal "Route 1" or "Route 2" label is
self-explanatory:

1. **Utterance-level predictability**: model unconditional utterance
   surprisal, contextual utterance surprisal, and context support as children
   age, with effort and stable child identity controlled explicitly; compare
   real child utterances with caregiver utterances and clearly named generated
   baselines where the comparison is valid.
2. **Utterance-level effort adaptation**: model words, morphemes, syllables,
   phoneme proxies, or related effort outcomes from age and conversational
   conditions, both as raw child effort and relative to the generated response
   distribution for the same context.
3. **Word-level contextual support**: test whether lexical rarity and age
   interact such that relatively rare words become increasingly supported by
   their utterance/conversational context, while controlling word identity,
   position, utterance properties, and child identity.
4. **Joint information-effort response clouds**: locate each observed child
   utterance inside the information-by-effort cloud of Qwen responses to the
   same context and model how that location changes with age. This is a
   generated-response-space comparison, not proof of an optimum or a
   meaning-preserving choice set.

Do not equate lower surprisal, higher surprisal, shorter speech, or longer
speech with communicative efficiency in isolation. State the estimand and
controls explicitly. In particular, the current negative fixed-effort age
slope means that older children's utterances are more predictable to Mistral at
the same measured effort; it is not by itself proof of a single normative
efficiency optimum.

## Scientific Interpretation Guardrails

The current evidence supports a narrower claim than the working project title:

- the strongest PBM result is increasing **predictability / conventionality of
  form at fixed measured effort** with child age;
- direct target surprisal `-log2 p(u | c)` is self-information under the
  scorer. A lower value means a more predictable target, not "more Shannon
  information";
- context gain
  `log2 p(u | c) - log2 p(u)` is the cleaner available measure of how much the
  preceding context supports the observed utterance and should be kept
  separate from unconditional form frequency;
- a stronger listener-utility analysis requires a downstream outcome, such as
  the gain in predicting the next caregiver response from the child utterance,
  or validated repair / clarification / contingent-response labels;
- the current exact-string response entropy is model-, prompt-, temperature-,
  and surface-form-dependent. It is not yet semantic response uncertainty;
- for effort adaptation, raw child effort and effort relative to a generated
  response distribution are different estimands. Generated expected effort is
  a model-based reference and may mediate contextual demand, so do not add it
  automatically as an ordinary confound in the primary total-association
  model. Keep models with and without that reference separate;
- next-token context entropy is a useful local uncertainty control, but it is
  not a substitute for entropy over complete plausible responses;
- random, n-gram, LSTM, and unconstrained LLM alternatives do not preserve the
  observed child's intended meaning. Do not make Pareto-optimality or
  meaning-preserving choice claims from those candidate sets.

Treat Brown, Manchester, and Providence (21 children) as the current discovery
sample. Before inspecting confirmatory estimates, freeze the primary outcomes,
effect directions, exclusions, model formulas, and onset rule. The remaining
58 children across the other 10 strict-naturalistic corpora are the preferred
confirmation sample now that the direct-Mistral 79-child scoring tree is
available. TinyDialogues currently covers the same 21 PBM children, so it is a
scorer-robustness analysis rather than an independent sample confirmation.
Observational CHILDES results can be described as consistent with developmental
adaptation or efficiency, but do not by themselves prove that children
optimize an objective.

Treat Hall as a separate cross-sectional sociolinguistic snapshot, not as an
80th longitudinal child or a 14th strict-naturalistic corpus. Its historical
race/social-class strata support within-Hall descriptive contrasts near age
four, with child-clustered uncertainty and explicit setting controls. Any
race/class score difference may reflect dialect, recording era, geography,
transcription, setting, or language-model representation; do not interpret it
as a causal SES effect, linguistic deficit, or inherent group efficiency.

## Current Active Data And Analysis State

The authoritative longitudinal handoffs and local Route 1/Route 2 products
below were rechecked on 2026-08-25; the Bayesian pilot state was verified on
2026-08-28; and the Hall snapshot state below was verified on 2026-08-17. When
any later historical paragraph conflicts with the dated
analysis-ready map in this section, use this section.

Primary external scored/feature handoffs:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023
results/external/compute_surprisal_mila/raw_surprisal_lstm_additive_same_length
results/external/compute_surprisal_mila/context_entropy_mistral
results/external/compute_surprisal_mila/raw_surprisal_heldout_real_child_generalization_2026-06-16
results/external/compute_surprisal_mila/raw_surprisal_cleaned_naturalistic_79_children_all_available_ages_fp16
results/external/compute_surprisal_mila/raw_surprisal_tinydialogues_pbm_21_children_all_6_conditions_k0_k1_k2_k3_fp32
results/external/compute_surprisal_mila/hall_snapshot_mistral_word_surprisal_20260813_66812c4
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa
```

These are symlinks into:

```text
/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/
```

Use the model- and sample-appropriate path for each analysis. Do not copy the
multi-GB scored trees into Git. Prefer
`raw_surprisal_cleaned_mistral_patched_006_023` for new analyses: it is a
complete PBM scored tree where the 006-023 generated-baseline patch has been
merged into the main cleaned Mistral results. New Mila products should be
symlinked here only after they have been rsynced locally and passed audits in
`compute_surprisal_mila`.

### Authoritative analysis-ready data map (2026-08-25)

For new work, start from these products rather than reconstructing paths from
old reports:

- **Utterance-level predictability, all 79 children / 13 corpora**:
  `results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz`
  is the 1,140,695-row child table and
  `results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz`
  is the 1,470,154-row caregiver table. Their source and scope contract is
  `results/direct_surprisal_replication/mistral_full79/manifest.json`; their
  staged analysis is under
  `results/direct_surprisal_replication/mistral_full79/modular/`. The raw
  scored-tree symlink is
  `results/external/compute_surprisal_mila/raw_surprisal_cleaned_naturalistic_79_children_all_available_ages_fp16`.
- **PBM utterance comparisons with generated baselines**:
  `results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz`
  contains the PBM real, random, unigram, bigram, trigram, and additive
  same-length LSTM comparisons. Use
  `results/direct_surprisal_replication/tinydialogues_pbm/` and
  `results/direct_surprisal_replication/paired_tiny_mistral_pbm/` for the
  PBM TinyDialogues and paired-scorer products. These products are not
  remaining-58 confirmation data.
- **Completed all-79 additive-LSTM generation and Mistral scoring handoff**:
  `/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/lstm_full79_mistral_scoring/current/`
  is the canonical local symlink to the immutable audited handoff. It contains
  1,140,218 scorer-ready same-length additive-LSTM targets for all 79 children,
  with utterance-level Mistral `k0` and `k3` scores. Its audit is `PASS`,
  `markers/COMPLETE_AND_AUDITED` is present, and the compressed score table has
  SHA-256 `03af2bc6abbca362eb9c7529b921e84048d65f68f6c950b841384e187271345e`.
  This completed compute product has **not yet been linked into
  `results/external/compute_surprisal_mila/` or ingested into the fixed-effort
  all-79 cloud analysis**. Do not rerun generation or scoring; the next task is
  local import, exact identity/hash audit, analysis rebuild, and report update.
- **All-79 Qwen response space for effort and joint clouds**:
  `results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa`
  is the canonical symlink to the extracted, audited handoff at
  `/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/qwen_response_mistral_full_scoring/20260817_qwen_response_mistral_full75_smoke_f5dd5aa_v1/extracted_run`.
  Within it,
  `prepared/inputs/core75/` and `prepared/inputs/extension25/` contain all 100
  generated response texts per context; `processed/core75/` and
  `processed/extension25/` contain per-response Mistral k0/k3 utterance
  scores; and `context_means/full100/` contains the 100-response means.
  `CORE75_COMPLETE`, `EXTENSION25_COMPLETE`, and `FULL100_AVAILABLE` must all
  be present before use.
- **Completed all-79 effort/cloud analysis**:
  `results/full79_joint_efficiency_analysis/` is the primary conditional
  effort-and-information product. Its 15/15 registered nonlinear models and
  38/38 independent audit checks passed, and
  `FULL79_JOINT_EFFICIENCY_COMPLETE_AND_AUDITED` is present. Read
  `docs/full79_joint_efficiency_pipeline.md` before rebuilding it and use
  `docs/full79_joint_efficiency_explorer.html` for consultation. The separate
  fixed-effort six-model atlas is under
  `results/full79_information_effort_clouds/` and
  `docs/full79_information_effort_clouds.html`; its core analysis is complete,
  but its current all-source marker remains deliberately withheld because the
  now-completed full-79 LSTM handoff has not yet been ingested. The existing
  `CORE_CLOUDS_COMPLETE_LSTM_PENDING` marker describes the current analysis
  artifact, not the current compute availability.
- **Completed utterance-informativity extension**:
  `results/utterance_informativity_analysis/` contains the child/caretaker
  occurrence tables, recurrent exact-string table, 30 newly fitted models,
  Route 1 and Route 2 model inventories, standardized age estimates, and the
  passing final audit. Its frozen scientific contract is
  `docs/utterance_informativity_route1_route2_protocol.md`; its human report is
  `docs/utterance_informativity_route1_route2_report.html`.
- **Bayesian Route 1 / Route 2 extension, audited pilot STOP**:
  `results/bayesian_route1_route2_20260828/` contains the hash-bound contract,
  full data audits, prior checks, six passing synthetic posterior fits, seven
  representative real-data pilot fits, and the independent
  `PILOT_STOP_AUDITED` marker. The human handoff is
  `docs/bayesian_route1_route2_report.html`. Production is not complete: B5
  passed its sampler-diagnostic gate with zero divergences, but the 189-fit
  program projects to 8,312 CPU-hours against its frozen 2,000-hour ceiling.
  No production posterior was run and the production completion marker is
  deliberately absent. Do not
  report pilot coefficients as scientific results or bypass the gate by
  silently changing the raw-row unit, likelihood, sample roles, or estimand.
- **Focused Bayesian joint adaptive-efficiency extension, complete and
  audited**: `results/bayesian_joint_adaptive_efficiency_20260828/` contains a
  separately frozen, bounded analysis of the project's central joint question.
  It uses 1,122,396 utterances to estimate shared session-clustered
  three-coefficient summaries for 78 children, then fits one trivariate
  hierarchical measurement-error model, one wider-prior sensitivity, and 13
  leave-one-corpus stress tests. The population fixed-effort k3 age slope is
  -0.685 bits per six months (95% CrI [-1.131, -0.239]); the entropy/effort
  slope at 42 months is +0.00584 log(1+words) per entropy SD
  [-0.00018, 0.01196], with 90.4% of the posterior in the declared small-effect
  ROPE; its age interaction is -0.00155 [-0.00389, 0.00085], with 99.9% in the
  ROPE. The hypothesized cross-child correlation is -0.005
  [-0.310, 0.295], unsupported. All 15 fits had zero divergences and zero
  treedepth saturation; the completion marker is
  `FOCUSED_JOINT_ANALYSIS_COMPLETE_AND_AUDITED`. Read
  `docs/bayesian_joint_adaptive_efficiency_report.html`. This extension does
  not complete or override the stopped 189-fit program and is not listener
  utility.
- **Word-level information, PBM 21 only**: the owning repository is
  `/home/apaixonada/EvaPortelance/Projet_1/developmental_word_information`.
  Its three canonical input symlinks are under
  `data/external/compute_surprisal_mila/` and are named
  `mistral_7b_v03_pbm21_word_20260731_e890ec1_v1`,
  `qwen3_14b_pbm21_word_20260803_c82d219_v1`, and
  `tinydialogues_pbm21_word_20260730_e890ec1_v1`. Completed analyses and
  `COMPLETE_AND_AUDITED` markers are under
  `results/modular_analysis/{mistral_pbm21,qwen_pbm21,tinydialogues_pbm21}/`.
- **Separate secondary products**: Hall remains under
  `results/hall_snapshot_analysis/`; corrected cross-fitted PBM Bayes results
  remain under `results/corrected_pbm_bayes_v2/`; and audited PBM complexity
  and legacy n-gram products remain under
  `results/mila_modular_runs_2026_07_08/products/`.
- **Unified cross-population scoring handoff, compute pending**:
  `results/cross_population_scoring_handoff/full_20260826/` and its deterministic
  archive cover 37 datasets, 892 source folders, 877 scoreable children, and
  1,825,624 real child targets across strict naturalistic, training-expansion,
  structured, clinical/control, and Hall designs. The archive SHA-256 is
  `e441d48f14c568b7cabd97aac1389bdfb15d1916ba144afc924adaf24d9baf28`.
  It freezes separate Mistral, TinyDialogues, and Qwen3-14B k0-k3 word-level
  scoring. PBM three-scorer outputs and Hall Mistral are reuse cells; the other
  101 model-by-dataset cells have not yet been scored on Mila. Do not describe
  the handoff as completed model output.
- **Downstream caregiver-response utility, scoring in progress/partly
  stopped**: `results/downstream_caregiver_response_handoff/` freezes 613,741
  immediate next-caregiver targets from the strict-naturalistic 79 children,
  with 413,084 primary caregiver-child-caregiver triads. The protocol is
  `docs/downstream_caregiver_response_efficiency_protocol.md`. A three-scorer
  Mila launch began on 2026-08-28. At the last user-provided status, all three
  preparation/smoke/release gates passed; TinyDialogues and Mistral completed
  their base-context score waves but their first CPU audits failed, while Qwen
  base-context scoring was still running. No downstream score archive is
  analysis-ready yet. Do not join, analyze, or describe results until the
  compute failure is diagnosed and every returned archive passes relocation
  audit locally.

The full100 Qwen/Mistral handoff is complete, not pending. Its extension archive
is 3,305,320,336 bytes with SHA-256
`909e961b980377be6ad39c738d02801896e6ec921661b7947723224157bb1160`.
The final audit passed 16,138,100 extension rows and the disjoint union passed
645,524 contexts with exactly 100 responses per context. Local verification
found 512 files in every core75, extension25, and full100 product family; all
645,524 full100 context means are finite and match exactly the 645,524 context
IDs and 1,122,396 eligible real-child rows in the all-79 table, with zero
per-context multiplicity mismatches.

The all-79 Qwen-response effort summaries, joined analysis tables, conditional
models, and cloud plots have now been produced locally; no further generation,
scoring, or Mila retrieval is needed to reproduce the current Route 2 result.
Exact-string response entropy uses all 100 `target_text` values per context.
Semantic-cluster entropy remains unavailable. The response scoring handoff is
utterance-level only and contains no generated-response word/token/allocation
payload.

Current strict naturalistic big-cleaned bundle:

```text
data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

The separately prepared Hall snapshot is under
`data/preprocessed_data/Hall/`, with compact audits and a real-target scoring
table under `results/hall_snapshot_preprocessing/`. Its 2026-08-10 audit passed
40 source files and 238,249 main tiers. The frozen primary sample contains 36
children and 70,510 scorable child utterances; the 37-child/71,830-row
sensitivity adds one folder-inferred demographic stratum. Three files remain
explicitly excluded: two missing-transcript placeholders and one unrevised-ASR
file with no identified target-child tier. The completed Hall Mistral
same-pass archive is local through the model/run-labelled external symlink. Its
independent relocation audit passed 4/4 k0–k3 contracts: 287,320 utterance
rows, 1,182,476 word rows, 1,769,650 token rows, 1,461,794 allocation rows,
and zero problems. The 455,153,574-byte archive SHA-256 is
`c7c2422f19f87a0096136f73bf3a1fa664f5551ed095371920b3462db6d21202`.
An outcome-blind 54–59-month comparison manifest selects one session nearest
57 months for 20 current Mistral children.

The completed modular Hall analysis is under
`results/hall_snapshot_analysis/`, with its human-facing report at
`docs/hall_snapshot_mistral_analysis.html`. All 20 registered models passed,
five primary model families completed 1,000 stratified child bootstraps, 72
registered contrasts and 9 plots passed the final audit, and
`ANALYSIS_COMPLETE_AND_AUDITED` is present. At fixed cleaned word count and
setting, the primary k0 race-by-class interaction is -3.516 bits (clustered
95% CI [-5.730, -1.302]); it is a scorer-indexed descriptive interaction, not
a causal SES effect. The adult-adjacent k0-minus-k3 context-support interaction
is -0.213 bits with an interval crossing zero. The guarded Hall-minus-current
locked-snapshot k0 contrast is +3.037 bits (95% CI [2.041, 4.032]); treat it as
domain/era/dialect/transcription sensitivity, not a causal cohort effect.

This bundle uses additive random/unigram/bigram/trigram dictionaries with one
first bin `006-023`, followed by 6-month bins:

```text
024-029, 030-035, 036-041, 042-047, 048-053, 054-059, 060-065
```

Strict naturalistic corpora in the current bundle:

- Belfast
- Brown
- Demetras1
- Forrester
- Kuczaj
- Lara
- MPI-EVA-Manchester
- Manchester
- Post
- Providence
- Sachs
- Weist
- Wells

Generated/scoring-ready row counts for this current bundle:

- 79 child folders
- 1,140,218 child scoring rows
- 1,470,154 caretaker scoring rows

The direct-Mistral 79-child production run `20260713_162955` completed and the
extracted scored tree is local. Its 1,896 CSVs cover 79 children x 6 modes x 4
contexts, with exactly 474 files for each of k0, k1, k2, and k3. The scored
child source has 1,140,695 rows after a 477-row Naima patch; the caretaker
source has 1,470,154 rows. Six generated target strings are blank, producing
24 blank baseline score cells across the four contexts. These small gaps must
be patched or explicitly flagged before describing the baseline row matrix as
literally complete. The compact final report and completion marker should
still be preserved beside the local archive even though the sibling repo
records that the final Mila audit passed.

The TinyDialogues PBM production run `20260717_201227` is also local and ready
for analysis. Its relocation-aware audit passed all 504 files: 21 children,
six modes, four contexts, 11,605,772 scored target rows, zero blank targets,
zero truncated-context rows, and zero problems. TinyDialogues uses
`LaurensWink/SmolLM2-135M_variants` revision
`149fd0d6f069ef7b0a915474c86367c7d34c1591` in FP32. Keep TinyDialogues and
Mistral scores in separate model-specific columns and output namespaces; do
not compare raw bits per model token as though their tokenizers were the same.

The Qwen3-14B PBM same-pass word production
`20260803_qwen3_14b_pbm21_batch16_persistent_production_c82d219_v1` is local
and analysis-ready. Its independently rehashed 15,774,773,220-byte archive and
relocation-aware audit passed all 504 contracts: 21 children, six modes, four
contexts, 11,605,772 utterance rows, 35,450,900 word rows, 55,528,922 token
rows, 44,008,510 token-to-word allocation rows, and zero audit problems. The
model/run-labelled symlink lives in `developmental_word_information`, which
owns the word-level analysis; do not duplicate this 15 GB tree here.

The PBM Mistral and TinyDialogues same-pass word archives are also local and
analysis-ready. Their 2026-08-05 relocation-aware audits passed all 504
contracts with 11,605,772 utterance rows, 35,450,900 word rows, and zero
problems. Mistral has 60,843,382 token rows and 49,203,516 allocation rows;
its 11,562,917 canonical utterance comparisons stayed inside the frozen FP16
cross-hardware tolerances, including the documented Naima patch. TinyDialogues
has 55,357,148 token rows and 43,721,905 allocation rows. Both quarantines were
promoted and linked into `developmental_word_information` under immutable
model/run labels.

The legacy Route 1/Route 2 products remain PBM-scoped (Brown, Manchester, and
Providence: 21 children):

```text
results/route1_analysis_dataset/
results/route2_response_space/
results/route2_response_space_analysis/
results/existing_scored_baseline_efficiency_cloud/
```

The 2026-07-21 frozen direct-score replication products are:

```text
results/direct_surprisal_replication/tinydialogues_pbm/
results/direct_surprisal_replication/mistral_full79/
results/direct_surprisal_replication/paired_tiny_mistral_pbm/
docs/direct_surprisal_replication_index.html
docs/direct_surprisal_results_explorer.html
docs/tinydialogues_pbm_direct_surprisal_replication.html
docs/mistral_full79_direct_surprisal_replication.html
docs/paired_tinydialogues_mistral_pbm_report.html
docs/paired_tinydialogues_mistral_child_trajectories.html
docs/tinydialogues_pbm_route1_model_atlas.html
docs/tinydialogues_pbm_visual_summary.html
docs/mistral_full79_visual_summary.html
docs/paired_tinydialogues_mistral_visual_summary.html
docs/tinydialogues_pbm_child_gallery.html
docs/mistral_full79_child_gallery.html
```

These products implement child-fixed, exact/top-coded word-effort models with
child-clustered covariance, child bootstrap, nonlinear and age-bin
sensitivities, leave-one-child/corpus influence, and individual trajectories.
TinyDialogues PBM P1 is negative (`-0.222` bits/month, clustered 95% CI
`[-0.311, -0.132]`). Mistral non-PBM P1 is also negative (`-0.062`), but its
frozen primary clustered interval crosses zero (`[-0.132, 0.007]`), so the
primary confirmation criterion is not met; the child-bootstrap sensitivity
does exclude zero and must be shown alongside, not substituted for, the
primary result. P3 context gain (`k0 - k3`) is negative in Tiny PBM, Mistral
PBM, and Mistral non-PBM, contrary to the frozen positive direction. All 21
Tiny child profiles, 79 pooled Mistral profiles, 58 non-PBM profiles, and 21
paired overlay profiles exist.

The complete TinyDialogues-compatible Route-1 long table contains 11,605,772
rows from all 504 scored files and has zero source-audit problems. Its separate
expanded model atlas fits 41/56 direct model-zoo subvariants and 45/45 explicit
comparison models. The 15 unavailable subvariants are exactly the Z3/Z4/Z10
next-token entropy/certainty families; do not interpret them as model failures
or fill their absent scorer-specific predictors with zeros.

The newer plot-led direct-score workflow is
`src/build_direct_surprisal_modular_analysis.py`, documented in
`docs/direct_surprisal_modular_pipeline.md`. Its `datasets`, `models`, `plots`,
and `report` stages are independent and chained by manifests. The completed
Tiny run has 34 recorded model rows (31 ordinary passes and 3 singular/boundary
mixed sensitivities) and 32 audited figures. The completed Mistral run has 102
model rows (93 ordinary passes, 8 singular/boundary mixed sensitivities, 1
nonconverged mixed sensitivity, and 0 failed primary/direct fits) and 171
audited figures. Treat unweighted design-cell mixed fits as sensitivities, not
as replacements for the frozen exact-cell WLS primary model.

The paired visual workflow is
`src/build_paired_direct_surprisal_visual_analysis.py`. It treats the exact
446,508-row PBM intersection as its immutable dataset stage, then separates
models, plots, and report rendering. Its completed model stage covers 11
real-target, context-gain, and n-gram-gap outcomes with 200 paired child
bootstraps. Supported child-level P1 slope signs agree across scorers for
18/21 children. The extended paired stage also saves P1/P2/P3 quadratic
coefficient bootstraps, age-bin candidate rankings, and candidate-source age
interactions; its plot audit records 7/7 figures present. Raw score magnitudes
remain non-comparable across scorer calibrations.

The recommended human consultation view is
`docs/direct_surprisal_results_explorer.html`, generated by
`src/build_direct_surprisal_results_explorer.py`. It is a static interactive
page over saved artifacts only: 136 filterable model cards, 31 summary plots,
179 scorer/scope child profiles, 30 model-family coverage rows, plain-language
interpretations, exact formulas, key age terms, and retained warnings. Use it
before sending users to linear reports or raw CSV tables.

The frozen sustained-onset follow-up is
`docs/direct_surprisal_onset_confirmation.html`, generated by
`src/build_direct_surprisal_onset_confirmation.py`. It uses 1,000
child-resampling bootstraps and simultaneous max-absolute-studentized bands on
the exact/top-coded word-effort design cells. Neither PBM discovery nor the
58-child non-PBM sample satisfies the sustained-onset rule. The earlier
24–29-month PBM nominal contrast remains exploratory and must not be reported
as a replicated onset.

Important current facts:

- the Hall Mistral same-pass archive is local and passed an independent
  relocation-aware audit with exact archive/input hashes, safe members, 4/4
  contracts, full row identities, and no scoring problems. Its 20-model
  cross-sectional analysis and final report also pass their complete audit;
- the PBM same-pass Mistral, Qwen3-14B, and TinyDialogues word productions are
  local and passed their 504-contract relocation audits, immutable handoff,
  exact-pairing, and no-effect feature gates. Each scorer has the exact same
  1,032,963-row primary occurrence set (SHA-256
  `4b12305ba8ff6ec2fc96557b68aa6b921dd34bb6f0d05023fcf8451a93bcb437`)
  over 1,032 word types; effects must still be fit separately;
- the remaining-58 real-child Mistral same-pass word DAG is implemented and
  locally audited at compute commit `aa6555f`. It targets 232 contracts and
  requires a fresh exact-wrapper smoke before production; no Mila job ran;
- `developmental_word_information` was locally verified at commit
  `12bd91b66d7fdb5155a8e380eabc807aa8017cf1`; it owns the frozen protocol,
  input audits, exact word pairing, registered 27-model engine, bootstrap,
  plots, reports, and final audit. The protocol SHA-256 is
  `705143ea70e4c3852fe852205010973fca7742d927c0a85993a917bf084d5989`;
  cross-scorer effects must be fit separately and raw score magnitudes must not
  be pooled;
- the full-79 direct-Mistral score tree and the audited full-79 additive-LSTM
  target/score handoff are available. Full-79 context entropy, word-level
  surprisal, complexity products, and corrected Bayes scores are not all
  available. The LSTM product still requires analysis-repo ingestion. The
  all-79 Qwen response-space text and utterance-level Mistral k0/k3 products
  are available through the full100 handoff above;
- TinyDialogues covers the 21-child PBM discovery set for real, random,
  unigram, bigram, trigram, and caretaker targets at k0-k3; it does not yet
  cover the other 58 children or the PBM LSTM candidates;
- the Route 1 long table includes real child, random, unigram, bigram,
  trigram, and additive same-length LSTM k3/k4/k5 targets scored by Mistral;
- PBM additive LSTM generation and scoring are complete; they are no longer a
  merely planned baseline;
- the older Mistral-generated response-space products under
  `results/route2_response_space/` remain PBM-only: about 444k child
  utterances and 268,712 contexts. Keep their 176 incomplete/fallback settings
  as audit flags and never relabel this legacy table as all-79;
- the newer all-79 response space is the Qwen-generated/Mistral-scored full100
  handoff verified on 2026-08-24: 64,552,400 scored responses, 645,524
  contexts, 79 children, and 13 corpora. The conditional all-79 effort/cloud
  suite is now complete: 15/15 models passed across pooled, PBM-discovery, and
  non-PBM-confirmation scopes. At 42 months, its pooled absolute-length ratio
  from response-entropy p10 to p90 is 1.028 [1.014, 1.043], whereas the
  Qwen-relative effort odds ratio is 0.931 [0.902, 0.962]. Preserve this
  estimand distinction and the developmental reversal;
- the utterance-informativity extension fitted 24 opportunity-weighted
  child-cell standardization models and six developmental k0/k3-density
  coupling models. The child age-by-k0-density interaction is unsupported in
  PBM discovery (+0.0065 per six months, interval crossing zero) and negative
  in the other-58 confirmation sample (-0.0061, 95% CI [-0.0118, -0.0003]).
  Because discovery and confirmation directions differ, this is not a
  replicated developmental effect. Caregiver coupling is approximately
  unchanged;
- July modular-repo products are under
  `results/mila_modular_runs_2026_07_08/products/`: PBM n-gram Bayes scores and
  PBM complexity predictors have passed their recorded join audits;
- the original Bayes values are unnormalized decomposition scores because `p(c)` has not
  been estimated. They are most defensible for same-context candidate
  comparisons and must not be labeled as normalized posterior surprisal;
- the current Bayes pilot is additionally unsuitable for substantive inference
  because its full-79 training data include the evaluated PBM real utterances
  and context pairs. This creates an in-sample advantage for real targets over
  generated targets;
- the order-3 likelihood in `bayes_efficiency_mila` conditions the first
  context token on only the candidate utterance's last word; after the first
  context token, the candidate utterance is no longer in the trigram history.
  Treat this as an implementation proof of concept, not a rich discourse
  likelihood. Do not use its raw per-child-word scores for developmental
  claims;
- the corrected PBM Bayes-derived product is under
  `results/corrected_pbm_bayes_v2/`. It uses leave-corpus-out cross-fitting,
  additive age-bin training, explicit unknown-token handling, whole-utterance
  contrastive context evidence, and normalization over each row's available
  real/random/unigram/bigram/trigram candidates. Its 2,232,524-row audit passed
  held-out matched-versus-shuffled context validation in Brown, Manchester,
  and Providence;
- corrected `candidate_set_probability` is a probability only over the supplied
  matched candidate set. It is not a posterior over every possible utterance.

Move real data, generated utterances, model checkpoints, and scored outputs
between machines with `rsync` or Globus, never Git.

## Current Reporting State

Current supervisor-facing utterance-information report:

```text
docs/predicting_utterance_level_information_report.md
docs/predicting_utterance_level_information_report.html
```

The current Route 1/Route 2 methods and model handoffs are:

```text
docs/utterance_informativity_route1_route2_protocol.md
docs/utterance_informativity_route1_route2_report.html
docs/full79_joint_efficiency_pipeline.md
docs/full79_joint_efficiency_explorer.html
docs/full79_information_effort_clouds.html
```

The separate Hall cross-sectional report is:

```text
docs/hall_snapshot_mistral_analysis.md
docs/hall_snapshot_mistral_analysis.html
```

The July supervisor-report landing page and formal methods reference are:

```text
docs/july_meeting_index.html
docs/july_meeting_definitions.html
docs/july_meeting_formal_mathematical_definitions.md
```

The definitions page is generated by `src/build_july_meeting_index.py` from
`src/july_formal_definitions.py`. Keep the HTML and copyable Markdown/LaTeX
source synchronized through that builder. When changing a formula, first
verify the corresponding scorer, feature builder, or statistical model rather
than silently regularizing the notation into a different estimand.

Before editing this report, always reread the current Markdown file because the
user may be editing it manually between agent turns. Keep the report
supervisor-facing: avoid implementation paths, repo workflow details, and
internal labels such as "Route 1" in the report body.

The current August supervisor package integrates the direct, three-scorer
word, corrected-Bayes, response-space, sustained-onset, trajectory, and Hall
evidence while preserving the frozen claim IDs and sample roles:

```text
docs/august_supervisor_index.html
docs/august_supervisor_report.md
docs/august_supervisor_report.html
```

Its thin controller is `src/build_august_supervisor_report.py`. It runs the
existing dataset, model-result extraction, synthesis, plot, report, index, and
independent-audit stages without fitting or selecting models. The final local
completion record is the ignored
`results/august_supervisor_report/AUGUST_REPORT_COMPLETE_AND_AUDITED`; it is
valid only when its audit and product hashes bind to the current clean commit.
Verify all status language against those artifacts before editing. Useful
technical evidence also remains distributed across:

```text
docs/new_efforts_report_index.html
docs/developmental_onset_working_report.md
docs/bayes_information_working_report.md
docs/new_efforts_complexity_metrics.md
docs/communicative_efficiency_supervisor_candidate_report_v0.md
docs/corrected_pbm_bayes_report.md
```

The clearest current PBM finding is a negative child-controlled, fixed-effort
Mistral age slope. The onset report estimates the first age-bin decrease by
`024-029`, but its child-age-cell sensitivity changes the sign/weighting and
child-bootstrap intervals are still pending. Keep this caveat visible; do not
promote an exact developmental onset as settled.

The current Route 2 relative-effort result does **not** support the simple
prediction that older children increasingly lengthen responses as sampled
response entropy rises. In the final relative-effort models, the age by
response-entropy interaction is in the opposite direction for the principal
residual/percentile outcomes. Treat this as a result or a measurement
diagnostic to be replicated after semantic-entropy calibration; do not spin it
as confirmation of the original hypothesis.

### August supervisor-report workflow

The staged, copy-ready operator guide is
`docs/august_supervisor_workflow/README.md`; its detailed scientific and stage
contract is beside it. Run prompts in strict numbered order, with exactly one
fresh task per stage and one shared physical worktree. Every handoff must name
the predecessor/resulting SHA, actual tests, manifests, blockers, and a clean
status. Never run the stages concurrently. Plotting and rendering consume
frozen saved artifacts and do not fit models. A failed independent audit goes
through the conditional remediation prompt and then a fresh audit before final
integration.

### Bayesian Route 1 / Route 2 pilot-stop and focused joint extension

The reviewed design proposal is
`docs/bayesian_route1_route2_program_2026-08-28.md`; the copy-ready fresh-chat
implementation prompt is
`docs/prompts/start_bayesian_route1_route2_program_2026-08-28.md`. That broad
program was implemented through an audited real-data pilot and remains stopped
before production because its 189-fit inventory projected to 8,312 CPU-hours.
Its pilot coefficients are not scientific results.

The first implementation lane contains exactly five priority families:

1. a paired hierarchical k0-k3 context-depth Route 1 model;
2. a Route 1 location-scale model for mean and residual predictability;
3. a negative-binomial raw-effort Route 2 response surface;
4. an endpoint-aware Qwen effort-rank model, with beta-binomial primary and
   zero-one-inflated beta sensitivity;
5. a bivariate measurement-error synthesis of child-specific Route 1 and
   Route 2 developmental slopes.

Use the already audited all-79 Mistral and Qwen-response products; Phase 1
requires no new neural scoring or Mila job. Preserve PBM discovery,
non-PBM replication, and all-79 descriptive scopes. Existing outcomes have
already been inspected, so call this a post-hoc Bayesian robustness/extension
program rather than a new prospective confirmation. Bayes factors are not a
primary decision rule. Prior predictive checks, synthetic recovery,
convergence/ESS/divergence audits, posterior predictive checks, prior
sensitivity, age-shape stacking, and leave-one-child/corpus validation are
mandatory.

After returning to the motivating emails and meetings, a separate focused
joint extension was frozen and completed at
`docs/bayesian_joint_adaptive_efficiency_protocol.md`. It treats the existing
nonlinear GAMMs as the primary marginal analyses and adds one compact
trivariate measurement-error synthesis of child-level fixed-effort
predictability, demand-sensitive effort at 42 months, and developmental change
in demand sensitivity. Corpus is a nuisance hierarchy; PBM is a discovery
label and never a prior. The model and report passed their independent audit
in 19.3 wall minutes / 1.285 CPU-hours. Its strongest result is the negative
fixed-effort predictability slope; demand-sensitive effort is modest, the
developmental effort interaction is practically near zero, and the predicted
cross-route child correlation is unsupported. The downstream caregiver-
response utility analysis remains the decisive next test.

## Current Scientific And Compute Focus

Current priorities and genuine compute gaps as of 2026-08-26:

1. Preserve the completed all-79 utterance-effort and joint
   information-effort analyses and their frozen PBM-discovery,
   non-PBM-confirmation, and all-79-descriptive scopes. Do not substitute the
   older PBM response-space table or refit models during plotting/reporting.
2. Keep unconditional surprisal, contextual surprisal, and context support as
   separate utterance-level outcomes. Caregiver input, real child speech, and
   generated candidates are different comparison objects and require explicit
   target-role/candidate labels.
3. Treat word-level information as PBM21-only until a completed remaining-58
   production and relocation audit exist. The current three-scorer word results
   are scorer robustness within the discovery sample, not independent-sample
   confirmation.
4. Treat the completed exact-string response entropy and generated-effort
   summaries as model/prompt/temperature-specific. Semantic-cluster entropy is
   the next measurement extension, not a missing transfer.
5. Preserve the completed onset result (`not_established` in both PBM and
   non-PBM). Do not promote a nominal age-bin contrast as a replicated onset.
6. Use corrected cross-fitted PBM Bayes results only as a
   decomposition/robustness analysis; keep prior, context-evidence, and
   candidate-set components visible.
7. Validate morphology, syllable, phoneme, and other complexity measures before
   promoting them to primary all-79 effort controls. Full-79 complexity and
   corrected-Bayes products are not currently complete.
8. The full-79 same-length additive-LSTM generation and Mistral k0/k3 scoring
   handoff is complete and audited for 1,140,218 rows and all 79 children. It
   is not yet imported into this repository's fixed-effort cloud products.
   Import and rebuild locally; do not repeat the Mila generation/scoring run.
9. Develop listener-relevant utility only with an actual downstream outcome,
   such as caregiver-response predictive gain or validated repair/clarification
   labels. Response predictability alone is not listener utility.
10. Use SES, race/ethnicity, parental education, sex/gender, or nationality
    only with explicit metadata-level provenance. Keep Hall separate from the
    79-child longitudinal analysis.

The legacy in-repo LSTM implementation remains useful for audits and local CPU
smokes, but real new training belongs on Mila. The execution-oriented baseline
repo is now:

```text
/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila
```

For an LSTM task, read these first:

1. `docs/lstm-baseline-pipeline.md`
2. `README.md`
3. `src/generate_baselines_mila/full79_lstm.py`
4. `src/generate_baselines_mila/lstm.py`
5. `src/generate_baselines_mila/cli.py`
6. `slurm/submit_full_79_lstm.sh`
7. `slurm/run_full_79_lstm_cell.sbatch`
8. `tests/test_full79_lstm_production.py`
9. `tests/test_lstm_generation.py`

The LSTM pipeline:

- trains a small word-level encoder-decoder LSTM;
- trains one model per additive age bin, matching the developmental information
  constraints used by the random/unigram/bigram/trigram baselines;
- uses caretaker context k3 and same-length generation for the selected full-79
  production comparison;
- keeps all eight additive age-bin checkpoints; reducing below eight would
  introduce future-age information or break the matched developmental design;
- selects k3 only, rather than repeating k3/k4/k5, because the PBM results show
  nearly identical aggregate LSTM behavior across context windows and k3 is the
  simplest primary-context comparison;
- decodes child-like utterance baselines;
- supports free-length generation generically, but it is not part of the
  selected full-79 production run because it changes the effort estimand;
- writes generated LSTM sibling files and compact scoring-ready files;
- gates production through CPU preparation, an exact-wrapper GPU smoke, staged
  array waves, output audits, and a final `COMPLETE_AND_AUDITED` marker;
- does not compute LLM surprisal.

Do not claim that a new LSTM was trained unless a real training command was run
and its checkpoints, vocabulary, manifest, and audits exist. Do not rerun the
completed PBM proof-of-concept merely because older documentation calls it
"planned." The full-79 k3 workflow subsequently completed generation and
Mistral k0/k3 scoring; its immutable local compute handoff is named above.
Only its import into the analysis repository remains pending.

For the PBM-held-out small-transformer baseline task, use the existing clean
worktree and branch:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/.worktrees/generate-pbm-transformers
branch: codex/pbm-transformer-generators
commit: a455000568f70506d4501d62f32c7c3a24e6fd53
```

Read `docs/pbm-transformer-pipeline.md` and
`configs/pbm_transformers_from_scratch_v1.json` there before acting. The
frozen design is two from-scratch, approximately 58M-parameter models over
eight cumulative age cutoffs: a BabyLlama-sized decoder-only LLaMA and an
encoder-decoder T5, for 16 final models total. Call the first architecture
"BabyLlama-sized LLaMA trained from scratch," not a BabyLlama replication:
the published BabyLlama used teacher distillation and this experiment does
not. Brown, Manchester, and Providence are held out from tokenizer training,
training, validation, and epoch selection.

The audited upstream input is
`results/transformer_training_expansion/full_20260825/`: 763,494 training,
175,216 whole-child-disjoint validation, 938,710 development, and 446,508 PBM
evaluation examples. The generation/scoring split is strict:

- `generate_baselines_mila` trains, selects/refits, and generates one
  unconstrained-length response per PBM target;
- the 128-subword-token ceiling is a safety bound whose censoring rate must be
  at most 0.1%, not an analytical length constraint;
- the exact two-architecture GPU smoke must pass before production can run;
- `2 x 8 = 16` is the final model count; do not create PBM cross-validation
  folds or 24 models;
- Mistral `k0`/`k3` scoring belongs in `compute_surprisal_mila` and starts only
  after the generated handoff is complete, retrieved, and audited.

The transformer implementation and smoke-gated Slurm DAG are complete and
pushed, but no transformer Mila training job has been submitted as of
2026-08-26. The next execution step is handoff/runtime transfer and the exact
two-architecture GPU smoke, followed by the dependency-gated 16-model run only
after the smoke audit passes.

## Repository Map

```text
communicative_efficiency/
|-- AGENTS.md
|-- TODO.md
|-- configs/
|   |-- lstm_baseline_16gb_default.json
|   |-- lstm_baseline_16gb_pbm_additive.json
|   `-- response_entropy_pilot_grid.json
|-- data/                  # ignored by Git; transfer with rsync/Globus
|-- docs/
|   |-- design.md
|   |-- notes.md
|   |-- predicting_utterance_level_information_report.md
|   |-- developmental_onset_working_report.md
|   `-- bayes_information_working_report.md
|-- figs/                  # ignored by Git unless explicitly needed elsewhere
|-- results/               # ignored by Git; generated outputs and bundles
|-- src/
|-- tests/
|-- scripts/
`-- notebooks/
```

## Important Source Files

- `src/prepare_datasets.py`: Stage 0 CHAT / CHILDES preprocessing.
- `src/create_big_cleaned_dataset.py`: consolidated strict-naturalistic bundle
  creation.
- `src/build_age_word_dicts.py`: additive age-binned vocabulary and count
  dictionaries.
- `src/add_random_and_unigram_utterances.py`: matched-length random, unigram,
  bigram, and trigram baseline utterance generation.
- `src/create_shared_caretaker_contexts.py`: role-specific caretaker context
  windows, currently `context_k1`, `context_k2`, `context_k3`.
- `src/create_minimal_surprisal_scoring_csvs.py`: compact child/caretaker
  scoring-ready CSVs.
- `src/create_pbm_early_baseline_rescoring_bundle.py`: PBM-only `006-023`
  generated-baseline handoff bundle for Mila rescoring.
- `src/audit_hall_scored_archive.py`: relocation-aware integrity, product, and
  cross-context audit for the returned Hall Mistral archive.
- `src/build_hall_snapshot_analysis.py`: modular Hall dataset, model,
  bootstrap, influence, plot, report, and final-audit workflow.
- `src/generate_lstm_utterances.py`: word-level LSTM model code.
- `src/run_lstm_baseline_pipeline.py`: config-driven LSTM orchestration.
- `src/build_route1_analysis_dataset.py`: audited PBM scored/effort long table.
- `src/build_route1_model_report_suite.py`: core Route 1 model/report suite.
- `src/build_route2_response_space_table.py`: joins real child rows to response
  entropy and generated-response effort summaries.
- `src/build_response_space_analysis_suite.py`: Route 1/Route 2 response-space
  estimator suite.
- `src/build_route2_relative_effort_model_suite.py`: child effort relative to
  the generated response-space models.
- `src/build_existing_scored_baseline_efficiency_cloud.py`: common-Mistral
  real/n-gram/LSTM information-effort cloud.
- `src/build_developmental_onset_report.py`: current onset and change-point
  working analyses.
- `src/build_bayes_information_report.py`: joins and audits Bayes, complexity,
  and direct Mistral products.
- `src/build_corrected_pbm_bayes_report.py`: corrected cross-fitted PBM
  candidate-set Bayes results, held-out validation, child bootstrap, and direct
  Mistral comparison.
- `src/plot_distributions.py`: distribution plots and summaries.

Sibling execution repositories:

- `compute_surprisal_mila`: direct Mistral scoring, Slurm, and scoring audits;
- `generate_baselines_mila`: manifest-driven n-gram and LSTM generation;
- `bayes_efficiency_mila`: n-gram and future neural Bayes components;
- `child_complexity_predictors`: complexity and lexical trajectories.

## Data And Git Policy

Large data and generated outputs should not be pushed to Git.

Ignored by `.gitignore`:

- `data/`
- `results/`
- `figs/`
- generated PDFs/images under docs
- archives and tarballs
- model checkpoints
- local environments and caches

Use `rsync` or Globus for machine-to-machine data transfer. Use Git for:

- source code
- tests
- configs
- Markdown documentation
- lightweight project metadata

Important: if bulky files were already tracked before `.gitignore` was updated,
they must be removed from the Git index with `git rm --cached`; do not delete
local data unless explicitly asked.

## How Agents Should Work Here

Before editing code:

1. Read this file.
2. Read `TODO.md`.
3. Read relevant docs under `docs/`.
4. Inspect directly involved source files and tests.

Default behavior:

- Make small, reviewable changes.
- Preserve raw data.
- Preserve row provenance wherever possible.
- Add or update tests for behavior changes.
- Prefer simple, explicit code over clever abstractions.
- Keep documentation synchronized when changing file formats or assumptions.
- After meaningful work, update `TODO.md` and `docs/notes.md` with dates,
  commands, outputs, and verification.
- Do not simplify scientific designs for convenience. If the requested analysis
  requires matched developmental information constraints, additive age bins,
  separate train/generate scopes, or other statistically important structure,
  implement that structure with tests or explicitly stop and explain the
  scientific tradeoff before coding.
- Treat this as senior-engineer research software for a PhD project: exhaustive
  tests, transparent provenance, and methods-level documentation are part of the
  deliverable, not optional polish.

## Testing

Current full unit-test command:

```bash
.venv/bin/python -m unittest discover -s tests
```

If `uv` is available, this also works:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

Do not copy an old test count into new notes. Record the command, date, pass
count, and any expected warnings from the test run actually performed.

Latest full-suite verification on 2026-08-17 after the completed Hall scoring,
relocation audit, modeling, plots, and report integration: 417 tests passed in
300.310 seconds with
`CUDA_VISIBLE_DEVICES=''`. The run emitted expected
Statsmodels convergence, perfect-separation, singular-fit, plotting, and
small-fixture numerical warnings but no test failures. Treat model-fit warnings
in production analyses as audit items even when unit tests allow them.

## Project-Specific Constraints

- Do not overwrite raw CHILDES / CHAT data.
- Do not silently drop utterance rows without recording why.
- Do not invent scientific results or pretend a model was run.
- Do not conflate the completed 79-child direct-Mistral score tree with a
  completed full-79 analysis or a complete full-79 predictor set. Preserve the
  final scoring marker/report locally and keep every partial predictor family
  labeled by its actual sample coverage.
- Do not generalize PBM (21-child, 3-corpus) analyses to the full 79-child,
  13-corpus bundle without a new scored analysis.
- Do not pool the PBM discovery sample into the remaining corpora and call the
  resulting estimate confirmatory; report the non-PBM replication separately.
- Do not call lower target surprisal "more information" without explicitly
  defining the direction and construct. Prefer predictability,
  conventionality, or contextual support where those are the actual measures.
- Do not describe response-space samples as same-meaning paraphrases.
- Do not use random, n-gram, or same-length LSTM baselines to test effort:
  their length is fixed to the observed child utterance by construction. Use
  the free-length Qwen response distribution for generated-relative effort.
- Do not describe Mistral response entropy as model-independent behavioral
  uncertainty.
- Do not conflate raw child-effort models with generated-relative effort
  models, or silently treat generated expected effort as a standard confound.
- Do not call the full100 Qwen/Mistral handoff word-level. It contains
  utterance-level k0/k3 scores and response texts only. For per-response cloud
  analyses, combine the disjoint `processed/core75/` and
  `processed/extension25/` tables; for context-level expected information, use
  `context_means/full100/`.
- Do not describe the legacy Bayes score as normalized `p(u | c)`.
- Do not promote the legacy Bayes pilot as evidence that real child utterances
  outperform generated alternatives until candidate scoring is cross-fitted
  and the likelihood passes held-out matched-vs-shuffled context validation.
- When using the corrected v2 score, call it a **Bayes-derived candidate-set
  probability/surprisal**. Always state the candidate set and keep the prior,
  context-evidence, and combined contributions separately visible.
- Do not promote an exact developmental onset from a data-selected breakpoint
  or row-level interval without child-level uncertainty and held-out
  replication.
- Do not use information/effort ratios as the sole primary efficiency outcome;
  denominator coupling can create artifacts. Prefer conditional models or a
  validated same-meaning frontier analysis.
- Do not treat caregiver speech addressed to children as an adult endpoint;
  it primarily measures caregiver input adaptation unless an adult-adult
  benchmark is added.
- Do not treat context tokens as target tokens when computing target surprisal.
- Do not treat empty or punctuation-only utterances as normal scored utterances.
- Do not change output schemas without documenting the change.
- Do not run GPU LSTM training on the laptop.
- Do not replace additive age-bin baselines with global training unless the user
  explicitly asks for an exploratory/global baseline. The fair LSTM baseline is
  additive by age bin: train on the current bin plus all previous bins, generate
  only for rows in the target bin.
- Match the LSTM training corpus to the comparison target. If comparing against
  PBM-trained n-gram baselines, use the PBM-only additive config; if comparing
  against full strict-naturalistic n-grams, use the all-corpus additive config.

## Data Handling Rules

This is a data-heavy research project. Do not load or print entire datasets into
the chat/context.

When inspecting data:

- Prefer `head`, `tail`, `wc -l`, `du -h`, and column/schema summaries.
- For CSV files, inspect shape, columns, dtypes, missing-value counts, and at
  most 20 example rows.
- Never run `cat` on large CSV/JSON/JSONL files.
- Never paste full datasets into Markdown files.
- Do not commit raw data unless explicitly instructed.
- Treat `data/raw_data/` as immutable.
