# Eva Portelance project recovery and portability guide

Date prepared: 2026-09-02  
External drive audited: `/media/alkan/T7/EvaPortelance/Projet_1`  
Main analysis repository: `communicative_efficiency`

## Purpose

This guide explains how to resume the communicative-efficiency project on a
new computer without copying every old result from the T7 drive.

The project has three different things that must not be confused:

1. **Git repositories** contain code, tests, configurations, and
   documentation. Recover these with Git.
2. **Portable working data** contain cleaned data and current analysis-ready
   tables. Transfer these with `rsync` to a computer where analyses will run.
3. **Expensive archival outputs** contain large neural-model scoring results.
   Keep one verified central copy and transfer them to a workstation only when
   an analysis actually needs the raw scores.

Nothing in this guide is authorization to delete data. Complete and verify at
least one independent backup before considering deletion from the T7.

## Big-picture storage plan

| Tier | Approximate size | Where it should live |
|---|---:|---|
| Portable working data | 17 GB | Every active analysis computer |
| Immutable raw/source backup | 2.5 GB | At least two independent locations |
| Expensive scored archives | 59 GB | One central working archive plus one backup |
| Current fitted-result state | About 2 GB beyond the working tables | Central archive; copy when exact fitted objects/draws are needed |

The current T7 contains substantially more because several runs retain both a
compressed archive and a fully extracted copy, and because historical
preprocessing variants and smoke outputs remain present.

## Required directory layout on a new computer

Keep the active repositories as siblings. This lets relative links work on any
machine regardless of username or home-directory location.

```text
Projet_1/
|-- communicative_efficiency/
|-- compute_surprisal_mila/
|-- developmental_word_information/
|-- generate_baselines_mila/
|-- bayes_efficiency_mila/
`-- child_complexity_predictors/
```

Avoid encoding paths such as `/home/apaixonada/...` in new scripts or links.

## Part 1: Restore and verify Git first

### Current audited local Git state

The local Git references on the T7 reported the following state during the
2026-09-02 read-only audit:

| Repository | Active branch | Commit | Cached upstream state |
|---|---|---|---|
| `communicative_efficiency` | `main` | `044a396f831989c16b564c5985f5c6e40a0a6bbd` | synchronized |
| `compute_surprisal_mila` | `main` | `e94f0758765c936704b746e44e0181493a14b71d` | synchronized |
| `developmental_word_information` | `agent/activate-three-scorer-handoffs` | `12bd91b66d7fdb5155a8e380eabc807aa8017cf1` | synchronized |
| `generate_baselines_mila` | `main` | `a1bef2980d46269f34c24afc6134c00f33cfa858` | synchronized |
| `bayes_efficiency_mila` | `main` | `d37703d59b76d047971a6fcf130e58c6f8c88aee` | synchronized |
| `child_complexity_predictors` | `main` | `33497c2189d28543a0f2280a5fff227d37c87dcb` | synchronized |

There were zero untracked files and zero content changes in these six active
checkouts. Hundreds of files appeared modified only because the external-drive
filesystem exposed ordinary files as executable (`644 -> 755`). Do not commit
those permission-only changes.

### Remove external-drive permission noise

Run once in each checkout that resides on the T7:

```bash
git config core.filemode false
```

This changes only the local repository configuration. It does not change
project content or publish anything.

### Live remote audit before pushing

The cached remote-tracking references were synchronized, but GitHub could not
be queried reliably during the audit. On a computer with GitHub access, run:

```bash
PROJECT_ROOT=/path/to/Projet_1

for repo in \
  communicative_efficiency \
  compute_surprisal_mila \
  developmental_word_information \
  generate_baselines_mila \
  bayes_efficiency_mila \
  child_complexity_predictors
do
  git -C "$PROJECT_ROOT/$repo" fetch --prune origin
  git -C "$PROJECT_ROOT/$repo" status --short --branch
  git -C "$PROJECT_ROOT/$repo" rev-list --left-right --count 'HEAD...@{upstream}'
  git -C "$PROJECT_ROOT/$repo" push --dry-run
done
```

Interpret `rev-list` as:

```text
LOCAL_ONLY_COMMITS    REMOTE_ONLY_COMMITS
```

The ideal result is `0  0`.

### One relevant local-only branch to preserve

The compute repository contains one relevant local-only commit:

```text
branch: codex/cross-population-scoring
commit: 32acbc06108f5691162da8f022d501e24202b95f
change: extends the documented SSH ControlPersist window from 72 hours to 7 days
```

Publish the branch after confirming the remote audit:

```bash
git -C "$PROJECT_ROOT/compute_surprisal_mila" \
  push --dry-run -u origin codex/cross-population-scoring

git -C "$PROJECT_ROOT/compute_surprisal_mila" \
  push -u origin codex/cross-population-scoring
```

Publishing the branch preserves the commit. Do not automatically merge it into
`main`; first decide whether a seven-day SSH control socket is still desired.

Do not publish or merge local commit `775fe190e45d4cb3108e8dd95afdaa7f671f3254`
from `codex/three-model-surprisal-schema`. It only records an old worktree
relocation and now describes the production state incorrectly.

The branch `agent/august-supervisor-report-v1` appears three commits ahead of
its own old branch upstream, but all three commits are already contained in
`origin/main`. It does not require another push.

### Clone the repositories on a new computer

```bash
NEW_ROOT=/path/on/new/computer/Projet_1
mkdir -p "$NEW_ROOT"

git clone git@github.com:NicolasGoulet/communicative_efficiency.git \
  "$NEW_ROOT/communicative_efficiency"
git clone git@github.com:NicolasGoulet/compute_surprisal_mila.git \
  "$NEW_ROOT/compute_surprisal_mila"
git clone git@github.com:NicolasGoulet/developmental_word_information.git \
  "$NEW_ROOT/developmental_word_information"
git clone git@github.com:NicolasGoulet/generate_baselines_mila.git \
  "$NEW_ROOT/generate_baselines_mila"
git clone git@github.com:NicolasGoulet/bayes_efficiency_mila.git \
  "$NEW_ROOT/bayes_efficiency_mila"
git clone git@github.com:NicolasGoulet/child_complexity_predictors.git \
  "$NEW_ROOT/child_complexity_predictors"
```

Activate the word-analysis branch:

```bash
git -C "$NEW_ROOT/developmental_word_information" \
  switch --track origin/agent/activate-three-scorer-handoffs
```

Do not copy `.git` directories or old `.worktrees` by drag-and-drop when a
fresh clone is possible.

### Optional offline Git backup

If GitHub is unavailable, a Git bundle can preserve every branch and tag until
network access returns:

```bash
mkdir -p "$NEW_ROOT/git-bundles"

for repo in \
  communicative_efficiency \
  compute_surprisal_mila \
  developmental_word_information \
  generate_baselines_mila \
  bayes_efficiency_mila \
  child_complexity_predictors
do
  git -C "$PROJECT_ROOT/$repo" bundle create \
    "$NEW_ROOT/git-bundles/$repo.bundle" --all
  git bundle verify "$NEW_ROOT/git-bundles/$repo.bundle"
done
```

## Part 2: Data to transfer to every active analysis computer

The following approximately 17 GB constitute the recommended data-only
working set. Small manifests, schemas, and stage-specific audits located next
to these data should travel with them.

### A. Current cleaned data

```text
communicative_efficiency/data/preprocessed_data/
communicative_efficiency/data/preprocessed_clinical_data/
communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

The `default_naturalistic_merged_006_023` bundle is the active 79-child
strict-naturalistic bundle.

### B. Frozen inputs for pending or reusable computation

```text
communicative_efficiency/results/cross_population_scoring_handoff/
  cross_population_child_scoring_20260826_v1.tar.gz
  cross_population_child_scoring_20260826_v1.tar.gz.sha256

communicative_efficiency/results/transformer_training_expansion/full_20260825/

communicative_efficiency/results/downstream_caregiver_response_handoff/
  downstream_caregiver_response_utility_full79_20260827_v1.tar.gz
  downstream_caregiver_response_utility_full79_20260827_v1.tar.gz.sha256

compute_surprisal_mila/mila_results/lstm_full79_mistral_scoring/
  20260825_lstm_full79_mistral_boundary_repair_7298e22_v1/immutable_handoff/
```

The full-79 LSTM immutable handoff is complete and audited but has not yet been
ingested into the fixed-effort all-79 cloud analysis. Do not rerun its Mila
generation or scoring.

### C. Current utterance-level analysis tables

```text
communicative_efficiency/results/direct_surprisal_replication/mistral_full79/
  child_direct_surprisal_wide.csv.gz
  caretaker_direct_surprisal_wide.csv.gz
  manifest.json
  source_file_audit.csv

communicative_efficiency/results/direct_surprisal_replication/tinydialogues_pbm/
  child_direct_surprisal_wide.csv.gz
  caretaker_direct_surprisal_wide.csv.gz
  route1_scored_utterance_effort_long.csv.gz
  manifest.json
  source_file_audit.csv
  route1_source_file_audit.csv

communicative_efficiency/results/direct_surprisal_replication/paired_tiny_mistral_pbm/
  paired_direct_surprisal_wide.csv.gz
  join_audit.json

communicative_efficiency/results/route1_analysis_dataset/
  route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz
  with_lstm_schema.json
  with_lstm_source_file_audit.csv
  with_lstm_context_entropy_join_audit.csv
  with_lstm_variant_context_audit.csv
```

The 2.6 GB Route 1 `context_entropy_with_lstm` file is the final combined table.
It supersedes the 6.1 GB plain CSV and the earlier 1.8 GB and 2.0 GB
intermediate tables.

### D. Current analysis-ready extensions

```text
communicative_efficiency/results/full79_information_effort_clouds/
  datasets/
  metrics/
  schemas/
  audit/

communicative_efficiency/results/full79_joint_efficiency_analysis/
  datasets/
  metrics/
  audit/

communicative_efficiency/results/utterance_informativity_analysis/datasets/

communicative_efficiency/results/bayesian_route1_route2_20260828/
  datasets/
  contract/
  audit/

communicative_efficiency/results/bayesian_joint_adaptive_efficiency_20260828/
  datasets/
  contract/
  audit/

communicative_efficiency/results/bidirectional_dyadic_efficiency_20260829/
  datasets/
  frequentist-input/
  parent-role/
  contract/
  final_audit.json

communicative_efficiency/results/hall_snapshot_analysis/
  prepared/
  archive_audit/
  final/

communicative_efficiency/results/corrected_pbm_bayes_v2/
  inputs/
  scores/
  manifests/

communicative_efficiency/results/mila_modular_runs_2026_07_08/products/
  pbm_complexity_predictors/
  full79_lstm_reports/

communicative_efficiency/results/downstream_caregiver_response_analysis/
  datasets/
  final_audit.json
```

Whole-analysis completion markers are valid only when the complete result
directory is present. If transferring only data subdirectories, rely on their
stage manifests and do not treat a copied root-level completion marker as proof
that models, diagnostics, plots, and reports were also transferred.

### E. Current PBM word-level data

For each of the three scorer directories below, transfer the complete modular
analysis directory. The non-data files are small, and keeping the complete
directory preserves the meaning of `COMPLETE_AND_AUDITED`.

```text
developmental_word_information/results/modular_analysis/mistral_pbm21/
developmental_word_information/results/modular_analysis/qwen_pbm21/
developmental_word_information/results/modular_analysis/tinydialogues_pbm21/
```

These total approximately 1.6 GB and are sufficient for current word-level
modeling. The three much larger raw word-score archives belong in the central
archive tier.

## Part 3: Immutable raw/source backup

Retain these in at least two independent locations:

```text
communicative_efficiency/data/raw_data/
communicative_efficiency/data/zip_files/
```

Together they are approximately 2.5 GB. `raw_data` contains extracted source
material not completely represented by `zip_files`, while `zip_files` retains
many original downloaded archives.

They need not be installed on every analysis laptop if the prepared working
set is available.

## Part 4: Expensive scored outputs to retain centrally

These approximately 59 GB should have one central copy and one verified
backup. Prefer compressed archives plus checksums and audit metadata instead
of simultaneously storing compressed and extracted copies.

### Full-79 direct Mistral

```text
compute_surprisal_mila/mila_results/production_runs/
  naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/
  20260713_162955/
    naturalistic_79_children_fp16_scored_csvs.tar.gz
    COMPLETE
```

The archive is approximately 2.1 GB. The extracted `scored_csvs/` tree is
approximately 12.9 GB and need not be transferred when the archive is retained.

### TinyDialogues PBM utterance scoring

```text
compute_surprisal_mila/mila_results/tinydialogues_pbm_production/20260717_201227/
  *.tar.gz
  PBM_COMPLETE
  LOCAL_RETRIEVAL_AUDIT_PASSED
  manifests/
  local_retrieval_audit/
```

The archive is approximately 1.6 GB. Its extracted scores account for most of
the 13 GB run directory.

### All-79 Qwen response space scored by Mistral

```text
compute_surprisal_mila/mila_results/qwen_response_mistral_full_scoring/
  20260817_qwen_response_mistral_full75_smoke_f5dd5aa_v1/
    qwen_response_mistral_core75_*.tar.gz
    qwen_response_mistral_core75_*.tar.gz.sha256
    qwen_response_mistral_extension25_*.tar.gz
    qwen_response_mistral_extension25_*.tar.gz.sha256
```

Keep both core75 and extension25 archives. Together they reconstruct the full
100 responses per context. Their combined archive size is approximately
5.5 GB. The `extracted_run/` tree is not required in the central archive when
both archives and checksums are retained.

### Three PBM word-surprisal archives

```text
compute_surprisal_mila/mila_results/crossmodel_word_surprisal/
  20260730_tinydialogues_pbm21_production_e890ec1_v1/*.tar.gz*
  20260731_mistral_pbm21_production_e890ec1_v1/*.tar.gz*
  20260803_qwen3_14b_pbm21_batch16_persistent_production_c82d219_v1/*.tar.gz*
```

These archives total approximately 46 GB and are the largest irreducible
central data asset. Each run directory currently also contains an extracted
copy, which is why the full `crossmodel_word_surprisal` directory occupies
about 90 GB.

### Downstream caregiver-response scoring

```text
compute_surprisal_mila/mila_results/downstream_caregiver_response_surprisal/
  20260831_123914/*.tar.gz
```

Keep all three scorer archives: Mistral, Qwen3-14B, and TinyDialogues. Their
expected sizes and SHA-256 hashes are recorded in
`communicative_efficiency/configs/downstream_caregiver_response_score_import_20260831.json`.
The extracted copies are redundant after the archives are verified.

### Hall, context entropy, held-out scores, and PBM LSTM scores

```text
compute_surprisal_mila/mila_results/hall_snapshot_mistral/
  20260813_hall_snapshot_mistral_word_smoke_66812c4_v1/*.tar.gz*

compute_surprisal_mila/mila_results/context_entropy_mistral/

compute_surprisal_mila/results/
  raw_surprisal_lstm_additive_pbm_006_065_k3_k4_k5_same_length/

communicative_efficiency/results/external/compute_surprisal_mila/
  raw_surprisal_heldout_real_child_generalization_2026-06-16/
```

There are currently two copies of the PBM LSTM scored directory: one under the
compute repository and one under the analysis repository's `results/external`
directory. Retain the compute-repository copy as canonical.

## Part 5: Data and directories that do not need migration

Do not transfer the following to a new working computer:

```text
communicative_efficiency/data/OLD/
communicative_efficiency/data/nltk_data/
communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_bin6/
communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_custom_early20k/
```

Also omit:

- `route1_scored_utterance_effort_long.plain.csv`;
- older Route 1 `with_lstm` and `context_entropy` intermediate tables;
- smoke runs and old exploratory response-entropy grids;
- the older PBM-only Mistral-generated response-space products when doing
  current all-79 Qwen response-space work;
- `results/downstream_caregiver_response_mila_bundle_20260827_v1/`, because it
  duplicates the archive in `results/downstream_caregiver_response_handoff/`;
- extracted cross-population handoff contents when its tarball and checksum
  are retained for transport;
- extracted score trees when the corresponding verified archive is retained;
- `.venv`, `.cmdstan`, `.bayes-r-lib`, caches, logs, and downloaded model
  caches;
- copied `.worktrees`; recreate only active worktrees from Git branches;
- old top-level projects such as `old_results`, `old_figs`,
  `BACK_UP_SURPRISAL_COMPUTING`, and `surprisal_computing` as part of the new
  active layout. Keep them untouched on the T7 until the new backup has been
  validated.

## Part 6: Transfer procedure with rsync

Use `rsync`, not manual drag-and-drop. The examples intentionally omit
`--delete`.

### Define the roots

```bash
T7_ROOT=/media/alkan/T7/EvaPortelance/Projet_1
NEW_ROOT=/path/on/new/computer/Projet_1
mkdir -p "$NEW_ROOT"
```

### Transfer the core prepared data

Always perform a dry run first by using `-n`:

```bash
rsync -rltvhn --relative \
  "$T7_ROOT/./communicative_efficiency/data/preprocessed_data/" \
  "$T7_ROOT/./communicative_efficiency/data/preprocessed_clinical_data/" \
  "$T7_ROOT/./communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/" \
  "$NEW_ROOT/"
```

If the destination paths look correct, remove `n` and run the transfer:

```bash
rsync -rltvhP --relative \
  "$T7_ROOT/./communicative_efficiency/data/preprocessed_data/" \
  "$T7_ROOT/./communicative_efficiency/data/preprocessed_clinical_data/" \
  "$T7_ROOT/./communicative_efficiency/data/big_cleaned_dataset/default_naturalistic_merged_006_023/" \
  "$NEW_ROOT/"
```

`-P` shows progress and retains partial transfers so interrupted large copies
can resume.

### Transfer data-bearing result directories

Use the same `--relative` pattern. For example:

```bash
rsync -rltvhP --relative \
  "$T7_ROOT/./communicative_efficiency/results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz" \
  "$T7_ROOT/./communicative_efficiency/results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz" \
  "$T7_ROOT/./communicative_efficiency/results/direct_surprisal_replication/mistral_full79/manifest.json" \
  "$T7_ROOT/./communicative_efficiency/results/direct_surprisal_replication/mistral_full79/source_file_audit.csv" \
  "$T7_ROOT/./communicative_efficiency/results/full79_information_effort_clouds/datasets/" \
  "$T7_ROOT/./communicative_efficiency/results/full79_information_effort_clouds/metrics/" \
  "$T7_ROOT/./communicative_efficiency/results/full79_information_effort_clouds/schemas/" \
  "$T7_ROOT/./communicative_efficiency/results/full79_information_effort_clouds/audit/" \
  "$T7_ROOT/./communicative_efficiency/results/full79_joint_efficiency_analysis/datasets/" \
  "$T7_ROOT/./communicative_efficiency/results/full79_joint_efficiency_analysis/metrics/" \
  "$T7_ROOT/./communicative_efficiency/results/full79_joint_efficiency_analysis/audit/" \
  "$NEW_ROOT/"
```

Repeat using the remaining paths in Part 2. Keeping several bounded commands
is preferable to one enormous command because it makes failures easier to
diagnose and resume.

### Transfer an expensive archive on demand

```bash
rsync -rltvhP --relative \
  "$T7_ROOT/./compute_surprisal_mila/mila_results/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/naturalistic_79_children_fp16_scored_csvs.tar.gz" \
  "$NEW_ROOT/"
```

### Verify a completed directory transfer

Run the same command with dry-run plus checksumming:

```bash
rsync -rltvhnc --relative \
  "$T7_ROOT/./communicative_efficiency/data/preprocessed_data/" \
  "$NEW_ROOT/"
```

No listed changes means the source and destination contents agree. Checksum
comparison reads both copies and can therefore take time.

### Verify archive hashes

For an archive with a sidecar, print both hashes:

```bash
sha256sum /path/to/archive.tar.gz
head -c 64 /path/to/archive.tar.gz.sha256
printf '\n'
```

The two 64-character hashes must match. Some existing sidecars contain old
absolute Mila paths, so direct `sha256sum -c` may fail only because the stored
filename is no longer valid. Comparing the hash fields remains valid.

### Known checksum gaps

Before calling the central archive complete, create sidecars for:

1. `naturalistic_79_children_fp16_scored_csvs.tar.gz`;
2. the TinyDialogues PBM utterance-scoring archive.

After obtaining permission to write:

```bash
cd /path/containing/archive
sha256sum archive.tar.gz > archive.tar.gz.sha256
```

The full-79 LSTM product hash is already recorded in its immutable manifest:

```text
03af2bc6abbca362eb9c7529b921e84048d65f68f6c950b841384e187271345e
```

## Part 7: Restore portable relative links only when needed

The current T7 analysis repository does not contain the set of external
symlinks described in `AGENTS.md`; only two older external directories are
present there. The actual current handoffs live in the sibling compute
repository.

After archives have been extracted on a new computer, create relative links,
not links containing a username-specific `/home/...` path.

Example for the full-79 direct scores:

```bash
LINK_ROOT="$NEW_ROOT/communicative_efficiency/results/external/compute_surprisal_mila"
mkdir -p "$LINK_ROOT"

ln -s \
  ../../../../compute_surprisal_mila/mila_results/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/scored_csvs \
  "$LINK_ROOT/raw_surprisal_cleaned_naturalistic_79_children_all_available_ages_fp16"
```

Before creating a link, confirm that the target directory exists and that no
file, directory, or link already occupies the destination name.

The documented full-79 LSTM `current` symlink is absent on the T7. Use the
immutable versioned path as the source of truth until a portable relative
`current` link is deliberately created.

## Part 8: Recreate only active worktrees

Old worktree registrations point into the dead laptop's
`/home/apaixonada/...` paths. Fresh clones will not contain those stale
registrations.

The two currently relevant PBM-transformer branches are already published:

```text
generate_baselines_mila: codex/pbm-transformer-generators
compute_surprisal_mila:  codex/pbm-transformer-mistral-scoring
```

If that experiment resumes, recreate the worktrees:

```bash
git -C "$NEW_ROOT/generate_baselines_mila" worktree add --track \
  -b codex/pbm-transformer-generators \
  "$NEW_ROOT/communicative_efficiency/.worktrees/generate-pbm-transformers" \
  origin/codex/pbm-transformer-generators

git -C "$NEW_ROOT/compute_surprisal_mila" worktree add --track \
  -b codex/pbm-transformer-mistral-scoring \
  "$NEW_ROOT/communicative_efficiency/.worktrees/score-pbm-transformers" \
  origin/codex/pbm-transformer-mistral-scoring
```

Do not recreate historical identity-fix, storage-inventory, or three-model
schema worktrees merely because stale registrations exist.

## Part 9: Final verification checklist

Before declaring a new computer ready:

- [ ] All six repositories clone successfully.
- [ ] The expected branches and commits are available.
- [ ] `git status --short` shows no content changes.
- [ ] Permission-only noise is handled with `core.filemode=false` where needed.
- [ ] The active merged big-cleaned bundle is present.
- [ ] Both all-79 Mistral wide tables are present.
- [ ] The final PBM Route 1 context-entropy-plus-LSTM table is present.
- [ ] Full-79 cloud and joint-analysis data tables are present.
- [ ] The downstream utility tables are present.
- [ ] The three modular PBM word-analysis products are present.
- [ ] The full-79 LSTM immutable handoff is present and its hash agrees.
- [ ] The cross-population and transformer-training frozen inputs are present.
- [ ] `rsync -nrc` reports no differences for transferred data.
- [ ] Large archives are verified against SHA-256 values.
- [ ] No absolute symlink still points to `/home/apaixonada/...`.
- [ ] No cleanup or deletion begins until a second independent backup passes
      verification.

## Documentation corrections to make later in the repository

The repository's agentic documentation should eventually record:

1. this three-tier portability policy and its concrete allow-lists;
2. the use of sibling-relative paths rather than `/home/apaixonada/...`;
3. that the documented external handoff links are absent on the T7;
4. that the versioned full-79 LSTM handoff exists but its `current` link is
   absent;
5. archive-versus-extracted redundancy rules;
6. the two checksum-sidecar gaps;
7. the external-drive `core.filemode` issue;
8. that downstream caregiver-response utility is complete and audited, even
   though one later priority paragraph still calls it gated.

This guide is an external operational note. It does not itself alter the
repository's scientific contracts, results, or completion markers.
