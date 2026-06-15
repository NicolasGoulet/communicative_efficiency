# Effort Slice Audit For Adjusted Age Plots

This document fixes the plotting issue we identified: a single median-effort
line is only one conditional slice of a fitted model. It is useful, but it is
not enough as the main evidence.

The audit uses the same real-child `k3` modeling rows used by the M1-M6 reports.
It does not refit any M1-M6 model.

## Straight Answer

Use three complementary views:

1. **Exact fixed-effort slices.** These are the strongest visual controls
   because every plotted line corresponds to a concrete effort count.
2. **Low / median / high fixed slices.** These should be quantile anchors such
   as p25/p50/p75 or wider p10/p50/p90, not only one median line.
3. **Low / mid / high effort groups.** These are diagnostic categorical models.
   They are not the same thing as exact fixed-effort control because each group
   contains a range of effort values.

## Saved Outputs

```text
results/effort_slice_audit/effort_quantile_summary.csv
results/effort_slice_audit/effort_value_distribution.csv
results/effort_slice_audit/effort_by_age_bin_distribution.csv
results/effort_slice_audit/effort_level_definitions.csv
results/effort_slice_audit/proposed_fixed_effort_slices.csv
```

## Effort Distributions

![Exact effort value distributions](../figs/effort_slice_audit/effort_value_distributions.png)

| effort_label | rows | mean | sd | p10 | p25 | p33 | p50 | p66 | p75 | p90 | p95 | p99 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | 446985 | 2.66 | 2.02 | 1 | 1 | 1 | 2 | 3 | 4 | 5 | 6 | 10 | 70 |
| Morphemes | 446985 | 2.96 | 2.32 | 1 | 1 | 1 | 2 | 3 | 4 | 6 | 7 | 11 | 98 |
| Syllables: CMU/pkg | 446985 | 3.24 | 2.48 | 1 | 1 | 2 | 3 | 4 | 4 | 6 | 8 | 12 | 84 |
| Syllables: pkg | 446985 | 3.43 | 2.64 | 1 | 1 | 2 | 3 | 4 | 5 | 7 | 8 | 12 | 84 |
| Phonemes | 446985 | 8.04 | 6.22 | 2 | 3 | 4 | 7 | 9 | 11 | 16 | 19 | 29 | 266 |

## How Low / Mid / High Effort Is Currently Defined

For each effort unit separately, we compute the empirical 33rd and 66th
percentiles. Then:

```text
low effort  = value <= p33
high effort = value >= p66
mid effort  = values between p33 and p66
```

Because effort counts are integers, these groups can be uneven. If p33 and p66
fall around the same integer, the mid group can become very narrow. This is why
low/mid/high effort groups should be treated as a diagnostic view, not the only
evidence.

| effort_label | effort_level | rule | rows | pct_rows | min_value | median_value | max_value | n_children | n_age_bins |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | low effort | value <= p33 (1.00) | 164264 | 0.367 | 1 | 1 | 1 | 21 | 8 |
| Words | mid effort | p33 < value < p66 (1.00 to 3.00) | 93824 | 0.21 | 2 | 2 | 2 | 21 | 8 |
| Words | high effort | value >= p66 (3.00) | 188897 | 0.423 | 3 | 4 | 70 | 21 | 8 |
| Morphemes | low effort | value <= p33 (1.00) | 153917 | 0.344 | 1 | 1 | 1 | 21 | 8 |
| Morphemes | mid effort | p33 < value < p66 (1.00 to 3.00) | 81932 | 0.183 | 2 | 2 | 2 | 21 | 8 |
| Morphemes | high effort | value >= p66 (3.00) | 211136 | 0.472 | 3 | 4 | 98 | 21 | 8 |
| Syllables: CMU/pkg | low effort | value <= p33 (2.00) | 216253 | 0.484 | 1 | 1 | 2 | 21 | 8 |
| Syllables: CMU/pkg | mid effort | p33 < value < p66 (2.00 to 4.00) | 72346 | 0.162 | 3 | 3 | 3 | 21 | 8 |
| Syllables: CMU/pkg | high effort | value >= p66 (4.00) | 158386 | 0.354 | 4 | 5 | 84 | 21 | 8 |
| Syllables: pkg | low effort | value <= p33 (2.00) | 204338 | 0.457 | 1 | 1 | 2 | 21 | 8 |
| Syllables: pkg | mid effort | p33 < value < p66 (2.00 to 4.00) | 67784 | 0.152 | 3 | 3 | 3 | 21 | 8 |
| Syllables: pkg | high effort | value >= p66 (4.00) | 174863 | 0.391 | 4 | 5 | 84 | 21 | 8 |
| Phonemes | low effort | value <= p33 (4.00) | 152639 | 0.341 | 1 | 3 | 4 | 21 | 8 |
| Phonemes | mid effort | p33 < value < p66 (4.00 to 9.00) | 128154 | 0.287 | 5 | 6 | 8 | 21 | 8 |
| Phonemes | high effort | value >= p66 (9.00) | 166192 | 0.372 | 9 | 12 | 266 | 21 | 8 |

## Proposed Fixed Effort Slices

### Mandatory Exact Word And Morpheme Slices

These implement the decision to show words and morphemes from 1 to 12.

| effort | values | supported_values |
| --- | --- | --- |
| Words | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 |
| Morphemes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 |
| Syllables: CMU/pkg |  |  |
| Syllables: pkg |  |  |
| Phonemes |  |  |

### Primary Low / Median / High Fixed Slices

These are p25/p50/p75 anchors. They are a cleaner replacement for a single
median line when we want only three lines.

| effort | values | supported_values |
| --- | --- | --- |
| Words | 1, 2, 4 | 1, 2, 4 |
| Morphemes | 1, 2, 4 | 1, 2, 4 |
| Syllables: CMU/pkg | 1, 3, 4 | 1, 3, 4 |
| Syllables: pkg | 1, 3, 5 | 1, 3, 5 |
| Phonemes | 3, 7, 11 | 3, 7, 11 |

### Wider Low / Median / High Fixed Slices

These are p10/p50/p90 anchors. They are useful when p25/p75 are too close and
we want to visibly stress-test the trajectory at small versus large utterances.

| effort | values | supported_values |
| --- | --- | --- |
| Words | 1, 2, 5 | 1, 2, 5 |
| Morphemes | 1, 2, 6 | 1, 2, 6 |
| Syllables: CMU/pkg | 1, 3, 6 | 1, 3, 6 |
| Syllables: pkg | 1, 3, 7 | 1, 3, 7 |
| Phonemes | 2, 7, 16 | 2, 7, 16 |

### Data-Supported Dense Core

These are exact effort values with enough support to be plotted without relying
on tiny cells. Current support rule:

```text
at least 500 rows, at least 10 children, at least 6 age bins, and not above p95
```

| effort | values | supported_values |
| --- | --- | --- |
| Words | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 |
| Morphemes | 1, 2, 3, 4, 5, 6, 7 | 1, 2, 3, 4, 5, 6, 7 |
| Syllables: CMU/pkg | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8 |
| Syllables: pkg | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8 |
| Phonemes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 |

## Support Preview For Key Proposed Values

| effort_label | proposal_set | fixed_effort_value | rows | n_children | n_age_bins | meets_support_rule |
| --- | --- | --- | --- | --- | --- | --- |
| Morphemes | primary_low_median_high_p25_p50_p75 | 1 | 153917 | 21 | 8 | True |
| Morphemes | primary_low_median_high_p25_p50_p75 | 2 | 81932 | 21 | 8 | True |
| Morphemes | primary_low_median_high_p25_p50_p75 | 4 | 52894 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 1 | 153917 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 2 | 81932 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 3 | 69111 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 4 | 52894 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 5 | 35618 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 6 | 21774 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 7 | 12587 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 8 | 7378 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 9 | 4295 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 10 | 2526 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 11 | 1568 | 21 | 8 | True |
| Morphemes | requested_dense_1_12 | 12 | 1020 | 21 | 8 | True |
| Morphemes | wide_low_median_high_p10_p50_p90 | 1 | 153917 | 21 | 8 | True |
| Morphemes | wide_low_median_high_p10_p50_p90 | 2 | 81932 | 21 | 8 | True |
| Morphemes | wide_low_median_high_p10_p50_p90 | 6 | 21774 | 21 | 8 | True |
| Phonemes | primary_low_median_high_p25_p50_p75 | 3 | 46836 | 21 | 8 | True |
| Phonemes | primary_low_median_high_p25_p50_p75 | 7 | 32405 | 21 | 8 | True |
| Phonemes | primary_low_median_high_p25_p50_p75 | 11 | 20107 | 21 | 8 | True |
| Phonemes | wide_low_median_high_p10_p50_p90 | 2 | 58082 | 21 | 8 | True |
| Phonemes | wide_low_median_high_p10_p50_p90 | 7 | 32405 | 21 | 8 | True |
| Phonemes | wide_low_median_high_p10_p50_p90 | 16 | 8327 | 21 | 8 | True |
| Syllables: CMU/pkg | primary_low_median_high_p25_p50_p75 | 1 | 121839 | 21 | 8 | True |
| Syllables: CMU/pkg | primary_low_median_high_p25_p50_p75 | 3 | 72346 | 21 | 8 | True |
| Syllables: CMU/pkg | primary_low_median_high_p25_p50_p75 | 4 | 55990 | 21 | 8 | True |
| Syllables: CMU/pkg | wide_low_median_high_p10_p50_p90 | 1 | 121839 | 21 | 8 | True |
| Syllables: CMU/pkg | wide_low_median_high_p10_p50_p90 | 3 | 72346 | 21 | 8 | True |
| Syllables: CMU/pkg | wide_low_median_high_p10_p50_p90 | 6 | 25149 | 21 | 8 | True |
| Syllables: pkg | primary_low_median_high_p25_p50_p75 | 1 | 116868 | 21 | 8 | True |
| Syllables: pkg | primary_low_median_high_p25_p50_p75 | 3 | 67784 | 21 | 8 | True |
| Syllables: pkg | primary_low_median_high_p25_p50_p75 | 5 | 40416 | 21 | 8 | True |
| Syllables: pkg | wide_low_median_high_p10_p50_p90 | 1 | 116868 | 21 | 8 | True |
| Syllables: pkg | wide_low_median_high_p10_p50_p90 | 3 | 67784 | 21 | 8 | True |
| Syllables: pkg | wide_low_median_high_p10_p50_p90 | 7 | 17456 | 21 | 8 | True |
| Words | primary_low_median_high_p25_p50_p75 | 1 | 164264 | 21 | 8 | True |
| Words | primary_low_median_high_p25_p50_p75 | 2 | 93824 | 21 | 8 | True |
| Words | primary_low_median_high_p25_p50_p75 | 4 | 49421 | 21 | 8 | True |
| Words | requested_dense_1_12 | 1 | 164264 | 21 | 8 | True |
| Words | requested_dense_1_12 | 2 | 93824 | 21 | 8 | True |
| Words | requested_dense_1_12 | 3 | 74048 | 21 | 8 | True |
| Words | requested_dense_1_12 | 4 | 49421 | 21 | 8 | True |
| Words | requested_dense_1_12 | 5 | 28966 | 21 | 8 | True |
| Words | requested_dense_1_12 | 6 | 15966 | 21 | 8 | True |
| Words | requested_dense_1_12 | 7 | 8606 | 21 | 8 | True |
| Words | requested_dense_1_12 | 8 | 4725 | 21 | 8 | True |
| Words | requested_dense_1_12 | 9 | 2656 | 21 | 8 | True |
| Words | requested_dense_1_12 | 10 | 1594 | 21 | 8 | True |
| Words | requested_dense_1_12 | 11 | 896 | 21 | 8 | True |
| Words | requested_dense_1_12 | 12 | 591 | 20 | 8 | True |
| Words | wide_low_median_high_p10_p50_p90 | 1 | 164264 | 21 | 8 | True |
| Words | wide_low_median_high_p10_p50_p90 | 2 | 93824 | 21 | 8 | True |
| Words | wide_low_median_high_p10_p50_p90 | 5 | 28966 | 21 | 8 | True |

## Recommendation

For the next M1-M6 figures:

- use **1-12 exact slices** for words and morphemes;
- use **distribution-supported dense-core values** for syllables and phonemes;
- include **p25/p50/p75** and optionally **p10/p50/p90** versions as compact
  low/median/high summaries;
- keep low/mid/high categorical models, but label them as coarse diagnostics.

This is more granular and safer than median-only plotting.
