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
| 48 | 0.5 | 400 | 40 | 10 | 0.0025 | 1 | 0.985 | 0.015 | 0 | 0.9825 | 48 | 4.22 | 3 | 9 | 12 | 25.29 | 13 |
| 48 | 0.7 | 400 | 40 | 10 | 0.0025 | 1 | 0.995 | 0.005 | 0 | 0.9925 | 48 | 4.29 | 3 | 8.1 | 11 | 27.05 | 14 |

## Stop Categories

| max_new_tokens | temperature | stop_category | rows | rate |
| --- | --- | --- | --- | --- |
| 48 | 0.5 | boundary_seen_and_generation_hit_cap | 393 | 0.9825 |
| 48 | 0.5 | empty | 1 | 0.0025 |
| 48 | 0.5 | hit_cap_no_boundary | 6 | 0.015 |
| 48 | 0.7 | boundary_seen_and_generation_hit_cap | 397 | 0.9925 |
| 48 | 0.7 | empty | 1 | 0.0025 |
| 48 | 0.7 | hit_cap_no_boundary | 2 | 0.005 |

## Figures

![max-token hit rate](../figs/response_entropy_stopping_probe_v3/stopping_probe_hit_max_rate.png)

![speaker-boundary rate](../figs/response_entropy_stopping_probe_v3/stopping_probe_boundary_rate.png)

![p90 trimmed response words](../figs/response_entropy_stopping_probe_v3/stopping_probe_p90_trimmed_words.png)

![stop categories](../figs/response_entropy_stopping_probe_v3/stopping_probe_stop_categories.png)

## Files

- Combined samples: `results/response_entropy_stopping_probe_v3/stopping_probe_samples_combined.csv.gz`
- Setting summary: `results/response_entropy_stopping_probe_v3/stopping_probe_setting_summary.csv`
- Stop categories: `results/response_entropy_stopping_probe_v3/stopping_probe_stop_category_summary.csv`
- Manual examples: `results/response_entropy_stopping_probe_v3/stopping_probe_manual_examples.csv`
- Figure manifest: `results/response_entropy_stopping_probe_v3/stopping_probe_figure_manifest.csv`
