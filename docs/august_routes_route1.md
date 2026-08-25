<div class="report-nav" aria-label="Report pages"><a href="august_routes_report.html">Data overview</a><a class="active" href="august_routes_route1.html">Route 1</a><a href="august_routes_route2.html">Route 2</a><a href="august_routes_word_level.html">Word level</a></div>

# Route 1 — utterance surprisal at fixed effort

**Question.** At the same measured word effort, does contextual self-information of the child's utterance change with age?

> Main result: PBM Mistral and same-child TinyDialogues lines are negative after child adjustment. The separate non-PBM Mistral estimate is also negative, but its frozen primary clustered interval crosses zero, so the confirmation criterion is not met.

## Route 1 results

### Model 0 — raw developmental trajectories

The raw lines show what changes with age before adjustment. They mix development with longer utterances, child composition, and corpus composition, so they orient the reader but do not answer the fixed-effort question.

![Route 1 raw regression lines](../results/august_routes_report/plots/route1_model0_raw_lines.png)

### Model 1 — control measured effort

```text
contextual utterance surprisal ~ age + exact/top-coded word count
```

These fitted lines compare utterances at the same word count but omit child identity. This effort-only HC1 model is a diagnostic bridge from the raw plot, not a registered primary claim.

![Route 1 effort-only regression lines](../results/august_routes_report/plots/route1_model1_effort_only_lines.png)

| sample | age_estimate | ci_low | ci_high | p_value | children | source_rows |
| --- | --- | --- | --- | --- | --- | --- |
| Mistral — PBM discovery | -0.016 | -0.026 | -0.005 | 0.003 | 21 | 444325 |
| TinyDialogues — PBM robustness | -0.080 | -0.096 | -0.065 | 8.44e-25 | 21 | 443848 |
| Mistral — non-PBM confirmation | -0.087 | -0.094 | -0.081 | 1.41e-145 | 58 | 678071 |

### Model 2 — control child identity

```text
contextual utterance surprisal ~ age + exact/top-coded word count + child identity
```

This is the registered primary design. Exact word-effort cells are weighted by their utterance counts, stable between-child differences are absorbed, and uncertainty is clustered or bootstrapped by whole child.

![Route 1 child-adjusted regression lines](../results/august_routes_report/plots/route1_model2_child_adjusted_lines.png)

### Model 3 — nonlinear and repeated-measures checks

The final figure compares the child-fixed WLS primary line with a quadratic-age curve, a Mundlak within/between-child decomposition, population-average GEE, and an available random-age mixed-model sensitivity. Their slopes and curvature are the comparison; intercepts and weighting differ.

![Route 1 nonlinear, Mundlak, GEE, and mixed-model lines](../results/august_routes_report/plots/route1_model3_complex_lines.png)

The mixed sensitivity uses unweighted design cells and is not a replacement for the weighted primary model. Singular fits are omitted. The frozen primary interval remains the decision rule for non-PBM confirmation.

#### Mistral PBM discovery

| model | estimate | ci_low | ci_high | p_value | adjustment |
| --- | --- | --- | --- | --- | --- |
| Linear child-adjusted | -0.131 | -0.179 | -0.083 | 7.70e-08 | exact word-effort cells; child fixed effects; 95% interval clustered by child |
| Nonlinear age | -0.155 | -0.228 | -0.082 | 2.89e-05 | adds age squared; reported coefficient is the local slope at centered age; child fixed effects; clustered by child |
| Within/between child | -0.133 | -0.182 | -0.084 | 8.42e-08 | separates within-child age from between-child mean age; corpus controls; clustered by child |
| Repeated-measures GEE | -0.152 | -0.200 | -0.104 | 5.74e-10 | Gaussian GEE with exchangeable within-child correlation; exact word-effort controls |

#### TinyDialogues PBM scorer robustness

| model | estimate | ci_low | ci_high | p_value | adjustment |
| --- | --- | --- | --- | --- | --- |
| Linear child-adjusted | -0.222 | -0.311 | -0.132 | 1.24e-06 | exact word-effort cells; child fixed effects; 95% interval clustered by child |
| Nonlinear age | -0.272 | -0.391 | -0.153 | 7.06e-06 | adds age squared; reported coefficient is the local slope at centered age; child fixed effects; clustered by child |
| Within/between child | -0.221 | -0.313 | -0.130 | 2.09e-06 | separates within-child age from between-child mean age; corpus controls; clustered by child |
| Repeated-measures GEE | -0.226 | -0.311 | -0.141 | 1.86e-07 | Gaussian GEE with exchangeable within-child correlation; exact word-effort controls |

#### Mistral non-PBM confirmation

| model | estimate | ci_low | ci_high | p_value | adjustment |
| --- | --- | --- | --- | --- | --- |
| Linear child-adjusted | -0.062 | -0.132 | 0.007 | 0.079 | exact word-effort cells; child fixed effects; 95% interval clustered by child |
| Nonlinear age | -0.089 | -0.160 | -0.018 | 0.014 | adds age squared; reported coefficient is the local slope at centered age; child fixed effects; clustered by child |
| Within/between child | -0.062 | -0.131 | 0.007 | 0.080 | separates within-child age from between-child mean age; corpus controls; clustered by child |
| Repeated-measures GEE | -0.104 | — | — | — | Gaussian GEE with exchangeable within-child correlation; exact word-effort controls |

## Route 1 conclusion

The strongest supported claim is narrow: within PBM discovery, older children's utterances are more predictable to the scorer at the same exact/top-coded word effort after child identity is controlled. TinyDialogues repeats the direction on the same children. The non-PBM primary result remains qualified because its registered interval includes zero.

<div class="next-page">Next: <a href="august_routes_route2.html">Route 2 — effort relative to response space →</a></div>
