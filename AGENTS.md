# AGENTS.md

Persistent guidance for coding agents working in this repository.

This file is the high-level project compass. Lower-level tasks belong in
`TODO.md`; longer design discussion belongs in `docs/design.md`; running notes
and decisions belong in `docs/notes.md`.

## Project Overview

Working title: **On Communicative Efficiency of Child Language Use**

This repository is the local **brain, analysis, and reporting repository** for
the project. It owns CHILDES / CHAT preparation and cleaning, scorer-ready
bundles, analysis-ready tables, statistical models, diagnostics, metadata,
plots, and supervisor-facing reports.

This repository is **not** the main place for large-scale LLM surprisal
scoring. Direct Mistral scoring and HPC audits belong in the sibling
`compute_surprisal_mila` repository. Baseline generation, Bayes-decomposition
execution, and complexity extraction also have lightweight sibling execution
repositories. This repo receives compact, audited products from them and owns
the scientific synthesis. Large outputs remain outside Git.

Broad scientific objects:

- **informativeness**: direct contextual Mistral surprisal `p(u | c)`,
  unconditional utterance priors `p(u)`, and exploratory Bayes-decomposition
  scores based on `p(u) p(c | u)`.
- **effort / complexity**: utterance length, morphemes, syllables, MLU-style
  measures, phoneme proxies, lexical trajectories, and related diagnostics.
- **efficiency**: currently studied through two complementary questions:
  information at fixed production effort, and production effort relative to
  contextual predictability / a generated response space.

Do not equate lower surprisal, higher surprisal, shorter speech, or longer
speech with communicative efficiency in isolation. State the estimand and
controls explicitly. In particular, the current negative fixed-effort age
slope means that older children's utterances are more predictable to Mistral at
the same measured effort; it is not by itself proof of a single normative
efficiency optimum.

## Current Active Data And Analysis State

Status verified locally on 2026-07-13.

Primary external scored/feature handoffs:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023
results/external/compute_surprisal_mila/raw_surprisal_lstm_additive_same_length
results/external/compute_surprisal_mila/context_entropy_mistral
results/external/compute_surprisal_mila/raw_surprisal_heldout_real_child_generalization_2026-06-16
```

These are symlinks into:

```text
/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/
```

Use these paths for PBM analyses. Do not copy the multi-GB scored trees into
Git. Prefer
`raw_surprisal_cleaned_mistral_patched_006_023` for new analyses: it is a
complete PBM scored tree where the 006-023 generated-baseline patch has been
merged into the main cleaned Mistral results. New Mila products should be
symlinked here only after they have been rsynced locally and passed audits in
`compute_surprisal_mila`.

Current strict naturalistic big-cleaned bundle:

```text
data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

This bundle uses additive random/unigram/bigram/trigram dictionaries with one
first bin `006-023`, followed by 6-month bins:

```text
024-029, 030-035, 036-041, 042-047, 048-053, 054-059, 060-065
```

Strict naturalistic corpora in the current bundle:

- Belfast
- Brown
- Demetras1
- Forrester
- Kuczaj
- Lara
- MPI-EVA-Manchester
- Manchester
- Post
- Providence
- Sachs
- Weist
- Wells

Generated/scoring-ready row counts for this current bundle:

- 79 child folders
- 1,140,218 child scoring rows
- 1,470,154 caretaker scoring rows

The full 79-child bundle is prepared, but it is **not yet fully scored with
Mistral**. The 2026-07-13 `compute_surprisal_mila` production contract targets
79 children x 6 modes x 4 contexts = 1,896 scored CSVs. Its audit found 167
reusable real/caretaker files and 1,729 files requiring new or replacement
scoring. The benchmark-gated scorer and production DAG are implemented, but a
successful Mila benchmark and final `COMPLETE_AND_AUDITED` production marker
have not yet been retrieved locally. Do not describe the 79-child Mistral run
as complete.

The current main analysis products remain PBM-scoped (Brown, Manchester, and
Providence: 21 children):

```text
results/route1_analysis_dataset/
results/route2_response_space/
results/route2_response_space_analysis/
results/existing_scored_baseline_efficiency_cloud/
```

Important current facts:

- the Route 1 long table includes real child, random, unigram, bigram,
  trigram, and additive same-length LSTM k3/k4/k5 targets scored by Mistral;
- PBM additive LSTM generation and scoring are complete; they are no longer a
  merely planned baseline;
- the production response-space run contains 268,712 unique k3 caregiver
  contexts and 26,871,200 selected samples (100 per context), with 176
  incomplete/fallback settings retained as audit flags;
- the local Route 2 table covers about 444k PBM child utterances, not all 79
  children, and generated responses have not yet been scored for a full
  information-effort cloud;
- July modular-repo products are under
  `results/mila_modular_runs_2026_07_08/products/`: PBM n-gram Bayes scores and
  PBM complexity predictors have passed their recorded join audits;
- Bayes values are unnormalized decomposition scores because `p(c)` has not
  been estimated. They are most defensible for same-context candidate
  comparisons and must not be labeled as normalized posterior surprisal.

Move real data, generated utterances, model checkpoints, and scored outputs
between machines with `rsync` or Globus, never Git.

## Current Reporting State

Current supervisor-facing utterance-information report:

```text
docs/predicting_utterance_level_information_report.md
docs/predicting_utterance_level_information_report.html
```

Before editing this report, always reread the current Markdown file because the
user may be editing it manually between agent turns. Keep the report
supervisor-facing: avoid implementation paths, repo workflow details, and
internal labels such as "Route 1" in the report body.

The report is still a June working draft centered on the 21-child PBM sample.
Its prose saying that LSTM scoring and response sampling are still planned is
stale; verify all status language against the artifacts above before editing.
The newest working evidence has not yet been fully promoted into that report:

```text
docs/new_efforts_report_index.html
docs/developmental_onset_working_report.md
docs/bayes_information_working_report.md
docs/new_efforts_complexity_metrics.md
docs/communicative_efficiency_supervisor_candidate_report_v0.md
```

The clearest current PBM finding is a negative child-controlled, fixed-effort
Mistral age slope. The onset report estimates the first age-bin decrease by
`024-029`, but its child-age-cell sensitivity changes the sign/weighting and
child-bootstrap intervals are still pending. Keep this caveat visible; do not
promote an exact developmental onset as settled.

## Current Scientific And Compute Focus

Priorities as of 2026-07-13:

1. Run and audit the benchmark-gated 79-child Mistral production pipeline in
   `compute_surprisal_mila`; retrieve only compact reports first.
2. Add child-level bootstrap intervals to the developmental-onset analysis and
   repeat onset timing with word, morpheme, syllable, and phoneme effort
   controls before supervisor-facing promotion.
3. Reconcile the main supervisor report with the completed LSTM,
   response-space, Bayes, and complexity work; keep working and final claims
   clearly separated.
4. Validate the Bayes decomposition under alternative training scopes and
   likelihood estimators. Keep the current n-gram result exploratory until the
   normalizer/conditioning language and robustness are locked.
5. Extend complexity validation for CHAT morphology, phonological proxies,
   lexical diversity, and dependency feasibility before treating them as
   primary controls.
6. If the full response-cloud question remains a priority, create a compact
   scoring bundle for sampled responses, score it on Mila, and distinguish
   Mistral-generated/Mistral-scored self-reference from decoupled generators.
7. Use SES, race/ethnicity, parental education, sex/gender, or nationality only
   with explicit metadata-level provenance. Current coverage is too sparse for
   most of these to serve as general covariates.

The legacy in-repo LSTM implementation remains useful for audits and local CPU
smokes, but real new training belongs on Mila. The execution-oriented baseline
repo is now:

```text
/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila
```

For an LSTM task, read these first:

1. `docs/lstm-baseline-pipeline.md`
2. `configs/lstm_baseline_16gb_smoke.json`
3. `configs/lstm_baseline_16gb_default.json`
4. `configs/lstm_baseline_16gb_pbm_additive.json`
5. `src/run_lstm_baseline_pipeline.py`
6. `src/generate_lstm_utterances.py`
7. `tests/test_lstm_baseline_pipeline.py`
8. `tests/test_lstm_generation.py`

The LSTM pipeline:

- trains a small word-level encoder-decoder LSTM;
- trains one model per additive age bin by default, matching the developmental
  information constraints used by the random/unigram/bigram/trigram baselines;
- encodes bounded prior caretaker context;
- decodes child-like utterance baselines;
- supports same-length and free-length generation variants;
- writes generated LSTM sibling files and compact scoring-ready files;
- does not compute LLM surprisal.

Do not claim that a new LSTM was trained unless a real training command was run
and its checkpoints, vocabulary, manifest, and audits exist. Do not rerun the
completed PBM proof-of-concept merely because older documentation calls it
"planned."

## Repository Map

```text
communicative_efficiency/
|-- AGENTS.md
|-- TODO.md
|-- configs/
|   |-- lstm_baseline_16gb_default.json
|   |-- lstm_baseline_16gb_pbm_additive.json
|   `-- response_entropy_pilot_grid.json
|-- data/                  # ignored by Git; transfer with rsync/Globus
|-- docs/
|   |-- design.md
|   |-- notes.md
|   |-- predicting_utterance_level_information_report.md
|   |-- developmental_onset_working_report.md
|   `-- bayes_information_working_report.md
|-- figs/                  # ignored by Git unless explicitly needed elsewhere
|-- results/               # ignored by Git; generated outputs and bundles
|-- src/
|-- tests/
|-- scripts/
`-- notebooks/
```

## Important Source Files

- `src/prepare_datasets.py`: Stage 0 CHAT / CHILDES preprocessing.
- `src/create_big_cleaned_dataset.py`: consolidated strict-naturalistic bundle
  creation.
- `src/build_age_word_dicts.py`: additive age-binned vocabulary and count
  dictionaries.
- `src/add_random_and_unigram_utterances.py`: matched-length random, unigram,
  bigram, and trigram baseline utterance generation.
- `src/create_shared_caretaker_contexts.py`: role-specific caretaker context
  windows, currently `context_k1`, `context_k2`, `context_k3`.
- `src/create_minimal_surprisal_scoring_csvs.py`: compact child/caretaker
  scoring-ready CSVs.
- `src/create_pbm_early_baseline_rescoring_bundle.py`: PBM-only `006-023`
  generated-baseline handoff bundle for Mila rescoring.
- `src/generate_lstm_utterances.py`: word-level LSTM model code.
- `src/run_lstm_baseline_pipeline.py`: config-driven LSTM orchestration.
- `src/build_route1_analysis_dataset.py`: audited PBM scored/effort long table.
- `src/build_route1_model_report_suite.py`: core Route 1 model/report suite.
- `src/build_route2_response_space_table.py`: joins real child rows to response
  entropy and generated-response effort summaries.
- `src/build_response_space_analysis_suite.py`: Route 1/Route 2 response-space
  estimator suite.
- `src/build_route2_relative_effort_model_suite.py`: child effort relative to
  the generated response-space models.
- `src/build_existing_scored_baseline_efficiency_cloud.py`: common-Mistral
  real/n-gram/LSTM information-effort cloud.
- `src/build_developmental_onset_report.py`: current onset and change-point
  working analyses.
- `src/build_bayes_information_report.py`: joins and audits Bayes, complexity,
  and direct Mistral products.
- `src/plot_distributions.py`: distribution plots and summaries.

Sibling execution repositories:

- `compute_surprisal_mila`: direct Mistral scoring, Slurm, and scoring audits;
- `generate_baselines_mila`: manifest-driven n-gram and LSTM generation;
- `bayes_efficiency_mila`: n-gram and future neural Bayes components;
- `child_complexity_predictors`: complexity and lexical trajectories.

## Data And Git Policy

Large data and generated outputs should not be pushed to Git.

Ignored by `.gitignore`:

- `data/`
- `results/`
- `figs/`
- generated PDFs/images under docs
- archives and tarballs
- model checkpoints
- local environments and caches

Use `rsync` or Globus for machine-to-machine data transfer. Use Git for:

- source code
- tests
- configs
- Markdown documentation
- lightweight project metadata

Important: if bulky files were already tracked before `.gitignore` was updated,
they must be removed from the Git index with `git rm --cached`; do not delete
local data unless explicitly asked.

## How Agents Should Work Here

Before editing code:

1. Read this file.
2. Read `TODO.md`.
3. Read relevant docs under `docs/`.
4. Inspect directly involved source files and tests.

Default behavior:

- Make small, reviewable changes.
- Preserve raw data.
- Preserve row provenance wherever possible.
- Add or update tests for behavior changes.
- Prefer simple, explicit code over clever abstractions.
- Keep documentation synchronized when changing file formats or assumptions.
- After meaningful work, update `TODO.md` and `docs/notes.md` with dates,
  commands, outputs, and verification.
- Do not simplify scientific designs for convenience. If the requested analysis
  requires matched developmental information constraints, additive age bins,
  separate train/generate scopes, or other statistically important structure,
  implement that structure with tests or explicitly stop and explain the
  scientific tradeoff before coding.
- Treat this as senior-engineer research software for a PhD project: exhaustive
  tests, transparent provenance, and methods-level documentation are part of the
  deliverable, not optional polish.

## Testing

Current full unit-test command:

```bash
.venv/bin/python -m unittest discover -s tests
```

If `uv` is available, this also works:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

Do not copy an old test count into new notes. Record the command, date, pass
count, and any expected warnings from the test run actually performed.

Latest full-suite verification on 2026-07-13: 370 tests passed in 248 seconds.
The suite emitted Statsmodels convergence, perfect-separation, singular-fit,
and small-fixture numerical warnings but no test failures. Treat model-fit
warnings in production analyses as audit items even when unit tests allow them.

## Project-Specific Constraints

- Do not overwrite raw CHILDES / CHAT data.
- Do not silently drop utterance rows without recording why.
- Do not invent scientific results or pretend a model was run.
- Do not call the 79-child Mistral expansion complete without its final audit
  marker and retrieved report.
- Do not generalize PBM (21-child, 3-corpus) analyses to the full 79-child,
  13-corpus bundle without a new scored analysis.
- Do not describe response-space samples as same-meaning paraphrases.
- Do not describe Mistral response entropy as model-independent behavioral
  uncertainty.
- Do not describe the current Bayes score as normalized `p(u | c)`.
- Do not treat context tokens as target tokens when computing target surprisal.
- Do not treat empty or punctuation-only utterances as normal scored utterances.
- Do not change output schemas without documenting the change.
- Do not run GPU LSTM training on the laptop.
- Do not replace additive age-bin baselines with global training unless the user
  explicitly asks for an exploratory/global baseline. The fair LSTM baseline is
  additive by age bin: train on the current bin plus all previous bins, generate
  only for rows in the target bin.
- Match the LSTM training corpus to the comparison target. If comparing against
  PBM-trained n-gram baselines, use the PBM-only additive config; if comparing
  against full strict-naturalistic n-grams, use the all-corpus additive config.

## Data Handling Rules

This is a data-heavy research project. Do not load or print entire datasets into
the chat/context.

When inspecting data:

- Prefer `head`, `tail`, `wc -l`, `du -h`, and column/schema summaries.
- For CSV files, inspect shape, columns, dtypes, missing-value counts, and at
  most 20 example rows.
- Never run `cat` on large CSV/JSON/JSONL files.
- Never paste full datasets into Markdown files.
- Do not commit raw data unless explicitly instructed.
- Treat `data/raw_data/` as immutable.
