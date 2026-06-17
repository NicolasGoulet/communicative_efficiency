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
| 12 | 0.5 | 400 | 40 | 10 | 0.065 | 1 | 0.4075 | 0.5925 | 0 | 0.3425 | 13.22 | 5.133 | 5 | 9 | 10.05 | 6.615 | 11 |
| 24 | 0.5 | 400 | 40 | 10 | 0.065 | 1 | 0.67 | 0.33 | 0 | 0.605 | 25.22 | 7.548 | 6 | 16 | 17 | 13.05 | 14 |
| 48 | 0.5 | 400 | 40 | 10 | 0.065 | 1 | 0.6975 | 0.3025 | 0 | 0.6325 | 49.22 | 12.4 | 6 | 32.1 | 36 | 26 | 15 |
| 96 | 0.5 | 400 | 40 | 10 | 0.065 | 1 | 0.7025 | 0.2975 | 0 | 0.6375 | 97.22 | 21.9 | 6 | 67.1 | 72 | 52.89 | 15 |
| 12 | 0.7 | 400 | 40 | 10 | 0.065 | 1 | 0.355 | 0.645 | 0 | 0.29 | 13.22 | 5.48 | 6 | 9 | 10 | 6.942 | 9 |
| 24 | 0.7 | 400 | 40 | 10 | 0.065 | 1 | 0.6375 | 0.3625 | 0 | 0.5725 | 25.22 | 8.277 | 7 | 17 | 18 | 13.6 | 17 |
| 48 | 0.7 | 400 | 40 | 10 | 0.065 | 1 | 0.6575 | 0.3425 | 0 | 0.5925 | 49.22 | 14.08 | 7 | 34 | 37 | 27.77 | 18 |
| 96 | 0.7 | 400 | 40 | 10 | 0.065 | 1 | 0.6675 | 0.3325 | 0 | 0.6025 | 97.22 | 25.42 | 7 | 70 | 75 | 57.1 | 18 |
| 12 | 1 | 400 | 40 | 10 | 0.065 | 1 | 0.305 | 0.695 | 0 | 0.24 | 13.22 | 5.997 | 6 | 10 | 11 | 7.49 | 9 |
| 24 | 1 | 400 | 40 | 10 | 0.065 | 1 | 0.4625 | 0.5375 | 0 | 0.3975 | 25.22 | 10.12 | 12 | 18 | 19 | 14.6 | 16 |
| 48 | 1 | 400 | 40 | 10 | 0.065 | 1 | 0.5175 | 0.4825 | 0 | 0.4525 | 49.22 | 18.29 | 18.5 | 36 | 38.05 | 30.05 | 19 |
| 96 | 1 | 400 | 40 | 10 | 0.065 | 1 | 0.525 | 0.475 | 0 | 0.46 | 97.22 | 34.63 | 23 | 73 | 76 | 62.67 | 19.5 |

## Stop Categories

| max_new_tokens | temperature | stop_category | rows | rate |
| --- | --- | --- | --- | --- |
| 12 | 0.5 | boundary_seen_and_generation_hit_cap | 137 | 0.3425 |
| 12 | 0.5 | empty | 26 | 0.065 |
| 12 | 0.5 | hit_cap_no_boundary | 237 | 0.5925 |
| 12 | 0.7 | boundary_seen_and_generation_hit_cap | 116 | 0.29 |
| 12 | 0.7 | empty | 26 | 0.065 |
| 12 | 0.7 | hit_cap_no_boundary | 258 | 0.645 |
| 12 | 1 | boundary_seen_and_generation_hit_cap | 96 | 0.24 |
| 12 | 1 | empty | 26 | 0.065 |
| 12 | 1 | hit_cap_no_boundary | 278 | 0.695 |
| 24 | 0.5 | boundary_seen_and_generation_hit_cap | 242 | 0.605 |
| 24 | 0.5 | empty | 26 | 0.065 |
| 24 | 0.5 | hit_cap_no_boundary | 132 | 0.33 |
| 24 | 0.7 | boundary_seen_and_generation_hit_cap | 229 | 0.5725 |
| 24 | 0.7 | empty | 26 | 0.065 |
| 24 | 0.7 | hit_cap_no_boundary | 145 | 0.3625 |
| 24 | 1 | boundary_seen_and_generation_hit_cap | 159 | 0.3975 |
| 24 | 1 | empty | 26 | 0.065 |
| 24 | 1 | hit_cap_no_boundary | 215 | 0.5375 |
| 48 | 0.5 | boundary_seen_and_generation_hit_cap | 253 | 0.6325 |
| 48 | 0.5 | empty | 26 | 0.065 |
| 48 | 0.5 | hit_cap_no_boundary | 121 | 0.3025 |
| 48 | 0.7 | boundary_seen_and_generation_hit_cap | 237 | 0.5925 |
| 48 | 0.7 | empty | 26 | 0.065 |
| 48 | 0.7 | hit_cap_no_boundary | 137 | 0.3425 |
| 48 | 1 | boundary_seen_and_generation_hit_cap | 181 | 0.4525 |
| 48 | 1 | empty | 26 | 0.065 |
| 48 | 1 | hit_cap_no_boundary | 193 | 0.4825 |
| 96 | 0.5 | boundary_seen_and_generation_hit_cap | 255 | 0.6375 |
| 96 | 0.5 | empty | 26 | 0.065 |
| 96 | 0.5 | hit_cap_no_boundary | 119 | 0.2975 |
| 96 | 0.7 | boundary_seen_and_generation_hit_cap | 241 | 0.6025 |
| 96 | 0.7 | empty | 26 | 0.065 |
| 96 | 0.7 | hit_cap_no_boundary | 133 | 0.3325 |
| 96 | 1 | boundary_seen_and_generation_hit_cap | 184 | 0.46 |
| 96 | 1 | empty | 26 | 0.065 |
| 96 | 1 | hit_cap_no_boundary | 190 | 0.475 |

## Figures

![max-token hit rate](../figs/response_entropy_stopping_probe/stopping_probe_hit_max_rate.png)

![speaker-boundary rate](../figs/response_entropy_stopping_probe/stopping_probe_boundary_rate.png)

![p90 trimmed response words](../figs/response_entropy_stopping_probe/stopping_probe_p90_trimmed_words.png)

![stop categories](../figs/response_entropy_stopping_probe/stopping_probe_stop_categories.png)

## Files

- Combined samples: `results/response_entropy_stopping_probe/stopping_probe_samples_combined.csv.gz`
- Setting summary: `results/response_entropy_stopping_probe/stopping_probe_setting_summary.csv`
- Stop categories: `results/response_entropy_stopping_probe/stopping_probe_stop_category_summary.csv`
- Manual examples: `results/response_entropy_stopping_probe/stopping_probe_manual_examples.csv`
- Figure manifest: `results/response_entropy_stopping_probe/stopping_probe_figure_manifest.csv`
