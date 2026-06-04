# Notes

Living project memory: discoveries, decisions, bugs, commands that worked, and
current state. Prefer dated notes.

## Current State

TODO: Summarize what currently works.

Known current structure:

- Source code: `src/`
- Tests: `tests/`
- Preprocessed data: `data/preprocessed_data/`
- Raw Hall data: `data/raw_data/Hall/`
- Distribution figures: `figs/utterance_distributions/`

## Recent Decisions

- 2026-05-19 - `src/cleaning.py` keeps the lexical base of the CHAT special
  `@` forms needed for current analyses: `@b`, `@c`, `@d`, `@f`, `@i`, `@k`,
  `@l`, `@ls`, `@n`, `@o`, `@p`, and `@wp`.
- 2026-05-19 - Added `src/special_forms_per_utterance.py` to audit CHAT
  special-form rates in raw Brown, Manchester, and Providence data using the
  same cleaner as `prepare_datasets.py`.
- 2026-05-19 - Diagnostic reports use `speaker_group`: `CHILD` for `CHI` and
  `CARETAKERS` for `MOT`/`FAT`. Scorable utterances are rows whose
  `utterance_clean` contains at least one word token.
- 2026-05-19 - Added `src/fillers_and_shortenings_per_utterance.py` to audit
  filler-like tokens and parenthetical shortenings under the same scorable-row
  rule.
- 2026-05-19 - Added `src/build_preprocessing_variant_probe.py` to create a
  real-data CSV for scoring several preprocessing variants of the same
  utterances.
- 2026-05-19 - Added `src/plot_diagnostic_analyses.py` to create PNG/PDF
  figures from the special-form, filler/shortening, and preprocessing-variant
  diagnostics, including a child-versus-caretaker age trajectory comparing
  special forms, fillers, and shortenings in one figure.
- 2026-06-03 - SES/race metadata is now handled through an explicit codebook
  rather than a single inferred covariate. Local CHAT `@ID` SES values are kept
  separate from curated documentation-based fields with source URL, scope, and
  confidence. The current PBM result: Brown has child-specific SES for Adam and
  Sarah and child-specific race only for Adam; Manchester has corpus-level
  predominant middle-class status; Providence has no defensible SES/race values.
  The full 79-child strict-naturalistic codebook has 33 children with some
  SES/class value, but only 4 have child-specific or single-child evidence
  marked as usable with caution as a core predictor. Race/ethnicity is known
  only for Adam, Forrester/Ella, Lara, plus Post's community-level
  predominantly-white description.
- 2026-06-03 - Context entropy is present locally at
  `results/external/compute_surprisal_mila/context_entropy_mistral/`.
  Added `src/attach_context_entropy_to_route1_dataset.py` to join those
  context-level Mistral next-token entropy features onto the long utterance
  dataset by `(context_col_used, context_text)`. The enriched output is
  `results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz`.
  It preserves all 11,607,680 base rows. Join statuses are explicit:
  6,609,625 exact matched child-context rows, 15,385 child rows recovered by
  text-only fallback across k labels, 2,233,017 child k0 rows with no context,
  39,900 child rows with empty context, 2,675,612 caretaker rows marked
  not-applicable, and 34,141 child rows with missing entropy. The text-only
  fallback is correct because the entropy scorer deduplicates by context text,
  not by context-window label; H(next token | text) is unchanged if the same
  text appears as `context_k1` in one row and `context_k2` in another. The true
  missing rows correspond to 2,250 unique context windows listed in
  `results/route1_analysis_dataset/missing_context_entropy_contexts.csv`.
  They are concentrated in Brown Adam `Adam/050212.cha`, Brown Sarah's
  `050xxx.cha` files, and Providence Naima `Naima/030000.cha`, because the
  older Yang/context-entropy manifest was built from a May 28 PBM row-level
  dataset that omitted Adam/Sarah age-60+ files and Naima's recovered-age
  `030000.cha`.

## Commands That Worked

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/special_forms_per_utterance.py --datasets Brown,Manchester,Providence --speakers CHI,MOT,FAT --run-name brown_manchester_providence_chi_mot_fat
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/fillers_and_shortenings_per_utterance.py --datasets Brown,Manchester,Providence --speakers CHI,MOT,FAT --run-name brown_manchester_providence_chi_mot_fat
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/build_preprocessing_variant_probe.py --datasets Brown,Manchester,Providence --speakers CHI,MOT,FAT --run-name brown_manchester_providence_chi_mot_fat --examples-per-category 12 --max-base-examples 96 --max-cleaned-words 12
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/plot_diagnostic_analyses.py --run-name brown_manchester_providence_chi_mot_fat
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/prepare_datasets.py --dataset Brown
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/prepare_datasets.py --dataset Manchester
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/prepare_datasets.py --dataset Providence
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/build_child_demographic_codebook.py
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_build_child_demographic_codebook
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/attach_context_entropy_to_route1_dataset.py
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_attach_context_entropy_to_route1_dataset
```

TODO: Add preprocessing, dictionary-building, and plotting commands as they are
confirmed.

## Known Bugs

- TODO: Add bug, path, symptom, and reproduction command.

## Open Questions

- TODO: Which cleaned utterance column is authoritative?
- TODO: Which corpora are active?
- TODO: Which baselines are active?
- TODO: What is the empty-utterance policy?

## Important Paths

- `src/prepare_datasets.py`
- `src/build_age_word_dicts.py`
- `src/add_random_and_unigram_utterances.py`
- `src/plot_distributions.py`
- `docs/ngram-models.md`
- `docs/llm-models.md`

## 2026-05-19 N-Gram Baseline Rewrite

- `src/build_age_word_dicts.py` now builds additive unigram, bigram, and trigram age-bin dictionaries from the current `chi.csv` / `caretakers.csv` Stage-0 structure.
- Bigram counts use the last word of the most recent prior caretaker utterance as context for the first child word.
- Trigram counts use the last two words of the most recent prior caretaker utterance for the first child word, then the last caretaker word plus the first child word for the second child word.
- `src/add_random_and_unigram_utterances.py` now generates random, unigram, bigram, and trigram baseline utterances using the same caretaker-boundary context logic.
- `src/new_create_parallel_data.py` now merges generated sibling columns from `chi.ngram_generated.csv` and `chi.lstm_generated.csv` when present, then exports `trigram_chi/binK` and `lstm_chi` subsets when those columns exist.

## 2026-05-19 LSTM Baseline Script

- Added `src/generate_lstm_utterances.py` as a word-level LSTM generation baseline.
- The default `seq2seq_lstm` architecture uses an encoder for caretaker context tokens and a decoder for child utterance tokens.
- The older `causal_lstm` comparison architecture is still available; it trains examples shaped as caretaker context tokens plus `<bos>` predicting child utterance tokens.
- In the `causal_lstm` path, caretaker context tokens are masked out of the loss, so context conditions the hidden state without being scored as target text.
- Important knobs are CLI flags: `--architecture`, `--context_utterances`, `--max_context_tokens`, `--max_train_examples`, `--max_generate_rows_per_child`, architecture size, temperature, and top-k.
- Actual LSTM training/generation requires PyTorch; helper tests and `--help` run without PyTorch.

## 2026-05-20 LSTM Environment And Smoke Run

- Added `torch>=2.12.0` to the project dependencies with `uv add torch`, updating `pyproject.toml` and `uv.lock`.
- Verified PyTorch imports through `uv`; the installed build is CPU-only in this environment because CUDA is not available.
- Ran the full test suite after installation: `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`.
- Ran a bounded encoder-decoder LSTM smoke generation on Brown only, with 500 training examples and 10 generated rows per child. Outputs are intentionally marked as smoke files: `chi.lstm_smoke_generated.csv`.
- Confirmed the additive n-gram outputs include random, unigram, bigram, and trigram columns in `chi.ngram_generated.csv`; the random column samples uniformly from the additive bin vocabulary.

## 2026-05-20 LSTM Length Modes

- Added explicit LSTM generation length modes to `src/generate_lstm_utterances.py`.
- `same_as_child` is the default and samples exactly the same number of word tokens as the paired child utterance.
- `free_until_eos` trains with an `<eos>` target and samples until `<eos>` or `--max_generated_tokens`, with `--min_generated_tokens` preventing empty early stops.
- The fixed-length mode is the better control for comparing informativeness/surprisal while holding effort constant.
- The free-length mode is the better comparison for asking whether a model chooses a similar communicative effort/answer length from the same caretaker context.
- Verified `random_model_utterance_bin6`, `unigram_model_utterance_bin6`, `bigram_model_utterance_bin6`, and `trigram_model_utterance_bin6` lengths against the paired child utterances in all 21 generated files: 446,508 scorable rows with usable `age_months` had 0 length mismatches for all four baselines.
- The 477 scorable rows with length mismatches are rows without usable `age_months`; generation intentionally leaves those blank because they cannot be assigned to an additive age bin.
- Re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` after the length-mode change: 68 tests passed.
- Ran tiny Brown-only smoke generations for both LSTM length modes. The `same_as_child` smoke output had 0 length mismatches across 15 generated rows. The `free_until_eos` smoke output generated to the configured cap of 8 tokens in all 15 rows, which is expected for an undertrained one-epoch smoke model and should not be interpreted scientifically.

## 2026-05-20 N-Gram Output Alignment And Context Columns

- Updated `src/add_random_and_unigram_utterances.py` so generated CSVs include `caretaker_context_p2`, `caretaker_context_p1`, and `caretaker_context_last_two`.
- These columns show the exact most-recent caretaker boundary words used by bigram/trigram generation.
- Added regression tests that parse the generated CSV with Python's `csv` module and assert every row has the same number of fields as the header.
- Regenerated all 21 `chi.ngram_generated.csv` files for Brown, Manchester, and Providence.
- Verified the regenerated files: 519,803 rows parsed with 0 row-width mismatches and all 21 files include the context columns.
- Re-ran the length check after regeneration: 446,508 scorable rows with usable `age_months` had 0 length mismatches for random, unigram, bigram, and trigram outputs.
- Re-ran the full unit-test suite after the n-gram output fix: 70 tests passed.

## 2026-05-20 N-Gram Metadata Sanity Fix

- Found that the prepared Brown, Manchester, and Providence `chi.csv` files had blank `source_group` values, which made generated CSVs look misaligned even when the CSV parser could read them.
- Updated `src/add_random_and_unigram_utterances.py` to fill blank generated-output metadata: `dataset`, `child_id`, `source_group`, and `speaker`.
- For corpora without a subgroup, generated n-gram outputs now use the dataset name as `source_group`.
- Updated `src/prepare_datasets.py` so future known-corpus preprocessing also fills `source_group` with the dataset name for Brown, Manchester, and Providence-style layouts.
- Regenerated all 21 n-gram sibling CSV files again.
- Verified semantic column sanity on the regenerated files: 519,803 rows checked, 0 issues for row width, required columns, empty `dataset`, empty `child_id`, empty `source_group`, nonnumeric `line_no`, empty `file`, or non-CHI `speaker`.
- Re-ran the full test suite after the metadata fix: 71 tests passed.

## 2026-05-20 N-Gram Explicit Output Schema Fix

- Removed `utt_id_role` from generated n-gram sibling CSV outputs.
- Added an explicit generated-output schema instead of inheriting all source `chi.csv` columns.
- The generated header is now exactly: `dataset`, `child_id`, `source_group`, `session_id`, `age_raw`, `age_months`, `sex`, `file`, `line_no`, `reference_line`, `utt_id`, `speaker`, `utterance`, `utterance_clean`, `cleaned_is_empty`, the three caretaker context columns, and generated model columns.
- Switched generated n-gram CSV writing to `csv.QUOTE_ALL` to make spreadsheet imports less fragile.
- Added tests that check exact header order, absence of `utt_id_role`, absence of blank headers, and that `speaker`, `utterance`, and `utterance_clean` values remain under the correct headers.
- Regenerated all 21 n-gram sibling CSV files.
- Verified all regenerated files: 519,803 rows checked, 0 header/order/row-width/speaker/line/file/source-group issues.
- Re-ran the full test suite after this schema fix: 72 tests passed.

## 2026-05-20 Role-Specific Shared Caretaker Context Files

- Added `src/create_shared_caretaker_contexts.py`.
- The script writes two sibling files per child folder: `chi.shared_caretaker_contexts.csv` and `caretakers.shared_caretaker_contexts.csv`.
- Child files contain only child rows and include real `utterance_clean` plus random, unigram, bigram, and trigram generated utterance columns.
- Caretaker files contain only caretaker rows and do not include generated model columns.
- For every row, `context_k1`, `context_k2`, and `context_k3` are the last up-to-k prior caretaker utterances in the same session, excluding the current row.
- Generated all Brown, Manchester, and Providence context files: 21 child files and 21 caretaker files.
- Verified the generated files: 519,803 child rows, 688,880 caretaker rows, 0 header/order/row-width/role/line/file/source-group issues.
- Removed the obsolete single combined context CSV created before the role-specific output clarification.
- Re-ran the full test suite after this context-file change: 74 tests passed.

## 2026-05-20 Utterance Count Strategy Probe

- Added `src/utterance_count_strategies.py` with explicit word, morpheme, and syllable count strategies.
- Word strategies: regex word tokens and whitespace tokens containing at least one letter.
- Morpheme strategies: one morpheme per word, clitic/contraction splitting, and a simple suffix heuristic for common English inflections.
- Syllable strategies: vowel groups with `y`, silent-final-e adjustment, consonant+`le` adjustment, and a no-`y` comparison strategy.
- Generated a 100-row validation probe at `results/count_validation/utterance_count_strategy_probe.csv`.
- The probe intentionally prioritizes rows where strategies disagree, then fills the rest with a seeded random sample from cleaned child and caretaker utterances.
- Verified the probe CSV: 100 rows, 23 columns, no blank headers, and no row-width issues.
- Added unit tests for each count family, probe selection, and exact CSV output schema.
- Re-ran the full test suite after adding the counters: 82 tests passed.

## 2026-05-20 Minimal Surprisal Scoring CSVs

- Added `src/create_minimal_surprisal_scoring_csvs.py`.
- The script reads the role-specific shared-context files and writes compact scoring-only sibling files.
- Child output file per child: `chi.surprisal_scoring.csv`.
- Caretaker output file per child: `caretakers.surprisal_scoring.csv`.
- Child files contain only metadata needed to identify rows, `context_k1`, `context_k2`, `context_k3`, the real child cleaned utterance, and random/unigram/bigram/trigram generated utterances.
- Caretaker files contain only metadata needed to identify rows, speaker, `context_k1`, `context_k2`, `context_k3`, and the cleaned caretaker utterance.
- Empty target rows are dropped by default because they do not need to be sent for surprisal scoring.
- Generated all Brown, Manchester, and Providence compact scoring files: 21 child files and 21 caretaker files.
- Verified the generated compact files: 446,985 child rows, 668,903 caretaker rows, 0 header/order/row-width/target/role/line/file/source-group issues.
- Re-ran the full test suite after adding the compact scoring exporter: 85 tests passed.

## 2026-05-20 MPI-EVA-Manchester Preprocessing

- Extracted `data/zip_files/MPI-EVA-Manchester.zip` into `data/raw_data/MPI-EVA-Manchester/`.
- Registered `MPI-EVA-Manchester` in `src/prepare_datasets.py` and the default distribution plotting dataset list.
- Added filename-age fallback for CHAT files whose CHI `@ID` age is blank. The fallback parses stems like `030400.cha` as age `3;04.00` and `020500b.cha` as age `2;05.00`.
- This fallback matters for MPI-EVA-Manchester because Gina and Helen have blank CHI ages in the `@ID` metadata but usable ages in the filenames.
- Reprocessed MPI-EVA-Manchester with `env UV_CACHE_DIR=/tmp/uv-cache /home/apaixonada/.local/bin/uv run python src/prepare_datasets.py --dataset MPI-EVA-Manchester --testing`.
- Prepared output now has 511,796 child rows, 462,100 non-empty cleaned child utterances, 567,224 caretaker rows, and 546,929 non-empty cleaned caretaker utterances, with 0 missing age rows.
- Wrote updated distribution outputs to `figs/utterance_distributions_with_mpi_eva_manchester/`.
- The most useful comparison outputs are `figs/utterance_distributions_with_mpi_eva_manchester/ALL_DATASETS/utterance_counts_by_age_bin_6m.csv` and `figs/utterance_distributions_with_mpi_eva_manchester/ALL_DATASETS/bmp_vs_bmp_plus_mpi_age_bin_counts_6m.png`.

## 2026-05-20 Named Longitudinal Corpus Expansion

- Checked the local zips named by the user: `Styles`, `Wells`, `Belfast`, `Cummings`, and `Champaign`.
- `Styles.zip` is not a CHILDES transcript dataset in this repo; it contains NeurIPS style files and no `.cha` transcripts, so it was skipped.
- `Wells`, `Belfast`, and `Champaign` are longitudinal naturalistic/observational CHILDES corpora and were added to preprocessing.
- `Cummings` is a PhonBank clinical corpus marked as "clinical, cross-sectional (some longitudinal)." It was processed for completeness but should be kept separate from naturalistic caregiver-child corpora.
- Added dataset registry entries for `Belfast`, `Wells`, `Champaign`, and `Cummings` in `src/prepare_datasets.py`.
- Added a Champaign-specific discovery rule because its local layout groups files by measurement/context folder (`27P`, `30X`) and uses file stems (`13B`, `05G`) as child IDs.
- Added parent-folder age fallback for Champaign files with blank CHI `@ID` ages, parsing folders like `21P` and `30X` as 21 and 30 months.
- Reprocessed `Belfast`, `Wells`, `Champaign`, and `Cummings`; all four now have 0 missing child age rows in their prepared child files.
- Wrote expanded distribution outputs to `figs/utterance_distributions_longitudinal_named_expansion/`.
- The most useful comparison outputs are `figs/utterance_distributions_longitudinal_named_expansion/ALL_DATASETS/previous_vs_named_longitudinal_additions_age_bin_counts_6m.csv` and `figs/utterance_distributions_longitudinal_named_expansion/ALL_DATASETS/previous_vs_named_longitudinal_additions_age_bin_counts_6m.png`.

## 2026-05-20 Naturalistic Caregiver-Child Focus

- Separated corpus groups explicitly in `src/plot_distributions.py`: `NATURALISTIC_CAREGIVER_CHILD_DATASETS` are the default; `CLINICAL_PROBE_DATASETS` contains `Cummings`.
- Added `results/corpus_groups/dataset_group_assignments.csv` to make this split auditable.
- Added EHS as a non-clinical parent-child interaction corpus. It is task-structured observational data, so it should be described separately from the most naturalistic home corpora, but it is not clinical/probe data.
- EHS preprocessing groups files by family/child ID across folders like `14-mot`, `24-mot`, `36-mot`, `pre-K-mot`, and `pre-K-fat`.
- Added EHS age fallback from header comments like `@Comment: age is 02;01.22`; remaining folder-wave fallback parses folders like `24-mot` and `36-mot`.
- EHS prepared output has 45,930 non-empty cleaned child utterances and 109,720 non-empty caretaker utterances. Forty-six child utterance rows remain without usable age because their pre-K files have no exact age metadata.
- Regenerated naturalistic caregiver-child-only outputs at `figs/utterance_distributions_naturalistic_caregiver_child_only/`, excluding Cummings.
- The EHS comparison outputs are `figs/utterance_distributions_naturalistic_caregiver_child_only/ALL_DATASETS/naturalistic_before_vs_after_ehs_age_bin_counts_6m.csv` and `.png`.

## 2026-05-20 Strict Naturalistic Corpus Expansion

- Extracted the newly available strict naturalistic zips from `data/zip_files/`: `Lara`, `Sachs`, `Weist`, `Kuczaj`, `Post`, `Demetras1`, and `Forrester`.
- `Thomas.zip` was not present in `data/zip_files`, so Thomas remains pending and was not included in preprocessing or plots.
- Registered the seven available corpora in `src/prepare_datasets.py`.

## 2026-05-26 Clinical Corpus Preparation

- Clinical/probe corpora are now kept separate from strict naturalistic data in `data/raw_data/Clinical/` and `data/preprocessed_clinical_data/`.
- Added `src/prepare_clinical_datasets.py` for clinical-specific discovery rules: separate control/clinical groups, child ID grouping across age/task folders, dynamic caregiver-role detection, and clinical metadata summaries.
- Prepared 15 clinical/control dataset groups: Ambrose HL/TD, Cummings PD, Feldman SLI/TD, Flusberg DS, Hooshyar DS/TD, Nicholas HL/TD, Rescorla LT/TD, Rondal DS/TD, and UCSD SLI.
- Current clinical Stage 0 output has 494 child folders: 240 control children and 254 clinical/probe children.
- Metadata files are `results/metadata/clinical_child_metadata_summary.csv`, `results/metadata/clinical_dataset_summary.csv`, and `data/preprocessed_clinical_data/manifest.csv`.
- CSV sanity check after generation: 989 CSV files, 667,455 data rows, 0 blank-header or row-width issues.

## 2026-05-26 Clinical Magnitude Analysis

- Added `src/analyze_clinical_magnitudes.py` to compare session size and age-bin coverage for clinical/probe subjects, the new TD/control arms, and the current strict naturalistic bundle.
- Generated tables in `results/clinical_magnitude_analysis/` and plots in `figs/clinical_magnitude_analysis/`.
- Current median total non-empty utterances per transcript: clinical subjects 384, new TD controls 458, strict naturalistic bundle 956.5.
- Age-bin outputs use fixed 6-month bins from month 006 onward and only include age-binnable utterances. Separate missing-age tables are written for utterances that cannot be assigned to a bin.
- No autism-labeled subjects were detected in the prepared clinical metadata; the analysis keeps an explicit Autism group with zero counts so that absence is visible.

## 2026-05-26 LSTM Baseline Pipeline

- Added `src/run_lstm_baseline_pipeline.py` as the GPU-oriented orchestration layer around `src/generate_lstm_utterances.py`.
- The pipeline trains one bounded-context encoder-decoder LSTM, generates `lstm_same_length_utterance` and optionally `lstm_free_length_utterance`, then writes `chi.lstm_generated.csv`, `chi.shared_caretaker_contexts.with_lstm.csv`, and `chi.surprisal_scoring_with_lstm.csv`.
- Default inputs target `data/big_cleaned_dataset/default_naturalistic_custom_early20k/`, using age range 6 through 65.999 months to match the current custom vocabulary-bin bundle.
- Added `tests/test_lstm_baseline_pipeline.py` and `docs/lstm-baseline-pipeline.md`.
- Ran a laptop dry run only, with no model training: 79 child folders and 1,140,218 usable examples were found. Full training should be run on a GPU machine with `--device cuda`.

## 2026-05-26 Merged Early N-Gram Bin

- Replaced the threshold early split for new random/unigram/bigram/trigram generation with one first bin, `006-023`, followed by the existing 6-month bins from `024-029` through `060-065`.
- Regenerated the strict naturalistic big-cleaned bundle at `data/big_cleaned_dataset/default_naturalistic_merged_006_023/`.
- The regenerated bundle has 79 child scoring files, 79 caretaker scoring files, 1,140,218 child scoring rows, and 1,470,154 caretaker scoring rows.
- CSV validation found 0 blank-header or row-width issues across manifest, generated n-gram files, shared-context files, and compact scoring files.
- Later additive dictionary files for `024-029` through `060-065` match the previous `default_naturalistic_custom_early20k` dictionaries byte-for-byte. Therefore, existing PBM scored baseline results for age `024+` can be kept if the goal is to avoid rerunning already-scored stochastic samples.
- Added `src/create_pbm_early_baseline_rescoring_bundle.py` to extract only the PBM generated-baseline targets that need rescoring under the new first bin.
- Generated `results/rescoring_subsets/pbm_006_023_merged_early_baselines/` and `results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_2026-05-26.tar.gz`.
- The PBM rescoring bundle contains 251,264 scorer rows: 62,816 each for `random_chi/bin6`, `unigram_chi/bin6`, `bigram_chi/bin6`, and `trigram_chi/bin6`. All rows have floored child age 006-023.

## 2026-05-27 PBM Rescoring Handoff Tarball

- Added `MERGE_BACK_GUIDE.md` to the PBM early rescoring bundle, documenting that only generated baseline rows for Brown/Manchester/Providence floor-age 006-023 should replace old scores.
- Added `replacement_keys.csv` with one unique replacement key per scorer row. The intended key is `dataset + child_id + source_text_col + source_row`, with file/line/utt provenance retained for audit.
- Created `results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_handoff_2026-05-27.tar.gz`.
- The handoff tarball includes the four scorer subsets, row-count manifests, merge-back guide, and replacement key table.
- Validation checked 18 CSVs in the bundle and found 0 blank-header or row-width issues.

## 2026-05-28 Config-Driven LSTM Baseline

- Updated `src/run_lstm_baseline_pipeline.py` so the default input bundle is now `data/big_cleaned_dataset/default_naturalistic_merged_006_023/`.
- Added `--config` JSON loading for the GPU LSTM pipeline. Config paths are resolved relative to the project root unless absolute.
- Added editable generation-variant objects: a config can now define output column, length mode, max generated tokens, and minimum generated tokens for each LSTM variant.
- Added `configs/lstm_baseline_16gb_default.json` for the intended full local-GPU run and `configs/lstm_baseline_16gb_smoke.json` for a smaller end-to-end GPU check.
- Rewrote `docs/lstm-baseline-pipeline.md` to state the high-level scientific model clearly: a word-level encoder-decoder LSTM maps bounded prior caretaker context to child utterance baselines, with same-length and free-length decoding variants.
- No training or generation was run on the laptop. Verification used tests only: focused LSTM tests and the full suite passed with 145 tests.

## 2026-05-28 Agent Handoff For PC LSTM Work

- Updated `AGENTS.md` so future agents see the current project split immediately: this repository prepares data and generated baselines, while large-scale surprisal scoring belongs to the separate Mila project.
- `AGENTS.md` now records the active strict naturalistic bundle, the merged early `006-023` bin decision, the current LSTM focus, the data/Git policy, and the files an LSTM-focused agent should read first.
- Added `docs/lstm_pc_handoff.md` for the next agent on the local GPU PC. It records the PC path, observed PC host/IP, rsync command for transferring the current big-cleaned bundle, dry-run/smoke/full LSTM commands, expected artifacts, and documentation requirements after any run.
- The current `TODO.md` focus now points to the PC LSTM generation run and explicitly says not to train on the laptop.
- Added root-direct CHAT discovery for corpora where one target child's `.cha` files live directly under the corpus root, as in `Kuczaj`, `Sachs`, `Lara`, `Demetras1`, and `Forrester`.
- Added corpus-specific caretaker speaker handling for `Lara`, keeping `ELS` with `MOT`/`FAT` in `caretakers.csv` because the raw headers identify `ELS` as grandmother/caregiver speech.
- Updated `src/plot_distributions.py` so the default strict naturalistic set is: Brown, Manchester, Providence, MPI-EVA-Manchester, Belfast, Wells, Lara, Sachs, Weist, Kuczaj, Post, Demetras1, and Forrester.
- Moved `Champaign` and `EHS` to a separate structured-observational caregiver-child grouping for stricter naturalistic analyses, while keeping `Cummings` as clinical/probe.
- Reprocessed the seven available new corpora with `--testing`; the new corpora produced 179,129 child rows and 195,806 caretaker rows, with 0 missing child ages, 0 missing caretaker ages, 0 row-width issues, and 0 blank headers.
- Regenerated strict naturalistic child-utterance age-bin outputs at `figs/utterance_distributions_strict_naturalistic_parent_child/`.
- The main total distribution is `figs/utterance_distributions_strict_naturalistic_parent_child/ALL_DATASETS/utterance_counts_by_age_bin_6m.csv`.
- The before/new comparison is `figs/utterance_distributions_strict_naturalistic_parent_child/ALL_DATASETS/previous_vs_new_strict_downloads_age_bin_counts_6m.csv` and `.png`.
- Also wrote the caretaker-side strict comparison to `figs/utterance_distributions_strict_naturalistic_parent_child/ALL_DATASETS/caretaker_previous_vs_new_strict_downloads_age_bin_counts_6m.csv` and `.png`.

## 2026-05-28 PBM Additive LSTM Generation

- Added `src/run_lstm_additive_age_context_pipeline.py` as a PBM-focused additive age-bin orchestration layer around `src/generate_lstm_utterances.py`.
- Added `tests/test_lstm_additive_age_context_pipeline.py`; focused LSTM/additive tests passed with `30 tests OK`.
- The new script trains one word-level encoder-decoder LSTM per context-window/age-bin cell. For each target age bin, training examples are cumulative from `006` through that bin's end, matching the additive information regime of the random/unigram/bigram/trigram baselines.
- The age-bin schedule is the current merged-early schedule: `006-023`, then `024-029`, `030-035`, `036-041`, `042-047`, `048-053`, `054-059`, and `060-065`.
- The first real run was PBM-only, not full strict-naturalistic, to stay comparable to earlier Providence/Brown/Manchester baseline work and avoid scaling before validating the design.
- Context-window sensitivity was built into the run with independent models for `k=3`, `k=4`, and `k=5` prior caretaker utterances, each capped at 60 context tokens.
- The main generated variant was same-length only, because same-length generated utterances are the apples-to-apples effort-controlled comparison against the existing random/unigram/bigram/trigram baselines.
- Added richer training/generation instrumentation:
  - per-bin `batch_training_log.csv`;
  - per-bin and run-level `training_summary.csv`;
  - `model_run_manifest.csv`;
  - `generation_diagnostics.csv`;
  - `generation_samples.csv`;
  - run-level PNG/PDF plots under `plots/`.
- Real run command:

```bash
.venv/bin/python src/run_lstm_additive_age_context_pipeline.py \
  --output_dir results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length \
  --contexts 3 4 5 \
  --variants same_length \
  --epochs 3 \
  --embedding_dim 128 \
  --hidden_dim 256 \
  --batch_size 128 \
  --max_vocab_size 30000 \
  --device cuda
```

- Hardware/runtime context: local PC with NVIDIA GeForce RTX 4060 Ti, 16GB VRAM; NVIDIA driver 595.71.05; PyTorch 2.12.0+cu130; CUDA available.
- Real run output directory:

```text
results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length/
```

- Generated sibling files per PBM child folder:
  - `chi.lstm_additive_generated.csv`
  - `chi.shared_caretaker_contexts.with_lstm_additive.csv`
  - `chi.surprisal_scoring_with_lstm_additive.csv`
- Generated columns:
  - `lstm_additive_k3_same_length_utterance`
  - `lstm_additive_k4_same_length_utterance`
  - `lstm_additive_k5_same_length_utterance`
- Validation after the run:
  - 21 generated child files found;
  - 519,803 child rows checked;
  - 446,508 non-empty generated rows per LSTM column;
  - 0 same-length mismatches for k3, k4, or k5;
  - 21 context-with-LSTM files and 21 scoring-with-LSTM files found;
  - 446,985 scoring rows with the LSTM columns.
- Scoring-context reminder: generation `k3`/`k4`/`k5` and scorer `context_k1`/`context_k2`/`context_k3` are separate axes. Every real child, generated child-like, or caretaker target utterance should be scored with its own row-matched scorer context columns.
- Added `docs/lstm-additive-pbm-supervisor-summary.md` for a high-level explanation with formulas and supervisor-facing rationale.
- Added `docs/agentic_history.md` to preserve timestamped decisions from the LSTM design/generation conversation for future agents.

## 2026-05-29 PBM 006-023 Scoring Patch

- User clarified that LSTM patching can be ignored in this laptop thread; the active work is only the PBM generated-baseline `006-023` patch.
- Added a tested patch workflow to the local `compute_surprisal_mila` checkout:
  - `src/create_pbm_006_023_scoring_patch.py`
  - `src/replace_pbm_006_023_input_baselines.py`
  - `src/merge_pbm_006_023_patch_scores.py`
  - `slurm/submit_pbm_006_023_patch_mistral.sh`
  - `slurm/merge_pbm_006_023_patch_scores.sbatch`
  - `docs/pbm_006_023_patch_rescoring.md`
  - `tests/test_pbm_006_023_patch.py`
- The patch creation script filters the current merged-early scoring CSVs to Brown, Manchester, and Providence child rows with `6 <= age_months < 24`.
- The input replacement script updates only the four generated baseline utterance columns in Mila's full cleaned-data inputs, after a dry-run audit and optional backup, so future full scoring reruns use the corrected `006-023` generated utterances.
- The merge script is dry-run by default and only applies changes when patch rows match full scored-result rows by stable utterance provenance keys: `dataset`, `child_id`, `session_id`, `file`, `line_no`, and `utt_id`.
- Verification in `compute_surprisal_mila`: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` passed with 4 tests.
- Built the actual patch tree at `results/scoring_patches/cleaned_data_patches/pbm_006_023_merged_early_baselines/`.
- Patch input tree summary: 17 child files, 62,816 rows. Dataset split: Brown 1 child / 6,715 rows; Manchester 10 children / 22,272 rows; Providence 6 children / 33,829 rows.
- Validated the scorer manifest with `src/build_cleaned_scoring_manifest.py`; it produced 272 tasks and no missing combinations: 17 child files times 4 generated modes times 4 context settings.
- Created tarball `results/scoring_bundles/pbm_006_023_scoring_patch_2026-05-29.tar.gz` for transfer to Mila.

## 2026-06-01 Route 1 From-Zero Reset

- User explicitly reset the scientific analysis plan: older `compute_surprisal_mila` analysis outputs are archive/scaffold, not the evidential baseline.
- Added `docs/route1_from_zero_handoff_2026-06-01.md` as the current compass for the 2026-06-02 Route 1 rebuild.
- The handoff records that `communicative_efficiency` is now the from-zero scientific analysis workspace, while `compute_surprisal_mila` remains the scoring/HPC/audit repo.
- Audited usable inputs carried forward: main cleaned Mistral tree with 504/504 CSVs and LSTM additive same-length tree with 252/252 CSVs.
- Route 1 should start with real-child Mistral scores, recomputed cleaned word counts, descriptive plots, and the simplest age/length/child model before adding contexts, generated baselines, LSTM comparisons, entropy/KL features, or word-level features.
- Pending caveats recorded in the handoff: PBM `006-023` generated-baseline patch still needs corrected Mila completion/audit after the Slurm comma-export bug; context entropy, KL/JS, and word-level surprisal features should not be used until hardened reruns pass audits.

## 2026-06-02 Utterance Measurement Validation Probe

- Added `src/validate_utterance_measurement_strategies.py` for publication-oriented audit rows covering word, morpheme, syllable, and phoneme counts side by side.
- Added `tests/test_validate_utterance_measurement_strategies.py`.
- Installed lightweight measurement dependencies with `uv add cmudict pronouncing pyphen syllables`, then added `g2p-en` for OOV word-form phoneme/syllable fallback.
- Added `openpyxl` so the validation probe can write a formatted LibreOffice-friendly `.xlsx` review workbook.
- Downloaded `g2p-en` NLTK resources under `data/nltk_data/`: `cmudict`, `averaged_perceptron_tagger`, and `averaged_perceptron_tagger_eng`.
- Generated the initial 25-row validation outputs, then replaced them with a more human-reviewable 50-row stratified probe.
- Current 50-row validation outputs:
  - `results/count_validation/publication_measurement_probe_50.csv`
  - `results/count_validation/publication_measurement_probe_50.md`
  - `results/count_validation/publication_measurement_review_50.csv`
  - `results/count_validation/publication_measurement_review_50_tokens.csv`
  - `results/count_validation/publication_measurement_review_50.xlsx`
- The review set is stratified by surface word length: 14 short rows, 14 medium rows, 12 long rows, and 10 very long rows. It has 0 duplicate cleaned utterances, 0 blank recommended syllable counts, and 0 blank recommended phoneme counts.
- The review workbook puts the utterance, indexed tokens, automatic counts, and blank manual columns together so the user can make judgment calls without scrolling across the full audit schema.
- The preferred phoneme counts use CMUdict ARPABET pronunciations for known words and `g2p-en` ARPABET predictions for OOV words as written.
- The preferred syllable counts now use CMUdict for known words and the `syllables` package for OOV words as written. G2P-derived syllables remain visible as a diagnostic only, after manual review caught `firetruck` as an undercount under G2P vowel-nucleus syllable counting.
- CMU-only diagnostic columns still go blank for OOV rows, but `recommended_syllable_count` and `recommended_phoneme_count` are complete for every non-empty validation row.
- The probe explicitly distinguishes surface-string counts from CHAT `%mor`/MLU-style counts. Rows with retracing/repetition markup such as `[/]` are flagged with `raw_repetition_marker` and `mor_surface_mismatch`.
- Added `docs/utterance_measurement_validation.md` to record the method hierarchy and the Levshina/word-level-bits context decision.
- Added `docs/utterance_measurement_package_writeup.md` as a reviewer-facing description of each package/resource used for word, morpheme, syllable, phoneme, and spreadsheet infrastructure.
- Verification:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_validate_utterance_measurement_strategies` passed with 8 tests.
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 153 tests.

## 2026-06-02 Additive Age-Bin LSTM Rewrite

- Corrected the LSTM baseline design so the default GPU configs now train one
  cumulative/additive LSTM per target age bin, matching the developmental
  information constraints used by random/unigram/bigram/trigram baselines.
- Added `LSTMAgeBinning`, additive bin-run helpers, cumulative training/example
  selection, per-bin model/vocabulary outputs, `lstm_age_bin` provenance, and
  dry-run summaries to `src/run_lstm_baseline_pipeline.py`.
- Updated default and smoke configs:
  - `configs/lstm_baseline_16gb_default.json`
  - `configs/lstm_baseline_16gb_smoke.json`
- The default age bins are loaded from:
  - `data/big_cleaned_dataset/default_naturalistic_merged_006_023/age_ngram_dicts/merged_early_006_023/age_bins.json`
- Additive-bin dry run on the laptop completed without training:
  - command: `env UV_CACHE_DIR=/tmp/uv-cache uv run python src/run_lstm_baseline_pipeline.py --config configs/lstm_baseline_16gb_default.json --dry_run`
  - units: 79
  - examples total: 1,140,218
  - bins: 8
  - summary: `results/lstm_baselines/default_naturalistic_merged_006_023_additive_seq2seq_ctx3/dry_run_summary.json`
- Dry-run additive plan:
  - `006-023`: train 82,720, target 82,720
  - `024-029`: train 386,676, target 303,956
  - `030-035`: train 662,895, target 276,219
  - `036-041`: train 887,348, target 224,453
  - `042-047`: train 971,400, target 84,052
  - `048-053`: train 1,064,947, target 93,547
  - `054-059`: train 1,114,730, target 49,783
  - `060-065`: train 1,140,218, target 25,488
- Updated `docs/lstm-baseline-pipeline.md`, `docs/lstm_pc_handoff.md`, and
  `AGENTS.md` so future agents do not replace additive-bin scientific logic
  with a simplified global LSTM unless explicitly requested.
- No GPU training was run on the laptop.
- Verification:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_lstm_baseline_pipeline` passed with 11 tests.
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 156 tests.

## 2026-06-02 PBM-Only Additive LSTM Config

- Added `configs/lstm_baseline_16gb_pbm_additive.json` for the first fair LSTM
  comparison against PBM-trained random/unigram/bigram/trigram baselines.
- The PBM config uses only Brown, Manchester, and Providence but preserves the
  same additive age-bin logic and same LSTM architecture/hyperparameters as the
  all-corpus default config.
- PBM dry-run command:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python src/run_lstm_baseline_pipeline.py --config configs/lstm_baseline_16gb_pbm_additive.json --dry_run`
- PBM dry-run summary:
  - summary path: `results/lstm_baselines/pbm_merged_006_023_additive_seq2seq_ctx3/dry_run_summary.json`
  - units: 21
  - examples total: 446,508
  - bins: 8
- PBM additive plan:
  - `006-023`: train 62,816, target 62,816
  - `024-029`: train 225,026, target 162,210
  - `030-035`: train 367,473, target 142,447
  - `036-041`: train 404,679, target 37,206
  - `042-047`: train 421,024, target 16,345
  - `048-053`: train 433,933, target 12,909
  - `054-059`: train 443,966, target 10,033
  - `060-065`: train 446,508, target 2,542
- Interpretation: PBM is large enough for the first fair comparison, especially
  through mid-childhood bins, but the final `060-065` target bin is small and
  should be flagged in analyses.

## 2026-06-03 Child-Output Vocabulary Constraint For PBM LSTM Generation

- Clarified the LSTM vocabulary design before the real PBM run: caretaker words
  are input-context tokens, while generated baseline utterances should represent
  child-like output.
- Updated `src/generate_lstm_utterances.py` so generation can take an
  `allowed_output_token_ids` mask. Sampling now rejects tokens outside that mask
  after applying normal special-token bans.
- Updated `src/run_lstm_additive_age_context_pipeline.py` so each additive
  context-window/age-bin model builds:
  - one shared model vocabulary from caretaker context tokens plus child target
    tokens;
  - one child-side allowed output vocabulary from child target tokens only.
- The effect is that parent-only words can condition the encoder but cannot be
  sampled as generated child baseline words unless they also appeared in child
  utterances in the cumulative training data for that age bin.
- Added `child_output_vocab_size` to `model_run_manifest.csv` so each trained
  model records both its shared vocabulary size and its child-side output
  vocabulary size.
- Added focused tests for output masking and child-only output id selection.
- Verification:
  - `.venv/bin/python -m unittest tests.test_lstm_generation tests.test_lstm_additive_age_context_pipeline tests.test_lstm_baseline_pipeline` passed with 35 tests.
  - Tiny PBM constrained smoke run completed all 24 k/bin cells with 234
    generated rows, 0 empty generated rows, and 0 same-length mismatches.

## 2026-06-03 Utterance-Level Information Report Started

- Added `docs/predicting_utterance_level_information_report.md` as the active
  supervisor-facing report for predicting informational content at the
  utterance level.
- Scope is intentionally narrow: utterance-level informational content over
  development, with controls for target length/effort, context, and repeated
  child observations.
- The report explicitly excludes Route 2 entropy/KL analyses and the
  Levshina-style word-token informativity route.
- The current source-of-truth handoff is
  `docs/route1_from_compute_surprisal_handoff_2026-06-03.md`.
- The current scored source tree for Route 1 is the patched PBM Mistral tree:
  `results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023`.
- The report records the current scientific framing, PBM corpus coverage,
  developmental bins, child trajectories, staged modeling questions, and
  interpretation guardrails without exposing distracting implementation paths.

## 2026-06-03 Route 1 Coverage Assets And HTML Report

- Added `src/build_route1_report_assets.py` to build Route 1 coverage tables
  and figures from the patched PBM Mistral scored tree.
- Added `src/render_markdown_report.py` as a dependency-light Markdown-to-HTML
  renderer so the Markdown report remains the source and the HTML report is
  reproducible on the laptop without pandoc.
- Added `tests/test_build_route1_report_assets.py` with coverage for the
  merged `006-023` Route 1 bin, six-month follow-up bins, filename-age recovery,
  k0 child/caretaker counting, Markdown table rendering, and HTML rendering.
- During the first coverage pass, 477 child rows and 507 caretaker rows appeared
  unbinned. Audit showed all of them were Providence/Naima `Naima/030000.cha`
  rows with blank scored `age_months`.
- Fixed the Route 1 asset builder to recover blank scored ages from
  YYMMDD-style CHAT filename stems, reusing the convention from
  `prepare_datasets.py`. `030000.cha` resolves to 36.0 months and is assigned
  to the `036-041` bin.
- Regenerated Route 1 coverage assets:
  - child k0 scored rows: 446,985; rows in Route 1 bins: 446,985
  - caretaker k0 scored rows: 668,903; rows in Route 1 bins: 668,903
  - missing age after recovery: 0 for both roles
  - outside Route 1 bins: 0 for both roles
- Generated figures under `figs/utterance_information/` and tables under
  `results/utterance_information/report_assets/`.
- Rendered the HTML report to
  `docs/predicting_utterance_level_information_report.html`.
- Verification:
  - `env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_build_route1_report_assets` passed with 6 tests.
  - `env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 163 tests.

## 2026-06-03 Supervisor-Facing Report Framing Update

- User clarified that the report should not expose internal labels such as
  "Route 1" or implementation details such as paths/symlinks/workflow sections.
- Reworked `docs/predicting_utterance_level_information_report.md` around
  communicative efficiency: informativeness versus production effort.
- Removed the premature "Analysis Questions" and next-modeling sections.
- Added a "Comparison Baselines" section describing:
  - random baseline as uniform sampling from age-additive vocabulary;
  - unigram/bigram/trigram baselines as additive developmental n-gram models;
  - LSTM baseline as an encoder-decoder comparison using the same additive age
    bin training logic, with same-length generation as the first effort-held
    comparison.
- Retitled report figures with short formal titles:
  - `Utterance Coverage by Age`
  - `Corpus Contributions by Age`
  - `Child Age Coverage`
- Regenerated report assets:
  - `env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache uv run python src/build_route1_report_assets.py`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python src/render_markdown_report.py docs/predicting_utterance_level_information_report.md docs/predicting_utterance_level_information_report.html`
- Full suite verification: `env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 163 tests.

## 2026-06-03 Route 1 Analysis Dataset Recovery

- Added `src/build_route1_analysis_dataset.py` and
  `tests/test_build_route1_analysis_dataset.py` to build a normalized
  utterance-level modeling CSV with scored `sum_bits` and selected effort
  counts for child real utterances, generated random/unigram/bigram/trigram
  baselines, and caretaker utterances.
- The first full build found exactly 7,632 unscored generated-baseline rows:
  Providence/Naima `Naima/030000.cha`, 477 underlying child utterances, for
  random/unigram/bigram/trigram across k0/k1/k2/k3. Real child rows were scored.
  Extracted row keys to:
  - `results/route1_analysis_dataset/unscored_generated_baseline_rows_long.csv`
  - `results/route1_analysis_dataset/unscored_generated_baseline_rows_unique.csv`
  - `results/route1_analysis_dataset/unscored_generated_baseline_summary.csv`
- Updated effort counting so word-like fillers or special word forms such as
  `hm`, `mm`, `shh`, and `ð` receive at least one syllable and at least one
  phoneme if they survive as scored lexical targets.
- Added atomic output publication to `src/build_route1_analysis_dataset.py`: the
  builder now writes hidden temporary files and only replaces the final CSV and
  audit files after validation succeeds. This prevents interrupted long runs
  from leaving a truncated file under the final output name.
- A user interruption left
  `results/route1_analysis_dataset/route1_scored_utterance_effort_long.csv.gz`
  truncated (`gzip -t` reported unexpected EOF). Moved that corrupt CSV and
  stale audit/schema files to:
  `results/route1_analysis_dataset/interrupted_2026-06-03_pre_atomic/`.
- Current status: the final Route 1 analysis CSV is intentionally absent and
  must be rebuilt with the atomic builder before modeling.
- Verification after code changes:
  `env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_validate_utterance_measurement_strategies tests.test_build_route1_analysis_dataset`
  passed with 17 tests.

## 2026-06-03 Naima 030000 Missing-Baseline Patch

- Investigated the 7,632 missing generated-baseline scoring tasks. The missing
  scope is exactly Providence/Naima `Naima/030000.cha`: 477 scorable child
  utterances x random/unigram/bigram/trigram x k0/k1/k2/k3.
- Real child utterance scores for these 477 rows exist in the Mistral scored
  tree; generated-baseline target text and scores were blank because the source
  scorer input had blank `age_months`.
- Confirmed `Naima/030000.cha` can be assigned to 36.0 months from the CHAT
  filename, so the scientifically consistent generated-baseline bin is the
  current additive `036-041` dictionary bin.
- Added `src/create_naima_030000_missing_baseline_patch.py` plus
  `tests/test_create_naima_030000_missing_baseline_patch.py`. The patch builder
  reads the real-child scored rows, recovers age from filename, generates
  same-word-count random/unigram/bigram/trigram utterances from the current
  additive `036-041` n-gram dictionaries, and writes a tiny cleaned-data-style
  scorer input.
- Generated and validated:
  - `results/scoring_patches/cleaned_data_patches/naima_030000_missing_baselines/data/preprocessed_data/Providence/Naima/chi.surprisal_scoring.csv`
  - `results/scoring_bundles/naima_030000_missing_baselines_scoring_patch_2026-06-03.tar.gz`
  - row count: 477
  - blank generated baselines: 0 for all four generated columns
  - recovered `age_months`: 36 for every row
- Added scorer-side helpers and copied them into
  `/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/`:
  - `scripts/score_naima_030000_missing_baselines_local.sh`
  - `src/merge_naima_030000_missing_baseline_patch_scores.py`
- Verification:
  - `env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_create_naima_030000_missing_baseline_patch tests.test_build_route1_analysis_dataset` passed with 8 tests.
  - `bash -n scripts/compute_surprisal_mila/score_naima_030000_missing_baselines_local.sh` passed.
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/compute_surprisal_mila/merge_naima_030000_missing_baseline_patch_scores.py src/create_naima_030000_missing_baseline_patch.py` passed.
- Updated the sibling `compute_surprisal_mila` Markdown workflow docs so an
  agent can resume from Git after push/pull:
  `AGENTS.md`, `README.md`, and
  `docs/naima_030000_missing_baseline_patch.md`.

## 2026-06-04 Route 1 Context-Entropy Patch Handoff

- The Mistral context-entropy run in `compute_surprisal_mila` is complete for
  its original manifest: both
  `mila_results/context_entropy_mistral/context_entropy_manifest.csv.gz` and
  `mila_results/context_entropy_mistral/context_entropy_features.csv.gz` have
  1,675,520 rows, and the feature file has 0 blank
  `llm_next_entropy_bits` values.
- The current Route 1 long table contains additional contexts that were not in
  that original manifest. After correcting the entropy attach script to reuse
  entropy by context text across k labels, the remaining gap is 34,141
  child-context rows across 2,250 missing-context audit rows.
- Added `src/create_context_entropy_rescoring_patch.py` and
  `tests/test_create_context_entropy_rescoring_patch.py`.
- Built the scorer handoff:
  - `results/scoring_bundles/route1_missing_context_entropy_patch_2026-06-04/context_entropy_patch_manifest.csv.gz`
  - `results/scoring_bundles/route1_missing_context_entropy_patch_2026-06-04/context_entropy_patch_contexts_with_examples.csv`
  - `results/scoring_bundles/route1_missing_context_entropy_patch_2026-06-04/README.md`
  - `results/scoring_bundles/route1_missing_context_entropy_patch_2026-06-04.tar.gz`
- Patch counts:
  - missing-context audit rows read: 2,250
  - nonempty context rows: 2,250
  - unique scorer contexts written: 2,235
  - duplicate context-id rows collapsed: 15
  - Route 1 rows represented: 34,141
- Copied the patch into the sibling scorer repo:
  - `/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/new_data/route1_missing_context_entropy_patch/`
  - `/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/new_data/route1_missing_context_entropy_patch_2026-06-04.tar.gz`
- Focused verification:
  `./.venv/bin/python -m unittest tests.test_create_context_entropy_rescoring_patch`
  passed with 2 tests.

## 2026-06-04 PBM Additive LSTM Generation Completed

- Completed the real PBM additive age-bin LSTM training and generation run on
  the local PC GPU.
- This run is separate from older LSTM/all-data artifacts. It is the new
  PBM-only same-length generated-utterance baseline intended for later scoring
  in `compute_surprisal_mila`.
- Completed run directory:
  `results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03/`
- Completed run command:

```bash
.venv/bin/python src/run_lstm_additive_age_context_pipeline.py \
  --output_dir results/lstm_baselines/pbm_additive_lstm_training_generation_2026_06_03 \
  --datasets Brown Manchester Providence \
  --contexts 3 4 5 \
  --variants same_length \
  --epochs 20 \
  --embedding_dim 256 \
  --hidden_dim 512 \
  --num_layers 2 \
  --dropout 0.2 \
  --batch_size 256 \
  --max_vocab_size 30000 \
  --device cuda
```

- Validation after completion:
  - 24 model checkpoints found;
  - 24 generation diagnostic rows found;
  - 1,339,524 generated rows across k/bin diagnostics;
  - 446,508 generated rows per LSTM column;
  - 0 empty generated rows;
  - 0 same-length mismatches;
  - 21 PBM `chi.surprisal_scoring_with_lstm_additive.csv` files found;
  - `model_run_manifest.csv` includes `child_output_vocab_size`.
- Generated columns:
  - `lstm_additive_k3_same_length_utterance`
  - `lstm_additive_k4_same_length_utterance`
  - `lstm_additive_k5_same_length_utterance`
- Scorer-ready files for the `compute_surprisal_mila` agent:
  `data/big_cleaned_dataset/default_naturalistic_merged_006_023/preprocessed_data/{Brown,Manchester,Providence}/{child}/chi.surprisal_scoring_with_lstm_additive.csv`
- Added `docs/lstm_additive_pbm_compute_surprisal_handoff_2026-06-04.md`
  as the dedicated handoff for the scoring agent.
- Reminder: this repository does not score the LSTM utterances. Scoring happens
  in `/home/alkan/Portelance/compute_surprisal_mila`.
