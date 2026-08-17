# Task 07 — Build the August supervisor landing page

You are implementing stage 07 of the August supervisor-report workflow in the
`communicative_efficiency` repository.

## Mandatory operating contract

- Work in the existing shared physical worktree on branch
  `agent/august-supervisor-report-v1`.
- Do not spawn agents. These prompts are sequential because all tasks share one
  physical worktree.
- Before editing, run `git status --short --branch`, verify a clean worktree,
  and verify `git rev-parse HEAD` equals `EXPECTED_SHA`.
- If the SHA differs, the worktree is dirty, or the prior handoff lacks
  `STAGE_PASS`, stop and report the discrepancy.
- Use test-driven development: demonstrate a failing focused test before code,
  then run focused and relevant tests after implementation.
- Use the Explicit file allowlist. Never use `git add .`; stage named files only
  after inspecting the diff.
- Do not invent, refit, select, or reinterpret results. Landing-page language
  and status cards must resolve to a frozen claim ID.
- Preserve the PBM discovery versus non-PBM confirmation distinction. Keep Hall
  separate as a descriptive cross-sectional/domain-sensitivity analysis.

`EXPECTED_SHA={{PASTE_STAGE_06_SHA}}`

## Explicit file allowlist

- `src/august_supervisor/index.py`
- `tests/test_august_supervisor_index.py`
- `docs/august_supervisor_index.html`

## Required implementation

1. Begin with failing tests for page-registry validation, required destinations,
   relative-link integrity, image integrity, status vocabulary, and deterministic
   HTML.
2. Generate the page from the frozen page registry; do not hard-code empty or
   title-only shell pages.
3. Provide a five-result executive card summary plus a clear status legend:
   completed/supported, qualified, contrary, descriptive, and pending.
4. Link the integrated August report, direct-results explorer, word-level
   cross-scorer report, Hall report, corrected Bayes report, onset report,
   individual trajectories, formal definitions, and evidence inventory.
5. Preserve legacy June/July pages as archive links only. Do not modify the
   July landing page or silently redirect old pages.
6. Ensure keyboard navigation, useful link labels, mobile layout, and readable
   warning text without relying on color alone.

## Verification and handoff

- Run focused landing-page tests and all August workflow tests.
- Validate every local link, image, and fragment; inspect source HTML and one
  desktop/mobile rendering.
- Run `git diff --check` and verify only allowlisted files changed.
- Commit with `August report phase 7: add supervisor landing page`.
- Return `STAGE_PASS`, commit SHA, test results, page hash, link-audit summary,
  and `git status --short --branch` showing a clean worktree.
