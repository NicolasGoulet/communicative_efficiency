<div class="report-nav" aria-label="Report pages"><a href="august_routes_report.html">Data overview</a><a href="august_routes_route1.html">Route 1</a><a class="active" href="august_routes_route2.html">Route 2</a><a href="august_routes_word_level.html">Word level</a></div>

# Route 2 — effort relative to a generated response space

**Question.** Relative to responses generated for the same context, does child word effort change with age and exact-string response uncertainty? This is a different estimand from Route 1.

> Main result: relative effort increases with age, but the age-by-response-entropy interaction is negative in the principal session models—the opposite of the original simple positive-interaction prediction.

## Route 2 results

### Model 0 — raw relative-effort trajectories

Observed child utterances lengthen with age, but generated expected length also changes. Raw child effort and effort relative to the generated distribution therefore stay separate.

![Route 2 raw trajectories](../results/august_routes_report/plots/route2_model0_raw_lines.png)

### Model 1 — age and child identity

The simplest adjusted model asks whether relative effort changes with age after stable child differences are controlled. It does not yet ask whether contextual uncertainty changes the developmental trajectory.

### Model 2 — add response entropy and situation-specific controls

```text
relative effort ~ age * response entropy
                + generated expected words
                + context word count + next-token context entropy
                + child identity
```

The lines hold other continuous predictors at their saved reference values and show low, middle, and high exact-string response entropy.

![Route 2 fully adjusted regression lines](../results/august_routes_report/plots/route2_model2_adjusted_lines.png)

### Model 3 — GEE, Mundlak, and mixed-effects checks

The comparison includes an utterance-level child-fixed model, child-session GEE, within/between-child Mundlak GEE, and a random-intercept/random-age mixed model. These handle longitudinal repetition differently and keep estimator sensitivity visible.

![Route 2 GEE, Mundlak, and mixed-model regression lines](../results/august_routes_report/plots/route2_model3_complex_lines.png)

#### Fully adjusted age terms

| model | estimate | ci_low | ci_high | p_value | adjustment |
| --- | --- | --- | --- | --- | --- |
| Linear child-fixed baseline | 0.093 | 0.080 | 0.106 | 3.39e-43 | utterance rows; child fixed effects; uncertainty clustered by child |
| Session GEE | 0.089 | 0.078 | 0.101 | 3.15e-50 | child-session means; exchangeable repeated observations grouped by child |
| Within/between-child GEE | 0.089 | 0.078 | 0.100 | 4.83e-56 | separates within-child age from child mean age; grouped by child |
| Mixed model | 0.102 | 0.090 | 0.114 | 7.00e-60 | child-session means; random child intercept and age slope |

#### Fully adjusted age × response-entropy terms

| model | estimate | ci_low | ci_high | p_value | adjustment |
| --- | --- | --- | --- | --- | --- |
| Linear child-fixed baseline | 1.82e-04 | -0.001 | 0.002 | 0.814 | utterance rows; child fixed effects; uncertainty clustered by child |
| Session GEE | -0.025 | -0.038 | -0.011 | 3.58e-04 | child-session means; exchangeable repeated observations grouped by child |
| Within/between-child GEE | -0.023 | -0.047 | 0.001 | 0.065 | separates within-child age from child mean age; grouped by child |
| Mixed model | -0.024 | -0.033 | -0.016 | 7.38e-08 | child-session means; random child intercept and age slope |

## Route 2 conclusion

The session GEE and mixed model support a positive age association in relative effort and a negative age-by-entropy interaction. The utterance-level fixed-effect model does not show the same interaction, so aggregation and estimator sensitivity remain part of the result. Exact-string entropy is model-, prompt-, temperature-, seed-, and surface-form-dependent; it is not semantic uncertainty or listener utility.

<div class="next-page">Next: <a href="august_routes_word_level.html">Word-level surprisal →</a></div>
