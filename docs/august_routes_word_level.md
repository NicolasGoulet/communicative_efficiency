<div class="report-nav" aria-label="Report pages"><a href="august_routes_report.html">Data overview</a><a href="august_routes_route1.html">Route 1</a><a href="august_routes_route2.html">Route 2</a><a class="active" href="august_routes_word_level.html">Word level</a></div>

# Word-level surprisal

**Question.** Does the information assigned to the same lexical item change with child age, and does preceding context support different word types differently?

> Main result: unconditional and contextual same-word surprisal decline with age in all three separately fitted PBM scorers. Development of word-level context gain is scorer-dependent.

## Word-level results

### Model 0 — descriptive trajectories for common words

These raw age-bin trajectories follow repeatedly observed words. Different lexical items occupy different surprisal levels, so the descriptive plot motivates—but cannot replace—the same-word model.

![Common-word descriptive trajectories](../results/august_routes_report/plots/word_model0_common_word_lines.png)

### Model 1 — compare the same word within children

```text
word surprisal ~ age + position + utterance length + singleton
                 + child identity + word identity
```

The primary model absorbs child and word identity and controls within-utterance position, utterance length, and singleton utterances. The plotted lines are centered at 36 months because the absorbed fixed effects identify developmental change rather than one universal intercept. Bands use 1,000 whole-child bootstrap replicates.

![Child- and word-adjusted regression lines](../results/august_routes_report/plots/word_model1_adjusted_lines.png)

Mistral, Qwen3-14B, and TinyDialogues are fit and displayed separately. Directions and interval support can be compared; raw bit magnitudes cannot be pooled across their tokenizers.

### Model 2 — nonlinear age sensitivity

The quadratic-age curve checks whether a single straight line hides curvature. It is a registered sensitivity, not a selected replacement for the linear primary model.

![Linear and nonlinear same-word regression lines](../results/august_routes_report/plots/word_model2_nonlinear_lines.png)

| question | scorer | estimate | ci_low | ci_high | bootstrap_ci_low | bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| Same-word unconditional age slope | Mistral | -0.049 | -0.055 | -0.043 | -0.057 | -0.042 |
| Same-word unconditional age slope | Qwen3-14B | -0.024 | -0.036 | -0.012 | -0.034 | -0.008 |
| Same-word unconditional age slope | TinyDialogues | -0.050 | -0.059 | -0.042 | -0.063 | -0.042 |
| Same-word contextual age slope | Mistral | -0.019 | -0.032 | -0.007 | -0.030 | -0.005 |
| Same-word contextual age slope | Qwen3-14B | -0.027 | -0.040 | -0.014 | -0.039 | -0.012 |
| Same-word contextual age slope | TinyDialogues | -0.050 | -0.058 | -0.041 | -0.064 | -0.042 |
| Word context-gain age slope | Mistral | -0.030 | -0.038 | -0.021 | -0.040 | -0.023 |
| Word context-gain age slope | Qwen3-14B | 0.002 | -0.006 | 0.011 | -0.007 | 0.013 |
| Word context-gain age slope | TinyDialogues | -6.55e-04 | -0.003 | 0.001 | -0.002 | 0.002 |
| Longer-word context support | Mistral | 0.312 | 0.285 | 0.340 | 0.282 | 0.341 |
| Longer-word context support | Qwen3-14B | 0.642 | 0.578 | 0.706 | 0.534 | 0.700 |
| Longer-word context support | TinyDialogues | 0.062 | 0.050 | 0.075 | 0.050 | 0.076 |

## Word-level conclusion

All three scorer-specific fits support negative unconditional and contextual same-word age slopes. Mistral shows a negative word context-gain slope, while the Qwen3-14B and TinyDialogues intervals include zero. Longer word types receive more contextual support in all three fits. Because every scorer uses the same 21 PBM children and exact shared occurrence set, this is scorer robustness rather than confirmation in the remaining 58 children.

## Return to the full evidence package

- [Data overview](august_routes_report.html)
- [Original audited August package](august_supervisor_index.html)
- [Complete August supervisor report](august_supervisor_report.html)
- [Word cross-scorer technical comparison](word_cross_scorer_comparison.html)
