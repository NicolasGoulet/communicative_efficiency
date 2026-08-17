# TinyDialogues–Mistral PBM Visual Comparison

This report uses the exact 446,508-row paired PBM intersection. It compares
developmental directions and within-child patterns, not raw model-token scales.
TinyDialogues and Mistral have different tokenizers and calibrations.

## The Short Answer

- Both scorers give negative fixed-effort P1 slopes on the same PBM utterances.
- TinyDialogues gives the more negative P1 magnitude; the paired child-bootstrap
  interval for that difference excludes zero.
- The P3 context-gain slope difference includes zero even though both observed
  slopes are negative.
- Supported child-level P1 slope signs agree for **85.7%** of children.

![All paired outcome slopes](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_all_outcome_slopes.png)

## Three Headline Questions

| question | Tiny slope | Mistral slope | Tiny − Mistral | bootstrap interval |
| --- | ---: | ---: | ---: | ---: |
| Contextual target (k3) | -0.222 | -0.133 | -0.089 | [-0.152, -0.028] |
| Unconditional target (k0) | -0.254 | -0.162 | -0.092 | [-0.168, -0.047] |
| Context support (k3) | -0.032 | -0.030 | -0.003 | [-0.052, 0.023] |

## Where The Scorers Differ

Bars are paired child-bootstrap intervals for TinyDialogues minus Mistral.
Intervals crossing zero do not show a stable slope-magnitude difference.

![Paired slope differences](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_slope_difference_forest.png)

## Do Individual Children Point The Same Way?

Each point is one supported child. Quadrants show sign agreement; distance from
the dashed diagonal shows magnitude disagreement.

![Child slope concordance](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_child_p1_concordance.png)

## Do The Nonlinear Age-Bin Shapes Match?

Both scorers use the same exact paired rows, word-effort design, early-bin
reference, child fixed effects, and child-clustered intervals.

![Paired P1 age bins](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_p1_age_bins.png)

The quadratic-age comparison is a sensitivity analysis rather than a new
primary model. Its paired intervals show whether scorer curvature differs.

![Paired quadratic age differences](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_quadratic_age_differences.png)

## Do The Generated Candidates Keep The Same Ordering?

Candidate-minus-real gaps are same-length controls, not meaning-preserving
alternatives. Smaller gaps mean a candidate is closer to the observed real
utterance on that scorer's scale.

![Paired candidate gap ordering](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_candidate_gap_ordering.png)

## Tokenization And Scale Diagnostics

The left panel audits the recorded evaluated-token counts; their median ratio
is 1.0 throughout this paired export. The right panel still shows a substantial
score-scale difference after dividing by the shared lexical word count, so raw
score magnitudes should not be treated as directly calibrated across scorers.

![Tokenization diagnostics](../figs/direct_surprisal_replication/paired_tiny_mistral_pbm/modular_visual/paired_tokenization_diagnostics.png)

## Detailed Audit Files

- All outcome slopes and paired intervals: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_all_outcome_slopes.csv`
- Bootstrap draws: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_all_outcome_bootstrap_draws.csv.gz`
- Age-bin contrasts: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_age_bin_contrasts.csv`
- Quadratic-age comparison: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_quadratic_age_comparison.csv`
- Candidate rankings: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_candidate_rankings.csv`
- Candidate source-by-age interactions: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_candidate_source_age_interactions.csv`
- Child slope concordance: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_child_slopes.csv`
- Tokenization/scale diagnostics: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_disagreement_diagnostics.csv`
