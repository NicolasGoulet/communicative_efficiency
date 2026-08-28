# Fresh-chat implementation prompt: Bayesian Route 1 / Route 2 program

Copy everything below into a fresh Codex chat opened in:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency
```

---

You are implementing the first Bayesian Route 1 / Route 2 analysis program in
the `communicative_efficiency` repository. Work as a senior research
statistician and research-software engineer. Do not merely discuss the models:
implement the staged, tested workflow described below, but fail closed at the
real-data pilot if final production would be computationally unsafe or if the
likelihood cannot recover known synthetic parameters.

## First actions and Git safety

1. Read `AGENTS.md` completely.
2. Read the current-focus section of `TODO.md` and the latest relevant entries
   in `docs/notes.md`.
3. Read these scientific contracts completely:

```text
docs/bayesian_route1_route2_program_2026-08-28.md
docs/utterance_informativity_route1_route2_protocol.md
docs/full79_joint_efficiency_analysis_design.md
docs/full79_joint_efficiency_pipeline.md
```

4. Review the source paper directly:

```text
/home/apaixonada/Downloads/2509.17161v1.pdf
expected SHA-256:
cecf8f0e696c3b95a3b4033352e484e3c0b863560959c793e8d67ebd957f1957
```

5. Inspect `git status --short --branch`, `git branch -vv`, and the recent
   graph before editing. The current analysis products live on the checked-out
   August analysis lineage; local `main` may be behind it. Do not switch to
   `main`, merge branches, rebase, pull, or discard changes on your own. Start
   a dedicated branch named `agent/bayesian-route1-route2-v1` from the clean
   current HEAD if that branch does not already exist. If the worktree is
   dirty or the starting lineage is ambiguous, stop and report the exact
   status.

6. Record the starting SHA in the new workflow contract. Never commit large
   data or generated result trees.

## Objective

Build a reproducible Bayesian robustness and extension analysis over the
already scored 79-child naturalistic data. Do not run language-model scoring,
do not submit Mila jobs, and do not include Hall, structured, or
clinical/control populations in Phase 1.

Existing outcomes have already been inspected. Describe this as a post-hoc
Bayesian extension with a preserved PBM/non-PBM split, not a new prospective
confirmation.

The scientific questions remain:

- Route 1: how unconditional and contextual child-utterance predictability
  change with age at fixed measured effort;
- Route 2: how absolute and generated-relative child effort adapt to
  conversational demand;
- joint: whether those developmental changes covary across children, without
  using information/effort ratios.

## Immutable inputs

Use only the audited local products:

```text
results/direct_surprisal_replication/mistral_full79/
  child_direct_surprisal_wide.csv.gz
results/direct_surprisal_replication/mistral_full79/modular/prepared/
  trajectory_input.csv.gz
results/direct_surprisal_replication/mistral_full79/modular/models/

results/full79_joint_efficiency_analysis/metrics/
  model_rows.parquet
  child_age_metric_cells.parquet
  observed_cloud_metrics.parquet
results/full79_joint_efficiency_analysis/models/
```

Verify hashes/manifests before deriving anything. Expected high-level facts:

```text
Route 2 eligible observed rows: 1,122,396
children: 79
corpora: 13
Qwen responses per included context: 100
effort-percentile endpoints: 145,618 at 0; 127,565 at 1
PBM discovery: 21 children (Brown, Manchester, Providence)
non-PBM replication: 58 children (the other 10 corpora)
```

Do not reconstruct these data from raw scored trees when an authoritative
analysis-ready table exists.

## Implement exactly five priority model families

The complete formulas, rationale, and interpretation boundaries are in
`docs/bayesian_route1_route2_program_2026-08-28.md`. Preserve them.

### B1: joint k0-k3 context-depth Route 1 model

- Pair the same child utterance at k0, k1, k2, and k3.
- Control exact/top-coded word effort.
- Use robust condition-specific age curves and correlated child/corpus effects.
- Use cell means with observed standard errors only after an exact aggregation
  audit against the raw rows.
- Derive k0-k1, k1-k2, k2-k3, and k0-k3 gains from the joint posterior.
- Do not fit independent gain models as substitutes for the paired posterior.

### B2: Route 1 location-scale model

- Model contextual k3 total surprisal with a Student-t likelihood.
- Let both the conditional mean and residual scale vary with age; control word
  effort and child/corpus structure.
- Query age change in mean predictability and age change in residual
  variability at common supported 1-4-word lengths.
- Keep bits per model token secondary.

### B3: raw Route 2 effort-adaptation model

- Negative-binomial child word count.
- Nonlinear age and response-entropy effects, their tensor interaction,
  context length, correlated child intercept/age/entropy effects, and corpus.
- Primary total-association model excludes Qwen expected length.
- Fit the Qwen-expected-length adjustment as a separately named sensitivity.
- Benchmark the exact raw-row likelihood. Do not silently replace the unit or
  sample if full NUTS is infeasible.

### B4: endpoint-aware Qwen-relative effort model

- Verify `rank200 = round(200 * effort_percentile_in_qwen)` exactly.
- Primary candidate: beta-binomial rank likelihood with 200 trials.
- Registered sensitivity: zero-one-inflated beta using the literal 0/1 ranks.
- Predictors mirror B3 without double-adjusting for generated expected length.
- Compare posterior predictive calibration, endpoint behavior, and supported
  age-by-entropy contrasts.

### B5: bivariate child-level information-effort development

- Estimate child-specific Route 1 fixed-effort age slopes and Route 2
  age/age-by-entropy slopes with their uncertainty.
- Obtain the within-child cross-outcome estimation covariance from a shared
  bootstrap or shared model. Do not assume independence.
- Fit a bivariate hierarchical measurement-error model with corpus structure.
- Primary outputs: population mean vector, between-child correlation, and
  leave-one-child/corpus sensitivity.
- Never replace this with an information/effort ratio.

## Required sample scopes

Run unchanged formulas in:

```text
pbm_discovery
non_pbm_replication
all79_descriptive
```

Do not pool PBM into non-PBM and call it confirmation. Do not choose different
priors or formulas after seeing which scope supports the desired direction.

## Required Bayesian workflow

Implement independent stages:

```text
contract
datasets
priors
synthetic-smoke
real-pilot
models
diagnostics
synthesis
plots
report
audit
```

Use a thin controller with independently callable stages and hash-bound
predecessor manifests. Plotting and reporting consume saved artifacts and must
not refit.

Before production fitting:

1. Audit the local R/Python Bayesian packages and compilers.
2. Prefer repository-local pinned `brms` + CmdStan because the required
   likelihoods and multivariate structures are supported directly.
3. Do not install global packages or change the primary environment silently.
4. Add a tiny synthetic compile/sample smoke.
5. Run deterministic synthetic recovery tests for every likelihood family.
6. Run prior predictive simulation and save machine-readable plausibility
   checks.
7. Run a representative real-data pilot and record projected wall time,
   memory, disk, ESS/hour, and output size for every final fit.
8. If the projection is unsafe, stop after producing the compact pilot report.
   Do not launch Mila GPU work or simplify the estimand without review.

Use regularizing, scale-aware priors. Freeze weak, skeptical, and wider prior
sets in a tracked config after prior predictive checks and before production
posterior fitting. Define effect-scale ROPEs for a six-month change in bits,
words, and rank percentile. Bayes factors are not primary.

For each production model save:

- exact formula, family, priors, contrasts, source hashes, and sample flow;
- posterior summaries and draws needed for registered contrasts;
- R-hat, bulk/tail ESS, divergences, treedepth and energy diagnostics;
- prior and posterior predictive summaries by age, effort, child, corpus, and
  entropy/rank support;
- linear, quadratic, and low-rank smooth age candidates;
- PSIS-LOO diagnostics and stacking weights;
- whole-child and leave-one-corpus influence results;
- weak/skeptical/wide prior sensitivity results;
- comparison with the corresponding frozen frequentist estimates without
  requiring exact numerical agreement.

## Testing requirements

Write tests before implementation for at least:

- immutable source/hash and sample-role contracts;
- one-row-per-identity joins and complete k0-k3 pairing;
- exact cell aggregation, means, SDs, counts, and SEs;
- literal preservation of percentile endpoints and integer `rank200`;
- formula/prior/contrast registry completeness;
- synthetic recovery of context, dispersion, count, endpoint, and correlated
  slope parameters;
- failure on mismatched dimensions, duplicated identities, changed scopes,
  missing priors, missing diagnostics, or stale manifests;
- report/plot stages proving that no fitting function is called;
- final audit refusal when any model/scope/sensitivity/diagnostic is missing.

Run focused tests throughout and the full repository suite before completion.
Record actual test counts and warnings; never copy historical counts.

## Output namespace

Keep all new products isolated:

```text
results/bayesian_route1_route2_20260828/
figs/bayesian_route1_route2_20260828/
docs/bayesian_route1_route2_report.md
docs/bayesian_route1_route2_report.html
```

Large posterior draws and generated artifacts stay ignored. Commit source,
tests, configs, compact manifests/summaries, and Markdown documentation only.

## Interpretation and reporting guardrails

- Lower surprisal means greater scorer predictability/conventionality, not
  greater Shannon information transmitted.
- Raw child effort and Qwen-relative effort are distinct estimands.
- Qwen responses are not meaning-preserving alternatives.
- Exact-string response entropy is model/prompt/temperature dependent.
- A correlation between Route 1 and Route 2 slopes is coordinated development,
  not proof of optimization or causality.
- Report contrary, null, heterogeneous, and prior-sensitive posteriors.
- Do not promote a breakpoint/onset selected from these data.
- Do not use Bayes-factor cutoffs as a replacement for p-value cutoffs.

## Documentation and handoff

Update `AGENTS.md`, `TODO.md`, `docs/design.md`, and `docs/notes.md` when the
implementation state changes. Do not overwrite the design-only language until
the corresponding stage truly exists.

At the end of each substantial stage, report concisely:

- outcome and stage status;
- exact commit SHA and branch;
- tests actually run;
- artifacts/manifests created;
- runtime projection or fitted-model diagnostics;
- next safe command or the exact blocker.

Do not claim completion until the independent audit verifies all five model
families across their registered scopes and the final completion marker is
written from a clean committed revision.

---
