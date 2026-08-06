# Current Scientific Answer Across Route 1, Route 2, and Word Information

This synthesis reads audited saved artifacts only. It does not select or refit models after seeing outcomes. The current machine contains **607 fitted variants or registered outcome fits**, plus the corrected Bayes decomposition and its validation products.

## Bottom line

1. **Predictability at fixed effort develops, but the independent-sample result is weaker than the discovery result.** Mistral PBM contextual surprisal decreases by `-0.131` bits/month at fixed exact/top-coded word effort (95% CI `[-0.179, -0.083]`). TinyDialogues gives the same negative PBM direction (`-0.222`, CI `[-0.311, -0.132]`). The frozen non-PBM58 Mistral estimate is also negative (`-0.062`), but its clustered interval `[-0.132, 0.007]` crosses zero, so it **does not meet the frozen confirmation criterion**.
2. **The form-development component is stronger than the contextual-support-development component.** In non-PBM58, unconditional surprisal decreases with age (`-0.089`, CI `[-0.145, -0.034]`). Utterance context gain also decreases (`-0.028`, CI `[-0.045, -0.010]`), opposite the registered positive direction. This favors increasing conventionality/predictability of form over a claim that older children increasingly exploit preceding context.
3. **Word-level evidence sharpens that distinction.** Same-word k0 and k3 surprisal decrease with age under all three scorers with all three clustered and bootstrap intervals excluding zero. Longer word types receive more contextual support at the centered age under all three scorers. In contrast, developmental change in overall word-level context gain is scorer-dependent, and the rarity-by-age result is also scorer-dependent.
4. **Route 2 shows catch-up toward a generated length reference, not the predicted stronger adaptation under high uncertainty.** The final session-GEE estimate for age is `0.089` words/month relative to the generated mean, while age × exact-string response entropy is `-0.025` (CI `[-0.038, -0.011]`). Thus catch-up is weaker in higher-entropy contexts. This remains model/prompt/temperature dependent and is not semantic response uncertainty.
5. **A discrete onset is not established.** Under 1,000 child bootstraps and simultaneous bands: pbm_discovery: not established, non_pbm_confirmation: not established.

![Current evidence map](../figs/current_scientific_synthesis/evidence_map.png)

## Route 1 direct estimates

| sample | scorer | question | estimate | ci_low | ci_high | evidence_status |
| --- | --- | --- | --- | --- | --- | --- |
| PBM21 scorer robustness | TinyDialogues | Contextual utterance surprisal at fixed word effort | -0.222 | -0.311 | -0.132 | supported_association |
| PBM21 scorer robustness | TinyDialogues | Unconditional utterance surprisal at fixed word effort | -0.254 | -0.339 | -0.168 | supported_association |
| PBM21 scorer robustness | TinyDialogues | Utterance context gain (k0 − k3) | -0.032 | -0.050 | -0.014 | contrary_to_registered_direction |
| PBM21 discovery | Mistral | Contextual utterance surprisal at fixed word effort | -0.131 | -0.179 | -0.083 | supported_association |
| PBM21 discovery | Mistral | Unconditional utterance surprisal at fixed word effort | -0.162 | -0.211 | -0.112 | supported_association |
| PBM21 discovery | Mistral | Utterance context gain (k0 − k3) | -0.030 | -0.050 | -0.011 | contrary_to_registered_direction |
| non-PBM58 confirmation | Mistral | Contextual utterance surprisal at fixed word effort | -0.062 | -0.132 | 0.007 | direction_consistent_not_confirmed |
| non-PBM58 confirmation | Mistral | Unconditional utterance surprisal at fixed word effort | -0.089 | -0.145 | -0.034 | supported_association |
| non-PBM58 confirmation | Mistral | Utterance context gain (k0 − k3) | -0.028 | -0.045 | -0.010 | contrary_to_registered_direction |

Raw coefficient magnitudes are never pooled across tokenizers. PBM scorer repetition is robustness, not independent-sample confirmation.

## Route 2 final relative-effort estimates

| outcome | term | estimate | conf_low | conf_high | evidence_status |
| --- | --- | --- | --- | --- | --- |
| child_words_minus_generated_mean | age_months_c | 0.0895 | 0.0777 | 0.1013 | measurement_limited_association |
| child_words_minus_generated_mean | age_months_c:response_entropy_bits_c | -0.0248 | -0.0384 | -0.0112 | measurement_limited_association |
| child_words_percentile_in_generated_distribution | age_months_c | 0.0108 | 0.0090 | 0.0125 | measurement_limited_association |
| child_words_percentile_in_generated_distribution | age_months_c:response_entropy_bits_c | -0.0034 | -0.0047 | -0.0022 | measurement_limited_association |

Raw child effort and effort relative to a generated response distribution are separate estimands. The generated expected effort term is part of the reference construction and is not automatically treated as an ordinary confound.

## Word-information questions

| question | common_direction | cluster_supported_scorers | bootstrap_supported_scorers | replication_status |
| --- | --- | --- | --- | --- |
| Does unconditional surprisal for the same word decrease with age? | negative | 3 | 3 | direction_and_interval_robust |
| Does contextual surprisal for the same word decrease with age? | negative | 3 | 3 | direction_and_interval_robust |
| Does word-level context gain change with age? | mixed | 1 | 1 | scorer_dependent |
| At the centered age, do longer word types receive more contextual support? | positive | 3 | 3 | direction_and_interval_robust |
| Does the longer-word context-support association change with age? | negative | 2 | 2 | direction_robust_partial_uncertainty |
| Does the rarity-context-support association change with age? | mixed | 2 | 2 | scorer_dependent |
| Within word type, does the age trend in context gain vary by word length? | negative | 2 | 3 | direction_robust_partial_uncertainty |
| Does the within-utterance k3 information-position gradient change with age? | positive | 1 | 0 | direction_robust_partial_uncertainty |

The three word scorers use the same exact 1,032,963-occurrence primary set, but each scorer was fit separately. The strongest cross-scorer statements are about direction and within-scorer uncertainty, not raw bit magnitudes.

## Fit inventory

| family | fitted_variants | status |
| --- | --- | --- |
| Direct TinyDialogues PBM | 34 | PASS_WITH_RECORDED_SENSITIVITIES |
| Direct Mistral full-79 | 102 | PASS_WITH_RECORDED_SENSITIVITIES |
| Paired TinyDialogues–Mistral | 11 | PASS |
| Route 1 model zoo | 56 | PASS |
| Route 1 explicit comparisons | 45 | PASS |
| Route 2 response space | 48 | PASS |
| Route 2 relative effort | 144 | PASS |
| PBM word Mistral | 55 | PASS |
| PBM word Qwen3-14B | 55 | PASS |
| PBM word TinyDialogues | 55 | PASS |
| Frozen sustained-onset tests | 2 | PASS |

## What the current models do not answer

- They do not provide a validated listener-utility outcome or show that children optimize a single efficiency objective.
- Route 2 still needs semantic clustering, rarefaction, prompt/temperature/seed calibration, and the incoming Qwen-generated/Mistral-scored decoupled-response product before a stronger uncertainty claim.
- The 58-child word-level Mistral confirmation remains blocked until its 232 same-pass contracts are scored and audited on Mila.
- The caregiver-responsive subset remains a future sensitivity until the 18,172 context mismatches and 325-row manual validation sample are adjudicated.
- Morpheme, syllable, and phoneme effort controls need validation before the frozen onset rule is repeated with those measures.

## Best next tests

1. Finish the Qwen-response/Mistral-scoring calibration smoke, then run the predeclared production gate and compare exact-string entropy, length reference, and scored response distributions without calling them semantic equivalents.
2. Run the remaining-58 same-pass Mistral word DAG and apply the already frozen word protocol without changing thresholds or formulas.
3. Add a downstream caregiver-response predictive-gain or validated repair/clarification outcome; that is the clearest route from model predictability toward listener-relevant utility.
