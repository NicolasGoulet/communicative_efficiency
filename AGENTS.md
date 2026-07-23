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

- **model-based predictability / self-information**: direct contextual
  Mistral or TinyDialogues surprisal `-log2 p(u | c)`, unconditional utterance
  surprisal `-log2 p(u)`, their context-gain difference, and exploratory
  Bayes-decomposition scores based on `p(u) p(c | u)`;
- **listener-relevant utility**: not yet a validated primary product; proposed
  measures include downstream caregiver-response predictive gain and coded
  repair, clarification, acknowledgement, or contingent continuation;
- **effort / complexity**: utterance length, morphemes, syllables, MLU-style
  measures, phoneme proxies, lexical trajectories, and related diagnostics;
- **efficiency**: currently studied through two complementary questions:
  information at fixed production effort, and production effort relative to
  contextual predictability / a generated response space.

Do not equate lower surprisal, higher surprisal, shorter speech, or longer
speech with communicative efficiency in isolation. State the estimand and
controls explicitly. In particular, the current negative fixed-effort age
slope means that older children's utterances are more predictable to Mistral at
the same measured effort; it is not by itself proof of a single normative
efficiency optimum.

## Scientific Interpretation Guardrails

The current evidence supports a narrower claim than the working project title:

- the strongest PBM result is increasing **predictability / conventionality of
  form at fixed measured effort** with child age;
- direct target surprisal `-log2 p(u | c)` is self-information under the
  scorer. A lower value means a more predictable target, not "more Shannon
  information";
- context gain
  `log2 p(u | c) - log2 p(u)` is the cleaner available measure of how much the
  preceding context supports the observed utterance and should be kept
  separate from unconditional form frequency;
- a stronger listener-utility analysis requires a downstream outcome, such as
  the gain in predicting the next caregiver response from the child utterance,
  or validated repair / clarification / contingent-response labels;
- the current exact-string response entropy is model-, prompt-, temperature-,
  and surface-form-dependent. It is not yet semantic response uncertainty;
- for effort adaptation, raw child effort and effort relative to a generated
  response distribution are different estimands. Generated expected effort is
  a model-based reference and may mediate contextual demand, so do not add it
  automatically as an ordinary confound in the primary total-association
  model. Keep models with and without that reference separate;
- next-token context entropy is a useful local uncertainty control, but it is
  not a substitute for entropy over complete plausible responses;
- random, n-gram, LSTM, and unconstrained LLM alternatives do not preserve the
  observed child's intended meaning. Do not make Pareto-optimality or
  meaning-preserving choice claims from those candidate sets.

Treat Brown, Manchester, and Providence (21 children) as the current discovery
sample. Before inspecting confirmatory estimates, freeze the primary outcomes,
effect directions, exclusions, model formulas, and onset rule. The remaining
58 children across the other 10 strict-naturalistic corpora are the preferred
confirmation sample now that the direct-Mistral 79-child scoring tree is
available. TinyDialogues currently covers the same 21 PBM children, so it is a
scorer-robustness analysis rather than an independent sample confirmation.
Observational CHILDES results can be described as consistent with developmental
adaptation or efficiency, but do not by themselves prove that children
optimize an objective.

## Current Active Data And Analysis State

Status verified locally on 2026-07-21.

Primary external scored/feature handoffs:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023
results/external/compute_surprisal_mila/raw_surprisal_lstm_additive_same_length
results/external/compute_surprisal_mila/context_entropy_mistral
results/external/compute_surprisal_mila/raw_surprisal_heldout_real_child_generalization_2026-06-16
results/external/compute_surprisal_mila/raw_surprisal_cleaned_naturalistic_79_children_all_available_ages_fp16
results/external/compute_surprisal_mila/raw_surprisal_tinydialogues_pbm_21_children_all_6_conditions_k0_k1_k2_k3_fp32
```

These are symlinks into:

```text
/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/
```

Use the model- and sample-appropriate path for each analysis. Do not copy the
multi-GB scored trees into Git. Prefer
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

The direct-Mistral 79-child production run `20260713_162955` completed and the
extracted scored tree is local. Its 1,896 CSVs cover 79 children x 6 modes x 4
contexts, with exactly 474 files for each of k0, k1, k2, and k3. The scored
child source has 1,140,695 rows after a 477-row Naima patch; the caretaker
source has 1,470,154 rows. Six generated target strings are blank, producing
24 blank baseline score cells across the four contexts. These small gaps must
be patched or explicitly flagged before describing the baseline row matrix as
literally complete. The compact final report and completion marker should
still be preserved beside the local archive even though the sibling repo
records that the final Mila audit passed.

The TinyDialogues PBM production run `20260717_201227` is also local and ready
for analysis. Its relocation-aware audit passed all 504 files: 21 children,
six modes, four contexts, 11,605,772 scored target rows, zero blank targets,
zero truncated-context rows, and zero problems. TinyDialogues uses
`LaurensWink/SmolLM2-135M_variants` revision
`149fd0d6f069ef7b0a915474c86367c7d34c1591` in FP32. Keep TinyDialogues and
Mistral scores in separate model-specific columns and output namespaces; do
not compare raw bits per model token as though their tokenizers were the same.

The legacy Route 1/Route 2 products remain PBM-scoped (Brown, Manchester, and
Providence: 21 children):

```text
results/route1_analysis_dataset/
results/route2_response_space/
results/route2_response_space_analysis/
results/existing_scored_baseline_efficiency_cloud/
```

The 2026-07-21 frozen direct-score replication products are:

```text
results/direct_surprisal_replication/tinydialogues_pbm/
results/direct_surprisal_replication/mistral_full79/
results/direct_surprisal_replication/paired_tiny_mistral_pbm/
docs/direct_surprisal_replication_index.html
docs/direct_surprisal_results_explorer.html
docs/tinydialogues_pbm_direct_surprisal_replication.html
docs/mistral_full79_direct_surprisal_replication.html
docs/paired_tinydialogues_mistral_pbm_report.html
docs/paired_tinydialogues_mistral_child_trajectories.html
docs/tinydialogues_pbm_route1_model_atlas.html
docs/tinydialogues_pbm_visual_summary.html
docs/mistral_full79_visual_summary.html
docs/paired_tinydialogues_mistral_visual_summary.html
docs/tinydialogues_pbm_child_gallery.html
docs/mistral_full79_child_gallery.html
```

These products implement child-fixed, exact/top-coded word-effort models with
child-clustered covariance, child bootstrap, nonlinear and age-bin
sensitivities, leave-one-child/corpus influence, and individual trajectories.
TinyDialogues PBM P1 is negative (`-0.222` bits/month, clustered 95% CI
`[-0.311, -0.132]`). Mistral non-PBM P1 is also negative (`-0.062`), but its
frozen primary clustered interval crosses zero (`[-0.132, 0.007]`), so the
primary confirmation criterion is not met; the child-bootstrap sensitivity
does exclude zero and must be shown alongside, not substituted for, the
primary result. P3 context gain (`k0 - k3`) is negative in Tiny PBM, Mistral
PBM, and Mistral non-PBM, contrary to the frozen positive direction. All 21
Tiny child profiles, 79 pooled Mistral profiles, 58 non-PBM profiles, and 21
paired overlay profiles exist.

The complete TinyDialogues-compatible Route-1 long table contains 11,605,772
rows from all 504 scored files and has zero source-audit problems. Its separate
expanded model atlas fits 41/56 direct model-zoo subvariants and 45/45 explicit
comparison models. The 15 unavailable subvariants are exactly the Z3/Z4/Z10
next-token entropy/certainty families; do not interpret them as model failures
or fill their absent scorer-specific predictors with zeros.

The newer plot-led direct-score workflow is
`src/build_direct_surprisal_modular_analysis.py`, documented in
`docs/direct_surprisal_modular_pipeline.md`. Its `datasets`, `models`, `plots`,
and `report` stages are independent and chained by manifests. The completed
Tiny run has 34 recorded model rows (31 ordinary passes and 3 singular/boundary
mixed sensitivities) and 32 audited figures. The completed Mistral run has 102
model rows (93 ordinary passes, 8 singular/boundary mixed sensitivities, 1
nonconverged mixed sensitivity, and 0 failed primary/direct fits) and 171
audited figures. Treat unweighted design-cell mixed fits as sensitivities, not
as replacements for the frozen exact-cell WLS primary model.

The paired visual workflow is
`src/build_paired_direct_surprisal_visual_analysis.py`. It treats the exact
446,508-row PBM intersection as its immutable dataset stage, then separates
models, plots, and report rendering. Its completed model stage covers 11
real-target, context-gain, and n-gram-gap outcomes with 200 paired child
bootstraps. Supported child-level P1 slope signs agree across scorers for
18/21 children. The extended paired stage also saves P1/P2/P3 quadratic
coefficient bootstraps, age-bin candidate rankings, and candidate-source age
interactions; its plot audit records 7/7 figures present. Raw score magnitudes
remain non-comparable across scorer calibrations.

The recommended human consultation view is
`docs/direct_surprisal_results_explorer.html`, generated by
`src/build_direct_surprisal_results_explorer.py`. It is a static interactive
page over saved artifacts only: 136 filterable model cards, 31 summary plots,
179 scorer/scope child profiles, 30 model-family coverage rows, plain-language
interpretations, exact formulas, key age terms, and retained warnings. Use it
before sending users to linear reports or raw CSV tables.

Important current facts:

- the full-79 direct-Mistral score tree is available, but full-79 context
  entropy, word-level surprisal, LSTM targets/scores, response-space products,
  complexity products, and corrected Bayes scores are not all available;
- TinyDialogues covers the 21-child PBM discovery set for real, random,
  unigram, bigram, trigram, and caretaker targets at k0-k3; it does not yet
  cover the other 58 children or the PBM LSTM candidates;
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
- the original Bayes values are unnormalized decomposition scores because `p(c)` has not
  been estimated. They are most defensible for same-context candidate
  comparisons and must not be labeled as normalized posterior surprisal;
- the current Bayes pilot is additionally unsuitable for substantive inference
  because its full-79 training data include the evaluated PBM real utterances
  and context pairs. This creates an in-sample advantage for real targets over
  generated targets;
- the order-3 likelihood in `bayes_efficiency_mila` conditions the first
  context token on only the candidate utterance's last word; after the first
  context token, the candidate utterance is no longer in the trigram history.
  Treat this as an implementation proof of concept, not a rich discourse
  likelihood. Do not use its raw per-child-word scores for developmental
  claims;
- the corrected PBM Bayes-derived product is under
  `results/corrected_pbm_bayes_v2/`. It uses leave-corpus-out cross-fitting,
  additive age-bin training, explicit unknown-token handling, whole-utterance
  contrastive context evidence, and normalization over each row's available
  real/random/unigram/bigram/trigram candidates. Its 2,232,524-row audit passed
  held-out matched-versus-shuffled context validation in Brown, Manchester,
  and Providence;
- corrected `candidate_set_probability` is a probability only over the supplied
  matched candidate set. It is not a posterior over every possible utterance.

Move real data, generated utterances, model checkpoints, and scored outputs
between machines with `rsync` or Globus, never Git.

## Current Reporting State

Current supervisor-facing utterance-information report:

```text
docs/predicting_utterance_level_information_report.md
docs/predicting_utterance_level_information_report.html
```

The July supervisor-report landing page and formal methods reference are:

```text
docs/july_meeting_index.html
docs/july_meeting_definitions.html
docs/july_meeting_formal_mathematical_definitions.md
```

The definitions page is generated by `src/build_july_meeting_index.py` from
`src/july_formal_definitions.py`. Keep the HTML and copyable Markdown/LaTeX
source synchronized through that builder. When changing a formula, first
verify the corresponding scorer, feature builder, or statistical model rather
than silently regularizing the notation into a different estimand.

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
docs/corrected_pbm_bayes_report.md
```

The clearest current PBM finding is a negative child-controlled, fixed-effort
Mistral age slope. The onset report estimates the first age-bin decrease by
`024-029`, but its child-age-cell sensitivity changes the sign/weighting and
child-bootstrap intervals are still pending. Keep this caveat visible; do not
promote an exact developmental onset as settled.

The current Route 2 relative-effort result does **not** support the simple
prediction that older children increasingly lengthen responses as sampled
response entropy rises. In the final relative-effort models, the age by
response-entropy interaction is in the opposite direction for the principal
residual/percentile outcomes. Treat this as a result or a measurement
diagnostic to be replicated after semantic-entropy calibration; do not spin it
as confirmation of the original hypothesis.

## Current Scientific And Compute Focus

Priorities as of the 2026-07-21 data-readiness audit:

1. Freeze a PBM-discovery / non-PBM-confirmation protocol before examining the
   remaining children's main estimates. Predeclare the primary context-gain,
   effort-adaptation, and onset estimands and their predicted directions.
2. Build the model-namespaced TinyDialogues PBM analysis and paired
   TinyDialogues-versus-Mistral robustness report from the audited 504-file
   handoff. Repeat applicable current direct-score models and record explicit
   blockers for context-entropy, LSTM, heldout, and Route 2 products.
3. Build and audit the full-79 Mistral analysis table, patch or flag the 24
   blank generated score cells, and produce individual trajectories for all 79
   children before fitting the frozen non-PBM confirmation models.
4. Preserve the full-79 compact final report/marker beside the local archive
   and freeze model/input manifests for both scorers.
5. Define the primary conversational eligibility sample: genuine child turns
   responding to a caregiver in the same session. Preserve flags for turn
   distance, child-initiated turns, imitation, routines/reading, backchannels,
   and repair sequences; manually validate a stratified subset.
6. Refit the fixed-effort analysis with unconditional surprisal, contextual
   surprisal, and context gain kept separate. Prototype downstream caregiver
   response utility and validated repair/clarification outcomes before making
   a broad communicative-success claim.
7. Calibrate sampled response uncertainty before rerunning the main effort
   hypothesis: compare exact-string and semantic-cluster entropy, sparse-sample
   estimators, sample-size rarefaction, seeds, prompts/temperatures, and at
   least one decoupled generator sensitivity where feasible.
8. Add child-level bootstrap/small-cluster intervals to the developmental
   analyses. Define onset through a predeclared sustained interval with a
   simultaneous confidence band, and promote it only after non-PBM
   replication.
9. Use the corrected cross-fitted Bayes report as a decomposition/robustness
   result, not a replacement for direct Mistral surprisal. If extending it,
   score LSTM or meaning-preserving candidates as newly named candidate sets,
   retain separate prior/context components, and rerun all held-out validation
   gates. Keep the original overlapping reverse-trigram product methods-only.
10. Reconcile the main supervisor report with the completed LSTM,
   response-space, Bayes, complexity, and scientific-audit work. Keep
   supported findings, contrary-direction findings, and proposed analyses
   visually distinct.
11. Extend complexity validation for CHAT morphology, phonological proxies,
   lexical diversity, and dependency feasibility before treating them as
   primary controls.
12. If the full response cloud remains a priority, score sampled responses on
   Mila and distinguish Mistral-generated/Mistral-scored self-reference from
   decoupled generators. Reserve efficiency-frontier claims for a separately
   validated meaning-preserving candidate set.
13. Use SES, race/ethnicity, parental education, sex/gender, or nationality
   only with explicit metadata-level provenance. Current coverage is too
   sparse for most of these to serve as general covariates.

The legacy in-repo LSTM implementation remains useful for audits and local CPU
smokes, but real new training belongs on Mila. The execution-oriented baseline
repo is now:

```text
/home/apaixonada/EvaPortelance/Projet_1/generate_baselines_mila
```

For an LSTM task, read these first:

1. `docs/lstm-baseline-pipeline.md`
2. `README.md`
3. `src/generate_baselines_mila/full79_lstm.py`
4. `src/generate_baselines_mila/lstm.py`
5. `src/generate_baselines_mila/cli.py`
6. `slurm/submit_full_79_lstm.sh`
7. `slurm/run_full_79_lstm_cell.sbatch`
8. `tests/test_full79_lstm_production.py`
9. `tests/test_lstm_generation.py`

The LSTM pipeline:

- trains a small word-level encoder-decoder LSTM;
- trains one model per additive age bin, matching the developmental information
  constraints used by the random/unigram/bigram/trigram baselines;
- uses caretaker context k3 and same-length generation for the selected full-79
  production comparison;
- keeps all eight additive age-bin checkpoints; reducing below eight would
  introduce future-age information or break the matched developmental design;
- selects k3 only, rather than repeating k3/k4/k5, because the PBM results show
  nearly identical aggregate LSTM behavior across context windows and k3 is the
  simplest primary-context comparison;
- decodes child-like utterance baselines;
- supports free-length generation generically, but it is not part of the
  selected full-79 production run because it changes the effort estimand;
- writes generated LSTM sibling files and compact scoring-ready files;
- gates production through CPU preparation, an exact-wrapper GPU smoke, staged
  array waves, output audits, and a final `COMPLETE_AND_AUDITED` marker;
- does not compute LLM surprisal.

Do not claim that a new LSTM was trained unless a real training command was run
and its checkpoints, vocabulary, manifest, and audits exist. Do not rerun the
completed PBM proof-of-concept merely because older documentation calls it
"planned." The full-79 k3 workflow is implemented and locally validated as of
2026-07-14, but no Mila GPU production run or final marker has been retrieved.

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
- `src/build_corrected_pbm_bayes_report.py`: corrected cross-fitted PBM
  candidate-set Bayes results, held-out validation, child bootstrap, and direct
  Mistral comparison.
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

Latest full-suite verification on 2026-07-22 after the interactive results
explorer integration and status reconciliation: 390 tests passed in 1767.508
seconds with `CUDA_VISIBLE_DEVICES=''`. The clean-cache run emitted expected
Statsmodels convergence, perfect-separation, singular-fit, plotting, and
small-fixture numerical warnings but no test failures. Treat model-fit warnings
in production analyses as audit items even when unit tests allow them.

## Project-Specific Constraints

- Do not overwrite raw CHILDES / CHAT data.
- Do not silently drop utterance rows without recording why.
- Do not invent scientific results or pretend a model was run.
- Do not conflate the completed 79-child direct-Mistral score tree with a
  completed full-79 analysis or a complete full-79 predictor set. Preserve the
  final scoring marker/report locally and keep every partial predictor family
  labeled by its actual sample coverage.
- Do not generalize PBM (21-child, 3-corpus) analyses to the full 79-child,
  13-corpus bundle without a new scored analysis.
- Do not pool the PBM discovery sample into the remaining corpora and call the
  resulting estimate confirmatory; report the non-PBM replication separately.
- Do not call lower target surprisal "more information" without explicitly
  defining the direction and construct. Prefer predictability,
  conventionality, or contextual support where those are the actual measures.
- Do not describe response-space samples as same-meaning paraphrases.
- Do not describe Mistral response entropy as model-independent behavioral
  uncertainty.
- Do not conflate raw child-effort models with generated-relative effort
  models, or silently treat generated expected effort as a standard confound.
- Do not describe the legacy Bayes score as normalized `p(u | c)`.
- Do not promote the legacy Bayes pilot as evidence that real child utterances
  outperform generated alternatives until candidate scoring is cross-fitted
  and the likelihood passes held-out matched-vs-shuffled context validation.
- When using the corrected v2 score, call it a **Bayes-derived candidate-set
  probability/surprisal**. Always state the candidate set and keep the prior,
  context-evidence, and combined contributions separately visible.
- Do not promote an exact developmental onset from a data-selected breakpoint
  or row-level interval without child-level uncertainty and held-out
  replication.
- Do not use information/effort ratios as the sole primary efficiency outcome;
  denominator coupling can create artifacts. Prefer conditional models or a
  validated same-meaning frontier analysis.
- Do not treat caregiver speech addressed to children as an adult endpoint;
  it primarily measures caregiver input adaptation unless an adult-adult
  benchmark is added.
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
