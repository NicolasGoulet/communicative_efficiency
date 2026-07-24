# TinyDialogues PBM: Visual Direct-Surprisal Summary

This is the short, plot-led report. It keeps the scientific decisions visible
and sends full coefficient tables, bootstrap draws, and diagnostics to saved
CSV files. A negative P1 slope means the scorer finds older children's observed
utterances more predictable at the same exact/top-coded word effort. It is not
proof of a universal efficiency optimum.

## What We Found

- **PBM discovery (21 children):** P1 = -0.222 bits/month, 95% CI [-0.311, -0.132]; is a discovery/scorer-robustness estimate.
- Context-gain development is negative in 1/1 displayed samples, opposite the frozen positive prediction wherever the interval excludes zero.

![Headline fixed-effort age slopes](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/headline_primary_age_slopes.png)

## The Three Frozen Questions

| sample | question | slope per month | 95% interval | protocol reading |
| --- | --- | ---: | ---: | --- |
| PBM discovery (21 children) | Contextual predictability (k3) | -0.222 | [-0.311, -0.132] | expected direction interval excludes zero |
| PBM discovery (21 children) | Unconditional form predictability (k0) | -0.254 | [-0.339, -0.168] | decomposition no directional rule |
| PBM discovery (21 children) | Context support (k0 − k3) | -0.032 | [-0.050, -0.014] | contrary direction interval excludes zero |

Context gain is `k0 - k3`: positive values mean the preceding context supports
the observed utterance under this scorer. The slope asks whether that support
changes with age.

## What The Raw Data Look Like

The lines are age-bin means and the shaded regions span the 10th to 90th
percentiles. They are descriptive; the fixed-effort models come afterward.

![Raw age-bin trajectories](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/raw_age_bin_trajectories.png)

## Do The Conclusions Depend On The Estimator?

The first row for each scope is the frozen child-fixed, child-clustered model.
Other rows are nonlinear, within/between, GEE, word-effort, tail-trim, and
mixed-effects sensitivities. Mixed models use unweighted design cells and are
therefore sensitivity estimands, not replacements for the primary model.

![P1 estimator robustness](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/p1_estimator_robustness.png)

This staged run records **31 passing fits**, **3 singular/boundary fits**, **0 nonconverged fits**, and **0 failed fits**. Nonconvergence and singularity are retained as results of the sensitivity audit; they are not hidden.

## Resampling And Influence Checks

Child bootstrap and corpus bootstrap show how the estimate changes when whole
sampling units are resampled. The age-permutation distribution is a falsification
reference created by scrambling age within children. In the influence plot, the
bar spans all leave-one-unit estimates and the red point is the full estimate.

![P1 resampling checks](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/p1_resampling_checks.png)

![P1 influence ranges](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/p1_influence_ranges.png)

## Development Across Frozen Age Bins

These are differences from 006–023 months at fixed lexical effort. They do not
by themselves establish a sustained onset.

![P1 age-bin contrasts](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/p1_age_bin_contrasts.png)

## Real Children Versus Generated N-Gram Candidates

These plots use candidate-minus-real score gaps. Random and n-gram utterances
are same-length controls, not same-meaning alternatives.

![Candidate-gap age slopes](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/candidate_gap_age_slopes.png)

## How Different Are Individual Children?

Each dot is one supported child-specific slope; the thick bar is the median.
The individual slopes are descriptive and not multiplicity-adjusted.

![Child slope distribution](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/child_slope_distribution.png)

[Open the individual-child trajectory gallery](tinydialogues_pbm_child_gallery.html)

## Child And Caregiver Input

Caregiver trajectories are indexed by child age and describe input adaptation;
they are not an adult developmental endpoint.

![Child and caregiver trajectories](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/child_caretaker_trajectories.png)

## Coverage Before Interpretation

Darker cells contain more observed utterances. Empty cells are genuine age
coverage gaps; plotted lines should not be read as observations there.

![coverage_pbm_discovery](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/coverage_pbm_discovery.png)

## What This Scorer Cannot Answer Yet

![Model-family coverage](../figs/direct_surprisal_replication/tinydialogues_pbm/modular_visual/model_family_coverage.png)

- Scorer-specific next-token entropy/top-k models require a separate entropy handoff.
- LSTM comparisons require the LSTM candidates to be scored by this scorer.
- Response-space and semantic-entropy analyses require separately frozen sampled responses.
- Corrected Bayes candidate-set probabilities and direct neural surprisal are different estimands.

## Detailed Audit Files

- Model status and headline coefficients: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/model_summaries.csv`
- Full coefficients: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/coefficients_long.csv`
- Child bootstrap: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/child_bootstrap_summary.csv`
- Corpus bootstrap: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/corpus_bootstrap_summary.csv`
- Age permutation draws: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/age_permutation_draws.csv.gz`
- Leave-one-child/corpus influence: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/leave_one_cluster_out.csv`
- Model-family coverage and blockers: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/model_coverage.csv`
- Child trajectories: `results/direct_surprisal_replication/tinydialogues_pbm/modular/models/child_age_session_trajectories.csv.gz`
- Dataset flow and coverage: `results/direct_surprisal_replication/tinydialogues_pbm/modular/prepared`
