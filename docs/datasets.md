## Candidate Datasets

Short list of English CHILDES/CHAT datasets that are either already used in this
project or are plausible next candidates.

## English, Controls, Longitudinal

| Dataset | Size / Age / Sessions | Short Description |
| --- | --- | --- |
| [Providence](https://talkbank.org/phon/access/Eng-NA/Providence.html) | 6 children; 0;11-4;00; 364 sessions | Spontaneous parent-child home recordings, mostly with mothers. Strong candidate because it is dense, naturalistic, and already used here. |
| [Brown](https://talkbank.org/childes/access/Eng-NA/Brown.html) | 3 children; about 1;6-5;2; 214 transcript sessions | Classic longitudinal corpus of Adam, Eve, and Sarah. Naturalistic American English. Already used here. |
| [Manchester](https://talkbank.org/childes/access/Eng-UK/Manchester.html) | 12 children; 1;8-3;0; about 34 recordings per child | British English, mostly mother-child play at home. Children were recorded for about one year. Already used here. |
| [MPI-EVA-Manchester](https://talkbank.org/childes/access/Eng-UK/MPI-EVA-Manchester.html) | 4 children; roughly 2;0-5;1; 700 local CHAT files extracted from the project zip | Very dense British English sampling. Useful for fine-grained developmental analyses, but larger and less simple than Manchester. Gina and Helen require filename-based age fallback because some CHI `@ID` ages are blank. |
| [Belfast](https://talkbank.org/childes/access/Eng-UK/Belfast.html) | 8 children; 2;0-4;5; 90 local CHAT files | Longitudinal Belfast English corpus with monthly family visits. Added to preprocessing on 2026-05-20. |
| [Wells](https://talkbank.org/childes/access/Eng-UK/Wells.html) | 32 children; 1;6-5;0; 299 transcript sessions | British preschool corpus. Naturalistic home recordings collected at random intervals during the day. |
| [Lara](https://talkbank.org/childes/access/Eng-UK/Lara.html) | 345 local CHAT files; 1 child | Longitudinal naturalistic caregiver-child corpus. Local transcripts are direct root files and include a grandmother caregiver tier (`ELS`) kept in `caretakers.csv`. |
| [Sachs](https://talkbank.org/childes/access/Eng-NA/Sachs.html) | 93 local CHAT files; 1 child | Longitudinal naturalistic mother-child corpus for Naomi. Local transcripts are direct root files. |
| [Weist](https://talkbank.org/childes/access/Eng-NA/Weist.html) | 6 local child folders; 182 local CHAT files | Longitudinal naturalistic caregiver-child corpus. |
| [Kuczaj](https://talkbank.org/childes/access/Eng-NA/Kuczaj.html) | 210 local CHAT files; 1 child | Longitudinal naturalistic father-child corpus for Abe. Local transcripts are direct root files. |
| [Post](https://talkbank.org/childes/access/Eng-NA/Post.html) | 3 children; 1;7-2;8; 30 sessions | Rural Florida home free-play corpus. Later-born children followed for about 9 months. |
| [Demetras1](https://talkbank.org/childes/access/Eng-NA/Demetras1.html) | 26 local CHAT files; 1 child | Longitudinal naturalistic father-child corpus for Trevor. Local transcripts are direct root files. |
| [Forrester](https://talkbank.org/childes/access/Eng-UK/Forrester.html) | 35 local CHAT files; 1 child | Longitudinal naturalistic father-child corpus for Ella. Local transcripts are direct root files. |
| Thomas | Pending local zip | Strict candidate from the download list, but `Thomas.zip` was not present in `data/zip_files` on 2026-05-20. |

## English, Controls, Structured Observation

| Dataset | Size / Age / Sessions | Short Description |
| --- | --- | --- |
| [Champaign](https://talkbank.org/childes/access/Eng-NA/Champaign.html) | 44 children; about 21-36 months; 6 measurement points | Longitudinal observational corpus. Added to preprocessing on 2026-05-20. Some blank `@ID` ages require parent-folder measurement-age fallback. Keep separate from the stricter naturalistic default. |
| [EHS / Early Head Start](https://talkbank.org/childes/access/Eng-NA/EHS.html) | 126 local child folders; 14, 24, 36 months and pre-K | Low-income rural parent-child interaction corpus. It is task-structured observational data, not clinical probe data. Keep separate from the stricter naturalistic default. |

## English, Clinical, Longitudinal

| Dataset | Size / Age / Sessions | Short Description |
| --- | --- | --- |
| [Ambrose Hearing Loss](https://talkbank.org/childes/access/Clinical-Eng/Ambrose/HL.html) | 22 children; about 1-3 years; up to 5 visits | Parent-child interactions with children with hearing loss. Visits around 13.5, 18, 22.5, 27, and 36 months. |
| [Ambrose Controls](https://talkbank.org/childes/access/Clinical-Eng/Ambrose/TD.html) | 23 listed controls; about 1-3 years; up to 5 visits | Normal-hearing comparison group for Ambrose. |
| [Feldman Parent-Child](https://talkbank.org/childes/access/Clinical-Eng/Feldman/ParentChild.html) | 56 target + 50 control children; 1;6-3;6; variable sessions | Parent-child data from children with focal brain lesions and matched controls. Good clinical comparison candidate. |
| [Cummings](https://talkbank.org/phon/access/Clinical/Cummings.html) | 21 local child folders; 3-7 years; clinical probes | PhonBank clinical corpus marked "clinical, cross-sectional (some longitudinal)." It has repeated child recordings but no caretaker rows in the local CHAT files, so keep it separate from naturalistic caregiver-child corpora. |

## English, Controls, Non-Longitudinal

| Dataset | Size / Age / Sessions | Short Description |
| --- | --- | --- |
| [Hall](https://talkbank.org/childes/access/Eng-NA/Hall.html) | 39 reported participants; 4;6-5;0; about 2 recording days per child | Naturalistic speech from preschool children across home, school, and transition settings. Designed for race and SES comparisons. Already used here. |
| Other | TBD | Add only if it is English, non-clinical, has usable child/caretaker speech, and preserves age/session metadata. |

## Notes

- "Size / Age / Sessions" uses TalkBank metadata when possible.
- When TalkBank reports transcripts rather than sessions, the table uses "transcript sessions" as a practical approximation.
- Before adding a corpus to the main pipeline, verify transcript count, speaker labels, age coverage, and whether parent/caretaker tiers are available.
- Current default distribution grouping is recorded in `results/corpus_groups/dataset_group_assignments.csv`.
