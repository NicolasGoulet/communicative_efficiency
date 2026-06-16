# Route 2 Response-Space Entropy Piloting Report

Created: 2026-06-16

Purpose: document how the Route 2 response-space entropy pilot was run, what
the generated samples show, what is currently defensible, and what should be
asked of supervisors before Mila-scale generation.

This is a meeting-facing technical note. It is not a final manuscript methods
section.

## 1. Supervisor Request Being Operationalized

The 2026-06-04 meeting clarified that the original next-token context entropy
measure was too narrow. The requested target is closer to uncertainty over
possible full child responses after a caregiver context.

The key idea from the transcript was:

- take the same caregiver context many times;
- sample possible responses from a language model;
- use the empirical distribution of sampled response strings to estimate
  response-space entropy;
- also record the average length of those sampled responses.

Important transcript interpretation:

- The supervisors asked for samples from a language model, not a search over
  observed child utterances.
- They did not prescribe the exact model, prompt, temperature, stopping rule, or
  quality filtering.
- Therefore, those details are measurement-design choices that must be piloted
  and reported.

## 2. Current Operational Definition

For each caregiver context, the current sampler constructs a minimal
transcript-style prompt:

```text
Caregiver: {context}
Child:
```

The model then generates a continuation. The intended analytic unit is the
first generated child response line, not an entire continued transcript.

Example:

```text
Prompt:
Caregiver: oh tell Kent tell Kent what happened to Inky?
Child:

Raw model continuation:
Inky went to the vet.
Caregiver: and what did the vet do?
Child: the vet gave Inky a shot.

Kept Route 2 response:
Inky went to the vet.
```

The `Caregiver:` / `Child:` wrapper is not a hidden result. It is part of the
measurement definition: it tells the base language model which discourse role
to continue.

## 3. Main Scientific Question About Stopping

Base Mistral does not reliably emit an EOS token for this task. In the probes,
generation usually stopped only because it hit `max_new_tokens`, not because
the model declared the continuation complete.

That means Route 2 needs an operational end-of-turn rule. The current best rule
is:

```text
sample the next child response line;
stop at the first newline or explicit speaker boundary;
keep max_new_tokens as a safety cap only.
```

This rule should not be described as "the model always changes speaker at
newline." The empirical finding is more careful:

- sometimes the first newline is followed by `Caregiver:` / `Parent:` / another
  speaker label;
- sometimes the first newline is followed by prose or document-like drift;
- in both cases, the first newline marks the end of the first generated response
  line.

For CHILDES-style utterance/turn analysis, the first generated response line is
the intended unit.

## 4. Pilot Runs Completed

### Full Temperature Pilot

Output:

```text
results/response_entropy_pilot_grid/pilot_response_samples_clean.csv.gz
docs/response_entropy_pilot_grid_diagnostics.html
```

Design:

```text
480 contexts
6 temperatures: 0.3, 0.5, 0.7, 1.0, 1.3, 1.6
100 samples per context-temperature
max_new_tokens = 24
total complete samples = 288,000
```

Completion audit:

```text
expected rows: 288,000
observed rows: 288,000
complete context-temperature pairs: 2,880 / 2,880
```

### Corrected Max-Token Probe

Output:

```text
results/response_entropy_stopping_probe_v2/
docs/response_entropy_stopping_probe_v2.html
```

Design:

```text
40 contexts balanced across context-length buckets
temperatures: 0.5, 0.7, 1.0
max_new_tokens: 12, 24, 48, 96
10 samples per context-temperature-cap
total samples = 4,800
```

Purpose: test whether later caps reduce failure to reach a newline/end-of-turn
boundary.

### Newline-Stop Validation Probe

Output:

```text
results/response_entropy_stopping_probe_v3/
docs/response_entropy_stopping_probe_v3.html
```

Design:

```text
40 contexts
temperatures: 0.5, 0.7
max_new_tokens = 48
10 samples per context-temperature
total samples = 800
```

Purpose: validate the first-newline/speaker-boundary trimming rule.

### Cap-96 Extreme-Temperature Smoke

Output:

```text
results/response_entropy_stopping_probe_v4_cap96_extreme_temps/
docs/response_entropy_stopping_probe_v4_cap96_extreme_temps.html
```

Design:

```text
40 contexts
temperatures: 0.3, 1.3, 1.6
max_new_tokens = 96
10 samples per context-temperature
planned samples = 1,200
```

Purpose: answer whether high temperatures that looked bad at cap 24 still fail
to reach a newline when given a much larger cap.

Status: completed on the PC at 2026-06-16 14:21:24 EDT.

Runtime note: this 1,200-sample cap-96 smoke took 699.9 seconds because the
then-current implementation still decoded all 96 tokens and trimmed afterward.
That limitation was addressed in the final generation smoke below, which used
true end-of-turn stopping during decoding.

### Final Generation Smoke With True End-Of-Turn Stopping

Output:

```text
results/response_entropy_final_generation_smoke/
docs/response_entropy_final_generation_smoke.html
```

Design:

```text
40 contexts balanced across context-length buckets
prompt variants: Caregiver, Parent, Adult
temperatures: 0.3, 0.5, 0.7, 1.0
target accepted samples per context-temperature-prompt: 20
max attempts per context-temperature-prompt: 60
max_new_tokens = 96 safety cap
```

Purpose: run the final pre-Slurm generation procedure itself, not entropy
scoring. This smoke tested true end-of-turn stopping, accepted versus rejected
attempt logging, deterministic quality flags, prompt-variant robustness, and
the final temperature grid.

Status: completed on the PC on 2026-06-16.

Result:

```text
accepted responses: 9,512
total attempts: 10,203
complete settings: 473 / 480
incomplete settings: 7 / 480
```

All 7 incomplete settings came from one repetitive context:

```text
blink blink blink blink blink blink blink. blink blink blink. that's a light too.
```

The generation procedure is therefore ready to feed an entropy-scoring smoke,
with the incomplete-context caveat retained in the audit tables.

## 4.1 Plot Artifacts

Detailed probe reports with figures:

```text
docs/response_entropy_stopping_probe_v2.html
docs/response_entropy_stopping_probe_v3.html
docs/response_entropy_stopping_probe_v4_cap96_extreme_temps.html
```

Most useful v4 plots:

![v4 boundary rate](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_boundary_rate.png)

![v4 stop categories](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_stop_categories.png)

![v4 p90 trimmed response words](../figs/response_entropy_stopping_probe_v4_cap96_extreme_temps/stopping_probe_p90_trimmed_words.png)

## 5. What We Learned About Max Tokens

The full 288k pilot had `max_new_tokens=24`. At that cap, the proportion of
samples that did not reach any newline before the cap was:

| Temperature | Cap | Did Not Reach Newline |
| --- | ---: | ---: |
| 0.3 | 24 | 0.83% |
| 0.5 | 24 | 1.11% |
| 0.7 | 24 | 1.76% |
| 1.0 | 24 | 8.83% |
| 1.3 | 24 | 40.76% |
| 1.6 | 24 | 76.68% |

The corrected cap-grid probe tested only T=0.5, T=0.7, and T=1.0 at larger
caps:

| Temperature | Cap 24 | Cap 48 | Cap 96 |
| --- | ---: | ---: | ---: |
| 0.5 | 2.00% | 1.50% | 1.25% |
| 0.7 | 1.50% | 0.50% | 0.25% |
| 1.0 | 8.25% | 2.25% | 0.50% |

The cap-96 extreme-temperature smoke added:

| Temperature | Cap 96 | Did Not Reach Newline |
| --- | ---: | ---: |
| 0.3 | 96 | 0.00% |
| 1.3 | 96 | 20.00% |
| 1.6 | 96 | 62.75% |

Interpretation after the extreme-temperature cap-96 smoke:

- T=0.5 and T=0.7 are already clean under cap 48/96.
- T=1.0 becomes much cleaner at cap 96 but remains less reliable in entropy
  stability and sample quality.
- T=0.3 is structurally very clean but may be too conservative for estimating
  a rich response-space distribution.
- T=1.3 and T=1.6 remain poor even with cap 96. The problem is not just the old
  24-token cap; high-temperature generations often do not form clean one-turn
  responses.

## 6. Quality Audit Of Existing Samples

An automatic audit was run on existing samples only. It simulated the proposed
first-line rule by re-trimming raw generations at the first newline.

Hard-bad flags included:

- empty first line;
- no newline before the cap;
- speaker label inside the kept first line;
- obvious metadata/prose starts;
- long cap-hit first lines;
- repetition loops.

Softer review flags additionally included possible context-copying.

Results for T=0.5/T=0.7:

| Source | Temperature | Hard Bad | Review-Flagged Including Copy |
| --- | ---: | ---: | ---: |
| v3 cap-48 probe | 0.5 | 4.25% | 9.75% |
| v3 cap-48 probe | 0.7 | 2.50% | 7.25% |
| full pilot first-line trim | 0.5 | 3.42% | 11.41% |
| full pilot first-line trim | 0.7 | 4.25% | 8.73% |
| full pilot first-line trim | 1.0 | 11.35% | 12.27% |
| v4 cap-96 smoke | 0.3 | 3.00% | 7.75% |
| v4 cap-96 smoke | 1.3 | 28.75% | 29.25% |
| v4 cap-96 smoke | 1.6 | 70.50% | 70.50% |

Interpretation:

- T=0.5 and T=0.7 are not perfect, but the obvious structural failure rate is
  low enough to justify a formalized smoke test.
- T=1.0 has more cap/no-boundary failures and is a less attractive production
  setting.
- T=0.3 is clean but conservative; it can be useful as a lower-temperature
  sensitivity point, but it is not the best primary measure of response-space
  uncertainty.
- T=1.3/T=1.6 should not be used for production. Their cap-96 hard-bad rates
  are too high, and manual examples show long incoherent continuations.

## 7. Examples

### Good / Usable

```text
Context:
good job Sweetie. good job.

Kept response:
thank you.
```

```text
Context:
didjou have Petrie over here? or was Petrie in the living room?

Kept response:
Petrie was in the living room.
```

### Good, And End-Of-Turn Stopping Helps

```text
Context:
oh tell Kent tell Kent what happened to Inky?

Raw generation:
Inky went to the vet.
Caregiver: and what did the vet do?
Child: the vet gave Inky a shot.

Kept response:
Inky went to the vet.
```

### Review: Possible Context Copy

```text
Context:
lettuce she's eating lettuce.

Kept response:
lettuce she's eating lettuce.
```

This may be a valid child-like repetition, but it should be flagged so that
copying rates can be reported.

### Bad: Repetition Loop

```text
Context:
Dominic. are you gonna tell me what these are? what?

Kept response:
they are like, like, like, like, like, like, like, like, like, like, like,
```

### Bad: Prose / Metadata Drift

```text
Context:
Ann_Marie no more foolin.

Raw generation:

## How I Grew Up

I grew up in a small town...
```

### Bad: No Clean Boundary Before Cap

```text
Context:
Daddy hasta set it up. Sarah don't you think it would be a lot easier if you got off the chair.

Kept response:
No, I'm not getting off the chair. I'm not getting off the chair. I'm not
```

### Bad: High-Temperature Incoherence

At T=1.3 and T=1.6, cap 96 often produces long continuations that are neither
child-like nor context-relevant.

```text
Context:
where's your egg?

T=1.3 kept response:
manned security just came running over saying they are running hot, tell
!manning alone them immediately along with carts ...
```

```text
Context:
what's Granny_Dryden doing?

T=1.6 kept response:
Oh watching others parment Name that beg literary fragject or commander segment
passenger boot texture demolction ...
```

## 8. Production Strategy After Final Smoke

Carry forward the final smoke design for Mila-scale generation:

1. Use true end-of-turn stopping during decoding.
2. Use `max_new_tokens=96` as a safety cap, not as the intended response
   length.
3. Use T=0.5 as the primary temperature and T=0.7 as the main sensitivity
   temperature, unless supervisors ask for a different design.
4. For each context-temperature, sample until the required number of valid
   child-turn responses is reached.
5. Record every rejected attempt and rejection reason.
6. Flag contexts with high rejection rates.
7. Store all accepted responses, all quality flags, and enough rejected-sample
   metadata to audit the measurement.

The "resample until valid" strategy is defensible only if rejection rates are
reported. Silently resampling would change the induced distribution without
making the conditioning clear.

Recommended wording:

```text
We estimate response entropy over valid one-turn child-response completions.
Invalid completions such as empty lines, no end-of-turn boundary before the
safety cap, metadata/prose drift, and repetition loops were rejected according
to preregistered quality rules; rejection counts and rates were retained as
diagnostics.
```

## 9. Questions For Supervisors

Ask these explicitly before production:

1. Is the transcript-style prompt `Caregiver: {context}\nChild:` acceptable as
   the operational definition of possible child responses?
2. Should response entropy be estimated over accepted valid child-turn samples
   only, with rejected samples recorded, or should invalid samples remain in the
   empirical distribution as model behavior?
3. Is T=0.5 primary plus T=0.7 sensitivity acceptable, or do they want a
   broader temperature sensitivity analysis?
4. Should exact context-copy responses be kept, flagged, or excluded?
5. Should the production run target 100 accepted samples per context, or 100
   total attempts with possible invalid samples included?

## 10. Current Recommendation

Do not launch the full Mila Slurm production run yet.

Do next:

1. Run the entropy/scoring smoke from
   `docs/route2_entropy_scoring_script_prompt.md`, using the accepted samples
   and audit tables from `results/response_entropy_final_generation_smoke/`.
2. Check entropy distributions, split-half reliability, downsample stability,
   temperature correlations, prompt-variant correlations, join coverage, and
   the tiny downstream sanity model.
3. Review the final generation-smoke examples and entropy-smoke examples with
   supervisors.
4. Confirm the operational definition with supervisors before full Mila-scale
   production.

Then proceed to Mila-scale generation if the entropy smoke shows stable
predictors, acceptable join coverage, and supervisor agreement on the
operational definition.

Current temperature recommendation:

```text
Primary: T=0.5
Sensitivity: T=0.7
Optional conservative diagnostic: T=0.3
Optional diagnostic only, not primary production: T=1.0
Do not use for production: T=1.3, T=1.6
```
