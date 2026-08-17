# August Supervisor Report Workflow Contract

## Objective

Build a new August 2026 supervisor package that integrates the current
longitudinal, word-level, response-space, corrected-Bayes, onset, trajectory,
and Hall evidence without modifying or pretending to complete missing
analyses. The package has a concise landing page, one integrated scientific
report, and links to audited technical companions.

The tracked primary products are:

```text
docs/august_supervisor_index.html
docs/august_supervisor_report.md
docs/august_supervisor_report.html
```

Any image-embedded sharing bundle belongs under ignored
`results/august_supervisor_report/`, not in Git.

## Non-negotiable architecture

```text
audited upstream artifacts
        -> frozen evidence specification
        -> datasets and model-results registries
        -> deterministic scientific synthesis tables
        -> supervisor plots
        -> integrated report
        -> landing page
        -> independent red-team audit
        -> remediation and fresh re-audit when needed
        -> final integration marker
```

The reporting workflow never fits models. The term **model-results stage**
means extracting already-fitted coefficients, contrasts, formulas, uncertainty
methods, warnings, and provenance from hash-locked audited artifacts. Missing
evidence is a blocker, not permission to fit or select a new model.

If the evidence-freeze stage identifies a genuinely necessary new estimand, it
must record it as `PENDING_NEW_ANALYSIS`. A separate user-approved,
preregistered fitting workflow must produce and audit that result before a
later version of this report can consume it.

## Stage contracts

### 00 Bootstrap

- Start from a clean, current `main` containing this workflow.
- Create `agent/august-supervisor-report-v1`.
- Record the starting main SHA and verify the workflow-documentation tests.
- Do not change scientific or report files.

### 01 Evidence freeze

- Inventory only declared audited artifacts.
- Freeze promoted claim IDs, page membership, exclusions, blockers, and
  interpretation rules in `configs/august_supervisor_report_v1.json`.
- Every claim records source path and SHA-256, audit marker, sample role,
  scorer, estimand, formula/contrast, row/child/session/corpus counts where
  available, estimate, interval and uncertainty method, evidence status, and
  limitation.
- No plotting, prose rendering, or fitting.

### 02 Contracts

- Implement versioned schemas, atomic manifest helpers, input-hash checks, and
  tiny fixtures.
- Demonstrate stage isolation and failure on missing, duplicate, ambiguous, or
  changed evidence.
- Commit passing contract tests; do not commit a permanently failing suite.

### 03 Extract results

- Read canonical saved tables and their PASS/COMPLETE markers, not prose.
- Produce compact registries under ignored `results/august_supervisor_report/`:
  `sample_registry.csv`, `effect_registry.csv`, `model_inventory.csv`,
  `declared_blockers.csv`, and `model_results_manifest.json`.
- Preserve source hashes and prove upstream files were not changed.
- Do not import or execute model-fitting libraries.

### 04 Scientific synthesis

- Read only the frozen configuration and compact registries.
- Produce `headline_findings.csv`, `supporting_findings.csv`,
  `coverage_and_limitations.csv`, `page_registry.csv`, and
  `synthesis_manifest.json`.
- Classifications are deterministic: `SUPPORTED`, `QUALIFIED`, `CONTRARY`,
  `DESCRIPTIVE`, or `PENDING`.
- Do not plot, fit, or write the final narrative.

### 05 Supervisor plots

- Read only compact registries and declared prediction/plot-data tables.
- Generate a small, frozen figure set plus one plot-data CSV per figure.
- Record claim IDs, captions, alt text, dimensions, hashes, and scientific
  roles in `figure_manifest.csv` and `plot_manifest.json`.
- Do not smooth, bootstrap, regress, or read raw scored trees.

### 06 Integrated report

- Retrieve every number by claim ID.
- Read only synthesis and figure manifests.
- Write supervisor-facing prose without internal labels such as “Route 1” or
  “Route 2” in the visible narrative.
- Render Markdown and lightweight HTML through the shared renderer.
- Do not fit models or create plots.

### 07 Landing page

- Build `docs/august_supervisor_index.html` from `page_registry.csv`.
- Link the integrated report, direct-results explorer, word comparison, Hall,
  corrected Bayes, onset, trajectories, definitions, and technical inventory.
- Do not link archived June/July candidate indexes as current work.
- Never create an empty shell merely to satisfy a link.

### 08 Independent red team

- Recalculate or reconcile every displayed result against the frozen sources.
- Check claim language, source-to-HTML consistency, links, images, anchors,
  accessibility basics, relative paths, file size, Git/data policy, and
  deterministic rendering.
- Do not edit product files. Return `AUDIT_PASS` or `AUDIT_FAIL` with severity
  and ownership for every issue.

### 09 Remediation

- Run only after `AUDIT_FAIL`.
- Fix the smallest approved file set, add regression tests, and rerun affected
  stages.
- Do not create the final marker.
- Start a fresh prompt-08 task after remediation.

### 10 Final integration

- Add the independent stage controller with `datasets`, `model-results`,
  `synthesis`, `plots`, `report`, `index`, `audit`, and `all` stages.
- Run every stage separately and through `--stage all`.
- Prove two report-only rebuilds are byte-stable.
- Run focused tests, the full repository suite, `git diff --check`, tracked
  file-size checks, and the final audit.
- Create `AUGUST_REPORT_COMPLETE_AND_AUDITED` only after a fresh independent
  `AUDIT_PASS` and every integration check passes.

## Scientific readings that must remain fixed

- The strongest result is increased scorer-based predictability or
  conventionality of form with age at fixed measured lexical effort in PBM.
- TinyDialogues and Mistral agreement on PBM is scorer robustness, not an
  independent child-sample confirmation.
- The non-PBM58 contextual Mistral slope has the expected negative sign, but
  its frozen primary clustered interval crosses zero. It is directionally
  consistent and not confirmed. The child bootstrap remains a sensitivity.
- Unconditional surprisal declines with age, while utterance context gain also
  declines, contrary to the registered positive direction.
- PBM same-word k0 and k3 age effects are robust across separate Mistral,
  Qwen3-14B, and TinyDialogues fits. Other word-level effects are partly
  scorer-dependent. Raw coefficient magnitudes are not pooled across models.
- The current response-space interaction is contrary to the simple prediction
  and uses exact-string, model/prompt/temperature-dependent uncertainty. It is
  not semantic response uncertainty.
- Sustained developmental onset is not established.
- Corrected Bayes values are probabilities within the supplied matched
  candidate set, not posteriors over all possible utterances.
- Generated alternatives are not meaning-preserving.
- Hall is a separate historical cross-sectional snapshot. Its strata support
  descriptive, scorer-indexed comparisons only, not causal SES, deficit, or
  inherent-group claims.
- Individual trajectories show heterogeneity and do not imply one universal
  developmental law.

## Declared pending evidence

- The remaining 58 children have not received same-pass Mistral word scoring.
- The conversationally responsive sample remains `REVIEW` pending 18,172
  `context_k1` mismatches and the 325-row manual validation.
- No validated listener-utility outcome exists.
- Qwen-generated/Mistral-scored response calibration is not yet integrated.
- Morpheme, syllable, and phoneme sustained-onset sensitivities remain pending.

These items must be visible on the August report but do not invalidate the
completed, explicitly scoped evidence.

## Shared-worktree and Git contract

- One fresh task owns one stage. Tasks never run concurrently.
- Every stage begins from `agent/august-supervisor-report-v1`, a clean tracked
  worktree, and the exact predecessor SHA supplied by the operator.
- An agent stops rather than switching, pulling, merging, rebasing, resetting,
  stashing, cleaning, or overwriting unexpected work.
- Each stage has an explicit file allowlist and must never use `git add .`.
- `data/`, `results/`, `figs/`, archives, checkpoints, secrets, logs, and large
  binary products never enter Git.
- Shared project files (`AGENTS.md`, `TODO.md`, `docs/design.md`, and
  `docs/notes.md`) are updated only by the final integration stage, except for
  this initial workflow-documentation change.
- A stage handoff contains status, commit SHA, changed files, commands and
  actual test results, manifests, blockers, and clean status.
