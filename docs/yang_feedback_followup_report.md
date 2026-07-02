# Yang Feedback Follow-up
This is a technical follow-up to the supervisor-facing report. It does not replace the main report.
## Point-by-point response
1. **Question being answered.** The current Route 1 analyses mainly answer: what factors predict or modulate the informativeness of child speech? They show modulation of child `sum_bits` after controlling age, child effort, and child identity.
2. **Caretaker-context interpretation.** The current Model 4 context predictors are `parent_context_nb_words` and `context_entropy_bits`. The entropy variable is next-token uncertainty after the preceding caretaker context; it is not identical to caretaker utterance informativeness. Therefore, this follow-up adds a direct companion predictor: the summed k0 `sum_bits` of the previous up-to-three caretaker utterances.
3. **Concrete examples.** The table below gives illustrative matched cases where child word count is the same within the pair. These examples are for intuition only; the regression is the evidential test.
4. **Context window clarification.** `k1`, `k2`, and `k3` mean previous caretaker utterances, not words. The supervisor-report Model 4 uses `k3`: up to three previous caretaker utterances in the same session. There is no word cap inside each caretaker utterance beyond the fact that the window is bounded to three utterances.
5. **Effort analogue.** A first-pass child-effort model is included below: child word count is predicted from age, preceding-context effort, context entropy, and child identity. This is the natural next Route 1 sibling model.
6. **When modulation emerges.** Two plots below visualize whether context modulation changes with age: one using continuous age interactions, and one using age-bin-specific context coefficients.
## Model summary
| model | term | estimate | 95% CI | p | n | R2 |
| --- | --- | --- | --- | --- | --- | --- |
| M4 current context controls | parent_context_words_c | -0.0428 | -0.0592 to -0.0264 | <.001 | 441413 | 0.627 |
| M4 current context controls | context_entropy_c | -0.4698 | -0.5440 to -0.3956 | <.001 | 441413 | 0.627 |
| Direct caretaker information | parent_context_words_c | 0.0694 | 0.0329 to 0.1058 | <.001 | 441413 | 0.627 |
| Direct caretaker information | prior_caretaker_sum_bits_c | -0.0194 | -0.0249 to -0.0139 | <.001 | 441413 | 0.627 |
| Age-varying informativeness modulation | parent_context_words_c | -0.0415 | -0.0620 to -0.0210 | <.001 | 441413 | 0.627 |
| Age-varying informativeness modulation | context_entropy_c | -0.4678 | -0.5364 to -0.3991 | <.001 | 441413 | 0.627 |
| Age-varying informativeness modulation | age_c:parent_context_words_c | -0.0035 | -0.0062 to -9.06e-04 | 0.008 | 441413 | 0.627 |
| Age-varying informativeness modulation | age_c:context_entropy_c | 0.0075 | -0.0032 to 0.0182 | 0.170 | 441413 | 0.627 |
| Child effort modulation | parent_context_words_c | 0.0023 | -0.0013 to 0.0060 | 0.213 | 441413 | 0.133 |
| Child effort modulation | context_entropy_c | 0.0102 | 0.0013 to 0.0190 | 0.024 | 441413 | 0.133 |
| Age-varying child effort modulation | parent_context_words_c | 0.0025 | -0.0014 to 0.0065 | 0.213 | 441413 | 0.133 |
| Age-varying child effort modulation | context_entropy_c | 0.0100 | 0.0011 to 0.0189 | 0.027 | 441413 | 0.133 |
| Age-varying child effort modulation | age_c:parent_context_words_c | -4.53e-04 | -0.0011 to 1.59e-04 | 0.147 | 441413 | 0.133 |
| Age-varying child effort modulation | age_c:context_entropy_c | -0.0012 | -0.0023 to -1.30e-04 | 0.029 | 441413 | 0.133 |
## Matched examples
| age_bin | child_words | high_context_words | high_context_bits | high_context_child_bits | high_context_text | high_context_child_response | low_context_words | low_context_bits | low_context_child_bits | low_context_text | low_context_child_response |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 048-053 | 7 | 40 | 299.5 | 14.7 | when the little fish had learned to swim together like one giant fish he said I'll be the eye. d you know why he was going to be the eye? why d you think he's going to b... | why he's going to be the eye? | 6 | 104.9 | 120.1 | your what? no no Adam. yes. | I wan a show Pucilia Urs la. |
| 024-029 | 8 | 30 | 218.6 | 7.2 | way far away from the bridge and the crack and the track. he went as far as he could. oh me oh my oh me oh my he sa:id. | oh me oh my oh me oh my. | 6 | 111.3 | 110.4 | orzo? yum! they are so lucky. | I think Loley Worm's going to pour orzo. |
| 024-029 | 6 | 19 | 216.1 | 11.5 | Shamu. do you can you introduce your friends to Amanda? hello Shamu do they both swim in the sea? | they both swim in the sea. | 8 | 107.4 | 112.8 | those aren't beans they're peas. what else? no. | man too_man Hum z_Dum. |
Saved full example table:
```text
results/yang_followup/matched_context_examples.csv
```
## Age-varying modulation plots
![Age-varying informativeness modulation](../figs/yang_followup/age_varying_informativeness_modulation.png)
![Age-varying effort modulation](../figs/yang_followup/age_varying_effort_modulation.png)
![Age-bin modulation coefficients](../figs/yang_followup/age_bin_modulation_coefficients.png)
## Original near-optimality question
The original question asks whether children are near-optimally informative, not just whether their informativeness is modulated. The present Route 1 results are evidence for modulation, but not a full optimality test. A stronger optimality test needs counterfactual alternatives for the same context and comparable effort, then asks where the real child utterance lies relative to those alternatives or an effort-information frontier.
Route 2 is the closer bridge to that question: for each caretaker context, generate/sample possible child responses, score their effort and informativeness, and compare the actual child response to the response set. The current Route 2 response-space entropy work is therefore not a distraction; it is the machinery needed to define the alternative response space for an optimality-style analysis.
## Saved artifacts
```text
Rows: 441,413
results/yang_followup/yang_followup_analysis_rows.csv.gz
results/yang_followup/yang_followup_model_summary.csv
results/yang_followup/age_bin_modulation_coefficients.csv
figs/yang_followup/
```
