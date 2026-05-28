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
