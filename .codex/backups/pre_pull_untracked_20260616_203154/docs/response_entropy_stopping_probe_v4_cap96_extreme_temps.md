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
| 96 | 0.3 | 400 | 40 | 10 | 0 | 1 | 1 | 0 | 0 | 1 | 96 | 3.53 | 3 | 7 | 8.05 | 47.79 | 13 |
| 96 | 1.3 | 400 | 40 | 10 | 0.005 | 1 | 0.8 | 0.2 | 0 | 0.795 | 96 | 20.86 | 8 | 66 | 70 | 60.81 | 32 |
| 96 | 1.6 | 400 | 40 | 10 | 0.0025 | 1 | 0.3725 | 0.6275 | 0 | 0.37 | 96 | 44.98 | 54 | 76 | 81 | 63.37 | 31 |

## Stop Categories

| max_new_tokens | temperature | stop_category | rows | rate |
| --- | --- | --- | --- | --- |
| 96 | 0.3 | boundary_seen_and_generation_hit_cap | 400 | 1 |
| 96 | 1.3 | boundary_seen_and_generation_hit_cap | 318 | 0.795 |
| 96 | 1.3 | empty | 2 | 0.005 |
| 96 | 1.3 | hit_cap_no_boundary | 80 | 0.2 |
| 96 | 1.6 | boundary_seen_and_generation_hit_cap | 148 | 0.37 |
| 96 | 1.6 | empty | 1 | 0.0025 |
| 96 | 1.6 | hit_cap_no_boundary | 251 | 0.6275 |

## Figures

![max-token hit rate](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_hit_max_rate.png)

![speaker-boundary rate](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_boundary_rate.png)

![p90 trimmed response words](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_p90_trimmed_words.png)

![stop categories](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_stop_categories.png)

## Files

- Combined samples: `results/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_samples_combined.csv.gz`
- Setting summary: `results/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_setting_summary.csv`
- Stop categories: `results/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_stop_category_summary.csv`
- Manual examples: `results/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_manual_examples.csv`
- Figure manifest: `results/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_figure_manifest.csv`
