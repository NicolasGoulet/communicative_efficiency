# Response-Space Entropy Generation On Mila

Created: 2026-06-15

This note records the computational plan for moving response-space entropy
generation from the local PC to Mila once the pilot has been inspected.

## Why Move This To Mila

The response-space entropy estimator scales as:

```text
unique_contexts x temperatures x samples_per_context
```

The current PC pilot is scientifically useful because it tests prompts,
temperatures, output quality, entropy stability, and code correctness. However,
it is running on one RTX 4060 Ti with 16GB VRAM. That forces conservative
microbatching and makes even the pilot feel slow.

For production, Mila is a better fit because we can:

- use larger GPUs with more memory and throughput;
- split the manifest into independent shards;
- run shards in parallel with Slurm arrays;
- keep the exact same scientific settings while reducing wall-clock time;
- preserve one output CSV per shard for auditing and restartability.

## Current Local Pilot Status

The current PC pilot is still valuable and should be allowed to finish unless
we intentionally cancel it. It is testing:

```text
model: mistralai/Mistral-7B-v0.3
prompt: Caregiver: {context}\nChild:
temperatures: 0.3, 0.5, 0.7, 1.0, 1.3, 1.6
samples_per_context: 100
top_p: 0.95
top_k: 0
max_new_tokens: 24
context windows: k1, k2, k3
pilot contexts: 480
planned samples: 288,000
```

The PC run uses:

```text
batch_contexts: 2
batch_samples: 16
shared HF cache: ~/.cache/huggingface
```

The pilot diagnostics should only be trusted after the generation is complete.
The diagnostics script now refuses incomplete final reports by default.

## What We Need From The Pilot Before Main Generation

Before launching a larger Mila run, inspect:

- empty response rate by temperature;
- max-token-hit rate by temperature;
- boundary-stop rate by temperature;
- entropy distributions by temperature;
- split-half reliability at M=100;
- downsample stability at M=25, 50, 75, 100;
- rank correlations of context entropy across temperatures;
- a small manual audit of generated responses.

The pilot should answer:

```text
Which temperatures produce interpretable child-like continuations?
Are context entropy rankings stable enough at M=100?
Can we reduce or must we increase samples_per_context?
Should the production grid use all pilot temperatures or a smaller subset?
```

No main production run should start before these questions are reviewed.

## Recommended Mila Strategy

Use the same scripts, but shard the generation manifest.

Recommended production layout:

```text
results/response_entropy_generation/
  manifests/
    production_manifest.csv
    shards/
      shard_0000.csv
      shard_0001.csv
      ...
  samples/
    temp_0.7/
      shard_0000.samples.csv.gz
      shard_0001.samples.csv.gz
      ...
    temp_1.0/
    temp_1.3/
  logs/
  diagnostics/
```

Each Slurm task should handle one independent unit such as:

```text
temperature x shard_id
```

This avoids one giant fragile job and makes failed tasks easy to rerun.

## Sharding Principles

Shard by context rows, not by sample rows.

Good:

```text
shard_0000.csv contains 500 or 1,000 contexts
one task samples all M responses for those contexts at one temperature
```

Avoid:

```text
one task generates sample indices 1-10 and another generates 11-20
```

Reason: context-level completion is easier to audit when every
context-temperature pair is complete inside one shard output.

## Cache And Model Handling On Mila

Do not put model weights inside this Git repo.

Use a shared Hugging Face cache on Mila scratch, for example:

```bash
export HF_HOME="$SCRATCH/huggingface"
```

or an equivalent project cache path. The exact path should be checked on Mila
before launch. The important rule is:

```text
all Slurm tasks use the same HF_HOME
```

This prevents every job from redownloading Mistral separately.

## Mila Generation Command Template

For one shard and one temperature:

```bash
env HF_HOME="$SCRATCH/huggingface" MPLCONFIGDIR=/tmp/matplotlib \
  .venv/bin/python src/sample_context_responses.py \
  --manifest results/response_entropy_generation/manifests/shards/shard_0000.csv \
  --output results/response_entropy_generation/samples/temp_1.0/shard_0000.samples.csv.gz \
  --model mistralai/Mistral-7B-v0.3 \
  --temperatures 1.0 \
  --samples-per-context 100 \
  --batch-contexts 2 \
  --batch-samples 16 \
  --max-new-tokens 24 \
  --top-p 0.95 \
  --top-k 0 \
  --dtype bfloat16 \
  --device auto
```

On larger GPUs, `--batch-samples` can be increased after a tiny smoke test.
The scientific setting is `samples_per_context`; `batch_samples` is only a
computational microbatch parameter.

## Suggested Mila Pilot Before Production

Before running the full production manifest on Mila:

1. Run one tiny smoke job:

```text
1 shard x 1 temperature x 2 contexts x 4 samples
```

2. Run one real-size shard:

```text
1 shard x 1 temperature x M=100
```

3. Confirm:

```text
output CSV exists
row count = contexts_in_shard x samples_per_context
GPU memory is stable
no model cache duplication
no empty/garbled catastrophic output
```

Only then launch the Slurm array.

## Completion Audit

After all shard outputs are present, build a combined sample file or a combined
feature table and audit:

```text
expected_rows = unique_contexts x temperatures x samples_per_context
observed_rows = sum rows across shard sample CSVs
expected_context_temperature_pairs = unique_contexts x temperatures
complete_pairs = pairs with exactly M unique sample_index values
```

No analysis should use response-space entropy outputs until this audit passes.

## Diagnostics After Mila Generation

The current diagnostics script expects one sample CSV:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \
  src/build_response_entropy_pilot_grid.py \
  --stage diagnostics \
  --samples results/response_entropy_generation/combined_samples.csv.gz \
  --generation-manifest results/response_entropy_generation/manifests/production_manifest.csv \
  --temperatures 0.7,1.0,1.3 \
  --samples-per-context 100 \
  --output-dir results/response_entropy_generation/diagnostics
```

If production uses many shard files, we should either:

- concatenate samples into one `combined_samples.csv.gz`; or
- add a diagnostics mode that reads a directory of shard CSVs.

The second option will be more scalable for very large production runs.

## Recommended Decision Flow

Use this sequence:

1. Finish the PC pilot or intentionally stop it.
2. Run final pilot diagnostics.
3. Decide temperature grid and sample count.
4. Build production manifest.
5. Split manifest into shards.
6. Rsync manifest/code/configs to Mila.
7. Run one smoke shard.
8. Run one real shard.
9. Launch Slurm array.
10. Audit completion.
11. Build diagnostics and recommendations.
12. Only then join response-space entropy predictors into analysis tables.

## Current Recommendation Before Seeing Pilot Results

For production, expect to use Mila with:

```text
primary model: mistralai/Mistral-7B-v0.3
prompt: Caregiver: {context}\nChild:
top_p: 0.95
top_k: 0
max_new_tokens: 24
samples_per_context: 100 unless pilot says otherwise
temperatures: likely a reduced grid such as 0.7, 1.0, 1.3
```

But this is not final. The actual production grid should be chosen after the
pilot diagnostics.

