# New Efforts Working Report

This report collects the newest work in one browsable place. It is separate from the formal July supervisor-facing pages, so we can inspect the evidence before deciding what to promote.

## Pages

| page | what_it_answers | link |
| --- | --- | --- |
| When CE Kicks In | Developmental onset, fixed-effort age-bin timing, and context-modulation timing. | [open](new_efforts_ce_kickoff.html) |
| Bayes-Decomposed Surprisal | The new p(u) plus p(c\|u) information family and its relation to direct Mistral surprisal. | [open](new_efforts_bayes_surprisal.html) |
| Complexity Metrics | MLU-style, syllable/phoneme proxy, and lexical complexity predictors. | [open](new_efforts_complexity_metrics.html) |
| Promotion Plan | What should move into the supervisor-facing July pages, and what needs robustness first. | [open](new_efforts_promotion_plan.html) |

## Current Read Across The New Work

| topic | current_read |
| --- | --- |
| CE onset | Fixed-word-count decrease starts in 024-029; context entropy is visible in 006-023. |
| Bayes surprisal | Trigram baseline is 1.98 Bayes bits/token and 1.30 Mistral bits/token above real child utterances. |
| Complexity metrics | MLU rises by 024-029: mean words/utterance is 2.35, with CI [2.09, 2.61]. |

## Highest-Level Onset Table

| signal | operational_definition | earliest_age_bin | estimate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| Continuous fixed-word-count age slope | utterance-level OLS with child fixed effects, exact/top-coded word-count controls, child-clustered SEs | whole range | -0.132 | -0.180 | -0.083 |
| Earliest exact-word-count age-bin decrease | age-bin model relative to 006-023 with child fixed effects and exact/top-coded word-count controls | 024-029 | -0.913 | -1.584 | -0.243 |
| context entropy modulation | age-specific regression coefficient predicting child total bits | 006-023 | -0.435 |  |  |
| parent context words modulation | age-specific regression coefficient predicting child total bits | 024-029 | -0.028 |  |  |
| Direct Mistral paired gap against trigram | same-context generated baseline minus real child bits/token; positive means real child has lower bits | 006-023 | 0.745 | 0.576 | 0.913 |
| Bayes decomposition paired gap against trigram | same-context generated baseline minus real child bits/token; positive means real child has lower bits | 006-023 | 1.604 | 1.055 | 2.154 |

## Existing Full Working Reports

- [Developmental onset working report](developmental_onset_working_report.html)
- [Bayes-decomposed informativeness working report](bayes_information_working_report.html)
