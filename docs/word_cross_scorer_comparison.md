# PBM Word-Information Cross-Scorer Comparison

Mistral, Qwen3-14B, and TinyDialogues were fit separately on the same registered word-occurrence estimands. **Raw coefficient magnitudes are not treated as calibrated across tokenizers.** This report compares direction, uncertainty labels, occurrence coverage, and child-level sign agreement.

- All registered primary-model coefficient directions shared by all scorers: `14/28`. This broad diagnostic includes nuisance controls and is not the scientific headline.
- PBM is one discovery sample; scorer repetition is robustness, not independent-sample confirmation.

## Question-by-question evidence

| Scientific question | Common direction | Cluster interval support | Bootstrap interval support | Assessment |
| --- | --- | ---: | ---: | --- |
| Does unconditional surprisal for the same word decrease with age? | negative | 3/3 | 3/3 | direction_and_interval_robust |
| Does contextual surprisal for the same word decrease with age? | negative | 3/3 | 3/3 | direction_and_interval_robust |
| Does word-level context gain change with age? | mixed | 1/3 | 1/3 | scorer_dependent |
| At the centered age, do longer word types receive more contextual support? | positive | 3/3 | 3/3 | direction_and_interval_robust |
| Does the longer-word context-support association change with age? | negative | 2/3 | 2/3 | direction_robust_partial_uncertainty |
| Does the rarity-context-support association change with age? | mixed | 2/3 | 2/3 | scorer_dependent |
| Within word type, does the age trend in context gain vary by word length? | negative | 2/3 | 3/3 | direction_robust_partial_uncertainty |
| Does the within-utterance k3 information-position gradient change with age? | positive | 1/3 | 0/0 | direction_robust_partial_uncertainty |

- Direction and interval robust across scorers: Does unconditional surprisal for the same word decrease with age?; Does contextual surprisal for the same word decrease with age?; At the centered age, do longer word types receive more contextual support?.
- Scorer-dependent direction: Does word-level context gain change with age?; Does the rarity-context-support association change with age?.

![Scientific question evidence](../figs/word_cross_scorer_comparison/scientific_question_evidence_matrix.png)

Filled circles mark scorer-specific clustered 95% intervals excluding zero; open circles include zero. Child-bootstrap support is reported separately in the table.

## Full registered-coefficient diagnostic

![Primary direction matrix](../figs/word_cross_scorer_comparison/primary_effect_direction_matrix.png)

## Child-level agreement

![Child slope sign agreement](../figs/word_cross_scorer_comparison/child_slope_sign_agreement.png)

## Guardrails

- Word surprisal is scorer-based predictability, not semantic information or listener utility.
- Positive context gain means k3 context reduced surprisal for the exact word occurrence.
- A difference in raw bits or bits/month between models is not interpreted as a calibrated effect-size difference.
- Null and contrary directions remain visible.
