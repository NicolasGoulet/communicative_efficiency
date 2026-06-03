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

- TODO: Restart Route 1 analyses from zero in this repo on 2026-06-02, using `docs/route1_from_zero_handoff_2026-06-01.md` as the project compass. Start with audited real-child Mistral scores, recomputed cleaned word counts, descriptive plots, and the simplest defensible age/length/child model before adding contexts, baselines, or LSTM comparisons.
- TODO: Build the supervisor-facing utterance-information report in `docs/predicting_utterance_level_information_report.md`, focused only on utterance-level informational content and its controls.
- TODO: Keep `compute_surprisal_mila` as the scoring/HPC/audit repo. Treat older Route 1 reports there as archive/scaffold, not as the evidential baseline for the restarted analyses.
- TODO: Hand off the PBM additive same-length LSTM generated utterances to `compute_surprisal_mila` for scoring with the same logic used for random/unigram/bigram/trigram baselines. Keep `lstm_additive_k3`, `lstm_additive_k4`, and `lstm_additive_k5` separate as distinct generated-baseline conditions.


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
- 2026-05-28 - Updated `AGENTS.md` and added `docs/lstm_pc_handoff.md` so a new agent on the PC can pick up the LSTM generation work from Markdown. The handoff records the current bundle, rsync path, model description, PC commands, expected artifacts, and what to document after running.
- 2026-05-28 - Added `src/run_lstm_additive_age_context_pipeline.py` and `tests/test_lstm_additive_age_context_pipeline.py` for PBM-only additive age-bin LSTM generation across caretaker context windows. The script writes per-model batch logs, manifests, generation diagnostics, qualitative samples, and PNG/PDF plots.
- 2026-05-28 - Ran the real PBM additive same-length LSTM generation on the local RTX 4060 Ti GPU: 24 models = k3/k4/k5 times 8 additive age bins (`006-023`, then 6-month bins through `060-065`), 3 epochs each. Output: `results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length/`. Verified 21 generated files, 519,803 child rows checked, 446,508 generated rows per k column, 0 same-length mismatches, 21 scoring-with-LSTM files, and 446,985 scoring rows.
- 2026-05-29 - Added a tested PBM `006-023` generated-baseline patch workflow to `compute_surprisal_mila`, including dry-run/apply scripts for both full cleaned-data inputs and scored-result outputs. Built `results/scoring_bundles/pbm_006_023_scoring_patch_2026-05-29.tar.gz`; verified 17 child files, 62,816 rows, and 272 generated-baseline scoring tasks.
- 2026-06-01 - Added `docs/route1_from_zero_handoff_2026-06-01.md`, summarizing the scoring repo state for the Route 1 reset: audited main Mistral tree, audited LSTM additive tree, PBM patch caveat, pending entropy/KL/word-level features, and the recommended June 2 from-zero modeling sequence.
- 2026-06-02 - Added publication-oriented utterance measurement validation in `src/validate_utterance_measurement_strategies.py`, with focused tests and `docs/utterance_measurement_validation.md`. Generated a human-reviewable 50-row stratified workbook at `results/count_validation/publication_measurement_review_50.xlsx`, plus compact review CSV, token-level CSV, full audit CSV, and Markdown. The review set has short/medium/long/very-long rows, 0 duplicate cleaned utterances, 0 blank recommended syllable counts, and 0 blank recommended phoneme counts. After manual inspection caught G2P syllable undercounting for `firetruck`, changed recommended syllables to CMUdict for known words plus `syllables` package for OOV words, while keeping G2P for phonemes. Added reviewer-facing package write-up at `docs/utterance_measurement_package_writeup.md`. Verified focused tests and full suite: 153 tests passing.
- 2026-06-02 - Rewrote the LSTM baseline orchestration to support the fair additive age-bin design by default: one cumulative LSTM/vocabulary per target age bin, generation only for rows in that target bin, and `lstm_age_bin` provenance in generated/scoring outputs. Updated configs, docs, PC handoff, and AGENTS standards. Real dry-run over the strict naturalistic bundle found 79 units, 1,140,218 examples, and 8 bins with cumulative train/target counts recorded in `docs/notes.md`. No GPU training was run. Verified focused LSTM tests and full suite: 156 tests passing.
- 2026-06-02 - Added PBM-only additive LSTM config `configs/lstm_baseline_16gb_pbm_additive.json` for fair comparison against currently PBM-trained n-gram baselines. Dry-run found 21 units, 446,508 examples, and 8 additive bins; counts are recorded in `docs/notes.md`. No training was run.
- 2026-06-03 - Started the supervisor-facing utterance-information report at `docs/predicting_utterance_level_information_report.md`, using the 2026-06-03 compute-surprisal handoff as the current PBM patched Mistral source-of-truth note.
- 2026-06-03 - Added Route 1 report asset generation and HTML rendering scripts; fixed PBM age-bin coverage by recovering blank Providence/Naima `030000.cha` ages from the filename, so child and caretaker age-bin totals now match all k0 scored rows exactly. Verified full suite: 162 tests passing.
- 2026-06-03 - Reworked the utterance-information report to be supervisor-facing: removed internal "Route 1" framing, removed workflow/source-path sections, removed premature modeling questions, added communicative-efficiency framing and baseline-construction sections for random, n-gram, and LSTM comparisons. Regenerated plots with short formal titles and verified full suite: 163 tests passing.
- 2026-06-03 - Added the Providence/Naima `030000.cha` missing-baseline patch builder and scorer-side local scripts. Built `results/scoring_bundles/naima_030000_missing_baselines_scoring_patch_2026-06-03.tar.gz` with 477 rows, recovered age 36 months, and nonblank random/unigram/bigram/trigram generated utterances from the current additive `036-041` dictionaries. Copied local scorer/merge helpers into `compute_surprisal_mila`; focused tests and script syntax checks passed.
- 2026-06-03 - Updated `compute_surprisal_mila` agent workflow Markdown for the Naima patch: `AGENTS.md`, `README.md`, and `docs/naima_030000_missing_baseline_patch.md` now document exact local scoring, dry-run merge, apply-merge, and post-merge Route 1 rebuild steps.
