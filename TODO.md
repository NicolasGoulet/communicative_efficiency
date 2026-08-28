# TODO.md

Lower-level working checklist for this repository.

Use this file for concrete tasks. Keep `AGENTS.md` high-level and stable.
When a task is completed, move any useful result or decision into
`docs/notes.md`.

## How To Use This File

- Keep tasks small enough to review in one diff.
- Use checkboxes for work items.
- Put open questions near the task they block.
- Add commands that verify the task.
- Link to files when the task concerns a specific script or output.

## Current Focus — Reconciled 2026-08-28

This section is the authoritative active checklist. The longer dated sections
below are retained as implementation/audit history; some of their unchecked
items were superseded or completed by the later modular direct-score workflow.

### Focused Bayesian joint adaptive-efficiency extension — completed 2026-08-28

- [x] Return the Bayesian work to the project's scientific center: contextual
      demand predicting speaker effort, fixed-effort form predictability, and
      their coordinated development. Treat corpus as background hierarchical
      structure rather than the research question; do not use PBM estimates as
      Bayesian priors.
- [x] Freeze the compact H1-H4 protocol at
      `docs/bayesian_joint_adaptive_efficiency_protocol.md`, with one
      trivariate child-level measurement-error model, one wider-prior
      sensitivity, and 13 leave-one-corpus stress tests.
- [x] Derive three coefficients and their shared 3 x 3 session-clustered
      covariance for 78 eligible children from all 1,122,396 joined
      utterances. Exclude only Weist/Emily under the outcome-blind five-session
      identifiability rule.
- [x] Pass synthetic recovery, both full posterior fits, all 13 influence
      refits, posterior predictive checks, prior sensitivity, staged report
      generation, and the independent completion audit. Total measured fitting
      cost was 19.3 wall minutes / 1.285 CPU-hours, with zero divergences and
      zero treedepth saturation.
- [x] Publish `docs/bayesian_joint_adaptive_efficiency_report.{md,html}` and
      preserve the interpretation boundary: the result concerns scorer
      predictability and word effort, not listener utility or an optimum.
- [ ] When the downstream caregiver-response score archives pass relocation
      audit, apply the frozen utility protocol. This is the decisive next test
      for a strong communicative-efficiency claim; do not substitute more
      corpus expansion for it.

### Bayesian Route 1 / Route 2 extension — pilot stopped 2026-08-28

- [x] Review Levshina's Bayesian-statistics-in-linguistics paper and translate
      only its methodologically relevant ideas into analyses supported by the
      existing all-79 Route 1 and Route 2 products.
- [x] Rank a broader 12-analysis candidate inventory and select exactly five
      Phase-1 families: paired k0-k3 context depth, Route 1 location-scale,
      raw-effort negative binomial, endpoint-aware Qwen effort rank, and joint
      child-level information-effort slopes.
- [x] Write the scientific design at
      `docs/bayesian_route1_route2_program_2026-08-28.md` and the complete
      fresh-chat implementation prompt at
      `docs/prompts/start_bayesian_route1_route2_program_2026-08-28.md`.
- [x] In dedicated branch `agent/bayesian-route1-route2-v1` from starting SHA
      `f52a7f102dd87a6a566ef72bbf24519efda16202`, freeze
      source hashes, row identities, formulas, priors, effect-scale ROPEs,
      posterior queries, and PBM/non-PBM/all-79 scopes before production fits.
- [x] Audit and pin repository-local brms 2.23.0, cmdstanr 0.9.0, and CmdStan
      2.39.0; run synthetic
      compile/recovery tests, prior predictive checks, and a representative
      real-data runtime/memory pilot before fitting any full model.
- [x] Implement the staged `contract -> datasets -> priors -> synthetic-smoke
      -> real-pilot -> models -> diagnostics -> synthesis -> plots -> report
      -> audit` workflow with independent hash-bound manifests. The downstream
      stages deterministically record the pilot STOP and cannot refit.
- [x] Enforce the real-data pilot gate. Seven representative fits completed;
      all passed the sampler-diagnostic thresholds with zero divergences, but
      the 189-fit suite projected to 8,312 CPU-hours against the frozen
      2,000-hour ceiling. Production was correctly blocked, with no automatic
      aggregation, estimand change, or Mila launch.
- [x] Do not launch the 189-fit production grid. After scientific review, keep
      its audited STOP as resource-planning history and use the separately
      frozen focused joint adaptive-efficiency extension above.
- [x] Publish the compact pilot handoff at
      `docs/bayesian_route1_route2_report.{md,html}` and pass the independent
      `PILOT_STOP_AUDITED` audit. The production completion marker remains
      deliberately absent.
- [x] Publish the separately scoped focused scientific posterior report and
      independent completion audit. Do not relabel it as completion of the
      original 189-fit inventory or as prospective confirmation.

### Unified clinical/non-clinical scoring expansion — 2026-08-26

- [x] Audit all identified installed naturalistic, structured, clinical/control,
      expansion, and Hall sources; rebuild the 15-group clinical preprocessing
      output and pass its focused tests.
- [x] Freeze the 37-dataset, 877-scoreable-child, 1,825,624-target real-child
      k0–k3 handoff for Mistral, TinyDialogues, and Qwen3-14B. Preserve design,
      population, clinical/control, and Hall strata explicitly.
- [x] Reuse the audited PBM three-scorer word products and Hall Mistral product;
      mark the remaining 101 model-by-dataset cells as pending rather than
      duplicating completed scoring.
- [x] Implement the compute-repository CPU preflight, exact-wrapper four-context
      GPU smoke, all-or-none 14-run release gate, audited k0/k3/k1/k2 waves,
      resumable output contracts, final archives, and one-OTP operator runbook.
- [ ] Transfer the frozen archive to Mila, review all 14 GPU smoke reports,
      explicitly release production, retrieve the audited archives, and import
      them here. No Mila work has been submitted yet.

### August supervisor report workflow — 2026-08-17

- [x] Define the staged reporting architecture, scientific guardrails, shared-
      worktree safety contract, and small operator guide under
      `docs/august_supervisor_workflow/`.
- [x] Prepare copy-ready, test-contracted prompts for bootstrap, evidence
      freeze, contracts, result extraction, synthesis, plots, report, landing
      page, independent red team, conditional remediation, and final
      integration.
- [x] Run prompt 00 only after this documentation is reviewed and merged to a
      clean `main`; then run one fresh task at a time in strict order.
- [x] Complete prompts 01–07 on `agent/august-supervisor-report-v1`, requiring
      `STAGE_PASS`, the exact predecessor SHA, tests, manifests, and a clean
      worktree at every handoff.
- [x] Run prompt 08 independently. Its first audit findings were remediated
      through prompt 09, then a fresh prompt 08 at `40d65a5` returned
      `AUDIT_PASS` with zero findings.
      If a later audit returns `AUDIT_FAIL`, run prompt 09
      only on its explicit remediation allowlist and repeat prompt 08 in a
      fresh task until it returns `AUDIT_PASS`.
- [x] Run prompt 10, the full repository suite, deterministic rebuild checks,
      and the final integrated audit before creating
      `AUGUST_REPORT_COMPLETE_AND_AUDITED` or publishing the package. The
      controller tests passed 9/9, all August tests passed 69/69, and the full
      suite passed 486/486; the final ignored marker carries the clean-commit
      audit and product hashes.

### All-79 joint information-effort clouds — 2026-08-24

- [x] Build and run the independently resumable `datasets`, `metrics`,
      `models`, `plots`, `report`, and `audit` stages from the canonical
      Qwen100/Mistral full100 handoff and the all-79 direct-score table.
- [x] Audit 645,524 contexts, exactly 100 Qwen responses per context,
      64,552,400 finite scored responses, the disjoint 75+25 union, all
      observed/context joins, source counts, frozen output hashes, and the
      pooled 79-child/13-corpus scope.
- [x] Replace the rejected pooled-scatter and same-context-gallery designs with
      the requested exact model-by-length-by-age analysis. The raw plotting
      grid contains exactly one mean-information value for every one of six
      models, 12 exact lengths, and eight age bins: `6 x 12 x 8 = 576` cells.
- [x] Reproduce the earlier fixed-effort visual grammar: age on the x-axis,
      information on the y-axis, exact lengths as separate labelled lines, and
      length panels grouped as 1--4, 5--8, and 9--12 words. Show raw age-bin
      means together with child-controlled regression predictions and 95%
      intervals for every model.
- [x] Publish the complete 576-cell 3D model-by-length-by-age view, linear and
      quadratic regression diagnostics, fixed-length coefficient comparisons,
      length distributions, and the Markdown/HTML report. All 31 registered
      weighted child-fixed-effect/child-clustered fits passed.
- [x] Retrieve and independently verify the canonical all-79 additive
      same-length LSTM handoff. Generation and Mistral `k0`/`k3` scoring are
      complete for 1,140,218 rows and 79 children; the compute handoff has
      `COMPLETE_AND_AUDITED` and score-table SHA-256
      `03af2bc6abbca362eb9c7529b921e84048d65f68f6c950b841384e187271345e`.
- [ ] Link that immutable handoff into `results/external/compute_surprisal_mila/`,
      satisfy the frozen LSTM ingestion schema, rebuild the fixed-effort cloud
      stages, and replace `CORE_CLOUDS_COMPLETE_LSTM_PENDING` only after the
      new all-source audit passes. No Mila regeneration or rescoring is needed.

### PBM-held-out BabyLlama-sized LLaMA and T5 baselines — 2026-08-26

- [x] Build and push the from-scratch two-architecture implementation on
      `generate_baselines_mila` branch `codex/pbm-transformer-generators` at
      `a455000568f70506d4501d62f32c7c3a24e6fd53`, including the shared tokenizer,
      selection/refit policy, generation audit, exact-wrapper smoke, and
      dependency-gated Slurm DAG.
- [x] Build and audit the PBM-excluded input handoff at
      `results/transformer_training_expansion/full_20260825/`: 763,494 train,
      175,216 whole-child-disjoint validation, 938,710 development, and
      446,508 PBM evaluation examples, with zero PBM overlap in learning data.
- [ ] Transfer the immutable input handoff and the frozen runtime to Mila,
      rehash the inputs there, and run the exact production-wrapper GPU smoke
      for both architectures. Do not treat login-node imports as a GPU smoke.
- [ ] After and only after the two-architecture smoke audit passes, run the
      dependency-gated `2 architectures x 8 cumulative cutoffs = 16` final
      model DAG. Preserve the selected-epoch fresh refit on development data
      and the 0.1% generation-censoring gate.
- [ ] Retrieve and independently audit the scorer-ready generated-response
      handoff. Then, as a separate project, smoke and run Mistral `k0`/`k3`
      scoring in `compute_surprisal_mila`; do not conflate generation completion
      with scoring completion.

### Full-79 conditional joint efficiency explorer — 2026-08-25

- [x] Implement the staged `datasets -> metrics -> models -> plots -> report ->
      audit` workflow specified in
      `docs/full79_joint_efficiency_analysis_design.md`. Every stage must bind
      its saved inputs and outputs by schema and hash; plotting/reporting must
      never refit models.
- [x] Fit the registered nonlinear repeated-measures suite: negative-binomial
      GAMMs for raw and generated-relative effort, robust GAMMs for information
      at adaptive effort and exact-length Qwen gaps, a beta GAMM for effort
      calibration, and a secondary binomial nondominance diagnostic. Control
      child identity and developmental heterogeneity explicitly.
- [x] Produce the registered visualization families, including the
      age-by-response-entropy demand surface, length calibration, paper-style
      exact-length atlas, joint cloud phase portrait, full distributions,
      child heterogeneity, context examples, diagnostics, and the separate
      corrected-Bayes decomposition sidecar.
- [x] Publish a polished browser-based explorer under
      `docs/full79_joint_efficiency_explorer.html`, with a Markdown evidence
      source, clear navigation, model cards, formulas, interpretation limits,
      and links to frozen tables and manifests.
- [x] Run focused tests, production audits, visual inspection, report link
      checks, and the repository-wide suite before writing
      `FULL79_JOINT_EFFICIENCY_COMPLETE_AND_AUDITED`.

### Utterance-level informativity extension — 2026-08-25

- [x] Freeze an utterance-primary informativity protocol that keeps k0
      unconditional surprisal, k3 contextual surprisal, and k0-minus-k3
      context support separate. Preserve PBM discovery, other-58 confirmation,
      and all-79 descriptive scopes.
- [x] Build child and caregiver occurrence tables, opportunity-weighted
      child-age-effort cells, and a separately gated recurrent exact-string
      type table without substituting a word-level analysis for the utterance
      estimand.
- [x] Fit 24 effort-standardization models and six age-by-unconditional-density
      coupling models with child-clustered covariance. Retain all 78 applicable
      frozen Route 1 model records and 14 applicable Route 2/joint records as
      inventories rather than silently refitting them.
- [x] Publish the protocol and Markdown/HTML report, pass the independent
      artifact audit, and write
      `UTTERANCE_INFORMATIVITY_COMPLETE_AND_AUDITED`.
- [ ] Treat the existing PBM21 three-scorer word-level work as a secondary
      lexical extension. Do not call it independent-sample confirmation until
      the remaining-58 word-scoring production is complete and audited.

### Complete local modeling and scientific synthesis — 2026-08-06

- [x] Run every locally eligible component of the complete analysis machine.
      Prepare/fit/plot/report stages recorded zero failures; the only blocked
      component is the deliberately separate remaining-58 Mistral word
      confirmation, whose 232 Mila scoring contracts do not yet exist.
- [x] Fit and audit the frozen PBM word protocol separately under Mistral,
      Qwen3-14B, and TinyDialogues. Each scorer completed 55 fitted variants
      with zero failures and the registered 1,000-child-bootstrap models.
- [x] Replace the crude all-coefficient cross-scorer direction count with an
      eight-question synthesis that reports clustered and bootstrap support
      separately. Same-word k0/k3 age slopes and longer-word contextual
      support are robust across all three scorers; context-gain development
      and rarity-by-age are scorer-dependent.
- [x] Publish `docs/current_scientific_synthesis.html` from audited saved
      outputs. It inventories 607 fitted variants/outcome fits, separates PBM
      discovery from non-PBM confirmation, preserves the contrary Route 2 and
      P3 results, and records that sustained onset is not established.
- [x] Complete the Qwen-response/Mistral-scoring production and audit, retrieve
      the immutable full100 handoff, and use it for the pooled all-79
      information-effort cloud analysis. The verified handoff contains
      645,524 contexts and 64,552,400 scored responses.

### Hall cross-sectional snapshot — 2026-08-10 to 2026-08-17

- [x] Implement and test a Hall-specific preprocessor that preserves all
      speaker tiers, situation boundaries, broad speaker roles, demographic
      provenance, and explicit transcript exclusions.
- [x] Preprocess all 40 local Hall files. The audit passed with 238,249 main
      tiers, 36 primary children/70,510 child targets, and a 37-child/71,830-
      target sensitivity that adds one folder-inferred stratum.
- [x] Freeze an outcome-blind current-corpus comparator: one Mistral session
      per eligible child nearest the Hall primary median age of 57 months in
      the 54–59 month window. The manifest contains 20 children (18 non-PBM,
      2 PBM) and does not inspect outcomes for selection.
- [x] Run the full repository suite after complete Hall scoring and analysis
      integration with `CUDA_VISIBLE_DEVICES='' MPLCONFIGDIR=/tmp/mpl-cache`;
      all 417 tests passed in 300.310 seconds with expected small-fixture statistical
      warnings and no failures.
- [x] Build the deterministic Mila handoff archive and verify its sidecar
      checksum. The 2,520,424-byte archive contains four k0–k3 contracts over
      71,830 inputs (287,320 expected scores), with SHA-256
      `23ca951da9912ea3d46235821cd877c972e7397acd64054ae5dff7d6125544a0`.
- [x] Write the test-driven compute-repository implementation prompt at
      `docs/compute_surprisal_mila_hall_prompt_2026-08-10.md`, including CPU
      preparation, exact-wrapper GPU smoke, resource validation, staged waves,
      audited resume, and final retrieval contracts.
- [x] Add a smoke-gated Hall Mistral scoring contract for the 71,830 real child
      targets at k0–k3, using previous adult-interlocutor turns within the same
      situation for contextual scores. The returned archive passed its local
      relocation audit across 287,320 utterance rows and all word/token products.
- [x] Fit the frozen Hall snapshot models only after scoring: within-Hall
      race-by-class descriptive contrasts at fixed exact word effort and
      setting, then guarded age-matched external comparisons. Treat historical
      strata and scorer/dialect effects as descriptive, not causal or deficit
      measures. All 20 models, 21,000 bootstrap contrast draws, 547 influence
      fits, 9 plots, and the final artifact audit passed.

### Reviewed local closeout — 2026-08-05

- [x] Review and retain the sustained-onset implementation, tests, and report.
      Its saved audit is `PASS`, reproduces the frozen point estimates within
      `2.007e-13`, completes 1,000/1,000 child bootstraps per scope, and finds
      no sustained onset in either PBM or non-PBM under simultaneous bands.
- [x] Review and retain the conversational-eligibility builder, test, and
      completed full-79 structural output. The 2026-07-23 run aligned all
      1,140,218 source rows with zero unresolved files or text mismatches and
      selected 629,334 structurally eligible child turns.
- [ ] Resolve or adjudicate the 18,172 eligible `context_k1` mismatches that
      keep the conversational audit at `REVIEW`, and complete the 325-row
      stratified manual validation sample before treating structural
      eligibility as a validated conversational analysis sample.
- [x] Reauthenticate the GitHub CLI and publish the reviewed closeout plus the
      complete analysis controller. Draft PR #2 is open from
      `agent/project-status-closeout`.
- [x] Historical closeout: the July command sheet intentionally stopped before
      full-79 LSTM scoring. That limitation was superseded by the later audited
      generation and Mistral-scoring workflows, whose immutable local handoff
      is now complete. Do not reuse the July stop point as current status.

### New word-information program — 2026-08-05

- [x] Freeze the high-level paper design: PBM21 Mistral primary plus separate
      Qwen/TinyDialogues scorer robustness; the other 58 children are a
      Mistral-only confirmation sample. Keep PBM and non-PBM estimates separate.
- [x] Implement the first analysis stages in `developmental_word_information`:
      compact archive provenance/coverage audit and exact disk-backed k0/k3
      pairing on `word_occurrence_id`, with atomic PASS markers and tests.
- [x] Implement the complete modular word pipeline: all-child k1/k2/k3 exact
      pairing, versioned no-effect features, registered exhaustive fits,
      1,000-draw child bootstrap, influence checks, audited plots/reports, and
      cross-scorer synthesis.
- [x] Implement the project-level complete analysis controller over direct,
      Route 1, Route 2, Bayes, onset, and word families with hash-verified
      resume and upstream-failure gates.
- [x] Review, validate, and locally commit the compute DAG for exactly 58
      non-PBM children × real speech × k0-k3 = 232 same-pass word contracts.
      Commit `aa6555f` passed 68 focused tests, shell syntax, fake-DAG checks,
      and resolved Mistral GPU resource validation. No Mila job was submitted.
- [x] Retrieve the completed PBM Mistral and TinyDialogues same-pass archives
      using `developmental_word_information/docs/mila_retrieval_commands_2026-08-05.md`,
      then checksum, extract, and run the 504-contract relocation-aware audit.
      Both full audits passed with zero problems; both handoffs and all three
      scorer-identical no-effect feature builds are active.
- [x] Finish the Qwen local relocation-aware audit and create the immutable
      model/run-labelled analysis symlink only after
      `LOCAL_RETRIEVAL_AUDIT_PASSED`. The 504-contract audit and an exact
      Brown/Adam k0/k3 pairing smoke passed with zero pairing problems.
- [x] Freeze and checksum all coverage-based lexical eligibility, cost,
      cross-fitted rarity, support, nonlinear-age, model, bootstrap, and
      multiplicity decisions before inspecting PBM word effects or any
      non-PBM confirmation coefficient. Protocol SHA-256:
      `705143ea70e4c3852fe852205010973fca7742d927c0a85993a917bf084d5989`.
- [x] Reauthenticate GitHub and publish the new local commits. The word repo is
      private at `NicolasGoulet/developmental_word_information`; the compute
      lane is draft PR #17 and the brain controller is draft PR #2. Do not
      submit the remaining-58 Mila smoke until PR #17 is merged and pulled on
      Mila.

### Completed milestone

- [x] Complete and audit the full 79-child direct-Mistral score tree: 1,896
      files covering 79 children, six target modes, and k0-k3.
- [x] Freeze the PBM-discovery/non-PBM-confirmation protocol before fitting the
      58-child confirmation estimates.
- [x] Build TinyDialogues PBM, Mistral PBM/non-PBM/all-79, and exact paired
      scorer analyses with child-level uncertainty, influence checks,
      candidate comparisons, and individual trajectories.
- [x] Publish the static interactive direct-score explorer over 136 model
      records, 31 summary plots, and 179 child profiles.
- [x] Complete the corrected cross-fitted PBM Bayes-derived candidate-set
      analysis and its held-out matched-versus-shuffled context validation.
- [x] Complete the PBM additive LSTM scoring, Route 2 response-space/relative
      effort analyses, and the first audited complexity-product joins.

### Immediate preservation and reporting

- [x] Freeze the two local scored-archive checksums plus compact analysis-audit
      hashes in `docs/direct_surprisal_artifact_freeze_2026-07-22.md`. The
      Mistral archive SHA-256 is now recorded even though its compact remote
      report/marker is not yet local.
- [ ] Retrieve the compact full-79 final report and `COMPLETE_AND_AUDITED`
      marker beside the local Mistral archive. Use the exact laptop commands in
      `docs/mila_handoff_commands_2026-07-22.md`; recover the exact Mistral
      model/tokenizer and scoring-code revisions from that report if present.
- [x] Reconcile `docs/predicting_utterance_level_information_report.md` and its
      HTML with the July direct-score replication, corrected Bayes result,
      completed PBM LSTM work, Route 2 contrary-direction result, and current
      interpretation limits.
- [x] Audit the reconciled supervisor report's six promoted figures and five
      consultation links; render both ordinary and embedded HTML and run the
      focused report/direct-score tests.
- [ ] Audit all other promoted Markdown/HTML pages for missing images, stale scope or
      scorer language, raw-tokenizer scale comparisons, and unsupported claims
      about information, efficiency, onset, or confirmation.
- [x] Keep source/tests/lightweight reports in Git, keep large data/results out
      of Git, and publish the reviewed 2026-07-21/22 implementation changes on
      `agent/project-status-closeout` with a draft pull request.

### Primary scientific work still open

- [ ] Finish manual validation of the completed structural responsive-turn
      sample and adjudicate its `context_k1` mismatches. Preserve
      adjacency/turn-distance, child-initiated, imitation, routine/reading,
      backchannel, question-type, and repair flags.
- [x] Complete lexical-word sustained-onset inference with child
      bootstrap/simultaneous uncertainty in PBM and non-PBM. The reviewed
      2026-07-22 run found no sustained onset in either scope.
- [ ] Repeat sustained-onset inference with validated morpheme, syllable, and
      phoneme effort controls.
- [ ] Prototype downstream caregiver-response predictive gain and validated
      repair/clarification/contingent-response outcomes as listener-utility
      measures. Keep these separate from target self-information.
- [ ] Calibrate Route 2 response uncertainty on a deeply sampled stratified
      subset: exact-string versus semantic-cluster entropy, coverage/rarefaction,
      seeds, prompts, temperatures, and a decoupled-generator sensitivity.
- [ ] After entropy calibration, refit raw-effort and generated-relative effort
      models as distinct estimands; do not use generated expected effort as an
      automatic ordinary confound.
- [ ] Audit morphology, syllable/phoneme, lexical-diversity/rarity, and
      dependency-feasibility coverage before using them as primary controls;
      then run the corresponding direct-score sensitivities.

### Compute extensions that do not block the core direct-score result

- [x] Preserve the implemented full-79 LSTM generation workflow in
      `generate_baselines_mila` commit
      `134f4df4eb3bc60df93fe1dfee72811012b08ea2`, add explicit single-task
      Slurm requests, pass its local tests/shell audit, push the branch, and
      open draft PR #1. No Mila job was submitted.
- [x] Run and audit the full-79 k3 same-length LSTM generation DAG, then run and
      audit Mistral utterance `k0`/`k3` scoring. The 1,140,218-row immutable
      compute handoff is local; analysis-repository ingestion remains the open
      task recorded above.
- [ ] Decide after scientific review whether full-79 TinyDialogues scoring,
      full-79 context entropy/word-level surprisal, or a scored generated
      response cloud is worth the additional compute.
- [ ] If SES, race/ethnicity, parental education, sex/gender, or nationality
      become predictors, perform a new provenance-aware metadata coding pass;
      current coverage is not sufficient for general covariate use.

## 2026-07-21 Priority: TinyDialogues PBM Replication And Full-79 Mistral Analysis

This is the active analysis roadmap. It separates two scientifically different
uses of the newly available scores:

1. TinyDialogues is a **same-21-child PBM scorer-robustness replication**. It
   is not an independent developmental confirmation sample.
2. The remaining 58 non-PBM children in the completed 79-child Mistral tree
   are the preferred confirmation sample, provided the protocol is frozen
   before their main estimates are inspected.

The instruction to repeat “all reports and fitted models” means: inventory
every existing analysis, repeat every scientifically applicable current
analysis in a model-specific output namespace, explicitly record why an
analysis is not applicable, and do not revive superseded model-zoo artifacts
merely to increase the number of fits.

### A. Verified Data Contract And Remaining Provenance Work

- [x] Confirm the TinyDialogues PBM handoff is local and audit-complete:
      `results/external/compute_surprisal_mila/raw_surprisal_tinydialogues_pbm_21_children_all_6_conditions_k0_k1_k2_k3_fp32`
      resolves to run `20260717_201227`; the local audit passes 504/504 files,
      21 children, 126 files per context, 84 files per mode, 11,605,772 scored
      target rows, zero blank targets, zero truncated-context rows, and zero
      recorded problems.
- [x] Confirm the completed full-79 Mistral handoff is local:
      `results/external/compute_surprisal_mila/raw_surprisal_cleaned_naturalistic_79_children_all_available_ages_fp16`
      resolves to run `20260713_162955` and contains 1,896 CSVs, 79 children,
      474 files per context, and 316 files per mode.
- [x] Run a strict TinyDialogues Route 1 ingestion smoke across caretaker plus
      real/random/unigram/bigram/trigram files. The 2026-07-21 six-file smoke
      wrote 252,717 rows and found zero missing target columns, blank targets,
      zero-word rows, missing/out-of-bin ages, missing scores, or matched-word
      length failures.
- [ ] Copy or regenerate a compact, relocation-safe full-79 audit report in
      `compute_surprisal_mila`, record its checksum, and link it from this
      repository's analysis manifest. Do not copy the 13 GB scored tree into
      Git.
- [ ] Freeze an analysis-input manifest for each scorer with model ID,
      immutable revision, tokenizer revision, precision, scoring-code
      revision, archive checksum, source root, file count, per-context/per-mode
      counts, row counts, and audit status.
- [x] Audit PBM row identity across TinyDialogues and Mistral using corpus,
      child, file, line number, utterance ID, role, candidate condition,
      context, exact target text, and exact context text. Use the TinyDialogues
      source hashes when present; never accept row position as the join key.
- [x] Produce a mismatch table for missing/extra/duplicate rows, target-text
      disagreement, context-text disagreement, age disagreement, and
      condition disagreement. Require zero unexplained mismatches before the
      paired cross-scorer analyses run.
- [x] Record that the six scored conditions are five child targets
      (`real`, `random`, `unigram`, `bigram`, `trigram`) plus a separate
      caretaker target; do not treat caretaker rows as a sixth matched child
      candidate.
- [x] Patch or explicitly exclude and flag the six empty full-79 generated
      targets (24 score cells across k0-k3): Forrester/Ella bigram IDs 1453 and
      1590; MPI-EVA-Manchester/Fraser bigram IDs 83669 and 12314 and trigram
      IDs 108945 and 38427. Regenerate and rescore them before calling the
      baseline matrix literally row-complete.
- [x] Preserve explicit context-availability flags for the 18,299 child rows
      and 2,722 caretaker rows without preceding k1/k2/k3 context; do not
      interpret them as ordinary context-bearing observations.
- [x] Recover Providence/Naima age 36.0 months for the 507 caretaker rows from
      `Naima/030000.cha`, preserve the original missing value, and record the
      repair source in the joined-table audit.

### B. Freeze The Analysis Protocol Before Looking At Non-PBM Effects

- [x] Write and date a PBM-discovery/non-PBM-confirmation protocol before
      fitting or plotting the remaining 58 children's main effects. Store the
      frozen formulas, outcomes, directions, exclusions, context choice,
      effort choice, onset rule, and multiplicity plan in a versioned Markdown
      document.
- [x] Make real-child k3 contextual target surprisal at fixed lexical word
      effort the primary direct-score outcome unless the frozen protocol states
      otherwise. Report k0 unconditional surprisal and k3-minus-k0 context gain
      as separate estimands rather than substituting one for another.
- [x] Predeclare the sign convention for context gain and all plotted labels:
      `gain_k = sum_bits_k0 - sum_bits_kk = log2 p(u | c_k) - log2 p(u)`;
      positive values mean the preceding context makes the observed target
      more probable under that scorer.
- [x] Predeclare primary child-turn eligibility and exclusions: same-session
      preceding caregiver turn, context availability, empty/punctuation-only
      targets, child-initiated turns, imitation, routines/reading,
      backchannels, question type, and repair sequences. Preserve every flag
      even when it is not part of the primary exclusion rule.
- [x] Predeclare the primary uncertainty method at the child level and the
      corpus-level sensitivity method. Do not use row-level IID intervals as
      the only uncertainty estimate for repeated utterances.
- [x] Predeclare the sustained-onset rule and simultaneous confidence-band
      procedure. Do not select the first significant age bin after inspecting
      the confirmation estimates.
- [x] State explicitly that TinyDialogues and Mistral have different
      tokenizers and scales. Primary cross-scorer conclusions compare
      within-model slopes, contrasts, context gains, rankings, and word- or
      character-normalized quantities—not raw bits per model token.
- [x] State explicitly that the TinyDialogues PBM rerun tests scorer robustness
      on the discovery data, whereas only the non-PBM 58-child Mistral analysis
      can serve as the planned sample replication.

### C. Build Model-Specific And Paired Analysis Tables

- [ ] Parameterize the Route 1 table/report pipeline around an immutable
      `scorer_id`/`scorer_family` rather than relying on Mistral-specific
      defaults. Keep model revision, tokenizer revision, dtype, scoring-code
      revision, source hashes, and input-manifest checksum in the schema and
      audits.
- [x] Give every generated table, fitted model, plot, and report a
      scorer-specific output directory. A TinyDialogues run must never
      overwrite the existing PBM Mistral products.
- [ ] Add tests covering the richer TinyDialogues provenance schema and the
      older Mistral schema, including explicit behavior when provenance fields
      are absent from a legacy score file.
- [x] Build the complete standalone TinyDialogues PBM long table from all 504
      files with recomputed word, character, morpheme, syllable, and phoneme
      effort from the exact scored target text. Publish source-file,
      variant-context, missingness, duplicate-key, and schema audits.
- [ ] Build a full-79 Mistral long table from all 1,896 files using streaming
      or partitioned outputs; retain all 28,694,516 possible target/context
      cells and flag, rather than silently discard, the 24 blank generated
      cells.
- [x] Add context-gain columns by exact within-scorer, within-target pairing of
      k1/k2/k3 against k0. Audit that target text is identical within every
      pair and keep k1, k2, and k3 gains separate.
- [ ] Rebuild parent-context effort, question type, context availability,
      session order, target frequency, lexical rarity, and the validated local
      complexity predictors against each new table. Do not blindly join PBM
      products to the new full-79 source.
- [x] Build a wide paired PBM table containing TinyDialogues and Mistral score
      columns on the same source rows, plus model-specific token counts,
      word/character-normalized scores, context gains, candidate gaps, and all
      join-status fields.
- [ ] Build sample-flow tables for every model: source rows, eligible rows,
      context-bearing rows, analysis rows, excluded rows by reason, children,
      sessions, corpora, age range, and age-bin coverage.
- [ ] Confirm whether TinyDialogues token offsets support the existing
      token-to-word alignment logic. If they do, generate a separate audited
      TinyDialogues word-level product; if they do not, mark word-level reports
      unavailable rather than reusing Mistral alignments.

### D. Inventory Every Existing Analysis And Decide Its Replication Status

- [ ] Generate a machine-readable CSV plus a readable Markdown matrix with one
      row for every analysis/report builder and current report. Required fields:
      scientific question, input columns, scorer dependence, PBM/full-79
      scope, current/superseded status, TinyDialogues action, full-79 Mistral
      action, missing prerequisite, output namespace, and verification command.
- [ ] Mark the following current direct-target families as mandatory
      TinyDialogues PBM repeats: core Route 1 descriptives; fixed-effort
      child-controlled models; child-length-controlled estimator suite;
      context-window and context-gain comparisons; real-versus-n-gram
      controls; caretaker/input trajectories; age-scrambling and leave-out
      robustness; developmental-onset analysis; and the selective
      candidate-evidence synthesis.
- [ ] Repeat the direct-score comparison portion of the corrected PBM Bayes
      report with TinyDialogues, while leaving the already cross-fitted
      Bayes-derived candidate-set probabilities unchanged. Label this as a new
      direct-scorer agreement analysis, not a new Bayes fit.
- [x] Classify context-entropy-dependent M4/Z3/Z4/Z10/F-family models as
      **not exact TinyDialogues replications** until TinyDialogues-specific
      next-token entropy/top-k features exist. A Mistral entropy predictor may
      be shown only as a clearly labeled cross-model sensitivity.
- [x] Classify LSTM-target comparisons as unavailable for TinyDialogues unless
      the PBM LSTM candidates are separately scored with TinyDialogues. Do not
      infer TinyDialogues LSTM performance from the Mistral-scored LSTM files.
- [ ] Classify heldout-child prediction as a separate Mistral generalization
      analysis unless corresponding TinyDialogues heldout scores are produced.
- [x] Classify Route 2 sampled-response entropy/relative-effort reports as a
      different data product, not something already repeated by the 504 Tiny
      target-score files. Repeating them with TinyDialogues would require a
      frozen response-sample contract and TinyDialogues scoring of those
      sampled responses.
- [ ] For each legacy M1-M15/model-zoo/atlas report, choose one of: regenerate
      because it supports a current estimand; retain as an archival Mistral
      artifact; or supersede with a focused model card. Record the decision so
      “exhaustive” means complete coverage, not indiscriminate fitting.
- [x] Regenerate the scientifically applicable legacy Route-1/model-atlas
      families from the complete TinyDialogues PBM long table in a dedicated
      namespace. The corrected atlas has 41/56 direct model-zoo subvariants
      and 45/45 explicit comparison models fitted; its 15 entropy/certainty
      subvariants are explicitly unavailable because TinyDialogues-specific
      next-token entropy/top-k predictors do not exist.
- [x] Add a top-level browser/report index that links the Mistral PBM,
      TinyDialogues PBM, paired cross-scorer, full-79 Mistral descriptive, and
      non-PBM confirmatory reports without mixing their claims.

### E. TinyDialogues PBM Models And Diagnostics To Fit

- [ ] Reproduce source/context/age/corpus/child coverage, score and effort
      distributions, extreme-tail audits, score-versus-length plots, token
      normalization diagnostics, and representative-row checks.
- [x] Fit the primary real-child fixed-effort model with age, lexical word
      effort, child identity, and the frozen context controls. Save formulas,
      coefficients, covariance method, fit warnings, prediction grids, and
      fixed-effort lines.
- [x] Fit repeated-measures estimator sensitivities that answer the same
      estimand: child-fixed-effects OLS with child-clustered covariance,
      within/between (Mundlak) model, child-clustered GEE, random-intercept and
      justified random-age-slope mixed models, and child-level bootstrap.
      Treat nonconvergence/singular fits as audit results, not silent omissions.
      Completed in the 2026-07-21 modular run for P1/P3 in TinyDialogues PBM
      and all three Mistral scopes; mixed fits are unweighted design-cell
      sensitivities, not replacements for the frozen primary model.
- [x] Fit continuous linear age, the predeclared nonlinear age form, and frozen
      age-bin contrasts. Do not select the displayed age form using the same
      significance criterion later used for inference.
- [x] Fit k0, k1, k2, and k3 target-surprisal models and direct k1/k2/k3
      context-gain models. Separate unconditional conventionality from
      context-supported predictability.
- [x] Fit real-versus-random/unigram/bigram/trigram paired gap models and
      source-by-age interactions. Report within-row candidate gaps and
      child-level uncertainty; do not call the candidates meaning-preserving.
      Completed with 200-child bootstrap intervals and leave-one-child/corpus
      influence; candidates remain explicitly non-meaning-preserving.
- [x] Fit caretaker/input trajectories separately from child-target models,
      with child age interpreted as caregiver input adaptation rather than an
      adult developmental endpoint. The modular run adds separate caretaker
      k3, k0, and context-gain models and age-bin trajectories for Tiny PBM and
      Mistral PBM/non-PBM/all79.
- [ ] Run exact/top-coded word-count strata, alternative effort denominators,
      context-availability, question/response eligibility, corpus leave-out,
      child leave-out, influential-child, age scrambling, and tail-trimming
      sensitivities.
- [ ] Repeat the developmental-onset workflow with TinyDialogues only after
      implementing child bootstrap/small-cluster uncertainty and the frozen
      sustained-onset rule. Do not promote a TinyDialogues onset from a
      data-selected breakpoint.
- [ ] Produce compact model cards for every promoted fit: estimand, formula,
      row/child/session/corpus counts, exclusions, coefficient direction and
      interval, covariance/cluster unit, convergence warnings, prediction
      range, and interpretation boundary.

### F. Paired TinyDialogues-Versus-Mistral Scorer Robustness

- [x] Compare paired real-target k0/k1/k2/k3 scores using word- and
      character-normalized scales, rank correlations, within-child centered
      correlations, and age/length/corpus calibration plots. Keep raw
      bits-per-token comparisons diagnostic only.
- [x] Compare each scorer's fixed-effort age coefficient, interval, predicted
      line, nonlinear shape, and age-bin contrasts. Bootstrap the difference
      in coefficients by child rather than declaring agreement from two
      separate p-values. The linear P1/P2/P3 slope differences and paired
      child overlays, frozen P1/P2/P3 age-bin contrasts, and paired
      quadratic-coefficient child bootstraps are complete.
- [x] Compare k1/k2/k3 context-gain magnitudes and developmental slopes across
      scorers on exactly paired utterances.
- [x] Compare real-minus-baseline gaps, candidate rankings, baseline ordering,
      source-by-age interactions, and child-level gap trajectories across
      scorers. The paired run includes all four gap slopes/bootstrap
      differences, supported child-specific slopes, age-bin rankings, and
      candidate-specific age interactions with source-specific child and word
      effects.
- [x] Quantify sign concordance and effect-size heterogeneity across the 21
      child-specific slopes. Identify influential reversals transparently; do
      not hide them behind only the pooled coefficient. The paired visual run
      records supported slopes for P1, P3, and all four candidate gaps; P1
      signs agree for 18/21 children.
- [ ] Diagnose disagreement by scorer tokenization, word/character length,
      age, corpus, child, target frequency, OOV/special-form flags, context
      length, and source condition. Recorded evaluated-token ratios and
      word-normalized age/corpus scale differences are complete; lexical
      frequency, OOV/special-form, context-length, and source-condition
      diagnostics remain.
- [x] Build a paired-scorer synthesis report that distinguishes robust
      agreement, scale-sensitive agreement, null results, and reversals. A
      TinyDialogues match strengthens scorer robustness but is not an
      independent sample replication.

### G. Individual Child Trajectories

- [ ] Create one canonical child-age-session trajectory table for all 79
      children, with utterance/session counts, age coverage, raw mean target
      surprisal, fixed-effort adjusted prediction, k0/k3 values, k3 context
      gain, effort, and missingness/eligibility counts.
- [x] Produce a 79-child Mistral trajectory index and one profile page/panel per
      child. The primary panel should show real-child k3 fixed-effort
      predictability across age; secondary panels should show k0, context gain,
      effort, and real-minus-baseline gaps.
- [x] Produce corresponding 21-child TinyDialogues profiles and paired
      TinyDialogues-versus-Mistral overlays on identical axes/ranges where
      meaningful.
- [ ] Show raw session/bin summaries and model-adjusted trajectories together,
      with utterance counts and age gaps visible. Do not draw a smooth line
      through unsupported age intervals without marking it as interpolation.
- [x] Define minimum support for child-specific slopes (distinct sessions,
      distinct ages, age span, and utterance count). Report insufficient-data
      children descriptively instead of forcing unstable regressions.
- [ ] Fit child-specific exploratory slopes/curves where support permits and a
      hierarchical partial-pooling trajectory model for population and child
      heterogeneity. Keep individual fits descriptive unless multiplicity and
      shrinkage are handled.
- [ ] Save child-level coefficient/interval tables, trajectory grids,
      influential-child diagnostics, and machine-readable plot audits so every
      child shown in the index has a traceable source.
- [ ] Add corpus-level small multiples, all-child spaghetti/heatmap summaries,
      and a distribution of child slopes, while retaining the individual pages
      requested above.

### H. Full-79 Mistral Discovery/Confirmation Models

- [x] Build a descriptive full-79 report without calling the pooled 79-child
      coefficient confirmatory. Show coverage, sample flow, distributions,
      corpora, contexts, effort, and individual trajectories first.
- [x] Fit the frozen primary formulas separately in PBM discovery (21
      children) and non-PBM confirmation (58 children/10 corpora). Never pool
      PBM into the confirmation estimate.
- [x] Report the non-PBM fixed-effort real-child k3 age effect, k0 age effect,
      and k3 context-gain age effect with child-level uncertainty and the
      predeclared direction/decision rule.
- [x] Fit the same repeated-measures estimator ladder in the confirmation
      sample: child FE/clustered OLS, within/between model, GEE, justified mixed
      effects, and child bootstrap. Add corpus leave-one-out and a small-number
      of-corpora uncertainty sensitivity. The completed modular run includes
      200 child bootstraps, 200 corpus bootstraps, GEE, Mundlak, mixed
      intercept/slope sensitivities, and corpus/child leave-out; boundary and
      convergence warnings remain in the manifest.
- [ ] Fit predeclared nonlinear/age-bin models and sustained-onset inference in
      the non-PBM sample. Present onset as replicated only if the frozen rule
      and simultaneous band are satisfied.
- [x] Repeat real-versus-random/unigram/bigram/trigram paired candidate-gap
      models in PBM and non-PBM samples, keeping same-length effort checks and
      candidate-set interpretation limits visible. The modular run repeats all
      four in PBM, non-PBM, and pooled descriptive scopes with child bootstrap
      and influence diagnostics.
- [x] Estimate corpus and child heterogeneity rather than reporting only a
      grand mean: forest plots, random-slope variance where identifiable,
      leave-one-corpus-out estimates, and influence diagnostics. The modular
      run adds supported child-slope distributions, random-age-slope fits, and
      leave-one-child/corpus ranges; warning-bearing fits are visibly flagged.
- [ ] Run local CPU-derived effort/complexity sensitivities (words,
      characters, validated morphology, syllables, phonemes, lexical rarity,
      vocabulary trajectory) after missingness and quality are audited by
      child/corpus/age.
- [ ] Treat context entropy, word-level neural surprisal, semantic entropy,
      complexity, and corrected Bayes scores as separate missing/partial
      predictor projects. Full-79 LSTM targets/scores and exact-string Qwen
      response-space entropy now exist, but their availability does not turn
      them into ordinary controls or meaning-preserving alternatives.
- [ ] Decide whether full-79 TinyDialogues scoring is scientifically worth the
      additional compute after the PBM cross-scorer report is reviewed. If
      selected, create a new smoke/manifest/audit contract; the 504-file PBM
      marker does not authorize that run.

### I. Reporting, Testing, And Completion Gates

- [ ] Write focused unit tests for multi-scorer ingestion, provenance
      preservation, exact paired joins, context-gain signs, scorer-specific
      namespaces, blank-target flags, Naima age repair, confirmation-sample
      exclusion, child-profile support rules, and report image/link audits.
- [ ] Add tiny integration fixtures with two scorers, multiple contexts,
      matched baselines, one missing context, one blank candidate, and one
      deliberate key mismatch; require the audit to fail on the mismatch.
- [x] Add resumable/atomic stages for the 11 GB Tiny tree and 13 GB full-79
      Mistral tree so a failed fit or plot does not require rebuilding the long
      table or overwrite valid results.
- [x] Save model summaries, coefficient-long tables, prediction grids,
      bootstrap draws/seeds, convergence warnings, sample-flow tables, and
      figure manifests before rendering reports.
- [x] Run focused tests after each pipeline change and the full unit suite at
      the end. Record the actual command, date, pass count, runtime, and
      expected warnings; do not reuse the July 13 count.
- [ ] Audit every Markdown/HTML report for missing images, stale Mistral-only
      wording, accidental raw token-scale comparisons, PBM/full-79 scope
      confusion, and unsupported claims of efficiency, information, onset, or
      confirmation.
- [x] Build short plot-led TinyDialogues and full-79 Mistral summaries with one
      compact headline table, separate individual-child galleries, model-family
      coverage plots, and machine-readable plot audits. Dataset, model, plot,
      and report stages are independently rerunnable and write chained JSON
      manifests.
- [x] Build a separate short paired-scorer visual report with 11 slope
      comparisons, 200 paired child bootstraps, P1/P2/P3 age-bin contrasts,
      child sign concordance, scale diagnostics, and a 5/5 plot audit. Its
      models, plots, and report are independently rerunnable from the immutable
      exact paired table.
- [ ] Update `AGENTS.md`, `docs/notes.md`, formal definitions, and the
      supervisor-facing synthesis only after the relevant outputs exist and
      their audits pass. Keep proposed, completed, null, contrary-direction,
      and blocked analyses visually distinct.
- [ ] Completion gate: every row in the analysis-replication matrix has a
      verified scorer-specific output or an explicit non-applicability/data
      blocker; all 21 TinyDialogues child profiles and all 79 Mistral child
      profiles exist; primary PBM/non-PBM estimates have child-level
      uncertainty; and no required audit reports unexplained mismatches.

## Recovered Initial Formulation: Bayes And Complexity TODOs

2026-07-05 source: `docs/Communicative_Efficiency (1).pdf`, the downloaded
initial project formulation. This is now treated as part of the core project
scope, not as an optional later extension.

### Informativeness Formulations To Implement / Compare

- [x] Restate the initial informativeness formulation in `docs/design.md`:
      unconditional `p(u)`, direct contextual `p(u | c)`, and Bayes
      decomposition `p(u | c) = p(c | u) * p(u) / p(c)`.
- [x] Keep the current Mistral contextual surprisal analyses as the direct
      `p(u | c)` family. Do not discard them: they are one legitimate
      operationalization of contextual informativeness.
- [x] Add a Bayes-decomposition design note for reports: for a fixed context
      `c`, compare candidate utterances by `log p(u) + log p(c | u)`, because
      `log p(c)` is a context-specific constant.
- [ ] Build additive age-bin `p(u)` prior tables for real and generated child
      utterances using the existing random/unigram/bigram/trigram dictionaries.
      Keep PBM proof-of-concept priors and full strict-naturalistic priors
      separate.
- [ ] Prototype an LSTM-based `p(u)` prior only after the additive LSTM
      generation/scoring artifacts are stable. CPU smoke tests are fine; real
      training belongs on Mila GPUs.
- [ ] Define and benchmark at least two replacements for the current weak
      order-3 `p(c | u)` proof of concept before any production rerun: a
      cross-fitted reverse/discourse model and either a full-utterance neural
      likelihood or a contrastive matched-versus-shuffled context scorer.
- [ ] Add a tiny local CPU smoke test for the Bayes algebra using fake
      probabilities so sign conventions are verified before any Mila run.
- [x] Build a compact Bayes pilot table on a small audited subset with columns:
      `context_id`, `utterance_id`, `source_model`, `log2_p_u`,
      `log2_p_c_given_u`, `bayes_log2_score_unnormalized`,
      `direct_mistral_sum_bits`, effort columns, age, child, and provenance.
- [x] Compare direct `p(u | c)` surprisal with Bayes-decomposed scores on real
      child utterances before using Bayes-derived results in supervisor-facing
      claims.
- [x] In all reports, label legacy Bayes scores as decomposition-based or
      posterior-style scores unless the normalizer `p(c)` has actually been
      estimated; label corrected v2 values as candidate-set probabilities or
      candidate-set surprisal and name the finite candidate set.

### Complexity / Effort Predictors To Add

- [x] Restate the initial complexity formulation in `docs/design.md`: MLU in
      orthographic, phonotactic, and word space; dependency length; grammatical
      complexity through MLU; lexical complexity through vocabulary size.
- [x] Create a CPU-first predictor extractor for orthographic MLU:
      word count, character count, mean word length, and age-bin/child-session
      aggregates.
- [ ] Create or audit morpheme-count extraction from CHAT-derived morphology
      where available. Record missingness by corpus, child, age bin, and
      session before using it as a primary outcome.
- [ ] Add syllable, phoneme, and simple phonotactic-shape predictors. Start
      with a deterministic CPU method, then document which utterances cannot be
      mapped reliably.
- [ ] Add lexical-complexity predictors: cumulative child vocabulary size,
      age-bin vocabulary size, type-token ratio, moving-average lexical
      diversity, and age-conditioned lexical rarity.
- [ ] Run a dependency-length feasibility audit on a small, age-stratified,
      corpus-stratified sample. Do not make dependency length a primary
      predictor until parser failure modes on short child utterances are
      documented.
- [x] Build per-child and per-age-bin complexity trajectories so grammatical
      and lexical complexity can be analyzed alongside informativeness and
      production effort.
- [x] Join complexity predictors to Route 1/Route 2 analysis-ready tables only
      after row keys and missingness have been audited.
- [ ] Add sensitivity analyses that ask whether age trends in informativeness
      survive controls for MLU, vocabulary size, and dependency/phonological
      complexity.

### Modular Repositories And Cluster Work

- [x] Create a lightweight `generate_baselines_mila` repo for baseline
      generation only. It should generate CPU n-gram/random baselines and GPU
      LSTM/neural baselines from manifest inputs, then export scorer-ready CSVs.
      Initial local repo path:
      `/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila`.
      Initial commit: `8251088` (`Initial baseline generation scaffold`).
      Pushed to `git@github.com:NicolasGoulet/generate_baselines_mila.git`
      on branch `main`.
      Latest production-path commit: `7ffca3d`.
- [x] Implement the first runnable CPU path in `generate_baselines_mila`:
      manifest-driven additive age-bin random, unigram, bigram, and trigram
      same-length generation with checksum/audit sidecars and unit tests.
- [ ] Keep this repo as the brain/reporting repo. It should prepare manifests,
      receive compact audited outputs, build analyses, and generate reports,
      but should not own multi-GB Mila scoring outputs.
- [ ] Keep `compute_surprisal_mila` as the direct LLM surprisal scoring repo.
- [x] Create a separate local `bayes_efficiency_mila` repo for `p(c | u)`
      likelihood scoring and Bayes-decomposition table building. Initial local
      repo path:
      `/home/apaixonada/EvaPortelance/Projet_1/bayes_efficiency_mila`.
      Initial commit: `c37acd5` (`Initial Bayes decomposition scaffold`).
      Pushed to `git@github.com:NicolasGoulet/bayes_efficiency_mila.git` on
      branch `main`.
      Latest production-path commit: `67bbcfc`.
- [x] Create a separate local `child_complexity_predictors` repo for MLU and
      complexity predictor extraction. Initial local repo path:
      `/home/apaixonada/EvaPortelance/Projet_1/child_complexity_predictors`.
      Initial commit: `758a388` (`Initial complexity predictor scaffold`).
      Pushed to
      `git@github.com:NicolasGoulet/child_complexity_predictors.git` on branch
      `main`.
      Latest production-path commit: `33497c2`.
- [x] Add one cross-repo Mila smoke-test Slurm script in the execution repo,
      not the local brain repo:
      `generate_baselines_mila/slurm/modular_repos_smoke.sbatch`. It creates
      tiny fixture data, runs all three modular repo test suites, runs n-gram
      generation, runs a tiny LSTM smoke if torch is importable, runs n-gram
      Bayes decomposition, and runs complexity extraction plus trajectory
      export. On Mila, keep only the three modular execution repo checkouts in
      a permanent `$HOME` code directory as siblings; do not require
      `communicative_efficiency` there. The smoke runner writes job artifacts
      to `$SCRATCH/modular_repo_smoke/<job_id>` by default.
- [x] Document the modular repo Git-vs-rsync data policy in
      `docs/modular_repo_data_policy.md`: only code/configs/docs/tests/tiny
      fixtures go through Git; real preprocessed data and generated/scored
      outputs move with `rsync`; permanent Git checkouts belong in `$HOME`
      while outputs and temporary files belong in `$SCRATCH` and must be
      removed after retrieval/audit.
- [x] Build PBM cleaned-data integration manifests using the existing
      `compute_surprisal_mila/data/{Brown,Manchester,Providence}/*/chi.csv`
      cleaned utterance files or strict-naturalistic bundle scoring CSVs as
      the first real-data test layer after synthetic smoke.
- [ ] After synthetic and PBM integration tests pass, `rsync` the full
      strict-naturalistic preprocessed bundle to Mila cluster storage and run
      production-scale manifests there.
- [x] Add an initial CPU Slurm scaffold for manifest-driven
      n-gram/random/unigram/bigram/trigram generation.
- [ ] Extend the CPU Slurm scaffold into job arrays over age bin, corpus scope,
      context window, and split once the production manifests are written.
- [x] Add a GPU LSTM Slurm scaffold and manifest with an explicit
      not-implemented CLI guard so nobody can accidentally claim LSTM
      generation ran before the real port exists.
- [x] 2026-07-14: Port the real encoder-decoder LSTM training/generation path
      into `generate_baselines_mila`, add resumable training and atomic
      artifacts, and make the GPU Slurm command execute real training.
- [x] 2026-07-14: Select the full-79 production scope from the PBM evidence:
      k3 caretaker context and same-length generation only, with eight additive
      age-bin models. Add CPU preparation, exact-wrapper GPU smoke, staged
      arrays, audits, and final marker handling.
- [x] Execute the selected full-79 LSTM DAG on Mila, retrieve and audit its
      compact generation handoff, and complete separate Mistral `k0`/`k3`
      scoring. This historical task is complete; do not rerun it.
- [ ] Add checksums/manifests to every generated-baseline export so scorer
      repos can verify that row order, row ids, context windows, and utterance
      counts match expectations.
- [ ] Preserve existing PBM proof-of-concept outputs. Build full
      strict-naturalistic baselines as new outputs with explicit names rather
      than overwriting old real utterances or old generated baselines.

## Current Route 2 Response-Space Preparation

2026-07-02 status: the Mila response-space generation run is complete enough
to begin Route 2 table construction. Production run:

```text
/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333
```

Known run summary from the Mila audit:

- `context_ks`: `k3`
- `prompt_variant`: `Caregiver`
- `temperature`: `0.5`
- `manifest_contexts`: `268,712`
- `selected_rows`: `26,871,200 / 26,871,200`
- `incomplete_settings`: `176`
- `fallback_settings`: `176`
- `invalid_fallback_selected_rows`: `6,584`

### Route 2 Build Principles

- Do not pull the full `selected_samples` or `all_attempts` production outputs
  to the laptop unless there is a specific audit reason. Build compact
  generated-response effort summaries on Mila, then `rsync` compact products
  back.
- Keep `compute_surprisal_mila` as the Slurm/HPC/audit repo. Put cluster-side
  summarization scripts there; put downstream analysis/report builders here.
- Use one stable context key everywhere:
  `response_entropy_context_id = sha256(normalize_context(context_text))[:24]`.
  Do not assume older `context_entropy_context_id` columns are equivalent
  without an audit.
- Restrict the first production Route 2 table to
  `role == child`, `target_variant == real`, `context_k == k3`, nonempty
  `context_text`, `prompt_variant == Caregiver`, and `temperature == 0.5`.
- Preserve row provenance: `score_id`, `utterance_id`, `dataset`, `child_id`,
  `session_id`, `age_months`, `age_bin`, `file`, `line_no`, `utt_id`,
  `context_text`, and `target_utterance_clean`.
- Treat the `176` incomplete contexts as visible audit flags, not hidden
  failures. Main models can exclude or sensitivity-check them, but the table
  must carry `fallback_used`, `valid_selected_count`, and
  `invalid_selected_count`.
- Do not claim the generated samples hold meaning constant. Frame them as a
  context-conditioned response space.

### Route 2 Inputs

- Real child row base:

```text
results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz
```

- Compact real-child context/effort helper, useful for fast audits:

```text
results/context_predictor_permutations/route1_real_child_context_measures_k3.csv.gz
```

- Mila response-entropy features:

```text
/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333/merged/context_response_entropy_features.csv.gz
```

- Mila selected generated samples for cluster-side aggregation only:

```text
/network/scratch/g/gouletn/compute_surprisal_mila/response_entropy_runs/20260618_164333/shard_outputs/shard_*/selected_samples.csv.gz
```

### Immediate Route 2 TODOs

- [x] In `compute_surprisal_mila`, add a CPU Slurm summarizer that streams
      `shard_outputs/shard_*/selected_samples.csv.gz` and writes a compact
      `generated_response_effort_summary_by_context.csv.gz`.
- [x] The generated-effort summary must be valid-only by default and include:
      sample count, word/character mean, SD, median, p10, p25, p75, p90, min,
      max, and a compact word-count histogram JSON by `context_id`,
      `prompt_variant`, and `temperature`.
- [x] Include audit columns in the summary: selected rows, valid rows, invalid
      fallback rows, fallback used, incomplete context flag, and source shard
      coverage.
- [x] `rsync` only compact Route 2 products back to the laptop:
      `context_response_entropy_features.csv.gz`,
      `setting_summary.csv.gz`, and
      `generated_response_effort_summary_by_context.csv.gz`.
- [x] Add a local `communicative_efficiency` builder that filters real child
      `k3` rows, recomputes `response_entropy_context_id`, and joins response
      entropy plus generated effort summaries. The builder now caches the
      filtered Route 1 base at
      `results/route2_response_space/route2_real_child_k3_base_rows.csv.gz`
      so reruns do not rescan the 1.7GB Route 1 long table unless
      `--rebuild-route1-cache` is passed.
- [x] Output the first analysis-ready table:

```text
results/route2_response_space/route2_child_response_space_effort_table.csv.gz
```

- [x] The first table must add these predictors to actual real-child rows:
      `response_entropy_bits`, `response_unique_response_count`,
      `response_top_probability`, `generated_expected_words`,
      `generated_median_words`, `generated_p90_words`,
      `child_words_minus_generated_mean`, `child_words_z_vs_generated`,
      `child_words_percentile_in_generated_distribution`,
      `child_shorter_than_generated_median`,
      `child_longer_than_generated_p90`, `fallback_used_for_context`,
      and `valid_sample_count`.
- [x] Write a join audit with row counts: eligible real child rows, matched
      response-entropy rows, matched generated-effort rows, missing context
      ids, duplicate context ids, and counts by age bin/dataset.
- [x] Write a manual-review sample CSV of joined rows: random rows, high
      entropy, low entropy, child much shorter than generated expectation,
      child much longer than generated expectation, and fallback contexts.
- [x] Make first-pass plots only after the table audit is clean: child length
      percentile in generated response space by age, generated expected length
      by child age, response entropy by child age, and child length residual
      versus response entropy.
- [x] Fit first-pass models after the clean table audit. This was upgraded from
      tiny OLS sanity models to a repeated-measures suite: child-session GEE,
      child-session Mundlak within/between age GEE, child-session MixedLM
      random effects where stable, and row-level OLS child-FE/clustered-SE as a
      comparator.

### Later Full Communicative-Efficiency Cloud

- [x] Build an available-now information-effort cloud from already scored
      real, random, unigram, bigram, trigram, and additive LSTM rows. This is
      the decoupled-generator baseline cloud we already had: non-Mistral
      generators scored under the common Mistral scorer.
- [ ] Use the existing scored baseline cloud as the first evidence layer in
      the July communicative-efficiency materials:

```text
results/existing_scored_baseline_efficiency_cloud/
figs/existing_scored_baseline_efficiency_cloud/
docs/existing_scored_baseline_efficiency_cloud.md
docs/existing_scored_baseline_efficiency_cloud.html
```

- [ ] Create a scoring bundle for generated selected samples so Mila can score
      `sampled_response_text` under the same `context_text` with Mistral.
- [ ] Score generated responses on Mila, not on the laptop.
- [ ] Build a cloud table with one generated response row per context/sample:
      generated effort plus generated surprisal/information.
- [ ] Treat Mistral-generated + Mistral-scored samples as a **Mistral
      self-reference cloud**, not as independent evidence. Keep it, but label
      it separately from decoupled-generator clouds.
- [ ] If compute allows, add another LLM generator and score those samples with
      Mistral. This would create a stronger decoupled-generator LLM cloud:
      other-model-generated + Mistral-scored.
- [ ] Continue using `response_entropy_bits` from the Mistral response-space
      run as a context-level scorer-uncertainty predictor/stratifier. Do not
      describe it as model-independent behavioral uncertainty.
- [ ] Join each real child utterance to its generated response cloud and compute
      cloud-relative information/effort metrics: information percentile,
      effort percentile, efficiency rank, Pareto/frontier indicator, and
      distance to generated frontier.
- [ ] Keep the length-only Route 2 table and the full information-effort cloud
      as separate products so the first analysis is not blocked by the later
      Mila scoring run.

### Current Response-Space Analysis TODOs

- [x] Build compact response-space predictor exports so the new predictors are
      usable beyond the Route 2 table without inflating the 11.6M-row Route 1
      long table:

```text
results/route2_response_space_analysis/response_space_predictors_by_context.csv.gz
results/route2_response_space_analysis/response_space_predictors_by_utterance.csv.gz
```

- [x] Build Route 2 effort-choice plots requested by the supervisor framing:
      child length percentile in the generated response distribution by age,
      generated expected response length by age, response entropy by age, child
      length residual versus response entropy, and actual child length versus
      generated expected length.
- [x] Fit focused Route 2 effort models, not a giant model zoo, while respecting
      repeated measures: child effort outcomes (`nb_words`, morphemes,
      syllables, phonemes) as a function of response entropy, generated
      expected effort, context length, next-token context entropy, and age using
      child-session aggregates, GEE grouped by child, mixed models with child
      random effects where stable, and within/between-child age decomposition.
      Keep OLS with child fixed effects and clustered SE only as a baseline
      comparator.
- [x] Fit a fallback-sensitivity Route 2 check excluding the `176` fallback
      contexts / `218` fallback child rows.
- [x] Build Route 1 response-space-enriched information models on actual real
      child rows: `sum_bits` and `mean_bits_per_token` as outcomes, with child
      effort, age, context entropy, response entropy, and generated expected
      effort. Use the same repeated-measures strategy: child-session aggregate
      GEE, mixed models where stable, within/between-child age decomposition,
      and OLS child-fixed-effect/clustered-SE only as a comparator. Treat this
      as Route 1 predictor enrichment, not as the full generated-response
      information-effort cloud.
- [x] Generate compact coefficient tables, prediction grids, and plots for the
      Route 1 response-space enrichment so the new predictors can be inspected
      alongside the older Route 1 fixed-effort story.
- [x] Write an audit/report Markdown summarizing row counts, formulas, model
      interpretations, and limitations, especially that generated responses are
      context-conditioned alternatives and are not held-meaning paraphrases.
- [x] Build the dedicated Route 2 peer-review relative-effort suite: outcomes
      are child effort residual/percentile/ratio against the generated
      response-space length distribution for the same caregiver context, plus
      binary indicators for shorter than generated median and longer than
      generated p90. Fit the full age/response-entropy/context-demand ladder
      with row-level child-FE clustered models, child-session GEE,
      child-session Mundlak GEE, child-session MixedLM checks, and no-fallback
      final-model sensitivity.
- [x] Generate the Route 2 relative-effort audit, age-bin descriptives,
      response-entropy-bin descriptives, final coefficient tables, prediction
      grids, figures, and supervisor-readable Markdown/HTML report:

```text
results/route2_relative_effort_model_suite/
figs/route2_relative_effort_model_suite/
docs/route2_relative_effort_model_suite.md
docs/route2_relative_effort_model_suite.html
```

## Next Priority: Route 1 Best-Model Robustness Package Before Supervisor Report

This is the next Codex task to start in a fresh session. Do not treat the Atlas
as the story. The Atlas is the inventory. The goal here is to fit, verify, and
plot the best Route 1 model families so the scientist can choose the strongest
evidence for answering Prof. Xu and Prof. Portelance before writing the actual
supervisor-facing report.

Scope:

- Route 1 only: outcome is utterance information, usually `sum_bits`.
- Do not write the final supervisor report yet.
- Build a pre-supervisor candidate report / evidence gallery that shows the best
  models, robustness checks, plots, model cards, effect interpretations, and
  cautions.
- Reuse existing correct fitted artifacts where possible. Refit only missing or
  incomplete model/estimator combinations.
- Keep all fitted summaries, prediction grids, plots, and model-card metadata so
  this does not need to be refit again to regenerate reports.

### Active Correction For The Current Agent Task

This section overrides any drift toward a giant M1-M15 inventory dump. The
current deliverable is a **focused, plot-first candidate report** for choosing
what belongs in the later supervisor report.

Keep these constraints in view while editing:

- Do not make the report a compact aggregate grid or a long table-first model
  zoo.
- Do not include every M1-M15 model just because it exists. Include the
  promising M1-M15 candidates that answer the scientific question, plus any
  newly fit simple parent-effort variants needed below.
- The analysis is about **communicative efficiency**, not raw growth in
  utterance size. Do not frame the goal as predicting how large total
  `sum_bits` gets with age. Raw total bits can rise simply because older
  children produce longer utterances, which is an MLU/length fact, not the
  efficiency claim.
- The main Route 1 estimand is conditional utterance information: how
  utterance-level `sum_bits` changes with age **at fixed child effort** and
  after relevant controls such as child identity and parent-context effort.
- The data are repeated utterance measurements from the same children, sampled
  across different sessions and ages. Estimator choices must be justified in
  that repeated-measures context.
- The key visual objects must be regression/fixed-effort age lines, including
  real children, generated baselines, caretaker contrasts, and the three
  heldout children's actual-vs-predicted lines.
- Tables are allowed only as compact support for interpretation and audit; they
  must not replace the plots.
- If an interaction is written, always write the lower-level predictors too:
  write `age_c + effort_c + age_c:effort_c`, not only `age_c:effort_c` or
  shorthand `age_c * effort_c`.
- Keep conditional total-bits and rate outcomes conceptually separate.
  `mean_bits_per_token` or `sum_bits / nb_words` is a secondary rate-outcome
  check. It may be useful for communicative efficiency, but it is not the same
  model as total `sum_bits` at fixed effort.
- Do not promote raw observed-vs-fitted `sum_bits` plots as evidence. Those
  mostly show that longer utterances contain more total bits and will confuse
  the communicative-efficiency question.
- Keep the pooled and child-controlled age effects visible as different
  answers. M1 (`sum_bits ~ age + effort`, no child identity) is a real
  pooled/compositional contrast. M2/M3 and richer child-identity models answer
  the within-child fixed-effort communicative-efficiency question.

Current focused formula family to test and plot:

- [x] **Base fixed-effort child model:** `sum_bits ~ age + child effort + child identity`.
- [x] **Simple parent-effort control:** `sum_bits ~ age + child effort + parent context effort + child identity`.
- [x] **Child-effort interaction:** `sum_bits ~ age + child effort + age:child effort + parent context effort + child identity`.
- [x] **Parent-effort reaction by age:** `sum_bits ~ age + child effort + parent context effort + age:parent context effort + child identity`.
- [x] **Parent-effort reaction by child effort:** `sum_bits ~ age + child effort + parent context effort + child effort:parent context effort + child identity`.
- [x] **Full age/context-interaction candidate:** `sum_bits ~ age + child effort + parent context effort + age:child effort + age:parent context effort + child identity`.
- [x] **Question/form-control variants:** rerun or reuse variants with and
      without `question_type`, but keep them clearly labeled so question type
      does not obscure the simpler parent-effort story.
- [x] **Promising existing M1-M15 candidates to include if relevant:** M2, M3,
      M4a, M4c, M5, M6, M7, M11, and M15. Do not include unpromising/noisy
      M1-M15 sections just to be exhaustive.
- [ ] **Secondary rate-outcome check:** repeat the strongest candidate(s) with
      `mean_bits_per_token` or `sum_bits / child effort` as the outcome, while
      still controlling for child effort as appropriate and clearly explaining
      that this is a different scientific question.

2026-06-18 status: added `docs/route1_formula_permutation_estimator_report.md`
and `.html` / `.embedded.html`. It fits 36 formulas x 7 estimator families on
the child-session/effort-band aggregate repeated-measures screen. Every formula
keeps age, child effort, and child identity handling. Context entropy,
parent-context effort, question type, `age:child effort`, `age:context entropy`,
and `age:parent context effort` are permuted with lower-order terms preserved.
The requested `child effort:parent context effort` interaction remains a
separate follow-up if needed, as does the secondary bits-per-token/rate outcome.

2026-06-18 correction: the formula-permutation report now puts the row-level
fixed-effort Atlas result before the aggregate estimator screen whenever an
exact Atlas analogue exists. It also adds a global fixed-effort summary that
averages the row-level fixed-word-count prediction lines across fixed sizes.
This is the compact answer to whether `sum_bits` goes up or down with age at
the same production-effort levels. Aggregate `mean_sum_bits` estimator lines
are explicitly labeled as sensitivity screens only.

2026-06-20 status: extended and reran the modular child-only
length-controlled model suite in
`src/build_route1_child_length_controlled_model_suite.py`. The current
real-child K3 word-effort run fit 21 formulas x 9 estimator/repeated-measures
structures (`189/189` successful fits), saved 189 fitted model pickle files,
generated 47 figures, and wrote
`docs/route1_child_length_controlled_model_suite.{md,html}`. The report is
plot-first and keeps all coefficient/fit tables as CSV artifacts. New F18-F21
models use exact word-count categories and exact-length age-slope interactions;
these are the strongest direct check that the fixed-effort developmental
pattern is not just the known age-related MLU increase.

2026-06-20 scientific read: primary row-level child-fixed-effect slopes remain
downward for all F01-F17 continuous-effort formulas. In the exact-length
F18-F21 layer, primary slopes are `41` downward and `7` upward; well-supported
short and middle lengths are predominantly downward, while the positive slopes
occur at length `8` and sparse longer lengths `10-12`, which must be treated as
support-limited rather than overclaimed.

2026-06-22 status: added `docs/route1_phoneme_effort_line_audit.md` and
`.html` to confirm the current real-child corrected Atlas phoneme-effort lines
use the 12 most frequent exact real-child phoneme counts. The selected values
are `2-13`, split as low `2-5`, middle `6-9`, and high `10-13`; the audit also
writes a frequency proof plot and a main-model phoneme-slope plot under
`figs/route1_phoneme_effort_line_audit/`.

2026-06-22 correction: replaced the weak supervisor proposed-completion
side-draft with a model-rich v2 in
`docs/predicting_utterance_level_information_report_proposed_completion.md`.
The original supervisor-facing report remains
`docs/predicting_utterance_level_information_report.md` and was not modified.
The side draft now promotes the model ladder, F01-F21 length-controlled suite,
exact-length MLU proof, estimator-family checks, age-scrambling checks,
real-vs-random/ngram/LSTM/caretaker context panels, source-specific Atlas
figures, paired source-gap models, and heldout-child diagnostics.

2026-06-22 status: added the figure-first exhaustive ANCOVA selection gallery
in `docs/route1_exhaustive_ancova_gallery.md` / `.html` / `.embedded.html`.
It fits and saves reusable adjusted age/source comparisons across words,
morphemes, both syllable measures, and phonemes. Outputs under
`results/route1_exhaustive_ancova_gallery/` include aggregate k0/k3/context
gain cells, ANCOVA term tests, adjusted marginal means, source-real contrasts,
top exact-effort values, exact-effort adjusted means, exact-effort source-real
gaps, and a figure manifest. The gallery is intentionally candidate-selection
material, not the supervisor report.

2026-06-22 update: revised the ANCOVA gallery so the report explains the model
logic and each plot. The opening now states why ANCOVA is needed instead of raw
ANOVA, which effort variables are controlled, how exact-effort plots guard
against an MLU-only explanation, and how the caregiver/CDS paper claim differs
from the current fixed-effort utterance-level analysis. The regenerated gallery
has `33` figure references and no missing image files; focused report-builder
tests pass (`9` tests).

2026-06-22 follow-up: clarified the source-minus-real plots. The report now
states that real child utterances are the `0` reference line, and the line plots
were regenerated with clearer titles, y-axis labels, and an in-plot `0 = real
child utterances` label.

2026-06-22 status: added
`src/build_route1_frequency_informativity_predictors.py` and computed the safe
first frequency-control layer:
`results/route1_frequency_informativity_predictors/hash_frequency_predictors.csv.gz`.
This gives exact-target recurrence and smoothed frequency bits by
`target_text_hash` for caretaker-CDS, real-child, and combined reference
scopes. Richer lexical/phone-sequence informativity predictors are scaffolded
in the builder but need a safer text-column streaming pass because pandas'
C parser segfaulted on the large scored text file in this environment.

2026-06-22 status: added the Portelance/Xu communicative-efficiency extension
suite in `docs/route1_portelance_xu_extension_suite.md` / `.html` /
`.embedded.html`. It implements Route 2 effort-as-outcome models, exact-
frequency-controlled Route 1 models, adult-likeness/caretaker-distance plots,
effort-information tradeoff plots, equalized age-bin bootstrap plots, and
scrambled-age null checks. Reusable outputs are saved under
`results/route1_portelance_xu_extension_suite/`, with figures under
`figs/route1_portelance_xu_extension_suite/`. Current limitation: the finite
k3 context-entropy extract contains real-child rows, so Route 2 effort models
are real-child models in this build; caretaker comparisons are covered through
the fixed-effort ANCOVA artifacts. Focused tests pass and the report image
audit found `18` image references with `0` missing files.

2026-06-22 status: added a curated staging report for possible additions to the
supervisor-facing report:
`docs/predicting_utterance_level_information_candidate_additions.md` /
`.html` / `.embedded.html`. This report does not modify the active supervisor
report. It explains the new predictors, states what the refreshed models say,
labels each figure as main-text/appendix/exploratory/optional, and writes
candidate manifests under
`results/route1_portelance_xu_extension_suite/candidate_additions/`.

2026-06-23 status: added a separate plot-first inspiration draft for the active
supervisor report:
`docs/predicting_utterance_level_information_route1_inspiration.md` and
`.html`. It does not modify
`docs/predicting_utterance_level_information_report.md`. The draft proposes a
cleaner fixed-effort utterance-information narrative, adds 10 existing Route 1
figure candidates, replaces the weak possible-next-steps framing, and records
how the already-existing word-level Mistral surprisal product can support a
lexical-identity / word-position follow-up.

Estimator rationale to state in the report:

- [x] **OLS + child fixed effects + clustered SE:** main comparable Atlas view;
      controls stable child identity and clusters repeated utterances by child.
- [x] **GEE Gaussian by child:** population-average repeated-measures check for
      continuous bits.
- [x] **GEE Gamma/log by child:** positive-skew robustness check for bits when
      the outcome is strictly positive.
- [x] **GLM Gaussian / Gamma-log where feasible:** distribution/link
      sensitivity checks; secondary to the repeated-measures estimators.
- [x] **MixedLM random child intercept:** lets children have different baseline
      information levels.
- [x] **MixedLM random child age slope:** lets children have different
      developmental trajectories; record convergence/singularity warnings.
- [x] **Month/session aggregate only as robustness:** useful for reducing
      pseudo-replication, but must not be presented as the main row-level
      result.

### Scientific Questions To Answer

- Given context and a fixed production-effort level, does child age predict
  total utterance information?
- Does the age effect survive child identity, effort, parent-context effort,
  context entropy/predictability, and question/statement type controls?
- Does the result survive estimator-family checks beyond ordinary least squares?
- Does the result survive age-bin / age-label robustness checks?
- Can PBM-trained models predict heldout children's real trajectories?
- Does the child pattern differ from the caretaker/parent pattern?
- Which plots and model families are strong enough to promote into the later
  supervisor-facing report?

### Core Formulas To Fit And Plot

Use centered predictors where the existing pipeline expects them. Always keep
lower-order terms when fitting interactions.

- [x] **M2 primary child-adjusted model:**
      `sum_bits ~ age + effort + child identity`.
      Hypothesis: at the same effort level, the child's age still predicts
      utterance information after accounting for stable child-level differences.
- [x] **M3 age-by-effort model:**
      `sum_bits ~ age * effort + child identity`.
      Hypothesis: the age effect may change depending on production effort.
- [x] **M4c question/form control model:**
      `sum_bits ~ age + effort + question type + child identity`.
      Hypothesis: the age effect is not just because older children receive or
      answer different kinds of prompts/questions.
- [x] **M5 combined context-control model:**
      `sum_bits ~ age + effort + context entropy + parent context effort + question type + child identity`.
      Hypothesis: the age effect remains after controlling major email-relevant
      confounds: target effort, context predictability, preceding caretaker
      effort, and question/statement type.
- [x] **M15 / richest current interaction model:**
      include age, effort, context entropy, parent context effort, question type,
      and theoretically relevant interactions, with all lower-order terms kept.
      Hypothesis: the developmental effect is not an artifact of a missing
      context or effort interaction.
- [x] **Nonlinear age model:**
      add age spline or age-quadratic/categorical-age-bin variants.
      Hypothesis: the developmental trajectory is not necessarily one straight
      line across all months.
- [x] **Month-level aggregated model:**
      model child-month / effort-bin summaries.
      Hypothesis: the result is not driven by treating many utterance rows from
      the same child/session/month as fully independent.
- [x] **Heldout population prediction model:**
      train on PBM real children, then predict heldout children.
      Hypothesis: the model predicts unseen children's trajectory shape rather
      than only fitting children it has already seen.

### Estimator Families To Fit Or Audit

OLS alone is not enough for the pre-supervisor robustness package. For each
core formula where feasible, fit and compare these estimator families. If an
estimator is already correctly fit in an existing deep-dive artifact, audit and
reuse it rather than refitting blindly.

- [x] **OLS + child fixed effects + child-clustered robust SE.**
      Main comparable Atlas baseline. Use for fixed-effort prediction plots and
      direct comparison with existing Atlas v2 outputs.
- [x] **GEE Gaussian, clustered by child.**
      Population-average robustness model for repeated utterances within child.
- [x] **GEE Gamma/log, clustered by child.**
      Robustness model for positive, skewed information outcomes. Interpret
      coefficients on the log expected-bits scale; prediction plots are the
      clearest presentation.
- [x] **GLM Gaussian.**
      Distributional sensitivity check; secondary to OLS/GEE/MixedLM.
- [x] **GLM Gamma/log.**
      Positive-outcome sensitivity check; use prediction-scale plots.
- [x] **MixedLM random child intercept.**
      Allows each child to have their own baseline information level.
- [x] **MixedLM random child age slope.**
      Allows each child to have their own developmental trajectory. Record and
      explain convergence or singular-fit warnings.
- [x] **Age-spline / nonlinear age estimator variant.**
      Checks whether the age effect should be curved or age-bin-specific rather
      than a single linear slope.
- [x] **Month-level aggregate estimator.**
      Fits on child-month/effort-bin summaries to reduce row-level
      pseudo-replication.
- [x] **Heldout prediction estimator.**
      Must not use `C(child_id)` for unseen children unless using a valid
      population/Mundlak-compatible prediction design. Plot actual heldout
      regression lines against predicted regression lines.

### Existing Artifacts To Audit Before Refitting

- [x] Audit `docs/utterance_information_m1_m2_deep_dive.md` and
      `results/m1_m2_utterance_information_deep_dive/` for existing OLS,
      clustered OLS, GLM, GEE, and MixedLM M1/M2/M3 sensitivity fits and plots.
- [x] Audit `docs/utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html`
      and `results/route1_source_specific_corrected_fixed_effort_atlas/real/`
      for current M1-M15 formula-ladder OLS artifacts.
- [x] Audit all source-specific Atlas v2 reports and result folders for real,
      random, unigram, bigram, trigram, and LSTM k3/k4/k5 source comparisons.
- [x] Audit `docs/utterance_information_age_scrambling_robustness.html` and
      `results/age_scrambling_robustness/` for age-label scrambling and balanced
      bootstrap robustness.
- [x] Audit `docs/utterance_information_route1_heldout_real_child_prediction_report.html`
      and `results/route1_heldout_real_child_prediction/` for heldout actual vs
      predicted trajectory artifacts.
- [x] Audit `docs/utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html`
      and `results/route1_caretaker_atlas/full_fit/` for parent/caretaker
      comparison artifacts.
- [x] Record which model/formula/estimator combinations are already usable and
      which ones are missing before launching any long run.

### Required Plots Before Supervisor Report

- [x] Fixed-effort age lines for the best models, especially M2, M3, M4c, M5,
      M15/rich, nonlinear age, and month-level aggregate variants.
- [x] The same scientific question plotted across estimator families:
      OLS/fixed effects, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM
      Gamma/log, MixedLM random intercept, MixedLM random age slope.
- [x] Coefficient/effect-size forest plots across estimator families.
- [x] Variable-importance / nested delta-R2 plots, with clear warnings that
      delta-R2 is not causal importance.
- [x] Actual real-data regression line vs model-predicted line where relevant.
- [x] Heldout actual-vs-predicted trajectory plots: actual heldout line and
      PBM-trained predicted line in the same panel.
- [x] Heldout calibration and residual-over-age plots.
- [x] Age-scrambling / balanced-bootstrap null robustness plots.
- [x] Source comparison plots across real, random, unigram, bigram, trigram, and
      LSTM sources.
- [x] Caretaker/parent contrast plots using analogous fixed-effort logic.
- [x] Residual diagnostics and assumption-check plots for the candidate best
      models.

### Required Model Cards In The Candidate Report

Every candidate model shown in the report must have a model-style card with:

- [x] Model ID / short name.
- [x] Scientific question / hypothesis being tested.
- [x] Formula in readable terms and exact statsmodels-style formula where
      relevant.
- [x] Outcome variable and scale/link function.
- [x] Estimator family and library used.
- [x] Dependence handling: child fixed effects, clustered SE, GEE cluster,
      random intercepts/slopes, or aggregation unit.
- [x] Predictors and controls, including why each is present.
- [x] What the age coefficient means in one sentence.
- [x] What the effort coefficient means in one sentence.
- [x] What each interaction means in one sentence.
- [x] Whether the model is for explanation, robustness, prediction, or
      descriptive comparison.
- [x] Takeaway: what the model says if taken seriously.
- [x] Caution: assumption, convergence, interpretability, or missing-predictor
      limitation.
- [x] Saved artifacts: model summary CSV, coefficient CSV, prediction grid, and
      plot paths.

### Required One-Line Effect Sentences

For every promoted plot, add literal interpretation sentences, not generic
plot-reading instructions:

- [x] "Age down arrow" sentence: what older age means for predicted `sum_bits`
      at fixed effort in this specific model.
- [x] "Effort up arrow" sentence: what longer utterance means for predicted
      `sum_bits` in this specific model.
- [x] "Age x effort" sentence: whether the age trend changes across effort
      levels in this specific model.
- [x] "Context entropy" sentence: whether context predictability/informativeness
      adds explanatory value in this specific model.
- [x] "Question type" sentence: whether the age effect survives broad context
      form controls.
- [x] "Caretaker contrast" sentence: whether adult/caretaker speech shows the
      same child-age pattern.
- [x] "Heldout prediction" sentence: whether the predicted trajectory matches
      the actual unseen-child trajectory.

### Acceptance Checklist

- [x] The next report is explicitly labeled as a pre-supervisor candidate /
      evidence-gallery report, not the final supervisor report.
- [x] It includes the core formulas, estimator-family robustness, source
      comparisons, heldout prediction, age-scrambling robustness, and caretaker
      contrast.
- [x] It clearly distinguishes Atlas inventory from the selected "best model"
      story.
- [x] It does not imply every Atlas v2 plot is GEE/MixedLM/GLM when the source
      artifact is OLS.
- [x] It says plainly when a model is OLS, GEE, GLM, MixedLM, or aggregated.
- [x] It saves all reusable fit outputs and prediction grids.
- [x] It creates Markdown, HTML, embedded HTML, and PDF outputs.
- [x] It verifies image links and embedded images.
- [x] It runs focused tests and relevant smoke checks.
- [x] It updates `docs/notes.md` with commands, outputs, and verification.

### Immediate Route 1 Cleanup / Baseline Atlas TODOs

- [ ] Use `docs/route1_corrected_baseline_atlas_agent_prompt.md` as the launch prompt for the next long implementation run.
- [x] Add a corrected Route 1 baseline-atlas scaffold that encodes source-specific
      M1-M6 manifests, child-structure variants, parent-context effort,
      question type, source-coverage audit, and bounded smoke fitting without
      launching the full long run.
- [x] Expand the corrected atlas scaffold with internal M7-M15 model families,
      LSTM source defaults, report-plan output, launch-command output, a
      preflight stage, and per-source `fit-atlas` report stubs.
- [ ] Freeze the corrected Route 1 formula ladder: M1 `sum_bits ~ age_c + effort_c`; M2 `+ C(child_id)`; M3 `age_c * effort_c + C(child_id)`; M4a/M4b/M4c adding parent-context effort, context entropy, and question type one at a time; M5 all context controls; M6 selected context interactions with all lower-order terms kept.
- [ ] Build/audit missing parent-context predictors: `parent_context_effort_*` for k1-k3 and `question_type` for preceding caretaker context. Existing context entropy/context-size columns can be reused only after an audit confirms coverage.
- [ ] Refit the real-child Route 1 atlas with the cleaned ladder before further supervisor-facing claims.
- [ ] Repeat the full M1-M6/MX Route 1 atlas independently for each generated target source: random, unigram, bigram, trigram, and LSTM variants. Keep formulas, effort units, context windows, age bins, and robustness checks parallel across sources, and write one technical atlas report per source.
- [ ] Compare real-child and baseline trajectories side by side: age coefficients, fixed-effort age curves, context-control stability, and balanced/scrambled age robustness.
- [ ] Only after source-specific atlases exist, fit the pooled formal comparison model `sum_bits ~ target_source * age_c * effort_c + context_controls + C(child_id)` and write it as a separate downstream comparison report.
- [ ] Run child-structure sensitivity for the corrected ladder as separate variants: no child identity plus clustered SE, `C(child_id)`, GEE clustered by child, MixedLM random intercept/slope, fixed-effect within-child age, and Mundlak within/between age. Do not combine `C(child_id)` with random child intercepts, and do not estimate `child_mean_age` inside a `C(child_id)` formula.
- [ ] After the child/baseline atlas finishes, run the prepared entropy-free caretaker-target atlas using `results/route1_caretaker_atlas/preflight/CARETAKER_FULL_RUN_COMMANDS.md`.
- [ ] Keep Route 2 effort/length-outcome modeling parked until the corrected Route 1 child/baseline atlas is complete.


## List of next possible focus

These are never to be implemented at the same time, always one at a time described in the previous section :


- TODO : Fix the utterance generation script and regenerate all the utterances
- TODO : Then, score again all the utterances making sure it preserved punctuation and that sentences without any scorable-words are ignored. 
- TODO: The generation of utterances using small LLM : it will be more detailed once it'll be the `Current Focus` but the general goal is that for every dataset from CHILDES we have,
- DONE 2026-06-16: Ran the Route 2 entropy-scoring smoke from `docs/route2_entropy_scoring_script_prompt.md` using the final generation-smoke outputs. This is a feature-stability smoke, not the full Route 2 effort-outcome modeling phase.
- TODO: Increase in questions over time?
- TODO: Clarify the & markers 
- TODO: Compare with and without these
- TODO: Create a minimalist interface to easily study various utterances surprisals. It should either take a csv file with a clean utterance per row and return it with an added column with the scored surprisal for each cleaned utterance.


## Done Log

Use this for short notes after finishing tasks.

- TODO: YYYY-MM-DD - Finished X; verified with Y.
- 2026-06-18 - Built the Route 1 best-model robustness package: fitted/audited M2, M3, M4c, M5, M15, nonlinear-age, month-level aggregate, and heldout-prediction evidence; generated Markdown/HTML/embedded HTML/PDF outputs plus 18/18 required plots; verified with focused tests, compile check, report rebuild, image-link audit, embedded-image audit, and estimator-fit coverage audit.
- 2026-06-18 - Revised the Route 1 robustness package into a formula-by-formula deep dive: added no-question-type, age-by-effort, and parent-context-reaction variants; wrote interaction formulas with lower-order predictors explicitly; generated one section per formula and one subsection per estimator; verified 10 formula sections, 70 estimator subsections, 70/70 estimator fits, 28/28 plots, 22/22 embedded images, no missing image refs, and no shorthand `age_c * effort_c` formulas.
- 2026-06-18 - Expanded the formula-by-formula robustness report with the full expected plot battery: existing row-level Atlas fixed-effort plots where available, estimator-family fixed-effort plots, actual-vs-predicted regression plots, residual/calibration plots, term-effect forests, and one actual-vs-fitted/residual diagnostic per formula-estimator subsection. Verified 70/70 estimator fits, 10 formula sections, 70 estimator subsections, 70 estimator diagnostic plots, 140/140 plot-manifest entries, 127 Markdown image refs with 0 missing, and 127 embedded HTML images.
- 2026-06-18 - Simplified `docs/route1_best_model_robustness_package.md` back to the requested fixed-effort regression-line report: row-level `sum_bits` Atlas plots for M2, M3, M4c, M5, M15, and M7; heldout actual-vs-predicted regression lines; age-scrambling/source/caretaker contrast plots. Removed aggregate diagnostic plots from the main narrative and clarified that `mean_sum_bits` aggregate cells are not the primary outcome and not bits per token. Verified 13/13 image refs and 13/13 embedded HTML images; PDF render is currently unavailable because local Chrome/Brave crashes before writing the PDF.
- 2026-06-18 - Corrected the Route 1 candidate package framing to communicative efficiency rather than raw `sum_bits` growth/MLU. Regenerated `docs/route1_best_model_robustness_package.md`, `.html`, and `.embedded.html` as a focused fixed-effort regression-line gallery with promising candidates M2, M3, M4a, M4c, M5, M6, M7, M11, M15 plus exact parent-effort all-estimator screening variants. Removed raw observed-vs-fitted aggregate total-bit diagnostics from the report body. Verified compile, focused unittest, 94 Markdown image refs with 0 missing, 85/85 manifest plots available, 94 embedded images, 0 `aggregate_actual_vs_model_prediction` refs, 0 raw actual-vs-fitted refs, and 0 `mean_sum_bits` mentions.
- 2026-06-20 - Extended the child-only length-controlled model suite with exact word-count F18-F21 formulas and MLU-focused plots. Reran the real-child K3 word-effort grid: 189/189 fits, 189 saved models, 47 figures, 47/47 Markdown image refs present, and 0 occurrences of the removed course-label phrase in the regenerated Markdown/HTML report. Exact-length primary slopes were 41 downward and 7 upward, with positive slopes concentrated at length 8 and sparse lengths 10-12. Verified compile, focused unittest, report regeneration, image audit, and full suite: 313 tests passing.
- 2026-05-19 - Rewrote additive age-binned unigram/bigram/trigram dictionary building in `src/build_age_word_dicts.py`; counts now use `chi.csv` plus `caretakers.csv`, with utterance-initial child bigrams/trigrams conditioned on the most recent prior caretaker utterance.
- 2026-05-19 - Rewrote baseline generation in `src/add_random_and_unigram_utterances.py`; generation now supports random, unigram, bigram, and trigram outputs, and bigram/trigram generation uses the same caretaker-boundary context logic as counting.
- 2026-05-19 - Added trigram baseline pickup to `src/new_create_parallel_data.py`; documented the n-gram rewrite in `docs/ngram-models.md`, `docs/general-overview.md`, `docs/design.md`, and `docs/notes.md`.
- 2026-05-19 - Verified the n-gram rewrite with `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` (48 tests passing); built real 6-month dictionaries at `results/age_ngram_dicts/bin6`; generated sibling baseline files as `chi.ngram_generated.csv` for Brown, Manchester, and Providence.
- 2026-05-19 - Added experimental LSTM generator in `src/generate_lstm_utterances.py`; it uses configurable caretaker context, writes `chi.lstm_generated.csv`, and requires PyTorch for actual training/generation.
- 2026-05-19 - Updated `src/new_create_parallel_data.py` to merge generated sibling columns from n-gram and LSTM outputs and export an `lstm_chi` scoring subset when `lstm_model_utterance` exists.
- 2026-05-19 - Updated the LSTM generator with an encoder-decoder `seq2seq_lstm` architecture as the default; the encoder reads caretaker context and the decoder generates child utterances, while the earlier prefix-style LSTM remains available as `causal_lstm`.
- 2026-05-20 - Added PyTorch to the uv-managed dependencies with `uv add torch`; verified `torch==2.12.0+cu130` imports, with CUDA unavailable on this machine.
- 2026-05-20 - Re-ran the full unit-test suite after the PyTorch install: `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 61 tests.
- 2026-05-20 - Ran a bounded LSTM smoke generation on Brown using `seq2seq_lstm`, 500 training examples, and 10 generated rows per child; wrote smoke outputs under `results/lstm_generation/smoke_seq2seq_brown` and `chi.lstm_smoke_generated.csv` files for Brown children.
- 2026-05-20 - Confirmed the additive n-gram generation already includes random, unigram, bigram, and trigram columns; `random_model_utterance_bin6` is the uniform random baseline sampled from each additive bin vocabulary.
- 2026-05-20 - Added tested LSTM length modes: default `same_as_child` for matched-length controls and `free_until_eos` for model-chosen answer length; documented the comparison logic in `docs/llm-models.md` and `docs/notes.md`.
- 2026-05-20 - Verified all 21 `chi.ngram_generated.csv` files: 446,508 scorable child rows with usable `age_months` had 0 length mismatches for random, unigram, bigram, and trigram baselines; 477 scorable rows without usable age remain blank because they cannot be assigned to an additive age bin.
- 2026-05-20 - Re-ran tests after the LSTM length-mode change: `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 68 tests.
- 2026-05-20 - Ran Brown-only LSTM smoke outputs for `same_as_child` and `free_until_eos`; fixed-length smoke had 0/15 mismatches, while free-length smoke hit the configured 8-token cap in all 15 examples, so free-length results need a real training run before interpretation.
- 2026-05-20 - Fixed and regenerated n-gram sibling CSV outputs with explicit `caretaker_context_p2`, `caretaker_context_p1`, and `caretaker_context_last_two` columns so the boundary context used by bigram/trigram generation is visible.
- 2026-05-20 - Added n-gram output regression tests for p2/p1 context columns and CSV row-width alignment; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 70 tests.
- 2026-05-20 - Verified all 21 regenerated `chi.ngram_generated.csv` files parse cleanly: 519,803 rows checked, 0 row-width mismatches, 0 files missing context columns.
- 2026-05-20 - Fixed blank n-gram output metadata by filling empty `source_group` with the dataset name and enforcing sane generated-output metadata; regenerated all 21 sibling CSVs and verified 519,803 rows with 0 semantic column issues.
- 2026-05-20 - Updated future known-corpus preprocessing to fill `source_group` with the dataset name for non-Hall layouts; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 71 tests.
- 2026-05-20 - Removed `utt_id_role` from generated n-gram CSV outputs, enforced a fixed generated-output schema with no blank headers, switched writing to `csv.QUOTE_ALL`, regenerated all 21 sibling CSVs, and verified 519,803 rows with 0 header/order/row-width/speaker/line/file/source-group issues.
- 2026-05-20 - Added tests proving generated n-gram headers are exactly ordered and that `speaker`, `utterance`, and `utterance_clean` remain under the correct columns; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 72 tests.
- 2026-05-20 - Added `src/create_shared_caretaker_contexts.py` to write role-specific context files per child folder: `chi.shared_caretaker_contexts.csv` and `caretakers.shared_caretaker_contexts.csv`.
- 2026-05-20 - Generated shared caretaker-context files for Brown, Manchester, and Providence: 21 child files and 21 caretaker files; verified 519,803 child rows and 688,880 caretaker rows with 0 header/order/row-width/role/line/file/source-group issues.
- 2026-05-20 - Added tests for role-specific context outputs, including exact headers, absence of `utt_id_role`, child/generated-column alignment, caretaker-only outputs without generated columns, and k1/k2/k3 caretaker context logic; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 74 tests.
- 2026-05-20 - Added `src/utterance_count_strategies.py` with TDD-covered word, morpheme, and syllable strategies; generated `results/count_validation/utterance_count_strategy_probe.csv` with 100 real cleaned utterances for manual validation.
- 2026-05-20 - Verified the utterance-count probe output: 100 rows, 23 columns, 0 blank headers, 0 row-width issues; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 82 tests.
- 2026-05-20 - Added `src/create_minimal_surprisal_scoring_csvs.py` to export compact per-child scoring files: `chi.surprisal_scoring.csv` and `caretakers.surprisal_scoring.csv`.
- 2026-05-20 - Generated compact scoring CSVs for Brown, Manchester, and Providence: 21 child files and 21 caretaker files; verified 446,985 child rows and 668,903 caretaker rows with 0 schema/row/target/role/metadata issues.
- 2026-05-20 - Added tests for exact compact scoring schemas, dropping empty targets, and excluding noisy columns like `utt_id_role`; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 85 tests.
- 2026-05-20 - Extracted and registered MPI-EVA-Manchester; added tested filename-age fallback for blank CHI `@ID` ages; reprocessed 1,079,020 rows and wrote updated age-bin distribution outputs under `figs/utterance_distributions_with_mpi_eva_manchester/`.
- 2026-05-20 - Confirmed named corpora: Wells, Belfast, and Champaign are longitudinal; Cummings is clinical cross-sectional with some longitudinal records; Styles is not CHAT data. Extracted and preprocessed Wells, Belfast, Champaign, and Cummings; wrote expanded plots under `figs/utterance_distributions_longitudinal_named_expansion/`.
- 2026-05-20 - Made the caregiver-child naturalistic/default corpus split explicit, keeping Cummings in a separate clinical/probe group; added and preprocessed EHS as non-clinical parent-child interaction data; regenerated naturalistic-only plots under `figs/utterance_distributions_naturalistic_caregiver_child_only/`.
- 2026-05-20 - Extracted and preprocessed the available stricter naturalistic downloads: Lara, Sachs, Weist, Kuczaj, Post, Demetras1, and Forrester. `Thomas.zip` was not present in `data/zip_files`, so Thomas remains pending.
- 2026-05-20 - Added root-direct CHAT corpus discovery and Lara-specific caregiver handling for `ELS`; updated strict naturalistic defaults to exclude structured-observational Champaign/EHS and clinical Cummings.
- 2026-05-20 - Regenerated strict naturalistic 6-month child- and caretaker-utterance distributions at `figs/utterance_distributions_strict_naturalistic_parent_child/`; the child comparison table/plot are `ALL_DATASETS/previous_vs_new_strict_downloads_age_bin_counts_6m.csv` and `.png`, and the caretaker comparison table/plot use the `caretaker_` prefix.
- 2026-05-20 - Added `docs/preprocessed_datasets.md` documenting every currently preprocessed dataset, corpus grouping, Stage 0 row counts, missing-age counts, downstream generated/context/scoring readiness, and non-preprocessed pending datasets.
- 2026-05-21 - Added all-preprocessed age-bin utterance tables under `results/utterance_age_tables/`, including total child-vs-caretaker counts and per-dataset long/wide formats.
- 2026-05-21 - Added `docs/project_deep_research_handoff.md`, a comprehensive technical and scientific handoff summarizing the current project state for a deep-research agent.
- 2026-05-21 - Created PBM scoring-ready tarballs under `results/scoring_bundles/`: combined child+caretaker scoring CSVs, child-only scoring CSVs, and caretaker-only scoring CSVs.
- 2026-05-25 - Added `src/extract_child_metadata_summary.py` and `tests/test_extract_child_metadata_summary.py`; generated `results/metadata/child_metadata_summary.csv` with one row per prepared child folder, recoverable CHAT demographics, utterance counts, age coverage, and downstream scoring-readiness flags.
- 2026-05-25 - Added `src/create_big_cleaned_dataset.py` and `tests/test_create_big_cleaned_dataset.py`; generated `data/big_cleaned_dataset/default_naturalistic_bin6/` with strict naturalistic Stage 0 files, additive bin-6 n-gram dictionaries, matched-length random/unigram/bigram/trigram baselines, shared caretaker-context files, compact scoring CSVs, `manifest.csv`, and a folder README. Verified 109 tests passing and 0 CSV header/row-width issues.
- 2026-05-25 - Generated strict-naturalistic big-cleaned actual utterance distribution plots and CSVs under `figs/big_cleaned_dataset/default_naturalistic_bin6/`, plus a Providence/Brown/Manchester-only version under `figs/big_cleaned_dataset/providence_brown_manchester_bin6/`, split by child versus caretaker 6-month age bins.
- 2026-05-25 - Added custom threshold early age bins via `src/custom_age_bins.py` and wired them into n-gram dictionary building/generation. Generated `data/big_cleaned_dataset/default_naturalistic_custom_early20k/` using bins `006-019`, `020-023`, then 6-month intervals from `024-029` through `060-065`; wrote all/PBM custom-bin utterance tables and plots under `figs/big_cleaned_dataset/*custom_early20k/`. Verified 121 tests passing and 0 CSV header/row-width issues.
- 2026-05-26 - Generated `results/metadata/strict_naturalistic_custom_early20k_child_metadata_summary.csv`, a 79-row metadata file matching the current custom-bin strict-naturalistic scoring bundle.
- 2026-05-26 - Added `src/prepare_clinical_datasets.py` and `tests/test_prepare_clinical_datasets.py`; prepared 15 clinical/control dataset groups under `data/preprocessed_clinical_data/`, writing 494 child folders and metadata summaries at `results/metadata/clinical_child_metadata_summary.csv` and `results/metadata/clinical_dataset_summary.csv`. Verified clinical CSVs have 0 header/row-width issues.
- 2026-05-26 - Added `src/analyze_clinical_magnitudes.py` and `tests/test_analyze_clinical_magnitudes.py`; generated session-size comparisons, clinical/control 6-month age-bin tables, and figures under `results/clinical_magnitude_analysis/` and `figs/clinical_magnitude_analysis/`.
- 2026-05-26 - Added GPU-ready LSTM baseline orchestration in `src/run_lstm_baseline_pipeline.py` with tests in `tests/test_lstm_baseline_pipeline.py` and documentation in `docs/lstm-baseline-pipeline.md`; laptop dry run found 79 child folders and 1,140,218 usable examples without training a model.
- 2026-05-26 - Added merged-early n-gram binning via `merged_early_006_023`, regenerated `data/big_cleaned_dataset/default_naturalistic_merged_006_023/`, and verified 79 child scoring files, 79 caretaker scoring files, 1,140,218 child scoring rows, 1,470,154 caretaker scoring rows, and 0 CSV header/row-width issues.
- 2026-05-26 - Added `src/create_pbm_early_baseline_rescoring_bundle.py` and tests; generated the PBM-only `006-023` generated-baseline rescoring shards at `results/rescoring_subsets/pbm_006_023_merged_early_baselines/` plus tarball `results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_2026-05-26.tar.gz`. Verified 251,264 scorer rows across random/unigram/bigram/trigram, all floor-age 006-023, with 0 CSV issues.
- 2026-05-27 - Added `MERGE_BACK_GUIDE.md` and `replacement_keys.csv` to the PBM early rescoring bundle; created handoff tarball `results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_handoff_2026-05-27.tar.gz` with scorer shards plus explicit replacement keys. Verified 18 CSVs in the bundle with 0 blank-header or row-width issues.
- 2026-05-28 - Updated the LSTM baseline pipeline to default to `default_naturalistic_merged_006_023`, added JSON config loading, editable configured generation variants, 16GB-GPU default/smoke configs, and a supervisor-facing LSTM pipeline document. Verified with `tests.test_lstm_baseline_pipeline`, `tests.test_lstm_generation`, and the full suite: 145 tests passing. No LSTM training or generation was run on the laptop.
- 2026-05-28 - Updated `AGENTS.md` and added `docs/lstm_pc_handoff.md` so a new agent on the PC can pick up the LSTM generation work from Markdown. The handoff records the current bundle, rsync path, model description, PC commands, expected artifacts, and what to document after running.
- 2026-05-28 - Added `src/run_lstm_additive_age_context_pipeline.py` and `tests/test_lstm_additive_age_context_pipeline.py` for PBM-only additive age-bin LSTM generation across caretaker context windows. The script writes per-model batch logs, manifests, generation diagnostics, qualitative samples, and PNG/PDF plots.
- 2026-05-28 - Ran the real PBM additive same-length LSTM generation on the local RTX 4060 Ti GPU: 24 models = k3/k4/k5 times 8 additive age bins (`006-023`, then 6-month bins through `060-065`), 3 epochs each. Output: `results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length/`. Verified 21 generated files, 519,803 child rows checked, 446,508 generated rows per k column, 0 same-length mismatches, 21 scoring-with-LSTM files, and 446,985 scoring rows.
- 2026-05-29 - Added a tested PBM `006-023` generated-baseline patch workflow to `compute_surprisal_mila`, including dry-run/apply scripts for both full cleaned-data inputs and scored-result outputs. Built `results/scoring_bundles/pbm_006_023_scoring_patch_2026-05-29.tar.gz`; verified 17 child files, 62,816 rows, and 272 generated-baseline scoring tasks.
- 2026-06-01 - Added `docs/route1_from_zero_handoff_2026-06-01.md`, summarizing the scoring repo state for the Route 1 reset: audited main Mistral tree, audited LSTM additive tree, PBM patch caveat, pending entropy/KL/word-level features, and the recommended June 2 from-zero modeling sequence.
- 2026-06-02 - Added publication-oriented utterance measurement validation in `src/validate_utterance_measurement_strategies.py`, with focused tests and `docs/utterance_measurement_validation.md`. Generated a human-reviewable 50-row stratified workbook at `results/count_validation/publication_measurement_review_50.xlsx`, plus compact review CSV, token-level CSV, full audit CSV, and Markdown. The review set has short/medium/long/very-long rows, 0 duplicate cleaned utterances, 0 blank recommended syllable counts, and 0 blank recommended phoneme counts. After manual inspection caught G2P syllable undercounting for `firetruck`, changed recommended syllables to CMUdict for known words plus `syllables` package for OOV words, while keeping G2P for phonemes. Added reviewer-facing package write-up at `docs/utterance_measurement_package_writeup.md`. Verified focused tests and full suite: 153 tests passing.
- 2026-06-02 - Rewrote the LSTM baseline orchestration to support the fair additive age-bin design by default: one cumulative LSTM/vocabulary per target age bin, generation only for rows in that target bin, and `lstm_age_bin` provenance in generated/scoring outputs. Updated configs, docs, PC handoff, and AGENTS standards. Real dry-run over the strict naturalistic bundle found 79 units, 1,140,218 examples, and 8 bins with cumulative train/target counts recorded in `docs/notes.md`. No GPU training was run. Verified focused LSTM tests and full suite: 156 tests passing.
- 2026-06-02 - Added PBM-only additive LSTM config `configs/lstm_baseline_16gb_pbm_additive.json` for fair comparison against currently PBM-trained n-gram baselines. Dry-run found 21 units, 446,508 examples, and 8 additive bins; counts are recorded in `docs/notes.md`. No training was run.
- 2026-06-03 - Started the supervisor-facing utterance-information report at `docs/predicting_utterance_level_information_report.md`, using the 2026-06-03 compute-surprisal handoff as the current PBM patched Mistral source-of-truth note.
- 2026-06-03 - Added Route 1 report asset generation and HTML rendering scripts; fixed PBM age-bin coverage by recovering blank Providence/Naima `030000.cha` ages from the filename, so child and caretaker age-bin totals now match all k0 scored rows exactly. Verified full suite: 162 tests passing.
- 2026-06-03 - Reworked the utterance-information report to be supervisor-facing: removed internal "Route 1" framing, removed workflow/source-path sections, removed premature modeling questions, added communicative-efficiency framing and baseline-construction sections for random, n-gram, and LSTM comparisons. Regenerated plots with short formal titles and verified full suite: 163 tests passing.
- 2026-06-03 - Added the Providence/Naima `030000.cha` missing-baseline patch builder and scorer-side local scripts. Built `results/scoring_bundles/naima_030000_missing_baselines_scoring_patch_2026-06-03.tar.gz` with 477 rows, recovered age 36 months, and nonblank random/unigram/bigram/trigram generated utterances from the current additive `036-041` dictionaries. Copied local scorer/merge helpers into `compute_surprisal_mila`; focused tests and script syntax checks passed.
- 2026-06-03 - Updated `compute_surprisal_mila` agent workflow Markdown for the Naima patch: `AGENTS.md`, `README.md`, and `docs/naima_030000_missing_baseline_patch.md` now document exact local scoring, dry-run merge, apply-merge, and post-merge Route 1 rebuild steps.
- 2026-06-03 - Added a strict-naturalistic child demographic codebook workflow: `configs/manual_child_demographic_overrides.csv`, `src/build_child_demographic_codebook.py`, tests, and `docs/child_demographic_codebook.md`. Generated PBM and 79-child SES/race codebooks under `results/metadata/`; focused demographic-codebook tests pass.
- 2026-06-03 - Added `src/attach_context_entropy_to_route1_dataset.py` and tests to attach Mistral next-token context entropy to the long Route 1 dataset. Generated `results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz` with 11,607,680 rows and explicit join statuses. Corrected the join to reuse entropy for the same context text across k labels, matching the scorer manifest's text-level deduplication. Remaining entropy gaps are 34,141 child rows across 2,250 unique contexts listed in `missing_context_entropy_contexts.csv`.
- 2026-06-04 - Added `src/create_context_entropy_rescoring_patch.py` and tests to isolate the remaining Route 1 context-entropy gaps into a scorer-ready manifest. Built `results/scoring_bundles/route1_missing_context_entropy_patch_2026-06-04/` and `.tar.gz`: 2,250 missing-context audit rows, 2,235 unique scorer contexts after text-level deduplication, representing 34,141 Route 1 rows. Copied the handoff to `compute_surprisal_mila/new_data/route1_missing_context_entropy_patch/` plus a portable tarball in `compute_surprisal_mila/new_data/`.
- 2026-06-04 - Completed the new PBM additive LSTM training/generation run at `results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03/`: 24 model checkpoints, 446,508 generated rows per k3/k4/k5 same-length LSTM column, 0 empty generated rows, 0 same-length mismatches, and 21 scorer-ready `chi.surprisal_scoring_with_lstm_additive.csv` files. Added scoring handoff `docs/lstm_additive_pbm_compute_surprisal_handoff_2026-06-04.md` for the `compute_surprisal_mila` agent.
- 2026-06-04 - Added the separate PBM utterance-information modeling proposal packet builder `src/build_utterance_information_model_proposals.py`, with tests in `tests/test_build_utterance_information_model_proposals.py`. Generated `docs/utterance_information_model_proposals.html`, `docs/utterance_information_model_proposals.md`, `notebooks/utterance_information_model_proposals.ipynb`, summary CSVs under `results/utterance_information_model_proposals/`, and plots under `figs/utterance_information_model_proposals/`. Verified the PBM long table has 11,607,680 scored rows matching the symlinked 504-file scorer tree, with 7,632 raw unscored/blank Naima placeholder rows documented and excluded from analysis rows.
- 2026-06-04 - Revised the utterance-information modeling proposal packet to clarify that raw mean total-bits plots are descriptive and not utterance-length-controlled. Added one result plot for each of the five candidate models, including adjusted total bits at fixed word counts, adjusted bits per word by corpus, child random intercepts, random-slope pilot diagnostics, and adjusted real-vs-baseline GEE predictions. Regenerated `docs/utterance_information_model_proposals.html`; verified 196 tests passing.
- 2026-06-04 - Extended the modeling proposal packet with effort-control sensitivity and child-control ladders. The new analyses compare utterance-level total bits while controlling separately for words, morphemes, CMU/pkg syllables, pkg syllables, and phonemes; plot child real + generated baselines both with and without caretakers; and compare length+age only, child fixed effects, and GEE grouped-by-child versions for real child utterances. Regenerated `docs/utterance_information_model_proposals.html`; verified source audits still match and 196 tests pass.
- 2026-06-08 - Extended the internal utterance-information deep dive with M3 age-by-effort interaction models, keeping effort measures separated. The report now defines OLS, child-clustered SE, GLM, Gamma/log link, GEE, mixed models, and fixed-median prediction lines; each model-family subsection includes its question, controls/structure, and coefficient interpretation. Regenerated `docs/utterance_information_m1_m2_deep_dive.html`; verified full suite: 212 tests passing.
- 2026-06-08 - Added `src/build_route1_model_report_suite.py` and tests to generate two new internal analysis reports: an extended M1/M2/M3 interpretation report and a broader research-question model zoo. The model zoo derives context length, question type, context entropy/certainty, fallback-quality flags, and row-matched real-minus-baseline deltas; it fit 11 candidate models with all statuses `fit`. Generated `docs/utterance_information_m123_extended.html` and `docs/utterance_information_research_model_zoo.html`; verified full suite: 216 tests passing.
- 2026-06-08 - Reworked `docs/utterance_information_research_model_zoo.html` into an explicit internal comparison report organized around child-vs-random, child-vs-unigram, child-vs-bigram, child-vs-trigram, child-vs-caretaker, and context-predictability/effort questions. Added full age-bin aggregate baseline/role trajectories, one dashboard per pairwise comparison, explicit comparison-model CSVs, and regenerated the report. Verified focused tests and full suite: 217 tests passing.
- 2026-06-08 - Reworked `docs/utterance_information_m1_m2_deep_dive.html` into a clearer M1-M4 model-ladder report. M1, M2, M3, and M4 now each have a question, formula, plot-reading guide, compact primary table, sensitivity snapshot, and takeaway. Added M4 context-entropy models, tables, and plots for effort/information outcomes using next-token entropy as a provisional context-predictability measure. Regenerated the report and verified full suite: 218 tests passing.
- 2026-06-08 - Reworked the expanded internal model-atlas report so every plotted figure is paired with a nearby "How to read this plot" explanation. Added structured Z1-Z11 model cards with question, formula, reason for inclusion, compact result, plot, and key coefficients; added tests for model-card guide coverage and card-plot generation. Regenerated `docs/utterance_information_research_model_zoo.html`; verified 24 image references and 24 plot-reading explanations, 11 Z-cards, and full suite: 220 tests passing.
- 2026-06-08 - Corrected the internal modeling reports after review: M4 is now the direct information model `sum_bits ~ age + effort + context_entropy + child identity`, repeated across effort controls and sensitivity families. Added M5 all-main-effects and M6 interaction-rich saturated exploratory models, with explicit warnings about multicollinearity and uneven child age coverage. Updated the model zoo so child-vs-baseline and child-vs-caretaker comparisons are repeated across words, morphemes, both syllable measures, and phonemes; generated 45 effort-controlled comparison models and two overview plots. Regenerated `docs/utterance_information_m1_m2_deep_dive.html` and `docs/utterance_information_research_model_zoo.html`; verified full suite: 221 tests passing.
- 2026-06-08 - Split the internal modeling report workflow into explicit `analysis` and `report` stages for both `src/build_m1_m2_utterance_information_deep_dive.py` and `src/build_route1_model_report_suite.py`. Use `--stage report` to rebuild Markdown/HTML from existing model tables and figures without refitting models; use `--stage analysis` only when the data, formulas, predictors, or fitted-result plots changed. Verified report-only rebuilds and full suite: 222 tests passing.
- 2026-06-08 - Reworked the M1-M6 internal report to reduce table dumping and make each model section self-contained with a question, formula, plot-reading explanation, one compact result table, and explicit table-column explanations. Replaced the previous all-continuous-effort M5/M6 stress tests with effort-separated low/mid/high effort-level models: M5 uses `sum_bits ~ age + context_entropy + C(effort_level) + C(child_id)`, and M6 adds age/context/effort-level interactions. Added a targeted `--stage m5m6` rebuild so effort-level models can be refit without rerunning the whole packet. Verified focused tests and full suite: 224 tests passing.
- 2026-06-08 - Tightened the M1-M6 internal report structure so every real model subvariant is visible in its own subsection, while alternate line plots are labeled as diagnostic views rather than new models. M1-M3 now expose their OLS/GLM/GEE/mixed/fixed-effect subvariants with compact tables and per-subvariant regression-line figures; M4 now writes separate M4a-M4e context-entropy prediction plots; M5/M6 list the effort-source subvariants separately from the low/mid/high diagnostic plots. Regenerated `docs/utterance_information_m1_m2_deep_dive.html`; verified focused tests and full suite: 225 tests passing.
- 2026-06-08 - Corrected the M1-M3 subvariant plots so covariance-only variants are visually interpretable: OLS and child-clustered OLS now correctly show the same fitted mean line but different model-based 95% confidence ribbons. Added `--stage expanded_plots`, CI columns in `expanded_adjusted_age_predictions.csv`, report text explaining why clustered-SE lines can be identical, and tests guarding this behavior. Regenerated `docs/utterance_information_m1_m2_deep_dive.html`; verified full suite: 226 tests passing.
- 2026-06-08 - Rebuilt the expanded research model zoo with the same family/subvariant logic as the M1-M6 report. Z1-Z11 now fit effort-separated variants instead of combining highly collinear effort measures, write `zoo_model_variant_manifest.csv`, generate family-level coefficient plots, and render subvariant sections with question/formula/estimator/table/coefficients. Added `--stage extract`, `--stage model`, and `--stage report` so extraction, fitting/plotting, and HTML rendering are decoupled. Regenerated `docs/utterance_information_research_model_zoo.html`; verified focused tests and full suite: 226 tests passing.
- 2026-06-09 - Added a compact shareable M1-M6 report renderer `src/build_m1_m6_quick_share_report.py`. It reads existing M1-M6 tables/figures without refitting and writes `docs/utterance_information_m1_m6_quick_share.md` and `.html` with one short section per model, best plots, formulas, how-to-read notes, and quick takeaways. Added focused tests in `tests/test_build_m1_m6_quick_share_report.py`.
- 2026-06-09 - Reworked the compact M1-M6 quick-share workflow into an explicit dual-effort analysis/report split. Added `src/fit_m1_m6_dual_effort_quick_models.py` to fit M1-M6 with both continuous effort controls and low/mid/high effort-level controls, writing 60 fitted rows and six two-row strategy plots. Updated the quick-share renderer to read only those saved artifacts and regenerated `docs/utterance_information_m1_m6_quick_share.html`.
- 2026-06-09 - Added `src/build_m1_m6_results_interpretation_report.py` and `tests/test_build_m1_m6_results_interpretation_report.py` to render a separate narrative interpretation document from the saved dual-effort M1-M6 outputs. Generated `docs/utterance_information_m1_m6_results_interpretation.md` and `.html`; the report summarizes takeaways, model-by-model results, scientific interpretation, limits of next-token context entropy, and next analyses. Verified focused tests and full suite: 231 tests passing.
- 2026-06-09 - Replaced the insufficient median-only continuous-effort visualization with distribution-audited fixed effort slices and marginal adjusted global trends. Added `src/build_effort_slice_audit_report.py`, `src/fit_m1_m6_fixed_effort_slice_models.py`, and `tests/test_effort_slice_audit_and_fixed_models.py`; generated `docs/utterance_effort_slice_audit.html` and `docs/utterance_information_m1_m6_fixed_effort_slices.html`. The fixed-slice workflow separates `--stage analysis` from `--stage report`, stores all predictions in CSV, and caps plotted dense slices to keep figures readable.
- 2026-06-09 - Added the exhaustive fixed-effort M1-M6 atlas in `src/build_m1_m6_fixed_effort_atlas_report.py` with tests in `tests/test_build_m1_m6_fixed_effort_atlas_report.py`. Regenerated the effort audit and fixed-slice model outputs with top-12 representative exact effort values, then wrote `docs/utterance_information_m1_m6_fixed_effort_atlas.html`. The atlas includes 1-4/5-8/9-12 word and morpheme panels, representative syllable/phoneme panels, coefficient tables, variance-explained summaries, predictor-significance summaries, fixed-slice slope tables, row-support plots, shaded model-confidence bands, and final research-question takeaways. Verified full suite: 238 tests passing.
- 2026-06-09 - Reworked the context-predictor permutation builder after an aborted high-memory run. The script now processes `k0`-`k3` one context window at a time, maps context-count checkpoint rows instead of doing a heavy merge, writes per-`k` measured-row files plus a manifest instead of one giant measured table, and extracts statsmodels fit summaries immediately instead of keeping heavy result objects in memory. Real full run completed in 12:35 with peak RSS 2,522,520 KB; wrote 27 figures, 240 model rows, and 185 fitted rows. The 55 skipped rows are the impossible `k0` context-predictor models. Rendered `docs/utterance_information_context_predictors_k0.html`, `k1.html`, `k2.html`, `k3.html`, and `k_comparison.html`. Verified with `MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_context_predictor_permutation_reports` (3 tests passing).
- 2026-06-09 - Added the missing context-predictor fixed-effort atlas in `src/build_context_fixed_effort_atlas_report.py`. It repeats the fixed-slice logic for all context windows and context model families: words/morphemes use exact 1-4, 5-8, and 9-12 panels; syllables/phonemes use the top 12 observed exact values split into three ordered representative groups. Real run completed in 3:58 with peak RSS 1,476,432 KB; wrote 80 model rows, 65 fitted rows, 54,600 prediction rows, 65 figures, and `docs/utterance_information_context_fixed_effort_atlas.html`. The 15 skipped rows are the impossible `k0` context-predictor rows. Verified with focused context tests: 5 tests passing.
- 2026-06-09 - Added the exhaustive M1-M6 context fixed-effort atlas in `src/build_context_m1_m6_fixed_effort_atlas_report.py`. It repeats the full M1-M6 ladder across `k0`-`k3`, with M4-M6 split into entropy-only, matched context-size-only, and entropy+size variants, and includes exact fixed-effort panels for every effort unit. Real run completed in 11:24 with peak RSS 1,690,664 KB; wrote 240 model rows, 195 fitted rows, 140,400 prediction rows, 195 figures, and `docs/utterance_information_context_m1_m6_fixed_effort_atlas.html`. The 45 skipped rows are the impossible `k0` context variants for M4-M6. Verified with focused context tests: 7 tests passing.
- 2026-06-15 - Added `docs/deepthink_response_entropy_temperature_handoff.md`, a standalone Markdown handoff for evaluating response-space context entropy design. It summarizes the 2026-06-04 supervisor transcript, distinguishes sampled full-response entropy from current next-token context entropy, documents model/temperature/prompt/stopping/sample-size options, and frames the questions to ask ChatGPT DeepThink before running a production sampling job.
- 2026-06-15 - Added `docs/paper_summary_pawar_cychosz_2025_frequency_informativity.md`, a future-agent paper summary for `papers/Frequency and informativity.pdf`. It documents the CHILDES caregiver-speech phonological informativity design, the 81,000-phone/100-bootstrap-samples-per-age-bin method, the two age-label scrambling controls, and concrete ways to adapt their stability and scrambling logic for response-space entropy and Route 1 developmental analyses.
- 2026-06-15 - Added `src/build_age_scrambling_robustness_report.py` and `tests/test_build_age_scrambling_robustness_report.py` for Pawar-style Route 1 robustness checks on real child utterances. The default workflow now streams the split PBM scored-result tree file by file, recomputes effort, attaches compact context-entropy features, aggregates to a 3,932-row child-session-context unit frame, and then runs balanced bootstrap plus age-label scrambling controls. Generated `docs/utterance_information_age_scrambling_robustness.html` with 105 observed M1-M6 fits and 42,000 replicate fits. Added `--source unit-frame` so future refits can reuse `results/age_scrambling_robustness/age_scrambling_unit_frame.csv.gz` without rereading scored files.
- 2026-06-15 - Reworked `docs/utterance_information_age_scrambling_robustness.html` from a diagnostic-heavy table dump into a clearer model-card report. Each M1-M6 section now includes a question, formula, plain-language robustness test, regression-line plot with balanced-bootstrap and age-scrambled null ribbons, a quick read, and one compact result table with column explanations.
- 2026-06-15 - Added the publication-oriented response-space entropy pilot framework in `src/build_response_entropy_pilot_grid.py`, with config `configs/response_entropy_pilot_grid.json` and tests in `tests/test_build_response_entropy_pilot_grid.py`. The manifest stage streams the split PBM scored tree, selects 20 unique contexts per age-bin/context-window stratum, deduplicates to 480 generation contexts, and writes `docs/response_entropy_pilot_grid_design.html`. Updated `src/sample_context_responses.py` to record `top_k`, raw generated text, max-token hits, speaker-boundary stops, and empty-response flags. The diagnostics stage computes quality rates, split-half reliability, downsample stability, and temperature rank correlations after GPU generation.
- 2026-06-15 - Hardened `src/sample_context_responses.py` after the first PC launch attempt: default model loading now uses the shared Hugging Face cache instead of creating a project-local `results/.../model_cache`, sampled rows are appended incrementally for resumability, and `--batch-samples` microbatches the 100 samples per context to avoid 16GB VRAM overload. Cleaned the incomplete duplicate PC cache at `results/response_level_context_entropy/model_cache` while preserving the complete shared cache under `~/.cache/huggingface/hub/models--mistralai--Mistral-7B-v0.3`. Tested `--batch-samples 16` on the longest pilot context, discarded the 600-row partial `batch-samples 4` output for clean provenance, and restarted the full pilot on the PC as PID 9701 with `--batch-samples 16`.
- 2026-06-15 - Added a completion audit to `src/build_response_entropy_pilot_grid.py` after diagnostics were accidentally run on a partial PC sample file. Final diagnostics now compare the sample file against the generation manifest, expected temperatures, and samples per context, then refuse to render unless every context-temperature pair is complete. Use `--allow-incomplete-diagnostics` only for explicit debug reports.
- 2026-06-15 - Added `docs/response_entropy_mila_generation_plan.md`, a Mila handoff for response-space entropy generation. It explains why the PC pilot is useful but too slow for production, recommends Slurm array sharding by `temperature x context-shard`, documents shared Hugging Face cache rules, gives a one-shard command template, and records the stop condition: finish pilot diagnostics and get user approval before launching any production-scale generation.
- 2026-06-15 - Minimally extended the supervisor-facing utterance-information report with the current M1-M3 smoking-gun results: formulas, `statsmodels` OLS + child-cluster robust SE description, compact coefficient table, fixed-effort slice summary, and balanced/scrambled age-check interpretation. Regenerated `docs/predicting_utterance_level_information_report.html` and `.embedded.html`; PDF export did not update and remains older.
- 2026-06-15 - Revised the supervisor-facing M1-M3 section after review: removed the confusing dual-effort low/mid/high figures, removed the coefficient table from the supervisor draft, and replaced the main visual evidence with exact fixed-effort slice plots for M1 and M2. Follow-up TODO: reintroduce a technical/statistical appendix later that explains the removed coefficient information more clearly: age coefficient = bits/month after controls, effort coefficient = bits per additional effort unit, age-by-effort coefficient = whether the effort slope changes with age, and R2 = observed-vs-fitted variance explained.
- 2026-06-15 - Clarified the supervisor-facing statistical-methods wording: M1-M3 are OLS/linear regression models with child-clustered robust SE; M2/M3 use child fixed effects; predictors are theory-driven rather than automatically selected; internal sensitivity work includes GEE/GLM/mixed-effect variants. Restored fixed-effort plots directly under M1, M2, and M3.
- 2026-06-15 - Rechecked the Advanced Data Analytics course notes on correlated data, regularization, and model selection before revising the supervisor report again. Updated the M1-M3 section to make clear that OLS is the transparent first-pass model, while GEE, GLM/Gamma, and mixed-effect models are sensitivity/appendix families; clarified that child identity is an adjustment for unbalanced longitudinal coverage, not the substantive finding. Added M1, M2, and M3 balanced/scrambled interval plots plus the three balanced/scrambled regression-line diagnostics to the supervisor-facing report. Regenerated local and embedded HTML; PDF remains older.
- 2026-06-16 - Completed the PC response-space entropy pilot generation after resuming the interrupted temperature-1.6 tail. The clean usable sample file is `results/response_entropy_pilot_grid/pilot_response_samples_clean.csv.gz`: 288,000 rows = 480 contexts x 6 temperatures x 100 samples, with 2,880/2,880 complete context-temperature pairs. Rendered `docs/response_entropy_pilot_grid_diagnostics.html` and copied the completed results/figures back to the laptop. Hardened the sampler CSV writer/resume scanner and added focused tests.
- 2026-06-16 - Rebuilt the supervisor-facing utterance-information report around Model 2 as the primary result. Filled the previous model TODO section with M2 coefficients, fixed-effort plots, matching k3 balanced/scrambled robustness results, interpretation, and next steps. Regenerated `docs/predicting_utterance_level_information_report.html` and `.embedded.html` with 9 embedded images.
- 2026-06-16 - Ran Route 2 response-generation stopping probes on the PC. The first probe exposed a left-padding prompt-slicing bug and is not scientifically usable; corrected probes show Mistral does not emit EOS naturally, but free child-turn sampling with first-newline/speaker-boundary trimming and a 48-token safety cap captures a boundary in 98.5% of T=0.5 samples and 99.5% of T=0.7 samples. Added `src/build_response_entropy_stopping_probe.py`, `scripts/run_response_entropy_stopping_probe_pc.sh`, sampler fixes, tests, and local reports `docs/response_entropy_stopping_probe_v2.html` and `docs/response_entropy_stopping_probe_v3.html`.
- 2026-06-16 - Added the exhaustive internal M1-M6 super-atlas renderer in `src/build_m1_m6_super_atlas_report.py`, with focused tests in `tests/test_build_m1_m6_super_atlas_report.py`. Generated `docs/utterance_information_m1_m6_super_atlas.md` and `.html`, plus overview figures under `figs/m1_m6_super_atlas/` and inventories under `results/m1_m6_super_atlas/`. The report pulls together 19 CSV artifacts, 413 existing PNG source figures, 11 new cross-atlas overview figures, model-by-model estimator/library/random-effect descriptions, caveats, takeaways, context variants, fixed-effort slices, and age-scrambling robustness tables. Verified focused tests, full suite (`260` tests), and 437 Markdown image references with 0 missing files.
- 2026-06-16 - Saved the recent communicative-efficiency email context verbatim at `docs/project_motivation_recent_email_context_2026-06-16.md`; added `src/build_m1_m6_interpreted_atlas_report.py` and `tests/test_build_m1_m6_interpreted_atlas_report.py`; generated `docs/utterance_information_m1_m6_super_atlas_v2_interpreted.md`/`.html` and `docs/utterance_information_m1_m6_technical_implementation_companion.md`/`.html`. The v2 atlas quotes the email exactly, explains Route 1 versus Route 2, interprets M1-M6, and treats new length-prediction models as proposed rather than fit. Verified focused tests, full suite (`261` tests), and 415 interpreted-atlas image references with 0 missing files.
- 2026-06-16 - Clarified the Route 1 modeling plan after review: documented the distinction between `C(child_id)`, `(1 | child_id)`, and child-clustered SE; clarified formula hierarchy for interactions; parked Route 2 for now; and updated the interpreted atlas/technical companion with the plan to repeat the full M1-M6 atlas independently for each random/ngram/LSTM baseline before fitting a pooled `target_source * age_c * effort_c` comparison. Verified the interpreted-atlas focused test and regenerated the reports with 415 image references and 0 missing links.
- 2026-06-16 - Added `docs/route1_corrected_baseline_atlas_agent_prompt.md`, an agent-facing launch prompt for the long corrected Route 1 rebuild. It defines the child-structure variants to compare separately, the corrected M1-M6 formulas, baseline-source atlas logic, implementation phases, deliverables, and acceptance checklist.
- 2026-06-16 - Ran the cap-96 extreme-temperature Route 2 smoke on the PC for T=0.3, T=1.3, and T=1.6: 40 contexts x 3 temperatures x 10 samples = 1,200 samples. Results show T=0.3 reached a newline in all samples, but T=1.3 still missed newline before cap in 20.0% and T=1.6 missed in 62.75%; hard-bad automatic quality rates were 3.0%, 28.75%, and 70.5% respectively. Rendered the meeting-facing piloting report `docs/response_entropy_route2_piloting_report.html`.
- 2026-06-16 - Added two future-agent Route 2 prompts: `docs/route2_final_generation_smoke_prompt.md` for the final pre-Slurm generation smoke at temperatures 0.3/0.5/0.7/1.0, and `docs/route2_entropy_scoring_script_prompt.md` for the downstream entropy feature/scoring script that consumes generated samples and builds Route 2 predictors.
- 2026-06-16 - Implemented and ran the final Route 2 pre-Slurm generation smoke on the PC with true end-of-turn stopping, accepted/rejected attempt logging, deterministic quality flags, prompt-variant checks, and temperatures 0.3/0.5/0.7/1.0. Output: `docs/response_entropy_final_generation_smoke.html`, `results/response_entropy_final_generation_smoke/`, and `figs/response_entropy_final_generation_smoke/`. The run wrote 9,512 accepted responses from 10,203 attempts across 40 contexts x 3 prompt variants x 4 temperatures, with 473/480 settings reaching 20 accepted samples before the 60-attempt cap.
- 2026-06-16 - Updated the Route 2 handoff Markdown after the final generation smoke so the next step points to `docs/route2_entropy_scoring_script_prompt.md` and uses the existing final-smoke artifacts rather than regenerating samples.
- 2026-06-16 - Added `src/build_response_entropy_final_scoring_smoke.py` and ran the Route 2 final entropy-scoring smoke locally. Outputs: `docs/response_entropy_final_scoring_smoke.md`/`.html`, ignored CSVs under `results/response_entropy_final_scoring_smoke/`, and ignored plots under `figs/response_entropy_final_scoring_smoke/`. The smoke wrote 480 context-prompt-temperature feature rows, 478 finite entropy rows, 480 stability rows, 7 incomplete-setting audit rows, 6,228 joined Route 2 smoke rows, and tiny non-scientific sanity model summaries. Verified focused tests and full suite: 286 tests passing.
- 2026-06-16 - Generated current-scored real-child coverage plots for the PBM scored universe: 21 Brown/Manchester/Providence children, 446,508 scored real-child rows, ages 11.133-62.4 months, and 52 covered integer months. The smallest current-scored month-cover set is Providence/Naima, Brown/Sarah, and Brown/Adam. Outputs are under `figs/route1_current_scored_coverage/` and `results/route1_current_scored_coverage/`.
- 2026-06-16 - Added tighter same-axis coverage comparison plots for candidate selection: proposed heldout children/unions, the current scored 3-child cover set, Brown/Manchester/Providence scored dataset-union rows, and the all-PBM scored union. Main output: `figs/route1_current_scored_coverage/scored_pbm_vs_proposed_sets_row_coverage.png`.
- 2026-06-16 - Added and tested `src/create_heldout_real_child_scoring_bundle.py` for the three-child heldout generalization scoring handoff. Built `results/scoring_bundles/heldout_real_child_generalization_2026-06-16.tar.gz` with Forrester/Ella, Sachs/Naomi, and MPI-EVA-Manchester/Helen real-child scoring CSVs only: 177,600 rows, 0 blank targets, 12 expected Mistral tasks across k0-k3. Rsynced the tarball and PC prompt to `compute_surprisal_mila/new_data/`; remote dry run on the PC built the 12-task manifest successfully.
- 2026-06-16 - Added the entropy-free caretaker-target Route 1 atlas prep/fitting scaffold in `src/build_route1_caretaker_atlas.py` with tests in `tests/test_build_route1_caretaker_atlas.py`. Ran a dyad-balanced real-data smoke fit for k1-k3 (`18/18` model rows fit), full caretaker preflight audit for k0-k3, and the full unit suite (`295` tests passing). Full caretaker fitting is prepared but not launched.
- 2026-06-17 - Completed the Route 1 source-specific corrected fixed-effort Atlas v2 suite and the caretaker/parent atlas. Source-specific child/baseline/LSTM groups now have independent Markdown/HTML/PDF reports for real, random, unigram, bigram, trigram, and LSTM k3/k4/k5, each backed by saved M1-M15 model summaries, coefficient-long tables, fixed-effort prediction grids, slope summaries, and PNG/PDF plot files. Real-child report also includes available estimator-family sensitivity and age-scrambling robustness sections. The caretaker atlas was fully fit for k0-k3 with 140 model rows, 120 fitted rows, and 120 plot panels. Verified 0 missing Markdown image links and full suite: 295 tests passing.
- 2026-06-17 - Repaired the Atlas v2 consultation layer after the first HTML pass showed broken plots and table-heavy bodies. Regenerated source-specific and caretaker Markdown/HTML reports with report-relative figure links, model-card-first sections, formula/library/regression explanations, and table-heavy material kept as saved CSV artifacts. Refreshed all Atlas v2 PDFs from the fixed HTML. Verified 2,230 HTML image refs with 0 missing files, headless browser screenshots for real and caretaker reports with visible plots, `py_compile`, and `tests.test_build_route1_caretaker_atlas`.
- 2026-06-17 - Fixed Route 1 Atlas v2 report consultation format and image loading. Reports now use model-card sections with formulas/OLS/statsmodels/uncertainty/outcome before plots, image links resolve correctly from `docs/`, and `.embedded.html` self-contained copies were generated for all source-specific and caretaker reports. Embedded audit: 2,230/2,230 images embedded, 0 external image refs.
- 2026-06-17 - Built the heldout real-child trajectory prediction report for Forrester/Ella, Sachs/Naomi, and MPI-EVA-Manchester/Helen. The new builder refits PBM-trained heldout-compatible OLS population and Mundlak models, produces the improved PBM-corpus-versus-heldout coverage plot, actual-vs-predicted trajectories, fixed-effort checks, Markdown/HTML/embedded HTML/PDF reports, and saved prediction CSV artifacts. Verification: 60 fits, 4 expected k0 context skips, 10 image refs with 0 missing, embedded HTML with 10/10 data images, visible headless-browser screenshot, and `py_compile` passing.
- 2026-06-17 - Built `docs/communicative_efficiency_supervisor_candidate_report_v0.{md,html,embedded.html,pdf}` as a selective supervisor-candidate synthesis. It links the current M1-M15 model cards, states line meanings explicitly, adds source-specific fixed-effort slope comparison, model-ladder R2/Delta-R2 importance, one-line effect cards, heldout actual-vs-predicted regression-line panels, calibration/residual checks, and PBM real-k3 predictor correlations. Verification: builder compiles, 6 image refs with 0 missing, embedded HTML has 6/6 data images, visible headless-browser screenshot, and PDF refreshed.
- 2026-06-18 - Strengthened `docs/communicative_efficiency_supervisor_candidate_report_v0.{md,html,embedded.html,pdf}` with explicit figure guides for every promoted figure: what the figure shows, how to read it, what it means for the Route 1 claim, and what not to overclaim. Added focused tests for the figure-guide layer and regenerated all report formats. Verification: focused unittest passed; `py_compile` passed; 6 Markdown image refs with 0 missing; embedded HTML has 6/6 data images and 0 external PNG refs.
- 2026-06-22 - Added the Route 1 real-vs-controls context report at `docs/route1_real_vs_controls_context_report.html`/`.embedded.html` and linked it from `docs/route1_current_reports_browser_index.html`. The report contrasts real children with random, unigram, bigram, trigram, LSTM k3/k4/k5, and caretaker speech using k0/k3 trajectories, with-context trajectories, context-gain trajectories, source-minus-real gaps, paired/control difference models, and illustrative examples. Added focused tests for paired-gap math, example selection, and report-relative figure links.
- 2026-06-22 update - Expanded the real-vs-controls report with model-based fixed-effort regression-line evidence from the saved corrected Atlas artifacts: M2/CM2 k3 lines at 2, 6, and 10 words, model-predicted source-minus-real line gaps, and slope-difference plots/tables across M2, M3, M4c, M5, M6, M7, M11, and M15 where available. The report now explicitly states the fixed-effort developmental trend, including the real-child downward slopes and which controls are flatter/upward.
- 2026-06-22 update - Added a separate proposed completion draft beside the current supervisor-facing report: `docs/predicting_utterance_level_information_report_proposed_completion.{md,html,embedded.html}`. The current `docs/predicting_utterance_level_information_report.*` files were left unchanged. The side draft inserts candidate real-vs-baseline/caretaker synthesis, fixed-effort slope tables, and promoted figures for manual reworking.
- 2026-06-23 status: added a separate word-level alternative model discussion
  report in `docs/predicting_word_level_information_alternative_report.md` and
  rendered `.html`. This side report does not modify the active supervisor
  report. It keeps the first-report boundary clear: Route 1 should focus on
  utterance-level `sum_bits` at fixed production effort, while the word-level
  follow-up should discuss form cost, contextual word informativity,
  same-word developmental models, word-level context gain, and a guarded
  utterance-level lexical-profile extension.
- 2026-06-23 status: fit the supervisor-facing union context Model 4 for real
  child k3 utterance-level `sum_bits`: `age + effort + age:effort + parent
  context effort + context entropy + child identity`, with no question-type
  predictor. Added `src/build_supervisor_union_context_model.py`, generated
  summaries under `results/supervisor_union_context_model/`, regenerated clean
  fixed-effort plots under `figs/supervisor_union_context_model/`, and updated
  `docs/predicting_utterance_level_information_report.{md,html,embedded.html}`.
  The word-count model keeps the age effect negative (`-0.122` bits/month,
  `p < .001`, `R2 = 0.627`) while both context predictors have independent
  negative associations. Focused test and syntax checks passed.
- 2026-06-23 status: added a separate two-candidate decision report for the
  possible final supervisor model: context-as-mechanism versus real-children-
  versus-baselines. Outputs are
  `docs/two_final_model_candidates_report.{md,html,embedded.html}`. This side
  report does not modify the active supervisor-facing report.
- 2026-06-23 update: expanded the two-candidate side report with a plain
  explanation of size control, exact-length/MLU-proof models, repeated-measures
  estimator choices, already-fit GEE/GLM/MixedLM sensitivity plots, and the
  no-question `F27` context-mechanism estimator screen.
- 2026-06-23 update: added fixed-word estimator-panel counterparts to the
  two-candidate side report, using the same supervisor-facing plot logic at 2,
  6, and 10 words. New files:
  `src/build_two_final_model_candidate_estimator_plots.py`,
  `tests/test_build_two_final_model_candidate_estimator_plots.py`,
  `figs/two_final_model_candidates_report/`, and
  `results/two_final_model_candidates_report/`. Regenerated
  `docs/two_final_model_candidates_report.{html,embedded.html}` and verified
  the focused test plus 0 missing Markdown image links.
- 2026-06-23 update: corrected the estimator-sensitivity question by fitting
  exactly the four current supervisor formulas M1-M4, rather than mixing in
  F19/F21 exact-length formulas or the F10 question-type context analogue.
  Added `src/build_supervisor_formula_estimator_sensitivity.py`,
  `tests/test_build_supervisor_formula_estimator_sensitivity.py`,
  `docs/supervisor_formula_estimator_sensitivity_report.{md,html,embedded.html}`,
  `results/supervisor_formula_estimator_sensitivity/`, and
  `figs/supervisor_formula_estimator_sensitivity/`. Final version excludes
  session-ID predictors/grouping/random intercepts and uses row-level or
  child-age-word-cell estimators only. All 20 fits completed; focused test
  passed; image audit found 0 missing links.
