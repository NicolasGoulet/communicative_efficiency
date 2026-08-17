# August Supervisor Report: Operator Guide

This is the short guide for running the August supervisor-report build through
fresh, sequential agent tasks. The copy-ready prompts are under `prompts/`.
The detailed scientific and technical rules are in `WORKFLOW_CONTRACT.md`.

## The one rule that matters most

Run **exactly one new task at a time**. These tasks use one shared physical
worktree and one ordered branch, so they must never run in parallel.

Start a new task only after the previous task returns all of the following:

- `STAGE_PASS`;
- the resulting commit SHA (or the recorded starting SHA for bootstrap);
- the commands and actual test results;
- the files and manifests it created;
- `git status --short --branch` showing a clean worktree.

Replace `EXPECTED_SHA` in the next prompt with the SHA returned by the previous
task. Do not start the next prompt if the previous task reports `BLOCKED`,
`STAGE_FAIL`, `AUDIT_FAIL`, a dirty worktree, or a different branch/SHA.

## How to run it

1. Begin from the local `communicative_efficiency` repository after these
   workflow documents have been merged to `main`.
2. Open a fresh agent task and paste all of
   [`prompts/00_bootstrap.md`](prompts/00_bootstrap.md).
3. When it returns `STAGE_PASS`, copy its reported SHA.
4. Open another fresh task, paste the next prompt, and replace
   `EXPECTED_SHA` with that SHA.
5. Continue in order. Never paste two prompts into two simultaneous tasks.

## Prompt sequence

| Order | Prompt | Start only when | Expected result |
| --- | --- | --- | --- |
| 00 | [`prompts/00_bootstrap.md`](prompts/00_bootstrap.md) | `main` is clean and contains this workflow | Create `agent/august-supervisor-report-v1`; record the starting SHA |
| 01 | [`prompts/01_evidence_freeze.md`](prompts/01_evidence_freeze.md) | 00 passed | Frozen report scope, claim registry configuration, blockers, and page contract |
| 02 | [`prompts/02_contracts.md`](prompts/02_contracts.md) | 01 passed | Tested schemas, fixtures, hashing, and stage contracts |
| 03 | [`prompts/03_extract_results.md`](prompts/03_extract_results.md) | 02 passed | Audited sample/effect/model registries from saved results; no fitting |
| 04 | [`prompts/04_synthesis.md`](prompts/04_synthesis.md) | 03 passed | Deterministic headline/supporting/limitations tables |
| 05 | [`prompts/05_plots.md`](prompts/05_plots.md) | 04 passed | Fixed supervisor figures and plot-data manifests; no fitting |
| 06 | [`prompts/06_report.md`](prompts/06_report.md) | 05 passed | Integrated Markdown and lightweight HTML report |
| 07 | [`prompts/07_landing_page.md`](prompts/07_landing_page.md) | 06 passed | August landing page with verified navigation |
| 08 | [`prompts/08_red_team.md`](prompts/08_red_team.md) | 07 passed | Independent `AUDIT_PASS` or `AUDIT_FAIL`; auditor does not edit product files |
| 09 | [`prompts/09_remediation.md`](prompts/09_remediation.md) | 08 returned `AUDIT_FAIL` | Targeted fixes and rerun of affected stages |
| 10 | [`prompts/10_final_integration.md`](prompts/10_final_integration.md) | A fresh run of 08 returned `AUDIT_PASS` | Controller, full verification, final marker, commit, and publication handoff |

Prompt 09 is conditional. If prompt 08 returns `AUDIT_PASS`, skip 09 and use
prompt 10. If prompt 08 returns `AUDIT_FAIL`, run prompt 09, then repeat prompt 08
in a fresh task using the remediation commit SHA. Repeat that loop until
the independent audit passes. Remediation never creates the final marker.

## What enters Git

Commit only source code, tests, configuration, this documentation, Markdown,
and lightweight supervisor HTML. Keep `data/`, `results/`, `figs/`, archives,
checkpoints, logs, screenshots, and self-contained image-heavy sharing bundles
out of Git. Never use `git add .` in this workflow.

## What this workflow does not do

It does not refit the existing model inventory. It consumes audited saved
artifacts. Missing evidence remains visibly `PENDING` or `BLOCKED`. A genuinely
new model requires a separate, explicitly approved and preregistered analysis
lane before it can become an input to this report.
