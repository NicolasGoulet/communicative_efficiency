# Route 1 Phoneme Fixed-Effort Line Audit

This audit checks whether the current Route 1 phoneme fixed-effort plots use the requested data-supported phoneme utterance sizes.

## Answer

Yes for the current real-child corrected source-specific Atlas: phoneme effort lines use the 12 most frequent exact phoneme counts in the real-child rows, ordered and split into three groups of four.

- Selected exact phoneme counts: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
- Current Atlas groups: low = 2-5, middle = 6-9, high = 10-13
- Source-specific nuance: generated baselines choose their own top 12 values from their generated utterance distributions.

## Selection Proof

![Top 12 phoneme frequency audit](../figs/route1_phoneme_effort_line_audit/real_phoneme_top12_frequency_audit.png)

### Current Atlas Bin Definitions

| atlas_bin | fixed_values | support_rows | support_children | rule |
| --- | --- | --- | --- | --- |
| low representative sizes | 2, 3, 4, 5 | 525210 | 21 | Ordered split of the 12 most frequent observed exact values. |
| middle representative sizes | 6, 7, 8, 9 | 356739 | 21 | Ordered split of the 12 most frequent observed exact values. |
| high representative sizes | 10, 11, 12, 13 | 221985 | 21 | Ordered split of the 12 most frequent observed exact values. |

### Top 12 Real-Child Phoneme Counts

| effort_value | rows | pct_rows | n_children | n_age_bins | age_min | age_max | frequency_rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 58082 | 12.99 | 21 | 8 | 11.1 | 62.4 | 1 |
| 3 | 46836 | 10.48 | 21 | 8 | 11.7 | 62.4 | 2 |
| 4 | 36656 | 8.2 | 21 | 8 | 11.7 | 62.4 | 3 |
| 5 | 33496 | 7.49 | 21 | 8 | 11.7 | 62.4 | 4 |
| 6 | 32426 | 7.25 | 21 | 8 | 11.7 | 62.4 | 5 |
| 7 | 32405 | 7.25 | 21 | 8 | 11.9 | 62.4 | 6 |
| 8 | 29827 | 6.67 | 21 | 8 | 11.7 | 62.4 | 7 |
| 9 | 24255 | 5.43 | 21 | 8 | 12.7 | 62.4 | 8 |
| 10 | 22351 | 5.0 | 21 | 8 | 11.9 | 62.4 | 9 |
| 11 | 20107 | 4.5 | 21 | 8 | 12.9 | 62.4 | 10 |
| 12 | 17339 | 3.88 | 21 | 8 | 11.9 | 62.4 | 11 |
| 13 | 14198 | 3.18 | 21 | 8 | 15.2 | 62.4 | 12 |

## Main Model Slopes Under Phoneme Effort

![Phoneme main model slope audit](../figs/route1_phoneme_effort_line_audit/real_k3_phoneme_main_model_slope_audit.png)

| model_id | fixed_effort_value | slope_bits_per_month | slope_bits_per_6_months | direction |
| --- | --- | --- | --- | --- |
| M4c | 2 | -0.0897 | -0.538 | downward |
| M4c | 3 | -0.0869 | -0.522 | downward |
| M4c | 4 | -0.0842 | -0.505 | downward |
| M4c | 5 | -0.0815 | -0.489 | downward |
| M4c | 6 | -0.0787 | -0.472 | downward |
| M4c | 7 | -0.076 | -0.456 | downward |
| M4c | 8 | -0.0733 | -0.44 | downward |
| M4c | 9 | -0.0706 | -0.423 | downward |
| M4c | 10 | -0.0678 | -0.407 | downward |
| M4c | 11 | -0.0651 | -0.391 | downward |
| M4c | 12 | -0.0624 | -0.374 | downward |
| M4c | 13 | -0.0597 | -0.358 | downward |
| M5 | 2 | -0.0851 | -0.511 | downward |
| M5 | 3 | -0.0818 | -0.491 | downward |
| M5 | 4 | -0.0785 | -0.471 | downward |
| M5 | 5 | -0.0752 | -0.451 | downward |
| M5 | 6 | -0.0718 | -0.431 | downward |
| M5 | 7 | -0.0685 | -0.411 | downward |
| M5 | 8 | -0.0652 | -0.391 | downward |
| M5 | 9 | -0.0618 | -0.371 | downward |
| M5 | 10 | -0.0585 | -0.351 | downward |
| M5 | 11 | -0.0552 | -0.331 | downward |
| M5 | 12 | -0.0519 | -0.311 | downward |
| M5 | 13 | -0.0485 | -0.291 | downward |

## Existing Atlas Plot To Read

The corresponding current main candidate plot is:

![Real k3 M4c phoneme fixed-effort Atlas](../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_phonemes_fixed_effort_atlas.png)

## Files Used

```text
src/build_route1_source_specific_m1_m6_fixed_effort_atlas.py
results/route1_source_specific_corrected_fixed_effort_atlas/real/fixed_effort_bin_definitions.csv
results/route1_source_specific_corrected_fixed_effort_atlas/real/fixed_slice_slopes.csv
results/effort_slice_audit/effort_value_distribution.csv
```
