# Hall Snapshot: Mistral Predictability at Approximately Age Four

## Bottom line

The Hall snapshot is fully scored and locally audited. The analysis includes
36 primary children and
70,510 primary utterances. All estimates
below are **descriptive, scorer-indexed contrasts**, not causal effects of race
or social class and not measures of linguistic worth or inherent communicative
efficiency.

At fixed cleaned word count and recorded setting, the primary unconditional
Mistral model shows a race-by-class interaction of **-3.52
bits** (child-clustered 95% CI [-5.73,
-1.30]). The stratified 1,000-child bootstrap interval is
[-5.75, -1.26]. This
means there is no scientifically honest single “race effect”: the Black-minus-
White contrast is 3.08 bits within WC but
-0.44 bits within UC. Conversely, UC-minus-WC is
-3.54 bits within the Black-labelled sample and
-0.03 bits within the White-labelled sample.
The interaction remains negative when each child is omitted in turn (range
[-4.10, -2.90] bits).

The contextual k3 interaction after an immediately preceding adult turn is
-3.25 bits (95% CI [-5.71,
-0.79]). The corresponding interaction for context
support, defined as k0 − k3, is -0.21 bits (95% CI
[-1.11, 0.68]). Thus the
group pattern is visible in Mistral target predictability, while the present
analysis does not show the same clear interaction in how much the preceding
adult context reduces surprisal.
Its leave-one-child interaction range is [-0.36,
0.03] bits, which reinforces that this context-support
contrast is not stable away from zero.

The locked age-matched comparison estimates Hall minus the current
naturalistic corpora at 3.04 unconditional bits at
fixed word count (95% CI [2.04,
4.03]; bootstrap [2.10,
3.98]). This is **not a causal cohort effect**:
Hall differs in recording era, geography, setting composition, transcription,
dialect distribution, and likely Mistral training representation. Eleven of
the 20 locked comparison children come from Wells, so corpus influence remains
important.
The Hall-minus-current estimate remains positive when each current corpus is
omitted in turn (range [2.81,
3.19] bits).

## Primary within-Hall result

![Adjusted unconditional surprisal by historical Hall stratum](../figs/hall_snapshot_analysis/hall_k0_adjusted_by_stratum.png)

The model is a weighted regression over child × setting × exact/top-coded word
count cells. It includes race, class, their interaction, setting, and exact
word-effort controls; uncertainty is clustered by child. Positive differences
mean that Mistral assigned more surprisal, or lower model-based predictability,
to the observed utterance at the same modeled effort.

![Registered within-Hall contrasts](../figs/hall_snapshot_analysis/hall_primary_registered_contrasts.png)

## Contextual predictability and context support

![Contextual surprisal after an adult turn](../figs/hall_snapshot_analysis/hall_k3_adjusted_by_stratum.png)

![Context support after an adult turn](../figs/hall_snapshot_analysis/hall_context_gain_adjusted_by_stratum.png)

Context support is k0 − k3. Larger positive values mean the preceding adult
utterances made the observed child utterance more predictable to Mistral.
Contextual analyses first restrict to genuine immediate child-after-adult
turns within the same recorded situation. “Adult” is retained as a role label;
not every adult is assumed to be a caregiver.

## Sensitivity analyses

![Within-Hall interaction sensitivities](../figs/hall_snapshot_analysis/hall_interaction_sensitivities.png)

The model family separately checks the 37th folder-inferred child, exact age,
sex, equal-child weighting, home-only and school-only observations, k1/k2/k3
context windows, and all context-available turns. These are sensitivities, not
replacements for the frozen primary model.

| model_id | contrast_id | estimate | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- |
| H1_k0_primary | race_by_class_interaction | -3.516 | -5.730 | -1.302 | 0.002 |
| H2_k0_all37 | race_by_class_interaction | -3.614 | -5.795 | -1.434 | 0.001 |
| H3_k0_sex_control | race_by_class_interaction | -3.515 | -5.726 | -1.305 | 0.002 |
| H4_k0_age_control | race_by_class_interaction | -3.566 | -5.826 | -1.306 | 0.002 |
| H5_k0_home | race_by_class_interaction | -2.387 | -4.971 | 0.198 | 0.070 |
| H6_k0_school | race_by_class_interaction | -5.334 | -7.174 | -3.493 | 0.000 |
| H7_k0_equal_child | race_by_class_interaction | -3.426 | -5.558 | -1.293 | 0.002 |
| H8_k3_adult_adjacent | race_by_class_interaction | -3.249 | -5.710 | -0.788 | 0.010 |
| H9_gain_k3_adult_adjacent | race_by_class_interaction | -0.213 | -1.105 | 0.679 | 0.640 |
| H10_gain_k1_adult_adjacent | race_by_class_interaction | -0.304 | -1.000 | 0.391 | 0.391 |
| H11_gain_k2_adult_adjacent | race_by_class_interaction | -0.308 | -1.149 | 0.533 | 0.473 |
| H12_k3_all_context | race_by_class_interaction | -3.362 | -5.962 | -0.761 | 0.011 |
| H13_gain_k3_all_context | race_by_class_interaction | -0.150 | -1.015 | 0.715 | 0.734 |
| E1_k0_locked_snapshot | hall_minus_current | 3.037 | 2.041 | 4.032 | 0.000 |
| E2_k0_age_control | hall_minus_current | 3.028 | 2.074 | 3.982 | 0.000 |
| E3_k0_hall_home | hall_minus_current | 2.934 | 1.919 | 3.949 | 0.000 |
| E4_k0_non_pbm | hall_minus_current | 3.068 | 2.003 | 4.132 | 0.000 |
| E5_k0_equal_child | hall_minus_current | 3.267 | 2.328 | 4.207 | 0.000 |
| E6_k3_locked_snapshot | hall_minus_current | 2.631 | 1.325 | 3.938 | 0.000 |
| E7_gain_k3_locked_snapshot | hall_minus_current | 0.374 | -0.400 | 1.149 | 0.343 |

## Locked external snapshot

![Hall and locked current-corpus predictions](../figs/hall_snapshot_analysis/external_locked_snapshot_predictions.png)

![External comparison sensitivities](../figs/hall_snapshot_analysis/external_snapshot_sensitivities.png)

Each current-corpus child contributes one outcome-blind session nearest 57
months within 54–59 months. PBM and non-PBM provenance remains recorded; a
non-PBM-only comparison, Hall-home restriction, age control, equal-child
weighting, contextual outcome, context-support outcome, and leave-one-current-
corpus influence audit are retained.

## Support and descriptive child distribution

![Hall sample support by setting and stratum](../figs/hall_snapshot_analysis/hall_setting_stratum_support.png)

![Child-level descriptive score distribution](../figs/hall_snapshot_analysis/hall_child_descriptive_distribution.png)

The child distribution uses bits per cleaned word only as a descriptive view.
It is not the primary fixed-effort estimand.

## Interpretation limits

- Mistral surprisal is model-based self-information, not a direct behavioral
  measure of what human listeners understand.
- Historical Hall race and class codes are corpus strata. They must not be
  converted into claims of linguistic deficit, innate difference, or causal
  socioeconomic effects.
- Dialect, orthography, disfluency transcription, recording situation,
  historical era, and model training representation can all change scores.
- Hall is a separate cross-sectional snapshot. It is not an 80th longitudinal
  child and does not alter the frozen PBM/non-PBM developmental analyses.
- The external comparison is guarded domain-shift evidence. It cannot isolate
  development, cohort, geography, transcription, or dialect.

## Audit summary

- Scorer: Mistral-7B-v0.3, frozen revision `caa1feb0e54d415e2df31207e5f4e273e33509b1`.
- Score archive: 4/4 k0–k3 contracts, 287,320 utterance rows, archive SHA-256
  `c7c2422f19f87a0096136f73bf3a1fa664f5551ed095371920b3462db6d21202`.
- Models: 20/20
  passed; 0 failed.
- Bootstrap: 1000 stratified child
  resamples for each registered primary bootstrap model.
- Plot audit: 9/9 figures
  present and nonempty.
