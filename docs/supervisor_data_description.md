# Data description

[← Back to report home](supervisor_report.md)

The developmental dataset contains recordings of caregiver–child speech from
CHILDES. This page describes the children, the source corpora, their age
coverage, and the measurements currently available.

| Dataset summary | Count |
| --- | ---: |
| Children observed at multiple ages | 79 |
| Longitudinal caregiver–child corpora | 13 |
| Scored child utterances | 1,140,695 |
| Scored caregiver utterances | 1,470,154 |

## What a corpus is

A **corpus** is a collection of transcripts assembled by one research project.
Each corpus has its own participants, recording schedule, setting, and
transcription practices. A corpus is not the same thing as a child, a recording
session, or an utterance.

The 79 children come from 13 corpora. The children have repeated recordings at
different ages, which is why we describe them as longitudinally observed.

## How the corpora were selected

The combined dataset includes longitudinal, non-clinical caregiver–child
interaction corpora with usable child identity, caregiver speech, age, and
session information. The recordings primarily capture spontaneous family,
home, or play interaction rather than a clinical probe or a tightly
standardized elicitation task.

The corpora do not all use identical recording procedures. They differ in
geography, setting, sampling density, age coverage, and transcription
conventions. These differences remain visible in the corpus table and are
considered in the statistical analyses.

Champaign and EHS are not included because their observations are more
explicitly task-structured. Cummings is a clinical/probe corpus and its locally
prepared files do not contain caregiver rows. Hall is analyzed separately
because it is a cross-sectional sociolinguistic sample near age four rather
than a longitudinal developmental corpus. Thomas was considered but was not
locally available when this dataset was assembled.

## How the 79 children are used in the analyses

We first developed the analyses using the 21 children from Brown, Manchester,
and Providence. We then evaluated the same questions in the other 58 children.
Finally, we combined all 79 children to estimate the overall relationships in
the complete dataset. All three analyses are reported so that the combined
estimate does not conceal differences between the two groups.

| Analysis group | Children | Corpora | Child utterances | Caregiver utterances | Child sessions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Brown, Manchester, and Providence | 21 | 3 | 446,985 | 668,903 | 983 |
| Other 10 corpora | 58 | 10 | 693,710 | 801,251 | 1,770 |
| All 13 corpora combined | 79 | 13 | 1,140,695 | 1,470,154 | 2,753 |

## Developmental age distributions

The first age group combines observations from 6–23 months. The remaining
groups cover six-month intervals through 60–65 months. The left and right
arrows move between the complete dataset, the two analysis groups, and each of
the 13 individual corpora.

<!-- AGE_DISTRIBUTION_GALLERY_START -->

![All 79 children](../results/supervisor_report/data_description/utterance_coverage_by_age.png)

Additional distribution plots:

- [Brown, Manchester, and Providence](../results/supervisor_report/data_description/utterance_coverage_by_age__three_corpora.png)
- [Other 10 corpora](../results/supervisor_report/data_description/utterance_coverage_by_age__other_corpora.png)
- [Belfast](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_belfast.png)
- [Brown](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_brown.png)
- [Demetras1](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_demetras1.png)
- [Forrester](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_forrester.png)
- [Kuczaj](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_kuczaj.png)
- [Lara](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_lara.png)
- [MPI-EVA-Manchester](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_mpi_eva_manchester.png)
- [Manchester](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_manchester.png)
- [Post](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_post.png)
- [Providence](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_providence.png)
- [Sachs](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_sachs.png)
- [Weist](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_weist.png)
- [Wells](../results/supervisor_report/data_description/utterance_coverage_by_age__corpus_wells.png)

<!-- AGE_DISTRIBUTION_GALLERY_END -->

## Corpora and children

| Corpus | Children | Child utterances | Sessions | Observed ages in months |
| --- | ---: | ---: | ---: | ---: |
| Belfast | 8 | 22,942 | 90 | 24.1–54.2 |
| Brown | 3 | 92,555 | 214 | 18.0–62.4 |
| Demetras1 | 1 | 6,842 | 26 | 24.9–47.9 |
| Forrester | 1 | 6,663 | 35 | 12.0–60.0 |
| Kuczaj | 1 | 37,109 | 210 | 28.8–60.4 |
| Lara | 1 | 49,328 | 120 | 21.4–39.8 |
| MPI-EVA-Manchester | 4 | 462,100 | 687 | 24.0–61.6 |
| Manchester | 12 | 232,614 | 408 | 20.7–36.3 |
| Post | 3 | 8,068 | 30 | 19.2–32.2 |
| Providence | 6 | 121,816 | 361 | 11.1–48.1 |
| Sachs | 1 | 16,344 | 93 | 15.0–57.1 |
| Weist | 6 | 46,347 | 182 | 25.0–60.2 |
| Wells | 32 | 37,967 | 297 | 17.7–60.8 |

![Observed age span for each of the 79 children](../results/supervisor_report/data_description/child_longitudinal_coverage.png)

The horizontal lines show the youngest and oldest recorded age for each child.
Teal identifies children from Brown, Manchester, and Providence; orange
identifies children from the other 10 corpora.

## Available measurements

| Measurement | Current coverage |
| --- | --- |
| Mistral utterance surprisal | All 79 children: 1,140,695 child utterances and 1,470,154 caregiver utterances, scored with zero to three preceding caregiver utterances. |
| TinyDialogues utterance surprisal | The same 21 children from Brown, Manchester, and Providence. |
| Word-level surprisal from Mistral, Qwen3-14B, and TinyDialogues | A shared set of 1,032,963 word occurrences from the same 21 children, analyzed separately for each language model. |
| Generated caregiver responses | 444,325 child utterances from the same 21 children, linked to 268,712 preceding conversational contexts. |
