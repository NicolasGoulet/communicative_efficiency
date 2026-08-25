<div class="report-nav" aria-label="Report pages"><a class="active" href="august_routes_report.html">Data overview</a><a href="august_routes_route1.html">Route 1</a><a href="august_routes_route2.html">Route 2</a><a href="august_routes_word_level.html">Word level</a></div>

# Data and analysis overview

This is the entry page for the supervisor-facing report. It restores the July reading order: first understand the data and measurements, then open one analysis at a time. The longer audited August package remains unchanged as the evidence archive.

## The three analysis pages

<div class="route-grid"><a class="route-card" href="august_routes_route1.html"><span>Page 2</span><strong>Route 1</strong><em>Utterance surprisal at fixed word effort</em></a><a class="route-card" href="august_routes_route2.html"><span>Page 3</span><strong>Route 2</strong><em>Child effort relative to a generated response space</em></a><a class="route-card" href="august_routes_word_level.html"><span>Page 4</span><strong>Word level</strong><em>Same-word surprisal across three scorers</em></a></div>

## Corpora, children, and inferential roles

The longitudinal data come from 13 strict-naturalistic CHILDES corpora. Brown, Manchester, and Providence form the **21-child PBM discovery sample**. The other 58 children across 10 corpora are a separate **non-PBM confirmation sample**. These roles are fixed and the samples are not pooled for a stronger-looking result.

TinyDialogues and the three word-level scorers reuse the PBM children. Agreement across them is scorer robustness, not independent-sample confirmation. Hall remains a separate historical cross-sectional/domain-sensitivity analysis and is not part of these four pages.

| analysis | sample | analysis_rows | children | role |
| --- | --- | --- | --- | --- |
| Route 1 | Mistral — PBM discovery | 444325 | 21 | discovery |
| Route 1 | TinyDialogues — PBM robustness | 443848 | 21 | same-child scorer robustness |
| Route 1 | Mistral — non-PBM confirmation | 678071 | 58 | confirmation |
| Route 2 | PBM utterances; final models use 976 child-session aggregates | 444325 | 21 | response-space exploration |
| Word level | exact shared PBM word-occurrence set | 1032963 | 21 | same-child scorer robustness |

> Row counts are analysis-specific denominators. The same utterance or word occurrence can contribute to more than one separately fit scorer, so the rows in this table must not be added together.

## Developmental coverage

The age distribution is uneven, as expected in longitudinal CHILDES data. The plot shows Mistral contextual-score coverage for the two longitudinal samples; it does not combine discovery and confirmation.

![PBM and non-PBM contextual-score coverage by age](../results/august_routes_report/plots/data_contextual_coverage_by_age.png)

The first bin combines 6–23 months; subsequent bins are six-month intervals through 60–65 months. Later-age estimates depend on fewer utterances and a changing mix of children and corpora, which is why child identity, within-child change, clustering, and repeated-measures checks matter.

## What is measured

- **Unconditional utterance surprisal (k0):** `-log2 p(u)`, a scorer-indexed measure of form predictability without preceding conversational context.
- **Contextual utterance surprisal (k3):** `-log2 p(u | c)`, using up to three preceding caregiver utterances.
- **Context gain:** `k0 - k3`, kept separate from unconditional form frequency.
- **Production effort:** lexical word count is the primary validated measure in these pages. Alternative morpheme, syllable, and phoneme measures remain sensitivities pending full validation.
- **Response-space uncertainty:** exact-string entropy over sampled Mistral responses. It is generator- and setting-dependent and is not semantic entropy.
- **Word-level surprisal:** scorer-specific information assigned to aligned word occurrences; Mistral, Qwen3-14B, and TinyDialogues are fit separately because their tokenizers and raw bit scales differ.

## Why the models become more complex

Many utterances come from the same child, and many word observations repeat the same lexical item. The report therefore starts with transparent descriptive lines, then adds effort controls, child identity, within-child decompositions, GEE or mixed effects, nonlinear age terms, and whole-child resampling. The more complex models are checks around a declared primary estimand; they are not used to select whichever result is most favorable.

## How to read the plots

A downward surprisal line means that the scorer finds the form more predictable at older ages under the controls named for that model. It does not by itself mean that more Shannon information was communicated, that a listener benefited, or that the child reached a normative efficiency optimum. Shaded ribbons are model-based uncertainty, not the raw spread of utterances.

## Full evidence preserved

- [Original audited August package](august_supervisor_index.html)
- [Complete August supervisor report](august_supervisor_report.html)
- [Combined self-contained archive of the three analysis pages](august_routes_report.embedded.html)

<div class="next-page">Next: <a href="august_routes_route1.html">Route 1 — utterance surprisal at fixed effort →</a></div>
