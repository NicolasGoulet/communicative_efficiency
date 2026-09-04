# Three-scorer predictive-performance comparison

On contextual child speech, **Mistral-7B** has the lowest child-balanced BPC (2.137); the ordering is Mistral-7B < Qwen3-14B < TinyDialogues-135M.

This report compares Mistral-7B-v0.3, Qwen3-14B, and TinyDialogues-135M on
exactly paired targets. **Lower bits per character (BPC) means less surprise
on this evaluation set.** BPC, not bits per model token, is the primary
cross-tokenizer metric.

## Main answer

- Contextual child-speech ranking (`k3`): **Mistral-7B < Qwen3-14B < TinyDialogues-135M**.
- Unconditional child-speech ranking (`k0`): **TinyDialogues-135M < Mistral-7B < Qwen3-14B**.
- Matched-context caregiver-response ranking: **Mistral-7B < Qwen3-14B < TinyDialogues-135M**.
- Qwen result: **more surprised than Mistral in all seven evaluated conditions**.
- Tiny result: **less surprised without context, but more surprised than Mistral in every contextual condition**.
- These are corpus-specific cross-entropy rankings. They are not a general
  ranking of semantic competence, child knowledge, or usefulness.

## Primary and stress-test estimates

| scope | model | n items | n children | child balanced bpc | child bootstrap ci low | child bootstrap ci high | bpc rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| caregiver response · matched child | Mistral-7B | 413084 | 79 | 1.3739 | 1.3412 | 1.4066 | 1.0000 |
| caregiver response · matched child | Qwen3-14B | 413084 | 79 | 1.4819 | 1.4468 | 1.5185 | 2.0000 |
| caregiver response · matched child | TinyDialogues-135M | 413084 | 79 | 2.3364 | 2.2893 | 2.3946 | 3.0000 |
| caregiver response · unconditional | TinyDialogues-135M | 413084 | 79 | 2.3460 | 2.3004 | 2.3968 | 1.0000 |
| caregiver response · unconditional | Mistral-7B | 413084 | 79 | 2.5236 | 2.4749 | 2.5711 | 2.0000 |
| caregiver response · unconditional | Qwen3-14B | 413084 | 79 | 3.4109 | 3.3577 | 3.4644 | 3.0000 |
| child utterance · k0 | TinyDialogues-135M | 446508 | 21 | 2.8946 | 2.8163 | 2.9784 | 1.0000 |
| child utterance · k0 | Mistral-7B | 446508 | 21 | 3.2793 | 3.1621 | 3.4015 | 2.0000 |
| child utterance · k0 | Qwen3-14B | 446508 | 21 | 4.1336 | 4.0093 | 4.2624 | 3.0000 |
| child utterance · k3 | Mistral-7B | 443848 | 21 | 2.1367 | 2.0648 | 2.2084 | 1.0000 |
| child utterance · k3 | Qwen3-14B | 443848 | 21 | 2.2818 | 2.2038 | 2.3604 | 2.0000 |
| child utterance · k3 | TinyDialogues-135M | 443848 | 21 | 2.9300 | 2.8486 | 3.0231 | 3.0000 |

Intervals are deterministic 10,000-resample whole-child bootstrap intervals.
The child-utterance domain contains 446,508 exact
targets across four contexts (1,778,052 paired score rows),
21 children, and three corpora. The secondary caregiver-response domain
contains 413,084 exact primary response
targets across 79 children and
13 corpora.

## Direct comparisons with Mistral

Every difference below is `candidate BPC - Mistral BPC`. Negative values mean
the candidate is less surprised.

| domain | condition | candidate model | child balanced bpc difference | child bootstrap ci low | child bootstrap ci high | candidate lower item share | assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| child_utterance | k0 | Qwen3-14B | 0.8543 | 0.8310 | 0.8788 | 0.1026 | Mistral-7B_lower |
| child_utterance | k0 | TinyDialogues-135M | -0.3847 | -0.4450 | -0.3261 | 0.8048 | TinyDialogues-135M_lower |
| child_utterance | k3 | Qwen3-14B | 0.1451 | 0.1342 | 0.1566 | 0.3363 | Mistral-7B_lower |
| child_utterance | k3 | TinyDialogues-135M | 0.7933 | 0.7480 | 0.8434 | 0.1456 | Mistral-7B_lower |
| caregiver_response | unconditional | Qwen3-14B | 0.8873 | 0.8736 | 0.9013 | 0.0732 | Mistral-7B_lower |
| caregiver_response | unconditional | TinyDialogues-135M | -0.1775 | -0.2134 | -0.1341 | 0.7495 | TinyDialogues-135M_lower |
| caregiver_response | matched_child | Qwen3-14B | 0.1079 | 0.1020 | 0.1139 | 0.3691 | Mistral-7B_lower |
| caregiver_response | matched_child | TinyDialogues-135M | 0.9625 | 0.9271 | 1.0059 | 0.0466 | Mistral-7B_lower |

At `k3`, Mistral is lower for all 21 child aggregates and for
66.4%
of individual targets against Qwen; it is lower for all 21 child aggregates
and 85.4%
of targets against TinyDialogues.

## Robustness and heterogeneity

- The contextual ordering is identical
  in all 13 utterance-length cells and
  identical in all
  8 observed age bins.
- Every leave-one-corpus-out estimate
  retains Mistral's advantage over both alternatives for `k3` child speech
  and matched-child caregiver responses.
- Qwen gains more from context than Mistral, but begins from a much worse
  unconditional score and remains 0.145
  BPC more surprised at `k3`.
- TinyDialogues' child-speech context support is near zero and slightly
  negative; this explains its reversal from the best unconditional score to
  the worst contextual score.

## Context use

Positive support means context reduced target surprisal.

| domain | contrast | model | child balanced support bpc | child bootstrap ci low | child bootstrap ci high | context lowers surprisal item share |
| --- | --- | --- | --- | --- | --- | --- |
| child_utterance | k0_minus_k3 | Mistral-7B | 1.1436 | 1.0725 | 1.2095 | 0.9884 |
| child_utterance | k0_minus_k3 | Qwen3-14B | 1.8528 | 1.7673 | 1.9345 | 0.9904 |
| child_utterance | k0_minus_k3 | TinyDialogues-135M | -0.0347 | -0.0499 | -0.0187 | 0.4541 |
| caregiver_response | unconditional_minus_matched_child | Mistral-7B | 1.1497 | 1.1149 | 1.1852 | 0.9973 |
| caregiver_response | unconditional_minus_matched_child | Qwen3-14B | 1.9291 | 1.8872 | 1.9690 | 0.9987 |
| caregiver_response | unconditional_minus_matched_child | TinyDialogues-135M | 0.0097 | -0.0057 | 0.0230 | 0.4707 |

## Figures

![Overall Bpc Forest](../figs/scorer_performance_comparison_20260904/overall_bpc_forest.png)

![Historical Style By Length](../figs/scorer_performance_comparison_20260904/historical_style_by_length.png)

![Historical Style By Age](../figs/scorer_performance_comparison_20260904/historical_style_by_age.png)

![Paired Difference Forest](../figs/scorer_performance_comparison_20260904/paired_difference_forest.png)

![Winner Shares](../figs/scorer_performance_comparison_20260904/winner_shares.png)

![Context Support](../figs/scorer_performance_comparison_20260904/context_support.png)

![Corpus Robustness](../figs/scorer_performance_comparison_20260904/corpus_robustness.png)

![Tokenization Diagnostic](../figs/scorer_performance_comparison_20260904/tokenization_diagnostic.png)

![Model Size Vs Bpc](../figs/scorer_performance_comparison_20260904/model_size_vs_bpc.png)

![Paired Score Hexbin](../figs/scorer_performance_comparison_20260904/paired_score_hexbin.png)

## Historical bridge

The new length and age analyses reuse the aggregation structure of these two
historical T7 scripts:

- `/mnt/d/EvaPortelance/Projet_1/surprisal_computing/proj_1/src/plot_surprisal_vs_length.py` (SHA-256 `2779ea0e644dfdfa6e6146b0b77e3d06be78ed3d4e566d0ffd975558b2d1684a`)
- `/mnt/d/EvaPortelance/Projet_1/surprisal_computing/proj_1/src/plot_surprisal_vs_length_by_model_age_schemes.py` (SHA-256 `48190975733d5e25cc93d2fb5b7a0002e47c1118eca12585a982cb97283e1f8f`)

The historical plots ranked models with token-weighted bits per token. That
quantity remains in the tokenization diagnostic, but the new ranking uses BPC
because the three current scorers have different tokenizers.

## Provenance and scoring compatibility

All three child-score retrieval audits and the shared caregiver-dataset audit
are `PASS`. Recomputed BPC and BPW agree exactly with the stored fields. Qwen's
tensor-valued `logits_to_keep` path limits vocabulary projection to target
positions; the shared scorer's equivalence tests compare it with the full-logit
path. The later Qwen scoring revision changed its batch size from 2 to 16 and
loaded contract source frames lazily; an explicit git diff found no change to
the target-log-softmax derivation. No evaluated child-utterance context required token truncation.

| scorer | model id | model revision | tokenizer revision | scoring code revision | dtype | max length | prediction prefix policy | truncated context rows | max context tokens truncated | audit status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mistral-7B | mistralai/Mistral-7B-v0.3 | caa1feb0e54d415e2df31207e5f4e273e33509b1 | caa1feb0e54d415e2df31207e5f4e273e33509b1 | e890ec1bbe34204c9388bbf53aba8121a685d89b | fp16 | 4096.0000 | tokenizer_bos | 0.0000 | 0.0000 | PASS |
| Qwen3-14B | Qwen/Qwen3-14B | 40c069824f4251a91eefaf281ebe4c544efd3e18 | 40c069824f4251a91eefaf281ebe4c544efd3e18 | c82d2196bd708b14a94359420363d4c38941aad4 | bf16 | 4096.0000 | inject_model_bos_if_missing | 0.0000 | 0.0000 | PASS |
| TinyDialogues-135M | LaurensWink/SmolLM2-135M_variants | 149fd0d6f069ef7b0a915474c86367c7d34c1591 | 149fd0d6f069ef7b0a915474c86367c7d34c1591 | e890ec1bbe34204c9388bbf53aba8121a685d89b | fp32 | 256.0000 | tokenizer_bos | 0.0000 | 0.0000 | PASS |

## Interpretation and publication limits

- The primary comparison is an exact-paired PBM21 child-speech evaluation; the
  caregiver-response analysis is a broader role/corpus stress test.
- Model size is confounded with training data, domain exposure, architecture,
  tokenizer, precision, and scoring conventions. Three models cannot establish
  a scaling law.
- TinyDialogues was trained for child-directed dialogue. Domain match can
  matter more than parameter count.
- Lower scorer surprisal is predictive fit to the observed string. It is not
  semantic information, listener utility, or evidence of a communicative
  optimum.

Protocol: `docs/scorer_performance_comparison_protocol_2026-09-04.md`.
