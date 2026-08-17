# Prompt for the `compute_surprisal_mila` Hall scoring implementation

Paste everything below into an agent whose working directory is the local
`compute_surprisal_mila` repository.

---

You are the implementation agent for `compute_surprisal_mila`. Build the
complete, production-safe Hall cross-sectional real-child Mistral scoring lane.
Use test-driven development. Do not submit a real Mila job during implementation.
Implement, test, document, commit, push, and return the exact smoke-only Mila
submission command only when the code is ready.

## Scientific and input contract

The upstream immutable handoff will be at:

```text
new_data/hall_snapshot_mistral_real_k0_k3_v1/
```

It contains:

```text
hall_snapshot_mistral_real_k0_k3_v1.tar.gz
hall_snapshot_mistral_real_k0_k3_v1.tar.gz.sha256
LOCAL_HANDOFF_AUDIT.json
LOCAL_HANDOFF_REPORT.md
```

Frozen archive facts:

```text
archive SHA-256: 23ca951da9912ea3d46235821cd877c972e7397acd64054ae5dff7d6125544a0
archive bytes: 2,520,424
input rows: 71,830
children: 37
primary children: 36
primary rows: 70,510
sensitivity-only child: 1
rows with a nonempty adult context: 70,018
rows with structurally blank adult context: 1,812
child turns immediately following an adult: 33,030
contracts: real child k0, k1, k2, k3
expected scored rows: 287,320
blank targets: 0
duplicate utterance IDs: 0
```

Score only `inputs/hall_child_snapshot_scoring.csv`. Do not score metadata,
comparators, or support files. The target is `chi_utterance_clean`. Contexts
are blank for k0 and are `context_k1`, `context_k2`, and `context_k3` for the
other contracts. Preserve every input row in every contract, including the
1,812 rows whose adult-context fields are structurally blank. Do not generate
baselines, word-level payloads, token-level payloads, or scientific models.

This is a cross-sectional Hall handoff, not an extension of the 79-child
longitudinal sample. The compute repository owns only scoring and scoring
audits; `communicative_efficiency` will own the analyses.

## Required scorer identity

Match the completed full-79 direct-Mistral production calibration:

```text
model: mistralai/Mistral-7B-v0.3
model revision: caa1feb0e54d415e2df31207e5f4e273e33509b1
dtype: fp16
units: bits
batch size: 16 unless an exact-wrapper smoke proves a lower safe value is required
target-token rule: the existing cleaned scorer target-overlap rule
cleaning: OFF; upstream targets are already canonical
```

Use the staged model and validate `STAGE_READY` before requesting a GPU. Reuse
the established cleaned scorer (`new_score_utterances_fast.py` or its exact
production-compatible internal API) rather than writing new probability math.
Record the tokenizer revision, scoring code revision, model revision, dtype,
batch size, max length, GPU name, and Slurm job ID in every output contract.
Do not leave known revision fields blank and do not claim equivalence without
running the existing golden-regression checks applicable to this scorer.

## Start with repository history

1. Read `AGENTS.md`, `TODO.md`, and the current branch/status.
2. Inspect the full-79 cleaned scoring implementation and tests, especially:
   `src/new_score_utterances.py`, `src/new_score_utterances_fast.py`,
   `src/run_cleaned_child_bundle_mistral_scoring.py`,
   `slurm/score_cleaned_79_bundle.sbatch`, and the cleaned scorer golden
   regression tests.
3. Inspect the newer smoke/release design in:
   `slurm/submit_qwen_response_mistral_calibration.sh`, its prepare/score/audit
   wrappers, and `tests/test_submit_qwen_response_mistral_calibration.py`.
4. Create a dedicated branch such as
   `agent/hall-snapshot-mistral-scoring` from the current remote default branch.
   Do not mix this work into an unrelated Qwen branch.

## Implement with tests first

Add a coherent Hall namespace. Suggested files are:

```text
src/prepare_hall_snapshot_mistral.py
src/run_hall_snapshot_mistral_scoring.py
src/audit_hall_snapshot_mistral.py
src/validate_hall_snapshot_smoke_approval.py
slurm/prepare_hall_snapshot_mistral.sbatch
slurm/score_hall_snapshot_mistral.sbatch
slurm/audit_hall_snapshot_mistral.sbatch
slurm/submit_hall_snapshot_mistral.sh
tests/test_prepare_hall_snapshot_mistral.py
tests/test_run_hall_snapshot_mistral_scoring.py
tests/test_audit_hall_snapshot_mistral.py
tests/test_submit_hall_snapshot_mistral.py
docs/hall_snapshot_mistral_runbook_2026-08-10.md
```

Names may change if the existing architecture has a clearly better fit, but
the contracts below may not be weakened.

### CPU preparation

- Verify the sidecar checksum and the hard-coded frozen archive SHA-256 before
  extraction.
- Reject path traversal, links, unexpected archive members, unexpected file
  hashes, wrong package ID, non-PASS upstream audits, wrong row/child counts,
  blank targets, duplicate `utterance_id`, invalid strata, or missing columns.
- Parse CSV with Python's `csv` module or another structured parser, never
  `awk -F,`.
- Copy/extract atomically into a fresh scratch run root.
- Build an exact four-row scoring manifest and deterministic, representative
  25-row smoke input. The smoke selection must cover all four race/class
  strata, primary and sensitivity-only provenance, home/school/transition/
  other settings, adult-adjacent and non-adult-adjacent turns, nonempty and
  blank contexts, and short plus long target/context cases. Save the selection
  and coverage audit.
- Prepare or validate the immutable Python environment entirely in the CPU
  stage. The GPU job must not run package installation, archive extraction,
  broad input scanning, or environment construction.
- Write `PREPARATION_PASSED` only after every preparation gate succeeds.

### Exact-wrapper GPU smoke

- Use `sbatch`; never load or run Mistral on a login node.
- Use the exact same `.sbatch` wrapper, Python runner, model, revision, dtype,
  batch size, max length, CSV reader, and output validator as production.
- One GPU smoke job should score the 25 selected rows under all four contracts,
  producing exactly 100 scored rows. Do not create a toy scorer.
- Force a fresh isolated smoke directory every submission attempt.
- The dependent CPU smoke audit must compare row identity/order, target text,
  exact context text and `context_col_used`, finite `sum_bits` and
  `mean_bits_per_token`, positive evaluated-token counts, and explicit context
  truncation fields. It must verify all required smoke strata.
- For the blank-context rows, compare k1/k2/k3 against k0 under the established
  FP16 golden-regression tolerance; do not silently assume exact equality.
- Write compact `smoke_report.md`, machine-readable summary/coverage files,
  environment/provenance, and `SMOKE_PASSED` only after all checks pass.

### Production staging and resume

Default submission must be smoke-only. Production requires an explicit
`PRODUCTION_APPROVED=1`, the exact passed smoke report root, the same archive
SHA, and the same Git/model/scorer revisions.

Use this dependency structure:

```text
CPU prepare
-> exact-wrapper GPU smoke
-> CPU smoke audit / SMOKE_PASSED

explicit later production approval:
CPU release audit of approved smoke
-> wave 1 GPU array: k0 and k3 (max 2 concurrent)
-> CPU wave-1 audit / WAVE1_READY
-> wave 2 GPU array: k1 and k2 (max 2 concurrent)
-> CPU final audit + compact archive / COMPLETE_AND_AUDITED
```

Outputs must be atomic. Resume may skip an output only after validating its
contract, row count, identity hashes, target/context hashes, scorer provenance,
and score fields. File existence alone is never sufficient. A normal new run
requires a fresh run root; recovery must be a separately tested explicit mode.

The final audit must require:

- four completed context outputs;
- exactly 71,830 ordered, identity-preserved rows per output;
- 287,320 total scored rows;
- zero blank targets and zero missing/nonfinite score rows;
- positive `n_eval_tokens` for every target;
- exact target/context/utterance identity against the extracted input;
- exactly 70,018 nonempty and 1,812 blank context rows in k1/k2/k3;
- model revision `caa1feb0e54d415e2df31207e5f4e273e33509b1` and FP16 provenance;
- a compact retrieval archive, its SHA-256, final report, and
  `COMPLETE_AND_AUDITED` marker.

Do not demand zero context truncation without measuring it. Target text must
never be truncated; any context truncation must be counted and surfaced in the
report and downstream contract.

## Slurm resource contract

CPU preparation/audits must use `long-cpu` and request no GPU. Every GPU
submission must explicitly include one coherent request family, for example:

```text
--ntasks=1
--cpus-per-task=4
--mem=48G
--time=01:00:00   # smoke; justify any change
--partition=long
--gpus-per-task=l40s:1
```

Production may use `--time=12:00:00` if justified by the exact smoke timing.
Never combine `--gpus-per-task` and GPU `--gres`. Never omit `--ntasks=1`.
Use argument arrays in the submitter so the task/GPU contract cannot disappear
from one stage.

Run the Mila Slurm argument validator against every resolved GPU submission:

```bash
python "$CODEX_HOME/skills/submit-mila-slurm-jobs/scripts/validate_sbatch_args.py" -- \
  --parsable --ntasks=1 --cpus-per-task=4 --mem=48G --time=01:00:00 \
  --partition=long --gpus-per-task=l40s:1 slurm/score_hall_snapshot_mistral.sbatch
```

### Mandatory orchestration tests

- Fake `sbatch`, capture every complete argument vector, and assert CPU/GPU
  resource separation, `--ntasks=1`, the single GPU request family,
  dependencies, arrays, scripts, and smoke-only default.
- Test both LF and CRLF manifests.
- Fake the model command and exercise the exact Slurm wrapper cheaply.
- Test atomic publication, interrupted-output rejection, and validated resume.
- Test that production cannot be released by a smoke-only branch or a dirty,
  revision-mismatched worktree.
- Run focused tests, the relevant scorer golden regression, full unit tests,
  `bash -n` on every shell file, the Slurm validator, and `git diff --check`.

## Submission interface and reports

Use roots like:

```text
RUN_ROOT=$SCRATCH/compute_surprisal_mila/hall_snapshot_mistral/hall_snapshot_mistral_real_k0_k3_v1/$RUN_ID
REPORT_ROOT=$HOME/compute_surprisal_mila/reports/hall_snapshot_mistral/hall_snapshot_mistral_real_k0_k3_v1/$RUN_ID
```

The submitter must print and record the prepare, smoke, smoke-audit, release,
wave, and final-audit job IDs; run/report/output roots; production-submitted
flag; exact code/model/archive revisions; and one-line rsync commands for the
compact smoke and final reports. State explicitly that no GPU is allocated
during CPU preparation.

When implementation is complete:

1. Commit and push the dedicated branch and open/update a draft PR.
2. Report files changed, tests and exact counts, branch/commit, remaining risks,
   and the exact Mila pull plus smoke-only submission command.
3. Do not submit production automatically and do not inspect or fit Hall
   scientific effects.

---
