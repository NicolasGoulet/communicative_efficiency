# Task 08 — Independently audit the August supervisor package

You are implementing stage 08 of the August supervisor-report workflow in the
`communicative_efficiency` repository. Act as an adversarial scientific and
publication auditor, not as the report author.

## Mandatory operating contract

- Work in the existing shared physical worktree on branch
  `agent/august-supervisor-report-v1`.
- Do not spawn agents. These prompts are sequential because all tasks share one
  physical worktree.
- Before editing, run `git status --short --branch`, verify a clean worktree,
  and verify `git rev-parse HEAD` equals `EXPECTED_SHA`.
- If the SHA differs, the worktree is dirty, or the prior stage lacks
  `STAGE_PASS`, stop and report the discrepancy.
- Use test-driven development for the audit tool: first show a failing test,
  then implement and run focused and relevant tests.
- Use the Explicit file allowlist. Never use `git add .`; stage only named files
  after inspecting the diff.
- Do not invent, refit, select, or reinterpret results. Audit every number and
  scientific statement against its frozen claim ID and registered source.
- Preserve the PBM discovery versus non-PBM confirmation distinction. Verify
  that Hall remains separate and descriptive rather than causal.

`EXPECTED_SHA={{PASTE_STAGE_07_SHA}}`

## Independence boundary

Do not edit report product files. Do not silently repair claims, links, plots,
or manifests during this stage. A substantive problem must produce
`AUDIT_FAIL` and a precise remediation allowlist. Do not create the final
completion marker.

## Explicit file allowlist

- `src/august_supervisor/audit.py`
- `tests/test_august_supervisor_audit.py`

Write audit products only under the ignored
`results/august_supervisor_report/audit/` namespace.

## Required implementation and audit

1. Begin with failing tests for claim-source reconciliation, number formatting,
   manifest hashes, local links/images/fragments, prohibited language, and
   deterministic-render checks.
2. Recompute no models, but independently trace every displayed estimate from
   source manifest through synthesis, plot data, report, and landing page.
3. Audit scientific guardrails: non-PBM primary CI, context-gain direction,
   cross-tokenizer non-pooling, response-entropy limits, onset not established,
   candidate-set Bayes scope, trajectory heterogeneity, and Hall interpretation.
4. Audit HTML source, accessibility basics, desktop/mobile appearance, missing
   assets, dead links, empty shells, and external-sharing behavior.
5. Audit Git hygiene, tracked file sizes, ignored large products, clean builds,
   and two deterministic render hashes.
6. Emit machine-readable findings with severity, affected claim ID/file,
   evidence, required action, and an explicit remediation file allowlist.

## Verification and handoff

- Run focused audit tests, all August workflow tests, and the audit itself.
- Commit only the audit tool/tests with
  `August report phase 8: add independent package audit` if they changed.
- If any blocking finding exists, return `AUDIT_FAIL`, the audit report/hash,
  exact findings, explicit remediation allowlist, current commit SHA, and clean
  worktree status. The operator must run task 09 next.
- If no blocking finding exists, return `STAGE_PASS` and `AUDIT_PASS`, the same
  evidence, and `git status --short --branch` proving a clean worktree. The
  operator may skip task 09 and proceed to task 10.
