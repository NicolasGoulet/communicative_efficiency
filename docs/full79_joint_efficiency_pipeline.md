# Full-79 conditional joint-efficiency pipeline

Status: production complete and independently audited on 2026-08-25.

This is the operator and future-agent handoff for the conditional joint
analysis. Read `full79_joint_efficiency_analysis_design.md` first for the
scientific contract. This file records the implemented workflow, output map,
run facts, and safe rebuild rules.

## Scientific separation

The pipeline answers two complementary questions:

1. Does absolute or Qwen-relative response effort adapt to full-response
   exact-string entropy as children age?
2. Does contextual Mistral surprisal change with age at the same exact word
   effort?

It does not optimize a universal shortness objective. Mistral surprisal is
scorer self-information, exact-string entropy is not semantic uncertainty,
and Qwen alternatives do not preserve the observed child's intended meaning.
Raw nondominance is therefore secondary.

## Commands

Use the project virtual environment and run stages independently:

```bash
MPLCONFIGDIR=/tmp/mpl-joint-efficiency .venv/bin/python \
  src/build_full79_joint_efficiency_analysis.py --stage datasets

MPLCONFIGDIR=/tmp/mpl-joint-efficiency .venv/bin/python \
  src/build_full79_joint_efficiency_analysis.py --stage metrics

MPLCONFIGDIR=/tmp/mpl-joint-efficiency .venv/bin/python \
  src/build_full79_joint_efficiency_analysis.py --stage models

MPLCONFIGDIR=/tmp/mpl-joint-efficiency .venv/bin/python \
  src/build_full79_joint_efficiency_analysis.py --stage plots

MPLCONFIGDIR=/tmp/mpl-joint-efficiency .venv/bin/python \
  src/build_full79_joint_efficiency_analysis.py --stage report

MPLCONFIGDIR=/tmp/mpl-joint-efficiency .venv/bin/python \
  src/build_full79_joint_efficiency_analysis.py --stage audit
```

`--stage all` executes the same sequence. Do not use it when only plots or the
browser report changed; those stages intentionally consume frozen estimates.

## Output map

```text
results/full79_joint_efficiency_analysis/
  datasets/
    analysis_rows.parquet
    analysis_rows.schema.json
    dataset_audit.json
    dataset_manifest.json
  metrics/
    model_rows.parquet
    gamm_rows.csv.gz
    observed_cloud_metrics.parquet
    child_age_metric_cells.parquet
    child_bootstrap_age_trajectories.csv
    paper_atlas_distribution_summary.csv
    corrected_bayes_decomposition_summary.csv
    metrics_audit.json
    metrics_manifest.json
  models/
    all79/
    pbm_discovery/
    non_pbm_confirmation/
    combined_model_registry.csv
    combined_model_contrasts.csv
    combined_prediction_grids.csv.gz
    combined_child_effects.csv
    combined_residual_diagnostics.csv.gz
    models_manifest.json
  plots/
    figure_catalog.csv
    plot_audit.json
    plots_manifest.json
  report/
    report_payload.json
    report_audit.json
    report_manifest.json
  audit/
    audit_checks.csv
    final_audit.json
    audit_manifest.json
  FULL79_JOINT_EFFICIENCY_COMPLETE_AND_AUDITED

figs/full79_joint_efficiency_analysis/
docs/full79_joint_efficiency_explorer.md
docs/full79_joint_efficiency_explorer.html
```

## Production facts

- Dataset gate: 1,122,396 unique observed utterances, 645,524 contexts, 79
  children, 13 corpora, and zero invalid core measurements.
- Qwen gate: 64,552,400 responses scanned, exactly 100 per context.
- Exact-length support: 525,873 observed utterances have at least five Qwen
  responses at the same exact length; 381,978 have no exact-length match.
- Bootstrap: 500 whole-child resamples per developmental age-bin summary.
- Models: 15/15 converged. The pooled descriptive scope has nine registered
  models. PBM discovery and other-58 confirmation each repeat unchanged M1,
  M3, and M4 core formulas.
- Smooth-basis check: minimum finite k-index is 0.953.
- Plots: 17/17 registered figures passed PNG and link audits.
- Browser microscope: 8 audited contexts and 840 responses, including all 100
  Qwen responses plus observed/n-gram/random comparison rows per context.
- Final audit: 38/38 checks passed.

## Headline adjusted results

- At 42 months, entropy p10 to p90 yields a small pooled absolute-length ratio
  of 1.028, 95% CI [1.014, 1.043]. The PBM discovery ratio is 1.042 [1.026,
  1.059]; the other-58 estimate is 1.017 [0.999, 1.037].
- Qwen-relative effort reverses over development. At 42 months the pooled
  effort-percentile odds ratio is 0.931 [0.902, 0.962]; both PBM discovery and
  other-58 confirmation have the same negative direction. Near 18 months the
  direction is positive.
- For two-word utterances, the supported-range age difference in contextual
  k3 total surprisal is -3.47 bits [-4.84, -2.10] pooled, -5.77 [-10.54,
  -1.01] in PBM discovery, and -2.34 [-3.96, -0.71] in the other-58
  confirmation sample.
- The fixed-effort age surface is nonlinear. Common 2-4-word regions support
  increasing predictability, whereas sparse long-length endpoints are
  unstable and must not be generalized.
- The child target is usually above the Qwen same-length median in raw k3
  summaries. Under high response entropy, the adjusted exact-length gap
  declines by 2.56 bits [-3.89, -1.24] across the supported pooled age range.
  This is a scorer-indexed generated-form comparison, not intended-meaning
  recovery.

## Rebuild and modification rules

- Change raw inputs or row definitions: rerun every stage.
- Change a metric definition: rerun `metrics` onward.
- Change a formula, family, sample scope, or support threshold: rerun `models`
  onward.
- Change only visual layout: rerun `plots`, `report`, and `audit`.
- Change only prose or browser layout: rerun `report` and `audit`.
- Never edit a manifest by hand. A downstream stage rejects a missing or
  hash-stale predecessor output.
- The corrected PBM Bayes sidecar is not the model engine. An all-79 Bayes
  extension requires a separate cross-fitted scoring and audit project.

## Verification

Focused tests:

```bash
MPLCONFIGDIR=/tmp/mpl-joint-efficiency-test .venv/bin/python -m unittest \
  tests.test_build_full79_joint_efficiency_analysis -v
```

The final audit is the authoritative local product gate. A completion marker
is valid only when `audit/final_audit.json` is `PASS` with no failed checks and
all predecessor manifests still hash-validate.

The final repository-wide verification command was:

```bash
CUDA_VISIBLE_DEVICES='' MPLCONFIGDIR=/tmp/mpl-joint-efficiency-full-rerun \
  .venv/bin/python -m unittest discover -s tests
```

It passed 533 tests in 394.037 seconds. The emitted convergence, separation,
rank, and plotting warnings are the documented behavior of small synthetic
legacy fixtures; there were no test failures.
