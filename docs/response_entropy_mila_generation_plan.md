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

## Completed Local Pilot And Final Smoke Status

The broad PC pilot completed and was audited:

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
completed samples: 288,000
```

The final pre-Slurm generation smoke also completed on the PC:

```text
output: results/response_entropy_final_generation_smoke/
report: docs/response_entropy_final_generation_smoke.html
contexts: 40 balanced across context-length buckets
prompt variants: Caregiver, Parent, Adult
temperatures: 0.3, 0.5, 0.7, 1.0
target accepted samples per context-temperature-prompt: 20
max attempts per setting: 60
accepted samples: 9,512
attempts: 10,203
complete settings: 473 / 480
```

The final smoke used true end-of-turn stopping during decoding, accepted versus
rejected attempt logging, deterministic quality flags, prompt-variant
robustness checks, and the cap-96 safety rule. The remaining 7 incomplete
settings came from one repetitive context and should be treated as a production
audit case, not as a reason to discard the overall procedure.

## What We Need Before Main Generation

Before launching a larger Mila run, run the Route 2 entropy smoke using the
final generation-smoke outputs. That smoke should inspect:

- entropy distributions by temperature;
- split-half reliability;
- downsample stability adapted to the available M=20 accepted-smoke sample cap;
- rank correlations of context entropy across temperatures;
- rank correlations of context entropy across prompt variants;
- join coverage back to real child rows;
- a small downstream sanity model.

The entropy smoke should answer:

```text
Do the accepted samples produce stable response-entropy predictors?
Do T=0.5 and T=0.7 rank contexts similarly enough for primary/sensitivity use?
Does prompt wording materially change the predictor?
Are join gaps small and explainable?
Is the entropy script ready to consume full Mila-scale samples?
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

The old pilot sampler command below is no longer the preferred production
template because it samples a fixed number of raw generations and trims
post-hoc. Production should be based on the final smoke procedure: true
end-of-turn stopping, accepted/rejected attempt logging, quality flags, and an
attempt cap. The exact Slurm command should be written after the entropy smoke
confirms the feature builder.

For historical reference, the older one-shard sampler command was:

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

On larger GPUs, computational microbatch sizes can be increased after a tiny
smoke test. The scientific target should be accepted valid child-turn samples,
not merely total raw attempts.

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

1. Completed: broad PC pilot.
2. Completed: final generation smoke with true stopping and rejection logging.
3. Next: run the entropy/scoring smoke from
   `docs/route2_entropy_scoring_script_prompt.md`.
4. Review entropy stability, prompt/temperature sensitivity, and join audit.
5. Confirm operational choices with supervisors.
6. Build production manifest.
7. Split manifest into shards.
8. Rsync manifest/code/configs to Mila.
9. Run one smoke shard.
10. Run one real shard.
11. Launch Slurm array.
12. Audit completion.
13. Build diagnostics and recommendations.
14. Only then join response-space entropy predictors into analysis tables.

## Current Recommendation After Generation Smoke

For production planning, expect to use:

```text
primary model: mistralai/Mistral-7B-v0.3
prompt: Caregiver: {context}\nChild:
top_p: 0.95
top_k: 0
max_new_tokens: 96 safety cap
primary temperature: 0.5
sensitivity temperature: 0.7
optional conservative diagnostic: 0.3
T=1.0: optional diagnostic only, not primary production
```

This is not final until the entropy smoke confirms stable predictors and the
supervisors approve accepted-only entropy and prompt-wrapper choices.
