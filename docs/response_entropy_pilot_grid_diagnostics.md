# Response-Space Entropy Pilot Diagnostics

This report audits the sampled-response pilot before any production-scale
response entropy run. It focuses on output quality, entropy stability, and
temperature sensitivity.

## Completion Audit

| sample_rows_observed | unique_contexts_observed | temperatures_observed | expected_contexts | expected_temperatures | samples_per_context | expected_rows | complete_context_temperature_pairs | expected_context_temperature_pairs | missing_or_incomplete_pairs | is_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.88e+05 | 480 | 0.3,0.5,0.7,1.0,1.3,1.6 | 480 | 0.3,0.5,0.7,1.0,1.3,1.6 | 100 | 2.88e+05 | 2880 | 2880 | 0 | True |

**How to read this table.** The pilot is final only if `is_complete` is true:
all selected contexts must have all planned temperatures and all planned
samples per context. If this is false, the report is a partial/debug report and
should not be used to choose production settings.

## Output Quality By Temperature

| temperature | contexts | mean_sample_count | min_sample_count | mean_entropy_mm_bits | sd_entropy_mm_bits | mean_unique_response_count | mean_top_response_probability | mean_empty_response_rate | mean_hit_max_new_tokens_rate | mean_stopped_by_boundary_rate | mean_sample_word_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 480 | 100 | 100 | 3.82 | 1.498 | 32.32 | 0.3525 | 0.007146 | 1 | 0.838 | 5.827 |
| 0.5 | 480 | 100 | 100 | 5.553 | 1.151 | 60.36 | 0.1883 | 0.007271 | 1 | 0.7863 | 6.506 |
| 0.7 | 480 | 100 | 100 | 6.607 | 0.6239 | 81.26 | 0.0946 | 0.007917 | 1 | 0.7098 | 7.505 |
| 1 | 480 | 100 | 100 | 7.203 | 0.2216 | 95.81 | 0.0371 | 0.007354 | 1 | 0.4786 | 10.38 |
| 1.3 | 480 | 100 | 100 | 7.292 | 0.1554 | 98.45 | 0.02508 | 0.007292 | 1 | 0.1288 | 14.03 |
| 1.6 | 480 | 100 | 100 | 7.295 | 0.1544 | 98.56 | 0.02435 | 0.007375 | 0.9999 | 0.0215 | 15.64 |

**How to read this table.** Temperatures with high empty-response rates, high
max-token-hit rates, or very unstable entropy should not be used as primary
measurement settings. Boundary-stop rate is not automatically bad: it can mean
the model naturally moved to the next speaker turn and the cleaner truncated it.

![quality rates by temperature](../figs/response_entropy_pilot_grid/pilot_quality_rates_by_temperature.png)

## Entropy Distributions

![entropy distributions by temperature](../figs/response_entropy_pilot_grid/pilot_entropy_distribution_by_temperature.png)

**How to read this plot.** Higher temperatures should usually increase entropy.
If entropy saturates near the sample cap or stops varying by context, that
temperature may be measuring decoding noise rather than contextual uncertainty.

## Split-Half Reliability

| temperature | contexts | pearson_r | spearman_r | mean_abs_diff_bits | median_abs_diff_bits |
| --- | --- | --- | --- | --- | --- |
| 0.3 | 480 | 0.9288 | 0.9257 | 0.4008 | 0.3325 |
| 0.5 | 480 | 0.8872 | 0.8553 | 0.3587 | 0.2754 |
| 0.7 | 480 | 0.7387 | 0.6881 | 0.2799 | 0.181 |
| 1 | 480 | 0.2118 | 0.3839 | 0.1591 | 0.05443 |
| 1.3 | 480 | -0.1112 | -0.07664 | 0.1274 | 0 |
| 1.6 | 480 | -0.1134 | -0.1137 | 0.1252 | 0 |

![split-half reliability](../figs/response_entropy_pilot_grid/pilot_split_half_reliability.png)

**How to read this plot.** High Spearman correlation means the ranking of
contexts by response entropy is similar in the first and second half of the
samples. Low reliability means more samples or a different decoding setting may
be needed.

## Downsample Stability

| sample_size | temperature | contexts | pearson_r_vs_full | spearman_r_vs_full | mean_abs_diff_bits_vs_full |
| --- | --- | --- | --- | --- | --- |
| 25 | 0.3 | 480 | 0.9229 | 0.9103 | 0.7483 |
| 25 | 0.5 | 480 | 0.8239 | 0.8402 | 1.282 |
| 25 | 0.7 | 480 | 0.6742 | 0.8003 | 1.782 |
| 25 | 1 | 480 | 0.7513 | 0.6441 | 2.099 |
| 25 | 1.3 | 480 | 0.9761 | 0.6994 | 2.165 |
| 25 | 1.6 | 480 | 0.9796 | 0.7432 | 2.167 |
| 50 | 0.3 | 480 | 0.9798 | 0.9782 | 0.344 |
| 50 | 0.5 | 480 | 0.9646 | 0.9549 | 0.5867 |
| 50 | 0.7 | 480 | 0.9207 | 0.9214 | 0.8348 |
| 50 | 1 | 480 | 0.864 | 0.8037 | 1.004 |
| 50 | 1.3 | 480 | 0.9783 | 0.7271 | 1.048 |
| 50 | 1.6 | 480 | 0.9797 | 0.7432 | 1.049 |
| 75 | 0.3 | 480 | 0.9942 | 0.9931 | 0.1651 |
| 75 | 0.5 | 480 | 0.9908 | 0.988 | 0.244 |
| 75 | 0.7 | 480 | 0.9804 | 0.9714 | 0.3338 |
| 75 | 1 | 480 | 0.9497 | 0.8735 | 0.4027 |
| 75 | 1.3 | 480 | 0.9794 | 0.7589 | 0.4241 |
| 75 | 1.6 | 480 | 0.9797 | 0.7469 | 0.4244 |
| 100 | 0.3 | 480 | 1 | 1 | 0 |
| 100 | 0.5 | 480 | 1 | 1 | 0 |
| 100 | 0.7 | 480 | 1 | 1 | 0 |
| 100 | 1 | 480 | 1 | 1 | 0 |
| 100 | 1.3 | 480 | 1 | 1 | 0 |
| 100 | 1.6 | 480 | 1 | 1 | 0 |

![downsample stability](../figs/response_entropy_pilot_grid/pilot_downsample_stability.png)

**How to read this plot.** If M=50 already matches M=100 closely, production
could potentially use fewer samples. If M=100 is still unstable, the pilot
argues for more samples or more robust predictors.

## Temperature Rank Correlation

| temperature_row | 0.3 | 0.5 | 0.7 | 1.0 | 1.3 | 1.6 |
| --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 1 | 0.8834 | 0.6578 | 0.2836 | -0.01423 | -0.0292 |
| 0.5 | 0.8834 | 1 | 0.8464 | 0.4287 | 0.09411 | 0.05261 |
| 0.7 | 0.6578 | 0.8464 | 1 | 0.6374 | 0.2779 | 0.2209 |
| 1 | 0.2836 | 0.4287 | 0.6374 | 1 | 0.6321 | 0.5813 |
| 1.3 | -0.01423 | 0.09411 | 0.2779 | 0.6321 | 1 | 0.9063 |
| 1.6 | -0.0292 | 0.05261 | 0.2209 | 0.5813 | 0.9063 | 1 |

![temperature rank correlation](../figs/response_entropy_pilot_grid/pilot_temperature_rank_correlation.png)

**How to read this plot.** High correlations mean temperatures mostly rank
contexts similarly. Low correlations mean temperature is not just a sensitivity
check: it changes the measurement object substantially.

## Files

- Context-temperature features: `results/response_entropy_pilot_grid/pilot_context_temperature_features.csv`
- Completion audit: `results/response_entropy_pilot_grid/pilot_completion_audit.csv`
- Quality by temperature: `results/response_entropy_pilot_grid/pilot_quality_by_temperature.csv`
- Split-half reliability: `results/response_entropy_pilot_grid/pilot_split_half_reliability.csv`
- Downsample stability: `results/response_entropy_pilot_grid/pilot_downsample_stability.csv`
- Temperature correlations: `results/response_entropy_pilot_grid/pilot_temperature_rank_correlations.csv`
- Figure manifest: `results/response_entropy_pilot_grid/pilot_diagnostic_figure_manifest.csv`
