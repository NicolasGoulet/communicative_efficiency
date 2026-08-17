# Task 06 — Render the integrated August supervisor report

You are implementing stage 06 of the August supervisor-report workflow in the
`communicative_efficiency` repository.

## Mandatory operating contract

- Work in the existing shared physical worktree on branch
  `agent/august-supervisor-report-v1`.
- Do not spawn agents. These prompts are sequential because all tasks share one
  physical worktree.
- Before editing, run `git status --short --branch`, verify a clean worktree,
  and verify that `git rev-parse HEAD` equals `EXPECTED_SHA` supplied below.
- If the SHA differs, the worktree is dirty, or a prior stage lacks
  `STAGE_PASS`, stop and report the discrepancy.
- Use test-driven development: start from a failing focused test, record it,
  implement, and then run focused and relevant tests.
- Use the Explicit file allowlist below. Never use `git add .`; inspect and
  stage only named files.
- Do not invent, refit, select, or reinterpret results. Every numeric sentence
  and status label must resolve to a frozen claim ID.
- Preserve the PBM discovery versus non-PBM confirmation distinction. Keep Hall
  separate as a descriptive cross-sectional/domain-sensitivity analysis.

`EXPECTED_SHA={{PASTE_STAGE_05_SHA}}`

## Hard stage boundary

Do not fit models. Do not create plots. Read only the frozen synthesis, table,
and figure manifests. If a desired result is missing, render it as pending or
stop on a broken contract; never derive a replacement in this stage.

## Explicit file allowlist

- `src/august_supervisor/sections.py`
- `src/august_supervisor/render.py`
- `tests/test_august_supervisor_report.py`
- `docs/august_supervisor_report.md`
- `docs/august_supervisor_report.html`

## Required implementation

1. Write failing tests for required sections, claim-ID resolution, prohibited
   wording, figure references, source links, and deterministic Markdown/HTML.
2. Render a concise executive section followed by: sample logic; utterance
   predictability at fixed effort; word-level three-scorer findings;
   unconditional/contextual decomposition; baseline and corrected-Bayes
   evidence; response uncertainty; onset; Hall as a separate snapshot;
   conclusions and next decisive tests.
3. Keep internal implementation labels such as Route 1/Route 2 out of the
   supervisor-facing prose when plain scientific wording is clearer.
4. Clearly distinguish `supported`, `qualified`, `contrary`, `descriptive`, and
   `pending`. Never call non-PBM contextual decline confirmed, surprisal
   listener utility, exact-string entropy semantic uncertainty, or Hall a
   causal SES result.
5. Keep tracked HTML lightweight. If an embedded sharing bundle is useful,
   generate it under ignored results and link it through the manifest.

## Verification and handoff

- Run focused report tests and all August workflow tests.
- Render twice and compare hashes for byte-identical output.
- Run `git diff --check`; inspect prose, tables, links, and source HTML.
- Commit with `August report phase 6: render integrated supervisor report`.
- Return `STAGE_PASS`, commit SHA, exact test results, report hashes, unresolved
  pending items, and `git status --short --branch` showing a clean worktree.
