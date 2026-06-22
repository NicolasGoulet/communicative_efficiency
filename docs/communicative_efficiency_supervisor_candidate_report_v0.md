# Candidate Supervisor Report v0: Communicative Efficiency in Child Speech

This is a candidate synthesis, not the final supervisor-facing report. It selects the clearest Route 1 plots, adds heldout regression checks, and states exactly what each line means.

## One-Sentence Story

At the same production effort, real children show an age-related change in utterance information that survives child identity and context-form controls, and PBM-trained models can be checked against unseen children with explicit actual-vs-predicted regression lines.

## Links To The Technical Model Cards

- Real-child Atlas v2 model cards for the implemented M1-M15 ladder: [utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html](utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html)
- Technical implementation companion for OLS, GLM, GEE, MixedLM, fixed effects, clustered SE, and interaction hierarchy: [utterance_information_m1_m6_technical_implementation_companion.html](utterance_information_m1_m6_technical_implementation_companion.html)
- Heldout child prediction report used for the new regression checks: [utterance_information_route1_heldout_real_child_prediction_report.html](utterance_information_route1_heldout_real_child_prediction_report.html)

**Important naming note.** I found implemented model cards for M1-M15. I do not find a real implemented M16 artifact in the current Atlas v2 ladder, so this candidate report does not pretend M16 exists.

## 1. The Two Questions From The Email

![Route map](../figs/supervisor_candidate_report/route1_route2_map.png)

- **What the figure shows:** the split between the current Route 1 evidence and the later Route 2 effort-choice question.
- **How to read it:** Route 1 keeps production effort fixed and predicts utterance information; Route 2 makes effort or length the outcome.
- **What it means here:** this candidate report can support the information-given-effort claim now, while keeping the stronger context-predictability/effort-choice claim parked for the next analysis.
- **Do not overclaim:** the route map is conceptual; it is not a statistical result.

- **Route 1:** Given context and fixed production effort, do children change the information content of their utterances over development?
- **Route 2:** Given context, do children modulate production effort itself, for example producing shorter utterances when context is more predictive?

This candidate report mainly supports Route 1. Route 2 is the next report family once response-space/context-predictability predictors are attached at production scale.

## 2. The Main Line Meaning

In the Atlas v2 fixed-effort plots, a line is not a raw average. It is the fitted regression model asking: **what `sum_bits` would we expect at this age if effort is held fixed and the listed controls are included?**

- **Downward fixed-effort line:** at the same word count, older children are predicted to carry less total information.
- **Upward fixed-effort line:** at the same word count, older children are predicted to carry more total information.
- **Separated low/mid/high effort lines:** longer utterances carry more information, which is why effort must be controlled.
- **Non-parallel effort lines:** the age effect changes depending on effort.

![Source comparison](../figs/supervisor_candidate_report/source_comparison_m4c_k3_words_slopes.png)

- **What the figure shows:** the fitted age slope for each target source, using the same k3 context window, M4c controls, and word-count effort bands.
- **How to read it:** bars left of zero mean predicted `sum_bits` goes down with age at fixed word count; bars right of zero mean it goes up. The three colors are short, medium, and longer utterance bands.
- **What it means here:** real child speech has negative fixed-effort slopes, while the random baseline is positive; n-gram and LSTM baselines mostly show negative slopes but with different magnitudes. This makes the real-child pattern visible against matched generated-target controls.
- **Do not overclaim:** these baselines are sanity checks for source specificity and scoring mechanics, not psychological models of children.

**Clean read:** the real-child fixed-effort slopes are downward in this k3/word M4c view, while the random baseline goes upward. That is a useful sanity check: the developmental line is not just a mechanical consequence of word count or the plotting code.

## 3. What The Best Controlled Model Is Doing

![Model ladder importance](../figs/supervisor_candidate_report/real_k3_words_model_ladder_r2_importance.png)

- **What the figure shows:** how much observed-vs-fitted R2 each real-child k3/word model achieves, and how much each model changes R2 relative to M2.
- **How to read it:** the left panel is absolute fit; the right panel is the small gain or loss after the primary child-identity-plus-effort model. Taller bars mean better in-sample fit, not causal importance.
- **What it means here:** effort and child identity carry the large fit improvement, while question type and richer context controls add smaller but interpretable gains. The age coefficient remains negative in the promoted controlled models.
- **Do not overclaim:** delta-R2 says what improves prediction inside this model family; it does not prove that a predictor causes the information change.

This plot is a variable-importance view, but not a causal ranking. In Advanced Data Analytics terms, it is a nested-model diagnostic: most variance is explained by effort and child identity; context controls add smaller but interpretable gains.

| model | what changed | R2 | delta R2 vs M2 | age effect | effort effect | context entropy | context effort |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Pooled age + effort sanity check; not the main developmental claim. | 0.6130 | -0.0129 | 0.000 bits/month (p=0.993) | 6.35 bits/word (p=<.001) |  (p=) |  (p=) |
| M2 | Primary controlled line: age + effort with child identity fixed effects. | 0.6259 | 0.0000 | -0.122 bits/month (p=<.001) | 6.37 bits/word (p=<.001) |  (p=) |  (p=) |
| M3 | Checks whether the age line changes across effort levels. | 0.6259 | 0.0000 | -0.122 bits/month (p=<.001) | 6.38 bits/word (p=<.001) |  (p=) |  (p=) |
| M4a | Adds preceding caretaker/context effort as a confound control. | 0.6266 | 0.0007 | -0.116 bits/month (p=<.001) | 6.38 bits/word (p=<.001) |  (p=) | -0.070 (p=<.001) |
| M4b | Adds next-token context entropy as a contextual predictability control. | 0.6266 | 0.0007 | -0.126 bits/month (p=<.001) | 6.37 bits/word (p=<.001) | -0.471 (p=<.001) |  (p=) |
| M4c | Adds broad question type, a key context-form confound from the email. | 0.6297 | 0.0038 | -0.127 bits/month (p=<.001) | 6.38 bits/word (p=<.001) |  (p=) |  (p=) |
| M5 | Combines context effort, context entropy, and question type. | 0.6269 | 0.0009 | -0.122 bits/month (p=<.001) | 6.38 bits/word (p=<.001) | -0.468 (p=<.001) | -0.044 (p=<.001) |
| M6 | Tests whether context entropy changes the age/effort relation. | 0.6269 | 0.0010 | -0.123 bits/month (p=<.001) | 6.38 bits/word (p=<.001) | -0.469 (p=<.001) | -0.044 (p=<.001) |
| M15 | Richest current context-interaction stress test. | 0.6285 | 0.0026 | -0.127 bits/month (p=<.001) | 6.42 bits/word (p=<.001) | -0.321 (p=<.001) | -0.034 (p=<.001) |

### One-Line Effect Cards

| arrow | effect | number |
| --- | --- | --- |
| age ↓ | Older children carry less total information at the same word count, after child identity and question type are controlled. | -0.127 bits/month; p=<.001 |
| effort ↑ | Longer utterances carry much more information; this is the mechanical predictor we must hold fixed. | 6.38 bits per extra word; p=<.001 |
| age × effort ≈ flat | In real child speech, the age slope is not strongly different across word-count levels in this model. | -0.0038 bits/month/word; p=0.522 |
| context entropy ↓ | Next-token context entropy is a meaningful control here, but it is not the final Route 2 response-space entropy claim. | -0.469 bits; p=<.001 |
| parent context effort ↓ | Longer preceding caretaker context slightly lowers child utterance information at fixed child effort. | -0.044 bits/context word; p=<.001 |
| question type matters | Question/statement form improves fit, so it belongs as a confound before telling the developmental story. | M4c has the best simple k3/word R2 among the context-control candidates. |

## 4. Heldout Children: Real Regression Line vs Prediction Regression Line

The plot below is the check you asked for. The black dots are actual heldout child data aggregated to month x effort-band cells. The black line is the regression line fitted to those actual heldout points. The teal dashed line is the regression line implied by the PBM-trained prediction for the same child and effort band.

![Heldout regression lines](../figs/supervisor_candidate_report/heldout_pop_m4c_actual_vs_predicted_regression_lines.png)

- **What the figure shows:** for each heldout child and word-count band, the observed heldout monthly trajectory and the PBM-trained model's predicted trajectory.
- **How to read it:** black points are actual heldout child month-by-band means; the black solid line is their fitted actual trend; the teal dashed line is the PBM-trained predicted trend for the same child and effort band.
- **What it means here:** the model can be checked visually on children it did not train on. In this current version, predicted slopes are flatter than several actual heldout slopes, so this is a useful diagnostic rather than the cleanest proof.
- **Do not overclaim:** the heldout panels summarize month/effort cells and should not be read as exact utterance-level predictions.

**Clean read:** this plot makes the generalization claim inspectable. We are no longer asking the reader to infer the regression from a model table; the actual heldout line and predicted line are literally in the same panel.

![Heldout calibration](../figs/supervisor_candidate_report/heldout_pop_m4c_calibration_residuals.png)

- **What the figure shows:** whether PBM-trained monthly predictions match heldout monthly means, and whether prediction errors drift with child age.
- **How to read it:** in the calibration panel, points near the diagonal are better calibrated. In the residual panel, points near zero mean the prediction is close; a sloped residual trend means errors change over development.
- **What it means here:** this separates level accuracy from developmental-shape accuracy: a model can get average information roughly right while still missing age-related changes.
- **Do not overclaim:** calibration and residual plots diagnose prediction quality; they do not replace the source-specific fixed-effort model evidence.

**Clean read:** calibration asks whether high-information months are predicted as high-information months. Residual-over-age asks whether the PBM-trained model misses systematically for younger or older heldout sessions.

## 5. Predictor Relations And Confounds

![Predictor correlations](../figs/supervisor_candidate_report/pbm_real_k3_predictor_correlation_heatmap.png)

- **What the figure shows:** raw Pearson correlations among age, information, effort, and context-predictability variables for PBM real-child k3 rows.
- **How to read it:** red/blue cells show stronger positive or negative pairwise association before regression controls are applied. Values near zero mean little linear pairwise association.
- **What it means here:** the plot explains why controls are needed: effort measures are strongly related to information, and context variables are not independent of the rest of the design.
- **Do not overclaim:** raw correlations are descriptive confound checks, not the final controlled age effect.

This heatmap is intentionally labeled as raw correlation. It is useful for seeing confounding, not for making the final claim. The controlled regression lines above are the actual scientific test.

Confounds handled in the current Route 1 candidate:

- child identity: handled by child fixed effects in Atlas v2 source-specific models;
- repeated utterances within children: primary uncertainty uses child-cluster robust standard errors where available;
- effort/length: held fixed in the plotted fixed-effort lines;
- parent context effort: included in M4a/M5/M6/M15-style controls;
- context predictability: current next-token context entropy is included in M4b/M5/M6/M15; response-space entropy is still Route 2/future-predictor work;
- question/statement type: included in M4c/M5/M12/M13/M15-style controls.

## 6. Regression Assumption Checks

- We should not pretend individual utterance rows are independent. The report therefore uses child fixed effects, child-cluster robust uncertainty, and heldout month/effort-bin summaries for visual checks.
- We should not assume one straight line blindly. Atlas v2 includes nonlinear age checks (M7/M8) and categorical age-bin checks (M9/M10). These belong in the technical appendix, while M2/M4c/M15 carry the clean story.
- We should not call raw correlations variable importance. The report separates raw correlations, nested R2 diagnostics, and controlled coefficient directions.
- We should not overclaim Route 2 from Route 1. Context entropy predicting `sum_bits` is not the same as context predictability predicting child length choice.

## 7. Candidate Model Card Appendix: Implemented M1-M15

| model | question | formula | plain-language role |
| --- | --- | --- | --- |
| M1 | Does age predict target information after controlling target effort, pooling children? | sum_bits ~ age + effort | Pooled age + effort sanity check; not the main developmental claim. |
| M2 | Does the age effect remain after child identity is controlled? | sum_bits ~ age + effort + C(child_id) | Primary controlled line: age + effort with child identity fixed effects. |
| M3 | Does the effort-information relation change with age? | sum_bits ~ age * effort + C(child_id) | Checks whether the age line changes across effort levels. |
| M4a | Does preceding caretaker effort explain additional target information? | sum_bits ~ age * effort + parent_context_effort + C(child_id) | Adds preceding caretaker/context effort as a confound control. |
| M4b | Does context entropy explain additional target information? | sum_bits ~ age * effort + context_entropy + C(child_id) | Adds next-token context entropy as a contextual predictability control. |
| M4c | Does preceding caretaker question type explain additional target information? | sum_bits ~ age * effort + C(question_type) + C(child_id) | Adds broad question type, a key context-form confound from the email. |
| M5 | Do parent effort, context entropy, and question type each matter after age, target effort, and child identity? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + C(child_id) | Combines context effort, context entropy, and question type. |
| M6 | Does context-entropy sensitivity change with age or target effort? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:context_entropy + effort:context_entropy + C(child_id) | Tests whether context entropy changes the age/effort relation. |
| M7 | Does a curved age trajectory explain target information beyond linear age and effort? | sum_bits ~ age + effort + I(age ** 2) + C(child_id) | Nonlinear age check: age plus age squared. |
| M8 | Does the effort-information relation change along a curved age trajectory? | sum_bits ~ age * effort + I(age ** 2) + I(age ** 2):effort + C(child_id) | Nonlinear age-by-effort check. |
| M9 | Do age-bin differences remain after target effort and child identity are controlled? | sum_bits ~ C(age_bin) + effort + C(child_id) | Categorical age-bin check rather than one straight age slope. |
| M10 | Does the effort-information relation differ across developmental age bins? | sum_bits ~ C(age_bin) * effort + C(child_id) | Age-bin-by-effort check. |
| M11 | Does preceding caretaker effort matter differently across development? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:parent_context_effort + C(child_id) | Age-by-parent-context-effort interaction check. |
| M12 | Does the developmental trajectory differ by broad preceding caretaker question type? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:C(question_type) + C(child_id) | Age-by-question-type interaction check. |
| M13 | Does context entropy matter differently after different broad caretaker question types? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + context_entropy:C(question_type) + C(child_id) | Context-entropy-by-question-type interaction check. |
| M14 | Do context entropy and preceding caretaker effort jointly predict target information? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + parent_context_effort:context_entropy + C(child_id) | Parent-context-effort-by-context-entropy interaction check. |
| M15 | Do the main context controls alter the age-effort trajectory under a larger interaction stress test? | sum_bits ~ age * effort + parent_context_effort + context_entropy + C(question_type) + age:context_entropy + effort:context_entropy + age:parent_context_effort + effort:parent_context_effort + context_entropy:C(question_type) + C(child_id) | Richest current context-interaction stress test. |

## Saved Candidate Artifacts

```text
results/supervisor_candidate_report/real_k3_words_model_ladder_importance.csv
results/supervisor_candidate_report/source_comparison_m4c_k3_words_slopes.csv
results/supervisor_candidate_report/heldout_pop_m4c_actual_vs_predicted_regression_slopes.csv
results/supervisor_candidate_report/heldout_pop_m4c_monthly_calibration.csv
results/supervisor_candidate_report/pbm_real_k3_predictor_correlations.csv
figs/supervisor_candidate_report/
```
