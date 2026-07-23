# Modular Direct-Surprisal Analysis Pipeline

This workflow separates expensive data preparation, statistical fitting,
plotting, and report wording. A downstream rerun never silently triggers an
upstream stage.

## Stage Contract

1. `datasets` reads the scorer-wide child/caregiver tables and writes compact
   exact-design-cell files, trajectory inputs, sample flow, descriptive
   summaries, and coverage. It does not fit or plot anything.
2. `models` reads only the prepared design cells. It writes coefficients,
   prediction grids, child/corpus bootstrap draws, age-permutation draws,
   influence estimates, mixed-model warnings, and trajectory tables. It does
   not read the source-wide data or create figures.
3. `plots` reads only prepared/model outputs. It writes population summaries,
   estimator checks, resampling/influence plots, coverage plots, and individual
   profiles plus a plot audit. It does not refit anything.
4. `report` reads saved tables and figures and writes a short visual report and
   separate child gallery. It does not rebuild datasets, models, or plots.

Each stage writes a JSON manifest with its upstream manifest embedded. Model
nonconvergence, boundary, and singularity statuses are preserved rather than
treated as successful primary evidence.

## Model Coverage

The applicable direct-score ladder includes:

- the frozen child-fixed/child-clustered P1 contextual, P2 unconditional, and
  P3 context-gain models;
- k1/k2 contextual and context-gain outcomes;
- random/unigram/bigram/trigram candidate-minus-real gaps;
- frozen age-bin and quadratic-age models;
- Mundlak within/between and GEE repeated-measures sensitivities;
- top-coded linear-word, 0.5% tail-trim, random-intercept, and random-age-slope
  mixed-model sensitivities;
- 200 child bootstraps for P1/P3 and all four candidate gaps;
- 200 corpus bootstraps and 200 within-child age permutations for P1/P3;
- leave-one-child and leave-one-corpus influence;
- caregiver-input trajectories and models; and
- individual-child adjusted trajectories under an explicit support rule.

The generated `model_coverage.csv` also records scorer-dependent families that
are partial, pending, or unavailable. Missing entropy, LSTM, response-space,
Bayes, or complexity products are never substituted from a different scorer.

## Example: Rebuild Only Plots

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_direct_surprisal_modular_analysis.py \
  --stage plots \
  --prepared-dir results/direct_surprisal_replication/mistral_full79/modular/prepared \
  --model-dir results/direct_surprisal_replication/mistral_full79/modular/models \
  --fig-dir figs/direct_surprisal_replication/mistral_full79/modular_visual \
  --report-md docs/mistral_full79_visual_summary.md \
  --report-html docs/mistral_full79_visual_summary.html \
  --gallery-md docs/mistral_full79_child_gallery.md \
  --gallery-html docs/mistral_full79_child_gallery.html \
  --scorer-label "Mistral full-79"
```

Use `--stage report` to change only prose. Use `--stage models` to refit from
prepared design cells. Use `--stage datasets` only when the scorer-wide inputs,
eligibility rules, outcomes, or design-cell construction change.

## Rebuild The Human-Facing Results Explorer

The recommended consultation interface is
`docs/direct_surprisal_results_explorer.html`. It reads only saved summaries,
key coefficient tables, coverage manifests, plot files, and child-profile
audits. It never rebuilds data or refits a model.

```bash
.venv/bin/python src/build_direct_surprisal_results_explorer.py
```

The explorer defaults to the 12 primary model records and provides filters for
all 136 fitted records. Expand “See the actual model” on any card to view its
formula, estimator, controls, sample sizes, age terms, and retained warnings.

## Paired TinyDialogues–Mistral Stages

The exact paired wide table is already the immutable paired dataset product.
`src/build_paired_direct_surprisal_visual_analysis.py` adds independent
`models`, `plots`, and `report` stages on top of it. The model stage covers all
k0–k3 real-target slopes, k1–k3 context-gain slopes, all four candidate-gap
slopes, paired child-bootstrap differences, frozen P1/P2/P3 age-bin contrasts,
supported child-specific slope concordance, and recorded-token/word-normalized
scale diagnostics. The short report is
`docs/paired_tinydialogues_mistral_visual_summary.html`.

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_paired_direct_surprisal_visual_analysis.py \
  --stage plots \
  --paired-wide results/direct_surprisal_replication/paired_tiny_mistral_pbm/paired_direct_surprisal_wide.csv.gz \
  --output-dir results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular \
  --fig-dir figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual \
  --report-md docs/paired_tinydialogues_mistral_visual_summary.md \
  --report-html docs/paired_tinydialogues_mistral_visual_summary.html
```
