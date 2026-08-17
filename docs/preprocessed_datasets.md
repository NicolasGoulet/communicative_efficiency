# Currently Preprocessed Datasets

Last checked: 2026-08-10.

This file describes the datasets currently present under
`data/preprocessed_data/`. A dataset is considered **Stage 0 preprocessed** when
it has per-child `chi.csv` and `caretakers.csv` files produced from CHAT
transcripts.

Important distinction:

- `chi.csv` / `caretakers.csv`: cleaned utterance files; ready for utterance
  distribution plots and other analyses that use real cleaned utterances.
- `chi.ngram_generated.csv`: matched-length random, unigram, bigram, and
  trigram generated utterances.
- `chi.shared_caretaker_contexts.csv`: child rows with shared caretaker context
  windows.
- `chi.surprisal_scoring.csv`: compact child-side file for surprisal scoring.

The expanded strict naturalistic corpora are Stage 0 preprocessed, but the
downstream generated/context/scoring files have not yet been regenerated for
them.

Update 2026-05-25: the strict naturalistic corpora have now also been exported
to a separate consolidated folder at
`data/big_cleaned_dataset/default_naturalistic_bin6/`. This folder is generated
by `src/create_big_cleaned_dataset.py` and should be treated as the current big
cleaned scoring bundle. It preserves copied Stage 0 `chi.csv` and
`caretakers.csv` files, builds additive 6-month n-gram dictionaries over the
selected strict naturalistic corpora, generates matched-length random/unigram/
bigram/trigram child baselines, adds `context_k1`, `context_k2`, and
`context_k3`, and writes compact child/caretaker surprisal-scoring CSVs. The
compact child scoring files require all four baseline columns to be present; the
copied Stage 0 files still retain rows whose missing age prevents baseline
generation.

Update 2026-05-25, later: because the earliest 6-month bins were sparse, a
second consolidated scoring bundle was generated at
`data/big_cleaned_dataset/default_naturalistic_custom_early20k/`. It uses the
same strict naturalistic corpora and same output schema as the bin-6 bundle, but
its additive n-gram dictionaries use custom age bins. The first bin starts at
`006-017` and expands by one month at a time until reaching at least 20,000
child utterances. In the current data, `006-018` has 16,980 child utterances and
`006-019` has 22,529, so the final custom bins are `006-019`, `020-023`,
`024-029`, `030-035`, `036-041`, `042-047`, `048-053`, `054-059`, and
`060-065`. The custom-binned distribution tables and plots are under
`figs/big_cleaned_dataset/default_naturalistic_custom_early20k/`, with a PBM-only
version under `figs/big_cleaned_dataset/providence_brown_manchester_custom_early20k/`.

Update 2026-05-26: the active generated-baseline bundle for future strict
naturalistic n-gram/random work is now
`data/big_cleaned_dataset/default_naturalistic_merged_006_023/`. This keeps the
same strict naturalistic corpora and output schema, but uses one first additive
dictionary bin, `006-023`, followed by the previous 6-month bins:
`024-029`, `030-035`, `036-041`, `042-047`, `048-053`, `054-059`, and
`060-065`. The later additive dictionaries are byte-identical to the
`default_naturalistic_custom_early20k` dictionaries from `024-029` onward,
because both strategies have accumulated the same months by that point.

For the already-scored Providence/Brown/Manchester run, only the generated
baseline utterances for floor-age months `006-023` need rescoring. A small
PBM-only rescoring bundle was written to
`results/rescoring_subsets/pbm_006_023_merged_early_baselines/` and packaged as
`results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_2026-05-26.tar.gz`.
It contains scorer-compatible shards for `random_chi/bin6`,
`unigram_chi/bin6`, `bigram_chi/bin6`, and `trigram_chi/bin6` only.

## Corpus Groups

The current auditable grouping file is
`results/corpus_groups/dataset_group_assignments.csv`.

- `naturalistic_caregiver_child`: longitudinal naturalistic caregiver-child
  interaction corpora. These are the current strict default for naturalistic
  analyses.
- `caregiver_child_structured_observation`: non-clinical caregiver-child data
  that should be kept separate from the stricter naturalistic default.
- `clinical_probe`: clinical or probe-style data that should be kept separate
  from naturalistic caregiver-child analyses.
- `unassigned`: present in `data/preprocessed_data/` but not yet assigned in
  the grouping file.
- `cross_sectional_sociolinguistic_snapshot`: Hall's age-four, multi-setting
  cross-sectional design. It is excluded from the longitudinal strict default.

## Current Summary

Counts below are row counts after Stage 0 preprocessing. `child_nonempty` and
`caretaker_nonempty` count rows whose `utterance_clean` is not blank. Missing age
counts are rows where `age_months` is blank. Row-width and blank-header checks
are CSV sanity checks.

| Dataset | Group | Strict Default | Child Folders | Child Non-Empty | Caretaker Non-Empty | Child Missing Age | Caretaker Missing Age | N-Gram Files | Context Files | Scoring Files | CSV Issues |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Belfast | naturalistic_caregiver_child | yes | 8 | 22,942 | 32,082 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brown | naturalistic_caregiver_child | yes | 3 | 92,555 | 64,206 | 0 | 0 | 3 | 3 | 3 | 0 |
| Champaign | caregiver_child_structured_observation | no | 44 | 106,349 | 141,136 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cummings | clinical_probe | no | 21 | 22,183 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Demetras1 | naturalistic_caregiver_child | yes | 1 | 6,842 | 8,270 | 0 | 0 | 0 | 0 | 0 | 0 |
| EHS | caregiver_child_structured_observation | no | 126 | 45,930 | 109,720 | 46 | 59 | 0 | 0 | 0 | 0 |
| Forrester | naturalistic_caregiver_child | yes | 1 | 6,664 | 8,890 | 0 | 0 | 0 | 0 | 0 | 0 |
| Hall | cross_sectional_sociolinguistic_snapshot | no | 40 | 71,830 | 49,343 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kuczaj | naturalistic_caregiver_child | yes | 1 | 37,109 | 28,223 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lara | naturalistic_caregiver_child | yes | 1 | 49,328 | 81,449 | 0 | 0 | 0 | 0 | 0 | 0 |
| MPI-EVA-Manchester | naturalistic_caregiver_child | yes | 4 | 462,100 | 546,929 | 0 | 0 | 0 | 0 | 0 | 0 |
| Manchester | naturalistic_caregiver_child | yes | 12 | 232,614 | 342,246 | 0 | 0 | 12 | 12 | 12 | 0 |
| Post | naturalistic_caregiver_child | yes | 3 | 8,068 | 18,387 | 0 | 0 | 0 | 0 | 0 | 0 |
| Providence | naturalistic_caregiver_child | yes | 6 | 121,816 | 262,451 | 626 | 522 | 6 | 6 | 6 | 0 |
| Sachs | naturalistic_caregiver_child | yes | 1 | 16,344 | 11,977 | 0 | 0 | 0 | 0 | 0 | 0 |
| Weist | naturalistic_caregiver_child | yes | 6 | 46,347 | 33,556 | 0 | 0 | 0 | 0 | 0 | 0 |
| Wells | naturalistic_caregiver_child | yes | 32 | 37,967 | 31,488 | 0 | 0 | 0 | 0 | 0 | 0 |

Totals:

- Child folders: 310
- Child rows: 1,593,965
- Non-empty cleaned child utterances: 1,386,988
- Caretaker rows: 1,840,403
- Non-empty cleaned caretaker utterances: 1,770,353
- Child rows missing `age_months`: 672
- Caretaker rows missing `age_months`: 581
- CSV row-width issues: 0
- Blank-header files: 0

## Readiness By Stage

### Stage 0 Cleaned Utterances

These datasets are currently ready for real-utterance analyses that use
`chi.csv` and `caretakers.csv`:

- Belfast
- Brown
- Champaign
- Cummings
- Demetras1
- EHS
- Forrester
- Hall
- Kuczaj
- Lara
- MPI-EVA-Manchester
- Manchester
- Post
- Providence
- Sachs
- Weist
- Wells

### Generated Baseline Utterances

These datasets currently have generated n-gram baseline child files:

- Brown
- Manchester
- Providence

The generated files were created before the newest strict naturalistic
expansion, so they do not yet reflect the expanded vocabulary/count dictionaries.

### Shared Context Files

These datasets currently have child-side shared caretaker context files:

- Brown
- Manchester
- Providence

### Minimal Surprisal Scoring Files

These datasets currently have compact child-side surprisal scoring files:

- Brown
- Manchester
- Providence

## Notes On Individual Datasets

- **Belfast**: Stage 0 ready; strict naturalistic default.
- **Brown**: Stage 0 ready and has downstream generated/context/scoring files.
- **Champaign**: Stage 0 ready, but assigned to structured observation rather
  than the strict naturalistic default.
- **Cummings**: Stage 0 ready for child rows only; clinical/probe group; no
  caretaker rows in the local prepared output.
- **Demetras1**: Stage 0 ready; strict naturalistic default.
- **EHS**: Stage 0 ready, but assigned to structured observation. It has a small
  number of rows missing `age_months`.
- **Forrester**: Stage 0 ready; strict naturalistic default.
- **Hall**: ready through the dedicated cross-sectional preprocessor
  `src/prepare_hall_snapshot.py`. It preserves all speaker tiers and active
  `@Situation` labels in `all_speakers.csv`, writes separate adult-interlocutor
  and family-caretaker views, and records race/social-class provenance and
  transcript exclusions. The primary snapshot has 36 children; a 37-child
  sensitivity adds one folder-inferred stratum. Hall is not part of the strict
  longitudinal default. Its completed k0–k3 Mistral same-pass archive passed
  the local relocation audit, and the separate cross-sectional model/report
  workflow is complete under `results/hall_snapshot_analysis/` and
  `docs/hall_snapshot_mistral_analysis.html`.
- **Kuczaj**: Stage 0 ready; strict naturalistic default.
- **Lara**: Stage 0 ready; strict naturalistic default. The `ELS` grandmother
  tier is included with caretakers.
- **MPI-EVA-Manchester**: Stage 0 ready; strict naturalistic default. Filename
  age fallback is used for sessions where CHI `@ID` age is blank.
- **Manchester**: Stage 0 ready and has downstream generated/context/scoring
  files.
- **Post**: Stage 0 ready; strict naturalistic default.
- **Providence**: Stage 0 ready and has downstream generated/context/scoring
  files. Some rows still have blank `age_months`.
- **Sachs**: Stage 0 ready; strict naturalistic default.
- **Weist**: Stage 0 ready; strict naturalistic default.
- **Wells**: Stage 0 ready; strict naturalistic default.

## Not Currently Preprocessed

- **Thomas**: discussed as a strict candidate, but `Thomas.zip` was not present
  in `data/zip_files` at the last check, so it is not extracted or preprocessed.
