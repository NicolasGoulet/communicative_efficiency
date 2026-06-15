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

## 2026-06-04 PBM Utterance-Information Modeling Proposal Packet

- Added `src/build_utterance_information_model_proposals.py` to build a
  separate model-review packet without modifying the supervisor-facing
  `docs/predicting_utterance_level_information_report.md`.
- Added focused tests in
  `tests/test_build_utterance_information_model_proposals.py` for source CSV
  row counting, scored-file path parsing, source-vs-long-table audit logic, and
  deterministic stratified sampling.
- Installed analysis dependencies in this repo with `uv add statsmodels seaborn
  duckdb`.
- Generated:
  - `docs/utterance_information_model_proposals.md`
  - `docs/utterance_information_model_proposals.html`
  - `notebooks/utterance_information_model_proposals.ipynb`
  - `results/utterance_information_model_proposals/`
  - `figs/utterance_information_model_proposals/`
- Build command:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_utterance_information_model_proposals.py
```

- Source audit:
  - scorer tree: 504 CSV files;
  - source scored rows: 11,607,680;
  - long-table rows: 11,607,680;
  - source/long mismatched groups: 0;
  - raw unscored/blank source rows documented and excluded: 7,632;
  - context entropy feature rows available: 1,675,520.
- Predictor diagnostics:
  effort measures are strongly collinear. VIFs exceed 10 for
  syllables, morphemes, words, and phonemes, so final inferential models should
  not include all effort measures simultaneously.
- Pilot model status:
  OLS, child-clustered OLS, child random-intercept LMM, Gamma GEE baseline
  comparison, and context-entropy Gaussian GEE fit successfully. The child
  random-intercept plus random-age-slope LMM fit but did not converge, so it is
  documented as a candidate requiring a more stable final fitting strategy
  before interpretation.
- Verification:

```bash
.venv/bin/python -m py_compile src/build_utterance_information_model_proposals.py
.venv/bin/python -m unittest tests.test_build_utterance_information_model_proposals
```

Both checks passed on 2026-06-04.

### 2026-06-04 Modeling Proposal Revision: Controlled Plots

- Clarified in `docs/utterance_information_model_proposals.md` that the raw
  mean total-bits age plot is descriptive and does not control for utterance
  size. It should be read alongside adjusted/model-based plots.
- Added a `Unit Labels` section: `dataset` refers to the corpus/source
  collection (`Brown`, `Manchester`, `Providence`), not the individual child;
  individual children are represented by `child_id`.
- Added one result plot per candidate model:
  - `model1_adjusted_total_bits_by_age.*`: total-bit predictions at fixed word
    counts;
  - `model2_adjusted_bits_per_word_by_dataset.*`: bits-per-word predictions by
    corpus at fixed length and `k3` context;
  - `model3_child_random_intercepts.*`: child-specific random intercepts;
  - `model4_random_slope_pilot.*`: random intercept/slope diagnostic for the
    non-converged random-slope pilot;
  - `model5_adjusted_baseline_predictions.*`: adjusted Gamma-GEE predictions
    for real/random/unigram/bigram/trigram targets at fixed length.
- Regenerated `docs/utterance_information_model_proposals.html`.
- Verification:

```bash
env UV_CACHE_DIR=/tmp/uv-cache MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python -m unittest discover -s tests
```

passed with 196 tests.

### 2026-06-08 M1/M2/M3 Utterance-Information Deep Dive

- Added M3 age-by-effort interaction model families to
  `src/build_m1_m2_utterance_information_deep_dive.py`, while keeping words,
  morphemes, both syllable estimates, and phonemes as separate effort-control
  versions.
- M3 formula family: `sum_bits ~ age * effort`, with pooled, child-clustered,
  child fixed-effect, GEE, Gamma/log, and mixed-model sensitivity versions.
- Regenerated the internal review report:
  `docs/utterance_information_m1_m2_deep_dive.html`.
- Added plain-language report scaffolding:
  - model vocabulary for OLS, child-clustered SE, GLM, Gamma/log link, GEE,
    mixed models, and fixed-median prediction lines;
  - one "question / controls / interpretation" block per model-family
    subsection;
  - explicit discussion of why M1 pooled age effects can differ from M2
    child-adjusted developmental effects in unbalanced longitudinal data.
- Added M3 outputs:
  - `results/m1_m2_utterance_information_deep_dive/m3_interaction_adjusted_age_predictions.csv`;
  - `figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png`;
  - one low/median/high effort interaction-line plot per M3 model family.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m2_utterance_information_deep_dive

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed, and the full suite passed with 212 tests.

### 2026-06-08 Route 1 Two-Report Analysis Suite

- Added `src/build_route1_model_report_suite.py` and
  `tests/test_build_route1_model_report_suite.py`.
- The builder creates two internal reports:
  - `docs/utterance_information_m123_extended.html`
  - `docs/utterance_information_research_model_zoo.html`
- The extended M1/M2/M3 report uses the already fitted M1/M2/M3 outputs and
  clarifies:
  - the M1 pooled versus M2 child-adjusted sign reversal;
  - why fixed-median prediction lines are a visualization/control decision;
  - how to interpret M3 age-by-effort interaction coefficients.
- The exploratory model zoo streams the Route 1 long table, derives bounded
  samples plus row-matched baseline deltas, and creates predictors for:
  - caretaker context length;
  - next-token context entropy and certainty;
  - rule-based context question type;
  - fallback-quality flags;
  - real-minus-random/unigram/bigram/trigram deltas.
- Full build command:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_model_report_suite.py
```

- Real build outputs:
  - `results/utterance_information_research_model_zoo/model_zoo_summary.csv`
  - `results/utterance_information_research_model_zoo/model_zoo_coefficients.csv`
  - `results/utterance_information_research_model_zoo/baseline_delta_table.csv.gz`
  - `figs/utterance_information_research_model_zoo/`
- Real model-zoo status on 2026-06-08:
  - 11 candidate models fit successfully;
  - row-matched baseline-delta model used 1,786,032 real-minus-baseline rows;
  - response-level entropy features were not yet present, so the report uses
    next-token context entropy as a provisional context-predictability measure.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_route1_model_report_suite

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed, and the full suite passed with 216 tests.

### 2026-06-08 Internal Child/Baseline/Caretaker Comparison Report Revision

- Reworked `docs/utterance_information_research_model_zoo.html` from a broad
  model-zoo scratchpad into a question-first comparison report.
- The report is now organized around:
  - child versus random;
  - child versus unigram;
  - child versus bigram;
  - child versus trigram;
  - children versus caretakers;
  - context predictability and child effort.
- Added full streamed aggregate tables:
  - `results/utterance_information_research_model_zoo/baseline_trends.csv.gz`
  - `results/utterance_information_research_model_zoo/role_trends.csv.gz`
- Added explicit comparison-model outputs:
  - `results/utterance_information_research_model_zoo/comparison_model_summary.csv`
  - `results/utterance_information_research_model_zoo/comparison_model_coefficients.csv`
- Added dashboard plots:
  - `figs/utterance_information_research_model_zoo/child_vs_random_dashboard.png`
  - `figs/utterance_information_research_model_zoo/child_vs_unigram_dashboard.png`
  - `figs/utterance_information_research_model_zoo/child_vs_bigram_dashboard.png`
  - `figs/utterance_information_research_model_zoo/child_vs_trigram_dashboard.png`
  - `figs/utterance_information_research_model_zoo/child_vs_caretaker_dashboard.png`
- Real build check on 2026-06-08:
  - `comparison_model_summary.csv`: 14 fitted comparison models;
  - `baseline_trends.csv.gz`: 40 full aggregate age-bin/variant rows;
  - `role_trends.csv.gz`: 16 full aggregate age-bin/speaker rows.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_route1_model_report_suite

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_model_report_suite.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed, the real report build completed, and the full suite
passed with 217 tests.

### 2026-06-08 M1-M4 Model-Ladder Report Revision

- Reworked `docs/utterance_information_m1_m2_deep_dive.html` so it follows a
  clean model-ladder structure instead of dumping all model-family tables.
- The report now has one readable section per model:
  - M1: pooled `sum_bits ~ age + effort`;
  - M2: child-adjusted `sum_bits ~ age + effort + child identity`;
  - M3: `sum_bits ~ age * effort`;
  - M4: context entropy as a predictor of effort and information.
- Each model section now includes:
  - question asked;
  - formula;
  - how to read the plot;
  - compact primary table;
  - short takeaway;
  - compact sensitivity snapshot where relevant.
- Added M4 context-entropy machinery to
  `src/build_m1_m2_utterance_information_deep_dive.py`:
  - M4a: `nb_words ~ age * context_entropy + context_length`;
  - M4b: `nb_phonemes ~ age * context_entropy + context_length`;
  - M4c: `sum_bits ~ age + nb_words + context_entropy + C(child_id)`;
  - M4d: `bits_per_word ~ age * context_entropy + log_nb_words`.
- M4a/M4b use Gaussian GEE rather than Poisson GEE in this internal report
  because Poisson GEE produced NaN coefficients on the full real-data run. The
  report labels this as a stable first-pass model; final effort-count models can
  still use a count GLMM or negative-binomial specification in a confirmatory
  analysis.
- New M4 outputs:
  - `results/m1_m2_utterance_information_deep_dive/m4_context_entropy_model_summary.csv`
  - `results/m1_m2_utterance_information_deep_dive/m4_context_entropy_coefficients.csv`
  - `results/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.csv`
  - `figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png`
  - `figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png`
  - `figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_coefficients.png`
- Real M4 build check:
  - 441,413 child k3 real rows with context entropy;
  - 21 children;
  - all four M4 rows fit with nonmissing context-entropy coefficients.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m2_utterance_information_deep_dive

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed, the real M1-M4 report build completed, and the full suite
passed with 218 tests.

### 2026-06-08 Expanded Model-Atlas Plot Explanation Revision

- Reworked `src/build_route1_model_report_suite.py` so
  `docs/utterance_information_research_model_zoo.md` and `.html` now read as an
  expanded internal model atlas instead of a table-heavy dump.
- Added structured Z1-Z11 model cards to the report generator. Each card now
  includes:
  - the question asked by the model;
  - the exact formula stored in the model summary;
  - why the model belongs in the expanded atlas rather than the compact M1-M4
    ladder;
  - a local "How to read this plot" paragraph immediately before the plot;
  - a compact result sentence and small coefficient table.
- Added direct card plots for:
  - Z1 child information with child identity;
  - Z2 nonlinear information density;
  - Z3 context entropy predicting effort;
  - Z4 context entropy predicting information density;
  - Z5 scoring context-window sensitivity;
  - Z6 question-type effort;
  - Z7 real children versus all matched baselines;
  - Z8 children versus caretakers;
  - Z9 information per phoneme;
  - Z10 context certainty predicting effort;
  - Z11 real-minus-baseline delta.
- Added explicit plot-reading paragraphs beside the omnibus baseline plots,
  pairwise child-vs-baseline dashboards, child-vs-caretaker dashboard, context
  entropy plots, question-type plot, predictor-correlation heatmap, and
  coefficient overview.
- Audit after regeneration:

```bash
.venv/bin/python -c "from pathlib import Path; text=Path('docs/utterance_information_research_model_zoo.md').read_text(); print('images', text.count('![')); print('how_to_read', text.count('How to read this plot')); print('z_cards', sum(1 for line in text.splitlines() if line.startswith('## Z')))"
```

returned:

```text
images 24
how_to_read 24
z_cards 11
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_route1_model_report_suite

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_model_report_suite.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed, the real report build completed, and the full suite passed
with 220 tests.

### 2026-06-08 M4/M5/M6 And Effort-Controlled Model-Zoo Revision

- Corrected the internal model-ladder report after review:
  - M4 now asks the same information-outcome question as M1/M2/M3 while adding
    context entropy as an additional predictor.
  - The core M4 formula family is:

```text
sum_bits ~ age + effort + context_entropy + child identity
```

  - M4 is repeated across the same five effort controls used elsewhere:
    words, morphemes, CMU/pkg syllables, package syllables, and phonemes.
  - M4 sensitivity versions include GEE, Gamma/log GEE, an age-by-context
    entropy version, and an M3-plus-context version.
- Added M5 and M6 to `src/build_m1_m2_utterance_information_deep_dive.py`:
  - M5 is an all-main-effects model with age, all effort measures, context
    entropy, context length, and child fixed effects.
  - M6 is a theory-rich interaction model with age-by-effort, age-by-context,
    context-by-word, and context-by-phoneme interactions plus child fixed
    effects.
  - Both are explicitly documented as saturated exploratory stress tests, not
    cleaner primary evidence, because the effort measures are highly
    collinear.
- Added an explicit uneven-child-age-coverage section to the M1-M6 report:
  child-clustered standard errors handle within-child dependence but do not by
  themselves solve unbalanced longitudinal coverage; child fixed effects,
  child-specific age slopes, random-slope sensitivity models, and model
  comparisons are the relevant safeguards.
- New M1-M6 outputs:

```text
results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_model_summary.csv
results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_coefficients.csv
results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.csv
figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png
figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png
```

- Updated the expanded model zoo so baseline and caretaker comparisons are
  effort-controlled rather than word-only:
  - child vs random;
  - child vs unigram;
  - child vs bigram;
  - child vs trigram;
  - child vs caretaker.
- Each comparison is repeated with one effort control at a time:

```text
Words
Morphemes
Syllables: CMU/pkg
Syllables: pkg
Phonemes
```

- Real model-zoo audit after regeneration:

```text
comparison_model_summary.csv rows: 45
models with explicit effort sweeps: 45
all effort-sweep comparison rows status: fit
model-zoo Markdown images: 26
model-zoo "How to read this plot" paragraphs: 26
Z model cards: 11
```

- New model-zoo plots:

```text
figs/utterance_information_research_model_zoo/effort_controlled_comparison_model_r2.png
figs/utterance_information_research_model_zoo/effort_controlled_comparison_age_coefficients.png
```

- Regenerated:

```text
docs/utterance_information_m1_m2_deep_dive.html
docs/utterance_information_research_model_zoo.html
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m2_utterance_information_deep_dive

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_route1_model_report_suite

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed, both real reports regenerated, and the full suite passed
with 221 tests.

### 2026-06-08 Analysis/Report Stage Split For Internal Modeling Reports

- Split the two internal report builders into separate analysis and rendering
  stages so wording/layout changes do not refit every model:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_model_report_suite.py --stage report
```

- Use `--stage report` when only Markdown/HTML text, section ordering, table
  inclusion, or explanatory wording needs to change.
- Use `--stage analysis` when the scored data, predictors, formulas, model
  families, or figures that depend on fitted model outputs change.
- Use `--stage all` when intentionally rebuilding both model outputs and the
  rendered reports from scratch.
- Added regression tests proving report-only rebuilds can run from the saved
  tables/figures after the raw analysis input has been removed.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_model_report_suite.py --stage report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

The report-only commands completed successfully, and the full suite passed with
222 tests.

### 2026-06-08 M1-M6 Report Rework And Effort-Level Models

- Reworked `src/build_m1_m2_utterance_information_deep_dive.py` so the
  internal M1-M6 report is more readable:
  - each model section now states the question, formula, plot interpretation,
    table-column meaning, compact result table, and takeaway;
  - the report no longer dumps multiple sensitivity tables inside each main
    model section;
  - plots included in the report have nearby "how to read" explanations.
- Removed the previous M5/M6 continuous-all-efforts stress-test logic from the
  main model ladder. It violated the cleaner one-effort-at-a-time rule because
  words, morphemes, syllables, and phonemes are highly collinear.
- New M5/M6 logic:

```text
M5: sum_bits ~ age + context_entropy + C(effort_level) + C(child_id)
M6: sum_bits ~ age * context_entropy
              + age * C(effort_level)
              + context_entropy * C(effort_level)
              + C(child_id)
```

- `effort_level` is low/mid/high, defined by tertiles within one effort unit at
  a time. The words version uses word-count tertiles, the phoneme version uses
  phoneme-count tertiles, and so on. The models remain effort-separated.
- Added a targeted analysis stage so M5/M6 can be refit without rerunning all
  M1-M4 sensitivity models:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage m5m6

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage report
```

- Regenerated the real M1-M6 report and effort-level plots:

```text
docs/utterance_information_m1_m2_deep_dive.html
docs/utterance_information_m1_m2_deep_dive.md
figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png
figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png
```

- Real M5/M6 outputs were refreshed under:

```text
results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_model_summary.csv
results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_coefficients.csv
results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.csv
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m2_utterance_information_deep_dive
```

passed with 10 tests. The real `--stage m5m6` and `--stage report` commands
completed successfully.

Full-suite verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

passed with 224 tests.

### 2026-06-08 M1-M6 Subvariant And Diagnostic-View Cleanup

- Clarified the internal M1-M6 report language:
  - a **subvariant** is now explicitly defined as a real model change, such as
    a different formula, estimator, link, child-dependence structure, or effort
    source;
  - a **diagnostic view** is explicitly not a new model, only the same fitted
    subvariant plotted with different reference values.
- Wired the existing M1-M3 expanded-family renderer into
  `docs/utterance_information_m1_m2_deep_dive.md/html`, so the report now has
  its own visible subsection for each OLS/clustered-OLS/GLM/GEE/mixed/fixed
  effect subvariant. Each subsection includes:
  - the question asked;
  - the formula;
  - how to read the coefficients;
  - a compact effort-by-effort result table;
  - the relevant adjusted regression-line figure.
- Updated M4 plotting so it no longer only shows M4a. The line-variant stage
  now writes one context-entropy prediction plot for each M4 subvariant:

```text
figs/m1_m2_utterance_information_deep_dive/m4_m4a_context_entropy_adjusted_predictions.png
figs/m1_m2_utterance_information_deep_dive/m4_m4b_context_entropy_adjusted_predictions.png
figs/m1_m2_utterance_information_deep_dive/m4_m4c_context_entropy_adjusted_predictions.png
figs/m1_m2_utterance_information_deep_dive/m4_m4d_context_entropy_adjusted_predictions.png
figs/m1_m2_utterance_information_deep_dive/m4_m4e_context_entropy_adjusted_predictions.png
```

- Updated M5/M6 report text so the low/mid/high effort split is not the only
  displayed evidence. The report now separates:
  - effort-source subvariants: words, morphemes, both syllable measures, and
    phonemes;
  - diagnostic views: low/mid/high effort lines and averaged effort-level
    lines.
- Commands run:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage line_variants

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m2_utterance_information_deep_dive

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

- Verification:
  - focused M1-M6 report tests passed with 11 tests;
  - full suite passed with 225 tests;
  - regenerated report paths:

```text
docs/utterance_information_m1_m2_deep_dive.html
docs/utterance_information_m1_m2_deep_dive.md
```

### 2026-06-08 M1-M3 Clustered-SE Plot Correction

- User flagged that M1 clustered and non-clustered plots looked suspiciously
  identical. Audit confirmed the fitted mean lines are supposed to be identical
  for OLS versus child-clustered OLS when the formula is the same:

```text
M1 ols vs ols_cluster: rows=450 max_abs_diff=0 mean_abs_diff=0
M3 ols_interaction vs ols_cluster_interaction: rows=450 max_abs_diff=0 mean_abs_diff=0
```

- The report presentation was still misleading because it plotted only the
  mean line. For covariance-only variants, the scientific difference is in the
  uncertainty and p-values, not the fitted mean.
- Added model-based 95% confidence ribbons to M1-M3 expanded subvariant plots
  whenever `statsmodels` exposes prediction intervals. The regenerated M1 audit
  now shows identical fitted lines but different confidence bands:

```text
Words: line max diff=0, ci_low max diff=2.0187, ci_high max diff=2.0187
Morphemes: line max diff=0, ci_low max diff=1.8833, ci_high max diff=1.8833
Syllables: CMU/pkg: line max diff=0, ci_low max diff=1.7114, ci_high max diff=1.7114
Syllables: pkg: line max diff=0, ci_low max diff=1.81635, ci_high max diff=1.81635
Phonemes: line max diff=0, ci_low max diff=1.72725, ci_high max diff=1.72725
```

- Added a targeted stage for refreshing only the M1-M3 expanded subvariant
  plots and tables:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage expanded_plots
```

- Regenerated the report:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m2_utterance_information_deep_dive.py --stage report
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m2_utterance_information_deep_dive

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

Focused tests passed with 12 tests. Full suite passed with 226 tests.

### 2026-06-08 Expanded Research Model Zoo Family/Subvariant Rebuild

- Reworked `src/build_route1_model_report_suite.py` so the larger exploratory
  model zoo follows the same logic as the M1-M6 internal report:
  - each Z-family has a scientific question family;
  - each real subvariant has its own subsection with question, formula,
    estimator, compact fit table, and key coefficients;
  - alternate plots are described as diagnostic views rather than being treated
    as separate models.
- Decoupled the workflow more explicitly:
  - `--stage extract`: refresh bounded samples and aggregate tables from the
    large Route 1 long table;
  - `--stage model`: refit models and regenerate plots from the saved bounded
    samples only;
  - `--stage report`: rebuild Markdown/HTML from existing CSV/figure outputs.
- Replaced the earlier all-effort formulas in the expanded zoo with
  effort-separated variants. Words, morphemes, both syllable estimates, and
  phonemes are no longer combined in the same zoo formula.
- The real regenerated zoo now contains:
  - `results/utterance_information_research_model_zoo/model_zoo_summary.csv`
    with 56 fitted Z-family subvariants;
  - `results/utterance_information_research_model_zoo/comparison_model_summary.csv`
    with 45 fitted effort-controlled comparison models;
  - `results/utterance_information_research_model_zoo/zoo_model_variant_manifest.csv`
    with one row per Z-family subvariant;
  - family-level coefficient plots:
    `figs/utterance_information_research_model_zoo/z1_family_coefficients.png`
    through `z11_family_coefficients.png`.
- Regenerated:

```text
docs/utterance_information_research_model_zoo.md
docs/utterance_information_research_model_zoo.html
docs/utterance_information_m123_extended.md
docs/utterance_information_m123_extended.html
```

- Commands run:

```bash
env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache \
  uv run python src/build_route1_model_report_suite.py --stage model

env MPLCONFIGDIR=/tmp/matplotlib UV_CACHE_DIR=/tmp/uv-cache \
  uv run python src/build_route1_model_report_suite.py --stage report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_route1_model_report_suite

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

- Verification:
  - real model-zoo summary: 56/56 Z-family subvariants fit;
  - real comparison summary: 45/45 effort-controlled comparison models fit;
  - focused suite passed with 8 tests;
  - full suite passed with 226 tests.

### 2026-06-09 Compact M1-M6 Quick-Share Report

- Added `src/build_m1_m6_quick_share_report.py`, a lightweight renderer that
  reads the already-generated M1-M6 analysis outputs and does not refit any
  models.
- Added `tests/test_build_m1_m6_quick_share_report.py` with fake output tables
  to protect the compact report structure.
- Generated:

```text
docs/utterance_information_m1_m6_quick_share.md
docs/utterance_information_m1_m6_quick_share.html
```

- The report is intentionally short:
  - one section each for M1-M6;
  - one best plot per model;
  - formula, quick takeaway, and "how to read the plot" text near each plot;
  - a tiny M1-vs-M2 coefficient overview;
  - no model refitting and no supervisor-facing report edits.
- Build command:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_quick_share_report.py
```

- Focused verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m6_quick_share_report
```

Focused test passed with 1 test.

### 2026-06-09 Dual-Effort Compact M1-M6 Quick-Share Revision

- Added a separate fitting/plotting stage:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/fit_m1_m6_dual_effort_quick_models.py
```

- This stage fits every M1-M6 family with two effort strategies:
  - `continuous`: utterance effort is kept as the exact numeric count and
    controlled directly;
  - `effort_level`: the same effort unit is converted to low/mid/high tertile
    groups and entered categorically.
- Each model is repeated separately for the five effort units: words,
  morphemes, CMU/pkg syllables, package syllables, and phonemes.
- The dual-effort analysis outputs are:

```text
results/m1_m6_dual_effort_quick_share/dual_model_summary.csv
results/m1_m6_dual_effort_quick_share/dual_model_predictions.csv
results/m1_m6_dual_effort_quick_share/dual_model_audit.csv
figs/m1_m6_dual_effort_quick_share/m1_dual_effort_predictions.png
figs/m1_m6_dual_effort_quick_share/m2_dual_effort_predictions.png
figs/m1_m6_dual_effort_quick_share/m3_dual_effort_predictions.png
figs/m1_m6_dual_effort_quick_share/m4_dual_effort_predictions.png
figs/m1_m6_dual_effort_quick_share/m5_dual_effort_predictions.png
figs/m1_m6_dual_effort_quick_share/m6_dual_effort_predictions.png
```

- The real run produced 60 fitted model rows:
  `6 models * 5 effort units * 2 effort strategies`; all rows have
  `status=fit`.
- Updated `src/build_m1_m6_quick_share_report.py` so it is report-only again:
  it reads the saved dual-effort CSV/PNG artifacts and renders:

```text
docs/utterance_information_m1_m6_quick_share.md
docs/utterance_information_m1_m6_quick_share.html
```

- Focused verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m6_quick_share_report
```

Focused test passed with 2 tests.

- Full verification after the dual-effort quick-share revision:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

Full suite passed with 228 tests. The console emitted the expected statsmodels
warnings from synthetic mixed/GLM test fixtures, but there were no failures.

### 2026-06-09 M1-M6 Results Interpretation Notes

- Added `src/build_m1_m6_results_interpretation_report.py`, a report-only
  renderer that reads the saved dual-effort M1-M6 outputs and writes narrative
  interpretation notes. It does not refit models.
- Generated:

```text
docs/utterance_information_m1_m6_results_interpretation.md
docs/utterance_information_m1_m6_results_interpretation.html
```

- The document interprets the compact M1-M6 report in relation to the
  communicative-efficiency questions:
  - M1-M6 currently answer the informativeness side:
    `sum_bits ~ age + effort (+ child identity/context/interactions)`;
  - the strongest current result is the continuous-effort, child-adjusted
    downward age pattern in M2/M4/M5/M6;
  - low/mid/high effort-level models are useful diagnostics but are coarser
    than exact effort control;
  - next-token context entropy is treated as provisional because the stronger
    supervisor-facing context-predictability question needs response-level
    entropy sampled over complete possible responses;
  - the next planned model family should use effort as the outcome:
    `effort ~ age + response_entropy + context_length + question_type + child`.
- Literature anchors included in the report:
  - Tal, Smith, Arnon, and Culbertson (2023), child communicative efficiency;
  - Tal, Grossman, Rohde, and Arnon (2023), efficient redundancy with learners;
  - Wang, Yu, and Shao (2026), joint surprisal/efficiency framing.
- Commands run:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_results_interpretation_report.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_m1_m6_results_interpretation_report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest discover -s tests
```

- Verification:
  - focused interpretation-report tests passed with 3 tests;
  - full suite passed with 231 tests;
  - statsmodels emitted expected warnings from synthetic model-test fixtures,
    with no failures.

### 2026-06-09 Fixed-Effort Slice Audit And M1-M6 Replot

- Problem corrected: the previous continuous-effort plots used a single median
  effort value. That is only one conditional slice of a model fit on all
  lengths, so it is not enough as the main visual evidence.
- Checked the local Advanced Data Analytics course context at:

```text
/home/apaixonada/school_agent/knowledge_base/courses/advanced-data-analytics/
```

- Relevant course constraints applied:
  - `sum_bits` is continuous;
  - rows are repeated within children, so child identity/dependence must be
    handled in the model family or uncertainty structure;
  - prediction summaries and inferential coefficients should not be confused;
  - fitting/prediction stages should be separated from report rendering.
- Added the effort distribution audit:

```text
src/build_effort_slice_audit_report.py
docs/utterance_effort_slice_audit.md
docs/utterance_effort_slice_audit.html
results/effort_slice_audit/effort_quantile_summary.csv
results/effort_slice_audit/effort_value_distribution.csv
results/effort_slice_audit/effort_by_age_bin_distribution.csv
results/effort_slice_audit/effort_level_definitions.csv
results/effort_slice_audit/proposed_fixed_effort_slices.csv
figs/effort_slice_audit/effort_value_distributions.png
```

- Real Route 1 child/k3 effort quantiles:

```text
Words: mean=2.66, p25=1, p50=2, p75=4, p90=5, p95=6, p99=10, max=70
Morphemes: mean=2.96, p25=1, p50=2, p75=4, p90=6, p95=7, p99=11, max=98
Syllables CMU/pkg: mean=3.24, p25=1, p50=3, p75=4, p90=6, p95=8, p99=12, max=84
Syllables pkg: mean=3.43, p25=1, p50=3, p75=5, p90=7, p95=8, p99=12, max=84
Phonemes: mean=8.04, p25=3, p50=7, p75=11, p90=16, p95=19, p99=29, max=266
```

- Low/mid/high effort groups are defined separately for each effort unit using
  empirical tertiles:

```text
low effort  = value <= p33
high effort = value >= p66
mid effort  = values between p33 and p66
```

  Because effort counts are integer-valued and heavily skewed, low/mid/high
  groups are diagnostic coarse categories, not a replacement for exact fixed
  effort slices.
- Added the fixed-effort M1-M6 workflow:

```text
src/fit_m1_m6_fixed_effort_slice_models.py
docs/utterance_information_m1_m6_fixed_effort_slices.md
docs/utterance_information_m1_m6_fixed_effort_slices.html
results/m1_m6_fixed_effort_slices/fixed_effort_model_summary.csv
results/m1_m6_fixed_effort_slices/marginal_adjusted_predictions.csv
results/m1_m6_fixed_effort_slices/fixed_effort_predictions.csv
results/m1_m6_fixed_effort_slices/selected_fixed_effort_values.csv
results/m1_m6_fixed_effort_slices/displayed_fixed_effort_values.csv
figs/m1_m6_fixed_effort_slices/
```

- Fixed-slice workflow stages:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/fit_m1_m6_fixed_effort_slice_models.py --stage analysis

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/fit_m1_m6_fixed_effort_slice_models.py --stage report
```

- Why this script refits models: previous outputs saved coefficient CSVs and
  figures, but not serialized statsmodels objects. The script refits the same
  M1-M6 formulas once per effort unit to produce new prediction grids. It does
  **not** fit separate models for each fixed effort value.
- Fixed values used:
  - words: exact values 1-12 saved;
  - morphemes: exact values 1-12 saved;
  - CMU/pkg syllables: data-supported dense core 1-8;
  - pkg syllables: data-supported dense core 1-8;
  - phonemes: data-supported dense core 1-19;
  - compact anchors also saved for p25/p50/p75 and p10/p50/p90.
- Readability rule:
  - all fixed values are kept in `fixed_effort_predictions.csv`;
  - dense plotted panels show at most 8 representative values per effort unit;
  - anchor plots show all 3 lines.
- Added marginal adjusted global trends:
  - one line per M1-M6 model and effort unit;
  - at each age, predictions are averaged over a standardization sample of
    observed rows, preserving the observed effort, child, and context
    distribution;
  - these are global prediction summaries, not new inferential tests and not
    restricted to one utterance length.
- Real fixed-slice run audit:

```text
rows: 446,985
children: 21
selected fixed value rows: 89
fitted model rows: 30
marginal prediction rows: 2,700
fixed-slice prediction rows: 48,060
```

- Focused verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m py_compile src/build_effort_slice_audit_report.py \
                src/fit_m1_m6_fixed_effort_slice_models.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_effort_slice_audit_and_fixed_models
```

Focused tests passed with 4 tests.

### 2026-06-04 Modeling Proposal Revision: Effort and Child-Control Sensitivity

- Extended `src/build_utterance_information_model_proposals.py` with
  utterance-level effort-control sensitivity models. These use total
  utterance bits as the outcome and swap exactly one effort control at a time:
  words, surface morphemes, CMU/pkg syllables, package syllables, or phonemes.
  This avoids putting highly collinear effort measures in the same regression.
- Added two comparison scopes:
  - child real utterances plus generated baselines;
  - child real utterances plus generated baselines plus caretakers.
- Added both short and full versions of the effort-sensitivity plots:
  - `effort_sensitivity_child_real_and_baselines_short.*`
  - `effort_sensitivity_child_real_and_baselines_full.*`
  - `effort_sensitivity_child_real_baselines_and_caretaker_short.*`
  - `effort_sensitivity_child_real_baselines_and_caretaker_full.*`
- Added the real-child-only child-control ladder:
  - OLS with age + effort only, using child-clustered standard errors;
  - OLS with age + effort + child fixed effects;
  - Gaussian GEE with child-level exchangeable correlation.
- Added `child_control_ladder_r2_age_pvalues.*` plus
  `results/utterance_information_model_proposals/child_control_ladder_stats.csv`.
- Clarified in the proposal report that a singular random-effect covariance in
  the statsmodels mixed model is an estimation warning, not a reason to ignore
  child-level variation. Stable child-control alternatives are child fixed
  effects and GEE grouped by child.
- Regenerated `docs/utterance_information_model_proposals.html`.
- Verification:

```bash
env UV_CACHE_DIR=/tmp/uv-cache MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python -m unittest discover -s tests
```

passed with 196 tests.

### 2026-06-09 Exhaustive Fixed-Effort M1-M6 Atlas

- Added an internal atlas report for the exact fixed-effort question:

```text
src/build_m1_m6_fixed_effort_atlas_report.py
tests/test_build_m1_m6_fixed_effort_atlas_report.py
docs/utterance_information_m1_m6_fixed_effort_atlas.md
docs/utterance_information_m1_m6_fixed_effort_atlas.html
results/m1_m6_fixed_effort_atlas/
figs/m1_m6_fixed_effort_atlas/
```

- The atlas report is report/plotting-only. It reads the saved M1-M6
  continuous-effort outputs from `results/m1_m6_fixed_effort_slices/` and does
  not refit models.
- Regenerated the effort-slice audit so `proposed_fixed_effort_slices.csv`
  includes `top_frequency_12`, the 12 most frequent exact values per effort
  unit.
- Regenerated the fixed-slice model/prediction stage from saved code:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_effort_slice_audit_report.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/fit_m1_m6_fixed_effort_slice_models.py --stage analysis

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/fit_m1_m6_fixed_effort_slice_models.py --stage report

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_fixed_effort_atlas_report.py
```

- Real fixed-slice run audit after adding top-frequency slices:

```text
input: results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_long.csv.gz
context_k: k3
rows: 446,985
children: 21
selected fixed value rows: 149
fitted model rows: 30
marginal adjusted prediction rows: 2,700
fixed-slice prediction rows: 80,460
```

- Atlas figure manifest:

```text
results/m1_m6_fixed_effort_atlas/atlas_figure_manifest.csv
30 model-by-effort fixed-slice figures
2 row-support distribution figures
32 PNG figures total in figs/m1_m6_fixed_effort_atlas/
```

- Atlas effort-bin logic:
  - words: exact fixed values 1-4, 5-8, 9-12;
  - morphemes: exact fixed values 1-4, 5-8, 9-12;
  - CMU/pkg syllables: top-12 observed values split into 1-4, 5-8, 9-12;
  - pkg syllables: top-12 observed values split into 1-4, 5-8, 9-12;
  - phonemes: top-12 observed values split into 2-5, 6-9, 10-13.
- Added saved atlas summaries:

```text
results/m1_m6_fixed_effort_atlas/atlas_effort_bin_definitions.csv
results/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution.csv
results/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution_by_age.csv
results/m1_m6_fixed_effort_atlas/atlas_model_fit_summary.csv
results/m1_m6_fixed_effort_atlas/atlas_predictor_significance_summary.csv
results/m1_m6_fixed_effort_atlas/atlas_fixed_slice_slopes.csv
results/m1_m6_fixed_effort_atlas/atlas_figure_manifest.csv
```

- Important numeric summaries from the atlas:
  - M1 pooled age+effort has 0/5 negative age slopes and 2/5 significant age
    slopes;
  - M2 child-identity model has 5/5 negative age slopes and 5/5 significant
    age slopes;
  - M3-M6 all have 5/5 negative age slopes, with 4/5 or 5/5 significant age
    slopes depending on the interaction model;
  - mean in-sample R2 across effort units ranges from 0.619 for M1 to 0.633
    for M6;
  - context entropy is significant in 15/15 model-effort rows where it is
    included, with negative coefficients in this current next-token entropy
    implementation.
- Interpretation guardrails written into the report:
  - coefficient tables provide inferential slopes and p-values;
  - fixed-slice slope tables are descriptive slopes from plotted prediction
    lines, not separate inferential models;
  - shaded ribbons are model-confidence bands for fitted mean lines, not the
    full observed data spread;
  - exact fixed effort values change only the prediction slice, not the fitted
    data used by the model.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_effort_slice_audit_and_fixed_models \
              tests.test_build_m1_m6_fixed_effort_atlas_report
```

passed with 7 tests.

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

passed with 238 tests. Statsmodels emitted expected warnings from synthetic
mixed/GLM fixtures, with no failures.

## 2026-06-09 - Context-Predictor Permutation Memory Fix

- The first real run of `src/build_context_predictor_permutation_reports.py`
  was stopped because memory use was far too high for a report-building
  workflow.
- Root causes identified:
  - all `k0`-`k3` child-real rows were being loaded and measured in one frame;
  - context counts were attached with a large dataframe merge;
  - fitted statsmodels result objects were kept in memory until all models had
    finished, which also retained large design matrices.
- Fix implemented:
  - process one context window at a time;
  - map context-count checkpoint rows by `context_text` instead of merging a
    giant context table;
  - write measured rows as per-`k` files plus
    `route1_real_child_context_measures_manifest.csv`;
  - extract coefficients, p-values, R2, RMSE, MAE, AIC, and BIC immediately
    after each fit, then discard the heavy model result object.
  - add `--context-count-checkpoint` so a scratch smoke run can reuse the
    existing context-count checkpoint without writing into the main output
    directory.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_context_predictor_permutation_reports
```

passed with 3 tests.

## 2026-06-15 - PC Response-Space Entropy Pilot Launch Fixes

- The first PC run exposed two implementation issues:
  - `src/sample_context_responses.py` defaulted `--model-dir` to a
    project-local cache under `results/response_level_context_entropy/model_cache`,
    which caused a redundant/incomplete Mistral download even though the PC had
    a complete shared Hugging Face cache.
  - the sampler tried to generate `batch_contexts * samples_per_context`
    continuations in one `model.generate` call. With the planned pilot settings,
    that would have been 200 simultaneous continuations, too risky for the
    16GB RTX 4060 Ti.
- Fixes made:
  - default `--model-dir` is now `None`, so Transformers uses the shared
    Hugging Face cache unless a direct local snapshot/cache is explicitly
    supplied;
  - `resolve_model_source()` supports either the shared cache, a cache
    directory, or a direct local snapshot containing `config.json`;
  - sampled rows are appended incrementally to the output CSV/CSV.GZ, making
    long GPU runs resumable;
  - `--batch-samples` was added to microbatch repeated samples while preserving
    the scientific `samples_per_context` value;
  - Transformers 5 compatibility was fixed by replacing the rejected
    `generator=` argument with explicit Torch seeding before each microbatch.
- Verification on the laptop:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_response_level_context_entropy \
              tests.test_build_response_entropy_pilot_grid

.venv/bin/python -m py_compile src/sample_context_responses.py
```

passed with 11 focused tests.

- Verification on the PC:
  - removed incomplete duplicate cache:

```text
/home/alkan/Portelance/communicative_efficiency/results/response_level_context_entropy/model_cache
```

  - preserved complete shared model cache:

```text
/home/alkan/.cache/huggingface/hub/models--mistralai--Mistral-7B-v0.3
```

  - tiny GPU smoke test wrote two sampled rows to:

```text
results/response_entropy_pilot_grid/pilot_response_samples_smoke.csv.gz
```

  - `--batch-samples 8` and `--batch-samples 16` smoke tests both succeeded;
  - `--batch-samples 16` also succeeded on the longest selected pilot context;
  - the 600-row partial output from the slower `--batch-samples 4` run was
    discarded so the final pilot has one consistent generation setting.

- Full PC pilot launched cleanly in the background:

```bash
cd /home/alkan/Portelance/communicative_efficiency

nohup env HF_HOME=/home/alkan/.cache/huggingface MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python src/sample_context_responses.py \
  --manifest results/response_entropy_pilot_grid/pilot_generation_manifest.csv \
  --output results/response_entropy_pilot_grid/pilot_response_samples.csv.gz \
  --model mistralai/Mistral-7B-v0.3 \
  --temperatures 0.3,0.5,0.7,1.0,1.3,1.6 \
  --samples-per-context 100 \
  --batch-contexts 2 \
  --batch-samples 16 \
  --max-new-tokens 24 \
  --top-p 0.95 \
  --top-k 0 \
  --dtype bfloat16 \
  --device auto \
  > results/response_entropy_pilot_grid/logs/pilot_generation.log 2>&1 &
```

PID recorded on the PC:

```text
results/response_entropy_pilot_grid/logs/pilot_generation.pid
PID 9701
```

- Initial health check:
  - GPU: RTX 4060 Ti, about 14.36GB / 16.38GB VRAM used, 99% utilization;
  - output file began writing successfully at
    `results/response_entropy_pilot_grid/pilot_response_samples.csv.gz`;
  - process active as `.venv/bin/python src/sample_context_responses.py ...`.
- Progress check command:

```bash
cd /home/alkan/Portelance/communicative_efficiency
ps -p "$(cat results/response_entropy_pilot_grid/logs/pilot_generation.pid)" \
  -o pid,etime,%cpu,%mem,rss,cmd
nvidia-smi
ls -lh results/response_entropy_pilot_grid/pilot_response_samples.csv.gz
tail -n 40 results/response_entropy_pilot_grid/logs/pilot_generation.log
```

- After generation finishes, run diagnostics on the PC:

```bash
cd /home/alkan/Portelance/communicative_efficiency
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_pilot_grid.py \
  --stage diagnostics \
  --samples results/response_entropy_pilot_grid/pilot_response_samples.csv.gz \
  --output-dir results/response_entropy_pilot_grid
```

- A diagnostics command was run while generation was still in progress. That
  partial run had only 6,600 rows, 66 contexts, and temperature `0.3` only, so
  it is **not** a valid final pilot diagnostic report.
- Added a completion audit to the diagnostics stage:
  - writes `results/response_entropy_pilot_grid/pilot_completion_audit.csv`;
  - checks the sample file against
    `results/response_entropy_pilot_grid/pilot_generation_manifest.csv`,
    expected temperatures, and `samples_per_context`;
  - refuses to render final diagnostics unless all context-temperature pairs
    are complete;
  - `--allow-incomplete-diagnostics` exists only for explicit debugging.
- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_response_entropy_pilot_grid \
              tests.test_response_level_context_entropy

.venv/bin/python -m py_compile \
  src/build_response_entropy_pilot_grid.py \
  src/sample_context_responses.py
```

passed with 12 focused tests.

## 2026-06-15 - Mila Plan For Response-Space Entropy Generation

- Added a dedicated handoff note:

```text
docs/response_entropy_mila_generation_plan.md
```

- Motivation:
  - the PC pilot is useful for output-quality and temperature diagnostics;
  - production response-space entropy scales as
    `unique_contexts x temperatures x samples_per_context`;
  - the RTX 4060 Ti 16GB forces small microbatches, so production should move
    to Mila if the final manifest is large.
- Recommended Mila strategy:
  - keep the same scientific settings decided from the pilot;
  - shard the manifest by context rows;
  - run Slurm array tasks over `temperature x shard_id`;
  - write one sample CSV per shard and temperature;
  - use one shared Hugging Face cache via `HF_HOME`, preferably on scratch;
  - audit completion before any analysis uses the generated samples.
- Important distinction:
  - `samples_per_context` is the scientific sample size;
  - `batch_samples` is only a computational microbatch for GPU memory.
- Stop condition:
  - do not launch the main Mila generation run yet;
  - first finish the current PC pilot, run final diagnostics, inspect
    temperature/output-quality/stability results, and produce recommendations
    for user review.

## 2026-06-15 - Pawar-Style Age-Trajectory Robustness Report

- Added a complementary robustness workflow for Route 1 real child utterance
  analyses:

```text
src/build_age_scrambling_robustness_report.py
tests/test_build_age_scrambling_robustness_report.py
docs/utterance_information_age_scrambling_robustness.md
docs/utterance_information_age_scrambling_robustness.html
```

- Important implementation correction: the default source is now the split
  scored-result tree, not the 11M-row long table. The script streams only real
  child scored files:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023/
```

- It recomputes effort counts from `chi_utterance_clean`, attaches context
  entropy from:

```text
results/external/compute_surprisal_mila/context_entropy_mistral/context_entropy_features.csv.gz
```

  and immediately aggregates to child-session-context units. This avoids
  keeping utterance-level rows in memory for the robustness analysis.

- Full real run command:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_age_scrambling_robustness_report.py \
  --stage full \
  --n-reps 100 \
  --balanced-units-per-bin 50
```

- Audit:

```text
source files read: 84
source rows read: 1,787,940
source rows kept: 1,787,940
source rows dropped: 0
unit rows: 3,932
children: 21
datasets: 3
child sessions: 983
context windows: k0,k1,k2,k3
observed model rows fit: 105
replicate model rows: 42,000
summary rows: 420
```

- Entropy attachment audit by context window:

```text
k0 rows kept: 446,985; entropy matched: 0; entropy missing: 446,985
k1 rows kept: 446,985; entropy matched: 442,220; entropy missing: 4,765
k2 rows kept: 446,985; entropy matched: 441,461; entropy missing: 5,524
k3 rows kept: 446,985; entropy matched: 441,413; entropy missing: 5,572
```

  The k0 entropy gaps are intentional because k0 has no context. The k1-k3
  gaps are carried as missing entropy in the source audit; M4-M6 naturally use
  complete unit rows for entropy models.

- Saved outputs:

```text
results/age_scrambling_robustness/age_scrambling_unit_frame.csv.gz
results/age_scrambling_robustness/age_scrambling_source_file_audit.csv
results/age_scrambling_robustness/age_scrambling_observed_model_summary.csv
results/age_scrambling_robustness/age_scrambling_replicate_age_slopes.csv.gz
results/age_scrambling_robustness/age_scrambling_robustness_summary.csv
figs/age_scrambling_robustness/
```

- Future fast refit mode:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_age_scrambling_robustness_report.py \
  --stage analysis \
  --source unit-frame \
  --unit-frame-input results/age_scrambling_robustness/age_scrambling_unit_frame.csv.gz
```

  Use this when changing model/scrambling logic but not the underlying scored
  data or effort-count definitions.

- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_age_scrambling_robustness_report

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_route1_analysis_dataset \
              tests.test_attach_context_entropy_to_route1_dataset

.venv/bin/python -m py_compile src/build_age_scrambling_robustness_report.py
```

  passed with 3 focused robustness tests, 14 adjacent Route 1/context-entropy
  tests, and a successful syntax compile.

- Reworked the rendered report after review because the first version was too
  table-heavy to be useful. The revised document is organized as M1-M6 model
  cards. Each card contains the question, formula, plain-language robustness
  interpretation, a regression-line plot, and one compact result table. The new
  line plots are:

```text
figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png
figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png
figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png
figs/age_scrambling_robustness/m4_clear_robustness_regression_lines.png
figs/age_scrambling_robustness/m5_clear_robustness_regression_lines.png
figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png
```

- The regression-line plots use the saved unit frame and saved slope
  summaries; report-only regeneration does not refit models. The red line is
  the observed age effect, the blue ribbon is the balanced-bootstrap slope
  interval, and the purple/orange/green ribbons are age-scrambled null
  intervals.

## 2026-06-15 - Response-Space Entropy Pilot Grid Framework

- Added a peer-review-oriented pilot framework for sampled full-response
  context entropy:

```text
src/build_response_entropy_pilot_grid.py
configs/response_entropy_pilot_grid.json
tests/test_build_response_entropy_pilot_grid.py
docs/response_entropy_pilot_grid_design.md
docs/response_entropy_pilot_grid_design.html
```

- The manifest stage streams the split scored tree and does not use the 11M-row
  Route 1 long table. Current source:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023
```

- Real manifest command run:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_pilot_grid.py \
  --stage manifest \
  --sample-per-age-bin-context-k 20 \
  --temperatures 0.3,0.5,0.7,1.0,1.3,1.6 \
  --samples-per-context 100 \
  --max-new-tokens 24 \
  --top-p 0.95 \
  --top-k 0
```

- Resulting pilot design:

```text
selected stratum rows: 480
deduplicated generation contexts: 480
temperatures: 6
samples per context per temperature: 100
planned generated responses: 288,000
```

- Strata are balanced as:

```text
8 age bins x 3 context windows x 20 contexts = 480 selected context strata
```

- Saved outputs:

```text
results/response_entropy_pilot_grid/pilot_eligible_context_strata.csv.gz
results/response_entropy_pilot_grid/pilot_selected_context_strata.csv
results/response_entropy_pilot_grid/pilot_generation_manifest.csv
results/response_entropy_pilot_grid/pilot_manifest_audit.csv
results/response_entropy_pilot_grid/pilot_source_file_audit.csv
results/response_entropy_pilot_grid/pilot_method_spec.json
docs/response_entropy_pilot_grid_design.html
```

- GPU generation command is embedded in
  `docs/response_entropy_pilot_grid_design.html`. The command uses base
  Mistral, temperatures `{0.3,0.5,0.7,1.0,1.3,1.6}`,
  `samples_per_context=100`, `max_new_tokens=24`, `top_p=0.95`, and `top_k=0`.

- Updated `src/sample_context_responses.py` so samples include:

```text
raw_generated_text
sampled_response_text
generated_token_count
hit_max_new_tokens
stopped_by_speaker_boundary
speaker_boundary_marker
empty_response
top_p
top_k
seed_used
```

- The diagnostics stage, to run after GPU generation, will write:

```text
results/response_entropy_pilot_grid/pilot_context_temperature_features.csv
results/response_entropy_pilot_grid/pilot_quality_by_temperature.csv
results/response_entropy_pilot_grid/pilot_split_half_reliability.csv
results/response_entropy_pilot_grid/pilot_downsample_stability.csv
results/response_entropy_pilot_grid/pilot_temperature_rank_correlations.csv
docs/response_entropy_pilot_grid_diagnostics.html
```

- Diagnostics include output-quality rates by temperature, split-half
  reliability, downsample stability for M=25/50/75/100, and temperature
  rank-correlation matrices.

- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_response_entropy_pilot_grid \
              tests.test_response_level_context_entropy

.venv/bin/python -m py_compile \
  src/build_response_entropy_pilot_grid.py \
  src/sample_context_responses.py \
  src/summarize_response_entropy_samples.py
```

  passed with 9 focused tests. The only console warning came from Seaborn's
  internal pending deprecation in the toy plotting test.

## 2026-06-15 Pawar and Cychosz 2025 Paper Summary

- Read local PDF:

```text
papers/Frequency and informativity.pdf
```

- Added future-agent summary:

```text
docs/paper_summary_pawar_cychosz_2025_frequency_informativity.md
```

- Key correction recorded: the paper did not sample 100 utterances per age bin.
  It sampled 100 bootstrap samples per age bin, each containing 81,000 phones,
  preserving complete utterance lines so that utterances were not split.
- The summary highlights two methods we can borrow:
  - stability-based sample-size choice, analogous to selecting the number of
    LLM response samples per context/temperature;
  - scrambling controls, including group-level age-bin shuffling and
    sample-level age-label shuffling, plus proposed context-entropy shuffles for
    our response-space entropy predictor.

## 2026-06-15 Response-Space Entropy DeepThink Handoff

- Added `docs/deepthink_response_entropy_temperature_handoff.md`.
- Purpose: give ChatGPT DeepThink a self-contained methods packet for the new
  supervisor-requested response-space context entropy feature.
- The document records the distinction between:
  - current Mistral next-token context entropy:

```text
H(next token | caregiver context)
```

  - proposed sampled full-response entropy:

```text
H(sampled child-like response | caregiver context, model, prompt, temperature)
```

- It summarizes the 2026-06-04 transcript evidence that the supervisors wanted
  repeated sampling from a language model, not real-child lookup, and that
  temperature is a core measurement parameter.
- Current recommendation recorded in the handoff:
  - primary model: `mistralai/Mistral-7B-v0.3`;
  - robustness model: `mistralai/Mistral-7B-Instruct-v0.3`;
  - pilot temperatures: `{0.3, 0.5, 0.7, 1.0, 1.3, 1.6}`;
  - likely main temperatures after pilot: `{0.7, 1.0, 1.3}`;
  - samples: 100 responses per context per temperature;
  - decoding: `top_p=0.95`, hard `max_new_tokens` cap, stop at EOS or speaker
    boundary.

## 2026-06-09 - Context Fixed-Effort Atlas

- Added `src/build_context_fixed_effort_atlas_report.py` to fill the missing
  fixed-effort slice views for context-predictor models.
- Scope:
  - all context windows: `k0`, `k1`, `k2`, `k3`;
  - all context model families:
    - `CF0`: `sum_bits ~ age + target effort + child identity`;
    - `CF1`: add context entropy;
    - `CF2`: add matched context-window size;
    - `CF3`: add both context entropy and matched context-window size;
  - all target effort units: words, morphemes, CMU/pkg syllables, pkg
    syllables, and phonemes.
- Fixed-slice logic:
  - words and morphemes use exact requested panels `1-4`, `5-8`, `9-12`;
  - syllables and phonemes use the 12 most frequent observed exact values,
    split into three ordered representative groups, matching the earlier
    fixed-effort atlas logic.
- Context-size models use the matched context-size unit for readability:
  target words use context words, target phonemes use context phonemes, etc.
  The broader context coefficient report still contains the exhaustive
  cross-unit context-size permutations.
- Real run:

```bash
/usr/bin/time -v env MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python src/build_context_fixed_effort_atlas_report.py \
  --stage analysis \
  --context-ks k0 k1 k2 k3
```

completed in 3:57.68 wall time with maximum resident set size 1,476,432 KB.
Audit:

```text
model_rows: 80
fitted_model_rows: 65
prediction_rows: 54,600
figure_rows: 65
```

- The 15 skipped rows are expected: `k0` has no context entropy or context-size
  predictors, so only `CF0` fits for `k0`.
- Report rendered:

```text
docs/utterance_information_context_fixed_effort_atlas.html
```

- Saved outputs:

```text
results/context_fixed_effort_atlas/context_fixed_effort_audit.csv
results/context_fixed_effort_atlas/context_fixed_effort_model_summary.csv
results/context_fixed_effort_atlas/context_fixed_effort_bin_definitions.csv
results/context_fixed_effort_atlas/context_fixed_effort_predictions.csv.gz
results/context_fixed_effort_atlas/context_fixed_effort_slice_slopes.csv
results/context_fixed_effort_atlas/context_fixed_effort_figure_manifest.csv
figs/context_fixed_effort_atlas/
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_context_fixed_effort_atlas_report \
              tests.test_build_context_predictor_permutation_reports
```

passed with 5 tests.

## 2026-06-09 - Exhaustive M1-M6 Context Fixed-Effort Atlas

- Added `src/build_context_m1_m6_fixed_effort_atlas_report.py`.
- This is the long internal report that combines:
  - `k0`, `k1`, `k2`, `k3`;
  - the M1-M6 model ladder;
  - entropy-only, matched context-size-only, and entropy+size variants for
    M4-M6;
  - fixed-effort slice panels for every effort unit.
- Model inventory:
  - `M1`: `sum_bits ~ age_c + target_effort_c`;
  - `M2`: `sum_bits ~ age_c + target_effort_c + C(child_id)`;
  - `M3`: `sum_bits ~ age_c * target_effort_c + C(child_id)`;
  - `M4E`: `sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)`;
  - `M4S`: `sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id)`;
  - `M4ES`: `sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id)`;
  - `M5E`: `sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id)`;
  - `M5S`: `sum_bits ~ age_c * context_size_c + target_effort_c + C(child_id)`;
  - `M5ES`: `sum_bits ~ age_c * context_entropy_c + age_c * context_size_c + target_effort_c + C(child_id)`;
  - `M6E`: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id)`;
  - `M6S`: `sum_bits ~ age_c * target_effort_c + age_c * context_size_c + target_effort_c * context_size_c + C(child_id)`;
  - `M6ES`: `sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + age_c * context_size_c + target_effort_c * context_size_c + context_entropy_c * context_size_c + C(child_id)`.
- Estimator for all fitted rows:
  - linear OLS via `statsmodels.formula.api.ols`;
  - child-cluster robust standard errors with `cov_type='cluster'`,
    cluster unit `child_id`.
- Fixed-slice logic:
  - words and morphemes use exact panels `1-4`, `5-8`, `9-12`;
  - syllables and phonemes use the top 12 observed exact values split into
    three ordered representative panels.
- Real run:

```bash
/usr/bin/time -v env MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python src/build_context_m1_m6_fixed_effort_atlas_report.py \
  --stage analysis \
  --context-ks k0 k1 k2 k3
```

completed in 11:23.89 wall time with maximum resident set size 1,690,664 KB.
Audit:

```text
model_rows: 240
fitted_model_rows: 195
prediction_rows: 140,400
figure_rows: 195
```

- The 45 skipped rows are expected: `k0` has no context entropy or context
  size, so M4-M6 context variants cannot fit for `k0`.
- Report rendered:

```text
docs/utterance_information_context_m1_m6_fixed_effort_atlas.html
```

- Saved outputs:

```text
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_audit.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_model_summary.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_bin_definitions.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_predictions.csv.gz
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_slice_slopes.csv
results/context_m1_m6_fixed_effort_atlas/context_m1_m6_figure_manifest.csv
figs/context_m1_m6_fixed_effort_atlas/
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_context_m1_m6_fixed_effort_atlas_report \
              tests.test_build_context_fixed_effort_atlas_report \
              tests.test_build_context_predictor_permutation_reports
```

passed with 7 tests.

- Real `k1` smoke test after the memory fix:

```bash
/usr/bin/time -v env MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python src/build_context_predictor_permutation_reports.py \
  --stage analysis \
  --context-ks k1 \
  --context-count-checkpoint results/context_predictor_permutations/unique_context_measurements.checkpoint.csv \
  --output-dir results/context_predictor_permutations_smoke_k1 \
  --fig-dir figs/context_predictor_permutations_smoke_k1
```

completed successfully in 3:36.85 wall time with maximum resident set size
2,561,600 KB. Audit: 446,985 rows, 175,142 unique `k1` context strings, 60/60
model rows fit, 6 figures written.

- The full context-predictor reports still need to be regenerated after this
  memory fix.
- Full `k0`-`k3` analysis after the memory fix:

```bash
/usr/bin/time -v env MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python src/build_context_predictor_permutation_reports.py \
  --stage analysis \
  --context-ks k0 k1 k2 k3 \
  --context-count-checkpoint results/context_predictor_permutations/unique_context_measurements.checkpoint.csv \
  --output-dir results/context_predictor_permutations \
  --fig-dir figs/context_predictor_permutations
```

completed successfully in 12:35.19 wall time with maximum resident set size
2,522,520 KB. Audit:

```text
rows: 1,787,940
unique_context_texts_by_k_sum: 701,880
model_rows: 240
fitted_model_rows: 185
figure_rows: 27
```

- Skipped model rows:
  - 55 skipped rows are expected and limited to `k0`, because `k0` has no
    context text, context entropy, or context size. Its baseline rows still fit.
- Reports rendered:

```text
docs/utterance_information_context_predictors_k0.html
docs/utterance_information_context_predictors_k1.html
docs/utterance_information_context_predictors_k2.html
docs/utterance_information_context_predictors_k3.html
docs/utterance_information_context_predictors_k_comparison.html
```

- Verification after report rendering:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  -m unittest tests.test_build_context_predictor_permutation_reports
```

passed with 3 tests.
