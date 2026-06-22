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

## 2026-06-18 Active Route 1 Candidate-Report Correction

- User clarified that `docs/route1_best_model_robustness_package.md` should not
  be a giant M1-M15 dump and should not be dominated by compact tables or
  aggregate diagnostics.
- Current deliverable is a focused, plot-first candidate report for choosing
  supervisor-report figures.
- This is a communicative-efficiency analysis, not a raw MLU/length-growth
  analysis. Do not frame the result as predicting how large total `sum_bits`
  becomes with age. Raw total bits can increase just because older children say
  longer utterances.
- Main Route 1 estimand is conditional utterance information: how
  utterance-level `sum_bits` changes with age at fixed child effort and after
  controls such as child identity and parent-context effort.
- The design context must be explicit: continuous bits are measured for many
  utterances from the same children, across multiple sessions/ages, with
  repeated measurements inside children and sessions. Estimator choices must be
  justified against this repeated-measures structure.
- The report should include promising existing M1-M15 candidates only when they
  answer the actual question. Current promising existing candidates are M2,
  M3, M4a, M4c, M5, M6, M7, M11, and M15, not the full M1-M15 inventory.
- The specific simple parent-effort candidate family to test/plot is:

```text
sum_bits ~ age + child effort + child identity
sum_bits ~ age + child effort + parent context effort + child identity
sum_bits ~ age + child effort + age:child effort + parent context effort + child identity
sum_bits ~ age + child effort + parent context effort + age:parent context effort + child identity
sum_bits ~ age + child effort + parent context effort + child effort:parent context effort + child identity
sum_bits ~ age + child effort + parent context effort
           + age:child effort
           + age:parent context effort
           + child effort:parent context effort
           + child identity
```

- When writing interactions, always include and display lower-order predictors.
  For example, write `age_c + effort_c + age_c:effort_c`; do not rely on
  shorthand alone.
- Keep conditional total-bits and bits-per-token/rate outcomes separate. A
  secondary `mean_bits_per_token` or `sum_bits / child effort` model can be
  added, but it answers a different question from total bits at fixed effort.
- Do not promote raw observed-vs-fitted `sum_bits` plots as evidence for
  communicative efficiency. They mostly show the mechanical length/total-bits
  relationship and can confuse the analysis with MLU.
- Required visual emphasis: regression/fixed-effort age lines for real
  children, generated baselines, caretaker contrasts, and the three heldout
  children's actual-vs-predicted lines. Tables should be brief support only.
- Estimator rationale to show:
  OLS with child fixed effects and child-clustered SE is the main Atlas
  baseline; GEE Gaussian handles population-average repeated continuous
  outcomes; GEE Gamma/log checks positive skew; GLM Gaussian/Gamma-log are
  distribution/link sensitivity checks; MixedLM random intercepts allow child
  baseline differences; MixedLM random age slopes allow child-specific
  developmental trajectories; month/session aggregation is robustness against
  pseudo-replication, not the main result.

## 2026-06-18 Route 1 Formula-Permutation Estimator Report

- Added `src/build_route1_formula_permutation_estimator_report.py`.
- Generated internal model-selection report:
  `docs/route1_formula_permutation_estimator_report.md`,
  `docs/route1_formula_permutation_estimator_report.html`, and
  `docs/route1_formula_permutation_estimator_report.embedded.html`.
- Report output artifacts:
  `results/route1_formula_permutation_estimator_report/` and
  `figs/route1_formula_permutation_estimator_report/`.
- Formula grid: 36 formulas. Every formula keeps age, child effort, and child
  identity handling. The grid permutes context entropy, parent-context effort,
  question/form type, `age:child effort`, `age:context entropy`, and
  `age:parent context effort`, with lower-order terms always written and fit.
- Estimator grid: 7 estimator families for every formula:
  OLS + child fixed effects + clustered SE, GEE Gaussian + `C(child_id)`,
  GEE Gamma/log + `C(child_id)`, GLM Gaussian, GLM Gamma/log, MixedLM random
  child intercept, and MixedLM random child age slope.
- Verification: `formula_estimator_summary.csv` has 252 rows, 36 unique
  formulas, 7 unique estimators, and all 252 fits have status `fit`.
  `formula_report_figure_manifest.csv` has 82 available figures. The Markdown
  report has 36 formula sections, 252 estimator subsections, and 90 image
  references with 0 missing.
- Command:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_formula_permutation_estimator_report.py
.venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package
```

- Important interpretation note: this new report is an aggregate
  child-session/effort-band repeated-measures screen using `mean_sum_bits`.
  It is for choosing formulas and estimator families. The row-level Atlas
  remains the source to promote for final supervisor-facing fixed-effort
  `sum_bits` claims.
- Correction after interpretability audit: the report now shows exact row-level
  fixed-effort Atlas plots before aggregate estimator screens for formulas that
  map to existing Atlas models. It also adds a global same-effort plot that
  averages the row-level fixed-word-count prediction lines across fixed sizes.
  For F02/M3, all 12 fixed-word-count slopes are downward, with mean
  -0.136 bits/month and range -0.157 to -0.115 bits/month.
- Verification after correction: regenerated Markdown/HTML/embedded HTML,
  confirmed 96 Markdown image references with 0 missing, confirmed the F02
  global fixed-effort plot exists, and reran
  `MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package`
  with 9 tests passing.

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

## 2026-06-15 - Supervisor-facing M1-M3 smoking-gun section

- Minimally updated `docs/predicting_utterance_level_information_report.md`
  without changing the earlier dataset, effort, information, or baseline
  sections.
- Filled the previous explanatory-model TODOs with Models 1-3:
  - M1: `sum_bits ~ age_c + effort_c`
  - M2: `sum_bits ~ age_c + effort_c + C(child_id)`
  - M3: `sum_bits ~ age_c * effort_c + C(child_id)`
- Documented that these are `statsmodels` OLS fits with child-clustered robust
  standard errors; M2/M3 also include child fixed effects through
  `C(child_id)`.
- Added compact coefficient table, fixed-effort slice summary, and balanced /
  scrambled age-check summary using the already-fit artifacts:
  `results/m1_m6_dual_effort_quick_share/dual_model_summary.csv`,
  `results/m1_m6_fixed_effort_atlas/atlas_fixed_slice_slopes.csv`, and
  `results/age_scrambling_robustness/age_scrambling_robustness_summary.csv`.
- Regenerated:
  - `docs/predicting_utterance_level_information_report.html`
  - `docs/predicting_utterance_level_information_report.embedded.html`
- No models were refit for this supervisor-facing edit. The attempted headless
  Brave PDF export did not update the PDF, so the current PDF remains older
  than the Markdown/HTML.

## 2026-06-15 - Supervisor-facing slice revision after review

- Updated the same report section after review of the HTML:
  - removed the dual-effort low/mid/high prediction figures from the
    supervisor-facing document because those categorical effort panels are a
    coarser alternate encoding and were confusing in this setting;
  - removed the compact coefficient table from the supervisor draft;
  - foregrounded exact fixed-effort slice plots for Model 1 and Model 2 instead.
- Added a short explanation that phoneme slices are distribution-supported:
  the supervisor-facing phoneme panel uses the twelve most frequent exact
  phoneme counts, 2-13; the fuller atlas groups these as low 2-5, middle 6-9,
  and high 10-13 representative sizes.
- Regenerated:
  - `docs/predicting_utterance_level_information_report.html`
  - `docs/predicting_utterance_level_information_report.embedded.html`
- No model fitting was rerun; this was a report/rendering change using existing
  fixed-effort artifacts.

## 2026-06-15 - Supervisor-facing methods clarification

- Updated the explanatory-model section to state explicitly that the displayed
  M1-M3 models are linear regression / OLS models in `statsmodels`, with
  child-clustered robust standard errors.
- Clarified that M2/M3 use child fixed effects rather than random intercepts in
  the supervisor-facing first pass; internal sensitivity reports explored GEE,
  GLM, and mixed-effect variants, including random-intercept/random-slope
  attempts.
- Added the methodological caveat that predictors were not selected by
  stepwise selection or variable-importance ranking; the ladder is
  theory-driven, and effort units are separated because they are highly
  correlated.
- Restored one fixed-effort plot directly inside each Model 1, Model 2, and
  Model 3 section. Regenerated local and embedded HTML. No models were refit.

## 2026-06-15 - Supervisor-facing M1-M3 plot and model-family cleanup

- Re-read the Advanced Data Analytics course notes on correlated data,
  regularization/model selection, and longitudinal modeling before editing the
  supervisor-facing report again.
- Tightened the statistical-methods paragraph:
  - displayed M1-M3 results are OLS / linear regression because `sum_bits` is a
    continuous outcome in bits and the coefficients are directly interpretable;
  - child-clustered robust standard errors account for repeated utterances from
    the same child in the uncertainty estimates;
  - M2/M3 use child fixed effects so each child gets their own baseline
    intercept;
  - internal sensitivity work also includes GEE grouped by child, GLM/Gamma
    variants, and mixed-effect random-intercept/random-slope models.
- Clarified that child identity is not the substantive "finding"; it is an
  adjustment for uneven longitudinal coverage, because different children enter
  and leave the corpus at different ages and contribute different numbers of
  sessions.
- Added all requested M1-M3 supervisor-facing plots:
  - fixed-effort slice plots for M1, M2, and M3;
  - balanced/scrambled interval plots for M1, M2, and M3;
  - the robustness heatmap;
  - balanced/scrambled regression-line diagnostics for M1, M2, and M3.
- Regenerated:
  - `docs/predicting_utterance_level_information_report.html`
  - `docs/predicting_utterance_level_information_report.embedded.html`
- Embedded HTML now reports 13 embedded images. The PDF was not regenerated and
  remains older than the Markdown/HTML.

## 2026-06-16 - Response-space entropy pilot completed and audited

- Interpreted the PC progress check:
  - no rows under `ps -p 9317,10913` meant the generator PID and watchdog PID
    were no longer running;
  - `nvidia-smi` showing `0` GPU utilization and about 257 MiB memory meant the
    GPU was idle;
  - the sample gzip timestamp showed the last write time, not completion by
    itself.
- The first PC run had stopped early with:
  - 272,600 valid sample rows out of 288,000 planned;
  - 2,726 complete context-temperature pairs out of 2,880;
  - the missing 154 context-temperature pairs were the tail of temperature
    1.6;
  - 16 malformed CSV records in the raw partial file, caused by multiline /
    punctuation-rich generated text interacting poorly with the earlier append
    format.
- Preserved the raw interrupted file as:

```text
results/response_entropy_pilot_grid/pilot_response_samples.partial_2026-06-15.raw.csv.gz
```

- Wrote a clean parsed copy from the valid rows, then resumed only the missing
  temperature-1.6 pairs into:

```text
results/response_entropy_pilot_grid/pilot_response_samples_clean.csv.gz
```

- Hardened `src/sample_context_responses.py`:
  - append writes now use `csv.QUOTE_ALL` and `lineterminator="\n"`;
  - resume scanning reads key columns as strings, skips malformed lines, drops
    nonnumeric temperatures/sample indices, and tracks unique sample indices
    per context-temperature pair.
- Added focused coverage in `tests/test_response_level_context_entropy.py` for
  quoted multiline sampled responses and malformed resume rows.
- Added `scripts/run_response_entropy_pilot_resume_watchdog.sh` as a small
  PC-side watchdog/resume helper. It waits for the original generator PID and
  then reruns the resumable temperature-1.6 command if needed.
- Verification commands:

```bash
.venv/bin/python -m unittest \
  tests.test_response_level_context_entropy \
  tests.test_build_response_entropy_pilot_grid
```

passed locally with 13 tests.

Remote diagnostics command:

```bash
ssh alkan@192.168.7.217 \
  "cd /home/alkan/Portelance/communicative_efficiency && \
   MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
   src/build_response_entropy_pilot_grid.py \
   --stage diagnostics \
   --samples results/response_entropy_pilot_grid/pilot_response_samples_clean.csv.gz \
   --generation-manifest results/response_entropy_pilot_grid/pilot_generation_manifest.csv \
   --temperatures 0.3,0.5,0.7,1.0,1.3,1.6 \
   --samples-per-context 100 \
   --output-dir results/response_entropy_pilot_grid \
   --fig-dir figs/response_entropy_pilot_grid \
   --diagnostic-md docs/response_entropy_pilot_grid_diagnostics.md \
   --diagnostic-html docs/response_entropy_pilot_grid_diagnostics.html"
```

completed successfully and wrote:

```text
results/response_entropy_pilot_grid/pilot_context_temperature_features.csv
results/response_entropy_pilot_grid/pilot_completion_audit.csv
results/response_entropy_pilot_grid/pilot_quality_by_temperature.csv
results/response_entropy_pilot_grid/pilot_split_half_reliability.csv
results/response_entropy_pilot_grid/pilot_downsample_stability.csv
results/response_entropy_pilot_grid/pilot_temperature_rank_correlations.csv
results/response_entropy_pilot_grid/pilot_diagnostic_figure_manifest.csv
docs/response_entropy_pilot_grid_diagnostics.md
docs/response_entropy_pilot_grid_diagnostics.html
```

- Strict completion audit:

```text
sample_rows_observed: 288000
unique_contexts_observed: 480
temperatures_observed: 0.3,0.5,0.7,1.0,1.3,1.6
samples_per_context: 100
expected_rows: 288000
complete_context_temperature_pairs: 2880
expected_context_temperature_pairs: 2880
missing_or_incomplete_pairs: 0
is_complete: True
```

- Temperature quality summary:
  - entropy rises from 3.82 bits at T=0.3 to about 7.30 bits at T=1.3/1.6;
  - unique sampled responses rise from about 32/100 at T=0.3 to about 98.5/100
    at T=1.3/1.6;
  - empty-response rate is low and stable, about 0.7-0.8% across temperatures;
  - hit-max-token rate is essentially 100% for all temperatures, so the current
    24-token cap is too short for interpreting full response endings;
  - boundary-stop rate falls from 83.8% at T=0.3 to 2.2% at T=1.6.
- Split-half reliability:
  - T=0.3 and T=0.5 are reliable across halves (`spearman_r` about 0.93 and
    0.86);
  - T=0.7 is moderate (`spearman_r` about 0.69);
  - T=1.0 is weak (`spearman_r` about 0.38);
  - T=1.3 and T=1.6 are unstable/negative because entropy is nearly saturated
    near the 100-sample cap.
- Temperature rank correlations show two regimes:
  - lower temperatures correlate with each other (`0.3` vs `0.5` about 0.88;
    `0.5` vs `0.7` about 0.85);
  - high temperatures correlate with each other (`1.3` vs `1.6` about 0.91)
    but not with low-temperature rankings.
- Immediate interpretation: the pilot generation itself is complete and usable
  for diagnostics. For production, T=1.3/1.6 look too close to saturated
  decoding noise; T=0.3 is stable but likely too conservative; T=0.5 and/or
  T=0.7 are the strongest primary candidates, with T=1.0 as a possible
  sensitivity point after manual response-quality review. The 24-token cap
  should be reconsidered before production because nearly every sample hit it.
- Synced completed PC outputs back to the laptop with `rsync` for
  `results/response_entropy_pilot_grid/`, `figs/response_entropy_pilot_grid/`,
  and the diagnostics Markdown/HTML.

## 2026-06-16 - Supervisor-facing report rebuilt around Model 2

- Re-read the current supervisor-facing Markdown before editing:

```text
docs/predicting_utterance_level_information_report.md
```

- The checked report was not in the state described by the earlier June 15
  notes: the Markdown/HTML still had placeholder explanatory-model sections
  (`TODO ADD RESULTS AND PLOTS` under First/Second/Third Model).
- Rebuilt the report so Model 2 is the first result after the introduction:

```text
total utterance information ~ age + production effort + child identity
```

- Kept the report supervisor-facing by avoiding internal workflow/path framing
  in the body and by preserving the existing dataset, effort, information, and
  baseline sections.
- Main M2 evidence promoted from saved artifacts:
  - sample: 446,985 real child utterances, 21 children, k3 context;
  - source table:
    `results/m1_m6_dual_effort_quick_share/dual_model_summary.csv`;
  - all five continuous-effort M2 age coefficients are negative:
    words -0.122 bits/month, morphemes -0.136, CMU/pkg syllables -0.063,
    package syllables -0.048, phonemes -0.065;
  - effort coefficients remain strongly positive for every effort measure.
- Added the five readable M2 fixed-effort plots from `figs/m2_simple_plots/`:

```text
m2_words_fixed_effort_and_global_trend.png
m2_morphemes_fixed_effort_and_global_trend.png
m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png
m2_syllables_pkg_fixed_effort_and_global_trend.png
m2_phonemes_fixed_effort_and_global_trend.png
```

- Added matching k3 robustness results from:

```text
results/age_scrambling_robustness/age_scrambling_robustness_summary.csv
figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png
```

- Important robustness distinction documented in the report: the robustness
  checks use an aggregated child-session-context frame, so their slopes are
  not numerically identical to the utterance-level M2 coefficients. The
  matching k3 aggregated M2 slopes are still negative for all five effort
  controls and fall outside the scrambled null intervals.
- Rendered:

```bash
.venv/bin/python src/render_markdown_report.py \
  docs/predicting_utterance_level_information_report.md \
  docs/predicting_utterance_level_information_report.html

.venv/bin/python src/embed_html_assets.py \
  docs/predicting_utterance_level_information_report.html \
  docs/predicting_utterance_level_information_report.embedded.html
```

- Embedded HTML reports 9 embedded images: the three coverage figures, five M2
  fixed-effort figures, and the M2 robustness figure.
- Verification:

```bash
rg -n "TODO|First Model|Second Model|Third Model|Route 1|breif|expending|bellow|Professor Xu :| t is " \
  docs/predicting_utterance_level_information_report.md \
  docs/predicting_utterance_level_information_report.html
```

returned no matches. The PDF was not regenerated.

## 2026-06-16 - Response-space entropy stopping/max-token probes

- Checked the completed Route 2 pilot first. The clean pilot output remains:

```text
results/response_entropy_pilot_grid/pilot_response_samples_clean.csv.gz
```

with 288,000 complete samples: 480 contexts x 6 temperatures x 100 samples.
The diagnostic conclusion from the full pilot was that T=0.5 and T=0.7 are
the strongest primary temperature candidates; T=0.3 is stable but
conservative, T=1.0 is less reliable, and T=1.3/T=1.6 look saturated/noisy.

- Built a bounded stopping probe workflow:

```text
src/build_response_entropy_stopping_probe.py
scripts/run_response_entropy_stopping_probe_pc.sh
tests/test_build_response_entropy_stopping_probe.py
```

The probe selects 40 contexts from the pilot manifest, balanced across context
length buckets, and summarizes how generation behaves under different
`max_new_tokens` caps.

- First probe caveat: the initial stopping-probe output is not scientifically
usable. It revealed a sampler bug caused by left-padded batches: generated
tokens were sliced using each row's attention length instead of the padded
prompt width, so some decoded "generated" text included the tail of the
caregiver prompt. Fixed this in `src/sample_context_responses.py` by slicing
from the batch prompt width:

```text
generated_token_ids(output_ids, prompt_token_width=encoded["input_ids"].shape[1])
```

and added a regression test in `tests/test_response_level_context_entropy.py`.

- Corrected max-token probe (`results/response_entropy_stopping_probe_v2/`,
  `docs/response_entropy_stopping_probe_v2.html`) tested 4,800 samples:
  40 contexts x temperatures 0.5, 0.7, 1.0 x caps 12, 24, 48, 96 x
  10 samples. With only explicit speaker-label stopping, every setting had
  `hit_max_rate=1.0`; base Mistral did not naturally emit EOS within these
  caps. Speaker-label boundary rates plateaued by 48-96 tokens:

```text
T=0.5 boundary_seen_rate: 0.345 at 12, 0.6425 at 24, 0.67 at 48, 0.675 at 96
T=0.7 boundary_seen_rate: 0.285 at 12, 0.6050 at 24, 0.63 at 48, 0.640 at 96
T=1.0 boundary_seen_rate: 0.205 at 12, 0.3950 at 24, 0.4575 at 48, 0.470 at 96
```

- Additional raw-text inspection on v2 showed that the model usually put a
  generic newline before a speaker label or prose continuation. For cap 48,
  generic-newline rates were about 0.985 at T=0.5, 0.995 at T=0.7, and 0.978
  at T=1.0; median words before the first newline were 3, 3, and 4
  respectively. This makes the first newline a more appropriate child-turn
  boundary than waiting for an explicit `Caregiver:` label.

- Updated `src/sample_context_responses.py` so the default stop strings include
  a generic newline after the child response:

```text
["\nCaregiver:", "\nParent:", "\nAdult:", "\nChild:", "\nCHI:", "\n"]
```

The cleaner records a generic newline boundary as speaker marker `\n`, and
focused tests cover both generic newline and explicit speaker-label behavior.

- Final validation probe (`results/response_entropy_stopping_probe_v3/`,
  `docs/response_entropy_stopping_probe_v3.html`) ran 800 samples on the PC:
  40 contexts x temperatures 0.5 and 0.7 x cap 48 x 10 samples. It completed
  at 2026-06-16 13:10:07 EDT. Summary:

```text
T=0.5: rows=400, boundary_seen_rate=0.985, hit_cap_no_boundary_rate=0.015,
       empty_response_rate=0.0025, mean trimmed words=4.22,
       p50 trimmed words=3, p90=9, p95=12
T=0.7: rows=400, boundary_seen_rate=0.995, hit_cap_no_boundary_rate=0.005,
       empty_response_rate=0.0025, mean trimmed words=4.29,
       p50 trimmed words=3, p90=8.1, p95=11
```

The report still shows `hit_max_rate=1.0` because the current implementation
generates the full 48 tokens and then trims the decoded text. That is a
computational inefficiency, not evidence that the analytic response is
length-capped. The scientifically relevant result is that the decoded text
almost always contains a line/turn boundary before the cap.

- Scientific decision for Route 2:
  - Do not enforce the observed child's utterance length. That would turn the
    response-space entropy measure into a same-length production control rather
    than a distribution over plausible next child turns.
  - Use free child-turn sampling: prompt with caretaker context and `Child:`,
    sample the next child turn, then trim at the first newline/speaker
    boundary/EOS.
  - Use `max_new_tokens=48` as a generous safety cap for T=0.5/T=0.7, and
    record sampled response length as a diagnostic/feature.
  - Treat T=0.5 as the primary production candidate and T=0.7 as the main
    sensitivity candidate unless manual quality review changes this. Avoid
    T=1.3/T=1.6 for production entropy; T=1.0 is optional and less reliable.
  - Before a large production run, consider adding a Transformers stopping
    criterion for newline/speaker markers to avoid wasting GPU time, but the
    existing post-generation trimming is scientifically adequate for the
    response text itself.

- Copied the corrected probe outputs back from the PC with `rsync` for:

```text
results/response_entropy_stopping_probe_v2/
figs/response_entropy_stopping_probe_v2/
docs/response_entropy_stopping_probe_v2.md
docs/response_entropy_stopping_probe_v2.html
results/response_entropy_stopping_probe_v3/
figs/response_entropy_stopping_probe_v3/
docs/response_entropy_stopping_probe_v3.md
docs/response_entropy_stopping_probe_v3.html
```

- Regenerated the local v2/v3 stopping-probe reports after replacing the
  stop-category figure with a more robust grouped bar plot. Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_response_level_context_entropy \
  tests.test_build_response_entropy_stopping_probe

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

passed with 13 focused tests and 257 full-suite tests.

## 2026-06-16 - Response-space generation automatic quality audit

- Ran an automatic quality audit on already-generated samples only; no new
  generation was launched. The audit re-trimmed raw text at the first newline
  to simulate the proposed first-line/end-of-turn response unit.
- Structural quality flags included empty first line, speaker label inside the
  kept first line, metadata/prose starts such as `The caregiver` or markdown
  headings, no newline before the cap, overly long first lines, repetition
  loops, and a softer exact/near context-copy review flag.
- Main automatic results:

```text
v3 cap-48 probe:
T=0.5 hard_bad_rate=0.0425, review_flag_including_copy=0.0975
T=0.7 hard_bad_rate=0.0250, review_flag_including_copy=0.0725

full 288k pilot, re-trimmed at first line:
T=0.5 hard_bad_rate=0.0342, review_flag_including_copy=0.1141
T=0.7 hard_bad_rate=0.0425, review_flag_including_copy=0.0873
T=1.0 hard_bad_rate=0.1135, review_flag_including_copy=0.1227
```

- Interpretation: T=0.5/T=0.7 look viable for a formalized Route 2 measurement
  after quality documentation; T=1.0 is much less attractive because cap/no-
  boundary failures rise sharply. The hard structural failure rate is low at
  T=0.5/T=0.7, but semantic oddities still require manual review because
  automatic flags cannot reliably judge context appropriateness.
- Recommended pre-Slurm sequence:
  1. Implement true end-of-turn stopping during generation, while preserving
     raw text, stop reason, and quality flags.
  2. Run one small smoke on existing pilot contexts at T=0.5/T=0.7.
  3. Manually label a stratified sample of generated first-line responses.
  4. Run a small prompt-robustness smoke before full Mila production.

## 2026-06-16 - Exhaustive Internal M1-M6 Super Atlas

- Added a reproducible synthesis/report stage:

```text
src/build_m1_m6_super_atlas_report.py
tests/test_build_m1_m6_super_atlas_report.py
```

- Purpose: create an internal cherry-picking source report for the supervisor
  writeup, not a supervisor-facing narrative. The report explicitly documents
  for each M1-M6 family:
  - scientific question and formula;
  - whether the main fit is ordinary least squares;
  - which library/object was used (`statsmodels.formula.api.ols`, GLM, GEE,
    or MixedLM);
  - whether child identity is a fixed effect (`C(child_id)`) or a random-effect
    sensitivity check;
  - takeaways and caveats before the plot/table galleries.

- Generated outputs:

```text
docs/utterance_information_m1_m6_super_atlas.md
docs/utterance_information_m1_m6_super_atlas.html
figs/m1_m6_super_atlas/
results/m1_m6_super_atlas/figure_inventory.csv
results/m1_m6_super_atlas/source_artifact_inventory.csv
results/m1_m6_super_atlas/model_coverage_summary.csv
results/m1_m6_super_atlas/overview_figure_manifest.csv
```

- Source coverage recorded in the report:
  - 19 source CSV artifacts.
  - 413 existing relevant PNG source figures.
  - 11 newly generated overview figures.
  - 437 Markdown image references in the final report, with 0 missing files.

- Model coverage summary after correcting figure grouping to infer model IDs
  from filenames rather than parent directories:

```text
model  dual_rows  estimator_sensitivity_rows  context_rows  robustness_rows  figure_rows
M1     10         20                          20            80               46
M2     10         35                          20            80               54
M3     10         55                          20            80               57
M4     10         0                           60            60               67
M5     10         0                           60            60               63
M6     10         0                           60            60               63
```

- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_m1_m6_super_atlas_report

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_super_atlas_report.py

.venv/bin/python -c "from pathlib import Path; import re; md=Path('docs/utterance_information_m1_m6_super_atlas.md'); text=md.read_text(); imgs=re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text); missing=[src for src in imgs if not (md.parent/src).resolve().exists()]; print(len(imgs), len(missing))"
```

Focused tests passed: 3 tests. Full suite passed: 260 tests in 259.611s.
Image-reference check: 437 refs, 0 missing.

## 2026-06-16 - Interpreted M1-M6 Atlas v2 and Technical Companion

- Saved the recent email motivating the naturalistic child communicative-
  efficiency analysis exactly as provided:

```text
docs/project_motivation_recent_email_context_2026-06-16.md
```

- Added a synthesis/report-only builder and focused test:

```text
src/build_m1_m6_interpreted_atlas_report.py
tests/test_build_m1_m6_interpreted_atlas_report.py
```

- Generated a new interpreted version of the M1-M6 super atlas without
  modifying the original atlas:

```text
docs/utterance_information_m1_m6_super_atlas_v2_interpreted.md
docs/utterance_information_m1_m6_super_atlas_v2_interpreted.html
```

- Generated a separate technical implementation companion:

```text
docs/utterance_information_m1_m6_technical_implementation_companion.md
docs/utterance_information_m1_m6_technical_implementation_companion.html
```

- The interpreted atlas now explicitly connects the email's two-part
  communicative-efficiency framing to the current modeling state:
  - Route 1/current evidence: informativeness under controlled effort,
    especially M2 `sum_bits ~ age_c + target_effort_c + C(child_id)`;
  - Route 2/future analysis: effort or utterance length as the outcome,
    predicted by response-space/context uncertainty plus confounds.
- The report includes the exact saved email block, a model-by-model M1-M6
  interpretation, coefficient meanings, plot-family reading notes, a balanced
  discussion of child fixed effects, and proposed-not-yet-run formulas for
  within/between child age decomposition, age-overlap checks, random slopes,
  and Route 2 length prediction.
- The companion explains OLS, GLM, GEE, MixedLM, fixed effects, random effects,
  clustered standard errors, interactions, centering, R2, p-values, fixed-
  effort prediction plots, and the Route 1/Route 2 distinction in mechanical
  terms.
- Generated audit outputs:

```text
results/m1_m6_interpreted_atlas/interpreted_atlas_image_link_audit.csv
results/m1_m6_interpreted_atlas/figure_inventory.csv
results/m1_m6_interpreted_atlas/source_artifact_inventory.csv
```

- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_m1_m6_interpreted_atlas_report

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_m1_m6_super_atlas_report \
  tests.test_build_m1_m6_interpreted_atlas_report

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_interpreted_atlas_report.py

rg -n ",False|,false" \
  results/m1_m6_interpreted_atlas/interpreted_atlas_image_link_audit.csv

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

Focused interpreted-atlas test passed: 1 test. Super-atlas plus interpreted-
atlas tests passed: 4 tests. Builder rendered both reports and audit CSVs.
Image-link audit recorded 415 interpreted-atlas image references with 0 missing
files. Full suite passed: 261 tests in 263.827s.

## 2026-06-16 - Route 2 cap-96 extreme-temperature smoke and meeting report

- User asked for a super-short cap-96 run at the temperatures not covered by
  the previous cap grid: T=0.3, T=1.3, and T=1.6. Purpose: distinguish whether
  the poor high-temperature newline rates in the full pilot were caused only
  by the earlier 24-token cap, or whether high temperatures remain unsuitable
  even with a larger safety cap.
- Synced the current Route 2 sampler/probe files to the PC:

```text
src/sample_context_responses.py
src/build_response_entropy_stopping_probe.py
scripts/run_response_entropy_stopping_probe_pc.sh
tests/test_response_level_context_entropy.py
tests/test_build_response_entropy_stopping_probe.py
```

- Launched a detached PC job:

```text
output_dir: results/response_entropy_stopping_probe_v4_cap96_extreme_temps/
fig_dir: figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/
report: docs/response_entropy_stopping_probe_v4_cap96_extreme_temps.html
temperatures: 0.3, 1.3, 1.6
max_new_tokens: 96
contexts_per_bucket: 10
samples_per_context: 10
planned samples: 1,200
```

The first launch failed immediately because the script was not executable on
the PC (`permission denied`). Relaunched successfully via `zsh
scripts/run_response_entropy_stopping_probe_pc.sh`.

- The independent progress-check command used during the run was:

```bash
ssh alkan@192.168.7.217 \
  'cd /home/alkan/Portelance/communicative_efficiency; \
   pid=$(cat results/response_entropy_stopping_probe_v4_cap96_extreme_temps/logs/stopping_probe_run.pid); \
   ps -o pid,ppid,sid,stat,etime,cmd -p "$pid"; \
   nvidia-smi --query-gpu=utilization.gpu,memory.used,power.draw,temperature.gpu --format=csv,noheader,nounits; \
   tail -n 30 results/response_entropy_stopping_probe_v4_cap96_extreme_temps/logs/stopping_probe_run.log'
```

- Run completed on the PC at 2026-06-16 14:21:24 EDT:

```text
rows_written: 1,200
elapsed_seconds: 699.9
```

Synced back:

```text
results/response_entropy_stopping_probe_v4_cap96_extreme_temps/
figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/
docs/response_entropy_stopping_probe_v4_cap96_extreme_temps.md
docs/response_entropy_stopping_probe_v4_cap96_extreme_temps.html
```

- Cap-96 stopping result:

```text
T=0.3: boundary_seen_rate=1.0000, hit_cap_no_boundary_rate=0.0000
T=1.3: boundary_seen_rate=0.8000, hit_cap_no_boundary_rate=0.2000
T=1.6: boundary_seen_rate=0.3725, hit_cap_no_boundary_rate=0.6275
```

In plain terms:

```text
T=0.3: 0.00% did not reach newline before cap 96
T=1.3: 20.00% did not reach newline before cap 96
T=1.6: 62.75% did not reach newline before cap 96
```

- Automatic quality audit for v4 first-line responses:

```text
T=0.3: hard_bad_rate=3.00%, review_rate=7.75%
T=1.3: hard_bad_rate=28.75%, review_rate=29.25%
T=1.6: hard_bad_rate=70.50%, review_rate=70.50%
```

The high-temperature examples were often long and incoherent, e.g. T=1.3/T=1.6
responses drifted into unrelated names, fragments, prose, and word salad. The
larger cap therefore does not rescue T=1.3/T=1.6 for production.

- Created a meeting-facing Route 2 piloting report:

```text
docs/response_entropy_route2_piloting_report.md
docs/response_entropy_route2_piloting_report.html
```

The report documents:

```text
supervisor-request interpretation;
current operational definition;
prompt and stopping rationale;
full 288k pilot;
corrected cap-grid probe;
newline-stop validation probe;
cap-96 extreme-temperature smoke;
automatic quality audit;
good/review/bad examples;
production recommendation;
questions to ask supervisors before Slurm production.
```

- Current Route 2 production recommendation:

```text
Primary temperature: T=0.5
Sensitivity temperature: T=0.7
Optional conservative diagnostic: T=0.3
Do not use for production: T=1.3, T=1.6
Safety cap: max_new_tokens=96
Generation rule: true end-of-turn stopping during decoding
Quality rule: resample until N valid child-turn responses, but record every
rejected attempt and rejection reason.
```

- Key supervisor questions now documented:
  1. Is `Caregiver: {context}\nChild:` an acceptable operational prompt for
     "possible child responses"?
  2. Should entropy be estimated over accepted valid child-turn completions
     only, with rejected attempts reported, or should invalid completions remain
     part of the empirical distribution?
  3. Is T=0.5 primary plus T=0.7 sensitivity sufficient?
  4. Should context-copy responses be kept, flagged, or excluded?
  5. Should production target 100 accepted samples per context or 100 total
     attempts?

- Added two future-agent task prompts:

```text
docs/route2_final_generation_smoke_prompt.md
docs/route2_entropy_scoring_script_prompt.md
```

The first prompt covers the final automatic generation smoke at temperatures
0.3/0.5/0.7/1.0. The second prompt covers the entropy feature/scoring script
that consumes generated samples. This explicitly preserves the distinction:
sampling possible answers is the GPU generation step, while entropy scoring is
the downstream CPU feature-building step unless sequence-probability rescoring
is added later.

## 2026-06-16 - Route 1 model-ladder clarification after review

- Clarified the child-identity language in the interpreted M1-M6 atlas and
  technical companion:
  - `C(child_id)` means child fixed intercepts: one baseline per child, with a
    shared child-adjusted age slope.
  - `(1 | child_id)` means a mixed-model random child intercept: partially
    pooled child baselines under a population-distribution assumption.
  - `(1 + age_c | child_id)` adds random child age slopes, useful if stable but
    potentially singular when child age coverage is narrow.
  - child-clustered standard errors are not a child-identity control; they keep
    the fitted mean but change uncertainty.

- Clarified formula hierarchy for the corrected Route 1 ladder. In
  statsmodels/Patsy syntax `age_c * effort_c` expands to:

```text
age_c + effort_c + age_c:effort_c
```

The cleaned Route 1 core to implement next is:

```text
M1:  sum_bits ~ age_c + effort_c
M2:  sum_bits ~ age_c + effort_c + C(child_id)
M3:  sum_bits ~ age_c * effort_c + C(child_id)
M4a: M3 + parent_context_effort_c
M4b: M3 + context_entropy_c
M4c: M3 + question_type
M5:  M3 + parent_context_effort_c + context_entropy_c + question_type
M6:  M3 + age_c:context_entropy_c + effort_c:context_entropy_c
     + parent_context_effort_c + question_type
```

- Clarified baseline-comparison logic for Route 1:
  - first repeat the complete M1-M6 atlas independently for real child, random,
    unigram, bigram, trigram, and LSTM target sources;
  - keep formulas, effort units, context windows, age bins, and robustness
    checks parallel across sources;
  - then compare source-specific age coefficients, fixed-effort curves, and
    age-scrambling robustness;
  - only after those source-specific atlases exist, fit the pooled formal
    comparison:

```text
sum_bits ~ target_source * age_c * effort_c + context_controls + C(child_id)
```

- Updated files:

```text
src/build_m1_m6_interpreted_atlas_report.py
tests/test_build_m1_m6_interpreted_atlas_report.py
docs/utterance_information_m1_m6_super_atlas_v2_interpreted.md
docs/utterance_information_m1_m6_super_atlas_v2_interpreted.html
docs/utterance_information_m1_m6_technical_implementation_companion.md
docs/utterance_information_m1_m6_technical_implementation_companion.html
TODO.md
```

- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_m1_m6_interpreted_atlas_report

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_interpreted_atlas_report.py

rg -n ",False|,false" \
  results/m1_m6_interpreted_atlas/interpreted_atlas_image_link_audit.csv
```

Focused test passed: 1 test. Builder regenerated both reports. Image-link
audit still has 415 interpreted-atlas image references with 0 missing files.

## 2026-06-16 - Corrected Route 1 baseline-atlas scaffold

- Added a first implementation scaffold for the corrected Route 1 rebuild:

```text
src/build_route1_corrected_baseline_atlas.py
tests/test_build_route1_corrected_baseline_atlas.py
```

- The scaffold does not run the full atlas by default. It writes manifests,
  source-coverage audits, and bounded smoke fits so the long run can be
  launched deliberately.
- Encoded the corrected scientific separation:
  - source-specific M1-M6/MX atlases are independent first-pass reports;
  - real, random, unigram, bigram, trigram, and each LSTM target variant should
    each get its own technical atlas report;
  - the pooled `target_source * age_c * effort_c` model is a later comparison
    report that reads/compares selected source-specific outputs, not a
    replacement for fitting the source-specific atlases.
- Encoded the child-structure guardrails:
  - `CS1`/`CS2` use `C(child_id)` fixed intercepts/slopes;
  - `CS4`/`CS5` MixedLM random-effect variants do not include `C(child_id)`;
  - `CS6` uses within-child age with `C(child_id)`;
  - `CS7` uses within-child age plus `child_mean_age_c` without `C(child_id)`.
- Added parent-context effort derivation from `context_text` for all five
  effort units and a rule-based `question_type` predictor.
- Generated manifest artifacts under ignored results:

```text
results/route1_corrected_baseline_atlas/corrected_primary_source_specific_manifest.csv
results/route1_corrected_baseline_atlas/corrected_child_structure_sensitivity_manifest.csv
results/route1_corrected_baseline_atlas/child_structure_definitions.csv
results/route1_corrected_baseline_atlas/corrected_model_family_definitions.csv
```

- Manifest row counts:

```text
corrected_primary_source_specific_manifest.csv: 600 model rows + header
corrected_child_structure_sensitivity_manifest.csv: 72 model rows + header
```

- Ran a bounded source audit on the existing smoke Route 1 long table:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_corrected_baseline_atlas.py \
  --stage audit \
  --input results/route1_analysis_dataset/smoke_route1_scored_utterance_effort_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/smoke_route1_long \
  --max-rows 250000 \
  --chunksize 50000
```

Audit output:

```text
results/route1_corrected_baseline_atlas/smoke_route1_long/source_coverage_audit.csv
```

The bounded smoke audit saw five child target sources (`real`, `random`,
`unigram`, `bigram`, `trigram`) for `k0`, but only one child in that smoke
slice, so it is a plumbing check rather than a scientific modeling sample.

- Ran a bounded smoke fit:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_corrected_baseline_atlas.py \
  --stage smoke-fit \
  --input results/route1_analysis_dataset/smoke_route1_scored_utterance_effort_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/smoke_route1_long \
  --max-rows 250000 \
  --chunksize 50000 \
  --target-sources real,random \
  --context-ks k0 \
  --effort-cols nb_words \
  --child-structures CS0c,CS1 \
  --model-ids M1,M2,M3,M4a,M4b
```

Smoke fit output:

```text
results/route1_corrected_baseline_atlas/smoke_route1_long/smoke_fit_summary.csv
```

It wrote 20 model rows. All non-entropy k0 rows were correctly skipped with
`fewer than two children`; entropy rows were correctly skipped with
`no complete rows` because the smoke input lacks context entropy.

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m py_compile \
  src/build_route1_corrected_baseline_atlas.py

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_route1_corrected_baseline_atlas

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

Focused tests passed: 10 tests. Full suite passed: 276 tests. The full long
Route 1 atlas has not been run.

## 2026-06-16 - Agent prompt for corrected Route 1 rebuild

- Added an agent-facing launch prompt for the long corrected Route 1
  implementation:

```text
docs/route1_corrected_baseline_atlas_agent_prompt.md
```

- The prompt is designed for a fresh coding agent and records:
  - the corrected Route 1 scope and the instruction to keep Route 2 parked;
  - the child-structure variants to compare separately;
  - the rule not to combine `C(child_id)` with `(1 | child_id)`;
  - the rule not to estimate `child_mean_age` inside a `C(child_id)` model;
  - the corrected M1-M6 formula ladder with hierarchy;
  - the requirement to repeat the full atlas independently for real child,
    random, unigram, bigram, trigram, and LSTM target sources;
  - the later pooled source-comparison model;
  - phased implementation steps, expected deliverables, and an acceptance
    checklist.

- Updated `TODO.md` so the immediate Route 1 cleanup section points to this
  prompt and makes the child-structure comparison explicit.
- Corrected the interpreted atlas/technical companion proposed-model wording so
  within/between age decomposition is not written as
  `child_mean_age + C(child_id)`.
- Verification:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_m1_m6_interpreted_atlas_report

env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_m1_m6_interpreted_atlas_report.py
```

Focused test passed: 1 test. Builder regenerated both reports. Image-link
audit still has 415 interpreted-atlas image references with 0 missing files.

## 2026-06-16 - Route 2 final pre-Slurm generation smoke

- Implemented the final response-generation smoke in:

```text
src/build_response_entropy_final_generation_smoke.py
scripts/run_response_entropy_final_generation_smoke_pc.sh
tests/test_build_response_entropy_final_generation_smoke.py
```

- The smoke is generation/sampling only. It does not compute downstream
  entropy features for Route 2 modeling.
- The sampler uses true end-of-turn stopping during decoding for:

```text
\n
\nCaregiver:
\nParent:
\nAdult:
\nChild:
\nCHI:
```

- It records every attempt, accepted or rejected, with deterministic quality
  flags and rejection reasons.
- Local focused verification before GPU launch:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_response_entropy_final_generation_smoke \
  tests.test_response_level_context_entropy \
  tests.test_build_response_entropy_stopping_probe
```

Focused regression result: 18 tests passed.

- Ran the real smoke on the PC through SSH, detached as PID `19436`:

```bash
ssh alkan@192.168.7.217
cd /home/alkan/Portelance/communicative_efficiency
setsid scripts/run_response_entropy_final_generation_smoke_pc.sh \
  > results/response_entropy_final_generation_smoke/logs/final_generation_smoke.log \
  2>&1 < /dev/null &
```

- PC generation settings:

```text
model: mistralai/Mistral-7B-v0.3
contexts: 40, balanced 10 per context-length bucket
prompt variants: Caregiver, Parent, Adult
temperatures: 0.3, 0.5, 0.7, 1.0
target accepted samples per context-temperature-prompt: 20
max attempts per context-temperature-prompt: 60
max_new_tokens: 96 safety cap
top_p: 0.95
top_k: 0
dtype: bfloat16
device: auto
```

- Runtime:

```text
PC start: 2026-06-16 15:06:23 EDT
PC finish: 2026-06-16 15:28:04 EDT
logged elapsed_seconds: 1288.0
```

- Copied the completed outputs back to the laptop:

```text
results/response_entropy_final_generation_smoke/
figs/response_entropy_final_generation_smoke/
docs/response_entropy_final_generation_smoke.md
docs/response_entropy_final_generation_smoke.html
```

- Required output tables exist:

```text
accepted_samples.csv.gz
all_attempts.csv.gz
rejection_summary_by_setting.csv
quality_flags_by_setting.csv
prompt_temperature_rank_correlations.csv
manual_review_examples.csv
smoke_manifest.csv
smoke_manifest_audit.csv
```

- Run totals:

```text
planned settings: 480 = 40 contexts x 3 prompt variants x 4 temperatures
planned accepted samples: 9,600
accepted samples written: 9,512
attempts written: 10,203
settings reaching 20 accepted samples: 473 / 480
settings hitting the 60-attempt cap incomplete: 7 / 480
```

- All incomplete settings came from one long repetitive context:

```text
context_id: 053b94a7737f6201a29fa0db
context_text: blink blink blink blink blink blink blink. blink blink blink. that's a light too.
```

The main rejection reason there was repetition-loop detection, especially at
lower temperatures.

- Temperature summary:

```text
T=0.3: 2,343 accepted / 2,540 attempts; rejection rate 7.76%; 3 incomplete settings
T=0.5: 2,371 accepted / 2,550 attempts; rejection rate 7.02%; 3 incomplete settings
T=0.7: 2,398 accepted / 2,523 attempts; rejection rate 4.95%; 1 incomplete setting
T=1.0: 2,400 accepted / 2,590 attempts; rejection rate 7.34%; 0 incomplete settings
```

- Prompt robustness:

```text
median prompt-within-temperature Spearman:
T=0.3: 0.605
T=0.5: 0.744
T=0.7: 0.732
T=1.0: 0.592
overall median: 0.693
```

- Decision readout from the smoke:
  - T=0.5 primary and T=0.7 sensitivity are defensible as the production
    recommendation, with explicit rejection-rate reporting.
  - T=0.3 is useful as a conservative diagnostic but is vulnerable to
    low-temperature repetition loops on pathological contexts.
  - T=1.0 should remain optional/diagnostic rather than primary production.
  - Prompt rankings are stable enough for a smoke-test recommendation, but not
    so high that prompt wording can be ignored.
  - Supervisors should explicitly approve accepted-only entropy, handling of
    context-copy responses, and whether to keep the prompt wrapper.

- Rerendered the local report after the PC run to make the incomplete-setting
  caveat explicit; no GPU rerun was needed.
- Post-run focused verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_final_generation_smoke.py \
  --stage summarize \
  --output-dir results/response_entropy_final_generation_smoke \
  --fig-dir figs/response_entropy_final_generation_smoke \
  --report-md docs/response_entropy_final_generation_smoke.md \
  --report-html docs/response_entropy_final_generation_smoke.html

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_response_entropy_final_generation_smoke
```

Focused post-run test result: 5 tests passed.

## 2026-06-16 - Expanded corrected Route 1 atlas readiness pass

- Expanded `src/build_route1_corrected_baseline_atlas.py` beyond the core
  M1-M6 ladder. The source-specific atlas manifest now includes:
  - core M1-M6, with M4 split into M4a/M4b/M4c;
  - extended internal models M7-M15:
    - M7 nonlinear age;
    - M8 nonlinear age by effort;
    - M9 categorical age-bin trajectory;
    - M10 age-bin by effort;
    - M11 age by parent-context effort;
    - M12 age by question type;
    - M13 context entropy by question type;
    - M14 parent effort by context entropy;
    - M15 expanded context-interaction stress test.
- Added default source targets for the LSTM scored variants:

```text
lstm_additive_k3_same_length
lstm_additive_k4_same_length
lstm_additive_k5_same_length
```

- Added stage support:
  - `manifest`: writes model/report/command manifests only;
  - `preflight`: writes manifests plus a bounded source-coverage audit;
  - `fit-atlas`: fits selected source-specific models one target source at a
    time and writes separate source report Markdown stubs;
  - `smoke-fit`: remains for bounded quick checks.
- The generated launch-command handoff is:

```text
results/route1_corrected_baseline_atlas/FULL_RUN_COMMANDS.md
```

- The launch handoff now includes a separate core child-structure sensitivity
  command for real child utterances: CS0, CS0c, CS1, CS2, CS3, CS4, CS5, CS6,
  and CS7 are fit outside the source-specific baseline atlas.

- Regenerated default manifest artifacts:

```text
results/route1_corrected_baseline_atlas/corrected_primary_source_specific_manifest.csv
results/route1_corrected_baseline_atlas/corrected_child_structure_sensitivity_manifest.csv
results/route1_corrected_baseline_atlas/corrected_report_plan.csv
results/route1_corrected_baseline_atlas/child_structure_definitions.csv
results/route1_corrected_baseline_atlas/corrected_model_family_definitions.csv
```

- Current manifest row counts:

```text
corrected_primary_source_specific_manifest.csv: 2,040 model rows + header
corrected_child_structure_sensitivity_manifest.csv: 72 model rows + header
corrected_report_plan.csv: 10 report-plan rows + header
```

- Ran small checks only, not the full scientific fit:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_route1_corrected_baseline_atlas

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_corrected_baseline_atlas.py \
  --stage preflight \
  --input results/route1_analysis_dataset/smoke_route1_scored_utterance_effort_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/smoke_preflight_expanded \
  --target-sources real,random,unigram,bigram,trigram,lstm_additive_k3_same_length \
  --context-ks k0 \
  --effort-cols nb_words \
  --model-ids M1,M2,M7,M10 \
  --max-rows 250000 \
  --chunksize 50000

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_corrected_baseline_atlas.py \
  --stage fit-atlas \
  --input results/route1_analysis_dataset/smoke_route1_scored_utterance_effort_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/smoke_fit_expanded \
  --target-sources real,random \
  --context-ks k0 \
  --effort-cols nb_words \
  --child-structures primary \
  --model-ids M1,M2,M7,M10 \
  --max-rows 250000 \
  --chunksize 50000
```

- Focused tests passed after the final launch-command update: 15 tests.
- Full suite passed after the final launch-command update: 281 tests in
  275.911 seconds.
- Smoke preflight wrote manifests, report plan, source audit, and launch
  commands.
- Smoke `fit-atlas` wrote 8 model rows plus independent source Markdown reports
  under `results/route1_corrected_baseline_atlas/smoke_fit_expanded/reports/`.
  The smoke input has only one child in the bounded slice, so the model rows
  correctly skip as non-scientific plumbing checks.
- Full long fit still has not been run.

## 2026-06-16 - Route 2 entropy-smoke handoff after final generation smoke

- Updated the Route 2 handoff Markdown after completing the final generation
  smoke. The next prompt is:

```text
docs/route2_entropy_scoring_script_prompt.md
```

- The entropy smoke should consume the existing final generation-smoke
  artifacts, not regenerate samples unless an artifact is missing or corrupted:

```text
results/response_entropy_final_generation_smoke/accepted_samples.csv.gz
results/response_entropy_final_generation_smoke/all_attempts.csv.gz
results/response_entropy_final_generation_smoke/rejection_summary_by_setting.csv
results/response_entropy_final_generation_smoke/quality_flags_by_setting.csv
results/response_entropy_final_generation_smoke/smoke_manifest.csv
results/response_entropy_final_generation_smoke/smoke_manifest_audit.csv
docs/response_entropy_final_generation_smoke.html
```

- The final generation smoke is ready to feed the entropy-scoring smoke. Full
  Mila-scale generation should still wait until the entropy smoke confirms
  stable predictors, acceptable join coverage, and supervisor approval of the
  accepted-only entropy definition.

## 2026-06-16 - Route 2 final entropy scoring smoke

- Added the CPU-only Route 2 entropy scoring script:

```text
src/build_response_entropy_final_scoring_smoke.py
tests/test_build_response_entropy_final_scoring_smoke.py
```

- The script consumes the final generation-smoke CSVs and does not generate
  responses or call Mistral. It computes response-space entropy over accepted
  sampled child-turn strings, with primary `casefold` response-type counting
  plus exact and punctuation-stripped sensitivity columns.
- The Route 2 join uses the existing real-child/context analysis frame only as
  the source of real child effort outcomes and caregiver `context_text` values.
  This is still Route 2 feature building, not a new Route 1 surprisal analysis.
- Verification commands:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_response_entropy_final_scoring_smoke

MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_final_scoring_smoke.py
```

- Focused tests passed: 5 tests.
- Full suite passed after the scoring smoke: 286 tests in 302.021 seconds.
- Real final-smoke scoring outputs:

```text
docs/response_entropy_final_scoring_smoke.md
docs/response_entropy_final_scoring_smoke.html
results/response_entropy_final_scoring_smoke/context_response_entropy_features.csv
results/response_entropy_final_scoring_smoke/context_response_entropy_stability.csv
results/response_entropy_final_scoring_smoke/context_response_entropy_join_audit.csv
results/response_entropy_final_scoring_smoke/context_response_entropy_temperature_correlations.csv
results/response_entropy_final_scoring_smoke/context_response_entropy_prompt_correlations.csv
results/response_entropy_final_scoring_smoke/route2_analysis_smoke_with_entropy.csv.gz
results/response_entropy_final_scoring_smoke/route2_sanity_model_summary.csv
results/response_entropy_final_scoring_smoke/manual_review_entropy_examples.csv
figs/response_entropy_final_scoring_smoke/
```

- Output counts:

```text
feature rows: 480
finite entropy rows: 478
zero-accepted settings: 2
settings below 20 accepted samples: 7
stability rows: 480
join-audit incomplete-setting rows: 7
joined Route 2 smoke rows written: 6,228
eligible real-child rows scanned for join audit: 1,332,975
matched real-child rows: 519
missing full-frame rows: 1,332,456
```

- Decision output from the smoke:
  - The entropy script is ready to consume full Mila-scale sample artifacts as
    a CPU feature builder.
  - The final smoke cannot directly answer whether 100 accepted samples per
    context are stable, because it targeted at most 20 accepted samples per
    context/prompt/temperature setting.
  - T=0.5 and T=0.7 give mostly similar context rankings in this smoke:
    median within-prompt Spearman is 0.815.
  - Prompt wording changes the predictor enough to keep prompt wording visible
    as a design choice: median prompt-within-temperature Spearman is 0.693.
  - Join gaps are explainable but not small for the full frame because this is
    a 40-context smoke; within sampled contexts, the normalized context-text
    hash join works and duplicate k1/k2/k3 text is deduplicated correctly.
  - Suggested supervisor summary: the measurement pipeline works; final-smoke
    entropy favors T=0.5 primary with T=0.7 sensitivity, but 20 samples cannot
    certify 100-sample production stability.

## 2026-06-16 - Current scored real-child coverage plots

- Built the current-scored real-child coverage plots from the PBM scored
  Mistral tree, counting each real utterance once from `k0` outputs.
- Current scored real-child universe: 21 children from Brown, Manchester, and
  Providence; 446,508 scored real-child rows; observed ages 11.133-62.4 months;
  52 integer months covered from 11 through 62.
- The smallest current-scored child set covering all current-scored integer
  months is Providence/Naima, Brown/Sarah, and Brown/Adam.
- Outputs:

```text
figs/route1_current_scored_coverage/current_scored_real_child_age_coverage.png
figs/route1_current_scored_coverage/current_scored_real_child_age_coverage.pdf
figs/route1_current_scored_coverage/current_scored_minimal_month_cover_set.png
figs/route1_current_scored_coverage/current_scored_minimal_month_cover_set.pdf
results/route1_current_scored_coverage/current_scored_real_child_coverage_summary.csv
results/route1_current_scored_coverage/current_scored_real_child_age_points.csv
results/route1_current_scored_coverage/current_scored_minimal_month_cover_set.csv
results/route1_current_scored_coverage/current_scored_child_candidate_ranking.csv
```

- Added same-axis row-comparison plots for selecting heldout children. These
  put proposed strict-preprocessed heldout candidates, the current scored
  3-child cover set, Brown/Manchester/Providence scored dataset-union rows, and
  the all-PBM scored union on one age axis:

```text
figs/route1_current_scored_coverage/current_scored_subset3_vs_all21_union_tight.png
figs/route1_current_scored_coverage/current_scored_subset3_vs_all21_union_tight.pdf
results/route1_current_scored_coverage/current_scored_subset3_vs_all21_union_by_month.csv
results/route1_current_scored_coverage/current_scored_subset3_vs_all21_union_summary.csv
figs/route1_current_scored_coverage/scored_pbm_vs_proposed_sets_row_coverage.png
figs/route1_current_scored_coverage/scored_pbm_vs_proposed_sets_row_coverage.pdf
results/route1_current_scored_coverage/scored_pbm_vs_proposed_sets_row_coverage.csv
results/route1_current_scored_coverage/nonpbm_three_child_set_ranking.csv
```

- Exhaustive ranking of all 30,856 three-child combinations from the 58
  non-PBM strict children confirms that Forrester/Ella,
  MPI-EVA-Manchester/Helen, and Sachs/Naomi are the unique 3-child set covering
  all non-PBM observed integer months, 12-61. No non-PBM set can cover PBM-only
  months 11 and 62.

## 2026-06-16 - Heldout real-child scoring handoff

- Added a tested heldout scoring bundle builder for the best non-PBM
  three-child set:

```text
src/create_heldout_real_child_scoring_bundle.py
tests/test_create_heldout_real_child_scoring_bundle.py
docs/heldout_real_child_generalization_pc_scoring_prompt.md
```

- Built the real-child-only bundle:

```text
results/scoring_bundles/heldout_real_child_generalization_2026-06-16/
results/scoring_bundles/heldout_real_child_generalization_2026-06-16.tar.gz
```

- Bundle contents: Forrester/Ella, Sachs/Naomi, and
  MPI-EVA-Manchester/Helen `chi.surprisal_scoring.csv` files, preserving
  age/session/file metadata, `context_k1`-`context_k3`, and real target text.
  It deliberately does not stage generated-baseline scoring.
- Row counts:

```text
Forrester/Ella: 6,663 rows, ages 12.033-60.000, 0 blank targets
Sachs/Naomi: 16,344 rows, ages 14.967-57.100, 0 blank targets
MPI-EVA-Manchester/Helen: 154,593 rows, ages 36.067-61.633, 0 blank targets
total: 177,600 rows
expected scoring tasks: 12 = 3 children x real mode x k0/k1/k2/k3
```

- Predictor availability is recorded in
  `metadata/predictor_availability.csv`: age/session/file metadata, real target
  text, and caretaker context text are available before scoring; context
  entropy, response-space entropy, and generated-baseline scores are not yet
  available for these heldout children.
- Verified locally with focused tests and a scorer-side dry run. The dry run
  extracted the tarball under `/tmp`, ran the bundled scoring wrapper with
  `DRY_RUN=1`, and built a 12-task manifest.
- Rsynced the tarball and PC prompt to:

```text
alkan@192.168.7.217:/home/alkan/Portelance/compute_surprisal_mila/new_data/
```

- Verified on the PC that the corrected wrapper falls back to
  `.venv/bin/python` when `uv` is not on PATH. Remote dry run wrote exactly 12
  tasks to:

```text
/home/alkan/Portelance/compute_surprisal_mila/slurm/tasks_heldout_real_child_generalization_2026-06-16_mistral.tsv
```

## 2026-06-16 - Caretaker Route 1 atlas preflight prepared

- Added the caretaker-target atlas scaffold:

```text
src/build_route1_caretaker_atlas.py
tests/test_build_route1_caretaker_atlas.py
```

- Scope: entropy-free caretaker utterance information models. The outcome is
  caretaker `sum_bits`; the timeline is focal child age; the target role is
  `caretaker`. This is separate from the child/baseline atlas and does not use
  context entropy.
- Model ladder prepared:

```text
CM1: sum_bits ~ age_c + effort_c
CM2: CM1 + C(child_id)
CM3: age_c * effort_c + C(child_id)
CM4a: CM3 + preceding_context_effort_c
CM4c: CM3 + C(question_type)
CM5: CM3 + preceding_context_effort_c + C(question_type)
CM6: CM5 + age/context-effort and effort/context-effort interactions
```

- Real-data dyad-balanced smoke fit:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_caretaker_atlas.py \
  --stage smoke-fit \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz \
  --output-dir results/route1_caretaker_atlas/smoke_fit_balanced \
  --context-ks k1,k2,k3 \
  --effort-cols nb_words \
  --model-ids CM1,CM2,CM3,CM4a,CM4c,CM5 \
  --max-rows 5000 \
  --chunksize 250000
```

- Smoke result: `18/18` model rows fit across k1-k3, with 5 dyads and 5,000
  caretaker rows per context window. Output:

```text
results/route1_caretaker_atlas/smoke_fit_balanced/caretaker_smoke_fit_summary.csv
results/route1_caretaker_atlas/smoke_fit_balanced/caretaker_smoke_fixed_effort_predictions.csv
```

- Full preflight audit command:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_caretaker_atlas.py \
  --stage preflight \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz \
  --output-dir results/route1_caretaker_atlas/preflight \
  --context-ks k0,k1,k2,k3 \
  --effort-cols all \
  --model-ids all \
  --max-rows 0 \
  --chunksize 250000
```

- Preflight audit result:

```text
k0: 668,903 rows, 21 children, 2 speakers, 139 sessions, 0 missing age/sum_bits/effort rows
k1: 668,903 rows, 21 children, 2 speakers, 139 sessions, 0 missing age/sum_bits/effort rows
k2: 668,903 rows, 21 children, 2 speakers, 139 sessions, 0 missing age/sum_bits/effort rows
k3: 668,903 rows, 21 children, 2 speakers, 139 sessions, 0 missing age/sum_bits/effort rows
```

- Preflight outputs:

```text
results/route1_caretaker_atlas/preflight/caretaker_context_audit.csv
results/route1_caretaker_atlas/preflight/caretaker_child_context_audit.csv
results/route1_caretaker_atlas/preflight/caretaker_model_manifest.csv
results/route1_caretaker_atlas/preflight/caretaker_model_family_definitions.csv
results/route1_caretaker_atlas/preflight/CARETAKER_FULL_RUN_COMMANDS.md
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_caretaker_atlas
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_corrected_baseline_atlas
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

- Results: focused caretaker tests passed, corrected baseline-atlas tests
  passed, and the full unit suite passed with `295` tests.
- The full caretaker atlas fit was deliberately not launched. Run it after the
  current child/baseline atlas finishes.

## 2026-06-17 - Route 1 corrected fixed-effort Atlas v2 suite completed

- Refit/saved the source-specific child/baseline/LSTM corrected fixed-effort
  atlas artifacts using the extended M1-M15 ladder:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_source_specific_m1_m6_fixed_effort_atlas.py \
  --stage analysis \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \
  --output-dir results/route1_source_specific_corrected_fixed_effort_atlas \
  --fig-dir figs/route1_source_specific_corrected_fixed_effort_atlas \
  --doc-dir docs \
  --sources real,random,unigram,bigram,trigram,lstm_additive_k3_same_length,lstm_additive_k4_same_length,lstm_additive_k5_same_length \
  --context-ks k1,k2,k3 \
  --effort-cols all \
  --model-ids M1,M2,M3,M4a,M4b,M4c,M5,M6,M7,M8,M9,M10,M11,M12,M13,M14,M15 \
  --chunksize 250000 \
  --n-points 60 \
  --no-pdf
```

- Each of the eight source groups wrote:

```text
255 model rows
255 fitted rows
7,095 coefficient rows
183,600 fixed-effort prediction rows
255 plot-manifest rows
510 figure files (PNG + PDF)
```

- Rendered independent Markdown/HTML/PDF Atlas v2 reports plus an index:

```text
docs/utterance_information_route1_real_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_random_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_unigram_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_bigram_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_trigram_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_lstm_additive_k3_same_length_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_lstm_additive_k4_same_length_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_lstm_additive_k5_same_length_corrected_fixed_effort_atlas_v2.{md,html,pdf}
docs/utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.{md,html,pdf}
```

- The real-child report includes the available model-version/estimator
  sensitivity layer and the real-child age-scrambling robustness section. Image
  link audit: 255 image refs per baseline/LSTM report, 325 image refs for the
  real-child report, and 0 missing images.

- Ran the full caretaker/parent atlas:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_caretaker_atlas.py \
  --stage fit-atlas \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz \
  --output-dir results/route1_caretaker_atlas/full_fit \
  --fig-dir figs/route1_caretaker_corrected_fixed_effort_atlas \
  --doc-dir docs \
  --context-ks k0,k1,k2,k3 \
  --effort-cols all \
  --model-ids all \
  --max-rows 0 \
  --chunksize 250000 \
  --n-points 60
```

- Caretaker audit:

```text
140 model rows
120 fitted rows
2,695 coefficient rows
86,400 fixed-effort prediction rows
120 plot-manifest rows
240 figure files (PNG + PDF)
```

- Caretaker reports:

```text
docs/utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.{md,html,pdf}
results/route1_caretaker_atlas/full_fit/reports/caretaker_corrected_fixed_effort_atlas_v2.{md,html,pdf}
```

- Caretaker image link audit: 120 image refs in each report copy and 0 missing
  images.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m py_compile \
  src/build_route1_source_specific_m1_m6_fixed_effort_atlas.py \
  src/build_route1_caretaker_atlas.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_caretaker_atlas
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

- Results: edited builders compile, focused caretaker tests passed, and the
  full suite passed with 295 tests in 291.829 seconds.

## 2026-06-17 - Atlas v2 Reader-Facing HTML/PDF Repair

- Repaired the source-specific and caretaker Atlas v2 report layer after the
  first HTML reports used repo-root-relative image paths that broke when opened
  from `docs/`.
- Regenerated all child/source Atlas v2 reports and the caretaker Atlas v2
  report from saved fit artifacts, without refitting models.
- Report body now starts with model cards and plots: each model section states
  the question, formula, statsmodels formula, regression type, library,
  uncertainty structure, outcome, coverage, and how to read the plots.
- Removed the large in-body formula/coefficient/status/slope tables from the
  reader-facing HTML. Those tables remain available as CSV artifacts under
  `results/route1_source_specific_corrected_fixed_effort_atlas/` and
  `results/route1_caretaker_atlas/full_fit/`.
- Added a caretaker `--stage report` path so future report-only regeneration can
  reuse saved caretaker artifacts:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_caretaker_atlas.py \
  --stage report \
  --output-dir results/route1_caretaker_atlas/full_fit \
  --fig-dir figs/route1_caretaker_corrected_fixed_effort_atlas \
  --doc-dir docs
```

- Regenerated/refreshed HTML and PDF files in `docs/` for real, random,
  unigram, bigram, trigram, LSTM k3/k4/k5, caretaker, and the source-specific
  index. The refreshed full-report PDFs now embed plots and are tens of MB
  rather than the old small broken-image exports.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m py_compile \
  src/build_route1_source_specific_m1_m6_fixed_effort_atlas.py \
  src/build_route1_caretaker_atlas.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_caretaker_atlas
```

- Link/render checks: 2,230 HTML image `src` references, 0 missing files; no
  remaining `figs/...` browser-broken image references in the regenerated
  report Markdown/HTML; headless browser screenshots of the real and caretaker
  HTML show visible plot panels.

## 2026-06-17 Route 1 Atlas v2 Consultation HTML Fix

- Reworked the Route 1 Atlas v2 report layer into model-card, plot-first
  consultation reports: each model section starts with the question, formula,
  fitted statsmodels formula, estimator/library, uncertainty structure,
  outcome, coverage, and then the fixed-effort plots.
- Fixed browser image paths for reports opened from `docs/` by writing image
  links relative to the report file instead of the repository root.
- Added `--embed-images` support to `src/render_markdown_report.py` and
  generated self-contained `.embedded.html` copies for all source-specific and
  caretaker Atlas v2 reports.
- Verification: 10 embedded reports, 2,230 total image references, 2,230
  embedded `data:image/...` sources, 0 non-embedded image links, about 506 MB
  total embedded HTML. Focused caretaker atlas tests passed.

## 2026-06-17 Heldout Real-Child Sum-Bits Rsync

- Found the heldout real-child scoring run on the PC at:

```text
/home/alkan/Portelance/compute_surprisal_mila/results/raw_surprisal_heldout_real_child_generalization_2026-06-16
```

- PC audit passed: 12 scored files, 710,400 total rows, 710,400 finite
  `sum_bits` rows, and 710,400 positive-token rows.
- Rsynced the scored tree back to the laptop/repo-local external-results area:

```text
results/external/compute_surprisal_mila/raw_surprisal_heldout_real_child_generalization_2026-06-16/
```

- Local audit passed with the same totals. Children and per-context rows:
  Forrester/Ella = 6,663 rows per context, Sachs/Naomi = 16,344 rows per
  context, MPI-EVA-Manchester/Helen = 154,593 rows per context, for k0-k3.

## 2026-06-17 Heldout Real-Child Trajectory Prediction Report

- Added `src/build_route1_heldout_real_child_prediction_report.py` for the
  final Route 1 out-of-child robustness check. The report trains PBM real-child
  population and Mundlak-compatible OLS models, then predicts the scored real
  trajectories of heldout Forrester/Ella, Sachs/Naomi, and
  MPI-EVA-Manchester/Helen.
- The report deliberately excludes fixed-effect `C(child_id)` models from the
  main heldout prediction because unseen children do not have fitted child
  intercepts. Entropy-dependent Route 1 models remain parked until heldout
  context-entropy and response-space-entropy predictors are computed.
- Generated report files:

```text
docs/utterance_information_route1_heldout_real_child_prediction_report.md
docs/utterance_information_route1_heldout_real_child_prediction_report.html
docs/utterance_information_route1_heldout_real_child_prediction_report.embedded.html
docs/utterance_information_route1_heldout_real_child_prediction_report.pdf
```

- Generated analysis artifacts:

```text
results/route1_heldout_real_child_prediction/heldout_prediction_fit_summary.csv
results/route1_heldout_real_child_prediction/heldout_prediction_metrics.csv
results/route1_heldout_real_child_prediction/heldout_prediction_monthly.csv.gz
results/route1_heldout_real_child_prediction/heldout_fixed_effort_prediction_grid.csv.gz
results/route1_heldout_real_child_prediction/heldout_fixed_effort_observed_monthly.csv.gz
results/route1_heldout_real_child_prediction/heldout_selection_coverage_rows.csv
figs/route1_heldout_real_child_prediction/
```

- Verification: the builder compiles; full run fit 60 model/context/effort
  combinations and skipped only the 4 impossible k0 context-predictor
  combinations; Markdown has 10 image references with 0 missing files; embedded
  HTML has 10 embedded data images and 0 external figure refs; a headless
  browser screenshot of the HTML shows the coverage plot rendering; PDF export
  wrote a 2.4 MB report.

## 2026-06-17 Supervisor Candidate Report v0

- Added `src/build_supervisor_candidate_report.py`, a selective candidate
  synthesis report for the next supervisor-facing draft. It does not replace
  `docs/predicting_utterance_level_information_report.*`; it is a staging
  report for choosing the cleanest story and plots.
- The report links the current model-card locations, explicitly notes that the
  implemented Atlas v2 ladder is M1-M15 rather than M1-M16, and separates Route
  1 from the email's Route 2 effort-prediction idea.
- New plots generated under `figs/supervisor_candidate_report/`:
  route map, source-specific fixed-effort slope comparison, real k3/word
  model-ladder R2/Delta-R2 importance view, heldout actual-vs-predicted
  regression-line checks, heldout calibration/residual checks, and PBM real-k3
  raw predictor correlation heatmap.
- Key saved tables under `results/supervisor_candidate_report/`: model-card
  appendix rows, effect sentence cards, nested variable-importance table,
  heldout actual-vs-predicted regression slopes, heldout calibration rows,
  source slope comparison, and raw predictor correlations.
- Generated report files:

```text
docs/communicative_efficiency_supervisor_candidate_report_v0.md
docs/communicative_efficiency_supervisor_candidate_report_v0.html
docs/communicative_efficiency_supervisor_candidate_report_v0.embedded.html
docs/communicative_efficiency_supervisor_candidate_report_v0.pdf
```

- Verification: `src/build_supervisor_candidate_report.py` compiles; 6 Markdown
  image refs with 0 missing files; embedded HTML has 6/6 data images and 0
  external figure refs; headless browser screenshot shows the first page and
  main source-slope plot rendering; PDF refreshed from the final HTML.

## 2026-06-18 Route 1 Best-Model Robustness Package Handoff

- Added a new top-priority handoff section to `TODO.md`:
  `Next Priority: Route 1 Best-Model Robustness Package Before Supervisor
  Report`.
- The handoff records that the Atlas is an inventory, not the final story, and
  that the next task should fit/audit the best Route 1 model families before
  updating the supervisor-facing report.
- The section lists the core formulas to fit and plot: M2, M3, M4c, M5,
  M15/rich context-interaction model, nonlinear age model, month-level aggregate
  model, and heldout population prediction model.
- It also lists the estimator families that must be audited or fit beyond OLS:
  OLS with child fixed effects and clustered SE, Gaussian GEE, Gamma/log GEE,
  Gaussian GLM, Gamma/log GLM, MixedLM random child intercept, MixedLM random
  child age slope, nonlinear age variants, aggregate models, and heldout
  prediction models.
- The handoff includes required plots, model-card fields, literal one-line
  effect sentences, existing artifacts to audit before refitting, and acceptance
  criteria for the pre-supervisor candidate evidence report.

## 2026-06-18 Supervisor Candidate Report Figure Explanations

- Updated `src/build_supervisor_candidate_report.py` so each promoted figure in
  `docs/communicative_efficiency_supervisor_candidate_report_v0.md` gets an
  explicit guide with four parts: what the figure shows, how to read it, what it
  means for the Route 1 claim, and what not to overclaim.
- The guide now covers the route map, source-slope comparison, model-ladder
  R2/Delta-R2 plot, heldout actual-vs-predicted regression lines, heldout
  calibration/residual plot, and raw predictor-correlation heatmap.
- Regenerated:

```text
docs/communicative_efficiency_supervisor_candidate_report_v0.md
docs/communicative_efficiency_supervisor_candidate_report_v0.html
docs/communicative_efficiency_supervisor_candidate_report_v0.embedded.html
docs/communicative_efficiency_supervisor_candidate_report_v0.pdf
```

- Added focused tests in `tests/test_build_supervisor_candidate_report.py`.
- Verification:

```bash
.venv/bin/python -m unittest tests.test_build_supervisor_candidate_report
.venv/bin/python -m py_compile src/build_supervisor_candidate_report.py tests/test_build_supervisor_candidate_report.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_supervisor_candidate_report.py
.venv/bin/python -c "from pathlib import Path; import re; md=Path('docs/communicative_efficiency_supervisor_candidate_report_v0.md'); text=md.read_text(encoding='utf-8'); refs=re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text); missing=[]; [missing.append(ref) for ref in refs if not (md.parent / ref).resolve().exists()]; print(f'image_refs={len(refs)} missing={len(missing)}')"
rg -o "data:image/[^;]+;base64" docs/communicative_efficiency_supervisor_candidate_report_v0.embedded.html | wc -l
rg -n "src=\"\\.\\./figs|src=\"figs|\\.png" docs/communicative_efficiency_supervisor_candidate_report_v0.embedded.html
```

- Results: focused unittest passed (`2` tests); `py_compile` passed; report
  rebuild refreshed Markdown, HTML, embedded HTML, and PDF; Markdown audit found
  `image_refs=6 missing=0`; embedded HTML audit found `6` embedded data images
  and no external PNG references.

## 2026-06-18 Route 1 Best-Model Robustness Package

- Added `src/build_route1_best_model_robustness_package.py`, a dedicated
  pre-supervisor evidence-gallery builder for the TODO block covering M2, M3,
  M4c, M5, M15/rich interactions, nonlinear age, month-level aggregation, and
  heldout population prediction evidence.
- The builder reuses the row-level Atlas, deep-dive, source-comparison,
  age-scrambling, heldout, and caretaker artifacts where they already exist,
  then fits the missing month-level aggregate robustness grid for the five core
  formulas across seven estimator families: OLS with child fixed effects and
  child-clustered SE, GEE Gaussian, GEE Gamma/log, GLM Gaussian, GLM Gamma/log,
  MixedLM random child intercept, and MixedLM random child age slope.
- New reusable outputs are under
  `results/route1_best_model_robustness_package/`, including:

```text
aggregate_estimator_family_summary.csv
aggregate_estimator_fixed_effort_predictions.csv
aggregate_ols_fe_nested_r2.csv
estimator_family_coverage.csv
existing_artifact_audit.csv
required_plot_manifest.csv
real_child_k3_month_effort_band_aggregate.csv.gz
```

- New figure outputs are under
  `figs/route1_best_model_robustness_package/`, including same-question
  estimator-family fixed-effort age lines, an estimator-family age-effect
  forest plot, aggregate nested delta-R2, and aggregate actual-vs-predicted
  regression-line checks.
- Generated report files:

```text
docs/route1_best_model_robustness_package.md
docs/route1_best_model_robustness_package.html
docs/route1_best_model_robustness_package.embedded.html
docs/route1_best_model_robustness_package.pdf
```

- The report is explicitly labeled as a pre-supervisor candidate/evidence
  gallery, not the final supervisor report. It includes model cards,
  estimator-family coverage, literal one-line effect interpretations, fixed
  effort age plots, estimator comparisons, coefficient forest plots,
  delta-R2/nested-model plots, actual-vs-predicted plots, heldout calibration,
  age-scrambling robustness, source comparisons, and caretaker contrast plots.
- Important interpretation note: the newly fit month-level aggregate robustness
  models reduce pseudo-replication, but they are not a drop-in replacement for
  the row-level Atlas story. In the aggregate robustness view, the M5 OLS
  child-fixed-effect age coefficient is positive and marginal
  (`0.166` bits/month, `p=0.064`), whereas the row-level fixed-effort Atlas
  remains the main comparable baseline. Treat the aggregate results as a
  sensitivity analysis until the final supervisor report chooses the promoted
  model family.
- Verification commands run:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package
.venv/bin/python -m py_compile src/build_route1_best_model_robustness_package.py tests/test_build_route1_best_model_robustness_package.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_best_model_robustness_package.py
.venv/bin/python -c "from pathlib import Path; import re; md=Path('docs/route1_best_model_robustness_package.md'); text=md.read_text(encoding='utf-8'); refs=re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text); missing=[ref for ref in refs if not (md.parent / ref).resolve().exists()]; print(f'image_refs={len(refs)} missing={len(missing)}')"
rg -o "data:image/[^;]+;base64" docs/route1_best_model_robustness_package.embedded.html
```

- Results: focused unittest passed (`6` tests); `py_compile` passed; the report
  rebuild refreshed Markdown, HTML, embedded HTML, and PDF; Markdown audit found
  `image_refs=18 missing=0`; embedded HTML audit found `18` embedded data
  images and `0` external figure refs; the estimator audit found `35/35`
  aggregate model/estimator fits and the required-plot manifest found `18/18`
  available plots. The report build emitted only non-fatal statsmodels
  FutureWarnings about the GLM BIC deviance formula.

## 2026-06-18 Route 1 Formula-by-Formula Deep-Dive Revision

- Revised `src/build_route1_best_model_robustness_package.py` so
  `docs/route1_best_model_robustness_package.md` is organized one formula at a
  time, with one subsection per estimator family, instead of asking the reader
  to inspect a broad compact grid/table first.
- Added explicit formula variants requested during model-selection discussion:
  `M5_no_question`, `M5_age_effort_no_question`,
  `M5_age_effort_question`, `M5_parent_reaction_no_question`, and
  `M5_parent_reaction_question`.
- Interaction formulas are now written with all lower-order terms visible. For
  example, the report writes `age_c + effort_c + age_c:effort_c` rather than
  Patsy shorthand.
- The report now includes natural-language test sentences for every formula,
  plain-language control descriptions, child-fixed-effect and
  population/random-effect formula versions, a note separating age-effort
  correlation from an actual interaction, variable-importance/R2 diagnostics,
  and term-level interpretations of the relation between each predictor and
  `sum_bits` inside each estimator subsection.
- Added `aggregate_key_term_relation_summary.csv` under
  `results/route1_best_model_robustness_package/` so all term-level
  coefficient, p-value, interval, and direction summaries are reusable without
  putting a long table in the reader-facing report.
- Regenerated:

```text
docs/route1_best_model_robustness_package.md
docs/route1_best_model_robustness_package.html
docs/route1_best_model_robustness_package.embedded.html
docs/route1_best_model_robustness_package.pdf
```

- Verification commands run:

```bash
.venv/bin/python -m py_compile src/build_route1_best_model_robustness_package.py tests/test_build_route1_best_model_robustness_package.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_best_model_robustness_package.py
rg -n "^## |^### |compact aggregate|Aggregate Estimator Fit Summary|Estimator-Family Coverage|age_c \\* effort_c|Natural-language test|Relation between predictors" docs/route1_best_model_robustness_package.md
.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd, re
summary = pd.read_csv('results/route1_best_model_robustness_package/aggregate_estimator_family_summary.csv')
relation = pd.read_csv('results/route1_best_model_robustness_package/aggregate_key_term_relation_summary.csv')
manifest = pd.read_csv('results/route1_best_model_robustness_package/required_plot_manifest.csv')
md = Path('docs/route1_best_model_robustness_package.md')
text = md.read_text(encoding='utf-8')
refs = re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text)
missing = [ref for ref in refs if not (md.parent / ref).resolve().exists()]
print('fit_rows=', int((summary['status']=='fit').sum()), '/', len(summary))
print('relation_rows=', len(relation))
print('plots=', int((manifest['status']=='available').sum()), '/', len(manifest))
print('image_refs=', len(refs), 'missing=', len(missing))
print('formula_sections=', len(re.findall(r'^## (M[0-9A-Za-z_]+)\\.', text, flags=re.M)))
print('estimator_subsections=', len(re.findall(r'^### M.* - ', text, flags=re.M)))
print('has_star_formula=', 'age_c * effort_c' in text)
print('has_compact_aggregate=', 'compact aggregate' in text.lower())
PY
rg -o "data:image/[^;]+;base64" docs/route1_best_model_robustness_package.embedded.html | wc -l
```

- Results: focused unittest passed (`7` tests); `py_compile` passed; report
  rebuild refreshed Markdown, HTML, embedded HTML, and PDF; the rebuilt report
  has `10` formula sections and `70` estimator subsections; estimator coverage
  is `70/70`; term-level relation rows are `329`; the plot manifest is
  `28/28`; Markdown image audit found `image_refs=22 missing=0`; embedded HTML
  contains `22` embedded images; the report contains no `age_c * effort_c`
  shorthand and no old "compact aggregate" language. The report build emitted
  only non-fatal statsmodels FutureWarnings about the GLM BIC deviance formula.

## 2026-06-18 Route 1 Deep-Dive Plot Battery Expansion

- Expanded `src/build_route1_best_model_robustness_package.py` so the
  formula-by-formula report includes the expected plot battery inside the
  model sections, not only at the end of the report.
- For every core/deep-dive formula, the report now includes:
  row-level Atlas fixed-effort plots when an existing Atlas plot is available,
  estimator-family fixed-effort age lines, actual-vs-predicted regression
  plots, estimator residual/calibration summaries, and term-effect forests.
- For every formula-estimator subsection, the report now includes a dedicated
  actual-vs-fitted and residual-over-age diagnostic plot for that exact
  estimator.
- The fitter now saves fitted values/residuals for all estimator families, not
  only OLS:

```text
results/route1_best_model_robustness_package/aggregate_estimator_fitted_values.csv.gz
```

  This file includes all seven estimator families for all ten formulas.
- Regenerated:

```text
docs/route1_best_model_robustness_package.md
docs/route1_best_model_robustness_package.html
docs/route1_best_model_robustness_package.embedded.html
docs/route1_best_model_robustness_package.pdf
```

- Verification commands run:

```bash
.venv/bin/python -m py_compile src/build_route1_best_model_robustness_package.py tests/test_build_route1_best_model_robustness_package.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_best_model_robustness_package.py
brave-browser --headless --no-sandbox --disable-gpu --print-to-pdf=/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/docs/route1_best_model_robustness_package.pdf file:///home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/docs/route1_best_model_robustness_package.html
.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd, re
base = Path('results/route1_best_model_robustness_package')
summary = pd.read_csv(base / 'aggregate_estimator_family_summary.csv')
relation = pd.read_csv(base / 'aggregate_key_term_relation_summary.csv')
manifest = pd.read_csv(base / 'required_plot_manifest.csv')
fitted = pd.read_csv(base / 'aggregate_estimator_fitted_values.csv.gz')
md = Path('docs/route1_best_model_robustness_package.md')
text = md.read_text(encoding='utf-8')
refs = re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text)
missing = [ref for ref in refs if not (md.parent / ref).resolve().exists()]
print('fit_rows=', int((summary['status']=='fit').sum()), '/', len(summary))
print('models=', summary['model_id'].nunique())
print('estimators=', summary['estimator_id'].nunique())
print('fitted_value_rows=', len(fitted), 'fitted_models=', fitted['model_id'].nunique(), 'fitted_estimators=', fitted['estimator_id'].nunique())
print('relation_rows=', len(relation))
print('plots=', int((manifest['status']=='available').sum()), '/', len(manifest))
print('image_refs=', len(refs), 'missing=', len(missing))
print('formula_sections=', len(re.findall(r'^## (M[0-9A-Za-z_]+)\\.', text, flags=re.M)))
print('estimator_subsections=', len(re.findall(r'^### M.* - ', text, flags=re.M)))
print('estimator_diagnostic_reads=', text.count('Estimator diagnostic read'))
print('actual_vs_predicted_reads=', text.count('Actual-vs-predicted read'))
print('residual_calibration_reads=', text.count('Residual/calibration read'))
print('term_forest_reads=', text.count('Predictor-relation read'))
print('has_star_formula=', 'age_c * effort_c' in text)
print('has_compact_aggregate=', 'compact aggregate' in text.lower())
PY
rg -o "data:image/[^;]+;base64" docs/route1_best_model_robustness_package.embedded.html | wc -l
```

- Results: focused unittest passed (`7` tests); `py_compile` passed; report
  rebuild refreshed Markdown, HTML, embedded HTML, and PDF; estimator coverage
  remained `70/70`; fitted-value diagnostics cover `199,353` formula-estimator
  fitted rows, `10` formulas, and `7` estimator families; term-level relation
  rows remained `329`; plot manifest is now `140/140`; Markdown image audit
  found `127` image refs with `0` missing; embedded HTML contains `127`
  embedded images; every one of the `70` estimator subsections has an
  estimator diagnostic read/plot; the report still contains no
  `age_c * effort_c` shorthand and no old "compact aggregate" language. The
  PDF was explicitly re-rendered after detecting a stale timestamp; the final
  PDF is `37,636,121` bytes, `113` pages, and has creation time
  `2026-06-18 08:37:56 EDT`. The report build emitted only non-fatal
  statsmodels FutureWarnings about the GLM BIC deviance formula.

## 2026-06-18 Route 1 Fixed-Effort Report Simplification

- Simplified `docs/route1_best_model_robustness_package.md` after reviewing the
  intended scientific question again. The report now focuses on row-level
  fixed-effort regression-line plots rather than the aggregate estimator
  diagnostic battery.
- The report states the outcome distinction explicitly:
  `sum_bits` is total uncertainty/information in one utterance; effort columns
  are predictors/controls; bits per token such as `sum_bits / nb_words` would
  be a separate rate outcome; `mean_sum_bits` aggregate-cell robustness is not
  the main outcome and not bits per token.
- Included row-level Atlas fixed-effort regression-line plots for M2, M3, M4c,
  M5, M15, and M7. These are the plots tied to the established claim that at
  fixed child effort, predicted total utterance bits generally decrease with
  age after child identity and other controls.
- Included the heldout actual-vs-predicted regression-line plot and calibration
  plot, plus age-scrambling, source-comparison, and caretaker contrast plots.
- Regenerated:

```text
docs/route1_best_model_robustness_package.md
docs/route1_best_model_robustness_package.html
docs/route1_best_model_robustness_package.embedded.html
```

- Verification:

```bash
.venv/bin/python -m py_compile src/build_route1_best_model_robustness_package.py tests/test_build_route1_best_model_robustness_package.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_best_model_robustness_package.py
.venv/bin/python - <<'PY'
from pathlib import Path
import re, pandas as pd
md=Path('docs/route1_best_model_robustness_package.md')
text=md.read_text(encoding='utf-8')
refs=re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text)
missing=[r for r in refs if not (md.parent/r).resolve().exists()]
manifest=pd.read_csv('results/route1_best_model_robustness_package/required_plot_manifest.csv')
print('image_refs=', len(refs), 'missing=', len(missing))
print('plots=', int((manifest.status=='available').sum()), '/', len(manifest))
print('formula_sections=', len(re.findall(r'^## (M[0-9A-Za-z_]+)\\.', text, flags=re.M)))
PY
rg -o "data:image/[^;]+;base64" docs/route1_best_model_robustness_package.embedded.html | wc -l
```

- Results: focused unittest passed (`7` tests); `py_compile` passed; report
  rebuild refreshed Markdown, HTML, and embedded HTML; Markdown audit found
  `13` image refs with `0` missing; plot manifest is `13/13`; embedded HTML
  contains `13` embedded images; the report now has `6` formula sections. PDF
  rendering is temporarily unavailable because both local Chrome and Brave
  crash in Crashpad before writing the PDF in this environment.

## 2026-06-18 Communicative-Efficiency Scope Correction

- Corrected the Route 1 candidate-report framing after user clarified that the
  project is communicative efficiency, not prediction of raw `sum_bits` growth.
  Raw total bits can rise because older children produce longer utterances;
  that is an MLU/length-growth fact and must not be treated as the core
  efficiency result.
- Updated `TODO.md` and this notes file so future agent work starts from the
  correct estimand: conditional utterance information at fixed child effort,
  with controls such as child identity and parent-context effort.
- Regenerated `docs/route1_best_model_robustness_package.md`, `.html`, and
  `.embedded.html` as a focused candidate regression-line gallery.
- The report now states that evidence should come from fixed-effort regression
  lines, not raw observed-vs-fitted total-bit diagnostics. Heldout
  actual-vs-predicted lines remain because those are the requested
  three-heldout-child generalization plots.
- Promising existing M1-M15 candidates shown: M2, M3, M4a, M4c, M5, M6, M7,
  M11, and M15. Exact parent-effort screening candidates shown from existing
  all-estimator artifacts: M5_no_question, M5_age_effort_no_question,
  M5_parent_reaction_no_question, and M5_parent_reaction_question.
- Verification run:

```bash
.venv/bin/python -m py_compile src/build_route1_best_model_robustness_package.py tests/test_build_route1_best_model_robustness_package.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest tests.test_build_route1_best_model_robustness_package
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_best_model_robustness_package.py
```

- Audit result: Markdown has 94 image references with 0 missing; required plot
  manifest is 85/85 available; embedded HTML contains 94 embedded images; the
  report contains 0 references to `aggregate_actual_vs_model_prediction`, 0 raw
  actual-vs-fitted references, 0 `mean_sum_bits` mentions, and explicit
  communicative-efficiency/MLU warnings. PDF rendering remains unavailable in
  this environment because Brave crashes in Crashpad before writing the file.
- Added an explicit "Multiple Age Effects Can Coexist" section to
  `docs/route1_best_model_robustness_package.md`: M1 pooled effort-only
  contrast, M2 child-identity contrast, and M3 age-by-effort contrast. The
  report now shows M1 fixed-effort lines plus M1/M2/M3 balanced/scrambled
  robustness lines. Key k3 word-effort values: row-level M1 is essentially
  flat/slightly upward (age coefficient 0.0003 bits/month, p=0.993), the
  age-bin/unit robustness M1 slope is positive (0.0542), and child-controlled
  M2/M3 remain downward. Rebuilt Markdown/HTML/embedded HTML; verified 100
  Markdown image references with 0 missing and 9 focused tests passing.

## 2026-06-20 Route 1 Child-Only Length-Controlled Model Suite

- Added `src/build_route1_child_length_controlled_model_suite.py` with decoupled
  `fit`, `plot`, `report`, and `all` stages, plus focused tests in
  `tests/test_build_route1_child_length_controlled_model_suite.py`.
- The suite is child-only by default and enforces the Route 1 length contract:
  every scientific formula includes either `effort_c` or exact word-count
  categories with `C(effort_value_int)`. Interactions are written with explicit
  lower-order terms, not formula shorthand.
- Added exact-length F18-F21 formulas to directly address the MLU concern:
  F18 absorbs exact word-count categories, F19 estimates separate age slopes
  inside each exact word count, F20 adds local-context controls, and F21
  combines exact-length age slopes with local-context controls. These models
  test developmental change within same-length utterance comparisons rather
  than across the changing age distribution of utterance lengths.
- Default real-child run used K3 context and word effort:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_child_length_controlled_model_suite.py \
  --stage all \
  --context-ks k3 \
  --effort-cols nb_words \
  --formula-ids all \
  --estimators all \
  --n-points 60
```

- Outputs:

```text
docs/route1_child_length_controlled_model_suite.md
docs/route1_child_length_controlled_model_suite.html
results/route1_child_length_controlled_model_suite/model_summary.csv
results/route1_child_length_controlled_model_suite/coefficient_long.csv
results/route1_child_length_controlled_model_suite/fixed_effort_predictions.csv.gz
results/route1_child_length_controlled_model_suite/fixed_slice_slopes.csv
results/route1_child_length_controlled_model_suite/exact_length_observed_age_bin_means.csv
results/route1_child_length_controlled_model_suite/formula_definitions.csv
results/route1_child_length_controlled_model_suite/estimator_definitions.csv
results/route1_child_length_controlled_model_suite/models/
figs/route1_child_length_controlled_model_suite/
```

- Fit audit: `446,985` real-child K3 rows, `21` children, `983` child-session
  keys. The model grid fit `189/189` requested combinations: 21 formulas x 9
  estimators/repeated-measures structures. All 189 fitted result objects were
  saved as pickle files with zero model-save errors.
- Figure/report audit: generated `47` PNG figures: 21 primary fixed-effort or
  exact-length line plots, 21 estimator-comparison fixed-effort line plots, one
  exact-length age-slope proof plot, one observed exact-length age-bin plot,
  one slope heatmap, one variance-explained plot, and one control-dominance
  standardized-coefficient diagnostic plot.
- Scientific signal in this run: fixed-effort slopes are mostly downward. The
  saved slope grid has `2,119` downward and `149` upward fixed-effort/exact-
  length lines overall. For the primary row-level OLS child-fixed-effect
  estimator, all F01-F17 continuous-effort slices were downward. The exact-
  length F18-F21 primary slopes were `41` downward and `7` upward; lengths
  `1-7` are consistently downward in the exact-length interaction formulas,
  while positive slopes at `8` and `10-12` should be interpreted cautiously
  because the longest lengths have much thinner support.
- Exact-length support audit from
  `exact_length_observed_age_bin_means.csv`: lengths 1-7 each have thousands
  of observed utterances and all 21 children represented; length 8 still has
  4,725 utterances and 20 children; lengths 10-12 are sparse by comparison
  and include small age-bin cells, so the report flags them as support-limited.
- The variance-explained figure uses squared observed-vs-fitted correlation as
  a bounded descriptive fit metric across OLS/GLM/GEE/MixedLM families. This
  avoids letting Gamma/log SSE-scale pseudo-R2 dominate the diagnostic plot.
- The standardized-coefficient plot was reframed as a control-dominance
  diagnostic. Large effort coefficients show why raw total bits are length-
  confounded; they are not presented as the communicative-efficiency finding.
- Regenerated `docs/route1_child_length_controlled_model_suite.md` and `.html`
  without course-label phrasing. The report now has an explicit "Why This Is
  Not Just MLU" section, 47 Markdown image references with zero missing files,
  and no occurrences of the removed phrase in the Markdown or HTML.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m py_compile \
  src/build_route1_child_length_controlled_model_suite.py \
  tests/test_build_route1_child_length_controlled_model_suite.py
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest \
  tests.test_build_route1_child_length_controlled_model_suite
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_child_length_controlled_model_suite.py \
  --stage all \
  --context-ks k3 \
  --effort-cols nb_words \
  --formula-ids all \
  --estimators all \
  --n-points 60
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_route1_child_length_controlled_model_suite.py --stage report
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python -m unittest discover -s tests
```

- Results: py_compile passed; focused tests passed (`7` tests). The full model
  run completed with `189/189` fits and zero model-save errors. The report-only
  regeneration completed after the final wording patch. Full unit suite passed
  `313` tests in `281.326` seconds. Existing statsmodels smoke tests still emit
  convergence, perfect-separation, and plotting warnings on tiny synthetic data,
  but the test suite completed successfully.

## 2026-06-22 - Route 1 phoneme fixed-effort line audit

- Added a small audit confirming the current real-child corrected
  source-specific Atlas uses the requested phoneme fixed-effort selection
  logic: the 12 most frequent exact real-child phoneme counts.
- Current real-child phoneme values are `2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
  13`, split in the Atlas as low `2-5`, middle `6-9`, and high `10-13`.
- Outputs:

```text
docs/route1_phoneme_effort_line_audit.md
docs/route1_phoneme_effort_line_audit.html
results/route1_phoneme_effort_line_audit/real_phoneme_effort_value_distribution_with_top12.csv
results/route1_phoneme_effort_line_audit/real_current_atlas_phoneme_bin_definitions.csv
results/route1_phoneme_effort_line_audit/real_k3_main_model_phoneme_fixed_effort_slopes.csv
figs/route1_phoneme_effort_line_audit/real_phoneme_top12_frequency_audit.png
figs/route1_phoneme_effort_line_audit/real_k3_phoneme_main_model_slope_audit.png
```

- Verification: inspected
  `src/build_route1_source_specific_m1_m6_fixed_effort_atlas.py` and the saved
  `fixed_effort_bin_definitions.csv`; rendered the audit Markdown to HTML; used
  `view_image` to visually confirm both generated PNGs are nonblank and legible.

## 2026-06-22 - Route 1 real-vs-controls context report

- Added `src/build_route1_real_vs_controls_context_report.py` and
  `tests/test_build_route1_real_vs_controls_context_report.py` to build and
  guard a comparison-first report opposing real child utterances against random,
  unigram, bigram, trigram, additive same-length LSTM k3/k4/k5, and caretaker
  speech over the same PBM developmental period.
- The report uses k0 as the no-context quantity and k3 as the with-context
  quantity. For generated child controls, source gaps are paired by
  `utterance_id`; caretaker comparisons are age/session-structure comparisons
  rather than utterance-paired alternatives.
- Generated sections for Real vs Random, Real vs Unigram, Real vs Bigram, Real
  vs Trigram, Real vs LSTMs, and Real vs Caretakers. Each section includes four
  plots: k0 versus k3 age means, k3 with-context focus, context gain through
  age, and source-minus-real gap through age.
- Fitted difference models for generated controls:
  `gap_k3 ~ age_c + effort_c + C(child_id)` and
  `gain_gap ~ age_c + effort_c + C(child_id)`, with child-clustered standard
  errors. Fitted caretaker source-interaction models for `sum_bits_k3` and
  `context_gain`.
- Retrieved illustrative matched examples for generated controls where the
  real child utterance had much lower k3 surprisal than the generated
  alternative under the same prior context. Caretaker examples are labeled as
  representative context-gain examples because they are not generated
  alternatives for the same child row.
- Outputs:

```text
docs/route1_real_vs_controls_context_report.md
docs/route1_real_vs_controls_context_report.html
docs/route1_real_vs_controls_context_report.embedded.html
results/route1_real_vs_controls_context_report/source_age_summary.csv
results/route1_real_vs_controls_context_report/paired_gap_summary.csv
results/route1_real_vs_controls_context_report/difference_model_summary.csv
results/route1_real_vs_controls_context_report/matched_examples.csv
results/route1_real_vs_controls_context_report/caretaker_examples.csv
figs/route1_real_vs_controls_context_report/
```

- Added the report to `docs/route1_current_reports_browser_index.html`.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m py_compile \
  src/build_route1_real_vs_controls_context_report.py \
  tests/test_build_route1_real_vs_controls_context_report.py
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m unittest \
  tests.test_build_route1_real_vs_controls_context_report
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_route1_real_vs_controls_context_report.py --stage all
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_route1_real_vs_controls_context_report.py --stage report
```

- Results: `py_compile` passed, the focused unittest passed (`4` tests), the
  full report build completed, the final report-only regeneration completed
  after fixing report-relative figure paths, and the Markdown audit found 24
  image references with 0 missing files.

## 2026-06-22 - Real-vs-controls regression-line expansion

- Expanded `docs/route1_real_vs_controls_context_report.md`/`.html` with a
  model-based fixed-effort regression-line layer. This addresses the missing
  difference-in-regression-lines evidence: the report now shows not only raw
  k0/k3 age-bin means, but also Atlas-predicted k3 lines at the same word
  counts.
- The primary regression-line plots use the saved corrected fixed-effort Atlas
  `M2` predictions for child sources and `CM2` for caretakers at fixed 2-, 6-,
  and 10-word utterances. Each comparison section now includes the source and
  real regression lines, source-minus-real predicted line gaps, and slope
  differences across model variants.
- Added slope-difference tables and plain-language M2/CM2 slope reads. Example:
  the random comparison reports real children at `-0.735` bits per 6 months
  versus random at `+1.068` bits per 6 months, with real `12/12` downward fixed
  word-count lines and random `0/12`.
- Model-slope comparisons use average bits per 6 months across the 12 fixed
  word-count lines for `M2`, `M3`, `M4c`, `M5`, `M6`, `M7`, `M11`, and `M15`
  where available. Caretakers use the available mapped `CM2`, `CM3`, `CM4c`,
  `CM5`, and `CM6` variants.
- Additional outputs:

```text
results/route1_real_vs_controls_context_report/regression_line_slope_difference_summary.csv
results/route1_real_vs_controls_context_report/*_regression_line_predictions.csv
results/route1_real_vs_controls_context_report/*_regression_line_slopes.csv
results/route1_real_vs_controls_context_report/*_regression_line_slope_differences.csv
results/route1_real_vs_controls_context_report/*_regression_line_gaps.csv
figs/route1_real_vs_controls_context_report/*_m2_k3_fixed_word_regression_lines.png
figs/route1_real_vs_controls_context_report/*_m2_k3_fixed_word_regression_gaps.png
figs/route1_real_vs_controls_context_report/*_k3_word_model_slope_differences.png
```

- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_route1_real_vs_controls_context_report.py --stage report
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m py_compile \
  src/build_route1_real_vs_controls_context_report.py \
  tests/test_build_route1_real_vs_controls_context_report.py
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m unittest \
  tests.test_build_route1_real_vs_controls_context_report
```

- Results: report-only regeneration completed; focused unittest passed (`6`
  tests); Markdown image audit found 42 image references with 0 missing files.
  Visually inspected the random fixed-effort regression-line and model-slope
  difference plots.

## 2026-06-22 - Side draft proposed supervisor-report completion

- Added `src/build_supervisor_proposed_completion_report.py` to generate a
  separate proposed completion beside the current supervisor-facing report. The
  builder reads `docs/predicting_utterance_level_information_report.md` as the
  base but writes only new side-draft outputs:

```text
docs/predicting_utterance_level_information_report_proposed_completion.md
docs/predicting_utterance_level_information_report_proposed_completion.html
docs/predicting_utterance_level_information_report_proposed_completion.embedded.html
```

- The current `docs/predicting_utterance_level_information_report.*` files were
  intentionally left unchanged.
- The side draft adds a proposed completion section summarizing
  real-vs-random, real-vs-ngram, real-vs-LSTM, and real-vs-caretaker evidence,
  including row-weighted k0/k3/context-gain means, primary fixed-effort slope
  comparisons, paired generated-control gap models, caretaker interaction
  results, and candidate promoted figures.
- Added the side draft to `docs/route1_current_reports_browser_index.html` and
  added focused tests in
  `tests/test_build_supervisor_proposed_completion_report.py`.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m py_compile \
  src/build_supervisor_proposed_completion_report.py \
  tests/test_build_supervisor_proposed_completion_report.py
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m unittest \
  tests.test_build_supervisor_proposed_completion_report
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_supervisor_proposed_completion_report.py
```

- Results: `py_compile` passed; focused unittest passed (`4` tests); side-draft
  regeneration completed; Markdown image audit found 18 image references with 0
  missing files; `git diff` confirmed no changes to the current supervisor
  report Markdown/HTML/embedded HTML files.

## 2026-06-22 - Supervisor proposed-completion v2 correction

- Replaced the weak proposed-completion side draft with a model-rich v2 while
  keeping the original supervisor-facing report untouched:

```text
docs/predicting_utterance_level_information_report.md
docs/predicting_utterance_level_information_report.html
docs/predicting_utterance_level_information_report.embedded.html
```

- Regenerated only the side-draft outputs:

```text
docs/predicting_utterance_level_information_report_proposed_completion.md
docs/predicting_utterance_level_information_report_proposed_completion.html
docs/predicting_utterance_level_information_report_proposed_completion.embedded.html
```

- The v2 side draft now includes the real-child k3/word model ladder, the
  F01-F21 length-controlled suite, exact-length MLU proof figures, estimator
  family checks, age-scrambling robustness, source-specific real-vs-random /
  unigram / bigram / trigram / LSTM / caretaker panels, source-specific Atlas
  figures, paired source-gap models, caretaker contrasts, and heldout-child
  diagnostics.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m py_compile \
  src/build_supervisor_proposed_completion_report.py \
  tests/test_build_supervisor_proposed_completion_report.py
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m unittest \
  tests.test_build_supervisor_proposed_completion_report
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_supervisor_proposed_completion_report.py
```

- Results: `py_compile` passed; focused unittest passed (`4` tests);
  regeneration completed; Markdown image audit found `70` image references with
  `0` missing files; `git diff` confirmed no changes to the current supervisor
  report Markdown/HTML/embedded HTML files.

## 2026-06-22 - Exhaustive ANCOVA group-comparison gallery

- Added `src/build_route1_exhaustive_ancova_gallery.py` and
  `tests/test_build_route1_exhaustive_ancova_gallery.py`.
- Built a figure-first pre-supervisor selection gallery that compares real
  children, generated baselines, LSTM baselines, and caretakers with ANCOVA-
  style adjusted group comparisons across five effort scales: words,
  morphemes, CMU/pkg syllables, package syllables, and phonemes.
- The report is intentionally organized with figures first and audit tables
  second:

```text
docs/route1_exhaustive_ancova_gallery.md
docs/route1_exhaustive_ancova_gallery.html
docs/route1_exhaustive_ancova_gallery.embedded.html
figs/route1_exhaustive_ancova_gallery/
```

- Reusable outputs for future plotting:

```text
results/route1_exhaustive_ancova_gallery/effort_cell_summary.csv.gz
results/route1_exhaustive_ancova_gallery/effort_cell_summary_nb_words.csv.gz
results/route1_exhaustive_ancova_gallery/effort_cell_summary_nb_morphemes.csv.gz
results/route1_exhaustive_ancova_gallery/effort_cell_summary_nb_syllables_cmu_or_pkg.csv.gz
results/route1_exhaustive_ancova_gallery/effort_cell_summary_nb_syllables_pkg.csv.gz
results/route1_exhaustive_ancova_gallery/effort_cell_summary_nb_phonemes.csv.gz
results/route1_exhaustive_ancova_gallery/ancova_term_tests.csv
results/route1_exhaustive_ancova_gallery/adjusted_marginal_means.csv
results/route1_exhaustive_ancova_gallery/source_real_adjusted_contrasts.csv
results/route1_exhaustive_ancova_gallery/top_exact_effort_values.csv
results/route1_exhaustive_ancova_gallery/exact_effort_adjusted_means.csv
results/route1_exhaustive_ancova_gallery/exact_effort_source_real_gaps.csv
results/route1_exhaustive_ancova_gallery/figure_manifest.csv
```

- Output sizes/shapes: aggregate effort cells `704,488` rows; ANCOVA term tests
  `580` rows; adjusted marginal means `2,000` rows; source-real contrasts `640`
  rows; exact-effort adjusted means `960` rows; exact-effort source-real gaps
  `7,680` rows; figure manifest `33` PNGs.
- Added the report to `docs/route1_current_reports_browser_index.html`.
- The report includes a note from the frequency/informativity CDS paper: age-bin
  ANOVA-style evidence is useful, but frequency and sampling confounds should
  be explicit, so this gallery is designed for later frequency-control model
  passes rather than overclaiming from raw age/source differences.
- Revised the gallery after review so the report now explains the ANCOVA logic
  before the figure gallery and adds plot-level reading cards. Each figure now
  states what is controlled, how to read the visual, and what the current model
  says. The main text explicitly separates the Route 1 child-output claim
  (children's own utterances become less unpredictable at fixed effort) from
  the copied paper's caregiver/CDS phonological-informativity claim. Added a
  dedicated real-child-vs-caretaker adjusted section with k3 and context-gain
  panels.
- Main reported evidence in the revised gallery: real-child adjusted k3 bits
  decline by `-5.46` to `-3.19` bits from first to last age bin across effort
  scales, with fitted slopes `-0.62` to `-0.29` bits per six months. Exact-
  effort checks show `51/60` top-exact-effort slopes downward.
- Follow-up clarification: regenerated source-minus-real line plots with titles
  and y-axis labels that explicitly say these are bits above/below real child
  utterances. The report now includes a source-comparison reading note: real
  child utterances are the `0` reference line, and colored lines are adjusted
  source-minus-real contrasts rather than raw surprisal curves.

## 2026-06-22 - Frequency/informativity predictor layer

- Added `src/build_route1_frequency_informativity_predictors.py` and
  `tests/test_build_route1_frequency_informativity_predictors.py`.
- Scaffolded text-level lexical/phone frequency and phone-bigram informativity
  predictors keyed by `target_text_hash`. The full text-column pass is not run
  yet because pandas' C parser segfaulted on the large scored text CSV in this
  environment, while the Python parser was too slow for a full text pass.
- Computed the safe first frequency-control layer without reading the text
  column, using standard-library `gzip`/`csv` streaming:

```text
results/route1_frequency_informativity_predictors/hash_frequency_predictors.csv.gz
results/route1_frequency_informativity_predictors/hash_frequency_predictor_dictionary.csv
results/route1_frequency_informativity_predictors/source_age_scoring_row_counts.csv
```

- `hash_frequency_predictors.csv.gz` has `5,447,310` rows: each target text hash
  scored under caretaker-CDS, real-child, and combined real-plus-caretaker
  reference scopes. Predictors are `exact_target_frequency` and smoothed
  `exact_target_frequency_bits`.
- Verification:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m py_compile \
  src/build_route1_exhaustive_ancova_gallery.py \
  src/build_route1_frequency_informativity_predictors.py \
  tests/test_build_route1_exhaustive_ancova_gallery.py \
  tests/test_build_route1_frequency_informativity_predictors.py
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m unittest \
  tests.test_build_route1_exhaustive_ancova_gallery \
  tests.test_build_route1_frequency_informativity_predictors
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_route1_exhaustive_ancova_gallery.py --stage all
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_route1_exhaustive_ancova_gallery.py --stage report
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python \
  src/build_route1_frequency_informativity_predictors.py --mode hash-only --chunksize 1000000
```

- Results: focused tests passed (`9` tests); report regeneration completed;
  Markdown image audit found `33` image references with `0` missing files; the
  safe hash-frequency predictor build completed.
- Additional 2026-06-22 verification after the explanatory-gallery revision:
  focused tests passed again (`9` tests), and the Markdown image audit again
  found `33` image references with `0` missing files.
