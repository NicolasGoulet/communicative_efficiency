# Prompt 02 — Implement schemas and stage contracts

Replace `EXPECTED_SHA` with the prompt-01 commit SHA and paste this entire
prompt into one fresh agent task.

## Prompt

You are stage 02 of the August supervisor-report workflow in
`/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency`.

This repository uses one **shared physical worktree**. Do not spawn agents and
do not run this task concurrently with another stage.

Read `AGENTS.md`, `TODO.md`, the workflow README and contract, the frozen
`configs/august_supervisor_report_v1.json`, and
`docs/august_supervisor_report_spec.md` completely.

Print `pwd`, `git status --short --branch`, `git branch --show-current`, and
`git rev-parse HEAD`. Require the exact repository root, branch
`agent/august-supervisor-report-v1`, a clean worktree, and
`HEAD == EXPECTED_SHA`. Stop without editing on any mismatch. Do not switch,
pull, merge, rebase, reset, stash, clean, or overwrite unexpected work.

### Explicit file allowlist

- `src/august_supervisor/__init__.py`
- `src/august_supervisor/contracts.py`
- `tests/fixtures/august_supervisor/**`
- `tests/test_august_supervisor_contracts.py`

Do not edit the frozen specification, reports, plots, shared project
documentation, or existing analysis code. Never use `git add .`; never stage
ignored data/results/figures or large binaries.

This is test-driven work. Add and run a focused test that fails for the first
missing contract behavior, record why it failed, implement the behavior, and
then make the test green. Do not commit a permanently failing suite.

Implement only reusable contracts:

- versioned schemas for sample, effect, model, blocker, synthesis, page,
  figure, and stage-manifest records;
- required-column, type, enumeration, uniqueness, and foreign-key validation;
- SHA-256 helpers and atomic JSON/CSV writes;
- upstream-manifest hash chaining;
- deterministic ordering and canonical serialization;
- strict failure on missing, duplicate, ambiguous, or changed evidence;
- tiny fixtures covering PBM discovery, non-PBM confirmation, scorer
  robustness, Hall, a contrary result, and a pending blocker;
- stage-isolation tests proving later stages cannot silently replace upstream
  products.

Do not implement extraction, scientific classification, plotting, prose,
HTML, model fitting, or the final controller in this stage.

Scientific rule: **Do not invent, refit, select, or reinterpret results.**
Every future numeric statement must resolve through a claim ID to an audited
source artifact. Preserve PBM discovery, non-PBM confirmation,
TinyDialogues/Qwen robustness, and Hall as separate scopes.

Run focused tests, the workflow-documentation test, relevant existing manifest
tests, and `git diff --check`. Commit only allowlisted files with:

```text
August report phase 2: add workflow contracts
```

Return `STAGE_PASS` only after tests pass and the commit leaves a clean
worktree. Return the commit SHA, changed files, red/green commands and actual
results, schema/fixture inventory, and final `git status --short --branch`.
