# TODO.md

Lower-level working checklist for this repository.

Use this file for concrete tasks. Keep `AGENTS.md` high-level and stable.
When a task is completed, move any useful result or decision into
`docs/notes.md`.

## How To Use This File

- Keep tasks small enough to review in one diff.
- Use checkboxes for work items.
- Put open questions near the task they block.
- Add commands that verify the task.
- Link to files when the task concerns a specific script or output.

## Current Focus

- TODO: Add a new option to the prepare_datasets.py that will output the cleaned utterances but only to csv files in cleaned_utterances. These will contain also the counts of words, morphemes and our various syllable strategies. It willalso contain all the erlvant info like the stuff in preprocesseddata (line_no, age, namne of child, session id, line id utt id etc etc)


## List of next possible focus

These are never to be implemented at the same time, always one at a time described in the previous section :


- TODO : Fix the utterance generation script and regenerate all the utterances
- TODO : Then, score again all the utterances making sure it preserved punctuation and that sentences without any scorable-words are ignored. 
- TODO: The generation of utterances using small LLM : it will be more detailed once it'll be the `Current Focus` but the general goal is that for every dataset from CHILDES we have,
- TODO: Increase in questions over time?
- TODO: Clarify the & markers 
- TODO: Compare with and without these
- TODO: Create a minimalist interface to easily study various utterances surprisals. It should either take a csv file with a clean utterance per row and return it with an added column with the scored surprisal for each cleaned utterance.


## Done Log

Use this for short notes after finishing tasks.

- TODO: YYYY-MM-DD - Finished X; verified with Y.
- 2026-05-19 - Rewrote additive age-binned unigram/bigram/trigram dictionary building in `src/build_age_word_dicts.py`; counts now use `chi.csv` plus `caretakers.csv`, with utterance-initial child bigrams/trigrams conditioned on the most recent prior caretaker utterance.
- 2026-05-19 - Rewrote baseline generation in `src/add_random_and_unigram_utterances.py`; generation now supports random, unigram, bigram, and trigram outputs, and bigram/trigram generation uses the same caretaker-boundary context logic as counting.
- 2026-05-19 - Added trigram baseline pickup to `src/new_create_parallel_data.py`; documented the n-gram rewrite in `docs/ngram-models.md`, `docs/general-overview.md`, `docs/design.md`, and `docs/notes.md`.
- 2026-05-19 - Verified the n-gram rewrite with `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` (48 tests passing); built real 6-month dictionaries at `results/age_ngram_dicts/bin6`; generated sibling baseline files as `chi.ngram_generated.csv` for Brown, Manchester, and Providence.
- 2026-05-19 - Added experimental LSTM generator in `src/generate_lstm_utterances.py`; it uses configurable caretaker context, writes `chi.lstm_generated.csv`, and requires PyTorch for actual training/generation.
- 2026-05-19 - Updated `src/new_create_parallel_data.py` to merge generated sibling columns from n-gram and LSTM outputs and export an `lstm_chi` scoring subset when `lstm_model_utterance` exists.
- 2026-05-19 - Updated the LSTM generator with an encoder-decoder `seq2seq_lstm` architecture as the default; the encoder reads caretaker context and the decoder generates child utterances, while the earlier prefix-style LSTM remains available as `causal_lstm`.
- 2026-05-20 - Added PyTorch to the uv-managed dependencies with `uv add torch`; verified `torch==2.12.0+cu130` imports, with CUDA unavailable on this machine.
- 2026-05-20 - Re-ran the full unit-test suite after the PyTorch install: `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 61 tests.
- 2026-05-20 - Ran a bounded LSTM smoke generation on Brown using `seq2seq_lstm`, 500 training examples, and 10 generated rows per child; wrote smoke outputs under `results/lstm_generation/smoke_seq2seq_brown` and `chi.lstm_smoke_generated.csv` files for Brown children.
- 2026-05-20 - Confirmed the additive n-gram generation already includes random, unigram, bigram, and trigram columns; `random_model_utterance_bin6` is the uniform random baseline sampled from each additive bin vocabulary.
- 2026-05-20 - Added tested LSTM length modes: default `same_as_child` for matched-length controls and `free_until_eos` for model-chosen answer length; documented the comparison logic in `docs/llm-models.md` and `docs/notes.md`.
- 2026-05-20 - Verified all 21 `chi.ngram_generated.csv` files: 446,508 scorable child rows with usable `age_months` had 0 length mismatches for random, unigram, bigram, and trigram baselines; 477 scorable rows without usable age remain blank because they cannot be assigned to an additive age bin.
- 2026-05-20 - Re-ran tests after the LSTM length-mode change: `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests` passed with 68 tests.
- 2026-05-20 - Ran Brown-only LSTM smoke outputs for `same_as_child` and `free_until_eos`; fixed-length smoke had 0/15 mismatches, while free-length smoke hit the configured 8-token cap in all 15 examples, so free-length results need a real training run before interpretation.
- 2026-05-20 - Fixed and regenerated n-gram sibling CSV outputs with explicit `caretaker_context_p2`, `caretaker_context_p1`, and `caretaker_context_last_two` columns so the boundary context used by bigram/trigram generation is visible.
- 2026-05-20 - Added n-gram output regression tests for p2/p1 context columns and CSV row-width alignment; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 70 tests.
- 2026-05-20 - Verified all 21 regenerated `chi.ngram_generated.csv` files parse cleanly: 519,803 rows checked, 0 row-width mismatches, 0 files missing context columns.
- 2026-05-20 - Fixed blank n-gram output metadata by filling empty `source_group` with the dataset name and enforcing sane generated-output metadata; regenerated all 21 sibling CSVs and verified 519,803 rows with 0 semantic column issues.
- 2026-05-20 - Updated future known-corpus preprocessing to fill `source_group` with the dataset name for non-Hall layouts; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 71 tests.
- 2026-05-20 - Removed `utt_id_role` from generated n-gram CSV outputs, enforced a fixed generated-output schema with no blank headers, switched writing to `csv.QUOTE_ALL`, regenerated all 21 sibling CSVs, and verified 519,803 rows with 0 header/order/row-width/speaker/line/file/source-group issues.
- 2026-05-20 - Added tests proving generated n-gram headers are exactly ordered and that `speaker`, `utterance`, and `utterance_clean` remain under the correct columns; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 72 tests.
- 2026-05-20 - Added `src/create_shared_caretaker_contexts.py` to write role-specific context files per child folder: `chi.shared_caretaker_contexts.csv` and `caretakers.shared_caretaker_contexts.csv`.
- 2026-05-20 - Generated shared caretaker-context files for Brown, Manchester, and Providence: 21 child files and 21 caretaker files; verified 519,803 child rows and 688,880 caretaker rows with 0 header/order/row-width/role/line/file/source-group issues.
- 2026-05-20 - Added tests for role-specific context outputs, including exact headers, absence of `utt_id_role`, child/generated-column alignment, caretaker-only outputs without generated columns, and k1/k2/k3 caretaker context logic; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 74 tests.
- 2026-05-20 - Added `src/utterance_count_strategies.py` with TDD-covered word, morpheme, and syllable strategies; generated `results/count_validation/utterance_count_strategy_probe.csv` with 100 real cleaned utterances for manual validation.
- 2026-05-20 - Verified the utterance-count probe output: 100 rows, 23 columns, 0 blank headers, 0 row-width issues; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 82 tests.
- 2026-05-20 - Added `src/create_minimal_surprisal_scoring_csvs.py` to export compact per-child scoring files: `chi.surprisal_scoring.csv` and `caretakers.surprisal_scoring.csv`.
- 2026-05-20 - Generated compact scoring CSVs for Brown, Manchester, and Providence: 21 child files and 21 caretaker files; verified 446,985 child rows and 668,903 caretaker rows with 0 schema/row/target/role/metadata issues.
- 2026-05-20 - Added tests for exact compact scoring schemas, dropping empty targets, and excluding noisy columns like `utt_id_role`; re-ran `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests`, passing 85 tests.
- 2026-05-20 - Extracted and registered MPI-EVA-Manchester; added tested filename-age fallback for blank CHI `@ID` ages; reprocessed 1,079,020 rows and wrote updated age-bin distribution outputs under `figs/utterance_distributions_with_mpi_eva_manchester/`.
- 2026-05-20 - Confirmed named corpora: Wells, Belfast, and Champaign are longitudinal; Cummings is clinical cross-sectional with some longitudinal records; Styles is not CHAT data. Extracted and preprocessed Wells, Belfast, Champaign, and Cummings; wrote expanded plots under `figs/utterance_distributions_longitudinal_named_expansion/`.
- 2026-05-20 - Made the caregiver-child naturalistic/default corpus split explicit, keeping Cummings in a separate clinical/probe group; added and preprocessed EHS as non-clinical parent-child interaction data; regenerated naturalistic-only plots under `figs/utterance_distributions_naturalistic_caregiver_child_only/`.
- 2026-05-20 - Extracted and preprocessed the available stricter naturalistic downloads: Lara, Sachs, Weist, Kuczaj, Post, Demetras1, and Forrester. `Thomas.zip` was not present in `data/zip_files`, so Thomas remains pending.
- 2026-05-20 - Added root-direct CHAT corpus discovery and Lara-specific caregiver handling for `ELS`; updated strict naturalistic defaults to exclude structured-observational Champaign/EHS and clinical Cummings.
- 2026-05-20 - Regenerated strict naturalistic 6-month child- and caretaker-utterance distributions at `figs/utterance_distributions_strict_naturalistic_parent_child/`; the child comparison table/plot are `ALL_DATASETS/previous_vs_new_strict_downloads_age_bin_counts_6m.csv` and `.png`, and the caretaker comparison table/plot use the `caretaker_` prefix.
- 2026-05-20 - Added `docs/preprocessed_datasets.md` documenting every currently preprocessed dataset, corpus grouping, Stage 0 row counts, missing-age counts, downstream generated/context/scoring readiness, and non-preprocessed pending datasets.
- 2026-05-21 - Added all-preprocessed age-bin utterance tables under `results/utterance_age_tables/`, including total child-vs-caretaker counts and per-dataset long/wide formats.
- 2026-05-21 - Added `docs/project_deep_research_handoff.md`, a comprehensive technical and scientific handoff summarizing the current project state for a deep-research agent.
- 2026-05-21 - Created PBM scoring-ready tarballs under `results/scoring_bundles/`: combined child+caretaker scoring CSVs, child-only scoring CSVs, and caretaker-only scoring CSVs.
- 2026-05-25 - Added `src/extract_child_metadata_summary.py` and `tests/test_extract_child_metadata_summary.py`; generated `results/metadata/child_metadata_summary.csv` with one row per prepared child folder, recoverable CHAT demographics, utterance counts, age coverage, and downstream scoring-readiness flags.
- 2026-05-25 - Added `src/create_big_cleaned_dataset.py` and `tests/test_create_big_cleaned_dataset.py`; generated `data/big_cleaned_dataset/default_naturalistic_bin6/` with strict naturalistic Stage 0 files, additive bin-6 n-gram dictionaries, matched-length random/unigram/bigram/trigram baselines, shared caretaker-context files, compact scoring CSVs, `manifest.csv`, and a folder README. Verified 109 tests passing and 0 CSV header/row-width issues.
- 2026-05-25 - Generated strict-naturalistic big-cleaned actual utterance distribution plots and CSVs under `figs/big_cleaned_dataset/default_naturalistic_bin6/`, plus a Providence/Brown/Manchester-only version under `figs/big_cleaned_dataset/providence_brown_manchester_bin6/`, split by child versus caretaker 6-month age bins.
- 2026-05-25 - Added custom threshold early age bins via `src/custom_age_bins.py` and wired them into n-gram dictionary building/generation. Generated `data/big_cleaned_dataset/default_naturalistic_custom_early20k/` using bins `006-019`, `020-023`, then 6-month intervals from `024-029` through `060-065`; wrote all/PBM custom-bin utterance tables and plots under `figs/big_cleaned_dataset/*custom_early20k/`. Verified 121 tests passing and 0 CSV header/row-width issues.
- 2026-05-26 - Generated `results/metadata/strict_naturalistic_custom_early20k_child_metadata_summary.csv`, a 79-row metadata file matching the current custom-bin strict-naturalistic scoring bundle.
- 2026-05-26 - Added `src/prepare_clinical_datasets.py` and `tests/test_prepare_clinical_datasets.py`; prepared 15 clinical/control dataset groups under `data/preprocessed_clinical_data/`, writing 494 child folders and metadata summaries at `results/metadata/clinical_child_metadata_summary.csv` and `results/metadata/clinical_dataset_summary.csv`. Verified clinical CSVs have 0 header/row-width issues.
- 2026-05-26 - Added `src/analyze_clinical_magnitudes.py` and `tests/test_analyze_clinical_magnitudes.py`; generated session-size comparisons, clinical/control 6-month age-bin tables, and figures under `results/clinical_magnitude_analysis/` and `figs/clinical_magnitude_analysis/`.
- 2026-05-26 - Added GPU-ready LSTM baseline orchestration in `src/run_lstm_baseline_pipeline.py` with tests in `tests/test_lstm_baseline_pipeline.py` and documentation in `docs/lstm-baseline-pipeline.md`; laptop dry run found 79 child folders and 1,140,218 usable examples without training a model.
- 2026-05-26 - Added merged-early n-gram binning via `merged_early_006_023`, regenerated `data/big_cleaned_dataset/default_naturalistic_merged_006_023/`, and verified 79 child scoring files, 79 caretaker scoring files, 1,140,218 child scoring rows, 1,470,154 caretaker scoring rows, and 0 CSV header/row-width issues.
- 2026-05-26 - Added `src/create_pbm_early_baseline_rescoring_bundle.py` and tests; generated the PBM-only `006-023` generated-baseline rescoring shards at `results/rescoring_subsets/pbm_006_023_merged_early_baselines/` plus tarball `results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_2026-05-26.tar.gz`. Verified 251,264 scorer rows across random/unigram/bigram/trigram, all floor-age 006-023, with 0 CSV issues.
- 2026-05-27 - Added `MERGE_BACK_GUIDE.md` and `replacement_keys.csv` to the PBM early rescoring bundle; created handoff tarball `results/scoring_bundles/pbm_006_023_merged_early_baselines_rescoring_handoff_2026-05-27.tar.gz` with scorer shards plus explicit replacement keys. Verified 18 CSVs in the bundle with 0 blank-header or row-width issues.
- 2026-05-28 - Updated the LSTM baseline pipeline to default to `default_naturalistic_merged_006_023`, added JSON config loading, editable configured generation variants, 16GB-GPU default/smoke configs, and a supervisor-facing LSTM pipeline document. Verified with `tests.test_lstm_baseline_pipeline`, `tests.test_lstm_generation`, and the full suite: 145 tests passing. No LSTM training or generation was run on the laptop.
