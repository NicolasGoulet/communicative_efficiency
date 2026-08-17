# Prompt 00 — Bootstrap the sequential workflow

Paste this entire prompt into one fresh agent task.

## Prompt

You are stage 00 of the August supervisor-report workflow in:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency
```

This repository uses one **shared physical worktree**. Do not spawn agents and
do not run this task concurrently with another stage.

Read completely before acting:

1. `AGENTS.md`
2. `TODO.md`
3. `docs/august_supervisor_workflow/README.md`
4. `docs/august_supervisor_workflow/WORKFLOW_CONTRACT.md`
5. `docs/august_supervisor_workflow/workflow_manifest.json`

Print and verify these checks:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
```

The repository root must be exactly `communicative_efficiency`; the tracked
worktree must be clean; the current branch must be `main`; and local `main`
must equal `origin/main`. If any check fails, stop without editing. Do not
switch, pull, merge, rebase, reset, stash, clean, or overwrite unexpected work.

If every check passes, create and switch to exactly:

```text
agent/august-supervisor-report-v1
```

Do not recreate or overwrite an existing branch. If it already exists, stop
and report the blocker.

### Explicit file allowlist

None. This bootstrap task does not edit or create tracked files.

Never use `git add .`. Never stage or commit `data/`, `results/`, `figs/`,
archives, checkpoints, logs, secrets, or binary outputs. Do not push `main` and
never force-push.

This bootstrap is part of a **test-driven** workflow. It must not fabricate a
failing implementation test because it implements no product behavior. Verify
the workflow documentation with:

```bash
.venv/bin/python -m unittest tests.test_august_supervisor_workflow_docs
git diff --check
git status --short --branch
```

Scientific rule for the entire workflow: Do not invent, refit, select, or reinterpret results.
Every numeric statement must resolve through a claim ID
to an audited source artifact. Keep PBM discovery, non-PBM confirmation,
TinyDialogues/Qwen robustness, and the separate Hall snapshot distinct. Do not
pool raw scores across tokenizers or turn predictability into a causal or
normative efficiency claim.

Return `STAGE_PASS` only if the branch exists, tests pass, and the task leaves a
clean worktree. Return:

- `STAGE_PASS` or `STAGE_FAIL`;
- starting `main` SHA;
- current branch and current SHA for use as the next task's `EXPECTED_SHA`;
- commands and actual results;
- confirmation that no tracked files changed;
- final `git status --short --branch` output.
