# Paired PBM Direct-Surprisal Scorer Comparison

This report compares `tinydialogues_pbm` and `mistral_full79` on exactly paired Brown, Manchester, and Providence utterances. It is a scorer-robustness analysis on the discovery sample, not an independent sample replication.

## Join Audit

| left_scorer | right_scorer | paired_rows | children | corpora | join_mismatches | explained_join_mismatches | unexplained_join_mismatches | join_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tinydialogues_pbm | mistral_full79 | 446508.000 | 21.000 | 3.000 | 477.000 | 477.000 | 0.000 | PASS_WITH_EXPLAINED_COVERAGE_DIFFERENCE |

No paired analysis is valid unless the unexplained mismatch count is zero. A declared source-version coverage difference may be retained in the mismatch table, but only the exact intersection is analyzed. Target and context identity is checked using source fields and SHA-256 hashes, not row position.

## Paired Score Agreement

| scope | outcome | paired_rows | children | pearson | spearman | within_child_pearson | within_child_spearman | same_sign_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_pbm | real_k0_sum_bits | 446508.000 | 21.000 | 0.857 | 0.895 | 0.850 | 0.886 | 1.000 |
| all_pbm | real_k1_sum_bits | 446508.000 | 21.000 | 0.823 | 0.836 | 0.815 | 0.830 | 1.000 |
| all_pbm | real_k2_sum_bits | 446508.000 | 21.000 | 0.808 | 0.820 | 0.800 | 0.812 | 1.000 |
| all_pbm | real_k3_sum_bits | 446508.000 | 21.000 | 0.801 | 0.811 | 0.793 | 0.803 | 1.000 |
| all_pbm | real_context_gain_k1 | 446508.000 | 21.000 | 0.199 | 0.154 | 0.200 | 0.155 | 0.450 |
| all_pbm | real_context_gain_k2 | 446508.000 | 21.000 | 0.198 | 0.167 | 0.198 | 0.168 | 0.452 |
| all_pbm | real_context_gain_k3 | 446508.000 | 21.000 | 0.179 | 0.157 | 0.180 | 0.158 | 0.457 |
| all_pbm | random_minus_real_k3_bits | 446508.000 | 21.000 | 0.906 | 0.875 | 0.902 | 0.883 | 0.939 |
| all_pbm | unigram_minus_real_k3_bits | 446508.000 | 21.000 | 0.741 | 0.740 | 0.738 | 0.746 | 0.806 |
| all_pbm | bigram_minus_real_k3_bits | 446508.000 | 21.000 | 0.676 | 0.691 | 0.674 | 0.696 | 0.768 |
| all_pbm | trigram_minus_real_k3_bits | 446508.000 | 21.000 | 0.636 | 0.659 | 0.634 | 0.666 | 0.720 |
| all_pbm | real_bits_per_word_k3 | 446508.000 | 21.000 | 0.670 | 0.665 | 0.671 | 0.665 | 1.000 |
| all_pbm | real_bits_per_character_k3 | 446508.000 | 21.000 | 0.664 | 0.618 | 0.663 | 0.617 | 1.000 |

Within-child correlations remove each child's mean before comparing scorers. Word- and character-normalized rows are comparable across tokenizers; raw bits per model token are deliberately omitted as scientific agreement measures.

## Fixed-Effort Age-Slope Comparison

| outcome | paired_rows | children | observed_slope_tiny | observed_slope_mistral | observed_difference_tiny_minus_mistral | requested_reps | successful_reps | difference_ci_low | difference_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| real_k3_sum_bits | 443848.000 | 21.000 | -0.222 | -0.133 | -0.089 | 200.000 | 200.000 | -0.152 | -0.028 |
| real_k0_sum_bits | 446508.000 | 21.000 | -0.254 | -0.162 | -0.092 | 200.000 | 200.000 | -0.157 | -0.045 |
| real_context_gain_k3 | 443848.000 | 21.000 | -0.032 | -0.030 | -0.003 | 200.000 | 200.000 | -0.040 | 0.025 |

The reported difference is `tinydialogues_pbm minus mistral_full79`. Its interval resamples children and refits both scorer slopes to each identical bootstrap draw.

## Interpretation Boundary

Agreement means the PBM developmental pattern is less dependent on one scorer. A magnitude difference can reflect model calibration and scale as well as a scientific disagreement. Context gain is `k0 - k3`; positive values mean the preceding context supports the observed target under that scorer.

## Saved Artifacts

- Join mismatches: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/join_mismatches.csv`
- Exact paired wide table: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/paired_direct_surprisal_wide.csv.gz`
- Paired correlations: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/paired_correlations.csv`
- Paired slope summary: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/paired_slope_bootstrap_summary.csv`
- Bootstrap draws: `results/direct_surprisal_replication/paired_tiny_mistral_pbm/paired_slope_bootstrap_draws.csv.gz`
