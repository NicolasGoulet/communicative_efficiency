# Hall Cross-Sectional Snapshot: Preprocessing and Analysis Plan

Design frozen on 2026-08-10; scoring and analysis completed and audited on
2026-08-17. The sample-selection decisions below were made without reading a
Hall surprisal outcome.

## Why Hall is a separate study

Hall is useful precisely because it is not another developmental trajectory.
It samples children at approximately age four across home, school, and
transition settings, and its CHAT metadata contains historical race and
social-class strata. The corpus documentation is available from the
[official CHILDES Hall page](https://talkbank.org/childes/access/Eng-NA/Hall.html)
and the [original project report](https://talkbank.org/childes/access/Eng-NA/0docs/Hall1979.pdf).

Hall must not be appended to the 79-child longitudinal age-slope sample. Its
main estimand is a cross-sectional difference at a narrow developmental
snapshot, with children—not utterances—as the independent sampling units.

## Existing individual trajectories

The longitudinal side is already complete enough for comparison:

- Mistral: all 79 children, including separate PBM and 58-child non-PBM
  profiles, in
  `results/direct_surprisal_replication/mistral_full79/modular/models/child_profile_audit.csv`;
- TinyDialogues: 21 PBM child profiles in
  `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/child_profile_audit.csv`;
- paired TinyDialogues/Mistral: 21 paired child trajectories in
  `results/direct_surprisal_replication/paired_tiny_mistral_pbm/trajectories/paired_child_profile_audit.csv`.

The human-facing Mistral gallery is `docs/mistral_full79_child_gallery.html`.
These trajectories remain available, but Hall comparisons will use one locked
age-matched session per eligible longitudinal child.

## Audited Hall data contract

Raw source: `data/raw_data/Hall/`.

Prepared source: `data/preprocessed_data/Hall/`.

Builder: `src/prepare_hall_snapshot.py`.

Compact audited products:

- `results/hall_snapshot_preprocessing/hall_preprocessing_audit.json`;
- `results/hall_snapshot_preprocessing/hall_file_inventory.csv`;
- `results/hall_snapshot_preprocessing/hall_child_metadata.csv`;
- `results/hall_snapshot_preprocessing/hall_child_snapshot_scoring.csv`.

The audit covers 40 source files and 238,249 CHAT main tiers. Every child
directory contains `chi.csv`, family-only `caretakers.csv`, all-adult
`adult_interlocutors.csv`, and lossless `all_speakers.csv`. The latter retains
speaker code and role, active situation text and an automatic setting label,
raw and cleaned text, source line, and previous-turn role.

### Locked samples

| Sample | Children | Scorable child utterances | Rule |
| --- | ---: | ---: | --- |
| Primary | 36 | 70,510 | Valid transcript and child-specific race/class in the CHI `@ID` or metadata table |
| Sensitivity | 37 | 71,830 | Primary plus `rog`, whose Black/WC stratum is inferred from the source folder |
| Excluded inventory | 3 | 0 | `grc` and `lea` are missing-transcript placeholders; `brh` is unrevised ASR with no identified CHI tier |

The primary strata contain 11 Black/UC, 9 Black/WC, 8 White/UC, and 8
White/WC children. `UC` and `WC` are preserved as historical corpus codes.
They are not converted into continuous SES, household income, or parental
education.

The 37-child scoring-ready table has 45,921 home, 20,155 school, 4,659
transition, and 1,095 other-setting child utterances. It records 33,030 child
turns immediately following an adult. Context k1–k3 is defined as the previous
one to three nonempty adult-interlocutor utterances within the same recorded
situation; situation boundaries reset context.

## Frozen snapshot comparison

Builder: `src/build_hall_snapshot_comparator.py`.

The comparator is selected without reading a surprisal outcome. The Hall
primary median is 57 months. Among the existing Mistral children, the rule
keeps each child's single recorded session nearest 57 months within
54 <= age < 60 months. The passed manifest contains 20 children: 18 non-PBM
and 2 PBM. Eleven are from Wells, so the external comparison is a guarded
descriptive sensitivity, not a clean cohort effect.

Outputs:

- `results/hall_snapshot_preprocessing/hall_comparison_snapshot_manifest.csv`;
- `results/hall_snapshot_preprocessing/hall_comparison_snapshot_audit.json`.

## Completed analysis sequence

1. Primary within-Hall outcome: unconditional Mistral utterance surprisal k0,
   modeled at exact/top-coded word effort using race, class, their interaction,
   and setting. Use child-clustered uncertainty and child-level resampling.
2. Secondary within-Hall outcome: contextual k3 surprisal and context gain,
   restricted first to child turns immediately following an adult. Preserve
   adult role and setting; do not call every adult a caregiver.
3. Sensitivities: add the 37th folder-inferred child; fit home and school
   separately; compare exact-effort cells; add sex only as a secondary control;
   audit leave-one-child influence and setting-class support.
4. External snapshot: compare Hall with the locked 20-child, one-session
   Mistral manifest at fixed effort. Keep PBM/non-PBM labels and corpus
   influence visible. Do not interpret the cohort coefficient causally.
5. Report race/class contrasts as scorer-indexed descriptive differences.
   Dialect, recording era, geography, setting, transcription, and language-
   model training representation can all affect Mistral scores. No group should
   be described as linguistically deficient or inherently less efficient.

No Hall model was fit until the score archive passed row-identity, target-text,
context, blank-score, artifact-hash, and model/revision audits.

## Completed scoring and analysis

The retrieved 455,153,574-byte archive has SHA-256
`c7c2422f19f87a0096136f73bf3a1fa664f5551ed095371920b3462db6d21202`.
The independent local relocation audit passed 4/4 k0–k3 contracts with
287,320 utterance rows, 1,182,476 word rows, 1,769,650 token rows, 1,461,794
token-to-word allocation rows, zero truncated contexts, and zero problems.
The 1,812 contextless rows in each nonzero context retain
`context_available=false` and pass the calibrated target-only equivalence
gate.

The modular local workflow fit 20/20 registered models, wrote 72 registered
contrasts, completed 21,000 bootstrap contrast draws across five primary
model families, retained 547 leave-one-child/corpus estimates, and audited
9/9 figures. The final marker is
`results/hall_snapshot_analysis/final/ANALYSIS_COMPLETE_AND_AUDITED`.

The primary unconditional k0 race-by-class interaction is -3.516 bits
(child-clustered 95% CI [-5.730, -1.302]; stratified child-bootstrap interval
[-5.752, -1.264]). Within WC, the Black-minus-White contrast is +3.077 bits;
within UC it is -0.439 bits with an interval crossing zero. The adult-adjacent
k3 interaction is -3.249 bits, while the corresponding k0-minus-k3
context-support interaction is -0.213 bits with an interval crossing zero.
This separation suggests that the group pattern is in Mistral target
predictability rather than a clear difference in contextual support.

The locked Hall-minus-current k0 contrast is +3.037 bits at fixed word count
(95% CI [2.041, 4.032]; bootstrap [2.096, 3.978]). It remains positive when
each current corpus is omitted, but it is a guarded domain/era/dialect/
transcription comparison, not a causal cohort effect. Full interpretation and
plots are in `docs/hall_snapshot_mistral_analysis.html`.

## Mila handoff

The original local immutable input handoff remains under
`results/scoring_bundles/hall_snapshot_mistral_real_k0_k3_v1/`. Its archive is
2,520,424 bytes with SHA-256
`23ca951da9912ea3d46235821cd877c972e7397acd64054ae5dff7d6125544a0`.
It defines four contracts and 287,320 expected scored rows. The sibling compute
implementation prompt is preserved at
`docs/compute_surprisal_mila_hall_prompt_2026-08-10.md` as provenance.

## Reproduce the local stages

```bash
.venv/bin/python -m unittest \
  tests.test_prepare_hall_snapshot \
  tests.test_build_hall_snapshot_comparator

.venv/bin/python src/prepare_hall_snapshot.py
.venv/bin/python src/build_hall_snapshot_comparator.py
.venv/bin/python src/build_hall_mila_handoff.py

.venv/bin/python src/audit_hall_scored_archive.py \
  --archive results/external/compute_surprisal_mila/hall_snapshot_mistral_word_surprisal_20260813_66812c4/hall_snapshot_mistral_real_k0_k1_k2_k3_word_surprisal_20260813_hall_snapshot_mistral_word_smoke_66812c4_v1.tar.gz \
  --output-dir results/hall_snapshot_analysis/archive_audit

MPLCONFIGDIR=/tmp/mpl-cache .venv/bin/python \
  src/build_hall_snapshot_analysis.py --stage all
```
