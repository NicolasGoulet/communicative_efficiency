# Project Portability And Git Recovery — 2026-09-02

This is the dated operational record for recovering the project from the T7
external drive and continuing work on a machine with limited local storage. It
supplements the scientific data map in `AGENTS.md`; it does not replace any
analysis contract or completion marker.

## Verified storage and operating decision

- The PC initially had 78,778,703,872 bytes free (about 73.4 GiB).
- The T7 had 228,494,934,016 bytes free (about 212.8 GiB).
- Raw data, scored archives, model outputs, checkpoints, and large historical
  results remain on the T7. None was copied or modified during the Git rescue.
- Local storage is for fresh Git checkouts, a bounded environment, and small
  active outputs. Keep the initial permanent local project footprint below
  10–15 GiB and retain at least 50 GiB of free space.
- Do not copy the approximately 17 GB working-data set or the approximately
  59 GB scored-archive layer to the PC by default. Read needed inputs from the
  mounted T7 and size-check every proposed local transfer first.

The current T7 sibling-repository root is:

```text
/media/alkan/T7/EvaPortelance/Projet_1/
```

That mount path is machine-specific. Discover it on each machine instead of
embedding it in new code. Paths under `/home/apaixonada/` in historical notes
record the previous laptop and are not current portable defaults.

## Six-repository Git scope

The complete project Git audit covered:

1. `communicative_efficiency`
2. `compute_surprisal_mila`
3. `developmental_word_information`
4. `generate_baselines_mila`
5. `bayes_efficiency_mila`
6. `child_complexity_predictors`

All six main T7 working directories had zero content changes and zero
untracked files when permission-only presentation noise was excluded. All six
passed `git fsck --full --no-reflogs` with no corrupt or missing objects.
Old dangling objects were retained in the exact backup; no prune, garbage
collection, reset, clean, rebase, or branch deletion was performed.

## Pre-change recovery artifacts

The PC recovery directory is:

```text
/home/alkan/Documents/EvaPortelance_git_safety_2026-09-02/
```

It occupies about 3.9 GiB and contains:

- one exact archive of all six original `.git` directories, including
  reflogs, the old worktree registrations, unreachable objects, and the
  `compute_surprisal_mila` stash;
- one verified `--all` Git bundle per repository, containing every named ref
  that existed before live remote operations.

SHA-256 checksums:

```text
21d86a165879399e6b17ce6c341fe02b1878d0ebb64094386aa298c44065eb82  exact_git_directories_pre_remote_2026-09-02.tar
38fffa76d7b996f2ec7d0ff7d7252a750ae6f2640437bbb03f0abe0a7c472c2e  communicative_efficiency_all_refs_pre_remote_2026-09-02.bundle
91fbc77c30a8731b12310ec2ff9337aabadc4f39d70b05e7c9a9440899b8c6d8  compute_surprisal_mila_all_refs_pre_remote_2026-09-02.bundle
40d229896238629f800da658eab66817bcda5e82c867136a644968ffcbab5b79  developmental_word_information_all_refs_pre_remote_2026-09-02.bundle
54a62828dcf15d870fd16e4623095675425de9491bfbd21207d142782299f00b  generate_baselines_mila_all_refs_pre_remote_2026-09-02.bundle
410bf47cb74734f2d5595acb9a8324444cf658c374792100c91c5c5ca8173be1  bayes_efficiency_mila_all_refs_pre_remote_2026-09-02.bundle
37a93000240c6ef55cb5d446683959d87ceae500592f44dc8ac22ebb97fb2206  child_complexity_predictors_all_refs_pre_remote_2026-09-02.bundle
```

The tar member listing and every bundle verification completed successfully.
Do not delete this directory until a second independent backup exists.

The March 2026 `compute_surprisal_mila` stash changes historical tracked
`data/` and `results/` CSVs and is therefore intentionally not published as a
GitHub branch. It is preserved in both the exact archive and the compute
bundle. Do not apply or drop it without a separate content/provenance review.

## Remote preservation and integration performed

Previously unrepresented branch names were pushed without force:

```text
communicative_efficiency
  agent/august-supervisor-report-v1       f52a7f102dd87a6a566ef72bbf24519efda16202
  agent/bayesian-route1-route2-v1         c19cf16ed7c016187105202c8ee7697932e30815

compute_surprisal_mila
  codex/cross-population-scoring          32acbc06108f5691162da8f022d501e24202b95f
  codex/three-model-surprisal-schema       775fe190e45d4cb3108e8dd95afdaa7f671f3254
```

Dated `recovery/pre-integration-main-2026-09-02` branches preserve the old
`main` tips of `communicative_efficiency`, `compute_surprisal_mila`,
`developmental_word_information`, and `generate_baselines_mila`.

Relevant completed feature work was integrated in isolated PC clones and
published first as `integration/validated-main-2026-09-02`:

- `compute_surprisal_mila` main is `6c9f716aaacccac65b3aadd9c94f6cb4dd8abf29`.
  It includes the PBM transformer Mistral scorer, the seven-day Mila control
  connection documentation correction, and a branch-independent test repair.
- `developmental_word_information` main is
  `12bd91b66d7fdb5155a8e380eabc807aa8017cf1`, activating the three audited PBM
  scorer handoffs.
- `generate_baselines_mila` main is
  `a455000568f70506d4501d62f32c7c3a24e6fd53`, adding the smoke-gated PBM
  transformer generators.
- `bayes_efficiency_mila` main remained
  `d37703d59b76d047971a6fcf130e58c6f8c88aee`.
- `child_complexity_predictors` main remained
  `33497c2189d28543a0f2280a5fff227d37c87dcb`.

The old three-model relocation-only commit was preserved on its branch but not
integrated because it describes a retired old-laptop worktree path.

## Verification record and known portability debt

- `generate_baselines_mila`: 23 tests passed, 2 skipped.
- `compute_surprisal_mila`: the 11 directly affected LSTM/transformer tests
  passed; the seven new transformer tests pass after the branch-independent
  test repair.
- The complete compute suite ran 374 tests and retained the same 9 failures
  and 2 errors observed on the untouched pre-integration main. These are
  pre-existing portability failures involving the dead laptop's
  `/home/apaixonada/.codex/skills/...` path, a missing checkout-local `.venv`,
  and retired TinyDialogues branch-name guards. The integration did not add a
  full-suite regression, but this portability debt must be repaired before
  calling the compute checkout fully machine-independent.
- `developmental_word_information` was a documentation-only fast-forward and
  passed `git diff --check`.

No Mila job, model download, data transformation, or scientific analysis was
run as part of this Git operation.

## Correct re-entry on this or another machine

1. Clone current repositories from GitHub into an internal ext4 code directory.
   Do not develop inside the old copied T7 Git metadata.
2. Run `git fsck --full` and record each `main` SHA after cloning.
3. Mount the T7 and discover the current sibling-repository root.
4. Point configurable input paths or deliberate symlinks from the local code
   checkouts to the audited T7 products. Never replace canonical T7 products.
5. Create a minimal environment only after dependency and cache sizes are
   estimated. Keep model caches and large outputs off the PC by default.
6. Write new outputs to a new, explicitly named run directory. Never overwrite
   raw CHILDES/CHAT data or an immutable audited handoff.
7. Use Git only for code, tests, configuration, Markdown, and lightweight
   metadata. Use `rsync`/Globus only for explicitly selected data products.

For an emergency bundle check:

```bash
git bundle verify /path/to/repository_all_refs_pre_remote_2026-09-02.bundle
git bundle list-heads /path/to/repository_all_refs_pre_remote_2026-09-02.bundle
```

For ordinary work, GitHub `main` is authoritative after verifying its live SHA;
the bundles are recovery artifacts, not the day-to-day remote.
