# Direct-Surprisal Replication: TinyDialogues PBM And Full-79 Mistral

Updated: 2026-07-22

This is the landing page for the newly implemented direct-surprisal analyses.

## Start With The Visual Reports

**Recommended:** open the
[interactive results explorer](direct_surprisal_results_explorer.html). It is
the usable consultation view: 136 filterable model cards with formulas and
plain-language readings, 31 click-to-enlarge summary plots, a searchable
one-child-at-a-time browser, model-family status, and a glossary. It contains
no result tables.

The older short reports remain available as linear snapshots:

- [Interactive model, plot, and child explorer](direct_surprisal_results_explorer.html)
- [TinyDialogues PBM visual summary](tinydialogues_pbm_visual_summary.html)
- [Mistral full-79 visual summary](mistral_full79_visual_summary.html)
- [Paired TinyDialogues–Mistral visual comparison](paired_tinydialogues_mistral_visual_summary.html)
- [TinyDialogues individual-child gallery](tinydialogues_pbm_child_gallery.html)
- [Mistral individual-child gallery](mistral_full79_child_gallery.html)
- [Modular pipeline and rerun instructions](direct_surprisal_modular_pipeline.md)
It keeps three claims separate:

1. TinyDialogues on the 21 PBM children is a **scorer-robustness analysis on
   the discovery sample**;
2. Mistral on the 58 non-PBM children is the prespecified **sample
   confirmation analysis**; and
3. Mistral on all 79 children is **descriptive**, not confirmatory.

The frozen protocol is in
[direct_surprisal_replication_protocol_2026-07-21.md](direct_surprisal_replication_protocol_2026-07-21.md).

## Data Audit

| Product | Child rows | Children | Corpora | Key/target mismatches | Score gaps |
| --- | ---: | ---: | ---: | ---: | --- |
| TinyDialogues PBM | 446,508 | 21 | 3 | 0 | none |
| Mistral full-79 | 1,140,695 | 79 | 13 | 0 | 24 generated-baseline cells; no real-child gaps |
| Exact TinyDialogues–Mistral PBM intersection | 446,508 | 21 | 3 | 0 unexplained | 477 Mistral-only Providence/Naima rows from the later source patch |

The 24 Mistral gaps are six generated n-gram targets repeated across k0–k3.
They affect only the bigram/trigram candidate comparisons. They do not affect
the real-child P1–P3 models. The 477-row Naima difference is a source-version
coverage difference: those rows were added to the later full-79 source after
the TinyDialogues PBM run.

## Frozen Primary Results

All coefficients are bits per month at fixed exact/top-coded lexical word
effort with child fixed effects and child-clustered covariance. Context gain is
`k0 - k3`; a positive value means the preceding context supports the observed
target under that scorer.

| Scorer/sample | Children | P1: k3 contextual slope [95% CI] | P2: k0 unconditional slope [95% CI] | P3: context-gain slope [95% CI] | Protocol reading |
| --- | ---: | --- | --- | --- | --- |
| TinyDialogues PBM discovery | 21 | −0.222 [−0.311, −0.132] | −0.254 [−0.339, −0.168] | −0.032 [−0.050, −0.014] | P1 expected direction; P3 contrary direction |
| Mistral PBM discovery | 21 | −0.131 [−0.179, −0.083] | −0.162 [−0.211, −0.112] | −0.030 [−0.050, −0.011] | P1 expected direction; P3 contrary direction |
| Mistral non-PBM confirmation | 58 | −0.062 [−0.132, 0.007] | −0.089 [−0.145, −0.034] | −0.028 [−0.045, −0.010] | P1 direction matches but primary interval includes zero; P3 contrary direction |
| Mistral all-79 descriptive | 79 | −0.080 [−0.134, −0.025] | −0.108 [−0.156, −0.059] | −0.029 [−0.041, −0.016] | descriptive only |

The frozen non-PBM P1 confirmation criterion is therefore **not met by the
primary child-clustered interval**, even though the estimate is negative. The
prespecified child bootstrap is more favorable: its non-PBM P1 percentile
interval is [−0.152, −0.014]. Both uncertainty results remain visible; the
bootstrap sensitivity is not substituted after inspection for the frozen
primary result.

The decomposition is consistent across these fits: k0 surprisal falls faster
with age than k3 surprisal, so `k0 - k3` context gain declines rather than
increases. That is a genuine contrary-direction result for P3.

## Paired Scorer Result

On the 446,508 exact shared PBM rows:

- k3 total-score Spearman correlation is 0.811 and within-child Spearman
  correlation is 0.803;
- the TinyDialogues P1 slope is 0.089 bits/month more negative than the Mistral
  slope, with paired child-bootstrap interval [−0.152, −0.028];
- the corresponding context-gain slope difference is −0.003 with interval
  [−0.044, 0.027], so that developmental decomposition is not detectably
  different between scorers on this comparison;
- 18 of the 21 supported child-specific P1 slopes have the same sign across
  scorers (85.7%); and
- raw utterance context-gain agreement is much weaker than target-surprisal
  agreement (k3 Spearman 0.157), which is an important calibration diagnostic.

## Individual Children

The implementation produced:

- 21 TinyDialogues PBM child profiles;
- 21 Mistral PBM child profiles;
- 58 non-PBM Mistral confirmation profiles;
- 79 all-child Mistral descriptive profiles; and
- 21 exact-cell TinyDialogues–Mistral overlay profiles.

All children meet the current descriptive slope support rule (at least three
distinct ages, six months of span, and 100 eligible utterances). Under
TinyDialogues, 20 of 21 child-specific adjusted k3 slopes are negative. Under
Mistral, 18 of 21 PBM slopes, 46 of 58 non-PBM slopes, and 63 of 79 pooled
descriptive slopes are negative. These child slopes are exploratory and are
not individually multiplicity-adjusted.

## Reports And Auditable Products

- [TinyDialogues PBM visual summary](tinydialogues_pbm_visual_summary.html)
- [Mistral full-79 visual summary](mistral_full79_visual_summary.html)
- [Paired TinyDialogues–Mistral visual comparison](paired_tinydialogues_mistral_visual_summary.html)
- [TinyDialogues PBM direct-surprisal report](tinydialogues_pbm_direct_surprisal_replication.html)
- [Full-79 Mistral discovery/confirmation report](mistral_full79_direct_surprisal_replication.html)
- [Paired TinyDialogues–Mistral scorer report](paired_tinydialogues_mistral_pbm_report.html)
- [Paired child trajectory overlays](paired_tinydialogues_mistral_child_trajectories.html)
- [TinyDialogues PBM expanded Route-1/model atlas](tinydialogues_pbm_route1_model_atlas.html)

Each report links its model summaries, coefficient tables, bootstrap draws,
sample-flow tables, influence diagnostics, trajectory tables, and plot audits.
The scorer-specific wide tables and bulky figures remain under ignored
`results/` and `figs/` paths rather than Git.

## Broader PBM Atlas

The complete TinyDialogues Route-1 long table contains 11,605,772 scored
target/context rows from all 504 files, with recomputed word, morpheme,
syllable, and phoneme effort and zero source-audit problems. The expanded atlas
fit 41 of 56 applicable direct model-zoo subvariants and all 45 explicit
comparison models. The other 15 subvariants are not failures: they are the
Z3/Z4/Z10 entropy or certainty families and are explicitly unavailable because
TinyDialogues-specific next-token entropy/top-k predictors do not exist.

## What Is Still In Progress

TinyDialogues-specific word-token alignments, LSTM target scores, and
response-space scores do not currently exist; analyses requiring them must be
marked unavailable or explicitly cross-model rather than presented as exact
TinyDialogues replications. Mixed-effects/hierarchical child trajectories,
simultaneous-band onset inference, richer complexity controls, and the six-cell
generated-target repair remain tracked in `TODO.md`.
