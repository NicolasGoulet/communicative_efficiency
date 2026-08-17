# Prompt 01 — Freeze the evidence and report scope

Replace `EXPECTED_SHA` below with the SHA returned by prompt 00, then paste the
entire prompt into one fresh agent task.

## Prompt

You are stage 01 of the August supervisor-report workflow in
`/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency`.

This repository uses one **shared physical worktree**. Do not spawn agents and
do not run this task concurrently with another stage.

Before editing, read `AGENTS.md`, `TODO.md`,
`docs/august_supervisor_workflow/README.md`, and
`docs/august_supervisor_workflow/WORKFLOW_CONTRACT.md`. Also inspect the current
July supervisor report, August scientific synthesis, direct-results explorer,
word cross-scorer report, Hall report, corrected Bayes report, onset report,
formal definitions, and the manifests that generated them.

Print and verify:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
```

The root must be `communicative_efficiency`, the branch must be
`agent/august-supervisor-report-v1`, the tracked worktree must be clean, and
HEAD must equal `EXPECTED_SHA`. If any check fails, stop without editing. Do
not switch, pull, merge, rebase, reset, stash, clean, or overwrite another
task's work.

### Explicit file allowlist

- `configs/august_supervisor_report_v1.json`
- `docs/august_supervisor_report_spec.md`
- `tests/test_august_supervisor_report_spec.py`

Do not edit any other tracked file. Never use `git add .`. Never stage data,
results, figures, archives, checkpoints, logs, secrets, or large binaries.

This is test-driven work. First add a focused test for the frozen specification
schema and required scientific statuses, run it, and record the expected
failure. Then implement the smallest complete specification and rerun the
focused test.

Build a frozen, machine-readable report configuration. For every promoted,
supporting, excluded, or pending claim, record:

- stable `claim_id` and scientific question;
- sample role and exact sample scope;
- scorer/model and tokenizer comparability rule;
- estimand, outcome, formula or contrast, controls, and direction convention;
- row, child, session, and corpus counts where available;
- estimate, interval, and uncertainty method when the claim is numerical;
- evidence status: `SUPPORTED`, `QUALIFIED`, `CONTRARY`, `DESCRIPTIVE`, or
  `PENDING`;
- canonical source artifact, source SHA-256, and required PASS/COMPLETE marker;
- required interpretation and limitation text;
- destination report section and figure eligibility.

Freeze the page contract for:

- `docs/august_supervisor_index.html`;
- `docs/august_supervisor_report.md`;
- `docs/august_supervisor_report.html`;
- links to the direct explorer, word comparison, Hall, corrected Bayes, onset,
  trajectories, definitions, and technical analysis inventory.

Lock these readings explicitly:

- non-PBM contextual Mistral is direction-consistent but not confirmed;
- the frozen child bootstrap is sensitivity evidence, not a replacement for
  the clustered primary interval;
- context-gain development is contrary to the registered positive direction;
- PBM cross-scorer repetition is robustness, not independent confirmation;
- raw magnitudes are not pooled across tokenizers;
- sustained onset is not established;
- exact-string response entropy is model/prompt/temperature dependent and not
  semantic uncertainty;
- generated candidates do not preserve meaning;
- corrected Bayes is finite candidate-set evidence;
- Hall is separate, descriptive, historical, non-causal, and non-deficit;
- remaining-58 word confirmation, listener utility, conversational manual
  validation, decoupled response calibration, and alternative-effort onset are
  pending.

Do not inspect unregistered outcomes, fit models, generate plots, or render the
report. Missing or conflicting artifacts must become explicit blockers.

Scientific rule: **Do not invent, refit, select, or reinterpret results.**
Every numeric statement must resolve through a claim ID to an audited source
artifact. Keep PBM discovery, non-PBM confirmation, TinyDialogues/Qwen
robustness, and Hall separate.

Run at minimum:

```bash
.venv/bin/python -m unittest tests.test_august_supervisor_report_spec
.venv/bin/python -m unittest tests.test_august_supervisor_workflow_docs
git diff --check
```

Commit only the allowlisted files with:

```text
August report phase 1: freeze evidence contract
```

Return `STAGE_PASS` only if focused tests pass, the commit exists, and the task
leaves a clean worktree. Return the commit SHA, changed files, red and green
test commands/results, verified artifact blockers, and final
`git status --short --branch` output.
