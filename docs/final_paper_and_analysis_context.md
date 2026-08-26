# Complete Research Context for the Final Paper and Final Analyses

**Project:** On Communicative Efficiency of Child Language Use

**Evidence snapshot:** 26 August 2026

**Purpose:** self-contained handoff for discussing the scientific story, deciding the final analyses, and writing the paper

**Repository:** `communicative_efficiency`

## How to use this document

This document is meant to be pasted into, or read by, another model that has no prior knowledge of the project. It describes:

- the scientific questions and the exact constructs being measured;
- the datasets, sample roles, scorers, generated baselines, and response spaces;
- the completed statistical analyses and their exact headline estimates;
- the results that were supported, qualified, contrary to prediction, descriptive, or still pending;
- the completed all-79-child Qwen/Mistral response-space analysis and the
  completed-but-not-yet-imported all-79 additive-LSTM score handoff;
- the claims that are and are not licensed by the evidence;
- the remaining decisions needed before the final paper can be frozen.

The intended use is not to rerun every historical analysis. The goal is to decide which results form one coherent paper, finish only the genuinely missing analyses, and write the paper without inflating the claims.

When local files conflict, prioritize the dated analysis-ready state in this document and the current `AGENTS.md`, followed by the audited August report. Some older reports remain scientifically useful as development history but have been superseded on particular questions, especially developmental onset, the original Bayes pilot, and whether the all-79 response-space data exist.

## Executive scientific summary

The strongest result is narrow and coherent:

> In longitudinal naturalistic child speech, older children's utterance forms are more predictable to neural language models at the same measured lexical effort in the 21-child Brown–Manchester–Providence discovery sample. The same direction appears under both Mistral and TinyDialogues. In the separate 58-child Mistral confirmation sample, the estimate points in the same direction, but the frozen primary child-clustered interval crosses zero, so the registered confirmation criterion is not met.

Several results prevent a broader, simpler “children become more communicatively efficient” conclusion:

1. Unconditional utterance surprisal declines more strongly than contextual utterance surprisal. Consequently, context gain also declines with age. The data are more consistent with increasing model-based conventionality or predictability of form than with the preregistered prediction that preceding context supplies increasing support with age.
2. In the existing 21-child generated-response analysis, children produce more words relative to a model-generated length reference as they age, but the principal age-by-exact-string-response-entropy interaction is negative. This is contrary to the simple prediction that older children increasingly lengthen responses when response uncertainty is high.
3. Word-level same-word predictability effects are robust across three separately fit scorers on the same PBM children, but word-level developmental changes in context gain and rarity-related support are scorer-dependent.
4. A discrete sustained developmental onset is not established in either the discovery or confirmation sample under simultaneous child-bootstrap bands.
5. No validated listener-relevant utility outcome has yet been analyzed. Target surprisal is not comprehension, communicative success, or evidence that children optimize a normative objective.

The all-79 Qwen-generated/Mistral-scored response space and its main
conditional effort/cloud analysis are now complete and audited: 645,524
contexts, exactly 100 responses per context, 64,552,400 scored responses, 15/15
registered nonlinear models, and 38/38 final audit checks. At 42 months, the
pooled absolute-length ratio from response-entropy p10 to p90 is 1.028 [1.014,
1.043], whereas the Qwen-relative effort odds ratio is 0.931 [0.902, 0.962].
The estimands differ and the relative-effort result reverses developmentally;
the simple prediction of uniformly stronger entropy-conditioned lengthening is
not supported.

The full-79 same-length additive-LSTM generation and separate Mistral `k0`/`k3`
scoring are also complete for 1,140,218 targets and all 79 children. That
immutable compute handoff is local, but it has not yet been linked into this
analysis repository or incorporated into the fixed-effort cloud atlas. No
additional LSTM generation or scoring is needed.

## Evidence labels used throughout

| Label | Meaning |
| --- | --- |
| **Supported** | The frozen estimate and its registered uncertainty support the stated, narrowly defined association. |
| **Qualified** | The direction or scoped association is informative, but a registered gate, sensitivity, or measurement limitation prevents a stronger claim. |
| **Contrary** | The estimate runs opposite to the frozen or preregistered directional prediction. This is a result, not a failed analysis. |
| **Descriptive** | The result is explicitly non-causal, outside the discovery/confirmation logic, or based on a model-generated reference. |
| **Pending** | Required data validation, modeling, or construct validation has not been completed. |

## The conceptual structure of the project

The working title uses “communicative efficiency,” but no single existing variable directly measures communicative efficiency. The project currently separates four analysis tracks.

### 1. Utterance-level predictability

This track asks whether unconditional utterance surprisal, contextual utterance surprisal, and context support change with child age when measured production effort and stable child identity are controlled.

The central estimand is information at fixed effort:

```text
contextual utterance surprisal ~ age + exact/top-coded word effort + child identity
```

A negative age coefficient means that the scorer assigns lower self-information to older children's observed utterances at the same measured word effort. The correct interpretation is greater scorer-based predictability or conventionality of form. It is not “more Shannon information communicated.”

### 2. Utterance-level effort adaptation

This track asks whether production effort changes with age and conversational conditions. It contains two distinct estimands:

- raw child effort, such as words, morphemes, syllables, or phoneme proxies;
- child effort relative to the distribution of free-length responses generated for the same context.

Generated expected effort is part of a model-based reference distribution. It may mediate contextual demand and therefore should not automatically be inserted as an ordinary confound into the primary raw-effort model.

### 3. Word-level contextual support

This track asks whether the same lexical item becomes more predictable with age and whether word properties such as length and leave-corpus-out frequency relate to contextual support. Word identity, child identity, utterance position, utterance length, and singleton status are controlled where relevant.

The word analysis uses three separately fit scorers on the exact same PBM occurrence set. Agreement is scorer robustness within one discovery sample, not independent-sample confirmation.

### 4. Joint information-effort response clouds

This completed track locates each observed child utterance in the
information-by-effort cloud of 100 Qwen responses to the same conversational
context. The generated responses have Mistral k0 and k3 utterance scores and
their text supplies lexical effort and exact-string response entropy. The
audited outputs are under `results/full79_joint_efficiency_analysis/`, with the
consultation view at `docs/full79_joint_efficiency_explorer.html`.

This is a generated-response-space comparison. It does not define a meaning-preserving choice set and cannot show that the observed utterance is Pareto-optimal, rationally chosen, or globally efficient.

## Core notation and measurements

Let `u` be a target utterance and `c_k` be up to `k` preceding caregiver utterances.

### Utterance surprisal

Unconditional utterance surprisal:

```math
S_0(u) = -\log_2 p(u)
```

Contextual utterance surprisal:

```math
S_k(u \mid c_k) = -\log_2 p(u \mid c_k)
```

The main contextual condition is `k3`, using up to three preceding caregiver utterances. `k1` and `k2` are available as context-window sensitivities. `k0` means no preceding conversational context.

Lower surprisal means greater predictability under that scorer. Direct target surprisal is self-information of the observed string, not semantic content and not listener utility.

### Context gain or context support

```math
G_k(u,c_k) = S_0(u) - S_k(u \mid c_k)
```

Equivalently, this is `log2 p(u | c_k) - log2 p(u)`. Positive values mean that the preceding context makes the exact observed target more probable under the scorer.

Context gain must be kept separate from contextual surprisal. A decrease in contextual surprisal can occur because the utterance form becomes more conventional overall, because the context becomes more supportive, or both.

### Generated-candidate gap

For a generated candidate `g` paired to the same row:

```math
\Delta_g = S_k(g \mid c_k) - S_k(u_{real} \mid c_k)
```

Positive values mean the generated candidate is more surprising than the observed child utterance under the scorer. Random, unigram, bigram, trigram, and additive LSTM candidates are matched in word count to the observed utterance. They cannot be used to test effort because their effort was fixed by construction.

### Effort

The primary validated effort control in the direct utterance analyses is cleaned lexical word count. Exact word counts are modeled through 11 words, with rare longer utterances top-coded as `12_plus`.

Available PBM exploratory complexity measures include:

- cleaned words;
- CHAT-derived morpheme counts;
- estimated syllables;
- phoneme proxies;
- MLU-style means;
- vocabulary size and type-token-ratio summaries;
- character length and lexical frequency measures.

These measures are not equally validated across all 79 children. Words remain the primary all-79 effort measure until morphology and phonological proxies pass corpus-level audits.

### Exact-string response entropy

For 100 sampled response strings to a context, with empirical string probabilities `p_j`:

```math
H_{string}(c) = -\sum_j p_j \log_2 p_j
```

This measures surface-string diversity under a specific generator, prompt, temperature, seed policy, and sample count. It is not semantic response uncertainty. Duplicate strings matter and should normally retain their sampling multiplicity; a distinct-string-weighted sensitivity would answer a different question.

### Listener-relevant utility

No validated listener-utility outcome is currently available. Candidate future outcomes include:

- improvement in predicting the next caregiver response when the child utterance is observed;
- contingent continuation;
- acknowledgement;
- repair or clarification requests;
- validated conversational-success labels.

Until one of these is built and validated, the paper must distinguish model predictability from communicative success.

## Longitudinal data

### Corpus selection

The main dataset contains 79 longitudinally observed children from 13 strict-naturalistic CHILDES corpora. The recordings primarily involve spontaneous family, home, or play interaction.

The 13 corpora are:

- Belfast
- Brown
- Demetras1
- Forrester
- Kuczaj
- Lara
- MPI-EVA-Manchester
- Manchester
- Post
- Providence
- Sachs
- Weist
- Wells

Champaign and EHS are excluded because they are more task-structured. Cummings is a clinical/probe corpus and its local preparation lacks caregiver rows. Hall is treated separately because it is a historical cross-sectional sociolinguistic snapshot, not a longitudinal corpus. Thomas was not locally available when the bundle was assembled.

### Sample roles

| Scope | Children | Corpora | Child utterances | Context-bearing child rows for Mistral k3 | Caregiver utterances | Sessions | Inferential role |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Brown, Manchester, Providence | 21 | 3 | 446,985 | 444,325 | 668,903 | 983 | discovery |
| Other 10 corpora | 58 | 10 | 693,710 | 678,071 | 801,251 | 1,770 | independent confirmation |
| All 13 corpora | 79 | 13 | 1,140,695 | 1,122,396 | 1,470,154 | 2,753 | pooled description only |

The discovery and confirmation estimates must remain separately reported. The all-79 estimate is useful descriptively but cannot substitute for the frozen confirmation result.

### Corpus-level coverage

| Corpus | Children | Child utterances | Sessions | Observed ages in months |
| --- | ---: | ---: | ---: | --- |
| Belfast | 8 | 22,942 | 90 | 24.1–54.2 |
| Brown | 3 | 92,555 | 214 | 18.0–62.4 |
| Demetras1 | 1 | 6,842 | 26 | 24.9–47.9 |
| Forrester | 1 | 6,663 | 35 | 12.0–60.0 |
| Kuczaj | 1 | 37,109 | 210 | 28.8–60.4 |
| Lara | 1 | 49,328 | 120 | 21.4–39.8 |
| MPI-EVA-Manchester | 4 | 462,100 | 687 | 24.0–61.6 |
| Manchester | 12 | 232,614 | 408 | 20.7–36.3 |
| Post | 3 | 8,068 | 30 | 19.2–32.2 |
| Providence | 6 | 121,816 | 361 | 11.1–48.1 |
| Sachs | 1 | 16,344 | 93 | 15.0–57.1 |
| Weist | 6 | 46,347 | 182 | 25.0–60.2 |
| Wells | 32 | 37,967 | 297 | 17.7–60.8 |

MPI-EVA-Manchester contributes many utterances from only four children, while Wells contributes many children with fewer utterances each. This is one reason utterance count cannot be treated as the independent sample size and why child-level clustering, fixed effects, whole-child resampling, and corpus influence checks are required.

### Age bins

The first bin combines 6–23 months. Later bins use six-month intervals:

```text
006-023
024-029
030-035
036-041
042-047
048-053
054-059
060-065
```

Later bins contain fewer children and a changing corpus mix. Linear age models are therefore accompanied by age-bin, nonlinear, within/between-child, influence, and simultaneous-onset checks.

### Main cleaned and analysis-ready products

The strict-naturalistic source bundle is:

```text
data/big_cleaned_dataset/default_naturalistic_merged_006_023/
```

The authoritative all-79 child and caregiver score tables are:

```text
results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz
results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz
results/direct_surprisal_replication/mistral_full79/manifest.json
```

The child scoring source originally had 1,140,218 generated rows and received a documented 477-row Naima patch, producing the authoritative 1,140,695-row scored table. No real-child score is missing. Six generated baseline strings are blank, causing 24 flagged baseline score cells across `k0`–`k3`; these gaps affect only a tiny number of generated-candidate cells.

## Scorers and generated data products

### Mistral utterance scoring

- Model: `mistralai/Mistral-7B-v0.3`.
- Frozen model revision used in the later audited products: `caa1feb0e54d415e2df31207e5f4e273e33509b1`.
- Coverage: all 79 children, all 13 corpora, and 1,470,154 caregiver utterances.
- Conditions: real child, random, unigram, bigram, trigram, and caregiver targets; `k0`, `k1`, `k2`, and `k3` contexts.
- The extracted full-79 run contains 1,896 CSVs: 79 children × 6 target modes × 4 context conditions.
- Raw scored tree:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_naturalistic_79_children_all_available_ages_fp16
```

### TinyDialogues utterance scoring

- Model family: `LaurensWink/SmolLM2-135M_variants`.
- Revision: `149fd0d6f069ef7b0a915474c86367c7d34c1591`.
- Numeric precision: FP32.
- Coverage: the same 21 PBM discovery children, six target modes, and `k0`–`k3`.
- Audit: 504 files, 11,605,772 scored target rows, zero blank targets, zero truncated-context rows, and zero reported problems.

Because TinyDialogues reuses the PBM children, it tests scorer robustness, not independent-sample replication. Its tokenizer differs from Mistral's, so raw bits per model token and raw coefficient magnitudes must not be pooled.

### PBM same-length baselines

The PBM long analysis table contains:

- observed real child utterances;
- random word strings;
- unigram-generated strings;
- bigram-generated strings;
- trigram-generated strings;
- additive same-length LSTM strings generated with caregiver context windows `k3`, `k4`, and `k5`.

The analysis-ready table is:

```text
results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz
```

The n-gram and LSTM training dictionaries are additive by age: each age model uses the target age bin and earlier bins but not later-child language. The LSTM is a small word-level encoder-decoder trained on PBM, not a pretrained LLM. Every baseline string is forced to the observed child's word length. These baselines are therefore appropriate for fixed-effort form comparisons but not for studying effort choice.

### Word-level same-pass scorers

Word-level utterance, word, token, and allocation outputs are complete for the PBM children under three scorers:

- Mistral-7B-v0.3;
- Qwen3-14B;
- TinyDialogues.

The three analyses use the exact same 1,032,963 primary word-occurrence rows over 1,032 word types. The occurrence-set SHA-256 is:

```text
4b12305ba8ff6ec2fc96557b68aa6b921dd34bb6f0d05023fcf8451a93bcb437
```

The word analysis is owned by the sibling repository:

```text
/home/apaixonada/EvaPortelance/Projet_1/developmental_word_information
```

Its completed model outputs are under:

```text
results/modular_analysis/mistral_pbm21/
results/modular_analysis/qwen_pbm21/
results/modular_analysis/tinydialogues_pbm21/
```

The remaining-58 word-level Mistral DAG exists but has not run on Mila. Word-level findings are therefore PBM scorer robustness only.

### Legacy PBM response space

The existing completed Route 2 analysis used Mistral-generated responses for PBM only:

- approximately 444,000 matched child utterances;
- 268,712 unique caregiver contexts;
- 100 sampled responses per context;
- 976 child-session aggregates in the principal repeated-measures models;
- 176 incomplete or fallback settings retained as audit flags.

These products are under:

```text
results/route2_response_space/
results/route2_response_space_analysis/
results/route2_relative_effort_model_suite/
```

This older response space must never be relabeled as all-79.

### New all-79 Qwen-generated/Mistral-scored response space

The canonical local handoff is:

```text
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa
```

It contains:

- 645,524 unique `k3` contexts;
- exactly 100 Qwen3-14B responses per context;
- 64,552,400 total response rows;
- all 79 children and 13 corpora;
- 48,414,300 `core75` response rows;
- 16,138,100 `extension25` response rows;
- Mistral `k0` and `k3` utterance scores for each response;
- context-level means over all 100 responses;
- all generated response strings needed to compute lexical effort and exact-string entropy.

Required markers are present:

```text
CORE75_COMPLETE
EXTENSION25_COMPLETE
FULL100_AVAILABLE
```

The disjoint core75/extension25 union passed audit with exactly 100 responses for all 645,524 contexts. Local verification found 512 files in each product family. All 645,524 context means are finite and the context identifiers match the 1,122,396 eligible context-bearing real-child rows with zero per-context multiplicity mismatches.

Important columns in the per-response scored tables include:

```text
response_id
setting_id
context_id
context_text
context_word_count
datasets
child_ids
n_target_rows
selected_sample_index
target_text
selection_tier
sum_bits_k0
n_eval_tokens_k0
sum_bits_k3
n_eval_tokens_k3
mean_bits_per_token_k0
mean_bits_per_token_k3
context_support_bits
```

Important columns in `context_means/full100/` include:

```text
context_id
qwen_responses
expected_k0_utterance_surprisal_bits
expected_k3_utterance_surprisal_bits
expected_context_support_bits
```

The handoff is utterance-level only. It does not contain generated-response word rows, token-to-word allocation rows, morphology, syllables, or phonemes. Word count and simple orthographic measures can be computed from `target_text`. Exact-string entropy can also be computed locally from the 100 strings.

## Statistical design principles already established

### Primary direct-surprisal model

The registered primary utterance model is a weighted regression over exact/top-coded word-effort design cells:

```text
cell mean contextual sum bits
    ~ centered age
    + exact/top-coded word count
    + child fixed effects
```

- Design cells are weighted by their source utterance count.
- Uncertainty is clustered by child.
- The age coefficient is in scorer bits per month at fixed measured word effort.
- PBM, non-PBM, and all-79 scopes are fit separately.

Prespecified sensitivities include:

- unconditional surprisal and context gain as separate outcomes;
- age bins and quadratic age;
- Mundlak within/between-child decomposition with corpus controls;
- population-average GEE;
- random-intercept/random-age mixed models;
- whole-child and whole-corpus bootstrap;
- age permutation;
- tail trimming;
- leave-one-child and leave-one-corpus influence;
- individual child trajectories.

Warning-bearing or singular mixed fits are retained as sensitivities and do not replace the frozen weighted primary model.

### Discovery and confirmation decision rule

PBM was used for discovery. The remaining 58 children were reserved for confirmation. The primary confirmation criterion is the frozen child-clustered interval for the non-PBM contextual-surprisal age coefficient. A child-bootstrap interval is informative sensitivity evidence but cannot replace the primary decision rule after results are known.

### Cross-scorer comparison rule

Scorers are fit separately. Valid comparisons include:

- sign and interval support within each scorer;
- within-model rankings and paired contrasts;
- exactly paired row correlations;
- child-level sign agreement;
- word- or character-normalized descriptions where explicitly justified.

Raw bits and raw coefficients are not treated as calibrated across tokenizers.

## Completed result 1: utterance predictability at fixed effort

### Frozen primary estimates

| Scorer and scope | Contextual slope, k3 | Unconditional slope, k0 | Context-gain slope, k0 − k3 | Scientific status |
| --- | ---: | ---: | ---: | --- |
| Mistral, PBM21 discovery | **−0.131** [−0.179, −0.083] | **−0.162** [−0.211, −0.112] | **−0.030** [−0.050, −0.011] | contextual association supported; context-gain direction contrary |
| TinyDialogues, PBM21 robustness | **−0.222** [−0.311, −0.132] | **−0.254** [−0.339, −0.168] | **−0.032** [−0.050, −0.014] | same-sample scorer robustness; context-gain direction contrary |
| Mistral, non-PBM58 confirmation | −0.062 [−0.132, 0.007] | **−0.089** [−0.145, −0.034] | **−0.028** [−0.045, −0.010] | contextual direction consistent but not confirmed; context-gain direction contrary |
| Mistral, all 79 descriptive | **−0.080** [−0.134, −0.025] | **−0.108** [−0.156, −0.059] | **−0.029** [−0.041, −0.016] | descriptive pooled association only |

All estimates are fixed-effort age slopes in scorer bits per month with 95% child-clustered intervals.

### Main interpretation

The PBM Mistral and TinyDialogues results support a negative fixed-effort contextual-surprisal trajectory. Older children's observed forms are more predictable to both scorers at the same measured word count after stable child differences are controlled.

The non-PBM Mistral point estimate is also negative, but its frozen primary interval crosses zero. The correct phrasing is “direction-consistent but not confirmed under the registered primary criterion.” The all-79 significant estimate cannot be used to override this decision because it pools discovery and confirmation children.

### Confirmation uncertainty sensitivity

For the non-PBM contextual slope:

- primary clustered interval: `[−0.132, 0.007]`;
- whole-child bootstrap interval in the modular analysis: approximately `[−0.157, −0.011]` with 1,000 resamples;
- an earlier 200-replicate product gave `[−0.152, −0.014]`.

The bootstrap supports a negative association, but the discrepancy shows that inference is sensitive to the treatment of between-child uncertainty. It should be displayed beside the primary result, not substituted for it.

### Estimator robustness around the contextual slope

| Scope and scorer | Linear child-adjusted | Quadratic/local slope | Mundlak within-child | GEE |
| --- | ---: | ---: | ---: | ---: |
| Mistral PBM21 | −0.131 [−0.179, −0.083] | −0.155 [−0.228, −0.082] | −0.133 [−0.182, −0.084] | −0.152 [−0.200, −0.104] |
| TinyDialogues PBM21 | −0.222 [−0.311, −0.132] | −0.272 [−0.391, −0.153] | −0.221 [−0.313, −0.130] | −0.226 [−0.311, −0.141] |
| Mistral non-PBM58 | −0.062 [−0.132, 0.007] | −0.089 [−0.160, −0.018] | −0.062 [−0.131, 0.007] | −0.104, interval unavailable in the saved summary |

The PBM direction is stable across the major repeated-measures estimators. The non-PBM inference remains specification-sensitive, so the frozen linear child-clustered interval remains the decision rule.

### Paired Mistral–TinyDialogues evidence

The exact paired PBM intersection contains 446,508 rows overall and 443,848 context-bearing rows. There are 477 explained source-version coverage differences and zero unexplained join mismatches.

For contextual surprisal:

- TinyDialogues slope on the paired intersection: `−0.222`;
- Mistral slope on the paired intersection: `−0.133`;
- paired difference, Tiny minus Mistral: `−0.089`;
- paired child-bootstrap interval for the difference: `[−0.152, −0.028]`.

Supported child-level P1 slope signs agree across scorers for 18 of 21 children. The direction is robust; the magnitude is scorer-calibration dependent.

Raw score agreement is high for utterance surprisal and much lower for context gain:

| Outcome | Pearson correlation across paired rows |
| --- | ---: |
| Real k0 sum bits | 0.857 |
| Real k3 sum bits | 0.801 |
| Real k3 context gain | 0.179 |
| Random-minus-real k3 gap | 0.906 |
| Unigram-minus-real k3 gap | 0.741 |
| Bigram-minus-real k3 gap | 0.676 |
| Trigram-minus-real k3 gap | 0.636 |

### Unconditional form predictability versus context support

Unconditional surprisal declines in PBM under both scorers and also declines in the non-PBM Mistral sample. In every registered scope, the unconditional decline is larger in magnitude than the contextual decline. Therefore `k0 − k3` context gain declines with age.

This supports the narrower interpretation that older children's forms become more probable or conventional under the scorer. It contradicts the preregistered positive developmental prediction for context gain. A repeated opposite sign is not confirmation of the original hypothesis.

### Individual and corpus variation

All 21 TinyDialogues child profiles and all 79 Mistral profiles were inspected. The analysis includes child-specific slopes, child and corpus leave-out estimates, corpus bootstrap, and trajectory galleries.

The population direction is not universal. Some children show slope reversals, and corpus composition changes across age. The paper should describe a population-level association with heterogeneity, not a developmental law followed by every child.

### Secondary caregiver-input trajectories

Caregiver utterances were scored and modeled with the same fixed-effort structure as a secondary input-adaptation analysis. The clearest all-79 descriptive caregiver results are:

| Outcome | Age slope | 95% CI | Reading |
| --- | ---: | ---: | --- |
| Caregiver contextual k3 surprisal | 0.018 | [−0.013, 0.049] | no clear all-79 contextual trajectory |
| Caregiver unconditional k0 surprisal | −0.048 | [−0.079, −0.017] | caregiver form predictability declines modestly with child age |
| Caregiver context gain | −0.066 | [−0.081, −0.050] | context gain declines |

In PBM, caregiver contextual and unconditional intervals cross zero, while caregiver context gain is negative. In the non-PBM sample, unconditional surprisal and context gain are negative, while contextual surprisal is near zero. These are secondary input-adaptation descriptions, not evidence about child communicative efficiency.

## Completed result 2: generated same-length baseline comparisons

The same-length baselines ask whether observed child strings become more or less distinguishable from age-appropriate generated strings at the same word count.

For Mistral, the age slopes of the generated-minus-real k3 gap are:

| Scope | Random | Unigram | Bigram | Trigram |
| --- | ---: | ---: | ---: | ---: |
| PBM21 | 0.404 [0.300, 0.508] | 0.076 [0.021, 0.131] | 0.069 [0.025, 0.114] | 0.082 [0.051, 0.113] |
| Non-PBM58 | 0.221 [0.082, 0.360] | 0.034 [−0.021, 0.089] | 0.026 [−0.025, 0.076] | 0.026 [−0.020, 0.072] |
| All 79 descriptive | 0.270 [0.150, 0.391] | 0.043 [0.001, 0.085] | 0.037 [−0.001, 0.074] | 0.040 [0.005, 0.075] |

Positive slopes mean the generated-minus-real surprisal gap increases with age. The PBM direction is positive for every baseline. Under both Mistral and TinyDialogues, the candidate ordering from closest to farthest remains trigram, bigram, unigram, random across age bins.

These are comparisons of string plausibility under the scorers. The candidate strings do not preserve intended meaning. They cannot justify claims about optimal choices, Pareto frontiers, or a child selecting the best utterance among equivalent alternatives.

The PBM additive LSTM `k3`, `k4`, and `k5` same-length generations and Mistral
scoring are complete. They provide stronger controlled neural baselines, but
they remain meaning-uncontrolled. The selected full-79 extension uses additive
age-bin training, caregiver context `k3`, and same-length generation only. Its
generation and Mistral utterance `k0`/`k3` scoring are complete and audited for
1,140,218 rows and 79 children. Its score-table SHA-256 is
`03af2bc6abbca362eb9c7529b921e84048d65f68f6c950b841384e187271345e`.
Analysis-repository import is still pending.

## Completed result 3: word-level information across three scorers

### Primary same-word model

The core occurrence-level formula is:

```text
word surprisal
    ~ age
    + word position
    + utterance length
    + singleton indicator
    + child identity
    + word identity
```

This compares the same lexical item within the developmental data while absorbing stable child and word differences. Whole-child bootstrap intervals use 1,000 replicates.

### Main word-level effects

| Question | Scorer | Estimate | Clustered 95% CI | Bootstrap 95% CI | Status |
| --- | --- | ---: | ---: | ---: | --- |
| Same-word unconditional age slope | Mistral | −0.049 | [−0.055, −0.043] | [−0.057, −0.042] | supported |
|  | Qwen3-14B | −0.024 | [−0.036, −0.012] | [−0.034, −0.008] | supported |
|  | TinyDialogues | −0.050 | [−0.059, −0.042] | [−0.063, −0.042] | supported |
| Same-word contextual age slope | Mistral | −0.019 | [−0.032, −0.007] | [−0.030, −0.005] | supported |
|  | Qwen3-14B | −0.027 | [−0.040, −0.014] | [−0.039, −0.012] | supported |
|  | TinyDialogues | −0.050 | [−0.058, −0.041] | [−0.064, −0.042] | supported |
| Word context-gain age slope | Mistral | −0.030 | [−0.038, −0.021] | [−0.040, −0.023] | supported negative under Mistral |
|  | Qwen3-14B | 0.002 | [−0.006, 0.011] | [−0.007, 0.013] | no clear effect |
|  | TinyDialogues | −0.001 | [−0.003, 0.001] | [−0.002, 0.002] | no clear effect |
| Longer-word context support at centered age | Mistral | 0.312 | [0.285, 0.340] | [0.282, 0.341] | supported |
|  | Qwen3-14B | 0.642 | [0.578, 0.706] | [0.534, 0.700] | supported |
|  | TinyDialogues | 0.062 | [0.050, 0.075] | [0.050, 0.076] | supported |

The raw coefficient magnitudes are scorer-native and must not be compared as though the tokenizers share a calibrated bit scale.

### Additional registered word questions

| Question | Mistral | Qwen3-14B | TinyDialogues | Cross-scorer conclusion |
| --- | ---: | ---: | ---: | --- |
| Age change in longer-word context support | −0.008, interval excludes 0 | −0.016, interval excludes 0 | −0.001, interval includes 0 | common negative direction; 2/3 supported |
| Age change in frequency-related context support | 0.005, interval excludes 0 | 0.008, interval excludes 0 | −0.001, interval includes 0 | scorer-dependent; coding uses centered leave-corpus-out log frequency |
| Within-word age × character length effect on context gain | −0.010, interval excludes 0 | −0.008, interval excludes 0 | −0.001, clustered interval includes 0 but bootstrap excludes 0 | common negative direction; uncertainty differs |
| Age change in within-utterance k3 information-position gradient | 0.015, interval includes 0 | 0.015, interval includes 0 | 0.014, interval excludes 0 | common positive direction but weak interval support |

The strongest word-level conclusions are:

1. unconditional surprisal for the same word decreases with age under all three scorers;
2. contextual surprisal for the same word decreases with age under all three scorers;
3. longer word types receive more context support at the centered age under all three scorers.

Overall developmental context gain and the rarity-related interaction are not robust across scorers. The result does not yet have an independent 58-child word-level confirmation.

## Completed result 4: corrected cross-fitted Bayes-derived candidate analysis

### What this analysis is

The corrected Bayes analysis decomposes a candidate score into:

- an age-appropriate utterance prior;
- a whole-utterance contrastive context-evidence term;
- a probability normalized only over the five candidates supplied for that row: real, random, unigram, bigram, and trigram.

Training is leave-corpus-out for Brown, Manchester, and Providence, additive by age, and includes explicit unknown-token handling. The context evidence is validated with held-out matched-versus-shuffled context pairs.

This candidate-set probability is not a posterior over every possible utterance.

### Audit and validation

- Total candidate rows: 2,232,524.
- Every candidate group sums to one within floating-point tolerance.
- Brown held-out matched-context accuracy: 62.2%; matched-minus-shuffled evidence: 0.281 bits.
- Manchester: 58.8%; 0.271 bits.
- Providence: 58.4%; 0.327 bits.
- All three predeclared validation gates pass.

### Candidate results

| Candidate | Rows | Mean candidate-set probability | Rank-1 rate | Mean prior bits/word | Mean context evidence bits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Real child | 446,508 | 40.0% | 43.7% | 11.521 | −0.008 |
| Random | 446,492 | 0.3% | 0.3% | 21.706 | −0.679 |
| Unigram | 446,508 | 11.1% | 11.2% | 13.967 | −0.519 |
| Bigram | 446,508 | 20.6% | 21.5% | 12.967 | −0.345 |
| Trigram | 446,508 | 28.0% | 30.8% | 12.268 | −0.206 |

The real child utterance is in the top two on 68.6% of rows. Five-way rank-1 chance is 20%. The prior alone ranks the real utterance first on 42.9%; context evidence raises this only to 43.7%. The real advantage is therefore primarily prior-driven, with a smaller independently validated context increment.

### Paired evidence in favor of the real utterance

| Baseline | Mean prior log Bayes factor | Mean context-evidence log Bayes factor | Mean combined log Bayes factor | Combined real-win rate |
| --- | ---: | ---: | ---: | ---: |
| Random | 21.023 | 0.671 | 21.694 | 96.0% |
| Unigram | 7.038 | 0.511 | 7.549 | 73.0% |
| Bigram | 3.840 | 0.337 | 4.177 | 62.5% |
| Trigram | 1.647 | 0.198 | 1.845 | 51.5% |

For trigram, the child-level interval for the proportion of rows won crosses 50%, although the child-mean log Bayes factor remains positive. The defensible claim is positive average evidence relative to the trigram, not a universal majority-win effect across children.

### Correct use in the paper

This analysis is a decomposition and robustness section. It shows that the observed child strings look more developmentally probable than the supplied baselines and that held-out context compatibility adds a smaller increment. It should not replace direct Mistral surprisal and should not be called normalized unrestricted Bayes surprisal.

The earlier Bayes pilot under `results/mila_modular_runs_2026_07_08/products/` is superseded for substantive claims because it used overlapping training data, omitted `p(c)`, and had a limited reverse-trigram context mechanism. It may remain methods history only.

## Completed result 5: legacy PBM effort relative to a response space

### Question

Relative to 100 generated responses for the same caregiver context, does observed child word effort change with age and exact-string response entropy?

The principal outcome is:

```text
child words − generated mean words
```

A percentile of child word count within the generated distribution is also analyzed.

### Main repeated-measures model

```text
relative effort
    ~ age * exact-string response entropy
    + generated expected words
    + caregiver-context word count
    + next-token context entropy
    + child identity or repeated-child structure
```

### Main estimates

| Outcome and term | Estimate | 95% CI | Status |
| --- | ---: | ---: | --- |
| Child words minus generated mean: age | 0.0895 words/month | [0.0777, 0.1013] | qualified positive association |
| Child words minus generated mean: age × response entropy | −0.0248 words/month/entropy bit | [−0.0384, −0.0112] | contrary to positive prediction |
| Child percentile in generated distribution: age | 0.0108/month | [0.0090, 0.0125] | qualified positive association |
| Child percentile: age × response entropy | −0.0034/month/entropy bit | [−0.0047, −0.0022] | contrary to positive prediction |

The headline estimates come from a session-level exchangeable GEE over 976 child-session aggregates.

### Estimator sensitivity

| Estimator | Relative-effort age term | Age × response-entropy term |
| --- | ---: | ---: |
| Utterance-level child-fixed OLS | 0.093 [0.080, 0.106] | 0.0002 [−0.0013, 0.0017] |
| Session GEE | 0.089 [0.078, 0.101] | −0.025 [−0.038, −0.011] |
| Session Mundlak GEE | 0.089 [0.078, 0.100] | −0.023 [−0.047, 0.001] |
| Random-intercept/random-age mixed model | 0.102 [0.090, 0.114] | −0.024 [−0.033, −0.016] |

Relative effort increases with age across estimators. The negative interaction is supported by the session GEE and mixed model, is borderline in the Mundlak model, and is absent at the utterance-row level. Aggregation and estimator sensitivity are part of the result.

This response space is model-, prompt-, temperature-, seed-, and surface-form-dependent. Because the same broad model family generated the responses and supplied related measurements, generator/scorer coupling is also a limitation.

## Completed result 6: sustained developmental onset

The frozen onset rule uses 1,000 whole-child bootstrap replicates and a simultaneous max-absolute-studentized band across all post-reference age-bin contrasts.

An onset is declared only if:

1. a bin has an upper simultaneous bound below zero;
2. it has adequate support;
3. every later adequately supported bin also remains below zero.

For confirmation, adequate support requires at least five children and three corpora.

Results:

- PBM discovery sustained onset: **not established**.
- Non-PBM confirmation sustained onset: **not established**.

In PBM, the 24–29-month simultaneous interval is `[−1.806, 0.012]`, narrowly crossing zero. The 30–35 interval is below zero, but 36–41 crosses zero and later PBM bins have insufficient corpus support. In the non-PBM sample, 36–41 is below zero, but later adequately supported bins cross zero.

Therefore, the earlier exploratory statement that a nominal decrease is visible by 24–29 months must not be presented as a replicated onset. The working onset report and its change-point scan are superseded by this simultaneous sustained-onset result for paper claims.

## Completed result 7: PBM complexity descriptions

Audited PBM complexity products show expected developmental growth in production effort. These are useful descriptive controls but not yet validated as primary full-79 measures.

| Age bin | Mean words/utterance | Mean syllables/utterance | Mean age-bin vocabulary size |
| --- | ---: | ---: | ---: |
| 006–023 | 1.727 | 2.165 | 651.7 |
| 024–029 | 2.349 | 2.858 | 1,173.5 |
| 030–035 | 2.840 | 3.399 | 1,372.6 |
| 036–041 | 3.193 | 3.817 | 1,170.5 |
| 042–047 | 3.875 | 4.662 | 1,192.0 |
| 048–053 | 3.703 | 4.403 | 1,270.3 |
| 054–059 | 4.156 | 4.937 | 1,661.5 |
| 060–065 | 4.068 | 4.830 | 710.5 |

The changing number of children and recording volume makes raw vocabulary size difficult to interpret at late ages. Morphology, syllable, phoneme, lexical diversity, and dependency measures need corpus/child/session validation before they are promoted to primary all-79 controls or used to rerun the onset rule.

## Separate descriptive analysis: Hall historical snapshot

Hall is not part of the longitudinal sample. It is a historical cross-sectional sociolinguistic snapshot near age four and must not be treated as an 80th child or a 14th longitudinal corpus.

### Sample and audit

- Primary Hall sample: 36 children and 70,510 utterances.
- Sensitivity sample: 37 children and 71,830 utterances.
- Scored archive: 287,320 utterance rows across `k0`–`k3`.
- Registered models: 20/20 passed.
- Bootstrap: 1,000 stratified child resamples for five primary families.
- Contrasts: 72 registered.
- Figures: 9/9 passed audit.

### Main descriptive estimates

| Hall contrast | Estimate | 95% CI | Interpretation |
| --- | ---: | ---: | --- |
| Within-Hall k0 race-by-class interaction at fixed word count and setting | −3.516 bits | [−5.730, −1.302] | historical scorer-indexed interaction only |
| Adult-adjacent k3 race-by-class interaction | −3.249 bits | [−5.710, −0.788] | contextual target-predictability interaction |
| Adult-adjacent context-support interaction | −0.213 bits | [−1.105, 0.679] | no clear interaction; interval crosses zero |
| Hall minus locked current-corpus k0 contrast | 3.037 bits | [2.041, 4.032] | domain/era/dialect/transcription/model sensitivity |

Historical race and class codes are corpus strata. Differences may reflect dialect, recording era, geography, transcription, setting, and language-model representation. They are not causal SES effects, linguistic deficits, inherent group differences, or estimates of communicative efficiency.

Hall is best treated as a separate analysis, appendix, or separate paper. It should not be used to strengthen the longitudinal developmental claim.

## Inventory of completed model families

Before the new all-79 Qwen cloud analysis, the saved synthesis counted 607 fitted variants or registered outcome fits:

| Family | Fits or variants | Status |
| --- | ---: | --- |
| Direct TinyDialogues PBM | 34 | pass with recorded sensitivities |
| Direct Mistral full-79 | 102 | pass with recorded sensitivities |
| Paired TinyDialogues–Mistral | 11 | pass |
| Route 1 model zoo | 56 | pass; 15 next-token entropy variants unavailable rather than failed |
| Route 1 explicit comparisons | 45 | pass |
| Legacy Route 2 response space | 48 | pass |
| Legacy Route 2 relative effort | 144 | pass |
| PBM word Mistral | 55 | pass |
| PBM word Qwen3-14B | 55 | pass |
| PBM word TinyDialogues | 55 | pass |
| Frozen sustained-onset tests | 2 | pass, both `not_established` |

The corrected Bayes decomposition and Hall models are additional completed analyses outside that 607-fit count.

This large model inventory should not become a paper organized around hundreds of models. The final paper needs a small declared primary model, a compact sensitivity ladder, and transparent appendices.

## Historical design implemented by the all-79 Qwen analysis

The following design section records the requirements that guided the now
completed analysis. The authoritative fitted products are
`results/full79_joint_efficiency_analysis/` and
`results/full79_information_effort_clouds/`; the report is
`docs/full79_joint_efficiency_explorer.html`. No additional Qwen generation or
Mistral scoring is needed to reproduce those results.

### Required feature stage

For each of the 645,524 contexts, compute from all 100 `target_text` values:

- exact-string entropy;
- number of unique strings;
- duplicate rate;
- lexical word count per response;
- character count per response;
- mean, median, standard deviation, quantiles, and empirical distribution of response word count;
- optional robust summaries such as median absolute deviation;
- optional sample-size rarefaction sensitivity using prefixes or deterministic subsamples of 25, 50, 75, and 100 responses.

The scored tables already supply per-response:

- unconditional sum bits;
- contextual sum bits;
- context support;
- scorer token count;
- mean bits per token.

For the main utterance-level comparison, total sum bits should remain primary and measured effort should be modeled explicitly. Bits per token can be a sensitivity but should not silently replace the fixed-effort estimand.

### Required join stage

Join the context summaries and per-response cloud to the authoritative 1,122,396 context-bearing real-child rows in:

```text
results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz
```

Preserve:

- `utterance_id` and source row identity;
- context ID;
- dataset and child key;
- session and age;
- discovery/confirmation membership;
- real target text and word count;
- real Mistral k0 and k3 sum bits;
- real context gain;
- all Qwen context-level summaries;
- exact multiplicity when one context is linked to multiple real utterance rows.

The join audit must verify:

- 1,122,396 eligible real-child rows;
- 79 children;
- 13 corpora;
- 645,524 unique contexts;
- no missing Qwen context summaries;
- exactly 100 generated responses per context;
- PBM and non-PBM scopes are disjoint and their union equals all 79;
- no row duplication beyond the known many-real-rows-per-context structure.

### Analysis A: raw effort development

Model child word effort as an outcome without conditioning on the generated expected length in the first model:

```text
child words ~ age + child identity
```

Then add clearly named conversational predictors, such as caregiver-context word count and exact-string response entropy, in separate specifications. Raw effort and generated-relative effort answer different questions and should not be mixed into one interpretation.

Alternative effort outcomes should be included only if they can be calculated reliably from the available text. Simple orthographic words and characters are immediately feasible. Full morphology, syllables, and phonemes require validation before promotion.

### Analysis B: effort relative to Qwen responses

Context-specific outcomes can include:

```text
child words − generated mean words
child words − generated median words
child word-count percentile in the 100-response distribution
indicator(child shorter than generated median)
indicator(child longer than generated 90th percentile)
```

Fit the same three scopes separately:

1. PBM21 discovery or historical comparability;
2. non-PBM58 confirmation;
3. all-79 description.

The new Qwen analysis is not a preregistered confirmation of the old Mistral response-space interaction unless the estimand and decision rule are frozen before inspecting the new coefficients. The best practice is to declare which old result is being tested and which new analyses are exploratory before fitting.

### Analysis C: joint information-effort cloud position

For each observed child utterance and its context-specific set of 100 Qwen responses, compute transparent position measures separately for `k0` and `k3`:

- child word-count percentile among responses;
- child sum-bits percentile among responses;
- child context-gain percentile among responses;
- standardized difference from the generated mean for effort and sum bits;
- robust standardized difference from the generated median using MAD or empirical quantiles;
- joint quadrant relative to the generated medians;
- bivariate distance from the generated cloud center, with covariance regularization documented;
- empirical depth or nearest-neighbor measures only as secondary analyses, because their scale and interpretation are less transparent.

A useful descriptive pair is:

```text
z_effort = (child words − generated mean words) / generated SD(words)
z_information = (child k3 sum bits − generated mean k3 sum bits) / generated SD(k3 bits)
```

Handle contexts with zero generated variance explicitly rather than dividing by zero. Empirical percentiles are often more stable than z scores for only 100 samples and should probably be the main cloud coordinates.

Model cloud position with age, child structure, and scope-specific uncertainty. Do not orient the axes as “better” and “worse” without a separately justified utility function. Lower surprisal is greater predictability, not automatically more useful; shorter speech is less measured effort, not automatically more efficient.

### Analysis D: response uncertainty moderation

Test whether exact-string response entropy moderates:

- raw child effort;
- effort relative to Qwen responses;
- real-versus-generated contextual surprisal position;
- real-versus-generated context-support position.

The age-by-entropy interaction should be presented with predicted lines at declared entropy quantiles, not interpreted from a coefficient alone. Because the old PBM interaction was negative, a genuine replication test should freeze whether the expected direction is negative, positive, or simply two-sided before opening the new result.

### Analysis E: discovery, confirmation, and descriptive scopes

For every promoted new effect, retain a table with:

| Scope | Role |
| --- | --- |
| PBM21 | discovery and comparability with earlier response-space results |
| Non-PBM58 | independent sample evaluation |
| All 79 | pooled descriptive precision, never a replacement for confirmation |

If a model is developed after looking at PBM, it can still be frozen before inspecting non-PBM. If the non-PBM result has already been inspected during model development, it must be labeled exploratory rather than confirmatory.

### Analysis F: sensitivity and audit requirements

At minimum, retain:

- child-clustered uncertainty;
- whole-child bootstrap;
- within/between-child decomposition;
- corpus controls or corpus influence checks;
- child-session aggregation sensitivity;
- nonlinear age and age-bin descriptions;
- sample-size rarefaction for exact-string entropy;
- duplicate-string and distinct-string summaries;
- leave-one-corpus influence;
- zero-variance and extreme-tail audits;
- exact product and code hashes;
- plots of individual or corpus heterogeneity.

Do not choose the estimator or outcome that produces the most favorable result. Freeze one primary outcome and one primary repeated-measures estimator, then report the rest as a sensitivity ladder.

### Final code status for this analysis

The early controller below was committed as a data/audit runner:

```text
src/build_full79_qwen_route2_analysis.py
```

It is not the final model owner. The final staged controller is
`src/build_full79_joint_efficiency_analysis.py`, with the dedicated nonlinear
model engine `src/fit_full79_joint_efficiency_models.R`. The final audit marker
is
`results/full79_joint_efficiency_analysis/FULL79_JOINT_EFFICIENCY_COMPLETE_AND_AUDITED`.
Report results from those frozen products rather than from the early runner.

## Results that are superseded or must remain exploratory

### Superseded onset claim

Older working reports said the fixed-word-count decrease “starts” in the 24–29-month bin. The final simultaneous sustained-onset analysis does not establish onset. The nominal 24–29 result may be mentioned only as exploratory history, not as the paper's onset result.

### Superseded original Bayes pilot

The original unnormalized Bayes decomposition omitted `p(c)`, used in-sample PBM training, and had a weak reverse-trigram dependency. Use the corrected leave-corpus-out candidate-set analysis for substantive reporting.

### Superseded response-space availability statement

Older reports said the Qwen-generated/Mistral-scored response product or its
analysis was pending. Both the full100 handoff and the primary all-79
conditional effort/cloud analysis are now local and audited. Semantic-cluster
entropy remains a future construct-validation extension.

### Exploratory change-point scans

Historical AIC scans favored a breakpoint near 44.5 months under one PBM model family. This does not establish a biological phase transition and should not compete with the frozen sustained-onset result.

### Exploratory complexity controls

PBM morphology, syllable, phoneme, vocabulary, and TTR results are useful diagnostics. They are not yet a validated all-79 primary adjustment set.

## What can safely be claimed now

### Strongest defensible claim

> In the PBM longitudinal discovery sample, older children's observed utterance forms receive lower contextual surprisal from two neural language models at the same exact/top-coded lexical word effort after stable child differences are controlled. This is evidence of increasing scorer-based predictability or conventionality of form. The independent 58-child Mistral estimate is direction-consistent but does not meet the frozen primary confirmation criterion because its child-clustered interval includes zero.

### Supported secondary claims

- Unconditional utterance surprisal declines with age in PBM under both scorers and in the non-PBM Mistral sample.
- Utterance context gain declines with age in all registered direct-score scopes, contrary to the frozen positive prediction.
- Same-word unconditional and contextual surprisal decline with age under Mistral, Qwen3-14B, and TinyDialogues on the exact PBM occurrence set.
- Longer word types receive more context support at the centered age under all three word scorers.
- Within the corrected five-way candidate set, the observed utterance has mean candidate-set probability 0.400 and ranks first on 43.7% of rows; the advantage is mainly prior-driven with a smaller validated context increment.
- In the legacy PBM response space, observed effort rises relative to generated expected effort with age, while the principal age-by-exact-string-entropy interaction is negative.
- Sustained onset is not established.

### Claims that are not licensed

Do not claim that:

- older children communicate more Shannon information because surprisal decreases;
- lower surprisal alone is greater communicative efficiency;
- children optimize a single objective;
- observed utterances are Pareto-optimal;
- generated alternatives preserve the child's intended meaning;
- exact-string response entropy is semantic uncertainty;
- scorer agreement is independent-sample replication when the same children are reused;
- the all-79 pooled estimate rescues the failed primary confirmation criterion;
- a significant child-bootstrap sensitivity replaces the frozen clustered interval;
- context use increases with age when context gain actually declines;
- a specific onset month has been replicated;
- Hall group differences are causal SES, race, dialect-quality, or deficit effects;
- raw bits from different tokenizers are directly comparable.

## Recommended paper architecture

### Recommended central paper

The most coherent single paper is about developmental predictability of form at fixed production effort, not a fully demonstrated universal efficiency optimum.

A possible title is:

> Developmental Change in the Predictability of Child Utterance Forms at Fixed Production Effort

The working communicative-efficiency framing can remain in the introduction as a motivating theory, but the title and abstract should match the measured construct.

### Suggested research questions

1. Does contextual surprisal of observed child utterances change with age at fixed lexical effort and within child?
2. Is the trajectory better explained by unconditional form predictability or increasing support from preceding context?
3. Is the direction robust to scorer choice and independent-sample evaluation?
4. At the word level, do the same lexical items become more predictable with age, and which word properties receive contextual support?
5. As a complementary analysis, where do observed child utterances fall relative to a free-length generated response distribution in effort and information?

The fifth question should enter the main paper only after the all-79 Qwen cloud analysis is complete and the estimand is frozen. Otherwise, retain the older Route 2 result as exploratory or move effort adaptation to a separate paper.

### Suggested paper sections

1. **Introduction**
   - communicative-efficiency motivation;
   - distinction between predictability, effort, contextual support, and listener utility;
   - developmental conventionalization hypothesis;
   - explicit predictions and non-predictions.
2. **Data**
   - CHILDES corpus selection;
   - 21-child discovery and 58-child confirmation split;
   - age and session coverage;
   - cleaning and role construction.
3. **Measurements**
   - Mistral and TinyDialogues utterance surprisal;
   - `k0`, `k3`, and context gain;
   - word count effort;
   - generated baselines;
   - word-level same-pass scores;
   - Qwen response-space measures if completed.
4. **Statistical analysis**
   - exact/top-coded word-effort design cells;
   - child fixed effects and clustered uncertainty;
   - discovery/confirmation logic;
   - sensitivity ladder and multiplicity policy.
5. **Results: utterance predictability**
   - PBM discovery;
   - TinyDialogues scorer robustness;
   - non-PBM confirmation;
   - all-79 description;
   - heterogeneity.
6. **Results: unconditional/contextual decomposition**
   - explain the negative context-gain finding directly.
7. **Results: word-level evidence**
   - same-word k0 and k3;
   - longer-word support;
   - scorer-dependent context-gain and rarity findings.
8. **Complementary generated-reference analyses**
   - corrected candidate-set Bayes;
   - all-79 Qwen effort/cloud results if completed.
9. **Discussion**
   - conventionalization at fixed effort;
   - failed primary confirmation criterion;
   - context-gain result contrary to prediction;
   - limits of scorer-based probability;
   - need for listener-utility outcomes.

### Results that probably belong in appendices or separate papers

- the full 607-model inventory;
- extensive mixed-model and nonlinear atlases;
- all individual child galleries;
- the complete generated-baseline ladder;
- the legacy original Bayes pilot;
- exploratory change-point scans;
- Hall historical race/class analysis;
- detailed complexity feature validation;
- full response-entropy calibration grids.

### Candidate main figures

1. Data coverage by age for PBM and non-PBM.
2. Primary fixed-effort contextual-surprisal slopes for PBM Mistral, PBM TinyDialogues, and non-PBM Mistral, with primary and bootstrap uncertainty visibly separated.
3. Unconditional, contextual, and context-gain age slopes in separate panels.
4. Child-level slope distribution or paired scorer slope agreement.
5. Word-level cross-scorer effect matrix for same-word k0, same-word k3, context gain, and longer-word support.
6. If completed, an all-79 Qwen joint information-effort cloud figure with scope-separated developmental summaries.

### Candidate main tables

1. Corpora, children, utterances, sessions, and age ranges.
2. Primary direct-surprisal estimates and registered evidence status.
3. Sensitivity estimator ladder.
4. Word-level cross-scorer primary effects.
5. If completed, Qwen effort/cloud primary effects by PBM, non-PBM, and all-79 scopes.

## Decisions still needed before the paper is frozen

### Decision 1: What is the paper's primary claim?

Recommended: developmental increase in scorer-based predictability or conventionality of utterance form at fixed lexical effort. Avoid making “communicative efficiency” the measured dependent variable unless the term is carefully operationalized.

### Decision 2: Is the non-PBM result called a replication?

Recommended: no. Call it direction-consistent but not confirmed under the frozen primary interval. Report the negative bootstrap sensitivity transparently.

### Decision 3: Is context gain a primary or decomposition outcome?

Recommended: include it prominently because it changes the theoretical story. It is contrary to the predicted positive direction and shows that the unconditional form-development component is stronger.

### Decision 4: Does the word-level analysis enter the same paper?

Recommended: yes, as a mechanistic or scale-bridging secondary analysis. Keep its PBM-only status explicit and avoid pooling scorer magnitudes.

### Decision 5: Does Route 2 enter the main paper?

Recommended: wait for the all-79 Qwen/Mistral analysis. The older PBM Mistral-generated result is scientifically interesting but measurement-limited and estimator-sensitive. The new decoupled generator/scorer handoff is much better suited to a final analysis.

### Decision 6: Which all-79 Qwen outcome is primary?

This must be frozen before fitting. A reasonable choice is child word-count percentile within the 100-response Qwen distribution, with a session-level repeated-measures estimator and whole-child bootstrap. For joint clouds, use empirical effort and k3-sum-bits percentiles as the most transparent bivariate coordinates.

### Decision 7: How much complexity adjustment is required?

Recommended: lexical word count is primary. Treat morphemes, syllables, phonemes, and other complexity variables as validation-dependent sensitivities until their full-79 measurement audit is complete.

### Decision 8: Is Hall part of this paper?

Recommended: no, except perhaps as a brief domain-sensitivity limitation. It is substantively and ethically distinct and deserves separate treatment.

### Decision 9: Is a listener-utility analysis required before submission?

It is required for a strong claim about communicative success or efficiency, but not for a carefully titled paper about model-based predictability and effort. The paper can explicitly identify listener utility as the next decisive test.

## Genuine remaining gaps

1. The remaining-58 word-level Mistral production has not run; the current
   word evidence is PBM-only.
2. Full-79 morphology, syllable, phoneme, and broader complexity products are
   not all complete and validated.
3. No validated listener-relevant outcome exists.
4. The structurally defined caregiver-responsive sample still needs
   adjudication of 18,172 `context_k1` mismatches and a 325-row manual
   validation sample.
5. Semantic-cluster response entropy is unavailable; current response entropy
   is exact-string and generator/prompt/temperature-specific.
6. The completed full-79 LSTM score handoff still needs exact local ingestion
   into the fixed-effort cloud analysis and a rebuilt all-source audit.
7. The PBM-held-out BabyLlama-sized LLaMA and T5 pipelines are implemented but
   have not yet run on Mila. The frozen design is two architectures by eight
   cumulative age cutoffs, or 16 final models.
8. Full-79 corrected Bayes and next-token context-entropy coverage are
   incomplete.
9. Demographic variables are too sparse or corpus-dependent for general
   developmental covariate claims. Hall is the only completed targeted
   sociolinguistic snapshot and must remain separate.

## Authoritative local artifact map

### Best high-level reading

```text
docs/august_supervisor_report.md
docs/august_supervisor_report.html
docs/august_supervisor_index.html
docs/current_scientific_synthesis.md
docs/predicting_utterance_level_information_report.md
docs/direct_surprisal_results_explorer.html
```

The August package is independently audited at commit `f94733ad14556ce6edb71a957b87c881f1edfaa5` with zero blocking findings.

### Data description

```text
docs/supervisor_data_description.md
results/supervisor_report/data_description/analysis_sample_summary.csv
results/supervisor_report/data_description/corpus_summary.csv
results/supervisor_report/data_description/manifest.json
```

### Direct utterance surprisal

```text
results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz
results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz
results/direct_surprisal_replication/mistral_full79/manifest.json
results/direct_surprisal_replication/mistral_full79/modular/
results/direct_surprisal_replication/tinydialogues_pbm/
results/direct_surprisal_replication/paired_tiny_mistral_pbm/
docs/mistral_full79_direct_surprisal_replication.md
docs/tinydialogues_pbm_direct_surprisal_replication.md
docs/paired_tinydialogues_mistral_pbm_report.md
docs/direct_surprisal_onset_confirmation.md
```

### Word level

```text
results/word_cross_scorer_comparison/
docs/word_cross_scorer_comparison.md
/home/apaixonada/EvaPortelance/Projet_1/developmental_word_information/results/modular_analysis/
```

### Generated baselines and corrected Bayes

```text
results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz
results/corrected_pbm_bayes_v2/
results/corrected_pbm_bayes_report/
docs/corrected_pbm_bayes_report.md
docs/lstm-additive-pbm-supervisor-summary.md
```

### Legacy PBM response space

```text
results/route2_response_space/
results/route2_response_space_analysis/
results/route2_relative_effort_model_suite/
docs/august_routes_route2.md
```

### New all-79 Qwen/Mistral response space

```text
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/prepared/inputs/core75/
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/prepared/inputs/extension25/
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/processed/core75/
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/processed/extension25/
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/context_means/full100/
results/external/compute_surprisal_mila/qwen_response_mistral_full100_20260817_f5dd5aa/reports/full100/full100_audit.json
src/build_full79_qwen_route2_analysis.py
```

### Complexity and older working analyses

```text
results/mila_modular_runs_2026_07_08/products/
docs/new_efforts_complexity_metrics.md
docs/developmental_onset_working_report.md
docs/bayes_information_working_report.md
```

Treat the latter two working reports as historical/exploratory where they conflict with the final sustained-onset and corrected-Bayes products.

### Hall

```text
results/hall_snapshot_analysis/
results/hall_snapshot_analysis/final/ANALYSIS_COMPLETE_AND_AUDITED
docs/hall_snapshot_mistral_analysis.md
```

## Compact prompt for the next model

The following can be appended after this document when asking another model for help:

> Act as a senior developmental psycholinguist, information-theory researcher, and statistical reviewer. Using the evidence dossier above, help me freeze a coherent paper and the genuinely final analyses. Do not invent results, do not pool tokenizer-specific magnitudes, do not call the non-PBM contextual result confirmed, and do not equate lower surprisal with listener utility. First propose the narrow central contribution and paper structure. Then specify a preregistration-style primary plan for the not-yet-fit all-79 Qwen/Mistral effort and joint information-effort cloud analysis, preserving PBM21 discovery, non-PBM58 confirmation, and all-79 descriptive scopes. Identify which existing results belong in the main text, supplement, or a separate paper. State every estimand, unit of analysis, clustering level, decision rule, and interpretation limit.

## Final integrity checklist

Before a paper draft or new result is considered final, verify all of the following:

- [ ] The primary claim says predictability or conventionality at fixed measured effort, not greater information communicated.
- [ ] Unconditional surprisal, contextual surprisal, and context gain are reported separately.
- [ ] PBM discovery, non-PBM confirmation, and all-79 description are not pooled into one evidence label.
- [ ] The non-PBM contextual interval crossing zero remains visible.
- [ ] The child-bootstrap sensitivity is shown without replacing the primary decision rule.
- [ ] Context-gain and response-entropy results contrary to prediction are not reframed as confirmation.
- [ ] Word-level cross-scorer magnitudes are not pooled.
- [ ] Generated candidates are not described as meaning-preserving.
- [ ] The old PBM response space is not mislabeled as all-79.
- [ ] The new Qwen handoff is described as data-complete but analysis-pending until a completion marker exists.
- [ ] Exact-string entropy is not called semantic entropy.
- [ ] Joint cloud positions are descriptive and not labeled Pareto-optimal.
- [ ] Sustained onset is reported as not established.
- [ ] The corrected cross-fitted Bayes analysis replaces the original pilot for substantive claims.
- [ ] Hall remains separate and non-causal.
- [ ] Listener utility is identified as a missing construct rather than inferred from target surprisal.
- [ ] All promoted estimates point to saved tables, manifests, and audit markers.
