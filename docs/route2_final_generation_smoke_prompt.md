# Prompt 1: Route 2 Final Generation Smoke Before Mila Production

Status as of 2026-06-16: completed. The implemented smoke script is
`src/build_response_entropy_final_generation_smoke.py`; the PC runner is
`scripts/run_response_entropy_final_generation_smoke_pc.sh`; the report is
`docs/response_entropy_final_generation_smoke.html`; and the generated smoke
artifacts are under `results/response_entropy_final_generation_smoke/`.

Use this prompt with a future coding agent before writing the full Mila Slurm
production script.

## Objective

Implement and run the final Route 2 response-generation smoke test. This smoke
must automatically test the final generation procedure before we ask supervisors
whether we are ready for Mila-scale production.

Important conceptual distinction:

- This task is **generation/sampling**, not entropy scoring.
- It samples possible child responses from Mistral for each caregiver context.
- The entropy script will be a separate downstream task.

## Scientific Goal

For each caregiver context, estimate the model-induced distribution over
possible child responses by repeatedly prompting Mistral:

```text
Caregiver: {context}
Child:
```

The intended generated unit is one child conversational turn / first response
line.

## Required Implementation

Implement items 1-5 from the pre-Slurm checklist:

1. **True end-of-turn stopping during generation**
   - Stop decoding as soon as an end-of-turn marker is generated.
   - End-of-turn markers should include at least:

```text
\n
\nCaregiver:
\nParent:
\nAdult:
\nChild:
\nCHI:
```

   - Keep `max_new_tokens=96` only as a safety cap.
   - Do not rely only on post-hoc trimming.

2. **Accepted vs rejected sampling**
   - For each context-temperature pair, sample until the target number of
     valid accepted child-turn responses is reached.
   - Record every attempt, accepted or rejected.
   - Record rejection reasons such as:

```text
empty_response
no_boundary_before_cap
repetition_loop
metadata_or_prose_drift
malformed_response
speaker_label_inside_response
other_quality_flag
```

   - Record attempts needed per accepted sample and total rejection rate per
     context-temperature pair.

3. **Automatic quality flags**
   - Add deterministic flags for:

```text
empty first-line response
speaker label inside kept response
metadata/prose start
repetition loop
no end-of-turn boundary before cap
possible context copy
very long first-line response
```

4. **Prompt robustness**
   - Test at least these prompt variants on the smoke contexts:

```text
Caregiver: {context}
Child:

Parent: {context}
Child:

Adult: {context}
Child:
```

   - Report whether entropy/rank ordering is similar across prompt variants.

5. **Temperature decision**
   - Test exactly these temperatures:

```text
0.3, 0.5, 0.7, 1.0
```

   - The current prior is:

```text
primary: 0.5
sensitivity: 0.7
optional conservative diagnostic: 0.3
no production use unless supervisors request it: 1.0
```

## Smoke Size

Use a small but informative smoke, not a full production run.

Recommended default:

```text
40 contexts balanced across context-length buckets
temperatures: 0.3, 0.5, 0.7, 1.0
prompt variants: Caregiver, Parent, Adult
accepted samples per context-temperature-prompt: 20
max attempts per context-temperature-prompt: choose a conservative cap, e.g. 60
max_new_tokens: 96
```

If compute time is too high, reduce accepted samples to 10, but document the
change.

## GPU / PC Instructions

Do not run GPU generation on the laptop.

Run the smoke on the PC through SSH:

```bash
ssh alkan@192.168.7.217
cd /home/alkan/Portelance/communicative_efficiency
```

Launch long commands detached with `setsid` or `nohup`, write logs under the
output directory, and print a progress-check command before leaving the job.

The progress-check command should report:

```text
process status
GPU utilization
output file size / row counts
tail of log
```

## Outputs Required

Write outputs under a new dated or clearly named directory, for example:

```text
results/response_entropy_final_generation_smoke/
figs/response_entropy_final_generation_smoke/
docs/response_entropy_final_generation_smoke.md
docs/response_entropy_final_generation_smoke.html
```

Required output tables:

```text
accepted_samples.csv.gz
all_attempts.csv.gz
rejection_summary_by_setting.csv
quality_flags_by_setting.csv
prompt_temperature_rank_correlations.csv
manual_review_examples.csv
smoke_manifest.csv
smoke_manifest_audit.csv
```

Required report sections:

```text
method and prompt definition
temperature results
prompt robustness results
rejection rates
quality flag rates
examples: good / review / rejected
recommendation for supervisor meeting
remaining risks before Slurm
```

## Tests

Add focused unit tests for:

```text
end-of-turn stopping
attempt logging
accepted/rejected sample schema
quality flag classification
prompt variant manifest
summary/report writing
```

Run focused tests locally. If the smoke requires GPU, run the smoke on the PC.

## Decision Output

At the end, state clearly:

```text
Can we justify T=0.5 primary and T=0.7 sensitivity?
Does T=0.3 add useful conservative information?
Should T=1.0 be excluded or kept as an optional diagnostic?
Are rejection rates low enough for production?
Are prompt-variant rankings stable enough?
What exact questions should be asked of supervisors?
```
