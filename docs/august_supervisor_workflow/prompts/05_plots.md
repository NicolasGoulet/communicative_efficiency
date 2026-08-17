# Task 05 — Build supervisor figures from frozen summaries

You are implementing stage 05 of the August supervisor-report workflow in the
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
- Use test-driven development: write a failing focused test, record the failure,
  implement the smallest complete change, then run focused and relevant tests.
- Use the Explicit file allowlist below. Never use `git add .`; stage only the
  named files after inspecting `git diff` and `git status`.
- Do not invent, refit, select, or reinterpret results. Every plotted estimate
  must resolve to a frozen claim ID and a registered source artifact.
- Preserve the PBM discovery versus non-PBM confirmation distinction. Keep Hall
  separate as a descriptive cross-sectional/domain-sensitivity analysis.

`EXPECTED_SHA={{PASTE_STAGE_04_SHA}}`

## Inputs

- `results/august_supervisor_report/synthesis/claim_registry.csv`
- `results/august_supervisor_report/synthesis/table_registry.csv`
- `results/august_supervisor_report/synthesis/synthesis_manifest.json`
- the preceding stage handoff

Do not import statsmodels. Do not read raw scored trees. Do not run bootstrap,
smoothing, model selection, or any statistical fit. Plot only compact frozen
tables emitted by stage 04.

## Explicit file allowlist

- `src/august_supervisor/plots.py`
- `tests/test_august_supervisor_plots.py`

Generated plot products belong under the ignored
`results/august_supervisor_report/plots/` namespace and must not be committed.

## Required implementation

1. Begin with failing tests for input-manifest validation, fixed output names,
   source claim IDs, plot-data export, alt text, captions, and deterministic
   manifest ordering.
2. Build a small fixed supervisor figure set covering only registered evidence:
   fixed-effort predictability, unconditional versus contextual components,
   word-level cross-scorer signs without pooling raw bits, Route 2 qualification,
   onset status, and a visually separate Hall snapshot panel.
3. Save the exact plot data behind every figure as a compact CSV.
4. Write a figure manifest containing figure ID, source claim IDs, plot-data
   path/hash, image path/hash, caption, alt text, and warnings.
5. Make the output deterministic and fail closed on missing or extra claims.

## Verification and handoff

- Run the focused plot tests and all August workflow tests.
- Inspect representative images for clipped labels and misleading shared axes.
- Run `git diff --check` and confirm only allowlisted tracked files are changed.
- Commit with `August report phase 5: add supervisor figures`.
- Return `STAGE_PASS`, the commit SHA, exact tests and results, generated manifest
  path/hash, and `git status --short --branch` proving a clean worktree.
