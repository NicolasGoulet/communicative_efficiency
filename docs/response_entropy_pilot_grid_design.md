# Response-Space Entropy Pilot Grid Design

This document defines the pilot grid for sampling possible child responses from
base Mistral. It is a measurement-design artifact: the goal is to decide which
decoding settings produce stable and interpretable response-space entropy
before running the full production job.

## Design

| field | value |
| --- | --- |
| model | mistralai/Mistral-7B-v0.3 |
| prompt_template | Caregiver: {context} Child: |
| context_ks | ["k1", "k2", "k3"] |
| sample_per_age_bin_context_k | 20 |
| min_context_words | 1 |
| temperatures | [0.3, 0.5, 0.7, 1.0, 1.3, 1.6] |
| samples_per_context | 100 |
| max_new_tokens | 24 |
| top_p | 0.95 |
| top_k | 0 |
| do_sample | True |
| num_beams | 1 |
| repetition_penalty | 1.0 |
| no_repeat_ngram_size | 0 |
| seed | 20260615 |
| source | split scored tree |
| scored_root | results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023 |

## Stratified Context Selection

The pilot uses observed caregiver contexts from real child-response rows. The
selection is balanced by:

```text
age_bin x context window
```

The generation manifest is deduplicated by normalized context text. This keeps
the scientific stratum audit while avoiding repeated generation for identical
prompts.

| age_bin | context_k | eligible_context_strata | selected_context_strata | selected_unique_context_texts | eligible_children | selected_target_rows |
| --- | --- | --- | --- | --- | --- | --- |
| 006-023 | k1 | 3.187e+04 | 20 | 20 | 17 | 37 |
| 006-023 | k2 | 4.346e+04 | 20 | 20 | 17 | 25 |
| 006-023 | k3 | 4.441e+04 | 20 | 20 | 17 | 31 |
| 024-029 | k1 | 6.811e+04 | 20 | 20 | 21 | 34 |
| 024-029 | k2 | 9.794e+04 | 20 | 20 | 21 | 37 |
| 024-029 | k3 | 1.015e+05 | 20 | 20 | 21 | 29 |
| 030-035 | k1 | 5.957e+04 | 20 | 20 | 20 | 68 |
| 030-035 | k2 | 8.308e+04 | 20 | 20 | 20 | 31 |
| 030-035 | k3 | 8.577e+04 | 20 | 20 | 20 | 26 |
| 036-041 | k1 | 1.453e+04 | 20 | 20 | 8 | 44 |
| 036-041 | k2 | 1.948e+04 | 20 | 20 | 8 | 44 |
| 036-041 | k3 | 1.978e+04 | 20 | 20 | 8 | 30 |
| 042-047 | k1 | 7330 | 20 | 20 | 5 | 97 |
| 042-047 | k2 | 9307 | 20 | 20 | 5 | 32 |
| 042-047 | k3 | 9400 | 20 | 20 | 5 | 28 |
| 048-053 | k1 | 3882 | 20 | 20 | 3 | 39 |
| 048-053 | k2 | 4615 | 20 | 20 | 3 | 46 |
| 048-053 | k3 | 4640 | 20 | 20 | 3 | 50 |
| 054-059 | k1 | 2496 | 20 | 20 | 2 | 167 |
| 054-059 | k2 | 2897 | 20 | 20 | 2 | 52 |
| 054-059 | k3 | 2907 | 20 | 20 | 2 | 49 |
| 060-065 | k1 | 581 | 20 | 20 | 2 | 102 |
| 060-065 | k2 | 666 | 20 | 20 | 2 | 82 |
| 060-065 | k3 | 666 | 20 | 20 | 2 | 87 |

## Scale

```text
selected stratum rows: 480
deduplicated generation contexts: 480
temperatures: 6
samples per context per temperature: 100
planned generations: 288,000
```

## Generation Command

Run this on the GPU machine, not on the laptop:

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

## After Generation

After the sample CSV exists, run diagnostics:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_pilot_grid.py \
  --stage diagnostics \
  --samples results/response_entropy_pilot_grid/pilot_response_samples.csv.gz \
  --output-dir results/response_entropy_pilot_grid
```

## Output Files

- Eligible context strata: `results/response_entropy_pilot_grid/pilot_eligible_context_strata.csv.gz`
- Selected context strata: `results/response_entropy_pilot_grid/pilot_selected_context_strata.csv`
- Deduplicated generation manifest: `results/response_entropy_pilot_grid/pilot_generation_manifest.csv`
- Pilot audit: `results/response_entropy_pilot_grid/pilot_manifest_audit.csv`
- Method spec: `results/response_entropy_pilot_grid/pilot_method_spec.json`
