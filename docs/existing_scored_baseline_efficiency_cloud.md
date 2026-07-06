# Existing Scored Baseline Efficiency Cloud

This report uses the cloud we already have: real child utterances, random baselines, n-gram baselines, and additive LSTM baselines, all scored under the same Mistral surprisal model.
It is different from the future Mistral-generated response cloud. Here, the generators are already decoupled from the scorer for random, n-gram, and LSTM baselines.

## Why This Is Useful Now

- It gives an immediate information-effort cloud without waiting for Mistral-generated sampled responses to be scored.
- It compares real child utterances to multiple non-Mistral generators under one common scorer.
- It can be used as an early communicative-efficiency visualization: age, effort, and Mistral information in one space.
- Mistral response entropy is retained as a context-level scorer uncertainty predictor, not as independent behavioral evidence.

## Inputs

- Scored long table: `results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz`
- Response entropy table: `results/route2_response_space/route2_child_response_space_effort_table.csv.gz`
- Output directory: `results/existing_scored_baseline_efficiency_cloud`
- Figure directory: `figs/existing_scored_baseline_efficiency_cloud`

## Audit

The builder scanned `16965776` long-table rows and retained `3572541` child `k3` cloud rows across `8` sources.

| metric | value |
| --- | --- |
| input_rows_read | 1.697e+07 |
| filtered_child_k3_cloud_rows | 3.573e+06 |
| response_entropy_matched_rows | 3.551e+06 |
| sample_rows | 9.6e+04 |
| sources | 8 |
| response_entropy_lookup_rows | 4.443e+05 |

## Source-Level Means

| source_label | n | mean_sum_bits | mean_nb_words | mean_bits_per_word | mean_response_entropy_bits |
| --- | --- | --- | --- | --- | --- |
| Real child | 4.47e+05 | 26.73 | 2.663 | 11.77 | 5.121 |
| Random | 4.465e+05 | 61.11 | 2.661 | 24.19 | 5.121 |
| Unigram | 4.465e+05 | 41.83 | 2.661 | 17.01 | 5.121 |
| Bigram | 4.465e+05 | 36.79 | 2.661 | 15.25 | 5.121 |
| Trigram | 4.465e+05 | 33.68 | 2.661 | 14.12 | 5.121 |
| LSTM k3 | 4.465e+05 | 28.42 | 2.661 | 12.35 | 5.121 |
| LSTM k4 | 4.465e+05 | 28.51 | 2.661 | 12.36 | 5.121 |
| LSTM k5 | 4.465e+05 | 28.51 | 2.661 | 12.39 | 5.121 |

## Figures

### 3D sampled cloud: age, effort, information

![3D sampled cloud: age, effort, information](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_3d_sampled_cloud.png)

### 3D centroid trajectories by source

![3D centroid trajectories by source](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_3d_centroid_trajectories.png)

### Effort-information sampled facets

![Effort-information sampled facets](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_effort_information_facets.png)

### Age-bin cloud centroids

![Age-bin cloud centroids](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_age_centroids.png)

### Fixed-word information trajectories

![Fixed-word information trajectories](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_fixed_word_trajectories.png)

### Response-entropy stratified cloud means

![Response-entropy stratified cloud means](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_response_entropy_panels.png)

### Same-utterance real-vs-baseline gaps

![Same-utterance real-vs-baseline gaps](../figs/existing_scored_baseline_efficiency_cloud/existing_scored_baseline_pairwise_gap_by_age.png)

## Same-Utterance Real-Vs-Baseline Gap Summary

Positive `control minus real` means the generated control has higher Mistral k3 surprisal than the real child utterance for the matched utterance.

| source_label | age_bin | n | mean_control_minus_real_k3_bits | baseline_higher_k3_bits_rate | mean_control_minus_real_context_gain |
| --- | --- | --- | --- | --- | --- |
| Bigram | 006-023 | 6.282e+04 | 6.855 | 0.6784 | -2.776 |
| Bigram | 024-029 | 1.622e+05 | 8.561 | 0.7276 | -2.925 |
| Bigram | 030-035 | 1.424e+05 | 11.24 | 0.7822 | -3.117 |
| Bigram | 036-041 | 3.721e+04 | 11.96 | 0.7755 | -2.253 |
| Bigram | 042-047 | 1.634e+04 | 16.1 | 0.8247 | -2.781 |
| Bigram | 048-053 | 1.291e+04 | 13.86 | 0.7868 | -1.45 |
| Bigram | 054-059 | 1.003e+04 | 15.15 | 0.7994 | -1.204 |
| Bigram | 060-065 | 2542 | 16.64 | 0.8415 | -1.386 |
| LSTM k3 | 006-023 | 6.282e+04 | 1.71 | 0.5475 | -2.923 |
| LSTM k3 | 024-029 | 1.622e+05 | 1.046 | 0.541 | -2.18 |
| LSTM k3 | 030-035 | 1.424e+05 | 2.385 | 0.5984 | -2.501 |
| LSTM k3 | 036-041 | 3.721e+04 | 1.294 | 0.5545 | -1.502 |
| LSTM k3 | 042-047 | 1.634e+04 | 3.889 | 0.6182 | -2.069 |
| LSTM k3 | 048-053 | 1.291e+04 | 0.831 | 0.5385 | -0.9179 |
| LSTM k3 | 054-059 | 1.003e+04 | 1.296 | 0.5505 | -0.4424 |
| LSTM k3 | 060-065 | 2542 | 3.923 | 0.6188 | -0.4892 |
| LSTM k4 | 006-023 | 6.282e+04 | 1.96 | 0.5551 | -2.964 |
| LSTM k4 | 024-029 | 1.622e+05 | 1.255 | 0.5457 | -2.088 |
| LSTM k4 | 030-035 | 1.424e+05 | 2.255 | 0.5921 | -2.227 |
| LSTM k4 | 036-041 | 3.721e+04 | 1.502 | 0.562 | -1.832 |
| LSTM k4 | 042-047 | 1.634e+04 | 3.663 | 0.6128 | -1.927 |
| LSTM k4 | 048-053 | 1.291e+04 | 0.9178 | 0.538 | -0.7078 |
| LSTM k4 | 054-059 | 1.003e+04 | 1.934 | 0.5678 | -0.4476 |
| LSTM k4 | 060-065 | 2542 | 3.13 | 0.5944 | -0.4972 |
| LSTM k5 | 006-023 | 6.282e+04 | 1.915 | 0.5543 | -2.837 |
| LSTM k5 | 024-029 | 1.622e+05 | 1.371 | 0.5547 | -2.227 |
| LSTM k5 | 030-035 | 1.424e+05 | 2.194 | 0.5902 | -2.275 |
| LSTM k5 | 036-041 | 3.721e+04 | 1.407 | 0.5559 | -1.495 |
| LSTM k5 | 042-047 | 1.634e+04 | 3.419 | 0.6053 | -1.909 |
| LSTM k5 | 048-053 | 1.291e+04 | 1.002 | 0.5387 | -0.6088 |
| LSTM k5 | 054-059 | 1.003e+04 | 1.791 | 0.5589 | -0.4548 |
| LSTM k5 | 060-065 | 2542 | 3.433 | 0.6058 | -0.5049 |
| Random | 006-023 | 6.282e+04 | 22.59 | 0.9324 | -5.771 |
| Random | 024-029 | 1.622e+05 | 28.62 | 0.959 | -5.822 |
| Random | 030-035 | 1.424e+05 | 37.84 | 0.9769 | -6.099 |
| Random | 036-041 | 3.721e+04 | 43.96 | 0.981 | -5.281 |
| Random | 042-047 | 1.634e+04 | 53.51 | 0.9856 | -5.738 |
| Random | 048-053 | 1.291e+04 | 53.3 | 0.9836 | -4.341 |
| Random | 054-059 | 1.003e+04 | 56.46 | 0.9834 | -3.905 |
| Random | 060-065 | 2542 | 57.27 | 0.9874 | -4.151 |
| Trigram | 006-023 | 6.282e+04 | 3.934 | 0.5673 | -1.46 |
| Trigram | 024-029 | 1.622e+05 | 5.859 | 0.6423 | -1.826 |
| Trigram | 030-035 | 1.424e+05 | 8.015 | 0.7006 | -2.085 |
| Trigram | 036-041 | 3.721e+04 | 8.508 | 0.698 | -1.377 |
| Trigram | 042-047 | 1.634e+04 | 11.76 | 0.7452 | -1.764 |
| Trigram | 048-053 | 1.291e+04 | 9.577 | 0.7141 | -0.6467 |
| Trigram | 054-059 | 1.003e+04 | 10.56 | 0.7246 | -0.4713 |
| Trigram | 060-065 | 2542 | 12.6 | 0.7785 | -0.7233 |
| Unigram | 006-023 | 6.282e+04 | 10.84 | 0.7753 | -4.548 |
| Unigram | 024-029 | 1.622e+05 | 12.83 | 0.8135 | -4.333 |
| Unigram | 030-035 | 1.424e+05 | 16.53 | 0.8634 | -4.53 |
| Unigram | 036-041 | 3.721e+04 | 18.22 | 0.8685 | -3.647 |
| Unigram | 042-047 | 1.634e+04 | 23.39 | 0.9033 | -4.183 |
| Unigram | 048-053 | 1.291e+04 | 21.51 | 0.8844 | -2.763 |
| Unigram | 054-059 | 1.003e+04 | 23.24 | 0.8849 | -2.546 |
| Unigram | 060-065 | 2542 | 24.75 | 0.9068 | -2.754 |

## Interpretation Boundary

- This is an already-scored baseline cloud, not a Mistral sampled-response cloud.
- Random, n-gram, and LSTM utterances are not same-meaning paraphrases; they are matched baseline alternatives or generated utterances under the same child/context rows.
- Response entropy from the Mistral-generated response-space run remains useful as the scorer model's context-level uncertainty, but it should be named that way.
- The future full cloud should include scored Mistral-generated samples as a self-reference condition and, ideally, other-generator samples scored by Mistral as decoupled-generator conditions.
