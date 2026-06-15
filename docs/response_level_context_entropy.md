# Response-Level Context Entropy

This note formalizes the context-predictability measure discussed in the
2026-06-04 meeting with Yang Xu and Eva Portelance.

## Motivation

The current context entropy feature in this project is next-token entropy:

```text
H(next token | context)
```

That is mathematically clean, but it only asks how uncertain the model is about
the first next token. The meeting discussion asked for a stronger measure:

```text
How uncertain is the model about the whole possible response to the context?
```

This is meant to support the production-effort hypothesis:

```text
high response uncertainty in the context  -> longer child response
low response uncertainty in the context   -> shorter child response
```

## Objects

For target utterance `i`, let:

- `c_i` be the preceding caretaker context, for example `context_k3`.
- `Y_i` be a possible response to that context.
- `G_theta,T(Y | c_i)` be the response distribution induced by a language model
  with parameters `theta` and sampling temperature `T`.
- `M` be the number of sampled responses per context, for example `M = 100`.

We sample:

```text
y_i1, y_i2, ..., y_iM ~ G_theta,T(Y | c_i)
```

The prompt template is part of the measurement definition. A default template
for child-response sampling is:

```text
Caregiver: {context}
Child:
```

This can and should be varied in robustness checks.

## Empirical Response Entropy

Let `nu(y)` be a response canonicalization function. The safest initial version
is exact normalized text: trim whitespace and collapse internal spaces. A
case-folded version can be used as a robustness check.

For a context `c_i`, define response types:

```text
z_im = nu(y_im)
R_i = unique response types among z_i1 ... z_iM
```

Counts:

```text
n_i(r) = sum_m 1[z_im = r]
```

Empirical probabilities:

```text
p_hat_i(r) = n_i(r) / M
```

Empirical response entropy:

```text
H_hat_resp(c_i, T) = - sum_{r in R_i} p_hat_i(r) log2 p_hat_i(r)
```

Finite-sample corrected version:

```text
H_hat_MM(c_i, T) = H_hat_resp(c_i, T) + (K_i - 1) / (2 M ln 2)
```

where `K_i = |R_i|`. The Miller-Madow correction is useful because empirical
entropy is downward-biased when `M` is finite.

## Additional Sample-Based Predictors

Expected response length under the model:

```text
E_hat[L_u(Y) | c_i, T] = (1/M) sum_m L_u(y_im)
```

where `u` can be words, surface morphemes, syllables, or phonemes. This is a
separate predictor from entropy. It asks whether children simply match the
model's expected response length for a context.

Other useful diagnostics:

- `unique_response_count = K_i`
- `top_response_probability = max_r p_hat_i(r)`
- `normalized_entropy_by_samples = H_hat_resp / log2(M)`
- `normalized_entropy_by_observed_types = H_hat_resp / log2(K_i)`

## Temperature Sensitivity

Temperature changes the generated response distribution:

```text
p_T(token | history) = softmax(logits / T)
```

Therefore response entropy is not an absolute property of the context alone.
It is a property of:

```text
model + prompt + decoding parameters + temperature
```

Recommended first grid:

```text
T in {0.7, 1.0, 1.3}
M = 100 samples per context
max_new_tokens = 20 or 30
```

The important robustness check is whether contexts keep roughly the same rank
ordering and whether the regression coefficient for response entropy remains
directionally stable across temperatures.

## Pilot Grid Framework

Before production sampling, use the pilot-grid workflow:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_pilot_grid.py \
  --stage manifest \
  --sample-per-age-bin-context-k 20 \
  --temperatures 0.3,0.5,0.7,1.0,1.3,1.6 \
  --samples-per-context 100 \
  --max-new-tokens 24 \
  --top-p 0.95 \
  --top-k 0
```

This streams the split scored-result tree rather than the 11M-row Route 1
table. It writes:

```text
results/response_entropy_pilot_grid/pilot_eligible_context_strata.csv.gz
results/response_entropy_pilot_grid/pilot_selected_context_strata.csv
results/response_entropy_pilot_grid/pilot_generation_manifest.csv
results/response_entropy_pilot_grid/pilot_manifest_audit.csv
results/response_entropy_pilot_grid/pilot_method_spec.json
docs/response_entropy_pilot_grid_design.html
```

The current PBM pilot design selects:

```text
20 contexts per age_bin x context_k
8 age bins x 3 context windows = 480 selected strata
480 deduplicated generation contexts
6 temperatures x 100 samples = 288,000 planned generated responses
```

Generation command from the design report:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/sample_context_responses.py \
  --manifest results/response_entropy_pilot_grid/pilot_generation_manifest.csv \
  --output results/response_entropy_pilot_grid/pilot_response_samples.csv.gz \
  --model mistralai/Mistral-7B-v0.3 \
  --temperatures 0.3,0.5,0.7,1.0,1.3,1.6 \
  --samples-per-context 100 \
  --batch-contexts 2 \
  --batch-samples 16 \
  --max-new-tokens 24 \
  --top-p 0.95 \
  --top-k 0 \
  --dtype bfloat16 \
  --device auto
```

After GPU generation, run:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_pilot_grid.py \
  --stage diagnostics \
  --samples results/response_entropy_pilot_grid/pilot_response_samples.csv.gz \
  --output-dir results/response_entropy_pilot_grid
```

Diagnostics include:

- output-quality rates by temperature;
- context-temperature response entropy;
- split-half entropy reliability;
- downsample stability for M=25, 50, 75, 100;
- temperature rank-correlation matrix;
- publication-facing diagnostic HTML.

This pilot is a decision step, not the production run. After diagnostics are
rendered, review the temperature/output-quality recommendations before
launching any larger response-space entropy job.

For the larger generation run, use the Mila handoff:

```text
docs/response_entropy_mila_generation_plan.md
```

That note records the sharding strategy, cache rules, Slurm-oriented execution
plan, completion audit, and stop point before production.

## First Inferential Model

For real child utterances:

```text
child_effort_i ~ age_i
               + response_entropy_i
               + expected_model_response_length_i
               + context_surface_length_i
               + preceding_question_features_i
               + child controls
```

The key prediction is:

```text
beta_response_entropy > 0
```

That is, contexts with more dispersed possible responses should elicit longer
or more effortful child utterances if children are modulating production effort
according to contextual uncertainty.
