# August 2026 supervisor report

This report integrates the frozen longitudinal, word-level, generated-reference, corrected candidate-set Bayes, response-uncertainty, onset, and Hall evidence. It states the estimand and evidence status for each claim and leaves missing analyses pending.

## Executive reading

The central result is narrow but coherent: development is associated with greater model-based predictability of form at fixed measured effort. The report separates evidence labels so directional robustness is not mistaken for sample confirmation.

| Evidence label | Meaning in this report |
|---|---|
| Supported | The frozen estimate and uncertainty support the registered reading. |
| Qualified | The direction or scoped association is informative, but a stated gate limits promotion. |
| Contrary | The result runs opposite to the preregistered or frozen directional prediction. |
| Descriptive | The comparison is explicitly non-causal and outside longitudinal confirmation. |
| Pending | The required evidence or validation has not yet been completed. |

**Supported.** In PBM discovery, older children's forms are more predictable at the same measured effort; the same-word direction is also robust across the three separately fit scorers.

**Qualified.** The separate non-PBM contextual association points in the same direction but is not confirmed because the frozen primary child-clustered interval crosses zero; child-resampling remains a sensitivity, not a replacement decision rule.

**Contrary.** Context gain declines rather than rises, and the principal response-uncertainty interaction also runs opposite to its registered positive prediction.

**Pending.** A broad communicative-success claim remains pending: target surprisal is not listener utility, and no validated downstream listener-relevant outcome is registered.

## Sample logic

The report uses discovery, confirmation, scorer-robustness, and cross-sectional samples for different inferential jobs. They are never pooled into one evidential label.

**Supported.** PBM is the 21-child discovery sample. TinyDialogues reuses those children, so agreement is scorer robustness rather than an independent replication.

**Qualified.** The remaining 58 children form the distinct non-PBM confirmation sample; its frozen primary contextual result keeps the qualified label.

**Pending.** The proposed conversationally responsive sample remains at review stage: the 325-row manual validation and resolution of 18,172 context-k1 mismatches are still required.

## Utterance predictability at fixed effort

The estimand is scorer self-information conditional on measured word effort and child baseline. Lower surprisal means greater scorer-based predictability or conventionality of form.

**Supported.** The negative fixed-effort age direction is supported for PBM with Mistral and repeats with TinyDialogues on the same children. It is not listener utility, greater Shannon information communicated, or proof of optimization.

**Qualified.** The paired scorer comparison supports directional robustness, but tokenizer and calibration differences prevent a universal cross-model magnitude interpretation.

**Qualified.** The non-PBM estimate is direction-consistent but not confirmed under the primary clustered interval. The child-resampling interval is reported beside it only as sensitivity evidence.

![Two-panel interval plot. The PBM discovery panel shows a negative contextual-surprisal age slope whose interval remains below zero. The non-PBM panel shows the clustered primary interval crossing zero and a separately labelled child-resampling sensitivity interval below zero.](../results/august_supervisor_report/plots/figure_01_fixed_effort_predictability.png)

*Figure caption.* Fixed-effort contextual Mistral age slopes. The 21-child PBM discovery estimate is supported; the separate 58-child primary estimate is direction-consistent but not confirmed because its clustered interval crosses zero. The child-resampling interval is shown only as sensitivity.

### Technical companions

- [Direct Results Explorer](direct_surprisal_results_explorer.html)

## Word-level findings across three scorers

The word analysis compares separate scorer-specific fits on the exact shared PBM word-occurrence set. Raw bits and coefficients are not pooled across tokenizers.

**Supported.** Same-word unconditional and contextual age directions are interval-supported in all three scorer-specific fits. This is same-sample robustness, not confirmation in the remaining 58 children.

**Supported.** Longer word types receive more contextual support in all three separate fits, while remaining a lexical and scorer-indexed association rather than a listener-utility result.

**Qualified.** Word-level context-gain development is scorer-dependent, with mixed signs. Direction and uncertainty may be compared, but raw magnitudes have no registered pooled interpretation.

**Pending.** No remaining-58 word estimate is available for promotion; the registered production, audit, and frozen analysis must finish before this result can be tested out of sample.

![A categorical matrix with separate columns for Mistral, Qwen3-14B, and TinyDialogues. Every scorer column shows negative, interval-supported same-word predictability directions and positive, interval-supported longer-word context support. A separate band states that context-gain development has mixed signs across scorers.](../results/august_supervisor_report/plots/figure_03_word_cross_scorer_signs.png)

*Figure caption.* Categorical word-level readings on the exact shared PBM occurrence set. All three separately fit scorers support negative same-word k0 and k3 age directions and positive context support for longer word types. Development of word-level context gain has mixed signs and remains scorer-dependent.

### Technical companions

- [Word Cross Scorer Comparison](word_cross_scorer_comparison.html)

## Unconditional and contextual decomposition

Contextual surprisal, unconditional surprisal, and context gain answer different questions. The decomposition keeps conventionality of form separate from the support supplied by preceding context.

**Supported.** Unconditional surprisal declines with age in PBM under both scorers and is also supported in the non-PBM Mistral sample. That association is distinct from contextual support.

**Contrary.** Utterance context gain declines in PBM under both scorers and in the non-PBM sample. This repeated negative direction is contrary to the frozen positive prediction, not confirmation of it.

![Three independent interval-plot panels: PBM Mistral discovery, PBM TinyDialogues scorer robustness, and non-PBM Mistral confirmation. Each panel shows unconditional, contextual, and context-gain age slopes. The three context-gain marks are highlighted as contrary negative directions.](../results/august_supervisor_report/plots/figure_02_unconditional_contextual_components.png)

*Figure caption.* Registered fixed-effort age slopes for unconditional surprisal, contextual surprisal, and context gain. PBM Mistral discovery, same-child TinyDialogues robustness, and non-PBM Mistral confirmation are isolated on independent axes. All registered context-gain slopes are negative, contrary to the frozen positive developmental prediction.

### Technical companions

- [Formal Definitions](july_meeting_definitions.html)

## Generated baselines and corrected candidate-set Bayes evidence

Generated alternatives are useful reference distributions and diagnostics. They do not define a meaning-preserving choice set for the child.

**Qualified.** Generated alternatives are model-based references or diagnostics and are not meaning-preserving. They cannot support Pareto-optimality or intended-meaning choice claims.

**Supported.** Within the supplied matched candidate set, the observed utterance ranks first on 43.7% of real rows and has mean candidate-set probability 0.400. This is not a posterior over every possible utterance.

**Supported.** The corrected context-evidence calculation passes the registered matched-versus-shuffled validation in all three held-out corpora. That validates the decomposition mechanics, not meaning preservation or a universal posterior.

### Technical companions

- [Corrected Bayes](corrected_pbm_bayes_report.html)

## Response uncertainty and effort adaptation

This analysis compares observed child effort with a generated response reference. The generated expectation can mediate contextual demand, so the result is kept distinct from raw effort.

**Qualified.** Observed effort relative to the model-generated reference increases with age, but the association is measurement-limited by the coupled generator and scorer.

**Contrary.** The principal age-by-response-entropy interaction is negative, opposite to the simple prediction that older children would increasingly lengthen responses as uncertainty rises.

**Qualified.** The present measure is exact-string response entropy. It is not semantic uncertainty and is model-, prompt-, temperature-, and seed-dependent.

**Pending.** Semantic clustering, rarefaction, settings sensitivity, and a decoupled generator comparison remain pending before the response-space hypothesis can receive a stronger reading.

![Two independent interval panels. The left panel shows a positive age association for observed word effort relative to a generated reference. The right panel shows a negative age-by-response-entropy interaction, labelled contrary to the registered positive prediction.](../results/august_supervisor_report/plots/figure_04_route2_qualification.png)

*Figure caption.* Registered response-space relative-effort associations on 976 PBM child-session aggregates. Relative effort increases with age, while the age-by-exact-string-entropy interaction is negative, opposite the simple lengthening prediction. Independent axes preserve the two different units.

## Developmental onset

The registered onset question requires a decrease that is sustained under simultaneous uncertainty, rather than selecting a favorable pointwise age contrast.

**Qualified.** Sustained onset is not established in either PBM discovery or the 58-child non-PBM confirmation sample. The earlier nominal 24-29-month PBM contrast is not promoted as onset.

**Pending.** Equivalent sustained-onset tests with validated morpheme, syllable, and phoneme effort controls remain pending.

![Two separate status cards, one for PBM discovery and one for non-PBM confirmation. Both cards read not established under the frozen simultaneous sustained-onset rule; no numeric onset age is displayed.](../results/august_supervisor_report/plots/figure_05_sustained_onset_status.png)

*Figure caption.* Categorical outcomes of the frozen simultaneous sustained-onset rule. Sustained onset is not established in either the 21-child PBM discovery sample or the separate 58-child non-PBM confirmation sample. No pointwise age-bin contrast is substituted for the registered rule.

### Technical companions

- [Sustained Onset](direct_surprisal_onset_confirmation.html)

## Hall: a separate historical snapshot

Hall is treated as a historical cross-sectional and domain-sensitivity analysis, separate from longitudinal development. Its scorer-indexed stratum contrasts are descriptive.

**Descriptive.** The within-Hall race-by-class interaction is a historical, scorer-indexed comparison at fixed cleaned word count and setting. It is not a causal SES effect, linguistic deficit, or inherent group difference.

**Descriptive.** The adult-adjacent context-support interaction has an interval crossing zero, so there is no clear interaction under the frozen scorer and specification.

**Descriptive.** The Hall-minus-current contrast is evidence of sensitivity to domain, era, dialect, geography, transcription, setting, and model representation—not a causal cohort comparison.

![Three Hall-only interval panels with different labelled horizontal scales. The historical race-by-class interaction is negative, the adult-adjacent context-support interval crosses zero, and the guarded Hall-minus-current domain-shift contrast is positive. Each panel is marked descriptive.](../results/august_supervisor_report/plots/figure_06_hall_snapshot.png)

*Figure caption.* Hall-only descriptive snapshot with independent axes for the registered race-by-class k0 interaction, adult-adjacent context-support interaction, and guarded Hall-minus-current domain shift. These scorer-indexed contrasts are historical, non-causal, and separate from development.

### Technical companions

- [Hall Snapshot](hall_snapshot_mistral_analysis.html)

## Conclusions and next decisive tests

The evidence supports a constrained developmental claim about scorer predictability at fixed lexical effort. It does not yet support a single normative efficiency optimum or a general claim about communicative success.

**Pending.** First, complete and audit the remaining-child same-pass word scores, then apply the already frozen word protocol.

**Pending.** Second, finish blinded manual validation before promoting a caregiver-responsive conversational sample.

**Pending.** Third, define and validate a downstream caregiver-response, repair, clarification, acknowledgement, or contingency outcome.

**Pending.** Fourth, calibrate response uncertainty semantically and across generation settings, including a decoupled generator.

**Pending.** Finally, repeat the frozen sustained-onset rule only after the alternative effort measures pass validation.

### Technical companions

- [Child Trajectories](paired_tinydialogues_mistral_child_trajectories.html)

- [Technical Analysis Inventory](complete_analysis_machine_index.html)
