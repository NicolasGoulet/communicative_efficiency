# Prompt 03 — Extract audited datasets and model results

Replace `EXPECTED_SHA` with the prompt-02 commit SHA and paste this entire
prompt into one fresh agent task.

## Prompt

You are stage 03 of the August supervisor-report workflow in
`/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency`.

This repository uses one **shared physical worktree**. Do not spawn agents and
do not run this task concurrently with another stage.

Read `AGENTS.md`, `TODO.md`, the workflow README/contract, frozen specification,
configuration, contracts, fixtures, and tests. Inspect only the canonical
saved tables and PASS/COMPLETE manifests declared by the frozen configuration.

Print `pwd`, `git status --short --branch`, `git branch --show-current`, and
`git rev-parse HEAD`. Require the exact root, branch
`agent/august-supervisor-report-v1`, clean tracked worktree, and
`HEAD == EXPECTED_SHA`. Stop without editing on any mismatch. Do not switch,
pull, merge, rebase, reset, stash, clean, or overwrite work.

### Explicit file allowlist

- `src/august_supervisor/evidence.py`
- `src/august_supervisor/model_results.py`
- `tests/test_august_supervisor_evidence.py`
- `tests/test_august_supervisor_model_results.py`

Generated registries and manifests go only under ignored
`results/august_supervisor_report/`. Do not edit reports, plots, configuration,
the frozen spec, or existing analysis code. Never use `git add .` and never
stage ignored or large products.

This is test-driven work. Add a focused failing test for extraction provenance
or hash validation, run it and record the expected failure, implement the
smallest complete behavior, and rerun it to green.

Implement independent `datasets` and `model-results` extraction functions.
They must:

- verify each upstream source hash and required audit marker before reading;
- read canonical saved CSV/JSON tables, never scrape estimates from report
  prose;
- preserve sample, scorer, outcome, formula/contrast, controls, estimator,
  clustering unit, interval method, convergence warnings, counts, evidence
  status, source path, and source hash;
- fail on duplicate claim IDs, ambiguous scorer/sample identities, schema
  mismatch, changed hashes, or unsupported missing values;
- write atomically and deterministically:
  `sample_registry.csv`, `effect_registry.csv`, `model_inventory.csv`,
  `declared_blockers.csv`, `dataset_manifest.json`, and
  `model_results_manifest.json`;
- prove through before/after hashes that upstream inputs remain unchanged.

Do not import or execute Statsmodels or any model-fitting entry point. Do not
fit, bootstrap, select, smooth, plot, or render prose. A missing result is
`PENDING`/`BLOCKED`, not permission to manufacture it.

Scientific rule: **Do not invent, refit, select, or reinterpret results.**
Every numeric statement must resolve through a claim ID to an audited source.
Keep PBM discovery, non-PBM confirmation, TinyDialogues/Qwen robustness, and
Hall separate; never pool raw tokenizer scales.

Run focused extraction tests, contract tests, relevant existing manifest
tests, and `git diff --check`. Execute the two extraction stages on the real
declared artifacts and require PASS manifests. Commit only allowlisted source
and test files with:

```text
August report phase 3: build audited results registry
```

Return `STAGE_PASS` only after tests and both manifests pass and the commit
leaves a clean worktree. Return commit SHA, changed files, red/green and real
stage commands/results, row counts/hashes, blockers, and final
`git status --short --branch`.
