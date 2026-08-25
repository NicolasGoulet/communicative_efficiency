# Conditional joint efficiency in child responses

## What this analysis asks

Longer is not automatically worse. The analysis estimates the joint policy of
response length and scorer predictability conditional on conversational demand
and child age. It combines 1,122,396 child utterances from 79 children with the
complete 100-response Qwen cloud for each of 645,524 contexts.

## Main results

1. **Absolute length adapts only modestly to exact-string response entropy.** At
   42 months, the pooled M1 predicted length ratio from entropy p10 to p90 is
   1.028 (95% CI 1.014–1.043). The PBM discovery ratio is 1.042 (95% CI 1.026–1.059); the
   other-58 confirmation ratio is 1.017 (95% CI 0.999–1.037).
2. **Relative effort reverses with development.** At 42 months, the pooled M4
   effort-percentile odds ratio is 0.931 (95% CI 0.902–0.962), with the same direction
   in PBM discovery (0.871 (95% CI 0.830–0.915)) and other-58 confirmation
   (0.939 (95% CI 0.905–0.976)). Near 18 months the adjusted direction is positive;
   later it is mostly negative or weak. The simple prediction that children
   always lengthen *relative to Qwen* as entropy rises is therefore not supported.
3. **At fixed exact effort, older speech is more predictable for common short
   lengths.** For two-word utterances, the pooled supported-range age contrast
   is -3.47 bits (95% CI -4.84 to -2.10); PBM discovery is -5.77 bits (95% CI -10.54 to -1.01) and the other-58
   confirmation result is -2.34 bits (95% CI -3.96 to -0.71). Longer, sparse cells are visibly
   less stable and are not generalized.
4. **Same-length generated comparison adds a different result.** Child targets
   remain more surprising than Qwen's median generated response at the same
   length in raw summaries. Under high response entropy, M5 estimates a
   developmental reduction of 2.56 bits
   (95% CI -3.89 to -1.24). This is a
   model-relative form comparison, not evidence that generated alternatives
   preserve what the child meant.

## Interpretation boundary

- Mistral surprisal is scorer self-information: lower means more predictable,
  not “more Shannon information transmitted.”
- Response entropy is exact-string entropy under one Qwen prompt and sampling
  procedure. It is not semantic uncertainty.
- Raw Qwen nondominance is secondary. It is not a Pareto-optimality claim and
  does not preserve intended meaning.
- Pooled all-79 estimates are descriptive. Brown/Manchester/Providence are
  discovery; the other 58 children are confirmation.
- The corrected PBM Bayes result decomposes a cross-fitted prior and context
  evidence over a supplied candidate set. It is separate from the GAMMs.

## Figures

### Developmental distributions

![Developmental distributions](../figs/full79_joint_efficiency_analysis/01_developmental_distributions.png)

Child-balanced raw trajectories for effort, Qwen-relative position, exact-length k3 gap, and the secondary nondominance flag.

### Adjusted response-length adaptation

![Adjusted response-length adaptation](../figs/full79_joint_efficiency_analysis/02_m1_entropy_lines.png)

Negative-binomial GAMM predictions show how absolute response length changes with exact-string response entropy at several ages and in each frozen sample role.

### Pooled joint length policy

![Pooled joint length policy](../figs/full79_joint_efficiency_analysis/03_m1_policy_surface.png)

One pooled surface for the conditional length policy over developmental age and response-space uncertainty.

### Generated expected-length sensitivity

![Generated expected-length sensitivity](../figs/full79_joint_efficiency_analysis/04_m2_qwen_reference.png)

Sensitivity surfaces add Qwen expected response length; this is a distinct reference-adjusted estimand, not the primary total association.

### Observed versus generated expected length

![Observed versus generated expected length](../figs/full79_joint_efficiency_analysis/05_length_calibration.png)

Observed length is compared with the complete generated length distribution rather than only one generated mean.

### Paper-inspired model × length × age atlas

![Paper-inspired model × length × age atlas](../figs/full79_joint_efficiency_analysis/06_paper_information_effort_atlas.png)

Every age panel contains every source and exact length 1–12: x is effort and y is contextual Mistral surprisal.

### Fixed-effort contextual surprisal

![Fixed-effort contextual surprisal](../figs/full79_joint_efficiency_analysis/07_m3_fixed_effort_surfaces.png)

The nonlinear age-by-length surface directly tests predictability at fixed exact effort in pooled, discovery, and confirmation scopes.

### Joint context-relative phase portrait

![Joint context-relative phase portrait](../figs/full79_joint_efficiency_analysis/08_joint_phase_portrait.png)

Child-age cells jointly locate effort percentile and surprisal percentile inside their context-matched generated response spaces.

### Relative effort by uncertainty and age

![Relative effort by uncertainty and age](../figs/full79_joint_efficiency_analysis/09_m4_relative_effort.png)

The Qwen-relative effort response to entropy reverses over development instead of following one universal increasing line.

### Exact-length gap and raw nondominance

![Exact-length gap and raw nondominance](../figs/full79_joint_efficiency_analysis/10_gap_and_nondominance.png)

Exact-length comparison is kept separate from raw nondominance; neither generated reference preserves intended meaning.

### Child-specific developmental heterogeneity

![Child-specific developmental heterogeneity](../figs/full79_joint_efficiency_analysis/11_child_heterogeneity.png)

Shrunken child-specific age and entropy responses show why a pooled mean is incomplete.

### Corrected PBM Bayes sidecar

![Corrected PBM Bayes sidecar](../figs/full79_joint_efficiency_analysis/12_bayes_decomposition.png)

Cross-fitted PBM priors and context evidence are a decomposition sidecar, not a Bayesian hierarchical fit and not all-79 evidence.

### Model diagnostics

![Model diagnostics](../figs/full79_joint_efficiency_analysis/13_model_diagnostics.png)

Fixed residual samples expose outcome-specific fit structure for the registered nonlinear models.

### Discovery/confirmation contrast forest

![Discovery/confirmation contrast forest](../figs/full79_joint_efficiency_analysis/14_scope_contrasts.png)

Covariance-aware contrasts keep pooled description, PBM discovery, and other-58 confirmation visibly separate.

### Context-matched response-cloud examples

![Context-matched response-cloud examples](../figs/full79_joint_efficiency_analysis/15_context_gallery.png)

Eight complete 100-response examples make the context-matching operation concrete and expose meaning-preservation limits.

### Raw model × length trajectories

![Raw model × length trajectories](../figs/full79_joint_efficiency_analysis/16_raw_model_length_age_lines.png)

This reconstructs the earlier readable 2D logic: every exact length is its own line over age, with a separate panel for each source model.

### Adjusted one-line-per-length trajectories

![Adjusted one-line-per-length trajectories](../figs/full79_joint_efficiency_analysis/17_adjusted_length_age_lines.png)

The registered M3 predictions retain one line per exact length while controlling child identity, corpus, response entropy, and context length.

## Registered analysis

The model stage fitted 15/15 registered `mgcv::bam` models: nine pooled models
and unchanged M1/M3/M4 core models in discovery and confirmation. Every model
contains a child random intercept, child random age slope, child random entropy
slope, and corpus random intercept. Plotting and this report consume saved
tables and never refit models.

## Reproducibility

The independent stages are `datasets → metrics → models → plots → report →
audit`. Each stage has a hash-bound manifest. The final completion marker is
written only after the separate audit checks sample coverage, all 15 models,
all registered figures, report links, and interpretation guardrails.
