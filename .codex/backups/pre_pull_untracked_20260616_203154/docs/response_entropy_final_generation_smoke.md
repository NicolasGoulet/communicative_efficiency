# Route 2 Final Generation Smoke

Created: 2026-06-16

This is the final pre-Slurm response-generation smoke. It is generation and
sampling only, not entropy scoring. The downstream entropy feature script
should consume the accepted samples after this smoke is approved.

## Method And Prompt Definition

For each caregiver context, the sampler repeatedly prompts base Mistral with a
transcript-style wrapper and keeps one generated child conversational turn.
The smoke tests three wrappers:

```text
Caregiver: {context}
Child:

Parent: {context}
Child:

Adult: {context}
Child:
```

Generation uses true end-of-turn stopping during decoding. Decoding stops as
soon as the generated suffix contains one of:

```text
\n
\nCaregiver:
\nParent:
\nAdult:
\nChild:
\nCHI:
```

`max_new_tokens=96` is only a safety cap. Attempts are accepted only if the
first generated child-turn response passes deterministic structural checks.
Possible context copies are kept as accepted review-flagged samples, not
silently removed.

Manifest audit:

| audit_scope | context_length_bucket | available_contexts | selected_base_contexts | prompt_variants | temperatures | accepted_samples_per_setting | max_attempts_per_setting | planned_accepted_samples | max_attempt_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context_bucket | 01_one_word | 15 | 10 | 3 | 0.3,0.5,0.7,1.0 | 20 | 60 | 2400 | 7200 |
| context_bucket | 02_two_to_four | 88 | 10 | 3 | 0.3,0.5,0.7,1.0 | 20 | 60 | 2400 | 7200 |
| context_bucket | 03_five_to_nine | 185 | 10 | 3 | 0.3,0.5,0.7,1.0 | 20 | 60 | 2400 | 7200 |
| context_bucket | 04_ten_plus | 192 | 10 | 3 | 0.3,0.5,0.7,1.0 | 20 | 60 | 2400 | 7200 |
| total | all | 480 | 40 | 3 | 0.3,0.5,0.7,1.0 | 20 | 60 | 9600 | 2.88e+04 |

## Temperature Results

| temperature | settings | attempts | accepted_samples | rejected_attempts | incomplete_settings | mean_attempts_per_accepted | rejection_rate | mean_entropy_mm_bits | sd_entropy_mm_bits | mean_unique_response_count | mean_top_response_probability | mean_sample_word_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 120 | 2540 | 2343 | 197 | 3 | 1.169 | 0.07756 | 2.274 | 1.42 | 7.356 | 0.5133 | 3.641 |
| 0.5 | 120 | 2550 | 2371 | 179 | 3 | 1.163 | 0.0702 | 3.326 | 1.334 | 11.64 | 0.3486 | 3.787 |
| 0.7 | 120 | 2523 | 2398 | 125 | 1 | 1.054 | 0.04954 | 4.062 | 1.111 | 15.08 | 0.2322 | 4.016 |
| 1 | 120 | 2590 | 2400 | 190 | 0 | 1.079 | 0.07336 | 4.766 | 0.5909 | 18.67 | 0.1013 | 5.122 |

![rejection rate by temperature](../figs/response_entropy_final_generation_smoke/final_smoke_rejection_rate_by_temperature.png)

![entropy by temperature and prompt](../figs/response_entropy_final_generation_smoke/final_smoke_entropy_by_temperature_prompt.png)

## Prompt Robustness Results

Prompt-variant rank correlations compare context-level accepted-response
entropy estimates across `Caregiver`, `Parent`, and `Adult` wrappers at the
same temperature.

| comparison_family | setting_a | setting_a_prompt_variant | setting_a_temperature | setting_b | setting_b_prompt_variant | setting_b_temperature | shared_contexts | spearman_r | pearson_r | mean_abs_entropy_diff_bits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| prompt_within_temperature | Adult_T0.3 | Adult | 0.3 | Caregiver_T0.3 | Caregiver | 0.3 | 39 | 0.605 | 0.6216 | 0.9223 |
| prompt_within_temperature | Adult_T0.3 | Adult | 0.3 | Parent_T0.3 | Parent | 0.3 | 39 | 0.4867 | 0.5165 | 1.069 |
| prompt_within_temperature | Adult_T0.5 | Adult | 0.5 | Caregiver_T0.5 | Caregiver | 0.5 | 40 | 0.7439 | 0.7319 | 0.8365 |
| prompt_within_temperature | Adult_T0.5 | Adult | 0.5 | Parent_T0.5 | Parent | 0.5 | 40 | 0.7321 | 0.7155 | 0.8967 |
| prompt_within_temperature | Adult_T0.7 | Adult | 0.7 | Caregiver_T0.7 | Caregiver | 0.7 | 40 | 0.7323 | 0.7532 | 0.537 |
| prompt_within_temperature | Adult_T0.7 | Adult | 0.7 | Parent_T0.7 | Parent | 0.7 | 40 | 0.7186 | 0.7551 | 0.5461 |
| prompt_within_temperature | Adult_T1 | Adult | 1 | Caregiver_T1 | Caregiver | 1 | 40 | 0.5797 | 0.2982 | 0.29 |
| prompt_within_temperature | Adult_T1 | Adult | 1 | Parent_T1 | Parent | 1 | 40 | 0.6668 | 0.4069 | 0.2189 |
| prompt_within_temperature | Caregiver_T0.3 | Caregiver | 0.3 | Parent_T0.3 | Parent | 0.3 | 39 | 0.6187 | 0.617 | 0.909 |
| prompt_within_temperature | Caregiver_T0.5 | Caregiver | 0.5 | Parent_T0.5 | Parent | 0.5 | 40 | 0.7674 | 0.8208 | 0.5416 |
| prompt_within_temperature | Caregiver_T0.7 | Caregiver | 0.7 | Parent_T0.7 | Parent | 0.7 | 40 | 0.7869 | 0.8236 | 0.4273 |
| prompt_within_temperature | Caregiver_T1 | Caregiver | 1 | Parent_T1 | Parent | 1 | 40 | 0.5916 | 0.8992 | 0.178 |

Temperature rank correlations compare entropy rankings across temperatures
within the same prompt wrapper.

| comparison_family | setting_a | setting_a_prompt_variant | setting_a_temperature | setting_b | setting_b_prompt_variant | setting_b_temperature | shared_contexts | spearman_r | pearson_r | mean_abs_entropy_diff_bits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| temperature_within_prompt | Adult_T0.3 | Adult | 0.3 | Adult_T0.5 | Adult | 0.5 | 39 | 0.8555 | 0.8408 | 0.9811 |
| temperature_within_prompt | Adult_T0.3 | Adult | 0.3 | Adult_T0.7 | Adult | 0.7 | 39 | 0.6838 | 0.6274 | 1.955 |
| temperature_within_prompt | Adult_T0.3 | Adult | 0.3 | Adult_T1 | Adult | 1 | 39 | 0.3607 | 0.3414 | 2.702 |
| temperature_within_prompt | Adult_T0.5 | Adult | 0.5 | Adult_T0.7 | Adult | 0.7 | 40 | 0.812 | 0.806 | 1.042 |
| temperature_within_prompt | Adult_T0.5 | Adult | 0.5 | Adult_T1 | Adult | 1 | 40 | 0.5753 | 0.5266 | 1.745 |
| temperature_within_prompt | Adult_T0.7 | Adult | 0.7 | Adult_T1 | Adult | 1 | 40 | 0.7661 | 0.7865 | 0.7447 |
| temperature_within_prompt | Caregiver_T0.3 | Caregiver | 0.3 | Caregiver_T0.5 | Caregiver | 0.5 | 39 | 0.9088 | 0.9216 | 1.169 |
| temperature_within_prompt | Caregiver_T0.3 | Caregiver | 0.3 | Caregiver_T0.7 | Caregiver | 0.7 | 39 | 0.809 | 0.7965 | 1.77 |
| temperature_within_prompt | Caregiver_T0.3 | Caregiver | 0.3 | Caregiver_T1 | Caregiver | 1 | 39 | 0.5216 | 0.4132 | 2.435 |
| temperature_within_prompt | Caregiver_T0.5 | Caregiver | 0.5 | Caregiver_T0.7 | Caregiver | 0.7 | 40 | 0.8149 | 0.8927 | 0.6833 |
| temperature_within_prompt | Caregiver_T0.5 | Caregiver | 0.5 | Caregiver_T1 | Caregiver | 1 | 40 | 0.6143 | 0.5746 | 1.294 |
| temperature_within_prompt | Caregiver_T0.7 | Caregiver | 0.7 | Caregiver_T1 | Caregiver | 1 | 40 | 0.5614 | 0.7128 | 0.6877 |
| temperature_within_prompt | Parent_T0.3 | Parent | 0.3 | Parent_T0.5 | Parent | 0.5 | 40 | 0.9028 | 0.8666 | 1.059 |
| temperature_within_prompt | Parent_T0.3 | Parent | 0.3 | Parent_T0.7 | Parent | 0.7 | 40 | 0.7411 | 0.7072 | 1.626 |
| temperature_within_prompt | Parent_T0.3 | Parent | 0.3 | Parent_T1 | Parent | 1 | 40 | 0.5701 | 0.4567 | 2.329 |
| temperature_within_prompt | Parent_T0.5 | Parent | 0.5 | Parent_T0.7 | Parent | 0.7 | 40 | 0.8229 | 0.8947 | 0.6551 |
| temperature_within_prompt | Parent_T0.5 | Parent | 0.5 | Parent_T1 | Parent | 1 | 40 | 0.7035 | 0.6695 | 1.279 |
| temperature_within_prompt | Parent_T0.7 | Parent | 0.7 | Parent_T1 | Parent | 1 | 40 | 0.6963 | 0.8113 | 0.7085 |

![prompt rank correlations](../figs/response_entropy_final_generation_smoke/final_smoke_prompt_rank_correlations.png)

Prompt summary:

| prompt_variant | settings | attempts | accepted_samples | rejected_attempts | incomplete_settings | mean_attempts_per_accepted | rejection_rate | mean_entropy_mm_bits | sd_entropy_mm_bits | mean_unique_response_count | mean_top_response_probability | mean_sample_word_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 160 | 3419 | 3164 | 255 | 3 | 1.102 | 0.07458 | 3.475 | 1.537 | 12.7 | 0.3299 | 4.232 |
| Caregiver | 160 | 3395 | 3168 | 227 | 2 | 1.077 | 0.06686 | 3.64 | 1.462 | 13.31 | 0.2921 | 3.958 |
| Parent | 160 | 3389 | 3180 | 209 | 2 | 1.169 | 0.06167 | 3.722 | 1.43 | 13.61 | 0.2719 | 4.241 |

## Rejection Rates

The table below is one row per context-temperature-prompt setting.

| setting_id | context_id | prompt_variant | temperature | attempts | accepted_samples | rejected_attempts | rejection_rate | target_accepted_samples | max_attempts_per_setting | reached_target | mean_attempts_per_accepted | empty_response_count | empty_response_rate | no_boundary_before_cap_count | no_boundary_before_cap_rate | repetition_loop_count | repetition_loop_rate | metadata_or_prose_drift_count | metadata_or_prose_drift_rate | malformed_response_count | malformed_response_rate | speaker_label_inside_response_count | speaker_label_inside_response_rate | other_quality_flag_count | other_quality_flag_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 053b94a7737f6201a29fa0db::Adult::T0.3 | 053b94a7737f6201a29fa0db | Adult | 0.3 | 60 | 0 | 60 | 1 | 20 | 60 | False |  | 0 | 0 | 3 | 0.05 | 57 | 0.95 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14d6e16463342cba7220efe9::Adult::T0.3 | 14d6e16463342cba7220efe9 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14e3326610d8811a01916d95::Adult::T0.3 | 14e3326610d8811a01916d95 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1504ecd75124adb0a428f3e8::Adult::T0.3 | 1504ecd75124adb0a428f3e8 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1660fb9fd1e06965cf3d0111::Adult::T0.3 | 1660fb9fd1e06965cf3d0111 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1827739c750772b0d9138518::Adult::T0.3 | 1827739c750772b0d9138518 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 18ac88ea01d39f7ebd865aa9::Adult::T0.3 | 18ac88ea01d39f7ebd865aa9 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1c2b2d381366aefb1939a0e0::Adult::T0.3 | 1c2b2d381366aefb1939a0e0 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2501a474b6bdc1e48ecf627f::Adult::T0.3 | 2501a474b6bdc1e48ecf627f | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a34856ba1e9a87b78e20c5b::Adult::T0.3 | 2a34856ba1e9a87b78e20c5b | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a78f97054bc6e864eb72208::Adult::T0.3 | 2a78f97054bc6e864eb72208 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3e4b6d8b2fab25b8377697ab::Adult::T0.3 | 3e4b6d8b2fab25b8377697ab | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 453d411381eb9b6a37254e50::Adult::T0.3 | 453d411381eb9b6a37254e50 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 48c85416ea70da856acb16a7::Adult::T0.3 | 48c85416ea70da856acb16a7 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5159122a0ac41bf1eab0e9de::Adult::T0.3 | 5159122a0ac41bf1eab0e9de | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 592dc16570fa1291fd499393::Adult::T0.3 | 592dc16570fa1291fd499393 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 67fecfb522597a47adde2a3d::Adult::T0.3 | 67fecfb522597a47adde2a3d | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7a04738ff0f6e576b5649d8b::Adult::T0.3 | 7a04738ff0f6e576b5649d8b | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7c2d211d792bd87f262787e1::Adult::T0.3 | 7c2d211d792bd87f262787e1 | Adult | 0.3 | 29 | 20 | 9 | 0.3103 | 20 | 60 | True | 1.45 | 0 | 0 | 2 | 0.06897 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0.2414 |
| 7e0ac5784bcfeb4dc8c10bdd::Adult::T0.3 | 7e0ac5784bcfeb4dc8c10bdd | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 823d43dd51d4e9f142631f03::Adult::T0.3 | 823d43dd51d4e9f142631f03 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 883d368df33c5bb2b9b1f8e5::Adult::T0.3 | 883d368df33c5bb2b9b1f8e5 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 89fea801bca3ef03b927e783::Adult::T0.3 | 89fea801bca3ef03b927e783 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8ce30f82254c3300e04cc27a::Adult::T0.3 | 8ce30f82254c3300e04cc27a | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 9dce315bc7318feb72a870c7::Adult::T0.3 | 9dce315bc7318feb72a870c7 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 9e36a8cc8350d74d483fe19b::Adult::T0.3 | 9e36a8cc8350d74d483fe19b | Adult | 0.3 | 21 | 20 | 1 | 0.04762 | 20 | 60 | True | 1.05 | 0 | 0 | 1 | 0.04762 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| aa1fd790e02dda7483980887::Adult::T0.3 | aa1fd790e02dda7483980887 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| aa4088ff841c9edfb908fee7::Adult::T0.3 | aa4088ff841c9edfb908fee7 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ae00cee9955979ad0b2079d8::Adult::T0.3 | ae00cee9955979ad0b2079d8 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| b41ed1b20b5e3bc6430de64e::Adult::T0.3 | b41ed1b20b5e3bc6430de64e | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| b76ebcb6cbf33626350e3146::Adult::T0.3 | b76ebcb6cbf33626350e3146 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| c523d6fe4d2799add289309a::Adult::T0.3 | c523d6fe4d2799add289309a | Adult | 0.3 | 21 | 20 | 1 | 0.04762 | 20 | 60 | True | 1.05 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0.04762 |
| c6e7732828ec91a2cc98c913::Adult::T0.3 | c6e7732828ec91a2cc98c913 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| c73eb7eeecb867962101377e::Adult::T0.3 | c73eb7eeecb867962101377e | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| daf1571720081d3dad16a778::Adult::T0.3 | daf1571720081d3dad16a778 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| e43b9aebb58548d8f53b8a76::Adult::T0.3 | e43b9aebb58548d8f53b8a76 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| e766024d43313fbfaa3b3136::Adult::T0.3 | e766024d43313fbfaa3b3136 | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ece3faec560e185c54667edd::Adult::T0.3 | ece3faec560e185c54667edd | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ececb26116c5fed4e5d53afb::Adult::T0.3 | ececb26116c5fed4e5d53afb | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| efb5b51f927794a50b8b276e::Adult::T0.3 | efb5b51f927794a50b8b276e | Adult | 0.3 | 20 | 20 | 0 | 0 | 20 | 60 | True | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Incomplete settings that hit the attempt cap before reaching 20 accepted
responses:

| context_id | prompt_variant | temperature | attempts | accepted_samples | rejected_attempts | rejection_rate | repetition_loop_count | no_boundary_before_cap_count | other_quality_flag_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 053b94a7737f6201a29fa0db | Adult | 0.3 | 60 | 0 | 60 | 1 | 57 | 3 | 0 |
| 053b94a7737f6201a29fa0db | Caregiver | 0.3 | 60 | 0 | 60 | 1 | 60 | 0 | 0 |
| 053b94a7737f6201a29fa0db | Parent | 0.3 | 60 | 3 | 57 | 0.95 | 55 | 2 | 0 |
| 053b94a7737f6201a29fa0db | Adult | 0.5 | 60 | 6 | 54 | 0.9 | 49 | 5 | 0 |
| 053b94a7737f6201a29fa0db | Caregiver | 0.5 | 60 | 8 | 52 | 0.8667 | 50 | 2 | 0 |
| 053b94a7737f6201a29fa0db | Parent | 0.5 | 60 | 17 | 43 | 0.7167 | 40 | 3 | 0 |
| 053b94a7737f6201a29fa0db | Adult | 0.7 | 60 | 18 | 42 | 0.7 | 38 | 3 | 0 |

## Quality Flag Rates

Quality flags are deterministic. The attempt-rate columns summarize all
attempts; accepted-rate columns in the CSV summarize accepted samples only.

| setting_id | empty_first_line_response_attempt_rate | no_end_of_turn_boundary_before_cap_attempt_rate | repetition_loop_attempt_rate | metadata_or_prose_start_attempt_rate | possible_context_copy_attempt_rate | very_long_first_line_response_attempt_rate |
| --- | --- | --- | --- | --- | --- | --- |
| 053b94a7737f6201a29fa0db::Adult::T0.3 | 0 | 0.05 | 1 | 0 | 0.95 | 0.05 |
| 14d6e16463342cba7220efe9::Adult::T0.3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14e3326610d8811a01916d95::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.05 | 0 |
| 1504ecd75124adb0a428f3e8::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.05 | 0 |
| 1660fb9fd1e06965cf3d0111::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.1 | 0 |
| 1827739c750772b0d9138518::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.1 | 0 |
| 18ac88ea01d39f7ebd865aa9::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.05 | 0 |
| 1c2b2d381366aefb1939a0e0::Adult::T0.3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2501a474b6bdc1e48ecf627f::Adult::T0.3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a34856ba1e9a87b78e20c5b::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.05 | 0 |
| 2a78f97054bc6e864eb72208::Adult::T0.3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3e4b6d8b2fab25b8377697ab::Adult::T0.3 | 0 | 0 | 0 | 0 | 1 | 0 |
| 453d411381eb9b6a37254e50::Adult::T0.3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 48c85416ea70da856acb16a7::Adult::T0.3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5159122a0ac41bf1eab0e9de::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.8 | 0 |
| 592dc16570fa1291fd499393::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.35 | 0 |
| 67fecfb522597a47adde2a3d::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.35 | 0 |
| 7a04738ff0f6e576b5649d8b::Adult::T0.3 | 0 | 0 | 0 | 0 | 1 | 0 |
| 7c2d211d792bd87f262787e1::Adult::T0.3 | 0 | 0.06897 | 0 | 0 | 0.1034 | 0.3103 |
| 7e0ac5784bcfeb4dc8c10bdd::Adult::T0.3 | 0 | 0 | 0 | 0 | 0.1 | 0 |

![quality flags by temperature](../figs/response_entropy_final_generation_smoke/final_smoke_quality_flags_by_temperature.png)

## Examples: Good / Review / Rejected

| example_type | review_reason | prompt_variant | temperature | quality_flags | rejection_reason | context_text | sampled_response_text |
| --- | --- | --- | --- | --- | --- | --- | --- |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | one. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | one. |
| good |  | Caregiver | 0.3 |  |  | six. | zero. |
| good |  | Caregiver | 0.3 |  |  | six. | one. |
| good |  | Caregiver | 0.3 |  |  | six. | one. |
| review | possible_context_copy | Caregiver | 0.3 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Caregiver | 0.7 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Caregiver | 0.7 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Parent | 0.5 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Parent | 0.7 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Parent | 0.7 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Parent | 0.7 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Parent | 1.0 | possible_context_copy |  | six. | six and three quarters. |
| review | possible_context_copy | Adult | 1.0 | possible_context_copy |  | six. | six. |
| review | possible_context_copy | Caregiver | 0.5 | possible_context_copy |  | ninety? | ninety? |
| review | possible_context_copy | Caregiver | 0.5 | possible_context_copy |  | ninety? | ninety? |
| review | possible_context_copy | Caregiver | 0.5 | possible_context_copy |  | ninety? | ninety? |
| rejected | empty_response | Parent | 1.0 | empty_first_line_response | empty_response | six. |  |
| rejected | malformed_response | Parent | 0.7 | malformed_response | malformed_response | well. | … |
| rejected | metadata_or_prose_drift | Caregiver | 1.0 | metadata_or_prose_start;possible_context_copy | metadata_or_prose_drift | well. | (smiling from her ball pool in the kitchen) Well. |
| rejected | no_boundary_before_cap | Caregiver | 1.0 | speaker_label_inside_response;no_end_of_turn_boundary_before_cap;very_long_first_line_response | no_boundary_before_cap | you said. | huh? Caregiver: You. Is really getting to me. Child: me.? No one takes care of me. I go to school, I play sports, and w... |
| rejected | other_quality_flag | Caregiver | 1.0 | very_long_first_line_response | other_quality_flag | yup. | the urge to answer all these questions in one big breath, the chaos that comes from not giving you the time to answer, ... |
| rejected | repetition_loop | Caregiver | 0.7 | repetition_loop;very_long_first_line_response | repetition_loop | he was called Joshua. the littler boy was called Nathan. | I met Joshua, I met him, I met him, I met him. He was called Joshua. I met him, I met him, I met him. |
| rejected | speaker_label_inside_response | Adult | 1.0 | speaker_label_inside_response;possible_context_copy;very_long_first_line_response | speaker_label_inside_response | you said. | i am an adult. Adult: yeah, but you said you feel like a little kid. Child: no. i don’t. Well…sometimes…you know, when ... |

## Recommendation For Supervisor Meeting

Use this smoke to ask supervisors to approve the operational definition before
Mila-scale production: response entropy over valid one-turn child-response
samples, with rejected attempts retained as diagnostics. The strongest
production candidate remains T=0.5 as primary and T=0.7 as sensitivity if their
rejection rates and prompt rankings remain stable in the tables above.

## Remaining Risks Before Slurm

- Accepted-only entropy conditions on the quality filter; this is defensible
  only because rejection rates are explicitly reported.
- Prompt wrappers can change the measurement object, so prompt-rank stability
  should be reviewed before choosing one production wrapper.
- M=20 is a smoke size. Production still needs a larger accepted sample count
  and a Slurm completion audit.
- Context-copy responses may be valid child-like repetitions or model copying;
  supervisors should decide whether flagged copies remain in production entropy.

## Files

- Accepted samples: `results/response_entropy_final_generation_smoke/accepted_samples.csv.gz`
- All attempts: `results/response_entropy_final_generation_smoke/all_attempts.csv.gz`
- Rejection summary: `results/response_entropy_final_generation_smoke/rejection_summary_by_setting.csv`
- Quality flags: `results/response_entropy_final_generation_smoke/quality_flags_by_setting.csv`
- Prompt/temperature rank correlations: `results/response_entropy_final_generation_smoke/prompt_temperature_rank_correlations.csv`
- Manual review examples: `results/response_entropy_final_generation_smoke/manual_review_examples.csv`
- Smoke manifest: `results/response_entropy_final_generation_smoke/smoke_manifest.csv`
- Smoke manifest audit: `results/response_entropy_final_generation_smoke/smoke_manifest_audit.csv`

## Decision Output

**Can we justify T=0.5 primary and T=0.7 sensitivity?**
Yes, as a smoke-test recommendation.
Observed rejection rates were T=0.5 `7.0%` and T=0.7 `5.0%`;
median prompt rank stability was T=0.5 `0.744` and T=0.7 `0.732`.
The smoke did have `7` incomplete context-temperature-prompt
settings, so production should keep the same attempt-cap audit and flag
pathological contexts rather than silently filling them.

**Does T=0.3 add useful conservative information?**
Yes: it is structurally clean enough to keep as a conservative diagnostic.
Its rejection rate was `7.8%`.

**Should T=1.0 be excluded or kept as an optional diagnostic?**
Keep as an optional diagnostic only, not as the primary production setting.
Its rejection rate was `7.3%`.

**Are rejection rates low enough for production?**
Yes for the proposed T=0.5/T=0.7 production pair, assuming supervisor approval of the rejection policy.

**Are prompt-variant rankings stable enough?**
Yes at smoke-test resolution.
Median prompt-within-temperature Spearman correlation across the smoke was `0.693`.

**What exact questions should be asked of supervisors?**

1. Is the transcript prompt wrapper acceptable: `Caregiver/Parent/Adult: {context}` followed by `Child:`?
2. Should response entropy be estimated over accepted valid child-turn samples only, with rejected attempts reported?
3. Should possible context-copy responses be kept as flagged valid samples, or excluded?
4. Is T=0.5 primary plus T=0.7 sensitivity sufficient for production?
5. Should T=0.3 remain as a conservative diagnostic, and should T=1.0 be excluded unless requested?

