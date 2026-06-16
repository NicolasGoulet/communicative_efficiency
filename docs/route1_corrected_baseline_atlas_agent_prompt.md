# Corrected Route 1 Baseline Atlas Agent Prompt

Use this document to launch the long corrective Route 1 modeling run. It is an
agent-facing implementation prompt, not a results report. Do not claim any of
the models below have been fit until real artifacts exist.

## Short Conceptual Answer

Route 1 still predicts utterance information:

```text
sum_bits ~ age + effort + controls
```

The corrected plan is to:

1. clean up the real-child M1-M6 formula ladder;
2. compare child-identity structures as separate variants;
3. repeat the full M1-M6 atlas independently for each baseline source;
4. only then fit a pooled source-comparison model.

Route 2, where effort/length is the outcome, is parked until this is complete.

## Child Identity Structures To Compare

These are not interchangeable, and the next implementation should compare them
as separate variants.

| variant | meaning | formula pattern | role |
| --- | --- | --- | --- |
| CS0 pooled OLS | no child identity control | `sum_bits ~ predictors` | diagnostic/confounded baseline |
| CS0c pooled OLS + child-clustered SE | same fitted mean as CS0, child-adjusted uncertainty | `sum_bits ~ predictors`, `cov_type='cluster'` | shows uncertainty effect only |
| CS1 child fixed intercepts | one baseline per child | `sum_bits ~ predictors + C(child_id)` | primary Route 1 control |
| CS2 child fixed intercepts and slopes | one baseline and age-slope adjustment per child | `sum_bits ~ predictors + C(child_id) + age_c:C(child_id)` | diagnostic, high-parameter |
| CS3 GEE grouped by child | population-average model with repeated-child correlation | `gee(..., groups=child_id)` | sensitivity |
| CS4 random child intercept | partially pooled child baselines | `MixedLM(..., groups=child_id)` / `(1 \| child_id)` | sensitivity |
| CS5 random child intercept and age slope | partially pooled baselines and slopes | `MixedLM(..., re_formula='~age_c')` / `(1 + age_c \| child_id)` | sensitivity if stable |
| CS6 fixed-effect within-child age | within-child age only, with child fixed baselines | `age_within_child * effort + controls + C(child_id)` | checks within-child slope |
| CS7 Mundlak within/between age | separates within-child and between-child age | `age_within_child * effort + child_mean_age + controls` with clustered/GEE/random child structure | checks composition |

Do not combine `C(child_id)` and `(1 | child_id)` as if they were two
independent controls in the same model. A child fixed intercept already gives
each child its own baseline; a random child intercept models those baselines
through a partially pooled distribution.

Do not estimate `child_mean_age` inside a `C(child_id)` model. Child fixed
intercepts absorb child-level constants. Use `age_within_child + C(child_id)`
for the fixed-effect within-child check, or use a Mundlak-style
`age_within_child + child_mean_age` model with clustered/GEE/random child
structure.

## Corrected Route 1 Formula Ladder

All interactions must obey hierarchy. In statsmodels/Patsy:

```text
age_c * effort_c
```

means:

```text
age_c + effort_c + age_c:effort_c
```

Fit effort units separately. Do not put words, morphemes, syllables, and
phonemes in the same formula.

Core ladder:

```text
M1:  sum_bits ~ age_c + effort_c
M2:  sum_bits ~ age_c + effort_c + C(child_id)
M3:  sum_bits ~ age_c * effort_c + C(child_id)
M4a: M3 + parent_context_effort_c
M4b: M3 + context_entropy_c
M4c: M3 + question_type
M5:  M3 + parent_context_effort_c + context_entropy_c + question_type
M6:  M3 + age_c:context_entropy_c + effort_c:context_entropy_c
     + parent_context_effort_c + question_type
```

Extended internal-report ladder:

```text
M7:  sum_bits ~ age_c + I(age_c^2) + effort_c + child structure
M8:  sum_bits ~ age_c * effort_c + I(age_c^2)
     + I(age_c^2):effort_c + child structure
M9:  sum_bits ~ C(age_bin) + effort_c + child structure
M10: sum_bits ~ C(age_bin) * effort_c + child structure
M11: M5 + age_c:parent_context_effort_c
M12: M5 + age_c:question_type
M13: M5 + context_entropy_c:question_type
M14: M5 + parent_context_effort_c:context_entropy_c
M15: expanded context interaction stress test with age/effort/context
     interactions and all lower-order context terms
```

The extended models are for internal robustness and model-comparison reporting.
They do not replace the core M1-M6 ladder.

For CS0/CS3/CS4/CS5/CS7 variants, remove `C(child_id)` and use the
corresponding child structure instead. Keep the same scientific predictors.

## Baseline Atlas Logic

Repeat the whole corrected M1-M6 Route 1 atlas independently for each target
source:

```text
real child target
random generated target
unigram generated target
bigram generated target
trigram generated target
LSTM generated target(s), keeping k variants separate
```

The point is to compare the developmental trajectory of the real children
against the developmental trajectories induced by the baselines.

Report products should preserve that separation:

```text
Report A: real child M1-M6 / MX atlas
Report B: random baseline M1-M6 / MX atlas
Report C: unigram baseline M1-M6 / MX atlas
Report D: bigram baseline M1-M6 / MX atlas
Report E: trigram baseline M1-M6 / MX atlas
Report F+: one separate atlas for each LSTM target variant
```

Each source-specific report should use the same formula ladder, effort units,
context windows, child-structure labels, fixed-effort plots, and robustness
logic where data support them. Do not put the baselines and real child targets
into one mixed report and then treat that as the atlas.

After the independent source-specific atlases exist, fit a pooled formal source
comparison:

```text
sum_bits ~ target_source * age_c * effort_c + context_controls + C(child_id)
```

This pooled model is a formal comparison after the separate atlases, not a
replacement for them. The pooled-comparison report should explicitly say which
source-specific atlas artifacts it is comparing.

## Prompt To Give A Fresh Agent

````text
You are working in /home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency.

Goal: implement the corrected Route 1 M1-M6 baseline-atlas rebuild. This is a
large modeling task. Route 1 means predicting utterance information
(`sum_bits`) from age, target effort, child/context controls, and source
condition. Do not work on Route 2 effort-as-outcome modeling in this task.

Read first:
1. AGENTS.md
2. TODO.md
3. docs/notes.md, especially the 2026-06-16 Route 1 model-ladder clarification
4. docs/route1_corrected_baseline_atlas_agent_prompt.md
5. docs/utterance_information_m1_m6_technical_implementation_companion.md
6. docs/utterance_information_m1_m6_super_atlas_v2_interpreted.md
7. current relevant model builders/tests, especially:
   - src/build_route1_analysis_dataset.py, if present
   - src/build_m1_m6_super_atlas_report.py
   - src/build_m1_m6_interpreted_atlas_report.py
   - src/build_context_m1_m6_fixed_effort_atlas_report.py
   - src/build_age_scrambling_robustness_report.py
   - tests touching the above

Non-negotiable modeling rules:
- Do not silently change schemas; document every output schema.
- Do not claim a model was fit unless the command ran and artifacts exist.
- Do not combine incompatible child structures: do not use `C(child_id)` and
  `(1 | child_id)` as redundant controls in the same model.
- Do not estimate child-level between predictors such as `child_mean_age` in a
  model with `C(child_id)`.
- If using an interaction, keep the lower-order terms. In Patsy, `a * b`
  expands to `a + b + a:b`; make this explicit in report text.
- Fit effort units separately.
- Repeat the whole source-specific atlas independently before fitting pooled
  source interactions.

Phase 0: audit inputs.
- Identify the current Route 1 scored long table and source scored trees.
- Identify exact target columns/sources for real child, random, unigram,
  bigram, trigram, and LSTM variants.
- Confirm row identifiers that pair real and generated target rows to the same
  child/session/context.
- Summarize row counts, missing age, missing target, missing `sum_bits`, missing
  context entropy, and target-source coverage. Never print whole datasets.

Phase 1: build or update the Route 1 modeling dataset.
- Create a long source-specific modeling frame with one row per source target:
  real child, random, unigram, bigram, trigram, LSTM variants.
- Preserve source row ids, child_id, dataset/corpus, session/file, age_months,
  age bin, context_k, context text/id, target_source, target_utterance,
  `sum_bits`, and scorer provenance.
- Recompute target effort for each target utterance/source separately:
  words, morphemes, syllables CMU/pkg, syllables pkg, phonemes.
- Add or audit `parent_context_effort_*` for k1-k3.
- Add or audit `question_type` for preceding caretaker context.
- Attach/audit `context_entropy` and `context_size`.
- Write compact schema/readme/audit CSVs under results, not Git-tracked data.
- Add tests for schema, row pairing, target-source coverage, effort recompute,
  and missingness accounting.

Phase 2: implement corrected M1-M6 model definitions.
- Use centered numeric predictors.
- Fit one effort unit per row.
- Use this scientific ladder:
  M1: age + effort
  M2: age + effort + child fixed intercepts
  M3: age * effort + child fixed intercepts
  M4a: M3 + parent_context_effort
  M4b: M3 + context_entropy
  M4c: M3 + question_type
  M5: M3 + parent_context_effort + context_entropy + question_type
  M6: M3 + age:context_entropy + effort:context_entropy
      + parent_context_effort + question_type
- Also prepare extended internal MX families M7-M15 for a larger technical
  model-comparison report, while labeling them as extended rather than core.
- Store readable formula, actual statsmodels formula, centered predictors,
  effort unit, target_source, context_k, child-structure variant, estimator,
  covariance, n_obs, n_children, n_sessions, coefficient summaries, status,
  warnings/errors, and artifact provenance.

Phase 3: child-structure sensitivity.
- For the core formulas, compare these as separate variants:
  CS0 pooled OLS no child identity;
  CS0c pooled OLS with child-clustered SE;
  CS1 OLS + `C(child_id)` with child-clustered SE, primary;
  CS2 OLS + `C(child_id) + age_c:C(child_id)`, diagnostic;
  CS3 GEE grouped by child, no child fixed intercept unless explicitly marked
      as a separate fixed-effect-plus-GEE sensitivity;
  CS4 MixedLM random intercept `(1 | child_id)`;
  CS5 MixedLM random intercept and slope `(1 + age_c | child_id)`;
  CS6 fixed-effect within-child age check;
  CS7 Mundlak within/between age check without `C(child_id)`.
- Summarize which child-structure choices change the age coefficient, the
  age-effort interaction, and fixed-effort predicted curves.

Phase 4: source-specific atlases.
- Repeat the corrected M1-M6 atlas independently for each target_source:
  real child, random, unigram, bigram, trigram, LSTM variants.
- Write one technical atlas report per target_source. A real-child report, a
  random report, each n-gram report, and each LSTM report are separate
  deliverables.
- Generate the same compact tables, fixed-effort plots, and robustness summaries
  for each source.
- Make side-by-side source comparison plots only after the independent source
  fits exist.

Phase 5: pooled source comparison.
- Fit `sum_bits ~ target_source * age_c * effort_c + context_controls
  + C(child_id)` after source-specific atlases exist.
- Interpret source interactions as differences in developmental trajectories,
  not as standalone effects.
- Write a separate comparison report that reads selected outputs from the
  source-specific atlases. It should not be the only place where baseline
  models are fit or interpreted.

Phase 6: robustness and reporting.
- Reuse or adapt age-bin balancing and age-scrambling checks for each source.
- Produce a technical internal report, not a supervisor-facing rewrite yet.
- Update TODO.md and docs/notes.md with commands, outputs, row counts, warnings,
  and verification.
- Add or update tests, then run focused tests and the full suite if feasible.

Expected deliverables:
- A tested dataset builder or updater for the corrected source-specific Route 1
  modeling frame.
- A tested model runner for corrected core M1-M6 formulas, extended M7-M15
  formulas, and child-structure variants.
- Source-specific M1-M6/MX results for real, random, unigram, bigram, trigram,
  and LSTM target sources.
- Separate technical atlas reports for real, random, unigram, bigram, trigram,
  and each LSTM target source.
- A later baseline-comparison report with side-by-side developmental
  trajectories, built from the source-specific atlas outputs.
- A child-structure sensitivity report explaining `C(child_id)` versus
  `(1 | child_id)` and related variants.
- TODO.md and docs/notes.md updates.

Stop and ask before launching very long/GPU/HPC work or before modifying
scored-source symlinks. Do not copy multi-GB scored outputs into Git.

Preflight command to run before the long fit:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_corrected_baseline_atlas.py \
  --stage preflight \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/full_preflight \
  --target-sources real,random,unigram,bigram,trigram,lstm_additive_k3_same_length,lstm_additive_k4_same_length,lstm_additive_k5_same_length \
  --context-ks k1,k2,k3 \
  --effort-cols all \
  --model-ids all \
  --max-rows 0 \
  --chunksize 250000
```

Full source-specific fit command after preflight passes:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_corrected_baseline_atlas.py \
  --stage fit-atlas \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/full_source_specific \
  --target-sources real,random,unigram,bigram,trigram,lstm_additive_k3_same_length,lstm_additive_k4_same_length,lstm_additive_k5_same_length \
  --context-ks k1,k2,k3 \
  --effort-cols all \
  --child-structures primary \
  --model-ids all \
  --max-rows 0 \
  --chunksize 250000
```

Core child-structure sensitivity command after the source-specific fit:

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_corrected_baseline_atlas.py \
  --stage fit-atlas \
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \
  --output-dir results/route1_corrected_baseline_atlas/full_child_structure_sensitivity \
  --target-sources real \
  --context-ks k3 \
  --effort-cols all \
  --child-structures CS0,CS0c,CS1,CS2,CS3,CS4,CS5,CS6,CS7 \
  --model-ids core \
  --max-rows 0 \
  --chunksize 250000
```
````

## Acceptance Checklist

- [ ] All generated target sources have audited row counts and paired row ids.
- [ ] Effort counts are recomputed from each source target utterance.
- [ ] Parent-context effort and question type are present or explicitly
      documented as unavailable.
- [ ] M1-M15 formulas obey interaction hierarchy.
- [ ] Child-structure variants are fit separately and labeled clearly.
- [ ] No model combines `C(child_id)` with random child intercepts.
- [ ] No model estimates `child_mean_age` together with `C(child_id)`.
- [ ] Independent source-specific atlases exist before pooled source
      interaction interpretation.
- [ ] There is one source-specific report per real/baseline/LSTM target source;
      the pooled comparison report is separate and explicitly downstream.
- [ ] Fixed-effort plots and age-scrambling checks are comparable across
      sources.
- [ ] Documentation says which models are fit versus proposed.
