# Full-79 Conditional Joint Efficiency Analysis: Design and Agent Handoff

Status: implemented and independently audited on 2026-08-25.

This document is the durable scientific and engineering contract for the
all-79 analysis of child response length, contextual surprisal, and generated
response-space uncertainty. Later agents should read this document before
changing models, plots, or report language.

## Scientific question

The analysis does **not** assume that shorter responses are always better.
Instead, it treats response length as an adaptive decision that may depend on
the conversational context. A short answer may be appropriate when the
response space is narrow, whereas a longer answer may be appropriate when the
response space is broad or the context demands a more elaborate response.

The central object is therefore the conditional joint response policy:

```text
p(response length, response surprisal | context, child age)
```

The project asks four complementary questions:

1. At the same exact word length, does contextual Mistral surprisal change with
   child age?
2. Does child response length adapt nonlinearly to full-response uncertainty,
   generated expected length, and observable context demand?
3. Where does each observed child response fall inside the complete
   information-by-effort cloud of 100 Qwen responses to the same context?
4. Does that context-relative joint position become better calibrated with
   age, and how heterogeneous is this developmental pattern across children?

Target surprisal is scorer self-information:

```text
S(u | c) = -log2 p_Mistral(u | c)
```

Lower values mean that the response is more predictable or conventional under
Mistral. They do not mean that the child transmitted more Shannon information.
The analysis may describe lower surprisal as lower scorer-indexed information
cost, but must keep this definition explicit.

## Supervisor motivation

The source record is:

```text
docs/project_motivation_recent_email_context_2026-06-16.md
results/zoom_transcripts/2026-06-04_yang_nicolas_eva/combined_transcript.txt
```

Professor Xu proposed two complementary efficiency analyses:

1. information/predictability with length constrained;
2. response-length modulation by contextual or response-space uncertainty.

The transcript specifically proposes sampling complete responses, estimating
their entropy, recording their length distribution, and testing whether high
response uncertainty predicts longer child productions. Generated expected
length is a distinct model-based reference and is not automatically an
ordinary confound.

## Immutable upstream inputs

The new workflow consumes already audited local products:

```text
results/full79_information_effort_clouds/datasets/non_lstm_candidates.parquet
results/full79_information_effort_clouds/metrics/candidate_context_normalized.parquet
results/full79_information_effort_clouds/metrics/qwen_context_metrics.parquet
results/full79_information_effort_clouds/metrics/child_age_model_length_cells.parquet
results/full79_information_effort_clouds/metrics/length_distribution_by_age_source.csv.gz
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa
```

The canonical Qwen handoff contains 645,524 contexts and 64,552,400 responses,
exactly 100 per context. No generation or neural scoring is performed here.

## Output namespace

```text
results/full79_joint_efficiency_analysis/
figs/full79_joint_efficiency_analysis/
docs/full79_joint_efficiency_explorer.md
docs/full79_joint_efficiency_explorer.html
```

## Independent stages

The controller implements:

```text
datasets -> metrics -> models -> plots -> report -> audit
```

Each stage writes a manifest with input hashes, output hashes, row counts, and
schemas. A downstream stage must consume the saved predecessor artifacts. It
must not silently reconstruct data or refit a model.

- `datasets`: freeze one row per eligible observed child utterance with all
  context, Qwen-reference, and score variables.
- `metrics`: compute descriptive distributions, exact-length conditional Qwen
  comparisons, cloud-position diagnostics, and bootstrap summaries.
- `models`: fit the registered nonlinear repeated-measures models and save
  coefficients, smooth diagnostics, prediction grids, and model metadata.
- `plots`: render figures only from frozen metric and model outputs.
- `report`: build the browser document only from manifests, tables, and plots.
- `audit`: independently verify stage hashes, schemas, model completion,
  figures, report links, sample coverage, and interpretation labels.

## Analysis-ready row contract

One row represents one eligible observed child utterance. Required fields:

- utterance, context, corpus, child, and session identifiers;
- age in months and the frozen age bin;
- observed word count, k0/k3 total surprisal, k3 bits per token, and context
  support;
- caregiver-context word count;
- exact-string response entropy and unique-response diagnostics;
- Qwen mean, median, SD, p10, and p90 word counts;
- Qwen mean, median, SD, p10, and p90 k3 surprisal;
- child-minus-Qwen length residual, effort z score, and effort percentile;
- k3 z score and overall k3 percentile;
- exact-length Qwen k3 support count, conditional percentile, conditional
  median gap, and conditional quantile band where identifiable;
- secondary raw Pareto diagnostics relative to the 100 Qwen responses.

## Smarter cloud metrics

Means remain useful descriptions but are not the primary representation.
Required distributional metrics include:

1. empirical effort percentile in the 100-response Qwen distribution;
2. empirical k3 percentile in the full response cloud;
3. k3 percentile among Qwen responses with the **same exact word length**;
4. observed-minus-Qwen conditional median k3 gap at exact length;
5. robust context-relative z coordinates and bivariate cloud distance;
6. raw dominance count and proportion under the explicitly secondary rule
   `Qwen length <= child length` and `Qwen k3 <= child k3`;
7. distance to the nearest dominating Qwen response when one exists;
8. medians, interquartile ranges, and whole-child bootstrap intervals by age
   and response-entropy band.

Raw Pareto status is not the definition of efficiency because longer answers
can be contextually appropriate. It is retained only as a transparent
generated-reference diagnostic.

## Registered nonlinear model suite

The primary engine is `mgcv::bam`, which is available locally and is suitable
for large nonlinear repeated-measures data. The suite is deliberately small;
it is not a p-value-selected model zoo.

Sample roles are frozen before fitting. The complete model suite is fitted to
all 79 children as a pooled descriptive analysis. M1, M3, and M4 are also fit
unchanged in Brown/Manchester/Providence as discovery and in the other 58
children as confirmation. Raw score levels are never pooled across scorers.

### M1: raw child effort

Negative-binomial GAMM:

```text
child_words ~ s(age)
            + s(response_entropy)
            + ti(age, response_entropy)
            + s(context_word_count)
            + child random intercept
            + child random age slope
            + child random entropy slope
            + corpus random intercept
```

This is the primary total-association effort model and does not condition on
generated expected length.

### M2: generated-reference effort sensitivity

M1 plus a smooth of Qwen expected words. This answers a different question:
child effort relative to a model-based response-length reference.

### M3: information at adaptive effort

Robust Student-t GAMM:

```text
child_k3_total_bits ~ s(age)
                    + s(exact_word_length)
                    + ti(age, exact_word_length)
                    + s(response_entropy)
                    + s(context_word_count)
                    + child random intercept
                    + child random age slope
                    + child random entropy slope
                    + corpus random intercept
```

Bits per token, k0, and context support are registered sensitivities and remain
separate outcomes.

### M4: effort calibration inside Qwen

Beta GAMM for the child effort percentile, using the standard open-interval
transformation for empirical 0/1 ranks. Predictors mirror M1; M2-style
generated-reference adjustment is not used because the outcome is already
defined relative to the generated distribution.

### M5: exact-length information calibration

Robust Student-t GAMM for the child-minus-Qwen conditional median k3 gap among
responses with the same exact word length. Only rows with adequate conditional
Qwen support enter the primary fit; exact word length remains a smooth control,
and support thresholds and exclusions are audited.

### M6: secondary raw nondominance

Binomial GAMM for whether no Qwen response simultaneously has no greater word
length and no greater k3 surprisal. This is labelled a raw generated-reference
diagnostic, not communicative optimality.

All models save population prediction grids, covariance-aware age, entropy,
and length contrasts, uncertainty intervals, effective degrees of freedom,
deviance explained, convergence state, and smooth-basis diagnostics. Stable
child identity is controlled through child random intercepts; random age and
entropy slopes represent developmental and context-response heterogeneity.
Whole-child bootstrap summaries are a sensitivity layer, not a replacement
selected after inspecting results.

## Required figures

1. **Developmental demand surface:** predicted child length over age and
   response entropy from M1, with observed data support shown.
2. **Generated-reference sensitivity surface:** M2 predictions at low, median,
   and high Qwen expected length.
3. **Length calibration:** child length versus Qwen expected length, faceted by
   age bin, with the identity line, entropy bands, and distributional summaries.
4. **Paper-style information-effort atlas:** x is exact word length and y is
   contextual surprisal; age bins are panels; source curves show medians and
   distributional ribbons with common axes.
5. **Joint cloud phase portrait:** effort percentile versus information
   percentile/gap with age trajectories and whole-child bootstrap ellipses.
6. **Distributional developmental plot:** full child-minus-Qwen length
   distributions by age and response-entropy band.
7. **Child heterogeneity:** child-specific developmental and entropy-response
   effects with uncertainty or shrinkage.
8. **Context examples:** selected high/low-entropy contexts showing all 100
   responses, observed child location, exact-length comparison, and the raw
   nondominated subset.
9. **Model diagnostics:** residual, smooth, support, and sensitivity summaries.
10. **Bayes decomposition sidecar:** prior contribution versus context-evidence
    contribution from the existing corrected PBM product, clearly separated
    from the all-79 direct-Mistral analysis.

## Bayes work

`bayes_efficiency_mila` performs a Bayes decomposition of utterance prior and
context evidence. It is not the Bayesian hierarchical regression engine.

The existing corrected cross-fitted PBM product can be visualized immediately
as a separate decomposition/robustness layer. Extending it to all 79 children
or all 64.5 million Qwen responses is a separate scored-production project and
requires its own frozen cross-fitting, validation, smoke, and audit contract.
It must not be silently launched from this local reporting workflow.

A future Bayesian hierarchical joint model could couple negative-binomial
length with robust continuous surprisal and correlated child effects. PyMC,
Bambi, Stan, and brms are not currently installed in the project environment,
so this is a deliberate later dependency decision rather than an implicit part
of the first production run.

## Interpretation rules

- Do not say shorter is universally better.
- Do not describe exact-string response entropy as semantic uncertainty.
- Do not treat Qwen expected length as an ordinary confound in every model.
- Do not call raw Qwen nondominance proof of a meaning-preserving optimum.
- Keep k0, k3, context support, and bits per token separate.
- Show raw distributions and support alongside adjusted predictions.
- Label the all-79 analysis descriptive and developmental.
- Preserve contrary or estimator-sensitive findings as results.

## Completion gate

The final marker is:

```text
results/full79_joint_efficiency_analysis/
  FULL79_JOINT_EFFICIENCY_COMPLETE_AND_AUDITED
```

It may be written only after the final audit verifies every stage manifest,
all registered model statuses, every figure and report link, all 79 children,
all 13 corpora, all eligible observed rows, the 645,524-context Qwen join, and
the browser report's binding to frozen outputs.
