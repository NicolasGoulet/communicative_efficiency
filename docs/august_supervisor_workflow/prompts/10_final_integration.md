# Task 10 — Integrate, verify, and hand off the August package

Run this task only after a fresh task 08 returned both `STAGE_PASS` and
`AUDIT_PASS` for the current commit.

## Mandatory operating contract

- Work in the existing shared physical worktree on branch
  `agent/august-supervisor-report-v1`.
- Do not spawn agents. These prompts are sequential because all tasks share one
  physical worktree.
- Before editing, run `git status --short --branch`, verify a clean worktree,
  and verify `git rev-parse HEAD` equals `EXPECTED_SHA`.
- If the SHA differs, the worktree is dirty, or the fresh audit did not return
  `AUDIT_PASS`, stop and report the discrepancy.
- Use test-driven development: add failing controller/completion-gate tests
  before implementation and record the red/green evidence.
- Use the Explicit file allowlist below. Never use `git add .`; inspect and
  stage only named files.
- Do not invent, refit, select, or reinterpret results. Preserve every frozen
  claim ID and the exact audit-approved products.
- Preserve the PBM discovery versus non-PBM confirmation distinction. Keep Hall
  separate as a descriptive cross-sectional/domain-sensitivity analysis.

`EXPECTED_SHA={{PASTE_FRESH_AUDIT_PASS_SHA}}`

## Explicit file allowlist

- `src/build_august_supervisor_report.py`
- `tests/test_august_supervisor_controller.py`
- `AGENTS.md`
- `TODO.md`
- `docs/design.md`
- `docs/notes.md`

The marker is generated under ignored
`results/august_supervisor_report/AUGUST_REPORT_COMPLETE_AND_AUDITED`; do not
commit it.

## Required implementation

1. Add a thin controller exposing independent stages: `datasets`,
   `model-results`, `synthesis`, `plots`, `report`, `index`, `audit`, and `all`.
   It orchestrates existing modules and validates hash dependencies; it must
   not contain modeling or plotting logic.
2. Test refusal on missing/stale manifests, changed input hashes, absent
   `AUDIT_PASS`, dirty or incomplete artifacts, and invalid stage names.
3. Run every stage separately and then `--stage all` from the frozen inputs.
4. Perform two report-only rebuilds and require byte-identical Markdown, HTML,
   plot, page, and manifest hashes.
5. Run focused controller tests, all August workflow tests, and the repository's
   full test suite. Record exact commands, counts, skips, and failures.
6. Run the independent audit once more on the integrated build. Only after it
   passes, write `AUGUST_REPORT_COMPLETE_AND_AUDITED` with commit, manifest,
   audit, product hashes, test summary, and timestamp.
7. Update the project compass/status documents narrowly and truthfully.

## Final Git and handoff checks

- Run `git diff --check`, inspect `git diff --stat`, audit tracked file sizes,
  confirm generated data remain ignored, and confirm only allowlisted tracked
  files changed.
- Commit with `August report phase 10: integrate and audit supervisor package`.
- Push the workflow branch and open a draft pull request if authentication is
  available. Do not merge into main.
- Return `STAGE_PASS`, final commit SHA, branch/PR, full test results, audit hash,
  product hashes, completion-marker path, and `git status --short --branch`
  proving a clean worktree.
