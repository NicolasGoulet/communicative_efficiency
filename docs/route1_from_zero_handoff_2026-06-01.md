# Route 1 From-Zero Handoff - 2026-06-01

This is the clean handoff for restarting the analyses from zero on
2026-06-02.

The key decision is now explicit:

```text
communicative_efficiency = from-zero scientific analysis workspace
compute_surprisal_mila  = scoring, HPC, audits, old analysis archive
```

Do not treat older analysis reports as the evidential baseline. They are useful
for engineering patterns, variable definitions, and sanity checks, but tomorrow
the Route 1 claims should be rebuilt from first principles with the user
choosing each modeling step.

## Repos And Data Paths

Main analysis repo:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency
```

Scoring / old-analysis repo:

```text
/home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila
```

Symlinks already available in this repo:

```text
results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral
  -> /home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/mila_results/raw_surprisal_cleaned

results/external/compute_surprisal_mila/raw_surprisal_lstm_additive_same_length
  -> /home/apaixonada/EvaPortelance/Projet_1/compute_surprisal_mila/results/raw_surprisal_lstm_additive_pbm_006_065_k3_k4_k5_same_length
```

## What Is Audited And Usable Now

Main cleaned Mistral scored tree:

```text
compute_surprisal_mila/mila_results/raw_surprisal_cleaned/
```

Audit status from `analysis/reports/scoring_integrity_audit_2026-06-01.md`:

```text
504/504 expected CSVs present
6 modes x 4 context settings x 21 children
missing files: 0
extra files: 0
problem files: 0
```

Modes:

```text
real
random
unigram
bigram
trigram
caretaker
```

Contexts:

```text
WITHOUT_context/k0
WITH_context/k1
WITH_context/k2
WITH_context/k3
```

LSTM additive same-length tree:

```text
compute_surprisal_mila/results/raw_surprisal_lstm_additive_pbm_006_065_k3_k4_k5_same_length/
```

Audit status:

```text
252/252 expected CSVs present
3 LSTM modes x 4 context settings x 21 children
problem files: 0
```

This is available for later baseline comparison. It is not the first thing to
model in the Route 1 restart unless the user explicitly chooses it.

## Dataset Summary For Route 1

The current local scored cleaned Mistral results cover:

```text
Brown
Manchester
Providence
```

These are longitudinal naturalistic parent-child corpora.

Counts below are from the no-context `k0` scored files, so each utterance is
counted once rather than once per context window.

| corpus | children | real child rows | caretaker rows | generated rows per baseline | age range months |
| --- | ---: | ---: | ---: | ---: | --- |
| Brown | 3 | 92,555 | 64,206 | 92,555 | 18.000-62.400 |
| Manchester | 12 | 232,614 | 342,246 | 232,614 | 20.733-36.333 |
| Providence | 6 | 121,816 | 262,451 | 121,816 | 11.133-48.067 |
| total | 21 | 446,985 | 668,903 | 446,985 | 11.133-62.400 |

## Information Outcomes

The scored CSVs give target-utterance Mistral surprisal. The main available
quantities are:

| quantity | formula | meaning | caveat |
| --- | --- | --- | --- |
| `sum_bits` | saved directly | total target utterance information | strongly length-dependent |
| `mean_bits_per_token` | saved directly | average Mistral-token surprisal | tokenizer unit, not production unit |
| `bits_per_word` | `sum_bits / cleaned_word_count` | information per produced lexical word | needs explicit cleaned word count |
| `context_gain_bits` | `sum_bits(k0) - sum_bits(k)` | how much context lowers target surprisal | still target-conditioned |
| `context_gain_per_word` | `context_gain_bits / cleaned_word_count` | context support per word | not context-only entropy |

Important: recompute word counts from the cleaned target string. Do not trust
old `word_count` or `morph_count` columns from old pipelines because punctuation
inflation was documented.

## Route 1 Restart Question

Start with one plain-language question:

```text
Does child age predict the information rate of child utterances after
controlling for utterance length and repeated observations from the same child?
```

Preferred first outcome to discuss:

```text
bits_per_word = sum_bits / cleaned_word_count
```

Sensitivity outcomes:

```text
mean_bits_per_token
sum_bits
```

The model should still control exact word count even when using
`bits_per_word`, because one-word and eight-word utterances have different
structure that a ratio does not erase.

## From-Zero Modeling Rule

For every Route 1 analysis, follow this order:

1. Define the scientific question in plain language.
2. Define the exact outcome variable.
3. Define the observational unit.
4. List candidate predictors and their types.
5. Decide which predictors are controls, focal predictors, or interactions.
6. Inspect descriptive plots and distributions before fitting models.
7. Fit the simplest defensible model first.
8. Add complexity one block at a time only when it answers a clear question.
9. Record why each model exists, not just its formula.
10. Bring old reports back only after the rebuilt analysis reaches the same
    conceptual point.

## Suggested June 2 Route 1 Sequence

Do this in order unless the user redirects.

1. Build one clean Route 1 model frame from the audited main Mistral tree.
   Include real child rows first. Add baselines only after the real-child frame
   is understood.
2. Recompute `cleaned_word_count` from the target string using the explicit
   word-count logic from the old scoring repo as a reference.
3. Create descriptive plots:
   - age distribution by child and corpus;
   - word-count distribution by age;
   - `bits_per_word` by age, split by context window;
   - same plots with sparse-bin counts visible.
4. Fit the simplest real-child k0 model:

```text
bits_per_word ~ age + exact_word_count + child
```

5. Add context windows:

```text
bits_per_word ~ age * context_window + exact_word_count + child
```

6. Only then compare to generated baselines:

```text
bits_per_word ~ age * variant + context_window + exact_word_count + child
```

7. Keep LSTM additive baselines as a later comparison block, not as the first
   Route 1 claim.

## What To Treat As Archive, Not Evidence

These exist and can be useful, but they are not the from-zero evidential
baseline:

```text
compute_surprisal_mila/analysis/reports/route1_groundup_advanced_analytics_report_2026-05-29.*
compute_surprisal_mila/analysis/reports/route1_bits_per_word_advanced_analytics_report_2026-05-29.*
compute_surprisal_mila/analysis/reports/supervisor_communicative_efficiency_current_results_2026-05-30.*
compute_surprisal_mila/results/cleaned_analysis/final_claim_surprisal_sequence/
```

Old headline result to remember, but not reuse as the new final claim:

```text
Older WLS models suggested bits_per_word decreases with age, especially at k0,
and the age slope weakens as more context is provided. This is a lead to
rebuild, not a claim to copy.
```

## Pending / Do Not Use Yet

PBM `006-023` generated-baseline patch:

```text
status: pending Mila completion and audit
```

The first PBM patch runs were affected by a Slurm `--export` comma-truncation
bug. The patch outputs only had random k0/k1, not all modes and contexts. Do
not use the PBM early generated-baseline patch until it is rerun and audited.

The wrapper bug is now documented and fixed in the scoring repo, but the
corrected result tree still needs to be produced and audited.

Context entropy, KL/JS divergence, and word-level surprisal features:

```text
status: pending hardened reruns and audits
```

Any feature job submitted before the 2026-06-01 wrapper fix should be treated
as suspect unless its merged output passes the feature audits.

## Practical Boundary For Tomorrow

For Route 1 on 2026-06-02, the safest starting point is:

```text
real child Mistral scores from raw_surprisal_cleaned_mistral
```

Then add:

```text
context windows k0-k3
```

Then add:

```text
random/unigram/bigram/trigram baselines, with the 006-023 patch status clearly
marked
```

Then, later:

```text
LSTM additive same-length baselines
entropy/KL/word-level features
Route 2 length-prediction models
```

