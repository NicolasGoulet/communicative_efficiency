# Prompt 2: Route 2 Entropy Scoring Script After Final Generation Smoke

Use this prompt with a future coding agent after the final Route 2 generation
smoke has completed.

Status as of 2026-06-16: the final generation smoke has completed. Use these
actual smoke artifacts as the default inputs for this entropy smoke:

```text
results/response_entropy_final_generation_smoke/accepted_samples.csv.gz
results/response_entropy_final_generation_smoke/all_attempts.csv.gz
results/response_entropy_final_generation_smoke/rejection_summary_by_setting.csv
results/response_entropy_final_generation_smoke/quality_flags_by_setting.csv
results/response_entropy_final_generation_smoke/smoke_manifest.csv
results/response_entropy_final_generation_smoke/smoke_manifest_audit.csv
docs/response_entropy_final_generation_smoke.html
```

Do not regenerate samples unless one of these artifacts is missing or corrupted.

## Objective

Create the entropy scoring / feature-building script that consumes the Route 2
generated response samples and computes response-space entropy predictors for
downstream Route 2 analyses.

Important conceptual distinction:

- The previous task generated possible child responses from Mistral.
- This task **does not generate new responses unless a missing smoke artifact
  must be regenerated**.
- This task computes entropy and related summary features from accepted sampled
  response strings.
- This entropy is **not computed from the real child utterances**.
- Real child utterances are downstream outcomes to be predicted.

## Scientific Goal

For each caregiver context `c`, we have accepted sampled responses:

```text
y_1, y_2, ..., y_M ~ Mistral(child response | caregiver context c)
```

Compute empirical response-space entropy over normalized response types:

```text
H(response | context) = - sum_r p_hat(r | c) log2 p_hat(r | c)
```

where:

```text
p_hat(r | c) = count(response_type = r) / accepted_sample_count
```

Then attach those context-level entropy predictors back to the Route 2 analysis
frame so we can model real child production effort:

```text
real_child_effort ~ response_entropy + expected_sample_length + controls
```

## Required Inputs

Consume the final generation-smoke outputs, expected to include:

```text
results/response_entropy_final_generation_smoke/accepted_samples.csv.gz
results/response_entropy_final_generation_smoke/all_attempts.csv.gz
results/response_entropy_final_generation_smoke/rejection_summary_by_setting.csv
results/response_entropy_final_generation_smoke/quality_flags_by_setting.csv
results/response_entropy_final_generation_smoke/smoke_manifest.csv
```

The completed smoke wrote 9,512 accepted responses from 10,203 attempts across
40 contexts x 3 prompt variants x 4 temperatures. It reached 20 accepted
samples for 473/480 context-temperature-prompt settings; the 7 incomplete
settings all came from one repetitive context and should remain visible in the
entropy stability and join audits.

Also consume the relevant context/Route 1 analysis frame or manifest needed to
join entropy features back to real child utterance rows.

Do not load or print entire large datasets.

## Required Entropy Features

For each unique context / temperature / prompt variant:

```text
accepted_sample_count
attempt_count
rejection_count
rejection_rate
unique_response_count
top_response_probability
empirical_response_entropy_bits
miller_madow_entropy_bits
normalized_entropy_by_log_sample_count
response_evenness_observed_types
mean_sample_words
median_sample_words
p90_sample_words
mean_sample_characters
quality_flag_rates
```

Response normalization should be explicit and tested. At minimum:

```text
strip leading/trailing whitespace
collapse internal whitespace
optionally lowercase for entropy type counting, but keep both raw and normalized variants
preserve punctuation-normalized and punctuation-sensitive alternatives if useful
```

## Stability Checks

Compute entropy stability from the accepted samples:

```text
entropy using first 25 accepted samples
entropy using first 50 accepted samples
entropy using full accepted samples
split-half entropy reliability
rank correlations across sample sizes
rank correlations across temperatures
rank correlations across prompt variants
```

If the final smoke used fewer than 100 accepted samples, adapt the sample-size
stability checks to the available sample counts and document this explicitly.

## Downstream Join Checks

Attach entropy features back to the analysis frame by stable context key:

```text
context_id if stable and unique
normalized context text if context_id differs across duplicated text
prompt variant
temperature
context window, if available
```

Audit:

```text
number of real child rows
number with entropy joined
number missing entropy
top missing contexts
duplicate context handling
whether k1/k2/k3 identical text was deduplicated correctly
```

## Tiny Downstream Sanity Model

Run only a tiny smoke model, not final science:

```text
real_child_words ~ response_entropy + mean_sample_words + context_word_count + age
```

Optionally repeat for:

```text
real_child_morphemes
real_child_syllables
real_child_phonemes
```

Purpose: verify the feature joins and signs are computable, not claim final
results.

## GPU / PC Instructions

Entropy computation from already-generated sample CSVs should usually be CPU
only.

If the script only reads generated samples and computes entropy, run locally.

If the task discovers that it needs to regenerate samples or compute
model-sequence probabilities with Mistral, do not run that on the laptop.
Run the GPU smoke on the PC:

```bash
ssh alkan@192.168.7.217
cd /home/alkan/Portelance/communicative_efficiency
```

Use a detached command for GPU work, write logs, and provide a progress-check
command before leaving the job.

## Outputs Required

Write outputs under a new directory, for example:

```text
results/response_entropy_final_scoring_smoke/
figs/response_entropy_final_scoring_smoke/
docs/response_entropy_final_scoring_smoke.md
docs/response_entropy_final_scoring_smoke.html
```

Required files:

```text
context_response_entropy_features.csv
context_response_entropy_stability.csv
context_response_entropy_join_audit.csv
context_response_entropy_temperature_correlations.csv
context_response_entropy_prompt_correlations.csv
route2_analysis_smoke_with_entropy.csv.gz
route2_sanity_model_summary.csv
manual_review_entropy_examples.csv
```

Required plots:

```text
entropy distribution by temperature
entropy vs mean sampled response length
sample-size stability plot
temperature rank-correlation heatmap
prompt-variant rank-correlation heatmap
joined/missing entropy audit plot
```

Required report sections:

```text
what was generated versus what was scored
entropy formula
normalization choices
sample-size stability
temperature/prompt sensitivity
join audit
tiny downstream sanity model
recommendation for supervisor meeting
questions that remain before full production
```

## Tests

Add focused tests for:

```text
response normalization
empirical entropy calculation
Miller-Madow correction
top-response probability
split-half stability
sample-size downsampling
context join audit
report writing
```

Run focused tests and, if feasible, the full suite.

## Decision Output

At the end, state clearly:

```text
Is the entropy script ready to consume full Mila-scale samples?
Are the generated samples stable enough for 100 accepted responses per context?
Do T=0.5 and T=0.7 give similar context rankings?
Does prompt wording materially change the predictor?
Are join gaps small and explainable?
What exact summary should be sent to supervisors?
```
