# Response Entropy Stopping Probe

This is a bounded diagnostic rerun for response-space entropy generation. It
tests whether generated child responses stop naturally, reach a later speaker
boundary, or keep running until the configured max-token cap.

## Manifest

| bucket | available_contexts | selected_contexts | min_context_words_selected | max_context_words_selected |
| --- | --- | --- | --- | --- |
| 01_one_word | 15 | 10 | 1 | 1 |
| 02_two_to_four | 88 | 10 | 2 | 4 |
| 03_five_to_nine | 185 | 10 | 5 | 9 |
| 04_ten_plus | 192 | 10 | 10 | 29 |

## Setting Summary

| max_new_tokens | temperature | rows | contexts | mean_samples_per_context | empty_response_rate | hit_max_rate | boundary_seen_rate | hit_cap_no_boundary_rate | natural_eos_no_boundary_rate | boundary_and_hit_cap_rate | mean_generated_tokens | mean_sampled_words_after_trim | p50_sampled_words_after_trim | p90_sampled_words_after_trim | p95_sampled_words_after_trim | mean_raw_generated_words | median_boundary_char_position |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 0.5 | 400 | 40 | 10 | 0 | 1 | 0.345 | 0.655 | 0 | 0.345 | 12 | 5.112 | 5 | 8 | 9 | 5.9 | 13 |
| 24 | 0.5 | 400 | 40 | 10 | 0 | 1 | 0.6425 | 0.3575 | 0 | 0.6425 | 24 | 7.72 | 6 | 16 | 17 | 12.33 | 13 |
| 48 | 0.5 | 400 | 40 | 10 | 0 | 1 | 0.67 | 0.33 | 0 | 0.67 | 48 | 12.97 | 6 | 33 | 36 | 25.29 | 13 |
| 96 | 0.5 | 400 | 40 | 10 | 0 | 1 | 0.675 | 0.325 | 0 | 0.675 | 96 | 23.32 | 6 | 68 | 72 | 52.17 | 13 |
| 12 | 0.7 | 400 | 40 | 10 | 0 | 1 | 0.285 | 0.715 | 0 | 0.285 | 12 | 5.51 | 6 | 9 | 9 | 6.228 | 13 |
| 24 | 0.7 | 400 | 40 | 10 | 0 | 1 | 0.605 | 0.395 | 0 | 0.605 | 24 | 8.555 | 7 | 17 | 18 | 12.88 | 13.5 |
| 48 | 0.7 | 400 | 40 | 10 | 0 | 1 | 0.63 | 0.37 | 0 | 0.63 | 48 | 14.84 | 7 | 34.1 | 37 | 27.05 | 14 |
| 96 | 0.7 | 400 | 40 | 10 | 0 | 1 | 0.64 | 0.36 | 0 | 0.64 | 96 | 27.06 | 7 | 70 | 75 | 56.38 | 14 |
| 12 | 1 | 400 | 40 | 10 | 0 | 1 | 0.205 | 0.795 | 0 | 0.205 | 12 | 6.192 | 7 | 9 | 10 | 6.775 | 14 |
| 24 | 1 | 400 | 40 | 10 | 0 | 1 | 0.395 | 0.605 | 0 | 0.395 | 24 | 10.83 | 12 | 18 | 19 | 13.89 | 18 |
| 48 | 1 | 400 | 40 | 10 | 0 | 1 | 0.4575 | 0.5425 | 0 | 0.4575 | 48 | 20.04 | 25 | 36 | 38 | 29.34 | 20 |
| 96 | 1 | 400 | 40 | 10 | 0 | 1 | 0.47 | 0.53 | 0 | 0.47 | 96 | 38.31 | 52 | 73 | 76 | 61.95 | 20 |

## Stop Categories

| max_new_tokens | temperature | stop_category | rows | rate |
| --- | --- | --- | --- | --- |
| 12 | 0.5 | boundary_seen_and_generation_hit_cap | 138 | 0.345 |
| 12 | 0.5 | hit_cap_no_boundary | 262 | 0.655 |
| 12 | 0.7 | boundary_seen_and_generation_hit_cap | 114 | 0.285 |
| 12 | 0.7 | hit_cap_no_boundary | 286 | 0.715 |
| 12 | 1 | boundary_seen_and_generation_hit_cap | 82 | 0.205 |
| 12 | 1 | hit_cap_no_boundary | 318 | 0.795 |
| 24 | 0.5 | boundary_seen_and_generation_hit_cap | 257 | 0.6425 |
| 24 | 0.5 | hit_cap_no_boundary | 143 | 0.3575 |
| 24 | 0.7 | boundary_seen_and_generation_hit_cap | 242 | 0.605 |
| 24 | 0.7 | hit_cap_no_boundary | 158 | 0.395 |
| 24 | 1 | boundary_seen_and_generation_hit_cap | 158 | 0.395 |
| 24 | 1 | hit_cap_no_boundary | 242 | 0.605 |
| 48 | 0.5 | boundary_seen_and_generation_hit_cap | 268 | 0.67 |
| 48 | 0.5 | hit_cap_no_boundary | 132 | 0.33 |
| 48 | 0.7 | boundary_seen_and_generation_hit_cap | 252 | 0.63 |
| 48 | 0.7 | hit_cap_no_boundary | 148 | 0.37 |
| 48 | 1 | boundary_seen_and_generation_hit_cap | 183 | 0.4575 |
| 48 | 1 | hit_cap_no_boundary | 217 | 0.5425 |
| 96 | 0.5 | boundary_seen_and_generation_hit_cap | 270 | 0.675 |
| 96 | 0.5 | hit_cap_no_boundary | 130 | 0.325 |
| 96 | 0.7 | boundary_seen_and_generation_hit_cap | 256 | 0.64 |
| 96 | 0.7 | hit_cap_no_boundary | 144 | 0.36 |
| 96 | 1 | boundary_seen_and_generation_hit_cap | 188 | 0.47 |
| 96 | 1 | hit_cap_no_boundary | 212 | 0.53 |

## Figures

![max-token hit rate](../figs/response_entropy_stopping_probe_v2/stopping_probe_hit_max_rate.png)

![speaker-boundary rate](../figs/response_entropy_stopping_probe_v2/stopping_probe_boundary_rate.png)

![p90 trimmed response words](../figs/response_entropy_stopping_probe_v2/stopping_probe_p90_trimmed_words.png)

![stop categories](../figs/response_entropy_stopping_probe_v2/stopping_probe_stop_categories.png)

## Files

- Combined samples: `results/response_entropy_stopping_probe_v2/stopping_probe_samples_combined.csv.gz`
- Setting summary: `results/response_entropy_stopping_probe_v2/stopping_probe_setting_summary.csv`
- Stop categories: `results/response_entropy_stopping_probe_v2/stopping_probe_stop_category_summary.csv`
- Manual examples: `results/response_entropy_stopping_probe_v2/stopping_probe_manual_examples.csv`
- Figure manifest: `results/response_entropy_stopping_probe_v2/stopping_probe_figure_manifest.csv`
