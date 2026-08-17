# Prompt 04 — Build deterministic scientific synthesis tables

Replace `EXPECTED_SHA` with the prompt-03 commit SHA and paste this entire
prompt into one fresh agent task.

## Prompt

You are stage 04 of the August supervisor-report workflow in
`/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency`.

This repository uses one **shared physical worktree**. Do not spawn agents and
do not run this task concurrently with another stage.

Read `AGENTS.md`, `TODO.md`, the workflow README/contract, frozen spec and
configuration, contracts, and the PASS dataset/model-results manifests.

Print `pwd`, `git status --short --branch`, `git branch --show-current`, and
`git rev-parse HEAD`. Require exact root, branch
`agent/august-supervisor-report-v1`, clean tracked worktree, and
`HEAD == EXPECTED_SHA`. Stop without editing on mismatch. Do not switch, pull,
merge, rebase, reset, stash, clean, or overwrite work.

### Explicit file allowlist

- `src/august_supervisor/synthesis.py`
- `tests/test_august_supervisor_synthesis.py`

Generated tables/manifests belong under ignored
`results/august_supervisor_report/`. Do not edit input registries, reports,
plots, configuration, the frozen spec, or existing analyses. Never use `git add .`;
never stage ignored or large products.

This is test-driven work. First add a focused failing classification or
claim-link test, record the expected failure, implement the smallest complete
solution, and rerun it to green.

Read only the frozen configuration and the compact PASS registries. Produce,
atomically and deterministically:

- `headline_findings.csv`;
- `supporting_findings.csv`;
- `coverage_and_limitations.csv`;
- `page_registry.csv`;
- `synthesis_manifest.json`.

Every sentence-level finding must carry its claim IDs. Classification must be
rule-based and limited to `SUPPORTED`, `QUALIFIED`, `CONTRARY`, `DESCRIPTIVE`,
or `PENDING`. Tests must preserve the frozen readings for non-PBM confirmation,
context gain, word-level scorer robustness, exact-string response uncertainty,
onset, corrected Bayes, Hall, and declared pending work.

Do not use Statsmodels, Matplotlib, report prose, outcome-driven model
selection, new arithmetic not declared in the frozen spec, plotting, or HTML.

Scientific rule: **Do not invent, refit, select, or reinterpret results.**
Every numeric statement must resolve through a claim ID to an audited source.
Keep PBM discovery, non-PBM confirmation, TinyDialogues/Qwen robustness, and
Hall separate. Preserve negative, null, contrary, descriptive, and pending
results instead of smoothing them into a positive narrative.

Run focused synthesis tests, upstream contract/extraction tests, the real
synthesis stage, and `git diff --check`. Commit only allowlisted files with:

```text
August report phase 4: build scientific claim synthesis
```

Return `STAGE_PASS` only if tests and the synthesis manifest pass and the
commit leaves a clean worktree. Return SHA, changed files, red/green commands
and results, finding counts by status, manifest hash, and final
`git status --short --branch`.
