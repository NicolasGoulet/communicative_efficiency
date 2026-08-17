# Task 09 — Remediate a failed independent audit

This task is conditional. Run it only after task 08 returned `AUDIT_FAIL`.

## Mandatory operating contract

- Work in the existing shared physical worktree on branch
  `agent/august-supervisor-report-v1`.
- Do not spawn agents. These prompts are sequential because all tasks share one
  physical worktree.
- Before editing, run `git status --short --branch`, verify a clean worktree,
  and verify `git rev-parse HEAD` equals `EXPECTED_SHA`.
- If the SHA differs, the worktree is dirty, or the prior output is not
  `AUDIT_FAIL`, stop and report the discrepancy.
- Use test-driven development: reproduce each defect with a failing test before
  changing the product, then run the affected stage and relevant tests.
- Obey the Explicit file allowlist pasted from the audit. Never use `git add .`;
  stage only the approved named files after inspecting the diff.
- Do not invent, refit, select, or reinterpret results. Every corrected number
  or sentence must still resolve to a frozen claim ID.
- Preserve the PBM discovery versus non-PBM confirmation distinction and keep
  Hall separate as a descriptive cross-sectional/domain-sensitivity analysis.

`EXPECTED_SHA={{PASTE_STAGE_08_SHA}}`

## Required audit handoff

`AUDIT_FINDINGS={{PASTE_AUDIT_FINDINGS}}`

### Explicit file allowlist

`{{PASTE_EXPLICIT_FILE_ALLOWLIST}}`

If either placeholder remains unreplaced, stop. Do not infer authority to edit
additional files.

## Required implementation

1. Reproduce every blocking finding with a focused failing test or an existing
   audit command and record the failure.
2. Make only the smallest corrections authorized by the pasted allowlist.
3. Rebuild only affected stages, preserving upstream input hashes and claim
   identities.
4. Rerun the focused tests, affected stage tests, and all August workflow tests.
5. Do not edit the audit findings or create the final completion marker.

## Verification and handoff

- Run `git diff --check`, inspect all corrections, and confirm a clean staged
  allowlist with no large generated products.
- Commit with `August report phase 9: remediate audit findings`.
- Return `STAGE_PASS`, commit SHA, finding-by-finding disposition, exact tests,
  rebuilt artifact hashes, and `git status --short --branch` proving a clean
  worktree.
- Then repeat prompt 08 in a fresh task with this commit as `EXPECTED_SHA`.
  Do not proceed to task 10 until that fresh run returns `AUDIT_PASS`.
